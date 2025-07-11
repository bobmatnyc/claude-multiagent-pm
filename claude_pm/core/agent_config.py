#!/usr/bin/env python3
"""
Agent Configuration System with Inheritance for Claude PM Framework
=================================================================

This module provides a comprehensive configuration system for agents with
hierarchical inheritance across the three-tier agent system.

Key Features:
- Configuration inheritance: Project -> User -> System
- Dynamic configuration merging and override mechanisms
- Template-based configuration generation
- Configuration validation and schema enforcement
- Hot-reload support for configuration changes
- Environment-specific configuration profiles
"""

import os
import yaml
import json
import copy
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Type, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime

from .config import Config
from .logging_config import setup_logging


@dataclass
class ConfigurationSource:
    """Represents a configuration source in the hierarchy."""

    name: str
    tier: str  # system, user, project
    path: Path
    priority: int  # 1=system, 2=user, 3=project
    config_data: Dict[str, Any] = field(default_factory=dict)
    last_modified: Optional[datetime] = None
    valid: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class AgentConfigurationProfile:
    """Represents a complete agent configuration profile."""

    agent_type: str
    agent_name: str
    tier: str
    merged_config: Dict[str, Any] = field(default_factory=dict)
    sources: List[ConfigurationSource] = field(default_factory=list)
    inheritance_chain: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class ConfigurationValidator(ABC):
    """Abstract base class for configuration validators."""

    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration and return (is_valid, errors)."""
        pass


class BasicAgentConfigValidator(ConfigurationValidator):
    """Basic validator for agent configurations."""

    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate basic agent configuration structure."""
        errors = []

        # Check required fields
        required_fields = ["name", "type", "enabled"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Validate agent type
        valid_types = [
            "engineer",
            "ops",
            "qa",
            "security",
            "architect",
            "orchestrator",
            "pm",
            "data",
            "ui",
            "integration",
            "performance",
            "research",
            "documentation",
            "scaffolding",
        ]

        agent_type = config.get("type")
        if agent_type and agent_type not in valid_types:
            errors.append(f"Invalid agent type: {agent_type}. Valid types: {valid_types}")

        # Validate boolean fields
        boolean_fields = ["enabled", "auto_load", "health_monitoring"]
        for field in boolean_fields:
            if field in config and not isinstance(config[field], bool):
                errors.append(f"Field '{field}' must be boolean")

        # Validate numeric fields
        numeric_fields = ["priority", "timeout", "retry_count"]
        for field in numeric_fields:
            if field in config and not isinstance(config[field], (int, float)):
                errors.append(f"Field '{field}' must be numeric")

        return len(errors) == 0, errors


class AgentConfigurationManager:
    """
    Manages agent configurations with hierarchical inheritance.

    This class handles:
    - Loading configurations from all tiers
    - Merging configurations with proper precedence
    - Validating configuration data
    - Hot-reloading configuration changes
    - Template-based configuration generation
    """

    def __init__(
        self,
        framework_path: Path,
        user_home: Path,
        project_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.framework_path = framework_path
        self.user_home = user_home
        self.project_path = project_path
        self.config = Config(config or {})
        self.logger = setup_logging("agent_config_manager")

        # Configuration paths
        self.system_config_path = framework_path / "config" / "agents"
        self.user_config_path = user_home / ".claude-pm" / "agents" / "user-defined" / "config"
        self.project_config_path = (
            project_path / ".claude-pm" / "agents" / "project-specific" / "config"
        )

        # Configuration sources cache
        self.config_sources: Dict[str, List[ConfigurationSource]] = {
            "system": [],
            "user": [],
            "project": [],
        }

        # Merged configurations cache
        self.agent_profiles: Dict[str, AgentConfigurationProfile] = {}

        # Validators
        self.validators: Dict[str, ConfigurationValidator] = {"basic": BasicAgentConfigValidator()}

        # File watchers for hot-reload
        self.file_watchers = []

        self.logger.info("Initialized AgentConfigurationManager")

    async def initialize(self) -> None:
        """Initialize the configuration manager."""
        try:
            # Ensure configuration directories exist
            self._ensure_config_directories()

            # Load all configuration sources
            await self._load_all_configuration_sources()

            # Generate merged configurations for all agent types
            await self._generate_all_agent_profiles()

            # Set up file monitoring for hot-reload
            if self.config.get("hot_reload_enabled", True):
                await self._setup_file_monitoring()

            self.logger.info("AgentConfigurationManager initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize AgentConfigurationManager: {e}")
            raise

    def _ensure_config_directories(self) -> None:
        """Ensure all configuration directories exist."""
        directories = [self.system_config_path, self.user_config_path, self.project_config_path]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

            # Create default config files if they don't exist
            default_config_file = directory / "default.yaml"
            if not default_config_file.exists():
                self._create_default_config_file(
                    default_config_file, self._get_tier_from_path(directory)
                )

    def _get_tier_from_path(self, path: Path) -> str:
        """Determine tier from configuration path."""
        path_str = str(path)

        if "claude_pm" in path_str or str(self.framework_path) in path_str:
            return "system"
        elif "user-defined" in path_str:
            return "user"
        elif "project-specific" in path_str:
            return "project"

        return "unknown"

    def _create_default_config_file(self, file_path: Path, tier: str) -> None:
        """Create a default configuration file for a tier."""
        default_configs = {
            "system": {
                "default_system_config": {
                    "name": "default_system_agent",
                    "type": "generic",
                    "enabled": True,
                    "tier": "system",
                    "priority": 1,
                    "auto_load": False,
                    "health_monitoring": True,
                    "timeout": 30,
                    "retry_count": 3,
                    "logging": {"level": "INFO", "enabled": True},
                    "permissions": {
                        "read_only": False,
                        "system_access": True,
                        "network_access": True,
                    },
                }
            },
            "user": {
                "default_user_config": {
                    "name": "default_user_agent",
                    "type": "generic",
                    "enabled": True,
                    "tier": "user",
                    "priority": 2,
                    "auto_load": False,
                    "health_monitoring": True,
                    "timeout": 30,
                    "retry_count": 3,
                    "logging": {"level": "INFO", "enabled": True},
                    "permissions": {
                        "read_only": False,
                        "system_access": False,
                        "network_access": True,
                    },
                    "customization": {
                        "user_preferences": {},
                        "custom_commands": [],
                        "override_system": True,
                    },
                }
            },
            "project": {
                "default_project_config": {
                    "name": "default_project_agent",
                    "type": "generic",
                    "enabled": True,
                    "tier": "project",
                    "priority": 3,
                    "auto_load": False,
                    "health_monitoring": True,
                    "timeout": 30,
                    "retry_count": 3,
                    "logging": {"level": "INFO", "enabled": True},
                    "permissions": {
                        "read_only": False,
                        "system_access": False,
                        "network_access": True,
                    },
                    "project_specific": {
                        "project_path": str(self.project_path),
                        "custom_settings": {},
                        "override_user": True,
                        "override_system": True,
                    },
                }
            },
        }

        config_data = default_configs.get(tier, {})

        try:
            with open(file_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

            self.logger.info(f"Created default {tier} configuration: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to create default config file {file_path}: {e}")

    async def _load_all_configuration_sources(self) -> None:
        """Load configuration sources from all tiers."""
        # Load system configurations
        await self._load_tier_configurations("system", self.system_config_path, 1)

        # Load user configurations
        await self._load_tier_configurations("user", self.user_config_path, 2)

        # Load project configurations
        await self._load_tier_configurations("project", self.project_config_path, 3)

        total_sources = sum(len(sources) for sources in self.config_sources.values())
        self.logger.info(f"Loaded {total_sources} configuration sources")

    async def _load_tier_configurations(self, tier: str, config_path: Path, priority: int) -> None:
        """Load configurations for a specific tier."""
        if not config_path.exists():
            return

        sources = []

        # Load YAML configuration files
        for config_file in config_path.glob("*.yaml"):
            try:
                source = await self._load_configuration_source(config_file, tier, priority)
                if source:
                    sources.append(source)
            except Exception as e:
                self.logger.error(f"Failed to load config {config_file}: {e}")

        # Load JSON configuration files
        for config_file in config_path.glob("*.json"):
            try:
                source = await self._load_configuration_source(config_file, tier, priority)
                if source:
                    sources.append(source)
            except Exception as e:
                self.logger.error(f"Failed to load config {config_file}: {e}")

        self.config_sources[tier] = sources
        self.logger.debug(f"Loaded {len(sources)} {tier} configuration sources")

    async def _load_configuration_source(
        self, file_path: Path, tier: str, priority: int
    ) -> Optional[ConfigurationSource]:
        """Load a single configuration source."""
        try:
            # Load configuration data
            if file_path.suffix == ".yaml":
                with open(file_path, "r") as f:
                    config_data = yaml.safe_load(f) or {}
            elif file_path.suffix == ".json":
                with open(file_path, "r") as f:
                    config_data = json.load(f)
            else:
                return None

            # Get file modification time
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

            # Create configuration source
            source = ConfigurationSource(
                name=file_path.stem,
                tier=tier,
                path=file_path,
                priority=priority,
                config_data=config_data,
                last_modified=last_modified,
                valid=True,
                errors=[],
            )

            # Validate configuration
            is_valid, errors = self._validate_configuration_source(source)
            source.valid = is_valid
            source.errors = errors

            return source

        except Exception as e:
            self.logger.error(f"Failed to load configuration source {file_path}: {e}")
            return ConfigurationSource(
                name=file_path.stem,
                tier=tier,
                path=file_path,
                priority=priority,
                valid=False,
                errors=[str(e)],
            )

    def _validate_configuration_source(self, source: ConfigurationSource) -> Tuple[bool, List[str]]:
        """Validate a configuration source."""
        all_errors = []
        all_valid = True

        # Validate each configuration in the source
        for config_name, config_data in source.config_data.items():
            if isinstance(config_data, dict):
                for validator_name, validator in self.validators.items():
                    is_valid, errors = validator.validate(config_data)
                    if not is_valid:
                        all_valid = False
                        all_errors.extend([f"{config_name}: {error}" for error in errors])

        return all_valid, all_errors

    async def _generate_all_agent_profiles(self) -> None:
        """Generate merged configuration profiles for all agent types."""
        # Collect all agent types from all tiers
        agent_types = set()

        for tier_sources in self.config_sources.values():
            for source in tier_sources:
                for config_name, config_data in source.config_data.items():
                    if isinstance(config_data, dict) and "type" in config_data:
                        agent_types.add(config_data["type"])

        # Generate profiles for each agent type
        for agent_type in agent_types:
            profile = await self._generate_agent_profile(agent_type)
            if profile:
                self.agent_profiles[agent_type] = profile

        self.logger.info(f"Generated {len(self.agent_profiles)} agent configuration profiles")

    async def _generate_agent_profile(self, agent_type: str) -> Optional[AgentConfigurationProfile]:
        """Generate a merged configuration profile for a specific agent type."""
        try:
            # Collect configurations for this agent type from all tiers
            relevant_sources = []

            for tier in ["system", "user", "project"]:
                for source in self.config_sources[tier]:
                    for config_name, config_data in source.config_data.items():
                        if isinstance(config_data, dict) and config_data.get("type") == agent_type:
                            relevant_sources.append((source, config_name, config_data))

            if not relevant_sources:
                return None

            # Sort by priority (system=1, user=2, project=3)
            relevant_sources.sort(key=lambda x: x[0].priority)

            # Merge configurations with inheritance
            merged_config = {}
            inheritance_chain = []
            sources_used = []

            for source, config_name, config_data in relevant_sources:
                # Deep merge configuration
                merged_config = self._deep_merge_config(merged_config, config_data)
                inheritance_chain.append(f"{source.tier}:{config_name}")
                sources_used.append(source)

            # Determine the primary tier (highest priority)
            primary_tier = relevant_sources[-1][0].tier if relevant_sources else "system"

            # Create agent profile
            profile = AgentConfigurationProfile(
                agent_type=agent_type,
                agent_name=merged_config.get("name", f"{agent_type}_agent"),
                tier=primary_tier,
                merged_config=merged_config,
                sources=sources_used,
                inheritance_chain=inheritance_chain,
                last_updated=datetime.now(),
            )

            # Validate merged configuration
            is_valid, errors = self._validate_merged_configuration(merged_config)
            profile.validation_errors = errors

            return profile

        except Exception as e:
            self.logger.error(f"Failed to generate agent profile for {agent_type}: {e}")
            return None

    def _deep_merge_config(
        self, base_config: Dict[str, Any], override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries."""
        result = copy.deepcopy(base_config)

        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge_config(result[key], value)
            else:
                # Override the value
                result[key] = copy.deepcopy(value)

        return result

    def _validate_merged_configuration(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a merged configuration."""
        all_errors = []
        all_valid = True

        for validator_name, validator in self.validators.items():
            is_valid, errors = validator.validate(config)
            if not is_valid:
                all_valid = False
                all_errors.extend(errors)

        return all_valid, all_errors

    async def _setup_file_monitoring(self) -> None:
        """Set up file monitoring for hot-reload of configurations."""
        # TODO: Implement file monitoring for configuration changes
        self.logger.info("Configuration file monitoring setup (placeholder)")

    def get_agent_configuration(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get the merged configuration for a specific agent type."""
        profile = self.agent_profiles.get(agent_type)
        return profile.merged_config if profile else None

    def get_agent_profile(self, agent_type: str) -> Optional[AgentConfigurationProfile]:
        """Get the complete configuration profile for a specific agent type."""
        return self.agent_profiles.get(agent_type)

    def get_all_agent_types(self) -> List[str]:
        """Get all available agent types."""
        return list(self.agent_profiles.keys())

    def get_configuration_inheritance_chain(self, agent_type: str) -> List[str]:
        """Get the configuration inheritance chain for an agent type."""
        profile = self.agent_profiles.get(agent_type)
        return profile.inheritance_chain if profile else []

    async def reload_configurations(self) -> None:
        """Reload all configurations from disk."""
        self.logger.info("Reloading all configurations...")

        # Clear existing data
        self.config_sources = {"system": [], "user": [], "project": []}
        self.agent_profiles = {}

        # Reload everything
        await self._load_all_configuration_sources()
        await self._generate_all_agent_profiles()

        self.logger.info("Configuration reload completed")

    async def create_agent_configuration(
        self, agent_type: str, agent_name: str, tier: str = "project", template: str = "default"
    ) -> bool:
        """Create a new agent configuration from template."""
        try:
            # Determine target directory
            if tier == "system":
                target_dir = self.system_config_path
            elif tier == "user":
                target_dir = self.user_config_path
            elif tier == "project":
                target_dir = self.project_config_path
            else:
                raise ValueError(f"Invalid tier: {tier}")

            # Generate configuration from template
            config_data = self._generate_config_from_template(
                agent_type, agent_name, tier, template
            )

            # Save configuration file
            config_file = target_dir / f"{agent_name}.yaml"
            if config_file.exists():
                raise FileExistsError(f"Configuration already exists: {config_file}")

            with open(config_file, "w") as f:
                yaml.dump({agent_name: config_data}, f, default_flow_style=False, indent=2)

            # Reload configurations to include the new one
            await self.reload_configurations()

            self.logger.info(f"Created {tier} configuration for {agent_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create agent configuration: {e}")
            return False

    def _generate_config_from_template(
        self, agent_type: str, agent_name: str, tier: str, template: str
    ) -> Dict[str, Any]:
        """Generate configuration from template."""
        base_config = {
            "name": agent_name,
            "type": agent_type,
            "enabled": True,
            "tier": tier,
            "priority": {"system": 1, "user": 2, "project": 3}.get(tier, 2),
            "auto_load": False,
            "health_monitoring": True,
            "timeout": 30,
            "retry_count": 3,
            "created_at": datetime.now().isoformat(),
            "logging": {"level": "INFO", "enabled": True},
        }

        # Add tier-specific configurations
        if tier == "system":
            base_config["permissions"] = {
                "read_only": False,
                "system_access": True,
                "network_access": True,
            }
        elif tier == "user":
            base_config["permissions"] = {
                "read_only": False,
                "system_access": False,
                "network_access": True,
            }
            base_config["customization"] = {
                "user_preferences": {},
                "custom_commands": [],
                "override_system": True,
            }
        elif tier == "project":
            base_config["permissions"] = {
                "read_only": False,
                "system_access": False,
                "network_access": True,
            }
            base_config["project_specific"] = {
                "project_path": str(self.project_path),
                "custom_settings": {},
                "override_user": True,
                "override_system": True,
            }

        return base_config

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get overall configuration system status."""
        total_sources = sum(len(sources) for sources in self.config_sources.values())
        valid_sources = sum(
            len([s for s in sources if s.valid]) for sources in self.config_sources.values()
        )

        return {
            "total_sources": total_sources,
            "valid_sources": valid_sources,
            "invalid_sources": total_sources - valid_sources,
            "agent_profiles": len(self.agent_profiles),
            "tiers": {
                tier: {"sources": len(sources), "valid": len([s for s in sources if s.valid])}
                for tier, sources in self.config_sources.items()
            },
            "last_reload": datetime.now().isoformat(),
        }
