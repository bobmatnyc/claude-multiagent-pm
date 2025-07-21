"""
Agent Training Dashboard Module
==============================

This module provides dashboard functionality for visualizing training performance,
generating reports, and exporting training data.

Classes:
    TrainingDashboard: Main class for dashboard and reporting functionality
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

from .types import (
    TrainingSession, LearningAdaptation, PerformancePrediction,
    TrainingTemplate
)

logger = logging.getLogger(__name__)


class TrainingDashboard:
    """Provides dashboard and reporting functionality for agent training."""
    
    def __init__(self):
        """Initialize the dashboard system."""
        self.logger = logger
    
    def get_agent_training_dashboard(self,
                                   agent_type: str,
                                   training_sessions: List[TrainingSession],
                                   adaptations: List[LearningAdaptation],
                                   performance_predictions: List[PerformancePrediction],
                                   trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive dashboard for specific agent training."""
        agent_sessions = [s for s in training_sessions if s.agent_type == agent_type]
        agent_adaptations = [a for a in adaptations if a.agent_type == agent_type]
        agent_predictions = [p for p in performance_predictions if p.agent_type == agent_type]
        
        dashboard = {
            'agent_type': agent_type,
            'overview': self._get_agent_overview(agent_sessions),
            'performance_trends': self._get_performance_trends(agent_type, agent_sessions, trend_data),
            'adaptations': self._get_adaptation_summary(agent_adaptations),
            'predictions': self._get_prediction_summary(agent_predictions),
            'recommendations': self._get_agent_recommendations(agent_type, agent_sessions)
        }
        
        return dashboard
    
    def _get_agent_overview(self, agent_sessions: List[TrainingSession]) -> Dict[str, Any]:
        """Get overview statistics for an agent."""
        if not agent_sessions:
            return {
                'total_training_sessions': 0,
                'successful_sessions': 0,
                'average_improvement': 0,
                'success_rate': 0,
                'last_training': None
            }
        
        return {
            'total_training_sessions': len(agent_sessions),
            'successful_sessions': len([s for s in agent_sessions if s.success]),
            'average_improvement': np.mean([s.improvement_score for s in agent_sessions]),
            'success_rate': len([s for s in agent_sessions if s.success]) / len(agent_sessions),
            'last_training': max([s.timestamp for s in agent_sessions]).isoformat()
        }
    
    def _get_performance_trends(self, 
                              agent_type: str,
                              agent_sessions: List[TrainingSession],
                              trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance trend data for an agent."""
        return {
            'recent_improvements': [s.improvement_score for s in agent_sessions[-10:]],
            'trend_data': list(trend_data.get(agent_type, []))[-20:],
            'prediction_accuracy': self._calculate_prediction_accuracy(agent_type, agent_sessions)
        }
    
    def _get_adaptation_summary(self, adaptations: List[LearningAdaptation]) -> Dict[str, Any]:
        """Get adaptation summary for an agent."""
        return {
            'active_adaptations': len([a for a in adaptations if a.active]),
            'total_adaptations': len(adaptations),
            'recent_adaptations': [a.to_dict() for a in adaptations[-5:]]
        }
    
    def _get_prediction_summary(self, predictions: List[PerformancePrediction]) -> Dict[str, Any]:
        """Get prediction summary for an agent."""
        if not predictions:
            return {
                'current_predictions': [],
                'prediction_confidence': 0
            }
        
        return {
            'current_predictions': [p.to_dict() for p in predictions[-3:]],
            'prediction_confidence': np.mean([p.confidence for p in predictions])
        }
    
    def _calculate_prediction_accuracy(self, agent_type: str, agent_sessions: List[TrainingSession]) -> float:
        """Calculate prediction accuracy for agent type."""
        # Simplified accuracy calculation
        if len(agent_sessions) < 10:
            return 0.0
        
        # Look at recent performance variance as a proxy for predictability
        recent_scores = [s.improvement_score for s in agent_sessions[-10:]]
        variance = np.var(recent_scores)
        
        # Lower variance means more predictable, higher accuracy
        accuracy = max(0.0, min(1.0, 1.0 - (variance / 100.0)))
        return accuracy * 100.0  # Return as percentage
    
    def _get_agent_recommendations(self, agent_type: str, agent_sessions: List[TrainingSession]) -> List[str]:
        """Get recommendations for specific agent type."""
        recommendations = []
        
        if not agent_sessions:
            return ["No training data available - start training sessions"]
        
        # Analyze performance
        recent_sessions = agent_sessions[-10:]
        success_rate = len([s for s in recent_sessions if s.success]) / len(recent_sessions)
        avg_improvement = np.mean([s.improvement_score for s in recent_sessions])
        
        if success_rate < 0.5:
            recommendations.append(f"Low success rate ({success_rate:.1%}) - review training templates")
        
        if avg_improvement < 10.0:
            recommendations.append(f"Low improvement score ({avg_improvement:.1f}) - consider strategy adjustment")
        
        if len(recent_sessions) < 5:
            recommendations.append("Insufficient recent training data - increase training frequency")
        
        # Check for stagnation
        if len(recent_sessions) >= 5:
            improvements = [s.improvement_score for s in recent_sessions]
            if np.std(improvements) < 5.0:
                recommendations.append("Performance stagnation detected - try new training approaches")
        
        return recommendations
    
    def export_training_data(self,
                           training_sessions: List[TrainingSession],
                           adaptations: List[LearningAdaptation],
                           performance_predictions: List[PerformancePrediction],
                           training_templates: Dict[str, TrainingTemplate],
                           training_statistics: Dict[str, Any],
                           agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Export training data for analysis or backup."""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'training_sessions': [],
            'adaptations': [],
            'predictions': [],
            'templates': [],
            'statistics': training_statistics
        }
        
        # Filter by agent type if specified
        if agent_type:
            sessions = [s for s in training_sessions if s.agent_type == agent_type]
            adapt_list = [a for a in adaptations if a.agent_type == agent_type]
            pred_list = [p for p in performance_predictions if p.agent_type == agent_type]
            templates = [t for t in training_templates.values() if t.agent_type == agent_type]
        else:
            sessions = training_sessions
            adapt_list = adaptations
            pred_list = performance_predictions
            templates = list(training_templates.values())
        
        export_data['training_sessions'] = [s.to_dict() for s in sessions]
        export_data['adaptations'] = [a.to_dict() for a in adapt_list]
        export_data['predictions'] = [p.to_dict() for p in pred_list]
        export_data['templates'] = [t.to_dict() for t in templates]
        
        return export_data
    
    def generate_training_report(self,
                               training_sessions: List[TrainingSession],
                               adaptations: List[LearningAdaptation],
                               performance_predictions: List[PerformancePrediction],
                               training_strategies: Dict[str, Any]) -> str:
        """Generate a comprehensive training report."""
        report = []
        report.append("# Agent Training System Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # System overview
        report.append("## System Overview")
        total_sessions = len(training_sessions)
        successful_sessions = len([s for s in training_sessions if s.success])
        success_rate = (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        report.append(f"- Total Training Sessions: {total_sessions}")
        report.append(f"- Successful Sessions: {successful_sessions}")
        report.append(f"- Overall Success Rate: {success_rate:.1f}%")
        report.append("")
        
        # Agent-specific performance
        report.append("## Agent Performance Summary")
        for agent_type in training_strategies.keys():
            agent_sessions = [s for s in training_sessions if s.agent_type == agent_type]
            if agent_sessions:
                agent_success = len([s for s in agent_sessions if s.success])
                agent_rate = (agent_success / len(agent_sessions) * 100)
                avg_improvement = np.mean([s.improvement_score for s in agent_sessions])
                
                report.append(f"\n### {agent_type.title()} Agent")
                report.append(f"- Sessions: {len(agent_sessions)}")
                report.append(f"- Success Rate: {agent_rate:.1f}%")
                report.append(f"- Average Improvement: {avg_improvement:.1f}")
        
        # Active adaptations
        active_adaptations = [a for a in adaptations if a.active]
        report.append(f"\n## Active Adaptations: {len(active_adaptations)}")
        for adapt in active_adaptations[:5]:  # Show top 5
            report.append(f"- {adapt.agent_type}: {adapt.adaptation_type} (effectiveness: {adapt.effectiveness_score:.2f})")
        
        # Recent predictions
        report.append(f"\n## Recent Performance Predictions")
        for pred in performance_predictions[-3:]:  # Show last 3
            report.append(f"- {pred.agent_type}: {pred.trend_direction} trend (confidence: {pred.confidence:.1%})")
        
        report.append("")
        return "\n".join(report)
    
    def get_training_health_status(self,
                                 training_sessions: List[TrainingSession],
                                 background_tasks: List[Any],
                                 training_strategies: Dict[str, Any],
                                 training_templates: Dict[str, TrainingTemplate]) -> Dict[str, bool]:
        """Get health status of the training system."""
        return {
            'training_strategies_loaded': len(training_strategies) > 0,
            'training_templates_loaded': len(training_templates) > 0,
            'background_tasks_running': len([t for t in background_tasks if not t.done()]) > 0,
            'recent_training_activity': len(training_sessions) > 0,
            'system_healthy': True  # Can add more sophisticated health checks
        }