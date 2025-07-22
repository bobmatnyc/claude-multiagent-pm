# Refactor agent_registry_sync.py (1,574 lines)

**Issue ID**: ISS-0157  
**Epic**: EP-0043  
**Status**: blocked  
**Priority**: high  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 3 days  
**Tags**: refactoring, maintainability, high-priority

## Summary
Refactor agent_registry_sync.py as part of the consolidation effort, splitting it into manageable modules after it becomes the primary agent registry implementation.

## Current State
- **File**: `claude_pm/core/agent_registry_sync.py`
- **Current Size**: 1,574 lines
- **Note**: This file will be renamed to `agent_registry.py` after ISS-0155 is complete
- **Status**: BLOCKED by ISS-0155 (consolidation must happen first)

## Proposed Refactoring

### Module Split Strategy
*See ISS-0155 for the complete refactoring plan, as this file will be the base for the consolidated agent registry*

The refactoring will create:
1. Core registry module (~400 lines)
2. Discovery module (~350 lines)
3. Loading module (~300 lines)
4. Caching module (~250 lines)
5. Metadata module (~200 lines)
6. Selection module (~200 lines)

### Dependencies
- **Blocking Issue**: ISS-0155 must be completed first
- This issue may be closed as duplicate if ISS-0155 handles the full refactoring

### Implementation Plan
If ISS-0155 only handles consolidation:
1. **Day 1**: Review consolidated code structure
2. **Day 2**: Implement module separation
3. **Day 3**: Testing and validation

## Testing Requirements
- Covered by ISS-0155 test plan

## Acceptance Criteria
- Covered by ISS-0155 acceptance criteria

## Risk Assessment
- **Low Risk**: Work will be done on already consolidated code
- **Mitigation**: Ensure ISS-0155 is thoroughly tested first

## Documentation Updates Required
- Covered by ISS-0155 documentation plan

## Notes
- This ticket exists for tracking purposes but may be merged with ISS-0155
- If ISS-0155 completes the full refactoring, this ticket should be closed as duplicate
- Keep this ticket updated based on ISS-0155 progress