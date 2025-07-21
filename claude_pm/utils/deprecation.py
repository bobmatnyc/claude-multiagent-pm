"""
Deprecation warnings and migration helpers for Claude PM Framework.
"""

import os
import warnings
from pathlib import Path
import sys

def check_editable_installation():
    """Check if the current installation is editable and issue deprecation warnings."""
    # Check if we're running from source directory
    module_path = Path(__file__).parent.parent
    source_indicators = [
        module_path / ".git",
        module_path / "setup.py",
        module_path / "pyproject.toml"
    ]
    
    is_editable = any(indicator.exists() for indicator in source_indicators)
    
    # Also check if we're in a known development path
    known_dev_paths = [
        Path.home() / "Projects" / "claude-multiagent-pm",
        Path("/Users/masa/Projects/claude-multiagent-pm")
    ]
    
    is_dev_path = any(str(module_path).startswith(str(dev_path)) for dev_path in known_dev_paths)
    
    # Check environment variable to suppress warning
    suppress_warning = os.environ.get("CLAUDE_PM_SOURCE_MODE") == "deprecated"
    
    if (is_editable or is_dev_path) and not suppress_warning:
        warnings.warn(
            "\n"
            "=" * 70 + "\n"
            "DEPRECATION WARNING: Editable installation detected\n"
            "=" * 70 + "\n"
            "You are running Claude PM from a source directory installation.\n"
            "This installation method is deprecated and will be removed in v2.0.\n"
            "\n"
            "Please migrate to PyPI installation:\n"
            "  1. Run: python scripts/migrate_to_pypi.py\n"
            "  2. Or manually: pip uninstall claude-multiagent-pm && pip install claude-multiagent-pm\n"
            "\n"
            "To suppress this warning temporarily:\n"
            "  export CLAUDE_PM_SOURCE_MODE=deprecated\n"
            "\n"
            "For more information:\n"
            "  https://github.com/bobmatnyc/claude-multiagent-pm/blob/main/docs/MIGRATION.md\n"
            "=" * 70,
            DeprecationWarning,
            stacklevel=2
        )
        
        # Also print to stderr for visibility
        if sys.stderr.isatty():  # Only if connected to terminal
            print("\033[33m" + "⚠️  DEPRECATION: Running from editable installation" + "\033[0m", file=sys.stderr)

def ensure_pypi_installation():
    """Helper to guide users to PyPI installation."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "claude-multiagent-pm"],
            capture_output=True,
            text=True
        )
        
        if "Editable project location" in result.stdout:
            return False, "editable"
        elif result.returncode == 0:
            return True, "pypi"
        else:
            return False, "none"
    except Exception:
        return False, "error"

# Don't automatically check on module import - let it be called explicitly