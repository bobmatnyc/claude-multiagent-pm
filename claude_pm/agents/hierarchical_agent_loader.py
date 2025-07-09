#!/usr/bin/env python3
"""
Hierarchical Agent Loader for Claude PM Framework
===============================================

This module provides a comprehensive agent loading system with three-tier hierarchy:
1. System Agents (framework-level): Core framework functionality
2. User Agents (global): User-specific customizations across all projects  
3. Project Agents (local): Project-specific implementations with inheritance

Key Features:
- Hierarchical agent precedence (Project > User > System)
- Dynamic agent discovery and loading
- Configuration inheritance and override mechanisms
- Agent validation and health checking
- Template-based agent creation
- CLI integration for agent management
"""

import os
import sys
import json
import yaml
import importlib.util
import inspect
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Union, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime

from ..core.base_service import BaseService
from ..core.config import Config
from ..core.logging_config import setup_logging


@dataclass
class AgentInfo:
    """Information about an available agent."""
    name: str
    agent_type: str
    tier: str  # system, user, project
    path: Path
    class_name: str
    priority: int  # 1=system, 2=user, 3=project
    config: Dict[str, Any] = field(default_factory=dict)
    loaded: bool = False
    instance: Optional[Any] = None
    health_status: str = "unknown"
    last_loaded: Optional[str] = None
    
    @property
    def tier_display(self) -> str:
        """Display-friendly tier name."""
        return {
            "system": "System (Framework)",
            "user": "User (Global)",
            "project": "Project (Local)"
        }.get(self.tier, self.tier)


@dataclass
class AgentHierarchy:
    """Represents the complete agent hierarchy."""
    system_agents: Dict[str, AgentInfo] = field(default_factory=dict)
    user_agents: Dict[str, AgentInfo] = field(default_factory=dict)
    project_agents: Dict[str, AgentInfo] = field(default_factory=dict)
    
    def get_all_agents(self) -> Dict[str, AgentInfo]:
        """Get all agents across all tiers."""
        all_agents = {}
        all_agents.update(self.system_agents)
        all_agents.update(self.user_agents)
        all_agents.update(self.project_agents)
        return all_agents
    
    def get_agent_by_type(self, agent_type: str) -> Optional[AgentInfo]:
        """Get the highest priority agent of a specific type."""
        # Check project agents first (highest priority)
        for name, agent in self.project_agents.items():
            if agent.agent_type == agent_type:
                return agent
        
        # Check user agents second
        for name, agent in self.user_agents.items():
            if agent.agent_type == agent_type:
                return agent
        
        # Check system agents last (fallback)
        for name, agent in self.system_agents.items():
            if agent.agent_type == agent_type:
                return agent
        
        return None
    
    def get_available_types(self) -> List[str]:
        """Get all available agent types."""
        types = set()
        for agent in self.get_all_agents().values():
            types.add(agent.agent_type)
        return sorted(list(types))


class HierarchicalAgentLoader(BaseService):
    """
    Hierarchical Agent Loader for three-tier agent management.
    
    This class manages agent discovery, loading, and hierarchy across:
    - System agents (framework core)
    - User agents (global customizations)
    - Project agents (local overrides)
    
    Features:
    - Automatic agent discovery
    - Priority-based loading
    - Configuration inheritance
    - Health monitoring
    - Template management
    """
    
    def __init__(
        self,
        framework_path: Path,
        user_home: Path,
        project_path: Path,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name="hierarchical_agent_loader", config=config)
        
        self.framework_path = framework_path
        self.user_home = user_home
        self.project_path = project_path
        
        # Agent directory paths
        self.system_agents_path = framework_path / "claude_pm" / "agents"
        self.user_agents_path = user_home / ".claude-multiagent-pm" / "agents" / "user-defined"
        self.project_agents_path = project_path / ".claude-multiagent-pm" / "agents" / "project-specific"
        
        # Agent hierarchy
        self.hierarchy = AgentHierarchy()
        
        # Loaded agents cache
        self._loaded_agents: Dict[str, Any] = {}
        
        # Configuration cache
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(f"Initialized HierarchicalAgentLoader")
        self.logger.info(f"  System agents: {self.system_agents_path}")
        self.logger.info(f"  User agents: {self.user_agents_path}")
        self.logger.info(f"  Project agents: {self.project_agents_path}")
    
    async def _initialize(self) -> None:
        """Initialize the agent loader."""
        try:
            # Create agent directories if they don't exist
            self._ensure_agent_directories()
            
            # Load agent configuration
            await self._load_agent_configuration()
            
            # Discover all agents
            await self._discover_agents()
            
            self.logger.info("HierarchicalAgentLoader initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize HierarchicalAgentLoader: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup agent loader resources."""
        try:
            # Unload all agents
            await self._unload_all_agents()
            
            # Clear caches
            self._loaded_agents.clear()
            self._config_cache.clear()
            
            self.logger.info("HierarchicalAgentLoader cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup HierarchicalAgentLoader: {e}")
            raise
    
    def _ensure_agent_directories(self) -> None:
        """Ensure all agent directories exist."""
        directories = [
            self.system_agents_path,
            self.user_agents_path,
            self.project_agents_path,
            self.user_agents_path / "templates",
            self.project_agents_path / "templates",
            self.project_agents_path / "config"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py if it doesn't exist
            init_file = directory / "__init__.py"
            if not init_file.exists() and directory.name != "templates":
                init_file.write_text('"""Agent package initialization."""\n')
    
    async def _load_agent_configuration(self) -> None:
        """Load agent configuration from hierarchy."""
        config_files = [
            self.project_path / ".claude-multiagent-pm" / "config" / "agents.yaml",
            self.user_home / ".claude-multiagent-pm" / "config" / "agents.yaml",
            self.framework_path / "config" / "agents.yaml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                        self._config_cache[str(config_file)] = config
                        self.logger.debug(f"Loaded agent config from {config_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to load config from {config_file}: {e}")
    
    async def _discover_agents(self) -> None:
        """Discover all agents in the hierarchy."""
        # Clear existing hierarchy
        self.hierarchy = AgentHierarchy()
        
        # Discover system agents
        await self._discover_system_agents()
        
        # Discover user agents
        await self._discover_user_agents()
        
        # Discover project agents
        await self._discover_project_agents()
        
        # Log discovery summary
        total_agents = len(self.hierarchy.get_all_agents())
        self.logger.info(f"Discovered {total_agents} agents across hierarchy")
        self.logger.info(f"  System: {len(self.hierarchy.system_agents)}")
        self.logger.info(f"  User: {len(self.hierarchy.user_agents)}")
        self.logger.info(f"  Project: {len(self.hierarchy.project_agents)}")
    
    async def _discover_system_agents(self) -> None:
        """Discover system agents in framework directory."""
        if not self.system_agents_path.exists():
            return
        
        for agent_file in self.system_agents_path.glob("*.py"):
            if agent_file.stem.startswith("_"):
                continue
            
            try:
                agent_info = await self._analyze_agent_file(agent_file, "system", 1)
                if agent_info:
                    self.hierarchy.system_agents[agent_info.name] = agent_info
                    self.logger.debug(f"Discovered system agent: {agent_info.name}")
            except Exception as e:
                self.logger.warning(f"Failed to analyze system agent {agent_file}: {e}")
    
    async def _discover_user_agents(self) -> None:
        """Discover user agents in global directory."""
        if not self.user_agents_path.exists():
            return
        
        for agent_file in self.user_agents_path.glob("*.py"):
            if agent_file.stem.startswith("_"):
                continue
            
            try:
                agent_info = await self._analyze_agent_file(agent_file, "user", 2)
                if agent_info:
                    self.hierarchy.user_agents[agent_info.name] = agent_info
                    self.logger.debug(f"Discovered user agent: {agent_info.name}")
            except Exception as e:
                self.logger.warning(f"Failed to analyze user agent {agent_file}: {e}")
    
    async def _discover_project_agents(self) -> None:
        """Discover project agents in local directory."""
        if not self.project_agents_path.exists():
            return
        
        for agent_file in self.project_agents_path.glob("*.py"):
            if agent_file.stem.startswith("_"):
                continue
            
            try:
                agent_info = await self._analyze_agent_file(agent_file, "project", 3)
                if agent_info:
                    self.hierarchy.project_agents[agent_info.name] = agent_info
                    self.logger.debug(f"Discovered project agent: {agent_info.name}")
            except Exception as e:
                self.logger.warning(f"Failed to analyze project agent {agent_file}: {e}")
    
    async def _analyze_agent_file(self, file_path: Path, tier: str, priority: int) -> Optional[AgentInfo]:
        """Analyze an agent file and extract information."""
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find agent classes
            agent_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    not name.startswith('_') and 
                    hasattr(obj, '__module__') and 
                    obj.__module__ == module.__name__):
                    agent_classes.append((name, obj))
            
            if not agent_classes:
                return None
            
            # Use first agent class found
            class_name, agent_class = agent_classes[0]
            
            # Determine agent type
            agent_type = self._determine_agent_type(file_path.stem, class_name, agent_class)
            
            # Create agent info
            agent_info = AgentInfo(
                name=file_path.stem,
                agent_type=agent_type,
                tier=tier,
                path=file_path,
                class_name=class_name,
                priority=priority
            )
            
            return agent_info
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze agent file {file_path}: {e}")
            return None
    
    def _determine_agent_type(self, file_name: str, class_name: str, agent_class: Type) -> str:
        """Determine the agent type from file name and class."""
        # Check for common agent type patterns
        type_patterns = {
            'engineer': ['engineer', 'eng', 'development', 'dev'],
            'ops': ['ops', 'operations', 'deploy', 'devops'],
            'qa': ['qa', 'quality', 'test', 'testing'],
            'security': ['security', 'sec', 'auth', 'authentication'],
            'architect': ['architect', 'architecture', 'design'],
            'orchestrator': ['orchestrator', 'orchestration', 'coordination'],
            'pm': ['pm', 'project', 'management', 'manager'],
            'data': ['data', 'database', 'db', 'analytics'],
            'ui': ['ui', 'ux', 'interface', 'frontend'],
            'integration': ['integration', 'api', 'webhook', 'connector'],
            'performance': ['performance', 'perf', 'monitoring', 'metrics'],
            'research': ['research', 'analysis', 'investigation'],
            'documentation': ['doc', 'docs', 'documentation', 'readme'],
            'scaffolding': ['scaffold', 'scaffolding', 'template', 'generator']
        }
        
        # Check file name first
        file_lower = file_name.lower()
        for agent_type, patterns in type_patterns.items():
            if any(pattern in file_lower for pattern in patterns):
                return agent_type
        
        # Check class name
        class_lower = class_name.lower()
        for agent_type, patterns in type_patterns.items():
            if any(pattern in class_lower for pattern in patterns):
                return agent_type
        
        # Default to generic
        return "generic"
    
    async def load_agent(self, agent_type: str, **kwargs) -> Optional[Any]:
        """
        Load an agent with hierarchical precedence.
        
        Args:
            agent_type: Type of agent to load
            **kwargs: Additional arguments for agent initialization
            
        Returns:
            Agent instance or None if not found
        """
        # Check if already loaded
        if agent_type in self._loaded_agents:
            return self._loaded_agents[agent_type]
        
        # Get agent with highest priority
        agent_info = self.hierarchy.get_agent_by_type(agent_type)
        if not agent_info:
            self.logger.warning(f"No agent found for type: {agent_type}")
            return None
        
        try:
            # Load the agent
            agent_instance = await self._load_agent_instance(agent_info, **kwargs)
            
            # Cache the loaded agent
            self._loaded_agents[agent_type] = agent_instance
            
            # Update agent info
            agent_info.loaded = True
            agent_info.instance = agent_instance
            agent_info.last_loaded = datetime.now().isoformat()
            agent_info.health_status = "loaded"
            
            self.logger.info(f"Loaded {agent_type} agent from {agent_info.tier} tier")
            return agent_instance
            
        except Exception as e:
            self.logger.error(f"Failed to load {agent_type} agent: {e}")
            agent_info.health_status = "error"
            return None
    
    async def _load_agent_instance(self, agent_info: AgentInfo, **kwargs) -> Any:
        """Load an agent instance from agent info."""
        # Load the module
        spec = importlib.util.spec_from_file_location(agent_info.name, agent_info.path)
        if not spec or not spec.loader:
            raise ValueError(f"Cannot load module from {agent_info.path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the agent class
        agent_class = getattr(module, agent_info.class_name)
        
        # Prepare initialization arguments
        init_args = {}
        init_args.update(agent_info.config)
        init_args.update(kwargs)
        
        # Create instance
        if inspect.iscoroutinefunction(agent_class.__init__):
            agent_instance = await agent_class(**init_args)
        else:
            agent_instance = agent_class(**init_args)
        
        return agent_instance
    
    async def unload_agent(self, agent_type: str) -> bool:
        """Unload a specific agent."""
        if agent_type not in self._loaded_agents:
            return False
        
        try:
            agent_instance = self._loaded_agents[agent_type]
            
            # Cleanup agent if it supports it
            if hasattr(agent_instance, 'cleanup'):
                if inspect.iscoroutinefunction(agent_instance.cleanup):
                    await agent_instance.cleanup()
                else:
                    agent_instance.cleanup()
            
            # Remove from cache
            del self._loaded_agents[agent_type]
            
            # Update agent info
            agent_info = self.hierarchy.get_agent_by_type(agent_type)
            if agent_info:
                agent_info.loaded = False
                agent_info.instance = None
                agent_info.health_status = "unloaded"
            
            self.logger.info(f"Unloaded {agent_type} agent")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload {agent_type} agent: {e}")
            return False
    
    async def _unload_all_agents(self) -> None:
        """Unload all loaded agents."""
        for agent_type in list(self._loaded_agents.keys()):
            await self.unload_agent(agent_type)
    
    async def reload_agent(self, agent_type: str, **kwargs) -> Optional[Any]:
        """Reload an agent."""
        # Unload first
        await self.unload_agent(agent_type)
        
        # Rediscover agents to pick up changes
        await self._discover_agents()
        
        # Load again
        return await self.load_agent(agent_type, **kwargs)
    
    def get_available_agents(self) -> Dict[str, List[AgentInfo]]:
        """Get all available agents organized by tier."""
        return {
            "system": list(self.hierarchy.system_agents.values()),
            "user": list(self.hierarchy.user_agents.values()),
            "project": list(self.hierarchy.project_agents.values())
        }
    
    def get_agent_info(self, agent_name: str) -> Optional[AgentInfo]:
        """Get information about a specific agent."""
        all_agents = self.hierarchy.get_all_agents()
        return all_agents.get(agent_name)
    
    def get_loaded_agents(self) -> Dict[str, Any]:
        """Get all currently loaded agents."""
        return self._loaded_agents.copy()
    
    async def validate_agent_hierarchy(self) -> Dict[str, Any]:
        """Validate the agent hierarchy consistency."""
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "summary": {
                "total_agents": 0,
                "system_agents": 0,
                "user_agents": 0,
                "project_agents": 0,
                "loaded_agents": len(self._loaded_agents)
            }
        }
        
        try:
            # Count agents
            validation_results["summary"]["system_agents"] = len(self.hierarchy.system_agents)
            validation_results["summary"]["user_agents"] = len(self.hierarchy.user_agents)
            validation_results["summary"]["project_agents"] = len(self.hierarchy.project_agents)
            validation_results["summary"]["total_agents"] = len(self.hierarchy.get_all_agents())
            
            # Check for agent conflicts
            agent_types = {}
            for agent_info in self.hierarchy.get_all_agents().values():
                if agent_info.agent_type not in agent_types:
                    agent_types[agent_info.agent_type] = []
                agent_types[agent_info.agent_type].append(agent_info)
            
            # Check for multiple agents of same type
            for agent_type, agents in agent_types.items():
                if len(agents) > 1:
                    highest_priority = max(agents, key=lambda x: x.priority)
                    validation_results["warnings"].append(
                        f"Multiple {agent_type} agents found. Using {highest_priority.tier} tier."
                    )
            
            # Check directory structure
            required_dirs = [
                self.system_agents_path,
                self.user_agents_path,
                self.project_agents_path
            ]
            
            for directory in required_dirs:
                if not directory.exists():
                    validation_results["issues"].append(f"Missing directory: {directory}")
                    validation_results["valid"] = False
            
            # Check for essential system agents
            essential_agents = ["system_init", "orchestrator", "pm"]
            for agent_type in essential_agents:
                if not any(agent.agent_type == agent_type for agent in self.hierarchy.system_agents.values()):
                    validation_results["warnings"].append(f"Missing essential system agent: {agent_type}")
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Validation error: {str(e)}")
        
        return validation_results
    
    async def create_agent_from_template(
        self, 
        agent_type: str, 
        agent_name: str, 
        tier: str = "project",
        template_name: str = "default"
    ) -> bool:
        """Create a new agent from template."""
        try:
            # Determine target directory
            if tier == "system":
                target_dir = self.system_agents_path
            elif tier == "user":
                target_dir = self.user_agents_path
            elif tier == "project":
                target_dir = self.project_agents_path
            else:
                raise ValueError(f"Invalid tier: {tier}")
            
            # Load template
            template_path = self._get_template_path(agent_type, template_name, tier)
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            
            # Generate agent file
            agent_file = target_dir / f"{agent_name}.py"
            if agent_file.exists():
                raise FileExistsError(f"Agent file already exists: {agent_file}")
            
            # Read template and substitute variables
            template_content = template_path.read_text()
            agent_content = self._substitute_template_variables(
                template_content, 
                agent_name, 
                agent_type, 
                tier
            )
            
            # Write agent file
            agent_file.write_text(agent_content)
            
            # Rediscover agents
            await self._discover_agents()
            
            self.logger.info(f"Created {agent_type} agent: {agent_name} in {tier} tier")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create agent {agent_name}: {e}")
            return False
    
    def _get_template_path(self, agent_type: str, template_name: str, tier: str) -> Path:
        """Get the template file path."""
        # Check tier-specific templates first
        if tier == "project":
            template_dir = self.project_agents_path / "templates"
        elif tier == "user":
            template_dir = self.user_agents_path / "templates"
        else:
            template_dir = self.system_agents_path / "templates"
        
        template_file = template_dir / f"{agent_type}_{template_name}.py.template"
        if template_file.exists():
            return template_file
        
        # Fall back to default template
        default_template = template_dir / "default_agent.py.template"
        return default_template
    
    def _substitute_template_variables(
        self, 
        template_content: str, 
        agent_name: str, 
        agent_type: str, 
        tier: str
    ) -> str:
        """Substitute variables in template content."""
        substitutions = {
            "{{AGENT_NAME}}": agent_name,
            "{{AGENT_TYPE}}": agent_type,
            "{{AGENT_TIER}}": tier,
            "{{CLASS_NAME}}": self._to_class_name(agent_name),
            "{{TIMESTAMP}}": datetime.now().isoformat(),
            "{{YEAR}}": str(datetime.now().year)
        }
        
        content = template_content
        for placeholder, value in substitutions.items():
            content = content.replace(placeholder, value)
        
        return content
    
    def _to_class_name(self, agent_name: str) -> str:
        """Convert agent name to class name."""
        return ''.join(word.capitalize() for word in agent_name.split('_'))
    
    async def get_agent_health_status(self) -> Dict[str, Any]:
        """Get health status for all agents."""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.hierarchy.get_all_agents()),
            "loaded_agents": len(self._loaded_agents),
            "tiers": {
                "system": {
                    "count": len(self.hierarchy.system_agents),
                    "agents": {}
                },
                "user": {
                    "count": len(self.hierarchy.user_agents),
                    "agents": {}
                },
                "project": {
                    "count": len(self.hierarchy.project_agents),
                    "agents": {}
                }
            }
        }
        
        # Check health of each agent
        for tier_name, tier_agents in [
            ("system", self.hierarchy.system_agents),
            ("user", self.hierarchy.user_agents),
            ("project", self.hierarchy.project_agents)
        ]:
            for agent_name, agent_info in tier_agents.items():
                health_status["tiers"][tier_name]["agents"][agent_name] = {
                    "type": agent_info.agent_type,
                    "health": agent_info.health_status,
                    "loaded": agent_info.loaded,
                    "last_loaded": agent_info.last_loaded
                }
        
        return health_status
    
    async def _health_check(self) -> Dict[str, bool]:
        """Custom health checks for the agent loader."""
        checks = {}
        
        # Check directory structure
        checks["system_dir_exists"] = self.system_agents_path.exists()
        checks["user_dir_exists"] = self.user_agents_path.exists()
        checks["project_dir_exists"] = self.project_agents_path.exists()
        
        # Check for essential agents
        essential_agents = ["system_init", "orchestrator"]
        for agent_type in essential_agents:
            agent_info = self.hierarchy.get_agent_by_type(agent_type)
            checks[f"essential_{agent_type}_available"] = agent_info is not None
        
        # Check loaded agents health
        checks["loaded_agents_healthy"] = len(self._loaded_agents) > 0
        
        return checks