#!/usr/bin/env python3
"""
Agent Prompt Builder - Proof of Concept
=======================================

This script demonstrates building agent prompts programmatically via the three-tier hierarchy system:
1. Project-specific agents (highest precedence)
2. User-defined agents (medium precedence)
3. System agents (fallback)

Key Features:
- Hierarchical agent file loading with precedence resolution
- Template variable substitution
- Task Tool integration format
- Memory collection requirements
- Context enhancement capabilities
- Error handling and fallback mechanisms

Usage:
    python scripts/agent_prompt_builder.py --agent engineer --task "Implement JWT authentication"
    python scripts/agent_prompt_builder.py --agent documentation --task "Update API docs"
    python scripts/agent_prompt_builder.py --list-agents
"""

import os
import sys
import json
import yaml
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import SharedPromptCache and AgentRegistry for performance optimization
try:
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from claude_pm.services.shared_prompt_cache import SharedPromptCache, cache_result
    from claude_pm.services.agent_registry import AgentRegistry, AgentMetadata
    SHARED_CACHE_AVAILABLE = True
    AGENT_REGISTRY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Services not available: {e}")
    SHARED_CACHE_AVAILABLE = False
    AGENT_REGISTRY_AVAILABLE = False
    
    # Fallback decorator
    def cache_result(key_pattern: str, ttl: Optional[float] = None, namespace: Optional[str] = None):
        def decorator(func):
            return func
        return decorator


class AgentTier(Enum):
    """Agent hierarchy tiers with precedence order."""
    PROJECT = "project"      # Highest precedence
    USER = "user"           # Medium precedence  
    SYSTEM = "system"       # Lowest precedence (fallback)


@dataclass
class AgentProfile:
    """Comprehensive agent profile structure."""
    name: str
    tier: AgentTier
    path: Path
    role: str
    capabilities: List[str] = field(default_factory=list)
    authority_scope: List[str] = field(default_factory=list)
    context_preferences: Dict[str, Any] = field(default_factory=dict)
    escalation_criteria: List[str] = field(default_factory=list)
    integration_patterns: Dict[str, str] = field(default_factory=dict)
    quality_standards: List[str] = field(default_factory=list)
    communication_style: Dict[str, str] = field(default_factory=dict)
    content: str = ""
    
    @property
    def profile_id(self) -> str:
        """Unique profile identifier."""
        return f"{self.tier.value}:{self.name}"
    
    @property
    def nickname(self) -> str:
        """Agent nickname for Task Tool integration."""
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
            'architect': 'Architect',
            'pm': 'PM',
            'orchestrator': 'Orchestrator'
        }
        return nickname_map.get(self.name, self.name.title())


@dataclass
class TaskContext:
    """Task context for prompt generation."""
    description: str
    temporal_context: str = ""
    specific_requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    expected_deliverables: List[str] = field(default_factory=list)
    memory_categories: List[str] = field(default_factory=list)
    priority: str = "medium"
    
    def __post_init__(self):
        """Set default temporal context."""
        if not self.temporal_context:
            self.temporal_context = f"Today is {datetime.now().strftime('%B %d, %Y')}. Apply date awareness to task execution."


class AgentPromptBuilder:
    """
    Agent Prompt Builder with Three-Tier Hierarchy Support
    
    Loads agent profiles following precedence:
    1. Project-specific profiles (highest priority)
    2. User-defined profiles (medium priority)
    3. System profiles (fallback)
    
    Generates complete agent prompts ready for Task Tool subprocess creation.
    """
    
    def __init__(self, working_directory: Optional[Path] = None):
        """Initialize prompt builder with working directory context."""
        self.working_directory = Path(working_directory or os.getcwd())
        self.framework_path = self._detect_framework_path()
        self.user_home = Path.home()
        self._profile_cache: Dict[str, AgentProfile] = {}
        self._hierarchy_config: Dict[str, Any] = {}
        self._tier_paths: Dict[AgentTier, Path] = {}
        
        # Initialize shared cache if available
        self._shared_cache = None
        if SHARED_CACHE_AVAILABLE:
            try:
                self._shared_cache = SharedPromptCache.get_instance({
                    "max_size": 500,  # Moderate cache size for prompt data
                    "max_memory_mb": 50,  # 50MB memory limit
                    "default_ttl": 1800,  # 30 minutes TTL for prompt data
                    "enable_metrics": True
                })
                logger.info("SharedPromptCache integration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize SharedPromptCache: {e}")
                self._shared_cache = None
        
        # Initialize AgentRegistry if available
        self._agent_registry = None
        if AGENT_REGISTRY_AVAILABLE:
            try:
                self._agent_registry = AgentRegistry(cache_service=self._shared_cache)
                logger.info("AgentRegistry integration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize AgentRegistry: {e}")
                self._agent_registry = None
        
        # Initialize tier paths
        self._initialize_tier_paths()
        
        # Load hierarchy configuration
        self._load_hierarchy_config()
        
        logger.info(f"AgentPromptBuilder initialized")
        logger.info(f"  Working directory: {self.working_directory}")
        logger.info(f"  Framework path: {self.framework_path}")
        logger.info(f"  Shared cache: {'enabled' if self._shared_cache else 'disabled'}")
        logger.info(f"  Agent registry: {'enabled' if self._agent_registry else 'disabled'}")
        for tier, path in self._tier_paths.items():
            exists = "✓" if path.exists() else "✗"
            logger.info(f"  {tier.value}: {path} {exists}")
    
    def _detect_framework_path(self) -> Path:
        """Detect framework path from environment or deployment structure."""
        # Try environment variable first
        if framework_path := os.getenv('CLAUDE_PM_FRAMEWORK_PATH'):
            return Path(framework_path)
            
        # Try deployment directory
        if deployment_dir := os.getenv('CLAUDE_PM_DEPLOYMENT_DIR'):
            return Path(deployment_dir)
            
        # Try relative to current module
        current_dir = Path(__file__).parent.parent
        if (current_dir / 'framework' / 'agent-roles').exists():
            return current_dir
            
        # Fallback to working directory
        return self.working_directory
    
    def _initialize_tier_paths(self) -> None:
        """Initialize paths for each tier."""
        self._tier_paths = {
            AgentTier.PROJECT: self.working_directory / '.claude-pm' / 'agents' / 'project-specific',
            AgentTier.USER: self.working_directory / '.claude-pm' / 'agents' / 'user-defined',
            AgentTier.SYSTEM: self.working_directory / '.claude-pm' / 'agents' / 'system'
        }
        
        # Create directories if they don't exist
        for tier_path in self._tier_paths.values():
            tier_path.mkdir(parents=True, exist_ok=True)
    
    def _load_hierarchy_config(self) -> None:
        """Load hierarchy configuration from YAML file."""
        config_path = self.working_directory / '.claude-pm' / 'agents' / 'hierarchy.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self._hierarchy_config = yaml.safe_load(f)
                logger.debug(f"Loaded hierarchy config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load hierarchy config: {e}")
                self._hierarchy_config = {}
        else:
            logger.warning(f"No hierarchy config found at {config_path}")
            self._hierarchy_config = {}
    
    def list_available_agents(self) -> Dict[AgentTier, List[str]]:
        """List all available agents by tier."""
        # Use AgentRegistry if available for enhanced discovery
        if self._agent_registry:
            return self._list_agents_via_registry()
        
        # Fallback to legacy directory scanning
        return self._list_agents_legacy()
    
    def _list_agents_via_registry(self) -> Dict[AgentTier, List[str]]:
        """List agents using AgentRegistry for enhanced discovery."""
        available_agents = {tier: [] for tier in AgentTier}
        
        try:
            import asyncio
            # Get registry statistics for comprehensive agent discovery
            registry_stats = asyncio.run(self._agent_registry.get_registry_stats())
            
            # Get all discovered agents
            all_agents = asyncio.run(self._agent_registry.list_agents())
            
            # Convert AgentMetadata to tier-based listing
            for agent_metadata in all_agents:
                # Map registry tiers to AgentTier enum
                if agent_metadata.tier == 'project':
                    tier = AgentTier.PROJECT
                elif agent_metadata.tier == 'user':
                    tier = AgentTier.USER
                elif agent_metadata.tier == 'system':
                    tier = AgentTier.SYSTEM
                else:
                    tier = AgentTier.USER  # Default fallback
                
                available_agents[tier].append(agent_metadata.name)
            
            logger.info(f"AgentRegistry discovered {len(all_agents)} agents across {len(registry_stats['agents_by_tier'])} tiers")
            
        except Exception as e:
            logger.warning(f"Error using AgentRegistry for discovery: {e}")
            # Fallback to legacy method
            return self._list_agents_legacy()
        
        return available_agents
    
    def _list_agents_legacy(self) -> Dict[AgentTier, List[str]]:
        """Legacy agent discovery via directory scanning."""
        available_agents = {tier: [] for tier in AgentTier}
        
        for tier, tier_path in self._tier_paths.items():
            if not tier_path.exists():
                continue
                
            try:
                # Look for .md files (agent profiles)
                for agent_file in tier_path.glob('*.md'):
                    agent_name = self._extract_agent_name(agent_file.stem)
                    available_agents[tier].append(agent_name)
                    
                # Look for .py files (agent implementations)
                for agent_file in tier_path.glob('*agent*.py'):
                    if not agent_file.stem.startswith('_'):
                        agent_name = self._extract_agent_name(agent_file.stem)
                        if agent_name not in available_agents[tier]:
                            available_agents[tier].append(agent_name)
                            
            except Exception as e:
                logger.warning(f"Error listing agents in {tier_path}: {e}")
                
        return available_agents
    
    def _extract_agent_name(self, filename: str) -> str:
        """Extract agent name from filename."""
        # Remove common suffixes
        name = filename.lower()
        for suffix in ['-agent', '_agent', '-profile']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        return name
    
    def load_agent_profile(self, agent_name: str) -> Optional[AgentProfile]:
        """
        Load agent profile following three-tier hierarchy.
        
        Args:
            agent_name: Name of agent profile to load (e.g., 'engineer', 'documentation')
            
        Returns:
            AgentProfile if found, None otherwise
        """
        # Check shared cache first if available
        if self._shared_cache:
            shared_cache_key = f"agent_profile:{agent_name}:{self.working_directory.name}"
            cached_profile = self._shared_cache.get(shared_cache_key)
            if cached_profile:
                logger.debug(f"Loaded {agent_name} profile from shared cache")
                return cached_profile
        
        # Check local cache
        cache_key = f"profile:{agent_name}"
        if cache_key in self._profile_cache:
            return self._profile_cache[cache_key]
            
        # Search through hierarchy (Project → User → System)
        for tier in [AgentTier.PROJECT, AgentTier.USER, AgentTier.SYSTEM]:
            if profile := self._load_profile_from_tier(agent_name, tier):
                # Cache in local cache
                self._profile_cache[cache_key] = profile
                
                # Cache in shared cache if available
                if self._shared_cache:
                    shared_cache_key = f"agent_profile:{agent_name}:{self.working_directory.name}"
                    self._shared_cache.set(shared_cache_key, profile, ttl=1800)  # 30 minutes
                
                logger.debug(f"Loaded {agent_name} profile from {tier.value} tier")
                return profile
                
        logger.warning(f"No profile found for agent: {agent_name}")
        return None
    
    def _load_profile_from_tier(self, agent_name: str, tier: AgentTier) -> Optional[AgentProfile]:
        """Load profile from specific tier."""
        tier_path = self._tier_paths[tier]
        if not tier_path.exists():
            return None
            
        # Try different file naming conventions
        profile_files = [
            f"{agent_name}.md",
            f"{agent_name}-agent.md",
            f"{agent_name}_agent.md", 
            f"{agent_name}-profile.md",
            # Special case for capital letter naming
            f"{agent_name.title()}.md"
        ]
        
        for filename in profile_files:
            profile_path = tier_path / filename
            if profile_path.exists():
                return self._parse_profile_file(profile_path, tier)
                
        return None
    
    def _parse_profile_file(self, profile_path: Path, tier: AgentTier) -> AgentProfile:
        """Parse agent profile markdown file."""
        try:
            content = profile_path.read_text(encoding='utf-8')
            
            # Extract profile metadata
            name = self._extract_agent_name(profile_path.stem)
            role = self._extract_role(content)
            capabilities = self._extract_capabilities(content)
            authority_scope = self._extract_authority_scope(content)
            context_preferences = self._extract_context_preferences(content)
            escalation_criteria = self._extract_escalation_criteria(content)
            integration_patterns = self._extract_integration_patterns(content)
            quality_standards = self._extract_quality_standards(content)
            communication_style = self._extract_communication_style(content)
            
            return AgentProfile(
                name=name,
                tier=tier,
                path=profile_path,
                role=role,
                capabilities=capabilities,
                authority_scope=authority_scope,
                context_preferences=context_preferences,
                escalation_criteria=escalation_criteria,
                integration_patterns=integration_patterns,
                quality_standards=quality_standards,
                communication_style=communication_style,
                content=content
            )
            
        except Exception as e:
            logger.error(f"Error parsing profile {profile_path}: {e}")
            raise
    
    def _extract_role(self, content: str) -> str:
        """Extract primary role from profile content."""
        # Look for role patterns
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('## Role') or line.startswith('# Role'):
                # Look for next non-empty line
                lines = content.split('\n')
                idx = lines.index(line)
                for i in range(idx + 1, len(lines)):
                    next_line = lines[i].strip()
                    if next_line and not next_line.startswith('#'):
                        return next_line
            elif line.startswith('**Role**:') or line.startswith('**Primary Role**:'):
                return line.split(':', 1)[1].strip().strip('*')
                
        return "Specialized Agent"
    
    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract capabilities from profile content."""
        capabilities = []
        in_capabilities_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect capabilities section
            if any(header in line.lower() for header in ['## capabilities', '## core capabilities', 
                                                         '## responsibilities', '## functions']):
                in_capabilities_section = True
                continue
                
            # Stop at next major section
            if in_capabilities_section and line.startswith('##'):
                break
                
            # Extract capability items
            if in_capabilities_section and line.startswith('- **'):
                # Extract from "- **Name**: Description" format
                capability = line[4:].split('**:')[0].strip('*')
                if capability:
                    capabilities.append(capability)
            elif in_capabilities_section and (line.startswith('- ') or line.startswith('* ')):
                capability = line[2:].strip()
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
            if any(header in line.lower() for header in ['## authority', '## authority scope', 
                                                         '## permissions', '## writing']):
                in_authority_section = True
                continue
                
            # Stop at next major section  
            if in_authority_section and line.startswith('##'):
                break
                
            # Extract authority items
            if in_authority_section and line.startswith('- **'):
                # Extract from "- **Name**: Description" format
                auth_item = line[4:].split('**:')[0].strip('*')
                if auth_item:
                    authority.append(auth_item)
            elif in_authority_section and (line.startswith('- ') or line.startswith('* ')):
                auth_item = line[2:].strip()
                if auth_item and not auth_item.startswith('#'):
                    authority.append(auth_item)
                    
        return authority[:8]  # Limit to top 8 authority items
    
    def _extract_context_preferences(self, content: str) -> Dict[str, Any]:
        """Extract context preferences from profile content."""
        preferences = {}
        in_context_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect context preferences section
            if any(header in line.lower() for header in ['## context preferences', '## context']):
                in_context_section = True
                continue
                
            # Stop at next major section
            if in_context_section and line.startswith('##'):
                break
                
            # Extract preferences
            if in_context_section and line.startswith('- **'):
                # Extract from "- **Include**: Description" format
                parts = line[4:].split('**:', 1)
                if len(parts) == 2:
                    key = parts[0].strip('*').lower().replace(' ', '_')
                    value = parts[1].strip()
                    preferences[key] = value
                    
        return preferences
    
    def _extract_escalation_criteria(self, content: str) -> List[str]:
        """Extract escalation criteria from profile content."""
        criteria = []
        in_escalation_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect escalation section
            if any(header in line.lower() for header in ['## escalation', '## escalation criteria']):
                in_escalation_section = True
                continue
                
            # Stop at next major section
            if in_escalation_section and line.startswith('##'):
                break
                
            # Extract criteria items
            if in_escalation_section and line.startswith('- **'):
                # Extract from "- **Name**: Description" format
                criterion = line[4:].split('**:')[0].strip('*')
                if criterion:
                    criteria.append(criterion)
            elif in_escalation_section and (line.startswith('- ') or line.startswith('* ')):
                criterion = line[2:].strip()
                if criterion and not criterion.startswith('#'):
                    criteria.append(criterion)
                    
        return criteria[:6]  # Limit to top 6 criteria
    
    def _extract_integration_patterns(self, content: str) -> Dict[str, str]:
        """Extract integration patterns from profile content."""
        patterns = {}
        in_integration_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect integration section
            if any(header in line.lower() for header in ['## integration', '## integration patterns']):
                in_integration_section = True
                continue
                
            # Stop at next major section
            if in_integration_section and line.startswith('##'):
                break
                
            # Extract patterns
            if in_integration_section and line.startswith('- **With '):
                # Extract from "- **With QA**: Description" format
                parts = line[9:].split('**:', 1)
                if len(parts) == 2:
                    agent = parts[0].strip().lower()
                    description = parts[1].strip()
                    patterns[agent] = description
                    
        return patterns
    
    def _extract_quality_standards(self, content: str) -> List[str]:
        """Extract quality standards from profile content."""
        standards = []
        in_standards_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect standards section
            if any(header in line.lower() for header in ['## quality standards', '## quality']):
                in_standards_section = True
                continue
                
            # Stop at next major section
            if in_standards_section and line.startswith('##'):
                break
                
            # Extract standards items
            if in_standards_section and line.startswith('- **'):
                # Extract from "- **Name**: Description" format
                standard = line[4:].split('**:')[0].strip('*')
                if standard:
                    standards.append(standard)
            elif in_standards_section and (line.startswith('- ') or line.startswith('* ')):
                standard = line[2:].strip()
                if standard and not standard.startswith('#'):
                    standards.append(standard)
                    
        return standards[:5]  # Limit to top 5 standards
    
    def _extract_communication_style(self, content: str) -> Dict[str, str]:
        """Extract communication style from profile content."""
        style = {}
        in_communication_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Detect communication section
            if any(header in line.lower() for header in ['## communication', '## communication style']):
                in_communication_section = True
                continue
                
            # Stop at next major section
            if in_communication_section and line.startswith('##'):
                break
                
            # Extract style items
            if in_communication_section and line.startswith('- **'):
                # Extract from "- **Updates**: Description" format
                parts = line[4:].split('**:', 1)
                if len(parts) == 2:
                    key = parts[0].strip('*').lower()
                    value = parts[1].strip()
                    style[key] = value
                    
        return style
    
    def build_task_tool_prompt(self, agent_name: str, task_context: TaskContext) -> str:
        """
        Build complete Task Tool subprocess prompt with agent profile integration.
        
        Args:
            agent_name: Name of agent to load
            task_context: Task context and requirements
            
        Returns:
            Complete formatted prompt ready for Task Tool subprocess creation
        """
        # Check shared cache for complete prompt first
        if self._shared_cache:
            prompt_cache_key = f"task_prompt:{agent_name}:{hash(str(task_context))}"
            cached_prompt = self._shared_cache.get(prompt_cache_key)
            if cached_prompt:
                logger.debug(f"Retrieved cached prompt for {agent_name}")
                return cached_prompt
        
        # Load agent profile
        profile = self.load_agent_profile(agent_name)
        if not profile:
            raise ValueError(f"No profile found for agent: {agent_name}")
        
        # Build prompt
        prompt = self._generate_task_tool_prompt(profile, task_context)
        
        # Cache the generated prompt if shared cache is available
        if self._shared_cache:
            prompt_cache_key = f"task_prompt:{agent_name}:{hash(str(task_context))}"
            self._shared_cache.set(prompt_cache_key, prompt, ttl=600)  # 10 minutes TTL for prompts
        
        return prompt
    
    def _generate_task_tool_prompt(self, profile: AgentProfile, task_context: TaskContext) -> str:
        """Generate complete Task Tool prompt with profile integration."""
        
        # Set default memory categories if not provided
        if not task_context.memory_categories:
            task_context.memory_categories = self._get_default_memory_categories(profile.name)
        
        # Build the prompt
        prompt = f"""**{profile.nickname}**: {task_context.description} + MEMORY COLLECTION REQUIRED

TEMPORAL CONTEXT: {task_context.temporal_context}

**Agent Profile Integration**: 
- **Role**: {profile.role}
- **Tier**: {profile.tier.value.title()} ({profile.path.parent.name})
- **Profile ID**: {profile.profile_id}

**Core Capabilities**:
{chr(10).join(f"- {cap}" for cap in profile.capabilities[:5])}

**Authority Scope**:
{chr(10).join(f"- {auth}" for auth in profile.authority_scope[:4])}

**Task Requirements**:
{chr(10).join(f"- {req}" for req in task_context.specific_requirements)}

**Context Preferences**:
{chr(10).join(f"- {key.replace('_', ' ').title()}: {value}" for key, value in profile.context_preferences.items())}

**Quality Standards**:
{chr(10).join(f"- {std}" for std in profile.quality_standards[:3])}

**Integration Patterns**:
{chr(10).join(f"- With {agent.title()}: {desc}" for agent, desc in profile.integration_patterns.items())}

**Escalation Criteria**:
{chr(10).join(f"- {crit}" for crit in profile.escalation_criteria[:3])}

**Expected Deliverables**:
{chr(10).join(f"- {deliverable}" for deliverable in task_context.expected_deliverables)}

**Dependencies**:
{chr(10).join(f"- {dep}" for dep in task_context.dependencies)}

**Authority**: {profile.role} operations + memory collection
**Memory Categories**: {', '.join(task_context.memory_categories)}
**Priority**: {task_context.priority}

**Profile-Enhanced Context**: This subprocess operates with enhanced context from {profile.tier.value}-tier agent profile, providing specialized knowledge and capability awareness for optimal task execution.
"""
        
        return prompt
    
    def _get_default_memory_categories(self, agent_name: str) -> List[str]:
        """Get default memory categories for agent type."""
        category_map = {
            'engineer': ['bug', 'error:runtime', 'error:logic', 'architecture:design'],
            'documentation': ['feedback:documentation', 'architecture:design', 'performance'],
            'qa': ['bug', 'error:integration', 'performance', 'qa'],
            'ops': ['error:deployment', 'performance', 'architecture:design'],
            'security': ['error:security', 'bug', 'architecture:design'],
            'research': ['architecture:design', 'feedback:research', 'performance'],
            'version_control': ['error:integration', 'bug', 'architecture:design'],
            'ticketing': ['bug', 'feedback:workflow', 'architecture:design'],
            'data': ['error:integration', 'bug', 'architecture:design', 'performance']
        }
        
        return category_map.get(agent_name, ['bug', 'feedback', 'architecture:design'])
    
    def create_deployment_structure(self) -> Dict[str, bool]:
        """Create agent deployment directory structure."""
        results = {}
        
        for tier, tier_path in self._tier_paths.items():
            try:
                tier_path.mkdir(parents=True, exist_ok=True)
                
                # Create __init__.py for project tier
                if tier == AgentTier.PROJECT:
                    init_file = tier_path / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text('"""Project-specific agent implementations."""\n')
                
                # Create templates directory
                templates_dir = tier_path / "templates"
                templates_dir.mkdir(exist_ok=True)
                
                # Create config directory for project tier
                if tier == AgentTier.PROJECT:
                    config_dir = tier_path / "config"
                    config_dir.mkdir(exist_ok=True)
                    init_file = config_dir / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text('"""Agent configuration files."""\n')
                
                results[f"{tier.value}_directory"] = True
                logger.info(f"Created {tier.value} agent directory: {tier_path}")
                
            except Exception as e:
                results[f"{tier.value}_directory"] = False
                logger.error(f"Failed to create {tier.value} agent directory: {e}")
                
        return results
    
    def get_profile_hierarchy(self, agent_name: str) -> List[AgentProfile]:
        """Get all available profiles for an agent across all tiers."""
        profiles = []
        
        for tier in [AgentTier.PROJECT, AgentTier.USER, AgentTier.SYSTEM]:
            if profile := self._load_profile_from_tier(agent_name, tier):
                profiles.append(profile)
                
        return profiles
    
    def validate_hierarchy(self) -> Dict[str, Any]:
        """Validate agent hierarchy consistency."""
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "summary": {
                "total_agents": 0,
                "by_tier": {}
            }
        }
        
        try:
            available_agents = self.list_available_agents()
            
            for tier, agents in available_agents.items():
                validation_results["summary"]["by_tier"][tier.value] = len(agents)
                validation_results["summary"]["total_agents"] += len(agents)
                
                # Check for duplicate agent types across tiers
                for agent in agents:
                    profile = self.load_agent_profile(agent)
                    if profile and profile.tier != tier:
                        validation_results["warnings"].append(
                            f"Agent {agent} loaded from {profile.tier.value} tier instead of {tier.value}"
                        )
            
            # Check for missing essential agents
            essential_agents = ["engineer", "documentation", "qa", "ops", "security"]
            for agent_type in essential_agents:
                if not self.load_agent_profile(agent_type):
                    validation_results["warnings"].append(
                        f"Missing essential agent type: {agent_type}"
                    )
            
            # Check directory structure
            for tier, tier_path in self._tier_paths.items():
                if not tier_path.exists():
                    validation_results["issues"].append(f"Missing directory: {tier_path}")
                    validation_results["valid"] = False
                    
        except Exception as e:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Validation error: {str(e)}")
            
        return validation_results
    
    def invalidate_cache(self, agent_name: Optional[str] = None) -> None:
        """
        Invalidate cache entries for specific agent or all agents.
        
        Args:
            agent_name: Specific agent to invalidate, or None for all agents
        """
        if agent_name:
            # Invalidate local cache
            cache_key = f"profile:{agent_name}"
            self._profile_cache.pop(cache_key, None)
            
            # Invalidate shared cache
            if self._shared_cache:
                self._shared_cache.invalidate(f"agent_profile:{agent_name}:*")
                self._shared_cache.invalidate(f"task_prompt:{agent_name}:*")
            
            logger.info(f"Invalidated cache for agent: {agent_name}")
        else:
            # Clear all local cache
            self._profile_cache.clear()
            
            # Clear all shared cache
            if self._shared_cache:
                self._shared_cache.invalidate("agent_profile:*")
                self._shared_cache.invalidate("task_prompt:*")
            
            logger.info("Invalidated all agent caches")
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        metrics = {
            "local_cache_size": len(self._profile_cache),
            "shared_cache_available": self._shared_cache is not None,
            "shared_cache_metrics": None
        }
        
        if self._shared_cache:
            metrics["shared_cache_metrics"] = self._shared_cache.get_metrics()
        
        return metrics
    
    async def list_agents_detailed(self) -> Dict[str, Dict[str, Any]]:
        """
        List all agents with detailed metadata using AgentRegistry.
        
        Returns:
            Dictionary mapping agent names to detailed metadata
        """
        if not self._agent_registry:
            logger.warning("AgentRegistry not available for detailed listing")
            return {}
        
        try:
            # Discover all agents
            await self._agent_registry.discover_agents()
            
            # Get registry statistics
            stats = await self._agent_registry.get_registry_stats()
            
            # Get all agents with metadata
            all_agents = await self._agent_registry.list_agents()
            
            detailed_agents = {}
            for agent_metadata in all_agents:
                detailed_agents[agent_metadata.name] = {
                    'name': agent_metadata.name,
                    'type': agent_metadata.type,
                    'tier': agent_metadata.tier,
                    'path': agent_metadata.path,
                    'description': agent_metadata.description,
                    'version': agent_metadata.version,
                    'capabilities': agent_metadata.capabilities,
                    'validated': agent_metadata.validated,
                    'error_message': agent_metadata.error_message,
                    'file_size': agent_metadata.file_size,
                    'last_modified': agent_metadata.last_modified
                }
            
            return detailed_agents
            
        except Exception as e:
            logger.error(f"Error getting detailed agent listing: {e}")
            return {}
    
    def get_registry_integration_status(self) -> Dict[str, Any]:
        """Get status of AgentRegistry integration."""
        status = {
            'agent_registry_available': self._agent_registry is not None,
            'shared_cache_available': self._shared_cache is not None,
            'discovery_method': 'registry' if self._agent_registry else 'legacy',
            'performance_optimization': 'enabled' if self._shared_cache else 'disabled'
        }
        
        if self._agent_registry:
            try:
                import asyncio
                stats = asyncio.run(self._agent_registry.get_registry_stats())
                status['registry_stats'] = stats
            except Exception as e:
                status['registry_stats_error'] = str(e)
        
        return status


def main():
    """Main entry point for the agent prompt builder."""
    parser = argparse.ArgumentParser(description='Agent Prompt Builder - Build agent prompts via script calls')
    parser.add_argument('--agent', type=str, help='Agent name to build prompt for')
    parser.add_argument('--task', type=str, help='Task description')
    parser.add_argument('--requirements', type=str, nargs='*', help='Specific requirements')
    parser.add_argument('--deliverables', type=str, nargs='*', help='Expected deliverables')
    parser.add_argument('--dependencies', type=str, nargs='*', help='Task dependencies')
    parser.add_argument('--priority', type=str, choices=['low', 'medium', 'high'], default='medium', help='Task priority')
    parser.add_argument('--memory-categories', type=str, nargs='*', help='Memory categories')
    parser.add_argument('--list-agents', action='store_true', help='List all available agents')
    parser.add_argument('--list-agents-detailed', action='store_true', help='List agents with detailed metadata via AgentRegistry')
    parser.add_argument('--registry-status', action='store_true', help='Show AgentRegistry integration status')
    parser.add_argument('--validate', action='store_true', help='Validate agent hierarchy')
    parser.add_argument('--create-structure', action='store_true', help='Create deployment structure')
    parser.add_argument('--working-dir', type=str, help='Working directory path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize builder
    working_dir = Path(args.working_dir) if args.working_dir else None
    builder = AgentPromptBuilder(working_dir)
    
    try:
        if args.list_agents:
            # List all available agents
            agents = builder.list_available_agents()
            print("\n🤖 Available Agents by Tier:")
            print("=" * 50)
            
            for tier, agent_list in agents.items():
                print(f"\n{tier.value.upper()} TIER:")
                if agent_list:
                    for agent in sorted(agent_list):
                        profile = builder.load_agent_profile(agent)
                        if profile:
                            print(f"  ✓ {agent} - {profile.role}")
                        else:
                            print(f"  ✗ {agent} - Profile not found")
                else:
                    print("  (No agents found)")
        
        elif args.list_agents_detailed:
            # List agents with detailed metadata
            import asyncio
            detailed_agents = asyncio.run(builder.list_agents_detailed())
            print("\n🔍 Detailed Agent Registry:")
            print("=" * 50)
            
            if detailed_agents:
                for agent_name, metadata in detailed_agents.items():
                    print(f"\n📁 {agent_name} ({metadata['type']})")
                    print(f"  Tier: {metadata['tier']}")
                    print(f"  Path: {metadata['path']}")
                    print(f"  Description: {metadata['description'] or 'No description'}")
                    print(f"  Version: {metadata['version'] or 'Unknown'}")
                    print(f"  Validated: {'✓' if metadata['validated'] else '✗'}")
                    if metadata['error_message']:
                        print(f"  Error: {metadata['error_message']}")
                    if metadata['capabilities']:
                        print(f"  Capabilities: {', '.join(metadata['capabilities'][:3])}...")
                    print(f"  File Size: {metadata['file_size']} bytes")
            else:
                print("No agents found via AgentRegistry")
        
        elif args.registry_status:
            # Show registry integration status
            status = builder.get_registry_integration_status()
            print("\n🏗️ AgentRegistry Integration Status:")
            print("=" * 50)
            
            print(f"Agent Registry Available: {'✓' if status['agent_registry_available'] else '✗'}")
            print(f"Shared Cache Available: {'✓' if status['shared_cache_available'] else '✗'}")
            print(f"Discovery Method: {status['discovery_method']}")
            print(f"Performance Optimization: {status['performance_optimization']}")
            
            if 'registry_stats' in status:
                stats = status['registry_stats']
                print(f"\nRegistry Statistics:")
                print(f"  Total Agents: {stats['total_agents']}")
                print(f"  Validated Agents: {stats['validated_agents']}")
                print(f"  Failed Agents: {stats['failed_agents']}")
                print(f"  Agent Types: {stats['agent_types']}")
                print(f"  Discovery Paths: {len(stats['discovery_paths'])}")
                
                if stats['agents_by_tier']:
                    print(f"  Agents by Tier:")
                    for tier, count in stats['agents_by_tier'].items():
                        print(f"    {tier}: {count}")
                
                if stats['agents_by_type']:
                    print(f"  Agents by Type:")
                    for agent_type, count in stats['agents_by_type'].items():
                        print(f"    {agent_type}: {count}")
            
            if 'registry_stats_error' in status:
                print(f"Registry Stats Error: {status['registry_stats_error']}")
            
        elif args.validate:
            # Validate hierarchy
            validation = builder.validate_hierarchy()
            print("\n🔍 Agent Hierarchy Validation:")
            print("=" * 50)
            
            if validation["valid"]:
                print("✓ Hierarchy is valid")
            else:
                print("✗ Hierarchy has issues")
            
            print(f"\nSummary: {validation['summary']['total_agents']} total agents")
            for tier, count in validation["summary"]["by_tier"].items():
                print(f"  {tier}: {count} agents")
            
            if validation["issues"]:
                print("\nIssues:")
                for issue in validation["issues"]:
                    print(f"  ✗ {issue}")
            
            if validation["warnings"]:
                print("\nWarnings:")
                for warning in validation["warnings"]:
                    print(f"  ⚠ {warning}")
        
        elif args.create_structure:
            # Create deployment structure
            results = builder.create_deployment_structure()
            print("\n🏗️ Deployment Structure Creation:")
            print("=" * 50)
            
            for operation, success in results.items():
                status = "✓" if success else "✗"
                print(f"  {status} {operation}")
        
        elif args.agent and args.task:
            # Build agent prompt
            task_context = TaskContext(
                description=args.task,
                specific_requirements=args.requirements or [],
                expected_deliverables=args.deliverables or [],
                dependencies=args.dependencies or [],
                priority=args.priority,
                memory_categories=args.memory_categories or []
            )
            
            prompt = builder.build_task_tool_prompt(args.agent, task_context)
            
            print("\n🤖 Generated Task Tool Prompt:")
            print("=" * 50)
            print(prompt)
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()