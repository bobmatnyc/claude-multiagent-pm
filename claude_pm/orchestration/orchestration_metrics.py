"""
Orchestration Metrics Management
===============================

This module handles metrics collection, tracking, and analysis for orchestration
operations.
"""

from typing import List, Dict, Any
from .orchestration_types import OrchestrationMetrics, OrchestrationMode, ReturnCode


class MetricsManager:
    """Manages orchestration metrics collection and analysis."""
    
    def __init__(self):
        self._orchestration_metrics: List[OrchestrationMetrics] = []
    
    def add_metrics(self, metrics: OrchestrationMetrics) -> None:
        """Add a new metrics entry."""
        self._orchestration_metrics.append(metrics)
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics."""
        if not self._orchestration_metrics:
            return {
                "total_orchestrations": 0,
                "metrics": [],
                "success_rate": 0.0,
                "average_token_reduction": 0.0
            }
        
        # Calculate statistics
        total = len(self._orchestration_metrics)
        local_count = sum(1 for m in self._orchestration_metrics if m.mode == OrchestrationMode.LOCAL)
        subprocess_count = sum(1 for m in self._orchestration_metrics if m.mode == OrchestrationMode.SUBPROCESS)
        
        # Success/failure statistics
        success_count = sum(1 for m in self._orchestration_metrics if m.return_code == ReturnCode.SUCCESS)
        failure_by_code = {}
        for m in self._orchestration_metrics:
            if m.return_code != ReturnCode.SUCCESS:
                code_name = self._get_return_code_name(m.return_code)
                failure_by_code[code_name] = failure_by_code.get(code_name, 0) + 1
        
        # Timing statistics
        avg_decision_time = sum(m.decision_time_ms for m in self._orchestration_metrics) / total
        avg_execution_time = sum(m.execution_time_ms for m in self._orchestration_metrics) / total
        
        # Token reduction statistics (only for local orchestrations with data)
        token_reductions = [
            m.token_reduction_percent 
            for m in self._orchestration_metrics 
            if m.mode == OrchestrationMode.LOCAL and m.context_size_original > 0
        ]
        avg_token_reduction = sum(token_reductions) / len(token_reductions) if token_reductions else 0.0
        
        # Context filtering timing (only for local orchestrations)
        context_filter_times = [
            m.context_filtering_time_ms 
            for m in self._orchestration_metrics 
            if m.mode == OrchestrationMode.LOCAL and m.context_filtering_time_ms > 0
        ]
        avg_context_filter_time = sum(context_filter_times) / len(context_filter_times) if context_filter_times else 0.0
        
        # Agent type distribution
        agent_type_counts = {}
        for m in self._orchestration_metrics:
            if m.agent_type:
                agent_type_counts[m.agent_type] = agent_type_counts.get(m.agent_type, 0) + 1
        
        return {
            "total_orchestrations": total,
            "local_orchestrations": local_count,
            "subprocess_orchestrations": subprocess_count,
            "success_count": success_count,
            "success_rate": (success_count / total * 100) if total > 0 else 0.0,
            "failure_by_code": failure_by_code,
            "average_decision_time_ms": avg_decision_time,
            "average_execution_time_ms": avg_execution_time,
            "average_context_filter_time_ms": avg_context_filter_time,
            "average_token_reduction_percent": avg_token_reduction,
            "agent_type_distribution": agent_type_counts,
            "recent_metrics": [m.to_dict() for m in self._orchestration_metrics[-10:]],
            "fallback_reasons": list(set(
                m.fallback_reason for m in self._orchestration_metrics 
                if m.fallback_reason
            ))
        }
    
    def _get_return_code_name(self, code: int) -> str:
        """Get human-readable name for return code."""
        code_names = {
            ReturnCode.SUCCESS: "SUCCESS",
            ReturnCode.GENERAL_FAILURE: "GENERAL_FAILURE",
            ReturnCode.TIMEOUT: "TIMEOUT",
            ReturnCode.CONTEXT_FILTERING_ERROR: "CONTEXT_FILTERING_ERROR",
            ReturnCode.AGENT_NOT_FOUND: "AGENT_NOT_FOUND",
            ReturnCode.MESSAGE_BUS_ERROR: "MESSAGE_BUS_ERROR"
        }
        return code_names.get(code, f"UNKNOWN_{code}")