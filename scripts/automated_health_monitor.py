#!/usr/bin/env python3
"""
Claude PM Framework - Enhanced Automated Project Health Monitor (Python Version)

Comprehensive health monitoring system that tracks:
- Project structure compliance
- Git activity and repository health
- Framework adherence (CLAUDE.md files, TrackDown system)
- Service availability (mem0ai on port 8002, portfolio manager on port 3000, etc.)
- Performance metrics and response times
- TrackDown system status and ticket progress
- Managed projects health across ~/Projects/managed/
- Automated alerting for critical issues
- Background monitoring capabilities

Features:
- JSON and markdown health reports
- Continuous background monitoring
- Service status checks with response times
- Framework compliance validation
- Intelligent alerting and recommendations
- Async/await patterns for performance
- Type hints for better maintainability
"""

import asyncio
import json
import os
import signal
import socket
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging
import argparse
from contextlib import asynccontextmanager

import aiohttp
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
import click

# Configure rich console
console = Console()

@dataclass
class ServiceConfig:
    """Configuration for a monitored service."""
    port: int
    path: str = "/"
    description: str = ""
    critical: bool = False
    timeout: int = 5000
    process_check: Optional[callable] = None

@dataclass
class HealthCheck:
    """Result of a health check operation."""
    name: str
    status: str
    timestamp: str
    error: Optional[str] = None
    response_time: Optional[int] = None
    http_status: Optional[int] = None
    performance: Optional[str] = None
    process_info: Optional[Dict] = None

@dataclass
class ProjectHealth:
    """Health status of a project."""
    name: str
    path: str
    status: str
    issues: List[str]
    metrics: Dict[str, Any]
    last_check: str

@dataclass
class FrameworkCompliance:
    """Framework compliance metrics."""
    compliance_percentage: int
    total_checks: int
    passed_checks: int
    optional_compliance: int
    optional_total: int
    file_checks: Dict[str, Dict]
    directory_checks: Dict[str, Dict]
    last_check: str
    managed_projects: Optional[Dict] = None
    trackdown: Optional[Dict] = None

@dataclass
class Alert:
    """Alert information."""
    timestamp: str
    level: str
    message: str
    data: Optional[Dict] = None

@dataclass
class HealthSummary:
    """Summary of overall health metrics."""
    total_projects: int = 0
    healthy_projects: int = 0
    warning_projects: int = 0
    critical_projects: int = 0
    framework_compliance: int = 0
    overall_health_percentage: int = 0
    project_health_percentage: int = 0
    service_health_percentage: int = 0

@dataclass
class HealthReport:
    """Complete health report."""
    timestamp: str
    version: str
    config: Dict
    summary: HealthSummary
    services: Dict[str, HealthCheck]
    projects: Dict[str, ProjectHealth]
    framework: FrameworkCompliance
    recommendations: List[str]
    alerts: List[Alert]

class ClaudePMHealthMonitor:
    """
    Enhanced health monitoring system for Claude PM Framework.
    
    Provides comprehensive monitoring of projects, services, and framework compliance
    with async operations for better performance.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the health monitor with configuration."""
        self.base_path = Path.home() / "Projects"
        self.claude_pm_path = self.base_path / "Claude-PM"
        self.managed_path = self.base_path / "managed"
        self.services_path = Path.home() / "Services"
        
        # Default configuration
        default_config = {
            "check_interval": 5 * 60,  # 5 minutes in seconds
            "alert_threshold": 60,
            "enable_alerting": True,
            "enable_service_checks": True,
            "enable_git_checks": True,
            "verbose_logging": False,
            "timeout": 5000,
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Initialize logging
        self._setup_logging()
        
        # Ensure logs directory exists
        self.logs_dir = self.claude_pm_path / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Log files
        self.log_file = self.logs_dir / "health-monitor.log"
        self.status_file = self.logs_dir / "monitor-status.json"
        self.alert_log = self.logs_dir / "health-alerts.log"
        
        # Initialize health report
        self.health_report = self._init_health_report()
        
        # Monitor status tracking
        self.monitor_status = {
            "pid": os.getpid(),
            "start_time": datetime.now().isoformat(),
            "last_check": None,
            "checks_run": 0,
            "alerts_sent": 0
        }
        
        # Service configurations
        self.services = {
            "mem0ai_mcp": ServiceConfig(
                port=8002,
                path="/health",
                description="mem0AI MCP Service",
                critical=True,
                process_check=self._check_mem0ai_service
            ),
            "portfolio_manager": ServiceConfig(
                port=3000,
                path="/",
                description="Claude PM Portfolio Manager",
                critical=False
            ),
            "git_portfolio_manager": ServiceConfig(
                port=3001,
                path="/health",
                description="Git Portfolio Manager",
                critical=False
            ),
            "claude_pm_dashboard": ServiceConfig(
                port=5173,
                path="/",
                description="Claude PM Dashboard (Vite)",
                critical=False
            )
        }
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        level = logging.DEBUG if self.config["verbose_logging"] else logging.INFO
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    self.claude_pm_path / "logs" / "health-monitor.log",
                    mode='a'
                ) if (self.claude_pm_path / "logs").exists() else logging.NullHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _init_health_report(self) -> HealthReport:
        """Initialize a fresh health report."""
        return HealthReport(
            timestamp=datetime.now().isoformat(),
            version="3.0.0-python",
            config=self.config,
            summary=HealthSummary(),
            services={},
            projects={},
            framework=FrameworkCompliance(
                compliance_percentage=0,
                total_checks=0,
                passed_checks=0,
                optional_compliance=0,
                optional_total=0,
                file_checks={},
                directory_checks={},
                last_check=datetime.now().isoformat()
            ),
            recommendations=[],
            alerts=[]
        )
    
    async def check_port(self, port: int, timeout: float = 1.0) -> Dict[str, Union[bool, str]]:
        """Check if a port is listening."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection('localhost', port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return {"listening": True}
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            return {"listening": False, "error": str(e)}
    
    async def http_check(self, url: str, timeout: float = 5.0) -> Dict[str, Union[bool, int, str, None]]:
        """Perform HTTP health check."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as response:
                    return {
                        "success": 200 <= response.status < 400,
                        "status_code": response.status,
                        "error": None
                    }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_mem0ai_service(self) -> Dict[str, Any]:
        """Check mem0AI service specific information."""
        try:
            service_path = self.services_path / "mem0ai-mcp"
            if service_path.exists():
                makefile_path = service_path / "Makefile"
                if makefile_path.exists():
                    result = subprocess.run(
                        ["make", "status"],
                        cwd=service_path,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    return {
                        "service_directory": str(service_path),
                        "status_output": result.stdout.strip(),
                        "makefile_exists": True,
                        "exit_code": result.returncode
                    }
                return {
                    "service_directory": str(service_path),
                    "makefile_exists": False
                }
            return {
                "service_directory": str(service_path),
                "directory_exists": False
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def check_service_health(self) -> None:
        """Check health of all configured services."""
        self.logger.info("Checking service health...")
        
        if not self.config["enable_service_checks"]:
            self.logger.info("Service checks disabled")
            return
        
        for service_name, service_config in self.services.items():
            try:
                start_time = asyncio.get_event_loop().time()
                
                # Check if port is listening
                port_check = await self.check_port(service_config.port)
                
                health_check = HealthCheck(
                    name=service_name,
                    status="down",
                    timestamp=datetime.now().isoformat(),
                    error=port_check.get("error")
                )
                
                if port_check["listening"]:
                    # Port is listening, check HTTP endpoint
                    url = f"http://localhost:{service_config.port}{service_config.path}"
                    response = await self.http_check(url, timeout=self.config["timeout"] / 1000)
                    response_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
                    
                    health_check.status = "healthy" if response["success"] else "unhealthy"
                    health_check.response_time = response_time
                    health_check.http_status = response.get("status_code")
                    health_check.error = response.get("error")
                    
                    # Add performance rating
                    if response["success"]:
                        if response_time < 100:
                            health_check.performance = "excellent"
                        elif response_time < 500:
                            health_check.performance = "good"
                        elif response_time < 2000:
                            health_check.performance = "fair"
                        else:
                            health_check.performance = "poor"
                else:
                    health_check.status = "down"
                    health_check.error = "Port not listening"
                    
                    # Check if process should be running
                    if service_config.process_check:
                        process_info = await service_config.process_check()
                        health_check.process_info = process_info
                
                self.health_report.services[service_name] = health_check
                
                # Generate alert for critical services that are down
                if service_config.critical and health_check.status != "healthy":
                    await self._add_alert(
                        "critical",
                        f"Critical service {service_name} is {health_check.status}",
                        {"service": service_name, "error": health_check.error}
                    )
                
                self.logger.info(
                    f"Service {service_name}: {health_check.status} "
                    f"({health_check.response_time}ms)"
                )
                
            except Exception as e:
                error_check = HealthCheck(
                    name=service_name,
                    status="error",
                    timestamp=datetime.now().isoformat(),
                    error=str(e)
                )
                
                self.health_report.services[service_name] = error_check
                
                if service_config.critical:
                    await self._add_alert(
                        "critical",
                        f"Critical service check failed for {service_name}: {str(e)}"
                    )
                
                self.logger.error(f"Service {service_name} check failed: {str(e)}")
    
    async def _add_alert(self, level: str, message: str, data: Optional[Dict] = None) -> None:
        """Add an alert to the health report and log it."""
        alert = Alert(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            data=data
        )
        
        self.health_report.alerts.append(alert)
        
        # Log alert to file
        alert_line = f"[{alert.timestamp}] {level.upper()}: {message}"
        if data:
            alert_line += f" | {json.dumps(data)}"
        alert_line += "\n"
        
        try:
            with open(self.alert_log, "a") as f:
                f.write(alert_line)
            self.monitor_status["alerts_sent"] += 1
        except Exception as e:
            self.logger.error(f"Failed to write alert to log file: {e}")
        
        if self.config["enable_alerting"]:
            console.print(f"🚨 [bold red]ALERT[/bold red]: {alert_line.strip()}")
    
    async def check_framework_compliance(self) -> None:
        """Check framework compliance."""
        self.logger.info("Checking framework compliance...")
        
        required_files = [
            "trackdown/BACKLOG.md",
            "trackdown/MILESTONES.md",
            "CLAUDE.md",
            "README.md",
        ]
        
        required_directories = [
            "trackdown",
            "docs", 
            "scripts",
            "logs"
        ]
        
        optional_files = [
            "trackdown/README.md",
            "trackdown/METRICS.md",
            "trackdown/RETROSPECTIVES.md",
            "docs/TOOLCHAIN.md",
            "docs/INSTRUCTIONS.md"
        ]
        
        compliance = 0
        total = len(required_files) + len(required_directories)
        optional_compliance = 0
        
        # Check required files
        file_checks = {}
        for file in required_files:
            file_path = self.claude_pm_path / file
            exists = file_path.exists()
            file_checks[file] = {
                "exists": exists,
                "path": str(file_path),
                "required": True
            }
            
            if exists:
                compliance += 1
                self.logger.debug(f"Found required file: {file}")
                
                # Additional content checks for critical files
                if file == "trackdown/BACKLOG.md":
                    stats = file_path.stat()
                    file_checks[file].update({
                        "size": stats.st_size,
                        "last_modified": stats.st_mtime,
                        "content_health": await self._check_backlog_health(file_path)
                    })
            else:
                self.logger.warning(f"Missing required file: {file}")
                self.health_report.recommendations.append(f"Create missing file: {file}")
        
        # Check required directories
        directory_checks = {}
        for directory in required_directories:
            dir_path = self.claude_pm_path / directory
            exists = dir_path.exists() and dir_path.is_dir()
            directory_checks[directory] = {
                "exists": exists,
                "path": str(dir_path),
                "required": True
            }
            
            if exists:
                compliance += 1
                self.logger.debug(f"Found required directory: {directory}")
                
                # Check directory contents
                files = list(dir_path.iterdir())
                directory_checks[directory].update({
                    "file_count": len(files),
                    "files": [f.name for f in files]
                })
            else:
                self.logger.warning(f"Missing required directory: {directory}")
                self.health_report.recommendations.append(f"Create missing directory: {directory}")
        
        # Check optional files
        for file in optional_files:
            file_path = self.claude_pm_path / file
            if file_path.exists():
                optional_compliance += 1
        
        # Update framework compliance
        self.health_report.framework = FrameworkCompliance(
            compliance_percentage=round((compliance / total) * 100),
            total_checks=total,
            passed_checks=compliance,
            optional_compliance=optional_compliance,
            optional_total=len(optional_files),
            file_checks=file_checks,
            directory_checks=directory_checks,
            last_check=datetime.now().isoformat()
        )
        
        # Check managed projects and TrackDown health
        await self._check_managed_projects_compliance()
        await self._check_trackdown_health()
        
        # Generate framework-specific alerts
        compliance_percentage = self.health_report.framework.compliance_percentage
        if compliance_percentage < 80:
            await self._add_alert(
                "warning",
                f"Framework compliance is {compliance_percentage}% (below 80% threshold)"
            )
    
    async def _check_backlog_health(self, backlog_path: Path) -> Dict[str, Any]:
        """Check health of backlog file."""
        try:
            content = backlog_path.read_text()
            
            import re
            total_tickets = len(re.findall(r'^\- \[', content, re.MULTILINE))
            completed_tickets = len(re.findall(r'^\- \[x\]', content, re.MULTILINE))
            in_progress_tickets = len(re.findall(r'^\- \[>\]', content, re.MULTILINE))
            pending_tickets = len(re.findall(r'^\- \[ \]', content, re.MULTILINE))
            
            # Count priority tickets
            high_priority_tickets = len(re.findall(r'HIGH', content))
            critical_tickets = len(re.findall(r'CRITICAL', content))
            
            # Check for recent updates
            lines = content.split('\n')
            recently_updated = sum(
                1 for line in lines 
                if re.search(r'\d{4}-\d{2}-\d{2}', line) and
                datetime.fromisoformat(re.search(r'\d{4}-\d{2}-\d{2}', line).group()) > 
                datetime.now() - timedelta(days=7)
            )
            
            completion_rate = round((completed_tickets / total_tickets) * 100) if total_tickets > 0 else 0
            
            return {
                "total_tickets": total_tickets,
                "completed_tickets": completed_tickets,
                "in_progress_tickets": in_progress_tickets,
                "pending_tickets": pending_tickets,
                "high_priority_tickets": high_priority_tickets,
                "critical_tickets": critical_tickets,
                "recently_updated_lines": recently_updated,
                "completion_rate": completion_rate,
                "health_status": self._calculate_backlog_health_status(
                    total_tickets, completed_tickets, recently_updated
                )
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze backlog health: {e}")
            return {"error": str(e)}
    
    def _calculate_backlog_health_status(self, total: int, completed: int, recent_updates: int) -> str:
        """Calculate backlog health status."""
        if total == 0:
            return "empty"
        
        completion_rate = (completed / total) * 100
        has_recent_activity = recent_updates > 0
        
        if completion_rate >= 80 and has_recent_activity:
            return "excellent"
        elif completion_rate >= 60 and has_recent_activity:
            return "good"
        elif completion_rate >= 40 or has_recent_activity:
            return "fair"
        else:
            return "poor"
    
    async def _check_managed_projects_compliance(self) -> None:
        """Check compliance of managed projects."""
        self.logger.info("Checking managed projects framework compliance...")
        
        if not self.managed_path.exists():
            self.logger.warning("Managed projects directory not found")
            return
        
        managed_projects = [
            p for p in self.managed_path.iterdir()
            if p.is_dir() and not p.name.startswith('.')
        ]
        
        compliant_projects = 0
        project_compliance = {}
        
        for project_path in managed_projects:
            compliance = await self._check_single_project_compliance(project_path)
            project_compliance[project_path.name] = compliance
            
            if compliance["score"] >= 80:
                compliant_projects += 1
        
        self.health_report.framework.managed_projects = {
            "total_projects": len(managed_projects),
            "compliant_projects": compliant_projects,
            "compliance_rate": round((compliant_projects / len(managed_projects)) * 100) if managed_projects else 0,
            "project_details": project_compliance
        }
    
    async def _check_single_project_compliance(self, project_path: Path) -> Dict[str, Any]:
        """Check compliance of a single project."""
        required_files = ['CLAUDE.md', 'README.md']
        recommended_files = ['trackdown/BACKLOG.md', 'docs/INSTRUCTIONS.md']
        
        score = 0
        max_score = 0
        checks = {}
        
        # Check required files (70% of score)
        for file in required_files:
            file_path = project_path / file
            exists = file_path.exists()
            checks[file] = {"exists": exists, "required": True, "weight": 35}
            max_score += 35
            if exists:
                score += 35
        
        # Check recommended files (30% of score)
        for file in recommended_files:
            file_path = project_path / file
            exists = file_path.exists()
            checks[file] = {"exists": exists, "required": False, "weight": 10}
            max_score += 10
            if exists:
                score += 10
        
        final_score = round((score / max_score) * 100) if max_score > 0 else 0
        
        return {
            "project_name": project_path.name,
            "score": final_score,
            "max_score": max_score,
            "checks": checks,
            "status": "compliant" if final_score >= 80 else "partial" if final_score >= 60 else "non-compliant"
        }
    
    async def _check_trackdown_health(self) -> None:
        """Check TrackDown system health."""
        try:
            backlog_path = self.claude_pm_path / "trackdown" / "BACKLOG.md"
            if backlog_path.exists():
                content = backlog_path.read_text()
                
                import re
                total_tickets = len(re.findall(r'^\- \[', content, re.MULTILINE))
                completed_tickets = len(re.findall(r'^\- \[x\]', content, re.MULTILINE))
                pending_tickets = len(re.findall(r'^\- \[ \]', content, re.MULTILINE))
                
                stats = backlog_path.stat()
                last_modified = datetime.fromtimestamp(stats.st_mtime)
                days_since_update = (datetime.now() - last_modified).days
                
                self.health_report.framework.trackdown = {
                    "total_tickets": total_tickets,
                    "completed_tickets": completed_tickets,
                    "pending_tickets": pending_tickets,
                    "completion_rate": round((completed_tickets / total_tickets) * 100) if total_tickets > 0 else 0,
                    "last_update_days": days_since_update,
                    "health_status": "active" if days_since_update <= 7 else "moderate" if days_since_update <= 30 else "stale"
                }
                
                if days_since_update > 7:
                    self.health_report.recommendations.append(
                        f"TrackDown system hasn't been updated in {days_since_update} days - consider reviewing progress"
                    )
        except Exception as e:
            self.logger.error(f"Failed to check TrackDown health: {e}")
    
    async def run_health_check(self) -> None:
        """Run a complete health check."""
        self.logger.info("Starting comprehensive health check...")
        
        try:
            # Reset health report
            self.health_report = self._init_health_report()
            
            # Update monitor status
            self.monitor_status["last_check"] = datetime.now().isoformat()
            self.monitor_status["checks_run"] += 1
            
            # Show progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Run health checks
                task1 = progress.add_task("Checking service health...", total=None)
                await self.check_service_health()
                progress.update(task1, completed=True)
                
                task2 = progress.add_task("Checking framework compliance...", total=None)
                await self.check_framework_compliance()
                progress.update(task2, completed=True)
                
                task3 = progress.add_task("Scanning all projects...", total=None)
                await self._scan_all_projects()
                progress.update(task3, completed=True)
            
            # Calculate overall health and generate recommendations
            self._calculate_overall_health()
            self._generate_recommendations()
            self._check_critical_thresholds()
            
            # Save reports
            await self._save_health_report()
            self._save_monitor_status()
            
            self.logger.info("Health check completed successfully")
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            await self._add_alert("critical", f"Health check failed: {str(e)}")
    
    async def _scan_all_projects(self) -> None:
        """Scan all projects for health status."""
        self.logger.info("Scanning all projects...")
        
        # Scan managed projects
        if self.managed_path.exists():
            managed_projects = [
                p for p in self.managed_path.iterdir()
                if p.is_dir() and not p.name.startswith('.')
            ]
            
            for project_path in managed_projects:
                health = await self._check_project_health(project_path)
                self.health_report.projects[f"managed/{project_path.name}"] = health
        
        # Scan other projects in base directory
        excluded = {'managed', 'Claude-PM', 'node_modules', '.git'}
        other_projects = [
            p for p in self.base_path.iterdir()
            if p.is_dir() and not p.name.startswith('.') and p.name not in excluded
        ]
        
        for project_path in other_projects:
            health = await self._check_project_health(project_path)
            self.health_report.projects[project_path.name] = health
    
    async def _check_project_health(self, project_path: Path) -> ProjectHealth:
        """Check health of a single project."""
        project_name = project_path.name
        health = ProjectHealth(
            name=project_name,
            path=str(project_path),
            status="healthy",
            issues=[],
            metrics={},
            last_check=datetime.now().isoformat()
        )
        
        try:
            # Check for required files
            required_files = ['CLAUDE.md', 'README.md']
            for file in required_files:
                if not (project_path / file).exists():
                    health.issues.append(f"Missing {file}")
                    health.status = "warning"
            
            # Check git health
            if (project_path / '.git').exists():
                try:
                    git_health = await self._check_git_health(project_path)
                    health.metrics["git"] = git_health
                    
                    if git_health.get("days_since_last_commit", 0) > 30:
                        health.issues.append(f"No commits in {git_health['days_since_last_commit']} days")
                        if health.status == "healthy":
                            health.status = "warning"
                except Exception as e:
                    health.issues.append(f"Git check failed: {str(e)}")
                    health.status = "error"
            
            # Check for build configuration
            build_configs = ['package.json', 'pyproject.toml', 'Cargo.toml', 'Makefile']
            has_build_config = any((project_path / config).exists() for config in build_configs)
            
            if not has_build_config:
                health.issues.append("No build configuration found")
                if health.status == "healthy":
                    health.status = "warning"
            
            # Update summary counters
            self.health_report.summary.total_projects += 1
            if health.status == "healthy":
                self.health_report.summary.healthy_projects += 1
            elif health.status == "warning":
                self.health_report.summary.warning_projects += 1
            else:
                self.health_report.summary.critical_projects += 1
                
        except Exception as e:
            health.status = "error"
            health.issues.append(f"Health check failed: {str(e)}")
            self.health_report.summary.critical_projects += 1
            self.logger.error(f"Project health check failed for {project_name}: {e}")
        
        return health
    
    async def _check_git_health(self, project_path: Path) -> Dict[str, Any]:
        """Check git repository health."""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%cd|%s", "--date=iso"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {"error": "Git log failed"}
            
            hash_val, date, message = result.stdout.strip().split('|', 2)
            last_commit_date = datetime.fromisoformat(date.replace(' ', 'T'))
            days_since_last_commit = (datetime.now() - last_commit_date).days
            
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Check for uncommitted changes
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            has_uncommitted_changes = bool(status_result.stdout.strip())
            
            return {
                "last_commit_hash": hash_val,
                "last_commit_date": date,
                "last_commit_message": message,
                "days_since_last_commit": days_since_last_commit,
                "current_branch": current_branch,
                "has_uncommitted_changes": has_uncommitted_changes,
                "health_status": "active" if days_since_last_commit <= 7 else "moderate" if days_since_last_commit <= 30 else "stale"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_overall_health(self) -> None:
        """Calculate overall health percentage."""
        summary = self.health_report.summary
        
        # Calculate project health percentage
        project_health_percentage = 0
        if summary.total_projects > 0:
            project_health_percentage = round((summary.healthy_projects / summary.total_projects) * 100)
        
        # Calculate service health percentage
        total_services = len(self.health_report.services)
        healthy_services = sum(1 for s in self.health_report.services.values() if s.status == "healthy")
        service_health_percentage = round((healthy_services / total_services) * 100) if total_services > 0 else 100
        
        # Get framework compliance percentage
        framework_compliance = self.health_report.framework.compliance_percentage
        
        # Weighted overall health score
        weights = {"projects": 0.4, "services": 0.35, "framework": 0.25}
        
        overall_health = round(
            (project_health_percentage * weights["projects"]) +
            (service_health_percentage * weights["services"]) +
            (framework_compliance * weights["framework"])
        )
        
        # Update summary
        summary.overall_health_percentage = overall_health
        summary.project_health_percentage = project_health_percentage
        summary.service_health_percentage = service_health_percentage
        summary.framework_compliance = framework_compliance
    
    def _generate_recommendations(self) -> None:
        """Generate recommendations based on health findings."""
        summary = self.health_report.summary
        
        if summary.critical_projects > 0:
            self.health_report.recommendations.append(
                f"Address {summary.critical_projects} critical project issues immediately"
            )
        
        if summary.warning_projects > summary.healthy_projects:
            self.health_report.recommendations.append(
                "More than half of projects have warnings - consider a framework compliance review"
            )
        
        if summary.framework_compliance < 80:
            self.health_report.recommendations.append(
                "Framework compliance below 80% - review and update framework structure"
            )
        
        # Service-specific recommendations
        down_services = [
            name for name, service in self.health_report.services.items()
            if service.status != "healthy"
        ]
        
        if down_services:
            self.health_report.recommendations.append(
                f"Restart or fix services: {', '.join(down_services)}"
            )
    
    def _check_critical_thresholds(self) -> None:
        """Check for critical threshold violations."""
        summary = self.health_report.summary
        
        # Check overall health threshold
        if summary.overall_health_percentage < self.config["alert_threshold"]:
            asyncio.create_task(self._add_alert(
                "critical",
                f"Overall health {summary.overall_health_percentage}% is below alert threshold {self.config['alert_threshold']}%"
            ))
        
        # Check for critical projects
        if summary.critical_projects > 0:
            asyncio.create_task(self._add_alert(
                "critical",
                f"{summary.critical_projects} project(s) have critical issues requiring immediate attention"
            ))
        
        # Check framework compliance
        if summary.framework_compliance < 50:
            asyncio.create_task(self._add_alert(
                "critical",
                f"Framework compliance {summary.framework_compliance}% is critically low"
            ))
    
    async def _save_health_report(self) -> None:
        """Save health report to files."""
        try:
            # Save JSON report
            report_path = self.logs_dir / "health-report.json"
            with open(report_path, 'w') as f:
                json.dump(asdict(self.health_report), f, indent=2, default=str)
            
            # Save markdown summary
            summary_path = self.logs_dir / "health-summary.md"
            with open(summary_path, 'w') as f:
                f.write(self._generate_markdown_summary())
            
            self.logger.info(f"Health report saved to {report_path} and {summary_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save health report: {e}")
    
    def _generate_markdown_summary(self) -> str:
        """Generate markdown summary of health report."""
        summary = self.health_report.summary
        framework = self.health_report.framework
        timestamp = datetime.fromisoformat(self.health_report.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        total = summary.total_projects
        healthy_pct = round((summary.healthy_projects / total) * 100) if total > 0 else 0
        warning_pct = round((summary.warning_projects / total) * 100) if total > 0 else 0
        critical_pct = round((summary.critical_projects / total) * 100) if total > 0 else 0
        
        md = f"""# Claude PM Framework Health Report

**Generated**: {timestamp}

## Summary

- **Total Projects**: {total}
- **Healthy**: {summary.healthy_projects} ({healthy_pct}%)
- **Warning**: {summary.warning_projects} ({warning_pct}%)
- **Critical**: {summary.critical_projects} ({critical_pct}%)
- **Framework Compliance**: {summary.framework_compliance}%
- **Overall Health**: {summary.overall_health_percentage}%

## Framework Status
"""
        
        if framework.trackdown:
            trackdown = framework.trackdown
            md += f"""
### TrackDown System
- **Total Tickets**: {trackdown['total_tickets']}
- **Completed**: {trackdown['completed_tickets']} ({trackdown['completion_rate']}%)
- **Pending**: {trackdown['pending_tickets']}
- **Last Update**: {trackdown['last_update_days']} days ago
- **Status**: {trackdown['health_status']}
"""
        
        md += f"""
## Services Status

{chr(10).join(f"- **{name}**: {service.status}" + (f" ({service.response_time}ms)" if service.response_time else "") for name, service in self.health_report.services.items())}

## Recommendations

{chr(10).join(f"- {rec}" for rec in self.health_report.recommendations)}

## Critical Issues

{chr(10).join(f"- **{name}**: {', '.join(project.issues)}" for name, project in self.health_report.projects.items() if project.status in ['error', 'critical']) or "None"}

---
*Report generated by Claude PM Automated Health Monitor (Python Version)*
"""
        return md
    
    def _save_monitor_status(self) -> None:
        """Save monitor status to file."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.monitor_status, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save monitor status: {e}")
    
    def get_monitor_status(self) -> Optional[Dict]:
        """Get current monitor status."""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to read monitor status: {e}")
        return None
    
    async def start_continuous_monitoring(self) -> None:
        """Start continuous health monitoring."""
        self.logger.info(f"Starting continuous health monitoring (interval: {self.config['check_interval']}s)")
        
        # Run initial check
        await self.run_health_check()
        
        # Set up periodic monitoring
        while True:
            await asyncio.sleep(self.config["check_interval"])
            await self.run_health_check()
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


# CLI Commands using Click
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--no-alerts', is_flag=True, help='Disable alert notifications')
@click.option('--no-services', is_flag=True, help='Skip service health checks')
@click.option('--no-git', is_flag=True, help='Skip git repository checks')
@click.option('--interval', default=5, help='Monitoring interval in minutes')
@click.option('--threshold', default=60, help='Alert threshold percentage')
@click.pass_context
def cli(ctx, verbose, no_alerts, no_services, no_git, interval, threshold):
    """Claude PM Enhanced Automated Health Monitor (Python Version)"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = {
        'verbose_logging': verbose,
        'enable_alerting': not no_alerts,
        'enable_service_checks': not no_services,
        'enable_git_checks': not no_git,
        'check_interval': interval * 60,  # Convert to seconds
        'alert_threshold': threshold
    }

@cli.command()
@click.pass_context
async def once(ctx):
    """Run single health check"""
    monitor = ClaudePMHealthMonitor(ctx.obj['config'])
    
    console.print("[bold blue]🏥 Running health check...[/bold blue]")
    
    await monitor.run_health_check()
    
    # Display results
    summary = monitor.health_report.summary
    
    table = Table(title="Health Check Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")
    
    table.add_row("Overall Health", f"{summary.overall_health_percentage}%", 
                  "✅ Good" if summary.overall_health_percentage >= 80 else "⚠️ Warning" if summary.overall_health_percentage >= 60 else "❌ Critical")
    table.add_row("Total Projects", str(summary.total_projects), "")
    table.add_row("Healthy Projects", str(summary.healthy_projects), "")
    table.add_row("Warning Projects", str(summary.warning_projects), "")
    table.add_row("Critical Projects", str(summary.critical_projects), "")
    table.add_row("Framework Compliance", f"{summary.framework_compliance}%", "")
    
    console.print(table)
    
    if monitor.health_report.alerts:
        console.print(f"\n🚨 [bold red]{len(monitor.health_report.alerts)} Alerts Generated[/bold red]")
        for alert in monitor.health_report.alerts[-3:]:  # Show last 3 alerts
            console.print(f"  [{alert.level.upper()}] {alert.message}")
    
    console.print(f"\n📊 Reports saved to:")
    console.print(f"  📝 JSON Report: {monitor.logs_dir}/health-report.json")
    console.print(f"  📋 Summary: {monitor.logs_dir}/health-summary.md")

@cli.command()
@click.pass_context
async def monitor(ctx):
    """Start continuous monitoring"""
    monitor = ClaudePMHealthMonitor(ctx.obj['config'])
    monitor.setup_signal_handlers()
    
    console.print("[bold blue]🔄 Starting continuous health monitoring...[/bold blue]")
    console.print(f"📊 Check interval: {ctx.obj['config']['check_interval']} seconds")
    console.print(f"🚨 Alert threshold: {ctx.obj['config']['alert_threshold']}%")
    console.print("💡 Use Ctrl+C to stop monitoring\n")
    
    await monitor.start_continuous_monitoring()

@cli.command()
@click.pass_context
def status(ctx):
    """Show monitor status and latest health summary"""
    monitor = ClaudePMHealthMonitor(ctx.obj['config'])
    status = monitor.get_monitor_status()
    
    if status:
        console.print("📊 [bold]Monitor Status[/bold]:")
        console.print(f"  PID: {status['pid']}")
        console.print(f"  Started: {status['start_time']}")
        console.print(f"  Last Check: {status.get('last_check', 'Never')}")
        console.print(f"  Checks Run: {status['checks_run']}")
        console.print(f"  Alerts Sent: {status['alerts_sent']}")
        
        # Show latest health summary if available
        report_path = monitor.logs_dir / "health-report.json"
        if report_path.exists():
            try:
                with open(report_path, 'r') as f:
                    report = json.load(f)
                
                console.print("\n📈 [bold]Latest Health Summary[/bold]:")
                summary = report['summary']
                console.print(f"  Overall Health: {summary['overall_health_percentage']}%")
                console.print(f"  Total Projects: {summary['total_projects']}")
                console.print(f"  Healthy Projects: {summary['healthy_projects']}")
                console.print(f"  Warning Projects: {summary['warning_projects']}")
                console.print(f"  Critical Projects: {summary['critical_projects']}")
                console.print(f"  Framework Compliance: {summary['framework_compliance']}%")
                
                if report.get('alerts'):
                    console.print(f"\n🚨 Recent Alerts: {len(report['alerts'])}")
                    for alert in report['alerts'][-3:]:
                        console.print(f"  [{alert['level'].upper()}] {alert['message']}")
                        
            except Exception as e:
                console.print(f"  Error reading health report: {e}")
    else:
        console.print("❌ No monitoring status found. Monitor may not be running.")

@cli.command()
@click.pass_context  
def reports(ctx):
    """List available health reports"""
    monitor = ClaudePMHealthMonitor(ctx.obj['config'])
    
    if monitor.logs_dir.exists():
        console.print("📁 [bold]Available Health Reports[/bold]:")
        
        health_files = [f for f in monitor.logs_dir.iterdir() if 'health' in f.name]
        
        if health_files:
            table = Table()
            table.add_column("File", style="cyan")
            table.add_column("Size", style="magenta") 
            table.add_column("Modified", style="green")
            
            for file_path in sorted(health_files, key=lambda x: x.stat().st_mtime, reverse=True):
                stats = file_path.stat()
                size = f"{stats.st_size} bytes"
                modified = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                table.add_row(file_path.name, size, modified)
            
            console.print(table)
        else:
            console.print("  No health reports found.")
    else:
        console.print("❌ No logs directory found.")

@cli.command()
@click.pass_context
def alerts(ctx):
    """Show recent health alerts"""
    monitor = ClaudePMHealthMonitor(ctx.obj['config'])
    
    if monitor.alert_log.exists():
        console.print("🚨 [bold]Recent Health Alerts[/bold]:")
        
        try:
            with open(monitor.alert_log, 'r') as f:
                alerts = f.read().strip().split('\n')
            
            if alerts and alerts[0]:  # Check if there are actual alerts
                for alert in alerts[-10:]:  # Show last 10 alerts
                    console.print(f"  {alert}")
            else:
                console.print("  No alerts found.")
                
        except Exception as e:
            console.print(f"  Error reading alerts: {e}")
    else:
        console.print("✅ No alerts found.")

if __name__ == '__main__':
    # Run the CLI with asyncio support
    import asyncio
    
    def run_async_command():
        """Wrapper to run async commands from click"""
        if len(sys.argv) > 1:
            command = sys.argv[1]
            if command in ['once', 'monitor']:
                # For async commands, we need to handle them specially
                async def main():
                    if command == 'once':
                        await once.callback()
                    elif command == 'monitor':
                        await monitor.callback()
                
                asyncio.run(main())
            else:
                cli()
        else:
            cli()
    
    try:
        # Check if we're running an async command
        if len(sys.argv) > 1 and sys.argv[1] in ['once', 'monitor']:
            # Create a simple argument parser for async commands
            parser = argparse.ArgumentParser(description='Claude PM Health Monitor')
            parser.add_argument('command', choices=['once', 'monitor'])
            parser.add_argument('--verbose', '-v', action='store_true')
            parser.add_argument('--no-alerts', action='store_true')
            parser.add_argument('--no-services', action='store_true')
            parser.add_argument('--no-git', action='store_true')
            parser.add_argument('--interval', type=int, default=5)
            parser.add_argument('--threshold', type=int, default=60)
            
            args = parser.parse_args()
            
            config = {
                'verbose_logging': args.verbose,
                'enable_alerting': not args.no_alerts,
                'enable_service_checks': not args.no_services,
                'enable_git_checks': not args.no_git,
                'check_interval': args.interval * 60,
                'alert_threshold': args.threshold
            }
            
            monitor = ClaudePMHealthMonitor(config)
            
            if args.command == 'once':
                asyncio.run(monitor.run_health_check())
                
                # Display results
                summary = monitor.health_report.summary
                console.print("\n📊 [bold]Health Check Results[/bold]")
                console.print(f"Overall Health: {summary.overall_health_percentage}%")
                console.print(f"Total Projects: {summary.total_projects}")
                console.print(f"Healthy: {summary.healthy_projects} | Warning: {summary.warning_projects} | Critical: {summary.critical_projects}")
                console.print(f"Framework Compliance: {summary.framework_compliance}%")
                
                if monitor.health_report.alerts:
                    console.print(f"\n🚨 {len(monitor.health_report.alerts)} alerts generated")
                
                console.print(f"\n📝 Reports saved to {monitor.logs_dir}/")
                
            elif args.command == 'monitor':
                monitor.setup_signal_handlers()
                console.print("🔄 Starting continuous monitoring... (Ctrl+C to stop)")
                asyncio.run(monitor.start_continuous_monitoring())
        else:
            cli()
    except KeyboardInterrupt:
        console.print("\n👋 Health monitoring stopped.")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Error: {e}")
        sys.exit(1)