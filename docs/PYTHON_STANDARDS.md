# Claude PM Framework - Python Coding Standards

## Overview

This document defines the coding standards and best practices for Python development within the Claude PM Framework. These standards ensure consistency, maintainability, and quality across all Python code in the framework.

## Table of Contents

- [General Principles](#general-principles)
- [Code Style](#code-style)
- [Project Structure](#project-structure)
- [Type Hints](#type-hints)
- [Documentation](#documentation)
- [Error Handling](#error-handling)
- [Async/Await Patterns](#asyncawait-patterns)
- [Testing](#testing)
- [Dependencies](#dependencies)
- [Performance](#performance)
- [Security](#security)

## General Principles

### 1. Readability First
Code should be written for humans to read. Optimize for clarity over cleverness.

```python
# Good
def calculate_project_health_percentage(healthy_projects: int, total_projects: int) -> int:
    """Calculate the percentage of healthy projects."""
    if total_projects == 0:
        return 0
    return round((healthy_projects / total_projects) * 100)

# Avoid
def calc_health_pct(h: int, t: int) -> int:
    return 0 if not t else round((h/t)*100)
```

### 2. Explicit is Better Than Implicit
Make intentions clear and avoid magic numbers or strings.

```python
# Good
DEFAULT_HEALTH_CHECK_INTERVAL = 300  # 5 minutes in seconds
CRITICAL_HEALTH_THRESHOLD = 60  # Percentage

# Avoid
def check_health():
    time.sleep(300)  # What is 300?
    if health < 60:  # Magic number
        alert()
```

### 3. Fail Fast and Clearly
Detect errors early and provide meaningful error messages.

```python
# Good
def create_project_memory(project_name: str) -> bool:
    if not project_name or not project_name.strip():
        raise ValueError("Project name cannot be empty or whitespace")
    
    if not self._is_valid_project_name(project_name):
        raise ValueError(f"Invalid project name format: {project_name}")
    
    # ... rest of implementation

# Avoid
def create_project_memory(project_name: str) -> bool:
    # Silent failure or unclear error
    if not project_name:
        return False
```

## Code Style

### Formatting with Black
All Python code must be formatted with [Black](https://black.readthedocs.io/) using these settings:

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']
```

### Import Organization with isort
Imports should be organized using [isort](https://pycqa.github.io/isort/) with Black compatibility:

```python
# Standard library imports
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
import aiohttp
import click
from rich.console import Console

# First-party imports
from claude_pm.core.base_service import BaseService
from claude_pm.services.memory_service import MemoryService

# Local imports
from .config import Config
from .utils import format_timestamp
```

### Naming Conventions

#### Variables and Functions
- Use `snake_case` for variables and functions
- Use descriptive names that explain purpose

```python
# Good
health_check_interval = 300
project_compliance_score = 85
memory_service_instance = MemoryService()

def calculate_framework_compliance() -> int:
    pass

def get_project_health_status(project_name: str) -> str:
    pass

# Avoid
hci = 300
pcs = 85
msi = MemoryService()

def calc_fc() -> int:
    pass
```

#### Classes
- Use `PascalCase` for class names
- Use descriptive names that indicate the class's responsibility

```python
# Good
class HealthMonitorService:
    pass

class ProjectComplianceChecker:
    pass

class Mem0AIIntegration:
    pass

# Avoid
class HMS:
    pass

class Checker:
    pass
```

#### Constants
- Use `UPPER_SNAKE_CASE` for constants
- Group related constants in classes or modules

```python
# Good
DEFAULT_PORT = 8002
MAX_RETRY_ATTEMPTS = 3
HEALTH_CHECK_INTERVAL_SECONDS = 300

class ServiceConfig:
    DEFAULT_TIMEOUT = 30
    MAX_CONNECTIONS = 100
    RETRY_DELAY_SECONDS = 1.0

# Avoid
port = 8002
max_retries = 3
```

## Project Structure

### Package Organization
```
claude_pm/
├── __init__.py          # Package initialization
├── py.typed             # PEP 561 type checking marker
├── cli.py               # Main CLI entry point
├── core/                # Core framework components
│   ├── __init__.py
│   ├── base_service.py  # Base service class
│   ├── config.py        # Configuration management
│   ├── logging_config.py # Logging setup
│   └── service_manager.py # Service orchestration
├── services/            # Service implementations
│   ├── __init__.py
│   ├── health_monitor.py
│   ├── memory_service.py
│   └── project_service.py
├── integrations/        # External service integrations
│   ├── __init__.py
│   ├── mem0ai_integration.py
│   └── langgraph_integration.py
└── scripts/             # Utility scripts
    ├── __init__.py
    └── service_manager.py
```

### Module Guidelines
- Keep modules focused on a single responsibility
- Use `__init__.py` to expose public APIs
- Keep implementation details private with underscore prefixes

```python
# claude_pm/services/__init__.py
"""Claude PM Framework services."""

from .health_monitor import HealthMonitorService
from .memory_service import MemoryService
from .project_service import ProjectService

__all__ = ["HealthMonitorService", "MemoryService", "ProjectService"]
```

## Type Hints

### Comprehensive Type Annotations
All public functions and methods must have complete type annotations:

```python
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

def process_project_data(
    project_name: str,
    config: Dict[str, Any],
    files: List[Path],
    timeout: Optional[int] = None
) -> Dict[str, Union[str, int, bool]]:
    """Process project data and return results."""
    pass

class ProjectService:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._projects: Dict[str, ProjectInfo] = {}
    
    async def get_project(self, name: str) -> Optional[ProjectInfo]:
        return self._projects.get(name)
```

### Use of dataclasses
Prefer dataclasses for structured data:

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ProjectInfo:
    """Information about a managed project."""
    name: str
    path: str
    type: str
    status: str
    compliance_score: int
    last_activity: str
    framework_files: Dict[str, bool]
    git_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServiceHealth:
    """Service health status information."""
    status: str
    message: str
    timestamp: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, bool] = field(default_factory=dict)
```

### Generic Types
Use generic types appropriately:

```python
from typing import TypeVar, Generic, Protocol

T = TypeVar('T')

class Repository(Generic[T]):
    def save(self, item: T) -> None:
        pass
    
    def find_by_id(self, id: str) -> Optional[T]:
        pass

class Serializable(Protocol):
    def to_dict(self) -> Dict[str, Any]:
        ...
```

## Documentation

### Docstring Standards
Use Google-style docstrings with comprehensive documentation:

```python
def calculate_compliance_score(
    framework_files: Dict[str, bool],
    weights: Dict[str, int]
) -> int:
    """
    Calculate compliance score based on framework files and their weights.
    
    This function evaluates project compliance by checking the presence of
    required framework files and applying weighted scoring.
    
    Args:
        framework_files: Dictionary mapping file names to existence status.
        weights: Dictionary mapping file names to their scoring weights.
        
    Returns:
        Compliance score as integer percentage (0-100).
        
    Raises:
        ValueError: If weights dictionary is empty.
        TypeError: If framework_files contains non-boolean values.
        
    Example:
        >>> files = {"CLAUDE.md": True, "README.md": False}
        >>> weights = {"CLAUDE.md": 30, "README.md": 20}
        >>> calculate_compliance_score(files, weights)
        60
    """
    if not weights:
        raise ValueError("Weights dictionary cannot be empty")
    
    total_weight = sum(weights.values())
    achieved_weight = sum(
        weight for file_name, weight in weights.items()
        if framework_files.get(file_name, False)
    )
    
    return round((achieved_weight / total_weight) * 100)
```

### Class Documentation
Document classes with their purpose, key methods, and usage examples:

```python
class MemoryService(BaseService):
    """
    Service for managing AI-enhanced project memory using mem0AI.
    
    This service provides integration with mem0AI for intelligent project
    memory management, including storing and retrieving project decisions,
    code patterns, and troubleshooting information.
    
    Attributes:
        categories: Available memory categories for classification.
        base_url: Base URL for mem0AI service communication.
        
    Example:
        >>> memory_service = MemoryService()
        >>> await memory_service.start()
        >>> memory_id = await memory_service.store_project_decision(
        ...     "my-project",
        ...     "Use PostgreSQL for data storage",
        ...     "Need ACID compliance for financial data"
        ... )
    """
```

## Error Handling

### Exception Hierarchy
Create custom exceptions with clear inheritance:

```python
class ClaudePMError(Exception):
    """Base exception for Claude PM Framework."""
    pass

class ServiceError(ClaudePMError):
    """Raised when service operations fail."""
    pass

class ConfigurationError(ClaudePMError):
    """Raised when configuration is invalid."""
    pass

class MemoryServiceError(ServiceError):
    """Raised when memory service operations fail."""
    
    def __init__(self, message: str, project_name: Optional[str] = None):
        super().__init__(message)
        self.project_name = project_name
```

### Error Handling Patterns
Use proper error handling with context and logging:

```python
async def store_memory(
    self, 
    project_name: str, 
    content: str
) -> Optional[str]:
    """Store a memory with comprehensive error handling."""
    try:
        # Validate inputs
        if not project_name.strip():
            raise ValueError("Project name cannot be empty")
        
        if not content.strip():
            raise ValueError("Memory content cannot be empty")
        
        # Attempt operation
        memory_id = await self._api_call(project_name, content)
        
        self.logger.info(f"Memory stored successfully: {memory_id}")
        return memory_id
        
    except aiohttp.ClientError as e:
        self.logger.error(f"Network error storing memory for {project_name}: {e}")
        raise MemoryServiceError(
            f"Failed to store memory due to network error: {e}",
            project_name=project_name
        ) from e
        
    except ValueError as e:
        self.logger.error(f"Invalid input for memory storage: {e}")
        raise  # Re-raise validation errors as-is
        
    except Exception as e:
        self.logger.error(f"Unexpected error storing memory for {project_name}: {e}")
        raise MemoryServiceError(
            f"Unexpected error storing memory: {e}",
            project_name=project_name
        ) from e
```

### Context Managers
Use context managers for resource management:

```python
from contextlib import asynccontextmanager

class MemoryService:
    @asynccontextmanager
    async def session(self):
        """Async context manager for memory service sessions."""
        session = None
        try:
            session = aiohttp.ClientSession()
            yield session
        finally:
            if session:
                await session.close()

# Usage
async with memory_service.session() as session:
    # Use session for multiple operations
    pass
```

## Async/Await Patterns

### Async Function Design
Use async/await consistently and properly:

```python
class BaseService:
    async def start(self) -> None:
        """Start the service with proper async patterns."""
        try:
            # Initialize in sequence
            await self._initialize()
            
            # Start background tasks in parallel
            tasks = await self._start_background_tasks()
            if tasks:
                self._background_tasks.extend(tasks)
            
            self._running = True
            self.logger.info(f"Service {self.name} started")
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            await self._cleanup()
            raise
    
    async def _initialize(self) -> None:
        """Override in subclasses for initialization."""
        pass
    
    async def _start_background_tasks(self) -> Optional[List[asyncio.Task]]:
        """Override in subclasses to start background tasks."""
        return None
```

### Proper Task Management
Handle asyncio tasks correctly:

```python
class ServiceManager:
    def __init__(self):
        self._background_tasks: List[asyncio.Task] = []
    
    async def start_background_task(self, coro):
        """Start a background task with proper tracking."""
        task = asyncio.create_task(coro)
        self._background_tasks.append(task)
        
        # Clean up completed tasks
        self._background_tasks = [
            t for t in self._background_tasks 
            if not t.done()
        ]
        
        return task
    
    async def stop_all_tasks(self):
        """Stop all background tasks gracefully."""
        if not self._background_tasks:
            return
        
        # Cancel all tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
```

### Timeout Handling
Use timeouts appropriately:

```python
async def health_check_with_timeout(self, timeout: float = 30.0) -> bool:
    """Health check with configurable timeout."""
    try:
        async with asyncio.timeout(timeout):
            result = await self._perform_health_check()
            return result
    except asyncio.TimeoutError:
        self.logger.warning(f"Health check timed out after {timeout}s")
        return False
```

## Testing

### Test Structure
Organize tests with clear structure and comprehensive coverage:

```python
# tests/services/test_memory_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from claude_pm.services.memory_service import MemoryService, MemoryItem

class TestMemoryService:
    """Test suite for MemoryService."""
    
    @pytest.fixture
    async def memory_service(self):
        """Create memory service for testing."""
        service = MemoryService({
            "mem0ai_host": "localhost",
            "mem0ai_port": 8002,
            "mem0ai_timeout": 5
        })
        await service._initialize()
        yield service
        await service._cleanup()
    
    @pytest.mark.asyncio
    async def test_store_memory_success(self, memory_service):
        """Test successful memory storage."""
        # Arrange
        project_name = "test-project"
        content = "Test memory content"
        category = "project_decision"
        
        # Mock the HTTP session
        memory_service._session = AsyncMock()
        memory_service._session.post.return_value.__aenter__.return_value.status = 201
        memory_service._session.post.return_value.__aenter__.return_value.json.return_value = {
            "id": "test-memory-id"
        }
        
        # Act
        memory_id = await memory_service.store_memory(
            project_name, content, category
        )
        
        # Assert
        assert memory_id == "test-memory-id"
        memory_service._session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_memory_validation_error(self, memory_service):
        """Test memory storage with invalid input."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            await memory_service.store_memory("", "content", "category")
    
    @pytest.mark.parametrize("project_name,content,category", [
        ("test-project", "valid content", "project_decision"),
        ("another-project", "another content", "code_pattern"),
        ("third-project", "error solution", "error_solution"),
    ])
    @pytest.mark.asyncio
    async def test_store_memory_various_inputs(
        self, memory_service, project_name, content, category
    ):
        """Test memory storage with various valid inputs."""
        # Setup mock
        memory_service._session = AsyncMock()
        memory_service._session.post.return_value.__aenter__.return_value.status = 201
        memory_service._session.post.return_value.__aenter__.return_value.json.return_value = {
            "id": f"memory-{project_name}"
        }
        
        # Test
        memory_id = await memory_service.store_memory(project_name, content, category)
        
        # Verify
        assert memory_id == f"memory-{project_name}"
```

### Test Configuration
Use pytest configuration for consistent testing:

```ini
# pytest.ini
[tool:pytest]
minversion = 7.0
addopts = 
    -ra
    -q
    --strict-markers
    --strict-config
    --cov=claude_pm
    --cov-report=term-missing
    --cov-report=html
testpaths = tests
python_files = test_*.py *_test.py
python_functions = test_*
python_classes = Test*
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    mem0ai: marks tests that require mem0ai service
```

## Dependencies

### Dependency Management
Use specific version ranges and organize dependencies by purpose:

```toml
# pyproject.toml
[project]
dependencies = [
    # Core framework
    "aiohttp>=3.9.0,<4.0.0",
    "click>=8.1.0,<9.0.0",
    "rich>=13.7.0,<14.0.0",
    "pydantic>=2.5.0,<3.0.0",
    
    # Configuration and data
    "pyyaml>=6.0.1",
    "python-dotenv>=1.0.0",
    
    # System monitoring
    "psutil>=5.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.9.0",
    "isort>=5.12.0",
    "mypy>=1.6.0",
]
```

### Import Guidelines
- Import only what you need
- Use absolute imports for clarity
- Group imports logically

```python
# Good
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from rich.console import Console

from claude_pm.core.base_service import BaseService

# Avoid
from pathlib import *
from typing import *
import claude_pm.core.base_service
```

## Performance

### Async Best Practices
Use async patterns efficiently:

```python
# Good - Concurrent operations
async def check_multiple_services(self, service_names: List[str]) -> Dict[str, bool]:
    """Check multiple services concurrently."""
    tasks = [
        self._check_single_service(name) 
        for name in service_names
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        name: result if not isinstance(result, Exception) else False
        for name, result in zip(service_names, results)
    }

# Avoid - Sequential operations
async def check_multiple_services_slow(self, service_names: List[str]) -> Dict[str, bool]:
    """Inefficient sequential checking."""
    results = {}
    for name in service_names:
        results[name] = await self._check_single_service(name)
    return results
```

### Memory Management
Be mindful of memory usage in long-running services:

```python
class MemoryService:
    def __init__(self):
        self._cache: Dict[str, List[MemoryItem]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._max_cache_size = 1000
        self._cache_ttl = 300  # 5 minutes
    
    def _cleanup_cache(self) -> None:
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._cache_timestamps.items()
            if current_time - timestamp > self._cache_ttl
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        
        # Limit cache size
        if len(self._cache) > self._max_cache_size:
            # Remove oldest entries
            sorted_keys = sorted(
                self._cache_timestamps.items(),
                key=lambda x: x[1]
            )
            
            keys_to_remove = sorted_keys[:len(sorted_keys) - self._max_cache_size]
            for key, _ in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
```

## Security

### Input Validation
Always validate and sanitize inputs:

```python
def validate_project_name(project_name: str) -> str:
    """Validate and sanitize project name."""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("Project name must be a non-empty string")
    
    # Remove leading/trailing whitespace
    clean_name = project_name.strip()
    
    # Check length
    if len(clean_name) < 1 or len(clean_name) > 100:
        raise ValueError("Project name must be 1-100 characters long")
    
    # Check for invalid characters
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', clean_name):
        raise ValueError("Project name can only contain letters, numbers, underscores, and hyphens")
    
    return clean_name
```

### Secret Management
Handle secrets securely:

```python
import os
from typing import Optional

class Config:
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        # Try multiple environment variable names
        for env_var in ['OPENAI_API_KEY', 'CLAUDE_PM_OPENAI_API_KEY']:
            api_key = os.getenv(env_var)
            if api_key:
                return api_key
        
        return None
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format without logging it."""
        if not api_key:
            return False
        
        # Basic format validation (don't log the actual key)
        if len(api_key) < 10:
            self.logger.warning("API key appears to be too short")
            return False
        
        return True
```

### Logging Security
Never log sensitive information:

```python
def log_api_request(self, url: str, headers: Dict[str, str]) -> None:
    """Log API request without sensitive information."""
    # Remove sensitive headers before logging
    safe_headers = {
        key: value if key.lower() not in ['authorization', 'x-api-key'] else '***'
        for key, value in headers.items()
    }
    
    self.logger.info(f"API request to {url}", extra={
        "headers": safe_headers,
        "url": url
    })
```

## Development Workflow

### Pre-commit Hooks
Use pre-commit hooks for code quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
```

### Makefile Integration
Use Make for development tasks:

```makefile
# Development workflow
dev: install-dev format lint type-check test
	@echo "Development workflow complete!"

# Code quality
check: format lint type-check
	@echo "All code quality checks passed!"

format:
	black claude_pm/ tests/
	isort claude_pm/ tests/

lint:
	flake8 claude_pm/ tests/

type-check:
	mypy claude_pm/
```

This concludes the Claude PM Framework Python coding standards. Following these guidelines ensures consistent, maintainable, and high-quality Python code across the entire framework.