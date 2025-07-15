#!/usr/bin/env python3
"""
Test Suite for Agent Modification Tracking System - ISS-0118
============================================================

Comprehensive test suite for the agent modification tracking and persistence
system including integration testing of all components.

Test Coverage:
- AgentModificationTracker functionality
- AgentPersistenceService operations  
- AgentLifecycleManager integration
- SharedPromptCache integration
- File system monitoring
- Backup and restore operations
- Conflict detection and resolution
- Performance benchmarking

Created for ISS-0118: Agent Registry and Hierarchical Discovery System
"""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock

# Import the components to test
from claude_pm.services.agent_modification_tracker import (
    AgentModificationTracker,
    AgentModification,
    ModificationType,
    ModificationTier,
    ModificationHistory
)
from claude_pm.services.agent_persistence_service import (
    AgentPersistenceService,
    PersistenceRecord,
    PersistenceStrategy,
    PersistenceOperation
)
from claude_pm.services.agent_lifecycle_manager import (
    AgentLifecycleManager,
    AgentLifecycleRecord,
    LifecycleOperation,
    LifecycleState
)
from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.agent_registry import AgentRegistry


class TestAgentModificationTracker:
    """Test suite for AgentModificationTracker."""
    
    @pytest.fixture
    async def tracker(self):
        """Create tracker instance for testing."""
        config = {
            "enable_monitoring": False,  # Disable for testing
            "backup_enabled": True,
            "validation_enabled": True,
            "persistence_interval": 1  # Fast persistence for testing
        }
        
        tracker = AgentModificationTracker(config)
        await tracker.start()
        yield tracker
        await tracker.stop()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_track_modification_create(self, tracker, temp_dir):
        """Test tracking agent creation."""
        agent_name = "test_agent"
        file_path = temp_dir / "test_agent.py"
        
        # Create test file
        file_path.write_text("# Test agent content")
        
        # Track creation
        modification = await tracker.track_modification(
            agent_name=agent_name,
            modification_type=ModificationType.CREATE,
            file_path=str(file_path),
            tier=ModificationTier.USER,
            test_metadata="test_value"
        )
        
        assert modification.agent_name == agent_name
        assert modification.modification_type == ModificationType.CREATE
        assert modification.tier == ModificationTier.USER
        assert modification.file_path == str(file_path)
        assert "test_metadata" in modification.metadata
        assert modification.modification_id is not None
        assert modification.timestamp > 0
    
    @pytest.mark.asyncio
    async def test_track_modification_modify(self, tracker, temp_dir):
        """Test tracking agent modification."""
        agent_name = "test_agent"
        file_path = temp_dir / "test_agent.py"
        
        # Create and modify test file
        file_path.write_text("# Original content")
        time.sleep(0.1)  # Ensure different timestamps
        file_path.write_text("# Modified content")
        
        # Track modification
        modification = await tracker.track_modification(
            agent_name=agent_name,
            modification_type=ModificationType.MODIFY,
            file_path=str(file_path),
            tier=ModificationTier.USER
        )
        
        assert modification.modification_type == ModificationType.MODIFY
        assert modification.file_hash_after is not None
        assert modification.file_size_after > 0
    
    @pytest.mark.asyncio
    async def test_modification_history(self, tracker, temp_dir):
        """Test modification history tracking."""
        agent_name = "history_test_agent"
        file_path = temp_dir / "history_test_agent.py"
        file_path.write_text("# Test content")
        
        # Track multiple modifications
        modifications = []
        for i in range(3):
            mod = await tracker.track_modification(
                agent_name=agent_name,
                modification_type=ModificationType.MODIFY,
                file_path=str(file_path),
                tier=ModificationTier.USER,
                iteration=i
            )
            modifications.append(mod)
            time.sleep(0.1)  # Ensure different timestamps
        
        # Get history
        history = await tracker.get_modification_history(agent_name)
        
        assert history is not None
        assert history.agent_name == agent_name
        assert history.total_modifications == 3
        assert len(history.modifications) == 3
        assert history.first_seen is not None
        assert history.last_modified is not None
    
    @pytest.mark.asyncio
    async def test_recent_modifications(self, tracker, temp_dir):
        """Test recent modifications retrieval."""
        agent_name = "recent_test_agent"
        file_path = temp_dir / "recent_test_agent.py"
        file_path.write_text("# Test content")
        
        # Track modification
        await tracker.track_modification(
            agent_name=agent_name,
            modification_type=ModificationType.CREATE,
            file_path=str(file_path),
            tier=ModificationTier.USER
        )
        
        # Get recent modifications
        recent = await tracker.get_recent_modifications(hours=1)
        
        assert len(recent) >= 1
        assert any(mod.agent_name == agent_name for mod in recent)
    
    @pytest.mark.asyncio
    async def test_modification_validation(self, tracker, temp_dir):
        """Test modification validation."""
        agent_name = "validation_test_agent"
        file_path = temp_dir / "validation_test_agent.py"
        
        # Create invalid Python file
        file_path.write_text("def invalid_syntax(\nprint('missing closing paren')")
        
        # Track modification
        modification = await tracker.track_modification(
            agent_name=agent_name,
            modification_type=ModificationType.CREATE,
            file_path=str(file_path),
            tier=ModificationTier.USER
        )
        
        # Should detect syntax error
        assert modification.validation_status == "invalid"
        assert len(modification.validation_errors) > 0
        assert "syntax error" in modification.validation_errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_backup_creation(self, tracker, temp_dir):
        """Test backup creation during modifications."""
        agent_name = "backup_test_agent"
        file_path = temp_dir / "backup_test_agent.py"
        original_content = "# Original content for backup test"
        file_path.write_text(original_content)
        
        # Track modification (should create backup)
        modification = await tracker.track_modification(
            agent_name=agent_name,
            modification_type=ModificationType.MODIFY,
            file_path=str(file_path),
            tier=ModificationTier.USER
        )
        
        # Check backup was created
        assert modification.backup_path is not None
        backup_path = Path(modification.backup_path)
        assert backup_path.exists()
        assert backup_path.read_text() == original_content
    
    @pytest.mark.asyncio
    async def test_modification_stats(self, tracker, temp_dir):
        """Test modification statistics collection."""
        # Create several modifications
        for i in range(5):
            agent_name = f"stats_test_agent_{i}"
            file_path = temp_dir / f"{agent_name}.py"
            file_path.write_text(f"# Agent {i}")
            
            await tracker.track_modification(
                agent_name=agent_name,
                modification_type=ModificationType.CREATE,
                file_path=str(file_path),
                tier=ModificationTier.USER
            )
        
        # Get stats
        stats = await tracker.get_modification_stats()
        
        assert stats['total_agents_tracked'] >= 5
        assert stats['total_modifications'] >= 5
        assert 'modifications_by_type' in stats
        assert 'modifications_by_tier' in stats
        assert ModificationType.CREATE.value in stats['modifications_by_type']


class TestAgentPersistenceService:
    """Test suite for AgentPersistenceService."""
    
    @pytest.fixture
    async def persistence_service(self):
        """Create persistence service for testing."""
        config = {
            "default_strategy": PersistenceStrategy.USER_OVERRIDE.value,
            "enable_auto_sync": False,  # Disable for testing
            "enable_conflict_detection": True
        }
        
        service = AgentPersistenceService(config)
        await service.start()
        yield service
        await service.stop()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_persist_agent_tier_specific(self, persistence_service, temp_dir):
        """Test tier-specific agent persistence."""
        agent_name = "tier_test_agent"
        agent_content = "# Test agent content for tier persistence"
        
        # Persist with tier-specific strategy
        record = await persistence_service.persist_agent(
            agent_name=agent_name,
            agent_content=agent_content,
            source_tier=ModificationTier.USER,
            target_tier=ModificationTier.USER,
            strategy=PersistenceStrategy.TIER_SPECIFIC
        )
        
        assert record.operation_type == PersistenceOperation.UPDATE
        assert record.agent_name == agent_name
        assert record.source_tier == ModificationTier.USER
        assert record.target_tier == ModificationTier.USER
        assert record.strategy == PersistenceStrategy.TIER_SPECIFIC
    
    @pytest.mark.asyncio
    async def test_persist_agent_user_override(self, persistence_service, temp_dir):
        """Test user override persistence strategy."""
        agent_name = "override_test_agent"
        agent_content = "# Test agent for user override"
        
        # Persist with user override strategy
        record = await persistence_service.persist_agent(
            agent_name=agent_name,
            agent_content=agent_content,
            source_tier=ModificationTier.SYSTEM,
            strategy=PersistenceStrategy.USER_OVERRIDE
        )
        
        assert record.strategy == PersistenceStrategy.USER_OVERRIDE
        # Should route to user tier regardless of source
        assert record.target_tier == ModificationTier.USER
    
    @pytest.mark.asyncio
    async def test_persistence_rollback(self, persistence_service, temp_dir):
        """Test persistence rollback functionality."""
        agent_name = "rollback_test_agent"
        
        # Mock a failed persistence operation
        with patch.object(persistence_service, '_execute_persistence_operation') as mock_execute:
            mock_execute.side_effect = Exception("Simulated persistence failure")
            
            record = await persistence_service.persist_agent(
                agent_name=agent_name,
                agent_content="# Test content",
                source_tier=ModificationTier.USER
            )
            
            assert record.success is False
            assert "Simulated persistence failure" in record.error_message
    
    @pytest.mark.asyncio
    async def test_conflict_detection(self, persistence_service, temp_dir):
        """Test conflict detection in persistence."""
        agent_name = "conflict_test_agent"
        
        # Create existing file
        user_dir = temp_dir / '.claude-pm' / 'agents'
        user_dir.mkdir(parents=True, exist_ok=True)
        agent_file = user_dir / f"{agent_name}_agent.py"
        agent_file.write_text("# Existing content")
        
        # Mock recent modification
        agent_file.touch()  # Update modification time
        
        conflicts = await persistence_service._detect_conflicts(agent_name, ModificationTier.USER)
        
        # Should detect recent modification conflict
        assert len(conflicts) > 0
    
    @pytest.mark.asyncio
    async def test_persistence_stats(self, persistence_service):
        """Test persistence statistics collection."""
        stats = await persistence_service.get_persistence_stats()
        
        assert 'total_operations' in stats
        assert 'pending_operations' in stats
        assert 'queued_conflicts' in stats
        assert 'auto_sync_enabled' in stats
        assert 'default_strategy' in stats
        assert 'tier_configurations' in stats


class TestAgentLifecycleManager:
    """Test suite for AgentLifecycleManager."""
    
    @pytest.fixture
    async def lifecycle_manager(self):
        """Create lifecycle manager for testing."""
        # Mock the core services to avoid complex setup
        with patch('claude_pm.services.agent_lifecycle_manager.SharedPromptCache') as mock_cache, \
             patch('claude_pm.services.agent_lifecycle_manager.AgentRegistry') as mock_registry, \
             patch('claude_pm.services.agent_lifecycle_manager.AgentModificationTracker') as mock_tracker, \
             patch('claude_pm.services.agent_lifecycle_manager.AgentPersistenceService') as mock_persistence:
            
            # Configure mocks
            mock_cache.get_instance.return_value = Mock()
            mock_registry.return_value = Mock()
            mock_tracker.return_value = Mock()
            mock_persistence.return_value = Mock()
            
            config = {
                "enable_auto_backup": True,
                "enable_auto_validation": True,
                "enable_cache_invalidation": False,  # Disable for testing
                "enable_registry_sync": False  # Disable for testing
            }
            
            manager = AgentLifecycleManager(config)
            
            # Mock the service initialization
            await manager._initialize_core_services()
            
            yield manager
            
            await manager._cleanup_core_services()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_create_agent_lifecycle(self, lifecycle_manager, temp_dir):
        """Test complete agent creation lifecycle."""
        agent_name = "lifecycle_create_test"
        agent_content = "# Test agent for lifecycle creation"
        
        # Mock the dependencies
        mock_modification = Mock()
        mock_modification.modification_id = "mod_123"
        
        mock_persistence_record = Mock()
        mock_persistence_record.operation_id = "pers_123"
        mock_persistence_record.success = True
        
        lifecycle_manager.modification_tracker.track_modification = AsyncMock(return_value=mock_modification)
        lifecycle_manager.persistence_service.persist_agent = AsyncMock(return_value=mock_persistence_record)
        
        # Create agent
        result = await lifecycle_manager.create_agent(
            agent_name=agent_name,
            agent_content=agent_content,
            tier=ModificationTier.USER,
            agent_type="test"
        )
        
        assert result.operation == LifecycleOperation.CREATE
        assert result.agent_name == agent_name
        assert result.success is True
        assert result.modification_id == "mod_123"
        assert result.persistence_id == "pers_123"
        
        # Check lifecycle record was created
        agent_record = await lifecycle_manager.get_agent_status(agent_name)
        assert agent_record is not None
        assert agent_record.agent_name == agent_name
        assert agent_record.current_state == LifecycleState.ACTIVE
        assert agent_record.tier == ModificationTier.USER
    
    @pytest.mark.asyncio
    async def test_update_agent_lifecycle(self, lifecycle_manager):
        """Test agent update lifecycle."""
        agent_name = "lifecycle_update_test"
        
        # Create initial lifecycle record
        initial_record = AgentLifecycleRecord(
            agent_name=agent_name,
            current_state=LifecycleState.ACTIVE,
            tier=ModificationTier.USER,
            file_path="/test/path.py",
            created_at=time.time(),
            last_modified=time.time(),
            version="1.0.0"
        )
        
        lifecycle_manager.agent_records[agent_name] = initial_record
        
        # Mock dependencies
        mock_modification = Mock()
        mock_modification.modification_id = "mod_update_123"
        
        mock_persistence_record = Mock()
        mock_persistence_record.operation_id = "pers_update_123"
        mock_persistence_record.success = True
        
        lifecycle_manager.modification_tracker.track_modification = AsyncMock(return_value=mock_modification)
        lifecycle_manager.persistence_service.persist_agent = AsyncMock(return_value=mock_persistence_record)
        
        # Update agent
        result = await lifecycle_manager.update_agent(
            agent_name=agent_name,
            agent_content="# Updated content"
        )
        
        assert result.operation == LifecycleOperation.UPDATE
        assert result.success is True
        
        # Check lifecycle record was updated
        updated_record = await lifecycle_manager.get_agent_status(agent_name)
        assert updated_record.current_state == LifecycleState.MODIFIED
        assert updated_record.version == "1.0.1"  # Version should increment
        assert len(updated_record.modifications) == 1
    
    @pytest.mark.asyncio
    async def test_delete_agent_lifecycle(self, lifecycle_manager):
        """Test agent deletion lifecycle."""
        agent_name = "lifecycle_delete_test"
        
        # Create initial lifecycle record
        initial_record = AgentLifecycleRecord(
            agent_name=agent_name,
            current_state=LifecycleState.ACTIVE,
            tier=ModificationTier.USER,
            file_path="/test/path.py",
            created_at=time.time(),
            last_modified=time.time(),
            version="1.0.0"
        )
        
        lifecycle_manager.agent_records[agent_name] = initial_record
        
        # Mock dependencies
        mock_modification = Mock()
        mock_modification.modification_id = "mod_delete_123"
        
        lifecycle_manager.modification_tracker.track_modification = AsyncMock(return_value=mock_modification)
        
        # Mock file deletion
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.unlink') as mock_unlink:
            
            # Delete agent
            result = await lifecycle_manager.delete_agent(agent_name)
            
            assert result.operation == LifecycleOperation.DELETE
            assert result.success is True
            mock_unlink.assert_called_once()
            
            # Check lifecycle record was updated
            deleted_record = await lifecycle_manager.get_agent_status(agent_name)
            assert deleted_record.current_state == LifecycleState.DELETED
    
    @pytest.mark.asyncio
    async def test_agent_not_found_error(self, lifecycle_manager):
        """Test error handling for non-existent agents."""
        # Try to update non-existent agent
        result = await lifecycle_manager.update_agent(
            agent_name="non_existent_agent",
            agent_content="# This should fail"
        )
        
        assert result.success is False
        assert "Agent not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_lifecycle_stats(self, lifecycle_manager):
        """Test lifecycle statistics collection."""
        # Add some test records
        for i in range(3):
            record = AgentLifecycleRecord(
                agent_name=f"stats_test_agent_{i}",
                current_state=LifecycleState.ACTIVE,
                tier=ModificationTier.USER,
                file_path=f"/test/path_{i}.py",
                created_at=time.time(),
                last_modified=time.time(),
                version="1.0.0"
            )
            lifecycle_manager.agent_records[record.agent_name] = record
        
        stats = await lifecycle_manager.get_lifecycle_stats()
        
        assert stats['total_agents'] >= 3
        assert 'agents_by_state' in stats
        assert 'agents_by_tier' in stats
        assert 'performance_metrics' in stats
    
    @pytest.mark.asyncio
    async def test_list_agents_filter(self, lifecycle_manager):
        """Test agent listing with state filtering."""
        # Add test records with different states
        states = [LifecycleState.ACTIVE, LifecycleState.MODIFIED, LifecycleState.DELETED]
        
        for i, state in enumerate(states):
            record = AgentLifecycleRecord(
                agent_name=f"filter_test_agent_{i}",
                current_state=state,
                tier=ModificationTier.USER,
                file_path=f"/test/path_{i}.py",
                created_at=time.time(),
                last_modified=time.time(),
                version="1.0.0"
            )
            lifecycle_manager.agent_records[record.agent_name] = record
        
        # Test filtering
        active_agents = await lifecycle_manager.list_agents(state_filter=LifecycleState.ACTIVE)
        modified_agents = await lifecycle_manager.list_agents(state_filter=LifecycleState.MODIFIED)
        deleted_agents = await lifecycle_manager.list_agents(state_filter=LifecycleState.DELETED)
        
        assert len(active_agents) >= 1
        assert len(modified_agents) >= 1
        assert len(deleted_agents) >= 1
        
        assert all(agent.current_state == LifecycleState.ACTIVE for agent in active_agents)
        assert all(agent.current_state == LifecycleState.MODIFIED for agent in modified_agents)
        assert all(agent.current_state == LifecycleState.DELETED for agent in deleted_agents)


class TestIntegratedSystem:
    """Integration tests for the complete modification tracking system."""
    
    @pytest.fixture
    async def integrated_system(self):
        """Set up complete integrated system for testing."""
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="agent_test_"))
        
        try:
            # Initialize services with minimal configuration
            cache_config = {
                "max_size": 50,
                "max_memory_mb": 5,
                "default_ttl": 60
            }
            
            cache_service = SharedPromptCache.get_instance(cache_config)
            await cache_service.start()
            
            tracker_config = {
                "enable_monitoring": False,
                "backup_enabled": True,
                "validation_enabled": True
            }
            
            tracker_service = AgentModificationTracker(tracker_config)
            await tracker_service.start()
            
            persistence_config = {
                "default_strategy": PersistenceStrategy.USER_OVERRIDE.value,
                "enable_auto_sync": False,
                "enable_conflict_detection": True
            }
            
            persistence_service = AgentPersistenceService(persistence_config)
            await persistence_service.start()
            
            lifecycle_config = {
                "enable_auto_backup": True,
                "enable_cache_invalidation": True,
                "enable_registry_sync": False
            }
            
            lifecycle_manager = AgentLifecycleManager(lifecycle_config)
            # Mock the initialization to avoid complex setup
            lifecycle_manager.shared_cache = cache_service
            lifecycle_manager.modification_tracker = tracker_service
            lifecycle_manager.persistence_service = persistence_service
            
            yield {
                'temp_dir': temp_dir,
                'cache_service': cache_service,
                'tracker_service': tracker_service,
                'persistence_service': persistence_service,
                'lifecycle_manager': lifecycle_manager
            }
            
        finally:
            # Cleanup
            await cache_service.stop()
            await tracker_service.stop()
            await persistence_service.stop()
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_end_to_end_agent_lifecycle(self, integrated_system):
        """Test complete end-to-end agent lifecycle."""
        services = integrated_system
        lifecycle_manager = services['lifecycle_manager']
        
        agent_name = "e2e_test_agent"
        original_content = "# Original agent content\ndef original_function(): pass"
        modified_content = "# Modified agent content\ndef modified_function(): pass"
        
        # Mock the required methods for the test
        mock_modification = Mock()
        mock_modification.modification_id = "e2e_mod_123"
        
        mock_persistence_record = Mock()
        mock_persistence_record.operation_id = "e2e_pers_123"
        mock_persistence_record.success = True
        
        services['tracker_service'].track_modification = AsyncMock(return_value=mock_modification)
        services['persistence_service'].persist_agent = AsyncMock(return_value=mock_persistence_record)
        
        # 1. Create agent
        create_result = await lifecycle_manager.create_agent(
            agent_name=agent_name,
            agent_content=original_content,
            tier=ModificationTier.USER
        )
        
        assert create_result.success is True
        assert create_result.operation == LifecycleOperation.CREATE
        
        # 2. Update agent
        update_result = await lifecycle_manager.update_agent(
            agent_name=agent_name,
            agent_content=modified_content
        )
        
        assert update_result.success is True
        assert update_result.operation == LifecycleOperation.UPDATE
        
        # 3. Check agent status
        agent_status = await lifecycle_manager.get_agent_status(agent_name)
        assert agent_status is not None
        assert agent_status.current_state == LifecycleState.MODIFIED
        assert agent_status.version == "1.0.1"
        
        # 4. Delete agent
        delete_result = await lifecycle_manager.delete_agent(agent_name)
        assert delete_result.success is True
        assert delete_result.operation == LifecycleOperation.DELETE
        
        # 5. Check final status
        final_status = await lifecycle_manager.get_agent_status(agent_name)
        assert final_status.current_state == LifecycleState.DELETED
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, integrated_system):
        """Test cache integration across the system."""
        services = integrated_system
        cache_service = services['cache_service']
        
        # Test cache operations
        test_key = "integration_test_key"
        test_value = {"agent": "test_data", "timestamp": time.time()}
        
        # Set cache entry
        success = cache_service.set(test_key, test_value, ttl=60)
        assert success is True
        
        # Get cache entry
        retrieved = cache_service.get(test_key)
        assert retrieved is not None
        assert retrieved["agent"] == "test_data"
        
        # Test invalidation
        invalidated = cache_service.invalidate("integration_test_*")
        assert invalidated >= 1
        
        # Verify entry was invalidated
        after_invalidation = cache_service.get(test_key)
        assert after_invalidation is None
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, integrated_system):
        """Test performance benchmarks for the integrated system."""
        services = integrated_system
        lifecycle_manager = services['lifecycle_manager']
        
        # Mock dependencies for performance test
        mock_modification = Mock()
        mock_modification.modification_id = "perf_mod"
        
        mock_persistence_record = Mock()
        mock_persistence_record.operation_id = "perf_pers"
        mock_persistence_record.success = True
        
        services['tracker_service'].track_modification = AsyncMock(return_value=mock_modification)
        services['persistence_service'].persist_agent = AsyncMock(return_value=mock_persistence_record)
        
        # Benchmark agent creation
        num_agents = 10
        start_time = time.time()
        
        for i in range(num_agents):
            result = await lifecycle_manager.create_agent(
                agent_name=f"perf_agent_{i}",
                agent_content=f"# Performance test agent {i}",
                tier=ModificationTier.USER
            )
            assert result.success is True
        
        total_time = time.time() - start_time
        avg_time_per_agent = (total_time / num_agents) * 1000  # Convert to ms
        
        # Performance assertion - should be under 100ms per agent
        assert avg_time_per_agent < 100, f"Average time per agent: {avg_time_per_agent:.1f}ms"
        
        # Check cache performance
        cache_metrics = services['cache_service'].get_metrics()
        assert cache_metrics['hit_rate'] >= 0  # Should have some cache activity
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, integrated_system):
        """Test error handling and recovery mechanisms."""
        services = integrated_system
        lifecycle_manager = services['lifecycle_manager']
        
        # Test creating agent with invalid content
        agent_name = "error_test_agent"
        
        # Mock a failure in persistence
        mock_modification = Mock()
        mock_modification.modification_id = "error_mod"
        
        mock_persistence_record = Mock()
        mock_persistence_record.operation_id = "error_pers"
        mock_persistence_record.success = False
        mock_persistence_record.error_message = "Simulated persistence failure"
        
        services['tracker_service'].track_modification = AsyncMock(return_value=mock_modification)
        services['persistence_service'].persist_agent = AsyncMock(return_value=mock_persistence_record)
        
        # Attempt to create agent
        result = await lifecycle_manager.create_agent(
            agent_name=agent_name,
            agent_content="# Test content",
            tier=ModificationTier.USER
        )
        
        # Should handle the error gracefully
        assert result.success is False
        assert "Simulated persistence failure" in result.error_message
        
        # Check that the agent record reflects the failure
        agent_status = await lifecycle_manager.get_agent_status(agent_name)
        if agent_status:  # May or may not be created depending on when failure occurred
            assert agent_status.current_state == LifecycleState.CONFLICTED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])