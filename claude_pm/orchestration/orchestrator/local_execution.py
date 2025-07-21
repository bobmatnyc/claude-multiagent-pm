"""
Local Orchestration Execution
============================

Handles execution of agent tasks using local orchestration for instant responses.
"""

import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

from .types import ReturnCode
from ..message_bus import SimpleMessageBus, MessageStatus
from ..context_manager import create_context_manager

logger = logging.getLogger(__name__)


class LocalExecutor:
    """Handles local orchestration execution for instant agent responses."""
    
    def __init__(self, message_bus: Optional[SimpleMessageBus] = None, 
                 context_manager=None, agent_registry=None, config=None):
        self._message_bus = message_bus
        self._context_manager = context_manager
        self._agent_registry = agent_registry
        self.config = config
        
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
            agent_prompt, agent_tier = self.get_agent_prompt_with_hierarchy(agent_type)
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
            full_context = await self.collect_full_context()
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
                # Note: agent handlers should be registered by caller
                logger.debug("message_bus_initialized_in_local_orchestration")
            
            # Route through message bus
            routing_start = time.perf_counter()
            response = await self._message_bus.send_request(
                agent_id=agent_type,
                request_data=request_data,
                timeout=kwargs.get('timeout_seconds') or self.config.timeout_seconds
            )
            routing_time = (time.perf_counter() - routing_start) * 1000
            
            # Determine return code based on response
            if response.status != MessageStatus.COMPLETED:
                if response.status == MessageStatus.TIMEOUT:
                    return_code = ReturnCode.TIMEOUT
                elif response.error and "context" in response.error.lower():
                    return_code = ReturnCode.GENERAL_ERROR  # Simplified from CONTEXT_FILTERING_ERROR
                else:
                    return_code = ReturnCode.GENERAL_ERROR  # Simplified from MESSAGE_BUS_ERROR
            
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
                    "generated_prompt": self.format_agent_prompt(
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
                "prompt": self.format_agent_prompt(
                    agent_type, task_description, agent_prompt, **kwargs
                ),
                "usage_instructions": self.generate_local_usage_instructions(
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
                return_code = ReturnCode.GENERAL_ERROR
                
            logger.error("local_orchestration_failed", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "return_code": return_code
            })
            
            # Return error result (caller should handle fallback)
            raise e
    
    def get_agent_prompt_with_hierarchy(self, agent_type: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get agent prompt from registry using proper hierarchy.
        
        Returns:
            Tuple of (prompt, tier) where tier indicates which level the agent was found at
        """
        if not self._agent_registry:
            return None, None
            
        try:
            # Get the agent from registry (it handles hierarchy internally)
            agent = self._agent_registry.get_agent(agent_type)
            
            if agent and hasattr(agent, 'prompt'):
                # Return the prompt and tier information
                tier = getattr(agent, 'tier', 'unknown')
                return agent.prompt, tier
            
            # Try loading as markdown file
            agents_discovered = self._agent_registry.discover_agents()
            for agent_name, agent_meta in agents_discovered.items():
                if agent_meta.type == agent_type or agent_name == agent_type:
                    # Found the agent, load its prompt
                    if hasattr(agent_meta, 'prompt') and agent_meta.prompt:
                        return agent_meta.prompt, agent_meta.tier
                    
                    # Try to load from file if prompt not cached
                    try:
                        with open(agent_meta.path, 'r') as f:
                            prompt_content = f.read()
                            return prompt_content, agent_meta.tier
                    except Exception as e:
                        logger.error(f"Failed to load agent prompt from {agent_meta.path}: {e}")
                        
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting agent prompt with hierarchy: {e}")
            return None, None
    
    async def collect_full_context(self) -> Dict[str, Any]:
        """
        Collect full context for agent execution.
        
        This should be implemented based on specific context needs.
        """
        # This is a placeholder - actual implementation depends on context manager
        return {
            "files": {},
            "memory": {},
            "working_directory": "",
            "project_info": {}
        }
    
    def format_agent_prompt(
        self,
        agent_type: str,
        task_description: str,
        agent_prompt: str,
        **kwargs
    ) -> str:
        """Format the agent prompt with task details."""
        # Build the formatted prompt
        formatted_parts = [
            f"**{agent_type.title()} Agent**: {task_description}",
            "",
            "## Task Details:"
        ]
        
        if kwargs.get("requirements"):
            formatted_parts.extend([
                "### Requirements:",
                *[f"- {req}" for req in kwargs["requirements"]],
                ""
            ])
            
        if kwargs.get("deliverables"):
            formatted_parts.extend([
                "### Expected Deliverables:",
                *[f"- {deliv}" for deliv in kwargs["deliverables"]],
                ""
            ])
            
        if kwargs.get("priority"):
            formatted_parts.append(f"### Priority: {kwargs['priority']}")
            formatted_parts.append("")
            
        # Add the agent prompt
        formatted_parts.extend([
            "## Agent Context:",
            agent_prompt
        ])
        
        return "\n".join(formatted_parts)
    
    def generate_local_usage_instructions(
        self,
        subprocess_id: str,
        agent_type: str,
        response
    ) -> str:
        """Generate usage instructions for local orchestration results."""
        instructions = [
            f"# LOCAL Orchestration Response ({subprocess_id})",
            f"Agent Type: {agent_type}",
            f"Status: {response.status.value}",
            f"Mode: LOCAL (instant execution)",
            "",
            "## How to use this response:",
            "1. This was executed locally for instant response",
            "2. Review the results/output provided",
            "3. The task has been processed by the local orchestrator",
            ""
        ]
        
        if response.status == MessageStatus.COMPLETED:
            instructions.extend([
                "## Success:",
                "The agent successfully processed your request.",
                "Check the 'results' field for the agent's output."
            ])
        else:
            instructions.extend([
                "## Error:",
                f"The request failed with status: {response.status.value}"
            ])
            if response.error:
                instructions.append(f"Error details: {response.error}")
                
        return "\n".join(instructions)