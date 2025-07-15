# Backup Creation Workflow - Developer Guide

## Overview

The Claude PM Framework now uses a centralized backup directory structure for all automated backup creation. This guide documents the new backup creation workflow and how different systems create backups.

## Centralized Backup Directory Structure

All backup files are now organized under a centralized `.claude-pm/backups/` directory:

```
.claude-pm/
└── backups/
    ├── framework/           # Framework template backups
    ├── scripts/            # Script deployment backups  
    ├── versions/           # Version file backups
    ├── templates/          # Template manager backups
    └── parent_directory_manager/  # Parent directory manager backups
```

## Backup Creation Systems

### 1. Parent Directory Manager

**Location**: `claude_pm/services/parent_directory_manager.py`

**Backup Directories**:
- **Framework templates**: `.claude-pm/backups/framework/`
- **General files**: `.claude-pm/backups/parent_directory_manager/`

**Key Methods**:
```python
# Framework template backup
backup_path = manager._backup_framework_template(framework_template_path)

# General file backup  
backup_path = await manager._create_backup(file_path)
```

**Backup Naming**:
- Framework: `framework_CLAUDE_md_{timestamp}.backup`
- General: `{filename}_{timestamp}.backup`

**Features**:
- Automatic backup rotation (keeps 2 most recent framework backups)
- Collision handling with counter suffixes
- Comprehensive backup status reporting

### 2. Script Deployment Manager

**Location**: `scripts/deploy_scripts.py`

**Backup Directory**: `.claude-pm/backups/scripts/`

**Key Methods**:
```python
# Automatic backup during deployment
success = manager.deploy_script("claude-pm")

# Manual rollback from backups
success = manager.rollback_script("claude-pm")
```

**Backup Naming**: `{script_name}_backup_{timestamp}`

**Features**:
- Automatic backup creation before script deployment
- Rollback functionality using most recent backup
- Deployment history tracking

### 3. Subsystem Version Manager

**Location**: `claude_pm/utils/subsystem_versions.py`

**Backup Directory**: `.claude-pm/backups/versions/`

**Key Methods**:
```python
# Automatic backup during version updates
success = await manager.update_subsystem_version("memory", "004")

# Manual backup creation
backup_path = manager._create_backup(version_file_path)
```

**Backup Naming**: `{version_filename}_backup_{timestamp}`

**Features**:
- Automatic backup before version file modifications
- Bulk update operations with backup support
- Version compatibility tracking

### 4. Template Manager

**Location**: `claude_pm/services/template_manager.py`

**Backup Directory**: `.claude-pm/backups/templates/`

**Key Methods**:
```python
# Automatic backup during template updates
backup_path = await manager._create_backup(template_id)
```

**Backup Naming**: `{template_id}_{timestamp}.backup`

**Features**:
- Template-specific subdirectories under backups/templates/
- Conflict detection and resolution
- Version tracking with backup correlation

## Backup Creation Best Practices

### 1. Consistent Naming Convention

All backup systems follow this naming pattern:
```
{identifier}_{backup|timestamp}_{optional_counter}.backup
```

Examples:
- `framework_CLAUDE_md_20250714_170156_489.backup`
- `claude-pm_backup_20250714_170157`
- `VERSION_backup_20250714_170158`

### 2. Timestamp Format

Standard timestamp format: `YYYYMMDD_HHMMSS`
- Framework templates include milliseconds for uniqueness
- Most systems use second precision
- All timestamps are in local time

### 3. Directory Creation

All backup systems ensure backup directories exist:
```python
self.backup_dir.mkdir(parents=True, exist_ok=True)
```

### 4. Error Handling

Robust error handling for backup operations:
```python
try:
    backup_path = self._create_backup(file_path)
    if backup_path:
        self.logger.info(f"Created backup: {backup_path}")
    else:
        self.logger.error(f"Failed to create backup for {file_path}")
except Exception as e:
    self.logger.error(f"Backup creation failed: {e}")
    return None
```

## Backward Compatibility

### Restore Operations

The framework maintains backward compatibility for restore operations:

1. **Framework Template Restore**: Looks only in new centralized location
2. **Script Rollback**: Uses new centralized backup directory
3. **Version File Restore**: Manual process using backup files

### Migration Notes

- **No automatic migration**: Existing backups in old locations remain unchanged
- **New backups only**: All new backups go to centralized locations
- **Manual cleanup**: Developers can manually clean old backup locations if desired

### Old vs New Locations

| System | Old Location | New Location |
|--------|-------------|-------------|
| Framework Templates | `.claude-pm/framework_backups/` | `.claude-pm/backups/framework/` |
| Scripts | Inline with scripts | `.claude-pm/backups/scripts/` |
| Versions | Inline with version files | `.claude-pm/backups/versions/` |
| Templates | `.claude-pm/template_manager/backups/` | `.claude-pm/backups/templates/` |

## Testing the Backup System

### Automated Tests

Run the provided test scripts to verify backup functionality:

```bash
# Test new backup creation workflow
python test_backup_creation.py

# Test backward compatibility
python test_backward_compatibility.py
```

### Manual Testing

1. **Framework Template Backup**:
   ```python
   from claude_pm.services.parent_directory_manager import ParentDirectoryManager
   manager = ParentDirectoryManager()
   await manager._initialize()
   
   framework_template = Path("framework/CLAUDE.md")
   backup_path = manager._backup_framework_template(framework_template)
   ```

2. **Script Deployment Backup**:
   ```bash
   python scripts/deploy_scripts.py --deploy --script claude-pm
   ```

3. **Version File Backup**:
   ```python
   from claude_pm.utils.subsystem_versions import SubsystemVersionManager
   manager = SubsystemVersionManager()
   await manager.update_subsystem_version("memory", "004")
   ```

## Integration Points

### Service Initialization

Backup directories are created during service initialization:
```python
async def _initialize(self) -> None:
    # Ensure backup directory exists
    self.backup_dir.mkdir(parents=True, exist_ok=True)
```

### Deployment Integration

The deployment system integrates backup creation:
```python
# Create backup before deployment
if target_path.exists():
    backup_path = self._create_backup(target_path)
    
# Proceed with deployment
self._deploy_content(source_path, target_path)
```

### Health Monitoring

Backup system health is monitored:
```python
status = manager.get_framework_backup_status()
# Returns: backup_count, backup_directory, backups[], etc.
```

## Troubleshooting

### Common Issues

1. **Backup Directory Not Created**:
   - Check permissions on `.claude-pm/` directory
   - Verify service initialization completed successfully

2. **Backup Creation Fails**:
   - Check disk space availability
   - Verify source file exists and is readable
   - Check backup directory write permissions

3. **Rollback/Restore Fails**:
   - Verify backup files exist in expected location
   - Check backup file integrity
   - Ensure target location is writable

### Debug Information

Enable debug logging to troubleshoot backup issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Backup operations log:
- Backup creation attempts
- Directory creation
- File copy operations
- Error conditions

## Future Enhancements

### Planned Improvements

1. **Backup Compression**: Compress older backup files to save space
2. **Backup Retention Policies**: Configurable retention periods for different backup types
3. **Backup Integrity Verification**: Checksum validation for backup files
4. **Cross-System Backup Coordination**: Unified backup management across all systems

### Configuration Options

Future versions will support backup configuration:
```yaml
backup_config:
  retention_days: 30
  compression_enabled: true
  max_backups_per_type: 10
  integrity_checking: true
```

---

**Last Updated**: 2025-07-14  
**Framework Version**: 0.7.5+  
**Documentation Version**: 1.0.0