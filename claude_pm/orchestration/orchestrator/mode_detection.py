"""
Orchestration Mode Detection
===========================

This module handles the logic for determining which orchestration mode
(local vs subprocess) should be used for agent delegation.
"""

import os
import time
import logging
from typing import Tuple, Optional

from .types import OrchestrationMode
from ..orchestration_detector import OrchestrationDetector
from ..message_bus import SimpleMessageBus
from ..context_manager import create_context_manager
from claude_pm.services.agent_registry_sync import AgentRegistry
from claude_pm.services.shared_prompt_cache import SharedPromptCache

logger = logging.getLogger(__name__)


class ModeDetector:
    """Handles orchestration mode detection and component initialization."""
    
    def __init__(self):
        self.detector = OrchestrationDetector()
        self._message_bus = None
        self._context_manager = None
        self._agent_registry = None
        self.force_mode = None
        
    def set_force_mode(self, mode: Optional[OrchestrationMode]) -> None:
        """Force a specific orchestration mode (for testing)."""
        self.force_mode = mode
        
    async def determine_orchestration_mode(self) -> Tuple[OrchestrationMode, Optional[str]]:
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
    
    def _register_default_agent_handlers(self):
        """Register default agent handlers. This will be imported from agent_handlers module."""
        # This is a placeholder - will be connected to agent_handlers module
        pass
    
    @property
    def message_bus(self):
        """Get the message bus instance."""
        return self._message_bus
    
    @property
    def context_manager(self):
        """Get the context manager instance."""
        return self._context_manager
    
    @property
    def agent_registry(self):
        """Get the agent registry instance."""
        return self._agent_registry