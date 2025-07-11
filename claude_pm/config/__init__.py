"""
Memory Trigger Configuration & Policy System

Comprehensive configuration and policy management for memory triggers.
Provides environment-specific configuration, validation, and policy engines.
"""

from .memory_trigger_config import (
    MemoryTriggerConfig,
    MemoryTriggerConfigManager,
    PerformanceConfig,
    TriggerPolicyConfig,
    LifecyclePolicyConfig,
    MonitoringConfig,
    BackendConfig,
    Environment,
    MemoryTriggerType,
    MemoryBackend,
    get_config_manager,
    initialize_config,
    get_config,
    apply_environment_overrides,
)

from .policy_engine_config import (
    PolicyEngine,
    PolicyEngineConfig,
    PolicyRule,
    PolicyCondition,
    PolicyAction,
    PolicyConditionType,
    PolicyActionType,
    PolicyScope,
    PolicyConditionEvaluator,
    get_policy_engine,
    initialize_policy_engine,
)

from .validation import (
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    ConfigurationSchemaValidator,
    RuntimeConfigurationValidator,
    PolicyValidator,
    ComprehensiveValidator,
    validate_config_dict,
    get_validation_summary,
    create_test_configuration,
)

__all__ = [
    # Configuration classes
    "MemoryTriggerConfig",
    "MemoryTriggerConfigManager",
    "PerformanceConfig",
    "TriggerPolicyConfig",
    "LifecyclePolicyConfig",
    "MonitoringConfig",
    "BackendConfig",
    # Enums
    "Environment",
    "MemoryTriggerType",
    "MemoryBackend",
    # Configuration functions
    "get_config_manager",
    "initialize_config",
    "get_config",
    "apply_environment_overrides",
    # Policy engine
    "PolicyEngine",
    "PolicyEngineConfig",
    "PolicyRule",
    "PolicyCondition",
    "PolicyAction",
    "PolicyConditionType",
    "PolicyActionType",
    "PolicyScope",
    "PolicyConditionEvaluator",
    "get_policy_engine",
    "initialize_policy_engine",
    # Validation
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    "ConfigurationSchemaValidator",
    "RuntimeConfigurationValidator",
    "PolicyValidator",
    "ComprehensiveValidator",
    "validate_config_dict",
    "get_validation_summary",
    "create_test_configuration",
]

# Version info
__version__ = "1.0.0"
__author__ = "Claude PM Framework Team"
__description__ = "Memory Trigger Configuration & Policy System"
