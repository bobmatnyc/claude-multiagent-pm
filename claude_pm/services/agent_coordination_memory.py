"""
Agent Coordination Memory Patterns
==================================

Specialized memory patterns for agent coordination, handoffs, and collaboration
in the Claude PM Framework. Provides intelligent memory-driven coordination
patterns that learn from successful and failed agent interactions.

Key Features:
- Agent handoff pattern recognition
- Coordination failure analysis
- Success pattern replication
- Performance optimization suggestions
- Context preservation across handoffs
- Learning from coordination patterns

Architecture:
- CoordinationMemoryManager: Central coordination memory management
- HandoffPatternAnalyzer: Analyzes handoff success patterns
- CoordinationLearningEngine: Learns from coordination outcomes
- PerformanceOptimizer: Optimizes coordination based on memory
"""

import asyncio
import logging
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from pathlib import Path
from enum import Enum
import json
import hashlib

from .memory.memory_trigger_service import MemoryTriggerService
from .memory.trigger_orchestrator import TriggerEvent, TriggerResult
from .memory.trigger_types import TriggerType, TriggerPriority
from .memory.interfaces.models import MemoryCategory, MemoryItem


class CoordinationPattern(Enum):
    """Types of coordination patterns."""
    SEQUENTIAL_HANDOFF = "sequential_handoff"
    PARALLEL_EXECUTION = "parallel_execution"
    CONDITIONAL_ROUTING = "conditional_routing"
    ERROR_RECOVERY = "error_recovery"
    CONTEXT_PRESERVATION = "context_preservation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class HandoffQuality(Enum):
    """Quality levels for agent handoffs."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    POOR = "poor"
    FAILED = "failed"


@dataclass
class CoordinationMemoryPattern:
    """Coordination pattern extracted from memory."""
    
    pattern_id: str
    pattern_type: CoordinationPattern
    agents_involved: List[str]
    project_context: str
    success_rate: float
    average_duration: float
    context_preservation_score: float
    performance_impact: float
    usage_frequency: int
    last_used: datetime
    failure_modes: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "agents_involved": self.agents_involved,
            "project_context": self.project_context,
            "success_rate": self.success_rate,
            "average_duration": self.average_duration,
            "context_preservation_score": self.context_preservation_score,
            "performance_impact": self.performance_impact,
            "usage_frequency": self.usage_frequency,
            "last_used": self.last_used.isoformat(),
            "failure_modes": self.failure_modes,
            "success_factors": self.success_factors,
            "optimization_suggestions": self.optimization_suggestions
        }


@dataclass
class HandoffAnalysis:
    """Analysis of agent handoff patterns."""
    
    source_agent: str
    target_agent: str
    handoff_quality: HandoffQuality
    duration: float
    context_transferred: Dict[str, Any]
    context_lost: List[str]
    success_factors: List[str]
    failure_points: List[str]
    performance_metrics: Dict[str, float]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "handoff_quality": self.handoff_quality.value,
            "duration": self.duration,
            "context_transferred": self.context_transferred,
            "context_lost": self.context_lost,
            "success_factors": self.success_factors,
            "failure_points": self.failure_points,
            "performance_metrics": self.performance_metrics,
            "timestamp": self.timestamp.isoformat()
        }


class HandoffPatternAnalyzer:
    """Analyzes handoff patterns from memory."""
    
    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
    
    async def analyze_handoff_patterns(self, 
                                     source_agent: str, 
                                     target_agent: str,
                                     project_name: str = None,
                                     days_back: int = 30) -> HandoffAnalysis:
        """
        Analyze handoff patterns between agents.
        
        Args:
            source_agent: Source agent ID
            target_agent: Target agent ID
            project_name: Optional project name filter
            days_back: Days of history to analyze
            
        Returns:
            Handoff analysis
        """
        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return self._create_default_analysis(source_agent, target_agent)
            
            # Search for handoff memories
            search_query = f"handoff {source_agent} {target_agent}"
            if project_name:
                search_query += f" {project_name}"
            
            memories = await memory_service.search_memories(
                query=search_query,
                filters={
                    "source_agent": source_agent,
                    "target_agent": target_agent,
                    "project_name": project_name
                },
                limit=100
            )
            
            # Filter by time range
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_memories = [
                m for m in memories 
                if datetime.fromisoformat(m.metadata.get("timestamp", "1970-01-01")) >= cutoff_date
            ]
            
            if not recent_memories:
                return self._create_default_analysis(source_agent, target_agent)
            
            # Analyze patterns
            analysis = self._analyze_handoff_memories(recent_memories, source_agent, target_agent)
            
            self.logger.info(f"Analyzed {len(recent_memories)} handoff memories for {source_agent} -> {target_agent}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze handoff patterns: {e}")
            return self._create_default_analysis(source_agent, target_agent)
    
    def _analyze_handoff_memories(self, memories: List[MemoryItem], 
                                source_agent: str, 
                                target_agent: str) -> HandoffAnalysis:
        """Analyze handoff memories to extract patterns."""
        
        # Calculate success rate
        successes = sum(1 for m in memories if m.metadata.get("success", False))
        success_rate = successes / len(memories) if memories else 0.0
        
        # Calculate average duration
        durations = [m.metadata.get("duration", 0) for m in memories]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        # Analyze context preservation
        context_scores = []
        context_lost_items = []
        
        for memory in memories:
            context_data = memory.metadata.get("context_data", {})
            if context_data:
                # Simple context preservation score (could be more sophisticated)
                context_score = len(context_data.get("preserved", [])) / max(1, len(context_data.get("total", [])))
                context_scores.append(context_score)
                context_lost_items.extend(context_data.get("lost", []))
        
        avg_context_score = sum(context_scores) / len(context_scores) if context_scores else 0.0
        
        # Extract success factors and failure points
        success_factors = []
        failure_points = []
        
        for memory in memories:
            if memory.metadata.get("success", False):
                success_factors.extend(memory.metadata.get("success_factors", []))
            else:
                failure_points.extend(memory.metadata.get("failure_points", []))
        
        # Count most common factors
        common_success_factors = [item for item, count in Counter(success_factors).most_common(5)]
        common_failure_points = [item for item, count in Counter(failure_points).most_common(5)]
        
        # Determine handoff quality
        handoff_quality = self._determine_handoff_quality(success_rate, avg_duration, avg_context_score)
        
        # Calculate performance metrics
        performance_metrics = {
            "success_rate": success_rate,
            "average_duration": avg_duration,
            "context_preservation": avg_context_score,
            "handoff_frequency": len(memories),
            "failure_rate": 1.0 - success_rate
        }
        
        return HandoffAnalysis(
            source_agent=source_agent,
            target_agent=target_agent,
            handoff_quality=handoff_quality,
            duration=avg_duration,
            context_transferred={"preserved_rate": avg_context_score},
            context_lost=list(set(context_lost_items)),
            success_factors=common_success_factors,
            failure_points=common_failure_points,
            performance_metrics=performance_metrics,
            timestamp=datetime.now()
        )
    
    def _determine_handoff_quality(self, success_rate: float, duration: float, context_score: float) -> HandoffQuality:
        """Determine handoff quality based on metrics."""
        
        # Weighted quality score
        quality_score = (success_rate * 0.5) + (context_score * 0.3) + (min(1.0, 60.0 / max(1.0, duration)) * 0.2)
        
        if quality_score >= 0.9:
            return HandoffQuality.EXCELLENT
        elif quality_score >= 0.7:
            return HandoffQuality.GOOD
        elif quality_score >= 0.5:
            return HandoffQuality.ADEQUATE
        elif quality_score >= 0.3:
            return HandoffQuality.POOR
        else:
            return HandoffQuality.FAILED
    
    def _create_default_analysis(self, source_agent: str, target_agent: str) -> HandoffAnalysis:
        """Create default analysis when no memory data available."""
        return HandoffAnalysis(
            source_agent=source_agent,
            target_agent=target_agent,
            handoff_quality=HandoffQuality.ADEQUATE,
            duration=30.0,  # Default 30 seconds
            context_transferred={},
            context_lost=[],
            success_factors=[],
            failure_points=[],
            performance_metrics={},
            timestamp=datetime.now()
        )


class CoordinationLearningEngine:
    """Learns from coordination patterns and outcomes."""
    
    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
        self.learned_patterns: Dict[str, CoordinationMemoryPattern] = {}
    
    async def learn_from_coordination(self, 
                                    coordination_context: Dict[str, Any],
                                    outcome: Dict[str, Any]) -> Optional[CoordinationMemoryPattern]:
        """
        Learn from coordination outcome and update patterns.
        
        Args:
            coordination_context: Context of coordination
            outcome: Outcome of coordination
            
        Returns:
            Updated or new coordination pattern
        """
        try:
            # Extract pattern signature
            pattern_signature = self._extract_pattern_signature(coordination_context)
            
            # Check if pattern exists
            pattern_id = hashlib.md5(pattern_signature.encode()).hexdigest()
            
            if pattern_id in self.learned_patterns:
                # Update existing pattern
                pattern = self.learned_patterns[pattern_id]
                pattern = self._update_pattern(pattern, coordination_context, outcome)
            else:
                # Create new pattern
                pattern = self._create_pattern(pattern_id, coordination_context, outcome)
                self.learned_patterns[pattern_id] = pattern
            
            # Store pattern in memory
            await self._store_pattern_memory(pattern)
            
            self.logger.info(f"Learned coordination pattern: {pattern_id}")
            return pattern
            
        except Exception as e:
            self.logger.error(f"Failed to learn from coordination: {e}")
            return None
    
    def _extract_pattern_signature(self, context: Dict[str, Any]) -> str:
        """Extract unique signature for coordination pattern."""
        
        # Key elements that define a coordination pattern
        agents = sorted(context.get("agents_involved", []))
        project_type = context.get("project_type", "unknown")
        workflow_type = context.get("workflow_type", "unknown")
        
        signature = f"{'-'.join(agents)}_{project_type}_{workflow_type}"
        return signature
    
    def _create_pattern(self, pattern_id: str, 
                       context: Dict[str, Any], 
                       outcome: Dict[str, Any]) -> CoordinationMemoryPattern:
        """Create new coordination pattern."""
        
        return CoordinationMemoryPattern(
            pattern_id=pattern_id,
            pattern_type=self._classify_pattern_type(context),
            agents_involved=context.get("agents_involved", []),
            project_context=context.get("project_name", "unknown"),
            success_rate=1.0 if outcome.get("success", False) else 0.0,
            average_duration=outcome.get("duration", 0.0),
            context_preservation_score=outcome.get("context_preservation", 0.0),
            performance_impact=outcome.get("performance_impact", 0.0),
            usage_frequency=1,
            last_used=datetime.now(),
            failure_modes=outcome.get("failure_modes", []),
            success_factors=outcome.get("success_factors", []),
            optimization_suggestions=self._generate_optimization_suggestions(context, outcome)
        )
    
    def _update_pattern(self, pattern: CoordinationMemoryPattern, 
                       context: Dict[str, Any], 
                       outcome: Dict[str, Any]) -> CoordinationMemoryPattern:
        """Update existing coordination pattern."""
        
        # Update metrics with exponential moving average
        alpha = 0.1  # Learning rate
        
        new_success = 1.0 if outcome.get("success", False) else 0.0
        pattern.success_rate = pattern.success_rate * (1 - alpha) + new_success * alpha
        
        new_duration = outcome.get("duration", 0.0)
        pattern.average_duration = pattern.average_duration * (1 - alpha) + new_duration * alpha
        
        new_context_score = outcome.get("context_preservation", 0.0)
        pattern.context_preservation_score = pattern.context_preservation_score * (1 - alpha) + new_context_score * alpha
        
        new_performance = outcome.get("performance_impact", 0.0)
        pattern.performance_impact = pattern.performance_impact * (1 - alpha) + new_performance * alpha
        
        # Update usage frequency and timestamp
        pattern.usage_frequency += 1
        pattern.last_used = datetime.now()
        
        # Update failure modes and success factors
        pattern.failure_modes.extend(outcome.get("failure_modes", []))
        pattern.success_factors.extend(outcome.get("success_factors", []))
        
        # Keep only unique items and limit list size
        pattern.failure_modes = list(set(pattern.failure_modes))[-10:]
        pattern.success_factors = list(set(pattern.success_factors))[-10:]
        
        # Update optimization suggestions
        pattern.optimization_suggestions = self._generate_optimization_suggestions(context, outcome)
        
        return pattern
    
    def _classify_pattern_type(self, context: Dict[str, Any]) -> CoordinationPattern:
        """Classify coordination pattern type."""
        
        workflow_type = context.get("workflow_type", "").lower()
        agents_count = len(context.get("agents_involved", []))
        
        if "parallel" in workflow_type:
            return CoordinationPattern.PARALLEL_EXECUTION
        elif "conditional" in workflow_type or "routing" in workflow_type:
            return CoordinationPattern.CONDITIONAL_ROUTING
        elif "error" in workflow_type or "recovery" in workflow_type:
            return CoordinationPattern.ERROR_RECOVERY
        elif agents_count > 1:
            return CoordinationPattern.SEQUENTIAL_HANDOFF
        else:
            return CoordinationPattern.CONTEXT_PRESERVATION
    
    def _generate_optimization_suggestions(self, context: Dict[str, Any], outcome: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on outcome."""
        
        suggestions = []
        
        # Duration-based suggestions
        duration = outcome.get("duration", 0.0)
        if duration > 300:  # 5 minutes
            suggestions.append("Consider parallel execution to reduce duration")
        elif duration > 120:  # 2 minutes
            suggestions.append("Optimize handoff context to reduce transfer time")
        
        # Success rate suggestions
        success_rate = outcome.get("success", False)
        if not success_rate:
            suggestions.append("Review failure modes and add error recovery")
        
        # Context preservation suggestions
        context_preservation = outcome.get("context_preservation", 0.0)
        if context_preservation < 0.7:
            suggestions.append("Improve context preservation between agents")
        
        # Performance impact suggestions
        performance_impact = outcome.get("performance_impact", 0.0)
        if performance_impact < 0.5:
            suggestions.append("Consider agent sequence optimization")
        
        return suggestions
    
    async def _store_pattern_memory(self, pattern: CoordinationMemoryPattern):
        """Store coordination pattern in memory."""
        
        try:
            # Create memory content
            content = f"Coordination pattern learned: {pattern.pattern_type.value} with {len(pattern.agents_involved)} agents. Success rate: {pattern.success_rate:.1%}"
            
            # Prepare metadata
            metadata = {
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type.value,
                "agents_involved": pattern.agents_involved,
                "project_context": pattern.project_context,
                "success_rate": pattern.success_rate,
                "average_duration": pattern.average_duration,
                "context_preservation_score": pattern.context_preservation_score,
                "performance_impact": pattern.performance_impact,
                "usage_frequency": pattern.usage_frequency,
                "optimization_suggestions": pattern.optimization_suggestions,
                "timestamp": datetime.now().isoformat()
            }
            
            # Create trigger event
            trigger_event = TriggerEvent(
                trigger_type=TriggerType.PATTERN_LEARNED,
                priority=TriggerPriority.LOW,
                project_name=pattern.project_context,
                event_id=f"coordination_pattern_{pattern.pattern_id}",
                content=content,
                category=MemoryCategory.LEARNING,
                tags=["coordination", "pattern", "learning"] + pattern.agents_involved,
                metadata=metadata,
                source="coordination_learning_engine"
            )
            
            # Process trigger
            orchestrator = self.memory_service.get_trigger_orchestrator()
            if orchestrator:
                await orchestrator.process_trigger(trigger_event)
            
        except Exception as e:
            self.logger.error(f"Failed to store pattern memory: {e}")
    
    async def get_pattern_recommendations(self, 
                                        coordination_context: Dict[str, Any]) -> List[CoordinationMemoryPattern]:
        """Get pattern recommendations for coordination context."""
        
        try:
            # Find similar patterns
            similar_patterns = []
            context_agents = set(coordination_context.get("agents_involved", []))
            project_type = coordination_context.get("project_type", "unknown")
            
            for pattern in self.learned_patterns.values():
                # Calculate similarity score
                pattern_agents = set(pattern.agents_involved)
                agent_similarity = len(context_agents.intersection(pattern_agents)) / len(context_agents.union(pattern_agents))
                
                project_similarity = 1.0 if pattern.project_context == project_type else 0.5
                
                overall_similarity = (agent_similarity * 0.7) + (project_similarity * 0.3)
                
                if overall_similarity > 0.6:
                    similar_patterns.append((pattern, overall_similarity))
            
            # Sort by similarity and success rate
            similar_patterns.sort(key=lambda x: (x[1], x[0].success_rate), reverse=True)
            
            # Return top recommendations
            return [pattern for pattern, similarity in similar_patterns[:5]]
            
        except Exception as e:
            self.logger.error(f"Failed to get pattern recommendations: {e}")
            return []


class PerformanceOptimizer:
    """Optimizes coordination performance based on memory patterns."""
    
    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
    
    async def optimize_coordination_sequence(self, 
                                           agents_sequence: List[str],
                                           project_name: str,
                                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize agent coordination sequence based on memory patterns.
        
        Args:
            agents_sequence: Original sequence of agents
            project_name: Project name
            context: Coordination context
            
        Returns:
            Optimization recommendations
        """
        try:
            # Analyze existing sequence performance
            sequence_analysis = await self._analyze_sequence_performance(agents_sequence, project_name)
            
            # Generate optimization suggestions
            optimizations = self._generate_sequence_optimizations(agents_sequence, sequence_analysis, context)
            
            # Calculate expected improvements
            expected_improvements = self._calculate_expected_improvements(optimizations)
            
            return {
                "original_sequence": agents_sequence,
                "analysis": sequence_analysis,
                "optimizations": optimizations,
                "expected_improvements": expected_improvements,
                "confidence_score": self._calculate_confidence_score(sequence_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to optimize coordination sequence: {e}")
            return {"error": str(e)}
    
    async def _analyze_sequence_performance(self, 
                                          agents_sequence: List[str], 
                                          project_name: str) -> Dict[str, Any]:
        """Analyze performance of agent sequence."""
        
        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return {"error": "Memory service not available"}
            
            # Search for sequence memories
            search_query = f"agents {' '.join(agents_sequence)} {project_name}"
            
            memories = await memory_service.search_memories(
                query=search_query,
                filters={"project_name": project_name},
                limit=50
            )
            
            if not memories:
                return {"sequences_found": 0, "analysis": "No historical data"}
            
            # Analyze performance metrics
            success_rates = []
            durations = []
            handoff_qualities = []
            
            for memory in memories:
                metadata = memory.metadata
                success_rates.append(metadata.get("success", False))
                durations.append(metadata.get("duration", 0))
                handoff_qualities.append(metadata.get("handoff_quality", "adequate"))
            
            # Calculate metrics
            avg_success_rate = sum(success_rates) / len(success_rates)
            avg_duration = sum(durations) / len(durations)
            
            # Analyze handoff bottlenecks
            bottlenecks = self._identify_bottlenecks(memories, agents_sequence)
            
            return {
                "sequences_found": len(memories),
                "success_rate": avg_success_rate,
                "average_duration": avg_duration,
                "bottlenecks": bottlenecks,
                "handoff_quality_distribution": Counter(handoff_qualities)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze sequence performance: {e}")
            return {"error": str(e)}
    
    def _identify_bottlenecks(self, memories: List[MemoryItem], agents_sequence: List[str]) -> List[str]:
        """Identify bottlenecks in agent sequence."""
        
        bottlenecks = []
        
        # Analyze handoff durations
        handoff_durations = defaultdict(list)
        
        for memory in memories:
            handoffs = memory.metadata.get("agent_handoffs", [])
            for i, handoff in enumerate(handoffs):
                if i < len(agents_sequence) - 1:
                    handoff_key = f"{agents_sequence[i]}->{agents_sequence[i+1]}"
                    handoff_durations[handoff_key].append(handoff.get("duration", 0))
        
        # Find slow handoffs
        for handoff_key, durations in handoff_durations.items():
            if durations:
                avg_duration = sum(durations) / len(durations)
                if avg_duration > 60:  # More than 1 minute
                    bottlenecks.append(f"Slow handoff: {handoff_key} ({avg_duration:.1f}s)")
        
        return bottlenecks
    
    def _generate_sequence_optimizations(self, 
                                       agents_sequence: List[str], 
                                       analysis: Dict[str, Any],
                                       context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions for sequence."""
        
        optimizations = []
        
        # Parallel execution opportunities
        if len(agents_sequence) > 2:
            optimizations.append({
                "type": "parallel_execution",
                "description": "Execute independent agents in parallel",
                "agents": agents_sequence[1:-1],  # Middle agents
                "expected_time_saving": "30-50%"
            })
        
        # Sequence reordering
        bottlenecks = analysis.get("bottlenecks", [])
        if bottlenecks:
            optimizations.append({
                "type": "sequence_reordering",
                "description": "Reorder sequence to avoid bottlenecks",
                "bottlenecks": bottlenecks,
                "suggested_reorder": self._suggest_reorder(agents_sequence, bottlenecks)
            })
        
        # Context optimization
        if analysis.get("success_rate", 1.0) < 0.8:
            optimizations.append({
                "type": "context_optimization",
                "description": "Improve context preservation between agents",
                "success_rate": analysis.get("success_rate", 0.0),
                "suggested_improvements": ["Enhanced context transfer", "Validation checkpoints"]
            })
        
        return optimizations
    
    def _suggest_reorder(self, agents_sequence: List[str], bottlenecks: List[str]) -> List[str]:
        """Suggest reordering to avoid bottlenecks."""
        
        # Simple reordering logic - move slow handoffs to end
        reordered = agents_sequence.copy()
        
        # Extract bottleneck agents
        bottleneck_agents = set()
        for bottleneck in bottlenecks:
            if "->" in bottleneck:
                agents = bottleneck.split("->")
                bottleneck_agents.update(agents)
        
        # Move bottleneck agents to end (simplified logic)
        for agent in bottleneck_agents:
            if agent in reordered:
                reordered.remove(agent)
                reordered.append(agent)
        
        return reordered
    
    def _calculate_expected_improvements(self, optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate expected improvements from optimizations."""
        
        improvements = {
            "time_savings": 0.0,
            "success_rate_improvement": 0.0,
            "context_preservation_improvement": 0.0
        }
        
        for optimization in optimizations:
            if optimization["type"] == "parallel_execution":
                improvements["time_savings"] += 0.4  # 40% time savings
            elif optimization["type"] == "sequence_reordering":
                improvements["time_savings"] += 0.2  # 20% time savings
            elif optimization["type"] == "context_optimization":
                improvements["success_rate_improvement"] += 0.15  # 15% improvement
                improvements["context_preservation_improvement"] += 0.25  # 25% improvement
        
        return improvements
    
    def _calculate_confidence_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for optimizations."""
        
        sequences_found = analysis.get("sequences_found", 0)
        
        if sequences_found == 0:
            return 0.0
        elif sequences_found < 5:
            return 0.3
        elif sequences_found < 15:
            return 0.6
        else:
            return 0.9


class CoordinationMemoryManager:
    """
    Central manager for coordination memory patterns.
    
    Coordinates handoff analysis, learning, and optimization for
    agent coordination patterns in the Claude PM Framework.
    """
    
    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.handoff_analyzer = HandoffPatternAnalyzer(memory_service)
        self.learning_engine = CoordinationLearningEngine(memory_service)
        self.performance_optimizer = PerformanceOptimizer(memory_service)
        
        # Coordination metrics
        self.coordination_metrics = {
            "total_handoffs_analyzed": 0,
            "patterns_learned": 0,
            "optimizations_suggested": 0,
            "successful_optimizations": 0
        }
        
        self.logger.info("Coordination Memory Manager initialized")
    
    async def analyze_coordination_handoff(self, 
                                         source_agent: str, 
                                         target_agent: str,
                                         project_name: str = None) -> HandoffAnalysis:
        """
        Analyze coordination handoff between agents.
        
        Args:
            source_agent: Source agent ID
            target_agent: Target agent ID
            project_name: Optional project name
            
        Returns:
            Handoff analysis
        """
        analysis = await self.handoff_analyzer.analyze_handoff_patterns(
            source_agent, target_agent, project_name
        )
        
        self.coordination_metrics["total_handoffs_analyzed"] += 1
        
        self.logger.info(f"Analyzed handoff: {source_agent} -> {target_agent}")
        return analysis
    
    async def learn_coordination_pattern(self, 
                                       coordination_context: Dict[str, Any],
                                       outcome: Dict[str, Any]) -> Optional[CoordinationMemoryPattern]:
        """
        Learn from coordination pattern and outcome.
        
        Args:
            coordination_context: Coordination context
            outcome: Coordination outcome
            
        Returns:
            Learned coordination pattern
        """
        pattern = await self.learning_engine.learn_from_coordination(
            coordination_context, outcome
        )
        
        if pattern:
            self.coordination_metrics["patterns_learned"] += 1
            self.logger.info(f"Learned coordination pattern: {pattern.pattern_id}")
        
        return pattern
    
    async def optimize_coordination_sequence(self, 
                                           agents_sequence: List[str],
                                           project_name: str,
                                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize agent coordination sequence.
        
        Args:
            agents_sequence: Agent sequence
            project_name: Project name
            context: Coordination context
            
        Returns:
            Optimization recommendations
        """
        optimization = await self.performance_optimizer.optimize_coordination_sequence(
            agents_sequence, project_name, context
        )
        
        if "optimizations" in optimization:
            self.coordination_metrics["optimizations_suggested"] += len(optimization["optimizations"])
        
        self.logger.info(f"Generated optimization for sequence: {agents_sequence}")
        return optimization
    
    async def get_coordination_recommendations(self, 
                                             coordination_context: Dict[str, Any]) -> List[CoordinationMemoryPattern]:
        """
        Get coordination recommendations based on context.
        
        Args:
            coordination_context: Coordination context
            
        Returns:
            List of recommended patterns
        """
        recommendations = await self.learning_engine.get_pattern_recommendations(
            coordination_context
        )
        
        self.logger.info(f"Generated {len(recommendations)} coordination recommendations")
        return recommendations
    
    def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get coordination metrics."""
        return {
            **self.coordination_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_old_patterns(self, days_old: int = 90):
        """Clean up old coordination patterns."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        patterns_to_remove = []
        for pattern_id, pattern in self.learning_engine.learned_patterns.items():
            if pattern.last_used < cutoff_date and pattern.usage_frequency < 3:
                patterns_to_remove.append(pattern_id)
        
        for pattern_id in patterns_to_remove:
            del self.learning_engine.learned_patterns[pattern_id]
        
        self.logger.info(f"Cleaned up {len(patterns_to_remove)} old coordination patterns")


# Factory function for creating coordination memory manager
def create_coordination_memory_manager(memory_service: MemoryTriggerService) -> CoordinationMemoryManager:
    """
    Create coordination memory manager instance.
    
    Args:
        memory_service: Memory trigger service
        
    Returns:
        Coordination memory manager instance
    """
    return CoordinationMemoryManager(memory_service)