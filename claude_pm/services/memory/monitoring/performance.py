"""
Performance Monitoring

This module provides performance monitoring capabilities for memory operations.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import threading


@dataclass
class OperationMetrics:
    """Metrics for a specific operation."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0
    percentiles: Dict[str, float] = field(default_factory=dict)
    recent_times: List[float] = field(default_factory=list)

    def add_measurement(self, duration: float, success: bool = True):
        """Add a measurement to the metrics."""
        self.total_calls += 1
        self.total_time += duration

        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.total_calls

        # Keep recent times for percentile calculations
        self.recent_times.append(duration)
        if len(self.recent_times) > 1000:  # Keep last 1000 measurements
            self.recent_times.pop(0)

        # Calculate percentiles
        if len(self.recent_times) >= 10:
            self._calculate_percentiles()

    def _calculate_percentiles(self):
        """Calculate percentiles from recent measurements."""
        if not self.recent_times:
            return

        sorted_times = sorted(self.recent_times)
        n = len(sorted_times)

        self.percentiles = {
            "p50": sorted_times[int(n * 0.5)],
            "p75": sorted_times[int(n * 0.75)],
            "p90": sorted_times[int(n * 0.9)],
            "p95": sorted_times[int(n * 0.95)],
            "p99": sorted_times[int(n * 0.99)],
        }

    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100


class PerformanceMonitor:
    """
    Performance monitoring for memory operations.

    This class tracks operation metrics including response times, success rates,
    and throughput for different backends and operations.
    """

    def __init__(self, retention_seconds: int = 86400):
        """
        Initialize performance monitor.

        Args:
            retention_seconds: How long to retain metrics data
        """
        self.retention_seconds = retention_seconds
        self.metrics: Dict[str, Dict[str, OperationMetrics]] = defaultdict(
            lambda: defaultdict(OperationMetrics)
        )
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Global metrics
        self.global_metrics = {
            "total_operations": 0,
            "total_time": 0.0,
            "backend_switches": 0,
            "circuit_breaker_opens": 0,
            "fallback_activations": 0,
            "start_time": time.time(),
        }

        # Performance alerts
        self.alert_thresholds = {
            "slow_operation_threshold": 5.0,  # seconds
            "high_error_rate_threshold": 0.1,  # 10%
            "low_throughput_threshold": 1.0,  # operations per second
        }

        self.alerts: List[Dict[str, Any]] = []

    def measure_operation(self, operation: str, backend: str):
        """
        Context manager for measuring operations.

        Args:
            operation: Operation name
            backend: Backend name

        Returns:
            OperationMeasurement: Context manager for measurement
        """
        return OperationMeasurement(self, operation, backend)

    def record_operation(self, operation: str, backend: str, duration: float, success: bool = True):
        """
        Record an operation measurement.

        Args:
            operation: Operation name
            backend: Backend name
            duration: Operation duration in seconds
            success: Whether the operation was successful
        """
        with self.lock:
            self.metrics[backend][operation].add_measurement(duration, success)

            # Update global metrics
            self.global_metrics["total_operations"] += 1
            self.global_metrics["total_time"] += duration

            # Check for alerts
            self._check_alerts(operation, backend, duration, success)

    def _check_alerts(self, operation: str, backend: str, duration: float, success: bool):
        """Check if any alert conditions are met."""
        current_time = time.time()

        # Check for slow operations
        if duration > self.alert_thresholds["slow_operation_threshold"]:
            self.alerts.append(
                {
                    "type": "slow_operation",
                    "operation": operation,
                    "backend": backend,
                    "duration": duration,
                    "threshold": self.alert_thresholds["slow_operation_threshold"],
                    "timestamp": current_time,
                }
            )

        # Check error rate
        metrics = self.metrics[backend][operation]
        if metrics.total_calls >= 10:  # Only check after some operations
            error_rate = metrics.failed_calls / metrics.total_calls
            if error_rate > self.alert_thresholds["high_error_rate_threshold"]:
                self.alerts.append(
                    {
                        "type": "high_error_rate",
                        "operation": operation,
                        "backend": backend,
                        "error_rate": error_rate,
                        "threshold": self.alert_thresholds["high_error_rate_threshold"],
                        "timestamp": current_time,
                    }
                )

        # Keep only recent alerts
        self.alerts = [
            alert
            for alert in self.alerts
            if current_time - alert["timestamp"] < 3600  # Keep alerts for 1 hour
        ]

    def get_metrics(self, backend: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current metrics.

        Args:
            backend: Specific backend to get metrics for (optional)

        Returns:
            Dict[str, Any]: Metrics data
        """
        with self.lock:
            if backend:
                return self._get_backend_metrics(backend)
            else:
                return self._get_all_metrics()

    def _get_backend_metrics(self, backend: str) -> Dict[str, Any]:
        """Get metrics for a specific backend."""
        if backend not in self.metrics:
            return {"backend": backend, "operations": {}}

        operations = {}
        for op, metrics in self.metrics[backend].items():
            operations[op] = {
                "total_calls": metrics.total_calls,
                "success_rate": metrics.get_success_rate(),
                "avg_response_time": metrics.avg_time,
                "min_response_time": metrics.min_time if metrics.min_time != float("inf") else 0,
                "max_response_time": metrics.max_time,
                "percentiles": metrics.percentiles,
                "successful_calls": metrics.successful_calls,
                "failed_calls": metrics.failed_calls,
            }

        return {"backend": backend, "operations": operations}

    def _get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all backends."""
        all_metrics = {}

        for backend_name, backend_metrics in self.metrics.items():
            all_metrics[backend_name] = self._get_backend_metrics(backend_name)

        return all_metrics

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all backends."""
        with self.lock:
            summary = {
                "global_metrics": self.global_metrics.copy(),
                "total_backends": len(self.metrics),
                "backend_performance": {},
                "fastest_backend": None,
                "most_reliable_backend": None,
                "slowest_operation": None,
                "uptime": time.time() - self.global_metrics["start_time"],
            }

            backend_speeds = {}
            backend_reliability = {}
            slowest_op = None
            slowest_time = 0

            for backend, operations in self.metrics.items():
                total_calls = sum(op.total_calls for op in operations.values())
                successful_calls = sum(op.successful_calls for op in operations.values())
                total_time = sum(op.total_time for op in operations.values())

                if total_calls > 0:
                    avg_time = total_time / total_calls
                    success_rate = (successful_calls / total_calls) * 100

                    backend_speeds[backend] = avg_time
                    backend_reliability[backend] = success_rate

                    summary["backend_performance"][backend] = {
                        "total_calls": total_calls,
                        "success_rate": success_rate,
                        "avg_response_time": avg_time,
                        "throughput": (
                            total_calls / summary["uptime"] if summary["uptime"] > 0 else 0
                        ),
                    }

                    # Find slowest operation
                    for op_name, op_metrics in operations.items():
                        if op_metrics.max_time > slowest_time:
                            slowest_time = op_metrics.max_time
                            slowest_op = {
                                "operation": op_name,
                                "backend": backend,
                                "max_time": op_metrics.max_time,
                                "avg_time": op_metrics.avg_time,
                            }

            # Determine fastest and most reliable backends
            if backend_speeds:
                summary["fastest_backend"] = min(backend_speeds, key=backend_speeds.get)

            if backend_reliability:
                summary["most_reliable_backend"] = max(
                    backend_reliability, key=backend_reliability.get
                )

            if slowest_op:
                summary["slowest_operation"] = slowest_op

            return summary

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts."""
        with self.lock:
            return self.alerts.copy()

    def clear_alerts(self):
        """Clear all alerts."""
        with self.lock:
            self.alerts.clear()

    def set_alert_threshold(self, threshold_name: str, value: float):
        """Set alert threshold."""
        if threshold_name in self.alert_thresholds:
            self.alert_thresholds[threshold_name] = value
            self.logger.info(f"Set alert threshold {threshold_name} to {value}")

    def get_throughput_stats(self) -> Dict[str, Any]:
        """Get throughput statistics."""
        with self.lock:
            uptime = time.time() - self.global_metrics["start_time"]

            if uptime <= 0:
                return {"error": "No uptime data available"}

            total_ops = self.global_metrics["total_operations"]
            overall_throughput = total_ops / uptime

            backend_throughput = {}
            for backend, operations in self.metrics.items():
                backend_ops = sum(op.total_calls for op in operations.values())
                backend_throughput[backend] = backend_ops / uptime

            return {
                "uptime_seconds": uptime,
                "total_operations": total_ops,
                "overall_throughput": overall_throughput,
                "backend_throughput": backend_throughput,
            }

    def get_response_time_distribution(self, backend: str, operation: str) -> Dict[str, Any]:
        """Get response time distribution for a specific operation."""
        with self.lock:
            if backend not in self.metrics or operation not in self.metrics[backend]:
                return {"error": "Operation not found"}

            metrics = self.metrics[backend][operation]

            return {
                "operation": operation,
                "backend": backend,
                "total_calls": metrics.total_calls,
                "min_time": metrics.min_time if metrics.min_time != float("inf") else 0,
                "max_time": metrics.max_time,
                "avg_time": metrics.avg_time,
                "percentiles": metrics.percentiles,
                "recent_samples": len(metrics.recent_times),
            }

    def reset_metrics(self):
        """Reset all metrics."""
        with self.lock:
            self.metrics.clear()
            self.global_metrics = {
                "total_operations": 0,
                "total_time": 0.0,
                "backend_switches": 0,
                "circuit_breaker_opens": 0,
                "fallback_activations": 0,
                "start_time": time.time(),
            }
            self.alerts.clear()

        self.logger.info("Reset all performance metrics")

    def record_backend_switch(self):
        """Record a backend switch event."""
        with self.lock:
            self.global_metrics["backend_switches"] += 1

    def record_circuit_breaker_open(self):
        """Record a circuit breaker opening event."""
        with self.lock:
            self.global_metrics["circuit_breaker_opens"] += 1

    def record_fallback_activation(self):
        """Record a fallback activation event."""
        with self.lock:
            self.global_metrics["fallback_activations"] += 1

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        with self.lock:
            metrics_data = {
                "timestamp": time.time(),
                "global_metrics": self.global_metrics,
                "backend_metrics": self._get_all_metrics(),
                "performance_summary": self.get_performance_summary(),
                "alerts": self.alerts,
            }

            if format.lower() == "json":
                import json

                return json.dumps(metrics_data, indent=2, default=str)
            else:
                return str(metrics_data)

    def __repr__(self) -> str:
        """String representation."""
        with self.lock:
            return (
                f"PerformanceMonitor(backends={len(self.metrics)}, "
                f"total_operations={self.global_metrics['total_operations']}, "
                f"alerts={len(self.alerts)})"
            )


class OperationMeasurement:
    """Context manager for measuring operation performance."""

    def __init__(self, monitor: PerformanceMonitor, operation: str, backend: str):
        """
        Initialize operation measurement.

        Args:
            monitor: Performance monitor instance
            operation: Operation name
            backend: Backend name
        """
        self.monitor = monitor
        self.operation = operation
        self.backend = backend
        self.start_time = 0
        self.success = True

    def __enter__(self):
        """Enter context manager."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        duration = time.time() - self.start_time
        success = exc_type is None
        self.monitor.record_operation(self.operation, self.backend, duration, success)

    def mark_failure(self):
        """Mark the operation as failed."""
        self.success = False
