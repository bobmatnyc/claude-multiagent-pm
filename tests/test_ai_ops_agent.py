#!/usr/bin/env python3
"""
Test suite for AI Ops Agent

Basic test coverage for AI Operations Agent functionality including
configuration management, provider integration, and core operations.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the components to test
from claude_pm.agents.ai_ops_agent import AIOpsAgent, AIServiceProvider, AIServiceRequest
from claude_pm.services.ai_ops.config_manager import ConfigManager, ConfigLevel, ProviderConfig, AIOpConfig


class TestConfigManager:
    """Test ConfigManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.config_manager = ConfigManager(project_root=self.project_root)
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initializes correctly."""
        assert self.config_manager.project_root == self.project_root
        assert isinstance(self.config_manager.config_cache, dict)
        assert len(self.config_manager.config_file_paths) == 4  # Four config levels
    
    def test_get_default_config(self):
        """Test default configuration generation."""
        default_config = self.config_manager._get_default_config()
        
        assert "providers" in default_config
        assert "cost" in default_config
        assert "security" in default_config
        assert "monitoring" in default_config
        
        # Check default providers
        assert "openai" in default_config["providers"]
        assert "anthropic" in default_config["providers"]
        
        # Check provider structure
        openai_config = default_config["providers"]["openai"]
        assert openai_config["provider_id"] == "openai"
        assert openai_config["api_key_env"] == "OPENAI_API_KEY"
        assert openai_config["enabled"] is True
    
    def test_get_merged_config(self):
        """Test configuration merging."""
        config = self.config_manager.get_merged_config()
        
        assert isinstance(config, AIOpConfig)
        assert len(config.providers) >= 2  # At least OpenAI and Anthropic
        assert config.cost.daily_budget > 0
        assert config.security.audit_logging is True
        assert config.monitoring.health_check_interval > 0
    
    def test_get_provider_config(self):
        """Test getting specific provider configuration."""
        openai_config = self.config_manager.get_provider_config("openai")
        assert openai_config is not None
        assert isinstance(openai_config, ProviderConfig)
        assert openai_config.provider_id == "openai"
        assert openai_config.api_key_env == "OPENAI_API_KEY"
        
        # Test non-existent provider
        fake_config = self.config_manager.get_provider_config("fake_provider")
        assert fake_config is None
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        validation = self.config_manager.validate_configuration()
        
        assert isinstance(validation, dict)
        assert "valid" in validation
        assert "errors" in validation
        assert "warnings" in validation
        assert "missing_env_vars" in validation
        
        # Should have warnings about missing environment variables
        assert len(validation["missing_env_vars"]) > 0
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key", "ANTHROPIC_API_KEY": "test_key"})
    def test_environment_variables_detection(self):
        """Test environment variable detection."""
        env_vars = self.config_manager.get_environment_variables()
        
        assert "OPENAI_API_KEY" in env_vars
        assert "ANTHROPIC_API_KEY" in env_vars
        assert env_vars["OPENAI_API_KEY"] == "test_key"
        assert env_vars["ANTHROPIC_API_KEY"] == "test_key"
    
    def test_config_update(self):
        """Test configuration updates."""
        # Create a test update
        updates = {
            "cost": {
                "daily_budget": 200.0,
                "monthly_budget": 5000.0
            }
        }
        
        # Update at project level
        self.config_manager.update_config(ConfigLevel.PROJECT, updates)
        
        # Verify the update
        config = self.config_manager.get_merged_config()
        assert config.cost.daily_budget == 200.0
        assert config.cost.monthly_budget == 5000.0


class TestAIOpsAgent:
    """Test AIOpsAgent functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.agent_id = "test_ai_ops"
        self.ai_ops_agent = AIOpsAgent(agent_id=self.agent_id)
    
    def test_ai_ops_agent_initialization(self):
        """Test AIOpsAgent initializes correctly."""
        assert self.ai_ops_agent.agent_id == self.agent_id
        assert hasattr(self.ai_ops_agent, 'config_manager')
        assert hasattr(self.ai_ops_agent, 'service_manager')
        assert hasattr(self.ai_ops_agent, 'cost_manager')
    
    def test_agent_type_properties(self):
        """Test agent type and identification properties."""
        assert self.ai_ops_agent.agent_type == "ai_ops"
        assert "AI Operations" in self.ai_ops_agent.description
        assert len(self.ai_ops_agent.capabilities) > 0
    
    @pytest.mark.asyncio
    async def test_ai_service_request_validation(self):
        """Test AI service request validation."""
        # Valid request
        valid_request = AIServiceRequest(
            provider="openai",
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=100,
            temperature=0.7
        )
        
        assert valid_request.provider == "openai"
        assert valid_request.model == "gpt-4"
        assert len(valid_request.messages) == 1
        assert valid_request.max_tokens == 100
        assert valid_request.temperature == 0.7
    
    def test_provider_enum(self):
        """Test AIServiceProvider enum."""
        assert AIServiceProvider.OPENAI.value == "openai"
        assert AIServiceProvider.ANTHROPIC.value == "anthropic"
        assert AIServiceProvider.GOOGLE.value == "google"
        assert AIServiceProvider.OPENROUTER.value == "openrouter"
        assert AIServiceProvider.VERCEL.value == "vercel"
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_configuration_access(self):
        """Test agent configuration access."""
        config = self.ai_ops_agent.config_manager.get_merged_config()
        
        assert isinstance(config, AIOpConfig)
        assert len(config.providers) >= 2
        
        # Test environment variable access
        env_vars = self.ai_ops_agent.config_manager.get_environment_variables()
        assert "OPENAI_API_KEY" in env_vars
    
    def test_health_check_capability(self):
        """Test health check capabilities."""
        validation = self.ai_ops_agent.config_manager.validate_configuration()
        
        assert isinstance(validation, dict)
        assert "valid" in validation
        
        # Agent should be able to perform basic health checks
        assert hasattr(self.ai_ops_agent, 'config_manager')


class TestAIOpsIntegration:
    """Test AI Ops integration with framework components."""
    
    def test_import_availability(self):
        """Test that all AI Ops components can be imported."""
        from claude_pm.agents.ai_ops_agent import AIOpsAgent
        from claude_pm.services.ai_ops.config_manager import ConfigManager
        from claude_pm.services.ai_ops.ai_service_manager import AIServiceManager
        from claude_pm.services.ai_ops.cost_manager import CostManager
        from claude_pm.services.ai_ops.tools_manager import ToolsManager
        from claude_pm.services.ai_ops.security_framework import SecurityFramework
        
        assert AIOpsAgent is not None
        assert ConfigManager is not None
        assert AIServiceManager is not None
        assert CostManager is not None
        assert ToolsManager is not None
        assert SecurityFramework is not None
    
    def test_agent_registration(self):
        """Test that AI Ops Agent is registered in the framework."""
        from claude_pm.agents import AIOpsAgent
        
        assert AIOpsAgent is not None
        
        # Test agent can be instantiated
        agent = AIOpsAgent(agent_id="test_integration")
        assert agent.agent_id == "test_integration"
    
    def test_cli_command_integration(self):
        """Test that CLI commands are available."""
        from claude_pm.cmpm_commands import cmpm_ai_ops
        
        assert cmpm_ai_ops is not None
        assert cmpm_ai_ops.name == "cmpm:ai-ops"
    
    def test_configuration_file_structure(self):
        """Test configuration file path structure."""
        config_manager = ConfigManager()
        
        assert len(config_manager.config_file_paths) == 4
        assert ConfigLevel.SYSTEM in config_manager.config_file_paths
        assert ConfigLevel.USER in config_manager.config_file_paths
        assert ConfigLevel.PROJECT in config_manager.config_file_paths
        assert ConfigLevel.RUNTIME in config_manager.config_file_paths


class TestAIOpsErrorHandling:
    """Test error handling in AI Ops components."""
    
    def test_config_manager_invalid_path(self):
        """Test ConfigManager with invalid project path."""
        invalid_path = Path("/nonexistent/path")
        config_manager = ConfigManager(project_root=invalid_path)
        
        # Should still work with default configuration
        config = config_manager.get_merged_config()
        assert isinstance(config, AIOpConfig)
    
    def test_missing_provider_config(self):
        """Test handling of missing provider configuration."""
        config_manager = ConfigManager()
        missing_provider = config_manager.get_provider_config("nonexistent")
        
        assert missing_provider is None
    
    def test_validation_with_missing_env_vars(self):
        """Test validation when environment variables are missing."""
        config_manager = ConfigManager()
        validation = config_manager.validate_configuration()
        
        # Should detect missing environment variables
        assert len(validation["missing_env_vars"]) > 0
        assert len(validation["warnings"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])