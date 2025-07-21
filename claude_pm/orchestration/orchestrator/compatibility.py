"""
Compatibility Module
===================

Handles backward compatibility validation and utilities for the orchestrator.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .types import OrchestrationMode, ReturnCode

logger = logging.getLogger(__name__)


class CompatibilityValidator:
    """Handles compatibility validation and return code management."""
    
    def __init__(self):
        self._return_code_names = {
            ReturnCode.SUCCESS: "SUCCESS",
            ReturnCode.GENERAL_ERROR: "GENERAL_ERROR",
            ReturnCode.INVALID_ARGUMENTS: "INVALID_ARGUMENTS",
            ReturnCode.AGENT_NOT_FOUND: "AGENT_NOT_FOUND",
            ReturnCode.EXECUTION_ERROR: "EXECUTION_ERROR",
            ReturnCode.TIMEOUT: "TIMEOUT",
            ReturnCode.PERMISSION_DENIED: "PERMISSION_DENIED",
            ReturnCode.COMMAND_NOT_FOUND: "COMMAND_NOT_FOUND"
        }
        
    async def validate_compatibility(self, orchestrator) -> Dict[str, Any]:
        """Validate backwards compatibility with existing systems."""
        validation_results = {
            "compatible": True,
            "checks": {}
        }
        
        try:
            # Check API compatibility
            test_result, test_return_code = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Compatibility validation test"
            )
            validation_results["checks"]["return_code_support"] = test_return_code is not None
            
            # Check required fields in response
            required_fields = ["success", "subprocess_id", "subprocess_info", "prompt"]
            for field in required_fields:
                if field not in test_result:
                    validation_results["compatible"] = False
                    validation_results["checks"][f"field_{field}"] = False
                else:
                    validation_results["checks"][f"field_{field}"] = True
            
            # Check orchestration detector
            validation_results["checks"]["detector_available"] = orchestrator.detector is not None
            validation_results["checks"]["orchestration_enabled"] = orchestrator.detector.is_orchestration_enabled()
            
            # Check component availability
            validation_results["checks"]["message_bus_available"] = orchestrator._message_bus is not None
            validation_results["checks"]["context_manager_available"] = orchestrator._context_manager is not None
            
            # Check metrics
            metrics = self.get_orchestration_metrics(orchestrator._orchestration_metrics)
            validation_results["checks"]["metrics_tracking"] = metrics["total_orchestrations"] > 0
            
        except Exception as e:
            validation_results["compatible"] = False
            validation_results["error"] = str(e)
        
        return validation_results
    
    def get_return_code_name(self, code: int) -> str:
        """Get human-readable name for return code."""
        return self._return_code_names.get(code, f"UNKNOWN_{code}")
    
    def get_orchestration_metrics(self, orchestration_metrics: List) -> Dict[str, Any]:
        """Get orchestration performance metrics."""
        if not orchestration_metrics:
            return {
                "total_orchestrations": 0,
                "metrics": [],
                "success_rate": 0.0,
                "average_token_reduction": 0.0
            }
        
        # Calculate statistics
        total = len(orchestration_metrics)
        local_count = sum(1 for m in orchestration_metrics if m.mode == OrchestrationMode.LOCAL)
        subprocess_count = sum(1 for m in orchestration_metrics if m.mode == OrchestrationMode.SUBPROCESS)
        
        # Success/failure statistics
        success_count = sum(1 for m in orchestration_metrics if m.return_code == ReturnCode.SUCCESS)
        failure_by_code = {}
        for m in orchestration_metrics:
            if m.return_code != ReturnCode.SUCCESS:
                code_name = self.get_return_code_name(m.return_code)
                failure_by_code[code_name] = failure_by_code.get(code_name, 0) + 1
        
        # Timing statistics
        avg_decision_time = sum(m.decision_time_ms for m in orchestration_metrics) / total
        avg_execution_time = sum(m.execution_time_ms for m in orchestration_metrics) / total
        
        # Token reduction statistics (only for local orchestrations with data)
        token_reductions = [
            m.token_reduction_percent 
            for m in orchestration_metrics 
            if m.mode == OrchestrationMode.LOCAL and m.context_size_original > 0
        ]
        avg_token_reduction = sum(token_reductions) / len(token_reductions) if token_reductions else 0.0
        
        # Context filtering timing (only for local orchestrations)
        context_filter_times = [
            m.context_filtering_time_ms 
            for m in orchestration_metrics 
            if m.mode == OrchestrationMode.LOCAL and m.context_filtering_time_ms > 0
        ]
        avg_context_filter_time = sum(context_filter_times) / len(context_filter_times) if context_filter_times else 0.0
        
        # Agent type distribution
        agent_type_counts = {}
        for m in orchestration_metrics:
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
            "recent_metrics": [m.to_dict() for m in orchestration_metrics[-10:]],
            "fallback_reasons": list(set(
                m.fallback_reason for m in orchestration_metrics 
                if m.fallback_reason
            ))
        }