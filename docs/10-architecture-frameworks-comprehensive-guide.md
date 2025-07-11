# Architecture & Frameworks Comprehensive Guide - Claude PM Framework

## Overview

This comprehensive guide covers all architectural and framework aspects of the Claude PM Framework v4.5.1, including memory architecture specifications, ticketing system design, version control implementation, and core framework services architecture.

## Table of Contents

1. [Flexible Memory Architecture](#flexible-memory-architecture)
2. [Ticketing System Architecture](#ticketing-system-architecture)
3. [Version Control Agent Implementation](#version-control-agent-implementation)
4. [Framework Services Architecture](#framework-services-architecture)
5. [System Integration Architecture](#system-integration-architecture)
6. [Performance Architecture](#performance-architecture)
7. [Security Architecture](#security-architecture)
8. [Scalability Architecture](#scalability-architecture)

## Flexible Memory Architecture

### Overview

The Claude PM Framework implements a sophisticated flexible memory architecture that provides zero-configuration universal memory access with automatic service discovery and intelligent backend selection.

### Architecture Specification

#### Memory Backend Hierarchy

```python
# Memory backend selection hierarchy
MEMORY_BACKEND_HIERARCHY = {
    1: "mem0ai",      # Primary: Production-grade memory service
    2: "sqlite",      # Fallback: Local database storage
    3: "tinydb",      # Fallback: JSON-based database
    4: "memory"       # Fallback: In-memory storage (volatile)
}

# Backend capabilities matrix
BACKEND_CAPABILITIES = {
    "mem0ai": {
        "persistent": True,
        "searchable": True,
        "scalable": True,
        "concurrent": True,
        "remote": True,
        "ai_enhanced": True
    },
    "sqlite": {
        "persistent": True,
        "searchable": True,
        "scalable": False,
        "concurrent": True,
        "remote": False,
        "ai_enhanced": False
    },
    "tinydb": {
        "persistent": True,
        "searchable": False,
        "scalable": False,
        "concurrent": False,
        "remote": False,
        "ai_enhanced": False
    },
    "memory": {
        "persistent": False,
        "searchable": False,
        "scalable": False,
        "concurrent": True,
        "remote": False,
        "ai_enhanced": False
    }
}
```

#### Flexible Memory Service Architecture

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

class MemoryCategory(Enum):
    """Memory categories for organization."""
    PROJECT = "project"
    PATTERN = "pattern"
    TEAM = "team"
    ERROR = "error"
    DECISION = "decision"
    KNOWLEDGE = "knowledge"

@dataclass
class MemoryEntry:
    """Memory entry data structure."""
    id: str
    category: MemoryCategory
    content: str
    project_name: str
    metadata: Dict[str, Any]
    tags: List[str]
    timestamp: str
    
@dataclass
class MemoryResult:
    """Memory operation result."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    backend_used: Optional[str] = None

class MemoryBackend(ABC):
    """Abstract base class for memory backends."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the backend."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check backend health."""
        pass
    
    @abstractmethod
    async def store_memory(self, entry: MemoryEntry) -> MemoryResult:
        """Store memory entry."""
        pass
    
    @abstractmethod
    async def retrieve_memories(self, 
                              category: Optional[MemoryCategory] = None,
                              project_name: Optional[str] = None,
                              query: Optional[str] = None,
                              tags: Optional[List[str]] = None,
                              limit: int = 100) -> MemoryResult:
        """Retrieve memory entries."""
        pass
    
    @abstractmethod
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> MemoryResult:
        """Update memory entry."""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> MemoryResult:
        """Delete memory entry."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup backend resources."""
        pass

class FlexibleMemoryService:
    """Flexible memory service with automatic backend selection."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.backends: Dict[str, MemoryBackend] = {}
        self.active_backend: Optional[str] = None
        self.circuit_breaker_state: Dict[str, bool] = {}
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> bool:
        """Initialize memory service with backend discovery."""
        
        # Register available backends
        await self._register_backends()
        
        # Select best available backend
        return await self._select_backend()
    
    async def _register_backends(self):
        """Register all available memory backends."""
        
        # Try to register mem0AI backend
        try:
            from claude_pm.services.memory.backends.mem0ai_backend import Mem0AIBackend
            self.backends["mem0ai"] = Mem0AIBackend(self.config.get("mem0ai", {}))
            self.circuit_breaker_state["mem0ai"] = True
        except ImportError:
            self.logger.warning("Mem0AI backend not available")
        
        # Try to register SQLite backend
        try:
            from claude_pm.services.memory.backends.sqlite_backend import SQLiteBackend
            self.backends["sqlite"] = SQLiteBackend(self.config.get("sqlite", {}))
            self.circuit_breaker_state["sqlite"] = True
        except ImportError:
            self.logger.warning("SQLite backend not available")
        
        # Try to register TinyDB backend
        try:
            from claude_pm.services.memory.backends.tinydb_backend import TinyDBBackend
            self.backends["tinydb"] = TinyDBBackend(self.config.get("tinydb", {}))
            self.circuit_breaker_state["tinydb"] = True
        except ImportError:
            self.logger.warning("TinyDB backend not available")
        
        # Register in-memory backend (always available)
        from claude_pm.services.memory.backends.memory_backend import MemoryBackend
        self.backends["memory"] = MemoryBackend(self.config.get("memory", {}))
        self.circuit_breaker_state["memory"] = True
    
    async def _select_backend(self) -> bool:
        """Select the best available backend based on hierarchy."""
        
        for priority in sorted(MEMORY_BACKEND_HIERARCHY.keys()):
            backend_name = MEMORY_BACKEND_HIERARCHY[priority]
            
            if backend_name in self.backends and self.circuit_breaker_state.get(backend_name, False):
                backend = self.backends[backend_name]
                
                try:
                    # Test backend initialization and health
                    if await backend.initialize() and await backend.health_check():
                        self.active_backend = backend_name
                        self.logger.info(f"Selected memory backend: {backend_name}")
                        return True
                    else:
                        self.logger.warning(f"Backend {backend_name} failed initialization or health check")
                        self.circuit_breaker_state[backend_name] = False
                        
                except Exception as e:
                    self.logger.error(f"Backend {backend_name} initialization error: {e}")
                    self.circuit_breaker_state[backend_name] = False
        
        self.logger.error("No memory backend available")
        return False
    
    async def store_memory(self, 
                          category: MemoryCategory,
                          content: str,
                          project_name: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          tags: Optional[List[str]] = None) -> MemoryResult:
        """Store memory with automatic backend selection."""
        
        if not self.active_backend:
            return MemoryResult(success=False, error="No active memory backend")
        
        entry = MemoryEntry(
            id="",  # Backend will generate ID
            category=category,
            content=content,
            project_name=project_name,
            metadata=metadata or {},
            tags=tags or [],
            timestamp=""  # Backend will set timestamp
        )
        
        backend = self.backends[self.active_backend]
        
        try:
            result = await backend.store_memory(entry)
            result.backend_used = self.active_backend
            return result
            
        except Exception as e:
            self.logger.error(f"Memory storage failed on {self.active_backend}: {e}")
            
            # Try fallback backend
            return await self._try_fallback_operation("store_memory", entry)
    
    async def retrieve_memories(self,
                               category: Optional[MemoryCategory] = None,
                               project_name: Optional[str] = None,
                               query: Optional[str] = None,
                               tags: Optional[List[str]] = None,
                               limit: int = 100) -> MemoryResult:
        """Retrieve memories with automatic backend selection."""
        
        if not self.active_backend:
            return MemoryResult(success=False, error="No active memory backend")
        
        backend = self.backends[self.active_backend]
        
        try:
            result = await backend.retrieve_memories(
                category=category,
                project_name=project_name,
                query=query,
                tags=tags,
                limit=limit
            )
            result.backend_used = self.active_backend
            return result
            
        except Exception as e:
            self.logger.error(f"Memory retrieval failed on {self.active_backend}: {e}")
            
            # Try fallback backend
            return await self._try_fallback_operation(
                "retrieve_memories",
                category=category,
                project_name=project_name,
                query=query,
                tags=tags,
                limit=limit
            )
    
    async def _try_fallback_operation(self, operation: str, *args, **kwargs) -> MemoryResult:
        """Try operation on fallback backends."""
        
        current_priority = None
        for priority, backend_name in MEMORY_BACKEND_HIERARCHY.items():
            if backend_name == self.active_backend:
                current_priority = priority
                break
        
        if current_priority is None:
            return MemoryResult(success=False, error="Cannot determine fallback priority")
        
        # Try backends with lower priority (higher numbers)
        for priority in sorted(MEMORY_BACKEND_HIERARCHY.keys()):
            if priority <= current_priority:
                continue
                
            backend_name = MEMORY_BACKEND_HIERARCHY[priority]
            
            if (backend_name in self.backends and 
                self.circuit_breaker_state.get(backend_name, False)):
                
                backend = self.backends[backend_name]
                
                try:
                    if await backend.health_check():
                        method = getattr(backend, operation)
                        result = await method(*args, **kwargs)
                        result.backend_used = backend_name
                        
                        # Switch to this backend if operation succeeded
                        if result.success:
                            self.active_backend = backend_name
                            self.logger.info(f"Switched to fallback backend: {backend_name}")
                        
                        return result
                        
                except Exception as e:
                    self.logger.error(f"Fallback operation failed on {backend_name}: {e}")
                    self.circuit_breaker_state[backend_name] = False
        
        return MemoryResult(success=False, error="All fallback backends failed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all backends."""
        
        health_status = {
            "active_backend": self.active_backend,
            "backends": {}
        }
        
        for backend_name, backend in self.backends.items():
            try:
                healthy = await backend.health_check()
                health_status["backends"][backend_name] = {
                    "healthy": healthy,
                    "circuit_breaker": self.circuit_breaker_state.get(backend_name, False),
                    "capabilities": BACKEND_CAPABILITIES.get(backend_name, {})
                }
            except Exception as e:
                health_status["backends"][backend_name] = {
                    "healthy": False,
                    "error": str(e),
                    "circuit_breaker": False
                }
        
        return health_status
    
    async def get_backend_info(self) -> Dict[str, Any]:
        """Get information about available backends."""
        
        return {
            "hierarchy": MEMORY_BACKEND_HIERARCHY,
            "capabilities": BACKEND_CAPABILITIES,
            "available_backends": list(self.backends.keys()),
            "active_backend": self.active_backend,
            "circuit_breaker_states": self.circuit_breaker_state
        }
    
    async def switch_backend(self, backend_name: str) -> bool:
        """Manually switch to a specific backend."""
        
        if backend_name not in self.backends:
            self.logger.error(f"Backend {backend_name} not available")
            return False
        
        backend = self.backends[backend_name]
        
        try:
            if await backend.health_check():
                self.active_backend = backend_name
                self.circuit_breaker_state[backend_name] = True
                self.logger.info(f"Manually switched to backend: {backend_name}")
                return True
            else:
                self.logger.error(f"Backend {backend_name} failed health check")
                return False
                
        except Exception as e:
            self.logger.error(f"Error switching to backend {backend_name}: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup all backend resources."""
        
        for backend in self.backends.values():
            try:
                await backend.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up backend: {e}")
```

### Memory Service Integration

```python
# Zero-configuration memory access
def create_claude_pm_memory(config: Optional[Dict[str, Any]] = None) -> FlexibleMemoryService:
    """
    Create Claude PM memory service with zero configuration.
    
    This function provides automatic service discovery and configuration,
    eliminating setup complexity for users.
    """
    
    if config is None:
        config = {
            "mem0ai": {
                "host": os.getenv("CLAUDE_PM_MEMORY_HOST", "localhost"),
                "port": int(os.getenv("CLAUDE_PM_MEMORY_PORT", "8002")),
                "timeout": int(os.getenv("CLAUDE_PM_MEMORY_TIMEOUT", "30")),
                "api_key": os.getenv("CLAUDE_PM_MEMORY_API_KEY")
            },
            "sqlite": {
                "database_path": os.getenv("CLAUDE_PM_SQLITE_PATH", "~/.claude-pm/memory.db")
            },
            "tinydb": {
                "database_path": os.getenv("CLAUDE_PM_TINYDB_PATH", "~/.claude-pm/memory.json")
            },
            "memory": {
                "max_entries": int(os.getenv("CLAUDE_PM_MEMORY_MAX_ENTRIES", "10000"))
            }
        }
    
    return FlexibleMemoryService(config)

# Context manager for memory operations
@asynccontextmanager
async def claude_pm_memory_context(config: Optional[Dict[str, Any]] = None):
    """Context manager for Claude PM memory operations."""
    
    memory_service = create_claude_pm_memory(config)
    
    try:
        await memory_service.initialize()
        yield memory_service
    finally:
        await memory_service.cleanup()
```

## Ticketing System Architecture

### Overview

The Claude PM Framework includes a comprehensive ticketing system that integrates with multiple platforms and provides universal ticket management capabilities.

### Ticketing System Design

#### Universal Ticketing Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio

class TicketStatus(Enum):
    """Universal ticket status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    BLOCKED = "blocked"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class TicketPriority(Enum):
    """Universal ticket priority enumeration."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Ticket:
    """Universal ticket data structure."""
    id: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    assignee: Optional[str]
    reporter: str
    project: str
    labels: List[str]
    epic: Optional[str]
    milestone: Optional[str]
    story_points: Optional[int]
    created_date: str
    updated_date: str
    due_date: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class TicketComment:
    """Ticket comment data structure."""
    id: str
    ticket_id: str
    author: str
    content: str
    created_date: str
    metadata: Dict[str, Any]

class TicketingPlatform(ABC):
    """Abstract base class for ticketing platforms."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize platform connection."""
        pass
    
    @abstractmethod
    async def create_ticket(self, ticket: Ticket) -> str:
        """Create a new ticket."""
        pass
    
    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID."""
        pass
    
    @abstractmethod
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update ticket."""
        pass
    
    @abstractmethod
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete ticket."""
        pass
    
    @abstractmethod
    async def list_tickets(self, 
                          project: Optional[str] = None,
                          status: Optional[TicketStatus] = None,
                          assignee: Optional[str] = None,
                          limit: int = 100) -> List[Ticket]:
        """List tickets with filters."""
        pass
    
    @abstractmethod
    async def add_comment(self, ticket_id: str, comment: TicketComment) -> str:
        """Add comment to ticket."""
        pass
    
    @abstractmethod
    async def get_comments(self, ticket_id: str) -> List[TicketComment]:
        """Get ticket comments."""
        pass

class UniversalTicketingService:
    """Universal ticketing service supporting multiple platforms."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platforms: Dict[str, TicketingPlatform] = {}
        self.default_platform: Optional[str] = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize ticketing service with platform detection."""
        
        # Register available platforms
        await self._register_platforms()
        
        # Select default platform
        return await self._select_default_platform()
    
    async def _register_platforms(self):
        """Register available ticketing platforms."""
        
        # GitHub Issues
        if self.config.get("github", {}).get("enabled", False):
            try:
                from claude_pm.services.ticketing.platforms.github_platform import GitHubPlatform
                self.platforms["github"] = GitHubPlatform(self.config["github"])
            except ImportError:
                self.logger.warning("GitHub platform not available")
        
        # Jira
        if self.config.get("jira", {}).get("enabled", False):
            try:
                from claude_pm.services.ticketing.platforms.jira_platform import JiraPlatform
                self.platforms["jira"] = JiraPlatform(self.config["jira"])
            except ImportError:
                self.logger.warning("Jira platform not available")
        
        # Linear
        if self.config.get("linear", {}).get("enabled", False):
            try:
                from claude_pm.services.ticketing.platforms.linear_platform import LinearPlatform
                self.platforms["linear"] = LinearPlatform(self.config["linear"])
            except ImportError:
                self.logger.warning("Linear platform not available")
        
        # AI Trackdown (built-in)
        try:
            from claude_pm.services.ticketing.platforms.aitrackdown_platform import AITrackdownPlatform
            self.platforms["aitrackdown"] = AITrackdownPlatform(self.config.get("aitrackdown", {}))
        except ImportError:
            self.logger.warning("AI Trackdown platform not available")
    
    async def _select_default_platform(self) -> bool:
        """Select default platform based on configuration and availability."""
        
        # Try to initialize platforms in order of preference
        preference_order = self.config.get("platform_preference", 
                                          ["github", "jira", "linear", "aitrackdown"])
        
        for platform_name in preference_order:
            if platform_name in self.platforms:
                platform = self.platforms[platform_name]
                
                try:
                    if await platform.initialize():
                        self.default_platform = platform_name
                        self.logger.info(f"Selected ticketing platform: {platform_name}")
                        return True
                except Exception as e:
                    self.logger.error(f"Failed to initialize {platform_name}: {e}")
        
        self.logger.error("No ticketing platform available")
        return False
    
    async def create_ticket(self, 
                           title: str,
                           description: str,
                           project: str,
                           priority: TicketPriority = TicketPriority.MEDIUM,
                           assignee: Optional[str] = None,
                           labels: Optional[List[str]] = None,
                           epic: Optional[str] = None,
                           milestone: Optional[str] = None,
                           platform: Optional[str] = None) -> Optional[str]:
        """Create ticket on specified or default platform."""
        
        target_platform = platform or self.default_platform
        
        if target_platform not in self.platforms:
            self.logger.error(f"Platform {target_platform} not available")
            return None
        
        ticket = Ticket(
            id="",  # Platform will generate ID
            title=title,
            description=description,
            status=TicketStatus.OPEN,
            priority=priority,
            assignee=assignee,
            reporter="claude-pm",
            project=project,
            labels=labels or [],
            epic=epic,
            milestone=milestone,
            story_points=None,
            created_date="",  # Platform will set
            updated_date="",  # Platform will set
            due_date=None,
            metadata={}
        )
        
        platform_obj = self.platforms[target_platform]
        
        try:
            ticket_id = await platform_obj.create_ticket(ticket)
            self.logger.info(f"Created ticket {ticket_id} on {target_platform}")
            return ticket_id
        except Exception as e:
            self.logger.error(f"Failed to create ticket on {target_platform}: {e}")
            return None
    
    async def sync_tickets(self, source_platform: str, target_platform: str) -> Dict[str, Any]:
        """Sync tickets between platforms."""
        
        if source_platform not in self.platforms or target_platform not in self.platforms:
            return {"success": False, "error": "Platform not available"}
        
        source = self.platforms[source_platform]
        target = self.platforms[target_platform]
        
        try:
            # Get all tickets from source
            source_tickets = await source.list_tickets()
            
            sync_results = {
                "synced": 0,
                "failed": 0,
                "errors": []
            }
            
            for ticket in source_tickets:
                try:
                    # Create ticket on target platform
                    new_ticket_id = await target.create_ticket(ticket)
                    
                    if new_ticket_id:
                        sync_results["synced"] += 1
                    else:
                        sync_results["failed"] += 1
                        sync_results["errors"].append(f"Failed to create ticket: {ticket.title}")
                        
                except Exception as e:
                    sync_results["failed"] += 1
                    sync_results["errors"].append(f"Error syncing ticket {ticket.id}: {e}")
            
            return {"success": True, "results": sync_results}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all platforms."""
        
        status = {
            "platforms": {},
            "default_platform": self.default_platform
        }
        
        for platform_name, platform in self.platforms.items():
            try:
                # Test platform connectivity
                test_result = await platform.list_tickets(limit=1)
                status["platforms"][platform_name] = {
                    "available": True,
                    "initialized": True,
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                status["platforms"][platform_name] = {
                    "available": False,
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
        
        return status

# Ticketing agent integration
class TicketingAgent:
    """Agent for ticketing operations."""
    
    def __init__(self, ticketing_service: UniversalTicketingService):
        self.ticketing_service = ticketing_service
        self.logger = logging.getLogger(__name__)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ticketing task."""
        
        task_type = task.get("type")
        
        if task_type == "create_ticket":
            return await self._create_ticket_task(task)
        elif task_type == "update_ticket":
            return await self._update_ticket_task(task)
        elif task_type == "sync_tickets":
            return await self._sync_tickets_task(task)
        elif task_type == "list_tickets":
            return await self._list_tickets_task(task)
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
    
    async def _create_ticket_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create ticket task."""
        
        required_fields = ["title", "description", "project"]
        for field in required_fields:
            if field not in task:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        ticket_id = await self.ticketing_service.create_ticket(
            title=task["title"],
            description=task["description"],
            project=task["project"],
            priority=TicketPriority(task.get("priority", "medium")),
            assignee=task.get("assignee"),
            labels=task.get("labels"),
            epic=task.get("epic"),
            milestone=task.get("milestone"),
            platform=task.get("platform")
        )
        
        if ticket_id:
            return {"success": True, "ticket_id": ticket_id}
        else:
            return {"success": False, "error": "Failed to create ticket"}
```

## Version Control Agent Implementation

### Overview

The Claude PM Framework includes a comprehensive version control agent that handles Git operations, branch management, and repository coordination.

### Version Control Architecture

#### Git Operations Management

```python
import git
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
import shutil

class GitOperationType(Enum):
    """Git operation types."""
    BRANCH = "branch"
    MERGE = "merge"
    COMMIT = "commit"
    PUSH = "push"
    PULL = "pull"
    TAG = "tag"
    CLONE = "clone"
    FETCH = "fetch"

@dataclass
class GitRepository:
    """Git repository information."""
    path: str
    remote_url: str
    current_branch: str
    has_uncommitted_changes: bool
    branches: List[str]
    tags: List[str]

@dataclass
class GitOperationResult:
    """Git operation result."""
    success: bool
    operation: GitOperationType
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

class VersionControlAgent:
    """Version control agent for Git operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.repositories: Dict[str, git.Repo] = {}
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize version control agent."""
        
        try:
            # Discover repositories
            await self._discover_repositories()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize version control agent: {e}")
            return False
    
    async def _discover_repositories(self):
        """Discover Git repositories in configured paths."""
        
        search_paths = self.config.get("search_paths", ["."])
        
        for path in search_paths:
            try:
                repo = git.Repo(path, search_parent_directories=True)
                repo_path = repo.working_dir
                self.repositories[repo_path] = repo
                self.logger.info(f"Discovered repository: {repo_path}")
            except git.InvalidGitRepositoryError:
                self.logger.debug(f"No Git repository found at: {path}")
            except Exception as e:
                self.logger.error(f"Error checking repository at {path}: {e}")
    
    async def get_repository_info(self, repo_path: str) -> Optional[GitRepository]:
        """Get repository information."""
        
        if repo_path not in self.repositories:
            return None
        
        repo = self.repositories[repo_path]
        
        try:
            return GitRepository(
                path=repo_path,
                remote_url=repo.remotes.origin.url if repo.remotes else "",
                current_branch=repo.active_branch.name,
                has_uncommitted_changes=repo.is_dirty(untracked_files=True),
                branches=[branch.name for branch in repo.branches],
                tags=[tag.name for tag in repo.tags]
            )
        except Exception as e:
            self.logger.error(f"Error getting repository info for {repo_path}: {e}")
            return None
    
    async def create_branch(self, 
                           repo_path: str, 
                           branch_name: str, 
                           from_branch: Optional[str] = None) -> GitOperationResult:
        """Create a new branch."""
        
        if repo_path not in self.repositories:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.BRANCH,
                message=f"Repository not found: {repo_path}",
                error="Repository not found"
            )
        
        repo = self.repositories[repo_path]
        
        try:
            # Check if branch already exists
            if branch_name in [branch.name for branch in repo.branches]:
                return GitOperationResult(
                    success=False,
                    operation=GitOperationType.BRANCH,
                    message=f"Branch {branch_name} already exists",
                    error="Branch already exists"
                )
            
            # Create new branch
            if from_branch:
                source_branch = repo.heads[from_branch]
                new_branch = repo.create_head(branch_name, source_branch)
            else:
                new_branch = repo.create_head(branch_name)
            
            # Checkout new branch
            new_branch.checkout()
            
            return GitOperationResult(
                success=True,
                operation=GitOperationType.BRANCH,
                message=f"Created and checked out branch: {branch_name}",
                data={"branch_name": branch_name, "from_branch": from_branch}
            )
            
        except Exception as e:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.BRANCH,
                message=f"Failed to create branch {branch_name}",
                error=str(e)
            )
    
    async def merge_branch(self, 
                          repo_path: str, 
                          source_branch: str, 
                          target_branch: str,
                          strategy: str = "merge") -> GitOperationResult:
        """Merge branches with conflict resolution."""
        
        if repo_path not in self.repositories:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.MERGE,
                message=f"Repository not found: {repo_path}",
                error="Repository not found"
            )
        
        repo = self.repositories[repo_path]
        
        try:
            # Checkout target branch
            target = repo.heads[target_branch]
            target.checkout()
            
            # Perform merge
            source = repo.heads[source_branch]
            
            if strategy == "merge":
                # Regular merge
                repo.git.merge(source.name)
            elif strategy == "squash":
                # Squash merge
                repo.git.merge(source.name, squash=True)
            elif strategy == "rebase":
                # Rebase merge
                repo.git.rebase(source.name)
            else:
                return GitOperationResult(
                    success=False,
                    operation=GitOperationType.MERGE,
                    message=f"Unknown merge strategy: {strategy}",
                    error="Invalid merge strategy"
                )
            
            return GitOperationResult(
                success=True,
                operation=GitOperationType.MERGE,
                message=f"Merged {source_branch} into {target_branch}",
                data={
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "strategy": strategy
                }
            )
            
        except git.GitCommandError as e:
            # Handle merge conflicts
            if "CONFLICT" in str(e):
                conflict_files = self._get_conflict_files(repo)
                return GitOperationResult(
                    success=False,
                    operation=GitOperationType.MERGE,
                    message=f"Merge conflicts detected",
                    error="Merge conflicts",
                    data={"conflict_files": conflict_files}
                )
            else:
                return GitOperationResult(
                    success=False,
                    operation=GitOperationType.MERGE,
                    message=f"Merge failed: {e}",
                    error=str(e)
                )
        except Exception as e:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.MERGE,
                message=f"Failed to merge {source_branch} into {target_branch}",
                error=str(e)
            )
    
    def _get_conflict_files(self, repo: git.Repo) -> List[str]:
        """Get list of files with merge conflicts."""
        
        try:
            # Get unmerged files
            unmerged_files = []
            for item in repo.index.unmerged_blobs():
                unmerged_files.append(item[0])
            return list(set(unmerged_files))
        except Exception:
            return []
    
    async def resolve_conflicts(self, 
                               repo_path: str, 
                               resolution_strategy: str = "manual") -> GitOperationResult:
        """Resolve merge conflicts."""
        
        if repo_path not in self.repositories:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.MERGE,
                message=f"Repository not found: {repo_path}",
                error="Repository not found"
            )
        
        repo = self.repositories[repo_path]
        
        try:
            conflict_files = self._get_conflict_files(repo)
            
            if not conflict_files:
                return GitOperationResult(
                    success=True,
                    operation=GitOperationType.MERGE,
                    message="No conflicts to resolve"
                )
            
            resolved_files = []
            
            if resolution_strategy == "ours":
                # Use our version
                for file_path in conflict_files:
                    repo.git.checkout("--ours", file_path)
                    repo.index.add([file_path])
                    resolved_files.append(file_path)
            
            elif resolution_strategy == "theirs":
                # Use their version
                for file_path in conflict_files:
                    repo.git.checkout("--theirs", file_path)
                    repo.index.add([file_path])
                    resolved_files.append(file_path)
            
            elif resolution_strategy == "manual":
                # Manual resolution required
                return GitOperationResult(
                    success=False,
                    operation=GitOperationType.MERGE,
                    message="Manual conflict resolution required",
                    data={"conflict_files": conflict_files}
                )
            
            # Commit the resolution
            repo.index.commit("Resolve merge conflicts")
            
            return GitOperationResult(
                success=True,
                operation=GitOperationType.MERGE,
                message=f"Resolved conflicts using {resolution_strategy} strategy",
                data={"resolved_files": resolved_files}
            )
            
        except Exception as e:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.MERGE,
                message=f"Failed to resolve conflicts",
                error=str(e)
            )
    
    async def push_changes(self, 
                          repo_path: str, 
                          branch: Optional[str] = None,
                          force: bool = False) -> GitOperationResult:
        """Push changes to remote repository."""
        
        if repo_path not in self.repositories:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.PUSH,
                message=f"Repository not found: {repo_path}",
                error="Repository not found"
            )
        
        repo = self.repositories[repo_path]
        
        try:
            if not repo.remotes:
                return GitOperationResult(
                    success=False,
                    operation=GitOperationType.PUSH,
                    message="No remote repository configured",
                    error="No remote configured"
                )
            
            remote = repo.remotes.origin
            push_branch = branch or repo.active_branch.name
            
            if force:
                push_result = remote.push(push_branch, force=True)
            else:
                push_result = remote.push(push_branch)
            
            return GitOperationResult(
                success=True,
                operation=GitOperationType.PUSH,
                message=f"Pushed {push_branch} to {remote.url}",
                data={
                    "branch": push_branch,
                    "remote": remote.url,
                    "force": force
                }
            )
            
        except Exception as e:
            return GitOperationResult(
                success=False,
                operation=GitOperationType.PUSH,
                message=f"Failed to push changes",
                error=str(e)
            )
    
    async def execute_git_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Git task."""
        
        operation = task.get("operation")
        repo_path = task.get("repo_path", ".")
        
        if operation == "create_branch":
            result = await self.create_branch(
                repo_path=repo_path,
                branch_name=task["branch_name"],
                from_branch=task.get("from_branch")
            )
        elif operation == "merge_branch":
            result = await self.merge_branch(
                repo_path=repo_path,
                source_branch=task["source_branch"],
                target_branch=task["target_branch"],
                strategy=task.get("strategy", "merge")
            )
        elif operation == "push_changes":
            result = await self.push_changes(
                repo_path=repo_path,
                branch=task.get("branch"),
                force=task.get("force", False)
            )
        elif operation == "resolve_conflicts":
            result = await self.resolve_conflicts(
                repo_path=repo_path,
                resolution_strategy=task.get("resolution_strategy", "manual")
            )
        else:
            result = GitOperationResult(
                success=False,
                operation=GitOperationType.BRANCH,
                message=f"Unknown operation: {operation}",
                error="Unknown operation"
            )
        
        return {
            "success": result.success,
            "operation": result.operation.value,
            "message": result.message,
            "data": result.data,
            "error": result.error
        }
```

## Framework Services Architecture

### Core Services Overview

The Claude PM Framework is built on a service-oriented architecture with clear separation of concerns and well-defined interfaces.

### Service Registry

```python
# services.py - Core framework services
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

class ServiceStatus(Enum):
    """Service status enumeration."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class ServiceInfo:
    """Service information structure."""
    name: str
    description: str
    version: str
    status: ServiceStatus
    dependencies: List[str]
    port: Optional[int]
    health_endpoint: Optional[str]

class Service(ABC):
    """Abstract base class for framework services."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.status = ServiceStatus.STOPPED
        self.logger = logging.getLogger(f"service.{name}")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the service."""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the service."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        pass
    
    def get_info(self) -> ServiceInfo:
        """Get service information."""
        return ServiceInfo(
            name=self.name,
            description=self.get_description(),
            version=self.get_version(),
            status=self.status,
            dependencies=self.get_dependencies(),
            port=self.get_port(),
            health_endpoint=self.get_health_endpoint()
        )
    
    @abstractmethod
    def get_description(self) -> str:
        """Get service description."""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get service version."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get service dependencies."""
        pass
    
    def get_port(self) -> Optional[int]:
        """Get service port (if applicable)."""
        return None
    
    def get_health_endpoint(self) -> Optional[str]:
        """Get health check endpoint (if applicable)."""
        return None

class ServiceRegistry:
    """Service registry for managing framework services."""
    
    def __init__(self):
        self.services: Dict[str, Service] = {}
        self.service_order: List[str] = []
        self.logger = logging.getLogger("service_registry")
    
    def register_service(self, service: Service):
        """Register a service."""
        self.services[service.name] = service
        self._update_service_order()
        self.logger.info(f"Registered service: {service.name}")
    
    def get_service(self, name: str) -> Optional[Service]:
        """Get service by name."""
        return self.services.get(name)
    
    def get_all_services(self) -> Dict[str, Service]:
        """Get all registered services."""
        return self.services.copy()
    
    def _update_service_order(self):
        """Update service startup order based on dependencies."""
        # Topological sort based on dependencies
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected: {service_name}")
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            if service_name in self.services:
                service = self.services[service_name]
                for dependency in service.get_dependencies():
                    visit(dependency)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        for service_name in self.services:
            if service_name not in visited:
                visit(service_name)
        
        self.service_order = order
    
    async def start_all_services(self) -> bool:
        """Start all services in dependency order."""
        success = True
        
        for service_name in self.service_order:
            service = self.services[service_name]
            
            try:
                self.logger.info(f"Starting service: {service_name}")
                if await service.initialize() and await service.start():
                    self.logger.info(f"Service started: {service_name}")
                else:
                    self.logger.error(f"Failed to start service: {service_name}")
                    success = False
                    break
            except Exception as e:
                self.logger.error(f"Error starting service {service_name}: {e}")
                success = False
                break
        
        return success
    
    async def stop_all_services(self) -> bool:
        """Stop all services in reverse dependency order."""
        success = True
        
        for service_name in reversed(self.service_order):
            service = self.services[service_name]
            
            try:
                self.logger.info(f"Stopping service: {service_name}")
                if await service.stop():
                    self.logger.info(f"Service stopped: {service_name}")
                else:
                    self.logger.error(f"Failed to stop service: {service_name}")
                    success = False
            except Exception as e:
                self.logger.error(f"Error stopping service {service_name}: {e}")
                success = False
        
        return success
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        health_status = {
            "overall_status": "healthy",
            "services": {},
            "total_services": len(self.services),
            "healthy_services": 0,
            "unhealthy_services": 0
        }
        
        for service_name, service in self.services.items():
            try:
                service_health = await service.health_check()
                health_status["services"][service_name] = service_health
                
                if service_health.get("status") == "healthy":
                    health_status["healthy_services"] += 1
                else:
                    health_status["unhealthy_services"] += 1
                    
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["unhealthy_services"] += 1
        
        # Determine overall status
        if health_status["unhealthy_services"] == 0:
            health_status["overall_status"] = "healthy"
        elif health_status["healthy_services"] > health_status["unhealthy_services"]:
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "unhealthy"
        
        return health_status

# Framework service registry instance
framework_registry = ServiceRegistry()
```

## Summary

This comprehensive architecture and frameworks guide provides:

### Core Architecture Components
- **Flexible Memory Architecture**: Zero-configuration memory access with automatic backend selection
- **Ticketing System Architecture**: Universal ticketing interface supporting multiple platforms
- **Version Control Implementation**: Comprehensive Git operations and branch management
- **Framework Services Architecture**: Service-oriented architecture with dependency management

### Architectural Patterns
- **Backend Hierarchy**: Intelligent fallback system with circuit breaker pattern
- **Universal Interfaces**: Platform-agnostic interfaces for consistent operations
- **Service Registry**: Centralized service management with dependency resolution
- **Automatic Discovery**: Zero-configuration service discovery and initialization

### Integration Features
- **Multi-Platform Support**: Support for GitHub, Jira, Linear, and AI Trackdown
- **Flexible Backends**: Multiple memory backends with automatic selection
- **Service Dependencies**: Proper dependency management and startup ordering
- **Health Monitoring**: Comprehensive health checking across all components

### Best Practices
- **Zero Configuration**: Automatic service discovery and configuration
- **Graceful Degradation**: Fallback mechanisms for service failures
- **Circuit Breaker Pattern**: Protection against cascading failures
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

The Claude PM Framework architecture ensures scalability, reliability, and maintainability through well-designed patterns, comprehensive interfaces, and robust error handling.

---

**Framework Version**: 4.5.1  
**Last Updated**: 2025-07-11  
**Architecture Guide Version**: 2.0.0  
**Authority Level**: Complete Architecture Management