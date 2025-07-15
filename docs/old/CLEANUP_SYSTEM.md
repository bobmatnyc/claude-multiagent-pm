# Claude PM Framework - Comprehensive Cleanup System

## Overview

The Claude PM Framework includes a comprehensive cleanup system designed to handle complete removal of all framework components while respecting user data and providing backup options. This system addresses the issue of orphaned data after NPM uninstall operations.

## Architecture

### Components

1. **Preuninstall Script** (`install/preuninstall.js`)
   - Main cleanup orchestrator
   - Detects all installation types
   - Handles user data with backup options
   - Provides interactive and automatic modes

2. **CLI Integration** (`bin/claude-pm --cleanup`)
   - Self-removal command in main CLI
   - Integration with preuninstall script
   - Safety checks and confirmations

3. **NPM Script Integration** (`package.json`)
   - Automatic preuninstall hook
   - Manual cleanup scripts
   - Complete uninstall workflow

4. **Memory Collection System**
   - Tracks cleanup operations
   - Collects user feedback
   - Provides insights for improvements

## Installation Detection

### NPM Installations
- Global npm packages via `npm config get prefix`
- NVM installations in `~/.nvm/versions/node/*/lib/node_modules/`
- Alternative global paths (`/usr/local/lib/node_modules/`, `~/.npm-global/`)
- Windows AppData npm installations

### Python pip Installations
- System pip installations
- User pip installations (`--user` flag)
- Virtual environment installations
- Multiple Python version detection (`python3`, `python`, `py`)

### User Data Locations
- Primary config: `~/.claude-pm/`
- Memory system: `~/.claude-pm/memory/`, `~/.claude-pm/chroma_db/`
- CLI executables: `~/.local/bin/claude-pm`, `/usr/local/bin/claude-pm`
- Backup locations: Multiple common backup directories
- Temporary files: OS temp directories and cache locations

## User Data Handling

### Backup Creation
```javascript
// Automatic backup with timestamped directories
const backupPath = `${userHome}/claude-pm-uninstall-backup/claude-pm-backup-${timestamp}`;

// Backup includes:
// - Complete ~/.claude-pm/ directory
// - Backup manifest with metadata
// - Memory system data (if present)
// - Configuration files
```

### Backup Manifest
```json
{
  "timestamp": "2025-07-14T10:00:00Z",
  "backup_reason": "pre_uninstall_cleanup",
  "original_paths": {
    "user_config": "/Users/user/.claude-pm"
  },
  "backup_paths": {
    "user_config": "/Users/user/claude-pm-uninstall-backup/.claude-pm"
  },
  "total_size_bytes": 20971520,
  "total_files": 1247,
  "memory_system_included": true,
  "platform": "darwin",
  "node_version": "v20.19.0"
}
```

## Cleanup Modes

### 1. Automatic Mode (npm preuninstall)
```bash
# Triggered automatically during npm uninstall
npm uninstall -g @bobmatnyc/claude-multiagent-pm
```

**Behavior:**
- Conservative cleanup (keeps user data)
- Removes package installations only
- No interactive prompts
- Creates cleanup memory entry
- Displays information about preserved user data

### 2. Interactive Mode (Manual)
```bash
# CLI integration
claude-pm --cleanup

# NPM scripts
npm run cleanup
npm run cleanup:full
```

**Options:**
1. Remove only package installations (keep user data)
2. Remove everything including user data (with backup)
3. Remove everything including user data (no backup)
4. Custom cleanup (interactive selection)
5. Cancel cleanup

### 3. Automatic Full Mode
```bash
claude-pm --cleanup --auto
npm run cleanup:auto
```

**Behavior:**
- Automatic execution with sensible defaults
- Preserves user data unless explicitly requested
- Creates backups when removing user data
- Minimal prompts for critical decisions

## Safety Features

### User Confirmations
```javascript
// Multiple confirmation levels
const removeUserData = await promptUser('Remove user data (~/.claude-pm)?', false);

const finalConfirm = await promptUser(
    '🚨 Final confirmation: Proceed with cleanup?', 
    false
);

// Special confirmation for destructive operations
const confirmNoBackup = await promptUser(
    '🚨 This will PERMANENTLY remove all user data without backup. Are you absolutely sure?',
    false
);
```

### Backup Safety
- Automatic backup creation before user data removal
- Timestamped backup directories prevent conflicts
- Backup verification and integrity checks
- Clear backup location reporting

### Error Handling
- Graceful failure handling with detailed error messages
- Partial cleanup support (continue on non-critical errors)
- Manual cleanup instructions for failure scenarios
- Memory collection of errors for improvement

## Memory Collection

### Cleanup Statistics
```json
{
  "timestamp": "2025-07-14T10:00:00Z",
  "category": "cleanup",
  "event_type": "pre_uninstall_cleanup",
  "platform": "darwin",
  "cleanup_stats": {
    "total_files_found": 1247,
    "total_size_bytes": 20971520,
    "total_size_formatted": "20.0 MB",
    "user_data_detected": true,
    "memory_system_detected": true,
    "items_removed": 8,
    "errors_encountered": 0,
    "backups_created": 1
  },
  "installation_paths": {
    "global_node_modules": ["/Users/user/.nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/claude-multiagent-pm"],
    "pip_packages": [],
    "backup_locations": ["/Users/user/.claude-pm/framework_backups"],
    "temp_files": ["/Users/user/.claude-pm/logs"]
  },
  "user_feedback": {
    "cleanup_reason": "uninstall",
    "satisfaction_with_cleanup": "pending_collection"
  }
}
```

## Usage Examples

### Complete Interactive Uninstall
```bash
# Run complete interactive uninstall process
npm run uninstall:complete

# This executes:
# 1. Interactive cleanup with user data options
# 2. Backup creation (if requested)
# 3. Comprehensive removal
# 4. NPM package uninstall
# 5. Verification and reporting
```

### Safe User Data Preservation
```bash
# Remove framework but keep user data
claude-pm --cleanup --auto

# User data preserved at:
# ~/.claude-pm/ (configurations, memory, backups)
```

### Complete Removal with Backup
```bash
# Interactive mode with backup option
claude-pm --cleanup --full

# Process:
# 1. Scan installations (reports 107MB+ found)
# 2. Offer backup creation
# 3. Create timestamped backup
# 4. Remove all components
# 5. Verify complete removal
```

### Manual Cleanup Scripts
```bash
# Alternative NPM script methods
npm run cleanup              # Interactive mode
npm run cleanup:full         # Full interactive cleanup
npm run cleanup:auto         # Automatic conservative cleanup
```

## Verification System

### Post-Cleanup Validation
```javascript
async verifyCleanup() {
    // Re-scan all installation locations
    const remainingPaths = await this.scanInstallations();
    
    if (remainingPaths.length === 0) {
        return true; // Complete cleanup
    } else {
        // Report remaining files for manual removal
        return false;
    }
}
```

### Cleanup Summary Report
```
🧹 Claude PM Framework Cleanup Summary
════════════════════════════════════════════════════════════════════════════════

📊 Cleanup Results:
   Items Removed: 8
   Errors: 0
   Backups Created: 1

✅ Successfully Removed:
   1. /Users/user/.nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/claude-multiagent-pm
   2. /Users/user/.local/bin/claude-pm
   3. /Users/user/.claude-pm/logs
   4. /Users/user/.claude-pm/temp
   5. npm:@bobmatnyc/claude-multiagent-pm
   6. /Users/user/.claude-pm/memory (backed up)
   7. /Users/user/.claude-pm/chroma_db (backed up)
   8. /Users/user/.claude-pm (backed up)

🛡️  Backup Location:
   /Users/user/claude-pm-uninstall-backup/claude-pm-backup-2025-07-14T10-00-00-000Z
   💡 Your user data has been safely backed up

📝 Memory Collection:
   All cleanup activities and user feedback have been logged
   for future improvements to the uninstall process.
```

## Error Scenarios and Recovery

### Common Issues

1. **Permission Errors**
   ```bash
   # Manual cleanup for permission issues
   sudo rm -rf ~/.claude-pm/
   sudo rm -f ~/.local/bin/claude-pm
   sudo npm uninstall -g @bobmatnyc/claude-multiagent-pm
   ```

2. **Partial Cleanup**
   ```bash
   # Re-run cleanup to catch missed items
   claude-pm --cleanup --auto
   
   # Or manual verification
   find ~ -name "*claude*pm*" -type d 2>/dev/null
   ```

3. **Backup Failures**
   ```bash
   # Continue without backup (with confirmation)
   # Manual backup before cleanup
   cp -r ~/.claude-pm ~/claude-pm-manual-backup
   ```

### Recovery Options

1. **Restore from Backup**
   ```bash
   # Restore user data from backup
   cp -r ~/claude-pm-uninstall-backup/claude-pm-backup-*/\.claude-pm ~/.claude-pm
   ```

2. **Partial Restoration**
   ```bash
   # Restore only specific components
   cp -r ~/claude-pm-uninstall-backup/claude-pm-backup-*/\.claude-pm/memory ~/.claude-pm/
   ```

## Integration with Framework

### NPM Lifecycle Integration
```json
{
  "scripts": {
    "preuninstall": "node install/preuninstall.js --automatic",
    "cleanup": "node install/preuninstall.js",
    "cleanup:full": "node install/preuninstall.js --interactive",
    "cleanup:auto": "node install/preuninstall.js --automatic",
    "uninstall:complete": "node install/preuninstall.js --interactive && npm uninstall -g @bobmatnyc/claude-multiagent-pm"
  }
}
```

### CLI Command Integration
```python
# claude-pm --cleanup command
def handle_cleanup_command(args):
    # Parse flags and execute cleanup script
    # Provide safety checks and user feedback
    # Display comprehensive cleanup results
```

## Testing

### Test Coverage
- Installation detection accuracy
- Size calculation correctness
- Memory system detection
- Backup creation functionality
- CLI integration verification
- NPM script integration
- Safety feature validation
- Error handling robustness

### Test Execution
```bash
# Run cleanup system tests
python tests/test_cleanup_system.py

# Validate integration
npm test  # Includes cleanup integration tests
```

## Best Practices

### For Users
1. **Always use interactive mode** for first-time cleanup
2. **Create backups** when removing user data
3. **Verify cleanup completion** with verification tools
4. **Keep backup manifests** for restoration reference

### For Developers
1. **Test cleanup thoroughly** before releases
2. **Document cleanup behavior** for new features
3. **Collect cleanup metrics** for improvement
4. **Handle edge cases gracefully** with clear error messages

## Future Enhancements

### Planned Features
- **Selective cleanup** (choose specific components)
- **Cleanup scheduling** (automated maintenance)
- **Cloud backup integration** (sync user data)
- **Cleanup analytics** (usage patterns and optimization)

### Community Feedback Integration
- **User satisfaction surveys** post-cleanup
- **Cleanup behavior analytics** for improvements
- **Error pattern analysis** for robustness
- **Performance optimization** based on usage data

## Troubleshooting

### Debug Mode
```bash
# Enable verbose cleanup logging
NODE_DEBUG=cleanup npm run cleanup:full

# Manual step-by-step cleanup
claude-pm --cleanup --interactive --verbose
```

### Support Resources
- GitHub Issues: Report cleanup problems
- Documentation: Comprehensive guides
- Community: User experiences and solutions
- Memory System: Automatic issue tracking and improvement