"""
Framework Initialization with Model Configuration
================================================

Integrates model configuration initialization into the framework startup process.
Ensures model defaults are properly loaded and validated during framework initialization.

Key Features:
- Framework startup integration
- Model configuration validation during init
- Environment variable setup
- Configuration health checks
- Initialization status tracking
- Error handling and recovery

Created: 2025-07-16
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from .model_configuration import IntegratedModelConfiguration, get_integrated_model_config
from .model_env_defaults import DeploymentEnvironment
from ..core.container import ServiceContainer, get_container

logger = logging.getLogger(__name__)


@dataclass
class FrameworkInitializationStatus:
    """Status of framework initialization with model configuration"""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success: bool = False
    model_config_initialized: bool = False
    model_config_validated: bool = False
    environment_variables_set: int = 0
    agents_configured: int = 0
    issues_found: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get initialization duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None
    
    @property
    def is_healthy(self) -> bool:
        """Check if initialization is healthy."""
        return (
            self.success and
            self.model_config_initialized and
            self.model_config_validated and
            len(self.issues_found) == 0
        )


class FrameworkModelConfigInitializer:
    """
    Initializes model configuration as part of framework startup.
    """
    
    def __init__(self, container: Optional[ServiceContainer] = None):
        """Initialize framework model config initializer."""
        self.container = container or get_container()
        self.status = FrameworkInitializationStatus()
        self._model_config: Optional[IntegratedModelConfiguration] = None
        
        logger.info("FrameworkModelConfigInitializer created")
    
    async def initialize(self, 
                        validate_config: bool = True,
                        set_env_defaults: bool = True,
                        override_existing_env: bool = False) -> FrameworkInitializationStatus:
        """
        Initialize model configuration for the framework.
        
        Args:
            validate_config: Whether to validate configuration
            set_env_defaults: Whether to set environment variable defaults
            override_existing_env: Whether to override existing environment variables
            
        Returns:
            Initialization status
        """
        self.status.started_at = datetime.now()
        
        try:
            logger.info("Starting framework model configuration initialization")
            
            # Step 1: Initialize model configuration
            await self._initialize_model_configuration()
            
            # Step 2: Set environment defaults if requested
            if set_env_defaults:
                await self._set_environment_defaults(override_existing_env)
            
            # Step 3: Validate configuration if requested
            if validate_config:
                await self._validate_configuration()
            
            # Step 4: Register with service container
            await self._register_with_container()
            
            # Step 5: Run health checks
            await self._run_health_checks()
            
            self.status.success = True
            logger.info(f"Framework model configuration initialized successfully in {self.status.duration_ms:.1f}ms")
            
        except Exception as e:
            logger.error(f"Framework model configuration initialization failed: {e}")
            self.status.issues_found.append(f"Initialization failed: {str(e)}")
            self.status.success = False
        
        finally:
            self.status.completed_at = datetime.now()
        
        return self.status
    
    async def _initialize_model_configuration(self) -> None:
        """Initialize the integrated model configuration."""
        start_time = datetime.now()
        
        try:
            self._model_config = get_integrated_model_config()
            self.status.model_config_initialized = True
            
            # Count configured agents
            agent_models = self._model_config.get_all_agent_models()
            self.status.agents_configured = len(agent_models)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            self.status.performance_metrics["model_config_init_ms"] = duration
            
            logger.info(f"Model configuration initialized with {self.status.agents_configured} agents in {duration:.1f}ms")
            
        except Exception as e:
            logger.error(f"Failed to initialize model configuration: {e}")
            self.status.issues_found.append(f"Model config initialization: {str(e)}")
            raise
    
    async def _set_environment_defaults(self, override_existing: bool) -> None:
        """Set environment variable defaults."""
        start_time = datetime.now()
        
        try:
            if not self._model_config:
                raise RuntimeError("Model configuration not initialized")
            
            init_results = self._model_config.initialize_framework_defaults(override_existing)
            self.status.environment_variables_set = init_results["env_vars_set"]
            
            if init_results["issues"]:
                self.status.warnings.extend(init_results["issues"])
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            self.status.performance_metrics["env_defaults_ms"] = duration
            
            logger.info(f"Set {self.status.environment_variables_set} environment defaults in {duration:.1f}ms")
            
        except Exception as e:
            logger.error(f"Failed to set environment defaults: {e}")
            self.status.issues_found.append(f"Environment defaults: {str(e)}")
            raise
    
    async def _validate_configuration(self) -> None:
        """Validate the complete model configuration."""
        start_time = datetime.now()
        
        try:
            if not self._model_config:
                raise RuntimeError("Model configuration not initialized")
            
            validation_results = self._model_config.validate_configuration()
            self.status.model_config_validated = validation_results["overall_valid"]
            
            if not validation_results["overall_valid"]:
                self.status.issues_found.extend(validation_results["all_issues"])
            
            # Add warnings from validation
            for component_name, component_validation in validation_results["component_validations"].items():
                if component_validation.get("warnings"):
                    for warning in component_validation["warnings"]:
                        if isinstance(warning, dict):
                            self.status.warnings.append(f"{component_name}: {warning.get('warning', warning)}")
                        else:
                            self.status.warnings.append(f"{component_name}: {warning}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            self.status.performance_metrics["validation_ms"] = duration
            
            logger.info(f"Configuration validation completed in {duration:.1f}ms - Valid: {self.status.model_config_validated}")
            
        except Exception as e:
            logger.error(f"Failed to validate configuration: {e}")
            self.status.issues_found.append(f"Configuration validation: {str(e)}")
            raise
    
    async def _register_with_container(self) -> None:
        """Register model configuration with the service container."""
        start_time = datetime.now()
        
        try:
            if not self._model_config:
                raise RuntimeError("Model configuration not initialized")
            
            # Register the integrated model configuration
            self.container.register_instance(IntegratedModelConfiguration, self._model_config)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            self.status.performance_metrics["container_registration_ms"] = duration
            
            logger.debug(f"Model configuration registered with service container in {duration:.1f}ms")
            
        except Exception as e:
            logger.error(f"Failed to register with service container: {e}")
            self.status.warnings.append(f"Container registration: {str(e)}")
            # Don't raise - this is not critical for basic functionality
    
    async def _run_health_checks(self) -> None:
        """Run health checks on the initialized configuration."""
        start_time = datetime.now()
        
        try:
            if not self._model_config:
                raise RuntimeError("Model configuration not initialized")
            
            # Check configuration status
            config_status = self._model_config.get_configuration_status()
            
            if not config_status.initialized:
                self.status.issues_found.append("Model configuration not properly initialized")
            
            if not config_status.validation_passed:
                self.status.issues_found.append("Model configuration validation failed")
            
            if config_status.configuration_issues:
                self.status.issues_found.extend(config_status.configuration_issues)
            
            # Test basic functionality
            try:
                test_model = self._model_config.get_model_for_agent("orchestrator")
                if not test_model:
                    self.status.warnings.append("Could not resolve model for orchestrator agent")
            except Exception as e:
                self.status.warnings.append(f"Model resolution test failed: {e}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            self.status.performance_metrics["health_checks_ms"] = duration
            
            logger.debug(f"Health checks completed in {duration:.1f}ms")
            
        except Exception as e:
            logger.error(f"Health checks failed: {e}")
            self.status.warnings.append(f"Health checks: {str(e)}")
    
    def get_status(self) -> FrameworkInitializationStatus:
        """Get current initialization status."""
        return self.status
    
    def get_model_config(self) -> Optional[IntegratedModelConfiguration]:
        """Get the initialized model configuration."""
        return self._model_config
    
    def get_summary(self) -> Dict[str, Any]:
        """Get initialization summary."""
        return {
            "initialization": {
                "success": self.status.success,
                "healthy": self.status.is_healthy,
                "duration_ms": self.status.duration_ms,
                "started_at": self.status.started_at.isoformat() if self.status.started_at else None,
                "completed_at": self.status.completed_at.isoformat() if self.status.completed_at else None
            },
            "model_configuration": {
                "initialized": self.status.model_config_initialized,
                "validated": self.status.model_config_validated,
                "agents_configured": self.status.agents_configured,
                "env_vars_set": self.status.environment_variables_set
            },
            "issues": {
                "total_issues": len(self.status.issues_found),
                "issues": self.status.issues_found,
                "total_warnings": len(self.status.warnings),
                "warnings": self.status.warnings
            },
            "performance": self.status.performance_metrics
        }


class FrameworkHealthChecker:
    """
    Health checker for framework model configuration.
    """
    
    def __init__(self, model_config: Optional[IntegratedModelConfiguration] = None):
        """Initialize framework health checker."""
        self.model_config = model_config or get_integrated_model_config()
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on framework model configuration.
        
        Returns:
            Health check results
        """
        health_results = {
            "overall_healthy": True,
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Check 1: Model configuration status
            config_status = self.model_config.get_configuration_status()
            health_results["checks"]["config_status"] = {
                "healthy": config_status.initialized and config_status.validation_passed,
                "details": {
                    "initialized": config_status.initialized,
                    "validation_passed": config_status.validation_passed,
                    "agents_configured": config_status.total_agents_configured,
                    "env_overrides": config_status.environment_overrides_active
                }
            }
            
            if not health_results["checks"]["config_status"]["healthy"]:
                health_results["overall_healthy"] = False
                health_results["issues"].append("Model configuration not properly initialized or validated")
            
            # Check 2: Core agent model assignments
            core_agents = ["orchestrator", "engineer", "documentation", "qa", "research", "ops", "security", "data_engineer"]
            missing_agents = []
            
            for agent_type in core_agents:
                try:
                    model_id = self.model_config.get_model_for_agent(agent_type)
                    if not model_id:
                        missing_agents.append(agent_type)
                except Exception as e:
                    missing_agents.append(f"{agent_type} (error: {e})")
            
            health_results["checks"]["core_agents"] = {
                "healthy": len(missing_agents) == 0,
                "details": {
                    "total_core_agents": len(core_agents),
                    "missing_agents": missing_agents
                }
            }
            
            if missing_agents:
                health_results["overall_healthy"] = False
                health_results["issues"].append(f"Missing model assignments for core agents: {missing_agents}")
            
            # Check 3: Model distribution
            all_models = self.model_config.get_all_agent_models()
            model_distribution = {}
            for model_id in all_models.values():
                model_distribution[model_id] = model_distribution.get(model_id, 0) + 1
            
            health_results["checks"]["model_distribution"] = {
                "healthy": len(model_distribution) > 0,
                "details": model_distribution
            }
            
            if len(model_distribution) == 0:
                health_results["overall_healthy"] = False
                health_results["issues"].append("No model assignments found")
            
            # Check 4: Environment configuration
            try:
                validation = self.model_config.validate_configuration()
                env_health = validation["environment_analysis"]
                
                health_results["checks"]["environment"] = {
                    "healthy": env_health["configuration_health"]["validation_passed"],
                    "details": env_health
                }
                
                if not env_health["configuration_health"]["validation_passed"]:
                    health_results["warnings"].append("Environment configuration has validation issues")
                
            except Exception as e:
                health_results["checks"]["environment"] = {
                    "healthy": False,
                    "error": str(e)
                }
                health_results["warnings"].append(f"Environment check failed: {e}")
            
            # Generate recommendations
            if not health_results["overall_healthy"]:
                health_results["recommendations"].append({
                    "priority": "high",
                    "message": "Model configuration has critical issues requiring immediate attention",
                    "action": "Review initialization logs and fix configuration issues"
                })
            
            if len(health_results["warnings"]) > 0:
                health_results["recommendations"].append({
                    "priority": "medium",
                    "message": "Model configuration has warnings that should be addressed",
                    "action": "Review warnings and optimize configuration"
                })
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_results["overall_healthy"] = False
            health_results["issues"].append(f"Health check error: {str(e)}")
        
        return health_results


# Helper functions for framework integration
async def initialize_framework_model_configuration(
    container: Optional[ServiceContainer] = None,
    validate_config: bool = True,
    set_env_defaults: bool = True,
    override_existing_env: bool = False
) -> FrameworkInitializationStatus:
    """
    Initialize model configuration for the framework.
    
    Args:
        container: Service container to use
        validate_config: Whether to validate configuration
        set_env_defaults: Whether to set environment defaults
        override_existing_env: Whether to override existing environment variables
        
    Returns:
        Initialization status
    """
    initializer = FrameworkModelConfigInitializer(container)
    return await initializer.initialize(validate_config, set_env_defaults, override_existing_env)


async def check_framework_model_health() -> Dict[str, Any]:
    """
    Check health of framework model configuration.
    
    Returns:
        Health check results
    """
    checker = FrameworkHealthChecker()
    return await checker.check_health()


def validate_framework_model_configuration() -> Dict[str, Any]:
    """
    Validate framework model configuration synchronously.
    
    Returns:
        Validation results
    """
    config = get_integrated_model_config()
    return config.validate_configuration()


if __name__ == "__main__":
    # Test framework initialization
    async def test_initialization():
        print("Framework Model Configuration Initialization Test")
        print("=" * 60)
        
        initializer = FrameworkModelConfigInitializer()
        
        # Run initialization
        status = await initializer.initialize()
        
        # Show results
        print(f"\nInitialization Results:")
        print(f"  Success: {status.success}")
        print(f"  Healthy: {status.is_healthy}")
        print(f"  Duration: {status.duration_ms:.1f}ms")
        print(f"  Model Config Initialized: {status.model_config_initialized}")
        print(f"  Model Config Validated: {status.model_config_validated}")
        print(f"  Agents Configured: {status.agents_configured}")
        print(f"  Environment Variables Set: {status.environment_variables_set}")
        
        if status.issues_found:
            print(f"\nIssues Found:")
            for issue in status.issues_found:
                print(f"  - {issue}")
        
        if status.warnings:
            print(f"\nWarnings:")
            for warning in status.warnings:
                print(f"  - {warning}")
        
        # Performance metrics
        print(f"\nPerformance Metrics:")
        for metric, value in status.performance_metrics.items():
            print(f"  {metric}: {value:.1f}ms")
        
        # Health check
        checker = FrameworkHealthChecker(initializer.get_model_config())
        health = await checker.check_health()
        
        print(f"\nHealth Check:")
        print(f"  Overall Healthy: {health['overall_healthy']}")
        print(f"  Issues: {len(health['issues'])}")
        print(f"  Warnings: {len(health['warnings'])}")
        print(f"  Recommendations: {len(health['recommendations'])}")
    
    # Run the test
    asyncio.run(test_initialization())