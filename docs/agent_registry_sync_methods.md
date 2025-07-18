# AgentRegistry Synchronous Methods

## Overview

The AgentRegistry now provides synchronous methods for agent discovery and listing, making it easier to use from synchronous contexts like CLI tools and the PM orchestrator.

## Added Synchronous Methods

### In `claude_pm.services.agent_registry.AgentRegistry`:

1. **`list_agents_sync(agent_type=None, tier=None)`**
   - Synchronous wrapper for the async `list_agents()` method
   - Returns a list of `AgentMetadata` objects
   - Supports filtering by agent type and tier

2. **`discover_agents_sync(force_refresh=False)`**
   - Synchronous wrapper for the async `discover_agents()` method
   - Returns a dictionary of agent name -> `AgentMetadata`
   - Supports force refresh of the cache

3. **`get_agent_sync(agent_name)`**
   - Synchronous wrapper for the async `get_agent()` method
   - Returns a single `AgentMetadata` object or None

4. **`get_registry_stats_sync()`**
   - Synchronous wrapper for the async `get_registry_stats()` method
   - Returns registry statistics dictionary

### In `claude_pm.core.agent_registry`:

1. **`listAgents()`** (camelCase for CLAUDE.md compatibility)
   - Returns a dictionary of agent name -> metadata dict
   - Automatically discovers all agents

2. **`list_agents(agent_type=None, tier=None)`**
   - Returns a list of agent metadata dictionaries
   - Supports filtering by type and tier

3. **`discover_agents_sync(force_refresh=False)`**
   - Returns full `AgentMetadata` objects
   - Direct wrapper around the service method

4. **`get_agent(agent_name)`**
   - Returns a single agent metadata dictionary
   - Returns None if agent not found

5. **`get_registry_stats()`**
   - Returns registry statistics
   - Direct wrapper around the service method

## Usage Examples

```python
# Using the core module functions
from claude_pm.core import agent_registry

# Get all agents (camelCase)
agents = agent_registry.listAgents()

# Get filtered agents
research_agents = agent_registry.list_agents(agent_type='research')

# Get specific agent
agent = agent_registry.get_agent('codebase_research_agent')

# Using the AgentRegistry class directly
from claude_pm.core.agent_registry import AgentRegistry
registry = AgentRegistry()

# Discover all agents
agents = registry.discover_agents_sync()

# Get filtered agents
research_agents = registry.list_agents_sync(agent_type='research')

# Get specific agent
agent = registry.get_agent_sync('codebase_research_agent')

# Check registry health
health = registry.health_check()
```

## Implementation Details

The synchronous methods handle event loop creation properly:
- If no event loop is running, they create a new one
- If an event loop is already running (async context), they use a thread pool to avoid conflicts
- They properly clean up event loops after use

This ensures the synchronous methods work correctly in all contexts:
- Command line scripts
- Interactive Python sessions
- Within async code
- In the PM orchestrator

## Backward Compatibility

All existing async methods remain unchanged and continue to work as before. The synchronous methods are additions that wrap the async methods, providing convenience for synchronous contexts.