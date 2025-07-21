"""
Orchestration Types and Data Classes
===================================

This module contains type definitions, enums, and data classes used by the
backwards compatible orchestrator.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, Dict


class OrchestrationMode(Enum):
    """Orchestration modes for the backwards compatible orchestrator."""
    LOCAL = "local"
    SUBPROCESS = "subprocess"
    HYBRID = "hybrid"


class ReturnCode:
    """Return codes for orchestration operations."""
    SUCCESS = 0
    GENERAL_FAILURE = 1
    TIMEOUT = 2
    CONTEXT_FILTERING_ERROR = 3
    AGENT_NOT_FOUND = 4
    MESSAGE_BUS_ERROR = 5


@dataclass
class OrchestrationMetrics:
    """Metrics for orchestration performance tracking."""
    mode: OrchestrationMode
    decision_time_ms: float
    execution_time_ms: float
    fallback_reason: Optional[str] = None
    context_filtering_time_ms: float = 0.0
    message_routing_time_ms: float = 0.0
    context_size_original: int = 0
    context_size_filtered: int = 0
    token_reduction_percent: float = 0.0
    return_code: int = ReturnCode.SUCCESS
    task_id: Optional[str] = None
    agent_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/reporting."""
        return {
            "mode": self.mode.value,
            "decision_time_ms": self.decision_time_ms,
            "execution_time_ms": self.execution_time_ms,
            "fallback_reason": self.fallback_reason,
            "context_filtering_time_ms": self.context_filtering_time_ms,
            "message_routing_time_ms": self.message_routing_time_ms,
            "total_time_ms": self.decision_time_ms + self.execution_time_ms,
            "context_size_original": self.context_size_original,
            "context_size_filtered": self.context_size_filtered,
            "token_reduction_percent": self.token_reduction_percent,
            "return_code": self.return_code,
            "task_id": self.task_id,
            "agent_type": self.agent_type
        }