#!/usr/bin/env python3
"""
Deployment Commands - ISS-0112 Claude PM Transformation

CLI commands for framework deployment, verification, and management.
Integrates with NPM installation architecture and provides comprehensive deployment operations.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.logging_config import get_logger
from ..services.framework_deployment_validator import FrameworkDeploymentValidator
from ..services.working_directory_deployer import (
    WorkingDirectoryDeployer, 
    DeploymentConfig,
    DeploymentResult
)
from ..core.deployment_enforcement import get_deployment_enforcer

logger = get_logger(__name__)
console = Console()


@click.group(name='deploy')
def deployment_commands():
    """Framework deployment and management commands."""
    pass


@deployment_commands.command()
@click.option('--working-directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Target working directory (defaults to current directory)')
@click.option('--force', '-f', is_flag=True, 
              help='Force deployment even if target already exists')
@click.option('--no-backup', is_flag=True,
              help='Skip backup creation before deployment')
@click.option('--no-verify', is_flag=True,
              help='Skip post-deployment verification')
@click.option('--dry-run', is_flag=True,
              help='Show what would be deployed without making changes')
def deploy(working_directory: Optional[Path], force: bool, no_backup: bool, 
          no_verify: bool, dry_run: bool):
    """Deploy Claude PM framework to working directory."""
    
    async def run_deployment():
        console.print("🚀 [bold blue]Claude PM Framework Deployment[/bold blue]")
        console.print()
        
        # Set defaults
        target_dir = working_directory or Path.cwd()
        
        try:
            deployer = WorkingDirectoryDeployer()
            
            # Configure deployment
            config = DeploymentConfig(
                source_path=Path.home() / ".claude-pm",
                target_path=target_dir / ".claude-pm",
                force_deployment=force,
                preserve_existing=not force,
                create_backup=not no_backup,
                verify_after_deployment=not no_verify
            )
            
            # Dry run mode
            if dry_run:
                await _show_deployment_preview(deployer, config)
                return
            
            # Pre-deployment status
            console.print("📋 [bold]Pre-deployment Status:[/bold]")
            pre_status = await deployer.get_deployment_status(target_dir)
            _display_deployment_status(pre_status)
            console.print()
            
            # Perform deployment with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Deploying framework...", total=None)
                
                result = await deployer.deploy_to_working_directory(target_dir, config)
                
                progress.update(task, completed=True)
            
            # Display results
            _display_deployment_result(result)
            
            # Post-deployment status
            if result.success:
                console.print("\n📊 [bold]Post-deployment Status:[/bold]")
                post_status = await deployer.get_deployment_status(target_dir)
                _display_deployment_status(post_status)
                
                if result.validation_result and not result.validation_result.is_valid:
                    console.print("\n⚠️  [yellow]Warning: Post-deployment validation failed[/yellow]")
                    _display_validation_issues(result.validation_result)
                else:
                    console.print("\n✅ [green]Framework deployment completed successfully![/green]")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            console.print(f"\n❌ [red]Deployment failed: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(run_deployment())


@deployment_commands.command()
@click.option('--working-directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Working directory to verify (defaults to current directory)')
@click.option('--detailed', is_flag=True,
              help='Show detailed validation information')
@click.option('--json-output', is_flag=True,
              help='Output results in JSON format')
def verify(working_directory: Optional[Path], detailed: bool, json_output: bool):
    """Verify framework deployment status."""
    
    async def run_verification():
        target_dir = working_directory or Path.cwd()
        
        try:
            validator = FrameworkDeploymentValidator()
            
            if not json_output:
                console.print("🔍 [bold blue]Framework Deployment Verification[/bold blue]")
                console.print()
            
            # Perform validation
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                disable=json_output
            ) as progress:
                if not json_output:
                    task = progress.add_task("Validating deployment...", total=None)
                
                result = await validator.validate_deployment(target_dir)
                
                if not json_output:
                    progress.update(task, completed=True)
            
            # Output results
            if json_output:
                verification_data = {
                    'valid': result.is_valid,
                    'framework_deployed': result.framework_deployed,
                    'npm_installation_found': result.npm_installation_found,
                    'working_directory_configured': result.working_directory_configured,
                    'claude_pm_directory': str(result.claude_pm_directory) if result.claude_pm_directory else None,
                    'validation_details': result.validation_details,
                    'error_message': result.error_message,
                    'actionable_guidance': result.actionable_guidance
                }
                console.print(json.dumps(verification_data, indent=2))
            else:
                _display_verification_result(result, detailed)
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            if json_output:
                console.print(json.dumps({'error': str(e)}, indent=2))
            else:
                console.print(f"\n❌ [red]Verification failed: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(run_verification())


@deployment_commands.command()
@click.option('--working-directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Working directory to check (defaults to current directory)')
@click.option('--json-output', is_flag=True,
              help='Output status in JSON format')
def status(working_directory: Optional[Path], json_output: bool):
    """Show deployment status for working directory."""
    
    async def run_status_check():
        target_dir = working_directory or Path.cwd()
        
        try:
            deployer = WorkingDirectoryDeployer()
            
            if not json_output:
                console.print("📊 [bold blue]Deployment Status[/bold blue]")
                console.print()
            
            status_info = await deployer.get_deployment_status(target_dir)
            
            if json_output:
                console.print(json.dumps(status_info, indent=2))
            else:
                _display_deployment_status(status_info)
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            if json_output:
                console.print(json.dumps({'error': str(e)}, indent=2))
            else:
                console.print(f"\n❌ [red]Status check failed: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(run_status_check())


@deployment_commands.command()
@click.option('--search-path', '-s', type=click.Path(exists=True, path_type=Path),
              help='Directory to search for deployments (defaults to current directory)')
@click.option('--json-output', is_flag=True,
              help='Output results in JSON format')
def list(search_path: Optional[Path], json_output: bool):
    """List all framework deployments in directory tree."""
    
    async def run_list():
        search_dir = search_path or Path.cwd()
        
        try:
            deployer = WorkingDirectoryDeployer()
            
            if not json_output:
                console.print("🔍 [bold blue]Framework Deployment Discovery[/bold blue]")
                console.print()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                disable=json_output
            ) as progress:
                if not json_output:
                    task = progress.add_task("Searching for deployments...", total=None)
                
                deployments = await deployer.list_deployments(search_dir)
                
                if not json_output:
                    progress.update(task, completed=True)
            
            if json_output:
                console.print(json.dumps(deployments, indent=2))
            else:
                _display_deployments_list(deployments)
            
        except Exception as e:
            logger.error(f"Deployment discovery failed: {e}")
            if json_output:
                console.print(json.dumps({'error': str(e)}, indent=2))
            else:
                console.print(f"\n❌ [red]Discovery failed: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(run_list())


@deployment_commands.command()
@click.option('--working-directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Working directory to undeploy (defaults to current directory)')
@click.option('--no-backup', is_flag=True,
              help='Skip backup creation before removal')
@click.option('--confirm', is_flag=True,
              help='Skip confirmation prompt')
def undeploy(working_directory: Optional[Path], no_backup: bool, confirm: bool):
    """Remove framework deployment from working directory."""
    
    async def run_undeploy():
        target_dir = working_directory or Path.cwd()
        
        try:
            deployer = WorkingDirectoryDeployer()
            
            console.print("🗑️  [bold red]Framework Undeployment[/bold red]")
            console.print()
            
            # Check if deployment exists
            status_info = await deployer.get_deployment_status(target_dir)
            if not status_info['deployed']:
                console.print(f"ℹ️  No deployment found in {target_dir}")
                return
            
            # Confirmation
            if not confirm:
                console.print(f"⚠️  This will remove the Claude PM framework deployment from:")
                console.print(f"   {target_dir / '.claude-pm'}")
                console.print()
                
                if not click.confirm("Are you sure you want to proceed?"):
                    console.print("Undeployment cancelled.")
                    return
            
            # Perform undeployment
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Removing deployment...", total=None)
                
                success = await deployer.undeploy_from_working_directory(
                    target_dir, 
                    create_backup=not no_backup
                )
                
                progress.update(task, completed=True)
            
            if success:
                console.print("\n✅ [green]Framework deployment removed successfully![/green]")
            else:
                console.print("\n❌ [red]Failed to remove deployment[/red]")
                sys.exit(1)
            
        except Exception as e:
            logger.error(f"Undeployment failed: {e}")
            console.print(f"\n❌ [red]Undeployment failed: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(run_undeploy())


@deployment_commands.command()
def diagnose():
    """Run comprehensive deployment diagnostics."""
    
    async def run_diagnostics():
        console.print("🔧 [bold blue]Claude PM Framework Diagnostics[/bold blue]")
        console.print()
        
        try:
            enforcer = get_deployment_enforcer()
            validator = FrameworkDeploymentValidator()
            
            # System-wide diagnostics
            console.print("🖥️  [bold]System Diagnostics:[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running diagnostics...", total=None)
                
                # Check npm installation
                npm_home = Path.home() / ".claude-pm"
                console.print(f"   NPM Home: {npm_home} ({'✅ Exists' if npm_home.exists() else '❌ Missing'})")
                
                # Check current directory deployment
                current_deployment = await validator.validate_deployment(Path.cwd())
                console.print(f"   Current Directory: {'✅ Deployed' if current_deployment.is_valid else '❌ Not Deployed'}")
                
                # Get comprehensive status
                status = await enforcer.check_deployment_status()
                
                progress.update(task, completed=True)
            
            console.print()
            
            # Display detailed status
            _display_diagnostic_results(status, current_deployment)
            
            # Generate report
            report = await validator.generate_deployment_report()
            
            console.print("\n📄 [bold]Detailed Report:[/bold]")
            console.print(Panel(report, border_style="blue", padding=(1, 2)))
            
        except Exception as e:
            logger.error(f"Diagnostics failed: {e}")
            console.print(f"\n❌ [red]Diagnostics failed: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(run_diagnostics())


# Helper functions for display

async def _show_deployment_preview(deployer: WorkingDirectoryDeployer, config: DeploymentConfig):
    """Show deployment preview for dry run."""
    console.print("🔍 [bold]Deployment Preview (Dry Run)[/bold]")
    console.print()
    
    preview_table = Table(show_header=True, header_style="bold magenta")
    preview_table.add_column("Component", style="cyan")
    preview_table.add_column("Source", style="yellow")
    preview_table.add_column("Target", style="green")
    
    for target_name, source_path in deployer.template_files.items():
        source_file = config.source_path / source_path
        target_file = config.target_path / target_name
        
        preview_table.add_row(
            target_name,
            str(source_file),
            str(target_file)
        )
    
    console.print(preview_table)
    console.print()
    console.print(f"📁 Target Directory: {config.target_path}")
    console.print(f"🔧 Force Deployment: {'Yes' if config.force_deployment else 'No'}")
    console.print(f"💾 Create Backup: {'Yes' if config.create_backup else 'No'}")
    console.print(f"✅ Verify After: {'Yes' if config.verify_after_deployment else 'No'}")


def _display_deployment_result(result: DeploymentResult):
    """Display deployment result."""
    if result.success:
        console.print(f"✅ [green]Deployment successful to {result.target_directory}[/green]")
        
        if result.deployed_files:
            console.print(f"\n📦 Deployed {len(result.deployed_files)} files:")
            for file_name in result.deployed_files:
                console.print(f"   • {file_name}")
        
        if result.backup_location:
            console.print(f"\n💾 Backup created at: {result.backup_location}")
    else:
        console.print(f"❌ [red]Deployment failed: {result.error_message}[/red]")


def _display_verification_result(result, detailed: bool):
    """Display verification result."""
    # Status overview
    status_panel = Panel(
        f"{'✅ VALID' if result.is_valid else '❌ INVALID'}\n\n"
        f"NPM Installation: {'✅ Found' if result.npm_installation_found else '❌ Missing'}\n"
        f"Framework Deployed: {'✅ Yes' if result.framework_deployed else '❌ No'}\n"
        f"Working Directory: {'✅ Configured' if result.working_directory_configured else '❌ Not Configured'}",
        title="🎯 Validation Summary",
        border_style="green" if result.is_valid else "red",
        padding=(1, 2)
    )
    console.print(status_panel)
    
    # Detailed information
    if detailed and result.validation_details:
        console.print("\n🔍 [bold]Detailed Validation Information:[/bold]")
        console.print(json.dumps(result.validation_details, indent=2))
    
    # Error guidance
    if not result.is_valid and result.actionable_guidance:
        console.print("\n💡 [bold green]Recommended Actions:[/bold green]")
        guidance_panel = Panel(
            "\n".join(result.actionable_guidance),
            title="🚀 Quick Fixes",
            border_style="green",
            padding=(1, 2)
        )
        console.print(guidance_panel)


def _display_deployment_status(status_info: Dict[str, Any]):
    """Display deployment status information."""
    status_table = Table(show_header=True, header_style="bold magenta")
    status_table.add_column("Property", style="cyan")
    status_table.add_column("Value", style="yellow")
    
    status_table.add_row("Deployed", "✅ Yes" if status_info['deployed'] else "❌ No")
    status_table.add_row("Working Directory", str(status_info['working_directory']))
    status_table.add_row("Claude PM Directory", str(status_info['claude_pm_directory']))
    
    if status_info.get('metadata'):
        metadata = status_info['metadata']
        status_table.add_row("Deployment ID", metadata.get('deployment_id', 'Unknown'))
        status_table.add_row("Deployed At", metadata.get('deployed_at', 'Unknown'))
        status_table.add_row("Framework Version", metadata.get('framework_version', 'Unknown'))
    
    if status_info.get('validation'):
        validation = status_info['validation']
        status_table.add_row("Validation Status", "✅ Valid" if validation['valid'] else "❌ Invalid")
    
    console.print(status_table)


def _display_deployments_list(deployments: list):
    """Display list of discovered deployments."""
    if not deployments:
        console.print("ℹ️  No framework deployments found.")
        return
    
    console.print(f"📦 Found {len(deployments)} framework deployment(s):")
    console.print()
    
    deployments_table = Table(show_header=True, header_style="bold magenta")
    deployments_table.add_column("Working Directory", style="cyan")
    deployments_table.add_column("Deployment Path", style="yellow")
    deployments_table.add_column("Version", style="green")
    deployments_table.add_column("Deployed At", style="blue")
    
    for deployment in deployments:
        version = "Unknown"
        deployed_at = "Unknown"
        
        if deployment.get('metadata'):
            metadata = deployment['metadata']
            version = metadata.get('framework_version', 'Unknown')
            deployed_at = metadata.get('deployed_at', 'Unknown')
        
        deployments_table.add_row(
            deployment['working_directory'],
            deployment['path'],
            version,
            deployed_at
        )
    
    console.print(deployments_table)


def _display_validation_issues(validation_result):
    """Display validation issues."""
    if validation_result.error_message:
        console.print(f"   Error: {validation_result.error_message}")
    
    if validation_result.actionable_guidance:
        console.print("   Suggested fixes:")
        for guidance in validation_result.actionable_guidance[:3]:  # Show first 3
            console.print(f"   • {guidance}")


def _display_diagnostic_results(status: Dict[str, Any], validation_result):
    """Display diagnostic results."""
    console.print("🎯 [bold]Overall Status:[/bold]")
    
    diag_table = Table(show_header=True, header_style="bold magenta")
    diag_table.add_column("Component", style="cyan")
    diag_table.add_column("Status", style="yellow")
    diag_table.add_column("Details", style="green")
    
    diag_table.add_row(
        "NPM Installation",
        "✅ Valid" if status.get('npm_installation') else "❌ Invalid",
        status.get('claude_pm_directory', 'Not found')
    )
    
    diag_table.add_row(
        "Framework Deployment",
        "✅ Valid" if status.get('framework_deployed') else "❌ Invalid",
        "Ready for operations" if status.get('framework_deployed') else "Needs deployment"
    )
    
    diag_table.add_row(
        "Working Directory",
        "✅ Valid" if status.get('working_directory_configured') else "❌ Invalid",
        "Configured" if status.get('working_directory_configured') else "Run 'claude-pm deploy'"
    )
    
    console.print(diag_table)
    
    if not status.get('valid'):
        console.print("\n⚠️  [yellow]Issues detected. Run 'claude-pm deploy' to fix deployment problems.[/yellow]")


# Register commands
def register_deployment_commands(cli):
    """Register deployment commands with main CLI."""
    cli.add_command(deployment_commands)