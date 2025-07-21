# Claude Multi-Agent PM Framework File Size Refactoring Guidelines

**Version**: 1.0.0  
**Created**: 2025-07-18  
**Epic**: EP-0043  
**Purpose**: Comprehensive guidelines for refactoring files to ~1000 lines or less

## Table of Contents
1. [Core Principles](#core-principles)
2. [File Size Standards](#file-size-standards)
3. [Module Splitting Strategies](#module-splitting-strategies)
4. [Naming Conventions](#naming-conventions)
5. [Import/Export Patterns](#importexport-patterns)
6. [Testing Requirements](#testing-requirements)
7. [Documentation Standards](#documentation-standards)
8. [Common Refactoring Patterns](#common-refactoring-patterns)
9. [Refactoring Checklist](#refactoring-checklist)
10. [Risk Mitigation](#risk-mitigation)

## Core Principles

### 1. Single Responsibility Principle
Each module should have one clear, focused responsibility. If a module handles multiple unrelated concerns, it should be split.

### 2. Maintain Backward Compatibility
All refactoring must preserve existing public APIs. Use the facade pattern to maintain compatibility while reorganizing internals.

### 3. Progressive Refactoring
Refactor incrementally, one module at a time, with comprehensive testing between each step.

### 4. Test-Driven Refactoring
Write tests for the new structure before moving code. Ensure all tests pass before and after refactoring.

## File Size Standards

### Target Sizes
- **Optimal**: 500-800 lines per file
- **Maximum**: 1000 lines per file
- **Minimum**: 100 lines per file (avoid over-fragmentation)

### When to Split
1. **Hard Limit**: Any file over 1000 lines must be split
2. **Recommended Split**: Files over 800 lines should be evaluated for splitting
3. **Complexity-Based**: High cyclomatic complexity warrants splitting regardless of size

### Size Categories and Priorities
- **Critical (>2000 lines)**: Immediate refactoring required
- **High (1500-2000 lines)**: Priority refactoring within 2 weeks
- **Medium (1200-1500 lines)**: Scheduled refactoring within 4 weeks
- **Low (1000-1200 lines)**: Refactor as part of regular maintenance

## Module Splitting Strategies

### 1. Functional Decomposition Pattern
Split based on distinct functional areas:
```python
# Before: parent_directory_manager.py (2,620 lines)
class ParentDirectoryManager:
    def scan_directories(self): ...
    def deploy_templates(self): ...
    def backup_files(self): ...
    def validate_health(self): ...

# After: Multiple focused modules
# parent_directory_manager.py (facade)
# directory_scanner.py
# template_deployment.py
# backup_manager.py
# health_validator.py
```

### 2. Layer Separation Pattern
Split by architectural layers:
```python
# Before: agent_registry.py (2,151 lines)
class AgentRegistry:
    def discover_agents(self): ...
    def load_agents(self): ...
    def cache_agents(self): ...
    def select_agents(self): ...

# After: Layer-based modules
# agent_registry.py (API layer)
# agent_discovery.py (discovery layer)
# agent_loader.py (data layer)
# agent_cache.py (cache layer)
# agent_selector.py (business logic layer)
```

### 3. Concern Separation Pattern
Split by cross-cutting concerns:
```python
# Before: continuous_learning_engine.py (1,335 lines)
class ContinuousLearningEngine:
    def collect_feedback(self): ...
    def analyze_patterns(self): ...
    def adapt_models(self): ...
    def track_metrics(self): ...

# After: Concern-based modules
# learning_engine.py (orchestration)
# feedback_collector.py (data collection)
# pattern_analyzer.py (analysis)
# model_adapter.py (adaptation)
# metrics_tracker.py (monitoring)
```

## Naming Conventions

### Module Names
1. **Descriptive**: Use clear, descriptive names that indicate purpose
2. **Consistent**: Follow existing project patterns
3. **Suffix Pattern**: Use appropriate suffixes:
   - `_manager.py` for management modules
   - `_service.py` for service modules
   - `_handler.py` for request/event handlers
   - `_utils.py` for utility collections
   - `_models.py` for data models
   - `_validators.py` for validation logic

### Class Names
- Keep original class names in facade modules for compatibility
- Use specific names in internal modules (e.g., `DirectoryScanner`, not `Scanner`)

### Import Names
```python
# Maintain compatibility with facade pattern
from claude_pm.services.parent_directory_manager import ParentDirectoryManager

# Internal imports use specific modules
from claude_pm.services.parent_directory.directory_scanner import DirectoryScanner
```

## Import/Export Patterns

### Facade Pattern for Backward Compatibility
```python
# parent_directory_manager.py (facade module)
from .parent_directory.directory_scanner import DirectoryScanner
from .parent_directory.template_deployment import TemplateDeployer
from .parent_directory.backup_manager import BackupManager

class ParentDirectoryManager:
    """Facade maintaining backward compatibility."""
    def __init__(self):
        self._scanner = DirectoryScanner()
        self._deployer = TemplateDeployer()
        self._backup = BackupManager()
    
    # Delegate to internal modules
    def scan_directories(self, *args, **kwargs):
        return self._scanner.scan(*args, **kwargs)
```

### Module Organization
```
claude_pm/
├── services/
│   ├── parent_directory_manager.py  # Facade (backward compatibility)
│   └── parent_directory/
│       ├── __init__.py
│       ├── directory_scanner.py
│       ├── template_deployment.py
│       ├── backup_manager.py
│       ├── config_manager.py
│       ├── health_validator.py
│       └── system_initializer.py
```

### Export Management
```python
# parent_directory/__init__.py
from .directory_scanner import DirectoryScanner
from .template_deployment import TemplateDeployer
from .backup_manager import BackupManager

__all__ = [
    'DirectoryScanner',
    'TemplateDeployer', 
    'BackupManager',
]
```

## Testing Requirements

### Test Structure
```
tests/
├── unit/
│   └── services/
│       └── parent_directory/
│           ├── test_directory_scanner.py
│           ├── test_template_deployment.py
│           ├── test_backup_manager.py
│           └── test_facade_compatibility.py
└── integration/
    └── test_parent_directory_integration.py
```

### Testing Standards
1. **Unit Tests**: Each new module requires comprehensive unit tests
2. **Integration Tests**: Test module interactions
3. **Facade Tests**: Ensure backward compatibility
4. **Performance Tests**: Verify no performance regression
5. **Coverage Target**: Maintain or improve existing coverage (minimum 80%)

### Test Template
```python
# test_<module_name>.py
import pytest
from unittest.mock import Mock, patch

class Test<ModuleName>:
    """Test suite for <ModuleName> module."""
    
    def test_public_api_compatibility(self):
        """Ensure public API remains unchanged."""
        # Test backward compatibility
    
    def test_core_functionality(self):
        """Test core module functionality."""
        # Test new module behavior
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test error scenarios
    
    def test_performance(self):
        """Ensure performance requirements met."""
        # Benchmark critical operations
```

## Documentation Standards

### Module Documentation
```python
"""
Module Name - Brief Description
================================

This module handles [specific responsibility] as part of the 
[parent system] refactoring (EP-0043).

Key Responsibilities:
- Responsibility 1
- Responsibility 2
- Responsibility 3

Dependencies:
- Internal: List internal dependencies
- External: List external dependencies

Usage:
    from claude_pm.services.module_name import ClassName
    
    instance = ClassName()
    result = instance.method()

Note:
    This module was extracted from [original_file.py] as part
    of the file size reduction initiative (EP-0043).
"""
```

### API Documentation
- Document all public methods with docstrings
- Include parameter types and return values
- Provide usage examples for complex methods

### Architecture Documentation
- Create/update architecture diagrams showing module relationships
- Document data flow between modules
- Maintain module dependency graph

## Common Refactoring Patterns

### Pattern 1: Extract Service Objects
```python
# Before: Single large class
class LargeService:
    def operation_a(self): 
        # 200 lines of code
    def operation_b(self):
        # 300 lines of code

# After: Extracted service objects
class LargeService:
    def __init__(self):
        self._service_a = ServiceA()
        self._service_b = ServiceB()
    
    def operation_a(self):
        return self._service_a.execute()
```

### Pattern 2: Extract Data Models
```python
# Before: Inline data structures
class ServiceClass:
    def process(self):
        data = {
            'field1': value1,
            'field2': value2,
            # 50 more fields
        }

# After: Extracted models
from .models import DataModel

class ServiceClass:
    def process(self):
        data = DataModel(field1=value1, field2=value2)
```

### Pattern 3: Extract Validators
```python
# Before: Inline validation
class ServiceClass:
    def process(self, data):
        if not data.get('field1'):
            raise ValueError()
        # 100 lines of validation

# After: Extracted validator
from .validators import DataValidator

class ServiceClass:
    def __init__(self):
        self._validator = DataValidator()
    
    def process(self, data):
        self._validator.validate(data)
```

## Refactoring Checklist

### Pre-Refactoring
- [ ] Analyze file structure and identify logical boundaries
- [ ] Document current public API
- [ ] Write comprehensive tests for existing functionality
- [ ] Create refactoring plan with module breakdown
- [ ] Get team review of refactoring plan

### During Refactoring
- [ ] Create new module structure
- [ ] Write tests for new modules FIRST
- [ ] Extract code incrementally
- [ ] Maintain facade for backward compatibility
- [ ] Run tests after each extraction
- [ ] Update imports throughout codebase
- [ ] Document new module structure

### Post-Refactoring
- [ ] Run full test suite
- [ ] Perform integration testing
- [ ] Check performance benchmarks
- [ ] Update architecture documentation
- [ ] Review with team
- [ ] Create migration guide if needed
- [ ] Monitor for issues in staging/production

### Quality Gates
- [ ] All tests passing
- [ ] No files exceed 1000 lines
- [ ] Code coverage maintained or improved
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Backward compatibility verified

## Risk Mitigation

### Risk Categories

#### High Risk Files
- Core system components (parent_directory_manager.py)
- Critical path modules (agent_registry.py)
- Mitigation: Extensive testing, feature flags, canary deployments

#### Medium Risk Files
- Service modules with external dependencies
- Modules with complex state management
- Mitigation: Integration testing, gradual rollout

#### Low Risk Files
- Utility modules
- Configuration handlers
- Mitigation: Standard testing, direct deployment

### Rollback Strategy
1. **Feature Flags**: Enable/disable refactored modules
2. **Parallel Running**: Run old and new implementations side by side
3. **Quick Revert**: Maintain ability to revert via git
4. **Monitoring**: Track errors and performance post-deployment

### Communication Plan
- Weekly updates on refactoring progress
- Immediate notification of breaking changes
- Documentation of any API changes
- Team reviews for critical refactorings

## Appendix: File-Specific Guidelines

### parent_directory_manager.py (2,620 lines)
- Extract directory operations into scanner module
- Separate template handling into deployment module
- Isolate backup operations
- Keep facade for compatibility

### agent_registry.py (2,151 lines)
- Remove async version entirely
- Split discovery from loading
- Extract caching logic
- Separate selection algorithms

### continuous_learning_engine.py (1,335 lines)
- Extract feedback collection
- Separate pattern analysis
- Isolate model adaptation
- Extract metrics tracking

---

This document provides comprehensive guidelines for the file size refactoring initiative. Follow these patterns and standards to ensure consistent, maintainable refactoring across the Claude Multi-Agent PM framework.