"""
Comprehensive E2E Tests for Agent Discovery System
Tests the three-tier agent hierarchy, discovery, and registry functionality

Created: 2025-07-19
Purpose: E2E test coverage for EP-0044 agent discovery implementation
"""

import os
import json
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import pytest
import logging

from claude_pm.core.agent_registry import (
    AgentRegistry, 
    AgentMetadata,
    create_agent_registry,
    discover_agents,
    get_core_agent_types,
    get_specialized_agent_types,
    listAgents,
    list_agents
)
from claude_pm.services.agent_registry.utils import CORE_AGENT_TYPES, SPECIALIZED_AGENT_TYPES

logger = logging.getLogger(__name__)


class TestAgentDiscoveryE2E:
    """Comprehensive E2E tests for agent discovery functionality"""
    
    @pytest.fixture
    def temp_hierarchy(self, tmp_path):
        """Create a temporary three-tier agent hierarchy for testing"""
        # Create directory structure
        project_dir = tmp_path / "test_project"
        project_agents = project_dir / ".claude-pm" / "agents" / "project-specific"
        user_agents = tmp_path / "user_home" / ".claude-pm" / "agents" / "user"
        system_agents = tmp_path / "system" / "framework" / "agent-roles"
        
        # Create all directories
        project_agents.mkdir(parents=True)
        user_agents.mkdir(parents=True)
        system_agents.mkdir(parents=True)
        
        # Create test agent files at different tiers
        # System tier - base agents
        self._create_agent_file(
            system_agents / "documentation-agent.md",
            "Documentation Agent",
            "system",
            ["documentation", "markdown", "api_docs"]
        )
        self._create_agent_file(
            system_agents / "qa-agent.md",
            "QA Agent",
            "system",
            ["testing", "validation", "quality_assurance"]
        )
        
        # User tier - customizations
        self._create_agent_file(
            user_agents / "documentation-agent.md",
            "Enhanced Documentation Agent",
            "user",
            ["documentation", "markdown", "api_docs", "changelog", "versioning"]
        )
        self._create_agent_file(
            user_agents / "performance-agent.md",
            "Performance Agent",
            "user",
            ["performance", "optimization", "monitoring"]
        )
        
        # Project tier - project-specific
        self._create_agent_file(
            project_agents / "documentation-agent.md",
            "Project Documentation Agent",
            "project",
            ["documentation", "project_docs", "custom_templates"]
        )
        self._create_agent_file(
            project_agents / "custom-agent.md",
            "Custom Project Agent",
            "project",
            ["custom", "project_specific", "automation"]
        )
        
        return {
            'project_dir': project_dir,
            'project_agents': project_agents,
            'user_agents': user_agents,
            'system_agents': system_agents,
            'user_home': tmp_path / "user_home",
            'tmp_path': tmp_path
        }
    
    def _create_agent_file(self, path: Path, name: str, tier: str, capabilities: List[str]):
        """Helper to create a test agent file"""
        content = f"""# {name}

## Overview
This is a test agent at the {tier} tier.

## Capabilities
{chr(10).join(f'- {cap}' for cap in capabilities)}

## Configuration
- Version: 1.0.0
- Type: {path.stem.replace('-agent', '')}
- Tier: {tier}

## Model Configuration
preferred_model: claude-3-haiku-20240307
temperature: 0.7
"""
        path.write_text(content)
    
    def test_three_tier_discovery(self, temp_hierarchy, monkeypatch):
        """Test agent discovery across all three tiers with proper precedence"""
        # Set up environment
        monkeypatch.chdir(temp_hierarchy['project_dir'])
        monkeypatch.setenv('HOME', str(temp_hierarchy['user_home']))
        
        # Mock the framework path
        import claude_pm
        monkeypatch.setattr(
            'claude_pm.__file__',
            str(temp_hierarchy['tmp_path'] / 'system' / 'claude_pm' / '__init__.py')
        )
        
        # Create registry and discover agents
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Verify discovery found agents from all tiers
        assert len(agents) > 0
        
        # Check that documentation-agent has project tier precedence
        doc_agent = agents.get('documentation-agent')
        assert doc_agent is not None
        assert doc_agent.tier == 'project'
        assert 'project_docs' in doc_agent.capabilities
        
        # Check that qa-agent only exists at system tier
        qa_agent = agents.get('qa-agent')
        assert qa_agent is not None
        assert qa_agent.tier == 'system'
        
        # Check that performance-agent exists at user tier
        perf_agent = agents.get('performance-agent')
        assert perf_agent is not None
        assert perf_agent.tier == 'user'
        
        # Check project-specific agent
        custom_agent = agents.get('custom-agent')
        assert custom_agent is not None
        assert custom_agent.tier == 'project'
    
    def test_agent_metadata_extraction(self, temp_hierarchy, monkeypatch):
        """Test comprehensive metadata extraction from agent files"""
        monkeypatch.chdir(temp_hierarchy['project_dir'])
        monkeypatch.setenv('HOME', str(temp_hierarchy['user_home']))
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Test metadata fields
        for agent_name, agent_metadata in agents.items():
            assert isinstance(agent_metadata, AgentMetadata)
            assert agent_metadata.name == agent_name
            assert agent_metadata.type in CORE_AGENT_TYPES or agent_metadata.type in SPECIALIZED_AGENT_TYPES
            assert agent_metadata.path.endswith('.md')
            assert agent_metadata.tier in ['project', 'user', 'system']
            assert agent_metadata.description
            assert agent_metadata.version == "1.0.0"
            assert isinstance(agent_metadata.capabilities, list)
            assert agent_metadata.last_modified > 0
            assert agent_metadata.file_size > 0
    
    def test_registry_caching(self, temp_hierarchy, monkeypatch):
        """Test agent registry caching behavior"""
        monkeypatch.chdir(temp_hierarchy['project_dir'])
        monkeypatch.setenv('HOME', str(temp_hierarchy['user_home']))
        
        registry = AgentRegistry()
        
        # First discovery should scan directories
        start_time = time.time()
        agents1 = registry.discover_agents(force_refresh=True)
        first_discovery_time = time.time() - start_time
        
        # Second discovery should use cache (much faster)
        start_time = time.time()
        agents2 = registry.discover_agents(force_refresh=False)
        cached_discovery_time = time.time() - start_time
        
        # Cache should be significantly faster
        assert cached_discovery_time < first_discovery_time * 0.5
        assert agents1 == agents2
        
        # Force refresh should rescan
        start_time = time.time()
        agents3 = registry.discover_agents(force_refresh=True)
        forced_discovery_time = time.time() - start_time
        
        # Forced refresh should take similar time to first discovery
        assert forced_discovery_time > cached_discovery_time * 2
    
    def test_agent_modification_detection(self, temp_hierarchy, monkeypatch):
        """Test detection of agent file modifications"""
        monkeypatch.chdir(temp_hierarchy['project_dir'])
        monkeypatch.setenv('HOME', str(temp_hierarchy['user_home']))
        
        registry = AgentRegistry()
        agents1 = registry.discover_agents(force_refresh=True)
        
        # Modify an agent file
        doc_agent_path = temp_hierarchy['project_agents'] / "documentation-agent.md"
        original_content = doc_agent_path.read_text()
        doc_agent_path.write_text(original_content + "\n## Modified: true")
        
        # Wait a moment to ensure modification time changes
        time.sleep(0.1)
        
        # Rediscover with force refresh
        agents2 = registry.discover_agents(force_refresh=True)
        
        # Check that modification was detected
        doc_agent1 = agents1.get('documentation-agent')
        doc_agent2 = agents2.get('documentation-agent')
        
        assert doc_agent2.last_modified > doc_agent1.last_modified
        assert doc_agent2.file_size > doc_agent1.file_size
    
    def test_malformed_agent_handling(self, temp_hierarchy, monkeypatch):
        """Test handling of malformed agent files"""
        monkeypatch.chdir(temp_hierarchy['project_dir'])
        monkeypatch.setenv('HOME', str(temp_hierarchy['user_home']))
        
        # Create malformed agent files
        malformed_path = temp_hierarchy['project_agents'] / "malformed-agent.md"
        malformed_path.write_text("This is not a valid agent file")
        
        empty_path = temp_hierarchy['project_agents'] / "empty-agent.md"
        empty_path.write_text("")
        
        # Registry should handle these gracefully
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Should still discover valid agents
        assert len(agents) > 0
        assert 'documentation-agent' in agents
        
        # Malformed agents might be included but with minimal metadata
        if 'malformed-agent' in agents:
            malformed = agents['malformed-agent']
            assert malformed.tier == 'project'
            assert malformed.type != ''  # Should have inferred type
    
    def test_performance_with_many_agents(self, tmp_path, monkeypatch):
        """Test discovery performance with many agent files"""
        # Create directory with many agents
        agents_dir = tmp_path / ".claude-pm" / "agents"
        agents_dir.mkdir(parents=True)
        
        # Create 100 test agents
        for i in range(100):
            agent_type = ['qa', 'documentation', 'engineer', 'ops', 'security'][i % 5]
            self._create_agent_file(
                agents_dir / f"{agent_type}-variant{i}-agent.md",
                f"{agent_type.title()} Variant {i}",
                "project",
                [agent_type, f"variant_{i}", "testing"]
            )
        
        monkeypatch.chdir(tmp_path)
        
        # Time discovery
        registry = AgentRegistry()
        start_time = time.time()
        agents = registry.discover_agents(force_refresh=True)
        discovery_time = time.time() - start_time
        
        # Should discover all agents
        assert len(agents) == 100
        
        # Should complete in reasonable time (less than 2 seconds)
        assert discovery_time < 2.0
        
        # Cache should be very fast
        start_time = time.time()
        cached_agents = registry.discover_agents(force_refresh=False)
        cache_time = time.time() - start_time
        
        assert cache_time < 0.1  # Cache should be under 100ms
        assert len(cached_agents) == 100
    
    def test_core_api_functions(self, temp_hierarchy, monkeypatch):
        """Test core API convenience functions"""
        monkeypatch.chdir(temp_hierarchy['project_dir'])
        monkeypatch.setenv('HOME', str(temp_hierarchy['user_home']))
        
        import claude_pm
        monkeypatch.setattr(
            'claude_pm.__file__',
            str(temp_hierarchy['tmp_path'] / 'system' / 'claude_pm' / '__init__.py')
        )
        
        # Test create_agent_registry
        registry = create_agent_registry()
        assert isinstance(registry, AgentRegistry)
        
        # Test discover_agents function
        agents = discover_agents(force_refresh=True)
        assert isinstance(agents, dict)
        assert len(agents) > 0
        
        # Test get_core_agent_types
        core_types = get_core_agent_types()
        assert isinstance(core_types, set)
        assert 'documentation' in core_types
        assert 'qa' in core_types
        
        # Test get_specialized_agent_types
        specialized_types = get_specialized_agent_types()
        assert isinstance(specialized_types, set)
        assert 'architecture' in specialized_types
        assert 'performance' in specialized_types
        
        # Test listAgents (camelCase)
        agents_camel = listAgents()
        assert isinstance(agents_camel, dict)
        assert len(agents_camel) > 0
        
        # Test list_agents with filters
        qa_agents = list_agents(agent_type='qa')
        assert all(agent.type == 'qa' for agent in qa_agents.values())
        
        project_agents = list_agents(tier='project')
        assert all(agent.tier == 'project' for agent in project_agents.values())
    
    def test_edge_cases(self, tmp_path, monkeypatch):
        """Test edge cases and error conditions"""
        monkeypatch.chdir(tmp_path)
        
        # Test with no agents
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        assert isinstance(agents, dict)
        assert len(agents) == 0  # No agents found
        
        # Test with non-existent paths
        registry.discovery_paths.append(tmp_path / "non_existent")
        agents = registry.discover_agents(force_refresh=True)
        assert isinstance(agents, dict)  # Should not crash
        
        # Test with permission issues (if possible to simulate)
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()
        restricted_file = restricted_dir / "test-agent.md"
        self._create_agent_file(restricted_file, "Test Agent", "project", ["test"])
        
        # Try to make it unreadable (may not work on all systems)
        try:
            os.chmod(restricted_file, 0o000)
            registry.discovery_paths = [restricted_dir]
            agents = registry.discover_agents(force_refresh=True)
            assert isinstance(agents, dict)  # Should handle gracefully
        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_file, 0o644)
    
    def test_agent_type_classification(self, temp_hierarchy, monkeypatch):
        """Test agent type classification logic"""
        monkeypatch.chdir(temp_hierarchy['project_dir'])
        monkeypatch.setenv('HOME', str(temp_hierarchy['user_home']))
        
        # Create agents with various naming patterns
        agents_dir = temp_hierarchy['project_agents']
        
        # Standard pattern
        self._create_agent_file(
            agents_dir / "researcher-agent.md",
            "Research Agent",
            "project",
            ["research", "analysis"]
        )
        
        # Compound name
        self._create_agent_file(
            agents_dir / "data-engineer-agent.md",
            "Data Engineer Agent",
            "project",
            ["data", "engineering", "etl"]
        )
        
        # Non-standard but valid
        self._create_agent_file(
            agents_dir / "ml-specialist-agent.md",
            "ML Specialist",
            "project",
            ["machine_learning", "ai", "modeling"]
        )
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Verify type classification
        assert agents['researcher-agent'].type == 'research'
        assert agents['data-engineer-agent'].type == 'data_engineer'
        
        # ML specialist should be classified as specialized type
        ml_agent = agents.get('ml-specialist-agent')
        assert ml_agent is not None
        assert ml_agent.type in SPECIALIZED_AGENT_TYPES or ml_agent.type == 'ml_specialist'
    
    def test_directory_precedence(self, temp_hierarchy, monkeypatch):
        """Test that directory precedence is properly applied"""
        monkeypatch.chdir(temp_hierarchy['project_dir'])
        monkeypatch.setenv('HOME', str(temp_hierarchy['user_home']))
        
        import claude_pm
        monkeypatch.setattr(
            'claude_pm.__file__',
            str(temp_hierarchy['tmp_path'] / 'system' / 'claude_pm' / '__init__.py')
        )
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Documentation agent should have project tier (highest precedence)
        doc_agent = agents['documentation-agent']
        assert doc_agent.tier == 'project'
        assert 'project_docs' in doc_agent.capabilities
        
        # Create a test to verify user overrides system
        # Remove project documentation agent
        project_doc = temp_hierarchy['project_agents'] / "documentation-agent.md"
        project_doc.unlink()
        
        # Rediscover
        agents = registry.discover_agents(force_refresh=True)
        
        # Now documentation agent should be from user tier
        doc_agent = agents['documentation-agent']
        assert doc_agent.tier == 'user'
        assert 'changelog' in doc_agent.capabilities  # User tier capability
        
        # Remove user agent too
        user_doc = temp_hierarchy['user_agents'] / "documentation-agent.md"
        user_doc.unlink()
        
        # Rediscover
        agents = registry.discover_agents(force_refresh=True)
        
        # Now should fall back to system
        doc_agent = agents['documentation-agent']
        assert doc_agent.tier == 'system'
        assert 'changelog' not in doc_agent.capabilities