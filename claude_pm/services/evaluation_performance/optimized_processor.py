"""
Optimized evaluation processor using batch processing.

Extends AsyncBatchProcessor for evaluation-specific optimizations.
"""

import hashlib
import json
import logging
from typing import Any, Dict, List

from ..mirascope_evaluator import MirascopeEvaluator
from .batch_processor import AsyncBatchProcessor
from .cache import AdvancedEvaluationCache
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class OptimizedEvaluationProcessor(AsyncBatchProcessor):
    """
    Optimized evaluation processor using batch processing.
    
    Extends AsyncBatchProcessor for evaluation-specific optimizations.
    """
    
    def __init__(
        self,
        evaluator: MirascopeEvaluator,
        cache: AdvancedEvaluationCache,
        circuit_breaker: CircuitBreaker,
        **kwargs
    ):
        """
        Initialize optimized processor.
        
        Args:
            evaluator: Mirascope evaluator instance
            cache: Advanced cache instance
            circuit_breaker: Circuit breaker instance
        """
        super().__init__(**kwargs)
        self.evaluator = evaluator
        self.cache = cache
        self.circuit_breaker = circuit_breaker
    
    async def _process_items(self, items: List[Dict[str, Any]]) -> List[Any]:
        """Process evaluation items in batch."""
        results = []
        
        # Separate cached and non-cached items
        cached_items = []
        non_cached_items = []
        cache_keys = []
        
        for item in items:
            cache_key = self._generate_cache_key(item)
            cache_keys.append(cache_key)
            
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                cached_items.append(cached_result)
                non_cached_items.append(None)
            else:
                cached_items.append(None)
                non_cached_items.append(item)
        
        # Process non-cached items
        evaluation_results = []
        for item in non_cached_items:
            if item is None:
                evaluation_results.append(None)
            else:
                try:
                    result = await self.circuit_breaker.call(
                        self.evaluator.evaluate_response,
                        item["agent_type"],
                        item["response_text"],
                        item["context"],
                        item.get("correction_id")
                    )
                    evaluation_results.append(result)
                except Exception as e:
                    evaluation_results.append(e)
        
        # Combine cached and evaluated results
        eval_index = 0
        for i, cached_result in enumerate(cached_items):
            if cached_result is not None:
                results.append(cached_result)
            else:
                eval_result = evaluation_results[eval_index]
                eval_index += 1
                
                if isinstance(eval_result, Exception):
                    results.append(eval_result)
                else:
                    # Cache the result
                    self.cache.put(cache_keys[i], eval_result)
                    results.append(eval_result)
        
        return results
    
    def _generate_cache_key(self, item: Dict[str, Any]) -> str:
        """Generate cache key for evaluation item."""
        content = f"{item['agent_type']}:{item['response_text']}:{json.dumps(item['context'], sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()