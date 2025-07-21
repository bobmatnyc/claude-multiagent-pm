"""Agent discovery and scanning functionality."""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import AgentMetadata
from .metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class AgentDiscovery:
    """Handles agent discovery across the file system hierarchy."""
    
    def __init__(self, metadata_extractor: MetadataExtractor):
        """Initialize agent discovery with metadata extractor."""
        self.metadata_extractor = metadata_extractor
        self.discovery_paths: List[Path] = []
        self._initialize_discovery_paths()
    
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
            logger.warning("Claude PM framework not available for system agent discovery")
        
        self.discovery_paths = paths
        logger.info(f"Initialized discovery paths: {[str(p) for p in paths]}")
    
    async def discover_agents(self) -> Dict[str, AgentMetadata]:
        """
        Discover all available agents across two-tier hierarchy.
        
        Returns:
            Dictionary of agent name -> AgentMetadata
        """
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
        
        return discovered_agents
    
    async def _scan_directory(self, directory: Path, tier: str) -> Dict[str, AgentMetadata]:
        """
        Scan directory for agent files and extract metadata.
        
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
                agent_metadata = await self.metadata_extractor.extract_agent_metadata(agent_file, tier)
                if agent_metadata:
                    agents[agent_metadata.name] = agent_metadata
            except Exception as e:
                logger.warning(f"Error processing agent file {agent_file}: {e}")
        
        return agents
    
    def _determine_tier(self, path: Path) -> str:
        """
        Determine hierarchy tier based on path.
        
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
        Check if tier1 has precedence over tier2.
        
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
    
    def get_discovery_paths(self) -> List[Path]:
        """Get current discovery paths."""
        return self.discovery_paths
    
    def add_discovery_path(self, path: Path) -> None:
        """Add a new discovery path."""
        if path not in self.discovery_paths:
            self.discovery_paths.append(path)
            logger.info(f"Added discovery path: {path}")