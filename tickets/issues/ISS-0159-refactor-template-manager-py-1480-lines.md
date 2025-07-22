# Refactor template_manager.py (1,480 lines)

**Issue ID**: ISS-0159  
**Epic**: EP-0043  
**Status**: open  
**Priority**: medium  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 3 days  
**Tags**: refactoring, maintainability, medium-priority

## Summary
Refactor the template_manager.py to reduce its size from 1,480 lines to multiple focused modules, improving template handling and processing capabilities.

## Current State
- **File**: `claude_pm/services/template_manager.py`
- **Current Size**: 1,480 lines
- **Complexity**: Manages various template operations:
  - Template loading and caching
  - Variable substitution (Handlebars)
  - Conditional processing
  - Template validation
  - Include file handling
  - Template rendering

## Proposed Refactoring

### Module Split Strategy
1. **template_manager.py** (~300 lines)
   - Core TemplateManager class
   - Public API maintenance
   - Template orchestration
   
2. **template_loader.py** (~250 lines)
   - Template file discovery
   - Template loading from disk
   - Template caching logic
   
3. **template_processor.py** (~350 lines)
   - Handlebars variable substitution
   - Conditional logic processing
   - Include file resolution
   
4. **template_validator.py** (~200 lines)
   - Template syntax validation
   - Variable reference checking
   - Structure validation
   
5. **template_renderer.py** (~250 lines)
   - Final template rendering
   - Output formatting
   - Post-processing hooks
   
6. **template_cache.py** (~130 lines)
   - Template caching implementation
   - Cache invalidation
   - Performance optimization

### Dependencies to Consider
- Used for framework template deployment
- Critical for CLAUDE.md processing
- Integrated with configuration system
- Used by multiple agent systems

### Implementation Plan
1. **Phase 1**: Extract template loading logic
2. **Phase 2**: Separate processing engine
3. **Phase 3**: Modularize validation
4. **Phase 4**: Implement rendering pipeline
5. **Phase 5**: Performance optimization

## Testing Requirements
- [ ] Unit tests for each module
- [ ] Template processing regression tests
- [ ] Performance benchmarks
- [ ] Edge case handling tests
- [ ] Integration tests with framework

## Acceptance Criteria
- [ ] No file exceeds 1000 lines
- [ ] All template features preserved
- [ ] No performance regression
- [ ] Backward compatibility maintained
- [ ] Enhanced error messages
- [ ] Clear module boundaries

## Risk Assessment
- **Medium Risk**: Templates are critical for framework operation
- **Mitigation**: Comprehensive test coverage, staged rollout

## Documentation Updates Required
- [ ] Template syntax guide
- [ ] Processing pipeline documentation
- [ ] Module API documentation
- [ ] Template best practices

## Notes
- Opportunity to improve template error messages
- Consider adding template debugging features
- Evaluate template security during refactoring