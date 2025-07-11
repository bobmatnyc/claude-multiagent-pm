"""
Health Data Models for Claude PM Framework.

Provides comprehensive data models for health monitoring across all subsystems.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DOWN = "down"
    ERROR = "error"


@dataclass
class ServiceHealthReport:
    """Health report for a single service/subsystem."""

    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time_ms: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, bool] = field(default_factory=dict)
    error: Optional[str] = None
    last_error: Optional[str] = None
    uptime_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms,
            "metrics": self.metrics,
            "checks": self.checks,
            "error": self.error,
            "last_error": self.last_error,
            "uptime_seconds": self.uptime_seconds,
        }


@dataclass
class SubsystemHealth:
    """Health information for a subsystem category."""

    name: str
    status: HealthStatus
    services: List[ServiceHealthReport]
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    down_services: int
    avg_response_time_ms: Optional[float] = None

    @property
    def health_percentage(self) -> float:
        """Calculate health percentage for this subsystem."""
        if self.total_services == 0:
            return 0.0
        return (self.healthy_services / self.total_services) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "status": self.status.value,
            "total_services": self.total_services,
            "healthy_services": self.healthy_services,
            "degraded_services": self.degraded_services,
            "unhealthy_services": self.unhealthy_services,
            "down_services": self.down_services,
            "health_percentage": self.health_percentage,
            "avg_response_time_ms": self.avg_response_time_ms,
            "services": [service.to_dict() for service in self.services],
        }


@dataclass
class HealthReport:
    """Comprehensive health report for a single collection cycle."""

    timestamp: datetime
    version: str
    overall_status: HealthStatus
    response_time_ms: float
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    down_services: int
    services: List[ServiceHealthReport] = field(default_factory=list)
    subsystems: Dict[str, SubsystemHealth] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def overall_health_percentage(self) -> float:
        """Calculate overall health percentage."""
        if self.total_services == 0:
            return 0.0
        return (self.healthy_services / self.total_services) * 100

    @property
    def is_cache_hit(self) -> bool:
        """Check if this was served from cache (response time < 100ms)."""
        return self.response_time_ms < 100

    def add_service(self, service: ServiceHealthReport) -> None:
        """Add a service health report."""
        self.services.append(service)
        self.total_services += 1

        if service.status == HealthStatus.HEALTHY:
            self.healthy_services += 1
        elif service.status == HealthStatus.DEGRADED:
            self.degraded_services += 1
        elif service.status in [HealthStatus.UNHEALTHY, HealthStatus.ERROR]:
            self.unhealthy_services += 1
        elif service.status == HealthStatus.DOWN:
            self.down_services += 1

    def add_alert(self, level: str, message: str, data: Any = None) -> None:
        """Add an alert to the report."""
        self.alerts.append(
            {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "data": data,
            }
        )

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation to the report."""
        self.recommendations.append(recommendation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "overall_status": self.overall_status.value,
            "response_time_ms": self.response_time_ms,
            "overall_health_percentage": self.overall_health_percentage,
            "is_cache_hit": self.is_cache_hit,
            "total_services": self.total_services,
            "healthy_services": self.healthy_services,
            "degraded_services": self.degraded_services,
            "unhealthy_services": self.unhealthy_services,
            "down_services": self.down_services,
            "services": [service.to_dict() for service in self.services],
            "subsystems": {name: subsys.to_dict() for name, subsys in self.subsystems.items()},
            "alerts": self.alerts,
            "recommendations": self.recommendations,
            "error": self.error,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class HealthDashboard:
    """Dashboard aggregating multiple health reports with trends and analytics."""

    timestamp: datetime
    current_report: HealthReport
    historical_reports: List[HealthReport] = field(default_factory=list)
    trends: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    cache_stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def overall_status(self) -> HealthStatus:
        """Get overall dashboard status."""
        return self.current_report.overall_status

    @property
    def total_response_time_ms(self) -> float:
        """Get total response time for dashboard generation."""
        return self.current_report.response_time_ms

    @total_response_time_ms.setter
    def total_response_time_ms(self, value: float) -> None:
        """Set total response time for dashboard generation."""
        self.current_report.response_time_ms = value

    def add_historical_report(self, report: HealthReport) -> None:
        """Add a historical report (keep last 10)."""
        self.historical_reports.append(report)
        if len(self.historical_reports) > 10:
            self.historical_reports.pop(0)

    def calculate_trends(self) -> None:
        """Calculate health trends from historical data."""
        if len(self.historical_reports) < 2:
            self.trends = {"status": "insufficient_data"}
            return

        recent_reports = self.historical_reports[-5:]  # Last 5 reports

        # Health percentage trend
        health_percentages = [r.overall_health_percentage for r in recent_reports]
        if len(health_percentages) >= 2:
            trend = (
                "improving"
                if health_percentages[-1] > health_percentages[0]
                else "declining" if health_percentages[-1] < health_percentages[0] else "stable"
            )
        else:
            trend = "stable"

        # Response time trend
        response_times = [r.response_time_ms for r in recent_reports]
        avg_response_time = sum(response_times) / len(response_times)

        # Service availability trend
        service_counts = [(r.healthy_services, r.total_services) for r in recent_reports]
        availability_trend = "stable"  # Simplified for now

        self.trends = {
            "health_trend": trend,
            "avg_response_time_ms": avg_response_time,
            "availability_trend": availability_trend,
            "last_updated": datetime.now().isoformat(),
        }

    def calculate_performance_metrics(self) -> None:
        """Calculate performance metrics."""
        current = self.current_report

        # Cache performance
        cache_hit_rate = 100.0 if current.is_cache_hit else 0.0

        # Service distribution
        service_distribution = {
            "healthy_percentage": (current.healthy_services / max(current.total_services, 1)) * 100,
            "degraded_percentage": (current.degraded_services / max(current.total_services, 1))
            * 100,
            "unhealthy_percentage": (current.unhealthy_services / max(current.total_services, 1))
            * 100,
            "down_percentage": (current.down_services / max(current.total_services, 1)) * 100,
        }

        # Response time analysis
        service_response_times = [
            s.response_time_ms for s in current.services if s.response_time_ms is not None
        ]
        avg_service_response = (
            sum(service_response_times) / len(service_response_times)
            if service_response_times
            else 0
        )

        self.performance_metrics = {
            "cache_hit_rate": cache_hit_rate,
            "avg_service_response_time_ms": avg_service_response,
            "service_distribution": service_distribution,
            "total_alerts": len(current.alerts),
            "total_recommendations": len(current.recommendations),
        }

    def update_cache_stats(self, hits: int, misses: int, size: int, ttl_seconds: int) -> None:
        """Update cache statistics."""
        total_requests = hits + misses
        hit_rate = (hits / max(total_requests, 1)) * 100

        self.cache_stats = {
            "hits": hits,
            "misses": misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": size,
            "ttl_seconds": ttl_seconds,
            "last_updated": datetime.now().isoformat(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "total_response_time_ms": self.total_response_time_ms,
            "current_report": self.current_report.to_dict(),
            "trends": self.trends,
            "performance_metrics": self.performance_metrics,
            "cache_stats": self.cache_stats,
            "historical_count": len(self.historical_reports),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def create_service_health_report(
    name: str,
    status: Union[HealthStatus, str],
    message: str = "",
    response_time_ms: Optional[float] = None,
    **kwargs,
) -> ServiceHealthReport:
    """Factory function to create a ServiceHealthReport."""
    if isinstance(status, str):
        status = HealthStatus(status)

    return ServiceHealthReport(
        name=name,
        status=status,
        message=message,
        timestamp=datetime.now(),
        response_time_ms=response_time_ms,
        **kwargs,
    )


def create_health_report(version: str = "3.0.0", response_time_ms: float = 0.0) -> HealthReport:
    """Factory function to create a HealthReport."""
    return HealthReport(
        timestamp=datetime.now(),
        version=version,
        overall_status=HealthStatus.UNKNOWN,
        response_time_ms=response_time_ms,
        total_services=0,
        healthy_services=0,
        degraded_services=0,
        unhealthy_services=0,
        down_services=0,
    )


def create_health_dashboard(current_report: HealthReport) -> HealthDashboard:
    """Factory function to create a HealthDashboard."""
    dashboard = HealthDashboard(timestamp=datetime.now(), current_report=current_report)
    dashboard.calculate_performance_metrics()
    return dashboard
