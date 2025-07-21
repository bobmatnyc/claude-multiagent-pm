"""
Task Tool Helper - PM Orchestrator Integration
==============================================

This module provides Task Tool compatibility layer and helper functions for seamless
integration between PM orchestrator and agent prompt builder.

Key Features:
- Task Tool subprocess creation helpers
- Automatic prompt generation and formatting
- Agent delegation workflow management
- Real-time integration with PM orchestrator
- Memory collection integration

Usage Example:
    from claude_pm.utils.task_tool_helper import TaskToolHelper
    
    # Initialize helper
    helper = TaskToolHelper()
    
    # Create Task Tool subprocess with automatic prompt generation
    subprocess_result = helper.create_agent_subprocess(
        agent_type="engineer",
        task_description="Implement JWT authentication",
        requirements=["Security best practices", "Token expiration"],
        deliverables=["Auth system", "Tests", "Documentation"]
    )
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import TaskToolResponse for standardized response format
from claude_pm.core.response_types import TaskToolResponse

# Import PM orchestrator
try:
    from claude_pm.services.pm_orchestrator import PMOrchestrator, AgentDelegationContext, collect_pm_orchestrator_memory
except ImportError as e:
    logging.error(f"Failed to import PM orchestrator: {e}")
    # Fallback minimal implementation
    class PMOrchestrator:
        def __init__(self, working_directory=None):
            self.working_directory = Path(working_directory or os.getcwd())
        
        def generate_agent_prompt(self, **kwargs) -> str:
            return f"**{kwargs.get('agent_type', 'Agent').title()}**: {kwargs.get('task_description', 'Task')} + MEMORY COLLECTION REQUIRED"
    
    def collect_pm_orchestrator_memory(**kwargs):
        return {"success": True, "memory_id": "fallback"}

# Import model selection services
try:
    from claude_pm.services.agent_registry import AgentRegistry
    from claude_pm.services.model_selector import ModelSelector, ModelSelectionCriteria
except ImportError as e:
    logging.error(f"Failed to import model selection services: {e}")
    # Fallback implementations
    class AgentRegistry:
        def __init__(self):
            self.available = False
        
        async def get_agent_model_configuration(self, agent_name):
            return None
    
    class ModelSelector:
        def __init__(self):
            self.available = False
        
        def select_model_for_agent(self, agent_type, criteria=None):
            return ("claude-sonnet-4-20250514", {"fallback": True})
    
    class ModelSelectionCriteria:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

# Import correction capture system
try:
    from claude_pm.services.correction_capture import CorrectionCapture, CorrectionType, capture_subprocess_correction
except ImportError as e:
    logging.error(f"Failed to import correction capture: {e}")
    # Fallback implementation
    class CorrectionCapture:
        def __init__(self):
            self.enabled = False
        
        def create_task_tool_integration_hook(self, *args, **kwargs):
            return {"hook_id": "disabled"}
    
    def capture_subprocess_correction(*args, **kwargs):
        return "disabled"
    
    class CorrectionType:
        CONTENT_CORRECTION = "content_correction"

# Import memory monitoring
try:
    from claude_pm.monitoring import (
        SubprocessMemoryMonitor, 
        get_subprocess_memory_monitor,
        MemoryThresholds
    )
    MEMORY_MONITORING_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import memory monitoring: {e}")
    MEMORY_MONITORING_AVAILABLE = False
    # Fallback implementation
    class SubprocessMemoryMonitor:
        def __init__(self, *args, **kwargs):
            pass
        def start_monitoring(self, *args, **kwargs):
            pass
        def stop_monitoring(self, *args, **kwargs):
            return {"error": "Memory monitoring not available"}
        def check_memory(self, *args, **kwargs):
            return 0.0, "NOT_AVAILABLE"
        def can_create_subprocess(self):
            return True, "Memory monitoring not available"
        def should_abort(self, *args, **kwargs):
            return False
    
    class MemoryThresholds:
        def __init__(self, **kwargs):
            self.warning_mb = kwargs.get('warning_mb', 1024)
            self.critical_mb = kwargs.get('critical_mb', 2048)
            self.max_mb = kwargs.get('max_mb', 4096)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskToolConfiguration:
    """Configuration for Task Tool subprocess creation."""
    timeout_seconds: int = 300
    memory_collection_required: bool = True
    auto_escalation: bool = True
    progress_tracking: bool = True
    integration_validation: bool = True
    correction_capture_enabled: bool = True
    correction_capture_auto_hook: bool = True
    # Model selection configuration
    enable_model_selection: bool = True
    auto_model_optimization: bool = True
    model_override: Optional[str] = None
    performance_priority: str = "balanced"  # "speed", "quality", "balanced"
    # Memory monitoring configuration
    enable_memory_monitoring: bool = True
    memory_warning_mb: int = 1024  # 1GB warning
    memory_critical_mb: int = 2048  # 2GB critical
    memory_max_mb: int = 4096  # 4GB hard limit
    abort_on_memory_limit: bool = True


class TaskToolHelper:
    """
    Task Tool Helper with PM Orchestrator Integration
    
    Provides seamless Task Tool subprocess creation with automatic prompt generation,
    delegation tracking, and PM orchestrator integration.
    """
    
    def __init__(self, working_directory: Optional[Path] = None, config: Optional[TaskToolConfiguration] = None, model_override: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None, verbose: bool = False):
        """Initialize Task Tool helper with PM orchestrator and model selection integration."""
        self.working_directory = Path(working_directory or os.getcwd())
        self.config = config or TaskToolConfiguration()
        
        # Check for test mode environment variable
        test_mode = os.environ.get('CLAUDE_PM_TEST_MODE', '').lower() == 'true'
        
        # Enable verbose logging if test mode is active OR verbose flag is set
        self.verbose = verbose or test_mode
        
        # If test mode enabled verbose logging, log this fact
        if test_mode and not verbose:
            logger.info("Test mode detected: Enabling verbose subprocess logging automatically")
        
        # Use CLI model override if provided
        if model_override and not self.config.model_override:
            self.config.model_override = model_override
        
        # Initialize PM orchestrator with model override support
        self.pm_orchestrator = PMOrchestrator(
            working_directory=self.working_directory,
            model_override=self.config.model_override,
            model_config=model_config,
            verbose=self.verbose
        )
        self._active_subprocesses: Dict[str, Dict[str, Any]] = {}
        self._subprocess_history: List[Dict[str, Any]] = []
        
        # Initialize model selection services
        self.agent_registry = None
        self.model_selector = None
        if self.config.enable_model_selection:
            try:
                # Use shared prompt cache singleton for consistency
                from claude_pm.services.shared_prompt_cache import SharedPromptCache
                shared_cache = SharedPromptCache.get_instance()
                
                self.model_selector = ModelSelector()
                self.agent_registry = AgentRegistry(cache_service=shared_cache, model_selector=self.model_selector)
                logger.info("Model selection services initialized with shared cache")
            except Exception as e:
                logger.error(f"Failed to initialize model selection services: {e}")
                self.agent_registry = None
                self.model_selector = None
        
        # Initialize correction capture system
        self.correction_capture = None
        if self.config.correction_capture_enabled:
            try:
                self.correction_capture = CorrectionCapture()
                logger.info("Correction capture system initialized")
            except Exception as e:
                logger.error(f"Failed to initialize correction capture: {e}")
                self.correction_capture = None
        
        # Initialize memory monitoring
        self.memory_monitor = None
        if self.config.enable_memory_monitoring and MEMORY_MONITORING_AVAILABLE:
            try:
                # Create memory thresholds from config
                thresholds = MemoryThresholds(
                    warning_mb=self.config.memory_warning_mb,
                    critical_mb=self.config.memory_critical_mb,
                    max_mb=self.config.memory_max_mb
                )
                
                # Get or create memory monitor instance
                self.memory_monitor = get_subprocess_memory_monitor(
                    thresholds=thresholds,
                    log_dir=self.working_directory / '.claude-pm' / 'logs' / 'memory'
                )
                logger.info("Memory monitoring system initialized")
            except Exception as e:
                logger.error(f"Failed to initialize memory monitoring: {e}")
                self.memory_monitor = None
        
        logger.info(f"TaskToolHelper initialized with working directory: {self.working_directory}")
    
    def _log_subprocess_prompt(self, subprocess_id: str, prompt: str, agent_type: str, 
                              task_description: str, model_info: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Log subprocess creation prompts when verbose mode is enabled.
        
        Args:
            subprocess_id: ID of the subprocess
            prompt: The generated prompt text
            agent_type: Type of agent
            task_description: Description of the task
            model_info: Model configuration info
            
        Returns:
            Path to the log file if created, None otherwise
        """
        if not self.verbose:
            return None
            
        try:
            # Create log directory structure
            now = datetime.now()
            
            # Check for custom prompts directory from environment
            prompts_dir_env = os.environ.get('CLAUDE_PM_PROMPTS_DIR')
            if prompts_dir_env:
                # Use the custom prompts directory
                log_dir = Path(prompts_dir_env) / now.strftime("%Y-%m-%d")
            else:
                # Use default location
                log_dir = self.working_directory / ".claude-pm" / "logs" / "prompts" / now.strftime("%Y-%m-%d")
            
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            timestamp = now.strftime("%H%M%S_%f")[:-3]  # Include milliseconds
            filename = f"subprocess_{agent_type}_{timestamp}.json"
            log_path = log_dir / filename
            
            # Prepare log entry
            log_entry = {
                "timestamp": now.isoformat(),
                "subprocess_id": subprocess_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "prompt_text": prompt,
                "metadata": {
                    "framework_version": "014",
                    "subprocess_type": "task_tool",
                    "working_directory": str(self.working_directory),
                    "prompt_length": len(prompt),
                    "verbose_mode": True
                }
            }
            
            # Add model info if available
            if model_info:
                log_entry["model_info"] = model_info
            
            # Write log file
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Logged subprocess prompt to: {log_path}")
            return str(log_path)
            
        except Exception as e:
            logger.warning(f"Failed to log subprocess prompt: {e}")
            return None
    
    async def create_agent_subprocess(
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
        Create Task Tool subprocess with automatic prompt generation.
        
        Args:
            agent_type: Type of agent to create subprocess for
            task_description: Clear description of the task
            requirements: List of specific requirements
            deliverables: List of expected deliverables
            dependencies: List of task dependencies
            priority: Task priority (low, medium, high)
            memory_categories: Memory categories for collection
            timeout_seconds: Subprocess timeout
            escalation_triggers: Conditions for escalation
            integration_notes: Additional integration context
            
        Returns:
            Dictionary containing subprocess information and generated prompt
        """
        # Check if orchestration is enabled for integrated context filtering
        try:
            from claude_pm.orchestration.detection import OrchestrationDetector
            from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator
            
            detector = OrchestrationDetector()
            if detector.is_enabled():
                # Use orchestration with context filtering
                orchestrator = BackwardsCompatibleOrchestrator()
                return await orchestrator.delegate_to_agent(
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
                    working_directory=self.working_directory
                )
        except ImportError:
            # Orchestration modules not available, continue with standard
            pass
        except Exception as e:
            logger.warning(f"Orchestration check failed, continuing with standard: {e}")
        
        # Standard implementation without orchestration
        try:
            # Check memory availability before creating subprocess
            if self.memory_monitor and self.config.enable_memory_monitoring:
                can_create, memory_status = self.memory_monitor.can_create_subprocess()
                if not can_create:
                    logger.error(f"Cannot create subprocess: {memory_status}")
                    error_request_id = f"memory_error_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    return TaskToolResponse(
                        request_id=error_request_id,
                        success=False,
                        error=memory_status,
                        enhanced_prompt=f"**{agent_type.title()}**: {task_description} [BLOCKED BY MEMORY]"
                    )
                elif "WARNING" in memory_status:
                    logger.warning(f"Memory warning: {memory_status}")
            
            # Generate subprocess ID
            subprocess_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Select optimal model for this agent and task
            selected_model, model_config = await self._select_model_for_subprocess(
                agent_type=agent_type,
                task_description=task_description,
                model_override=model_override or self.config.model_override,
                performance_requirements=performance_requirements
            )
            
            # Generate prompt using PM orchestrator with model configuration
            prompt = self.pm_orchestrator.generate_agent_prompt(
                agent_type=agent_type,
                task_description=task_description,
                requirements=requirements,
                deliverables=deliverables,
                dependencies=dependencies,
                priority=priority,
                memory_categories=memory_categories,
                escalation_triggers=escalation_triggers,
                integration_notes=integration_notes,
                selected_model=selected_model,
                model_config=model_config
            )
            
            # Create subprocess information
            subprocess_info = {
                "subprocess_id": subprocess_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "generated_prompt": prompt,
                "creation_time": datetime.now().isoformat(),
                "status": "created",
                "timeout_seconds": timeout_seconds or self.config.timeout_seconds,
                "requirements": requirements or [],
                "deliverables": deliverables or [],
                "dependencies": dependencies or [],
                "priority": priority,
                "memory_categories": memory_categories or [],
                "escalation_triggers": escalation_triggers or [],
                "integration_notes": integration_notes,
                # Model configuration
                "selected_model": selected_model,
                "model_config": model_config,
                "performance_requirements": performance_requirements or {}
            }
            
            # Track active subprocess
            self._active_subprocesses[subprocess_id] = subprocess_info
            
            # Add to history
            self._subprocess_history.append({
                "subprocess_id": subprocess_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "creation_time": datetime.now().isoformat(),
                "status": "created"
            })
            
            # Start memory monitoring for this subprocess
            if self.memory_monitor and self.config.enable_memory_monitoring:
                try:
                    self.memory_monitor.start_monitoring(subprocess_id, {
                        "agent_type": agent_type,
                        "task_description": task_description
                    })
                    logger.info(f"Started memory monitoring for subprocess {subprocess_id}")
                except Exception as e:
                    logger.warning(f"Failed to start memory monitoring: {e}")
            
            # Collect memory for subprocess creation
            if self.config.memory_collection_required:
                collect_pm_orchestrator_memory(
                    category="architecture:design",
                    content=f"Created Task Tool subprocess for {agent_type}: {task_description}",
                    priority="medium",
                    delegation_id=subprocess_id
                )
            
            # Create correction capture hook
            correction_hook = None
            if self.config.correction_capture_auto_hook and self.correction_capture:
                try:
                    correction_hook = self.correction_capture.create_task_tool_integration_hook(
                        subprocess_id=subprocess_id,
                        agent_type=agent_type,
                        task_description=task_description
                    )
                    logger.info(f"Created correction capture hook: {correction_hook.get('hook_id', 'unknown')}")
                except Exception as e:
                    logger.error(f"Failed to create correction capture hook: {e}")
            
            logger.info(f"Created Task Tool subprocess: {subprocess_id}")
            
            # Log subprocess prompt if verbose mode is enabled
            if self.verbose:
                log_path = self._log_subprocess_prompt(
                    subprocess_id=subprocess_id,
                    prompt=prompt,
                    agent_type=agent_type,
                    task_description=task_description,
                    model_info={
                        "selected_model": selected_model,
                        **model_config
                    } if selected_model else None
                )
                if log_path:
                    logger.info(f"Subprocess prompt logged to: {log_path}")
            
            # Add memory monitoring status
            memory_monitoring_status = {
                "enabled": self.memory_monitor is not None and self.config.enable_memory_monitoring,
                "thresholds": {
                    "warning_mb": self.config.memory_warning_mb,
                    "critical_mb": self.config.memory_critical_mb,
                    "max_mb": self.config.memory_max_mb
                } if self.memory_monitor else None
            }
            
            return {
                "success": True,
                "subprocess_id": subprocess_id,
                "subprocess_info": subprocess_info,
                "prompt": prompt,
                "usage_instructions": self._generate_usage_instructions(subprocess_info),
                "correction_hook": correction_hook,
                "memory_monitoring": memory_monitoring_status
            }
            
        except Exception as e:
            logger.error(f"Error creating Task Tool subprocess: {e}")
            
            # Collect error memory
            if self.config.memory_collection_required:
                collect_pm_orchestrator_memory(
                    category="error:integration",
                    content=f"Failed to create Task Tool subprocess for {agent_type}: {str(e)}",
                    priority="high"
                )
            
            # Generate request_id for error response
            error_request_id = f"error_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return TaskToolResponse(
                request_id=error_request_id,
                success=False,
                error=str(e),
                enhanced_prompt=f"**{agent_type.title()}**: {task_description} + MEMORY COLLECTION REQUIRED"
            )
    
    async def _select_model_for_subprocess(
        self,
        agent_type: str,
        task_description: str,
        model_override: Optional[str] = None,
        performance_requirements: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Select optimal model for subprocess based on agent type and task requirements.
        
        Args:
            agent_type: Type of agent
            task_description: Description of the task
            model_override: Optional model override
            performance_requirements: Optional performance requirements
            
        Returns:
            Tuple of (model_id, model_configuration)
        """
        try:
            # Check for explicit model override
            if model_override:
                logger.debug(f"Using model override for {agent_type}: {model_override}")
                # Validate the override model if possible
                if self.model_selector:
                    validation = self.model_selector.validate_model_selection(agent_type, model_override)
                    if not validation["valid"]:
                        logger.warning(f"Invalid model override {model_override} for {agent_type}: {validation.get('error')}")
                        # Fall through to normal selection
                    else:
                        return model_override, {
                            "override": True,
                            "source": "explicit_override",
                            "max_tokens": 4096,  # Default
                            "validation": validation
                        }
                else:
                    return model_override, {
                        "override": True,
                        "source": "explicit_override",
                        "max_tokens": 4096  # Default
                    }
            
            # Try to get agent-specific model configuration from Agent Registry
            selected_model = None
            model_config = None
            
            if self.agent_registry and self.config.enable_model_selection:
                try:
                    # First check if we have a specific agent configuration
                    agent_model_config = await self.agent_registry.get_agent_model_configuration(agent_type)
                    if agent_model_config and agent_model_config.get("preferred_model"):
                        selected_model = agent_model_config["preferred_model"]
                        model_config = {
                            "max_tokens": agent_model_config.get("model_config", {}).get("max_tokens", 4096),
                            "context_window": agent_model_config.get("model_config", {}).get("context_window", 200000),
                            "capabilities": agent_model_config.get("capabilities", []),
                            "complexity_level": agent_model_config.get("complexity_level", "medium"),
                            "specializations": agent_model_config.get("specializations", []),
                            "selection_method": "agent_registry_configuration",
                            "source": "agent_specific_config"
                        }
                        logger.debug(f"Using Agent Registry configuration for {agent_type}: {selected_model}")
                except Exception as e:
                    logger.warning(f"Failed to get agent model configuration from registry: {e}")
            
            # If no agent-specific config, use ModelSelector with criteria
            if not selected_model and self.model_selector and self.config.enable_model_selection:
                try:
                    # Create selection criteria from task analysis
                    criteria = self._create_selection_criteria(
                        agent_type=agent_type,
                        task_description=task_description,
                        performance_requirements=performance_requirements
                    )
                    
                    # Select model using ModelSelector
                    model_type, model_configuration = self.model_selector.select_model_for_agent(
                        agent_type, criteria
                    )
                    
                    selected_model = model_type.value
                    model_config = {
                        "max_tokens": model_configuration.max_tokens,
                        "context_window": model_configuration.context_window,
                        "capabilities": model_configuration.capabilities,
                        "performance_profile": model_configuration.performance_profile,
                        "selection_method": "intelligent_selection",
                        "source": "model_selector",
                        "criteria": {
                            "task_complexity": criteria.task_complexity,
                            "reasoning_depth": criteria.reasoning_depth_required,
                            "speed_priority": criteria.speed_priority,
                            "creativity_required": criteria.creativity_required
                        }
                    }
                    logger.debug(f"Using ModelSelector for {agent_type}: {selected_model}")
                except Exception as e:
                    logger.warning(f"ModelSelector failed for {agent_type}: {e}")
            
            # Fallback to default model mapping if all else fails
            if not selected_model:
                default_models = {
                    'orchestrator': 'claude-4-opus',
                    'engineer': 'claude-4-opus',
                    'architecture': 'claude-4-opus',
                    'documentation': 'claude-sonnet-4-20250514',
                    'qa': 'claude-sonnet-4-20250514',
                    'research': 'claude-sonnet-4-20250514',
                    'ops': 'claude-sonnet-4-20250514',
                    'security': 'claude-sonnet-4-20250514',
                    'data_engineer': 'claude-sonnet-4-20250514'
                }
                
                selected_model = default_models.get(agent_type, 'claude-sonnet-4-20250514')
                model_config = {
                    "selection_method": "fallback",
                    "max_tokens": 4096,
                    "source": "default_mapping"
                }
                logger.debug(f"Using fallback model for {agent_type}: {selected_model}")
            
            return selected_model, model_config
            
        except Exception as e:
            logger.error(f"Error selecting model for {agent_type}: {e}")
            # Ultimate fallback
            return 'claude-sonnet-4-20250514', {
                "selection_method": "error_fallback",
                "error": str(e),
                "max_tokens": 4096
            }
    
    def _create_selection_criteria(
        self,
        agent_type: str,
        task_description: str,
        performance_requirements: Optional[Dict[str, Any]] = None
    ) -> 'ModelSelectionCriteria':
        """
        Create model selection criteria from task analysis.
        
        Args:
            agent_type: Type of agent
            task_description: Task description
            performance_requirements: Performance requirements
            
        Returns:
            ModelSelectionCriteria instance
        """
        # Analyze task complexity
        task_complexity = self._analyze_task_complexity(task_description)
        
        # Determine reasoning depth requirement
        reasoning_depth = self._determine_reasoning_depth(agent_type, task_description)
        
        # Check for creativity requirements
        creativity_required = self._check_creativity_requirements(task_description)
        
        # Check for speed priority
        speed_priority = self._check_speed_priority(task_description, performance_requirements)
        
        # Apply performance priority from config
        if self.config.performance_priority == "speed":
            speed_priority = True
        elif self.config.performance_priority == "quality":
            if task_complexity == "low":
                task_complexity = "medium"
        
        return ModelSelectionCriteria(
            agent_type=agent_type,
            task_complexity=task_complexity,
            performance_requirements=performance_requirements or {},
            reasoning_depth_required=reasoning_depth,
            creativity_required=creativity_required,
            speed_priority=speed_priority
        )
    
    def _analyze_task_complexity(self, task_description: str) -> str:
        """Analyze task complexity from description."""
        if not task_description:
            return "medium"
        
        task_lower = task_description.lower()
        
        # Expert complexity indicators
        expert_indicators = [
            "architecture", "design pattern", "complex system", "optimization",
            "machine learning", "ai", "algorithm", "performance tuning"
        ]
        if any(indicator in task_lower for indicator in expert_indicators):
            return "expert"
        
        # High complexity indicators
        high_indicators = [
            "implement", "develop", "create", "build", "integrate",
            "analyze", "engineer", "design", "system"
        ]
        if any(indicator in task_lower for indicator in high_indicators):
            return "high"
        
        # Low complexity indicators
        low_indicators = [
            "list", "show", "display", "format", "simple", "basic", "quick"
        ]
        if any(indicator in task_lower for indicator in low_indicators):
            return "low"
        
        return "medium"
    
    def _determine_reasoning_depth(self, agent_type: str, task_description: str) -> str:
        """Determine reasoning depth requirement."""
        task_lower = task_description.lower()
        
        # Agent type-based defaults
        if agent_type in ['engineer', 'architecture', 'orchestrator']:
            base_depth = "expert"
        elif agent_type in ['research', 'analysis', 'qa']:
            base_depth = "deep"
        else:
            base_depth = "standard"
        
        # Task-based adjustments
        if any(word in task_lower for word in ["strategy", "planning", "architecture"]):
            return "expert"
        elif any(word in task_lower for word in ["analyze", "investigate", "research"]):
            return "deep"
        elif any(word in task_lower for word in ["simple", "basic", "quick"]):
            return "simple"
        
        return base_depth
    
    def _check_creativity_requirements(self, task_description: str) -> bool:
        """Check if task requires creativity."""
        task_lower = task_description.lower()
        creativity_indicators = [
            "creative", "innovative", "design", "brainstorm", "ideate",
            "generate", "invent", "original", "novel"
        ]
        return any(indicator in task_lower for indicator in creativity_indicators)
    
    def _check_speed_priority(
        self, 
        task_description: str, 
        performance_requirements: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if speed is a priority."""
        # Check explicit performance requirements
        if performance_requirements and performance_requirements.get("speed_priority"):
            return True
        
        # Check task description
        task_lower = task_description.lower()
        speed_indicators = [
            "urgent", "quick", "fast", "immediate", "asap", "rapid",
            "real-time", "instant", "responsive"
        ]
        return any(indicator in task_lower for indicator in speed_indicators)
    
    def _generate_usage_instructions(self, subprocess_info: Dict[str, Any]) -> str:
        """Generate usage instructions for Task Tool subprocess."""
        correction_status = "enabled" if self.correction_capture else "disabled"
        memory_status = "enabled" if self.memory_monitor and self.config.enable_memory_monitoring else "disabled"
        
        return f"""
Task Tool Subprocess Usage Instructions:
========================================

Subprocess ID: {subprocess_info['subprocess_id']}
Agent Type: {subprocess_info['agent_type']}
Creation Time: {subprocess_info['creation_time']}

To use this subprocess:
1. Copy the generated prompt below
2. Create a new Task Tool subprocess
3. Paste the prompt as the subprocess content
4. Monitor subprocess progress
5. Report completion back to PM orchestrator

Generated Prompt:
{'-' * 50}
{subprocess_info['generated_prompt']}
{'-' * 50}

Integration Notes:
- This subprocess is tracked by PM orchestrator
- Memory collection is required for all operations
- Escalation triggers are configured for automatic PM notification
- Progress updates should be provided regularly
- Correction capture is {correction_status} for automatic prompt improvement
- Memory monitoring is {memory_status} for subprocess protection

Model Configuration:
- Selected Model: {subprocess_info.get('selected_model', 'Not specified')}
- Model Config: {subprocess_info.get('model_config', {}).get('selection_method', 'default')}
- Performance Profile: {subprocess_info.get('model_config', {}).get('performance_profile', {}).get('reasoning_quality', 'standard')}

Memory Monitoring:
- Status: {memory_status}
- Warning Threshold: {self.config.memory_warning_mb}MB
- Critical Threshold: {self.config.memory_critical_mb}MB
- Maximum Limit: {self.config.memory_max_mb}MB
- Auto-abort on limit: {self.config.abort_on_memory_limit}
- Memory alerts will be logged to .claude-pm/logs/memory/memory-alerts.log

Correction Capture Usage:
- If the subprocess response needs correction, use the capture_correction method
- This will help improve future agent responses automatically
- Corrections are stored for evaluation and prompt optimization
"""
    
    def get_subprocess_status(self, subprocess_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of Task Tool subprocesses."""
        if subprocess_id:
            info = self._active_subprocesses.get(subprocess_id)
            result = {
                "subprocess_id": subprocess_id,
                "info": info,
                "active": subprocess_id in self._active_subprocesses
            }
            
            # Add memory status if available
            if info and self.memory_monitor and self.config.enable_memory_monitoring:
                try:
                    memory_mb, memory_status = self.memory_monitor.check_memory(subprocess_id)
                    result["memory_status"] = {
                        "current_mb": memory_mb,
                        "status": memory_status,
                        "should_abort": self.memory_monitor.should_abort(subprocess_id)
                    }
                except Exception as e:
                    logger.warning(f"Failed to get memory status: {e}")
            
            return result
        
        # Get overall status
        status = {
            "active_subprocesses": len(self._active_subprocesses),
            "total_subprocesses": len(self._subprocess_history),
            "active_agents": list(set(info["agent_type"] for info in self._active_subprocesses.values())),
            "recent_subprocesses": self._subprocess_history[-5:] if self._subprocess_history else []
        }
        
        # Add memory monitoring status
        if self.memory_monitor and self.config.enable_memory_monitoring:
            try:
                status["memory_monitoring"] = {
                    "enabled": True,
                    "system_memory": self.memory_monitor.get_system_memory(),
                    "subprocess_stats": self.memory_monitor.get_all_subprocess_stats()
                }
            except Exception as e:
                logger.warning(f"Failed to get memory monitoring status: {e}")
                status["memory_monitoring"] = {"enabled": True, "error": str(e)}
        else:
            status["memory_monitoring"] = {"enabled": False}
        
        return status
    
    def complete_subprocess(self, subprocess_id: str, results: Dict[str, Any]) -> bool:
        """Mark subprocess as complete and process results."""
        if subprocess_id in self._active_subprocesses:
            # Stop memory monitoring first
            memory_stats = None
            if self.memory_monitor and self.config.enable_memory_monitoring:
                try:
                    memory_stats = self.memory_monitor.stop_monitoring(subprocess_id)
                    logger.info(f"Memory monitoring stopped for {subprocess_id}: {memory_stats}")
                except Exception as e:
                    logger.warning(f"Failed to stop memory monitoring: {e}")
            
            # Update subprocess info
            self._active_subprocesses[subprocess_id]["status"] = "completed"
            self._active_subprocesses[subprocess_id]["completion_time"] = datetime.now().isoformat()
            self._active_subprocesses[subprocess_id]["results"] = results
            if memory_stats:
                self._active_subprocesses[subprocess_id]["memory_stats"] = memory_stats
            
            # Update history
            for entry in self._subprocess_history:
                if entry["subprocess_id"] == subprocess_id:
                    entry["status"] = "completed"
                    entry["completion_time"] = datetime.now().isoformat()
                    entry["results"] = results
                    if memory_stats:
                        entry["memory_stats"] = memory_stats
                    break
            
            # Complete delegation in PM orchestrator
            self.pm_orchestrator.complete_delegation(subprocess_id, results)
            
            # Remove from active tracking
            del self._active_subprocesses[subprocess_id]
            
            # Collect completion memory
            if self.config.memory_collection_required:
                memory_summary = ""
                if memory_stats and "memory_stats" in memory_stats:
                    peak_mb = memory_stats["memory_stats"].get("peak_mb", "N/A")
                    memory_summary = f" (peak memory: {peak_mb}MB)"
                
                collect_pm_orchestrator_memory(
                    category="architecture:design",
                    content=f"Completed Task Tool subprocess {subprocess_id}: {results.get('summary', 'No summary')}{memory_summary}",
                    priority="medium",
                    delegation_id=subprocess_id
                )
            
            logger.info(f"Completed Task Tool subprocess: {subprocess_id}")
            return True
        
        return False
    
    def capture_correction(
        self,
        subprocess_id: str,
        original_response: str,
        user_correction: str,
        correction_type: str = "content_correction",
        severity: str = "medium",
        user_feedback: Optional[str] = None
    ) -> str:
        """
        Capture a correction for a subprocess response.
        
        Args:
            subprocess_id: ID of the subprocess
            original_response: Original agent response
            user_correction: User's correction
            correction_type: Type of correction
            severity: Severity level
            user_feedback: Additional feedback
            
        Returns:
            Correction ID
        """
        if not self.correction_capture:
            logger.warning("Correction capture not enabled")
            return ""
        
        # Get subprocess info
        subprocess_info = self._active_subprocesses.get(subprocess_id)
        if not subprocess_info:
            # Check history
            for entry in self._subprocess_history:
                if entry["subprocess_id"] == subprocess_id:
                    subprocess_info = entry
                    break
        
        if not subprocess_info:
            logger.error(f"Subprocess {subprocess_id} not found")
            return ""
        
        try:
            # Convert string correction type to enum
            correction_type_enum = getattr(CorrectionType, correction_type.upper(), CorrectionType.CONTENT_CORRECTION)
            
            correction_id = self.correction_capture.capture_correction(
                agent_type=subprocess_info["agent_type"],
                original_response=original_response,
                user_correction=user_correction,
                context={
                    "subprocess_id": subprocess_id,
                    "task_description": subprocess_info.get("task_description", ""),
                    "working_directory": str(self.working_directory)
                },
                correction_type=correction_type_enum,
                subprocess_id=subprocess_id,
                task_description=subprocess_info.get("task_description", ""),
                severity=severity,
                user_feedback=user_feedback
            )
            
            logger.info(f"Captured correction {correction_id} for subprocess {subprocess_id}")
            return correction_id
            
        except Exception as e:
            logger.error(f"Failed to capture correction: {e}")
            return ""
    
    def get_correction_statistics(self) -> Dict[str, Any]:
        """Get correction capture statistics."""
        if not self.correction_capture:
            return {"enabled": False, "message": "Correction capture not enabled"}
        
        try:
            stats = self.correction_capture.get_correction_stats()
            return {
                "enabled": True,
                "statistics": stats,
                "storage_path": str(self.correction_capture.storage_config.storage_path)
            }
        except Exception as e:
            logger.error(f"Failed to get correction statistics: {e}")
            # Generate error response with TaskToolResponse for consistency
            error_request_id = f"stats_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return TaskToolResponse(
                request_id=error_request_id,
                success=False,
                error=str(e),
                performance_metrics={"enabled": True}
            )
    
    def check_subprocess_memory(self, subprocess_id: str) -> Dict[str, Any]:
        """Check memory status for a specific subprocess and take action if needed."""
        if not self.memory_monitor or not self.config.enable_memory_monitoring:
            return {"enabled": False, "message": "Memory monitoring not enabled"}
        
        try:
            memory_mb, status = self.memory_monitor.check_memory(subprocess_id)
            should_abort = self.memory_monitor.should_abort(subprocess_id)
            
            result = {
                "subprocess_id": subprocess_id,
                "memory_mb": memory_mb,
                "status": status,
                "should_abort": should_abort,
                "timestamp": datetime.now().isoformat()
            }
            
            # Handle critical situations
            if should_abort and self.config.abort_on_memory_limit:
                logger.error(f"Subprocess {subprocess_id} exceeded memory limit, recommending abort")
                result["action"] = "ABORT_RECOMMENDED"
                result["reason"] = f"Memory usage ({memory_mb}MB) exceeded limit ({self.config.memory_max_mb}MB)"
                
                # Mark subprocess as aborted in tracking
                if subprocess_id in self._active_subprocesses:
                    self._active_subprocesses[subprocess_id]["status"] = "aborted_memory"
                    self._active_subprocesses[subprocess_id]["abort_time"] = datetime.now().isoformat()
                    
            elif status == "CRITICAL":
                logger.warning(f"Subprocess {subprocess_id} memory critical: {memory_mb}MB")
                result["action"] = "WARNING"
                result["reason"] = f"Memory usage ({memory_mb}MB) is critical"
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to check subprocess memory: {e}")
            return {"enabled": True, "error": str(e)}
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report for all subprocesses."""
        if not self.memory_monitor or not self.config.enable_memory_monitoring:
            return {"enabled": False, "message": "Memory monitoring not enabled"}
        
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_memory": self.memory_monitor.get_system_memory(),
                "subprocess_stats": self.memory_monitor.get_all_subprocess_stats(),
                "configuration": {
                    "warning_mb": self.config.memory_warning_mb,
                    "critical_mb": self.config.memory_critical_mb,
                    "max_mb": self.config.memory_max_mb,
                    "abort_on_limit": self.config.abort_on_memory_limit
                },
                "active_subprocesses": len(self._active_subprocesses),
                "memory_alerts": []
            }
            
            # Check each subprocess and collect alerts
            for subprocess_id in self._active_subprocesses:
                check_result = self.check_subprocess_memory(subprocess_id)
                if check_result.get("status") in ["WARNING", "CRITICAL", "ABORTED"]:
                    report["memory_alerts"].append(check_result)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate memory report: {e}")
            return {"enabled": True, "error": str(e)}
    
    def list_available_agents(self) -> Dict[str, List[str]]:
        """List all available agents for Task Tool subprocess creation."""
        return self.pm_orchestrator.list_available_agents()
    
    def validate_integration(self) -> Dict[str, Any]:
        """Validate Task Tool helper integration with PM orchestrator."""
        try:
            # Test PM orchestrator integration
            pm_validation = self.pm_orchestrator.validate_agent_hierarchy()
            
            # Test agent listing
            agents = self.pm_orchestrator.list_available_agents()
            
            # Test prompt generation
            test_prompt = self.pm_orchestrator.generate_agent_prompt(
                agent_type="engineer",
                task_description="Integration validation test",
                requirements=["Test functionality"],
                deliverables=["Validation report"]
            )
            
            return {
                "valid": True,
                "pm_orchestrator_integration": pm_validation.get("valid", False),
                "available_agents": agents,
                "prompt_generation": len(test_prompt) > 0,
                "active_subprocesses": len(self._active_subprocesses),
                "total_subprocesses": len(self._subprocess_history),
                "working_directory": str(self.working_directory),
                "config": {
                    "timeout_seconds": self.config.timeout_seconds,
                    "memory_collection_required": self.config.memory_collection_required,
                    "auto_escalation": self.config.auto_escalation,
                    "progress_tracking": self.config.progress_tracking,
                    "integration_validation": self.config.integration_validation,
                    "correction_capture_enabled": self.config.correction_capture_enabled,
                    "correction_capture_auto_hook": self.config.correction_capture_auto_hook,
                    "enable_model_selection": self.config.enable_model_selection,
                    "auto_model_optimization": self.config.auto_model_optimization,
                    "model_override": self.config.model_override,
                    "performance_priority": self.config.performance_priority
                },
                "correction_capture": {
                    "enabled": self.correction_capture is not None,
                    "service_active": self.correction_capture.enabled if self.correction_capture else False
                },
                "model_selection": {
                    "enabled": self.model_selector is not None,
                    "agent_registry_available": self.agent_registry is not None,
                    "model_selector_available": self.model_selector is not None and hasattr(self.model_selector, 'select_model_for_agent'),
                    "agent_registry_models": self.agent_registry is not None and hasattr(self.agent_registry, 'get_agent_model_configuration'),
                    "configuration": {
                        "enable_model_selection": self.config.enable_model_selection,
                        "auto_model_optimization": self.config.auto_model_optimization,
                        "model_override": self.config.model_override,
                        "performance_priority": self.config.performance_priority
                    },
                    "available_models": self.get_available_models() if self.model_selector else [],
                    "model_mapping_available": bool(self.model_selector and hasattr(self.model_selector, 'get_agent_model_mapping'))
                },
                "memory_monitoring": {
                    "enabled": self.memory_monitor is not None and self.config.enable_memory_monitoring,
                    "available": MEMORY_MONITORING_AVAILABLE,
                    "configuration": {
                        "enable_memory_monitoring": self.config.enable_memory_monitoring,
                        "memory_warning_mb": self.config.memory_warning_mb,
                        "memory_critical_mb": self.config.memory_critical_mb,
                        "memory_max_mb": self.config.memory_max_mb,
                        "abort_on_memory_limit": self.config.abort_on_memory_limit
                    },
                    "system_memory": self.memory_monitor.get_system_memory() if self.memory_monitor else None,
                    "active_monitors": len(self.memory_monitor.active_monitors) if self.memory_monitor and hasattr(self.memory_monitor, 'active_monitors') else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Integration validation failed: {e}")
            return {
                "valid": False,
                "error": str(e),
                "working_directory": str(self.working_directory)
            }
    
    async def create_shortcut_subprocess(self, shortcut_type: str, **kwargs) -> Dict[str, Any]:
        """Create subprocess for common PM orchestrator shortcuts."""
        shortcut_mapping = {
            "push": {
                "agent_type": "documentation",
                "task_description": "Generate changelog and analyze semantic versioning impact for push operation",
                "requirements": ["Analyze git commit history", "Determine version bump needed"],
                "deliverables": ["Changelog content", "Version bump recommendation", "Release notes"]
            },
            "deploy": {
                "agent_type": "ops",
                "task_description": "Execute local deployment operations with validation",
                "requirements": ["Deploy framework files", "Validate deployment"],
                "deliverables": ["Deployment status report", "Validation results"]
            },
            "test": {
                "agent_type": "qa",
                "task_description": "Execute comprehensive test suite and validation",
                "requirements": ["Run all tests", "Validate quality standards"],
                "deliverables": ["Test results", "Quality validation report"]
            },
            "publish": {
                "agent_type": "ops",
                "task_description": "Execute package publication pipeline",
                "requirements": ["Validate package integrity", "Publish to registry"],
                "deliverables": ["Publication status", "Version confirmation"]
            }
        }
        
        if shortcut_type not in shortcut_mapping:
            error_request_id = f"shortcut_error_{shortcut_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return TaskToolResponse(
                request_id=error_request_id,
                success=False,
                error=f"Unknown shortcut type: {shortcut_type}",
                performance_metrics={"available_shortcuts": list(shortcut_mapping.keys())}
            )
        
        # Merge shortcut defaults with provided kwargs
        shortcut_config = shortcut_mapping[shortcut_type]
        shortcut_config.update(kwargs)
        
        return await self.create_agent_subprocess(**shortcut_config)
    
    def generate_delegation_summary(self) -> str:
        """Generate a summary of current Task Tool delegations."""
        active_count = len(self._active_subprocesses)
        total_count = len(self._subprocess_history)
        
        summary = f"""
Task Tool Helper - Delegation Summary
=====================================

Current Status:
- Active Subprocesses: {active_count}
- Total Subprocesses Created: {total_count}
- Working Directory: {self.working_directory}

Active Delegations:
"""
        
        if self._active_subprocesses:
            for subprocess_id, info in self._active_subprocesses.items():
                summary += f"""
- {subprocess_id}:
  - Agent: {info['agent_type']}
  - Task: {info['task_description'][:50]}...
  - Priority: {info['priority']}
  - Created: {info['creation_time']}
"""
        else:
            summary += "  (No active delegations)\n"
        
        summary += f"""
Recent History:
"""
        
        if self._subprocess_history:
            for entry in self._subprocess_history[-3:]:
                summary += f"""
- {entry['subprocess_id']}:
  - Agent: {entry['agent_type']}
  - Task: {entry['task_description'][:50]}...
  - Status: {entry['status']}
  - Created: {entry['creation_time']}
"""
        else:
            summary += "  (No delegation history)\n"
        
        return summary
    
    # Model selection and configuration methods
    
    async def get_agent_model_recommendation(
        self, 
        agent_type: str, 
        task_description: str = ""
    ) -> Dict[str, Any]:
        """
        Get model recommendation for an agent type and task.
        
        Args:
            agent_type: Type of agent
            task_description: Optional task description for analysis
            
        Returns:
            Model recommendation with analysis
        """
        if not self.model_selector:
            return {
                "error": "Model selection not available",
                "fallback_model": "claude-sonnet-4-20250514"
            }
        
        try:
            return self.model_selector.get_model_recommendation(agent_type, task_description)
        except Exception as e:
            logger.error(f"Error getting model recommendation: {e}")
            return {
                "error": str(e),
                "fallback_model": "claude-sonnet-4-20250514"
            }
    
    async def validate_model_configuration(
        self, 
        agent_type: str, 
        model_id: str
    ) -> Dict[str, Any]:
        """
        Validate model configuration for an agent type.
        
        Args:
            agent_type: Type of agent
            model_id: Model identifier to validate
            
        Returns:
            Validation results
        """
        if not self.model_selector:
            return {"valid": False, "error": "Model selection not available"}
        
        try:
            return self.model_selector.validate_model_selection(agent_type, model_id)
        except Exception as e:
            logger.error(f"Error validating model configuration: {e}")
            return {"valid": False, "error": str(e)}
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List of available model IDs
        """
        if not self.model_selector:
            return ["claude-sonnet-4-20250514", "claude-4-opus"]
        
        try:
            stats = self.model_selector.get_selection_statistics()
            return list(stats.get("configuration_summary", {}).keys())
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return ["claude-sonnet-4-20250514", "claude-4-opus"]
    
    def get_model_selection_statistics(self) -> Dict[str, Any]:
        """
        Get model selection statistics.
        
        Returns:
            Model selection statistics
        """
        if not self.model_selector:
            return {"error": "Model selection not available"}
        
        try:
            return self.model_selector.get_selection_statistics()
        except Exception as e:
            logger.error(f"Error getting model selection statistics: {e}")
            return {"error": str(e)}
    
    async def get_agent_registry_model_stats(self) -> Dict[str, Any]:
        """
        Get model usage statistics from agent registry.
        
        Returns:
            Agent registry model statistics
        """
        if not self.agent_registry:
            return {"error": "Agent registry not available"}
        
        try:
            return await self.agent_registry.get_model_usage_statistics()
        except Exception as e:
            logger.error(f"Error getting agent registry model stats: {e}")
            return {"error": str(e)}
    
    def configure_model_selection(
        self,
        enable_model_selection: Optional[bool] = None,
        auto_model_optimization: Optional[bool] = None,
        model_override: Optional[str] = None,
        performance_priority: Optional[str] = None
    ) -> bool:
        """
        Configure model selection settings.
        
        Args:
            enable_model_selection: Enable/disable model selection
            auto_model_optimization: Enable/disable auto optimization
            model_override: Global model override
            performance_priority: Performance priority setting
            
        Returns:
            True if configuration updated successfully
        """
        try:
            if enable_model_selection is not None:
                self.config.enable_model_selection = enable_model_selection
            
            if auto_model_optimization is not None:
                self.config.auto_model_optimization = auto_model_optimization
            
            if model_override is not None:
                self.config.model_override = model_override
            
            if performance_priority is not None:
                if performance_priority in ["speed", "quality", "balanced"]:
                    self.config.performance_priority = performance_priority
                else:
                    logger.warning(f"Invalid performance priority: {performance_priority}")
                    return False
            
            logger.info("Model selection configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring model selection: {e}")
            return False
    
    async def validate_model_configuration_for_subprocess(
        self,
        agent_type: str,
        model_id: str
    ) -> Dict[str, Any]:
        """
        Validate model configuration for subprocess creation.
        
        Args:
            agent_type: Type of agent
            model_id: Model identifier to validate
            
        Returns:
            Validation results with recommendations
        """
        if not self.model_selector:
            return {"valid": False, "error": "Model selection service not available"}
        
        try:
            return await self.validate_model_configuration(agent_type, model_id)
        except Exception as e:
            logger.error(f"Error validating model configuration: {e}")
            return {"valid": False, "error": str(e)}
    
    async def get_optimal_model_for_subprocess(
        self,
        agent_type: str,
        task_description: str,
        performance_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get optimal model recommendation for subprocess creation.
        
        Args:
            agent_type: Type of agent
            task_description: Description of the task
            performance_requirements: Performance requirements
            
        Returns:
            Model recommendation with configuration
        """
        if not self.model_selector:
            return {
                "error": "Model selection service not available",
                "fallback_model": "claude-3-5-sonnet-20241022"
            }
        
        try:
            return await self.get_agent_model_recommendation(agent_type, task_description)
        except Exception as e:
            logger.error(f"Error getting optimal model: {e}")
            return {
                "error": str(e),
                "fallback_model": "claude-sonnet-4-20250514"
            }


# Helper functions for easy integration
async def quick_create_subprocess(
    agent_type: str,
    task_description: str,
    requirements: Optional[List[str]] = None,
    deliverables: Optional[List[str]] = None,
    working_directory: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Quick subprocess creation helper.
    
    Args:
        agent_type: Type of agent to create subprocess for
        task_description: Task description
        requirements: List of requirements
        deliverables: List of expected deliverables
        working_directory: Working directory path
        
    Returns:
        Subprocess creation result with generated prompt
    """
    # Check if orchestration is enabled
    try:
        from claude_pm.orchestration.detection import OrchestrationDetector
        from claude_pm.orchestration.backwards_compatible_orchestrator import quick_delegate
        
        detector = OrchestrationDetector()
        if detector.is_enabled():
            # Use orchestration with context filtering
            return await quick_delegate(
                agent_type=agent_type,
                task_description=task_description,
                requirements=requirements,
                deliverables=deliverables,
                working_directory=working_directory
            )
    except ImportError:
        # Orchestration modules not available, fall back to standard
        pass
    except Exception as e:
        logger.warning(f"Orchestration check failed, falling back to standard: {e}")
    
    # Standard implementation without orchestration
    helper = TaskToolHelper(working_directory)
    return await helper.create_agent_subprocess(
        agent_type=agent_type,
        task_description=task_description,
        requirements=requirements,
        deliverables=deliverables
    )


async def create_pm_shortcuts() -> Dict[str, Dict[str, Any]]:
    """Create all PM orchestrator shortcuts as Task Tool subprocesses."""
    helper = TaskToolHelper()
    
    shortcuts = {}
    shortcut_types = ["push", "deploy", "test", "publish"]
    
    for shortcut_type in shortcut_types:
        shortcuts[shortcut_type] = await helper.create_shortcut_subprocess(shortcut_type)
    
    return shortcuts


def validate_task_tool_integration() -> Dict[str, Any]:
    """Validate Task Tool helper integration with PM orchestrator."""
    helper = TaskToolHelper()
    return helper.validate_integration()


if __name__ == "__main__":
    # Test the Task Tool helper
    helper = TaskToolHelper()
    
    # Test subprocess creation
    result = helper.create_agent_subprocess(
        agent_type="engineer",
        task_description="Test Task Tool helper integration",
        requirements=["Create integration test", "Verify functionality"],
        deliverables=["Working test", "Integration validation"]
    )
    
    print("Task Tool Subprocess Creation Result:")
    print("=" * 50)
    print(f"Success: {result['success']}")
    
    if result['success']:
        print(f"Subprocess ID: {result['subprocess_id']}")
        print(f"Generated Prompt Length: {len(result['prompt'])} characters")
        print("\nUsage Instructions:")
        print(result['usage_instructions'])
    else:
        print(f"Error: {result['error']}")
    
    # Test status tracking
    status = helper.get_subprocess_status()
    print(f"\nHelper Status: {status}")
    
    # Test validation
    validation = helper.validate_integration()
    print(f"\nIntegration Validation: {validation['valid']}")
    
    # Generate delegation summary
    summary = helper.generate_delegation_summary()
    print(f"\nDelegation Summary:\n{summary}")