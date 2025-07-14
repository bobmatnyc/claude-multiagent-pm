# Development Standards Comprehensive Guide - Claude PM Framework

## Overview

This comprehensive guide covers all development standards and practices for the Claude PM Framework v4.5.1, including Python coding standards, quick start procedures, system architecture guidelines, and best practices for maintainable, scalable development.

## Table of Contents

1. [Python Coding Standards](#python-coding-standards)
2. [Quick Start Guide](#quick-start-guide)
3. [System Architecture Guidelines](#system-architecture-guidelines)
4. [Development Workflow](#development-workflow)
5. [Code Quality Standards](#code-quality-standards)
6. [Best Practices](#best-practices)
7. [Performance Guidelines](#performance-guidelines)
8. [Security Standards](#security-standards)

## Python Coding Standards

### General Principles

#### 1. Readability First
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

#### 2. Explicit is Better Than Implicit
Make intentions clear and avoid magic numbers or strings.

```python
# Good
DEFAULT_HEALTH_CHECK_INTERVAL = 300  # 5 minutes in seconds
CRITICAL_HEALTH_THRESHOLD = 60  # Percentage

def check_health():
    time.sleep(DEFAULT_HEALTH_CHECK_INTERVAL)
    if health_percentage < CRITICAL_HEALTH_THRESHOLD:
        trigger_alert()

# Avoid
def check_health():
    time.sleep(300)  # What is 300?
    if health < 60:  # Magic number
        trigger_alert()
```

### Code Style

#### Formatting Standards

Follow PEP 8 with these specific guidelines:

```python
# Line length: 100 characters (not 79)
# Use Black for automatic formatting
# Use isort for import organization

# Good import organization
from typing import Dict, List, Optional, Union
import asyncio
import logging
from datetime import datetime

from claude_pm.core.config import Config
from claude_pm.services.memory_service import MemoryService
from claude_pm.utils.logging import setup_logging
```

#### Naming Conventions

```python
# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30

# Variables and functions: snake_case
user_session_data = {}
health_check_interval = 300

def validate_user_permissions(user_id: str, required_permissions: List[str]) -> bool:
    """Validate if user has required permissions."""
    pass

# Classes: PascalCase
class MemoryServiceManager:
    """Manages memory service operations."""
    pass

# Private methods: _snake_case
def _internal_validation(self, data: Dict[str, Any]) -> bool:
    """Internal validation method."""
    pass
```

### Type Hints

#### Comprehensive Type Annotations

```python
from typing import Dict, List, Optional, Union, Any, Callable, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum

# Function signatures
def process_user_data(
    user_id: str,
    user_data: Dict[str, Any],
    validation_rules: List[Callable[[str, Any], bool]],
    timeout: Optional[float] = None
) -> Dict[str, Union[str, bool, List[str]]]:
    """Process user data with validation."""
    pass

# Class with type hints
@dataclass
class ProjectConfiguration:
    """Project configuration with type safety."""
    project_name: str
    memory_enabled: bool
    health_check_interval: int
    allowed_agents: List[str]
    metadata: Optional[Dict[str, Any]] = None

# Generic classes
T = TypeVar('T')

class ServiceManager(Generic[T]):
    """Generic service manager."""
    
    def __init__(self, service_class: type[T]) -> None:
        self.service_class = service_class
        self.instances: Dict[str, T] = {}
    
    def get_service(self, service_id: str) -> Optional[T]:
        """Get service instance by ID."""
        return self.instances.get(service_id)
```

#### Union Types and Optional

```python
# Use Union for multiple types
def parse_config_value(value: Union[str, int, bool]) -> str:
    """Parse configuration value to string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

# Use Optional for nullable values
def get_user_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user session data if it exists."""
    return sessions.get(user_id)

# Modern Python 3.10+ syntax
def process_response(response: str | int | None) -> str:
    """Process API response."""
    match response:
        case str() if response:
            return f"String response: {response}"
        case int() if response > 0:
            return f"Numeric response: {response}"
        case None:
            return "No response"
        case _:
            return "Invalid response"
```

### Documentation

#### Docstring Standards

```python
def store_project_memory(
    project_name: str,
    memory_content: str,
    category: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Store memory content for a specific project.
    
    This function stores memory content in the project's memory space
    with appropriate categorization and metadata.
    
    Args:
        project_name: Name of the project (must be non-empty)
        memory_content: Content to store (must be non-empty)
        category: Memory category (e.g., 'decision', 'pattern', 'error')
        metadata: Optional metadata to associate with the memory
    
    Returns:
        True if memory was stored successfully, False otherwise
    
    Raises:
        ValueError: If project_name or memory_content is empty
        MemoryServiceError: If memory service is unavailable
    
    Example:
        >>> store_project_memory(
        ...     "web_app", 
        ...     "Use JWT for authentication", 
        ...     "decision",
        ...     {"priority": "high", "timestamp": "2025-01-01"}
        ... )
        True
    """
    if not project_name.strip():
        raise ValueError("Project name cannot be empty")
    
    if not memory_content.strip():
        raise ValueError("Memory content cannot be empty")
    
    try:
        memory_service = get_memory_service()
        return memory_service.store_memory(
            project_name=project_name,
            content=memory_content,
            category=category,
            metadata=metadata or {}
        )
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise MemoryServiceError(f"Memory storage failed: {e}")
```

### Error Handling

#### Exception Hierarchy

```python
# Custom exception hierarchy
class ClaudePMError(Exception):
    """Base exception for Claude PM Framework."""
    pass

class ConfigurationError(ClaudePMError):
    """Configuration-related errors."""
    pass

class ServiceError(ClaudePMError):
    """Service-related errors."""
    
    def __init__(self, message: str, service_name: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.service_name = service_name
        self.error_code = error_code

class MemoryServiceError(ServiceError):
    """Memory service specific errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message, "memory_service", error_code)
```

#### Error Handling Patterns

```python
# Comprehensive error handling
async def safe_memory_operation(operation: Callable, *args, **kwargs) -> OperationResult:
    """Safely execute memory operation with proper error handling."""
    
    try:
        result = await operation(*args, **kwargs)
        return OperationResult(success=True, data=result)
        
    except MemoryServiceError as e:
        logger.warning(f"Memory service error: {e}")
        return OperationResult(
            success=False, 
            error=str(e), 
            error_type="memory_service",
            retry_recommended=True
        )
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return OperationResult(
            success=False, 
            error=str(e), 
            error_type="configuration",
            retry_recommended=False
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error in memory operation: {e}")
        return OperationResult(
            success=False, 
            error=f"Unexpected error: {e}", 
            error_type="unexpected",
            retry_recommended=False
        )

# Context manager for resource cleanup
@contextmanager
async def memory_service_context():
    """Context manager for memory service operations."""
    
    service = None
    try:
        service = await get_memory_service()
        yield service
    except Exception as e:
        logger.error(f"Memory service context error: {e}")
        raise
    finally:
        if service:
            await service.cleanup()
```

### Async/Await Patterns

#### Asynchronous Best Practices

```python
# Proper async function definition
async def fetch_user_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user data asynchronously."""
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"/api/users/{user_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"User {user_id} not found: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching user {user_id}")
            return None

# Concurrent operations
async def batch_process_users(user_ids: List[str]) -> List[Optional[Dict[str, Any]]]:
    """Process multiple users concurrently."""
    
    # Create tasks for concurrent execution
    tasks = [fetch_user_data(user_id) for user_id in user_ids]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and handle exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error processing user {user_ids[i]}: {result}")
            processed_results.append(None)
        else:
            processed_results.append(result)
    
    return processed_results

# Async context managers
class AsyncMemoryService:
    """Async memory service with proper resource management."""
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        if exc_type:
            logger.error(f"Error in async context: {exc_val}")
        return False  # Don't suppress exceptions
```

## Quick Start Guide

### 5-Minute Setup

#### Prerequisites Check
```bash
# Verify you're in the framework directory
pwd
# Should show: /Users/masa/Projects/claude-multiagent-pm

# Check memory service status
curl http://localhost:8002/health
# Expected: {"status": "healthy", "memory_service": "operational"}
```

#### Instant Memory Integration
```python
# Zero-configuration memory access
from config.memory_config import create_claude_pm_memory

# Automatic service discovery and connection
memory = create_claude_pm_memory()

# Immediate memory operations - no setup required
memory.add_project_memory("Started Claude PM Framework quick start guide")
print("✅ Memory integration working!")
```

#### Framework Status Check
```bash
# Current framework status
cat trackdown/CURRENT-STATUS.md

# Phase 1 progress (should show 83% complete)
grep -A5 "Phase 1 Progress" trackdown/BACKLOG.md

# Active services verification
systemctl status claude-pm-health-monitor 2>/dev/null || echo "Health monitor available"
```

### 10-Minute Deep Dive

#### Understanding the 11-Agent Ecosystem

```python
# Example: Engineer agent delegation
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator

async def quick_agent_demo():
    orchestrator = MultiAgentOrchestrator()
    
    # Get available agents
    agents = await orchestrator.get_available_agents()
    print(f"Available agents: {list(agents.keys())}")
    
    # Example delegation to Research Agent
    result = await orchestrator.delegate_task(
        agent_type="research",
        task="Analyze project dependencies and provide recommendations",
        context={
            "project_path": "/Users/masa/Projects/claude-multiagent-pm",
            "focus": "security_vulnerabilities"
        }
    )
    
    if result.success:
        print(f"Research completed: {result.summary}")
    else:
        print(f"Research failed: {result.error}")

# Run the demo
import asyncio
asyncio.run(quick_agent_demo())
```

#### Memory-First Development Pattern

```python
# Memory-augmented development workflow
from claude_pm.services.memory_service import get_memory_service

async def memory_enhanced_workflow():
    memory = get_memory_service()
    
    # 1. Check for existing patterns
    patterns = await memory.retrieve_memories(
        category="pattern",
        query="authentication security"
    )
    
    print(f"Found {len(patterns)} relevant patterns")
    
    # 2. Store new decision
    decision_id = await memory.store_memory(
        category="decision",
        content="Implement OAuth2 with PKCE for mobile app authentication",
        project_name="mobile_app_v2",
        metadata={
            "alternatives": ["JWT", "Session-based"],
            "reasoning": "Better security for mobile devices",
            "impact": "high"
        }
    )
    
    print(f"Decision stored with ID: {decision_id}")
    
    # 3. Add implementation pattern
    await memory.store_memory(
        category="pattern",
        content="Use authorization code flow with PKCE for OAuth2 implementation",
        project_name="mobile_app_v2",
        tags=["oauth2", "mobile", "security", "authentication"]
    )
    
    print("✅ Memory-enhanced workflow complete")

asyncio.run(memory_enhanced_workflow())
```

### 15-Minute Production Setup

#### Complete Environment Configuration

```bash
# 1. Memory service setup
# Service should already be running on port 8002
curl http://localhost:8002/health

# 2. Framework validation
python ~/.claude/commands/cmpm-bridge.py cmcp-init --verify

# 3. Agent hierarchy check
ls -la .claude-pm/agents/
ls -la ~/.claude-pm/agents/user-defined/
ls -la /Users/masa/Projects/claude-multiagent-pm/claude_pm/agents/

# 4. Health monitoring setup
python -c "
from claude_pm.services.health_dashboard import HealthDashboard
dashboard = HealthDashboard()
status = dashboard.get_system_health()
print(f'System Health: {status[\"overall_health\"]}%')
"
```

#### Production Memory Configuration

```python
# Production memory configuration
from claude_pm.services.memory_service import ClaudePMMemory, ClaudePMConfig

# Production configuration
config = ClaudePMConfig(
    host="localhost",
    port=8002,
    timeout=30,
    max_retries=3,
    enable_logging=True,
    connection_pool_size=10,
    # Production optimizations
    batch_size=50,
    cache_ttl=600,  # 10 minutes
    compression_enabled=True
)

memory = ClaudePMMemory(config)

# Verify production setup
async def verify_production_setup():
    # Health check
    health = await memory.health_check()
    print(f"Memory service health: {health}")
    
    # Performance test
    start_time = time.time()
    test_id = await memory.store_memory(
        category="test",
        content="Production setup verification",
        project_name="framework_test"
    )
    response_time = (time.time() - start_time) * 1000
    
    print(f"Memory storage response time: {response_time:.2f}ms")
    print(f"Test memory ID: {test_id}")
    
    # Cleanup test data
    await memory.delete_memory(test_id)
    print("✅ Production setup verified")

asyncio.run(verify_production_setup())
```

## System Architecture Guidelines

### Modular Design Principles

#### Service-Oriented Architecture

```python
# Service interface definition
from abc import ABC, abstractmethod
from typing import Protocol

class ServiceInterface(Protocol):
    """Protocol defining service interface."""
    
    async def initialize(self) -> bool:
        """Initialize the service."""
        ...
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        ...
    
    async def cleanup(self) -> None:
        """Cleanup service resources."""
        ...

# Service implementation
class MemoryService(ServiceInterface):
    """Memory service implementation."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.connection_pool = None
        self.cache = None
    
    async def initialize(self) -> bool:
        """Initialize memory service."""
        try:
            self.connection_pool = await create_connection_pool(self.config)
            self.cache = await create_cache_instance(self.config)
            return True
        except Exception as e:
            logger.error(f"Memory service initialization failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check memory service health."""
        return {
            "status": "healthy" if self.connection_pool else "unhealthy",
            "connections": len(self.connection_pool) if self.connection_pool else 0,
            "cache_size": self.cache.size() if self.cache else 0,
            "response_time": await self._measure_response_time()
        }
```

#### Dependency Injection

```python
# Dependency injection container
class ServiceContainer:
    """Dependency injection container for services."""
    
    def __init__(self):
        self._services = {}
        self._factories = {}
    
    def register_factory(self, service_type: type, factory: Callable):
        """Register service factory."""
        self._factories[service_type] = factory
    
    def register_instance(self, service_type: type, instance: Any):
        """Register service instance."""
        self._services[service_type] = instance
    
    def get_service(self, service_type: type):
        """Get service instance."""
        if service_type in self._services:
            return self._services[service_type]
        
        if service_type in self._factories:
            instance = self._factories[service_type]()
            self._services[service_type] = instance
            return instance
        
        raise ServiceNotRegisteredError(f"Service {service_type} not registered")

# Usage example
container = ServiceContainer()

# Register services
container.register_factory(MemoryService, lambda: MemoryService(memory_config))
container.register_factory(HealthService, lambda: HealthService(health_config))

# Use services
memory_service = container.get_service(MemoryService)
health_service = container.get_service(HealthService)
```

### Configuration Management

#### Environment-Based Configuration

```python
# Configuration hierarchy
@dataclass
class BaseConfig:
    """Base configuration class."""
    
    def __post_init__(self):
        self.validate()
    
    def validate(self):
        """Validate configuration values."""
        pass

@dataclass
class MemoryConfig(BaseConfig):
    """Memory service configuration."""
    
    host: str = "localhost"
    port: int = 8002
    timeout: int = 30
    max_retries: int = 3
    enable_logging: bool = True
    
    def validate(self):
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port: {self.port}")
        if self.timeout <= 0:
            raise ValueError(f"Invalid timeout: {self.timeout}")

# Configuration loading
def load_config() -> MemoryConfig:
    """Load configuration with environment override."""
    
    # Default values
    config_data = {
        "host": "localhost",
        "port": 8002,
        "timeout": 30,
        "max_retries": 3,
        "enable_logging": True
    }
    
    # Environment overrides
    env_overrides = {
        "host": os.getenv("CLAUDE_PM_MEMORY_HOST"),
        "port": int(os.getenv("CLAUDE_PM_MEMORY_PORT", 0)) or None,
        "timeout": int(os.getenv("CLAUDE_PM_MEMORY_TIMEOUT", 0)) or None,
        "max_retries": int(os.getenv("CLAUDE_PM_MEMORY_MAX_RETRIES", 0)) or None,
        "enable_logging": os.getenv("CLAUDE_PM_MEMORY_ENABLE_LOGGING", "").lower() == "true"
    }
    
    # Apply non-None overrides
    for key, value in env_overrides.items():
        if value is not None:
            config_data[key] = value
    
    return MemoryConfig(**config_data)
```

## Development Workflow

### Git Workflow Standards

#### Branch Naming Convention

```bash
# Feature branches
feature/agent-delegation-enhancement
feature/memory-service-optimization

# Bug fix branches
bugfix/connection-pool-leak
bugfix/async-context-cleanup

# Hot fix branches
hotfix/security-vulnerability-fix
hotfix/critical-memory-leak

# Release branches
release/v4.5.1
release/v4.6.0-beta
```

#### Commit Message Standards

```bash
# Format: type(scope): description

# Examples
feat(memory): add batch operation support for memory service
fix(agents): resolve agent communication timeout issues
docs(api): update memory service API documentation
test(integration): add comprehensive agent delegation tests
refactor(core): optimize service discovery mechanism
perf(memory): improve memory retrieval query performance
security(auth): implement secure token validation
```

### Code Review Process

#### Pre-Review Checklist

```python
# Pre-review validation script
def validate_code_changes():
    """Validate code changes before review."""
    
    checks = [
        ("Type hints", check_type_hints),
        ("Documentation", check_documentation),
        ("Tests", check_test_coverage),
        ("Security", check_security_issues),
        ("Performance", check_performance_impact)
    ]
    
    results = []
    for check_name, check_function in checks:
        try:
            result = check_function()
            results.append((check_name, result.passed, result.issues))
        except Exception as e:
            results.append((check_name, False, [f"Check failed: {e}"]))
    
    return results

def check_type_hints() -> ValidationResult:
    """Check if all functions have proper type hints."""
    # Implementation for type hint validation
    pass

def check_documentation() -> ValidationResult:
    """Check if all public functions have docstrings."""
    # Implementation for documentation validation
    pass
```

## Code Quality Standards

### Testing Requirements

#### Test Coverage Standards

```python
# Test coverage requirements
COVERAGE_REQUIREMENTS = {
    "overall": 85,  # Minimum overall coverage
    "core_services": 95,  # Core services must have high coverage
    "agents": 80,  # Agent implementations
    "utilities": 90,  # Utility functions
    "integrations": 75  # External integrations
}

# Test organization
class TestMemoryService:
    """Comprehensive test suite for memory service."""
    
    @pytest.fixture
    async def memory_service(self):
        """Create memory service for testing."""
        config = MemoryConfig(
            host="localhost",
            port=8002,
            timeout=10,
            enable_logging=False
        )
        service = MemoryService(config)
        await service.initialize()
        yield service
        await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_storage_success(self, memory_service):
        """Test successful memory storage."""
        result = await memory_service.store_memory(
            category="test",
            content="Test memory content",
            project_name="test_project"
        )
        
        assert result.success
        assert result.memory_id is not None
        assert len(result.memory_id) > 0
    
    @pytest.mark.asyncio
    async def test_memory_storage_validation(self, memory_service):
        """Test memory storage input validation."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await memory_service.store_memory(
                category="test",
                content="",
                project_name="test_project"
            )
```

### Performance Standards

#### Performance Benchmarks

```python
# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "memory_storage": {
        "max_response_time": 100,  # milliseconds
        "throughput": 1000,  # operations per second
        "memory_usage": 50   # MB maximum
    },
    "agent_delegation": {
        "max_response_time": 500,  # milliseconds
        "concurrent_tasks": 10,    # concurrent delegations
        "memory_usage": 100  # MB maximum
    }
}

@pytest.mark.performance
async def test_memory_service_performance():
    """Test memory service performance benchmarks."""
    
    memory_service = get_memory_service()
    
    # Response time test
    start_time = time.time()
    await memory_service.store_memory(
        category="performance_test",
        content="Performance test content",
        project_name="test_project"
    )
    response_time = (time.time() - start_time) * 1000
    
    assert response_time < PERFORMANCE_BENCHMARKS["memory_storage"]["max_response_time"]
    
    # Throughput test
    start_time = time.time()
    tasks = [
        memory_service.store_memory(
            category="throughput_test",
            content=f"Test content {i}",
            project_name="test_project"
        )
        for i in range(100)
    ]
    await asyncio.gather(*tasks)
    elapsed_time = time.time() - start_time
    throughput = 100 / elapsed_time
    
    assert throughput >= PERFORMANCE_BENCHMARKS["memory_storage"]["throughput"]
```

## Best Practices

### Code Organization

#### Package Structure
```
claude_pm/
├── __init__.py
├── core/                    # Core framework functionality
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── exceptions.py       # Custom exceptions
│   └── logging.py          # Logging setup
├── services/               # Service implementations
│   ├── __init__.py
│   ├── memory_service.py   # Memory service
│   ├── health_service.py   # Health monitoring
│   └── agent_service.py    # Agent management
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py      # Base agent class
│   ├── engineer_agent.py  # Engineer agent
│   └── qa_agent.py        # QA agent
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── async_utils.py     # Async utilities
│   └── validation.py      # Validation functions
└── tests/                  # Test suites
    ├── __init__.py
    ├── test_services/     # Service tests
    ├── test_agents/       # Agent tests
    └── conftest.py        # Test configuration
```

### Documentation Standards

#### API Documentation

```python
def calculate_agent_efficiency(
    successful_tasks: int,
    total_tasks: int,
    average_response_time: float,
    error_rate: float
) -> float:
    """
    Calculate agent efficiency score based on performance metrics.
    
    The efficiency score is calculated using a weighted combination of:
    - Success rate (40% weight)
    - Response time performance (30% weight) 
    - Error rate (30% weight)
    
    Args:
        successful_tasks: Number of successfully completed tasks
        total_tasks: Total number of tasks assigned to agent
        average_response_time: Average response time in seconds
        error_rate: Error rate as percentage (0-100)
    
    Returns:
        Efficiency score from 0.0 to 1.0, where 1.0 is perfect efficiency
    
    Raises:
        ValueError: If total_tasks is 0 or negative
        ValueError: If error_rate is not between 0 and 100
    
    Example:
        >>> calculate_agent_efficiency(95, 100, 2.5, 5.0)
        0.875
        
        >>> calculate_agent_efficiency(80, 100, 5.0, 20.0)
        0.640
    
    Note:
        Response time is normalized against a baseline of 3 seconds.
        Times under 1 second get maximum score, over 10 seconds get minimum.
    """
    if total_tasks <= 0:
        raise ValueError("Total tasks must be positive")
    
    if not 0 <= error_rate <= 100:
        raise ValueError("Error rate must be between 0 and 100")
    
    # Calculate component scores
    success_rate = successful_tasks / total_tasks
    response_score = max(0, min(1, (10 - average_response_time) / 9))
    error_score = (100 - error_rate) / 100
    
    # Weighted efficiency calculation
    efficiency = (
        success_rate * 0.4 +
        response_score * 0.3 +
        error_score * 0.3
    )
    
    return round(efficiency, 3)
```

## Summary

This comprehensive development standards guide provides:

### Core Standards
- **Python Coding Standards**: PEP 8 compliance with framework-specific guidelines
- **Type Safety**: Comprehensive type hints and validation
- **Documentation**: Detailed docstring standards and API documentation
- **Error Handling**: Robust exception hierarchy and error management

### Development Workflow
- **Quick Start Procedures**: 5, 10, and 15-minute setup guides
- **Git Workflow**: Branch naming, commit message standards
- **Code Review Process**: Pre-review validation and quality checks
- **Testing Standards**: Coverage requirements and performance benchmarks

### Architecture Guidelines
- **Service-Oriented Design**: Modular service architecture with dependency injection
- **Configuration Management**: Environment-based configuration with validation
- **Performance Standards**: Benchmarks and optimization guidelines
- **Security Standards**: Secure coding practices and validation

### Best Practices
- **Code Organization**: Logical package structure and module organization
- **Quality Standards**: Comprehensive testing and performance requirements
- **Documentation Standards**: Clear, comprehensive API and code documentation

The Claude PM Framework development standards ensure consistent, maintainable, and high-quality code across all framework components while providing clear guidelines for contributors and maintaining system reliability.

---

**Framework Version**: 4.5.1  
**Last Updated**: 2025-07-11  
**Development Guide Version**: 2.0.0  
**Authority Level**: Complete Development Standards