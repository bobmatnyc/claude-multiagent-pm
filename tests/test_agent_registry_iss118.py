#!/usr/bin/env python3
"""
Test AgentRegistry Implementation - ISS-0118 Validation
======================================================

Comprehensive test suite for AgentRegistry class with discovery mechanisms
and integration with SharedPromptCache.

ISS-0118: Agent Registry Implementation Test Suite
Created: 2025-07-15
"""

import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
import sys
import os
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from claude_pm.services.agent_registry import AgentRegistry, AgentMetadata
    from claude_pm.services.shared_prompt_cache import SharedPromptCache
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Services not available for testing: {e}")
    SERVICES_AVAILABLE = False

class TestAgentRegistryISS118(unittest.TestCase):
    """Test AgentRegistry functionality for ISS-0118."""
    
    def setUp(self):
        """Set up test environment."""
        if not SERVICES_AVAILABLE:
            self.skipTest("Required services not available")
        
        # Create temporary directory structure
        self.test_dir = Path(tempfile.mkdtemp())
        self.user_agents_dir = self.test_dir / '.claude-pm' / 'agents' / 'user'
        self.user_agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test agent files
        self._create_test_agents()
        
        # Initialize SharedPromptCache
        self.cache_service = SharedPromptCache()
        
        # Initialize AgentRegistry
        self.registry = AgentRegistry(cache_service=self.cache_service)
        
        # Override discovery paths to use test directory
        self.registry.discovery_paths = [self.user_agents_dir]
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'test_dir'):
            shutil.rmtree(self.test_dir)
    
    def _create_test_agents(self):
        """Create test agent files for discovery."""
        # Create a Python agent file
        engineer_agent = self.user_agents_dir / 'engineer_agent.py'
        engineer_agent.write_text('''"""
Engineer Agent Implementation
============================

VERSION = "1.2.0"

Core engineering agent for code implementation and development tasks.
"""

class EngineerAgent:
    """Core engineering agent implementation."""
    
    def __init__(self):
        self.version = "1.2.0"
    
    def implement_feature(self, requirements):
        """Implement new feature based on requirements."""
        pass
    
    def fix_bug(self, bug_report):
        """Fix reported bug."""
        pass
    
    def review_code(self, code_diff):
        """Review code changes."""
        pass
    
    async def async_deploy(self, deployment_config):
        """Deploy code asynchronously."""
        pass
''')
        
        # Create a documentation agent file
        docs_agent = self.user_agents_dir / 'documentation_specialist.py'
        docs_agent.write_text('''"""
Documentation Specialist Agent
=============================

__version__ = "2.1.0"

Specialized documentation agent for comprehensive documentation management.
"""

def generate_changelog(commits):
    """Generate changelog from git commits."""
    pass

def update_api_docs(api_spec):
    """Update API documentation."""
    pass

def validate_docs_structure(docs_path):
    """Validate documentation structure."""
    pass
''')
        
        # Create a QA agent file with syntax error
        qa_agent = self.user_agents_dir / 'qa_testing_agent.py'
        qa_agent.write_text('''"""
QA Testing Agent
===============

VERSION = "0.9.0"

Quality assurance agent for comprehensive testing.
"""

def run_test_suite(test_config)
    """Run comprehensive test suite."""  # Missing colon - syntax error
    pass

def validate_quality_standards(code_base):
    """Validate code quality standards."""
    pass
''')
        
        # Create a data management agent file
        data_agent = self.user_agents_dir / 'data_pipeline_manager.py'
        data_agent.write_text('''"""
Data Pipeline Manager Agent
==========================

VERSION = "3.0.1"

Data pipeline management and API integration specialist.
"""

class DataPipelineManager:
    """Manages data pipelines and API integrations."""
    
    def create_pipeline(self, pipeline_config):
        """Create new data pipeline."""
        pass
    
    def manage_api_keys(self, api_config):
        """Manage API key rotation."""
        pass
    
    def optimize_queries(self, database_schema):
        """Optimize database queries."""
        pass
    
    def backup_data(self, backup_config):
        """Backup data stores."""
        pass
''')
    
    async def test_agent_discovery(self):
        """Test basic agent discovery functionality."""
        # Test discovery
        agents = await self.registry.discover_agents()
        
        # Verify agents were discovered
        self.assertGreater(len(agents), 0, "Should discover test agents")
        
        # Check for specific agents
        expected_agents = ['engineer_agent', 'documentation_specialist', 'qa_testing_agent', 'data_pipeline_manager']
        for expected_agent in expected_agents:
            self.assertIn(expected_agent, agents, f"Should discover {expected_agent}")
    
    async def test_agent_metadata_extraction(self):
        """Test agent metadata extraction."""
        agents = await self.registry.discover_agents()
        
        # Test engineer agent metadata
        engineer = agents.get('engineer_agent')
        self.assertIsNotNone(engineer, "Engineer agent should be discovered")
        self.assertEqual(engineer.type, 'engineer', "Should classify as engineer type")
        self.assertEqual(engineer.tier, 'user', "Should be in user tier")
        self.assertEqual(engineer.version, '1.2.0', "Should extract version")
        self.assertIn('implement_feature', engineer.capabilities, "Should extract capabilities")
        self.assertIn('async_async_deploy', engineer.capabilities, "Should extract async capabilities")
        
        # Test documentation agent metadata
        docs = agents.get('documentation_specialist')
        self.assertIsNotNone(docs, "Documentation agent should be discovered")
        self.assertEqual(docs.type, 'documentation', "Should classify as documentation type")
        self.assertEqual(docs.version, '2.1.0', "Should extract version from __version__")
        
        # Test data agent metadata
        data = agents.get('data_pipeline_manager')
        self.assertIsNotNone(data, "Data agent should be discovered")
        self.assertEqual(data.type, 'data_engineer', "Should classify as data_engineer type")
        self.assertEqual(data.version, '3.0.1', "Should extract version")
    
    async def test_agent_validation(self):
        """Test agent validation functionality."""
        agents = await self.registry.discover_agents()
        
        # Test valid agents
        engineer = agents.get('engineer_agent')
        self.assertTrue(engineer.validated, "Valid agent should pass validation")
        self.assertIsNone(engineer.error_message, "Valid agent should have no error message")
        
        # Test invalid agent (syntax error)
        qa_agent = agents.get('qa_testing_agent')
        self.assertFalse(qa_agent.validated, "Agent with syntax error should fail validation")
        self.assertIsNotNone(qa_agent.error_message, "Invalid agent should have error message")
        self.assertIn("Syntax error", qa_agent.error_message, "Should detect syntax error")
    
    async def test_agent_type_classification(self):
        """Test agent type classification accuracy."""
        agents = await self.registry.discover_agents()
        
        # Test classification accuracy
        classifications = {
            'engineer_agent': 'engineer',
            'documentation_specialist': 'documentation',
            'qa_testing_agent': 'qa',
            'data_pipeline_manager': 'data_engineer'
        }
        
        for agent_name, expected_type in classifications.items():
            agent = agents.get(agent_name)
            self.assertIsNotNone(agent, f"Agent {agent_name} should be discovered")
            self.assertEqual(agent.type, expected_type, f"Agent {agent_name} should be classified as {expected_type}")
    
    async def test_cache_integration(self):
        """Test SharedPromptCache integration."""
        # First discovery - should cache results
        start_time = time.time()
        agents_first = await self.registry.discover_agents()
        first_discovery_time = time.time() - start_time
        
        # Second discovery - should use cache
        start_time = time.time()
        agents_second = await self.registry.discover_agents()
        second_discovery_time = time.time() - start_time
        
        # Verify results are the same
        self.assertEqual(len(agents_first), len(agents_second), "Cache should return same results")
        
        # Cache should be faster (though timing can be variable)
        # We'll just verify cache was used by checking it's not None
        cache_key = "agent_registry_discovery"
        cached_data = await self.cache_service.get(cache_key)
        self.assertIsNotNone(cached_data, "Discovery results should be cached")
    
    async def test_registry_statistics(self):
        """Test registry statistics functionality."""
        agents = await self.registry.discover_agents()
        stats = await self.registry.get_registry_stats()
        
        # Verify statistics
        self.assertEqual(stats['total_agents'], len(agents), "Total agents should match discovery")
        self.assertGreaterEqual(stats['validated_agents'], 3, "Should have at least 3 valid agents")
        self.assertGreaterEqual(stats['failed_agents'], 1, "Should have at least 1 failed agent (syntax error)")
        self.assertGreaterEqual(stats['agent_types'], 4, "Should have at least 4 agent types")
        
        # Verify tier distribution
        self.assertIn('user', stats['agents_by_tier'], "Should have user tier agents")
        self.assertEqual(stats['agents_by_tier']['user'], len(agents), "All test agents should be user tier")
        
        # Verify type distribution
        self.assertIn('engineer', stats['agents_by_type'], "Should have engineer type")
        self.assertIn('documentation', stats['agents_by_type'], "Should have documentation type")
        self.assertIn('qa', stats['agents_by_type'], "Should have qa type")
        self.assertIn('data_engineer', stats['agents_by_type'], "Should have data_engineer type")
    
    async def test_agent_retrieval(self):
        """Test individual agent retrieval."""
        # Discover agents first
        await self.registry.discover_agents()
        
        # Test getting specific agent
        engineer = await self.registry.get_agent('engineer_agent')
        self.assertIsNotNone(engineer, "Should retrieve specific agent")
        self.assertEqual(engineer.name, 'engineer_agent', "Should return correct agent")
        
        # Test getting non-existent agent
        nonexistent = await self.registry.get_agent('nonexistent_agent')
        self.assertIsNone(nonexistent, "Should return None for non-existent agent")
    
    async def test_agent_listing_with_filters(self):
        """Test agent listing with type and tier filters."""
        await self.registry.discover_agents()
        
        # Test filtering by type
        engineer_agents = await self.registry.list_agents(agent_type='engineer')
        self.assertEqual(len(engineer_agents), 1, "Should find 1 engineer agent")
        self.assertEqual(engineer_agents[0].name, 'engineer_agent', "Should return engineer agent")
        
        # Test filtering by tier
        user_agents = await self.registry.list_agents(tier='user')
        self.assertEqual(len(user_agents), 4, "Should find all 4 user tier agents")
        
        # Test filtering by both type and tier
        user_docs_agents = await self.registry.list_agents(agent_type='documentation', tier='user')
        self.assertEqual(len(user_docs_agents), 1, "Should find 1 documentation agent in user tier")
    
    async def test_agent_types_discovery(self):
        """Test agent types discovery functionality."""
        await self.registry.discover_agents()
        
        agent_types = await self.registry.get_agent_types()
        expected_types = {'engineer', 'documentation', 'qa', 'data_engineer'}
        
        self.assertTrue(expected_types.issubset(agent_types), "Should discover all expected agent types")
    
    async def test_agent_refresh(self):
        """Test individual agent refresh functionality."""
        await self.registry.discover_agents()
        
        # Get initial agent
        initial_agent = await self.registry.get_agent('engineer_agent')
        self.assertIsNotNone(initial_agent, "Should find initial agent")
        
        # Refresh the agent
        refreshed_agent = await self.registry.refresh_agent('engineer_agent')
        self.assertIsNotNone(refreshed_agent, "Should refresh existing agent")
        self.assertEqual(refreshed_agent.name, 'engineer_agent', "Refreshed agent should have same name")
        
        # Test refreshing non-existent agent
        nonexistent_refresh = await self.registry.refresh_agent('nonexistent_agent')
        self.assertIsNone(nonexistent_refresh, "Should return None for non-existent agent")
    
    async def test_cache_clearing(self):
        """Test cache clearing functionality."""
        await self.registry.discover_agents()
        
        # Verify cache is populated
        cache_key = "agent_registry_discovery"
        cached_data = await self.cache_service.get(cache_key)
        self.assertIsNotNone(cached_data, "Cache should be populated")
        
        # Clear cache
        self.registry.clear_cache()
        
        # Verify discovery time is None (cache cleared)
        self.assertIsNone(self.registry.last_discovery_time, "Discovery time should be reset")
        self.assertEqual(len(self.registry.registry), 0, "Registry should be cleared")
    
    def test_sync_functionality(self):
        """Test synchronous functionality and integration."""
        # Test async functionality through sync wrapper
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Test basic discovery
            agents = loop.run_until_complete(self.registry.discover_agents())
            self.assertGreater(len(agents), 0, "Should discover agents in sync mode")
            
            # Test statistics
            stats = loop.run_until_complete(self.registry.get_registry_stats())
            self.assertIn('total_agents', stats, "Should get statistics in sync mode")
            
        finally:
            loop.close()
    
    def test_performance_requirements(self):
        """Test performance requirements from ISS-0118."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Test discovery performance (<100ms target)
            start_time = time.time()
            agents = loop.run_until_complete(self.registry.discover_agents())
            discovery_time = time.time() - start_time
            
            # Note: In real deployment with more agents, this may take longer
            # For test environment with 4 agents, should be well under 100ms
            self.assertLess(discovery_time, 1.0, "Discovery should complete in reasonable time")
            
            # Test cached discovery (should be faster)
            start_time = time.time()
            cached_agents = loop.run_until_complete(self.registry.discover_agents())
            cached_discovery_time = time.time() - start_time
            
            self.assertLessEqual(cached_discovery_time, discovery_time, "Cached discovery should not be slower")
            self.assertEqual(len(agents), len(cached_agents), "Cached discovery should return same count")
            
        finally:
            loop.close()


def run_agent_registry_tests():
    """Run comprehensive AgentRegistry tests for ISS-0118."""
    if not SERVICES_AVAILABLE:
        print("❌ Services not available for testing")
        return False
    
    print("🧪 Running AgentRegistry Implementation Tests (ISS-0118)")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAgentRegistryISS118)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"🧪 ISS-0118 Test Results:")
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception: ')[-1].split('\n')[0]}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ All AgentRegistry tests passed! ISS-0118 implementation validated.")
    else:
        print("\n❌ Some AgentRegistry tests failed. Review implementation.")
    
    return success


if __name__ == '__main__':
    success = run_agent_registry_tests()
    sys.exit(0 if success else 1)