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
    get_memory_integration,
    memory_aware_command,
    _display_directory_context,
    _initialize_memory_reliability_background
)

console = Console()
logger = logging.getLogger(__name__)


class ModularCLI:
    """Modular CLI system that loads commands from separate modules."""
    
    def __init__(self):
        self.cli_group = None
        self.modules_loaded = False
    
    def create_cli_group(self):
        """Create the main CLI group with core functionality."""
        
        @click.group()
        @click.version_option(prog_name="Claude Multi-Agent PM Framework")
        @click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
        @click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
        @click.pass_context
        def cli(ctx, verbose, config):
            """
            Claude Multi-Agent Project Management Framework - Multi-Agent Orchestration for AI-driven Project Management

            A comprehensive framework for managing AI-enhanced development projects with
            integrated memory management, health monitoring, and multi-agent coordination.
            """
            ctx.ensure_object(dict)
            ctx.obj["verbose"] = verbose
            ctx.obj["config"] = config

            # FIXED: Display deployment and working directories on every call
            _display_directory_context()
            
            # Initialize memory reliability service in background
            _initialize_memory_reliability_background()

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


__all__ = [
    'ModularCLI',
    'get_cli', 
    'create_modular_cli',
    'register_external_commands'
]