"""
Health Monitor Service Adapter for Claude PM Framework.

Provides integration between the new health dashboard system and the existing
HealthMonitorService to maintain backward compatibility.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..interfaces.health import HealthCollector
from ..models.health import ServiceHealthReport, HealthStatus
from ..services.health_monitor import HealthMonitorService


class HealthMonitorServiceAdapter(HealthCollector):
    """
    Adapter that integrates the existing HealthMonitorService into the new health dashboard system.

    This adapter allows the legacy health monitoring system to work seamlessly
    with the new parallel collection and dashboard orchestration.
    """

    def __init__(
        self, health_service: Optional[HealthMonitorService] = None, timeout_seconds: float = 2.0
    ):
        """
        Initialize the health monitor service adapter.

        Args:
            health_service: Optional existing HealthMonitorService instance
            timeout_seconds: Timeout for health collection operations
        """
        super().__init__("health_monitor_service", timeout_seconds)
        self._health_service = health_service
        self._health_report_path = (
            Path.home() / "Projects" / "Claude-PM" / "logs" / "health-report.json"
        )

        # Alternative path for current project structure
        if not self._health_report_path.exists():
            self._health_report_path = (
                Path(__file__).parent.parent.parent / "logs" / "health-report.json"
            )

    async def collect_health(self) -> List[ServiceHealthReport]:
        """
        Collect health information from the existing health monitoring system.

        Returns:
            List of ServiceHealthReport objects from legacy system
        """
        reports = []

        # If we have a health service instance, use it directly
        if self._health_service and self._health_service.running:
            reports.extend(await self._collect_from_service())

        # Always try to read the health report file as fallback/supplement
        reports.extend(await self._collect_from_report_file())

        return reports

    async def _collect_from_service(self) -> List[ServiceHealthReport]:
        """Collect health from the running HealthMonitorService."""
        reports = []

        try:
            # Get health status from the service
            health_status = await self._health_service.get_health_status()

            # Convert to our format
            if health_status:
                service_report = ServiceHealthReport(
                    name="health_monitor_service",
                    status=self._map_health_status(
                        "healthy" if health_status.get("overall_health", 0) > 50 else "unhealthy"
                    ),
                    message=f"Framework health: {health_status.get('overall_health', 0)}%",
                    timestamp=datetime.now(),
                    metrics={
                        "overall_health": health_status.get("overall_health", 0),
                        "total_projects": health_status.get("total_projects", 0),
                        "healthy_projects": health_status.get("healthy_projects", 0),
                        "alerts": health_status.get("alerts", 0),
                        "framework_compliance": health_status.get("framework_compliance", 0),
                    },
                )
                reports.append(service_report)

            # Run an on-demand health check to get fresh data
            fresh_report = await self._health_service.run_health_check()
            if fresh_report and fresh_report.get("status") == "completed":
                service_report = ServiceHealthReport(
                    name="health_check_execution",
                    status=HealthStatus.HEALTHY,
                    message="Health check executed successfully",
                    timestamp=datetime.now(),
                    metrics=fresh_report,
                )
                reports.append(service_report)

        except Exception as e:
            # If service collection fails, create an error report
            error_report = ServiceHealthReport(
                name="health_monitor_service",
                status=HealthStatus.ERROR,
                message=f"Failed to collect from service: {str(e)}",
                timestamp=datetime.now(),
                error=str(e),
            )
            reports.append(error_report)

        return reports

    async def _collect_from_report_file(self) -> List[ServiceHealthReport]:
        """Collect health information from the health report JSON file."""
        reports = []

        try:
            if not self._health_report_path.exists():
                return reports

            # Read the health report file
            with open(self._health_report_path, "r") as f:
                health_data = json.load(f)

            # Parse services section
            services = health_data.get("services", {})
            for service_name, service_data in services.items():
                if isinstance(service_data, dict):
                    status = self._map_health_status(service_data.get("status", "unknown"))

                    service_report = ServiceHealthReport(
                        name=service_name,
                        status=status,
                        message=service_data.get("description", "No description"),
                        timestamp=self._parse_timestamp(
                            service_data.get("last_check", service_data.get("timestamp"))
                        ),
                        response_time_ms=service_data.get("response_time"),
                        metrics={
                            "port": service_data.get("port"),
                            "critical": service_data.get("critical", False),
                            "http_status": service_data.get("http_status"),
                            "performance": service_data.get("performance"),
                        },
                        error=service_data.get("error"),
                        uptime_seconds=None,  # Not available in legacy format
                    )
                    reports.append(service_report)

            # Parse projects section and create aggregate report
            projects = health_data.get("projects", {})
            if projects:
                healthy_projects = sum(1 for p in projects.values() if p.get("status") == "healthy")
                total_projects = len(projects)

                # Improved project health assessment
                health_ratio = healthy_projects / max(total_projects, 1)
                if health_ratio > 0.8:
                    project_status = HealthStatus.HEALTHY
                elif health_ratio > 0.5:
                    project_status = HealthStatus.DEGRADED
                else:
                    project_status = HealthStatus.UNHEALTHY

                project_report = ServiceHealthReport(
                    name="project_health_aggregate",
                    status=project_status,
                    message=f"Project health: {healthy_projects}/{total_projects} healthy ({health_ratio:.1%})",
                    timestamp=self._parse_timestamp(health_data.get("timestamp")),
                    metrics={
                        "total_projects": total_projects,
                        "healthy_projects": healthy_projects,
                        "warning_projects": sum(
                            1 for p in projects.values() if p.get("status") == "warning"
                        ),
                        "critical_projects": sum(
                            1 for p in projects.values() if p.get("status") == "critical"
                        ),
                        "overall_health_percentage": health_data.get("summary", {}).get(
                            "overall_health_percentage", 0
                        ),
                    },
                )
                reports.append(project_report)

            # Parse framework section
            framework = health_data.get("framework", {})
            if framework:
                # Improved framework compliance assessment
                compliance = framework.get("compliance_percentage", 0)
                if compliance > 90:
                    framework_status = HealthStatus.HEALTHY
                elif compliance > 70:
                    framework_status = HealthStatus.DEGRADED
                else:
                    framework_status = HealthStatus.UNHEALTHY

                framework_report = ServiceHealthReport(
                    name="framework_compliance",
                    status=framework_status,
                    message=f"Framework compliance: {compliance}%",
                    timestamp=self._parse_timestamp(framework.get("last_check")),
                    metrics=framework,
                )
                reports.append(framework_report)

        except Exception as e:
            # If file reading fails, create an error report
            error_report = ServiceHealthReport(
                name="health_report_file",
                status=HealthStatus.ERROR,
                message=f"Failed to read health report file: {str(e)}",
                timestamp=datetime.now(),
                error=str(e),
            )
            reports.append(error_report)

        return reports

    def _map_health_status(self, status_str: str) -> HealthStatus:
        """Map legacy health status strings to HealthStatus enum."""
        status_mapping = {
            "healthy": HealthStatus.HEALTHY,
            "degraded": HealthStatus.DEGRADED,
            "unhealthy": HealthStatus.UNHEALTHY,
            "down": HealthStatus.DOWN,
            "error": HealthStatus.ERROR,
            "unknown": HealthStatus.UNKNOWN,
            "warning": HealthStatus.DEGRADED,
            "critical": HealthStatus.UNHEALTHY,
            "fair": HealthStatus.DEGRADED,
            "active": HealthStatus.HEALTHY,
            "moderate": HealthStatus.DEGRADED,
        }
        return status_mapping.get(status_str.lower(), HealthStatus.UNKNOWN)

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return datetime.now()

        try:
            # Try multiple timestamp formats
            for fmt in [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
            ]:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue

            # If all formats fail, return current time
            return datetime.now()

        except Exception:
            return datetime.now()

    def get_subsystem_name(self) -> str:
        """Get the subsystem name for this collector."""
        return "Legacy Health Monitor"

    def get_service_names(self) -> List[str]:
        """Get the list of service names this collector monitors."""
        return [
            "health_monitor_service",
            "health_check_execution",
            "project_health_aggregate",
            "framework_compliance",
            "portfolio_manager",
            "git_portfolio_manager",
            "claude_pm_dashboard",
            "documentation_sync",
        ]

    def set_health_service(self, health_service: HealthMonitorService) -> None:
        """Set the health service instance for direct integration."""
        self._health_service = health_service

    def get_report_file_path(self) -> Path:
        """Get the path to the health report file."""
        return self._health_report_path

    def set_report_file_path(self, path: Path) -> None:
        """Set the path to the health report file."""
        self._health_report_path = path
