# Module Structure Standards - Claude Multi-Agent PM Framework

**Version**: 1.0.0  
**Created**: 2025-07-18  
**Epic**: EP-0043  
**Purpose**: Standards for organizing modules after refactoring large files

## Table of Contents
1. [Directory Structure](#directory-structure)
2. [Naming Conventions](#naming-conventions)
3. [Module Organization](#module-organization)
4. [Import/Export Standards](#importexport-standards)
5. [Documentation Requirements](#documentation-requirements)
6. [Examples](#examples)

## Directory Structure

### Standard Module Package Structure
```
claude_pm/
├── services/
│   ├── parent_directory_manager.py  # Facade (backward compatibility)
│   └── parent_directory/            # Package for split modules
│       ├── __init__.py             # Package exports
│       ├── _constants.py           # Private constants
│       ├── _types.py               # Private type definitions
│       ├── models.py               # Public data models
│       ├── directory_scanner.py    # Feature module
│       ├── template_deployment.py  # Feature module
│       ├── backup_manager.py       # Feature module
│       └── utils.py                # Shared utilities
```

### File Organization Rules

1. **Facade File**: Keep original filename as facade for backward compatibility
2. **Package Directory**: Create subdirectory with base name (without `_manager`, `_service`, etc.)
3. **Private Modules**: Prefix with underscore for internal-only modules
4. **Public Modules**: No underscore prefix for modules with exported APIs

## Naming Conventions

### Package Names
- Use the base name of the original file
- Remove suffixes like `_manager`, `_service`, `_engine`
- Use lowercase with underscores

```python
# Original file: parent_directory_manager.py
# Package name: parent_directory/

# Original file: continuous_learning_engine.py  
# Package name: continuous_learning/
```

### Module Names
- Descriptive names indicating functionality
- Avoid generic names like `handler`, `processor`
- Use specific action or component names

```python
# Good module names
directory_scanner.py      # Scans directories
template_deployment.py    # Deploys templates
feedback_collector.py     # Collects feedback

# Avoid generic names
handler.py               # Too generic
processor.py            # Unclear purpose
manager.py              # Redundant with package
```

### Class Names
- Maintain original class names in facades
- Use specific names in internal modules
- Follow PascalCase convention

```python
# In facade (backward compatibility)
class ParentDirectoryManager:
    pass

# In internal modules (specific names)
class DirectoryScanner:
    pass

class TemplateDeployer:
    pass
```

## Module Organization

### Standard Module Template
```python
"""
Module Name - Brief Description
================================

Detailed description of module's responsibility within the larger system.
This module was extracted from [original_file] as part of EP-0043.

Dependencies:
    - Internal: List of internal dependencies
    - External: List of external packages

Example:
    from claude_pm.services.parent_directory import DirectoryScanner
    
    scanner = DirectoryScanner()
    results = scanner.scan(path)
"""

# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import click
from typing import Dict, List, Optional

# Internal imports (absolute imports preferred)
from claude_pm.core.base_service import BaseService
from claude_pm.utils.logging import get_logger

# Module-level logger
logger = get_logger(__name__)

# Module constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Main module code
class DirectoryScanner:
    """Handles directory scanning operations."""
    pass
```

### Module Size Guidelines
- **Target**: 500-800 lines
- **Maximum**: 1000 lines
- **Minimum**: 100 lines
- **Sweet Spot**: 300-500 lines

### Module Cohesion Rules
1. **Single Responsibility**: Each module should have one clear purpose
2. **High Cohesion**: All code in a module should be closely related
3. **Low Coupling**: Minimize dependencies between modules
4. **Clear Interfaces**: Well-defined public APIs

## Import/Export Standards

### Package __init__.py
```python
"""
Parent Directory Management Package
===================================

This package provides comprehensive parent directory management functionality,
split from the original parent_directory_manager.py file.

Main Components:
    - DirectoryScanner: Scans and identifies parent directories
    - TemplateDeployer: Handles template deployment operations
    - BackupManager: Manages file backups and recovery
"""

# Public API exports
from .directory_scanner import DirectoryScanner
from .template_deployment import TemplateDeployer
from .backup_manager import BackupManager
from .models import (
    ParentDirectoryConfig,
    ParentDirectoryStatus,
    ParentDirectoryOperation,
)

# Version information
__version__ = "1.0.0"

# Define public API
__all__ = [
    "DirectoryScanner",
    "TemplateDeployer", 
    "BackupManager",
    "ParentDirectoryConfig",
    "ParentDirectoryStatus",
    "ParentDirectoryOperation",
]
```

### Import Best Practices
```python
# 1. Use absolute imports within the package
from claude_pm.services.parent_directory.models import Config  # Good
from .models import Config  # Avoid in larger projects

# 2. Group imports logically
# Standard library
import os
import sys

# Third-party
import pytest
import click

# Internal
from claude_pm.core import BaseService
from claude_pm.utils import logger

# 3. Avoid circular imports
# Use TYPE_CHECKING for type hints only
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claude_pm.services.other_service import OtherClass
```

### Facade Pattern Implementation
```python
# parent_directory_manager.py (Facade maintaining backward compatibility)
"""Backward compatibility facade for ParentDirectoryManager."""

from .parent_directory import (
    DirectoryScanner,
    TemplateDeployer,
    BackupManager,
)

class ParentDirectoryManager:
    """
    Facade class maintaining backward compatibility.
    
    This class delegates to the refactored modules while preserving
    the original API for existing code.
    """
    
    def __init__(self, *args, **kwargs):
        self._scanner = DirectoryScanner(*args, **kwargs)
        self._deployer = TemplateDeployer(*args, **kwargs)
        self._backup = BackupManager(*args, **kwargs)
    
    # Delegate all methods to appropriate modules
    def scan_directories(self, *args, **kwargs):
        return self._scanner.scan(*args, **kwargs)
    
    def deploy_template(self, *args, **kwargs):
        return self._deployer.deploy(*args, **kwargs)
    
    def backup_files(self, *args, **kwargs):
        return self._backup.backup(*args, **kwargs)
```

## Documentation Requirements

### Module-Level Documentation
Every module must include:
1. Module docstring with description
2. List of main classes/functions
3. Dependencies (internal and external)
4. Usage examples
5. Notes about extraction from original file

### Class-Level Documentation
```python
class DirectoryScanner:
    """
    Scans directories to identify parent directory structures.
    
    This class handles the discovery and validation of parent directories
    within the Claude PM framework structure. It was extracted from
    parent_directory_manager.py as part of the refactoring initiative.
    
    Attributes:
        base_path: Root path for scanning operations
        max_depth: Maximum directory depth to scan
        ignore_patterns: List of patterns to ignore during scanning
    
    Example:
        scanner = DirectoryScanner(base_path="/projects")
        results = scanner.scan(recursive=True)
        for dir_info in results:
            print(f"Found: {dir_info.path}")
    """
```

### Function-Level Documentation
```python
def scan(self, path: Path, recursive: bool = True) -> List[DirectoryInfo]:
    """
    Scan a directory for parent directory markers.
    
    Args:
        path: Directory path to scan
        recursive: Whether to scan subdirectories
        
    Returns:
        List of DirectoryInfo objects for found parent directories
        
    Raises:
        PermissionError: If directory cannot be accessed
        ValueError: If path is not a valid directory
        
    Example:
        results = scanner.scan(Path("/home/user/projects"))
    """
```

## Examples

### Example 1: Service Manager Refactoring
```
# Original: health_monitor.py (1,482 lines)

# Refactored structure:
claude_pm/
├── services/
│   ├── health_monitor.py  # Facade (150 lines)
│   └── health_monitoring/
│       ├── __init__.py
│       ├── models.py          # Data models (150 lines)
│       ├── system_checker.py  # System checks (300 lines)
│       ├── agent_monitor.py   # Agent monitoring (300 lines)
│       ├── metrics_collector.py # Metrics (250 lines)
│       ├── reporters.py       # Reporting (200 lines)
│       └── utils.py          # Utilities (132 lines)
```

### Example 2: Registry Refactoring
```
# Original: agent_registry.py (2,151 lines)

# Refactored structure:
claude_pm/
├── core/
│   ├── agent_registry.py  # Facade (200 lines)
│   └── agent_registry/
│       ├── __init__.py
│       ├── models.py         # Agent models (200 lines)
│       ├── discovery.py      # Agent discovery (400 lines)
│       ├── loader.py         # Agent loading (350 lines)
│       ├── cache.py          # Caching logic (300 lines)
│       ├── selector.py       # Selection algorithms (250 lines)
│       ├── metadata.py       # Metadata management (200 lines)
│       └── utils.py          # Utilities (250 lines)
```

### Example 3: CLI Refactoring
```
# Original: __main__.py (1,165 lines)

# Refactored structure:
claude_pm/
├── __main__.py  # Entry point (100 lines)
└── cli/
    ├── __init__.py
    ├── commands.py      # Command definitions (300 lines)
    ├── parsers.py       # Argument parsing (250 lines)
    ├── handlers.py      # Command handlers (300 lines)
    ├── formatters.py    # Output formatting (200 lines)
    └── utils.py         # CLI utilities (115 lines)
```

## Anti-Patterns to Avoid

### 1. Over-Fragmentation
```python
# Bad: Too many tiny modules
models/
├── config_model.py      # 20 lines
├── status_model.py      # 15 lines
├── operation_model.py   # 25 lines
└── result_model.py      # 18 lines

# Good: Logical grouping
models.py  # All related models in one file (100 lines)
```

### 2. Circular Dependencies
```python
# Bad: Circular import
# file_a.py
from .file_b import ClassB

# file_b.py
from .file_a import ClassA

# Good: Use dependency injection or interfaces
# file_a.py
class ClassA:
    def __init__(self, b_instance):
        self.b = b_instance
```

### 3. God Modules
```python
# Bad: Module doing too much
utils.py  # 900 lines of unrelated utilities

# Good: Specific utility modules
path_utils.py      # Path manipulation (200 lines)
string_utils.py    # String operations (150 lines)
date_utils.py      # Date/time helpers (150 lines)
```

### 4. Inconsistent Interfaces
```python
# Bad: Different patterns in same package
scanner.scan_directories()
deployer.execute_deployment()
backup_mgr.run()

# Good: Consistent interface
scanner.execute()
deployer.execute()
backup_manager.execute()
```

## Validation Checklist

Before completing a module refactoring:

- [ ] Module follows naming conventions
- [ ] Directory structure matches standards
- [ ] All imports are properly organized
- [ ] __init__.py exports public API
- [ ] Facade maintains backward compatibility
- [ ] Documentation is complete
- [ ] No circular dependencies
- [ ] Module size is within limits
- [ ] Tests cover new module structure
- [ ] Integration points are validated

---

These standards ensure consistency across the refactoring effort and maintain a clean, navigable codebase for the Claude Multi-Agent PM framework.