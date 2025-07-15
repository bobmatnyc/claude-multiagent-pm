"""
Evaluation Metrics System
========================

This module provides comprehensive evaluation metrics for the Claude PM Framework,
including performance tracking, analytics, and improvement recommendations.

Key Features:
- Real-time performance metrics
- Agent-specific performance analysis
- Trend analysis and improvement tracking
- Performance benchmarking
- Automated recommendations
- Export capabilities for reporting

Metrics Categories:
- Response Quality: Correctness, relevance, completeness
- Performance: Speed, efficiency, resource usage
- User Satisfaction: User corrections, feedback analysis
- System Health: Error rates, availability, reliability
- Improvement: Learning trends, optimization opportunities
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Deque
from enum import Enum
import statistics
import uuid

from claude_pm.core.config import Config
from claude_pm.services.mirascope_evaluator import EvaluationResult, EvaluationCriteria
from claude_pm.services.correction_capture import CorrectionData, CorrectionType

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""
    RESPONSE_QUALITY = "response_quality"
    PERFORMANCE = "performance"
    USER_SATISFACTION = "user_satisfaction"
    SYSTEM_HEALTH = "system_health"
    IMPROVEMENT = "improvement"


class TrendDirection(Enum):
    """Trend direction indicators."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    UNKNOWN = "unknown"


@dataclass
class MetricPoint:
    """Individual metric data point."""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "metadata": self.metadata
        }


@dataclass
class MetricSeries:
    """Time series of metric points."""
    metric_name: str
    metric_type: MetricType
    agent_type: Optional[str] = None
    points: List[MetricPoint] = field(default_factory=list)
    max_points: int = 1000
    
    def add_point(self, value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a new metric point."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            metadata=metadata or {}
        )
        
        self.points.append(point)
        
        # Maintain max points limit
        if len(self.points) > self.max_points:
            self.points.pop(0)
    
    def get_recent_points(self, hours: int = 24) -> List[MetricPoint]:
        """Get points from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [p for p in self.points if p.timestamp >= cutoff]
    
    def get_trend(self, hours: int = 24) -> TrendDirection:
        """Calculate trend direction."""
        recent_points = self.get_recent_points(hours)
        
        if len(recent_points) < 5:
            return TrendDirection.UNKNOWN
        
        # Split into two halves and compare averages
        midpoint = len(recent_points) // 2
        first_half = recent_points[:midpoint]
        second_half = recent_points[midpoint:]
        
        first_avg = statistics.mean(p.value for p in first_half)
        second_avg = statistics.mean(p.value for p in second_half)
        
        # Calculate threshold as 5% of the average value
        avg_value = statistics.mean(p.value for p in recent_points)
        threshold = max(0.05 * avg_value, 1.0)  # At least 1.0 difference
        
        if second_avg - first_avg > threshold:
            return TrendDirection.IMPROVING
        elif first_avg - second_avg > threshold:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get statistical summary."""
        recent_points = self.get_recent_points(hours)
        
        if not recent_points:
            return {
                "count": 0,
                "mean": 0,
                "median": 0,
                "std_dev": 0,
                "min": 0,
                "max": 0,
                "trend": TrendDirection.UNKNOWN.value
            }
        
        values = [p.value for p in recent_points]
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "trend": self.get_trend(hours).value
        }


@dataclass
class PerformanceBenchmark:
    """Performance benchmark data."""
    agent_type: str
    metric_name: str
    target_value: float
    threshold_warning: float
    threshold_critical: float
    description: str
    
    def evaluate(self, current_value: float) -> str:
        """Evaluate current value against benchmarks."""
        if current_value >= self.target_value:
            return "excellent"
        elif current_value >= self.threshold_warning:
            return "good"
        elif current_value >= self.threshold_critical:
            return "warning"
        else:
            return "critical"


@dataclass
class ImprovementRecommendation:
    """Improvement recommendation."""
    agent_type: str
    metric_name: str
    current_value: float
    target_value: float
    recommendation: str
    priority: str  # high, medium, low
    estimated_impact: str
    implementation_effort: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class EvaluationMetricsSystem:
    """
    Comprehensive evaluation metrics system.
    
    Tracks performance, quality, and improvement metrics across all agents
    and provides analytics and recommendations.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize metrics system.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.enabled = self.config.get("enable_evaluation_metrics", True)
        
        # Metric storage
        self.metrics: Dict[str, MetricSeries] = {}
        self.agent_metrics: Dict[str, Dict[str, MetricSeries]] = defaultdict(dict)
        
        # Performance benchmarks
        self.benchmarks = self._initialize_benchmarks()
        
        # Recent data caches for performance
        self.recent_evaluations: Deque[EvaluationResult] = deque(maxlen=1000)
        self.recent_corrections: Deque[CorrectionData] = deque(maxlen=1000)
        
        # Storage
        self.storage_path = Path(self.config.get("evaluation_storage_path", "~/.claude-pm/training")).expanduser()
        self.metrics_dir = self.storage_path / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.start_time = datetime.now()
        self.total_evaluations_processed = 0
        self.total_corrections_processed = 0
        
        if self.enabled:
            logger.info("Evaluation metrics system initialized")
        else:
            logger.info("Evaluation metrics system disabled")
    
    def _initialize_benchmarks(self) -> Dict[str, PerformanceBenchmark]:
        """Initialize performance benchmarks."""
        benchmarks = {}
        
        # General response quality benchmarks
        benchmarks["overall_score"] = PerformanceBenchmark(
            agent_type="*",
            metric_name="overall_score",
            target_value=85.0,
            threshold_warning=70.0,
            threshold_critical=50.0,
            description="Overall response quality score"
        )
        
        # Response time benchmarks
        benchmarks["response_time"] = PerformanceBenchmark(
            agent_type="*",
            metric_name="response_time",
            target_value=100.0,  # 100ms target
            threshold_warning=200.0,
            threshold_critical=500.0,
            description="Response evaluation time in milliseconds"
        )
        
        # Agent-specific benchmarks
        agent_benchmarks = {
            "engineer": {"overall_score": 80.0, "response_time": 150.0},
            "researcher": {"overall_score": 85.0, "response_time": 200.0},
            "ops": {"overall_score": 90.0, "response_time": 100.0},
            "qa": {"overall_score": 95.0, "response_time": 100.0},
            "documentation": {"overall_score": 88.0, "response_time": 150.0}
        }
        
        for agent_type, agent_values in agent_benchmarks.items():
            for metric_name, target_value in agent_values.items():
                key = f"{agent_type}_{metric_name}"
                benchmarks[key] = PerformanceBenchmark(
                    agent_type=agent_type,
                    metric_name=metric_name,
                    target_value=target_value,
                    threshold_warning=target_value * 0.8,
                    threshold_critical=target_value * 0.6,
                    description=f"{agent_type} {metric_name} benchmark"
                )
        
        return benchmarks
    
    def record_evaluation(self, evaluation_result: EvaluationResult) -> None:
        """Record an evaluation result for metrics tracking."""
        if not self.enabled:
            return
        
        try:
            # Add to recent cache
            self.recent_evaluations.append(evaluation_result)
            self.total_evaluations_processed += 1
            
            agent_type = evaluation_result.agent_type
            
            # Record overall score
            self._record_metric(
                "overall_score",
                MetricType.RESPONSE_QUALITY,
                evaluation_result.overall_score,
                agent_type,
                {"evaluation_id": evaluation_result.evaluation_id}
            )
            
            # Record response time
            self._record_metric(
                "response_time",
                MetricType.PERFORMANCE,
                evaluation_result.evaluation_time_ms,
                agent_type,
                {"evaluation_id": evaluation_result.evaluation_id}
            )
            
            # Record criterion scores
            for criterion_score in evaluation_result.criterion_scores:
                metric_name = f"{criterion_score.criterion.value}_score"
                self._record_metric(
                    metric_name,
                    MetricType.RESPONSE_QUALITY,
                    criterion_score.score,
                    agent_type,
                    {
                        "evaluation_id": evaluation_result.evaluation_id,
                        "confidence": criterion_score.confidence
                    }
                )
            
            # Record system health metrics
            self._record_metric(
                "evaluations_per_hour",
                MetricType.SYSTEM_HEALTH,
                self._calculate_evaluations_per_hour(),
                None,
                {"timestamp": datetime.now().isoformat()}
            )
            
            logger.debug(f"Recorded evaluation metrics for {agent_type}")
            
        except Exception as e:
            logger.error(f"Failed to record evaluation metrics: {e}")
    
    def record_correction(self, correction_data: CorrectionData) -> None:
        """Record a correction for metrics tracking."""
        if not self.enabled:
            return
        
        try:
            # Add to recent cache
            self.recent_corrections.append(correction_data)
            self.total_corrections_processed += 1
            
            agent_type = correction_data.agent_type
            
            # Record correction rate
            self._record_metric(
                "correction_rate",
                MetricType.USER_SATISFACTION,
                self._calculate_correction_rate(agent_type),
                agent_type,
                {"correction_id": correction_data.correction_id}
            )
            
            # Record correction severity
            severity_score = self._severity_to_score(correction_data.severity)
            self._record_metric(
                "correction_severity",
                MetricType.USER_SATISFACTION,
                severity_score,
                agent_type,
                {
                    "correction_id": correction_data.correction_id,
                    "severity": correction_data.severity
                }
            )
            
            # Record correction type distribution
            self._record_metric(
                f"correction_type_{correction_data.correction_type.value}",
                MetricType.USER_SATISFACTION,
                1.0,
                agent_type,
                {"correction_id": correction_data.correction_id}
            )
            
            logger.debug(f"Recorded correction metrics for {agent_type}")
            
        except Exception as e:
            logger.error(f"Failed to record correction metrics: {e}")
    
    def _record_metric(
        self,
        metric_name: str,
        metric_type: MetricType,
        value: float,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric point."""
        # Global metric
        global_key = f"global_{metric_name}"
        if global_key not in self.metrics:
            self.metrics[global_key] = MetricSeries(
                metric_name=metric_name,
                metric_type=metric_type
            )
        
        self.metrics[global_key].add_point(value, metadata)
        
        # Agent-specific metric
        if agent_type:
            agent_key = f"{agent_type}_{metric_name}"
            if agent_key not in self.agent_metrics[agent_type]:
                self.agent_metrics[agent_type][agent_key] = MetricSeries(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    agent_type=agent_type
                )
            
            self.agent_metrics[agent_type][agent_key].add_point(value, metadata)
    
    def _calculate_evaluations_per_hour(self) -> float:
        """Calculate evaluations per hour."""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        recent_count = sum(
            1 for eval_result in self.recent_evaluations
            if datetime.fromisoformat(eval_result.timestamp) >= one_hour_ago
        )
        
        return float(recent_count)
    
    def _calculate_correction_rate(self, agent_type: str) -> float:
        """Calculate correction rate for an agent."""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Count recent corrections for this agent
        recent_corrections = sum(
            1 for correction in self.recent_corrections
            if correction.agent_type == agent_type and
            datetime.fromisoformat(correction.timestamp) >= one_hour_ago
        )
        
        # Count recent evaluations for this agent
        recent_evaluations = sum(
            1 for evaluation in self.recent_evaluations
            if evaluation.agent_type == agent_type and
            datetime.fromisoformat(evaluation.timestamp) >= one_hour_ago
        )
        
        if recent_evaluations == 0:
            return 0.0
        
        return (recent_corrections / recent_evaluations) * 100.0
    
    def _severity_to_score(self, severity: str) -> float:
        """Convert severity to numeric score."""
        severity_map = {
            "low": 25.0,
            "medium": 50.0,
            "high": 75.0,
            "critical": 100.0
        }
        
        return severity_map.get(severity.lower(), 50.0)
    
    def get_agent_metrics(self, agent_type: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics for a specific agent."""
        if agent_type not in self.agent_metrics:
            return {
                "agent_type": agent_type,
                "metrics": {},
                "summary": "No metrics available"
            }
        
        agent_data = self.agent_metrics[agent_type]
        metrics_summary = {}
        
        for metric_key, metric_series in agent_data.items():
            metrics_summary[metric_key] = metric_series.get_statistics(hours)
        
        return {
            "agent_type": agent_type,
            "metrics": metrics_summary,
            "summary": self._generate_agent_summary(agent_type, metrics_summary)
        }
    
    def _generate_agent_summary(self, agent_type: str, metrics: Dict[str, Any]) -> str:
        """Generate summary for agent metrics."""
        if not metrics:
            return "No performance data available"
        
        # Get overall score if available
        overall_score_key = f"{agent_type}_overall_score"
        if overall_score_key in metrics:
            overall_data = metrics[overall_score_key]
            score = overall_data.get("mean", 0)
            trend = overall_data.get("trend", "unknown")
            
            if score >= 85:
                performance = "excellent"
            elif score >= 75:
                performance = "good"
            elif score >= 65:
                performance = "fair"
            else:
                performance = "needs improvement"
            
            return f"Performance: {performance} (avg: {score:.1f}, trend: {trend})"
        
        return "Performance data available"
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics."""
        now = datetime.now()
        uptime = now - self.start_time
        
        # Calculate rates
        evaluations_per_hour = self._calculate_evaluations_per_hour()
        corrections_per_hour = sum(
            1 for correction in self.recent_corrections
            if datetime.fromisoformat(correction.timestamp) >= now - timedelta(hours=1)
        )
        
        # Error rate (simplified - could track actual errors)
        error_rate = 0.0  # Placeholder
        
        health_score = 100.0
        if evaluations_per_hour < 1:
            health_score -= 20
        if corrections_per_hour > evaluations_per_hour * 0.3:  # High correction rate
            health_score -= 30
        if error_rate > 0.05:  # High error rate
            health_score -= 40
        
        return {
            "health_score": max(0, health_score),
            "uptime_seconds": uptime.total_seconds(),
            "evaluations_per_hour": evaluations_per_hour,
            "corrections_per_hour": corrections_per_hour,
            "error_rate": error_rate,
            "total_evaluations": self.total_evaluations_processed,
            "total_corrections": self.total_corrections_processed,
            "active_agents": len(self.agent_metrics),
            "metrics_enabled": self.enabled
        }
    
    def get_performance_benchmarks(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance benchmarks comparison."""
        results = {}
        
        # Get current metrics
        if agent_type:
            agent_metrics = self.get_agent_metrics(agent_type)
            metrics_to_check = {f"{agent_type}_{k}": v for k, v in agent_metrics["metrics"].items()}
        else:
            metrics_to_check = {k: v.get_statistics() for k, v in self.metrics.items()}
        
        # Compare against benchmarks
        for metric_key, metric_data in metrics_to_check.items():
            # Find matching benchmark
            benchmark = None
            if metric_key in self.benchmarks:
                benchmark = self.benchmarks[metric_key]
            else:
                # Try general benchmark
                metric_name = metric_key.split("_", 1)[-1]
                if metric_name in self.benchmarks:
                    benchmark = self.benchmarks[metric_name]
            
            if benchmark:
                current_value = metric_data.get("mean", 0)
                status = benchmark.evaluate(current_value)
                
                results[metric_key] = {
                    "current_value": current_value,
                    "target_value": benchmark.target_value,
                    "status": status,
                    "benchmark": benchmark.description,
                    "trend": metric_data.get("trend", "unknown")
                }
        
        return results
    
    def generate_improvement_recommendations(self, agent_type: Optional[str] = None) -> List[ImprovementRecommendation]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Get benchmark comparison
        benchmark_results = self.get_performance_benchmarks(agent_type)
        
        for metric_key, result in benchmark_results.items():
            current_value = result["current_value"]
            target_value = result["target_value"]
            status = result["status"]
            trend = result["trend"]
            
            # Generate recommendation if performance is below target
            if status in ["warning", "critical"] or trend == "declining":
                recommendation = self._generate_recommendation(
                    metric_key, current_value, target_value, status, trend
                )
                
                if recommendation:
                    recommendations.append(recommendation)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return recommendations
    
    def _generate_recommendation(
        self,
        metric_key: str,
        current_value: float,
        target_value: float,
        status: str,
        trend: str
    ) -> Optional[ImprovementRecommendation]:
        """Generate specific improvement recommendation."""
        # Parse metric key
        parts = metric_key.split("_", 1)
        if len(parts) == 2:
            agent_type, metric_name = parts
        else:
            agent_type = "system"
            metric_name = metric_key
        
        # Generate recommendation based on metric type
        if metric_name == "overall_score":
            return ImprovementRecommendation(
                agent_type=agent_type,
                metric_name=metric_name,
                current_value=current_value,
                target_value=target_value,
                recommendation=f"Improve response quality through better prompt engineering and training. Current score: {current_value:.1f}, target: {target_value:.1f}",
                priority="high" if status == "critical" else "medium",
                estimated_impact="High - directly improves user satisfaction",
                implementation_effort="Medium - requires prompt optimization and training data review"
            )
        
        elif metric_name == "response_time":
            return ImprovementRecommendation(
                agent_type=agent_type,
                metric_name=metric_name,
                current_value=current_value,
                target_value=target_value,
                recommendation=f"Optimize response time through caching and model optimization. Current: {current_value:.1f}ms, target: {target_value:.1f}ms",
                priority="medium" if status == "warning" else "high",
                estimated_impact="Medium - improves user experience",
                implementation_effort="Low - enable caching and optimize model calls"
            )
        
        elif metric_name == "correction_rate":
            return ImprovementRecommendation(
                agent_type=agent_type,
                metric_name=metric_name,
                current_value=current_value,
                target_value=target_value,
                recommendation=f"Reduce correction rate by improving initial response quality. Current: {current_value:.1f}%, target: <10%",
                priority="high",
                estimated_impact="High - reduces user frustration and improves efficiency",
                implementation_effort="High - requires comprehensive response quality improvement"
            )
        
        return None
    
    def export_metrics(self, agent_type: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Export metrics data."""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "hours_included": hours,
            "system_health": self.get_system_health(),
            "metrics": {}
        }
        
        if agent_type:
            export_data["metrics"][agent_type] = self.get_agent_metrics(agent_type, hours)
        else:
            # Export all agents
            for agent in self.agent_metrics.keys():
                export_data["metrics"][agent] = self.get_agent_metrics(agent, hours)
        
        # Add benchmarks
        export_data["benchmarks"] = self.get_performance_benchmarks(agent_type)
        
        # Add recommendations
        export_data["recommendations"] = [
            rec.to_dict() for rec in self.generate_improvement_recommendations(agent_type)
        ]
        
        return export_data
    
    def save_metrics_report(self, agent_type: Optional[str] = None) -> str:
        """Save comprehensive metrics report."""
        try:
            export_data = self.export_metrics(agent_type)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_report_{agent_type or 'all'}_{timestamp}.json"
            
            report_file = self.metrics_dir / filename
            with open(report_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Saved metrics report: {report_file}")
            
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Failed to save metrics report: {e}")
            raise
    
    def cleanup_old_metrics(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old metrics data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean up metric series
            cleaned_metrics = 0
            for metric_series in self.metrics.values():
                original_count = len(metric_series.points)
                metric_series.points = [
                    p for p in metric_series.points
                    if p.timestamp >= cutoff_date
                ]
                cleaned_metrics += original_count - len(metric_series.points)
            
            # Clean up agent metrics
            for agent_metrics in self.agent_metrics.values():
                for metric_series in agent_metrics.values():
                    original_count = len(metric_series.points)
                    metric_series.points = [
                        p for p in metric_series.points
                        if p.timestamp >= cutoff_date
                    ]
                    cleaned_metrics += original_count - len(metric_series.points)
            
            # Clean up report files
            removed_files = []
            if self.metrics_dir.exists():
                for report_file in self.metrics_dir.glob("metrics_report_*.json"):
                    try:
                        file_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            report_file.unlink()
                            removed_files.append(str(report_file))
                    except Exception as e:
                        logger.error(f"Failed to process {report_file}: {e}")
            
            logger.info(f"Cleaned up {cleaned_metrics} metric points and {len(removed_files)} report files")
            
            return {
                "cleaned_metric_points": cleaned_metrics,
                "removed_report_files": len(removed_files),
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup metrics: {e}")
            return {"error": str(e)}


# Global metrics instance
_metrics_system: Optional[EvaluationMetricsSystem] = None


def get_metrics_system(config: Optional[Config] = None) -> EvaluationMetricsSystem:
    """Get global metrics system instance."""
    global _metrics_system
    
    if _metrics_system is None:
        _metrics_system = EvaluationMetricsSystem(config)
    
    return _metrics_system


def initialize_metrics_system(config: Optional[Config] = None) -> Dict[str, Any]:
    """Initialize the evaluation metrics system."""
    try:
        system = get_metrics_system(config)
        health = system.get_system_health()
        
        return {
            "initialized": True,
            "enabled": system.enabled,
            "system_health": health,
            "storage_path": str(system.storage_path)
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize metrics system: {e}")
        return {"initialized": False, "error": str(e)}


# Helper functions
def record_evaluation_metrics(evaluation_result: EvaluationResult) -> None:
    """Record evaluation metrics."""
    system = get_metrics_system()
    system.record_evaluation(evaluation_result)


def record_correction_metrics(correction_data: CorrectionData) -> None:
    """Record correction metrics."""
    system = get_metrics_system()
    system.record_correction(correction_data)


def get_agent_performance_summary(agent_type: str) -> Dict[str, Any]:
    """Get performance summary for an agent."""
    system = get_metrics_system()
    return system.get_agent_metrics(agent_type)


def generate_performance_report(agent_type: Optional[str] = None) -> str:
    """Generate and save performance report."""
    system = get_metrics_system()
    return system.save_metrics_report(agent_type)


if __name__ == "__main__":
    # Test the metrics system
    print("Testing Evaluation Metrics System")
    print("=" * 50)
    
    # Initialize system
    init_result = initialize_metrics_system()
    print(f"Initialization: {init_result['initialized']}")
    print(f"System enabled: {init_result['enabled']}")
    
    if init_result['initialized']:
        system = get_metrics_system()
        
        # Test metric recording
        from claude_pm.services.mirascope_evaluator import EvaluationResult, EvaluationScore, EvaluationProvider, EvaluationCriteria
        
        # Create mock evaluation result
        mock_result = EvaluationResult(
            evaluation_id="test_eval_123",
            agent_type="engineer",
            response_text="def hello(): print('Hello, World!')",
            context={"task": "create hello function"},
            overall_score=85.5,
            criterion_scores=[
                EvaluationScore(
                    criterion=EvaluationCriteria.CORRECTNESS,
                    score=90.0,
                    explanation="Code is correct",
                    confidence=0.9
                ),
                EvaluationScore(
                    criterion=EvaluationCriteria.CLARITY,
                    score=80.0,
                    explanation="Code is clear",
                    confidence=0.8
                )
            ],
            evaluation_time_ms=150.0,
            provider=EvaluationProvider.OPENAI
        )
        
        # Record metrics
        record_evaluation_metrics(mock_result)
        
        # Get agent metrics
        agent_metrics = get_agent_performance_summary("engineer")
        print(f"Engineer metrics: {agent_metrics['summary']}")
        
        # Get system health
        health = system.get_system_health()
        print(f"System health score: {health['health_score']}")
        
        # Get recommendations
        recommendations = system.generate_improvement_recommendations("engineer")
        print(f"Recommendations: {len(recommendations)}")
        
        # Generate report
        report_path = generate_performance_report("engineer")
        print(f"Generated report: {report_path}")
        
    else:
        print(f"Initialization failed: {init_result.get('error', 'Unknown error')}")