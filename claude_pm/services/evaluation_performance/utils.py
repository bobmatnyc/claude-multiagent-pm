"""
Helper functions and global instance management for evaluation performance.
"""

import logging
from typing import Dict, Any, Optional

from claude_pm.core.config import Config
from ..mirascope_evaluator import MirascopeEvaluator, EvaluationResult
from .cache import CacheStrategy
from .circuit_breaker import CircuitBreakerState

logger = logging.getLogger(__name__)

# Type imports for public API
from ..mirascope_evaluator import EvaluationResult  # noqa: F401

# Global performance manager instance
_performance_manager: Optional['EvaluationPerformanceManager'] = None


def get_performance_manager(config: Optional[Config] = None) -> 'EvaluationPerformanceManager':
    """Get global performance manager instance."""
    global _performance_manager
    
    # Import here to avoid circular dependency
    from . import EvaluationPerformanceManager
    
    if _performance_manager is None:
        _performance_manager = EvaluationPerformanceManager(config)
    
    return _performance_manager


async def initialize_performance_manager(evaluator: MirascopeEvaluator, config: Optional[Config] = None) -> Dict[str, Any]:
    """Initialize the performance manager."""
    try:
        manager = get_performance_manager(config)
        await manager.initialize(evaluator)
        
        stats = manager.get_performance_stats()
        
        return {
            "initialized": True,
            "performance_enabled": manager.enabled,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize performance manager: {e}")
        return {"initialized": False, "error": str(e)}


async def shutdown_performance_manager() -> None:
    """Shutdown the performance manager."""
    global _performance_manager
    
    if _performance_manager:
        await _performance_manager.shutdown()
        _performance_manager = None


# Helper functions
async def optimized_evaluate_response(
    agent_type: str,
    response_text: str,
    context: Dict[str, Any],
    correction_id: Optional[str] = None,
    config: Optional[Config] = None
) -> EvaluationResult:
    """
    Evaluate response with performance optimization.
    
    Args:
        agent_type: Type of agent
        response_text: Response to evaluate
        context: Context information
        correction_id: Optional correction ID
        config: Optional configuration
        
    Returns:
        Evaluation result
    """
    manager = get_performance_manager(config)
    return await manager.evaluate_response(agent_type, response_text, context, correction_id)


def get_evaluation_performance_stats(config: Optional[Config] = None) -> Dict[str, Any]:
    """Get evaluation performance statistics."""
    manager = get_performance_manager(config)
    return manager.get_performance_stats()