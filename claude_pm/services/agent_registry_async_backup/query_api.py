"""Query API for agent search and filtering."""

import logging
from typing import Dict, List, Optional, Set, Any

from .models import AgentMetadata

logger = logging.getLogger(__name__)


class AgentQueryAPI:
    """Provides search and query methods for agent registry."""
    
    def __init__(self, registry: Dict[str, AgentMetadata]):
        """Initialize query API with agent registry."""
        self.registry = registry
    
    async def get_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """
        Get specific agent metadata.
        
        Args:
            agent_name: Name of agent to retrieve
            
        Returns:
            AgentMetadata or None if not found
        """
        return self.registry.get(agent_name)
    
    async def list_agents(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """
        List agents with optional filtering.
        
        Args:
            agent_type: Filter by agent type
            tier: Filter by hierarchy tier
            
        Returns:
            List of matching AgentMetadata
        """
        agents = list(self.registry.values())
        
        if agent_type:
            agents = [a for a in agents if a.type == agent_type]
        
        if tier:
            agents = [a for a in agents if a.tier == tier]
        
        return agents
    
    async def get_agent_types(self) -> Set[str]:
        """
        Get all discovered agent types.
        
        Returns:
            Set of agent types
        """
        return {metadata.type for metadata in self.registry.values()}
    
    async def get_specialized_agents(self, agent_type: str) -> List[AgentMetadata]:
        """
        Get all agents of a specific specialized type.
        
        Args:
            agent_type: Specialized agent type to search for
            
        Returns:
            List of matching specialized agents
        """
        specialized_agents = []
        for metadata in self.registry.values():
            if (metadata.type == agent_type or 
                agent_type in metadata.specializations or
                agent_type in metadata.hybrid_types):
                specialized_agents.append(metadata)
        
        return sorted(specialized_agents, key=lambda x: x.validation_score, reverse=True)
    
    async def get_agents_by_framework(self, framework: str) -> List[AgentMetadata]:
        """
        Get agents that use a specific framework.
        
        Args:
            framework: Framework name to search for
            
        Returns:
            List of agents using the framework
        """
        return [metadata for metadata in self.registry.values() 
                if framework.lower() in [f.lower() for f in metadata.frameworks]]
    
    async def get_agents_by_domain(self, domain: str) -> List[AgentMetadata]:
        """
        Get agents specialized in a specific domain.
        
        Args:
            domain: Domain name to search for
            
        Returns:
            List of domain-specialized agents
        """
        return [metadata for metadata in self.registry.values() 
                if domain.lower() in [d.lower() for d in metadata.domains]]
    
    async def get_agents_by_role(self, role: str) -> List[AgentMetadata]:
        """
        Get agents with a specific role.
        
        Args:
            role: Role name to search for
            
        Returns:
            List of agents with the role
        """
        return [metadata for metadata in self.registry.values() 
                if role.lower() in [r.lower() for r in metadata.roles]]
    
    async def get_hybrid_agents(self) -> List[AgentMetadata]:
        """
        Get all hybrid agents (combining multiple agent types).
        
        Returns:
            List of hybrid agents
        """
        return [metadata for metadata in self.registry.values() if metadata.is_hybrid]
    
    async def get_agents_by_complexity(self, complexity_level: str) -> List[AgentMetadata]:
        """
        Get agents by complexity level.
        
        Args:
            complexity_level: Complexity level ('basic', 'intermediate', 'advanced', 'expert')
            
        Returns:
            List of agents at the complexity level
        """
        return [metadata for metadata in self.registry.values() 
                if metadata.complexity_level == complexity_level]
    
    async def search_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """
        Search agents by specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agents with the capability
        """
        matching_agents = []
        capability_lower = capability.lower()
        
        for metadata in self.registry.values():
            # Check direct capabilities
            if any(capability_lower in cap.lower() for cap in metadata.capabilities):
                matching_agents.append(metadata)
            # Check specializations
            elif any(capability_lower in spec.lower() for spec in metadata.specializations):
                matching_agents.append(metadata)
            # Check frameworks
            elif any(capability_lower in fw.lower() for fw in metadata.frameworks):
                matching_agents.append(metadata)
        
        return sorted(matching_agents, key=lambda x: x.validation_score, reverse=True)
    
    async def get_agents_by_model(self, model_id: str) -> List[AgentMetadata]:
        """
        Get all agents that use a specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            List of agents using the specified model
        """
        return [
            metadata for metadata in self.registry.values()
            if metadata.preferred_model == model_id
        ]
    
    async def query_agents(self, query: Dict[str, Any]) -> List[AgentMetadata]:
        """
        Advanced query interface for complex agent searches.
        
        Args:
            query: Query dictionary with multiple criteria
                - type: Agent type filter
                - tier: Tier filter
                - specializations: List of required specializations
                - frameworks: List of required frameworks
                - domains: List of required domains
                - complexity: Complexity level filter
                - model: Model preference filter
                - validated_only: Only return validated agents
                - min_score: Minimum validation score
                
        Returns:
            List of agents matching all criteria
        """
        results = list(self.registry.values())
        
        # Apply filters
        if query.get('type'):
            results = [a for a in results if a.type == query['type']]
        
        if query.get('tier'):
            results = [a for a in results if a.tier == query['tier']]
        
        if query.get('specializations'):
            required_specs = set(query['specializations'])
            results = [a for a in results 
                      if required_specs.issubset(set(a.specializations))]
        
        if query.get('frameworks'):
            required_frameworks = set(query['frameworks'])
            results = [a for a in results 
                      if required_frameworks.issubset(set(a.frameworks))]
        
        if query.get('domains'):
            required_domains = set(query['domains'])
            results = [a for a in results 
                      if required_domains.issubset(set(a.domains))]
        
        if query.get('complexity'):
            results = [a for a in results if a.complexity_level == query['complexity']]
        
        if query.get('model'):
            results = [a for a in results if a.preferred_model == query['model']]
        
        if query.get('validated_only', False):
            results = [a for a in results if a.validated]
        
        if query.get('min_score') is not None:
            min_score = query['min_score']
            results = [a for a in results if a.validation_score >= min_score]
        
        # Sort by validation score
        return sorted(results, key=lambda x: x.validation_score, reverse=True)
    
    def get_registry_size(self) -> int:
        """Get the total number of agents in registry."""
        return len(self.registry)