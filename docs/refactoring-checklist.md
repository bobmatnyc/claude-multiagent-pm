# Claude Multi-Agent PM Framework - Engineer's Refactoring Checklist

**Version**: 1.0.0  
**Created**: 2025-07-18  
**Epic**: EP-0043  
**Purpose**: Step-by-step checklist for engineers refactoring large files

## Quick Reference

**Goal**: Reduce all files to ≤1000 lines while maintaining functionality and backward compatibility.

**Priority Order**:
1. Critical: >2000 lines
2. High: 1500-2000 lines  
3. Medium: 1200-1500 lines
4. Low: 1000-1200 lines

---

## Phase 1: Analysis and Planning (Day 1)

### 1.1 Initial Assessment
- [ ] Record current file metrics:
  - [ ] Line count: _______
  - [ ] Number of classes: _______
  - [ ] Number of methods: _______
  - [ ] Cyclomatic complexity: _______
  - [ ] Test coverage: _______

### 1.2 Dependency Analysis
- [ ] List all imports (internal and external)
- [ ] Identify circular dependencies
- [ ] Map out which modules depend on this file
- [ ] Document public API surface

### 1.3 Functional Analysis
- [ ] Identify distinct functional areas
- [ ] Group related methods and classes
- [ ] Note cross-cutting concerns
- [ ] Identify data models and structures

### 1.4 Create Refactoring Plan
- [ ] Define new module structure
- [ ] Assign line count targets per module
- [ ] Create module dependency diagram
- [ ] Get plan reviewed by team lead

---

## Phase 2: Test Preparation (Day 1-2)

### 2.1 Existing Test Analysis
- [ ] Run existing tests and record results
- [ ] Measure current test coverage
- [ ] Identify untested code paths
- [ ] Note any flaky or slow tests

### 2.2 Write Missing Tests
- [ ] Add tests for untested public methods
- [ ] Create integration tests for main workflows
- [ ] Add performance benchmarks
- [ ] Ensure all tests pass before refactoring

### 2.3 Create Refactoring Tests
- [ ] Write tests for new module interfaces
- [ ] Create backward compatibility tests
- [ ] Add module interaction tests
- [ ] Set up performance comparison tests

---

## Phase 3: Module Extraction (Day 2-3)

### 3.1 Create Module Structure
```bash
# Example structure
mkdir -p claude_pm/services/<original_name>/
touch claude_pm/services/<original_name>/__init__.py
```

- [ ] Create new package directory
- [ ] Create `__init__.py` with exports
- [ ] Create empty module files
- [ ] Set up imports between modules

### 3.2 Extract First Module
- [ ] Choose least dependent functionality
- [ ] Copy (don't move) code to new module
- [ ] Write module docstring
- [ ] Update imports within module
- [ ] Run module-specific tests

### 3.3 Create Facade Pattern
```python
# In original file (now facade)
from .<original_name>.module1 import Module1
from .<original_name>.module2 import Module2

class OriginalClass:
    def __init__(self):
        self._module1 = Module1()
        self._module2 = Module2()
    
    def original_method(self, *args, **kwargs):
        return self._module1.new_method(*args, **kwargs)
```

- [ ] Import new modules in original file
- [ ] Delegate methods to new modules
- [ ] Maintain exact same public API
- [ ] Test facade functionality

### 3.4 Iterate Module Extraction
- [ ] Extract remaining modules one by one
- [ ] Run tests after each extraction
- [ ] Update facade for each module
- [ ] Monitor file sizes stay under 1000 lines

---

## Phase 4: Integration and Testing (Day 3-4)

### 4.1 Update Imports Project-Wide
```bash
# Find all imports of the original module
grep -r "from.*<original_module> import" .
grep -r "import.*<original_module>" .
```

- [ ] Update internal imports if needed
- [ ] Ensure backward compatibility
- [ ] Fix any circular dependencies
- [ ] Run full test suite

### 4.2 Integration Testing
- [ ] Run all unit tests
- [ ] Run integration test suite
- [ ] Test main application workflows
- [ ] Verify CLI commands still work
- [ ] Check all agent interactions

### 4.3 Performance Validation
- [ ] Run performance benchmarks
- [ ] Compare with baseline metrics
- [ ] Profile critical operations
- [ ] Optimize if regression found

---

## Phase 5: Documentation (Day 4)

### 5.1 Code Documentation
- [ ] Update module docstrings
- [ ] Document new module structure
- [ ] Add usage examples
- [ ] Document any API changes

### 5.2 Architecture Documentation
- [ ] Update architecture diagrams
- [ ] Create module dependency graph
- [ ] Document design decisions
- [ ] Update developer guide

### 5.3 Migration Guide
- [ ] Document any breaking changes
- [ ] Provide migration examples
- [ ] List deprecated methods
- [ ] Include troubleshooting tips

---

## Phase 6: Review and Deployment (Day 4-5)

### 6.1 Code Review Preparation
- [ ] Self-review all changes
- [ ] Run linting and formatting
- [ ] Ensure all tests pass
- [ ] Check documentation completeness

### 6.2 Pull Request
- [ ] Create detailed PR description
- [ ] Link to refactoring issue
- [ ] Include before/after metrics
- [ ] Request reviews from team

### 6.3 Address Review Feedback
- [ ] Respond to all comments
- [ ] Make requested changes
- [ ] Re-run tests after changes
- [ ] Get final approval

### 6.4 Deployment Preparation
- [ ] Merge to development branch
- [ ] Run CI/CD pipeline
- [ ] Deploy to staging environment
- [ ] Perform smoke tests

---

## Common Gotchas and Solutions

### Circular Dependencies
**Problem**: Module A imports from Module B, which imports from Module A  
**Solution**: Extract shared functionality to a third module or use dependency injection

### Breaking Backward Compatibility
**Problem**: Existing code breaks after refactoring  
**Solution**: Always use facade pattern, maintain exact same public API

### Performance Regression
**Problem**: Refactored code runs slower  
**Solution**: Profile to find bottleneck, consider caching or optimization

### Test Coverage Drop
**Problem**: Coverage decreases after refactoring  
**Solution**: Write tests for new module boundaries and internal APIs

### Import Path Confusion
**Problem**: Confusion between old and new import paths  
**Solution**: Clear documentation, consider deprecation warnings

---

## File-Specific Tips

### For Manager/Service Classes (>2000 lines)
1. Extract by responsibility (CRUD operations, validation, business logic)
2. Create separate handler classes for different operations
3. Use strategy pattern for algorithm variations

### For Registry/Repository Classes
1. Separate discovery from storage
2. Extract caching to dedicated module
3. Split query building from execution

### For Async/Sync Duplicates
1. Choose one implementation (prefer sync for simplicity)
2. Remove the other completely
3. Update all imports project-wide

### For Utility Collections
1. Group by functionality
2. Create focused utility modules
3. Consider promoting to service if complex

---

## Success Metrics

### Must Have
- [ ] All files ≤1000 lines
- [ ] All tests passing
- [ ] No public API changes
- [ ] Performance within 5% of baseline

### Should Have
- [ ] Improved test coverage
- [ ] Better module cohesion
- [ ] Clearer separation of concerns
- [ ] Updated documentation

### Nice to Have
- [ ] Performance improvements
- [ ] Additional test scenarios
- [ ] Refined module interfaces
- [ ] Example usage code

---

## Emergency Procedures

### If Tests Start Failing
1. Stop and investigate immediately
2. Check for missing imports
3. Verify facade delegation is correct
4. Consider rolling back last change

### If Performance Degrades
1. Profile the specific operation
2. Check for unnecessary object creation
3. Verify caching still works
4. Consider keeping some methods together

### If Circular Dependencies Arise
1. Map out the dependency cycle
2. Extract shared code to new module
3. Use interfaces/protocols
4. Consider dependency injection

### If File Still Too Large
1. Re-evaluate module boundaries
2. Look for hidden responsibilities
3. Consider extracting data models
4. Split complex methods

---

## Final Verification

Before marking complete:
- [ ] Original file is now ≤1000 lines
- [ ] All extracted modules are ≤1000 lines  
- [ ] Full test suite passes
- [ ] Performance benchmarks pass
- [ ] Documentation is complete
- [ ] PR is approved and merged

## Notes Section

Use this space to track specific challenges and solutions for your refactoring:

```
File: _______________________
Date Started: _______________
Date Completed: _____________

Challenges:
1. 
2. 
3. 

Solutions:
1. 
2. 
3. 

Lessons Learned:


```

---

Remember: Take it slow, test thoroughly, and maintain backward compatibility. Good refactoring takes time but pays dividends in maintainability!