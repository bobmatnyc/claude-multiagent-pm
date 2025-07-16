"""
Model Environment Variable Defaults for Claude PM Framework
===========================================================

Provides environment variable defaults and loading mechanisms for model configuration.
This module ensures consistent model selection across different deployment environments.

Key Features:
- Environment variable defaults
- Configuration validation
- Development vs production settings
- Deployment-specific overrides
- Fallback configuration

Created: 2025-07-16
"""

import os
import logging
from typing import Dict, Optional, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ModelEnvironmentDefaults:
    """Default environment variable configuration for models"""
    
    # Global defaults
    CLAUDE_PM_MODEL_OVERRIDE: Optional[str] = None
    CLAUDE_PM_DEPLOYMENT_ENV: str = DeploymentEnvironment.DEVELOPMENT.value
    CLAUDE_PM_MODEL_CACHE_ENABLED: str = "true"
    CLAUDE_PM_MODEL_CACHE_TTL: str = "300"
    CLAUDE_PM_MODEL_VALIDATION_ENABLED: str = "true"
    CLAUDE_PM_MODEL_FALLBACK_ENABLED: str = "true"
    CLAUDE_PM_MODEL_DEBUG_LOGGING: str = "false"
    
    # Agent-specific defaults (Claude 4 Opus for orchestrator/engineer, Claude 4 Sonnet for others)
    CLAUDE_PM_MODEL_ORCHESTRATOR: str = "claude-4-opus"
    CLAUDE_PM_MODEL_ENGINEER: str = "claude-4-opus"
    CLAUDE_PM_MODEL_ARCHITECTURE: str = "claude-4-opus"
    CLAUDE_PM_MODEL_PERFORMANCE: str = "claude-4-opus"
    CLAUDE_PM_MODEL_INTEGRATION: str = "claude-4-opus"
    CLAUDE_PM_MODEL_BACKEND: str = "claude-4-opus"
    CLAUDE_PM_MODEL_MACHINE_LEARNING: str = "claude-4-opus"
    CLAUDE_PM_MODEL_DATA_SCIENCE: str = "claude-4-opus"
    
    # Sonnet for balanced performance agents
    CLAUDE_PM_MODEL_DOCUMENTATION: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_QA: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_RESEARCH: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_OPS: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_SECURITY: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_DATA_ENGINEER: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_TICKETING: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_VERSION_CONTROL: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_UI_UX: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_FRONTEND: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_DATABASE: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_API: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_TESTING: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_MONITORING: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_ANALYTICS: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_DEPLOYMENT: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_WORKFLOW: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_DEVOPS: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_CLOUD: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_INFRASTRUCTURE: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_BUSINESS_ANALYSIS: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_PROJECT_MANAGEMENT: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_COMPLIANCE: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_CONTENT: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_CUSTOMER_SUPPORT: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_MARKETING: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_SCAFFOLDING: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_CODE_REVIEW: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_MEMORY_MANAGEMENT: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_KNOWLEDGE_BASE: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_VALIDATION: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_AUTOMATION: str = "claude-sonnet-4-20250514"
    CLAUDE_PM_MODEL_CUSTOM: str = "claude-sonnet-4-20250514"
    
    # Fallback model
    CLAUDE_PM_MODEL_FALLBACK: str = "claude-sonnet-4-20250514"


class ModelEnvironmentLoader:
    """
    Loads and manages model environment variable configuration with defaults
    and deployment-specific settings.
    """
    
    def __init__(self, deployment_env: Optional[DeploymentEnvironment] = None):
        """Initialize model environment loader."""
        self.deployment_env = deployment_env or self._detect_deployment_environment()
        self.defaults = ModelEnvironmentDefaults()
        self._loaded_config: Optional[Dict[str, str]] = None
        
        logger.info(f"ModelEnvironmentLoader initialized for {self.deployment_env.value} environment")
    
    def load_configuration(self, apply_defaults: bool = True) -> Dict[str, str]:
        """
        Load model configuration from environment variables with defaults.
        
        Args:
            apply_defaults: Whether to apply default values for missing variables
            
        Returns:
            Dictionary of configuration values
        """
        if self._loaded_config is not None:
            return self._loaded_config
        
        config = {}
        
        # Get all default configuration attributes
        default_attrs = {
            attr: getattr(self.defaults, attr)
            for attr in dir(self.defaults)
            if not attr.startswith('_') and attr.isupper()
        }
        
        # Load from environment with defaults
        for env_var, default_value in default_attrs.items():
            if apply_defaults:
                config[env_var] = os.getenv(env_var, default_value)
            else:
                env_value = os.getenv(env_var)
                if env_value is not None:
                    config[env_var] = env_value
        
        # Apply deployment-specific overrides
        config = self._apply_deployment_overrides(config)
        
        # Validate configuration
        validation_results = self._validate_configuration(config)
        if not validation_results["valid"]:
            logger.warning(f"Configuration validation issues: {validation_results['issues']}")
        
        self._loaded_config = config
        logger.info(f"Loaded model configuration with {len(config)} variables")
        
        return config
    
    def get_model_for_agent(self, agent_type: str) -> Optional[str]:
        """
        Get model assignment for specific agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Model ID or None if not configured
        """
        config = self.load_configuration()
        env_var = f"CLAUDE_PM_MODEL_{agent_type.upper()}"
        
        # Check for global override first
        global_override = config.get("CLAUDE_PM_MODEL_OVERRIDE")
        if global_override:
            return global_override
        
        # Return agent-specific model
        return config.get(env_var)
    
    def set_environment_defaults(self, override_existing: bool = False) -> int:
        """
        Set environment variable defaults in the current process.
        
        Args:
            override_existing: Whether to override existing environment variables
            
        Returns:
            Number of variables set
        """
        defaults = self.load_configuration(apply_defaults=True)
        set_count = 0
        
        for env_var, default_value in defaults.items():
            if override_existing or env_var not in os.environ:
                os.environ[env_var] = str(default_value)
                set_count += 1
                logger.debug(f"Set environment default: {env_var}={default_value}")
        
        logger.info(f"Set {set_count} environment variable defaults")
        return set_count
    
    def generate_env_file(self, file_path: Path, include_comments: bool = True) -> None:
        """
        Generate .env file with model configuration defaults.
        
        Args:
            file_path: Path to write .env file
            include_comments: Whether to include explanatory comments
        """
        config = self.load_configuration(apply_defaults=True)
        
        lines = []
        
        if include_comments:
            lines.extend([
                "# Claude PM Framework - Model Configuration Environment Variables",
                f"# Generated for {self.deployment_env.value} environment",
                f"# Generated on: {os.popen('date').read().strip()}",
                "",
                "# Global Configuration",
            ])
        
        # Global configuration
        global_vars = [
            "CLAUDE_PM_MODEL_OVERRIDE",
            "CLAUDE_PM_DEPLOYMENT_ENV",
            "CLAUDE_PM_MODEL_CACHE_ENABLED",
            "CLAUDE_PM_MODEL_CACHE_TTL",
            "CLAUDE_PM_MODEL_VALIDATION_ENABLED",
            "CLAUDE_PM_MODEL_FALLBACK_ENABLED",
            "CLAUDE_PM_MODEL_DEBUG_LOGGING"
        ]
        
        for env_var in global_vars:
            if env_var in config:
                value = config[env_var]
                if include_comments and env_var == "CLAUDE_PM_MODEL_OVERRIDE":
                    lines.append("# Global model override (uncomment to use)")
                    lines.append(f"# {env_var}={value}")
                else:
                    lines.append(f"{env_var}={value}")
        
        if include_comments:
            lines.extend([
                "",
                "# Agent-Specific Model Assignments",
                "# Opus models (high capability, complex tasks):"
            ])
        
        # Group agent models by type
        opus_agents = []
        sonnet_agents = []
        other_agents = []
        
        for env_var, value in config.items():
            if env_var.startswith("CLAUDE_PM_MODEL_") and env_var not in global_vars:
                if "claude-3-opus" in value:
                    opus_agents.append((env_var, value))
                elif "claude-3-5-sonnet" in value:
                    sonnet_agents.append((env_var, value))
                else:
                    other_agents.append((env_var, value))
        
        # Add Opus agents
        for env_var, value in sorted(opus_agents):
            lines.append(f"{env_var}={value}")
        
        if include_comments:
            lines.extend([
                "",
                "# Sonnet models (balanced performance, recommended default):"
            ])
        
        # Add Sonnet agents
        for env_var, value in sorted(sonnet_agents):
            lines.append(f"{env_var}={value}")
        
        # Add other agents if any
        if other_agents:
            if include_comments:
                lines.extend([
                    "",
                    "# Other model assignments:"
                ])
            for env_var, value in sorted(other_agents):
                lines.append(f"{env_var}={value}")
        
        if include_comments:
            lines.extend([
                "",
                "# Available Models:",
                "# - claude-4-opus (highest capability, slower, higher cost)",
                "# - claude-sonnet-4-20250514 (balanced performance, recommended)",
                "# - claude-sonnet-4-20250514 (enhanced capabilities, medium cost)",
                "# - claude-3-haiku-20240307 (fastest, lowest cost, basic capabilities)",
                "",
                "# Usage Examples:",
                "# export CLAUDE_PM_MODEL_OVERRIDE=claude-sonnet-4-20250514",
                "# export CLAUDE_PM_MODEL_ENGINEER=claude-4-opus"
            ])
        
        # Write file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Generated environment file: {file_path}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive configuration summary.
        
        Returns:
            Summary of current configuration
        """
        config = self.load_configuration()
        
        # Count models
        model_counts = {}
        agent_assignments = {}
        
        for env_var, value in config.items():
            if env_var.startswith("CLAUDE_PM_MODEL_") and env_var != "CLAUDE_PM_MODEL_OVERRIDE":
                agent_type = env_var.replace("CLAUDE_PM_MODEL_", "").lower()
                agent_assignments[agent_type] = value
                model_counts[value] = model_counts.get(value, 0) + 1
        
        # Environment override info
        override_info = {
            "global_override": config.get("CLAUDE_PM_MODEL_OVERRIDE"),
            "deployment_env": config.get("CLAUDE_PM_DEPLOYMENT_ENV"),
            "cache_enabled": config.get("CLAUDE_PM_MODEL_CACHE_ENABLED") == "true",
            "validation_enabled": config.get("CLAUDE_PM_MODEL_VALIDATION_ENABLED") == "true",
            "fallback_enabled": config.get("CLAUDE_PM_MODEL_FALLBACK_ENABLED") == "true",
            "debug_logging": config.get("CLAUDE_PM_MODEL_DEBUG_LOGGING") == "true"
        }
        
        return {
            "deployment_environment": self.deployment_env.value,
            "total_variables": len(config),
            "agent_assignments": agent_assignments,
            "model_distribution": model_counts,
            "environment_settings": override_info,
            "configuration_status": {
                "loaded": self._loaded_config is not None,
                "defaults_applied": True,
                "validation_passed": self._validate_configuration(config)["valid"]
            }
        }
    
    def _detect_deployment_environment(self) -> DeploymentEnvironment:
        """Detect deployment environment from various indicators."""
        # Check explicit environment variable
        env_var = os.getenv("CLAUDE_PM_DEPLOYMENT_ENV", "").lower()
        if env_var:
            try:
                return DeploymentEnvironment(env_var)
            except ValueError:
                pass
        
        # Check common deployment indicators
        if os.getenv("PRODUCTION"):
            return DeploymentEnvironment.PRODUCTION
        elif os.getenv("STAGING"):
            return DeploymentEnvironment.STAGING
        elif os.getenv("CI") or os.getenv("CONTINUOUS_INTEGRATION"):
            return DeploymentEnvironment.TESTING
        else:
            return DeploymentEnvironment.DEVELOPMENT
    
    def _apply_deployment_overrides(self, config: Dict[str, str]) -> Dict[str, str]:
        """Apply deployment-specific configuration overrides."""
        if self.deployment_env == DeploymentEnvironment.PRODUCTION:
            # Production optimizations
            config["CLAUDE_PM_MODEL_CACHE_ENABLED"] = "true"
            config["CLAUDE_PM_MODEL_CACHE_TTL"] = "600"  # 10 minutes
            config["CLAUDE_PM_MODEL_DEBUG_LOGGING"] = "false"
            config["CLAUDE_PM_MODEL_VALIDATION_ENABLED"] = "true"
            config["CLAUDE_PM_MODEL_FALLBACK_ENABLED"] = "true"
            
        elif self.deployment_env == DeploymentEnvironment.DEVELOPMENT:
            # Development settings
            config["CLAUDE_PM_MODEL_DEBUG_LOGGING"] = "true"
            config["CLAUDE_PM_MODEL_CACHE_TTL"] = "60"  # 1 minute for faster iteration
            
        elif self.deployment_env == DeploymentEnvironment.TESTING:
            # Testing optimizations
            config["CLAUDE_PM_MODEL_CACHE_ENABLED"] = "false"  # Consistent test results
            config["CLAUDE_PM_MODEL_DEBUG_LOGGING"] = "true"
            config["CLAUDE_PM_MODEL_VALIDATION_ENABLED"] = "true"
        
        return config
    
    def _validate_configuration(self, config: Dict[str, str]) -> Dict[str, Any]:
        """Validate configuration values."""
        validation = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Validate model IDs
        valid_models = [
            "claude-4-opus",
            "claude-sonnet-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-3-haiku-20240307"
        ]
        
        for env_var, value in config.items():
            if env_var.startswith("CLAUDE_PM_MODEL_") and value:
                if value not in valid_models:
                    validation["valid"] = False
                    validation["issues"].append(f"Invalid model ID in {env_var}: {value}")
        
        # Validate boolean settings
        boolean_vars = [
            "CLAUDE_PM_MODEL_CACHE_ENABLED",
            "CLAUDE_PM_MODEL_VALIDATION_ENABLED",
            "CLAUDE_PM_MODEL_FALLBACK_ENABLED",
            "CLAUDE_PM_MODEL_DEBUG_LOGGING"
        ]
        
        for env_var in boolean_vars:
            value = config.get(env_var, "").lower()
            if value not in ["true", "false", ""]:
                validation["warnings"].append(f"Invalid boolean value in {env_var}: {value}")
        
        # Validate numeric settings
        cache_ttl = config.get("CLAUDE_PM_MODEL_CACHE_TTL", "")
        if cache_ttl and not cache_ttl.isdigit():
            validation["warnings"].append(f"Invalid numeric value in CLAUDE_PM_MODEL_CACHE_TTL: {cache_ttl}")
        
        return validation


# Helper functions for easy integration
def load_model_environment_defaults() -> Dict[str, str]:
    """Load model environment defaults for current deployment environment."""
    loader = ModelEnvironmentLoader()
    return loader.load_configuration()


def get_model_for_agent_from_env(agent_type: str) -> Optional[str]:
    """Get model assignment for agent type from environment configuration."""
    loader = ModelEnvironmentLoader()
    return loader.get_model_for_agent(agent_type)


def initialize_model_environment_defaults() -> int:
    """Initialize environment with model defaults. Returns count of variables set."""
    loader = ModelEnvironmentLoader()
    return loader.set_environment_defaults()


def generate_model_env_file(file_path: Path) -> None:
    """Generate .env file with model configuration defaults."""
    loader = ModelEnvironmentLoader()
    loader.generate_env_file(file_path)


if __name__ == "__main__":
    # Test the model environment loader
    print("Model Environment Configuration Test")
    print("=" * 50)
    
    loader = ModelEnvironmentLoader()
    
    # Load configuration
    config = loader.load_configuration()
    print(f"Loaded {len(config)} configuration variables")
    
    # Show summary
    summary = loader.get_configuration_summary()
    print(f"\nDeployment Environment: {summary['deployment_environment']}")
    print(f"Agent Assignments: {len(summary['agent_assignments'])}")
    print(f"Model Distribution: {summary['model_distribution']}")
    print(f"Environment Settings: {summary['environment_settings']}")
    
    # Test specific agent
    engineer_model = loader.get_model_for_agent("engineer")
    print(f"\nEngineer Agent Model: {engineer_model}")
    
    documentation_model = loader.get_model_for_agent("documentation")
    print(f"Documentation Agent Model: {documentation_model}")
    
    # Validate configuration
    validation = loader._validate_configuration(config)
    print(f"\nConfiguration Valid: {validation['valid']}")
    if validation['issues']:
        print(f"Issues: {validation['issues']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")