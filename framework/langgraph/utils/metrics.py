"""
Metrics collection and analysis for LangGraph workflows.

Provides comprehensive metrics tracking for workflow execution,
agent performance, and resource utilization.
"""

import time
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path

try:
    from ....core.logging_config import get_logger
except ImportError:
    # Fallback for testing
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""
    workflow_id: str
    workflow_type: str
    start_time: float
    end_time: Optional[float] = None
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    agent_executions: Dict[str, int] = field(default_factory=dict)
    state_transitions: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    human_interventions: int = 0
    memory_operations: Dict[str, int] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate workflow duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens processed per second."""
        duration = self.duration_seconds
        return self.total_tokens / duration if duration > 0 else 0.0
    
    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token."""
        return self.total_cost_usd / self.total_tokens if self.total_tokens > 0 else 0.0
    
    @property
    def agent_utilization(self) -> Dict[str, float]:
        """Calculate relative utilization of each agent."""
        total_executions = sum(self.agent_executions.values())
        if total_executions == 0:
            return {}
        
        return {
            agent: (count / total_executions) * 100
            for agent, count in self.agent_executions.items()
        }
    
    def add_state_transition(self, from_state: str, to_state: str, agent: str) -> None:
        """Record a state transition."""
        self.state_transitions.append({
            "timestamp": time.time(),
            "from_state": from_state,
            "to_state": to_state,
            "agent": agent
        })
    
    def add_error(self, error_type: str, message: str, agent: str) -> None:
        """Record an error."""
        self.errors.append({
            "timestamp": time.time(),
            "error_type": error_type,
            "message": message,
            "agent": agent
        })
    
    def add_agent_execution(self, agent: str, tokens_used: int = 0, cost_usd: float = 0.0) -> None:
        """Record agent execution."""
        if agent not in self.agent_executions:
            self.agent_executions[agent] = 0
        
        self.agent_executions[agent] += 1
        self.total_tokens += tokens_used
        self.total_cost_usd += cost_usd
    
    def add_memory_operation(self, operation_type: str) -> None:
        """Record a memory operation."""
        if operation_type not in self.memory_operations:
            self.memory_operations[operation_type] = 0
        self.memory_operations[operation_type] += 1
    
    def finish(self) -> None:
        """Mark workflow as finished."""
        self.end_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        data = asdict(self)
        data['duration_seconds'] = self.duration_seconds
        data['tokens_per_second'] = self.tokens_per_second
        data['cost_per_token'] = self.cost_per_token
        data['agent_utilization'] = self.agent_utilization
        return data


class MetricsCollector:
    """Collects and manages workflow metrics."""
    
    def __init__(self, export_file: Optional[str] = None):
        """
        Initialize metrics collector.
        
        Args:
            export_file: Optional file path for metrics export
        """
        self.active_workflows: Dict[str, WorkflowMetrics] = {}
        self.completed_workflows: List[WorkflowMetrics] = []
        self.export_file = Path(export_file) if export_file else None
        
        # Ensure export directory exists
        if self.export_file:
            self.export_file.parent.mkdir(parents=True, exist_ok=True)
    
    def start_workflow(
        self,
        workflow_id: str,
        workflow_type: str = "unknown"
    ) -> WorkflowMetrics:
        """
        Start tracking a workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            workflow_type: Type of workflow (task, project, review, etc.)
            
        Returns:
            WorkflowMetrics: Metrics object for the workflow
        """
        metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            start_time=time.time()
        )
        
        self.active_workflows[workflow_id] = metrics
        logger.info(f"Started tracking workflow {workflow_id}")
        return metrics
    
    def get_workflow_metrics(self, workflow_id: str) -> Optional[WorkflowMetrics]:
        """Get metrics for an active workflow."""
        return self.active_workflows.get(workflow_id)
    
    def finish_workflow(self, workflow_id: str) -> Optional[WorkflowMetrics]:
        """
        Finish tracking a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            WorkflowMetrics: Final metrics for the workflow
        """
        metrics = self.active_workflows.pop(workflow_id, None)
        if metrics:
            metrics.finish()
            self.completed_workflows.append(metrics)
            logger.info(f"Finished tracking workflow {workflow_id} "
                       f"(duration: {metrics.duration_seconds:.2f}s)")
            
            # Export if configured
            if self.export_file:
                self._export_metrics()
        
        return metrics
    
    def record_agent_execution(
        self,
        workflow_id: str,
        agent_name: str,
        tokens_used: int = 0,
        cost_usd: float = 0.0
    ) -> None:
        """Record an agent execution in a workflow."""
        metrics = self.active_workflows.get(workflow_id)
        if metrics:
            metrics.add_agent_execution(agent_name, tokens_used, cost_usd)
    
    def record_state_transition(
        self,
        workflow_id: str,
        from_state: str,
        to_state: str,
        agent: str
    ) -> None:
        """Record a state transition in a workflow."""
        metrics = self.active_workflows.get(workflow_id)
        if metrics:
            metrics.add_state_transition(from_state, to_state, agent)
    
    def record_error(
        self,
        workflow_id: str,
        error_type: str,
        message: str,
        agent: str
    ) -> None:
        """Record an error in a workflow."""
        metrics = self.active_workflows.get(workflow_id)
        if metrics:
            metrics.add_error(error_type, message, agent)
    
    def record_human_intervention(self, workflow_id: str) -> None:
        """Record a human intervention in a workflow."""
        metrics = self.active_workflows.get(workflow_id)
        if metrics:
            metrics.human_interventions += 1
    
    def record_memory_operation(self, workflow_id: str, operation_type: str) -> None:
        """Record a memory operation in a workflow."""
        metrics = self.active_workflows.get(workflow_id)
        if metrics:
            metrics.add_memory_operation(operation_type)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics across all workflows."""
        if not self.completed_workflows:
            return {
                "total_workflows": 0,
                "avg_duration": 0.0,
                "avg_tokens": 0.0,
                "avg_cost": 0.0,
                "success_rate": 0.0
            }
        
        total_workflows = len(self.completed_workflows)
        total_duration = sum(w.duration_seconds for w in self.completed_workflows)
        total_tokens = sum(w.total_tokens for w in self.completed_workflows)
        total_cost = sum(w.total_cost_usd for w in self.completed_workflows)
        successful_workflows = sum(1 for w in self.completed_workflows if not w.errors)
        
        return {
            "total_workflows": total_workflows,
            "avg_duration": total_duration / total_workflows,
            "avg_tokens": total_tokens / total_workflows,
            "avg_cost": total_cost / total_workflows,
            "success_rate": (successful_workflows / total_workflows) * 100,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_duration": total_duration
        }
    
    def get_agent_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics by agent."""
        agent_stats = {}
        
        for workflow in self.completed_workflows:
            for agent, executions in workflow.agent_executions.items():
                if agent not in agent_stats:
                    agent_stats[agent] = {
                        "total_executions": 0,
                        "total_tokens": 0,
                        "total_cost": 0.0,
                        "total_duration": 0.0,
                        "workflows": 0
                    }
                
                agent_stats[agent]["total_executions"] += executions
                agent_stats[agent]["total_duration"] += workflow.duration_seconds
                agent_stats[agent]["workflows"] += 1
        
        # Calculate averages
        for agent, stats in agent_stats.items():
            workflows = stats["workflows"]
            if workflows > 0:
                stats["avg_executions_per_workflow"] = stats["total_executions"] / workflows
                stats["avg_duration_per_workflow"] = stats["total_duration"] / workflows
        
        return agent_stats
    
    def _export_metrics(self) -> None:
        """Export metrics to configured file."""
        try:
            export_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": self.get_summary_stats(),
                "agent_performance": self.get_agent_performance(),
                "completed_workflows": [w.to_dict() for w in self.completed_workflows],
                "active_workflows": [w.to_dict() for w in self.active_workflows.values()]
            }
            
            with open(self.export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported metrics to {self.export_file}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def export_to_file(self, file_path: str) -> None:
        """Export metrics to a specific file."""
        original_export_file = self.export_file
        self.export_file = Path(file_path)
        self.export_file.parent.mkdir(parents=True, exist_ok=True)
        self._export_metrics()
        self.export_file = original_export_file


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(export_file: Optional[str] = None) -> MetricsCollector:
    """
    Get or create the global metrics collector.
    
    Args:
        export_file: Optional file path for metrics export
        
    Returns:
        MetricsCollector: Global metrics collector instance
    """
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(export_file)
    
    return _metrics_collector