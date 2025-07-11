#!/usr/bin/env python3
"""
{{AGENT_TYPE}} Agent Template - Project Tier
============================================

This is a template for creating project-level agents in the Claude PM Framework.
Project agents are local to a specific project and have the highest precedence.

Agent: {{AGENT_NAME}}
Type: {{AGENT_TYPE}}
Tier: {{AGENT_TIER}}
Created: {{TIMESTAMP}}

Project Agent Characteristics:
- Highest precedence in agent hierarchy
- Project-specific implementations
- Can override both user and system agents
- Local to specific project
- Context-aware functionality
- Project-tailored behavior
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ..core.base_service import BaseService
from ..core.config import Config
from ..core.logging_config import setup_logging


class {{CLASS_NAME}}(BaseService):
    """
    {{AGENT_TYPE}} Agent - Project Tier
    
    This is a project-level agent that provides project-specific {{AGENT_TYPE}} functionality.
    Project agents have the highest precedence and can override both user and system agents
    to provide tailored behavior for specific projects.
    
    Responsibilities:
    - Project-specific {{AGENT_TYPE}} implementations
    - Context-aware {{AGENT_TYPE}} operations
    - Project-tailored customizations
    - Override higher-tier agents when needed
    """
    
    def __init__(self, project_path: Path, config: Optional[Dict[str, Any]] = None):
        """Initialize the {{AGENT_TYPE}} project agent."""
        super().__init__(name="{{AGENT_NAME}}", config=config)
        
        # Agent metadata
        self.agent_type = "{{AGENT_TYPE}}"
        self.agent_tier = "project"
        self.agent_priority = 3
        self.agent_authority = "project_highest"
        
        # Project-specific configuration
        self.project_path = project_path
        self.project_name = project_path.name
        self.system_access = False
        self.network_access = True
        self.override_user = True
        self.override_system = True
        
        # Project-specific settings
        self.project_settings = {}
        self.project_context = {}
        self.custom_workflows = []
        
        # Agent capabilities
        self.capabilities = [
            "project_{{AGENT_TYPE}}_operations",
            "context_aware_processing",
            "project_customization",
            "agent_override"
        ]
        
        # Performance metrics
        self.start_time = None
        self.operations_count = 0
        self.error_count = 0
        self.context_adaptations = 0
        self.overrides_applied = 0
        
        self.logger.info(f"Initialized {{AGENT_TYPE}} project agent: {{AGENT_NAME}} for project: {self.project_name}")
    
    async def _initialize(self) -> None:
        """Initialize the project agent."""
        try:
            self.start_time = datetime.now()
            
            # Analyze project context
            await self._analyze_project_context()
            
            # Load project settings
            await self._load_project_settings()
            
            # Initialize project-specific resources
            await self._initialize_project_resources()
            
            # Setup project customizations
            await self._setup_project_customizations()
            
            # Initialize agent capabilities
            await self._initialize_capabilities()
            
            # Register with framework
            await self._register_with_framework()
            
            self.logger.info(f"{{AGENT_TYPE}} project agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {{AGENT_TYPE}} project agent: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup project agent resources."""
        try:
            # Save project settings
            await self._save_project_settings()
            
            # Cleanup capabilities
            await self._cleanup_capabilities()
            
            # Cleanup project resources
            await self._cleanup_project_resources()
            
            # Unregister from framework
            await self._unregister_from_framework()
            
            self.logger.info(f"{{AGENT_TYPE}} project agent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup {{AGENT_TYPE}} project agent: {e}")
            raise
    
    async def _analyze_project_context(self) -> None:
        """Analyze project context for adaptive behavior."""
        try:
            # Analyze project structure
            project_files = list(self.project_path.glob("**/*"))
            
            # Detect project type
            project_type = self._detect_project_type()
            
            # Analyze dependencies
            dependencies = await self._analyze_dependencies()
            
            # Build context
            self.project_context = {
                "project_type": project_type,
                "file_count": len(project_files),
                "dependencies": dependencies,
                "last_analyzed": datetime.now().isoformat()
            }
            
            self.logger.debug(f"Analyzed project context: {project_type}")
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze project context: {e}")
            self.project_context = {}
    
    def _detect_project_type(self) -> str:
        """Detect the type of project."""
        # Check for common project indicators
        if (self.project_path / "package.json").exists():
            return "node_js"
        elif (self.project_path / "pyproject.toml").exists():
            return "python"
        elif (self.project_path / "Cargo.toml").exists():
            return "rust"
        elif (self.project_path / "go.mod").exists():
            return "go"
        elif (self.project_path / ".git").exists():
            return "git_repository"
        else:
            return "unknown"
    
    async def _analyze_dependencies(self) -> List[str]:
        """Analyze project dependencies."""
        dependencies = []
        
        # Check package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    deps = package_data.get("dependencies", {})
                    dev_deps = package_data.get("devDependencies", {})
                    dependencies.extend(list(deps.keys()) + list(dev_deps.keys()))
            except Exception as e:
                self.logger.warning(f"Failed to analyze package.json: {e}")
        
        # Check pyproject.toml
        pyproject_toml = self.project_path / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                import toml
                with open(pyproject_toml, 'r') as f:
                    pyproject_data = toml.load(f)
                    deps = pyproject_data.get("project", {}).get("dependencies", [])
                    dependencies.extend(deps)
            except Exception as e:
                self.logger.warning(f"Failed to analyze pyproject.toml: {e}")
        
        return dependencies
    
    async def _load_project_settings(self) -> None:
        """Load project-specific settings."""
        try:
            settings_file = self.project_path / ".claude-pm" / "agents" / "project-specific" / "config" / f"{self.name}.yaml"
            
            if settings_file.exists():
                import yaml
                with open(settings_file, 'r') as f:
                    self.project_settings = yaml.safe_load(f) or {}
            else:
                self.project_settings = {}
            
            self.logger.debug("Loaded project settings")
            
        except Exception as e:
            self.logger.warning(f"Failed to load project settings: {e}")
            self.project_settings = {}
    
    async def _save_project_settings(self) -> None:
        """Save project-specific settings."""
        try:
            settings_file = self.project_path / ".claude-pm" / "agents" / "project-specific" / "config" / f"{self.name}.yaml"
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            import yaml
            with open(settings_file, 'w') as f:
                yaml.dump(self.project_settings, f, default_flow_style=False, indent=2)
            
            self.logger.debug("Saved project settings")
            
        except Exception as e:
            self.logger.warning(f"Failed to save project settings: {e}")
    
    async def _initialize_project_resources(self) -> None:
        """Initialize project-specific resources."""
        # TODO: Implement project resource initialization
        self.logger.debug("Initializing project resources")
    
    async def _setup_project_customizations(self) -> None:
        """Setup project-specific customizations."""
        # TODO: Implement project customization setup
        self.logger.debug("Setting up project customizations")
    
    async def _initialize_capabilities(self) -> None:
        """Initialize agent capabilities."""
        # TODO: Implement capability initialization
        self.logger.debug("Initializing agent capabilities")
    
    async def _register_with_framework(self) -> None:
        """Register agent with the framework."""
        # TODO: Implement framework registration
        self.logger.debug("Registering with framework")
    
    async def _cleanup_capabilities(self) -> None:
        """Cleanup agent capabilities."""
        # TODO: Implement capability cleanup
        self.logger.debug("Cleaning up capabilities")
    
    async def _cleanup_project_resources(self) -> None:
        """Cleanup project resources."""
        # TODO: Implement project resource cleanup
        self.logger.debug("Cleaning up project resources")
    
    async def _unregister_from_framework(self) -> None:
        """Unregister agent from framework."""
        # TODO: Implement framework unregistration
        self.logger.debug("Unregistering from framework")
    
    async def execute_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a {{AGENT_TYPE}} operation with project-specific context.
        
        Args:
            operation: Operation name
            **kwargs: Operation parameters
            
        Returns:
            Operation result
        """
        operation_start = time.time()
        
        try:
            self.operations_count += 1
            
            # Apply project context
            kwargs = await self._apply_project_context(operation, kwargs)
            
            # Apply project customizations
            kwargs = await self._apply_project_customizations(operation, kwargs)
            
            # Log operation
            self.logger.info(f"Executing {{AGENT_TYPE}} operation: {operation}")
            
            # Execute operation based on type
            if operation == "project_analysis":
                result = await self._analyze_project(**kwargs)
            elif operation == "context_adaptation":
                result = await self._adapt_to_context(**kwargs)
            elif operation == "project_workflow":
                result = await self._execute_project_workflow(**kwargs)
            elif operation == "override_behavior":
                result = await self._override_behavior(**kwargs)
            else:
                result = await self._execute_custom_operation(operation, **kwargs)
            
            # Record success metrics
            operation_time = time.time() - operation_start
            self.logger.info(f"Operation {operation} completed in {operation_time:.2f}s")
            
            return {
                "success": True,
                "operation": operation,
                "result": result,
                "execution_time": operation_time,
                "agent_type": self.agent_type,
                "agent_tier": self.agent_tier,
                "project_name": self.project_name,
                "context_adaptations": self.context_adaptations,
                "overrides_applied": self.overrides_applied
            }
            
        except Exception as e:
            self.error_count += 1
            operation_time = time.time() - operation_start
            
            self.logger.error(f"Operation {operation} failed: {e}")
            
            return {
                "success": False,
                "operation": operation,
                "error": str(e),
                "execution_time": operation_time,
                "agent_type": self.agent_type,
                "agent_tier": self.agent_tier,
                "project_name": self.project_name
            }
    
    async def _apply_project_context(self, operation: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply project context to operation parameters."""
        # TODO: Implement project context application
        self.context_adaptations += 1
        kwargs["project_context"] = self.project_context
        return kwargs
    
    async def _apply_project_customizations(self, operation: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply project customizations to operation parameters."""
        # TODO: Implement project customization application
        kwargs["project_settings"] = self.project_settings
        return kwargs
    
    async def _analyze_project(self, **kwargs) -> Dict[str, Any]:
        """Analyze current project."""
        return {
            "project_path": str(self.project_path),
            "project_name": self.project_name,
            "project_context": self.project_context,
            "project_settings": self.project_settings,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def _adapt_to_context(self, **kwargs) -> Dict[str, Any]:
        """Adapt agent behavior to project context."""
        # TODO: Implement context adaptation
        self.context_adaptations += 1
        return {
            "adaptation": "context adaptation not implemented",
            "context": self.project_context,
            "parameters": kwargs
        }
    
    async def _execute_project_workflow(self, **kwargs) -> Dict[str, Any]:
        """Execute project-specific workflow."""
        # TODO: Implement project workflow execution
        return {
            "workflow": "project workflow not implemented",
            "project": self.project_name,
            "parameters": kwargs
        }
    
    async def _override_behavior(self, **kwargs) -> Dict[str, Any]:
        """Override higher-tier agent behavior."""
        # TODO: Implement behavior override
        self.overrides_applied += 1
        return {
            "override": "behavior override not implemented",
            "overrides_applied": self.overrides_applied,
            "parameters": kwargs
        }
    
    async def _execute_custom_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute custom operation."""
        # TODO: Implement custom operation handling
        return {
            "message": f"Custom operation {operation} not implemented",
            "parameters": kwargs
        }
    
    async def add_custom_workflow(self, workflow_name: str, workflow_steps: List[Dict[str, Any]]) -> bool:
        """Add a custom workflow to the agent."""
        try:
            self.custom_workflows.append({
                "name": workflow_name,
                "steps": workflow_steps,
                "added_at": datetime.now().isoformat()
            })
            await self._save_project_settings()
            self.logger.info(f"Added custom workflow: {workflow_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add custom workflow {workflow_name}: {e}")
            return False
    
    async def remove_custom_workflow(self, workflow_name: str) -> bool:
        """Remove a custom workflow from the agent."""
        try:
            self.custom_workflows = [
                workflow for workflow in self.custom_workflows 
                if workflow["name"] != workflow_name
            ]
            await self._save_project_settings()
            self.logger.info(f"Removed custom workflow: {workflow_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove custom workflow {workflow_name}: {e}")
            return False
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        return {
            "agent_name": self.name,
            "agent_type": self.agent_type,
            "agent_tier": self.agent_tier,
            "agent_priority": self.agent_priority,
            "agent_authority": self.agent_authority,
            "project_name": self.project_name,
            "project_path": str(self.project_path),
            "running": self.running,
            "uptime": self.uptime,
            "capabilities": self.capabilities,
            "operations_count": self.operations_count,
            "error_count": self.error_count,
            "context_adaptations": self.context_adaptations,
            "overrides_applied": self.overrides_applied,
            "custom_workflows_count": len(self.custom_workflows),
            "project_settings_count": len(self.project_settings),
            "last_health_check": datetime.now().isoformat()
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "operations_per_second": self.operations_count / (self.uptime or 1),
            "error_rate": self.error_count / (self.operations_count or 1),
            "context_adaptation_rate": self.context_adaptations / (self.operations_count or 1),
            "override_rate": self.overrides_applied / (self.operations_count or 1),
            "uptime_seconds": self.uptime or 0,
            "memory_usage": 0.0,  # TODO: Implement memory monitoring
            "cpu_usage": 0.0      # TODO: Implement CPU monitoring
        }
    
    async def _health_check(self) -> Dict[str, bool]:
        """Project agent health check."""
        checks = {}
        
        # Check if agent is running
        checks["agent_running"] = self.running
        
        # Check project path
        checks["project_path_exists"] = self.project_path.exists()
        
        # Check project context
        checks["project_context_loaded"] = len(self.project_context) > 0
        
        # Check project settings
        checks["project_settings_loaded"] = len(self.project_settings) >= 0
        
        # Check capabilities
        checks["capabilities_ready"] = True  # TODO: Implement capability readiness check
        
        # Check error rate
        error_rate = self.error_count / (self.operations_count or 1)
        checks["low_error_rate"] = error_rate < 0.1  # Less than 10% error rate
        
        return checks
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information."""
        return {
            "agent_metadata": {
                "name": self.name,
                "type": self.agent_type,
                "tier": self.agent_tier,
                "priority": self.agent_priority,
                "authority": self.agent_authority,
                "created": "{{TIMESTAMP}}"
            },
            "project_info": {
                "project_name": self.project_name,
                "project_path": str(self.project_path),
                "project_type": self.project_context.get("project_type", "unknown")
            },
            "configuration": {
                "system_access": self.system_access,
                "network_access": self.network_access,
                "override_user": self.override_user,
                "override_system": self.override_system
            },
            "capabilities": self.capabilities,
            "customizations": {
                "project_settings": len(self.project_settings),
                "custom_workflows": len(self.custom_workflows),
                "context_adaptations": self.context_adaptations,
                "overrides_applied": self.overrides_applied
            },
            "runtime_info": {
                "running": self.running,
                "uptime": self.uptime,
                "operations_count": self.operations_count,
                "error_count": self.error_count
            }
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{{CLASS_NAME}}(name='{self.name}', type='{self.agent_type}', tier='{self.agent_tier}', project='{self.project_name}')"
    
    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return f"<{{CLASS_NAME}} name='{self.name}' type='{self.agent_type}' tier='{self.agent_tier}' project='{self.project_name}' running={self.running}>"