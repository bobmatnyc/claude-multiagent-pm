"""Synchronous wrappers for async methods."""

import asyncio
import concurrent.futures
from typing import Dict, List, Optional, Any

from .models import AgentMetadata


class SyncWrapper:
    """Provides synchronous wrappers for async agent registry methods."""
    
    @staticmethod
    def run_async(coro):
        """
        Run an async coroutine synchronously.
        
        Args:
            coro: Coroutine to run
            
        Returns:
            Result of the coroutine
        """
        loop = None
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an async context, we can't use run_until_complete
            # Create a new thread to run the async method
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            # No event loop running, we can create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
                asyncio.set_event_loop(None)
    
    @classmethod
    def list_agents_sync(cls, registry, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """
        Synchronous wrapper for list_agents method.
        
        Args:
            registry: AgentRegistry instance
            agent_type: Filter by agent type
            tier: Filter by hierarchy tier
            
        Returns:
            List of matching AgentMetadata
        """
        return cls.run_async(registry.list_agents(agent_type=agent_type, tier=tier))
    
    @classmethod
    def discover_agents_sync(cls, registry, force_refresh: bool = False) -> Dict[str, AgentMetadata]:
        """
        Synchronous wrapper for discover_agents method.
        
        Args:
            registry: AgentRegistry instance
            force_refresh: Force cache refresh even if within TTL
            
        Returns:
            Dictionary of agent name -> AgentMetadata
        """
        return cls.run_async(registry.discover_agents(force_refresh=force_refresh))
    
    @classmethod
    def get_agent_sync(cls, registry, agent_name: str) -> Optional[AgentMetadata]:
        """
        Synchronous wrapper for get_agent method.
        
        Args:
            registry: AgentRegistry instance
            agent_name: Name of agent to retrieve
            
        Returns:
            AgentMetadata or None if not found
        """
        return cls.run_async(registry.get_agent(agent_name))
    
    @classmethod
    def get_registry_stats_sync(cls, registry) -> Dict[str, Any]:
        """
        Synchronous wrapper for get_registry_stats method.
        
        Args:
            registry: AgentRegistry instance
            
        Returns:
            Dictionary of registry statistics
        """
        return cls.run_async(registry.get_registry_stats())