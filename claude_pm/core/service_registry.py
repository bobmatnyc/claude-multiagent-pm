"""
Service Registry for Claude PM Framework

Provides singleton service management to prevent connection leaks
and ensure proper service lifecycle management.
"""

import asyncio
import logging
import weakref
from typing import Dict, Type, Optional, Any
from dataclasses import dataclass
from contextlib import asynccontextmanager

from .base_service import BaseService


@dataclass
class ServiceInfo:
    """Information about a registered service."""

    instance: BaseService
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0


class ServiceRegistry:
    """
    Singleton service registry for managing service instances.

    Prevents connection leaks by ensuring services are properly
    managed and cleaned up.
    """

    _instance: Optional["ServiceRegistry"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        """Initialize service registry."""
        self.logger = logging.getLogger(__name__)
        self._services: Dict[str, ServiceInfo] = {}
        self._cleanup_lock = asyncio.Lock()
        self._initialized = False
        self._shutdown = False

        # Track service references
        self._service_refs: weakref.WeakSet = weakref.WeakSet()

    @classmethod
    async def get_instance(cls) -> "ServiceRegistry":
        """Get singleton service registry instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance.initialize()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize the service registry."""
        if self._initialized:
            return

        self.logger.info("Initializing Service Registry")
        self._initialized = True
        self._shutdown = False

    async def get_service(
        self, service_class: Type[BaseService], service_name: Optional[str] = None, **kwargs
    ) -> BaseService:
        """
        Get or create a service instance.

        Args:
            service_class: Service class to instantiate
            service_name: Optional custom service name
            **kwargs: Arguments for service initialization

        Returns:
            Service instance
        """
        if self._shutdown:
            raise RuntimeError("Service registry is shutdown")

        # Generate service key
        key = service_name or service_class.__name__

        # Check for existing service
        if key in self._services:
            service_info = self._services[key]
            service_info.access_count += 1
            service_info.last_accessed = asyncio.get_event_loop().time()

            # Ensure service is still healthy
            if service_info.instance.running:
                self.logger.debug(f"Reusing service: {key}")
                return service_info.instance
            else:
                # Service is not running, remove and recreate
                self.logger.warning(f"Service {key} found but not running, recreating")
                await self._remove_service(key)

        # Create new service instance
        self.logger.info(f"Creating new service: {key}")
        service = service_class(**kwargs)

        # Start the service
        await service.start()

        # Register service
        current_time = asyncio.get_event_loop().time()
        service_info = ServiceInfo(
            instance=service, created_at=current_time, access_count=1, last_accessed=current_time
        )

        self._services[key] = service_info
        self._service_refs.add(service)

        self.logger.info(f"Service {key} created and registered")
        return service

    @asynccontextmanager
    async def temporary_service(self, service_class: Type[BaseService], **kwargs):
        """
        Create a temporary service that's automatically cleaned up.

        This is ideal for health checks and short-lived operations.
        """
        service = None
        try:
            # Create service without registering it
            service = service_class(**kwargs)
            await service.start()

            self.logger.debug(f"Created temporary service: {service_class.__name__}")
            yield service

        finally:
            # Always cleanup the temporary service
            if service:
                try:
                    await service.stop()
                    self.logger.debug(f"Cleaned up temporary service: {service_class.__name__}")
                except Exception as e:
                    self.logger.warning(
                        f"Error cleaning up temporary service {service_class.__name__}: {e}"
                    )

    async def remove_service(self, service_name: str) -> bool:
        """
        Remove a service from the registry.

        Args:
            service_name: Name of service to remove

        Returns:
            True if service was removed
        """
        return await self._remove_service(service_name)

    async def _remove_service(self, service_name: str) -> bool:
        """Internal method to remove a service."""
        if service_name not in self._services:
            return False

        service_info = self._services[service_name]

        try:
            # Stop the service
            if service_info.instance.running:
                await service_info.instance.stop()

            # Remove from registry
            del self._services[service_name]

            self.logger.info(f"Service {service_name} removed from registry")
            return True

        except Exception as e:
            self.logger.error(f"Error removing service {service_name}: {e}")
            return False

    async def cleanup_all(self) -> None:
        """Cleanup all registered services."""
        async with self._cleanup_lock:
            if not self._services:
                return

            self.logger.info(f"Cleaning up {len(self._services)} registered services")

            # Stop all services in parallel
            cleanup_tasks = []
            for service_name, service_info in list(self._services.items()):
                task = asyncio.create_task(self._cleanup_service(service_name, service_info))
                cleanup_tasks.append(task)

            # Wait for all cleanup tasks to complete
            if cleanup_tasks:
                results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)

                # Log any cleanup errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        service_name = (
                            list(self._services.keys())[i]
                            if i < len(self._services)
                            else f"service_{i}"
                        )
                        self.logger.error(f"Error cleaning up service {service_name}: {result}")

            # Clear registry
            self._services.clear()
            self.logger.info("Service registry cleanup completed")

    async def _cleanup_service(self, service_name: str, service_info: ServiceInfo) -> None:
        """Cleanup a single service."""
        try:
            if service_info.instance.running:
                await service_info.instance.stop()
            self.logger.debug(f"Cleaned up service: {service_name}")
        except Exception as e:
            self.logger.warning(f"Error cleaning up service {service_name}: {e}")

    async def shutdown(self) -> None:
        """Shutdown the service registry."""
        if self._shutdown:
            return

        self.logger.info("Shutting down Service Registry")
        self._shutdown = True

        # Cleanup all services
        await self.cleanup_all()

        self.logger.info("Service Registry shutdown completed")

    def get_stats(self) -> Dict[str, Any]:
        """Get service registry statistics."""
        current_time = asyncio.get_event_loop().time()

        service_stats = {}
        for name, info in self._services.items():
            service_stats[name] = {
                "running": info.instance.running,
                "access_count": info.access_count,
                "uptime": current_time - info.created_at,
                "last_accessed": current_time - info.last_accessed,
            }

        return {
            "total_services": len(self._services),
            "initialized": self._initialized,
            "shutdown": self._shutdown,
            "services": service_stats,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on service registry."""
        try:
            stats = self.get_stats()

            # Check service health
            healthy_services = 0
            total_services = len(self._services)

            for service_info in self._services.values():
                if service_info.instance.running:
                    healthy_services += 1

            health_status = "healthy" if healthy_services == total_services else "degraded"

            return {
                "status": health_status,
                "total_services": total_services,
                "healthy_services": healthy_services,
                "stats": stats,
            }

        except Exception as e:
            self.logger.error(f"Service registry health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Convenience function for getting service registry
async def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return await ServiceRegistry.get_instance()
