# mem0AI Integration Security Guide

## Overview

This guide covers the security implementation for the Claude PM Framework's mem0AI integration, including API authentication, credential management, and security best practices.

## Security Architecture

The mem0AI integration implements a layered security approach:

1. **API Key Authentication** - Bearer token or custom header authentication
2. **TLS/SSL Encryption** - Secure communication channels
3. **Request Signing** - Optional HMAC-based request integrity verification
4. **Credential Management** - Secure storage and rotation of API keys
5. **Security Event Logging** - Comprehensive audit trail
6. **Failure Lockout Protection** - Rate limiting and lockout mechanisms

## Configuration

### Environment Variables

Configure security settings using environment variables:

```bash
# Required: API Key for mem0AI service authentication
MEM0AI_API_KEY=your_secure_api_key_here

# Service Configuration
MEM0AI_HOST=localhost
MEM0AI_PORT=8002
MEM0AI_TIMEOUT=30

# Security Configuration
MEM0AI_USE_TLS=false              # Enable TLS/HTTPS (recommended for production)
MEM0AI_VERIFY_SSL=true            # Verify SSL certificates (recommended)
MEM0AI_AUTH_RETRY_ATTEMPTS=3      # Authentication retry attempts
MEM0AI_AUTH_RETRY_DELAY=1.0       # Delay between retries (seconds)
MEM0AI_MAX_AUTH_FAILURES=5        # Max failures before lockout
MEM0AI_AUTH_LOCKOUT_MINUTES=15    # Lockout duration (minutes)
```

### Security Configuration Classes

```python
from claude_pm.integrations.security import SecurityConfig, create_security_config

# Create security configuration from environment
security_config = create_security_config()

# Or create custom configuration
security_config = SecurityConfig(
    api_key="your_secure_api_key_here",
    use_tls=True,
    verify_ssl=True,
    auth_retry_attempts=3,
    max_auth_failures=5,
    auth_failure_lockout_minutes=15
)
```

## API Key Management

### Generating Secure API Keys

```python
from claude_pm.integrations.security import generate_secure_api_key

# Generate a cryptographically secure API key
api_key = generate_secure_api_key()
print(f"Generated API key: {api_key}")
```

### API Key Requirements

- **Minimum Length**: 32 characters
- **Entropy**: Cryptographically secure random generation
- **Storage**: Environment variables only, never in code
- **Rotation**: Regular rotation recommended (quarterly)

### API Key Validation

The system validates API keys for:
- Minimum length requirements
- Common insecure patterns (test, demo, password, etc.)
- Format and character set validity

## Authentication Flow

### Basic Authentication

```python
from claude_pm.integrations.mem0ai_integration import create_mem0ai_integration

# Create integration with API key authentication
integration = create_mem0ai_integration(
    host="localhost",
    port=8002,
    api_key="your_secure_api_key_here"
)

# Connect with authentication
async with integration:
    if integration.is_authenticated():
        print("Successfully authenticated!")
    else:
        print("Authentication failed!")
```

### Secure Integration (TLS + Authentication)

```python
from claude_pm.integrations.mem0ai_integration import create_secure_mem0ai_integration

# Create secure integration with TLS and authentication
integration = create_secure_mem0ai_integration(
    host="mem0ai.yourdomain.com",
    port=443,
    api_key="your_secure_api_key_here"
)
```

## TLS/SSL Configuration

### Development Environment

```python
# Basic development setup (no TLS)
integration = create_mem0ai_integration(
    host="localhost",
    port=8002,
    api_key="dev_key_with_sufficient_length_123",
    use_tls=False
)
```

### Production Environment

```python
# Production setup with TLS
integration = create_mem0ai_integration(
    host="mem0ai.production.com",
    port=443,
    api_key=os.getenv("MEM0AI_PRODUCTION_API_KEY"),
    use_tls=True,
    verify_ssl=True
)
```

### Custom SSL Context

```python
from claude_pm.integrations.security import Mem0AIAuthenticator

authenticator = Mem0AIAuthenticator(security_config)
ssl_context = authenticator.create_ssl_context()

# The SSL context is automatically used by the integration
```

## Security Event Logging

### Viewing Security Events

```python
from claude_pm.integrations.security import SecurityEventLogger

# Access security logger from authenticator
logger = integration.authenticator.security_logger

# View recent events
for event in logger.events[-10:]:  # Last 10 events
    print(f"{event.timestamp}: {event.event_type} - {event.service_host}")

# Check recent failures
failures = logger.get_recent_failures("localhost:8002", minutes=60)
print(f"Failures in last hour: {failures}")

# Check lockout status
locked_out = logger.is_host_locked_out("localhost:8002")
print(f"Host locked out: {locked_out}")
```

### Security Event Types

- `auth_success` - Successful authentication
- `auth_failure` - Authentication failure
- `auth_lockout` - Host locked out due to failures
- `key_rotation` - API key rotation event

### Log File Location

Security events are logged to: `logs/security_events.log`

## Error Handling

### Authentication Errors

```python
async def handle_authentication():
    try:
        async with integration:
            # Perform operations
            pass
    except ValueError as e:
        if "No API key available" in str(e):
            print("❌ API key not configured")
        elif "API key must be at least" in str(e):
            print("❌ API key too short")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
```

### Checking Authentication Status

```python
# Get detailed security status
status = integration.get_security_status()
print(f"Connected: {status['connected']}")
print(f"Authenticated: {status['authenticated']}")
print(f"TLS Enabled: {status['tls_enabled']}")
print(f"API Key Configured: {status['api_key_configured']}")

# Get authenticator-specific status
auth_status = integration.authenticator.get_auth_status()
print(f"Failure Count: {auth_status['failure_count']}")
print(f"Last Failure: {auth_status['last_failure']}")
```

## Security Best Practices

### 1. API Key Security

- ✅ **Store in environment variables only**
- ✅ **Use minimum 32 character keys**
- ✅ **Rotate keys regularly (quarterly)**
- ✅ **Use unique keys per environment**
- ❌ **Never commit keys to version control**
- ❌ **Never log full API keys**

### 2. Network Security

- ✅ **Use TLS in production environments**
- ✅ **Verify SSL certificates**
- ✅ **Use secure network connections**
- ✅ **Implement network-level access controls**
- ❌ **Never disable SSL verification in production**

### 3. Error Handling

- ✅ **Log security events for monitoring**
- ✅ **Implement exponential backoff for retries**
- ✅ **Handle authentication failures gracefully**
- ✅ **Monitor for suspicious activity**
- ❌ **Never expose sensitive information in error messages**

### 4. Monitoring and Alerting

- ✅ **Monitor authentication failure rates**
- ✅ **Alert on repeated authentication failures**
- ✅ **Track API key usage patterns**
- ✅ **Monitor for unusual access patterns**

## Security Validation

### Configuration Validation

```python
from claude_pm.integrations.security import validate_security_configuration

# Validate security configuration
validation = validate_security_configuration(security_config)

if validation["valid"]:
    print("✅ Security configuration is valid")
else:
    print("❌ Security configuration errors:")
    for error in validation["errors"]:
        print(f"  - {error}")

if validation["warnings"]:
    print("⚠️ Security warnings:")
    for warning in validation["warnings"]:
        print(f"  - {warning}")

if validation["recommendations"]:
    print("💡 Security recommendations:")
    for rec in validation["recommendations"]:
        print(f"  - {rec}")
```

### Security Checklist

Use this checklist to ensure proper security configuration:

#### Development Environment
- [ ] API key configured (minimum 32 chars)
- [ ] Security event logging enabled
- [ ] Basic error handling implemented
- [ ] No hardcoded credentials

#### Staging Environment
- [ ] Production-like security configuration
- [ ] TLS enabled and tested
- [ ] SSL certificate verification enabled
- [ ] Authentication monitoring in place
- [ ] Security validation passes

#### Production Environment
- [ ] Strong API key (48+ characters)
- [ ] TLS/HTTPS enabled
- [ ] SSL certificate verification enabled
- [ ] Security event monitoring and alerting
- [ ] Regular API key rotation schedule
- [ ] Network access controls in place
- [ ] Security audit completed

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

```bash
# Check API key configuration
echo "API Key configured: ${MEM0AI_API_KEY:+YES}"

# Verify key length
python -c "import os; key=os.getenv('MEM0AI_API_KEY', ''); print(f'Key length: {len(key)}')"
```

#### 2. TLS/SSL Issues

```python
# Test TLS configuration
from claude_pm.integrations.security import SecurityConfig, Mem0AIAuthenticator

config = SecurityConfig(use_tls=True, verify_ssl=True)
auth = Mem0AIAuthenticator(config)
ssl_context = auth.create_ssl_context()

if ssl_context:
    print("✅ SSL context created successfully")
else:
    print("❌ Failed to create SSL context")
```

#### 3. Lockout Issues

```python
# Check if host is locked out
logger = integration.authenticator.security_logger
locked_out = logger.is_host_locked_out("localhost:8002")

if locked_out:
    print("❌ Host is locked out due to authentication failures")
    failures = logger.get_recent_failures("localhost:8002", 15)  # Last 15 minutes
    print(f"Recent failures: {failures}")
```

### Debug Logging

Enable debug logging for security components:

```python
import logging
logging.getLogger("claude_pm.integrations.security").setLevel(logging.DEBUG)
logging.getLogger("claude_pm.integrations.mem0ai_integration").setLevel(logging.DEBUG)
```

## Security Updates

### Version Compatibility

- **Claude PM Framework**: 3.0.0+
- **mem0AI Service**: Any version with authentication support
- **Python**: 3.8+
- **aiohttp**: 3.8+

### Security Patches

Check for security updates regularly:

```bash
# Update Claude PM Framework
pip install --upgrade claude-pm-framework

# Check for security advisories
pip-audit
```

## Support

For security-related issues:

1. **Non-sensitive issues**: Create GitHub issue
2. **Security vulnerabilities**: Email security contact
3. **Configuration help**: Check troubleshooting section
4. **Emergency**: Follow incident response procedures

## Compliance

This security implementation supports:

- **SOC 2 Type II** compliance requirements
- **ISO 27001** security standards
- **GDPR** data protection requirements
- **Industry standard** authentication practices

---

**Last Updated**: 2025-07-07  
**Security Review**: Required quarterly  
**Next Review**: 2025-10-07