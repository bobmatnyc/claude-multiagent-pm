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
from ..services.project_service import ProjectService
# TemplateDeploymentIntegration removed - use Claude Code Task Tool instead
from ..models.health import HealthStatus, create_service_health_report
# PMAgent removed - use Claude Code Task Tool instead
from ..utils.framework_detection import is_framework_source_directory

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
    """Add project indexing health monitoring to orchestrator - SERVICE REMOVED."""
    try:
        logger.debug("Project indexing service removed - use native project discovery instead")
        return None
    except Exception as e:
        logger.debug(f"Failed to add project indexing health collector: {e}")



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




async def _display_indexing_service_health(verbose):
    """Display indexing service specific health - SERVICE REMOVED."""
    try:
        console.print("[bold]Indexing Service Health[/bold]")
        console.print("  ❌ Project Indexing: REMOVED")
        if verbose:
            console.print("    • Service removed - use native project discovery instead")
        
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
    @click.option('--framework-dev', is_flag=True, help='Allow deployment in framework source directory (developer mode)')
    @click.pass_context
    def setup(ctx, target_dir, backup, force, framework_dev):
        """🚀 Setup CLAUDE.md template in parent directory with deployment-aware configuration."""

        async def run():
            manager = None  # Initialize to None to avoid undefined variable issues
            try:
                # Import ParentDirectoryManager for CLAUDE.md deployment
                from ..services.parent_directory_manager import ParentDirectoryManager

                # Check if we're in the framework source directory
                current_dir = Path.cwd()
                is_framework_source, framework_markers = is_framework_source_directory(current_dir)
                
                if is_framework_source and not framework_dev:
                    console.print("[bold yellow]⚠️  Framework Source Directory Detected[/bold yellow]")
                    console.print(f"[dim]   Detected markers: {', '.join(framework_markers)}[/dim]")
                    console.print("[dim]   Skipping CLAUDE.md deployment to preserve development file[/dim]")
                    console.print("[dim]   Use --framework-dev flag to force deployment if needed[/dim]")
                    return

                # Determine target directory
                if target_dir:
                    target_directory = Path(target_dir)
                else:
                    target_directory = Path.cwd().parent

                # Ensure target directory exists
                target_directory.mkdir(parents=True, exist_ok=True)

                console.print(f"🔧 [bold]Setting up CLAUDE.md Template[/bold]")
                console.print(f"   • Target Directory: {target_directory}")

                # Initialize Parent Directory Manager
                manager = ParentDirectoryManager()
                await manager._initialize()

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

                # Deploy CLAUDE.md using Parent Directory Manager
                operation = await manager.install_template_to_parent_directory(
                    target_directory=target_directory,
                    template_id="claude_md",
                    template_variables=None,  # Use default deployment variables
                    force=force  # Use the force flag from command line
                )

                if operation.success:
                    console.print(f"✅ [bold green]CLAUDE.md setup completed![/bold green]")
                    console.print(f"   • Target: {operation.target_path}")
                    if operation.backup_path:
                        console.print(f"   • Backup: {operation.backup_path}")
                else:
                    console.print(f"❌ Setup failed: {operation.error_message}")
                    logger.error(f"Setup command failed: {operation.error_message}")

            except ImportError as e:
                console.print(f"❌ Import error: {e}")
                console.print("💡 Try using 'claude-pm init' instead for basic setup")
                logger.error(f"Setup command import error: {e}")
            except Exception as e:
                console.print(f"❌ Setup failed: {e}")
                logger.error(f"Setup command failed: {e}")
            finally:
                # Cleanup manager resources only if it was initialized
                if manager is not None:
                    try:
                        await manager._cleanup()
                    except Exception as cleanup_error:
                        logger.debug(f"Cleanup error (non-critical): {cleanup_error}")

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
    @click.pass_context
    def health(ctx, detailed, service, export, report):
        """🏥 Unified Health Dashboard - Central monitoring for all framework subsystems (M01-044)."""

        async def run():
            from ..services.health_dashboard import HealthDashboardOrchestrator
            # project_indexer removed - use native project discovery instead

            start_time = time.time()
            
            # Get verbose from parent context
            verbose = ctx.obj.get("verbose", False) if ctx.obj else False

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
                if service == "all":
                    _display_unified_health_dashboard(
                        dashboard, managed_projects_health, detailed, verbose
                    )
                elif service == "memory":
                    console.print("[bold]Memory Service Health[/bold]")
                    console.print("  🔴 Memory Service: DISABLED")
                    console.print("    • Memory system removed for clean slate implementation")
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
    
    @cli_group.command()
    @click.option('--force', is_flag=True, help='Force re-initialization even if already set up')
    @click.option('--post-install', is_flag=True, help='Run post-installation process (NPM functionality)')
    @click.option('--skip-postinstall', is_flag=True, help='Skip post-installation process')
    @click.option('--postinstall-only', is_flag=True, help='Run only post-installation process')
    @click.option('--validate', is_flag=True, help='Validate post-installation completeness')
    @click.option('--comprehensive-validation', is_flag=True, help='Run comprehensive post-installation validation')
    @click.option('--framework-dev', is_flag=True, help='Allow deployment in framework source directory (developer mode)')
    @click.pass_context
    def init(ctx, force, post_install, skip_postinstall, postinstall_only, validate, comprehensive_validation, framework_dev):
        """🛠️ Initialize Claude PM Framework with comprehensive setup and post-installation support.
        
        This command supports all the functionality previously in NPM postinstall.js:
        
        Examples:
            claude-pm init                     # Standard initialization
            claude-pm init --post-install      # Include post-installation process
            claude-pm init --postinstall-only  # Run only post-installation
            claude-pm init --validate          # Validate post-installation
            claude-pm init --comprehensive-validation  # Run comprehensive validation
            claude-pm init --force             # Force re-initialization
        """
        console.print("[bold blue]🛠️ Claude PM Framework Initialization[/bold blue]")
        
        # Determine post-installation behavior
        if postinstall_only:
            console.print("[dim]Running post-installation process only...[/dim]")
            run_post_install = True
            run_framework_init = False
        elif skip_postinstall:
            console.print("[dim]Skipping post-installation process...[/dim]")
            run_post_install = False
            run_framework_init = True
        elif post_install:
            console.print("[dim]Including post-installation process...[/dim]")
            run_post_install = True
            run_framework_init = True
        else:
            console.print("[dim]Standard initialization (no post-install)...[/dim]")
            run_post_install = False
            run_framework_init = True
        
        async def run():
            try:
                # Basic framework initialization without agent system
                console.print("[bold blue]🔧 Framework Initialization[/bold blue]")
                
                # Create basic framework directories
                framework_path = Path.home() / ".claude-pm"
                framework_path.mkdir(parents=True, exist_ok=True)
                
                # Create basic config
                config_path = framework_path / "config.json"
                if not config_path.exists() or force:
                    config_data = {
                        "version": _get_framework_version(),
                        "installationType": "python",
                        "installationComplete": True,
                        "timestamp": datetime.now().isoformat(),
                        "framework_path": str(framework_path),
                        "agent_system": "disabled"  # Agent system removed
                    }
                    
                    with open(config_path, 'w') as f:
                        json.dump(config_data, f, indent=2)
                    
                    console.print(f"✅ Created configuration: {config_path}")
                
                # Create basic directory structure
                dirs_to_create = [
                    framework_path / "logs",
                    framework_path / "templates",
                    framework_path / "memory",
                ]
                
                for dir_path in dirs_to_create:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    console.print(f"✅ Created directory: {dir_path}")
                
                # Check for tasks/ to tickets/ migration
                console.print("[bold blue]🔄 Checking for legacy tasks/ directory...[/bold blue]")
                try:
                    from ..utils.tasks_to_tickets_migration import check_and_migrate_tasks_directory
                    
                    # Check current directory for migration needs
                    current_dir = Path.cwd()
                    migration_result = await check_and_migrate_tasks_directory(current_dir, silent=False)
                    
                    if migration_result.get("migrated"):
                        console.print(f"✅ Successfully migrated tasks/ to tickets/")
                        console.print(f"   Files migrated: {migration_result.get('files_migrated', 0)}")
                        if migration_result.get('backup_created'):
                            console.print(f"   Backup saved: {Path(migration_result['backup_created']).name}")
                    elif migration_result.get("success"):
                        console.print("[dim]✓ No tasks/ directory migration needed[/dim]")
                        
                except Exception as migration_error:
                    console.print(f"[yellow]⚠️ Migration check failed: {migration_error}[/yellow]")
                    logger.warning(f"Tasks to tickets migration failed: {migration_error}")
                    # Continue with initialization even if migration fails
                
                # Initialize ticketing if not already present
                console.print("[bold blue]🎫 Initializing ticketing system...[/bold blue]")
                try:
                    tickets_dir = current_dir / "tickets"
                    if not tickets_dir.exists():
                        # Create ticketing structure
                        for subdir in ['epics', 'issues', 'tasks', 'prs', 'templates', 'archive', 'reports']:
                            (tickets_dir / subdir).mkdir(parents=True, exist_ok=True)
                        
                        # Create .ai-trackdown directory and counters
                        tracking_dir = tickets_dir / '.ai-trackdown'
                        tracking_dir.mkdir(parents=True, exist_ok=True)
                        
                        counters_file = tracking_dir / 'counters.json'
                        if not counters_file.exists():
                            counters = {
                                "epic": 0,
                                "issue": 0,
                                "task": 0,
                                "pr": 0
                            }
                            counters_file.write_text(json.dumps(counters, indent=2))
                        
                        console.print(f"✅ Created ticketing structure at: {tickets_dir}")
                    else:
                        console.print("[dim]✓ Ticketing directory already exists[/dim]")
                    
                    # Check if ai-trackdown-pytools is available
                    try:
                        import ai_trackdown_pytools
                        console.print("✅ ai-trackdown-pytools is installed - ticketing enabled")
                    except ImportError:
                        console.print("[yellow]⚠️ ai-trackdown-pytools not installed - ticketing features limited[/yellow]")
                        console.print("[dim]   Install with: pip install --user ai-trackdown-pytools==1.4.0[/dim]")
                        
                except Exception as ticketing_error:
                    console.print(f"[yellow]⚠️ Ticketing initialization failed: {ticketing_error}[/yellow]")
                    logger.warning(f"Ticketing initialization failed: {ticketing_error}")
                    # Continue with initialization even if ticketing fails
                
                # Check if we're in the framework source directory before deploying CLAUDE.md
                current_dir = Path.cwd()
                parent_dir = current_dir.parent
                
                # Detect framework source directory markers
                is_framework_source, framework_markers = is_framework_source_directory(current_dir)
                
                if is_framework_source and not framework_dev:
                    console.print("[bold yellow]⚠️  Framework Source Directory Detected[/bold yellow]")
                    console.print(f"[dim]   Detected markers: {', '.join(framework_markers)}[/dim]")
                    console.print("[dim]   Skipping CLAUDE.md deployment to preserve development file[/dim]")
                    console.print("[dim]   Use --framework-dev flag to force deployment if needed[/dim]")
                    
                    # Skip loading framework into Claude Code since we didn't deploy
                    console.print("[dim]   Skipping framework loading into Claude Code[/dim]")
                    target_file = None  # Set to None so we skip the loading step
                else:
                    # Always attempt to deploy CLAUDE.md to parent directory (not just with force flag)
                    # This ensures framework is deployed immediately after pip install
                    console.print("[bold blue]🚀 Deploying CLAUDE.md to parent directory[/bold blue]")
                    
                    target_file = parent_dir / "CLAUDE.md"
                    
                    try:
                        from ..services.parent_directory_manager import ParentDirectoryManager
                        
                        # Initialize Parent Directory Manager
                        manager = ParentDirectoryManager()
                        await manager._initialize()
                        
                        # Check if CLAUDE.md already exists
                        if target_file.exists() and not force:
                            console.print(f"[dim]ℹ️  CLAUDE.md already exists at {target_file}[/dim]")
                            console.print(f"[dim]   Use --force to update it[/dim]")
                        else:
                            # Deploy CLAUDE.md
                            operation = await manager.install_template_to_parent_directory(
                                target_directory=parent_dir,
                                template_id="claude_md",
                                template_variables=None,  # Use defaults
                                force=force  # Use force flag if provided
                            )
                            
                            if operation.success:
                                console.print(f"✅ CLAUDE.md deployed to: {operation.target_path}")
                                if operation.backup_path:
                                    console.print(f"📁 Backup created: {operation.backup_path}")
                            else:
                                console.print(f"❌ CLAUDE.md deployment failed: {operation.error_message}")
                                logger.error(f"CLAUDE.md deployment failed: {operation.error_message}")
                        
                        if 'manager' in locals():
                            await manager._cleanup()
                        
                    except Exception as deploy_error:
                        console.print(f"❌ CLAUDE.md deployment error: {deploy_error}")
                        logger.error(f"CLAUDE.md deployment error: {deploy_error}")
                        # Continue with initialization even if deployment fails
                
                # Load framework into Claude Code if CLAUDE.md was deployed
                if target_file and target_file.exists():
                    console.print("[bold blue]🔄 Loading framework into Claude Code...[/bold blue]")
                    try:
                        from ..services.claude_code_integration import load_framework_into_claude_code, create_framework_loading_summary
                        
                        # Load framework with retry logic
                        framework_loaded = await load_framework_into_claude_code()
                        
                        # Create and display summary
                        summary = await create_framework_loading_summary()
                        console.print(summary)
                        
                        if framework_loaded:
                            console.print("[green]✅ Framework successfully loaded into Claude Code![/green]")
                            console.print("[dim]🎯 Framework is now active and ready for use[/dim]")
                        else:
                            console.print("[yellow]⚠️ Framework initialization completed but Claude Code loading failed[/yellow]")
                            console.print("[dim]💡 You can still use claude-pm commands, but framework may not be fully active[/dim]")
                            
                    except Exception as loading_error:
                        console.print(f"[red]❌ Framework loading error: {loading_error}[/red]")
                        logger.error(f"Framework loading error: {loading_error}")
                        console.print("[dim]💡 Framework initialization completed but loading failed[/dim]")
                
                console.print("[green]\n✅ Framework initialization completed successfully![/green]")
                console.print("[dim]🚀 You can now use claude-pm commands[/dim]")
                console.print("[dim]📖 Use Claude Code Task Tool for agent functionality[/dim]")
                
                return True
                    
            except Exception as e:
                console.print(f"[red]❌ Initialization error: {e}[/red]")
                logger.error(f"Init command failed: {e}")
                return False
        
        success = asyncio.run(run())
        if not success:
            sys.exit(1)

    return cli_group