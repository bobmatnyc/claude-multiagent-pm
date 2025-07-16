"""
Core Agent Registry Module - Core framework exposure of agent registry functionality

This module exposes the AgentRegistry from services to the core framework layer,
providing the expected interface for core framework operations.

Created: 2025-07-16 (Emergency restoration)
Purpose: Restore missing claude_pm.core.agent_registry import
"""

# Import AgentRegistry from services and expose it at core level
from claude_pm.services.agent_registry import AgentRegistry, AgentMetadata

# Expose key classes and functions for core framework access
__all__ = ['AgentRegistry', 'AgentMetadata']

# Create convenience aliases for common operations
def create_agent_registry(cache_service=None):
    """
    Create a new AgentRegistry instance
    
    Args:
        cache_service: Optional cache service for performance optimization
        
    Returns:
        AgentRegistry instance
    """
    return AgentRegistry(cache_service=cache_service)

async def discover_agents_async(force_refresh=False):
    """
    Convenience function for async agent discovery
    
    Args:
        force_refresh: Force cache refresh
        
    Returns:
        Dictionary of discovered agents
    """
    registry = AgentRegistry()
    return await registry.discover_agents(force_refresh=force_refresh)

def get_core_agent_types():
    """
    Get the set of core agent types
    
    Returns:
        Set of core agent type names
    """
    registry = AgentRegistry()
    return registry.core_agent_types

def get_specialized_agent_types():
    """
    Get the set of specialized agent types beyond core 9
    
    Returns:
        Set of specialized agent type names
    """
    registry = AgentRegistry()
    return registry.specialized_agent_types