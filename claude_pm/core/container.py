"""
Dependency Injection Container for Claude PM Framework v0.8.0
============================================================

Implements a comprehensive dependency injection container with support for:
- Singleton and transient service lifetimes
- Service scoping for request-based services
- Factory pattern for complex object creation
- Circular dependency detection and resolution
- Service validation and health monitoring
- Thread-safe operations

Key Features:
- Interface-based service registration
- Automatic dependency resolution
- Service lifecycle management
- Configuration injection
- Error handling and validation
"""

import asyncio
import inspect
import logging
import threading
import weakref
from typing import Any, Dict, Type, TypeVar, Optional, List, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from datetime import datetime
import traceback

from .interfaces import (
    IService, IServiceContainer, IServiceScope, IServiceFactory,
    IConfigurationService, ILogger
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ServiceRegistration:
    """Service registration information."""
    interface: Type
    implementation: Optional[Type] = None
    instance: Optional[Any] = None
    factory: Optional[Callable] = None
    singleton: bool = True
    initialized: bool = False
    dependencies: List[Type] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceScope:
    """Service scope for managing scoped service instances."""
    id: str
    instances: Dict[Type, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected."""
    pass


class ServiceNotRegisteredError(Exception):
    """Raised when requested service is not registered."""
    pass


class ServiceContainer(IServiceContainer):
    """
    Thread-safe dependency injection container with comprehensive service management.
    
    Supports singleton and transient lifetimes, service scoping, factory patterns,
    and automatic dependency resolution with circular dependency detection.
    """
    
    def __init__(self, config: Optional[IConfigurationService] = None):
        """Initialize the service container."""
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scopes: Dict[str, ServiceScope] = {}
        self._building: set = set()  # For circular dependency detection
        self._lock = threading.RLock()
        self._config = config
        self._logger = logger
        
        # Register self as a service
        self.register_instance(IServiceContainer, self)
        
        # Register configuration service if provided
        if config:
            self.register_instance(IConfigurationService, config)
    
    def register_service(self, interface: Type[T], implementation: Type[T], 
                        singleton: bool = True, **metadata) -> None:
        """
        Register a service implementation for an interface.
        
        Args:
            interface: The interface type
            implementation: The implementation type
            singleton: Whether to use singleton lifetime
            **metadata: Additional metadata for the service
        """
        with self._lock:
            # Validate that implementation implements interface
            if not self._implements_interface(implementation, interface):
                raise ValueError(f"{implementation} does not implement {interface}")
            
            # Extract dependencies from constructor
            dependencies = self._extract_dependencies(implementation)
            
            registration = ServiceRegistration(
                interface=interface,
                implementation=implementation,
                singleton=singleton,
                dependencies=dependencies,
                metadata=metadata
            )
            
            self._registrations[interface] = registration
            
            self._logger.debug(
                f"Registered service: {interface.__name__} -> {implementation.__name__} "
                f"(singleton={singleton}, dependencies={[d.__name__ for d in dependencies]})"
            )
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        Register a service instance for an interface.
        
        Args:
            interface: The interface type
            instance: The service instance
        """
        with self._lock:
            registration = ServiceRegistration(
                interface=interface,
                instance=instance,
                singleton=True,
                initialized=True
            )
            
            self._registrations[interface] = registration
            self._singletons[interface] = instance
            
            self._logger.debug(f"Registered instance: {interface.__name__}")
    
    def register_factory(self, interface: Type[T], factory: Callable[..., T], 
                        singleton: bool = False, **metadata) -> None:
        """
        Register a factory function for an interface.
        
        Args:
            interface: The interface type
            factory: Factory function that creates instances
            singleton: Whether to cache factory results
            **metadata: Additional metadata for the service
        """
        with self._lock:
            # Extract dependencies from factory function
            dependencies = self._extract_dependencies(factory)
            
            registration = ServiceRegistration(
                interface=interface,
                factory=factory,
                singleton=singleton,
                dependencies=dependencies,
                metadata=metadata
            )
            
            self._registrations[interface] = registration
            
            self._logger.debug(
                f"Registered factory: {interface.__name__} "
                f"(singleton={singleton}, dependencies={[d.__name__ for d in dependencies]})"
            )
    
    def get_service(self, interface: Type[T]) -> T:
        """
        Get service instance for interface.
        
        Args:
            interface: The interface type to resolve
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotRegisteredError: If service is not registered
            CircularDependencyError: If circular dependency is detected
        """
        with self._lock:
            if interface not in self._registrations:
                raise ServiceNotRegisteredError(f"Service not registered: {interface}")
            
            registration = self._registrations[interface]
            
            # Return existing singleton if available
            if registration.singleton and interface in self._singletons:
                return self._singletons[interface]
            
            # Check for circular dependency
            if interface in self._building:
                chain = " -> ".join([t.__name__ for t in self._building]) + f" -> {interface.__name__}"
                raise CircularDependencyError(f"Circular dependency detected: {chain}")
            
            try:
                self._building.add(interface)
                instance = self._create_instance(registration)
                
                # Cache singleton
                if registration.singleton:
                    self._singletons[interface] = instance
                    registration.initialized = True
                
                return instance
                
            finally:
                self._building.discard(interface)
    
    def has_service(self, interface: Type) -> bool:
        """
        Check if service is registered for interface.
        
        Args:
            interface: The interface type to check
            
        Returns:
            True if service is registered
        """
        with self._lock:
            return interface in self._registrations
    
    def create_scope(self) -> 'ServiceContainerScope':
        """
        Create a new service scope for scoped services.
        
        Returns:
            New service scope
        """
        scope_id = f"scope_{datetime.now().timestamp()}_{id(self)}"
        scope = ServiceScope(id=scope_id)
        
        with self._lock:
            self._scopes[scope_id] = scope
        
        return ServiceContainerScope(self, scope)
    
    def get_registrations(self) -> Dict[Type, ServiceRegistration]:
        """Get all service registrations."""
        with self._lock:
            return self._registrations.copy()
    
    def validate_registrations(self) -> List[str]:
        """
        Validate all service registrations for dependency issues.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        with self._lock:
            for interface, registration in self._registrations.items():
                try:
                    # Check if all dependencies are registered
                    for dependency in registration.dependencies:
                        if dependency not in self._registrations:
                            errors.append(
                                f"Service {interface.__name__} has unregistered dependency: {dependency.__name__}"
                            )
                    
                    # Try to resolve the service (without building)
                    if not registration.initialized and registration.instance is None:
                        # Check for potential circular dependencies
                        visited = set()
                        if self._has_circular_dependency(interface, visited):
                            errors.append(f"Circular dependency detected for service: {interface.__name__}")
                
                except Exception as e:
                    errors.append(f"Error validating service {interface.__name__}: {str(e)}")
        
        return errors
    
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """Create service instance from registration."""
        try:
            if registration.instance is not None:
                return registration.instance
            
            if registration.factory is not None:
                return self._create_from_factory(registration)
            
            if registration.implementation is not None:
                return self._create_from_implementation(registration)
            
            raise ValueError(f"Invalid registration: no instance, factory, or implementation")
            
        except Exception as e:
            self._logger.error(
                f"Failed to create instance for {registration.interface.__name__}: {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            raise
    
    def _create_from_factory(self, registration: ServiceRegistration) -> Any:
        """Create instance using factory function."""
        factory = registration.factory
        dependencies = self._resolve_dependencies(registration.dependencies)
        
        # Call factory with resolved dependencies
        sig = inspect.signature(factory)
        kwargs = {}
        
        for param_name, param in sig.parameters.items():
            if param.annotation in dependencies:
                kwargs[param_name] = dependencies[param.annotation]
        
        return factory(**kwargs)
    
    def _create_from_implementation(self, registration: ServiceRegistration) -> Any:
        """Create instance from implementation class."""
        implementation = registration.implementation
        dependencies = self._resolve_dependencies(registration.dependencies)
        
        # Get constructor signature
        sig = inspect.signature(implementation.__init__)
        kwargs = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            if param.annotation in dependencies:
                kwargs[param_name] = dependencies[param.annotation]
            elif param.annotation == IConfigurationService and self._config:
                kwargs[param_name] = self._config
        
        return implementation(**kwargs)
    
    def _resolve_dependencies(self, dependencies: List[Type]) -> Dict[Type, Any]:
        """Resolve all dependencies for a service."""
        resolved = {}
        
        for dependency in dependencies:
            resolved[dependency] = self.get_service(dependency)
        
        return resolved
    
    def _extract_dependencies(self, target: Union[Type, Callable]) -> List[Type]:
        """Extract dependencies from constructor or function signature."""
        dependencies = []
        
        try:
            if inspect.isclass(target):
                sig = inspect.signature(target.__init__)
            else:
                sig = inspect.signature(target)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # Check if parameter has type annotation
                if param.annotation != inspect.Parameter.empty:
                    annotation = param.annotation
                    
                    # Handle Optional types
                    if hasattr(annotation, '__origin__') and annotation.__origin__ is Union:
                        args = annotation.__args__
                        if len(args) == 2 and type(None) in args:
                            # This is Optional[T]
                            non_none_type = args[0] if args[1] is type(None) else args[1]
                            if self._is_service_interface(non_none_type):
                                dependencies.append(non_none_type)
                    elif self._is_service_interface(annotation):
                        dependencies.append(annotation)
        
        except Exception as e:
            self._logger.warning(f"Failed to extract dependencies from {target}: {e}")
        
        return dependencies
    
    def _implements_interface(self, implementation: Type, interface: Type) -> bool:
        """Check if implementation implements the interface."""
        if interface == implementation:
            return True
        
        # Check if implementation is a subclass of interface
        try:
            return issubclass(implementation, interface)
        except TypeError:
            # interface might not be a class (e.g., typing constructs)
            return False
    
    def _is_service_interface(self, annotation: Type) -> bool:
        """Check if annotation represents a service interface."""
        if annotation is None:
            return False
        
        try:
            # Check if it's a registered interface
            if annotation in self._registrations:
                return True
            
            # Check if it inherits from known service interfaces
            service_interfaces = (IService, IConfigurationService, ILogger)
            return any(issubclass(annotation, iface) for iface in service_interfaces)
        
        except TypeError:
            return False
    
    def _has_circular_dependency(self, interface: Type, visited: set) -> bool:
        """Check for circular dependencies in registration graph."""
        if interface in visited:
            return True
        
        if interface not in self._registrations:
            return False
        
        visited.add(interface)
        registration = self._registrations[interface]
        
        for dependency in registration.dependencies:
            if self._has_circular_dependency(dependency, visited):
                return True
        
        visited.remove(interface)
        return False
    
    def dispose(self) -> None:
        """Dispose of all services and clean up resources."""
        with self._lock:
            # Dispose of all scopes
            for scope in self._scopes.values():
                if scope.active:
                    scope.active = False
                    for instance in scope.instances.values():
                        if hasattr(instance, 'dispose'):
                            try:
                                instance.dispose()
                            except Exception as e:
                                self._logger.error(f"Error disposing scoped service: {e}")
            
            # Dispose of singletons
            for instance in self._singletons.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception as e:
                        self._logger.error(f"Error disposing singleton service: {e}")
            
            # Clear all collections
            self._scopes.clear()
            self._singletons.clear()
            self._registrations.clear()
            self._building.clear()


class ServiceContainerScope(IServiceScope):
    """Service scope implementation for managing scoped service instances."""
    
    def __init__(self, container: ServiceContainer, scope: ServiceScope):
        """Initialize the service scope."""
        self._container = container
        self._scope = scope
        self._disposed = False
    
    def get_service(self, interface: Type[T]) -> T:
        """
        Get service instance within this scope.
        
        Args:
            interface: The interface type to resolve
            
        Returns:
            Service instance
        """
        if self._disposed:
            raise RuntimeError("Cannot get service from disposed scope")
        
        if not self._scope.active:
            raise RuntimeError("Scope is no longer active")
        
        # Check if we have a scoped instance
        if interface in self._scope.instances:
            return self._scope.instances[interface]
        
        # Get from container and cache in scope
        instance = self._container.get_service(interface)
        self._scope.instances[interface] = instance
        
        return instance
    
    def dispose(self) -> None:
        """Dispose of all scoped services."""
        if self._disposed:
            return
        
        self._disposed = True
        self._scope.active = False
        
        # Dispose of scoped instances
        for instance in self._scope.instances.values():
            if hasattr(instance, 'dispose'):
                try:
                    instance.dispose()
                except Exception as e:
                    logger.error(f"Error disposing scoped service: {e}")
        
        # Remove from container
        with self._container._lock:
            if self._scope.id in self._container._scopes:
                del self._container._scopes[self._scope.id]


# Factory implementations

class ServiceFactory(IServiceFactory):
    """Generic service factory implementation."""
    
    def __init__(self, container: IServiceContainer, service_type: Type):
        """Initialize the service factory."""
        self._container = container
        self._service_type = service_type
    
    def create(self, *args, **kwargs) -> Any:
        """Create a new service instance."""
        if args or kwargs:
            # If arguments provided, create directly
            return self._service_type(*args, **kwargs)
        else:
            # Use container for dependency injection
            return self._container.get_service(self._service_type)
    
    def can_create(self, service_type: Type) -> bool:
        """Check if factory can create service type."""
        return service_type == self._service_type or issubclass(service_type, self._service_type)


# Utility functions and decorators

def injectable(interface: Type = None, singleton: bool = True):
    """
    Decorator to mark a class as injectable service.
    
    Args:
        interface: The interface this service implements
        singleton: Whether to use singleton lifetime
    """
    def decorator(cls):
        # Store injection metadata
        cls._injection_interface = interface or cls
        cls._injection_singleton = singleton
        return cls
    
    return decorator


def inject(interface: Type):
    """
    Decorator to inject a service dependency.
    
    Args:
        interface: The interface to inject
    """
    def decorator(func):
        if not hasattr(func, '_injected_dependencies'):
            func._injected_dependencies = []
        func._injected_dependencies.append(interface)
        return func
    
    return decorator


@contextmanager
def service_scope(container: IServiceContainer):
    """
    Context manager for creating and disposing service scopes.
    
    Args:
        container: The service container
    """
    scope = container.create_scope()
    try:
        yield scope
    finally:
        scope.dispose()


# Default container instance for convenience
_default_container: Optional[ServiceContainer] = None
_container_lock = threading.Lock()


def get_default_container() -> ServiceContainer:
    """Get the default service container instance."""
    global _default_container
    
    if _default_container is None:
        with _container_lock:
            if _default_container is None:
                _default_container = ServiceContainer()
    
    return _default_container


def configure_default_container(config: Optional[IConfigurationService] = None) -> ServiceContainer:
    """Configure and get the default service container."""
    global _default_container
    
    with _container_lock:
        _default_container = ServiceContainer(config)
    
    return _default_container


def reset_default_container() -> None:
    """Reset the default container (mainly for testing)."""
    global _default_container
    
    with _container_lock:
        if _default_container:
            _default_container.dispose()
        _default_container = None