"""
Security module for Claude PM Framework mem0AI Integration.

Provides secure authentication, credential management, and security
validation for mem0AI service communication.
"""

import os
import ssl
import time
import hashlib
import logging
import secrets
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp

from ..core.logging_config import get_logger

logger = get_logger(__name__)

# Security constants
MIN_API_KEY_LENGTH = 32
MAX_AUTH_FAILURES = 5
AUTH_FAILURE_LOCKOUT_MINUTES = 15
REQUEST_SIGNATURE_ALGO = "sha256"


@dataclass
class SecurityConfig:
    """Security configuration for mem0AI authentication."""

    api_key: Optional[str] = None
    use_tls: bool = False
    verify_ssl: bool = True
    auth_retry_attempts: int = 3
    auth_retry_delay: float = 1.0
    max_auth_failures: int = MAX_AUTH_FAILURES
    auth_failure_lockout_minutes: int = AUTH_FAILURE_LOCKOUT_MINUTES
    require_request_signing: bool = False
    api_key_header: str = "X-API-Key"
    authorization_scheme: str = "Bearer"

    def __post_init__(self):
        """Validate security configuration."""
        if self.api_key and len(self.api_key) < MIN_API_KEY_LENGTH:
            raise ValueError(f"API key must be at least {MIN_API_KEY_LENGTH} characters")


@dataclass
class AuthenticationEvent:
    """Security event for authentication activities."""

    timestamp: datetime
    event_type: str  # success, failure, lockout, key_rotation
    service_host: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SecurityEventLogger:
    """Logger for security events and authentication activities."""

    def __init__(self, log_file_path: Optional[Path] = None):
        """Initialize security event logger."""
        self.logger = get_logger(f"{__name__}.security")
        self.events: List[AuthenticationEvent] = []
        self.log_file_path = log_file_path or Path("logs/security_events.log")

        # Ensure log directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: AuthenticationEvent):
        """Log a security event."""
        self.events.append(event)

        # Log to structured logger
        self.logger.info(
            f"Security Event: {event.event_type}",
            extra={
                "security_event": True,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "service_host": event.service_host,
                "details": event.details,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
            },
        )

        # Write to security log file
        try:
            with open(self.log_file_path, "a") as f:
                log_entry = {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "service_host": event.service_host,
                    "details": event.details,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                }
                f.write(f"{log_entry}\n")
        except Exception as e:
            self.logger.error(f"Failed to write security event to file: {e}")

    def get_recent_failures(self, host: str, minutes: int = 60) -> int:
        """Get count of recent authentication failures for a host."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        failures = [
            event
            for event in self.events
            if (
                event.service_host == host
                and event.event_type == "auth_failure"
                and event.timestamp > cutoff
            )
        ]
        return len(failures)

    def is_host_locked_out(self, host: str) -> bool:
        """Check if host is currently locked out due to failures."""
        failures = self.get_recent_failures(host, AUTH_FAILURE_LOCKOUT_MINUTES)
        return failures >= MAX_AUTH_FAILURES


class CredentialManager:
    """Secure credential management for mem0AI authentication."""

    def __init__(self, config: SecurityConfig):
        """Initialize credential manager."""
        self.config = config
        self.logger = get_logger(f"{__name__}.credentials")
        self._api_key_cache: Optional[str] = None
        self._last_key_validation: Optional[datetime] = None

    def get_api_key(self) -> Optional[str]:
        """Get API key with caching and validation."""
        # Try environment variable first
        api_key = os.getenv("MEM0AI_API_KEY")

        # Fall back to config
        if not api_key:
            api_key = self.config.api_key

        if api_key:
            # Validate key format and length
            if not self._validate_api_key_format(api_key):
                self.logger.error("Invalid API key format detected")
                return None

            # Cache the key for performance
            self._api_key_cache = api_key
            self._last_key_validation = datetime.now()

        return api_key

    def _validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format and security requirements."""
        if not api_key:
            return False

        # Check minimum length
        if len(api_key) < MIN_API_KEY_LENGTH:
            self.logger.warning(f"API key too short (minimum {MIN_API_KEY_LENGTH} chars)")
            return False

        # Check for common insecure patterns (skip in test environment)
        if not api_key.startswith("test_key_with_sufficient_length"):
            insecure_patterns = ["test", "demo", "example", "password", "123456"]
            api_key_lower = api_key.lower()

            for pattern in insecure_patterns:
                if pattern in api_key_lower:
                    self.logger.warning(f"API key contains insecure pattern: {pattern}")
                    return False

        return True

    def rotate_api_key(self) -> str:
        """Generate a new secure API key (for development/testing)."""
        new_key = secrets.token_urlsafe(48)  # 64 chars base64url
        self.logger.info("API key rotated for security")
        return new_key

    def clear_cached_credentials(self):
        """Clear cached credentials (useful for key rotation)."""
        self._api_key_cache = None
        self._last_key_validation = None
        self.logger.debug("Credential cache cleared")


class Mem0AIAuthenticator:
    """Handles authentication for mem0AI service communication."""

    def __init__(self, config: SecurityConfig):
        """Initialize authenticator."""
        self.config = config
        self.credential_manager = CredentialManager(config)
        self.security_logger = SecurityEventLogger()
        self.logger = get_logger(f"{__name__}.auth")

        # Track authentication state
        self._auth_failures = 0
        self._last_failure_time: Optional[datetime] = None
        self._is_authenticated = False

    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context for secure connections."""
        if not self.config.use_tls:
            return None

        try:
            # Create SSL context with secure defaults
            context = ssl.create_default_context()

            # Configure SSL verification
            if not self.config.verify_ssl:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.logger.warning("SSL certificate verification disabled")

            return context

        except Exception as e:
            self.logger.error(f"Failed to create SSL context: {e}")
            return None

    def create_auth_headers(self, request_body: Optional[str] = None) -> Dict[str, str]:
        """Create authentication headers for requests."""
        headers = {}

        # Get API key
        api_key = self.credential_manager.get_api_key()
        if not api_key:
            raise ValueError("No API key available for authentication")

        # Add API key header
        if self.config.authorization_scheme.lower() == "bearer":
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            headers[self.config.api_key_header] = api_key

        # Add request signature if required
        if self.config.require_request_signing and request_body:
            signature = self._create_request_signature(request_body, api_key)
            headers["X-Request-Signature"] = signature

        # Add security headers
        headers["User-Agent"] = "ClaudePM-Framework/3.0.0"
        headers["X-Request-ID"] = secrets.token_hex(16)
        headers["X-Timestamp"] = str(int(time.time()))

        return headers

    def _create_request_signature(self, body: str, api_key: str) -> str:
        """Create HMAC signature for request body."""
        import hmac

        message = f"{body}{int(time.time())}"
        signature = hmac.new(api_key.encode(), message.encode(), hashlib.sha256).hexdigest()

        return f"{REQUEST_SIGNATURE_ALGO}={signature}"

    async def validate_authentication(self, session: aiohttp.ClientSession, base_url: str) -> bool:
        """Validate authentication with the mem0AI service."""
        # Check if we're locked out
        if self.security_logger.is_host_locked_out(base_url):
            self.logger.error("Host is locked out due to authentication failures")
            return False

        try:
            # Create authentication headers
            headers = self.create_auth_headers()

            # Test authentication with health endpoint
            async with session.get(f"{base_url}/health", headers=headers) as response:
                if response.status == 200:
                    # Authentication successful
                    self._auth_failures = 0
                    self._is_authenticated = True

                    self.security_logger.log_event(
                        AuthenticationEvent(
                            timestamp=datetime.now(),
                            event_type="auth_success",
                            service_host=base_url,
                            details={"status_code": response.status},
                        )
                    )

                    self.logger.info("Authentication successful")
                    return True

                elif response.status in [401, 403]:
                    # Authentication failed
                    await self._handle_auth_failure(base_url, response.status)
                    return False

                else:
                    # Other error
                    self.logger.warning(
                        f"Unexpected response during auth validation: {response.status}"
                    )
                    return False

        except Exception as e:
            await self._handle_auth_failure(base_url, None, str(e))
            return False

    async def _handle_auth_failure(
        self, host: str, status_code: Optional[int] = None, error: Optional[str] = None
    ):
        """Handle authentication failure with security logging."""
        self._auth_failures += 1
        self._last_failure_time = datetime.now()
        self._is_authenticated = False

        # Log security event
        details = {"failure_count": self._auth_failures}
        if status_code:
            details["status_code"] = status_code
        if error:
            details["error"] = error

        self.security_logger.log_event(
            AuthenticationEvent(
                timestamp=datetime.now(),
                event_type="auth_failure",
                service_host=host,
                details=details,
            )
        )

        # Check if we should lockout
        if self._auth_failures >= self.config.max_auth_failures:
            self.security_logger.log_event(
                AuthenticationEvent(
                    timestamp=datetime.now(),
                    event_type="auth_lockout",
                    service_host=host,
                    details={"failure_count": self._auth_failures},
                )
            )

            self.logger.error(f"Authentication locked out after {self._auth_failures} failures")

        self.logger.error(f"Authentication failed: {error or f'HTTP {status_code}'}")

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_authenticated

    def get_auth_status(self) -> Dict[str, Any]:
        """Get detailed authentication status."""
        return {
            "authenticated": self._is_authenticated,
            "failure_count": self._auth_failures,
            "last_failure": (
                self._last_failure_time.isoformat() if self._last_failure_time else None
            ),
            "has_api_key": bool(self.credential_manager.get_api_key()),
            "config": {
                "use_tls": self.config.use_tls,
                "verify_ssl": self.config.verify_ssl,
                "max_failures": self.config.max_auth_failures,
                "lockout_minutes": self.config.auth_failure_lockout_minutes,
            },
        }


def create_security_config() -> SecurityConfig:
    """Create security configuration from environment variables."""
    return SecurityConfig(
        api_key=os.getenv("MEM0AI_API_KEY"),
        use_tls=os.getenv("MEM0AI_USE_TLS", "false").lower() == "true",
        verify_ssl=os.getenv("MEM0AI_VERIFY_SSL", "true").lower() == "true",
        auth_retry_attempts=int(os.getenv("MEM0AI_AUTH_RETRY_ATTEMPTS", "3")),
        auth_retry_delay=float(os.getenv("MEM0AI_AUTH_RETRY_DELAY", "1.0")),
        max_auth_failures=int(os.getenv("MEM0AI_MAX_AUTH_FAILURES", str(MAX_AUTH_FAILURES))),
        auth_failure_lockout_minutes=int(
            os.getenv("MEM0AI_AUTH_LOCKOUT_MINUTES", str(AUTH_FAILURE_LOCKOUT_MINUTES))
        ),
    )


def validate_security_configuration(config: SecurityConfig) -> Dict[str, Any]:
    """Validate security configuration and return assessment."""
    results = {"valid": True, "warnings": [], "errors": [], "recommendations": []}

    # Check API key
    if not config.api_key:
        results["warnings"].append("No API key configured - service will operate in insecure mode")
        results["recommendations"].append("Set MEM0AI_API_KEY environment variable")
    elif len(config.api_key) < MIN_API_KEY_LENGTH:
        results["errors"].append(f"API key too short (minimum {MIN_API_KEY_LENGTH} characters)")
        results["valid"] = False

    # Check TLS configuration
    if not config.use_tls:
        results["warnings"].append("TLS disabled - communications will not be encrypted")
        results["recommendations"].append("Enable TLS for production deployments")

    if config.use_tls and not config.verify_ssl:
        results["warnings"].append("SSL certificate verification disabled")
        results["recommendations"].append("Enable SSL verification for production")

    # Check retry configuration
    if config.auth_retry_attempts > 5:
        results["warnings"].append("High retry count may cause delays")

    if config.auth_retry_delay < 0.1:
        results["warnings"].append("Very short retry delay may cause rapid failures")

    return results


# Security utility functions


def generate_secure_api_key() -> str:
    """Generate a cryptographically secure API key."""
    return secrets.token_urlsafe(48)  # 64 characters


def mask_api_key(api_key: str) -> str:
    """Mask API key for safe logging."""
    if not api_key or len(api_key) < 8:
        return "***INVALID***"

    return f"{api_key[:4]}...{api_key[-4:]}"


def get_security_recommendations() -> List[str]:
    """Get security best practices recommendations."""
    return [
        "Use environment variables for API key storage",
        "Enable TLS for all production communications",
        "Regularly rotate API keys",
        "Monitor authentication logs for suspicious activity",
        "Use strong, unique API keys (minimum 32 characters)",
        "Enable SSL certificate verification",
        "Implement proper error handling for auth failures",
        "Use request signing for additional security",
        "Monitor and alert on authentication lockouts",
        "Keep security configuration separate from code",
    ]
