"""
Health Monitoring

This module provides health monitoring capabilities for memory backends.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime

from ..interfaces.backend import MemoryBackend
from ..interfaces.models import HealthStatus, BackendHealth


@dataclass
class HealthAlert:
    """Health alert information."""
    backend_name: str
    alert_type: str
    message: str
    severity: str  # low, medium, high, critical
    timestamp: float
    resolved: bool = False
    resolution_time: Optional[float] = None


class HealthMonitor:
    """
    Health monitoring for memory backends.
    
    This class continuously monitors the health of memory backends,
    tracks uptime, and generates alerts for issues.
    """
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Health check interval in seconds
        """
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)
        
        # Health data storage
        self.health_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.current_health: Dict[str, BackendHealth] = {}
        self.backends: Dict[str, MemoryBackend] = {}
        
        # Monitoring state
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._start_time = time.time()
        
        # Alert system
        self.alerts: List[HealthAlert] = []
        self.alert_thresholds = {
            "max_consecutive_failures": 5,
            "min_uptime_percentage": 95.0,
            "max_response_time": 10.0,
            "alert_history_hours": 24
        }
        
        # Health metrics
        self.metrics = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "alerts_generated": 0,
            "alerts_resolved": 0,
            "monitoring_start_time": time.time()
        }
    
    async def start_monitoring(self, backends: Dict[str, MemoryBackend]):
        """
        Start health monitoring for backends.
        
        Args:
            backends: Dictionary of backend name to backend instance
        """
        self.backends = backends
        self._stop_event.clear()
        
        # Initialize health status for all backends
        for name, backend in backends.items():
            self.current_health[name] = BackendHealth(
                backend_name=name,
                is_healthy=False,
                response_time=0.0
            )
        
        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info(f"Started health monitoring for {len(backends)} backends")
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        self._stop_event.set()
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped health monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                await self._check_all_backends()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_backends(self):
        """Check health of all backends."""
        tasks = []
        
        for name, backend in self.backends.items():
            task = asyncio.create_task(
                self._check_backend_health(name, backend),
                name=f"health_check_{name}"
            )
            tasks.append(task)
        
        # Wait for all health checks to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                task_name = tasks[i].get_name()
                backend_name = task_name.replace("health_check_", "")
                
                if isinstance(result, Exception):
                    self.logger.error(f"Health check error for {backend_name}: {result}")
                    self._record_health_check(backend_name, False, float('inf'), str(result))
                else:
                    # Result is already recorded in _check_backend_health
                    pass
    
    async def _check_backend_health(self, name: str, backend: MemoryBackend):
        """Check health of a specific backend."""
        start_time = time.time()
        
        try:
            # Perform health check
            is_healthy = await backend.health_check()
            response_time = time.time() - start_time
            
            # Record health check
            self._record_health_check(name, is_healthy, response_time)
            
            # Update health status
            health = self.current_health[name]
            health.update_health(is_healthy, response_time)
            
            # Check for alerts
            self._check_health_alerts(name, health)
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Health check failed for {name}: {e}")
            
            # Record failed health check
            self._record_health_check(name, False, response_time, str(e))
            
            # Update health status
            health = self.current_health[name]
            health.update_health(False, response_time, str(e))
            
            # Check for alerts
            self._check_health_alerts(name, health)
    
    def _record_health_check(
        self,
        backend_name: str,
        is_healthy: bool,
        response_time: float,
        error_message: Optional[str] = None
    ):
        """Record a health check result."""
        self.metrics["total_checks"] += 1
        
        if is_healthy:
            self.metrics["successful_checks"] += 1
        else:
            self.metrics["failed_checks"] += 1
        
        # Record in history
        health_record = {
            "timestamp": time.time(),
            "healthy": is_healthy,
            "response_time": response_time,
            "error_message": error_message
        }
        
        self.health_history[backend_name].append(health_record)
        
        # Keep only recent history
        cutoff_time = time.time() - (self.alert_thresholds["alert_history_hours"] * 3600)
        self.health_history[backend_name] = [
            record for record in self.health_history[backend_name]
            if record["timestamp"] > cutoff_time
        ]
    
    def _check_health_alerts(self, backend_name: str, health: BackendHealth):
        """Check if health alerts should be generated."""
        current_time = time.time()
        
        # Check consecutive failures
        if health.consecutive_failures >= self.alert_thresholds["max_consecutive_failures"]:
            self._generate_alert(
                backend_name,
                "consecutive_failures",
                f"Backend has {health.consecutive_failures} consecutive failures",
                "high"
            )
        
        # Check response time
        if health.response_time > self.alert_thresholds["max_response_time"]:
            self._generate_alert(
                backend_name,
                "slow_response",
                f"Backend response time ({health.response_time:.2f}s) exceeds threshold",
                "medium"
            )
        
        # Check uptime percentage
        if health.total_requests >= 10:  # Only check after some requests
            uptime_percentage = health.get_success_rate()
            if uptime_percentage < self.alert_thresholds["min_uptime_percentage"]:
                self._generate_alert(
                    backend_name,
                    "low_uptime",
                    f"Backend uptime ({uptime_percentage:.1f}%) below threshold",
                    "high"
                )
        
        # Check if backend came back online (resolve alerts)
        if health.is_healthy and health.consecutive_successes >= 3:
            self._resolve_alerts(backend_name)
    
    def _generate_alert(
        self,
        backend_name: str,
        alert_type: str,
        message: str,
        severity: str
    ):
        """Generate a health alert."""
        # Check if similar alert already exists
        for alert in self.alerts:
            if (alert.backend_name == backend_name and 
                alert.alert_type == alert_type and 
                not alert.resolved):
                return  # Alert already exists
        
        # Create new alert
        alert = HealthAlert(
            backend_name=backend_name,
            alert_type=alert_type,
            message=message,
            severity=severity,
            timestamp=time.time()
        )
        
        self.alerts.append(alert)
        self.metrics["alerts_generated"] += 1
        
        self.logger.warning(f"Health alert generated: {backend_name} - {message}")
    
    def _resolve_alerts(self, backend_name: str):
        """Resolve alerts for a backend that has recovered."""
        current_time = time.time()
        resolved_count = 0
        
        for alert in self.alerts:
            if (alert.backend_name == backend_name and 
                not alert.resolved):
                alert.resolved = True
                alert.resolution_time = current_time
                resolved_count += 1
        
        if resolved_count > 0:
            self.metrics["alerts_resolved"] += resolved_count
            self.logger.info(f"Resolved {resolved_count} alerts for {backend_name}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all backends."""
        return {
            "monitoring_active": not self._stop_event.is_set(),
            "monitoring_duration": time.time() - self._start_time,
            "backends": {
                name: health.to_dict() 
                for name, health in self.current_health.items()
            },
            "metrics": self.metrics.copy()
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        total_backends = len(self.backends)
        healthy_backends = sum(1 for health in self.current_health.values() if health.is_healthy)
        unhealthy_backends = total_backends - healthy_backends
        
        # Calculate overall uptime
        overall_uptime = 0.0
        if self.current_health:
            uptime_sum = sum(health.get_success_rate() for health in self.current_health.values())
            overall_uptime = uptime_sum / len(self.current_health)
        
        # Count active alerts
        active_alerts = sum(1 for alert in self.alerts if not alert.resolved)
        
        return {
            "total_backends": total_backends,
            "healthy_backends": healthy_backends,
            "unhealthy_backends": unhealthy_backends,
            "overall_uptime": overall_uptime,
            "active_alerts": active_alerts,
            "monitoring_duration": time.time() - self._start_time,
            "health_check_interval": self.check_interval,
            "last_check": max(
                (health.last_checked for health in self.current_health.values()),
                default=0
            )
        }
    
    def get_backend_health(self, backend_name: str) -> Optional[Dict[str, Any]]:
        """Get health information for a specific backend."""
        if backend_name not in self.current_health:
            return None
        
        health = self.current_health[backend_name]
        history = self.health_history[backend_name]
        
        # Calculate recent metrics
        recent_checks = [h for h in history if h["timestamp"] > time.time() - 3600]  # Last hour
        recent_success_rate = 0.0
        avg_response_time = 0.0
        
        if recent_checks:
            successful_recent = sum(1 for h in recent_checks if h["healthy"])
            recent_success_rate = (successful_recent / len(recent_checks)) * 100
            avg_response_time = sum(h["response_time"] for h in recent_checks) / len(recent_checks)
        
        return {
            "backend_name": backend_name,
            "current_health": health.to_dict(),
            "recent_metrics": {
                "checks_last_hour": len(recent_checks),
                "success_rate_last_hour": recent_success_rate,
                "avg_response_time_last_hour": avg_response_time
            },
            "history_summary": {
                "total_checks": len(history),
                "oldest_check": min((h["timestamp"] for h in history), default=0),
                "newest_check": max((h["timestamp"] for h in history), default=0)
            }
        }
    
    def get_alerts(self, backend_name: Optional[str] = None, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Get alerts.
        
        Args:
            backend_name: Filter by backend name (optional)
            resolved: Filter by resolved status (optional)
            
        Returns:
            List of alerts
        """
        alerts = self.alerts
        
        if backend_name:
            alerts = [a for a in alerts if a.backend_name == backend_name]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return [
            {
                "backend_name": alert.backend_name,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "severity": alert.severity,
                "timestamp": alert.timestamp,
                "resolved": alert.resolved,
                "resolution_time": alert.resolution_time,
                "age_seconds": time.time() - alert.timestamp
            }
            for alert in alerts
        ]
    
    def get_health_history(self, backend_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for a backend."""
        if backend_name not in self.health_history:
            return []
        
        cutoff_time = time.time() - (hours * 3600)
        return [
            record for record in self.health_history[backend_name]
            if record["timestamp"] > cutoff_time
        ]
    
    def set_alert_threshold(self, threshold_name: str, value: Any):
        """Set alert threshold."""
        if threshold_name in self.alert_thresholds:
            self.alert_thresholds[threshold_name] = value
            self.logger.info(f"Set alert threshold {threshold_name} to {value}")
    
    def clear_alerts(self, backend_name: Optional[str] = None):
        """Clear alerts."""
        if backend_name:
            self.alerts = [a for a in self.alerts if a.backend_name != backend_name]
        else:
            self.alerts.clear()
        
        self.logger.info(f"Cleared alerts for {backend_name or 'all backends'}")
    
    def reset_metrics(self):
        """Reset monitoring metrics."""
        self.metrics = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "alerts_generated": 0,
            "alerts_resolved": 0,
            "monitoring_start_time": time.time()
        }
        self.logger.info("Reset health monitoring metrics")
    
    def export_health_report(self, format: str = "json") -> str:
        """Export comprehensive health report."""
        report_data = {
            "timestamp": time.time(),
            "monitoring_summary": self.get_health_summary(),
            "backend_health": {
                name: self.get_backend_health(name)
                for name in self.backends.keys()
            },
            "active_alerts": self.get_alerts(resolved=False),
            "resolved_alerts": self.get_alerts(resolved=True),
            "metrics": self.metrics.copy(),
            "alert_thresholds": self.alert_thresholds.copy()
        }
        
        if format.lower() == "json":
            import json
            return json.dumps(report_data, indent=2, default=str)
        else:
            return str(report_data)
    
    async def manual_health_check(self, backend_name: Optional[str] = None):
        """Perform manual health check."""
        if backend_name:
            if backend_name in self.backends:
                await self._check_backend_health(backend_name, self.backends[backend_name])
                self.logger.info(f"Manual health check completed for {backend_name}")
            else:
                self.logger.error(f"Backend {backend_name} not found")
        else:
            await self._check_all_backends()
            self.logger.info("Manual health check completed for all backends")
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"HealthMonitor(backends={len(self.backends)}, "
            f"active_alerts={len([a for a in self.alerts if not a.resolved])}, "
            f"monitoring_active={not self._stop_event.is_set()})"
        )