"""
Orchestrator Type Definitions
============================

This module contains type definitions and data structures used by the
backwards compatible orchestrator.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional


class OrchestrationMode(Enum):
    """Modes of orchestration execution."""
    LOCAL = "local"
    SUBPROCESS = "subprocess"
    FORCED_LOCAL = "forced_local"
    FORCED_SUBPROCESS = "forced_subprocess"


class ReturnCode:
    """Standard return codes matching subprocess behavior."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENTS = 2
    AGENT_NOT_FOUND = 3
    EXECUTION_ERROR = 4
    TIMEOUT = 5
    PERMISSION_DENIED = 126
    COMMAND_NOT_FOUND = 127


@dataclass
class OrchestrationMetrics:
    """Metrics for orchestration performance tracking."""
    
    # Mode selection metrics
    mode_determinations: int = 0
    local_mode_selections: int = 0
    subprocess_mode_selections: int = 0
    
    # Execution metrics
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0
    
    # Performance metrics by mode
    local_execution_times: List[float] = field(default_factory=list)
    subprocess_execution_times: List[float] = field(default_factory=list)
    
    # Fallback metrics
    emergency_fallbacks: int = 0
    fallback_reasons: List[str] = field(default_factory=list)
    
    # Agent-specific metrics
    agent_execution_counts: Dict[str, int] = field(default_factory=dict)
    agent_success_rates: Dict[str, float] = field(default_factory=dict)
    
    # Start time for session metrics
    session_start: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/reporting."""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "session_duration_seconds": session_duration,
            "mode_selection": {
                "total_determinations": self.mode_determinations,
                "local_selections": self.local_mode_selections,
                "subprocess_selections": self.subprocess_mode_selections,
                "local_percentage": (self.local_mode_selections / max(self.mode_determinations, 1)) * 100
            },
            "execution": {
                "total_executions": self.successful_executions + self.failed_executions,
                "successful": self.successful_executions,
                "failed": self.failed_executions,
                "success_rate": (self.successful_executions / max(self.successful_executions + self.failed_executions, 1)) * 100,
                "total_time": self.total_execution_time,
                "average_time": self.total_execution_time / max(self.successful_executions + self.failed_executions, 1)
            },
            "performance_by_mode": {
                "local": {
                    "count": len(self.local_execution_times),
                    "average_time": sum(self.local_execution_times) / max(len(self.local_execution_times), 1),
                    "total_time": sum(self.local_execution_times)
                },
                "subprocess": {
                    "count": len(self.subprocess_execution_times),
                    "average_time": sum(self.subprocess_execution_times) / max(len(self.subprocess_execution_times), 1),
                    "total_time": sum(self.subprocess_execution_times)
                }
            },
            "fallbacks": {
                "count": self.emergency_fallbacks,
                "reasons": self.fallback_reasons
            },
            "agent_metrics": {
                "execution_counts": self.agent_execution_counts,
                "success_rates": self.agent_success_rates
            }
        }