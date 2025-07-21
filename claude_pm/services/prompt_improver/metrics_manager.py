"""
Metrics calculation and analytics module

This module handles the calculation and management of improvement metrics
and analytics for the prompt improvement system.

Author: Claude PM Framework
Date: 2025-07-19
Version: 1.0.0
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .models import ImprovementMetrics, PromptImprovement, STATUS_APPROVED, STATUS_ROLLED_BACK


class MetricsManager:
    """Manages improvement metrics and analytics"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    async def create_improvement_metrics(self, improvement: PromptImprovement) -> ImprovementMetrics:
        """Create metrics for applied improvement"""
        try:
            metrics = ImprovementMetrics(
                improvement_id=improvement.improvement_id,
                success_rate=0.0,  # To be updated with actual usage data
                error_reduction=0.0,
                performance_improvement=improvement.effectiveness_score or 0.0,
                user_satisfaction=0.0,
                rollback_rate=0.0,
                adoption_rate=1.0  # Initially 100% since it's applied
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error creating metrics for {improvement.improvement_id}: {e}")
            raise
    
    async def update_rollback_metrics(self, improvement_id: str, metrics: ImprovementMetrics):
        """Update metrics when improvement is rolled back"""
        metrics.rollback_rate = 1.0
        
    async def calculate_improvement_metrics(self, 
                                          improvements: List[PromptImprovement],
                                          agent_type: Optional[str] = None,
                                          days_back: int = 30) -> Dict[str, Any]:
        """
        Calculate improvement metrics and analytics
        
        Args:
            improvements: List of improvements to analyze
            agent_type: Filter by agent type (optional)
            days_back: Number of days to analyze
            
        Returns:
            Improvement metrics and analytics
        """
        try:
            # Filter by timeframe
            since_date = datetime.now() - timedelta(days=days_back)
            filtered_improvements = [
                i for i in improvements 
                if i.timestamp >= since_date
            ]
            
            if agent_type:
                filtered_improvements = [
                    i for i in filtered_improvements 
                    if i.agent_type == agent_type
                ]
            
            # Calculate metrics
            total_improvements = len(filtered_improvements)
            approved_improvements = len([i for i in filtered_improvements if i.validation_status == STATUS_APPROVED])
            applied_improvements = len([i for i in filtered_improvements if i.validation_status == STATUS_APPROVED])
            rolled_back = len([i for i in filtered_improvements if i.validation_status == STATUS_ROLLED_BACK])
            
            # Effectiveness metrics
            effectiveness_scores = [i.effectiveness_score for i in filtered_improvements if i.effectiveness_score is not None]
            avg_effectiveness = statistics.mean(effectiveness_scores) if effectiveness_scores else 0.0
            
            # Strategy distribution
            strategy_counts = {}
            for improvement in filtered_improvements:
                strategy = improvement.strategy.value
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            # Agent type distribution
            agent_counts = {}
            for improvement in filtered_improvements:
                agent = improvement.agent_type
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            return {
                'period': {
                    'days_back': days_back,
                    'start_date': since_date.isoformat(),
                    'end_date': datetime.now().isoformat()
                },
                'summary': {
                    'total_improvements': total_improvements,
                    'approved_improvements': approved_improvements,
                    'applied_improvements': applied_improvements,
                    'rolled_back': rolled_back,
                    'approval_rate': approved_improvements / total_improvements if total_improvements > 0 else 0.0,
                    'rollback_rate': rolled_back / applied_improvements if applied_improvements > 0 else 0.0
                },
                'effectiveness': {
                    'average_effectiveness': avg_effectiveness,
                    'improvements_with_scores': len(effectiveness_scores),
                    'effectiveness_distribution': self._calculate_effectiveness_distribution(effectiveness_scores)
                },
                'strategy_distribution': strategy_counts,
                'agent_distribution': agent_counts,
                'recent_improvements': self._get_recent_improvements(filtered_improvements)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating improvement metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_effectiveness_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate effectiveness score distribution"""
        if not scores:
            return {}
        
        ranges = {
            'excellent': 0,  # > 0.8
            'good': 0,       # 0.6 - 0.8
            'moderate': 0,   # 0.4 - 0.6
            'poor': 0        # < 0.4
        }
        
        for score in scores:
            if score > 0.8:
                ranges['excellent'] += 1
            elif score > 0.6:
                ranges['good'] += 1
            elif score > 0.4:
                ranges['moderate'] += 1
            else:
                ranges['poor'] += 1
        
        return ranges
    
    def _get_recent_improvements(self, improvements: List[PromptImprovement], limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent improvements formatted for display"""
        sorted_improvements = sorted(improvements, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                'improvement_id': i.improvement_id,
                'agent_type': i.agent_type,
                'strategy': i.strategy.value,
                'status': i.validation_status,
                'effectiveness': i.effectiveness_score,
                'timestamp': i.timestamp.isoformat()
            }
            for i in sorted_improvements
        ]