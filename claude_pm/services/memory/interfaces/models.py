"""
Data Models for Memory Service

This module defines the core data models used throughout the memory service.
"""

import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class MemoryCategory(str, Enum):
    """Standardized memory categories for the Claude PM Framework."""

    PROJECT = "project"  # Architectural decisions, requirements, milestones
    PATTERN = "pattern"  # Successful solutions, code patterns, reusable approaches
    TEAM = "team"  # Coding standards, team preferences, workflows
    ERROR = "error"  # Bug patterns, error solutions, debugging knowledge

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "MemoryCategory":
        """Create category from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.PROJECT  # Default fallback


@dataclass
class MemoryItem:
    """Unified memory item representation across all backends."""

    id: str
    content: str
    category: MemoryCategory
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    project_name: str

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if isinstance(self.category, str):
            self.category = MemoryCategory.from_string(self.category)

        if not isinstance(self.tags, list):
            self.tags = []

        if not isinstance(self.metadata, dict):
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_name": self.project_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create from dictionary representation."""
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            category=MemoryCategory.from_string(data.get("category", "project")),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            project_name=data.get("project_name", ""),
        )

    def get_age_seconds(self) -> float:
        """Get age of memory item in seconds."""
        try:
            created_time = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            return (datetime.now(created_time.tzinfo) - created_time).total_seconds()
        except (ValueError, AttributeError):
            return 0.0

    def matches_query(self, query: str) -> bool:
        """Check if memory item matches a text query."""
        query_lower = query.lower()
        return (
            query_lower in self.content.lower()
            or any(query_lower in tag.lower() for tag in self.tags)
            or query_lower in str(self.metadata).lower()
        )


@dataclass
class MemoryQuery:
    """Standardized query parameters for memory searches."""

    query: str
    category: Optional[MemoryCategory] = None
    tags: Optional[List[str]] = None
    limit: int = 10
    offset: int = 0
    include_metadata: bool = True
    similarity_threshold: float = 0.7
    max_age_seconds: Optional[float] = None
    min_age_seconds: Optional[float] = None

    def __post_init__(self):
        """Validate query parameters."""
        if self.limit <= 0:
            self.limit = 10
        if self.offset < 0:
            self.offset = 0
        if self.similarity_threshold < 0 or self.similarity_threshold > 1:
            self.similarity_threshold = 0.7

        if isinstance(self.category, str):
            self.category = MemoryCategory.from_string(self.category)

        if self.tags and not isinstance(self.tags, list):
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "category": self.category.value if self.category else None,
            "tags": self.tags,
            "limit": self.limit,
            "offset": self.offset,
            "include_metadata": self.include_metadata,
            "similarity_threshold": self.similarity_threshold,
            "max_age_seconds": self.max_age_seconds,
            "min_age_seconds": self.min_age_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryQuery":
        """Create from dictionary representation."""
        return cls(
            query=data.get("query", ""),
            category=MemoryCategory.from_string(data["category"]) if data.get("category") else None,
            tags=data.get("tags"),
            limit=data.get("limit", 10),
            offset=data.get("offset", 0),
            include_metadata=data.get("include_metadata", True),
            similarity_threshold=data.get("similarity_threshold", 0.7),
            max_age_seconds=data.get("max_age_seconds"),
            min_age_seconds=data.get("min_age_seconds"),
        )


@dataclass
class HealthStatus:
    """Health status information for memory backends."""

    backend_name: str
    is_healthy: bool
    response_time_ms: float
    error_message: Optional[str] = None
    features: Dict[str, bool] = field(default_factory=dict)
    last_checked: float = field(default_factory=time.time)
    uptime_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "backend_name": self.backend_name,
            "is_healthy": self.is_healthy,
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
            "features": self.features,
            "last_checked": self.last_checked,
            "uptime_percentage": self.uptime_percentage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthStatus":
        """Create from dictionary representation."""
        return cls(
            backend_name=data.get("backend_name", ""),
            is_healthy=data.get("is_healthy", False),
            response_time_ms=data.get("response_time_ms", 0.0),
            error_message=data.get("error_message"),
            features=data.get("features", {}),
            last_checked=data.get("last_checked", time.time()),
            uptime_percentage=data.get("uptime_percentage", 0.0),
        )


@dataclass
class BackendHealth:
    """Comprehensive backend health information."""

    backend_name: str
    is_healthy: bool
    response_time: float
    error_message: Optional[str] = None
    features: Dict[str, bool] = field(default_factory=dict)
    last_checked: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_requests: int = 0
    successful_requests: int = 0

    def update_health(
        self, is_healthy: bool, response_time: float, error_message: Optional[str] = None
    ):
        """Update health status with new check result."""
        self.is_healthy = is_healthy
        self.response_time = response_time
        self.error_message = error_message
        self.last_checked = time.time()
        self.total_requests += 1

        if is_healthy:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.successful_requests += 1
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0

    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "backend_name": self.backend_name,
            "is_healthy": self.is_healthy,
            "response_time": self.response_time,
            "error_message": self.error_message,
            "features": self.features,
            "last_checked": self.last_checked,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "success_rate": self.get_success_rate(),
        }


@dataclass
class OperationResult:
    """Result of a memory operation."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    backend_used: Optional[str] = None
    response_time_ms: float = 0.0
    operation_type: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "backend_used": self.backend_used,
            "response_time_ms": self.response_time_ms,
            "operation_type": self.operation_type,
        }


@dataclass
class MemoryStatistics:
    """Statistics about memory usage and performance."""

    total_memories: int = 0
    memories_by_category: Dict[str, int] = field(default_factory=dict)
    memories_by_project: Dict[str, int] = field(default_factory=dict)
    total_size_bytes: int = 0
    average_memory_age_seconds: float = 0.0
    most_recent_memory: Optional[str] = None
    oldest_memory: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_memories": self.total_memories,
            "memories_by_category": self.memories_by_category,
            "memories_by_project": self.memories_by_project,
            "total_size_bytes": self.total_size_bytes,
            "average_memory_age_seconds": self.average_memory_age_seconds,
            "most_recent_memory": self.most_recent_memory,
            "oldest_memory": self.oldest_memory,
        }


# Type aliases for convenience
MemoryID = str
ProjectName = str
BackendName = str
Timestamp = float
