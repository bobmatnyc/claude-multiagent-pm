"""
Local Orchestration Executor
===========================

This module handles local orchestration execution, including context collection,
filtering, and message routing.
"""

import time
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from .message_bus import SimpleMessageBus, MessageStatus
from .context_manager import ContextManager, create_context_manager
from ..services.agent_registry_sync import AgentRegistry
from ..services.shared_prompt_cache import SharedPromptCache
from ..core.logging_config import get_logger
from .orchestration_types import ReturnCode
from .agent_handlers import AgentHandlerManager

logger = get_logger(__name__)


class LocalExecutor:
    """Handles local orchestration execution."""
    
    def __init__(self, working_directory: Path):
        self.working_directory = working_directory
        self._message_bus: Optional[SimpleMessageBus] = None
        self._context_manager: Optional[ContextManager] = None
        self._agent_registry: Optional[AgentRegistry] = None
        self._prompt_cache: Optional[SharedPromptCache] = None
    
    async def execute_local_orchestration(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Execute task using local orchestration.
        
        This method uses the new orchestration components while maintaining
        the same return structure as subprocess delegation.
        """
        task_id = kwargs.get("task_id", str(uuid.uuid4())[:8])
        return_code = ReturnCode.SUCCESS
        
        try:
            logger.debug("local_orchestration_start", extra={
                "agent_type": agent_type,
                "task_id": task_id
            })
            
            # Generate subprocess ID for compatibility
            subprocess_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Get agent prompt from registry using proper hierarchy
            agent_prompt_start = time.perf_counter()
            agent_prompt, agent_tier = self._get_agent_prompt_with_hierarchy(agent_type)
            agent_prompt_time = (time.perf_counter() - agent_prompt_start) * 1000
            
            # Log which agent level was selected
            if agent_prompt and agent_tier:
                logger.info("agent_selected", extra={
                    "agent_type": agent_type,
                    "agent_tier": agent_tier,
                    "prompt_loading_ms": agent_prompt_time,
                    "task_id": task_id,
                    "mode": "LOCAL"
                })
            
            if not agent_prompt:
                # Fallback if no agent found in registry (should rarely happen)
                logger.warning("agent_not_found_in_registry", extra={
                    "agent_type": agent_type,
                    "fallback": "generic_prompt",
                    "task_id": task_id
                })
                agent_prompt = f"""You are the {agent_type.title()} Agent.
Your role is to assist with {agent_type} tasks and provide expert guidance.
This is a LOCAL orchestration mode execution for instant responses."""
                agent_tier = "fallback"
            
            logger.debug("agent_prompt_ready", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "prompt_size": len(agent_prompt),
                "load_time_ms": agent_prompt_time
            })
            
            # Ensure context manager is initialized
            if not self._context_manager:
                self._context_manager = create_context_manager()
                logger.debug("context_manager_initialized_in_local_orchestration")
            
            # Collect current full context
            context_collection_start = time.perf_counter()
            full_context = await self._collect_full_context()
            context_collection_time = (time.perf_counter() - context_collection_start) * 1000
            
            # Calculate original context size
            original_context_size = self._context_manager.get_context_size_estimate(full_context)
            
            logger.debug("context_collected", extra={
                "task_id": task_id,
                "collection_time_ms": context_collection_time,
                "context_size_tokens": original_context_size,
                "files_count": len(full_context.get("files", {}))
            })
            
            # Filter context for agent
            context_filter_start = time.perf_counter()
            filtered_context = self._context_manager.filter_context_for_agent(agent_type, full_context)
            context_filter_time = (time.perf_counter() - context_filter_start) * 1000
            
            # Calculate filtered context size
            filtered_context_size = self._context_manager.get_context_size_estimate(filtered_context)
            token_reduction_percent = ((original_context_size - filtered_context_size) / original_context_size * 100) if original_context_size > 0 else 0
            
            logger.info("context_filtered", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "filter_time_ms": context_filter_time,
                "original_tokens": original_context_size,
                "filtered_tokens": filtered_context_size,
                "reduction_percent": token_reduction_percent,
                "files_after_filter": len(filtered_context.get("files", {}))
            })
            
            # Create request data
            request_data = {
                "agent_type": agent_type,
                "task": task_description,
                "context": filtered_context,
                "requirements": kwargs.get("requirements", []),
                "deliverables": kwargs.get("deliverables", []),
                "priority": kwargs.get("priority", "medium"),
                "task_id": task_id
            }
            
            # Ensure message bus is initialized
            if not self._message_bus:
                self._message_bus = SimpleMessageBus()
                AgentHandlerManager.register_default_handlers(self._message_bus)
                logger.debug("message_bus_initialized_in_local_orchestration")
            
            # Route through message bus
            routing_start = time.perf_counter()
            response = await self._message_bus.send_request(
                agent_id=agent_type,
                request_data=request_data,
                timeout=kwargs.get('timeout_seconds') or 300
            )
            routing_time = (time.perf_counter() - routing_start) * 1000
            
            # Determine return code based on response
            if response.status != MessageStatus.COMPLETED:
                if response.status == MessageStatus.TIMEOUT:
                    return_code = ReturnCode.TIMEOUT
                elif response.error and "context" in response.error.lower():
                    return_code = ReturnCode.CONTEXT_FILTERING_ERROR
                else:
                    return_code = ReturnCode.MESSAGE_BUS_ERROR
            
            logger.info("message_bus_routing_complete", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "routing_time_ms": routing_time,
                "response_status": response.status.value,
                "return_code": return_code
            })
            
            # Format response for compatibility
            result = {
                "success": response.status == MessageStatus.COMPLETED,
                "subprocess_id": subprocess_id,
                "subprocess_info": {
                    "subprocess_id": subprocess_id,
                    "agent_type": agent_type,
                    "task_description": task_description,
                    "generated_prompt": self._format_agent_prompt(
                        agent_type, task_description, agent_prompt, **kwargs
                    ),
                    "creation_time": datetime.now().isoformat(),
                    "status": "completed" if response.status == MessageStatus.COMPLETED else "failed",
                    "requirements": kwargs.get("requirements", []),
                    "deliverables": kwargs.get("deliverables", []),
                    "priority": kwargs.get("priority", "medium"),
                    "orchestration_mode": "LOCAL",  # Emphasize LOCAL mode
                    "task_id": task_id,
                    "performance_note": "Executed instantly using LOCAL orchestration"
                },
                "prompt": self._format_agent_prompt(
                    agent_type, task_description, agent_prompt, **kwargs
                ),
                "usage_instructions": self._generate_local_usage_instructions(
                    subprocess_id, agent_type, response
                ),
                "local_orchestration": {
                    "context_filtering_ms": context_filter_time,
                    "message_routing_ms": routing_time,
                    "response_status": response.status.value,
                    "filtered_context_size": filtered_context_size,
                    "context_size_original": original_context_size,
                    "context_size_filtered": filtered_context_size,
                    "token_reduction_percent": token_reduction_percent,
                    "agent_tier": agent_tier,
                    "agent_prompt_loading_ms": agent_prompt_time
                },
                "return_code": return_code
            }
            
            # Include error if present
            if response.error:
                result["error"] = response.error
            
            # Include results if present
            if response.data and "result" in response.data:
                result["results"] = response.data["result"]
            
            logger.info("local_orchestration_complete", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "subprocess_id": subprocess_id,
                "return_code": return_code,
                "total_time_ms": context_filter_time + routing_time
            })
            
            return result, return_code
            
        except Exception as e:
            if return_code == ReturnCode.SUCCESS:
                return_code = ReturnCode.GENERAL_FAILURE
                
            logger.error("local_orchestration_failed", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "return_code": return_code
            })
            
            # Return error result
            return {
                "success": False,
                "error": str(e),
                "return_code": return_code,
                "task_id": task_id,
                "subprocess_info": {
                    "agent_type": agent_type,
                    "task_description": task_description,
                    "status": "failed",
                    "orchestration_mode": "LOCAL",
                    "error": str(e)
                }
            }, return_code
    
    def _get_agent_prompt_with_hierarchy(self, agent_type: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get agent prompt from registry with hierarchy information.
        
        Returns:
            Tuple of (agent_prompt, tier) where tier is 'project', 'user', or 'system'
        """
        try:
            if not self._prompt_cache:
                self._prompt_cache = SharedPromptCache.get_instance()
            
            if not self._agent_registry:
                # Initialize agent registry if needed
                cache = SharedPromptCache.get_instance()
                self._agent_registry = AgentRegistry(cache_service=cache)
                
            # Discover all agents to ensure we have the latest
            all_agents = self._agent_registry.discover_agents()
            
            # Find the agent with proper hierarchy precedence
            agent_metadata = None
            agent_tier = None
            
            for agent_name, metadata in all_agents.items():
                if metadata.type == agent_type:
                    # Apply hierarchy precedence: project > user > system
                    if metadata.tier == 'project':
                        agent_metadata = metadata
                        agent_tier = 'project'
                        break  # Project level has highest precedence
                    elif metadata.tier == 'user' and agent_tier != 'project':
                        agent_metadata = metadata
                        agent_tier = 'user'
                    elif metadata.tier == 'system' and agent_tier is None:
                        agent_metadata = metadata
                        agent_tier = 'system'
            
            if agent_metadata:
                # Try cache first
                cache_key = f"agent_prompt:{agent_type}:{agent_tier}"
                cached_prompt = self._prompt_cache.get(cache_key)
                if cached_prompt:
                    return cached_prompt, agent_tier
                
                # Load agent definition file
                agent_path = Path(agent_metadata.path)
                if agent_path.exists():
                    agent_content = agent_path.read_text()
                    # Cache for future use
                    self._prompt_cache.set(cache_key, agent_content, ttl=3600)
                    
                    logger.info("agent_prompt_loaded", extra={
                        "agent_type": agent_type,
                        "agent_tier": agent_tier,
                        "agent_path": str(agent_path),
                        "specializations": agent_metadata.specializations
                    })
                    
                    return agent_content, agent_tier
                else:
                    # Fallback to basic prompt from metadata
                    basic_prompt = f"{agent_metadata.description}\n\nSpecializations: {', '.join(agent_metadata.specializations or [])}"
                    self._prompt_cache.set(cache_key, basic_prompt, ttl=3600)
                    return basic_prompt, agent_tier
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting agent prompt with hierarchy: {e}")
            return None, None
    
    def _format_agent_prompt(
        self,
        agent_type: str,
        task_description: str,
        base_prompt: str,
        **kwargs
    ) -> str:
        """Format agent prompt with task details."""
        # Get current date for temporal context
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Format requirements
        requirements = kwargs.get("requirements", [])
        requirements_text = "\n".join(f"- {req}" for req in requirements) if requirements else "None specified"
        
        # Format deliverables
        deliverables = kwargs.get("deliverables", [])
        deliverables_text = "\n".join(f"- {dlv}" for dlv in deliverables) if deliverables else "None specified"
        
        # Build formatted prompt
        formatted_prompt = f"""**{agent_type.title()} Agent**: {task_description}

TEMPORAL CONTEXT: Today is {current_date}. Apply date awareness to task execution.

**Task**: {task_description}

**Requirements**:
{requirements_text}

**Deliverables**:
{deliverables_text}

Priority: {kwargs.get('priority', 'medium')}

**Base Agent Instructions**:
{base_prompt}

**Integration Notes**: {kwargs.get('integration_notes', 'None')}
"""
        
        return formatted_prompt
    
    async def _collect_full_context(self) -> Dict[str, Any]:
        """
        Collect the full context for the current working directory.
        
        This includes:
        - Project files and structure
        - CLAUDE.md instructions
        - Current task information
        - Git status and recent commits
        - Active tickets
        """
        context = {
            "working_directory": str(self.working_directory),
            "timestamp": datetime.now().isoformat(),
            "files": {},
        }
        
        try:
            # Collect CLAUDE.md files
            claude_md_files = {}
            
            # Check for project CLAUDE.md
            project_claude = self.working_directory / "CLAUDE.md"
            if project_claude.exists():
                claude_md_files[str(project_claude)] = project_claude.read_text()
            
            # Check for parent CLAUDE.md
            parent_claude = self.working_directory.parent / "CLAUDE.md"
            if parent_claude.exists():
                claude_md_files[str(parent_claude)] = parent_claude.read_text()
            
            # Check for framework CLAUDE.md
            framework_claude = Path(__file__).parent.parent.parent / "framework" / "CLAUDE.md"
            if framework_claude.exists():
                claude_md_files[str(framework_claude)] = framework_claude.read_text()
            
            if claude_md_files:
                context["files"].update(claude_md_files)
                context["claude_md_content"] = claude_md_files
            
            # Collect project structure information
            # For now, we'll add a simplified version - in production this would be more comprehensive
            context["project_structure"] = {
                "type": "python_project",
                "has_git": (self.working_directory / ".git").exists(),
                "has_tests": (self.working_directory / "tests").exists(),
                "main_directories": []
            }
            
            # Add main directories
            for item in self.working_directory.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    context["project_structure"]["main_directories"].append(item.name)
            
            # Add any active task information from shared context if available
            if hasattr(self, "_task_context"):
                context["current_task"] = self._task_context
            
            logger.debug(f"Collected full context with {len(context['files'])} files")
            
        except Exception as e:
            logger.error(f"Error collecting full context: {e}")
            # Return minimal context on error
            return {
                "working_directory": str(self.working_directory),
                "timestamp": datetime.now().isoformat(),
                "error": f"Context collection error: {str(e)}"
            }
        
        return context
    
    def _generate_local_usage_instructions(
        self,
        subprocess_id: str,
        agent_type: str,
        response
    ) -> str:
        """Generate usage instructions for local orchestration."""
        return f"""
Local Orchestration Execution Instructions:
===========================================

Subprocess ID: {subprocess_id}
Agent Type: {agent_type}
Orchestration Mode: LOCAL
Response Status: {response.status.value.upper()}

This task was executed using local orchestration:
- Context was automatically filtered for the agent type
- Message was routed through the internal message bus
- No external subprocess was created

Results:
{'-' * 50}
Status: {response.status.value.upper()}
{f"Error: {response.error}" if response.error else "Success"}
{f"Results: {response.data.get('result', '')}" if response.data and 'result' in response.data else ""}
{'-' * 50}

Integration Notes:
- This execution used in-process orchestration
- Context filtering reduced data transfer overhead
- Performance metrics are included in orchestration_metadata
"""