"""
Agent Registry Service - Core agent discovery and management system
Implements comprehensive agent discovery with two-tier hierarchy and performance optimization

ISS-0118: Agent Registry Implementation
Created: 2025-07-15
"""

import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from claude_pm.services.shared_prompt_cache import SharedPromptCache

logger = logging.getLogger(__name__)

@dataclass
class AgentMetadata:
    """Agent metadata structure for registry entries"""
    name: str
    type: str
    path: str
    tier: str  # 'user', 'system'
    description: Optional[str] = None
    version: Optional[str] = None
    capabilities: List[str] = None
    last_modified: Optional[float] = None
    file_size: Optional[int] = None
    validated: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []

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
    
    def __init__(self, cache_service: Optional[SharedPromptCache] = None):
        """Initialize AgentRegistry with optional cache service"""
        self.cache_service = cache_service or SharedPromptCache()
        self.registry: Dict[str, AgentMetadata] = {}
        self.discovery_paths: List[Path] = []
        self.core_agent_types = {
            'documentation', 'ticketing', 'version_control', 'qa', 'research',
            'ops', 'security', 'engineer', 'data_engineer'
        }
        self.last_discovery_time: Optional[float] = None
        self.discovery_cache_ttl = 300  # 5 minutes
        
        # Initialize discovery paths
        self._initialize_discovery_paths()
    
    def _initialize_discovery_paths(self) -> None:
        """Initialize agent discovery paths with two-tier hierarchy"""
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
            logger.warning("Claude PM framework not available for system agent discovery")
        
        self.discovery_paths = paths
        logger.info(f"Initialized discovery paths: {[str(p) for p in paths]}")
    
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
                return self.registry
        
        logger.info("Starting agent discovery across hierarchy")
        discovered_agents = {}
        
        # Discover agents from each path with hierarchy precedence
        for path in self.discovery_paths:
            tier = self._determine_tier(path)
            path_agents = await self._scan_directory(path, tier)
            
            # Apply hierarchy precedence (user overrides system)
            for agent_name, agent_metadata in path_agents.items():
                if agent_name not in discovered_agents:
                    discovered_agents[agent_name] = agent_metadata
                    logger.debug(f"Discovered agent '{agent_name}' from {tier} tier")
                else:
                    # Check tier precedence
                    existing_tier = discovered_agents[agent_name].tier
                    if self._has_tier_precedence(tier, existing_tier):
                        discovered_agents[agent_name] = agent_metadata
                        logger.debug(f"Agent '{agent_name}' overridden by {tier} tier")
        
        # Validate discovered agents
        validated_agents = await self._validate_agents(discovered_agents)
        
        # Update registry and cache
        self.registry = validated_agents
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
    
    async def _scan_directory(self, directory: Path, tier: str) -> Dict[str, AgentMetadata]:
        """
        Scan directory for agent files and extract metadata
        
        Args:
            directory: Directory path to scan
            tier: Hierarchy tier ('user' or 'system')
            
        Returns:
            Dictionary of discovered agents
        """
        agents = {}
        
        if not directory.exists():
            return agents
        
        logger.debug(f"Scanning directory: {directory} (tier: {tier})")
        
        # Scan for Python agent files
        for agent_file in directory.rglob("*.py"):
            if agent_file.name.startswith('__'):
                continue  # Skip __init__.py and __pycache__
            
            try:
                agent_metadata = await self._extract_agent_metadata(agent_file, tier)
                if agent_metadata:
                    agents[agent_metadata.name] = agent_metadata
            except Exception as e:
                logger.warning(f"Error processing agent file {agent_file}: {e}")
        
        return agents
    
    async def _extract_agent_metadata(self, agent_file: Path, tier: str) -> Optional[AgentMetadata]:
        """
        Extract metadata from agent file
        
        Args:
            agent_file: Path to agent file
            tier: Hierarchy tier
            
        Returns:
            AgentMetadata or None if extraction fails
        """
        try:
            # Get file stats
            stat = agent_file.stat()
            file_size = stat.st_size
            last_modified = stat.st_mtime
            
            # Determine agent name and type
            agent_name = agent_file.stem
            agent_type = self._classify_agent_type(agent_name, agent_file)
            
            # Read file for additional metadata
            description, version, capabilities = await self._parse_agent_file(agent_file)
            
            return AgentMetadata(
                name=agent_name,
                type=agent_type,
                path=str(agent_file),
                tier=tier,
                description=description,
                version=version,
                capabilities=capabilities,
                last_modified=last_modified,
                file_size=file_size,
                validated=False  # Will be validated later
            )
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {agent_file}: {e}")
            return None
    
    async def _parse_agent_file(self, agent_file: Path) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Parse agent file for metadata information
        
        Args:
            agent_file: Path to agent file
            
        Returns:
            Tuple of (description, version, capabilities)
        """
        description = None
        version = None
        capabilities = []
        
        try:
            content = agent_file.read_text(encoding='utf-8')
            
            # Extract docstring description
            if '"""' in content:
                docstring_start = content.find('"""')
                if docstring_start != -1:
                    docstring_end = content.find('"""', docstring_start + 3)
                    if docstring_end != -1:
                        docstring = content[docstring_start + 3:docstring_end].strip()
                        # Use first line as description
                        description = docstring.split('\n')[0].strip()
            
            # Extract version information
            if 'VERSION' in content or '__version__' in content:
                lines = content.split('\n')
                for line in lines:
                    if 'VERSION' in line or '__version__' in line:
                        if '=' in line:
                            version_part = line.split('=')[1].strip().strip('"\'')
                            version = version_part
                            break
            
            # Extract capabilities from methods/functions
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('def ') and not line.startswith('def _'):
                    # Extract public method names as capabilities
                    method_name = line.split('(')[0].replace('def ', '').strip()
                    if method_name not in ['__init__', '__str__', '__repr__']:
                        capabilities.append(method_name)
                elif line.startswith('async def ') and not line.startswith('async def _'):
                    # Extract async method names as capabilities
                    method_name = line.split('(')[0].replace('async def ', '').strip()
                    if method_name not in ['__init__', '__str__', '__repr__']:
                        capabilities.append(f"async_{method_name}")
        
        except Exception as e:
            logger.warning(f"Error parsing agent file {agent_file}: {e}")
        
        return description, version, capabilities
    
    def _classify_agent_type(self, agent_name: str, agent_file: Path) -> str:
        """
        Classify agent type based on name and path
        
        Args:
            agent_name: Agent name
            agent_file: Agent file path
            
        Returns:
            Agent type classification
        """
        # Check for core agent types
        name_lower = agent_name.lower()
        
        # Direct core agent type matches
        for core_type in self.core_agent_types:
            if core_type in name_lower or name_lower in core_type:
                return core_type
        
        # Pattern-based classification
        if 'doc' in name_lower:
            return 'documentation'
        elif 'ticket' in name_lower:
            return 'ticketing'
        elif any(term in name_lower for term in ['version', 'git', 'vcs']):
            return 'version_control'
        elif any(term in name_lower for term in ['qa', 'test', 'quality']):
            return 'qa'
        elif any(term in name_lower for term in ['research', 'analyze', 'investigate']):
            return 'research'
        elif any(term in name_lower for term in ['ops', 'deploy', 'infrastructure']):
            return 'ops'
        elif 'security' in name_lower:
            return 'security'
        elif any(term in name_lower for term in ['engineer', 'code', 'develop']):
            return 'engineer'
        elif any(term in name_lower for term in ['data', 'database', 'api']):
            return 'data_engineer'
        else:
            return 'custom'
    
    def _determine_tier(self, path: Path) -> str:
        """
        Determine hierarchy tier based on path
        
        Args:
            path: Directory path
            
        Returns:
            Tier classification
        """
        path_str = str(path)
        
        if '.claude-pm/agents/user' in path_str:
            return 'user'
        elif 'claude_pm/agents' in path_str:
            return 'system'
        else:
            return 'project'  # Current/parent directory agents
    
    def _has_tier_precedence(self, tier1: str, tier2: str) -> bool:
        """
        Check if tier1 has precedence over tier2
        
        Args:
            tier1: First tier
            tier2: Second tier
            
        Returns:
            True if tier1 has precedence
        """
        precedence_order = ['project', 'user', 'system']
        try:
            return precedence_order.index(tier1) < precedence_order.index(tier2)
        except ValueError:
            return False
    
    async def _validate_agents(self, agents: Dict[str, AgentMetadata]) -> Dict[str, AgentMetadata]:
        """
        Validate discovered agents for correctness
        
        Args:
            agents: Dictionary of agents to validate
            
        Returns:
            Validated agents dictionary
        """
        validated = {}
        
        for name, metadata in agents.items():
            try:
                # Basic file validation
                if not Path(metadata.path).exists():
                    metadata.validated = False
                    metadata.error_message = "File not found"
                    continue
                
                # Syntax validation (basic Python syntax check)
                try:
                    with open(metadata.path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, metadata.path, 'exec')
                    metadata.validated = True
                    metadata.error_message = None
                except SyntaxError as e:
                    metadata.validated = False
                    metadata.error_message = f"Syntax error: {e}"
                
                validated[name] = metadata
                
            except Exception as e:
                logger.warning(f"Validation error for agent {name}: {e}")
                metadata.validated = False
                metadata.error_message = str(e)
                validated[name] = metadata
        
        return validated
    
    def _is_discovery_cache_valid(self) -> bool:
        """Check if discovery cache is still valid"""
        if self.last_discovery_time is None:
            return False
        return (time.time() - self.last_discovery_time) < self.discovery_cache_ttl
    
    async def get_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """
        Get specific agent metadata
        
        Args:
            agent_name: Name of agent to retrieve
            
        Returns:
            AgentMetadata or None if not found
        """
        if not self.registry:
            await self.discover_agents()
        
        return self.registry.get(agent_name)
    
    async def list_agents(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """
        List agents with optional filtering
        
        Args:
            agent_type: Filter by agent type
            tier: Filter by hierarchy tier
            
        Returns:
            List of matching AgentMetadata
        """
        if not self.registry:
            await self.discover_agents()
        
        agents = list(self.registry.values())
        
        if agent_type:
            agents = [a for a in agents if a.type == agent_type]
        
        if tier:
            agents = [a for a in agents if a.tier == tier]
        
        return agents
    
    async def get_agent_types(self) -> Set[str]:
        """
        Get all discovered agent types
        
        Returns:
            Set of agent types
        """
        if not self.registry:
            await self.discover_agents()
        
        return {metadata.type for metadata in self.registry.values()}
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics and metrics
        
        Returns:
            Dictionary of registry statistics
        """
        if not self.registry:
            await self.discover_agents()
        
        stats = {
            'total_agents': len(self.registry),
            'validated_agents': len([a for a in self.registry.values() if a.validated]),
            'failed_agents': len([a for a in self.registry.values() if not a.validated]),
            'agent_types': len(await self.get_agent_types()),
            'agents_by_tier': {},
            'agents_by_type': {},
            'last_discovery': self.last_discovery_time,
            'discovery_paths': [str(p) for p in self.discovery_paths]
        }
        
        # Count by tier
        for metadata in self.registry.values():
            tier = metadata.tier
            stats['agents_by_tier'][tier] = stats['agents_by_tier'].get(tier, 0) + 1
        
        # Count by type
        for metadata in self.registry.values():
            agent_type = metadata.type
            stats['agents_by_type'][agent_type] = stats['agents_by_type'].get(agent_type, 0) + 1
        
        return stats
    
    async def refresh_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """
        Refresh specific agent metadata
        
        Args:
            agent_name: Name of agent to refresh
            
        Returns:
            Updated AgentMetadata or None if not found
        """
        if agent_name not in self.registry:
            return None
        
        current_metadata = self.registry[agent_name]
        agent_file = Path(current_metadata.path)
        
        if not agent_file.exists():
            # Agent file removed
            del self.registry[agent_name]
            return None
        
        # Re-extract metadata
        updated_metadata = await self._extract_agent_metadata(agent_file, current_metadata.tier)
        if updated_metadata:
            # Validate updated agent
            validated = await self._validate_agents({agent_name: updated_metadata})
            if agent_name in validated:
                self.registry[agent_name] = validated[agent_name]
                return validated[agent_name]
        
        return None
    
    def clear_cache(self) -> None:
        """Clear discovery cache and force refresh on next access"""
        self.last_discovery_time = None
        self.registry.clear()
        # Clear cache entry synchronously
        self.cache_service.invalidate("agent_registry_discovery")