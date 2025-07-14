"""
Memory Collection Health Monitor

This module provides comprehensive health monitoring and diagnostics for the memory
collection system across all agents in the Claude PM Framework.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .services.unified_service import FlexibleMemoryService
from .memory_trigger_service import MemoryTriggerService
from .interfaces.models import MemoryCategory, HealthStatus
from .interfaces.exceptions import MemoryServiceError


class HealthLevel(Enum):
    """Memory system health levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric."""
    name: str
    value: Any
    threshold: Optional[float] = None
    status: HealthLevel = HealthLevel.UNKNOWN
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentHealthReport:
    """Health report for a single agent."""
    agent_id: str
    agent_type: str
    overall_health: HealthLevel
    metrics: List[HealthMetric] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    last_check_time: datetime = field(default_factory=datetime.now)


@dataclass
class SystemHealthReport:
    """Overall system health report."""
    overall_health: HealthLevel
    agent_reports: Dict[str, AgentHealthReport] = field(default_factory=dict)
    system_metrics: List[HealthMetric] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    report_time: datetime = field(default_factory=datetime.now)


class MemoryHealthMonitor:
    """
    Comprehensive health monitoring for memory collection system.
    
    Provides real-time health monitoring, issue detection, performance analysis,
    and automated diagnostics for memory collection across all agents.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize memory health monitor.
        
        Args:
            config: Health monitoring configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Monitoring configuration
        self.monitoring_enabled = self.config.get("enabled", True)
        self.check_interval = self.config.get("check_interval", 60)  # seconds
        self.history_retention = self.config.get("history_retention", 24 * 60 * 60)  # 24 hours
        
        # Health thresholds
        self.thresholds = {
            "memory_response_time": self.config.get("memory_response_threshold", 5.0),  # seconds
            "error_rate": self.config.get("error_rate_threshold", 0.05),  # 5%
            "agent_registration_rate": self.config.get("agent_registration_threshold", 0.9),  # 90%
            "memory_storage_usage": self.config.get("storage_usage_threshold", 0.8),  # 80%
            "circuit_breaker_threshold": self.config.get("circuit_breaker_threshold", 3),  # failures
        }
        
        # Monitoring state
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_running = False
        
        # Health data
        self.health_history: List[SystemHealthReport] = []
        self.agent_health_cache: Dict[str, AgentHealthReport] = {}
        self.last_system_check: Optional[datetime] = None
        
        # Services
        self.memory_service: Optional[FlexibleMemoryService] = None
        self.memory_trigger_service: Optional[MemoryTriggerService] = None
        self.registered_agents: Dict[str, Any] = {}
    
    async def initialize(
        self,
        memory_service: FlexibleMemoryService,
        memory_trigger_service: MemoryTriggerService
    ) -> bool:
        """
        Initialize the health monitor.
        
        Args:
            memory_service: Memory service instance
            memory_trigger_service: Memory trigger service instance
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.memory_service = memory_service
            self.memory_trigger_service = memory_trigger_service
            
            if self.monitoring_enabled:
                await self.start_monitoring()
            
            self.logger.info("Memory health monitor initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory health monitor: {e}")
            return False
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._monitoring_running:
            return
        
        self._monitoring_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Memory health monitoring started")
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring."""
        self._monitoring_running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        self.logger.info("Memory health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._monitoring_running:
            try:
                await self.perform_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def perform_health_check(self) -> SystemHealthReport:
        """
        Perform comprehensive health check.
        
        Returns:
            SystemHealthReport: Complete system health report
        """
        start_time = time.time()
        
        try:
            # Create system health report
            report = SystemHealthReport(overall_health=HealthLevel.UNKNOWN)
            
            # Check memory service health
            memory_metrics = await self._check_memory_service_health()
            report.system_metrics.extend(memory_metrics)
            
            # Check agent health
            for agent_id, agent in self.registered_agents.items():
                agent_report = await self._check_agent_health(agent_id, agent)
                report.agent_reports[agent_id] = agent_report
                self.agent_health_cache[agent_id] = agent_report
            
            # Analyze overall system health
            report.overall_health = self._analyze_overall_health(report)
            
            # Generate recommendations
            report.recommendations = self._generate_recommendations(report)
            
            # Store in history
            self.health_history.append(report)
            self._cleanup_old_reports()
            
            self.last_system_check = datetime.now()
            
            # Log health status
            check_duration = time.time() - start_time
            self.logger.info(
                f"Health check completed in {check_duration:.2f}s - "
                f"Overall health: {report.overall_health.value}"
            )
            
            # Collect health check memory
            if self.memory_service:
                await self._collect_health_memory(report, check_duration)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return SystemHealthReport(
                overall_health=HealthLevel.CRITICAL,
                critical_issues=[f"Health check failed: {e}"]
            )
    
    async def _check_memory_service_health(self) -> List[HealthMetric]:
        """Check memory service health."""
        metrics = []
        
        try:
            if not self.memory_service:
                metrics.append(HealthMetric(
                    name="memory_service_available",
                    value=False,
                    status=HealthLevel.CRITICAL,
                    message="Memory service not available"
                ))
                return metrics
            
            # Check service health
            health_data = await self.memory_service.get_service_health()
            
            # Service initialization status
            metrics.append(HealthMetric(
                name="memory_service_initialized",
                value=health_data.get("service_initialized", False),
                status=HealthLevel.HEALTHY if health_data.get("service_initialized") else HealthLevel.CRITICAL,
                message="Memory service initialization status"
            ))
            
            # Active backend
            active_backend = health_data.get("active_backend")
            metrics.append(HealthMetric(
                name="active_backend",
                value=active_backend,
                status=HealthLevel.HEALTHY if active_backend else HealthLevel.WARNING,
                message=f"Active backend: {active_backend or 'None'}"
            ))
            
            # Performance metrics
            service_metrics = health_data.get("metrics", {})
            
            # Operation success rate
            total_ops = service_metrics.get("total_operations", 0)
            successful_ops = service_metrics.get("successful_operations", 0)
            success_rate = successful_ops / total_ops if total_ops > 0 else 1.0
            
            metrics.append(HealthMetric(
                name="operation_success_rate",
                value=success_rate,
                threshold=1.0 - self.thresholds["error_rate"],
                status=HealthLevel.HEALTHY if success_rate >= (1.0 - self.thresholds["error_rate"]) else HealthLevel.WARNING,
                message=f"Success rate: {success_rate:.2%}"
            ))
            
            # Circuit breaker activations
            cb_activations = service_metrics.get("circuit_breaker_activations", 0)
            metrics.append(HealthMetric(
                name="circuit_breaker_activations",
                value=cb_activations,
                threshold=self.thresholds["circuit_breaker_threshold"],
                status=HealthLevel.HEALTHY if cb_activations < self.thresholds["circuit_breaker_threshold"] else HealthLevel.WARNING,
                message=f"Circuit breaker activations: {cb_activations}"
            ))
            
            # Backend health
            backends = health_data.get("backends", {})
            healthy_backends = sum(1 for backend in backends.values() if backend.get("is_healthy"))
            total_backends = len(backends)
            
            metrics.append(HealthMetric(
                name="healthy_backends",
                value=f"{healthy_backends}/{total_backends}",
                status=HealthLevel.HEALTHY if healthy_backends > 0 else HealthLevel.CRITICAL,
                message=f"Healthy backends: {healthy_backends}/{total_backends}"
            ))
            
        except Exception as e:
            metrics.append(HealthMetric(
                name="memory_service_check_error",
                value=str(e),
                status=HealthLevel.CRITICAL,
                message=f"Error checking memory service: {e}"
            ))
        
        return metrics
    
    async def _check_agent_health(self, agent_id: str, agent: Any) -> AgentHealthReport:
        """Check health of a single agent."""
        report = AgentHealthReport(
            agent_id=agent_id,
            agent_type=getattr(agent, 'agent_type', 'unknown'),
            overall_health=HealthLevel.UNKNOWN
        )
        
        try:
            # Memory integration status
            memory_enabled = getattr(agent, 'memory_enabled', False)
            report.metrics.append(HealthMetric(
                name="memory_enabled",
                value=memory_enabled,
                status=HealthLevel.HEALTHY if memory_enabled else HealthLevel.WARNING,
                message="Memory integration enabled status"
            ))
            
            # Memory service connection
            memory_service_connected = getattr(agent, 'memory_service', None) is not None
            report.metrics.append(HealthMetric(
                name="memory_service_connected",
                value=memory_service_connected,
                status=HealthLevel.HEALTHY if memory_service_connected else HealthLevel.CRITICAL,
                message="Memory service connection status"
            ))
            
            # Auto-collect enabled
            memory_auto_collect = getattr(agent, 'memory_auto_collect', False)
            report.metrics.append(HealthMetric(
                name="memory_auto_collect",
                value=memory_auto_collect,
                status=HealthLevel.HEALTHY if memory_auto_collect else HealthLevel.WARNING,
                message="Memory auto-collect enabled status"
            ))
            
            # Memory health status
            if memory_service_connected:
                try:
                    memory_health = await agent.get_memory_health_status()
                    health_status = memory_health.get("memory_health", "unknown")
                    
                    report.metrics.append(HealthMetric(
                        name="memory_system_health",
                        value=health_status,
                        status=HealthLevel.HEALTHY if health_status == "healthy" else HealthLevel.WARNING,
                        message=f"Memory system health: {health_status}"
                    ))
                    
                    # Memory metrics
                    memory_metrics = memory_health.get("memory_metrics", {})
                    if memory_metrics:
                        report.metrics.append(HealthMetric(
                            name="memory_operations",
                            value=memory_metrics.get("total_operations", 0),
                            status=HealthLevel.HEALTHY,
                            message="Total memory operations"
                        ))
                
                except Exception as e:
                    report.metrics.append(HealthMetric(
                        name="memory_health_check_error",
                        value=str(e),
                        status=HealthLevel.WARNING,
                        message=f"Error checking memory health: {e}"
                    ))
            
            # Agent-specific health checks
            try:
                if hasattr(agent, '_health_check'):
                    agent_health = await agent._health_check()
                    
                    for check_name, check_result in agent_health.items():
                        if check_name.startswith('memory_'):
                            report.metrics.append(HealthMetric(
                                name=check_name,
                                value=check_result,
                                status=HealthLevel.HEALTHY if check_result else HealthLevel.WARNING,
                                message=f"Agent health check: {check_name}"
                            ))
                
            except Exception as e:
                report.metrics.append(HealthMetric(
                    name="agent_health_check_error",
                    value=str(e),
                    status=HealthLevel.WARNING,
                    message=f"Error in agent health check: {e}"
                ))
            
            # Determine overall agent health
            report.overall_health = self._determine_agent_health(report.metrics)
            
            # Generate agent-specific issues and recommendations
            report.issues, report.recommendations = self._analyze_agent_metrics(report.metrics)
            
        except Exception as e:
            report.overall_health = HealthLevel.CRITICAL
            report.issues.append(f"Agent health check failed: {e}")
        
        return report
    
    def _analyze_overall_health(self, report: SystemHealthReport) -> HealthLevel:
        """Analyze overall system health."""
        # Check for critical system issues
        critical_system_metrics = [m for m in report.system_metrics if m.status == HealthLevel.CRITICAL]
        if critical_system_metrics:
            report.critical_issues.extend([m.message for m in critical_system_metrics])
            return HealthLevel.CRITICAL
        
        # Check agent health
        critical_agents = [r for r in report.agent_reports.values() if r.overall_health == HealthLevel.CRITICAL]
        if critical_agents:
            report.critical_issues.extend([f"Agent {a.agent_id} in critical state" for a in critical_agents])
            return HealthLevel.CRITICAL
        
        # Check for warnings
        warning_system_metrics = [m for m in report.system_metrics if m.status == HealthLevel.WARNING]
        warning_agents = [r for r in report.agent_reports.values() if r.overall_health == HealthLevel.WARNING]
        
        if warning_system_metrics or warning_agents:
            report.warnings.extend([m.message for m in warning_system_metrics])
            report.warnings.extend([f"Agent {a.agent_id} has warnings" for a in warning_agents])
            return HealthLevel.WARNING
        
        return HealthLevel.HEALTHY
    
    def _determine_agent_health(self, metrics: List[HealthMetric]) -> HealthLevel:
        """Determine overall health for a single agent."""
        if any(m.status == HealthLevel.CRITICAL for m in metrics):
            return HealthLevel.CRITICAL
        elif any(m.status == HealthLevel.WARNING for m in metrics):
            return HealthLevel.WARNING
        elif any(m.status == HealthLevel.HEALTHY for m in metrics):
            return HealthLevel.HEALTHY
        else:
            return HealthLevel.UNKNOWN
    
    def _analyze_agent_metrics(self, metrics: List[HealthMetric]) -> tuple[List[str], List[str]]:
        """Analyze agent metrics to generate issues and recommendations."""
        issues = []
        recommendations = []
        
        for metric in metrics:
            if metric.status == HealthLevel.CRITICAL:
                issues.append(f"Critical: {metric.message}")
                
                if metric.name == "memory_service_connected" and not metric.value:
                    recommendations.append("Enable memory integration for this agent")
                
            elif metric.status == HealthLevel.WARNING:
                issues.append(f"Warning: {metric.message}")
                
                if metric.name == "memory_enabled" and not metric.value:
                    recommendations.append("Consider enabling memory collection for better insights")
                elif metric.name == "memory_auto_collect" and not metric.value:
                    recommendations.append("Enable automatic memory collection for operational insights")
        
        return issues, recommendations
    
    def _generate_recommendations(self, report: SystemHealthReport) -> List[str]:
        """Generate system-wide recommendations."""
        recommendations = []
        
        # Memory service recommendations
        memory_service_metrics = {m.name: m for m in report.system_metrics}
        
        if "memory_service_initialized" in memory_service_metrics:
            if not memory_service_metrics["memory_service_initialized"].value:
                recommendations.append("Initialize memory service to enable memory collection")
        
        if "operation_success_rate" in memory_service_metrics:
            success_rate = memory_service_metrics["operation_success_rate"].value
            if success_rate < 0.9:
                recommendations.append("Investigate memory service reliability issues")
        
        if "healthy_backends" in memory_service_metrics:
            healthy_backends = memory_service_metrics["healthy_backends"].value
            if "0/" in healthy_backends:
                recommendations.append("Check memory backend configuration and connectivity")
        
        # Agent recommendations
        total_agents = len(report.agent_reports)
        agents_with_memory = sum(
            1 for agent_report in report.agent_reports.values()
            if any(m.name == "memory_enabled" and m.value for m in agent_report.metrics)
        )
        
        if total_agents > 0 and agents_with_memory / total_agents < 0.8:
            recommendations.append("Enable memory integration on more agents for better system insights")
        
        return recommendations
    
    def _cleanup_old_reports(self):
        """Remove old health reports beyond retention period."""
        cutoff_time = datetime.now() - timedelta(seconds=self.history_retention)
        self.health_history = [
            report for report in self.health_history
            if report.report_time > cutoff_time
        ]
    
    async def _collect_health_memory(self, report: SystemHealthReport, check_duration: float):
        """Collect memory about health check results."""
        try:
            if not self.memory_service:
                return
            
            # Collect health check memory
            health_summary = {
                "overall_health": report.overall_health.value,
                "total_agents": len(report.agent_reports),
                "critical_issues_count": len(report.critical_issues),
                "warnings_count": len(report.warnings),
                "check_duration": check_duration,
                "system_metrics_count": len(report.system_metrics),
            }
            
            await self.memory_service.add_memory(
                project_name="memory_health_monitoring",
                content=f"Memory system health check - Overall status: {report.overall_health.value}",
                category=MemoryCategory.SYSTEM,
                tags=["health_check", "monitoring", "system"],
                metadata=health_summary
            )
            
            # Collect critical issues
            if report.critical_issues:
                for issue in report.critical_issues:
                    await self.memory_service.add_memory(
                        project_name="memory_health_monitoring",
                        content=f"Critical memory system issue: {issue}",
                        category=MemoryCategory.BUG,
                        tags=["critical", "health_issue", "system"],
                        metadata={"issue_type": "critical", "health_check_time": report.report_time.isoformat()}
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to collect health memory: {e}")
    
    def register_agent(self, agent_id: str, agent: Any):
        """Register an agent for health monitoring."""
        self.registered_agents[agent_id] = agent
        self.logger.info(f"Agent {agent_id} registered for health monitoring")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from health monitoring."""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
        if agent_id in self.agent_health_cache:
            del self.agent_health_cache[agent_id]
        self.logger.info(f"Agent {agent_id} unregistered from health monitoring")
    
    def get_latest_health_report(self) -> Optional[SystemHealthReport]:
        """Get the most recent health report."""
        return self.health_history[-1] if self.health_history else None
    
    def get_agent_health(self, agent_id: str) -> Optional[AgentHealthReport]:
        """Get health report for a specific agent."""
        return self.agent_health_cache.get(agent_id)
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_reports = [
            report for report in self.health_history
            if report.report_time > cutoff_time
        ]
        
        if not recent_reports:
            return {"error": "No recent health data available"}
        
        # Analyze trends
        health_levels = [report.overall_health.value for report in recent_reports]
        critical_count = health_levels.count("critical")
        warning_count = health_levels.count("warning")
        healthy_count = health_levels.count("healthy")
        
        return {
            "period_hours": hours,
            "total_checks": len(recent_reports),
            "health_distribution": {
                "healthy": healthy_count,
                "warning": warning_count,
                "critical": critical_count
            },
            "health_percentage": {
                "healthy": healthy_count / len(recent_reports) * 100,
                "warning": warning_count / len(recent_reports) * 100,
                "critical": critical_count / len(recent_reports) * 100
            },
            "recent_status": recent_reports[-1].overall_health.value,
            "trend": self._calculate_health_trend(recent_reports)
        }
    
    def _calculate_health_trend(self, reports: List[SystemHealthReport]) -> str:
        """Calculate health trend from recent reports."""
        if len(reports) < 2:
            return "insufficient_data"
        
        # Simple trend analysis based on recent vs older health levels
        recent_half = reports[len(reports)//2:]
        older_half = reports[:len(reports)//2]
        
        recent_score = sum(self._health_level_score(r.overall_health) for r in recent_half) / len(recent_half)
        older_score = sum(self._health_level_score(r.overall_health) for r in older_half) / len(older_half)
        
        if recent_score > older_score + 0.2:
            return "improving"
        elif recent_score < older_score - 0.2:
            return "degrading"
        else:
            return "stable"
    
    def _health_level_score(self, level: HealthLevel) -> float:
        """Convert health level to numeric score."""
        scores = {
            HealthLevel.CRITICAL: 0.0,
            HealthLevel.WARNING: 0.5,
            HealthLevel.HEALTHY: 1.0,
            HealthLevel.UNKNOWN: 0.25
        }
        return scores.get(level, 0.0)
    
    async def cleanup(self):
        """Cleanup health monitor resources."""
        await self.stop_monitoring()
        self.registered_agents.clear()
        self.agent_health_cache.clear()
        self.health_history.clear()
        self.logger.info("Memory health monitor cleanup completed")