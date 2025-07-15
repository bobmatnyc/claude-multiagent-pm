#!/usr/bin/env python3
"""
Claude PM Service Manager Script

Provides command-line interface for managing Claude PM services
including health monitoring, memory service, and project services.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add the parent directory to the path so we can import claude_pm
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_pm.core.service_manager import ServiceManager
from claude_pm.services.health_monitor import HealthMonitorService
from claude_pm.services.project_service import ProjectService

console = Console()


class ClaudePMServiceManager:
    """Command-line service manager for Claude PM Framework."""

    def __init__(self):
        self.service_manager = ServiceManager()
        self._setup_services()

    def _setup_services(self):
        """Setup default Claude PM services."""
        # Health Monitor Service
        health_service = HealthMonitorService()
        self.service_manager.register_service(
            health_service, dependencies=[], startup_order=1, auto_start=True, critical=True
        )

        # Memory Service has been removed from framework

        # Project Service - updated to not depend on removed memory_service
        project_service = ProjectService()
        self.service_manager.register_service(
            project_service,
            dependencies=[],  # memory_service dependency removed
            startup_order=2,  # moved up in startup order
            auto_start=True,
            critical=False,
        )

    async def start_all(self):
        """Start all services."""
        try:
            console.print("[bold blue]🚀 Starting Claude PM services...[/bold blue]")
            await self.service_manager.start_all()

            # Wait for critical services to become healthy
            if await self.service_manager.wait_for_healthy(timeout=30):
                console.print("[bold green]✅ All critical services are healthy[/bold green]")
            else:
                console.print("[bold yellow]⚠️ Some services may not be fully healthy[/bold yellow]")

            self._display_status()

        except Exception as e:
            console.print(f"[bold red]❌ Failed to start services: {e}[/bold red]")
            return False

        return True

    async def stop_all(self):
        """Stop all services."""
        try:
            console.print("[bold blue]🛑 Stopping Claude PM services...[/bold blue]")
            await self.service_manager.stop_all()
            console.print("[bold green]✅ All services stopped[/bold green]")

        except Exception as e:
            console.print(f"[bold red]❌ Failed to stop services: {e}[/bold red]")
            return False

        return True

    async def restart_all(self):
        """Restart all services."""
        console.print("[bold blue]🔄 Restarting Claude PM services...[/bold blue]")
        success = await self.stop_all()
        if success:
            success = await self.start_all()
        return success

    async def status(self):
        """Show service status."""
        self._display_status()

        # Run health checks
        console.print("\n[bold blue]Running health checks...[/bold blue]")
        health_results = await self.service_manager.health_check_all()

        self._display_health_results(health_results)

    def _display_status(self):
        """Display service status table."""
        status = self.service_manager.get_service_status()

        table = Table(title="Claude PM Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Uptime", style="yellow")
        table.add_column("Health", style="magenta")
        table.add_column("Critical", style="red")

        for service_name, service_status in status.items():
            running_status = "🟢 Running" if service_status["running"] else "🔴 Stopped"
            uptime = f"{service_status['uptime']:.1f}s" if service_status["uptime"] else "N/A"
            health_status = service_status["health"]
            critical = "Yes" if service_status["critical"] else "No"

            table.add_row(service_name, running_status, uptime, health_status, critical)

        console.print(table)

    def _display_health_results(self, health_results):
        """Display health check results."""
        table = Table(title="Service Health Details")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Message", style="yellow")
        table.add_column("Checks", style="magenta")

        for service_name, health in health_results.items():
            # Format checks
            checks_str = ""
            if health.checks:
                passed = sum(1 for v in health.checks.values() if v)
                total = len(health.checks)
                checks_str = f"{passed}/{total}"

            # Color status
            status_color = {
                "healthy": "[green]✅ Healthy[/green]",
                "degraded": "[yellow]⚠️ Degraded[/yellow]",
                "unhealthy": "[red]❌ Unhealthy[/red]",
                "unknown": "[gray]❓ Unknown[/gray]",
            }.get(health.status, health.status)

            table.add_row(
                service_name,
                status_color,
                health.message[:50] + "..." if len(health.message) > 50 else health.message,
                checks_str,
            )

        console.print(table)


# CLI interface
@click.group()
def cli():
    """Claude PM Service Manager - Manage Claude PM Framework services."""
    pass


@cli.command()
def start():
    """Start all Claude PM services."""
    manager = ClaudePMServiceManager()

    async def run():
        success = await manager.start_all()
        if success:
            console.print("\n[bold green]Services started successfully![/bold green]")
            console.print("Use 'claude-pm-service status' to check service health")
        else:
            console.print("\n[bold red]Failed to start some services[/bold red]")
            sys.exit(1)

    asyncio.run(run())


@cli.command()
def stop():
    """Stop all Claude PM services."""
    manager = ClaudePMServiceManager()

    async def run():
        success = await manager.stop_all()
        if not success:
            console.print("\n[bold red]Failed to stop some services[/bold red]")
            sys.exit(1)

    asyncio.run(run())


@cli.command()
def restart():
    """Restart all Claude PM services."""
    manager = ClaudePMServiceManager()

    async def run():
        success = await manager.restart_all()
        if success:
            console.print("\n[bold green]Services restarted successfully![/bold green]")
        else:
            console.print("\n[bold red]Failed to restart services[/bold red]")
            sys.exit(1)

    asyncio.run(run())


@cli.command()
def status():
    """Show status of all Claude PM services."""
    manager = ClaudePMServiceManager()

    async def run():
        await manager.status()

    asyncio.run(run())


@cli.command()
@click.argument("service_name")
def start_service(service_name):
    """Start a specific service."""
    manager = ClaudePMServiceManager()

    async def run():
        try:
            await manager.service_manager.start_service(service_name)
            console.print(f"[bold green]✅ Service '{service_name}' started[/bold green]")
        except ValueError as e:
            console.print(f"[bold red]❌ {e}[/bold red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]❌ Failed to start service '{service_name}': {e}[/bold red]")
            sys.exit(1)

    asyncio.run(run())


@cli.command()
@click.argument("service_name")
def stop_service(service_name):
    """Stop a specific service."""
    manager = ClaudePMServiceManager()

    async def run():
        try:
            await manager.service_manager.stop_service(service_name)
            console.print(f"[bold green]✅ Service '{service_name}' stopped[/bold green]")
        except ValueError as e:
            console.print(f"[bold red]❌ {e}[/bold red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]❌ Failed to stop service '{service_name}': {e}[/bold red]")
            sys.exit(1)

    asyncio.run(run())


@cli.command()
@click.argument("service_name")
def restart_service(service_name):
    """Restart a specific service."""
    manager = ClaudePMServiceManager()

    async def run():
        try:
            await manager.service_manager.restart_service(service_name)
            console.print(f"[bold green]✅ Service '{service_name}' restarted[/bold green]")
        except ValueError as e:
            console.print(f"[bold red]❌ {e}[/bold red]")
            sys.exit(1)
        except Exception as e:
            console.print(
                f"[bold red]❌ Failed to restart service '{service_name}': {e}[/bold red]"
            )
            sys.exit(1)

    asyncio.run(run())


@cli.command()
def list():
    """List all registered services."""
    manager = ClaudePMServiceManager()
    services = manager.service_manager.list_services()

    console.print("[bold blue]Registered Services:[/bold blue]")
    for service_name in services:
        service_info = manager.service_manager.get_service_info(service_name)
        deps = ", ".join(service_info.dependencies) if service_info.dependencies else "None"
        console.print(f"  • {service_name} (dependencies: {deps})")


@cli.command()
def health():
    """Run health check on all services."""
    manager = ClaudePMServiceManager()

    async def run():
        console.print("[bold blue]Running health checks on all services...[/bold blue]")
        health_results = await manager.service_manager.health_check_all()
        manager._display_health_results(health_results)

        # Summary
        healthy = sum(1 for h in health_results.values() if h.status == "healthy")
        total = len(health_results)

        if healthy == total:
            console.print(f"\n[bold green]✅ All {total} services are healthy[/bold green]")
        else:
            console.print(f"\n[bold yellow]⚠️ {healthy}/{total} services are healthy[/bold yellow]")

    asyncio.run(run())


@cli.command()
def dependencies():
    """Show service dependency graph."""
    manager = ClaudePMServiceManager()
    deps = manager.service_manager.get_dependency_graph()

    console.print("[bold blue]Service Dependency Graph:[/bold blue]")
    for service, dependencies in deps.items():
        deps_str = " -> ".join(dependencies) if dependencies else "No dependencies"
        console.print(f"  {service}: {deps_str}")


def main():
    """Main entry point for the service manager."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Service management interrupted[/bold yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
