"""
Evaluation System Monitoring and Configuration
=============================================

This module provides comprehensive monitoring, configuration management, and
observability for the evaluation system.

Key Features:
- Real-time monitoring dashboards
- Configuration management and validation
- Health checks and alerting
- Performance profiling
- Resource monitoring
- Automated optimization
- Comprehensive logging and metrics

Monitoring Categories:
- System Health: Service availability, error rates, response times
- Performance: Throughput, latency, resource utilization
- Quality: Evaluation scores, accuracy, consistency
- Usage: Request patterns, user interactions, system load
- Operational: Deployments, configurations, maintenance
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
import threading
import psutil
import weakref
from collections import defaultdict, deque

from claude_pm.core.config import Config
from claude_pm.services.mirascope_evaluator import MirascopeEvaluator, EvaluationResult
from claude_pm.services.evaluation_integration import EvaluationIntegrationService
from claude_pm.services.evaluation_metrics import EvaluationMetricsSystem
from claude_pm.services.evaluation_performance import EvaluationPerformanceManager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Health check definition."""
    name: str
    description: str
    check_function: Callable[[], Dict[str, Any]]
    interval_seconds: int = 60
    timeout_seconds: int = 10
    enabled: bool = True
    last_check: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    consecutive_failures: int = 0


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    description: str
    condition: str  # Python expression
    severity: AlertSeverity
    threshold: float
    duration_seconds: int = 300  # 5 minutes
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class MonitoringMetric:
    """Monitoring metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags
        }


class EvaluationMonitor:
    """
    Comprehensive monitoring system for evaluation services.
    
    Provides health checks, alerting, and performance monitoring.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize evaluation monitor.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.enabled = self.config.get("evaluation_monitoring_enabled", True)
        
        # Component references (weak references to avoid circular dependencies)
        self.evaluator: Optional[MirascopeEvaluator] = None
        self.integration_service: Optional[EvaluationIntegrationService] = None
        self.metrics_system: Optional[EvaluationMetricsSystem] = None
        self.performance_manager: Optional[EvaluationPerformanceManager] = None
        
        # Monitoring data
        self.metrics: deque = deque(maxlen=10000)  # Recent metrics
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: List[Dict[str, Any]] = []
        
        # Background tasks
        self.monitor_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        self.alert_check_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        
        # Storage
        self.storage_path = Path(self.config.get("evaluation_storage_path", "~/.claude-pm/training")).expanduser()
        self.monitoring_dir = self.storage_path / "monitoring"
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._initialize_health_checks()
        self._initialize_alert_rules()
        
        # Statistics
        self.start_time = datetime.now()
        self.total_health_checks = 0
        self.total_alerts_triggered = 0
        
        if self.enabled:
            logger.info("Evaluation monitoring system initialized")
    
    def register_services(
        self,
        evaluator: Optional[MirascopeEvaluator] = None,
        integration_service: Optional[EvaluationIntegrationService] = None,
        metrics_system: Optional[EvaluationMetricsSystem] = None,
        performance_manager: Optional[EvaluationPerformanceManager] = None
    ) -> None:
        """Register services for monitoring."""
        self.evaluator = evaluator
        self.integration_service = integration_service
        self.metrics_system = metrics_system
        self.performance_manager = performance_manager
        
        logger.info("Monitoring services registered")
    
    def _initialize_health_checks(self) -> None:
        """Initialize health check definitions."""
        self.health_checks = {
            "system_resources": HealthCheck(
                name="system_resources",
                description="System resource utilization",
                check_function=self._check_system_resources,
                interval_seconds=30
            ),
            "evaluation_service": HealthCheck(
                name="evaluation_service",
                description="Evaluation service availability",
                check_function=self._check_evaluation_service,
                interval_seconds=60
            ),
            "performance_metrics": HealthCheck(
                name="performance_metrics",
                description="Performance metrics health",
                check_function=self._check_performance_metrics,
                interval_seconds=60
            ),
            "integration_service": HealthCheck(
                name="integration_service",
                description="Integration service health",
                check_function=self._check_integration_service,
                interval_seconds=90
            ),
            "storage_health": HealthCheck(
                name="storage_health",
                description="Storage system health",
                check_function=self._check_storage_health,
                interval_seconds=120
            )
        }
    
    def _initialize_alert_rules(self) -> None:
        """Initialize alert rule definitions."""
        self.alert_rules = {
            "high_cpu_usage": AlertRule(
                name="high_cpu_usage",
                description="High CPU usage detected",
                condition="cpu_percent > threshold",
                severity=AlertSeverity.WARNING,
                threshold=80.0,
                duration_seconds=300
            ),
            "high_memory_usage": AlertRule(
                name="high_memory_usage",
                description="High memory usage detected",
                condition="memory_percent > threshold",
                severity=AlertSeverity.WARNING,
                threshold=85.0,
                duration_seconds=300
            ),
            "high_error_rate": AlertRule(
                name="high_error_rate",
                description="High error rate in evaluations",
                condition="error_rate > threshold",
                severity=AlertSeverity.ERROR,
                threshold=5.0,
                duration_seconds=180
            ),
            "slow_response_time": AlertRule(
                name="slow_response_time",
                description="Slow evaluation response time",
                condition="avg_response_time > threshold",
                severity=AlertSeverity.WARNING,
                threshold=500.0,  # 500ms
                duration_seconds=300
            ),
            "low_cache_hit_rate": AlertRule(
                name="low_cache_hit_rate",
                description="Low cache hit rate",
                condition="cache_hit_rate < threshold",
                severity=AlertSeverity.WARNING,
                threshold=70.0,
                duration_seconds=600
            ),
            "circuit_breaker_open": AlertRule(
                name="circuit_breaker_open",
                description="Circuit breaker is open",
                condition="circuit_breaker_state == 'open'",
                severity=AlertSeverity.CRITICAL,
                threshold=1.0,
                duration_seconds=60
            )
        }
    
    async def start_monitoring(self) -> None:
        """Start monitoring tasks."""
        if not self.enabled:
            return
        
        # Start monitoring tasks
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        self.alert_check_task = asyncio.create_task(self._alert_check_loop())
        
        logger.info("Evaluation monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring tasks."""
        self.shutdown_event.set()
        
        # Cancel tasks
        for task in [self.monitor_task, self.health_check_task, self.alert_check_task]:
            if task:
                task.cancel()
        
        # Wait for tasks to complete
        tasks = [t for t in [self.monitor_task, self.health_check_task, self.alert_check_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Evaluation monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while not self.shutdown_event.is_set():
            try:
                await self._collect_metrics()
                await asyncio.sleep(30)  # Collect metrics every 30 seconds
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _health_check_loop(self) -> None:
        """Health check loop."""
        while not self.shutdown_event.is_set():
            try:
                await self._run_health_checks()
                await asyncio.sleep(30)  # Check health every 30 seconds
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)
    
    async def _alert_check_loop(self) -> None:
        """Alert check loop."""
        while not self.shutdown_event.is_set():
            try:
                await self._check_alerts()
                await asyncio.sleep(15)  # Check alerts every 15 seconds
            except Exception as e:
                logger.error(f"Alert check loop error: {e}")
                await asyncio.sleep(60)
    
    async def _collect_metrics(self) -> None:
        """Collect system and service metrics."""
        timestamp = datetime.now()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        self.metrics.append(MonitoringMetric(
            name="cpu_percent",
            value=cpu_percent,
            timestamp=timestamp,
            tags={"type": "system"}
        ))
        
        self.metrics.append(MonitoringMetric(
            name="memory_percent",
            value=memory.percent,
            timestamp=timestamp,
            tags={"type": "system"}
        ))
        
        self.metrics.append(MonitoringMetric(
            name="disk_percent",
            value=disk.percent,
            timestamp=timestamp,
            tags={"type": "system"}
        ))
        
        # Service metrics
        if self.performance_manager:
            perf_stats = self.performance_manager.get_performance_stats()
            
            self.metrics.append(MonitoringMetric(
                name="avg_response_time",
                value=perf_stats.get("average_evaluation_time", 0),
                timestamp=timestamp,
                tags={"type": "performance"}
            ))
            
            self.metrics.append(MonitoringMetric(
                name="cache_hit_rate",
                value=perf_stats.get("cache_stats", {}).get("hit_rate", 0),
                timestamp=timestamp,
                tags={"type": "performance"}
            ))
            
            self.metrics.append(MonitoringMetric(
                name="evaluations_per_second",
                value=perf_stats.get("evaluations_per_second", 0),
                timestamp=timestamp,
                tags={"type": "performance"}
            ))
        
        # Integration metrics
        if self.integration_service:
            integration_stats = self.integration_service.get_integration_statistics()
            
            self.metrics.append(MonitoringMetric(
                name="total_evaluations",
                value=integration_stats.get("integration_stats", {}).get("total_evaluations", 0),
                timestamp=timestamp,
                tags={"type": "integration"}
            ))
            
            self.metrics.append(MonitoringMetric(
                name="corrections_evaluated",
                value=integration_stats.get("integration_stats", {}).get("corrections_evaluated", 0),
                timestamp=timestamp,
                tags={"type": "integration"}
            ))
    
    async def _run_health_checks(self) -> None:
        """Run all health checks."""
        for name, health_check in self.health_checks.items():
            if not health_check.enabled:
                continue
            
            # Check if it's time to run this check
            if health_check.last_check:
                elapsed = (datetime.now() - health_check.last_check).total_seconds()
                if elapsed < health_check.interval_seconds:
                    continue
            
            try:
                # Run health check with timeout
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, health_check.check_function
                    ),
                    timeout=health_check.timeout_seconds
                )
                
                health_check.last_check = datetime.now()
                health_check.last_result = result
                health_check.consecutive_failures = 0
                
                self.total_health_checks += 1
                
            except Exception as e:
                health_check.consecutive_failures += 1
                health_check.last_result = {
                    "status": HealthStatus.CRITICAL.value,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.error(f"Health check {name} failed: {e}")
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource utilization."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = HealthStatus.HEALTHY
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.CRITICAL
            elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                status = HealthStatus.WARNING
            
            return {
                "status": status.value,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_evaluation_service(self) -> Dict[str, Any]:
        """Check evaluation service health."""
        try:
            if not self.evaluator:
                return {
                    "status": HealthStatus.WARNING.value,
                    "message": "Evaluator not registered",
                    "timestamp": datetime.now().isoformat()
                }
            
            stats = self.evaluator.get_evaluation_statistics()
            
            status = HealthStatus.HEALTHY
            if not stats.get("enabled", False):
                status = HealthStatus.WARNING
            elif stats.get("cache_hit_rate", 0) < 50:
                status = HealthStatus.WARNING
            
            return {
                "status": status.value,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_performance_metrics(self) -> Dict[str, Any]:
        """Check performance metrics health."""
        try:
            if not self.performance_manager:
                return {
                    "status": HealthStatus.WARNING.value,
                    "message": "Performance manager not registered",
                    "timestamp": datetime.now().isoformat()
                }
            
            stats = self.performance_manager.get_performance_stats()
            
            status = HealthStatus.HEALTHY
            avg_time = stats.get("average_evaluation_time", 0)
            circuit_state = stats.get("circuit_breaker_state", {}).get("state", "closed")
            
            if circuit_state == "open":
                status = HealthStatus.CRITICAL
            elif avg_time > 1000:  # 1 second
                status = HealthStatus.WARNING
            
            return {
                "status": status.value,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_integration_service(self) -> Dict[str, Any]:
        """Check integration service health."""
        try:
            if not self.integration_service:
                return {
                    "status": HealthStatus.WARNING.value,
                    "message": "Integration service not registered",
                    "timestamp": datetime.now().isoformat()
                }
            
            stats = self.integration_service.get_integration_statistics()
            
            status = HealthStatus.HEALTHY
            if not stats.get("service_enabled", False):
                status = HealthStatus.WARNING
            elif stats.get("integration_stats", {}).get("errors", 0) > 10:
                status = HealthStatus.WARNING
            
            return {
                "status": status.value,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_storage_health(self) -> Dict[str, Any]:
        """Check storage system health."""
        try:
            # Check storage directories
            directories = [
                self.storage_path / "corrections",
                self.storage_path / "evaluations",
                self.storage_path / "integration",
                self.storage_path / "monitoring"
            ]
            
            status = HealthStatus.HEALTHY
            directory_status = {}
            
            for directory in directories:
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                
                # Check if writable
                try:
                    test_file = directory / "test_write.tmp"
                    test_file.write_text("test")
                    test_file.unlink()
                    directory_status[str(directory)] = "ok"
                except Exception:
                    directory_status[str(directory)] = "error"
                    status = HealthStatus.WARNING
            
            return {
                "status": status.value,
                "directories": directory_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_alerts(self) -> None:
        """Check alert conditions."""
        current_time = datetime.now()
        
        for name, alert_rule in self.alert_rules.items():
            if not alert_rule.enabled:
                continue
            
            try:
                # Evaluate alert condition
                should_trigger = await self._evaluate_alert_condition(alert_rule)
                
                if should_trigger:
                    # Check if alert should be triggered (duration consideration)
                    if alert_rule.last_triggered is None or \
                       (current_time - alert_rule.last_triggered).total_seconds() > alert_rule.duration_seconds:
                        
                        await self._trigger_alert(alert_rule)
                        alert_rule.last_triggered = current_time
                        alert_rule.trigger_count += 1
                        
            except Exception as e:
                logger.error(f"Alert check error for {name}: {e}")
    
    async def _evaluate_alert_condition(self, alert_rule: AlertRule) -> bool:
        """Evaluate alert condition."""
        try:
            # Get recent metrics
            recent_metrics = self._get_recent_metrics(minutes=5)
            
            # Create evaluation context
            context = {
                "threshold": alert_rule.threshold,
                "recent_metrics": recent_metrics
            }
            
            # Add specific metrics based on condition
            if "cpu_percent" in alert_rule.condition:
                cpu_metrics = [m for m in recent_metrics if m.name == "cpu_percent"]
                context["cpu_percent"] = sum(m.value for m in cpu_metrics) / len(cpu_metrics) if cpu_metrics else 0
            
            if "memory_percent" in alert_rule.condition:
                memory_metrics = [m for m in recent_metrics if m.name == "memory_percent"]
                context["memory_percent"] = sum(m.value for m in memory_metrics) / len(memory_metrics) if memory_metrics else 0
            
            if "error_rate" in alert_rule.condition:
                # Calculate error rate from health checks
                error_count = sum(1 for hc in self.health_checks.values() if hc.last_result and hc.last_result.get("status") == HealthStatus.CRITICAL.value)
                total_checks = len(self.health_checks)
                context["error_rate"] = (error_count / total_checks * 100) if total_checks > 0 else 0
            
            if "avg_response_time" in alert_rule.condition:
                response_time_metrics = [m for m in recent_metrics if m.name == "avg_response_time"]
                context["avg_response_time"] = sum(m.value for m in response_time_metrics) / len(response_time_metrics) if response_time_metrics else 0
            
            if "cache_hit_rate" in alert_rule.condition:
                cache_metrics = [m for m in recent_metrics if m.name == "cache_hit_rate"]
                context["cache_hit_rate"] = sum(m.value for m in cache_metrics) / len(cache_metrics) if cache_metrics else 0
            
            if "circuit_breaker_state" in alert_rule.condition:
                if self.performance_manager:
                    stats = self.performance_manager.get_performance_stats()
                    context["circuit_breaker_state"] = stats.get("circuit_breaker_state", {}).get("state", "closed")
                else:
                    context["circuit_breaker_state"] = "closed"
            
            # Evaluate condition
            return eval(alert_rule.condition, {"__builtins__": {}}, context)
            
        except Exception as e:
            logger.error(f"Error evaluating alert condition for {alert_rule.name}: {e}")
            return False
    
    def _get_recent_metrics(self, minutes: int = 5) -> List[MonitoringMetric]:
        """Get recent metrics."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics if m.timestamp >= cutoff_time]
    
    async def _trigger_alert(self, alert_rule: AlertRule) -> None:
        """Trigger an alert."""
        alert = {
            "name": alert_rule.name,
            "description": alert_rule.description,
            "severity": alert_rule.severity.value,
            "threshold": alert_rule.threshold,
            "timestamp": datetime.now().isoformat(),
            "trigger_count": alert_rule.trigger_count + 1
        }
        
        self.active_alerts.append(alert)
        self.total_alerts_triggered += 1
        
        # Log alert
        logger.warning(f"Alert triggered: {alert['name']} - {alert['description']}")
        
        # Store alert
        await self._store_alert(alert)
        
        # Send notification (placeholder for actual implementation)
        await self._send_alert_notification(alert)
    
    async def _store_alert(self, alert: Dict[str, Any]) -> None:
        """Store alert to file."""
        try:
            alert_file = self.monitoring_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(alert_file, 'w') as f:
                json.dump(alert, f, indent=2)
            
            logger.debug(f"Stored alert: {alert_file}")
            
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
    
    async def _send_alert_notification(self, alert: Dict[str, Any]) -> None:
        """Send alert notification (placeholder)."""
        # This is where you would integrate with notification systems
        # like email, Slack, PagerDuty, etc.
        pass
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Get health check status
        health_status = {}
        overall_health = HealthStatus.HEALTHY
        
        for name, health_check in self.health_checks.items():
            if health_check.last_result:
                status = health_check.last_result.get("status", HealthStatus.UNKNOWN.value)
                health_status[name] = status
                
                if status == HealthStatus.CRITICAL.value:
                    overall_health = HealthStatus.CRITICAL
                elif status == HealthStatus.WARNING.value and overall_health != HealthStatus.CRITICAL:
                    overall_health = HealthStatus.WARNING
        
        # Get recent metrics summary
        recent_metrics = self._get_recent_metrics(minutes=5)
        metrics_summary = {}
        
        for metric in recent_metrics:
            if metric.name not in metrics_summary:
                metrics_summary[metric.name] = []
            metrics_summary[metric.name].append(metric.value)
        
        # Calculate averages
        for name, values in metrics_summary.items():
            metrics_summary[name] = {
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
        
        return {
            "enabled": self.enabled,
            "uptime_seconds": uptime,
            "overall_health": overall_health.value,
            "health_checks": health_status,
            "metrics_summary": metrics_summary,
            "active_alerts": len(self.active_alerts),
            "total_health_checks": self.total_health_checks,
            "total_alerts_triggered": self.total_alerts_triggered,
            "monitoring_tasks_running": sum(1 for t in [self.monitor_task, self.health_check_task, self.alert_check_task] if t and not t.done())
        }
    
    def get_health_check_details(self) -> Dict[str, Any]:
        """Get detailed health check information."""
        details = {}
        
        for name, health_check in self.health_checks.items():
            details[name] = {
                "description": health_check.description,
                "enabled": health_check.enabled,
                "interval_seconds": health_check.interval_seconds,
                "last_check": health_check.last_check.isoformat() if health_check.last_check else None,
                "last_result": health_check.last_result,
                "consecutive_failures": health_check.consecutive_failures
            }
        
        return details
    
    def get_alert_rules(self) -> Dict[str, Any]:
        """Get alert rule configuration."""
        rules = {}
        
        for name, alert_rule in self.alert_rules.items():
            rules[name] = {
                "description": alert_rule.description,
                "condition": alert_rule.condition,
                "severity": alert_rule.severity.value,
                "threshold": alert_rule.threshold,
                "duration_seconds": alert_rule.duration_seconds,
                "enabled": alert_rule.enabled,
                "last_triggered": alert_rule.last_triggered.isoformat() if alert_rule.last_triggered else None,
                "trigger_count": alert_rule.trigger_count
            }
        
        return rules
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = []
        for alert in self.active_alerts:
            alert_time = datetime.fromisoformat(alert["timestamp"])
            if alert_time >= cutoff_time:
                recent_alerts.append(alert)
        
        return recent_alerts
    
    def clear_alerts(self) -> Dict[str, Any]:
        """Clear active alerts."""
        cleared_count = len(self.active_alerts)
        self.active_alerts.clear()
        
        return {
            "cleared_alerts": cleared_count,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        return {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_status": self.get_monitoring_status(),
            "health_checks": self.get_health_check_details(),
            "alert_rules": self.get_alert_rules(),
            "recent_alerts": self.get_recent_alerts(hours=24),
            "system_metrics": {
                "cpu_usage": self._get_metric_summary("cpu_percent"),
                "memory_usage": self._get_metric_summary("memory_percent"),
                "disk_usage": self._get_metric_summary("disk_percent"),
                "response_time": self._get_metric_summary("avg_response_time"),
                "cache_hit_rate": self._get_metric_summary("cache_hit_rate")
            }
        }
    
    def _get_metric_summary(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get summary for a specific metric."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        metric_values = [
            m.value for m in self.metrics 
            if m.name == metric_name and m.timestamp >= cutoff_time
        ]
        
        if not metric_values:
            return {"count": 0, "average": 0, "min": 0, "max": 0}
        
        return {
            "count": len(metric_values),
            "average": sum(metric_values) / len(metric_values),
            "min": min(metric_values),
            "max": max(metric_values)
        }
    
    async def save_monitoring_report(self) -> str:
        """Save monitoring report to file."""
        try:
            report = self.generate_monitoring_report()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.monitoring_dir / f"monitoring_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Saved monitoring report: {report_file}")
            
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Failed to save monitoring report: {e}")
            raise


# Global monitoring instance
_evaluation_monitor: Optional[EvaluationMonitor] = None


def get_evaluation_monitor(config: Optional[Config] = None) -> EvaluationMonitor:
    """Get global evaluation monitor instance."""
    global _evaluation_monitor
    
    if _evaluation_monitor is None:
        _evaluation_monitor = EvaluationMonitor(config)
    
    return _evaluation_monitor


async def initialize_evaluation_monitoring(config: Optional[Config] = None) -> Dict[str, Any]:
    """Initialize evaluation monitoring system."""
    try:
        monitor = get_evaluation_monitor(config)
        await monitor.start_monitoring()
        
        status = monitor.get_monitoring_status()
        
        return {
            "initialized": True,
            "monitoring_enabled": monitor.enabled,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize evaluation monitoring: {e}")
        return {"initialized": False, "error": str(e)}


async def shutdown_evaluation_monitoring() -> None:
    """Shutdown evaluation monitoring."""
    global _evaluation_monitor
    
    if _evaluation_monitor:
        await _evaluation_monitor.stop_monitoring()
        _evaluation_monitor = None


# Helper functions
def get_monitoring_status() -> Dict[str, Any]:
    """Get monitoring status."""
    monitor = get_evaluation_monitor()
    return monitor.get_monitoring_status()


def get_health_status() -> Dict[str, Any]:
    """Get health status."""
    monitor = get_evaluation_monitor()
    return monitor.get_health_check_details()


async def generate_monitoring_report() -> str:
    """Generate and save monitoring report."""
    monitor = get_evaluation_monitor()
    return await monitor.save_monitoring_report()


if __name__ == "__main__":
    # Test the monitoring system
    print("Testing Evaluation Monitoring System")
    print("=" * 50)
    
    # Test initialization
    async def test_monitoring():
        init_result = await initialize_evaluation_monitoring()
        print(f"Initialization: {init_result['initialized']}")
        print(f"Monitoring enabled: {init_result['monitoring_enabled']}")
        
        if init_result['initialized']:
            monitor = get_evaluation_monitor()
            
            # Wait for some monitoring data
            await asyncio.sleep(2)
            
            # Get status
            status = monitor.get_monitoring_status()
            print(f"Overall health: {status['overall_health']}")
            print(f"Active alerts: {status['active_alerts']}")
            print(f"Health checks: {status['total_health_checks']}")
            
            # Get health details
            health_details = monitor.get_health_check_details()
            for name, details in health_details.items():
                print(f"Health check {name}: {details.get('last_result', {}).get('status', 'unknown')}")
            
            # Generate report
            report_file = await monitor.save_monitoring_report()
            print(f"Generated report: {report_file}")
            
            # Shutdown
            await shutdown_evaluation_monitoring()
        
        else:
            print(f"Initialization failed: {init_result.get('error', 'Unknown error')}")
    
    # Run test
    asyncio.run(test_monitoring())