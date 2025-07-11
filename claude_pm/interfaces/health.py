"""
Health Collector Interface for Claude PM Framework.

Defines the abstract interface for health data collection from various subsystems.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio

from ..models.health import ServiceHealthReport, HealthStatus


class HealthCollector(ABC):
    """
    Abstract base class for health data collectors.

    Each collector is responsible for gathering health information
    from a specific subsystem or service category.
    """

    def __init__(self, name: str, timeout_seconds: float = 5.0):
        """
        Initialize the health collector.

        Args:
            name: Unique name for this collector
            timeout_seconds: Maximum time to wait for health collection
        """
        self.name = name
        self.timeout_seconds = timeout_seconds
        self._last_error: Optional[str] = None
        self._collection_count = 0
        self._success_count = 0

    @abstractmethod
    async def collect_health(self) -> List[ServiceHealthReport]:
        """
        Collect health reports from this collector's subsystem.

        Returns:
            List of ServiceHealthReport objects for services in this subsystem

        Raises:
            TimeoutError: If collection takes longer than timeout_seconds
            Exception: For other collection errors
        """
        pass

    @abstractmethod
    def get_subsystem_name(self) -> str:
        """
        Get the name of the subsystem this collector monitors.

        Returns:
            Human-readable subsystem name (e.g., "Framework Services", "External APIs")
        """
        pass

    @abstractmethod
    def get_service_names(self) -> List[str]:
        """
        Get the list of service names this collector monitors.

        Returns:
            List of service names that will be included in health reports
        """
        pass

    async def collect_with_timeout(self) -> List[ServiceHealthReport]:
        """
        Collect health with timeout and error handling.

        Returns:
            List of ServiceHealthReport objects, or error reports if collection fails
        """
        self._collection_count += 1
        start_time = asyncio.get_event_loop().time()

        try:
            # Use asyncio.wait_for for timeout handling
            reports = await asyncio.wait_for(self.collect_health(), timeout=self.timeout_seconds)

            self._success_count += 1
            self._last_error = None
            return reports

        except asyncio.TimeoutError:
            error_msg = f"Health collection timed out after {self.timeout_seconds}s"
            self._last_error = error_msg

            # Return error reports for all services in this collector
            return [
                ServiceHealthReport(
                    name=service_name,
                    status=HealthStatus.ERROR,
                    message=error_msg,
                    timestamp=start_time,
                    error=error_msg,
                )
                for service_name in self.get_service_names()
            ]

        except Exception as e:
            error_msg = f"Health collection error: {str(e)}"
            self._last_error = error_msg

            # Return error reports for all services in this collector
            return [
                ServiceHealthReport(
                    name=service_name,
                    status=HealthStatus.ERROR,
                    message=error_msg,
                    timestamp=start_time,
                    error=error_msg,
                )
                for service_name in self.get_service_names()
            ]

    def get_collector_stats(self) -> Dict[str, Any]:
        """
        Get statistics for this collector.

        Returns:
            Dictionary with collector performance statistics
        """
        success_rate = (self._success_count / max(self._collection_count, 1)) * 100

        return {
            "name": self.name,
            "subsystem": self.get_subsystem_name(),
            "collection_count": self._collection_count,
            "success_count": self._success_count,
            "success_rate": success_rate,
            "timeout_seconds": self.timeout_seconds,
            "last_error": self._last_error,
            "monitored_services": self.get_service_names(),
        }

    def is_healthy(self) -> bool:
        """
        Check if this collector is operating normally.

        Returns:
            True if collector has no recent errors
        """
        return self._last_error is None

    def reset_stats(self) -> None:
        """Reset collector statistics."""
        self._collection_count = 0
        self._success_count = 0
        self._last_error = None

    def __repr__(self) -> str:
        """String representation of the collector."""
        return f"<{self.__class__.__name__}(name='{self.name}', subsystem='{self.get_subsystem_name()}')>"
