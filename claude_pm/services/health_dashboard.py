"""
Health Dashboard Orchestrator for Claude PM Framework.

Provides comprehensive health monitoring across all subsystems with parallel execution,
circuit breaker pattern for fault tolerance, caching for performance, and rich analytics.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ..interfaces.health import HealthCollector
from ..models.health import (
    HealthReport,
    HealthDashboard,
    ServiceHealthReport,
    SubsystemHealth,
    HealthStatus,
    create_health_report,
    create_health_dashboard,
)
from ..utils.performance import CircuitBreaker, HealthCache, CircuitBreakerOpenError
from ..adapters.health_adapter import HealthMonitorServiceAdapter


class HealthDashboardOrchestrator:
    """
    Orchestrates comprehensive health monitoring across all Claude PM subsystems.

    Features:
    - Parallel health collection from multiple collectors
    - Circuit breaker pattern for fault tolerance
    - Intelligent caching with 60-second TTL
    - Sub-3-second response time target
    - Rich dashboard analytics and trends
    - Backward compatibility with existing HealthMonitorService
    """

    def __init__(
        self,
        cache_ttl_seconds: float = 60.0,
        max_parallel_collectors: int = 8,
        global_timeout_seconds: float = 8.0,  # Optimized for <3s total target
        version: str = "3.0.0",
    ):
        """
        Initialize the health dashboard orchestrator.

        Args:
            cache_ttl_seconds: Cache TTL for health reports (default 60s)
            max_parallel_collectors: Maximum parallel collector execution
            global_timeout_seconds: Global timeout for health collection (optimized for <3s total target)
            version: Framework version for reports
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_parallel_collectors = max_parallel_collectors
        self.global_timeout_seconds = global_timeout_seconds
        self.version = version

        # Core components
        self._cache = HealthCache(default_ttl_seconds=cache_ttl_seconds)
        self._collectors: List[HealthCollector] = []
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._logger = logging.getLogger("health_dashboard")

        # Performance tracking
        self._total_requests = 0
        self._cache_hits = 0
        self._successful_collections = 0
        self._failed_collections = 0

        # Initialize default collectors
        self._initialize_default_collectors()

    def _initialize_default_collectors(self) -> None:
        """Initialize default health collectors."""
        # Legacy health monitor adapter
        legacy_adapter = HealthMonitorServiceAdapter(
            timeout_seconds=2.5
        )  # Optimized for sub-3s performance target
        self.add_collector(legacy_adapter)

        # Framework services collector
        from ..collectors.framework_services import FrameworkServicesCollector

        framework_collector = FrameworkServicesCollector(
            timeout_seconds=2.5
        )  # Optimized for sub-3s performance target
        self.add_collector(framework_collector)

        # AI-trackdown tools collector
        from ..collectors.ai_trackdown_collector import AITrackdownHealthCollector

        ai_trackdown_collector = AITrackdownHealthCollector(
            timeout_seconds=2.5
        )  # Optimized for sub-3s performance target
        self.add_collector(ai_trackdown_collector)

    def add_collector(self, collector: HealthCollector) -> None:
        """
        Add a health collector to the orchestrator.

        Args:
            collector: HealthCollector instance to add
        """
        self._collectors.append(collector)

        # Create circuit breaker for this collector
        circuit_breaker = CircuitBreaker(
            name=f"collector_{collector.name}",
            failure_threshold=3,
            failure_rate_threshold=50.0,
            recovery_timeout=30.0,
        )
        self._circuit_breakers[collector.name] = circuit_breaker

        self._logger.info(
            f"Added health collector: {collector.name} ({collector.get_subsystem_name()})"
        )

    def remove_collector(self, collector_name: str) -> bool:
        """
        Remove a health collector by name.

        Args:
            collector_name: Name of collector to remove

        Returns:
            True if collector was found and removed
        """
        for i, collector in enumerate(self._collectors):
            if collector.name == collector_name:
                del self._collectors[i]
                if collector_name in self._circuit_breakers:
                    del self._circuit_breakers[collector_name]
                self._logger.info(f"Removed health collector: {collector_name}")
                return True
        return False

    async def get_health_dashboard(self, force_refresh: bool = False) -> HealthDashboard:
        """
        Get comprehensive health dashboard with caching.

        Args:
            force_refresh: Skip cache and force fresh collection

        Returns:
            HealthDashboard with current health status and analytics
        """
        start_time = time.time()
        self._total_requests += 1

        # Check cache first (unless force refresh)
        cache_key = "health_dashboard"
        if not force_refresh:
            cached_report = self._cache.get(cache_key)
            if cached_report is not None:
                self._cache_hits += 1

                # Create dashboard from cached report
                dashboard = create_health_dashboard(cached_report)
                dashboard.total_response_time_ms = (time.time() - start_time) * 1000

                # Update cache stats
                cache_stats = self._cache.get_stats()
                dashboard.update_cache_stats(
                    hits=cache_stats["hits"],
                    misses=cache_stats["misses"],
                    size=cache_stats["current_size"],
                    ttl_seconds=int(self.cache_ttl_seconds),
                )

                self._logger.debug(
                    f"Health dashboard served from cache ({dashboard.total_response_time_ms:.1f}ms)"
                )
                return dashboard

        # Collect fresh health data
        try:
            health_report = await self._collect_fresh_health()

            # Cache the report
            self._cache.set(cache_key, health_report, self.cache_ttl_seconds)

            # Create dashboard
            dashboard = create_health_dashboard(health_report)
            dashboard.total_response_time_ms = (time.time() - start_time) * 1000

            # Update cache stats
            cache_stats = self._cache.get_stats()
            dashboard.update_cache_stats(
                hits=cache_stats["hits"],
                misses=cache_stats["misses"],
                size=cache_stats["current_size"],
                ttl_seconds=int(self.cache_ttl_seconds),
            )

            # Calculate trends and performance metrics
            dashboard.calculate_trends()
            dashboard.calculate_performance_metrics()

            self._successful_collections += 1
            self._logger.info(
                f"Health dashboard generated ({dashboard.total_response_time_ms:.1f}ms)"
            )

            return dashboard

        except Exception as e:
            self._failed_collections += 1
            self._logger.error(f"Failed to generate health dashboard: {e}")

            # Return error dashboard
            error_report = create_health_report(self.version, (time.time() - start_time) * 1000)
            error_report.overall_status = HealthStatus.ERROR
            error_report.error = str(e)

            return create_health_dashboard(error_report)

    async def _collect_fresh_health(self) -> HealthReport:
        """
        Collect fresh health data from all collectors in parallel.

        Returns:
            Comprehensive HealthReport with data from all collectors
        """
        start_time = time.time()

        # Create health report
        health_report = create_health_report(self.version, 0.0)

        if not self._collectors:
            health_report.overall_status = HealthStatus.UNKNOWN
            health_report.add_recommendation("No health collectors configured")
            health_report.response_time_ms = (time.time() - start_time) * 1000
            return health_report

        # Execute collectors in parallel with circuit breakers
        collector_tasks = []
        for collector in self._collectors:
            task = self._execute_collector_with_circuit_breaker(collector)
            collector_tasks.append((collector, task))

        # Use semaphore to limit parallel execution
        semaphore = asyncio.Semaphore(self.max_parallel_collectors)

        async def limited_execute(collector_task_tuple):
            collector, task = collector_task_tuple
            async with semaphore:
                return collector, await task

        # Execute with global timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    *[limited_execute(ct) for ct in collector_tasks], return_exceptions=True
                ),
                timeout=self.global_timeout_seconds,
            )
        except asyncio.TimeoutError:
            self._logger.warning(
                f"Health collection timed out after {self.global_timeout_seconds}s"
            )
            results = [
                (collector, TimeoutError("Global timeout")) for collector, _ in collector_tasks
            ]

        # Process results
        subsystems = {}
        successful_collectors = 0
        failed_collectors = 0

        for i, result in enumerate(results):
            collector = collector_tasks[i][0]

            if isinstance(result, Exception):
                # Handle collector exception
                self._logger.error(f"Collector {collector.name} failed: {result}")
                failed_collectors += 1

                # Add error reports for all services in this collector
                for service_name in collector.get_service_names():
                    error_report = ServiceHealthReport(
                        name=service_name,
                        status=HealthStatus.ERROR,
                        message=f"Collector failed: {str(result)}",
                        timestamp=datetime.now(),
                        error=str(result),
                    )
                    health_report.add_service(error_report)
            else:
                # Process successful collector result
                collector_instance, service_reports = result

                if isinstance(service_reports, Exception):
                    failed_collectors += 1
                    continue

                successful_collectors += 1

                # Add service reports
                for service_report in service_reports:
                    health_report.add_service(service_report)

                # Group by subsystem
                subsystem_name = collector.get_subsystem_name()
                if subsystem_name not in subsystems:
                    subsystems[subsystem_name] = []
                subsystems[subsystem_name].extend(service_reports)

        # Create subsystem health summaries
        for subsystem_name, services in subsystems.items():
            subsystem_health = self._create_subsystem_health(subsystem_name, services)
            health_report.subsystems[subsystem_name] = subsystem_health

        # Determine overall status
        health_report.overall_status = self._calculate_overall_status(health_report)

        # Add recommendations and alerts
        self._add_recommendations_and_alerts(
            health_report, successful_collectors, failed_collectors
        )

        # Set final response time
        health_report.response_time_ms = (time.time() - start_time) * 1000

        return health_report

    async def _execute_collector_with_circuit_breaker(
        self, collector: HealthCollector
    ) -> List[ServiceHealthReport]:
        """
        Execute a collector with circuit breaker protection.

        Args:
            collector: HealthCollector to execute

        Returns:
            List of ServiceHealthReport objects
        """
        circuit_breaker = self._circuit_breakers[collector.name]

        try:
            return await circuit_breaker.call(collector.collect_with_timeout)
        except CircuitBreakerOpenError:
            self._logger.warning(f"Circuit breaker open for collector {collector.name}")

            # Return degraded reports for all services
            return [
                ServiceHealthReport(
                    name=service_name,
                    status=HealthStatus.DEGRADED,
                    message="Circuit breaker open - collector temporarily unavailable",
                    timestamp=datetime.now(),
                )
                for service_name in collector.get_service_names()
            ]

    def _create_subsystem_health(
        self, name: str, services: List[ServiceHealthReport]
    ) -> SubsystemHealth:
        """Create subsystem health summary from service reports."""
        if not services:
            return SubsystemHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                services=[],
                total_services=0,
                healthy_services=0,
                degraded_services=0,
                unhealthy_services=0,
                down_services=0,
            )

        # Count services by status
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.DOWN: 0,
            HealthStatus.ERROR: 0,
            HealthStatus.UNKNOWN: 0,
        }

        response_times = []
        for service in services:
            status_counts[service.status] += 1
            if service.response_time_ms is not None:
                response_times.append(service.response_time_ms)

        # Calculate subsystem status
        total_services = len(services)
        healthy_services = status_counts[HealthStatus.HEALTHY]
        degraded_services = status_counts[HealthStatus.DEGRADED]
        unhealthy_services = (
            status_counts[HealthStatus.UNHEALTHY] + status_counts[HealthStatus.ERROR]
        )
        down_services = status_counts[HealthStatus.DOWN] + status_counts[HealthStatus.UNKNOWN]

        # Determine overall subsystem status
        if unhealthy_services > 0 or down_services > total_services / 2:
            subsystem_status = HealthStatus.UNHEALTHY
        elif degraded_services > 0 or down_services > 0:
            subsystem_status = HealthStatus.DEGRADED
        elif healthy_services == total_services:
            subsystem_status = HealthStatus.HEALTHY
        else:
            subsystem_status = HealthStatus.UNKNOWN

        return SubsystemHealth(
            name=name,
            status=subsystem_status,
            services=services,
            total_services=total_services,
            healthy_services=healthy_services,
            degraded_services=degraded_services,
            unhealthy_services=unhealthy_services,
            down_services=down_services,
            avg_response_time_ms=(
                sum(response_times) / len(response_times) if response_times else None
            ),
        )

    def _calculate_overall_status(self, health_report: HealthReport) -> HealthStatus:
        """Calculate overall health status from service reports."""
        if health_report.total_services == 0:
            return HealthStatus.UNKNOWN

        health_percentage = health_report.overall_health_percentage

        if health_percentage >= 90:
            return HealthStatus.HEALTHY
        elif health_percentage >= 70:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    def _add_recommendations_and_alerts(
        self, health_report: HealthReport, successful_collectors: int, failed_collectors: int
    ) -> None:
        """Add recommendations and alerts based on health data."""
        # Alert for low health percentage
        if health_report.overall_health_percentage < 50:
            health_report.add_alert(
                "critical",
                f"Overall health {health_report.overall_health_percentage:.1f}% is critically low",
            )
        elif health_report.overall_health_percentage < 70:
            health_report.add_alert(
                "warning",
                f"Overall health {health_report.overall_health_percentage:.1f}% is below target",
            )

        # Alert for failed collectors
        if failed_collectors > 0:
            health_report.add_alert("warning", f"{failed_collectors} health collectors failed")

        # Alert for slow response time - optimized thresholds
        if health_report.response_time_ms > 500:
            health_report.add_alert(
                "performance",
                f"Health collection took {health_report.response_time_ms:.0f}ms (target: <500ms)",
            )
        elif health_report.response_time_ms > 200:
            health_report.add_alert(
                "info",
                f"Health collection response time: {health_report.response_time_ms:.0f}ms (good: <200ms)",
            )

        # Recommendations
        if health_report.unhealthy_services > 0:
            health_report.add_recommendation(
                f"Investigate {health_report.unhealthy_services} unhealthy services"
            )

        if health_report.down_services > 0:
            health_report.add_recommendation(
                f"Restart or fix {health_report.down_services} down services"
            )

        if failed_collectors > successful_collectors:
            health_report.add_recommendation(
                "Review health collector configuration and connectivity"
            )

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator statistics."""
        cache_stats = self._cache.get_stats()

        # Circuit breaker stats
        circuit_breaker_stats = {}
        for name, cb in self._circuit_breakers.items():
            circuit_breaker_stats[name] = cb.get_status()

        # Collector stats
        collector_stats = {}
        for collector in self._collectors:
            collector_stats[collector.name] = collector.get_collector_stats()

        return {
            "orchestrator": {
                "total_requests": self._total_requests,
                "cache_hits": self._cache_hits,
                "cache_hit_rate": (self._cache_hits / max(self._total_requests, 1)) * 100,
                "successful_collections": self._successful_collections,
                "failed_collections": self._failed_collections,
                "success_rate": (
                    self._successful_collections
                    / max(self._successful_collections + self._failed_collections, 1)
                )
                * 100,
            },
            "cache": cache_stats,
            "circuit_breakers": circuit_breaker_stats,
            "collectors": collector_stats,
            "config": {
                "cache_ttl_seconds": self.cache_ttl_seconds,
                "max_parallel_collectors": self.max_parallel_collectors,
                "global_timeout_seconds": self.global_timeout_seconds,
                "version": self.version,
            },
        }

    def clear_cache(self) -> None:
        """Clear the health cache."""
        self._cache.clear()
        self._logger.info("Health dashboard cache cleared")

    def reset_circuit_breakers(self) -> None:
        """Reset all circuit breakers to closed state."""
        for cb in self._circuit_breakers.values():
            cb.reset()
        self._logger.info("All circuit breakers reset")

    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries."""
        return self._cache.cleanup_expired()

    async def cleanup(self) -> None:
        """Cleanup all resources including collector connections."""
        try:
            # Cleanup all collectors
            for collector in self._collectors:
                if hasattr(collector, "cleanup") and callable(getattr(collector, "cleanup")):
                    try:
                        await collector.cleanup()
                        self._logger.debug(f"Cleaned up collector: {collector.name}")
                    except Exception as e:
                        self._logger.warning(f"Error cleaning up collector {collector.name}: {e}")

            # Clear cache
            self._cache.clear()

            # Reset circuit breakers
            for cb in self._circuit_breakers.values():
                cb.reset()

            self._logger.info("Health dashboard cleanup completed")

        except Exception as e:
            self._logger.error(f"Error during health dashboard cleanup: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the orchestrator itself."""
        try:
            # Quick health dashboard generation (should be fast due to caching)
            start_time = time.time()
            dashboard = await self.get_health_dashboard()
            response_time = (time.time() - start_time) * 1000

            # Check if response time is acceptable - optimized target
            performance_ok = response_time < 500  # 500ms target for excellent performance

            # Check cache performance
            cache_stats = self._cache.get_stats()
            cache_ok = cache_stats["hit_rate"] > 50 if cache_stats["total_requests"] > 0 else True

            # Check circuit breaker states
            circuit_breaker_ok = all(
                cb.state.value == "closed" or cb.state.value == "half_open"
                for cb in self._circuit_breakers.values()
            )

            # Check collector health
            collectors_ok = all(collector.is_healthy() for collector in self._collectors)

            overall_ok = performance_ok and cache_ok and circuit_breaker_ok and collectors_ok

            return {
                "status": "healthy" if overall_ok else "degraded",
                "response_time_ms": response_time,
                "performance_ok": performance_ok,
                "cache_ok": cache_ok,
                "circuit_breakers_ok": circuit_breaker_ok,
                "collectors_ok": collectors_ok,
                "dashboard_status": dashboard.overall_status.value,
                "total_services": dashboard.current_report.total_services,
                "healthy_services": dashboard.current_report.healthy_services,
            }

        except Exception as e:
            self._logger.error(f"Orchestrator health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
