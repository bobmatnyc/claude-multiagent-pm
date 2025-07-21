"""
Service-level Agent Registry Module - Wrapper for synchronous implementation

This module provides a simple wrapper around agent_registry_sync.py to maintain
backward compatibility for code that imports from claude_pm.services.agent_registry.

The async implementation has been removed as per EP-0043 refactoring guidelines.
All functionality is now provided by the synchronous implementation.

Created: 2025-07-19 (EP-0043 Refactoring)
Purpose: Maintain backward compatibility while using only sync implementation
"""

# Import everything from the synchronous implementation
from .agent_registry_sync import (
    AgentRegistry,
    AgentMetadata,
)

# Export the same public interface
__all__ = ['AgentRegistry', 'AgentMetadata']