#!/usr/bin/env python3
"""
Main entry point for claude_pm.cli module.

This enables `python -m claude_pm.cli` execution.
"""

import sys
from .cli_utils import _display_directory_context
from . import create_modular_cli


def main():
    """Main entry point for CLI module execution."""
    # Display directory context on startup
    _display_directory_context()
    
    # Create and run the modular CLI
    cli = create_modular_cli()
    
    # Execute with passed arguments
    cli()


if __name__ == "__main__":
    main()