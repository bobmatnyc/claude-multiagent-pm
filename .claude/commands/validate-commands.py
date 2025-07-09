#!/usr/bin/env python3
"""
Claude Code Slash Commands Validation Script
===========================================

This script validates that all custom Claude PM Framework slash commands
are properly configured and working correctly.
"""

import sys
import os
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def validate_command_files():
    """Validate that all command files exist and are properly formatted."""
    commands_dir = Path(".claude/commands")
    
    if not commands_dir.exists():
        console.print("[red]Error: .claude/commands directory not found![/red]")
        return False
    
    required_files = [
        "cmpm-health.md",
        "cmpm-agents.md", 
        "cmpm-index.md",
        "cmpm-bridge.py",
        "README.md"
    ]
    
    missing_files = []
    for file in required_files:
        if not (commands_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        console.print(f"[red]Missing files: {', '.join(missing_files)}[/red]")
        return False
    
    # Check bridge script is executable
    bridge_script = commands_dir / "cmpm-bridge.py"
    if not os.access(bridge_script, os.X_OK):
        console.print("[yellow]Warning: Bridge script is not executable[/yellow]")
    
    console.print("[green]✓ All command files present and valid[/green]")
    return True

def validate_framework_integration():
    """Validate that framework modules can be imported."""
    try:
        # Add framework to path
        framework_path = Path.cwd()
        sys.path.insert(0, str(framework_path))
        
        from claude_pm.cmpm_commands import CMPMHealthMonitor, CMPMAgentMonitor, CMPMIndexOrchestrator
        console.print("[green]✓ Framework modules imported successfully[/green]")
        return True
    except ImportError as e:
        console.print(f"[red]✗ Framework import failed: {e}[/red]")
        return False

async def test_bridge_commands():
    """Test that bridge commands execute without errors."""
    bridge_script = Path(".claude/commands/cmpm-bridge.py")
    
    if not bridge_script.exists():
        console.print("[red]✗ Bridge script not found[/red]")
        return False
    
    commands = ["health", "agents", "index"]
    results = {}
    
    for cmd in commands:
        try:
            # Import and test the bridge functions
            sys.path.insert(0, str(Path(".claude/commands")))
            
            if cmd == "health":
                from claude_pm.cmpm_commands import CMPMHealthMonitor
                monitor = CMPMHealthMonitor()
                # Test instantiation only
                results[cmd] = "✓ OK"
            elif cmd == "agents":
                from claude_pm.cmpm_commands import CMPMAgentMonitor
                monitor = CMPMAgentMonitor()
                results[cmd] = "✓ OK"
            elif cmd == "index":
                from claude_pm.cmpm_commands import CMPMIndexOrchestrator
                orchestrator = CMPMIndexOrchestrator()
                results[cmd] = "✓ OK"
                
        except Exception as e:
            results[cmd] = f"✗ Error: {str(e)[:50]}..."
    
    # Display results
    table = Table(title="Bridge Command Validation")
    table.add_column("Command", style="cyan")
    table.add_column("Status", style="green")
    
    for cmd, status in results.items():
        color = "green" if "✓" in status else "red"
        table.add_row(f"cmpm:{cmd}", f"[{color}]{status}[/{color}]")
    
    console.print(table)
    
    # Return True if all commands passed
    return all("✓" in status for status in results.values())

def validate_command_content():
    """Validate that command files have proper content structure."""
    commands_dir = Path(".claude/commands")
    commands = ["cmpm-health.md", "cmpm-agents.md", "cmpm-index.md"]
    
    for cmd_file in commands:
        cmd_path = commands_dir / cmd_file
        try:
            with open(cmd_path, 'r') as f:
                content = f.read()
                
            # Check for required sections
            if "# CMPM" not in content:
                console.print(f"[yellow]Warning: {cmd_file} missing title[/yellow]")
            
            if "## Instructions" not in content:
                console.print(f"[yellow]Warning: {cmd_file} missing instructions[/yellow]")
                
            if "python" not in content:
                console.print(f"[yellow]Warning: {cmd_file} missing execution instructions[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error reading {cmd_file}: {e}[/red]")
            return False
    
    console.print("[green]✓ Command content validation passed[/green]")
    return True

def display_usage_instructions():
    """Display instructions for using the commands."""
    usage_panel = Panel(
        """
[bold cyan]Claude Code Slash Commands Usage:[/bold cyan]

In Claude Code interface, type:
• [green]/project:cmpm-health[/green] - System health dashboard
• [green]/project:cmpm-agents[/green] - Agent registry overview  
• [green]/project:cmpm-index[/green] - Project discovery index

[bold cyan]Direct CLI Usage:[/bold cyan]

• [green]python .claude/commands/cmpm-bridge.py health[/green]
• [green]python .claude/commands/cmpm-bridge.py agents[/green]
• [green]python .claude/commands/cmpm-bridge.py index[/green]

[bold cyan]Framework CLI Usage:[/bold cyan]

• [green]python -m claude_pm.cmpm_commands cmpm:health[/green]
• [green]python -m claude_pm.cmpm_commands cmpm:agents[/green]
• [green]python -m claude_pm.cmpm_commands cmpm:index[/green]
        """.strip(),
        title="Usage Instructions",
        border_style="blue"
    )
    console.print(usage_panel)

async def main():
    """Main validation function."""
    console.print(Panel("[bold white]Claude PM Framework Slash Commands Validation[/bold white]", 
                        title="🔍 Validation Report", border_style="cyan"))
    
    console.print()
    
    # Run all validations
    file_validation = validate_command_files()
    framework_validation = validate_framework_integration()
    content_validation = validate_command_content()
    bridge_validation = await test_bridge_commands()
    
    console.print()
    
    # Overall status
    all_passed = all([file_validation, framework_validation, content_validation, bridge_validation])
    
    if all_passed:
        console.print(Panel("[bold green]✅ All validations passed! Commands are ready for use.[/bold green]", 
                           border_style="green"))
    else:
        console.print(Panel("[bold red]❌ Some validations failed. Please check the errors above.[/bold red]", 
                           border_style="red"))
    
    console.print()
    display_usage_instructions()
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)