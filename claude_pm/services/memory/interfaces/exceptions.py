"""
Memory Service Exceptions

This module defines custom exceptions for the memory service.
"""


class MemoryServiceError(Exception):
    """Base exception for memory service errors."""
    
    def __init__(self, message: str, backend_name: str = None, operation: str = None):
        self.message = message
        self.backend_name = backend_name
        self.operation = operation
        super().__init__(self.message)
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.backend_name:
            parts.append(f"Backend: {self.backend_name}")
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        return " | ".join(parts)


class BackendError(MemoryServiceError):
    """Exception raised when a backend operation fails."""
    
    def __init__(self, message: str, backend_name: str = None, operation: str = None, 
                 original_error: Exception = None):
        super().__init__(message, backend_name, operation)
        self.original_error = original_error
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.original_error:
            return f"{base_str} | Original Error: {self.original_error}"
        return base_str


class CircuitBreakerOpenError(MemoryServiceError):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, message: str = "Circuit breaker is open", backend_name: str = None):
        super().__init__(message, backend_name, "circuit_breaker")


class ConfigurationError(MemoryServiceError):
    """Exception raised when there's a configuration error."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, operation="configuration")
        self.config_key = config_key
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.config_key:
            return f"{base_str} | Config Key: {self.config_key}"
        return base_str


class MigrationError(MemoryServiceError):
    """Exception raised during data migration."""
    
    def __init__(self, message: str, source_backend: str = None, target_backend: str = None):
        super().__init__(message, operation="migration")
        self.source_backend = source_backend
        self.target_backend = target_backend
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.source_backend and self.target_backend:
            return f"{base_str} | Migration: {self.source_backend} -> {self.target_backend}"
        return base_str


class ValidationError(MemoryServiceError):
    """Exception raised when data validation fails."""
    
    def __init__(self, message: str, field_name: str = None, field_value: str = None):
        super().__init__(message, operation="validation")
        self.field_name = field_name
        self.field_value = field_value
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.field_name:
            return f"{base_str} | Field: {self.field_name}"
        return base_str


class TimeoutError(MemoryServiceError):
    """Exception raised when an operation times out."""
    
    def __init__(self, message: str, timeout_seconds: float = None, backend_name: str = None):
        super().__init__(message, backend_name, "timeout")
        self.timeout_seconds = timeout_seconds
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.timeout_seconds:
            return f"{base_str} | Timeout: {self.timeout_seconds}s"
        return base_str


class AuthenticationError(MemoryServiceError):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str, backend_name: str = None):
        super().__init__(message, backend_name, "authentication")


class PermissionError(MemoryServiceError):
    """Exception raised when permission is denied."""
    
    def __init__(self, message: str, backend_name: str = None, resource: str = None):
        super().__init__(message, backend_name, "permission")
        self.resource = resource
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.resource:
            return f"{base_str} | Resource: {self.resource}"
        return base_str


class BackendNotAvailableError(MemoryServiceError):
    """Exception raised when no backend is available."""
    
    def __init__(self, message: str = "No memory backend available", 
                 attempted_backends: list = None):
        super().__init__(message, operation="backend_selection")
        self.attempted_backends = attempted_backends or []
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.attempted_backends:
            return f"{base_str} | Attempted: {', '.join(self.attempted_backends)}"
        return base_str


class MemoryNotFoundError(MemoryServiceError):
    """Exception raised when a memory item is not found."""
    
    def __init__(self, message: str, memory_id: str = None, project_name: str = None):
        super().__init__(message, operation="memory_retrieval")
        self.memory_id = memory_id
        self.project_name = project_name
    
    def __str__(self) -> str:
        base_str = super().__str__()
        parts = []
        if self.project_name:
            parts.append(f"Project: {self.project_name}")
        if self.memory_id:
            parts.append(f"Memory ID: {self.memory_id}")
        if parts:
            return f"{base_str} | {' | '.join(parts)}"
        return base_str


class DuplicateMemoryError(MemoryServiceError):
    """Exception raised when trying to add a duplicate memory."""
    
    def __init__(self, message: str, memory_id: str = None, project_name: str = None):
        super().__init__(message, operation="memory_creation")
        self.memory_id = memory_id
        self.project_name = project_name
    
    def __str__(self) -> str:
        base_str = super().__str__()
        parts = []
        if self.project_name:
            parts.append(f"Project: {self.project_name}")
        if self.memory_id:
            parts.append(f"Memory ID: {self.memory_id}")
        if parts:
            return f"{base_str} | {' | '.join(parts)}"
        return base_str


class StorageFullError(MemoryServiceError):
    """Exception raised when storage is full."""
    
    def __init__(self, message: str, backend_name: str = None, used_space: int = None, 
                 max_space: int = None):
        super().__init__(message, backend_name, "storage")
        self.used_space = used_space
        self.max_space = max_space
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.used_space is not None and self.max_space is not None:
            return f"{base_str} | Usage: {self.used_space}/{self.max_space} bytes"
        return base_str


class BackendInitializationError(MemoryServiceError):
    """Exception raised when backend initialization fails."""
    
    def __init__(self, message: str, backend_name: str = None, init_step: str = None):
        super().__init__(message, backend_name, "initialization")
        self.init_step = init_step
    
    def __str__(self) -> str:
        base_str = super().__str__()
        if self.init_step:
            return f"{base_str} | Step: {self.init_step}"
        return base_str