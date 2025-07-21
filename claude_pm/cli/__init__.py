#!/usr/bin/env python3
"""
CLI Module - Claude Multi-Agent PM Framework

Modular CLI system with dynamic command loading.
Part of ISS-0114 modularization initiative.
"""

import logging
from typing import Dict, Any, Optional

import click
from rich.console import Console

from .cli_utils import (
    _display_directory_context,
)
from ..services.model_selector import ModelType

console = Console()
logger = logging.getLogger(__name__)


def _resolve_model_selection(model_input: str) -> Optional[str]:
    """
    Resolve model selection from user input to valid ModelType.
    
    Supports both full model IDs and friendly aliases:
    - 'sonnet' -> 'claude-sonnet-4-20250514'
    - 'opus' -> 'claude-4-opus'
    - 'haiku' -> 'claude-3-haiku-20240307'
    - Direct model IDs are validated against ModelType enum
    
    Args:
        model_input: User input for model selection
        
    Returns:
        Valid model ID string or None if invalid
    """
    if not model_input:
        return None
    
    # Define friendly aliases
    model_aliases = {
        'sonnet': ModelType.SONNET_4.value,
        'sonnet4': ModelType.SONNET_4.value,
        'opus': ModelType.OPUS_4.value,
        'opus4': ModelType.OPUS_4.value,
        'haiku': ModelType.HAIKU.value,
        'sonnet3': ModelType.SONNET.value,
        'opus3': ModelType.OPUS.value,
    }
    
    # Normalize input
    normalized_input = model_input.lower().strip()
    
    # CRITICAL FIX: Check if normalized input is empty after stripping
    # This prevents whitespace-only inputs (spaces, tabs, newlines) from 
    # matching against all model strings in the partial match logic
    if not normalized_input:
        return None
    
    # Check aliases first
    if normalized_input in model_aliases:
        return model_aliases[normalized_input]
    
    # Check if it's a valid ModelType directly
    try:
        for model_type in ModelType:
            if model_type.value.lower() == normalized_input:
                return model_type.value
    except Exception:
        pass
    
    # Check partial matches for convenience
    for model_type in ModelType:
        if normalized_input in model_type.value.lower():
            return model_type.value
    
    return None


def get_available_models() -> Dict[str, str]:
    """
    Get available models and their aliases for help text and validation.
    
    Returns:
        Dictionary mapping aliases to full model IDs
    """
    return {
        'sonnet': ModelType.SONNET_4.value,
        'sonnet4': ModelType.SONNET_4.value,
        'opus': ModelType.OPUS_4.value,
        'opus4': ModelType.OPUS_4.value,
        'haiku': ModelType.HAIKU.value,
        'sonnet3': ModelType.SONNET.value,
        'opus3': ModelType.OPUS.value,
    }


def format_model_help() -> str:
    """Format help text for model selection flag."""
    aliases = get_available_models()
    help_lines = ["Available models and aliases:"]
    
    # Group by model type
    claude4_models = []
    claude3_models = []
    
    for alias, model_id in aliases.items():
        if "claude-4" in model_id or "claude-sonnet-4" in model_id:
            claude4_models.append(f"  {alias} -> {model_id}")
        else:
            claude3_models.append(f"  {alias} -> {model_id}")
    
    if claude4_models:
        help_lines.extend(["", "Claude 4 models (recommended):"] + claude4_models)
    
    if claude3_models:
        help_lines.extend(["", "Claude 3 models (legacy):"] + claude3_models)
    
    help_lines.extend([
        "",
        "Examples:",
        "  --model sonnet      # Use Claude Sonnet 4 (default for most agents)",
        "  --model opus        # Use Claude 4 Opus (for complex tasks)",
        "  --model haiku       # Use Claude 3 Haiku (for simple tasks)"
    ])
    
    return "\n".join(help_lines)


class ModularCLI:
    """Modular CLI system that loads commands from separate modules."""
    
    def __init__(self):
        self.cli_group = None
        self.modules_loaded = False
    
    def create_cli_group(self):
        """Create the main CLI group with core functionality."""
        
        @click.group()
        @click.version_option(version=None, package_name="claude-multiagent-pm", prog_name="Claude Multi-Agent PM Framework")
        @click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
        @click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
        @click.option("--model", "-m", type=str, 
                     help="Override AI model selection. Use 'sonnet' (Claude Sonnet 4), 'opus' (Claude 4 Opus), 'haiku' (Claude 3 Haiku), or full model ID.")
        @click.option("--test-mode", is_flag=True, help="Enable test mode for framework testing (includes hello world protocol)")
        @click.pass_context
        def cli(ctx, verbose, config, model, test_mode):
            """
            Claude Multi-Agent Project Management Framework - Multi-Agent Orchestration for AI-driven Project Management

            A comprehensive framework for managing AI-enhanced development projects with
            integrated memory management, health monitoring, and multi-agent coordination.
            """
            ctx.ensure_object(dict)
            ctx.obj["verbose"] = verbose
            ctx.obj["config"] = config
            ctx.obj["test_mode"] = test_mode
            
            # Set test mode environment variable if enabled
            if test_mode:
                import os
                os.environ['CLAUDE_PM_TEST_MODE'] = 'true'
                if verbose:
                    console.print("[yellow]Test mode enabled: Hello world protocol active[/yellow]")
            
            # Process and validate model selection
            resolved_model = None
            if model:
                resolved_model = _resolve_model_selection(model)
                if resolved_model:
                    ctx.obj["model"] = resolved_model
                    if verbose:
                        console.print(f"[dim]Using model: {resolved_model}[/dim]")
                else:
                    console.print(f"[red]Warning: Invalid model '{model}'. Using default model selection.[/red]")
            
            # FIXED: Display deployment and working directories on every call
            _display_directory_context()

            if verbose:
                console.print("[dim]Claude Multi-Agent PM Framework v3.0.0 - Python Edition[/dim]")

        self.cli_group = cli
        return cli
    
    def load_command_modules(self):
        """Load all command modules and register their commands."""
        if self.modules_loaded:
            return
        
        if not self.cli_group:
            raise RuntimeError("CLI group must be created before loading modules")
        
        try:
            # Import and register setup commands
            from .setup_commands import register_setup_commands
            register_setup_commands(self.cli_group)
            logger.debug("Loaded setup commands module")
            
            # Import and register test commands  
            from .test_commands import register_test_commands
            register_test_commands(self.cli_group)
            logger.debug("Loaded test commands module")
            
            # Import and register productivity commands
            from .productivity_commands import register_productivity_commands
            register_productivity_commands(self.cli_group)
            logger.debug("Loaded productivity commands module")
            
            # Import and register deployment commands
            from .deployment_commands import register_deployment_commands
            register_deployment_commands(self.cli_group)
            logger.debug("Loaded deployment commands module")
            
            # Import and register system commands
            from .system_commands import register_system_commands
            register_system_commands(self.cli_group)
            logger.debug("Loaded system commands module")
            
            self.modules_loaded = True
            logger.info("All CLI command modules loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load command modules: {e}")
            raise
    
    def get_cli(self):
        """Get the fully configured CLI with all modules loaded."""
        if not self.cli_group:
            self.create_cli_group()
        
        if not self.modules_loaded:
            self.load_command_modules()
        
        return self.cli_group


# Global instance for the modular CLI
_modular_cli = ModularCLI()


def get_cli():
    """Get the main CLI instance with all modules loaded."""
    return _modular_cli.get_cli()


def register_external_commands(cli_group):
    """Register external commands that aren't in the modular system yet."""
    
    # Add enhanced CLI flags (pure Python implementation)
    try:
        from ..cli_flags import cli_flags
        cli_group.add_command(cli_flags, name="flags")
        logger.debug("Added enhanced CLI flags")
    except Exception as e:
        logger.warning(f"Failed to load enhanced CLI flags: {e}")
    
    # Add enforcement commands (from cli_enforcement.py)
    try:
        from ..cli_enforcement import enforcement_cli
        cli_group.add_command(enforcement_cli)
        logger.debug("Added enforcement commands")
    except Exception as e:
        logger.warning(f"Failed to load enforcement commands: {e}")
    
    # Register CMPM commands (from cmpm_commands.py)
    try:
        from ..cmpm_commands import register_cmpm_commands
        register_cmpm_commands(cli_group)
        logger.debug("Added CMPM commands")
    except Exception as e:
        logger.warning(f"Failed to load CMPM commands: {e}")
    
    # Integrate deployment system (from cli_deployment_integration.py)
    try:
        from ..cli_deployment_integration import integrate_deployment_system
        integrate_deployment_system(cli_group)
        logger.debug("Added deployment integration")
    except Exception as e:
        logger.warning(f"Failed to load deployment integration: {e}")


def create_modular_cli():
    """Create the complete CLI with all modules and external commands."""
    cli = get_cli()
    
    # Register external commands that haven't been modularized yet
    register_external_commands(cli)
    
    return cli


def main():
    """Main entry point for the CLI application."""
    from .__main__ import main as cli_main
    cli_main()


__all__ = [
    'ModularCLI',
    'get_cli', 
    'create_modular_cli',
    'register_external_commands',
    'main',
    'get_available_models',
    'format_model_help',
    '_resolve_model_selection'
]