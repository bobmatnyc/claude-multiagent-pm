"""
Unified Core Service - Central coordination hub for core framework services

This module provides unified access to core framework services including:
- Agent Registry
- Health Monitoring
- Service Management
- Configuration Management
- Performance Monitoring

Created: 2025-07-16 (Emergency restoration)
Purpose: Restore missing claude_pm.core.unified_core_service import
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from claude_pm.core.service_registry import ServiceRegistry
from claude_pm.core.config_service import ConfigurationService
from claude_pm.services.agent_registry import AgentRegistry
from claude_pm.services.health_monitor import HealthMonitorService
from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class UnifiedCoreService:
    """
    Unified Core Service - Central coordination hub for framework services
    
    Features:
    - Service lifecycle management
    - Agent registry coordination
    - Health monitoring
    - Performance tracking
    - Configuration management
    """
    
    def __init__(self) -> None:
        """Initialize unified core service"""
        self.service_registry = ServiceRegistry()
        self.config_service = ConfigurationService()
        self.cache_service = SharedPromptCache()
        self.agent_registry = AgentRegistry(cache_service=self.cache_service)
        self.health_monitor = HealthMonitorService()
        self.performance_monitor = PerformanceMonitor()
        self._initialized: bool = False
        self._services: Dict[str, Any] = {}
    
    async def initialize(self) -> bool:
        """
        Initialize all core services
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing unified core service...")
            
            # Initialize services in dependency order
            await self.config_service.initialize()
            await self.cache_service._initialize()
            await self.health_monitor._initialize()
            await self.performance_monitor._initialize()
            
            # Register core services
            self._services = {
                'config': self.config_service,
                'cache': self.cache_service,
                'agent_registry': self.agent_registry,
                'health_monitor': self.health_monitor,
                'performance_monitor': self.performance_monitor
            }
            
            # Discover agents
            self.agent_registry.discover_agents()
            
            # Start health monitoring
            # await self.health_monitor.start_monitoring()  # TODO: Fix method name
            
            self._initialized = True
            logger.info("Unified core service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize unified core service: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown all core services"""
        try:
            logger.info("Shutting down unified core service...")
            
            # Stop monitoring
            # await self.health_monitor.stop_monitoring()  # TODO: Fix method name
            
            # Shutdown services in reverse order
            for service_name, service in reversed(self._services.items()):
                try:
                    if hasattr(service, 'shutdown'):
                        await service.shutdown()
                    logger.debug(f"Service {service_name} shutdown complete")
                except Exception as e:
                    logger.warning(f"Error shutting down {service_name}: {e}")
            
            self._initialized = False
            logger.info("Unified core service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during unified core service shutdown: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            Dictionary containing system status information
        """
        if not self._initialized:
            return {'status': 'not_initialized', 'services': {}}
        
        try:
            status: Dict[str, Any] = {
                'status': 'operational',
                'initialized': self._initialized,
                'services': {},
                'agent_registry': {},
                'health': {},
                'performance': {}
            }
            
            # Service status
            for service_name, service in self._services.items():
                try:
                    if hasattr(service, 'get_status'):
                        status['services'][service_name] = await service.get_status()
                    else:
                        status['services'][service_name] = 'operational'
                except Exception as e:
                    status['services'][service_name] = f'error: {e}'
            
            # Agent registry stats
            try:
                status['agent_registry'] = self.agent_registry.get_registry_stats()
            except Exception as e:
                status['agent_registry'] = {'error': str(e)}
            
            # Health status
            try:
                status['health'] = await self.health_monitor.get_health_status()
            except Exception as e:
                status['health'] = {'error': str(e)}
            
            # Performance metrics
            try:
                status['performance'] = await self.performance_monitor.get_performance_report()
            except Exception as e:
                status['performance'] = {'error': str(e)}
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def validate_core_system(self) -> Dict[str, Any]:
        """
        Validate core system functionality
        
        Returns:
            Validation results
        """
        validation_results: Dict[str, Any] = {
            'overall_status': 'unknown',
            'service_validation': {},
            'agent_discovery': {},
            'health_check': {},
            'performance_check': {},
            'errors': []
        }
        
        try:
            # Validate services
            for service_name, service in self._services.items():
                try:
                    if hasattr(service, 'validate'):
                        validation_results['service_validation'][service_name] = await service.validate()
                    else:
                        validation_results['service_validation'][service_name] = 'no_validation_method'
                except Exception as e:
                    validation_results['service_validation'][service_name] = f'error: {e}'
                    validation_results['errors'].append(f"Service {service_name} validation failed: {e}")
            
            # Validate agent discovery
            try:
                agents = self.agent_registry.discover_agents(force_refresh=True)
                validation_results['agent_discovery'] = {
                    'discovered_agents': len(agents),
                    'validated_agents': len([a for a in agents.values() if a.validated]),
                    'agent_types': len(self.agent_registry.get_agent_types()),
                    'status': 'success'
                }
            except Exception as e:
                validation_results['agent_discovery'] = {'status': 'error', 'error': str(e)}
                validation_results['errors'].append(f"Agent discovery validation failed: {e}")
            
            # Health check validation
            try:
                health_status = await self.health_monitor.get_health_status()
                validation_results['health_check'] = health_status
            except Exception as e:
                validation_results['health_check'] = {'status': 'error', 'error': str(e)}
                validation_results['errors'].append(f"Health check validation failed: {e}")
            
            # Performance check
            try:
                perf_metrics = await self.performance_monitor.get_performance_report()
                validation_results['performance_check'] = {
                    'metrics_available': len(perf_metrics) > 0,
                    'status': 'success'
                }
            except Exception as e:
                validation_results['performance_check'] = {'status': 'error', 'error': str(e)}
                validation_results['errors'].append(f"Performance check validation failed: {e}")
            
            # Determine overall status
            if not validation_results['errors']:
                validation_results['overall_status'] = 'valid'
            elif len(validation_results['errors']) < 3:
                validation_results['overall_status'] = 'warning'
            else:
                validation_results['overall_status'] = 'error'
            
            return validation_results
            
        except Exception as e:
            validation_results['overall_status'] = 'error'
            validation_results['errors'].append(f"Core system validation failed: {e}")
            return validation_results
    
    async def get_agent_registry(self) -> AgentRegistry:
        """Get agent registry instance"""
        if not self._initialized:
            await self.initialize()
        return self.agent_registry
    
    async def get_health_monitor(self) -> HealthMonitorService:
        """Get health monitor instance"""
        if not self._initialized:
            await self.initialize()
        return self.health_monitor
    
    async def get_performance_monitor(self) -> PerformanceMonitor:
        """Get performance monitor instance"""
        if not self._initialized:
            await self.initialize()
        return self.performance_monitor
    
    async def get_cache_service(self) -> SharedPromptCache:
        """Get cache service instance"""
        if not self._initialized:
            await self.initialize()
        return self.cache_service
    
    async def get_config_service(self) -> ConfigurationService:
        """Get config service instance"""
        if not self._initialized:
            await self.initialize()
        return self.config_service
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

# Global instance for singleton access
_unified_core_service = None

async def get_unified_core_service() -> UnifiedCoreService:
    """
    Get or create global unified core service instance
    
    Returns:
        UnifiedCoreService instance
    """
    global _unified_core_service
    if _unified_core_service is None:
        _unified_core_service = UnifiedCoreService()
        await _unified_core_service.initialize()
    return _unified_core_service

def unified_core_service() -> UnifiedCoreService:
    """
    Synchronous access to unified core service (creates uninitialized instance)
    
    Returns:
        UnifiedCoreService instance (may need async initialization)
    """
    global _unified_core_service
    if _unified_core_service is None:
        _unified_core_service = UnifiedCoreService()
    return _unified_core_service

async def validate_core_system() -> Dict[str, Any]:
    """
    Convenience function for core system validation
    
    Returns:
        Validation results
    """
    service = await get_unified_core_service()
    return await service.validate_core_system()

async def initialize_core_services() -> bool:
    """
    Initialize all core services
    
    Returns:
        True if successful
    """
    service = await get_unified_core_service()
    return service.is_initialized

# Export key functions and classes
__all__ = [
    'UnifiedCoreService',
    'get_unified_core_service', 
    'unified_core_service',
    'validate_core_system',
    'initialize_core_services'
]