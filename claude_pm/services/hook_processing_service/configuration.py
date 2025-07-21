"""
System for managing hook configurations and registration.
"""

import logging
import weakref
from typing import Dict, List, Optional, Any

from .models import HookConfiguration, HookType


class HookConfigurationSystem:
    """System for managing hook configurations and registration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hooks: Dict[str, HookConfiguration] = {}
        self.hook_groups: Dict[HookType, List[str]] = {hook_type: [] for hook_type in HookType}
        self.weak_refs: Dict[str, weakref.ref] = {}
    
    def register_hook(self, hook_config: HookConfiguration) -> bool:
        """Register a new hook configuration."""
        try:
            if hook_config.hook_id in self.hooks:
                self.logger.warning(f"Hook {hook_config.hook_id} already registered, updating...")
            
            # Validate hook configuration
            if not callable(hook_config.handler):
                raise ValueError(f"Handler for hook {hook_config.hook_id} is not callable")
            
            # Store configuration
            self.hooks[hook_config.hook_id] = hook_config
            
            # Add to hook type group
            if hook_config.hook_id not in self.hook_groups[hook_config.hook_type]:
                self.hook_groups[hook_config.hook_type].append(hook_config.hook_id)
            
            # Create weak reference if handler is a bound method
            if hasattr(hook_config.handler, '__self__'):
                self.weak_refs[hook_config.hook_id] = weakref.ref(hook_config.handler.__self__)
            
            self.logger.info(f"Registered hook: {hook_config.hook_id} ({hook_config.hook_type.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register hook {hook_config.hook_id}: {str(e)}")
            return False
    
    def unregister_hook(self, hook_id: str) -> bool:
        """Unregister a hook configuration."""
        try:
            if hook_id not in self.hooks:
                self.logger.warning(f"Hook {hook_id} not found for unregistration")
                return False
            
            hook_config = self.hooks[hook_id]
            
            # Remove from hook type group
            if hook_id in self.hook_groups[hook_config.hook_type]:
                self.hook_groups[hook_config.hook_type].remove(hook_id)
            
            # Remove weak reference
            if hook_id in self.weak_refs:
                del self.weak_refs[hook_id]
            
            # Remove configuration
            del self.hooks[hook_id]
            
            self.logger.info(f"Unregistered hook: {hook_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister hook {hook_id}: {str(e)}")
            return False
    
    def get_hooks_by_type(self, hook_type: HookType) -> List[HookConfiguration]:
        """Get all enabled hooks of a specific type, sorted by priority."""
        hook_ids = self.hook_groups[hook_type]
        hooks = [self.hooks[hook_id] for hook_id in hook_ids if hook_id in self.hooks]
        
        # Filter enabled hooks and sort by priority
        enabled_hooks = [hook for hook in hooks if hook.enabled]
        return sorted(enabled_hooks, key=lambda h: h.priority, reverse=True)
    
    def get_hook(self, hook_id: str) -> Optional[HookConfiguration]:
        """Get a specific hook configuration."""
        return self.hooks.get(hook_id)
    
    def update_hook_status(self, hook_id: str, enabled: bool) -> bool:
        """Enable or disable a hook."""
        if hook_id not in self.hooks:
            return False
        
        self.hooks[hook_id].enabled = enabled
        self.logger.info(f"Hook {hook_id} {'enabled' if enabled else 'disabled'}")
        return True
    
    def get_configuration_stats(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        total_hooks = len(self.hooks)
        enabled_hooks = sum(1 for hook in self.hooks.values() if hook.enabled)
        
        return {
            'total_hooks': total_hooks,
            'enabled_hooks': enabled_hooks,
            'disabled_hooks': total_hooks - enabled_hooks,
            'hooks_by_type': {
                hook_type.value: len(self.hook_groups[hook_type])
                for hook_type in HookType
            },
            'dead_references': sum(
                1 for ref in self.weak_refs.values() if ref() is None
            )
        }
    
    def cleanup_dead_references(self):
        """Clean up dead weak references."""
        dead_refs = [
            hook_id for hook_id, ref in self.weak_refs.items()
            if ref() is None
        ]
        
        for hook_id in dead_refs:
            self.logger.info(f"Cleaning up dead reference for hook: {hook_id}")
            self.unregister_hook(hook_id)