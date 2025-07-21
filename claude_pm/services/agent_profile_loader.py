"""
Backward compatibility stub for agent_profile_loader module.

This module has been refactored into a directory-based structure for better organization.
All original functionality is preserved through this compatibility layer.
"""

# Import all public APIs from the new module structure
from claude_pm.services.agent_profile_loader import *

# Preserve backward compatibility
logger.warning("Using backward compatibility import for agent_profile_loader. "
               "Please update imports to use 'from claude_pm.services.agent_profile_loader import ...'")