#!/usr/bin/env python3
"""
CLI Utilities Module - Claude Multi-Agent PM Framework

Shared utilities and common patterns for modular CLI system.
Extracted from main CLI as part of ISS-0114 modularization initiative.
"""

import asyncio
import sys
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from functools import wraps

import click
from rich.console import Console
from rich.panel import Panel

from ..core.config import Config
# TEMPORARILY DISABLED: Memory integration causing import failures
# from ..services.memory.cli_integration import MemoryIntegratedCLI
from ..core.logging_config import setup_streaming_logger, finalize_streaming_logs

console = Console()
logger = logging.getLogger(__name__)

# Global memory integration instance
_memory_integration = None


async def get_memory_integration():
    """Get or create global memory integration instance. (DISABLED - memory system disabled)"""
    global _memory_integration
    if _memory_integration is None:
        # TEMPORARILY DISABLED: Memory integration causing import failures
        # _memory_integration = MemoryIntegratedCLI()
        # try:
        #     await _memory_integration.initialize()
        #     logger.info("Memory trigger CLI integration initialized")
        # except Exception as e:
        #     logger.warning(f"Failed to initialize memory integration: {e}")
        logger.debug("Memory integration disabled - returning None")
        _memory_integration = None
    return _memory_integration


def memory_aware_command(func):
    """Decorator to add memory trigger support to CLI commands."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # For sync CLI commands, wrap the execution with memory triggers
        async def execute_with_memory():
            integration = await get_memory_integration()
            if integration and integration.service:
                try:
                    return await integration.execute_with_memory_trigger(
                        operation_name=func.__name__,
                        operation_func=lambda **kw: func(*args, **kwargs),
                        project_name="claude-multiagent-pm",
                        operation_type="cli_command"
                    )
                except Exception as e:
                    logger.warning(f"Memory trigger execution failed: {e}")
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        # Run the async wrapper
        try:
            return asyncio.run(execute_with_memory())
        except RuntimeError:
            # If already in event loop, just run normally
            return func(*args, **kwargs)
    
    return wrapper


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


def _get_framework_version():
    """Get framework version from VERSION file."""
    try:
        version_file = Path(__file__).parent.parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "0.4.6"  # Fallback version
    except Exception:
        return "0.4.6"


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


def _display_directory_context_streaming():
    """Display deployment and working directory context with streaming logger."""
    try:
        streaming_logger = setup_streaming_logger("directory_context")
        
        working_dir = Path.cwd()
        claude_pm_path = get_claude_pm_path()
        
        streaming_logger.info(f"📂 Working Directory: {working_dir}")
        streaming_logger.info(f"🔧 Framework Path: {claude_pm_path}")
        streaming_logger.info("✅ Directory context loaded")
        
        finalize_streaming_logs(streaming_logger)
        print()  # Add spacing after streaming output
        
    except Exception as e:
        logger.debug(f"Failed to display directory context: {e}")


def _initialize_memory_reliability_background():
    """Initialize memory reliability service in background. (DISABLED - memory system disabled)"""
    async def init_memory_reliability():
        try:
            # TEMPORARILY DISABLED: Memory reliability service causing import failures
            # from ..services.memory_reliability import get_memory_reliability_service
            # reliability_service = await get_memory_reliability_service()
            # logger.debug("Memory reliability service initialized in background")
            logger.debug("Memory reliability service disabled")
        except Exception as e:
            logger.debug(f"Background memory reliability initialization failed: {e}")
    
    # Run in background without blocking CLI startup (disabled)
    try:
        # asyncio.create_task(init_memory_reliability())
        logger.debug("Memory reliability background initialization disabled")
    except RuntimeError:
        # Event loop not running, skip background initialization
        pass


def async_command(func):
    """Decorator to handle async CLI commands."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        async def run():
            return await func(*args, **kwargs)
        
        try:
            return asyncio.run(run())
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Operation cancelled by user[/bold yellow]")
            sys.exit(130)
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
            logger.error(f"Command failed: {func.__name__}: {e}")
            sys.exit(1)
    
    return wrapper


def timed_operation(operation_name: str):
    """Decorator to time operations and display results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                console.print(f"[dim]{operation_name} completed in {duration:.0f}ms[/dim]")
                return result
            except Exception as e:
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                console.print(f"[dim]{operation_name} failed after {duration:.0f}ms[/dim]")
                raise
        return wrapper
    return decorator


def confirm_action(message: str, default: bool = False):
    """Helper for confirming dangerous actions."""
    from rich.prompt import Confirm
    return Confirm.ask(message, default=default)


def format_table_data(data: list, title: str, columns: dict):
    """Helper to format data into rich tables."""
    from rich.table import Table
    
    table = Table(title=title)
    
    # Add columns
    for col_name, col_style in columns.items():
        table.add_column(col_name, style=col_style)
    
    # Add rows
    for row in data:
        table.add_row(*[str(row.get(col, "")) for col in columns.keys()])
    
    return table


def format_status_panel(data: dict, title: str):
    """Helper to format status data into panels."""
    content_lines = []
    for key, value in data.items():
        formatted_key = key.replace("_", " ").title()
        content_lines.append(f"[bold]{formatted_key}:[/bold] {value}")
    
    content = "\n".join(content_lines)
    return Panel(content, title=title)


def handle_service_errors(func):
    """Decorator to handle common service errors gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError as e:
            console.print(f"[red]❌ Connection error: {e}[/red]")
            console.print("[yellow]Check that required services are running[/yellow]")
            sys.exit(1)
        except FileNotFoundError as e:
            console.print(f"[red]❌ File not found: {e}[/red]")
            console.print("[yellow]Check your configuration and paths[/yellow]")
            sys.exit(1)
        except PermissionError as e:
            console.print(f"[red]❌ Permission denied: {e}[/red]")
            console.print("[yellow]Check file/directory permissions[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]❌ Unexpected error: {e}[/red]")
            logger.error(f"Service error in {func.__name__}: {e}")
            sys.exit(1)
    
    return wrapper


def validate_project_name(project_name: str) -> bool:
    """Validate project name format."""
    if not project_name:
        return False
    
    # Basic validation: no spaces, reasonable length, alphanumeric + hyphens/underscores
    if len(project_name) > 100:
        return False
    
    import re
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, project_name))


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def safe_json_loads(json_str: str, default=None):
    """Safely load JSON with fallback."""
    try:
        import json
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate string with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


class CLIContext:
    """Context manager for CLI operations with shared state."""
    
    def __init__(self):
        self.start_time = None
        self.verbose = False
        self.config = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.config = get_framework_config()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time and self.verbose:
            duration = time.time() - self.start_time
            console.print(f"[dim]Operation completed in {format_duration(duration)}[/dim]")


def load_config_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file with fallbacks."""
    import json
    import yaml
    
    if not config_path:
        # Try default locations
        for default_path in [".claude-pm/config.json", ".claude-pm/config.yaml", "config.json"]:
            if Path(default_path).exists():
                config_path = default_path
                break
    
    if not config_path or not Path(config_path).exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            if config_path.endswith('.json'):
                return json.load(f)
            elif config_path.endswith(('.yaml', '.yml')):
                return yaml.safe_load(f)
            else:
                # Try JSON first, then YAML
                content = f.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return yaml.safe_load(content)
    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {e}")
        return {}


def save_config_file(config: Dict[str, Any], config_path: str):
    """Save configuration to file."""
    import json
    
    # Ensure directory exists
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save config to {config_path}: {e}")
        raise


def check_dependency(package_name: str, import_name: str = None) -> bool:
    """Check if a dependency is available."""
    try:
        import importlib
        module_name = import_name or package_name
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def get_system_info() -> Dict[str, str]:
    """Get system information for debugging."""
    import platform
    
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "working_directory": str(Path.cwd()),
        "framework_path": str(get_claude_pm_path()),
        "managed_path": str(get_managed_path()),
    }


# Common click options that can be reused
verbose_option = click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
config_option = click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
dry_run_option = click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
force_option = click.option("--force", is_flag=True, help="Force operation without confirmation")
quiet_option = click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")


def common_options(func):
    """Decorator to add common CLI options."""
    func = verbose_option(func)
    func = config_option(func)
    return func