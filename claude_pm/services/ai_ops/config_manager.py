"""
AI Ops Configuration Manager

Centralized configuration management for AI Operations with environment-aware
settings, provider configurations, and runtime parameter management.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigLevel(Enum):
    """Configuration level hierarchy."""

    SYSTEM = "system"
    USER = "user"
    PROJECT = "project"
    RUNTIME = "runtime"


@dataclass
class ProviderConfig:
    """Configuration for AI service providers."""

    provider_id: str
    api_key_env: str
    base_url: Optional[str] = None
    model_mapping: Optional[Dict[str, str]] = None
    rate_limits: Optional[Dict[str, int]] = None
    timeout: int = 30
    max_retries: int = 3
    enabled: bool = True


@dataclass
class CostConfig:
    """Cost management configuration."""

    daily_budget: float = 100.0
    monthly_budget: float = 2500.0
    cost_tracking_enabled: bool = True
    budget_alerts: bool = True
    cost_optimization: bool = True
    token_limit_per_request: int = 100000


@dataclass
class SecurityConfig:
    """Security framework configuration."""

    api_key_rotation_enabled: bool = True
    rotation_interval_days: int = 30
    audit_logging: bool = True
    secure_storage: bool = True
    encryption_enabled: bool = True
    compliance_mode: str = "standard"  # standard, soc2, iso27001, gdpr


@dataclass
class MonitoringConfig:
    """Monitoring and health check configuration."""

    health_check_interval: int = 60
    performance_monitoring: bool = True
    error_tracking: bool = True
    metrics_retention_days: int = 30
    alerting_enabled: bool = True


@dataclass
class AIOpConfig:
    """Complete AI Operations configuration."""

    providers: Dict[str, ProviderConfig]
    cost: CostConfig
    security: SecurityConfig
    monitoring: MonitoringConfig
    created_at: datetime
    updated_at: datetime
    tools_sandbox_enabled: bool = True
    circuit_breaker_enabled: bool = True


class ConfigManager:
    """
    Centralized configuration manager for AI Operations.

    Manages configuration hierarchy: Runtime > Project > User > System
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize configuration manager."""
        self.project_root = project_root or Path.cwd()
        self.config_cache: Dict[str, Any] = {}
        self.config_file_paths = self._get_config_paths()
        self._load_configurations()

    def _get_config_paths(self) -> Dict[ConfigLevel, Path]:
        """Get configuration file paths for each level."""
        home = Path.home()

        return {
            ConfigLevel.SYSTEM: Path(__file__).parent.parent.parent
            / "config"
            / "ai_ops_system.json",
            ConfigLevel.USER: home / ".claude-pm" / "ai_ops_config.json",
            ConfigLevel.PROJECT: self.project_root / ".claude-pm" / "ai_ops_config.json",
            ConfigLevel.RUNTIME: Path("/tmp") / "claude_pm_ai_ops_runtime.json",
        }

    def _load_configurations(self):
        """Load configurations from all levels."""
        self.config_cache.clear()

        # Load in hierarchy order (system -> user -> project -> runtime)
        for level in ConfigLevel:
            config_path = self.config_file_paths[level]
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config_data = json.load(f)
                        self.config_cache[level.value] = config_data
                        logger.debug(f"Loaded {level.value} config from {config_path}")
                except Exception as e:
                    logger.warning(f"Failed to load {level.value} config: {e}")
            else:
                logger.debug(f"No {level.value} config found at {config_path}")

    def get_merged_config(self) -> AIOpConfig:
        """Get merged configuration with proper hierarchy precedence."""
        # Start with default configuration
        merged = self._get_default_config()

        # Apply configurations in hierarchy order
        for level in ConfigLevel:
            if level.value in self.config_cache:
                self._merge_config(merged, self.config_cache[level.value])

        return self._dict_to_aiop_config(merged)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default AI Operations configuration."""
        return {
            "providers": {
                "openai": {
                    "provider_id": "openai",
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": None,
                    "model_mapping": {"gpt-4": "gpt-4-turbo-preview", "gpt-3.5": "gpt-3.5-turbo"},
                    "rate_limits": {"requests_per_minute": 60, "tokens_per_minute": 40000},
                    "timeout": 30,
                    "max_retries": 3,
                    "enabled": True,
                },
                "anthropic": {
                    "provider_id": "anthropic",
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "base_url": None,
                    "model_mapping": {
                        "claude-3": "claude-3-opus-20240229",
                        "claude-3-sonnet": "claude-3-sonnet-20240229",
                    },
                    "rate_limits": {"requests_per_minute": 60, "tokens_per_minute": 40000},
                    "timeout": 30,
                    "max_retries": 3,
                    "enabled": True,
                },
            },
            "cost": {
                "daily_budget": 100.0,
                "monthly_budget": 2500.0,
                "cost_tracking_enabled": True,
                "budget_alerts": True,
                "cost_optimization": True,
                "token_limit_per_request": 100000,
            },
            "security": {
                "api_key_rotation_enabled": True,
                "rotation_interval_days": 30,
                "audit_logging": True,
                "secure_storage": True,
                "encryption_enabled": True,
                "compliance_mode": "standard",
            },
            "monitoring": {
                "health_check_interval": 60,
                "performance_monitoring": True,
                "error_tracking": True,
                "metrics_retention_days": 30,
                "alerting_enabled": True,
            },
            "tools_sandbox_enabled": True,
            "circuit_breaker_enabled": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Merge configuration with override precedence."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _dict_to_aiop_config(self, config_dict: Dict[str, Any]) -> AIOpConfig:
        """Convert dictionary to AIOpConfig dataclass."""
        # Convert provider configs
        providers = {}
        for provider_id, provider_data in config_dict.get("providers", {}).items():
            providers[provider_id] = ProviderConfig(**provider_data)

        # Convert other configs
        cost_config = CostConfig(**config_dict.get("cost", {}))
        security_config = SecurityConfig(**config_dict.get("security", {}))
        monitoring_config = MonitoringConfig(**config_dict.get("monitoring", {}))

        # Parse datetime strings
        created_at = datetime.fromisoformat(
            config_dict.get("created_at", datetime.now().isoformat())
        )
        updated_at = datetime.fromisoformat(
            config_dict.get("updated_at", datetime.now().isoformat())
        )

        return AIOpConfig(
            providers=providers,
            cost=cost_config,
            security=security_config,
            monitoring=monitoring_config,
            tools_sandbox_enabled=config_dict.get("tools_sandbox_enabled", True),
            circuit_breaker_enabled=config_dict.get("circuit_breaker_enabled", True),
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_provider_config(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get configuration for specific provider."""
        config = self.get_merged_config()
        return config.providers.get(provider_id)

    def update_config(self, level: ConfigLevel, config_updates: Dict[str, Any]):
        """Update configuration at specific level."""
        config_path = self.config_file_paths[level]

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config or start with empty
        existing_config = {}
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    existing_config = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing config: {e}")

        # Merge updates
        self._merge_config(existing_config, config_updates)
        existing_config["updated_at"] = datetime.now().isoformat()

        # Save updated config
        try:
            with open(config_path, "w") as f:
                json.dump(existing_config, f, indent=2, default=str)
            logger.info(f"Updated {level.value} config at {config_path}")

            # Reload configurations
            self._load_configurations()

        except Exception as e:
            logger.error(f"Failed to save {level.value} config: {e}")
            raise

    def get_environment_variables(self) -> Dict[str, str]:
        """Get required environment variables for current configuration."""
        config = self.get_merged_config()
        env_vars = {}

        for provider_id, provider_config in config.providers.items():
            if provider_config.enabled and provider_config.api_key_env:
                env_value = os.getenv(provider_config.api_key_env)
                env_vars[provider_config.api_key_env] = env_value or "NOT_SET"

        return env_vars

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration and return validation results."""
        config = self.get_merged_config()
        validation_results = {"valid": True, "errors": [], "warnings": [], "missing_env_vars": []}

        # Validate providers
        enabled_providers = 0
        for provider_id, provider_config in config.providers.items():
            if provider_config.enabled:
                enabled_providers += 1

                # Check API key environment variable
                if not os.getenv(provider_config.api_key_env):
                    validation_results["missing_env_vars"].append(provider_config.api_key_env)
                    validation_results["warnings"].append(
                        f"Provider {provider_id} enabled but {provider_config.api_key_env} not set"
                    )

        if enabled_providers == 0:
            validation_results["valid"] = False
            validation_results["errors"].append("No AI providers are enabled")

        # Validate cost configuration
        if config.cost.daily_budget <= 0:
            validation_results["warnings"].append("Daily budget is not set or invalid")

        # Validate security configuration
        if not config.security.audit_logging:
            validation_results["warnings"].append("Audit logging is disabled")

        return validation_results

    def export_config(self, level: ConfigLevel) -> Dict[str, Any]:
        """Export configuration at specific level."""
        if level.value in self.config_cache:
            return self.config_cache[level.value].copy()
        return {}

    def reset_config(self, level: ConfigLevel):
        """Reset configuration at specific level to defaults."""
        config_path = self.config_file_paths[level]

        if config_path.exists():
            try:
                config_path.unlink()
                logger.info(f"Reset {level.value} config at {config_path}")
                self._load_configurations()
            except Exception as e:
                logger.error(f"Failed to reset {level.value} config: {e}")
                raise
