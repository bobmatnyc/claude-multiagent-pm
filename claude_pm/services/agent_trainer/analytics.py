"""
Agent Training Analytics Module
==============================

This module handles analytics, trend analysis, and predictions for the agent training system.

Classes:
    TrainingAnalytics: Main class for training analytics and predictions
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from .types import (
    TrainingSession, PerformancePrediction, LearningAdaptation
)

logger = logging.getLogger(__name__)


class TrainingAnalytics:
    """Handles analytics and performance predictions for agent training."""
    
    def __init__(self):
        """Initialize the analytics system."""
        self.logger = logger
        self.trend_data = defaultdict(lambda: deque(maxlen=100))  # Last 100 data points
        self.prediction_models = {}
        self.performance_predictions: List[PerformancePrediction] = []
    
    async def analyze_performance_trends(self, 
                                       training_sessions: List[TrainingSession],
                                       training_strategies: Dict[str, Any]) -> None:
        """Analyze performance trends for each agent type."""
        for agent_type in training_strategies.keys():
            recent_sessions = [
                session for session in training_sessions[-50:]  # Last 50 sessions
                if session.agent_type == agent_type
            ]
            
            if len(recent_sessions) < 5:
                continue  # Need at least 5 sessions for trend analysis
            
            # Calculate trend metrics
            improvements = [session.improvement_score for session in recent_sessions]
            avg_improvement = np.mean(improvements)
            trend_slope = np.polyfit(range(len(improvements)), improvements, 1)[0]
            
            # Update trend data
            self.trend_data[agent_type].append({
                'timestamp': datetime.now(),
                'average_improvement': avg_improvement,
                'trend_slope': trend_slope,
                'session_count': len(recent_sessions)
            })
    
    async def update_prediction_models(self, training_strategies: Dict[str, Any]) -> None:
        """Update predictive models for performance forecasting."""
        for agent_type in training_strategies.keys():
            trend_data = list(self.trend_data[agent_type])
            
            if len(trend_data) < 10:
                continue  # Need at least 10 data points
            
            # Extract features for prediction
            features = []
            targets = []
            
            for i in range(len(trend_data) - 1):
                features.append([
                    trend_data[i]['average_improvement'],
                    trend_data[i]['trend_slope'],
                    trend_data[i]['session_count']
                ])
                targets.append(trend_data[i + 1]['average_improvement'])
            
            # Simple linear regression model (would use more sophisticated models in production)
            if len(features) >= 3:
                X = np.array(features)
                y = np.array(targets)
                
                # Calculate simple linear relationship
                coefficients = np.linalg.lstsq(X, y, rcond=None)[0]
                
                # Store model
                self.prediction_models[agent_type] = coefficients
    
    async def generate_performance_predictions(self) -> None:
        """Generate performance predictions for each agent type."""
        for agent_type, model in self.prediction_models.items():
            current_data = list(self.trend_data[agent_type])
            
            if not current_data:
                continue
            
            latest = current_data[-1]
            
            # Predict future performance
            current_features = np.array([
                latest['average_improvement'],
                latest['trend_slope'],
                latest['session_count']
            ])
            
            predicted_score = np.dot(current_features, model)
            
            # Determine trend direction
            if latest['trend_slope'] > 0.5:
                trend_direction = "improving"
            elif latest['trend_slope'] < -0.5:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
            
            # Calculate confidence (simplified)
            confidence = min(0.95, max(0.5, 1.0 - abs(latest['trend_slope']) * 0.1))
            
            # Generate prediction
            prediction = PerformancePrediction(
                agent_type=agent_type,
                prediction_type="performance_trend",
                current_score=latest['average_improvement'],
                predicted_score=predicted_score,
                confidence=confidence,
                trend_direction=trend_direction,
                time_horizon=7,  # 7 days
                factors=["recent_performance", "trend_slope", "session_volume"],
                recommendations=self._generate_recommendations(agent_type, prediction)
            )
            
            self.performance_predictions.append(prediction)
    
    def _generate_recommendations(self, agent_type: str, prediction: PerformancePrediction) -> List[str]:
        """Generate recommendations based on prediction."""
        recommendations = []
        
        if prediction.trend_direction == "declining":
            recommendations.extend([
                f"Review {agent_type} training templates for effectiveness",
                f"Increase training frequency for {agent_type} agents",
                f"Analyze failed training sessions for {agent_type}",
                f"Consider updating {agent_type} training strategy"
            ])
        elif prediction.trend_direction == "improving":
            recommendations.extend([
                f"Maintain current {agent_type} training approach",
                f"Document successful {agent_type} training patterns",
                f"Consider applying {agent_type} strategy to other agents"
            ])
        else:
            recommendations.extend([
                f"Experiment with new {agent_type} training techniques",
                f"Gather more diverse training data for {agent_type}",
                f"Consider hybrid training approaches for {agent_type}"
            ])
        
        return recommendations
    
    async def update_trend_data(self, 
                               training_sessions: List[TrainingSession],
                               training_strategies: Dict[str, Any]) -> None:
        """Update trend data for analytics."""
        for agent_type in training_strategies.keys():
            recent_sessions = [
                session for session in training_sessions[-20:]
                if session.agent_type == agent_type
            ]
            
            if recent_sessions:
                avg_improvement = np.mean([s.improvement_score for s in recent_sessions])
                success_rate = len([s for s in recent_sessions if s.success]) / len(recent_sessions)
                avg_duration = np.mean([s.training_duration for s in recent_sessions])
                
                self.trend_data[f"{agent_type}_metrics"].append({
                    'timestamp': datetime.now(),
                    'avg_improvement': avg_improvement,
                    'success_rate': success_rate,
                    'avg_duration': avg_duration,
                    'session_count': len(recent_sessions)
                })
    
    def calculate_prediction_accuracy(self, agent_type: str) -> float:
        """Calculate prediction accuracy for agent type."""
        # Simplified accuracy calculation
        predictions = [p for p in self.performance_predictions if p.agent_type == agent_type]
        
        if not predictions:
            return 0.0
        
        # Calculate average confidence as a proxy for accuracy
        return np.mean([p.confidence for p in predictions])
    
    def get_agent_recommendations(self, 
                                agent_type: str,
                                training_sessions: List[TrainingSession]) -> List[str]:
        """Get recommendations for specific agent type."""
        recommendations = []
        
        agent_sessions = [s for s in training_sessions if s.agent_type == agent_type]
        
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
    
    def get_effectiveness_metrics(self, training_sessions: List[TrainingSession]) -> Dict[str, Any]:
        """Calculate overall system effectiveness metrics."""
        if not training_sessions:
            return {
                'average_improvement': 0.0,
                'success_rate': 0.0,
                'total_sessions': 0,
                'active_adaptations': 0
            }
        
        total_improvement = sum(s.improvement_score for s in training_sessions)
        avg_improvement = total_improvement / len(training_sessions)
        
        success_rate = len([s for s in training_sessions if s.success]) / len(training_sessions)
        
        return {
            'average_improvement': avg_improvement,
            'success_rate': success_rate,
            'total_sessions': len(training_sessions),
            'active_adaptations': 0  # Will be updated by the main module
        }
    
    def get_agent_performance_stats(self, 
                                  agent_type: str,
                                  training_sessions: List[TrainingSession]) -> Dict[str, Any]:
        """Get performance statistics for a specific agent type."""
        agent_sessions = [s for s in training_sessions if s.agent_type == agent_type]
        
        if not agent_sessions:
            return {
                'total_sessions': 0,
                'successful_sessions': 0,
                'average_improvement': 0.0,
                'success_rate': 0.0,
                'average_duration': 0.0
            }
        
        return {
            'total_sessions': len(agent_sessions),
            'successful_sessions': len([s for s in agent_sessions if s.success]),
            'average_improvement': np.mean([s.improvement_score for s in agent_sessions]),
            'success_rate': len([s for s in agent_sessions if s.success]) / len(agent_sessions),
            'average_duration': np.mean([s.training_duration for s in agent_sessions])
        }
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance predictions."""
        return [pred.to_dict() for pred in self.performance_predictions[-limit:]]