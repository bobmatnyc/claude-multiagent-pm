"""
E2E Tests for Agent Discovery Edge Cases and Error Scenarios
Tests unusual conditions, error handling, and boundary cases

Created: 2025-07-19  
Purpose: Comprehensive edge case testing for EP-0044 agent discovery
"""

import os
import sys
import json
import time
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import logging

from claude_pm.core.agent_registry import (
    AgentRegistry,
    AgentMetadata,
    create_agent_registry,
    discover_agents
)
from claude_pm.services.agent_registry.utils import (
    CORE_AGENT_TYPES,
    SPECIALIZED_AGENT_TYPES,
    determine_tier,
    extract_specialized_metadata
)

logger = logging.getLogger(__name__)


class TestAgentDiscoveryEdgeCases:
    """Edge case and error scenario tests for agent discovery"""
    
    @pytest.fixture
    def edge_case_setup(self, tmp_path):
        """Setup for edge case testing"""
        return {
            'tmp_path': tmp_path,
            'agents_dir': tmp_path / ".claude-pm" / "agents",
            'user_home': tmp_path / "user_home",
            'system_dir': tmp_path / "system"
        }
    
    def test_empty_agent_files(self, edge_case_setup, monkeypatch):
        """Test handling of empty agent files"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Create empty files
        (agents_dir / "empty-agent.md").touch()
        (agents_dir / "whitespace-agent.md").write_text("   \n\t\n   ")
        
        # Create valid agent for comparison
        (agents_dir / "valid-agent.md").write_text("""# Valid Agent
## Capabilities
- testing
## Version
1.0.0""")
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Should at least find the valid agent
        assert 'valid-agent' in agents
        
        # Empty agents might be skipped or have minimal metadata
        if 'empty-agent' in agents:
            assert agents['empty-agent'].tier in ['project', 'user', 'system']
    
    def test_unicode_and_special_characters(self, edge_case_setup, monkeypatch):
        """Test handling of unicode and special characters in agent files"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Create agents with unicode content
        unicode_content = """# Documentation Agent 文档代理 📚

## Overview
This agent handles documentation with émojis and 中文字符.

## Capabilities
- Documentation générale
- API ドキュメント
- Émoji support 🎉
- Special chars: @#$%^&*()

## Version
1.0.0-β1
"""
        
        (agents_dir / "unicode-agent.md").write_text(unicode_content, encoding='utf-8')
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Should handle unicode gracefully
        assert 'unicode-agent' in agents
        unicode_agent = agents['unicode-agent']
        assert unicode_agent.version == "1.0.0-β1"
    
    def test_very_large_agent_files(self, edge_case_setup, monkeypatch):
        """Test handling of unusually large agent files"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Create a very large agent file (5MB)
        large_content = """# Large Agent

## Capabilities
- testing
- large file handling

## Description
""" + ("This is a very long description. " * 50000) + """

## Version
1.0.0
"""
        
        large_file = agents_dir / "large-agent.md"
        large_file.write_text(large_content)
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Should handle large files
        assert 'large-agent' in agents
        large_agent = agents['large-agent']
        assert large_agent.file_size > 5_000_000  # Over 5MB
        assert large_agent.type != ''
    
    def test_circular_symlinks(self, edge_case_setup, monkeypatch):
        """Test handling of circular symlinks in agent directories"""
        if sys.platform == 'win32':
            pytest.skip("Symlink test not reliable on Windows")
        
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Create circular symlink
        link_dir = agents_dir / "linked"
        link_dir.mkdir()
        try:
            os.symlink(str(agents_dir), str(link_dir / "circular"))
        except OSError:
            pytest.skip("Cannot create symlinks on this system")
        
        # Create a normal agent
        (agents_dir / "normal-agent.md").write_text("""# Normal Agent
## Version
1.0.0""")
        
        registry = AgentRegistry()
        # Should not hang or crash
        agents = registry.discover_agents(force_refresh=True)
        
        assert 'normal-agent' in agents
    
    def test_permission_denied_scenarios(self, edge_case_setup, monkeypatch):
        """Test handling of permission-denied scenarios"""
        if sys.platform == 'win32':
            pytest.skip("Permission test not reliable on Windows")
        
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Create agents
        readable_agent = agents_dir / "readable-agent.md"
        readable_agent.write_text("""# Readable Agent
## Version
1.0.0""")
        
        unreadable_agent = agents_dir / "unreadable-agent.md"
        unreadable_agent.write_text("""# Unreadable Agent
## Version
1.0.0""")
        
        # Make one unreadable
        try:
            os.chmod(unreadable_agent, 0o000)
            
            registry = AgentRegistry()
            agents = registry.discover_agents(force_refresh=True)
            
            # Should find readable agent
            assert 'readable-agent' in agents
            
            # May or may not find unreadable agent depending on implementation
        finally:
            # Restore permissions
            os.chmod(unreadable_agent, 0o644)
    
    def test_concurrent_file_modifications(self, edge_case_setup, monkeypatch):
        """Test behavior when files are modified during discovery"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Create initial agents
        for i in range(10):
            (agents_dir / f"agent{i}-agent.md").write_text(f"""# Agent {i}
## Version
1.0.0""")
        
        # Start discovery in thread while modifying files
        import threading
        
        registry = AgentRegistry()
        results = []
        errors = []
        
        def discover():
            try:
                agents = registry.discover_agents(force_refresh=True)
                results.append(agents)
            except Exception as e:
                errors.append(e)
        
        def modify_files():
            time.sleep(0.01)  # Small delay
            # Modify files during discovery
            for i in range(5):
                agent_file = agents_dir / f"agent{i}-agent.md"
                if agent_file.exists():
                    agent_file.write_text(f"""# Modified Agent {i}
## Version
2.0.0""")
        
        # Run concurrently
        discover_thread = threading.Thread(target=discover)
        modify_thread = threading.Thread(target=modify_files)
        
        discover_thread.start()
        modify_thread.start()
        
        discover_thread.join()
        modify_thread.join()
        
        # Should complete without errors
        assert len(errors) == 0
        assert len(results) == 1
    
    def test_malformed_json_in_cache(self, edge_case_setup, monkeypatch):
        """Test recovery from corrupted cache files"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        # Create cache directory with corrupted files
        cache_dir = edge_case_setup['tmp_path'] / ".claude-pm" / "cache"
        cache_dir.mkdir(parents=True)
        
        # Various corruption scenarios
        (cache_dir / "agent_registry_cache.json").write_text("{corrupted")
        (cache_dir / "discovery_cache.json").write_text("null")
        (cache_dir / "metadata_cache.json").write_text('{"half": "formed"')
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        (agents_dir / "test-agent.md").write_text("""# Test Agent
## Version
1.0.0""")
        
        # Should recover and perform fresh discovery
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=False)  # Try to use cache
        
        assert 'test-agent' in agents
    
    def test_agent_name_edge_cases(self, edge_case_setup, monkeypatch):
        """Test handling of unusual agent names"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Various edge case names
        edge_names = [
            "agent.with.dots-agent.md",
            "UPPERCASE-AGENT.md",
            "123-numeric-agent.md",
            "-leading-dash-agent.md",
            "very-long-name-that-exceeds-reasonable-limits-for-agent-names-agent.md",
            "agent_with_underscores-agent.md",
            "agent@special#chars-agent.md",
            "agent agent.md",  # Space in name
        ]
        
        for name in edge_names:
            try:
                (agents_dir / name).write_text(f"""# {name}
## Version
1.0.0""")
            except OSError:
                # Some filesystems may not support certain names
                continue
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Should discover at least some agents
        assert len(agents) > 0
    
    def test_discovery_without_framework(self, edge_case_setup, monkeypatch):
        """Test discovery when framework is not properly installed"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        # Mock ImportError for claude_pm
        with patch('claude_pm.services.agent_registry.discovery.claude_pm', side_effect=ImportError):
            agents_dir = edge_case_setup['agents_dir']
            agents_dir.mkdir(parents=True)
            
            (agents_dir / "local-agent.md").write_text("""# Local Agent
## Version
1.0.0""")
            
            registry = AgentRegistry()
            agents = registry.discover_agents(force_refresh=True)
            
            # Should still find local agents
            assert 'local-agent' in agents
    
    def test_memory_efficiency_with_many_agents(self, edge_case_setup, monkeypatch):
        """Test memory efficiency with thousands of agents"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Create 1000 small agents
        for i in range(1000):
            (agents_dir / f"agent{i:04d}-agent.md").write_text(f"""# Agent {i}
## Capabilities
- capability_{i}
## Version
1.0.{i}""")
        
        import psutil
        process = psutil.Process()
        
        # Measure memory before discovery
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # Measure memory after discovery
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before
        
        assert len(agents) == 1000
        # Memory increase should be reasonable (less than 100MB for 1000 agents)
        assert mem_increase < 100, f"Memory increased by {mem_increase:.1f}MB"
    
    def test_agent_type_inference_edge_cases(self, edge_case_setup, monkeypatch):
        """Test agent type inference for unusual patterns"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        # Create agents with ambiguous names
        test_cases = [
            ("multi-function-specialist-agent.md", "# Multi Function Agent\n## Capabilities\n- qa\n- documentation\n- engineering"),
            ("generic-agent.md", "# Generic Agent"),
            ("unknown-type-agent.md", "# Mystery Agent\n## Does stuff"),
            ("qa-documentation-hybrid-agent.md", "# QA Documentation Hybrid"),
        ]
        
        for filename, content in test_cases:
            (agents_dir / filename).write_text(content + "\n## Version\n1.0.0")
        
        registry = AgentRegistry()
        agents = registry.discover_agents(force_refresh=True)
        
        # All should be discovered with some type
        for filename, _ in test_cases:
            agent_name = filename.replace('.md', '')
            assert agent_name in agents
            agent = agents[agent_name]
            assert agent.type != ''  # Should infer some type
    
    def test_race_conditions_in_caching(self, edge_case_setup, monkeypatch):
        """Test handling of race conditions in cache operations"""
        monkeypatch.chdir(edge_case_setup['tmp_path'])
        
        agents_dir = edge_case_setup['agents_dir']
        agents_dir.mkdir(parents=True)
        
        (agents_dir / "test-agent.md").write_text("""# Test Agent
## Version
1.0.0""")
        
        # Simulate concurrent cache access
        import threading
        
        registries = [AgentRegistry() for _ in range(3)]
        results = []
        errors = []
        
        def concurrent_discover(registry):
            try:
                agents = registry.discover_agents(force_refresh=True)
                results.append(len(agents))
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=concurrent_discover, args=(reg,))
            for reg in registries
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # All should succeed
        assert len(errors) == 0
        assert len(results) == 3
        assert all(r == results[0] for r in results)  # All should find same agents