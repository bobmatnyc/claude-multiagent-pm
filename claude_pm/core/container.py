"""
Dependency Injection Container for Claude PM Framework
====================================================

Phase 1 Refactoring: Service-oriented architecture with dependency injection
- ServiceContainer: Core DI container implementation
- ServiceRegistration: Service metadata and lifecycle management  
- ServiceScope: Singleton and transient service management
- DependencyResolver: Automatic dependency resolution with circular detection

This container reduces complexity by centralizing service creation and management,
enabling loose coupling and testability improvements.

Key Features:
- Automatic dependency injection via constructor parameters
- Singleton and transient service lifetimes
- Circular dependency detection
- Service factory support
- Interface-based registration
- Lazy loading and initialization
"""

import asyncio
import inspect
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Callable, get_type_hints
from weakref import WeakValueDictionary

from .interfaces import IServiceContainer, IStructuredLogger

T = TypeVar('T')


class ServiceScope(Enum):
    """Service lifetime scopes"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"  # Per-request scope (future implementation)


@dataclass
class ServiceRegistration:
    """Service registration metadata"""
    service_type: Type
    implementation_type: Optional[Type] = None
    instance: Optional[Any] = None
    factory: Optional[Callable] = None
    scope: ServiceScope = ServiceScope.SINGLETON
    is_interface: bool = False
    dependencies: List[Type] = None
    initialized: bool = False
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected"""
    
    def __init__(self, dependency_chain: List[Type]):
        self.dependency_chain = dependency_chain
        chain_names = " -> ".join(t.__name__ for t in dependency_chain)
        super().__init__(f"Circular dependency detected: {chain_names}")


class ServiceNotFoundError(Exception):
    """Raised when a service cannot be resolved"""
    
    def __init__(self, service_type: Type):
        super().__init__(f"Service not registered: {service_type.__name__}")


class ServiceContainer(IServiceContainer):
    """
    Dependency injection container with automatic dependency resolution
    
    Features:
    - Constructor injection via type hints
    - Singleton and transient lifetimes
    - Circular dependency detection
    - Interface-based registration
    - Factory method support
    - Thread-safe operations
    """
    
    def __init__(self, logger: Optional[IStructuredLogger] = None):
        """Initialize service container"""
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._resolving: Set[Type] = set()  # Track services being resolved
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._logger = logger
        
        # Register the container itself
        self.register_instance(IServiceContainer, self)
        self.register_instance(ServiceContainer, self)
    
    def register(self, service_type: Type, implementation: Type, singleton: bool = True) -> None:
        """
        Register a service implementation
        
        Args:
            service_type: Interface or abstract class type
            implementation: Concrete implementation type
            singleton: Whether to use singleton lifetime
        """
        with self._lock:
            scope = ServiceScope.SINGLETON if singleton else ServiceScope.TRANSIENT
            dependencies = self._extract_dependencies(implementation)
            
            registration = ServiceRegistration(
                service_type=service_type,
                implementation_type=implementation,
                scope=scope,
                is_interface=service_type != implementation,
                dependencies=dependencies
            )
            
            self._registrations[service_type] = registration
            
            if self._logger:
                self._logger.debug(
                    f"Registered service: {service_type.__name__} -> {implementation.__name__}",
                    service_type=service_type.__name__,
                    implementation=implementation.__name__,
                    scope=scope.value,
                    dependencies=[d.__name__ for d in dependencies]
                )
    
    def register_instance(self, service_type: Type, instance: Any) -> None:
        """
        Register a service instance
        
        Args:
            service_type: Service type
            instance: Service instance
        """
        with self._lock:
            registration = ServiceRegistration(
                service_type=service_type,
                instance=instance,
                scope=ServiceScope.SINGLETON,
                initialized=True
            )
            
            self._registrations[service_type] = registration
            self._instances[service_type] = instance
            
            if self._logger:
                self._logger.debug(
                    f"Registered instance: {service_type.__name__}",
                    service_type=service_type.__name__,
                    instance_type=type(instance).__name__
                )
    
    def register_factory(self, service_type: Type, factory: Callable, singleton: bool = True) -> None:
        """
        Register a service factory
        
        Args:
            service_type: Service type
            factory: Factory function
            singleton: Whether to use singleton lifetime
        """
        with self._lock:
            scope = ServiceScope.SINGLETON if singleton else ServiceScope.TRANSIENT
            dependencies = self._extract_dependencies(factory)
            
            registration = ServiceRegistration(
                service_type=service_type,
                factory=factory,
                scope=scope,
                dependencies=dependencies
            )
            
            self._registrations[service_type] = registration
            
            if self._logger:
                self._logger.debug(
                    f"Registered factory: {service_type.__name__}",
                    service_type=service_type.__name__,
                    factory=factory.__name__,
                    scope=scope.value
                )
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service by type
        
        Args:
            service_type: Type to resolve
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency detected
        """
        with self._lock:
            return self._resolve_service(service_type, [])
    
    def resolve_all(self, service_type: Type) -> List[Any]:
        """
        Resolve all implementations of a service type
        
        Args:
            service_type: Service type
            
        Returns:
            List of service instances
        """
        with self._lock:
            instances = []
            
            for registered_type, registration in self._registrations.items():
                # Check if registered type is subclass of requested type
                if (registered_type == service_type or 
                    (inspect.isclass(registered_type) and 
                     issubclass(registered_type, service_type))):
                    
                    instance = self._resolve_service(registered_type, [])
                    instances.append(instance)
            
            return instances
    
    def is_registered(self, service_type: Type) -> bool:
        """
        Check if a service type is registered
        
        Args:
            service_type: Service type to check
            
        Returns:
            True if registered, False otherwise
        """
        with self._lock:
            return service_type in self._registrations
    
    def unregister(self, service_type: Type) -> bool:
        """
        Unregister a service type
        
        Args:
            service_type: Service type to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        with self._lock:
            if service_type in self._registrations:
                del self._registrations[service_type]
                
                # Remove instance if cached
                if service_type in self._instances:
                    del self._instances[service_type]
                
                if self._logger:
                    self._logger.debug(
                        f"Unregistered service: {service_type.__name__}",
                        service_type=service_type.__name__
                    )
                
                return True
            return False
    
    def clear(self) -> None:
        """Clear all registrations except the container itself"""
        with self._lock:
            # Keep container registration
            container_reg = self._registrations.get(ServiceContainer)
            interface_reg = self._registrations.get(IServiceContainer)
            
            self._registrations.clear()
            self._instances.clear()
            
            # Restore container registrations
            if container_reg:
                self._registrations[ServiceContainer] = container_reg
                self._instances[ServiceContainer] = self
            if interface_reg:
                self._registrations[IServiceContainer] = interface_reg
                self._instances[IServiceContainer] = self
            
            if self._logger:
                self._logger.info("Service container cleared")
    
    def get_registration(self, service_type: Type) -> Optional[ServiceRegistration]:
        """Get service registration metadata"""
        with self._lock:
            return self._registrations.get(service_type)
    
    def get_registrations(self) -> Dict[Type, ServiceRegistration]:
        """Get all service registrations"""
        with self._lock:
            return self._registrations.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get container statistics"""
        with self._lock:
            singleton_count = sum(1 for r in self._registrations.values() 
                                if r.scope == ServiceScope.SINGLETON)
            transient_count = sum(1 for r in self._registrations.values() 
                                if r.scope == ServiceScope.TRANSIENT)
            interface_count = sum(1 for r in self._registrations.values() if r.is_interface)
            
            return {
                "total_registrations": len(self._registrations),
                "singleton_services": singleton_count,
                "transient_services": transient_count,
                "interface_registrations": interface_count,
                "cached_instances": len(self._instances),
                "currently_resolving": len(self._resolving)
            }
    
    # Private implementation methods
    
    def _resolve_service(self, service_type: Type, dependency_chain: List[Type]) -> Any:
        """
        Internal service resolution with circular dependency detection
        
        Args:
            service_type: Type to resolve
            dependency_chain: Current dependency chain for circular detection
            
        Returns:
            Service instance
        """
        # Check for circular dependency
        if service_type in dependency_chain:
            circular_chain = dependency_chain + [service_type]
            raise CircularDependencyError(circular_chain)
        
        # Check if service is registered
        if service_type not in self._registrations:
            raise ServiceNotFoundError(service_type)
        
        registration = self._registrations[service_type]
        
        # Return existing instance for singletons
        if (registration.scope == ServiceScope.SINGLETON and 
            service_type in self._instances):
            return self._instances[service_type]
        
        # Create new instance
        new_dependency_chain = dependency_chain + [service_type]
        
        try:
            if registration.instance is not None:
                # Pre-created instance
                instance = registration.instance
            elif registration.factory is not None:
                # Factory method
                instance = self._create_from_factory(registration.factory, new_dependency_chain)
            elif registration.implementation_type is not None:
                # Constructor injection
                instance = self._create_from_constructor(registration.implementation_type, new_dependency_chain)
            else:
                raise ServiceNotFoundError(service_type)
            
            # Cache singleton instances
            if registration.scope == ServiceScope.SINGLETON:
                self._instances[service_type] = instance
                registration.initialized = True
            
            if self._logger:
                self._logger.debug(
                    f"Created service instance: {service_type.__name__}",
                    service_type=service_type.__name__,
                    scope=registration.scope.value,
                    dependency_chain=[t.__name__ for t in new_dependency_chain]
                )
            
            return instance
            
        except Exception as e:
            if self._logger:
                self._logger.error(
                    f"Failed to create service: {service_type.__name__}",
                    service_type=service_type.__name__,
                    error=str(e),
                    dependency_chain=[t.__name__ for t in new_dependency_chain]
                )
            raise
    
    def _create_from_constructor(self, implementation_type: Type, dependency_chain: List[Type]) -> Any:
        """Create service instance via constructor injection"""
        constructor = implementation_type.__init__
        dependencies = self._resolve_dependencies(constructor, dependency_chain)
        
        return implementation_type(**dependencies)
    
    def _create_from_factory(self, factory: Callable, dependency_chain: List[Type]) -> Any:
        """Create service instance via factory method"""
        dependencies = self._resolve_dependencies(factory, dependency_chain)
        
        return factory(**dependencies)
    
    def _resolve_dependencies(self, callable_obj: Callable, dependency_chain: List[Type]) -> Dict[str, Any]:
        """Resolve dependencies for a callable (constructor or factory)"""
        dependencies = {}
        
        # Get type hints for parameters
        type_hints = get_type_hints(callable_obj)
        signature = inspect.signature(callable_obj)
        
        for param_name, param in signature.parameters.items():
            # Skip 'self' parameter
            if param_name == 'self':
                continue
            
            # Get parameter type from type hints
            if param_name in type_hints:
                param_type = type_hints[param_name]
                
                # Handle Optional types
                if hasattr(param_type, '__origin__') and param_type.__origin__ is Union:
                    # Get the non-None type from Optional[T]
                    args = param_type.__args__
                    param_type = next((arg for arg in args if arg is not type(None)), param_type)
                
                # Try to resolve the dependency
                if self.is_registered(param_type):
                    dependencies[param_name] = self._resolve_service(param_type, dependency_chain)
                elif param.default is not param.empty:
                    # Use default value if available
                    dependencies[param_name] = param.default
                else:
                    # Required dependency not registered
                    if self._logger:
                        self._logger.warning(
                            f"Required dependency not registered: {param_type.__name__}",
                            parameter=param_name,
                            type=param_type.__name__
                        )
        
        return dependencies
    
    def _extract_dependencies(self, target: Callable) -> List[Type]:
        """Extract dependency types from a callable"""
        dependencies = []
        
        try:
            type_hints = get_type_hints(target)
            signature = inspect.signature(target)
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                if param_name in type_hints:
                    param_type = type_hints[param_name]
                    
                    # Handle Optional types
                    if hasattr(param_type, '__origin__') and param_type.__origin__ is Union:
                        args = param_type.__args__
                        param_type = next((arg for arg in args if arg is not type(None)), param_type)
                    
                    dependencies.append(param_type)
        
        except Exception as e:
            if self._logger:
                self._logger.warning(
                    f"Failed to extract dependencies for {target.__name__}: {e}",
                    target=target.__name__,
                    error=str(e)
                )
        
        return dependencies


class ServiceContainerBuilder:
    """Builder for configuring service container"""
    
    def __init__(self):
        self._container = ServiceContainer()
        self._registrations: List[Callable[[ServiceContainer], None]] = []
    
    def add_singleton(self, service_type: Type, implementation: Type) -> 'ServiceContainerBuilder':
        """Add singleton service registration"""
        def register(container: ServiceContainer):
            container.register(service_type, implementation, singleton=True)
        
        self._registrations.append(register)
        return self
    
    def add_transient(self, service_type: Type, implementation: Type) -> 'ServiceContainerBuilder':
        """Add transient service registration"""
        def register(container: ServiceContainer):
            container.register(service_type, implementation, singleton=False)
        
        self._registrations.append(register)
        return self
    
    def add_instance(self, service_type: Type, instance: Any) -> 'ServiceContainerBuilder':
        """Add service instance"""
        def register(container: ServiceContainer):
            container.register_instance(service_type, instance)
        
        self._registrations.append(register)
        return self
    
    def add_factory(self, service_type: Type, factory: Callable, singleton: bool = True) -> 'ServiceContainerBuilder':
        """Add factory registration"""
        def register(container: ServiceContainer):
            container.register_factory(service_type, factory, singleton)
        
        self._registrations.append(register)
        return self
    
    def build(self) -> ServiceContainer:
        """Build configured service container"""
        for registration in self._registrations:
            registration(self._container)
        
        return self._container


# Module-level container instance
_default_container: Optional[ServiceContainer] = None
_container_lock = threading.Lock()


def get_container() -> ServiceContainer:
    """Get the default service container instance"""
    global _default_container
    
    if _default_container is None:
        with _container_lock:
            if _default_container is None:
                _default_container = ServiceContainer()
    
    return _default_container


def set_container(container: ServiceContainer) -> None:
    """Set the default service container instance"""
    global _default_container
    
    with _container_lock:
        _default_container = container


def reset_container() -> None:
    """Reset the default container (useful for testing)"""
    global _default_container
    
    with _container_lock:
        _default_container = None


# Convenience functions for the default container
def register(service_type: Type, implementation: Type, singleton: bool = True) -> None:
    """Register service in default container"""
    get_container().register(service_type, implementation, singleton)


def register_instance(service_type: Type, instance: Any) -> None:
    """Register instance in default container"""
    get_container().register_instance(service_type, instance)


def register_factory(service_type: Type, factory: Callable, singleton: bool = True) -> None:
    """Register factory in default container"""
    get_container().register_factory(service_type, factory, singleton)


def resolve(service_type: Type[T]) -> T:
    """Resolve service from default container"""
    return get_container().resolve(service_type)


def resolve_all(service_type: Type) -> List[Any]:
    """Resolve all services from default container"""
    return get_container().resolve_all(service_type)


def is_registered(service_type: Type) -> bool:
    """Check if service is registered in default container"""
    return get_container().is_registered(service_type)