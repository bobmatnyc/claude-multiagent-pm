"""
Unified Memory Service

This module implements the main FlexibleMemoryService that provides a unified
interface to multiple memory backends with auto-detection, circuit breaker,
and fallback capabilities.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union

from ..interfaces.backend import MemoryBackend
from ..interfaces.models import (
    MemoryItem,
    MemoryQuery,
    MemoryCategory,
    HealthStatus,
    OperationResult,
    MemoryStatistics,
)
from ..interfaces.exceptions import (
    MemoryServiceError,
    BackendNotAvailableError,
    CircuitBreakerOpenError,
    ConfigurationError,
    BackendError,
)
from ..backends.mem0ai_backend import Mem0AIBackend
from ..backends.sqlite_backend import SQLiteBackend
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerManager
from .auto_detection import AutoDetectionEngine
from ..monitoring.performance import PerformanceMonitor


class FlexibleMemoryService:
    """
    Unified memory service with auto-detection and fallback capabilities.

    This service provides a consistent interface to memory operations while
    automatically selecting the best available backend and gracefully handling
    failures through circuit breaker patterns and fallback mechanisms.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the flexible memory service.

        Args:
            config: Service configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Service state
        self._initialized = False
        self._is_healthy = False

        # Available backends
        self.backends: Dict[str, MemoryBackend] = {}
        self.active_backend: Optional[MemoryBackend] = None
        self.active_backend_name: Optional[str] = None

        # Fallback chain configuration
        self.fallback_chain: List[str] = self.config.get("fallback_chain", ["mem0ai", "sqlite"])

        # Circuit breaker manager
        cb_config = CircuitBreakerConfig(
            failure_threshold=self.config.get("circuit_breaker_threshold", 5),
            recovery_timeout=self.config.get("circuit_breaker_recovery", 60),
            test_requests=self.config.get("circuit_breaker_test_requests", 3),
            success_threshold=self.config.get("circuit_breaker_success_threshold", 2),
        )
        self.circuit_breaker_manager = CircuitBreakerManager(cb_config)

        # Auto-detection engine
        self.auto_detection = AutoDetectionEngine(
            timeout=self.config.get("detection_timeout", 2.0),
            retry_attempts=self.config.get("detection_retries", 3),
        )

        # Performance monitoring
        self.performance_monitor = PerformanceMonitor(
            retention_seconds=self.config.get("metrics_retention", 86400)
        )

        # Service metrics
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "backend_switches": 0,
            "circuit_breaker_activations": 0,
            "fallback_activations": 0,
            "initialization_time": 0.0,
            "service_start_time": time.time(),
        }

        # Initialize backends
        self._initialize_backends()

    def _initialize_backends(self):
        """Initialize all available backends."""
        try:
            # mem0AI Backend
            if self.config.get("mem0ai_enabled", True):
                self.backends["mem0ai"] = Mem0AIBackend(
                    {
                        "host": self.config.get("mem0ai_host", "localhost"),
                        "port": self.config.get("mem0ai_port", 8002),
                        "timeout": self.config.get("mem0ai_timeout", 30),
                        "api_key": self.config.get("mem0ai_api_key"),
                    }
                )

            # SQLite Backend
            if self.config.get("sqlite_enabled", True):
                self.backends["sqlite"] = SQLiteBackend(
                    {
                        "db_path": self.config.get("sqlite_path", "memory.db"),
                        "enable_fts": self.config.get("sqlite_fts", True),
                        "enable_wal": self.config.get("sqlite_wal", True),
                    }
                )

            # Filter fallback chain to only include enabled backends
            self.fallback_chain = [
                backend for backend in self.fallback_chain if backend in self.backends
            ]

            self.logger.info(
                f"Initialized {len(self.backends)} backends: {list(self.backends.keys())}"
            )
            self.logger.info(f"Fallback chain: {self.fallback_chain}")

        except Exception as e:
            self.logger.error(f"Failed to initialize backends: {e}")
            raise ConfigurationError(f"Backend initialization failed: {e}")

    async def initialize(self) -> bool:
        """
        Initialize the memory service with auto-detection.

        Returns:
            bool: True if initialization was successful
        """
        if self._initialized:
            return True

        start_time = time.time()

        try:
            self.logger.info("Initializing flexible memory service...")

            # Auto-detect best available backend
            detection_result = await self.auto_detection.detect_best_backend(
                self.backends, self.fallback_chain
            )

            if detection_result:
                self.active_backend = detection_result.backend
                self.active_backend_name = detection_result.backend_name
                self.logger.info(f"Selected backend: {self.active_backend_name}")
                self.logger.info(f"Selection reason: {detection_result.selection_reason}")

                self._initialized = True
                self._is_healthy = True

                # Record initialization metrics
                self.metrics["initialization_time"] = time.time() - start_time

                return True
            else:
                self.logger.error("No functional memory backend detected")
                raise BackendNotAvailableError(
                    "No healthy backend available", list(self.backends.keys())
                )

        except Exception as e:
            self.logger.error(f"Failed to initialize memory service: {e}")
            self._initialized = False
            self._is_healthy = False
            raise

    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Add a memory with circuit breaker protection and fallback.

        Args:
            project_name: Name of the project
            content: Memory content
            category: Memory category
            tags: Optional tags
            metadata: Optional metadata

        Returns:
            Optional[str]: Memory ID if successful, None otherwise
        """
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")

        operation_result = await self._execute_with_fallback(
            "add_memory",
            project_name=project_name,
            content=content,
            category=category,
            tags=tags,
            metadata=metadata,
        )

        if operation_result.success:
            return operation_result.data
        else:
            self.logger.error(f"Failed to add memory: {operation_result.error}")
            return None

    async def search_memories(self, project_name: str, query: MemoryQuery) -> List[MemoryItem]:
        """
        Search memories with circuit breaker protection and fallback.

        Args:
            project_name: Name of the project
            query: Search query

        Returns:
            List[MemoryItem]: List of matching memories
        """
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")

        operation_result = await self._execute_with_fallback(
            "search_memories", project_name=project_name, query=query
        )

        if operation_result.success:
            return operation_result.data or []
        else:
            self.logger.error(f"Failed to search memories: {operation_result.error}")
            return []

    async def get_memory(self, project_name: str, memory_id: str) -> Optional[MemoryItem]:
        """
        Get a specific memory by ID.

        Args:
            project_name: Name of the project
            memory_id: Memory identifier

        Returns:
            Optional[MemoryItem]: Memory item if found
        """
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")

        operation_result = await self._execute_with_fallback(
            "get_memory", project_name=project_name, memory_id=memory_id
        )

        if operation_result.success:
            return operation_result.data
        else:
            self.logger.error(f"Failed to get memory: {operation_result.error}")
            return None

    async def update_memory(
        self,
        project_name: str,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update an existing memory.

        Args:
            project_name: Name of the project
            memory_id: Memory identifier
            content: New content (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)

        Returns:
            bool: True if update was successful
        """
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")

        operation_result = await self._execute_with_fallback(
            "update_memory",
            project_name=project_name,
            memory_id=memory_id,
            content=content,
            tags=tags,
            metadata=metadata,
        )

        if operation_result.success:
            return operation_result.data or False
        else:
            self.logger.error(f"Failed to update memory: {operation_result.error}")
            return False

    async def delete_memory(self, project_name: str, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            project_name: Name of the project
            memory_id: Memory identifier

        Returns:
            bool: True if deletion was successful
        """
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")

        operation_result = await self._execute_with_fallback(
            "delete_memory", project_name=project_name, memory_id=memory_id
        )

        if operation_result.success:
            return operation_result.data or False
        else:
            self.logger.error(f"Failed to delete memory: {operation_result.error}")
            return False

    async def get_project_memories(
        self, project_name: str, category: Optional[MemoryCategory] = None, limit: int = 100
    ) -> List[MemoryItem]:
        """
        Get all memories for a project.

        Args:
            project_name: Name of the project
            category: Optional category filter
            limit: Maximum number of memories to return

        Returns:
            List[MemoryItem]: List of memories
        """
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")

        operation_result = await self._execute_with_fallback(
            "get_project_memories", project_name=project_name, category=category, limit=limit
        )

        if operation_result.success:
            return operation_result.data or []
        else:
            self.logger.error(f"Failed to get project memories: {operation_result.error}")
            return []

    async def get_memory_stats(self, project_name: str) -> Dict[str, Any]:
        """
        Get memory statistics for a project.

        Args:
            project_name: Name of the project

        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")

        operation_result = await self._execute_with_fallback(
            "get_memory_stats", project_name=project_name
        )

        if operation_result.success:
            return operation_result.data or {}
        else:
            self.logger.error(f"Failed to get memory stats: {operation_result.error}")
            return {}

    async def _execute_with_fallback(self, operation: str, **kwargs) -> OperationResult:
        """
        Execute operation with circuit breaker protection and fallback.

        Args:
            operation: Operation name
            **kwargs: Operation arguments

        Returns:
            OperationResult: Operation result
        """
        self.metrics["total_operations"] += 1

        # Try each backend in fallback chain
        for backend_name in self.fallback_chain:
            if backend_name not in self.backends:
                continue

            backend = self.backends[backend_name]
            circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(backend_name)

            try:
                # Execute operation with circuit breaker
                result = await circuit_breaker.call(
                    self._execute_backend_operation, backend, operation, **kwargs
                )

                # Success - update metrics and return
                self.metrics["successful_operations"] += 1

                # Switch active backend if different
                if self.active_backend_name != backend_name:
                    self.logger.info(
                        f"Switching active backend from {self.active_backend_name} to {backend_name}"
                    )
                    self.active_backend = backend
                    self.active_backend_name = backend_name
                    self.metrics["backend_switches"] += 1

                return OperationResult(
                    success=True, data=result, backend_used=backend_name, operation_type=operation
                )

            except CircuitBreakerOpenError:
                self.logger.warning(f"Circuit breaker open for {backend_name}, trying next backend")
                self.metrics["circuit_breaker_activations"] += 1
                continue

            except Exception as e:
                self.logger.warning(f"Backend {backend_name} failed for {operation}: {e}")
                continue

        # All backends failed
        self.metrics["failed_operations"] += 1
        self.metrics["fallback_activations"] += 1

        return OperationResult(success=False, error="All backends failed", operation_type=operation)

    async def _execute_backend_operation(
        self, backend: MemoryBackend, operation: str, **kwargs
    ) -> Any:
        """
        Execute operation on a specific backend with performance monitoring.

        Args:
            backend: Backend instance
            operation: Operation name
            **kwargs: Operation arguments

        Returns:
            Any: Operation result
        """
        # Ensure backend is initialized
        if not backend.is_initialized():
            await backend.initialize()

        # Get operation method
        method = getattr(backend, operation)
        if not method:
            raise BackendError(f"Backend {backend.backend_name} does not support {operation}")

        # Execute with performance monitoring
        with self.performance_monitor.measure_operation(operation, backend.backend_name):
            return await method(**kwargs)

    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get comprehensive service health information.

        Returns:
            Dict[str, Any]: Service health data
        """
        health_data = {
            "service_initialized": self._initialized,
            "service_healthy": self._is_healthy,
            "active_backend": self.active_backend_name,
            "fallback_chain": self.fallback_chain,
            "metrics": self.metrics.copy(),
            "backends": {},
            "circuit_breakers": {},
            "performance": {},
        }

        # Get backend health
        for name, backend in self.backends.items():
            try:
                health_status = await backend.get_health_status()
                health_data["backends"][name] = health_status.to_dict()
            except Exception as e:
                health_data["backends"][name] = {
                    "backend_name": name,
                    "is_healthy": False,
                    "error": str(e),
                }

        # Get circuit breaker states
        health_data["circuit_breakers"] = await self.circuit_breaker_manager.get_all_states()

        # Get performance metrics
        health_data["performance"] = self.performance_monitor.get_performance_summary()

        return health_data

    async def switch_backend(self, backend_name: str) -> bool:
        """
        Manually switch to a specific backend.

        Args:
            backend_name: Name of the backend to switch to

        Returns:
            bool: True if switch was successful
        """
        if backend_name not in self.backends:
            self.logger.error(f"Backend {backend_name} not available")
            return False

        backend = self.backends[backend_name]

        # Check if backend is healthy
        try:
            if not backend.is_initialized():
                await backend.initialize()

            if not await backend.health_check():
                self.logger.error(f"Backend {backend_name} is not healthy")
                return False

            # Switch backend
            old_backend = self.active_backend_name
            self.active_backend = backend
            self.active_backend_name = backend_name
            self.metrics["backend_switches"] += 1

            self.logger.info(f"Switched backend from {old_backend} to {backend_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to switch to backend {backend_name}: {e}")
            return False

    async def reset_circuit_breaker(self, backend_name: str = None) -> bool:
        """
        Reset circuit breaker for a specific backend or all backends.

        Args:
            backend_name: Backend name (optional, resets all if None)

        Returns:
            bool: True if reset was successful
        """
        try:
            if backend_name:
                await self.circuit_breaker_manager.reset_circuit_breaker(backend_name)
            else:
                await self.circuit_breaker_manager.reset_all()

            self.logger.info(f"Reset circuit breaker for {backend_name or 'all backends'}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reset circuit breaker: {e}")
            return False

    def get_backend_list(self) -> List[str]:
        """
        Get list of available backends.

        Returns:
            List[str]: List of backend names
        """
        return list(self.backends.keys())

    def get_active_backend_name(self) -> Optional[str]:
        """
        Get name of currently active backend.

        Returns:
            Optional[str]: Active backend name
        """
        return self.active_backend_name

    def get_fallback_chain(self) -> List[str]:
        """
        Get current fallback chain.

        Returns:
            List[str]: Fallback chain
        """
        return self.fallback_chain.copy()

    def set_fallback_chain(self, chain: List[str]) -> bool:
        """
        Set new fallback chain.

        Args:
            chain: New fallback chain

        Returns:
            bool: True if successful
        """
        # Validate chain
        for backend_name in chain:
            if backend_name not in self.backends:
                self.logger.error(f"Backend {backend_name} not available")
                return False

        self.fallback_chain = chain.copy()
        self.logger.info(f"Updated fallback chain: {self.fallback_chain}")
        return True

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.

        Returns:
            Dict[str, Any]: Service metrics
        """
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset service metrics."""
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "backend_switches": 0,
            "circuit_breaker_activations": 0,
            "fallback_activations": 0,
            "initialization_time": self.metrics["initialization_time"],
            "service_start_time": self.metrics["service_start_time"],
        }

        # Reset performance monitor
        self.performance_monitor.reset_metrics()

        # Reset circuit breaker metrics
        for cb in self.circuit_breaker_manager.circuit_breakers.values():
            cb.reset_metrics()

    async def cleanup(self):
        """Cleanup all resources."""
        self.logger.info("Cleaning up flexible memory service...")

        # Cleanup all backends
        for name, backend in self.backends.items():
            try:
                await backend.cleanup()
                self.logger.debug(f"Cleaned up backend: {name}")
            except Exception as e:
                self.logger.warning(f"Error cleaning up backend {name}: {e}")

        # Reset state
        self._initialized = False
        self._is_healthy = False
        self.active_backend = None
        self.active_backend_name = None

        self.logger.info("Flexible memory service cleanup completed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"FlexibleMemoryService(initialized={self._initialized}, "
            f"active_backend={self.active_backend_name}, "
            f"backends={list(self.backends.keys())})"
        )
