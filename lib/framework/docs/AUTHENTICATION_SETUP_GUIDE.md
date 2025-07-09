# mem0AI Authentication Setup Guide

## Quick Start

This guide will help you set up secure API authentication for the Claude PM Framework's mem0AI integration in under 5 minutes.

## Prerequisites

- Claude PM Framework installed and configured
- mem0AI service running (locally or remote)
- Access to your shell/terminal

## Step 1: Generate an API Key 🔑

The Claude PM Framework includes a built-in tool to generate secure API keys:

```bash
# Generate a new secure API key
python -m claude_pm.scripts.security_cli generate-key
```

This will output something like:
```
==================================================
  API Key Generation
==================================================
✅ Generated secure API key:

API Key: Xy9mN2kL8pQ4vR7sT1uW6eY3rE5tU2iO9pA1sD4fG7hJ0kL3zX8cV5bN6mQ9wE2r

📋 Usage Instructions:
1. Copy the API key above
2. Add to your .env file:
   MEM0AI_API_KEY=Xy9mN2kL8pQ4vR7sT1uW6eY3rE5tU2iO9pA1sD4fG7hJ0kL3zX8cV5bN6mQ9wE2r
3. Restart your Claude PM services
4. Store the key securely (password manager recommended)
```

**⚠️ IMPORTANT**: Copy this API key immediately - it won't be shown again!

## Step 2: Configure Environment Variables 🔧

### For Development

Create or edit your `.env` file in the project root:

```bash
# Navigate to your Claude PM project directory
cd ~/Projects/claude-multiagent-pm

# Create/edit .env file
nano .env
```

Add the following configuration:

```bash
# mem0AI Authentication
MEM0AI_API_KEY=your_generated_api_key_here

# Service Configuration
MEM0AI_HOST=localhost
MEM0AI_PORT=8002
MEM0AI_TIMEOUT=30

# Security Settings (development)
MEM0AI_USE_TLS=false
MEM0AI_VERIFY_SSL=false
```

### For Production

Use the production environment template:

```bash
# Copy production template
cp deployment/environments/production.env .env

# Edit with your values
nano .env
```

Replace the placeholder values:

```bash
# mem0AI Authentication - REQUIRED
MEM0AI_API_KEY=your_production_api_key_here

# Service Configuration
MEM0AI_HOST=your-mem0ai-server.com
MEM0AI_PORT=443
MEM0AI_TIMEOUT=60

# Security Settings (production)
MEM0AI_USE_TLS=true
MEM0AI_VERIFY_SSL=true
```

## Step 3: Validate Configuration ✅

Test your authentication setup:

```bash
# Validate your configuration
python -m claude_pm.scripts.security_cli validate
```

This will check:
- ✅ API key format and length
- ✅ Security configuration
- ✅ Environment variables
- ✅ TLS settings

Example output:
```
==================================================
  Security Configuration Validation
==================================================
📋 Current Configuration:
  API Key: Configured
  API Key (masked): Xy9m...wE2r
  API Key length: 64 chars
  TLS Enabled: True
  SSL Verification: True

✅ Configuration is valid
```

## Step 4: Test Authentication 🧪

Test your connection to mem0AI:

```bash
# Test authentication
python -m claude_pm.scripts.security_cli test-auth
```

For custom settings:
```bash
# Test with specific host/port
python -m claude_pm.scripts.security_cli test-auth --host mem0ai.yourserver.com --port 443 --tls
```

Successful output:
```
==================================================
  Authentication Test
==================================================
📋 Test Configuration:
  Host: localhost
  Port: 8002
  TLS: False
  API Key: Configured

✅ Successfully connected to mem0AI service
✅ Authentication successful
✅ Successfully created test project space
```

## Step 5: Start Using mem0AI 🚀

Your authentication is now configured! You can start using mem0AI integration:

```python
from claude_pm.integrations.mem0ai_integration import create_mem0ai_integration

# Create integration (uses environment variables automatically)
integration = create_mem0ai_integration()

# Use with async context manager
async with integration:
    if integration.is_authenticated():
        print("🎉 Ready to use mem0AI!")
        
        # Create a project memory space
        await integration.create_project_space("my-project", "My awesome project")
        
        # Store some memories
        memory_id = await integration.store_memory(
            "my-project",
            "We decided to use FastAPI for the backend API",
            "project_decision",
            tags=["backend", "api", "framework"]
        )
```

## Troubleshooting Common Issues 🔍

### Issue: "No API key available for authentication"

**Solution:**
1. Check that `MEM0AI_API_KEY` is set in your environment
2. Restart your shell/IDE after setting the environment variable
3. Verify the key is not empty: `echo $MEM0AI_API_KEY`

### Issue: "API key must be at least 32 characters"

**Solution:**
1. Generate a new key using: `python -m claude_pm.scripts.security_cli generate-key`
2. Make sure you copied the full key (they're usually 64+ characters)

### Issue: "Authentication failed" (HTTP 401/403)

**Solution:**
1. Verify your API key is correct
2. Check that mem0AI service is configured to accept your key
3. Test with: `python -m claude_pm.scripts.security_cli test-auth`

### Issue: "Failed to connect to mem0AI service"

**Solution:**
1. Check that mem0AI service is running: `curl http://localhost:8002/health`
2. Verify host and port settings in your `.env` file
3. Check firewall/network connectivity

### Issue: "SSL certificate verification failed"

**Solution:**
1. For development: Set `MEM0AI_VERIFY_SSL=false`
2. For production: Ensure valid SSL certificates are installed
3. Check TLS configuration: `MEM0AI_USE_TLS=true`

## Advanced Configuration ⚙️

### Using Custom Security Settings

```python
from claude_pm.integrations.security import SecurityConfig
from claude_pm.integrations.mem0ai_integration import Mem0AIIntegration, Mem0AIConfig

# Create custom security configuration
security_config = SecurityConfig(
    api_key="your_api_key_here",
    use_tls=True,
    verify_ssl=True,
    max_auth_failures=10,
    auth_failure_lockout_minutes=30
)

# Create integration with custom config
config = Mem0AIConfig(
    host="custom-host.com",
    port=8443,
    timeout=60,
    security_config=security_config
)

integration = Mem0AIIntegration(config)
```

### Request Signing (Optional)

For enhanced security, enable request signing:

```python
security_config = SecurityConfig(
    api_key="your_api_key_here",
    require_request_signing=True
)
```

### Monitoring Authentication Events

```python
# Access security event logger
logger = integration.authenticator.security_logger

# View recent authentication events
for event in logger.events[-5:]:  # Last 5 events
    print(f"{event.timestamp}: {event.event_type} - {event.service_host}")

# Check for authentication failures
failures = logger.get_recent_failures("localhost:8002", minutes=60)
print(f"Authentication failures in last hour: {failures}")

# Check if host is locked out
locked_out = logger.is_host_locked_out("localhost:8002")
if locked_out:
    print("⚠️ Host is currently locked out due to authentication failures")
```

## Security Best Practices 🛡️

### Development Environment
- ✅ Use unique API keys for development
- ✅ Never commit API keys to version control
- ✅ Use `.env` files and add them to `.gitignore`
- ✅ Enable authentication even in development

### Production Environment
- ✅ Use strong, unique API keys (64+ characters)
- ✅ Enable TLS encryption (`MEM0AI_USE_TLS=true`)
- ✅ Enable SSL certificate verification (`MEM0AI_VERIFY_SSL=true`)
- ✅ Monitor authentication logs and failures
- ✅ Rotate API keys regularly (quarterly)
- ✅ Use environment variables or secure secret management
- ✅ Run production validation: `python scripts/validate_production_env.py`

### Key Management
- ✅ Generate keys using cryptographically secure methods
- ✅ Store keys in password managers or secure vaults
- ✅ Use separate keys for each environment
- ✅ Rotate keys on a regular schedule
- ✅ Monitor key usage and access patterns

## Getting Help 📞

### Check Configuration Status
```bash
python -m claude_pm.scripts.security_cli status
```

### View Security Recommendations
```bash
python -m claude_pm.scripts.security_cli recommendations
```

### Enable Debug Logging
```python
import logging
logging.getLogger("claude_pm.integrations.security").setLevel(logging.DEBUG)
logging.getLogger("claude_pm.integrations.mem0ai_integration").setLevel(logging.DEBUG)
```

### Resources
- 📖 [Security Guide](MEM0AI_SECURITY_GUIDE.md) - Comprehensive security documentation
- 🧪 [Test Suite](../tests/test_mem0ai_authentication.py) - Authentication test examples
- 🔧 [CLI Tools](../claude_pm/scripts/security_cli.py) - Security management commands
- 📋 [Environment Templates](../deployment/environments/) - Configuration templates

## Need More Help?

1. **Configuration Issues**: Run `python -m claude_pm.scripts.security_cli validate`
2. **Connection Issues**: Run `python -m claude_pm.scripts.security_cli test-auth`
3. **Security Questions**: See [MEM0AI_SECURITY_GUIDE.md](MEM0AI_SECURITY_GUIDE.md)
4. **Bug Reports**: Create an issue in the project repository

---

**🎉 Congratulations!** You've successfully set up secure API authentication for mem0AI integration. Your Claude PM Framework is now ready for secure memory management and context preservation.

*Last Updated: 2025-07-07*