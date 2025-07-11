"""
Context Builder

This module implements context enrichment with relevant memories. It builds
enhanced operation contexts by intelligently combining current operation data
with historical memories, patterns, and recommendations to provide agents
with comprehensive decision-making context.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from .interfaces.models import MemoryItem, MemoryCategory
from .memory_context_enhancer import MemoryContext, RecallTrigger
from .similarity_matcher import SimilarityMatcher, SimilarityResult


class ContextType(str, Enum):
    """Types of contexts that can be built."""
    
    AGENT_OPERATION = "agent_operation"     # Context for agent operations
    WORKFLOW_COMMAND = "workflow_command"   # Context for push/deploy/publish
    ERROR_RESOLUTION = "error_resolution"   # Context for error handling
    DECISION_SUPPORT = "decision_support"   # Context for strategic decisions
    PERFORMANCE_OPT = "performance_opt"     # Context for performance optimization


@dataclass
class ContextTemplate:
    """Template for building specific types of contexts."""
    
    context_type: ContextType
    required_fields: List[str]
    optional_fields: List[str]
    memory_categories: List[MemoryCategory]
    max_memories_per_category: int
    similarity_threshold: float
    include_patterns: bool
    include_recommendations: bool
    
    def validate_context(self, context_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that context data meets template requirements.
        
        Args:
            context_data: Context data to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, missing_fields)
        """
        missing_fields = []
        
        for field in self.required_fields:
            if field not in context_data:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields


@dataclass
class EnrichedContext:
    """Enhanced context with memories and analysis."""
    
    context_type: ContextType
    original_context: Dict[str, Any]
    memory_context: MemoryContext
    enriched_data: Dict[str, Any]
    analysis_summary: Dict[str, Any]
    recommendations: List[str]
    warnings: List[str]
    confidence_score: float
    build_timestamp: float
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "context_type": self.context_type.value,
            "original_context": self.original_context,
            "memory_context": {
                "operation_type": self.memory_context.operation_type,
                "recall_trigger": self.memory_context.recall_trigger.value,
                "total_memories": self.memory_context.get_total_memories(),
                "memory_categories": self.memory_context.get_memory_categories(),
                "top_recommendations": self.memory_context.get_top_recommendations(3)
            },
            "enriched_data": self.enriched_data,
            "analysis_summary": self.analysis_summary,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "confidence_score": self.confidence_score,
            "build_timestamp": self.build_timestamp,
            "processing_time_ms": self.processing_time_ms
        }
    
    def get_agent_context(self) -> Dict[str, Any]:
        """Get context formatted for agent consumption."""
        return {
            "operation_context": self.original_context,
            "relevant_memories": [
                {
                    "content": memory.content[:200] + "..." if len(memory.content) > 200 else memory.content,
                    "category": memory.category.value,
                    "tags": memory.tags,
                    "age_days": int(memory.get_age_seconds() / (24 * 3600))
                }
                for memory in self.memory_context.relevant_memories[:5]
            ],
            "pattern_insights": [
                {
                    "content": memory.content[:150] + "..." if len(memory.content) > 150 else memory.content,
                    "success_indicator": "successful" in memory.content.lower()
                }
                for memory in self.memory_context.pattern_memories[:3]
            ],
            "error_prevention": [
                {
                    "content": memory.content[:150] + "..." if len(memory.content) > 150 else memory.content,
                    "severity": "high" if any(word in memory.content.lower() 
                                           for word in ["critical", "failure", "error"])
                                     else "medium"
                }
                for memory in self.memory_context.error_memories[:3]
            ],
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "confidence": self.confidence_score
        }


class ContextBuilder:
    """
    Context enrichment with relevant memories.
    
    This class builds enhanced operation contexts by combining current operation
    data with historical memories, patterns, and intelligent analysis to provide
    agents with comprehensive context for decision-making.
    """
    
    def __init__(self, similarity_matcher: SimilarityMatcher):
        """
        Initialize the context builder.
        
        Args:
            similarity_matcher: Similarity matcher for memory ranking
        """
        self.similarity_matcher = similarity_matcher
        self.logger = logging.getLogger(__name__)
        
        # Context templates for different types of operations
        self.context_templates = self._initialize_context_templates()
        
        # Performance tracking
        self.build_stats = {
            "total_builds": 0,
            "builds_by_type": {ctx_type.value: 0 for ctx_type in ContextType},
            "average_build_time_ms": 0.0,
            "successful_builds": 0,
            "failed_builds": 0,
            "template_usage": {},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
        }
        
        # Context analysis patterns
        self.analysis_patterns = {
            "success_indicators": [
                "successful", "completed", "working", "fixed", "resolved",
                "implemented", "deployed", "tested", "validated"
            ],
            "warning_indicators": [
                "careful", "caution", "warning", "issue", "problem",
                "temporary", "workaround", "hack", "todo"
            ],
            "error_indicators": [
                "error", "failure", "exception", "bug", "crash",
                "broken", "failed", "timeout", "connection"
            ],
            "performance_indicators": [
                "slow", "fast", "optimization", "performance", "bottleneck",
                "memory", "cpu", "latency", "throughput"
            ]
        }
    
    def build_context(
        self,
        context_type: ContextType,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        custom_template: Optional[ContextTemplate] = None
    ) -> EnrichedContext:
        """
        Build enriched context with memories and analysis.
        
        Args:
            context_type: Type of context to build
            operation_context: Current operation context
            memory_context: Memory context from recall
            custom_template: Optional custom template to use
            
        Returns:
            EnrichedContext: Enhanced context with memories and analysis
        """
        start_time = time.time()
        self.build_stats["total_builds"] += 1
        self.build_stats["builds_by_type"][context_type.value] += 1
        
        try:
            # Select template
            template = custom_template or self.context_templates.get(context_type)
            if not template:
                raise ValueError(f"No template available for context type: {context_type}")
            
            # Validate context data
            is_valid, missing_fields = template.validate_context(operation_context)
            if not is_valid:
                self.logger.warning(f"Context validation failed for {context_type}: missing {missing_fields}")
            
            # Build enriched context
            enriched_context = self._build_enriched_context(
                context_type, operation_context, memory_context, template
            )
            
            # Update performance stats
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_build_stats(processing_time_ms, True, enriched_context.confidence_score)
            
            enriched_context.processing_time_ms = processing_time_ms
            
            self.logger.info(
                f"Context built for {context_type.value} in {processing_time_ms:.2f}ms "
                f"(confidence: {enriched_context.confidence_score:.2f})"
            )
            
            return enriched_context
            
        except Exception as e:
            # Update error stats
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_build_stats(processing_time_ms, False, 0.0)
            
            self.logger.error(f"Context building failed for {context_type}: {e}")
            
            # Return minimal context on failure
            return EnrichedContext(
                context_type=context_type,
                original_context=operation_context,
                memory_context=memory_context,
                enriched_data={},
                analysis_summary={"error": str(e)},
                recommendations=[],
                warnings=[f"Context building failed: {str(e)}"],
                confidence_score=0.0,
                build_timestamp=time.time(),
                processing_time_ms=processing_time_ms
            )
    
    def _build_enriched_context(
        self,
        context_type: ContextType,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        template: ContextTemplate
    ) -> EnrichedContext:
        """
        Build the enriched context using the template.
        
        Args:
            context_type: Type of context
            operation_context: Current operation context
            memory_context: Memory context from recall
            template: Context template
            
        Returns:
            EnrichedContext: Built context
        """
        # Analyze memories
        analysis_summary = self._analyze_memories(memory_context, template)
        
        # Build enriched data
        enriched_data = self._build_enriched_data(
            operation_context, memory_context, template, analysis_summary
        )
        
        # Generate context-specific recommendations
        recommendations = self._generate_context_recommendations(
            context_type, operation_context, memory_context, analysis_summary
        )
        
        # Generate warnings
        warnings = self._generate_warnings(
            operation_context, memory_context, analysis_summary
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            memory_context, analysis_summary, len(warnings)
        )
        
        return EnrichedContext(
            context_type=context_type,
            original_context=operation_context,
            memory_context=memory_context,
            enriched_data=enriched_data,
            analysis_summary=analysis_summary,
            recommendations=recommendations,
            warnings=warnings,
            confidence_score=confidence_score,
            build_timestamp=time.time(),
            processing_time_ms=0.0  # Will be set by caller
        )
    
    def _analyze_memories(
        self,
        memory_context: MemoryContext,
        template: ContextTemplate
    ) -> Dict[str, Any]:
        """
        Analyze memories to extract insights.
        
        Args:
            memory_context: Memory context to analyze
            template: Context template
            
        Returns:
            Dict[str, Any]: Analysis summary
        """
        all_memories = (
            memory_context.relevant_memories +
            memory_context.pattern_memories +
            memory_context.error_memories +
            memory_context.decision_memories +
            memory_context.performance_memories
        )
        
        analysis = {
            "total_memories": len(all_memories),
            "memory_distribution": memory_context.get_memory_categories(),
            "success_patterns": 0,
            "error_patterns": 0,
            "warning_patterns": 0,
            "performance_patterns": 0,
            "recent_memories": 0,
            "old_memories": 0,
            "confidence_indicators": []
        }
        
        # Analyze memory content patterns
        for memory in all_memories:
            content_lower = memory.content.lower()
            
            # Success patterns
            if any(indicator in content_lower for indicator in self.analysis_patterns["success_indicators"]):
                analysis["success_patterns"] += 1
                analysis["confidence_indicators"].append("success_pattern")
            
            # Error patterns
            if any(indicator in content_lower for indicator in self.analysis_patterns["error_indicators"]):
                analysis["error_patterns"] += 1
                analysis["confidence_indicators"].append("error_pattern")
            
            # Warning patterns
            if any(indicator in content_lower for indicator in self.analysis_patterns["warning_indicators"]):
                analysis["warning_patterns"] += 1
                analysis["confidence_indicators"].append("warning_pattern")
            
            # Performance patterns
            if any(indicator in content_lower for indicator in self.analysis_patterns["performance_indicators"]):
                analysis["performance_patterns"] += 1
                analysis["confidence_indicators"].append("performance_pattern")
            
            # Age analysis
            age_days = memory.get_age_seconds() / (24 * 3600)
            if age_days <= 30:  # Recent memories (last 30 days)
                analysis["recent_memories"] += 1
            elif age_days > 90:  # Old memories (older than 90 days)
                analysis["old_memories"] += 1
        
        # Calculate pattern ratios
        if analysis["total_memories"] > 0:
            analysis["success_ratio"] = analysis["success_patterns"] / analysis["total_memories"]
            analysis["error_ratio"] = analysis["error_patterns"] / analysis["total_memories"]
            analysis["warning_ratio"] = analysis["warning_patterns"] / analysis["total_memories"]
            analysis["recent_ratio"] = analysis["recent_memories"] / analysis["total_memories"]
        else:
            analysis["success_ratio"] = 0.0
            analysis["error_ratio"] = 0.0
            analysis["warning_ratio"] = 0.0
            analysis["recent_ratio"] = 0.0
        
        return analysis
    
    def _build_enriched_data(
        self,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        template: ContextTemplate,
        analysis_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build enriched data combining operation context with memory insights.
        
        Args:
            operation_context: Current operation context
            memory_context: Memory context
            template: Context template
            analysis_summary: Memory analysis
            
        Returns:
            Dict[str, Any]: Enriched data
        """
        enriched_data = operation_context.copy()
        
        # Add memory-derived insights
        enriched_data["memory_insights"] = {
            "total_relevant_memories": memory_context.get_total_memories(),
            "success_patterns_found": analysis_summary["success_patterns"],
            "error_patterns_found": analysis_summary["error_patterns"],
            "recent_experience_available": analysis_summary["recent_memories"] > 0,
            "high_confidence_context": analysis_summary["success_ratio"] > 0.3
        }
        
        # Add pattern-based enrichments
        if template.include_patterns and memory_context.pattern_memories:
            enriched_data["successful_approaches"] = [
                {
                    "approach": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
                    "tags": memory.tags,
                    "category": memory.category.value
                }
                for memory in memory_context.pattern_memories[:3]
            ]
        
        # Add error prevention data
        if memory_context.error_memories:
            enriched_data["error_prevention"] = {
                "known_issues": len(memory_context.error_memories),
                "critical_errors": len([
                    memory for memory in memory_context.error_memories
                    if any(word in memory.content.lower() for word in ["critical", "fatal", "severe"])
                ]),
                "recent_errors": len([
                    memory for memory in memory_context.error_memories
                    if memory.get_age_seconds() < (30 * 24 * 3600)  # Last 30 days
                ])
            }
        
        # Add decision support data
        if memory_context.decision_memories:
            enriched_data["decision_context"] = {
                "historical_decisions": len(memory_context.decision_memories),
                "decision_patterns": [
                    {
                        "decision": memory.content[:80] + "..." if len(memory.content) > 80 else memory.content,
                        "outcome_positive": any(word in memory.content.lower() 
                                              for word in ["successful", "worked", "good", "effective"])
                    }
                    for memory in memory_context.decision_memories[:3]
                ]
            }
        
        # Add performance context
        if memory_context.performance_memories:
            enriched_data["performance_context"] = {
                "optimization_history": len(memory_context.performance_memories),
                "performance_insights": [
                    {
                        "insight": memory.content[:80] + "..." if len(memory.content) > 80 else memory.content,
                        "performance_related": any(word in memory.content.lower() 
                                                 for word in ["fast", "slow", "optimization", "performance"])
                    }
                    for memory in memory_context.performance_memories[:3]
                ]
            }
        
        # Add temporal context
        enriched_data["temporal_context"] = {
            "operation_timestamp": time.time(),
            "has_recent_experience": analysis_summary["recent_ratio"] > 0.2,
            "experience_age_distribution": {
                "recent": analysis_summary["recent_memories"],
                "moderate": analysis_summary["total_memories"] - analysis_summary["recent_memories"] - analysis_summary["old_memories"],
                "old": analysis_summary["old_memories"]
            }
        }
        
        return enriched_data
    
    def _generate_context_recommendations(
        self,
        context_type: ContextType,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        analysis_summary: Dict[str, Any]
    ) -> List[str]:
        """
        Generate context-specific recommendations.
        
        Args:
            context_type: Type of context
            operation_context: Operation context
            memory_context: Memory context
            analysis_summary: Analysis summary
            
        Returns:
            List[str]: Context-specific recommendations
        """
        recommendations = []
        
        # Add memory-based recommendations
        recommendations.extend(memory_context.recommendations[:5])
        
        # Add context-specific recommendations
        if context_type == ContextType.AGENT_OPERATION:
            recommendations.extend(self._get_agent_operation_recommendations(
                operation_context, memory_context, analysis_summary
            ))
        elif context_type == ContextType.WORKFLOW_COMMAND:
            recommendations.extend(self._get_workflow_command_recommendations(
                operation_context, memory_context, analysis_summary
            ))
        elif context_type == ContextType.ERROR_RESOLUTION:
            recommendations.extend(self._get_error_resolution_recommendations(
                operation_context, memory_context, analysis_summary
            ))
        elif context_type == ContextType.DECISION_SUPPORT:
            recommendations.extend(self._get_decision_support_recommendations(
                operation_context, memory_context, analysis_summary
            ))
        elif context_type == ContextType.PERFORMANCE_OPT:
            recommendations.extend(self._get_performance_optimization_recommendations(
                operation_context, memory_context, analysis_summary
            ))
        
        # Remove duplicates and limit
        return list(dict.fromkeys(recommendations))[:10]
    
    def _get_agent_operation_recommendations(
        self,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        analysis_summary: Dict[str, Any]
    ) -> List[str]:
        """Get recommendations for agent operations."""
        recommendations = []
        
        if analysis_summary["success_patterns"] > 0:
            recommendations.append("Apply successful patterns from similar operations")
        
        if analysis_summary["error_patterns"] > 2:
            recommendations.append("Exercise caution - multiple error patterns detected")
        
        if analysis_summary["recent_ratio"] > 0.5:
            recommendations.append("Leverage recent experience for this operation")
        
        return recommendations
    
    def _get_workflow_command_recommendations(
        self,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        analysis_summary: Dict[str, Any]
    ) -> List[str]:
        """Get recommendations for workflow commands (push/deploy/publish)."""
        recommendations = []
        
        operation_type = memory_context.operation_type.lower()
        
        if operation_type == "push":
            if analysis_summary["error_patterns"] > 0:
                recommendations.append("Run thorough tests before pushing - errors detected in history")
            recommendations.append("Verify all quality gates pass before push")
        
        elif operation_type == "deploy":
            if analysis_summary["performance_patterns"] > 0:
                recommendations.append("Monitor performance during deployment - optimization history available")
            recommendations.append("Verify environment configuration before deployment")
        
        elif operation_type == "publish":
            recommendations.append("Ensure version increment and documentation are complete")
            if analysis_summary["error_patterns"] > 0:
                recommendations.append("Double-check package integrity - publication errors detected in history")
        
        return recommendations
    
    def _get_error_resolution_recommendations(
        self,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        analysis_summary: Dict[str, Any]
    ) -> List[str]:
        """Get recommendations for error resolution."""
        recommendations = []
        
        if memory_context.error_memories:
            recommendations.append("Review similar error resolutions from memory")
            
            # Look for specific error patterns
            for memory in memory_context.error_memories[:3]:
                if "solution" in memory.content.lower() or "fix" in memory.content.lower():
                    recommendations.append(f"Consider approach: {memory.content[:50]}...")
        
        if analysis_summary["success_ratio"] > 0.3:
            recommendations.append("Apply successful resolution patterns from history")
        
        return recommendations
    
    def _get_decision_support_recommendations(
        self,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        analysis_summary: Dict[str, Any]
    ) -> List[str]:
        """Get recommendations for decision support."""
        recommendations = []
        
        if memory_context.decision_memories:
            recommendations.append("Consider historical decision outcomes in similar contexts")
            
            # Analyze decision outcomes
            positive_decisions = [
                memory for memory in memory_context.decision_memories
                if any(word in memory.content.lower() for word in ["successful", "effective", "good"])
            ]
            
            if positive_decisions:
                recommendations.append("Favor approaches similar to historically successful decisions")
        
        if analysis_summary["warning_ratio"] > 0.2:
            recommendations.append("Proceed with caution - warning patterns detected in history")
        
        return recommendations
    
    def _get_performance_optimization_recommendations(
        self,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        analysis_summary: Dict[str, Any]
    ) -> List[str]:
        """Get recommendations for performance optimization."""
        recommendations = []
        
        if memory_context.performance_memories:
            recommendations.append("Apply performance optimization patterns from history")
            
            # Look for specific optimization approaches
            for memory in memory_context.performance_memories[:3]:
                if any(word in memory.content.lower() for word in ["faster", "optimized", "improved"]):
                    recommendations.append(f"Consider optimization: {memory.content[:50]}...")
        
        if analysis_summary["performance_patterns"] > 2:
            recommendations.append("Extensive performance history available - leverage optimization insights")
        
        return recommendations
    
    def _generate_warnings(
        self,
        operation_context: Dict[str, Any],
        memory_context: MemoryContext,
        analysis_summary: Dict[str, Any]
    ) -> List[str]:
        """
        Generate warnings based on memory analysis.
        
        Args:
            operation_context: Operation context
            memory_context: Memory context
            analysis_summary: Analysis summary
            
        Returns:
            List[str]: Generated warnings
        """
        warnings = []
        
        # Error pattern warnings
        if analysis_summary["error_ratio"] > 0.3:
            warnings.append("High error pattern density detected - proceed with caution")
        
        # Warning pattern warnings
        if analysis_summary["warning_ratio"] > 0.2:
            warnings.append("Multiple warning patterns found in historical context")
        
        # Low success pattern warnings
        if analysis_summary["success_ratio"] < 0.1 and analysis_summary["total_memories"] > 5:
            warnings.append("Limited successful patterns found - consider alternative approaches")
        
        # Old memory warnings
        if analysis_summary["recent_ratio"] < 0.2 and analysis_summary["total_memories"] > 3:
            warnings.append("Most relevant memories are older - verify current applicability")
        
        # Context-specific warnings
        operation_type = memory_context.operation_type.lower()
        
        if operation_type in ["push", "deploy", "publish"]:
            if any("rollback" in memory.content.lower() for memory in memory_context.error_memories):
                warnings.append(f"Previous {operation_type} operations required rollbacks - ensure safety measures")
        
        return warnings[:5]  # Limit to 5 warnings
    
    def _calculate_confidence_score(
        self,
        memory_context: MemoryContext,
        analysis_summary: Dict[str, Any],
        warning_count: int
    ) -> float:
        """
        Calculate confidence score for the enriched context.
        
        Args:
            memory_context: Memory context
            analysis_summary: Analysis summary
            warning_count: Number of warnings generated
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Memory quantity boost
        memory_count = analysis_summary["total_memories"]
        if memory_count > 10:
            confidence += 0.2
        elif memory_count > 5:
            confidence += 0.1
        elif memory_count < 2:
            confidence -= 0.1
        
        # Success pattern boost
        success_ratio = analysis_summary["success_ratio"]
        confidence += success_ratio * 0.3
        
        # Recent memory boost
        recent_ratio = analysis_summary["recent_ratio"]
        confidence += recent_ratio * 0.2
        
        # Error pattern penalty
        error_ratio = analysis_summary["error_ratio"]
        confidence -= error_ratio * 0.2
        
        # Warning penalty
        confidence -= warning_count * 0.05
        
        # Similarity score boost (if available)
        if memory_context.similarity_scores:
            avg_similarity = sum(memory_context.similarity_scores.values()) / len(memory_context.similarity_scores)
            confidence += avg_similarity * 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _initialize_context_templates(self) -> Dict[ContextType, ContextTemplate]:
        """Initialize context templates for different operation types."""
        templates = {}
        
        # Agent Operation Template
        templates[ContextType.AGENT_OPERATION] = ContextTemplate(
            context_type=ContextType.AGENT_OPERATION,
            required_fields=["operation_type", "agent_type"],
            optional_fields=["target_files", "operation_params", "expected_outcome"],
            memory_categories=[MemoryCategory.PATTERN, MemoryCategory.ERROR, MemoryCategory.TEAM],
            max_memories_per_category=5,
            similarity_threshold=0.6,
            include_patterns=True,
            include_recommendations=True
        )
        
        # Workflow Command Template
        templates[ContextType.WORKFLOW_COMMAND] = ContextTemplate(
            context_type=ContextType.WORKFLOW_COMMAND,
            required_fields=["command_type"],
            optional_fields=["branch_name", "environment", "deployment_target"],
            memory_categories=[MemoryCategory.PATTERN, MemoryCategory.ERROR, MemoryCategory.PROJECT],
            max_memories_per_category=7,
            similarity_threshold=0.7,
            include_patterns=True,
            include_recommendations=True
        )
        
        # Error Resolution Template
        templates[ContextType.ERROR_RESOLUTION] = ContextTemplate(
            context_type=ContextType.ERROR_RESOLUTION,
            required_fields=["error_type", "error_message"],
            optional_fields=["stack_trace", "error_context", "attempted_solutions"],
            memory_categories=[MemoryCategory.ERROR, MemoryCategory.PATTERN],
            max_memories_per_category=10,
            similarity_threshold=0.8,
            include_patterns=True,
            include_recommendations=True
        )
        
        # Decision Support Template
        templates[ContextType.DECISION_SUPPORT] = ContextTemplate(
            context_type=ContextType.DECISION_SUPPORT,
            required_fields=["decision_type", "decision_context"],
            optional_fields=["alternatives", "constraints", "success_criteria"],
            memory_categories=[MemoryCategory.PROJECT, MemoryCategory.PATTERN, MemoryCategory.TEAM],
            max_memories_per_category=8,
            similarity_threshold=0.7,
            include_patterns=True,
            include_recommendations=True
        )
        
        # Performance Optimization Template
        templates[ContextType.PERFORMANCE_OPT] = ContextTemplate(
            context_type=ContextType.PERFORMANCE_OPT,
            required_fields=["performance_metric", "current_performance"],
            optional_fields=["target_performance", "optimization_area", "constraints"],
            memory_categories=[MemoryCategory.PATTERN, MemoryCategory.PROJECT],
            max_memories_per_category=6,
            similarity_threshold=0.7,
            include_patterns=True,
            include_recommendations=True
        )
        
        return templates
    
    def _update_build_stats(self, processing_time_ms: float, success: bool, confidence: float):
        """Update build statistics."""
        if success:
            self.build_stats["successful_builds"] += 1
            
            # Update confidence distribution
            if confidence >= 0.8:
                self.build_stats["confidence_distribution"]["high"] += 1
            elif confidence >= 0.5:
                self.build_stats["confidence_distribution"]["medium"] += 1
            else:
                self.build_stats["confidence_distribution"]["low"] += 1
        else:
            self.build_stats["failed_builds"] += 1
        
        # Update average build time
        total_builds = self.build_stats["total_builds"]
        current_avg = self.build_stats["average_build_time_ms"]
        
        self.build_stats["average_build_time_ms"] = (
            (current_avg * (total_builds - 1) + processing_time_ms) / total_builds
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.build_stats.copy()
        
        # Add success rate
        total_builds = self.build_stats["total_builds"]
        if total_builds > 0:
            stats["success_rate"] = (self.build_stats["successful_builds"] / total_builds) * 100
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.build_stats = {
            "total_builds": 0,
            "builds_by_type": {ctx_type.value: 0 for ctx_type in ContextType},
            "average_build_time_ms": 0.0,
            "successful_builds": 0,
            "failed_builds": 0,
            "template_usage": {},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
        }
    
    def get_context_template(self, context_type: ContextType) -> Optional[ContextTemplate]:
        """
        Get context template for a specific type.
        
        Args:
            context_type: Type of context template
            
        Returns:
            Optional[ContextTemplate]: Template if available
        """
        return self.context_templates.get(context_type)
    
    def add_context_template(self, template: ContextTemplate):
        """
        Add or update a context template.
        
        Args:
            template: Context template to add
        """
        self.context_templates[template.context_type] = template
        self.logger.info(f"Added context template for {template.context_type.value}")
    
    def get_available_context_types(self) -> List[ContextType]:
        """
        Get list of available context types.
        
        Returns:
            List[ContextType]: Available context types
        """
        return list(self.context_templates.keys())