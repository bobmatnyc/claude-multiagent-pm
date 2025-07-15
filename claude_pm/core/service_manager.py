"""
Service manager for Claude PM Framework.

Provides centralized service management including:
- Service registration and discovery
- Lifecycle management
- Health monitoring across services
- Dependency resolution
- Graceful shutdown coordination
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Type, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .base_service import BaseService, ServiceHealth


@dataclass
class ServiceInfo:
    """Information about a registered service."""

    name: str
    service: BaseService
    dependencies: List[str]
    startup_order: int
    auto_start: bool = True
    critical: bool = False


class ServiceManager:
    """
    Central service manager for Claude PM Framework.

    Manages the lifecycle of all services in the framework,
    handles dependencies, and provides service discovery.
    """

    def __init__(
        self,
        framework_path: Optional[Path] = None,
        user_home: Optional[Path] = None,
        project_path: Optional[Path] = None,
    ):
        """Initialize the service manager."""
        self.logger = logging.getLogger(__name__)
        self._services: Dict[str, ServiceInfo] = {}
        self._running = False
        self._start_order: List[str] = []
        self._stop_order: List[str] = []

        # Path configuration
        self.framework_path = framework_path or Path.cwd()
        self.user_home = user_home or Path.home()
        self.project_path = project_path or Path.cwd()

    def register_service(
        self,
        service: BaseService,
        dependencies: Optional[List[str]] = None,
        startup_order: int = 0,
        auto_start: bool = True,
        critical: bool = False,
    ) -> None:
        """
        Register a service with the manager.

        Args:
            service: Service instance to register
            dependencies: List of service names this service depends on
            startup_order: Order priority for startup (lower starts first)
            auto_start: Whether to start automatically with start_all()
            critical: Whether this is a critical service
        """
        if service.name in self._services:
            raise ValueError(f"Service '{service.name}' is already registered")

        service_info = ServiceInfo(
            name=service.name,
            service=service,
            dependencies=dependencies or [],
            startup_order=startup_order,
            auto_start=auto_start,
            critical=critical,
        )

        self._services[service.name] = service_info
        self.logger.info(f"Registered service: {service.name}")

        # Recalculate startup/shutdown order
        self._calculate_service_order()

    def unregister_service(self, name: str) -> None:
        """Unregister a service."""
        if name not in self._services:
            self.logger.warning(f"Service '{name}' not found for unregistration")
            return

        service_info = self._services[name]
        if service_info.service.running:
            self.logger.warning(f"Stopping running service '{name}' during unregistration")
            asyncio.create_task(service_info.service.stop())

        del self._services[name]
        self.logger.info(f"Unregistered service: {name}")

        # Recalculate startup/shutdown order
        self._calculate_service_order()

    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a service by name."""
        service_info = self._services.get(name)
        return service_info.service if service_info else None

    def list_services(self) -> List[str]:
        """Get list of registered service names."""
        return list(self._services.keys())

    def get_service_info(self, name: str) -> Optional[ServiceInfo]:
        """Get service information."""
        return self._services.get(name)

    async def start_service(self, name: str) -> None:
        """Start a specific service and its dependencies."""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found")

        service_info = self._services[name]

        # Start dependencies first
        for dep_name in service_info.dependencies:
            dep_service = self.get_service(dep_name)
            if dep_service and not dep_service.running:
                self.logger.info(f"Starting dependency '{dep_name}' for '{name}'")
                await self.start_service(dep_name)

        # Start the service
        if not service_info.service.running:
            self.logger.info(f"Starting service: {name}")
            await service_info.service.start()
        else:
            self.logger.info(f"Service '{name}' is already running")

    async def stop_service(self, name: str) -> None:
        """Stop a specific service."""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found")

        service_info = self._services[name]

        if service_info.service.running:
            self.logger.info(f"Stopping service: {name}")
            await service_info.service.stop()
        else:
            self.logger.info(f"Service '{name}' is already stopped")

    async def restart_service(self, name: str) -> None:
        """Restart a specific service."""
        self.logger.info(f"Restarting service: {name}")
        await self.stop_service(name)
        await self.start_service(name)

    async def start_all(self) -> None:
        """Start all registered services in dependency order."""
        if self._running:
            self.logger.warning("Service manager is already running")
            return

        self.logger.info("Starting all services...")

        try:
            for service_name in self._start_order:
                service_info = self._services[service_name]

                if service_info.auto_start and not service_info.service.running:
                    self.logger.info(f"Starting service: {service_name}")
                    await service_info.service.start()

                    # Brief pause between service starts
                    await asyncio.sleep(0.1)

            self._running = True
            self.logger.info("All services started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start all services: {e}")
            # Stop any services that were started
            await self.stop_all()
            raise

    async def stop_all(self) -> None:
        """Stop all running services in reverse dependency order."""
        if not self._running:
            self.logger.warning("Service manager is not running")
            return

        self.logger.info("Stopping all services...")

        try:
            # Stop in reverse order
            for service_name in self._stop_order:
                service_info = self._services[service_name]

                if service_info.service.running:
                    self.logger.info(f"Stopping service: {service_name}")
                    await service_info.service.stop()

                    # Brief pause between service stops
                    await asyncio.sleep(0.1)

            self._running = False
            self.logger.info("All services stopped successfully")

        except Exception as e:
            self.logger.error(f"Error stopping services: {e}")
            raise

    async def restart_all(self) -> None:
        """Restart all services."""
        self.logger.info("Restarting all services...")
        await self.stop_all()
        await self.start_all()

    async def health_check_all(self) -> Dict[str, ServiceHealth]:
        """Perform health check on all services."""
        self.logger.debug("Running health check on all services...")

        health_results = {}

        for service_name, service_info in self._services.items():
            try:
                health = await service_info.service.health_check()
                health_results[service_name] = health
            except Exception as e:
                self.logger.error(f"Health check failed for service '{service_name}': {e}")
                health_results[service_name] = ServiceHealth(
                    status="unhealthy",
                    message=f"Health check error: {str(e)}",
                    timestamp=datetime.now().isoformat(),
                )

        return health_results

    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all services."""
        status = {}

        for service_name, service_info in self._services.items():
            service = service_info.service
            status[service_name] = {
                "running": service.running,
                "uptime": service.uptime,
                "health": service.health.status,
                "dependencies": service_info.dependencies,
                "critical": service_info.critical,
                "auto_start": service_info.auto_start,
            }

        return status

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the service dependency graph."""
        graph = {}
        for service_name, service_info in self._services.items():
            graph[service_name] = service_info.dependencies.copy()
        return graph

    def _calculate_service_order(self) -> None:
        """Calculate startup and shutdown order based on dependencies."""
        # Topological sort for startup order
        self._start_order = self._topological_sort()

        # Reverse order for shutdown
        self._stop_order = list(reversed(self._start_order))

    def _topological_sort(self) -> List[str]:
        """Perform topological sort to determine service startup order."""
        # Build dependency graph
        graph = {}
        in_degree = {}

        for service_name, service_info in self._services.items():
            graph[service_name] = service_info.dependencies.copy()
            in_degree[service_name] = 0

        # Calculate in-degrees
        for service_name, dependencies in graph.items():
            for dep in dependencies:
                if dep in in_degree:
                    in_degree[service_name] += 1
                else:
                    self.logger.warning(
                        f"Dependency '{dep}' for service '{service_name}' not found"
                    )

        # Sort by startup_order within same dependency level
        queue = []
        for service_name in self._services:
            if in_degree[service_name] == 0:
                queue.append(service_name)

        # Sort initial queue by startup_order
        queue.sort(key=lambda name: self._services[name].startup_order)

        result = []

        while queue:
            # Sort current level by startup_order
            queue.sort(key=lambda name: self._services[name].startup_order)
            current = queue.pop(0)
            result.append(current)

            # Update dependencies
            for service_name, dependencies in graph.items():
                if current in dependencies:
                    dependencies.remove(current)
                    in_degree[service_name] -= 1

                    if in_degree[service_name] == 0:
                        queue.append(service_name)

        # Check for circular dependencies
        if len(result) != len(self._services):
            remaining = set(self._services.keys()) - set(result)
            raise ValueError(f"Circular dependency detected among services: {remaining}")

        return result

    async def wait_for_healthy(self, timeout: float = 60.0) -> bool:
        """
        Wait for all critical services to become healthy.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if all critical services are healthy, False if timeout
        """
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            health_results = await self.health_check_all()

            # Check critical services
            critical_unhealthy = []
            for service_name, service_info in self._services.items():
                if service_info.critical:
                    health = health_results.get(service_name)
                    if not health or health.status != "healthy":
                        critical_unhealthy.append(service_name)

            if not critical_unhealthy:
                self.logger.info("All critical services are healthy")
                return True

            self.logger.debug(
                f"Waiting for critical services to become healthy: {critical_unhealthy}"
            )
            await asyncio.sleep(1.0)

        self.logger.warning(f"Timeout waiting for critical services to become healthy")
        return False

    def __repr__(self) -> str:
        """String representation of service manager."""
        return f"<ServiceManager(services={len(self._services)}, running={self._running})>"