---
issue_id: ISS-0113
title: Implement Claude PM CLI Flags (--save, --version, --upgrade, --rollback)
description: |-
  ## Overview
  Implement essential claude-pm CLI flags for enhanced user experience and operational control.

  ## Core Flags Required:
  - --save: Safe mode with no YOLO operations, requires confirmation for all destructive actions
  - --version: Display current version and component information
  - --upgrade: Update installation including NPM packages and framework components
  - --rollback: Rollback to previous stable version with state restoration

  ## Additional Supporting Flags:
  - --verify: Comprehensive installation verification and health checks
  - --debug: Verbose output for troubleshooting
  - --force: Override safety checks when necessary (opposite of --save)
  - --dry-run: Preview mode without execution

  ## Priority: Critical (User Experience)
status: active
priority: critical
assignee: masa
created_date: 2025-07-14T01:48:03.000Z
updated_date: 2025-07-14T01:48:03.000Z
estimated_tokens: 12000
actual_tokens: 0
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
related_tasks: []
related_issues:
  - EP-0037
  - ISS-0081
completion_percentage: 0
blocked_by: []
blocks: []
---

# Issue: Implement Claude PM CLI Flags (--save, --version, --upgrade, --rollback)

## Description
Implement essential claude-pm CLI flags for enhanced user experience and operational control, focusing on safety, version management, and upgrade capabilities.

## Background
Users need comprehensive CLI flag support for safe operations, version management, and system maintenance. This ticket implements the core flags necessary for production-ready framework usage with emphasis on safety and recoverability.

## Core CLI Flags

### 1. --save Flag (Safe Mode)
**Purpose**: Enable safe mode with no YOLO operations, requiring confirmation for all destructive actions.

**Behavior**:
- Require user confirmation for any destructive operations
- Create automatic backups before changes
- Enable comprehensive validation and checking
- Prevent automatic overwriting of existing files
- Display detailed information about what will be changed

**Implementation**:
```python
class SafeModeManager:
    def confirm_destructive_action(self, action: str, details: List[str]) -> bool
    def create_backup_before_action(self, action: str) -> str
    def validate_before_execution(self, operation: str) -> bool
    def log_safe_mode_operations(self, operation: str, result: bool) -> None
```

**Example Usage**:
```bash
claude-pm deploy --save          # Requires confirmation before deployment
claude-pm update --save          # Confirms each update operation
claude-pm rollback --save        # Confirms rollback with impact analysis
```

### 2. --version Flag
**Purpose**: Display current version and comprehensive component information.

**Information Displayed**:
- claude-pm framework version
- NPM package version
- Component versions (agents, templates, scripts)
- Installation location and status
- Last update timestamp
- Compatibility information

**Implementation**:
```python
class VersionManager:
    def get_framework_version(self) -> str
    def get_component_versions(self) -> Dict[str, str]
    def get_installation_info(self) -> Dict[str, Any]
    def format_version_display(self) -> str
    def check_version_compatibility(self) -> Dict[str, bool]
```

**Example Output**:
```
Claude PM Framework v0.6.1
==========================

Framework Core: v0.6.1
NPM Package: @bobmatnyc/claude-pm@0.6.1
Installation: ~/.claude-pm/
Deployed: /current/project/.claude-pm/

Components:
  - Agents System: v0.6.1
  - Template Engine: v0.6.1
  - Script Deployment: v0.6.1
  - Health Monitoring: v0.6.1

Platform: macOS 14.5 (Apple Silicon)
Python: 3.11.5
Node.js: 20.19.0

Status: ✅ All components up-to-date
Last Update: 2025-07-14T01:45:03.000Z
```

### 3. --upgrade Flag
**Purpose**: Update installation including NPM packages and framework components.

**Upgrade Process**:
1. Check for available updates
2. Create backup of current installation
3. Update NPM package to latest version
4. Update framework components
5. Migrate configuration if needed
6. Validate upgraded installation
7. Report upgrade results

**Implementation**:
```python
class UpgradeManager:
    def check_for_updates(self) -> Dict[str, str]
    def create_upgrade_backup(self) -> str
    def perform_npm_update(self) -> bool
    def update_framework_components(self) -> bool
    def migrate_configuration(self) -> bool
    def validate_upgrade(self) -> Dict[str, bool]
    def rollback_failed_upgrade(self) -> bool
```

**Example Usage**:
```bash
claude-pm --upgrade              # Update to latest version
claude-pm --upgrade --save       # Update with confirmation prompts
claude-pm --upgrade --verify     # Update with comprehensive validation
```

### 4. --rollback Flag
**Purpose**: Rollback to previous stable version with state restoration.

**Rollback Process**:
1. List available rollback points
2. Allow user selection of target version
3. Validate rollback compatibility
4. Create backup of current state
5. Restore previous version
6. Migrate configuration backward if needed
7. Validate rollback success

**Implementation**:
```python
class RollbackManager:
    def list_rollback_points(self) -> List[Dict[str, Any]]
    def validate_rollback_target(self, version: str) -> bool
    def create_rollback_backup(self) -> str
    def perform_rollback(self, version: str) -> bool
    def migrate_configuration_backward(self) -> bool
    def validate_rollback_success(self) -> Dict[str, bool]
```

**Example Usage**:
```bash
claude-pm --rollback             # Interactive rollback selection
claude-pm --rollback v0.6.0      # Rollback to specific version
claude-pm --rollback --save      # Rollback with confirmation
```

## Additional Supporting Flags

### 5. --verify Flag
**Purpose**: Comprehensive installation verification and health checks.

**Verification Process**:
- Component integrity checking
- Configuration validation
- Permission verification
- Dependency checking
- Performance validation
- Integration testing

### 6. --debug Flag
**Purpose**: Verbose output for troubleshooting and diagnostics.

**Debug Information**:
- Detailed operation logging
- Component status information
- Configuration details
- Error stack traces
- Performance metrics

### 7. --force Flag
**Purpose**: Override safety checks when necessary (opposite of --save).

**Behavior**:
- Skip confirmation prompts
- Override compatibility checks
- Force operations even with warnings
- Bypass validation when needed

### 8. --dry-run Flag
**Purpose**: Preview mode without execution.

**Behavior**:
- Show what would be done without executing
- Validate operations without changes
- Preview upgrade/rollback impact
- Test configuration changes

## Flag Combination Logic

### Compatible Combinations
- `--save --verify`: Safe mode with comprehensive validation
- `--upgrade --save`: Safe upgrade with confirmations
- `--rollback --save`: Safe rollback with confirmations
- `--debug --verify`: Debug mode with comprehensive checking
- `--dry-run --upgrade`: Preview upgrade without execution

### Incompatible Combinations
- `--save --force`: Contradictory safety approaches
- `--dry-run --force`: Preview mode conflicts with force execution

## Implementation Architecture

### CLI Argument Parser
```python
class CLIArgumentParser:
    def parse_arguments(self, args: List[str]) -> Dict[str, Any]
    def validate_flag_combinations(self, flags: Dict[str, bool]) -> bool
    def apply_flag_hierarchy(self, flags: Dict[str, bool]) -> Dict[str, bool]
```

### Flag Manager System
```python
class FlagManager:
    def __init__(self, flags: Dict[str, bool])
    def is_safe_mode(self) -> bool
    def requires_confirmation(self) -> bool
    def is_debug_enabled(self) -> bool
    def is_dry_run_mode(self) -> bool
```

### Operation Executor
```python
class OperationExecutor:
    def execute_with_flags(self, operation: str, flags: FlagManager) -> bool
    def handle_safe_mode_execution(self, operation: str) -> bool
    def handle_force_mode_execution(self, operation: str) -> bool
    def handle_dry_run_execution(self, operation: str) -> Dict[str, Any]
```

## Tasks
- [ ] Implement CLI argument parsing system
- [ ] Create flag validation and combination logic
- [ ] Build safe mode (--save) functionality
- [ ] Implement version display (--version) system
- [ ] Create upgrade management (--upgrade) system
- [ ] Build rollback capabilities (--rollback)
- [ ] Implement verification (--verify) system
- [ ] Add debug mode (--debug) functionality
- [ ] Create force mode (--force) operations
- [ ] Build dry-run (--dry-run) preview system
- [ ] Implement flag combination validation
- [ ] Create comprehensive help system
- [ ] Add flag inheritance for subcommands
- [ ] Build configuration file integration
- [ ] Create testing suite for all flag combinations

## Acceptance Criteria
- [ ] All core flags (--save, --version, --upgrade, --rollback) implemented
- [ ] Safe mode provides comprehensive confirmation and backup
- [ ] Version display shows complete component information
- [ ] Upgrade system updates all components reliably
- [ ] Rollback system restores previous versions successfully
- [ ] Flag combinations validated and handled correctly
- [ ] Help system provides clear guidance for all flags
- [ ] Error messages clear and actionable
- [ ] Performance impact minimal for flag processing
- [ ] Comprehensive testing covers all flag scenarios

## Technical Specifications

### Flag Processing Performance
- Argument parsing: <50ms
- Version information gathering: <500ms
- Upgrade checking: <2 seconds
- Rollback point enumeration: <1 second

### Safety and Backup Requirements
- Automatic backup creation before destructive operations
- Backup retention policy (keep last 5 versions)
- Backup validation and integrity checking
- Rollback point creation with metadata

### Configuration Integration
- Flag defaults from configuration files
- Environment variable support
- User preference persistence
- Project-specific flag overrides

## Error Handling

### Common Error Scenarios
1. **Invalid Flag Combinations**: Clear error messages with suggestions
2. **Insufficient Permissions**: Guidance for permission resolution
3. **Network Issues During Upgrade**: Offline mode and retry logic
4. **Corrupted Rollback Points**: Backup validation and recovery
5. **Version Compatibility Issues**: Compatibility checking and guidance

## Documentation Requirements
- Flag reference documentation
- Usage examples for each flag
- Flag combination guide
- Troubleshooting guide for flag-related issues
- Best practices for safe operations

## Notes
This implementation provides users with comprehensive control over claude-pm operations while maintaining safety and recoverability. The flags are designed to work together logically and provide clear feedback about their effects.

Related to EP-0037 (robust Mac installation system) and ISS-0081 (universal flag inheritance architecture).
