#!/usr/bin/env python3
"""
Deployment Commands Module - Claude Multi-Agent PM Framework

Handles deployment, ticket management, and release operations.
Extracted from main CLI as part of ISS-0114 modularization initiative.
"""

import asyncio
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.config import Config
from ..scripts.service_manager import ClaudePMServiceManager

console = Console()
logger = logging.getLogger(__name__)


def get_claude_pm_path():
    """Get the Claude PM framework path from configuration."""
    config = Config()
    return Path(config.get("claude_pm_path"))


def register_deployment_commands(cli_group):
    """Register all deployment commands with the main CLI group."""
    
    # Deployment Commands
    @cli_group.group()
    def deploy():
        """Deployment operations and management."""
        pass

    @deploy.command()
    @click.option("--service", "-s", help="Deploy specific service")
    @click.option(
        "--health-check/--no-health-check", default=True, help="Run health checks after deployment"
    )
    @click.option("--timeout", "-t", default=300, help="Deployment timeout in seconds")
    def start(service, health_check, timeout):
        """Deploy services with health checks."""

        async def run():
            console.print("[bold blue]🚀 Starting deployment process...[/bold blue]")
            
            # Check for tasks/ to tickets/ migration before deployment
            try:
                from ..utils.tasks_to_tickets_migration import check_and_migrate_tasks_directory
                
                # Check current directory for migration needs
                current_dir = Path.cwd()
                migration_result = await check_and_migrate_tasks_directory(current_dir, silent=False)
                
                if migration_result.get("migrated"):
                    console.print(f"✅ Migrated tasks/ to tickets/ before deployment")
                    
            except Exception as migration_error:
                console.print(f"[yellow]⚠️ Migration check failed: {migration_error}[/yellow]")
                logger.warning(f"Tasks to tickets migration failed: {migration_error}")
                # Continue with deployment even if migration fails

            if service:
                console.print(f"Deploying specific service: {service}")
                services_to_deploy = [service]
            else:
                console.print("Deploying all Claude PM services")
                services_to_deploy = ["health_monitor", "project_service"]  # memory_service removed

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
                    console.print(
                        "\n[bold blue]🏥 Running post-deployment health checks...[/bold blue]"
                    )

                    start_time = time.time()

                    while time.time() - start_time < timeout:
                        health_results = await manager.service_manager.health_check_all()

                        healthy_services = sum(
                            1 for h in health_results.values() if h.status == "healthy"
                        )
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
                                console.print(
                                    f"[green]✅ All {total_services} services are healthy[/green]"
                                )
                                break

                        console.print(
                            f"[yellow]⏳ Waiting for services to become healthy ({healthy_services}/{total_services})...[/yellow]"
                        )
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
    @click.option("--steps", "-s", type=int, help="Number of rollback steps")
    @click.confirmation_option(prompt="Are you sure you want to rollback?")
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
            "5. Verifying rollback success",
        ]

        for step in rollback_steps:
            console.print(f"[blue]{step}[/blue]")
            time.sleep(1)

        console.print("[green]✅ Rollback simulation completed[/green]")

    @deploy.command()
    @click.option("--env", "-e", default="development", help="Environment name")
    def environment(env):
        """Manage deployment environments."""
        console.print(f"[bold blue]🌍 Environment Management: {env}[/bold blue]\n")

        environments = {
            "development": {
                "description": "Local development environment",
                "services": ["health_monitor", "project_service"],
                "ports": {"dashboard": 7001},
                "status": "Active",
            },
            "staging": {
                "description": "Staging environment for testing",
                "services": ["health_monitor", "project_service"],
                "ports": {"dashboard": 7002},
                "status": "Not configured",
            },
            "production": {
                "description": "Production environment",
                "services": ["health_monitor", "project_service"],
                "ports": {"dashboard": 7003},
                "status": "Not configured",
            },
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

            if env_data["status"] == "Not configured":
                console.print(f"\n[yellow]⚠️ Environment '{env}' requires configuration[/yellow]")
                console.print("Use 'claude-pm deploy start' to configure this environment")
        else:
            console.print(f"[red]Environment '{env}' not found[/red]")
            console.print(f"Available environments: {', '.join(environments.keys())}")

    # Tickets Commands
    @cli_group.group()
    def tickets():
        """TrackDown integration and ticket management."""
        pass

    @tickets.command()
    @click.option("--sprint", "-s", help="Specific sprint number")
    def sprint(sprint):
        """Show current sprint tickets."""

        async def run():
            from ..services.project_service import ProjectService

            console.print("[bold blue]🎯 Sprint Tickets Overview[/bold blue]\n")

            try:
                project_service = ProjectService()
                await project_service._initialize()

                # Get sprint tickets (placeholder implementation)
                if sprint:
                    console.print(f"Showing tickets for Sprint {sprint}")
                    tickets = await project_service.get_sprint_tickets(sprint)
                else:
                    console.print("Showing current sprint tickets")
                    tickets = await project_service.get_current_sprint_tickets()

                if not tickets:
                    console.print("[yellow]No tickets found for this sprint[/yellow]")
                    return

                # Display tickets table
                ticket_table = Table(title=f"Sprint {sprint or 'Current'} Tickets")
                ticket_table.add_column("ID", style="cyan")
                ticket_table.add_column("Title", style="white")
                ticket_table.add_column("Status", style="green")
                ticket_table.add_column("Priority", style="yellow")
                ticket_table.add_column("Assignee", style="magenta")

                for ticket in tickets:
                    status_color = {
                        "open": "red",
                        "in_progress": "yellow",
                        "review": "blue",
                        "done": "green"
                    }.get(ticket.get("status", "open"), "white")
                    
                    status_display = f"[{status_color}]{ticket.get('status', 'unknown')}[/{status_color}]"
                    
                    ticket_table.add_row(
                        ticket.get("id", "N/A"),
                        ticket.get("title", "No title")[:50],
                        status_display,
                        ticket.get("priority", "medium"),
                        ticket.get("assignee", "unassigned")
                    )

                console.print(ticket_table)

                # Sprint summary
                total_tickets = len(tickets)
                completed_tickets = len([t for t in tickets if t.get("status") == "done"])
                completion_rate = (completed_tickets / total_tickets * 100) if total_tickets > 0 else 0

                summary_text = f"""
[bold]Total Tickets:[/bold] {total_tickets}
[bold]Completed:[/bold] {completed_tickets}
[bold]Completion Rate:[/bold] {completion_rate:.1f}%
[bold]In Progress:[/bold] {len([t for t in tickets if t.get('status') == 'in_progress'])}
"""
                console.print(Panel(summary_text.strip(), title="Sprint Summary"))

                await project_service._cleanup()

            except Exception as e:
                console.print(f"[red]❌ Error getting sprint tickets: {e}[/red]")

        asyncio.run(run())

    @tickets.command()
    @click.argument("ticket_id")
    def show(ticket_id):
        """Show detailed ticket information."""

        async def run():
            from ..services.project_service import ProjectService

            console.print(f"[bold blue]🎫 Ticket Details: {ticket_id}[/bold blue]\n")

            try:
                project_service = ProjectService()
                await project_service._initialize()

                ticket = await project_service.get_ticket_details(ticket_id)

                if not ticket:
                    console.print(f"[red]❌ Ticket '{ticket_id}' not found[/red]")
                    return

                # Display ticket details
                details_text = f"""
[bold]ID:[/bold] {ticket.get('id', 'N/A')}
[bold]Title:[/bold] {ticket.get('title', 'No title')}
[bold]Status:[/bold] {ticket.get('status', 'unknown')}
[bold]Priority:[/bold] {ticket.get('priority', 'medium')}
[bold]Assignee:[/bold] {ticket.get('assignee', 'unassigned')}
[bold]Created:[/bold] {ticket.get('created_at', 'unknown')}
[bold]Updated:[/bold] {ticket.get('updated_at', 'unknown')}
[bold]Sprint:[/bold] {ticket.get('sprint', 'unassigned')}

[bold]Description:[/bold]
{ticket.get('description', 'No description available')}
"""

                console.print(Panel(details_text.strip(), title=f"Ticket: {ticket_id}"))

                # Show comments if available
                if ticket.get('comments'):
                    console.print("\n[bold blue]💬 Comments:[/bold blue]")
                    for comment in ticket['comments'][-5:]:  # Show last 5 comments
                        console.print(f"[dim]{comment.get('author', 'Unknown')} - {comment.get('created_at', '')}[/dim]")
                        console.print(f"{comment.get('content', 'No content')}\n")

                await project_service._cleanup()

            except Exception as e:
                console.print(f"[red]❌ Error getting ticket details: {e}[/red]")

        asyncio.run(run())

    @tickets.command()
    @click.argument("title")
    @click.option("--description", "-d", help="Ticket description")
    @click.option("--priority", "-p", type=click.Choice(["low", "medium", "high", "urgent"]), default="medium")
    @click.option("--assignee", "-a", help="Assign to user")
    def create(title, description, priority, assignee):
        """Create a new ticket."""

        async def run():
            from ..services.project_service import ProjectService

            console.print("[bold blue]🎫 Creating new ticket...[/bold blue]\n")

            try:
                project_service = ProjectService()
                await project_service._initialize()

                ticket_data = {
                    "title": title,
                    "description": description or "No description provided",
                    "priority": priority,
                    "assignee": assignee,
                    "status": "open",
                    "created_at": datetime.now().isoformat()
                }

                ticket_id = await project_service.create_ticket(ticket_data)

                if ticket_id:
                    console.print(f"[green]✅ Ticket created successfully: {ticket_id}[/green]")
                    
                    # Show created ticket details
                    details_text = f"""
[bold]ID:[/bold] {ticket_id}
[bold]Title:[/bold] {title}
[bold]Priority:[/bold] {priority}
[bold]Assignee:[/bold] {assignee or 'unassigned'}
[bold]Status:[/bold] open
"""
                    console.print(Panel(details_text.strip(), title="Created Ticket"))
                else:
                    console.print("[red]❌ Failed to create ticket[/red]")

                await project_service._cleanup()

            except Exception as e:
                console.print(f"[red]❌ Error creating ticket: {e}[/red]")

        asyncio.run(run())

    @tickets.command()
    @click.argument("ticket_id")
    @click.option("--status", "-s", type=click.Choice(["open", "in_progress", "review", "done", "closed"]))
    @click.option("--priority", "-p", type=click.Choice(["low", "medium", "high", "urgent"]))
    @click.option("--assignee", "-a", help="Assign to user")
    def update(ticket_id, status, priority, assignee):
        """Update ticket properties."""

        async def run():
            from ..services.project_service import ProjectService

            console.print(f"[bold blue]🔄 Updating ticket: {ticket_id}[/bold blue]\n")

            try:
                project_service = ProjectService()
                await project_service._initialize()

                updates = {}
                if status:
                    updates["status"] = status
                if priority:
                    updates["priority"] = priority
                if assignee:
                    updates["assignee"] = assignee
                
                updates["updated_at"] = datetime.now().isoformat()

                if not updates:
                    console.print("[yellow]No updates specified[/yellow]")
                    return

                success = await project_service.update_ticket(ticket_id, updates)

                if success:
                    console.print(f"[green]✅ Ticket {ticket_id} updated successfully[/green]")
                    
                    # Show what was updated
                    for key, value in updates.items():
                        if key != "updated_at":
                            console.print(f"  • {key}: {value}")
                else:
                    console.print(f"[red]❌ Failed to update ticket {ticket_id}[/red]")

                await project_service._cleanup()

            except Exception as e:
                console.print(f"[red]❌ Error updating ticket: {e}[/red]")

        asyncio.run(run())

    @tickets.command()
    @click.option("--status", "-s", help="Filter by status")
    @click.option("--assignee", "-a", help="Filter by assignee")
    @click.option("--limit", "-l", default=20, help="Maximum tickets to show")
    def list(status, assignee, limit):
        """List tickets with optional filters."""

        async def run():
            from ..services.project_service import ProjectService

            console.print("[bold blue]📋 Tickets List[/bold blue]\n")

            try:
                project_service = ProjectService()
                await project_service._initialize()

                filters = {}
                if status:
                    filters["status"] = status
                if assignee:
                    filters["assignee"] = assignee

                tickets = await project_service.list_tickets(filters=filters, limit=limit)

                if not tickets:
                    console.print("[yellow]No tickets found[/yellow]")
                    return

                # Display tickets table
                ticket_table = Table(title="Tickets")
                ticket_table.add_column("ID", style="cyan")
                ticket_table.add_column("Title", style="white")
                ticket_table.add_column("Status", style="green")
                ticket_table.add_column("Priority", style="yellow")
                ticket_table.add_column("Assignee", style="magenta")
                ticket_table.add_column("Updated", style="dim")

                for ticket in tickets:
                    status_color = {
                        "open": "red",
                        "in_progress": "yellow",
                        "review": "blue",
                        "done": "green",
                        "closed": "dim"
                    }.get(ticket.get("status", "open"), "white")
                    
                    status_display = f"[{status_color}]{ticket.get('status', 'unknown')}[/{status_color}]"
                    
                    # Format updated date
                    updated = ticket.get("updated_at", "")
                    if updated:
                        try:
                            updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                            updated = updated_dt.strftime("%m/%d %H:%M")
                        except:
                            updated = updated[:10]  # Just the date part
                    
                    ticket_table.add_row(
                        ticket.get("id", "N/A"),
                        ticket.get("title", "No title")[:40],
                        status_display,
                        ticket.get("priority", "medium"),
                        ticket.get("assignee", "unassigned"),
                        updated
                    )

                console.print(ticket_table)

                # Summary
                console.print(f"\n[dim]Showing {len(tickets)} tickets[/dim]")
                if filters:
                    filter_text = ", ".join(f"{k}={v}" for k, v in filters.items())
                    console.print(f"[dim]Filters: {filter_text}[/dim]")

                await project_service._cleanup()

            except Exception as e:
                console.print(f"[red]❌ Error listing tickets: {e}[/red]")

        asyncio.run(run())

    return cli_group