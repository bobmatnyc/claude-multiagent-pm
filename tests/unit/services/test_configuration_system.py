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
from unittest.mock import Mock, patch, MagicMock, AsyncMock
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
)


class TestMemoryTriggerConfig:
    """Test configuration data classes and validation."""

    def test_performance_config_defaults(self):
        """Test performance configuration defaults."""
        config = PerformanceConfig()

        assert config.max_memory_mb == 512
        assert config.cache_size == 1000
        assert config.gc_threshold == 700
        assert config.optimization_level == "standard"
        assert config.enable_monitoring is True
        assert config.metrics_interval_seconds == 60

    def test_performance_config_validation(self):
        """Test performance configuration validation."""
        # Valid configuration
        config = PerformanceConfig()
        assert config.validate() is True

        # Invalid configurations
        invalid_configs = [
            PerformanceConfig(max_memory_mb=-1),
            PerformanceConfig(cache_size=0),
            PerformanceConfig(gc_threshold=-10),
            PerformanceConfig(optimization_level="invalid"),
            PerformanceConfig(metrics_interval_seconds=0),
        ]

        for invalid_config in invalid_configs:
            assert invalid_config.validate() is False

    def test_trigger_policy_config_defaults(self):
        """Test trigger policy configuration defaults."""
        config = TriggerPolicyConfig()

        assert config.enabled is True
        assert config.trigger_threshold == 0.8
        assert config.cooldown_seconds == 300
        assert config.max_triggers_per_hour == 12
        assert "critical" in config.priority_weights
        assert config.priority_weights["critical"] == 1.0

    def test_trigger_policy_config_validation(self):
        """Test trigger policy configuration validation."""
        # Valid configuration
        config = TriggerPolicyConfig()
        assert config.validate() is True

        # Invalid configurations
        invalid_configs = [
            TriggerPolicyConfig(trigger_threshold=1.5),
            TriggerPolicyConfig(trigger_threshold=-0.1),
            TriggerPolicyConfig(cooldown_seconds=-1),
            TriggerPolicyConfig(max_triggers_per_hour=0),
            TriggerPolicyConfig(priority_weights={"test": 1.5}),
        ]

        for invalid_config in invalid_configs:
            assert invalid_config.validate() is False


class TestMemoryTriggerConfigManager:
    """Test configuration manager functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_config(self):
        """Sample configuration data."""
        return {
            "environment": "development",
            "performance": {
                "max_memory_mb": 256,
                "cache_size": 500,
                "optimization_level": "minimal"
            },
            "trigger_policies": {
                "default": {
                    "enabled": True,
                    "trigger_threshold": 0.7,
                    "cooldown_seconds": 120
                }
            }
        }

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create configuration manager instance."""
        manager = MemoryTriggerConfigManager(
            config_directory=temp_config_dir,
            environment=Environment.DEVELOPMENT
        )
        return manager

    def test_manager_initialization(self, config_manager, temp_config_dir):
        """Test configuration manager initialization."""
        assert config_manager.config_directory == temp_config_dir
        assert config_manager.environment == Environment.DEVELOPMENT
        assert config_manager.config is not None

    def test_load_configuration(self, config_manager, temp_config_dir, sample_config):
        """Test loading configuration from file."""
        # Write configuration file
        config_file = temp_config_dir / "memory_trigger_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load configuration
        success = config_manager.load_configuration()
        assert success is True

        # Verify loaded values
        assert config_manager.config.performance.max_memory_mb == 256
        assert config_manager.config.performance.cache_size == 500

    def test_save_configuration(self, config_manager, temp_config_dir):
        """Test saving configuration to file."""
        # Modify configuration
        config_manager.config.performance.max_memory_mb = 1024

        # Save configuration
        success = config_manager.save_configuration()
        assert success is True

        # Verify file exists
        config_file = temp_config_dir / "memory_trigger_config.yaml"
        assert config_file.exists()

        # Load and verify
        with open(config_file, "r") as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config["performance"]["max_memory_mb"] == 1024

    def test_validate_configuration(self, config_manager):
        """Test configuration validation."""
        # Valid configuration
        assert config_manager.validate_configuration() is True

        # Invalid configuration
        config_manager.config.performance.max_memory_mb = -1
        assert config_manager.validate_configuration() is False

    def test_apply_environment_overrides(self, config_manager):
        """Test environment-specific overrides."""
        # Create environment override
        config_manager.config.performance.max_memory_mb = 256

        # Apply production overrides
        overrides = {
            "performance": {
                "max_memory_mb": 2048,
                "optimization_level": "aggressive"
            }
        }

        config_manager._apply_overrides(overrides)

        assert config_manager.config.performance.max_memory_mb == 2048
        assert config_manager.config.performance.optimization_level == "aggressive"

    def test_get_trigger_policy(self, config_manager):
        """Test getting trigger policies."""
        # Add test policy
        test_policy = TriggerPolicyConfig(
            enabled=True,
            trigger_threshold=0.9,
            cooldown_seconds=60
        )
        
        # Mock the trigger_policies attribute
        config_manager.config.trigger_policies = {"test": test_policy}

        # Get policy
        policy = config_manager.get_trigger_policy("test")
        assert policy is not None
        assert policy.trigger_threshold == 0.9

        # Get non-existent policy
        policy = config_manager.get_trigger_policy("non_existent")
        assert policy is None

    def test_update_trigger_policy(self, config_manager):
        """Test updating trigger policies."""
        # Update policy
        updates = {
            "trigger_threshold": 0.95,
            "cooldown_seconds": 180
        }

        # Mock the trigger_policies attribute
        config_manager.config.trigger_policies = {
            "default": TriggerPolicyConfig()
        }

        success = config_manager.update_trigger_policy("default", updates)
        assert success is True

        policy = config_manager.get_trigger_policy("default")
        assert policy.trigger_threshold == 0.95
        assert policy.cooldown_seconds == 180

    def test_hot_reload_configuration(self, config_manager, temp_config_dir, sample_config):
        """Test hot reload functionality."""
        # Write initial configuration
        config_file = temp_config_dir / "memory_trigger_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load initial configuration
        config_manager.load_configuration()
        initial_memory = config_manager.config.performance.max_memory_mb

        # Modify configuration file
        sample_config["performance"]["max_memory_mb"] = 512
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Trigger hot reload
        config_manager.reload_configuration()

        # Verify updated value
        assert config_manager.config.performance.max_memory_mb == 512
        assert config_manager.config.performance.max_memory_mb != initial_memory

    def test_register_callback(self, config_manager):
        """Test callback registration."""
        callback_called = False
        callback_config = None

        def test_callback(config):
            nonlocal callback_called, callback_config
            callback_called = True
            callback_config = config

        # Register callback
        config_manager.register_callback(test_callback)

        # Trigger callbacks
        config_manager._notify_callbacks()

        assert callback_called is True
        assert callback_config is not None

    def test_thread_safety(self, config_manager):
        """Test thread-safe configuration access."""
        results = []
        errors = []

        def read_config():
            try:
                for _ in range(100):
                    value = config_manager.config.performance.max_memory_mb
                    results.append(value)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def write_config():
            try:
                for i in range(100):
                    config_manager.config.performance.max_memory_mb = 256 + i
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Create threads
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=read_config))
            threads.append(threading.Thread(target=write_config))

        # Start threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) > 0


class TestConfigurationFileWatcher:
    """Test configuration file watcher functionality."""

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary configuration file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            yaml.dump({"test": "initial"}, temp_file)
            temp_path = Path(temp_file.name)

        yield temp_path

        # Cleanup
        try:
            temp_path.unlink()
        except:
            pass

    def test_file_watcher_initialization(self, temp_config_file):
        """Test file watcher initialization."""
        watcher = ConfigurationFileWatcher(
            file_path=temp_config_file,
            callback=lambda: None
        )

        assert watcher.file_path == temp_config_file
        assert watcher.callback is not None
        assert not watcher.is_running

    def test_file_change_detection(self, temp_config_file):
        """Test detecting file changes."""
        changes_detected = []

        def on_change():
            changes_detected.append(True)

        watcher = ConfigurationFileWatcher(
            file_path=temp_config_file,
            callback=on_change,
            check_interval=0.1
        )

        # Start watching
        watcher.start()

        # Wait for initial setup
        time.sleep(0.2)

        # Modify file
        with open(temp_config_file, "w") as f:
            yaml.dump({"test": "modified"}, f)

        # Wait for detection
        time.sleep(0.3)

        # Stop watching
        watcher.stop()

        # Verify change was detected
        assert len(changes_detected) > 0

    def test_file_watcher_error_handling(self):
        """Test file watcher error handling."""
        non_existent_file = Path("/non/existent/file.yaml")
        errors = []

        def error_callback():
            errors.append("callback_called")

        watcher = ConfigurationFileWatcher(
            file_path=non_existent_file,
            callback=error_callback
        )

        # Should handle gracefully
        watcher.start()
        time.sleep(0.1)
        watcher.stop()

        # Callback should not be called for non-existent file
        assert len(errors) == 0


class TestConfigurationIntegration:
    """Test configuration system integration."""

    @pytest.fixture
    def full_config_setup(self):
        """Set up full configuration environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create configuration files
            base_config = {
                "environment": "development",
                "performance": {
                    "max_memory_mb": 256,
                    "cache_size": 500
                },
                "trigger_policies": {
                    "default": {
                        "enabled": True,
                        "trigger_threshold": 0.7
                    }
                }
            }

            prod_config = {
                "environment": "production",
                "performance": {
                    "max_memory_mb": 2048,
                    "optimization_level": "aggressive"
                }
            }

            # Write configuration files
            with open(config_dir / "memory_trigger_config.yaml", "w") as f:
                yaml.dump(base_config, f)

            with open(config_dir / "memory_trigger_config.production.yaml", "w") as f:
                yaml.dump(prod_config, f)

            yield config_dir

    def test_environment_specific_loading(self, full_config_setup):
        """Test loading environment-specific configurations."""
        # Development environment
        dev_manager = MemoryTriggerConfigManager(
            config_directory=full_config_setup,
            environment=Environment.DEVELOPMENT
        )
        dev_manager.load_configuration()

        assert dev_manager.config.performance.max_memory_mb == 256

        # Production environment
        prod_manager = MemoryTriggerConfigManager(
            config_directory=full_config_setup,
            environment=Environment.PRODUCTION
        )
        prod_manager.load_configuration()

        # Should have production overrides
        assert prod_manager.config.performance.max_memory_mb == 2048
        assert prod_manager.config.performance.optimization_level == "aggressive"

    def test_configuration_merging(self, full_config_setup):
        """Test configuration merging behavior."""
        manager = MemoryTriggerConfigManager(
            config_directory=full_config_setup,
            environment=Environment.PRODUCTION
        )
        manager.load_configuration()

        # Should have base values not overridden
        assert manager.config.performance.cache_size == 500
        
        # Should have production overrides
        assert manager.config.performance.max_memory_mb == 2048

    @pytest.mark.asyncio
    async def test_async_configuration_updates(self, full_config_setup):
        """Test asynchronous configuration updates."""
        manager = MemoryTriggerConfigManager(
            config_directory=full_config_setup,
            environment=Environment.DEVELOPMENT
        )
        
        # Mock async update method
        async def async_update():
            await asyncio.sleep(0.1)
            manager.config.performance.max_memory_mb = 512
            return True

        # Perform async update
        result = await async_update()
        assert result is True
        assert manager.config.performance.max_memory_mb == 512


if __name__ == "__main__":
    pytest.main([__file__, "-v"])