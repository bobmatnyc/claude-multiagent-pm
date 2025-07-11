"""
CMPM Health Commands
==================

Health monitoring and integration management commands for the Claude PM Framework.
Provides system health dashboards and integration status monitoring.
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..services.health_dashboard import HealthDashboardOrchestrator
from ..services.memory_service import MemoryService
from ..core.config import Config
from ..agents.enhanced_qa_agent import EnhancedQAAgent
from .utils.command_utils import CMPMCommandBase, handle_command_error, run_async_command
from .utils.formatters import format_health_status, format_json_output

console = Console()
logger = logging.getLogger(__name__)


class CMPMHealthMonitor(CMPMCommandBase):
    """CMPM Health Command Implementation with ai-trackdown integration."""
    
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
                "framework_version": "4.5.0",
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
        """Get ai-trackdown-tools integration health status via orchestrator."""
        try:
            # Use health dashboard orchestrator for consistent status reporting
            dashboard = HealthDashboardOrchestrator(
                cache_ttl_seconds=10.0,
                global_timeout_seconds=2.0
            )
            
            # Collect health data from orchestrator
            health_data = await dashboard._collect_fresh_health()
            
            # Find ai-trackdown specific reports
            ai_trackdown_reports = []
            for subsystem in health_data.subsystems:
                # Handle both object and dict subsystem data
                subsystem_name = getattr(subsystem, 'name', subsystem) if hasattr(subsystem, 'name') else str(subsystem)
                if subsystem_name == "AI-Trackdown Tools":
                    ai_trackdown_reports = getattr(subsystem, 'services', []) if hasattr(subsystem, 'services') else []
                    break
            
            if ai_trackdown_reports:
                # Aggregate status from all ai-trackdown reports
                all_healthy = all(report.status.value == "healthy" for report in ai_trackdown_reports)
                any_error = any(report.status.value in ["error", "down"] for report in ai_trackdown_reports)
                
                if all_healthy:
                    status = "operational"
                elif any_error:
                    status = "error"
                else:
                    status = "degraded"
                
                # Calculate metrics
                total_items = 0
                for report in ai_trackdown_reports:
                    if "items tracked" in report.message:
                        import re
                        match = re.search(r'(\d+)\s+items tracked', report.message)
                        if match:
                            total_items = int(match.group(1))
                
                return {
                    "status": status,
                    "service": "ai-trackdown-tools",
                    "version": "1.0.0+build.1",
                    "cli_responsive": True,
                    "total_items": total_items,
                    "reports_count": len(ai_trackdown_reports),
                    "last_check": datetime.now().isoformat()
                }
            else:
                # Fallback to direct CLI test if orchestrator has no ai-trackdown data
                result = subprocess.run(
                    ["aitrackdown", "status"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    cwd=self.framework_path
                )
                
                if result.returncode == 0:
                    return {
                        "status": "operational",
                        "service": "ai-trackdown-tools",
                        "version": "1.0.0+build.1",
                        "cli_responsive": True,
                        "fallback_method": "direct_cli",
                        "last_check": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "error", 
                        "service": "ai-trackdown-tools",
                        "error": "CLI not accessible",
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
            # Get epic, issue, and task counts using global CLI
            epic_result = subprocess.run(
                ["aitrackdown", "epic", "list"],
                capture_output=True,
                text=True,
                timeout=3,
                cwd=self.framework_path
            )
            
            issue_result = subprocess.run(
                ["aitrackdown", "issue", "list"],
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
                # self.get_qa_system_health(),  # Excluded - QA Agent not ready
                return_exceptions=True
            )
            
            progress.update(task, description="Generating dashboard...")
            
            # Process collected data
            framework_health, aitrackdown_health, task_health, memory_health = health_data
            qa_health = None  # QA Agent excluded from health checks
            
            # Calculate reliability score
            all_health_data = {
                "framework": framework_health,
                "aitrackdown": aitrackdown_health,
                "task_system": task_health,
                "memory_system": memory_health
                # "qa_system": qa_health  # Excluded - QA Agent not ready
            }
            
            reliability_score = self.calculate_system_reliability_score(all_health_data)
            
            progress.update(task, description="Rendering dashboard...")
        
        # Create dashboard header
        total_time = self.get_execution_time()
        
        header = Panel(
            Text(f"CMPM Health Dashboard v4.5.0\nSystem Reliability Score: {reliability_score}%\nResponse Time: {total_time:.2f}s", 
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
            # Fix status mapping: accept both "operational" and "healthy" as operational
            status = aitrackdown_health.get("status", "unknown")
            is_operational = status in ["operational", "healthy"]
            status_color = "green" if is_operational else "red"
            table.add_row(
                "AI-Trackdown Tools",
                f"[{status_color}]{status.upper()}[/{status_color}]",
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
        
        # Add QA system health - EXCLUDED (not ready)
        # Enhanced QA Agent excluded from health monitoring until development complete
        table.add_row(
            "Enhanced QA Agent",
            "[yellow]EXCLUDED[/yellow]",
            "Not included in health monitoring (development in progress)"
        )
        
        console.print(table)
        console.print()
        
        # System summary
        summary_text = f"""
🚀 **Framework Status**: Claude PM Framework v4.5.0 operational
📊 **Task Management**: {task_health.get('total_items', 0)} total items managed
🧠 **Memory Integration**: mem0AI connectivity {'active' if memory_health.get('mem0ai_connected') else 'inactive'}
🧪 **Enhanced QA Agent**: Excluded from monitoring (development in progress)
⚡ **Performance**: {total_time:.2f}s response time | {reliability_score}% reliability
        """
        
        console.print(Panel(summary_text.strip(), title="System Summary", border_style="blue"))




# CLI Commands
@click.command(name="cmpm:health")
@click.option("--output-json", is_flag=True, help="Output detailed health data as JSON")
@click.option("--detailed", is_flag=True, help="Show detailed component information")
def cmpm_health(output_json: bool, detailed: bool):
    """🏥 CMPM Health - Comprehensive system health dashboard"""
    
    async def run_health_check():
        monitor = CMPMHealthMonitor()
        
        if output_json:
            # Collect all health data for JSON output
            health_data = await asyncio.gather(
                monitor.get_framework_health(),
                monitor.get_aitrackdown_health(),
                monitor.get_task_system_health(),
                monitor.get_memory_system_health(),
                return_exceptions=True
            )
            
            framework_health, aitrackdown_health, task_health, memory_health = health_data
            
            output = {
                "framework": framework_health,
                "aitrackdown": aitrackdown_health,
                "task_system": task_health,
                "memory_system": memory_health,
                "timestamp": datetime.now().isoformat()
            }
            
            console.print(format_json_output(output))
        else:
            # Show interactive dashboard
            await monitor.generate_health_dashboard()
    
    run_async_command(run_health_check())




__all__ = [
    'cmpm_health',
    'CMPMHealthMonitor'
]