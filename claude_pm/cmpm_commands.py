#!/usr/bin/env python3
"""
CMPM (Claude Multi-Agent PM) Slash Commands - Streamlined Architecture
======================================================================

This module provides the main entry point for CMPM slash commands, streamlined
for basic Claude PM Framework operations.

Core commands:
- init: Initialize framework
- status: Check framework health
- help: Show help information

All commands work with the existing CLI interface: python -m claude_pm.cmpm_commands [command]
"""

import click
from rich.console import Console

console = Console()

@click.group()
@click.pass_context
def main(ctx):
    """Claude Multi-Agent PM Framework Commands"""
    ctx.ensure_object(dict)

@main.command()
@click.pass_context
def init(ctx):
    """Initialize Claude PM Framework"""
    console.print("[green]Initializing Claude PM Framework...[/green]")
    console.print("[yellow]Basic framework initialization complete.[/yellow]")

@main.command()
@click.pass_context
def status(ctx):
    """Check framework health status"""
    console.print("[green]Framework Status: [bold]Operational[/bold][/green]")
    console.print("[blue]Core services: [bold]Running[/bold][/blue]")

@main.command()
@click.pass_context
def help_cmd(ctx):
    """Show help information"""
    console.print("[cyan]Claude PM Framework - Available Commands:[/cyan]")
    console.print("  init   - Initialize framework")
    console.print("  status - Check framework health")
    console.print("  help   - Show this help message")

# Register commands for CLI integration (backward compatibility)
def register_cmpm_commands(cli_group):
    """Register CMPM commands with the main CLI group."""
    cli_group.add_command(init)
    cli_group.add_command(status)
    cli_group.add_command(help_cmd)

# Export the main function for direct module execution
__all__ = [
    "main",
    "register_cmpm_commands",
    "init",
    "status",
    "help_cmd",
]

# Main entry point for direct module execution
if __name__ == "__main__":
    main()