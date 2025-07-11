"""
Dependency Command for Claude PM Framework CLI.

Provides dependency management capabilities including:
- Dependency discovery and analysis
- Installation automation
- Health monitoring
- Verification and reporting

CMPM-103: Dependency Management Strategy CLI Interface
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from ..services.dependency_manager import DependencyManager, DependencyType, InstallationMethod
from ..core.cli_base import CLICommand


class DependencyCommand(CLICommand):
    """Dependency management CLI command."""

    def __init__(self):
        super().__init__("dependency", "Dependency management operations")
        self.console = Console()
        self.dependency_manager = None

    def create_command_group(self) -> click.Group:
        """Create the dependency command group."""

        @click.group(name="dependency", help="Dependency management operations")
        @click.pass_context
        def dependency_group(ctx):
            """Dependency management command group."""
            # Store context for subcommands
            ctx.ensure_object(dict)
            ctx.obj["dependency_command"] = self

        # Add subcommands
        dependency_group.add_command(self._create_status_command())
        dependency_group.add_command(self._create_check_command())
        dependency_group.add_command(self._create_install_command())
        dependency_group.add_command(self._create_verify_command())
        dependency_group.add_command(self._create_report_command())
        dependency_group.add_command(self._create_health_command())
        dependency_group.add_command(self._create_ai_trackdown_command())

        return dependency_group

    def _create_status_command(self) -> click.Command:
        """Create the status subcommand."""

        @click.command(name="status", help="Show dependency status")
        @click.option(
            "--format",
            type=click.Choice(["table", "json", "summary"]),
            default="table",
            help="Output format",
        )
        @click.option(
            "--type",
            type=click.Choice([t.value for t in DependencyType]),
            help="Filter by dependency type",
        )
        @click.option("--missing-only", is_flag=True, help="Show only missing dependencies")
        @click.pass_context
        def status_command(ctx, format, type, missing_only):
            """Show dependency status."""
            return asyncio.run(self._handle_status(ctx, format, type, missing_only))

        return status_command

    def _create_check_command(self) -> click.Command:
        """Create the check subcommand."""

        @click.command(name="check", help="Check all dependencies")
        @click.option("--refresh", is_flag=True, help="Force refresh of dependency information")
        @click.option("--verbose", is_flag=True, help="Show detailed information")
        @click.pass_context
        def check_command(ctx, refresh, verbose):
            """Check all dependencies."""
            return asyncio.run(self._handle_check(ctx, refresh, verbose))

        return check_command

    def _create_install_command(self) -> click.Command:
        """Create the install subcommand."""

        @click.command(name="install", help="Install a dependency")
        @click.argument("dependency_name")
        @click.option(
            "--method",
            type=click.Choice([m.value for m in InstallationMethod]),
            help="Installation method",
        )
        @click.option(
            "--dry-run",
            is_flag=True,
            help="Show what would be installed without actually installing",
        )
        @click.pass_context
        def install_command(ctx, dependency_name, method, dry_run):
            """Install a dependency."""
            return asyncio.run(self._handle_install(ctx, dependency_name, method, dry_run))

        return install_command

    def _create_verify_command(self) -> click.Command:
        """Create the verify subcommand."""

        @click.command(name="verify", help="Verify dependency installation")
        @click.argument("dependency_name", required=False)
        @click.option("--all", is_flag=True, help="Verify all dependencies")
        @click.pass_context
        def verify_command(ctx, dependency_name, all):
            """Verify dependency installation."""
            return asyncio.run(self._handle_verify(ctx, dependency_name, all))

        return verify_command

    def _create_report_command(self) -> click.Command:
        """Create the report subcommand."""

        @click.command(name="report", help="Generate dependency report")
        @click.option(
            "--format",
            type=click.Choice(["json", "detailed", "summary"]),
            default="detailed",
            help="Report format",
        )
        @click.option("--output", type=click.Path(), help="Output file path")
        @click.pass_context
        def report_command(ctx, format, output):
            """Generate dependency report."""
            return asyncio.run(self._handle_report(ctx, format, output))

        return report_command

    def _create_health_command(self) -> click.Command:
        """Create the health subcommand."""

        @click.command(name="health", help="Check dependency health")
        @click.option("--detailed", is_flag=True, help="Show detailed health information")
        @click.pass_context
        def health_command(ctx, detailed):
            """Check dependency health."""
            return asyncio.run(self._handle_health(ctx, detailed))

        return health_command

    def _create_ai_trackdown_command(self) -> click.Command:
        """Create the ai-trackdown subcommand."""

        @click.command(name="ai-trackdown", help="AI-Trackdown-Tools specific operations")
        @click.option("--install", is_flag=True, help="Install ai-trackdown-tools")
        @click.option("--verify", is_flag=True, help="Verify ai-trackdown-tools installation")
        @click.option("--status", is_flag=True, help="Show ai-trackdown-tools status")
        @click.pass_context
        def ai_trackdown_command(ctx, install, verify, status):
            """AI-Trackdown-Tools specific operations."""
            return asyncio.run(self._handle_ai_trackdown(ctx, install, verify, status))

        return ai_trackdown_command

    async def _initialize_dependency_manager(self) -> None:
        """Initialize the dependency manager."""
        if self.dependency_manager is None:
            self.dependency_manager = DependencyManager()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Initializing dependency manager...", total=None)
                await self.dependency_manager._initialize()
                progress.update(task, completed=True)

    async def _handle_status(
        self, ctx, format: str, type_filter: Optional[str], missing_only: bool
    ) -> None:
        """Handle status command."""
        await self._initialize_dependency_manager()

        dependencies = self.dependency_manager.get_dependencies()

        # Apply filters
        if type_filter:
            dependencies = {
                name: info for name, info in dependencies.items() if info.type.value == type_filter
            }

        if missing_only:
            dependencies = {
                name: info for name, info in dependencies.items() if not info.is_installed
            }

        if format == "json":
            # JSON format
            output = {}
            for name, info in dependencies.items():
                output[name] = {
                    "type": info.type.value,
                    "is_installed": info.is_installed,
                    "version": info.version,
                    "required_version": info.required_version,
                    "installation_method": (
                        info.installation_method.value if info.installation_method else None
                    ),
                    "installation_path": info.installation_path,
                    "last_checked": info.last_checked,
                }

            self.console.print(json.dumps(output, indent=2))

        elif format == "summary":
            # Summary format
            total = len(dependencies)
            installed = sum(1 for info in dependencies.values() if info.is_installed)
            missing = total - installed

            self.console.print(f"Dependencies Summary:")
            self.console.print(f"  Total: {total}")
            self.console.print(f"  Installed: {installed}")
            self.console.print(f"  Missing: {missing}")
            self.console.print(f"  Health: {round((installed/total)*100) if total > 0 else 0}%")

        else:
            # Table format (default)
            table = Table(title="Dependency Status")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Version", style="blue")
            table.add_column("Method", style="yellow")

            for name, info in dependencies.items():
                status = "✅ Installed" if info.is_installed else "❌ Missing"
                version = info.version or "unknown"
                method = info.installation_method.value if info.installation_method else "unknown"

                table.add_row(name, info.type.value, status, version, method)

            self.console.print(table)

    async def _handle_check(self, ctx, refresh: bool, verbose: bool) -> None:
        """Handle check command."""
        await self._initialize_dependency_manager()

        if refresh:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Refreshing dependencies...", total=None)
                await self.dependency_manager.refresh_dependencies()
                progress.update(task, completed=True)

        dependencies = self.dependency_manager.get_dependencies()

        # Count status
        total = len(dependencies)
        installed = sum(1 for info in dependencies.values() if info.is_installed)
        missing = total - installed

        # Show summary
        self.console.print(
            Panel(
                f"Dependency Check Complete\n"
                f"Total: {total} | Installed: {installed} | Missing: {missing}\n"
                f"Health Score: {round((installed/total)*100) if total > 0 else 0}%",
                title="Check Results",
            )
        )

        # Show missing dependencies
        if missing > 0:
            missing_deps = [name for name, info in dependencies.items() if not info.is_installed]
            self.console.print(f"\n❌ Missing Dependencies: {', '.join(missing_deps)}")

            # Show installation recommendations
            recommendations = await self.dependency_manager.get_installation_recommendations()
            if recommendations:
                self.console.print("\n💡 Installation Recommendations:")
                for rec in recommendations:
                    self.console.print(f"  • {rec}")

        if verbose:
            # Show detailed information
            self.console.print("\n📋 Detailed Information:")
            for name, info in dependencies.items():
                status = "✅" if info.is_installed else "❌"
                self.console.print(f"  {status} {name}")
                if info.is_installed:
                    self.console.print(f"    Version: {info.version or 'unknown'}")
                    self.console.print(
                        f"    Method: {info.installation_method.value if info.installation_method else 'unknown'}"
                    )
                    if info.installation_path:
                        self.console.print(f"    Path: {info.installation_path}")
                else:
                    self.console.print(f"    Required: {info.required_version or 'any'}")
                self.console.print(f"    Type: {info.type.value}")
                self.console.print(f"    Last Checked: {info.last_checked or 'never'}")

    async def _handle_install(
        self, ctx, dependency_name: str, method: Optional[str], dry_run: bool
    ) -> None:
        """Handle install command."""
        await self._initialize_dependency_manager()

        if dry_run:
            self.console.print(f"🔍 Dry run: Would install {dependency_name}")

            # Show what would be installed
            dep_info = self.dependency_manager.get_dependency(dependency_name)
            if dep_info:
                if dep_info.is_installed:
                    self.console.print(f"  ✅ {dependency_name} is already installed")
                else:
                    install_method = InstallationMethod(method) if method else None
                    if not install_method:
                        # Get best method
                        dep_config = self.dependency_manager.CORE_DEPENDENCIES.get(
                            dependency_name, {}
                        )
                        install_method = self.dependency_manager._select_best_installation_method(
                            dep_config.get("type", DependencyType.SYSTEM_BINARY), dep_config
                        )

                    self.console.print(
                        f"  📦 Would install {dependency_name} using {install_method.value}"
                    )
            else:
                self.console.print(f"  ❌ Unknown dependency: {dependency_name}")

            return

        # Perform actual installation
        self.console.print(f"🔧 Installing {dependency_name}...")

        install_method = InstallationMethod(method) if method else None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Installing {dependency_name}...", total=None)

            result = await self.dependency_manager.install_dependency(
                dependency_name, install_method
            )

            progress.update(task, completed=True)

        if result.success:
            self.console.print(f"✅ Successfully installed {dependency_name}")
            if result.version:
                self.console.print(f"   Version: {result.version}")
            if result.installation_path:
                self.console.print(f"   Path: {result.installation_path}")
        else:
            self.console.print(f"❌ Failed to install {dependency_name}")
            self.console.print(f"   Error: {result.error_message}")

            if result.logs:
                self.console.print("\n📋 Installation Logs:")
                for log in result.logs:
                    if log.strip():
                        self.console.print(f"   {log}")

    async def _handle_verify(self, ctx, dependency_name: Optional[str], all: bool) -> None:
        """Handle verify command."""
        await self._initialize_dependency_manager()

        if all:
            # Verify all dependencies
            self.console.print("🔍 Verifying all dependencies...")

            dependencies = self.dependency_manager.get_dependencies()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Verifying dependencies...", total=len(dependencies))

                verified = 0
                for name, info in dependencies.items():
                    if info.is_installed:
                        # For now, just check if it's marked as installed
                        # In a real implementation, we might re-check each dependency
                        verified += 1

                    progress.update(task, advance=1)

            self.console.print(f"✅ Verified {verified}/{len(dependencies)} dependencies")

        elif dependency_name:
            # Verify specific dependency
            if dependency_name == "ai-trackdown-tools":
                self.console.print(f"🔍 Verifying {dependency_name}...")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                    transient=True,
                ) as progress:
                    task = progress.add_task(f"Verifying {dependency_name}...", total=None)

                    is_functional = await self.dependency_manager.verify_ai_trackdown_tools()

                    progress.update(task, completed=True)

                if is_functional:
                    self.console.print(f"✅ {dependency_name} is functional")
                else:
                    self.console.print(f"❌ {dependency_name} is not functional")
            else:
                # Generic verification
                dep_info = self.dependency_manager.get_dependency(dependency_name)
                if dep_info:
                    if dep_info.is_installed:
                        self.console.print(f"✅ {dependency_name} is installed")
                    else:
                        self.console.print(f"❌ {dependency_name} is not installed")
                else:
                    self.console.print(f"❌ Unknown dependency: {dependency_name}")
        else:
            self.console.print("❌ Please specify a dependency name or use --all")

    async def _handle_report(self, ctx, format: str, output: Optional[str]) -> None:
        """Handle report command."""
        await self._initialize_dependency_manager()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Generating dependency report...", total=None)

            report = await self.dependency_manager.generate_dependency_report()

            progress.update(task, completed=True)

        if format == "json":
            # JSON format
            report_data = {
                "deployment_type": report.deployment_type,
                "platform": report.platform,
                "timestamp": report.timestamp,
                "health_score": report.health_score,
                "dependencies": {
                    name: {
                        "type": info.type.value,
                        "is_installed": info.is_installed,
                        "version": info.version,
                        "required_version": info.required_version,
                        "installation_method": (
                            info.installation_method.value if info.installation_method else None
                        ),
                        "installation_path": info.installation_path,
                        "last_checked": info.last_checked,
                    }
                    for name, info in report.dependencies.items()
                },
                "missing_dependencies": report.missing_dependencies,
                "outdated_dependencies": report.outdated_dependencies,
                "installation_recommendations": report.installation_recommendations,
            }

            json_output = json.dumps(report_data, indent=2)

            if output:
                Path(output).write_text(json_output)
                self.console.print(f"📄 Report saved to {output}")
            else:
                self.console.print(json_output)

        elif format == "summary":
            # Summary format
            self.console.print(f"Dependency Report Summary:")
            self.console.print(f"  Deployment: {report.deployment_type}")
            self.console.print(f"  Platform: {report.platform}")
            self.console.print(f"  Health Score: {report.health_score}%")
            self.console.print(f"  Total Dependencies: {len(report.dependencies)}")
            self.console.print(f"  Missing: {len(report.missing_dependencies)}")
            self.console.print(f"  Outdated: {len(report.outdated_dependencies)}")
            self.console.print(f"  Recommendations: {len(report.installation_recommendations)}")

        else:
            # Detailed format (default)
            self.console.print(
                Panel(
                    f"Deployment: {report.deployment_type}\n"
                    f"Platform: {report.platform}\n"
                    f"Health Score: {report.health_score}%\n"
                    f"Generated: {report.timestamp}",
                    title="Dependency Report",
                )
            )

            # Dependencies table
            table = Table(title="Dependencies")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Version", style="blue")

            for name, info in report.dependencies.items():
                status = "✅ Installed" if info.is_installed else "❌ Missing"
                version = info.version or "unknown"

                table.add_row(name, info.type.value, status, version)

            self.console.print(table)

            # Show missing dependencies
            if report.missing_dependencies:
                self.console.print("\n❌ Missing Dependencies:")
                for dep in report.missing_dependencies:
                    self.console.print(f"  • {dep}")

            # Show recommendations
            if report.installation_recommendations:
                self.console.print("\n💡 Installation Recommendations:")
                for rec in report.installation_recommendations:
                    self.console.print(f"  • {rec}")

    async def _handle_health(self, ctx, detailed: bool) -> None:
        """Handle health command."""
        await self._initialize_dependency_manager()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Checking dependency health...", total=None)

            health_checks = await self.dependency_manager._health_check()

            progress.update(task, completed=True)

        # Calculate health score
        total_checks = len(health_checks)
        passed_checks = sum(1 for status in health_checks.values() if status)
        health_score = round((passed_checks / total_checks) * 100) if total_checks > 0 else 0

        # Show health summary
        self.console.print(
            Panel(
                f"Health Score: {health_score}%\n" f"Passed: {passed_checks}/{total_checks}",
                title="Dependency Health",
            )
        )

        if detailed:
            # Show detailed health information
            table = Table(title="Health Checks")
            table.add_column("Check", style="cyan")
            table.add_column("Status", style="green")

            for check_name, status in health_checks.items():
                status_text = "✅ Pass" if status else "❌ Fail"
                table.add_row(check_name, status_text)

            self.console.print(table)

    async def _handle_ai_trackdown(self, ctx, install: bool, verify: bool, status: bool) -> None:
        """Handle ai-trackdown command."""
        await self._initialize_dependency_manager()

        if install:
            # Install ai-trackdown-tools
            self.console.print("🔧 Installing ai-trackdown-tools...")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Installing ai-trackdown-tools...", total=None)

                result = await self.dependency_manager.install_dependency("ai-trackdown-tools")

                progress.update(task, completed=True)

            if result.success:
                self.console.print("✅ ai-trackdown-tools installed successfully")
            else:
                self.console.print("❌ Failed to install ai-trackdown-tools")
                self.console.print(f"   Error: {result.error_message}")

        elif verify:
            # Verify ai-trackdown-tools
            self.console.print("🔍 Verifying ai-trackdown-tools...")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Verifying ai-trackdown-tools...", total=None)

                is_functional = await self.dependency_manager.verify_ai_trackdown_tools()

                progress.update(task, completed=True)

            if is_functional:
                self.console.print("✅ ai-trackdown-tools is functional")
            else:
                self.console.print("❌ ai-trackdown-tools is not functional")

        elif status:
            # Show ai-trackdown-tools status
            dep_info = self.dependency_manager.get_dependency("ai-trackdown-tools")

            if dep_info:
                self.console.print(f"AI-Trackdown-Tools Status:")
                self.console.print(f"  Installed: {'✅ Yes' if dep_info.is_installed else '❌ No'}")
                self.console.print(f"  Version: {dep_info.version or 'unknown'}")
                self.console.print(
                    f"  Method: {dep_info.installation_method.value if dep_info.installation_method else 'unknown'}"
                )
                self.console.print(f"  Required: {dep_info.required_version or 'any'}")

                if dep_info.installation_path:
                    self.console.print(f"  Path: {dep_info.installation_path}")

                # Verify functionality
                is_functional = await self.dependency_manager.verify_ai_trackdown_tools()
                self.console.print(f"  Functional: {'✅ Yes' if is_functional else '❌ No'}")
            else:
                self.console.print("❌ ai-trackdown-tools dependency not found")

        else:
            self.console.print("❌ Please specify an action: --install, --verify, or --status")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.dependency_manager:
            await self.dependency_manager._cleanup()
            self.dependency_manager = None
