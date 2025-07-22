# Refactor directory_utils.py (1,070 lines)

**Issue ID**: ISS-0169  
**Epic**: EP-0043  
**Status**: open  
**Priority**: low  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 2 days  
**Tags**: refactoring, maintainability, low-priority

## Summary
Refactor directory_utils.py to reduce its size from 1,070 lines to multiple focused modules, improving directory operation utilities.

## Current State
- **File**: `claude_pm/utils/directory_utils.py`
- **Current Size**: 1,070 lines
- **Complexity**: Comprehensive directory utilities:
  - Path manipulation
  - Directory traversal
  - File operations
  - Permission handling
  - Pattern matching
  - Directory watching

## Proposed Refactoring

### Module Split Strategy
1. **directory_utils.py** (~150 lines)
   - Core utilities interface
   - Public API
   - Common operations
   
2. **path_utils.py** (~200 lines)
   - Path manipulation
   - Path normalization
   - Path validation
   
3. **directory_traversal.py** (~200 lines)
   - Directory walking
   - Recursive operations
   - Filter application
   
4. **file_operations.py** (~200 lines)
   - File CRUD operations
   - Atomic operations
   - Batch processing
   
5. **permission_handler.py** (~150 lines)
   - Permission checking
   - Permission modification
   - Platform compatibility
   
6. **pattern_matcher.py** (~170 lines)
   - Glob pattern matching
   - Regex matching
   - Exclusion rules

### Implementation Plan
1. **Day 1**: Extract path and traversal utilities
2. **Day 2**: Separate file operations and permissions

## Testing Requirements
- [ ] Path manipulation tests
- [ ] Directory traversal tests
- [ ] Permission tests (multi-platform)
- [ ] Pattern matching tests
- [ ] Edge case handling

## Acceptance Criteria
- [ ] No file exceeds 1000 lines
- [ ] All utilities functional
- [ ] Platform compatibility
- [ ] Performance maintained
- [ ] Clear API boundaries

## Risk Assessment
- **Low Risk**: Well-tested utility functions
- **Mitigation**: Comprehensive test coverage

## Documentation Updates Required
- [ ] Utility function reference
- [ ] Platform compatibility notes
- [ ] Pattern syntax guide
- [ ] Best practices

## Notes
- Foundation utilities used everywhere
- Ensure cross-platform compatibility
- Consider adding async variants