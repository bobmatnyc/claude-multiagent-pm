"""
Configuration System

Comprehensive configuration management for the Claude PM Framework.
Includes model configuration, environment defaults, and framework initialization.
"""

from .model_configuration import (
    IntegratedModelConfiguration,
    get_integrated_model_config,
    get_model_for_agent,
    validate_model_configuration,
    initialize_model_configuration_defaults
)

from .default_model_config import (
    DefaultModelConfigManager,
    get_default_model_config,
    get_default_model_for_agent_type,
    validate_default_model_configuration,
    generate_model_env_template
)

from .model_env_defaults import (
    ModelEnvironmentLoader,
    DeploymentEnvironment,
    load_model_environment_defaults,
    get_model_for_agent_from_env,
    initialize_model_environment_defaults,
    generate_model_env_file
)

from .framework_initialization import (
    FrameworkModelConfigInitializer,
    FrameworkHealthChecker,
    FrameworkInitializationStatus,
    initialize_framework_model_configuration,
    check_framework_model_health,
    validate_framework_model_configuration
)

__all__ = [
    # Main model configuration
    "IntegratedModelConfiguration",
    "get_integrated_model_config",
    "get_model_for_agent",
    "validate_model_configuration",
    "initialize_model_configuration_defaults",
    
    # Default model configuration
    "DefaultModelConfigManager",
    "get_default_model_config",
    "get_default_model_for_agent_type",
    "validate_default_model_configuration",
    "generate_model_env_template",
    
    # Environment configuration
    "ModelEnvironmentLoader",
    "DeploymentEnvironment",
    "load_model_environment_defaults",
    "get_model_for_agent_from_env",
    "initialize_model_environment_defaults",
    "generate_model_env_file",
    
    # Framework initialization
    "FrameworkModelConfigInitializer",
    "FrameworkHealthChecker",
    "FrameworkInitializationStatus",
    "initialize_framework_model_configuration",
    "check_framework_model_health",
    "validate_framework_model_configuration"
]

# Version info
__version__ = "2.0.0"
__author__ = "Claude PM Framework Team"
__description__ = "Configuration System with Model Management"

# Quick access functions
def get_model_assignment(agent_type: str) -> str:
    """Quick function to get model assignment for an agent type."""
    return get_model_for_agent(agent_type)

def validate_configuration() -> dict:
    """Quick function to validate the complete configuration."""
    return validate_model_configuration()

def initialize_defaults() -> dict:
    """Quick function to initialize configuration defaults."""
    return initialize_model_configuration_defaults()
