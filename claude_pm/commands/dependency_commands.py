#!/usr/bin/env python3
"""
Dependency Management Commands for Claude PM Framework

Provides CLI commands for dependency management and updates.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from ..services.dependency_updater import DependencyUpdater, UpdateConfig
from ..core.service_manager import ServiceManager

console = Console()


@click.group()
def dependencies():
    """Dependency management and update commands."""
    pass


@dependencies.command("status")
@click.option("--ecosystem", type=click.Choice(["python", "nodejs", "all"]), default="all",
              help="Ecosystem to check (default: all)")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table",
              help="Output format")
@click.option("--updates-only", is_flag=True, help="Show only dependencies with updates available")
def status_cmd(ecosystem: str, output_format: str, updates_only: bool):
    """Check status of all dependencies."""
    
    async def _run_status():
        try:
            updater = DependencyUpdater()
            await updater._initialize()
            
            # Get dependencies based on ecosystem
            if ecosystem in ["python", "all"]:
                python_deps = await updater.get_python_dependencies()
            else:
                python_deps = []
                
            if ecosystem in ["nodejs", "all"]:
                nodejs_deps = await updater.get_nodejs_dependencies()
            else:
                nodejs_deps = []
            
            all_deps = python_deps + nodejs_deps
            
            if updates_only:
                all_deps = [d for d in all_deps if d.update_available]
            
            if output_format == "json":
                # JSON output
                output_data = {
                    "total_dependencies": len(all_deps),
                    "updates_available": len([d for d in all_deps if d.update_available]),
                    "security_updates": len([d for d in all_deps if d.security_update]),
                    "dependencies": [
                        {
                            "name": d.name,
                            "current_version": d.current_version,
                            "latest_version": d.latest_version,
                            "ecosystem": d.ecosystem,
                            "update_available": d.update_available,
                            "is_major_update": d.is_major_update,
                            "security_update": d.security_update,
                            "confidence": d.confidence
                        }
                        for d in all_deps
                    ]
                }
                console.print_json(data=output_data)
            else:
                # Table output
                updater.display_dependency_status(all_deps)
                
                # Summary
                updates_count = len([d for d in all_deps if d.update_available])
                security_count = len([d for d in all_deps if d.security_update])
                
                if updates_count > 0:
                    console.print(f"\n[yellow]📦 {updates_count} updates available[/yellow]")
                    if security_count > 0:
                        console.print(f"[red]🔒 {security_count} security updates[/red]")
                    console.print("Run 'claude-pm dependencies update' to update dependencies")
            
            await updater._cleanup()
            
        except Exception as e:
            console.print(f"[red]Error checking dependency status: {e}[/red]")
    
    asyncio.run(_run_status())


@dependencies.command("update")
@click.option("--ecosystem", type=click.Choice(["python", "nodejs", "all"]), default="all",
              help="Ecosystem to update (default: all)")
@click.option("--include-major", is_flag=True, help="Include major version updates")
@click.option("--security-only", is_flag=True, help="Only apply security updates")
@click.option("--dry-run", is_flag=True, help="Show what would be updated without making changes")
@click.option("--no-tests", is_flag=True, help="Skip running tests after updates")
@click.option("--no-backup", is_flag=True, help="Skip creating backup before updates")
@click.option("--exclude", multiple=True, help="Exclude specific packages from updates")
def update_cmd(ecosystem: str, include_major: bool, security_only: bool, 
               dry_run: bool, no_tests: bool, no_backup: bool, exclude: tuple):
    """Update dependencies to latest versions."""
    
    async def _run_update():
        try:
            updater = DependencyUpdater()
            await updater._initialize()
            
            # Configure update settings
            updater.update_config.auto_update_major = include_major
            updater.update_config.run_tests_after_update = not no_tests
            updater.update_config.create_backup = not no_backup
            updater.update_config.dry_run = dry_run
            
            if exclude:
                updater.update_config.exclude_packages = list(exclude)
            
            # Get dependencies
            if ecosystem in ["python", "all"]:
                python_deps = await updater.get_python_dependencies()
            else:
                python_deps = []
                
            if ecosystem in ["nodejs", "all"]:
                nodejs_deps = await updater.get_nodejs_dependencies()
            else:
                nodejs_deps = []
            
            all_deps = python_deps + nodejs_deps
            
            # Filter for security-only updates if requested
            if security_only:
                all_deps = [d for d in all_deps if d.security_update]
                if not all_deps:
                    console.print("[green]✓[/green] No security updates available")
                    return
            
            # Filter for updates available
            update_deps = [d for d in all_deps if d.update_available]
            
            if not update_deps:
                console.print("[green]✓[/green] All dependencies are up to date")
                return
            
            # Show what will be updated
            console.print(f"\n[yellow]📦 Found {len(update_deps)} dependencies to update[/yellow]\n")
            updater.display_dependency_status(update_deps)
            
            # Confirm unless dry run
            if not dry_run:
                if not Confirm.ask(f"\nProceed with updating {len(update_deps)} dependencies?"):
                    console.print("Update cancelled")
                    return
            
            # Perform updates
            console.print(f"\n[blue]🔄 {'Simulating' if dry_run else 'Performing'} dependency updates...[/blue]\n")
            results = await updater.update_dependencies(update_deps, dry_run=dry_run)
            
            # Display results
            updater.display_update_results(results)
            
            # Show recommendations
            if not dry_run:
                recommendations = await updater.get_update_recommendations()
                if recommendations["recommendations"]:
                    console.print("\n[blue]💡 Recommendations:[/blue]")
                    for rec in recommendations["recommendations"]:
                        priority_color = {
                            "critical": "red",
                            "high": "yellow", 
                            "medium": "blue",
                            "low": "dim"
                        }.get(rec["priority"], "white")
                        console.print(f"[{priority_color}]• {rec['message']}[/{priority_color}]")
            
            await updater._cleanup()
            
        except Exception as e:
            console.print(f"[red]Error updating dependencies: {e}[/red]")
    
    asyncio.run(_run_update())


@dependencies.command("security")
def security_cmd():
    """Check for security vulnerabilities in dependencies."""
    
    async def _run_security():
        try:
            updater = DependencyUpdater()
            await updater._initialize()
            
            console.print("[blue]🔍 Checking for security vulnerabilities...[/blue]\n")
            
            vulnerabilities = await updater.check_security_vulnerabilities()
            
            total_vulns = len(vulnerabilities["python"]) + len(vulnerabilities["nodejs"])
            
            if total_vulns == 0:
                console.print("[green]✓ No security vulnerabilities found[/green]")
            else:
                console.print(f"[red]⚠ Found {total_vulns} packages with security vulnerabilities[/red]\n")
                
                if vulnerabilities["python"]:
                    table = Table(title="Python Security Issues")
                    table.add_column("Package", style="red")
                    for package in vulnerabilities["python"]:
                        table.add_row(package)
                    console.print(table)
                
                if vulnerabilities["nodejs"]:
                    table = Table(title="Node.js Security Issues")
                    table.add_column("Package", style="red")
                    for package in vulnerabilities["nodejs"]:
                        table.add_row(package)
                    console.print(table)
                
                console.print(f"\n[yellow]Run 'claude-pm dependencies update --security-only' to update vulnerable packages[/yellow]")
            
            await updater._cleanup()
            
        except Exception as e:
            console.print(f"[red]Error checking security vulnerabilities: {e}[/red]")
    
    asyncio.run(_run_security())


@dependencies.command("recommendations")
def recommendations_cmd():
    """Get update recommendations."""
    
    async def _run_recommendations():
        try:
            updater = DependencyUpdater()
            await updater._initialize()
            
            recommendations = await updater.get_update_recommendations()
            
            # Display summary
            panel_content = f"""
Total Dependencies: {recommendations['total_dependencies']}
Updates Available: {recommendations['updates_available']}
Security Updates: {recommendations['security_updates']}
Safe Updates: {recommendations['safe_updates']}
Major Updates: {recommendations['major_updates']}
High Confidence Updates: {recommendations['high_confidence_updates']}
            """.strip()
            
            if recommendations['last_update']:
                from datetime import datetime
                last_update = datetime.fromisoformat(recommendations['last_update'])
                panel_content += f"\nLast Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}"
            
            console.print(Panel(panel_content, title="Dependency Summary", style="blue"))
            
            # Display recommendations
            if recommendations["recommendations"]:
                console.print("\n[blue]💡 Recommendations:[/blue]")
                for rec in recommendations["recommendations"]:
                    priority_color = {
                        "critical": "red bold",
                        "high": "yellow", 
                        "medium": "blue",
                        "low": "dim"
                    }.get(rec["priority"], "white")
                    console.print(f"[{priority_color}]• {rec['message']}[/{priority_color}]")
            else:
                console.print("\n[green]✓ All dependencies are up to date[/green]")
            
            await updater._cleanup()
            
        except Exception as e:
            console.print(f"[red]Error getting recommendations: {e}[/red]")
    
    asyncio.run(_run_recommendations())


@dependencies.command("health")
def health_cmd():
    """Check overall dependency health."""
    
    async def _run_health():
        try:
            updater = DependencyUpdater()
            await updater._initialize()
            
            console.print("[blue]🏥 Checking dependency health...[/blue]\n")
            
            # Get package managers
            managers = await updater.detect_package_managers()
            
            # Package manager status
            console.print("[bold]Package Managers:[/bold]")
            for manager, available in managers.items():
                status_icon = "✓" if available else "✗"
                status_color = "green" if available else "red"
                console.print(f"[{status_color}]{status_icon}[/{status_color}] {manager}")
            
            # Get recommendations
            recommendations = await updater.get_update_recommendations()
            
            # Calculate health score
            total_deps = recommendations["total_dependencies"]
            updates_available = recommendations["updates_available"]
            security_updates = recommendations["security_updates"]
            
            if total_deps == 0:
                health_score = 100
            else:
                # Penalize security updates more heavily
                security_penalty = security_updates * 20
                update_penalty = (updates_available - security_updates) * 5
                health_score = max(0, 100 - security_penalty - update_penalty)
            
            # Display health score
            if health_score >= 90:
                score_color = "green"
                status = "Excellent"
            elif health_score >= 70:
                score_color = "yellow"
                status = "Good"
            elif health_score >= 50:
                score_color = "orange"
                status = "Poor"
            else:
                score_color = "red"
                status = "Critical"
            
            console.print(f"\n[bold]Health Score: [{score_color}]{health_score}/100[/{score_color}] ({status})[/bold]")
            
            # Display issues
            if security_updates > 0:
                console.print(f"[red]⚠ {security_updates} security vulnerabilities found[/red]")
            if updates_available > security_updates:
                console.print(f"[yellow]📦 {updates_available - security_updates} regular updates available[/yellow]")
            
            if health_score < 100:
                console.print(f"\n[blue]💡 Run 'claude-pm dependencies update' to improve health score[/blue]")
            
            await updater._cleanup()
            
        except Exception as e:
            console.print(f"[red]Error checking dependency health: {e}[/red]")
    
    asyncio.run(_run_health())


@dependencies.command("config")
@click.option("--auto-minor", is_flag=True, help="Auto-update minor versions")
@click.option("--auto-patch", is_flag=True, help="Auto-update patch versions") 
@click.option("--auto-major", is_flag=True, help="Auto-update major versions")
@click.option("--no-tests", is_flag=True, help="Skip running tests after updates")
@click.option("--no-backup", is_flag=True, help="Skip creating backups")
@click.option("--schedule", type=click.Choice(["daily", "weekly", "monthly"]), 
              help="Set update schedule")
@click.option("--exclude", multiple=True, help="Packages to exclude from auto-updates")
@click.option("--show", is_flag=True, help="Show current configuration")
def config_cmd(auto_minor: bool, auto_patch: bool, auto_major: bool,
               no_tests: bool, no_backup: bool, schedule: Optional[str],
               exclude: tuple, show: bool):
    """Configure automatic dependency updates."""
    try:
        updater = DependencyUpdater()
        
        if show:
            # Show current configuration
            config = updater.update_config
            
            table = Table(title="Dependency Update Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Auto-update minor versions", "✓" if config.auto_update_minor else "✗")
            table.add_row("Auto-update patch versions", "✓" if config.auto_update_patch else "✗") 
            table.add_row("Auto-update major versions", "✓" if config.auto_update_major else "✗")
            table.add_row("Run tests after update", "✓" if config.run_tests_after_update else "✗")
            table.add_row("Create backups", "✓" if config.create_backup else "✗")
            table.add_row("Skip dev dependencies", "✓" if config.skip_dev_dependencies else "✗")
            table.add_row("Update schedule", config.update_schedule or "Manual")
            table.add_row("Max concurrent updates", str(config.max_concurrent_updates))
            table.add_row("Update timeout", f"{config.update_timeout}s")
            
            if config.exclude_packages:
                table.add_row("Excluded packages", ", ".join(config.exclude_packages))
            
            console.print(table)
            return
        
        # Update configuration
        if auto_minor:
            updater.update_config.auto_update_minor = True
        if auto_patch:
            updater.update_config.auto_update_patch = True
        if auto_major:
            updater.update_config.auto_update_major = True
        if no_tests:
            updater.update_config.run_tests_after_update = False
        if no_backup:
            updater.update_config.create_backup = False
        if schedule:
            updater.update_config.update_schedule = schedule
        if exclude:
            if updater.update_config.exclude_packages:
                updater.update_config.exclude_packages.extend(exclude)
            else:
                updater.update_config.exclude_packages = list(exclude)
        
        # Save configuration
        updater._save_update_config()
        
        console.print("[green]✓[/green] Configuration updated successfully")
        
    except Exception as e:
        console.print(f"[red]Error configuring dependencies: {e}[/red]")


@dependencies.group("backup")
def backup_group():
    """Dependency backup management."""
    pass


@backup_group.command("create")
def backup_create():
    """Create a backup of current dependency files."""
    
    async def _run_backup_create():
        try:
            updater = DependencyUpdater()
            await updater._initialize()
            
            console.print("[blue]💾 Creating dependency backup...[/blue]")
            backup_name = await updater.create_backup()
            console.print(f"[green]✓[/green] Backup created: {backup_name}")
            
            await updater._cleanup()
            
        except Exception as e:
            console.print(f"[red]Error creating backup: {e}[/red]")
    
    asyncio.run(_run_backup_create())


@backup_group.command("list")
def backup_list():
    """List available dependency backups."""
    try:
        updater = DependencyUpdater()
        
        backups = updater.list_backups()
        
        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            return
        
        table = Table(title="Available Backups")
        table.add_column("Name", style="cyan")
        table.add_column("Timestamp", style="blue")
        table.add_column("Files", style="green")
        table.add_column("Path", style="dim")
        
        for backup in backups:
            table.add_row(
                backup["name"],
                backup["timestamp"],
                str(backup["files"]),
                backup["path"]
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing backups: {e}[/red]")


@backup_group.command("restore")
@click.argument("backup_name")
@click.option("--force", is_flag=True, help="Force restore without confirmation")
def backup_restore(backup_name: str, force: bool):
    """Restore from a dependency backup."""
    
    async def _run_backup_restore():
        try:
            updater = DependencyUpdater()
            await updater._initialize()
            
            if not force:
                if not Confirm.ask(f"Are you sure you want to restore backup '{backup_name}'? This will overwrite current dependency files."):
                    console.print("Restore cancelled")
                    return
            
            console.print(f"[blue]📁 Restoring from backup: {backup_name}[/blue]")
            success = await updater.restore_backup(backup_name)
            
            if success:
                console.print("[green]✓[/green] Backup restored successfully")
            else:
                console.print("[red]✗[/red] Failed to restore backup")
            
            await updater._cleanup()
            
        except Exception as e:
            console.print(f"[red]Error restoring backup: {e}[/red]")
    
    asyncio.run(_run_backup_restore())


@dependencies.command("outdated")
@click.option("--ecosystem", type=click.Choice(["python", "nodejs", "all"]), default="all",
              help="Ecosystem to check (default: all)")
def outdated_cmd(ecosystem: str):
    """Show outdated dependencies (alias for status --updates-only)."""
    # Call the status command implementation directly
    status_cmd.callback(ecosystem=ecosystem, output_format="table", updates_only=True)