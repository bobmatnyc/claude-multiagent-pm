#!/usr/bin/env python3
"""
CMPM (Claude Multi-Agent PM) Slash Commands - Modular Architecture
===================================================================

This module provides the main entry point for CMPM slash commands, now organized
into focused component modules for better maintainability and separation of concerns.

Commands are organized into these modules:
- health_commands.py: Health monitoring and integration management
- agent_commands.py: Agent management and project indexing
- qa_commands.py: QA testing and validation
- integration_commands.py: AI operations and provider management
- dashboard_commands.py: Dashboard launching and management

All commands maintain backward compatibility and continue to work with the existing
CLI interface: python -m claude_pm.cmpm_commands [command]
"""

import click
from rich.console import Console

# Import all commands from the modular architecture
from .commands import (
    main,
    cmpm_health,
    cmpm_agents,
    cmpm_index,
    cmpm_dashboard,
    cmpm_qa_status,
    cmpm_qa_test,
    cmpm_qa_results,
    cmpm_integration,
    cmpm_ai_ops
)

console = Console()


# Register commands for CLI integration (backward compatibility)
def register_cmpm_commands(cli_group):
    """Register CMPM commands with the main CLI group."""
    cli_group.add_command(cmpm_health)
    cli_group.add_command(cmpm_agents)
    cli_group.add_command(cmpm_index)
    cli_group.add_command(cmpm_dashboard)
    cli_group.add_command(cmpm_qa_status)
    cli_group.add_command(cmpm_qa_test)
    cli_group.add_command(cmpm_qa_results)
    cli_group.add_command(cmpm_integration)
    cli_group.add_command(cmpm_ai_ops)


# Export the main function for direct module execution
__all__ = [
    'main',
    'register_cmpm_commands',
    'cmpm_health',
    'cmpm_agents',
    'cmpm_index',
    'cmpm_dashboard',
    'cmpm_qa_status',
    'cmpm_qa_test',
    'cmpm_qa_results',
    'cmpm_integration',
    'cmpm_ai_ops'
]


# Main entry point for direct module execution
if __name__ == "__main__":
    # Use the main function from the commands module
    main()