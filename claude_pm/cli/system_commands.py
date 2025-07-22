#!/usr/bin/env python3
"""
System Commands Module - Claude Multi-Agent PM Framework

Handles agents, testing, utilities, and system diagnostics.
Extracted from main CLI as part of ISS-0114 modularization initiative.
"""

import asyncio
import sys
import subprocess
import shutil
import platform
import os
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.config import Config

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
    return Path(config.get("managed_projects_path"))


def register_system_commands(cli_group):
    """Register all system commands with the main CLI group."""
    
    # Agents Commands
    @cli_group.group()
    def agents():
        """Multi-agent coordination and management."""
        pass

    @agents.command()
    def status():
        """Show agent status and availability."""
        console.print("[bold blue]🤖 Multi-Agent Status[/bold blue]\n")

        # Agent types from the framework
        agent_types = {
            "orchestrator": {
                "status": "available",
                "current_task": None,
                "specialization": "Task coordination",
            },
            "architect": {
                "status": "available",
                "current_task": None,
                "specialization": "System design",
            },
            "engineer": {
                "status": "busy",
                "current_task": "M01-008 Implementation",
                "specialization": "Code implementation",
            },
            "qa": {"status": "available", "current_task": None, "specialization": "Quality assurance"},
            "researcher": {
                "status": "available",
                "current_task": None,
                "specialization": "Information gathering",
            },
            "security": {
                "status": "available",
                "current_task": None,
                "specialization": "Security analysis",
            },
            "performance": {
                "status": "idle",
                "current_task": None,
                "specialization": "Performance optimization",
            },
            "devops": {"status": "available", "current_task": None, "specialization": "Infrastructure"},
            "data": {"status": "available", "current_task": None, "specialization": "Data engineering"},
            "ui_ux": {"status": "available", "current_task": None, "specialization": "User experience"},
            "code_review": {
                "status": "available",
                "current_task": None,
                "specialization": "Code review",
            },
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
                "offline": "[red]🔴 Offline[/red]",
            }.get(agent_data["status"], agent_data["status"])

            current_task = agent_data["current_task"] or "None"

            table.add_row(
                agent_name.replace("_", " ").title(),
                status_display,
                current_task,
                agent_data["specialization"],
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

    # Testing Commands
    @cli_group.command()
    @click.option("--unit", is_flag=True, help="Run unit tests only")
    @click.option("--integration", is_flag=True, help="Run integration tests only")
    @click.option("--coverage", is_flag=True, help="Generate coverage report")
    @click.option("--watch", is_flag=True, help="Watch for changes and re-run tests")
    @click.option("--pattern", help="Run tests matching pattern")
    @click.option("--quiet", "-q", is_flag=True, help="Quiet output")
    @click.option("--failfast", is_flag=True, help="Stop on first failure")
    @click.option("--html", is_flag=True, help="Generate HTML coverage report")
    @click.option("--xml", is_flag=True, help="Generate XML coverage report")
    @click.option("--json", is_flag=True, help="Output results in JSON format")
    @click.option("--parallel", is_flag=True, help="Run tests in parallel")
    @click.option("--workers", type=int, default=4, help="Number of parallel workers")
    @click.argument("pytest_args", nargs=-1, type=click.UNPROCESSED)
    @click.pass_context
    def test(
        ctx,
        unit,
        integration,
        coverage,
        watch,
        pattern,
        quiet,
        failfast,
        html,
        xml,
        json,
        parallel,
        workers,
        pytest_args,
    ):
        """
        🧪 Run tests with pytest integration.

        This command provides a unified interface for running tests with pytest,
        supporting all major testing scenarios and options.

        Examples:
            claude-pm test                      # Run all tests
            claude-pm test --unit               # Run unit tests only
            claude-pm test --integration        # Run integration tests only
            claude-pm test --coverage           # Run with coverage
            claude-pm test --watch              # Watch mode
            claude-pm test --pattern "test_cli" # Run tests matching pattern
            claude-pm test --verbose            # Verbose output
            claude-pm test --parallel           # Run in parallel

        Advanced usage:
            claude-pm test -- --pdb             # Pass args to pytest
            claude-pm test -- -k "test_health"  # Use pytest's -k selector
        """
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add test markers
        if unit:
            cmd.extend(["-m", "unit"])
        elif integration:
            cmd.extend(["-m", "integration"])

        # Add coverage options
        if coverage:
            cmd.extend(["--cov=claude_pm", "--cov-report=term-missing"])
            if html:
                cmd.extend(["--cov-report=html"])
            if xml:
                cmd.extend(["--cov-report=xml"])

        # Add output options (get verbose from parent context)
        verbose = ctx.obj.get("verbose", False) if ctx.obj else False
        if verbose:
            cmd.append("--verbose")
        elif quiet:
            cmd.append("--quiet")

        # Add behavior options
        if failfast:
            cmd.append("--maxfail=1")

        # Add pattern matching
        if pattern:
            cmd.extend(["-k", pattern])

        # Add parallel execution
        if parallel:
            try:
                import pytest_xdist
                cmd.extend(["-n", str(workers)])
            except ImportError:
                console.print(
                    "[yellow]⚠️ pytest-xdist not installed. Run: pip install pytest-xdist[/yellow]"
                )

        # Add watch mode
        if watch:
            try:
                import pytest_watch
                # Replace pytest with ptw for watch mode
                cmd[1] = "ptw"
                cmd.append("--")  # Separator for ptw
            except ImportError:
                console.print(
                    "[yellow]⚠️ pytest-watch not installed. Run: pip install pytest-watch[/yellow]"
                )

        # Add JSON output
        if json:
            cmd.extend(["--json-report", "--json-report-file=test-results.json"])

        # Add any additional pytest arguments
        if pytest_args:
            cmd.extend(pytest_args)

        # Display command being run
        console.print(f"[bold blue]🧪 Running tests...[/bold blue]")
        if verbose:
            console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")

        try:
            # Set PYTHONPATH to include current directory
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path.cwd())

            # Run the tests
            result = subprocess.run(cmd, env=env)
            
            if result.returncode == 0:
                console.print("[bold green]✅ All tests passed![/bold green]")
            else:
                console.print(f"[bold red]❌ Tests failed with exit code {result.returncode}[/bold red]")
                sys.exit(result.returncode)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]⚠️ Tests interrupted by user[/bold yellow]")
            sys.exit(130)
        except Exception as e:
            console.print(f"[red]❌ Error running tests: {e}[/red]")
            sys.exit(1)

    # Utility Commands
    @cli_group.group()
    def util():
        """Utility commands and tools."""
        pass

    @util.command()
    def info():
        """Show Claude PM Framework information."""
        from .. import __version__

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
npm test → claude-pm test
npm run lint → make lint

[bold yellow]New Python-specific commands:[/bold yellow]
make setup-dev → Complete development setup
make install-ai → Install AI dependencies
make type-check → Run type checking
claude-pm service start → Start all services
claude-pm project list → List all projects
claude-pm memory search → Search project memories
claude-pm test → Run tests with pytest integration

[bold yellow]Development workflow:[/bold yellow]
1. source .venv/bin/activate (activate virtual environment)
2. make install-dev (install dependencies)
3. claude-pm service start (start services)
4. claude-pm health check (verify health)
5. claude-pm test (run tests)

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

        console.print("[bold blue]🏥 Claude Multi-Agent PM Framework Doctor[/bold blue]\n")

        checks = []

        # Python version check
        python_version = sys.version.split()[0]
        python_ok = tuple(map(int, python_version.split("."))) >= (3, 9)
        checks.append(("Python >= 3.9", python_ok, f"Found: {python_version}"))

        # Virtual environment check
        venv_active = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )
        checks.append(("Virtual Environment", venv_active, "Activate with: source .venv/bin/activate"))

        # Required tools check
        required_tools = ["git", "make"]
        for tool in required_tools:
            tool_available = shutil.which(tool) is not None
            checks.append((f"{tool} available", tool_available, f"Install {tool}"))

        # Directory structure check
        base_path = Path.home() / "Projects"
        claude_pm_path = base_path / "claude-pm"
        managed_path = base_path / "managed"

        checks.append(("Base directory", base_path.exists(), f"Create {base_path}"))
        checks.append(
            ("Claude Multi-Agent PM directory", claude_pm_path.exists(), f"Create {claude_pm_path}")
        )
        checks.append(("Managed directory", managed_path.exists(), f"Create {managed_path}"))


        # Framework dependencies check
        try:
            import click
            import rich
            deps_available = True
        except ImportError:
            deps_available = False
        checks.append(("Core dependencies", deps_available, "pip install -r requirements/base.txt"))

        # pytest check for testing
        try:
            import pytest
            pytest_available = True
        except ImportError:
            pytest_available = False
        checks.append(("Testing framework", pytest_available, "pip install pytest"))

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
            console.print(
                "\n[bold green]✅ All checks passed! Claude Multi-Agent PM Framework is ready.[/bold green]"
            )
        else:
            console.print(
                "\n[bold red]❌ Some checks failed. Please address the issues above.[/bold red]"
            )

        # Additional recommendations
        recommendations = []
        
        if not venv_active:
            recommendations.append("Activate virtual environment before running commands")
        
        
        if not pytest_available:
            recommendations.append("Install pytest for testing capabilities")

        if recommendations:
            console.print("\n[bold blue]💡 Recommendations:[/bold blue]")
            for rec in recommendations:
                console.print(f"  • {rec}")

    @util.command()
    def version():
        """Show detailed version information."""
        from .. import __version__
        
        console.print(f"[bold]Claude Multi-Agent PM Framework[/bold] v{__version__}")
        console.print(f"Python {sys.version}")
        console.print(f"Platform: {platform.platform()}")
        
        # Check for key dependencies
        deps_info = []
        
        try:
            import click
            deps_info.append(f"click: {click.__version__}")
        except ImportError:
            deps_info.append("click: not installed")
        
        try:
            import rich
            deps_info.append(f"rich: {rich.__version__}")
        except ImportError:
            deps_info.append("rich: not installed")
        
        try:
            import pytest
            deps_info.append(f"pytest: {pytest.__version__}")
        except ImportError:
            deps_info.append("pytest: not installed")
        
        if deps_info:
            console.print("\n[bold]Dependencies:[/bold]")
            for dep in deps_info:
                console.print(f"  {dep}")

    @util.group()
    def versions():
        """Service version management commands."""
        pass

    @versions.command()
    def scan():
        """Scan and display all subsystem and service versions."""
        from ..utils.subsystem_versions import SubsystemVersionManager
        
        async def _scan_versions():
            manager = SubsystemVersionManager()
            await manager.scan_subsystem_versions()
            
            report = manager.get_summary_report()
            
            console.print("[bold blue]📋 Service Version Report[/bold blue]\n")
            
            # Summary table
            summary = report.get("summary", {})
            console.print(f"[bold]Total Services:[/bold] {summary.get('total_subsystems', 0)}")
            console.print(f"[bold]Found:[/bold] {summary.get('found', 0)}")
            console.print(f"[bold]Missing:[/bold] {summary.get('missing', 0)}")
            console.print(f"[bold]Errors:[/bold] {summary.get('errors', 0)}")
            console.print(f"[bold]Coverage:[/bold] {summary.get('coverage_percentage', 0):.1f}%\n")
            
            # Services table
            table = Table(title="Service Versions")
            table.add_column("Service", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Path", style="dim")
            
            for name, info in report.get("subsystems", {}).items():
                status_icon = {
                    "found": "🟢",
                    "missing": "🔴",
                    "error": "🟠"
                }.get(info.get("status"), "❓")
                
                table.add_row(
                    name,
                    info.get("version", "unknown"),
                    f"{status_icon} {info.get('status', 'unknown')}",
                    str(Path(info.get("file_path", "")).name)
                )
            
            console.print(table)
        
        asyncio.run(_scan_versions())

    @versions.command()
    @click.argument("service")
    @click.argument("version")
    @click.option("--no-backup", is_flag=True, help="Skip creating backup")
    def update(service, version, no_backup):
        """Update a specific service version."""
        from ..utils.subsystem_versions import SubsystemVersionManager
        
        async def _update_version():
            manager = SubsystemVersionManager()
            
            # Check if service exists
            available = manager.get_all_available_subsystems()
            if service not in available:
                console.print(f"[red]❌ Unknown service: {service}[/red]")
                console.print(f"[yellow]Available services:[/yellow] {', '.join(available)}")
                return
            
            success = await manager.update_version(service, version, backup=not no_backup)
            
            if success:
                console.print(f"[green]✅ Updated {service} to version {version}[/green]")
            else:
                console.print(f"[red]❌ Failed to update {service}[/red]")
        
        asyncio.run(_update_version())

    @versions.command()
    @click.argument("updates", nargs=-1)
    @click.option("--no-backup", is_flag=True, help="Skip creating backups")
    def bulk_update(updates, no_backup):
        """Update multiple service versions. Format: service1:version1 service2:version2"""
        from ..utils.subsystem_versions import SubsystemVersionManager
        
        if not updates:
            console.print("[red]❌ No updates specified[/red]")
            console.print("[yellow]Usage:[/yellow] claude-pm util versions bulk-update service1:version1 service2:version2")
            return
        
        async def _bulk_update():
            manager = SubsystemVersionManager()
            
            # Parse updates
            update_dict = {}
            for update in updates:
                if ":" not in update:
                    console.print(f"[red]❌ Invalid format: {update}[/red]")
                    console.print("[yellow]Expected format:[/yellow] service:version")
                    return
                
                service, version = update.split(":", 1)
                update_dict[service] = version
            
            # Validate services
            available = manager.get_all_available_subsystems()
            for service in update_dict:
                if service not in available:
                    console.print(f"[red]❌ Unknown service: {service}[/red]")
                    console.print(f"[yellow]Available services:[/yellow] {', '.join(available)}")
                    return
            
            console.print(f"[blue]📦 Updating {len(update_dict)} services...[/blue]")
            
            results = await manager.bulk_update(update_dict, backup=not no_backup)
            
            # Display results
            table = Table(title="Bulk Update Results")
            table.add_column("Service", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Status", style="yellow")
            
            for service, version in update_dict.items():
                success = results.get(service, False)
                status = "✅ Success" if success else "❌ Failed"
                table.add_row(service, version, status)
            
            console.print(table)
            
            success_count = sum(1 for success in results.values() if success)
            console.print(f"[bold]Updated {success_count}/{len(update_dict)} services[/bold]")
        
        asyncio.run(_bulk_update())

    @versions.command()
    @click.argument("requirements", nargs=-1)
    def validate(requirements):
        """Validate service versions against requirements. Format: service1:version1 service2:version2"""
        from ..utils.subsystem_versions import SubsystemVersionManager
        
        if not requirements:
            console.print("[red]❌ No requirements specified[/red]")
            console.print("[yellow]Usage:[/yellow] claude-pm util versions validate service1:version1 service2:version2")
            return
        
        async def _validate():
            manager = SubsystemVersionManager()
            
            # Parse requirements
            req_dict = {}
            for req in requirements:
                if ":" not in req:
                    console.print(f"[red]❌ Invalid format: {req}[/red]")
                    console.print("[yellow]Expected format:[/yellow] service:version")
                    return
                
                service, version = req.split(":", 1)
                req_dict[service] = version
            
            console.print(f"[blue]🔍 Validating {len(req_dict)} requirements...[/blue]")
            
            checks = await manager.validate_compatibility(req_dict)
            
            # Display results
            table = Table(title="Compatibility Validation")
            table.add_column("Service", style="cyan")
            table.add_column("Required", style="yellow")
            table.add_column("Current", style="green")
            table.add_column("Status", style="magenta")
            table.add_column("Message", style="dim")
            
            all_compatible = True
            for check in checks:
                status_icon = "✅" if check.compatible else "❌"
                if not check.compatible:
                    all_compatible = False
                
                table.add_row(
                    check.subsystem,
                    check.required_version,
                    check.current_version or "missing",
                    f"{status_icon} {check.status.value}",
                    check.message or ""
                )
            
            console.print(table)
            
            if all_compatible:
                console.print("[bold green]✅ All requirements satisfied[/bold green]")
            else:
                console.print("[bold red]❌ Some requirements not satisfied[/bold red]")
        
        asyncio.run(_validate())

    @util.command()
    @click.option("--config", is_flag=True, help="Show configuration paths")
    @click.option("--services", is_flag=True, help="Show service status")
    @click.option("--environment", is_flag=True, help="Show environment variables")
    def debug(config, services, environment):
        """Show debug information for troubleshooting."""
        console.print("[bold blue]🔍 Debug Information[/bold blue]\n")
        
        if config or not any([config, services, environment]):
            # Configuration paths
            console.print("[bold]Configuration Paths:[/bold]")
            console.print(f"  Framework Config: {get_framework_config()}")
            console.print(f"  Claude PM Path: {get_claude_pm_path()}")
            console.print(f"  Managed Path: {get_managed_path()}")
            console.print("")
        
        if services or not any([config, services, environment]):
            # Service status (basic check)
            console.print("[bold]Service Status:[/bold]")
            
            console.print("")
        
        if environment or not any([config, services, environment]):
            # Environment variables
            console.print("[bold]Environment:[/bold]")
            console.print(f"  PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}")
            console.print(f"  VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'not set')}")
            console.print(f"  PATH: {os.environ.get('PATH', 'not set')[:100]}...")
            console.print("")

    # Model Management Commands
    @cli_group.command()
    @click.option("--show-details", is_flag=True, help="Show detailed model information")
    @click.option("--aliases", is_flag=True, help="Show model aliases and mappings")
    @click.pass_context
    def models(ctx, show_details, aliases):
        """Show available AI models and their configurations."""
        from ..services.model_selector import ModelSelector, ModelType
        from . import get_available_models, format_model_help
        
        console.print("[bold blue]🤖 Available AI Models[/bold blue]\n")
        
        if aliases:
            # Show alias mappings
            available_models = get_available_models()
            
            table = Table(title="Model Aliases")
            table.add_column("Alias", style="cyan")
            table.add_column("Model ID", style="green")
            table.add_column("Type", style="yellow")
            
            for alias, model_id in available_models.items():
                model_type = "Claude 4" if ("claude-4" in model_id or "claude-sonnet-4" in model_id) else "Claude 3"
                table.add_row(alias, model_id, model_type)
            
            console.print(table)
            console.print()
        
        # Get verbose from parent context or use show_details flag
        verbose = ctx.obj.get("verbose", False) if ctx.obj else False
        
        if show_details:
            # Show detailed model information
            selector = ModelSelector()
            
            table = Table(title="Model Configurations")
            table.add_column("Model", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Max Tokens", style="yellow")
            table.add_column("Context Window", style="blue")
            table.add_column("Cost Tier", style="magenta")
            table.add_column("Speed Tier", style="red")
            table.add_column("Reasoning", style="bright_green")
            
            for model_type in ModelType:
                config = selector.model_configurations[model_type]
                table.add_row(
                    model_type.value,
                    model_type.name,
                    str(config.max_tokens),
                    str(config.context_window),
                    config.cost_tier,
                    config.speed_tier,
                    config.reasoning_tier
                )
            
            console.print(table)
            console.print()
            
            # Show agent mappings
            agent_mapping = selector.get_agent_model_mapping()
            
            table = Table(title="Agent Model Assignments")
            table.add_column("Agent Type", style="cyan")
            table.add_column("Assigned Model", style="green")
            
            # Group by model for better visualization
            model_groups = {}
            for agent_type, model_id in agent_mapping.items():
                if model_id not in model_groups:
                    model_groups[model_id] = []
                model_groups[model_id].append(agent_type)
            
            for model_id, agent_types in model_groups.items():
                for i, agent_type in enumerate(agent_types):
                    display_model = model_id if i == 0 else ""
                    table.add_row(agent_type, display_model)
                if len(agent_types) > 1:
                    table.add_row("", "")  # Add separator
            
            console.print(table)
            console.print()
        
        # Show current override if set
        from .cli_utils import get_model_override
        current_override = get_model_override(ctx)
        if current_override:
            console.print(f"[bold yellow]Current Override:[/bold yellow] {current_override}")
            console.print()
        
        # Show usage examples
        console.print("[bold]Usage Examples:[/bold]")
        console.print("  claude-pm --model sonnet status     # Use Sonnet 4 for status command")
        console.print("  claude-pm --model opus test         # Use Opus 4 for test command")
        console.print("  claude-pm models --show-details     # Show detailed model info")
        console.print("  claude-pm models --aliases          # Show model aliases")
        console.print()
        
        console.print("[bold]Environment Override Examples:[/bold]")
        console.print("  export CLAUDE_PM_MODEL_OVERRIDE=claude-4-opus")
        console.print("  export CLAUDE_PM_MODEL_ENGINEER=claude-sonnet-4-20250514")
    
    # Memory Commands
    @cli_group.group()
    def memory():
        """Memory diagnostics and management commands."""
        pass
    
    @memory.command()
    @click.option('--json', is_flag=True, help='Output in JSON format')
    def profile():
        """Show current memory profile and diagnostics."""
        from ..services.health_monitor import HealthMonitor
        
        async def _show_profile():
            monitor = HealthMonitor()
            try:
                await monitor.start()
                profile_data = await monitor.get_memory_profile()
                
                if click.get_current_context().params.get('json'):
                    import json
                    console.print(json.dumps(profile_data, indent=2))
                else:
                    # Format output nicely
                    console.print("[bold blue]💾 Memory Profile[/bold blue]\n")
                    
                    # Process memory
                    process_info = profile_data.get("process", {})
                    memory_mb = process_info.get("memory_mb", 0)
                    threshold_mb = process_info.get("threshold_mb", 500)
                    
                    memory_color = "red" if memory_mb > threshold_mb else "green"
                    console.print(f"[bold]Process Memory:[/bold] [{memory_color}]{memory_mb:.1f}MB[/{memory_color}] / {threshold_mb}MB")
                    
                    # System memory
                    system_info = profile_data.get("system", {})
                    if system_info:
                        console.print(f"[bold]System Memory:[/bold] {system_info.get('percent', 0):.1f}% used")
                    
                    # Cache info
                    cache_info = profile_data.get("cache", {})
                    if cache_info and "error" not in cache_info:
                        console.print(f"\n[bold]Cache Statistics:[/bold]")
                        console.print(f"  Size: {cache_info.get('size_mb', 0):.2f}MB")
                        console.print(f"  Entries: {cache_info.get('entry_count', 0)}")
                        console.print(f"  Hit Rate: {cache_info.get('hit_rate', 0):.1f}%")
                        console.print(f"  Memory Usage: {cache_info.get('memory_usage_percent', 0):.1f}%")
                    
                    # Memory pressure
                    if profile_data.get("memory_pressure"):
                        console.print("\n[bold red]⚠️  Memory Pressure Detected![/bold red]")
                        console.print("Consider running 'claude-pm memory cleanup' to free resources")
                    
            finally:
                await monitor.stop()
        
        asyncio.run(_show_profile())
    
    @memory.command()
    @click.option('--force', is_flag=True, help='Force cleanup even if cooldown period not elapsed')
    @click.option('--json', is_flag=True, help='Output cleanup results in JSON format')
    def cleanup():
        """Perform emergency memory cleanup to free resources."""
        from ..services.health_monitor import HealthMonitor
        
        async def _perform_cleanup():
            monitor = HealthMonitor()
            try:
                await monitor.start()
                
                console.print("[bold yellow]🧹 Performing memory cleanup...[/bold yellow]\n")
                
                # Perform cleanup
                results = await monitor.perform_memory_cleanup(
                    force=click.get_current_context().params.get('force', False)
                )
                
                if click.get_current_context().params.get('json'):
                    import json
                    console.print(json.dumps(results, indent=2))
                else:
                    if results.get("success"):
                        console.print("[bold green]✅ Cleanup completed successfully![/bold green]\n")
                        
                        # Show freed memory
                        freed_mb = results.get("freed_mb", 0)
                        if freed_mb > 0:
                            console.print(f"[bold]Memory Freed:[/bold] {freed_mb:.2f}MB")
                        
                        # Show actions taken
                        actions = results.get("actions", [])
                        if actions:
                            console.print("\n[bold]Actions Performed:[/bold]")
                            for action in actions:
                                action_name = action.get("action", "unknown")
                                if "error" in action:
                                    console.print(f"  ❌ {action_name}: {action['error']}")
                                elif action_name == "clear_cache":
                                    console.print(f"  ✅ Cleared cache: {action.get('entries_cleared', 0)} entries, {action.get('freed_mb', 0):.2f}MB freed")
                                elif action_name == "garbage_collection":
                                    console.print(f"  ✅ Garbage collection: {action.get('objects_collected', 0)} objects collected")
                                elif action_name == "terminate_zombies":
                                    console.print(f"  ✅ Terminated {action.get('processes_terminated', 0)} zombie processes")
                                else:
                                    console.print(f"  ✅ {action_name}")
                        
                        # Show final state
                        console.print(f"\n[bold]Final Memory:[/bold] {results.get('after', {}).get('process_mb', 0):.1f}MB")
                    else:
                        reason = results.get("reason", "Unknown error")
                        console.print(f"[bold red]❌ Cleanup failed:[/bold red] {reason}")
                        
                        if "cooldown" in reason:
                            console.print("\n[dim]Use --force flag to override cooldown period[/dim]")
                
            finally:
                await monitor.stop()
        
        asyncio.run(_perform_cleanup())
    
    @memory.command()
    def diagnostics():
        """Show comprehensive memory diagnostics report."""
        from ..services.health_monitor import HealthMonitor
        
        async def _show_diagnostics():
            monitor = HealthMonitor()
            try:
                await monitor.start()
                diagnostics_data = await monitor.get_memory_diagnostics()
                
                console.print("[bold blue]🔍 Memory Diagnostics Report[/bold blue]\n")
                
                # Thresholds
                thresholds = diagnostics_data.get("thresholds", {})
                console.print("[bold]Configuration Thresholds:[/bold]")
                console.print(f"  Process Memory: {thresholds.get('process_mb', 0)}MB")
                console.print(f"  Cache Pressure: {thresholds.get('cache_pressure', 0) * 100:.0f}%")
                console.print(f"  Subprocess Memory: {thresholds.get('subprocess_mb', 0)}MB")
                
                # Profile summary
                profile = diagnostics_data.get("profile", {})
                if profile:
                    console.print(f"\n[bold]Current Status:[/bold]")
                    console.print(f"  Memory Pressure: {'Yes' if diagnostics_data.get('pressure_detected') else 'No'}")
                    console.print(f"  Auto Cleanup: {'Enabled' if diagnostics_data.get('auto_cleanup_enabled') else 'Disabled'}")
                    console.print(f"  Profiling: {'Active' if diagnostics_data.get('profiling_enabled') else 'Inactive'}")
                    
                    if diagnostics_data.get("last_cleanup"):
                        console.print(f"  Last Cleanup: {diagnostics_data['last_cleanup']}")
                
                # Subprocess info
                subprocess_info = profile.get("subprocesses", {})
                if subprocess_info and "error" not in subprocess_info:
                    console.print(f"\n[bold]Subprocess Memory:[/bold]")
                    console.print(f"  Active Processes: {subprocess_info.get('count', 0)}")
                    console.print(f"  Total Memory: {subprocess_info.get('total_mb', 0):.1f}MB")
                    
                    if subprocess_info.get('exceeds_threshold'):
                        console.print("  [red]⚠️  Exceeds threshold![/red]")
                
                # Top allocations (if profiling enabled)
                top_allocations = profile.get("top_allocations", [])
                if top_allocations:
                    console.print(f"\n[bold]Top Memory Allocations:[/bold]")
                    for i, alloc in enumerate(top_allocations[:5], 1):
                        console.print(f"  {i}. {alloc['file']}: {alloc['size_diff_mb']:.2f}MB")
                
                # Potential leaks
                potential_leaks = profile.get("potential_leaks", [])
                if potential_leaks:
                    console.print(f"\n[bold red]⚠️  Potential Memory Leaks:[/bold red]")
                    for leak in potential_leaks[:3]:
                        console.print(f"  • {leak['location']}: {leak['growth_mb']:.2f}MB growth")
                
            finally:
                await monitor.stop()
        
        asyncio.run(_show_diagnostics())
    
    @memory.command()
    @click.option('--threshold', type=float, help='Set memory threshold in MB')
    @click.option('--auto-cleanup/--no-auto-cleanup', help='Enable/disable automatic cleanup')
    def configure():
        """Configure memory management settings."""
        from ..services.health_monitor import HealthMonitor
        from ..services.memory_diagnostics import get_memory_diagnostics
        
        async def _configure():
            monitor = HealthMonitor()
            memory_diag = get_memory_diagnostics()
            
            try:
                await monitor.start()
                await memory_diag.start()
                
                # Apply configuration changes
                threshold = click.get_current_context().params.get('threshold')
                auto_cleanup = click.get_current_context().params.get('auto_cleanup')
                
                if threshold is not None:
                    memory_diag.set_memory_threshold(threshold)
                    console.print(f"[green]✅ Memory threshold set to {threshold}MB[/green]")
                
                if auto_cleanup is not None:
                    memory_diag.enable_auto_cleanup(auto_cleanup)
                    status = "enabled" if auto_cleanup else "disabled"
                    console.print(f"[green]✅ Auto cleanup {status}[/green]")
                
                # Show current configuration
                console.print("\n[bold]Current Memory Configuration:[/bold]")
                console.print(f"  Threshold: {memory_diag.memory_threshold_mb}MB")
                console.print(f"  Auto Cleanup: {'Enabled' if memory_diag.enable_auto_cleanup else 'Disabled'}")
                console.print(f"  Profile Interval: {memory_diag.profile_interval}s")
                console.print(f"  Cleanup Cooldown: {memory_diag._cleanup_cooldown}s")
                
            finally:
                await memory_diag.stop()
                await monitor.stop()
        
        asyncio.run(_configure())

    return cli_group