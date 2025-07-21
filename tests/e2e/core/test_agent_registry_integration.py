"""
E2E Tests for Agent Registry Integration
Tests integration with other framework components and real-world usage patterns

Created: 2025-07-19
Purpose: Integration testing for EP-0044 agent registry implementation
"""

import os
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Optional
import pytest
import logging

from claude_pm.core.agent_registry import (
    AgentRegistry,
    AgentMetadata,
    get_agent,
    get_registry_stats,
    discover_agents_sync
)
from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.agent_registry.utils import (
    CORE_AGENT_TYPES,
    SPECIALIZED_AGENT_TYPES,
    determine_tier,
    has_tier_precedence
)

logger = logging.getLogger(__name__)


class TestAgentRegistryIntegration:
    """Tests for Agent Registry integration with framework components"""
    
    @pytest.fixture
    def mock_agents_dir(self, tmp_path):
        """Create a mock agents directory with test agents"""
        agents_dir = tmp_path / ".claude-pm" / "agents"
        agents_dir.mkdir(parents=True)
        
        # Create various agent types
        agent_configs = [
            ("documentation-agent.md", "documentation", ["docs", "api", "changelog"]),
            ("qa-agent.md", "qa", ["testing", "validation", "ci"]),
            ("engineer-agent.md", "engineer", ["code", "implementation", "refactoring"]),
            ("data-engineer-agent.md", "data_engineer", ["data", "etl", "analytics"]),
            ("performance-agent.md", "performance", ["optimization", "profiling", "monitoring"]),
            ("architecture-agent.md", "architecture", ["design", "patterns", "structure"]),
            ("security-agent.md", "security", ["audit", "vulnerability", "compliance"]),
            ("devops-agent.md", "ops", ["deployment", "infrastructure", "automation"]),
            ("research-agent.md", "research", ["investigation", "analysis", "documentation"])
        ]
        
        for filename, agent_type, capabilities in agent_configs:
            self._create_test_agent(agents_dir / filename, agent_type, capabilities)
        
        return agents_dir
    
    def _create_test_agent(self, path: Path, agent_type: str, capabilities: list):
        """Helper to create test agent files"""
        content = f"""# {agent_type.replace('_', ' ').title()} Agent

## Overview
Test agent for {agent_type} operations.

## Capabilities
{chr(10).join(f'- {cap}' for cap in capabilities)}

## Model Configuration
preferred_model: claude-3-haiku-20240307
temperature: 0.7
max_tokens: 4096

## Specializations
- {agent_type}
{chr(10).join(f'- {cap}' for cap in capabilities[:2])}

## Version
1.0.0
"""
        path.write_text(content)
    
    def test_shared_prompt_cache_integration(self, mock_agents_dir, monkeypatch):
        """Test integration with SharedPromptCache for performance optimization"""
        monkeypatch.chdir(mock_agents_dir.parent.parent)
        
        # Create cache service
        cache = SharedPromptCache()
        
        # Create registry with cache
        registry = AgentRegistry(cache_service=cache)
        
        # First discovery - should populate cache
        agents1 = registry.discover_agents(force_refresh=True)
        assert len(agents1) > 0
        
        # Check that cache was populated
        assert cache.stats()['total_prompts'] > 0
        
        # Second discovery - should benefit from cache
        cache_stats_before = cache.stats()
        agents2 = registry.discover_agents(force_refresh=False)
        cache_stats_after = cache.stats()
        
        # Should have cache hits
        assert cache_stats_after['cache_hits'] > cache_stats_before.get('cache_hits', 0)
        assert agents1 == agents2
    
    def test_model_selector_integration(self, mock_agents_dir, monkeypatch):
        """Test integration with model selector for agent-specific models"""
        monkeypatch.chdir(mock_agents_dir.parent.parent)
        
        # Mock model selector
        class MockModelSelector:
            def get_model_for_agent(self, agent_type: str, complexity: str = "medium") -> str:
                if agent_type in ["architecture", "security"]:
                    return "claude-3-opus-20240229"
                elif agent_type in ["documentation", "qa"]:
                    return "claude-3-sonnet-20240229"
                else:
                    return "claude-3-haiku-20240307"
        
        model_selector = MockModelSelector()
        registry = AgentRegistry(model_selector=model_selector)
        
        agents = registry.discover_agents(force_refresh=True)
        
        # Verify model selection based on agent type
        if 'architecture-agent' in agents:
            arch_agent = agents['architecture-agent']
            # Model might be from file or selector
            assert arch_agent.preferred_model in [
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ]
    
    def test_concurrent_discovery(self, mock_agents_dir, monkeypatch):
        """Test thread-safe concurrent agent discovery"""
        monkeypatch.chdir(mock_agents_dir.parent.parent)
        
        import threading
        import concurrent.futures
        
        registry = AgentRegistry()
        results = []
        errors = []
        
        def discover_agents_thread():
            try:
                agents = registry.discover_agents(force_refresh=True)
                results.append(agents)
            except Exception as e:
                errors.append(e)
        
        # Run concurrent discoveries
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(discover_agents_thread) for _ in range(5)]
            concurrent.futures.wait(futures)
        
        # Should have no errors
        assert len(errors) == 0
        
        # All results should be consistent
        assert len(results) == 5
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
    
    def test_registry_stats_functionality(self, mock_agents_dir, monkeypatch):
        """Test get_registry_stats functionality"""
        monkeypatch.chdir(mock_agents_dir.parent.parent)
        
        # Discover agents first
        agents = discover_agents_sync()
        
        # Get registry stats
        stats = get_registry_stats()
        
        assert 'total_agents' in stats
        assert 'agents_by_type' in stats
        assert 'agents_by_tier' in stats
        assert 'discovery_time' in stats
        assert 'cache_status' in stats
        
        # Verify counts
        assert stats['total_agents'] == len(agents)
        assert sum(stats['agents_by_type'].values()) == stats['total_agents']
    
    def test_get_agent_functionality(self, mock_agents_dir, monkeypatch):
        """Test get_agent helper function"""
        monkeypatch.chdir(mock_agents_dir.parent.parent)
        
        # Discover agents
        discover_agents_sync()
        
        # Test getting existing agent
        doc_agent = get_agent('documentation-agent')
        assert doc_agent is not None
        assert isinstance(doc_agent, AgentMetadata)
        assert doc_agent.type == 'documentation'
        
        # Test getting non-existent agent
        missing_agent = get_agent('non-existent-agent')
        assert missing_agent is None
    
    def test_real_world_usage_patterns(self, mock_agents_dir, monkeypatch):
        """Test real-world usage patterns from CLAUDE.md"""
        monkeypatch.chdir(mock_agents_dir.parent.parent)
        
        # Pattern 1: Task-specific agent discovery
        registry = AgentRegistry()
        agents = registry.listAgents()
        
        # Find agents with specific specializations
        performance_agents = [
            (name, meta) for name, meta in agents.items()
            if 'performance' in meta.get('specializations', []) or
               'optimization' in meta.get('capabilities', [])
        ]
        assert len(performance_agents) > 0
        
        # Pattern 2: Select optimal agent for task
        task_type = "performance_optimization"
        required_specs = ["performance", "monitoring"]
        
        matching_agents = {}
        for name, meta in agents.items():
            agent_caps = meta.get('capabilities', [])
            agent_specs = meta.get('specializations', [])
            if any(spec in agent_caps + agent_specs for spec in required_specs):
                matching_agents[name] = meta
        
        assert len(matching_agents) > 0
        
        # Pattern 3: Filter by tier for specific use cases
        all_agents = registry.discover_agents()
        project_agents = {
            name: agent for name, agent in all_agents.items()
            if agent.tier == 'project'
        }
        # In this test, all agents are in current dir, so tier might be 'project'
    
    def test_agent_modification_tracking(self, mock_agents_dir, monkeypatch):
        """Test agent modification detection and tracking"""
        monkeypatch.chdir(mock_agents_dir.parent.parent)
        
        registry = AgentRegistry()
        
        # Initial discovery
        agents1 = registry.discover_agents(force_refresh=True)
        initial_count = len(agents1)
        
        # Add a new agent
        new_agent_path = mock_agents_dir / "new-test-agent.md"
        self._create_test_agent(new_agent_path, "test", ["testing", "validation"])
        
        # Rediscover
        agents2 = registry.discover_agents(force_refresh=True)
        
        # Should find the new agent
        assert len(agents2) == initial_count + 1
        assert 'new-test-agent' in agents2
        
        # Modify existing agent
        qa_agent_path = mock_agents_dir / "qa-agent.md"
        content = qa_agent_path.read_text()
        qa_agent_path.write_text(content + "\n## Modified: true")
        
        # Rediscover and check modification
        agents3 = registry.discover_agents(force_refresh=True)
        
        qa_agent_new = agents3['qa-agent']
        qa_agent_old = agents1['qa-agent']
        
        assert qa_agent_new.last_modified > qa_agent_old.last_modified
        assert qa_agent_new.file_size > qa_agent_old.file_size
    
    def test_error_handling_and_recovery(self, tmp_path, monkeypatch):
        """Test error handling and recovery mechanisms"""
        monkeypatch.chdir(tmp_path)
        
        # Test with corrupted cache
        cache_dir = tmp_path / ".claude-pm" / "cache"
        cache_dir.mkdir(parents=True)
        
        # Create corrupted cache file
        cache_file = cache_dir / "agent_registry_cache.json"
        cache_file.write_text("{ corrupted json")
        
        # Registry should handle gracefully
        registry = AgentRegistry()
        agents = registry.discover_agents()
        assert isinstance(agents, dict)  # Should return empty dict or discover fresh
        
        # Test with invalid agent metadata
        agents_dir = tmp_path / ".claude-pm" / "agents"
        agents_dir.mkdir(parents=True)
        
        # Create agent with invalid content
        invalid_agent = agents_dir / "invalid-agent.md"
        invalid_agent.write_bytes(b'\x00\x01\x02\x03')  # Binary content
        
        # Should handle gracefully
        agents = registry.discover_agents(force_refresh=True)
        assert isinstance(agents, dict)
        # Invalid agent might be skipped or included with minimal metadata
    
    def test_backward_compatibility(self, mock_agents_dir, monkeypatch):
        """Test backward compatibility with legacy code"""
        monkeypatch.chdir(mock_agents_dir.parent.parent)
        
        # Test old import paths still work
        from claude_pm.services.agent_registry import AgentRegistry as ServiceRegistry
        from claude_pm.services.agent_registry_sync import AgentRegistry as SyncRegistry
        from claude_pm.core.agent_registry import AgentRegistry as CoreRegistry
        
        # All should be the same class
        assert ServiceRegistry == SyncRegistry == CoreRegistry
        
        # Test legacy method names
        registry = AgentRegistry()
        
        # Both camelCase and snake_case should work
        agents_camel = registry.listAgents()
        agents_snake = list_agents()
        
        assert isinstance(agents_camel, dict)
        assert isinstance(agents_snake, dict)
    
    def test_performance_benchmarks(self, tmp_path, monkeypatch):
        """Test performance benchmarks for agent discovery"""
        import time
        
        monkeypatch.chdir(tmp_path)
        
        # Create a large number of agents
        agents_dir = tmp_path / ".claude-pm" / "agents"
        agents_dir.mkdir(parents=True)
        
        # Create 500 agents
        for i in range(500):
            agent_type = CORE_AGENT_TYPES[i % len(CORE_AGENT_TYPES)]
            self._create_test_agent(
                agents_dir / f"{agent_type}-variant{i}-agent.md",
                agent_type,
                [agent_type, f"variant_{i}"]
            )
        
        registry = AgentRegistry()
        
        # Benchmark discovery
        start = time.time()
        agents = registry.discover_agents(force_refresh=True)
        discovery_time = time.time() - start
        
        assert len(agents) == 500
        assert discovery_time < 5.0  # Should complete within 5 seconds
        
        # Benchmark cache performance
        start = time.time()
        cached_agents = registry.discover_agents(force_refresh=False)
        cache_time = time.time() - start
        
        assert cache_time < 0.5  # Cache should be under 500ms
        assert len(cached_agents) == 500
        
        # Log performance metrics
        logger.info(f"Discovery time for 500 agents: {discovery_time:.3f}s")
        logger.info(f"Cache retrieval time: {cache_time:.3f}s")
        logger.info(f"Performance improvement: {discovery_time / cache_time:.1f}x")