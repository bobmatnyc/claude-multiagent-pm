# Subsystem Versioning Workflow Guide

## CLI Commands for Version Management

The Claude PM Framework provides comprehensive CLI utilities for managing subsystem versions across the development lifecycle.

### Core Version Commands

#### 1. Version Scanning and Display

```bash
# Scan all subsystem versions
python -m claude_pm.cli versions

# Detailed version report with status
python -m claude_pm.cli versions --detailed

# Export version information
python -m claude_pm.cli versions --export versions.json
python -m claude_pm.cli versions --export versions.yaml
```

#### 2. Individual Version Management

```bash
# Update specific subsystem version
python -m claude_pm.cli set-version memory 003

# Update with automatic backup
python -m claude_pm.cli set-version memory 003 --backup

# Bulk version updates
python -m claude_pm.cli set-version memory=003 agents=002 cli=002
```

#### 3. Version Validation

```bash
# Validate all versions against framework requirements
python -m claude_pm.cli validate-versions

# Validate specific requirements
python -m claude_pm.cli validate-versions --requirements requirements.json

# Detailed validation with fix suggestions
python -m claude_pm.cli validate-versions --detailed --fix-suggestions
```

### Using the Validation Script

The framework includes a dedicated validation script for comprehensive checks:

```bash
# Basic validation
python scripts/validate_subsystem_versions.py

# Detailed validation with full report
python scripts/validate_subsystem_versions.py --detailed

# Export validation results
python scripts/validate_subsystem_versions.py --export validation-report.json
```

## Developer Workflow Integration

### 1. Pre-Development Setup

Before starting development work, validate current version state:

```bash
# Check current version status
python -m claude_pm.cli versions --detailed

# Validate compatibility
python -m claude_pm.cli validate-versions

# Review health status including versions
npm run monitor:status
```

### 2. Development Phase

During development, track changes that may require version updates:

```bash
# Track memory system changes
git log --oneline scripts/memory-*.js
git log --oneline claude_pm/services/claude_pm_memory.py

# Monitor for breaking changes
git diff HEAD~1 -- claude_pm/utils/subsystem_versions.py
```

### 3. Version Update Decision Matrix

| Change Type | Version Update Required | Example |
|-------------|-------------------------|---------|
| Bug Fix | No | Fixed typo in logging message |
| Feature Enhancement | Yes | Added new memory optimization algorithm |
| API Change | Yes | Modified subsystem manager interface |
| Configuration Change | Maybe | Updated default memory thresholds |
| Breaking Change | Yes | Changed version file format |

### 4. Version Update Process

```bash
# Step 1: Determine current version
python -m claude_pm.cli versions | grep memory

# Step 2: Increment version (with backup)
python -m claude_pm.cli set-version memory 003 --backup

# Step 3: Validate compatibility
python -m claude_pm.cli validate-versions

# Step 4: Test functionality
npm run memory:monitor
npm run memory:optimize

# Step 5: Update documentation
# Edit docs/architecture/subsystem-versioning.md
```

### 5. Git Integration

```bash
# Commit version updates with clear message
git add MEMORY_VERSION
git commit -m "version: Increment MEMORY_VERSION to 003 for enhanced subprocess isolation

- Added advanced memory pooling
- Improved subprocess lifecycle management
- Enhanced leak detection algorithms"

# Tag framework versions
git tag -a framework-010-memory-003 -m "Framework 010 with Memory subsystem v003"
```

## Advanced Workflows

### Bulk Version Management

For coordinated subsystem updates:

```bash
# Create version update plan
cat > version-updates.json << EOF
{
    "memory": "003",
    "agents": "002", 
    "cli": "002",
    "integration": "002"
}
EOF

# Apply bulk updates
python -c "
import json
import asyncio
from claude_pm.utils.subsystem_versions import SubsystemVersionManager

async def bulk_update():
    with open('version-updates.json') as f:
        updates = json.load(f)
    
    manager = SubsystemVersionManager()
    results = await manager.bulk_update(updates, backup=True)
    
    for subsystem, success in results.items():
        status = '✅' if success else '❌'
        print(f'{status} {subsystem}: {updates[subsystem]}')

asyncio.run(bulk_update())
"
```

### Version Rollback

If issues are discovered after version update:

```bash
# Check backup files
ls -la MEMORY_VERSION.backup.*

# Restore from backup
cp MEMORY_VERSION.backup.20250714_143025 MEMORY_VERSION

# Validate rollback
python -m claude_pm.cli validate-versions

# Verify functionality
npm run memory:health
```

### Automated Version Checking

Set up pre-commit hooks for version validation:

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "🔢 Validating subsystem versions..."
python -m claude_pm.cli validate-versions --quiet

if [ $? -ne 0 ]; then
    echo "❌ Version validation failed. Please resolve version conflicts."
    exit 1
fi

echo "✅ Version validation passed"
```

### CI/CD Integration

```yaml
# .github/workflows/version-validation.yml
name: Subsystem Version Validation

on: [push, pull_request]

jobs:
  validate-versions:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e .
    
    - name: Validate subsystem versions
      run: |
        python -m claude_pm.cli validate-versions --detailed
    
    - name: Export version report
      run: |
        python -m claude_pm.cli versions --export version-report.json
    
    - name: Upload version report
      uses: actions/upload-artifact@v3
      with:
        name: version-report
        path: version-report.json
```

## Memory System Specific Workflows

### Memory Subsystem Version 002 Workflow

The enhanced memory system (v002) requires special handling:

```bash
# Monitor memory optimization effectiveness
npm run memory:monitor &
MONITOR_PID=$!

# Run memory-intensive operations
npm run memory:test

# Check memory reports
npm run memory:report

# Stop monitoring
kill $MONITOR_PID

# Validate memory system health
npm run memory:health
```

### Memory Script Integration Testing

```bash
# Test subprocess manager integration
node scripts/memory-optimization.js monitor &
node scripts/memory-monitor.js &

# Verify subprocess coordination
ps aux | grep "memory-"

# Check memory utilization patterns
cat logs/memory-usage-history.json | jq '.[] | {timestamp, heapUsed, subprocessCount}'
```

## Troubleshooting Workflows

### Version Conflict Resolution

```bash
# Identify conflicts
python -m claude_pm.cli validate-versions --detailed

# Check specific subsystem
python -c "
from claude_pm.utils.subsystem_versions import SubsystemVersionManager
import asyncio

async def check_memory():
    manager = SubsystemVersionManager()
    await manager.scan_subsystem_versions()
    
    memory_info = manager.subsystem_info.get('memory')
    if memory_info:
        print(f'Memory version: {memory_info.version}')
        print(f'Status: {memory_info.status.value}')
        print(f'File: {memory_info.file_path}')
        if memory_info.error:
            print(f'Error: {memory_info.error}')

asyncio.run(check_memory())
"
```

### Version File Corruption Recovery

```bash
# Check for corruption
file MEMORY_VERSION
cat MEMORY_VERSION | hexdump -C

# Restore from backup
if [ -f MEMORY_VERSION.backup.* ]; then
    cp $(ls -t MEMORY_VERSION.backup.* | head -1) MEMORY_VERSION
    echo "Restored from backup"
else
    echo "002" > MEMORY_VERSION
    echo "Recreated with default version"
fi

# Validate recovery
python -m claude_pm.cli validate-versions
```

### Performance Validation

```bash
# Test version detection performance
time python -m claude_pm.cli versions

# Monitor memory during version operations
npm run memory:monitor &
python -m claude_pm.cli validate-versions --detailed
```

## Best Practices Summary

### Version Update Guidelines

1. **Always Backup**: Use `--backup` flag for version updates
2. **Test Thoroughly**: Validate functionality after version changes
3. **Document Changes**: Update architecture documentation
4. **Coordinate Updates**: Plan bulk updates for related subsystems
5. **Monitor Performance**: Check system health after version changes

### Development Integration

1. **Pre-commit Validation**: Ensure versions are compatible before commits
2. **Feature Branch Versioning**: Update versions in feature branches
3. **Release Coordination**: Synchronize version updates with releases
4. **Rollback Planning**: Maintain backup strategies for quick recovery
5. **CI/CD Integration**: Automate version validation in pipelines

### Memory System Considerations

1. **Resource Monitoring**: Track memory usage during version operations
2. **Subprocess Coordination**: Ensure memory scripts work with new versions
3. **Performance Validation**: Verify <15 second health monitoring
4. **Integration Testing**: Test memory optimization with framework changes
5. **Leak Detection**: Monitor for memory leaks after version updates

This workflow guide ensures consistent, reliable subsystem version management across the Claude PM Framework development lifecycle.