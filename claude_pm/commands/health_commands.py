"""
CMPM Health Commands
==================

Health monitoring and integration management commands for the Claude PM Framework.
Provides system health dashboards and integration status monitoring.
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..services.health_dashboard import HealthDashboardOrchestrator
from ..services.memory_service import MemoryService
from ..core.config import Config
# from ..agents.enhanced_qa_agent import EnhancedQAAgent  # Module not yet implemented
from .utils.command_utils import CMPMCommandBase, handle_command_error, run_async_command
from .utils.formatters import format_health_status, format_json_output

console = Console()
logger = logging.getLogger(__name__)


class CMPMHealthMonitor(CMPMCommandBase):
    """CMPM Health Command Implementation with ai-trackdown integration."""

    async def get_framework_health(self) -> Dict[str, Any]:
        """Get comprehensive framework health status."""
        try:
            # Initialize health dashboard orchestrator with aggressive timeouts
            dashboard = HealthDashboardOrchestrator(
                cache_ttl_seconds=10.0,  # Faster for real-time slash commands
                global_timeout_seconds=5.0,  # Optimized for sub-3s performance target
            )

            try:
                # Collect health data
                health_data = await dashboard._collect_fresh_health()
            finally:
                # Ensure cleanup happens regardless of success/failure
                await dashboard.cleanup()

            return {
                "status": (
                    "healthy" if health_data.overall_status.value == "healthy" else "degraded"
                ),
                "framework_version": "4.5.0",
                "components": health_data.subsystems,
                "response_time": health_data.response_time_ms,
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Framework health check failed: {e}")
            return {"status": "error", "error": str(e), "last_updated": datetime.now().isoformat()}

    def get_aitrackdown_version(self) -> str:
        """Get ai-trackdown-tools version from npm."""
        try:
            result = subprocess.run(
                ["npm", "list", "-g", "@bobmatnyc/ai-trackdown-tools", "--depth=0", "--json"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                # Navigate the npm list structure
                deps = data.get("dependencies", {})
                package_info = deps.get("@bobmatnyc/ai-trackdown-tools", {})
                return package_info.get("version", "unknown")
        except Exception:
            pass
        return "unknown"

    async def get_aitrackdown_health(self) -> Dict[str, Any]:
        """Get ai-trackdown-tools integration health status via orchestrator."""
        try:
            # Use health dashboard orchestrator for consistent status reporting
            dashboard = HealthDashboardOrchestrator(
                cache_ttl_seconds=10.0, global_timeout_seconds=15.0
            )

            # Collect health data from orchestrator
            health_data = await dashboard._collect_fresh_health()

            # Find ai-trackdown specific reports
            ai_trackdown_reports = []
            for subsystem in health_data.subsystems:
                # Handle both object and dict subsystem data
                subsystem_name = (
                    getattr(subsystem, "name", subsystem)
                    if hasattr(subsystem, "name")
                    else str(subsystem)
                )
                if subsystem_name == "AI-Trackdown Tools":
                    ai_trackdown_reports = (
                        getattr(subsystem, "services", []) if hasattr(subsystem, "services") else []
                    )
                    break

            if ai_trackdown_reports:
                # Aggregate status from all ai-trackdown reports
                all_healthy = all(
                    report.status.value == "healthy" for report in ai_trackdown_reports
                )
                any_error = any(
                    report.status.value in ["error", "down"] for report in ai_trackdown_reports
                )

                if all_healthy:
                    status = "operational"
                elif any_error:
                    status = "error"
                else:
                    status = "degraded"

                # Calculate metrics
                total_items = 0
                for report in ai_trackdown_reports:
                    if "items tracked" in report.message:
                        import re

                        match = re.search(r"(\d+)\s+items tracked", report.message)
                        if match:
                            total_items = int(match.group(1))

                return {
                    "status": status,
                    "service": "ai-trackdown-tools",
                    "version": self.get_aitrackdown_version(),
                    "cli_responsive": True,
                    "total_items": total_items,
                    "reports_count": len(ai_trackdown_reports),
                    "last_check": datetime.now().isoformat(),
                }
            else:
                # Fallback to direct CLI test if orchestrator has no ai-trackdown data
                result = subprocess.run(
                    ["aitrackdown", "status"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    cwd=self.framework_path,
                )

                if result.returncode == 0:
                    return {
                        "status": "operational",
                        "service": "ai-trackdown-tools",
                        "version": self.get_aitrackdown_version(),
                        "cli_responsive": True,
                        "fallback_method": "direct_cli",
                        "last_check": datetime.now().isoformat(),
                    }
                else:
                    return {
                        "status": "error",
                        "service": "ai-trackdown-tools",
                        "error": "CLI not accessible",
                        "last_check": datetime.now().isoformat(),
                    }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "service": "ai-trackdown-tools",
                "error": "Command timed out after 5 seconds",
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "service": "ai-trackdown-tools",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def get_task_system_health(self) -> Dict[str, Any]:
        """Get task system operational status."""
        try:
            # Get epic, issue, and task counts using global CLI
            epic_result = subprocess.run(
                ["aitrackdown", "epic", "list"],
                capture_output=True,
                text=True,
                timeout=3,
                cwd=self.framework_path,
            )

            issue_result = subprocess.run(
                ["aitrackdown", "issue", "list"],
                capture_output=True,
                text=True,
                timeout=3,
                cwd=self.framework_path,
            )

            if epic_result.returncode == 0 and issue_result.returncode == 0:
                # Parse counts from output
                epic_count = epic_result.stdout.count("EP-")
                issue_count = issue_result.stdout.count("ISS-")

                return {
                    "status": "operational",
                    "service": "task_system",
                    "epic_count": epic_count,
                    "issue_count": issue_count,
                    "total_items": epic_count + issue_count,
                    "last_check": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "error",
                    "service": "task_system",
                    "error": "Failed to query task counts",
                    "last_check": datetime.now().isoformat(),
                }

        except Exception as e:
            return {
                "status": "error",
                "service": "task_system",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def get_memory_system_health(self) -> Dict[str, Any]:
        """Get memory system connectivity status."""
        try:
            # Use the new FlexibleMemoryService with optimized config
            from ..services.memory import FlexibleMemoryService

            # Configure service for fast health checks with both backends
            config = {
                "detection_timeout": 1.0,
                "detection_retries": 1,
                "fallback_chain": ["mem0ai", "sqlite"],  # Test both backends
                "circuit_breaker_threshold": 2,
                "circuit_breaker_recovery": 30,
            }

            memory_service = FlexibleMemoryService(config)

            # Initialize with timeout
            start_time = time.time()
            await memory_service.initialize()
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Get backend status information
            active_backend = memory_service.active_backend_name
            available_backends = list(memory_service.backends.keys())
            is_healthy = memory_service._is_healthy

            # Determine backend-specific status
            mem0ai_available = "mem0ai" in available_backends
            sqlite_available = "sqlite" in available_backends
            mem0ai_active = active_backend == "mem0ai"
            sqlite_active = active_backend == "sqlite"

            return {
                "status": "operational" if is_healthy else "degraded",
                "service": "memory_system",
                "active_backend": active_backend,
                "backend_health": {
                    "mem0ai": {
                        "available": mem0ai_available,
                        "active": mem0ai_active,
                        "status": (
                            "operational"
                            if mem0ai_active and is_healthy
                            else "standby" if mem0ai_available else "unavailable"
                        ),
                    },
                    "sqlite": {
                        "available": sqlite_available,
                        "active": sqlite_active,
                        "status": (
                            "operational"
                            if sqlite_active and is_healthy
                            else "standby" if sqlite_available else "unavailable"
                        ),
                    },
                },
                "response_time": int(response_time),
                "available_backends": available_backends,
                "system_healthy": is_healthy,
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "service": "memory_system",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def get_qa_system_health(self) -> Dict[str, Any]:
        """Get Enhanced QA Agent system health status."""
        # QA Agent module not yet implemented
        return {
            "status": "not_implemented",
            "service": "enhanced_qa_agent",
            "message": "QA Agent module not yet implemented",
            "last_check": datetime.now().isoformat(),
        }

    def calculate_system_reliability_score(self, health_data: Dict[str, Any]) -> int:
        """Calculate system reliability score (0-100)."""
        total_components = 0
        healthy_components = 0

        for component_name, component_data in health_data.items():
            if isinstance(component_data, dict) and "status" in component_data:
                total_components += 1
                if component_data["status"] in ["healthy", "operational"]:
                    healthy_components += 1

        if total_components == 0:
            return 0

        return int((healthy_components / total_components) * 100)

    async def generate_health_dashboard(self) -> None:
        """Generate comprehensive CMPM health dashboard."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Collecting system health data...", total=None)

            # Collect all health data in parallel
            health_data = await asyncio.gather(
                self.get_framework_health(),
                self.get_aitrackdown_health(),
                self.get_task_system_health(),
                self.get_memory_system_health(),
                # self.get_qa_system_health(),  # Excluded - QA Agent not ready
                return_exceptions=True,
            )

            progress.update(task, description="Generating dashboard...")

            # Process collected data
            framework_health, aitrackdown_health, task_health, memory_health = health_data
            qa_health = None  # QA Agent excluded from health checks

            # Calculate reliability score
            all_health_data = {
                "framework": framework_health,
                "aitrackdown": aitrackdown_health,
                "task_system": task_health,
                "memory_system": memory_health,
                # "qa_system": qa_health  # Excluded - QA Agent not ready
            }

            reliability_score = self.calculate_system_reliability_score(all_health_data)

            progress.update(task, description="Rendering dashboard...")

        # Create dashboard header
        total_time = self.get_execution_time()

        header = Panel(
            Text(
                f"CMPM Health Dashboard v4.5.0\nSystem Reliability Score: {reliability_score}%\nResponse Time: {total_time:.2f}s",
                justify="center",
                style="bold white",
            ),
            title="🟢 Claude Multi-Agent PM Framework",
            border_style=(
                "green"
                if reliability_score >= 80
                else "yellow" if reliability_score >= 60 else "red"
            ),
        )

        console.print(header)
        console.print()

        # Create health status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Details", style="dim")

        # Add framework health
        if isinstance(framework_health, dict):
            status_color = "green" if framework_health.get("status") == "healthy" else "red"
            table.add_row(
                "Framework Core",
                f"[{status_color}]{framework_health.get('status', 'unknown').upper()}[/{status_color}]",
                f"v{framework_health.get('framework_version', 'unknown')} | {framework_health.get('response_time', 0)}ms",
            )

        # Add ai-trackdown health
        if isinstance(aitrackdown_health, dict):
            # Fix status mapping: accept both "operational" and "healthy" as operational
            status = aitrackdown_health.get("status", "unknown")
            is_operational = status in ["operational", "healthy"]
            status_color = "green" if is_operational else "red"
            table.add_row(
                "AI-Trackdown Tools",
                f"[{status_color}]{status.upper()}[/{status_color}]",
                f"CLI: {'✓' if aitrackdown_health.get('cli_responsive') else '✗'} | Service: {aitrackdown_health.get('service', 'unknown')}",
            )

        # Add task system health
        if isinstance(task_health, dict):
            status_color = "green" if task_health.get("status") == "operational" else "red"
            table.add_row(
                "Task System",
                f"[{status_color}]{task_health.get('status', 'unknown').upper()}[/{status_color}]",
                f"Epics: {task_health.get('epic_count', 0)} | Issues: {task_health.get('issue_count', 0)}",
            )

        # Add memory system health
        if isinstance(memory_health, dict):
            status_color = "green" if memory_health.get("status") == "operational" else "red"
            active_backend = memory_health.get("active_backend", "unknown")
            backend_health = memory_health.get("backend_health", {})

            # Create backend status summary
            mem0ai_status = "✓" if backend_health.get("mem0ai", {}).get("available", False) else "✗"
            sqlite_status = "✓" if backend_health.get("sqlite", {}).get("available", False) else "✗"

            table.add_row(
                "Memory System",
                f"[{status_color}]{memory_health.get('status', 'unknown').upper()}[/{status_color}]",
                f"Active: {active_backend} | mem0AI: {mem0ai_status} | SQLite: {sqlite_status} | {memory_health.get('response_time', 0)}ms",
            )

        # Add QA system health - EXCLUDED (not ready)
        # Enhanced QA Agent excluded from health monitoring until development complete
        table.add_row(
            "Enhanced QA Agent",
            "[yellow]EXCLUDED[/yellow]",
            "Not included in health monitoring (development in progress)",
        )

        console.print(table)
        console.print()

        # System summary
        active_backend = (
            memory_health.get("active_backend", "unknown")
            if isinstance(memory_health, dict)
            else "unknown"
        )
        memory_status = (
            memory_health.get("status", "unknown") if isinstance(memory_health, dict) else "unknown"
        )

        summary_text = f"""
🚀 **Framework Status**: Claude PM Framework v4.5.0 operational
📊 **Task Management**: {task_health.get('total_items', 0)} total items managed
🧠 **Memory Integration**: {active_backend} backend active, system {memory_status}
🧪 **Enhanced QA Agent**: Excluded from monitoring (development in progress)
⚡ **Performance**: {total_time:.2f}s response time | {reliability_score}% reliability
        """

        console.print(Panel(summary_text.strip(), title="System Summary", border_style="blue"))


# CLI Commands
@click.command(name="cmpm:health")
@click.option("--output-json", is_flag=True, help="Output detailed health data as JSON")
@click.option("--detailed", is_flag=True, help="Show detailed component information")
def cmpm_health(output_json: bool, detailed: bool):
    """🏥 CMPM Health - Comprehensive system health dashboard"""

    async def run_health_check():
        monitor = CMPMHealthMonitor()

        if output_json:
            # Collect all health data for JSON output
            health_data = await asyncio.gather(
                monitor.get_framework_health(),
                monitor.get_aitrackdown_health(),
                monitor.get_task_system_health(),
                monitor.get_memory_system_health(),
                return_exceptions=True,
            )

            framework_health, aitrackdown_health, task_health, memory_health = health_data

            output = {
                "framework": framework_health,
                "aitrackdown": aitrackdown_health,
                "task_system": task_health,
                "memory_system": memory_health,
                "timestamp": datetime.now().isoformat(),
            }

            console.print(format_json_output(output))
        else:
            # Show interactive dashboard
            await monitor.generate_health_dashboard()

    run_async_command(run_health_check())


__all__ = ["cmpm_health", "CMPMHealthMonitor"]
