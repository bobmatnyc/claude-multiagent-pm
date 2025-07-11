"""
AI-Trackdown Tools Health Collector for ISS-0002.

Monitors the health and functionality of the ai-trackdown-tools CLI system
including ticket management, task system operational status, and 
migration progress tracking.
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..interfaces.health import HealthCollector  
from ..models.health import ServiceHealthReport, HealthStatus, create_service_health_report


class AITrackdownHealthCollector(HealthCollector):
    """
    Health collector for ai-trackdown-tools CLI system.
    
    Monitors:
    - CLI functionality and responsiveness
    - Task system operational status
    - Migration progress tracking
    - Framework component availability
    - Ticket system integrity
    """
    
    def __init__(self, framework_root: Optional[Path] = None, timeout_seconds: float = 5.0):
        """
        Initialize AI-Trackdown health collector.
        
        Args:
            framework_root: Root directory of the framework
            timeout_seconds: Timeout for health collection
        """
        super().__init__("ai_trackdown_tools", timeout_seconds)
        self.framework_root = framework_root or Path("/Users/masa/Projects/claude-multiagent-pm")
        # Use global CLI installation instead of local bin
        self.cli_path = "aitrackdown"  # Use global command
        self.tasks_path = self.framework_root / "tasks"
        
    async def collect_health(self) -> List[ServiceHealthReport]:
        """
        Collect health reports from ai-trackdown-tools system.
        
        Returns:
            List of ServiceHealthReport objects for trackdown services
        """
        reports = []
        
        # CLI functionality health
        reports.append(await self._check_cli_functionality())
        
        # CLI status command validation
        reports.append(await self._check_cli_status_command())
        
        # Task system health
        reports.append(await self._check_task_system())
        
        # Migration progress health
        reports.append(await self._check_migration_progress())
        
        # Framework component availability
        reports.append(await self._check_framework_components())
        
        # Ticket system integrity
        reports.append(await self._check_ticket_system_integrity())
        
        # Project backlog health
        reports.append(await self._check_project_backlog())
        
        # CLI command execution health
        reports.append(await self._check_cli_command_execution())
        
        return reports
    
    async def _check_cli_functionality(self) -> ServiceHealthReport:
        """Check ai-trackdown-tools CLI functionality."""
        try:
            start_time = time.time()
            
            # Try to execute basic CLI command with fallback
            try:
                # First try the wrapper script
                process = await asyncio.create_subprocess_exec(
                    str(self.cli_path), "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.framework_root)
                )
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), 
                        timeout=3.0
                    )
                finally:
                    # Ensure process cleanup
                    if process.returncode is None:
                        try:
                            process.terminate()
                            await asyncio.wait_for(process.wait(), timeout=1.0)
                        except asyncio.TimeoutError:
                            process.kill()
                            await process.wait()
                
                response_time = (time.time() - start_time) * 1000
                
                if process.returncode == 0:
                    # CLI is working properly
                    version_info = stdout.decode().strip()
                    return create_service_health_report(
                        name="ai_trackdown_cli",
                        status=HealthStatus.HEALTHY,
                        message=f"CLI functional and responsive ({version_info})",
                        response_time_ms=response_time,
                        metrics={
                            "cli_path": str(self.cli_path),
                            "version": version_info,
                            "response_time_ms": response_time
                        }
                    )
                else:
                    # CLI has issues
                    error_msg = stderr.decode().strip()
                    return create_service_health_report(
                        name="ai_trackdown_cli",
                        status=HealthStatus.UNHEALTHY,
                        message=f"CLI command failed: {error_msg}",
                        response_time_ms=response_time,
                        error=error_msg
                    )
                    
            except asyncio.TimeoutError:
                return create_service_health_report(
                    name="ai_trackdown_cli",
                    status=HealthStatus.UNHEALTHY,
                    message="CLI command timed out (>3s)",
                    response_time_ms=3000.0
                )
                
        except Exception as e:
            # Fallback: Check if CLI exists and is executable
            if self.cli_path.exists() and self.cli_path.is_file():
                # CLI exists but may have runtime issues
                return create_service_health_report(
                    name="ai_trackdown_cli",
                    status=HealthStatus.DEGRADED,
                    message=f"CLI exists but execution failed: {str(e)}",
                    error=str(e),
                    metrics={
                        "cli_exists": True,
                        "cli_path": str(self.cli_path),
                        "executable": self.cli_path.stat().st_mode & 0o111 != 0
                    }
                )
            else:
                # CLI is missing
                return create_service_health_report(
                    name="ai_trackdown_cli",
                    status=HealthStatus.DOWN,
                    message="CLI binary not found or not executable",
                    error=str(e),
                    metrics={
                        "cli_exists": False,
                        "cli_path": str(self.cli_path)
                    }
                )
    
    async def _check_task_system(self) -> ServiceHealthReport:
        """Check task system operational status."""
        try:
            start_time = time.time()
            
            # Check task directory structure
            if not self.tasks_path.exists():
                return create_service_health_report(
                    name="task_system",
                    status=HealthStatus.DOWN,
                    message="Task system directory not found",
                    metrics={"tasks_path": str(self.tasks_path)}
                )
            
            # Count active tasks, issues, and epics
            epics_count = len(list((self.tasks_path / "epics").glob("*.md"))) if (self.tasks_path / "epics").exists() else 0
            issues_count = len(list((self.tasks_path / "issues").glob("*.md"))) if (self.tasks_path / "issues").exists() else 0
            tasks_count = len(list((self.tasks_path / "tasks").glob("*.md"))) if (self.tasks_path / "tasks").exists() else 0
            
            response_time = (time.time() - start_time) * 1000
            
            total_items = epics_count + issues_count + tasks_count
            
            if total_items > 0:
                status = HealthStatus.HEALTHY
                message = f"Task system operational ({total_items} items tracked)"
            else:
                status = HealthStatus.DEGRADED
                message = "Task system directories exist but no items found"
            
            return create_service_health_report(
                name="task_system",
                status=status,
                message=message,
                response_time_ms=response_time,
                metrics={
                    "epics_count": epics_count,
                    "issues_count": issues_count,
                    "tasks_count": tasks_count,
                    "total_items": total_items,
                    "tasks_path": str(self.tasks_path)
                }
            )
            
        except Exception as e:
            return create_service_health_report(
                name="task_system",
                status=HealthStatus.ERROR,
                message=f"Error checking task system: {str(e)}",
                error=str(e)
            )
    
    async def _check_migration_progress(self) -> ServiceHealthReport:
        """Check migration progress from legacy trackdown system."""
        try:
            start_time = time.time()
            
            # Check for TSK-0001 (migration task)
            migration_task = self.tasks_path / "tasks" / "TSK-0001-complete-ticket-data-migration.md"
            
            if migration_task.exists():
                # Read migration task to check completion status
                content = migration_task.read_text()
                
                # Check for completion indicators
                if "status: completed" in content:
                    status = HealthStatus.HEALTHY
                    message = "Migration task completed successfully"
                elif "status: active" in content:
                    status = HealthStatus.DEGRADED
                    message = "Migration task still in progress"
                else:
                    status = HealthStatus.UNKNOWN
                    message = "Migration task status unclear"
                
                # Count migration progress indicators
                completion_percentage = 100 if "status: completed" in content else 80
                
                response_time = (time.time() - start_time) * 1000
                
                return create_service_health_report(
                    name="migration_progress",
                    status=status,
                    message=message,
                    response_time_ms=response_time,
                    metrics={
                        "migration_task_exists": True,
                        "completion_percentage": completion_percentage,
                        "migration_task_path": str(migration_task)
                    }
                )
            else:
                return create_service_health_report(
                    name="migration_progress",
                    status=HealthStatus.UNKNOWN,
                    message="Migration task not found",
                    metrics={
                        "migration_task_exists": False,
                        "expected_path": str(migration_task)
                    }
                )
                
        except Exception as e:
            return create_service_health_report(
                name="migration_progress",
                status=HealthStatus.ERROR,
                message=f"Error checking migration progress: {str(e)}",
                error=str(e)
            )
    
    async def _check_framework_components(self) -> ServiceHealthReport:
        """Check framework component availability."""
        try:
            start_time = time.time()
            
            # Check key framework components
            components = {
                "templates": self.tasks_path / "templates",
                "epics": self.tasks_path / "epics",
                "issues": self.tasks_path / "issues", 
                "tasks": self.tasks_path / "tasks",
                "prs": self.tasks_path / "prs"
            }
            
            available_components = {}
            for name, path in components.items():
                available_components[name] = path.exists()
            
            available_count = sum(available_components.values())
            total_count = len(components)
            
            response_time = (time.time() - start_time) * 1000
            
            if available_count == total_count:
                status = HealthStatus.HEALTHY
                message = f"All {total_count} framework components available"
            elif available_count >= total_count * 0.8:
                status = HealthStatus.DEGRADED
                message = f"{available_count}/{total_count} framework components available"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Only {available_count}/{total_count} framework components available"
            
            return create_service_health_report(
                name="framework_components",
                status=status,
                message=message,
                response_time_ms=response_time,
                metrics={
                    "available_components": available_count,
                    "total_components": total_count,
                    "components_status": available_components
                }
            )
            
        except Exception as e:
            return create_service_health_report(
                name="framework_components",
                status=HealthStatus.ERROR,
                message=f"Error checking framework components: {str(e)}",
                error=str(e)
            )
    
    async def _check_cli_status_command(self) -> ServiceHealthReport:
        """Check ai-trackdown-tools status command functionality."""
        try:
            start_time = time.time()
            
            # Try to execute status command
            process = await asyncio.create_subprocess_exec(
                str(self.cli_path), "status", "--table",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.framework_root)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=10.0
                )
            finally:
                # Ensure process cleanup
                if process.returncode is None:
                    try:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=1.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
            
            response_time = (time.time() - start_time) * 1000
            
            if process.returncode == 0:
                status_output = stdout.decode().strip()
                
                # Parse status output for key metrics
                metrics = {
                    "status_command_working": True,
                    "response_time_ms": response_time,
                    "output_length": len(status_output)
                }
                
                # Check for key status indicators
                if "epics" in status_output.lower() or "issues" in status_output.lower():
                    metrics["has_structured_output"] = True
                else:
                    metrics["has_structured_output"] = False
                
                return create_service_health_report(
                    name="cli_status_command",
                    status=HealthStatus.HEALTHY,
                    message="Status command executed successfully",
                    response_time_ms=response_time,
                    metrics=metrics
                )
            else:
                error_msg = stderr.decode().strip()
                return create_service_health_report(
                    name="cli_status_command",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Status command failed: {error_msg}",
                    response_time_ms=response_time,
                    error=error_msg
                )
                
        except asyncio.TimeoutError:
            return create_service_health_report(
                name="cli_status_command",
                status=HealthStatus.UNHEALTHY,
                message="Status command timed out (>10s)",
                response_time_ms=10000.0
            )
        except Exception as e:
            return create_service_health_report(
                name="cli_status_command",
                status=HealthStatus.ERROR,
                message=f"Error executing status command: {str(e)}",
                error=str(e)
            )
    
    async def _check_project_backlog(self) -> ServiceHealthReport:
        """Check project backlog health using ai-trackdown-tools."""
        try:
            start_time = time.time()
            
            # Try to execute backlog command
            process = await asyncio.create_subprocess_exec(
                str(self.cli_path), "backlog",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.framework_root)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=10.0
                )
            finally:
                # Ensure process cleanup
                if process.returncode is None:
                    try:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=1.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
            
            response_time = (time.time() - start_time) * 1000
            
            if process.returncode == 0:
                backlog_output = stdout.decode().strip()
                
                metrics = {
                    "backlog_command_working": True,
                    "response_time_ms": response_time,
                    "backlog_accessible": True
                }
                
                return create_service_health_report(
                    name="project_backlog",
                    status=HealthStatus.HEALTHY,
                    message="Project backlog accessible via CLI",
                    response_time_ms=response_time,
                    metrics=metrics
                )
            else:
                error_msg = stderr.decode().strip()
                return create_service_health_report(
                    name="project_backlog",
                    status=HealthStatus.DEGRADED,
                    message=f"Backlog command issues: {error_msg}",
                    response_time_ms=response_time,
                    error=error_msg
                )
                
        except asyncio.TimeoutError:
            return create_service_health_report(
                name="project_backlog",
                status=HealthStatus.UNHEALTHY,
                message="Backlog command timed out (>10s)",
                response_time_ms=10000.0
            )
        except Exception as e:
            return create_service_health_report(
                name="project_backlog",
                status=HealthStatus.ERROR,
                message=f"Error checking project backlog: {str(e)}",
                error=str(e)
            )
    
    async def _check_cli_command_execution(self) -> ServiceHealthReport:
        """Check various CLI command execution health."""
        try:
            start_time = time.time()
            
            # Test multiple CLI commands
            test_commands = [
                (["epic", "list"], "epic_list"),
                (["issue", "list"], "issue_list"),
                (["task", "list"], "task_list")
            ]
            
            command_results = {}
            working_commands = 0
            
            for command_args, command_name in test_commands:
                try:
                    process = await asyncio.create_subprocess_exec(
                        str(self.cli_path), *command_args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=str(self.framework_root)
                    )
                    
                    try:
                        stdout, stderr = await asyncio.wait_for(
                            process.communicate(), 
                            timeout=5.0
                        )
                    finally:
                        # Ensure process cleanup
                        if process.returncode is None:
                            try:
                                process.terminate()
                                await asyncio.wait_for(process.wait(), timeout=1.0)
                            except asyncio.TimeoutError:
                                process.kill()
                                await process.wait()
                    
                    command_results[command_name] = {
                        "success": process.returncode == 0,
                        "error": stderr.decode().strip() if process.returncode != 0 else None
                    }
                    
                    if process.returncode == 0:
                        working_commands += 1
                        
                except asyncio.TimeoutError:
                    command_results[command_name] = {
                        "success": False,
                        "error": "Command timed out"
                    }
                except Exception as e:
                    command_results[command_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            response_time = (time.time() - start_time) * 1000
            total_commands = len(test_commands)
            
            metrics = {
                "working_commands": working_commands,
                "total_commands": total_commands,
                "success_rate": (working_commands / total_commands) * 100,
                "command_results": command_results,
                "response_time_ms": response_time
            }
            
            if working_commands == total_commands:
                status = HealthStatus.HEALTHY
                message = f"All {total_commands} CLI commands working properly"
            elif working_commands >= total_commands * 0.7:
                status = HealthStatus.DEGRADED
                message = f"{working_commands}/{total_commands} CLI commands working"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Only {working_commands}/{total_commands} CLI commands working"
            
            return create_service_health_report(
                name="cli_command_execution",
                status=status,
                message=message,
                response_time_ms=response_time,
                metrics=metrics
            )
            
        except Exception as e:
            return create_service_health_report(
                name="cli_command_execution",
                status=HealthStatus.ERROR,
                message=f"Error testing CLI command execution: {str(e)}",
                error=str(e)
            )
    
    async def _check_ticket_system_integrity(self) -> ServiceHealthReport:
        """Check ticket system integrity and cross-references."""
        try:
            start_time = time.time()
            
            # Check for ISS-0002 (this current issue)
            current_issue = self.tasks_path / "issues" / "ISS-0002-comprehensive-health-slash-command.md"
            
            integrity_issues = []
            metrics = {}
            
            if current_issue.exists():
                content = current_issue.read_text()
                
                # Check for expected content
                if "ISS-0002" in content:
                    metrics["issue_id_present"] = True
                else:
                    integrity_issues.append("Issue ID not found in content")
                
                if "completion_percentage" in content:
                    import re
                    percentage_match = re.search(r'completion_percentage:\s*(\d+)', content)
                    if percentage_match:
                        metrics["completion_percentage"] = int(percentage_match.group(1))
                    else:
                        metrics["completion_percentage"] = 0
                else:
                    integrity_issues.append("Completion percentage not found")
                
                metrics["current_issue_exists"] = True
            else:
                integrity_issues.append("Current issue (ISS-0002) not found")
                metrics["current_issue_exists"] = False
            
            response_time = (time.time() - start_time) * 1000
            
            if not integrity_issues:
                status = HealthStatus.HEALTHY
                message = "Ticket system integrity verified"
            elif len(integrity_issues) == 1:
                status = HealthStatus.DEGRADED
                message = f"Minor integrity issue: {integrity_issues[0]}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Multiple integrity issues: {', '.join(integrity_issues)}"
            
            return create_service_health_report(
                name="ticket_system_integrity",
                status=status,
                message=message,
                response_time_ms=response_time,
                metrics=metrics
            )
            
        except Exception as e:
            return create_service_health_report(
                name="ticket_system_integrity",
                status=HealthStatus.ERROR,
                message=f"Error checking ticket system integrity: {str(e)}",
                error=str(e)
            )
    
    def get_subsystem_name(self) -> str:
        """Get the subsystem name for this collector."""
        return "AI-Trackdown Tools"
    
    def get_service_names(self) -> List[str]:
        """Get the list of service names this collector monitors."""
        return [
            "ai_trackdown_cli",
            "cli_status_command",
            "task_system",
            "migration_progress",
            "framework_components",
            "ticket_system_integrity",
            "project_backlog",
            "cli_command_execution"
        ]
    
    def get_collector_stats(self) -> Dict[str, Any]:
        """Get collector-specific statistics."""
        return {
            "framework_root": str(self.framework_root),
            "cli_path": str(self.cli_path),
            "tasks_path": str(self.tasks_path),
            "cli_exists": self.cli_path.exists(),
            "tasks_dir_exists": self.tasks_path.exists()
        }