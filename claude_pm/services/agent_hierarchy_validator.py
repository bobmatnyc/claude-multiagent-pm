#!/usr/bin/env python3
"""
Agent Hierarchy Validator and Status Reporter for Claude PM Framework
===================================================================

This service provides comprehensive validation and status reporting for the
three-tier agent hierarchy system.

Key Features:
- Hierarchy consistency validation
- Agent health monitoring and reporting
- Configuration validation across tiers
- Performance metrics and analysis
- Status dashboard generation
- Automated health checks
- Issue detection and resolution recommendations
"""

import asyncio
import json
import yaml
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.base_service import BaseService
from ..core.logging_config import setup_logging
from ..agents.hierarchical_agent_loader import HierarchicalAgentLoader, AgentInfo
from ..core.agent_config import AgentConfigurationManager
from ..services.agent_discovery_service import AgentDiscoveryService


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue in the agent hierarchy."""
    issue_id: str
    severity: ValidationSeverity
    category: str
    title: str
    description: str
    affected_agents: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    auto_fixable: bool = False
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "issue_id": self.issue_id,
            "severity": self.severity.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "affected_agents": self.affected_agents,
            "recommendations": self.recommendations,
            "auto_fixable": self.auto_fixable,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class AgentHealthReport:
    """Comprehensive health report for an agent."""
    agent_name: str
    agent_type: str
    tier: str
    health_status: str
    last_check: datetime
    response_time: float
    memory_usage: float
    cpu_usage: float
    error_count: int
    warning_count: int
    uptime: float
    last_restart: Optional[datetime] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "tier": self.tier,
            "health_status": self.health_status,
            "last_check": self.last_check.isoformat(),
            "response_time": self.response_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "uptime": self.uptime,
            "last_restart": self.last_restart.isoformat() if self.last_restart else None,
            "custom_metrics": self.custom_metrics
        }


@dataclass
class HierarchyValidationReport:
    """Comprehensive validation report for the agent hierarchy."""
    report_id: str
    generated_at: datetime
    validation_duration: float
    overall_health: str
    total_agents: int
    healthy_agents: int
    unhealthy_agents: int
    issues: List[ValidationIssue] = field(default_factory=list)
    agent_reports: List[AgentHealthReport] = field(default_factory=list)
    tier_summary: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "validation_duration": self.validation_duration,
            "overall_health": self.overall_health,
            "total_agents": self.total_agents,
            "healthy_agents": self.healthy_agents,
            "unhealthy_agents": self.unhealthy_agents,
            "issues": [issue.to_dict() for issue in self.issues],
            "agent_reports": [report.to_dict() for report in self.agent_reports],
            "tier_summary": self.tier_summary,
            "performance_metrics": self.performance_metrics,
            "recommendations": self.recommendations
        }


class AgentHierarchyValidator(BaseService):
    """
    Service for validating and monitoring the agent hierarchy.
    
    This service provides:
    - Comprehensive hierarchy validation
    - Agent health monitoring
    - Performance metrics collection
    - Issue detection and reporting
    - Automated health checks
    - Status dashboard generation
    """
    
    def __init__(
        self,
        agent_loader: HierarchicalAgentLoader,
        config_manager: AgentConfigurationManager,
        discovery_service: AgentDiscoveryService,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name="agent_hierarchy_validator", config=config)
        
        self.agent_loader = agent_loader
        self.config_manager = config_manager
        self.discovery_service = discovery_service
        
        # Validation state
        self.last_validation_time: Optional[datetime] = None
        self.validation_history: List[HierarchyValidationReport] = []
        self.known_issues: Dict[str, ValidationIssue] = {}
        
        # Health monitoring
        self.health_history: Dict[str, List[AgentHealthReport]] = {}
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        
        # Validation rules
        self.validation_rules = self._initialize_validation_rules()
        
        # Reports storage
        self.reports_path = Path.cwd() / ".claude-multiagent-pm" / "reports"
        self.reports_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Initialized AgentHierarchyValidator")
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for the hierarchy."""
        return {
            "tier_structure": {
                "required_directories": [
                    "system_agents",
                    "user_agents", 
                    "project_agents"
                ],
                "required_files": [
                    "hierarchy.yaml",
                    "registry.json"
                ]
            },
            "agent_requirements": {
                "required_methods": [
                    "__init__",
                    "initialize",
                    "cleanup"
                ],
                "required_attributes": [
                    "name",
                    "agent_type"
                ]
            },
            "performance_thresholds": {
                "max_response_time": 5.0,
                "max_memory_usage": 500.0,  # MB
                "max_cpu_usage": 80.0,      # Percent
                "max_error_rate": 0.05      # 5%
            },
            "health_check_intervals": {
                "fast_check": 30,     # seconds
                "full_check": 300,    # seconds
                "deep_check": 3600    # seconds
            }
        }
    
    async def _initialize(self) -> None:
        """Initialize the hierarchy validator."""
        try:
            # Start periodic validation
            if self.get_config("auto_validation_enabled", True):
                self.start_periodic_validation()
            
            # Start health monitoring
            if self.get_config("health_monitoring_enabled", True):
                self.start_health_monitoring()
            
            # Load validation history
            await self.load_validation_history()
            
            self.logger.info("AgentHierarchyValidator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentHierarchyValidator: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup the hierarchy validator."""
        try:
            # Save validation history
            await self.save_validation_history()
            
            # Save final health reports
            await self.save_health_reports()
            
            self.logger.info("AgentHierarchyValidator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup AgentHierarchyValidator: {e}")
            raise
    
    def start_periodic_validation(self) -> None:
        """Start periodic validation tasks."""
        # Fast validation (basic health checks)
        fast_interval = self.validation_rules["health_check_intervals"]["fast_check"]
        fast_task = asyncio.create_task(self._periodic_fast_validation(fast_interval))
        self._background_tasks.append(fast_task)
        
        # Full validation (comprehensive checks)
        full_interval = self.validation_rules["health_check_intervals"]["full_check"]
        full_task = asyncio.create_task(self._periodic_full_validation(full_interval))
        self._background_tasks.append(full_task)
        
        # Deep validation (performance analysis)
        deep_interval = self.validation_rules["health_check_intervals"]["deep_check"]
        deep_task = asyncio.create_task(self._periodic_deep_validation(deep_interval))
        self._background_tasks.append(deep_task)
        
        self.logger.info("Started periodic validation tasks")
    
    def start_health_monitoring(self) -> None:
        """Start health monitoring tasks."""
        monitoring_interval = self.get_config("health_monitoring_interval", 60)
        
        async def health_monitoring_task():
            while not self._stop_event.is_set():
                try:
                    await self.collect_agent_health_metrics()
                    await asyncio.sleep(monitoring_interval)
                except Exception as e:
                    self.logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(monitoring_interval)
        
        task = asyncio.create_task(health_monitoring_task())
        self._background_tasks.append(task)
        
        self.logger.info("Started health monitoring")
    
    async def _periodic_fast_validation(self, interval: int) -> None:
        """Perform periodic fast validation."""
        while not self._stop_event.is_set():
            try:
                await self.validate_agent_availability()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Fast validation error: {e}")
                await asyncio.sleep(interval)
    
    async def _periodic_full_validation(self, interval: int) -> None:
        """Perform periodic full validation."""
        while not self._stop_event.is_set():
            try:
                await self.validate_hierarchy_comprehensive()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Full validation error: {e}")
                await asyncio.sleep(interval)
    
    async def _periodic_deep_validation(self, interval: int) -> None:
        """Perform periodic deep validation."""
        while not self._stop_event.is_set():
            try:
                await self.validate_hierarchy_deep()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Deep validation error: {e}")
                await asyncio.sleep(interval)
    
    async def validate_agent_availability(self) -> Dict[str, Any]:
        """Perform fast validation of agent availability."""
        validation_start = time.time()
        
        try:
            hierarchy = self.agent_loader.hierarchy
            all_agents = hierarchy.get_all_agents()
            
            availability_results = {
                "total_agents": len(all_agents),
                "available_agents": 0,
                "unavailable_agents": 0,
                "agents_by_tier": {
                    "system": {"available": 0, "unavailable": 0},
                    "user": {"available": 0, "unavailable": 0},
                    "project": {"available": 0, "unavailable": 0}
                },
                "validation_time": 0
            }
            
            for agent_name, agent_info in all_agents.items():
                is_available = await self._check_agent_availability(agent_info)
                
                if is_available:
                    availability_results["available_agents"] += 1
                    availability_results["agents_by_tier"][agent_info.tier]["available"] += 1
                else:
                    availability_results["unavailable_agents"] += 1
                    availability_results["agents_by_tier"][agent_info.tier]["unavailable"] += 1
            
            availability_results["validation_time"] = time.time() - validation_start
            
            return availability_results
            
        except Exception as e:
            self.logger.error(f"Agent availability validation failed: {e}")
            return {
                "error": str(e),
                "validation_time": time.time() - validation_start
            }
    
    async def _check_agent_availability(self, agent_info: AgentInfo) -> bool:
        """Check if an agent is available."""
        try:
            # Check if agent file exists
            if not agent_info.path.exists():
                return False
            
            # Check if agent is loadable (basic syntax check)
            try:
                with open(agent_info.path, 'r') as f:
                    content = f.read()
                    compile(content, str(agent_info.path), 'exec')
                return True
            except SyntaxError:
                return False
            
        except Exception:
            return False
    
    async def validate_hierarchy_comprehensive(self) -> HierarchyValidationReport:
        """Perform comprehensive hierarchy validation."""
        validation_start = time.time()
        report_id = f"validation_{int(time.time())}"
        
        try:
            issues = []
            agent_reports = []
            
            # Validate directory structure
            structure_issues = await self._validate_directory_structure()
            issues.extend(structure_issues)
            
            # Validate agent configurations
            config_issues = await self._validate_agent_configurations()
            issues.extend(config_issues)
            
            # Validate agent hierarchy consistency
            hierarchy_issues = await self._validate_hierarchy_consistency()
            issues.extend(hierarchy_issues)
            
            # Collect agent health reports
            agent_reports = await self._collect_agent_health_reports()
            
            # Generate tier summary
            tier_summary = self._generate_tier_summary()
            
            # Generate performance metrics
            performance_metrics = await self._collect_performance_metrics()
            
            # Generate recommendations
            recommendations = self._generate_recommendations(issues)
            
            # Calculate overall health
            overall_health = self._calculate_overall_health(issues, agent_reports)
            
            # Create validation report
            report = HierarchyValidationReport(
                report_id=report_id,
                generated_at=datetime.now(),
                validation_duration=time.time() - validation_start,
                overall_health=overall_health,
                total_agents=len(self.agent_loader.hierarchy.get_all_agents()),
                healthy_agents=len([r for r in agent_reports if r.health_status == "healthy"]),
                unhealthy_agents=len([r for r in agent_reports if r.health_status != "healthy"]),
                issues=issues,
                agent_reports=agent_reports,
                tier_summary=tier_summary,
                performance_metrics=performance_metrics,
                recommendations=recommendations
            )
            
            # Store validation report
            self.validation_history.append(report)
            self.last_validation_time = datetime.now()
            
            # Update known issues
            self._update_known_issues(issues)
            
            # Save report
            await self.save_validation_report(report)
            
            self.logger.info(f"Comprehensive validation completed in {report.validation_duration:.2f}s")
            self.logger.info(f"Overall health: {overall_health}, Issues: {len(issues)}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Comprehensive validation failed: {e}")
            
            # Create error report
            error_report = HierarchyValidationReport(
                report_id=report_id,
                generated_at=datetime.now(),
                validation_duration=time.time() - validation_start,
                overall_health="error",
                total_agents=0,
                healthy_agents=0,
                unhealthy_agents=0,
                issues=[ValidationIssue(
                    issue_id=f"validation_error_{int(time.time())}",
                    severity=ValidationSeverity.CRITICAL,
                    category="validation",
                    title="Validation Process Failed",
                    description=f"Validation process failed with error: {str(e)}",
                    recommendations=["Check validator configuration", "Review system logs"]
                )]
            )
            
            return error_report
    
    async def validate_hierarchy_deep(self) -> Dict[str, Any]:
        """Perform deep validation with performance analysis."""
        validation_start = time.time()
        
        try:
            deep_analysis = {
                "performance_analysis": await self._analyze_agent_performance(),
                "resource_usage": await self._analyze_resource_usage(),
                "dependency_analysis": await self._analyze_agent_dependencies(),
                "security_analysis": await self._analyze_security_posture(),
                "optimization_recommendations": [],
                "validation_time": 0
            }
            
            # Generate optimization recommendations
            deep_analysis["optimization_recommendations"] = self._generate_optimization_recommendations(
                deep_analysis
            )
            
            deep_analysis["validation_time"] = time.time() - validation_start
            
            return deep_analysis
            
        except Exception as e:
            self.logger.error(f"Deep validation failed: {e}")
            return {
                "error": str(e),
                "validation_time": time.time() - validation_start
            }
    
    async def _validate_directory_structure(self) -> List[ValidationIssue]:
        """Validate the directory structure of the hierarchy."""
        issues = []
        
        # Check required directories
        required_dirs = [
            self.agent_loader.system_agents_path,
            self.agent_loader.user_agents_path,
            self.agent_loader.project_agents_path
        ]
        
        for directory in required_dirs:
            if not directory.exists():
                issues.append(ValidationIssue(
                    issue_id=f"missing_dir_{directory.name}",
                    severity=ValidationSeverity.ERROR,
                    category="directory_structure",
                    title=f"Missing Directory: {directory.name}",
                    description=f"Required directory does not exist: {directory}",
                    recommendations=[f"Create directory: {directory}"],
                    auto_fixable=True
                ))
        
        return issues
    
    async def _validate_agent_configurations(self) -> List[ValidationIssue]:
        """Validate agent configurations."""
        issues = []
        
        try:
            # Get all agent profiles
            agent_types = self.config_manager.get_all_agent_types()
            
            for agent_type in agent_types:
                profile = self.config_manager.get_agent_profile(agent_type)
                
                if profile and profile.validation_errors:
                    issues.append(ValidationIssue(
                        issue_id=f"config_error_{agent_type}",
                        severity=ValidationSeverity.WARNING,
                        category="configuration",
                        title=f"Configuration Issues: {agent_type}",
                        description=f"Configuration validation errors: {', '.join(profile.validation_errors)}",
                        affected_agents=[agent_type],
                        recommendations=["Review agent configuration", "Fix validation errors"]
                    ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                issue_id="config_validation_error",
                severity=ValidationSeverity.ERROR,
                category="configuration",
                title="Configuration Validation Failed",
                description=f"Failed to validate configurations: {str(e)}",
                recommendations=["Check configuration manager", "Review configuration files"]
            ))
        
        return issues
    
    async def _validate_hierarchy_consistency(self) -> List[ValidationIssue]:
        """Validate hierarchy consistency."""
        issues = []
        
        try:
            hierarchy = self.agent_loader.hierarchy
            
            # Check for agent type conflicts
            agent_types = {}
            for agent_info in hierarchy.get_all_agents().values():
                if agent_info.agent_type not in agent_types:
                    agent_types[agent_info.agent_type] = []
                agent_types[agent_info.agent_type].append(agent_info)
            
            # Check for multiple agents of same type
            for agent_type, agents in agent_types.items():
                if len(agents) > 1:
                    tiers = [agent.tier for agent in agents]
                    issues.append(ValidationIssue(
                        issue_id=f"duplicate_type_{agent_type}",
                        severity=ValidationSeverity.WARNING,
                        category="hierarchy",
                        title=f"Multiple {agent_type} Agents",
                        description=f"Multiple agents of type {agent_type} found in tiers: {', '.join(tiers)}",
                        affected_agents=[agent.name for agent in agents],
                        recommendations=["Consider consolidating agents", "Check agent precedence"]
                    ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                issue_id="hierarchy_validation_error",
                severity=ValidationSeverity.ERROR,
                category="hierarchy",
                title="Hierarchy Validation Failed",
                description=f"Failed to validate hierarchy: {str(e)}",
                recommendations=["Check hierarchy loader", "Review agent structure"]
            ))
        
        return issues
    
    async def _collect_agent_health_reports(self) -> List[AgentHealthReport]:
        """Collect health reports for all agents."""
        reports = []
        
        try:
            loaded_agents = self.agent_loader.get_loaded_agents()
            
            for agent_type, agent_instance in loaded_agents.items():
                try:
                    report = await self._generate_agent_health_report(agent_type, agent_instance)
                    reports.append(report)
                except Exception as e:
                    self.logger.error(f"Failed to generate health report for {agent_type}: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to collect agent health reports: {e}")
        
        return reports
    
    async def _generate_agent_health_report(self, agent_type: str, agent_instance: Any) -> AgentHealthReport:
        """Generate health report for a specific agent."""
        try:
            # Get agent info
            agent_info = self.agent_loader.hierarchy.get_agent_by_type(agent_type)
            
            # Basic health check
            health_status = "healthy"
            response_time = 0.0
            
            if hasattr(agent_instance, 'health_check'):
                start_time = time.time()
                
                try:
                    if asyncio.iscoroutinefunction(agent_instance.health_check):
                        health_result = await agent_instance.health_check()
                    else:
                        health_result = agent_instance.health_check()
                    
                    response_time = time.time() - start_time
                    
                    if isinstance(health_result, dict):
                        health_status = "healthy" if health_result.get("healthy", True) else "unhealthy"
                    else:
                        health_status = "healthy" if health_result else "unhealthy"
                        
                except Exception as e:
                    health_status = "error"
                    response_time = time.time() - start_time
            
            # Create health report
            report = AgentHealthReport(
                agent_name=agent_info.name if agent_info else agent_type,
                agent_type=agent_type,
                tier=agent_info.tier if agent_info else "unknown",
                health_status=health_status,
                last_check=datetime.now(),
                response_time=response_time,
                memory_usage=0.0,  # TODO: Implement memory monitoring
                cpu_usage=0.0,     # TODO: Implement CPU monitoring
                error_count=0,     # TODO: Implement error tracking
                warning_count=0,   # TODO: Implement warning tracking
                uptime=0.0         # TODO: Implement uptime tracking
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate health report for {agent_type}: {e}")
            
            # Return error report
            return AgentHealthReport(
                agent_name=agent_type,
                agent_type=agent_type,
                tier="unknown",
                health_status="error",
                last_check=datetime.now(),
                response_time=0.0,
                memory_usage=0.0,
                cpu_usage=0.0,
                error_count=1,
                warning_count=0,
                uptime=0.0
            )
    
    def _generate_tier_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for each tier."""
        hierarchy = self.agent_loader.hierarchy
        
        return {
            "system": {
                "total_agents": len(hierarchy.system_agents),
                "agent_types": list(set(agent.agent_type for agent in hierarchy.system_agents.values())),
                "loaded_agents": len([agent for agent in hierarchy.system_agents.values() if agent.loaded])
            },
            "user": {
                "total_agents": len(hierarchy.user_agents),
                "agent_types": list(set(agent.agent_type for agent in hierarchy.user_agents.values())),
                "loaded_agents": len([agent for agent in hierarchy.user_agents.values() if agent.loaded])
            },
            "project": {
                "total_agents": len(hierarchy.project_agents),
                "agent_types": list(set(agent.agent_type for agent in hierarchy.project_agents.values())),
                "loaded_agents": len([agent for agent in hierarchy.project_agents.values() if agent.loaded])
            }
        }
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics for the hierarchy."""
        return {
            "agent_load_time": 0.0,     # TODO: Implement load time tracking
            "memory_usage": 0.0,        # TODO: Implement memory monitoring
            "cpu_usage": 0.0,           # TODO: Implement CPU monitoring
            "response_times": {},       # TODO: Implement response time tracking
            "error_rates": {},          # TODO: Implement error rate tracking
            "throughput": 0.0           # TODO: Implement throughput monitoring
        }
    
    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate recommendations based on validation issues."""
        recommendations = []
        
        # Count issues by severity
        severity_counts = {}
        for issue in issues:
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate recommendations based on issue patterns
        if severity_counts.get("critical", 0) > 0:
            recommendations.append("Address critical issues immediately")
        
        if severity_counts.get("error", 0) > 0:
            recommendations.append("Fix error-level issues to improve stability")
        
        if severity_counts.get("warning", 0) > 3:
            recommendations.append("Review warning-level issues for potential improvements")
        
        # Add specific recommendations
        auto_fixable_issues = [issue for issue in issues if issue.auto_fixable]
        if auto_fixable_issues:
            recommendations.append(f"Consider auto-fixing {len(auto_fixable_issues)} issues")
        
        return recommendations
    
    def _calculate_overall_health(self, issues: List[ValidationIssue], agent_reports: List[AgentHealthReport]) -> str:
        """Calculate overall health status."""
        # Check for critical issues
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            return "critical"
        
        # Check for error issues
        error_issues = [issue for issue in issues if issue.severity == ValidationSeverity.ERROR]
        if error_issues:
            return "unhealthy"
        
        # Check agent health
        unhealthy_agents = [report for report in agent_reports if report.health_status != "healthy"]
        if unhealthy_agents:
            total_agents = len(agent_reports)
            unhealthy_percentage = len(unhealthy_agents) / total_agents if total_agents > 0 else 0
            
            if unhealthy_percentage > 0.5:
                return "unhealthy"
            elif unhealthy_percentage > 0.2:
                return "degraded"
        
        # Check for warnings
        warning_issues = [issue for issue in issues if issue.severity == ValidationSeverity.WARNING]
        if warning_issues:
            return "warning"
        
        return "healthy"
    
    def _update_known_issues(self, issues: List[ValidationIssue]) -> None:
        """Update the cache of known issues."""
        # Clear resolved issues
        current_issue_ids = {issue.issue_id for issue in issues}
        resolved_issues = set(self.known_issues.keys()) - current_issue_ids
        
        for issue_id in resolved_issues:
            del self.known_issues[issue_id]
        
        # Add new issues
        for issue in issues:
            self.known_issues[issue.issue_id] = issue
    
    async def collect_agent_health_metrics(self) -> Dict[str, Any]:
        """Collect health metrics for all agents."""
        try:
            health_metrics = {
                "timestamp": datetime.now().isoformat(),
                "total_agents": len(self.agent_loader.hierarchy.get_all_agents()),
                "loaded_agents": len(self.agent_loader.get_loaded_agents()),
                "agent_health": {}
            }
            
            # Collect health from loaded agents
            loaded_agents = self.agent_loader.get_loaded_agents()
            for agent_type, agent_instance in loaded_agents.items():
                try:
                    health_report = await self._generate_agent_health_report(agent_type, agent_instance)
                    health_metrics["agent_health"][agent_type] = health_report.to_dict()
                except Exception as e:
                    self.logger.error(f"Failed to collect health metrics for {agent_type}: {e}")
            
            return health_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect agent health metrics: {e}")
            return {"error": str(e)}
    
    async def save_validation_report(self, report: HierarchyValidationReport) -> None:
        """Save validation report to disk."""
        try:
            report_file = self.reports_path / f"validation_{report.report_id}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)
            
            self.logger.debug(f"Saved validation report: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")
    
    async def load_validation_history(self) -> None:
        """Load validation history from disk."""
        try:
            # Load recent validation reports
            report_files = list(self.reports_path.glob("validation_*.json"))
            report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Load last 10 reports
            for report_file in report_files[:10]:
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    
                    # Convert back to report object (simplified)
                    # TODO: Implement full deserialization
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load validation report {report_file}: {e}")
            
            self.logger.info(f"Loaded {len(self.validation_history)} validation reports")
            
        except Exception as e:
            self.logger.error(f"Failed to load validation history: {e}")
    
    async def save_validation_history(self) -> None:
        """Save validation history to disk."""
        try:
            # Keep only recent reports
            recent_reports = self.validation_history[-10:]
            
            for report in recent_reports:
                await self.save_validation_report(report)
            
            self.logger.info(f"Saved {len(recent_reports)} validation reports")
            
        except Exception as e:
            self.logger.error(f"Failed to save validation history: {e}")
    
    async def save_health_reports(self) -> None:
        """Save health reports to disk."""
        try:
            health_file = self.reports_path / "health_history.json"
            
            # Convert health history to serializable format
            health_data = {}
            for agent_type, reports in self.health_history.items():
                health_data[agent_type] = [report.to_dict() for report in reports[-10:]]  # Keep last 10
            
            with open(health_file, 'w') as f:
                json.dump(health_data, f, indent=2)
            
            self.logger.info("Saved health reports")
            
        except Exception as e:
            self.logger.error(f"Failed to save health reports: {e}")
    
    async def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status."""
        latest_report = self.validation_history[-1] if self.validation_history else None
        
        return {
            "service_status": "running" if self.running else "stopped",
            "last_validation": self.last_validation_time.isoformat() if self.last_validation_time else None,
            "validation_history_count": len(self.validation_history),
            "known_issues_count": len(self.known_issues),
            "latest_overall_health": latest_report.overall_health if latest_report else "unknown",
            "health_monitoring_active": True  # TODO: Check actual monitoring status
        }
    
    async def _analyze_agent_performance(self) -> Dict[str, Any]:
        """Analyze agent performance metrics."""
        # TODO: Implement performance analysis
        return {"placeholder": "performance analysis not implemented"}
    
    async def _analyze_resource_usage(self) -> Dict[str, Any]:
        """Analyze resource usage patterns."""
        # TODO: Implement resource usage analysis
        return {"placeholder": "resource usage analysis not implemented"}
    
    async def _analyze_agent_dependencies(self) -> Dict[str, Any]:
        """Analyze agent dependencies."""
        # TODO: Implement dependency analysis
        return {"placeholder": "dependency analysis not implemented"}
    
    async def _analyze_security_posture(self) -> Dict[str, Any]:
        """Analyze security posture of the hierarchy."""
        # TODO: Implement security analysis
        return {"placeholder": "security analysis not implemented"}
    
    def _generate_optimization_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations."""
        # TODO: Implement optimization recommendations
        return ["Performance optimization recommendations not implemented"]
    
    async def _health_check(self) -> Dict[str, bool]:
        """Custom health checks for the validator."""
        checks = {}
        
        # Check if validation is running
        checks["validation_active"] = self.last_validation_time is not None
        
        # Check if there are recent validations
        if self.last_validation_time:
            time_since_last = datetime.now() - self.last_validation_time
            checks["recent_validation"] = time_since_last.total_seconds() < 3600  # Within last hour
        else:
            checks["recent_validation"] = False
        
        # Check for critical issues
        critical_issues = [issue for issue in self.known_issues.values() if issue.severity == ValidationSeverity.CRITICAL]
        checks["no_critical_issues"] = len(critical_issues) == 0
        
        # Check reports directory
        checks["reports_directory_exists"] = self.reports_path.exists()
        
        return checks