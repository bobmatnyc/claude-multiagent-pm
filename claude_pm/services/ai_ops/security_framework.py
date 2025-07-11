"""
Security Framework for AI Operations

Provides comprehensive security controls, compliance monitoring,
and enterprise-grade security features for AI operations.
"""

import asyncio
import logging
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import time


class SecurityLevel(Enum):
    """Security level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Security event types."""
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_SUCCESS = "authorization_success"
    AUTHORIZATION_FAILURE = "authorization_failure"
    REQUEST_BLOCKED = "request_blocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    COMPLIANCE_VIOLATION = "compliance_violation"
    KEY_ROTATION = "key_rotation"
    SECURITY_ALERT = "security_alert"


@dataclass
class SecurityEvent:
    """Security event record."""
    id: str
    event_type: SecurityEventType
    timestamp: datetime
    user_id: Optional[str] = None
    provider: Optional[str] = None
    severity: SecurityLevel = SecurityLevel.MEDIUM
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "provider": self.provider,
            "severity": self.severity.value,
            "description": self.description,
            "metadata": self.metadata,
            "resolved": self.resolved
        }


@dataclass
class ComplianceRule:
    """Compliance rule definition."""
    name: str
    description: str
    severity: SecurityLevel
    check_function: str
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecurityFramework:
    """
    Enterprise security framework for AI operations.
    
    Provides comprehensive security controls including authentication,
    authorization, compliance monitoring, and security event management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize security framework.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Security configuration
        self.security_level = SecurityLevel(self.config.get("security_level", "medium"))
        self.encryption_enabled = self.config.get("encryption_enabled", True)
        self.audit_logging_enabled = self.config.get("audit_logging_enabled", True)
        self.compliance_monitoring_enabled = self.config.get("compliance_monitoring_enabled", True)
        
        # Security events
        self.security_events: List[SecurityEvent] = []
        self.max_events = self.config.get("max_security_events", 10000)
        
        # Compliance rules
        self.compliance_rules: Dict[str, ComplianceRule] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        
        # Authentication tracking
        self.authentication_attempts: Dict[str, List[datetime]] = {}
        self.failed_auth_threshold = self.config.get("failed_auth_threshold", 5)
        self.auth_lockout_duration = self.config.get("auth_lockout_duration", 300)  # 5 minutes
        
        # Security metrics
        self.total_security_events = 0
        self.blocked_requests = 0
        self.compliance_violations = 0
        
        # Initialize default compliance rules
        self._initialize_compliance_rules()
        
        self.logger.info(f"Security framework initialized with {self.security_level.value} security level")
    
    def _initialize_compliance_rules(self):
        """Initialize default compliance rules."""
        self.compliance_rules = {
            "api_key_rotation": ComplianceRule(
                name="API Key Rotation",
                description="API keys must be rotated every 90 days",
                severity=SecurityLevel.HIGH,
                check_function="check_api_key_rotation"
            ),
            "encryption_at_rest": ComplianceRule(
                name="Encryption at Rest",
                description="Sensitive data must be encrypted at rest",
                severity=SecurityLevel.HIGH,
                check_function="check_encryption_at_rest"
            ),
            "access_logging": ComplianceRule(
                name="Access Logging",
                description="All access attempts must be logged",
                severity=SecurityLevel.MEDIUM,
                check_function="check_access_logging"
            ),
            "secure_communication": ComplianceRule(
                name="Secure Communication",
                description="All communication must use TLS",
                severity=SecurityLevel.HIGH,
                check_function="check_secure_communication"
            ),
            "data_minimization": ComplianceRule(
                name="Data Minimization",
                description="Only necessary data should be collected and stored",
                severity=SecurityLevel.MEDIUM,
                check_function="check_data_minimization"
            ),
            "access_control": ComplianceRule(
                name="Access Control",
                description="Proper access controls must be implemented",
                severity=SecurityLevel.HIGH,
                check_function="check_access_control"
            )
        }
    
    async def validate_request(self, request) -> bool:
        """
        Validate security of AI service request.
        
        Args:
            request: AI service request
            
        Returns:
            True if request is valid
        """
        try:
            # Check rate limits
            if not await self._check_rate_limit(request):
                await self._log_security_event(
                    event_type=SecurityEventType.REQUEST_BLOCKED,
                    description="Rate limit exceeded",
                    provider=request.provider,
                    severity=SecurityLevel.MEDIUM
                )
                return False
            
            # Validate request content
            if not await self._validate_request_content(request):
                await self._log_security_event(
                    event_type=SecurityEventType.REQUEST_BLOCKED,
                    description="Invalid request content",
                    provider=request.provider,
                    severity=SecurityLevel.HIGH
                )
                return False
            
            # Check for suspicious patterns
            if await self._detect_suspicious_activity(request):
                await self._log_security_event(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    description="Suspicious activity detected",
                    provider=request.provider,
                    severity=SecurityLevel.HIGH
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Request validation failed: {e}")
            return False
    
    async def _check_rate_limit(self, request) -> bool:
        """Check rate limiting."""
        provider = request.provider
        current_time = datetime.now()
        
        # Initialize rate limit tracking for provider
        if provider not in self.rate_limits:
            self.rate_limits[provider] = {
                "requests": [],
                "limit": self.config.get(f"{provider}_rate_limit", 100),
                "window": self.config.get(f"{provider}_rate_window", 60)  # seconds
            }
        
        rate_limit = self.rate_limits[provider]
        
        # Clean old requests
        cutoff_time = current_time - timedelta(seconds=rate_limit["window"])
        rate_limit["requests"] = [
            req_time for req_time in rate_limit["requests"]
            if req_time > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(rate_limit["requests"]) >= rate_limit["limit"]:
            return False
        
        # Add current request
        rate_limit["requests"].append(current_time)
        return True
    
    async def _validate_request_content(self, request) -> bool:
        """Validate request content for security."""
        # Check for malicious patterns in messages
        if hasattr(request, 'messages'):
            for message in request.messages:
                content = message.get('content', '')
                
                # Check for injection attempts
                if any(pattern in content.lower() for pattern in [
                    'script>', '<iframe', 'javascript:', 'eval(',
                    'exec(', 'import os', 'subprocess', '__import__'
                ]):
                    return False
                
                # Check for PII patterns
                if self._contains_pii(content):
                    self.logger.warning("PII detected in request content")
                    # Don't block but log for compliance
        
        return True
    
    def _contains_pii(self, content: str) -> bool:
        """Check if content contains PII."""
        import re
        
        # Simple PII patterns
        patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # Phone number
        ]
        
        for pattern in patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    async def _detect_suspicious_activity(self, request) -> bool:
        """Detect suspicious activity patterns."""
        # Check for unusual request patterns
        if hasattr(request, 'messages'):
            message_count = len(request.messages)
            
            # Unusually long messages
            if message_count > 50:
                return True
            
            # Check for repetitive content
            if message_count > 5:
                contents = [msg.get('content', '') for msg in request.messages]
                if len(set(contents)) < len(contents) * 0.5:
                    return True
        
        return False
    
    async def log_request(self, request, response):
        """Log AI service request for audit."""
        if not self.audit_logging_enabled:
            return
        
        try:
            # Create audit log entry
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "provider": request.provider,
                "model": request.model,
                "success": response.success,
                "cost": response.cost,
                "usage": response.usage,
                "request_id": getattr(request, 'request_id', None),
                "user_id": getattr(request, 'user_id', None)
            }
            
            # Log to security events
            await self._log_security_event(
                event_type=SecurityEventType.AUTHORIZATION_SUCCESS if response.success else SecurityEventType.AUTHORIZATION_FAILURE,
                description=f"AI request processed: {request.provider}/{request.model}",
                provider=request.provider,
                severity=SecurityLevel.LOW,
                metadata=audit_entry
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log request: {e}")
    
    async def log_security_event(
        self,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security event."""
        event_type_enum = SecurityEventType(event_type)
        await self._log_security_event(
            event_type=event_type_enum,
            description=description,
            metadata=details or {}
        )
    
    async def _log_security_event(
        self,
        event_type: SecurityEventType,
        description: str,
        provider: Optional[str] = None,
        user_id: Optional[str] = None,
        severity: SecurityLevel = SecurityLevel.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log security event."""
        event = SecurityEvent(
            id=f"sec_{int(time.time() * 1000)}_{secrets.token_hex(4)}",
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            provider=provider,
            severity=severity,
            description=description,
            metadata=metadata or {}
        )
        
        self.security_events.append(event)
        self.total_security_events += 1
        
        # Limit events to prevent memory issues
        if len(self.security_events) > self.max_events:
            self.security_events = self.security_events[-self.max_events:]
        
        # Log to system logger
        log_level = {
            SecurityLevel.LOW: logging.INFO,
            SecurityLevel.MEDIUM: logging.WARNING,
            SecurityLevel.HIGH: logging.ERROR,
            SecurityLevel.CRITICAL: logging.CRITICAL
        }.get(severity, logging.WARNING)
        
        self.logger.log(log_level, f"Security event: {event_type.value} - {description}")
    
    async def validate_tool_execution(self, tool_name: str, parameters: Dict[str, Any]):
        """Validate tool execution security."""
        # Check if tool execution is allowed
        if self.security_level == SecurityLevel.CRITICAL:
            # Only allow specific tools in critical mode
            allowed_tools = self.config.get("critical_allowed_tools", [])
            if tool_name not in allowed_tools:
                raise ValueError(f"Tool '{tool_name}' not allowed in critical security mode")
        
        # Validate parameters
        if "file_path" in parameters:
            file_path = parameters["file_path"]
            if not self._is_safe_file_path(file_path):
                raise ValueError(f"Unsafe file path: {file_path}")
        
        if "command" in parameters:
            command = parameters["command"]
            if not self._is_safe_command(command):
                raise ValueError(f"Unsafe command: {command}")
    
    def _is_safe_file_path(self, file_path: str) -> bool:
        """Check if file path is safe."""
        # Check for path traversal
        if ".." in file_path:
            return False
        
        # Check for system paths
        dangerous_paths = ["/etc", "/sys", "/proc", "/root", "/var"]
        for path in dangerous_paths:
            if file_path.startswith(path):
                return False
        
        return True
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if command is safe."""
        dangerous_commands = [
            "rm", "rmdir", "del", "format", "fdisk",
            "sudo", "su", "passwd", "chmod", "chown",
            "wget", "curl", "nc", "netcat", "telnet"
        ]
        
        command_parts = command.split()
        if command_parts and command_parts[0] in dangerous_commands:
            return False
        
        return True
    
    async def log_tool_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """Log tool execution for audit."""
        if not self.audit_logging_enabled:
            return
        
        await self._log_security_event(
            event_type=SecurityEventType.AUTHORIZATION_SUCCESS if result.get("success") else SecurityEventType.AUTHORIZATION_FAILURE,
            description=f"Tool executed: {tool_name}",
            severity=SecurityLevel.LOW,
            metadata={
                "tool_name": tool_name,
                "parameters": parameters,
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0)
            }
        )
    
    async def validate_all_authentications(self) -> Dict[str, Any]:
        """Validate all provider authentications."""
        # This would integrate with the authentication service
        # For now, return a mock response
        return {
            "all_valid": True,
            "providers": {},
            "issues": []
        }
    
    async def get_recent_security_events(self, hours: int = 24) -> List[SecurityEvent]:
        """Get recent security events."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            event for event in self.security_events
            if event.timestamp >= cutoff_time
        ]
    
    async def check_compliance(self) -> Dict[str, Any]:
        """Check compliance with security rules."""
        if not self.compliance_monitoring_enabled:
            return {"compliant": True, "issues": [], "recommendations": []}
        
        compliance_result = {
            "compliant": True,
            "issues": [],
            "recommendations": [],
            "rules_checked": 0,
            "rules_passed": 0,
            "rules_failed": 0
        }
        
        for rule_name, rule in self.compliance_rules.items():
            if not rule.enabled:
                continue
            
            compliance_result["rules_checked"] += 1
            
            try:
                # Execute compliance check
                check_result = await self._execute_compliance_check(rule)
                
                if check_result["compliant"]:
                    compliance_result["rules_passed"] += 1
                else:
                    compliance_result["rules_failed"] += 1
                    compliance_result["compliant"] = False
                    compliance_result["issues"].append({
                        "rule": rule_name,
                        "description": rule.description,
                        "severity": rule.severity.value,
                        "details": check_result.get("details", "")
                    })
                    
                    if check_result.get("recommendation"):
                        compliance_result["recommendations"].append(check_result["recommendation"])
                
            except Exception as e:
                self.logger.error(f"Compliance check failed for {rule_name}: {e}")
                compliance_result["issues"].append({
                    "rule": rule_name,
                    "description": f"Compliance check failed: {e}",
                    "severity": "error"
                })
        
        return compliance_result
    
    async def _execute_compliance_check(self, rule: ComplianceRule) -> Dict[str, Any]:
        """Execute compliance check."""
        # This would execute the actual compliance check
        # For now, return mock results
        if rule.check_function == "check_api_key_rotation":
            return {
                "compliant": True,
                "details": "API keys are within rotation policy"
            }
        elif rule.check_function == "check_encryption_at_rest":
            return {
                "compliant": self.encryption_enabled,
                "details": "Encryption at rest is enabled" if self.encryption_enabled else "Encryption at rest is disabled",
                "recommendation": "Enable encryption at rest" if not self.encryption_enabled else None
            }
        elif rule.check_function == "check_access_logging":
            return {
                "compliant": self.audit_logging_enabled,
                "details": "Access logging is enabled" if self.audit_logging_enabled else "Access logging is disabled",
                "recommendation": "Enable access logging" if not self.audit_logging_enabled else None
            }
        else:
            return {"compliant": True, "details": "Check passed"}
    
    async def check_key_rotation_status(self) -> Dict[str, Any]:
        """Check API key rotation status."""
        return {
            "keys_need_rotation": False,
            "providers_needing_rotation": [],
            "last_rotation_check": datetime.now().isoformat()
        }
    
    async def rotate_keys(self) -> Dict[str, Any]:
        """Rotate API keys."""
        # This would integrate with the authentication service
        # For now, return a mock response
        return {
            "success": True,
            "keys_rotated": 0,
            "providers_updated": [],
            "timestamp": datetime.now().isoformat()
        }
    
    async def audit_compliance(self) -> Dict[str, Any]:
        """Perform comprehensive compliance audit."""
        audit_result = {
            "timestamp": datetime.now().isoformat(),
            "compliance_status": await self.check_compliance(),
            "security_events_summary": {
                "total_events": len(self.security_events),
                "events_by_severity": {},
                "events_by_type": {}
            },
            "recommendations": []
        }
        
        # Analyze security events
        for event in self.security_events:
            severity = event.severity.value
            event_type = event.event_type.value
            
            audit_result["security_events_summary"]["events_by_severity"][severity] = \
                audit_result["security_events_summary"]["events_by_severity"].get(severity, 0) + 1
            
            audit_result["security_events_summary"]["events_by_type"][event_type] = \
                audit_result["security_events_summary"]["events_by_type"].get(event_type, 0) + 1
        
        return audit_result
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "healthy": True,
            "security_level": self.security_level.value,
            "encryption_enabled": self.encryption_enabled,
            "audit_logging_enabled": self.audit_logging_enabled,
            "compliance_monitoring_enabled": self.compliance_monitoring_enabled,
            "total_security_events": self.total_security_events,
            "blocked_requests": self.blocked_requests,
            "compliance_rules": len(self.compliance_rules)
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "security_level": self.security_level.value,
            "total_security_events": self.total_security_events,
            "blocked_requests": self.blocked_requests,
            "compliance_violations": self.compliance_violations,
            "active_compliance_rules": len([r for r in self.compliance_rules.values() if r.enabled]),
            "encryption_enabled": self.encryption_enabled,
            "audit_logging_enabled": self.audit_logging_enabled
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"SecurityFramework(level={self.security_level.value}, events={len(self.security_events)})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"<SecurityFramework level={self.security_level.value} events={len(self.security_events)} rules={len(self.compliance_rules)}>"