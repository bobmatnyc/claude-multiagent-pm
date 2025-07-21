"""
Evaluation Performance Optimization Module.

Provides performance optimization for the evaluation system including
advanced caching, async processing, and performance monitoring.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from claude_pm.core.config import Config
from ..mirascope_evaluator import MirascopeEvaluator, EvaluationResult
from .cache import AdvancedEvaluationCache
from .circuit_breaker import CircuitBreaker, CircuitBreakerState
from .optimized_processor import OptimizedEvaluationProcessor

logger = logging.getLogger(__name__)


class EvaluationPerformanceManager:
    """
    Main performance manager for evaluation system.
    
    Coordinates caching, batching, and performance optimization.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize performance manager.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.enabled = self.config.get("evaluation_performance_enabled", True)
        
        # Initialize components
        self.cache = AdvancedEvaluationCache(
            max_size=self.config.get("evaluation_cache_max_size", 1000),
            ttl_seconds=self.config.get("evaluation_cache_ttl_seconds", 3600),
            strategy=self.config.get("evaluation_cache_strategy", "hybrid"),
            memory_limit_mb=self.config.get("evaluation_cache_memory_limit_mb", 100)
        )
        
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("evaluation_circuit_breaker_threshold", 5),
            timeout_seconds=self.config.get("evaluation_circuit_breaker_timeout", 60),
            success_threshold=self.config.get("evaluation_circuit_breaker_success_threshold", 3)
        )
        
        # Will be initialized with evaluator
        self.processor: Optional[OptimizedEvaluationProcessor] = None
        self.evaluator: Optional[MirascopeEvaluator] = None
        
        # Performance tracking
        self.start_time = datetime.now()
        self.total_evaluations = 0
        self.total_time = 0.0
        
        if self.enabled:
            logger.info("Evaluation performance manager initialized")
    
    async def initialize(self, evaluator: MirascopeEvaluator) -> None:
        """Initialize with evaluator instance."""
        self.evaluator = evaluator
        
        # Initialize batch processor
        self.processor = OptimizedEvaluationProcessor(
            evaluator=evaluator,
            cache=self.cache,
            circuit_breaker=self.circuit_breaker,
            batch_size=self.config.get("evaluation_batch_size", 10),
            max_batch_wait_ms=self.config.get("evaluation_batch_wait_ms", 100),
            max_concurrent_batches=self.config.get("evaluation_max_concurrent_batches", 5)
        )
        
        # Start background tasks
        await self.cache.start_cleanup_task()
        await self.processor.start()
        
        logger.info("Performance manager initialized with evaluator")
    
    async def shutdown(self) -> None:
        """Shutdown performance manager."""
        if self.processor:
            await self.processor.stop()
        
        await self.cache.stop_cleanup_task()
        
        logger.info("Performance manager shutdown complete")
    
    async def evaluate_response(
        self,
        agent_type: str,
        response_text: str,
        context: Dict[str, Any],
        correction_id: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate response with performance optimization.
        
        Args:
            agent_type: Type of agent
            response_text: Response to evaluate
            context: Context information
            correction_id: Optional correction ID
            
        Returns:
            Evaluation result
        """
        if not self.enabled or not self.processor:
            # Fallback to direct evaluation
            return await self.evaluator.evaluate_response(
                agent_type, response_text, context, correction_id
            )
        
        start_time = time.time()
        
        try:
            # Submit to batch processor
            item = {
                "agent_type": agent_type,
                "response_text": response_text,
                "context": context,
                "correction_id": correction_id
            }
            
            result = await self.processor.submit(item)
            
            # Handle exceptions
            if isinstance(result, Exception):
                raise result
            
            # Update performance metrics
            self.total_evaluations += 1
            self.total_time += time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Optimized evaluation failed: {e}")
            
            # Fallback to direct evaluation
            return await self.evaluator.evaluate_response(
                agent_type, response_text, context, correction_id
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            "enabled": self.enabled,
            "uptime_seconds": uptime,
            "total_evaluations": self.total_evaluations,
            "average_evaluation_time": self.total_time / self.total_evaluations if self.total_evaluations > 0 else 0,
            "evaluations_per_second": self.total_evaluations / uptime if uptime > 0 else 0,
            "cache_stats": self.cache.get_stats(),
            "circuit_breaker_state": self.circuit_breaker.get_state(),
            "processor_stats": self.processor.get_stats() if self.processor else None
        }
        
        return stats
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear performance cache."""
        self.cache.clear()
        
        return {
            "cache_cleared": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_circuit_breaker(self) -> Dict[str, Any]:
        """Reset circuit breaker to closed state."""
        with self.circuit_breaker.lock:
            self.circuit_breaker.state = CircuitBreakerState.CLOSED
            self.circuit_breaker.failure_count = 0
            self.circuit_breaker.success_count = 0
            self.circuit_breaker.last_failure_time = None
        
        return {
            "circuit_breaker_reset": True,
            "timestamp": datetime.now().isoformat()
        }


# Import and re-export public API
from .utils import (
    get_performance_manager,
    initialize_performance_manager,
    shutdown_performance_manager,
    optimized_evaluate_response,
    get_evaluation_performance_stats,
)
from .cache import CacheStrategy
from .metrics import PerformanceMetrics
from .batch_processor import AsyncBatchProcessor

__all__ = [
    'EvaluationPerformanceManager',
    'AdvancedEvaluationCache',
    'CircuitBreaker',
    'AsyncBatchProcessor',
    'OptimizedEvaluationProcessor',
    'CacheStrategy',
    'CircuitBreakerState',
    'PerformanceMetrics',
    'get_performance_manager',
    'initialize_performance_manager',
    'shutdown_performance_manager',
    'optimized_evaluate_response',
    'get_evaluation_performance_stats'
]