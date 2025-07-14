#!/usr/bin/env python3
"""
Claude Multi-Agent Project Management Framework - Modular CLI Entry Point

Streamlined main CLI file using modular command system.
Part of ISS-0114 modularization initiative - reduced from 4,146 lines to <500 lines.
"""

import asyncio
import sys
import logging
from pathlib import Path

from rich.console import Console

# Import the modular CLI system
from .cli import create_modular_cli

console = Console()
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point with modular command loading."""
    try:
        # Create the modular CLI with all commands loaded
        cli = create_modular_cli()
        
        # Execute the CLI
        cli()
        
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Operation cancelled by user[/bold yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        logger.error(f"CLI execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()