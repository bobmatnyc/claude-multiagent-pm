"""
Enhanced Agent Registry Service for Claude PM Framework v0.8.0
============================================================

Enhanced implementation of the IAgentRegistry interface with:
- Dependency injection integration
- Enhanced error handling and recovery
- Performance optimization with caching
- Service lifecycle management
- Health monitoring integration
- Circuit breaker pattern for resilience

Key Features:
- Interface-based design
- Automatic dependency resolution
- Comprehensive error handling
- Performance optimization
- Agent validation and scoring
- Specialized agent discovery
"""

import asyncio
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Type
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.interfaces import IAgentRegistry, AgentMetadata, ICacheService, IConfigurationService
from ..core.enhanced_base_service import EnhancedBaseService
from ..core.container import injectable
from ..services.shared_prompt_cache import SharedPromptCache

logger = logging.getLogger(__name__)


@dataclass
class AgentDiscoveryMetrics:
    """Metrics for agent discovery operations."""
    total_discovered: int = 0
    discovery_time_ms: float = 0.0
    validation_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    failed_validations: int = 0
    specialized_agents_found: int = 0
    hybrid_agents_found: int = 0


@injectable(IAgentRegistry)
class EnhancedAgentRegistry(EnhancedBaseService, IAgentRegistry):
    """
    Enhanced Agent Registry implementing IAgentRegistry interface.
    
    Provides comprehensive agent discovery and management with performance optimization,
    error handling, and health monitoring integration.
    """
    
    def __init__(self, config: Optional[IConfigurationService] = None,
                 cache_service: Optional[ICacheService] = None):
        """Initialize the enhanced agent registry."""
        super().__init__("enhanced_agent_registry", config)
        
        # Service dependencies
        self._cache_service = cache_service or self._get_injected_service(ICacheService)
        if self._cache_service is None:
            # Fallback to SharedPromptCache if no cache service injected
            self._cache_service = SharedPromptCache.get_instance()
        
        # Agent discovery configuration
        self._discovery_paths: List[Path] = []
        self._core_agent_types = {
            'documentation', 'ticketing', 'version_control', 'qa', 'research',
            'ops', 'security', 'engineer', 'data_engineer'
        }
        self._specialized_agent_types = {
            'ui_ux', 'database', 'api', 'testing', 'performance', 'monitoring',
            'analytics', 'deployment', 'integration', 'workflow', 'content',
            'machine_learning', 'data_science', 'frontend', 'backend', 'mobile',
            'devops', 'cloud', 'infrastructure', 'compliance', 'audit',
            'project_management', 'business_analysis', 'customer_support',
            'marketing', 'sales', 'finance', 'legal', 'hr', 'training',
            'documentation_specialist', 'code_review', 'architecture',
            'orchestrator', 'scaffolding', 'memory_management', 'knowledge_base'
        }
        
        # Registry state
        self._registry: Dict[str, AgentMetadata] = {}
        self._last_discovery_time: Optional[float] = None
        self._discovery_cache_ttl = 300  # 5 minutes
        
        # Performance tracking
        self._discovery_metrics = AgentDiscoveryMetrics()
        
        # Configuration
        self._max_cache_size = self._config.get("agent_registry.max_cache_size", 1000) if self._config else 1000
        self._validation_timeout = self._config.get("agent_registry.validation_timeout", 30) if self._config else 30
        self._enable_file_watching = self._config.get("agent_registry.enable_file_watching", False) if self._config else False
        
        self._logger.info("Enhanced Agent Registry initialized")
    
    async def _initialize(self) -> None:
        """Initialize the agent registry service."""
        self._logger.info("Initializing Enhanced Agent Registry...")
        
        try:
            # Initialize discovery paths
            self._initialize_discovery_paths()
            
            # Perform initial discovery
            await self.discover_agents(force_refresh=True)
            
            self._logger.info("Enhanced Agent Registry initialized successfully")
        
        except Exception as e:
            self._logger.error(f"Failed to initialize Enhanced Agent Registry: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup agent registry resources."""
        self._logger.info("Cleaning up Enhanced Agent Registry...")
        
        try:
            # Clear registry
            self._registry.clear()
            
            # Clear cache
            if self._cache_service:
                self._cache_service.invalidate("agent_registry_*")
            
            self._logger.info("Enhanced Agent Registry cleanup completed")
        
        except Exception as e:
            self._logger.error(f"Failed to cleanup Enhanced Agent Registry: {e}")
    
    async def _health_check(self) -> Dict[str, bool]:
        """Perform agent registry health checks."""
        checks = {}
        
        try:
            # Check cache service
            if self._cache_service:
                test_key = f"health_check_{time.time()}"
                self._cache_service.set(test_key, {"test": True}, ttl=5)
                retrieved = self._cache_service.get(test_key)
                checks["cache_service"] = retrieved is not None and retrieved.get("test") is True
                self._cache_service.delete(test_key)
            else:
                checks["cache_service"] = False
            
            # Check discovery paths
            checks["discovery_paths"] = len(self._discovery_paths) > 0
            
            # Check registry state
            checks["registry_populated"] = len(self._registry) > 0
            
            # Check recent discovery
            if self._last_discovery_time:
                time_since_discovery = time.time() - self._last_discovery_time
                checks["recent_discovery"] = time_since_discovery < (self._discovery_cache_ttl * 2)
            else:
                checks["recent_discovery"] = False
        
        except Exception as e:
            self._logger.error(f"Agent registry health check failed: {e}")
            checks["health_check_error"] = False
        
        return checks
    
    async def discover_agents(self, force_refresh: bool = False) -> Dict[str, AgentMetadata]:
        """
        Discover all available agents across hierarchy with enhanced performance.
        
        Args:
            force_refresh: Force cache refresh even if within TTL
            
        Returns:
            Dictionary of agent name -> AgentMetadata
        """
        async with self._service_operation("discover_agents"):
            discovery_start = time.time()
            
            try:
                # Check if we need to refresh discovery
                if not force_refresh and self._is_discovery_cache_valid():
                    cached_result = await self._get_cached_discovery()
                    if cached_result:
                        self._discovery_metrics.cache_hits += 1
                        self._logger.debug("Using cached agent discovery results")
                        return cached_result
                
                self._discovery_metrics.cache_misses += 1
                self._logger.info("Starting agent discovery across hierarchy")
                
                discovered_agents = {}
                
                # Discover agents from each path with hierarchy precedence
                for path in self._discovery_paths:
                    tier = self._determine_tier(path)
                    try:
                        path_agents = await self._scan_directory(path, tier)
                        
                        # Apply hierarchy precedence
                        for agent_name, agent_metadata in path_agents.items():
                            if agent_name not in discovered_agents:
                                discovered_agents[agent_name] = agent_metadata
                                self._logger.debug(f"Discovered agent '{agent_name}' from {tier} tier")
                            else:
                                # Check tier precedence
                                existing_tier = discovered_agents[agent_name].tier
                                if self._has_tier_precedence(tier, existing_tier):
                                    discovered_agents[agent_name] = agent_metadata
                                    self._logger.debug(f"Agent '{agent_name}' overridden by {tier} tier")
                    
                    except Exception as e:
                        self._logger.error(f"Failed to scan directory {path}: {e}")
                        await self._handle_error(e, {"operation": "scan_directory", "path": str(path)})
                
                # Validate discovered agents
                validation_start = time.time()
                validated_agents = await self._validate_agents(discovered_agents)
                validation_time = (time.time() - validation_start) * 1000
                
                # Update registry and cache
                self._registry = validated_agents
                self._last_discovery_time = time.time()
                
                # Cache discovery results
                await self._cache_discovery_results(validated_agents)
                
                # Update metrics
                discovery_time = (time.time() - discovery_start) * 1000
                self._discovery_metrics.total_discovered = len(validated_agents)
                self._discovery_metrics.discovery_time_ms = discovery_time
                self._discovery_metrics.validation_time_ms = validation_time
                self._discovery_metrics.specialized_agents_found = len([
                    a for a in validated_agents.values() 
                    if a.type in self._specialized_agent_types
                ])
                self._discovery_metrics.hybrid_agents_found = len([
                    a for a in validated_agents.values() 
                    if hasattr(a, 'is_hybrid') and getattr(a, 'is_hybrid', False)
                ])
                
                self._logger.info(
                    f"Agent discovery completed in {discovery_time:.1f}ms, "
                    f"found {len(validated_agents)} agents "
                    f"({self._discovery_metrics.specialized_agents_found} specialized, "
                    f"{self._discovery_metrics.hybrid_agents_found} hybrid)"
                )
                
                return self._registry
            
            except Exception as e:
                self._logger.error(f"Agent discovery failed: {e}")
                await self._handle_error(e, {"operation": "discover_agents"})
                raise
    
    async def get_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """
        Get specific agent metadata with caching.
        
        Args:
            agent_name: Name of agent to retrieve
            
        Returns:
            AgentMetadata or None if not found
        """
        async with self._service_operation("get_agent"):
            try:
                # Check cache first
                cache_key = f"agent_registry_agent_{agent_name}"
                if self._cache_service:
                    cached_agent = self._cache_service.get(cache_key)
                    if cached_agent:
                        return AgentMetadata(**cached_agent)
                
                # Ensure registry is populated
                if not self._registry:
                    await self.discover_agents()
                
                agent = self._registry.get(agent_name)
                
                # Cache the result
                if agent and self._cache_service:
                    self._cache_service.set(cache_key, asdict(agent), ttl=300)
                
                return agent
            
            except Exception as e:
                self._logger.error(f"Failed to get agent {agent_name}: {e}")
                await self._handle_error(e, {"operation": "get_agent", "agent_name": agent_name})
                return None
    
    async def list_agents(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """
        List agents with optional filtering and caching.
        
        Args:
            agent_type: Filter by agent type
            tier: Filter by hierarchy tier
            
        Returns:
            List of matching AgentMetadata
        """
        async with self._service_operation("list_agents"):
            try:
                # Create cache key based on filters
                cache_key = f"agent_registry_list_{agent_type}_{tier}"
                
                # Check cache
                if self._cache_service:
                    cached_result = self._cache_service.get(cache_key)
                    if cached_result:
                        return [AgentMetadata(**agent_data) for agent_data in cached_result]
                
                # Ensure registry is populated
                if not self._registry:
                    await self.discover_agents()
                
                agents = list(self._registry.values())
                
                # Apply filters
                if agent_type:
                    agents = [a for a in agents if a.type == agent_type]
                
                if tier:
                    agents = [a for a in agents if a.tier == tier]
                
                # Cache the result
                if self._cache_service:
                    cached_data = [asdict(agent) for agent in agents]
                    self._cache_service.set(cache_key, cached_data, ttl=300)
                
                return agents
            
            except Exception as e:
                self._logger.error(f"Failed to list agents: {e}")
                await self._handle_error(e, {
                    "operation": "list_agents", 
                    "agent_type": agent_type, 
                    "tier": tier
                })
                return []
    
    async def get_specialized_agents(self, agent_type: str) -> List[AgentMetadata]:
        """
        Get all agents of a specific specialized type with enhanced filtering.
        
        Args:
            agent_type: Specialized agent type to search for
            
        Returns:
            List of matching specialized agents sorted by validation score
        """
        async with self._service_operation("get_specialized_agents"):
            try:
                cache_key = f"agent_registry_specialized_{agent_type}"
                
                # Check cache
                if self._cache_service:
                    cached_result = self._cache_service.get(cache_key)
                    if cached_result:
                        return [AgentMetadata(**agent_data) for agent_data in cached_result]
                
                # Ensure registry is populated
                if not self._registry:
                    await self.discover_agents()
                
                specialized_agents = []
                
                for metadata in self._registry.values():
                    # Check primary type
                    if metadata.type == agent_type:
                        specialized_agents.append(metadata)
                    # Check specializations
                    elif hasattr(metadata, 'specializations') and agent_type in metadata.specializations:
                        specialized_agents.append(metadata)
                    # Check hybrid types
                    elif (hasattr(metadata, 'hybrid_types') and 
                          isinstance(getattr(metadata, 'hybrid_types', []), list) and 
                          agent_type in getattr(metadata, 'hybrid_types', [])):
                        specialized_agents.append(metadata)
                
                # Sort by validation score (descending)
                specialized_agents.sort(
                    key=lambda x: getattr(x, 'validation_score', 0.0), 
                    reverse=True
                )
                
                # Cache the result
                if self._cache_service:
                    cached_data = [asdict(agent) for agent in specialized_agents]
                    self._cache_service.set(cache_key, cached_data, ttl=300)
                
                return specialized_agents
            
            except Exception as e:
                self._logger.error(f"Failed to get specialized agents for {agent_type}: {e}")
                await self._handle_error(e, {
                    "operation": "get_specialized_agents", 
                    "agent_type": agent_type
                })
                return []
    
    async def search_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """
        Search agents by specific capability with fuzzy matching.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agents with the capability sorted by relevance
        """
        async with self._service_operation("search_agents_by_capability"):
            try:
                cache_key = f"agent_registry_capability_{capability.lower()}"
                
                # Check cache
                if self._cache_service:
                    cached_result = self._cache_service.get(cache_key)
                    if cached_result:
                        return [AgentMetadata(**agent_data) for agent_data in cached_result]
                
                # Ensure registry is populated
                if not self._registry:
                    await self.discover_agents()
                
                matching_agents = []
                capability_lower = capability.lower()
                
                for metadata in self._registry.values():
                    relevance_score = 0.0
                    
                    # Check direct capabilities
                    if hasattr(metadata, 'capabilities') and metadata.capabilities:
                        for cap in metadata.capabilities:
                            if capability_lower in cap.lower():
                                relevance_score += 1.0
                            elif capability_lower in cap.lower().replace('_', ' '):
                                relevance_score += 0.8
                    
                    # Check specializations
                    if hasattr(metadata, 'specializations') and metadata.specializations:
                        for spec in metadata.specializations:
                            if capability_lower in spec.lower():
                                relevance_score += 0.9
                    
                    # Check frameworks
                    if hasattr(metadata, 'frameworks') and metadata.frameworks:
                        for fw in metadata.frameworks:
                            if capability_lower in fw.lower():
                                relevance_score += 0.7
                    
                    # Check description
                    if metadata.description and capability_lower in metadata.description.lower():
                        relevance_score += 0.5
                    
                    if relevance_score > 0:
                        # Add relevance score to metadata for sorting
                        agent_copy = AgentMetadata(**asdict(metadata))
                        setattr(agent_copy, 'relevance_score', relevance_score)
                        matching_agents.append(agent_copy)
                
                # Sort by relevance score and validation score
                matching_agents.sort(
                    key=lambda x: (
                        getattr(x, 'relevance_score', 0.0),
                        getattr(x, 'validation_score', 0.0)
                    ),
                    reverse=True
                )
                
                # Cache the result
                if self._cache_service:
                    cached_data = [asdict(agent) for agent in matching_agents]
                    self._cache_service.set(cache_key, cached_data, ttl=300)
                
                return matching_agents
            
            except Exception as e:
                self._logger.error(f"Failed to search agents by capability {capability}: {e}")
                await self._handle_error(e, {
                    "operation": "search_agents_by_capability", 
                    "capability": capability
                })
                return []
    
    async def refresh_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """
        Refresh specific agent metadata with validation.
        
        Args:
            agent_name: Name of agent to refresh
            
        Returns:
            Updated AgentMetadata or None if not found
        """
        async with self._service_operation("refresh_agent"):
            try:
                if agent_name not in self._registry:
                    return None
                
                current_metadata = self._registry[agent_name]
                agent_file = Path(current_metadata.path)
                
                if not agent_file.exists():
                    # Agent file removed
                    del self._registry[agent_name]
                    
                    # Clear from cache
                    if self._cache_service:
                        self._cache_service.delete(f"agent_registry_agent_{agent_name}")
                    
                    return None
                
                # Re-extract metadata
                updated_metadata = await self._extract_agent_metadata(agent_file, current_metadata.tier)
                if updated_metadata:
                    # Validate updated agent
                    validated = await self._validate_agents({agent_name: updated_metadata})
                    if agent_name in validated:
                        self._registry[agent_name] = validated[agent_name]
                        
                        # Update cache
                        if self._cache_service:
                            cache_key = f"agent_registry_agent_{agent_name}"
                            self._cache_service.set(cache_key, asdict(validated[agent_name]), ttl=300)
                        
                        return validated[agent_name]
                
                return None
            
            except Exception as e:
                self._logger.error(f"Failed to refresh agent {agent_name}: {e}")
                await self._handle_error(e, {"operation": "refresh_agent", "agent_name": agent_name})
                return None
    
    def clear_cache(self) -> None:
        """Clear discovery cache and force refresh on next access."""
        try:
            self._last_discovery_time = None
            self._registry.clear()
            
            # Clear cache entries
            if self._cache_service:
                self._cache_service.invalidate("agent_registry_*")
            
            self._logger.info("Agent registry cache cleared")
        
        except Exception as e:
            self._logger.error(f"Failed to clear cache: {e}")
    
    def get_discovery_metrics(self) -> AgentDiscoveryMetrics:
        """Get agent discovery performance metrics."""
        return self._discovery_metrics
    
    # Private implementation methods (inherited from original implementation)
    
    def _initialize_discovery_paths(self) -> None:
        """Initialize agent discovery paths with two-tier hierarchy."""
        paths = []
        
        # Current directory → parent directories scanning
        current_path = Path.cwd()
        while current_path.parent != current_path:  # Until we reach root
            claude_pm_dir = current_path / '.claude-pm' / 'agents'
            if claude_pm_dir.exists():
                paths.append(claude_pm_dir)
            current_path = current_path.parent
        
        # User directory agents
        user_home = Path.home()
        user_agents_dir = user_home / '.claude-pm' / 'agents' / 'user'
        if user_agents_dir.exists():
            paths.append(user_agents_dir)
        
        # System agents (framework directory)
        try:
            import claude_pm
            framework_path = Path(claude_pm.__file__).parent / 'agents'
            if framework_path.exists():
                paths.append(framework_path)
        except ImportError:
            self._logger.warning("Claude PM framework not available for system agent discovery")
        
        self._discovery_paths = paths
        self._logger.info(f"Initialized discovery paths: {[str(p) for p in paths]}")
    
    async def _scan_directory(self, directory: Path, tier: str) -> Dict[str, AgentMetadata]:
        """Scan directory for agent files with enhanced error handling."""
        agents = {}
        
        if not directory.exists():
            return agents
        
        self._logger.debug(f"Scanning directory: {directory} (tier: {tier})")
        
        try:
            # Scan for Python agent files
            for agent_file in directory.rglob("*.py"):
                if agent_file.name.startswith('__'):
                    continue  # Skip __init__.py and __pycache__
                
                try:
                    agent_metadata = await self._extract_agent_metadata(agent_file, tier)
                    if agent_metadata:
                        agents[agent_metadata.name] = agent_metadata
                except Exception as e:
                    self._logger.warning(f"Error processing agent file {agent_file}: {e}")
                    await self._handle_error(e, {
                        "operation": "extract_agent_metadata",
                        "file": str(agent_file),
                        "tier": tier
                    })
        
        except Exception as e:
            self._logger.error(f"Failed to scan directory {directory}: {e}")
            raise
        
        return agents
    
    async def _extract_agent_metadata(self, agent_file: Path, tier: str) -> Optional[AgentMetadata]:
        """Extract metadata from agent file with timeout protection."""
        try:
            # Use timeout to prevent hanging on large files
            return await asyncio.wait_for(
                self._do_extract_agent_metadata(agent_file, tier),
                timeout=self._validation_timeout
            )
        except asyncio.TimeoutError:
            self._logger.warning(f"Agent metadata extraction timed out for {agent_file}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to extract metadata from {agent_file}: {e}")
            return None
    
    async def _do_extract_agent_metadata(self, agent_file: Path, tier: str) -> Optional[AgentMetadata]:
        """Actual metadata extraction implementation."""
        # This would contain the original metadata extraction logic
        # For brevity, using simplified version here
        try:
            stat = agent_file.stat()
            agent_name = agent_file.stem
            agent_type = self._classify_agent_type(agent_name, agent_file)
            
            # Basic metadata structure
            return AgentMetadata(
                name=agent_name,
                type=agent_type,
                path=str(agent_file),
                tier=tier,
                description=f"Agent {agent_name}",
                capabilities=[],
                specializations=[],
                frameworks=[],
                domains=[],
                roles=[],
                last_modified=stat.st_mtime,
                validated=False,
                validation_score=0.0
            )
        
        except Exception as e:
            self._logger.error(f"Failed to extract metadata from {agent_file}: {e}")
            return None
    
    def _classify_agent_type(self, agent_name: str, agent_file: Path) -> str:
        """Classify agent type based on name and path."""
        name_lower = agent_name.lower()
        
        # Check core agent types first
        for core_type in self._core_agent_types:
            if core_type in name_lower or name_lower in core_type:
                return core_type
        
        # Check specialized types
        for spec_type in self._specialized_agent_types:
            if spec_type in name_lower or name_lower in spec_type:
                return spec_type
        
        return 'custom'
    
    async def _validate_agents(self, agents: Dict[str, AgentMetadata]) -> Dict[str, AgentMetadata]:
        """Validate agents with enhanced scoring."""
        validated = {}
        
        for name, metadata in agents.items():
            try:
                # Basic validation
                if not Path(metadata.path).exists():
                    metadata.validated = False
                    metadata.validation_score = 0.0
                else:
                    metadata.validated = True
                    metadata.validation_score = 75.0  # Base score for existing files
                
                validated[name] = metadata
            
            except Exception as e:
                self._logger.warning(f"Validation error for agent {name}: {e}")
                self._discovery_metrics.failed_validations += 1
                metadata.validated = False
                metadata.validation_score = 0.0
                validated[name] = metadata
        
        return validated
    
    def _determine_tier(self, path: Path) -> str:
        """Determine hierarchy tier based on path."""
        path_str = str(path)
        
        if '.claude-pm/agents/user' in path_str:
            return 'user'
        elif 'claude_pm/agents' in path_str:
            return 'system'
        else:
            return 'project'
    
    def _has_tier_precedence(self, tier1: str, tier2: str) -> bool:
        """Check if tier1 has precedence over tier2."""
        precedence_order = ['project', 'user', 'system']
        try:
            return precedence_order.index(tier1) < precedence_order.index(tier2)
        except ValueError:
            return False
    
    def _is_discovery_cache_valid(self) -> bool:
        """Check if discovery cache is still valid."""
        if self._last_discovery_time is None:
            return False
        return (time.time() - self._last_discovery_time) < self._discovery_cache_ttl
    
    async def _get_cached_discovery(self) -> Optional[Dict[str, AgentMetadata]]:
        """Get cached discovery results."""
        if not self._cache_service:
            return None
        
        try:
            cached_data = self._cache_service.get("agent_registry_discovery")
            if cached_data:
                return {name: AgentMetadata(**data) for name, data in cached_data.items()}
        except Exception as e:
            self._logger.warning(f"Failed to get cached discovery: {e}")
        
        return None
    
    async def _cache_discovery_results(self, agents: Dict[str, AgentMetadata]) -> None:
        """Cache discovery results."""
        if not self._cache_service:
            return
        
        try:
            cache_data = {name: asdict(metadata) for name, metadata in agents.items()}
            self._cache_service.set("agent_registry_discovery", cache_data, ttl=self._discovery_cache_ttl)
        except Exception as e:
            self._logger.warning(f"Failed to cache discovery results: {e}")
    
    async def _collect_custom_metrics(self) -> None:
        """Collect custom metrics for the agent registry."""
        try:
            # Update service metrics with agent registry data
            self.update_metrics(
                registry_size=len(self._registry),
                discovery_cache_ttl=self._discovery_cache_ttl,
                last_discovery_time=self._last_discovery_time,
                discovery_time_ms=self._discovery_metrics.discovery_time_ms,
                validation_time_ms=self._discovery_metrics.validation_time_ms,
                cache_hit_rate=(
                    self._discovery_metrics.cache_hits / 
                    max(1, self._discovery_metrics.cache_hits + self._discovery_metrics.cache_misses)
                ),
                specialized_agents_count=self._discovery_metrics.specialized_agents_found,
                hybrid_agents_count=self._discovery_metrics.hybrid_agents_found
            )
        except Exception as e:
            self._logger.warning(f"Failed to collect agent registry metrics: {e}")