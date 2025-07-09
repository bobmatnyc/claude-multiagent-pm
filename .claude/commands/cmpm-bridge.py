#!/usr/bin/env python3
"""
Claude Code Slash Commands Bridge Script
========================================

This script bridges Claude Code slash commands to the existing CMPM framework functionality.
It allows the custom slash commands to execute the framework's native command implementations.

Usage:
    python .claude/commands/cmpm-bridge.py health
    python .claude/commands/cmpm-bridge.py agents
    python .claude/commands/cmpm-bridge.py index
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the framework path to Python path
framework_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_path))

try:
    from claude_pm.cmpm_commands import CMPMHealthMonitor, CMPMAgentMonitor, CMPMIndexOrchestrator
    from rich.console import Console
except ImportError as e:
    print(f"Error importing CMPM modules: {e}")
    print("Please ensure you're running this from the Claude PM Framework directory")
    sys.exit(1)

console = Console()

async def run_health_command():
    """Execute the CMPM health dashboard."""
    try:
        monitor = CMPMHealthMonitor()
        await monitor.generate_health_dashboard()
    except Exception as e:
        console.print(f"[red]Health dashboard error: {e}[/red]")
        return False
    return True

async def run_agents_command():
    """Execute the CMPM agents registry."""
    try:
        monitor = CMPMAgentMonitor()
        await monitor.generate_agents_dashboard()
    except Exception as e:
        console.print(f"[red]Agents dashboard error: {e}[/red]")
        return False
    return True

async def run_index_command():
    """Execute the CMPM project index."""
    try:
        orchestrator = CMPMIndexOrchestrator()
        await orchestrator.generate_index_dashboard()
    except Exception as e:
        console.print(f"[red]Index dashboard error: {e}[/red]")
        return False
    return True

async def main():
    """Main bridge execution."""
    if len(sys.argv) < 2:
        console.print("[red]Usage: python cmpm-bridge.py <command>[/red]")
        console.print("Available commands: health, agents, index")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "health":
        success = await run_health_command()
    elif command == "agents":
        success = await run_agents_command()
    elif command == "index":
        success = await run_index_command()
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("Available commands: health, agents, index")
        sys.exit(1)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())