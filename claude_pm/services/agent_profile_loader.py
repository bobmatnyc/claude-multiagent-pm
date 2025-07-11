#!/usr/bin/env python3
"""
Agent Profile Loading Service

Provides standardized agent profile loading with three-tier hierarchy support:
- Project-specific profiles (.claude-pm/agents/project-specific/)
- User-defined profiles (~/.claude-pm/agents/user-defined/)
- System profiles (framework/agent-roles/)

Integrates with Task Tool for subprocess context enhancement.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProfileTier(Enum):
    """Agent profile hierarchy tiers with precedence order."""
    PROJECT = "project"      # Highest precedence
    USER = "user"           # Medium precedence  
    SYSTEM = "system"       # Lowest precedence (fallback)


@dataclass
class AgentProfile:
    """Standardized agent profile structure."""
    name: str
    tier: ProfileTier
    path: Path
    role: str
    capabilities: List[str]
    authority_scope: List[str]
    context_preferences: Dict[str, Any]
    escalation_triggers: List[str]
    coordination_protocols: Dict[str, str]
    content: str
    
    @property
    def profile_id(self) -> str:
        """Unique profile identifier."""
        return f"{self.tier.value}:{self.name}"


class AgentProfileLoader:
    """
    Agent Profile Loading Service with Three-Tier Hierarchy
    
    Loads agent profiles following precedence:
    1. Project-specific profiles (highest priority)
    2. User-defined profiles (medium priority)
    3. System profiles (fallback)
    """
    
    def __init__(self, working_directory: Optional[Path] = None):
        """Initialize profile loader with working directory context."""
        self.working_directory = Path(working_directory or os.getcwd())
        self.framework_path = self._detect_framework_path()
        self.user_home = Path.home()
        self._profile_cache: Dict[str, AgentProfile] = {}
        self._tier_paths: Dict[ProfileTier, Path] = {}
        
    def _detect_framework_path(self) -> Path:
        """Detect framework path from environment or deployment structure."""
        # Try environment variable first
        if framework_path := os.getenv('CLAUDE_PM_FRAMEWORK_PATH'):
            return Path(framework_path)
            
        # Try deployment directory
        if deployment_dir := os.getenv('CLAUDE_PM_DEPLOYMENT_DIR'):
            return Path(deployment_dir)
            
        # Try relative to current module
        current_dir = Path(__file__).parent.parent.parent
        if (current_dir / 'framework' / 'agent-roles').exists():
            return current_dir
            
        # Fallback to working directory parent
        return self.working_directory.parent
        
    async def initialize(self) -> None:
        """Initialize profile loader and discover tier paths."""
        self._tier_paths = {
            ProfileTier.PROJECT: self._get_project_profiles_path(),
            ProfileTier.USER: self._get_user_profiles_path(), 
            ProfileTier.SYSTEM: self._get_system_profiles_path()
        }
        
        logger.info(f"Profile loader initialized with paths:")
        for tier, path in self._tier_paths.items():
            exists = "✓" if path.exists() else "✗"
            logger.info(f"  {tier.value}: {path} {exists}")
            
    def _get_project_profiles_path(self) -> Path:
        """Get project-specific profiles directory."""
        return self.working_directory / '.claude-pm' / 'agents' / 'project-specific'
        
    def _get_user_profiles_path(self) -> Path:
        """Get user-defined profiles directory."""
        return self.user_home / '.claude-pm' / 'agents' / 'user-defined'
        
    def _get_system_profiles_path(self) -> Path:
        """Get system profiles directory."""
        return self.framework_path / 'framework' / 'agent-roles'
        
    async def load_profile(self, agent_name: str) -> Optional[AgentProfile]:
        """
        Load agent profile following three-tier hierarchy.
        
        Args:
            agent_name: Name of agent profile to load (e.g., 'engineer', 'documentation')
            
        Returns:
            AgentProfile if found, None otherwise
        """
        # Check cache first
        cache_key = f"profile:{agent_name}"
        if cache_key in self._profile_cache:
            return self._profile_cache[cache_key]
            
        # Search through hierarchy (Project → User → System)
        for tier in [ProfileTier.PROJECT, ProfileTier.USER, ProfileTier.SYSTEM]:
            if profile := await self._load_profile_from_tier(agent_name, tier):
                self._profile_cache[cache_key] = profile
                logger.debug(f"Loaded {agent_name} profile from {tier.value} tier")
                return profile
                
        logger.warning(f"No profile found for agent: {agent_name}")
        return None
        
    async def _load_profile_from_tier(self, agent_name: str, tier: ProfileTier) -> Optional[AgentProfile]:
        """Load profile from specific tier."""
        tier_path = self._tier_paths[tier]
        if not tier_path.exists():
            return None
            
        # Try different file naming conventions
        profile_files = [
            f"{agent_name}-agent.md",
            f"{agent_name}_agent.md", 
            f"{agent_name}.md",
            f"{agent_name}-profile.md"
        ]
        
        for filename in profile_files:
            profile_path = tier_path / filename
            if profile_path.exists():
                return await self._parse_profile_file(profile_path, tier)
                
        return None
        
    async def _parse_profile_file(self, profile_path: Path, tier: ProfileTier) -> AgentProfile:
        """Parse agent profile markdown file."""
        try:
            content = profile_path.read_text(encoding='utf-8')
            
            # Extract profile metadata
            name = self._extract_agent_name(profile_path.stem)
            role = self._extract_role(content)
            capabilities = self._extract_capabilities(content)
            authority_scope = self._extract_authority_scope(content)
            context_preferences = self._extract_context_preferences(content)
            escalation_triggers = self._extract_escalation_triggers(content)
            coordination_protocols = self._extract_coordination_protocols(content)
            
            return AgentProfile(
                name=name,
                tier=tier,
                path=profile_path,
                role=role,
                capabilities=capabilities,
                authority_scope=authority_scope,
                context_preferences=context_preferences,
                escalation_triggers=escalation_triggers,
                coordination_protocols=coordination_protocols,
                content=content
            )
            
        except Exception as e:
            logger.error(f"Error parsing profile {profile_path}: {e}")
            raise
            
    def _extract_agent_name(self, filename: str) -> str:
        """Extract agent name from filename."""
        # Remove common suffixes
        name = filename.lower()
        for suffix in ['-agent', '_agent', '-profile']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        return name
        
    def _extract_role(self, content: str) -> str:
        """Extract primary role from profile content."""
        # Look for role patterns
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('**Primary Role**') or line.startswith('## 🎯 Primary Role'):
                # Extract role from next line or same line
                if ':' in line:
                    return line.split(':', 1)[1].strip().strip('*')
                continue
            if line.startswith('**') and ('Role' in line or 'Specialist' in line):
                return line.strip('*').strip()
                
        return "Specialized Agent"
        
    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract capabilities from profile content."""
        capabilities = []
        in_capabilities_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect capabilities section
            if any(header in line.lower() for header in ['capabilities', 'responsibilities', 'functions']):
                in_capabilities_section = True
                continue
                
            # Stop at next major section
            if in_capabilities_section and line.startswith('#'):
                break
                
            # Extract capability items
            if in_capabilities_section and (line.startswith('-') or line.startswith('*')):
                capability = line.lstrip('-*').strip()
                if capability and not capability.startswith('#'):
                    capabilities.append(capability)
                    
        return capabilities[:10]  # Limit to top 10 capabilities
        
    def _extract_authority_scope(self, content: str) -> List[str]:
        """Extract authority scope from profile content."""
        authority = []
        in_authority_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect authority sections
            if any(header in line.lower() for header in ['authority', 'permissions', 'writing']):
                in_authority_section = True
                continue
                
            # Stop at next major section  
            if in_authority_section and line.startswith('#'):
                break
                
            # Extract authority items
            if in_authority_section and (line.startswith('-') or line.startswith('*')):
                auth_item = line.lstrip('-*').strip()
                if auth_item and not auth_item.startswith('#'):
                    authority.append(auth_item)
                    
        return authority[:8]  # Limit to top 8 authority items
        
    def _extract_context_preferences(self, content: str) -> Dict[str, Any]:
        """Extract context preferences from profile content."""
        preferences = {
            'memory_integration': 'pattern_memory' in content.lower(),
            'collaboration_style': 'coordinate' if 'coordinate' in content.lower() else 'independent',
            'escalation_preference': 'immediate' if 'immediate' in content.lower() else 'standard',
            'context_depth': 'comprehensive' if len(content) > 5000 else 'focused'
        }
        
        # Extract specific preferences
        if 'tdd' in content.lower():
            preferences['development_approach'] = 'test_driven'
        if 'api' in content.lower():
            preferences['api_focus'] = True
        if 'documentation' in content.lower():
            preferences['documentation_priority'] = 'high'
            
        return preferences
        
    def _extract_escalation_triggers(self, content: str) -> List[str]:
        """Extract escalation triggers from profile content."""
        triggers = []
        in_escalation_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect escalation section
            if 'escalation' in line.lower() and ('trigger' in line.lower() or 'alert' in line.lower()):
                in_escalation_section = True
                continue
                
            # Stop at next major section
            if in_escalation_section and line.startswith('#'):
                break
                
            # Extract trigger items
            if in_escalation_section and (line.startswith('-') or line.startswith('*')):
                trigger = line.lstrip('-*').strip()
                if trigger and not trigger.startswith('#'):
                    triggers.append(trigger)
                    
        return triggers[:6]  # Limit to top 6 triggers
        
    def _extract_coordination_protocols(self, content: str) -> Dict[str, str]:
        """Extract coordination protocols from profile content."""
        protocols = {}
        
        # Look for coordination patterns
        if 'architect agent' in content.lower():
            protocols['architect'] = 'API specifications, system design'
        if 'qa agent' in content.lower():
            protocols['qa'] = 'Test requirements, quality standards'
        if 'ops agent' in content.lower():
            protocols['ops'] = 'Deployment constraints, configuration'
        if 'research agent' in content.lower():
            protocols['research'] = 'Best practices, technology recommendations'
            
        return protocols
        
    async def list_available_profiles(self) -> Dict[ProfileTier, List[str]]:
        """List all available profiles by tier."""
        available_profiles = {tier: [] for tier in ProfileTier}
        
        for tier, tier_path in self._tier_paths.items():
            if not tier_path.exists():
                continue
                
            try:
                for profile_file in tier_path.glob('*.md'):
                    agent_name = self._extract_agent_name(profile_file.stem)
                    available_profiles[tier].append(agent_name)
            except Exception as e:
                logger.warning(f"Error listing profiles in {tier_path}: {e}")
                
        return available_profiles
        
    async def get_profile_hierarchy(self, agent_name: str) -> List[AgentProfile]:
        """Get all available profiles for an agent across all tiers."""
        profiles = []
        
        for tier in [ProfileTier.PROJECT, ProfileTier.USER, ProfileTier.SYSTEM]:
            if profile := await self._load_profile_from_tier(agent_name, tier):
                profiles.append(profile)
                
        return profiles
        
    def generate_subprocess_context(self, profile: AgentProfile, task_context: str = "") -> str:
        """
        Generate Task Tool subprocess context instruction with profile loading.
        
        Args:
            profile: Agent profile to load
            task_context: Specific task context for the subprocess
            
        Returns:
            Formatted context instruction for subprocess
        """
        context_instruction = f"""**{profile.role} Agent Profile Loaded**

**Agent Identity**: {profile.name.title()} Agent (Profile: {profile.tier.value})
**Primary Role**: {profile.role}

**Core Capabilities**:
{chr(10).join(f"- {cap}" for cap in profile.capabilities[:5])}

**Authority Scope**:
{chr(10).join(f"- {auth}" for auth in profile.authority_scope[:4])}

**Context Preferences**:
- Memory Integration: {'Enabled' if profile.context_preferences.get('memory_integration') else 'Standard'}
- Collaboration Style: {profile.context_preferences.get('collaboration_style', 'Coordinate').title()}
- Documentation Priority: {profile.context_preferences.get('documentation_priority', 'Standard').title()}

**Key Escalation Triggers**:
{chr(10).join(f"- {trigger}" for trigger in profile.escalation_triggers[:3])}

**Task Context**: {task_context}

**Profile Integration**: This subprocess operates with enhanced context from {profile.tier.value}-tier agent profile, providing specialized knowledge and capability awareness for optimal task execution.
"""
        return context_instruction
        
    async def create_profile_deployment_structure(self) -> Dict[str, bool]:
        """Create profile deployment directory structure."""
        results = {}
        
        for tier, tier_path in self._tier_paths.items():
            try:
                tier_path.mkdir(parents=True, exist_ok=True)
                results[f"{tier.value}_directory"] = True
                logger.info(f"Created {tier.value} profiles directory: {tier_path}")
            except Exception as e:
                results[f"{tier.value}_directory"] = False
                logger.error(f"Failed to create {tier.value} profiles directory: {e}")
                
        return results
        
    async def deploy_system_profiles(self) -> Dict[str, bool]:
        """Deploy system profiles to working directory if not present."""
        results = {}
        system_path = self._tier_paths[ProfileTier.SYSTEM]
        project_path = self._tier_paths[ProfileTier.PROJECT]
        
        if not system_path.exists():
            logger.warning(f"System profiles directory not found: {system_path}")
            return results
            
        # Ensure project directory exists
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Copy system profiles as project defaults if not present
        try:
            for profile_file in system_path.glob('*-agent.md'):
                target_file = project_path / profile_file.name
                
                if not target_file.exists():
                    target_file.write_text(profile_file.read_text(encoding='utf-8'))
                    results[profile_file.stem] = True
                    logger.info(f"Deployed system profile: {profile_file.name}")
                else:
                    results[profile_file.stem] = False  # Already exists
                    
        except Exception as e:
            logger.error(f"Error deploying system profiles: {e}")
            
        return results