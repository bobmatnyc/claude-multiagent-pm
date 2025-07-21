# Safe Local Test Deployment Plan

## Current State
- ✅ `backwards_compatible_orchestrator.py` - Successfully refactored (27 lines)
- ✅ `agent_registry.py` - Reduced to 157 lines  
- ❌ `parent_directory_manager.py` - Still 1048 lines (needs modules created)
- ❌ `agent_registry_sync.py` - File removed (consolidated with agent_registry.py)

## Safe Test Options

### Option 1: Virtual Environment Test (Recommended)
```bash
# Run the local test deployment script
./scripts/local_test_deployment.sh
```
- Creates isolated Python virtual environment
- Copies code to separate directory
- Runs tests without affecting system
- Easy rollback: just delete test directory

### Option 2: Docker Test (Most Isolated)
```bash
# Run Docker-based test
./scripts/docker_test_deployment.sh
```
- Complete isolation in container
- No impact on host system
- Requires Docker installed

### Option 3: Branch-Based Test
```bash
# Create test branch
git checkout -b test/ep-0043-refactoring

# Make changes and test
python scripts/quick_refactor_test.py

# If issues, just switch back
git checkout main
```

## What The Test Will Validate

1. **Import Compatibility**
   - Old import paths still work
   - No breaking changes for users

2. **Functionality**
   - Core features work as expected
   - No runtime errors

3. **Performance**
   - No significant slowdown
   - Memory usage normal

## Quick Pre-Test Check
```bash
# Check current state
python scripts/quick_refactor_test.py

# Verify no uncommitted changes that could be lost
git status
```

## Rollback Procedures

### For Virtual Environment Test:
```bash
# Complete removal
rm -rf ~/test-deployments/claude-pm-refactor-test

# Your system remains untouched
```

### For Docker Test:
```bash
# Remove test image
docker rmi claude-pm-refactor-test

# No system changes needed
```

### For Branch Test:
```bash
# Discard changes and return to main
git checkout main
git branch -D test/ep-0043-refactoring
```

## Next Steps

1. Choose your preferred test method
2. Run the test
3. Review results
4. If successful, plan production deployment
5. If issues found, fix and retest

## Important Notes

- **These tests do NOT affect your installed claude-pm**
- **Your current working installation remains safe**
- **Tests are completely isolated**
- **Easy rollback if any issues**

The virtual environment test (Option 1) is recommended as it's:
- Easy to run
- Provides good isolation  
- Allows interactive debugging
- Doesn't require Docker