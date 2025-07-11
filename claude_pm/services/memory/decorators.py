"""
Memory Trigger Decorators

Decorators and utilities for automatic memory capture throughout the
Claude PM Framework. Provides easy-to-use decorators for functions
and methods to automatically trigger memory creation.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generic
from functools import wraps
from dataclasses import dataclass, field
import inspect

from .trigger_types import TriggerType, TriggerPriority
from .interfaces.models import MemoryCategory

# Forward declarations to avoid circular imports
FrameworkMemoryHooks = None
TriggerResult = None

# Simple HookContext implementation to avoid circular imports
@dataclass
class HookContext:
    """Context information for memory hook execution."""
    
    operation_name: str
    project_name: str
    source: str
    start_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def duration_ms(self) -> float:
        """Get operation duration in milliseconds."""
        return (time.time() - self.start_time) * 1000


# Global hooks instance (will be set during initialization)
_global_hooks: Optional[FrameworkMemoryHooks] = None


def set_global_hooks(hooks):
    """Set the global hooks instance."""
    global _global_hooks
    _global_hooks = hooks


def get_global_hooks():
    """Get the global hooks instance."""
    return _global_hooks


F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class MemoryTriggerConfig:
    """Configuration for memory trigger decorators."""
    
    trigger_type: Optional[TriggerType] = None
    priority: TriggerPriority = TriggerPriority.MEDIUM
    category: MemoryCategory = MemoryCategory.PROJECT
    project_name: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    capture_on_success: bool = True
    capture_on_error: bool = True
    capture_args: bool = False
    capture_result: bool = False
    content_template: Optional[str] = None
    hook_type: Optional[str] = None


def memory_trigger(
    trigger_type: Optional[TriggerType] = None,
    priority: TriggerPriority = TriggerPriority.MEDIUM,
    category: MemoryCategory = MemoryCategory.PROJECT,
    project_name: Optional[str] = None,
    source: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    capture_on_success: bool = True,
    capture_on_error: bool = True,
    capture_args: bool = False,
    capture_result: bool = False,
    content_template: Optional[str] = None,
    hook_type: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator for automatic memory trigger creation.
    
    Args:
        trigger_type: Type of trigger to create
        priority: Priority of the trigger
        category: Memory category
        project_name: Project name (auto-detected if None)
        source: Source identifier (auto-detected if None)
        tags: Additional tags for the memory
        metadata: Additional metadata
        capture_on_success: Whether to capture on successful execution
        capture_on_error: Whether to capture on error
        capture_args: Whether to capture function arguments
        capture_result: Whether to capture function result
        content_template: Template for memory content
        hook_type: Specific hook type to use
        
    Returns:
        Decorated function
    """
    
    def decorator(func: F) -> F:
        # Create configuration
        config = MemoryTriggerConfig(
            trigger_type=trigger_type,
            priority=priority,
            category=category,
            project_name=project_name,
            source=source or f"{func.__module__}.{func.__name__}",
            tags=tags or [],
            metadata=metadata or {},
            capture_on_success=capture_on_success,
            capture_on_error=capture_on_error,
            capture_args=capture_args,
            capture_result=capture_result,
            content_template=content_template,
            hook_type=hook_type
        )
        
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await _execute_with_memory_trigger(func, config, args, kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return _execute_sync_with_memory_trigger(func, config, args, kwargs)
            return sync_wrapper
    
    return decorator


def workflow_memory_trigger(
    project_name: Optional[str] = None,
    workflow_type: Optional[str] = None,
    priority: TriggerPriority = TriggerPriority.HIGH,
    capture_result: bool = True
) -> Callable[[F], F]:
    """
    Decorator for workflow memory triggers.
    
    Args:
        project_name: Project name
        workflow_type: Type of workflow
        priority: Trigger priority
        capture_result: Whether to capture workflow result
        
    Returns:
        Decorated function
    """
    return memory_trigger(
        trigger_type=TriggerType.WORKFLOW_COMPLETION,
        priority=priority,
        category=MemoryCategory.PATTERN,
        project_name=project_name,
        tags=["workflow", workflow_type] if workflow_type else ["workflow"],
        capture_result=capture_result,
        hook_type="workflow_complete"
    )


def agent_memory_trigger(
    agent_type: str,
    project_name: Optional[str] = None,
    priority: TriggerPriority = TriggerPriority.MEDIUM,
    capture_result: bool = True
) -> Callable[[F], F]:
    """
    Decorator for agent operation memory triggers.
    
    Args:
        agent_type: Type of agent
        project_name: Project name
        priority: Trigger priority
        capture_result: Whether to capture operation result
        
    Returns:
        Decorated function
    """
    return memory_trigger(
        trigger_type=TriggerType.AGENT_OPERATION,
        priority=priority,
        category=MemoryCategory.PATTERN,
        project_name=project_name,
        source=f"{agent_type}_agent",
        tags=["agent_operation", agent_type],
        metadata={"agent_type": agent_type},
        capture_result=capture_result,
        hook_type="agent_operation_complete"
    )


def issue_memory_trigger(
    issue_id: Optional[str] = None,
    project_name: Optional[str] = None,
    priority: TriggerPriority = TriggerPriority.HIGH
) -> Callable[[F], F]:
    """
    Decorator for issue resolution memory triggers.
    
    Args:
        issue_id: Issue identifier
        project_name: Project name
        priority: Trigger priority
        
    Returns:
        Decorated function
    """
    return memory_trigger(
        trigger_type=TriggerType.ISSUE_RESOLUTION,
        priority=priority,
        category=MemoryCategory.PROJECT,
        project_name=project_name,
        tags=["issue_resolution", issue_id] if issue_id else ["issue_resolution"],
        metadata={"issue_id": issue_id} if issue_id else {},
        hook_type="issue_resolved"
    )


def error_memory_trigger(
    error_type: Optional[str] = None,
    project_name: Optional[str] = None,
    priority: TriggerPriority = TriggerPriority.CRITICAL
) -> Callable[[F], F]:
    """
    Decorator for error resolution memory triggers.
    
    Args:
        error_type: Type of error
        project_name: Project name
        priority: Trigger priority
        
    Returns:
        Decorated function
    """
    return memory_trigger(
        trigger_type=TriggerType.ERROR_RESOLUTION,
        priority=priority,
        category=MemoryCategory.ERROR,
        project_name=project_name,
        tags=["error_resolution", error_type] if error_type else ["error_resolution"],
        metadata={"error_type": error_type} if error_type else {},
        capture_on_error=True,
        hook_type="error_resolution"
    )


def knowledge_memory_trigger(
    knowledge_type: str,
    project_name: Optional[str] = None,
    priority: TriggerPriority = TriggerPriority.MEDIUM
) -> Callable[[F], F]:
    """
    Decorator for knowledge capture memory triggers.
    
    Args:
        knowledge_type: Type of knowledge
        project_name: Project name
        priority: Trigger priority
        
    Returns:
        Decorated function
    """
    return memory_trigger(
        trigger_type=TriggerType.KNOWLEDGE_CAPTURE,
        priority=priority,
        category=MemoryCategory.PATTERN,
        project_name=project_name,
        tags=["knowledge_capture", knowledge_type],
        metadata={"knowledge_type": knowledge_type},
        hook_type="knowledge_capture"
    )


def decision_memory_trigger(
    decision_type: str,
    project_name: Optional[str] = None,
    priority: TriggerPriority = TriggerPriority.HIGH
) -> Callable[[F], F]:
    """
    Decorator for decision point memory triggers.
    
    Args:
        decision_type: Type of decision
        project_name: Project name
        priority: Trigger priority
        
    Returns:
        Decorated function
    """
    return memory_trigger(
        trigger_type=TriggerType.DECISION_POINT,
        priority=priority,
        category=MemoryCategory.PROJECT,
        project_name=project_name,
        tags=["decision_point", decision_type],
        metadata={"decision_type": decision_type},
        hook_type="decision_point"
    )


async def _execute_with_memory_trigger(
    func: Callable,
    config: MemoryTriggerConfig,
    args: tuple,
    kwargs: dict
) -> Any:
    """Execute async function with memory trigger."""
    hooks = get_global_hooks()
    if not hooks:
        # No hooks configured, execute function normally
        return await func(*args, **kwargs)
    
    # Determine project name
    project_name = config.project_name or _extract_project_name(args, kwargs)
    
    # Create hook context
    context = HookContext(
        operation_name=func.__name__,
        project_name=project_name,
        source=config.source,
        metadata=config.metadata.copy(),
        tags=config.tags.copy()
    )
    
    # Add function arguments if requested
    if config.capture_args:
        context.metadata["function_args"] = _sanitize_args(args, kwargs)
    
    success = False
    result = None
    error = None
    
    try:
        # Execute function
        result = await func(*args, **kwargs)
        success = True
        
        # Add result if requested
        if config.capture_result:
            context.metadata["function_result"] = _sanitize_result(result)
        
        # Execute success hook
        if config.capture_on_success and config.hook_type:
            hook_kwargs = {
                "success": True,
                "result": result,
                **context.metadata
            }
            
            # Add specific hook metadata
            if config.hook_type == "workflow_complete":
                hook_kwargs["workflow_type"] = config.metadata.get("workflow_type")
            elif config.hook_type == "agent_operation_complete":
                hook_kwargs["agent_type"] = config.metadata.get("agent_type")
            elif config.hook_type == "issue_resolved":
                hook_kwargs["issue_id"] = config.metadata.get("issue_id")
                hook_kwargs["resolution"] = _sanitize_result(result)
            
            await hooks.execute_hook(config.hook_type, context, **hook_kwargs)
        
        return result
        
    except Exception as e:
        error = e
        success = False
        
        # Add error information
        context.metadata["error"] = str(e)
        context.metadata["error_type"] = type(e).__name__
        
        # Execute error hook
        if config.capture_on_error:
            error_hook_type = config.hook_type + "_error" if config.hook_type else "error_resolution"
            hook_kwargs = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                **context.metadata
            }
            
            await hooks.execute_hook(error_hook_type, context, **hook_kwargs)
        
        raise


def _execute_sync_with_memory_trigger(
    func: Callable,
    config: MemoryTriggerConfig,
    args: tuple,
    kwargs: dict
) -> Any:
    """Execute sync function with memory trigger."""
    hooks = get_global_hooks()
    if not hooks:
        # No hooks configured, execute function normally
        return func(*args, **kwargs)
    
    # For sync functions, we need to handle async hooks differently
    # For now, just execute the function without memory triggers
    # TODO: Implement proper sync hook execution
    return func(*args, **kwargs)


def _extract_project_name(args: tuple, kwargs: dict) -> str:
    """Extract project name from function arguments."""
    # Look for common project name arguments
    project_name_keys = ["project_name", "project", "project_id"]
    
    for key in project_name_keys:
        if key in kwargs:
            return str(kwargs[key])
    
    # Look in positional arguments
    for arg in args:
        if hasattr(arg, "project_name"):
            return str(arg.project_name)
        elif hasattr(arg, "project"):
            return str(arg.project)
    
    # Default project name
    return "unknown"


def _sanitize_args(args: tuple, kwargs: dict) -> dict:
    """Sanitize function arguments for memory storage."""
    sanitized = {}
    
    # Sanitize positional arguments
    if args:
        sanitized["args"] = [_sanitize_value(arg) for arg in args]
    
    # Sanitize keyword arguments
    if kwargs:
        sanitized["kwargs"] = {
            key: _sanitize_value(value) 
            for key, value in kwargs.items()
        }
    
    return sanitized


def _sanitize_result(result: Any) -> Any:
    """Sanitize function result for memory storage."""
    return _sanitize_value(result)


def _sanitize_value(value: Any) -> Any:
    """Sanitize a value for memory storage."""
    # Handle None
    if value is None:
        return None
    
    # Handle basic types
    if isinstance(value, (str, int, float, bool)):
        return value
    
    # Handle lists
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value[:10]]  # Limit size
    
    # Handle dictionaries
    if isinstance(value, dict):
        return {
            key: _sanitize_value(val) 
            for key, val in list(value.items())[:10]  # Limit size
        }
    
    # Handle tuples
    if isinstance(value, tuple):
        return tuple(_sanitize_value(item) for item in value[:10])  # Limit size
    
    # Handle sets
    if isinstance(value, set):
        return list(_sanitize_value(item) for item in list(value)[:10])  # Limit size
    
    # Handle objects with __dict__
    if hasattr(value, "__dict__"):
        return {
            key: _sanitize_value(val) 
            for key, val in list(value.__dict__.items())[:5]  # Limit size
        }
    
    # Handle other types by converting to string
    return str(value)[:1000]  # Limit string length


# Context managers for memory triggers

class MemoryTriggerContext:
    """Context manager for memory triggers."""
    
    def __init__(
        self,
        operation_name: str,
        project_name: str,
        source: str,
        hook_type: str,
        **kwargs
    ):
        self.operation_name = operation_name
        self.project_name = project_name
        self.source = source
        self.hook_type = hook_type
        self.kwargs = kwargs
        self.context: Optional[HookContext] = None
        self.hooks = get_global_hooks()
    
    async def __aenter__(self):
        """Enter context manager."""
        if self.hooks:
            self.context = HookContext(
                operation_name=self.operation_name,
                project_name=self.project_name,
                source=self.source,
                metadata=self.kwargs.copy()
            )
            
            # Execute start hook
            start_hook_type = self.hook_type + "_start"
            await self.hooks.execute_hook(start_hook_type, self.context, **self.kwargs)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.hooks and self.context:
            # Update context with result
            success = exc_type is None
            self.context.metadata["success"] = success
            
            if not success:
                self.context.metadata["error"] = str(exc_val)
                self.context.metadata["error_type"] = exc_type.__name__
            
            # Execute completion hook
            complete_hook_type = self.hook_type + "_complete"
            await self.hooks.execute_hook(
                complete_hook_type, 
                self.context, 
                success=success,
                **self.kwargs
            )
    
    def set_result(self, result: Any):
        """Set operation result."""
        if self.context:
            self.context.metadata["result"] = _sanitize_result(result)
    
    def add_metadata(self, **metadata):
        """Add metadata to context."""
        if self.context:
            self.context.metadata.update(metadata)
    
    def add_tags(self, *tags):
        """Add tags to context."""
        if self.context:
            self.context.tags.extend(tags)


def workflow_trigger_context(
    operation_name: str,
    project_name: str,
    workflow_type: Optional[str] = None,
    **kwargs
) -> MemoryTriggerContext:
    """Create a workflow trigger context manager."""
    return MemoryTriggerContext(
        operation_name=operation_name,
        project_name=project_name,
        source="workflow",
        hook_type="workflow",
        workflow_type=workflow_type,
        **kwargs
    )


def agent_trigger_context(
    operation_name: str,
    project_name: str,
    agent_type: str,
    **kwargs
) -> MemoryTriggerContext:
    """Create an agent trigger context manager."""
    return MemoryTriggerContext(
        operation_name=operation_name,
        project_name=project_name,
        source=f"{agent_type}_agent",
        hook_type="agent_operation",
        agent_type=agent_type,
        **kwargs
    )


def issue_trigger_context(
    operation_name: str,
    project_name: str,
    issue_id: str,
    **kwargs
) -> MemoryTriggerContext:
    """Create an issue trigger context manager."""
    return MemoryTriggerContext(
        operation_name=operation_name,
        project_name=project_name,
        source="issue_tracker",
        hook_type="issue",
        issue_id=issue_id,
        **kwargs
    )


# Utility functions

def trigger_immediate_memory(
    project_name: str,
    content: str,
    category: MemoryCategory = MemoryCategory.PROJECT,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    source: str = "manual"
):
    """
    Trigger immediate memory creation.
    
    Args:
        project_name: Project name
        content: Memory content
        category: Memory category
        tags: Memory tags
        metadata: Memory metadata
        source: Source identifier
        
    Returns:
        Optional[TriggerResult]: Result if hooks available
    """
    hooks = get_global_hooks()
    if not hooks:
        return None
    
    # Create a simple context object
    class SimpleContext:
        def __init__(self, operation_name, project_name, source, metadata, tags):
            self.operation_name = operation_name
            self.project_name = project_name
            self.source = source
            self.metadata = metadata or {}
            self.tags = tags or []
    
    context = SimpleContext(
        operation_name="manual_memory",
        project_name=project_name,
        source=source,
        metadata=metadata or {},
        tags=tags or []
    )
    
    # Create async task to execute hook
    async def execute_hook():
        return await hooks.knowledge_capture(
            context,
            content=content,
            knowledge_type="manual",
            category=category.value
        )
    
    # Execute in event loop
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(execute_hook())
    except RuntimeError:
        # No event loop running
        return None


def is_memory_triggers_enabled() -> bool:
    """Check if memory triggers are enabled."""
    hooks = get_global_hooks()
    return hooks is not None and hooks._enabled


def get_memory_trigger_metrics() -> Dict[str, Any]:
    """Get memory trigger metrics."""
    hooks = get_global_hooks()
    if not hooks:
        return {"enabled": False, "hooks_available": False}
    
    return {
        "enabled": True,
        "hooks_available": True,
        **hooks.get_metrics()
    }