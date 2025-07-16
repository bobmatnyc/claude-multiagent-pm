#!/usr/bin/env python3
"""
Memory Trigger Configuration Module
===================================

Configuration management for memory trigger systems, hot reloading,
and dynamic configuration updates.

Framework Version: 014
Implementation: 2025-07-16
"""

import asyncio
import logging
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class MemoryTriggerType(Enum):
    """Memory trigger types."""
    THRESHOLD = "threshold"
    PERIODIC = "periodic"
    EVENT_DRIVEN = "event_driven"
    ADAPTIVE = "adaptive"


class MemoryBackend(Enum):
    """Memory backend types."""
    REDIS = "redis"
    MEMCACHED = "memcached"
    IN_MEMORY = "in_memory"
    FILE_BASED = "file_based"


@dataclass
class PerformanceConfig:
    """Performance configuration settings."""
    max_memory_mb: int = 512
    cache_size: int = 1000
    gc_threshold: int = 700
    optimization_level: str = "standard"
    enable_monitoring: bool = True
    metrics_interval_seconds: int = 60
    
    def validate(self) -> bool:
        """Validate performance configuration."""
        try:
            assert self.max_memory_mb > 0, "max_memory_mb must be positive"
            assert self.cache_size > 0, "cache_size must be positive"
            assert self.gc_threshold > 0, "gc_threshold must be positive"
            assert self.optimization_level in ["minimal", "standard", "aggressive"], "Invalid optimization level"
            assert self.metrics_interval_seconds > 0, "metrics_interval_seconds must be positive"
            return True
        except AssertionError as e:
            logger.error(f"Performance config validation failed: {e}")
            return False


@dataclass
class TriggerPolicyConfig:
    """Trigger policy configuration."""
    enabled: bool = True
    trigger_threshold: float = 0.8
    cooldown_seconds: int = 300
    max_triggers_per_hour: int = 12
    priority_weights: Dict[str, float] = field(default_factory=lambda: {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.6,
        "low": 0.4
    })
    
    def validate(self) -> bool:
        """Validate trigger policy configuration."""
        try:
            assert 0.0 <= self.trigger_threshold <= 1.0, "trigger_threshold must be between 0 and 1"
            assert self.cooldown_seconds >= 0, "cooldown_seconds must be non-negative"
            assert self.max_triggers_per_hour > 0, "max_triggers_per_hour must be positive"
            
            for priority, weight in self.priority_weights.items():
                assert 0.0 <= weight <= 1.0, f"Priority weight for {priority} must be between 0 and 1"
            
            return True
        except AssertionError as e:
            logger.error(f"Trigger policy config validation failed: {e}")
            return False


@dataclass
class LifecyclePolicyConfig:
    """Lifecycle policy configuration."""
    auto_cleanup: bool = True
    retention_days: int = 30
    archive_after_days: int = 7
    max_archived_items: int = 1000
    cleanup_schedule: str = "daily"
    enable_compression: bool = True
    
    def validate(self) -> bool:
        """Validate lifecycle policy configuration."""
        try:
            assert self.retention_days > 0, "retention_days must be positive"
            assert self.archive_after_days > 0, "archive_after_days must be positive"
            assert self.max_archived_items > 0, "max_archived_items must be positive"
            assert self.cleanup_schedule in ["hourly", "daily", "weekly"], "Invalid cleanup schedule"
            return True
        except AssertionError as e:
            logger.error(f"Lifecycle policy config validation failed: {e}")
            return False


@dataclass
class BackendConfig:
    """Backend configuration settings."""
    backend_type: MemoryBackend = MemoryBackend.IN_MEMORY
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    connection_pool_size: int = 10
    timeout_seconds: int = 30
    retry_attempts: int = 3
    ssl_enabled: bool = False
    
    def validate(self) -> bool:
        """Validate backend configuration."""
        try:
            assert self.port > 0, "port must be positive"
            assert self.connection_pool_size > 0, "connection_pool_size must be positive"
            assert self.timeout_seconds > 0, "timeout_seconds must be positive"
            assert self.retry_attempts >= 0, "retry_attempts must be non-negative"
            return True
        except AssertionError as e:
            logger.error(f"Backend config validation failed: {e}")
            return False


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    log_level: str = "INFO"
    metrics_enabled: bool = True
    health_check_interval: int = 60
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "memory_usage": 0.85,
        "cpu_usage": 0.90,
        "error_rate": 0.05
    })
    notification_channels: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate monitoring configuration."""
        try:
            assert self.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "Invalid log level"
            assert self.health_check_interval > 0, "health_check_interval must be positive"
            
            for metric, threshold in self.alert_thresholds.items():
                assert 0.0 <= threshold <= 1.0, f"Alert threshold for {metric} must be between 0 and 1"
            
            return True
        except AssertionError as e:
            logger.error(f"Monitoring config validation failed: {e}")
            return False


@dataclass
class MemoryTriggerConfig:
    """Main memory trigger configuration."""
    version: str = "1.0"
    environment: str = "development"
    debug_mode: bool = False
    
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    trigger_policy: TriggerPolicyConfig = field(default_factory=TriggerPolicyConfig)
    lifecycle_policy: LifecyclePolicyConfig = field(default_factory=LifecyclePolicyConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    backend: BackendConfig = field(default_factory=BackendConfig)
    
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate entire configuration."""
        try:
            assert self.version, "version is required"
            assert self.environment in ["development", "staging", "production"], "Invalid environment"
            
            # Validate sub-configurations
            configs_valid = [
                self.performance.validate(),
                self.trigger_policy.validate(),
                self.lifecycle_policy.validate(),
                self.monitoring.validate(),
                self.backend.validate()
            ]
            
            return all(configs_valid)
            
        except AssertionError as e:
            logger.error(f"Memory trigger config validation failed: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'version': self.version,
            'environment': self.environment,
            'debug_mode': self.debug_mode,
            'performance': {
                'max_memory_mb': self.performance.max_memory_mb,
                'cache_size': self.performance.cache_size,
                'gc_threshold': self.performance.gc_threshold,
                'optimization_level': self.performance.optimization_level,
                'enable_monitoring': self.performance.enable_monitoring,
                'metrics_interval_seconds': self.performance.metrics_interval_seconds
            },
            'trigger_policy': {
                'enabled': self.trigger_policy.enabled,
                'trigger_threshold': self.trigger_policy.trigger_threshold,
                'cooldown_seconds': self.trigger_policy.cooldown_seconds,
                'max_triggers_per_hour': self.trigger_policy.max_triggers_per_hour,
                'priority_weights': self.trigger_policy.priority_weights
            },
            'lifecycle_policy': {
                'auto_cleanup': self.lifecycle_policy.auto_cleanup,
                'retention_days': self.lifecycle_policy.retention_days,
                'archive_after_days': self.lifecycle_policy.archive_after_days,
                'max_archived_items': self.lifecycle_policy.max_archived_items,
                'cleanup_schedule': self.lifecycle_policy.cleanup_schedule,
                'enable_compression': self.lifecycle_policy.enable_compression
            },
            'monitoring': {
                'enabled': self.monitoring.enabled,
                'log_level': self.monitoring.log_level,
                'metrics_enabled': self.monitoring.metrics_enabled,
                'health_check_interval': self.monitoring.health_check_interval,
                'alert_thresholds': self.monitoring.alert_thresholds,
                'notification_channels': self.monitoring.notification_channels
            },
            'backend': {
                'backend_type': self.backend.backend_type.value,
                'host': self.backend.host,
                'port': self.backend.port,
                'database': self.backend.database,
                'username': self.backend.username,
                'password': self.backend.password,
                'connection_pool_size': self.backend.connection_pool_size,
                'timeout_seconds': self.backend.timeout_seconds,
                'retry_attempts': self.backend.retry_attempts,
                'ssl_enabled': self.backend.ssl_enabled
            },
            'custom_settings': self.custom_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryTriggerConfig':
        """Create configuration from dictionary."""
        try:
            # Create sub-configurations
            performance = PerformanceConfig(**data.get('performance', {}))
            trigger_policy = TriggerPolicyConfig(**data.get('trigger_policy', {}))
            lifecycle_policy = LifecyclePolicyConfig(**data.get('lifecycle_policy', {}))
            monitoring = MonitoringConfig(**data.get('monitoring', {}))
            
            # Handle backend config with enum conversion
            backend_data = data.get('backend', {})
            if 'backend_type' in backend_data and isinstance(backend_data['backend_type'], str):
                backend_data['backend_type'] = MemoryBackend(backend_data['backend_type'])
            backend = BackendConfig(**backend_data)
            
            return cls(
                version=data.get('version', '1.0'),
                environment=data.get('environment', 'development'),
                debug_mode=data.get('debug_mode', False),
                performance=performance,
                trigger_policy=trigger_policy,
                lifecycle_policy=lifecycle_policy,
                monitoring=monitoring,
                backend=backend,
                custom_settings=data.get('custom_settings', {})
            )
            
        except Exception as e:
            logger.error(f"Error creating config from dict: {e}")
            # Return default config on error
            return cls()


class MemoryTriggerConfigManager:
    """Configuration manager with hot reloading and dynamic updates."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self.config = MemoryTriggerConfig()
        self.observers: List[Callable[[MemoryTriggerConfig], None]] = []
        self.watcher_thread: Optional[threading.Thread] = None
        self.watching = False
        self.last_modified = None
        
        # Load initial config if path provided
        if self.config_path and self.config_path.exists():
            self.load_config()
    
    def add_observer(self, callback: Callable[[MemoryTriggerConfig], None]):
        """Add configuration change observer."""
        self.observers.append(callback)
    
    def remove_observer(self, callback: Callable[[MemoryTriggerConfig], None]):
        """Remove configuration change observer."""
        if callback in self.observers:
            self.observers.remove(callback)
    
    def notify_observers(self):
        """Notify all observers of configuration changes."""
        for observer in self.observers:
            try:
                observer(self.config)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
    
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if not self.config_path or not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return False
            
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            new_config = MemoryTriggerConfig.from_dict(data)
            
            if new_config.validate():
                old_config = self.config
                self.config = new_config
                
                # Update last modified time
                self.last_modified = self.config_path.stat().st_mtime
                
                # Notify observers if config changed
                if old_config.to_dict() != new_config.to_dict():
                    self.notify_observers()
                
                logger.info(f"Configuration loaded from {self.config_path}")
                return True
            else:
                logger.error("Configuration validation failed")
                return False
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            if not self.config_path:
                logger.error("No config path set")
                return False
            
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config.to_dict(), f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values."""
        try:
            current_dict = self.config.to_dict()
            
            # Deep merge updates
            def deep_merge(base, updates):
                for key, value in updates.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            
            deep_merge(current_dict, updates)
            
            # Create new config from updated dict
            new_config = MemoryTriggerConfig.from_dict(current_dict)
            
            if new_config.validate():
                self.config = new_config
                self.notify_observers()
                
                # Save if path is set
                if self.config_path:
                    self.save_config()
                
                logger.info("Configuration updated successfully")
                return True
            else:
                logger.error("Updated configuration failed validation")
                return False
                
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False
    
    def start_watching(self):
        """Start watching configuration file for changes."""
        if self.watching or not self.config_path:
            return
        
        self.watching = True
        self.watcher_thread = threading.Thread(target=self._watch_config_file, daemon=True)
        self.watcher_thread.start()
        logger.info("Started watching configuration file")
    
    def stop_watching(self):
        """Stop watching configuration file."""
        self.watching = False
        if self.watcher_thread:
            self.watcher_thread.join(timeout=1.0)
        logger.info("Stopped watching configuration file")
    
    def _watch_config_file(self):
        """Watch configuration file for changes."""
        while self.watching:
            try:
                if self.config_path and self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime
                    
                    if self.last_modified is None:
                        self.last_modified = current_mtime
                    elif current_mtime > self.last_modified:
                        logger.info("Configuration file changed, reloading...")
                        self.load_config()
                
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                logger.error(f"Error watching config file: {e}")
                time.sleep(5.0)  # Wait longer on error
    
    def get_config(self) -> MemoryTriggerConfig:
        """Get current configuration."""
        return self.config
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration."""
        return self.config.performance
    
    def get_trigger_policy_config(self) -> TriggerPolicyConfig:
        """Get trigger policy configuration."""
        return self.config.trigger_policy
    
    def get_lifecycle_policy_config(self) -> LifecyclePolicyConfig:
        """Get lifecycle policy configuration."""
        return self.config.lifecycle_policy
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        return self.config.monitoring


class ConfigurationFileWatcher:
    """Watch configuration files for changes."""
    
    def __init__(self, config_manager: MemoryTriggerConfigManager):
        self.config_manager = config_manager
        self.watching = False
    
    def start_watching(self):
        """Start watching for configuration changes."""
        self.watching = True
        self.config_manager.start_watching()
    
    def stop_watching(self):
        """Stop watching for configuration changes."""
        self.watching = False
        self.config_manager.stop_watching()


# Global configuration manager instance
_global_config_manager: Optional[MemoryTriggerConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> MemoryTriggerConfigManager:
    """Get global configuration manager instance."""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = create_config_manager(config_path)
    return _global_config_manager


def initialize_config(config_path: Optional[str] = None) -> bool:
    """Initialize global configuration."""
    manager = get_config_manager(config_path)
    if config_path:
        return manager.load_config()
    return True


def get_config() -> MemoryTriggerConfig:
    """Get current global configuration."""
    manager = get_config_manager()
    return manager.get_config()


def apply_environment_overrides(config: MemoryTriggerConfig, 
                              env_overrides: Dict[str, Any]) -> MemoryTriggerConfig:
    """Apply environment-specific configuration overrides."""
    try:
        config_dict = config.to_dict()
        
        # Apply environment overrides
        for key, value in env_overrides.items():
            if '.' in key:
                # Handle nested keys like 'performance.max_memory_mb'
                parts = key.split('.')
                current = config_dict
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                config_dict[key] = value
        
        return MemoryTriggerConfig.from_dict(config_dict)
        
    except Exception as e:
        logger.error(f"Error applying environment overrides: {e}")
        return config


# Factory functions
def create_default_config() -> MemoryTriggerConfig:
    """Create default configuration."""
    return MemoryTriggerConfig()


def create_config_manager(config_path: Optional[str] = None) -> MemoryTriggerConfigManager:
    """Create configuration manager."""
    return MemoryTriggerConfigManager(config_path)


# For backwards compatibility and testing
Observer = MemoryTriggerConfigManager  # Mock Observer class for tests


if __name__ == "__main__":
    # Demo functionality
    def demo():
        """Demonstrate memory trigger configuration."""
        print("🔧 Memory Trigger Configuration Demo")
        print("=" * 45)
        
        # Create default config
        config = create_default_config()
        print(f"Default config valid: {config.validate()}")
        
        # Create config manager
        manager = create_config_manager()
        
        # Add observer
        def config_changed(new_config):
            print(f"Configuration changed! Environment: {new_config.environment}")
        
        manager.add_observer(config_changed)
        
        # Update config
        updates = {
            'environment': 'production',
            'performance': {
                'max_memory_mb': 1024,
                'optimization_level': 'aggressive'
            }
        }
        
        success = manager.update_config(updates)
        print(f"Config update success: {success}")
        
        # Get current config
        current = manager.get_config()
        print(f"Current environment: {current.environment}")
        print(f"Current max memory: {current.performance.max_memory_mb}MB")
    
    demo()