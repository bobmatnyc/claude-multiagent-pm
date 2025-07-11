"""
Memory Trigger Configuration System

Comprehensive configuration management for memory triggers, policies, and lifecycle management.
Provides environment-specific configuration, hot reloading, and schema validation.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import timedelta
from enum import Enum
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class MemoryTriggerType(Enum):
    """Types of memory triggers available"""

    WORKFLOW = "workflow"
    AGENT = "agent"
    TASK = "task"
    ERROR = "error"
    SUCCESS = "success"
    PATTERN = "pattern"
    CONTEXT = "context"
    LIFECYCLE = "lifecycle"


class MemoryBackend(Enum):
    """Available memory storage backends"""

    MEM0 = "mem0"
    LOCAL = "local"
    REDIS = "redis"
    POSTGRESQL = "postgresql"
    HYBRID = "hybrid"


class Environment(Enum):
    """Deployment environments"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class PerformanceConfig:
    """Performance tuning configuration"""

    # Memory operation timeouts
    create_timeout: float = 5.0
    recall_timeout: float = 3.0
    search_timeout: float = 10.0

    # Batch processing
    batch_size: int = 50
    max_concurrent_operations: int = 10
    rate_limit_per_second: int = 100

    # Cache configuration
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000

    # Memory thresholds
    max_memory_size_mb: int = 100
    memory_cleanup_threshold: float = 0.8

    # Quality thresholds
    min_memory_quality_score: float = 0.6
    max_memories_per_context: int = 100

    # Background processing
    background_processing_enabled: bool = True
    background_queue_size: int = 1000
    worker_thread_count: int = 3

    def validate(self) -> List[str]:
        """Validate performance configuration"""
        errors = []

        if self.create_timeout <= 0:
            errors.append("create_timeout must be positive")
        if self.recall_timeout <= 0:
            errors.append("recall_timeout must be positive")
        if self.batch_size <= 0:
            errors.append("batch_size must be positive")
        if self.max_concurrent_operations <= 0:
            errors.append("max_concurrent_operations must be positive")
        if self.min_memory_quality_score < 0 or self.min_memory_quality_score > 1:
            errors.append("min_memory_quality_score must be between 0 and 1")
        if self.memory_cleanup_threshold < 0 or self.memory_cleanup_threshold > 1:
            errors.append("memory_cleanup_threshold must be between 0 and 1")

        return errors


@dataclass
class TriggerPolicyConfig:
    """Configuration for specific trigger types"""

    enabled: bool = True
    trigger_type: MemoryTriggerType = MemoryTriggerType.WORKFLOW

    # Trigger conditions
    success_threshold: float = 0.8
    failure_threshold: float = 0.3
    create_on_success: bool = True
    create_on_failure: bool = True
    create_on_error: bool = True

    # Pattern detection
    pattern_detection_enabled: bool = True
    pattern_similarity_threshold: float = 0.7

    # Context requirements
    min_context_length: int = 10
    max_context_length: int = 10000
    context_required_fields: List[str] = field(default_factory=list)

    # Quality requirements
    require_quality_validation: bool = True
    min_trigger_confidence: float = 0.6

    # Rate limiting
    max_triggers_per_minute: int = 60
    cooldown_period_seconds: int = 30

    # Agent-specific settings
    agent_name: Optional[str] = None
    agent_trigger_patterns: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """Validate trigger policy configuration"""
        errors = []

        if self.success_threshold < 0 or self.success_threshold > 1:
            errors.append("success_threshold must be between 0 and 1")
        if self.failure_threshold < 0 or self.failure_threshold > 1:
            errors.append("failure_threshold must be between 0 and 1")
        if self.pattern_similarity_threshold < 0 or self.pattern_similarity_threshold > 1:
            errors.append("pattern_similarity_threshold must be between 0 and 1")
        if self.min_context_length < 0:
            errors.append("min_context_length must be non-negative")
        if self.max_context_length <= self.min_context_length:
            errors.append("max_context_length must be greater than min_context_length")
        if self.min_trigger_confidence < 0 or self.min_trigger_confidence > 1:
            errors.append("min_trigger_confidence must be between 0 and 1")
        if self.max_triggers_per_minute <= 0:
            errors.append("max_triggers_per_minute must be positive")
        if self.cooldown_period_seconds < 0:
            errors.append("cooldown_period_seconds must be non-negative")

        return errors


@dataclass
class LifecyclePolicyConfig:
    """Memory lifecycle management configuration"""

    # Retention policies
    default_retention_days: int = 90
    important_memory_retention_days: int = 365
    error_memory_retention_days: int = 30
    workflow_memory_retention_days: int = 180

    # Cleanup policies
    auto_cleanup_enabled: bool = True
    cleanup_interval_hours: int = 24
    cleanup_batch_size: int = 100

    # Quality-based cleanup
    quality_based_cleanup: bool = True
    min_quality_for_retention: float = 0.4

    # Archival policies
    archival_enabled: bool = False
    archive_after_days: int = 365
    archive_backend: Optional[str] = None

    # Migration policies
    migration_enabled: bool = False
    migration_schedule: Optional[str] = None  # Cron expression

    # Compression
    compression_enabled: bool = True
    compression_after_days: int = 7

    def validate(self) -> List[str]:
        """Validate lifecycle policy configuration"""
        errors = []

        if self.default_retention_days <= 0:
            errors.append("default_retention_days must be positive")
        if self.important_memory_retention_days <= 0:
            errors.append("important_memory_retention_days must be positive")
        if self.error_memory_retention_days <= 0:
            errors.append("error_memory_retention_days must be positive")
        if self.workflow_memory_retention_days <= 0:
            errors.append("workflow_memory_retention_days must be positive")
        if self.cleanup_interval_hours <= 0:
            errors.append("cleanup_interval_hours must be positive")
        if self.cleanup_batch_size <= 0:
            errors.append("cleanup_batch_size must be positive")
        if self.min_quality_for_retention < 0 or self.min_quality_for_retention > 1:
            errors.append("min_quality_for_retention must be between 0 and 1")
        if self.archive_after_days <= 0:
            errors.append("archive_after_days must be positive")
        if self.compression_after_days < 0:
            errors.append("compression_after_days must be non-negative")

        return errors


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""

    # Metrics collection
    metrics_enabled: bool = True
    metrics_collection_interval: int = 60
    metrics_retention_days: int = 30

    # Performance monitoring
    performance_monitoring_enabled: bool = True
    slow_operation_threshold_ms: int = 1000
    error_rate_threshold: float = 0.05

    # Health checks
    health_check_enabled: bool = True
    health_check_interval: int = 30
    health_check_timeout: int = 5

    # Logging configuration
    log_level: str = "INFO"
    log_memory_operations: bool = True
    log_performance_metrics: bool = False
    structured_logging: bool = True

    # Alerting
    alerting_enabled: bool = False
    alert_channels: List[str] = field(default_factory=list)
    error_alert_threshold: int = 10
    performance_alert_threshold: float = 2.0

    def validate(self) -> List[str]:
        """Validate monitoring configuration"""
        errors = []

        if self.metrics_collection_interval <= 0:
            errors.append("metrics_collection_interval must be positive")
        if self.metrics_retention_days <= 0:
            errors.append("metrics_retention_days must be positive")
        if self.slow_operation_threshold_ms <= 0:
            errors.append("slow_operation_threshold_ms must be positive")
        if self.error_rate_threshold < 0 or self.error_rate_threshold > 1:
            errors.append("error_rate_threshold must be between 0 and 1")
        if self.health_check_interval <= 0:
            errors.append("health_check_interval must be positive")
        if self.health_check_timeout <= 0:
            errors.append("health_check_timeout must be positive")
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append("log_level must be a valid logging level")
        if self.error_alert_threshold <= 0:
            errors.append("error_alert_threshold must be positive")
        if self.performance_alert_threshold <= 0:
            errors.append("performance_alert_threshold must be positive")

        return errors


@dataclass
class BackendConfig:
    """Memory backend configuration"""

    backend_type: MemoryBackend = MemoryBackend.MEM0

    # Connection settings
    connection_timeout: float = 10.0
    read_timeout: float = 5.0
    write_timeout: float = 10.0
    max_retries: int = 3
    retry_delay: float = 1.0

    # Backend-specific settings
    backend_settings: Dict[str, Any] = field(default_factory=dict)

    # Connection pooling
    pool_enabled: bool = True
    pool_size: int = 10
    pool_max_overflow: int = 20

    # Failover settings
    failover_enabled: bool = False
    failover_backends: List[str] = field(default_factory=list)

    # Encryption
    encryption_enabled: bool = False
    encryption_key_path: Optional[str] = None

    def validate(self) -> List[str]:
        """Validate backend configuration"""
        errors = []

        if self.connection_timeout <= 0:
            errors.append("connection_timeout must be positive")
        if self.read_timeout <= 0:
            errors.append("read_timeout must be positive")
        if self.write_timeout <= 0:
            errors.append("write_timeout must be positive")
        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")
        if self.retry_delay < 0:
            errors.append("retry_delay must be non-negative")
        if self.pool_size <= 0:
            errors.append("pool_size must be positive")
        if self.pool_max_overflow < 0:
            errors.append("pool_max_overflow must be non-negative")
        if self.encryption_enabled and not self.encryption_key_path:
            errors.append("encryption_key_path required when encryption_enabled")

        return errors


@dataclass
class MemoryTriggerConfig:
    """Main memory trigger configuration"""

    # Environment and basic settings
    environment: Environment = Environment.DEVELOPMENT
    debug_mode: bool = False
    config_version: str = "1.0"

    # Core components
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    lifecycle: LifecyclePolicyConfig = field(default_factory=LifecyclePolicyConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    backend: BackendConfig = field(default_factory=BackendConfig)

    # Trigger policies
    trigger_policies: Dict[str, TriggerPolicyConfig] = field(default_factory=dict)

    # Feature toggles
    features: Dict[str, bool] = field(
        default_factory=lambda: {
            "workflow_triggers": True,
            "agent_triggers": True,
            "error_triggers": True,
            "pattern_detection": True,
            "auto_recall": True,
            "quality_assessment": True,
            "background_processing": True,
            "hot_reloading": True,
        }
    )

    # Global settings
    global_enabled: bool = True
    max_memory_operations_per_second: int = 100

    # Configuration management
    config_file_path: Optional[str] = None
    auto_reload: bool = True
    validation_strict: bool = True

    def validate(self) -> List[str]:
        """Validate entire configuration"""
        errors = []

        # Validate sub-configurations
        errors.extend(self.performance.validate())
        errors.extend(self.lifecycle.validate())
        errors.extend(self.monitoring.validate())
        errors.extend(self.backend.validate())

        # Validate trigger policies
        for name, policy in self.trigger_policies.items():
            policy_errors = policy.validate()
            for error in policy_errors:
                errors.append(f"Trigger policy '{name}': {error}")

        # Validate global settings
        if self.max_memory_operations_per_second <= 0:
            errors.append("max_memory_operations_per_second must be positive")

        # Cross-validation
        if self.performance.max_concurrent_operations > self.max_memory_operations_per_second:
            errors.append(
                "max_concurrent_operations cannot exceed max_memory_operations_per_second"
            )

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryTriggerConfig":
        """Create configuration from dictionary"""
        # Convert environment string to enum
        if "environment" in data and isinstance(data["environment"], str):
            data["environment"] = Environment(data["environment"])

        # Handle nested configurations
        if "performance" in data:
            data["performance"] = PerformanceConfig(**data["performance"])

        if "lifecycle" in data:
            data["lifecycle"] = LifecyclePolicyConfig(**data["lifecycle"])

        if "monitoring" in data:
            data["monitoring"] = MonitoringConfig(**data["monitoring"])

        if "backend" in data:
            if "backend_type" in data["backend"] and isinstance(
                data["backend"]["backend_type"], str
            ):
                data["backend"]["backend_type"] = MemoryBackend(data["backend"]["backend_type"])
            data["backend"] = BackendConfig(**data["backend"])

        # Handle trigger policies
        if "trigger_policies" in data:
            policies = {}
            for name, policy_data in data["trigger_policies"].items():
                if "trigger_type" in policy_data and isinstance(policy_data["trigger_type"], str):
                    policy_data["trigger_type"] = MemoryTriggerType(policy_data["trigger_type"])
                policies[name] = TriggerPolicyConfig(**policy_data)
            data["trigger_policies"] = policies

        return cls(**data)


class ConfigurationFileWatcher(FileSystemEventHandler):
    """File system watcher for configuration hot reloading"""

    def __init__(self, config_manager: "MemoryTriggerConfigManager"):
        self.config_manager = config_manager
        self.last_reload = time.time()
        self.reload_cooldown = 1.0  # Prevent rapid reloads

    def on_modified(self, event):
        if event.is_directory:
            return

        current_time = time.time()
        if current_time - self.last_reload < self.reload_cooldown:
            return

        if event.src_path == self.config_manager.config_file_path:
            logger.info(f"Configuration file modified: {event.src_path}")
            try:
                self.config_manager.reload_config()
                self.last_reload = current_time
                logger.info("Configuration reloaded successfully")
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")


class MemoryTriggerConfigManager:
    """Configuration manager with hot reloading and validation"""

    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path
        self.config: Optional[MemoryTriggerConfig] = None
        self.observer: Optional[Observer] = None
        self.watcher: Optional[ConfigurationFileWatcher] = None
        self._lock = threading.RLock()

        # Load initial configuration
        if config_file_path:
            self.load_config_from_file(config_file_path)
        else:
            self.config = MemoryTriggerConfig()

    def load_config_from_file(self, file_path: str) -> None:
        """Load configuration from YAML file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            with self._lock:
                self.config = MemoryTriggerConfig.from_dict(data)
                self.config.config_file_path = file_path

                # Validate configuration
                if self.config.validation_strict:
                    errors = self.config.validate()
                    if errors:
                        raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

                # Setup hot reloading if enabled
                if self.config.auto_reload:
                    self._setup_hot_reloading(file_path)

            logger.info(f"Configuration loaded from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            raise

    def save_config_to_file(self, file_path: Optional[str] = None) -> None:
        """Save current configuration to YAML file"""
        if not file_path:
            file_path = self.config_file_path

        if not file_path:
            raise ValueError("No file path specified for saving configuration")

        try:
            with self._lock:
                data = self.config.to_dict()

                # Convert enums to strings for YAML serialization
                self._convert_enums_to_strings(data)

                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, indent=2)

            logger.info(f"Configuration saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
            raise

    def _convert_enums_to_strings(self, data: Any) -> None:
        """Convert enum values to strings for YAML serialization"""
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(value, "value"):  # Enum
                    data[key] = value.value
                else:
                    self._convert_enums_to_strings(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if hasattr(item, "value"):  # Enum
                    data[i] = item.value
                else:
                    self._convert_enums_to_strings(item)

    def _setup_hot_reloading(self, file_path: str) -> None:
        """Setup file system watcher for hot reloading"""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()

            self.watcher = ConfigurationFileWatcher(self)
            self.observer = Observer()

            watch_dir = Path(file_path).parent
            self.observer.schedule(self.watcher, str(watch_dir), recursive=False)
            self.observer.start()

            logger.info(f"Hot reloading enabled for {file_path}")

        except Exception as e:
            logger.warning(f"Failed to setup hot reloading: {e}")

    def reload_config(self) -> None:
        """Reload configuration from file"""
        if not self.config_file_path:
            raise ValueError("No configuration file path available for reloading")

        self.load_config_from_file(self.config_file_path)

    def get_config(self) -> MemoryTriggerConfig:
        """Get current configuration (thread-safe)"""
        with self._lock:
            if not self.config:
                self.config = MemoryTriggerConfig()
            return self.config

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        with self._lock:
            if not self.config:
                self.config = MemoryTriggerConfig()

            # Apply updates
            current_dict = self.config.to_dict()
            self._deep_update(current_dict, updates)

            # Create new config
            new_config = MemoryTriggerConfig.from_dict(current_dict)

            # Validate if strict validation is enabled
            if self.config.validation_strict:
                errors = new_config.validate()
                if errors:
                    raise ValueError(f"Configuration update validation failed: {', '.join(errors)}")

            self.config = new_config

            # Save if file path is available
            if self.config_file_path:
                self.save_config_to_file()

    def _deep_update(self, base_dict: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Deep update dictionary"""
        for key, value in updates.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def get_trigger_policy(self, name: str) -> Optional[TriggerPolicyConfig]:
        """Get specific trigger policy configuration"""
        with self._lock:
            return self.config.trigger_policies.get(name) if self.config else None

    def add_trigger_policy(self, name: str, policy: TriggerPolicyConfig) -> None:
        """Add or update trigger policy"""
        with self._lock:
            if not self.config:
                self.config = MemoryTriggerConfig()

            # Validate policy
            errors = policy.validate()
            if errors and self.config.validation_strict:
                raise ValueError(f"Trigger policy validation failed: {', '.join(errors)}")

            self.config.trigger_policies[name] = policy

            # Save if file path is available
            if self.config_file_path:
                self.save_config_to_file()

    def remove_trigger_policy(self, name: str) -> bool:
        """Remove trigger policy"""
        with self._lock:
            if self.config and name in self.config.trigger_policies:
                del self.config.trigger_policies[name]

                # Save if file path is available
                if self.config_file_path:
                    self.save_config_to_file()

                return True
            return False

    def validate_config(self) -> List[str]:
        """Validate current configuration"""
        with self._lock:
            if not self.config:
                return ["No configuration loaded"]
            return self.config.validate()

    def get_environment_config_path(self, environment: Environment, base_path: str) -> str:
        """Get environment-specific configuration file path"""
        base_dir = Path(base_path).parent
        base_name = Path(base_path).stem
        extension = Path(base_path).suffix

        return str(base_dir / f"{base_name}.{environment.value}{extension}")

    def shutdown(self) -> None:
        """Shutdown configuration manager"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self.watcher = None
        logger.info("Configuration manager shutdown complete")


# Global configuration manager instance
_config_manager: Optional[MemoryTriggerConfigManager] = None


def get_config_manager() -> MemoryTriggerConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = MemoryTriggerConfigManager()
    return _config_manager


def initialize_config(config_file_path: Optional[str] = None) -> MemoryTriggerConfigManager:
    """Initialize global configuration manager"""
    global _config_manager
    _config_manager = MemoryTriggerConfigManager(config_file_path)
    return _config_manager


def get_config() -> MemoryTriggerConfig:
    """Get current configuration"""
    return get_config_manager().get_config()


# Environment variable overrides
def apply_environment_overrides(config: MemoryTriggerConfig) -> None:
    """Apply environment variable overrides to configuration"""
    # Performance overrides
    if os.getenv("MEMORY_CREATE_TIMEOUT"):
        config.performance.create_timeout = float(os.getenv("MEMORY_CREATE_TIMEOUT"))

    if os.getenv("MEMORY_RECALL_TIMEOUT"):
        config.performance.recall_timeout = float(os.getenv("MEMORY_RECALL_TIMEOUT"))

    if os.getenv("MEMORY_BATCH_SIZE"):
        config.performance.batch_size = int(os.getenv("MEMORY_BATCH_SIZE"))

    if os.getenv("MEMORY_MAX_CONCURRENT"):
        config.performance.max_concurrent_operations = int(os.getenv("MEMORY_MAX_CONCURRENT"))

    # Backend overrides
    if os.getenv("MEMORY_BACKEND_TYPE"):
        config.backend.backend_type = MemoryBackend(os.getenv("MEMORY_BACKEND_TYPE"))

    if os.getenv("MEMORY_CONNECTION_TIMEOUT"):
        config.backend.connection_timeout = float(os.getenv("MEMORY_CONNECTION_TIMEOUT"))

    # Feature toggles
    if os.getenv("MEMORY_TRIGGERS_ENABLED"):
        config.global_enabled = os.getenv("MEMORY_TRIGGERS_ENABLED").lower() == "true"

    if os.getenv("MEMORY_DEBUG_MODE"):
        config.debug_mode = os.getenv("MEMORY_DEBUG_MODE").lower() == "true"

    # Environment
    if os.getenv("MEMORY_ENVIRONMENT"):
        config.environment = Environment(os.getenv("MEMORY_ENVIRONMENT"))
