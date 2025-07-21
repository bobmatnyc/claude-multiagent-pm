#!/usr/bin/env python3
"""
CLI Deployment Integration - ISS-0112 Claude PM Transformation

Integrates deployment enforcement and commands into the main CLI.
Ensures mandatory deployment validation for all operations.
"""

import sys
import asyncio
from pathlib import Path
from functools import wraps

import click
from rich.console import Console

from .core.deployment_enforcement import (
    require_deployment, 
    require_deployment_async,
    validate_deployment_for_cli,
    deployment_status_summary,
    get_deployment_enforcer
)
from .cli.deployment_commands import register_deployment_commands
from .core.logging_config import get_logger

logger = get_logger(__name__)
console = Console()


def add_deployment_enforcement_to_cli(cli_group):
    """
    Add deployment enforcement to existing CLI commands.
    
    This function wraps existing CLI commands with deployment validation
    to ensure framework is properly deployed before operations proceed.
    """
    
    # Commands that should skip deployment checking (deployment-related commands)
    SKIP_DEPLOYMENT_CHECK = {
        'deploy', 'verify', 'status', 'diagnose', 'list', 'undeploy',
        'version', 'help', 'util', 'agents', 'monitoring', 'service',
        'project-index', 'analytics', 'workflow', 'tickets',
        'init'  # Skip deployment check for init - it's the command that sets up deployment
    }
    
    # Wrap all existing commands with deployment enforcement
    original_commands = {}
    
    for name, command in cli_group.commands.items():
        if name not in SKIP_DEPLOYMENT_CHECK:
            original_commands[name] = command
            
            # Create wrapped command with deployment enforcement
            wrapped_command = _create_deployment_enforced_command(command, name)
            cli_group.commands[name] = wrapped_command
    
    logger.debug(f"Added deployment enforcement to {len(original_commands)} CLI commands")


def _create_deployment_enforced_command(original_command, command_name):
    """Create a deployment-enforced version of a CLI command."""
    
    # Create a wrapper function that preserves the original command's signature
    def create_wrapper():
        # Get the original callback function
        original_callback = original_command.callback
        
        @click.pass_context
        def enforced_wrapper(ctx, *args, **kwargs):
            """Wrapper that enforces deployment before execution."""
            
            async def run_with_enforcement():
                try:
                    # Validate deployment requirement
                    enforcer = get_deployment_enforcer()
                    await enforcer.enforce_deployment_requirement(
                        working_directory=Path.cwd(),
                        operation_name=command_name
                    )
                    
                    # If validation passes, execute original command through context
                    return ctx.invoke(original_callback, *args, **kwargs)
                    
                except Exception as e:
                    logger.error(f"Deployment enforcement failed for {command_name}: {e}")
                    console.print(f"❌ [red]Cannot execute '{command_name}': {e}[/red]")
                    sys.exit(1)
            
            # Handle both sync and async commands
            if asyncio.iscoroutinefunction(original_callback):
                return asyncio.run(run_with_enforcement())
            else:
                return asyncio.run(run_with_enforcement())
        
        return enforced_wrapper
    
    # Create the wrapper function
    wrapper_function = create_wrapper()
    
    # Create a new command with the same parameters and attributes
    # Only include parameters that exist in the Click version being used
    command_kwargs = {
        'name': command_name,
        'callback': wrapper_function,
        'params': original_command.params.copy(),  # Properly copy parameters
        'help': original_command.help,
    }
    
    # Conditionally add attributes that might exist
    for attr in ['epilog', 'short_help', 'options_metavar', 'add_help_option', 'context_settings']:
        if hasattr(original_command, attr):
            command_kwargs[attr] = getattr(original_command, attr)
    
    enforced_command = click.Command(**command_kwargs)
    
    return enforced_command


def enhance_cli_with_deployment_features(cli_group):
    """
    Enhance CLI with comprehensive deployment features.
    
    This adds:
    1. Deployment enforcement to existing commands
    2. New deployment management commands
    3. Startup deployment status display
    """
    
    # Add deployment commands
    register_deployment_commands(cli_group)
    
    # Add deployment enforcement to existing commands
    add_deployment_enforcement_to_cli(cli_group)
    
    # Enhance CLI startup with deployment status
    _enhance_cli_startup_with_deployment_status(cli_group)
    
    logger.info("CLI enhanced with comprehensive deployment features")


def _enhance_cli_startup_with_deployment_status(cli_group):
    """Enhance CLI startup to show deployment status."""
    
    # Store original callback
    original_callback = cli_group.callback
    
    @click.pass_context
    def enhanced_callback(ctx, **kwargs):
        """Enhanced CLI callback with deployment status."""
        
        # Display deployment status on startup
        _display_startup_deployment_status()
        
        # Call original callback with proper context handling
        if original_callback:
            # The original callback has @click.pass_context decorator,
            # so it expects to get the context automatically injected.
            # We need to call it through Click's context invoke mechanism.
            return ctx.invoke(original_callback, **kwargs)
    
    # Replace CLI callback
    cli_group.callback = enhanced_callback


def _display_startup_deployment_status():
    """Display deployment status during CLI startup."""
    try:
        status_summary = deployment_status_summary()
        
        # Only show if there are issues (don't clutter successful setups)
        if "❌" in status_summary:
            console.print(f"\n📊 Deployment Status: {status_summary}")
            console.print("💡 Run '[cyan]claude-pm deploy[/cyan]' if deployment issues are detected")
            console.print()
    except Exception as e:
        logger.debug(f"Failed to display startup deployment status: {e}")


# Deployment-aware command decorators for new commands

def deployment_required_command(name=None, **attrs):
    """
    Command decorator that requires valid deployment.
    
    Use this for new CLI commands that need deployment validation.
    """
    def decorator(f):
        # Add deployment requirement decorator
        f = require_deployment(operation_name=name or f.__name__)(f)
        
        # Add click command decorator
        return click.command(name=name, **attrs)(f)
    
    return decorator


def deployment_required_group(name=None, **attrs):
    """
    Group decorator that requires valid deployment for all subcommands.
    
    Use this for new CLI command groups that need deployment validation.
    """
    def decorator(f):
        # Create click group
        group = click.group(name=name, **attrs)(f)
        
        # Add deployment enforcement to group callback
        original_callback = group.callback
        
        @click.pass_context
        def enforced_callback(ctx, *args, **kwargs):
            # Validate deployment before group execution
            asyncio.run(validate_deployment_for_cli())
            
            # Execute original callback
            if original_callback:
                return original_callback(ctx, *args, **kwargs)
        
        group.callback = enforced_callback
        return group
    
    return decorator


# Utility functions for deployment integration

async def check_deployment_before_operation(operation_name: str) -> bool:
    """
    Check deployment status before an operation.
    
    Args:
        operation_name: Name of operation being performed
        
    Returns:
        True if deployment is valid, False otherwise
    """
    try:
        enforcer = get_deployment_enforcer()
        await enforcer.enforce_deployment_requirement(
            working_directory=Path.cwd(),
            operation_name=operation_name
        )
        return True
    except Exception as e:
        logger.error(f"Deployment check failed for {operation_name}: {e}")
        return False


def display_deployment_guidance():
    """Display deployment guidance for users."""
    console.print()
    console.print("🚀 [bold blue]Claude PM Framework Deployment Required[/bold blue]")
    console.print()
    console.print("To use Claude PM commands, you need to deploy the framework:")
    console.print()
    console.print("1. 📦 Install via NPM:")
    console.print("   [cyan]npm install -g @bobmatnyc/claude-multiagent-pm[/cyan]")
    console.print()
    console.print("2. 🔧 Deploy to working directory:")
    console.print("   [cyan]claude-pm deploy[/cyan]")
    console.print()
    console.print("3. ✅ Verify deployment:")
    console.print("   [cyan]claude-pm verify[/cyan]")
    console.print()
    console.print("🆘 Need help? Run '[cyan]claude-pm diagnose[/cyan]' for detailed guidance")
    console.print()


def get_deployment_status_for_display() -> dict:
    """Get deployment status formatted for CLI display."""
    try:
        enforcer = get_deployment_enforcer()
        return asyncio.run(enforcer.check_deployment_status())
    except Exception as e:
        logger.error(f"Failed to get deployment status: {e}")
        return {
            'valid': False,
            'error': str(e)
        }


# Integration helpers for existing CLI code

def ensure_deployment_validated():
    """
    Ensure deployment is validated before proceeding.
    
    Call this function at the start of critical operations that require
    framework deployment.
    """
    try:
        asyncio.run(validate_deployment_for_cli())
    except SystemExit:
        # Re-raise system exit from deployment validation
        raise
    except Exception as e:
        logger.error(f"Deployment validation failed: {e}")
        console.print(f"❌ [red]Deployment validation failed: {e}[/red]")
        sys.exit(1)


def deployment_status_check_command():
    """Quick deployment status check command for troubleshooting."""
    
    @click.command(name='deployment-status')
    def deployment_status():
        """Show current deployment status."""
        status = get_deployment_status_for_display()
        
        if status.get('valid'):
            console.print("✅ [green]Framework deployment is valid[/green]")
        else:
            console.print("❌ [red]Framework deployment issues detected[/red]")
            if status.get('error'):
                console.print(f"   Error: {status['error']}")
        
        console.print(f"\n📊 Status Summary: {deployment_status_summary()}")
    
    return deployment_status


# Export integration function for main CLI
def integrate_deployment_system(cli_group):
    """
    Main integration function to add deployment system to CLI.
    
    Call this from the main CLI setup to enable all deployment features.
    """
    enhance_cli_with_deployment_features(cli_group)
    
    # Add quick status command
    cli_group.add_command(deployment_status_check_command())
    
    logger.info("Deployment system fully integrated into CLI")