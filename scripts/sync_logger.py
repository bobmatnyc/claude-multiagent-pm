"""
Comprehensive Logging and Error Handling System for Claude PM GitHub Sync

This module provides structured logging, error handling, monitoring,
and reporting capabilities for the GitHub sync operations.
"""

import json
import logging
import logging.handlers
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class SyncEventType(Enum):
    """Types of sync events for categorization"""
    SYNC_START = "sync_start"
    SYNC_COMPLETE = "sync_complete"
    SYNC_ERROR = "sync_error"
    ISSUE_CREATED = "issue_created"
    ISSUE_UPDATED = "issue_updated"
    ISSUE_SKIPPED = "issue_skipped"
    RATE_LIMIT_HIT = "rate_limit_hit"
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    BACKUP_CREATED = "backup_created"
    ROLLBACK_INITIATED = "rollback_initiated"


class SyncErrorSeverity(Enum):
    """Severity levels for sync errors"""
    CRITICAL = "critical"  # Sync cannot continue
    HIGH = "high"         # Major functionality affected
    MEDIUM = "medium"     # Minor issues, sync can continue
    LOW = "low"          # Warnings and info


@dataclass
class SyncEvent:
    """Structured sync event for logging and monitoring"""
    timestamp: str
    event_type: SyncEventType
    severity: SyncErrorSeverity
    message: str
    context: Dict[str, Any]
    error_details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncEvent':
        """Create from dictionary"""
        data['event_type'] = SyncEventType(data['event_type'])
        data['severity'] = SyncErrorSeverity(data['severity'])
        return cls(**data)


class GitHubSyncError(Exception):
    """Base exception for GitHub sync operations"""
    
    def __init__(self, message: str, error_code: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SYNC_ERROR"
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()


class RateLimitExceededError(GitHubSyncError):
    """Raised when API rate limit is exceeded"""
    
    def __init__(self, remaining: int, reset_time: int, context: Dict[str, Any] = None):
        super().__init__(
            f"Rate limit exceeded. {remaining} requests remaining, resets at {reset_time}",
            "RATE_LIMIT_EXCEEDED",
            context
        )
        self.remaining = remaining
        self.reset_time = reset_time


class AuthenticationError(GitHubSyncError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "GitHub authentication failed", context: Dict[str, Any] = None):
        super().__init__(message, "AUTH_ERROR", context)


class ValidationError(GitHubSyncError):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, validation_errors: List[str] = None, context: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", context)
        self.validation_errors = validation_errors or []


class SyncConflictError(GitHubSyncError):
    """Raised when sync conflicts cannot be resolved automatically"""
    
    def __init__(self, ticket_id: str, conflicts: List[str], context: Dict[str, Any] = None):
        super().__init__(
            f"Sync conflict for ticket {ticket_id}: {', '.join(conflicts)}",
            "SYNC_CONFLICT",
            context
        )
        self.ticket_id = ticket_id
        self.conflicts = conflicts


class SyncLogger:
    """Comprehensive logging system for GitHub sync operations"""
    
    def __init__(self, log_dir: str = "/Users/masa/Projects/Claude-PM/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Event log for structured logging
        self.events: List[SyncEvent] = []
        self.events_file = self.log_dir / "sync_events.jsonl"
        
        # Setup loggers
        self._setup_loggers()
        
        # Performance metrics
        self.metrics = {
            "sync_duration": 0,
            "api_requests": 0,
            "rate_limit_hits": 0,
            "errors_by_severity": {severity.value: 0 for severity in SyncErrorSeverity},
            "tickets_processed": 0,
            "issues_created": 0,
            "issues_updated": 0,
            "issues_skipped": 0
        }
    
    def _setup_loggers(self):
        """Setup rotating file and console loggers"""
        
        # Main sync logger
        self.logger = logging.getLogger("github_sync")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "github_sync.log",
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Error-specific logger
        self.error_logger = logging.getLogger("github_sync.errors")
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "sync_errors.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.error_logger.addHandler(error_handler)
        
        # API requests logger for debugging
        self.api_logger = logging.getLogger("github_sync.api")
        api_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "api_requests.log",
            maxBytes=25 * 1024 * 1024,  # 25MB
            backupCount=2
        )
        api_handler.setLevel(logging.DEBUG)
        api_handler.setFormatter(detailed_formatter)
        self.api_logger.addHandler(api_handler)
    
    def log_event(self, event_type: SyncEventType, severity: SyncErrorSeverity, 
                  message: str, context: Dict[str, Any] = None, 
                  error_details: Dict[str, Any] = None):
        """Log a structured sync event"""
        
        event = SyncEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            severity=severity,
            message=message,
            context=context or {},
            error_details=error_details
        )
        
        self.events.append(event)
        
        # Write to events file immediately
        with open(self.events_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
        
        # Log to appropriate logger
        log_level = self._severity_to_log_level(severity)
        self.logger.log(log_level, f"[{event_type.value.upper()}] {message}")
        
        if error_details:
            self.logger.log(log_level, f"Error details: {json.dumps(error_details, indent=2)}")
        
        # Update metrics
        self.metrics["errors_by_severity"][severity.value] += 1
    
    def log_sync_start(self, repository: str, direction: str, dry_run: bool = False):
        """Log sync operation start"""
        self.sync_start_time = datetime.now()
        
        context = {
            "repository": repository,
            "direction": direction,
            "dry_run": dry_run,
            "start_time": self.sync_start_time.isoformat()
        }
        
        self.log_event(
            SyncEventType.SYNC_START,
            SyncErrorSeverity.LOW,
            f"Starting sync: {repository} ({direction})",
            context
        )
    
    def log_sync_complete(self, repository: str, results: Dict[str, Any]):
        """Log sync operation completion"""
        end_time = datetime.now()
        duration = (end_time - self.sync_start_time).total_seconds()
        
        self.metrics["sync_duration"] = duration
        self.metrics.update(results)
        
        context = {
            "repository": repository,
            "duration_seconds": duration,
            "end_time": end_time.isoformat(),
            "results": results,
            "metrics": self.metrics
        }
        
        severity = SyncErrorSeverity.LOW if results.get("success", False) else SyncErrorSeverity.HIGH
        
        self.log_event(
            SyncEventType.SYNC_COMPLETE,
            severity,
            f"Sync completed: {repository} in {duration:.2f}s",
            context
        )
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       response_time: float, rate_limit_remaining: int = None):
        """Log API request details"""
        self.metrics["api_requests"] += 1
        
        context = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time_ms": response_time * 1000,
            "rate_limit_remaining": rate_limit_remaining
        }
        
        self.api_logger.debug(f"{method} {endpoint} - {status_code} ({response_time:.3f}s)")
        
        # Log rate limit warnings
        if rate_limit_remaining is not None and rate_limit_remaining < 100:
            self.log_event(
                SyncEventType.RATE_LIMIT_HIT,
                SyncErrorSeverity.MEDIUM,
                f"Rate limit warning: {rate_limit_remaining} requests remaining",
                context
            )
    
    def log_issue_action(self, action: str, ticket_id: str, issue_number: int = None, 
                        error: str = None):
        """Log issue creation, update, or skip"""
        context = {
            "ticket_id": ticket_id,
            "issue_number": issue_number,
            "action": action
        }
        
        if action == "created":
            event_type = SyncEventType.ISSUE_CREATED
            severity = SyncErrorSeverity.LOW
            message = f"Created issue #{issue_number} for {ticket_id}"
            self.metrics["issues_created"] += 1
        
        elif action == "updated":
            event_type = SyncEventType.ISSUE_UPDATED
            severity = SyncErrorSeverity.LOW
            message = f"Updated issue #{issue_number} for {ticket_id}"
            self.metrics["issues_updated"] += 1
        
        elif action == "skipped":
            event_type = SyncEventType.ISSUE_SKIPPED
            severity = SyncErrorSeverity.LOW
            message = f"Skipped {ticket_id} (no changes needed)"
            self.metrics["issues_skipped"] += 1
        
        else:  # error
            event_type = SyncEventType.API_ERROR
            severity = SyncErrorSeverity.MEDIUM
            message = f"Failed to {action} issue for {ticket_id}: {error}"
            context["error"] = error
        
        self.log_event(event_type, severity, message, context)
        self.metrics["tickets_processed"] += 1
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, 
                  severity: SyncErrorSeverity = SyncErrorSeverity.HIGH):
        """Log error with full context and traceback"""
        
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc()
        }
        
        if isinstance(error, GitHubSyncError):
            error_details["error_code"] = error.error_code
            error_details["error_context"] = error.context
            severity = self._determine_error_severity(error)
        
        self.log_event(
            SyncEventType.SYNC_ERROR,
            severity,
            f"Error: {str(error)}",
            context or {},
            error_details
        )
        
        # Also log to error logger
        self.error_logger.error(f"Sync error: {str(error)}", exc_info=True)
    
    def log_validation_errors(self, ticket_id: str, errors: List[str]):
        """Log validation errors for a ticket"""
        context = {
            "ticket_id": ticket_id,
            "validation_errors": errors
        }
        
        self.log_event(
            SyncEventType.VALIDATION_ERROR,
            SyncErrorSeverity.MEDIUM,
            f"Validation errors for {ticket_id}: {', '.join(errors)}",
            context
        )
    
    def log_backup_created(self, backup_file: str, operation: str):
        """Log backup creation"""
        context = {
            "backup_file": backup_file,
            "operation": operation,
            "file_size_bytes": Path(backup_file).stat().st_size if Path(backup_file).exists() else 0
        }
        
        self.log_event(
            SyncEventType.BACKUP_CREATED,
            SyncErrorSeverity.LOW,
            f"Backup created for {operation}: {backup_file}",
            context
        )
    
    def log_rollback(self, backup_file: str, reason: str):
        """Log rollback operation"""
        context = {
            "backup_file": backup_file,
            "reason": reason
        }
        
        self.log_event(
            SyncEventType.ROLLBACK_INITIATED,
            SyncErrorSeverity.HIGH,
            f"Rollback initiated: {reason}",
            context
        )
    
    def generate_sync_report(self, output_file: str = None) -> str:
        """Generate comprehensive sync report"""
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(self.log_dir / f"sync_report_{timestamp}.md")
        
        # Calculate summary statistics
        total_events = len(self.events)
        error_events = [e for e in self.events if e.severity in [SyncErrorSeverity.HIGH, SyncErrorSeverity.CRITICAL]]
        warning_events = [e for e in self.events if e.severity == SyncErrorSeverity.MEDIUM]
        
        # Group errors by type
        error_types = {}
        for event in error_events:
            error_type = event.error_details.get('error_type', 'Unknown') if event.error_details else 'Unknown'
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Generate report
        report_lines = [
            "# Claude PM GitHub Sync Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            f"- Total Events: {total_events}",
            f"- Errors: {len(error_events)}",
            f"- Warnings: {len(warning_events)}",
            f"- Sync Duration: {self.metrics['sync_duration']:.2f} seconds",
            f"- API Requests: {self.metrics['api_requests']}",
            "",
            "## Sync Performance",
            f"- Tickets Processed: {self.metrics['tickets_processed']}",
            f"- Issues Created: {self.metrics['issues_created']}",
            f"- Issues Updated: {self.metrics['issues_updated']}",
            f"- Issues Skipped: {self.metrics['issues_skipped']}",
            f"- Rate Limit Hits: {self.metrics['rate_limit_hits']}",
            "",
            "## Error Summary"
        ]
        
        if error_types:
            report_lines.append("### Error Types")
            for error_type, count in sorted(error_types.items()):
                report_lines.append(f"- {error_type}: {count}")
            report_lines.append("")
        
        # Recent errors
        if error_events:
            report_lines.extend([
                "### Recent Errors",
                "| Time | Type | Message |",
                "|------|------|---------|"
            ])
            
            for event in error_events[-10:]:  # Last 10 errors
                time_str = event.timestamp.split('T')[1][:8]  # HH:MM:SS
                error_type = event.error_details.get('error_type', 'Unknown') if event.error_details else 'Unknown'
                message = event.message[:50] + "..." if len(event.message) > 50 else event.message
                report_lines.append(f"| {time_str} | {error_type} | {message} |")
            
            report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "## Recommendations",
            self._generate_recommendations(),
            "",
            "## Log Files",
            f"- Main Log: {self.log_dir / 'github_sync.log'}",
            f"- Error Log: {self.log_dir / 'sync_errors.log'}",
            f"- API Log: {self.log_dir / 'api_requests.log'}",
            f"- Events Log: {self.events_file}",
            ""
        ])
        
        report_content = "\n".join(report_lines)
        
        # Write report to file
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"Sync report generated: {output_file}")
        return report_content
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the last N hours"""
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_events = [
            e for e in self.events 
            if datetime.fromisoformat(e.timestamp) > cutoff
        ]
        
        stats = {
            "total_events": len(recent_events),
            "errors": len([e for e in recent_events if e.severity in [SyncErrorSeverity.HIGH, SyncErrorSeverity.CRITICAL]]),
            "warnings": len([e for e in recent_events if e.severity == SyncErrorSeverity.MEDIUM]),
            "error_rate": 0,
            "common_errors": {},
            "hour_range": hours
        }
        
        if stats["total_events"] > 0:
            stats["error_rate"] = (stats["errors"] / stats["total_events"]) * 100
        
        # Count common error types
        for event in recent_events:
            if event.severity in [SyncErrorSeverity.HIGH, SyncErrorSeverity.CRITICAL] and event.error_details:
                error_type = event.error_details.get('error_type', 'Unknown')
                stats["common_errors"][error_type] = stats["common_errors"].get(error_type, 0) + 1
        
        return stats
    
    def _severity_to_log_level(self, severity: SyncErrorSeverity) -> int:
        """Convert sync severity to logging level"""
        mapping = {
            SyncErrorSeverity.CRITICAL: logging.CRITICAL,
            SyncErrorSeverity.HIGH: logging.ERROR,
            SyncErrorSeverity.MEDIUM: logging.WARNING,
            SyncErrorSeverity.LOW: logging.INFO
        }
        return mapping.get(severity, logging.INFO)
    
    def _determine_error_severity(self, error: GitHubSyncError) -> SyncErrorSeverity:
        """Determine severity based on error type"""
        if isinstance(error, (AuthenticationError, SyncConflictError)):
            return SyncErrorSeverity.CRITICAL
        elif isinstance(error, RateLimitExceededError):
            return SyncErrorSeverity.HIGH
        elif isinstance(error, ValidationError):
            return SyncErrorSeverity.MEDIUM
        else:
            return SyncErrorSeverity.HIGH
    
    def _generate_recommendations(self) -> str:
        """Generate recommendations based on logged events"""
        
        recommendations = []
        
        # Check rate limiting
        rate_limit_events = [e for e in self.events if e.event_type == SyncEventType.RATE_LIMIT_HIT]
        if len(rate_limit_events) > 5:
            recommendations.append("- Consider reducing batch size or adding delays between requests")
        
        # Check authentication errors
        auth_errors = [e for e in self.events if e.error_details and e.error_details.get('error_type') == 'AuthenticationError']
        if auth_errors:
            recommendations.append("- Verify GitHub token permissions and expiration")
        
        # Check validation errors
        validation_errors = [e for e in self.events if e.event_type == SyncEventType.VALIDATION_ERROR]
        if len(validation_errors) > 10:
            recommendations.append("- Review ticket format in BACKLOG.md for consistency")
        
        # Check error rate
        total_events = len(self.events)
        error_events = [e for e in self.events if e.severity in [SyncErrorSeverity.HIGH, SyncErrorSeverity.CRITICAL]]
        
        if total_events > 0 and (len(error_events) / total_events) > 0.1:
            recommendations.append("- High error rate detected - review sync configuration")
        
        if not recommendations:
            recommendations.append("- No specific issues detected - sync is performing well")
        
        return "\n".join(recommendations)


class SyncMonitor:
    """Monitor sync operations and provide alerting"""
    
    def __init__(self, logger: SyncLogger):
        self.logger = logger
        self.alerts_file = logger.log_dir / "sync_alerts.json"
        self.alert_thresholds = {
            "error_rate_percent": 10,
            "consecutive_failures": 3,
            "rate_limit_hits_per_hour": 5,
            "sync_duration_minutes": 30
        }
    
    def check_sync_health(self) -> Dict[str, Any]:
        """Check sync health and generate alerts if needed"""
        
        health_status = {
            "status": "healthy",
            "alerts": [],
            "warnings": [],
            "metrics": self.logger.metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check error rate
        stats = self.logger.get_error_statistics(hours=1)
        if stats["error_rate"] > self.alert_thresholds["error_rate_percent"]:
            health_status["alerts"].append({
                "type": "high_error_rate",
                "message": f"Error rate {stats['error_rate']:.1f}% exceeds threshold {self.alert_thresholds['error_rate_percent']}%",
                "severity": "high"
            })
            health_status["status"] = "unhealthy"
        
        # Check sync duration
        if self.logger.metrics["sync_duration"] > (self.alert_thresholds["sync_duration_minutes"] * 60):
            health_status["warnings"].append({
                "type": "slow_sync",
                "message": f"Sync duration {self.logger.metrics['sync_duration']:.1f}s exceeds normal range",
                "severity": "medium"
            })
        
        # Check rate limiting
        if self.logger.metrics["rate_limit_hits"] > self.alert_thresholds["rate_limit_hits_per_hour"]:
            health_status["warnings"].append({
                "type": "frequent_rate_limits",
                "message": f"Rate limit hits ({self.logger.metrics['rate_limit_hits']}) may indicate need for throttling",
                "severity": "medium"
            })
        
        # Save health status
        with open(self.alerts_file, 'w') as f:
            json.dumps(health_status, f, indent=2)
        
        return health_status
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert (placeholder for integration with notification systems)"""
        
        # This could be extended to integrate with:
        # - Slack webhooks
        # - Email notifications  
        # - PagerDuty
        # - Discord webhooks
        # - etc.
        
        self.logger.logger.error(f"ALERT: {alert['message']}")
        
        # For now, just log the alert
        print(f"🚨 ALERT: {alert['message']}")


def setup_sync_logging(log_dir: str = "/Users/masa/Projects/Claude-PM/logs", 
                      verbose: bool = False) -> Tuple[SyncLogger, SyncMonitor]:
    """Setup comprehensive sync logging and monitoring"""
    
    # Create sync logger
    sync_logger = SyncLogger(log_dir)
    
    # Adjust log levels based on verbose flag
    if verbose:
        logging.getLogger("github_sync").setLevel(logging.DEBUG)
    else:
        logging.getLogger("github_sync").setLevel(logging.INFO)
    
    # Create monitor
    monitor = SyncMonitor(sync_logger)
    
    return sync_logger, monitor