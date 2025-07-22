# Refactor parent_directory_manager.py (2,620 lines)

**Issue ID**: ISS-0154  
**Epic**: EP-0043  
**Status**: open  
**Priority**: critical  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 1 week  
**Tags**: refactoring, maintainability, critical-priority

## Summary
Refactor the parent_directory_manager.py service to reduce its size from 2,620 lines to multiple modules of ~1000 lines or less, improving maintainability and testability.

## Current State
- **File**: `claude_pm/services/parent_directory_manager.py`
- **Current Size**: 2,620 lines
- **Complexity**: Handles multiple responsibilities including:
  - Directory scanning and management
  - Framework template deployment
  - Configuration management
  - Backup and recovery operations
  - Health monitoring
  - Version management
  - System initialization

## Proposed Refactoring

### Module Split Strategy
1. **parent_directory_manager.py** (~500 lines)
   - Core ParentDirectoryManager class with high-level orchestration
   - Public API maintained for backward compatibility
   
2. **directory_scanner.py** (~400 lines)
   - Directory traversal and scanning logic
   - Parent directory detection
   - Path validation and normalization
   
3. **template_deployment.py** (~600 lines)
   - Framework template deployment
   - Template validation and processing
   - Version comparison logic
   - Handlebars variable substitution
   
4. **backup_manager.py** (~400 lines)
   - Backup creation and rotation
   - Recovery operations
   - Backup validation
   
5. **config_manager.py** (~300 lines)
   - Configuration file management
   - Settings persistence
   - Configuration validation
   
6. **health_validator.py** (~300 lines)
   - Health check operations
   - System validation
   - Diagnostic reporting
   
7. **system_initializer.py** (~120 lines)
   - System initialization logic
   - Directory structure creation

### Dependencies to Consider
- Used by CLI module for framework deployment
- Critical for `claude-pm init` functionality
- Integrated with health monitoring system
- Referenced by multiple agent systems

### Implementation Plan
1. **Phase 1**: Create new module structure with interfaces
2. **Phase 2**: Extract and migrate functionality module by module
3. **Phase 3**: Update original class to use new modules (facade pattern)
4. **Phase 4**: Comprehensive testing of refactored system
5. **Phase 5**: Performance validation and optimization

## Testing Requirements
- [ ] Unit tests for each new module (100% coverage target)
- [ ] Integration tests for ParentDirectoryManager facade
- [ ] Regression tests for all existing functionality
- [ ] Performance benchmarks (should not degrade)
- [ ] End-to-end tests for `claude-pm init` workflow

## Acceptance Criteria
- [ ] No file exceeds 1000 lines
- [ ] All existing functionality preserved
- [ ] Public API unchanged (backward compatibility)
- [ ] Test coverage ≥ current level
- [ ] Documentation updated for new structure
- [ ] No performance regression

## Risk Assessment
- **High Risk**: Core framework component - errors could break deployments
- **Mitigation**: Extensive testing, feature flags, gradual rollout

## Documentation Updates Required
- [ ] Update architecture documentation
- [ ] Create module dependency diagram
- [ ] Document new internal APIs
- [ ] Update developer guide

## Notes
- This is the largest file in the codebase and most critical to refactor
- Consider creating ADR (Architecture Decision Record) for the refactoring approach
- Coordinate with DevOps team for deployment strategy