# Refactor backwards_compatible_orchestrator.py (1,961 lines)

**Issue ID**: ISS-0156  
**Epic**: EP-0043  
**Status**: open  
**Priority**: high  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 4 days  
**Tags**: refactoring, maintainability, high-priority

## Summary
Refactor the backwards_compatible_orchestrator.py to reduce its size from 1,961 lines to multiple focused modules, improving maintainability while preserving backward compatibility features.

## Current State
- **File**: `claude_pm/orchestration/backwards_compatible_orchestrator.py`
- **Current Size**: 1,961 lines
- **Complexity**: Manages orchestration with backward compatibility for:
  - Legacy agent interfaces
  - Multiple orchestration strategies
  - Task delegation patterns
  - Agent communication protocols
  - Version compatibility layers

## Proposed Refactoring

### Module Split Strategy
1. **orchestrator.py** (~400 lines)
   - Core orchestrator class
   - Public API maintenance
   - High-level coordination
   
2. **legacy_adapters.py** (~350 lines)
   - Legacy agent interface adapters
   - Version compatibility handlers
   - Backward compatibility shims
   
3. **delegation_strategies.py** (~400 lines)
   - Task delegation patterns
   - Agent selection strategies
   - Priority and routing logic
   
4. **agent_communication.py** (~300 lines)
   - Inter-agent communication protocols
   - Message formatting and parsing
   - Response handling
   
5. **task_context.py** (~250 lines)
   - Task context management
   - Context filtering for agents
   - Temporal context handling
   
6. **orchestration_utils.py** (~261 lines)
   - Helper functions
   - Common utilities
   - Validation logic

### Dependencies to Consider
- Central component for multi-agent coordination
- Used by PM agent for task delegation
- Integrates with agent registry
- Critical for Task Tool functionality

### Implementation Plan
1. **Phase 1**: Identify and document all public APIs
2. **Phase 2**: Create new module structure
3. **Phase 3**: Extract legacy compatibility code first
4. **Phase 4**: Migrate core orchestration logic
5. **Phase 5**: Update tests and validate compatibility

## Testing Requirements
- [ ] Unit tests for each module
- [ ] Integration tests for orchestration workflows
- [ ] Backward compatibility test suite
- [ ] Performance benchmarks
- [ ] End-to-end multi-agent coordination tests

## Acceptance Criteria
- [ ] No file exceeds 1000 lines
- [ ] All backward compatibility preserved
- [ ] Public APIs unchanged
- [ ] Test coverage maintained
- [ ] No performance degradation
- [ ] Clear separation of concerns

## Risk Assessment
- **High Risk**: Critical orchestration component
- **Mitigation**: Extensive compatibility testing, phased rollout

## Documentation Updates Required
- [ ] Document module responsibilities
- [ ] Update orchestration flow diagrams
- [ ] Create compatibility matrix
- [ ] Developer migration guide

## Notes
- Pay special attention to maintaining backward compatibility
- Consider deprecation warnings for legacy features
- Coordinate with teams using custom orchestration strategies