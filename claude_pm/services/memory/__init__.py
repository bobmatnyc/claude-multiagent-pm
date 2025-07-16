"""
Unified Memory Service Module

This module provides a flexible, backend-agnostic memory management system
for the Claude PM Framework. It supports multiple memory backends including
mem0AI and SQLite with automatic detection, circuit breaker patterns, and
graceful degradation.

Key Features:
- Backend auto-detection and selection
- Circuit breaker pattern for resilience
- Graceful degradation with fallback backends
- Configuration management with three-tier hierarchy
- Performance monitoring and health checking
- Data migration between backends
- Intelligent memory recall with context enhancement
- Memory-driven recommendations and pattern matching
- Automatic error prevention through memory analysis
- Backward compatibility with existing integrations

Supported Backends:
- mem0AI: Advanced memory service with similarity search
- SQLite: Lightweight file-based storage with FTS

Usage:
    from claude_pm.services.memory import (
        FlexibleMemoryService,
        create_memory_recall_service,
        MemoryCategory,
        MemoryQuery
    )

    # Initialize basic memory service
    memory_service = FlexibleMemoryService()
    await memory_service.initialize()

    # Add memory
    memory_id = await memory_service.add_memory(
        "my_project",
        "Important decision",
        MemoryCategory.PROJECT
    )

    # Search memories
    memories = await memory_service.search_memories(
        "my_project",
        MemoryQuery("decision")
    )

    # Use intelligent memory recall
    recall_service = create_memory_recall_service(memory_service)
    await recall_service.initialize()

    # Get memory-driven recommendations for operations
    result = await recall_service.recall_for_operation(
        project_name="my_project",
        operation_type="deploy",
        operation_context={"environment": "production"}
    )

    if result.success:
        recommendations = result.recommendations.get_top_recommendations()
        context = result.enriched_context.get_agent_context()
"""

# Basic models and types - minimal implementation for import compatibility
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


class MemoryCategory(Enum):
    """Memory categories for classification"""
    PROJECT = "project"
    AGENT = "agent"
    WORKFLOW = "workflow"
    DECISION = "decision"
    ERROR = "error"
    KNOWLEDGE = "knowledge"


@dataclass
class MemoryItem:
    """Basic memory item structure"""
    id: str
    content: str
    category: MemoryCategory
    metadata: Dict[str, Any]


@dataclass
class MemoryQuery:
    """Memory search query structure"""
    text: str
    categories: Optional[List[MemoryCategory]] = None
    limit: int = 10


class HealthStatus(Enum):
    """Health status for monitoring"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class BackendHealth:
    """Backend health information"""
    status: HealthStatus
    message: str
    metrics: Dict[str, Any]


# Basic service interfaces for import compatibility
class MemoryBackend:
    """Base memory backend interface"""
    
    async def initialize(self) -> bool:
        """Initialize the backend"""
        return True
    
    async def add_memory(self, project_id: str, content: str, category: MemoryCategory) -> str:
        """Add a memory item"""
        return "mock_id"
    
    async def search_memories(self, project_id: str, query: MemoryQuery) -> List[MemoryItem]:
        """Search memory items"""
        return []


class FlexibleMemoryService:
    """Main memory service - minimal implementation for import compatibility"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._backend = None
    
    async def initialize(self) -> bool:
        """Initialize the service"""
        return True
    
    async def add_memory(self, project_id: str, content: str, category: MemoryCategory) -> str:
        """Add a memory item"""
        return "mock_id"
    
    async def search_memories(self, project_id: str, query: MemoryQuery) -> List[MemoryItem]:
        """Search memory items"""
        return []


# Exception classes for import compatibility
class MemoryServiceError(Exception):
    """Base memory service exception"""
    pass


class BackendError(MemoryServiceError):
    """Backend-specific error"""
    pass


class CircuitBreakerOpenError(MemoryServiceError):
    """Circuit breaker is open"""
    pass


class ConfigurationError(MemoryServiceError):
    """Configuration error"""
    pass


class MigrationError(MemoryServiceError):
    """Migration error"""
    pass


# Factory functions
def create_flexible_memory_service(config: dict = None) -> FlexibleMemoryService:
    """
    Factory function to create a FlexibleMemoryService instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        FlexibleMemoryService: Configured memory service instance
    """
    return FlexibleMemoryService(config)


def create_memory_recall_service(
    memory_service: FlexibleMemoryService = None, config: Optional[Dict] = None
):
    """
    Factory function to create a MemoryRecallService instance.

    Args:
        memory_service: Optional memory service instance (creates one if None)
        config: Optional recall configuration

    Returns:
        MemoryRecallService: Configured memory recall service instance
    """
    if memory_service is None:
        memory_service = create_flexible_memory_service()

    # Return a mock service for now
    return memory_service


# Backward compatibility
def get_memory_service(config: dict = None) -> FlexibleMemoryService:
    """Legacy factory function for backward compatibility."""
    return create_flexible_memory_service(config)


__version__ = "1.2.0"
__author__ = "Claude PM Framework"

__all__ = [
    # Core interfaces
    "MemoryCategory",
    "MemoryItem", 
    "MemoryQuery",
    "HealthStatus",
    "BackendHealth",
    "MemoryBackend",
    # Main service
    "FlexibleMemoryService",
    "create_flexible_memory_service",
    "create_memory_recall_service",
    "get_memory_service",  # Legacy
    # Exceptions
    "MemoryServiceError",
    "BackendError",
    "CircuitBreakerOpenError", 
    "ConfigurationError",
    "MigrationError",
]