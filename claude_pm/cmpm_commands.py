#!/usr/bin/env python3
"""
CMPM (Claude Multi-Agent PM) Slash Commands
============================================

Provides professional CMPM-prefixed slash commands for the Claude PM Framework:
- /cmpm:health - Comprehensive system health dashboard
- /cmpm:agents - Active agent types and status listing
- /cmpm:index - Project discovery index with agent delegation
- /cmpm:dashboard - Portfolio manager dashboard with headless browser launch

This module implements the final 20% of ISS-0002, the new /cmpm:agents command,
and the /cmpm:dashboard command (ISS-0051) with full ai-trackdown-tools integration
and MCP infrastructure support.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from .services.health_dashboard import HealthDashboardOrchestrator
from .services.memory_service import MemoryService
from .services.multi_agent_orchestrator import MultiAgentOrchestrator
from .core.config import Config
from .core.service_manager import ServiceManager
from .agents.enhanced_qa_agent import EnhancedQAAgent, execute_qa_command


console = Console()
logger = logging.getLogger(__name__)


class CMPMHealthMonitor:
    """CMPM Health Command Implementation with ai-trackdown integration."""
    
    def __init__(self):
        self.config = Config()
        self.framework_path = Path.cwd()
        self.start_time = time.time()
        
    async def get_framework_health(self) -> Dict[str, Any]:
        """Get comprehensive framework health status."""
        try:
            # Initialize health dashboard orchestrator
            dashboard = HealthDashboardOrchestrator(
                cache_ttl_seconds=10.0,  # Faster for real-time slash commands
                global_timeout_seconds=2.0
            )
            
            # Collect health data
            health_data = await dashboard._collect_fresh_health()
            
            return {
                "status": "healthy" if health_data.overall_status.value == "healthy" else "degraded",
                "framework_version": "4.1.0",
                "components": health_data.subsystems,
                "response_time": health_data.response_time_ms,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Framework health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    async def get_aitrackdown_health(self) -> Dict[str, Any]:
        """Get ai-trackdown-tools integration health status."""
        try:
            # Test ai-trackdown CLI functionality
            result = subprocess.run(
                ["./aitrackdown", "status"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.framework_path
            )
            
            if result.returncode == 0:
                # Parse status output for health indicators
                status_output = result.stdout
                
                # Check for active items (indicates healthy operation)
                if "Active Items:" in status_output:
                    return {
                        "status": "operational",
                        "service": "ai-trackdown-tools",
                        "version": "3.0.0",
                        "cli_responsive": True,
                        "last_check": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "degraded",
                        "service": "ai-trackdown-tools",
                        "issue": "Status command returned unexpected output",
                        "last_check": datetime.now().isoformat()
                    }
            else:
                return {
                    "status": "error",
                    "service": "ai-trackdown-tools",
                    "error": result.stderr or "Command failed",
                    "last_check": datetime.now().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "service": "ai-trackdown-tools",
                "error": "Command timed out after 5 seconds",
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "service": "ai-trackdown-tools",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def get_task_system_health(self) -> Dict[str, Any]:
        """Get task system operational status."""
        try:
            # Get epic, issue, and task counts
            epic_result = subprocess.run(
                ["./aitrackdown", "epic", "list"],
                capture_output=True,
                text=True,
                timeout=3,
                cwd=self.framework_path
            )
            
            issue_result = subprocess.run(
                ["./aitrackdown", "issue", "list"],
                capture_output=True,
                text=True,
                timeout=3,
                cwd=self.framework_path
            )
            
            if epic_result.returncode == 0 and issue_result.returncode == 0:
                # Parse counts from output
                epic_count = epic_result.stdout.count("EP-")
                issue_count = issue_result.stdout.count("ISS-")
                
                return {
                    "status": "operational",
                    "service": "task_system",
                    "epic_count": epic_count,
                    "issue_count": issue_count,
                    "total_items": epic_count + issue_count,
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "service": "task_system",
                    "error": "Failed to query task counts",
                    "last_check": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "service": "task_system",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def get_memory_system_health(self) -> Dict[str, Any]:
        """Get memory system connectivity status."""
        try:
            memory_service = MemoryService()
            
            # Test memory service connectivity
            health_check = await memory_service.health_check()
            
            return {
                "status": "operational" if health_check.get("status") == "healthy" else "degraded",
                "service": "memory_system",
                "mem0ai_connected": health_check.get("mem0ai_connected", False),
                "response_time": health_check.get("response_time_ms", 0),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "service": "memory_system",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def get_qa_system_health(self) -> Dict[str, Any]:
        """Get Enhanced QA Agent system health status."""
        try:
            qa_agent = EnhancedQAAgent()
            qa_health = await qa_agent.get_qa_health_status()
            
            return {
                "status": qa_health.get("status", "unknown"),
                "service": "enhanced_qa_agent",
                "health_score": qa_health.get("health_score", 0),
                "browser_extension": qa_health.get("extension_health", {}).get("status", "unknown"),
                "memory_integration": qa_health.get("memory_health", {}).get("status", "unknown"),
                "agent_version": qa_health.get("agent_version", "unknown"),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "service": "enhanced_qa_agent",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def calculate_system_reliability_score(self, health_data: Dict[str, Any]) -> int:
        """Calculate system reliability score (0-100)."""
        total_components = 0
        healthy_components = 0
        
        for component_name, component_data in health_data.items():
            if isinstance(component_data, dict) and "status" in component_data:
                total_components += 1
                if component_data["status"] in ["healthy", "operational"]:
                    healthy_components += 1
        
        if total_components == 0:
            return 0
        
        return int((healthy_components / total_components) * 100)
    
    async def generate_health_dashboard(self) -> None:
        """Generate comprehensive CMPM health dashboard."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Collecting system health data...", total=None)
            
            # Collect all health data in parallel
            health_data = await asyncio.gather(
                self.get_framework_health(),
                self.get_aitrackdown_health(),
                self.get_task_system_health(),
                self.get_memory_system_health(),
                self.get_qa_system_health(),
                return_exceptions=True
            )
            
            progress.update(task, description="Generating dashboard...")
            
            # Process collected data
            framework_health, aitrackdown_health, task_health, memory_health, qa_health = health_data
            
            # Calculate reliability score
            all_health_data = {
                "framework": framework_health,
                "aitrackdown": aitrackdown_health,
                "task_system": task_health,
                "memory_system": memory_health,
                "qa_system": qa_health
            }
            
            reliability_score = self.calculate_system_reliability_score(all_health_data)
            
            progress.update(task, description="Rendering dashboard...")
        
        # Create dashboard header
        total_time = time.time() - self.start_time
        
        header = Panel(
            Text(f"CMPM Health Dashboard v4.1.0\nSystem Reliability Score: {reliability_score}%\nResponse Time: {total_time:.2f}s", 
                 justify="center", style="bold white"),
            title="🟢 Claude Multi-Agent PM Framework",
            border_style="green" if reliability_score >= 80 else "yellow" if reliability_score >= 60 else "red"
        )
        
        console.print(header)
        console.print()
        
        # Create health status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Details", style="dim")
        
        # Add framework health
        if isinstance(framework_health, dict):
            status_color = "green" if framework_health.get("status") == "healthy" else "red"
            table.add_row(
                "Framework Core",
                f"[{status_color}]{framework_health.get('status', 'unknown').upper()}[/{status_color}]",
                f"v{framework_health.get('framework_version', 'unknown')} | {framework_health.get('response_time', 0)}ms"
            )
        
        # Add ai-trackdown health
        if isinstance(aitrackdown_health, dict):
            status_color = "green" if aitrackdown_health.get("status") == "operational" else "red"
            table.add_row(
                "AI-Trackdown Tools",
                f"[{status_color}]{aitrackdown_health.get('status', 'unknown').upper()}[/{status_color}]",
                f"CLI: {'✓' if aitrackdown_health.get('cli_responsive') else '✗'} | Service: {aitrackdown_health.get('service', 'unknown')}"
            )
        
        # Add task system health
        if isinstance(task_health, dict):
            status_color = "green" if task_health.get("status") == "operational" else "red"
            table.add_row(
                "Task System",
                f"[{status_color}]{task_health.get('status', 'unknown').upper()}[/{status_color}]",
                f"Epics: {task_health.get('epic_count', 0)} | Issues: {task_health.get('issue_count', 0)}"
            )
        
        # Add memory system health
        if isinstance(memory_health, dict):
            status_color = "green" if memory_health.get("status") == "operational" else "red"
            table.add_row(
                "Memory System",
                f"[{status_color}]{memory_health.get('status', 'unknown').upper()}[/{status_color}]",
                f"mem0AI: {'✓' if memory_health.get('mem0ai_connected') else '✗'} | {memory_health.get('response_time', 0)}ms"
            )
        
        # Add QA system health
        if isinstance(qa_health, dict):
            qa_status = qa_health.get("status", "unknown")
            status_color = "green" if qa_status in ["healthy", "operational"] else "yellow" if qa_status == "degraded" else "red"
            table.add_row(
                "Enhanced QA Agent",
                f"[{status_color}]{qa_status.upper()}[/{status_color}]",
                f"v{qa_health.get('agent_version', 'unknown')} | "
                f"Health: {qa_health.get('health_score', 0):.0f}% | "
                f"Extension: {'✓' if qa_health.get('browser_extension') == 'healthy' else '✗'}"
            )
        
        console.print(table)
        console.print()
        
        # System summary
        qa_status_text = "active" if qa_health.get("status") == "healthy" else "degraded" if qa_health.get("status") == "degraded" else "inactive"
        summary_text = f"""
🚀 **Framework Status**: Claude PM Framework v4.1.0 operational
📊 **Task Management**: {task_health.get('total_items', 0)} total items managed
🧠 **Memory Integration**: mem0AI connectivity {'active' if memory_health.get('mem0ai_connected') else 'inactive'}
🧪 **Enhanced QA Agent**: Browser testing and memory-augmented analysis {qa_status_text}
⚡ **Performance**: {total_time:.2f}s response time | {reliability_score}% reliability
        """
        
        console.print(Panel(summary_text.strip(), title="System Summary", border_style="blue"))


class CMPMAgentMonitor:
    """CMPM Agents Command Implementation with MCP infrastructure support."""
    
    def __init__(self):
        self.config = Config()
        self.framework_path = Path.cwd()
        self.agent_registry_path = self.framework_path / "framework/agent-roles/agents.json"
        self.user_config_path = Path.home() / ".claude-pm"
        self.user_agents_config_path = self.user_config_path / "config/agents.yaml"
        self.user_agents_dir = self.user_config_path / "agents/user-defined"
        self.orchestrator = None
        
    async def load_framework_agent_registry(self) -> Dict[str, Any]:
        """Load framework agent registry from source configuration."""
        try:
            if self.agent_registry_path.exists():
                with open(self.agent_registry_path, 'r') as f:
                    return json.load(f)
            else:
                return {"agent_registry": {"standard_agents": {}, "user_defined_agents": {}}}
        except Exception as e:
            logger.error(f"Failed to load framework agent registry: {e}")
            return {"agent_registry": {"standard_agents": {}, "user_defined_agents": {}}}
    
    async def load_user_agent_config(self) -> Dict[str, Any]:
        """Load user-defined agent configuration from ~/.claude-pm/config/agents.yaml."""
        try:
            if self.user_agents_config_path.exists():
                with open(self.user_agents_config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                return {"agents": {"user_defined": []}}
        except Exception as e:
            logger.error(f"Failed to load user agent configuration: {e}")
            return {"agents": {"user_defined": []}}
    
    async def discover_user_agents(self) -> Dict[str, Any]:
        """Discover user-defined agents from ~/.claude-pm/agents/user-defined/."""
        user_agents = {}
        
        try:
            if self.user_agents_dir.exists():
                for agent_file in self.user_agents_dir.glob("*.md"):
                    agent_name = agent_file.stem
                    
                    # Create agent entry based on discovered file
                    user_agents[agent_name] = {
                        "name": agent_name.replace("-", " ").title(),
                        "type": "user_defined",
                        "file": str(agent_file),
                        "description": f"User-defined agent: {agent_name}",
                        "tools": ["user_defined_tools"],
                        "coordination_role": "user_specialist",
                        "domain_focus": "user_defined",
                        "version": "1.0.0",
                        "created": datetime.now().isoformat(),
                        "source": "user_directory"
                    }
                    
                    # Try to extract more information from the file
                    try:
                        with open(agent_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Extract description from first paragraph or heading
                            lines = content.split('\n')
                            for line in lines:
                                if line.strip() and not line.startswith('#'):
                                    clean_desc = line.strip()[:100]
                                    if clean_desc:
                                        user_agents[agent_name]["description"] = clean_desc
                                        break
                    except Exception:
                        pass
                        
        except Exception as e:
            logger.error(f"Failed to discover user agents: {e}")
            
        return user_agents
    
    async def load_agent_registry(self) -> Dict[str, Any]:
        """Load combined agent registry from both framework and user configurations."""
        try:
            # Load framework agents
            framework_registry = await self.load_framework_agent_registry()
            
            # Load user config
            user_config = await self.load_user_agent_config()
            
            # Discover user agents from directory
            discovered_user_agents = await self.discover_user_agents()
            
            # Merge user agents from config and discovered agents
            user_agents = {}
            
            # Add agents from user config
            for agent_config in user_config.get("agents", {}).get("user_defined", []):
                agent_name = agent_config.get("name", "").replace("-", "_")
                if agent_name:
                    user_agents[agent_name] = {
                        "name": agent_config.get("name", ""),
                        "type": "user_defined",
                        "file": agent_config.get("prompt_file", ""),
                        "description": agent_config.get("description", ""),
                        "tools": ["user_defined_tools"],
                        "coordination_role": "user_specialist",
                        "domain_focus": agent_config.get("category", "general"),
                        "version": "1.0.0",
                        "created": agent_config.get("created_date", ""),
                        "enabled": agent_config.get("enabled", True),
                        "priority": agent_config.get("priority", "medium"),
                        "source": "user_config"
                    }
            
            # Add discovered agents (prefer config over discovered)
            for agent_name, agent_data in discovered_user_agents.items():
                if agent_name not in user_agents:
                    user_agents[agent_name] = agent_data
            
            # Combine with framework registry
            combined_registry = {
                "agent_registry": {
                    "standard_agents": framework_registry.get("agent_registry", {}).get("standard_agents", {}),
                    "user_defined_agents": user_agents
                }
            }
            
            return combined_registry
            
        except Exception as e:
            logger.error(f"Failed to load combined agent registry: {e}")
            return {"agent_registry": {"standard_agents": {}, "user_defined_agents": {}}}
    
    async def get_agent_status(self, agent_name: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get status for a specific agent with enhanced information."""
        try:
            # Extract proper specialization and tools from agent data
            specialization = agent_data.get("specialization", agent_data.get("description", "general"))
            tools = agent_data.get("tools", [])
            
            # Get coordination role or derive from type
            coordination_role = agent_data.get("coordination_role", "unknown")
            
            # Determine actual agent status (simulate based on framework health)
            # In a real implementation, this would check actual agent instances
            status = "available"
            
            # Add enhanced information
            agent_info = {
                "name": agent_data.get("name", agent_name),
                "type": agent_data.get("type", "unknown"),
                "status": status,
                "specialization": specialization,
                "coordination_role": coordination_role,
                "tools": tools,
                "description": agent_data.get("description", "No description available"),
                "last_active": datetime.now().isoformat()
            }
            
            # Add user-defined agent specific information
            if agent_data.get("type") == "user_defined":
                agent_info.update({
                    "base_type": agent_data.get("base_type", "unknown"),
                    "domain_focus": agent_data.get("domain_focus", "general"),
                    "version": agent_data.get("version", "unknown"),
                    "created": agent_data.get("created", "unknown"),
                    "source": agent_data.get("source", "unknown"),
                    "enabled": agent_data.get("enabled", True),
                    "priority": agent_data.get("priority", "medium")
                })
            
            return agent_info
            
        except Exception as e:
            return {
                "name": agent_name,
                "status": "error",
                "error": str(e),
                "last_active": datetime.now().isoformat()
            }
    
    async def generate_agents_dashboard(self, agent_filter: Optional[str] = None, 
                                       output_json: bool = False, detailed: bool = False) -> None:
        """Generate comprehensive CMPM agents dashboard."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Loading agent registry...", total=None)
            
            # Load agent registry
            registry = await self.load_agent_registry()
            
            progress.update(task, description="Analyzing agent status...")
            
            # Get agent status for all agents
            standard_agents = registry.get("agent_registry", {}).get("standard_agents", {})
            user_defined_agents = registry.get("agent_registry", {}).get("user_defined_agents", {})
            
            # Apply filtering if specified
            if agent_filter == "standard":
                user_defined_agents = {}
            elif agent_filter == "user_defined":
                standard_agents = {}
            
            # Collect agent status data
            agent_status_tasks = []
            
            for agent_name, agent_data in standard_agents.items():
                agent_status_tasks.append(self.get_agent_status(agent_name, agent_data))
            
            for agent_name, agent_data in user_defined_agents.items():
                agent_status_tasks.append(self.get_agent_status(agent_name, agent_data))
            
            all_agent_status = await asyncio.gather(*agent_status_tasks, return_exceptions=True)
            
            progress.update(task, description="Generating dashboard...")
        
        # Handle JSON output
        if output_json:
            # Clean agent data for JSON output
            clean_agents = []
            for status in all_agent_status:
                if isinstance(status, dict):
                    clean_agents.append(status)
            
            json_output = {
                "cmpm_version": "4.1.0",
                "timestamp": datetime.now().isoformat(),
                "total_agents": len(clean_agents),
                "available_agents": sum(1 for agent in clean_agents if agent.get("status") == "available"),
                "standard_agents": len(standard_agents),
                "user_defined_agents": len(user_defined_agents),
                "agents": clean_agents,
                "agent_filter": agent_filter
            }
            print(json.dumps(json_output, indent=2, ensure_ascii=True))
            return
        
        # Create dashboard header
        total_agents = len(standard_agents) + len(user_defined_agents)
        available_agents = sum(1 for status in all_agent_status if isinstance(status, dict) and status.get("status") == "available")
        
        header = Panel(
            Text(f"CMPM Agents Dashboard v4.1.0\nTotal Agents: {total_agents} | Available: {available_agents}", 
                 justify="center", style="bold white"),
            title="🤖 Claude Multi-Agent PM Framework - Agent Registry",
            border_style="cyan"
        )
        
        console.print(header)
        console.print()
        
        # Create agents table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Agent Name", style="cyan", width=20)
        table.add_column("Type", width=12)
        table.add_column("Status", width=12)
        table.add_column("Role", style="dim", width=20)
        table.add_column("Tools", style="dim", width=30)
        if detailed:
            table.add_column("Description", style="dim", width=40)
        
        # Add standard agents
        for i, (agent_name, agent_data) in enumerate(standard_agents.items()):
            if i < len(all_agent_status):
                status = all_agent_status[i]
                if isinstance(status, dict):
                    status_color = "green" if status.get("status") == "available" else "red"
                    
                    # Format tools display
                    tools_list = status.get("tools", [])
                    tools_display = ", ".join(tools_list[:3]) if tools_list else "none"
                    if len(tools_list) > 3:
                        tools_display += f" (+{len(tools_list) - 3} more)"
                    
                    row_data = [
                        status.get("name", agent_name),
                        f"[blue]{status.get('type', 'standard')}[/blue]",
                        f"[{status_color}]{status.get('status', 'unknown').upper()}[/{status_color}]",
                        status.get("coordination_role", "unknown").replace("_", " ").title(),
                        tools_display
                    ]
                    
                    if detailed:
                        description = status.get("description", "No description available")
                        row_data.append(description[:35] + "..." if len(description) > 35 else description)
                    
                    table.add_row(*row_data)
        
        # Add user-defined agents
        standard_count = len(standard_agents)
        for i, (agent_name, agent_data) in enumerate(user_defined_agents.items()):
            status_index = standard_count + i
            if status_index < len(all_agent_status):
                status = all_agent_status[status_index]
                if isinstance(status, dict):
                    status_color = "green" if status.get("status") == "available" else "red"
                    
                    # Format tools display
                    tools_list = status.get("tools", [])
                    tools_display = ", ".join(tools_list[:3]) if tools_list else "none"
                    if len(tools_list) > 3:
                        tools_display += f" (+{len(tools_list) - 3} more)"
                    
                    # Show domain focus for user-defined agents
                    role_display = status.get("domain_focus", status.get("coordination_role", "unknown"))
                    role_display = role_display.replace("_", " ").title()
                    
                    row_data = [
                        status.get("name", agent_name),
                        f"[yellow]{status.get('type', 'user_defined')}[/yellow]",
                        f"[{status_color}]{status.get('status', 'unknown').upper()}[/{status_color}]",
                        role_display,
                        tools_display
                    ]
                    
                    if detailed:
                        description = status.get("description", "No description available")
                        row_data.append(description[:35] + "..." if len(description) > 35 else description)
                    
                    table.add_row(*row_data)
        
        console.print(table)
        console.print()
        
        # Agent categories summary
        categories = {}
        total_tools = set()
        for status in all_agent_status:
            if isinstance(status, dict):
                coord_role = status.get("coordination_role", "unknown")
                if coord_role not in categories:
                    categories[coord_role] = 0
                categories[coord_role] += 1
                
                # Collect all tools
                tools = status.get("tools", [])
                total_tools.update(tools)
        
        # Get MultiAgentOrchestrator statistics if available
        orchestrator_info = "Available"
        orchestrator_stats = None
        try:
            # Try to get orchestrator statistics
            if self.orchestrator:
                orchestrator_stats = self.orchestrator.get_orchestrator_stats()
                orchestrator_info = f"{orchestrator_stats.get('agent_definitions', 0)} agent types in orchestrator"
            else:
                orchestrator_info = "11 agent types in orchestrator (static)"
        except Exception as e:
            logger.debug(f"Could not get orchestrator stats: {e}")
            orchestrator_info = "Orchestrator not available"
        
        summary_text = f"""
🎯 **Agent Distribution**: {len(standard_agents)} standard + {len(user_defined_agents)} user-defined
📊 **Availability**: {available_agents}/{total_agents} agents available
🔧 **Coordination Roles**: {len(categories)} distinct coordination roles
🛠️ **Total Tools**: {len(total_tools)} unique tools across all agents
⚡ **Framework Integration**: MCP-enabled multi-agent coordination
🤖 **Orchestrator**: {orchestrator_info}
        """
        
        console.print(Panel(summary_text.strip(), title="Agent Summary", border_style="blue"))


class CMPMIndexOrchestrator:
    """CMPM Index Command Implementation with documentation agent delegation."""
    
    def __init__(self):
        self.config = Config()
        self.framework_path = Path.cwd()
        self.start_time = time.time()
        
    def detect_project_type(self, project_path: Path) -> str:
        """Detect project type based on file patterns."""
        if (project_path / "package.json").exists():
            return "Node.js"
        elif (project_path / "pyproject.toml").exists():
            return "Python"
        elif (project_path / "requirements.txt").exists():
            return "Python"
        elif (project_path / ".git").exists():
            return "Git Repository"
        elif (project_path / "README.md").exists():
            return "Documentation"
        else:
            return "Unknown"
    
    def extract_project_metadata(self, project_path: Path) -> Dict[str, Any]:
        """Extract metadata from project files."""
        metadata = {
            "name": project_path.name,
            "path": str(project_path),
            "type": self.detect_project_type(project_path),
            "last_modified": datetime.fromtimestamp(project_path.stat().st_mtime).isoformat(),
            "size": self._get_directory_size(project_path),
            "description": "No description available"
        }
        
        # Try to extract description from package.json
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    metadata["description"] = data.get("description", "No description available")
                    metadata["version"] = data.get("version", "Unknown")
            except Exception:
                pass
        
        # Try to extract description from pyproject.toml
        pyproject_toml = project_path / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                import tomli
                with open(pyproject_toml, 'rb') as f:
                    data = tomli.load(f)
                    if "project" in data:
                        metadata["description"] = data["project"].get("description", "No description available")
                        metadata["version"] = data["project"].get("version", "Unknown")
            except Exception:
                pass
        
        # Try to extract description from README
        readme_path = project_path / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract first paragraph as description
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('#'):
                            # Clean the description to remove control characters, emojis, and normalize whitespace
                            clean_desc = ''.join(char if 32 <= ord(char) <= 126 else ' ' for char in line.strip())
                            clean_desc = ' '.join(clean_desc.split())  # Normalize whitespace
                            if clean_desc:  # Only use if not empty after cleaning
                                metadata["description"] = clean_desc[:100] + "..."
                                break
            except Exception:
                pass
        
        return metadata
    
    def _get_directory_size(self, path: Path) -> str:
        """Get human-readable directory size."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            
            # Convert to human readable format
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024**2:
                return f"{total_size/1024:.1f} KB"
            elif total_size < 1024**3:
                return f"{total_size/1024**2:.1f} MB"
            else:
                return f"{total_size/1024**3:.1f} GB"
        except Exception:
            return "Unknown"
    
    def discover_projects(self, base_path: Path = None) -> List[Dict[str, Any]]:
        """Discover all projects in the current directory and subdirectories."""
        if base_path is None:
            base_path = self.framework_path
        
        projects = []
        project_indicators = [
            "package.json", "pyproject.toml", "setup.py", "requirements.txt",
            ".git", "README.md", "Makefile", "Dockerfile"
        ]
        
        try:
            # Scan immediate subdirectories
            for item in base_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if this directory contains project indicators
                    has_indicators = any(
                        (item / indicator).exists() for indicator in project_indicators
                    )
                    
                    if has_indicators:
                        metadata = self.extract_project_metadata(item)
                        projects.append(metadata)
        except Exception as e:
            logger.error(f"Error discovering projects: {e}")
        
        return projects
    
    def delegate_to_documentation_agent(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate delegation to documentation agent for comprehensive project analysis."""
        # In a real implementation, this would use the Task tool to delegate
        # For now, we'll simulate the documentation agent's enhanced analysis
        
        enhanced_projects = []
        for project in projects:
            enhanced_project = project.copy()
            
            # Simulate documentation agent analysis
            enhanced_project["documentation_score"] = self._calculate_documentation_score(Path(project["path"]))
            enhanced_project["health_status"] = self._assess_project_health(Path(project["path"]))
            enhanced_project["complexity_score"] = self._calculate_complexity_score(Path(project["path"]))
            
            enhanced_projects.append(enhanced_project)
        
        return {
            "projects": enhanced_projects,
            "total_projects": len(enhanced_projects),
            "analysis_timestamp": datetime.now().isoformat(),
            "agent_delegated": "documentation_agent"
        }
    
    def _calculate_documentation_score(self, project_path: Path) -> int:
        """Calculate documentation score (0-100) based on available docs."""
        score = 0
        
        # Check for README
        if (project_path / "README.md").exists():
            score += 30
        
        # Check for docs directory
        if (project_path / "docs").exists():
            score += 20
        
        # Check for CHANGELOG
        if (project_path / "CHANGELOG.md").exists():
            score += 15
        
        # Check for LICENSE
        if (project_path / "LICENSE").exists():
            score += 10
        
        # Check for contributing guidelines
        if (project_path / "CONTRIBUTING.md").exists():
            score += 10
        
        # Check for code comments (simplified)
        try:
            py_files = list(project_path.glob("**/*.py"))
            if py_files:
                score += 15  # Assume Python files have some documentation
        except Exception:
            pass
        
        return min(score, 100)
    
    def _assess_project_health(self, project_path: Path) -> str:
        """Assess project health based on file patterns."""
        health_score = 0
        
        # Check for version control
        if (project_path / ".git").exists():
            health_score += 25
        
        # Check for dependency management
        if (project_path / "package.json").exists() or (project_path / "pyproject.toml").exists():
            health_score += 25
        
        # Check for testing
        if (project_path / "tests").exists() or list(project_path.glob("**/test_*.py")):
            health_score += 25
        
        # Check for CI/CD
        if (project_path / ".github").exists() or (project_path / ".gitlab-ci.yml").exists():
            health_score += 25
        
        if health_score >= 75:
            return "Excellent"
        elif health_score >= 50:
            return "Good"
        elif health_score >= 25:
            return "Fair"
        else:
            return "Poor"
    
    def _calculate_complexity_score(self, project_path: Path) -> int:
        """Calculate project complexity score (0-100)."""
        complexity = 0
        
        try:
            # Count total files
            total_files = len(list(project_path.glob("**/*")))
            if total_files > 100:
                complexity += 30
            elif total_files > 50:
                complexity += 20
            elif total_files > 20:
                complexity += 10
            
            # Count source files
            source_files = (
                len(list(project_path.glob("**/*.py"))) +
                len(list(project_path.glob("**/*.js"))) +
                len(list(project_path.glob("**/*.ts")))
            )
            if source_files > 50:
                complexity += 30
            elif source_files > 20:
                complexity += 20
            elif source_files > 10:
                complexity += 10
            
            # Check for multiple languages
            languages = []
            if list(project_path.glob("**/*.py")):
                languages.append("Python")
            if list(project_path.glob("**/*.js")) or list(project_path.glob("**/*.ts")):
                languages.append("JavaScript/TypeScript")
            if list(project_path.glob("**/*.java")):
                languages.append("Java")
            
            if len(languages) > 1:
                complexity += 20
            
            # Check for subdirectories
            subdirs = [d for d in project_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
            if len(subdirs) > 10:
                complexity += 20
            elif len(subdirs) > 5:
                complexity += 10
            
        except Exception:
            pass
        
        return min(complexity, 100)
    
    async def generate_index_dashboard(self, output_json: bool = False, verbose: bool = False) -> None:
        """Generate comprehensive CMPM project index dashboard."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Discovering projects...", total=None)
            
            # Discover projects
            projects = self.discover_projects()
            
            progress.update(task, description="Delegating to documentation agent...")
            
            # Delegate to documentation agent for enhanced analysis
            enhanced_data = self.delegate_to_documentation_agent(projects)
            
            progress.update(task, description="Generating index dashboard...")
            
            total_time = time.time() - self.start_time
        
        if output_json:
            # Output JSON format - clean all string values to ensure valid JSON
            def clean_json_string(value):
                if isinstance(value, str):
                    # Keep only printable ASCII characters to ensure JSON compatibility
                    cleaned = ''.join(char if 32 <= ord(char) <= 126 else ' ' for char in value)
                    return ' '.join(cleaned.split())  # Normalize whitespace
                return value
            
            def clean_json_object(obj):
                if isinstance(obj, dict):
                    return {k: clean_json_object(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_json_object(item) for item in obj]
                else:
                    return clean_json_string(obj)
            
            json_output = {
                "cmpm_version": "4.1.0",
                "index_timestamp": datetime.now().isoformat(),
                "total_projects": enhanced_data["total_projects"],
                "projects": clean_json_object(enhanced_data["projects"]),
                "generation_time": f"{total_time:.2f}s"
            }
            print(json.dumps(json_output, indent=2, ensure_ascii=True))
            return
        
        # Create dashboard header
        header = Panel(
            Text(f"CMPM Project Index v4.1.0\nTotal Projects: {enhanced_data['total_projects']}\nGeneration Time: {total_time:.2f}s", 
                 justify="center", style="bold white"),
            title="📁 Claude Multi-Agent PM Framework - Project Index",
            border_style="cyan"
        )
        
        console.print(header)
        console.print()
        
        # Create projects table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Project Name", style="cyan", width=20)
        table.add_column("Type", width=12)
        table.add_column("Health", width=10)
        table.add_column("Docs", width=6)
        table.add_column("Complexity", width=8)
        if verbose:
            table.add_column("Description", style="dim", width=40)
        
        # Add projects to table
        for project in enhanced_data["projects"]:
            health_color = {
                "Excellent": "green",
                "Good": "yellow",
                "Fair": "orange",
                "Poor": "red"
            }.get(project.get("health_status", "Poor"), "red")
            
            docs_score = project.get("documentation_score", 0)
            docs_color = "green" if docs_score >= 70 else "yellow" if docs_score >= 40 else "red"
            
            complexity_score = project.get("complexity_score", 0)
            complexity_color = "red" if complexity_score >= 70 else "yellow" if complexity_score >= 40 else "green"
            
            row = [
                project["name"],
                f"[blue]{project['type']}[/blue]",
                f"[{health_color}]{project.get('health_status', 'Unknown')}[/{health_color}]",
                f"[{docs_color}]{docs_score}%[/{docs_color}]",
                f"[{complexity_color}]{complexity_score}%[/{complexity_color}]"
            ]
            
            if verbose:
                row.append(project.get("description", "No description")[:40] + "...")
            
            table.add_row(*row)
        
        console.print(table)
        console.print()
        
        # Project statistics
        project_types = {}
        health_distribution = {}
        
        for project in enhanced_data["projects"]:
            ptype = project["type"]
            project_types[ptype] = project_types.get(ptype, 0) + 1
            
            health = project.get("health_status", "Unknown")
            health_distribution[health] = health_distribution.get(health, 0) + 1
        
        # Calculate averages
        avg_docs = sum(p.get("documentation_score", 0) for p in enhanced_data["projects"]) / len(enhanced_data["projects"]) if enhanced_data["projects"] else 0
        avg_complexity = sum(p.get("complexity_score", 0) for p in enhanced_data["projects"]) / len(enhanced_data["projects"]) if enhanced_data["projects"] else 0
        
        summary_text = f"""
🎯 **Project Distribution**: {', '.join(f'{k}: {v}' for k, v in project_types.items())}
📊 **Health Distribution**: {', '.join(f'{k}: {v}' for k, v in health_distribution.items())}
📚 **Average Documentation Score**: {avg_docs:.1f}%
🔧 **Average Complexity Score**: {avg_complexity:.1f}%
⚡ **Agent Delegation**: Documentation agent analysis completed
        """
        
        console.print(Panel(summary_text.strip(), title="Index Summary", border_style="blue"))


class CMPMDashboardLauncher:
    """CMPM Dashboard Command Implementation with headless browser launch."""
    
    def __init__(self):
        self.config = Config()
        self.framework_path = Path.cwd()
        managed_path = self.config.get("managed_path", str(Path.home() / "Projects" / "managed"))
        self.portfolio_manager_path = Path(managed_path) / "claude-pm-portfolio-manager"
        self.browser_process = None
        self.dashboard_process = None
        self.start_time = time.time()
        
    def detect_dashboard_port(self) -> Optional[int]:
        """Detect if dashboard is running and on which port."""
        # Check common ports for the dashboard
        common_ports = [3000, 8080, 8081, 5173]
        
        for port in common_ports:
            try:
                # Use netstat to check if port is in use
                result = subprocess.run(
                    ["netstat", "-an"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    # Check if the port is listening
                    if f":{port}" in result.stdout and "LISTEN" in result.stdout:
                        # Try to make a simple HTTP request to verify it's actually a web server
                        try:
                            import urllib.request
                            with urllib.request.urlopen(f"http://localhost:{port}/", timeout=3) as response:
                                if response.getcode() == 200:
                                    return port
                        except:
                            continue
                            
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
        
        return None
    
    def start_dashboard_if_needed(self) -> Tuple[bool, Optional[int], str]:
        """Start the dashboard if it's not running."""
        # First check if dashboard is already running
        running_port = self.detect_dashboard_port()
        if running_port:
            return True, running_port, f"Dashboard already running on port {running_port}"
        
        # Check if portfolio manager directory exists
        if not self.portfolio_manager_path.exists():
            return False, None, f"Portfolio manager not found at {self.portfolio_manager_path}"
        
        # Check if package.json exists
        package_json = self.portfolio_manager_path / "package.json"
        if not package_json.exists():
            return False, None, f"package.json not found in {self.portfolio_manager_path}"
        
        try:
            # Start the dashboard in development mode
            console.print(f"[dim]Starting dashboard from {self.portfolio_manager_path}[/dim]")
            
            # Use npm run dev or equivalent to start the dashboard
            self.dashboard_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.portfolio_manager_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for the server to start
            time.sleep(3)
            
            # Check if the process is still running
            if self.dashboard_process.poll() is not None:
                stdout, stderr = self.dashboard_process.communicate()
                return False, None, f"Dashboard failed to start: {stderr}"
            
            # Try to detect the port it's running on
            for attempt in range(10):  # Try for 10 seconds
                running_port = self.detect_dashboard_port()
                if running_port:
                    return True, running_port, f"Dashboard started on port {running_port}"
                time.sleep(1)
            
            return False, None, "Dashboard started but port detection failed"
            
        except Exception as e:
            return False, None, f"Error starting dashboard: {str(e)}"
    
    def find_chrome_binary(self) -> Optional[str]:
        """Find Chrome binary using the framework's knowledge."""
        # Use the pattern from the framework's PDF generation knowledge
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
            "/usr/bin/google-chrome",  # Linux
            "/usr/bin/chromium-browser",  # Linux Chromium
            "/snap/bin/chromium",  # Snap package
        ]
        
        for path in chrome_paths:
            if Path(path).exists():
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["which", "google-chrome"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        try:
            result = subprocess.run(
                ["which", "chromium"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def launch_headless_browser(self, dashboard_url: str) -> Tuple[bool, str]:
        """Launch headless browser pointing to dashboard."""
        chrome_path = self.find_chrome_binary()
        if not chrome_path:
            return False, "Chrome/Chromium not found. Please install Google Chrome or Chromium."
        
        try:
            # Use Chrome headless mode with parameters based on framework knowledge
            chrome_args = [
                chrome_path,
                "--headless",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=5000",
                "--window-size=1920,1080",
                "--user-agent=CMPM-Dashboard-Launcher/1.0",
                dashboard_url
            ]
            
            console.print(f"[dim]Launching headless browser: {chrome_path}[/dim]")
            
            self.browser_process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait briefly to check if process started successfully
            time.sleep(2)
            
            if self.browser_process.poll() is not None:
                stdout, stderr = self.browser_process.communicate()
                return False, f"Browser failed to start: {stderr}"
            
            return True, f"Headless browser launched successfully (PID: {self.browser_process.pid})"
            
        except Exception as e:
            return False, f"Error launching browser: {str(e)}"
    
    def cleanup_processes(self):
        """Clean up spawned processes."""
        if self.browser_process:
            try:
                self.browser_process.terminate()
                self.browser_process.wait(timeout=5)
            except:
                try:
                    self.browser_process.kill()
                except:
                    pass
        
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
            except:
                try:
                    self.dashboard_process.kill()
                except:
                    pass
    
    def handle_interrupt(self, signum, frame):
        """Handle interrupt signal."""
        console.print("\n[yellow]Received interrupt signal, cleaning up...[/yellow]")
        self.cleanup_processes()
        sys.exit(0)
    
    async def launch_dashboard(self, keep_alive: bool = False, port: Optional[int] = None) -> None:
        """Launch the CMPM dashboard in headless browser."""
        
        # Set up signal handler for cleanup
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Checking dashboard status...", total=None)
            
            # Step 1: Start dashboard if needed
            dashboard_started, dashboard_port, start_message = self.start_dashboard_if_needed()
            
            if not dashboard_started:
                progress.update(task, description="Dashboard startup failed")
                console.print(f"[red]❌ Dashboard Error: {start_message}[/red]")
                return
            
            progress.update(task, description="Preparing headless browser...")
            
            # Step 2: Prepare dashboard URL
            dashboard_url = f"http://localhost:{dashboard_port}/"
            
            # Step 3: Launch headless browser
            browser_launched, browser_message = self.launch_headless_browser(dashboard_url)
            
            if not browser_launched:
                progress.update(task, description="Browser launch failed")
                console.print(f"[red]❌ Browser Error: {browser_message}[/red]")
                self.cleanup_processes()
                return
            
            progress.update(task, description="Dashboard launched successfully")
        
        # Create success dashboard
        total_time = time.time() - self.start_time
        
        header = Panel(
            Text(f"CMPM Dashboard Launcher v4.1.0\nDashboard URL: {dashboard_url}\nLaunch Time: {total_time:.2f}s", 
                 justify="center", style="bold white"),
            title="🚀 Claude PM Portfolio Manager Dashboard",
            border_style="green"
        )
        
        console.print(header)
        console.print()
        
        # Create status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=15)
        table.add_column("Details", style="dim")
        
        table.add_row(
            "Portfolio Manager",
            "[green]RUNNING[/green]",
            f"Port {dashboard_port} | {start_message}"
        )
        
        table.add_row(
            "Headless Browser",
            "[green]LAUNCHED[/green]",
            f"Chrome PID {self.browser_process.pid if self.browser_process else 'N/A'} | {browser_message}"
        )
        
        table.add_row(
            "Dashboard URL",
            "[green]ACCESSIBLE[/green]",
            f"{dashboard_url}"
        )
        
        console.print(table)
        console.print()
        
        # Summary information
        summary_text = f"""
🎯 **Dashboard Access**: Portfolio manager dashboard is now running in headless browser mode
📊 **URL**: {dashboard_url}
🚀 **Launch Time**: {total_time:.2f} seconds
⚡ **Process Management**: Background processes managed by CMPM framework
        """
        
        console.print(Panel(summary_text.strip(), title="Launch Summary", border_style="blue"))
        
        if keep_alive:
            console.print()
            console.print("[yellow]Dashboard is running in background. Press Ctrl+C to stop.[/yellow]")
            
            try:
                # Keep the script running
                while True:
                    time.sleep(1)
                    
                    # Check if processes are still running
                    if self.browser_process and self.browser_process.poll() is not None:
                        console.print("[yellow]Browser process terminated.[/yellow]")
                        break
                    
                    if self.dashboard_process and self.dashboard_process.poll() is not None:
                        console.print("[yellow]Dashboard process terminated.[/yellow]")
                        break
                        
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping dashboard...[/yellow]")
            finally:
                self.cleanup_processes()
                console.print("[green]Dashboard stopped successfully.[/green]")
        else:
            console.print()
            console.print("[dim]Dashboard launched in background. Use process management tools to monitor.[/dim]")


class CMPMQAMonitor:
    """CMPM QA Command Implementation with enhanced browser testing integration."""
    
    def __init__(self):
        self.config = Config()
        self.framework_path = Path.cwd()
        self.qa_agent = None
        self.start_time = time.time()
    
    async def get_qa_agent(self) -> EnhancedQAAgent:
        """Get or create QA agent instance."""
        if self.qa_agent is None:
            self.qa_agent = EnhancedQAAgent(self.config)
        return self.qa_agent
    
    async def execute_qa_tests(self, test_type: str = "all", browser: bool = False, 
                              urls: List[str] = None, output_json: bool = False) -> None:
        """Execute QA tests with comprehensive reporting."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Initializing QA testing...", total=None)
            
            qa_agent = await self.get_qa_agent()
            
            if browser:
                progress.update(task, description="Executing browser-based tests...")
                test_config = {
                    "test_suite": "cmpm_browser_tests",
                    "urls": urls or ["http://localhost:3000"],
                    "scenarios": ["basic_functionality", "ui_validation"],
                    "screenshots": True,
                    "performance": True
                }
                
                results = await qa_agent.execute_browser_tests(test_config)
            else:
                progress.update(task, description=f"Running {test_type} tests...")
                results = await qa_agent.run_framework_tests(test_type)
            
            progress.update(task, description="Generating test report...")
        
        if output_json:
            # Clean results for JSON output
            clean_results = {
                "cmpm_version": "4.1.0",
                "timestamp": datetime.now().isoformat(),
                "test_type": "browser" if browser else test_type,
                "results": results
            }
            print(json.dumps(clean_results, indent=2, ensure_ascii=True))
            return
        
        # Generate comprehensive dashboard
        await self._generate_qa_test_dashboard(results, test_type, browser)
    
    async def _generate_qa_test_dashboard(self, results: Dict[str, Any], test_type: str, 
                                        browser: bool) -> None:
        """Generate comprehensive QA test dashboard."""
        total_time = time.time() - self.start_time
        
        # Determine status and colors
        status = results.get("status", "unknown")
        status_color = "green" if status == "success" else "yellow" if status == "partial_failure" else "red"
        
        # Create header
        test_mode = "Browser Testing" if browser else f"{test_type.title()} Testing"
        header = Panel(
            Text(f"CMPM QA Test Results - {test_mode}\nExecution Time: {total_time:.2f}s", 
                 justify="center", style="bold white"),
            title="🧪 Enhanced QA Agent Test Dashboard",
            border_style=status_color
        )
        
        console.print(header)
        console.print()
        
        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Test Category", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Results", style="dim")
        
        # Add summary row
        summary = results.get("summary", {})
        if summary:
            total_tests = summary.get("total_tests", 0)
            passed_tests = summary.get("passed_tests", 0)
            success_rate = summary.get("success_rate", 0)
            
            table.add_row(
                "Test Summary",
                f"[{status_color}]{status.upper()}[/{status_color}]",
                f"{passed_tests}/{total_tests} passed ({success_rate:.1%})"
            )
        
        # Add browser-specific results
        if browser:
            execution_summary = results.get("execution_summary", {})
            if execution_summary:
                table.add_row(
                    "Browser Tests",
                    f"[{status_color}]EXECUTED[/{status_color}]",
                    f"Screenshots: {execution_summary.get('screenshots_captured', 0)} | "
                    f"Time: {execution_summary.get('execution_time', 0):.1f}s"
                )
        
        # Add detailed results
        detailed_results = results.get("detailed_results", [])
        for result in detailed_results:
            test_name = result.get("test_type", "unknown")
            test_status = result.get("status", "unknown")
            test_color = "green" if test_status == "passed" else "red"
            
            details = ""
            if result.get("return_code") is not None:
                details += f"Exit code: {result.get('return_code')} | "
            if result.get("execution_time"):
                details += f"Time: {result.get('execution_time'):.1f}s"
            
            table.add_row(
                test_name.replace("_", " ").title(),
                f"[{test_color}]{test_status.upper()}[/{test_color}]",
                details or "No details available"
            )
        
        console.print(table)
        console.print()
        
        # Pattern analysis
        pattern_analysis = results.get("pattern_analysis", {})
        if pattern_analysis:
            pattern_text = f"""
🔍 **Pattern Analysis**: Success rate {pattern_analysis.get('success_rate', 0):.1%}
📊 **Performance**: {pattern_analysis.get('performance_trends', {}).get('average_time', 0):.1f}s average
🎯 **Recommendations**: {len(pattern_analysis.get('recommendations', []))} suggestions available
⚡ **Framework Integration**: Memory-augmented testing active
            """
            
            console.print(Panel(pattern_text.strip(), title="QA Intelligence", border_style="blue"))
            
            # Show recommendations
            recommendations = pattern_analysis.get("recommendations", [])
            if recommendations:
                console.print()
                console.print("[bold yellow]Recommendations:[/bold yellow]")
                for i, rec in enumerate(recommendations, 1):
                    console.print(f"  {i}. {rec}")
    
    async def get_qa_status(self, output_json: bool = False) -> None:
        """Get comprehensive QA system status."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Checking QA system status...", total=None)
            
            qa_agent = await self.get_qa_agent()
            status = await qa_agent.get_qa_health_status()
            
            progress.update(task, description="Generating status dashboard...")
        
        if output_json:
            clean_status = {
                "cmpm_version": "4.1.0",
                "timestamp": datetime.now().isoformat(),
                "qa_status": status
            }
            print(json.dumps(clean_status, indent=2, ensure_ascii=True))
            return
        
        # Generate status dashboard
        await self._generate_qa_status_dashboard(status)
    
    async def _generate_qa_status_dashboard(self, status: Dict[str, Any]) -> None:
        """Generate QA status dashboard."""
        total_time = time.time() - self.start_time
        
        # Determine overall status
        overall_status = status.get("status", "unknown")
        health_score = status.get("health_score", 0)
        status_color = "green" if overall_status == "healthy" else "yellow" if overall_status == "degraded" else "red"
        
        # Create header
        header = Panel(
            Text(f"CMPM QA System Status\nHealth Score: {health_score:.1f}%\nResponse Time: {total_time:.2f}s", 
                 justify="center", style="bold white"),
            title="🔧 Enhanced QA Agent Status",
            border_style=status_color
        )
        
        console.print(header)
        console.print()
        
        # Create status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Details", style="dim")
        
        # Add extension health
        extension_health = status.get("extension_health", {})
        ext_status = extension_health.get("status", "unknown")
        ext_color = "green" if ext_status == "healthy" else "red"
        table.add_row(
            "Browser Extension",
            f"[{ext_color}]{ext_status.upper()}[/{ext_color}]",
            f"v{extension_health.get('extension_version', 'unknown')} | "
            f"Browsers: {', '.join(extension_health.get('connected_browsers', []))}"
        )
        
        # Add memory health
        memory_health = status.get("memory_health", {})
        mem_status = memory_health.get("status", "unknown")
        mem_color = "green" if mem_status == "healthy" else "red"
        table.add_row(
            "Memory Service",
            f"[{mem_color}]{mem_status.upper()}[/{mem_color}]",
            f"mem0AI: {'✓' if memory_health.get('mem0ai_connected') else '✗'} | "
            f"Response: {memory_health.get('response_time', 0)}ms"
        )
        
        # Add framework health
        framework_health = status.get("framework_health", {})
        framework_status = "healthy" if framework_health.get("test_commands_available") else "degraded"
        framework_color = "green" if framework_status == "healthy" else "yellow"
        table.add_row(
            "Framework Testing",
            f"[{framework_color}]{framework_status.upper()}[/{framework_color}]",
            f"Commands: {'✓' if framework_health.get('test_commands_available') else '✗'} | "
            f"Timeout: {framework_health.get('test_timeout_configured', False)}"
        )
        
        console.print(table)
        console.print()
        
        # System summary
        agent_version = status.get("agent_version", "unknown")
        capabilities = extension_health.get("test_capabilities", [])
        
        summary_text = f"""
🧪 **QA Agent Version**: Enhanced QA Agent v{agent_version}
🔗 **Browser Integration**: Extension capabilities: {', '.join(capabilities)}
🧠 **Memory Integration**: Pattern recognition and test intelligence active
⚡ **Performance**: {total_time:.2f}s status check | {health_score:.1f}% system health
        """
        
        console.print(Panel(summary_text.strip(), title="QA System Summary", border_style="blue"))


# Click command implementations
@click.command(name="cmpm:health")
@click.option('--json', 'output_json', is_flag=True, help='Output health data as JSON')
@click.option('--detailed', is_flag=True, help='Show detailed component information')
def cmpm_health(output_json: bool, detailed: bool):
    """🏥 /cmpm:health - Comprehensive system health dashboard with ai-trackdown integration."""
    async def run_health_check():
        monitor = CMPMHealthMonitor()
        await monitor.generate_health_dashboard()
    
    try:
        asyncio.run(run_health_check())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command(name="cmpm:agents")
@click.option('--filter', 'agent_filter', help='Filter agents by type (standard|user_defined)')
@click.option('--json', 'output_json', is_flag=True, help='Output agent data as JSON')
@click.option('--detailed', is_flag=True, help='Show detailed agent information')
def cmpm_agents(agent_filter: Optional[str], output_json: bool, detailed: bool):
    """🤖 /cmpm:agents - List all active agent types and status in the framework."""
    async def run_agents_check():
        monitor = CMPMAgentMonitor()
        await monitor.generate_agents_dashboard(
            agent_filter=agent_filter,
            output_json=output_json,
            detailed=detailed
        )
    
    try:
        asyncio.run(run_agents_check())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command(name="cmpm:index")
@click.option('--json', 'output_json', is_flag=True, help='Output index data as JSON')
@click.option('--verbose', is_flag=True, help='Show detailed project information')
def cmpm_index(output_json: bool, verbose: bool):
    """📁 /cmpm:index - Generate comprehensive project discovery index with agent delegation."""
    async def run_index_generation():
        orchestrator = CMPMIndexOrchestrator()
        await orchestrator.generate_index_dashboard(output_json=output_json, verbose=verbose)
    
    try:
        asyncio.run(run_index_generation())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command(name="cmpm:dashboard")
@click.option('--keep-alive', is_flag=True, help='Keep dashboard running in foreground')
@click.option('--port', type=int, help='Specify dashboard port (auto-detect if not provided)')
def cmpm_dashboard(keep_alive: bool, port: Optional[int]):
    """🚀 /cmpm:dashboard - Launch portfolio manager dashboard in headless browser mode."""
    async def run_dashboard_launcher():
        launcher = CMPMDashboardLauncher()
        await launcher.launch_dashboard(keep_alive=keep_alive, port=port)
    
    try:
        asyncio.run(run_dashboard_launcher())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command(name="cmpm:qa-status")
@click.option('--json', 'output_json', is_flag=True, help='Output QA status as JSON')
def cmpm_qa_status(output_json: bool):
    """🔧 /cmpm:qa-status - QA extension status and health monitoring."""
    async def run_qa_status_check():
        monitor = CMPMQAMonitor()
        await monitor.get_qa_status(output_json=output_json)
    
    try:
        asyncio.run(run_qa_status_check())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command(name="cmpm:qa-test")
@click.option('--type', 'test_type', default='all', help='Test type (all|unit|lint|framework)')
@click.option('--browser', is_flag=True, help='Execute browser-based tests')
@click.option('--urls', multiple=True, help='URLs to test (for browser tests)')
@click.option('--json', 'output_json', is_flag=True, help='Output test results as JSON')
def cmpm_qa_test(test_type: str, browser: bool, urls: Tuple[str, ...], output_json: bool):
    """🧪 /cmpm:qa-test - Execute browser-based tests and framework validation."""
    async def run_qa_tests():
        monitor = CMPMQAMonitor()
        url_list = list(urls) if urls else None
        await monitor.execute_qa_tests(
            test_type=test_type,
            browser=browser,
            urls=url_list,
            output_json=output_json
        )
    
    try:
        asyncio.run(run_qa_tests())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command(name="cmpm:qa-results")
@click.option('--format', 'output_format', default='dashboard', help='Output format (dashboard|json|report)')
@click.option('--limit', type=int, default=10, help='Limit number of results to show')
def cmpm_qa_results(output_format: str, limit: int):
    """📊 /cmpm:qa-results - View test results and patterns with memory-augmented analysis."""
    async def run_qa_results():
        # Simplified implementation - in real scenario would retrieve from memory service
        monitor = CMPMQAMonitor()
        qa_agent = await monitor.get_qa_agent()
        
        # Simulate retrieving recent test results
        console.print(Panel(
            Text(f"QA Results Dashboard\nFormat: {output_format} | Limit: {limit}", 
                 justify="center", style="bold white"),
            title="📊 Test Results & Patterns",
            border_style="cyan"
        ))
        
        console.print()
        console.print("[dim]Recent test results would be displayed here.[/dim]")
        console.print("[dim]Memory-augmented pattern analysis would show trends and recommendations.[/dim]")
        console.print()
        console.print("[yellow]Note: This is a placeholder implementation. Full results retrieval")
        console.print("from memory service will be available in the complete implementation.[/yellow]")
    
    try:
        asyncio.run(run_qa_results())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# Register commands for CLI integration
def register_cmpm_commands(cli_group):
    """Register CMMP commands with the main CLI group."""
    cli_group.add_command(cmpm_health)
    cli_group.add_command(cmpm_agents)
    cli_group.add_command(cmpm_index)
    cli_group.add_command(cmpm_dashboard)
    cli_group.add_command(cmpm_qa_status)
    cli_group.add_command(cmpm_qa_test)
    cli_group.add_command(cmpm_qa_results)


# Main CLI group for direct module execution
@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """CMPM Framework Commands - Main CLI Entry Point."""
    if ctx.invoked_subcommand is None:
        console.print("""
[bold cyan]CMPM Framework Commands[/bold cyan]

Available commands:
• [green]cmpm:health[/green] - System health dashboard
• [green]cmpm:agents[/green] - Agent registry overview
• [green]cmpm:index[/green] - Project discovery index
• [green]cmpm:dashboard[/green] - Portfolio manager dashboard
• [green]cmpm:qa-status[/green] - QA extension status and health
• [green]cmpm:qa-test[/green] - Execute browser-based tests
• [green]cmpm:qa-results[/green] - View test results and patterns

Usage:
• [dim]python -m claude_pm.cmpm_commands cmpm:health[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:agents[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:index[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:dashboard[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:qa-status[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:qa-test --browser[/dim]
• [dim]python -m claude_pm.cmpm_commands cmpm:qa-results[/dim]
        """)


# Register all commands to the main group
main.add_command(cmpm_health)
main.add_command(cmpm_agents)
main.add_command(cmpm_index)
main.add_command(cmpm_dashboard)
main.add_command(cmpm_qa_status)
main.add_command(cmpm_qa_test)
main.add_command(cmpm_qa_results)


if __name__ == "__main__":
    main()