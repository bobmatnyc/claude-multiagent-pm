"""
Backwards Compatible Orchestrator
=================================

This module provides a refactored backwards-compatible orchestration wrapper that
seamlessly integrates local orchestration capabilities while maintaining 100%
compatibility with existing subprocess delegation patterns.
"""

import os
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Import refactored modules
from .types import OrchestrationMode, ReturnCode, OrchestrationMetrics
from .mode_detection import ModeDetector
from .local_execution import LocalExecutor
from .subprocess_execution import SubprocessExecutor
from .agent_handlers import register_default_agent_handlers
from .context_collection import ContextCollector
from .compatibility import CompatibilityValidator

# Import existing components for compatibility
from claude_pm.core.response_types import TaskToolResponse
from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration
from claude_pm.services.agent_registry_sync import AgentRegistry
from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.core.agent_keyword_parser import AgentKeywordParser

# Import orchestration components
from ..orchestration_detector import OrchestrationDetector
from ..message_bus import SimpleMessageBus
from ..context_manager import create_context_manager

logger = logging.getLogger(__name__)


class BackwardsCompatibleOrchestrator:
    """
    Orchestrator that provides local orchestration with full backwards compatibility.
    
    This orchestrator automatically determines whether to use local orchestration
    or subprocess delegation based on environment configuration and availability.
    """
    
    def __init__(
        self, 
        working_directory: Optional[str] = None,
        config: Optional[TaskToolConfiguration] = None
    ):
        """
        Initialize the backwards compatible orchestrator.
        
        Args:
            working_directory: Working directory for operations
            config: Task tool configuration
        """
        self.working_directory = Path(working_directory) if working_directory else Path.cwd()
        self.config = config or TaskToolConfiguration()
        
        # Initialize components
        self.detector = OrchestrationDetector()
        self._mode_detector = ModeDetector()
        self._local_executor = LocalExecutor()
        self._subprocess_executor = SubprocessExecutor(working_directory, config)
        self._context_collector = ContextCollector(self.working_directory)
        self._compatibility_validator = CompatibilityValidator()
        
        # Component instances (lazy initialization)
        self._message_bus = None
        self._context_manager = None
        self._agent_registry = None
        self._task_tool_helper = None
        
        # Metrics tracking
        self._orchestration_metrics: List[OrchestrationMetrics] = []
        self.metrics = OrchestrationMetrics()
        
        # Force mode for testing
        self.force_mode = None
        
        logger.info("BackwardsCompatibleOrchestrator initialized", extra={
            "working_directory": str(self.working_directory),
            "timeout_seconds": self.config.timeout_seconds
        })
    
    async def delegate_to_agent(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Delegate a task to an agent with automatic orchestration mode selection.
        
        This method maintains full API compatibility with TaskToolHelper.create_agent_subprocess
        while providing transparent local orchestration when available.
        
        Args:
            agent_type: Type of agent to delegate to
            task_description: Description of the task
            **kwargs: Additional arguments (requirements, deliverables, etc.)
            
        Returns:
            Tuple of (result_dict, return_code) matching subprocess behavior
        """
        # Generate task ID if not provided
        task_id = kwargs.get("task_id", str(uuid.uuid4())[:8])
        
        # Record start time
        start_time = time.perf_counter()
        
        # Create metrics entry
        current_metric = OrchestrationMetrics()
        current_metric.agent_type = agent_type
        current_metric.task_id = task_id
        
        try:
            # Determine orchestration mode
            decision_start = time.perf_counter()
            mode, fallback_reason = await self._mode_detector.determine_orchestration_mode()
            decision_time = (time.perf_counter() - decision_start) * 1000
            
            current_metric.mode = mode
            current_metric.fallback_reason = fallback_reason
            current_metric.decision_time_ms = decision_time
            
            # Update global metrics
            self.metrics.mode_determinations += 1
            if mode in [OrchestrationMode.LOCAL, OrchestrationMode.FORCED_LOCAL]:
                self.metrics.local_mode_selections += 1
            else:
                self.metrics.subprocess_mode_selections += 1
            
            logger.info("orchestration_mode_determined", extra={
                "mode": mode.value,
                "agent_type": agent_type,
                "task_id": task_id,
                "fallback_reason": fallback_reason,
                "decision_time_ms": decision_time
            })
            
            # Execute based on mode
            execution_start = time.perf_counter()
            
            if mode in [OrchestrationMode.LOCAL, OrchestrationMode.FORCED_LOCAL]:
                # Transfer components from mode detector
                self._local_executor._message_bus = self._mode_detector.message_bus
                self._local_executor._context_manager = self._mode_detector.context_manager
                self._local_executor._agent_registry = self._mode_detector.agent_registry
                self._local_executor.config = self.config
                
                # Register handlers if needed
                if self._local_executor._message_bus and not hasattr(self, '_handlers_registered'):
                    register_default_agent_handlers(self._local_executor._message_bus)
                    self._handlers_registered = True
                
                # Bind context collection method
                self._local_executor.collect_full_context = self._context_collector.collect_full_context
                
                try:
                    result, return_code = await self._local_executor.execute_local_orchestration(
                        agent_type=agent_type,
                        task_description=task_description,
                        **kwargs
                    )
                    
                    # Extract metrics from result
                    if "local_orchestration" in result:
                        local_metrics = result["local_orchestration"]
                        current_metric.context_filtering_time_ms = local_metrics.get("context_filtering_ms", 0)
                        current_metric.context_size_original = local_metrics.get("context_size_original", 0)
                        current_metric.context_size_filtered = local_metrics.get("context_size_filtered", 0)
                        current_metric.token_reduction_percent = local_metrics.get("token_reduction_percent", 0)
                        
                except Exception as e:
                    # Fallback to subprocess on local execution failure
                    logger.error("local_execution_failed_falling_back", extra={
                        "error": str(e),
                        "agent_type": agent_type,
                        "task_id": task_id
                    })
                    result, return_code = await self._subprocess_executor.execute_subprocess_delegation(
                        agent_type=agent_type,
                        task_description=task_description,
                        **kwargs
                    )
            else:
                result, return_code = await self._subprocess_executor.execute_subprocess_delegation(
                    agent_type=agent_type,
                    task_description=task_description,
                    **kwargs
                )
            
            execution_time = (time.perf_counter() - execution_start) * 1000
            total_time = (time.perf_counter() - start_time) * 1000
            
            # Update metrics
            current_metric.execution_time_ms = execution_time
            current_metric.total_time_ms = total_time
            current_metric.return_code = return_code
            current_metric.success = return_code == ReturnCode.SUCCESS
            
            # Update global metrics
            if return_code == ReturnCode.SUCCESS:
                self.metrics.successful_executions += 1
            else:
                self.metrics.failed_executions += 1
                
            self.metrics.total_execution_time += total_time
            
            if mode == OrchestrationMode.LOCAL:
                self.metrics.local_execution_times.append(execution_time)
            else:
                self.metrics.subprocess_execution_times.append(execution_time)
            
            # Track agent execution
            self.metrics.agent_execution_counts[agent_type] = \
                self.metrics.agent_execution_counts.get(agent_type, 0) + 1
            
            # Add orchestration metadata to result
            result["orchestration_metadata"] = {
                "mode": mode.value,
                "decision_time_ms": decision_time,
                "execution_time_ms": execution_time,
                "total_time_ms": total_time,
                "fallback_reason": fallback_reason
            }
            
            logger.info("orchestration_complete", extra={
                "mode": mode.value,
                "agent_type": agent_type,
                "task_id": task_id,
                "return_code": return_code,
                "execution_time_ms": execution_time,
                "total_time_ms": total_time,
                "success": return_code == ReturnCode.SUCCESS
            })
            
            # Track this orchestration
            self._orchestration_metrics.append(current_metric)
            
            return result, return_code
            
        except Exception as e:
            logger.error("orchestration_failed", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Update metrics for failure
            current_metric.success = False
            current_metric.return_code = ReturnCode.GENERAL_ERROR
            current_metric.error = str(e)
            self._orchestration_metrics.append(current_metric)
            
            # Emergency fallback
            return await self._subprocess_executor.emergency_subprocess_fallback(
                agent_type=agent_type,
                task_description=task_description,
                error=e,
                **kwargs
            )
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics."""
        return self._compatibility_validator.get_orchestration_metrics(self._orchestration_metrics)
    
    async def validate_compatibility(self) -> Dict[str, Any]:
        """Validate backwards compatibility with existing systems."""
        return await self._compatibility_validator.validate_compatibility(self)
    
    def set_force_mode(self, mode: Optional[OrchestrationMode]) -> None:
        """
        Force a specific orchestration mode (for testing).
        
        Args:
            mode: OrchestrationMode to force, or None to use auto-detection
        """
        self.force_mode = mode
        self._mode_detector.set_force_mode(mode)
        logger.info(f"Orchestration mode forced to: {mode.value if mode else 'auto-detection'}")


# Convenience functions for drop-in replacement
async def create_backwards_compatible_orchestrator(
    working_directory: Optional[str] = None,
    config: Optional[TaskToolConfiguration] = None
) -> BackwardsCompatibleOrchestrator:
    """
    Create a backwards compatible orchestrator instance.
    
    This is a convenience function for easy initialization.
    """
    return BackwardsCompatibleOrchestrator(
        working_directory=working_directory,
        config=config
    )


async def delegate_with_compatibility(
    agent_type: str,
    task_description: str,
    working_directory: Optional[str] = None,
    **kwargs
) -> Tuple[Dict[str, Any], int]:
    """
    Delegate a task with automatic backwards compatible orchestration.
    
    This is a convenience function that creates an orchestrator and delegates.
    """
    orchestrator = BackwardsCompatibleOrchestrator(working_directory=working_directory)
    return await orchestrator.delegate_to_agent(
        agent_type=agent_type,
        task_description=task_description,
        **kwargs
    )


# Export key classes and functions
__all__ = [
    'BackwardsCompatibleOrchestrator',
    'OrchestrationMode',
    'ReturnCode',
    'create_backwards_compatible_orchestrator',
    'delegate_with_compatibility'
]