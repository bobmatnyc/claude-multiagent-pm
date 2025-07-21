# Refactor project_config_repository.py (1,139 lines)

**Issue ID**: ISS-0168  
**Epic**: EP-0043  
**Status**: open  
**Priority**: low  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 2 days  
**Tags**: refactoring, maintainability, low-priority

## Summary
Refactor project_config_repository.py to reduce its size from 1,139 lines to multiple focused modules, improving configuration management architecture.

## Current State
- **File**: `claude_pm/config/project_config_repository.py`
- **Current Size**: 1,139 lines
- **Complexity**: Manages project configuration:
  - Config storage and retrieval
  - Multi-project support
  - Configuration merging
  - Validation logic
  - Migration handling
  - Default management

## Proposed Refactoring

### Module Split Strategy
1. **project_config_repository.py** (~200 lines)
   - Core repository interface
   - Public API
   - Repository orchestration
   
2. **config_storage.py** (~200 lines)
   - Configuration persistence
   - File operations
   - Storage backend
   
3. **config_merger.py** (~200 lines)
   - Configuration merging logic
   - Precedence rules
   - Conflict resolution
   
4. **config_validator.py** (~200 lines)
   - Schema validation
   - Type checking
   - Constraint validation
   
5. **config_migrator.py** (~150 lines)
   - Version migration
   - Schema updates
   - Backward compatibility
   
6. **config_defaults.py** (~189 lines)
   - Default configurations
   - Template management
   - Initialization values

### Implementation Plan
1. **Day 1**: Extract storage and validation
2. **Day 2**: Separate merging and migration logic

## Testing Requirements
- [ ] Configuration CRUD tests
- [ ] Merge logic tests
- [ ] Validation edge cases
- [ ] Migration scenarios
- [ ] Multi-project tests

## Acceptance Criteria
- [ ] No file exceeds 1000 lines
- [ ] All config features work
- [ ] Migration paths preserved
- [ ] Validation comprehensive
- [ ] Performance maintained

## Risk Assessment
- **Medium Risk**: Configuration affects all components
- **Mitigation**: Backward compatibility testing

## Documentation Updates Required
- [ ] Configuration schema docs
- [ ] Migration guide
- [ ] Precedence rules
- [ ] Best practices guide

## Notes
- Critical for multi-project support
- Opportunity to improve validation
- Consider configuration hot-reload