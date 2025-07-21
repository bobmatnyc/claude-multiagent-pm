"""
Factory functions and constants for hook processing service.
"""

from typing import Dict, Any, Optional

from .models import HookType


# Example configuration
DEFAULT_CONFIG = {
    'max_workers': 4,
    'max_history': 1000,
    'max_log_files': 10,
    'max_log_size_mb': 10,
    'project_root': None,  # Defaults to current working directory
    'alert_thresholds': {
        'execution_time': 10.0,
        'error_rate': 0.1,
        'failure_rate': 0.05
    },
    'async_by_default': True  # New default behavior
}


async def create_hook_processing_service(config: Optional[Dict[str, Any]] = None):
    """Create and start a hook processing service.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        HookProcessingService: Initialized and started service
    """
    from . import HookProcessingService
    
    service = HookProcessingService(config)
    await service.start()
    return service