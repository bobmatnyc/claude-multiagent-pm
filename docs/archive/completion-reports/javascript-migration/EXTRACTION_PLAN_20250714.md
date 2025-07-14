# Claude PM CLI Module Extraction Plan

**ISS-0085**: Modularize claude-pm script from monolithic 3,048-line file  
**Phase 1 Status**: Infrastructure Complete  
**Date**: 2025-07-13

## Current Status: Phase 1 Complete ✅

### Phase 1 Achievements
- ✅ **Module Infrastructure**: Created `lib/cli-modules/` with complete loading system
- ✅ **Module Loader**: Implemented dynamic loading with fallback support (`module-loader.js`)
- ✅ **Core Modules Extracted**: 3 Phase 1 modules implemented
  - ✅ `version-resolver.js` (Lines 17-102 extracted)
  - ✅ `environment-validator.js` (Environment validation logic extracted)
  - ✅ `display-manager.js` (UI/display logic extracted)
- ✅ **Test Framework**: Comprehensive testing infrastructure (`test-framework.js`)
- ✅ **Documentation**: Complete README and architecture documentation

### Phase 1 Module Statistics
| Module | Lines Extracted | Risk Level | Memory Impact | Status |
|--------|----------------|------------|---------------|---------|
| version-resolver | ~85 lines | Low | <50KB | ✅ Complete |
| environment-validator | ~150 lines | Low | <100KB | ✅ Complete |
| display-manager | ~200 lines | Low | <75KB | ✅ Complete |
| **Total Phase 1** | **~435 lines** | **Low** | **<225KB** | **✅ Complete** |

## Phase 2 Plan: Secondary Modules (Weeks 4-6)

### Target Modules for Phase 2
1. **deployment-detector.js** (~536 lines, Lines 110-649)
   - **Risk Level**: Medium-High (core functionality)
   - **Description**: Extract DeploymentDetector class and related logic
   - **Dependencies**: version-resolver, environment-validator
   - **Memory Target**: <400KB

2. **framework-manager.js** (~540 lines)
   - **Risk Level**: High (framework initialization)
   - **Description**: Framework initialization and management logic
   - **Dependencies**: deployment-detector, configuration-manager
   - **Memory Target**: <450KB

3. **command-dispatcher.js** (~400 lines)
   - **Risk Level**: Medium (command routing)
   - **Description**: Main function command parsing and routing
   - **Dependencies**: All other modules
   - **Memory Target**: <300KB

### Phase 2 Extraction Strategy

#### 1. deployment-detector.js (Week 4)
**Source Lines**: 110-649 from bin/claude-pm
```javascript
// Extract DeploymentDetector class:
class DeploymentDetector {
    constructor() { /* ... */ }
    detectDeployment() { /* ... */ }
    _performDetection() { /* ... */ }
    // + all helper methods
}
```

**Integration Points**:
- Uses version-resolver for version information
- Integrates with environment-validator for platform detection
- Provides deployment config to framework-manager

#### 2. framework-manager.js (Week 5)
**Source Lines**: Framework initialization logic from main()
```javascript
// Extract framework management:
- getFrameworkPath()
- getDeploymentConfig()
- Framework service initialization
- Memory management setup
```

**Integration Points**:
- Depends on deployment-detector for environment info
- Uses configuration-manager for settings
- Coordinates with command-dispatcher for execution

#### 3. command-dispatcher.js (Week 6)
**Source Lines**: Main function command parsing (Lines 1714-2341)
```javascript
// Extract command routing:
- Argument parsing
- Command flag handling
- Route to appropriate handlers
- Memory monitoring setup
```

**Integration Points**:
- Uses all other modules as dependencies
- Central coordination point
- Implements fallback mechanisms

## Phase 3 Plan: Complex Modules (Weeks 7-8)

### Target Modules for Phase 3
1. **configuration-manager.js** (~250 lines)
2. **template-system.js** (~300 lines)
3. **error-handler.js** (~200 lines)
4. **utilities.js** (~322 lines)

## Detailed Implementation Steps

### Step 1: Pre-Phase 2 Preparation
1. **Create Phase 2 test cases**
   ```bash
   mkdir -p tests/phase2
   ```

2. **Set up performance benchmarks**
   - Baseline memory usage measurement
   - Loading time benchmarks
   - Integration test scenarios

3. **Backup current state**
   ```bash
   cp bin/claude-pm bin/claude-pm.backup-phase1-complete
   ```

### Step 2: deployment-detector.js Extraction

#### 2.1 Identify Extraction Boundaries
- **Start**: Line 110 (`class DeploymentDetector`)
- **End**: Line 649 (end of class and related functions)
- **Dependencies**: File system operations, path utilities

#### 2.2 Create Module Structure
```javascript
// deployment-detector.js structure:
class DeploymentDetector {
    // All existing methods
}

module.exports = {
    main: (options) => new DeploymentDetector().detectDeployment(options),
    config: { /* module config */ },
    dependencies: ['version-resolver', 'environment-validator'],
    DeploymentDetector: DeploymentDetector  // Export class
};
```

#### 2.3 Integration Testing
- Test deployment detection across all scenarios
- Validate memory usage under 400KB
- Test integration with Phase 1 modules

### Step 3: framework-manager.js Extraction

#### 3.1 Extract Framework Functions
```javascript
// Functions to extract:
- getFrameworkPath() (Line 650)
- getDeploymentConfig() (Line 670)
- Framework initialization logic from main()
```

#### 3.2 Memory Management Integration
- Implement cleanup protocols
- Add memory monitoring
- Integrate with module loader

### Step 4: command-dispatcher.js Extraction

#### 4.1 Extract Main Function Logic
```javascript
// Extract from main() function (Lines 1714-2341):
- Argument parsing
- Flag handling
- Command routing
- Error handling
```

#### 4.2 Integration Layer
- Create unified interface for all modules
- Implement fallback mechanisms
- Add comprehensive error handling

## Success Criteria for Phase 2

### Functional Requirements
- [ ] All existing CLI functionality preserved
- [ ] No breaking changes to user interface
- [ ] All deployment scenarios continue working
- [ ] Memory usage reduced by additional 15% (total 30%)

### Performance Requirements
- [ ] Module loading time under 50ms each
- [ ] Total memory impact under 1.2MB (all modules)
- [ ] CLI response time maintained or improved
- [ ] Startup time under 2 seconds

### Quality Requirements
- [ ] Each module under 600 lines
- [ ] 90%+ test coverage maintained
- [ ] No circular dependencies
- [ ] Comprehensive error handling

## Risk Mitigation Strategy

### High-Risk Module Handling
1. **deployment-detector.js**
   - **Risk**: Core deployment logic affects all scenarios
   - **Mitigation**: Extensive testing across all deployment types
   - **Fallback**: Feature flag to revert to monolithic detection

2. **framework-manager.js**
   - **Risk**: Framework initialization is critical
   - **Mitigation**: Gradual extraction with validation at each step
   - **Fallback**: Maintain initialization in main script until validated

### Testing Strategy
- **Unit Tests**: Individual module testing
- **Integration Tests**: Module interaction validation
- **Scenario Tests**: Real-world deployment scenario validation
- **Performance Tests**: Memory and speed regression testing

### Rollback Procedures
1. **Immediate Rollback**: Feature flags to disable modular loading
2. **Module-Level Rollback**: Individual module fallback to monolithic
3. **Complete Rollback**: Restore from `claude-pm.backup-phase1-complete`

## Timeline Checkpoints

### Week 4 Checkpoint (End of deployment-detector.js)
- [ ] Module extracted and tested
- [ ] Integration tests passing
- [ ] Memory usage under target
- [ ] No regression in functionality

### Week 5 Checkpoint (End of framework-manager.js)
- [ ] Framework initialization modularized
- [ ] Cross-module communication working
- [ ] Performance benchmarks met
- [ ] User experience unchanged

### Week 6 Checkpoint (End of Phase 2)
- [ ] Command dispatching modularized
- [ ] All Phase 2 modules integrated
- [ ] 90%+ test coverage achieved
- [ ] Ready for Phase 3 planning

## Next Actions (Ready for Implementation)

1. **Immediate** (This Week):
   - Create detailed deployment-detector.js extraction specification
   - Set up Phase 2 testing infrastructure
   - Begin deployment-detector.js implementation

2. **Week 4** (deployment-detector.js):
   - Extract DeploymentDetector class
   - Implement module interface
   - Complete integration testing

3. **Week 5** (framework-manager.js):
   - Extract framework management functions
   - Implement cross-module coordination
   - Validate memory management

4. **Week 6** (command-dispatcher.js):
   - Extract main function logic
   - Complete Phase 2 integration
   - Performance optimization

---

**Status**: Phase 1 Complete ✅ - Ready for Phase 2 Implementation  
**Next**: Begin deployment-detector.js extraction (Week 4)  
**Overall Progress**: 435/3048 lines modularized (14.3%)