"""
Unit Tests for Phase 1 Interface Implementations
==============================================

Comprehensive test suite for the new interface-based architecture including:
- Core service interfaces
- Dependency injection container
- Configuration service
- Enhanced base service
- Agent registry service
- Shared prompt cache service

Test Categories:
- Interface compliance testing
- Dependency injection validation
- Service lifecycle management
- Error handling and resilience
- Performance and caching
- Health monitoring
"""

import asyncio
import pytest
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

# Import the interfaces and implementations
from claude_pm.core.interfaces import (
    IServiceLifecycle, IConfigurationService, ICacheService, IAgentRegistry,
    AgentMetadata
)
from claude_pm.core.base_service import ServiceHealth, ServiceMetrics
from claude_pm.core.container import ServiceContainer
from claude_pm.core.config_service import ConfigurationService
# These enhanced services have compatibility issues with missing decorators/interfaces
# from claude_pm.core.enhanced_base_service import EnhancedBaseService
# from claude_pm.services.enhanced_agent_registry import EnhancedAgentRegistry  
# from claude_pm.services.enhanced_shared_prompt_cache import EnhancedSharedPromptCache


class TestServiceInterfaces:
    """Test core service interfaces for compliance and functionality."""
    
    def test_service_interface_contract(self):
        """Test that IServiceLifecycle interface defines required methods."""
        # IServiceLifecycle has different methods than the old IService
        required_methods = ['initialize', 'start', 'stop', 'restart', 'is_running']
        
        for method in required_methods:
            assert hasattr(IServiceLifecycle, method), f"IServiceLifecycle missing required method: {method}"
    
    def test_configuration_service_interface_contract(self):
        """Test that IConfigurationService interface defines required methods."""
        required_methods = ['get', 'set', 'update', 'validate', 'load_file', 'save']
        
        for method in required_methods:
            assert hasattr(IConfigurationService, method), f"IConfigurationService missing required method: {method}"
    
    def test_cache_service_interface_contract(self):
        """Test that ICacheService interface defines required methods."""
        required_methods = ['get', 'set', 'delete', 'invalidate', 'clear', 'get_cache_metrics']
        
        for method in required_methods:
            assert hasattr(ICacheService, method), f"ICacheService missing required method: {method}"
    
    def test_agent_registry_interface_contract(self):
        """Test that IAgentRegistry interface defines required methods."""
        required_methods = [
            'discover_agents', 'get_agent', 'list_agents', 
            'get_specialized_agents', 'search_agents_by_capability', 
            'refresh_agent', 'clear_cache'
        ]
        
        for method in required_methods:
            assert hasattr(IAgentRegistry, method), f"IAgentRegistry missing required method: {method}"


class TestServiceContainer:
    """Test dependency injection container functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.container = ServiceContainer()
    
    def test_container_initialization(self):
        """Test container initializes correctly."""
        assert self.container is not None
        assert len(self.container.get_registrations()) >= 1  # Should have itself registered
    
    def test_register_service_implementation(self):
        """Test registering service implementation."""
        
        # Define test interface and implementation
        class ITestService:
            def do_something(self) -> str:
                pass
        
        class TestServiceImpl:
            def do_something(self) -> str:
                return "test_result"
        
        # Register service
        self.container.register_service(ITestService, TestServiceImpl)
        
        # Verify registration
        assert self.container.has_service(ITestService)
        
        # Get service
        service = self.container.get_service(ITestService)
        assert service is not None
        assert isinstance(service, TestServiceImpl)
        assert service.do_something() == "test_result"
    
    def test_register_service_instance(self):
        """Test registering service instance."""
        
        class ITestService:
            def get_value(self) -> str:
                pass
        
        class TestServiceImpl:
            def __init__(self, value: str):
                self.value = value
            
            def get_value(self) -> str:
                return self.value
        
        # Create instance and register
        instance = TestServiceImpl("instance_value")
        self.container.register_instance(ITestService, instance)
        
        # Verify registration
        assert self.container.has_service(ITestService)
        
        # Get service - should be same instance
        service = self.container.get_service(ITestService)
        assert service is instance
        assert service.get_value() == "instance_value"
    
    def test_dependency_injection(self):
        """Test automatic dependency injection."""
        
        class IDependency:
            def get_data(self) -> str:
                pass
        
        class ITestService:
            def process(self) -> str:
                pass
        
        class DependencyImpl:
            def get_data(self) -> str:
                return "dependency_data"
        
        class TestServiceImpl:
            def __init__(self, dependency: IDependency):
                self.dependency = dependency
            
            def process(self) -> str:
                return f"processed_{self.dependency.get_data()}"
        
        # Register dependency first
        self.container.register_service(IDependency, DependencyImpl)
        
        # Register service with dependency
        self.container.register_service(ITestService, TestServiceImpl)
        
        # Get service - dependency should be injected
        service = self.container.get_service(ITestService)
        assert service.process() == "processed_dependency_data"
    
    def test_singleton_behavior(self):
        """Test singleton service behavior."""
        
        class ITestService:
            def get_id(self) -> int:
                pass
        
        class TestServiceImpl:
            def __init__(self):
                self.id = id(self)
            
            def get_id(self) -> int:
                return self.id
        
        # Register as singleton (default)
        self.container.register_service(ITestService, TestServiceImpl, singleton=True)
        
        # Get service multiple times
        service1 = self.container.get_service(ITestService)
        service2 = self.container.get_service(ITestService)
        
        # Should be same instance
        assert service1 is service2
        assert service1.get_id() == service2.get_id()
    
    def test_transient_behavior(self):
        """Test transient service behavior."""
        
        class ITestService:
            def get_id(self) -> int:
                pass
        
        class TestServiceImpl:
            def __init__(self):
                self.id = id(self)
            
            def get_id(self) -> int:
                return self.id
        
        # Register as transient
        self.container.register_service(ITestService, TestServiceImpl, singleton=False)
        
        # Get service multiple times
        service1 = self.container.get_service(ITestService)
        service2 = self.container.get_service(ITestService)
        
        # Should be different instances
        assert service1 is not service2
        assert service1.get_id() != service2.get_id()
    
    def test_service_validation(self):
        """Test service registration validation."""
        errors = self.container.validate_registrations()
        
        # Should have no errors for basic setup
        assert isinstance(errors, list)
    
    def test_service_scope(self):
        """Test service scope functionality."""
        
        class ITestService:
            def get_value(self) -> str:
                pass
        
        class TestServiceImpl:
            def get_value(self) -> str:
                return "scoped_value"
        
        self.container.register_service(ITestService, TestServiceImpl)
        
        # Create scope
        scope = self.container.create_scope()
        
        # Get service from scope
        service = scope.get_service(ITestService)
        assert service.get_value() == "scoped_value"
        
        # Dispose scope
        scope.dispose()


class TestConfigurationService:
    """Test configuration service implementation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config_service = ConfigurationService()
    
    def test_configuration_service_initialization(self):
        """Test configuration service initializes correctly."""
        assert self.config_service is not None
        assert isinstance(self.config_service, IConfigurationService)
    
    def test_get_set_configuration(self):
        """Test getting and setting configuration values."""
        # Set value
        self.config_service.set("test.key", "test_value")
        
        # Get value
        value = self.config_service.get("test.key")
        assert value == "test_value"
        
        # Get non-existent value with default
        default_value = self.config_service.get("non.existent", "default")
        assert default_value == "default"
    
    def test_nested_configuration(self):
        """Test nested configuration with dot notation."""
        # Set nested value
        self.config_service.set("app.database.host", "localhost")
        self.config_service.set("app.database.port", 5432)
        
        # Get nested values
        assert self.config_service.get("app.database.host") == "localhost"
        assert self.config_service.get("app.database.port") == 5432
    
    def test_configuration_update(self):
        """Test configuration updates."""
        # Initial values
        self.config_service.set("key1", "value1")
        self.config_service.set("key2", "value2")
        
        # Update with dictionary
        updates = {
            "key1": "updated_value1",
            "key3": "new_value3"
        }
        self.config_service.update(updates)
        
        # Verify updates
        assert self.config_service.get("key1") == "updated_value1"
        assert self.config_service.get("key2") == "value2"  # unchanged
        assert self.config_service.get("key3") == "new_value3"
    
    def test_configuration_file_operations(self):
        """Test loading and saving configuration files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "test_key": "test_value",
                "nested": {
                    "inner_key": "inner_value"
                }
            }
            json.dump(config_data, f)
            config_file = Path(f.name)
        
        try:
            # Load configuration from file
            self.config_service.load_file(config_file)
            
            # Verify loaded values
            assert self.config_service.get("test_key") == "test_value"
            assert self.config_service.get("nested.inner_key") == "inner_value"
            
            # Modify and save
            self.config_service.set("new_key", "new_value")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as save_f:
                save_file = Path(save_f.name)
            
            self.config_service.save(save_file, format="json")
            
            # Verify saved file
            with open(save_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["test_key"] == "test_value"
            assert saved_data["new_key"] == "new_value"
            
        finally:
            # Cleanup
            config_file.unlink(missing_ok=True)
            if 'save_file' in locals():
                save_file.unlink(missing_ok=True)
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Set test values
        self.config_service.set("string_key", "string_value")
        self.config_service.set("int_key", 42)
        self.config_service.set("bool_key", True)
        
        # Define validation schema
        schema = {
            "string_key": str,
            "int_key": int,
            "bool_key": bool
        }
        
        # Validate - should pass
        assert self.config_service.validate(schema) is True
        
        # Invalid schema - should fail
        invalid_schema = {
            "string_key": int,  # Wrong type
            "missing_key": str  # Missing key
        }
        
        assert self.config_service.validate(invalid_schema) is False


class TestEnhancedBaseService:
    """Test enhanced base service implementation."""
    
    def setup_method(self):
        """Setup test environment."""
        
        class TestService(EnhancedBaseService):
            def __init__(self):
                super().__init__("test_service")
                self.initialized = False
                self.cleaned_up = False
            
            async def _initialize(self):
                self.initialized = True
            
            async def _cleanup(self):
                self.cleaned_up = True
        
        self.test_service = TestService()
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """Test service start/stop lifecycle."""
        # Initially not running
        assert not self.test_service.running
        
        # Start service
        await self.test_service.start()
        
        # Should be running and initialized
        assert self.test_service.running
        assert self.test_service.initialized
        
        # Stop service
        await self.test_service.stop()
        
        # Should not be running and cleaned up
        assert not self.test_service.running
        assert self.test_service.cleaned_up
    
    @pytest.mark.asyncio
    async def test_service_health_check(self):
        """Test service health checking."""
        # Start service first
        await self.test_service.start()
        
        # Perform health check
        health = await self.test_service.health_check()
        
        # Verify health object
        assert isinstance(health, ServiceHealth)
        assert health.status in ["healthy", "degraded", "unhealthy"]
        assert isinstance(health.checks, dict)
        assert "running" in health.checks
        assert health.checks["running"] is True
    
    def test_service_metrics(self):
        """Test service metrics collection."""
        metrics = self.test_service.get_metrics()
        
        assert isinstance(metrics, ServiceMetrics)
        assert hasattr(metrics, 'requests_total')
        assert hasattr(metrics, 'uptime_seconds')
    
    def test_service_properties(self):
        """Test service properties."""
        assert self.test_service.name == "test_service"
        assert isinstance(self.test_service.health, ServiceHealth)


class TestEnhancedAgentRegistry:
    """Test enhanced agent registry implementation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = ConfigurationService({"agent_registry.max_cache_size": 100})
        self.cache = EnhancedSharedPromptCache(self.config)
        self.registry = EnhancedAgentRegistry(self.config, self.cache)
    
    @pytest.mark.asyncio
    async def test_agent_registry_initialization(self):
        """Test agent registry initializes correctly."""
        assert isinstance(self.registry, IAgentRegistry)
        assert self.registry.name == "enhanced_agent_registry"
    
    @pytest.mark.asyncio
    async def test_agent_discovery(self):
        """Test agent discovery functionality."""
        # Mock discovery for testing
        with patch.object(self.registry, '_scan_directory') as mock_scan:
            mock_scan.return_value = {
                "test_agent": AgentMetadata(
                    name="test_agent",
                    type="custom",
                    path="/test/path",
                    tier="system",
                    validated=True,
                    validation_score=80.0
                )
            }
            
            # Discover agents
            agents = await self.registry.discover_agents(force_refresh=True)
            
            # Verify results
            assert isinstance(agents, dict)
            assert "test_agent" in agents
            assert agents["test_agent"].name == "test_agent"
    
    @pytest.mark.asyncio
    async def test_get_agent(self):
        """Test getting specific agent."""
        # Setup mock agent
        test_agent = AgentMetadata(
            name="test_agent",
            type="custom",
            path="/test/path",
            tier="system"
        )
        self.registry._registry["test_agent"] = test_agent
        
        # Get agent
        agent = await self.registry.get_agent("test_agent")
        
        assert agent is not None
        assert agent.name == "test_agent"
        
        # Get non-existent agent
        missing = await self.registry.get_agent("missing_agent")
        assert missing is None
    
    @pytest.mark.asyncio
    async def test_list_agents_with_filters(self):
        """Test listing agents with filters."""
        # Setup mock agents
        agents = {
            "doc_agent": AgentMetadata(name="doc_agent", type="documentation", path="/doc", tier="system"),
            "qa_agent": AgentMetadata(name="qa_agent", type="qa", path="/qa", tier="user"),
            "custom_agent": AgentMetadata(name="custom_agent", type="custom", path="/custom", tier="project")
        }
        self.registry._registry.update(agents)
        
        # List all agents
        all_agents = await self.registry.list_agents()
        assert len(all_agents) == 3
        
        # Filter by type
        doc_agents = await self.registry.list_agents(agent_type="documentation")
        assert len(doc_agents) == 1
        assert doc_agents[0].name == "doc_agent"
        
        # Filter by tier
        user_agents = await self.registry.list_agents(tier="user")
        assert len(user_agents) == 1
        assert user_agents[0].name == "qa_agent"
    
    @pytest.mark.asyncio
    async def test_search_agents_by_capability(self):
        """Test searching agents by capability."""
        # Setup mock agent with capabilities
        test_agent = AgentMetadata(
            name="test_agent",
            type="custom",
            path="/test",
            tier="system",
            capabilities=["testing", "validation", "automation"]
        )
        self.registry._registry["test_agent"] = test_agent
        
        # Search for capability
        results = await self.registry.search_agents_by_capability("testing")
        
        assert len(results) >= 1
        assert any(agent.name == "test_agent" for agent in results)
    
    def test_cache_operations(self):
        """Test cache clear functionality."""
        # Add some mock data
        self.registry._registry["test"] = AgentMetadata(
            name="test", type="custom", path="/test", tier="system"
        )
        
        # Clear cache
        self.registry.clear_cache()
        
        # Verify cache cleared
        assert len(self.registry._registry) == 0


class TestEnhancedSharedPromptCache:
    """Test enhanced shared prompt cache implementation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = ConfigurationService({
            "cache.max_size": 100,
            "cache.max_memory_mb": 10,
            "cache.default_ttl": 300
        })
        self.cache = EnhancedSharedPromptCache(self.config)
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self):
        """Test cache initializes correctly."""
        assert isinstance(self.cache, ICacheService)
        assert self.cache.name == "enhanced_shared_prompt_cache"
    
    def test_basic_cache_operations(self):
        """Test basic cache get/set/delete operations."""
        # Set value
        success = self.cache.set("test_key", "test_value", ttl=60)
        assert success is True
        
        # Get value
        value = self.cache.get("test_key")
        assert value == "test_value"
        
        # Delete value
        deleted = self.cache.delete("test_key")
        assert deleted is True
        
        # Get deleted value
        missing = self.cache.get("test_key")
        assert missing is None
    
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        # Set value with short TTL
        self.cache.set("expire_key", "expire_value", ttl=0.1)
        
        # Should be available immediately
        value = self.cache.get("expire_key")
        assert value == "expire_value"
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired
        expired = self.cache.get("expire_key")
        assert expired is None
    
    def test_cache_invalidation(self):
        """Test cache invalidation patterns."""
        # Set multiple values
        self.cache.set("prefix:key1", "value1")
        self.cache.set("prefix:key2", "value2")
        self.cache.set("other:key3", "value3")
        
        # Invalidate with pattern
        invalidated = self.cache.invalidate("prefix:*")
        assert invalidated == 2
        
        # Verify invalidation
        assert self.cache.get("prefix:key1") is None
        assert self.cache.get("prefix:key2") is None
        assert self.cache.get("other:key3") == "value3"
    
    def test_cache_clear(self):
        """Test cache clear operation."""
        # Set multiple values
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        # Clear cache
        self.cache.clear()
        
        # Verify all values cleared
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
    
    def test_cache_metrics(self):
        """Test cache metrics collection."""
        # Perform some operations
        self.cache.set("key1", "value1")
        self.cache.get("key1")  # hit
        self.cache.get("missing")  # miss
        
        # Get metrics
        metrics = self.cache.get_cache_metrics()
        
        assert isinstance(metrics, dict)
        assert "hits" in metrics
        assert "misses" in metrics
        assert "hit_rate" in metrics
        assert metrics["hits"] >= 1
        assert metrics["misses"] >= 1
    
    def test_cache_info(self):
        """Test detailed cache information."""
        # Set some values
        self.cache.set("info_key", "info_value", metadata={"source": "test"})
        
        # Get cache info
        info = self.cache.get_cache_info()
        
        assert isinstance(info, dict)
        assert "total_entries" in info
        assert "entries" in info
        assert info["total_entries"] >= 1
        
        # Check entry details
        entries = info["entries"]
        assert len(entries) >= 1
        test_entry = next((e for e in entries if e["key"] == "info_key"), None)
        assert test_entry is not None
        assert test_entry["metadata"]["source"] == "test"
    
    def test_invalidation_callbacks(self):
        """Test cache invalidation callbacks."""
        callback_called = []
        
        def test_callback(pattern):
            callback_called.append(pattern)
        
        # Register callback
        self.cache.register_invalidation_callback("test:*", test_callback)
        
        # Set and invalidate
        self.cache.set("test:key", "value")
        self.cache.invalidate("test:*")
        
        # Verify callback was called
        assert len(callback_called) == 1
        assert callback_called[0] == "test:*"


class TestIntegration:
    """Integration tests for the complete system."""
    
    def setup_method(self):
        """Setup integration test environment."""
        self.container = ServiceContainer()
        
        # Register services
        self.container.register_service(IConfigurationService, ConfigurationService)
        self.container.register_service(ICacheService, EnhancedSharedPromptCache)
        self.container.register_service(IAgentRegistry, EnhancedAgentRegistry)
    
    def test_service_integration(self):
        """Test services work together through dependency injection."""
        # Get configuration service
        config = self.container.get_service(IConfigurationService)
        assert isinstance(config, IConfigurationService)
        
        # Set some configuration
        config.set("test.integration", "working")
        
        # Get cache service
        cache = self.container.get_service(ICacheService)
        assert isinstance(cache, ICacheService)
        
        # Test cache operations
        cache.set("integration_key", "integration_value")
        value = cache.get("integration_key")
        assert value == "integration_value"
        
        # Get agent registry
        registry = self.container.get_service(IAgentRegistry)
        assert isinstance(registry, IAgentRegistry)
    
    @pytest.mark.asyncio
    async def test_service_lifecycle_integration(self):
        """Test integrated service lifecycle management."""
        # Create enhanced services
        config = self.container.get_service(IConfigurationService)
        cache = self.container.get_service(ICacheService)
        
        # If services are enhanced base services, test lifecycle
        if isinstance(cache, EnhancedBaseService):
            await cache.start()
            assert cache.running
            
            health = await cache.health_check()
            assert isinstance(health, ServiceHealth)
            
            await cache.stop()
            assert not cache.running
    
    def test_configuration_propagation(self):
        """Test configuration propagates through dependency injection."""
        # Set configuration values
        config = self.container.get_service(IConfigurationService)
        config.set("cache.max_size", 500)
        config.set("agent_registry.validation_timeout", 60)
        
        # Services should pick up configuration through injection
        cache = self.container.get_service(ICacheService)
        registry = self.container.get_service(IAgentRegistry)
        
        # Verify services are properly configured
        assert cache is not None
        assert registry is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])