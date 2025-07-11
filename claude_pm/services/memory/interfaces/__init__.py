"""
Memory Service Interfaces

This module defines the core interfaces and data models for the unified memory service.
"""

from .models import (
    MemoryCategory,
    MemoryItem,
    MemoryQuery, 
    HealthStatus,
    BackendHealth
)

from .backend import MemoryBackend

from .exceptions import (
    MemoryServiceError,
    BackendError,
    CircuitBreakerOpenError,
    ConfigurationError,
    MigrationError
)

__all__ = [
    "MemoryCategory",
    "MemoryItem", 
    "MemoryQuery",
    "HealthStatus",
    "BackendHealth",
    "MemoryBackend",
    "MemoryServiceError",
    "BackendError", 
    "CircuitBreakerOpenError",
    "ConfigurationError",
    "MigrationError"
]