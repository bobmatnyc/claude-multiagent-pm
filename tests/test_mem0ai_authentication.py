"""
Test suite for mem0AI integration authentication and security features.

Tests secure API authentication, credential management, error handling,
and security validation for the mem0AI service integration.
"""

import pytest
import asyncio
import os
import secrets
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from claude_pm.integrations.security import (
    SecurityConfig, Mem0AIAuthenticator, CredentialManager,
    SecurityEventLogger, AuthenticationEvent, create_security_config,
    validate_security_configuration, generate_secure_api_key, mask_api_key
)
from claude_pm.integrations.mem0ai_integration import (
    Mem0AIConfig, Mem0AIIntegration, create_mem0ai_integration,
    create_secure_mem0ai_integration
)


class TestSecurityConfig:
    """Test security configuration and validation."""
    
    def test_valid_config_creation(self):
        """Test creating a valid security configuration."""
        config = SecurityConfig(
            api_key="test_key_with_sufficient_length_12345",
            use_tls=True,
            verify_ssl=True
        )
        
        assert config.api_key == "test_key_with_sufficient_length_12345"
        assert config.use_tls is True
        assert config.verify_ssl is True
        assert config.auth_retry_attempts == 3
        assert config.max_auth_failures == 5
    
    def test_invalid_api_key_length(self):
        """Test that short API keys are rejected."""
        with pytest.raises(ValueError, match="API key must be at least 32 characters"):
            SecurityConfig(api_key="short_key")
    
    def test_config_from_environment(self):
        """Test creating config from environment variables."""
        with patch.dict(os.environ, {
            'MEM0AI_API_KEY': 'env_key_with_sufficient_length_12345',
            'MEM0AI_USE_TLS': 'true',
            'MEM0AI_VERIFY_SSL': 'false',
            'MEM0AI_AUTH_RETRY_ATTEMPTS': '5'
        }):
            config = create_security_config()
            
            assert config.api_key == 'env_key_with_sufficient_length_12345'
            assert config.use_tls is True
            assert config.verify_ssl is False
            assert config.auth_retry_attempts == 5
    
    def test_config_validation(self):
        """Test security configuration validation."""
        # Valid configuration
        valid_config = SecurityConfig(
            api_key="valid_key_with_sufficient_length_123",
            use_tls=True,
            verify_ssl=True
        )
        
        validation = validate_security_configuration(valid_config)
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        
        # Invalid configuration (no API key)
        invalid_config = SecurityConfig(api_key=None)
        validation = validate_security_configuration(invalid_config)
        assert len(validation["warnings"]) > 0
        assert "No API key configured" in str(validation["warnings"])


class TestCredentialManager:
    """Test credential management functionality."""
    
    def test_api_key_retrieval(self):
        """Test API key retrieval from config and environment."""
        config = SecurityConfig(api_key="config_key_with_sufficient_length_123")
        manager = CredentialManager(config)
        
        # Should get key from config
        key = manager.get_api_key()
        assert key == "config_key_with_sufficient_length_123"
    
    def test_api_key_environment_override(self):
        """Test that environment variable overrides config."""
        config = SecurityConfig(api_key="config_key_with_sufficient_length_123")
        manager = CredentialManager(config)
        
        with patch.dict(os.environ, {
            'MEM0AI_API_KEY': 'env_key_with_sufficient_length_12345'
        }):
            key = manager.get_api_key()
            assert key == 'env_key_with_sufficient_length_12345'
    
    def test_invalid_key_format_rejection(self):
        """Test that invalid API key formats are rejected."""
        config = SecurityConfig(api_key="test_key_with_sufficient_length_123")
        manager = CredentialManager(config)
        
        # Mock the validation to return False
        with patch.object(manager, '_validate_api_key_format', return_value=False):
            key = manager.get_api_key()
            assert key is None
    
    def test_api_key_rotation(self):
        """Test API key rotation functionality."""
        config = SecurityConfig()
        manager = CredentialManager(config)
        
        new_key = manager.rotate_api_key()
        assert len(new_key) >= 32
        assert isinstance(new_key, str)
    
    def test_credential_cache_clearing(self):
        """Test credential cache clearing."""
        config = SecurityConfig(api_key="test_key_with_sufficient_length_123")
        manager = CredentialManager(config)
        
        # Get key to populate cache
        manager.get_api_key()
        assert manager._api_key_cache is not None
        
        # Clear cache
        manager.clear_cached_credentials()
        assert manager._api_key_cache is None
        assert manager._last_key_validation is None


class TestSecurityEventLogger:
    """Test security event logging functionality."""
    
    def test_event_logging(self):
        """Test logging security events."""
        logger = SecurityEventLogger()
        
        event = AuthenticationEvent(
            timestamp=datetime.now(),
            event_type="auth_success",
            service_host="localhost:8002",
            details={"status_code": 200}
        )
        
        logger.log_event(event)
        
        assert len(logger.events) == 1
        assert logger.events[0].event_type == "auth_success"
        assert logger.events[0].service_host == "localhost:8002"
    
    def test_failure_counting(self):
        """Test counting authentication failures."""
        logger = SecurityEventLogger()
        
        # Log multiple failures
        for i in range(3):
            event = AuthenticationEvent(
                timestamp=datetime.now(),
                event_type="auth_failure",
                service_host="localhost:8002"
            )
            logger.log_event(event)
        
        failures = logger.get_recent_failures("localhost:8002", 60)
        assert failures == 3
    
    def test_lockout_detection(self):
        """Test lockout detection after multiple failures."""
        logger = SecurityEventLogger()
        
        # Log enough failures to trigger lockout
        for i in range(6):  # More than MAX_AUTH_FAILURES (5)
            event = AuthenticationEvent(
                timestamp=datetime.now(),
                event_type="auth_failure",
                service_host="localhost:8002"
            )
            logger.log_event(event)
        
        assert logger.is_host_locked_out("localhost:8002") is True
        assert logger.is_host_locked_out("other_host:8002") is False


class TestMem0AIAuthenticator:
    """Test mem0AI authentication functionality."""
    
    def test_authenticator_initialization(self):
        """Test authenticator initialization."""
        config = SecurityConfig(api_key="test_key_with_sufficient_length_123")
        auth = Mem0AIAuthenticator(config)
        
        assert auth.config == config
        assert isinstance(auth.credential_manager, CredentialManager)
        assert isinstance(auth.security_logger, SecurityEventLogger)
    
    def test_auth_header_creation(self):
        """Test authentication header creation."""
        config = SecurityConfig(
            api_key="test_key_with_sufficient_length_123",
            authorization_scheme="Bearer"
        )
        auth = Mem0AIAuthenticator(config)
        
        headers = auth.create_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_key_with_sufficient_length_123"
        assert "User-Agent" in headers
        assert "X-Request-ID" in headers
        assert "X-Timestamp" in headers
    
    def test_auth_header_creation_without_key(self):
        """Test that creating headers without API key raises error."""
        config = SecurityConfig(api_key=None)
        auth = Mem0AIAuthenticator(config)
        
        with pytest.raises(ValueError, match="No API key available"):
            auth.create_auth_headers()
    
    def test_ssl_context_creation(self):
        """Test SSL context creation."""
        # With TLS enabled
        config = SecurityConfig(use_tls=True, verify_ssl=True)
        auth = Mem0AIAuthenticator(config)
        
        context = auth.create_ssl_context()
        assert context is not None
        
        # Without TLS
        config = SecurityConfig(use_tls=False)
        auth = Mem0AIAuthenticator(config)
        
        context = auth.create_ssl_context()
        assert context is None
    
    @pytest.mark.asyncio
    async def test_authentication_validation_success(self):
        """Test successful authentication validation."""
        config = SecurityConfig(api_key="test_key_with_sufficient_length_123")
        auth = Mem0AIAuthenticator(config)
        
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await auth.validate_authentication(mock_session, "http://localhost:8002")
        
        assert result is True
        assert auth.is_authenticated() is True
        assert auth._auth_failures == 0
    
    @pytest.mark.asyncio
    async def test_authentication_validation_failure(self):
        """Test authentication validation failure."""
        config = SecurityConfig(api_key="test_key_with_sufficient_length_123")
        auth = Mem0AIAuthenticator(config)
        
        # Mock authentication failure response
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await auth.validate_authentication(mock_session, "http://localhost:8002")
        
        assert result is False
        assert auth.is_authenticated() is False
        assert auth._auth_failures == 1
    
    def test_auth_status_reporting(self):
        """Test authentication status reporting."""
        config = SecurityConfig(api_key="test_key_with_sufficient_length_123")
        auth = Mem0AIAuthenticator(config)
        
        status = auth.get_auth_status()
        
        assert "authenticated" in status
        assert "failure_count" in status
        assert "has_api_key" in status
        assert "config" in status
        assert status["has_api_key"] is True


class TestMem0AIIntegrationSecurity:
    """Test mem0AI integration with security features."""
    
    def test_integration_with_security_config(self):
        """Test integration initialization with security configuration."""
        config = Mem0AIConfig(
            host="localhost",
            port=8002,
            api_key="test_key_with_sufficient_length_123"
        )
        
        integration = Mem0AIIntegration(config)
        
        assert integration.config.api_key == "test_key_with_sufficient_length_123"
        assert isinstance(integration.authenticator, Mem0AIAuthenticator)
        assert integration.base_url == "http://localhost:8002"  # HTTP by default
    
    def test_integration_with_tls(self):
        """Test integration with TLS configuration."""
        security_config = SecurityConfig(
            api_key="test_key_with_sufficient_length_123",
            use_tls=True
        )
        
        config = Mem0AIConfig(
            host="localhost",
            port=8002,
            security_config=security_config
        )
        
        integration = Mem0AIIntegration(config)
        
        assert integration.base_url == "https://localhost:8002"  # HTTPS with TLS
    
    def test_security_status_reporting(self):
        """Test security status reporting."""
        config = Mem0AIConfig(
            api_key="test_key_with_sufficient_length_123"
        )
        
        integration = Mem0AIIntegration(config)
        status = integration.get_security_status()
        
        assert "connected" in status
        assert "authenticated" in status
        assert "base_url" in status
        assert "tls_enabled" in status
        assert "api_key_configured" in status
        assert "authenticator_status" in status
        
        assert status["api_key_configured"] is True
        assert status["base_url"] == "http://localhost:8002"
    
    def test_factory_function_with_security(self):
        """Test factory function with security parameters."""
        integration = create_mem0ai_integration(
            host="localhost",
            port=8002,
            api_key="test_key_with_sufficient_length_123",
            use_tls=True,
            verify_ssl=False
        )
        
        assert integration.config.api_key == "test_key_with_sufficient_length_123"
        assert integration.config.security_config.use_tls is True
        assert integration.config.security_config.verify_ssl is False
    
    def test_secure_factory_function(self):
        """Test secure factory function."""
        integration = create_secure_mem0ai_integration(
            host="localhost",
            port=8002,
            api_key="test_key_with_sufficient_length_123"
        )
        
        assert integration.config.security_config.use_tls is True
        assert integration.config.security_config.verify_ssl is True
        assert integration.base_url == "https://localhost:8002"
    
    def test_secure_factory_without_api_key(self):
        """Test that secure factory requires API key."""
        with pytest.raises(ValueError, match="API key is required"):
            create_secure_mem0ai_integration(
                host="localhost",
                port=8002,
                api_key=None
            )


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_api_key_generation(self):
        """Test secure API key generation."""
        key = generate_secure_api_key()
        
        assert isinstance(key, str)
        assert len(key) >= 32
        
        # Generate multiple keys to ensure uniqueness
        keys = [generate_secure_api_key() for _ in range(5)]
        assert len(set(keys)) == 5  # All should be unique
    
    def test_api_key_masking(self):
        """Test API key masking for safe logging."""
        key = "test_key_with_sufficient_length_123456789"
        masked = mask_api_key(key)
        
        assert masked.startswith("test")
        assert masked.endswith("6789")
        assert "..." in masked
        assert len(masked) < len(key)
        
        # Test invalid key
        invalid_masked = mask_api_key("short")
        assert invalid_masked == "***INVALID***"
        
        # Test empty key
        empty_masked = mask_api_key("")
        assert empty_masked == "***INVALID***"


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self):
        """Test complete authentication flow."""
        # This test would require a running mem0AI service
        # For now, we'll mock the necessary components
        
        config = Mem0AIConfig(
            api_key="test_key_with_sufficient_length_123"
        )
        
        integration = Mem0AIIntegration(config)
        
        # Mock the session and responses
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock successful auth validation
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Test connection with authentication
            connected = await integration.connect()
            
            # Verify the flow
            assert connected is True
            assert integration.is_connected() is True
            assert integration.is_authenticated() is True
    
    def test_environment_configuration_precedence(self):
        """Test environment variable configuration precedence."""
        with patch.dict(os.environ, {
            'MEM0AI_API_KEY': 'env_key_with_sufficient_length_12345',
            'MEM0AI_USE_TLS': 'true',
            'MEM0AI_VERIFY_SSL': 'false'
        }):
            # Config should be loaded from environment
            integration = create_mem0ai_integration()
            
            assert integration.config.api_key == 'env_key_with_sufficient_length_12345'
            assert integration.config.security_config.use_tls is True
            assert integration.config.security_config.verify_ssl is False
    
    def test_security_validation_workflow(self):
        """Test security validation workflow."""
        # Create config with various security issues
        configs = [
            SecurityConfig(api_key=None),  # No API key
            SecurityConfig(api_key="short"),  # Short key (should raise exception)
            SecurityConfig(api_key="valid_key_with_sufficient_length_123", use_tls=False)  # No TLS
        ]
        
        # Test validation
        try:
            validation = validate_security_configuration(configs[0])
            assert len(validation["warnings"]) > 0
        except ValueError:
            pass  # Expected for invalid config
        
        # Test with good config
        good_config = SecurityConfig(
            api_key="secure_key_with_sufficient_length_123",
            use_tls=True,
            verify_ssl=True
        )
        
        validation = validate_security_configuration(good_config)
        assert validation["valid"] is True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])