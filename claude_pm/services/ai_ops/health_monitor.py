"""
Health Monitor for AI Operations

Provides comprehensive health monitoring for AI services, providers,
and operations with real-time metrics and alerting capabilities.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Health metric definition."""

    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    unit: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def status(self) -> HealthStatus:
        """Get health status based on thresholds."""
        if self.value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.value >= self.threshold_warning:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


@dataclass
class Alert:
    """Health alert definition."""

    id: str
    severity: AlertSeverity
    message: str
    component: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """
    Comprehensive health monitor for AI operations.

    Monitors providers, services, and operations with real-time metrics,
    alerting, and health status reporting.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize health monitor.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Health tracking
        self.component_health: Dict[str, HealthStatus] = {}
        self.metrics: Dict[str, HealthMetric] = {}
        self.alerts: Dict[str, Alert] = {}
        self.health_history: List[Dict[str, Any]] = []

        # Monitoring configuration
        self.monitoring_interval = self.config.get("monitoring_interval", 60)
        self.alert_retention_days = self.config.get("alert_retention_days", 30)
        self.metrics_retention_hours = self.config.get("metrics_retention_hours", 24)

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

        # Monitoring state
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.start_time = datetime.now()

        # Component categories
        self.component_categories = {
            "providers": ["openai", "anthropic", "google", "openrouter", "vercel"],
            "services": [
                "ai_service_manager",
                "cost_manager",
                "tools_manager",
                "security_framework",
            ],
            "infrastructure": ["circuit_breakers", "authentication", "storage"],
        }

        self.logger.info("Health monitor initialized")

    def add_alert_callback(self, callback: Callable):
        """
        Add callback for alert notifications.

        Args:
            callback: Callback function for alerts
        """
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable):
        """
        Remove alert callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """Stop continuous health monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Health monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _perform_health_check(self):
        """Perform comprehensive health check."""
        # Check all components
        for category, components in self.component_categories.items():
            for component in components:
                try:
                    await self._check_component_health(component)
                except Exception as e:
                    self.logger.error(f"Health check failed for {component}: {e}")
                    await self._create_alert(
                        severity=AlertSeverity.ERROR,
                        message=f"Health check failed for {component}: {str(e)}",
                        component=component,
                    )

        # Update overall health
        await self._update_overall_health()

        # Clean up old data
        await self._cleanup_old_data()

    async def _check_component_health(self, component: str):
        """Check health of specific component."""
        # This would be implemented to check specific components
        # For now, we'll simulate health checks

        # Simulate some health metrics
        if component in ["openai", "anthropic", "google"]:
            # Provider health check
            response_time = await self._check_provider_response_time(component)
            success_rate = await self._check_provider_success_rate(component)

            # Update metrics
            self.metrics[f"{component}_response_time"] = HealthMetric(
                name=f"{component}_response_time",
                value=response_time,
                threshold_warning=5.0,
                threshold_critical=10.0,
                unit="seconds",
                description=f"Average response time for {component}",
            )

            self.metrics[f"{component}_success_rate"] = HealthMetric(
                name=f"{component}_success_rate",
                value=success_rate,
                threshold_warning=0.95,
                threshold_critical=0.90,
                unit="%",
                description=f"Success rate for {component}",
            )

            # Determine component health
            if response_time > 10.0 or success_rate < 0.90:
                self.component_health[component] = HealthStatus.CRITICAL
            elif response_time > 5.0 or success_rate < 0.95:
                self.component_health[component] = HealthStatus.DEGRADED
            else:
                self.component_health[component] = HealthStatus.HEALTHY

        elif component in ["ai_service_manager", "cost_manager"]:
            # Service health check
            memory_usage = await self._check_service_memory_usage(component)
            cpu_usage = await self._check_service_cpu_usage(component)

            # Update metrics
            self.metrics[f"{component}_memory_usage"] = HealthMetric(
                name=f"{component}_memory_usage",
                value=memory_usage,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit="%",
                description=f"Memory usage for {component}",
            )

            self.metrics[f"{component}_cpu_usage"] = HealthMetric(
                name=f"{component}_cpu_usage",
                value=cpu_usage,
                threshold_warning=70.0,
                threshold_critical=90.0,
                unit="%",
                description=f"CPU usage for {component}",
            )

            # Determine component health
            if memory_usage > 95.0 or cpu_usage > 90.0:
                self.component_health[component] = HealthStatus.CRITICAL
            elif memory_usage > 80.0 or cpu_usage > 70.0:
                self.component_health[component] = HealthStatus.DEGRADED
            else:
                self.component_health[component] = HealthStatus.HEALTHY

        else:
            # Default health check
            self.component_health[component] = HealthStatus.HEALTHY

    async def _check_provider_response_time(self, provider: str) -> float:
        """Check provider response time."""
        # This would make actual API calls to check response time
        # For now, simulate with random values
        import random

        return random.uniform(0.5, 8.0)

    async def _check_provider_success_rate(self, provider: str) -> float:
        """Check provider success rate."""
        # This would calculate actual success rate from metrics
        # For now, simulate with random values
        import random

        return random.uniform(0.85, 1.0)

    async def _check_service_memory_usage(self, service: str) -> float:
        """Check service memory usage."""
        # This would check actual memory usage
        # For now, simulate with random values
        import random

        return random.uniform(30.0, 85.0)

    async def _check_service_cpu_usage(self, service: str) -> float:
        """Check service CPU usage."""
        # This would check actual CPU usage
        # For now, simulate with random values
        import random

        return random.uniform(10.0, 75.0)

    async def _update_overall_health(self):
        """Update overall system health."""
        if not self.component_health:
            return

        # Count components by health status
        status_counts = {}
        for status in HealthStatus:
            status_counts[status] = sum(1 for s in self.component_health.values() if s == status)

        # Determine overall health
        total_components = len(self.component_health)
        critical_count = status_counts.get(HealthStatus.CRITICAL, 0)
        unhealthy_count = status_counts.get(HealthStatus.UNHEALTHY, 0)
        degraded_count = status_counts.get(HealthStatus.DEGRADED, 0)

        if critical_count > 0:
            overall_health = HealthStatus.CRITICAL
        elif unhealthy_count > total_components * 0.5:
            overall_health = HealthStatus.UNHEALTHY
        elif degraded_count > total_components * 0.3:
            overall_health = HealthStatus.DEGRADED
        else:
            overall_health = HealthStatus.HEALTHY

        # Update overall health
        self.component_health["overall"] = overall_health

        # Record health history
        self.health_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "overall_health": overall_health.value,
                "component_health": {k: v.value for k, v in self.component_health.items()},
                "metrics_count": len(self.metrics),
                "alerts_count": len([a for a in self.alerts.values() if not a.resolved]),
            }
        )

        # Limit history size
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-1000:]

    async def _create_alert(
        self,
        severity: AlertSeverity,
        message: str,
        component: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create new alert."""
        alert_id = f"{component}_{int(time.time() * 1000)}"

        alert = Alert(
            id=alert_id,
            severity=severity,
            message=message,
            component=component,
            metadata=metadata or {},
        )

        self.alerts[alert_id] = alert

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")

        self.logger.warning(f"Alert created: {severity.value} - {message}")

    async def _cleanup_old_data(self):
        """Clean up old alerts and metrics."""
        current_time = datetime.now()

        # Clean up old alerts
        alert_cutoff = current_time - timedelta(days=self.alert_retention_days)
        alerts_to_remove = [
            alert_id
            for alert_id, alert in self.alerts.items()
            if alert.timestamp < alert_cutoff and alert.resolved
        ]

        for alert_id in alerts_to_remove:
            del self.alerts[alert_id]

        # Clean up old metrics
        metrics_cutoff = current_time - timedelta(hours=self.metrics_retention_hours)
        metrics_to_remove = [
            metric_name
            for metric_name, metric in self.metrics.items()
            if metric.timestamp < metrics_cutoff
        ]

        for metric_name in metrics_to_remove:
            del self.metrics[metric_name]

    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": self.component_health.get("overall", HealthStatus.UNKNOWN).value,
            "component_health": {k: v.value for k, v in self.component_health.items()},
            "total_components": len(self.component_health) - 1,  # Exclude overall
            "active_alerts": len([a for a in self.alerts.values() if not a.resolved]),
            "metrics_count": len(self.metrics),
            "monitoring_active": self.is_monitoring,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                name: {
                    "value": metric.value,
                    "status": metric.status.value,
                    "threshold_warning": metric.threshold_warning,
                    "threshold_critical": metric.threshold_critical,
                    "unit": metric.unit,
                    "description": metric.description,
                    "timestamp": metric.timestamp.isoformat(),
                }
                for name, metric in self.metrics.items()
            },
        }

    async def get_alerts(self, active_only: bool = True) -> Dict[str, Any]:
        """Get alerts."""
        alerts = self.alerts.values()

        if active_only:
            alerts = [a for a in alerts if not a.resolved]

        return {
            "timestamp": datetime.now().isoformat(),
            "alerts": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "component": alert.component,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "metadata": alert.metadata,
                }
                for alert in alerts
            ],
        }

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()

            self.logger.info(f"Alert resolved: {alert_id}")
            return True

        return False

    async def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_history = [
            entry
            for entry in self.health_history
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time
        ]

        return filtered_history

    def health_check(self) -> Dict[str, Any]:
        """Perform immediate health check."""
        return {
            "healthy": self.component_health.get("overall", HealthStatus.UNKNOWN)
            in [HealthStatus.HEALTHY, HealthStatus.DEGRADED],
            "monitoring_active": self.is_monitoring,
            "total_components": len(self.component_health),
            "active_alerts": len([a for a in self.alerts.values() if not a.resolved]),
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "monitoring_active": self.is_monitoring,
            "health_checks_performed": len(self.health_history),
            "alerts_created": len(self.alerts),
            "metrics_tracked": len(self.metrics),
            "alert_callbacks_registered": len(self.alert_callbacks),
        }

    def __str__(self) -> str:
        """String representation."""
        return f"HealthMonitor(components={len(self.component_health)}, alerts={len(self.alerts)})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"<HealthMonitor monitoring={self.is_monitoring} components={len(self.component_health)}>"
