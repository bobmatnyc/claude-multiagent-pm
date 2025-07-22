# Refactor agent_loader.py (1,174 lines)

**Issue ID**: ISS-0164  
**Epic**: EP-0043  
**Status**: open  
**Priority**: low  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 2 days  
**Tags**: refactoring, maintainability, low-priority

## Summary
Refactor agent_loader.py to reduce its size from 1,174 lines to multiple focused modules, improving agent loading and management architecture.

## Current State
- **File**: `claude_pm/agents/agent_loader.py`
- **Current Size**: 1,174 lines
- **Complexity**: Handles agent loading operations:
  - Agent discovery
  - Dynamic loading
  - Agent validation
  - Hierarchy management
  - Cache management
  - Error handling

## Proposed Refactoring

### Module Split Strategy
1. **agent_loader.py** (~200 lines)
   - Core AgentLoader class
   - Public API
   - Loading orchestration
   
2. **agent_discovery.py** (~200 lines)
   - File system scanning
   - Agent detection
   - Path resolution
   
3. **dynamic_loader.py** (~250 lines)
   - Dynamic import logic
   - Module loading
   - Class instantiation
   
4. **agent_validator.py** (~200 lines)
   - Agent contract validation
   - Interface checking
   - Capability verification
   
5. **hierarchy_manager.py** (~150 lines)
   - Three-tier hierarchy logic
   - Precedence resolution
   - Override handling
   
6. **loader_cache.py** (~174 lines)
   - Agent caching
   - Cache invalidation
   - Performance optimization

### Implementation Plan
1. **Day 1**: Extract discovery and validation
2. **Day 2**: Separate loading and caching logic

## Testing Requirements
- [ ] Unit tests for each module
- [ ] Agent loading scenarios
- [ ] Hierarchy precedence tests
- [ ] Cache effectiveness tests
- [ ] Error handling validation

## Acceptance Criteria
- [ ] No file exceeds 1000 lines
- [ ] Loading performance maintained
- [ ] Hierarchy rules preserved
- [ ] Enhanced error messages
- [ ] Clear module separation

## Risk Assessment
- **Medium Risk**: Agent loading is critical functionality
- **Mitigation**: Parallel testing, gradual migration

## Documentation Updates Required
- [ ] Agent loading sequence
- [ ] Hierarchy documentation
- [ ] Cache strategy guide
- [ ] Troubleshooting guide

## Notes
- Coordinate with agent registry refactoring
- Opportunity to improve loading performance
- Consider lazy loading strategies