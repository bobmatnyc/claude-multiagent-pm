"""
Default Model Configuration for Claude PM Framework
==================================================

Provides default model assignments for different agent types based on research findings:
- Claude 4 Opus: Orchestrator, Engineer agents (complex implementation tasks)
- Claude 4 Sonnet: Documentation, QA, Research, Ops, Security, Data Engineer agents
- Legacy Claude 3 models available as fallback

Key Features:
- Production-ready Claude 4 default assignments
- Environment variable overrides
- Model capability validation
- Configuration inheritance
- Performance optimization defaults

Created: 2025-07-16
Updated: 2025-07-16 (Claude 4 migration)
"""

import os
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
from dataclasses import dataclass, field

from ..services.model_selector import ModelType, ModelSelector, ModelSelectionCriteria

logger = logging.getLogger(__name__)


@dataclass
class DefaultModelConfig:
    """Default model configuration for the framework"""
    orchestrator_model: str = ModelType.OPUS_4.value
    engineer_model: str = ModelType.OPUS_4.value
    documentation_model: str = ModelType.SONNET_4.value
    qa_model: str = ModelType.SONNET_4.value
    research_model: str = ModelType.SONNET_4.value
    ops_model: str = ModelType.SONNET_4.value
    security_model: str = ModelType.SONNET_4.value
    data_engineer_model: str = ModelType.SONNET_4.value
    ticketing_model: str = ModelType.SONNET_4.value
    version_control_model: str = ModelType.SONNET_4.value
    
    # Advanced agent types
    architecture_model: str = ModelType.OPUS_4.value
    performance_model: str = ModelType.OPUS_4.value
    integration_model: str = ModelType.OPUS_4.value
    backend_model: str = ModelType.OPUS_4.value
    machine_learning_model: str = ModelType.OPUS_4.value
    data_science_model: str = ModelType.OPUS_4.value
    
    # Standard agent types
    ui_ux_model: str = ModelType.SONNET_4.value
    frontend_model: str = ModelType.SONNET_4.value
    database_model: str = ModelType.SONNET_4.value
    api_model: str = ModelType.SONNET_4.value
    testing_model: str = ModelType.SONNET_4.value
    monitoring_model: str = ModelType.SONNET_4.value
    analytics_model: str = ModelType.SONNET_4.value
    deployment_model: str = ModelType.SONNET_4.value
    workflow_model: str = ModelType.SONNET_4.value
    devops_model: str = ModelType.SONNET_4.value
    cloud_model: str = ModelType.SONNET_4.value
    infrastructure_model: str = ModelType.SONNET_4.value
    business_analysis_model: str = ModelType.SONNET_4.value
    project_management_model: str = ModelType.SONNET_4.value
    compliance_model: str = ModelType.SONNET_4.value
    content_model: str = ModelType.SONNET_4.value
    customer_support_model: str = ModelType.SONNET_4.value
    marketing_model: str = ModelType.SONNET_4.value
    scaffolding_model: str = ModelType.SONNET_4.value
    code_review_model: str = ModelType.SONNET_4.value
    memory_management_model: str = ModelType.SONNET_4.value
    knowledge_base_model: str = ModelType.SONNET_4.value
    validation_model: str = ModelType.SONNET_4.value
    automation_model: str = ModelType.SONNET_4.value
    
    # Fallback model
    fallback_model: str = ModelType.SONNET_4.value
    
    # Environment variable overrides
    enable_env_overrides: bool = True
    
    # Performance settings
    enable_model_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # Validation settings
    validate_model_availability: bool = True
    fallback_on_error: bool = True


class DefaultModelConfigManager:
    """
    Manager for default model configuration with environment overrides
    and validation capabilities.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize default model configuration manager."""
        self.config_path = config_path
        self.config = DefaultModelConfig()
        self.model_selector = ModelSelector()
        self._load_environment_overrides()
        
        logger.info("DefaultModelConfigManager initialized with production defaults")
    
    def get_default_model_for_agent(self, agent_type: str) -> str:
        """
        Get default model for an agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Model ID string
        """
        # Apply environment overrides if enabled
        if self.config.enable_env_overrides:
            env_override = self._get_environment_override(agent_type)
            if env_override:
                logger.debug(f"Using environment override for {agent_type}: {env_override}")
                return env_override
        
        # Get default mapping
        model_attr = f"{agent_type}_model"
        if hasattr(self.config, model_attr):
            default_model = getattr(self.config, model_attr)
            logger.debug(f"Default model for {agent_type}: {default_model}")
            return default_model
        
        # Fallback to default
        logger.info(f"No specific default for {agent_type}, using fallback: {self.config.fallback_model}")
        return self.config.fallback_model
    
    def get_all_default_mappings(self) -> Dict[str, str]:
        """
        Get all default agent type to model mappings.
        
        Returns:
            Dictionary mapping agent types to model IDs
        """
        mappings = {}
        
        # Extract all agent type mappings from config
        for attr_name in dir(self.config):
            if attr_name.endswith('_model') and not attr_name.startswith('_'):
                agent_type = attr_name[:-6]  # Remove '_model' suffix
                model_id = getattr(self.config, attr_name)
                
                # Apply environment overrides
                if self.config.enable_env_overrides:
                    env_override = self._get_environment_override(agent_type)
                    if env_override:
                        model_id = env_override
                
                mappings[agent_type] = model_id
        
        return mappings
    
    def validate_default_configuration(self) -> Dict[str, Any]:
        """
        Validate the default model configuration.
        
        Returns:
            Validation results with any issues found
        """
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "model_distribution": {},
            "recommendations": []
        }
        
        mappings = self.get_all_default_mappings()
        
        # Count model distribution
        model_counts = {}
        for agent_type, model_id in mappings.items():
            model_counts[model_id] = model_counts.get(model_id, 0) + 1
        
        validation_results["model_distribution"] = model_counts
        
        # Validate each model assignment
        for agent_type, model_id in mappings.items():
            try:
                # Validate model exists
                model_type = ModelType(model_id)
                
                # Use ModelSelector for validation
                validation = self.model_selector.validate_model_selection(agent_type, model_id)
                
                if not validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["issues"].append({
                        "agent_type": agent_type,
                        "model_id": model_id,
                        "error": validation.get("error", "Invalid model selection")
                    })
                
                # Check for warnings
                if validation.get("warnings"):
                    validation_results["warnings"].extend([
                        {
                            "agent_type": agent_type,
                            "model_id": model_id,
                            "warning": warning
                        }
                        for warning in validation["warnings"]
                    ])
                
                # Check for suggestions
                if validation.get("suggestions"):
                    validation_results["recommendations"].extend([
                        {
                            "agent_type": agent_type,
                            "model_id": model_id,
                            "suggestion": suggestion
                        }
                        for suggestion in validation["suggestions"]
                    ])
                
            except ValueError as e:
                validation_results["valid"] = False
                validation_results["issues"].append({
                    "agent_type": agent_type,
                    "model_id": model_id,
                    "error": f"Invalid model ID: {e}"
                })
        
        # Generate overall recommendations
        opus_count = model_counts.get(ModelType.OPUS.value, 0)
        sonnet_count = model_counts.get(ModelType.SONNET.value, 0)
        
        if opus_count == 0:
            validation_results["recommendations"].append({
                "type": "performance",
                "message": "No agents assigned to Opus model - consider using Opus for complex tasks"
            })
        
        if sonnet_count == 0:
            validation_results["recommendations"].append({
                "type": "efficiency",
                "message": "No agents assigned to Sonnet model - consider using Sonnet for balanced tasks"
            })
        
        # Cost analysis
        if opus_count > sonnet_count * 2:
            validation_results["warnings"].append({
                "type": "cost",
                "message": "High ratio of Opus assignments may increase costs significantly"
            })
        
        return validation_results
    
    def generate_environment_template(self) -> str:
        """
        Generate environment variable template for model overrides.
        
        Returns:
            Environment variable template string
        """
        template_lines = [
            "# Claude PM Framework - Model Configuration Environment Variables",
            "# Override default model assignments by setting these variables",
            "",
            "# Global model override (affects all agents)",
            "# CLAUDE_PM_MODEL_OVERRIDE=claude-3-5-sonnet-20241022",
            "",
            "# Agent-specific model overrides",
        ]
        
        mappings = self.get_all_default_mappings()
        for agent_type, default_model in sorted(mappings.items()):
            env_var = f"CLAUDE_PM_MODEL_{agent_type.upper()}"
            template_lines.append(f"# {env_var}={default_model}")
        
        template_lines.extend([
            "",
            "# Available models:",
            f"# - {ModelType.OPUS_4.value} (Claude 4 highest capability, recommended for complex tasks)",
            f"# - {ModelType.SONNET_4.value} (Claude 4 balanced performance, recommended default)",
            f"# - {ModelType.OPUS.value} (legacy Claude 3 highest capability, slower, higher cost)",
            f"# - {ModelType.SONNET.value} (legacy Claude 3 balanced performance)",
            f"# - {ModelType.HAIKU.value} (fastest, lowest cost, basic capabilities)",
            "",
            "# Example usage:",
            "# export CLAUDE_PM_MODEL_ENGINEER=claude-4-opus",
            "# export CLAUDE_PM_MODEL_DOCUMENTATION=claude-sonnet-4-20250514"
        ])
        
        return "\n".join(template_lines)
    
    def _load_environment_overrides(self) -> None:
        """Load any environment variable overrides into the configuration."""
        if not self.config.enable_env_overrides:
            return
        
        # Global override
        global_override = os.getenv('CLAUDE_PM_MODEL_OVERRIDE')
        if global_override:
            try:
                ModelType(global_override)  # Validate model exists
                logger.info(f"Global model override detected: {global_override}")
                # Note: Global override is handled in _get_environment_override method
            except ValueError:
                logger.warning(f"Invalid global model override: {global_override}")
        
        # Agent-specific overrides
        override_count = 0
        for attr_name in dir(self.config):
            if attr_name.endswith('_model') and not attr_name.startswith('_'):
                agent_type = attr_name[:-6]  # Remove '_model' suffix
                env_var = f'CLAUDE_PM_MODEL_{agent_type.upper()}'
                env_value = os.getenv(env_var)
                
                if env_value:
                    try:
                        ModelType(env_value)  # Validate model exists
                        override_count += 1
                        logger.debug(f"Environment override for {agent_type}: {env_value}")
                    except ValueError:
                        logger.warning(f"Invalid model override in {env_var}: {env_value}")
        
        if override_count > 0:
            logger.info(f"Loaded {override_count} environment model overrides")
    
    def _get_environment_override(self, agent_type: str) -> Optional[str]:
        """Get environment variable override for an agent type."""
        # Check global override first
        global_override = os.getenv('CLAUDE_PM_MODEL_OVERRIDE')
        if global_override:
            try:
                ModelType(global_override)  # Validate
                return global_override
            except ValueError:
                pass
        
        # Check agent-specific override
        env_var = f'CLAUDE_PM_MODEL_{agent_type.upper()}'
        env_value = os.getenv(env_var)
        if env_value:
            try:
                ModelType(env_value)  # Validate
                return env_value
            except ValueError:
                pass
        
        return None
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive configuration summary.
        
        Returns:
            Configuration summary with mappings, overrides, and statistics
        """
        mappings = self.get_all_default_mappings()
        validation = self.validate_default_configuration()
        
        # Count environment overrides
        override_count = 0
        active_overrides = {}
        
        for agent_type in mappings.keys():
            override = self._get_environment_override(agent_type)
            if override:
                override_count += 1
                active_overrides[agent_type] = override
        
        return {
            "total_agent_types": len(mappings),
            "default_mappings": mappings,
            "model_distribution": validation["model_distribution"],
            "environment_overrides": {
                "count": override_count,
                "active_overrides": active_overrides,
                "global_override": os.getenv('CLAUDE_PM_MODEL_OVERRIDE')
            },
            "configuration_health": {
                "valid": validation["valid"],
                "issues_count": len(validation["issues"]),
                "warnings_count": len(validation["warnings"]),
                "recommendations_count": len(validation["recommendations"])
            },
            "settings": {
                "enable_env_overrides": self.config.enable_env_overrides,
                "enable_model_caching": self.config.enable_model_caching,
                "cache_ttl_seconds": self.config.cache_ttl_seconds,
                "validate_model_availability": self.config.validate_model_availability,
                "fallback_on_error": self.config.fallback_on_error,
                "fallback_model": self.config.fallback_model
            }
        }


# Helper functions for easy integration
def get_default_model_config() -> DefaultModelConfigManager:
    """Get default model configuration manager instance."""
    return DefaultModelConfigManager()


def get_default_model_for_agent_type(agent_type: str) -> str:
    """
    Quick helper to get default model for an agent type.
    
    Args:
        agent_type: Type of agent
        
    Returns:
        Model ID string
    """
    manager = get_default_model_config()
    return manager.get_default_model_for_agent(agent_type)


def validate_default_model_configuration() -> Dict[str, Any]:
    """
    Validate the default model configuration.
    
    Returns:
        Validation results
    """
    manager = get_default_model_config()
    return manager.validate_default_configuration()


def generate_model_env_template() -> str:
    """
    Generate environment variable template for model configuration.
    
    Returns:
        Environment variable template string
    """
    manager = get_default_model_config()
    return manager.generate_environment_template()


if __name__ == "__main__":
    # Test the default model configuration
    print("Default Model Configuration Test")
    print("=" * 50)
    
    manager = DefaultModelConfigManager()
    
    # Show all mappings
    mappings = manager.get_all_default_mappings()
    print(f"\nTotal agent types configured: {len(mappings)}")
    
    # Group by model
    by_model = {}
    for agent_type, model_id in mappings.items():
        if model_id not in by_model:
            by_model[model_id] = []
        by_model[model_id].append(agent_type)
    
    print(f"\nModel Distribution:")
    for model_id, agent_types in by_model.items():
        print(f"  {model_id}: {len(agent_types)} agents")
        for agent_type in sorted(agent_types):
            print(f"    - {agent_type}")
    
    # Validation
    print(f"\nValidation Results:")
    validation = manager.validate_default_configuration()
    print(f"  Valid: {validation['valid']}")
    print(f"  Issues: {len(validation['issues'])}")
    print(f"  Warnings: {len(validation['warnings'])}")
    print(f"  Recommendations: {len(validation['recommendations'])}")
    
    # Configuration summary
    print(f"\nConfiguration Summary:")
    summary = manager.get_configuration_summary()
    print(f"  Environment overrides: {summary['environment_overrides']['count']}")
    print(f"  Configuration health: {summary['configuration_health']}")
    
    # Environment template
    print(f"\nEnvironment Template (first 10 lines):")
    template = manager.generate_environment_template()
    for line in template.split('\n')[:10]:
        print(f"  {line}")