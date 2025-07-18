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
__all__ = [
    'AgentRegistry', 
    'AgentMetadata',
    'create_agent_registry',
    'discover_agents_async',
    'get_core_agent_types',
    'get_specialized_agent_types',
    'listAgents',
    'list_agents',
    'discover_agents_sync',
    'get_agent',
    'get_registry_stats'
]

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

# Add convenience method for synchronous access with camelCase naming
def listAgents():
    """
    Synchronous wrapper for listing all agents (camelCase compatibility)
    
    This provides a non-async interface for simple agent listing operations
    that matches the camelCase naming convention in CLAUDE.md documentation.
    
    Returns:
        Dictionary of agent name -> agent metadata
    """
    registry = AgentRegistry()
    agents = registry.discover_agents_sync()
    return {name: {
        'type': metadata.type,
        'path': metadata.path,
        'tier': metadata.tier,
        'last_modified': metadata.last_modified,
        'specializations': metadata.specializations
    } for name, metadata in agents.items()}

# Add synchronous convenience functions
def list_agents(agent_type=None, tier=None):
    """
    Synchronous function to list agents with optional filtering
    
    Args:
        agent_type: Filter by agent type
        tier: Filter by hierarchy tier
        
    Returns:
        List of agent metadata dictionaries
    """
    registry = AgentRegistry()
    agents = registry.list_agents_sync(agent_type=agent_type, tier=tier)
    return [{
        'name': agent.name,
        'type': agent.type,
        'path': agent.path,
        'tier': agent.tier,
        'last_modified': agent.last_modified,
        'specializations': agent.specializations,
        'description': agent.description
    } for agent in agents]

def discover_agents_sync(force_refresh=False):
    """
    Synchronous function for agent discovery
    
    Args:
        force_refresh: Force cache refresh
        
    Returns:
        Dictionary of discovered agents
    """
    registry = AgentRegistry()
    return registry.discover_agents_sync(force_refresh=force_refresh)

def get_agent(agent_name):
    """
    Synchronous function to get a specific agent
    
    Args:
        agent_name: Name of agent to retrieve
        
    Returns:
        Agent metadata or None
    """
    registry = AgentRegistry()
    agent = registry.get_agent_sync(agent_name)
    if agent:
        return {
            'name': agent.name,
            'type': agent.type,
            'path': agent.path,
            'tier': agent.tier,
            'last_modified': agent.last_modified,
            'specializations': agent.specializations,
            'description': agent.description
        }
    return None

def get_registry_stats():
    """
    Synchronous function to get registry statistics
    
    Returns:
        Dictionary of registry statistics
    """
    registry = AgentRegistry()
    return registry.get_registry_stats_sync()