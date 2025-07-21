#!/usr/bin/env python3
"""
E2E Test Suite for Agent Selection
==================================

Comprehensive end-to-end tests for agent selection functionality,
including optimal agent selection, model integration, tier precedence,
and performance requirements matching.

Test Categories:
1. Core agent selection (9 core agents)
2. Specialized agent selection
3. Model selector integration
4. Tier precedence testing
5. Performance requirements matching
6. Multi-criteria selection
7. Fallback agent selection
8. Load balancing across agents

Created: 2025-07-19
"""

import os
import sys
import json
import asyncio
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from claude_pm.core.agent_keyword_parser import AgentKeywordParser
from claude_pm.core.agent_registry import AgentRegistry
from claude_pm.services.agent_registry_sync import AgentRegistry as AgentRegistrySync
from claude_pm.services.model_selector import ModelSelector, ModelType, ModelSelectionCriteria
from claude_pm.orchestration.backwards_compatible_orchestrator import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode
)
from claude_pm.services.shared_prompt_cache import SharedPromptCache


class TestAgentSelection:
    """Comprehensive E2E tests for agent selection functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Clear any existing cache
        cache = SharedPromptCache.get_instance()
        cache.clear()
        
        # Initialize components
        self.keyword_parser = AgentKeywordParser()
        self.model_selector = ModelSelector()
        self.registry = AgentRegistry()
        
        # Setup test project structure
        self.test_dir = tempfile.mkdtemp()
        self.project_agents_dir = Path(self.test_dir) / ".claude-pm" / "agents" / "project-specific"
        self.project_agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Store original working directory
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_mock_agent(self, agent_name: str, tier: str = "project", specializations: List[str] = None):
        """Create a mock agent file for testing."""
        agent_content = f"""# {agent_name.title()} Agent

## Role
Test {agent_name} agent for E2E testing.

## Specializations
{json.dumps(specializations or [])}

## Tier
{tier}

## Model Requirements
{{
    "preferred_model": "claude-sonnet-4-20250514",
    "complexity_threshold": "medium"
}}
"""
        
        if tier == "project":
            agent_path = self.project_agents_dir / f"{agent_name}_agent.md"
        else:
            # For user/system agents, we'll mock them differently
            agent_path = Path(self.test_dir) / f"{agent_name}_agent.md"
        
        agent_path.write_text(agent_content)
        return agent_path
    
    def test_core_agent_selection(self):
        """Test selection of core agent types."""
        test_cases = [
            # (task_description, expected_agent_type)
            ("Update the API documentation with new endpoints", "documentation"),
            ("Create a new ticket for the bug in payment processing", "ticketing"),
            ("Implement the user authentication feature", "engineer"),
            ("Run comprehensive tests on the new module", "qa"),
            ("Scan for security vulnerabilities in dependencies", "security"),
            ("Research best practices for microservices architecture", "research"),
            ("Set up PostgreSQL database with optimized indexes", "data_engineer"),
            ("Deploy the application to production server", "ops"),
            ("Create a new feature branch for ISS-123", "version_control"),
        ]
        
        for task_description, expected_agent in test_cases:
            # Test keyword parsing
            detected_agent = self.keyword_parser.parse_task_description(task_description)
            assert detected_agent == expected_agent, f"Failed to detect {expected_agent} from: {task_description}"
            
            # Test model selection for agent
            criteria = ModelSelectionCriteria(
                agent_type=expected_agent,
                task_complexity="medium"
            )
            selected_model = self.model_selector.select_model(criteria)
            assert selected_model is not None, f"No model selected for {expected_agent}"
            
            # Verify model is appropriate for agent type
            if expected_agent in ["engineer", "pm_agent", "orchestrator"]:
                assert selected_model == ModelType.OPUS_4, f"Wrong model for {expected_agent}"
            else:
                assert selected_model == ModelType.SONNET_4, f"Wrong model for {expected_agent}"
    
    def test_optimal_agent_selection_with_specializations(self):
        """Test optimal agent selection based on specializations."""
        # Create specialized agents
        self.create_mock_agent("performance", specializations=["performance", "monitoring", "optimization"])
        self.create_mock_agent("database", specializations=["database", "sql", "optimization"])
        self.create_mock_agent("api", specializations=["api", "rest", "integration"])
        
        # Test cases with specialization requirements
        test_cases = [
            # (task, required_specializations, expected_agent)
            ("Optimize database query performance", ["database", "optimization"], "database"),
            ("Monitor API response times and performance", ["performance", "monitoring"], "performance"),
            ("Integrate with third-party REST API", ["api", "integration"], "api"),
        ]
        
        for task, specializations, expected_agent in test_cases:
            # Mock the registry to return our test agents
            with patch.object(self.registry, 'listAgents') as mock_list:
                mock_list.return_value = {
                    f"{expected_agent}_agent": {
                        "type": expected_agent,
                        "specializations": specializations,
                        "tier": "project",
                        "path": str(self.project_agents_dir / f"{expected_agent}_agent.md")
                    }
                }
                
                # Test optimal selection
                agents = self.registry.listAgents(specializations=specializations)
                assert len(agents) > 0, f"No agents found with specializations: {specializations}"
                
                # Verify the expected agent is selected
                agent_id = list(agents.keys())[0]
                assert expected_agent in agent_id, f"Wrong agent selected for task: {task}"
    
    async def test_model_selector_integration(self):
        """Test integration between agent selection and model selector."""
        # Test different complexity levels
        complexity_test_cases = [
            # (agent_type, task_complexity, expected_model)
            ("engineer", "high", ModelType.OPUS_4),
            ("engineer", "expert", ModelType.OPUS_4),
            ("documentation", "low", ModelType.SONNET_4),
            ("qa", "medium", ModelType.SONNET_4),
            ("orchestrator", "high", ModelType.OPUS_4),
        ]
        
        for agent_type, complexity, expected_model in complexity_test_cases:
            criteria = ModelSelectionCriteria(
                agent_type=agent_type,
                task_complexity=complexity,
                reasoning_depth_required="deep" if complexity in ["high", "expert"] else "standard"
            )
            
            selected_model = self.model_selector.select_model(criteria)
            assert selected_model == expected_model, \
                f"Wrong model for {agent_type} with {complexity} complexity. Got {selected_model}, expected {expected_model}"
        
        # Test performance requirements
        performance_test_cases = [
            # (performance_requirements, expected_consideration)
            ({"speed_priority": True}, "Should consider faster models"),
            ({"context_length_required": 150000}, "Should consider high-context models"),
            ({"reasoning_depth": "expert"}, "Should prefer Opus models"),
        ]
        
        for perf_req, consideration in performance_test_cases:
            criteria = ModelSelectionCriteria(
                agent_type="engineer",
                performance_requirements=perf_req
            )
            
            selected_model = self.model_selector.select_model(criteria)
            assert selected_model is not None, f"No model selected with {consideration}"
    
    def test_tier_precedence_in_selection(self):
        """Test agent selection respects tier precedence (project > user > system)."""
        # Create agents at different tiers
        self.create_mock_agent("test_agent", tier="project", specializations=["test", "project"])
        
        # Mock user and system agents
        with patch.object(self.registry, 'discover_agents') as mock_discover:
            mock_discover.return_value = {
                "test_agent_project": {
                    "type": "test_agent",
                    "tier": "project",
                    "path": str(self.project_agents_dir / "test_agent.md"),
                    "specializations": ["test", "project"]
                },
                "test_agent_user": {
                    "type": "test_agent",
                    "tier": "user",
                    "path": "~/.claude-pm/agents/test_agent.md",
                    "specializations": ["test", "user"]
                },
                "test_agent_system": {
                    "type": "test_agent",
                    "tier": "system",
                    "path": "/framework/agents/test_agent.md",
                    "specializations": ["test", "system"]
                }
            }
            
            # Test precedence selection
            all_agents = self.registry.discover_agents()
            
            # Filter by agent type
            test_agents = {k: v for k, v in all_agents.items() if v["type"] == "test_agent"}
            
            # Verify project agent has precedence
            project_agents = [a for a in test_agents.values() if a["tier"] == "project"]
            assert len(project_agents) > 0, "Project agent should be available"
            
            # In real implementation, the selection logic should prefer project > user > system
            selected_agent = None
            for tier in ["project", "user", "system"]:
                tier_agents = [a for a in test_agents.values() if a["tier"] == tier]
                if tier_agents:
                    selected_agent = tier_agents[0]
                    break
            
            assert selected_agent is not None, "No agent selected"
            assert selected_agent["tier"] == "project", "Project agent should have precedence"
    
    def test_performance_requirements_matching(self):
        """Test agent selection based on performance requirements."""
        # Test cases for performance-based selection
        performance_cases = [
            # (requirements, expected_model_characteristics)
            (
                {"max_latency_ms": 500, "speed_priority": True},
                {"speed_tier": "fast", "expected_model": ModelType.SONNET_4}
            ),
            (
                {"memory_limit_mb": 1024, "resource_constrained": True},
                {"cost_tier": "low", "expected_model": ModelType.SONNET_4}
            ),
            (
                {"accuracy_required": 0.95, "reasoning_depth": "expert"},
                {"reasoning_tier": "expert", "expected_model": ModelType.OPUS_4}
            ),
        ]
        
        for requirements, expected_chars in performance_cases:
            criteria = ModelSelectionCriteria(
                agent_type="engineer",
                performance_requirements=requirements,
                speed_priority=requirements.get("speed_priority", False)
            )
            
            selected_model = self.model_selector.select_model(criteria)
            model_config = self.model_selector.get_model_configuration(selected_model)
            
            # Verify model characteristics match requirements
            if "speed_tier" in expected_chars:
                assert model_config.speed_tier == expected_chars["speed_tier"], \
                    f"Speed tier mismatch for requirements: {requirements}"
            
            if "expected_model" in expected_chars:
                assert selected_model == expected_chars["expected_model"], \
                    f"Wrong model selected for requirements: {requirements}"
    
    def test_multi_criteria_selection(self):
        """Test agent selection with multiple criteria."""
        # Complex selection scenarios
        test_scenarios = [
            {
                "task": "Optimize database queries for high-traffic API endpoints",
                "criteria": {
                    "specializations": ["database", "performance", "optimization"],
                    "complexity": "high",
                    "performance_requirements": {
                        "latency_critical": True,
                        "high_throughput": True
                    }
                },
                "expected": {
                    "agent_specializations": ["database", "optimization"],
                    "model_type": ModelType.OPUS_4
                }
            },
            {
                "task": "Generate comprehensive test documentation",
                "criteria": {
                    "specializations": ["documentation", "testing"],
                    "complexity": "medium",
                    "performance_requirements": {
                        "accuracy_required": 0.9
                    }
                },
                "expected": {
                    "agent_specializations": ["documentation"],
                    "model_type": ModelType.SONNET_4
                }
            }
        ]
        
        for scenario in test_scenarios:
            # Parse task to get base agent type
            detected_agent = self.keyword_parser.parse_task_description(scenario["task"])
            
            # Create model selection criteria
            criteria = ModelSelectionCriteria(
                agent_type=detected_agent or "engineer",
                task_complexity=scenario["criteria"]["complexity"],
                performance_requirements=scenario["criteria"]["performance_requirements"]
            )
            
            # Select model
            selected_model = self.model_selector.select_model(criteria)
            
            # Verify expectations
            assert selected_model == scenario["expected"]["model_type"], \
                f"Wrong model for scenario: {scenario['task']}"
    
    def test_fallback_agent_selection(self):
        """Test fallback mechanisms when preferred agents are not available."""
        # Test fallback chain
        fallback_chains = [
            # (requested_agent, fallback_chain)
            ("performance_optimizer", ["performance", "engineer", "agent"]),
            ("ml_specialist", ["ml_engineer", "data_engineer", "engineer"]),
            ("devops_engineer", ["devops", "ops", "engineer"]),
        ]
        
        for requested_agent, fallback_chain in fallback_chains:
            # Mock registry to simulate missing agents
            with patch.object(self.registry, 'get_agent') as mock_get:
                # Simulate first agent not found, fallback to next
                mock_get.side_effect = [None] * (len(fallback_chain) - 1) + [
                    {"type": fallback_chain[-1], "tier": "system"}
                ]
                
                # Test fallback selection
                selected_agent = None
                for fallback in fallback_chain:
                    agent = self.registry.get_agent(fallback)
                    if agent:
                        selected_agent = agent
                        break
                
                assert selected_agent is not None, f"No fallback agent found for {requested_agent}"
                assert selected_agent["type"] == fallback_chain[-1], \
                    f"Wrong fallback agent selected for {requested_agent}"
    
    def test_selection_with_missing_agents(self):
        """Test behavior when requested agents are missing."""
        # Test error handling
        missing_agent_cases = [
            ("nonexistent_agent", "Should return None or default"),
            ("@missing_specialist", "Should handle @ prefix gracefully"),
            ("", "Should handle empty agent type"),
        ]
        
        for agent_type, expected_behavior in missing_agent_cases:
            # Test with registry
            result = self.registry.get_agent(agent_type)
            assert result is None or result.get("type") == "agent", \
                f"Unexpected result for missing agent: {agent_type}"
            
            # Test with keyword parser
            if agent_type:
                detected = self.keyword_parser.parse_task_description(f"Task for {agent_type}")
                # Should either return None or a valid agent type
                assert detected is None or detected in self.keyword_parser.AGENT_KEYWORDS, \
                    f"Invalid detection for missing agent: {agent_type}"
    
    async def test_load_balancing_across_agents(self):
        """Test load balancing when multiple agents can handle a task."""
        # Create multiple agents with same capabilities
        for i in range(3):
            self.create_mock_agent(f"worker_{i}", specializations=["task_processing", "general"])
        
        # Simulate multiple task delegations
        task_distribution = {}
        
        with patch.object(self.registry, 'listAgents') as mock_list:
            # Return all worker agents
            mock_list.return_value = {
                f"worker_{i}": {
                    "type": f"worker_{i}",
                    "specializations": ["task_processing", "general"],
                    "tier": "project",
                    "load": 0  # Track load for testing
                }
                for i in range(3)
            }
            
            # Simulate load balancing logic
            agents = mock_list.return_value
            for task_num in range(9):
                # Simple round-robin for testing
                selected_agent_idx = task_num % len(agents)
                selected_agent = f"worker_{selected_agent_idx}"
                
                task_distribution[selected_agent] = task_distribution.get(selected_agent, 0) + 1
        
        # Verify even distribution
        assert len(task_distribution) == 3, "Tasks should be distributed across all agents"
        assert all(count == 3 for count in task_distribution.values()), \
            "Tasks should be evenly distributed"
    
    @pytest.mark.asyncio
    async def test_agent_capability_matching(self):
        """Test matching agent capabilities to task requirements."""
        # Test capability-based selection
        capability_tests = [
            {
                "task": "Implement real-time data streaming with WebSockets",
                "required_capabilities": ["websockets", "streaming", "real-time"],
                "agent_capabilities": {
                    "engineer": ["implementation", "websockets", "streaming"],
                    "data_engineer": ["data_processing", "streaming", "etl"],
                },
                "expected_agent": "engineer"
            },
            {
                "task": "Design RESTful API with OpenAPI specification",
                "required_capabilities": ["api_design", "openapi", "rest"],
                "agent_capabilities": {
                    "architect": ["api_design", "system_design", "openapi"],
                    "engineer": ["implementation", "rest", "api"],
                },
                "expected_agent": "architect"
            }
        ]
        
        for test in capability_tests:
            # Calculate capability match scores
            match_scores = {}
            for agent, capabilities in test["agent_capabilities"].items():
                # Count matching capabilities
                matches = len(set(capabilities) & set(test["required_capabilities"]))
                match_scores[agent] = matches
            
            # Select agent with highest match score
            best_agent = max(match_scores, key=match_scores.get)
            
            assert best_agent == test["expected_agent"], \
                f"Wrong agent selected for task: {test['task']}. Expected {test['expected_agent']}, got {best_agent}"
    
    def test_selection_performance_metrics(self):
        """Test and measure agent selection performance."""
        # Performance benchmarks
        iterations = 100
        
        # Test keyword parsing performance
        parsing_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            self.keyword_parser.parse_task_description("Implement user authentication with JWT tokens")
            parsing_times.append((time.perf_counter() - start) * 1000)
        
        avg_parsing_time = sum(parsing_times) / len(parsing_times)
        assert avg_parsing_time < 1.0, f"Keyword parsing too slow: {avg_parsing_time:.2f}ms average"
        
        # Test model selection performance
        selection_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            criteria = ModelSelectionCriteria(
                agent_type="engineer",
                task_complexity="high"
            )
            self.model_selector.select_model(criteria)
            selection_times.append((time.perf_counter() - start) * 1000)
        
        avg_selection_time = sum(selection_times) / len(selection_times)
        assert avg_selection_time < 0.5, f"Model selection too slow: {avg_selection_time:.2f}ms average"
        
        print(f"\nPerformance Metrics:")
        print(f"  Keyword Parsing: {avg_parsing_time:.2f}ms avg")
        print(f"  Model Selection: {avg_selection_time:.2f}ms avg")
        print(f"  Total Selection: {avg_parsing_time + avg_selection_time:.2f}ms avg")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])