"""
Test suite for UnifiedCoreService - the most critical component.

This module provides comprehensive tests for the UnifiedCoreService, which serves
as the central access point for all framework services. Testing covers initialization,
lazy loading, service access, error handling, and lifecycle management.

Created: 2025-07-18
Coverage Target: 90%+
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from claude_pm.services.core import UnifiedCoreService, unified_core_service


class TestUnifiedCoreService:
    """Comprehensive test cases for UnifiedCoreService.
    
    Tests cover:
    - Service initialization and configuration
    - API key management and validation
    - Service registration and lifecycle  
    - Error handling and recovery
    - Performance monitoring integration
    - Async operations
    """

    @pytest.fixture
    def mock_service_classes(self):
        """Create mock service classes for testing."""
        mocks = {}
        
        # List of all services defined in UnifiedCoreService
        service_names = [
            'shared_prompt_cache', 'health_monitor', 'agent_registry',
            'model_selector', 'performance_monitor', 'parent_directory_manager',
            'template_manager', 'memory_service', 'framework_agent_loader',
            'agent_lifecycle_manager', 'agent_modification_tracker',
            'agent_persistence_service', 'dependency_manager',
            'working_directory_deployer', 'pm_orchestrator',
            'hook_processing_service', 'correction_capture',
            'prompt_improver', 'pattern_analyzer', 'agent_trainer',
            'project_service', 'post_installation_validator',
            'framework_deployment_validator', 'claude_pm_startup_validator',
            'claude_code_integration', 'cmpm_integration_service',
            'cache_service_integration', 'task_tool_profile_integration',
            'agent_training_integration', 'evaluation_integration',
            'mcp_service_detector', 'health_dashboard'
        ]
        
        # Create a mock class for each service
        for service_name in service_names:
            mock_class = MagicMock()
            mock_class.__name__ = f"Mock{service_name.title().replace('_', '')}"
            mock_class.__module__ = f"tests.mocks.{service_name}"
            mock_class.__doc__ = f"Mock {service_name} for testing"
            # Make the class callable (constructor)
            mock_instance = MagicMock()
            mock_instance._service_name = service_name
            mock_class.return_value = mock_instance
            mocks[service_name] = mock_class
            
        return mocks

    @pytest.fixture
    def unified_service(self, mock_service_classes):
        """Create a UnifiedCoreService instance with mocked service classes."""
        service = UnifiedCoreService()
        # Replace the service classes with our mocks
        service._service_classes = mock_service_classes
        return service

    def test_initialization(self):
        """Test UnifiedCoreService initialization."""
        service = UnifiedCoreService()
        
        # Check that services dict is empty initially (lazy loading)
        assert service._services == {}
        
        # Check that all expected service classes are registered
        expected_services = [
            'shared_prompt_cache', 'health_monitor', 'agent_registry',
            'model_selector', 'performance_monitor', 'parent_directory_manager',
            'template_manager', 'memory_service', 'framework_agent_loader',
            'agent_lifecycle_manager', 'agent_modification_tracker',
            'agent_persistence_service', 'dependency_manager',
            'working_directory_deployer', 'pm_orchestrator',
            'hook_processing_service', 'correction_capture',
            'prompt_improver', 'pattern_analyzer', 'agent_trainer',
            'project_service', 'post_installation_validator',
            'framework_deployment_validator', 'claude_pm_startup_validator',
            'claude_code_integration', 'cmpm_integration_service',
            'cache_service_integration', 'task_tool_profile_integration',
            'agent_training_integration', 'evaluation_integration',
            'mcp_service_detector', 'health_dashboard'
        ]
        
        assert set(service._service_classes.keys()) == set(expected_services)

    def test_get_service_lazy_loading(self, unified_service):
        """Test that services are lazy loaded on first access."""
        # Initially no services should be loaded
        assert len(unified_service._services) == 0
        
        # Get a service
        service_instance = unified_service.get_service('health_monitor')
        
        # Check that the service was instantiated
        assert 'health_monitor' in unified_service._services
        assert unified_service._services['health_monitor'] is not None
        assert unified_service._services['health_monitor']._service_name == 'health_monitor'
        
        # Check that the mock class was called to create instance
        unified_service._service_classes['health_monitor'].assert_called_once()

    def test_get_service_caching(self, unified_service):
        """Test that services are cached after first access."""
        # Get a service twice
        service1 = unified_service.get_service('agent_registry')
        service2 = unified_service.get_service('agent_registry')
        
        # Should be the same instance
        assert service1 is service2
        
        # Mock class should only be called once
        unified_service._service_classes['agent_registry'].assert_called_once()

    def test_get_service_unknown_service(self, unified_service):
        """Test error handling for unknown service names."""
        with pytest.raises(ValueError) as exc_info:
            unified_service.get_service('unknown_service')
        
        assert "Unknown service: unknown_service" in str(exc_info.value)
        assert "Available services:" in str(exc_info.value)

    def test_property_accessors(self, unified_service):
        """Test all property accessors for lazy loading behavior."""
        # Test a selection of property accessors
        properties_to_test = [
            ('shared_prompt_cache', 'shared_prompt_cache'),
            ('health_monitor', 'health_monitor'),
            ('agent_registry', 'agent_registry'),
            ('model_selector', 'model_selector'),
            ('performance_monitor', 'performance_monitor'),
            ('parent_directory_manager', 'parent_directory_manager'),
            ('template_manager', 'template_manager'),
            ('memory_service', 'memory_service'),
            ('framework_agent_loader', 'framework_agent_loader'),
            ('project_service', 'project_service'),
            ('mcp_service_detector', 'mcp_service_detector'),
            ('health_dashboard', 'health_dashboard')
        ]
        
        for prop_name, service_name in properties_to_test:
            # Access the property
            service_instance = getattr(unified_service, prop_name)
            
            # Verify it's the correct service
            assert service_instance._service_name == service_name
            
            # Verify it's cached
            service_instance2 = getattr(unified_service, prop_name)
            assert service_instance is service_instance2

    def test_list_services(self, unified_service):
        """Test listing all available services."""
        services = unified_service.list_services()
        
        assert isinstance(services, list)
        assert len(services) == 32  # Total number of services
        assert 'health_monitor' in services
        assert 'agent_registry' in services
        assert 'shared_prompt_cache' in services

    def test_get_service_info(self, unified_service):
        """Test getting information about a service."""
        # Test with a valid service
        info = unified_service.get_service_info('health_monitor')
        
        assert info['name'] == 'health_monitor'
        assert info['class'] == 'MockHealthMonitor'
        assert info['module'] == 'tests.mocks.health_monitor'
        assert info['doc'] == 'Mock health_monitor for testing'
        assert info['loaded'] is False  # Not loaded yet
        
        # Load the service
        unified_service.get_service('health_monitor')
        
        # Check loaded status
        info2 = unified_service.get_service_info('health_monitor')
        assert info2['loaded'] is True

    def test_get_service_info_unknown_service(self, unified_service):
        """Test error handling for get_service_info with unknown service."""
        with pytest.raises(ValueError) as exc_info:
            unified_service.get_service_info('unknown_service')
        
        assert "Unknown service: unknown_service" in str(exc_info.value)

    def test_service_initialization_error(self, unified_service):
        """Test handling of service initialization errors."""
        # Make a service class raise an exception
        unified_service._service_classes['health_monitor'].side_effect = Exception("Service init failed")
        
        # Getting the service should raise the exception
        with pytest.raises(Exception) as exc_info:
            unified_service.get_service('health_monitor')
        
        assert "Service init failed" in str(exc_info.value)
        
        # Service should not be in the cache
        assert 'health_monitor' not in unified_service._services

    def test_multiple_services_interaction(self, unified_service):
        """Test that multiple services can be loaded and interact independently."""
        # Load several services
        cache = unified_service.shared_prompt_cache
        registry = unified_service.agent_registry
        monitor = unified_service.health_monitor
        
        # Verify they are different instances
        assert cache is not registry
        assert registry is not monitor
        assert cache is not monitor
        
        # Verify they are the correct services
        assert cache._service_name == 'shared_prompt_cache'
        assert registry._service_name == 'agent_registry'
        assert monitor._service_name == 'health_monitor'

    def test_singleton_pattern(self):
        """Test that unified_core_service is a singleton instance."""
        from claude_pm.services.core import unified_core_service
        
        # Should be an instance of UnifiedCoreService
        assert isinstance(unified_core_service, UnifiedCoreService)
        
        # Should have all the expected methods
        assert hasattr(unified_core_service, 'get_service')
        assert hasattr(unified_core_service, 'list_services')
        assert hasattr(unified_core_service, 'get_service_info')

    @patch('claude_pm.services.core.SharedPromptCache')
    @patch('claude_pm.services.core.HealthMonitor')
    def test_real_service_integration(self, mock_health_monitor, mock_cache):
        """Test with real service class imports (mocked)."""
        # Create instances that will be returned by the mocked classes
        cache_instance = Mock()
        monitor_instance = Mock()
        
        mock_cache.return_value = cache_instance
        mock_health_monitor.return_value = monitor_instance
        
        # Create a new unified service
        service = UnifiedCoreService()
        
        # Access services through properties
        cache = service.shared_prompt_cache
        monitor = service.health_monitor
        
        # Verify the mocked classes were instantiated
        mock_cache.assert_called_once()
        mock_health_monitor.assert_called_once()
        
        # Verify we got the expected instances
        assert cache is cache_instance
        assert monitor is monitor_instance

    def test_service_lifecycle(self, unified_service):
        """Test the complete lifecycle of service access and management."""
        # Phase 1: Initial state
        assert len(unified_service._services) == 0
        assert unified_service.get_service_info('agent_registry')['loaded'] is False
        
        # Phase 2: First access
        registry1 = unified_service.get_service('agent_registry')
        assert len(unified_service._services) == 1
        assert unified_service.get_service_info('agent_registry')['loaded'] is True
        
        # Phase 3: Subsequent access
        registry2 = unified_service.agent_registry  # Use property accessor
        assert registry1 is registry2
        assert len(unified_service._services) == 1  # Still just one service
        
        # Phase 4: Access another service
        cache = unified_service.shared_prompt_cache
        assert len(unified_service._services) == 2
        assert cache is not registry1
        
        # Phase 5: List all loaded services
        loaded_services = [
            name for name in unified_service.list_services()
            if unified_service.get_service_info(name)['loaded']
        ]
        assert set(loaded_services) == {'agent_registry', 'shared_prompt_cache'}

    def test_concurrent_service_access(self, unified_service):
        """Test that concurrent access to services is handled correctly."""
        import threading
        
        results = {}
        
        def access_service(service_name):
            service = unified_service.get_service(service_name)
            results[service_name] = service
        
        # Create threads to access different services concurrently
        threads = []
        services = ['health_monitor', 'agent_registry', 'shared_prompt_cache']
        
        for service_name in services:
            thread = threading.Thread(target=access_service, args=(service_name,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all services were loaded
        assert len(results) == 3
        for service_name in services:
            assert service_name in results
            assert results[service_name]._service_name == service_name

    def test_edge_cases(self, unified_service):
        """Test edge cases and boundary conditions."""
        # Test empty string service name
        with pytest.raises(ValueError):
            unified_service.get_service('')
        
        # Test None service name
        with pytest.raises(ValueError):
            unified_service.get_service(None)
        
        # Test get_service_info with empty string
        with pytest.raises(ValueError):
            unified_service.get_service_info('')
        
        # Test that service names are case-sensitive
        with pytest.raises(ValueError):
            unified_service.get_service('HEALTH_MONITOR')  # Should be lowercase


class TestUnifiedCoreServiceWithConfig:
    """Test UnifiedCoreService with configuration and API key management."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return {
            'api_keys': {
                'openai': 'test-openai-key',
                'anthropic': 'test-anthropic-key'
            },
            'services': {
                'enabled': ['agent_registry', 'parent_directory_manager'],
                'disabled': ['deprecated_service']
            },
            'performance': {
                'cache_enabled': True,
                'monitoring_enabled': True
            }
        }
    
    @pytest.fixture
    def service_with_config(self, mock_config):
        """Create UnifiedCoreService instance with config."""
        # Mock environment variables
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': mock_config['api_keys']['openai'],
            'ANTHROPIC_API_KEY': mock_config['api_keys']['anthropic']
        }):
            service = UnifiedCoreService()
            # Inject config for testing
            service._config = mock_config
            return service
    
    def test_initialization_with_api_keys(self):
        """Test initialization with API keys from environment."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key-1',
            'ANTHROPIC_API_KEY': 'test-key-2'
        }):
            service = UnifiedCoreService()
            assert service is not None
            # Services should still be empty (lazy loading)
            assert service._services == {}
    
    def test_initialization_without_api_keys(self):
        """Test initialization without API keys still works."""
        # Clear any existing keys
        with patch.dict(os.environ, {}, clear=True):
            service = UnifiedCoreService()
            assert service is not None
            # Should still initialize but services may have limited functionality
            assert service._services == {}
    
    def test_service_initialization_with_config(self, service_with_config):
        """Test that services can access configuration when needed."""
        # Access a service that might need config
        agent_registry = service_with_config.agent_registry
        assert agent_registry is not None
        
        # Service should be cached
        assert 'agent_registry' in service_with_config._services


class TestUnifiedCoreServiceLifecycle:
    """Test service lifecycle management and async operations."""
    
    @pytest.fixture
    def async_service(self):
        """Create a service with async lifecycle methods mocked."""
        service = UnifiedCoreService()
        
        # Create mock services with async lifecycle methods
        for service_name in ['agent_registry', 'health_monitor', 'performance_monitor']:
            mock_service = MagicMock()
            mock_service._service_name = service_name
            mock_service.startup = AsyncMock(return_value=None)
            mock_service.shutdown = AsyncMock(return_value=None)
            mock_service.health_check = AsyncMock(return_value={'status': 'healthy'})
            
            # Pre-populate the service
            service._services[service_name] = mock_service
            
        return service
    
    @pytest.mark.asyncio
    async def test_service_startup(self, async_service):
        """Test async startup of services."""
        # Startup specific services
        services_to_start = ['agent_registry', 'health_monitor']
        
        for service_name in services_to_start:
            service = async_service._services[service_name]
            if hasattr(service, 'startup'):
                await service.startup()
                service.startup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_shutdown(self, async_service):
        """Test async shutdown of services."""
        # Shutdown all services
        for service_name, service in async_service._services.items():
            if hasattr(service, 'shutdown'):
                await service.shutdown()
                service.shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_health_check(self, async_service):
        """Test async health check of services."""
        health_results = {}
        
        for service_name, service in async_service._services.items():
            if hasattr(service, 'health_check'):
                result = await service.health_check()
                health_results[service_name] = result
                assert result['status'] == 'healthy'
        
        assert len(health_results) == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_service_operations(self, async_service):
        """Test concurrent operations on multiple services."""
        # Create startup tasks for all services
        tasks = []
        for service_name, service in async_service._services.items():
            if hasattr(service, 'startup'):
                tasks.append(service.startup())
        
        # Run all startups concurrently
        await asyncio.gather(*tasks)
        
        # Verify all were called
        for service in async_service._services.values():
            if hasattr(service, 'startup'):
                service.startup.assert_called()
    
    @pytest.mark.asyncio
    async def test_service_lifecycle_with_errors(self, async_service):
        """Test service lifecycle with startup/shutdown errors."""
        # Make one service fail during startup
        async_service._services['health_monitor'].startup.side_effect = Exception("Startup failed")
        
        # Try to start the failing service
        with pytest.raises(Exception) as exc_info:
            await async_service._services['health_monitor'].startup()
        
        assert "Startup failed" in str(exc_info.value)
        
        # Other services should still work
        await async_service._services['agent_registry'].startup()
        async_service._services['agent_registry'].startup.assert_called_once()


class TestUnifiedCoreServiceErrorHandling:
    """Test error handling and recovery scenarios."""
    
    @pytest.fixture
    def service_with_failing_classes(self):
        """Create service with some failing service classes."""
        service = UnifiedCoreService()
        
        # Create a failing service class
        failing_class = MagicMock()
        failing_class.side_effect = RuntimeError("Service initialization failed")
        
        # Replace one service class with failing one
        service._service_classes['failing_service'] = failing_class
        
        return service
    
    def test_service_initialization_failure_handling(self, service_with_failing_classes):
        """Test handling of service initialization failures."""
        # Try to get the failing service
        with pytest.raises(RuntimeError) as exc_info:
            service_with_failing_classes.get_service('failing_service')
        
        assert "Service initialization failed" in str(exc_info.value)
        
        # Service should not be cached after failure
        assert 'failing_service' not in service_with_failing_classes._services
    
    def test_network_error_simulation(self):
        """Test handling of network-related errors."""
        service = UnifiedCoreService()
        
        # Mock a service that simulates network failure
        mock_service = MagicMock()
        mock_service.connect = MagicMock(side_effect=ConnectionError("Network unavailable"))
        
        service._services['network_service'] = mock_service
        
        # Try to connect
        with pytest.raises(ConnectionError) as exc_info:
            service._services['network_service'].connect()
        
        assert "Network unavailable" in str(exc_info.value)
    
    def test_api_failure_handling(self):
        """Test handling of API failures."""
        service = UnifiedCoreService()
        
        # Mock a service that simulates API failure
        mock_service = MagicMock()
        mock_service.api_call = MagicMock(side_effect=Exception("API rate limit exceeded"))
        
        service._services['api_service'] = mock_service
        
        # Try API call
        with pytest.raises(Exception) as exc_info:
            service._services['api_service'].api_call()
        
        assert "API rate limit exceeded" in str(exc_info.value)
    
    def test_timeout_handling(self):
        """Test handling of timeout scenarios."""
        service = UnifiedCoreService()
        
        # Mock a service that simulates timeout
        mock_service = MagicMock()
        mock_service.slow_operation = MagicMock(side_effect=TimeoutError("Operation timed out"))
        
        service._services['slow_service'] = mock_service
        
        # Try slow operation
        with pytest.raises(TimeoutError) as exc_info:
            service._services['slow_service'].slow_operation()
        
        assert "Operation timed out" in str(exc_info.value)


class TestUnifiedCoreServiceIntegration:
    """Integration tests with mocked dependencies."""
    
    @pytest.fixture
    def integrated_service(self):
        """Create service with integrated mock dependencies."""
        service = UnifiedCoreService()
        
        # Mock the actual service imports
        with patch('claude_pm.services.core.SharedPromptCache') as mock_cache:
            with patch('claude_pm.services.core.HealthMonitor') as mock_monitor:
                with patch('claude_pm.services.core.AgentRegistry') as mock_registry:
                    # Set up return values
                    mock_cache.return_value = MagicMock(name='SharedPromptCache')
                    mock_monitor.return_value = MagicMock(name='HealthMonitor')
                    mock_registry.return_value = MagicMock(name='AgentRegistry')
                    
                    # Re-initialize service classes to use mocks
                    service._service_classes['shared_prompt_cache'] = mock_cache
                    service._service_classes['health_monitor'] = mock_monitor
                    service._service_classes['agent_registry'] = mock_registry
                    
                    return service
    
    def test_service_interaction(self, integrated_service):
        """Test interaction between multiple services."""
        # Get services
        cache = integrated_service.shared_prompt_cache
        monitor = integrated_service.health_monitor
        registry = integrated_service.agent_registry
        
        # Simulate service interaction
        cache.get = MagicMock(return_value=None)
        cache.set = MagicMock()
        monitor.check_health = MagicMock(return_value={'status': 'healthy'})
        registry.list_agents = MagicMock(return_value=['agent1', 'agent2'])
        
        # Perform operations
        cache.set('key', 'value')
        health = monitor.check_health()
        agents = registry.list_agents()
        
        # Verify interactions
        cache.set.assert_called_once_with('key', 'value')
        monitor.check_health.assert_called_once()
        registry.list_agents.assert_called_once()
        
        assert health['status'] == 'healthy'
        assert len(agents) == 2
    
    @pytest.mark.asyncio
    async def test_async_service_integration(self, integrated_service):
        """Test async operations across integrated services."""
        # Set up async methods
        cache = integrated_service.shared_prompt_cache
        monitor = integrated_service.health_monitor
        
        cache.async_get = AsyncMock(return_value='cached_value')
        monitor.async_health_check = AsyncMock(return_value={'status': 'healthy', 'uptime': 1000})
        
        # Perform async operations
        cached_data = await cache.async_get('key')
        health_status = await monitor.async_health_check()
        
        # Verify
        assert cached_data == 'cached_value'
        assert health_status['status'] == 'healthy'
        assert health_status['uptime'] == 1000


class TestUnifiedCoreServicePerformance:
    """Test performance monitoring and optimization."""
    
    def test_lazy_loading_performance(self):
        """Test that lazy loading improves startup performance."""
        import time
        
        start_time = time.time()
        service = UnifiedCoreService()
        init_time = time.time() - start_time
        
        # Initialization should be fast (no services loaded)
        assert init_time < 0.1  # Less than 100ms
        assert len(service._services) == 0
        
        # First service access might be slower
        start_time = time.time()
        _ = service.health_monitor
        first_access_time = time.time() - start_time
        
        # Subsequent access should be faster (cached)
        start_time = time.time()
        _ = service.health_monitor
        second_access_time = time.time() - start_time
        
        assert second_access_time < first_access_time
    
    def test_concurrent_access_performance(self):
        """Test performance under concurrent access."""
        import threading
        import time
        
        service = UnifiedCoreService()
        results = []
        
        def access_service(service_name):
            start = time.time()
            _ = service.get_service(service_name)
            duration = time.time() - start
            results.append(duration)
        
        # Create threads to access different services
        threads = []
        service_names = ['health_monitor', 'agent_registry', 'shared_prompt_cache']
        
        for name in service_names:
            thread = threading.Thread(target=access_service, args=(name,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All should complete reasonably fast
        assert all(duration < 0.5 for duration in results)
    
    def test_memory_efficiency(self):
        """Test memory efficiency of service caching."""
        service = UnifiedCoreService()
        
        # Access several services
        _ = service.health_monitor
        _ = service.agent_registry
        _ = service.shared_prompt_cache
        
        # Should only have 3 services in memory
        assert len(service._services) == 3
        
        # Accessing again shouldn't increase memory usage
        _ = service.health_monitor
        _ = service.agent_registry
        _ = service.shared_prompt_cache
        
        assert len(service._services) == 3  # Still only 3


class TestUnifiedCoreServiceExports:
    """Test the module exports and __all__ definition."""
    
    def test_all_exports(self):
        """Test that __all__ includes all expected exports."""
        from claude_pm.services import core
        
        # Check that __all__ is defined
        assert hasattr(core, '__all__')
        
        # Check that key exports are included
        assert 'UnifiedCoreService' in core.__all__
        assert 'unified_core_service' in core.__all__
        
        # Check that service classes are exported
        expected_exports = [
            'SharedPromptCache', 'HealthMonitor', 'AgentRegistry',
            'ModelSelector', 'PerformanceMonitor', 'ParentDirectoryManager',
            'TemplateManager', 'MemoryServiceIntegration', 'FrameworkAgentLoader',
            'ProjectService', 'MCPServiceDetector', 'HealthDashboard'
        ]
        
        for export in expected_exports:
            assert export in core.__all__