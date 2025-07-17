# Security Guide

## Overview

This guide covers security best practices, vulnerability management, and secure coding guidelines for the Claude PM Framework. Security is a critical aspect of the framework, especially when handling API keys, executing subprocesses, and managing user-defined agents.

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Input Validation                       │
│               (CLI arguments, API inputs)                │
├─────────────────────────────────────────────────────────┤
│                 Authentication Layer                     │
│              (API key management, access)                │
├─────────────────────────────────────────────────────────┤
│                Authorization Layer                       │
│           (Agent permissions, file access)               │
├─────────────────────────────────────────────────────────┤
│                 Execution Sandbox                        │
│          (Subprocess isolation, resource limits)         │
├─────────────────────────────────────────────────────────┤
│                   Data Protection                        │
│         (Encryption, secure storage, logging)            │
└─────────────────────────────────────────────────────────┘
```

### Security Principles

1. **Defense in Depth**: Multiple security layers
2. **Least Privilege**: Minimal permissions for operations
3. **Secure by Default**: Safe default configurations
4. **Zero Trust**: Verify all inputs and operations
5. **Audit Trail**: Comprehensive security logging

## API Key Management

### 1. Environment Variable Security

```python
import os
from typing import Optional

class SecureAPIKeyManager:
    """Secure API key management."""
    
    # Never hardcode keys
    ALLOWED_KEY_NAMES = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'GITHUB_TOKEN'
    ]
    
    @staticmethod
    def get_api_key(key_name: str) -> Optional[str]:
        """Securely retrieve API key."""
        if key_name not in SecureAPIKeyManager.ALLOWED_KEY_NAMES:
            raise ValueError(f"Unknown API key: {key_name}")
        
        key = os.environ.get(key_name)
        
        if not key:
            return None
        
        # Basic validation
        if len(key) < 20:
            raise ValueError(f"Invalid {key_name} format")
        
        # Never log the actual key
        import logging
        logging.debug(f"Retrieved {key_name} (length: {len(key)})")
        
        return key
    
    @staticmethod
    def validate_key_format(key_name: str, key: str) -> bool:
        """Validate API key format."""
        validators = {
            'OPENAI_API_KEY': lambda k: k.startswith('sk-'),
            'ANTHROPIC_API_KEY': lambda k: k.startswith('sk-ant-'),
            'GITHUB_TOKEN': lambda k: len(k) == 40
        }
        
        validator = validators.get(key_name, lambda k: True)
        return validator(key)
```

### 2. Secure Storage

```python
import keyring
from cryptography.fernet import Fernet
import json

class SecureCredentialStore:
    """Encrypted credential storage."""
    
    def __init__(self, app_name: str = 'claude_pm'):
        self.app_name = app_name
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption key."""
        # Get or create encryption key
        key = keyring.get_password(self.app_name, 'master_key')
        
        if not key:
            key = Fernet.generate_key().decode()
            keyring.set_password(self.app_name, 'master_key', key)
        
        self.cipher = Fernet(key.encode())
    
    def store_credential(self, name: str, value: str):
        """Store encrypted credential."""
        encrypted = self.cipher.encrypt(value.encode())
        keyring.set_password(self.app_name, name, encrypted.decode())
    
    def get_credential(self, name: str) -> Optional[str]:
        """Retrieve and decrypt credential."""
        encrypted = keyring.get_password(self.app_name, name)
        
        if not encrypted:
            return None
        
        try:
            decrypted = self.cipher.decrypt(encrypted.encode())
            return decrypted.decode()
        except Exception:
            # Invalid key or corrupted data
            return None
    
    def delete_credential(self, name: str):
        """Securely delete credential."""
        try:
            keyring.delete_password(self.app_name, name)
        except keyring.errors.PasswordDeleteError:
            pass
```

### 3. Key Rotation

```python
import time
from datetime import datetime, timedelta

class APIKeyRotation:
    """Manage API key rotation."""
    
    def __init__(self, credential_store: SecureCredentialStore):
        self.store = credential_store
    
    def should_rotate(self, key_name: str, max_age_days: int = 90) -> bool:
        """Check if key should be rotated."""
        last_rotation = self.store.get_credential(f"{key_name}_rotation_date")
        
        if not last_rotation:
            return True
        
        last_date = datetime.fromisoformat(last_rotation)
        age = datetime.now() - last_date
        
        return age > timedelta(days=max_age_days)
    
    def rotate_key(self, key_name: str, new_key: str):
        """Rotate API key."""
        # Store old key temporarily
        old_key = self.store.get_credential(key_name)
        if old_key:
            self.store.store_credential(f"{key_name}_old", old_key)
        
        # Store new key
        self.store.store_credential(key_name, new_key)
        self.store.store_credential(
            f"{key_name}_rotation_date", 
            datetime.now().isoformat()
        )
        
        # Log rotation (without exposing keys)
        import logging
        logging.info(f"Rotated {key_name} at {datetime.now()}")
```

## Input Validation and Sanitization

### 1. Command Line Input

```python
import re
import shlex
from typing import List, Optional

class InputValidator:
    """Validate and sanitize user inputs."""
    
    # Patterns for validation
    SAFE_PATH_PATTERN = re.compile(r'^[\w\-./]+$')
    SAFE_AGENT_NAME = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    @staticmethod
    def validate_file_path(path: str) -> str:
        """Validate and sanitize file path."""
        # Remove any null bytes
        path = path.replace('\0', '')
        
        # Normalize path
        from pathlib import Path
        normalized = Path(path).resolve()
        
        # Check for path traversal
        cwd = Path.cwd()
        try:
            normalized.relative_to(cwd)
        except ValueError:
            raise ValueError(f"Path traversal detected: {path}")
        
        return str(normalized)
    
    @staticmethod
    def validate_agent_name(name: str) -> str:
        """Validate agent name."""
        if not name or len(name) > 50:
            raise ValueError("Invalid agent name length")
        
        if not InputValidator.SAFE_AGENT_NAME.match(name):
            raise ValueError(f"Invalid agent name: {name}")
        
        return name
    
    @staticmethod
    def sanitize_shell_command(command: str) -> List[str]:
        """Safely parse shell command."""
        try:
            # Use shlex for safe parsing
            parts = shlex.split(command)
            
            # Validate each part
            for part in parts:
                if any(char in part for char in ['&', '|', ';', '$', '`']):
                    raise ValueError(f"Unsafe character in command: {part}")
            
            return parts
        except ValueError as e:
            raise ValueError(f"Invalid command: {e}")
```

### 2. Agent Input Validation

```python
import yaml
from marshmallow import Schema, fields, validates, ValidationError

class AgentMetadataSchema(Schema):
    """Validate agent metadata."""
    
    nickname = fields.Str(required=True, validate=lambda x: len(x) <= 20)
    type = fields.Str(required=True)
    specializations = fields.List(fields.Str(), required=True)
    authority = fields.Str(required=True)
    
    @validates('type')
    def validate_type(self, value):
        """Validate agent type."""
        allowed_types = [
            'documentation', 'qa', 'security', 'performance',
            'architecture', 'custom'
        ]
        if value not in allowed_types:
            raise ValidationError(f"Invalid agent type: {value}")

def validate_agent_file(file_path: str) -> Dict:
    """Validate agent file content."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract metadata section
    metadata = extract_metadata(content)
    
    # Validate schema
    schema = AgentMetadataSchema()
    try:
        validated = schema.load(metadata)
        return validated
    except ValidationError as e:
        raise ValueError(f"Invalid agent metadata: {e.messages}")
```

## Subprocess Security

### 1. Secure Subprocess Execution

```python
import subprocess
import resource
import os
from typing import Dict, List, Optional

class SecureSubprocess:
    """Secure subprocess execution."""
    
    @staticmethod
    def execute(
        command: List[str],
        timeout: int = 30,
        memory_limit_mb: int = 512,
        env: Optional[Dict[str, str]] = None,
        allowed_paths: Optional[List[str]] = None
    ) -> subprocess.CompletedProcess:
        """Execute subprocess with security constraints."""
        
        # Validate command
        if not command or not isinstance(command, list):
            raise ValueError("Invalid command format")
        
        # Prepare secure environment
        secure_env = os.environ.copy()
        if env:
            # Only allow specific environment variables
            allowed_env_vars = ['PATH', 'HOME', 'USER']
            for key, value in env.items():
                if key in allowed_env_vars:
                    secure_env[key] = value
        
        # Remove sensitive variables
        for key in ['API_KEY', 'SECRET', 'TOKEN', 'PASSWORD']:
            secure_env.pop(key, None)
            for env_key in list(secure_env.keys()):
                if key in env_key:
                    secure_env.pop(env_key, None)
        
        def set_limits():
            """Set resource limits for subprocess."""
            # Memory limit
            resource.setrlimit(
                resource.RLIMIT_AS,
                (memory_limit_mb * 1024 * 1024, memory_limit_mb * 1024 * 1024)
            )
            
            # CPU time limit
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (timeout, timeout)
            )
            
            # Disable core dumps
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        
        try:
            # Execute with limits
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=secure_env,
                preexec_fn=set_limits if os.name != 'nt' else None,
                # Prevent shell injection
                shell=False
            )
            
            return result
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out after {timeout}s")
        except Exception as e:
            raise RuntimeError(f"Subprocess execution failed: {e}")
```

### 2. Agent Sandboxing

```python
import tempfile
import shutil
from contextlib import contextmanager
from pathlib import Path

class AgentSandbox:
    """Sandbox environment for agent execution."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.sandbox_dir = None
    
    @contextmanager
    def create_sandbox(self):
        """Create isolated sandbox environment."""
        try:
            # Create temporary directory
            self.sandbox_dir = tempfile.mkdtemp(prefix=f"agent_{self.agent_id}_")
            sandbox_path = Path(self.sandbox_dir)
            
            # Set restrictive permissions
            sandbox_path.chmod(0o700)
            
            # Create allowed subdirectories
            (sandbox_path / 'input').mkdir()
            (sandbox_path / 'output').mkdir()
            (sandbox_path / 'temp').mkdir()
            
            yield sandbox_path
            
        finally:
            # Clean up sandbox
            if self.sandbox_dir and Path(self.sandbox_dir).exists():
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)
    
    def copy_allowed_files(self, files: List[str], sandbox_path: Path):
        """Copy allowed files to sandbox."""
        input_dir = sandbox_path / 'input'
        
        for file_path in files:
            # Validate file path
            source = Path(file_path).resolve()
            if not source.exists():
                continue
            
            # Copy to sandbox
            dest = input_dir / source.name
            shutil.copy2(source, dest)
            
            # Make read-only
            dest.chmod(0o400)
```

## Access Control

### 1. Permission Management

```python
from enum import Enum
from typing import Set, Dict

class Permission(Enum):
    """Agent permissions."""
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    EXECUTE_COMMANDS = "execute_commands"
    NETWORK_ACCESS = "network_access"
    SYSTEM_CONFIG = "system_config"

class AgentPermissions:
    """Manage agent permissions."""
    
    # Default permissions by agent type
    DEFAULT_PERMISSIONS = {
        'documentation': {Permission.READ_FILES},
        'qa': {Permission.READ_FILES, Permission.EXECUTE_COMMANDS},
        'engineer': {Permission.READ_FILES, Permission.WRITE_FILES},
        'security': {Permission.READ_FILES},
        'ops': {Permission.READ_FILES, Permission.EXECUTE_COMMANDS, Permission.SYSTEM_CONFIG}
    }
    
    def __init__(self):
        self.permissions: Dict[str, Set[Permission]] = {}
    
    def get_permissions(self, agent_type: str) -> Set[Permission]:
        """Get permissions for agent type."""
        return self.DEFAULT_PERMISSIONS.get(agent_type, set())
    
    def check_permission(self, agent_type: str, permission: Permission) -> bool:
        """Check if agent has permission."""
        agent_perms = self.get_permissions(agent_type)
        return permission in agent_perms
    
    def enforce_permission(self, agent_type: str, permission: Permission):
        """Enforce permission check."""
        if not self.check_permission(agent_type, permission):
            raise PermissionError(
                f"Agent '{agent_type}' lacks permission: {permission.value}"
            )
```

### 2. File Access Control

```python
import os
from pathlib import Path
from typing import List, Optional

class FileAccessControl:
    """Control file system access."""
    
    def __init__(self, allowed_paths: Optional[List[str]] = None):
        self.allowed_paths = allowed_paths or [os.getcwd()]
        self._validate_allowed_paths()
    
    def _validate_allowed_paths(self):
        """Validate allowed paths exist."""
        validated = []
        for path in self.allowed_paths:
            resolved = Path(path).resolve()
            if resolved.exists():
                validated.append(str(resolved))
        self.allowed_paths = validated
    
    def is_allowed(self, file_path: str) -> bool:
        """Check if file access is allowed."""
        target = Path(file_path).resolve()
        
        # Check if within allowed paths
        for allowed in self.allowed_paths:
            allowed_path = Path(allowed).resolve()
            try:
                target.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        
        return False
    
    def validate_access(self, file_path: str, mode: str = 'r'):
        """Validate file access."""
        if not self.is_allowed(file_path):
            raise PermissionError(f"Access denied: {file_path}")
        
        target = Path(file_path)
        
        # Check file permissions
        if mode == 'r' and not os.access(target, os.R_OK):
            raise PermissionError(f"Read access denied: {file_path}")
        elif mode == 'w' and not os.access(target.parent, os.W_OK):
            raise PermissionError(f"Write access denied: {file_path}")
```

## Security Logging and Monitoring

### 1. Security Event Logging

```python
import logging
import json
from datetime import datetime
from typing import Dict, Any

class SecurityLogger:
    """Log security-related events."""
    
    def __init__(self, log_file: str = 'security_events.log'):
        self.logger = logging.getLogger('security')
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        # Remove sensitive data
        sanitized = self._sanitize_event(event)
        
        self.logger.info(json.dumps(sanitized))
    
    def _sanitize_event(self, event: Dict) -> Dict:
        """Remove sensitive data from events."""
        sensitive_keys = ['password', 'token', 'key', 'secret']
        
        def sanitize_dict(d: Dict) -> Dict:
            sanitized = {}
            for key, value in d.items():
                if any(s in key.lower() for s in sensitive_keys):
                    sanitized[key] = '***REDACTED***'
                elif isinstance(value, dict):
                    sanitized[key] = sanitize_dict(value)
                else:
                    sanitized[key] = value
            return sanitized
        
        return sanitize_dict(event)
    
    def log_auth_attempt(self, success: bool, user: str, method: str):
        """Log authentication attempt."""
        self.log_event('auth_attempt', {
            'success': success,
            'user': user,
            'method': method
        })
    
    def log_permission_denied(self, agent: str, resource: str, permission: str):
        """Log permission denied event."""
        self.log_event('permission_denied', {
            'agent': agent,
            'resource': resource,
            'permission': permission
        })
```

### 2. Intrusion Detection

```python
from collections import defaultdict
import time

class IntrusionDetector:
    """Detect potential security threats."""
    
    def __init__(self):
        self.failed_attempts = defaultdict(list)
        self.rate_limits = defaultdict(list)
    
    def check_failed_attempts(self, identifier: str, window: int = 300) -> bool:
        """Check for too many failed attempts."""
        now = time.time()
        
        # Clean old attempts
        self.failed_attempts[identifier] = [
            t for t in self.failed_attempts[identifier]
            if now - t < window
        ]
        
        # Check threshold
        if len(self.failed_attempts[identifier]) >= 5:
            return True  # Potential attack
        
        return False
    
    def record_failed_attempt(self, identifier: str):
        """Record failed attempt."""
        self.failed_attempts[identifier].append(time.time())
    
    def check_rate_limit(self, identifier: str, max_requests: int = 100, 
                        window: int = 60) -> bool:
        """Check rate limiting."""
        now = time.time()
        
        # Clean old requests
        self.rate_limits[identifier] = [
            t for t in self.rate_limits[identifier]
            if now - t < window
        ]
        
        # Check limit
        if len(self.rate_limits[identifier]) >= max_requests:
            return True  # Rate limit exceeded
        
        return False
    
    def record_request(self, identifier: str):
        """Record request for rate limiting."""
        self.rate_limits[identifier].append(time.time())
```

## Vulnerability Management

### 1. Dependency Scanning

```python
import subprocess
import json

class DependencyScanner:
    """Scan for vulnerable dependencies."""
    
    @staticmethod
    def scan_python_deps() -> List[Dict]:
        """Scan Python dependencies for vulnerabilities."""
        try:
            # Run safety check
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return []  # No vulnerabilities
            
            vulnerabilities = json.loads(result.stdout)
            return vulnerabilities
            
        except Exception as e:
            logging.error(f"Dependency scan failed: {e}")
            return []
    
    @staticmethod
    def scan_npm_deps() -> List[Dict]:
        """Scan npm dependencies for vulnerabilities."""
        try:
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                capture_output=True,
                text=True
            )
            
            audit_data = json.loads(result.stdout)
            return audit_data.get('vulnerabilities', {})
            
        except Exception as e:
            logging.error(f"NPM audit failed: {e}")
            return []
```

### 2. Security Headers

```python
from typing import Dict

class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
```

## Security Checklist

### Development
- [ ] Never hardcode secrets or API keys
- [ ] Validate all user inputs
- [ ] Use parameterized queries for databases
- [ ] Implement proper error handling without exposing internals
- [ ] Use secure random number generation
- [ ] Keep dependencies updated

### API Keys
- [ ] Store keys in environment variables
- [ ] Use secure credential storage for persistent keys
- [ ] Implement key rotation
- [ ] Monitor key usage
- [ ] Never log API keys

### Subprocess Execution
- [ ] Validate and sanitize all inputs
- [ ] Use subprocess with shell=False
- [ ] Set resource limits
- [ ] Use sandbox environments
- [ ] Monitor subprocess execution

### File Operations
- [ ] Validate all file paths
- [ ] Prevent path traversal
- [ ] Set appropriate permissions
- [ ] Use secure temporary files
- [ ] Clean up sensitive files

### Logging
- [ ] Never log sensitive information
- [ ] Use structured logging
- [ ] Monitor security events
- [ ] Implement log rotation
- [ ] Secure log files

## Incident Response

### 1. Security Incident Handler

```python
class SecurityIncidentHandler:
    """Handle security incidents."""
    
    def __init__(self, security_logger: SecurityLogger):
        self.logger = security_logger
    
    def handle_incident(self, incident_type: str, details: Dict):
        """Handle security incident."""
        # Log incident
        self.logger.log_event(f'incident_{incident_type}', details)
        
        # Take action based on type
        if incident_type == 'intrusion_attempt':
            self._handle_intrusion(details)
        elif incident_type == 'data_breach':
            self._handle_data_breach(details)
        elif incident_type == 'malicious_agent':
            self._handle_malicious_agent(details)
    
    def _handle_intrusion(self, details: Dict):
        """Handle intrusion attempt."""
        # Block IP/user
        # Alert administrators
        # Increase monitoring
        pass
    
    def _handle_data_breach(self, details: Dict):
        """Handle data breach."""
        # Isolate affected systems
        # Preserve evidence
        # Notify stakeholders
        pass
    
    def _handle_malicious_agent(self, details: Dict):
        """Handle malicious agent detection."""
        # Quarantine agent
        # Block execution
        # Alert user
        pass
```

## Reporting Security Issues

For security vulnerabilities, please:

1. **Do NOT** create public GitHub issues
2. Email security concerns to: security@claudepm.dev
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fixes (if any)

We aim to respond within 48 hours and provide fixes promptly.

---

*Security is everyone's responsibility. Stay vigilant and keep the framework secure.*