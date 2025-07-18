"""
Core Agent Loader - Synchronous agent loading for core services

This module provides simple, synchronous agent loading functionality
for core framework services. It focuses on reading agent profiles from
the filesystem without the overhead of async operations.

Key Features:
- Synchronous file operations for fast agent discovery
- Three-tier hierarchy support (Project → User → System)
- No async overhead for simple file reads
- Direct integration with core services
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AgentTier(Enum):
    """Agent hierarchy tiers."""
    PROJECT = "project"
    USER = "user"
    SYSTEM = "system"


@dataclass
class AgentProfile:
    """Simple agent profile for core services."""
    name: str
    tier: AgentTier
    path: Path
    content: str
    role: str = ""
    nickname: str = ""
    
    @property
    def profile_id(self) -> str:
        return f"{self.tier.value}:{self.name}"


class CoreAgentLoader:
    """
    Synchronous agent loader for core framework services.
    
    Provides simple, fast agent discovery and loading without async overhead.
    """
    
    def __init__(self, working_directory: Optional[Path] = None):
        """Initialize the core agent loader."""
        self.working_directory = Path(working_directory or os.getcwd())
        self.user_home = Path.home()
        self.framework_path = self._detect_framework_path()
        self.tier_paths: Dict[AgentTier, Path] = {}
        self._profile_cache: Dict[str, AgentProfile] = {}
        
        # Initialize tier paths
        self._initialize_tier_paths()
        
        logger.info(f"CoreAgentLoader initialized")
        logger.info(f"  Working directory: {self.working_directory}")
        logger.info(f"  Framework path: {self.framework_path}")
    
    def _detect_framework_path(self) -> Path:
        """Detect framework path containing agent-roles."""
        # Try environment variable first
        if framework_path := os.getenv('CLAUDE_PM_FRAMEWORK_PATH'):
            return Path(framework_path)
        
        # Method 1: Try to find from current file location
        current_file = Path(__file__)
        current_dir = current_file.parent
        
        # Go up until we find framework/agent-roles
        while current_dir != current_dir.parent:
            framework_dir = current_dir / 'framework'
            if framework_dir.exists() and (framework_dir / 'agent-roles').exists():
                return framework_dir
            
            # Also check if we're already in the framework directory
            agent_roles_dir = current_dir / 'agent-roles'
            if agent_roles_dir.exists():
                return current_dir
            
            # Check if we're at project root (has package.json)
            if (current_dir / 'package.json').exists():
                framework_dir = current_dir / 'framework'
                if framework_dir.exists():
                    return framework_dir
                # If no framework subdir, we might be in the framework itself
                if (current_dir / 'agent-roles').exists():
                    return current_dir
            
            current_dir = current_dir.parent
        
        # Method 2: Try common locations relative to working directory
        for possible_path in [
            self.working_directory / 'framework',
            self.working_directory.parent / 'framework',
            self.working_directory,  # Maybe we're already in framework
            Path.home() / 'Projects' / 'claude-multiagent-pm' / 'framework',
            Path('/Users/masa/Projects/claude-multiagent-pm/framework')  # Hardcoded fallback
        ]:
            if possible_path.exists() and (possible_path / 'agent-roles').exists():
                return possible_path
        
        # Method 3: Search for agent-roles directory
        logger.warning("Framework path detection struggling, searching for agent-roles...")
        
        # Start from current directory and search up
        search_dir = self.working_directory
        max_levels = 5
        level = 0
        
        while level < max_levels and search_dir != search_dir.parent:
            # Look for agent-roles in this directory and immediate subdirectories
            for item in search_dir.rglob('agent-roles'):
                if item.is_dir() and (item / 'engineer.md').exists():
                    # Found agent-roles with expected content
                    framework_path = item.parent
                    logger.info(f"Found framework path via search: {framework_path}")
                    return framework_path
            
            search_dir = search_dir.parent
            level += 1
        
        # Final fallback - use working directory
        logger.error(f"Could not detect framework path, using working directory: {self.working_directory}")
        return self.working_directory
    
    def _initialize_tier_paths(self) -> None:
        """Initialize paths for each tier."""
        # Project tier - current directory (highest precedence)
        project_path = self.working_directory / '.claude-pm' / 'agents' / 'project-specific'
        self.tier_paths[AgentTier.PROJECT] = project_path
        
        # User tier - user home directory
        user_path = self.user_home / '.claude-pm' / 'agents' / 'user-defined'
        self.tier_paths[AgentTier.USER] = user_path
        
        # System tier - framework agent-roles directory
        system_path = self.framework_path / 'agent-roles'
        if not system_path.exists():
            raise FileNotFoundError(
                f"System agents directory not found at {system_path}. "
                f"Framework path: {self.framework_path}"
            )
        self.tier_paths[AgentTier.SYSTEM] = system_path
        
        # Create project and user directories if they don't exist
        project_path.mkdir(parents=True, exist_ok=True)
        user_path.mkdir(parents=True, exist_ok=True)
    
    def load_agent_profile(self, agent_name: str) -> Optional[AgentProfile]:
        """
        Load agent profile synchronously.
        
        Args:
            agent_name: Name of agent to load
            
        Returns:
            AgentProfile if found, None otherwise
        """
        # Check cache first
        if agent_name in self._profile_cache:
            return self._profile_cache[agent_name]
        
        # Search through hierarchy (Project → User → System)
        for tier in [AgentTier.PROJECT, AgentTier.USER, AgentTier.SYSTEM]:
            profile = self._load_profile_from_tier(agent_name, tier)
            if profile:
                self._profile_cache[agent_name] = profile
                logger.debug(f"Loaded {agent_name} profile from {tier.value} tier")
                return profile
        
        # No profile found - throw error
        checked_paths = []
        for tier in [AgentTier.PROJECT, AgentTier.USER, AgentTier.SYSTEM]:
            tier_path = self.tier_paths[tier]
            checked_paths.append(f"{tier.value}: {tier_path}")
        
        error_msg = (
            f"Agent profile '{agent_name}' not found in any tier.\n"
            f"Searched paths:\n" + "\n".join(f"  - {path}" for path in checked_paths)
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    def _load_profile_from_tier(self, agent_name: str, tier: AgentTier) -> Optional[AgentProfile]:
        """Load profile from specific tier."""
        tier_path = self.tier_paths[tier]
        if not tier_path.exists():
            return None
        
        # Try different file naming conventions
        profile_files = [
            f"{agent_name}.md",
            f"{agent_name}-agent.md",
            f"{agent_name}_agent.md",
            f"{agent_name.replace('_', '-')}.md",
            f"{agent_name.replace('_', '-')}-agent.md"
        ]
        
        for filename in profile_files:
            profile_path = tier_path / filename
            if profile_path.exists():
                try:
                    content = profile_path.read_text(encoding='utf-8')
                    
                    # Extract basic info
                    role = self._extract_role(content)
                    nickname = self._get_nickname(agent_name)
                    
                    return AgentProfile(
                        name=agent_name,
                        tier=tier,
                        path=profile_path,
                        content=content,
                        role=role,
                        nickname=nickname
                    )
                except Exception as e:
                    logger.error(f"Error reading profile {profile_path}: {e}")
                    continue
        
        return None
    
    def _extract_role(self, content: str) -> str:
        """Extract role from profile content."""
        lines = content.split('\n')
        
        # Look for Primary Role section
        for i, line in enumerate(lines):
            if 'Primary Role' in line and (line.startswith('##') or line.startswith('**')):
                # Look for the next line with content
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('#'):
                        # Remove markdown formatting
                        role = next_line.replace('**', '').strip()
                        return role
        
        # Fallback: look for ## Role
        for i, line in enumerate(lines):
            if line.strip().startswith('## Role') or line.strip().startswith('# Role'):
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('#'):
                        return next_line.replace('**', '').strip()
        
        return "Specialized Agent"
    
    def _get_nickname(self, agent_name: str) -> str:
        """Get agent nickname."""
        nickname_map = {
            'engineer': 'Engineer',
            'documentation': 'Documenter',
            'qa': 'QA',
            'ops': 'Ops',
            'security': 'Security',
            'research': 'Researcher',
            'version_control': 'Versioner',
            'ticketing': 'Ticketer',
            'data': 'Data Engineer',
            'data_engineer': 'Data Engineer'
        }
        return nickname_map.get(agent_name, agent_name.title())
    
    def list_available_agents(self) -> Dict[str, List[str]]:
        """List all available agents by tier (synchronous)."""
        available_agents = {}
        
        for tier, tier_path in self.tier_paths.items():
            agents = []
            if tier_path.exists():
                for file in tier_path.glob("*.md"):
                    if not file.name.startswith('_'):
                        # Extract agent name from filename
                        agent_name = file.stem
                        if agent_name.endswith('-agent'):
                            agent_name = agent_name[:-6]
                        agent_name = agent_name.replace('-', '_')
                        agents.append(agent_name)
            
            available_agents[tier.value] = sorted(agents)
        
        return available_agents
    
    def build_task_prompt(self, agent_name: str, task_context: Dict[str, Any]) -> str:
        """
        Build Task Tool prompt for agent (synchronous).
        
        Args:
            agent_name: Name of agent
            task_context: Task context dictionary
            
        Returns:
            Complete Task Tool prompt
        """
        try:
            profile = self.load_agent_profile(agent_name)
            
            # Build the prompt
            prompt = f"""**{profile.nickname}**: {task_context.get('task_description', 'Task execution')}

TEMPORAL CONTEXT: {task_context.get('temporal_context', f"Today is {datetime.now().strftime('%B %d, %Y')}. Apply date awareness to task execution.")}

**Agent Profile Loaded**
- **Role**: {profile.role}
- **Source**: {profile.tier.value} tier ({profile.path.parent.name})

**Task**: {task_context.get('task_description', 'Execute assigned task')}

**Requirements**:
{chr(10).join(f"- {req}" for req in task_context.get('requirements', []))}

**Expected Deliverables**:
{chr(10).join(f"- {deliverable}" for deliverable in task_context.get('deliverables', []))}

**Context**: Full agent profile loaded from {profile.path}
**Authority**: As defined in agent profile
**Expected Results**: Complete all deliverables with high quality
**Escalation**: Return to PM orchestrator if blocked or need clarification

{task_context.get('integration_notes', '')}"""
            
            return prompt
            
        except FileNotFoundError:
            # Re-raise the error - no fallback
            raise