"""
Core Service Interfaces for Claude PM Framework v0.8.0
======================================================

This module defines the core interfaces for the framework's service-oriented architecture.
All services implement these interfaces to ensure consistency, testability, and loose coupling.

Key Features:
- Service lifecycle management
- Configuration abstraction
- Health monitoring and metrics
- Cache management
- Agent registry operations
- Dependency injection support
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import asyncio


@dataclass
class ServiceHealth:
    """Standard health status for all services."""
    status: str  # healthy, degraded, unhealthy, unknown
    message: str
    timestamp: str
    metrics: Dict[str, Any]
    checks: Dict[str, bool]


@dataclass
class ServiceMetrics:
    """Standard metrics collection for all services."""
    requests_total: int = 0
    requests_failed: int = 0
    response_time_avg: float = 0.0
    uptime_seconds: int = 0
    memory_usage_mb: float = 0.0
    custom_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}


# Core Infrastructure Interfaces

class IService(ABC):
    """Base interface for all framework services."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Service name for identification."""
        pass
    
    @property
    @abstractmethod
    def running(self) -> bool:
        """Check if service is currently running."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the service."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the service gracefully."""
        pass
    
    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """Perform comprehensive health check."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> ServiceMetrics:
        """Get current service metrics."""
        pass


class IConfigurationService(ABC):
    """Interface for configuration management services."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        pass
    
    @abstractmethod
    def validate(self, schema: Dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        pass
    
    @abstractmethod
    def load_file(self, file_path: Union[str, Path]) -> None:
        """Load configuration from file."""
        pass
    
    @abstractmethod
    def save(self, file_path: Union[str, Path], format: str = "json") -> None:
        """Save configuration to file."""
        pass


class IHealthMonitor(ABC):
    """Interface for health monitoring services."""
    
    @abstractmethod
    async def register_service(self, service: IService) -> None:
        """Register a service for monitoring."""
        pass
    
    @abstractmethod
    async def unregister_service(self, service_name: str) -> None:
        """Unregister a service from monitoring."""
        pass
    
    @abstractmethod
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all registered services."""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> ServiceHealth:
        """Get overall system health status."""
        pass


class ICacheService(ABC):
    """Interface for caching services."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set cached value with optional TTL."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete cached value."""
        pass
    
    @abstractmethod
    def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        pass


# Agent-Specific Interfaces

@dataclass
class AgentMetadata:
    """Standard agent metadata structure."""
    name: str
    type: str
    path: str
    tier: str
    description: Optional[str] = None
    version: Optional[str] = None
    capabilities: List[str] = None
    specializations: List[str] = None
    frameworks: List[str] = None
    domains: List[str] = None
    roles: List[str] = None
    last_modified: Optional[float] = None
    validated: bool = False
    validation_score: float = 0.0
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.specializations is None:
            self.specializations = []
        if self.frameworks is None:
            self.frameworks = []
        if self.domains is None:
            self.domains = []
        if self.roles is None:
            self.roles = []


class IAgentRegistry(ABC):
    """Interface for agent discovery and management."""
    
    @abstractmethod
    async def discover_agents(self, force_refresh: bool = False) -> Dict[str, AgentMetadata]:
        """Discover all available agents across hierarchy."""
        pass
    
    @abstractmethod
    async def get_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """Get specific agent metadata."""
        pass
    
    @abstractmethod
    async def list_agents(self, agent_type: Optional[str] = None, tier: Optional[str] = None) -> List[AgentMetadata]:
        """List agents with optional filtering."""
        pass
    
    @abstractmethod
    async def get_specialized_agents(self, agent_type: str) -> List[AgentMetadata]:
        """Get all agents of a specific specialized type."""
        pass
    
    @abstractmethod
    async def search_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """Search agents by specific capability."""
        pass
    
    @abstractmethod
    async def refresh_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """Refresh specific agent metadata."""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear discovery cache and force refresh."""
        pass


# Service Management Interfaces

class IServiceContainer(ABC):
    """Interface for dependency injection container."""
    
    @abstractmethod
    def register_service(self, interface: type, implementation: type, singleton: bool = True) -> None:
        """Register a service implementation for an interface."""
        pass
    
    @abstractmethod
    def register_instance(self, interface: type, instance: Any) -> None:
        """Register a service instance for an interface."""
        pass
    
    @abstractmethod
    def get_service(self, interface: type) -> Any:
        """Get service instance for interface."""
        pass
    
    @abstractmethod
    def has_service(self, interface: type) -> bool:
        """Check if service is registered for interface."""
        pass
    
    @abstractmethod
    def create_scope(self) -> 'IServiceScope':
        """Create a new service scope for scoped services."""
        pass


class IServiceScope(ABC):
    """Interface for service scope management."""
    
    @abstractmethod
    def get_service(self, interface: type) -> Any:
        """Get service instance within this scope."""
        pass
    
    @abstractmethod
    def dispose(self) -> None:
        """Dispose of all scoped services."""
        pass


class IServiceFactory(ABC):
    """Interface for service factories."""
    
    @abstractmethod
    def create(self, *args, **kwargs) -> Any:
        """Create a new service instance."""
        pass
    
    @abstractmethod
    def can_create(self, service_type: type) -> bool:
        """Check if factory can create service type."""
        pass


# Logging and Error Handling Interfaces

class ILogger(ABC):
    """Interface for structured logging services."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        pass


class IErrorHandler(ABC):
    """Interface for centralized error handling."""
    
    @abstractmethod
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Handle an error with context."""
        pass
    
    @abstractmethod
    def register_handler(self, error_type: type, handler: callable) -> None:
        """Register error handler for specific error type."""
        pass


# Event and Notification Interfaces

class IEventBus(ABC):
    """Interface for event publishing and subscription."""
    
    @abstractmethod
    async def publish(self, event: str, data: Any) -> None:
        """Publish an event."""
        pass
    
    @abstractmethod
    def subscribe(self, event: str, handler: callable) -> None:
        """Subscribe to an event."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event: str, handler: callable) -> None:
        """Unsubscribe from an event."""
        pass


# Data Access Interfaces

class IRepository(ABC):
    """Base interface for data repositories."""
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[Any]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def save(self, entity: Any) -> Any:
        """Save entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete entity by ID."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Any]:
        """Find all entities."""
        pass


class IUnitOfWork(ABC):
    """Interface for unit of work pattern."""
    
    @abstractmethod
    async def begin(self) -> None:
        """Begin transaction."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction."""
        pass


# Framework-Specific Service Interfaces

class IParentDirectoryManager(ABC):
    """Interface for parent directory management."""
    
    @abstractmethod
    async def install_template(self, target_directory: Path, template_id: str, 
                              variables: Optional[Dict[str, Any]] = None, 
                              force: bool = False) -> bool:
        """Install template to parent directory."""
        pass
    
    @abstractmethod
    async def get_directory_status(self, target_directory: Path) -> Dict[str, Any]:
        """Get parent directory status."""
        pass
    
    @abstractmethod
    async def backup_directory(self, target_directory: Path) -> Optional[Path]:
        """Create backup of parent directory."""
        pass


class IAgentPromptBuilder(ABC):
    """Interface for agent prompt building."""
    
    @abstractmethod
    async def build_prompt(self, agent_name: str, context: Dict[str, Any]) -> str:
        """Build prompt for agent."""
        pass
    
    @abstractmethod
    async def get_prompt_template(self, agent_name: str) -> Optional[str]:
        """Get prompt template for agent."""
        pass
    
    @abstractmethod
    def register_template(self, agent_name: str, template: str) -> None:
        """Register prompt template for agent."""
        pass


# Integration and Extension Interfaces

class IPluginManager(ABC):
    """Interface for plugin management."""
    
    @abstractmethod
    def load_plugin(self, plugin_path: Path) -> None:
        """Load plugin from path."""
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> None:
        """Unload plugin by name."""
        pass
    
    @abstractmethod
    def get_plugins(self) -> List[Dict[str, Any]]:
        """Get list of loaded plugins."""
        pass


class ITaskExecutor(ABC):
    """Interface for task execution."""
    
    @abstractmethod
    async def execute_task(self, task_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a task with parameters."""
        pass
    
    @abstractmethod
    def register_task(self, task_name: str, task_handler: callable) -> None:
        """Register a task handler."""
        pass
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a running task."""
        pass


# Validation and Quality Assurance Interfaces

class IValidator(ABC):
    """Interface for validation services."""
    
    @abstractmethod
    def validate(self, data: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate data against schema."""
        pass
    
    @abstractmethod
    def register_validator(self, data_type: str, validator: callable) -> None:
        """Register custom validator."""
        pass


class IQualityMonitor(ABC):
    """Interface for quality monitoring."""
    
    @abstractmethod
    async def check_code_quality(self, file_path: Path) -> Dict[str, Any]:
        """Check code quality metrics."""
        pass
    
    @abstractmethod
    async def check_test_coverage(self, project_path: Path) -> Dict[str, Any]:
        """Check test coverage metrics."""
        pass
    
    @abstractmethod
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get overall quality metrics."""
        pass