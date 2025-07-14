#!/usr/bin/env python3
"""
Setup Commands Module - Claude Multi-Agent PM Framework

Handles framework setup, initialization, and configuration commands.
Extracted from main CLI as part of ISS-0114 modularization initiative.
"""

import asyncio
import sys
import json
import platform
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from ..core.config import Config
from ..services.health_monitor import HealthMonitorService
from ..services.memory_service import MemoryService
from ..services.project_service import ProjectService
from ..services.template_deployment_integration import TemplateDeploymentIntegration
from ..models.health import HealthStatus, create_service_health_report

console = Console()
logger = logging.getLogger(__name__)


def _get_framework_version():
    """Get framework version from VERSION file."""
    try:
        version_file = Path(__file__).parent.parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "0.4.6"  # Fallback version
    except Exception:
        return "0.4.6"


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
    return Path(config.get("managed_projects_path"))


def _display_directory_context():
    """Display deployment and working directory context."""
    try:
        working_dir = Path.cwd()
        claude_pm_path = get_claude_pm_path()
        
        console.print(f"[dim]Working Directory:[/dim] {working_dir}")
        console.print(f"[dim]Framework Path:[/dim] {claude_pm_path}")
        console.print("")
    except Exception as e:
        logger.debug(f"Failed to display directory context: {e}")


async def _add_project_indexing_health_collector(orchestrator):
    """Add project indexing health monitoring to orchestrator."""
    try:
        from ..services.project_indexer import create_project_indexer
        
        indexer = await create_project_indexer()
        if indexer:
            # Add health check for project indexing
            def check_indexing_health():
                return HealthStatus.HEALTHY if indexer else HealthStatus.UNHEALTHY
            
            await orchestrator.add_health_collector(
                "project_indexing",
                check_indexing_health,
                description="Project indexing service health"
            )
    except Exception as e:
        logger.debug(f"Failed to add project indexing health collector: {e}")


async def _add_memory_reliability_health_collector(orchestrator):
    """Add memory reliability health monitoring to orchestrator."""
    try:
        from ..services.memory_reliability import get_memory_reliability_service
        
        reliability_service = await get_memory_reliability_service()
        if reliability_service:
            # Add health check for memory reliability
            def check_memory_reliability():
                return HealthStatus.HEALTHY if reliability_service else HealthStatus.UNHEALTHY
            
            await orchestrator.add_health_collector(
                "memory_reliability",
                check_memory_reliability,
                description="Memory reliability service health"
            )
    except Exception as e:
        logger.debug(f"Failed to add memory reliability health collector: {e}")


async def _get_managed_projects_health():
    """Get health status of managed projects."""
    try:
        managed_path = get_managed_path()
        if not managed_path.exists():
            return {"status": "no_managed_projects", "projects": []}
        
        projects = []
        for project_dir in managed_path.iterdir():
            if project_dir.is_dir() and (project_dir / ".claude-pm").exists():
                projects.append({
                    "name": project_dir.name,
                    "path": str(project_dir),
                    "status": "healthy"
                })
        
        return {
            "status": "healthy" if projects else "no_projects",
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        logger.error(f"Failed to get managed projects health: {e}")
        return {"status": "error", "error": str(e)}


def _display_unified_health_dashboard(dashboard, managed_projects_health, detailed, verbose):
    """Display unified health dashboard."""
    try:
        # Framework Core Health
        console.print("[bold]Framework Core Health[/bold]")
        if dashboard.current_report:
            for service_name, health_info in dashboard.current_report.services.items():
                status_icon = "🟢" if health_info.status == HealthStatus.HEALTHY else "🔴"
                console.print(f"  {status_icon} {service_name}: {health_info.status.value}")
                
                if detailed and health_info.details:
                    for detail_key, detail_value in health_info.details.items():
                        console.print(f"    • {detail_key}: {detail_value}")
        
        # Managed Projects Health
        console.print(f"\n[bold]Managed Projects ({managed_projects_health.get('count', 0)})[/bold]")
        if managed_projects_health.get('projects'):
            for project in managed_projects_health['projects']:
                console.print(f"  🟢 {project['name']}: {project['status']}")
        else:
            console.print("  📁 No managed projects detected")
        
        console.print("")
        
    except Exception as e:
        logger.error(f"Failed to display unified health dashboard: {e}")
        console.print(f"❌ Error displaying health dashboard: {e}")


async def _display_memory_service_health(verbose):
    """Display memory service specific health."""
    try:
        from ..services.memory_reliability import get_memory_reliability_service
        
        console.print("[bold]Memory Service Health[/bold]")
        
        reliability_service = await get_memory_reliability_service()
        if reliability_service:
            console.print("  🟢 Memory Reliability: HEALTHY")
            if verbose:
                console.print("    • Service initialized and ready")
        else:
            console.print("  🔴 Memory Reliability: UNAVAILABLE")
        
        console.print("")
        
    except Exception as e:
        logger.error(f"Failed to display memory service health: {e}")
        console.print(f"❌ Error checking memory service: {e}")


async def _display_indexing_service_health(verbose):
    """Display indexing service specific health."""
    try:
        from ..services.project_indexer import create_project_indexer
        
        console.print("[bold]Indexing Service Health[/bold]")
        
        indexer = await create_project_indexer()
        if indexer:
            console.print("  🟢 Project Indexing: HEALTHY")
            if verbose:
                console.print("    • Indexer service initialized")
        else:
            console.print("  🔴 Project Indexing: UNAVAILABLE")
        
        console.print("")
        
    except Exception as e:
        logger.error(f"Failed to display indexing service health: {e}")
        console.print(f"❌ Error checking indexing service: {e}")


def _display_projects_health(managed_projects_health, verbose):
    """Display projects specific health."""
    console.print("[bold]Projects Health[/bold]")
    
    if managed_projects_health.get('projects'):
        for project in managed_projects_health['projects']:
            console.print(f"  🟢 {project['name']}: {project['status']}")
            if verbose:
                console.print(f"    • Path: {project['path']}")
    else:
        console.print("  📁 No managed projects detected")
    
    console.print("")


async def _export_health_data(dashboard, managed_projects_health, export_format):
    """Export health data to specified format."""
    try:
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "framework_health": dashboard.current_report.to_dict() if dashboard.current_report else {},
            "managed_projects": managed_projects_health
        }
        
        export_file = f"health_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        
        if export_format == "json":
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
        elif export_format == "yaml":
            import yaml
            with open(export_file, 'w') as f:
                yaml.dump(export_data, f, default_flow_style=False)
        
        console.print(f"✅ Health data exported to: {export_file}")
        
    except Exception as e:
        logger.error(f"Failed to export health data: {e}")
        console.print(f"❌ Export failed: {e}")


async def _generate_health_report(dashboard, managed_projects_health):
    """Generate detailed health report."""
    try:
        report_file = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w') as f:
            f.write(f"# Claude PM Framework Health Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            f.write(f"## Framework Services\n\n")
            if dashboard.current_report:
                for service_name, health_info in dashboard.current_report.services.items():
                    f.write(f"### {service_name}\n")
                    f.write(f"Status: {health_info.status.value}\n")
                    if health_info.details:
                        for detail_key, detail_value in health_info.details.items():
                            f.write(f"- {detail_key}: {detail_value}\n")
                    f.write(f"\n")
            
            f.write(f"## Managed Projects\n\n")
            if managed_projects_health.get('projects'):
                for project in managed_projects_health['projects']:
                    f.write(f"- **{project['name']}**: {project['status']}\n")
                    f.write(f"  - Path: {project['path']}\n")
            else:
                f.write(f"No managed projects detected.\n")
        
        console.print(f"✅ Health report generated: {report_file}")
        
    except Exception as e:
        logger.error(f"Failed to generate health report: {e}")
        console.print(f"❌ Report generation failed: {e}")


def register_setup_commands(cli_group):
    """Register all setup commands with the main CLI group."""
    
    @cli_group.command()
    @click.option(
        "--target-dir",
        type=click.Path(),
        help="Target directory (defaults to parent of current working directory)",
    )
    @click.option("--backup/--no-backup", default=True, help="Create backup of existing CLAUDE.md file")
    @click.option("--force", is_flag=True, help="Force overwrite without confirmation")
    @click.pass_context
    def setup(ctx, target_dir, backup, force):
        """🚀 Setup CLAUDE.md template in parent directory with deployment-aware configuration."""

        async def run():
            from ..commands.template_commands import deploy_claude_md

            # Create a mock Click context for the template command
            import click

            template_ctx = click.Context(deploy_claude_md)
            template_ctx.params = {"target_dir": target_dir, "backup": backup, "force": force}

            try:
                # Import the deploy_claude_md function directly
                from ..commands.template_commands import deploy_claude_md

                # Run the deployment directly
                # Initialize template deployment integration
                integration = TemplateDeploymentIntegration()
                await integration._initialize()

                # Get deployment config
                deployment_config = await integration.get_deployment_aware_template_config()

                # Determine target directory
                if target_dir:
                    target_directory = Path(target_dir)
                else:
                    target_directory = Path.cwd().parent

                # Ensure target directory exists
                target_directory.mkdir(parents=True, exist_ok=True)

                # Check for framework CLAUDE.md template
                # Use explicit framework path to avoid deployment detection issues
                framework_path = Path(__file__).parent.parent.parent  # Go up to project root
                framework_template_path = framework_path / "framework" / "CLAUDE.md"

                if not framework_template_path.exists():
                    console.print(
                        f"❌ Framework CLAUDE.md template not found at: {framework_template_path}"
                    )
                    return

                # Read template content
                template_content = framework_template_path.read_text()

                # Set up template variables for handlebars processing
                # Get framework template serial for FRAMEWORK_VERSION
                framework_version_file = framework_path / "FRAMEWORK_VERSION"
                if framework_version_file.exists():
                    framework_version = framework_version_file.read_text().strip()  # This is the serial (010)
                else:
                    # Fallback to default serial
                    framework_version = "001"
                
                template_variables = {
                    "FRAMEWORK_VERSION": framework_version,  # Serial from FRAMEWORK_VERSION (010)
                    "CLAUDE_MD_VERSION": _get_framework_version(),  # Main version from VERSION (0.4.6)
                    "DEPLOYMENT_DATE": datetime.now().isoformat(),
                    "PLATFORM": platform.system().lower(),
                    "PYTHON_CMD": "python3",
                    "DEPLOYMENT_ID": str(int(datetime.now().timestamp() * 1000)),
                    "DEPLOYMENT_DIR": str(framework_path),
                    "WORKING_DIR": str(Path.cwd()),
                    "TARGET_DIR": str(target_directory),
                    "AI_TRACKDOWN_PATH": "/Users/masa/.nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/ai-trackdown-tools/dist/index.js",
                    "PLATFORM_NOTES": "**macOS-specific:**\n- Use `.sh` files for scripts\n- CLI wrappers: `bin/aitrackdown` and `bin/atd`\n- Health check: `scripts/health-check.sh`\n- May require Xcode Command Line Tools",
                    "LAST_UPDATED": datetime.now().isoformat(),
                }

                console.print(f"🔧 [bold]Setting up CLAUDE.md Template[/bold]")
                console.print(f"   • Framework Path: {framework_path}")
                console.print(f"   • Template Path: {framework_template_path}")
                console.print(f"   • Target Directory: {target_directory}")

                # Process handlebars variables
                processed_content = template_content
                for key, value in template_variables.items():
                    placeholder = f"{{{{{key}}}}}"
                    processed_content = processed_content.replace(placeholder, str(value))

                # Handle target file
                target_file = target_directory / "CLAUDE.md"

                # Create backup if file exists and backup is enabled
                if target_file.exists() and backup:
                    backup_filename = f"CLAUDE.md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    backup_path = target_directory / backup_filename
                    shutil.copy2(target_file, backup_path)
                    console.print(f"   • Created backup: {backup_path}")

                # Check if file exists and get confirmation
                if target_file.exists() and not force:
                    if not Confirm.ask(f"CLAUDE.md already exists at {target_file}. Overwrite?"):
                        console.print("❌ Setup cancelled")
                        return

                # Write processed content
                target_file.write_text(processed_content)

                console.print(f"✅ [bold green]CLAUDE.md setup completed![/bold green]")
                console.print(f"   • Target: {target_file}")
                console.print(f"   • Size: {len(processed_content)} characters")
                console.print(f"   • Variables processed: {len(template_variables)}")

                await integration._cleanup()

            except Exception as e:
                console.print(f"❌ Setup failed: {e}")
                logger.error(f"Setup command failed: {e}")

        asyncio.run(run())

    @cli_group.command()
    @click.option("--detailed", is_flag=True, help="Show detailed subsystem information")
    @click.option(
        "--service",
        type=click.Choice(["memory", "indexing", "projects", "all"]),
        default="all",
        help="Focus on specific service",
    )
    @click.option("--export", type=click.Choice(["json", "yaml"]), help="Export health data")
    @click.option("--report", is_flag=True, help="Generate detailed health report")
    @click.option("--verbose", "-v", is_flag=True, help="Verbose output with full diagnostics")
    @click.pass_context
    def health(ctx, detailed, service, export, report, verbose):
        """🏥 Unified Health Dashboard - Central monitoring for all framework subsystems (M01-044)."""

        async def run():
            from ..services.health_dashboard import HealthDashboardOrchestrator
            from ..services.project_indexer import create_project_indexer
            from ..services.project_memory_manager import create_project_memory_manager
            from ..services.memory_reliability import get_memory_reliability_service
            from ..integrations.mem0ai_integration import create_mem0ai_integration

            start_time = time.time()

            try:
                console.print("[bold blue]🟢 Claude PM Framework Health Dashboard[/bold blue]")
                console.print("═══════════════════════════════════════\n")

                # Initialize orchestrator with enhanced collectors for M01-044
                orchestrator = HealthDashboardOrchestrator()

                # Add MEM-007 project indexing health monitoring
                await _add_project_indexing_health_collector(orchestrator)
                
                # Add memory reliability health monitoring
                await _add_memory_reliability_health_collector(orchestrator)

                # Get comprehensive health dashboard
                dashboard = await orchestrator.get_health_dashboard(force_refresh=True)

                # Add managed projects portfolio health
                managed_projects_health = await _get_managed_projects_health()

                # Display unified dashboard
                if service == "all":
                    _display_unified_health_dashboard(
                        dashboard, managed_projects_health, detailed, verbose
                    )
                elif service == "memory":
                    await _display_memory_service_health(verbose)
                elif service == "indexing":
                    await _display_indexing_service_health(verbose)
                elif service == "projects":
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
                console.print(
                    f"[dim]{cache_indicator} Health check completed in {total_time:.0f}ms[/dim]"
                )

            except Exception as e:
                console.print(f"❌ Health check failed: {e}")
                logger.error(f"Health command failed: {e}")

        asyncio.run(run())

    return cli_group