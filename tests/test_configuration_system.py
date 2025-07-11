"""
Configuration System Tests

Comprehensive testing for the memory trigger configuration system including:
- Configuration validation and schema enforcement
- Hot reloading and dynamic updates
- Environment-specific configuration handling
- Policy engine configuration
- Performance configuration validation
- Error handling and recovery
"""

import asyncio
import pytest
import tempfile
import os
import yaml
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from claude_pm.config.memory_trigger_config import (
    MemoryTriggerConfig,
    MemoryTriggerConfigManager,
    PerformanceConfig,
    TriggerPolicyConfig,
    LifecyclePolicyConfig,
    MonitoringConfig,
    BackendConfig,
    Environment,
    MemoryTriggerType,
    MemoryBackend,
    ConfigurationFileWatcher,
    get_config_manager,
    initialize_config,
    get_config,
    apply_environment_overrides
)


class TestMemoryTriggerConfig:
    """Test configuration data classes and validation."""
    
    def test_performance_config_defaults(self):
        """Test performance configuration defaults."""
        config = PerformanceConfig()
        
        assert config.create_timeout == 5.0
        assert config.recall_timeout == 3.0
        assert config.batch_size == 50
        assert config.max_concurrent_operations == 10
        assert config.cache_enabled is True
        assert config.background_processing_enabled is True
        assert config.worker_thread_count == 3
    
    def test_performance_config_validation(self):
        """Test performance configuration validation."""
        # Valid configuration
        valid_config = PerformanceConfig(
            create_timeout=5.0,
            recall_timeout=3.0,
            batch_size=50,
            max_concurrent_operations=10
        )
        
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # Invalid configuration
        invalid_config = PerformanceConfig(
            create_timeout=-1.0,  # Invalid: negative
            recall_timeout=0.0,   # Invalid: zero
            batch_size=0,         # Invalid: zero
            max_concurrent_operations=-5,  # Invalid: negative
            min_memory_quality_score=1.5,  # Invalid: > 1.0
            memory_cleanup_threshold=-0.1  # Invalid: negative
        )
        
        errors = invalid_config.validate()
        assert len(errors) == 6  # All invalid fields should be caught
        assert any("create_timeout must be positive" in error for error in errors)
        assert any("recall_timeout must be positive" in error for error in errors)
        assert any("batch_size must be positive" in error for error in errors)
        assert any("max_concurrent_operations must be positive" in error for error in errors)
        assert any("min_memory_quality_score must be between 0 and 1" in error for error in errors)
        assert any("memory_cleanup_threshold must be between 0 and 1" in error for error in errors)
    
    def test_trigger_policy_config_defaults(self):
        """Test trigger policy configuration defaults."""
        config = TriggerPolicyConfig()
        
        assert config.enabled is True
        assert config.trigger_type == MemoryTriggerType.WORKFLOW
        assert config.success_threshold == 0.8
        assert config.create_on_success is True
        assert config.pattern_detection_enabled is True
        assert config.min_context_length == 10
        assert config.max_context_length == 10000
    
    def test_trigger_policy_config_validation(self):
        """Test trigger policy configuration validation."""
        # Valid configuration
        valid_config = TriggerPolicyConfig(
            success_threshold=0.8,
            failure_threshold=0.3,
            pattern_similarity_threshold=0.7,
            min_context_length=10,
            max_context_length=5000,
            min_trigger_confidence=0.6,
            max_triggers_per_minute=60,
            cooldown_period_seconds=30
        )
        
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # Invalid configuration
        invalid_config = TriggerPolicyConfig(
            success_threshold=1.5,  # Invalid: > 1.0
            failure_threshold=-0.1,  # Invalid: negative
            pattern_similarity_threshold=2.0,  # Invalid: > 1.0
            min_context_length=-1,  # Invalid: negative
            max_context_length=5,   # Invalid: <= min_context_length
            min_trigger_confidence=1.2,  # Invalid: > 1.0
            max_triggers_per_minute=0,  # Invalid: zero
            cooldown_period_seconds=-5  # Invalid: negative
        )
        
        errors = invalid_config.validate()
        assert len(errors) == 8  # All invalid fields should be caught
    
    def test_lifecycle_policy_config_validation(self):
        """Test lifecycle policy configuration validation."""
        # Valid configuration
        valid_config = LifecyclePolicyConfig(
            default_retention_days=90,
            cleanup_interval_hours=24,
            min_quality_for_retention=0.4
        )
        
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # Invalid configuration
        invalid_config = LifecyclePolicyConfig(
            default_retention_days=0,  # Invalid: zero
            cleanup_interval_hours=-1,  # Invalid: negative
            min_quality_for_retention=1.5  # Invalid: > 1.0
        )
        
        errors = invalid_config.validate()
        assert len(errors) >= 3
    
    def test_monitoring_config_validation(self):
        """Test monitoring configuration validation."""
        # Valid configuration
        valid_config = MonitoringConfig(
            metrics_collection_interval=60,
            error_rate_threshold=0.05,
            log_level="INFO"
        )
        
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # Invalid configuration
        invalid_config = MonitoringConfig(
            metrics_collection_interval=0,  # Invalid: zero
            error_rate_threshold=1.5,  # Invalid: > 1.0
            log_level="INVALID"  # Invalid: not a valid log level
        )
        
        errors = invalid_config.validate()
        assert len(errors) >= 3
    
    def test_backend_config_validation(self):
        """Test backend configuration validation."""
        # Valid configuration
        valid_config = BackendConfig(
            backend_type=MemoryBackend.MEM0,
            connection_timeout=10.0,
            pool_size=10
        )
        
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # Invalid configuration with encryption
        invalid_config = BackendConfig(
            connection_timeout=-1.0,  # Invalid: negative
            pool_size=0,  # Invalid: zero
            encryption_enabled=True,
            encryption_key_path=None  # Invalid: encryption enabled but no key path
        )
        
        errors = invalid_config.validate()
        assert len(errors) >= 3
    
    def test_main_config_validation(self):
        """Test main configuration validation and cross-validation."""
        # Valid configuration
        valid_config = MemoryTriggerConfig(
            environment=Environment.TESTING,
            performance=PerformanceConfig(max_concurrent_operations=5),
            max_memory_operations_per_second=10
        )
        
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # Invalid configuration with cross-validation error
        invalid_config = MemoryTriggerConfig(
            performance=PerformanceConfig(max_concurrent_operations=20),
            max_memory_operations_per_second=10  # Invalid: less than max_concurrent_operations
        )
        
        errors = invalid_config.validate()
        assert len(errors) >= 1
        assert any("max_concurrent_operations cannot exceed max_memory_operations_per_second" in error for error in errors)
    
    def test_config_serialization(self):
        """Test configuration serialization and deserialization."""
        # Create configuration
        original_config = MemoryTriggerConfig(
            environment=Environment.PRODUCTION,
            performance=PerformanceConfig(
                create_timeout=10.0,
                batch_size=100
            ),
            trigger_policies={
                "test_policy": TriggerPolicyConfig(
                    trigger_type=MemoryTriggerType.AGENT,
                    success_threshold=0.9
                )
            }
        )
        
        # Serialize to dictionary
        config_dict = original_config.to_dict()
        
        # Verify serialization
        assert config_dict["environment"] == Environment.PRODUCTION
        assert config_dict["performance"]["create_timeout"] == 10.0
        assert config_dict["performance"]["batch_size"] == 100
        assert "test_policy" in config_dict["trigger_policies"]
        
        # Deserialize back to configuration
        restored_config = MemoryTriggerConfig.from_dict(config_dict)
        
        # Verify deserialization
        assert restored_config.environment == Environment.PRODUCTION
        assert restored_config.performance.create_timeout == 10.0
        assert restored_config.performance.batch_size == 100
        assert "test_policy" in restored_config.trigger_policies
        assert restored_config.trigger_policies["test_policy"].trigger_type == MemoryTriggerType.AGENT


class TestMemoryTriggerConfigManager:
    """Test configuration manager functionality."""
    
    @pytest.fixture
    def sample_config_data(self):
        """Create sample configuration data."""
        return {
            "environment": "testing",
            "global_enabled": True,
            "debug_mode": False,
            "performance": {
                "create_timeout": 5.0,
                "recall_timeout": 3.0,
                "batch_size": 50,
                "cache_enabled": True
            },
            "backend": {
                "backend_type": "mem0",
                "connection_timeout": 10.0,
                "pool_size": 10
            },
            "trigger_policies": {
                "workflow_completion": {
                    "enabled": True,
                    "trigger_type": "workflow",
                    "success_threshold": 0.8,
                    "create_on_success": True
                },
                "error_resolution": {
                    "enabled": True,
                    "trigger_type": "error",
                    "create_on_error": True,
                    "pattern_detection_enabled": True
                }
            },
            "features": {
                "workflow_triggers": True,
                "agent_triggers": True,
                "pattern_detection": True
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, sample_config_data):
        """Create temporary configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config_data, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except OSError:
            pass
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        # Initialize without file
        manager = MemoryTriggerConfigManager()
        assert manager.config is not None
        assert isinstance(manager.config, MemoryTriggerConfig)
        
        # Initialize with non-existent file
        with pytest.raises(FileNotFoundError):
            MemoryTriggerConfigManager("/non/existent/file.yaml")
    
    def test_load_config_from_file(self, temp_config_file):
        """Test loading configuration from file."""
        manager = MemoryTriggerConfigManager()
        manager.load_config_from_file(temp_config_file)
        
        config = manager.get_config()
        
        # Verify loaded configuration
        assert config.environment == Environment.TESTING
        assert config.global_enabled is True
        assert config.debug_mode is False
        assert config.performance.create_timeout == 5.0
        assert config.performance.batch_size == 50
        assert config.backend.backend_type == MemoryBackend.MEM0
        assert "workflow_completion" in config.trigger_policies
        assert "error_resolution" in config.trigger_policies
        assert config.features["workflow_triggers"] is True
    
    def test_save_config_to_file(self, temp_config_file):
        """Test saving configuration to file."""
        manager = MemoryTriggerConfigManager(temp_config_file)
        
        # Modify configuration
        config = manager.get_config()
        config.debug_mode = True
        config.performance.batch_size = 75
        
        # Save configuration
        manager.save_config_to_file()
        
        # Load from file to verify
        with open(temp_config_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["debug_mode"] is True
        assert saved_data["performance"]["batch_size"] == 75
    
    def test_config_validation_strict_mode(self, sample_config_data):
        """Test configuration validation in strict mode."""
        # Create invalid configuration data
        invalid_data = sample_config_data.copy()
        invalid_data["performance"]["create_timeout"] = -1.0  # Invalid
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_data, f)
            temp_file = f.name
        
        try:
            # Should raise validation error in strict mode
            with pytest.raises(ValueError, match="Configuration validation failed"):
                MemoryTriggerConfigManager(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_config_update(self, temp_config_file):
        """Test configuration updates."""
        manager = MemoryTriggerConfigManager(temp_config_file)
        
        # Get initial batch size
        initial_batch_size = manager.get_config().performance.batch_size
        
        # Update configuration
        updates = {
            "performance": {
                "batch_size": initial_batch_size + 25,
                "create_timeout": 8.0
            },
            "debug_mode": True
        }
        
        manager.update_config(updates)
        
        # Verify updates
        updated_config = manager.get_config()
        assert updated_config.performance.batch_size == initial_batch_size + 25
        assert updated_config.performance.create_timeout == 8.0
        assert updated_config.debug_mode is True
        
        # Verify file was updated
        with open(temp_config_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["performance"]["batch_size"] == initial_batch_size + 25
        assert saved_data["debug_mode"] is True
    
    def test_trigger_policy_management(self, temp_config_file):
        """Test trigger policy management."""
        manager = MemoryTriggerConfigManager(temp_config_file)
        
        # Add new trigger policy
        new_policy = TriggerPolicyConfig(
            trigger_type=MemoryTriggerType.AGENT,
            success_threshold=0.9,
            agent_name="test_agent"
        )
        
        manager.add_trigger_policy("test_agent_policy", new_policy)
        
        # Verify policy was added
        retrieved_policy = manager.get_trigger_policy("test_agent_policy")
        assert retrieved_policy is not None
        assert retrieved_policy.trigger_type == MemoryTriggerType.AGENT
        assert retrieved_policy.success_threshold == 0.9
        assert retrieved_policy.agent_name == "test_agent"
        
        # Remove trigger policy
        removed = manager.remove_trigger_policy("test_agent_policy")
        assert removed is True
        
        # Verify policy was removed
        retrieved_policy = manager.get_trigger_policy("test_agent_policy")
        assert retrieved_policy is None
        
        # Try to remove non-existent policy
        removed = manager.remove_trigger_policy("non_existent_policy")
        assert removed is False
    
    def test_config_validation_reporting(self, temp_config_file):
        """Test configuration validation reporting."""
        manager = MemoryTriggerConfigManager(temp_config_file)
        
        # Valid configuration should have no errors
        errors = manager.validate_config()
        assert len(errors) == 0
        
        # Introduce validation errors
        updates = {
            "performance": {
                "create_timeout": -1.0,  # Invalid
                "batch_size": 0  # Invalid
            },
            "max_memory_operations_per_second": -5  # Invalid
        }
        
        # This should fail validation in strict mode
        with pytest.raises(ValueError):
            manager.update_config(updates)
    
    def test_environment_specific_config_path(self):
        """Test environment-specific configuration file paths."""
        manager = MemoryTriggerConfigManager()
        
        base_path = "/path/to/config.yaml"
        
        # Test different environments
        dev_path = manager.get_environment_config_path(Environment.DEVELOPMENT, base_path)
        assert dev_path == "/path/to/config.development.yaml"
        
        prod_path = manager.get_environment_config_path(Environment.PRODUCTION, base_path)
        assert prod_path == "/path/to/config.production.yaml"
        
        test_path = manager.get_environment_config_path(Environment.TESTING, base_path)
        assert test_path == "/path/to/config.testing.yaml"
    
    def test_config_manager_shutdown(self, temp_config_file):
        """Test configuration manager shutdown."""
        manager = MemoryTriggerConfigManager(temp_config_file)
        
        # Should shutdown without errors
        manager.shutdown()
        
        # Observer should be stopped
        assert manager.observer is None
        assert manager.watcher is None


class TestConfigurationHotReloading:
    """Test configuration hot reloading functionality."""
    
    @pytest.fixture
    def hot_reload_config_file(self):
        """Create configuration file for hot reload testing."""
        config_data = {
            "environment": "testing",
            "auto_reload": True,
            "performance": {
                "batch_size": 50,
                "create_timeout": 5.0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        yield temp_file
        
        try:
            os.unlink(temp_file)
        except OSError:
            pass
    
    def test_hot_reload_detection(self, hot_reload_config_file):
        """Test hot reload file change detection."""
        manager = MemoryTriggerConfigManager(hot_reload_config_file)
        
        # Get initial batch size
        initial_batch_size = manager.get_config().performance.batch_size
        
        # Modify configuration file
        config_data = {
            "environment": "testing",
            "auto_reload": True,
            "performance": {
                "batch_size": initial_batch_size + 25,
                "create_timeout": 5.0
            }
        }
        
        with open(hot_reload_config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Wait for file system event processing
        time.sleep(0.1)
        
        # Manual reload (simulating hot reload trigger)
        manager.reload_config()
        
        # Verify configuration was reloaded
        updated_config = manager.get_config()
        assert updated_config.performance.batch_size == initial_batch_size + 25
        
        manager.shutdown()
    
    @patch('claude_pm.config.memory_trigger_config.Observer')
    def test_hot_reload_setup(self, mock_observer_class, hot_reload_config_file):
        """Test hot reload setup with mocked file watcher."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer
        
        manager = MemoryTriggerConfigManager(hot_reload_config_file)
        
        # Verify observer was set up
        assert manager.observer is not None
        assert manager.watcher is not None
        
        # Verify observer methods were called
        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()
        
        manager.shutdown()
        mock_observer.stop.assert_called_once()
    
    def test_hot_reload_cooldown(self, hot_reload_config_file):
        """Test hot reload cooldown prevents rapid reloads."""
        manager = MemoryTriggerConfigManager(hot_reload_config_file)
        watcher = ConfigurationFileWatcher(manager)
        
        # Mock event
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = hot_reload_config_file
        
        # First modification
        first_time = time.time()
        watcher.last_reload = first_time - 2.0  # 2 seconds ago
        
        with patch.object(manager, 'reload_config') as mock_reload:
            watcher.on_modified(mock_event)
            mock_reload.assert_called_once()
        
        # Rapid second modification (should be ignored due to cooldown)
        watcher.last_reload = time.time() - 0.5  # 0.5 seconds ago (within cooldown)
        
        with patch.object(manager, 'reload_config') as mock_reload:
            watcher.on_modified(mock_event)
            mock_reload.assert_not_called()
        
        manager.shutdown()


class TestEnvironmentVariableOverrides:
    """Test environment variable override functionality."""
    
    def test_performance_overrides(self):
        """Test performance configuration overrides."""
        config = MemoryTriggerConfig()
        
        # Set environment variables
        with patch.dict(os.environ, {
            'MEMORY_CREATE_TIMEOUT': '10.0',
            'MEMORY_RECALL_TIMEOUT': '5.0',
            'MEMORY_BATCH_SIZE': '100',
            'MEMORY_MAX_CONCURRENT': '20'
        }):
            apply_environment_overrides(config)
            
            assert config.performance.create_timeout == 10.0
            assert config.performance.recall_timeout == 5.0
            assert config.performance.batch_size == 100
            assert config.performance.max_concurrent_operations == 20
    
    def test_backend_overrides(self):
        """Test backend configuration overrides."""
        config = MemoryTriggerConfig()
        
        with patch.dict(os.environ, {
            'MEMORY_BACKEND_TYPE': 'local',
            'MEMORY_CONNECTION_TIMEOUT': '15.0'
        }):
            apply_environment_overrides(config)
            
            assert config.backend.backend_type == MemoryBackend.LOCAL
            assert config.backend.connection_timeout == 15.0
    
    def test_feature_toggles_overrides(self):
        """Test feature toggle overrides."""
        config = MemoryTriggerConfig()
        
        with patch.dict(os.environ, {
            'MEMORY_TRIGGERS_ENABLED': 'false',
            'MEMORY_DEBUG_MODE': 'true',
            'MEMORY_ENVIRONMENT': 'production'
        }):
            apply_environment_overrides(config)
            
            assert config.global_enabled is False
            assert config.debug_mode is True
            assert config.environment == Environment.PRODUCTION
    
    def test_invalid_environment_values(self):
        """Test handling of invalid environment variable values."""
        config = MemoryTriggerConfig()
        
        # Invalid backend type should raise ValueError
        with patch.dict(os.environ, {'MEMORY_BACKEND_TYPE': 'invalid_backend'}):
            with pytest.raises(ValueError):
                apply_environment_overrides(config)
        
        # Invalid environment should raise ValueError
        with patch.dict(os.environ, {'MEMORY_ENVIRONMENT': 'invalid_env'}):
            with pytest.raises(ValueError):
                apply_environment_overrides(config)


class TestGlobalConfigurationManagement:
    """Test global configuration management functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset global configuration manager
        import claude_pm.config.memory_trigger_config as config_module
        config_module._config_manager = None
    
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton instance."""
        self.setUp()
        
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, MemoryTriggerConfigManager)
    
    def test_initialize_config_with_file(self):
        """Test initialize_config with configuration file."""
        self.setUp()
        
        config_data = {
            "environment": "testing",
            "performance": {"batch_size": 75}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        try:
            manager = initialize_config(temp_file)
            config = manager.get_config()
            
            assert config.environment == Environment.TESTING
            assert config.performance.batch_size == 75
            
        finally:
            os.unlink(temp_file)
    
    def test_get_config_convenience_function(self):
        """Test get_config convenience function."""
        self.setUp()
        
        config = get_config()
        
        assert isinstance(config, MemoryTriggerConfig)
        assert config.environment == Environment.DEVELOPMENT  # Default


class TestConfigurationErrorHandling:
    """Test configuration error handling and recovery."""
    
    def test_malformed_yaml_handling(self):
        """Test handling of malformed YAML files."""
        malformed_yaml = """
        environment: testing
        performance:
          batch_size: 50
          invalid_yaml: [unclosed list
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(malformed_yaml)
            temp_file = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                MemoryTriggerConfigManager(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_missing_required_fields(self):
        """Test handling of missing required configuration fields."""
        incomplete_config = {
            "environment": "testing"
            # Missing other required fields
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(incomplete_config, f)
            temp_file = f.name
        
        try:
            # Should not raise error - should use defaults
            manager = MemoryTriggerConfigManager(temp_file)
            config = manager.get_config()
            
            # Should have default values
            assert config.performance is not None
            assert config.backend is not None
            
        finally:
            os.unlink(temp_file)
    
    def test_permission_error_handling(self):
        """Test handling of file permission errors."""
        # Create a file we can't write to
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"environment": "testing"}, f)
            temp_file = f.name
        
        try:
            # Make file read-only
            os.chmod(temp_file, 0o444)
            
            manager = MemoryTriggerConfigManager(temp_file)
            
            # Trying to save should raise permission error
            with pytest.raises(PermissionError):
                manager.save_config_to_file()
                
        finally:
            # Restore permissions and cleanup
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)
    
    def test_concurrent_config_access(self):
        """Test concurrent configuration access."""
        config_data = {
            "environment": "testing",
            "performance": {"batch_size": 50}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        try:
            manager = MemoryTriggerConfigManager(temp_file)
            
            def update_config(batch_size):
                updates = {"performance": {"batch_size": batch_size}}
                manager.update_config(updates)
            
            def read_config():
                return manager.get_config().performance.batch_size
            
            # Start concurrent threads
            threads = []
            for i in range(10):
                if i % 2 == 0:
                    thread = threading.Thread(target=update_config, args=(50 + i,))
                else:
                    thread = threading.Thread(target=read_config)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Should not crash and should have valid configuration
            final_config = manager.get_config()
            assert isinstance(final_config.performance.batch_size, int)
            assert final_config.performance.batch_size >= 50
            
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    # Run configuration tests
    pytest.main([__file__, "-v"])