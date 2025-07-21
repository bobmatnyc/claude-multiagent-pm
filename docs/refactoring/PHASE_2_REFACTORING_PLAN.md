# Phase 2 Refactoring Plan - Target 500 Lines

**Epic**: EP-0043 - Code Maintainability  
**Phase**: 2 - Aggressive Modularization  
**Target**: ~500 lines per file  
**Created**: 2025-01-19  

## Overview

Phase 2 takes the refactoring further by breaking down files to approximately 500 lines each. This provides optimal readability, testability, and maintainability.

## Refactoring Process (TDD Approach)

For each file:
1. **Write comprehensive unit tests** for all atomic methods
2. **Run tests** to establish baseline
3. **Refactor** into modules (~500 lines each)
4. **Re-run tests** to verify no regression
5. **Update documentation**

## Priority Order

### 1. parent_directory_manager.py (1,048 → ~500 lines)
**Current**: Single file with mixed responsibilities  
**Target Structure**:
```
claude_pm/services/parent_directory/
├── __init__.py              # Public API exports (~50 lines)
├── core.py                  # Core ParentDirectoryManager (~500 lines)
├── backup_manager.py        # Backup operations (~200 lines)
├── template_deployer.py     # Template deployment (~200 lines)
├── framework_protector.py   # Framework protection (~150 lines)
├── version_control.py       # Version management (~150 lines)
└── validators.py            # Validation utilities (~100 lines)
```

### 2. orchestrator modules (already <500 lines each)
**Current modules in orchestrator/**:
- mode_detection.py (needs tests)
- compatibility.py (needs tests)
- subprocess_execution.py (needs tests)
- agent_handlers.py (needs tests)
- local_execution.py (needs tests)
- context_collection.py (needs tests)

### 3. agent_registry.py (157 → maintain, add tests)
Already under target, but needs:
- Comprehensive unit tests
- Missing method implementations
- Documentation

### 4. Future files from EP-0043 list
Continue with remaining 12 files in priority order

## Testing Strategy

### Unit Test Structure
```python
# test_parent_directory_manager_atomic.py
class TestParentDirectoryManagerAtomic:
    """Test all atomic methods before refactoring"""
    
    def test_init(self):
        """Test initialization"""
        
    def test_get_config(self):
        """Test configuration retrieval"""
        
    def test_validate_path(self):
        """Test path validation"""
        
    # ... test every public method
```

### Test Categories
1. **Atomic Method Tests**: Individual method functionality
2. **Integration Tests**: Module interactions
3. **Backward Compatibility Tests**: Import paths and APIs
4. **Performance Tests**: Ensure no regression

## Module Design Principles

### Size Guidelines
- **Target**: 300-500 lines per module
- **Maximum**: 600 lines (hard limit)
- **Minimum**: 100 lines (avoid over-fragmentation)

### Cohesion Rules
- **Single Responsibility**: One clear purpose per module
- **High Cohesion**: Related functions stay together
- **Low Coupling**: Minimize cross-module dependencies

### Naming Conventions
- **Descriptive names**: `backup_manager.py` not `bm.py`
- **Action-oriented**: `validate_config()` not `config_check()`
- **Consistent patterns**: `_manager`, `_handler`, `_validator` suffixes

## Implementation Timeline

### Week 1: Foundation
- [ ] Set up test infrastructure
- [ ] Write tests for parent_directory_manager
- [ ] Refactor parent_directory_manager
- [ ] Validate all tests pass

### Week 2: Core Services  
- [ ] Test and refactor orchestrator modules
- [ ] Complete agent_registry implementation
- [ ] Integration testing

### Week 3: Extended Refactoring
- [ ] Continue with next 4 files from EP-0043
- [ ] Maintain test-first approach
- [ ] Update documentation

## Success Metrics

### Quantitative
- All files ≤ 500 lines (stretch goal)
- All files ≤ 600 lines (requirement)
- 100% test coverage for public methods
- No performance regression

### Qualitative  
- Improved code clarity
- Easier debugging
- Faster development
- Better team collaboration

## Risk Mitigation

### Testing First
- Write tests before refactoring
- Establish baseline behavior
- Catch regressions immediately

### Incremental Changes
- One module at a time
- Frequent test runs
- Git commits after each success

### Rollback Strategy
- Feature branch for all work
- Tag before each major change
- Easy revert if issues

## File-Specific Plans

### parent_directory_manager.py Breakdown

**Core Operations** (~500 lines):
- Main class definition
- Initialization
- Public API methods
- Core business logic

**Backup Manager** (~200 lines):
- Backup creation
- Restore operations
- Cleanup routines
- Validation

**Template Deployer** (~200 lines):
- Template reading
- Variable substitution
- Deployment logic
- Version checking

**Framework Protector** (~150 lines):
- Protection policies
- File monitoring
- Recovery procedures

## Next Steps

1. Create issue for Phase 2 implementation
2. Set up comprehensive test suite
3. Begin with parent_directory_manager
4. Track progress in EP-0043

## Notes

- This is a test-driven refactoring effort
- No functionality should be lost
- All APIs must remain compatible
- Performance must not degrade

---

**Phase**: 2 of 3  
**Target Completion**: 3 weeks  
**Risk Level**: Medium (mitigated by testing)