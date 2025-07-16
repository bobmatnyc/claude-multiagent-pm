"""
Integrated Model Configuration for Claude PM Framework
=====================================================

Main configuration module that integrates default model assignments,
environment variables, system agent configurations, and validation.

This module provides the primary interface for model configuration
across the entire framework.

Key Features:
- Unified configuration interface
- Environment variable integration
- System agent model assignments
- Configuration validation and health checks
- Framework initialization integration
- Performance optimization settings

Created: 2025-07-16
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

from .default_model_config import DefaultModelConfigManager
from .model_env_defaults import ModelEnvironmentLoader, DeploymentEnvironment
from ..agents.system_agent_config import SystemAgentConfigManager
from ..services.model_selector import ModelSelector

logger = logging.getLogger(__name__)


@dataclass
class ModelConfigurationStatus:
    """Status of model configuration system"""
    initialized: bool = False
    validation_passed: bool = False
    environment_overrides_active: int = 0
    total_agents_configured: int = 0
    model_distribution: Dict[str, int] = None
    configuration_issues: List[str] = None
    last_updated: Optional[str] = None
    
    def __post_init__(self):
        if self.model_distribution is None:
            self.model_distribution = {}
        if self.configuration_issues is None:
            self.configuration_issues = []


class IntegratedModelConfiguration:
    """
    Integrated model configuration manager that coordinates all model configuration
    components and provides a unified interface for the framework.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize integrated model configuration."""
        self.config_path = config_path
        self._status = ModelConfigurationStatus()
        
        # Initialize component managers
        self.default_config_manager = DefaultModelConfigManager(config_path)
        self.env_loader = ModelEnvironmentLoader()
        self.system_agent_manager = SystemAgentConfigManager()
        self.model_selector = ModelSelector()
        
        # Initialize configuration
        self._initialize_configuration()
        
        logger.info("IntegratedModelConfiguration initialized successfully")
    
    def _initialize_configuration(self) -> None:
        """Initialize the complete model configuration system."""
        try:
            # Load environment configuration
            env_config = self.env_loader.load_configuration()
            
            # Validate all configurations
            validation_results = self._validate_all_configurations()
            
            # Update status
            self._status.initialized = True
            self._status.validation_passed = validation_results["overall_valid"]
            self._status.environment_overrides_active = len(
                validation_results["environment_analysis"]["active_overrides"]
            )
            self._status.total_agents_configured = validation_results["agent_analysis"]["total_agents"]
            self._status.model_distribution = validation_results["model_distribution"]
            self._status.configuration_issues = validation_results["all_issues"]
            self._status.last_updated = validation_results.get("timestamp")
            
            logger.info(f"Model configuration initialized with {self._status.total_agents_configured} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize model configuration: {e}")
            self._status.initialized = False
            self._status.configuration_issues = [str(e)]
    
    def get_model_for_agent(self, agent_type: str) -> str:
        """
        Get the effective model for an agent type, considering all configuration sources.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Model ID string
        """
        # Priority order: Environment variables > System agent config > Default config
        
        # 1. Check environment variables (highest priority)
        env_model = self.env_loader.get_model_for_agent(agent_type)
        if env_model:
            logger.debug(f"Using environment model for {agent_type}: {env_model}")
            return env_model
        
        # 2. Check system agent configuration
        agent_config = self.system_agent_manager.get_agent_config(agent_type)
        if agent_config:
            model = agent_config.get_effective_model()
            logger.debug(f"Using system agent model for {agent_type}: {model}")
            return model
        
        # 3. Fall back to default configuration
        default_model = self.default_config_manager.get_default_model_for_agent(agent_type)
        logger.debug(f"Using default model for {agent_type}: {default_model}")
        return default_model
    
    def get_model_with_validation(self, agent_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Get model for agent with comprehensive validation.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Tuple of (model_id, validation_results)
        """
        model_id = self.get_model_for_agent(agent_type)
        validation = self.model_selector.validate_model_selection(agent_type, model_id)
        
        return model_id, validation
    
    def get_all_agent_models(self) -> Dict[str, str]:
        """
        Get effective models for all configured agents.
        
        Returns:
            Dictionary mapping agent types to model IDs
        """
        agent_models = {}
        
        # Get all agent types from various sources
        agent_types = set()
        
        # From system agent manager
        agent_types.update(self.system_agent_manager.get_all_agents().keys())
        
        # From default config manager
        agent_types.update(self.default_config_manager.get_all_default_mappings().keys())
        
        # Get effective model for each agent type
        for agent_type in agent_types:
            agent_models[agent_type] = self.get_model_for_agent(agent_type)
        
        return agent_models
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Comprehensive configuration validation.
        
        Returns:
            Complete validation results
        """
        return self._validate_all_configurations()
    
    def _validate_all_configurations(self) -> Dict[str, Any]:
        """Validate all configuration components."""
        validation_results = {
            "overall_valid": True,
            "timestamp": os.popen('date').read().strip(),
            "all_issues": [],
            "component_validations": {},
            "environment_analysis": {},
            "agent_analysis": {},
            "model_distribution": {},
            "recommendations": []
        }
        
        try:
            # 1. Validate default configuration
            default_validation = self.default_config_manager.validate_default_configuration()
            validation_results["component_validations"]["default_config"] = default_validation
            
            if not default_validation["valid"]:
                validation_results["overall_valid"] = False
                validation_results["all_issues"].extend([
                    f"Default config: {issue['error']}" for issue in default_validation["issues"]
                ])
            
            # 2. Validate environment configuration
            env_config = self.env_loader.load_configuration()
            env_validation = self.env_loader._validate_configuration(env_config)
            validation_results["component_validations"]["environment"] = env_validation
            
            if not env_validation["valid"]:
                validation_results["overall_valid"] = False
                validation_results["all_issues"].extend([
                    f"Environment: {issue}" for issue in env_validation["issues"]
                ])
            
            # 3. Validate system agent configurations
            agent_validation = self.system_agent_manager.validate_agent_model_assignments()
            validation_results["component_validations"]["system_agents"] = agent_validation
            
            if not agent_validation["valid"]:
                validation_results["overall_valid"] = False
                validation_results["all_issues"].extend([
                    f"Agent {issue['agent_type']}: {issue['error']}" for issue in agent_validation["issues"]
                ])
            
            # 4. Environment analysis
            env_summary = self.env_loader.get_configuration_summary()
            validation_results["environment_analysis"] = {
                "deployment_environment": env_summary["deployment_environment"],
                "total_variables": env_summary["total_variables"],
                "active_overrides": env_summary["environment_settings"],
                "configuration_health": env_summary["configuration_status"]
            }
            
            # 5. Agent analysis
            agent_summary = self.system_agent_manager.get_configuration_summary()
            validation_results["agent_analysis"] = {
                "total_agents": agent_summary["total_agents"],
                "enabled_agents": agent_summary["enabled_agents"],
                "environment_overrides": agent_summary["environment_overrides"],
                "capabilities_coverage": agent_summary["capabilities_coverage"]
            }
            
            # 6. Model distribution analysis
            all_models = self.get_all_agent_models()
            model_distribution = {}
            for model_id in all_models.values():
                model_distribution[model_id] = model_distribution.get(model_id, 0) + 1
            
            validation_results["model_distribution"] = model_distribution
            
            # 7. Generate recommendations
            validation_results["recommendations"] = self._generate_configuration_recommendations(
                validation_results
            )
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            validation_results["overall_valid"] = False
            validation_results["all_issues"].append(f"Validation error: {str(e)}")
        
        return validation_results
    
    def _generate_configuration_recommendations(self, validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate configuration recommendations based on validation results."""
        recommendations = []
        
        # Model distribution recommendations
        model_dist = validation_results.get("model_distribution", {})
        opus_4_count = model_dist.get("claude-4-opus", 0)
        sonnet_4_count = model_dist.get("claude-sonnet-4-20250514", 0)
        # Legacy models
        opus_count = model_dist.get("claude-3-opus-20240229", 0)
        sonnet_count = model_dist.get("claude-3-5-sonnet-20241022", 0)
        
        if opus_4_count == 0 and opus_count == 0:
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "message": "No agents using Opus model - consider assigning to complex tasks",
                "action": "Review agent assignments for orchestrator and engineer roles"
            })
        
        if sonnet_4_count == 0 and sonnet_count == 0:
            recommendations.append({
                "type": "efficiency",
                "priority": "low",
                "message": "No agents using Sonnet model - consider for balanced performance tasks",
                "action": "Review agent assignments for documentation and QA roles"
            })
        
        # Cost optimization
        total_agents = sum(model_dist.values())
        if total_agents > 0:
            opus_total = opus_4_count + opus_count
            opus_ratio = opus_total / total_agents
            if opus_ratio > 0.5:
                recommendations.append({
                    "type": "cost",
                    "priority": "high",
                    "message": f"High Opus usage ({opus_ratio:.1%}) may increase costs significantly",
                    "action": "Consider using Sonnet 4 for non-critical tasks"
                })
        
        # Environment recommendations
        env_analysis = validation_results.get("environment_analysis", {})
        if env_analysis.get("deployment_environment") == "development":
            recommendations.append({
                "type": "configuration",
                "priority": "low",
                "message": "Development environment detected - consider enabling debug logging",
                "action": "Set CLAUDE_PM_MODEL_DEBUG_LOGGING=true for development"
            })
        
        # Validation issues
        if not validation_results.get("overall_valid", True):
            recommendations.append({
                "type": "critical",
                "priority": "high",
                "message": "Configuration validation failed - immediate attention required",
                "action": "Review and fix configuration issues before deployment"
            })
        
        return recommendations
    
    def get_configuration_status(self) -> ModelConfigurationStatus:
        """Get current configuration status."""
        return self._status
    
    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive configuration summary.
        
        Returns:
            Complete summary of all configuration aspects
        """
        validation = self.validate_configuration()
        
        return {
            "status": {
                "initialized": self._status.initialized,
                "validation_passed": self._status.validation_passed,
                "last_updated": self._status.last_updated
            },
            "agent_models": self.get_all_agent_models(),
            "model_distribution": validation["model_distribution"],
            "environment_analysis": validation["environment_analysis"],
            "agent_analysis": validation["agent_analysis"],
            "validation_summary": {
                "overall_valid": validation["overall_valid"],
                "total_issues": len(validation["all_issues"]),
                "issues": validation["all_issues"][:5],  # First 5 issues
                "recommendations_count": len(validation["recommendations"])
            },
            "recommendations": validation["recommendations"],
            "component_health": {
                "default_config": validation["component_validations"]["default_config"]["valid"],
                "environment": validation["component_validations"]["environment"]["valid"],
                "system_agents": validation["component_validations"]["system_agents"]["valid"]
            }
        }
    
    def initialize_framework_defaults(self, override_existing: bool = False) -> Dict[str, Any]:
        """
        Initialize framework with model configuration defaults.
        
        Args:
            override_existing: Whether to override existing environment variables
            
        Returns:
            Initialization results
        """
        results = {
            "success": False,
            "env_vars_set": 0,
            "agents_configured": 0,
            "validation_passed": False,
            "issues": []
        }
        
        try:
            # Set environment defaults
            results["env_vars_set"] = self.env_loader.set_environment_defaults(override_existing)
            
            # Count configured agents
            results["agents_configured"] = len(self.get_all_agent_models())
            
            # Validate configuration
            validation = self.validate_configuration()
            results["validation_passed"] = validation["overall_valid"]
            results["issues"] = validation["all_issues"]
            
            # Update status
            self._status.initialized = True
            self._status.validation_passed = validation["overall_valid"]
            
            results["success"] = True
            logger.info(f"Framework defaults initialized: {results['env_vars_set']} env vars, {results['agents_configured']} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize framework defaults: {e}")
            results["issues"].append(str(e))
        
        return results
    
    def generate_configuration_files(self, output_dir: Path) -> Dict[str, Path]:
        """
        Generate configuration files for deployment.
        
        Args:
            output_dir: Directory to write configuration files
            
        Returns:
            Dictionary mapping file types to paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = {}
        
        try:
            # Generate .env file
            env_file = output_dir / ".env"
            self.env_loader.generate_env_file(env_file)
            generated_files["env_file"] = env_file
            
            # Generate environment template
            template_file = output_dir / "model_config_template.env"
            template_content = self.default_config_manager.generate_environment_template()
            with open(template_file, 'w') as f:
                f.write(template_content)
            generated_files["template_file"] = template_file
            
            # Generate configuration summary
            summary_file = output_dir / "model_config_summary.json"
            import json
            summary = self.get_comprehensive_summary()
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            generated_files["summary_file"] = summary_file
            
            logger.info(f"Generated {len(generated_files)} configuration files in {output_dir}")
            
        except Exception as e:
            logger.error(f"Failed to generate configuration files: {e}")
            raise
        
        return generated_files


# Module-level instance for easy access
_integrated_config: Optional[IntegratedModelConfiguration] = None


def get_integrated_model_config() -> IntegratedModelConfiguration:
    """Get the integrated model configuration instance."""
    global _integrated_config
    if _integrated_config is None:
        _integrated_config = IntegratedModelConfiguration()
    return _integrated_config


def get_model_for_agent(agent_type: str) -> str:
    """Get effective model for an agent type."""
    config = get_integrated_model_config()
    return config.get_model_for_agent(agent_type)


def validate_model_configuration() -> Dict[str, Any]:
    """Validate the complete model configuration."""
    config = get_integrated_model_config()
    return config.validate_configuration()


def initialize_model_configuration_defaults() -> Dict[str, Any]:
    """Initialize model configuration defaults for the framework."""
    config = get_integrated_model_config()
    return config.initialize_framework_defaults()


if __name__ == "__main__":
    # Test the integrated model configuration
    print("Integrated Model Configuration Test")
    print("=" * 60)
    
    config = IntegratedModelConfiguration()
    
    # Show configuration status
    status = config.get_configuration_status()
    print(f"Configuration Status:")
    print(f"  Initialized: {status.initialized}")
    print(f"  Validation Passed: {status.validation_passed}")
    print(f"  Environment Overrides: {status.environment_overrides_active}")
    print(f"  Total Agents: {status.total_agents_configured}")
    print(f"  Issues: {len(status.configuration_issues)}")
    
    # Show comprehensive summary
    summary = config.get_comprehensive_summary()
    print(f"\nModel Distribution:")
    for model_id, count in summary["model_distribution"].items():
        print(f"  {model_id}: {count} agents")
    
    print(f"\nValidation Summary:")
    print(f"  Overall Valid: {summary['validation_summary']['overall_valid']}")
    print(f"  Total Issues: {summary['validation_summary']['total_issues']}")
    print(f"  Recommendations: {summary['validation_summary']['recommendations_count']}")
    
    print(f"\nComponent Health:")
    for component, health in summary["component_health"].items():
        print(f"  {component}: {'✓' if health else '✗'}")
    
    # Test specific agent models
    print(f"\nAgent Model Assignments:")
    test_agents = ["orchestrator", "engineer", "documentation", "qa", "research"]
    for agent_type in test_agents:
        model_id = config.get_model_for_agent(agent_type)
        print(f"  {agent_type}: {model_id}")
    
    # Show recommendations
    if summary["recommendations"]:
        print(f"\nTop Recommendations:")
        for i, rec in enumerate(summary["recommendations"][:3], 1):
            print(f"  {i}. [{rec['priority'].upper()}] {rec['message']}")
            print(f"     Action: {rec['action']}")