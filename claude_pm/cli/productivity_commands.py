#!/usr/bin/env python3
"""
Productivity Commands Module - Claude Multi-Agent PM Framework

Handles memory, analytics, project indexing, and productivity commands.
Extracted from main CLI as part of ISS-0114 modularization initiative.

NOTE: Memory system has been removed for clean slate implementation.
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
    
    # Memory Management Commands (DISABLED)
    @cli_group.command()
    def memory():
        """Memory management and AI integration (DISABLED)."""
        console.print("[bold red]Memory system has been removed for clean slate implementation.[/bold red]")
        console.print("This command group is no longer available.")
        console.print("Memory functionality will be re-implemented in a future version.")

    # Project Index Commands (DISABLED - depends on memory system)
    @cli_group.group()
    def project_index():
        """Project indexing and fast retrieval (DISABLED)."""
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
        """Get comprehensive project information (DISABLED)."""
        console.print("[bold red]Project info command disabled - memory system removed.[/bold red]")
        console.print("This functionality will be re-implemented in a future version.")

    @project_index.command(name="search")
    @click.argument("query")
    @click.option("--language", "-l", help="Filter by programming language")
    @click.option("--framework", "-f", help="Filter by framework")
    @click.option("--limit", "-n", default=10, help="Maximum results")
    def search_projects(query, language, framework, limit):
        """Search indexed projects (DISABLED)."""
        console.print("[bold red]Project search command disabled - memory system removed.[/bold red]")
        console.print("This functionality will be re-implemented in a future version.")

    @project_index.command(name="recommend")
    @click.argument("project_name")
    @click.option("--limit", "-n", default=5, help="Maximum recommendations")
    def recommend_projects(project_name, limit):
        """Get project recommendations (DISABLED)."""
        console.print("[bold red]Project recommendations disabled - memory system removed.[/bold red]")
        console.print("This functionality will be re-implemented in a future version.")

    @project_index.command(name="stats")
    def index_stats():
        """Show project index statistics (DISABLED)."""
        console.print("[bold red]Project index stats disabled - memory system removed.[/bold red]")
        console.print("This functionality will be re-implemented in a future version.")

    @project_index.command(name="clear-cache")
    def clear_cache():
        """Clear project index cache (DISABLED)."""
        console.print("[bold red]Project index cache clearing disabled - memory system removed.[/bold red]")
        console.print("This functionality will be re-implemented in a future version.")

    # Analytics Commands (Simplified)
    @cli_group.group()
    def analytics():
        """Analytics and reporting commands."""
        pass

    @analytics.command()
    @click.option("--days", "-d", default=30, help="Number of days to analyze")
    def activity(days):
        """Show activity analytics."""
        console.print(f"[bold blue]📊 Activity Analysis (Last {days} days)[/bold blue]")
        console.print("")
        
        # Simple file-based activity tracking
        managed_path = get_managed_path()
        if not managed_path.exists():
            console.print("[yellow]No managed projects directory found[/yellow]")
            return
        
        project_count = 0
        total_files = 0
        
        for project_dir in managed_path.iterdir():
            if project_dir.is_dir() and (project_dir / ".claude-pm").exists():
                project_count += 1
                for file_path in project_dir.rglob("*"):
                    if file_path.is_file():
                        total_files += 1
        
        console.print(f"[bold]Projects:[/bold] {project_count}")
        console.print(f"[bold]Total Files:[/bold] {total_files}")
        console.print(f"[bold]Average Files/Project:[/bold] {total_files/project_count if project_count > 0 else 0:.1f}")

    @analytics.command()
    @click.option("--export", "-e", help="Export to JSON file")
    def projects(export):
        """Show project analytics."""
        console.print("[bold blue]📊 Project Portfolio Analytics[/bold blue]")
        console.print("")
        
        managed_path = get_managed_path()
        if not managed_path.exists():
            console.print("[yellow]No managed projects directory found[/yellow]")
            return
        
        projects = []
        for project_dir in managed_path.iterdir():
            if project_dir.is_dir() and (project_dir / ".claude-pm").exists():
                projects.append({
                    "name": project_dir.name,
                    "path": str(project_dir),
                    "has_config": (project_dir / ".claude-pm" / "config.yaml").exists(),
                    "last_modified": datetime.fromtimestamp(project_dir.stat().st_mtime).isoformat()
                })
        
        if export:
            with open(export, 'w') as f:
                json.dump(projects, f, indent=2)
            console.print(f"[green]✅ Analytics exported to {export}[/green]")
        else:
            table = Table(title="Project Portfolio")
            table.add_column("Project", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Last Modified", style="yellow")
            
            for project in projects:
                status = "✅ Configured" if project["has_config"] else "⚠️ Basic"
                table.add_row(
                    project["name"],
                    status,
                    project["last_modified"][:10]  # Just date
                )
            
            console.print(table)

    # Workflow Commands
    @cli_group.group()
    def workflow():
        """Workflow and automation commands."""
        pass

    @workflow.command()
    @click.argument("project_name")
    @click.option("--template", "-t", default="default", help="Workflow template")
    def create(project_name, template):
        """Create a new workflow."""
        console.print(f"[bold blue]⚙️ Creating workflow for {project_name}[/bold blue]")
        console.print(f"Using template: {template}")
        
        # Simple workflow creation
        managed_path = get_managed_path()
        project_path = managed_path / project_name
        
        if not project_path.exists():
            console.print(f"[red]❌ Project {project_name} not found[/red]")
            return
        
        workflow_path = project_path / ".claude-pm" / "workflows"
        workflow_path.mkdir(parents=True, exist_ok=True)
        
        workflow_file = workflow_path / f"{template}.yaml"
        
        # Create basic workflow template
        workflow_content = f"""# Workflow: {template}
# Project: {project_name}
# Created: {datetime.now().isoformat()}

name: {template}
description: "Automated workflow for {project_name}"

steps:
  - name: "Initialize"
    command: "echo 'Starting workflow'"
  
  - name: "Process"
    command: "echo 'Processing...'"
    
  - name: "Complete"
    command: "echo 'Workflow complete'"

triggers:
  - on_change: true
  - on_schedule: "0 9 * * *"  # Daily at 9 AM
"""
        
        workflow_file.write_text(workflow_content)
        console.print(f"[green]✅ Workflow created: {workflow_file}[/green]")

    @workflow.command()
    @click.argument("project_name")
    def list(project_name):
        """List workflows for a project."""
        console.print(f"[bold blue]📋 Workflows for {project_name}[/bold blue]")
        
        managed_path = get_managed_path()
        project_path = managed_path / project_name
        workflow_path = project_path / ".claude-pm" / "workflows"
        
        if not workflow_path.exists():
            console.print("[yellow]No workflows found[/yellow]")
            return
        
        workflows = list(workflow_path.glob("*.yaml"))
        if not workflows:
            console.print("[yellow]No workflows found[/yellow]")
            return
        
        table = Table(title=f"Workflows: {project_name}")
        table.add_column("Name", style="cyan")
        table.add_column("Modified", style="yellow")
        
        for workflow in workflows:
            table.add_row(
                workflow.stem,
                datetime.fromtimestamp(workflow.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)

    # Quick Commands
    @cli_group.command()
    @click.argument("project_name")
    def quick_status(project_name):
        """Get quick project status."""
        console.print(f"[bold blue]📊 Quick Status: {project_name}[/bold blue]")
        
        managed_path = get_managed_path()
        project_path = managed_path / project_name
        
        if not project_path.exists():
            console.print(f"[red]❌ Project {project_name} not found[/red]")
            return
        
        # Basic project info
        config_exists = (project_path / ".claude-pm" / "config.yaml").exists()
        git_exists = (project_path / ".git").exists()
        
        files_count = sum(1 for _ in project_path.rglob("*") if _.is_file())
        
        status_text = f"""
[bold]Project:[/bold] {project_name}
[bold]Path:[/bold] {project_path}
[bold]Configuration:[/bold] {'✅ Present' if config_exists else '⚠️ Missing'}
[bold]Git Repository:[/bold] {'✅ Present' if git_exists else '⚠️ Missing'}
[bold]Total Files:[/bold] {files_count}
[bold]Last Modified:[/bold] {datetime.fromtimestamp(project_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}
"""
        
        console.print(Panel(status_text.strip(), title="Quick Status"))