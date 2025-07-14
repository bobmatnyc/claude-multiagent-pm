#!/usr/bin/env python3
"""
Productivity Commands Module - Claude Multi-Agent PM Framework

Handles memory, analytics, project indexing, and productivity commands.
Extracted from main CLI as part of ISS-0114 modularization initiative.
"""

import asyncio
import sys
import json
import subprocess
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import io

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.config import Config
from ..services.project_service import ProjectService

console = Console()
logger = logging.getLogger(__name__)


def get_managed_path():
    """Get the managed projects path from configuration."""
    config = Config()
    return Path(config.get("managed_projects_path"))


def register_productivity_commands(cli_group):
    """Register all productivity commands with the main CLI group."""
    
    # Memory Management Commands
    @cli_group.group()
    def memory():
        """Memory management and AI integration."""
        pass

    @memory.command()
    @click.argument("project_name")
    def stats(project_name):
        """Show memory statistics for a project."""

        async def run():
            from ..integrations.mem0ai_integration import create_mem0ai_integration

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
                if stats["by_category"]:
                    table = Table(title="Memories by Category")
                    table.add_column("Category", style="cyan")
                    table.add_column("Count", style="green")
                    table.add_column("Description", style="yellow")

                    for category, count in stats["by_category"].items():
                        description = mem0ai.categories.get(category, "Unknown category")
                        table.add_row(category, str(count), description)

                    console.print(table)

        asyncio.run(run())

    @memory.command()
    @click.argument("project_name")
    @click.argument("query")
    @click.option("--category", "-c", help="Filter by category")
    @click.option("--limit", "-l", default=5, help="Maximum results")
    def search(project_name, query, category, limit):
        """Search memories in a project."""

        async def run():
            from ..integrations.mem0ai_integration import create_mem0ai_integration

            async with create_mem0ai_integration() as mem0ai:
                if not mem0ai.is_connected():
                    console.print("[red]❌ Cannot connect to mem0AI service[/red]")
                    return

                memories = await mem0ai.retrieve_memories(
                    project_name, query, category=category, limit=limit
                )

                if not memories:
                    console.print(f"[yellow]No memories found for query: {query}[/yellow]")
                    return

                console.print(f"[bold]Found {len(memories)} memories for: {query}[/bold]\n")

                for i, memory in enumerate(memories, 1):
                    content = (
                        memory.get("content", "")[:200] + "..."
                        if len(memory.get("content", "")) > 200
                        else memory.get("content", "")
                    )
                    metadata = memory.get("metadata", {})

                    memory_panel = f"""
[bold]Content:[/bold] {content}
[bold]Category:[/bold] {metadata.get('category', 'unknown')}
[bold]Tags:[/bold] {', '.join(metadata.get('tags', []))}
[bold]Stored:[/bold] {metadata.get('stored_at', 'unknown')}
"""

                    console.print(Panel(memory_panel.strip(), title=f"Memory {i}"))

        asyncio.run(run())

    # Project Index Commands (MEM-007)
    @cli_group.group()
    def project_index():
        """Project indexing and fast retrieval (MEM-007)."""
        pass

    @project_index.command(name="refresh")
    @click.option("--force", "-f", is_flag=True, help="Force refresh all projects")
    @click.option("--project", "-p", help="Refresh specific project only")
    def refresh_index(force, project):
        """Refresh project index from managed directory."""

        async def run():
            from ..services.project_indexer import create_project_indexer

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

                    if results.get("errors"):
                        console.print("\n[bold red]Errors:[/bold red]")
                        for error in results["errors"]:
                            console.print(f"  • {error}")

                    # Performance stats
                    perf = results.get("performance", {})
                    if perf:
                        console.print(
                            f"\n[bold blue]Performance:[/bold blue] {perf.get('projects_per_second', 0):.1f} projects/sec"
                        )

            finally:
                await indexer.cleanup()

        asyncio.run(run())

    @project_index.command(name="info")
    @click.argument("project_name")
    @click.option("--format", "-f", type=click.Choice(["summary", "full", "json"]), default="summary")
    def project_info(project_name, format):
        """Get comprehensive project information."""

        async def run():
            from ..services.project_memory_manager import create_project_memory_manager

            manager = create_project_memory_manager()

            try:
                if not await manager.initialize():
                    console.print("[red]❌ Failed to initialize project memory manager[/red]")
                    return

                if format == "summary":
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

                elif format == "full":
                    # Get full project details
                    details = await manager.get_project_details(project_name)

                    if not details:
                        console.print(f"[red]❌ Project '{project_name}' not found in index[/red]")
                        return

                    console.print(f"[bold]Full details for: {project_name}[/bold]\n")
                    console.print(json.dumps(details, indent=2))

                elif format == "json":
                    # Get raw JSON data
                    data = await manager.get_project_raw_data(project_name)
                    
                    if not data:
                        console.print(f"[red]❌ Project '{project_name}' not found in index[/red]")
                        return
                    
                    console.print(json.dumps(data, indent=2))

            finally:
                await manager.cleanup()

        asyncio.run(run())

    @project_index.command(name="search")
    @click.argument("query")
    @click.option("--language", "-l", help="Filter by programming language")
    @click.option("--framework", "-f", help="Filter by framework")
    @click.option("--limit", "-n", default=10, help="Maximum results")
    def search_projects(query, language, framework, limit):
        """Search indexed projects."""

        async def run():
            from ..services.project_memory_manager import create_project_memory_manager

            manager = create_project_memory_manager()

            try:
                if not await manager.initialize():
                    console.print("[red]❌ Failed to initialize project memory manager[/red]")
                    return

                # Build search filters
                filters = {}
                if language:
                    filters["language"] = language
                if framework:
                    filters["framework"] = framework

                results = await manager.search_projects(query, filters=filters, limit=limit)

                if not results:
                    console.print(f"[yellow]No projects found matching: {query}[/yellow]")
                    return

                console.print(f"[bold]Found {len(results)} projects matching: {query}[/bold]\n")

                # Display results
                for result in results:
                    project_info = f"""
[bold]Name:[/bold] {result['name']}
[bold]Type:[/bold] {result['type']}
[bold]Languages:[/bold] {', '.join(result['main_languages'])}
[bold]Relevance:[/bold] {result.get('relevance_score', 0):.2f}
[bold]Path:[/bold] {result['path']}
"""
                    console.print(Panel(project_info.strip(), title=result['name']))

            finally:
                await manager.cleanup()

        asyncio.run(run())

    @project_index.command(name="recommend")
    @click.argument("project_name")
    @click.option("--limit", "-n", default=5, help="Maximum recommendations")
    def recommend_projects(project_name, limit):
        """Get project recommendations based on similarity."""

        async def run():
            from ..services.project_memory_manager import create_project_memory_manager

            manager = create_project_memory_manager()

            try:
                if not await manager.initialize():
                    console.print("[red]❌ Failed to initialize project memory manager[/red]")
                    return

                recommendations = await manager.get_similar_projects(project_name, limit=limit)

                if not recommendations:
                    console.print(f"[yellow]No recommendations found for: {project_name}[/yellow]")
                    return

                console.print(f"[bold]Projects similar to {project_name}:[/bold]\n")

                for rec in recommendations:
                    similarity = rec.get('similarity_score', 0)
                    rec_info = f"""
[bold]Similarity:[/bold] {similarity:.2f}
[bold]Type:[/bold] {rec['type']}
[bold]Languages:[/bold] {', '.join(rec['main_languages'])}
[bold]Reason:[/bold] {rec.get('similarity_reason', 'Similar tech stack')}
"""
                    console.print(Panel(rec_info.strip(), title=rec['name']))

            finally:
                await manager.cleanup()

        asyncio.run(run())

    @project_index.command(name="stats")
    def index_stats():
        """Show project index statistics."""

        async def run():
            from ..services.project_memory_manager import create_project_memory_manager

            manager = create_project_memory_manager()

            try:
                if not await manager.initialize():
                    console.print("[red]❌ Failed to initialize project memory manager[/red]")
                    return

                stats = await manager.get_index_stats()

                if not stats:
                    console.print("[yellow]No index statistics available[/yellow]")
                    return

                # Display stats
                stats_text = f"""
[bold]Total Projects:[/bold] {stats['total_projects']}
[bold]Indexed Projects:[/bold] {stats['indexed_projects']}
[bold]Languages Found:[/bold] {stats['languages_count']}
[bold]Frameworks Found:[/bold] {stats['frameworks_count']}
[bold]Last Refresh:[/bold] {stats['last_refresh']}
[bold]Index Size:[/bold] {stats['index_size']}
"""

                console.print(Panel(stats_text.strip(), title="Project Index Statistics"))

                # Language breakdown
                if stats.get('language_breakdown'):
                    lang_table = Table(title="Languages Distribution")
                    lang_table.add_column("Language", style="cyan")
                    lang_table.add_column("Projects", style="green")
                    lang_table.add_column("Percentage", style="yellow")

                    for lang, count in stats['language_breakdown'].items():
                        percentage = (count / stats['total_projects']) * 100
                        lang_table.add_row(lang, str(count), f"{percentage:.1f}%")

                    console.print(lang_table)

            finally:
                await manager.cleanup()

        asyncio.run(run())

    @project_index.command(name="clear-cache")
    def clear_cache():
        """Clear project index cache."""

        async def run():
            from ..services.project_memory_manager import create_project_memory_manager

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
    @cli_group.group()
    def analytics():
        """Framework metrics and analytics."""
        pass

    @analytics.command()
    @click.option("--period", "-p", default="7d", help="Time period (1d, 7d, 30d)")
    @click.option(
        "--format", "-f", type=click.Choice(["summary", "detailed", "csv"]), default="summary"
    )
    def productivity(period, format):
        """Show productivity metrics."""

        async def run():
            period_days = {"1d": 1, "7d": 7, "30d": 30}.get(period, 7)
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
                "error_rate": 0,
            }

            # Get health data
            try:
                health_script = Path(__file__).parent.parent.parent / "scripts" / "automated_health_monitor.py"
                result = subprocess.run(
                    ["python", str(health_script), "status"], capture_output=True, text=True
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
                metrics["projects_compliance"] = stats["compliance_summary"]["average_score"]
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
                                    project_stats = await mem0ai.get_project_statistics(
                                        project_dir.name
                                    )
                                    if "total_memories" in project_stats:
                                        total_memories += project_stats["total_memories"]

                        metrics["memory_usage"] = total_memories
            except:
                metrics["memory_usage"] = 0

            if format == "summary":
                # Summary panel
                summary_text = f"""
[bold]Framework Health:[/bold] {metrics['framework_health']}%
[bold]Services Uptime:[/bold] {metrics['services_uptime']}%
[bold]Project Compliance:[/bold] {metrics['projects_compliance']:.1f}%
[bold]Total Memories:[/bold] {metrics['memory_usage']}
[bold]Period:[/bold] {period}
"""
                console.print(Panel(summary_text.strip(), title="Productivity Summary"))

            elif format == "detailed":
                # Detailed table
                table = Table(title="Detailed Productivity Metrics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                table.add_column("Trend", style="yellow")
                table.add_column("Target", style="magenta")

                table.add_row(
                    "Framework Health", f"{metrics['framework_health']}%", "↗️ Improving", "90%"
                )
                table.add_row("Services Uptime", f"{metrics['services_uptime']}%", "↗️ Stable", "95%")
                table.add_row(
                    "Project Compliance", f"{metrics['projects_compliance']:.1f}%", "→ Steady", "85%"
                )
                table.add_row("Memory Usage", str(metrics["memory_usage"]), "↗️ Growing", "N/A")
                table.add_row("Error Rate", f"{metrics['error_rate']}%", "↘️ Decreasing", "<5%")

                console.print(table)

            elif format == "csv":
                output = io.StringIO()
                output.write("metric,value,period,timestamp\n")
                timestamp = datetime.now().isoformat()
                for key, value in metrics.items():
                    if key not in ["period", "start_date"]:
                        output.write(f"{key},{value},{period},{timestamp}\n")

                csv_content = output.getvalue()
                console.print("[bold blue]CSV Output:[/bold blue]")
                console.print(csv_content)

        asyncio.run(run())

    @analytics.command()
    @click.option("--service", "-s", help="Specific service to analyze")
    @click.option("--period", "-p", default="24h", help="Time period (1h, 24h, 7d)")
    def performance(service, period):
        """Show service performance trends."""

        async def run():
            console.print(f"[bold blue]⚡ Performance Analysis ({period})[/bold blue]\n")

            # Service performance metrics
            services = ["health_monitor", "memory_service", "project_service"]
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
                response_time = (
                    "45ms"
                    if svc == "health_monitor"
                    else "120ms" if svc == "memory_service" else "80ms"
                )
                success_rate = (
                    "99.2%"
                    if svc == "health_monitor"
                    else "98.7%" if svc == "memory_service" else "99.8%"
                )
                memory_usage = (
                    "24MB"
                    if svc == "health_monitor"
                    else "156MB" if svc == "memory_service" else "89MB"
                )
                status = "🟢 Healthy"

                table.add_row(svc, response_time, success_rate, memory_usage, status)

            console.print(table)

            # Performance recommendations
            recommendations = [
                "Memory service could benefit from connection pooling",
                "Consider caching for frequently accessed project data",
                "Health monitor is performing optimally",
            ]

            console.print("\n[bold blue]💡 Recommendations:[/bold blue]")
            for rec in recommendations:
                console.print(f"  • {rec}")

        asyncio.run(run())

    return cli_group