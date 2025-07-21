# Refactor agent_registry.py and Consolidate with Sync Version

**Issue ID**: ISS-0155  
**Epic**: EP-0043  
**Status**: open  
**Priority**: critical  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 5 days  
**Tags**: refactoring, maintainability, critical-priority, consolidation

## Summary
Refactor and consolidate the agent registry system by removing the async version (agent_registry.py, 2,151 lines) and enhancing the sync version (agent_registry_sync.py, 1,574 lines) to be the single source of truth, then split into manageable modules.

## Current State
- **Async File**: `claude_pm/core/agent_registry.py` - 2,151 lines (TO BE REMOVED)
- **Sync File**: `claude_pm/core/agent_registry_sync.py` - 1,574 lines (TO BE KEPT AND REFACTORED)
- **Duplication**: Significant code duplication between async and sync versions
- **Complexity**: Handles agent discovery, loading, caching, and management

## Proposed Refactoring

### Phase 1: Consolidation
1. **Remove async version** entirely
2. **Rename sync version** to `agent_registry.py`
3. **Update all imports** throughout the codebase
4. **Ensure no async dependencies** remain

### Phase 2: Module Split Strategy
1. **agent_registry.py** (~400 lines)
   - Core AgentRegistry class with public API
   - High-level orchestration and facade
   
2. **agent_discovery.py** (~350 lines)
   - Directory scanning for agents
   - Hierarchy management (project → user → system)
   - Agent metadata extraction
   
3. **agent_loader.py** (~300 lines)
   - Agent file loading and parsing
   - Dynamic agent instantiation
   - Agent validation
   
4. **agent_cache.py** (~250 lines)
   - Caching mechanisms
   - Performance optimization
   - Cache invalidation logic
   
5. **agent_metadata.py** (~200 lines)
   - Metadata models and schemas
   - Specialization management
   - Agent capability tracking
   
6. **agent_selector.py** (~200 lines)
   - Optimal agent selection algorithms
   - Task matching logic
   - Precedence resolution

### Dependencies to Consider
- Core component used by orchestrator
- Critical for Task Tool subprocess creation
- Integrated with SharedPromptCache
- Referenced by all agent systems

### Implementation Plan
1. **Day 1**: Remove async version, update imports
2. **Day 2**: Create module structure and interfaces
3. **Day 3**: Extract and migrate functionality
4. **Day 4**: Update tests and documentation
5. **Day 5**: Performance testing and optimization

## Testing Requirements
- [ ] Verify all async code removed successfully
- [ ] Unit tests for each new module
- [ ] Integration tests for consolidated registry
- [ ] Performance tests (99.7% cache performance maintained)
- [ ] Regression tests for agent discovery and loading
- [ ] End-to-end tests for Task Tool integration

## Acceptance Criteria
- [ ] Only one agent registry implementation exists
- [ ] No file exceeds 1000 lines
- [ ] All agent discovery functionality preserved
- [ ] Performance metrics maintained or improved
- [ ] Zero async dependencies
- [ ] Documentation updated

## Risk Assessment
- **Medium Risk**: Core system component but with good test coverage
- **Mitigation**: Incremental migration, comprehensive testing

## Documentation Updates Required
- [ ] Remove all references to async registry
- [ ] Update architecture diagrams
- [ ] Document consolidation decision
- [ ] Update API documentation

## Notes
- This consolidation will simplify the codebase significantly
- Removing async reduces complexity without losing functionality
- Consider creating migration script for any cached data