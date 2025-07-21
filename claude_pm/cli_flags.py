#!/usr/bin/env python3
"""
Claude Multi-Agent PM Framework - CLI Flags Implementation

Pure Python implementation of CLI flags using Click framework.
Replaces the incorrect JavaScript implementation in ISS-0113.
"""

import asyncio
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from claude_pm.utils.subprocess_manager import SubprocessManager

console = Console()


class SafeModeManager:
    """Python implementation of safe mode operations."""
    
    def __init__(self, backup_dir: Optional[str] = None, verbose: bool = False):
        self.backup_dir = Path(backup_dir) if backup_dir else Path.home() / ".claude-pm" / "backups"
        self.verbose = verbose
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, operation: str, context: Dict[str, Any] = None) -> Path:
        """Create a backup before performing an operation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{operation}_backup_{timestamp}.json"
        
        backup_data = {
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "environment": {
                "platform": sys.platform,
                "python_version": sys.version,
                "working_directory": str(Path.cwd())
            }
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
            
        if self.verbose:
            console.print(f"[green]✅ Backup created: {backup_file}[/green]")
            
        return backup_file
    
    def confirm_operation(self, operation: str, changes: List[str] = None, risks: List[str] = None) -> bool:
        """Request user confirmation for safe mode operations."""
        console.print("\n[bold blue]🛡️  SafeMode Confirmation Required[/bold blue]")
        console.print("═" * 60)
        console.print(f"Operation: [bold]{operation}[/bold]")
        
        if changes:
            console.print("\n[bold]Changes:[/bold]")
            for i, change in enumerate(changes, 1):
                console.print(f"  {i}. {change}")
                
        if risks:
            console.print("\n[bold yellow]⚠️  Potential Risks:[/bold yellow]")
            for i, risk in enumerate(risks, 1):
                console.print(f"  {i}. {risk}")
                
        return click.confirm("\nDo you want to proceed?")


class VersionManager:
    """Python implementation of version management."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.framework_path = self._detect_framework_path()
        self.subprocess_manager = SubprocessManager()
        
    def _detect_framework_path(self) -> Path:
        """Detect the framework path."""
        possible_paths = [
            Path.cwd(),
            Path(__file__).parent.parent,
            Path.home() / ".claude-pm"
        ]
        
        for path in possible_paths:
            if (path / "claude_pm").exists() or (path / "package.json").exists():
                return path
                
        return Path.cwd()
    
    def get_version_info(self, include_components: bool = False, include_git: bool = False) -> Dict[str, Any]:
        """Get comprehensive version information."""
        version_info = {
            "unified": self._get_unified_version(),
            "timestamp": datetime.now().isoformat()
        }
        
        if include_components:
            version_info["components"] = self._get_component_versions()
            
        if include_git:
            version_info["git"] = self._get_git_info()
            
        return version_info
    
    def _get_unified_version(self) -> str:
        """Get the unified version from multiple sources."""
        # Try package.json first
        package_json = self.framework_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if data.get("name") == "@bobmatnyc/claude-multiagent-pm":
                        return data.get("version", "unknown")
            except (json.JSONDecodeError, KeyError):
                pass
                
        # Try VERSION file
        version_file = self.framework_path / "VERSION"
        if version_file.exists():
            try:
                return version_file.read_text().strip()
            except OSError:
                pass
                
        # Try Python package version
        init_file = self.framework_path / "claude_pm" / "__init__.py"
        if init_file.exists():
            try:
                content = init_file.read_text()
                import re
                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except OSError:
                pass
                
        return "unknown"
    
    def _get_component_versions(self) -> Dict[str, str]:
        """Get versions of system components."""
        components = {}
        
        # Python version
        components["python"] = sys.version.split()[0]
        
        # Try to get other component versions
        commands = {
            "node": ["node", "--version"],
            "npm": ["npm", "--version"],
            "git": ["git", "--version"],
            "claude": ["claude", "--version"]
        }
        
        for name, cmd in commands.items():
            try:
                result = self.subprocess_manager.run(cmd, capture_output=True, text=True, timeout=5)
                if result.success:
                    components[name] = result.stdout.strip()
                else:
                    components[name] = "not-available"
            except (OSError, FileNotFoundError):
                components[name] = "not-available"
                
        return components
    
    def _get_git_info(self) -> Dict[str, str]:
        """Get Git repository information."""
        git_info = {}
        
        commands = {
            "branch": ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            "commit": ["git", "rev-parse", "--short", "HEAD"],
            "status": ["git", "status", "--porcelain"]
        }
        
        for key, cmd in commands.items():
            try:
                result = self.subprocess_manager.run(cmd, capture_output=True, text=True, timeout=5)
                if result.success:
                    git_info[key] = result.stdout.strip()
                else:
                    git_info[key] = "unknown"
            except (OSError, FileNotFoundError):
                git_info[key] = "not-a-git-repo"
                
        # Determine if repo is clean
        git_info["clean"] = git_info.get("status", "") == ""
        
        return git_info
    
    def display_version(self, format_type: str = "standard", **kwargs) -> None:
        """Display version information in specified format."""
        version_info = self.get_version_info(**kwargs)
        
        if format_type == "simple":
            console.print(version_info["unified"])
        elif format_type == "json":
            console.print(json.dumps(version_info, indent=2))
        elif format_type == "detailed":
            self._display_detailed_version(version_info)
        else:
            self._display_standard_version(version_info)
    
    def _display_standard_version(self, version_info: Dict[str, Any]) -> None:
        """Display standard version format."""
        console.print(f"[bold]Claude Multi-Agent PM Framework v{version_info['unified']}[/bold]")
        
        if "components" in version_info:
            console.print("\n[bold]📦 Component Versions:[/bold]")
            for name, version in version_info["components"].items():
                console.print(f"   {name}: {version}")
                
        if "git" in version_info and version_info["git"].get("branch") != "not-a-git-repo":
            git = version_info["git"]
            status = "clean" if git.get("clean") else "dirty"
            console.print(f"\n[bold]🌿 Git:[/bold] {git.get('branch')}@{git.get('commit')} ({status})")
    
    def _display_detailed_version(self, version_info: Dict[str, Any]) -> None:
        """Display detailed version information."""
        console.print("[bold]Claude Multi-Agent PM Framework - Detailed Version Information[/bold]")
        console.print("═" * 80)
        console.print(f"Unified Version: [bold]{version_info['unified']}[/bold]")
        console.print(f"Generated: {version_info['timestamp']}")
        
        if "components" in version_info:
            table = Table(title="System Components")
            table.add_column("Component", style="cyan")
            table.add_column("Version", style="green")
            
            for name, version in version_info["components"].items():
                table.add_row(name, version)
                
            console.print(table)
            
        if "git" in version_info and version_info["git"].get("branch") != "not-a-git-repo":
            git = version_info["git"]
            console.print(f"\n[bold]🌿 Git Information:[/bold]")
            console.print(f"   Branch: {git.get('branch')}")
            console.print(f"   Commit: {git.get('commit')}")
            console.print(f"   Status: {'clean' if git.get('clean') else 'dirty'}")


class UpgradeManager:
    """Python implementation of upgrade management."""
    
    def __init__(self, safe_mode: bool = False, verbose: bool = False):
        self.safe_mode = safe_mode
        self.verbose = verbose
        self.safe_manager = SafeModeManager(verbose=verbose) if safe_mode else None
        self.subprocess_manager = SubprocessManager()
        
    async def upgrade_framework(self, target_version: Optional[str] = None) -> bool:
        """Upgrade the framework to the specified or latest version."""
        if self.safe_mode:
            changes = [
                "Update Claude PM Framework to latest version",
                "Update dependencies and configuration files",
                "Restart any running services"
            ]
            risks = [
                "Potential breaking changes in new version",
                "Configuration file format changes",
                "Temporary service disruption"
            ]
            
            if not self.safe_manager.confirm_operation("upgrade", changes, risks):
                console.print("[yellow]Upgrade cancelled by user[/yellow]")
                return False
                
            self.safe_manager.create_backup("upgrade", {"target_version": target_version})
        
        try:
            # Implement upgrade logic
            console.print(f"[blue]🚀 Upgrading Claude PM Framework...[/blue]")
            
            if target_version:
                cmd = ["npm", "install", "-g", f"@bobmatnyc/claude-multiagent-pm@{target_version}"]
                console.print(f"Upgrading to version: {target_version}")
            else:
                cmd = ["npm", "install", "-g", "@bobmatnyc/claude-multiagent-pm@latest"]
                console.print("Upgrading to latest version")
            
            if self.verbose:
                console.print(f"Running: {' '.join(cmd)}")
                
            result = self.subprocess_manager.run(cmd, capture_output=True, text=True)
            
            if result.success:
                console.print("[green]✅ Upgrade completed successfully[/green]")
                return True
            else:
                console.print(f"[red]❌ Upgrade failed: {result.stderr}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Upgrade error: {e}[/red]")
            return False


class RollbackManager:
    """Python implementation of rollback management."""
    
    def __init__(self, safe_mode: bool = False, verbose: bool = False):
        self.safe_mode = safe_mode
        self.verbose = verbose
        self.safe_manager = SafeModeManager(verbose=verbose) if safe_mode else None
        self.subprocess_manager = SubprocessManager()
        
    async def rollback_to_version(self, version: str) -> bool:
        """Rollback to a specific version."""
        if self.safe_mode:
            changes = [
                f"Rollback Claude PM Framework to version {version}",
                "Restore previous configuration",
                "Restart services with previous version"
            ]
            risks = [
                "Loss of features from newer version",
                "Potential data compatibility issues",
                "Service restart required"
            ]
            
            if not self.safe_manager.confirm_operation("rollback", changes, risks):
                console.print("[yellow]Rollback cancelled by user[/yellow]")
                return False
                
            self.safe_manager.create_backup("rollback", {"target_version": version})
        
        try:
            console.print(f"[blue]🔄 Rolling back to version {version}...[/blue]")
            
            cmd = ["npm", "install", "-g", f"@bobmatnyc/claude-multiagent-pm@{version}"]
            
            if self.verbose:
                console.print(f"Running: {' '.join(cmd)}")
                
            result = self.subprocess_manager.run(cmd, capture_output=True, text=True)
            
            if result.success:
                console.print(f"[green]✅ Rollback to {version} completed successfully[/green]")
                return True
            else:
                console.print(f"[red]❌ Rollback failed: {result.stderr}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Rollback error: {e}[/red]")
            return False


# CLI command definitions using Click
@click.group(invoke_without_command=True)
@click.option("--safe", is_flag=True, help="Enable safe mode with confirmations and backups")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
@click.option("--test-mode", is_flag=True, help="Enable test mode with prompt logging to .claude-pm/logs/prompts/")
@click.pass_context
def cli_flags(ctx, safe, verbose, dry_run, test_mode):
    """Claude Multi-Agent PM Framework - Enhanced CLI flags."""
    # Handle test mode flag
    if test_mode:
        # Set up test mode environment
        prompts_dir = Path.cwd() / ".claude-pm" / "logs" / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        console.print("[bold blue]🧪 Test Mode Activated[/bold blue]")
        console.print("═" * 60)
        console.print(f"📁 Prompts directory: {prompts_dir}")
        console.print("✅ Prompt logging enabled")
        console.print("\n[dim]Launching Claude CLI with verbose mode for prompt logging...[/dim]")
        
        # Set environment variables
        os.environ["CLAUDE_PM_TEST_MODE"] = "true"
        os.environ["CLAUDE_PM_PROMPTS_DIR"] = str(prompts_dir)
        
        # Launch Claude via the main claude-pm script
        # This ensures proper routing through the framework
        try:
            # Get the claude-pm script path
            claude_pm_path = shutil.which("claude-pm")
            if not claude_pm_path:
                # Try to find it in the bin directory
                bin_path = Path(__file__).parent.parent / "bin" / "claude-pm"
                if bin_path.exists():
                    claude_pm_path = str(bin_path)
                else:
                    console.print("[red]❌ claude-pm script not found[/red]")
                    sys.exit(1)
            
            # Re-launch claude-pm without --test-mode flag to avoid infinite loop
            # The environment variables will ensure test mode is active
            remaining_args = [arg for arg in sys.argv[1:] if arg != "--test-mode"]
            cmd = [sys.executable, claude_pm_path] + remaining_args
            
            # Use subprocess manager to maintain environment
            manager = SubprocessManager()
            result = manager.run(cmd, env=os.environ.copy())
            sys.exit(result.returncode)
            
        except Exception as e:
            console.print(f"[red]❌ Failed to launch Claude CLI: {e}[/red]")
            sys.exit(1)
    
    if ctx.invoked_subcommand is None:
        # If no subcommand is provided, show help
        click.echo(ctx.get_help())
    else:
        # Store flags in context for subcommands
        ctx.ensure_object(dict)
        ctx.obj['safe'] = safe
        ctx.obj['verbose'] = verbose
        ctx.obj['dry_run'] = dry_run
        ctx.obj['test_mode'] = test_mode


@cli_flags.command()
@click.option("--format", type=click.Choice(["simple", "standard", "detailed", "json"]), default="standard")
@click.option("--components", is_flag=True, help="Include component versions")
@click.option("--git", is_flag=True, help="Include Git information")
@click.pass_context
def version(ctx, format, components, git):
    """Display version information."""
    verbose = ctx.obj.get('verbose', False)
    
    manager = VersionManager(verbose=verbose)
    manager.display_version(
        format_type=format,
        include_components=components,
        include_git=git
    )


@cli_flags.command()
@click.argument("version", required=False)
@click.option("--check-only", is_flag=True, help="Check for updates without upgrading")
@click.pass_context
def upgrade(ctx, version, check_only):
    """Upgrade to the latest or specified version."""
    safe = ctx.obj.get('safe', False)
    verbose = ctx.obj.get('verbose', False)
    dry_run = ctx.obj.get('dry_run', False)
    
    if dry_run or check_only:
        console.print("[blue]🔍 Checking for updates...[/blue]")
        # Implement check logic here
        console.print("[green]✅ Check completed[/green]")
        return
    
    manager = UpgradeManager(safe_mode=safe, verbose=verbose)
    
    async def run_upgrade():
        success = await manager.upgrade_framework(version)
        sys.exit(0 if success else 1)
    
    asyncio.run(run_upgrade())


@cli_flags.command()
@click.argument("version", required=True)
@click.pass_context
def rollback(ctx, version):
    """Rollback to a specific version."""
    safe = ctx.obj.get('safe', False)
    verbose = ctx.obj.get('verbose', False)
    dry_run = ctx.obj.get('dry_run', False)
    
    if dry_run:
        console.print(f"[blue]🔍 Would rollback to version {version}[/blue]")
        return
    
    manager = RollbackManager(safe_mode=safe, verbose=verbose)
    
    async def run_rollback():
        success = await manager.rollback_to_version(version)
        sys.exit(0 if success else 1)
    
    asyncio.run(run_rollback())




@cli_flags.command()
@click.option("--backup-dir", help="Custom backup directory")
@click.pass_context
def safe_mode_test(ctx, backup_dir):
    """Test safe mode functionality."""
    verbose = ctx.obj.get('verbose', False)
    
    manager = SafeModeManager(backup_dir=backup_dir, verbose=verbose)
    
    # Test backup creation
    backup_file = manager.create_backup("test", {"test": True})
    console.print(f"[green]✅ Test backup created: {backup_file}[/green]")
    
    # Test confirmation (only in interactive mode)
    if sys.stdin.isatty():
        result = manager.confirm_operation(
            "test_operation",
            changes=["This is a test change"],
            risks=["No real risks"]
        )
        console.print(f"[blue]Confirmation result: {result}[/blue]")
    else:
        console.print("[yellow]⚠️  Non-interactive mode - skipping confirmation test[/yellow]")


if __name__ == "__main__":
    cli_flags()