"""
CMPM Commands Module
==================

Central command registration and management for the Claude PM Framework.
This module provides the main CLI entry point and registers all CMPM commands
from their respective component modules.
"""

import click
from rich.console import Console

from .health_commands import cmpm_health
from .agent_commands import cmpm_agents, cmpm_index
from .qa_commands import cmpm_qa_status, cmpm_qa_test, cmpm_qa_results
from .integration_commands import cmpm_integration, cmpm_ai_ops
from .dashboard_commands import cmpm_dashboard
from .template_commands import template

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """CMPM Framework Commands - Main CLI Entry Point."""
    if ctx.invoked_subcommand is None:
        console.print("""
[bold cyan]CMPM Framework Commands[/bold cyan]

Available commands:
• [green]cmpm:health[/green] - System health dashboard
• [green]cmpm:agents[/green] - Agent registry overview
• [green]cmpm:index[/green] - Project discovery index
• [green]cmpm:dashboard[/green] - Portfolio manager dashboard
• [green]cmpm:qa-status[/green] - QA extension status and health
• [green]cmpm:qa-test[/green] - Execute browser-based tests
• [green]cmpm:qa-results[/green] - View test results and patterns
• [green]cmpm:integration[/green] - Integration management
• [green]cmpm:ai-ops[/green] - AI operations management
• [green]template[/green] - Template management with versioning

Usage:
• [dim]python -m claude_pm.cmpm_commands cmpm:health[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:agents[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:index[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:dashboard[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:qa-status[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:qa-test --browser[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:qa-results[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:integration[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:ai-ops[/dim]
• [dim]python -m claude_pm.cmpm_commands template deploy-claude-md[/dim]
        """)


# Register all commands to the main group
main.add_command(cmpm_health)
main.add_command(cmpm_agents)
main.add_command(cmpm_index)
main.add_command(cmpm_dashboard)
main.add_command(cmpm_qa_status)
main.add_command(cmpm_qa_test)
main.add_command(cmpm_qa_results)
main.add_command(cmpm_integration)
main.add_command(cmpm_ai_ops)
main.add_command(template)


__all__ = [
    'main',
    'cmpm_health',
    'cmpm_agents',
    'cmpm_index',
    'cmpm_dashboard',
    'cmpm_qa_status',
    'cmpm_qa_test',
    'cmpm_qa_results',
    'cmpm_integration',
    'cmpm_ai_ops',
    'template'
]