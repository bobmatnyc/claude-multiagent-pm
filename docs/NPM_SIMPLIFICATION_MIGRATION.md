# NPM Package Simplification Migration Guide

## Overview

This document outlines the migration from a complex NPM package (bundling 350+ Python files) to a simplified installer-only approach where NPM serves purely as an installation mechanism for the PyPI package.

## Current State (Before Migration)

- **NPM Package Size**: ~17MB containing 350+ Python source files
- **Postinstall Script**: 733 lines of complex installation logic
- **Distribution**: Python source bundled within NPM package
- **Maintenance**: Dual distribution (NPM + PyPI) causing synchronization issues

## Target State (After Migration)

- **NPM Package Size**: <100KB (only installer scripts)
- **Postinstall Script**: ~70 lines of simple PyPI installation
- **Distribution**: NPM installs from PyPI (single source of truth)
- **Maintenance**: Simplified - PyPI is the only Python source distribution

## Migration Files

### 1. Simplified Postinstall Script
**File**: `install/postinstall-simple.js`
```javascript
#!/usr/bin/env node
// Simple script that only installs from PyPI
// Falls back to local installation for development
```

### 2. Simplified Package.json
**File**: `package-simple.json`
- Removed Python source from `files` array
- Simplified scripts to only essential commands
- Updated postinstall to use `postinstall-simple.js`

### 3. NPM Ignore File
**File**: `.npmignore`
- Excludes all Python source (`claude_pm/`, `*.py`)
- Excludes tests, scripts, and development files
- Only includes: `bin/`, `install/postinstall-simple.js`, `README.md`, `LICENSE`

### 4. Simplified CLI Wrapper
**File**: `bin/claude-pm-simple`
- Minimal Python wrapper (~20 lines)
- Simply executes `python -m claude_pm.cli`
- No complex path detection or framework loading

## Migration Steps

### Phase 1: Local Testing
1. Test simplified postinstall script locally
2. Verify PyPI installation works correctly
3. Test fallback to local installation

### Phase 2: Pre-PyPI Publishing
1. Rename current files (backup):
   - `package.json` → `package-complex.json`
   - `install/postinstall-minimal.js` → `install/postinstall-complex.js`
   
2. Activate simplified files:
   - `package-simple.json` → `package.json`
   - Update package.json to use `postinstall-simple.js`

3. Test NPM package locally:
   ```bash
   npm pack
   npm install -g bobmatnyc-claude-multiagent-pm-*.tgz
   ```

### Phase 3: PyPI Publishing
1. Publish Python package to PyPI:
   ```bash
   python -m build
   twine upload dist/*
   ```

2. Update postinstall-simple.js to remove fallback logic

3. Test NPM package with PyPI:
   ```bash
   npm publish --dry-run
   ```

### Phase 4: NPM Publishing
1. Publish simplified NPM package:
   ```bash
   npm publish
   ```

2. Monitor installation success rates

3. Address any installation issues

## Backward Compatibility

During transition period:
- Keep complex postinstall as `postinstall-complex.js`
- Maintain fallback in simple postinstall for pre-PyPI users
- Document migration path for existing users

## Benefits

1. **Reduced Complexity**: 90% reduction in postinstall script size
2. **Single Source**: PyPI becomes single source of Python code
3. **Faster Installation**: No need to bundle/unbundle Python files
4. **Easier Maintenance**: No dual distribution synchronization
5. **Better Security**: Users get code directly from PyPI

## Rollback Plan

If issues arise:
1. Restore complex package.json: `mv package-complex.json package.json`
2. Update postinstall back to complex version
3. Publish patch version with full Python source

## Testing Checklist

- [ ] Simple postinstall installs from PyPI successfully
- [ ] Fallback to local installation works (pre-PyPI)
- [ ] NPM package size is under 100KB
- [ ] `claude-pm` command works after installation
- [ ] All Python functionality remains intact
- [ ] Clean uninstall removes all components

## Timeline

- **Week 1**: Local testing and validation
- **Week 2**: PyPI publishing preparation
- **Week 3**: PyPI publication and NPM transition
- **Week 4**: Monitor and address any issues