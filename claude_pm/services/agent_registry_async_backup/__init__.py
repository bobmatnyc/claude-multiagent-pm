"""
Agent Registry Service - Core agent discovery and management system
Implements comprehensive agent discovery with two-tier hierarchy and performance optimization

ISS-0118: Agent Registry Implementation
Created: 2025-07-15
"""

import time
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import asdict

from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.model_selector import ModelSelector

from .models import AgentMetadata
from .discovery import AgentDiscovery
from .metadata_extractor import MetadataExtractor
from .model_configuration import ModelConfigurator
from .classification import AgentClassifier
from .validation import AgentValidator
from .query_api import AgentQueryAPI
from .analytics import AgentAnalytics
from .sync_wrappers import SyncWrapper
from .health_check import HealthMonitor

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Core Agent Registry - Comprehensive agent discovery and management system
    
    Features:
    - Two-tier hierarchy discovery (user → system)
    - Directory scanning with performance optimization
    - Agent metadata collection and caching
    - Agent type detection and classification
    - SharedPromptCache integration
    - Agent validation and error handling
    """
    
    def __init__(self, cache_service: Optional[SharedPromptCache] = None, model_selector: Optional[ModelSelector] = None):
        """Initialize AgentRegistry with optional cache service and model selector"""
        self.cache_service = cache_service or SharedPromptCache()
        self.model_selector = model_selector or ModelSelector()
        self.registry: Dict[str, AgentMetadata] = {}
        self.last_discovery_time: Optional[float] = None
        self.discovery_cache_ttl = 300  # 5 minutes
        
        # Initialize components
        self.classifier = AgentClassifier()
        self.model_configurator = ModelConfigurator(self.model_selector)
        self.metadata_extractor = MetadataExtractor(self.classifier, self.model_configurator)
        self.discovery = AgentDiscovery(self.metadata_extractor)
        self.validator = AgentValidator()
        self.query_api = AgentQueryAPI(self.registry)
        self.analytics = AgentAnalytics(self.classifier)
        self.health_monitor = HealthMonitor(
            self.discovery.discovery_paths,
            self.cache_service,
            self.model_selector
        )
        
        # Expose core agent types
        self.core_agent_types = self.classifier.core_agent_types
        self.specialized_agent_types = self.classifier.specialized_agent_types
        self.discovery_paths = self.discovery.discovery_paths
    
    async def discover_agents(self, force_refresh: bool = False) -> Dict[str, AgentMetadata]:
        """
        Discover all available agents across two-tier hierarchy
        
        Args:
            force_refresh: Force cache refresh even if within TTL
            
        Returns:
            Dictionary of agent name -> AgentMetadata
        """
        discovery_start = time.time()
        
        # Check if we need to refresh discovery
        if not force_refresh and self._is_discovery_cache_valid():
            cache_hit = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.cache_service.get("agent_registry_discovery")
            )
            if cache_hit:
                logger.debug("Using cached agent discovery results")
                self.registry = {name: AgentMetadata(**data) for name, data in cache_hit.items()}
                self.query_api = AgentQueryAPI(self.registry)
                return self.registry
        
        # Perform discovery
        discovered_agents = await self.discovery.discover_agents()
        
        # Validate discovered agents
        validated_agents = await self.validator.validate_agents(discovered_agents)
        
        # Update registry and cache
        self.registry = validated_agents
        self.query_api = AgentQueryAPI(self.registry)
        self.last_discovery_time = time.time()
        
        # Cache discovery results for performance
        cache_data = {name: asdict(metadata) for name, metadata in validated_agents.items()}
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.cache_service.set("agent_registry_discovery", cache_data, ttl=self.discovery_cache_ttl)
        )
        
        discovery_time = time.time() - discovery_start
        logger.info(f"Agent discovery completed in {discovery_time:.3f}s, found {len(validated_agents)} agents")
        
        return self.registry
    
    def _is_discovery_cache_valid(self) -> bool:
        """Check if discovery cache is still valid"""
        if self.last_discovery_time is None:
            return False
        return (time.time() - self.last_discovery_time) < self.discovery_cache_ttl
    
    # Query API delegation methods
    async def get_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """Get specific agent metadata"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_agent(agent_name)
    
    async def list_agents(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """List agents with optional filtering"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.list_agents(agent_type, tier)
    
    async def listAgents(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """List agents with optional filtering (camelCase wrapper for compatibility)"""
        return await self.list_agents(agent_type=agent_type, tier=tier)
    
    async def get_agent_types(self) -> Set[str]:
        """Get all discovered agent types"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_agent_types()
    
    # Analytics delegation methods
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics and metrics"""
        if not self.registry:
            await self.discover_agents()
        return await self.analytics.get_registry_stats(
            self.registry, self.discovery_paths, self.last_discovery_time
        )
    
    async def get_enhanced_registry_stats(self) -> Dict[str, Any]:
        """Get enhanced registry statistics including specialized agent metrics"""
        if not self.registry:
            await self.discover_agents()
        return await self.analytics.get_enhanced_registry_stats(
            self.registry, self.discovery_paths, self.last_discovery_time
        )
    
    async def get_model_usage_statistics(self) -> Dict[str, Any]:
        """Get statistics on model usage across all agents"""
        if not self.registry:
            await self.discover_agents()
        return await self.analytics.get_model_usage_statistics(self.registry)
    
    # Refresh and cache management
    async def refresh_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """Refresh specific agent metadata"""
        if agent_name not in self.registry:
            return None
        
        current_metadata = self.registry[agent_name]
        agent_file = Path(current_metadata.path)
        
        if not agent_file.exists():
            # Agent file removed
            del self.registry[agent_name]
            return None
        
        # Re-extract metadata
        updated_metadata = await self.metadata_extractor.extract_agent_metadata(
            agent_file, current_metadata.tier
        )
        if updated_metadata:
            # Validate updated agent
            validated = await self.validator.validate_agents({agent_name: updated_metadata})
            if agent_name in validated:
                self.registry[agent_name] = validated[agent_name]
                return validated[agent_name]
        
        return None
    
    def clear_cache(self) -> None:
        """Clear discovery cache and force refresh on next access"""
        self.last_discovery_time = None
        self.registry.clear()
        self.cache_service.invalidate("agent_registry_discovery")
    
    # Enhanced API methods for ISS-0118 specialized agent discovery
    async def get_specialized_agents(self, agent_type: str) -> List[AgentMetadata]:
        """Get all agents of a specific specialized type"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_specialized_agents(agent_type)
    
    async def get_agents_by_framework(self, framework: str) -> List[AgentMetadata]:
        """Get agents that use a specific framework"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_agents_by_framework(framework)
    
    async def get_agents_by_domain(self, domain: str) -> List[AgentMetadata]:
        """Get agents specialized in a specific domain"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_agents_by_domain(domain)
    
    async def get_agents_by_role(self, role: str) -> List[AgentMetadata]:
        """Get agents with a specific role"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_agents_by_role(role)
    
    async def get_hybrid_agents(self) -> List[AgentMetadata]:
        """Get all hybrid agents (combining multiple agent types)"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_hybrid_agents()
    
    async def get_agents_by_complexity(self, complexity_level: str) -> List[AgentMetadata]:
        """Get agents by complexity level"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_agents_by_complexity(complexity_level)
    
    async def search_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """Search agents by specific capability"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.search_agents_by_capability(capability)
    
    # Model configuration methods
    async def get_agent_model_configuration(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get model configuration for a specific agent"""
        if not self.registry:
            await self.discover_agents()
        
        agent_metadata = self.registry.get(agent_name)
        if not agent_metadata:
            return None
        
        return {
            "agent_name": agent_name,
            "agent_type": agent_metadata.type,
            "preferred_model": agent_metadata.preferred_model,
            "model_config": agent_metadata.model_config,
            "complexity_level": agent_metadata.complexity_level,
            "capabilities": agent_metadata.capabilities,
            "specializations": agent_metadata.specializations
        }
    
    async def get_agents_by_model(self, model_id: str) -> List[AgentMetadata]:
        """Get all agents that use a specific model"""
        if not self.registry:
            await self.discover_agents()
        return await self.query_api.get_agents_by_model(model_id)
    
    async def get_model_recommendations_for_agents(
        self, 
        agent_names: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get model recommendations for specified agents or all agents"""
        if not self.registry:
            await self.discover_agents()
        
        recommendations = {}
        
        # Determine which agents to analyze
        if agent_names:
            agents_to_analyze = {
                name: metadata for name, metadata in self.registry.items()
                if name in agent_names
            }
        else:
            agents_to_analyze = self.registry
        
        # Generate recommendations for each agent
        for agent_name, metadata in agents_to_analyze.items():
            try:
                recommendation = self.model_selector.get_model_recommendation(
                    agent_type=metadata.type,
                    task_description=metadata.description or "",
                    performance_requirements=metadata.model_config.get("selection_criteria", {})
                )
                
                recommendations[agent_name] = {
                    "current_model": metadata.preferred_model,
                    "recommended_model": recommendation["recommended_model"],
                    "matches_recommendation": metadata.preferred_model == recommendation["recommended_model"],
                    "recommendation_details": recommendation,
                    "agent_metadata": {
                        "type": metadata.type,
                        "complexity_level": metadata.complexity_level,
                        "specializations": metadata.specializations
                    }
                }
                
            except Exception as e:
                logger.error(f"Error generating recommendation for agent {agent_name}: {e}")
                recommendations[agent_name] = {
                    "error": str(e),
                    "current_model": metadata.preferred_model
                }
        
        return recommendations
    
    async def validate_agent_model_configurations(self) -> Dict[str, Any]:
        """Validate model configurations for all agents"""
        if not self.registry:
            await self.discover_agents()
        
        validation_results = {
            "total_agents": len(self.registry),
            "valid_configurations": 0,
            "invalid_configurations": 0,
            "missing_configurations": 0,
            "warnings": [],
            "recommendations": [],
            "detailed_results": {}
        }
        
        for agent_name, metadata in self.registry.items():
            try:
                if not metadata.preferred_model:
                    validation_results["missing_configurations"] += 1
                    validation_results["warnings"].append(
                        f"Agent '{agent_name}' has no model configuration"
                    )
                    continue
                
                # Validate using ModelSelector
                validation = self.model_selector.validate_model_selection(
                    agent_type=metadata.type,
                    selected_model=metadata.preferred_model
                )
                
                if validation["valid"]:
                    validation_results["valid_configurations"] += 1
                else:
                    validation_results["invalid_configurations"] += 1
                
                validation_results["detailed_results"][agent_name] = validation
                
                # Collect warnings and recommendations
                for warning in validation.get("warnings", []):
                    validation_results["warnings"].append(f"{agent_name}: {warning}")
                
                for suggestion in validation.get("suggestions", []):
                    validation_results["recommendations"].append(f"{agent_name}: {suggestion}")
                
            except Exception as e:
                logger.error(f"Error validating model configuration for {agent_name}: {e}")
                validation_results["invalid_configurations"] += 1
                validation_results["detailed_results"][agent_name] = {
                    "valid": False,
                    "error": str(e)
                }
        
        return validation_results
    
    async def update_agent_model_configuration(
        self,
        agent_name: str,
        model_id: str,
        model_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update model configuration for a specific agent"""
        if not self.registry:
            await self.discover_agents()
        
        if agent_name not in self.registry:
            logger.error(f"Agent '{agent_name}' not found in registry")
            return False
        
        try:
            # Validate model selection
            validation = self.model_selector.validate_model_selection(
                agent_type=self.registry[agent_name].type,
                selected_model=model_id
            )
            
            if not validation["valid"]:
                logger.error(f"Invalid model selection for agent '{agent_name}': {validation.get('error')}")
                return False
            
            # Update metadata
            self.registry[agent_name].preferred_model = model_id
            if model_config:
                self.registry[agent_name].model_config.update(model_config)
            else:
                # Set basic configuration
                self.registry[agent_name].model_config = {
                    "manually_updated": True,
                    "update_timestamp": time.time()
                }
            
            logger.info(f"Updated model configuration for agent '{agent_name}': {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating model configuration for agent '{agent_name}': {e}")
            return False
    
    def get_model_selector(self) -> ModelSelector:
        """Get the ModelSelector instance for direct access."""
        return self.model_selector
    
    # Synchronous wrappers
    def list_agents_sync(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """Synchronous wrapper for async list_agents method"""
        return SyncWrapper.list_agents_sync(self, agent_type, tier)
    
    def discover_agents_sync(self, force_refresh: bool = False) -> Dict[str, AgentMetadata]:
        """Synchronous wrapper for discover_agents method"""
        return SyncWrapper.discover_agents_sync(self, force_refresh)
    
    def get_agent_sync(self, agent_name: str) -> Optional[AgentMetadata]:
        """Synchronous wrapper for get_agent method"""
        return SyncWrapper.get_agent_sync(self, agent_name)
    
    def get_registry_stats_sync(self) -> Dict[str, Any]:
        """Synchronous wrapper for get_registry_stats method"""
        return SyncWrapper.get_registry_stats_sync(self)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check on the AgentRegistry"""
        return self.health_monitor.health_check(self.registry, self.last_discovery_time)


# Import asyncio at module level
import asyncio
from pathlib import Path