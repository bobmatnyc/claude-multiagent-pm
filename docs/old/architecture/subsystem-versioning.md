# Claude PM Framework - Subsystem Versioning Architecture

## Overview

The Claude PM Framework implements a comprehensive subsystem versioning system that enables granular version tracking and compatibility validation across all framework components. This architecture supports both serial number versioning (001, 002) for framework subsystems and semantic versioning (x.y.z) for package compatibility.

## Architecture Design

### Version File Structure

Each subsystem maintains its own version file in the framework root directory:

```
/Users/masa/Projects/claude-multiagent-pm/
├── FRAMEWORK_VERSION        # Main framework version (010)
├── MEMORY_VERSION          # Memory subsystem version (002)
├── AGENTS_VERSION          # Agent subsystem version (001)
├── TICKETING_VERSION       # Ticketing subsystem version (001)
├── DOCUMENTATION_VERSION   # Documentation subsystem version (001)
├── SERVICES_VERSION        # Services subsystem version (001)
├── CLI_VERSION             # CLI subsystem version (001)
├── INTEGRATION_VERSION     # Integration subsystem version (001)
└── HEALTH_VERSION          # Health monitoring version (001)
```

### Current Version Status (2025-07-14)

| Subsystem      | Version | Status | Description |
|----------------|---------|--------|-------------|
| FRAMEWORK      | 010     | ✅ Active | Core framework version |
| MEMORY         | 002     | ✅ Enhanced | Memory optimization with subprocess integration |
| AGENTS         | 001     | ✅ Stable | Agent management system |
| TICKETING      | 001     | ✅ Stable | Universal ticketing interface |
| DOCUMENTATION  | 001     | ✅ Stable | Documentation management |
| SERVICES       | 001     | ✅ Stable | Core services layer |
| CLI            | 001     | ✅ Stable | Command-line interface |
| INTEGRATION    | 001     | ✅ Stable | System integration layer |
| HEALTH         | 001     | ✅ Stable | Health monitoring system |

## Serial Number Versioning Standards

### Format Specification

- **Pattern**: Three-digit zero-padded serial numbers (001, 002, 003, etc.)
- **Increment**: Sequential increment for each subsystem update
- **Scope**: Independent versioning per subsystem
- **Reset**: Never reset; always increment forward

### Version Increment Rules

1. **Initial Version**: Always starts at `001`
2. **Update Process**: Increment by 1 for each significant change
3. **Zero-Padding**: Maintain three-digit format (001, 002, 010, 100)
4. **Cross-Subsystem**: Versions are independent across subsystems

### Example Evolution

```
MEMORY_VERSION progression:
001 → Initial memory system implementation
002 → Memory optimization with subprocess manager integration
003 → (Future) Advanced memory pooling and leak prevention
```

## Framework-Subsystem Relationship

### Version Compatibility Matrix

| Framework Version | Compatible Subsystem Versions |
|-------------------|-------------------------------|
| 010               | MEMORY: 002+, All others: 001+ |
| 011 (future)      | MEMORY: 003+, AGENTS: 002+    |

### Dependency Management

```python
# Example compatibility requirements
FRAMEWORK_010_REQUIREMENTS = {
    "memory": "002",        # Requires enhanced memory system
    "agents": "001",        # Base agent system sufficient
    "ticketing": "001",     # Base ticketing system sufficient
    "documentation": "001", # Base documentation system sufficient
    "services": "001",      # Base services sufficient
    "cli": "001",          # Base CLI sufficient
    "integration": "001",   # Base integration sufficient
    "health": "001"        # Base health monitoring sufficient
}
```

## Enhanced Memory Scripts Integration

### Memory System v002 Features

The MEMORY_VERSION 002 includes enhanced subprocess management integration:

#### Enhanced Scripts
- **memory-optimization.js**: Memory optimization with subprocess coordination
- **memory-monitor.js**: Real-time memory monitoring with predictive alerts
- **Subprocess Integration**: Coordinated memory management across processes

#### Key Enhancements in v002
1. **Subprocess Memory Isolation**: 1.5GB per subprocess limit
2. **Predictive Alerting**: Proactive memory threshold monitoring
3. **Circuit Breaker Pattern**: Automatic process termination at 3.5GB
4. **Memory History Tracking**: Comprehensive memory usage analytics
5. **Process Health Management**: Integrated subprocess lifecycle management

### Memory Configuration Standards

```javascript
// Memory limits for v002
const memoryConfig = {
    maxHeapSize: 4 * 1024 * 1024 * 1024,      // 4GB total heap
    subprocessLimit: 1.5 * 1024 * 1024 * 1024, // 1.5GB per subprocess
    criticalThreshold: 0.8,                    // 80% of max heap
    warningThreshold: 0.7,                     // 70% of max heap
    maxSubprocesses: 2,                        // Maximum concurrent processes
    subprocessTimeout: 300000                  // 5 minute timeout
};
```

## Version Management Utilities

### SubsystemVersionManager Class

The framework provides a comprehensive version management utility:

```python
from claude_pm.utils.subsystem_versions import SubsystemVersionManager

# Initialize version manager
manager = SubsystemVersionManager()

# Scan all subsystem versions
await manager.scan_subsystem_versions()

# Get specific version
memory_version = manager.get_version("memory")  # Returns "002"

# Update version with backup
await manager.update_version("memory", "003", backup=True)

# Validate compatibility
requirements = {"memory": "002", "framework": "010"}
checks = await manager.validate_compatibility(requirements)
```

### Version Comparison Logic

The system supports multiple version formats:

```python
# Serial number comparison (001, 002, 003)
manager.compare_versions("002", "001")  # Returns 1 (002 > 001)

# Semantic version comparison (x.y.z)
manager.compare_versions("1.2.3", "1.2.0")  # Returns 1 (1.2.3 > 1.2.0)

# Mixed format handling with fallback to string comparison
```

### Version Increment Utilities

```python
from claude_pm.utils.subsystem_versions import increment_version

# Serial number increment
increment_version("002", "serial")  # Returns "003"

# Semantic version increment
increment_version("1.2.3", "patch")  # Returns "1.2.4"
increment_version("1.2.3", "minor")  # Returns "1.3.0"
increment_version("1.2.3", "major")  # Returns "2.0.0"
```

## Package.json Integration

### NPM Package Version

The framework maintains version consistency across multiple systems:

- **NPM Package Version**: 0.6.2 (in package.json)
- **Framework Version**: 010 (subsystem versioning)
- **Python Package**: Uses NPM version for consistency

### Script Integration

```json
{
  "version": "0.6.2",
  "scripts": {
    "memory:monitor": "NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node scripts/memory-monitor.js",
    "memory:optimize": "NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node scripts/memory-optimization.js optimize",
    "memory:health": "NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node scripts/process-health-manager.js"
  }
}
```

## Version File Management

### File Format Standards

Each version file contains a single line with the version number:

```bash
# MEMORY_VERSION
002

# FRAMEWORK_VERSION  
010

# AGENTS_VERSION
001
```

### Backup and Recovery

The system automatically creates backups during version updates:

```
.claude-pm/framework_backups/
├── MEMORY_VERSION.backup.20250714_143025
├── FRAMEWORK_VERSION.backup.20250714_143025
└── ...
```

### Atomic Updates

Version updates are atomic operations:
1. Create backup of existing version file
2. Write new version to temporary file
3. Atomic rename to replace original
4. Update internal tracking

## Health Monitoring Integration

### Version-Aware Health Checks

The health monitoring system reports subsystem versions:

```python
{
    "framework_version": "010",
    "subsystem_versions": {
        "memory": "002",
        "agents": "001",
        "ticketing": "001"
    },
    "version_compatibility": {
        "all_compatible": true,
        "validation_timestamp": "2025-07-14T14:30:25Z"
    }
}
```

### Performance Optimization

Version 002 memory system includes performance enhancements:
- **<15 second health monitoring** (77% improvement)
- **Optimized version detection** with caching
- **Reduced subprocess overhead** through better isolation

## Development Workflow Standards

### Version Update Process

1. **Development Changes**: Implement subsystem enhancements
2. **Version Increment**: Update appropriate VERSION file
3. **Compatibility Testing**: Validate against framework requirements
4. **Documentation Update**: Update architecture docs
5. **Deployment**: Deploy with version validation

### Best Practices

1. **Independent Versioning**: Each subsystem versions independently
2. **Backward Compatibility**: Maintain compatibility within major framework versions
3. **Clear Documentation**: Document all version changes and requirements
4. **Automated Validation**: Use CLI tools for version validation
5. **Backup Management**: Always backup before version updates

### Version Planning

```
Planned Version Evolution:
├── Framework 011
│   ├── MEMORY_VERSION: 003 (Advanced pooling)
│   ├── AGENTS_VERSION: 002 (Enhanced orchestration)
│   └── CLI_VERSION: 002 (Extended commands)
└── Framework 012
    ├── INTEGRATION_VERSION: 002 (MCP enhancements)
    └── HEALTH_VERSION: 002 (Predictive monitoring)
```

## Conclusion

The Claude PM Framework's subsystem versioning architecture provides:

- **Granular Control**: Independent versioning per subsystem
- **Compatibility Validation**: Automated requirement checking
- **Enhanced Memory Management**: Optimized subprocess coordination
- **Developer Tools**: Comprehensive CLI utilities
- **Future-Proof Design**: Scalable to framework evolution

This architecture ensures maintainable, compatible, and traceable evolution of the framework while supporting the complex multi-agent orchestration requirements of the Claude PM system.