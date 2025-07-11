"""
Intelligent Workflow Selection Engine - M02-014 Implementation

This module implements automatic workflow selection based on task analysis, memory patterns,
and success metrics. It builds upon the memory-augmented agent capabilities and intelligent
task planner to provide optimal workflow routing for the Claude PM Framework.

Key Features:
- Automatic workflow pattern matching
- Task complexity-driven routing
- Success probability prediction
- Dynamic resource allocation
- Continuous learning from outcomes
"""

import asyncio
import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .claude_pm_memory import ClaudePMMemory, MemoryCategory, MemoryResponse
from .intelligent_task_planner import (
    IntelligentTaskPlanner,
    TaskComplexity,
    DecompositionStrategy,
    TaskDecomposition,
    SubTask,
)
from .mem0_context_manager import Mem0ContextManager, ContextRequest, ContextType, ContextScope

# Removed LangGraph imports - functionality replaced with mem0AI context manager
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowType(str, Enum):
    """Available workflow types in the Claude PM Framework."""

    SIMPLE_LINEAR = "simple_linear"  # Single agent, linear execution
    PARALLEL_MULTI_AGENT = "parallel_multi_agent"  # Multiple agents, parallel execution
    HIERARCHICAL_REVIEW = "hierarchical_review"  # Multi-stage with reviews
    ITERATIVE_REFINEMENT = "iterative_refinement"  # Iterative improvement cycles
    RESEARCH_DISCOVERY = "research_discovery"  # Research-first approach
    CRITICAL_PATH = "critical_path"  # Dependencies-optimized execution
    EMERGENCY_FAST_TRACK = "emergency_fast_track"  # Minimized overhead for urgent tasks


class RoutingStrategy(str, Enum):
    """Strategies for workflow routing decisions."""

    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Optimize for speed/efficiency
    QUALITY_OPTIMIZED = "quality_optimized"  # Optimize for highest quality
    RESOURCE_OPTIMIZED = "resource_optimized"  # Optimize for resource usage
    BALANCED = "balanced"  # Balance all factors
    LEARNING_OPTIMIZED = "learning_optimized"  # Optimize for learning/patterns


@dataclass
class WorkflowPattern:
    """A workflow pattern stored in memory with success metrics."""

    pattern_id: str
    workflow_type: WorkflowType
    task_characteristics: Dict[str, Any]
    complexity_range: Tuple[TaskComplexity, TaskComplexity]
    success_rate: float
    avg_execution_time: float
    avg_resource_usage: Dict[str, float]
    team_preferences: List[str]
    recent_usage_count: int
    last_used: datetime

    # Performance metrics
    quality_score: float = 0.0
    efficiency_score: float = 0.0
    satisfaction_score: float = 0.0
    failure_reasons: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)


@dataclass
class WorkflowRecommendation:
    """Recommendation for workflow selection with reasoning."""

    workflow_type: WorkflowType
    confidence: float
    reasoning: str
    predicted_success_rate: float
    estimated_duration_minutes: int
    resource_requirements: Dict[str, Any]
    routing_strategy: RoutingStrategy

    # Supporting data
    pattern_matches: List[str] = field(default_factory=list)
    fallback_workflows: List[WorkflowType] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)


@dataclass
class WorkflowSelectionRequest:
    """Request for intelligent workflow selection."""

    task_description: str
    task_complexity: Optional[TaskComplexity] = None
    project_name: Optional[str] = None
    priority_level: str = "medium"  # low, medium, high, critical
    deadline: Optional[datetime] = None
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    quality_requirements: str = "standard"  # minimal, standard, high, critical
    team_preferences: List[str] = field(default_factory=list)

    # Context
    similar_tasks: List[str] = field(default_factory=list)
    previous_workflow_outcomes: List[Dict] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)


class WorkflowSelectionEngine:
    """
    Intelligent Workflow Selection Engine for automatic workflow routing.

    Uses memory patterns, performance data, and task analysis to automatically
    select the optimal workflow approach for each task.
    """

    def __init__(
        self,
        memory: ClaudePMMemory,
        context_manager: Mem0ContextManager,
        agent_memory_manager: Any,  # Replaced AgentMemoryManager with mem0AI context manager
        task_planner: IntelligentTaskPlanner,
    ):
        """
        Initialize the Workflow Selection Engine.

        Args:
            memory: ClaudePMMemory for pattern storage and retrieval
            context_manager: Context manager for memory preparation
            agent_memory_manager: Agent performance and selection data
            task_planner: Intelligent task decomposition capabilities
        """
        self.memory = memory
        self.context_manager = context_manager
        self.agent_memory_manager = agent_memory_manager
        self.task_planner = task_planner

        # Workflow patterns and rules
        self.workflow_patterns: Dict[str, WorkflowPattern] = {}
        self.selection_rules = self._initialize_selection_rules()
        self.routing_weights = self._initialize_routing_weights()

        # Performance tracking
        self.selection_history: List[Dict] = []
        self.performance_metrics = {
            "total_selections": 0,
            "success_rate": 0.0,
            "average_confidence": 0.0,
            "pattern_hit_rate": 0.0,
            "optimization_improvements": [],
        }

        # Learning system
        self.learning_rate = 0.1
        self.pattern_threshold = 0.7
        self.last_pattern_update = datetime.now()

        logger.info("WorkflowSelectionEngine initialized with intelligent routing capabilities")

    def _initialize_selection_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize workflow selection rules based on task characteristics."""
        return {
            # Simple tasks - minimal overhead
            "trivial_simple": {
                "complexity_range": [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE],
                "preferred_workflows": [
                    WorkflowType.SIMPLE_LINEAR,
                    WorkflowType.EMERGENCY_FAST_TRACK,
                ],
                "max_agents": 2,
                "review_required": False,
                "parallel_beneficial": False,
            },
            # Medium complexity - balanced approach
            "medium_balanced": {
                "complexity_range": [TaskComplexity.MEDIUM],
                "preferred_workflows": [
                    WorkflowType.PARALLEL_MULTI_AGENT,
                    WorkflowType.HIERARCHICAL_REVIEW,
                    WorkflowType.ITERATIVE_REFINEMENT,
                ],
                "max_agents": 4,
                "review_required": True,
                "parallel_beneficial": True,
            },
            # Complex tasks - comprehensive approach
            "complex_comprehensive": {
                "complexity_range": [TaskComplexity.COMPLEX, TaskComplexity.EPIC],
                "preferred_workflows": [
                    WorkflowType.HIERARCHICAL_REVIEW,
                    WorkflowType.RESEARCH_DISCOVERY,
                    WorkflowType.CRITICAL_PATH,
                ],
                "max_agents": 6,
                "review_required": True,
                "parallel_beneficial": True,
            },
            # Research-heavy tasks
            "research_discovery": {
                "task_keywords": [
                    "research",
                    "investigate",
                    "analyze",
                    "explore",
                    "poc",
                    "feasibility",
                ],
                "preferred_workflows": [
                    WorkflowType.RESEARCH_DISCOVERY,
                    WorkflowType.ITERATIVE_REFINEMENT,
                ],
                "max_agents": 3,
                "review_required": True,
                "parallel_beneficial": False,
            },
            # Time-critical tasks
            "urgent_fast_track": {
                "priority_levels": ["high", "critical"],
                "deadline_threshold_hours": 24,
                "preferred_workflows": [
                    WorkflowType.EMERGENCY_FAST_TRACK,
                    WorkflowType.SIMPLE_LINEAR,
                    WorkflowType.PARALLEL_MULTI_AGENT,
                ],
                "max_agents": 3,
                "review_required": False,
                "parallel_beneficial": True,
            },
        }

    def _initialize_routing_weights(self) -> Dict[str, Dict[str, float]]:
        """Initialize weights for different routing strategies."""
        return {
            RoutingStrategy.PERFORMANCE_OPTIMIZED.value: {
                "execution_time": 0.4,
                "success_rate": 0.3,
                "resource_efficiency": 0.2,
                "quality": 0.1,
            },
            RoutingStrategy.QUALITY_OPTIMIZED.value: {
                "quality": 0.4,
                "success_rate": 0.3,
                "execution_time": 0.1,
                "resource_efficiency": 0.2,
            },
            RoutingStrategy.RESOURCE_OPTIMIZED.value: {
                "resource_efficiency": 0.4,
                "execution_time": 0.3,
                "success_rate": 0.2,
                "quality": 0.1,
            },
            RoutingStrategy.BALANCED.value: {
                "success_rate": 0.3,
                "execution_time": 0.25,
                "quality": 0.25,
                "resource_efficiency": 0.2,
            },
            RoutingStrategy.LEARNING_OPTIMIZED.value: {
                "pattern_learning": 0.3,
                "success_rate": 0.25,
                "quality": 0.25,
                "execution_time": 0.2,
            },
        }

    async def select_workflow(self, request: WorkflowSelectionRequest) -> WorkflowRecommendation:
        """
        Intelligently select the optimal workflow for a task.

        Args:
            request: WorkflowSelectionRequest with task details and requirements

        Returns:
            WorkflowRecommendation with selected workflow and reasoning
        """
        start_time = time.time()
        logger.info(f"Selecting workflow for task: {request.task_description[:100]}...")

        try:
            # Step 1: Analyze task characteristics and complexity
            task_analysis = await self._analyze_task_characteristics(request)

            # Step 2: Load relevant workflow patterns from memory
            patterns = await self._load_workflow_patterns(request, task_analysis)

            # Step 3: Determine optimal routing strategy
            routing_strategy = self._determine_routing_strategy(request, task_analysis)

            # Step 4: Match task to workflow patterns
            pattern_matches = await self._match_workflow_patterns(
                request, task_analysis, patterns, routing_strategy
            )

            # Step 5: Predict outcomes for candidate workflows
            outcome_predictions = await self._predict_workflow_outcomes(
                request, pattern_matches, task_analysis
            )

            # Step 6: Select optimal workflow based on predictions
            selected_workflow = self._select_optimal_workflow(
                outcome_predictions, routing_strategy, request
            )

            # Step 7: Generate comprehensive recommendation
            recommendation = await self._generate_workflow_recommendation(
                selected_workflow, request, task_analysis, pattern_matches, routing_strategy
            )

            # Step 8: Store selection for learning
            await self._store_workflow_selection(request, recommendation, task_analysis)

            # Step 9: Update performance metrics
            self._update_selection_metrics(recommendation, time.time() - start_time)

            logger.info(
                f"Selected workflow: {recommendation.workflow_type.value} "
                f"(confidence: {recommendation.confidence:.2f})"
            )

            return recommendation

        except Exception as e:
            logger.error(f"Workflow selection failed: {e}")
            return self._create_fallback_recommendation(request)

    async def _analyze_task_characteristics(
        self, request: WorkflowSelectionRequest
    ) -> Dict[str, Any]:
        """Analyze task characteristics for workflow selection."""
        analysis = {
            "complexity": None,
            "keywords": [],
            "domain": "general",
            "estimated_duration": 0,
            "resource_intensity": "medium",
            "collaboration_level": "medium",
            "risk_level": "medium",
            "research_required": False,
            "critical_path_dependencies": False,
        }

        try:
            # Extract task complexity (use provided or analyze)
            if request.task_complexity:
                analysis["complexity"] = request.task_complexity
            else:
                # Use task planner for complexity analysis
                decomposition = await self.task_planner.decompose_task(
                    request.task_description, request.project_name
                )
                analysis["complexity"] = decomposition.complexity
                analysis["estimated_duration"] = decomposition.total_estimated_hours * 60  # minutes

            # Extract keywords and analyze task type
            analysis["keywords"] = self._extract_task_keywords(request.task_description)

            # Analyze task characteristics
            analysis.update(self._analyze_task_type(request.task_description, analysis["keywords"]))

            # Assess urgency and resource requirements
            analysis.update(self._assess_urgency_and_resources(request))

            logger.debug(f"Task analysis completed: {analysis}")
            return analysis

        except Exception as e:
            logger.error(f"Task analysis failed: {e}")
            return analysis

    def _extract_task_keywords(self, task_description: str) -> List[str]:
        """Extract relevant keywords from task description."""
        keywords = []
        task_lower = task_description.lower()

        # Workflow-relevant keywords
        workflow_keywords = {
            "research": ["research", "investigate", "analyze", "explore", "study"],
            "implementation": ["implement", "build", "create", "develop", "code"],
            "design": ["design", "architect", "plan", "model", "structure"],
            "testing": ["test", "validate", "verify", "qa", "quality"],
            "integration": ["integrate", "connect", "merge", "combine"],
            "migration": ["migrate", "move", "transfer", "convert"],
            "optimization": ["optimize", "improve", "enhance", "performance"],
            "fix": ["fix", "bug", "issue", "error", "problem"],
            "deployment": ["deploy", "release", "launch", "publish"],
            "documentation": ["document", "doc", "readme", "guide"],
        }

        for category, words in workflow_keywords.items():
            for word in words:
                if word in task_lower:
                    keywords.append(category)
                    break

        return list(set(keywords))

    def _analyze_task_type(self, task_description: str, keywords: List[str]) -> Dict[str, Any]:
        """Analyze task type characteristics."""
        analysis = {}
        task_lower = task_description.lower()

        # Research intensity
        research_indicators = [
            "research",
            "investigate",
            "analyze",
            "explore",
            "poc",
            "feasibility",
        ]
        analysis["research_required"] = any(
            indicator in task_lower for indicator in research_indicators
        )

        # Collaboration level
        collab_indicators = ["team", "collaborate", "review", "discuss", "meeting"]
        if any(indicator in task_lower for indicator in collab_indicators):
            analysis["collaboration_level"] = "high"
        elif "solo" in task_lower or "individual" in task_lower:
            analysis["collaboration_level"] = "low"
        else:
            analysis["collaboration_level"] = "medium"

        # Risk assessment
        risk_indicators = ["critical", "production", "security", "migration", "major"]
        if any(indicator in task_lower for indicator in risk_indicators):
            analysis["risk_level"] = "high"
        elif "simple" in task_lower or "minor" in task_lower or "small" in task_lower:
            analysis["risk_level"] = "low"
        else:
            analysis["risk_level"] = "medium"

        # Dependencies analysis
        dep_indicators = ["depends on", "requires", "after", "before", "prerequisite"]
        analysis["critical_path_dependencies"] = any(
            indicator in task_lower for indicator in dep_indicators
        )

        return analysis

    def _assess_urgency_and_resources(self, request: WorkflowSelectionRequest) -> Dict[str, Any]:
        """Assess task urgency and resource requirements."""
        assessment = {}

        # Urgency assessment
        if request.deadline:
            time_until_deadline = request.deadline - datetime.now()
            hours_until_deadline = time_until_deadline.total_seconds() / 3600

            if hours_until_deadline < 4:
                assessment["urgency"] = "critical"
            elif hours_until_deadline < 24:
                assessment["urgency"] = "high"
            elif hours_until_deadline < 72:
                assessment["urgency"] = "medium"
            else:
                assessment["urgency"] = "low"
        else:
            # Base urgency on priority level
            priority_to_urgency = {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "low": "low",
            }
            assessment["urgency"] = priority_to_urgency.get(request.priority_level, "medium")

        # Resource intensity
        if request.resource_constraints:
            if request.resource_constraints.get(
                "cpu_intensive", False
            ) or request.resource_constraints.get("memory_intensive", False):
                assessment["resource_intensity"] = "high"
            elif request.resource_constraints.get("lightweight", False):
                assessment["resource_intensity"] = "low"

        return assessment

    async def _load_workflow_patterns(
        self, request: WorkflowSelectionRequest, task_analysis: Dict[str, Any]
    ) -> List[WorkflowPattern]:
        """Load relevant workflow patterns from memory."""
        try:
            patterns = []

            # Build search query for similar workflow patterns
            search_terms = [
                "workflow pattern",
                request.task_description[:50],
                task_analysis["complexity"].value if task_analysis.get("complexity") else "medium",
            ]
            search_terms.extend(task_analysis.get("keywords", []))

            query = " ".join(search_terms)

            # Search for workflow patterns in memory
            response = await self.memory.retrieve_memories(
                category=MemoryCategory.PATTERN,
                query=query,
                tags=["workflow_pattern", "routing", "selection"],
                limit=15,
            )

            if response.success and response.data:
                memories = response.data.get("memories", [])

                for memory in memories:
                    pattern = self._parse_workflow_pattern(memory)
                    if pattern and self._is_pattern_relevant(pattern, request, task_analysis):
                        patterns.append(pattern)

            # Sort patterns by relevance and recent success
            patterns.sort(key=lambda p: (p.success_rate, p.recent_usage_count), reverse=True)

            logger.debug(f"Loaded {len(patterns)} relevant workflow patterns")
            return patterns[:10]  # Return top 10 most relevant patterns

        except Exception as e:
            logger.error(f"Failed to load workflow patterns: {e}")
            return []

    def _parse_workflow_pattern(self, memory: Dict[str, Any]) -> Optional[WorkflowPattern]:
        """Parse a memory into a WorkflowPattern object."""
        try:
            metadata = memory.get("metadata", {})
            pattern_data = metadata.get("pattern_data", {})

            if not pattern_data:
                return None

            return WorkflowPattern(
                pattern_id=memory.get("id", "unknown"),
                workflow_type=WorkflowType(pattern_data.get("workflow_type", "simple_linear")),
                task_characteristics=pattern_data.get("task_characteristics", {}),
                complexity_range=(
                    TaskComplexity(pattern_data.get("min_complexity", "simple")),
                    TaskComplexity(pattern_data.get("max_complexity", "medium")),
                ),
                success_rate=float(pattern_data.get("success_rate", 0.5)),
                avg_execution_time=float(pattern_data.get("avg_execution_time", 30)),
                avg_resource_usage=pattern_data.get("avg_resource_usage", {}),
                team_preferences=pattern_data.get("team_preferences", []),
                recent_usage_count=int(pattern_data.get("recent_usage_count", 0)),
                last_used=datetime.fromisoformat(
                    pattern_data.get("last_used", datetime.now().isoformat())
                ),
                quality_score=float(pattern_data.get("quality_score", 0.7)),
                efficiency_score=float(pattern_data.get("efficiency_score", 0.7)),
                satisfaction_score=float(pattern_data.get("satisfaction_score", 0.7)),
                failure_reasons=pattern_data.get("failure_reasons", []),
                success_factors=pattern_data.get("success_factors", []),
            )

        except Exception as e:
            logger.error(f"Failed to parse workflow pattern: {e}")
            return None

    def _is_pattern_relevant(
        self,
        pattern: WorkflowPattern,
        request: WorkflowSelectionRequest,
        task_analysis: Dict[str, Any],
    ) -> bool:
        """Check if a workflow pattern is relevant to the current request."""
        try:
            # Check complexity compatibility
            task_complexity = task_analysis.get("complexity", TaskComplexity.MEDIUM)
            min_complexity, max_complexity = pattern.complexity_range

            complexity_order = [
                TaskComplexity.TRIVIAL,
                TaskComplexity.SIMPLE,
                TaskComplexity.MEDIUM,
                TaskComplexity.COMPLEX,
                TaskComplexity.EPIC,
            ]

            task_idx = complexity_order.index(task_complexity)
            min_idx = complexity_order.index(min_complexity)
            max_idx = complexity_order.index(max_complexity)

            if not (min_idx <= task_idx <= max_idx):
                return False

            # Check keyword overlap
            task_keywords = set(task_analysis.get("keywords", []))
            pattern_keywords = set(pattern.task_characteristics.get("keywords", []))

            if task_keywords and pattern_keywords:
                overlap_ratio = len(task_keywords.intersection(pattern_keywords)) / len(
                    task_keywords.union(pattern_keywords)
                )
                if overlap_ratio < 0.2:  # Less than 20% overlap
                    return False

            # Check recent success rate
            if pattern.success_rate < 0.3:  # Low success rate
                return False

            return True

        except Exception as e:
            logger.error(f"Pattern relevance check failed: {e}")
            return False

    def _determine_routing_strategy(
        self, request: WorkflowSelectionRequest, task_analysis: Dict[str, Any]
    ) -> RoutingStrategy:
        """Determine the optimal routing strategy based on request and analysis."""

        # Critical/urgent tasks optimize for performance
        urgency = task_analysis.get("urgency", "medium")
        if urgency in ["critical", "high"]:
            return RoutingStrategy.PERFORMANCE_OPTIMIZED

        # High quality requirements
        if request.quality_requirements == "critical":
            return RoutingStrategy.QUALITY_OPTIMIZED

        # Resource constraints
        if request.resource_constraints.get("limited_resources", False):
            return RoutingStrategy.RESOURCE_OPTIMIZED

        # Learning/experimental tasks
        if (
            "experiment" in request.task_description.lower()
            or "poc" in request.task_description.lower()
        ):
            return RoutingStrategy.LEARNING_OPTIMIZED

        # Default to balanced approach
        return RoutingStrategy.BALANCED

    async def _match_workflow_patterns(
        self,
        request: WorkflowSelectionRequest,
        task_analysis: Dict[str, Any],
        patterns: List[WorkflowPattern],
        routing_strategy: RoutingStrategy,
    ) -> Dict[WorkflowType, List[WorkflowPattern]]:
        """Match workflow patterns to potential workflow types."""
        matches = {}

        # Group patterns by workflow type
        for pattern in patterns:
            workflow_type = pattern.workflow_type
            if workflow_type not in matches:
                matches[workflow_type] = []
            matches[workflow_type].append(pattern)

        # Apply selection rules to find additional candidate workflows
        rule_matches = self._apply_selection_rules(request, task_analysis)

        for workflow_type in rule_matches:
            if workflow_type not in matches:
                matches[workflow_type] = []

        # Score and sort matches by routing strategy
        for workflow_type, pattern_list in matches.items():
            pattern_list.sort(
                key=lambda p: self._score_pattern_for_strategy(p, routing_strategy), reverse=True
            )

        return matches

    def _apply_selection_rules(
        self, request: WorkflowSelectionRequest, task_analysis: Dict[str, Any]
    ) -> List[WorkflowType]:
        """Apply selection rules to identify candidate workflows."""
        candidates = []

        complexity = task_analysis.get("complexity", TaskComplexity.MEDIUM)
        keywords = task_analysis.get("keywords", [])
        urgency = task_analysis.get("urgency", "medium")

        for rule_name, rule in self.selection_rules.items():
            rule_applies = False

            # Check complexity range
            if "complexity_range" in rule:
                if complexity in rule["complexity_range"]:
                    rule_applies = True

            # Check keywords
            if "task_keywords" in rule:
                if any(keyword in keywords for keyword in rule["task_keywords"]):
                    rule_applies = True

            # Check priority/urgency
            if "priority_levels" in rule:
                if (
                    request.priority_level in rule["priority_levels"]
                    or urgency in rule["priority_levels"]
                ):
                    rule_applies = True

            # Check deadline constraints
            if "deadline_threshold_hours" in rule and request.deadline:
                hours_until_deadline = (request.deadline - datetime.now()).total_seconds() / 3600
                if hours_until_deadline <= rule["deadline_threshold_hours"]:
                    rule_applies = True

            if rule_applies:
                candidates.extend(rule["preferred_workflows"])

        return list(set(candidates))  # Remove duplicates

    def _score_pattern_for_strategy(
        self, pattern: WorkflowPattern, strategy: RoutingStrategy
    ) -> float:
        """Score a pattern based on the routing strategy."""
        weights = self.routing_weights.get(
            strategy.value, self.routing_weights[RoutingStrategy.BALANCED.value]
        )

        # Normalize scores to 0-1 range
        success_score = pattern.success_rate
        quality_score = pattern.quality_score
        efficiency_score = pattern.efficiency_score
        time_score = 1.0 - min(pattern.avg_execution_time / 180.0, 1.0)  # Normalize to 3 hours max
        resource_score = 1.0 - pattern.avg_resource_usage.get("cpu", 0.5)  # Assume lower is better

        # Calculate weighted score
        score = (
            weights.get("success_rate", 0) * success_score
            + weights.get("quality", 0) * quality_score
            + weights.get("execution_time", 0) * time_score
            + weights.get("resource_efficiency", 0) * resource_score
            + weights.get("pattern_learning", 0) * (pattern.recent_usage_count / 10.0)
        )

        return min(score, 1.0)

    async def _predict_workflow_outcomes(
        self,
        request: WorkflowSelectionRequest,
        pattern_matches: Dict[WorkflowType, List[WorkflowPattern]],
        task_analysis: Dict[str, Any],
    ) -> Dict[WorkflowType, Dict[str, Any]]:
        """Predict outcomes for each candidate workflow type."""
        predictions = {}

        for workflow_type, patterns in pattern_matches.items():
            if not patterns:
                continue

            # Calculate predictions based on pattern data
            success_rates = [p.success_rate for p in patterns]
            execution_times = [p.avg_execution_time for p in patterns]
            quality_scores = [p.quality_score for p in patterns]

            # Weighted averages (more recent patterns have higher weight)
            weights = [self._calculate_pattern_weight(p) for p in patterns]
            total_weight = sum(weights)

            if total_weight > 0:
                predicted_success_rate = (
                    sum(sr * w for sr, w in zip(success_rates, weights)) / total_weight
                )
                predicted_duration = (
                    sum(et * w for et, w in zip(execution_times, weights)) / total_weight
                )
                predicted_quality = (
                    sum(qs * w for qs, w in zip(quality_scores, weights)) / total_weight
                )
            else:
                predicted_success_rate = (
                    sum(success_rates) / len(success_rates) if success_rates else 0.5
                )
                predicted_duration = (
                    sum(execution_times) / len(execution_times) if execution_times else 30
                )
                predicted_quality = (
                    sum(quality_scores) / len(quality_scores) if quality_scores else 0.7
                )

            # Adjust predictions based on task analysis
            adjusted_predictions = self._adjust_predictions_for_task(
                workflow_type,
                task_analysis,
                predicted_success_rate,
                predicted_duration,
                predicted_quality,
            )

            predictions[workflow_type] = {
                "success_rate": adjusted_predictions["success_rate"],
                "duration_minutes": adjusted_predictions["duration"],
                "quality_score": adjusted_predictions["quality"],
                "confidence": self._calculate_prediction_confidence(patterns, task_analysis),
                "pattern_count": len(patterns),
                "risk_factors": self._identify_risk_factors(workflow_type, task_analysis, patterns),
            }

        return predictions

    def _calculate_pattern_weight(self, pattern: WorkflowPattern) -> float:
        """Calculate weight for a pattern based on recency and reliability."""
        # Time decay (more recent patterns are weighted higher)
        days_since_used = (datetime.now() - pattern.last_used).days
        time_weight = math.exp(-days_since_used / 30.0)  # 30-day half-life

        # Success rate weight
        success_weight = pattern.success_rate

        # Usage frequency weight
        usage_weight = min(pattern.recent_usage_count / 10.0, 1.0)

        return time_weight * 0.4 + success_weight * 0.4 + usage_weight * 0.2

    def _adjust_predictions_for_task(
        self,
        workflow_type: WorkflowType,
        task_analysis: Dict[str, Any],
        base_success_rate: float,
        base_duration: float,
        base_quality: float,
    ) -> Dict[str, Any]:
        """Adjust predictions based on specific task characteristics."""

        # Complexity adjustments
        complexity = task_analysis.get("complexity", TaskComplexity.MEDIUM)
        complexity_multipliers = {
            TaskComplexity.TRIVIAL: {"duration": 0.5, "success": 1.2, "quality": 1.0},
            TaskComplexity.SIMPLE: {"duration": 0.8, "success": 1.1, "quality": 1.0},
            TaskComplexity.MEDIUM: {"duration": 1.0, "success": 1.0, "quality": 1.0},
            TaskComplexity.COMPLEX: {"duration": 1.5, "success": 0.9, "quality": 1.1},
            TaskComplexity.EPIC: {"duration": 2.0, "success": 0.8, "quality": 1.2},
        }

        multiplier = complexity_multipliers.get(
            complexity, complexity_multipliers[TaskComplexity.MEDIUM]
        )

        # Urgency adjustments
        urgency = task_analysis.get("urgency", "medium")
        if urgency == "critical":
            multiplier["duration"] *= 1.2  # Rush can slow things down
            multiplier["success"] *= 0.9  # Higher error rate under pressure
        elif urgency == "low":
            multiplier["quality"] *= 1.1  # More time for quality

        # Workflow-specific adjustments
        workflow_adjustments = {
            WorkflowType.EMERGENCY_FAST_TRACK: {"duration": 0.7, "success": 0.85, "quality": 0.8},
            WorkflowType.RESEARCH_DISCOVERY: {"duration": 1.3, "success": 0.9, "quality": 1.2},
            WorkflowType.HIERARCHICAL_REVIEW: {"duration": 1.2, "success": 1.1, "quality": 1.3},
            WorkflowType.PARALLEL_MULTI_AGENT: {"duration": 0.8, "success": 1.05, "quality": 1.1},
        }

        if workflow_type in workflow_adjustments:
            workflow_adj = workflow_adjustments[workflow_type]
            multiplier["duration"] *= workflow_adj["duration"]
            multiplier["success"] *= workflow_adj["success"]
            multiplier["quality"] *= workflow_adj["quality"]

        return {
            "success_rate": min(base_success_rate * multiplier["success"], 1.0),
            "duration": base_duration * multiplier["duration"],
            "quality": min(base_quality * multiplier["quality"], 1.0),
        }

    def _calculate_prediction_confidence(
        self, patterns: List[WorkflowPattern], task_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence in outcome predictions."""
        if not patterns:
            return 0.3

        # More patterns = higher confidence (up to a point)
        pattern_confidence = min(len(patterns) / 5.0, 1.0)

        # Recent usage = higher confidence
        recent_patterns = [p for p in patterns if (datetime.now() - p.last_used).days < 30]
        recency_confidence = len(recent_patterns) / len(patterns)

        # Consistency in success rates = higher confidence
        success_rates = [p.success_rate for p in patterns]
        if len(success_rates) > 1:
            import statistics

            consistency_confidence = 1.0 - (
                statistics.stdev(success_rates) / 0.5
            )  # Normalize by max possible stdev
        else:
            consistency_confidence = 0.7

        # Combined confidence
        overall_confidence = (
            pattern_confidence * 0.4
            + recency_confidence * 0.3
            + max(consistency_confidence, 0.0) * 0.3
        )

        return min(overall_confidence, 1.0)

    def _identify_risk_factors(
        self,
        workflow_type: WorkflowType,
        task_analysis: Dict[str, Any],
        patterns: List[WorkflowPattern],
    ) -> List[str]:
        """Identify potential risk factors for the workflow."""
        risks = []

        # Complexity-based risks
        complexity = task_analysis.get("complexity", TaskComplexity.MEDIUM)
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.EPIC]:
            risks.append("High complexity may lead to scope creep")

        # Urgency-based risks
        urgency = task_analysis.get("urgency", "medium")
        if urgency == "critical":
            risks.append("Time pressure may compromise quality")

        # Pattern-based risks
        if patterns:
            common_failures = []
            for pattern in patterns:
                common_failures.extend(pattern.failure_reasons)

            # Find most common failure reasons
            if common_failures:
                from collections import Counter

                failure_counts = Counter(common_failures)
                most_common = failure_counts.most_common(2)
                for failure, count in most_common:
                    if count >= 2:  # Appears in at least 2 patterns
                        risks.append(f"Historical risk: {failure}")

        # Workflow-specific risks
        workflow_risks = {
            WorkflowType.EMERGENCY_FAST_TRACK: ["Reduced testing may introduce bugs"],
            WorkflowType.PARALLEL_MULTI_AGENT: ["Coordination overhead", "Integration challenges"],
            WorkflowType.RESEARCH_DISCOVERY: ["Scope uncertainty", "Timeline unpredictability"],
            WorkflowType.CRITICAL_PATH: ["Dependency bottlenecks"],
        }

        if workflow_type in workflow_risks:
            risks.extend(workflow_risks[workflow_type])

        return risks

    def _select_optimal_workflow(
        self,
        predictions: Dict[WorkflowType, Dict[str, Any]],
        routing_strategy: RoutingStrategy,
        request: WorkflowSelectionRequest,
    ) -> Tuple[WorkflowType, Dict[str, Any]]:
        """Select the optimal workflow based on predictions and strategy."""

        if not predictions:
            # Fallback to simple linear workflow
            return WorkflowType.SIMPLE_LINEAR, {
                "success_rate": 0.7,
                "duration_minutes": 30,
                "quality_score": 0.7,
                "confidence": 0.3,
                "pattern_count": 0,
                "risk_factors": ["No historical patterns available"],
            }

        # Score each workflow based on routing strategy
        workflow_scores = {}
        weights = self.routing_weights.get(
            routing_strategy.value, self.routing_weights[RoutingStrategy.BALANCED.value]
        )

        for workflow_type, prediction in predictions.items():
            # Normalize scores
            success_score = prediction["success_rate"]
            time_score = 1.0 - min(
                prediction["duration_minutes"] / 180.0, 1.0
            )  # Normalize to 3 hours
            quality_score = prediction["quality_score"]
            confidence_score = prediction["confidence"]

            # Calculate weighted score
            score = (
                weights.get("success_rate", 0) * success_score
                + weights.get("execution_time", 0) * time_score
                + weights.get("quality", 0) * quality_score
                + weights.get("resource_efficiency", 0)
                * (1.0 - len(prediction["risk_factors"]) / 10.0)
                + weights.get("pattern_learning", 0) * (prediction["pattern_count"] / 10.0)
            )

            # Apply confidence weighting
            workflow_scores[workflow_type] = score * confidence_score

        # Select workflow with highest score
        best_workflow = max(workflow_scores.items(), key=lambda x: x[1])
        return best_workflow[0], predictions[best_workflow[0]]

    async def _generate_workflow_recommendation(
        self,
        selected_workflow: Tuple[WorkflowType, Dict[str, Any]],
        request: WorkflowSelectionRequest,
        task_analysis: Dict[str, Any],
        pattern_matches: Dict[WorkflowType, List[WorkflowPattern]],
        routing_strategy: RoutingStrategy,
    ) -> WorkflowRecommendation:
        """Generate comprehensive workflow recommendation."""

        workflow_type, prediction = selected_workflow
        patterns = pattern_matches.get(workflow_type, [])

        # Generate reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Selected {workflow_type.value} workflow")
        reasoning_parts.append(f"Based on {prediction['pattern_count']} historical patterns")
        reasoning_parts.append(f"Predicted success rate: {prediction['success_rate']:.1%}")
        reasoning_parts.append(f"Strategy: {routing_strategy.value}")

        if task_analysis.get("urgency") in ["critical", "high"]:
            reasoning_parts.append("Optimized for urgency")

        # Determine fallback workflows
        all_predictions = {
            wf: pred
            for wf, pred in [(k, v) for k, v in pattern_matches.items() if k != workflow_type]
        }
        fallback_workflows = sorted(
            all_predictions.keys(),
            key=lambda wf: all_predictions[wf][0]["success_rate"] if all_predictions[wf] else 0,
            reverse=True,
        )[:2]

        # Resource requirements
        resource_requirements = self._estimate_resource_requirements(
            workflow_type, task_analysis, prediction
        )

        # Optimization opportunities
        optimization_opportunities = self._identify_optimization_opportunities(
            workflow_type, task_analysis, patterns
        )

        return WorkflowRecommendation(
            workflow_type=workflow_type,
            confidence=prediction["confidence"],
            reasoning=" | ".join(reasoning_parts),
            predicted_success_rate=prediction["success_rate"],
            estimated_duration_minutes=int(prediction["duration_minutes"]),
            resource_requirements=resource_requirements,
            routing_strategy=routing_strategy,
            pattern_matches=[p.pattern_id for p in patterns[:3]],
            fallback_workflows=fallback_workflows,
            risk_factors=prediction["risk_factors"],
            optimization_opportunities=optimization_opportunities,
        )

    def _estimate_resource_requirements(
        self, workflow_type: WorkflowType, task_analysis: Dict[str, Any], prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate resource requirements for the selected workflow."""

        # Base requirements by workflow type
        base_requirements = {
            WorkflowType.SIMPLE_LINEAR: {
                "agents": 1,
                "cpu": "low",
                "memory": "low",
                "coordination": "none",
            },
            WorkflowType.PARALLEL_MULTI_AGENT: {
                "agents": 3,
                "cpu": "medium",
                "memory": "medium",
                "coordination": "high",
            },
            WorkflowType.HIERARCHICAL_REVIEW: {
                "agents": 4,
                "cpu": "medium",
                "memory": "medium",
                "coordination": "high",
            },
            WorkflowType.ITERATIVE_REFINEMENT: {
                "agents": 2,
                "cpu": "medium",
                "memory": "low",
                "coordination": "medium",
            },
            WorkflowType.RESEARCH_DISCOVERY: {
                "agents": 2,
                "cpu": "low",
                "memory": "low",
                "coordination": "low",
            },
            WorkflowType.CRITICAL_PATH: {
                "agents": 4,
                "cpu": "high",
                "memory": "medium",
                "coordination": "high",
            },
            WorkflowType.EMERGENCY_FAST_TRACK: {
                "agents": 1,
                "cpu": "medium",
                "memory": "low",
                "coordination": "none",
            },
        }

        requirements = base_requirements.get(
            workflow_type, base_requirements[WorkflowType.SIMPLE_LINEAR]
        ).copy()

        # Adjust based on task complexity
        complexity = task_analysis.get("complexity", TaskComplexity.MEDIUM)
        complexity_multipliers = {
            TaskComplexity.TRIVIAL: 0.5,
            TaskComplexity.SIMPLE: 0.8,
            TaskComplexity.MEDIUM: 1.0,
            TaskComplexity.COMPLEX: 1.5,
            TaskComplexity.EPIC: 2.0,
        }

        multiplier = complexity_multipliers.get(complexity, 1.0)
        if multiplier != 1.0:
            requirements["agents"] = max(1, int(requirements["agents"] * multiplier))

        # Add estimated duration and quality target
        requirements["estimated_duration_minutes"] = prediction["duration_minutes"]
        requirements["quality_target"] = prediction["quality_score"]

        return requirements

    def _identify_optimization_opportunities(
        self,
        workflow_type: WorkflowType,
        task_analysis: Dict[str, Any],
        patterns: List[WorkflowPattern],
    ) -> List[str]:
        """Identify opportunities for workflow optimization."""
        opportunities = []

        # Pattern-based optimizations
        if patterns:
            # Find successful optimization factors
            success_factors = []
            for pattern in patterns:
                if pattern.success_rate > 0.8:
                    success_factors.extend(pattern.success_factors)

            if success_factors:
                from collections import Counter

                common_factors = Counter(success_factors).most_common(2)
                for factor, count in common_factors:
                    if count >= 2:
                        opportunities.append(f"Apply successful pattern: {factor}")

        # Workflow-specific optimizations
        workflow_optimizations = {
            WorkflowType.PARALLEL_MULTI_AGENT: [
                "Consider task decomposition for better parallelization",
                "Use async coordination to reduce wait times",
            ],
            WorkflowType.HIERARCHICAL_REVIEW: [
                "Implement early feedback loops",
                "Use staged reviews to catch issues early",
            ],
            WorkflowType.RESEARCH_DISCOVERY: [
                "Set clear research boundaries",
                "Use incremental discovery approach",
            ],
        }

        if workflow_type in workflow_optimizations:
            opportunities.extend(workflow_optimizations[workflow_type])

        # Task-specific optimizations
        if task_analysis.get("research_required"):
            opportunities.append("Consider research phase before implementation")

        if task_analysis.get("urgency") == "critical":
            opportunities.append("Focus on MVP approach to meet deadline")

        return opportunities

    async def _store_workflow_selection(
        self,
        request: WorkflowSelectionRequest,
        recommendation: WorkflowRecommendation,
        task_analysis: Dict[str, Any],
    ) -> None:
        """Store the workflow selection for future learning."""
        try:
            selection_data = {
                "request": {
                    "task_description": request.task_description,
                    "complexity": (
                        task_analysis.get("complexity", {}).value
                        if task_analysis.get("complexity")
                        else "medium"
                    ),
                    "priority": request.priority_level,
                    "quality_requirements": request.quality_requirements,
                    "keywords": task_analysis.get("keywords", []),
                },
                "recommendation": {
                    "workflow_type": recommendation.workflow_type.value,
                    "confidence": recommendation.confidence,
                    "routing_strategy": recommendation.routing_strategy.value,
                    "predicted_success_rate": recommendation.predicted_success_rate,
                    "estimated_duration": recommendation.estimated_duration_minutes,
                },
                "selection_timestamp": datetime.now().isoformat(),
                "pattern_matches_used": recommendation.pattern_matches,
            }

            # Store in memory for learning
            await self.memory.store_memory(
                category=MemoryCategory.PATTERN,
                content=f"Workflow selection: {recommendation.workflow_type.value} for {request.task_description[:100]}",
                metadata={
                    "type": "workflow_selection",
                    "selection_data": selection_data,
                    "workflow_type": recommendation.workflow_type.value,
                    "confidence": recommendation.confidence,
                    "routing_strategy": recommendation.routing_strategy.value,
                },
                project_name=request.project_name or "global",
                tags=[
                    "workflow_selection",
                    "routing",
                    recommendation.workflow_type.value,
                    recommendation.routing_strategy.value,
                ],
            )

            logger.debug("Stored workflow selection in memory for learning")

        except Exception as e:
            logger.error(f"Failed to store workflow selection: {e}")

    def _update_selection_metrics(
        self, recommendation: WorkflowRecommendation, execution_time: float
    ) -> None:
        """Update performance metrics for workflow selection."""
        self.performance_metrics["total_selections"] += 1

        # Update running averages
        total = self.performance_metrics["total_selections"]
        self.performance_metrics["average_confidence"] = (
            self.performance_metrics["average_confidence"] * (total - 1) + recommendation.confidence
        ) / total

        # Pattern hit rate (if patterns were used)
        if recommendation.pattern_matches:
            self.performance_metrics["pattern_hit_rate"] = (
                self.performance_metrics["pattern_hit_rate"] * (total - 1) + 1.0
            ) / total
        else:
            self.performance_metrics["pattern_hit_rate"] = (
                self.performance_metrics["pattern_hit_rate"] * (total - 1) + 0.0
            ) / total

        # Store selection for history
        self.selection_history.append(
            {
                "timestamp": datetime.now(),
                "workflow_type": recommendation.workflow_type.value,
                "confidence": recommendation.confidence,
                "predicted_success_rate": recommendation.predicted_success_rate,
                "execution_time_seconds": execution_time,
            }
        )

        # Keep only recent history
        if len(self.selection_history) > 100:
            self.selection_history = self.selection_history[-100:]

    def _create_fallback_recommendation(
        self, request: WorkflowSelectionRequest
    ) -> WorkflowRecommendation:
        """Create a fallback recommendation when selection fails."""

        # Simple fallback logic based on priority
        if request.priority_level in ["critical", "high"]:
            workflow_type = WorkflowType.EMERGENCY_FAST_TRACK
            duration = 20
        elif "research" in request.task_description.lower():
            workflow_type = WorkflowType.RESEARCH_DISCOVERY
            duration = 45
        else:
            workflow_type = WorkflowType.SIMPLE_LINEAR
            duration = 30

        return WorkflowRecommendation(
            workflow_type=workflow_type,
            confidence=0.3,
            reasoning="Fallback selection due to analysis failure",
            predicted_success_rate=0.6,
            estimated_duration_minutes=duration,
            resource_requirements={"agents": 1, "cpu": "medium", "memory": "low"},
            routing_strategy=RoutingStrategy.BALANCED,
            risk_factors=["Limited analysis available"],
            optimization_opportunities=["Improve task description for better analysis"],
        )

    async def get_workflow_analytics(self) -> Dict[str, Any]:
        """Get analytics and insights about workflow selection performance."""
        analytics = {
            "performance_metrics": self.performance_metrics.copy(),
            "recent_selections": self.selection_history[-10:],
            "workflow_type_distribution": {},
            "routing_strategy_distribution": {},
            "confidence_trends": [],
            "pattern_effectiveness": {},
        }

        # Analyze recent selections
        if self.selection_history:
            # Workflow type distribution
            workflow_types = [s["workflow_type"] for s in self.selection_history]
            from collections import Counter

            analytics["workflow_type_distribution"] = dict(Counter(workflow_types))

            # Confidence trends (last 20 selections)
            recent_confidences = [s["confidence"] for s in self.selection_history[-20:]]
            analytics["confidence_trends"] = recent_confidences

            # Average metrics
            analytics["average_predicted_success"] = sum(
                s["predicted_success_rate"] for s in self.selection_history
            ) / len(self.selection_history)

        return analytics

    def get_selection_stats(self) -> Dict[str, Any]:
        """Get current workflow selection statistics."""
        return {
            "total_selections": self.performance_metrics["total_selections"],
            "average_confidence": self.performance_metrics["average_confidence"],
            "pattern_hit_rate": self.performance_metrics["pattern_hit_rate"],
            "success_rate": self.performance_metrics["success_rate"],
            "loaded_patterns": len(self.workflow_patterns),
            "last_selection": self.selection_history[-1] if self.selection_history else None,
        }


# Factory function for easy integration
def create_workflow_selection_engine(
    memory: ClaudePMMemory,
    context_manager: Mem0ContextManager,
    agent_memory_manager: Any,  # Replaced AgentMemoryManager with mem0AI
    task_planner: IntelligentTaskPlanner,
) -> WorkflowSelectionEngine:
    """
    Factory function to create WorkflowSelectionEngine instance.

    Args:
        memory: ClaudePMMemory for pattern storage and retrieval
        context_manager: Context manager for memory preparation
        agent_memory_manager: Agent performance and selection data
        task_planner: Intelligent task decomposition capabilities

    Returns:
        WorkflowSelectionEngine: Configured workflow selection engine
    """
    return WorkflowSelectionEngine(memory, context_manager, agent_memory_manager, task_planner)
