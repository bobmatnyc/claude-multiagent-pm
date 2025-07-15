#!/usr/bin/env python3
"""
Framework Version 014 Compliance Validation
===========================================

Comprehensive validation script to ensure all implemented components
are compliant with Framework Version 014 requirements.

Validation Areas:
- AgentProfileLoader implementation
- Improved prompt integration
- Task Tool subprocess enhancement
- SharedPromptCache integration
- Training system connectivity
- Performance optimization compliance

Framework Version: 014
Validation Script: 2025-07-15
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Framework014Validator:
    """Framework Version 014 compliance validator."""
    
    def __init__(self):
        """Initialize the validator."""
        self.project_root = project_root
        self.validation_results = {
            'overall_compliance': False,
            'validation_timestamp': datetime.now().isoformat(),
            'framework_version': '014',
            'components': {},
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Framework 014 requirements
        self.requirements = {
            'agent_profile_loader': {
                'required_classes': ['AgentProfileLoader', 'AgentProfile', 'ImprovedPrompt'],
                'required_methods': [
                    'load_agent_profile',
                    'build_enhanced_task_prompt',
                    'save_improved_prompt',
                    'deploy_improved_prompt',
                    'list_available_agents'
                ],
                'required_features': [
                    'three_tier_hierarchy',
                    'improved_prompt_integration',
                    'training_system_connectivity',
                    'shared_cache_integration',
                    'performance_optimization'
                ]
            },
            'task_tool_integration': {
                'required_classes': ['TaskToolProfileIntegration', 'TaskToolRequest', 'TaskToolResponse'],
                'required_methods': [
                    'create_enhanced_subprocess',
                    'batch_create_subprocesses',
                    'get_integration_status',
                    'get_request_history'
                ],
                'required_features': [
                    'enhanced_prompt_generation',
                    'cache_optimization',
                    'performance_metrics',
                    'training_integration'
                ]
            },
            'shared_prompt_cache': {
                'required_classes': ['SharedPromptCache', 'CacheEntry', 'CacheMetrics'],
                'required_methods': [
                    'get_instance',
                    'set',
                    'get',
                    'invalidate',
                    'get_metrics'
                ],
                'required_features': [
                    'singleton_pattern',
                    'lru_eviction',
                    'ttl_support',
                    'performance_metrics'
                ]
            },
            'agent_registry': {
                'required_classes': ['AgentRegistry', 'AgentMetadata'],
                'required_methods': [
                    'discover_agents',
                    'list_agents',
                    'get_agent',
                    'get_registry_stats'
                ],
                'required_features': [
                    'two_tier_hierarchy',
                    'agent_validation',
                    'performance_optimization',
                    'specialized_agent_support'
                ]
            }
        }
        
        logger.info("Framework 014 Validator initialized")
    
    async def validate_all_components(self) -> Dict[str, Any]:
        """Validate all framework components."""
        logger.info("Starting Framework 014 compliance validation...")
        
        # Validate each component
        for component_name, requirements in self.requirements.items():
            logger.info(f"Validating {component_name}...")
            
            component_result = await self._validate_component(component_name, requirements)
            self.validation_results['components'][component_name] = component_result
            
            if not component_result['compliant']:
                self.validation_results['issues'].extend(component_result['issues'])
                self.validation_results['warnings'].extend(component_result['warnings'])
        
        # Validate integration between components
        integration_result = await self._validate_integration()
        self.validation_results['components']['integration'] = integration_result
        
        # Validate performance requirements
        performance_result = await self._validate_performance()
        self.validation_results['components']['performance'] = performance_result
        
        # Determine overall compliance
        component_compliance = [
            result['compliant'] for result in self.validation_results['components'].values()
        ]
        self.validation_results['overall_compliance'] = all(component_compliance)
        
        # Generate recommendations
        self._generate_recommendations()
        
        logger.info(f"Validation completed. Overall compliance: {self.validation_results['overall_compliance']}")
        return self.validation_results
    
    async def _validate_component(self, component_name: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a specific component."""
        result = {
            'compliant': True,
            'issues': [],
            'warnings': [],
            'features_validated': [],
            'module_found': False,
            'classes_found': [],
            'methods_found': []
        }
        
        try:
            # Import component module
            module_path = self._get_module_path(component_name)
            if not module_path or not module_path.exists():
                result['compliant'] = False
                result['issues'].append(f"Module not found: {component_name}")
                return result
            
            # Load module
            spec = importlib.util.spec_from_file_location(component_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result['module_found'] = True
            
            # Validate required classes
            for class_name in requirements['required_classes']:
                if hasattr(module, class_name):
                    result['classes_found'].append(class_name)
                    
                    # Validate class methods
                    cls = getattr(module, class_name)
                    for method_name in requirements['required_methods']:
                        if hasattr(cls, method_name):
                            result['methods_found'].append(f"{class_name}.{method_name}")
                        else:
                            result['warnings'].append(f"Method {method_name} not found in {class_name}")
                else:
                    result['issues'].append(f"Required class {class_name} not found")
                    result['compliant'] = False
            
            # Validate features
            feature_validation = await self._validate_component_features(
                component_name, 
                requirements['required_features'], 
                module
            )
            result['features_validated'] = feature_validation['validated']
            result['issues'].extend(feature_validation['issues'])
            result['warnings'].extend(feature_validation['warnings'])
            
            if feature_validation['issues']:
                result['compliant'] = False
            
        except Exception as e:
            result['compliant'] = False
            result['issues'].append(f"Error validating {component_name}: {str(e)}")
        
        return result
    
    def _get_module_path(self, component_name: str) -> Optional[Path]:
        """Get module path for component."""
        module_paths = {
            'agent_profile_loader': self.project_root / 'claude_pm' / 'services' / 'agent_profile_loader.py',
            'task_tool_integration': self.project_root / 'claude_pm' / 'services' / 'task_tool_profile_integration.py',
            'shared_prompt_cache': self.project_root / 'claude_pm' / 'services' / 'shared_prompt_cache.py',
            'agent_registry': self.project_root / 'claude_pm' / 'services' / 'agent_registry.py'
        }
        
        return module_paths.get(component_name)
    
    async def _validate_component_features(self, component_name: str, 
                                         required_features: List[str], 
                                         module: Any) -> Dict[str, Any]:
        """Validate component-specific features."""
        result = {
            'validated': [],
            'issues': [],
            'warnings': []
        }
        
        if component_name == 'agent_profile_loader':
            result = await self._validate_agent_profile_loader_features(required_features, module)
        elif component_name == 'task_tool_integration':
            result = await self._validate_task_tool_integration_features(required_features, module)
        elif component_name == 'shared_prompt_cache':
            result = await self._validate_shared_cache_features(required_features, module)
        elif component_name == 'agent_registry':
            result = await self._validate_agent_registry_features(required_features, module)
        
        return result
    
    async def _validate_agent_profile_loader_features(self, features: List[str], module: Any) -> Dict[str, Any]:
        """Validate AgentProfileLoader features."""
        result = {'validated': [], 'issues': [], 'warnings': []}
        
        for feature in features:
            if feature == 'three_tier_hierarchy':
                if hasattr(module, 'ProfileTier') and hasattr(module.ProfileTier, 'PROJECT'):
                    result['validated'].append(feature)
                else:
                    result['issues'].append("Three-tier hierarchy not properly implemented")
            
            elif feature == 'improved_prompt_integration':
                if hasattr(module, 'ImprovedPrompt'):
                    result['validated'].append(feature)
                else:
                    result['issues'].append("Improved prompt integration not implemented")
            
            elif feature == 'training_system_connectivity':
                if hasattr(module, 'AgentProfileLoader'):
                    loader_class = getattr(module, 'AgentProfileLoader')
                    if hasattr(loader_class, 'save_improved_prompt'):
                        result['validated'].append(feature)
                    else:
                        result['issues'].append("Training system connectivity not implemented")
            
            elif feature == 'shared_cache_integration':
                # Check if SharedPromptCache is imported and used
                if 'SharedPromptCache' in str(module):
                    result['validated'].append(feature)
                else:
                    result['warnings'].append("SharedPromptCache integration may not be implemented")
            
            elif feature == 'performance_optimization':
                if hasattr(module, 'AgentProfileLoader'):
                    loader_class = getattr(module, 'AgentProfileLoader')
                    if hasattr(loader_class, 'get_performance_metrics'):
                        result['validated'].append(feature)
                    else:
                        result['warnings'].append("Performance optimization not fully implemented")
        
        return result
    
    async def _validate_task_tool_integration_features(self, features: List[str], module: Any) -> Dict[str, Any]:
        """Validate TaskToolProfileIntegration features."""
        result = {'validated': [], 'issues': [], 'warnings': []}
        
        for feature in features:
            if feature == 'enhanced_prompt_generation':
                if hasattr(module, 'TaskToolProfileIntegration'):
                    integration_class = getattr(module, 'TaskToolProfileIntegration')
                    if hasattr(integration_class, 'create_enhanced_subprocess'):
                        result['validated'].append(feature)
                    else:
                        result['issues'].append("Enhanced prompt generation not implemented")
            
            elif feature == 'cache_optimization':
                if hasattr(module, 'TaskToolProfileIntegration'):
                    integration_class = getattr(module, 'TaskToolProfileIntegration')
                    if hasattr(integration_class, '_get_cached_prompt'):
                        result['validated'].append(feature)
                    else:
                        result['warnings'].append("Cache optimization not fully implemented")
            
            elif feature == 'performance_metrics':
                if hasattr(module, 'TaskToolProfileIntegration'):
                    integration_class = getattr(module, 'TaskToolProfileIntegration')
                    if hasattr(integration_class, 'get_integration_status'):
                        result['validated'].append(feature)
                    else:
                        result['issues'].append("Performance metrics not implemented")
            
            elif feature == 'training_integration':
                if hasattr(module, 'TaskToolProfileIntegration'):
                    integration_class = getattr(module, 'TaskToolProfileIntegration')
                    if hasattr(integration_class, '_integrate_with_training'):
                        result['validated'].append(feature)
                    else:
                        result['warnings'].append("Training integration not implemented")
        
        return result
    
    async def _validate_shared_cache_features(self, features: List[str], module: Any) -> Dict[str, Any]:
        """Validate SharedPromptCache features."""
        result = {'validated': [], 'issues': [], 'warnings': []}
        
        for feature in features:
            if feature == 'singleton_pattern':
                if hasattr(module, 'SharedPromptCache'):
                    cache_class = getattr(module, 'SharedPromptCache')
                    if hasattr(cache_class, 'get_instance'):
                        result['validated'].append(feature)
                    else:
                        result['issues'].append("Singleton pattern not implemented")
            
            elif feature == 'lru_eviction':
                if hasattr(module, 'SharedPromptCache'):
                    cache_class = getattr(module, 'SharedPromptCache')
                    if hasattr(cache_class, '_evict_lru_entry'):
                        result['validated'].append(feature)
                    else:
                        result['warnings'].append("LRU eviction not implemented")
            
            elif feature == 'ttl_support':
                if hasattr(module, 'CacheEntry'):
                    entry_class = getattr(module, 'CacheEntry')
                    if hasattr(entry_class, 'is_expired'):
                        result['validated'].append(feature)
                    else:
                        result['issues'].append("TTL support not implemented")
            
            elif feature == 'performance_metrics':
                if hasattr(module, 'SharedPromptCache'):
                    cache_class = getattr(module, 'SharedPromptCache')
                    if hasattr(cache_class, 'get_metrics'):
                        result['validated'].append(feature)
                    else:
                        result['issues'].append("Performance metrics not implemented")
        
        return result
    
    async def _validate_agent_registry_features(self, features: List[str], module: Any) -> Dict[str, Any]:
        """Validate AgentRegistry features."""
        result = {'validated': [], 'issues': [], 'warnings': []}
        
        for feature in features:
            if feature == 'two_tier_hierarchy':
                if hasattr(module, 'AgentRegistry'):
                    registry_class = getattr(module, 'AgentRegistry')
                    if hasattr(registry_class, '_initialize_discovery_paths'):
                        result['validated'].append(feature)
                    else:
                        result['issues'].append("Two-tier hierarchy not implemented")
            
            elif feature == 'agent_validation':
                if hasattr(module, 'AgentRegistry'):
                    registry_class = getattr(module, 'AgentRegistry')
                    if hasattr(registry_class, '_validate_agents'):
                        result['validated'].append(feature)
                    else:
                        result['issues'].append("Agent validation not implemented")
            
            elif feature == 'performance_optimization':
                if hasattr(module, 'AgentRegistry'):
                    registry_class = getattr(module, 'AgentRegistry')
                    if hasattr(registry_class, 'get_registry_stats'):
                        result['validated'].append(feature)
                    else:
                        result['warnings'].append("Performance optimization not fully implemented")
            
            elif feature == 'specialized_agent_support':
                if hasattr(module, 'AgentRegistry'):
                    registry_class = getattr(module, 'AgentRegistry')
                    if hasattr(registry_class, 'get_specialized_agents'):
                        result['validated'].append(feature)
                    else:
                        result['warnings'].append("Specialized agent support not implemented")
        
        return result
    
    async def _validate_integration(self) -> Dict[str, Any]:
        """Validate integration between components."""
        result = {
            'compliant': True,
            'validated_integrations': [],
            'issues': [],
            'warnings': []
        }
        
        try:
            # Test AgentProfileLoader + TaskToolProfileIntegration
            loader_path = self.project_root / 'claude_pm' / 'services' / 'agent_profile_loader.py'
            integration_path = self.project_root / 'claude_pm' / 'services' / 'task_tool_profile_integration.py'
            
            if loader_path.exists() and integration_path.exists():
                # Check if integration imports loader
                integration_content = integration_path.read_text()
                if 'AgentProfileLoader' in integration_content:
                    result['validated_integrations'].append('AgentProfileLoader → TaskToolProfileIntegration')
                else:
                    result['issues'].append('TaskToolProfileIntegration does not import AgentProfileLoader')
                    result['compliant'] = False
            
            # Test SharedPromptCache integration
            cache_path = self.project_root / 'claude_pm' / 'services' / 'shared_prompt_cache.py'
            if cache_path.exists():
                cache_content = cache_path.read_text()
                if 'singleton' in cache_content.lower():
                    result['validated_integrations'].append('SharedPromptCache singleton pattern')
                else:
                    result['warnings'].append('SharedPromptCache singleton pattern not clearly implemented')
            
            # Test AgentRegistry integration
            registry_path = self.project_root / 'claude_pm' / 'services' / 'agent_registry.py'
            if registry_path.exists() and loader_path.exists():
                loader_content = loader_path.read_text()
                if 'AgentRegistry' in loader_content:
                    result['validated_integrations'].append('AgentProfileLoader → AgentRegistry')
                else:
                    result['warnings'].append('AgentProfileLoader may not integrate with AgentRegistry')
            
        except Exception as e:
            result['compliant'] = False
            result['issues'].append(f"Integration validation error: {str(e)}")
        
        return result
    
    async def _validate_performance(self) -> Dict[str, Any]:
        """Validate performance requirements."""
        result = {
            'compliant': True,
            'performance_targets': {},
            'issues': [],
            'warnings': []
        }
        
        # Framework 014 performance requirements
        performance_requirements = {
            'agent_discovery': {'target': '<100ms', 'description': 'Agent discovery time'},
            'agent_loading': {'target': '<50ms', 'description': 'Agent loading time'},
            'cache_hit_ratio': {'target': '>95%', 'description': 'Cache hit ratio'},
            'prompt_generation': {'target': '<200ms', 'description': 'Enhanced prompt generation'},
            'registry_initialization': {'target': '<200ms', 'description': 'Registry initialization time'}
        }
        
        for req_name, req_data in performance_requirements.items():
            # Check if performance monitoring is implemented
            if req_name == 'agent_discovery':
                agent_registry_path = self.project_root / 'claude_pm' / 'services' / 'agent_registry.py'
                if agent_registry_path.exists():
                    content = agent_registry_path.read_text()
                    if 'time.time()' in content and 'discovery' in content:
                        result['performance_targets'][req_name] = 'monitored'
                    else:
                        result['warnings'].append(f'{req_name} performance not monitored')
            
            elif req_name == 'cache_hit_ratio':
                cache_path = self.project_root / 'claude_pm' / 'services' / 'shared_prompt_cache.py'
                if cache_path.exists():
                    content = cache_path.read_text()
                    if 'hit_rate' in content:
                        result['performance_targets'][req_name] = 'monitored'
                    else:
                        result['warnings'].append(f'{req_name} performance not monitored')
            
            elif req_name == 'prompt_generation':
                integration_path = self.project_root / 'claude_pm' / 'services' / 'task_tool_profile_integration.py'
                if integration_path.exists():
                    content = integration_path.read_text()
                    if 'response_time' in content:
                        result['performance_targets'][req_name] = 'monitored'
                    else:
                        result['warnings'].append(f'{req_name} performance not monitored')
        
        return result
    
    def _generate_recommendations(self) -> None:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check overall compliance
        if not self.validation_results['overall_compliance']:
            recommendations.append("Address all compliance issues before deployment")
        
        # Check component-specific recommendations
        for component, result in self.validation_results['components'].items():
            if not result.get('compliant', True):
                recommendations.append(f"Fix compliance issues in {component}")
            
            if result.get('warnings'):
                recommendations.append(f"Review warnings for {component}")
        
        # Performance recommendations
        performance_result = self.validation_results['components'].get('performance', {})
        if performance_result.get('warnings'):
            recommendations.append("Implement performance monitoring for all components")
        
        # Integration recommendations
        integration_result = self.validation_results['components'].get('integration', {})
        if integration_result.get('issues'):
            recommendations.append("Fix component integration issues")
        
        # Add general recommendations
        recommendations.extend([
            "Run comprehensive testing before deployment",
            "Monitor performance metrics in production",
            "Implement proper error handling and logging",
            "Document all framework extensions and modifications"
        ])
        
        self.validation_results['recommendations'] = recommendations
    
    def generate_report(self) -> str:
        """Generate validation report."""
        report = f"""
Framework Version 014 Compliance Report
======================================
Generated: {self.validation_results['validation_timestamp']}
Overall Compliance: {'✅ COMPLIANT' if self.validation_results['overall_compliance'] else '❌ NOT COMPLIANT'}

Component Validation Results:
"""
        
        for component, result in self.validation_results['components'].items():
            status = '✅ COMPLIANT' if result.get('compliant', True) else '❌ NOT COMPLIANT'
            report += f"\n{component.upper()}: {status}\n"
            
            if result.get('classes_found'):
                report += f"  Classes Found: {', '.join(result['classes_found'])}\n"
            
            if result.get('methods_found'):
                report += f"  Methods Found: {len(result['methods_found'])}\n"
            
            if result.get('features_validated'):
                report += f"  Features Validated: {', '.join(result['features_validated'])}\n"
            
            if result.get('issues'):
                report += f"  Issues: {len(result['issues'])}\n"
                for issue in result['issues']:
                    report += f"    - {issue}\n"
            
            if result.get('warnings'):
                report += f"  Warnings: {len(result['warnings'])}\n"
                for warning in result['warnings']:
                    report += f"    - {warning}\n"
        
        # Add issues summary
        if self.validation_results['issues']:
            report += f"\nCRITICAL ISSUES ({len(self.validation_results['issues'])}):\n"
            for issue in self.validation_results['issues']:
                report += f"  - {issue}\n"
        
        # Add warnings summary
        if self.validation_results['warnings']:
            report += f"\nWARNINGS ({len(self.validation_results['warnings'])}):\n"
            for warning in self.validation_results['warnings']:
                report += f"  - {warning}\n"
        
        # Add recommendations
        if self.validation_results['recommendations']:
            report += f"\nRECOMMENDATIONS:\n"
            for rec in self.validation_results['recommendations']:
                report += f"  - {rec}\n"
        
        report += "\n" + "=" * 50 + "\n"
        return report
    
    def save_report(self, filepath: Path) -> None:
        """Save validation report to file."""
        report = self.generate_report()
        filepath.write_text(report)
        
        # Also save raw JSON results
        json_filepath = filepath.with_suffix('.json')
        with open(json_filepath, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        logger.info(f"Validation report saved to {filepath}")
        logger.info(f"Raw results saved to {json_filepath}")


async def main():
    """Main validation function."""
    print("🔍 Framework Version 014 Compliance Validation")
    print("=" * 50)
    
    # Create validator
    validator = Framework014Validator()
    
    # Run validation
    try:
        results = await validator.validate_all_components()
        
        # Generate and display report
        report = validator.generate_report()
        print(report)
        
        # Save report
        report_path = validator.project_root / 'validation_report_014.txt'
        validator.save_report(report_path)
        
        # Exit with appropriate code
        if results['overall_compliance']:
            print("✅ All components are Framework 014 compliant!")
            sys.exit(0)
        else:
            print("❌ Framework 014 compliance issues found. See report for details.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())