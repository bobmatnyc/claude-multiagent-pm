"""
CMPM Commands Module
==================

Central command registration and management for the Claude PM Framework.
This module provides the main CLI entry point and registers all CMPM commands
from their respective component modules.
"""

import click
from rich.console import Console

try:
    from .health_commands import cmpm_health
except ImportError:
    cmpm_health = None

try:
    from .agent_commands import cmpm_agents, cmpm_index
except ImportError:
    cmpm_agents = None
    cmpm_index = None

try:
    from .qa_commands import cmpm_qa_status, cmpm_qa_test, cmpm_qa_results
except ImportError:
    cmpm_qa_status = None
    cmpm_qa_test = None
    cmpm_qa_results = None

try:
    from .integration_commands import cmpm_integration, cmpm_ai_ops
except ImportError:
    cmpm_integration = None
    cmpm_ai_ops = None

try:
    from .dashboard_commands import cmpm_dashboard
except ImportError:
    cmpm_dashboard = None

try:
    from .template_commands import template
except ImportError:
    template = None

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """CMPM Framework Commands - Main CLI Entry Point."""
    if ctx.invoked_subcommand is None:
        console.print(
            """
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
        """
        )


# Register all commands to the main group (only if they exist)
if cmpm_health:
    main.add_command(cmpm_health)
if cmpm_agents:
    main.add_command(cmpm_agents)
if cmpm_index:
    main.add_command(cmpm_index)
if cmpm_dashboard:
    main.add_command(cmpm_dashboard)
if cmpm_qa_status:
    main.add_command(cmpm_qa_status)
if cmpm_qa_test:
    main.add_command(cmpm_qa_test)
if cmpm_qa_results:
    main.add_command(cmpm_qa_results)
if cmpm_integration:
    main.add_command(cmpm_integration)
if cmpm_ai_ops:
    main.add_command(cmpm_ai_ops)
if template:
    main.add_command(template)


__all__ = [
    "main",
]

# Add available commands to __all__
if cmpm_health:
    __all__.append("cmpm_health")
if cmpm_agents:
    __all__.extend(["cmpm_agents", "cmpm_index"])
if cmpm_qa_status:
    __all__.extend(["cmpm_qa_status", "cmpm_qa_test", "cmpm_qa_results"])
if cmpm_integration:
    __all__.extend(["cmpm_integration", "cmpm_ai_ops"])
if cmpm_dashboard:
    __all__.append("cmpm_dashboard")
if template:
    __all__.append("template")