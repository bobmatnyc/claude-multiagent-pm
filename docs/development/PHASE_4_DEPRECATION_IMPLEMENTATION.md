# Phase 4 Deprecation Implementation Report

## Overview
Implemented deprecation warnings and migration helpers for transitioning from editable/source installations to PyPI package installations as part of ISS-0163.

## Changes Implemented

### 1. **bin/claude-pm Script Updates**
- Removed hardcoded path: `/Users/masa/Projects/claude-multiagent-pm` (line 43)
- Added deprecation warning when editable mode is detected
- Added support for `CLAUDE_PM_SOURCE_MODE=deprecated` environment variable
- Updated path detection to prefer package installations over source

### 2. **postinstall-minimal.js Updates**
- Modified to prefer PyPI installation over editable mode
- Added deprecation warning when falling back to editable installation
- Reordered installation attempts: PyPI first, then editable as fallback

### 3. **Python Package Deprecation Module**
Created `claude_pm/utils/deprecation.py`:
- `check_editable_installation()`: Detects and warns about editable installations
- `ensure_pypi_installation()`: Helper to verify installation type
- Integrated with main package __init__.py for automatic warnings

### 4. **Migration Helper Script**
Created `scripts/migrate_to_pypi.py`:
- Automated migration from editable to PyPI installation
- Backs up user data before migration
- Uninstalls editable version
- Installs from PyPI
- Verifies installation
- Provides clear migration instructions

### 5. **Documentation**
- Created comprehensive `docs/MIGRATION.md` guide
- Updated README.md with deprecation notice
- Added migration instructions and timeline

## Key Features

### Environment Variable Support
```bash
export CLAUDE_PM_SOURCE_MODE=deprecated
```
Suppresses deprecation warnings during transition period.

### Backward Compatibility
- All existing functionality maintained
- Graceful fallback to editable mode if PyPI fails
- Clear migration path without breaking changes

### User Data Protection
- Migration script backs up all user data
- Preserves custom agents, configs, and memory
- Rollback capability via backups

## Migration Path

### For Users
1. See deprecation warning on startup
2. Run `python scripts/migrate_to_pypi.py`
3. Follow automated migration process
4. Verify installation works

### For Developers
1. Use virtual environment for development
2. Set `CLAUDE_PM_SOURCE_MODE=deprecated` 
3. Continue development with suppressed warnings

## Testing
Created `test_deprecation_warnings.py` to verify:
- Warnings appear without suppression
- Warnings suppressed with environment variable
- CLI shows appropriate messages

## Timeline
- **v1.3.0**: Deprecation warnings introduced (current)
- **v1.4.0**: Stronger warnings, limited support
- **v2.0.0**: Complete removal of editable support

## Benefits
1. **Consistency**: Single installation method
2. **Reliability**: No path detection issues
3. **Performance**: Optimized package loading
4. **Security**: Verified package integrity
5. **Maintenance**: Easier to support and update

## Next Steps
1. Monitor user feedback on migration process
2. Update CI/CD to test PyPI installations
3. Remove editable-specific code in v2.0.0
4. Update all documentation to reflect PyPI-first approach