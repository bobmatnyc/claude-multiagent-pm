"""
Unified Memory Service Module

This module provides a flexible, backend-agnostic memory management system
for the Claude PM Framework. It supports multiple memory backends including
mem0AI and SQLite with automatic detection, circuit breaker patterns, and
graceful degradation.

Key Features:
- Backend auto-detection and selection
- Circuit breaker pattern for resilience
- Graceful degradation with fallback backends
- Configuration management with three-tier hierarchy
- Performance monitoring and health checking
- Data migration between backends
- Intelligent memory recall with context enhancement
- Memory-driven recommendations and pattern matching
- Automatic error prevention through memory analysis
- Backward compatibility with existing integrations
- Release-ready deployment support without API dependencies

Supported Backends:
- mem0AI: Advanced memory service with similarity search
- SQLite: Lightweight file-based storage with FTS

Usage:
    from claude_pm.services.memory import (
        FlexibleMemoryService,
        create_memory_recall_service,
        MemoryCategory,
        MemoryQuery,
        ReleaseReadyMemoryService,
        create_fallback_memory_service,
        validate_memory_system_for_release,
    )

    # For development and testing
    memory_service = FlexibleMemoryService()
    await memory_service.initialize()

    # For production deployments
    service = ReleaseReadyMemoryService(environment="production")
    await service.initialize()

    # For guaranteed fallback operation
    service = create_fallback_memory_service()
    await service.initialize()

    # Add memory
    memory_id = await memory_service.add_memory(
        "my_project",
        "Important decision",
        MemoryCategory.PROJECT
    )

    # Search memories
    memories = await memory_service.search_memories(
        "my_project",
        MemoryQuery("decision")
    )

    # Use intelligent memory recall
    recall_service = create_memory_recall_service(memory_service)
    await recall_service.initialize()

    # Get memory-driven recommendations for operations
    result = await recall_service.recall_for_operation(
        project_name="my_project",
        operation_type="deploy",
        operation_context={"environment": "production"}
    )

    if result.success:
        recommendations = result.recommendations.get_top_recommendations()
        context = result.enriched_context.get_agent_context()

    # Validate system for release
    validation_results = await validate_memory_system_for_release()
    if validation_results["release_ready"]:
        print("Memory system ready for production deployment")
"""

from .interfaces.models import MemoryCategory, MemoryItem, MemoryQuery, HealthStatus, BackendHealth

from .interfaces.backend import MemoryBackend
from .interfaces.exceptions import (
    MemoryServiceError,
    BackendError,
    CircuitBreakerOpenError,
    ConfigurationError,
    MigrationError,
)

from .services.unified_service import FlexibleMemoryService
from .services.circuit_breaker import CircuitBreaker, CircuitState
from .services.auto_detection import AutoDetectionEngine

from .backends.mem0ai_backend import Mem0AIBackend
from .backends.sqlite_backend import SQLiteBackend

from .monitoring.performance import PerformanceMonitor
from .monitoring.health import HealthMonitor

# Memory trigger infrastructure
from .trigger_types import TriggerType, TriggerPriority
from .trigger_orchestrator import MemoryTriggerOrchestrator, TriggerEvent, TriggerResult
from .trigger_policies import TriggerPolicyEngine, PolicyRule, PolicyConfig, PolicyDecision
from .framework_hooks import FrameworkMemoryHooks, HookContext
from .decorators import (
    memory_trigger,
    workflow_memory_trigger,
    agent_memory_trigger,
    issue_memory_trigger,
    error_memory_trigger,
    knowledge_memory_trigger,
    decision_memory_trigger,
    workflow_trigger_context,
    agent_trigger_context,
    issue_trigger_context,
    trigger_immediate_memory,
    is_memory_triggers_enabled,
    get_memory_trigger_metrics,
    set_global_hooks,
    get_global_hooks,
)
from .memory_trigger_service import (
    MemoryTriggerService,
    create_memory_trigger_service,
    load_memory_trigger_config,
    get_global_memory_trigger_service,
    initialize_global_memory_trigger_service,
    cleanup_global_memory_trigger_service,
    DEFAULT_CONFIG,
)

# Memory recall system
from ..memory_recall_service import MemoryRecallService, MemoryRecallConfig, MemoryRecallResult
from .memory_context_enhancer import (
    MemoryContextEnhancer,
    MemoryContext,
    RecallTrigger,
    RecallConfig,
)
from .similarity_matcher import (
    SimilarityMatcher,
    SimilarityResult,
    SimilarityAlgorithm,
    MatchingConfig,
)
from .context_builder import ContextBuilder, EnrichedContext, ContextType, ContextTemplate
from .recommendation_engine import (
    RecommendationEngine,
    Recommendation,
    RecommendationSet,
    RecommendationType,
    RecommendationConfig,
)

# Agent memory integration and health monitoring
from .agent_memory_integration import (
    AgentMemoryIntegration,
    initialize_global_memory_integration,
    cleanup_global_memory_integration,
    register_agent_for_memory,
    validate_global_memory_compliance,
    get_global_memory_integration,
)
from .memory_health_monitor import (
    MemoryHealthMonitor,
    HealthLevel,
    HealthMetric,
    AgentHealthReport,
    SystemHealthReport,
)

# Release-ready memory services
from .fallback_memory_config import (
    get_development_safe_memory_config,
    get_release_ready_memory_config,
    create_fallback_memory_service,
    validate_memory_system_health,
    migrate_memory_system_if_needed,
)
from .release_ready_memory import (
    ReleaseReadyMemoryService,
    get_global_memory_service,
    cleanup_global_memory_service,
    collect_memory,
    search_project_memories,
)
from .validation import (
    validate_memory_system_for_release,
    print_validation_report,
)

__version__ = "1.3.0"
__author__ = "Claude PM Framework"


# Main service factory
def create_flexible_memory_service(config: dict = None) -> FlexibleMemoryService:
    """
    Factory function to create a FlexibleMemoryService instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        FlexibleMemoryService: Configured memory service instance
    """
    return FlexibleMemoryService(config)


# Memory recall service factory
def create_memory_recall_service(
    memory_service: FlexibleMemoryService = None, config: MemoryRecallConfig = None
) -> MemoryRecallService:
    """
    Factory function to create a MemoryRecallService instance.

    Args:
        memory_service: Optional memory service instance (creates one if None)
        config: Optional recall configuration

    Returns:
        MemoryRecallService: Configured memory recall service instance
    """
    if memory_service is None:
        memory_service = create_flexible_memory_service()

    return MemoryRecallService(memory_service, config)


# Convenience function for release-ready deployments
def create_release_ready_memory_service(environment: str = None) -> ReleaseReadyMemoryService:
    """
    Factory function to create a release-ready memory service.

    Args:
        environment: Deployment environment (development, production, test)

    Returns:
        ReleaseReadyMemoryService: Production-ready memory service
    """
    return ReleaseReadyMemoryService(environment=environment)


# Backward compatibility
def get_memory_service(config: dict = None) -> FlexibleMemoryService:
    """Legacy factory function for backward compatibility."""
    return create_flexible_memory_service(config)


# Quick validation function
async def quick_memory_validation() -> bool:
    """
    Quick validation check for memory system health.
    
    Returns:
        bool: True if memory system is healthy and functional
    """
    try:
        health_status = validate_memory_system_health()
        if health_status["overall_health"] in ["healthy", "degraded"]:
            # Test basic operation
            service = ReleaseReadyMemoryService()
            success = await service.initialize()
            await service.cleanup()
            return success
        return False
    except Exception:
        return False


__all__ = [
    # Core interfaces
    "MemoryCategory",
    "MemoryItem",
    "MemoryQuery",
    "HealthStatus",
    "BackendHealth",
    "MemoryBackend",
    # Main service
    "FlexibleMemoryService",
    "create_flexible_memory_service",
    "create_memory_recall_service",
    "create_release_ready_memory_service",
    "get_memory_service",  # Legacy
    # Support services
    "CircuitBreaker",
    "CircuitState",
    "AutoDetectionEngine",
    # Backends
    "Mem0AIBackend",
    "SQLiteBackend",
    # Monitoring
    "PerformanceMonitor",
    "HealthMonitor",
    # Memory trigger infrastructure
    "MemoryTriggerOrchestrator",
    "TriggerType",
    "TriggerPriority",
    "TriggerEvent",
    "TriggerResult",
    "TriggerPolicyEngine",
    "PolicyRule",
    "PolicyConfig",
    "PolicyDecision",
    "FrameworkMemoryHooks",
    "HookContext",
    "MemoryTriggerService",
    "create_memory_trigger_service",
    "load_memory_trigger_config",
    "get_global_memory_trigger_service",
    "initialize_global_memory_trigger_service",
    "cleanup_global_memory_trigger_service",
    "DEFAULT_CONFIG",
    # Memory trigger decorators
    "memory_trigger",
    "workflow_memory_trigger",
    "agent_memory_trigger",
    "issue_memory_trigger",
    "error_memory_trigger",
    "knowledge_memory_trigger",
    "decision_memory_trigger",
    "workflow_trigger_context",
    "agent_trigger_context",
    "issue_trigger_context",
    "trigger_immediate_memory",
    "is_memory_triggers_enabled",
    "get_memory_trigger_metrics",
    "set_global_hooks",
    "get_global_hooks",
    # Memory recall system
    "MemoryRecallService",
    "MemoryRecallConfig",
    "MemoryRecallResult",
    "MemoryContextEnhancer",
    "MemoryContext",
    "RecallTrigger",
    "RecallConfig",
    "SimilarityMatcher",
    "SimilarityResult",
    "SimilarityAlgorithm",
    "MatchingConfig",
    "ContextBuilder",
    "EnrichedContext",
    "ContextType",
    "ContextTemplate",
    "RecommendationEngine",
    "Recommendation",
    "RecommendationSet",
    "RecommendationType",
    "RecommendationConfig",
    # Exceptions
    "MemoryServiceError",
    "BackendError",
    "CircuitBreakerOpenError",
    "ConfigurationError",
    "MigrationError",
    # Agent memory integration and health monitoring
    "AgentMemoryIntegration",
    "initialize_global_memory_integration",
    "cleanup_global_memory_integration",
    "register_agent_for_memory",
    "validate_global_memory_compliance",
    "get_global_memory_integration",
    "MemoryHealthMonitor",
    "HealthLevel",
    "HealthMetric",
    "AgentHealthReport",
    "SystemHealthReport",
    # Release-ready deployment support
    "get_development_safe_memory_config",
    "get_release_ready_memory_config",
    "create_fallback_memory_service",
    "validate_memory_system_health",
    "migrate_memory_system_if_needed",
    "ReleaseReadyMemoryService",
    "get_global_memory_service",
    "cleanup_global_memory_service",
    "collect_memory",
    "search_project_memories",
    "validate_memory_system_for_release",
    "print_validation_report",
    "quick_memory_validation",
]