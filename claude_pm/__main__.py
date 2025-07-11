#!/usr/bin/env python3
"""
Claude PM Framework - Module Entry Point
========================================

Entry point for running the Claude PM Framework commands via 'python -m claude_pm'.
This module provides access to the CMPM command suite.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for module imports
framework_path = Path(__file__).parent.parent
sys.path.insert(0, str(framework_path))

# Import and run the main CLI
try:
    from .cmpm_commands import main

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Error importing CMPM commands: {e}")
    print("Please ensure you're running this from the Claude PM Framework directory")
    sys.exit(1)
