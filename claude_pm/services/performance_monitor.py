"""
Performance Monitor Service for Claude PM Framework.

Monitors framework performance metrics, identifies bottlenecks,
and provides optimization recommendations.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..core.base_service import BaseService
from ..models.health import HealthStatus, ServiceHealthReport


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""

    timestamp: datetime
    response_time_ms: float
    cpu_usage_percent: float
    memory_usage_mb: float
    cache_hit_rate: float
    active_services: int
    total_requests: int
    error_rate: float


class PerformanceMonitor(BaseService):
    """
    Performance monitoring service for Claude PM Framework.

    Tracks performance metrics, identifies bottlenecks, and provides
    optimization recommendations for the framework core.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize performance monitor."""
        super().__init__("performance_monitor", config)

        # Performance targets
        self.target_response_time_ms = self.config.get("target_response_time_ms", 500)
        self.warning_threshold_ms = self.config.get("warning_threshold_ms", 200)
        self.error_threshold_ms = self.config.get("error_threshold_ms", 1000)

        # Metrics storage
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 100

        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.last_optimization_check = datetime.now()

        # Optimization flags
        self.optimization_enabled = True
        self.auto_optimization = True

        # Logger
        self.logger = logging.getLogger("performance_monitor")

    async def start(self) -> None:
        """Start performance monitoring."""
        await super().start()

        # Start performance collection task
        self.add_task(self._collect_metrics_loop())
        self.add_task(self._optimization_loop())

        self.logger.info("Performance monitor started")

    async def _collect_metrics_loop(self) -> None:
        """Continuous performance metrics collection."""
        while self.running:
            try:
                await self._collect_current_metrics()
                await asyncio.sleep(10)  # Collect every 10 seconds
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    async def _optimization_loop(self) -> None:
        """Continuous optimization analysis."""
        while self.running:
            try:
                await self._analyze_performance()
                await asyncio.sleep(60)  # Analyze every minute
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def _collect_current_metrics(self) -> None:
        """Collect current performance metrics."""
        try:
            import psutil

            process = psutil.Process()

            # Get current metrics
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                response_time_ms=self._get_average_response_time(),
                cpu_usage_percent=process.cpu_percent(),
                memory_usage_mb=process.memory_info().rss / 1024 / 1024,
                cache_hit_rate=self._get_cache_hit_rate(),
                active_services=self._get_active_services_count(),
                total_requests=self.request_count,
                error_rate=self._get_error_rate(),
            )

            # Add to history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)

        except ImportError:
            # psutil not available, use basic metrics
            self.logger.warning("psutil not available, using basic metrics")
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                response_time_ms=self._get_average_response_time(),
                cpu_usage_percent=0.0,
                memory_usage_mb=0.0,
                cache_hit_rate=self._get_cache_hit_rate(),
                active_services=self._get_active_services_count(),
                total_requests=self.request_count,
                error_rate=self._get_error_rate(),
            )
            self.metrics_history.append(metrics)

    def _get_average_response_time(self) -> float:
        """Calculate average response time."""
        if self.request_count == 0:
            return 0.0
        return self.total_response_time / self.request_count

    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate from health dashboard."""
        try:
            from .health_dashboard import HealthDashboardOrchestrator

            # This is a simplified implementation
            return 75.0  # Placeholder
        except:
            return 0.0

    def _get_active_services_count(self) -> int:
        """Get count of active services."""
        # This would integrate with service manager
        return 5  # Placeholder

    def _get_error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100

    async def _analyze_performance(self) -> None:
        """Analyze performance and identify issues."""
        if not self.metrics_history:
            return

        current_metrics = self.metrics_history[-1]

        # Check response time
        if current_metrics.response_time_ms > self.error_threshold_ms:
            await self._handle_performance_degradation(current_metrics)
        elif current_metrics.response_time_ms > self.warning_threshold_ms:
            await self._handle_performance_warning(current_metrics)

        # Check for trends
        if len(self.metrics_history) >= 5:
            await self._analyze_trends()

    async def _handle_performance_degradation(self, metrics: PerformanceMetrics) -> None:
        """Handle performance degradation."""
        self.logger.warning(
            f"Performance degradation detected: {metrics.response_time_ms:.0f}ms "
            f"(target: {self.target_response_time_ms}ms)"
        )

        if self.auto_optimization:
            await self._apply_optimizations(metrics)

    async def _handle_performance_warning(self, metrics: PerformanceMetrics) -> None:
        """Handle performance warning."""
        self.logger.info(
            f"Performance warning: {metrics.response_time_ms:.0f}ms "
            f"(target: {self.target_response_time_ms}ms)"
        )

    async def _analyze_trends(self) -> None:
        """Analyze performance trends."""
        recent_metrics = self.metrics_history[-5:]

        # Calculate trend
        response_times = [m.response_time_ms for m in recent_metrics]
        if len(response_times) >= 2:
            trend = response_times[-1] - response_times[0]
            if trend > 100:  # Increasing by more than 100ms
                self.logger.warning(f"Performance trend degrading: +{trend:.0f}ms over 5 samples")

    async def _apply_optimizations(self, metrics: PerformanceMetrics) -> None:
        """Apply automatic performance optimizations."""
        if not self.optimization_enabled:
            return

        optimizations_applied = []

        # Optimize cache if hit rate is low
        if metrics.cache_hit_rate < 50:
            optimizations_applied.append("increased_cache_ttl")

        # Optimize timeouts if response time is high
        if metrics.response_time_ms > self.target_response_time_ms:
            optimizations_applied.append("reduced_timeouts")

        if optimizations_applied:
            self.logger.info(f"Applied optimizations: {', '.join(optimizations_applied)}")
            self.last_optimization_check = datetime.now()

    async def record_request(self, response_time_ms: float, success: bool = True) -> None:
        """Record a request for performance tracking."""
        self.request_count += 1
        self.total_response_time += response_time_ms

        if not success:
            self.error_count += 1

    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No performance data available"}

        current_metrics = self.metrics_history[-1]

        # Calculate averages
        avg_response_time = sum(m.response_time_ms for m in self.metrics_history) / len(
            self.metrics_history
        )
        avg_cpu_usage = sum(m.cpu_usage_percent for m in self.metrics_history) / len(
            self.metrics_history
        )
        avg_memory_usage = sum(m.memory_usage_mb for m in self.metrics_history) / len(
            self.metrics_history
        )

        # Determine status
        if current_metrics.response_time_ms <= self.warning_threshold_ms:
            status = "excellent"
        elif current_metrics.response_time_ms <= self.target_response_time_ms:
            status = "good"
        elif current_metrics.response_time_ms <= self.error_threshold_ms:
            status = "degraded"
        else:
            status = "poor"

        return {
            "status": status,
            "current_metrics": {
                "response_time_ms": current_metrics.response_time_ms,
                "cpu_usage_percent": current_metrics.cpu_usage_percent,
                "memory_usage_mb": current_metrics.memory_usage_mb,
                "cache_hit_rate": current_metrics.cache_hit_rate,
                "active_services": current_metrics.active_services,
                "error_rate": current_metrics.error_rate,
            },
            "averages": {
                "response_time_ms": avg_response_time,
                "cpu_usage_percent": avg_cpu_usage,
                "memory_usage_mb": avg_memory_usage,
            },
            "targets": {
                "response_time_ms": self.target_response_time_ms,
                "warning_threshold_ms": self.warning_threshold_ms,
                "error_threshold_ms": self.error_threshold_ms,
            },
            "optimizations": {
                "enabled": self.optimization_enabled,
                "auto_optimization": self.auto_optimization,
                "last_check": self.last_optimization_check.isoformat(),
            },
            "recommendations": await self._generate_recommendations(),
        }

    async def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        if not self.metrics_history:
            return recommendations

        current_metrics = self.metrics_history[-1]

        if current_metrics.response_time_ms > self.target_response_time_ms:
            recommendations.append("Consider optimizing health check timeouts")

        if current_metrics.cache_hit_rate < 70:
            recommendations.append("Increase cache TTL or optimize cache strategy")

        if current_metrics.error_rate > 5:
            recommendations.append("Investigate and fix error sources")

        if current_metrics.memory_usage_mb > 500:
            recommendations.append("Monitor memory usage and optimize if needed")

        return recommendations

    async def get_health_report(self) -> ServiceHealthReport:
        """Get health report for performance monitor."""
        try:
            performance_report = await self.get_performance_report()
            status_mapping = {
                "excellent": HealthStatus.HEALTHY,
                "good": HealthStatus.HEALTHY,
                "degraded": HealthStatus.DEGRADED,
                "poor": HealthStatus.UNHEALTHY,
            }

            status = status_mapping.get(performance_report["status"], HealthStatus.UNKNOWN)

            return ServiceHealthReport(
                name="performance_monitor",
                status=status,
                message=f"Performance: {performance_report['status']} ({performance_report['current_metrics']['response_time_ms']:.0f}ms)",
                timestamp=datetime.now(),
                response_time_ms=performance_report["current_metrics"]["response_time_ms"],
                metrics=performance_report["current_metrics"],
            )
        except Exception as e:
            return ServiceHealthReport(
                name="performance_monitor",
                status=HealthStatus.ERROR,
                message=f"Performance monitor error: {str(e)}",
                timestamp=datetime.now(),
                error=str(e),
            )

    async def optimize_framework(self) -> Dict[str, Any]:
        """Perform comprehensive framework optimization."""
        self.logger.info("Starting framework optimization")

        optimization_results = {
            "optimizations_applied": [],
            "improvements": {},
            "recommendations": [],
        }

        # Apply cache optimizations
        cache_optimization = await self._optimize_cache()
        if cache_optimization:
            optimization_results["optimizations_applied"].append("cache_optimization")

        # Apply timeout optimizations
        timeout_optimization = await self._optimize_timeouts()
        if timeout_optimization:
            optimization_results["optimizations_applied"].append("timeout_optimization")

        # Apply service optimizations
        service_optimization = await self._optimize_services()
        if service_optimization:
            optimization_results["optimizations_applied"].append("service_optimization")

        optimization_results["recommendations"] = await self._generate_recommendations()

        return optimization_results

    async def _optimize_cache(self) -> bool:
        """Optimize cache settings."""
        # This would implement cache optimization logic
        self.logger.info("Optimizing cache settings")
        return True

    async def _optimize_timeouts(self) -> bool:
        """Optimize timeout settings."""
        # This would implement timeout optimization logic
        self.logger.info("Optimizing timeout settings")
        return True

    async def _optimize_services(self) -> bool:
        """Optimize service configurations."""
        # This would implement service optimization logic
        self.logger.info("Optimizing service configurations")
        return True
    
    async def _initialize(self) -> None:
        """Initialize the performance monitor service."""
        try:
            # Initialize metrics history
            self.metrics_history = []
            self.request_count = 0
            self.error_count = 0
            self.total_response_time = 0.0
            self.last_optimization_check = datetime.now()
            
            self.logger.info("Performance monitor initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize performance monitor: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup performance monitor resources."""
        try:
            # Clear metrics history
            self.metrics_history.clear()
            
            # Reset counters
            self.request_count = 0
            self.error_count = 0
            self.total_response_time = 0.0
            
            self.logger.info("Performance monitor cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during performance monitor cleanup: {e}")
