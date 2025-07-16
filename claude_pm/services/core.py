"""
Core Service Module - Unified access to all framework services

This module provides a centralized aggregation of all framework services for easy import
and unified access. This simplifies service discovery and reduces import complexity.

Created: 2025-07-16 (Phase 1 Core Infrastructure - CRITICAL-001)
Purpose: Fix import resolution by providing unified service access
"""

# Import all core services for aggregated access
from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.health_monitor import HealthMonitor
from claude_pm.services.agent_registry import AgentRegistry
from claude_pm.services.model_selector import ModelSelector
from claude_pm.services.performance_monitor import PerformanceMonitor
from claude_pm.services.parent_directory_manager import ParentDirectoryManager
from claude_pm.services.template_manager import TemplateManager
from claude_pm.services.memory_service_integration import MemoryServiceIntegration
from claude_pm.services.framework_agent_loader import FrameworkAgentLoader
from claude_pm.services.agent_lifecycle_manager import AgentLifecycleManager
from claude_pm.services.agent_modification_tracker import AgentModificationTracker
from claude_pm.services.agent_persistence_service import AgentPersistenceService
from claude_pm.services.dependency_manager import DependencyManager
from claude_pm.services.working_directory_deployer import WorkingDirectoryDeployer
from claude_pm.services.pm_orchestrator import PMOrchestrator
from claude_pm.services.hook_processing_service import HookProcessingService
from claude_pm.services.correction_capture import CorrectionCapture
from claude_pm.services.prompt_improver import PromptImprover
from claude_pm.services.pattern_analyzer import PatternAnalyzer
from claude_pm.services.agent_trainer import AgentTrainer
# from claude_pm.services.mirascope_evaluator import MirascopeEvaluator  # Commented out - service unavailable

# Import project service for project management
from claude_pm.services.project_service import ProjectService

# Import validation services
from claude_pm.services.post_installation_validator import PostInstallationValidator
from claude_pm.services.framework_deployment_validator import FrameworkDeploymentValidator
from claude_pm.services.claude_pm_startup_validator import StartupValidator

# Import integration services
from claude_pm.services.claude_code_integration import ClaudeCodeIntegrationService
from claude_pm.services.cmpm_integration_service import CMPMIntegrationService
from claude_pm.services.cache_service_integration import CacheServiceWrapper
from claude_pm.services.task_tool_profile_integration import TaskToolProfileIntegration
from claude_pm.services.agent_training_integration import AgentTrainingIntegration
from claude_pm.services.evaluation_integration import EvaluationIntegrationService

# Import MCP service detector
from claude_pm.services.mcp_service_detector import MCPServiceDetector

# Import health dashboard
from claude_pm.services.health_dashboard import HealthDashboard

# Define a unified core service interface
class UnifiedCoreService:
    """
    Unified Core Service - Single point of access for all framework services
    
    This class provides a unified interface to all framework services, making it easier
    to discover and use services without needing to know their individual import paths.
    """
    
    def __init__(self):
        """Initialize unified core service with lazy loading of services"""
        self._services = {}
        self._service_classes = {
            'shared_prompt_cache': SharedPromptCache,
            'health_monitor': HealthMonitor,
            'agent_registry': AgentRegistry,
            'model_selector': ModelSelector,
            'performance_monitor': PerformanceMonitor,
            'parent_directory_manager': ParentDirectoryManager,
            'template_manager': TemplateManager,
            'memory_service': MemoryServiceIntegration,
            'framework_agent_loader': FrameworkAgentLoader,
            'agent_lifecycle_manager': AgentLifecycleManager,
            'agent_modification_tracker': AgentModificationTracker,
            'agent_persistence_service': AgentPersistenceService,
            'dependency_manager': DependencyManager,
            'working_directory_deployer': WorkingDirectoryDeployer,
            'pm_orchestrator': PMOrchestrator,
            'hook_processing_service': HookProcessingService,
            'correction_capture': CorrectionCapture,
            'prompt_improver': PromptImprover,
            'pattern_analyzer': PatternAnalyzer,
            'agent_trainer': AgentTrainer,
            # 'mirascope_evaluator': MirascopeEvaluator,  # Commented out - service unavailable
            'project_service': ProjectService,
            'post_installation_validator': PostInstallationValidator,
            'framework_deployment_validator': FrameworkDeploymentValidator,
            'claude_pm_startup_validator': StartupValidator,
            'claude_code_integration': ClaudeCodeIntegrationService,
            'cmpm_integration_service': CMPMIntegrationService,
            'cache_service_integration': CacheServiceWrapper,
            'task_tool_profile_integration': TaskToolProfileIntegration,
            'agent_training_integration': AgentTrainingIntegration,
            'evaluation_integration': EvaluationIntegrationService,
            'mcp_service_detector': MCPServiceDetector,
            'health_dashboard': HealthDashboard
        }
    
    def get_service(self, service_name: str):
        """
        Get a service instance by name (lazy loading)
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service name is not recognized
        """
        if service_name not in self._service_classes:
            raise ValueError(f"Unknown service: {service_name}. Available services: {list(self._service_classes.keys())}")
        
        # Lazy load service
        if service_name not in self._services:
            service_class = self._service_classes[service_name]
            self._services[service_name] = service_class()
        
        return self._services[service_name]
    
    @property
    def shared_prompt_cache(self) -> SharedPromptCache:
        """Get shared prompt cache service"""
        return self.get_service('shared_prompt_cache')
    
    @property
    def health_monitor(self) -> HealthMonitor:
        """Get health monitor service"""
        return self.get_service('health_monitor')
    
    @property
    def agent_registry(self) -> AgentRegistry:
        """Get agent registry service"""
        return self.get_service('agent_registry')
    
    @property
    def model_selector(self) -> ModelSelector:
        """Get model selector service"""
        return self.get_service('model_selector')
    
    @property
    def performance_monitor(self) -> PerformanceMonitor:
        """Get performance monitor service"""
        return self.get_service('performance_monitor')
    
    @property
    def parent_directory_manager(self) -> ParentDirectoryManager:
        """Get parent directory manager service"""
        return self.get_service('parent_directory_manager')
    
    @property
    def template_manager(self) -> TemplateManager:
        """Get template manager service"""
        return self.get_service('template_manager')
    
    @property
    def memory_service(self) -> MemoryServiceIntegration:
        """Get memory service integration"""
        return self.get_service('memory_service')
    
    @property
    def framework_agent_loader(self) -> FrameworkAgentLoader:
        """Get framework agent loader service"""
        return self.get_service('framework_agent_loader')
    
    @property
    def project_service(self) -> ProjectService:
        """Get project service"""
        return self.get_service('project_service')
    
    @property
    def mcp_service_detector(self) -> MCPServiceDetector:
        """Get MCP service detector"""
        return self.get_service('mcp_service_detector')
    
    @property
    def health_dashboard(self) -> HealthDashboard:
        """Get health dashboard service"""
        return self.get_service('health_dashboard')
    
    def list_services(self) -> list:
        """List all available services"""
        return list(self._service_classes.keys())
    
    def get_service_info(self, service_name: str) -> dict:
        """
        Get information about a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary with service information
        """
        if service_name not in self._service_classes:
            raise ValueError(f"Unknown service: {service_name}")
        
        service_class = self._service_classes[service_name]
        return {
            'name': service_name,
            'class': service_class.__name__,
            'module': service_class.__module__,
            'doc': service_class.__doc__,
            'loaded': service_name in self._services
        }

# Create a singleton instance for easy access
unified_core_service = UnifiedCoreService()

# Export all service classes and the unified service
__all__ = [
    # Core services
    'SharedPromptCache',
    'HealthMonitor',
    'AgentRegistry',
    'ModelSelector',
    'PerformanceMonitor',
    'ParentDirectoryManager',
    'TemplateManager',
    'MemoryServiceIntegration',
    'FrameworkAgentLoader',
    'AgentLifecycleManager',
    'AgentModificationTracker',
    'AgentPersistenceService',
    'DependencyManager',
    'WorkingDirectoryDeployer',
    'PMOrchestrator',
    'HookProcessingService',
    'CorrectionCapture',
    'PromptImprover',
    'PatternAnalyzer',
    'AgentTrainer',
    # 'MirascopeEvaluator',  # Commented out - service unavailable
    'ProjectService',
    
    # Validation services
    'PostInstallationValidator',
    'FrameworkDeploymentValidator',
    'StartupValidator',
    
    # Integration services
    'ClaudeCodeIntegrationService',
    'CMPMIntegrationService',
    'CacheServiceWrapper',
    'TaskToolProfileIntegration',
    'AgentTrainingIntegration',
    'EvaluationIntegrationService',
    
    # Other services
    'MCPServiceDetector',
    'HealthDashboard',
    
    # Unified service
    'UnifiedCoreService',
    'unified_core_service'
]