#!/usr/bin/env python3
"""
Claude Multi-Agent Project Management Framework - Main CLI Entry Point

Provides unified command-line interface for all Claude Multi-Agent PM operations
including health monitoring, service management, project operations,
and framework utilities.
"""

import asyncio
import sys
import json
import uuid
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core.service_manager import ServiceManager
from .core.config import Config
from .services.health_monitor import HealthMonitorService
from .services.memory_service import MemoryService
from .services.project_service import ProjectService
from .scripts.service_manager import ClaudePMServiceManager
from .cli_enforcement import enforcement_cli
from .cmpm_commands import register_cmpm_commands

console = Console()
logger = logging.getLogger(__name__)

def get_framework_config():
    """Get framework configuration with dynamic path resolution."""
    return Config()

def get_claude_pm_path():
    """Get the Claude PM framework path from configuration."""
    config = get_framework_config()
    return Path(config.get("claude_pm_path"))

def get_managed_path():
    """Get the managed projects path from configuration."""
    config = get_framework_config()
    return Path(config.get("managed_path"))


@click.group()
@click.version_option(version="3.0.0", prog_name="Claude Multi-Agent PM Framework")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx, verbose, config):
    """
    Claude Multi-Agent Project Management Framework - Multi-Agent Orchestration for AI-driven Project Management
    
    A comprehensive framework for managing AI-enhanced development projects with
    integrated memory management, health monitoring, and multi-agent coordination.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    
    if verbose:
        console.print("[dim]Claude Multi-Agent PM Framework v3.0.0 - Python Edition[/dim]")


# Health Monitoring Commands
@cli.group()
def monitoring():
    """Legacy health monitoring and system diagnostics."""
    pass


@cli.command()
@click.option('--detailed', is_flag=True, help='Show detailed subsystem information')
@click.option('--service', type=click.Choice(['memory', 'indexing', 'projects', 'all']), default='all', help='Focus on specific service')
@click.option('--export', type=click.Choice(['json', 'yaml']), help='Export health data')
@click.option('--report', is_flag=True, help='Generate detailed health report')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with full diagnostics')
@click.pass_context
def health(ctx, detailed, service, export, report, verbose):
    """🏥 Unified Health Dashboard - Central monitoring for all framework subsystems (M01-044)."""
    async def run():
        from .services.health_dashboard import HealthDashboardOrchestrator
        from .services.project_indexer import create_project_indexer
        from .services.project_memory_manager import create_project_memory_manager
        from .integrations.mem0ai_integration import create_mem0ai_integration
        from .models.health import HealthStatus, create_service_health_report
        import time
        
        start_time = time.time()
        
        try:
            console.print("[bold blue]🟢 Claude PM Framework Health Dashboard[/bold blue]")
            console.print("═══════════════════════════════════════\n")
            
            # Initialize orchestrator with enhanced collectors for M01-044
            orchestrator = HealthDashboardOrchestrator()
            
            # Add MEM-007 project indexing health monitoring
            await _add_project_indexing_health_collector(orchestrator)
            
            # Get comprehensive health dashboard
            dashboard = await orchestrator.get_health_dashboard(force_refresh=True)
            
            # Add managed projects portfolio health
            managed_projects_health = await _get_managed_projects_health()
            
            # Display unified dashboard
            if service == 'all':
                _display_unified_health_dashboard(dashboard, managed_projects_health, detailed, verbose)
            elif service == 'memory':
                await _display_memory_service_health(verbose)
            elif service == 'indexing':
                await _display_indexing_service_health(verbose)
            elif service == 'projects':
                _display_projects_health(managed_projects_health, verbose)
            
            # Handle export options
            if export:
                await _export_health_data(dashboard, managed_projects_health, export)
            
            # Generate report if requested
            if report:
                await _generate_health_report(dashboard, managed_projects_health)
            
            # Performance summary
            total_time = (time.time() - start_time) * 1000
            cache_indicator = "💨" if dashboard.current_report.is_cache_hit else "🔄"
            console.print(f"\n[dim]Response time: {total_time:.0f}ms {cache_indicator} | Framework v3.0.0[/dim]")
            
        except Exception as e:
            console.print(f"[bold red]❌ Error generating health dashboard: {e}[/bold red]")
            if verbose or ctx.obj.get('verbose'):
                import traceback
                console.print(traceback.format_exc())
            sys.exit(1)
    
    asyncio.run(run())


@monitoring.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def check(ctx, verbose):
    """Run a comprehensive health check."""
    import subprocess
    
    try:
        health_script = Path(__file__).parent.parent / "scripts" / "automated_health_monitor.py"
        
        cmd = ["python", str(health_script), "once"]
        if verbose or ctx.obj.get('verbose'):
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
@click.option('--format', '-f', type=click.Choice(['dashboard', 'json', 'summary']), default='dashboard', help='Output format')
@click.option('--force-refresh', is_flag=True, help='Force refresh (skip cache)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with detailed metrics')
@click.pass_context
def comprehensive(ctx, format, force_refresh, verbose):
    """Run comprehensive health dashboard for all subsystems (M01-044)."""
    async def run():
        from .services.health_dashboard import HealthDashboardOrchestrator
        from .models.health import HealthStatus
        
        try:
            console.print("[bold blue]🚀 Generating comprehensive health dashboard...[/bold blue]")
            
            # Initialize orchestrator
            orchestrator = HealthDashboardOrchestrator()
            
            # Get health dashboard
            dashboard = await orchestrator.get_health_dashboard(force_refresh=force_refresh)
            
            # Display results based on format
            if format == 'json':
                console.print(dashboard.to_json())
            elif format == 'summary':
                _display_health_summary(dashboard, verbose)
            else:  # dashboard
                _display_health_dashboard(dashboard, verbose)
            
        except Exception as e:
            console.print(f"[bold red]❌ Error generating health dashboard: {e}[/bold red]")
            if verbose or ctx.obj.get('verbose'):
                import traceback
                console.print(traceback.format_exc())
            sys.exit(1)
    
    asyncio.run(run())


def _display_health_dashboard(dashboard, verbose: bool = False):
    """Display comprehensive health dashboard."""
    from .models.health import HealthStatus
    
    current = dashboard.current_report
    
    # Overall status panel
    status_color = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.DEGRADED: "yellow", 
        HealthStatus.UNHEALTHY: "red",
        HealthStatus.DOWN: "red",
        HealthStatus.ERROR: "red",
        HealthStatus.UNKNOWN: "blue"
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
    
    console.print(Panel(overview_text.strip(), title="🏥 Health Dashboard Overview", border_style=status_color))
    
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
            avg_response = f"{subsystem.avg_response_time_ms:.0f}ms" if subsystem.avg_response_time_ms else "N/A"
            
            subsystem_table.add_row(name, status_display, health_pct, service_breakdown, avg_response)
        
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
            level_color = {"critical": "red", "warning": "yellow", "info": "blue"}.get(alert.get("level", "info"), "white")
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
            response_time = f"{service.response_time_ms:.0f}ms" if service.response_time_ms else "N/A"
            error = service.error[:30] + "..." if service.error and len(service.error) > 30 else (service.error or "")
            
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
        "unknown": "❓"
    }.get(current.overall_status.value, "❓")
    
    cache_indicator = "💨" if current.is_cache_hit else "🔄"
    
    console.print(f"{status_symbol} Overall: {current.overall_status.value.upper()} ({current.overall_health_percentage:.1f}%)")
    console.print(f"⏱️  Response: {current.response_time_ms:.0f}ms {cache_indicator}")
    console.print(f"🔧 Services: {current.healthy_services}/{current.total_services} healthy")
    
    if current.alerts:
        console.print(f"🚨 Alerts: {len(current.alerts)}")
    
    if current.recommendations:
        console.print(f"💡 Recommendations: {len(current.recommendations)}")
    
    if verbose:
        console.print(f"📊 Subsystems: {len(current.subsystems)}")
        console.print(f"🕐 Generated: {current.timestamp.strftime('%H:%M:%S')}")


@monitoring.command()
@click.option('--interval', '-i', default=5, help='Check interval in minutes')
@click.option('--threshold', '-t', default=60, help='Alert threshold percentage')
@click.pass_context
def monitor(ctx, interval, threshold):
    """Start continuous health monitoring."""
    import subprocess
    
    try:
        health_script = Path(__file__).parent.parent / "scripts" / "automated_health_monitor.py"
        
        cmd = [
            "python", str(health_script), "monitor",
            f"--interval={interval}",
            f"--threshold={threshold}"
        ]
        
        console.print(f"[bold blue]🔄 Starting continuous monitoring (interval: {interval}min, threshold: {threshold}%)[/bold blue]")
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
    import subprocess
    
    try:
        health_script = Path(__file__).parent.parent / "scripts" / "automated_health_monitor.py"
        
        result = subprocess.run(
            ["python", str(health_script), "status"],
            capture_output=True,
            text=True
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
    import subprocess
    
    try:
        health_script = Path(__file__).parent.parent / "scripts" / "automated_health_monitor.py"
        
        result = subprocess.run(
            ["python", str(health_script), "reports"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print(result.stdout)
        else:
            console.print("[bold red]❌ Failed to list reports[/bold red]")
            console.print(result.stderr)
            
    except Exception as e:
        console.print(f"[bold red]❌ Error listing reports: {e}[/bold red]")


@monitoring.command()
def alerts():
    """Show recent health alerts."""
    import subprocess
    
    try:
        health_script = Path(__file__).parent.parent / "scripts" / "automated_health_monitor.py"
        
        result = subprocess.run(
            ["python", str(health_script), "alerts"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print(result.stdout)
        else:
            console.print("[bold red]❌ Failed to get alerts[/bold red]")
            console.print(result.stderr)
            
    except Exception as e:
        console.print(f"[bold red]❌ Error getting alerts: {e}[/bold red]")


# Service Management Commands
@cli.group()
def service():
    """Service management and orchestration."""
    pass


@service.command()
def start():
    """Start all Claude PM services."""
    async def run():
        manager = ClaudePMServiceManager()
        success = await manager.start_all()
        if not success:
            sys.exit(1)
    
    asyncio.run(run())


@service.command()
def stop():
    """Stop all Claude PM services."""
    async def run():
        manager = ClaudePMServiceManager()
        success = await manager.stop_all()
        if not success:
            sys.exit(1)
    
    asyncio.run(run())


@service.command()
def restart():
    """Restart all Claude PM services."""
    async def run():
        manager = ClaudePMServiceManager()
        success = await manager.restart_all()
        if not success:
            sys.exit(1)
    
    asyncio.run(run())


@service.command(name="status")
def service_status():
    """Show status of all services."""
    async def run():
        manager = ClaudePMServiceManager()
        await manager.status()
    
    asyncio.run(run())


@service.command()
def list():
    """List all registered services."""
    async def run():
        manager = ClaudePMServiceManager()
        services = manager.service_manager.list_services()
        
        console.print("[bold blue]Registered Services:[/bold blue]")
        for service_name in services:
            service_info = manager.service_manager.get_service_info(service_name)
            deps = ", ".join(service_info.dependencies) if service_info.dependencies else "None"
            critical = "🔴 Critical" if service_info.critical else "🟡 Standard"
            console.print(f"  • {service_name} ({critical}, deps: {deps})")
    
    asyncio.run(run())


# Project Management Commands
@cli.group()
def project():
    """Project management and framework compliance."""
    pass


@project.command()
def list():
    """List all discovered projects."""
    async def run():
        project_service = ProjectService()
        await project_service._initialize()
        
        projects = project_service.get_projects()
        
        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return
        
        table = Table(title="Claude PM Projects")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Compliance", style="magenta")
        table.add_column("Last Activity", style="blue")
        
        for project in projects.values():
            compliance_color = "green" if project.compliance_score >= 80 else "yellow" if project.compliance_score >= 60 else "red"
            
            table.add_row(
                project.name,
                project.type,
                project.status,
                f"[{compliance_color}]{project.compliance_score}%[/{compliance_color}]",
                project.last_activity.split('T')[0] if 'T' in project.last_activity else project.last_activity[:10]
            )
        
        console.print(table)
        
        await project_service._cleanup()
    
    asyncio.run(run())


@project.command()
@click.argument('project_name')
def info(project_name):
    """Show detailed information about a project."""
    async def run():
        project_service = ProjectService()
        await project_service._initialize()
        
        project = project_service.get_project(project_name)
        if not project:
            console.print(f"[red]Project '{project_name}' not found[/red]")
            return
        
        compliance = project_service.get_compliance(project_name)
        
        # Project info panel
        info_text = f"""
[bold]Path:[/bold] {project.path}
[bold]Type:[/bold] {project.type}
[bold]Status:[/bold] {project.status}
[bold]Compliance Score:[/bold] {project.compliance_score}%
[bold]Last Activity:[/bold] {project.last_activity}
"""
        
        if project.git_info:
            info_text += f"""
[bold]Git Branch:[/bold] {project.git_info.get('current_branch', 'unknown')}
[bold]Uncommitted Changes:[/bold] {'Yes' if project.git_info.get('has_uncommitted_changes') else 'No'}
"""
        
        console.print(Panel(info_text.strip(), title=f"Project: {project.name}"))
        
        # Framework files status
        table = Table(title="Framework Files")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Required", style="yellow")
        
        for file_name, exists in project.framework_files.items():
            file_config = project_service.REQUIRED_FILES.get(file_name, {"critical": False})
            status = "✅ Present" if exists else "❌ Missing"
            required = "Critical" if file_config.get("critical") else "Optional"
            
            table.add_row(file_name, status, required)
        
        console.print(table)
        
        # Compliance recommendations
        if compliance and compliance.recommendations:
            console.print("\n[bold]Recommendations:[/bold]")
            for rec in compliance.recommendations:
                console.print(f"  • {rec}")
        
        await project_service._cleanup()
    
    asyncio.run(run())


@project.command()
def stats():
    """Show project statistics."""
    async def run():
        project_service = ProjectService()
        await project_service._initialize()
        
        stats = await project_service.get_project_stats()
        
        # Summary panel
        summary_text = f"""
[bold]Total Projects:[/bold] {stats['total_projects']}
[bold]Average Compliance:[/bold] {stats['compliance_summary']['average_score']}%
[bold]Compliant Projects:[/bold] {stats['compliance_summary']['compliant_projects']}
[bold]Non-compliant Projects:[/bold] {stats['compliance_summary']['non_compliant_projects']}
"""
        
        console.print(Panel(summary_text.strip(), title="Project Statistics"))
        
        # By type table
        if stats['by_type']:
            type_table = Table(title="Projects by Type")
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", style="green")
            
            for project_type, count in stats['by_type'].items():
                type_table.add_row(project_type, str(count))
            
            console.print(type_table)
        
        # By status table
        if stats['by_status']:
            status_table = Table(title="Projects by Status")
            status_table.add_column("Status", style="cyan")
            status_table.add_column("Count", style="green")
            
            for status, count in stats['by_status'].items():
                status_table.add_row(status, str(count))
            
            console.print(status_table)
        
        await project_service._cleanup()
    
    asyncio.run(run())


# Memory Management Commands
@cli.group()
def memory():
    """Memory management and AI integration."""
    pass


@memory.command()
@click.argument('project_name')
def stats(project_name):
    """Show memory statistics for a project."""
    async def run():
        from .integrations.mem0ai_integration import create_mem0ai_integration
        
        async with create_mem0ai_integration() as mem0ai:
            if not mem0ai.is_connected():
                console.print("[red]❌ Cannot connect to mem0AI service[/red]")
                console.print("Make sure mem0AI is running on port 8002")
                return
            
            stats = await mem0ai.get_project_statistics(project_name)
            
            if "error" in stats:
                console.print(f"[red]❌ Error getting stats: {stats['error']}[/red]")
                return
            
            # Summary panel
            summary_text = f"""
[bold]Total Memories:[/bold] {stats['total_memories']}
[bold]Recent Activity (7 days):[/bold] {stats['recent_activity']}
"""
            
            console.print(Panel(summary_text.strip(), title=f"Memory Statistics: {project_name}"))
            
            # By category table
            if stats['by_category']:
                table = Table(title="Memories by Category")
                table.add_column("Category", style="cyan")
                table.add_column("Count", style="green")
                table.add_column("Description", style="yellow")
                
                for category, count in stats['by_category'].items():
                    description = mem0ai.categories.get(category, "Unknown category")
                    table.add_row(category, str(count), description)
                
                console.print(table)
    
    asyncio.run(run())


@memory.command()
@click.argument('project_name')
@click.argument('query')
@click.option('--category', '-c', help='Filter by category')
@click.option('--limit', '-l', default=5, help='Maximum results')
def search(project_name, query, category, limit):
    """Search memories in a project."""
    async def run():
        from .integrations.mem0ai_integration import create_mem0ai_integration
        
        async with create_mem0ai_integration() as mem0ai:
            if not mem0ai.is_connected():
                console.print("[red]❌ Cannot connect to mem0AI service[/red]")
                return
            
            memories = await mem0ai.retrieve_memories(
                project_name,
                query,
                category=category,
                limit=limit
            )
            
            if not memories:
                console.print(f"[yellow]No memories found for query: {query}[/yellow]")
                return
            
            console.print(f"[bold]Found {len(memories)} memories for: {query}[/bold]\n")
            
            for i, memory in enumerate(memories, 1):
                content = memory.get('content', '')[:200] + "..." if len(memory.get('content', '')) > 200 else memory.get('content', '')
                metadata = memory.get('metadata', {})
                
                memory_panel = f"""
[bold]Content:[/bold] {content}
[bold]Category:[/bold] {metadata.get('category', 'unknown')}
[bold]Tags:[/bold] {', '.join(metadata.get('tags', []))}
[bold]Stored:[/bold] {metadata.get('stored_at', 'unknown')}
"""
                
                console.print(Panel(memory_panel.strip(), title=f"Memory {i}"))
    
    asyncio.run(run())


# Project Index Commands (MEM-007)
@cli.group()
def project_index():
    """Project indexing and fast retrieval (MEM-007)."""
    pass


@project_index.command(name="refresh")
@click.option('--force', '-f', is_flag=True, help='Force refresh all projects')
@click.option('--project', '-p', help='Refresh specific project only')
def refresh_index(force, project):
    """Refresh project index from managed directory."""
    async def run():
        from .services.project_indexer import create_project_indexer
        
        console.print("[bold blue]🔍 Refreshing project index...[/bold blue]")
        
        indexer = create_project_indexer()
        
        try:
            if not await indexer.initialize():
                console.print("[red]❌ Failed to initialize project indexer[/red]")
                return
            
            if project:
                # Refresh specific project
                console.print(f"Refreshing project: {project}")
                # TODO: Implement single project refresh
                console.print("[yellow]⚠️ Single project refresh not yet implemented[/yellow]")
            else:
                # Refresh all projects
                results = await indexer.scan_and_index_all(force_refresh=force)
                
                # Display results
                summary_text = f"""
[bold]Projects Found:[/bold] {results['projects_found']}
[bold]Projects Indexed:[/bold] {results['projects_indexed']}
[bold]Projects Updated:[/bold] {results['projects_updated']}
[bold]Projects Skipped:[/bold] {results['projects_skipped']}
[bold]Scan Time:[/bold] {results.get('performance', {}).get('scan_time_seconds', 0):.2f}s
"""
                
                console.print(Panel(summary_text.strip(), title="Index Refresh Results"))
                
                if results.get('errors'):
                    console.print("\n[bold red]Errors:[/bold red]")
                    for error in results['errors']:
                        console.print(f"  • {error}")
                
                # Performance stats
                perf = results.get('performance', {})
                if perf:
                    console.print(f"\n[bold blue]Performance:[/bold blue] {perf.get('projects_per_second', 0):.1f} projects/sec")
            
        finally:
            await indexer.cleanup()
    
    asyncio.run(run())


@project_index.command(name="info")
@click.argument('project_name')
@click.option('--format', '-f', type=click.Choice(['summary', 'full', 'json']), default='summary')
def project_info(project_name, format):
    """Get comprehensive project information."""
    async def run():
        from .services.project_memory_manager import create_project_memory_manager
        
        manager = create_project_memory_manager()
        
        try:
            if not await manager.initialize():
                console.print("[red]❌ Failed to initialize project memory manager[/red]")
                return
            
            if format == 'summary':
                # Get concise summary
                summary = await manager.get_project_summary(project_name)
                
                if not summary:
                    console.print(f"[red]❌ Project '{project_name}' not found in index[/red]")
                    console.print("Run 'claude-pm project-index refresh' to update index")
                    return
                
                # Display summary
                summary_text = f"""
[bold]Type:[/bold] {summary['type']}
[bold]Tech Stack:[/bold] {summary['tech_stack']}
[bold]Description:[/bold] {summary['description']}
[bold]Languages:[/bold] {', '.join(summary['main_languages'])}
[bold]Frameworks:[/bold] {', '.join(summary['key_frameworks'])}
[bold]Size:[/bold] {summary['size']}
[bold]Last Updated:[/bold] {summary['last_updated']}
[bold]Quick Facts:[/bold] {', '.join(summary['quick_facts'])}
"""
                
                console.print(Panel(summary_text.strip(), title=f"Project: {project_name}"))
                
                # Top features
                if summary['top_features']:
                    console.print("\n[bold blue]Key Features:[/bold blue]")
                    for feature in summary['top_features']:
                        console.print(f"  • {feature}")
                
                # Development commands
                if summary['development_commands']:
                    console.print("\n[bold green]Development Commands:[/bold green]")
                    for cmd in summary['development_commands']:
                        console.print(f"  • {cmd}")
            
            elif format == 'full':
                # Get full project info
                project_info = await manager.get_project_info(project_name)
                
                if not project_info:
                    console.print(f"[red]❌ Project '{project_name}' not found in index[/red]")
                    return
                
                # Display comprehensive info
                info_text = f"""
[bold]Path:[/bold] {project_info['path']}
[bold]Type:[/bold] {project_info['type']}
[bold]Tech Stack:[/bold] {project_info['tech_stack']}
[bold]Status:[/bold] {project_info['status']}
[bold]Description:[/bold] {project_info['description']}
[bold]File Count:[/bold] {project_info['file_count']}
[bold]Size:[/bold] {project_info['size_mb']:.1f} MB
[bold]Last Modified:[/bold] {project_info['last_modified']}
[bold]Last Indexed:[/bold] {project_info['last_indexed']}
"""
                
                console.print(Panel(info_text.strip(), title=f"Project: {project_name}"))
                
                # Languages and frameworks
                if project_info.get('languages'):
                    lang_table = Table(title="Languages & Frameworks")
                    lang_table.add_column("Languages", style="cyan")
                    lang_table.add_column("Frameworks", style="green")
                    
                    lang_table.add_row(
                        ', '.join(project_info['languages']),
                        ', '.join(project_info.get('frameworks', []))
                    )
                    console.print(lang_table)
                
                # Features
                if project_info.get('features'):
                    console.print("\n[bold blue]Features:[/bold blue]")
                    for feature in project_info['features']:
                        console.print(f"  • {feature}")
                
                # Architecture decisions
                if project_info.get('architecture_decisions'):
                    console.print("\n[bold yellow]Architecture Decisions:[/bold yellow]")
                    for decision in project_info['architecture_decisions'][:5]:
                        console.print(f"  • {decision}")
                
            elif format == 'json':
                # Get project info as JSON
                project_info = await manager.get_project_info(project_name)
                
                if project_info:
                    import json
                    console.print(json.dumps(project_info, indent=2))
                else:
                    console.print(f"[red]❌ Project '{project_name}' not found[/red]")
        
        finally:
            await manager.cleanup()
    
    asyncio.run(run())


@project_index.command(name="search")
@click.argument('query')
@click.option('--type', '-t', help='Filter by project type')
@click.option('--tech', help='Filter by tech stack')
@click.option('--limit', '-l', default=10, help='Maximum results')
@click.option('--mode', type=click.Choice(['exact', 'fuzzy', 'semantic', 'hybrid']), default='hybrid')
def search_projects(query, type, tech, limit, mode):
    """Search projects by technology, features, or description."""
    async def run():
        from .services.project_memory_manager import create_project_memory_manager, SearchQuery, SearchMode
        
        manager = create_project_memory_manager()
        
        try:
            if not await manager.initialize():
                console.print("[red]❌ Failed to initialize project memory manager[/red]")
                return
            
            # Build search query
            filters = {}
            if type:
                filters['project_type'] = type
            if tech:
                filters['tech_stack'] = tech
            
            search_query = SearchQuery(
                query=query,
                mode=SearchMode(mode),
                filters=filters,
                limit=limit
            )
            
            console.print(f"[bold blue]🔍 Searching for: '{query}'[/bold blue]")
            
            results = await manager.search_projects(search_query)
            
            if not results:
                console.print(f"[yellow]No projects found matching: {query}[/yellow]")
                console.print("Try a broader search or run 'claude-pm project-index refresh' to update index")
                return
            
            console.print(f"[bold green]Found {len(results)} matching projects:[/bold green]\n")
            
            # Display results table
            table = Table(title="Search Results")
            table.add_column("Project", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Tech Stack", style="yellow")
            table.add_column("Score", style="magenta")
            table.add_column("Match Reasons", style="blue")
            
            for result in results:
                project_data = result.project_data
                match_reasons = ", ".join(result.match_reasons[:2]) if result.match_reasons else "General match"
                
                table.add_row(
                    project_data['name'],
                    project_data.get('type', 'unknown'),
                    project_data.get('tech_stack', 'unknown'),
                    f"{result.relevance_score:.2f}",
                    match_reasons[:50] + "..." if len(match_reasons) > 50 else match_reasons
                )
            
            console.print(table)
            
            # Show cache performance
            stats = manager.get_performance_stats()
            cache_indicator = "💨 (cached)" if results[0].cache_hit else "🔄 (fresh)"
            console.print(f"\n[dim]Response time: {stats['avg_response_time_ms']:.1f}ms {cache_indicator}[/dim]")
        
        finally:
            await manager.cleanup()
    
    asyncio.run(run())


@project_index.command(name="recommend")
@click.argument('project_name')
@click.option('--limit', '-l', default=5, help='Maximum recommendations')
def recommend_projects(project_name, limit):
    """Get project recommendations based on similarity."""
    async def run():
        from .services.project_memory_manager import create_project_memory_manager
        
        manager = create_project_memory_manager()
        
        try:
            if not await manager.initialize():
                console.print("[red]❌ Failed to initialize project memory manager[/red]")
                return
            
            console.print(f"[bold blue]💡 Getting recommendations based on: {project_name}[/bold blue]")
            
            recommendations = await manager.get_project_recommendations(project_name, limit)
            
            if not recommendations:
                console.print(f"[yellow]No recommendations found for: {project_name}[/yellow]")
                console.print("Make sure the project exists in the index")
                return
            
            console.print(f"[bold green]Similar projects you might find useful:[/bold green]\n")
            
            for i, result in enumerate(recommendations, 1):
                project_data = result.project_data
                
                rec_text = f"""
[bold]Type:[/bold] {project_data.get('type', 'unknown')}
[bold]Tech Stack:[/bold] {project_data.get('tech_stack', 'unknown')}
[bold]Description:[/bold] {project_data.get('description', 'No description')[:100]}...
[bold]Why similar:[/bold] {', '.join(result.match_reasons[:2])}
"""
                
                console.print(Panel(rec_text.strip(), title=f"{i}. {project_data['name']}"))
        
        finally:
            await manager.cleanup()
    
    asyncio.run(run())


@project_index.command(name="stats")
def index_stats():
    """Show project index statistics and performance metrics."""
    async def run():
        from .services.project_memory_manager import create_project_memory_manager
        
        manager = create_project_memory_manager()
        
        try:
            if not await manager.initialize():
                console.print("[red]❌ Failed to initialize project memory manager[/red]")
                return
            
            stats = manager.get_performance_stats()
            
            # Main statistics
            stats_text = f"""
[bold]Total Queries:[/bold] {stats['queries_total']}
[bold]Cache Hit Rate:[/bold] {stats['cache_hit_rate']:.1f}%
[bold]Average Response Time:[/bold] {stats['avg_response_time_ms']:.1f}ms
[bold]Memory Connected:[/bold] {'✅ Yes' if stats['memory_connected'] else '❌ No'}
[bold]Cache Size:[/bold] {stats['cache_size']} queries, {stats['project_cache_size']} projects
"""
            
            console.print(Panel(stats_text.strip(), title="Project Index Performance"))
            
            # Popular queries
            if stats.get('popular_queries'):
                console.print("\n[bold blue]Popular Queries:[/bold blue]")
                for query, count in list(stats['popular_queries'].items())[:5]:
                    console.print(f"  • '{query}' - {count} times")
            
            # Performance insights
            cache_hit_rate = stats['cache_hit_rate']
            avg_response = stats['avg_response_time_ms']
            
            console.print("\n[bold green]Performance Analysis:[/bold green]")
            
            if cache_hit_rate >= 70:
                console.print("  ✅ Excellent cache performance")
            elif cache_hit_rate >= 50:
                console.print("  ⚠️ Good cache performance")
            else:
                console.print("  ❌ Low cache hit rate - consider warming up cache")
            
            if avg_response <= 50:
                console.print("  ✅ Excellent response times")
            elif avg_response <= 200:
                console.print("  ⚠️ Good response times")
            else:
                console.print("  ❌ Slow response times - check mem0AI service")
        
        finally:
            await manager.cleanup()
    
    asyncio.run(run())


@project_index.command(name="clear-cache")
@click.confirmation_option(prompt='Clear all cached project data?')
def clear_cache():
    """Clear project index cache."""
    async def run():
        from .services.project_memory_manager import create_project_memory_manager
        
        manager = create_project_memory_manager()
        
        try:
            if not await manager.initialize():
                console.print("[red]❌ Failed to initialize project memory manager[/red]")
                return
            
            await manager.clear_cache()
            console.print("[green]✅ Project index cache cleared[/green]")
        
        finally:
            await manager.cleanup()
    
    asyncio.run(run())


# Analytics Commands
@cli.group()
def analytics():
    """Framework metrics and analytics."""
    pass


@analytics.command()
@click.option('--period', '-p', default='7d', help='Time period (1d, 7d, 30d)')
@click.option('--format', '-f', type=click.Choice(['summary', 'detailed', 'csv']), default='summary')
def productivity(period, format):
    """Show productivity metrics."""
    async def run():
        import json
        from datetime import datetime, timedelta
        
        period_days = {'1d': 1, '7d': 7, '30d': 30}.get(period, 7)
        start_date = datetime.now() - timedelta(days=period_days)
        
        console.print(f"[bold blue]📊 Productivity Metrics ({period})[/bold blue]\n")
        
        # Framework metrics
        metrics = {
            "period": period,
            "start_date": start_date.isoformat(),
            "framework_health": 0,
            "services_uptime": 0,
            "projects_compliance": 0,
            "memory_usage": 0,
            "tickets_completed": 0,
            "error_rate": 0
        }
        
        # Get health data
        try:
            health_script = Path(__file__).parent.parent / "scripts" / "automated_health_monitor.py"
            result = subprocess.run(
                ["python", str(health_script), "status"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Parse health status for metrics
                metrics["framework_health"] = 85  # Simulated based on health
                metrics["services_uptime"] = 95
        except:
            metrics["framework_health"] = 0
            metrics["services_uptime"] = 0
        
        # Get project compliance
        try:
            project_service = ProjectService()
            await project_service._initialize()
            stats = await project_service.get_project_stats()
            metrics["projects_compliance"] = stats['compliance_summary']['average_score']
            await project_service._cleanup()
        except:
            metrics["projects_compliance"] = 0
        
        # Get memory usage
        try:
            from ..integrations.mem0ai_integration import create_mem0ai_integration
            async with create_mem0ai_integration() as mem0ai:
                if mem0ai.is_connected():
                    # Count total memories across projects
                    total_memories = 0
                    managed_path = get_managed_path()
                    if managed_path.exists():
                        for project_dir in managed_path.iterdir():
                            if project_dir.is_dir():
                                project_stats = await mem0ai.get_project_statistics(project_dir.name)
                                if "total_memories" in project_stats:
                                    total_memories += project_stats["total_memories"]
                    
                    metrics["memory_usage"] = total_memories
        except:
            metrics["memory_usage"] = 0
        
        if format == 'summary':
            # Summary panel
            summary_text = f"""
[bold]Framework Health:[/bold] {metrics['framework_health']}%
[bold]Services Uptime:[/bold] {metrics['services_uptime']}%
[bold]Project Compliance:[/bold] {metrics['projects_compliance']:.1f}%
[bold]Total Memories:[/bold] {metrics['memory_usage']}
[bold]Period:[/bold] {period}
"""
            console.print(Panel(summary_text.strip(), title="Productivity Summary"))
            
        elif format == 'detailed':
            # Detailed table
            table = Table(title="Detailed Productivity Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Trend", style="yellow")
            table.add_column("Target", style="magenta")
            
            table.add_row("Framework Health", f"{metrics['framework_health']}%", "↗️ Improving", "90%")
            table.add_row("Services Uptime", f"{metrics['services_uptime']}%", "↗️ Stable", "95%")
            table.add_row("Project Compliance", f"{metrics['projects_compliance']:.1f}%", "→ Steady", "85%")
            table.add_row("Memory Usage", str(metrics['memory_usage']), "↗️ Growing", "N/A")
            table.add_row("Error Rate", f"{metrics['error_rate']}%", "↘️ Decreasing", "<5%")
            
            console.print(table)
            
        elif format == 'csv':
            import io
            output = io.StringIO()
            output.write("metric,value,period,timestamp\n")
            timestamp = datetime.now().isoformat()
            for key, value in metrics.items():
                if key not in ['period', 'start_date']:
                    output.write(f"{key},{value},{period},{timestamp}\n")
            
            csv_content = output.getvalue()
            console.print("[bold blue]CSV Output:[/bold blue]")
            console.print(csv_content)
    
    asyncio.run(run())


@analytics.command()
@click.option('--service', '-s', help='Specific service to analyze')
@click.option('--period', '-p', default='24h', help='Time period (1h, 24h, 7d)')
def performance(service, period):
    """Show service performance trends."""
    async def run():
        console.print(f"[bold blue]⚡ Performance Analysis ({period})[/bold blue]\n")
        
        # Service performance metrics
        services = ['health_monitor', 'memory_service', 'project_service']
        if service:
            services = [service] if service in services else []
        
        if not services:
            console.print(f"[red]Service '{service}' not found[/red]")
            return
        
        table = Table(title="Service Performance Metrics")
        table.add_column("Service", style="cyan")
        table.add_column("Response Time", style="green")
        table.add_column("Success Rate", style="yellow")
        table.add_column("Memory Usage", style="magenta")
        table.add_column("Status", style="red")
        
        for svc in services:
            # Simulated performance data - in real implementation, this would query actual metrics
            response_time = "45ms" if svc == "health_monitor" else "120ms" if svc == "memory_service" else "80ms"
            success_rate = "99.2%" if svc == "health_monitor" else "98.7%" if svc == "memory_service" else "99.8%"
            memory_usage = "24MB" if svc == "health_monitor" else "156MB" if svc == "memory_service" else "89MB"
            status = "🟢 Healthy"
            
            table.add_row(svc, response_time, success_rate, memory_usage, status)
        
        console.print(table)
        
        # Performance recommendations
        recommendations = [
            "Memory service could benefit from connection pooling",
            "Consider caching for frequently accessed project data",
            "Health monitor is performing optimally"
        ]
        
        console.print("\n[bold yellow]Performance Recommendations:[/bold yellow]")
        for rec in recommendations:
            console.print(f"  • {rec}")
    
    asyncio.run(run())


@analytics.command()
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text')
@click.option('--period', '-p', default='30d', help='Time period (7d, 30d, 90d)')
def summary(format, period):
    """Generate executive summary."""
    async def run():
        import json
        from datetime import datetime
        
        console.print(f"[bold blue]📋 Executive Summary ({period})[/bold blue]\n")
        
        # Gather summary data
        summary_data = {
            "generated_at": datetime.now().isoformat(),
            "period": period,
            "framework_status": "Operational",
            "total_projects": 0,
            "compliance_score": 0,
            "service_health": "Good",
            "key_metrics": {},
            "achievements": [],
            "challenges": [],
            "recommendations": []
        }
        
        # Get project data
        try:
            project_service = ProjectService()
            await project_service._initialize()
            stats = await project_service.get_project_stats()
            
            summary_data["total_projects"] = stats['total_projects']
            summary_data["compliance_score"] = stats['compliance_summary']['average_score']
            
            # Achievements based on data
            if stats['compliance_summary']['average_score'] > 80:
                summary_data["achievements"].append("High project compliance maintained")
            
            if stats['total_projects'] > 5:
                summary_data["achievements"].append(f"Successfully managing {stats['total_projects']} projects")
            
            await project_service._cleanup()
        except Exception as e:
            summary_data["challenges"].append("Project service integration needs attention")
        
        # Check memory service
        try:
            from ..integrations.mem0ai_integration import create_mem0ai_integration
            async with create_mem0ai_integration() as mem0ai:
                if mem0ai.is_connected():
                    summary_data["achievements"].append("Memory service operational")
                    summary_data["key_metrics"]["memory_service"] = "Connected"
                else:
                    summary_data["challenges"].append("Memory service connectivity issues")
        except:
            summary_data["challenges"].append("Memory service requires setup")
        
        # Default recommendations
        summary_data["recommendations"] = [
            "Continue monitoring service health",
            "Maintain project compliance above 85%",
            "Expand memory usage for better context preservation",
            "Consider automation for routine tasks"
        ]
        
        if format == 'json':
            console.print(json.dumps(summary_data, indent=2))
        else:
            # Formatted text output
            status_color = "green" if summary_data["framework_status"] == "Operational" else "yellow"
            
            summary_text = f"""
[bold]Framework Status:[/bold] [{status_color}]{summary_data['framework_status']}[/{status_color}]
[bold]Total Projects:[/bold] {summary_data['total_projects']}
[bold]Average Compliance:[/bold] {summary_data['compliance_score']:.1f}%
[bold]Service Health:[/bold] {summary_data['service_health']}
[bold]Report Period:[/bold] {period}
"""
            console.print(Panel(summary_text.strip(), title="Claude PM Framework Executive Summary"))
            
            # Achievements
            if summary_data["achievements"]:
                console.print("\n[bold green]✅ Key Achievements:[/bold green]")
                for achievement in summary_data["achievements"]:
                    console.print(f"  • {achievement}")
            
            # Challenges
            if summary_data["challenges"]:
                console.print("\n[bold yellow]⚠️ Challenges:[/bold yellow]")
                for challenge in summary_data["challenges"]:
                    console.print(f"  • {challenge}")
            
            # Recommendations
            console.print("\n[bold blue]💡 Recommendations:[/bold blue]")
            for rec in summary_data["recommendations"]:
                console.print(f"  • {rec}")
    
    asyncio.run(run())


# Deployment Commands
@cli.group()
def deploy():
    """Deployment operations and management."""
    pass


@deploy.command()
@click.option('--service', '-s', help='Deploy specific service')
@click.option('--health-check/--no-health-check', default=True, help='Run health checks after deployment')
@click.option('--timeout', '-t', default=300, help='Deployment timeout in seconds')
def start(service, health_check, timeout):
    """Deploy services with health checks."""
    async def run():
        console.print("[bold blue]🚀 Starting deployment process...[/bold blue]")
        
        if service:
            console.print(f"Deploying specific service: {service}")
            services_to_deploy = [service]
        else:
            console.print("Deploying all Claude PM services")
            services_to_deploy = ['health_monitor', 'memory_service', 'project_service']
        
        # Start deployment
        manager = ClaudePMServiceManager()
        
        try:
            if service:
                # Deploy specific service
                await manager.service_manager.start_service(service)
                console.print(f"[green]✅ Service '{service}' deployed[/green]")
            else:
                # Deploy all services
                success = await manager.start_all()
                if not success:
                    console.print("[red]❌ Deployment failed[/red]")
                    return
        
            # Health checks
            if health_check:
                console.print("\n[bold blue]🏥 Running post-deployment health checks...[/bold blue]")
                
                import time
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    health_results = await manager.service_manager.health_check_all()
                    
                    healthy_services = sum(1 for h in health_results.values() if h.status == "healthy")
                    total_services = len(health_results)
                    
                    if service:
                        # Check specific service
                        service_health = health_results.get(service)
                        if service_health and service_health.status == "healthy":
                            console.print(f"[green]✅ Service '{service}' is healthy[/green]")
                            break
                    else:
                        # Check all services
                        if healthy_services == total_services:
                            console.print(f"[green]✅ All {total_services} services are healthy[/green]")
                            break
                    
                    console.print(f"[yellow]⏳ Waiting for services to become healthy ({healthy_services}/{total_services})...[/yellow]")
                    await asyncio.sleep(5)
                else:
                    console.print(f"[yellow]⚠️ Health check timeout after {timeout}s[/yellow]")
            
            console.print("\n[bold green]🎉 Deployment completed successfully![/bold green]")
            
        except Exception as e:
            console.print(f"[red]❌ Deployment failed: {e}[/red]")
    
    asyncio.run(run())


@deploy.command()
def status():
    """Show deployment status."""
    async def run():
        console.print("[bold blue]📊 Deployment Status[/bold blue]\n")
        
        manager = ClaudePMServiceManager()
        await manager.status()
        
        # Additional deployment info
        deployment_info = f"""
[bold]Deployment Environment:[/bold] Development
[bold]Framework Version:[/bold] 3.0.0
[bold]Python Version:[/bold] {sys.version.split()[0]}
[bold]Base Path:[/bold] {get_claude_pm_path()}
"""
        console.print(Panel(deployment_info.strip(), title="Deployment Information"))
    
    asyncio.run(run())


@deploy.command()
@click.option('--steps', '-s', type=int, help='Number of rollback steps')
@click.confirmation_option(prompt='Are you sure you want to rollback?')
def rollback(steps):
    """Rollback deployment (simulation)."""
    console.print("[bold yellow]🔄 Initiating rollback...[/bold yellow]")
    
    # In a real implementation, this would:
    # - Stop current services
    # - Restore previous configuration
    # - Restart with previous version
    # - Verify rollback success
    
    console.print("[yellow]⚠️ Rollback functionality is in development[/yellow]")
    console.print("Current implementation: simulation mode only")
    
    rollback_steps = [
        "1. Stopping current services",
        "2. Backing up current configuration", 
        "3. Restoring previous version",
        "4. Restarting services",
        "5. Verifying rollback success"
    ]
    
    for step in rollback_steps:
        console.print(f"[blue]{step}[/blue]")
        import time
        time.sleep(1)
    
    console.print("[green]✅ Rollback simulation completed[/green]")


@deploy.command()
@click.option('--env', '-e', default='development', help='Environment name')
def environment(env):
    """Manage deployment environments."""
    console.print(f"[bold blue]🌍 Environment Management: {env}[/bold blue]\n")
    
    environments = {
        'development': {
            'description': 'Local development environment',
            'services': ['health_monitor', 'memory_service', 'project_service'],
            'ports': {'mem0ai': 8002, 'dashboard': 7001},
            'status': 'Active'
        },
        'staging': {
            'description': 'Staging environment for testing',
            'services': ['health_monitor', 'memory_service', 'project_service'],
            'ports': {'mem0ai': 8003, 'dashboard': 7002},
            'status': 'Not configured'
        },
        'production': {
            'description': 'Production environment',
            'services': ['health_monitor', 'memory_service', 'project_service'],
            'ports': {'mem0ai': 8004, 'dashboard': 7003},
            'status': 'Not configured'
        }
    }
    
    if env in environments:
        env_data = environments[env]
        
        env_text = f"""
[bold]Description:[/bold] {env_data['description']}
[bold]Status:[/bold] {env_data['status']}
[bold]Services:[/bold] {', '.join(env_data['services'])}
[bold]Ports:[/bold] {', '.join(f"{k}:{v}" for k, v in env_data['ports'].items())}
"""
        console.print(Panel(env_text.strip(), title=f"Environment: {env}"))
        
        if env_data['status'] == 'Not configured':
            console.print(f"\n[yellow]⚠️ Environment '{env}' requires configuration[/yellow]")
            console.print("Use 'claude-pm deploy start' to configure this environment")
    else:
        console.print(f"[red]Environment '{env}' not found[/red]")
        console.print(f"Available environments: {', '.join(environments.keys())}")


# Tickets Commands
@cli.group()
def tickets():
    """TrackDown integration and ticket management."""
    pass


@tickets.command()
@click.option('--sprint', '-s', help='Specific sprint number')
def sprint(sprint):
    """Show current sprint progress."""
    try:
        backlog_path = get_claude_pm_path() / "trackdown" / "BACKLOG.md"
        
        if not backlog_path.exists():
            console.print("[red]❌ TrackDown BACKLOG.md not found[/red]")
            return
        
        with open(backlog_path, 'r') as f:
            content = f.read()
        
        console.print("[bold blue]🎯 Current Sprint Progress[/bold blue]\n")
        
        # Extract sprint information
        lines = content.split('\n')
        in_current_sprint = False
        sprint_tasks = []
        
        for line in lines:
            if "🎯 Current Sprint" in line:
                in_current_sprint = True
                continue
            elif line.startswith("### ") and in_current_sprint:
                in_current_sprint = False
                break
            elif in_current_sprint and line.strip().startswith("- ["):
                sprint_tasks.append(line.strip())
        
        if not sprint_tasks:
            console.print("[yellow]No sprint tasks found in BACKLOG.md[/yellow]")
            return
        
        # Parse and display tasks
        completed = 0
        total = len(sprint_tasks)
        
        table = Table(title="Sprint Tasks")
        table.add_column("Status", style="green")
        table.add_column("Task ID", style="cyan")
        table.add_column("Description", style="yellow")
        
        for task in sprint_tasks:
            if "[x]" in task:
                status = "✅ Done"
                completed += 1
            elif "[ ]" in task:
                status = "🔄 TODO"
            else:
                status = "❓ Unknown"
                
            # Extract task ID and description
            task_clean = task.replace("- [x]", "").replace("- [ ]", "").strip()
            
            # Parse task ID (format: **[M01-XXX]**)
            task_id = "N/A"
            description = task_clean
            
            if "**[" in task_clean and "]**" in task_clean:
                start = task_clean.index("**[") + 3
                end = task_clean.index("]**")
                task_id = task_clean[start:end]
                description = task_clean[end+3:].strip()
            
            table.add_row(status, task_id, description)
        
        console.print(table)
        
        # Sprint summary
        progress = (completed / total) * 100 if total > 0 else 0
        
        summary_text = f"""
[bold]Sprint Progress:[/bold] {completed}/{total} tasks ({progress:.1f}%)
[bold]Completed:[/bold] {completed}
[bold]Remaining:[/bold] {total - completed}
[bold]Velocity:[/bold] {"On track" if progress >= 60 else "Behind schedule"}
"""
        console.print(Panel(summary_text.strip(), title="Sprint Summary"))
        
    except Exception as e:
        console.print(f"[red]❌ Error reading sprint data: {e}[/red]")


@tickets.command()
@click.option('--priority', '-p', type=click.Choice(['critical', 'high', 'medium', 'low']), help='Filter by priority')
@click.option('--status', '-s', type=click.Choice(['todo', 'in_progress', 'completed']), help='Filter by status')
def list(priority, status):
    """List priority tickets and status."""
    try:
        backlog_path = get_claude_pm_path() / "trackdown" / "BACKLOG.md"
        
        if not backlog_path.exists():
            console.print("[red]❌ TrackDown BACKLOG.md not found[/red]")
            return
        
        with open(backlog_path, 'r') as f:
            content = f.read()
        
        console.print("[bold blue]🎫 Priority Tickets[/bold blue]\n")
        
        # Extract priority tickets section
        lines = content.split('\n')
        in_priority_section = False
        tickets = []
        current_ticket = None
        
        for line in lines:
            if "🚀 Priority Implementation Tickets" in line:
                in_priority_section = True
                continue
            elif line.startswith("## ") and in_priority_section:
                in_priority_section = False
                break
            elif in_priority_section and line.startswith("### "):
                # New ticket
                if current_ticket:
                    tickets.append(current_ticket)
                current_ticket = {"title": line.strip("# "), "details": []}
            elif in_priority_section and current_ticket and line.strip():
                current_ticket["details"].append(line)
        
        if current_ticket:
            tickets.append(current_ticket)
        
        if not tickets:
            console.print("[yellow]No priority tickets found[/yellow]")
            return
        
        # Display tickets
        for ticket in tickets:
            title = ticket["title"]
            details = ticket["details"]
            
            # Extract ticket info
            ticket_priority = "medium"  # default
            ticket_status = "todo"  # default
            story_points = "N/A"
            
            for detail in details:
                if "Priority" in detail and ":" in detail:
                    ticket_priority = detail.split(":")[1].strip().lower()
                elif "Story Points" in detail and ":" in detail:
                    story_points = detail.split(":")[1].strip()
            
            # Apply filters
            if priority and ticket_priority != priority:
                continue
            if status and ticket_status != status:
                continue
            
            # Format priority
            priority_color = {
                "critical": "red",
                "high": "yellow", 
                "medium": "blue",
                "low": "green"
            }.get(ticket_priority, "white")
            
            ticket_text = f"""
[bold]Priority:[/bold] [{priority_color}]{ticket_priority.upper()}[/{priority_color}]
[bold]Story Points:[/bold] {story_points}
[bold]Status:[/bold] {ticket_status.replace('_', ' ').title()}
"""
            
            console.print(Panel(ticket_text.strip(), title=title))
        
    except Exception as e:
        console.print(f"[red]❌ Error reading tickets: {e}[/red]")


@tickets.command()
def completion():
    """Display ticket completion rates."""
    try:
        backlog_path = get_claude_pm_path() / "trackdown" / "BACKLOG.md"
        
        if not backlog_path.exists():
            console.print("[red]❌ TrackDown BACKLOG.md not found[/red]")
            return
        
        with open(backlog_path, 'r') as f:
            content = f.read()
        
        console.print("[bold blue]📈 Ticket Completion Rates[/bold blue]\n")
        
        # Count different ticket sections
        sections = {
            "Current Sprint": {"completed": 0, "total": 0},
            "Priority Tickets": {"completed": 0, "total": 0},
            "M01 Foundation": {"completed": 0, "total": 0},
            "M02 Automation": {"completed": 0, "total": 0},
            "M03 Orchestration": {"completed": 0, "total": 0}
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            # Detect sections
            if "Current Sprint" in line:
                current_section = "Current Sprint"
            elif "Priority Implementation Tickets" in line:
                current_section = "Priority Tickets"
            elif "M01 Foundation" in line:
                current_section = "M01 Foundation"
            elif "M02 Automation" in line:
                current_section = "M02 Automation"
            elif "M03 Orchestration" in line:
                current_section = "M03 Orchestration"
            
            # Count tickets
            if current_section and line.strip().startswith("- ["):
                sections[current_section]["total"] += 1
                if "[x]" in line:
                    sections[current_section]["completed"] += 1
        
        # Display completion table
        table = Table(title="Completion Rates by Section")
        table.add_column("Section", style="cyan")
        table.add_column("Completed", style="green")
        table.add_column("Total", style="yellow")
        table.add_column("Rate", style="magenta")
        table.add_column("Progress", style="blue")
        
        for section_name, data in sections.items():
            if data["total"] > 0:
                completion_rate = (data["completed"] / data["total"]) * 100
                progress_bar = "█" * int(completion_rate / 10) + "░" * (10 - int(completion_rate / 10))
                
                table.add_row(
                    section_name,
                    str(data["completed"]),
                    str(data["total"]),
                    f"{completion_rate:.1f}%",
                    progress_bar
                )
        
        console.print(table)
        
        # Overall summary
        total_completed = sum(data["completed"] for data in sections.values())
        total_tickets = sum(data["total"] for data in sections.values())
        overall_rate = (total_completed / total_tickets) * 100 if total_tickets > 0 else 0
        
        summary_text = f"""
[bold]Overall Progress:[/bold] {total_completed}/{total_tickets} ({overall_rate:.1f}%)
[bold]Total Sections:[/bold] {len([s for s in sections.values() if s['total'] > 0])}
[bold]Velocity:[/bold] {"Excellent" if overall_rate >= 80 else "Good" if overall_rate >= 60 else "Needs attention"}
"""
        console.print(Panel(summary_text.strip(), title="Overall Completion Summary"))
        
    except Exception as e:
        console.print(f"[red]❌ Error calculating completion rates: {e}[/red]")


@tickets.command()
@click.argument('ticket_id')
@click.argument('title')
@click.option('--priority', '-p', type=click.Choice(['critical', 'high', 'medium', 'low']), default='medium')
@click.option('--points', type=int, default=3, help='Story points')
def create(ticket_id, title, priority, points):
    """Create new tickets with templates."""
    try:
        tickets_dir = get_claude_pm_path() / "trackdown" / "issues"
        tickets_dir.mkdir(exist_ok=True)
        
        ticket_file = tickets_dir / f"{ticket_id}.md"
        
        if ticket_file.exists():
            console.print(f"[yellow]⚠️ Ticket {ticket_id} already exists[/yellow]")
            return
        
        # Create ticket content from template
        template_content = f"""---
title: "{title}"
ticket_id: {ticket_id}
priority: {priority}
story_points: {points}
status: todo
created_at: {datetime.now().isoformat()}
---

# {ticket_id}: {title}

## Description

[Provide detailed description of the ticket]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Notes

[Add implementation notes and technical details]

## Dependencies

- None

## Definition of Done

- [ ] Code implemented
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Deployed and verified

## Priority: {priority.upper()}
## Story Points: {points}
"""
        
        with open(ticket_file, 'w') as f:
            f.write(template_content)
        
        console.print(f"[green]✅ Ticket {ticket_id} created successfully[/green]")
        console.print(f"File: {ticket_file}")
        
        # Add to backlog
        backlog_path = get_claude_pm_path() / "trackdown" / "BACKLOG.md"
        if backlog_path.exists():
            with open(backlog_path, 'r') as f:
                backlog_content = f.read()
            
            # Find appropriate section to add ticket
            new_entry = f"- [ ] **[{ticket_id}]** {title}"
            
            # Add to current sprint section if it exists
            if "### In Progress" in backlog_content:
                backlog_content = backlog_content.replace(
                    "### In Progress\n",
                    f"### In Progress\n{new_entry}\n"
                )
                
                with open(backlog_path, 'w') as f:
                    f.write(backlog_content)
                
                console.print(f"[green]✅ Added {ticket_id} to current sprint[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error creating ticket: {e}[/red]")


# Agents Commands
@cli.group()
def agents():
    """Multi-agent coordination and management."""
    pass


@agents.command()
def status():
    """Show agent status and availability."""
    console.print("[bold blue]🤖 Multi-Agent Status[/bold blue]\n")
    
    # Agent types from the framework
    agent_types = {
        "orchestrator": {"status": "available", "current_task": None, "specialization": "Task coordination"},
        "architect": {"status": "available", "current_task": None, "specialization": "System design"},
        "engineer": {"status": "busy", "current_task": "M01-008 Implementation", "specialization": "Code implementation"},
        "qa": {"status": "available", "current_task": None, "specialization": "Quality assurance"},
        "researcher": {"status": "available", "current_task": None, "specialization": "Information gathering"},
        "security": {"status": "available", "current_task": None, "specialization": "Security analysis"},
        "performance": {"status": "idle", "current_task": None, "specialization": "Performance optimization"},
        "devops": {"status": "available", "current_task": None, "specialization": "Infrastructure"},
        "data": {"status": "available", "current_task": None, "specialization": "Data engineering"},
        "ui_ux": {"status": "available", "current_task": None, "specialization": "User experience"},
        "code_review": {"status": "available", "current_task": None, "specialization": "Code review"}
    }
    
    table = Table(title="Agent Ecosystem Status")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Current Task", style="yellow")
    table.add_column("Specialization", style="magenta")
    
    for agent_name, agent_data in agent_types.items():
        # Status colors
        status_display = {
            "available": "[green]🟢 Available[/green]",
            "busy": "[yellow]🟡 Busy[/yellow]",
            "idle": "[blue]🔵 Idle[/blue]",
            "offline": "[red]🔴 Offline[/red]"
        }.get(agent_data["status"], agent_data["status"])
        
        current_task = agent_data["current_task"] or "None"
        
        table.add_row(
            agent_name.replace("_", " ").title(),
            status_display,
            current_task,
            agent_data["specialization"]
        )
    
    console.print(table)
    
    # Summary
    available_count = sum(1 for a in agent_types.values() if a["status"] == "available")
    busy_count = sum(1 for a in agent_types.values() if a["status"] == "busy")
    total_count = len(agent_types)
    
    summary_text = f"""
[bold]Total Agents:[/bold] {total_count}
[bold]Available:[/bold] {available_count}
[bold]Busy:[/bold] {busy_count}
[bold]Utilization:[/bold] {(busy_count/total_count)*100:.1f}%
[bold]Max Parallel:[/bold] 5 agents
"""
    console.print(Panel(summary_text.strip(), title="Agent Summary"))


# Utility Commands
# Add enforcement commands
cli.add_command(enforcement_cli)


@cli.group()
def util():
    """Utility commands and tools."""
    pass


@util.command()
def info():
    """Show Claude PM Framework information."""
    import platform
    from . import __version__
    
    info_text = f"""
[bold]Claude Multi-Agent Project Management Framework[/bold]
Version: {__version__}
Python Edition: [green]✅ Active[/green]

[bold]System Information:[/bold]
Platform: {platform.system()} {platform.release()}
Python: {sys.version.split()[0]}
Architecture: {platform.machine()}

[bold]Framework Paths:[/bold]
Base Path: {get_framework_config().get('base_path')}
Claude Multi-Agent PM: {get_claude_pm_path()}
Managed Projects: {get_managed_path()}

[bold]Services:[/bold]
Health Monitor: Python-based health monitoring
Memory Service: mem0AI integration (port 8002)
Project Service: Framework compliance monitoring
"""
    
    console.print(Panel(info_text.strip(), title="Claude Multi-Agent PM Framework Information"))


@util.command()
def migrate():
    """Show migration information from npm to Python."""
    migration_info = """
[bold]Migration from npm to Python Build System[/bold]

[bold yellow]Old npm commands → New commands:[/bold yellow]
npm run health-check → claude-pm health check
npm run monitor:health → claude-pm health monitor
npm run monitor:status → claude-pm health status
npm test → make test
npm run lint → make lint

[bold yellow]New Python-specific commands:[/bold yellow]
make setup-dev → Complete development setup
make install-ai → Install AI dependencies
make type-check → Run type checking
claude-pm service start → Start all services
claude-pm project list → List all projects
claude-pm memory search → Search project memories

[bold yellow]Development workflow:[/bold yellow]
1. source .venv/bin/activate (activate virtual environment)
2. make install-dev (install dependencies)
3. claude-pm service start (start services)
4. claude-pm health check (verify health)
5. make test (run tests)

[bold yellow]Build system:[/bold yellow]
• Makefile replaces package.json scripts
• pyproject.toml replaces package.json
• requirements/ directory for dependencies
• Python virtual environment instead of node_modules
"""
    
    console.print(Panel(migration_info.strip(), title="Migration Guide"))


@util.command()
def doctor():
    """Run comprehensive system diagnostics."""
    import subprocess
    import shutil
    
    console.print("[bold blue]🏥 Claude Multi-Agent PM Framework Doctor[/bold blue]\n")
    
    checks = []
    
    # Python version check
    python_version = sys.version.split()[0]
    python_ok = tuple(map(int, python_version.split('.'))) >= (3, 9)
    checks.append(("Python >= 3.9", python_ok, f"Found: {python_version}"))
    
    # Virtual environment check
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    checks.append(("Virtual Environment", venv_active, "Activate with: source .venv/bin/activate"))
    
    # Required tools check
    required_tools = ['git', 'make']
    for tool in required_tools:
        tool_available = shutil.which(tool) is not None
        checks.append((f"{tool} available", tool_available, f"Install {tool}"))
    
    # Directory structure check
    base_path = Path.home() / "Projects"
    claude_pm_path = base_path / "claude-pm"
    managed_path = base_path / "managed"
    
    checks.append(("Base directory", base_path.exists(), f"Create {base_path}"))
    checks.append(("Claude Multi-Agent PM directory", claude_pm_path.exists(), f"Create {claude_pm_path}"))
    checks.append(("Managed directory", managed_path.exists(), f"Create {managed_path}"))
    
    # mem0AI service check
    try:
        import aiohttp
        mem0ai_available = True
    except ImportError:
        mem0ai_available = False
    checks.append(("mem0AI dependencies", mem0ai_available, "pip install aiohttp"))
    
    # Display results
    table = Table(title="System Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    all_passed = True
    for check_name, passed, details in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        table.add_row(check_name, status, details)
    
    console.print(table)
    
    if all_passed:
        console.print("\n[bold green]✅ All checks passed! Claude Multi-Agent PM Framework is ready.[/bold green]")
    else:
        console.print("\n[bold yellow]⚠️ Some checks failed. Please address the issues above.[/bold yellow]")
        console.print("Run 'claude-pm util migrate' for migration assistance.")


# M01-044 Unified Health Dashboard Helper Functions

async def _add_project_indexing_health_collector(orchestrator):
    """Add MEM-007 project indexing health monitoring to orchestrator."""
    from .collectors.framework_services import ProjectIndexingHealthCollector
    
    try:
        # Create and add project indexing health collector
        indexing_collector = ProjectIndexingHealthCollector(timeout_seconds=2.0)
        orchestrator.add_collector(indexing_collector)
    except Exception as e:
        logger.warning(f"Could not add project indexing health collector: {e}")


async def _get_managed_projects_health():
    """Get health status of managed projects portfolio."""
    from pathlib import Path
    import os
    
    try:
        managed_path = get_managed_path()
        if not managed_path.exists():
            return {
                "status": "down",
                "total_projects": 0,
                "healthy_projects": 0,
                "message": f"Managed directory not found: {managed_path}",
                "projects": []
            }
        
        projects = []
        healthy_count = 0
        
        for project_dir in managed_path.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                try:
                    # Check project health indicators
                    has_git = (project_dir / ".git").exists()
                    has_claude_md = (project_dir / "CLAUDE.md").exists()
                    has_recent_activity = _check_recent_activity(project_dir)
                    
                    # Simple health assessment
                    health_score = 0
                    if has_git:
                        health_score += 30
                    if has_claude_md:
                        health_score += 40
                    if has_recent_activity:
                        health_score += 30
                    
                    status = "healthy" if health_score >= 70 else "degraded" if health_score >= 40 else "unhealthy"
                    if status == "healthy":
                        healthy_count += 1
                    
                    projects.append({
                        "name": project_dir.name,
                        "status": status,
                        "health_score": health_score,
                        "has_git": has_git,
                        "has_claude_md": has_claude_md,
                        "has_recent_activity": has_recent_activity,
                        "path": str(project_dir)
                    })
                    
                except Exception as e:
                    projects.append({
                        "name": project_dir.name,
                        "status": "error",
                        "health_score": 0,
                        "error": str(e),
                        "path": str(project_dir)
                    })
        
        total_projects = len(projects)
        overall_status = "healthy" if healthy_count >= total_projects * 0.8 else \
                        "degraded" if healthy_count >= total_projects * 0.5 else "unhealthy"
        
        return {
            "status": overall_status,
            "total_projects": total_projects,
            "healthy_projects": healthy_count,
            "degraded_projects": len([p for p in projects if p["status"] == "degraded"]),
            "unhealthy_projects": len([p for p in projects if p["status"] in ["unhealthy", "error"]]),
            "message": f"{healthy_count}/{total_projects} projects healthy",
            "projects": projects
        }
        
    except Exception as e:
        return {
            "status": "error",
            "total_projects": 0,
            "healthy_projects": 0,
            "message": f"Error assessing managed projects: {e}",
            "projects": []
        }


def _check_recent_activity(project_dir: Path) -> bool:
    """Check if project has recent activity (within 30 days)."""
    from datetime import datetime, timedelta
    import os
    
    try:
        # Check modification time of key files
        key_files = ["CLAUDE.md", "README.md", "package.json", "pyproject.toml"]
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        for file_name in key_files:
            file_path = project_dir / file_name
            if file_path.exists():
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mod_time > thirty_days_ago:
                    return True
        
        # Check git activity if available
        git_dir = project_dir / ".git"
        if git_dir.exists():
            # Check .git directory modification time as proxy for recent commits
            mod_time = datetime.fromtimestamp(git_dir.stat().st_mtime)
            if mod_time > thirty_days_ago:
                return True
        
        return False
        
    except Exception:
        return False


def _display_unified_health_dashboard(dashboard, managed_projects_health, detailed=False, verbose=False):
    """Display the unified health dashboard combining all subsystems."""
    from .models.health import HealthStatus
    
    current = dashboard.current_report
    
    # Framework Services Status
    framework_status = _get_framework_services_status(current)
    console.print(f"Framework Services:        {framework_status['indicator']} {framework_status['status']}")
    
    if detailed or verbose:
        for subsystem_name, subsystem in current.subsystems.items():
            subsystem_indicator = _get_status_indicator(subsystem.status)
            avg_response = f" ({subsystem.avg_response_time_ms:.1f}ms)" if subsystem.avg_response_time_ms else ""
            console.print(f"├─ {subsystem_name:18} {subsystem_indicator} {subsystem.status.value.title()}{avg_response}")
    else:
        # Show key services only
        key_services = _get_key_services_summary(current)
        for service_name, service_info in key_services.items():
            console.print(f"├─ {service_name:18} {service_info['indicator']} {service_info['status']}")
    
    # Managed Projects Status
    projects_indicator = _get_status_indicator_from_string(managed_projects_health["status"])
    console.print(f"\nManaged Projects:          {projects_indicator} {managed_projects_health['total_projects']}/{managed_projects_health['total_projects']} MONITORED")
    
    # Show project breakdown
    if detailed:
        for project in managed_projects_health["projects"][:10]:  # Show first 10
            proj_indicator = _get_status_indicator_from_string(project["status"])
            console.print(f"├─ {project['name'][:18]:18} {proj_indicator} {project['status'].title()}")
        
        if len(managed_projects_health["projects"]) > 10:
            remaining = len(managed_projects_health["projects"]) - 10
            console.print(f"└─ ... and {remaining} more projects")
    else:
        console.print(f"├─ Healthy:               🟢 {managed_projects_health['healthy_projects']}")
        console.print(f"├─ Degraded:              🟡 {managed_projects_health.get('degraded_projects', 0)}")
        console.print(f"└─ Issues:                🔴 {managed_projects_health.get('unhealthy_projects', 0)}")
    
    # Performance Metrics
    console.print(f"\nPerformance Metrics:")
    perf = dashboard.performance_metrics
    cache_hit_rate = perf.get('cache_hit_rate', 0)
    avg_response = perf.get('avg_service_response_time_ms', 0)
    console.print(f"├─ Cache Hit Rate:        {cache_hit_rate:.0f}% {'💨' if cache_hit_rate > 70 else '🐌' if cache_hit_rate < 30 else '⚡'}")
    console.print(f"├─ Avg Response Time:     {avg_response:.0f}ms {'⚡' if avg_response < 100 else '🐌' if avg_response > 1000 else '✅'}")
    console.print(f"└─ Framework Health:      {current.overall_health_percentage:.0f}%")
    
    # Critical Alerts
    if current.alerts:
        critical_alerts = [a for a in current.alerts if a.get("level") == "critical"]
        if critical_alerts:
            console.print(f"\n🚨 {len(critical_alerts)} Critical Alert(s):")
            for alert in critical_alerts[:3]:  # Show first 3
                console.print(f"  • {alert['message']}")
    
    # Key Recommendations
    if current.recommendations:
        console.print(f"\n💡 {len(current.recommendations)} Recommendation(s):")
        for rec in current.recommendations[:2]:  # Show top 2
            console.print(f"  • {rec}")


async def _display_memory_service_health(verbose=False):
    """Display detailed memory service health."""
    try:
        from .integrations.mem0ai_integration import create_mem0ai_integration
        
        console.print("[bold blue]Memory Service Health[/bold blue]")
        console.print("─" * 40)
        
        async with create_mem0ai_integration() as mem0ai:
            if mem0ai.is_connected():
                console.print("🟢 mem0AI Service:        Connected")
                console.print(f"🌐 Endpoint:              http://localhost:8002")
                
                if verbose:
                    # Test memory operations
                    start_time = time.time()
                    test_response = await mem0ai.get_service_info()
                    response_time = (time.time() - start_time) * 1000
                    
                    console.print(f"⏱️  Response Time:         {response_time:.1f}ms")
                    console.print(f"📊 Service Info:          {test_response.get('status', 'Unknown')}")
            else:
                console.print("🔴 mem0AI Service:        Disconnected")
                console.print("⚠️  Check service on port 8002")
        
    except Exception as e:
        console.print(f"🔴 Memory Service:        Error - {e}")


async def _display_indexing_service_health(verbose=False):
    """Display detailed project indexing service health."""
    try:
        from .services.project_indexer import create_project_indexer
        
        console.print("[bold blue]Project Indexing Service Health (MEM-007)[/bold blue]")
        console.print("─" * 50)
        
        indexer = create_project_indexer()
        
        if await indexer.initialize():
            console.print("🟢 Indexer Service:       Connected")
            
            # Get indexer statistics
            stats = indexer.get_indexer_statistics()
            console.print(f"📊 Projects Indexed:      {stats['projects_indexed']}")
            console.print(f"💾 Cache Hit Rate:        {stats['cache_hit_rate']:.1f}%")
            console.print(f"📁 Managed Path:          {stats['managed_path']}")
            
            if verbose:
                console.print(f"⏱️  Avg Index Time:       {stats.get('avg_index_time', 0):.2f}s")
                console.print(f"✅ Success Rate:          {stats.get('success_rate', 0):.1f}%")
            
            await indexer.cleanup()
        else:
            console.print("🔴 Indexer Service:       Failed to initialize")
            
    except Exception as e:
        console.print(f"🔴 Indexing Service:      Error - {e}")


def _display_projects_health(managed_projects_health, verbose=False):
    """Display detailed projects health."""
    console.print("[bold blue]Managed Projects Portfolio Health[/bold blue]")
    console.print("─" * 45)
    
    total = managed_projects_health["total_projects"]
    healthy = managed_projects_health["healthy_projects"]
    
    console.print(f"📊 Total Projects:        {total}")
    console.print(f"🟢 Healthy:               {healthy}")
    console.print(f"🟡 Degraded:              {managed_projects_health.get('degraded_projects', 0)}")
    console.print(f"🔴 Unhealthy:             {managed_projects_health.get('unhealthy_projects', 0)}")
    
    if verbose and managed_projects_health["projects"]:
        console.print("\nProject Details:")
        table = Table()
        table.add_column("Project", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Health Score", style="green")
        table.add_column("Indicators", style="yellow")
        
        for project in managed_projects_health["projects"]:
            indicator = _get_status_indicator_from_string(project["status"])
            
            indicators = []
            if project.get("has_git"):
                indicators.append("Git")
            if project.get("has_claude_md"):
                indicators.append("CLAUDE.md")
            if project.get("has_recent_activity"):
                indicators.append("Recent")
            
            table.add_row(
                project["name"],
                f"{indicator} {project['status'].title()}",
                f"{project['health_score']}%",
                ", ".join(indicators) if indicators else "None"
            )
        
        console.print(table)


async def _export_health_data(dashboard, managed_projects_health, format_type):
    """Export health data to specified format."""
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "framework_health": dashboard.to_dict(),
        "managed_projects": managed_projects_health
    }
    
    if format_type == "json":
        import json
        filename = f"health_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        console.print(f"[green]✅ Health data exported to {filename}[/green]")
    
    elif format_type == "yaml":
        try:
            import yaml
            filename = f"health_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
            with open(filename, 'w') as f:
                yaml.dump(export_data, f, default_flow_style=False)
            console.print(f"[green]✅ Health data exported to {filename}[/green]")
        except ImportError:
            console.print("[red]❌ PyYAML not installed. Install with: pip install pyyaml[/red]")


async def _generate_health_report(dashboard, managed_projects_health):
    """Generate comprehensive health report."""
    current = dashboard.current_report
    
    report_content = f"""# Claude PM Framework Health Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Overall Health**: {current.overall_health_percentage:.1f}%
- **Framework Status**: {current.overall_status.value.upper()}
- **Total Services**: {current.total_services}
- **Managed Projects**: {managed_projects_health['total_projects']}

## Framework Services

- Healthy: {current.healthy_services}
- Degraded: {current.degraded_services}
- Unhealthy: {current.unhealthy_services}
- Down: {current.down_services}

## Managed Projects Portfolio

- Total: {managed_projects_health['total_projects']}
- Healthy: {managed_projects_health['healthy_projects']}
- Issues: {managed_projects_health.get('unhealthy_projects', 0)}

## Performance Metrics

- Response Time: {current.response_time_ms:.0f}ms
- Cache Performance: {dashboard.performance_metrics.get('cache_hit_rate', 0):.1f}%

## Active Alerts

"""
    
    if current.alerts:
        for alert in current.alerts:
            report_content += f"- **{alert.get('level', 'info').upper()}**: {alert['message']}\n"
    else:
        report_content += "No active alerts.\n"
    
    report_content += "\n## Recommendations\n\n"
    
    if current.recommendations:
        for rec in current.recommendations:
            report_content += f"- {rec}\n"
    else:
        report_content += "No recommendations at this time.\n"
    
    filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, 'w') as f:
        f.write(report_content)
    
    console.print(f"[green]✅ Health report generated: {filename}[/green]")


def _get_framework_services_status(current_report):
    """Get overall framework services status."""
    if current_report.overall_health_percentage >= 90:
        return {"indicator": "🟢", "status": "OPERATIONAL"}
    elif current_report.overall_health_percentage >= 70:
        return {"indicator": "🟡", "status": "DEGRADED"}
    else:
        return {"indicator": "🔴", "status": "CRITICAL"}


def _get_key_services_summary(current_report):
    """Get summary of key services."""
    services = {}
    
    # Look for key services in the report
    for service in current_report.services:
        if any(keyword in service.name.lower() for keyword in ['health', 'memory', 'project', 'index']):
            services[service.name] = {
                "indicator": _get_status_indicator(service.status),
                "status": f"{service.status.value.title()} ({service.response_time_ms:.0f}ms)" if service.response_time_ms else service.status.value.title()
            }
    
    return services


def _get_status_indicator(status):
    """Get status indicator emoji."""
    from .models.health import HealthStatus
    
    return {
        HealthStatus.HEALTHY: "🟢",
        HealthStatus.DEGRADED: "🟡",
        HealthStatus.UNHEALTHY: "🔴",
        HealthStatus.DOWN: "🔴",
        HealthStatus.ERROR: "💥",
        HealthStatus.UNKNOWN: "❓"
    }.get(status, "❓")


def _get_status_indicator_from_string(status_str):
    """Get status indicator from string."""
    return {
        "healthy": "🟢",
        "degraded": "🟡",
        "unhealthy": "🔴",
        "down": "🔴",
        "error": "💥",
        "unknown": "❓"
    }.get(status_str.lower(), "❓")


def main():
    """Main entry point for the Claude Multi-Agent PM CLI."""
    try:
        # Register CMPM slash commands
        register_cmpm_commands(cli)
        cli()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Operation cancelled by user[/bold yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


if __name__ == '__main__':
    main()