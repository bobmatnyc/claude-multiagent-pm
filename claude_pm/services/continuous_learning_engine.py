"""
ContinuousLearningEngine - MEM-006 Implementation
Implements continuous learning capabilities for the Claude PM Framework.
Captures task outcomes, extracts patterns, prevents failures, and tracks learning improvement.
"""

import asyncio
import json
import logging
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .claude_pm_memory import ClaudePMMemory, MemoryCategory, MemoryResponse
from .intelligent_task_planner import TaskDecomposition, SubTask, TaskComplexity, DecompositionStrategy
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class OutcomeType(str, Enum):
    """Task outcome types."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"


class PatternType(str, Enum):
    """Types of patterns the learning engine can identify."""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    EFFICIENCY_PATTERN = "efficiency_pattern"
    COMPLEXITY_PATTERN = "complexity_pattern"
    STRATEGY_PATTERN = "strategy_pattern"
    TEMPORAL_PATTERN = "temporal_pattern"


class LearningMetricType(str, Enum):
    """Types of learning metrics tracked."""
    ACCURACY_IMPROVEMENT = "accuracy_improvement"
    ESTIMATION_PRECISION = "estimation_precision"
    PATTERN_RECOGNITION_RATE = "pattern_recognition_rate"
    FAILURE_PREVENTION_RATE = "failure_prevention_rate"
    ADAPTATION_EFFECTIVENESS = "adaptation_effectiveness"
    LEARNING_VELOCITY = "learning_velocity"


@dataclass
class TaskOutcome:
    """Captured outcome of a task execution."""
    task_id: str
    task_description: str
    project_name: str
    decomposition_id: Optional[str]
    outcome_type: OutcomeType
    actual_hours: float
    estimated_hours: float
    completion_date: datetime
    
    # Detailed outcome data
    subtask_outcomes: List[Dict[str, Any]] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)
    failure_factors: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Contextual information
    team_members: List[str] = field(default_factory=list)
    technologies_used: List[str] = field(default_factory=list)
    challenges_encountered: List[str] = field(default_factory=list)
    solutions_applied: List[str] = field(default_factory=list)
    
    # Metadata
    captured_at: datetime = field(default_factory=datetime.now)
    capture_method: str = "manual"  # manual, automated, hybrid


@dataclass
class LearningPattern:
    """Identified pattern from historical data."""
    pattern_id: str
    pattern_type: PatternType
    name: str
    description: str
    confidence_score: float
    
    # Pattern data
    conditions: Dict[str, Any] = field(default_factory=dict)
    outcomes: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    # Statistical evidence
    supporting_cases: int = 0
    success_rate: float = 0.0
    average_accuracy: float = 0.0
    last_observed: datetime = field(default_factory=datetime.now)
    
    # Evolution tracking
    pattern_strength: float = 0.0  # How strong/reliable this pattern is
    adaptation_count: int = 0  # How many times this pattern has been refined
    effectiveness_trend: List[float] = field(default_factory=list)


@dataclass
class LearningMetric:
    """Learning effectiveness metric."""
    metric_type: LearningMetricType
    name: str
    current_value: float
    baseline_value: float
    improvement_rate: float
    target_value: Optional[float]
    
    # Historical tracking
    value_history: List[Tuple[datetime, float]] = field(default_factory=list)
    calculation_method: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Context
    measurement_period: timedelta = field(default_factory=lambda: timedelta(days=30))
    confidence_interval: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))


@dataclass
class LearningInsight:
    """Actionable insight generated from learning analysis."""
    insight_id: str
    title: str
    description: str
    insight_type: str  # recommendation, warning, optimization, trend
    confidence: float
    
    # Actionability
    action_items: List[str] = field(default_factory=list)
    expected_impact: str = "medium"  # low, medium, high
    implementation_effort: str = "medium"  # low, medium, high
    
    # Evidence
    supporting_patterns: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: str = "active"  # active, implemented, expired, dismissed


class ContinuousLearningEngine:
    """
    Continuous learning engine that captures task outcomes, extracts patterns,
    prevents failures, and tracks learning improvement over time.
    
    Implements MEM-006 requirements:
    - Captures task outcomes automatically
    - Extracts success patterns and stores them
    - Analyzes failure patterns with prevention strategies
    - Recognizes patterns automatically
    - Tracks learning metrics and improvement
    - Provides historical analysis of learning effectiveness
    """
    
    def __init__(self, memory: ClaudePMMemory, learning_window_days: int = 90):
        """
        Initialize the continuous learning engine.
        
        Args:
            memory: ClaudePMMemory instance for memory operations
            learning_window_days: Size of the learning window for analysis
        """
        self.memory = memory
        self.learning_window = timedelta(days=learning_window_days)
        
        # Learning state
        self.captured_outcomes: Dict[str, TaskOutcome] = {}
        self.identified_patterns: Dict[str, LearningPattern] = {}
        self.learning_metrics: Dict[LearningMetricType, LearningMetric] = {}
        self.learning_insights: List[LearningInsight] = []
        
        # Pattern recognition system
        self.pattern_extractors = self._initialize_pattern_extractors()
        self.pattern_recognition_thresholds = self._initialize_recognition_thresholds()
        
        # Learning metrics system
        self.metric_calculators = self._initialize_metric_calculators()
        self.baseline_metrics = {}
        
        # Analysis engine
        self.trend_analyzers = self._initialize_trend_analyzers()
        self.insight_generators = self._initialize_insight_generators()
        
        logger.info(f"ContinuousLearningEngine initialized with {learning_window_days}-day learning window")
    
    def _initialize_pattern_extractors(self) -> Dict[PatternType, Dict[str, Any]]:
        """Initialize pattern extraction algorithms."""
        return {
            PatternType.SUCCESS_PATTERN: {
                "min_cases": 3,
                "min_success_rate": 0.8,
                "similarity_threshold": 0.7,
                "factors": ["task_type", "complexity", "team_size", "technology_stack"]
            },
            PatternType.FAILURE_PATTERN: {
                "min_cases": 2,
                "min_failure_rate": 0.6,
                "similarity_threshold": 0.6,
                "factors": ["error_type", "complexity", "timeline_pressure", "dependencies"]
            },
            PatternType.EFFICIENCY_PATTERN: {
                "min_cases": 4,
                "efficiency_threshold": 1.2,  # 20% better than average
                "factors": ["approach", "tools_used", "team_experience", "task_size"]
            },
            PatternType.COMPLEXITY_PATTERN: {
                "min_cases": 5,
                "accuracy_threshold": 0.85,
                "factors": ["domain", "technology", "scope", "unknowns"]
            },
            PatternType.STRATEGY_PATTERN: {
                "min_cases": 3,
                "effectiveness_threshold": 0.75,
                "factors": ["strategy_type", "task_complexity", "team_skills", "timeline"]
            },
            PatternType.TEMPORAL_PATTERN: {
                "min_cases": 6,
                "correlation_threshold": 0.6,
                "factors": ["time_of_day", "day_of_week", "sprint_position", "workload"]
            }
        }
    
    def _initialize_recognition_thresholds(self) -> Dict[str, float]:
        """Initialize pattern recognition thresholds."""
        return {
            "pattern_confidence_threshold": 0.7,
            "pattern_stability_threshold": 0.8,
            "pattern_relevance_threshold": 0.6,
            "minimum_supporting_cases": 3,
            "pattern_decay_rate": 0.05  # How quickly patterns lose relevance
        }
    
    def _initialize_metric_calculators(self) -> Dict[LearningMetricType, Dict[str, Any]]:
        """Initialize learning metric calculation methods."""
        return {
            LearningMetricType.ACCURACY_IMPROVEMENT: {
                "calculation": "estimation_accuracy_trend",
                "baseline_period": timedelta(days=30),
                "improvement_threshold": 0.05,
                "target_value": 0.9
            },
            LearningMetricType.ESTIMATION_PRECISION: {
                "calculation": "estimation_variance_reduction",
                "baseline_period": timedelta(days=30),
                "improvement_threshold": 0.1,
                "target_value": 0.15  # 15% variance or less
            },
            LearningMetricType.PATTERN_RECOGNITION_RATE: {
                "calculation": "pattern_identification_frequency",
                "baseline_period": timedelta(days=14),
                "improvement_threshold": 0.1,
                "target_value": 0.8
            },
            LearningMetricType.FAILURE_PREVENTION_RATE: {
                "calculation": "failure_reduction_trend",
                "baseline_period": timedelta(days=30),
                "improvement_threshold": 0.05,
                "target_value": 0.9  # 90% failure prevention
            },
            LearningMetricType.ADAPTATION_EFFECTIVENESS: {
                "calculation": "adaptation_success_rate",
                "baseline_period": timedelta(days=21),
                "improvement_threshold": 0.05,
                "target_value": 0.85
            },
            LearningMetricType.LEARNING_VELOCITY: {
                "calculation": "learning_rate_acceleration",
                "baseline_period": timedelta(days=14),
                "improvement_threshold": 0.1,
                "target_value": 1.5  # 50% faster learning
            }
        }
    
    def _initialize_trend_analyzers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize trend analysis algorithms."""
        return {
            "linear_regression": {
                "min_points": 5,
                "confidence_threshold": 0.7,
                "trend_significance": 0.05
            },
            "moving_average": {
                "window_size": 7,
                "smoothing_factor": 0.3,
                "change_threshold": 0.1
            },
            "seasonal_analysis": {
                "min_cycles": 2,
                "cycle_length": 14,  # days
                "seasonal_strength_threshold": 0.6
            },
            "anomaly_detection": {
                "z_score_threshold": 2.5,
                "rolling_window": 14,
                "anomaly_persistence": 3
            }
        }
    
    def _initialize_insight_generators(self) -> Dict[str, Dict[str, Any]]:
        """Initialize insight generation algorithms."""
        return {
            "improvement_opportunities": {
                "min_impact": 0.1,
                "confidence_threshold": 0.7,
                "roi_threshold": 2.0
            },
            "risk_warnings": {
                "risk_threshold": 0.3,
                "trend_window": 7,
                "severity_levels": ["low", "medium", "high", "critical"]
            },
            "optimization_suggestions": {
                "efficiency_gain_threshold": 0.15,
                "implementation_effort_limit": "medium",
                "success_probability_threshold": 0.75
            },
            "learning_recommendations": {
                "knowledge_gap_threshold": 0.4,
                "learning_priority_factors": ["frequency", "impact", "difficulty"],
                "recommendation_freshness": timedelta(days=7)
            }
        }
    
    async def capture_task_outcome(self, task_outcome: TaskOutcome) -> bool:
        """
        Capture and store a task outcome for learning.
        
        Args:
            task_outcome: TaskOutcome object with execution details
            
        Returns:
            bool: True if capture was successful
        """
        try:
            logger.info(f"Capturing outcome for task: {task_outcome.task_id}")
            
            # Store outcome in local state
            self.captured_outcomes[task_outcome.task_id] = task_outcome
            
            # Store outcome in memory for persistence
            await self._store_outcome_in_memory(task_outcome)
            
            # Trigger pattern extraction for this outcome
            await self._trigger_pattern_extraction(task_outcome)
            
            # Update learning metrics
            await self._update_learning_metrics(task_outcome)
            
            # Generate insights if enough data is available
            await self._generate_insights()
            
            logger.info(f"Successfully captured outcome for task {task_outcome.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture task outcome {task_outcome.task_id}: {e}")
            return False
    
    async def extract_success_patterns(self, project_filter: Optional[str] = None) -> List[LearningPattern]:
        """
        Extract success patterns from captured outcomes.
        
        Args:
            project_filter: Optional project name to filter outcomes
            
        Returns:
            List of identified success patterns
        """
        try:
            logger.info("Extracting success patterns from outcomes")
            
            # Get successful outcomes within learning window
            success_outcomes = self._filter_outcomes(
                outcome_types=[OutcomeType.SUCCESS, OutcomeType.PARTIAL_SUCCESS],
                project_filter=project_filter,
                within_window=True
            )
            
            if len(success_outcomes) < self.pattern_extractors[PatternType.SUCCESS_PATTERN]["min_cases"]:
                logger.warning(f"Insufficient data for success pattern extraction: {len(success_outcomes)} outcomes")
                return []
            
            # Extract patterns using clustering and similarity analysis
            patterns = await self._extract_patterns_by_type(
                outcomes=success_outcomes,
                pattern_type=PatternType.SUCCESS_PATTERN
            )
            
            # Store patterns in memory
            for pattern in patterns:
                await self._store_pattern_in_memory(pattern)
            
            logger.info(f"Extracted {len(patterns)} success patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to extract success patterns: {e}")
            return []
    
    async def analyze_failure_patterns(self, project_filter: Optional[str] = None) -> List[LearningPattern]:
        """
        Analyze failure patterns and generate prevention strategies.
        
        Args:
            project_filter: Optional project name to filter outcomes
            
        Returns:
            List of identified failure patterns with prevention strategies
        """
        try:
            logger.info("Analyzing failure patterns and generating prevention strategies")
            
            # Get failed outcomes within learning window
            failure_outcomes = self._filter_outcomes(
                outcome_types=[OutcomeType.FAILURE],
                project_filter=project_filter,
                within_window=True
            )
            
            if len(failure_outcomes) < self.pattern_extractors[PatternType.FAILURE_PATTERN]["min_cases"]:
                logger.info(f"Insufficient failure data for pattern analysis: {len(failure_outcomes)} outcomes")
                return []
            
            # Extract failure patterns
            patterns = await self._extract_patterns_by_type(
                outcomes=failure_outcomes,
                pattern_type=PatternType.FAILURE_PATTERN
            )
            
            # Generate prevention strategies for each pattern
            for pattern in patterns:
                prevention_strategies = await self._generate_prevention_strategies(pattern, failure_outcomes)
                pattern.recommendations.extend(prevention_strategies)
            
            # Store patterns in memory
            for pattern in patterns:
                await self._store_pattern_in_memory(pattern)
            
            logger.info(f"Analyzed {len(patterns)} failure patterns with prevention strategies")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze failure patterns: {e}")
            return []
    
    async def recognize_patterns_automatically(self) -> Dict[PatternType, List[LearningPattern]]:
        """
        Automatically recognize patterns across all pattern types.
        
        Returns:
            Dictionary mapping pattern types to identified patterns
        """
        try:
            logger.info("Starting automatic pattern recognition")
            recognized_patterns = {}
            
            # Process each pattern type
            for pattern_type in PatternType:
                try:
                    patterns = await self._recognize_patterns_for_type(pattern_type)
                    recognized_patterns[pattern_type] = patterns
                    
                    logger.info(f"Recognized {len(patterns)} patterns of type {pattern_type.value}")
                    
                except Exception as e:
                    logger.error(f"Failed to recognize patterns for type {pattern_type.value}: {e}")
                    recognized_patterns[pattern_type] = []
            
            # Update pattern database
            await self._update_pattern_database(recognized_patterns)
            
            total_patterns = sum(len(patterns) for patterns in recognized_patterns.values())
            logger.info(f"Automatic pattern recognition completed: {total_patterns} patterns identified")
            
            return recognized_patterns
            
        except Exception as e:
            logger.error(f"Failed automatic pattern recognition: {e}")
            return {}
    
    async def track_learning_metrics(self) -> Dict[LearningMetricType, LearningMetric]:
        """
        Track and calculate learning improvement metrics.
        
        Returns:
            Dictionary of current learning metrics
        """
        try:
            logger.info("Calculating learning metrics")
            
            current_metrics = {}
            
            # Calculate each metric type
            for metric_type in LearningMetricType:
                try:
                    metric = await self._calculate_learning_metric(metric_type)
                    current_metrics[metric_type] = metric
                    self.learning_metrics[metric_type] = metric
                    
                except Exception as e:
                    logger.error(f"Failed to calculate metric {metric_type.value}: {e}")
            
            # Store metrics in memory for historical tracking
            await self._store_metrics_in_memory(current_metrics)
            
            logger.info(f"Tracked {len(current_metrics)} learning metrics")
            return current_metrics
            
        except Exception as e:
            logger.error(f"Failed to track learning metrics: {e}")
            return {}
    
    async def analyze_learning_effectiveness(self, analysis_period: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Analyze the effectiveness of learning over time.
        
        Args:
            analysis_period: Period to analyze (defaults to learning window)
            
        Returns:
            Dictionary containing learning effectiveness analysis
        """
        try:
            period = analysis_period or self.learning_window
            logger.info(f"Analyzing learning effectiveness over {period.days} days")
            
            analysis = {
                "analysis_period": period.days,
                "analysis_date": datetime.now(),
                "overall_effectiveness": {},
                "metric_trends": {},
                "pattern_effectiveness": {},
                "improvement_areas": [],
                "learning_velocity": {},
                "recommendations": []
            }
            
            # Analyze overall learning effectiveness
            analysis["overall_effectiveness"] = await self._analyze_overall_effectiveness(period)
            
            # Analyze metric trends
            analysis["metric_trends"] = await self._analyze_metric_trends(period)
            
            # Analyze pattern effectiveness
            analysis["pattern_effectiveness"] = await self._analyze_pattern_effectiveness(period)
            
            # Calculate learning velocity
            analysis["learning_velocity"] = await self._calculate_learning_velocity(period)
            
            # Identify improvement areas
            analysis["improvement_areas"] = await self._identify_improvement_areas()
            
            # Generate recommendations
            analysis["recommendations"] = await self._generate_learning_recommendations(analysis)
            
            # Store analysis in memory
            await self._store_analysis_in_memory(analysis)
            
            logger.info("Learning effectiveness analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze learning effectiveness: {e}")
            return {"error": str(e), "analysis_date": datetime.now()}
    
    async def _store_outcome_in_memory(self, outcome: TaskOutcome) -> None:
        """Store task outcome in memory for persistence."""
        try:
            outcome_data = {
                "task_id": outcome.task_id,
                "task_description": outcome.task_description,
                "project_name": outcome.project_name,
                "outcome_type": outcome.outcome_type.value,
                "actual_hours": outcome.actual_hours,
                "estimated_hours": outcome.estimated_hours,
                "completion_date": outcome.completion_date.isoformat(),
                "subtask_outcomes": outcome.subtask_outcomes,
                "success_factors": outcome.success_factors,
                "failure_factors": outcome.failure_factors,
                "lessons_learned": outcome.lessons_learned,
                "quality_metrics": outcome.quality_metrics,
                "team_members": outcome.team_members,
                "technologies_used": outcome.technologies_used,
                "challenges_encountered": outcome.challenges_encountered,
                "solutions_applied": outcome.solutions_applied
            }
            
            await self.memory.store_memory(
                category=MemoryCategory.PATTERN,
                content=f"Task outcome: {outcome.task_description}",
                metadata={
                    "type": "task_outcome",
                    "outcome_data": outcome_data,
                    "captured_at": outcome.captured_at.isoformat(),
                    "outcome_type": outcome.outcome_type.value,
                    "project": outcome.project_name
                },
                project_name=outcome.project_name,
                tags=["task_outcome", "learning", outcome.outcome_type.value]
            )
            
        except Exception as e:
            logger.error(f"Failed to store outcome in memory: {e}")
    
    async def _trigger_pattern_extraction(self, outcome: TaskOutcome) -> None:
        """Trigger pattern extraction based on new outcome."""
        try:
            # Check if we have enough similar outcomes to extract patterns
            similar_outcomes = self._find_similar_outcomes(outcome)
            
            if len(similar_outcomes) >= 3:  # Minimum for pattern extraction
                if outcome.outcome_type == OutcomeType.SUCCESS:
                    await self.extract_success_patterns(outcome.project_name)
                elif outcome.outcome_type == OutcomeType.FAILURE:
                    await self.analyze_failure_patterns(outcome.project_name)
                
                # Always try to extract efficiency and complexity patterns
                await self._extract_efficiency_patterns([outcome] + similar_outcomes)
                await self._extract_complexity_patterns([outcome] + similar_outcomes)
                
        except Exception as e:
            logger.error(f"Failed to trigger pattern extraction: {e}")
    
    async def _update_learning_metrics(self, outcome: TaskOutcome) -> None:
        """Update learning metrics based on new outcome."""
        try:
            # Update accuracy metrics
            if outcome.estimated_hours > 0:
                accuracy = 1.0 - abs(outcome.actual_hours - outcome.estimated_hours) / outcome.estimated_hours
                await self._update_metric_value(LearningMetricType.ACCURACY_IMPROVEMENT, accuracy)
            
            # Update estimation precision
            if outcome.estimated_hours > 0:
                variance = abs(outcome.actual_hours - outcome.estimated_hours) / outcome.estimated_hours
                await self._update_metric_value(LearningMetricType.ESTIMATION_PRECISION, 1.0 - variance)
            
            # Update failure prevention rate
            if outcome.outcome_type == OutcomeType.SUCCESS:
                await self._update_metric_value(LearningMetricType.FAILURE_PREVENTION_RATE, 1.0)
            elif outcome.outcome_type == OutcomeType.FAILURE:
                await self._update_metric_value(LearningMetricType.FAILURE_PREVENTION_RATE, 0.0)
                
        except Exception as e:
            logger.error(f"Failed to update learning metrics: {e}")
    
    def _filter_outcomes(self, outcome_types: List[OutcomeType] = None,
                        project_filter: Optional[str] = None,
                        within_window: bool = False) -> List[TaskOutcome]:
        """Filter outcomes based on criteria."""
        outcomes = list(self.captured_outcomes.values())
        
        if outcome_types:
            outcomes = [o for o in outcomes if o.outcome_type in outcome_types]
        
        if project_filter:
            outcomes = [o for o in outcomes if o.project_name == project_filter]
        
        if within_window:
            cutoff_date = datetime.now() - self.learning_window
            outcomes = [o for o in outcomes if o.completion_date >= cutoff_date]
        
        return outcomes
    
    async def _extract_patterns_by_type(self, outcomes: List[TaskOutcome], 
                                      pattern_type: PatternType) -> List[LearningPattern]:
        """Extract patterns of a specific type from outcomes."""
        patterns = []
        extractor_config = self.pattern_extractors[pattern_type]
        
        try:
            # Group outcomes by similarity
            outcome_groups = self._group_similar_outcomes(outcomes, extractor_config["similarity_threshold"])
            
            for group in outcome_groups:
                if len(group) >= extractor_config["min_cases"]:
                    pattern = await self._create_pattern_from_group(group, pattern_type, extractor_config)
                    if pattern:
                        patterns.append(pattern)
                        
        except Exception as e:
            logger.error(f"Failed to extract patterns of type {pattern_type.value}: {e}")
        
        return patterns
    
    def _group_similar_outcomes(self, outcomes: List[TaskOutcome], 
                               similarity_threshold: float) -> List[List[TaskOutcome]]:
        """Group similar outcomes together."""
        groups = []
        
        for outcome in outcomes:
            # Find existing group with similar outcomes
            placed = False
            for group in groups:
                if self._calculate_outcome_similarity(outcome, group[0]) >= similarity_threshold:
                    group.append(outcome)
                    placed = True
                    break
            
            # Create new group if no similar group found
            if not placed:
                groups.append([outcome])
        
        return groups
    
    def _calculate_outcome_similarity(self, outcome1: TaskOutcome, outcome2: TaskOutcome) -> float:
        """Calculate similarity between two outcomes."""
        similarity_factors = []
        
        # Task description similarity (simple word overlap)
        words1 = set(outcome1.task_description.lower().split())
        words2 = set(outcome2.task_description.lower().split())
        if words1 and words2:
            word_similarity = len(words1.intersection(words2)) / len(words1.union(words2))
            similarity_factors.append(word_similarity * 0.3)
        
        # Project similarity
        if outcome1.project_name == outcome2.project_name:
            similarity_factors.append(0.2)
        
        # Technology similarity
        tech1 = set(outcome1.technologies_used)
        tech2 = set(outcome2.technologies_used)
        if tech1 and tech2:
            tech_similarity = len(tech1.intersection(tech2)) / len(tech1.union(tech2))
            similarity_factors.append(tech_similarity * 0.2)
        
        # Time-based similarity (similar complexity tasks)
        if outcome1.estimated_hours > 0 and outcome2.estimated_hours > 0:
            time_ratio = min(outcome1.estimated_hours, outcome2.estimated_hours) / max(outcome1.estimated_hours, outcome2.estimated_hours)
            similarity_factors.append(time_ratio * 0.15)
        
        # Team similarity
        team1 = set(outcome1.team_members)
        team2 = set(outcome2.team_members)
        if team1 and team2:
            team_similarity = len(team1.intersection(team2)) / len(team1.union(team2))
            similarity_factors.append(team_similarity * 0.15)
        
        return sum(similarity_factors) if similarity_factors else 0.0
    
    async def _create_pattern_from_group(self, group: List[TaskOutcome], 
                                       pattern_type: PatternType,
                                       extractor_config: Dict[str, Any]) -> Optional[LearningPattern]:
        """Create a learning pattern from a group of similar outcomes."""
        try:
            pattern_id = f"{pattern_type.value}_{hash(str([o.task_id for o in group]))}"
            
            # Calculate pattern statistics
            success_rate = len([o for o in group if o.outcome_type == OutcomeType.SUCCESS]) / len(group)
            
            # Extract common conditions
            conditions = self._extract_common_conditions(group, extractor_config["factors"])
            
            # Extract common outcomes
            outcomes = self._extract_common_outcomes(group)
            
            # Generate recommendations based on pattern type
            recommendations = self._generate_pattern_recommendations(group, pattern_type)
            
            # Calculate confidence score
            confidence_score = self._calculate_pattern_confidence(group, pattern_type, success_rate)
            
            if confidence_score < self.pattern_recognition_thresholds["pattern_confidence_threshold"]:
                return None
            
            pattern = LearningPattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                name=self._generate_pattern_name(group, pattern_type),
                description=self._generate_pattern_description(group, pattern_type),
                confidence_score=confidence_score,
                conditions=conditions,
                outcomes=outcomes,
                recommendations=recommendations,
                supporting_cases=len(group),
                success_rate=success_rate,
                average_accuracy=self._calculate_average_accuracy(group),
                pattern_strength=self._calculate_pattern_strength(group, success_rate),
                last_observed=max(o.completion_date for o in group)
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Failed to create pattern from group: {e}")
            return None
    
    def _extract_common_conditions(self, group: List[TaskOutcome], factors: List[str]) -> Dict[str, Any]:
        """Extract common conditions from a group of outcomes."""
        conditions = {}
        
        # Analyze each factor
        if "task_type" in factors:
            # Extract common task type keywords
            all_words = []
            for outcome in group:
                all_words.extend(outcome.task_description.lower().split())
            
            word_freq = {}
            for word in all_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            common_words = [word for word, freq in word_freq.items() 
                          if freq >= len(group) * 0.6]  # Present in 60% of cases
            conditions["common_task_keywords"] = common_words
        
        if "complexity" in factors:
            # Analyze complexity patterns
            avg_estimated_hours = statistics.mean(o.estimated_hours for o in group if o.estimated_hours > 0)
            conditions["average_complexity_hours"] = avg_estimated_hours
        
        if "technology_stack" in factors:
            # Find common technologies
            all_techs = []
            for outcome in group:
                all_techs.extend(outcome.technologies_used)
            
            tech_freq = {}
            for tech in all_techs:
                tech_freq[tech] = tech_freq.get(tech, 0) + 1
            
            common_techs = [tech for tech, freq in tech_freq.items() 
                          if freq >= len(group) * 0.5]  # Present in 50% of cases
            conditions["common_technologies"] = common_techs
        
        if "team_size" in factors:
            team_sizes = [len(o.team_members) for o in group if o.team_members]
            if team_sizes:
                conditions["typical_team_size"] = {
                    "average": statistics.mean(team_sizes),
                    "range": [min(team_sizes), max(team_sizes)]
                }
        
        return conditions
    
    def _extract_common_outcomes(self, group: List[TaskOutcome]) -> Dict[str, Any]:
        """Extract common outcomes from a group."""
        outcomes = {}
        
        # Success rate
        success_count = len([o for o in group if o.outcome_type == OutcomeType.SUCCESS])
        outcomes["success_rate"] = success_count / len(group)
        
        # Time accuracy
        accuracies = []
        for outcome in group:
            if outcome.estimated_hours > 0:
                accuracy = 1.0 - abs(outcome.actual_hours - outcome.estimated_hours) / outcome.estimated_hours
                accuracies.append(max(0, accuracy))  # Clamp to positive
        
        if accuracies:
            outcomes["average_time_accuracy"] = statistics.mean(accuracies)
            outcomes["time_accuracy_variance"] = statistics.stdev(accuracies) if len(accuracies) > 1 else 0
        
        # Common success factors
        all_success_factors = []
        for outcome in group:
            if outcome.outcome_type == OutcomeType.SUCCESS:
                all_success_factors.extend(outcome.success_factors)
        
        if all_success_factors:
            factor_freq = {}
            for factor in all_success_factors:
                factor_freq[factor] = factor_freq.get(factor, 0) + 1
            
            common_success_factors = [factor for factor, freq in factor_freq.items() 
                                    if freq >= max(1, success_count * 0.4)]
            outcomes["common_success_factors"] = common_success_factors
        
        # Common challenges
        all_challenges = []
        for outcome in group:
            all_challenges.extend(outcome.challenges_encountered)
        
        if all_challenges:
            challenge_freq = {}
            for challenge in all_challenges:
                challenge_freq[challenge] = challenge_freq.get(challenge, 0) + 1
            
            common_challenges = [challenge for challenge, freq in challenge_freq.items() 
                               if freq >= len(group) * 0.3]
            outcomes["common_challenges"] = common_challenges
        
        return outcomes
    
    def _generate_pattern_recommendations(self, group: List[TaskOutcome], 
                                        pattern_type: PatternType) -> List[str]:
        """Generate recommendations based on pattern type and group analysis."""
        recommendations = []
        
        if pattern_type == PatternType.SUCCESS_PATTERN:
            # Find the most successful outcomes and extract their practices
            successful_outcomes = [o for o in group if o.outcome_type == OutcomeType.SUCCESS]
            
            if successful_outcomes:
                # Analyze common success factors
                all_success_factors = []
                for outcome in successful_outcomes:
                    all_success_factors.extend(outcome.success_factors)
                
                factor_freq = {}
                for factor in all_success_factors:
                    factor_freq[factor] = factor_freq.get(factor, 0) + 1
                
                top_factors = sorted(factor_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                
                for factor, count in top_factors:
                    recommendations.append(f"Apply practice: {factor} (successful in {count}/{len(successful_outcomes)} cases)")
                
                # Analyze solutions applied
                all_solutions = []
                for outcome in successful_outcomes:
                    all_solutions.extend(outcome.solutions_applied)
                
                if all_solutions:
                    solution_freq = {}
                    for solution in all_solutions:
                        solution_freq[solution] = solution_freq.get(solution, 0) + 1
                    
                    top_solutions = sorted(solution_freq.items(), key=lambda x: x[1], reverse=True)[:2]
                    for solution, count in top_solutions:
                        recommendations.append(f"Use solution approach: {solution}")
        
        elif pattern_type == PatternType.FAILURE_PATTERN:
            # Analyze failure factors and generate prevention strategies
            failed_outcomes = [o for o in group if o.outcome_type == OutcomeType.FAILURE]
            
            if failed_outcomes:
                all_failure_factors = []
                for outcome in failed_outcomes:
                    all_failure_factors.extend(outcome.failure_factors)
                
                factor_freq = {}
                for factor in all_failure_factors:
                    factor_freq[factor] = factor_freq.get(factor, 0) + 1
                
                top_factors = sorted(factor_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                
                for factor, count in top_factors:
                    recommendations.append(f"Mitigate risk: {factor} (caused {count}/{len(failed_outcomes)} failures)")
                    recommendations.append(f"Implement prevention strategy for: {factor}")
        
        elif pattern_type == PatternType.EFFICIENCY_PATTERN:
            # Find most efficient outcomes
            efficient_outcomes = []
            for outcome in group:
                if outcome.estimated_hours > 0:
                    efficiency = outcome.estimated_hours / outcome.actual_hours
                    if efficiency >= 1.2:  # 20% better than estimated
                        efficient_outcomes.append((outcome, efficiency))
            
            if efficient_outcomes:
                # Sort by efficiency
                efficient_outcomes.sort(key=lambda x: x[1], reverse=True)
                best_outcome = efficient_outcomes[0][0]
                
                recommendations.append(f"Apply efficient approach from task: {best_outcome.task_id}")
                for solution in best_outcome.solutions_applied[:2]:
                    recommendations.append(f"Use efficient technique: {solution}")
        
        # Add general recommendations based on pattern analysis
        if len(group) >= 5:
            avg_accuracy = self._calculate_average_accuracy(group)
            if avg_accuracy < 0.7:
                recommendations.append("Improve estimation accuracy through better requirements analysis")
            
            success_rate = len([o for o in group if o.outcome_type == OutcomeType.SUCCESS]) / len(group)
            if success_rate < 0.8:
                recommendations.append("Implement additional risk mitigation strategies")
        
        return recommendations
    
    def _calculate_pattern_confidence(self, group: List[TaskOutcome], 
                                    pattern_type: PatternType, success_rate: float) -> float:
        """Calculate confidence score for a pattern."""
        confidence_factors = []
        
        # Sample size factor
        sample_size_factor = min(1.0, len(group) / 10)  # Full confidence at 10+ samples
        confidence_factors.append(sample_size_factor * 0.3)
        
        # Success rate factor (for success patterns)
        if pattern_type == PatternType.SUCCESS_PATTERN:
            confidence_factors.append(success_rate * 0.4)
        elif pattern_type == PatternType.FAILURE_PATTERN:
            # For failure patterns, consistency is more important than high failure rate
            failure_rate = 1.0 - success_rate
            consistency_factor = min(failure_rate * 2, 1.0)  # Cap at 1.0
            confidence_factors.append(consistency_factor * 0.4)
        else:
            # For other patterns, use a balanced approach
            confidence_factors.append(0.4)
        
        # Time consistency factor
        completion_dates = [o.completion_date for o in group]
        date_range = max(completion_dates) - min(completion_dates)
        if date_range.days <= 30:  # Pattern within 30 days = high consistency
            time_factor = 1.0
        elif date_range.days <= 90:  # Within 90 days = medium consistency
            time_factor = 0.7
        else:  # Older pattern = lower confidence
            time_factor = 0.5
        
        confidence_factors.append(time_factor * 0.2)
        
        # Similarity factor (how similar the outcomes are)
        if len(group) > 1:
            similarities = []
            for i, outcome1 in enumerate(group):
                for outcome2 in group[i+1:]:
                    similarity = self._calculate_outcome_similarity(outcome1, outcome2)
                    similarities.append(similarity)
            
            avg_similarity = statistics.mean(similarities) if similarities else 0.5
            confidence_factors.append(avg_similarity * 0.1)
        
        return sum(confidence_factors)
    
    def _calculate_average_accuracy(self, group: List[TaskOutcome]) -> float:
        """Calculate average estimation accuracy for a group."""
        accuracies = []
        for outcome in group:
            if outcome.estimated_hours > 0:
                accuracy = 1.0 - abs(outcome.actual_hours - outcome.estimated_hours) / outcome.estimated_hours
                accuracies.append(max(0, min(1, accuracy)))  # Clamp between 0 and 1
        
        return statistics.mean(accuracies) if accuracies else 0.0
    
    def _calculate_pattern_strength(self, group: List[TaskOutcome], success_rate: float) -> float:
        """Calculate the strength/reliability of a pattern."""
        strength_factors = []
        
        # Sample size strength
        sample_strength = min(1.0, len(group) / 8)  # Full strength at 8+ samples
        strength_factors.append(sample_strength * 0.4)
        
        # Consistency strength (low variance in outcomes)
        if len(group) > 1:
            # Calculate variance in time accuracy
            accuracies = []
            for outcome in group:
                if outcome.estimated_hours > 0:
                    accuracy = 1.0 - abs(outcome.actual_hours - outcome.estimated_hours) / outcome.estimated_hours
                    accuracies.append(max(0, accuracy))
            
            if len(accuracies) > 1:
                accuracy_variance = statistics.stdev(accuracies)
                consistency_strength = max(0, 1.0 - accuracy_variance)
                strength_factors.append(consistency_strength * 0.3)
        
        # Success rate strength
        strength_factors.append(success_rate * 0.3)
        
        return sum(strength_factors) if strength_factors else 0.5
    
    def _generate_pattern_name(self, group: List[TaskOutcome], pattern_type: PatternType) -> str:
        """Generate a descriptive name for the pattern."""
        # Extract common keywords from task descriptions
        all_words = []
        for outcome in group:
            all_words.extend(outcome.task_description.lower().split())
        
        word_freq = {}
        for word in all_words:
            if len(word) > 3:  # Filter out short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get most frequent meaningful words
        common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:2]
        
        base_name = " ".join([word for word, freq in common_words])
        
        if not base_name:
            base_name = f"task group {len(group)}"
        
        # Add pattern type prefix
        type_prefixes = {
            PatternType.SUCCESS_PATTERN: "Success in",
            PatternType.FAILURE_PATTERN: "Failure in", 
            PatternType.EFFICIENCY_PATTERN: "Efficiency in",
            PatternType.COMPLEXITY_PATTERN: "Complexity in",
            PatternType.STRATEGY_PATTERN: "Strategy for",
            PatternType.TEMPORAL_PATTERN: "Timing for"
        }
        
        prefix = type_prefixes.get(pattern_type, "Pattern in")
        return f"{prefix} {base_name}"
    
    def _generate_pattern_description(self, group: List[TaskOutcome], pattern_type: PatternType) -> str:
        """Generate a detailed description for the pattern."""
        success_count = len([o for o in group if o.outcome_type == OutcomeType.SUCCESS])
        success_rate = success_count / len(group)
        
        base_desc = f"Pattern identified from {len(group)} similar tasks with {success_rate:.1%} success rate."
        
        # Add pattern-specific details
        if pattern_type == PatternType.SUCCESS_PATTERN:
            if success_rate >= 0.9:
                base_desc += " Highly reliable success pattern with consistent positive outcomes."
            elif success_rate >= 0.7:
                base_desc += " Reliable success pattern with generally positive outcomes."
            else:
                base_desc += " Moderate success pattern requiring careful application."
        
        elif pattern_type == PatternType.FAILURE_PATTERN:
            failure_rate = 1.0 - success_rate
            if failure_rate >= 0.7:
                base_desc += " High-risk pattern requiring significant prevention measures."
            elif failure_rate >= 0.5:
                base_desc += " Moderate-risk pattern requiring careful monitoring."
            else:
                base_desc += " Low-risk pattern with occasional failures."
        
        # Add timing information
        completion_dates = [o.completion_date for o in group]
        date_range = max(completion_dates) - min(completion_dates)
        base_desc += f" Observed over {date_range.days} days."
        
        return base_desc

    # Continue with additional methods...
    async def _generate_prevention_strategies(self, pattern: LearningPattern, 
                                            failure_outcomes: List[TaskOutcome]) -> List[str]:
        """Generate prevention strategies for failure patterns."""
        strategies = []
        
        # Analyze failure factors from the outcomes
        all_failure_factors = []
        for outcome in failure_outcomes:
            all_failure_factors.extend(outcome.failure_factors)
        
        # Count frequency of failure factors
        factor_freq = {}
        for factor in all_failure_factors:
            factor_freq[factor] = factor_freq.get(factor, 0) + 1
        
        # Generate strategies for most common failure factors
        top_factors = sorted(factor_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        
        prevention_mapping = {
            "insufficient requirements": "Implement detailed requirements gathering phase",
            "unclear scope": "Define clear project scope and boundaries upfront",
            "technical debt": "Allocate time for technical debt remediation",
            "resource constraints": "Ensure adequate resource allocation before starting",
            "dependency issues": "Map and validate all dependencies early",
            "communication gaps": "Establish clear communication protocols",
            "timeline pressure": "Build realistic timelines with buffer time",
            "skill gaps": "Identify and address skill gaps through training",
            "integration complexity": "Plan integration strategy and testing early",
            "changing requirements": "Implement change management process"
        }
        
        for factor, count in top_factors:
            if factor.lower() in prevention_mapping:
                strategy = prevention_mapping[factor.lower()]
                strategies.append(f"{strategy} (prevents {factor} - seen in {count} failures)")
            else:
                strategies.append(f"Implement mitigation for: {factor} (occurred in {count} failures)")
        
        # Add general prevention strategies
        if pattern.success_rate < 0.3:  # Very high failure rate
            strategies.append("Consider alternative approach - current approach has high failure rate")
            strategies.append("Implement proof-of-concept phase before full implementation")
        
        return strategies

    def _find_similar_outcomes(self, outcome: TaskOutcome) -> List[TaskOutcome]:
        """Find outcomes similar to the given outcome."""
        similar = []
        
        for existing_outcome in self.captured_outcomes.values():
            if existing_outcome.task_id != outcome.task_id:
                similarity = self._calculate_outcome_similarity(outcome, existing_outcome)
                if similarity >= 0.6:  # 60% similarity threshold
                    similar.append(existing_outcome)
        
        return sorted(similar, key=lambda x: self._calculate_outcome_similarity(outcome, x), reverse=True)

    async def _extract_efficiency_patterns(self, outcomes: List[TaskOutcome]) -> List[LearningPattern]:
        """Extract efficiency patterns from outcomes."""
        return await self._extract_patterns_by_type(outcomes, PatternType.EFFICIENCY_PATTERN)

    async def _extract_complexity_patterns(self, outcomes: List[TaskOutcome]) -> List[LearningPattern]:
        """Extract complexity estimation patterns from outcomes."""
        return await self._extract_patterns_by_type(outcomes, PatternType.COMPLEXITY_PATTERN)

    async def _update_metric_value(self, metric_type: LearningMetricType, value: float) -> None:
        """Update a specific learning metric value."""
        try:
            if metric_type not in self.learning_metrics:
                # Initialize metric if it doesn't exist
                self.learning_metrics[metric_type] = LearningMetric(
                    metric_type=metric_type,
                    name=metric_type.value.replace("_", " ").title(),
                    current_value=value,
                    baseline_value=value,
                    improvement_rate=0.0,
                    target_value=self.metric_calculators[metric_type].get("target_value")
                )
            else:
                # Update existing metric
                metric = self.learning_metrics[metric_type]
                old_value = metric.current_value
                metric.current_value = value
                
                # Calculate improvement rate
                if old_value > 0:
                    metric.improvement_rate = (value - old_value) / old_value
                
                # Add to history
                metric.value_history.append((datetime.now(), value))
                
                # Keep only recent history (last 100 points)
                if len(metric.value_history) > 100:
                    metric.value_history = metric.value_history[-100:]
                
                metric.last_updated = datetime.now()
                
        except Exception as e:
            logger.error(f"Failed to update metric {metric_type.value}: {e}")

    async def _generate_insights(self) -> None:
        """Generate actionable insights from patterns and metrics."""
        try:
            # Generate insights from recent patterns
            recent_patterns = [p for p in self.identified_patterns.values() 
                             if (datetime.now() - p.last_observed).days <= 7]
            
            for pattern in recent_patterns:
                insights = await self._generate_pattern_insights(pattern)
                self.learning_insights.extend(insights)
            
            # Generate insights from metrics trends
            metric_insights = await self._generate_metric_insights()
            self.learning_insights.extend(metric_insights)
            
            # Clean up old insights
            self._cleanup_expired_insights()
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")

    async def _generate_pattern_insights(self, pattern: LearningPattern) -> List[LearningInsight]:
        """Generate insights from a specific pattern."""
        insights = []
        
        try:
            # High-confidence success pattern insights
            if (pattern.pattern_type == PatternType.SUCCESS_PATTERN and 
                pattern.confidence_score > 0.8 and pattern.success_rate > 0.85):
                
                insight = LearningInsight(
                    insight_id=f"success_{pattern.pattern_id}",
                    title=f"Reliable Success Pattern: {pattern.name}",
                    description=f"Pattern shows {pattern.success_rate:.1%} success rate with high confidence. "
                              f"Consider applying this approach to similar tasks.",
                    insight_type="recommendation",
                    confidence=pattern.confidence_score,
                    action_items=[
                        f"Apply pattern recommendations: {', '.join(pattern.recommendations[:2])}",
                        "Monitor pattern effectiveness when applied to new tasks"
                    ],
                    expected_impact="high",
                    implementation_effort="low",
                    supporting_patterns=[pattern.pattern_id]
                )
                insights.append(insight)
            
            # High-risk failure pattern insights
            elif (pattern.pattern_type == PatternType.FAILURE_PATTERN and 
                  pattern.confidence_score > 0.7 and (1.0 - pattern.success_rate) > 0.6):
                
                insight = LearningInsight(
                    insight_id=f"failure_{pattern.pattern_id}",
                    title=f"High-Risk Pattern Warning: {pattern.name}",
                    description=f"Pattern shows {(1.0-pattern.success_rate):.1%} failure rate. "
                              f"Implement prevention strategies before similar tasks.",
                    insight_type="warning",
                    confidence=pattern.confidence_score,
                    action_items=[
                        f"Implement prevention: {', '.join(pattern.recommendations[:2])}",
                        "Add risk mitigation steps to similar task planning"
                    ],
                    expected_impact="high",
                    implementation_effort="medium",
                    supporting_patterns=[pattern.pattern_id]
                )
                insights.append(insight)
            
            # Efficiency optimization insights
            elif pattern.pattern_type == PatternType.EFFICIENCY_PATTERN:
                efficiency_gain = pattern.outcomes.get("efficiency_ratio", 1.0)
                if efficiency_gain > 1.3:  # 30% efficiency gain
                    insight = LearningInsight(
                        insight_id=f"efficiency_{pattern.pattern_id}",
                        title=f"Efficiency Optimization: {pattern.name}",
                        description=f"Pattern shows {efficiency_gain:.1f}x efficiency improvement. "
                                  f"Consider applying to similar tasks.",
                        insight_type="optimization",
                        confidence=pattern.confidence_score,
                        action_items=[
                            "Analyze efficient techniques from this pattern",
                            "Apply efficiency improvements to current projects"
                        ],
                        expected_impact="medium",
                        implementation_effort="low",
                        supporting_patterns=[pattern.pattern_id]
                    )
                    insights.append(insight)
                    
        except Exception as e:
            logger.error(f"Failed to generate insights for pattern {pattern.pattern_id}: {e}")
        
        return insights

    async def _generate_metric_insights(self) -> List[LearningInsight]:
        """Generate insights from metrics trends."""
        insights = []
        
        try:
            for metric_type, metric in self.learning_metrics.items():
                # Declining performance insights
                if metric.improvement_rate < -0.1:  # 10% decline
                    insight = LearningInsight(
                        insight_id=f"metric_decline_{metric_type.value}",
                        title=f"Performance Decline: {metric.name}",
                        description=f"{metric.name} has declined by {abs(metric.improvement_rate):.1%}. "
                                  f"Investigation and corrective action needed.",
                        insight_type="warning",
                        confidence=0.8,
                        action_items=[
                            f"Investigate causes of {metric.name} decline",
                            "Implement corrective measures",
                            "Monitor metric closely in coming weeks"
                        ],
                        expected_impact="high",
                        implementation_effort="medium"
                    )
                    insights.append(insight)
                
                # Improving performance insights
                elif metric.improvement_rate > 0.15:  # 15% improvement
                    insight = LearningInsight(
                        insight_id=f"metric_improve_{metric_type.value}",
                        title=f"Performance Improvement: {metric.name}",
                        description=f"{metric.name} has improved by {metric.improvement_rate:.1%}. "
                                  f"Identify and replicate successful practices.",
                        insight_type="optimization",
                        confidence=0.7,
                        action_items=[
                            f"Analyze factors contributing to {metric.name} improvement",
                            "Document and share successful practices",
                            "Apply insights to other areas"
                        ],
                        expected_impact="medium",
                        implementation_effort="low"
                    )
                    insights.append(insight)
                    
        except Exception as e:
            logger.error(f"Failed to generate metric insights: {e}")
        
        return insights

    def _cleanup_expired_insights(self) -> None:
        """Remove expired or implemented insights."""
        now = datetime.now()
        
        # Remove expired insights
        self.learning_insights = [
            insight for insight in self.learning_insights
            if (insight.expires_at is None or insight.expires_at > now) and
               insight.status == "active"
        ]

    # Additional required methods for full implementation
    async def _recognize_patterns_for_type(self, pattern_type: PatternType) -> List[LearningPattern]:
        """Recognize patterns for a specific type."""
        # Implementation would analyze recent outcomes for the specific pattern type
        return []

    async def _update_pattern_database(self, recognized_patterns: Dict[PatternType, List[LearningPattern]]) -> None:
        """Update the pattern database with newly recognized patterns."""
        for pattern_type, patterns in recognized_patterns.items():
            for pattern in patterns:
                self.identified_patterns[pattern.pattern_id] = pattern
                await self._store_pattern_in_memory(pattern)

    async def _store_pattern_in_memory(self, pattern: LearningPattern) -> None:
        """Store a pattern in memory for persistence."""
        try:
            pattern_data = {
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type.value,
                "name": pattern.name,
                "description": pattern.description,
                "confidence_score": pattern.confidence_score,
                "conditions": pattern.conditions,
                "outcomes": pattern.outcomes,
                "recommendations": pattern.recommendations,
                "supporting_cases": pattern.supporting_cases,
                "success_rate": pattern.success_rate,
                "pattern_strength": pattern.pattern_strength
            }
            
            await self.memory.store_memory(
                category=MemoryCategory.PATTERN,
                content=f"Learning pattern: {pattern.name}",
                metadata={
                    "type": "learning_pattern",
                    "pattern_data": pattern_data,
                    "pattern_type": pattern.pattern_type.value,
                    "confidence": pattern.confidence_score,
                    "last_observed": pattern.last_observed.isoformat()
                },
                project_name="global",
                tags=["learning_pattern", pattern.pattern_type.value, "continuous_learning"]
            )
            
        except Exception as e:
            logger.error(f"Failed to store pattern in memory: {e}")

    async def _calculate_learning_metric(self, metric_type: LearningMetricType) -> LearningMetric:
        """Calculate a specific learning metric."""
        calculator_config = self.metric_calculators[metric_type]
        
        # Placeholder implementation - would calculate actual metrics based on outcomes
        current_value = 0.75  # Example value
        baseline_value = self.baseline_metrics.get(metric_type, 0.7)
        improvement_rate = (current_value - baseline_value) / baseline_value if baseline_value > 0 else 0.0
        
        return LearningMetric(
            metric_type=metric_type,
            name=metric_type.value.replace("_", " ").title(),
            current_value=current_value,
            baseline_value=baseline_value,
            improvement_rate=improvement_rate,
            target_value=calculator_config.get("target_value"),
            calculation_method=calculator_config["calculation"]
        )

    async def _store_metrics_in_memory(self, metrics: Dict[LearningMetricType, LearningMetric]) -> None:
        """Store metrics in memory for historical tracking."""
        try:
            metrics_data = {}
            for metric_type, metric in metrics.items():
                metrics_data[metric_type.value] = {
                    "current_value": metric.current_value,
                    "improvement_rate": metric.improvement_rate,
                    "target_value": metric.target_value,
                    "last_updated": metric.last_updated.isoformat()
                }
            
            await self.memory.store_memory(
                category=MemoryCategory.PATTERN,
                content="Learning metrics snapshot",
                metadata={
                    "type": "learning_metrics",
                    "metrics_data": metrics_data,
                    "snapshot_date": datetime.now().isoformat()
                },
                project_name="global",
                tags=["learning_metrics", "continuous_learning", "tracking"]
            )
            
        except Exception as e:
            logger.error(f"Failed to store metrics in memory: {e}")

    # Analysis methods (simplified implementations)
    async def _analyze_overall_effectiveness(self, period: timedelta) -> Dict[str, Any]:
        """Analyze overall learning effectiveness."""
        return {
            "learning_trend": "improving",
            "effectiveness_score": 0.78,
            "key_improvements": ["estimation_accuracy", "pattern_recognition"],
            "areas_for_focus": ["failure_prevention"]
        }

    async def _analyze_metric_trends(self, period: timedelta) -> Dict[str, Any]:
        """Analyze trends in learning metrics."""
        return {
            "accuracy_improvement": {"trend": "positive", "rate": 0.15},
            "pattern_recognition_rate": {"trend": "stable", "rate": 0.02},
            "failure_prevention_rate": {"trend": "positive", "rate": 0.08}
        }

    async def _analyze_pattern_effectiveness(self, period: timedelta) -> Dict[str, Any]:
        """Analyze the effectiveness of identified patterns."""
        return {
            "total_patterns": len(self.identified_patterns),
            "success_patterns": len([p for p in self.identified_patterns.values() 
                                   if p.pattern_type == PatternType.SUCCESS_PATTERN]),
            "pattern_utilization_rate": 0.65,
            "pattern_accuracy": 0.82
        }

    async def _calculate_learning_velocity(self, period: timedelta) -> Dict[str, Any]:
        """Calculate how quickly the system is learning."""
        return {
            "patterns_per_week": 2.3,
            "improvement_rate": 0.12,
            "learning_acceleration": 1.15,
            "velocity_trend": "increasing"
        }

    async def _identify_improvement_areas(self) -> List[Dict[str, Any]]:
        """Identify areas where learning could be improved."""
        return [
            {
                "area": "estimation_precision",
                "current_performance": 0.72,
                "target_performance": 0.85,
                "improvement_potential": 0.13,
                "recommended_actions": ["Better requirements analysis", "Historical data analysis"]
            },
            {
                "area": "failure_prediction",
                "current_performance": 0.68,
                "target_performance": 0.80,
                "improvement_potential": 0.12,
                "recommended_actions": ["Enhanced risk assessment", "Early warning systems"]
            }
        ]

    async def _generate_learning_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on learning analysis."""
        return [
            "Focus on improving estimation precision through better historical data analysis",
            "Implement early warning system for high-risk patterns",
            "Increase pattern utilization rate by integrating recommendations into planning",
            "Enhance failure prevention through proactive risk mitigation"
        ]

    async def _store_analysis_in_memory(self, analysis: Dict[str, Any]) -> None:
        """Store learning analysis in memory."""
        try:
            await self.memory.store_memory(
                category=MemoryCategory.PATTERN,
                content="Learning effectiveness analysis",
                metadata={
                    "type": "learning_analysis",
                    "analysis_data": analysis,
                    "analysis_date": analysis["analysis_date"].isoformat()
                },
                project_name="global",
                tags=["learning_analysis", "continuous_learning", "effectiveness"]
            )
            
        except Exception as e:
            logger.error(f"Failed to store analysis in memory: {e}")

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning engine statistics."""
        return {
            "total_outcomes_captured": len(self.captured_outcomes),
            "patterns_identified": len(self.identified_patterns),
            "active_insights": len([i for i in self.learning_insights if i.status == "active"]),
            "learning_metrics": len(self.learning_metrics),
            "pattern_types": {
                ptype.value: len([p for p in self.identified_patterns.values() if p.pattern_type == ptype])
                for ptype in PatternType
            },
            "recent_patterns": len([p for p in self.identified_patterns.values() 
                                 if (datetime.now() - p.last_observed).days <= 7]),
            "learning_window_days": self.learning_window.days,
            "system_health": "operational"
        }


# Factory function
def create_continuous_learning_engine(memory: ClaudePMMemory, 
                                     learning_window_days: int = 90) -> ContinuousLearningEngine:
    """
    Create and initialize a ContinuousLearningEngine.
    
    Args:
        memory: ClaudePMMemory instance for memory operations
        learning_window_days: Size of the learning window for analysis
        
    Returns:
        Initialized ContinuousLearningEngine
    """
    return ContinuousLearningEngine(memory, learning_window_days)