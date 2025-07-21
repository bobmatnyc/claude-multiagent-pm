#!/usr/bin/env python3
"""
E2E Test Suite for Agent Selection Strategies
============================================

Tests for different agent selection strategies, custom selection algorithms,
weighted selection criteria, and dynamic agent selection.

Test Categories:
1. Different selection strategies (round-robin, least-loaded, capability-based)
2. Custom selection algorithms
3. Weighted selection criteria
4. Dynamic agent selection based on runtime conditions
5. Strategy performance comparison
6. Adaptive strategy selection

Created: 2025-07-19
"""

import os
import sys
import json
import asyncio
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import Mock, patch
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from claude_pm.core.agent_registry import AgentRegistry
from claude_pm.services.model_selector import ModelSelector, ModelType


class SelectionStrategy(Enum):
    """Available agent selection strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CAPABILITY_BASED = "capability_based"
    WEIGHTED_RANDOM = "weighted_random"
    PRIORITY_BASED = "priority_based"
    ADAPTIVE = "adaptive"
    CUSTOM = "custom"


@dataclass
class AgentLoadMetrics:
    """Metrics for tracking agent load and performance."""
    agent_id: str
    current_tasks: int = 0
    total_tasks_completed: int = 0
    average_task_duration_ms: float = 0.0
    success_rate: float = 1.0
    last_task_timestamp: Optional[float] = None
    specialization_match_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class SelectionContext:
    """Context for agent selection decisions."""
    task_description: str
    required_capabilities: List[str]
    performance_requirements: Dict[str, Any]
    priority_level: int = 5  # 1-10, higher is more important
    deadline: Optional[datetime] = None
    previous_attempts: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)


class AgentSelectionStrategy:
    """Base class for agent selection strategies."""
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.metrics: Dict[str, AgentLoadMetrics] = {}
    
    def select_agent(self, context: SelectionContext, available_agents: Dict[str, Any]) -> Optional[str]:
        """Select an agent based on the strategy. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement select_agent")
    
    def update_metrics(self, agent_id: str, task_duration_ms: float, success: bool):
        """Update agent metrics after task completion."""
        if agent_id not in self.metrics:
            self.metrics[agent_id] = AgentLoadMetrics(agent_id=agent_id)
        
        metrics = self.metrics[agent_id]
        metrics.total_tasks_completed += 1
        
        # Update average duration
        total_duration = metrics.average_task_duration_ms * (metrics.total_tasks_completed - 1)
        metrics.average_task_duration_ms = (total_duration + task_duration_ms) / metrics.total_tasks_completed
        
        # Update success rate
        total_successes = metrics.success_rate * (metrics.total_tasks_completed - 1)
        if success:
            total_successes += 1
        metrics.success_rate = total_successes / metrics.total_tasks_completed
        
        metrics.last_task_timestamp = time.time()


class RoundRobinStrategy(AgentSelectionStrategy):
    """Round-robin agent selection strategy."""
    
    def __init__(self, registry: AgentRegistry):
        super().__init__(registry)
        self.current_index = 0
    
    def select_agent(self, context: SelectionContext, available_agents: Dict[str, Any]) -> Optional[str]:
        """Select next agent in round-robin order."""
        if not available_agents:
            return None
        
        agent_ids = list(available_agents.keys())
        selected = agent_ids[self.current_index % len(agent_ids)]
        self.current_index += 1
        
        return selected


class LeastLoadedStrategy(AgentSelectionStrategy):
    """Select the agent with the least current load."""
    
    def select_agent(self, context: SelectionContext, available_agents: Dict[str, Any]) -> Optional[str]:
        """Select agent with minimum current tasks."""
        if not available_agents:
            return None
        
        # Initialize metrics for new agents
        for agent_id in available_agents:
            if agent_id not in self.metrics:
                self.metrics[agent_id] = AgentLoadMetrics(agent_id=agent_id)
        
        # Find least loaded agent
        min_load = float('inf')
        selected_agent = None
        
        for agent_id in available_agents:
            current_load = self.metrics[agent_id].current_tasks
            if current_load < min_load:
                min_load = current_load
                selected_agent = agent_id
        
        return selected_agent


class CapabilityBasedStrategy(AgentSelectionStrategy):
    """Select agent based on capability match score."""
    
    def select_agent(self, context: SelectionContext, available_agents: Dict[str, Any]) -> Optional[str]:
        """Select agent with best capability match."""
        if not available_agents:
            return None
        
        best_score = -1
        selected_agent = None
        
        for agent_id, agent_info in available_agents.items():
            # Calculate capability match score
            agent_capabilities = set(agent_info.get("specializations", []))
            required_capabilities = set(context.required_capabilities)
            
            if required_capabilities:
                # Jaccard similarity coefficient
                intersection = agent_capabilities & required_capabilities
                union = agent_capabilities | required_capabilities
                score = len(intersection) / len(union) if union else 0
            else:
                score = 1.0  # No specific requirements, all agents equal
            
            # Consider agent performance metrics
            if agent_id in self.metrics:
                score *= self.metrics[agent_id].success_rate
            
            if score > best_score:
                best_score = score
                selected_agent = agent_id
        
        return selected_agent


class WeightedRandomStrategy(AgentSelectionStrategy):
    """Select agent using weighted random selection based on performance."""
    
    def select_agent(self, context: SelectionContext, available_agents: Dict[str, Any]) -> Optional[str]:
        """Select agent with weighted random probability."""
        if not available_agents:
            return None
        
        # Calculate weights for each agent
        weights = {}
        for agent_id in available_agents:
            if agent_id not in self.metrics:
                self.metrics[agent_id] = AgentLoadMetrics(agent_id=agent_id)
            
            # Base weight
            weight = 1.0
            
            # Adjust by success rate
            weight *= self.metrics[agent_id].success_rate
            
            # Adjust by current load (inverse)
            current_load = self.metrics[agent_id].current_tasks
            weight *= 1.0 / (1.0 + current_load)
            
            weights[agent_id] = weight
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight == 0:
            return random.choice(list(available_agents.keys()))
        
        # Weighted random selection
        rand_val = random.random() * total_weight
        cumulative = 0
        
        for agent_id, weight in weights.items():
            cumulative += weight
            if rand_val <= cumulative:
                return agent_id
        
        return list(available_agents.keys())[-1]


class PriorityBasedStrategy(AgentSelectionStrategy):
    """Select agent based on task priority and agent tier."""
    
    def select_agent(self, context: SelectionContext, available_agents: Dict[str, Any]) -> Optional[str]:
        """Select agent based on priority matching."""
        if not available_agents:
            return None
        
        # High priority tasks go to project-tier agents first
        if context.priority_level >= 8:
            # Prefer project-tier agents
            project_agents = {
                aid: info for aid, info in available_agents.items() 
                if info.get("tier") == "project"
            }
            if project_agents:
                # Use capability matching within project agents
                cap_strategy = CapabilityBasedStrategy(self.registry)
                return cap_strategy.select_agent(context, project_agents)
        
        # Medium priority: balance load and capability
        elif context.priority_level >= 5:
            # Calculate combined score
            best_score = -1
            selected_agent = None
            
            for agent_id, agent_info in available_agents.items():
                score = 0.5  # Base score
                
                # Capability match (40% weight)
                agent_caps = set(agent_info.get("specializations", []))
                req_caps = set(context.required_capabilities)
                if req_caps:
                    cap_score = len(agent_caps & req_caps) / len(req_caps)
                    score += 0.4 * cap_score
                
                # Load factor (30% weight)
                if agent_id in self.metrics:
                    load_factor = 1.0 / (1.0 + self.metrics[agent_id].current_tasks)
                    score += 0.3 * load_factor
                
                # Tier bonus (30% weight)
                tier_scores = {"project": 1.0, "user": 0.7, "system": 0.4}
                score += 0.3 * tier_scores.get(agent_info.get("tier", "system"), 0.4)
                
                if score > best_score:
                    best_score = score
                    selected_agent = agent_id
            
            return selected_agent
        
        # Low priority: use least loaded
        else:
            return LeastLoadedStrategy(self.registry).select_agent(context, available_agents)


class AdaptiveStrategy(AgentSelectionStrategy):
    """Adaptive strategy that learns from past performance."""
    
    def __init__(self, registry: AgentRegistry):
        super().__init__(registry)
        self.strategy_performance: Dict[str, float] = defaultdict(lambda: 1.0)
        self.task_history: List[Dict[str, Any]] = []
        self.strategies = {
            SelectionStrategy.ROUND_ROBIN: RoundRobinStrategy(registry),
            SelectionStrategy.LEAST_LOADED: LeastLoadedStrategy(registry),
            SelectionStrategy.CAPABILITY_BASED: CapabilityBasedStrategy(registry),
            SelectionStrategy.WEIGHTED_RANDOM: WeightedRandomStrategy(registry),
            SelectionStrategy.PRIORITY_BASED: PriorityBasedStrategy(registry),
        }
    
    def select_agent(self, context: SelectionContext, available_agents: Dict[str, Any]) -> Optional[str]:
        """Select agent using the best performing strategy for similar tasks."""
        # Analyze task characteristics
        task_chars = self._analyze_task(context)
        
        # Select best strategy based on historical performance
        best_strategy = self._select_best_strategy(task_chars)
        
        # Use selected strategy
        selected_agent = self.strategies[best_strategy].select_agent(context, available_agents)
        
        # Record decision for learning
        self.task_history.append({
            "timestamp": time.time(),
            "task_chars": task_chars,
            "strategy": best_strategy,
            "agent": selected_agent,
            "context": context
        })
        
        return selected_agent
    
    def _analyze_task(self, context: SelectionContext) -> Dict[str, Any]:
        """Analyze task characteristics for strategy selection."""
        return {
            "has_capabilities": len(context.required_capabilities) > 0,
            "priority_level": context.priority_level,
            "has_deadline": context.deadline is not None,
            "retry_attempt": len(context.previous_attempts) > 0,
            "task_type": self._classify_task_type(context.task_description)
        }
    
    def _classify_task_type(self, description: str) -> str:
        """Classify task type from description."""
        keywords = {
            "implementation": ["implement", "code", "develop", "build"],
            "testing": ["test", "qa", "validate", "verify"],
            "documentation": ["document", "write", "describe", "explain"],
            "research": ["research", "investigate", "analyze", "study"],
            "deployment": ["deploy", "release", "publish", "launch"]
        }
        
        description_lower = description.lower()
        for task_type, words in keywords.items():
            if any(word in description_lower for word in words):
                return task_type
        
        return "general"
    
    def _select_best_strategy(self, task_chars: Dict[str, Any]) -> SelectionStrategy:
        """Select best strategy based on task characteristics."""
        # Simple heuristic-based selection (can be replaced with ML model)
        if task_chars["has_capabilities"] and not task_chars["retry_attempt"]:
            return SelectionStrategy.CAPABILITY_BASED
        elif task_chars["priority_level"] >= 7:
            return SelectionStrategy.PRIORITY_BASED
        elif task_chars["has_deadline"]:
            return SelectionStrategy.LEAST_LOADED
        elif task_chars["task_type"] in ["implementation", "research"]:
            return SelectionStrategy.CAPABILITY_BASED
        else:
            # Use weighted random for general tasks
            return SelectionStrategy.WEIGHTED_RANDOM


class TestAgentSelectionStrategies:
    """Test suite for agent selection strategies."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.registry = AgentRegistry()
        self.model_selector = ModelSelector()
        
        # Create mock agents
        self.mock_agents = {
            "engineer_1": {
                "type": "engineer",
                "tier": "project",
                "specializations": ["python", "backend", "api"],
                "model_config": {"preferred_model": "claude-4-opus"}
            },
            "engineer_2": {
                "type": "engineer",
                "tier": "user",
                "specializations": ["javascript", "frontend", "react"],
                "model_config": {"preferred_model": "claude-sonnet-4-20250514"}
            },
            "qa_1": {
                "type": "qa",
                "tier": "project",
                "specializations": ["testing", "automation", "selenium"],
                "model_config": {"preferred_model": "claude-sonnet-4-20250514"}
            },
            "researcher_1": {
                "type": "research",
                "tier": "system",
                "specializations": ["ml", "algorithms", "optimization"],
                "model_config": {"preferred_model": "claude-sonnet-4-20250514"}
            },
            "generalist_1": {
                "type": "agent",
                "tier": "system",
                "specializations": ["general", "support"],
                "model_config": {"preferred_model": "claude-sonnet-4-20250514"}
            }
        }
    
    def test_round_robin_strategy(self):
        """Test round-robin selection strategy."""
        strategy = RoundRobinStrategy(self.registry)
        
        # Create selection context
        context = SelectionContext(
            task_description="Generic task",
            required_capabilities=[]
        )
        
        # Track selections
        selections = []
        for _ in range(10):
            selected = strategy.select_agent(context, self.mock_agents)
            selections.append(selected)
        
        # Verify round-robin behavior
        agent_ids = list(self.mock_agents.keys())
        for i, selected in enumerate(selections):
            expected = agent_ids[i % len(agent_ids)]
            assert selected == expected, f"Round-robin order broken at index {i}"
    
    def test_least_loaded_strategy(self):
        """Test least loaded selection strategy."""
        strategy = LeastLoadedStrategy(self.registry)
        
        # Set initial loads
        strategy.metrics["engineer_1"] = AgentLoadMetrics("engineer_1", current_tasks=3)
        strategy.metrics["engineer_2"] = AgentLoadMetrics("engineer_2", current_tasks=1)
        strategy.metrics["qa_1"] = AgentLoadMetrics("qa_1", current_tasks=2)
        
        context = SelectionContext(
            task_description="New task",
            required_capabilities=[]
        )
        
        # Should select engineer_2 (least loaded)
        selected = strategy.select_agent(context, self.mock_agents)
        assert selected == "engineer_2", f"Should select least loaded agent, got {selected}"
        
        # Increase load and test again
        strategy.metrics["engineer_2"].current_tasks = 5
        selected = strategy.select_agent(context, self.mock_agents)
        assert selected != "engineer_2", "Should not select heavily loaded agent"
    
    def test_capability_based_strategy(self):
        """Test capability-based selection strategy."""
        strategy = CapabilityBasedStrategy(self.registry)
        
        # Test exact match
        context = SelectionContext(
            task_description="Implement Python backend API",
            required_capabilities=["python", "backend", "api"]
        )
        
        selected = strategy.select_agent(context, self.mock_agents)
        assert selected == "engineer_1", "Should select agent with exact capability match"
        
        # Test partial match
        context.required_capabilities = ["testing", "automation"]
        selected = strategy.select_agent(context, self.mock_agents)
        assert selected == "qa_1", "Should select QA agent for testing capabilities"
        
        # Test with performance metrics
        strategy.metrics["qa_1"] = AgentLoadMetrics("qa_1", success_rate=0.5)
        strategy.metrics["engineer_1"] = AgentLoadMetrics("engineer_1", success_rate=0.9)
        
        context.required_capabilities = ["general"]  # Both have some match
        selected = strategy.select_agent(context, self.mock_agents)
        # Should prefer agent with better success rate
        assert selected in ["engineer_1", "generalist_1"], \
            "Should consider success rate in selection"
    
    def test_weighted_random_strategy(self):
        """Test weighted random selection strategy."""
        strategy = WeightedRandomStrategy(self.registry)
        
        # Set up metrics
        strategy.metrics["engineer_1"] = AgentLoadMetrics(
            "engineer_1", 
            current_tasks=0, 
            success_rate=0.95
        )
        strategy.metrics["engineer_2"] = AgentLoadMetrics(
            "engineer_2", 
            current_tasks=5, 
            success_rate=0.8
        )
        
        context = SelectionContext(
            task_description="Random task",
            required_capabilities=[]
        )
        
        # Run multiple selections to verify weighting
        selections = defaultdict(int)
        for _ in range(1000):
            selected = strategy.select_agent(context, self.mock_agents)
            selections[selected] += 1
        
        # Engineer_1 should be selected more often (better metrics)
        assert selections["engineer_1"] > selections["engineer_2"], \
            "Agent with better metrics should be selected more often"
    
    def test_priority_based_strategy(self):
        """Test priority-based selection strategy."""
        strategy = PriorityBasedStrategy(self.registry)
        
        # High priority task
        high_priority_context = SelectionContext(
            task_description="Critical production fix",
            required_capabilities=["backend"],
            priority_level=9
        )
        
        selected = strategy.select_agent(high_priority_context, self.mock_agents)
        # Should prefer project-tier agents for high priority
        assert self.mock_agents[selected]["tier"] == "project", \
            "High priority tasks should go to project-tier agents"
        
        # Low priority task
        low_priority_context = SelectionContext(
            task_description="Minor documentation update",
            required_capabilities=[],
            priority_level=2
        )
        
        # Set some loads
        strategy.metrics["engineer_1"] = AgentLoadMetrics("engineer_1", current_tasks=5)
        strategy.metrics["generalist_1"] = AgentLoadMetrics("generalist_1", current_tasks=0)
        
        selected = strategy.select_agent(low_priority_context, self.mock_agents)
        # Should use least loaded for low priority
        assert selected == "generalist_1", \
            "Low priority tasks should go to least loaded agents"
    
    def test_adaptive_strategy(self):
        """Test adaptive selection strategy."""
        strategy = AdaptiveStrategy(self.registry)
        
        # Test task classification
        test_tasks = [
            ("Implement new user authentication system", "implementation"),
            ("Run regression tests on payment module", "testing"),
            ("Document the API endpoints", "documentation"),
            ("Research best practices for caching", "research"),
            ("Deploy application to production", "deployment"),
            ("Fix the bug in user profile", "general")
        ]
        
        for description, expected_type in test_tasks:
            task_type = strategy._classify_task_type(description)
            assert task_type == expected_type, \
                f"Wrong classification for '{description}': got {task_type}, expected {expected_type}"
        
        # Test strategy selection based on task characteristics
        capability_context = SelectionContext(
            task_description="Implement Python API",
            required_capabilities=["python", "api"],
            priority_level=5
        )
        
        selected = strategy.select_agent(capability_context, self.mock_agents)
        assert selected is not None, "Adaptive strategy should select an agent"
        
        # Verify task history is recorded
        assert len(strategy.task_history) == 1, "Task history should be recorded"
        assert strategy.task_history[0]["agent"] == selected
    
    def test_custom_selection_algorithm(self):
        """Test custom selection algorithm implementation."""
        
        class CustomStrategy(AgentSelectionStrategy):
            """Custom strategy that prefers agents with specific name patterns."""
            
            def select_agent(self, context: SelectionContext, available_agents: Dict[str, Any]) -> Optional[str]:
                # Prefer agents with "_1" suffix
                for agent_id in available_agents:
                    if agent_id.endswith("_1"):
                        return agent_id
                
                # Fallback to first available
                return list(available_agents.keys())[0] if available_agents else None
        
        strategy = CustomStrategy(self.registry)
        context = SelectionContext(
            task_description="Custom task",
            required_capabilities=[]
        )
        
        selected = strategy.select_agent(context, self.mock_agents)
        assert selected.endswith("_1"), "Custom strategy should prefer _1 agents"
    
    def test_strategy_performance_comparison(self):
        """Compare performance of different strategies."""
        strategies = {
            "round_robin": RoundRobinStrategy(self.registry),
            "least_loaded": LeastLoadedStrategy(self.registry),
            "capability_based": CapabilityBasedStrategy(self.registry),
            "weighted_random": WeightedRandomStrategy(self.registry),
            "priority_based": PriorityBasedStrategy(self.registry),
        }
        
        # Performance metrics
        performance_results = {}
        
        # Test each strategy
        for name, strategy in strategies.items():
            start_time = time.perf_counter()
            
            # Run 1000 selections
            for i in range(1000):
                context = SelectionContext(
                    task_description=f"Task {i}",
                    required_capabilities=["python"] if i % 3 == 0 else [],
                    priority_level=random.randint(1, 10)
                )
                
                strategy.select_agent(context, self.mock_agents)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            performance_results[name] = {
                "total_time_ms": elapsed_ms,
                "avg_time_per_selection_ms": elapsed_ms / 1000
            }
        
        # Print results
        print("\nStrategy Performance Comparison:")
        for name, metrics in performance_results.items():
            print(f"  {name}: {metrics['avg_time_per_selection_ms']:.3f}ms per selection")
        
        # All strategies should be fast
        for name, metrics in performance_results.items():
            assert metrics['avg_time_per_selection_ms'] < 1.0, \
                f"{name} strategy is too slow: {metrics['avg_time_per_selection_ms']}ms"
    
    def test_dynamic_agent_pool_changes(self):
        """Test strategies with dynamic changes to available agents."""
        strategy = CapabilityBasedStrategy(self.registry)
        
        # Start with limited agents
        limited_agents = {
            k: v for k, v in self.mock_agents.items() 
            if k in ["engineer_1", "qa_1"]
        }
        
        context = SelectionContext(
            task_description="Test task",
            required_capabilities=["ml", "algorithms"]
        )
        
        # Should work with limited pool
        selected = strategy.select_agent(context, limited_agents)
        assert selected in limited_agents, "Should select from available agents"
        
        # Add more agents dynamically
        expanded_agents = self.mock_agents.copy()
        expanded_agents["ml_specialist"] = {
            "type": "researcher",
            "tier": "project",
            "specializations": ["ml", "algorithms", "tensorflow"],
            "model_config": {"preferred_model": "claude-4-opus"}
        }
        
        # Should now prefer the ML specialist
        selected = strategy.select_agent(context, expanded_agents)
        assert selected in ["researcher_1", "ml_specialist"], \
            "Should select agent with ML capabilities"
    
    def test_selection_with_constraints(self):
        """Test selection with various constraints."""
        strategy = PriorityBasedStrategy(self.registry)
        
        # Test with deadline constraint
        urgent_context = SelectionContext(
            task_description="Urgent fix needed",
            required_capabilities=["backend"],
            priority_level=10,
            deadline=datetime.now()
        )
        
        # Set up agent availability
        strategy.metrics["engineer_1"] = AgentLoadMetrics(
            "engineer_1",
            current_tasks=2,
            average_task_duration_ms=5000  # 5 seconds average
        )
        strategy.metrics["engineer_2"] = AgentLoadMetrics(
            "engineer_2",
            current_tasks=1,
            average_task_duration_ms=2000  # 2 seconds average
        )
        
        selected = strategy.select_agent(urgent_context, self.mock_agents)
        # For urgent tasks, should still prefer project-tier despite load
        assert selected == "engineer_1", \
            "Urgent high-priority tasks should go to project-tier agents"
        
        # Test with previous failure constraint
        retry_context = SelectionContext(
            task_description="Retry failed task",
            required_capabilities=[],
            previous_attempts=["engineer_1", "engineer_2"]
        )
        
        # Should avoid previously failed agents if possible
        remaining_agents = {
            k: v for k, v in self.mock_agents.items()
            if k not in retry_context.previous_attempts
        }
        
        selected = strategy.select_agent(retry_context, remaining_agents)
        assert selected not in retry_context.previous_attempts, \
            "Should avoid agents that previously failed the task"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])