"""
Recommendation Engine

This module implements memory-driven recommendations and suggestions for the
Claude PM Framework. It analyzes memory patterns, successful operations, and
error histories to provide intelligent recommendations for operations,
error prevention, and performance optimization.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import Counter, defaultdict

from .interfaces.models import MemoryItem, MemoryCategory
from .memory_context_enhancer import MemoryContext
from .context_builder import EnrichedContext, ContextType
from .similarity_matcher import SimilarityMatcher


class RecommendationType(str, Enum):
    """Types of recommendations that can be generated."""
    
    OPERATION_GUIDANCE = "operation_guidance"       # Best practices for operations
    ERROR_PREVENTION = "error_prevention"          # Warnings about potential errors
    PERFORMANCE_OPT = "performance_optimization"   # Performance improvement suggestions
    WORKFLOW_IMPROVEMENT = "workflow_improvement"  # Process optimization recommendations
    DECISION_SUPPORT = "decision_support"          # Strategic decision recommendations
    RESOURCE_OPTIMIZATION = "resource_optimization" # Resource usage recommendations


@dataclass
class Recommendation:
    """A single recommendation with context and confidence."""
    
    id: str
    type: RecommendationType
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    rationale: str
    supporting_memories: List[str]  # Memory IDs
    confidence: float
    estimated_impact: str  # "high", "medium", "low"
    implementation_effort: str  # "low", "medium", "high"
    tags: List[str]
    created_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "supporting_memories": self.supporting_memories,
            "confidence": self.confidence,
            "estimated_impact": self.estimated_impact,
            "implementation_effort": self.implementation_effort,
            "tags": self.tags,
            "created_at": self.created_at
        }
    
    def get_score(self) -> float:
        """Calculate overall recommendation score for ranking."""
        priority_weights = {"high": 1.0, "medium": 0.7, "low": 0.4}
        impact_weights = {"high": 1.0, "medium": 0.7, "low": 0.4}
        effort_weights = {"low": 1.0, "medium": 0.7, "high": 0.4}
        
        score = (
            self.confidence * 0.4 +
            priority_weights.get(self.priority, 0.5) * 0.3 +
            impact_weights.get(self.estimated_impact, 0.5) * 0.2 +
            effort_weights.get(self.implementation_effort, 0.5) * 0.1
        )
        
        return score


@dataclass
class RecommendationSet:
    """A set of recommendations for a specific context."""
    
    context_id: str
    context_type: ContextType
    recommendations: List[Recommendation]
    generation_timestamp: float
    processing_time_ms: float
    total_memories_analyzed: int
    
    def get_by_type(self, rec_type: RecommendationType) -> List[Recommendation]:
        """Get recommendations by type."""
        return [rec for rec in self.recommendations if rec.type == rec_type]
    
    def get_by_priority(self, priority: str) -> List[Recommendation]:
        """Get recommendations by priority."""
        return [rec for rec in self.recommendations if rec.priority == priority]
    
    def get_top_recommendations(self, limit: int = 5) -> List[Recommendation]:
        """Get top recommendations by score."""
        sorted_recs = sorted(self.recommendations, key=lambda r: r.get_score(), reverse=True)
        return sorted_recs[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "context_id": self.context_id,
            "context_type": self.context_type.value,
            "recommendations": [rec.to_dict() for rec in self.recommendations],
            "generation_timestamp": self.generation_timestamp,
            "processing_time_ms": self.processing_time_ms,
            "total_memories_analyzed": self.total_memories_analyzed,
            "summary": {
                "total_recommendations": len(self.recommendations),
                "by_type": {rec_type.value: len(self.get_by_type(rec_type)) 
                           for rec_type in RecommendationType},
                "by_priority": {priority: len(self.get_by_priority(priority)) 
                               for priority in ["high", "medium", "low"]}
            }
        }


@dataclass
class RecommendationConfig:
    """Configuration for recommendation generation."""
    
    max_recommendations_per_type: int = 5
    min_confidence_threshold: float = 0.6
    enable_performance_recommendations: bool = True
    enable_error_prevention: bool = True
    enable_workflow_optimization: bool = True
    pattern_analysis_depth: int = 10
    similarity_threshold: float = 0.7
    temporal_weight_decay: float = 0.1
    success_pattern_weight: float = 0.8
    error_pattern_weight: float = 0.9
    
    def validate(self):
        """Validate configuration values."""
        if not (0.0 <= self.min_confidence_threshold <= 1.0):
            raise ValueError("min_confidence_threshold must be between 0.0 and 1.0")
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")
        if self.max_recommendations_per_type <= 0:
            raise ValueError("max_recommendations_per_type must be positive")


class RecommendationEngine:
    """
    Memory-driven recommendation and suggestion system.
    
    This class analyzes memory patterns, successful operations, and error histories
    to provide intelligent recommendations for operations, error prevention,
    performance optimization, and workflow improvements.
    """
    
    def __init__(
        self,
        similarity_matcher: SimilarityMatcher,
        config: Optional[RecommendationConfig] = None
    ):
        """
        Initialize the recommendation engine.
        
        Args:
            similarity_matcher: Similarity matcher for pattern analysis
            config: Configuration for recommendation generation
        """
        self.similarity_matcher = similarity_matcher
        self.config = config or RecommendationConfig()
        self.config.validate()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.generation_stats = {
            "total_generations": 0,
            "generations_by_type": {ctx_type.value: 0 for ctx_type in ContextType},
            "recommendations_by_type": {rec_type.value: 0 for rec_type in RecommendationType},
            "average_generation_time_ms": 0.0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_recommendations_generated": 0
        }
        
        # Pattern databases for recommendation generation
        self.success_patterns = self._initialize_success_patterns()
        self.error_patterns = self._initialize_error_patterns()
        self.performance_patterns = self._initialize_performance_patterns()
        self.workflow_patterns = self._initialize_workflow_patterns()
        
        # Recommendation templates
        self.recommendation_templates = self._initialize_recommendation_templates()
    
    def generate_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> RecommendationSet:
        """
        Generate recommendations based on enriched context.
        
        Args:
            enriched_context: Enhanced context with memories and analysis
            
        Returns:
            RecommendationSet: Generated recommendations
        """
        start_time = time.time()
        self.generation_stats["total_generations"] += 1
        self.generation_stats["generations_by_type"][enriched_context.context_type.value] += 1
        
        try:
            recommendations = []
            
            # Generate different types of recommendations
            if self.config.enable_error_prevention:
                error_recs = self._generate_error_prevention_recommendations(enriched_context)
                recommendations.extend(error_recs)
            
            if self.config.enable_performance_recommendations:
                perf_recs = self._generate_performance_recommendations(enriched_context)
                recommendations.extend(perf_recs)
            
            if self.config.enable_workflow_optimization:
                workflow_recs = self._generate_workflow_recommendations(enriched_context)
                recommendations.extend(workflow_recs)
            
            # Generate context-specific recommendations
            context_recs = self._generate_context_specific_recommendations(enriched_context)
            recommendations.extend(context_recs)
            
            # Filter and rank recommendations
            filtered_recs = self._filter_and_rank_recommendations(recommendations)
            
            # Update statistics
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_generation_stats(processing_time_ms, True, len(filtered_recs))
            
            self.logger.info(
                f"Generated {len(filtered_recs)} recommendations for {enriched_context.context_type.value} "
                f"in {processing_time_ms:.2f}ms"
            )
            
            return RecommendationSet(
                context_id=f"{enriched_context.context_type.value}_{int(time.time())}",
                context_type=enriched_context.context_type,
                recommendations=filtered_recs,
                generation_timestamp=time.time(),
                processing_time_ms=processing_time_ms,
                total_memories_analyzed=enriched_context.memory_context.get_total_memories()
            )
            
        except Exception as e:
            # Update error stats
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_generation_stats(processing_time_ms, False, 0)
            
            self.logger.error(f"Recommendation generation failed: {e}")
            
            # Return empty recommendation set on failure
            return RecommendationSet(
                context_id=f"error_{int(time.time())}",
                context_type=enriched_context.context_type,
                recommendations=[],
                generation_timestamp=time.time(),
                processing_time_ms=processing_time_ms,
                total_memories_analyzed=0
            )
    
    def _generate_error_prevention_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate error prevention recommendations."""
        recommendations = []
        memory_context = enriched_context.memory_context
        
        # Analyze error memories for patterns
        error_patterns = self._analyze_error_patterns(memory_context.error_memories)
        
        for pattern in error_patterns:
            if pattern["frequency"] >= 2 and pattern["confidence"] >= self.config.min_confidence_threshold:
                rec = self._create_error_prevention_recommendation(pattern, memory_context)
                if rec:
                    recommendations.append(rec)
        
        # Generate recommendations based on error indicators
        if enriched_context.analysis_summary.get("error_ratio", 0) > 0.3:
            rec = Recommendation(
                id=f"error_prev_{int(time.time())}",
                type=RecommendationType.ERROR_PREVENTION,
                priority="high",
                title="High Error Pattern Density Detected",
                description="Multiple error patterns found in historical context. Exercise extra caution.",
                rationale=f"Error ratio: {enriched_context.analysis_summary.get('error_ratio', 0):.2f}",
                supporting_memories=[m.id for m in memory_context.error_memories[:3]],
                confidence=0.8,
                estimated_impact="high",
                implementation_effort="low",
                tags=["error_prevention", "caution", "patterns"],
                created_at=time.time()
            )
            recommendations.append(rec)
        
        return recommendations[:self.config.max_recommendations_per_type]
    
    def _generate_performance_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate performance optimization recommendations."""
        recommendations = []
        memory_context = enriched_context.memory_context
        
        # Analyze performance memories
        if memory_context.performance_memories:
            perf_patterns = self._analyze_performance_patterns(memory_context.performance_memories)
            
            for pattern in perf_patterns:
                if pattern["impact_score"] >= 0.7:
                    rec = self._create_performance_recommendation(pattern, memory_context)
                    if rec:
                        recommendations.append(rec)
        
        # Check for performance indicators in operation context
        operation_type = memory_context.operation_type.lower()
        
        if operation_type in ["deploy", "publish"] and memory_context.performance_memories:
            rec = Recommendation(
                id=f"perf_opt_{int(time.time())}",
                type=RecommendationType.PERFORMANCE_OPT,
                priority="medium",
                title=f"Performance Optimization Available for {operation_type.title()}",
                description=f"Historical performance optimizations found for {operation_type} operations.",
                rationale=f"Found {len(memory_context.performance_memories)} performance memories",
                supporting_memories=[m.id for m in memory_context.performance_memories[:3]],
                confidence=0.7,
                estimated_impact="medium",
                implementation_effort="medium",
                tags=["performance", operation_type, "optimization"],
                created_at=time.time()
            )
            recommendations.append(rec)
        
        return recommendations[:self.config.max_recommendations_per_type]
    
    def _generate_workflow_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate workflow improvement recommendations."""
        recommendations = []
        memory_context = enriched_context.memory_context
        
        # Analyze workflow patterns from team memories
        team_memories = [m for m in memory_context.relevant_memories 
                        if m.category == MemoryCategory.TEAM]
        
        if team_memories:
            workflow_patterns = self._analyze_workflow_patterns(team_memories)
            
            for pattern in workflow_patterns:
                if pattern["adoption_score"] >= 0.6:
                    rec = self._create_workflow_recommendation(pattern, memory_context)
                    if rec:
                        recommendations.append(rec)
        
        # Generate recommendations based on success patterns
        if enriched_context.analysis_summary.get("success_ratio", 0) > 0.5:
            rec = Recommendation(
                id=f"workflow_success_{int(time.time())}",
                type=RecommendationType.WORKFLOW_IMPROVEMENT,
                priority="medium",
                title="Apply Successful Operation Patterns",
                description="High success ratio detected in historical operations. Consider applying successful patterns.",
                rationale=f"Success ratio: {enriched_context.analysis_summary.get('success_ratio', 0):.2f}",
                supporting_memories=[m.id for m in memory_context.pattern_memories[:3]],
                confidence=0.75,
                estimated_impact="medium",
                implementation_effort="low",
                tags=["workflow", "success_patterns", "best_practices"],
                created_at=time.time()
            )
            recommendations.append(rec)
        
        return recommendations[:self.config.max_recommendations_per_type]
    
    def _generate_context_specific_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate recommendations specific to the context type."""
        recommendations = []
        
        if enriched_context.context_type == ContextType.AGENT_OPERATION:
            recommendations.extend(self._generate_agent_operation_recommendations(enriched_context))
        elif enriched_context.context_type == ContextType.WORKFLOW_COMMAND:
            recommendations.extend(self._generate_workflow_command_recommendations(enriched_context))
        elif enriched_context.context_type == ContextType.ERROR_RESOLUTION:
            recommendations.extend(self._generate_error_resolution_recommendations(enriched_context))
        elif enriched_context.context_type == ContextType.DECISION_SUPPORT:
            recommendations.extend(self._generate_decision_support_recommendations(enriched_context))
        elif enriched_context.context_type == ContextType.PERFORMANCE_OPT:
            recommendations.extend(self._generate_performance_context_recommendations(enriched_context))
        
        return recommendations
    
    def _generate_agent_operation_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate recommendations for agent operations."""
        recommendations = []
        memory_context = enriched_context.memory_context
        
        # Agent-specific recommendations based on patterns
        agent_type = enriched_context.original_context.get("agent_type", "unknown")
        
        if memory_context.pattern_memories:
            rec = Recommendation(
                id=f"agent_pattern_{int(time.time())}",
                type=RecommendationType.OPERATION_GUIDANCE,
                priority="medium",
                title=f"Apply {agent_type} Agent Best Practices",
                description=f"Successful patterns found for {agent_type} agent operations.",
                rationale=f"Found {len(memory_context.pattern_memories)} relevant patterns",
                supporting_memories=[m.id for m in memory_context.pattern_memories[:3]],
                confidence=0.7,
                estimated_impact="medium",
                implementation_effort="low",
                tags=["agent_operation", agent_type, "patterns"],
                created_at=time.time()
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_workflow_command_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate recommendations for workflow commands."""
        recommendations = []
        memory_context = enriched_context.memory_context
        operation_type = memory_context.operation_type.lower()
        
        # Command-specific recommendations
        if operation_type == "push":
            if memory_context.error_memories:
                rec = Recommendation(
                    id=f"push_safety_{int(time.time())}",
                    type=RecommendationType.ERROR_PREVENTION,
                    priority="high",
                    title="Ensure Pre-Push Validation",
                    description="Error history detected for push operations. Ensure all quality gates pass.",
                    rationale=f"Found {len(memory_context.error_memories)} push-related errors",
                    supporting_memories=[m.id for m in memory_context.error_memories[:2]],
                    confidence=0.8,
                    estimated_impact="high",
                    implementation_effort="low",
                    tags=["push", "quality_gates", "validation"],
                    created_at=time.time()
                )
                recommendations.append(rec)
        
        elif operation_type == "deploy":
            if memory_context.performance_memories:
                rec = Recommendation(
                    id=f"deploy_perf_{int(time.time())}",
                    type=RecommendationType.PERFORMANCE_OPT,
                    priority="medium",
                    title="Monitor Deployment Performance",
                    description="Performance optimization history available for deployment operations.",
                    rationale=f"Found {len(memory_context.performance_memories)} performance insights",
                    supporting_memories=[m.id for m in memory_context.performance_memories[:2]],
                    confidence=0.7,
                    estimated_impact="medium",
                    implementation_effort="low",
                    tags=["deploy", "performance", "monitoring"],
                    created_at=time.time()
                )
                recommendations.append(rec)
        
        elif operation_type == "publish":
            rec = Recommendation(
                id=f"publish_quality_{int(time.time())}",
                type=RecommendationType.OPERATION_GUIDANCE,
                priority="high",
                title="Verify Publication Requirements",
                description="Ensure version increment, documentation, and package integrity before publishing.",
                rationale="Best practice for publication operations",
                supporting_memories=[],
                confidence=0.9,
                estimated_impact="high",
                implementation_effort="low",
                tags=["publish", "quality", "requirements"],
                created_at=time.time()
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_error_resolution_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate recommendations for error resolution."""
        recommendations = []
        memory_context = enriched_context.memory_context
        
        # Find similar errors and their resolutions
        error_type = enriched_context.original_context.get("error_type", "")
        
        similar_errors = [
            memory for memory in memory_context.error_memories
            if error_type.lower() in memory.content.lower()
        ]
        
        if similar_errors:
            rec = Recommendation(
                id=f"error_resolution_{int(time.time())}",
                type=RecommendationType.OPERATION_GUIDANCE,
                priority="high",
                title=f"Apply Previous Resolution for {error_type}",
                description="Similar error patterns found with resolution history.",
                rationale=f"Found {len(similar_errors)} similar error resolutions",
                supporting_memories=[m.id for m in similar_errors[:3]],
                confidence=0.8,
                estimated_impact="high",
                implementation_effort="medium",
                tags=["error_resolution", error_type.lower(), "patterns"],
                created_at=time.time()
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_decision_support_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate recommendations for decision support."""
        recommendations = []
        memory_context = enriched_context.memory_context
        
        # Analyze decision memories for patterns
        if memory_context.decision_memories:
            positive_decisions = [
                memory for memory in memory_context.decision_memories
                if any(word in memory.content.lower() for word in ["successful", "effective", "good"])
            ]
            
            if positive_decisions:
                rec = Recommendation(
                    id=f"decision_pattern_{int(time.time())}",
                    type=RecommendationType.DECISION_SUPPORT,
                    priority="high",
                    title="Apply Successful Decision Patterns",
                    description="Historical successful decisions found for similar contexts.",
                    rationale=f"Found {len(positive_decisions)} successful decision patterns",
                    supporting_memories=[m.id for m in positive_decisions[:3]],
                    confidence=0.8,
                    estimated_impact="high",
                    implementation_effort="medium",
                    tags=["decision_support", "successful_patterns"],
                    created_at=time.time()
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_performance_context_recommendations(
        self,
        enriched_context: EnrichedContext
    ) -> List[Recommendation]:
        """Generate recommendations for performance optimization context."""
        recommendations = []
        memory_context = enriched_context.memory_context
        
        # Performance-specific recommendations
        current_performance = enriched_context.original_context.get("current_performance", "")
        target_performance = enriched_context.original_context.get("target_performance", "")
        
        if memory_context.performance_memories:
            optimization_approaches = [
                memory for memory in memory_context.performance_memories
                if any(word in memory.content.lower() for word in ["faster", "optimized", "improved"])
            ]
            
            if optimization_approaches:
                rec = Recommendation(
                    id=f"perf_approach_{int(time.time())}",
                    type=RecommendationType.PERFORMANCE_OPT,
                    priority="high",
                    title="Apply Proven Optimization Approaches",
                    description="Historical performance optimizations found for similar scenarios.",
                    rationale=f"Found {len(optimization_approaches)} optimization approaches",
                    supporting_memories=[m.id for m in optimization_approaches[:3]],
                    confidence=0.8,
                    estimated_impact="high",
                    implementation_effort="medium",
                    tags=["performance", "optimization", "proven_approaches"],
                    created_at=time.time()
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _analyze_error_patterns(self, error_memories: List[MemoryItem]) -> List[Dict[str, Any]]:
        """Analyze error memories for patterns."""
        patterns = []
        
        if not error_memories:
            return patterns
        
        # Group by error types
        error_groups = defaultdict(list)
        
        for memory in error_memories:
            # Extract error keywords
            error_keywords = self._extract_error_keywords(memory.content)
            
            for keyword in error_keywords:
                error_groups[keyword].append(memory)
        
        # Analyze each group
        for error_type, memories in error_groups.items():
            if len(memories) >= 2:  # Minimum pattern threshold
                pattern = {
                    "error_type": error_type,
                    "frequency": len(memories),
                    "memories": [m.id for m in memories],
                    "confidence": min(0.9, len(memories) * 0.2),
                    "recent_occurrences": len([
                        m for m in memories 
                        if m.get_age_seconds() < (30 * 24 * 3600)  # Last 30 days
                    ])
                }
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p["frequency"], reverse=True)
    
    def _analyze_performance_patterns(self, perf_memories: List[MemoryItem]) -> List[Dict[str, Any]]:
        """Analyze performance memories for optimization patterns."""
        patterns = []
        
        if not perf_memories:
            return patterns
        
        # Group by performance improvement types
        perf_groups = defaultdict(list)
        
        for memory in perf_memories:
            # Extract performance keywords
            perf_keywords = self._extract_performance_keywords(memory.content)
            
            for keyword in perf_keywords:
                perf_groups[keyword].append(memory)
        
        # Analyze each group
        for perf_type, memories in perf_groups.items():
            if len(memories) >= 1:
                impact_score = self._calculate_performance_impact(memories)
                
                pattern = {
                    "optimization_type": perf_type,
                    "frequency": len(memories),
                    "memories": [m.id for m in memories],
                    "impact_score": impact_score,
                    "implementation_complexity": self._estimate_implementation_complexity(memories)
                }
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p["impact_score"], reverse=True)
    
    def _analyze_workflow_patterns(self, team_memories: List[MemoryItem]) -> List[Dict[str, Any]]:
        """Analyze team memories for workflow patterns."""
        patterns = []
        
        if not team_memories:
            return patterns
        
        # Group by workflow types
        workflow_groups = defaultdict(list)
        
        for memory in team_memories:
            # Extract workflow keywords
            workflow_keywords = self._extract_workflow_keywords(memory.content)
            
            for keyword in workflow_keywords:
                workflow_groups[keyword].append(memory)
        
        # Analyze each group
        for workflow_type, memories in workflow_groups.items():
            if len(memories) >= 1:
                adoption_score = self._calculate_adoption_score(memories)
                
                pattern = {
                    "workflow_type": workflow_type,
                    "frequency": len(memories),
                    "memories": [m.id for m in memories],
                    "adoption_score": adoption_score,
                    "effectiveness": self._estimate_workflow_effectiveness(memories)
                }
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p["adoption_score"], reverse=True)
    
    def _create_error_prevention_recommendation(
        self,
        pattern: Dict[str, Any],
        memory_context: MemoryContext
    ) -> Optional[Recommendation]:
        """Create error prevention recommendation from pattern."""
        error_type = pattern["error_type"]
        frequency = pattern["frequency"]
        
        if frequency < 2:
            return None
        
        priority = "high" if frequency >= 3 else "medium"
        
        return Recommendation(
            id=f"error_prev_{error_type}_{int(time.time())}",
            type=RecommendationType.ERROR_PREVENTION,
            priority=priority,
            title=f"Prevent {error_type.title()} Errors",
            description=f"Pattern detected: {error_type} errors occur frequently. Implement prevention measures.",
            rationale=f"Occurred {frequency} times in recent history",
            supporting_memories=pattern["memories"],
            confidence=pattern["confidence"],
            estimated_impact="high" if frequency >= 3 else "medium",
            implementation_effort="medium",
            tags=["error_prevention", error_type, "pattern"],
            created_at=time.time()
        )
    
    def _create_performance_recommendation(
        self,
        pattern: Dict[str, Any],
        memory_context: MemoryContext
    ) -> Optional[Recommendation]:
        """Create performance recommendation from pattern."""
        opt_type = pattern["optimization_type"]
        impact = pattern["impact_score"]
        
        if impact < 0.5:
            return None
        
        priority = "high" if impact >= 0.8 else "medium"
        
        return Recommendation(
            id=f"perf_opt_{opt_type}_{int(time.time())}",
            type=RecommendationType.PERFORMANCE_OPT,
            priority=priority,
            title=f"Apply {opt_type.title()} Optimization",
            description=f"Performance improvement opportunity: {opt_type} optimization available.",
            rationale=f"Estimated impact score: {impact:.2f}",
            supporting_memories=pattern["memories"],
            confidence=min(0.9, impact),
            estimated_impact="high" if impact >= 0.8 else "medium",
            implementation_effort=pattern["implementation_complexity"],
            tags=["performance", opt_type, "optimization"],
            created_at=time.time()
        )
    
    def _create_workflow_recommendation(
        self,
        pattern: Dict[str, Any],
        memory_context: MemoryContext
    ) -> Optional[Recommendation]:
        """Create workflow recommendation from pattern."""
        workflow_type = pattern["workflow_type"]
        adoption = pattern["adoption_score"]
        
        if adoption < 0.5:
            return None
        
        priority = "medium" if adoption >= 0.7 else "low"
        
        return Recommendation(
            id=f"workflow_{workflow_type}_{int(time.time())}",
            type=RecommendationType.WORKFLOW_IMPROVEMENT,
            priority=priority,
            title=f"Adopt {workflow_type.title()} Workflow",
            description=f"Workflow improvement: {workflow_type} practices show good adoption.",
            rationale=f"Adoption score: {adoption:.2f}",
            supporting_memories=pattern["memories"],
            confidence=adoption,
            estimated_impact="medium",
            implementation_effort="medium",
            tags=["workflow", workflow_type, "improvement"],
            created_at=time.time()
        )
    
    def _filter_and_rank_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """Filter and rank recommendations by quality and relevance."""
        # Filter by confidence threshold
        filtered = [
            rec for rec in recommendations 
            if rec.confidence >= self.config.min_confidence_threshold
        ]
        
        # Remove duplicates (same type and similar content)
        deduplicated = self._deduplicate_recommendations(filtered)
        
        # Rank by score
        ranked = sorted(deduplicated, key=lambda r: r.get_score(), reverse=True)
        
        # Update statistics
        for rec in ranked:
            self.generation_stats["recommendations_by_type"][rec.type.value] += 1
        
        return ranked
    
    def _deduplicate_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """Remove duplicate recommendations."""
        unique_recs = []
        seen_combinations = set()
        
        for rec in recommendations:
            # Create a signature for the recommendation
            signature = (rec.type.value, rec.title.lower()[:50])
            
            if signature not in seen_combinations:
                unique_recs.append(rec)
                seen_combinations.add(signature)
        
        return unique_recs
    
    def _extract_error_keywords(self, content: str) -> List[str]:
        """Extract error-related keywords from content."""
        error_terms = [
            "timeout", "connection", "authentication", "permission", "syntax",
            "runtime", "compile", "build", "test", "deployment", "memory",
            "disk", "network", "database", "api", "service", "configuration"
        ]
        
        content_lower = content.lower()
        found_terms = [term for term in error_terms if term in content_lower]
        
        return found_terms
    
    def _extract_performance_keywords(self, content: str) -> List[str]:
        """Extract performance-related keywords from content."""
        perf_terms = [
            "caching", "indexing", "optimization", "compression", "parallel",
            "async", "batch", "streaming", "memory", "cpu", "disk", "network",
            "database", "query", "algorithm", "data_structure"
        ]
        
        content_lower = content.lower()
        found_terms = [term for term in perf_terms if term in content_lower]
        
        return found_terms
    
    def _extract_workflow_keywords(self, content: str) -> List[str]:
        """Extract workflow-related keywords from content."""
        workflow_terms = [
            "testing", "code_review", "documentation", "deployment", "monitoring",
            "logging", "error_handling", "validation", "automation", "ci_cd",
            "git_workflow", "branching", "merging", "release", "staging"
        ]
        
        content_lower = content.lower()
        found_terms = [term for term in workflow_terms if term in content_lower]
        
        return found_terms
    
    def _calculate_performance_impact(self, memories: List[MemoryItem]) -> float:
        """Calculate estimated performance impact score."""
        impact_indicators = ["faster", "optimized", "improved", "reduced", "efficient"]
        
        total_score = 0.0
        
        for memory in memories:
            content_lower = memory.content.lower()
            memory_score = 0.0
            
            for indicator in impact_indicators:
                if indicator in content_lower:
                    memory_score += 0.2
            
            # Age weighting (newer is better for performance)
            age_days = memory.get_age_seconds() / (24 * 3600)
            age_weight = max(0.1, 1.0 - age_days * 0.01)
            
            total_score += memory_score * age_weight
        
        return min(1.0, total_score / len(memories))
    
    def _estimate_implementation_complexity(self, memories: List[MemoryItem]) -> str:
        """Estimate implementation complexity from memories."""
        complexity_indicators = {
            "low": ["simple", "easy", "quick", "straightforward"],
            "medium": ["moderate", "some_effort", "careful"],
            "high": ["complex", "difficult", "major", "significant", "architectural"]
        }
        
        complexity_scores = {"low": 0, "medium": 0, "high": 0}
        
        for memory in memories:
            content_lower = memory.content.lower()
            
            for complexity, indicators in complexity_indicators.items():
                for indicator in indicators:
                    if indicator in content_lower:
                        complexity_scores[complexity] += 1
        
        # Return the complexity with the highest score
        max_complexity = max(complexity_scores.items(), key=lambda x: x[1])
        return max_complexity[0] if max_complexity[1] > 0 else "medium"
    
    def _calculate_adoption_score(self, memories: List[MemoryItem]) -> float:
        """Calculate workflow adoption score."""
        adoption_indicators = ["adopted", "using", "implemented", "standard", "practice"]
        
        total_score = 0.0
        
        for memory in memories:
            content_lower = memory.content.lower()
            memory_score = 0.0
            
            for indicator in adoption_indicators:
                if indicator in content_lower:
                    memory_score += 0.2
            
            total_score += memory_score
        
        return min(1.0, total_score / len(memories))
    
    def _estimate_workflow_effectiveness(self, memories: List[MemoryItem]) -> str:
        """Estimate workflow effectiveness from memories."""
        effectiveness_indicators = {
            "high": ["effective", "successful", "improved", "better"],
            "medium": ["moderate", "adequate", "acceptable"],
            "low": ["ineffective", "problematic", "issues"]
        }
        
        effectiveness_scores = {"high": 0, "medium": 0, "low": 0}
        
        for memory in memories:
            content_lower = memory.content.lower()
            
            for effectiveness, indicators in effectiveness_indicators.items():
                for indicator in indicators:
                    if indicator in content_lower:
                        effectiveness_scores[effectiveness] += 1
        
        # Return the effectiveness with the highest score
        max_effectiveness = max(effectiveness_scores.items(), key=lambda x: x[1])
        return max_effectiveness[0] if max_effectiveness[1] > 0 else "medium"
    
    def _initialize_success_patterns(self) -> Dict[str, Any]:
        """Initialize success pattern database."""
        return {
            "operation_patterns": {
                "push": ["tests_pass", "documentation_updated", "linting_clean"],
                "deploy": ["environment_validated", "dependencies_checked", "health_verified"],
                "publish": ["version_incremented", "package_validated", "registry_accessible"]
            },
            "quality_indicators": ["successful", "completed", "working", "tested", "validated"]
        }
    
    def _initialize_error_patterns(self) -> Dict[str, Any]:
        """Initialize error pattern database."""
        return {
            "common_errors": {
                "timeout": ["network", "service", "database", "api"],
                "permission": ["access", "authentication", "authorization"],
                "configuration": ["missing", "invalid", "incorrect"]
            },
            "error_indicators": ["error", "failure", "exception", "crash", "timeout"]
        }
    
    def _initialize_performance_patterns(self) -> Dict[str, Any]:
        """Initialize performance pattern database."""
        return {
            "optimization_types": {
                "caching": ["memory", "disk", "distributed"],
                "database": ["indexing", "query", "connection"],
                "network": ["compression", "batching", "cdn"]
            },
            "performance_indicators": ["faster", "optimized", "efficient", "reduced", "improved"]
        }
    
    def _initialize_workflow_patterns(self) -> Dict[str, Any]:
        """Initialize workflow pattern database."""
        return {
            "workflow_types": {
                "testing": ["unit", "integration", "e2e", "automated"],
                "deployment": ["staging", "production", "rollback", "monitoring"],
                "development": ["git_flow", "code_review", "documentation"]
            },
            "workflow_indicators": ["process", "workflow", "practice", "standard", "guideline"]
        }
    
    def _initialize_recommendation_templates(self) -> Dict[str, str]:
        """Initialize recommendation templates."""
        return {
            "error_prevention": "Prevent {error_type} errors by implementing {solution}",
            "performance_opt": "Improve performance by applying {optimization_type} optimization",
            "workflow_improvement": "Enhance workflow by adopting {workflow_type} practices",
            "operation_guidance": "Follow best practices for {operation_type} operations",
            "decision_support": "Consider {decision_factor} when making {decision_type} decisions"
        }
    
    def _update_generation_stats(self, processing_time_ms: float, success: bool, rec_count: int):
        """Update generation statistics."""
        if success:
            self.generation_stats["successful_generations"] += 1
            self.generation_stats["total_recommendations_generated"] += rec_count
        else:
            self.generation_stats["failed_generations"] += 1
        
        # Update average generation time
        total_generations = self.generation_stats["total_generations"]
        current_avg = self.generation_stats["average_generation_time_ms"]
        
        self.generation_stats["average_generation_time_ms"] = (
            (current_avg * (total_generations - 1) + processing_time_ms) / total_generations
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.generation_stats.copy()
        
        # Add success rate
        total_generations = self.generation_stats["total_generations"]
        if total_generations > 0:
            stats["success_rate"] = (self.generation_stats["successful_generations"] / total_generations) * 100
            stats["average_recommendations_per_generation"] = (
                self.generation_stats["total_recommendations_generated"] / total_generations
            )
        else:
            stats["success_rate"] = 0.0
            stats["average_recommendations_per_generation"] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.generation_stats = {
            "total_generations": 0,
            "generations_by_type": {ctx_type.value: 0 for ctx_type in ContextType},
            "recommendations_by_type": {rec_type.value: 0 for rec_type in RecommendationType},
            "average_generation_time_ms": 0.0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_recommendations_generated": 0
        }
    
    def get_config(self) -> RecommendationConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, config: RecommendationConfig):
        """
        Update configuration.
        
        Args:
            config: New configuration
        """
        config.validate()
        self.config = config
        self.logger.info("Recommendation engine configuration updated")