# Environment Variable Migration Guide

## Overview

The Claude Multi-Agent PM Framework has migrated from `CLAUDE_PM_` to `CLAUDE_MULTIAGENT_PM_` environment variable prefix to better reflect the project's expanded scope and modernize the configuration system.

## Migration Timeline

- **Current Version**: Full backward compatibility with legacy `CLAUDE_PM_` variables
- **v4.0**: Legacy `CLAUDE_PM_` variables will be deprecated and removed
- **Recommended Action**: Migrate to new `CLAUDE_MULTIAGENT_PM_` prefix immediately

## Variable Mapping

### Core Framework Variables

| Legacy Variable | New Variable | Description |
|---|---|---|
| `CLAUDE_PM_ROOT` | `CLAUDE_MULTIAGENT_PM_ROOT` | Framework root directory |
| `CLAUDE_PM_LOG_LEVEL` | `CLAUDE_MULTIAGENT_PM_LOG_LEVEL` | Logging level |
| `CLAUDE_PM_DEBUG` | `CLAUDE_MULTIAGENT_PM_DEBUG` | Debug mode |
| `CLAUDE_PM_VERBOSE` | `CLAUDE_MULTIAGENT_PM_VERBOSE` | Verbose logging |

### Service Configuration

| Legacy Variable | New Variable | Description |
|---|---|---|
| `CLAUDE_PM_ENABLE_HEALTH_MONITORING` | `CLAUDE_MULTIAGENT_PM_ENABLE_HEALTH_MONITORING` | Health monitoring |
| `CLAUDE_PM_HEALTH_CHECK_INTERVAL` | `CLAUDE_MULTIAGENT_PM_HEALTH_CHECK_INTERVAL` | Health check interval |
| `CLAUDE_PM_ENABLE_METRICS` | `CLAUDE_MULTIAGENT_PM_ENABLE_METRICS` | Metrics collection |
| `CLAUDE_PM_METRICS_INTERVAL` | `CLAUDE_MULTIAGENT_PM_METRICS_INTERVAL` | Metrics interval |
| `CLAUDE_PM_GRACEFUL_SHUTDOWN_TIMEOUT` | `CLAUDE_MULTIAGENT_PM_GRACEFUL_SHUTDOWN_TIMEOUT` | Shutdown timeout |
| `CLAUDE_PM_STARTUP_TIMEOUT` | `CLAUDE_MULTIAGENT_PM_STARTUP_TIMEOUT` | Startup timeout |

### Memory Integration

| Legacy Variable | New Variable | Description |
|---|---|---|
| `CLAUDE_PM_MEMORY_HOST` | `CLAUDE_MULTIAGENT_PM_MEMORY_HOST` | Memory service host |
| `CLAUDE_PM_MEMORY_PORT` | `CLAUDE_MULTIAGENT_PM_MEMORY_PORT` | Memory service port |
| `CLAUDE_PM_MEMORY_TIMEOUT` | `CLAUDE_MULTIAGENT_PM_MEMORY_TIMEOUT` | Memory service timeout |
| `CLAUDE_PM_MEMORY_API_KEY` | `CLAUDE_MULTIAGENT_PM_MEMORY_API_KEY` | Memory service API key |

### Alerting & Monitoring

| Legacy Variable | New Variable | Description |
|---|---|---|
| `CLAUDE_PM_ENABLE_ALERTING` | `CLAUDE_MULTIAGENT_PM_ENABLE_ALERTING` | Enable alerting |
| `CLAUDE_PM_ALERT_THRESHOLD` | `CLAUDE_MULTIAGENT_PM_ALERT_THRESHOLD` | Alert threshold |
| `CLAUDE_PM_EMAIL_ALERTS` | `CLAUDE_MULTIAGENT_PM_EMAIL_ALERTS` | Email alerts |
| `CLAUDE_PM_SLACK_ALERTS` | `CLAUDE_MULTIAGENT_PM_SLACK_ALERTS` | Slack alerts |

### Feature Flags

| Legacy Variable | New Variable | Description |
|---|---|---|
| `CLAUDE_PM_EXPERIMENTAL_FEATURES` | `CLAUDE_MULTIAGENT_PM_EXPERIMENTAL_FEATURES` | Experimental features |
| `CLAUDE_PM_LANGGRAPH_ENABLED` | `CLAUDE_MULTIAGENT_PM_LANGGRAPH_ENABLED` | LangGraph support |
| `CLAUDE_PM_MULTI_AGENT_PARALLEL` | `CLAUDE_MULTIAGENT_PM_MULTI_AGENT_PARALLEL` | Parallel agents |

### Performance Tuning

| Legacy Variable | New Variable | Description |
|---|---|---|
| `CLAUDE_PM_MAX_WORKERS` | `CLAUDE_MULTIAGENT_PM_MAX_WORKERS` | Maximum workers |
| `CLAUDE_PM_MEMORY_LIMIT` | `CLAUDE_MULTIAGENT_PM_MEMORY_LIMIT` | Memory limit |
| `CLAUDE_PM_TASK_TIMEOUT` | `CLAUDE_MULTIAGENT_PM_TASK_TIMEOUT` | Task timeout |

### Security

| Legacy Variable | New Variable | Description |
|---|---|---|
| `CLAUDE_PM_SECURITY_MODE` | `CLAUDE_MULTIAGENT_PM_SECURITY_MODE` | Security mode |
| `CLAUDE_PM_CORS_ENABLED` | `CLAUDE_MULTIAGENT_PM_CORS_ENABLED` | CORS enabled |
| `CLAUDE_PM_SESSION_SECRET` | `CLAUDE_MULTIAGENT_PM_SESSION_SECRET` | Session secret |

## Migration Steps

### Step 1: Update Environment Files

1. **Development Environment**
   ```bash
   # Update .env or development.env
   cp deployment/environments/development.env .env
   ```

2. **Production Environment**
   ```bash
   # Update production.env
   # Edit deployment/environments/production.env
   ```

3. **Staging Environment**
   ```bash
   # Update staging.env
   # Edit deployment/environments/staging.env
   ```

### Step 2: Update Docker Configuration

For Docker deployments:
```bash
# Update docker.env
# Edit deployment/environments/docker.env
```

### Step 3: Update Scripts and Automation

Update any deployment scripts, CI/CD pipelines, or automation that sets environment variables:

```bash
# Old way
export CLAUDE_PM_LOG_LEVEL=DEBUG
export CLAUDE_PM_DEBUG=true

# New way
export CLAUDE_MULTIAGENT_PM_LOG_LEVEL=DEBUG
export CLAUDE_MULTIAGENT_PM_DEBUG=true
```

### Step 4: Test Migration

1. **Validate Configuration**
   ```bash
   # Check configuration is loaded correctly
   claude-pm config validate
   ```

2. **Run Health Check**
   ```bash
   # Verify services start correctly
   claude-pm health check
   ```

3. **Test Memory Integration**
   ```bash
   # Test memory service connectivity
   claude-pm memory test
   ```

## Backward Compatibility

The framework maintains full backward compatibility:

- **Legacy variables are automatically detected** and used if new variables aren't set
- **Warning messages** are logged when legacy variables are used
- **Gradual migration** is supported - you can migrate variables incrementally

### Example of Backward Compatibility

```python
# Configuration system automatically handles both
# Priority: New variable > Legacy variable > Default value

# This works:
CLAUDE_PM_LOG_LEVEL=DEBUG  # Legacy

# This works better:
CLAUDE_MULTIAGENT_PM_LOG_LEVEL=DEBUG  # New

# This works best:
CLAUDE_MULTIAGENT_PM_LOG_LEVEL=DEBUG  # New
# CLAUDE_PM_LOG_LEVEL=INFO  # Legacy (ignored)
```

## Validation

### Check Current Configuration

```bash
# View current environment variables
claude-pm config show

# Check for legacy variables
claude-pm config audit
```

### Validate Migration

```bash
# Test with new variables
claude-pm config test

# Verify all services work
claude-pm health check --comprehensive
```

## Environment-Specific Examples

### Development

```bash
# development.env
CLAUDE_MULTIAGENT_PM_ROOT=/Users/username/Projects/claude-multiagent-pm
CLAUDE_MULTIAGENT_PM_LOG_LEVEL=DEBUG
CLAUDE_MULTIAGENT_PM_DEBUG=true
CLAUDE_MULTIAGENT_PM_VERBOSE=true
```

### Production

```bash
# production.env
CLAUDE_MULTIAGENT_PM_ROOT=/opt/claude-multiagent-pm
CLAUDE_MULTIAGENT_PM_LOG_LEVEL=INFO
CLAUDE_MULTIAGENT_PM_DEBUG=false
CLAUDE_MULTIAGENT_PM_ENABLE_ALERTING=true
```

### Docker

```bash
# docker.env
CLAUDE_MULTIAGENT_PM_ROOT=/app/claude-multiagent-pm
CLAUDE_MULTIAGENT_PM_LOG_LEVEL=INFO
CLAUDE_MULTIAGENT_PM_CONTAINER_METRICS=true
```

## Troubleshooting

### Common Issues

1. **Mixed Variable Usage**
   - Problem: Using both old and new variables
   - Solution: Use only new variables, remove old ones

2. **Path Issues**
   - Problem: `CLAUDE_PM_ROOT` vs `CLAUDE_MULTIAGENT_PM_ROOT`
   - Solution: Update all path references

3. **Memory Service Connection**
   - Problem: Memory variables not updated
   - Solution: Update all `CLAUDE_PM_MEMORY_*` variables

### Debug Commands

```bash
# Show all environment variables
claude-pm debug env

# Show configuration source
claude-pm config source

# Test configuration
claude-pm config validate --strict
```

## Best Practices

1. **Complete Migration**: Update all variables at once per environment
2. **Validate Changes**: Test thoroughly before deployment
3. **Document Changes**: Update team documentation and runbooks
4. **CI/CD Updates**: Update all automation scripts
5. **Monitor Warnings**: Watch for legacy variable warnings in logs

## Support

For migration assistance:
- Review this documentation
- Check the example environment files in `deployment/environments/`
- Test with `claude-pm config validate`
- Monitor logs for migration warnings

## Timeline

- **Now**: Start migration to new variables
- **v3.x**: Legacy variables supported with warnings
- **v4.0**: Legacy variables removed completely

Start your migration today to ensure smooth transition!