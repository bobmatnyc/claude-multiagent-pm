#!/usr/bin/env python3
"""
System Initialization Agent for Claude PM Framework
=====================================================

This agent specializes in framework initialization, setup, and configuration
management. It ensures proper deployment and dependency verification across
different working directories.

Responsibilities:
- Framework initialization and setup
- Dependency installation and verification
- Configuration file generation
- Local directory structure creation
- Troubleshooting setup issues
"""

import os
import sys
import json
import yaml
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.base_service import BaseService
from ..core.config import Config
from ..core.logging_config import setup_logging


class SystemInitAgent(BaseService):
    """
    Specialized agent for Claude PM Framework system initialization and setup.
    
    This agent handles:
    - Framework deployment setup (multi-project orchestrator)
    - Dependency verification and installation
    - Local configuration management
    - Directory structure creation (framework vs project)
    - Troubleshooting and diagnostics
    
    Directory Structure:
    - Framework Directory: Global user agents, system training data
    - Working Directory: Current working location
    - Project Directory: Project-specific agents and configurations
    """
    
    def __init__(self, working_dir: Path = None, project_dir: Path = None):
        super().__init__(name="system_init_agent")
        self.working_dir = working_dir or Path.cwd()
        self.project_dir = project_dir or self._detect_project_directory()
        self.framework_path = self._discover_framework_path()
        self.local_config_dir = self.working_dir / ".claude-multiagent-pm"
        self.project_config_dir = self.project_dir / ".claude-multiagent-pm"
        self.framework_config_dir = self.framework_path / ".claude-multiagent-pm" if self.framework_path else None
        self.console = Console()
        self.logger = setup_logging(__name__)
    
    async def _initialize(self) -> bool:
        """Initialize the System Init Agent service."""
        try:
            self.logger.info("System Init Agent initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize System Init Agent: {e}")
            return False
    
    async def _cleanup(self) -> bool:
        """Cleanup the System Init Agent service."""
        try:
            self.logger.info("System Init Agent cleanup completed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup System Init Agent: {e}")
            return False
        
    def _detect_project_directory(self) -> Path:
        """
        Detect the project directory for the current context.
        
        Project directory detection logic:
        1. Look for project indicators (.git, package.json, pyproject.toml, etc.)
        2. Check for existing .claude-multiagent-pm directory
        3. Use working directory as fallback
        """
        current = self.working_dir
        
        # Project indicators
        project_files = [
            ".git",
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            ".claude-multiagent-pm"
        ]
        
        # Walk up the directory tree to find project root
        while current != current.parent:
            for indicator in project_files:
                if (current / indicator).exists():
                    return current
            current = current.parent
        
        # Fallback to working directory
        return self.working_dir
    
    def _discover_framework_path(self) -> Optional[Path]:
        """Discover the Claude PM Framework installation path."""
        # Check environment variable first
        env_path = os.environ.get('CLAUDE_PM_FRAMEWORK_PATH')
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        # Check common installation locations
        home = Path.home()
        candidates = [
            home / "Projects" / "claude-multiagent-pm",
            home / "Clients" / "claude-multiagent-pm",
            Path.cwd(),
            Path.cwd().parent,
        ]
        
        for candidate in candidates:
            if candidate.exists() and (candidate / "claude_pm" / "__init__.py").exists():
                return candidate
        
        return None
    
    async def initialize_framework(self, force: bool = False) -> Dict[str, Any]:
        """
        Initialize the Claude PM Framework in the current directory.
        
        Args:
            force: Force reinitialize even if already set up
            
        Returns:
            Dict containing initialization results and status
        """
        self.logger.info(f"Starting framework initialization in {self.working_dir}")
        
        results = {
            "success": False,
            "working_directory": str(self.working_dir),
            "framework_location": str(self.framework_path),
            "steps_completed": [],
            "errors": [],
            "setup_status": "unknown"
        }
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                
                # Step 1: Check existing setup
                check_task = progress.add_task("Checking existing setup...", total=1)
                local_config_exists = self.local_config_dir.exists()
                
                if local_config_exists and not force:
                    progress.update(check_task, completed=1)
                    results["setup_status"] = "already_exists"
                    results["success"] = True
                    results["steps_completed"].append("check_existing")
                    return results
                
                progress.update(check_task, completed=1)
                results["steps_completed"].append("check_existing")
                
                # Step 2: Create directory structure
                structure_task = progress.add_task("Creating directory structure...", total=1)
                if self._create_directory_structure():
                    progress.update(structure_task, completed=1)
                    results["steps_completed"].append("directory_structure")
                else:
                    results["errors"].append("Failed to create directory structure")
                    return results
                
                # Step 3: Generate configuration files
                config_task = progress.add_task("Generating configuration files...", total=1)
                if await self._generate_configuration_files():
                    progress.update(config_task, completed=1)
                    results["steps_completed"].append("configuration_files")
                else:
                    results["errors"].append("Failed to generate configuration files")
                    return results
                
                # Step 4: Verify dependencies
                deps_task = progress.add_task("Verifying dependencies...", total=1)
                dependency_status = await self._verify_dependencies()
                results["dependencies"] = dependency_status
                progress.update(deps_task, completed=1)
                results["steps_completed"].append("dependency_verification")
                
                # Step 5: Final setup status
                results["setup_status"] = self._get_final_setup_status(dependency_status)
                results["success"] = True
                
        except Exception as e:
            self.logger.error(f"Framework initialization failed: {e}")
            results["errors"].append(f"Initialization failed: {str(e)}")
            results["success"] = False
        
        return results
    
    def _create_directory_structure(self) -> bool:
        """
        Create the enhanced .claude-multiagent-pm directory structure with three-tier agent hierarchy.
        
        Creates three types of directories:
        1. Framework directory: Global user agents, system training data
        2. Working directory: Current working location config
        3. Project directory: Project-specific agents and configurations
        
        Agent Hierarchy Structure:
        - System Agents: /framework/claude_pm/agents/ (core framework)
        - User Agents: ~/.claude-multiagent-pm/agents/user-defined/ (global)
        - Project Agents: $PROJECT/.claude-multiagent-pm/agents/project-specific/ (local)
        """
        try:
            # Framework directory structure (global) - ENHANCED WITH AGENT HIERARCHY
            if self.framework_config_dir:
                framework_dirs = [
                    self.framework_config_dir,
                    self.framework_config_dir / "config",
                    self.framework_config_dir / "agents" / "user-defined",  # Global user agents
                    self.framework_config_dir / "agents" / "user-defined" / "templates",  # User agent templates
                    self.framework_config_dir / "agents" / "system-trained",  # System training data
                    self.framework_config_dir / "agents" / "system-trained" / "patterns",  # Learned patterns
                    self.framework_config_dir / "templates" / "global",
                    self.framework_config_dir / "templates" / "agents",  # Agent templates
                    self.framework_config_dir / "logs" / "framework",
                    self.framework_config_dir / "logs" / "agents",  # Agent-specific logs
                    self.framework_config_dir / "cache" / "global",
                    self.framework_config_dir / "cache" / "agents"  # Agent cache
                ]
                
                for directory in framework_dirs:
                    directory.mkdir(parents=True, exist_ok=True)
            
            # Working directory structure (current session) - ENHANCED WITH AGENT HIERARCHY
            working_dirs = [
                self.local_config_dir,
                self.local_config_dir / "config",
                self.local_config_dir / "agents" / "project-specific",  # Project-local agents
                self.local_config_dir / "agents" / "project-specific" / "templates",  # Project agent templates
                self.local_config_dir / "agents" / "project-specific" / "config",  # Project agent config
                self.local_config_dir / "agents" / "hierarchy",  # Agent hierarchy metadata
                self.local_config_dir / "index",  # Project indexing system
                self.local_config_dir / "index" / "cache",  # Index cache files
                self.local_config_dir / "index" / "agents",  # Agent index data
                self.local_config_dir / "sessions",
                self.local_config_dir / "logs" / "working",
                self.local_config_dir / "logs" / "init",  # Initialization logs
                self.local_config_dir / "logs" / "agents",  # Agent operation logs
                self.local_config_dir / "cache" / "working",
                self.local_config_dir / "cache" / "agents",  # Agent cache
                self.local_config_dir / "templates" / "project",  # Project templates
                self.local_config_dir / "templates" / "agents"  # Agent templates
            ]
            
            for directory in working_dirs:
                directory.mkdir(parents=True, exist_ok=True)
            
            # Project directory structure (project-specific) - ENHANCED WITH AGENT HIERARCHY
            if self.project_dir != self.working_dir:
                project_dirs = [
                    self.project_config_dir,
                    self.project_config_dir / "config",
                    self.project_config_dir / "agents" / "project-specific",  # Project agents
                    self.project_config_dir / "agents" / "project-specific" / "templates",  # Project agent templates
                    self.project_config_dir / "agents" / "project-specific" / "config",  # Project agent config
                    self.project_config_dir / "agents" / "hierarchy",  # Agent hierarchy metadata
                    self.project_config_dir / "templates" / "project",
                    self.project_config_dir / "templates" / "agents",  # Agent templates
                    self.project_config_dir / "logs" / "project",
                    self.project_config_dir / "logs" / "agents",  # Agent operation logs
                    self.project_config_dir / "cache" / "project",
                    self.project_config_dir / "cache" / "agents"  # Agent cache
                ]
                
                for directory in project_dirs:
                    directory.mkdir(parents=True, exist_ok=True)
            
            # Create initial README files and agent hierarchy metadata
            self._create_initial_readme_files()
            self._create_agent_hierarchy_metadata()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory structure: {e}")
            return False
    
    def _create_initial_readme_files(self):
        """Create initial README files for guidance across all directory types."""
        
        # Framework directory READMEs (global)
        if self.framework_config_dir:
            framework_readme_contents = {
                "README.md": """# Claude PM Framework - Global Configuration

This directory contains global framework configuration and user agents.

## Directory Structure
- `agents/user-defined/`: Global user-defined agents (available across all projects)
- `agents/system-trained/`: System training data and learned patterns
- `templates/global/`: Global templates available to all projects
- `logs/framework/`: Framework-level operation logs
- `cache/global/`: Global cache and state files

## Multi-Project Orchestration
This framework acts as a multi-project orchestrator, managing:
- Global user agents shared across projects
- System-trained prompts and behaviors
- Framework-level configuration and settings
""",
                "agents/user-defined/README.md": """# Global User-Defined Agents

This directory contains user-defined agents that are available across ALL projects.

## Purpose
- Global agents that can be used in any project
- Shared agent behaviors and capabilities
- Framework-level agent definitions

## Structure
- Place your global agent files here
- Follow the framework's agent template structure
- Use the `.py` extension for Python agents
- Include proper documentation and type hints

## Usage
Global agents are automatically available to all projects using this framework.
""",
                "agents/system-trained/README.md": """# System Training Data

This directory contains system-trained prompts and learned behaviors.

## Purpose
- Store system-level training data
- Framework-learned patterns and behaviors
- Automated training improvements
- Performance optimization data

## Files
- System training configurations
- Learned behavior patterns
- Performance optimization data
- Automated improvement scripts

## Note
This directory is managed automatically by the framework's learning system.
""",
                "templates/global/README.md": """# Global Templates

This directory contains global templates available to all projects.

## Template Types
- Global agent templates
- Framework scaffolding templates
- Standard configuration templates
- Deployment templates

## Usage
Global templates are inherited by all projects and can be overridden at the project level.
"""
            }
            
            for path, content in framework_readme_contents.items():
                readme_path = self.framework_config_dir / path
                readme_path.parent.mkdir(parents=True, exist_ok=True)
                readme_path.write_text(content)
        
        # Working directory READMEs (current session)
        working_readme_contents = {
            "README.md": """# Claude PM Framework - Working Directory

This directory contains configuration for the current working session.

## Directory Structure
- `config/`: Working directory specific configuration
- `sessions/`: Session data and state
- `logs/working/`: Working directory operation logs
- `cache/working/`: Working directory cache files

## Purpose
This configuration manages the current working session and provides:
- Session-specific settings
- Working directory context
- Temporary session data
""",
            "sessions/README.md": """# Working Sessions

This directory contains session data and state for the current working directory.

## Contents
- Session state files
- Working context data
- Temporary session variables
- Session-specific configurations

## Note
Session data is temporary and tied to the current working directory.
"""
        }
        
        for path, content in working_readme_contents.items():
            readme_path = self.local_config_dir / path
            readme_path.parent.mkdir(parents=True, exist_ok=True)
            readme_path.write_text(content)
        
        # Project directory READMEs (project-specific)
        if self.project_dir != self.working_dir and self.project_config_dir:
            project_readme_contents = {
                "README.md": """# Claude PM Framework - Project Configuration

This directory contains project-specific configuration and agents.

## Directory Structure
- `agents/project-specific/`: Agents specific to this project only
- `templates/project/`: Project-specific templates
- `logs/project/`: Project operation logs
- `cache/project/`: Project cache files

## Purpose
Project-specific configuration that overrides global settings:
- Project-specific agents and behaviors
- Custom templates for this project
- Project-level logging and caching
""",
                "agents/project-specific/README.md": """# Project-Specific Agents

This directory contains agents that are specific to this project only.

## Purpose
- Project-specific agent implementations
- Custom behaviors for this project
- Project-tailored agent configurations

## Structure
- Place your project-specific agent files here
- Follow the framework's agent template structure
- Use the `.py` extension for Python agents
- Include proper documentation and type hints

## Usage
Project agents are only available within this specific project.
They can override or extend global agents.
""",
                "templates/project/README.md": """# Project Templates

This directory contains templates specific to this project.

## Template Types
- Project-specific agent templates
- Custom scaffolding templates
- Project configuration templates
- Deployment templates for this project

## Usage
Project templates override global templates for this specific project.
"""
            }
            
            for path, content in project_readme_contents.items():
                readme_path = self.project_config_dir / path
                readme_path.parent.mkdir(parents=True, exist_ok=True)
                readme_path.write_text(content)
        
        # Common logs and cache READMEs
        common_readme_contents = {
            "logs/README.md": """# Framework Logs

This directory contains Claude PM Framework operation logs.

## Log Types
- Framework operation logs
- Agent execution logs
- Error and debug logs
- Performance metrics

## Maintenance
Logs are automatically rotated and managed by the framework.
""",
            "cache/README.md": """# Framework Cache

This directory contains temporary cache and state files.

## Contents
- Temporary processing files
- State persistence
- Performance optimization cache
- Session data

## Note
This directory is managed automatically by the framework.
Contents may be cleared during framework updates.
"""
        }
        
        # Write common READMEs to all relevant directories
        for directory in [self.local_config_dir, self.project_config_dir]:
            if directory and directory.exists():
                for path, content in common_readme_contents.items():
                    readme_path = directory / path
                    readme_path.parent.mkdir(parents=True, exist_ok=True)
                    readme_path.write_text(content)
    
    def _create_agent_hierarchy_metadata(self):
        """Create agent hierarchy metadata files for three-tier system."""
        
        # Framework-level hierarchy metadata (global)
        if self.framework_config_dir:
            framework_hierarchy = {
                "hierarchy_version": "1.0",
                "tier": "framework",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agent_tiers": {
                    "system": {
                        "path": "./claude_pm/agents/",
                        "priority": 1,
                        "description": "Core framework agents with highest authority",
                        "immutable": True,
                        "examples": ["system_init_agent.py", "orchestrator_agent.py", "ops_agent.py"]
                    },
                    "user": {
                        "path": "./agents/user-defined/",
                        "priority": 2,
                        "description": "Global user-defined agents across all projects",
                        "immutable": False,
                        "examples": ["custom_engineer_agent.py", "personal_qa_agent.py"]
                    },
                    "project": {
                        "path": "PROJECT/.claude-multiagent-pm/agents/project-specific/",
                        "priority": 3,
                        "description": "Project-specific agents with highest precedence",
                        "immutable": False,
                        "examples": ["project_engineer_agent.py", "project_security_agent.py"]
                    }
                },
                "loading_rules": {
                    "precedence_order": ["project", "user", "system"],
                    "conflict_resolution": "highest_priority_wins",
                    "fallback_enabled": True,
                    "inheritance_enabled": True
                }
            }
            
            framework_hierarchy_path = self.framework_config_dir / "agents" / "hierarchy.yaml"
            framework_hierarchy_path.parent.mkdir(parents=True, exist_ok=True)
            with open(framework_hierarchy_path, 'w') as f:
                yaml.dump(framework_hierarchy, f, default_flow_style=False, indent=2)
        
        # Working directory hierarchy metadata
        working_hierarchy = {
            "hierarchy_version": "1.0",
            "tier": "working",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "working_directory": str(self.working_dir),
            "project_directory": str(self.project_dir),
            "framework_location": str(self.framework_path),
            "agent_discovery": {
                "auto_discovery": True,
                "scan_depth": 2,
                "file_patterns": ["*.py"],
                "exclude_patterns": ["__*", ".*", "test_*"]
            },
            "agent_loading": {
                "lazy_loading": True,
                "cache_agents": True,
                "reload_on_change": True,
                "validation_enabled": True
            },
            "hierarchy_paths": {
                "system_agents": str(self.framework_path / "claude_pm" / "agents") if self.framework_path else None,
                "user_agents": str(self.framework_config_dir / "agents" / "user-defined") if self.framework_config_dir else None,
                "project_agents": str(self.local_config_dir / "agents" / "project-specific")
            }
        }
        
        working_hierarchy_path = self.local_config_dir / "agents" / "hierarchy.yaml"
        working_hierarchy_path.parent.mkdir(parents=True, exist_ok=True)
        with open(working_hierarchy_path, 'w') as f:
            yaml.dump(working_hierarchy, f, default_flow_style=False, indent=2)
        
        # Project-specific hierarchy metadata (if different from working)
        if self.project_dir != self.working_dir and self.project_config_dir:
            project_hierarchy = {
                "hierarchy_version": "1.0",
                "tier": "project",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "project_directory": str(self.project_dir),
                "working_directory": str(self.working_dir),
                "framework_location": str(self.framework_path),
                "project_specific": {
                    "agent_overrides": True,
                    "inheritance_from_user": True,
                    "inheritance_from_system": True,
                    "custom_templates": True
                },
                "agent_types": {
                    "supported": ["engineer", "qa", "security", "ops", "architect", "performance"],
                    "custom_types": [],
                    "override_system": True,
                    "override_user": True
                },
                "hierarchy_paths": {
                    "system_agents": str(self.framework_path / "claude_pm" / "agents") if self.framework_path else None,
                    "user_agents": str(self.framework_config_dir / "agents" / "user-defined") if self.framework_config_dir else None,
                    "project_agents": str(self.project_config_dir / "agents" / "project-specific")
                }
            }
            
            project_hierarchy_path = self.project_config_dir / "agents" / "hierarchy.yaml"
            project_hierarchy_path.parent.mkdir(parents=True, exist_ok=True)
            with open(project_hierarchy_path, 'w') as f:
                yaml.dump(project_hierarchy, f, default_flow_style=False, indent=2)
        
        # Create agent registry file for tracking
        agent_registry = {
            "registry_version": "1.0",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_agents": 0,
            "agents_by_tier": {
                "system": {},
                "user": {},
                "project": {}
            },
            "agent_types": {},
            "health_status": {
                "last_check": None,
                "healthy_agents": 0,
                "unhealthy_agents": 0,
                "unloaded_agents": 0
            }
        }
        
        registry_path = self.local_config_dir / "agents" / "registry.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, 'w') as f:
            json.dump(agent_registry, f, indent=2)
    
    async def _generate_configuration_files(self) -> bool:
        """Generate configuration files for multi-project setup."""
        try:
            # Generate framework-level configuration (global)
            if self.framework_config_dir:
                framework_config = {
                    "claude-multiagent-pm": {
                        "version": "4.2.3",
                        "mode": "multi-project-orchestrator",
                        "framework_location": str(self.framework_path),
                        "initialized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "agent_id": "system-init-agent"
                    },
                    "global_agents": {
                        "user_defined_path": "./agents/user-defined",
                        "system_trained_path": "./agents/system-trained",
                        "auto_discover": True,
                        "load_on_startup": True
                    },
                    "templates": {
                        "global_templates_path": "./templates/global",
                        "inheritance_enabled": True
                    },
                    "dependencies": {
                        "mem0ai": {
                            "service_url": "http://localhost:8002",
                            "health_endpoint": "/health",
                            "required": True
                        },
                        "ai-trackdown-tools": {
                            "package": "@bobmatnyc/ai-trackdown-tools",
                            "command": "aitrackdown",
                            "required": True
                        },
                        "claude-pm-portfolio-manager": {
                            "package": "@bobmatnyc/claude-pm-portfolio-manager",
                            "required": False
                        }
                    }
                }
                
                framework_config_path = self.framework_config_dir / "config" / "framework.yaml"
                with open(framework_config_path, 'w') as f:
                    yaml.dump(framework_config, f, default_flow_style=False, indent=2)
            
            # Generate working directory configuration
            working_config = {
                "claude-multiagent-pm": {
                    "version": "4.2.3",
                    "mode": "working-directory",
                    "working_directory": str(self.working_dir),
                    "project_directory": str(self.project_dir),
                    "framework_location": str(self.framework_path),
                    "initialized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "is_project_specific": self.project_dir != self.working_dir
                },
                "session": {
                    "session_id": f"working-{int(time.time())}",
                    "session_path": "./sessions",
                    "auto_save": True
                },
                "logging": {
                    "level": "INFO",
                    "log_dir": "./logs/working",
                    "rotate_logs": True,
                    "max_log_size": "10MB"
                }
            }
            
            working_config_path = self.local_config_dir / "config" / "working.yaml"
            with open(working_config_path, 'w') as f:
                yaml.dump(working_config, f, default_flow_style=False, indent=2)
            
            # Generate project-specific configuration (if different from working)
            if self.project_dir != self.working_dir and self.project_config_dir:
                project_config = {
                    "claude-multiagent-pm": {
                        "version": "4.2.3",
                        "mode": "project-specific",
                        "project_directory": str(self.project_dir),
                        "working_directory": str(self.working_dir),
                        "framework_location": str(self.framework_path),
                        "initialized_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "project_agents": {
                        "enabled": True,
                        "load_path": "./agents/project-specific",
                        "auto_discover": True,
                        "override_global": True,
                        "naming_convention": "snake_case"
                    },
                    "templates": {
                        "project_templates_path": "./templates/project",
                        "inherit_global": True,
                        "override_global": True
                    },
                    "coordination": {
                        "multi_agent_enabled": True,
                        "parallel_execution": True,
                        "coordination_timeout": 300,
                        "project_scope": True
                    },
                    "logging": {
                        "level": "INFO",
                        "log_dir": "./logs/project",
                        "rotate_logs": True,
                        "max_log_size": "10MB",
                        "project_specific": True
                    }
                }
                
                project_config_path = self.project_config_dir / "config" / "project.yaml"
                with open(project_config_path, 'w') as f:
                    yaml.dump(project_config, f, default_flow_style=False, indent=2)
            
            # Generate consolidated agents configuration with three-tier hierarchy
            agents_config = {
                "agent_hierarchy": {
                    "system_agents": {
                        "path": str(self.framework_path / "claude_pm" / "agents") if self.framework_path else None,
                        "priority": 1,
                        "immutable": True,
                        "description": "Core framework agents with highest authority"
                    },
                    "user_agents": {
                        "path": str(self.framework_config_dir / "agents" / "user-defined") if self.framework_config_dir else None,
                        "priority": 2,
                        "immutable": False,
                        "description": "Global user-defined agents across all projects"
                    },
                    "project_agents": {
                        "path": str(self.local_config_dir / "agents" / "project-specific"),
                        "priority": 3,
                        "immutable": False,
                        "description": "Project-specific agents with highest precedence"
                    }
                },
                "agent_loading": {
                    "auto_discover": True,
                    "precedence_order": ["project_agents", "user_agents", "system_agents"],
                    "conflict_resolution": "highest_priority_wins",
                    "fallback_enabled": True,
                    "lazy_loading": True,
                    "cache_agents": True,
                    "reload_on_change": True,
                    "validation_enabled": True
                },
                "agent_types": {
                    "engineer": {
                        "system": "system_engineer_agent.py",
                        "user": "custom_engineer_agent.py",
                        "project": "project_engineer_agent.py"
                    },
                    "ops": {
                        "system": "ops_agent.py",
                        "user": "personal_ops_agent.py",
                        "project": "project_ops_agent.py"
                    },
                    "qa": {
                        "system": "qa_agent.py",
                        "user": "custom_qa_agent.py",
                        "project": "project_qa_agent.py"
                    },
                    "security": {
                        "system": "security_agent.py",
                        "user": "personal_security_agent.py",
                        "project": "project_security_agent.py"
                    },
                    "architect": {
                        "system": "architect_agent.py",
                        "user": "custom_architect_agent.py",
                        "project": "project_architect_agent.py"
                    },
                    "orchestrator": {
                        "system": "orchestrator_agent.py",
                        "user": "custom_orchestrator_agent.py",
                        "project": "project_orchestrator_agent.py"
                    }
                },
                "templates": {
                    "template_hierarchy": ["project", "user", "system"],
                    "template_inheritance": True,
                    "template_override": True,
                    "custom_templates_enabled": True
                },
                "coordination": {
                    "multi_agent_enabled": True,
                    "parallel_execution": True,
                    "coordination_timeout": 300,
                    "cross_project_coordination": True,
                    "hierarchical_coordination": True
                },
                "health_monitoring": {
                    "enabled": True,
                    "check_interval": 60,
                    "auto_reload_on_failure": True,
                    "health_logging": True
                }
            }
            
            agents_config_path = self.local_config_dir / "config" / "agents.yaml"
            with open(agents_config_path, 'w') as f:
                yaml.dump(agents_config, f, default_flow_style=False, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to generate configuration files: {e}")
            return False
    
    async def _verify_dependencies(self) -> Dict[str, Dict[str, str]]:
        """Verify all framework dependencies."""
        dependencies = {
            "mem0ai": await self._check_mem0ai_service(),
            "ai_trackdown_tools": await self._check_ai_trackdown_tools(),
            "claude_pm_portfolio_manager": await self._check_claude_pm_portfolio_manager(),
            "framework_core": await self._check_framework_core(),
            "python_environment": await self._check_python_environment(),
            "node_environment": await self._check_node_environment()
        }
        
        # Save dependency status (only if directory exists)
        if self.local_config_dir.exists():
            dependencies_config = {
                "last_checked": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": dependencies,
                "checked_by": "system-init-agent"
            }
            
            dependencies_config_path = self.local_config_dir / "config" / "dependencies.yaml"
            dependencies_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dependencies_config_path, 'w') as f:
                yaml.dump(dependencies_config, f, default_flow_style=False, indent=2)
        
        return dependencies
    
    async def _check_mem0ai_service(self) -> Dict[str, str]:
        """Check mem0AI service availability."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8002/health", timeout=5) as response:
                    if response.status == 200:
                        return {"status": "✅ ONLINE", "version": "active", "details": "Service responding"}
                    else:
                        return {"status": "⚠️ DEGRADED", "version": "unknown", "details": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "❌ OFFLINE", "version": "unknown", "details": str(e)}
    
    async def _check_ai_trackdown_tools(self) -> Dict[str, str]:
        """Check ai-trackdown-tools package with enhanced detection."""
        try:
            # Enhanced CLI detection
            availability = self.check_aitrackdown_availability(self.working_dir)
            
            if availability["available"]:
                return {
                    "status": "✅ INSTALLED", 
                    "version": availability["version"], 
                    "details": f"CLI available ({'local' if availability['local_cli'] else 'global'})"
                }
            else:
                return {"status": "❌ MISSING", "version": "none", "details": "CLI not available"}
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}
    
    async def _check_claude_pm_portfolio_manager(self) -> Dict[str, str]:
        """Check claude-pm-portfolio-manager package."""
        try:
            result = subprocess.run(
                ["npm", "list", "-g", "@bobmatnyc/claude-pm-portfolio-manager"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                version_line = [line for line in result.stdout.split('\n') if '@bobmatnyc/claude-pm-portfolio-manager' in line]
                version = version_line[0].split('@')[-1] if version_line else "unknown"
                return {"status": "✅ INSTALLED", "version": version, "details": "NPM package available"}
            else:
                return {"status": "❌ MISSING", "version": "none", "details": "NPM package not found"}
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}
    
    async def _check_framework_core(self) -> Dict[str, str]:
        """Check framework core installation."""
        try:
            if self.framework_path and (self.framework_path / "claude_pm" / "__init__.py").exists():
                version_file = self.framework_path / "VERSION"
                version = version_file.read_text().strip() if version_file.exists() else "unknown"
                return {"status": "✅ INSTALLED", "version": version, "details": f"Framework at {self.framework_path}"}
            else:
                return {"status": "❌ MISSING", "version": "none", "details": "Framework not found"}
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}
    
    async def _check_python_environment(self) -> Dict[str, str]:
        """Check Python environment and required packages."""
        try:
            required_packages = ["rich", "pydantic", "aiohttp", "yaml", "asyncio"]
            missing_packages = []
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if not missing_packages:
                return {"status": "✅ READY", "version": f"Python {sys.version.split()[0]}", "details": "All required packages available"}
            else:
                return {"status": "⚠️ PARTIAL", "version": f"Python {sys.version.split()[0]}", "details": f"Missing: {', '.join(missing_packages)}"}
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}
    
    async def _check_node_environment(self) -> Dict[str, str]:
        """Check Node.js environment."""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                return {"status": "✅ READY", "version": version, "details": "Node.js available"}
            else:
                return {"status": "❌ MISSING", "version": "none", "details": "Node.js not found"}
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}
    
    def _get_final_setup_status(self, dependencies: Dict[str, Dict[str, str]]) -> str:
        """Get overall setup status based on dependencies."""
        all_ready = all(dep["status"].startswith("✅") for dep in dependencies.values())
        some_ready = any(dep["status"].startswith("✅") for dep in dependencies.values())
        
        if all_ready:
            return "✅ READY"
        elif some_ready:
            return "⚠️ PARTIAL"
        else:
            return "❌ NEEDS_SETUP"
    
    async def display_initialization_report(self, results: Dict[str, Any]):
        """Display comprehensive initialization report."""
        self.console.print("\n" + "="*60)
        self.console.print("🤖 [bold blue]System Init Agent - Multi-Project Orchestrator Report[/bold blue]")
        self.console.print("="*60)
        
        # Basic info
        self.console.print(f"📍 Working Directory: {results['working_directory']}")
        self.console.print(f"📂 Framework Location: {results['framework_location']}")
        self.console.print(f"🎯 Project Directory: {self.project_dir}")
        self.console.print(f"🏗️  Multi-Project Mode: {'Yes' if self.project_dir != self.working_dir else 'No'}")
        self.console.print(f"🎯 Setup Status: [{results['setup_status']}]")
        
        # Directory structure overview
        self.console.print(f"\n🏢 [bold]Directory Structure:[/bold]")
        self.console.print(f"   • Framework Config: {self.framework_config_dir}")
        self.console.print(f"   • Working Config: {self.local_config_dir}")
        if self.project_dir != self.working_dir:
            self.console.print(f"   • Project Config: {self.project_config_dir}")
        
        # Agent hierarchy
        self.console.print(f"\n🤖 [bold]Agent Hierarchy:[/bold]")
        self.console.print(f"   • Global Agents: {self.framework_config_dir / 'agents' / 'user-defined' if self.framework_config_dir else 'Not configured'}")
        self.console.print(f"   • System Training: {self.framework_config_dir / 'agents' / 'system-trained' if self.framework_config_dir else 'Not configured'}")
        if self.project_dir != self.working_dir:
            self.console.print(f"   • Project Agents: {self.project_config_dir / 'agents' / 'project-specific'}")
        
        # Steps completed
        if results['steps_completed']:
            self.console.print(f"\n✅ [bold green]Completed Steps:[/bold green]")
            for step in results['steps_completed']:
                self.console.print(f"   • {step.replace('_', ' ').title()}")
        
        # Dependencies table
        if 'dependencies' in results:
            self.console.print(f"\n🔧 [bold]Dependencies Status:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Component", style="dim")
            table.add_column("Status", justify="center")
            table.add_column("Version", justify="center")
            table.add_column("Details", style="dim")
            
            for name, info in results['dependencies'].items():
                display_name = name.replace("_", " ").title()
                table.add_row(display_name, info['status'], info['version'], info['details'])
            
            self.console.print(table)
        
        # Errors
        if results['errors']:
            self.console.print(f"\n❌ [bold red]Errors:[/bold red]")
            for error in results['errors']:
                self.console.print(f"   • {error}")
        
        # Success/failure summary
        if results['success']:
            self.console.print(f"\n✅ [bold green]Framework initialization completed successfully![/bold green]")
        else:
            self.console.print(f"\n❌ [bold red]Framework initialization failed![/bold red]")
        
        self.console.print("="*60)
    
    async def troubleshoot_setup_issues(self) -> Dict[str, Any]:
        """Troubleshoot common setup issues and provide solutions."""
        issues = []
        solutions = []
        
        # Check if framework path exists
        if not self.framework_path:
            issues.append("Claude PM Framework not found")
            solutions.append("Install framework: git clone https://github.com/bobmatnyc/claude-multiagent-pm.git ~/Projects/claude-multiagent-pm")
        
        # Check dependencies
        dependencies = await self._verify_dependencies()
        
        for name, info in dependencies.items():
            if info['status'].startswith("❌"):
                issues.append(f"{name.replace('_', ' ').title()} not available")
                
                if name == "mem0ai":
                    solutions.append("Start mem0AI service: Follow the mem0AI installation guide")
                elif name == "ai_trackdown_tools":
                    solutions.append("Install ai-trackdown-tools: npm install -g @bobmatnyc/ai-trackdown-tools")
                elif name == "claude_pm_portfolio_manager":
                    solutions.append("Install portfolio manager: npm install -g @bobmatnyc/claude-pm-portfolio-manager")
                elif name == "node_environment":
                    solutions.append("Install Node.js: https://nodejs.org/en/download/")
        
        return {
            "issues": issues,
            "solutions": solutions,
            "dependencies": dependencies
        }
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive diagnostics for the framework setup."""
        diagnostics = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "working_directory": str(self.working_dir),
            "framework_path": str(self.framework_path),
            "local_config_exists": self.local_config_dir.exists(),
            "dependencies": await self._verify_dependencies(),
            "troubleshooting": await self.troubleshoot_setup_issues(),
            "recommendations": []
        }
        
        # Generate recommendations
        if not diagnostics["local_config_exists"]:
            diagnostics["recommendations"].append("Run initialization: python ~/.claude/commands/cmpm-bridge.py init --setup")
        
        # Check for critical issues
        critical_deps = ["framework_core", "python_environment"]
        for dep in critical_deps:
            if dep in diagnostics["dependencies"] and diagnostics["dependencies"][dep]["status"].startswith("❌"):
                diagnostics["recommendations"].append(f"Critical: Fix {dep.replace('_', ' ').title()} installation")
        
        return diagnostics

    # NEW: Enhanced CMCP-init methods with project indexing
    
    async def initialize_framework_with_indexing(self, force: bool = False) -> Dict[str, Any]:
        """
        Enhanced framework initialization with comprehensive project indexing.
        
        Args:
            force: Force reinitialize even if already set up
            
        Returns:
            Dict containing initialization results and project index status
        """
        self.logger.info(f"Starting enhanced framework initialization with indexing in {self.working_dir}")
        
        results = {
            "success": False,
            "working_directory": str(self.working_dir),
            "framework_location": str(self.framework_path),
            "steps_completed": [],
            "errors": [],
            "setup_status": "unknown",
            "project_index": None
        }
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                
                # Step 1: Check existing setup
                check_task = progress.add_task("Checking existing setup...", total=1)
                local_config_exists = self.local_config_dir.exists()
                
                if local_config_exists and not force:
                    progress.update(check_task, completed=1)
                    results["setup_status"] = "already_exists"
                    results["success"] = True
                    results["steps_completed"].append("check_existing")
                    
                    # Load existing project index
                    results["project_index"] = await self.get_project_index()
                    return results
                
                progress.update(check_task, completed=1)
                results["steps_completed"].append("check_existing")
                
                # Step 2: Create enhanced directory structure
                structure_task = progress.add_task("Creating enhanced directory structure...", total=1)
                if self._create_directory_structure():
                    progress.update(structure_task, completed=1)
                    results["steps_completed"].append("enhanced_directory_structure")
                else:
                    results["errors"].append("Failed to create enhanced directory structure")
                    return results
                
                # Step 3: Generate configuration files with index support
                config_task = progress.add_task("Generating configuration files...", total=1)
                if await self._generate_enhanced_configuration_files():
                    progress.update(config_task, completed=1)
                    results["steps_completed"].append("enhanced_configuration_files")
                else:
                    results["errors"].append("Failed to generate enhanced configuration files")
                    return results
                
                # Step 4: Initialize project index
                index_task = progress.add_task("Initializing project index...", total=1)
                if await self._initialize_project_index():
                    progress.update(index_task, completed=1)
                    results["steps_completed"].append("project_index_initialization")
                    results["project_index"] = await self.get_project_index()
                else:
                    results["errors"].append("Failed to initialize project index")
                    return results
                
                # Step 5: Verify dependencies
                deps_task = progress.add_task("Verifying dependencies...", total=1)
                dependency_status = await self._verify_dependencies()
                results["dependencies"] = dependency_status
                progress.update(deps_task, completed=1)
                results["steps_completed"].append("dependency_verification")
                
                # Step 6: Update project health status
                health_task = progress.add_task("Updating project health status...", total=1)
                await self._update_project_health_status()
                progress.update(health_task, completed=1)
                results["steps_completed"].append("project_health_update")
                
                # Step 7: Final setup status
                results["setup_status"] = self._get_final_setup_status(dependency_status)
                results["success"] = True
                
        except Exception as e:
            self.logger.error(f"Enhanced framework initialization failed: {e}")
            results["errors"].append(f"Enhanced initialization failed: {str(e)}")
            results["success"] = False
        
        return results
    
    async def _generate_enhanced_configuration_files(self) -> bool:
        """Generate enhanced configuration files with project indexing support."""
        try:
            # Generate base configuration files
            base_success = await self._generate_configuration_files()
            if not base_success:
                return False
            
            # Generate project indexing configuration with CLI support
            index_config = {
                "project_indexing": {
                    "enabled": True,
                    "auto_discovery": True,
                    "scan_depth": 3,
                    "update_interval": 300,
                    "health_check_interval": 600,
                    "cli_integration": {
                        "enabled": True,
                        "priority": "cli_first",
                        "fallback_to_basic": True,
                        "timeout": 10
                    }
                },
                "index_database": {
                    "projects_file": "./index/projects.json",
                    "dependencies_file": "./index/dependencies.json",
                    "cache_directory": "./index/cache",
                    "cli_cache": "./index/cache/cli_data.json"
                },
                "project_types": {
                    "claude-pm-framework": {
                        "indicators": ["claude_pm/__init__.py", "claude_pm/core/"],
                        "health_check": "framework_core_check",
                        "cli_commands": ["status", "epic list", "issue list"]
                    },
                    "managed": {
                        "indicators": [".claude-multiagent-pm/", "package.json"],
                        "health_check": "managed_project_check",
                        "cli_commands": ["status", "epic list", "issue list", "task list"]
                    },
                    "standalone": {
                        "indicators": [".git/", "pyproject.toml", "requirements.txt"],
                        "health_check": "standalone_project_check",
                        "cli_commands": ["status"]
                    }
                },
                "cli_integration": {
                    "ai_trackdown_tools": {
                        "enabled": True,
                        "commands": ["aitrackdown", "atd"],
                        "local_paths": ["./bin/aitrackdown", "./node_modules/.bin/aitrackdown"],
                        "config_detection": [".ai-trackdown/", "tasks/"],
                        "data_collection": {
                            "epics": "epic list --json",
                            "issues": "issue list --json",
                            "tasks": "task list --json",
                            "stats": "status --stats --json"
                        }
                    }
                }
            }
            
            index_config_path = self.local_config_dir / "config" / "index.yaml"
            with open(index_config_path, 'w') as f:
                yaml.dump(index_config, f, default_flow_style=False, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to generate enhanced configuration files: {e}")
            return False
    
    async def _initialize_project_index(self) -> bool:
        """Initialize the project index database."""
        try:
            # Create initial projects.json
            projects_data = {
                "version": "4.3.0",
                "lastUpdated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "currentProject": str(self.working_dir),
                "projects": {}
            }
            
            # Scan current directory for project information
            current_project = await self._scan_current_project()
            if current_project:
                project_id = f"project-{int(time.time())}"
                projects_data["projects"][project_id] = current_project
            
            # Save projects index
            projects_file = self.local_config_dir / "index" / "projects.json"
            with open(projects_file, 'w') as f:
                json.dump(projects_data, f, indent=2)
            
            # Create dependencies index
            dependencies_data = {
                "version": "4.3.0",
                "lastUpdated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dependencies": await self._verify_dependencies()
            }
            
            dependencies_file = self.local_config_dir / "index" / "dependencies.json"
            with open(dependencies_file, 'w') as f:
                json.dump(dependencies_data, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize project index: {e}")
            return False
    
    async def _scan_current_project(self) -> Optional[Dict[str, Any]]:
        """Scan current directory to determine project type and metadata with CLI integration."""
        try:
            # Use CLI integration to collect comprehensive project data
            cli_project_data = await self.collect_project_data_via_cli(self.working_dir)
            
            # Build enhanced project info
            project_info = {
                "name": self.working_dir.name,
                "path": str(self.working_dir),
                "type": "standalone",
                "lastAccess": time.strftime("%Y-%m-%d %H:%M:%S"),
                "health": "unknown",
                "dependencies": {}
            }
            
            # Detect project type
            if (self.working_dir / "claude_pm" / "__init__.py").exists():
                project_info["type"] = "claude-pm-framework"
                project_info["name"] = "Claude PM Framework"
            elif (self.working_dir / ".claude-multiagent-pm").exists():
                project_info["type"] = "managed"
            elif (self.working_dir / ".git").exists():
                project_info["type"] = "standalone"
            
            # Check for common dependencies
            if (self.working_dir / "package.json").exists():
                project_info["dependencies"]["node"] = "detected"
            if (self.working_dir / "requirements.txt").exists():
                project_info["dependencies"]["python"] = "detected"
            if (self.working_dir / "pyproject.toml").exists():
                project_info["dependencies"]["python"] = "detected"
            
            # Enhanced data from CLI integration
            if cli_project_data:
                # Merge CLI data into project info
                project_info.update(cli_project_data)
                
                # Set health based on CLI availability and data
                if cli_project_data.get("aiTrackdownTools", {}).get("available"):
                    project_info["health"] = "operational"
                else:
                    project_info["health"] = "operational"  # Still operational, just without CLI features
            
            return project_info
        except Exception as e:
            self.logger.error(f"Failed to scan current project: {e}")
            return None
    
    async def get_project_index(self) -> Optional[Dict[str, Any]]:
        """Get the current project index data."""
        try:
            projects_file = self.local_config_dir / "index" / "projects.json"
            if projects_file.exists():
                with open(projects_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get project index: {e}")
            return None
    
    async def rebuild_project_index(self) -> bool:
        """Rebuild the project index from scratch."""
        try:
            # Remove existing index files
            index_dir = self.local_config_dir / "index"
            if index_dir.exists():
                import shutil
                shutil.rmtree(index_dir)
            
            # Recreate index directory
            index_dir.mkdir(parents=True, exist_ok=True)
            (index_dir / "cache").mkdir(parents=True, exist_ok=True)
            
            # Initialize new index
            return await self._initialize_project_index()
        except Exception as e:
            self.logger.error(f"Failed to rebuild project index: {e}")
            return False
    
    async def _update_project_health_status(self) -> bool:
        """Update the health status of the current project."""
        try:
            projects_data = await self.get_project_index()
            if not projects_data:
                return False
            
            # Update health status for current project
            current_project_path = str(self.working_dir)
            for project_id, project_info in projects_data["projects"].items():
                if project_info["path"] == current_project_path:
                    # Run health checks based on project type
                    if project_info["type"] == "claude-pm-framework":
                        project_info["health"] = "operational" if self.framework_path else "issues"
                    elif project_info["type"] == "managed":
                        project_info["health"] = "operational" if self.local_config_dir.exists() else "issues"
                    else:
                        project_info["health"] = "operational"
                    
                    project_info["lastAccess"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    break
            
            # Save updated index
            projects_file = self.local_config_dir / "index" / "projects.json"
            with open(projects_file, 'w') as f:
                json.dump(projects_data, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to update project health status: {e}")
            return False
    
    async def display_enhanced_initialization_report(self, results: Dict[str, Any]):
        """Display comprehensive enhanced initialization report."""
        self.console.print("\n" + "="*70)
        self.console.print("🚀 [bold blue]CMCP-init Enhanced Initialization Report[/bold blue]")
        self.console.print("="*70)
        
        # Basic info
        self.console.print(f"📍 Working Directory: {results['working_directory']}")
        self.console.print(f"📂 Framework Location: {results['framework_location']}")
        self.console.print(f"🎯 Project Directory: {self.project_dir}")
        self.console.print(f"🏗️  Multi-Project Mode: {'Yes' if self.project_dir != self.working_dir else 'No'}")
        self.console.print(f"🎯 Setup Status: [{results['setup_status']}]")
        
        # Enhanced directory structure overview
        self.console.print(f"\n🏢 [bold]Enhanced Directory Structure:[/bold]")
        self.console.print(f"   • Framework Config: {self.framework_config_dir}")
        self.console.print(f"   • Working Config: {self.local_config_dir}")
        self.console.print(f"   • Project Index: {self.local_config_dir / 'index'}")
        self.console.print(f"   • Index Cache: {self.local_config_dir / 'index' / 'cache'}")
        if self.project_dir != self.working_dir:
            self.console.print(f"   • Project Config: {self.project_config_dir}")
        
        # Project index information
        if results.get("project_index"):
            index_data = results["project_index"]
            self.console.print(f"\n📊 [bold]Project Index:[/bold]")
            self.console.print(f"   • Version: {index_data.get('version', 'Unknown')}")
            self.console.print(f"   • Last Updated: {index_data.get('lastUpdated', 'Unknown')}")
            self.console.print(f"   • Current Project: {index_data.get('currentProject', 'Unknown')}")
            self.console.print(f"   • Projects Indexed: {len(index_data.get('projects', {}))}")
        
        # Enhanced agent hierarchy
        self.console.print(f"\n🤖 [bold]Enhanced Agent Hierarchy:[/bold]")
        self.console.print(f"   • Global Agents: {self.framework_config_dir / 'agents' / 'user-defined' if self.framework_config_dir else 'Not configured'}")
        self.console.print(f"   • System Training: {self.framework_config_dir / 'agents' / 'system-trained' if self.framework_config_dir else 'Not configured'}")
        self.console.print(f"   • Project Agents: {self.local_config_dir / 'agents' / 'project-specific'}")
        if self.project_dir != self.working_dir:
            self.console.print(f"   • Project-Specific: {self.project_config_dir / 'agents' / 'project-specific'}")
        
        # Steps completed
        if results['steps_completed']:
            self.console.print(f"\n✅ [bold green]Enhanced Steps Completed:[/bold green]")
            for step in results['steps_completed']:
                self.console.print(f"   • {step.replace('_', ' ').title()}")
        
        # Dependencies table
        if 'dependencies' in results:
            self.console.print(f"\n🔧 [bold]Dependencies Status:[/bold]")
            from rich.table import Table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Component", style="dim")
            table.add_column("Status", justify="center")
            table.add_column("Version", justify="center")
            table.add_column("Details", style="dim")
            
            for name, info in results['dependencies'].items():
                display_name = name.replace("_", " ").title()
                table.add_row(display_name, info['status'], info['version'], info['details'])
            
            self.console.print(table)
        
        # Errors
        if results['errors']:
            self.console.print(f"\n❌ [bold red]Errors:[/bold red]")
            for error in results['errors']:
                self.console.print(f"   • {error}")
        
        # Success/failure summary
        if results['success']:
            self.console.print(f"\n✅ [bold green]Enhanced CMCP-init completed successfully![/bold green]")
            self.console.print(f"🎯 [bold]Next Steps:[/bold]")
            self.console.print(f"   • Use 'cmcp-init --show-index' to view project index")
            self.console.print(f"   • Use 'cmcp-init --verify' to run enhanced diagnostics")
            self.console.print(f"   • Use 'cmcp-init --reindex' to rebuild project index")
        else:
            self.console.print(f"\n❌ [bold red]Enhanced CMCP-init failed![/bold red]")
        
        self.console.print("="*70)
    
    # Cross-Directory Functionality Methods
    
    async def switch_project_directory(self, new_path: Path) -> Dict[str, Any]:
        """
        Switch to a different project directory and update index.
        
        Args:
            new_path: New project directory path
            
        Returns:
            Dict with switch results and updated project data
        """
        try:
            old_path = self.working_dir
            self.working_dir = new_path
            self.project_dir = self._detect_project_directory()
            self.local_config_dir = self.working_dir / ".claude-multiagent-pm"
            self.project_config_dir = self.project_dir / ".claude-multiagent-pm"
            
            # Update project index for new location
            await self._update_project_index_for_directory(new_path)
            
            # Collect project data for new directory
            project_data = await self.collect_project_data_via_cli(new_path)
            
            return {
                "success": True,
                "old_directory": str(old_path),
                "new_directory": str(new_path),
                "project_data": project_data,
                "index_updated": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to switch project directory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_project_index_for_directory(self, directory: Path) -> bool:
        """Update project index to include new directory."""
        try:
            # Get or create project index
            projects_data = await self.get_project_index()
            if not projects_data:
                projects_data = {
                    "version": "4.3.0",
                    "lastUpdated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "currentProject": str(directory),
                    "projects": {}
                }
            
            # Update current project
            projects_data["currentProject"] = str(directory)
            projects_data["lastUpdated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Scan new directory
            project_data = await self.collect_project_data_via_cli(directory)
            if project_data:
                project_id = f"project-{directory.name}-{int(time.time())}"
                projects_data["projects"][project_id] = {
                    "name": directory.name,
                    "path": str(directory),
                    "type": self._detect_project_type(directory),
                    "lastAccess": time.strftime("%Y-%m-%d %H:%M:%S"),
                    **project_data
                }
            
            # Save updated index
            projects_file = self.local_config_dir / "index" / "projects.json"
            projects_file.parent.mkdir(parents=True, exist_ok=True)
            with open(projects_file, 'w') as f:
                json.dump(projects_data, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update project index for directory: {e}")
            return False
    
    def _detect_project_type(self, directory: Path) -> str:
        """Detect project type from directory contents."""
        if (directory / "claude_pm" / "__init__.py").exists():
            return "claude-pm-framework"
        elif (directory / ".claude-multiagent-pm").exists():
            return "managed"
        elif (directory / ".git").exists():
            return "standalone"
        else:
            return "unknown"
    
    async def display_multi_project_status(self) -> None:
        """Display status across multiple projects in index."""
        try:
            projects_data = await self.get_project_index()
            if not projects_data:
                self.console.print("❌ No project index found. Run cmcp-init --setup first.")
                return
            
            self.console.print("\n" + "="*70)
            self.console.print("📊 [bold blue]Multi-Project Status Dashboard[/bold blue]")
            self.console.print("="*70)
            
            # Current project info
            current_project = projects_data.get("currentProject", "Unknown")
            self.console.print(f"📍 Current Project: {current_project}")
            self.console.print(f"🔄 Last Updated: {projects_data.get('lastUpdated', 'Unknown')}")
            
            # Projects table
            if projects_data.get("projects"):
                self.console.print(f"\n📂 [bold]Indexed Projects:[/bold]")
                
                from rich.table import Table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Project", style="dim")
                table.add_column("Type", justify="center")
                table.add_column("CLI Status", justify="center")
                table.add_column("Health", justify="center")
                table.add_column("Last Access", style="dim")
                
                for project_id, project_info in projects_data["projects"].items():
                    cli_status = "✅" if project_info.get("aiTrackdownTools", {}).get("available") else "❌"
                    health = project_info.get("health", "unknown")
                    health_icon = "✅" if health == "operational" else "⚠️"
                    
                    table.add_row(
                        project_info.get("name", "Unknown"),
                        project_info.get("type", "unknown"),
                        cli_status,
                        health_icon,
                        project_info.get("lastAccess", "Unknown")
                    )
                
                self.console.print(table)
                
                # CLI availability summary
                total_projects = len(projects_data["projects"])
                cli_available = sum(1 for p in projects_data["projects"].values() 
                                  if p.get("aiTrackdownTools", {}).get("available"))
                
                self.console.print(f"\n📈 [bold]CLI Integration Summary:[/bold]")
                self.console.print(f"   • Total Projects: {total_projects}")
                self.console.print(f"   • With CLI: {cli_available}")
                self.console.print(f"   • Without CLI: {total_projects - cli_available}")
                
            else:
                self.console.print("\n❌ No projects indexed yet.")
            
            self.console.print("="*70)
            
        except Exception as e:
            self.logger.error(f"Failed to display multi-project status: {e}")
            self.console.print(f"❌ Error displaying multi-project status: {e}")
    
    async def display_rich_project_information(self, project_path: Optional[Path] = None) -> None:
        """Display rich project information with CLI data when available."""
        try:
            target_path = project_path or self.working_dir
            project_data = await self.collect_project_data_via_cli(target_path)
            
            self.console.print("\n" + "="*70)
            self.console.print("🔍 [bold blue]Rich Project Information[/bold blue]")
            self.console.print("="*70)
            
            # Basic project info
            self.console.print(f"📍 Project Path: {target_path}")
            self.console.print(f"📂 Project Name: {target_path.name}")
            self.console.print(f"🎯 Project Type: {self._detect_project_type(target_path)}")
            
            # CLI integration status
            ai_trackdown_info = project_data.get("aiTrackdownTools", {})
            if ai_trackdown_info.get("available"):
                self.console.print(f"✅ [bold green]AI-Trackdown-Tools: Available[/bold green]")
                self.console.print(f"   • Version: {ai_trackdown_info.get('version', 'Unknown')}")
                self.console.print(f"   • CLI Type: {'Local' if ai_trackdown_info.get('localCli') else 'Global'}")
                self.console.print(f"   • Config Path: {ai_trackdown_info.get('configPath', 'Unknown')}")
                
                # Rich project data
                project_info = project_data.get("projectData", {})
                if project_info:
                    self.console.print(f"\n📊 [bold]Project Data:[/bold]")
                    
                    # Epics
                    epics = project_info.get("epics", {})
                    if epics and not epics.get("error"):
                        self.console.print(f"   • Epics: {epics.get('total', 0)} total, {epics.get('active', 0)} active")
                    
                    # Issues
                    issues = project_info.get("issues", {})
                    if issues and not issues.get("error"):
                        self.console.print(f"   • Issues: {issues.get('total', 0)} total, {issues.get('high', 0)} high priority")
                    
                    # Tasks
                    tasks = project_info.get("tasks", {})
                    if tasks and not tasks.get("error"):
                        self.console.print(f"   • Tasks: {tasks.get('total', 0)} total, {tasks.get('active', 0)} active")
                
                # Statistics
                stats = project_data.get("statistics", {})
                if stats and not stats.get("error"):
                    self.console.print(f"\n📈 [bold]Statistics:[/bold]")
                    self.console.print(f"   • Completion Rate: {stats.get('completionRate', 'Unknown')}")
                    self.console.print(f"   • Last Activity: {stats.get('lastActivity', 'Unknown')}")
                    self.console.print(f"   • Velocity: {stats.get('velocity', 'Unknown')}")
                    
            else:
                self.console.print(f"❌ [bold red]AI-Trackdown-Tools: Not Available[/bold red]")
                note = ai_trackdown_info.get("note", "Install ai-trackdown-tools for rich project features")
                self.console.print(f"   • Note: {note}")
                
                # Basic project statistics
                stats = project_data.get("statistics", {})
                if stats:
                    self.console.print(f"\n📊 [bold]Basic Statistics:[/bold]")
                    self.console.print(f"   • File Count: {stats.get('fileCount', 'Unknown')}")
                    self.console.print(f"   • Has Git: {stats.get('hasGit', False)}")
                    self.console.print(f"   • Has package.json: {stats.get('hasPackageJson', False)}")
                    self.console.print(f"   • Has pyproject.toml: {stats.get('hasPyproject', False)}")
            
            self.console.print("="*70)
            
        except Exception as e:
            self.logger.error(f"Failed to display rich project information: {e}")
            self.console.print(f"❌ Error displaying project information: {e}")
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run enhanced diagnostics with project index information."""
        diagnostics = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "working_directory": str(self.working_dir),
            "framework_path": str(self.framework_path),
            "local_config_exists": self.local_config_dir.exists(),
            "dependencies": await self._verify_dependencies(),
            "troubleshooting": await self.troubleshoot_setup_issues(),
            "recommendations": [],
            "index_status": await self._get_index_status()
        }
        
        # Generate recommendations
        if not diagnostics["local_config_exists"]:
            diagnostics["recommendations"].append("Run enhanced initialization: python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup")
        
        # Check for critical issues
        critical_deps = ["framework_core", "python_environment"]
        for dep in critical_deps:
            if dep in diagnostics["dependencies"] and diagnostics["dependencies"][dep]["status"].startswith("❌"):
                diagnostics["recommendations"].append(f"Critical: Fix {dep.replace('_', ' ').title()} installation")
        
        # Index-specific recommendations
        if not diagnostics["index_status"]["exists"]:
            diagnostics["recommendations"].append("Initialize project index: python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup")
        elif diagnostics["index_status"]["project_count"] == 0:
            diagnostics["recommendations"].append("Rebuild project index: python ~/.claude/commands/cmpm-bridge.py cmcp-init --reindex")
        
        return diagnostics
    
    async def _get_index_status(self) -> Dict[str, Any]:
        """Get current project index status."""
        try:
            projects_file = self.local_config_dir / "index" / "projects.json"
            if projects_file.exists():
                with open(projects_file, 'r') as f:
                    index_data = json.load(f)
                    return {
                        "exists": True,
                        "project_count": len(index_data.get("projects", {})),
                        "last_updated": index_data.get("lastUpdated", "Unknown"),
                        "version": index_data.get("version", "Unknown")
                    }
            else:
                return {
                    "exists": False,
                    "project_count": 0,
                    "last_updated": "Never",
                    "version": "Unknown"
                }
        except Exception as e:
            self.logger.error(f"Failed to get index status: {e}")
            return {
                "exists": False,
                "project_count": 0,
                "last_updated": "Error",
                "version": "Unknown"
            }
    
    # AI-Trackdown-Tools CLI Integration Methods
    
    def check_aitrackdown_availability(self, project_path: Path) -> Dict[str, Any]:
        """
        Check if ai-trackdown-tools is available in project directory.
        
        Args:
            project_path: Path to check for CLI availability
            
        Returns:
            Dict with availability status, version, and CLI type
        """
        try:
            # Check for local CLI wrappers first
            local_cli_paths = [
                project_path / "bin" / "aitrackdown",
                project_path / "bin" / "atd",
                project_path / "node_modules" / ".bin" / "aitrackdown",
                project_path / "node_modules" / ".bin" / "atd"
            ]
            
            for cli_path in local_cli_paths:
                if cli_path.exists() and cli_path.is_file():
                    # Check if it's executable
                    if os.access(cli_path, os.X_OK):
                        version = self._get_cli_version(str(cli_path))
                        return {
                            "available": True,
                            "version": version,
                            "local_cli": True,
                            "cli_path": str(cli_path),
                            "config_path": str(project_path / ".ai-trackdown")
                        }
            
            # Check for global installation
            global_commands = ["aitrackdown", "atd"]
            for cmd in global_commands:
                try:
                    result = subprocess.run(
                        [cmd, "--version"],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        return {
                            "available": True,
                            "version": version,
                            "local_cli": False,
                            "cli_path": cmd,
                            "config_path": str(project_path / ".ai-trackdown")
                        }
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                    continue
            
            # Check for .ai-trackdown directory structure
            config_dir = project_path / ".ai-trackdown"
            if config_dir.exists():
                return {
                    "available": False,
                    "version": "config-only",
                    "local_cli": False,
                    "cli_path": None,
                    "config_path": str(config_dir),
                    "note": "Configuration exists but CLI not available"
                }
            
            return {
                "available": False,
                "version": "none",
                "local_cli": False,
                "cli_path": None,
                "config_path": None
            }
            
        except Exception as e:
            self.logger.error(f"Error checking ai-trackdown-tools availability: {e}")
            return {
                "available": False,
                "version": "error",
                "local_cli": False,
                "cli_path": None,
                "config_path": None,
                "error": str(e)
            }
    
    def _get_cli_version(self, cli_path: str) -> str:
        """Get version from CLI command."""
        try:
            result = subprocess.run(
                [cli_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "unknown"
        except Exception:
            return "unknown"
    
    async def collect_project_data_via_cli(self, project_path: Path) -> Dict[str, Any]:
        """
        Collect project data using ai-trackdown-tools CLI.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            Dict with project data or basic fallback data
        """
        availability = self.check_aitrackdown_availability(project_path)
        
        if not availability["available"]:
            return self.collect_basic_project_data(project_path)
        
        try:
            cli_path = availability["cli_path"]
            project_data = {
                "aiTrackdownTools": {
                    "available": True,
                    "version": availability["version"],
                    "localCli": availability["local_cli"],
                    "configPath": availability["config_path"]
                },
                "projectData": {},
                "statistics": {}
            }
            
            # Collect epic data
            try:
                epics_result = subprocess.run(
                    [cli_path, "epic", "list", "--json"],
                    capture_output=True, text=True, timeout=10,
                    cwd=str(project_path)
                )
                if epics_result.returncode == 0:
                    epics_data = json.loads(epics_result.stdout)
                    project_data["projectData"]["epics"] = self._process_epics_data(epics_data)
            except Exception as e:
                self.logger.warning(f"Failed to collect epic data: {e}")
                project_data["projectData"]["epics"] = {"error": str(e)}
            
            # Collect issue data
            try:
                issues_result = subprocess.run(
                    [cli_path, "issue", "list", "--json"],
                    capture_output=True, text=True, timeout=10,
                    cwd=str(project_path)
                )
                if issues_result.returncode == 0:
                    issues_data = json.loads(issues_result.stdout)
                    project_data["projectData"]["issues"] = self._process_issues_data(issues_data)
            except Exception as e:
                self.logger.warning(f"Failed to collect issue data: {e}")
                project_data["projectData"]["issues"] = {"error": str(e)}
            
            # Collect task data
            try:
                tasks_result = subprocess.run(
                    [cli_path, "task", "list", "--json"],
                    capture_output=True, text=True, timeout=10,
                    cwd=str(project_path)
                )
                if tasks_result.returncode == 0:
                    tasks_data = json.loads(tasks_result.stdout)
                    project_data["projectData"]["tasks"] = self._process_tasks_data(tasks_data)
            except Exception as e:
                self.logger.warning(f"Failed to collect task data: {e}")
                project_data["projectData"]["tasks"] = {"error": str(e)}
            
            # Collect project statistics
            try:
                stats_result = subprocess.run(
                    [cli_path, "status", "--stats", "--json"],
                    capture_output=True, text=True, timeout=10,
                    cwd=str(project_path)
                )
                if stats_result.returncode == 0:
                    stats_data = json.loads(stats_result.stdout)
                    project_data["statistics"] = self._process_stats_data(stats_data)
            except Exception as e:
                self.logger.warning(f"Failed to collect statistics: {e}")
                project_data["statistics"] = {"error": str(e)}
            
            return project_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect project data via CLI: {e}")
            return self.collect_basic_project_data(project_path)
    
    def collect_basic_project_data(self, project_path: Path) -> Dict[str, Any]:
        """
        Collect basic project data when ai-trackdown-tools is not available.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            Dict with basic project data
        """
        try:
            basic_data = {
                "aiTrackdownTools": {
                    "available": False,
                    "version": "none",
                    "localCli": False,
                    "configPath": None,
                    "note": "Limited indexing capabilities - install ai-trackdown-tools for full features"
                },
                "projectData": {
                    "type": "basic_scan",
                    "indicators": []
                },
                "statistics": {
                    "note": "Basic statistics only - install ai-trackdown-tools for detailed metrics"
                }
            }
            
            # Detect project type through file system scanning
            project_indicators = []
            
            # Check for common project files
            common_files = [
                (".git", "git repository"),
                ("package.json", "Node.js project"),
                ("pyproject.toml", "Python project (pyproject)"),
                ("requirements.txt", "Python project (requirements)"),
                ("Cargo.toml", "Rust project"),
                ("go.mod", "Go project"),
                ("pom.xml", "Java Maven project"),
                ("build.gradle", "Java Gradle project"),
                (".ai-trackdown", "AI Trackdown configuration")
            ]
            
            for file_name, description in common_files:
                if (project_path / file_name).exists():
                    project_indicators.append({
                        "file": file_name,
                        "description": description,
                        "exists": True
                    })
            
            basic_data["projectData"]["indicators"] = project_indicators
            
            # Basic project statistics
            basic_data["statistics"] = {
                "projectPath": str(project_path),
                "projectName": project_path.name,
                "lastScanned": time.strftime("%Y-%m-%d %H:%M:%S"),
                "fileCount": len(list(project_path.glob("**/*"))),
                "hasGit": (project_path / ".git").exists(),
                "hasPackageJson": (project_path / "package.json").exists(),
                "hasPyproject": (project_path / "pyproject.toml").exists()
            }
            
            return basic_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect basic project data: {e}")
            return {
                "aiTrackdownTools": {
                    "available": False,
                    "version": "error",
                    "localCli": False,
                    "configPath": None,
                    "error": str(e)
                },
                "projectData": {"error": str(e)},
                "statistics": {"error": str(e)}
            }
    
    def _process_epics_data(self, epics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process epic data from CLI response."""
        try:
            epics = epics_data.get("epics", [])
            return {
                "total": len(epics),
                "active": len([e for e in epics if e.get("status") == "active"]),
                "completed": len([e for e in epics if e.get("status") == "completed"]),
                "items": epics[:5]  # Store first 5 for display
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _process_issues_data(self, issues_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process issue data from CLI response."""
        try:
            issues = issues_data.get("issues", [])
            return {
                "total": len(issues),
                "high": len([i for i in issues if i.get("priority") == "high"]),
                "inProgress": len([i for i in issues if i.get("status") == "in-progress"]),
                "completed": len([i for i in issues if i.get("status") == "completed"]),
                "items": issues[:5]  # Store first 5 for display
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _process_tasks_data(self, tasks_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process task data from CLI response."""
        try:
            tasks = tasks_data.get("tasks", [])
            return {
                "total": len(tasks),
                "active": len([t for t in tasks if t.get("status") == "active"]),
                "completed": len([t for t in tasks if t.get("status") == "completed"]),
                "items": tasks[:5]  # Store first 5 for display
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _process_stats_data(self, stats_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process statistics data from CLI response."""
        try:
            return {
                "completionRate": stats_data.get("completionRate", "unknown"),
                "lastActivity": stats_data.get("lastActivity", "unknown"),
                "velocity": stats_data.get("velocity", "unknown"),
                "health": stats_data.get("health", "unknown")
            }
        except Exception as e:
            return {"error": str(e)}