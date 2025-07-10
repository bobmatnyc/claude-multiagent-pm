# Environment Variable Migration Guide

## Overview

The Claude PM Framework has migrated from `CLAUDE_PM_` environment variable prefix to `CLAUDE_MULTIAGENT_PM_` prefix for improved compatibility and naming consistency.

## Migration Status

✅ **COMPLETED** - Migration tools and validation systems are ready  
✅ **BACKWARD COMPATIBLE** - Legacy variables still work with deprecation warnings  
✅ **VALIDATED** - Both old and new variables tested and confirmed working  

## Quick Migration

To migrate your environment variables immediately:

```bash
# 1. Generate migration commands
python3 scripts/migrate_env_variables.py

# 2. Apply migration (choose option 1 for testing, option 2 for permanent)
scripts/setup_env_migration.sh

# 3. Validate migration worked
python3 scripts/validate_env_migration.py
```

## Migration Timeline

- **2025-07-10**: Migration tools created and validated
- **Current**: Legacy variables work with deprecation warnings
- **Recommended**: Migrate to new variables as soon as convenient
- **Future**: Legacy variable support may be removed in future major versions

## Environment Variables Migrated

| Legacy Variable | New Variable | Description |
|-----------------|--------------|-------------|
| `CLAUDE_PM_ROOT` | `CLAUDE_MULTIAGENT_PM_ROOT` | Framework root directory |
| `CLAUDE_PM_MANAGED` | `CLAUDE_MULTIAGENT_PM_MANAGED` | Managed projects directory |
| `CLAUDE_PM_MEMORY_ENABLED` | `CLAUDE_MULTIAGENT_PM_MEMORY_ENABLED` | Enable memory service integration |
| `CLAUDE_PM_MEMORY_SERVICE_URL` | `CLAUDE_MULTIAGENT_PM_MEMORY_SERVICE_URL` | Memory service URL |
| `CLAUDE_PM_MEMORY_SERVICE_TIMEOUT` | `CLAUDE_MULTIAGENT_PM_MEMORY_SERVICE_TIMEOUT` | Memory service timeout |
| `CLAUDE_PM_MEMORY_FALLBACK_MODE` | `CLAUDE_MULTIAGENT_PM_MEMORY_FALLBACK_MODE` | Memory service fallback mode |
| `CLAUDE_PM_MEMORY_NAMESPACE` | `CLAUDE_MULTIAGENT_PM_MEMORY_NAMESPACE` | Memory service namespace |
| `CLAUDE_PM_MEMORY_CACHE_TTL` | `CLAUDE_MULTIAGENT_PM_MEMORY_CACHE_TTL` | Memory cache TTL |
| `CLAUDE_PM_MEMORY_MAX_CACHE_SIZE` | `CLAUDE_MULTIAGENT_PM_MEMORY_MAX_CACHE_SIZE` | Memory cache max size |
| `CLAUDE_PM_MEMORY_BATCH_SIZE` | `CLAUDE_MULTIAGENT_PM_MEMORY_BATCH_SIZE` | Memory batch size |
| `CLAUDE_PM_PROJECT_CONTEXT_ENABLED` | `CLAUDE_MULTIAGENT_PM_PROJECT_CONTEXT_ENABLED` | Enable project context |
| `CLAUDE_PM_GLOBAL_PATTERNS_ENABLED` | `CLAUDE_MULTIAGENT_PM_GLOBAL_PATTERNS_ENABLED` | Enable global patterns |
| `CLAUDE_PM_CROSS_PROJECT_LEARNING` | `CLAUDE_MULTIAGENT_PM_CROSS_PROJECT_LEARNING` | Enable cross-project learning |
| `CLAUDE_PM_MANAGED_PROJECTS` | `CLAUDE_MULTIAGENT_PM_MANAGED_PROJECTS` | List of managed projects |
| `CLAUDE_PM_SPECIALIZED_MEMORY_PROJECTS` | `CLAUDE_MULTIAGENT_PM_SPECIALIZED_MEMORY_PROJECTS` | Projects with specialized memory |
| `CLAUDE_PM_MEMORY_INTEGRATED_PROJECTS` | `CLAUDE_MULTIAGENT_PM_MEMORY_INTEGRATED_PROJECTS` | Projects with memory integration |
| `CLAUDE_PM_MEMORY_STATUS` | `CLAUDE_MULTIAGENT_PM_MEMORY_STATUS` | Memory service status |
| `CLAUDE_PM_SESSION_MEMORY_ID` | `CLAUDE_MULTIAGENT_PM_SESSION_MEMORY_ID` | Session memory identifier |
| `CLAUDE_PM_CURRENT_PROJECT` | `CLAUDE_MULTIAGENT_PM_CURRENT_PROJECT` | Current active project |
| `CLAUDE_PM_PROJECT_MEMORY_ENABLED` | `CLAUDE_MULTIAGENT_PM_PROJECT_MEMORY_ENABLED` | Enable project memory |
| `CLAUDE_PM_FRAMEWORK_STATUS` | `CLAUDE_MULTIAGENT_PM_FRAMEWORK_STATUS` | Framework status |
| `CLAUDE_PM_MANAGED_STATUS` | `CLAUDE_MULTIAGENT_PM_MANAGED_STATUS` | Managed projects status |

## Migration Tools

### 1. Migration Script (`scripts/migrate_env_variables.py`)

Comprehensive migration tool that:
- Scans current environment for `CLAUDE_PM_` variables
- Generates migration commands for new variables  
- Scans shell configuration files for variables
- Creates backup files before modifications
- Validates migration feasibility

```bash
# Generate migration commands
python3 scripts/migrate_env_variables.py

# Dry run mode (no changes)
python3 scripts/migrate_env_variables.py --dry-run

# Generate report only
python3 scripts/migrate_env_variables.py --report-only

# Validate migration feasibility
python3 scripts/migrate_env_variables.py --validate-only
```

### 2. Setup Script (`scripts/setup_env_migration.sh`)

Interactive setup script that:
- Applies migration to current session (temporary)
- Adds migration to shell configuration files (permanent)
- Shows migration commands for review
- Creates backups of configuration files

```bash
# Run interactive setup
scripts/setup_env_migration.sh
```

### 3. Validation Script (`scripts/validate_env_migration.py`)

Comprehensive validation that:
- Tests framework with new variables (should have no warnings)
- Tests framework with legacy variables (should have warnings)
- Confirms migration eliminates deprecation warnings
- Generates validation report

```bash
# Validate migration works correctly
python3 scripts/validate_env_migration.py
```

## Migration Process

### Step-by-Step Migration

1. **Assessment**
   ```bash
   # Check current environment variables
   env | grep CLAUDE_PM_
   
   # Generate migration report
   python3 scripts/migrate_env_variables.py --report-only
   ```

2. **Testing**
   ```bash
   # Test migration feasibility
   python3 scripts/migrate_env_variables.py --validate-only
   
   # Run validation suite
   python3 scripts/validate_env_migration.py
   ```

3. **Temporary Migration** (for testing)
   ```bash
   # Apply to current session only
   scripts/setup_env_migration.sh
   # Choose option 1
   ```

4. **Permanent Migration**
   ```bash
   # Apply to shell configuration
   scripts/setup_env_migration.sh
   # Choose option 2
   
   # Restart terminal or source config
   source ~/.bashrc  # or ~/.zshrc
   ```

5. **Verification**
   ```bash
   # Verify new variables are set
   env | grep CLAUDE_MULTIAGENT_PM_
   
   # Test framework works without warnings
   python3 -c "from claude_pm.core.config import Config; Config()"
   ```

6. **Cleanup** (optional)
   ```bash
   # Remove legacy variables (after confirming everything works)
   # See env_migration_commands.sh for unset commands
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