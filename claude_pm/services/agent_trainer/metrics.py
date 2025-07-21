"""
Agent Training Metrics Module
============================

This module handles metrics collection, tracking, and adaptation effectiveness
for the agent training system.

Classes:
    TrainingMetrics: Main class for training metrics management
"""

import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional
import numpy as np

from .types import (
    TrainingSession, LearningAdaptation
)

logger = logging.getLogger(__name__)


class TrainingMetrics:
    """Handles metrics collection and tracking for agent training."""
    
    def __init__(self):
        """Initialize the metrics system."""
        self.logger = logger
        
        # Core metrics
        self.training_metrics = {
            'total_sessions': 0,
            'successful_sessions': 0,
            'average_improvement': 0.0,
            'agent_performance': defaultdict(list),
            'adaptation_effectiveness': defaultdict(list),
            'system_effectiveness': {}
        }
    
    def update_training_metrics(self, session: TrainingSession) -> None:
        """Update training metrics with new session data."""
        self.training_metrics['total_sessions'] += 1
        
        if session.success:
            self.training_metrics['successful_sessions'] += 1
        
        # Update average improvement
        if session.improvement_score > 0:
            current_avg = self.training_metrics['average_improvement']
            total_sessions = self.training_metrics['total_sessions']
            self.training_metrics['average_improvement'] = (
                (current_avg * (total_sessions - 1) + session.improvement_score) / total_sessions
            )
        
        # Update agent-specific performance
        self.training_metrics['agent_performance'][session.agent_type].append({
            'timestamp': session.timestamp,
            'improvement_score': session.improvement_score,
            'success': session.success,
            'duration': session.training_duration
        })
    
    async def check_adaptation_triggers(self, 
                                      agent_type: str, 
                                      session: TrainingSession,
                                      training_sessions: List[TrainingSession]) -> List[LearningAdaptation]:
        """Check if adaptations should be triggered based on session results."""
        adaptations = []
        
        # Check for poor performance
        if session.improvement_score < 5.0:
            adaptation = LearningAdaptation(
                agent_type=agent_type,
                adaptation_type="low_performance",
                trigger_condition=f"improvement_score < 5.0 (actual: {session.improvement_score})",
                adaptation_data={"focus": "basic_improvements", "complexity": "reduced"},
                effectiveness_score=0.0
            )
            adaptations.append(adaptation)
        
        # Check for consistently good performance
        recent_sessions = [
            s for s in training_sessions[-10:]
            if s.agent_type == agent_type and s.success
        ]
        
        if len(recent_sessions) >= 8:  # 8 out of 10 successful
            adaptation = LearningAdaptation(
                agent_type=agent_type,
                adaptation_type="high_performance",
                trigger_condition="8/10 recent sessions successful",
                adaptation_data={"focus": "advanced_techniques", "complexity": "increased"},
                effectiveness_score=0.0
            )
            adaptations.append(adaptation)
        
        return adaptations
    
    def update_effectiveness_metrics(self, training_sessions: List[TrainingSession], 
                                   active_adaptations: int) -> None:
        """Update effectiveness metrics for the training system."""
        # Calculate overall system effectiveness
        if training_sessions:
            total_improvement = sum(s.improvement_score for s in training_sessions)
            avg_improvement = total_improvement / len(training_sessions)
            
            success_rate = len([s for s in training_sessions if s.success]) / len(training_sessions)
            
            # Update system metrics
            self.training_metrics['system_effectiveness'] = {
                'average_improvement': avg_improvement,
                'success_rate': success_rate,
                'total_sessions': len(training_sessions),
                'active_adaptations': active_adaptations
            }
    
    def record_adaptation_effectiveness(self, 
                                      agent_type: str,
                                      adaptation_type: str,
                                      effectiveness_score: float,
                                      sessions_evaluated: int) -> None:
        """Record effectiveness of an adaptation."""
        self.training_metrics['adaptation_effectiveness'][agent_type].append({
            'adaptation_type': adaptation_type,
            'effectiveness_score': effectiveness_score,
            'sessions_evaluated': sessions_evaluated,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_training_statistics(self, 
                              training_strategies: Dict[str, Any],
                              training_sessions: List[TrainingSession],
                              performance_predictions: List[Any],
                              adaptations: List[LearningAdaptation]) -> Dict[str, Any]:
        """Get comprehensive training statistics."""
        stats = {
            'system_metrics': self.training_metrics,
            'agent_performance': {},
            'recent_predictions': [],
            'active_adaptations': [],
            'training_effectiveness': {}
        }
        
        # Agent-specific statistics
        for agent_type in training_strategies.keys():
            agent_sessions = [s for s in training_sessions if s.agent_type == agent_type]
            
            if agent_sessions:
                stats['agent_performance'][agent_type] = {
                    'total_sessions': len(agent_sessions),
                    'successful_sessions': len([s for s in agent_sessions if s.success]),
                    'average_improvement': np.mean([s.improvement_score for s in agent_sessions]),
                    'success_rate': len([s for s in agent_sessions if s.success]) / len(agent_sessions),
                    'average_duration': np.mean([s.training_duration for s in agent_sessions])
                }
        
        # Recent predictions
        stats['recent_predictions'] = [
            pred.to_dict() for pred in performance_predictions[-10:]
        ]
        
        # Active adaptations
        stats['active_adaptations'] = [
            adapt.to_dict() for adapt in adaptations if adapt.active
        ]
        
        # Training effectiveness by agent type
        for agent_type in training_strategies.keys():
            effectiveness_data = self.training_metrics['adaptation_effectiveness'][agent_type]
            if effectiveness_data:
                stats['training_effectiveness'][agent_type] = {
                    'adaptation_count': len(effectiveness_data),
                    'average_effectiveness': np.mean([d['effectiveness_score'] for d in effectiveness_data])
                }
        
        return stats
    
    def get_agent_metrics(self, agent_type: str) -> Dict[str, Any]:
        """Get metrics for a specific agent type."""
        agent_data = self.training_metrics['agent_performance'][agent_type]
        
        if not agent_data:
            return {
                'total_sessions': 0,
                'successful_sessions': 0,
                'average_improvement': 0.0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'recent_performance': []
            }
        
        successful = len([d for d in agent_data if d['success']])
        
        return {
            'total_sessions': len(agent_data),
            'successful_sessions': successful,
            'average_improvement': np.mean([d['improvement_score'] for d in agent_data]),
            'success_rate': successful / len(agent_data),
            'average_duration': np.mean([d['duration'] for d in agent_data]),
            'recent_performance': agent_data[-10:]  # Last 10 sessions
        }
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        return {
            'total_sessions': self.training_metrics['total_sessions'],
            'successful_sessions': self.training_metrics['successful_sessions'],
            'success_rate': (self.training_metrics['successful_sessions'] / 
                           self.training_metrics['total_sessions'] 
                           if self.training_metrics['total_sessions'] > 0 else 0),
            'average_improvement': self.training_metrics['average_improvement'],
            'active_agent_types': len(self.training_metrics['agent_performance']),
            'system_effectiveness': self.training_metrics.get('system_effectiveness', {})
        }
    
    def export_metrics(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Export metrics for analysis or backup."""
        if agent_type:
            return {
                'agent_type': agent_type,
                'metrics': self.get_agent_metrics(agent_type),
                'effectiveness_data': self.training_metrics['adaptation_effectiveness'].get(agent_type, []),
                'export_timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'system_metrics': self.get_system_health_metrics(),
                'agent_metrics': {
                    agent: self.get_agent_metrics(agent)
                    for agent in self.training_metrics['agent_performance'].keys()
                },
                'adaptation_effectiveness': dict(self.training_metrics['adaptation_effectiveness']),
                'export_timestamp': datetime.now().isoformat()
            }