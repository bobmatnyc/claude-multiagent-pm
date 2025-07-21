"""
Agent Registry Service - Backward Compatibility Wrapper
This module now imports from the modularized agent_registry package

Created: 2025-07-18
Refactored: 2025-07-19 - Split into modular components
Purpose: Maintain backward compatibility for existing imports
"""

# Import everything from the new modular structure
from claude_pm.services.agent_registry import AgentRegistry, AgentMetadata

# Re-export for backward compatibility
__all__ = ['AgentRegistry', 'AgentMetadata']