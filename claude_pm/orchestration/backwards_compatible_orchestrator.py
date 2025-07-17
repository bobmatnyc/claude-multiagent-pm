"""
Backwards Compatible Orchestrator
=================================

This module provides a backwards-compatible orchestration wrapper that seamlessly
integrates local orchestration capabilities while maintaining 100% compatibility
with existing subprocess delegation patterns.

Key Features:
- Automatic detection of orchestration mode via OrchestrationDetector
- Transparent fallback to subprocess delegation when needed
- Complete API compatibility with existing TaskToolHelper
- Performance metrics and logging for mode selection
- Zero breaking changes to existing code

Usage:
    # Drop-in replacement for existing delegation
    orchestrator = BackwardsCompatibleOrchestrator()
    result = await orchestrator.delegate_to_agent(
        agent_type="engineer",
        task_description="Implement feature X",
        requirements=["Requirement 1", "Requirement 2"]
    )
    
    # Result has same structure as TaskToolHelper.create_agent_subprocess
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Import orchestration components
from .orchestration_detector import OrchestrationDetector
from .message_bus import SimpleMessageBus, Request, Response, MessageStatus
from .context_manager import ContextManager, create_context_manager

# Import existing components for compatibility
from claude_pm.core.response_types import TaskToolResponse
from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration
from claude_pm.services.agent_registry import AgentRegistry
from claude_pm.services.shared_prompt_cache import SharedPromptCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestrationMode(Enum):
    """Orchestration modes for the backwards compatible orchestrator."""
    LOCAL = "local"
    SUBPROCESS = "subprocess"
    HYBRID = "hybrid"


@dataclass
class OrchestrationMetrics:
    """Metrics for orchestration performance tracking."""
    mode: OrchestrationMode
    decision_time_ms: float
    execution_time_ms: float
    fallback_reason: Optional[str] = None
    context_filtering_time_ms: float = 0.0
    message_routing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/reporting."""
        return {
            "mode": self.mode.value,
            "decision_time_ms": self.decision_time_ms,
            "execution_time_ms": self.execution_time_ms,
            "fallback_reason": self.fallback_reason,
            "context_filtering_time_ms": self.context_filtering_time_ms,
            "message_routing_time_ms": self.message_routing_time_ms,
            "total_time_ms": self.decision_time_ms + self.execution_time_ms
        }


class BackwardsCompatibleOrchestrator:
    """
    Backwards Compatible Orchestrator with automatic mode selection.
    
    This orchestrator provides seamless integration of local orchestration
    capabilities while maintaining 100% backwards compatibility with existing
    subprocess delegation patterns.
    """
    
    def __init__(
        self, 
        working_directory: Optional[Path] = None,
        config: Optional[TaskToolConfiguration] = None,
        force_mode: Optional[OrchestrationMode] = None
    ):
        """
        Initialize the backwards compatible orchestrator.
        
        Args:
            working_directory: Working directory for operations
            config: Task tool configuration
            force_mode: Force a specific orchestration mode (for testing)
        """
        self.working_directory = Path(working_directory or os.getcwd())
        self.config = config or TaskToolConfiguration()
        self.force_mode = force_mode
        
        # Initialize orchestration detector
        self.detector = OrchestrationDetector()
        
        # Initialize components (lazy loading)
        self._message_bus: Optional[SimpleMessageBus] = None
        self._context_manager: Optional[ContextManager] = None
        self._task_tool_helper: Optional[TaskToolHelper] = None
        self._agent_registry: Optional[AgentRegistry] = None
        self._prompt_cache: Optional[SharedPromptCache] = None
        
        # Metrics tracking
        self._orchestration_metrics: List[OrchestrationMetrics] = []
        
        logger.info(f"BackwardsCompatibleOrchestrator initialized in {self.working_directory}")
    
    async def delegate_to_agent(
        self,
        agent_type: str,
        task_description: str,
        requirements: Optional[List[str]] = None,
        deliverables: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        priority: str = "medium",
        memory_categories: Optional[List[str]] = None,
        timeout_seconds: Optional[int] = None,
        escalation_triggers: Optional[List[str]] = None,
        integration_notes: str = "",
        model_override: Optional[str] = None,
        performance_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Delegate task to agent with automatic orchestration mode selection.
        
        This method maintains the exact same API as TaskToolHelper.create_agent_subprocess
        for 100% backwards compatibility.
        
        Args:
            Same as TaskToolHelper.create_agent_subprocess
            
        Returns:
            Same structure as TaskToolHelper.create_agent_subprocess
        """
        start_time = datetime.now()
        
        try:
            # Determine orchestration mode
            mode, fallback_reason = await self._determine_orchestration_mode()
            decision_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Selected orchestration mode: {mode.value}")
            if fallback_reason:
                logger.info(f"Fallback reason: {fallback_reason}")
            
            # Execute based on mode
            execution_start = datetime.now()
            
            if mode == OrchestrationMode.LOCAL:
                result = await self._execute_local_orchestration(
                    agent_type=agent_type,
                    task_description=task_description,
                    requirements=requirements,
                    deliverables=deliverables,
                    dependencies=dependencies,
                    priority=priority,
                    memory_categories=memory_categories,
                    timeout_seconds=timeout_seconds,
                    escalation_triggers=escalation_triggers,
                    integration_notes=integration_notes,
                    model_override=model_override,
                    performance_requirements=performance_requirements
                )
            else:
                # Fallback to subprocess delegation
                result = await self._execute_subprocess_delegation(
                    agent_type=agent_type,
                    task_description=task_description,
                    requirements=requirements,
                    deliverables=deliverables,
                    dependencies=dependencies,
                    priority=priority,
                    memory_categories=memory_categories,
                    timeout_seconds=timeout_seconds,
                    escalation_triggers=escalation_triggers,
                    integration_notes=integration_notes,
                    model_override=model_override,
                    performance_requirements=performance_requirements
                )
            
            execution_time = (datetime.now() - execution_start).total_seconds() * 1000
            
            # Record metrics
            metrics = OrchestrationMetrics(
                mode=mode,
                decision_time_ms=decision_time,
                execution_time_ms=execution_time,
                fallback_reason=fallback_reason
            )
            self._orchestration_metrics.append(metrics)
            
            # Add orchestration metadata to result
            if isinstance(result, dict) and "success" in result:
                result["orchestration_metadata"] = {
                    "mode": mode.value,
                    "metrics": metrics.to_dict()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in backwards compatible orchestration: {e}")
            # Always fallback to subprocess on error
            return await self._emergency_subprocess_fallback(
                agent_type=agent_type,
                task_description=task_description,
                error=str(e)
            )
    
    async def _determine_orchestration_mode(self) -> Tuple[OrchestrationMode, Optional[str]]:
        """
        Determine which orchestration mode to use.
        
        Returns:
            Tuple of (mode, fallback_reason)
        """
        # Check if mode is forced (for testing)
        if self.force_mode:
            return self.force_mode, "Forced mode for testing"
        
        # Check if orchestration is enabled
        is_enabled = self.detector.is_orchestration_enabled()
        if not is_enabled:
            return OrchestrationMode.SUBPROCESS, "CLAUDE_PM_ORCHESTRATION not enabled"
        
        # Verify all components are available
        try:
            # Check message bus
            if not self._message_bus:
                self._message_bus = SimpleMessageBus()
            
            # Check context manager
            if not self._context_manager:
                self._context_manager = create_context_manager()
            
            # Check agent registry
            if not self._agent_registry:
                cache = SharedPromptCache.get_instance()
                self._agent_registry = AgentRegistry(cache_service=cache)
            
            # All components available, use local orchestration
            return OrchestrationMode.LOCAL, None
            
        except Exception as e:
            logger.warning(f"Component initialization failed: {e}")
            return OrchestrationMode.SUBPROCESS, f"Component initialization failed: {str(e)}"
    
    async def _execute_local_orchestration(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute task using local orchestration.
        
        This method uses the new orchestration components while maintaining
        the same return structure as subprocess delegation.
        """
        try:
            logger.debug(f"Executing local orchestration for {agent_type}")
            
            # Generate subprocess ID for compatibility
            subprocess_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Get agent prompt from registry
            agent_prompt = await self._get_agent_prompt(agent_type)
            if not agent_prompt:
                raise ValueError(f"No agent prompt found for {agent_type}")
            
            # Collect current full context
            full_context = await self._collect_full_context()
            
            # Filter context for agent
            context_start = datetime.now()
            filtered_context = self._context_manager.filter_context_for_agent(agent_type, full_context)
            context_time = (datetime.now() - context_start).total_seconds() * 1000
            
            # Create request message
            request = Request(
                agent_id=agent_type,
                data={
                    "agent_type": agent_type,
                    "task": task_description,
                    "context": filtered_context,
                    "requirements": kwargs.get("requirements", []),
                    "deliverables": kwargs.get("deliverables", []),
                    "priority": kwargs.get("priority", "medium")
                }
            )
            
            # Route through message bus
            routing_start = datetime.now()
            response = await self._message_bus.route_message(request)
            routing_time = (datetime.now() - routing_start).total_seconds() * 1000
            
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
                    "orchestration_mode": "local"
                },
                "prompt": self._format_agent_prompt(
                    agent_type, task_description, agent_prompt, **kwargs
                ),
                "usage_instructions": self._generate_local_usage_instructions(
                    subprocess_id, agent_type, response
                ),
                "local_orchestration": {
                    "context_filtering_ms": context_time,
                    "message_routing_ms": routing_time,
                    "response_status": response.status.value,
                    "filtered_context_size": len(filtered_context)
                }
            }
            
            # Include error if present
            if response.error:
                result["error"] = response.error
            
            # Include results if present
            if response.data and "result" in response.data:
                result["results"] = response.data["result"]
            
            logger.info(f"Local orchestration completed for {subprocess_id}")
            return result
            
        except Exception as e:
            logger.error(f"Local orchestration failed: {e}")
            # Fallback to subprocess
            return await self._execute_subprocess_delegation(
                agent_type=agent_type,
                task_description=task_description,
                **kwargs
            )
    
    async def _execute_subprocess_delegation(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute task using traditional subprocess delegation.
        
        This maintains full compatibility with existing code.
        """
        logger.debug(f"Executing subprocess delegation for {agent_type}")
        
        # Initialize task tool helper if needed
        if not self._task_tool_helper:
            self._task_tool_helper = TaskToolHelper(
                working_directory=self.working_directory,
                config=self.config
            )
        
        # Delegate to task tool helper
        return await self._task_tool_helper.create_agent_subprocess(
            agent_type=agent_type,
            task_description=task_description,
            **kwargs
        )
    
    async def _emergency_subprocess_fallback(
        self,
        agent_type: str,
        task_description: str,
        error: str
    ) -> Dict[str, Any]:
        """
        Emergency fallback to subprocess delegation with error information.
        """
        logger.warning(f"Emergency subprocess fallback due to: {error}")
        
        try:
            # Try subprocess delegation
            result = await self._execute_subprocess_delegation(
                agent_type=agent_type,
                task_description=task_description
            )
            
            # Add error context
            if isinstance(result, dict):
                result["orchestration_error"] = error
                result["fallback_mode"] = "emergency_subprocess"
            
            return result
            
        except Exception as e:
            # Ultimate fallback - return error response
            subprocess_id = f"error_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return TaskToolResponse(
                request_id=subprocess_id,
                success=False,
                error=f"Orchestration failed: {error}. Subprocess fallback also failed: {str(e)}",
                enhanced_prompt=f"**{agent_type.title()}**: {task_description}"
            )
    
    async def _get_agent_prompt(self, agent_type: str) -> Optional[str]:
        """Get agent prompt from registry."""
        try:
            if not self._prompt_cache:
                self._prompt_cache = SharedPromptCache.get_instance()
            
            # Try to get from cache first
            cache_key = f"agent_prompt:{agent_type}"
            cached_prompt = self._prompt_cache.get(cache_key)
            if cached_prompt:
                return cached_prompt
            
            # Load from agent registry
            if self._agent_registry:
                agent_metadata = await self._agent_registry.get_agent(agent_type)
                if agent_metadata:
                    # Load agent definition file
                    agent_path = Path(agent_metadata.path)
                    if agent_path.exists():
                        agent_content = agent_path.read_text()
                        # Cache for future use
                        cache_key = f"agent_prompt:{agent_type}"
                        self._prompt_cache.set(cache_key, agent_content, ttl=3600)
                        return agent_content
                    else:
                        # Fallback to basic prompt from metadata
                        basic_prompt = f"{agent_metadata.description}\n\nSpecializations: {', '.join(agent_metadata.specializations)}"
                        cache_key = f"agent_prompt:{agent_type}"
                        self._prompt_cache.set(cache_key, basic_prompt, ttl=3600)
                        return basic_prompt
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent prompt: {e}")
            return None
    
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
        response: Response
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
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics."""
        if not self._orchestration_metrics:
            return {
                "total_orchestrations": 0,
                "metrics": []
            }
        
        # Calculate statistics
        total = len(self._orchestration_metrics)
        local_count = sum(1 for m in self._orchestration_metrics if m.mode == OrchestrationMode.LOCAL)
        subprocess_count = sum(1 for m in self._orchestration_metrics if m.mode == OrchestrationMode.SUBPROCESS)
        
        avg_decision_time = sum(m.decision_time_ms for m in self._orchestration_metrics) / total
        avg_execution_time = sum(m.execution_time_ms for m in self._orchestration_metrics) / total
        
        return {
            "total_orchestrations": total,
            "local_orchestrations": local_count,
            "subprocess_orchestrations": subprocess_count,
            "average_decision_time_ms": avg_decision_time,
            "average_execution_time_ms": avg_execution_time,
            "recent_metrics": [m.to_dict() for m in self._orchestration_metrics[-10:]],
            "fallback_reasons": list(set(
                m.fallback_reason for m in self._orchestration_metrics 
                if m.fallback_reason
            ))
        }
    
    async def validate_compatibility(self) -> Dict[str, Any]:
        """Validate backwards compatibility with existing systems."""
        validation_results = {
            "compatible": True,
            "checks": {}
        }
        
        try:
            # Check API compatibility
            test_result = await self.delegate_to_agent(
                agent_type="test",
                task_description="Compatibility validation test"
            )
            
            # Check required fields in response
            required_fields = ["success", "subprocess_id", "subprocess_info", "prompt"]
            for field in required_fields:
                if field not in test_result:
                    validation_results["compatible"] = False
                    validation_results["checks"][f"field_{field}"] = False
                else:
                    validation_results["checks"][f"field_{field}"] = True
            
            # Check orchestration detector
            validation_results["checks"]["detector_available"] = self.detector is not None
            validation_results["checks"]["orchestration_enabled"] = self.detector.is_orchestration_enabled()
            
            # Check component availability
            validation_results["checks"]["message_bus_available"] = self._message_bus is not None
            validation_results["checks"]["context_manager_available"] = self._context_manager is not None
            
            # Check metrics
            metrics = self.get_orchestration_metrics()
            validation_results["checks"]["metrics_tracking"] = metrics["total_orchestrations"] > 0
            
        except Exception as e:
            validation_results["compatible"] = False
            validation_results["error"] = str(e)
        
        return validation_results
    
    def set_force_mode(self, mode: Optional[OrchestrationMode]) -> None:
        """
        Force a specific orchestration mode (for testing).
        
        Args:
            mode: Orchestration mode to force, or None to auto-detect
        """
        self.force_mode = mode
        logger.info(f"Force mode set to: {mode.value if mode else 'auto-detect'}")


# Convenience functions for drop-in replacement

async def create_backwards_compatible_orchestrator(
    working_directory: Optional[Path] = None,
    config: Optional[TaskToolConfiguration] = None
) -> BackwardsCompatibleOrchestrator:
    """
    Create a backwards compatible orchestrator instance.
    
    This is a drop-in replacement for TaskToolHelper initialization.
    """
    return BackwardsCompatibleOrchestrator(
        working_directory=working_directory,
        config=config
    )


async def delegate_with_compatibility(
    agent_type: str,
    task_description: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick delegation helper with automatic orchestration mode selection.
    
    This is a drop-in replacement for quick_create_subprocess.
    """
    orchestrator = BackwardsCompatibleOrchestrator()
    return await orchestrator.delegate_to_agent(
        agent_type=agent_type,
        task_description=task_description,
        **kwargs
    )