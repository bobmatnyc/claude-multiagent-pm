# Subsystem Version Compatibility Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for subsystem version compatibility issues in the Claude PM Framework. It covers common problems, diagnostic procedures, and resolution strategies for maintaining version harmony across all framework components.

## Common Version Compatibility Issues

### 1. Version File Missing or Corrupted

**Symptoms:**
- `VersionStatus.MISSING` errors in validation
- Health check failures related to version detection
- CLI commands failing with version read errors

**Diagnostic Commands:**
```bash
# Check which version files exist
ls -la *_VERSION

# Validate file contents
for file in *_VERSION; do
    echo "=== $file ==="
    cat "$file" | hexdump -C
    file "$file"
done

# Test version detection
python -m claude_pm.cli versions --detailed
```

**Resolution Steps:**
```bash
# 1. Identify missing version file
python -c "
from claude_pm.utils.subsystem_versions import SubsystemVersionManager
import asyncio

async def check_missing():
    manager = SubsystemVersionManager()
    await manager.scan_subsystem_versions()
    
    for name, info in manager.subsystem_info.items():
        if info.status.value == 'missing':
            print(f'❌ Missing: {name} -> {info.file_path}')
        elif info.status.value == 'error':
            print(f'🔥 Error: {name} -> {info.error}')

asyncio.run(check_missing())
"

# 2. Restore from backup if available
if [ -f MEMORY_VERSION.backup.* ]; then
    cp $(ls -t MEMORY_VERSION.backup.* | head -1) MEMORY_VERSION
    echo "Restored MEMORY_VERSION from backup"
fi

# 3. Recreate missing version files with defaults
echo "001" > AGENTS_VERSION
echo "001" > TICKETING_VERSION
echo "001" > DOCUMENTATION_VERSION
echo "001" > SERVICES_VERSION
echo "001" > CLI_VERSION
echo "001" > INTEGRATION_VERSION
echo "001" > HEALTH_VERSION
echo "002" > MEMORY_VERSION
echo "010" > FRAMEWORK_VERSION

# 4. Validate restoration
python -m claude_pm.cli validate-versions
```

### 2. Version Incompatibility Errors

**Symptoms:**
- Framework requiring newer subsystem versions than available
- Health monitoring reporting compatibility failures
- Memory system not functioning with expected features

**Diagnostic Commands:**
```bash
# Check compatibility requirements
python -c "
import asyncio
from claude_pm.utils.subsystem_versions import SubsystemVersionManager

async def check_compatibility():
    manager = SubsystemVersionManager()
    
    # Framework 010 requirements
    requirements = {
        'memory': '002',
        'agents': '001',
        'ticketing': '001',
        'documentation': '001',
        'services': '001',
        'cli': '001',
        'integration': '001',
        'health': '001'
    }
    
    checks = await manager.validate_compatibility(requirements)
    
    for check in checks:
        status = '✅' if check.compatible else '❌'
        print(f'{status} {check.subsystem}: {check.current_version} vs {check.required_version} - {check.message}')

asyncio.run(check_compatibility())
"

# Detailed version validation
python scripts/validate_subsystem_versions.py --detailed
```

**Resolution Steps:**
```bash
# 1. Identify incompatible subsystems
python -m claude_pm.cli validate-versions --detailed | grep -E "(❌|incompatible)"

# 2. Update incompatible versions
python -m claude_pm.cli set-version memory 002 --backup
python -m claude_pm.cli set-version agents 001 --backup

# 3. Bulk update if needed
python -c "
import asyncio
from claude_pm.utils.subsystem_versions import SubsystemVersionManager

async def bulk_fix():
    manager = SubsystemVersionManager()
    
    updates = {
        'memory': '002',
        'agents': '001',
        'ticketing': '001',
        'documentation': '001',
        'services': '001',
        'cli': '001',
        'integration': '001',
        'health': '001'
    }
    
    results = await manager.bulk_update(updates, backup=True)
    
    for subsystem, success in results.items():
        status = '✅' if success else '❌'
        print(f'{status} Updated {subsystem} to {updates[subsystem]}')

asyncio.run(bulk_fix())
"

# 4. Verify fixes
python -m claude_pm.cli validate-versions
npm run monitor:health
```

### 3. Memory System Version Conflicts

**Symptoms:**
- Memory optimization scripts failing
- Subprocess coordination errors
- Memory monitoring not working as expected

**Diagnostic Commands:**
```bash
# Check memory system version
cat MEMORY_VERSION

# Test memory system functionality
npm run memory:health
npm run memory:monitor &
MONITOR_PID=$!
sleep 10
kill $MONITOR_PID

# Check memory script compatibility
node -e "
try {
    const memoryOptimizer = require('./scripts/memory-optimization.js');
    console.log('✅ Memory optimization script loaded successfully');
} catch (error) {
    console.log('❌ Memory optimization script error:', error.message);
}

try {
    const memoryMonitor = require('./scripts/memory-monitor.js');
    console.log('✅ Memory monitor script loaded successfully');
} catch (error) {
    console.log('❌ Memory monitor script error:', error.message);
}
"
```

**Resolution Steps:**
```bash
# 1. Verify memory version requirements
python -c "
from claude_pm.utils.subsystem_versions import SubsystemVersionManager
import asyncio

async def check_memory():
    manager = SubsystemVersionManager()
    await manager.scan_subsystem_versions()
    
    memory_info = manager.subsystem_info.get('memory')
    if memory_info:
        print(f'Current MEMORY_VERSION: {memory_info.version}')
        print(f'Required for Framework 010: 002')
        
        if memory_info.version == '002':
            print('✅ Memory version is compatible')
        else:
            print('❌ Memory version needs update')

asyncio.run(check_memory())
"

# 2. Update memory version if needed
if [ "$(cat MEMORY_VERSION)" != "002" ]; then
    cp MEMORY_VERSION MEMORY_VERSION.backup.$(date +%Y%m%d_%H%M%S)
    echo "002" > MEMORY_VERSION
    echo "Updated MEMORY_VERSION to 002"
fi

# 3. Test memory system features
npm run memory:optimize
npm run memory:leak-detect

# 4. Validate subprocess integration
npm run memory:monitor &
MONITOR_PID=$!
ps aux | grep memory
kill $MONITOR_PID
```

## Advanced Troubleshooting Scenarios

### 4. Framework Version Mismatch

**Symptoms:**
- Framework components reporting different versions
- Health checks showing framework version inconsistencies
- CLI commands behaving unexpectedly

**Diagnostic Commands:**
```bash
# Check all version sources
echo "=== Version File ==="
cat FRAMEWORK_VERSION

echo "=== Package.json ==="
cat package.json | jq '.version'

echo "=== Python Package ==="
python -c "import claude_pm; print(claude_pm.__version__)" 2>/dev/null || echo "Not available"

echo "=== VERSION File ==="
cat VERSION

# Check for version inconsistencies
python -c "
import json
from pathlib import Path

# Load package.json
with open('package.json') as f:
    pkg = json.load(f)

print(f'NPM Package Version: {pkg[\"version\"]}')

# Check VERSION file
if Path('VERSION').exists():
    version_content = Path('VERSION').read_text().strip()
    print(f'VERSION file: {version_content}')

# Check FRAMEWORK_VERSION
if Path('FRAMEWORK_VERSION').exists():
    framework_content = Path('FRAMEWORK_VERSION').read_text().strip()
    print(f'FRAMEWORK_VERSION: {framework_content}')

print('\\n=== Recommendations ===')
print('NPM version should be semantic (e.g., 0.6.2)')
print('FRAMEWORK_VERSION should be serial (e.g., 010)')
print('VERSION file should match NPM version')
"
```

**Resolution Steps:**
```bash
# 1. Standardize framework version
echo "010" > FRAMEWORK_VERSION

# 2. Ensure VERSION file matches package.json
PACKAGE_VERSION=$(cat package.json | jq -r '.version')
echo "$PACKAGE_VERSION" > VERSION

# 3. Validate version consistency
python scripts/validate_subsystem_versions.py

# 4. Test framework functionality
python -m claude_pm.cli --version
npm run test
```

### 5. Serialization and Version Increment Issues

**Symptoms:**
- Version increment commands failing
- Incorrect version comparison results
- Version history showing gaps or inconsistencies

**Diagnostic Commands:**
```bash
# Test version comparison logic
python -c "
from claude_pm.utils.subsystem_versions import SubsystemVersionManager

manager = SubsystemVersionManager()

# Test serial number comparison
test_cases = [
    ('001', '002'),
    ('002', '001'), 
    ('010', '009'),
    ('001', '001')
]

for v1, v2 in test_cases:
    result = manager.compare_versions(v1, v2)
    comparison = 'greater' if result > 0 else 'less' if result < 0 else 'equal'
    print(f'{v1} is {comparison} than {v2}')
"

# Test version increment
python -c "
from claude_pm.utils.subsystem_versions import increment_version

test_versions = ['001', '002', '009', '010', '099']

for version in test_versions:
    incremented = increment_version(version, 'serial')
    print(f'{version} -> {incremented}')
"
```

**Resolution Steps:**
```bash
# 1. Fix version format if needed
for file in *_VERSION; do
    current=$(cat "$file")
    if [[ ${#current} -lt 3 ]]; then
        printf "%03d\n" "$current" > "$file"
        echo "Fixed format for $file: $current -> $(cat "$file")"
    fi
done

# 2. Validate increment logic
python -c "
from claude_pm.utils.subsystem_versions import increment_version

# Test edge cases
edge_cases = ['001', '009', '099', '999']

for version in edge_cases:
    try:
        next_version = increment_version(version, 'serial')
        print(f'✅ {version} -> {next_version}')
    except Exception as e:
        print(f'❌ {version} -> Error: {e}')
"

# 3. Manual increment if automated fails
CURRENT_MEMORY=$(cat MEMORY_VERSION)
NEXT_MEMORY=$(printf "%03d" $((10#$CURRENT_MEMORY + 1)))
echo "$NEXT_MEMORY" > MEMORY_VERSION
echo "Manually incremented MEMORY_VERSION: $CURRENT_MEMORY -> $NEXT_MEMORY"
```

## Performance-Related Version Issues

### 6. Health Monitoring Performance Degradation

**Symptoms:**
- Health checks taking longer than 15 seconds
- Memory monitoring consuming excessive resources
- Version validation causing timeouts

**Diagnostic Commands:**
```bash
# Time health monitoring operations
echo "=== Health Check Performance ==="
time npm run monitor:once

echo "=== Version Validation Performance ==="
time python -m claude_pm.cli validate-versions

echo "=== Memory Monitoring Performance ==="
time npm run memory:health

# Monitor resource usage during health checks
npm run monitor:once &
HEALTH_PID=$!
sleep 2
ps -p $HEALTH_PID -o pid,pcpu,pmem,comm
wait $HEALTH_PID
```

**Resolution Steps:**
```bash
# 1. Optimize version detection
python -c "
import time
import asyncio
from claude_pm.utils.subsystem_versions import SubsystemVersionManager

async def optimize_test():
    start = time.time()
    
    manager = SubsystemVersionManager()
    await manager.scan_subsystem_versions()
    
    scan_time = time.time() - start
    print(f'Version scan time: {scan_time:.2f}s')
    
    if scan_time > 2.0:
        print('⚠️  Version scanning is slow - consider optimization')
    else:
        print('✅ Version scanning performance is good')

asyncio.run(optimize_test())
"

# 2. Check memory system efficiency
npm run memory:monitor &
MONITOR_PID=$!
sleep 5
kill $MONITOR_PID

echo "Memory monitoring test completed"

# 3. Verify Framework 010 + Memory v002 optimizations
python -c "
from pathlib import Path

framework_version = Path('FRAMEWORK_VERSION').read_text().strip()
memory_version = Path('MEMORY_VERSION').read_text().strip()

print(f'Framework: {framework_version}, Memory: {memory_version}')

if framework_version == '010' and memory_version == '002':
    print('✅ Optimal version combination for performance')
    print('Expected: <15s health checks (77% improvement)')
else:
    print('⚠️  Suboptimal version combination')
    print('Recommended: Framework 010 + Memory 002')
"
```

## Compatibility Requirements Reference

### Framework Version Compatibility Matrix

| Framework | Memory | Agents | CLI | Integration | Health | Notes |
|-----------|--------|--------|-----|-------------|--------|-------|
| 010       | 002+   | 001+   | 001+ | 001+       | 001+   | Current stable |
| 011       | 003+   | 002+   | 002+ | 001+       | 001+   | Future release |
| 012       | 003+   | 002+   | 002+ | 002+       | 002+   | Future release |

### Memory Subsystem Requirements

| Memory Version | Features | Framework Compatibility | Performance |
|----------------|----------|------------------------|-------------|
| 001            | Basic memory management | 009+ | Baseline |
| 002            | Subprocess isolation, predictive alerts | 010+ | 77% improvement |
| 003            | Advanced pooling (planned) | 011+ | TBD |

### Validation Commands Reference

```bash
# Quick compatibility check
python -m claude_pm.cli validate-versions

# Detailed compatibility analysis
python scripts/validate_subsystem_versions.py --detailed

# Export compatibility report
python -m claude_pm.cli versions --export compatibility-report.json

# Memory-specific validation
npm run memory:health && echo "✅ Memory system compatible"

# Framework health validation
npm run monitor:health && echo "✅ Framework health compatible"
```

## Prevention and Maintenance

### Regular Maintenance Tasks

```bash
# Weekly version validation
#!/bin/bash
# weekly-version-check.sh

echo "🔢 Weekly Version Compatibility Check - $(date)"
echo "================================================"

# 1. Validate all versions
python -m claude_pm.cli validate-versions --detailed

# 2. Check performance
echo "⏱️  Performance Check"
time npm run monitor:once > /dev/null

# 3. Memory system health
echo "🧠 Memory System Check"
npm run memory:health

# 4. Generate report
python -m claude_pm.cli versions --export "weekly-version-report-$(date +%Y%m%d).json"

echo "✅ Weekly check completed"
```

### Automated Monitoring Setup

```yaml
# .github/workflows/version-monitoring.yml
name: Continuous Version Monitoring

on:
  schedule:
    - cron: '0 */6 * * *' # Every 6 hours
  
jobs:
  version-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Validate versions
      run: |
        python -m claude_pm.cli validate-versions --detailed
    
    - name: Performance check
      run: |
        timeout 30s npm run monitor:once || exit 1
    
    - name: Create issue on failure
      if: failure()
      uses: actions/github-script@v6
      with:
        script: |
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: 'Version Compatibility Issue Detected',
            body: 'Automated version monitoring detected compatibility issues. Please investigate.',
            labels: ['bug', 'version-compatibility']
          })
```

This comprehensive troubleshooting guide ensures rapid resolution of version compatibility issues while maintaining the integrity and performance of the Claude PM Framework.