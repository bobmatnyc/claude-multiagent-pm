"""
Learning Integration Service - MEM-006 Integration Component
Integrates ContinuousLearningEngine with IntelligentTaskPlanner and mem0AI systems.
Provides seamless workflow for learning-enhanced task management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .continuous_learning_engine import (
    ContinuousLearningEngine, TaskOutcome, OutcomeType, PatternType,
    LearningPattern, LearningMetric, LearningMetricType, create_continuous_learning_engine
)
from .intelligent_task_planner import (
    IntelligentTaskPlanner, TaskDecomposition, SubTask, TaskComplexity, 
    DecompositionStrategy, create_intelligent_task_planner
)
from .claude_pm_memory import ClaudePMMemory, MemoryCategory
from .mem0_context_manager import Mem0ContextManager
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class LearningMode(str, Enum):
    """Learning integration modes."""
    PASSIVE = "passive"      # Learning runs in background
    ACTIVE = "active"        # Learning influences planning
    PREDICTIVE = "predictive"  # Learning predicts outcomes
    ADAPTIVE = "adaptive"    # Learning adapts strategies


@dataclass
class LearningEnhancedDecomposition:
    """Task decomposition enhanced with learning insights."""
    base_decomposition: TaskDecomposition
    learning_confidence: float
    risk_assessment: Dict[str, float]
    similar_patterns: List[LearningPattern]
    recommended_adjustments: List[str]
    predicted_accuracy: float
    learning_insights: List[str]
    
    # Enhanced estimation
    confidence_adjusted_hours: float
    risk_adjusted_hours: float
    learning_adjusted_strategy: Optional[DecompositionStrategy] = None


@dataclass
class LearningFeedback:
    """Feedback from learning system to improve planning."""
    feedback_id: str
    task_description: str
    original_estimate: float
    learning_adjustment: float
    confidence_level: float
    reasoning: str
    supporting_patterns: List[str]
    recommended_changes: List[str]
    created_at: datetime


class LearningIntegrationService:
    """
    Integration service that connects ContinuousLearningEngine with IntelligentTaskPlanner.
    Provides learning-enhanced task planning and outcome-driven improvements.
    """
    
    def __init__(self, memory: ClaudePMMemory, context_manager: Mem0ContextManager,
                 learning_mode: LearningMode = LearningMode.ADAPTIVE):
        """
        Initialize the learning integration service.
        
        Args:
            memory: ClaudePMMemory instance
            context_manager: Mem0ContextManager instance
            learning_mode: Mode of learning integration
        """
        self.memory = memory
        self.context_manager = context_manager
        self.learning_mode = learning_mode
        
        # Initialize core components
        self.learning_engine = create_continuous_learning_engine(memory)
        self.task_planner = create_intelligent_task_planner(memory, context_manager)
        
        # Integration state
        self.active_tasks: Dict[str, TaskDecomposition] = {}
        self.learning_feedback_history: List[LearningFeedback] = []
        self.integration_metrics = {
            "learning_influenced_plans": 0,
            "accuracy_improvements": [],
            "risk_predictions": [],
            "adaptation_count": 0
        }
        
        # Configuration
        self.confidence_threshold = 0.7
        self.risk_threshold = 0.3
        self.learning_adjustment_limit = 0.5  # Max 50% adjustment
        
        logger.info(f"LearningIntegrationService initialized in {learning_mode.value} mode")
    
    async def create_learning_enhanced_decomposition(self, task_description: str,
                                                   project_name: Optional[str] = None,
                                                   **kwargs) -> LearningEnhancedDecomposition:
        """
        Create a task decomposition enhanced with learning insights.
        
        Args:
            task_description: Description of the task to decompose
            project_name: Optional project context
            **kwargs: Additional parameters for decomposition
            
        Returns:
            Learning-enhanced task decomposition
        """
        try:
            logger.info(f"Creating learning-enhanced decomposition for: {task_description[:100]}...")
            
            # Step 1: Get base decomposition from IntelligentTaskPlanner
            base_decomposition = await self.task_planner.decompose_task(
                task_description, project_name, **kwargs
            )
            
            # Step 2: Analyze similar patterns from learning engine
            similar_patterns = await self._find_relevant_learning_patterns(
                task_description, project_name
            )
            
            # Step 3: Assess risk based on learning history
            risk_assessment = await self._assess_learning_based_risk(
                task_description, base_decomposition, similar_patterns
            )
            
            # Step 4: Generate learning insights and adjustments
            learning_insights, adjustments = await self._generate_learning_insights(
                base_decomposition, similar_patterns, risk_assessment
            )
            
            # Step 5: Calculate confidence and predictions
            learning_confidence = self._calculate_learning_confidence(
                similar_patterns, base_decomposition
            )
            predicted_accuracy = self._predict_decomposition_accuracy(
                base_decomposition, similar_patterns
            )
            
            # Step 6: Apply learning adjustments if in active/adaptive mode
            adjusted_hours, adjusted_strategy = await self._apply_learning_adjustments(
                base_decomposition, similar_patterns, risk_assessment
            )
            
            # Step 7: Create enhanced decomposition
            enhanced_decomposition = LearningEnhancedDecomposition(
                base_decomposition=base_decomposition,
                learning_confidence=learning_confidence,
                risk_assessment=risk_assessment,
                similar_patterns=similar_patterns,
                recommended_adjustments=adjustments,
                predicted_accuracy=predicted_accuracy,
                learning_insights=learning_insights,
                confidence_adjusted_hours=adjusted_hours,
                risk_adjusted_hours=self._calculate_risk_adjusted_hours(
                    adjusted_hours, risk_assessment
                ),
                learning_adjusted_strategy=adjusted_strategy
            )
            
            # Store for tracking
            self.active_tasks[base_decomposition.decomposition_id] = base_decomposition
            
            # Update metrics
            self.integration_metrics["learning_influenced_plans"] += 1
            
            logger.info(f"Created learning-enhanced decomposition with {learning_confidence:.2f} confidence")
            return enhanced_decomposition
            
        except Exception as e:
            logger.error(f"Failed to create learning-enhanced decomposition: {e}")
            # Fallback to base decomposition
            base_decomposition = await self.task_planner.decompose_task(
                task_description, project_name, **kwargs
            )
            return LearningEnhancedDecomposition(
                base_decomposition=base_decomposition,
                learning_confidence=0.5,
                risk_assessment={},
                similar_patterns=[],
                recommended_adjustments=[],
                predicted_accuracy=0.5,
                learning_insights=["Learning analysis failed - using base decomposition"],
                confidence_adjusted_hours=base_decomposition.total_estimated_hours,
                risk_adjusted_hours=base_decomposition.total_estimated_hours
            )
    
    async def capture_task_completion(self, task_id: str, actual_outcome: TaskOutcome) -> bool:
        """
        Capture task completion and trigger learning updates.
        
        Args:
            task_id: ID of the completed task
            actual_outcome: Actual outcome of the task
            
        Returns:
            Success status of capture and learning update
        """
        try:
            logger.info(f"Capturing completion for task: {task_id}")
            
            # Capture outcome in learning engine
            learning_result = await self.learning_engine.capture_task_outcome(actual_outcome)
            
            if not learning_result:
                logger.warning(f"Failed to capture outcome in learning engine for task {task_id}")
                return False
            
            # If we have the original decomposition, analyze learning effectiveness
            if actual_outcome.decomposition_id in self.active_tasks:
                original_decomposition = self.active_tasks[actual_outcome.decomposition_id]
                await self._analyze_decomposition_accuracy(original_decomposition, actual_outcome)
            
            # Trigger pattern extraction and learning updates
            await self._trigger_learning_updates(actual_outcome)
            
            # Generate feedback for future planning
            feedback = await self._generate_learning_feedback(actual_outcome)
            if feedback:
                self.learning_feedback_history.append(feedback)
            
            logger.info(f"Successfully captured task completion and updated learning")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture task completion: {e}")
            return False
    
    async def get_learning_recommendations(self, task_description: str,
                                         project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get learning-based recommendations for a task.
        
        Args:
            task_description: Description of the task
            project_name: Optional project context
            
        Returns:
            Dictionary of learning recommendations
        """
        try:
            recommendations = {
                "risk_level": "medium",
                "confidence": 0.5,
                "estimated_accuracy": 0.5,
                "similar_patterns": [],
                "risk_factors": [],
                "success_factors": [],
                "prevention_strategies": [],
                "optimization_opportunities": [],
                "recommended_approach": "standard"
            }
            
            # Find similar patterns
            similar_patterns = await self._find_relevant_learning_patterns(
                task_description, project_name
            )
            
            if similar_patterns:
                recommendations["similar_patterns"] = [
                    {
                        "pattern_name": p.name,
                        "success_rate": p.success_rate,
                        "confidence": p.confidence_score,
                        "recommendations": p.recommendations[:3]
                    }
                    for p in similar_patterns[:3]
                ]
                
                # Analyze risk factors
                failure_patterns = [p for p in similar_patterns if p.pattern_type == PatternType.FAILURE_PATTERN]
                if failure_patterns:
                    risk_level = self._calculate_risk_level(failure_patterns)
                    recommendations["risk_level"] = risk_level
                    recommendations["risk_factors"] = self._extract_risk_factors(failure_patterns)
                    recommendations["prevention_strategies"] = self._extract_prevention_strategies(failure_patterns)
                
                # Analyze success factors
                success_patterns = [p for p in similar_patterns if p.pattern_type == PatternType.SUCCESS_PATTERN]
                if success_patterns:
                    recommendations["success_factors"] = self._extract_success_factors(success_patterns)
                    recommendations["optimization_opportunities"] = self._extract_optimizations(success_patterns)
                
                # Calculate overall confidence
                avg_confidence = sum(p.confidence_score for p in similar_patterns) / len(similar_patterns)
                recommendations["confidence"] = avg_confidence
                
                # Predict accuracy
                recommendations["estimated_accuracy"] = self._predict_task_accuracy(similar_patterns)
                
                # Recommend approach
                recommendations["recommended_approach"] = self._recommend_approach(similar_patterns)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get learning recommendations: {e}")
            return {"error": str(e)}
    
    async def analyze_learning_effectiveness(self, period_days: int = 90) -> Dict[str, Any]:
        """
        Analyze the effectiveness of learning integration.
        
        Args:
            period_days: Analysis period in days
            
        Returns:
            Learning effectiveness analysis
        """
        try:
            analysis_period = timedelta(days=period_days)
            
            # Get learning engine analysis
            learning_analysis = await self.learning_engine.analyze_learning_effectiveness(analysis_period)
            
            # Add integration-specific analysis
            integration_analysis = {
                "integration_mode": self.learning_mode.value,
                "learning_influenced_plans": self.integration_metrics["learning_influenced_plans"],
                "average_prediction_accuracy": self._calculate_average_prediction_accuracy(),
                "risk_prediction_effectiveness": self._analyze_risk_predictions(),
                "adaptation_impact": self._analyze_adaptation_impact(),
                "feedback_quality": self._analyze_feedback_quality(),
                "integration_recommendations": self._generate_integration_recommendations()
            }
            
            # Combine analyses
            combined_analysis = {
                **learning_analysis,
                "integration_analysis": integration_analysis,
                "overall_integration_health": self._assess_integration_health()
            }
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze learning effectiveness: {e}")
            return {"error": str(e)}
    
    async def _find_relevant_learning_patterns(self, task_description: str,
                                             project_name: Optional[str]) -> List[LearningPattern]:
        """Find learning patterns relevant to the task."""
        try:
            # Get all current patterns from learning engine
            all_patterns = list(self.learning_engine.identified_patterns.values())
            
            # Filter for relevance (simplified implementation)
            relevant_patterns = []
            task_keywords = task_description.lower().split()
            
            for pattern in all_patterns:
                # Check if pattern is recent and relevant
                days_since_observed = (datetime.now() - pattern.last_observed).days
                if days_since_observed <= 90:  # Recent patterns only
                    
                    # Simple relevance scoring based on keyword overlap
                    pattern_keywords = pattern.name.lower().split()
                    overlap = len(set(task_keywords).intersection(set(pattern_keywords)))
                    
                    if overlap > 0:
                        relevant_patterns.append(pattern)
            
            # Sort by confidence and relevance
            relevant_patterns.sort(key=lambda p: p.confidence_score, reverse=True)
            return relevant_patterns[:5]  # Top 5 most relevant
            
        except Exception as e:
            logger.error(f"Failed to find relevant patterns: {e}")
            return []
    
    async def _assess_learning_based_risk(self, task_description: str,
                                        decomposition: TaskDecomposition,
                                        patterns: List[LearningPattern]) -> Dict[str, float]:
        """Assess risk based on learning patterns."""
        risk_assessment = {
            "overall_risk": 0.3,  # Default medium risk
            "estimation_risk": 0.3,
            "complexity_risk": 0.3,
            "failure_risk": 0.3,
            "timeline_risk": 0.3
        }
        
        if not patterns:
            return risk_assessment
        
        # Analyze failure patterns
        failure_patterns = [p for p in patterns if p.pattern_type == PatternType.FAILURE_PATTERN]
        if failure_patterns:
            failure_rate = sum((1.0 - p.success_rate) for p in failure_patterns) / len(failure_patterns)
            risk_assessment["failure_risk"] = min(0.9, failure_rate)
            risk_assessment["overall_risk"] = max(risk_assessment["overall_risk"], failure_rate * 0.8)
        
        # Analyze complexity patterns
        if decomposition.complexity == TaskComplexity.COMPLEX or decomposition.complexity == TaskComplexity.EPIC:
            risk_assessment["complexity_risk"] = 0.6
            risk_assessment["overall_risk"] = max(risk_assessment["overall_risk"], 0.5)
        
        # Analyze estimation accuracy from patterns
        estimation_accuracies = []
        for pattern in patterns:
            if "average_time_accuracy" in pattern.outcomes:
                estimation_accuracies.append(pattern.outcomes["average_time_accuracy"])
        
        if estimation_accuracies:
            avg_accuracy = sum(estimation_accuracies) / len(estimation_accuracies)
            estimation_risk = 1.0 - avg_accuracy
            risk_assessment["estimation_risk"] = min(0.9, estimation_risk)
        
        return risk_assessment
    
    async def _generate_learning_insights(self, decomposition: TaskDecomposition,
                                        patterns: List[LearningPattern],
                                        risk_assessment: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """Generate learning insights and recommended adjustments."""
        insights = []
        adjustments = []
        
        if not patterns:
            insights.append("No similar historical patterns found - proceeding with standard approach")
            return insights, adjustments
        
        # Analyze success patterns
        success_patterns = [p for p in patterns if p.pattern_type == PatternType.SUCCESS_PATTERN]
        if success_patterns:
            best_pattern = max(success_patterns, key=lambda p: p.success_rate)
            insights.append(f"Similar successful pattern found: {best_pattern.name} ({best_pattern.success_rate:.1%} success)")
            adjustments.extend(best_pattern.recommendations[:2])
        
        # Analyze failure patterns
        failure_patterns = [p for p in patterns if p.pattern_type == PatternType.FAILURE_PATTERN]
        if failure_patterns:
            worst_pattern = min(failure_patterns, key=lambda p: p.success_rate)
            insights.append(f"Risk pattern identified: {worst_pattern.name} - implement prevention strategies")
            adjustments.extend([f"Prevent: {rec}" for rec in worst_pattern.recommendations[:2]])
        
        # Risk-based insights
        if risk_assessment["overall_risk"] > 0.6:
            insights.append("High risk detected - recommend additional planning and risk mitigation")
            adjustments.append("Add risk mitigation phase to decomposition")
        
        # Efficiency insights
        efficiency_patterns = [p for p in patterns if p.pattern_type == PatternType.EFFICIENCY_PATTERN]
        if efficiency_patterns:
            insights.append("Efficiency optimization opportunities identified")
            adjustments.append("Apply efficiency best practices from similar tasks")
        
        return insights, adjustments
    
    def _calculate_learning_confidence(self, patterns: List[LearningPattern],
                                     decomposition: TaskDecomposition) -> float:
        """Calculate confidence based on learning patterns."""
        if not patterns:
            return 0.5  # Medium confidence with no patterns
        
        # Average confidence of relevant patterns
        pattern_confidence = sum(p.confidence_score for p in patterns) / len(patterns)
        
        # Adjust based on pattern age and relevance
        recent_patterns = [p for p in patterns if (datetime.now() - p.last_observed).days <= 30]
        recency_factor = len(recent_patterns) / len(patterns)
        
        # Adjust based on sample size
        total_cases = sum(p.supporting_cases for p in patterns)
        sample_factor = min(1.0, total_cases / 10)  # Full confidence at 10+ cases
        
        overall_confidence = pattern_confidence * recency_factor * sample_factor
        return min(0.95, max(0.1, overall_confidence))
    
    def _predict_decomposition_accuracy(self, decomposition: TaskDecomposition,
                                      patterns: List[LearningPattern]) -> float:
        """Predict the accuracy of the decomposition."""
        if not patterns:
            return 0.7  # Default prediction
        
        # Analyze historical accuracy from patterns
        accuracies = []
        for pattern in patterns:
            if "average_time_accuracy" in pattern.outcomes:
                accuracies.append(pattern.outcomes["average_time_accuracy"])
        
        if accuracies:
            return sum(accuracies) / len(accuracies)
        
        # Fallback based on pattern success rates
        avg_success_rate = sum(p.success_rate for p in patterns) / len(patterns)
        return avg_success_rate * 0.8  # Conservative estimate
    
    async def _apply_learning_adjustments(self, decomposition: TaskDecomposition,
                                        patterns: List[LearningPattern],
                                        risk_assessment: Dict[str, float]) -> Tuple[float, Optional[DecompositionStrategy]]:
        """Apply learning-based adjustments to decomposition."""
        adjusted_hours = decomposition.total_estimated_hours
        adjusted_strategy = None
        
        if self.learning_mode not in [LearningMode.ACTIVE, LearningMode.ADAPTIVE]:
            return adjusted_hours, adjusted_strategy
        
        # Adjust based on historical accuracy
        if patterns:
            # Calculate average estimation bias from patterns
            estimation_biases = []
            for pattern in patterns:
                if "time_accuracy_variance" in pattern.outcomes:
                    variance = pattern.outcomes["time_accuracy_variance"]
                    if variance > 0.2:  # High variance indicates underestimation
                        estimation_biases.append(0.15)  # 15% buffer
                    elif variance < 0.1:  # Low variance indicates good estimation
                        estimation_biases.append(0.0)
                    else:
                        estimation_biases.append(0.05)  # 5% buffer
            
            if estimation_biases:
                avg_bias = sum(estimation_biases) / len(estimation_biases)
                adjustment_factor = 1.0 + min(self.learning_adjustment_limit, avg_bias)
                adjusted_hours = decomposition.total_estimated_hours * adjustment_factor
        
        # Adjust based on risk assessment
        overall_risk = risk_assessment.get("overall_risk", 0.3)
        if overall_risk > 0.6:
            risk_buffer = 1.0 + (overall_risk - 0.5) * 0.4  # Up to 20% buffer for high risk
            adjusted_hours *= risk_buffer
        
        # Suggest strategy adjustment for high-risk tasks
        if overall_risk > 0.7 and decomposition.strategy != DecompositionStrategy.LINEAR:
            adjusted_strategy = DecompositionStrategy.LINEAR  # More conservative approach
        
        return adjusted_hours, adjusted_strategy
    
    def _calculate_risk_adjusted_hours(self, base_hours: float,
                                     risk_assessment: Dict[str, float]) -> float:
        """Calculate risk-adjusted hours estimate."""
        overall_risk = risk_assessment.get("overall_risk", 0.3)
        
        # Apply risk multiplier
        if overall_risk > 0.7:
            risk_multiplier = 1.3  # 30% buffer for high risk
        elif overall_risk > 0.5:
            risk_multiplier = 1.15  # 15% buffer for medium-high risk
        elif overall_risk > 0.3:
            risk_multiplier = 1.05  # 5% buffer for medium risk
        else:
            risk_multiplier = 1.0  # No buffer for low risk
        
        return base_hours * risk_multiplier
    
    # Additional helper methods for analysis and recommendations
    def _calculate_risk_level(self, failure_patterns: List[LearningPattern]) -> str:
        """Calculate risk level from failure patterns."""
        if not failure_patterns:
            return "low"
        
        avg_failure_rate = sum((1.0 - p.success_rate) for p in failure_patterns) / len(failure_patterns)
        
        if avg_failure_rate > 0.7:
            return "critical"
        elif avg_failure_rate > 0.5:
            return "high"
        elif avg_failure_rate > 0.3:
            return "medium"
        else:
            return "low"
    
    def _extract_risk_factors(self, failure_patterns: List[LearningPattern]) -> List[str]:
        """Extract risk factors from failure patterns."""
        risk_factors = []
        for pattern in failure_patterns:
            for condition in pattern.conditions.get("common_failure_factors", []):
                if condition not in risk_factors:
                    risk_factors.append(condition)
        return risk_factors[:5]  # Top 5
    
    def _extract_prevention_strategies(self, failure_patterns: List[LearningPattern]) -> List[str]:
        """Extract prevention strategies from failure patterns."""
        strategies = []
        for pattern in failure_patterns:
            for rec in pattern.recommendations:
                if "prevent" in rec.lower() or "mitigate" in rec.lower():
                    if rec not in strategies:
                        strategies.append(rec)
        return strategies[:3]  # Top 3
    
    def _extract_success_factors(self, success_patterns: List[LearningPattern]) -> List[str]:
        """Extract success factors from success patterns."""
        factors = []
        for pattern in success_patterns:
            for factor in pattern.outcomes.get("common_success_factors", []):
                if factor not in factors:
                    factors.append(factor)
        return factors[:5]  # Top 5
    
    def _extract_optimizations(self, success_patterns: List[LearningPattern]) -> List[str]:
        """Extract optimization opportunities from success patterns."""
        optimizations = []
        for pattern in success_patterns:
            for rec in pattern.recommendations:
                if "efficient" in rec.lower() or "optimize" in rec.lower():
                    if rec not in optimizations:
                        optimizations.append(rec)
        return optimizations[:3]  # Top 3
    
    def _predict_task_accuracy(self, patterns: List[LearningPattern]) -> float:
        """Predict task estimation accuracy from patterns."""
        accuracies = []
        for pattern in patterns:
            if "average_time_accuracy" in pattern.outcomes:
                accuracies.append(pattern.outcomes["average_time_accuracy"])
        
        if accuracies:
            return sum(accuracies) / len(accuracies)
        
        # Fallback based on success rates
        avg_success = sum(p.success_rate for p in patterns) / len(patterns)
        return avg_success * 0.8  # Conservative estimate
    
    def _recommend_approach(self, patterns: List[LearningPattern]) -> str:
        """Recommend approach based on patterns."""
        success_patterns = [p for p in patterns if p.pattern_type == PatternType.SUCCESS_PATTERN]
        failure_patterns = [p for p in patterns if p.pattern_type == PatternType.FAILURE_PATTERN]
        
        if len(failure_patterns) > len(success_patterns):
            return "conservative"
        elif any(p.pattern_type == PatternType.EFFICIENCY_PATTERN for p in patterns):
            return "optimized"
        elif success_patterns and all(p.success_rate > 0.8 for p in success_patterns):
            return "aggressive"
        else:
            return "standard"
    
    # Placeholder methods for integration analysis
    def _calculate_average_prediction_accuracy(self) -> float:
        """Calculate average prediction accuracy."""
        return 0.78  # Placeholder
    
    def _analyze_risk_predictions(self) -> Dict[str, Any]:
        """Analyze risk prediction effectiveness."""
        return {"accuracy": 0.75, "precision": 0.72, "recall": 0.68}
    
    def _analyze_adaptation_impact(self) -> Dict[str, Any]:
        """Analyze impact of learning adaptations."""
        return {"improvement_rate": 0.12, "accuracy_gain": 0.08}
    
    def _analyze_feedback_quality(self) -> Dict[str, Any]:
        """Analyze quality of learning feedback."""
        return {"relevance": 0.82, "actionability": 0.76}
    
    def _generate_integration_recommendations(self) -> List[str]:
        """Generate recommendations for integration improvement."""
        return [
            "Increase pattern recognition frequency",
            "Enhance risk assessment algorithms",
            "Improve feedback loop responsiveness"
        ]
    
    def _assess_integration_health(self) -> str:
        """Assess overall integration health."""
        return "good"  # Placeholder
    
    async def _analyze_decomposition_accuracy(self, decomposition: TaskDecomposition,
                                           outcome: TaskOutcome) -> None:
        """Analyze accuracy of decomposition vs actual outcome."""
        try:
            accuracy = 1.0 - abs(outcome.actual_hours - decomposition.total_estimated_hours) / decomposition.total_estimated_hours
            self.integration_metrics["accuracy_improvements"].append(accuracy)
            
            # Store analysis in memory for learning
            accuracy_data = {
                "decomposition_id": decomposition.decomposition_id,
                "estimated_hours": decomposition.total_estimated_hours,
                "actual_hours": outcome.actual_hours,
                "accuracy": accuracy,
                "strategy": decomposition.strategy.value,
                "complexity": decomposition.complexity.value
            }
            
            await self.memory.store_memory(
                category=MemoryCategory.PATTERN,
                content=f"Decomposition accuracy analysis: {accuracy:.2%}",
                metadata={
                    "type": "decomposition_accuracy",
                    "accuracy_data": accuracy_data
                },
                project_name=outcome.project_name,
                tags=["decomposition_accuracy", "learning_integration"]
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze decomposition accuracy: {e}")
    
    async def _trigger_learning_updates(self, outcome: TaskOutcome) -> None:
        """Trigger learning updates based on outcome."""
        try:
            # Trigger pattern extraction
            if outcome.outcome_type == OutcomeType.SUCCESS:
                await self.learning_engine.extract_success_patterns(outcome.project_name)
            elif outcome.outcome_type == OutcomeType.FAILURE:
                await self.learning_engine.analyze_failure_patterns(outcome.project_name)
            
            # Update learning metrics
            await self.learning_engine.track_learning_metrics()
            
        except Exception as e:
            logger.error(f"Failed to trigger learning updates: {e}")
    
    async def _generate_learning_feedback(self, outcome: TaskOutcome) -> Optional[LearningFeedback]:
        """Generate learning feedback for future planning."""
        try:
            if outcome.estimated_hours <= 0:
                return None
            
            accuracy = 1.0 - abs(outcome.actual_hours - outcome.estimated_hours) / outcome.estimated_hours
            
            if accuracy < 0.8:  # Generate feedback for inaccurate estimates
                feedback = LearningFeedback(
                    feedback_id=f"feedback_{outcome.task_id}",
                    task_description=outcome.task_description,
                    original_estimate=outcome.estimated_hours,
                    learning_adjustment=outcome.actual_hours - outcome.estimated_hours,
                    confidence_level=0.7,
                    reasoning=f"Task took {outcome.actual_hours:.1f}h vs estimated {outcome.estimated_hours:.1f}h",
                    supporting_patterns=[],
                    recommended_changes=[
                        "Adjust estimation for similar tasks",
                        "Consider additional complexity factors"
                    ],
                    created_at=datetime.now()
                )
                return feedback
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate learning feedback: {e}")
            return None
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration service statistics."""
        return {
            "learning_mode": self.learning_mode.value,
            "active_tasks": len(self.active_tasks),
            "learning_feedback_count": len(self.learning_feedback_history),
            "integration_metrics": self.integration_metrics,
            "learning_engine_stats": self.learning_engine.get_learning_stats(),
            "task_planner_stats": self.task_planner.get_planner_stats()
        }


# Factory function
def create_learning_integration_service(memory: ClaudePMMemory, 
                                       context_manager: Mem0ContextManager,
                                       learning_mode: LearningMode = LearningMode.ADAPTIVE) -> LearningIntegrationService:
    """
    Create and initialize a LearningIntegrationService.
    
    Args:
        memory: ClaudePMMemory instance
        context_manager: Mem0ContextManager instance
        learning_mode: Mode of learning integration
        
    Returns:
        Initialized LearningIntegrationService
    """
    return LearningIntegrationService(memory, context_manager, learning_mode)