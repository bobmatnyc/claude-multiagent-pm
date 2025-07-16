#!/usr/bin/env python3
"""
CMPM Integration Service - CMPM-105: Enhanced Startup Integration
================================================================

This service provides comprehensive integration of all CMPM systems (101-104)
with unified error handling, troubleshooting, and seamless user experience.

Key Features:
- Unified initialization of all CMPM services
- Comprehensive error handling and recovery
- Service health monitoring and diagnostics
- Troubleshooting guide integration
- Seamless CLI command integration
- Deployment-aware service coordination

Dependencies:
- CMPM-101 (Deployment Detection System) - DeploymentDetector
- CMPM-102 (Versioned Template Management) - TemplateManager
- CMPM-103 (Dependency Management Strategy) - DependencyManager
- CMPM-104 (Parent Directory Template Installation) - ParentDirectoryManager
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.base_service import BaseService
from ..core.logging_config import setup_logging
from ..core.response_types import TaskToolResponse

# Import all CMPM services
# Template Manager removed - use Claude Code Task Tool instead
TEMPLATE_MANAGER_AVAILABLE = False

# Dependency Manager removed - use Claude Code Task Tool instead
DEPENDENCY_MANAGER_AVAILABLE = False

try:
    from .parent_directory_manager import ParentDirectoryManager, ParentDirectoryContext

    PARENT_DIRECTORY_MANAGER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Parent Directory Manager not available: {e}")
    PARENT_DIRECTORY_MANAGER_AVAILABLE = False


class CMPMServiceStatus(Enum):
    """Status of CMPM services."""

    INITIALIZING = "initializing"
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class IntegrationLevel(Enum):
    """Levels of CMPM integration."""

    BASIC = "basic"
    STANDARD = "standard"
    FULL = "full"
    ADVANCED = "advanced"


@dataclass
class CMPMServiceInfo:
    """Information about a CMPM service."""

    service_id: str
    name: str
    version: str
    status: CMPMServiceStatus
    available: bool
    initialized: bool = False
    error_message: Optional[str] = None
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CMPMIntegrationStatus:
    """Overall CMPM integration status."""

    integration_level: IntegrationLevel
    services: Dict[str, CMPMServiceInfo]
    deployment_config: Dict[str, Any]
    health_score: int
    total_services: int
    operational_services: int
    error_services: int
    timestamp: datetime
    troubleshooting_recommendations: List[str] = field(default_factory=list)


class CMPMIntegrationService(BaseService):
    """
    CMPM Integration Service for unified framework deployment.

    This service coordinates all CMPM systems and provides:
    - Unified service initialization and management
    - Comprehensive error handling and recovery
    - Health monitoring and diagnostics
    - Troubleshooting guidance
    - CLI command integration
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CMPM Integration Service.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(name="cmpm_integration_service", config=config)
        self.logger = setup_logging(__name__)

        # Service instances
        # template_manager removed - use Claude Code Task Tool instead
        self.template_manager: Optional[Any] = None
        # dependency_manager removed - use Claude Code Task Tool instead
        self.dependency_manager: Optional[Any] = None
        self.parent_directory_manager: Optional[ParentDirectoryManager] = None

        # Integration state
        self.services: Dict[str, CMPMServiceInfo] = {}
        self.deployment_config: Dict[str, Any] = {}
        self.integration_level: IntegrationLevel = IntegrationLevel.BASIC

        # Configuration
        self.auto_recovery_enabled = self.get_config("auto_recovery_enabled", True)
        self.health_check_interval = self.get_config("health_check_interval", 300)  # 5 minutes
        self.initialization_timeout = self.get_config("initialization_timeout", 60)  # 1 minute

        # Initialize service registry
        self._initialize_service_registry()

    async def _initialize(self) -> None:
        """Initialize the CMPM Integration Service."""
        self.logger.info("Initializing CMPM Integration Service...")

        try:
            # Load deployment configuration
            await self._load_deployment_configuration()

            # Initialize all available services
            await self._initialize_all_services()

            # Perform initial health check
            await self._perform_comprehensive_health_check()

            # Determine integration level
            self._determine_integration_level()

            # Setup monitoring if enabled
            if self.get_config("enable_health_monitoring", True):
                asyncio.create_task(self._health_monitoring_task())

            self.logger.info(
                f"CMPM Integration Service initialized at {self.integration_level.value} level"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize CMPM Integration Service: {e}")
            raise

    async def _cleanup(self) -> None:
        """Cleanup the CMPM Integration Service."""
        self.logger.info("Cleaning up CMPM Integration Service...")

        try:
            # Cleanup all services
            cleanup_tasks = []

            # template_manager removed - no cleanup needed

            # dependency_manager removed - no cleanup needed

            if self.parent_directory_manager:
                cleanup_tasks.append(self.parent_directory_manager._cleanup())

            # Wait for all cleanup tasks
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            self.logger.info("CMPM Integration Service cleanup completed")

        except Exception as e:
            self.logger.error(f"Failed to cleanup CMPM Integration Service: {e}")

    def _initialize_service_registry(self):
        """Initialize the service registry with available services."""
        self.services = {
            "deployment_detector": CMPMServiceInfo(
                service_id="deployment_detector",
                name="Deployment Detection System",
                version="1.0.0",
                status=CMPMServiceStatus.UNAVAILABLE,
                available=True,  # Always available as it's built into the CLI
            ),
            "template_manager": CMPMServiceInfo(
                service_id="template_manager",
                name="Versioned Template Management",
                version="1.0.0",
                status=CMPMServiceStatus.UNAVAILABLE,
                available=TEMPLATE_MANAGER_AVAILABLE,
            ),
            "dependency_manager": CMPMServiceInfo(
                service_id="dependency_manager",
                name="Dependency Management Strategy",
                version="1.0.0",
                status=CMPMServiceStatus.UNAVAILABLE,
                available=DEPENDENCY_MANAGER_AVAILABLE,
            ),
            "parent_directory_manager": CMPMServiceInfo(
                service_id="parent_directory_manager",
                name="Parent Directory Template Installation",
                version="1.0.0",
                status=CMPMServiceStatus.UNAVAILABLE,
                available=PARENT_DIRECTORY_MANAGER_AVAILABLE,
            ),
        }

    async def _load_deployment_configuration(self):
        """Load deployment configuration from environment or detection."""
        try:
            # Try to get deployment config from environment
            deployment_type = os.getenv("CLAUDE_PM_DEPLOYMENT_TYPE", "unknown")
            framework_path = os.getenv("CLAUDE_PM_FRAMEWORK_PATH", str(Path.cwd()))

            self.deployment_config = {
                "deployment_type": deployment_type,
                "framework_path": framework_path,
                "platform": sys.platform,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "working_directory": str(Path.cwd()),
                "timestamp": datetime.now().isoformat(),
            }

            self.logger.info(f"Loaded deployment configuration: {deployment_type}")

        except Exception as e:
            self.logger.error(f"Failed to load deployment configuration: {e}")
            # Use fallback configuration
            self.deployment_config = {
                "deployment_type": "fallback",
                "framework_path": str(Path.cwd()),
                "platform": sys.platform,
                "error": str(e),
            }

    async def _initialize_all_services(self):
        """Initialize all available CMPM services."""
        self.logger.info("Initializing all CMPM services...")

        initialization_tasks = []

        # Initialize Template Manager (CMPM-102) - REMOVED
        # template_manager removed - use Claude Code Task Tool instead

        # Initialize Dependency Manager (CMPM-103) - REMOVED
        # dependency_manager removed - use Claude Code Task Tool instead

        # Initialize Parent Directory Manager (CMPM-104)
        if PARENT_DIRECTORY_MANAGER_AVAILABLE:
            initialization_tasks.append(self._initialize_parent_directory_manager())

        # Execute initialization tasks with timeout
        if initialization_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*initialization_tasks, return_exceptions=True),
                    timeout=self.initialization_timeout,
                )
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Service initialization timed out after {self.initialization_timeout}s"
                )

        # Update deployment detector status (always operational)
        self.services["deployment_detector"].status = CMPMServiceStatus.OPERATIONAL
        self.services["deployment_detector"].initialized = True
        self.services["deployment_detector"].last_health_check = datetime.now()

    async def _initialize_template_manager(self):
        """Initialize the Template Manager service - SERVICE REMOVED."""
        self.logger.debug("Template Manager removed - use Claude Code Task Tool instead")
        return

    async def _initialize_dependency_manager(self):
        """Initialize the Dependency Manager service - SERVICE REMOVED."""
        self.logger.debug("Dependency Manager removed - use Claude Code Task Tool instead")
        return

    async def _initialize_parent_directory_manager(self):
        """Initialize the Parent Directory Manager service."""
        try:
            self.logger.debug("Initializing Parent Directory Manager...")
            self.services["parent_directory_manager"].status = CMPMServiceStatus.INITIALIZING

            self.parent_directory_manager = ParentDirectoryManager()
            await self.parent_directory_manager._initialize()

            self.services["parent_directory_manager"].status = CMPMServiceStatus.OPERATIONAL
            self.services["parent_directory_manager"].initialized = True
            self.services["parent_directory_manager"].last_health_check = datetime.now()

            # Get managed directory count for metadata
            directories = await self.parent_directory_manager.list_managed_directories()
            self.services["parent_directory_manager"].metadata = {
                "managed_directories": len(directories),
                "deployment_integration": True,
            }

            self.logger.info("Parent Directory Manager initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Parent Directory Manager: {e}")
            self.services["parent_directory_manager"].status = CMPMServiceStatus.ERROR
            self.services["parent_directory_manager"].error_message = str(e)

    def _determine_integration_level(self):
        """Determine the current integration level based on service availability."""
        operational_services = sum(
            1
            for service in self.services.values()
            if service.status == CMPMServiceStatus.OPERATIONAL
        )
        total_available = sum(1 for service in self.services.values() if service.available)

        if operational_services == total_available and operational_services == 4:
            self.integration_level = IntegrationLevel.ADVANCED
        elif operational_services >= 3:
            self.integration_level = IntegrationLevel.FULL
        elif operational_services >= 2:
            self.integration_level = IntegrationLevel.STANDARD
        else:
            self.integration_level = IntegrationLevel.BASIC

        self.logger.info(
            f"Integration level: {self.integration_level.value} ({operational_services}/{total_available} services)"
        )

    async def _perform_comprehensive_health_check(self):
        """Perform comprehensive health check on all services."""
        self.logger.debug("Performing comprehensive health check...")

        for service_id, service_info in self.services.items():
            if not service_info.available:
                continue

            try:
                if service_id == "deployment_detector":
                    # Deployment detector is always healthy if we get this far
                    service_info.status = CMPMServiceStatus.OPERATIONAL
                    service_info.last_health_check = datetime.now()

                elif service_id == "template_manager" and self.template_manager:
                    # Perform template manager health check
                    await self._health_check_template_manager()

                elif service_id == "dependency_manager" and self.dependency_manager:
                    # Perform dependency manager health check
                    await self._health_check_dependency_manager()

                elif service_id == "parent_directory_manager" and self.parent_directory_manager:
                    # Perform parent directory manager health check
                    await self._health_check_parent_directory_manager()

            except Exception as e:
                self.logger.error(f"Health check failed for {service_id}: {e}")
                service_info.status = CMPMServiceStatus.ERROR
                service_info.error_message = str(e)

    async def _health_check_template_manager(self):
        """Perform health check on Template Manager."""
        try:
            # Try to list templates
            templates = await self.template_manager.list_templates()

            self.services["template_manager"].status = CMPMServiceStatus.OPERATIONAL
            self.services["template_manager"].last_health_check = datetime.now()
            self.services["template_manager"].metadata["template_count"] = len(templates)

        except Exception as e:
            self.services["template_manager"].status = CMPMServiceStatus.DEGRADED
            self.services["template_manager"].error_message = str(e)

    async def _health_check_dependency_manager(self):
        """Perform health check on Dependency Manager."""
        try:
            # Check dependency tracking
            dependencies = self.dependency_manager.get_dependencies()
            report = await self.dependency_manager.generate_dependency_report()

            self.services["dependency_manager"].status = CMPMServiceStatus.OPERATIONAL
            self.services["dependency_manager"].last_health_check = datetime.now()
            self.services["dependency_manager"].metadata.update(
                {"dependencies_tracked": len(dependencies), "health_score": report.health_score}
            )

        except Exception as e:
            self.services["dependency_manager"].status = CMPMServiceStatus.DEGRADED
            self.services["dependency_manager"].error_message = str(e)

    async def _health_check_parent_directory_manager(self):
        """Perform health check on Parent Directory Manager."""
        try:
            # Check managed directories
            directories = await self.parent_directory_manager.list_managed_directories()

            self.services["parent_directory_manager"].status = CMPMServiceStatus.OPERATIONAL
            self.services["parent_directory_manager"].last_health_check = datetime.now()
            self.services["parent_directory_manager"].metadata["managed_directories"] = len(
                directories
            )

        except Exception as e:
            self.services["parent_directory_manager"].status = CMPMServiceStatus.DEGRADED
            self.services["parent_directory_manager"].error_message = str(e)

    async def _health_monitoring_task(self):
        """Background task for continuous health monitoring."""
        while not self._stop_event.is_set():
            try:
                await self._perform_comprehensive_health_check()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring task error: {e}")
                await asyncio.sleep(self.health_check_interval)

    # Public API Methods

    async def get_integration_status(self) -> CMPMIntegrationStatus:
        """Get comprehensive integration status."""
        operational_services = sum(
            1
            for service in self.services.values()
            if service.status == CMPMServiceStatus.OPERATIONAL
        )
        error_services = sum(
            1 for service in self.services.values() if service.status == CMPMServiceStatus.ERROR
        )
        total_services = len([s for s in self.services.values() if s.available])

        # Calculate health score
        health_score = (
            int((operational_services / total_services) * 100) if total_services > 0 else 0
        )

        # Generate troubleshooting recommendations
        recommendations = self._generate_troubleshooting_recommendations()

        return CMPMIntegrationStatus(
            integration_level=self.integration_level,
            services=self.services.copy(),
            deployment_config=self.deployment_config.copy(),
            health_score=health_score,
            total_services=total_services,
            operational_services=operational_services,
            error_services=error_services,
            timestamp=datetime.now(),
            troubleshooting_recommendations=recommendations,
        )

    def _generate_troubleshooting_recommendations(self) -> List[str]:
        """Generate troubleshooting recommendations based on current status."""
        recommendations = []

        for service_id, service_info in self.services.items():
            if service_info.status == CMPMServiceStatus.ERROR:
                if service_id == "template_manager":
                    recommendations.append(
                        "Template Manager error: Check template directory permissions and disk space"
                    )
                elif service_id == "dependency_manager":
                    recommendations.append(
                        "Dependency Manager error: Verify Python environment and network connectivity"
                    )
                elif service_id == "parent_directory_manager":
                    recommendations.append(
                        "Parent Directory Manager error: Check file system permissions and configuration"
                    )

            elif service_info.status == CMPMServiceStatus.DEGRADED:
                recommendations.append(
                    f"{service_info.name} is degraded: {service_info.error_message}"
                )

            elif not service_info.available:
                recommendations.append(f"{service_info.name} is not available: Check installation")

        if self.integration_level == IntegrationLevel.BASIC:
            recommendations.append(
                "Consider installing missing CMPM services for enhanced functionality"
            )

        return recommendations

    async def repair_service(self, service_id: str) -> bool:
        """Attempt to repair a failed service."""
        if service_id not in self.services:
            return False

        service_info = self.services[service_id]
        if service_info.status != CMPMServiceStatus.ERROR:
            return True

        try:
            self.logger.info(f"Attempting to repair service: {service_id}")

            if service_id == "template_manager" and TEMPLATE_MANAGER_AVAILABLE:
                await self._initialize_template_manager()
            elif service_id == "dependency_manager" and DEPENDENCY_MANAGER_AVAILABLE:
                await self._initialize_dependency_manager()
            elif service_id == "parent_directory_manager" and PARENT_DIRECTORY_MANAGER_AVAILABLE:
                await self._initialize_parent_directory_manager()

            return service_info.status == CMPMServiceStatus.OPERATIONAL

        except Exception as e:
            self.logger.error(f"Failed to repair service {service_id}: {e}")
            return False

    async def get_service_diagnostics(self, service_id: str) -> Dict[str, Any]:
        """Get detailed diagnostics for a specific service."""
        if service_id not in self.services:
            return TaskToolResponse(
                request_id=f"diagnostics_{service_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                error=f"Service {service_id} not found",
                performance_metrics={"service_found": False}
            ).__dict__

        service_info = self.services[service_id]
        diagnostics = {
            "service_id": service_id,
            "name": service_info.name,
            "version": service_info.version,
            "status": service_info.status.value,
            "available": service_info.available,
            "initialized": service_info.initialized,
            "error_message": service_info.error_message,
            "last_health_check": (
                service_info.last_health_check.isoformat()
                if service_info.last_health_check
                else None
            ),
            "metadata": service_info.metadata,
            "deployment_config": self.deployment_config,
        }

        # Add service-specific diagnostics
        try:
            if service_id == "template_manager" and self.template_manager:
                diagnostics["service_specific"] = {
                    "template_paths": str(self.template_manager.template_paths),
                    "registry_loaded": bool(self.template_manager.template_registry),
                }
            elif service_id == "dependency_manager" and self.dependency_manager:
                diagnostics["service_specific"] = {
                    "dependencies_count": len(self.dependency_manager.get_dependencies()),
                    "python_command": self.dependency_manager.python_cmd,
                    "platform": self.dependency_manager.platform,
                }
            elif service_id == "parent_directory_manager" and self.parent_directory_manager:
                directories = await self.parent_directory_manager.list_managed_directories()
                diagnostics["service_specific"] = {
                    "managed_directories_count": len(directories),
                    "working_dir": str(self.parent_directory_manager.working_dir),
                }
        except Exception as e:
            diagnostics["service_specific"] = {"error": str(e)}

        return diagnostics

    async def generate_troubleshooting_guide(self) -> Dict[str, Any]:
        """Generate comprehensive troubleshooting guide."""
        status = await self.get_integration_status()

        guide = {
            "cmpm_version": "4.5.1",
            "integration_level": status.integration_level.value,
            "health_score": status.health_score,
            "timestamp": datetime.now().isoformat(),
            "deployment_config": status.deployment_config,
            "service_status": {},
            "common_issues": [],
            "troubleshooting_steps": [],
            "recommendations": status.troubleshooting_recommendations,
        }

        # Add service status
        for service_id, service_info in status.services.items():
            guide["service_status"][service_id] = {
                "name": service_info.name,
                "status": service_info.status.value,
                "available": service_info.available,
                "error": service_info.error_message,
            }

        # Add common issues and solutions
        guide["common_issues"] = [
            {
                "issue": "Service initialization timeout",
                "solution": "Increase initialization timeout or check system resources",
                "command": "claude-pm --dependency-status",
            },
            {
                "issue": "Template Manager not available",
                "solution": "Check Python path and module installation",
                "command": "python -c 'from claude_pm.services.template_manager import TemplateManager'",
            },
            {
                "issue": "Dependency detection failures",
                "solution": "Verify network connectivity and package managers (npm, pip)",
                "command": "claude-pm --dependency-status",
            },
            {
                "issue": "Parent directory access denied",
                "solution": "Check file system permissions and working directory",
                "command": "claude-pm --parent-directory-status",
            },
        ]

        # Add troubleshooting steps
        guide["troubleshooting_steps"] = [
            "1. Check deployment detection: claude-pm --deployment-info",
            "2. Verify service availability: claude-pm --template-status",
            "3. Test dependency management: claude-pm --dependency-status",
            "4. Validate parent directory setup: claude-pm --parent-directory-status",
            "5. Review logs in logs/ directory for detailed error information",
            "6. Try service repair using the CLI repair commands",
        ]

        return guide

    # CLI Integration Methods

    async def handle_cli_template_status(self) -> Dict[str, Any]:
        """Handle CLI template status command."""
        if not TEMPLATE_MANAGER_AVAILABLE:
            return {
                "error": "Template Manager not available",
                "available": False,
                "recommendation": "Check Python path and module installation",
            }

        try:
            if not self.template_manager:
                await self._initialize_template_manager()

            templates = await self.template_manager.list_templates()

            return {
                "initialized": True,
                "template_count": len(templates),
                "templates": templates[:5],  # Show first 5
                "deployment_type": self.deployment_config.get("deployment_type", "unknown"),
                "status": "operational",
            }
        except Exception as e:
            return TaskToolResponse(
                request_id=f"template_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                error=str(e),
                performance_metrics={"initialized": False, "status": "error"}
            ).__dict__

    async def handle_cli_dependency_status(self) -> Dict[str, Any]:
        """Handle CLI dependency status command."""
        if not DEPENDENCY_MANAGER_AVAILABLE:
            return {
                "error": "Dependency Manager not available",
                "available": False,
                "recommendation": "Check Python path and module installation",
            }

        try:
            if not self.dependency_manager:
                await self._initialize_dependency_manager()

            dependencies = self.dependency_manager.get_dependencies()
            report = await self.dependency_manager.generate_dependency_report()

            return {
                "initialized": True,
                "dependencies_tracked": len(dependencies),
                "health_score": report.health_score,
                "missing_dependencies": report.missing_dependencies,
                "deployment_type": self.deployment_config.get("deployment_type", "unknown"),
                "status": "operational",
            }
        except Exception as e:
            return TaskToolResponse(
                request_id=f"dependency_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                error=str(e),
                performance_metrics={"initialized": False, "status": "error"}
            ).__dict__

    async def handle_cli_parent_directory_status(self) -> Dict[str, Any]:
        """Handle CLI parent directory status command."""
        if not PARENT_DIRECTORY_MANAGER_AVAILABLE:
            return {
                "error": "Parent Directory Manager not available",
                "available": False,
                "recommendation": "Check Python path and module installation",
            }

        try:
            if not self.parent_directory_manager:
                await self._initialize_parent_directory_manager()

            directories = await self.parent_directory_manager.list_managed_directories()

            return {
                "initialized": True,
                "managed_directories": len(directories),
                "directories": directories[:3],  # Show first 3
                "deployment_type": self.deployment_config.get("deployment_type", "unknown"),
                "status": "operational",
            }
        except Exception as e:
            return TaskToolResponse(
                request_id=f"parent_directory_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                error=str(e),
                performance_metrics={"initialized": False, "status": "error"}
            ).__dict__
