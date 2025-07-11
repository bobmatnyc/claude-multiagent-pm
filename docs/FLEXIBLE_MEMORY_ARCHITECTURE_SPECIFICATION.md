# Flexible Memory Architecture Specification

## Executive Summary

This document specifies a comprehensive flexible memory architecture for the Claude PM Framework that makes mem0AI optional through auto-detection, circuit breaker patterns, and lightweight fallbacks. The architecture provides seamless memory service regardless of backend while maintaining all existing functionality and enabling future enhancements.

**Version**: 1.0.0  
**Date**: July 10, 2025  
**Author**: Architect Agent  
**Framework Version**: 4.5.0+

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Service Abstraction Layer](#service-abstraction-layer)
3. [Auto-Detection Architecture](#auto-detection-architecture)
4. [Circuit Breaker Implementation](#circuit-breaker-implementation)
5. [Backend Service Architectures](#backend-service-architectures)
6. [Configuration Management](#configuration-management)
7. [Data Migration and Compatibility](#data-migration-and-compatibility)
8. [Framework Integration Design](#framework-integration-design)
9. [Performance and Monitoring](#performance-and-monitoring)
10. [Implementation Blueprints](#implementation-blueprints)
11. [Migration Strategy](#migration-strategy)
12. [Risk Assessment](#risk-assessment)

---

## Architecture Overview

### Design Principles

1. **Transparency**: Memory operations work identically regardless of backend
2. **Resilience**: Graceful degradation when preferred backends fail
3. **Performance**: Optimized for common use cases with intelligent caching
4. **Maintainability**: Clean separation of concerns and extensible design
5. **Compatibility**: Seamless integration with existing Claude PM Framework

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude PM Framework                          │
├─────────────────────────────────────────────────────────────────┤
│                Memory Service Interface                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Service Abstraction Layer                      │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │            Auto-Detection Engine                        │ │ │
│  │  │  ┌─────────────────────────────────────────────────────┐ │ │ │
│  │  │  │          Circuit Breaker Pattern                   │ │ │ │
│  │  │  └─────────────────────────────────────────────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                      Backend Services                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   mem0AI    │  │   SQLite    │  │   TinyDB    │  │  In-Memory  │ │
│  │   Service   │  │   Service   │  │   Service   │  │   Service   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Service Priority Order

1. **mem0AI**: Preferred for production with full feature set
2. **SQLite**: Lightweight alternative with full compatibility
3. **TinyDB**: JSON-based fallback for simple deployments
4. **In-Memory**: Development and testing mode

---

## Service Abstraction Layer

### Core Interface Definition

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio

class MemoryCategory(str, Enum):
    """Standardized memory categories."""
    PROJECT = "project"
    PATTERN = "pattern"
    TEAM = "team"
    ERROR = "error"

@dataclass
class MemoryItem:
    """Unified memory item representation."""
    id: str
    content: str
    category: MemoryCategory
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    project_name: str

@dataclass
class MemoryQuery:
    """Standardized query parameters."""
    query: str
    category: Optional[MemoryCategory] = None
    tags: Optional[List[str]] = None
    limit: int = 10
    offset: int = 0
    include_metadata: bool = True
    similarity_threshold: float = 0.7

class MemoryBackend(ABC):
    """Abstract base class for memory backends."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the backend service."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if backend is healthy."""
        pass
    
    @abstractmethod
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add a memory item."""
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search for memories."""
        pass
    
    @abstractmethod
    async def get_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> Optional[MemoryItem]:
        """Get a specific memory."""
        pass
    
    @abstractmethod
    async def update_memory(
        self,
        project_name: str,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing memory."""
        pass
    
    @abstractmethod
    async def delete_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> bool:
        """Delete a memory."""
        pass
    
    @abstractmethod
    async def get_project_memories(
        self,
        project_name: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Get all memories for a project."""
        pass
    
    @abstractmethod
    async def get_memory_stats(
        self,
        project_name: str
    ) -> Dict[str, Any]:
        """Get memory statistics."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Get backend name."""
        pass
    
    @property
    @abstractmethod
    def supports_similarity_search(self) -> bool:
        """Check if backend supports similarity search."""
        pass
```

### Unified Memory Service

```python
from typing import Optional, List, Dict, Any
import asyncio
import logging
from datetime import datetime, timedelta

class FlexibleMemoryService:
    """
    Unified memory service with auto-detection and fallback capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Available backends
        self.backends: Dict[str, MemoryBackend] = {}
        self.active_backend: Optional[MemoryBackend] = None
        self.fallback_chain: List[str] = []
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("circuit_breaker_threshold", 5),
            recovery_timeout=self.config.get("circuit_breaker_recovery", 60),
            test_requests=self.config.get("circuit_breaker_test_requests", 3)
        )
        
        # Auto-detection
        self.auto_detection = AutoDetectionEngine(
            timeout=self.config.get("detection_timeout", 2.0),
            retry_attempts=self.config.get("detection_retries", 3)
        )
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize backends
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize all available backends."""
        try:
            # mem0AI Backend
            self.backends["mem0ai"] = Mem0AIBackend(
                host=self.config.get("mem0ai_host", "localhost"),
                port=self.config.get("mem0ai_port", 8002),
                timeout=self.config.get("mem0ai_timeout", 30)
            )
            
            # SQLite Backend
            self.backends["sqlite"] = SQLiteBackend(
                db_path=self.config.get("sqlite_path", "memory.db"),
                enable_fts=self.config.get("sqlite_fts", True)
            )
            
            # TinyDB Backend
            self.backends["tinydb"] = TinyDBBackend(
                db_path=self.config.get("tinydb_path", "memory.json")
            )
            
            # In-Memory Backend
            self.backends["memory"] = InMemoryBackend()
            
            # Set fallback chain
            self.fallback_chain = self.config.get("fallback_chain", [
                "mem0ai", "sqlite", "tinydb", "memory"
            ])
            
        except Exception as e:
            self.logger.error(f"Failed to initialize backends: {e}")
            raise
    
    async def initialize(self) -> bool:
        """Initialize the memory service with auto-detection."""
        try:
            # Auto-detect best available backend
            detected_backend = await self.auto_detection.detect_best_backend(
                self.backends, self.fallback_chain
            )
            
            if detected_backend:
                self.active_backend = detected_backend
                self.logger.info(f"Memory service initialized with {detected_backend.backend_name}")
                return True
            else:
                self.logger.error("No functional memory backend detected")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize memory service: {e}")
            return False
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add a memory with circuit breaker protection."""
        return await self.circuit_breaker.call(
            self._add_memory_internal,
            project_name, content, category, tags, metadata
        )
    
    async def _add_memory_internal(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Internal memory addition with fallback."""
        for backend_name in self.fallback_chain:
            if backend_name in self.backends:
                backend = self.backends[backend_name]
                try:
                    with self.performance_monitor.measure_operation("add_memory", backend_name):
                        if await backend.health_check():
                            result = await backend.add_memory(
                                project_name, content, category, tags, metadata
                            )
                            if result:
                                self.logger.debug(f"Memory added using {backend_name}: {result}")
                                return result
                        else:
                            self.logger.warning(f"Backend {backend_name} failed health check")
                except Exception as e:
                    self.logger.warning(f"Backend {backend_name} failed: {e}")
                    continue
        
        raise Exception("All memory backends failed")
    
    # Additional methods follow the same pattern...
```

---

## Auto-Detection Architecture

### Detection Engine

```python
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class BackendHealth:
    """Backend health status."""
    is_healthy: bool
    response_time: float
    error_message: Optional[str] = None
    features: Dict[str, bool] = None
    last_checked: float = 0

class AutoDetectionEngine:
    """
    Intelligent backend detection with performance profiling.
    """
    
    def __init__(self, timeout: float = 2.0, retry_attempts: int = 3):
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.logger = logging.getLogger(__name__)
        self.health_cache: Dict[str, BackendHealth] = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def detect_best_backend(
        self,
        backends: Dict[str, MemoryBackend],
        priority_order: List[str]
    ) -> Optional[MemoryBackend]:
        """
        Detect the best available backend based on priority and health.
        """
        health_results = await self._check_all_backends(backends)
        
        # Select best backend based on priority and health
        for backend_name in priority_order:
            if backend_name in health_results:
                health = health_results[backend_name]
                if health.is_healthy:
                    self.logger.info(f"Selected {backend_name} (response: {health.response_time:.2f}s)")
                    return backends[backend_name]
        
        self.logger.warning("No healthy backends detected")
        return None
    
    async def _check_all_backends(
        self,
        backends: Dict[str, MemoryBackend]
    ) -> Dict[str, BackendHealth]:
        """Check health of all backends concurrently."""
        tasks = []
        
        for name, backend in backends.items():
            # Check cache first
            cached_health = self._get_cached_health(name)
            if cached_health:
                continue
                
            task = asyncio.create_task(
                self._check_backend_health(name, backend),
                name=f"health_check_{name}"
            )
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    backend_name = tasks[i].get_name().replace("health_check_", "")
                    self.health_cache[backend_name] = BackendHealth(
                        is_healthy=False,
                        response_time=float('inf'),
                        error_message=str(result),
                        last_checked=time.time()
                    )
        
        return {name: health for name, health in self.health_cache.items()}
    
    async def _check_backend_health(
        self,
        name: str,
        backend: MemoryBackend
    ) -> BackendHealth:
        """Check individual backend health with timeout."""
        start_time = time.time()
        
        try:
            # Use timeout for health check
            health_check = asyncio.wait_for(
                backend.health_check(),
                timeout=self.timeout
            )
            
            is_healthy = await health_check
            response_time = time.time() - start_time
            
            # Check backend features
            features = await self._check_backend_features(backend)
            
            health = BackendHealth(
                is_healthy=is_healthy,
                response_time=response_time,
                features=features,
                last_checked=time.time()
            )
            
            self.health_cache[name] = health
            return health
            
        except asyncio.TimeoutError:
            health = BackendHealth(
                is_healthy=False,
                response_time=float('inf'),
                error_message="Timeout",
                last_checked=time.time()
            )
            self.health_cache[name] = health
            return health
            
        except Exception as e:
            response_time = time.time() - start_time
            health = BackendHealth(
                is_healthy=False,
                response_time=response_time,
                error_message=str(e),
                last_checked=time.time()
            )
            self.health_cache[name] = health
            return health
    
    async def _check_backend_features(
        self,
        backend: MemoryBackend
    ) -> Dict[str, bool]:
        """Check what features a backend supports."""
        features = {
            "similarity_search": backend.supports_similarity_search,
            "async_operations": hasattr(backend, 'add_memory'),
            "bulk_operations": hasattr(backend, 'bulk_add_memories'),
            "transactions": hasattr(backend, 'begin_transaction'),
            "full_text_search": hasattr(backend, 'full_text_search')
        }
        return features
    
    def _get_cached_health(self, backend_name: str) -> Optional[BackendHealth]:
        """Get cached health if still valid."""
        if backend_name in self.health_cache:
            health = self.health_cache[backend_name]
            if time.time() - health.last_checked < self.cache_ttl:
                return health
        return None
    
    def invalidate_cache(self, backend_name: Optional[str] = None):
        """Invalidate health cache."""
        if backend_name:
            self.health_cache.pop(backend_name, None)
        else:
            self.health_cache.clear()
```

---

## Circuit Breaker Implementation

### Circuit Breaker Pattern

```python
import asyncio
import time
from enum import Enum
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    test_requests: int = 3
    success_threshold: int = 2

class CircuitBreaker:
    """
    Circuit breaker implementation for memory service resilience.
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.test_request_count = 0
        self.success_count = 0
        self.logger = logging.getLogger(__name__)
        
        # Metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_opens": 0,
            "fallback_triggers": 0
        }
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        """
        self.metrics["total_requests"] += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.test_request_count = 0
                self.success_count = 0
                self.logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                self.metrics["fallback_triggers"] += 1
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        return (
            self.state == CircuitState.OPEN and
            time.time() - self.last_failure_time >= self.config.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful request."""
        self.metrics["successful_requests"] += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self.test_request_count += 1
            
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.logger.info("Circuit breaker reset to CLOSED state")
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed request."""
        self.metrics["failed_requests"] += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.test_request_count += 1
            
            if self.test_request_count >= self.config.test_requests:
                self.state = CircuitState.OPEN
                self.metrics["circuit_opens"] += 1
                self.logger.warning("Circuit breaker moved to OPEN state after test failures")
        
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.metrics["circuit_opens"] += 1
                self.logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state information."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "test_request_count": self.test_request_count,
            "success_count": self.success_count,
            "metrics": self.metrics.copy()
        }
    
    def reset(self):
        """Manually reset circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.test_request_count = 0
        self.success_count = 0
        self.logger.info("Circuit breaker manually reset")

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass
```

---

## Backend Service Architectures

### mem0AI Backend Service

```python
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

class Mem0AIBackend(MemoryBackend):
    """
    Enhanced mem0AI backend with fallback awareness.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8002, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
    
    @property
    def backend_name(self) -> str:
        return "mem0ai"
    
    @property
    def supports_similarity_search(self) -> bool:
        return True
    
    async def initialize(self) -> bool:
        """Initialize mem0AI connection."""
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection
            return await self.health_check()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize mem0AI backend: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check mem0AI service health."""
        try:
            if not self.session:
                return False
            
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.debug(f"mem0AI health check failed: {e}")
            return False
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add memory to mem0AI service."""
        try:
            data = {
                "content": content,
                "space_name": project_name,
                "metadata": {
                    "category": category.value,
                    "tags": tags or [],
                    "project": project_name,
                    "created_at": datetime.now().isoformat(),
                    **(metadata or {})
                }
            }
            
            async with self.session.post(f"{self.base_url}/memories", json=data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    return result.get("id")
                else:
                    self.logger.error(f"Failed to add memory: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error adding memory: {e}")
            return None
    
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search memories in mem0AI."""
        try:
            params = {
                "query": query.query,
                "space_name": project_name,
                "limit": query.limit,
                "include_metadata": query.include_metadata
            }
            
            if query.category:
                params["category"] = query.category.value
            
            async with self.session.get(f"{self.base_url}/memories/search", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return [self._convert_to_memory_item(item) for item in result.get("memories", [])]
                else:
                    self.logger.error(f"Search failed: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error searching memories: {e}")
            return []
    
    def _convert_to_memory_item(self, data: Dict[str, Any]) -> MemoryItem:
        """Convert mem0AI response to MemoryItem."""
        metadata = data.get("metadata", {})
        return MemoryItem(
            id=data.get("id", ""),
            content=data.get("content", ""),
            category=MemoryCategory(metadata.get("category", "project")),
            tags=metadata.get("tags", []),
            metadata=metadata,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            project_name=metadata.get("project", "")
        )
    
    # Additional methods follow similar pattern...
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None
```

### SQLite Backend Service

```python
import aiosqlite
import sqlite3
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

class SQLiteBackend(MemoryBackend):
    """
    SQLite-based memory backend with full feature parity.
    """
    
    def __init__(self, db_path: str = "memory.db", enable_fts: bool = True):
        self.db_path = db_path
        self.enable_fts = enable_fts
        self.logger = logging.getLogger(__name__)
        self._connection: Optional[aiosqlite.Connection] = None
    
    @property
    def backend_name(self) -> str:
        return "sqlite"
    
    @property
    def supports_similarity_search(self) -> bool:
        return self.enable_fts
    
    async def initialize(self) -> bool:
        """Initialize SQLite database."""
        try:
            self._connection = await aiosqlite.connect(self.db_path)
            
            # Enable WAL mode for better concurrency
            await self._connection.execute("PRAGMA journal_mode=WAL")
            await self._connection.execute("PRAGMA synchronous=NORMAL")
            await self._connection.execute("PRAGMA cache_size=10000")
            await self._connection.execute("PRAGMA temp_store=MEMORY")
            
            # Create tables
            await self._create_tables()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite backend: {e}")
            return False
    
    async def _create_tables(self):
        """Create necessary tables."""
        # Main memories table
        await self._connection.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,  -- JSON array
                metadata TEXT,  -- JSON object
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                INDEX(project_name),
                INDEX(category),
                INDEX(created_at)
            )
        ''')
        
        # Full-text search table if enabled
        if self.enable_fts:
            await self._connection.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id UNINDEXED,
                    project_name UNINDEXED,
                    content,
                    category UNINDEXED,
                    tags UNINDEXED,
                    content='memories',
                    content_rowid='rowid'
                )
            ''')
            
            # Trigger to keep FTS in sync
            await self._connection.execute('''
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(id, project_name, content, category, tags)
                    VALUES (new.id, new.project_name, new.content, new.category, new.tags);
                END
            ''')
            
            await self._connection.execute('''
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, id, project_name, content, category, tags)
                    VALUES ('delete', old.id, old.project_name, old.content, old.category, old.tags);
                END
            ''')
        
        await self._connection.commit()
    
    async def health_check(self) -> bool:
        """Check SQLite database health."""
        try:
            if not self._connection:
                return False
            
            await self._connection.execute("SELECT 1")
            return True
            
        except Exception:
            return False
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add memory to SQLite database."""
        try:
            memory_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            tags_json = json.dumps(tags or [])
            metadata_json = json.dumps(metadata or {})
            
            await self._connection.execute('''
                INSERT INTO memories (id, project_name, content, category, tags, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (memory_id, project_name, content, category.value, tags_json, metadata_json, now, now))
            
            await self._connection.commit()
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error adding memory to SQLite: {e}")
            return None
    
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search memories in SQLite."""
        try:
            sql_params = [project_name]
            
            if self.enable_fts and query.query:
                # Use FTS for text search
                sql = '''
                    SELECT m.* FROM memories m
                    JOIN memories_fts fts ON m.id = fts.id
                    WHERE m.project_name = ? AND memories_fts MATCH ?
                '''
                sql_params.append(query.query)
            else:
                # Fallback to LIKE search
                sql = '''
                    SELECT * FROM memories
                    WHERE project_name = ?
                '''
                if query.query:
                    sql += ' AND content LIKE ?'
                    sql_params.append(f'%{query.query}%')
            
            # Add category filter
            if query.category:
                sql += ' AND category = ?'
                sql_params.append(query.category.value)
            
            # Add ordering and limit
            sql += ' ORDER BY created_at DESC LIMIT ?'
            sql_params.append(query.limit)
            
            if query.offset:
                sql += ' OFFSET ?'
                sql_params.append(query.offset)
            
            async with self._connection.execute(sql, sql_params) as cursor:
                rows = await cursor.fetchall()
                return [self._convert_to_memory_item(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error searching memories in SQLite: {e}")
            return []
    
    def _convert_to_memory_item(self, row: tuple) -> MemoryItem:
        """Convert SQLite row to MemoryItem."""
        return MemoryItem(
            id=row[0],
            project_name=row[1],
            content=row[2],
            category=MemoryCategory(row[3]),
            tags=json.loads(row[4]),
            metadata=json.loads(row[5]),
            created_at=row[6],
            updated_at=row[7]
        )
    
    # Additional methods follow similar pattern...
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._connection:
            await self._connection.close()
            self._connection = None
```

### TinyDB Backend Service

```python
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import threading

class TinyDBBackend(MemoryBackend):
    """
    TinyDB-based memory backend for simple deployments.
    """
    
    def __init__(self, db_path: str = "memory.json"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._db: Optional[TinyDB] = None
        self._lock = threading.RLock()
    
    @property
    def backend_name(self) -> str:
        return "tinydb"
    
    @property
    def supports_similarity_search(self) -> bool:
        return False  # Limited text search
    
    async def initialize(self) -> bool:
        """Initialize TinyDB database."""
        try:
            self._db = TinyDB(self.db_path, storage=JSONStorage)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TinyDB backend: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check TinyDB health."""
        try:
            return self._db is not None and hasattr(self._db, 'all')
        except Exception:
            return False
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add memory to TinyDB."""
        try:
            with self._lock:
                memory_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                document = {
                    "id": memory_id,
                    "project_name": project_name,
                    "content": content,
                    "category": category.value,
                    "tags": tags or [],
                    "metadata": metadata or {},
                    "created_at": now,
                    "updated_at": now
                }
                
                self._db.insert(document)
                return memory_id
                
        except Exception as e:
            self.logger.error(f"Error adding memory to TinyDB: {e}")
            return None
    
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search memories in TinyDB."""
        try:
            with self._lock:
                Memory = Query()
                
                # Build query
                search_query = Memory.project_name == project_name
                
                if query.category:
                    search_query &= Memory.category == query.category.value
                
                if query.query:
                    # Simple text search
                    search_query &= Memory.content.search(query.query)
                
                # Execute search
                results = self._db.search(search_query)
                
                # Sort and limit
                results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                results = results[:query.limit]
                
                return [self._convert_to_memory_item(doc) for doc in results]
                
        except Exception as e:
            self.logger.error(f"Error searching memories in TinyDB: {e}")
            return []
    
    def _convert_to_memory_item(self, doc: Dict[str, Any]) -> MemoryItem:
        """Convert TinyDB document to MemoryItem."""
        return MemoryItem(
            id=doc.get("id", ""),
            project_name=doc.get("project_name", ""),
            content=doc.get("content", ""),
            category=MemoryCategory(doc.get("category", "project")),
            tags=doc.get("tags", []),
            metadata=doc.get("metadata", {}),
            created_at=doc.get("created_at", ""),
            updated_at=doc.get("updated_at", "")
        )
    
    # Additional methods follow similar pattern...
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._db:
            self._db.close()
            self._db = None
```

### In-Memory Backend Service

```python
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import threading

class InMemoryBackend(MemoryBackend):
    """
    In-memory backend for testing and development.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._memories: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    @property
    def backend_name(self) -> str:
        return "memory"
    
    @property
    def supports_similarity_search(self) -> bool:
        return False
    
    async def initialize(self) -> bool:
        """Initialize in-memory storage."""
        return True
    
    async def health_check(self) -> bool:
        """Always healthy."""
        return True
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add memory to in-memory storage."""
        try:
            with self._lock:
                memory_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                self._memories[memory_id] = {
                    "id": memory_id,
                    "project_name": project_name,
                    "content": content,
                    "category": category.value,
                    "tags": tags or [],
                    "metadata": metadata or {},
                    "created_at": now,
                    "updated_at": now
                }
                
                return memory_id
                
        except Exception as e:
            self.logger.error(f"Error adding memory to in-memory storage: {e}")
            return None
    
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search memories in in-memory storage."""
        try:
            with self._lock:
                results = []
                
                for memory_data in self._memories.values():
                    # Filter by project
                    if memory_data["project_name"] != project_name:
                        continue
                    
                    # Filter by category
                    if query.category and memory_data["category"] != query.category.value:
                        continue
                    
                    # Simple text search
                    if query.query and query.query.lower() not in memory_data["content"].lower():
                        continue
                    
                    results.append(self._convert_to_memory_item(memory_data))
                
                # Sort by created_at descending
                results.sort(key=lambda x: x.created_at, reverse=True)
                
                return results[:query.limit]
                
        except Exception as e:
            self.logger.error(f"Error searching memories in in-memory storage: {e}")
            return []
    
    def _convert_to_memory_item(self, data: Dict[str, Any]) -> MemoryItem:
        """Convert dict to MemoryItem."""
        return MemoryItem(
            id=data["id"],
            project_name=data["project_name"],
            content=data["content"],
            category=MemoryCategory(data["category"]),
            tags=data["tags"],
            metadata=data["metadata"],
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )
    
    # Additional methods follow similar pattern...
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        with self._lock:
            self._memories.clear()
```

---

## Configuration Management

### Three-Tier Configuration System

```python
import os
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class MemoryConfig:
    """Memory service configuration."""
    # Backend selection
    preferred_backend: str = "mem0ai"
    fallback_chain: List[str] = None
    auto_detection: bool = True
    
    # mem0AI configuration
    mem0ai_host: str = "localhost"
    mem0ai_port: int = 8002
    mem0ai_timeout: int = 30
    mem0ai_api_key: Optional[str] = None
    
    # SQLite configuration
    sqlite_path: str = "memory.db"
    sqlite_fts: bool = True
    sqlite_wal_mode: bool = True
    
    # TinyDB configuration
    tinydb_path: str = "memory.json"
    
    # Circuit breaker configuration
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery: int = 60
    circuit_breaker_test_requests: int = 3
    
    # Auto-detection configuration
    detection_timeout: float = 2.0
    detection_retries: int = 3
    detection_cache_ttl: int = 300
    
    # Performance configuration
    enable_caching: bool = True
    cache_ttl: int = 300
    max_cache_size: int = 1000
    
    # Monitoring configuration
    enable_monitoring: bool = True
    metrics_retention: int = 86400  # 24 hours
    
    def __post_init__(self):
        if self.fallback_chain is None:
            self.fallback_chain = ["mem0ai", "sqlite", "tinydb", "memory"]

class ConfigurationManager:
    """
    Three-tier configuration management for memory services.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.logger = logging.getLogger(__name__)
        
        # Configuration paths (in order of precedence)
        self.config_paths = [
            self.project_root / ".claude-multiagent-pm" / "config" / "memory.yaml",  # Project
            Path.home() / ".claude-multiagent-pm" / "config" / "memory.yaml",      # User
            Path(__file__).parent / "config" / "memory.yaml"                        # System
        ]
        
        self._config_cache: Optional[MemoryConfig] = None
        self._config_timestamp = 0
    
    def load_config(self) -> MemoryConfig:
        """Load configuration with three-tier hierarchy."""
        try:
            # Check cache validity
            if self._config_cache and self._is_cache_valid():
                return self._config_cache
            
            # Start with default configuration
            config_data = asdict(MemoryConfig())
            
            # Load from system, user, then project (in order)
            for config_path in reversed(self.config_paths):
                if config_path.exists():
                    try:
                        with open(config_path, 'r') as f:
                            if config_path.suffix == '.yaml':
                                file_config = yaml.safe_load(f)
                            else:
                                file_config = json.load(f)
                        
                        # Merge configuration
                        config_data.update(file_config)
                        self.logger.debug(f"Loaded config from {config_path}")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load config from {config_path}: {e}")
            
            # Override with environment variables
            self._apply_env_overrides(config_data)
            
            # Create configuration object
            config = MemoryConfig(**config_data)
            
            # Cache configuration
            self._config_cache = config
            self._config_timestamp = time.time()
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return MemoryConfig()  # Return default config
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]):
        """Apply environment variable overrides."""
        env_mappings = {
            "CLAUDE_MEMORY_BACKEND": "preferred_backend",
            "CLAUDE_MEM0AI_HOST": "mem0ai_host",
            "CLAUDE_MEM0AI_PORT": "mem0ai_port",
            "CLAUDE_MEM0AI_API_KEY": "mem0ai_api_key",
            "CLAUDE_SQLITE_PATH": "sqlite_path",
            "CLAUDE_MEMORY_CACHE_TTL": "cache_ttl",
            "CLAUDE_CIRCUIT_BREAKER_THRESHOLD": "circuit_breaker_threshold"
        }
        
        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion
                if config_key.endswith("_port") or config_key.endswith("_ttl") or config_key.endswith("_threshold"):
                    value = int(value)
                elif config_key.endswith("_timeout"):
                    value = float(value)
                elif config_key.endswith("_enabled") or config_key.endswith("_mode"):
                    value = value.lower() in ("true", "1", "yes", "on")
                
                config_data[config_key] = value
    
    def _is_cache_valid(self) -> bool:
        """Check if cached configuration is still valid."""
        if not self._config_cache:
            return False
        
        # Check if any config file has been modified
        for config_path in self.config_paths:
            if config_path.exists():
                try:
                    if config_path.stat().st_mtime > self._config_timestamp:
                        return False
                except OSError:
                    pass
        
        return True
    
    def save_config(self, config: MemoryConfig, level: str = "project"):
        """Save configuration to specified level."""
        try:
            if level == "project":
                config_path = self.config_paths[0]
            elif level == "user":
                config_path = self.config_paths[1]
            else:
                raise ValueError(f"Invalid config level: {level}")
            
            # Create directory if needed
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(config_path, 'w') as f:
                yaml.dump(asdict(config), f, default_flow_style=False)
            
            self.logger.info(f"Saved configuration to {config_path}")
            
            # Invalidate cache
            self._config_cache = None
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about current configuration."""
        config = self.load_config()
        
        return {
            "active_config": asdict(config),
            "config_sources": [
                {
                    "path": str(path),
                    "exists": path.exists(),
                    "level": level
                }
                for path, level in zip(self.config_paths, ["project", "user", "system"])
            ],
            "environment_overrides": [
                key for key in os.environ if key.startswith("CLAUDE_MEMORY_")
            ]
        }
```

---

## Data Migration and Compatibility

### Migration Framework

```python
import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class MigrationPlan:
    """Migration plan between backends."""
    source_backend: str
    target_backend: str
    projects: List[str]
    estimated_items: int
    estimated_time: int  # seconds
    backup_required: bool = True

class DataMigrator:
    """
    Data migration utility between memory backends.
    """
    
    def __init__(self, source_backend: MemoryBackend, target_backend: MemoryBackend):
        self.source_backend = source_backend
        self.target_backend = target_backend
        self.logger = logging.getLogger(__name__)
    
    async def create_migration_plan(self, projects: Optional[List[str]] = None) -> MigrationPlan:
        """Create a migration plan."""
        try:
            # Get all projects if none specified
            if projects is None:
                projects = await self._get_all_projects()
            
            # Estimate migration size
            total_items = 0
            for project in projects:
                stats = await self.source_backend.get_memory_stats(project)
                total_items += stats.get("total", 0)
            
            # Estimate time (rough approximation)
            estimated_time = max(60, total_items * 0.1)  # 0.1 seconds per item, minimum 1 minute
            
            return MigrationPlan(
                source_backend=self.source_backend.backend_name,
                target_backend=self.target_backend.backend_name,
                projects=projects,
                estimated_items=total_items,
                estimated_time=int(estimated_time)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create migration plan: {e}")
            raise
    
    async def migrate_data(
        self,
        plan: MigrationPlan,
        batch_size: int = 100,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Execute data migration according to plan."""
        try:
            results = {
                "success": True,
                "migrated_items": 0,
                "failed_items": 0,
                "errors": [],
                "start_time": datetime.now().isoformat(),
                "end_time": None
            }
            
            # Backup if required
            if plan.backup_required:
                backup_path = await self._create_backup(plan.projects)
                results["backup_path"] = backup_path
            
            # Initialize target backend
            if not await self.target_backend.initialize():
                raise Exception("Failed to initialize target backend")
            
            # Migrate each project
            for project in plan.projects:
                try:
                    project_results = await self._migrate_project(
                        project, batch_size, progress_callback
                    )
                    
                    results["migrated_items"] += project_results["migrated"]
                    results["failed_items"] += project_results["failed"]
                    
                    if project_results["errors"]:
                        results["errors"].extend(project_results["errors"])
                    
                except Exception as e:
                    error_msg = f"Failed to migrate project {project}: {e}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
                    results["success"] = False
            
            results["end_time"] = datetime.now().isoformat()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "migrated_items": 0,
                "failed_items": 0
            }
    
    async def _migrate_project(
        self,
        project: str,
        batch_size: int,
        progress_callback: Optional[callable]
    ) -> Dict[str, Any]:
        """Migrate a single project."""
        results = {"migrated": 0, "failed": 0, "errors": []}
        
        try:
            # Get all memories for project
            memories = await self.source_backend.get_project_memories(project, limit=10000)
            
            # Process in batches
            for i in range(0, len(memories), batch_size):
                batch = memories[i:i + batch_size]
                
                for memory in batch:
                    try:
                        # Add to target backend
                        memory_id = await self.target_backend.add_memory(
                            memory.project_name,
                            memory.content,
                            memory.category,
                            memory.tags,
                            memory.metadata
                        )
                        
                        if memory_id:
                            results["migrated"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Failed to migrate memory {memory.id}")
                        
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(f"Error migrating memory {memory.id}: {e}")
                
                # Progress callback
                if progress_callback:
                    progress_callback(project, results["migrated"], len(memories))
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.01)
        
        except Exception as e:
            results["errors"].append(f"Error processing project {project}: {e}")
        
        return results
    
    async def _get_all_projects(self) -> List[str]:
        """Get all projects with memories."""
        # This would need to be implemented based on backend capabilities
        # For now, return empty list
        return []
    
    async def _create_backup(self, projects: List[str]) -> str:
        """Create backup of source data."""
        try:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "source_backend": self.source_backend.backend_name,
                "projects": {}
            }
            
            for project in projects:
                memories = await self.source_backend.get_project_memories(project, limit=10000)
                backup_data["projects"][project] = [
                    {
                        "id": memory.id,
                        "content": memory.content,
                        "category": memory.category.value,
                        "tags": memory.tags,
                        "metadata": memory.metadata,
                        "created_at": memory.created_at,
                        "updated_at": memory.updated_at
                    }
                    for memory in memories
                ]
            
            # Save backup
            backup_path = f"memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            self.logger.info(f"Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise

class CompatibilityLayer:
    """
    Compatibility layer for existing mem0AI integrations.
    """
    
    def __init__(self, memory_service: FlexibleMemoryService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
    
    async def migrate_from_legacy(self, legacy_config: Dict[str, Any]) -> bool:
        """Migrate from legacy mem0AI configuration."""
        try:
            # Initialize flexible memory service
            if not await self.memory_service.initialize():
                raise Exception("Failed to initialize flexible memory service")
            
            # Create migration plan
            migrator = DataMigrator(
                source_backend=self.memory_service.backends["mem0ai"],
                target_backend=self.memory_service.backends["sqlite"]
            )
            
            plan = await migrator.create_migration_plan()
            
            # Execute migration
            results = await migrator.migrate_data(plan)
            
            self.logger.info(f"Legacy migration completed: {results}")
            return results["success"]
            
        except Exception as e:
            self.logger.error(f"Legacy migration failed: {e}")
            return False
    
    def create_compatibility_wrapper(self) -> "LegacyMemoryWrapper":
        """Create wrapper for legacy code compatibility."""
        return LegacyMemoryWrapper(self.memory_service)

class LegacyMemoryWrapper:
    """
    Wrapper to maintain compatibility with existing mem0AI integration code.
    """
    
    def __init__(self, memory_service: FlexibleMemoryService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
    
    async def store_memory(self, project_name: str, content: str, category: str, **kwargs):
        """Legacy store_memory method."""
        try:
            category_enum = MemoryCategory(category)
        except ValueError:
            category_enum = MemoryCategory.PROJECT
        
        return await self.memory_service.add_memory(
            project_name, content, category_enum, **kwargs
        )
    
    async def retrieve_memories(self, project_name: str, query: str, **kwargs):
        """Legacy retrieve_memories method."""
        memory_query = MemoryQuery(query=query, **kwargs)
        memories = await self.memory_service.search_memories(project_name, memory_query)
        
        # Convert to legacy format
        return [
            {
                "id": memory.id,
                "content": memory.content,
                "metadata": memory.metadata,
                "created_at": memory.created_at
            }
            for memory in memories
        ]
    
    # Additional legacy methods...
```

---

## Performance and Monitoring

### Performance Monitoring System

```python
import time
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import threading

@dataclass
class OperationMetrics:
    """Metrics for a specific operation."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    
    def add_measurement(self, duration: float, success: bool = True):
        """Add a measurement."""
        self.total_calls += 1
        self.total_time += duration
        
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.total_calls

class PerformanceMonitor:
    """
    Performance monitoring for memory operations.
    """
    
    def __init__(self, retention_seconds: int = 86400):
        self.retention_seconds = retention_seconds
        self.metrics: Dict[str, Dict[str, OperationMetrics]] = defaultdict(lambda: defaultdict(OperationMetrics))
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def measure_operation(self, operation: str, backend: str):
        """Context manager for measuring operations."""
        return OperationMeasurement(self, operation, backend)
    
    def record_operation(self, operation: str, backend: str, duration: float, success: bool = True):
        """Record an operation measurement."""
        with self.lock:
            self.metrics[backend][operation].add_measurement(duration, success)
    
    def get_metrics(self, backend: Optional[str] = None) -> Dict[str, Any]:
        """Get current metrics."""
        with self.lock:
            if backend:
                return {
                    "backend": backend,
                    "operations": {
                        op: {
                            "total_calls": metrics.total_calls,
                            "success_rate": metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0,
                            "avg_response_time": metrics.avg_time,
                            "min_response_time": metrics.min_time if metrics.min_time != float('inf') else 0,
                            "max_response_time": metrics.max_time
                        }
                        for op, metrics in self.metrics[backend].items()
                    }
                }
            else:
                return {
                    backend_name: {
                        "operations": {
                            op: {
                                "total_calls": metrics.total_calls,
                                "success_rate": metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0,
                                "avg_response_time": metrics.avg_time,
                                "min_response_time": metrics.min_time if metrics.min_time != float('inf') else 0,
                                "max_response_time": metrics.max_time
                            }
                            for op, metrics in backend_metrics.items()
                        }
                    }
                    for backend_name, backend_metrics in self.metrics.items()
                }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all backends."""
        with self.lock:
            summary = {
                "total_backends": len(self.metrics),
                "backend_performance": {},
                "fastest_backend": None,
                "most_reliable_backend": None
            }
            
            backend_speeds = {}
            backend_reliability = {}
            
            for backend, operations in self.metrics.items():
                total_calls = sum(op.total_calls for op in operations.values())
                successful_calls = sum(op.successful_calls for op in operations.values())
                avg_time = sum(op.avg_time * op.total_calls for op in operations.values()) / total_calls if total_calls > 0 else 0
                
                backend_speeds[backend] = avg_time
                backend_reliability[backend] = successful_calls / total_calls if total_calls > 0 else 0
                
                summary["backend_performance"][backend] = {
                    "total_calls": total_calls,
                    "success_rate": backend_reliability[backend],
                    "avg_response_time": avg_time
                }
            
            if backend_speeds:
                summary["fastest_backend"] = min(backend_speeds, key=backend_speeds.get)
            
            if backend_reliability:
                summary["most_reliable_backend"] = max(backend_reliability, key=backend_reliability.get)
            
            return summary
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self.lock:
            self.metrics.clear()

class OperationMeasurement:
    """Context manager for measuring operation performance."""
    
    def __init__(self, monitor: PerformanceMonitor, operation: str, backend: str):
        self.monitor = monitor
        self.operation = operation
        self.backend = backend
        self.start_time = 0
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None
        self.monitor.record_operation(self.operation, self.backend, duration, success)
    
    def mark_failure(self):
        """Mark the operation as failed."""
        self.success = False

class HealthMonitor:
    """
    Health monitoring for memory backends.
    """
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.health_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.current_health: Dict[str, bool] = {}
        self.logger = logging.getLogger(__name__)
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
    
    async def start_monitoring(self, backends: Dict[str, MemoryBackend]):
        """Start health monitoring."""
        self.backends = backends
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        self._stop_event.set()
        if self._monitoring_task:
            await self._monitoring_task
        self.logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                await self._check_all_backends()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_backends(self):
        """Check health of all backends."""
        for name, backend in self.backends.items():
            try:
                start_time = time.time()
                is_healthy = await backend.health_check()
                response_time = time.time() - start_time
                
                health_record = {
                    "timestamp": datetime.now().isoformat(),
                    "healthy": is_healthy,
                    "response_time": response_time
                }
                
                self.health_history[name].append(health_record)
                self.current_health[name] = is_healthy
                
                # Keep only recent history
                cutoff_time = time.time() - (24 * 60 * 60)  # 24 hours
                self.health_history[name] = [
                    record for record in self.health_history[name]
                    if datetime.fromisoformat(record["timestamp"]).timestamp() > cutoff_time
                ]
                
            except Exception as e:
                self.logger.error(f"Health check failed for {name}: {e}")
                self.current_health[name] = False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "current_health": self.current_health.copy(),
            "health_history": {
                name: history[-10:]  # Last 10 records
                for name, history in self.health_history.items()
            }
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        summary = {
            "total_backends": len(self.backends),
            "healthy_backends": sum(1 for healthy in self.current_health.values() if healthy),
            "unhealthy_backends": sum(1 for healthy in self.current_health.values() if not healthy),
            "backend_uptime": {}
        }
        
        # Calculate uptime percentages
        for name, history in self.health_history.items():
            if history:
                healthy_count = sum(1 for record in history if record["healthy"])
                uptime = (healthy_count / len(history)) * 100
                summary["backend_uptime"][name] = uptime
        
        return summary
```

---

## Implementation Blueprints

### Directory Structure

```
claude_pm/
├── memory/
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── backend.py           # MemoryBackend abstract class
│   │   ├── models.py            # MemoryItem, MemoryQuery, etc.
│   │   └── exceptions.py        # Custom exceptions
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── mem0ai_backend.py    # mem0AI implementation
│   │   ├── sqlite_backend.py    # SQLite implementation
│   │   ├── tinydb_backend.py    # TinyDB implementation
│   │   └── memory_backend.py    # In-memory implementation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── memory_service.py    # FlexibleMemoryService
│   │   ├── auto_detection.py    # AutoDetectionEngine
│   │   ├── circuit_breaker.py   # CircuitBreaker
│   │   └── migration.py         # DataMigrator
│   ├── config/
│   │   ├── __init__.py
│   │   ├── manager.py           # ConfigurationManager
│   │   └── defaults.yaml        # Default configuration
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── performance.py       # PerformanceMonitor
│   │   └── health.py            # HealthMonitor
│   └── utils/
│       ├── __init__.py
│       ├── compatibility.py     # Legacy compatibility
│       └── helpers.py           # Utility functions
```

### Key Classes and Relationships

```python
# Main service class
class FlexibleMemoryService:
    def __init__(self, config: Optional[Dict[str, Any]] = None)
    async def initialize(self) -> bool
    async def add_memory(self, ...) -> Optional[str]
    async def search_memories(self, ...) -> List[MemoryItem]
    # ... other methods

# Backend interface
class MemoryBackend(ABC):
    @abstractmethod
    async def initialize(self) -> bool
    @abstractmethod
    async def health_check(self) -> bool
    @abstractmethod
    async def add_memory(self, ...) -> Optional[str]
    # ... other methods

# Concrete backends
class Mem0AIBackend(MemoryBackend): pass
class SQLiteBackend(MemoryBackend): pass
class TinyDBBackend(MemoryBackend): pass
class InMemoryBackend(MemoryBackend): pass

# Support services
class AutoDetectionEngine:
    async def detect_best_backend(self, ...) -> Optional[MemoryBackend]

class CircuitBreaker:
    async def call(self, func: Callable, *args, **kwargs) -> Any

class ConfigurationManager:
    def load_config(self) -> MemoryConfig

class PerformanceMonitor:
    def measure_operation(self, operation: str, backend: str)
    def get_metrics(self, backend: Optional[str] = None) -> Dict[str, Any]
```

### Integration Points

```python
# CMCP-init integration
class MemoryServiceInitializer:
    """Initialize memory service during CMCP-init."""
    
    async def initialize_memory_service(self, project_root: Path) -> bool:
        """Initialize memory service for a project."""
        config_manager = ConfigurationManager(project_root)
        config = config_manager.load_config()
        
        memory_service = FlexibleMemoryService(asdict(config))
        
        if await memory_service.initialize():
            # Register with framework
            self._register_memory_service(memory_service)
            return True
        return False

# Agent delegation integration
class MemoryServiceDelegator:
    """Delegate memory operations to appropriate agents."""
    
    def __init__(self, memory_service: FlexibleMemoryService):
        self.memory_service = memory_service
    
    async def delegate_memory_operation(self, operation: str, **kwargs):
        """Delegate memory operation based on agent hierarchy."""
        # Implementation depends on agent framework
        pass

# CLI integration
class MemoryServiceCLI:
    """CLI commands for memory service management."""
    
    def __init__(self, memory_service: FlexibleMemoryService):
        self.memory_service = memory_service
    
    async def status(self):
        """Show memory service status."""
        # Implementation for status command
        pass
    
    async def migrate(self, source: str, target: str):
        """Migrate between backends."""
        # Implementation for migration command
        pass
```

---

## Migration Strategy

### Phase 1: Foundation (Week 1-2)

**Objectives:**
- Implement core interfaces and abstract classes
- Create basic configuration management
- Set up project structure and initial testing

**Deliverables:**
- `MemoryBackend` abstract base class
- `MemoryItem`, `MemoryQuery`, and other data models
- `ConfigurationManager` with three-tier support
- Basic test framework

**Tasks:**
1. Create interface definitions
2. Implement configuration management
3. Set up directory structure
4. Create basic unit tests
5. Document API interfaces

### Phase 2: Backend Implementation (Week 3-4)

**Objectives:**
- Implement all backend services
- Create auto-detection engine
- Implement circuit breaker pattern

**Deliverables:**
- Complete backend implementations (mem0AI, SQLite, TinyDB, In-Memory)
- `AutoDetectionEngine` with health checking
- `CircuitBreaker` with state management
- Backend-specific tests

**Tasks:**
1. Implement mem0AI backend (enhance existing)
2. Implement SQLite backend with FTS
3. Implement TinyDB backend
4. Implement in-memory backend
5. Create auto-detection engine
6. Implement circuit breaker
7. Create comprehensive backend tests

### Phase 3: Service Integration (Week 5-6)

**Objectives:**
- Implement main FlexibleMemoryService
- Integrate with existing framework
- Create migration tools

**Deliverables:**
- `FlexibleMemoryService` with all features
- Framework integration points
- `DataMigrator` for backend migration
- Performance monitoring system

**Tasks:**
1. Implement FlexibleMemoryService
2. Create CMCP-init integration
3. Implement data migrator
4. Create performance monitoring
5. Integrate with agent delegation
6. Create CLI commands

### Phase 4: Testing and Optimization (Week 7-8)

**Objectives:**
- Comprehensive testing of all components
- Performance optimization
- Documentation completion

**Deliverables:**
- Complete test suite with >90% coverage
- Performance benchmarks
- Complete documentation
- Migration guides

**Tasks:**
1. Integration testing
2. Performance benchmarking
3. Load testing
4. Error handling testing
5. Documentation writing
6. Migration guide creation

### Phase 5: Deployment and Rollout (Week 9-10)

**Objectives:**
- Deploy to production
- Migrate existing integrations
- Monitor and stabilize

**Deliverables:**
- Production deployment
- Migrated existing integrations
- Monitoring dashboards
- Support documentation

**Tasks:**
1. Deploy to production environment
2. Migrate existing mem0AI integrations
3. Set up monitoring dashboards
4. Create support documentation
5. Train team on new system
6. Monitor and fix issues

### Rollback Plan

**Scenario 1: Performance Issues**
- Revert to mem0AI-only configuration
- Disable auto-detection temporarily
- Fix performance issues in isolated environment

**Scenario 2: Data Loss**
- Restore from backup created during migration
- Revert to previous configuration
- Investigate and fix data loss issues

**Scenario 3: Integration Failures**
- Disable flexible memory service
- Revert to direct mem0AI integration
- Fix integration issues offline

**Rollback Procedures:**
1. Stop memory service
2. Revert configuration to previous version
3. Restore data from backup if necessary
4. Restart with previous configuration
5. Investigate and fix issues

---

## Risk Assessment

### Technical Risks

**High Risk:**
1. **Data Migration Failures**
   - Risk: Loss of existing memory data during migration
   - Mitigation: Comprehensive backup and restore procedures, incremental migration
   - Contingency: Rollback to previous system with data restore

2. **Performance Degradation**
   - Risk: New system slower than direct mem0AI integration
   - Mitigation: Extensive performance testing, caching strategies
   - Contingency: Performance-optimized configuration, selective backend use

3. **Integration Compatibility**
   - Risk: Existing integrations break with new system
   - Mitigation: Compatibility wrapper, extensive testing
   - Contingency: Gradual rollout, parallel systems

**Medium Risk:**
1. **Circuit Breaker False Positives**
   - Risk: Healthy backends marked as unhealthy
   - Mitigation: Careful threshold tuning, multiple health checks
   - Contingency: Manual override capabilities

2. **Configuration Complexity**
   - Risk: Complex configuration leads to misconfigurations
   - Mitigation: Sensible defaults, validation, documentation
   - Contingency: Configuration validation tools

3. **Backend Inconsistencies**
   - Risk: Different backends behave differently
   - Mitigation: Comprehensive testing, standardized interfaces
   - Contingency: Backend-specific handling

**Low Risk:**
1. **Auto-Detection Failures**
   - Risk: Auto-detection selects wrong backend
   - Mitigation: Manual override options, detailed logging
   - Contingency: Manual backend selection

2. **Monitoring Overhead**
   - Risk: Monitoring impacts performance
   - Mitigation: Lightweight monitoring, configurable intervals
   - Contingency: Disable monitoring if needed

### Business Risks

**High Risk:**
1. **Service Disruption**
   - Risk: Memory service unavailable during migration
   - Mitigation: Gradual rollout, maintenance windows
   - Contingency: Rapid rollback procedures

2. **Data Loss**
   - Risk: Critical project data lost during migration
   - Mitigation: Multiple backups, verification procedures
   - Contingency: Data recovery procedures

**Medium Risk:**
1. **Training Requirements**
   - Risk: Team unfamiliar with new system
   - Mitigation: Comprehensive documentation, training sessions
   - Contingency: Expert support during transition

2. **Increased Complexity**
   - Risk: System more complex to maintain
   - Mitigation: Good documentation, monitoring tools
   - Contingency: Simplified configuration options

### Mitigation Strategies

**Pre-Implementation:**
1. Comprehensive testing in isolated environment
2. Performance benchmarking against current system
3. Data migration testing with non-critical data
4. Team training on new architecture

**During Implementation:**
1. Phased rollout starting with non-critical projects
2. Continuous monitoring of performance and health
3. Daily backups during migration period
4. On-call support during critical phases

**Post-Implementation:**
1. 24/7 monitoring for first week
2. Weekly performance reviews for first month
3. User feedback collection and response
4. Continuous optimization based on usage patterns

---

## Conclusion

This flexible memory architecture specification provides a comprehensive solution for making mem0AI optional in the Claude PM Framework while maintaining full functionality and enabling future enhancements. The architecture emphasizes:

1. **Transparency**: Users experience identical functionality regardless of backend
2. **Resilience**: Graceful degradation and automatic failover
3. **Performance**: Optimized for common use cases with intelligent caching
4. **Maintainability**: Clean architecture with clear separation of concerns
5. **Extensibility**: Easy to add new backends and features

The implementation plan provides a structured approach to deployment with clear milestones, risk mitigation strategies, and rollback procedures. The architecture will provide a robust foundation for the Claude PM Framework's memory management needs while ensuring reliability and performance.

**Next Steps:**
1. Review and approve architecture specification
2. Begin Phase 1 implementation
3. Set up development environment and testing framework
4. Create project team and assign responsibilities
5. Establish monitoring and success metrics

This architecture represents a significant enhancement to the Claude PM Framework, providing flexibility, reliability, and performance improvements while maintaining backward compatibility with existing integrations.