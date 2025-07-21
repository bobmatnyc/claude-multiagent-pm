"""Health monitoring system for agent registry."""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors health and status of the agent registry system."""
    
    def __init__(self, discovery_paths: List[Path], cache_service, model_selector):
        """Initialize health monitor with dependencies."""
        self.discovery_paths = discovery_paths
        self.cache_service = cache_service
        self.model_selector = model_selector
    
    def health_check(self, registry: Dict[str, Any], last_discovery_time: Optional[float]) -> Dict[str, Any]:
        """
        Perform a comprehensive health check on the AgentRegistry.
        
        Args:
            registry: Current agent registry
            last_discovery_time: Last discovery timestamp
            
        Returns:
            Dictionary with health status information
        """
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check 1: Discovery paths accessibility
            health_status['checks']['discovery_paths'] = self._check_discovery_paths()
            
            if health_status['checks']['discovery_paths']['accessible'] == 0:
                health_status['errors'].append('No accessible discovery paths found')
                health_status['status'] = 'critical'
            elif health_status['checks']['discovery_paths']['accessible'] < len(self.discovery_paths):
                health_status['warnings'].append(
                    f"Only {health_status['checks']['discovery_paths']['accessible']}/{len(self.discovery_paths)} discovery paths are accessible"
                )
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'degraded'
            
            # Check 2: Cache service availability
            health_status['checks']['cache_service'] = self._check_cache_service()
            
            if not health_status['checks']['cache_service'].get('functional'):
                health_status['warnings'].append('Cache service is not functioning properly')
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'degraded'
            
            # Check 3: Model selector availability
            health_status['checks']['model_selector'] = self._check_model_selector()
            
            if not health_status['checks']['model_selector'].get('available'):
                health_status['warnings'].append('Model selector not available')
            
            # Check 4: Registry state
            health_status['checks']['registry'] = self._check_registry_state(registry, last_discovery_time)
            
            # Check 5: Agent type coverage
            if registry:
                health_status['checks']['agent_coverage'] = self._check_agent_coverage(registry)
                
                missing_core = health_status['checks']['agent_coverage'].get('missing_core_types', [])
                if missing_core:
                    health_status['warnings'].append(f'Missing core agent types: {", ".join(sorted(missing_core))}')
            else:
                health_status['checks']['agent_coverage'] = {
                    'message': 'No agents discovered yet'
                }
            
            # Check 6: System resources
            health_status['checks']['system_resources'] = self._check_system_resources()
            
            # Overall health assessment
            if health_status['errors']:
                health_status['status'] = 'critical'
            elif len(health_status['warnings']) > 3:
                health_status['status'] = 'degraded'
            
            health_status['summary'] = {
                'status': health_status['status'],
                'error_count': len(health_status['errors']),
                'warning_count': len(health_status['warnings']),
                'checks_passed': sum(1 for check in health_status['checks'].values() 
                                   if isinstance(check, dict) and check.get('available', True))
            }
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['errors'].append(f'Health check failed: {str(e)}')
            health_status['exception'] = str(e)
        
        return health_status
    
    def _check_discovery_paths(self) -> Dict[str, Any]:
        """Check discovery paths accessibility."""
        discovery_paths_status = []
        accessible_paths = 0
        
        for path in self.discovery_paths:
            path_status = {
                'path': str(path),
                'exists': path.exists(),
                'readable': path.exists() and os.access(path, os.R_OK)
            }
            discovery_paths_status.append(path_status)
            if path_status['readable']:
                accessible_paths += 1
        
        return {
            'total': len(self.discovery_paths),
            'accessible': accessible_paths,
            'details': discovery_paths_status
        }
    
    def _check_cache_service(self) -> Dict[str, Any]:
        """Check cache service availability."""
        try:
            cache_test_key = 'agent_registry_health_check_test'
            self.cache_service.set(cache_test_key, {'test': True}, ttl=1)
            cache_result = self.cache_service.get(cache_test_key)
            cache_healthy = cache_result is not None and cache_result.get('test') == True
            
            return {
                'available': True,
                'functional': cache_healthy,
                'type': type(self.cache_service).__name__
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def _check_model_selector(self) -> Dict[str, Any]:
        """Check model selector availability."""
        try:
            model_selector_status = self.model_selector is not None
            return {
                'available': model_selector_status,
                'type': type(self.model_selector).__name__ if model_selector_status else None
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def _check_registry_state(self, registry: Dict[str, Any], last_discovery_time: Optional[float]) -> Dict[str, Any]:
        """Check registry state."""
        return {
            'loaded': bool(registry),
            'agent_count': len(registry),
            'last_discovery': last_discovery_time,
            'cache_valid': self._is_discovery_cache_valid(last_discovery_time) if last_discovery_time else False
        }
    
    def _check_agent_coverage(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        """Check agent type coverage."""
        from .classification import AgentClassifier
        classifier = AgentClassifier()
        
        discovered_types = set(metadata.type for metadata in registry.values())
        core_coverage = len(classifier.core_agent_types.intersection(discovered_types))
        
        coverage_info = {
            'core_types_discovered': core_coverage,
            'core_types_total': len(classifier.core_agent_types),
            'specialized_types_discovered': len(discovered_types.intersection(classifier.specialized_agent_types)),
            'total_types_discovered': len(discovered_types)
        }
        
        if core_coverage < len(classifier.core_agent_types):
            missing_core = classifier.core_agent_types - discovered_types
            coverage_info['missing_core_types'] = list(missing_core)
        
        return coverage_info
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'memory_usage_mb': memory_info.rss / 1024 / 1024,
                'available': True
            }
        except ImportError:
            return {
                'available': False,
                'note': 'psutil not installed'
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def _is_discovery_cache_valid(self, last_discovery_time: float, ttl: int = 300) -> bool:
        """Check if discovery cache is still valid."""
        return (time.time() - last_discovery_time) < ttl