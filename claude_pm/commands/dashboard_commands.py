"""
CMPM Dashboard Commands
======================

Dashboard launching and management commands for the Claude PM Framework.
Provides portfolio manager dashboard launch with headless browser support.
"""

import logging
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from .utils.command_utils import CMPMCommandBase, run_async_command

console = Console()
logger = logging.getLogger(__name__)


class CMPMDashboardLauncher(CMPMCommandBase):
    """CMPM Dashboard Command Implementation with headless browser launch."""

    def __init__(self):
        super().__init__()
        managed_path = self.config.get("managed_path", str(Path.home() / "Projects" / "managed"))
        self.portfolio_manager_path = Path(managed_path) / "claude-pm-portfolio-manager"
        self.browser_process = None
        self.dashboard_process = None

    def detect_dashboard_port(self) -> Optional[int]:
        """Detect if dashboard is running and on which port."""
        # Check common ports for the dashboard
        common_ports = [3000, 8080, 8081, 5173]

        for port in common_ports:
            try:
                # Use netstat to check if port is in use
                result = subprocess.run(
                    ["netstat", "-an"], capture_output=True, text=True, timeout=5
                )

                if result.returncode == 0:
                    # Check if the port is listening
                    if f":{port}" in result.stdout and "LISTEN" in result.stdout:
                        # Try to make a simple HTTP request to verify it's actually a web server
                        try:
                            import urllib.request

                            with urllib.request.urlopen(
                                f"http://localhost:{port}/", timeout=3
                            ) as response:
                                if response.getcode() == 200:
                                    return port
                        except:
                            continue

            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue

        return None

    def start_dashboard_if_needed(self) -> Tuple[bool, Optional[int], str]:
        """Start the dashboard if it's not running."""
        # First check if dashboard is already running
        running_port = self.detect_dashboard_port()
        if running_port:
            return True, running_port, f"Dashboard already running on port {running_port}"

        # Check if portfolio manager directory exists
        if not self.portfolio_manager_path.exists():
            return False, None, f"Portfolio manager not found at {self.portfolio_manager_path}"

        # Check if package.json exists
        package_json = self.portfolio_manager_path / "package.json"
        if not package_json.exists():
            return False, None, f"package.json not found in {self.portfolio_manager_path}"

        try:
            # Start the dashboard in development mode
            console.print(f"[dim]Starting dashboard from {self.portfolio_manager_path}[/dim]")

            # Use npm run dev or equivalent to start the dashboard
            self.dashboard_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.portfolio_manager_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait a bit for the server to start
            time.sleep(3)

            # Check if the process is still running
            if self.dashboard_process.poll() is not None:
                stdout, stderr = self.dashboard_process.communicate()
                return False, None, f"Dashboard failed to start: {stderr}"

            # Try to detect the port it's running on
            for attempt in range(10):  # Try for 10 seconds
                running_port = self.detect_dashboard_port()
                if running_port:
                    return True, running_port, f"Dashboard started on port {running_port}"
                time.sleep(1)

            return False, None, "Dashboard started but port detection failed"

        except Exception as e:
            return False, None, f"Error starting dashboard: {str(e)}"

    def find_chrome_binary(self) -> Optional[str]:
        """Find Chrome binary using the framework's knowledge."""
        # Use the pattern from the framework's PDF generation knowledge
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
            "/usr/bin/google-chrome",  # Linux
            "/usr/bin/chromium-browser",  # Linux Chromium
            "/snap/bin/chromium",  # Snap package
        ]

        for path in chrome_paths:
            if Path(path).exists():
                return path

        # Try to find in PATH
        try:
            result = subprocess.run(
                ["which", "google-chrome"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        try:
            result = subprocess.run(
                ["which", "chromium"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def launch_headless_browser(self, dashboard_url: str) -> Tuple[bool, str]:
        """Launch headless browser pointing to dashboard."""
        chrome_path = self.find_chrome_binary()
        if not chrome_path:
            return False, "Chrome/Chromium not found. Please install Google Chrome or Chromium."

        try:
            # Use Chrome headless mode with parameters based on framework knowledge
            chrome_args = [
                chrome_path,
                "--headless",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=5000",
                "--window-size=1920,1080",
                "--user-agent=CMPM-Dashboard-Launcher/1.0",
                dashboard_url,
            ]

            console.print(f"[dim]Launching headless browser: {chrome_path}[/dim]")

            self.browser_process = subprocess.Popen(
                chrome_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Wait briefly to check if process started successfully
            time.sleep(2)

            if self.browser_process.poll() is not None:
                stdout, stderr = self.browser_process.communicate()
                return False, f"Browser failed to start: {stderr}"

            return True, f"Headless browser launched successfully (PID: {self.browser_process.pid})"

        except Exception as e:
            return False, f"Error launching browser: {str(e)}"

    def cleanup_processes(self):
        """Clean up spawned processes."""
        if self.browser_process:
            try:
                self.browser_process.terminate()
                self.browser_process.wait(timeout=5)
            except:
                try:
                    self.browser_process.kill()
                except:
                    pass

        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
            except:
                try:
                    self.dashboard_process.kill()
                except:
                    pass

    def handle_interrupt(self, signum, frame):
        """Handle interrupt signal."""
        console.print("\n[yellow]Received interrupt signal, cleaning up...[/yellow]")
        self.cleanup_processes()
        sys.exit(0)

    async def launch_dashboard(self, keep_alive: bool = False, port: Optional[int] = None) -> None:
        """Launch the CMPM dashboard in headless browser."""

        # Set up signal handler for cleanup
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Checking dashboard status...", total=None)

            # Step 1: Start dashboard if needed
            dashboard_started, dashboard_port, start_message = self.start_dashboard_if_needed()

            if not dashboard_started:
                progress.update(task, description="Dashboard startup failed")
                console.print(f"[red]❌ Dashboard Error: {start_message}[/red]")
                return

            progress.update(task, description="Preparing headless browser...")

            # Step 2: Prepare dashboard URL
            dashboard_url = f"http://localhost:{dashboard_port}/"

            # Step 3: Launch headless browser
            browser_launched, browser_message = self.launch_headless_browser(dashboard_url)

            if not browser_launched:
                progress.update(task, description="Browser launch failed")
                console.print(f"[red]❌ Browser Error: {browser_message}[/red]")
                self.cleanup_processes()
                return

            progress.update(task, description="Dashboard launched successfully")

        # Create success dashboard
        total_time = self.get_execution_time()

        header = Panel(
            Text(
                f"CMPM Dashboard Launcher v4.5.0\nDashboard URL: {dashboard_url}\nLaunch Time: {total_time:.2f}s",
                justify="center",
                style="bold white",
            ),
            title="🚀 Claude PM Portfolio Manager Dashboard",
            border_style="green",
        )

        console.print(header)
        console.print()

        # Create status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=15)
        table.add_column("Details", style="dim")

        table.add_row(
            "Portfolio Manager",
            "[green]RUNNING[/green]",
            f"Port {dashboard_port} | {start_message}",
        )

        table.add_row(
            "Headless Browser",
            "[green]LAUNCHED[/green]",
            f"Chrome PID {self.browser_process.pid if self.browser_process else 'N/A'} | {browser_message}",
        )

        table.add_row("Dashboard URL", "[green]ACCESSIBLE[/green]", f"{dashboard_url}")

        console.print(table)
        console.print()

        # Summary information
        summary_text = f"""
🎯 **Dashboard Access**: Portfolio manager dashboard is now running in headless browser mode
📊 **URL**: {dashboard_url}
🚀 **Launch Time**: {total_time:.2f} seconds
⚡ **Process Management**: Background processes managed by CMPM framework
        """

        console.print(Panel(summary_text.strip(), title="Launch Summary", border_style="blue"))

        if keep_alive:
            console.print()
            console.print(
                "[yellow]Dashboard is running in background. Press Ctrl+C to stop.[/yellow]"
            )

            try:
                # Keep the script running
                while True:
                    time.sleep(1)

                    # Check if processes are still running
                    if self.browser_process and self.browser_process.poll() is not None:
                        console.print("[yellow]Browser process terminated.[/yellow]")
                        break

                    if self.dashboard_process and self.dashboard_process.poll() is not None:
                        console.print("[yellow]Dashboard process terminated.[/yellow]")
                        break

            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping dashboard...[/yellow]")
            finally:
                self.cleanup_processes()
        else:
            console.print()
            console.print(
                "[dim]Dashboard launched in background. Processes will continue running.[/dim]"
            )
            console.print(
                "[dim]To stop the dashboard, use process management tools or rerun with --keep-alive.[/dim]"
            )


# CLI Commands
@click.command(name="cmpm:dashboard")
@click.option("--keep-alive", is_flag=True, help="Keep dashboard running in foreground")
@click.option("--port", type=int, help="Specify dashboard port (auto-detect if not provided)")
def cmpm_dashboard(keep_alive: bool, port: Optional[int]):
    """🚀 CMPM Dashboard - Launch portfolio manager dashboard in headless browser mode"""

    async def run_dashboard_launcher():
        launcher = CMPMDashboardLauncher()
        await launcher.launch_dashboard(keep_alive=keep_alive, port=port)

    run_async_command(run_dashboard_launcher())


__all__ = ["cmpm_dashboard", "CMPMDashboardLauncher"]
