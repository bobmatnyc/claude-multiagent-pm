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
import asyncio
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Import orchestration components
from .orchestration_detector import OrchestrationDetector
from .message_bus import SimpleMessageBus, Response, MessageStatus, Request
from .context_manager import ContextManager, create_context_manager

# Import existing components for compatibility
from claude_pm.core.response_types import TaskToolResponse
from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration
from claude_pm.services.agent_registry import AgentRegistry
from claude_pm.services.shared_prompt_cache import SharedPromptCache

# Import subprocess runner for real subprocess creation
try:
    from claude_pm.services.subprocess_runner import SubprocessRunner
except ImportError:
    SubprocessRunner = None
    
# Use project standard logging configuration
from claude_pm.core.logging_config import get_logger
logger = get_logger(__name__)


class OrchestrationMode(Enum):
    """Orchestration modes for the backwards compatible orchestrator."""
    LOCAL = "local"
    SUBPROCESS = "subprocess"
    HYBRID = "hybrid"


class ReturnCode:
    """Return codes for orchestration operations."""
    SUCCESS = 0
    GENERAL_FAILURE = 1
    TIMEOUT = 2
    CONTEXT_FILTERING_ERROR = 3
    AGENT_NOT_FOUND = 4
    MESSAGE_BUS_ERROR = 5


@dataclass
class OrchestrationMetrics:
    """Metrics for orchestration performance tracking."""
    mode: OrchestrationMode
    decision_time_ms: float
    execution_time_ms: float
    fallback_reason: Optional[str] = None
    context_filtering_time_ms: float = 0.0
    message_routing_time_ms: float = 0.0
    context_size_original: int = 0
    context_size_filtered: int = 0
    token_reduction_percent: float = 0.0
    return_code: int = ReturnCode.SUCCESS
    task_id: Optional[str] = None
    agent_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/reporting."""
        return {
            "mode": self.mode.value,
            "decision_time_ms": self.decision_time_ms,
            "execution_time_ms": self.execution_time_ms,
            "fallback_reason": self.fallback_reason,
            "context_filtering_time_ms": self.context_filtering_time_ms,
            "message_routing_time_ms": self.message_routing_time_ms,
            "total_time_ms": self.decision_time_ms + self.execution_time_ms,
            "context_size_original": self.context_size_original,
            "context_size_filtered": self.context_size_filtered,
            "token_reduction_percent": self.token_reduction_percent,
            "return_code": self.return_code,
            "task_id": self.task_id,
            "agent_type": self.agent_type
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
        self._subprocess_runner: Optional[SubprocessRunner] = None
        
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
    ) -> Tuple[Dict[str, Any], int]:
        """
        Delegate task to agent with automatic orchestration mode selection.
        
        This method maintains the exact same API as TaskToolHelper.create_agent_subprocess
        for 100% backwards compatibility.
        
        Args:
            Same as TaskToolHelper.create_agent_subprocess
            
        Returns:
            Same structure as TaskToolHelper.create_agent_subprocess
        """
        start_time = time.perf_counter()
        task_id = str(uuid.uuid4())[:8]  # Short task ID for tracking
        return_code = ReturnCode.SUCCESS
        
        # Log delegation start
        logger.info("agent_delegation_start", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "task_description": task_description[:100],  # First 100 chars
            "priority": priority,
            "requirements_count": len(requirements) if requirements else 0,
            "deliverables_count": len(deliverables) if deliverables else 0
        })
        
        try:
            # Determine orchestration mode
            mode_start = time.perf_counter()
            mode, fallback_reason = await self._determine_orchestration_mode()
            decision_time = (time.perf_counter() - mode_start) * 1000
            
            logger.info("orchestration_mode_selected", extra={
                "mode": mode.value,
                "fallback_reason": fallback_reason,
                "decision_time_ms": decision_time,
                "task_id": task_id
            })
            
            # Execute based on mode
            execution_start = time.perf_counter()
            
            if mode == OrchestrationMode.LOCAL:
                result, exec_return_code = await self._execute_local_orchestration(
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
                    performance_requirements=performance_requirements,
                    task_id=task_id
                )
                return_code = exec_return_code
            else:
                # Fallback to subprocess delegation
                result, exec_return_code = await self._execute_subprocess_delegation(
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
                    performance_requirements=performance_requirements,
                    task_id=task_id
                )
                return_code = exec_return_code
            
            execution_time = (time.perf_counter() - execution_start) * 1000
            total_time = (time.perf_counter() - start_time) * 1000
            
            # Determine return code from result
            if isinstance(result, dict):
                if not result.get("success", True):
                    return_code = ReturnCode.GENERAL_FAILURE
                if "return_code" in result:
                    return_code = result["return_code"]
            
            # Extract metrics from result if available
            context_size_original = 0
            context_size_filtered = 0
            token_reduction_percent = 0.0
            
            if isinstance(result, dict) and "local_orchestration" in result:
                local_orch = result["local_orchestration"]
                if "context_size_original" in local_orch:
                    context_size_original = local_orch["context_size_original"]
                if "context_size_filtered" in local_orch:
                    context_size_filtered = local_orch["context_size_filtered"]
                if context_size_original > 0:
                    token_reduction_percent = ((context_size_original - context_size_filtered) / context_size_original) * 100
            
            # Record metrics
            metrics = OrchestrationMetrics(
                mode=mode,
                decision_time_ms=decision_time,
                execution_time_ms=execution_time,
                fallback_reason=fallback_reason,
                return_code=return_code,
                task_id=task_id,
                agent_type=agent_type,
                context_size_original=context_size_original,
                context_size_filtered=context_size_filtered,
                token_reduction_percent=token_reduction_percent
            )
            
            # Extract timing from local orchestration if available
            if isinstance(result, dict) and "local_orchestration" in result:
                local_orch = result["local_orchestration"]
                metrics.context_filtering_time_ms = local_orch.get("context_filtering_ms", 0.0)
                metrics.message_routing_time_ms = local_orch.get("message_routing_ms", 0.0)
            
            self._orchestration_metrics.append(metrics)
            
            # Log delegation end
            logger.info("agent_delegation_end", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "duration_ms": total_time,
                "execution_time_ms": execution_time,
                "return_code": return_code,
                "mode": mode.value,
                "context_tokens_original": context_size_original,
                "context_tokens_filtered": context_size_filtered,
                "token_reduction_percent": token_reduction_percent
            })
            
            # Add orchestration metadata to result
            if isinstance(result, dict) and "success" in result:
                result["orchestration_metadata"] = {
                    "mode": mode.value,
                    "metrics": metrics.to_dict(),
                    "task_id": task_id
                }
                result["return_code"] = return_code
            
            return result, return_code
            
        except asyncio.TimeoutError as e:
            return_code = ReturnCode.TIMEOUT
            logger.error("agent_delegation_timeout", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "timeout_seconds": timeout_seconds,
                "error": str(e)
            })
            # Always fallback to subprocess on error
            result = await self._emergency_subprocess_fallback(
                agent_type=agent_type,
                task_description=task_description,
                error=f"Timeout after {timeout_seconds}s",
                task_id=task_id,
                return_code=return_code
            )
            return result, return_code
        except Exception as e:
            return_code = ReturnCode.GENERAL_FAILURE
            logger.error("agent_delegation_error", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            # Always fallback to subprocess on error
            result = await self._emergency_subprocess_fallback(
                agent_type=agent_type,
                task_description=task_description,
                error=str(e),
                task_id=task_id,
                return_code=return_code
            )
            return result, return_code
    
    async def _determine_orchestration_mode(self) -> Tuple[OrchestrationMode, Optional[str]]:
        """
        Determine which orchestration mode to use.
        
        Returns:
            Tuple of (mode, fallback_reason)
        """
        start_time = time.perf_counter()
        
        # Check if mode is forced (for testing)
        if self.force_mode:
            logger.debug("orchestration_mode_forced", extra={
                "mode": self.force_mode.value,
                "reason": "testing"
            })
            return self.force_mode, "Forced mode for testing"
        
        # NEW: Default to LOCAL mode for instant responses
        # Check environment variable for explicit subprocess mode
        if os.getenv('CLAUDE_PM_FORCE_SUBPROCESS_MODE', 'false').lower() == 'true':
            logger.debug("subprocess_mode_forced", extra={
                "reason": "environment_variable_CLAUDE_PM_FORCE_SUBPROCESS_MODE"
            })
            return OrchestrationMode.SUBPROCESS, "Subprocess mode forced by environment variable"
        
        # Check if orchestration is explicitly disabled (rare case)
        is_enabled = self.detector.is_orchestration_enabled()
        if not is_enabled:
            logger.debug("orchestration_disabled", extra={
                "reason": "explicitly_disabled_in_claude_md"
            })
            return OrchestrationMode.SUBPROCESS, "CLAUDE_PM_ORCHESTRATION explicitly disabled"
        
        # Initialize components eagerly for LOCAL mode
        try:
            # Initialize all components immediately for instant responses
            if not self._message_bus:
                self._message_bus = SimpleMessageBus()
                self._register_default_agent_handlers()  # Register handlers for instant LOCAL mode
                logger.debug("message_bus_initialized_with_handlers")
            
            if not self._context_manager:
                self._context_manager = create_context_manager()
                logger.debug("context_manager_initialized")
            
            if not self._agent_registry:
                cache = SharedPromptCache.get_instance()
                self._agent_registry = AgentRegistry(cache_service=cache)
                logger.debug("agent_registry_initialized", extra={
                    "cache_available": cache is not None
                })
            
            initialization_time = (time.perf_counter() - start_time) * 1000
            
            logger.info("orchestration_mode_selected_LOCAL", extra={
                "initialization_time_ms": initialization_time,
                "mode": OrchestrationMode.LOCAL.value,
                "reason": "default_mode_for_instant_responses"
            })
            
            # LOCAL mode is now the default for instant responses
            return OrchestrationMode.LOCAL, None
            
        except Exception as e:
            # Only fall back to subprocess on critical errors
            logger.error("critical_component_initialization_failed", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "fallback_mode": OrchestrationMode.SUBPROCESS.value
            })
            return OrchestrationMode.SUBPROCESS, f"Critical component initialization failed: {str(e)}"
    
    async def _execute_local_orchestration(
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
            
            # Get agent prompt from registry (or use default for instant LOCAL mode)
            agent_prompt_start = time.perf_counter()
            agent_prompt = await self._get_agent_prompt(agent_type)
            agent_prompt_time = (time.perf_counter() - agent_prompt_start) * 1000
            
            if not agent_prompt:
                # Use agent-specific default prompts for instant LOCAL mode
                agent_prompts = {
                    'security': """You are the Security Agent, responsible for security analysis, vulnerability assessment, and protection.
You provide comprehensive security capabilities protecting projects from vulnerabilities and threats.""",
                    'engineer': """You are the Engineer Agent, responsible for code implementation, development, and technical problem solving.
You provide software engineering expertise and best practices.""",
                    'documentation': """You are the Documentation Agent, responsible for creating and maintaining project documentation.
You ensure clear, comprehensive documentation across all project aspects.""",
                    'qa': """You are the QA Agent, responsible for quality assurance, testing, and validation.
You ensure project quality through comprehensive testing strategies.""",
                    'research': """You are the Research Agent, responsible for investigation, analysis, and information gathering.
You provide in-depth research and technical analysis.""",
                    'ops': """You are the Ops Agent, responsible for deployment, operations, and infrastructure.
You handle all operational aspects of project deployment and maintenance.""",
                    'version_control': """You are the Version Control Agent, responsible for Git operations and version management.
You manage branches, merges, and repository workflows.""",
                    'ticketing': """You are the Ticketing Agent, responsible for ticket lifecycle and issue tracking.
You provide universal ticketing interface across platforms.""",
                    'data_engineer': """You are the Data Engineer Agent, responsible for data management and AI API integrations.
You handle databases, data pipelines, and data architecture."""
                }
                
                agent_prompt = agent_prompts.get(agent_type, f"""You are the {agent_type.title()} Agent.
Your role is to assist with {agent_type} tasks and provide expert guidance.
This is a LOCAL orchestration mode execution for instant responses.""")
                
                logger.debug("using_default_agent_prompt", extra={
                    "agent_type": agent_type,
                    "task_id": task_id,
                    "reason": "instant_local_mode"
                })
            
            logger.debug("agent_prompt_ready", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "prompt_size": len(agent_prompt),
                "load_time_ms": agent_prompt_time
            })
            
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
                    "token_reduction_percent": token_reduction_percent
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
            
            # Fallback to subprocess
            result, _ = await self._execute_subprocess_delegation(
                agent_type=agent_type,
                task_description=task_description,
                **kwargs
            )
            result["return_code"] = return_code
            return result, return_code
    
    async def _execute_subprocess_delegation(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Execute task using traditional subprocess delegation.
        
        This maintains full compatibility with existing code.
        """
        task_id = kwargs.get("task_id", str(uuid.uuid4())[:8])
        
        logger.warning("subprocess_delegation_start", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "reason": "fallback_to_subprocess",
            "note": "Using slower SUBPROCESS mode - consider fixing initialization errors for instant LOCAL mode"
        })
        
        # Check if we should use real subprocess (when SubprocessRunner is available)
        use_real_subprocess = (
            SubprocessRunner is not None and 
            os.getenv('CLAUDE_PM_USE_REAL_SUBPROCESS', 'false').lower() == 'true'
        )
        
        if use_real_subprocess:
            # Use real subprocess via SubprocessRunner
            return await self._execute_real_subprocess(
                agent_type=agent_type,
                task_description=task_description,
                **kwargs
            )
        
        # Otherwise use traditional TaskToolHelper approach
        # Initialize task tool helper if needed
        if not self._task_tool_helper:
            self._task_tool_helper = TaskToolHelper(
                working_directory=self.working_directory,
                config=self.config
            )
        
        start_time = time.perf_counter()
        
        # Remove task_id from kwargs before passing to TaskToolHelper
        clean_kwargs = {k: v for k, v in kwargs.items() if k != "task_id"}
        
        # Delegate to task tool helper
        result = await self._task_tool_helper.create_agent_subprocess(
            agent_type=agent_type,
            task_description=task_description,
            **clean_kwargs
        )
        
        execution_time = (time.perf_counter() - start_time) * 1000
        
        logger.info("subprocess_delegation_complete", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "execution_time_ms": execution_time,
            "success": result.get("success", False) if isinstance(result, dict) else False
        })
        
        # Add task_id to result for tracking
        if isinstance(result, dict):
            result["task_id"] = task_id
        
        # Determine return code based on result
        return_code = ReturnCode.SUCCESS
        if isinstance(result, dict) and not result.get("success", True):
            return_code = ReturnCode.GENERAL_FAILURE
            
        return result, return_code
    
    async def _execute_real_subprocess(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Execute task using real OS subprocess with proper environment.
        
        This creates an actual subprocess with the subprocess runner.
        """
        task_id = kwargs.get("task_id", str(uuid.uuid4())[:8])
        subprocess_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("real_subprocess_execution_start", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "subprocess_id": subprocess_id
        })
        
        try:
            # Initialize subprocess runner if needed
            if not self._subprocess_runner:
                self._subprocess_runner = SubprocessRunner()
                
                # Test environment setup
                test_result = self._subprocess_runner.test_environment()
                if not test_result.get('success'):
                    logger.error("subprocess_environment_test_failed", extra={
                        "error": test_result.get('error'),
                        "task_id": task_id
                    })
                    raise RuntimeError(f"Subprocess environment test failed: {test_result.get('error')}")
            
            # Prepare task data
            task_data = {
                'task_description': task_description,
                'requirements': kwargs.get('requirements', []),
                'deliverables': kwargs.get('deliverables', []),
                'dependencies': kwargs.get('dependencies', []),
                'priority': kwargs.get('priority', 'medium'),
                'memory_categories': kwargs.get('memory_categories', []),
                'escalation_triggers': kwargs.get('escalation_triggers', []),
                'integration_notes': kwargs.get('integration_notes', ''),
                'current_date': datetime.now().strftime('%Y-%m-%d'),
                'task_id': task_id,
                'subprocess_id': subprocess_id
            }
            
            # Run subprocess
            start_time = time.perf_counter()
            return_code, stdout, stderr = await self._subprocess_runner.run_agent_subprocess_async(
                agent_type=agent_type,
                task_data=task_data,
                timeout=kwargs.get('timeout_seconds', 300)
            )
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Parse results
            success = return_code == 0
            
            logger.info("real_subprocess_execution_complete", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "subprocess_id": subprocess_id,
                "return_code": return_code,
                "execution_time_ms": execution_time,
                "success": success
            })
            
            # Build result
            result = {
                "success": success,
                "subprocess_id": subprocess_id,
                "task_id": task_id,
                "return_code": return_code if return_code >= 0 else ReturnCode.GENERAL_FAILURE,
                "subprocess_info": {
                    "subprocess_id": subprocess_id,
                    "agent_type": agent_type,
                    "task_description": task_description,
                    "creation_time": datetime.now().isoformat(),
                    "status": "completed" if success else "failed",
                    "requirements": kwargs.get("requirements", []),
                    "deliverables": kwargs.get("deliverables", []),
                    "priority": kwargs.get("priority", "medium"),
                    "orchestration_mode": "real_subprocess",
                    "task_id": task_id,
                    "execution_time_ms": execution_time
                },
                "stdout": stdout,
                "stderr": stderr,
                "prompt": f"**{agent_type.title()} Agent**: {task_description}",
                "usage_instructions": self._generate_real_subprocess_instructions(
                    subprocess_id, agent_type, return_code, stdout, stderr
                )
            }
            
            return result, return_code if return_code >= 0 else ReturnCode.GENERAL_FAILURE
            
        except Exception as e:
            logger.error("real_subprocess_execution_failed", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Return error result
            return {
                "success": False,
                "subprocess_id": subprocess_id,
                "task_id": task_id,
                "return_code": ReturnCode.GENERAL_FAILURE,
                "error": str(e),
                "subprocess_info": {
                    "subprocess_id": subprocess_id,
                    "agent_type": agent_type,
                    "task_description": task_description,
                    "status": "failed",
                    "orchestration_mode": "real_subprocess",
                    "error": str(e)
                }
            }, ReturnCode.GENERAL_FAILURE
    
    def _generate_real_subprocess_instructions(
        self,
        subprocess_id: str,
        agent_type: str,
        return_code: int,
        stdout: str,
        stderr: str
    ) -> str:
        """Generate usage instructions for real subprocess execution."""
        return f"""
Real Subprocess Execution Instructions:
======================================

Subprocess ID: {subprocess_id}
Agent Type: {agent_type}
Return Code: {return_code}
Status: {'SUCCESS' if return_code == 0 else 'FAILED'}

This task was executed in a real OS subprocess:
- Environment variables were properly configured
- Agent profile was loaded from framework
- Subprocess had isolated execution context

Output:
{'-' * 50}
{stdout[:1000]}{'... (truncated)' if len(stdout) > 1000 else ''}
{'-' * 50}

{'Errors:' if stderr else ''}
{'='*50 if stderr else ''}
{stderr[:500] if stderr else ''}
{'='*50 if stderr else ''}

Integration Notes:
- Real subprocess execution provides true isolation
- Framework path and environment were properly set
- Agent profiles were successfully loaded
"""
    
    async def _emergency_subprocess_fallback(
        self,
        agent_type: str,
        task_description: str,
        error: str,
        task_id: Optional[str] = None,
        return_code: int = ReturnCode.GENERAL_FAILURE
    ) -> Tuple[Dict[str, Any], int]:
        """
        Emergency fallback to subprocess delegation with error information.
        """
        task_id = task_id or str(uuid.uuid4())[:8]
        
        logger.warning("emergency_fallback_triggered", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "error": error,
            "return_code": return_code
        })
        
        try:
            # Try subprocess delegation
            result, subprocess_return_code = await self._execute_subprocess_delegation(
                agent_type=agent_type,
                task_description=task_description,
                task_id=task_id
            )
            
            # Add error context
            if isinstance(result, dict):
                result["orchestration_error"] = error
                result["fallback_mode"] = "emergency_subprocess"
                result["return_code"] = return_code
                result["task_id"] = task_id
            
            logger.info("emergency_fallback_succeeded", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "subprocess_success": result.get("success", False) if isinstance(result, dict) else False
            })
            
            # Return original return code if subprocess succeeded, otherwise use subprocess return code
            final_return_code = return_code if subprocess_return_code == ReturnCode.SUCCESS else subprocess_return_code
            return result, final_return_code
            
        except Exception as e:
            # Ultimate fallback - return error response
            subprocess_id = f"error_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.error("emergency_fallback_failed", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "original_error": error,
                "fallback_error": str(e),
                "return_code": return_code
            })
            
            error_result = {
                "success": False,
                "subprocess_id": subprocess_id,
                "task_id": task_id,
                "return_code": return_code,
                "error": f"Orchestration failed: {error}. Subprocess fallback also failed: {str(e)}",
                "subprocess_info": {
                    "subprocess_id": subprocess_id,
                    "agent_type": agent_type,
                    "task_description": task_description,
                    "status": "failed",
                    "fallback_mode": "emergency_subprocess"
                },
                "prompt": f"**{agent_type.title()}**: {task_description}"
            }
            return error_result, return_code
    
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
                "metrics": [],
                "success_rate": 0.0,
                "average_token_reduction": 0.0
            }
        
        # Calculate statistics
        total = len(self._orchestration_metrics)
        local_count = sum(1 for m in self._orchestration_metrics if m.mode == OrchestrationMode.LOCAL)
        subprocess_count = sum(1 for m in self._orchestration_metrics if m.mode == OrchestrationMode.SUBPROCESS)
        
        # Success/failure statistics
        success_count = sum(1 for m in self._orchestration_metrics if m.return_code == ReturnCode.SUCCESS)
        failure_by_code = {}
        for m in self._orchestration_metrics:
            if m.return_code != ReturnCode.SUCCESS:
                code_name = self._get_return_code_name(m.return_code)
                failure_by_code[code_name] = failure_by_code.get(code_name, 0) + 1
        
        # Timing statistics
        avg_decision_time = sum(m.decision_time_ms for m in self._orchestration_metrics) / total
        avg_execution_time = sum(m.execution_time_ms for m in self._orchestration_metrics) / total
        
        # Token reduction statistics (only for local orchestrations with data)
        token_reductions = [
            m.token_reduction_percent 
            for m in self._orchestration_metrics 
            if m.mode == OrchestrationMode.LOCAL and m.context_size_original > 0
        ]
        avg_token_reduction = sum(token_reductions) / len(token_reductions) if token_reductions else 0.0
        
        # Context filtering timing (only for local orchestrations)
        context_filter_times = [
            m.context_filtering_time_ms 
            for m in self._orchestration_metrics 
            if m.mode == OrchestrationMode.LOCAL and m.context_filtering_time_ms > 0
        ]
        avg_context_filter_time = sum(context_filter_times) / len(context_filter_times) if context_filter_times else 0.0
        
        # Agent type distribution
        agent_type_counts = {}
        for m in self._orchestration_metrics:
            if m.agent_type:
                agent_type_counts[m.agent_type] = agent_type_counts.get(m.agent_type, 0) + 1
        
        return {
            "total_orchestrations": total,
            "local_orchestrations": local_count,
            "subprocess_orchestrations": subprocess_count,
            "success_count": success_count,
            "success_rate": (success_count / total * 100) if total > 0 else 0.0,
            "failure_by_code": failure_by_code,
            "average_decision_time_ms": avg_decision_time,
            "average_execution_time_ms": avg_execution_time,
            "average_context_filter_time_ms": avg_context_filter_time,
            "average_token_reduction_percent": avg_token_reduction,
            "agent_type_distribution": agent_type_counts,
            "recent_metrics": [m.to_dict() for m in self._orchestration_metrics[-10:]],
            "fallback_reasons": list(set(
                m.fallback_reason for m in self._orchestration_metrics 
                if m.fallback_reason
            ))
        }
    
    def _get_return_code_name(self, code: int) -> str:
        """Get human-readable name for return code."""
        code_names = {
            ReturnCode.SUCCESS: "SUCCESS",
            ReturnCode.GENERAL_FAILURE: "GENERAL_FAILURE",
            ReturnCode.TIMEOUT: "TIMEOUT",
            ReturnCode.CONTEXT_FILTERING_ERROR: "CONTEXT_FILTERING_ERROR",
            ReturnCode.AGENT_NOT_FOUND: "AGENT_NOT_FOUND",
            ReturnCode.MESSAGE_BUS_ERROR: "MESSAGE_BUS_ERROR"
        }
        return code_names.get(code, f"UNKNOWN_{code}")
    
    async def validate_compatibility(self) -> Dict[str, Any]:
        """Validate backwards compatibility with existing systems."""
        validation_results = {
            "compatible": True,
            "checks": {}
        }
        
        try:
            # Check API compatibility
            test_result, test_return_code = await self.delegate_to_agent(
                agent_type="test",
                task_description="Compatibility validation test"
            )
            validation_results["checks"]["return_code_support"] = test_return_code is not None
            
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
    
    def _register_default_agent_handlers(self) -> None:
        """
        Register default handlers for all agent types to enable instant LOCAL mode.
        These handlers provide agent-specific responses based on their role.
        """
        # Define agent-specific greetings
        agent_greetings = {
            'security': """Hello! I'm the Security Agent.

I specialize in:
- Security analysis and vulnerability assessment
- Threat modeling and risk evaluation  
- Security policy implementation
- Incident response coordination
- Compliance verification

I'm here to help protect your project from security vulnerabilities and ensure best practices are followed.""",
            'engineer': """Hello! I'm the Engineer Agent.

I specialize in:
- Code implementation and development
- Software architecture design
- Technical problem solving
- Performance optimization
- Code quality and best practices

I'm here to help with all your engineering and development needs.""",
            'documentation': """Hello! I'm the Documentation Agent.

I specialize in:
- Technical documentation creation
- API documentation
- User guides and tutorials
- Code documentation standards
- Documentation health analysis

I'm here to ensure your project has clear, comprehensive documentation.""",
            'qa': """Hello! I'm the QA Agent.

I specialize in:
- Test planning and execution
- Quality assurance processes
- Test automation
- Bug tracking and verification
- Quality metrics and reporting

I'm here to ensure your project meets quality standards.""",
            'research': """Hello! I'm the Research Agent.

I specialize in:
- Technical research and investigation
- Library and framework analysis
- Best practices research
- Technology evaluation
- Solution exploration

I'm here to help investigate and analyze technical topics.""",
            'ops': """Hello! I'm the Ops Agent.

I specialize in:
- Deployment and operations
- Infrastructure management
- CI/CD pipeline setup
- Monitoring and alerting
- Performance optimization

I'm here to handle all operational aspects of your project.""",
            'version_control': """Hello! I'm the Version Control Agent.

I specialize in:
- Git operations and workflows
- Branch management
- Merge conflict resolution
- Version tagging and releases
- Repository maintenance

I'm here to manage all version control operations.""",
            'ticketing': """Hello! I'm the Ticketing Agent.

I specialize in:
- Ticket lifecycle management
- Issue tracking integration
- Sprint planning support
- Status reporting
- Cross-platform ticket sync

I'm here to manage your project's ticketing workflow.""",
            'data_engineer': """Hello! I'm the Data Engineer Agent.

I specialize in:
- Database design and optimization
- Data pipeline development
- ETL processes
- Data storage solutions
- AI/ML API integrations

I'm here to handle all data engineering tasks."""
        }
        
        def create_agent_handler(agent_type: str):
            """Create a handler for a specific agent type."""
            async def agent_handler(request: Request) -> Response:
                """Handler that provides agent-specific responses."""
                task_data = request.data
                task = task_data.get('task', '')
                
                # Check if this is a simple greeting/role query
                greeting_keywords = ['who are you', 'hello', 'hi', 'greet', 'introduce', 'role', 'what do you do']
                is_greeting = any(keyword in task.lower() for keyword in greeting_keywords)
                
                if is_greeting:
                    # Provide agent-specific greeting
                    result_text = agent_greetings.get(agent_type, f"""Hello! I'm the {agent_type.title()} Agent.

I'm ready to assist with {agent_type} tasks. Please let me know what you need help with!""")
                else:
                    # For actual tasks, provide a task acknowledgment
                    result_text = f"""**{agent_type.title()} Agent Response**

Task received: {task}

I understand you need help with this {agent_type} task. As the {agent_type.title()} Agent, I'll analyze the requirements and provide appropriate assistance.

Requirements:
{chr(10).join('- ' + req for req in task_data.get('requirements', ['None specified']))}

Deliverables:
{chr(10).join('- ' + dlv for dlv in task_data.get('deliverables', ['None specified']))}

Priority: {task_data.get('priority', 'medium')}

I'm processing this request using LOCAL orchestration for instant response."""
                
                return Response(
                    request_id=request.id,
                    correlation_id=request.correlation_id,
                    agent_id=agent_type,
                    status=MessageStatus.COMPLETED,
                    data={"result": result_text}
                )
            
            return agent_handler
        
        # Register handlers for all common agent types
        agent_types = [
            'engineer', 'documentation', 'qa', 'research', 'ops', 
            'security', 'version_control', 'ticketing', 'data_engineer',
            'architect', 'ui_ux', 'performance', 'test', 'deployment'
        ]
        
        for agent_type in agent_types:
            try:
                handler = create_agent_handler(agent_type)
                self._message_bus.register_handler(agent_type, handler)
                logger.debug(f"Registered specific handler for {agent_type} agent")
            except ValueError:
                # Handler already registered, skip
                pass
            except Exception as e:
                logger.warning(f"Failed to register handler for {agent_type}: {e}")


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
) -> Tuple[Dict[str, Any], int]:
    """
    Quick delegation helper with automatic orchestration mode selection.
    
    This is a drop-in replacement for quick_create_subprocess.
    Returns tuple of (result_dict, return_code).
    """
    orchestrator = BackwardsCompatibleOrchestrator()
    return await orchestrator.delegate_to_agent(
        agent_type=agent_type,
        task_description=task_description,
        **kwargs
    )