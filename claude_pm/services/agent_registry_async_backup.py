"""
Backward compatibility stub for agent_registry_async_backup module.

This file maintains backward compatibility after refactoring to a directory-based structure.
All functionality has been moved to the agent_registry_async_backup/ directory.
"""

# Import all public APIs from the new module structure
from claude_pm.services.agent_registry_async_backup import *
from claude_pm.services.agent_registry_async_backup.models import AgentMetadata

# Ensure backward compatibility by exposing all previously available names
__all__ = ['AgentRegistry', 'AgentMetadata']