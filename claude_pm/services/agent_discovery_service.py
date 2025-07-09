#!/usr/bin/env python3
"""
Agent Discovery Service for Claude PM Framework
==============================================

This service provides automatic agent discovery and management across
the three-tier agent hierarchy (system, user, project).

Key Features:
- Automatic agent discovery across all tiers
- Real-time agent monitoring and health checking
- Agent lifecycle management
- Template-based agent creation
- Integration with HierarchicalAgentLoader
- CLI management commands
"""

import asyncio
import json
import yaml
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..core.base_service import BaseService
from ..core.config import Config
from ..core.logging_config import setup_logging
from ..agents.hierarchical_agent_loader import HierarchicalAgentLoader, AgentInfo, AgentHierarchy


@dataclass
class AgentDiscoveryEvent:
    """Event for agent discovery operations."""
    event_type: str  # discovered, modified, removed, loaded, unloaded
    agent_name: str
    agent_type: str
    tier: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)


class AgentFileWatcher(FileSystemEventHandler):
    """File system watcher for agent directory changes."""
    
    def __init__(self, discovery_service: 'AgentDiscoveryService'):
        self.discovery_service = discovery_service
        self.logger = setup_logging("agent_file_watcher")
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.info(f"New agent file detected: {event.src_path}")
            asyncio.create_task(self.discovery_service.handle_agent_file_change(
                event.src_path, 'created'
            ))
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.info(f"Agent file modified: {event.src_path}")
            asyncio.create_task(self.discovery_service.handle_agent_file_change(
                event.src_path, 'modified'
            ))
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.info(f"Agent file deleted: {event.src_path}")
            asyncio.create_task(self.discovery_service.handle_agent_file_change(
                event.src_path, 'deleted'
            ))


class AgentDiscoveryService(BaseService):
    """
    Service for discovering and managing agents across the three-tier hierarchy.
    
    This service:
    - Discovers agents across system, user, and project tiers
    - Monitors agent file changes in real-time
    - Manages agent lifecycle (load, unload, reload)
    - Provides health monitoring for agents
    - Generates agent templates
    - Integrates with CLI commands
    """
    
    def __init__(
        self,
        framework_path: Path,
        user_home: Path,
        project_path: Path,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name="agent_discovery_service", config=config)
        
        self.framework_path = framework_path
        self.user_home = user_home
        self.project_path = project_path
        
        # Initialize hierarchical agent loader
        self.agent_loader = HierarchicalAgentLoader(
            framework_path=framework_path,
            user_home=user_home,
            project_path=project_path,
            config=config
        )
        
        # Discovery state
        self.discovery_events: List[AgentDiscoveryEvent] = []
        self.last_discovery_time: Optional[datetime] = None
        self.discovery_stats = {
            "total_discoveries": 0,
            "successful_loads": 0,
            "failed_loads": 0,
            "agents_monitored": 0
        }
        
        # File system monitoring
        self.file_observer: Optional[Observer] = None
        self.file_watcher = AgentFileWatcher(self)
        
        # Agent registry cache
        self.agent_registry_path = project_path / ".claude-multiagent-pm" / "agents" / "registry.json"
        
        self.logger.info(f"Initialized AgentDiscoveryService")
    
    async def _initialize(self) -> None:
        """Initialize the agent discovery service."""
        try:
            # Initialize agent loader
            await self.agent_loader.start()
            
            # Initial agent discovery
            await self.discover_all_agents()
            
            # Start file monitoring if enabled
            if self.get_config("file_monitoring_enabled", True):
                await self.start_file_monitoring()
            
            # Start periodic health checks
            if self.get_config("health_monitoring_enabled", True):
                self.schedule_health_checks()
            
            self.logger.info("AgentDiscoveryService initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentDiscoveryService: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup the agent discovery service."""
        try:
            # Stop file monitoring
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join()
            
            # Stop agent loader
            await self.agent_loader.stop()
            
            # Save final registry state
            await self.save_agent_registry()
            
            self.logger.info("AgentDiscoveryService cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup AgentDiscoveryService: {e}")
            raise
    
    async def discover_all_agents(self) -> Dict[str, Any]:
        """
        Perform comprehensive agent discovery across all tiers.
        
        Returns:
            Discovery results with agent counts and details
        """
        self.logger.info("Starting comprehensive agent discovery...")
        
        discovery_start = time.time()
        
        try:
            # Trigger discovery in the hierarchical loader
            await self.agent_loader._discover_agents()
            
            # Get the discovered hierarchy
            hierarchy = self.agent_loader.hierarchy
            
            # Update discovery stats
            self.discovery_stats["total_discoveries"] += 1
            self.discovery_stats["agents_monitored"] = len(hierarchy.get_all_agents())
            self.last_discovery_time = datetime.now()
            
            # Create discovery event
            discovery_event = AgentDiscoveryEvent(
                event_type="discovery_complete",
                agent_name="all",
                agent_type="all",
                tier="all",
                timestamp=datetime.now().isoformat(),
                details={
                    "system_agents": len(hierarchy.system_agents),
                    "user_agents": len(hierarchy.user_agents),
                    "project_agents": len(hierarchy.project_agents),
                    "total_agents": len(hierarchy.get_all_agents()),
                    "discovery_time": time.time() - discovery_start
                }
            )
            
            self.discovery_events.append(discovery_event)
            
            # Update agent registry
            await self.update_agent_registry()
            
            discovery_results = {
                "success": True,
                "discovery_time": time.time() - discovery_start,
                "agents_discovered": {
                    "system": len(hierarchy.system_agents),
                    "user": len(hierarchy.user_agents),
                    "project": len(hierarchy.project_agents),
                    "total": len(hierarchy.get_all_agents())
                },
                "agent_types": hierarchy.get_available_types(),
                "last_discovery": self.last_discovery_time.isoformat()
            }
            
            self.logger.info(f"Agent discovery completed in {discovery_results['discovery_time']:.2f}s")
            self.logger.info(f"Discovered {discovery_results['agents_discovered']['total']} agents")
            
            return discovery_results
            
        except Exception as e:
            self.logger.error(f"Agent discovery failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "discovery_time": time.time() - discovery_start
            }
    
    async def start_file_monitoring(self) -> None:
        """Start file system monitoring for agent directories."""
        try:
            if self.file_observer:
                return  # Already monitoring
            
            self.file_observer = Observer()
            
            # Monitor agent directories
            directories_to_monitor = [
                self.framework_path / "claude_pm" / "agents",
                self.user_home / ".claude-multiagent-pm" / "agents" / "user-defined",
                self.project_path / ".claude-multiagent-pm" / "agents" / "project-specific"
            ]
            
            for directory in directories_to_monitor:
                if directory.exists():
                    self.file_observer.schedule(
                        self.file_watcher, 
                        str(directory), 
                        recursive=True
                    )
                    self.logger.info(f"Started monitoring: {directory}")
            
            self.file_observer.start()
            self.logger.info("File monitoring started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start file monitoring: {e}")
    
    async def handle_agent_file_change(self, file_path: str, event_type: str) -> None:
        """Handle agent file change events."""
        try:
            path = Path(file_path)
            
            # Determine tier based on path
            tier = self.determine_tier_from_path(path)
            if not tier:
                return
            
            # Extract agent name
            agent_name = path.stem
            
            # Handle different event types
            if event_type == 'created':
                await self.handle_agent_created(path, tier)
            elif event_type == 'modified':
                await self.handle_agent_modified(path, tier)
            elif event_type == 'deleted':
                await self.handle_agent_deleted(path, tier)
            
            # Trigger rediscovery
            await self.discover_all_agents()
            
        except Exception as e:
            self.logger.error(f"Failed to handle agent file change: {e}")
    
    def determine_tier_from_path(self, path: Path) -> Optional[str]:
        """Determine agent tier from file path."""
        path_str = str(path)
        
        if "claude_pm/agents" in path_str:
            return "system"
        elif "user-defined" in path_str:
            return "user"
        elif "project-specific" in path_str:
            return "project"
        
        return None
    
    async def handle_agent_created(self, path: Path, tier: str) -> None:
        """Handle new agent file creation."""
        agent_name = path.stem
        
        # Create discovery event
        event = AgentDiscoveryEvent(
            event_type="discovered",
            agent_name=agent_name,
            agent_type="unknown",  # Will be determined during discovery
            tier=tier,
            timestamp=datetime.now().isoformat(),
            details={"file_path": str(path)}
        )
        
        self.discovery_events.append(event)
        self.logger.info(f"New {tier} agent discovered: {agent_name}")
    
    async def handle_agent_modified(self, path: Path, tier: str) -> None:
        """Handle agent file modification."""
        agent_name = path.stem
        
        # Try to reload the agent if it's currently loaded
        agent_type = self.get_agent_type_by_name(agent_name)
        if agent_type and agent_type in self.agent_loader.get_loaded_agents():
            await self.agent_loader.reload_agent(agent_type)
            self.logger.info(f"Reloaded {tier} agent: {agent_name}")
        
        # Create discovery event
        event = AgentDiscoveryEvent(
            event_type="modified",
            agent_name=agent_name,
            agent_type=agent_type or "unknown",
            tier=tier,
            timestamp=datetime.now().isoformat(),
            details={"file_path": str(path)}
        )
        
        self.discovery_events.append(event)
    
    async def handle_agent_deleted(self, path: Path, tier: str) -> None:
        """Handle agent file deletion."""
        agent_name = path.stem
        
        # Try to unload the agent if it's currently loaded
        agent_type = self.get_agent_type_by_name(agent_name)
        if agent_type and agent_type in self.agent_loader.get_loaded_agents():
            await self.agent_loader.unload_agent(agent_type)
            self.logger.info(f"Unloaded deleted {tier} agent: {agent_name}")
        
        # Create discovery event
        event = AgentDiscoveryEvent(
            event_type="removed",
            agent_name=agent_name,
            agent_type=agent_type or "unknown",
            tier=tier,
            timestamp=datetime.now().isoformat(),
            details={"file_path": str(path)}
        )
        
        self.discovery_events.append(event)
    
    def get_agent_type_by_name(self, agent_name: str) -> Optional[str]:
        """Get agent type by name from the current hierarchy."""
        all_agents = self.agent_loader.hierarchy.get_all_agents()
        for name, agent_info in all_agents.items():
            if name == agent_name:
                return agent_info.agent_type
        return None
    
    def schedule_health_checks(self) -> None:
        """Schedule periodic health checks for loaded agents."""
        interval = self.get_config("health_check_interval", 60)
        
        async def health_check_task():
            while not self._stop_event.is_set():
                try:
                    await self.perform_agent_health_checks()
                    await asyncio.sleep(interval)
                except Exception as e:
                    self.logger.error(f"Health check error: {e}")
                    await asyncio.sleep(interval)
        
        task = asyncio.create_task(health_check_task())
        self._background_tasks.append(task)
    
    async def perform_agent_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on all loaded agents."""
        health_results = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.agent_loader.get_loaded_agents()),
            "healthy_agents": 0,
            "unhealthy_agents": 0,
            "agent_health": {}
        }
        
        loaded_agents = self.agent_loader.get_loaded_agents()
        
        for agent_type, agent_instance in loaded_agents.items():
            try:
                # Check if agent has health check method
                if hasattr(agent_instance, 'health_check'):
                    if asyncio.iscoroutinefunction(agent_instance.health_check):
                        health_status = await agent_instance.health_check()
                    else:
                        health_status = agent_instance.health_check()
                    
                    is_healthy = health_status.get('healthy', True)
                else:
                    # Basic health check - just verify instance exists
                    is_healthy = agent_instance is not None
                    health_status = {"healthy": is_healthy, "message": "Basic health check"}
                
                health_results["agent_health"][agent_type] = health_status
                
                if is_healthy:
                    health_results["healthy_agents"] += 1
                else:
                    health_results["unhealthy_agents"] += 1
                
            except Exception as e:
                self.logger.error(f"Health check failed for {agent_type}: {e}")
                health_results["agent_health"][agent_type] = {
                    "healthy": False,
                    "error": str(e)
                }
                health_results["unhealthy_agents"] += 1
        
        # Update discovery stats
        self.discovery_stats["agents_monitored"] = health_results["total_agents"]
        
        return health_results
    
    async def load_agent_by_type(self, agent_type: str, **kwargs) -> Optional[Any]:
        """Load an agent of a specific type."""
        try:
            agent_instance = await self.agent_loader.load_agent(agent_type, **kwargs)
            
            if agent_instance:
                self.discovery_stats["successful_loads"] += 1
                
                # Create load event
                event = AgentDiscoveryEvent(
                    event_type="loaded",
                    agent_name=agent_type,
                    agent_type=agent_type,
                    tier="unknown",  # Will be determined from hierarchy
                    timestamp=datetime.now().isoformat(),
                    details={"load_success": True}
                )
                
                self.discovery_events.append(event)
                self.logger.info(f"Successfully loaded {agent_type} agent")
            else:
                self.discovery_stats["failed_loads"] += 1
                
                # Create failure event
                event = AgentDiscoveryEvent(
                    event_type="load_failed",
                    agent_name=agent_type,
                    agent_type=agent_type,
                    tier="unknown",
                    timestamp=datetime.now().isoformat(),
                    details={"load_success": False, "error": "Agent not found"}
                )
                
                self.discovery_events.append(event)
                self.logger.warning(f"Failed to load {agent_type} agent")
            
            return agent_instance
            
        except Exception as e:
            self.discovery_stats["failed_loads"] += 1
            self.logger.error(f"Error loading {agent_type} agent: {e}")
            return None
    
    async def unload_agent_by_type(self, agent_type: str) -> bool:
        """Unload an agent of a specific type."""
        try:
            success = await self.agent_loader.unload_agent(agent_type)
            
            # Create unload event
            event = AgentDiscoveryEvent(
                event_type="unloaded",
                agent_name=agent_type,
                agent_type=agent_type,
                tier="unknown",
                timestamp=datetime.now().isoformat(),
                details={"unload_success": success}
            )
            
            self.discovery_events.append(event)
            
            if success:
                self.logger.info(f"Successfully unloaded {agent_type} agent")
            else:
                self.logger.warning(f"Failed to unload {agent_type} agent")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error unloading {agent_type} agent: {e}")
            return False
    
    async def update_agent_registry(self) -> None:
        """Update the agent registry with current discovery state."""
        try:
            hierarchy = self.agent_loader.hierarchy
            
            registry_data = {
                "registry_version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "last_discovery": self.last_discovery_time.isoformat() if self.last_discovery_time else None,
                "total_agents": len(hierarchy.get_all_agents()),
                "agents_by_tier": {
                    "system": {agent.name: {
                        "type": agent.agent_type,
                        "path": str(agent.path),
                        "loaded": agent.loaded,
                        "health_status": agent.health_status,
                        "last_loaded": agent.last_loaded
                    } for agent in hierarchy.system_agents.values()},
                    "user": {agent.name: {
                        "type": agent.agent_type,
                        "path": str(agent.path),
                        "loaded": agent.loaded,
                        "health_status": agent.health_status,
                        "last_loaded": agent.last_loaded
                    } for agent in hierarchy.user_agents.values()},
                    "project": {agent.name: {
                        "type": agent.agent_type,
                        "path": str(agent.path),
                        "loaded": agent.loaded,
                        "health_status": agent.health_status,
                        "last_loaded": agent.last_loaded
                    } for agent in hierarchy.project_agents.values()}
                },
                "agent_types": {agent_type: {
                    "available": True,
                    "tier": hierarchy.get_agent_by_type(agent_type).tier if hierarchy.get_agent_by_type(agent_type) else "unknown"
                } for agent_type in hierarchy.get_available_types()},
                "discovery_stats": self.discovery_stats,
                "health_status": {
                    "total_agents": len(hierarchy.get_all_agents()),
                    "loaded_agents": len(self.agent_loader.get_loaded_agents()),
                    "unloaded_agents": len(hierarchy.get_all_agents()) - len(self.agent_loader.get_loaded_agents())
                }
            }
            
            # Ensure directory exists
            self.agent_registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save registry
            with open(self.agent_registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            
            self.logger.debug("Agent registry updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update agent registry: {e}")
    
    async def save_agent_registry(self) -> None:
        """Save the current agent registry state."""
        await self.update_agent_registry()
    
    async def get_discovery_status(self) -> Dict[str, Any]:
        """Get current discovery status and statistics."""
        return {
            "service_status": "running" if self.running else "stopped",
            "last_discovery": self.last_discovery_time.isoformat() if self.last_discovery_time else None,
            "discovery_stats": self.discovery_stats.copy(),
            "file_monitoring": self.file_observer is not None and self.file_observer.is_alive(),
            "loaded_agents": len(self.agent_loader.get_loaded_agents()),
            "total_agents": len(self.agent_loader.hierarchy.get_all_agents()),
            "recent_events": self.discovery_events[-10:] if self.discovery_events else []
        }
    
    async def get_agent_hierarchy_status(self) -> Dict[str, Any]:
        """Get comprehensive agent hierarchy status."""
        hierarchy = self.agent_loader.hierarchy
        
        return {
            "hierarchy_valid": True,  # TODO: Implement validation
            "total_agents": len(hierarchy.get_all_agents()),
            "tiers": {
                "system": {
                    "count": len(hierarchy.system_agents),
                    "agents": list(hierarchy.system_agents.keys())
                },
                "user": {
                    "count": len(hierarchy.user_agents),
                    "agents": list(hierarchy.user_agents.keys())
                },
                "project": {
                    "count": len(hierarchy.project_agents),
                    "agents": list(hierarchy.project_agents.keys())
                }
            },
            "agent_types": hierarchy.get_available_types(),
            "loaded_agents": list(self.agent_loader.get_loaded_agents().keys())
        }
    
    async def _health_check(self) -> Dict[str, bool]:
        """Custom health checks for the discovery service."""
        checks = {}
        
        # Check if agent loader is healthy
        loader_health = await self.agent_loader.health_check()
        checks["agent_loader_healthy"] = loader_health.status == "healthy"
        
        # Check file monitoring
        checks["file_monitoring_active"] = (
            self.file_observer is not None and 
            self.file_observer.is_alive()
        )
        
        # Check recent discovery activity
        checks["recent_discovery"] = (
            self.last_discovery_time is not None and
            (datetime.now() - self.last_discovery_time).total_seconds() < 3600  # Within last hour
        )
        
        # Check agent registry
        checks["agent_registry_exists"] = self.agent_registry_path.exists()
        
        return checks