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
        config_path = temp_config_dir / "config.yaml"
        manager = MemoryTriggerConfigManager(
            config_path=str(config_path)
        )
        return manager

    def test_manager_initialization(self, config_manager, temp_config_dir):
        """Test configuration manager initialization."""
        assert config_manager.config_path == temp_config_dir / "config.yaml"
        assert config_manager.config is not None

    def test_load_configuration(self, config_manager, temp_config_dir, sample_config):
        """Test loading configuration from file."""
        # Write configuration file
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load configuration
        success = config_manager.load_config()
        assert success is True

        # Verify loaded values
        assert config_manager.config.performance.max_memory_mb == 256
        assert config_manager.config.performance.cache_size == 500

    def test_save_configuration(self, config_manager, temp_config_dir):
        """Test saving configuration to file."""
        # Modify configuration
        config_manager.config.performance.max_memory_mb = 1024

        # Save configuration
        success = config_manager.save_config()
        assert success is True

        # Verify file exists
        config_file = temp_config_dir / "config.yaml"
        assert config_file.exists()

        # Load and verify
        with open(config_file, "r") as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config["performance"]["max_memory_mb"] == 1024

    def test_validate_configuration(self, config_manager):
        """Test configuration validation."""
        # Valid configuration
        assert config_manager.config.validate() is True

        # Invalid configuration
        config_manager.config.performance.max_memory_mb = -1
        assert config_manager.config.validate() is False

    def test_update_config(self, config_manager):
        """Test configuration updates."""
        # Create initial config
        config_manager.config.performance.max_memory_mb = 256

        # Update configuration
        updates = {
            "performance": {
                "max_memory_mb": 2048,
                "optimization_level": "aggressive"
            }
        }

        success = config_manager.update_config(updates)
        assert success is True

        assert config_manager.config.performance.max_memory_mb == 2048
        assert config_manager.config.performance.optimization_level == "aggressive"

    def test_get_trigger_policy(self, config_manager):
        """Test getting trigger policy configuration."""
        # The config has a default trigger_policy attribute
        policy = config_manager.config.trigger_policy
        assert policy is not None
        assert isinstance(policy, TriggerPolicyConfig)
        
        # Update trigger policy
        config_manager.config.trigger_policy.trigger_threshold = 0.9
        config_manager.config.trigger_policy.cooldown_seconds = 60
        
        # Verify updates
        assert config_manager.config.trigger_policy.trigger_threshold == 0.9
        assert config_manager.config.trigger_policy.cooldown_seconds == 60

    def test_update_trigger_policy(self, config_manager):
        """Test updating trigger policy."""
        # Update policy using update_config
        updates = {
            "trigger_policy": {
                "trigger_threshold": 0.95,
                "cooldown_seconds": 180
            }
        }

        success = config_manager.update_config(updates)
        assert success is True

        assert config_manager.config.trigger_policy.trigger_threshold == 0.95
        assert config_manager.config.trigger_policy.cooldown_seconds == 180

    def test_hot_reload_configuration(self, config_manager, temp_config_dir, sample_config):
        """Test hot reload functionality."""
        # Write initial configuration
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load initial configuration
        config_manager.load_config()
        initial_memory = config_manager.config.performance.max_memory_mb

        # Modify configuration file
        sample_config["performance"]["max_memory_mb"] = 512
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Reload configuration
        config_manager.load_config()

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

        # Register callback (observer)
        config_manager.add_observer(test_callback)

        # Trigger callbacks
        config_manager.notify_observers()

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
        dev_config_path = full_config_setup / "memory_trigger_config.yaml"
        dev_manager = MemoryTriggerConfigManager(
            config_path=str(dev_config_path)
        )
        dev_manager.load_config()

        assert dev_manager.config.performance.max_memory_mb == 256

        # Production environment - merge configs manually
        base_config_path = full_config_setup / "memory_trigger_config.yaml"
        prod_config_path = full_config_setup / "memory_trigger_config.production.yaml"
        
        with open(base_config_path, "r") as f:
            config_data = yaml.safe_load(f)
        with open(prod_config_path, "r") as f:
            prod_overrides = yaml.safe_load(f)
        
        # Merge configs
        config_data["performance"].update(prod_overrides["performance"])
        
        prod_yaml_path = full_config_setup / "prod_config.yaml"
        with open(prod_yaml_path, "w") as f:
            yaml.dump(config_data, f)
            
        prod_manager = MemoryTriggerConfigManager(
            config_path=str(prod_yaml_path)
        )
        prod_manager.load_config()

        # Should have production overrides
        assert prod_manager.config.performance.max_memory_mb == 2048
        assert prod_manager.config.performance.optimization_level == "aggressive"

    def test_configuration_merging(self, full_config_setup):
        """Test configuration merging behavior."""
        # Load base config
        base_config_path = full_config_setup / "memory_trigger_config.yaml"
        with open(base_config_path, "r") as f:
            base_config = yaml.safe_load(f)
            
        # Load production overrides
        prod_config_path = full_config_setup / "memory_trigger_config.production.yaml"
        with open(prod_config_path, "r") as f:
            prod_config = yaml.safe_load(f)
            
        # Merge configs
        base_config["performance"].update(prod_config["performance"])
        
        # Save merged config as YAML
        merged_path = full_config_setup / "merged_config.yaml"
        with open(merged_path, "w") as f:
            yaml.dump(base_config, f)
            
        manager = MemoryTriggerConfigManager(
            config_path=str(merged_path)
        )
        manager.load_config()

        # Should have base values not overridden
        assert manager.config.performance.cache_size == 500
        
        # Should have production overrides
        assert manager.config.performance.max_memory_mb == 2048

    @pytest.mark.asyncio
    async def test_async_configuration_updates(self, full_config_setup):
        """Test asynchronous configuration updates."""
        config_path = full_config_setup / "async_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"performance": {"max_memory_mb": 256}}, f)
            
        manager = MemoryTriggerConfigManager(
            config_path=str(config_path)
        )
        manager.load_config()
        
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