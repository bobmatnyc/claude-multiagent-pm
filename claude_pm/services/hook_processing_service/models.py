"""
Data models and enums for hook processing service.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable


class HookType(Enum):
    """Enumeration of supported hook types."""
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    SUBAGENT_STOP = "subagent_stop"
    ERROR_DETECTION = "error_detection"
    PERFORMANCE_MONITOR = "performance_monitor"
    WORKFLOW_TRANSITION = "workflow_transition"


class ErrorSeverity(Enum):
    """Error severity levels for hook processing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HookExecutionResult:
    """Result of hook execution with metadata."""
    hook_id: str
    success: bool
    execution_time: float
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorDetectionResult:
    """Result of error detection analysis."""
    error_detected: bool
    error_type: str
    severity: ErrorSeverity
    details: Dict[str, Any]
    suggested_action: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HookConfiguration:
    """Configuration for a single hook."""
    hook_id: str
    hook_type: HookType
    handler: Callable
    priority: int = 0
    enabled: bool = True
    timeout: float = 30.0
    retry_count: int = 3
    prefer_async: bool = True  # Default to async execution
    force_sync: bool = False   # Override to force sync execution
    metadata: Dict[str, Any] = field(default_factory=dict)