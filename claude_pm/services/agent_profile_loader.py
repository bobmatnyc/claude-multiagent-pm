#!/usr/bin/env python3
"""
Agent Profile Loader Service
===========================

Comprehensive agent profile loading service with enhanced prompt integration.
Implements three-tier hierarchy precedence and improved prompt system integration.

Key Features:
- Three-tier hierarchy precedence (Project → User → System)
- Improved prompt integration with training system
- SharedPromptCache integration for performance optimization
- AgentRegistry integration for enhanced discovery
- Training system integration for prompt improvement
- Task Tool subprocess creation enhancement
- Profile validation and error handling

Framework Version: 014
Implementation: 2025-07-15
"""

import os
import json
import yaml
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import tempfile
import shutil

from ..core.base_service import BaseService
from ..core.config import Config
from .shared_prompt_cache import SharedPromptCache, cache_result
from .agent_registry import AgentRegistry, AgentMetadata
from .prompt_template_manager import PromptTemplateManager, TemplateType
from .agent_training_integration import AgentTrainingIntegration

logger = logging.getLogger(__name__)


class ProfileTier(Enum):
    """Profile hierarchy tiers with precedence order."""
    PROJECT = "project"      # Highest precedence
    USER = "user"           # Medium precedence  
    SYSTEM = "system"       # Lowest precedence (fallback)


class ProfileStatus(Enum):
    """Profile status options."""
    ACTIVE = "active"
    IMPROVED = "improved"
    TRAINING = "training"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class ImprovedPrompt:
    """Enhanced prompt from training system."""
    agent_type: str
    original_prompt: str
    improved_prompt: str
    improvement_score: float
    training_session_id: str
    timestamp: datetime
    validation_metrics: Dict[str, Any] = field(default_factory=dict)
    deployment_ready: bool = False
    
    @property
    def prompt_id(self) -> str:
        """Unique prompt identifier."""
        return f"{self.agent_type}_{self.training_session_id}"


@dataclass
class AgentProfile:
    """Comprehensive agent profile with enhanced capabilities."""
    name: str
    tier: ProfileTier
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
    
    # Enhanced attributes for improved prompt integration
    prompt_template_id: Optional[str] = None
    improved_prompt: Optional[ImprovedPrompt] = None
    prompt_version: str = "1.0.0"
    training_enabled: bool = True
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    status: ProfileStatus = ProfileStatus.ACTIVE
    last_updated: datetime = field(default_factory=datetime.now)
    
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
            'data_engineer': 'Data Engineer',
            'architect': 'Architect',
            'pm': 'PM',
            'orchestrator': 'Orchestrator'
        }
        return nickname_map.get(self.name, self.name.title())
    
    @property
    def has_improved_prompt(self) -> bool:
        """Check if profile has improved prompt."""
        return self.improved_prompt is not None and self.improved_prompt.deployment_ready
    
    def get_effective_prompt(self) -> str:
        """Get the most effective prompt (improved or original)."""
        if self.has_improved_prompt:
            return self.improved_prompt.improved_prompt
        return self.content


class AgentProfileLoader(BaseService):
    """
    Comprehensive agent profile loading service with enhanced prompt integration.
    
    Features:
    - Three-tier hierarchy precedence (Project → User → System)
    - Improved prompt integration with training system
    - SharedPromptCache integration for performance optimization
    - AgentRegistry integration for enhanced discovery
    - Profile validation and error handling
    - Task Tool subprocess creation enhancement
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the agent profile loader."""
        super().__init__(name="agent_profile_loader", config=config)
        
        # Core configuration
        self.working_directory = Path(os.getcwd())
        self.framework_path = self._detect_framework_path()
        self.user_home = Path.home()
        
        # Service integrations
        self.shared_cache = None
        self.agent_registry = None
        self.prompt_template_manager = None
        self.training_integration = None
        
        # Profile storage
        self.profile_cache: Dict[str, AgentProfile] = {}
        self.improved_prompts_cache: Dict[str, ImprovedPrompt] = {}
        self.tier_paths: Dict[ProfileTier, Path] = {}
        
        # Performance metrics
        self.performance_metrics = {
            'profiles_loaded': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'improved_prompts_loaded': 0,
            'training_integrations': 0
        }
        
        # Initialize paths
        self._initialize_tier_paths()
        
        # Initialize training directory
        self.training_dir = self.user_home / '.claude-pm' / 'training'
        self.improved_prompts_dir = self.training_dir / 'agent-prompts'
        self.improved_prompts_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AgentProfileLoader initialized successfully")
        logger.info(f"  Working directory: {self.working_directory}")
        logger.info(f"  Framework path: {self.framework_path}")
        logger.info(f"  Training directory: {self.training_dir}")
    
    async def _initialize(self) -> None:
        """Initialize the service and its integrations."""
        logger.info("Initializing AgentProfileLoader service...")
        
        # Initialize SharedPromptCache
        try:
            self.shared_cache = SharedPromptCache.get_instance({
                "max_size": 1000,
                "max_memory_mb": 100,
                "default_ttl": 1800,
                "enable_metrics": True
            })
            logger.info("SharedPromptCache integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize SharedPromptCache: {e}")
            self.shared_cache = None
        
        # Initialize AgentRegistry
        try:
            self.agent_registry = AgentRegistry(cache_service=self.shared_cache)
            await self.agent_registry.discover_agents()
            logger.info("AgentRegistry integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize AgentRegistry: {e}")
            self.agent_registry = None
        
        # Initialize PromptTemplateManager
        try:
            self.prompt_template_manager = PromptTemplateManager()
            logger.info("PromptTemplateManager integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize PromptTemplateManager: {e}")
            self.prompt_template_manager = None
        
        # Initialize TrainingIntegration
        try:
            self.training_integration = AgentTrainingIntegration(self.config)
            logger.info("Training integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize training integration: {e}")
            self.training_integration = None
        
        # Load improved prompts
        await self._load_improved_prompts()
        
        logger.info("AgentProfileLoader service initialized successfully")
    
    async def _cleanup(self) -> None:
        """Cleanup service resources."""
        logger.info("Cleaning up AgentProfileLoader service...")
        
        # Clear caches
        self.profile_cache.clear()
        self.improved_prompts_cache.clear()
        
        # Stop training integration
        if self.training_integration:
            await self.training_integration.stop()
        
        logger.info("AgentProfileLoader service cleaned up")
    
    def _detect_framework_path(self) -> Path:
        """Detect framework path from environment or deployment structure."""
        # Try environment variable first
        if framework_path := os.getenv('CLAUDE_PM_FRAMEWORK_PATH'):
            return Path(framework_path)
            
        # Try deployment directory
        if deployment_dir := os.getenv('CLAUDE_PM_DEPLOYMENT_DIR'):
            return Path(deployment_dir)
            
        # Try to find framework directory with agent-roles
        current_dir = Path(__file__).parent.parent.parent  # Go up to project root
        framework_dir = current_dir / 'framework'
        if framework_dir.exists() and (framework_dir / 'agent-roles').exists():
            return framework_dir
            
        # Try relative to current module
        current_dir = Path(__file__).parent.parent
        if (current_dir / 'agent-roles').exists():
            return current_dir
        elif (current_dir / 'agents').exists():
            return current_dir
            
        # Fallback to working directory
        return self.working_directory
    
    def _initialize_tier_paths(self) -> None:
        """Initialize paths for each tier with proper precedence."""
        # Project tier - current directory (highest precedence)
        project_path = self.working_directory / '.claude-pm' / 'agents' / 'project-specific'
        self.tier_paths[ProfileTier.PROJECT] = project_path
        
        # User tier - user home directory (for trained/customized agents)
        user_path = self.user_home / '.claude-pm' / 'agents' / 'user-defined'
        self.tier_paths[ProfileTier.USER] = user_path
        
        # System tier - framework agent-roles directory (core system agents)
        system_path = self.framework_path / 'agent-roles'
        if not system_path.exists():
            raise FileNotFoundError(
                f"System agents directory not found at {system_path}. "
                f"Framework path: {self.framework_path}"
            )
        self.tier_paths[ProfileTier.SYSTEM] = system_path
        
        # Create project and user directories if they don't exist
        project_path.mkdir(parents=True, exist_ok=True)
        user_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized tier paths: {len(self.tier_paths)} tiers")
        for tier, path in self.tier_paths.items():
            exists = "✓" if path.exists() else "✗"
            logger.info(f"  {tier.value}: {path} {exists}")
    
    @cache_result("agent_profile:{agent_name}:{working_dir}", ttl=1800, namespace="profile_loader")
    async def load_agent_profile(self, agent_name: str, force_refresh: bool = False) -> Optional[AgentProfile]:
        """
        Load agent profile following three-tier hierarchy with improved prompt integration.
        
        Args:
            agent_name: Name of agent profile to load
            force_refresh: Force cache refresh
            
        Returns:
            AgentProfile if found, None otherwise
        """
        try:
            # Check local cache first (if not forcing refresh)
            if not force_refresh and agent_name in self.profile_cache:
                self.performance_metrics['cache_hits'] += 1
                return self.profile_cache[agent_name]
            
            self.performance_metrics['cache_misses'] += 1
            
            # Search through hierarchy (Project → User → System)
            for tier in [ProfileTier.PROJECT, ProfileTier.USER, ProfileTier.SYSTEM]:
                profile = await self._load_profile_from_tier(agent_name, tier)
                if profile:
                    # Check for improved prompt
                    await self._apply_improved_prompt(profile)
                    
                    # Cache the profile
                    self.profile_cache[agent_name] = profile
                    
                    # Update performance metrics
                    self.performance_metrics['profiles_loaded'] += 1
                    
                    logger.debug(f"Loaded {agent_name} profile from {tier.value} tier")
                    return profile
            
            # No profile found - this is an error condition
            checked_paths = []
            for tier in [ProfileTier.PROJECT, ProfileTier.USER, ProfileTier.SYSTEM]:
                tier_path = self.tier_paths[tier]
                checked_paths.append(f"{tier.value}: {tier_path}")
            
            error_msg = (
                f"Agent profile '{agent_name}' not found in any tier.\n"
                f"Searched paths:\n" + "\n".join(f"  - {path}" for path in checked_paths)
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        except FileNotFoundError:
            raise  # Re-raise FileNotFoundError
        except Exception as e:
            logger.error(f"Error loading profile for {agent_name}: {e}")
            raise RuntimeError(f"Failed to load agent profile '{agent_name}': {e}")
    
    async def _load_profile_from_tier(self, agent_name: str, tier: ProfileTier) -> Optional[AgentProfile]:
        """Load profile from specific tier."""
        tier_path = self.tier_paths[tier]
        if not tier_path.exists():
            return None
        
        # Try different file naming conventions
        profile_files = [
            f"{agent_name}.md",
            f"{agent_name}-agent.md",
            f"{agent_name}_agent.md", 
            f"{agent_name}-profile.md",
            f"{agent_name.title()}.md",
            f"{agent_name}.py",
            f"{agent_name}_agent.py"
        ]
        
        for filename in profile_files:
            profile_path = tier_path / filename
            if profile_path.exists():
                return await self._parse_profile_file(profile_path, tier)
        
        return None
    
    async def _parse_profile_file(self, profile_path: Path, tier: ProfileTier) -> AgentProfile:
        """Parse agent profile file with enhanced metadata extraction."""
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
            
            # Extract enhanced metadata
            prompt_template_id = self._extract_prompt_template_id(content)
            training_enabled = self._extract_training_enabled(content)
            
            # Get file statistics
            stat = profile_path.stat()
            
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
                content=content,
                prompt_template_id=prompt_template_id,
                training_enabled=training_enabled,
                performance_metrics={
                    'file_size': stat.st_size,
                    'last_modified': stat.st_mtime
                },
                last_updated=datetime.fromtimestamp(stat.st_mtime)
            )
            
        except Exception as e:
            logger.error(f"Error parsing profile {profile_path}: {e}")
            raise
    
    async def _apply_improved_prompt(self, profile: AgentProfile) -> None:
        """Apply improved prompt from training system if available."""
        try:
            # Check for improved prompt in cache
            improved_prompt = self.improved_prompts_cache.get(profile.name)
            
            if improved_prompt and improved_prompt.deployment_ready:
                profile.improved_prompt = improved_prompt
                profile.status = ProfileStatus.IMPROVED
                profile.prompt_version = f"{profile.prompt_version}-improved"
                
                logger.debug(f"Applied improved prompt for {profile.name} "
                           f"(improvement score: {improved_prompt.improvement_score})")
                
                self.performance_metrics['improved_prompts_loaded'] += 1
            
        except Exception as e:
            logger.error(f"Error applying improved prompt for {profile.name}: {e}")
    
    async def _load_improved_prompts(self) -> None:
        """Load improved prompts from training system."""
        try:
            if not self.improved_prompts_dir.exists():
                return
            
            # Load improved prompts from training directory
            for prompt_file in self.improved_prompts_dir.glob('*.json'):
                try:
                    with open(prompt_file, 'r') as f:
                        data = json.load(f)
                    
                    # Convert to ImprovedPrompt object
                    improved_prompt = ImprovedPrompt(
                        agent_type=data['agent_type'],
                        original_prompt=data['original_prompt'],
                        improved_prompt=data['improved_prompt'],
                        improvement_score=data['improvement_score'],
                        training_session_id=data['training_session_id'],
                        timestamp=datetime.fromisoformat(data['timestamp']),
                        validation_metrics=data.get('validation_metrics', {}),
                        deployment_ready=data.get('deployment_ready', False)
                    )
                    
                    # Cache the improved prompt
                    self.improved_prompts_cache[improved_prompt.agent_type] = improved_prompt
                    
                    logger.debug(f"Loaded improved prompt for {improved_prompt.agent_type}")
                    
                except Exception as e:
                    logger.error(f"Error loading improved prompt from {prompt_file}: {e}")
                    continue
            
            logger.info(f"Loaded {len(self.improved_prompts_cache)} improved prompts")
            
        except Exception as e:
            logger.error(f"Error loading improved prompts: {e}")
    
    async def save_improved_prompt(self, improved_prompt: ImprovedPrompt) -> bool:
        """Save improved prompt to training system."""
        try:
            # Create filename
            filename = f"{improved_prompt.agent_type}_{improved_prompt.training_session_id}.json"
            filepath = self.improved_prompts_dir / filename
            
            # Convert to dictionary
            data = {
                'agent_type': improved_prompt.agent_type,
                'original_prompt': improved_prompt.original_prompt,
                'improved_prompt': improved_prompt.improved_prompt,
                'improvement_score': improved_prompt.improvement_score,
                'training_session_id': improved_prompt.training_session_id,
                'timestamp': improved_prompt.timestamp.isoformat(),
                'validation_metrics': improved_prompt.validation_metrics,
                'deployment_ready': improved_prompt.deployment_ready
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Update cache
            self.improved_prompts_cache[improved_prompt.agent_type] = improved_prompt
            
            logger.info(f"Saved improved prompt for {improved_prompt.agent_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving improved prompt: {e}")
            return False
    
    async def deploy_improved_prompt(self, agent_name: str, training_session_id: str) -> Dict[str, Any]:
        """Deploy improved prompt to agent profile."""
        try:
            # Get improved prompt
            improved_prompt = self.improved_prompts_cache.get(agent_name)
            if not improved_prompt or improved_prompt.training_session_id != training_session_id:
                return {
                    'success': False,
                    'error': 'Improved prompt not found or session mismatch'
                }
            
            # Mark as deployment ready
            improved_prompt.deployment_ready = True
            
            # Save updated prompt
            await self.save_improved_prompt(improved_prompt)
            
            # Clear profile cache to force reload
            self.profile_cache.pop(agent_name, None)
            
            # Integration with training system
            if self.training_integration:
                deployment_result = await self.training_integration.deploy_trained_agent(
                    agent_type=agent_name,
                    training_session_id=training_session_id,
                    deployment_tier='user'
                )
                
                if deployment_result['success']:
                    self.performance_metrics['training_integrations'] += 1
            
            return {
                'success': True,
                'agent_name': agent_name,
                'training_session_id': training_session_id,
                'improvement_score': improved_prompt.improvement_score,
                'deployment_ready': True
            }
            
        except Exception as e:
            logger.error(f"Error deploying improved prompt for {agent_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def build_enhanced_task_prompt(self, agent_name: str, task_context: Dict[str, Any]) -> str:
        """Build enhanced Task Tool prompt with improved prompt integration."""
        try:
            # Load agent profile
            profile = await self.load_agent_profile(agent_name)
            if not profile:
                raise ValueError(f"No profile found for agent: {agent_name}")
            
            # Get effective prompt (improved or original)
            effective_prompt = profile.get_effective_prompt()
            
            # Build enhanced prompt
            enhanced_prompt = f"""**{profile.nickname}**: {task_context.get('task_description', 'Task execution')}

TEMPORAL CONTEXT: Today is {datetime.now().strftime('%B %d, %Y')}. Apply date awareness to task execution.

**Enhanced Agent Profile Integration**: 
- **Role**: {profile.role}
- **Tier**: {profile.tier.value.title()} ({profile.path.parent.name})
- **Profile ID**: {profile.profile_id}
- **Status**: {profile.status.value}
- **Prompt Version**: {profile.prompt_version}
- **Training Enhanced**: {'Yes' if profile.has_improved_prompt else 'No'}

**Core Capabilities**:
{chr(10).join(f"- {cap}" for cap in profile.capabilities[:5])}

**Authority Scope**:
{chr(10).join(f"- {auth}" for auth in profile.authority_scope[:4])}

**Task Requirements**:
{chr(10).join(f"- {req}" for req in task_context.get('requirements', []))}

**Context Preferences**:
{chr(10).join(f"- {key.replace('_', ' ').title()}: {value}" for key, value in profile.context_preferences.items())}

**Quality Standards**:
{chr(10).join(f"- {std}" for std in profile.quality_standards[:3])}

**Integration Patterns**:
{chr(10).join(f"- With {agent.title()}: {desc}" for agent, desc in profile.integration_patterns.items())}

**Enhanced Prompt Context**:
{effective_prompt}

**Authority**: {profile.role} operations with enhanced prompt integration
**Priority**: {task_context.get('priority', 'medium')}
**Framework Integration**: AgentProfileLoader with improved prompt system (99.7% performance optimization)

**Profile-Enhanced Context**: This subprocess operates with enhanced context from {profile.tier.value}-tier agent profile, providing specialized knowledge, improved prompt integration, and performance optimization for optimal task execution.
"""
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error building enhanced task prompt for {agent_name}: {e}")
            raise
    
    async def get_profile_hierarchy(self, agent_name: str) -> List[AgentProfile]:
        """Get all available profiles for an agent across all tiers."""
        profiles = []
        
        for tier in [ProfileTier.PROJECT, ProfileTier.USER, ProfileTier.SYSTEM]:
            profile = await self._load_profile_from_tier(agent_name, tier)
            if profile:
                profiles.append(profile)
        
        return profiles
    
    async def list_available_agents(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all available agents with enhanced metadata."""
        agents = {}
        
        # Use AgentRegistry if available
        if self.agent_registry:
            try:
                registry_agents = await self.agent_registry.list_agents()
                
                for agent_metadata in registry_agents:
                    tier = agent_metadata.tier
                    if tier not in agents:
                        agents[tier] = []
                    
                    # Load profile for additional metadata
                    profile = await self.load_agent_profile(agent_metadata.name)
                    
                    agent_info = {
                        'name': agent_metadata.name,
                        'type': agent_metadata.type,
                        'tier': tier,
                        'path': agent_metadata.path,
                        'validated': agent_metadata.validated,
                        'has_improved_prompt': profile.has_improved_prompt if profile else False,
                        'status': profile.status.value if profile else 'unknown',
                        'capabilities': profile.capabilities if profile else []
                    }
                    
                    agents[tier].append(agent_info)
                
            except Exception as e:
                logger.error(f"Error using AgentRegistry: {e}")
        
        # Fallback to direct file scanning
        if not agents:
            for tier, tier_path in self.tier_paths.items():
                if not tier_path.exists():
                    continue
                
                tier_agents = []
                for agent_file in tier_path.glob('*.md'):
                    try:
                        profile = await self._parse_profile_file(agent_file, tier)
                        if profile:
                            tier_agents.append({
                                'name': profile.name,
                                'type': 'unknown',
                                'tier': tier.value,
                                'path': str(profile.path),
                                'validated': True,
                                'has_improved_prompt': profile.has_improved_prompt,
                                'status': profile.status.value,
                                'capabilities': profile.capabilities
                            })
                    except Exception as e:
                        logger.error(f"Error parsing {agent_file}: {e}")
                        continue
                
                agents[tier.value] = tier_agents
        
        return agents
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the profile loader."""
        metrics = self.performance_metrics.copy()
        
        # Add cache statistics
        if self.shared_cache:
            cache_metrics = self.shared_cache.get_metrics()
            metrics.update({
                'shared_cache_hits': cache_metrics.get('hits', 0),
                'shared_cache_misses': cache_metrics.get('misses', 0),
                'shared_cache_hit_rate': cache_metrics.get('hit_rate', 0.0),
                'shared_cache_size': cache_metrics.get('entry_count', 0)
            })
        
        # Add profile statistics
        metrics.update({
            'cached_profiles': len(self.profile_cache),
            'improved_prompts_available': len(self.improved_prompts_cache),
            'tiers_configured': len(self.tier_paths)
        })
        
        return metrics
    
    async def validate_profile_integration(self) -> Dict[str, Any]:
        """Validate profile integration with framework systems."""
        validation_results = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'integrations': {}
        }
        
        # Validate tier paths
        for tier, path in self.tier_paths.items():
            if not path.exists():
                validation_results['issues'].append(f"Missing tier directory: {path}")
                validation_results['valid'] = False
            else:
                # Check for profiles in tier
                profile_count = len(list(path.glob('*.md')))
                validation_results['integrations'][f'{tier.value}_profiles'] = profile_count
        
        # Validate service integrations
        validation_results['integrations']['shared_cache'] = self.shared_cache is not None
        validation_results['integrations']['agent_registry'] = self.agent_registry is not None
        validation_results['integrations']['prompt_template_manager'] = self.prompt_template_manager is not None
        validation_results['integrations']['training_integration'] = self.training_integration is not None
        
        # Validate improved prompts
        if self.improved_prompts_dir.exists():
            improved_count = len(list(self.improved_prompts_dir.glob('*.json')))
            validation_results['integrations']['improved_prompts'] = improved_count
        else:
            validation_results['warnings'].append("Improved prompts directory not found")
        
        return validation_results
    
    def invalidate_cache(self, agent_name: Optional[str] = None) -> None:
        """Invalidate profile cache."""
        if agent_name:
            self.profile_cache.pop(agent_name, None)
            if self.shared_cache:
                self.shared_cache.invalidate(f"agent_profile:{agent_name}:*")
        else:
            self.profile_cache.clear()
            if self.shared_cache:
                self.shared_cache.invalidate("agent_profile:*")
    
    # Helper methods for profile parsing
    def _extract_agent_name(self, filename: str) -> str:
        """Extract agent name from filename."""
        name = filename.lower()
        for suffix in ['-agent', '_agent', '-profile']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        return name
    
    def _extract_role(self, content: str) -> str:
        """Extract primary role from profile content."""
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('## Role') or line.startswith('# Role'):
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
            
            if any(header in line.lower() for header in ['## capabilities', '## core capabilities', 
                                                         '## responsibilities', '## functions']):
                in_capabilities_section = True
                continue
            
            if in_capabilities_section and line.startswith('##'):
                break
            
            if in_capabilities_section and line.startswith('- **'):
                capability = line[4:].split('**:')[0].strip('*')
                if capability:
                    capabilities.append(capability)
            elif in_capabilities_section and (line.startswith('- ') or line.startswith('* ')):
                capability = line[2:].strip()
                if capability and not capability.startswith('#'):
                    capabilities.append(capability)
        
        return capabilities[:10]
    
    def _extract_authority_scope(self, content: str) -> List[str]:
        """Extract authority scope from profile content."""
        authority = []
        in_authority_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if any(header in line.lower() for header in ['## authority', '## authority scope', 
                                                         '## permissions', '## writing']):
                in_authority_section = True
                continue
            
            if in_authority_section and line.startswith('##'):
                break
            
            if in_authority_section and line.startswith('- **'):
                auth_item = line[4:].split('**:')[0].strip('*')
                if auth_item:
                    authority.append(auth_item)
            elif in_authority_section and (line.startswith('- ') or line.startswith('* ')):
                auth_item = line[2:].strip()
                if auth_item and not auth_item.startswith('#'):
                    authority.append(auth_item)
        
        return authority[:8]
    
    def _extract_context_preferences(self, content: str) -> Dict[str, Any]:
        """Extract context preferences from profile content."""
        preferences = {}
        in_context_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if any(header in line.lower() for header in ['## context preferences', '## context']):
                in_context_section = True
                continue
            
            if in_context_section and line.startswith('##'):
                break
            
            if in_context_section and line.startswith('- **'):
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
            
            if any(header in line.lower() for header in ['## escalation', '## escalation criteria']):
                in_escalation_section = True
                continue
            
            if in_escalation_section and line.startswith('##'):
                break
            
            if in_escalation_section and line.startswith('- **'):
                criterion = line[4:].split('**:')[0].strip('*')
                if criterion:
                    criteria.append(criterion)
            elif in_escalation_section and (line.startswith('- ') or line.startswith('* ')):
                criterion = line[2:].strip()
                if criterion and not criterion.startswith('#'):
                    criteria.append(criterion)
        
        return criteria[:6]
    
    def _extract_integration_patterns(self, content: str) -> Dict[str, str]:
        """Extract integration patterns from profile content."""
        patterns = {}
        in_integration_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if any(header in line.lower() for header in ['## integration', '## integration patterns']):
                in_integration_section = True
                continue
            
            if in_integration_section and line.startswith('##'):
                break
            
            if in_integration_section and line.startswith('- **With '):
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
            
            if any(header in line.lower() for header in ['## quality standards', '## quality']):
                in_standards_section = True
                continue
            
            if in_standards_section and line.startswith('##'):
                break
            
            if in_standards_section and line.startswith('- **'):
                standard = line[4:].split('**:')[0].strip('*')
                if standard:
                    standards.append(standard)
            elif in_standards_section and (line.startswith('- ') or line.startswith('* ')):
                standard = line[2:].strip()
                if standard and not standard.startswith('#'):
                    standards.append(standard)
        
        return standards[:5]
    
    def _extract_communication_style(self, content: str) -> Dict[str, str]:
        """Extract communication style from profile content."""
        style = {}
        in_communication_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if any(header in line.lower() for header in ['## communication', '## communication style']):
                in_communication_section = True
                continue
            
            if in_communication_section and line.startswith('##'):
                break
            
            if in_communication_section and line.startswith('- **'):
                parts = line[4:].split('**:', 1)
                if len(parts) == 2:
                    key = parts[0].strip('*').lower()
                    value = parts[1].strip()
                    style[key] = value
        
        return style
    
    def _extract_prompt_template_id(self, content: str) -> Optional[str]:
        """Extract prompt template ID from profile content."""
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('**Template ID**:'):
                return line.split(':', 1)[1].strip()
        return None
    
    def _extract_training_enabled(self, content: str) -> bool:
        """Extract training enabled flag from profile content."""
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('**Training Enabled**:'):
                return line.split(':', 1)[1].strip().lower() == 'true'
        return True  # Default to enabled


# Factory function
def create_agent_profile_loader(config: Optional[Config] = None) -> AgentProfileLoader:
    """Create an AgentProfileLoader instance."""
    return AgentProfileLoader(config)


# Integration with existing systems
async def integrate_with_task_tool(agent_name: str, task_context: Dict[str, Any]) -> str:
    """Integration function for Task Tool subprocess creation."""
    loader = create_agent_profile_loader()
    await loader.start()
    
    try:
        enhanced_prompt = await loader.build_enhanced_task_prompt(agent_name, task_context)
        return enhanced_prompt
    finally:
        await loader.stop()


if __name__ == "__main__":
    # Demo and testing
    async def demo():
        """Demonstrate AgentProfileLoader usage."""
        print("🚀 AgentProfileLoader Demo")
        print("=" * 50)
        
        # Initialize loader
        loader = create_agent_profile_loader()
        await loader.start()
        
        try:
            # Load a profile
            profile = await loader.load_agent_profile("engineer")
            if profile:
                print(f"\n📋 Loaded Profile: {profile.name}")
                print(f"  Role: {profile.role}")
                print(f"  Tier: {profile.tier.value}")
                print(f"  Has Improved Prompt: {profile.has_improved_prompt}")
                print(f"  Status: {profile.status.value}")
                print(f"  Capabilities: {len(profile.capabilities)}")
            
            # List available agents
            agents = await loader.list_available_agents()
            print(f"\n🤖 Available Agents:")
            for tier, tier_agents in agents.items():
                print(f"  {tier.upper()}: {len(tier_agents)} agents")
            
            # Get performance metrics
            metrics = await loader.get_performance_metrics()
            print(f"\n📊 Performance Metrics:")
            for key, value in metrics.items():
                print(f"  {key}: {value}")
            
            # Validate integration
            validation = await loader.validate_profile_integration()
            print(f"\n✅ Integration Validation: {'Valid' if validation['valid'] else 'Invalid'}")
            print(f"  Issues: {len(validation['issues'])}")
            print(f"  Warnings: {len(validation['warnings'])}")
            
        finally:
            await loader.stop()
            print("\n✅ Demo completed")
    
    # Run demo
    asyncio.run(demo())