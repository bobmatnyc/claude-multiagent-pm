"""
Backward compatibility stub for evaluation_performance module.

This module has been refactored into a directory-based structure.
All imports should continue to work as before.
"""

# Import all public API from the new module structure
from claude_pm.services.evaluation_performance import *  # noqa: F401, F403

# Maintain backward compatibility
import warnings

warnings.warn(
    "Importing from 'claude_pm.services.evaluation_performance' as a file is deprecated. "
    "Please import from 'claude_pm.services.evaluation_performance' package instead.",
    DeprecationWarning,
    stacklevel=2
)