#!/usr/bin/env python3
"""
Test Commands Module - Claude Multi-Agent PM Framework

Handles monitoring, testing, and validation commands.
Extracted from main CLI as part of ISS-0114 modularization initiative.
"""

import asyncio
import sys
import subprocess
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..models.health import HealthStatus

console = Console()
logger = logging.getLogger(__name__)


def _display_health_dashboard(dashboard, verbose: bool = False):
    """Display comprehensive health dashboard."""
    current = dashboard.current_report

    # Overall status panel
    status_color = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.DEGRADED: "yellow",
        HealthStatus.UNHEALTHY: "red",
        HealthStatus.DOWN: "red",
        HealthStatus.ERROR: "red",
        HealthStatus.UNKNOWN: "blue",
    }.get(current.overall_status, "white")

    cache_indicator = "💨" if current.is_cache_hit else "🔄"

    overview_text = f"""
[bold]Overall Status:[/bold] [{status_color}]{current.overall_status.value.upper()}[/{status_color}]
[bold]Health Score:[/bold] {current.overall_health_percentage:.1f}%
[bold]Response Time:[/bold] {current.response_time_ms:.0f}ms {cache_indicator}
[bold]Total Services:[/bold] {current.total_services}
[bold]Healthy:[/bold] [green]{current.healthy_services}[/green] | [bold]Degraded:[/bold] [yellow]{current.degraded_services}[/yellow] | [bold]Unhealthy:[/bold] [red]{current.unhealthy_services}[/red] | [bold]Down:[/bold] [red]{current.down_services}[/red]
[bold]Generated:[/bold] {current.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

    console.print(
        Panel(
            overview_text.strip(), title="🏥 Health Dashboard Overview", border_style=status_color
        )
    )

    # Subsystem breakdown
    if current.subsystems:
        subsystem_table = Table(title="Subsystem Health Breakdown")
        subsystem_table.add_column("Subsystem", style="cyan")
        subsystem_table.add_column("Status", style="white")
        subsystem_table.add_column("Health %", style="green")
        subsystem_table.add_column("Services", style="yellow")
        subsystem_table.add_column("Avg Response", style="blue")

        for name, subsystem in current.subsystems.items():
            status_display = f"[{status_color}]{subsystem.status.value}[/{status_color}]"
            health_pct = f"{subsystem.health_percentage:.1f}%"
            service_breakdown = f"{subsystem.healthy_services}/{subsystem.total_services}"
            avg_response = (
                f"{subsystem.avg_response_time_ms:.0f}ms"
                if subsystem.avg_response_time_ms
                else "N/A"
            )

            subsystem_table.add_row(
                name, status_display, health_pct, service_breakdown, avg_response
            )

        console.print(subsystem_table)

    # Performance metrics
    if dashboard.performance_metrics:
        perf = dashboard.performance_metrics
        cache_stats = dashboard.cache_stats

        if verbose:
            perf_text = f"""
[bold]Cache Hit Rate:[/bold] {perf.get('cache_hit_rate', 0):.1f}%
[bold]Avg Service Response:[/bold] {perf.get('avg_service_response_time_ms', 0):.1f}ms
[bold]Total Alerts:[/bold] {perf.get('total_alerts', 0)}
[bold]Total Recommendations:[/bold] {perf.get('total_recommendations', 0)}
[bold]Cache Requests:[/bold] {cache_stats.get('total_requests', 0)} (Hits: {cache_stats.get('hits', 0)}, Misses: {cache_stats.get('misses', 0)})
"""
            console.print(Panel(perf_text.strip(), title="⚡ Performance Metrics"))

    # Alerts
    if current.alerts:
        console.print("\n[bold red]🚨 Active Alerts:[/bold red]")
        for alert in current.alerts[-5:]:  # Show last 5 alerts
            level_color = {"critical": "red", "warning": "yellow", "info": "blue"}.get(
                alert.get("level", "info"), "white"
            )
            console.print(f"  [{level_color}]●[/{level_color}] {alert['message']}")

    # Recommendations
    if current.recommendations:
        console.print("\n[bold blue]💡 Recommendations:[/bold blue]")
        for rec in current.recommendations[:3]:  # Show top 3 recommendations
            console.print(f"  • {rec}")

    # Service details (if verbose)
    if verbose and current.services:
        service_table = Table(title="Service Details")
        service_table.add_column("Service", style="cyan")
        service_table.add_column("Status", style="white")
        service_table.add_column("Message", style="white")
        service_table.add_column("Response Time", style="blue")
        service_table.add_column("Error", style="red")

        for service in current.services:
            status_display = f"[{status_color}]{service.status.value}[/{status_color}]"
            message = service.message[:50] + "..." if len(service.message) > 50 else service.message
            response_time = (
                f"{service.response_time_ms:.0f}ms" if service.response_time_ms else "N/A"
            )
            error = (
                service.error[:30] + "..."
                if service.error and len(service.error) > 30
                else (service.error or "")
            )

            service_table.add_row(service.name, status_display, message, response_time, error)

        console.print(service_table)


def _display_health_summary(dashboard, verbose: bool = False):
    """Display concise health summary."""
    current = dashboard.current_report

    status_symbol = {
        "healthy": "✅",
        "degraded": "⚠️",
        "unhealthy": "❌",
        "down": "🔴",
        "error": "💥",
        "unknown": "❓",
    }.get(current.overall_status.value, "❓")

    cache_indicator = "💨" if current.is_cache_hit else "🔄"

    console.print(
        f"{status_symbol} Overall: {current.overall_status.value.upper()} ({current.overall_health_percentage:.1f}%)"
    )
    console.print(f"⏱️  Response: {current.response_time_ms:.0f}ms {cache_indicator}")
    console.print(f"🔧 Services: {current.healthy_services}/{current.total_services} healthy")

    if current.alerts:
        console.print(f"🚨 Alerts: {len(current.alerts)}")

    if current.recommendations:
        console.print(f"💡 Recommendations: {len(current.recommendations)}")

    if verbose:
        console.print(f"📊 Subsystems: {len(current.subsystems)}")
        console.print(f"🕐 Generated: {current.timestamp.strftime('%H:%M:%S')}")


def register_test_commands(cli_group):
    """Register all test/monitoring commands with the main CLI group."""
    
    @cli_group.group()
    def monitoring():
        """Legacy health monitoring and system diagnostics."""
        pass

    @monitoring.command()
    @click.pass_context
    def check(ctx):
        """Run a comprehensive health check."""
        try:
            health_script = Path(__file__).parent.parent.parent / "scripts" / "automated_health_monitor.py"

            cmd = ["python", str(health_script), "once"]
            verbose = ctx.obj.get("verbose", False) if ctx.obj else False
            if verbose:
                cmd.append("--verbose")

            console.print("[bold blue]🏥 Running comprehensive health check...[/bold blue]")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                console.print("[bold green]✅ Health check completed successfully[/bold green]")
                if verbose:
                    console.print(result.stdout)
            else:
                console.print("[bold red]❌ Health check failed[/bold red]")
                console.print(result.stderr)
                sys.exit(1)

        except Exception as e:
            console.print(f"[bold red]❌ Error running health check: {e}[/bold red]")
            sys.exit(1)

    @monitoring.command()
    @click.option(
        "--format",
        "-f",
        type=click.Choice(["dashboard", "json", "summary"]),
        default="dashboard",
        help="Output format",
    )
    @click.option("--force-refresh", is_flag=True, help="Force refresh (skip cache)")
    @click.pass_context
    def comprehensive(ctx, format, force_refresh):
        """Run comprehensive health dashboard for all subsystems (M01-044)."""

        async def run():
            from ..services.health_dashboard import HealthDashboardOrchestrator

            try:
                console.print("[bold blue]🚀 Generating comprehensive health dashboard...[/bold blue]")

                # Get verbose from parent context
                verbose = ctx.obj.get("verbose", False) if ctx.obj else False

                # Initialize orchestrator
                orchestrator = HealthDashboardOrchestrator()

                # Get health dashboard
                dashboard = await orchestrator.get_health_dashboard(force_refresh=force_refresh)

                # Display results based on format
                if format == "json":
                    console.print(dashboard.to_json())
                elif format == "summary":
                    _display_health_summary(dashboard, verbose)
                else:  # dashboard
                    _display_health_dashboard(dashboard, verbose)

            except Exception as e:
                console.print(f"[bold red]❌ Error generating health dashboard: {e}[/bold red]")
                if verbose:
                    import traceback
                    console.print(traceback.format_exc())
                sys.exit(1)

        asyncio.run(run())

    @monitoring.command()
    @click.option("--interval", "-i", default=5, help="Check interval in minutes")
    @click.option("--threshold", "-t", default=60, help="Alert threshold percentage")
    @click.pass_context
    def monitor(ctx, interval, threshold):
        """Start continuous health monitoring."""
        try:
            health_script = Path(__file__).parent.parent.parent / "scripts" / "automated_health_monitor.py"

            cmd = [
                "python",
                str(health_script),
                "monitor",
                f"--interval={interval}",
                f"--threshold={threshold}",
            ]

            console.print(
                f"[bold blue]🔄 Starting continuous monitoring (interval: {interval}min, threshold: {threshold}%)[/bold blue]"
            )
            console.print("Press Ctrl+C to stop monitoring")

            subprocess.run(cmd)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Monitoring stopped by user[/bold yellow]")
        except Exception as e:
            console.print(f"[bold red]❌ Error starting monitoring: {e}[/bold red]")
            sys.exit(1)

    @monitoring.command()
    def status():
        """Show health monitoring status."""
        try:
            health_script = Path(__file__).parent.parent.parent / "scripts" / "automated_health_monitor.py"

            result = subprocess.run(
                ["python", str(health_script), "status"], capture_output=True, text=True
            )

            if result.returncode == 0:
                console.print(result.stdout)
            else:
                console.print("[bold red]❌ Failed to get health status[/bold red]")
                console.print(result.stderr)

        except Exception as e:
            console.print(f"[bold red]❌ Error getting health status: {e}[/bold red]")

    @monitoring.command()
    def reports():
        """List available health reports."""
        try:
            health_script = Path(__file__).parent.parent.parent / "scripts" / "automated_health_monitor.py"

            result = subprocess.run(
                ["python", str(health_script), "reports"], capture_output=True, text=True
            )

            if result.returncode == 0:
                console.print(result.stdout)
            else:
                console.print("[bold red]❌ Failed to get health reports[/bold red]")
                console.print(result.stderr)

        except Exception as e:
            console.print(f"[bold red]❌ Error getting health reports: {e}[/bold red]")

    @monitoring.command()
    @click.option("--limit", "-l", default=10, help="Number of logs to show")
    @click.option("--level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]), help="Filter by log level")
    def logs(limit, level):
        """Show recent framework logs."""
        try:
            health_script = Path(__file__).parent.parent.parent / "scripts" / "automated_health_monitor.py"

            cmd = ["python", str(health_script), "logs", f"--limit={limit}"]
            if level:
                cmd.append(f"--level={level}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                console.print(result.stdout)
            else:
                console.print("[bold red]❌ Failed to get logs[/bold red]")
                console.print(result.stderr)

        except Exception as e:
            console.print(f"[bold red]❌ Error getting logs: {e}[/bold red]")

    # Service Management Commands
    @cli_group.group()
    def service():
        """Service management and orchestration."""
        pass

    @service.command()
    def start():
        """Start framework services."""
        console.print("[bold blue]🚀 Starting Claude PM Framework services...[/bold blue]")
        
        async def run():
            from ..core.service_manager import ServiceManager
            
            try:
                service_manager = ServiceManager()
                await service_manager.start_all_services()
                console.print("[bold green]✅ All services started successfully[/bold green]")
            except Exception as e:
                console.print(f"[bold red]❌ Failed to start services: {e}[/bold red]")
                sys.exit(1)
        
        asyncio.run(run())

    @service.command()
    def stop():
        """Stop framework services."""
        console.print("[bold yellow]🛑 Stopping Claude PM Framework services...[/bold yellow]")
        
        async def run():
            from ..core.service_manager import ServiceManager
            
            try:
                service_manager = ServiceManager()
                await service_manager.stop_all_services()
                console.print("[bold green]✅ All services stopped successfully[/bold green]")
            except Exception as e:
                console.print(f"[bold red]❌ Failed to stop services: {e}[/bold red]")
                sys.exit(1)
        
        asyncio.run(run())

    @service.command()
    def restart():
        """Restart framework services."""
        console.print("[bold blue]🔄 Restarting Claude PM Framework services...[/bold blue]")
        
        async def run():
            from ..core.service_manager import ServiceManager
            
            try:
                service_manager = ServiceManager()
                await service_manager.stop_all_services()
                console.print("[dim]Services stopped...[/dim]")
                await service_manager.start_all_services()
                console.print("[bold green]✅ All services restarted successfully[/bold green]")
            except Exception as e:
                console.print(f"[bold red]❌ Failed to restart services: {e}[/bold red]")
                sys.exit(1)
        
        asyncio.run(run())

    @service.command(name="status")
    def service_status():
        """Show service status."""
        console.print("[bold blue]📊 Checking service status...[/bold blue]")
        
        async def run():
            from ..core.service_manager import ServiceManager
            
            try:
                service_manager = ServiceManager()
                status = await service_manager.get_service_status()
                
                status_table = Table(title="Service Status")
                status_table.add_column("Service", style="cyan")
                status_table.add_column("Status", style="white")
                status_table.add_column("Uptime", style="green")
                
                for service_name, service_info in status.items():
                    status_color = "green" if service_info.get("running") else "red"
                    status_text = f"[{status_color}]{'RUNNING' if service_info.get('running') else 'STOPPED'}[/{status_color}]"
                    uptime = service_info.get("uptime", "N/A")
                    
                    status_table.add_row(service_name, status_text, str(uptime))
                
                console.print(status_table)
                
            except Exception as e:
                console.print(f"[bold red]❌ Failed to get service status: {e}[/bold red]")
                sys.exit(1)
        
        asyncio.run(run())

    @service.command()
    @click.argument("service_name")
    def logs(service_name):
        """Show logs for a specific service."""
        console.print(f"[bold blue]📜 Showing logs for {service_name}...[/bold blue]")
        
        async def run():
            from ..core.service_manager import ServiceManager
            
            try:
                service_manager = ServiceManager()
                logs = await service_manager.get_service_logs(service_name)
                
                if logs:
                    for log_entry in logs[-20:]:  # Show last 20 log entries
                        timestamp = log_entry.get("timestamp", "")
                        level = log_entry.get("level", "INFO")
                        message = log_entry.get("message", "")
                        
                        level_color = {
                            "ERROR": "red",
                            "WARNING": "yellow", 
                            "INFO": "blue",
                            "DEBUG": "dim"
                        }.get(level, "white")
                        
                        console.print(f"[dim]{timestamp}[/dim] [{level_color}]{level}[/{level_color}] {message}")
                else:
                    console.print(f"[yellow]No logs found for service: {service_name}[/yellow]")
                
            except Exception as e:
                console.print(f"[bold red]❌ Failed to get service logs: {e}[/bold red]")
                sys.exit(1)
        
        asyncio.run(run())

    return cli_group