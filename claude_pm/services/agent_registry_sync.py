"""
Agent Registry Service - Synchronous Implementation
Provides fully synchronous agent discovery without async complexity

Created: 2025-07-18
Purpose: Simplified synchronous agent registry for CLI/script usage
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.model_selector import ModelSelector, ModelSelectionCriteria

logger = logging.getLogger(__name__)

@dataclass
class AgentMetadata:
    """Enhanced agent metadata structure for registry entries with specialization and model support"""
    name: str
    type: str
    path: str
    tier: str  # 'user', 'system', 'project'
    description: Optional[str] = None
    version: Optional[str] = None
    capabilities: List[str] = None
    last_modified: Optional[float] = None
    file_size: Optional[int] = None
    validated: bool = False
    error_message: Optional[str] = None
    # Enhanced metadata for ISS-0118
    specializations: List[str] = None
    frameworks: List[str] = None
    domains: List[str] = None
    roles: List[str] = None
    is_hybrid: bool = False
    hybrid_types: List[str] = None
    composite_agents: List[str] = None
    validation_score: float = 0.0
    complexity_level: str = 'basic'  # 'basic', 'intermediate', 'advanced', 'expert'
    # Model configuration fields
    preferred_model: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.specializations is None:
            self.specializations = []
        if self.frameworks is None:
            self.frameworks = []
        if self.domains is None:
            self.domains = []
        if self.roles is None:
            self.roles = []
        if self.hybrid_types is None:
            self.hybrid_types = []
        if self.composite_agents is None:
            self.composite_agents = []
        if self.model_config is None:
            self.model_config = {}

class AgentRegistry:
    """
    Core Agent Registry - Fully synchronous agent discovery and management system
    
    Features:
    - Two-tier hierarchy discovery (user → system)
    - Synchronous directory scanning
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
        self.discovery_paths: List[Path] = []
        self.core_agent_types = {
            'documentation', 'ticketing', 'version_control', 'qa', 'research',
            'ops', 'security', 'engineer', 'data_engineer'
        }
        # Extended specialized agent types for ISS-0118
        self.specialized_agent_types = {
            'ui_ux', 'database', 'api', 'testing', 'performance', 'monitoring',
            'analytics', 'deployment', 'integration', 'workflow', 'content',
            'machine_learning', 'data_science', 'frontend', 'backend', 'mobile',
            'devops', 'cloud', 'infrastructure', 'compliance', 'audit',
            'project_management', 'business_analysis', 'customer_support',
            'marketing', 'sales', 'finance', 'legal', 'hr', 'training',
            'documentation_specialist', 'code_review', 'architecture',
            'orchestrator', 'scaffolding', 'memory_management', 'knowledge_base'
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
    
    def discover_agents(self, force_refresh: bool = False) -> Dict[str, AgentMetadata]:
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
            cache_hit = self.cache_service.get("agent_registry_discovery")
            if cache_hit:
                logger.debug("Using cached agent discovery results")
                self.registry = {name: AgentMetadata(**data) for name, data in cache_hit.items()}
                return self.registry
        
        logger.info("Starting agent discovery across hierarchy")
        discovered_agents = {}
        
        # Discover agents from each path with hierarchy precedence
        for path in self.discovery_paths:
            tier = self._determine_tier(path)
            path_agents = self._scan_directory(path, tier)
            
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
        validated_agents = self._validate_agents(discovered_agents)
        
        # Update registry and cache
        self.registry = validated_agents
        self.last_discovery_time = time.time()
        
        # Cache discovery results for performance
        cache_data = {name: asdict(metadata) for name, metadata in validated_agents.items()}
        self.cache_service.set("agent_registry_discovery", cache_data, ttl=self.discovery_cache_ttl)
        
        discovery_time = time.time() - discovery_start
        logger.info(f"Agent discovery completed in {discovery_time:.3f}s, found {len(validated_agents)} agents")
        
        return self.registry
    
    def _scan_directory(self, directory: Path, tier: str) -> Dict[str, AgentMetadata]:
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
                agent_metadata = self._extract_agent_metadata(agent_file, tier)
                if agent_metadata:
                    agents[agent_metadata.name] = agent_metadata
            except Exception as e:
                logger.warning(f"Error processing agent file {agent_file}: {e}")
        
        return agents
    
    def _extract_agent_metadata(self, agent_file: Path, tier: str) -> Optional[AgentMetadata]:
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
            description, version, capabilities = self._parse_agent_file(agent_file)
            
            # Enhanced metadata extraction for ISS-0118
            specializations, frameworks, domains, roles = self._extract_specialized_metadata(capabilities)
            is_hybrid, hybrid_types = self._detect_hybrid_agent(agent_type, specializations)
            complexity_level = self._assess_complexity_level(capabilities, specializations)
            
            # Extract model configuration from agent file
            preferred_model, model_config = self._extract_model_configuration(agent_file, agent_type, complexity_level)
            
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
                validated=False,  # Will be validated later
                specializations=specializations,
                frameworks=frameworks,
                domains=domains,
                roles=roles,
                is_hybrid=is_hybrid,
                hybrid_types=hybrid_types,
                complexity_level=complexity_level,
                preferred_model=preferred_model,
                model_config=model_config
            )
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {agent_file}: {e}")
            return None
    
    def _parse_agent_file(self, agent_file: Path) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Enhanced agent file parsing with specialized capability detection for ISS-0118.
        Extracts comprehensive metadata including specialization indicators.
        
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
            
            # Extract docstring description with specialization detection
            if '"""' in content:
                docstring_start = content.find('"""')
                if docstring_start != -1:
                    docstring_end = content.find('"""', docstring_start + 3)
                    if docstring_end != -1:
                        docstring = content[docstring_start + 3:docstring_end].strip()
                        # Use first line as description
                        description = docstring.split('\n')[0].strip()
                        
                        # Extract specialization hints from docstring
                        docstring_lower = docstring.lower()
                        specialization_indicators = [
                            'specializes in', 'specialized for', 'expert in', 'focused on',
                            'handles', 'manages', 'responsible for', 'domain:', 'specialty:'
                        ]
                        for indicator in specialization_indicators:
                            if indicator in docstring_lower:
                                # Extract text after indicator as specialization capability
                                spec_start = docstring_lower.find(indicator) + len(indicator)
                                spec_text = docstring[spec_start:spec_start+100].strip()
                                if spec_text:
                                    capabilities.append(f"specialization:{spec_text.split('.')[0].strip()}")
            
            # Extract version information
            if 'VERSION' in content or '__version__' in content:
                lines = content.split('\n')
                for line in lines:
                    if 'VERSION' in line or '__version__' in line:
                        if '=' in line:
                            version_part = line.split('=')[1].strip().strip('"\'')
                            version = version_part
                            break
            
            # Enhanced capability extraction from methods/functions
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
            
            # Extract capabilities from class definitions and inheritance
            import ast
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Add class name as capability
                        capabilities.append(f"class:{node.name}")
                        
                        # Extract base classes as capability indicators
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                capabilities.append(f"inherits:{base.id}")
                            elif isinstance(base, ast.Attribute):
                                capabilities.append(f"inherits:{base.attr}")
            except SyntaxError:
                pass  # Skip AST parsing if syntax errors
            
            # Extract framework and library capabilities from imports
            framework_capabilities = self._extract_framework_capabilities(content)
            capabilities.extend(framework_capabilities)
            
            # Extract role and domain capabilities from comments
            role_capabilities = self._extract_role_capabilities(content)
            capabilities.extend(role_capabilities)
        
        except Exception as e:
            logger.warning(f"Error parsing agent file {agent_file}: {e}")
        
        return description, version, capabilities
    
    def _extract_framework_capabilities(self, content: str) -> List[str]:
        """
        Extract framework and library capabilities from import statements.
        
        Args:
            content: File content
            
        Returns:
            List of framework capabilities
        """
        capabilities = []
        
        framework_patterns = {
            'fastapi': ['fastapi', 'pydantic'],
            'django': ['django'],
            'flask': ['flask'],
            'react': ['react', '@types/react'],
            'vue': ['vue', '@vue/'],
            'angular': ['@angular/', 'angular'],
            'express': ['express'],
            'tensorflow': ['tensorflow', 'tf'],
            'pytorch': ['torch', 'pytorch'],
            'pandas': ['pandas'],
            'numpy': ['numpy'],
            'selenium': ['selenium'],
            'pytest': ['pytest'],
            'jest': ['jest'],
            'docker': ['docker'],
            'kubernetes': ['kubernetes', 'kubectl'],
            'aws': ['boto3', 'aws-'],
            'azure': ['azure-'],
            'gcp': ['google-cloud-'],
            'redis': ['redis'],
            'mongodb': ['pymongo', 'mongodb'],
            'postgresql': ['psycopg2', 'postgresql'],
            'mysql': ['mysql', 'pymysql'],
            'graphql': ['graphql'],
            'rest_api': ['requests', 'urllib'],
            'machine_learning': ['scikit-learn', 'sklearn'],
            'data_analysis': ['matplotlib', 'seaborn'],
            'async_processing': ['asyncio', 'aiohttp'],
            'task_queue': ['celery', 'rq'],
            'monitoring': ['prometheus', 'grafana'],
            'logging': ['loguru', 'structlog']
        }
        
        content_lower = content.lower()
        
        for framework, patterns in framework_patterns.items():
            for pattern in patterns:
                if f'import {pattern}' in content_lower or f'from {pattern}' in content_lower:
                    capabilities.append(f'framework:{framework}')
                    break
        
        return capabilities
    
    def _extract_role_capabilities(self, content: str) -> List[str]:
        """
        Extract role and domain capabilities from comments and docstrings.
        
        Args:
            content: File content
            
        Returns:
            List of role capabilities
        """
        capabilities = []
        
        role_patterns = {
            'ui_designer': ['ui design', 'user interface', 'interface design'],
            'ux_specialist': ['user experience', 'ux research', 'usability'],
            'frontend_developer': ['frontend development', 'client-side', 'web development'],
            'backend_developer': ['backend development', 'server-side', 'api development'],
            'database_administrator': ['database admin', 'db management', 'database design'],
            'devops_engineer': ['devops', 'ci/cd', 'deployment automation'],
            'security_specialist': ['security analysis', 'vulnerability assessment', 'penetration testing'],
            'performance_engineer': ['performance optimization', 'load testing', 'benchmarking'],
            'quality_assurance': ['quality assurance', 'test automation', 'qa testing'],
            'data_scientist': ['data science', 'machine learning', 'statistical analysis'],
            'business_analyst': ['business analysis', 'requirements gathering', 'process mapping'],
            'project_manager': ['project management', 'agile', 'scrum master'],
            'technical_writer': ['technical writing', 'documentation', 'content creation'],
            'integration_specialist': ['system integration', 'api integration', 'middleware'],
            'architecture_specialist': ['system architecture', 'software architecture', 'design patterns']
        }
        
        content_lower = content.lower()
        
        for role, patterns in role_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    capabilities.append(f'role:{role}')
                    break
        
        # Extract domain capabilities from comments
        domain_keywords = {
            'e_commerce': ['e-commerce', 'shopping', 'payment', 'order'],
            'healthcare': ['healthcare', 'medical', 'patient', 'clinical'],
            'finance': ['financial', 'banking', 'trading', 'investment'],
            'education': ['education', 'learning', 'student', 'course'],
            'gaming': ['gaming', 'game', 'player', 'score'],
            'social_media': ['social', 'feed', 'post', 'like', 'share'],
            'iot': ['iot', 'sensor', 'device', 'telemetry'],
            'blockchain': ['blockchain', 'crypto', 'smart contract', 'web3'],
            'ai_ml': ['artificial intelligence', 'machine learning', 'neural network'],
            'cloud_native': ['cloud native', 'microservices', 'serverless']
        }
        
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    capabilities.append(f'domain:{domain}')
                    break
        
        return capabilities
    
    def _extract_model_configuration(
        self, 
        agent_file: Path, 
        agent_type: str, 
        complexity_level: str
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract model configuration from agent file and apply intelligent selection.
        
        Args:
            agent_file: Path to agent file
            agent_type: Agent type classification
            complexity_level: Assessed complexity level
            
        Returns:
            Tuple of (preferred_model, model_config)
        """
        try:
            # Check for explicit model configuration in agent file
            content = agent_file.read_text(encoding='utf-8')
            preferred_model = None
            model_config = {}
            
            # Parse explicit model preferences from agent file
            explicit_model = self._parse_explicit_model_config(content)
            if explicit_model:
                preferred_model = explicit_model["model_id"]
                model_config = explicit_model.get("config", {})
                logger.debug(f"Found explicit model configuration in {agent_file.name}: {preferred_model}")
            
            # If no explicit configuration, use intelligent selection
            if not preferred_model:
                # Create selection criteria based on agent analysis
                criteria = ModelSelectionCriteria(
                    agent_type=agent_type,
                    task_complexity=complexity_level,
                    performance_requirements=self._analyze_performance_requirements(content),
                    reasoning_depth_required=self._analyze_reasoning_requirements(content, agent_type),
                    creativity_required=self._analyze_creativity_requirements(content),
                    speed_priority=self._analyze_speed_requirements(content)
                )
                
                # Select model using ModelSelector
                model_type, model_configuration = self.model_selector.select_model_for_agent(
                    agent_type, criteria
                )
                
                preferred_model = model_type.value
                model_config = {
                    "max_tokens": model_configuration.max_tokens,
                    "context_window": model_configuration.context_window,
                    "selection_criteria": {
                        "task_complexity": criteria.task_complexity,
                        "reasoning_depth": criteria.reasoning_depth_required,
                        "speed_priority": criteria.speed_priority,
                        "creativity_required": criteria.creativity_required
                    },
                    "capabilities": model_configuration.capabilities,
                    "performance_profile": model_configuration.performance_profile,
                    "auto_selected": True
                }
                
                logger.debug(f"Auto-selected model for {agent_type}: {preferred_model}")
            
            return preferred_model, model_config
            
        except Exception as e:
            logger.warning(f"Error extracting model configuration from {agent_file}: {e}")
            # Fallback to default model selection
            try:
                model_type, model_configuration = self.model_selector.select_model_for_agent(agent_type)
                return model_type.value, {
                    "max_tokens": model_configuration.max_tokens,
                    "fallback_selection": True,
                    "error": str(e)
                }
            except Exception as fallback_error:
                logger.error(f"Fallback model selection failed: {fallback_error}")
                return None, {"error": str(e), "fallback_error": str(fallback_error)}
    
    def _parse_explicit_model_config(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse explicit model configuration from agent file content.
        
        Looks for patterns like:
        - MODEL_PREFERENCE = "claude-3-opus-20240229"
        - PREFERRED_MODEL = "claude-3-5-sonnet-20241022"
        - model_config = {"model": "claude-3-opus-20240229", "max_tokens": 4096}
        
        Args:
            content: Agent file content
            
        Returns:
            Dictionary with model configuration or None
        """
        import re
        
        # Pattern for direct model assignment
        model_patterns = [
            r'MODEL_PREFERENCE\s*=\s*["\']([^"\']+)["\']',
            r'PREFERRED_MODEL\s*=\s*["\']([^"\']+)["\']',
            r'model\s*=\s*["\']([^"\']+)["\']',
            r'MODEL\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                model_id = match.group(1)
                return {"model_id": model_id, "config": {"explicit": True}}
        
        # Pattern for configuration dictionary
        config_pattern = r'model_config\s*=\s*\{([^}]+)\}'
        config_match = re.search(config_pattern, content, re.IGNORECASE)
        if config_match:
            try:
                # Simple parsing of model config dictionary
                config_str = config_match.group(1)
                model_match = re.search(r'["\']model["\']:\s*["\']([^"\']+)["\']', config_str)
                if model_match:
                    return {
                        "model_id": model_match.group(1),
                        "config": {"explicit": True, "from_dict": True}
                    }
            except Exception as e:
                logger.warning(f"Error parsing model config dictionary: {e}")
        
        return None
    
    def _analyze_performance_requirements(self, content: str) -> Dict[str, Any]:
        """Analyze performance requirements from agent file content."""
        requirements = {}
        content_lower = content.lower()
        
        # Speed requirements
        if any(keyword in content_lower for keyword in ['fast', 'quick', 'rapid', 'immediate']):
            requirements["speed_priority"] = True
        
        # Quality requirements  
        if any(keyword in content_lower for keyword in ['quality', 'accurate', 'precise', 'detailed']):
            requirements["quality_priority"] = True
            
        # Resource constraints
        if any(keyword in content_lower for keyword in ['efficient', 'lightweight', 'minimal']):
            requirements["resource_efficiency"] = True
            
        return requirements
    
    def _analyze_reasoning_requirements(self, content: str, agent_type: str) -> str:
        """Analyze reasoning depth requirements from content and agent type."""
        content_lower = content.lower()
        
        # Expert reasoning indicators
        if any(keyword in content_lower for keyword in [
            'architecture', 'design pattern', 'complex system', 'optimization',
            'strategic', 'planning', 'analysis', 'research'
        ]):
            return "expert"
        
        # Deep reasoning indicators
        if any(keyword in content_lower for keyword in [
            'investigate', 'analyze', 'evaluate', 'assess', 'compare'
        ]):
            return "deep"
        
        # Simple reasoning indicators
        if any(keyword in content_lower for keyword in [
            'format', 'display', 'show', 'list', 'basic'
        ]):
            return "simple"
        
        # Agent type-based defaults
        if agent_type in ['engineer', 'architecture', 'orchestrator']:
            return "expert"
        elif agent_type in ['research', 'analysis', 'qa']:
            return "deep"
        else:
            return "standard"
    
    def _analyze_creativity_requirements(self, content: str) -> bool:
        """Analyze creativity requirements from agent file content."""
        content_lower = content.lower()
        
        creativity_indicators = [
            'creative', 'innovative', 'design', 'brainstorm', 'ideate',
            'generate', 'invent', 'original', 'novel'
        ]
        
        return any(indicator in content_lower for indicator in creativity_indicators)
    
    def _analyze_speed_requirements(self, content: str) -> bool:
        """Analyze speed priority requirements from agent file content."""
        content_lower = content.lower()
        
        speed_indicators = [
            'urgent', 'quick', 'fast', 'immediate', 'rapid', 'asap',
            'real-time', 'instant', 'responsive'
        ]
        
        return any(indicator in content_lower for indicator in speed_indicators)
    
    def _extract_specialized_metadata(self, capabilities: List[str]) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Extract specialized metadata from capabilities list.
        
        Args:
            capabilities: List of agent capabilities
            
        Returns:
            Tuple of (specializations, frameworks, domains, roles)
        """
        specializations = []
        frameworks = []
        domains = []
        roles = []
        
        for capability in capabilities:
            if capability.startswith('specialization:'):
                specializations.append(capability.replace('specialization:', ''))
            elif capability.startswith('framework:'):
                frameworks.append(capability.replace('framework:', ''))
            elif capability.startswith('domain:'):
                domains.append(capability.replace('domain:', ''))
            elif capability.startswith('role:'):
                roles.append(capability.replace('role:', ''))
        
        return specializations, frameworks, domains, roles
    
    def _detect_hybrid_agent(self, agent_type: str, specializations: List[str]) -> Tuple[bool, List[str]]:
        """
        Detect if agent is hybrid (combines multiple agent types).
        
        Args:
            agent_type: Primary agent type
            specializations: List of specializations
            
        Returns:
            Tuple of (is_hybrid, hybrid_types)
        """
        hybrid_types = []
        
        # Check if agent combines multiple core types
        core_type_indicators = {
            'documentation': ['docs', 'documentation', 'technical_writing'],
            'ticketing': ['ticketing', 'issue', 'bug_tracking'],
            'version_control': ['git', 'version', 'branching'],
            'qa': ['testing', 'quality', 'validation'],
            'research': ['research', 'analysis', 'investigation'],
            'ops': ['operations', 'deployment', 'infrastructure'],
            'security': ['security', 'auth', 'vulnerability'],
            'engineer': ['engineering', 'development', 'coding'],
            'data_engineer': ['data', 'pipeline', 'etl']
        }
        
        primary_type = agent_type
        detected_types = set()
        
        for spec in specializations:
            for core_type, indicators in core_type_indicators.items():
                if any(indicator in spec.lower() for indicator in indicators):
                    detected_types.add(core_type)
        
        # If more than one core type detected, it's hybrid
        if len(detected_types) > 1 or (len(detected_types) == 1 and primary_type not in detected_types):
            hybrid_types = list(detected_types)
            if primary_type not in hybrid_types:
                hybrid_types.append(primary_type)
            return True, hybrid_types
        
        return False, []
    
    def _assess_complexity_level(self, capabilities: List[str], specializations: List[str]) -> str:
        """
        Assess agent complexity level based on capabilities and specializations.
        
        Args:
            capabilities: List of capabilities
            specializations: List of specializations
            
        Returns:
            Complexity level ('basic', 'intermediate', 'advanced', 'expert')
        """
        total_features = len(capabilities) + len(specializations)
        
        # Count advanced features
        advanced_indicators = [
            'async_', 'class:', 'framework:', 'machine_learning', 'ai',
            'microservices', 'kubernetes', 'blockchain', 'neural_network'
        ]
        
        advanced_count = sum(1 for cap in capabilities 
                           if any(indicator in cap.lower() for indicator in advanced_indicators))
        
        # Assess complexity
        if total_features >= 20 or advanced_count >= 5:
            return 'expert'
        elif total_features >= 15 or advanced_count >= 3:
            return 'advanced'
        elif total_features >= 8 or advanced_count >= 1:
            return 'intermediate'
        else:
            return 'basic'
    
    def _classify_agent_type(self, agent_name: str, agent_file: Path) -> str:
        """
        Enhanced agent type classification supporting specialized agents beyond core 9 types.
        Implements comprehensive pattern-based detection for ISS-0118.
        
        Args:
            agent_name: Agent name
            agent_file: Agent file path
            
        Returns:
            Agent type classification
        """
        name_lower = agent_name.lower()
        
        # First check for core agent types (highest priority)
        for core_type in self.core_agent_types:
            if core_type in name_lower or name_lower in core_type:
                return core_type
        
        # Enhanced pattern-based classification for specialized agents
        classification_patterns = {
            # UI/UX and Frontend specializations
            'ui_ux': ['ui', 'ux', 'design', 'interface', 'user_experience', 'frontend_design'],
            'frontend': ['frontend', 'front_end', 'react', 'vue', 'angular', 'web_ui', 'client_side'],
            
            # Backend and Infrastructure specializations
            'backend': ['backend', 'back_end', 'server', 'api_server', 'microservice'],
            'database': ['database', 'db', 'sql', 'nosql', 'mysql', 'postgres', 'mongodb', 'redis'],
            'api': ['api', 'rest', 'graphql', 'endpoint', 'service', 'web_service'],
            
            # Testing and Quality specializations
            'testing': ['test', 'testing', 'unit_test', 'integration_test', 'e2e', 'automation'],
            'performance': ['performance', 'benchmark', 'optimization', 'profiling', 'load_test'],
            'monitoring': ['monitoring', 'observability', 'metrics', 'logging', 'alerting'],
            
            # DevOps and Infrastructure specializations
            'devops': ['devops', 'ci_cd', 'pipeline', 'automation', 'build'],
            'cloud': ['cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'container'],
            'infrastructure': ['infrastructure', 'terraform', 'ansible', 'provisioning'],
            'deployment': ['deployment', 'deploy', 'release', 'staging', 'production'],
            
            # Data and Analytics specializations
            'analytics': ['analytics', 'metrics', 'reporting', 'business_intelligence', 'dashboard'],
            'machine_learning': ['ml', 'machine_learning', 'ai', 'model', 'training', 'prediction'],
            'data_science': ['data_science', 'data_scientist', 'analysis', 'statistics', 'modeling'],
            
            # Business and Process specializations
            'project_management': ['pm', 'project_management', 'scrum', 'agile', 'planning'],
            'business_analysis': ['business_analyst', 'requirements', 'specification', 'process'],
            'compliance': ['compliance', 'audit', 'governance', 'policy', 'regulatory'],
            
            # Content and Communication specializations
            'content': ['content', 'copywriting', 'documentation', 'technical_writing'],
            'customer_support': ['support', 'helpdesk', 'customer_service', 'ticketing'],
            'marketing': ['marketing', 'campaign', 'promotion', 'seo', 'social_media'],
            
            # Framework-specific specializations
            'orchestrator': ['orchestrator', 'coordinator', 'workflow', 'pipeline'],
            'scaffolding': ['scaffolding', 'template', 'generator', 'boilerplate'],
            'architecture': ['architect', 'architecture', 'design_pattern', 'system_design'],
            'code_review': ['code_review', 'review', 'quality_assurance', 'peer_review'],
            'memory_management': ['memory', 'cache', 'storage', 'persistence'],
            'knowledge_base': ['knowledge', 'kb', 'documentation', 'wiki', 'reference'],
            
            # Integration and Workflow specializations
            'integration': ['integration', 'connector', 'bridge', 'adapter', 'sync'],
            'workflow': ['workflow', 'process', 'automation', 'orchestration']
        }
        
        # Check specialized agent patterns
        for agent_type, patterns in classification_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                return agent_type
        
        # Enhanced core agent type pattern matching (fallback)
        core_patterns = {
            'documentation': ['doc', 'docs', 'manual', 'guide', 'readme'],
            'ticketing': ['ticket', 'issue', 'bug', 'task', 'jira'],
            'version_control': ['version', 'git', 'vcs', 'commit', 'branch', 'merge'],
            'qa': ['qa', 'quality', 'assurance', 'validation', 'verification'],
            'research': ['research', 'analyze', 'investigate', 'study', 'explore'],
            'ops': ['ops', 'operations', 'maintenance', 'administration'],
            'security': ['security', 'auth', 'permission', 'vulnerability', 'encryption'],
            'engineer': ['engineer', 'code', 'develop', 'programming', 'implementation'],
            'data_engineer': ['data_engineer', 'etl', 'pipeline', 'warehouse']
        }
        
        for core_type, patterns in core_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                return core_type
        
        # Path-based classification hints
        path_str = str(agent_file).lower()
        if 'frontend' in path_str or 'ui' in path_str:
            return 'frontend'
        elif 'backend' in path_str or 'api' in path_str:
            return 'backend'
        elif 'database' in path_str or 'db' in path_str:
            return 'database'
        elif 'test' in path_str:
            return 'testing'
        elif 'deploy' in path_str:
            return 'deployment'
        
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
    
    def _validate_agents(self, agents: Dict[str, AgentMetadata]) -> Dict[str, AgentMetadata]:
        """
        Enhanced agent validation with specialized agent verification for ISS-0118.
        
        Args:
            agents: Dictionary of agents to validate
            
        Returns:
            Validated agents dictionary with validation scores
        """
        validated = {}
        
        for name, metadata in agents.items():
            try:
                validation_score = 0.0
                validation_errors = []
                
                # Basic file validation
                if not Path(metadata.path).exists():
                    metadata.validated = False
                    metadata.error_message = "File not found"
                    metadata.validation_score = 0.0
                    validated[name] = metadata
                    continue
                
                validation_score += 10  # File exists
                
                # Syntax validation (basic Python syntax check)
                try:
                    with open(metadata.path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, metadata.path, 'exec')
                    validation_score += 20  # Valid syntax
                except SyntaxError as e:
                    validation_errors.append(f"Syntax error: {e}")
                    validation_score -= 10
                
                # Enhanced validation for specialized agents
                validation_score += self._validate_specialized_agent(metadata, content)
                
                # Hybrid agent validation
                if metadata.is_hybrid:
                    validation_score += self._validate_hybrid_agent(metadata)
                
                # Capability consistency validation
                validation_score += self._validate_capability_consistency(metadata)
                
                # Framework compatibility validation
                validation_score += self._validate_framework_compatibility(metadata)
                
                # Set validation results
                metadata.validation_score = max(0.0, min(100.0, validation_score))
                metadata.validated = validation_score >= 50.0  # 50% threshold
                
                if validation_errors:
                    metadata.error_message = "; ".join(validation_errors)
                else:
                    metadata.error_message = None
                
                validated[name] = metadata
                
            except Exception as e:
                logger.warning(f"Validation error for agent {name}: {e}")
                metadata.validated = False
                metadata.error_message = str(e)
                metadata.validation_score = 0.0
                validated[name] = metadata
        
        return validated
    
    def _validate_specialized_agent(self, metadata: AgentMetadata, content: str) -> float:
        """
        Validate specialized agent requirements and capabilities.
        
        Args:
            metadata: Agent metadata
            content: Agent file content
            
        Returns:
            Validation score contribution
        """
        score = 0.0
        
        # Validate specialization alignment
        if metadata.specializations:
            score += 15  # Has specializations
            
            # Check if specializations align with agent type
            type_alignment = any(spec.lower() in metadata.type.lower() or 
                               metadata.type.lower() in spec.lower() 
                               for spec in metadata.specializations)
            if type_alignment:
                score += 10
        
        # Validate framework usage
        if metadata.frameworks:
            score += 10  # Uses frameworks
            
            # Check for proper import statements
            for framework in metadata.frameworks:
                if framework.lower() in content.lower():
                    score += 2  # Framework properly imported
        
        # Validate domain expertise
        if metadata.domains:
            score += 8  # Has domain expertise
        
        # Validate role definitions
        if metadata.roles:
            score += 7  # Has defined roles
        
        return score
    
    def _validate_hybrid_agent(self, metadata: AgentMetadata) -> float:
        """
        Validate hybrid agent configuration.
        
        Args:
            metadata: Agent metadata
            
        Returns:
            Validation score contribution
        """
        score = 0.0
        
        if metadata.is_hybrid and metadata.hybrid_types:
            # Bonus for being hybrid
            score += 5
            
            # Validate hybrid type consistency
            if len(metadata.hybrid_types) >= 2:
                score += 10  # Valid hybrid combination
            
            # Check for capability coverage across types
            type_coverage = len(set(metadata.hybrid_types))
            score += type_coverage * 2  # Coverage bonus
        
        return score
    
    def _validate_capability_consistency(self, metadata: AgentMetadata) -> float:
        """
        Validate capability consistency with agent type and specializations.
        
        Args:
            metadata: Agent metadata
            
        Returns:
            Validation score contribution
        """
        score = 0.0
        
        # Basic capability validation
        if metadata.capabilities:
            score += len(metadata.capabilities) * 0.5  # Base capability score
            
            # Check for consistent naming
            consistent_caps = sum(1 for cap in metadata.capabilities 
                                if not cap.startswith('_'))
            score += consistent_caps * 0.3
        
        # Validate complexity assessment
        complexity_levels = ['basic', 'intermediate', 'advanced', 'expert']
        if metadata.complexity_level in complexity_levels:
            score += 5
            
            # Bonus for higher complexity with sufficient capabilities
            complexity_index = complexity_levels.index(metadata.complexity_level)
            expected_caps = (complexity_index + 1) * 5
            if len(metadata.capabilities) >= expected_caps:
                score += 5
        
        return score
    
    def _validate_framework_compatibility(self, metadata: AgentMetadata) -> float:
        """
        Validate framework compatibility and integration.
        
        Args:
            metadata: Agent metadata
            
        Returns:
            Validation score contribution
        """
        score = 0.0
        
        if metadata.frameworks:
            # Validate framework combinations
            compatible_combinations = {
                'react': ['typescript', 'javascript', 'webpack'],
                'django': ['python', 'postgresql', 'redis'],
                'fastapi': ['python', 'pydantic', 'asyncio'],
                'kubernetes': ['docker', 'yaml', 'helm']
            }
            
            for framework in metadata.frameworks:
                if framework in compatible_combinations:
                    compatible_techs = compatible_combinations[framework]
                    compatibility_score = sum(1 for tech in compatible_techs 
                                            if any(tech in cap.lower() for cap in metadata.capabilities))
                    score += compatibility_score * 2
        
        return score
    
    def _is_discovery_cache_valid(self) -> bool:
        """Check if discovery cache is still valid"""
        if self.last_discovery_time is None:
            return False
        return (time.time() - self.last_discovery_time) < self.discovery_cache_ttl
    
    def get_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """
        Get specific agent metadata
        
        Args:
            agent_name: Name of agent to retrieve
            
        Returns:
            AgentMetadata or None if not found
        """
        if not self.registry:
            self.discover_agents()
        
        return self.registry.get(agent_name)
    
    def list_agents(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """
        List agents with optional filtering
        
        Args:
            agent_type: Filter by agent type
            tier: Filter by hierarchy tier
            
        Returns:
            List of matching AgentMetadata
        """
        if not self.registry:
            self.discover_agents()
        
        agents = list(self.registry.values())
        
        if agent_type:
            agents = [a for a in agents if a.type == agent_type]
        
        if tier:
            agents = [a for a in agents if a.tier == tier]
        
        return agents
    
    def listAgents(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        List agents with optional filtering (camelCase wrapper for compatibility)
        
        This method provides a camelCase interface to maintain compatibility with
        the CLAUDE.md documentation while preserving the snake_case Python convention.
        
        Args:
            agent_type: Filter by agent type
            tier: Filter by hierarchy tier
            
        Returns:
            Dictionary of agent name -> agent metadata
        """
        agents = self.list_agents(agent_type=agent_type, tier=tier)
        
        # Convert to expected dictionary format
        return {
            agent.name: {
                'type': agent.type,
                'path': agent.path,
                'tier': agent.tier,
                'last_modified': agent.last_modified,
                'specializations': agent.specializations,
                'description': agent.description,
                'validated': agent.validated,
                'complexity_level': agent.complexity_level,
                'preferred_model': agent.preferred_model
            } for agent in agents
        }
    
    def get_agent_types(self) -> Set[str]:
        """
        Get all discovered agent types
        
        Returns:
            Set of agent types
        """
        if not self.registry:
            self.discover_agents()
        
        return {metadata.type for metadata in self.registry.values()}
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics and metrics
        
        Returns:
            Dictionary of registry statistics
        """
        if not self.registry:
            self.discover_agents()
        
        stats = {
            'total_agents': len(self.registry),
            'validated_agents': len([a for a in self.registry.values() if a.validated]),
            'failed_agents': len([a for a in self.registry.values() if not a.validated]),
            'agent_types': len(self.get_agent_types()),
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
    
    def refresh_agent(self, agent_name: str) -> Optional[AgentMetadata]:
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
        updated_metadata = self._extract_agent_metadata(agent_file, current_metadata.tier)
        if updated_metadata:
            # Validate updated agent
            validated = self._validate_agents({agent_name: updated_metadata})
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
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check on the AgentRegistry.
        
        Returns:
            Dictionary with health status information
        """
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check 1: Discovery paths accessibility
            discovery_paths_status = []
            accessible_paths = 0
            for path in self.discovery_paths:
                path_status = {
                    'path': str(path),
                    'exists': path.exists(),
                    'readable': path.exists() and os.access(path, os.R_OK)
                }
                discovery_paths_status.append(path_status)
                if path_status['readable']:
                    accessible_paths += 1
            
            health_status['checks']['discovery_paths'] = {
                'total': len(self.discovery_paths),
                'accessible': accessible_paths,
                'details': discovery_paths_status
            }
            
            if accessible_paths == 0:
                health_status['errors'].append('No accessible discovery paths found')
                health_status['status'] = 'critical'
            elif accessible_paths < len(self.discovery_paths):
                health_status['warnings'].append(f'Only {accessible_paths}/{len(self.discovery_paths)} discovery paths are accessible')
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'degraded'
            
            # Check 2: Cache service availability
            try:
                cache_test_key = 'agent_registry_health_check_test'
                self.cache_service.set(cache_test_key, {'test': True}, ttl=1)
                cache_result = self.cache_service.get(cache_test_key)
                cache_healthy = cache_result is not None and cache_result.get('test') == True
                
                health_status['checks']['cache_service'] = {
                    'available': True,
                    'functional': cache_healthy,
                    'type': type(self.cache_service).__name__
                }
                
                if not cache_healthy:
                    health_status['warnings'].append('Cache service is not functioning properly')
                    if health_status['status'] == 'healthy':
                        health_status['status'] = 'degraded'
                        
            except Exception as e:
                health_status['checks']['cache_service'] = {
                    'available': False,
                    'error': str(e)
                }
                health_status['warnings'].append(f'Cache service error: {e}')
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'degraded'
            
            # Check 3: Model selector availability
            try:
                model_selector_status = self.model_selector is not None
                health_status['checks']['model_selector'] = {
                    'available': model_selector_status,
                    'type': type(self.model_selector).__name__ if model_selector_status else None
                }
                
                if not model_selector_status:
                    health_status['warnings'].append('Model selector not available')
                    
            except Exception as e:
                health_status['checks']['model_selector'] = {
                    'available': False,
                    'error': str(e)
                }
                health_status['warnings'].append(f'Model selector error: {e}')
            
            # Check 4: Registry state
            health_status['checks']['registry'] = {
                'loaded': bool(self.registry),
                'agent_count': len(self.registry),
                'last_discovery': self.last_discovery_time,
                'cache_valid': self._is_discovery_cache_valid() if self.last_discovery_time else False
            }
            
            # Check 5: Agent type coverage
            if self.registry:
                discovered_types = set(metadata.type for metadata in self.registry.values())
                core_coverage = len(self.core_agent_types.intersection(discovered_types))
                
                health_status['checks']['agent_coverage'] = {
                    'core_types_discovered': core_coverage,
                    'core_types_total': len(self.core_agent_types),
                    'specialized_types_discovered': len(discovered_types.intersection(self.specialized_agent_types)),
                    'total_types_discovered': len(discovered_types)
                }
                
                if core_coverage < len(self.core_agent_types):
                    missing_core = self.core_agent_types - discovered_types
                    health_status['warnings'].append(f'Missing core agent types: {", ".join(sorted(missing_core))}')
            else:
                health_status['checks']['agent_coverage'] = {
                    'message': 'No agents discovered yet'
                }
            
            # Check 6: System resources
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                
                health_status['checks']['system_resources'] = {
                    'memory_usage_mb': memory_info.rss / 1024 / 1024,
                    'available': True
                }
            except ImportError:
                health_status['checks']['system_resources'] = {
                    'available': False,
                    'note': 'psutil not installed'
                }
            except Exception as e:
                health_status['checks']['system_resources'] = {
                    'available': False,
                    'error': str(e)
                }
            
            # Overall health assessment
            if health_status['errors']:
                health_status['status'] = 'critical'
            elif len(health_status['warnings']) > 3:
                health_status['status'] = 'degraded'
            
            health_status['summary'] = {
                'status': health_status['status'],
                'error_count': len(health_status['errors']),
                'warning_count': len(health_status['warnings']),
                'checks_passed': sum(1 for check in health_status['checks'].values() 
                                   if isinstance(check, dict) and check.get('available', True))
            }
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['errors'].append(f'Health check failed: {str(e)}')
            health_status['exception'] = str(e)
        
        return health_status