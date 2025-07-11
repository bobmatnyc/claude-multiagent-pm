"""
Memory Trigger Service

Unified service for initializing and managing memory triggers throughout
the Claude PM Framework. Provides a single entry point for all memory
trigger functionality.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from pathlib import Path

from .services.unified_service import FlexibleMemoryService
from .trigger_orchestrator import MemoryTriggerOrchestrator
from .trigger_policies import TriggerPolicyEngine
from .framework_hooks import FrameworkMemoryHooks
from .decorators import set_global_hooks
from .interfaces.exceptions import MemoryServiceError


class MemoryTriggerService:
    """
    Unified memory trigger service for the Claude PM Framework.
    
    Coordinates memory service, trigger orchestrator, policy engine,
    and framework hooks into a single, easy-to-use service.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the memory trigger service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Service components
        self.memory_service: Optional[FlexibleMemoryService] = None
        self.trigger_orchestrator: Optional[MemoryTriggerOrchestrator] = None
        self.policy_engine: Optional[TriggerPolicyEngine] = None
        self.framework_hooks: Optional[FrameworkMemoryHooks] = None
        
        # State tracking
        self._initialized = False
        self._enabled = self.config.get("enabled", True)
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all service components."""
        try:
            # Initialize memory service
            memory_config = self.config.get("memory", {})
            self.memory_service = FlexibleMemoryService(memory_config)
            
            # Initialize policy engine
            policy_config = self.config.get("policies", {})
            self.policy_engine = TriggerPolicyEngine(policy_config)
            
            # Initialize trigger orchestrator
            orchestrator_config = self.config.get("orchestrator", {})
            self.trigger_orchestrator = MemoryTriggerOrchestrator(
                self.memory_service,
                orchestrator_config
            )
            
            # Initialize framework hooks
            hooks_config = self.config.get("hooks", {})
            self.framework_hooks = FrameworkMemoryHooks(
                self.memory_service,
                self.trigger_orchestrator,
                self.policy_engine,
                hooks_config
            )
            
            # Set global hooks for decorators
            set_global_hooks(self.framework_hooks)
            
            self.logger.info("Memory trigger service components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory trigger service components: {e}")
            raise MemoryServiceError(f"Component initialization failed: {e}")
    
    async def initialize(self) -> bool:
        """
        Initialize the memory trigger service.
        
        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            return True
        
        if not self._enabled:
            self.logger.info("Memory trigger service disabled")
            return True
        
        try:
            self.logger.info("Initializing memory trigger service...")
            
            # Initialize memory service
            if not await self.memory_service.initialize():
                raise MemoryServiceError("Failed to initialize memory service")
            
            # Initialize trigger orchestrator
            if not await self.trigger_orchestrator.initialize():
                raise MemoryServiceError("Failed to initialize trigger orchestrator")
            
            # Framework hooks don't need async initialization
            
            self._initialized = True
            self.logger.info("Memory trigger service initialized successfully")
            
            # Log service status
            await self._log_service_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory trigger service: {e}")
            self._initialized = False
            raise
    
    async def _log_service_status(self):
        """Log the current service status."""
        try:
            # Get service health
            health = await self.get_service_health()
            
            self.logger.info(f"Memory Service Status: {health['memory_service']['status']}")
            self.logger.info(f"Active Backend: {health['memory_service']['active_backend']}")
            self.logger.info(f"Trigger Orchestrator: {health['trigger_orchestrator']['status']}")
            self.logger.info(f"Policy Engine: {health['policy_engine']['status']}")
            self.logger.info(f"Framework Hooks: {health['framework_hooks']['status']}")
            
        except Exception as e:
            self.logger.warning(f"Could not log service status: {e}")
    
    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get comprehensive service health information.
        
        Returns:
            Dict[str, Any]: Service health data
        """
        health = {
            "service_initialized": self._initialized,
            "service_enabled": self._enabled,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Memory service health
        if self.memory_service:
            try:
                memory_health = await self.memory_service.get_service_health()
                health["memory_service"] = {
                    "status": "healthy" if memory_health["service_healthy"] else "unhealthy",
                    "active_backend": memory_health["active_backend"],
                    "backends": memory_health["backends"],
                    "metrics": memory_health["metrics"]
                }
            except Exception as e:
                health["memory_service"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health["memory_service"] = {"status": "not_initialized"}
        
        # Trigger orchestrator health
        if self.trigger_orchestrator:
            try:
                orchestrator_metrics = self.trigger_orchestrator.get_metrics()
                health["trigger_orchestrator"] = {
                    "status": "healthy" if orchestrator_metrics["initialized"] else "unhealthy",
                    "enabled": orchestrator_metrics["enabled"],
                    "queue_size": orchestrator_metrics["queue_size"],
                    "metrics": orchestrator_metrics
                }
            except Exception as e:
                health["trigger_orchestrator"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health["trigger_orchestrator"] = {"status": "not_initialized"}
        
        # Policy engine health
        if self.policy_engine:
            try:
                policy_metrics = self.policy_engine.get_policy_metrics()
                health["policy_engine"] = {
                    "status": "healthy",
                    "total_policies": policy_metrics["total_policies"],
                    "enabled_policies": policy_metrics["enabled_policies"],
                    "metrics": policy_metrics
                }
            except Exception as e:
                health["policy_engine"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health["policy_engine"] = {"status": "not_initialized"}
        
        # Framework hooks health
        if self.framework_hooks:
            try:
                hooks_metrics = self.framework_hooks.get_metrics()
                health["framework_hooks"] = {
                    "status": "healthy",
                    "enabled": hooks_metrics["enabled"],
                    "registered_hooks": hooks_metrics["registered_hooks"],
                    "metrics": hooks_metrics
                }
            except Exception as e:
                health["framework_hooks"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health["framework_hooks"] = {"status": "not_initialized"}
        
        return health
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive service metrics.
        
        Returns:
            Dict[str, Any]: Service metrics
        """
        metrics = {}
        
        # Memory service metrics
        if self.memory_service:
            try:
                metrics["memory_service"] = self.memory_service.get_metrics()
            except Exception as e:
                metrics["memory_service"] = {"error": str(e)}
        
        # Trigger orchestrator metrics
        if self.trigger_orchestrator:
            try:
                metrics["trigger_orchestrator"] = self.trigger_orchestrator.get_metrics()
            except Exception as e:
                metrics["trigger_orchestrator"] = {"error": str(e)}
        
        # Policy engine metrics
        if self.policy_engine:
            try:
                metrics["policy_engine"] = self.policy_engine.get_policy_metrics()
            except Exception as e:
                metrics["policy_engine"] = {"error": str(e)}
        
        # Framework hooks metrics
        if self.framework_hooks:
            try:
                metrics["framework_hooks"] = self.framework_hooks.get_metrics()
            except Exception as e:
                metrics["framework_hooks"] = {"error": str(e)}
        
        return metrics
    
    def get_memory_service(self) -> Optional[FlexibleMemoryService]:
        """Get the memory service instance."""
        return self.memory_service
    
    def get_trigger_orchestrator(self) -> Optional[MemoryTriggerOrchestrator]:
        """Get the trigger orchestrator instance."""
        return self.trigger_orchestrator
    
    def get_policy_engine(self) -> Optional[TriggerPolicyEngine]:
        """Get the policy engine instance."""
        return self.policy_engine
    
    def get_framework_hooks(self) -> Optional[FrameworkMemoryHooks]:
        """Get the framework hooks instance."""
        return self.framework_hooks
    
    async def cleanup(self):
        """Cleanup all service components."""
        self.logger.info("Cleaning up memory trigger service...")
        
        # Cleanup trigger orchestrator
        if self.trigger_orchestrator:
            try:
                await self.trigger_orchestrator.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up trigger orchestrator: {e}")
        
        # Cleanup memory service
        if self.memory_service:
            try:
                await self.memory_service.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up memory service: {e}")
        
        # Clear global hooks
        set_global_hooks(None)
        
        # Reset state
        self._initialized = False
        
        self.logger.info("Memory trigger service cleanup completed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MemoryTriggerService(initialized={self._initialized}, "
            f"enabled={self._enabled})"
        )


# Factory function for easy service creation
def create_memory_trigger_service(config: Dict[str, Any] = None) -> MemoryTriggerService:
    """
    Create a memory trigger service instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        MemoryTriggerService: Service instance
    """
    return MemoryTriggerService(config)


# Load configuration from file
def load_memory_trigger_config(config_path: str) -> Dict[str, Any]:
    """
    Load memory trigger configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    import json
    import yaml
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r') as f:
            if config_file.suffix.lower() == '.json':
                return json.load(f)
            elif config_file.suffix.lower() in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            else:
                # Try JSON first, then YAML
                content = f.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return yaml.safe_load(content)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load config from {config_path}: {e}")
        return {}


# Default configuration
DEFAULT_CONFIG = {
    "enabled": True,
    "memory": {
        "fallback_chain": ["mem0ai", "sqlite", "tinydb", "memory"],
        "circuit_breaker_threshold": 5,
        "circuit_breaker_recovery": 60,
        "detection_timeout": 2.0,
        "detection_retries": 3,
        "metrics_retention": 86400
    },
    "orchestrator": {
        "enabled": True,
        "max_queue_size": 1000,
        "batch_size": 10,
        "timeout_seconds": 30
    },
    "policies": {
        "enabled": True,
        "default_decision": "allow",
        "rate_limiting": True
    },
    "hooks": {
        "enabled": True,
        "capture_on_success": True,
        "capture_on_error": True,
        "capture_args": False,
        "capture_result": False
    }
}


# Global service instance
_global_service: Optional[MemoryTriggerService] = None


async def get_global_memory_trigger_service() -> Optional[MemoryTriggerService]:
    """
    Get the global memory trigger service instance.
    
    Returns:
        Optional[MemoryTriggerService]: Global service instance
    """
    return _global_service


async def initialize_global_memory_trigger_service(config: Dict[str, Any] = None) -> MemoryTriggerService:
    """
    Initialize the global memory trigger service.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        MemoryTriggerService: Initialized service instance
    """
    global _global_service
    
    if _global_service is None:
        # Merge with default config
        final_config = DEFAULT_CONFIG.copy()
        if config:
            final_config.update(config)
        
        _global_service = create_memory_trigger_service(final_config)
        await _global_service.initialize()
    
    return _global_service


async def cleanup_global_memory_trigger_service():
    """Cleanup the global memory trigger service."""
    global _global_service
    
    if _global_service:
        await _global_service.cleanup()
        _global_service = None