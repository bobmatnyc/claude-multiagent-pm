"""
Engine for executing hooks with support for sync/async operations.
"""

import asyncio
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Any

from .models import HookConfiguration, HookExecutionResult


class HookExecutionEngine:
    """Engine for executing hooks with support for sync/async operations."""
    
    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0,
            'last_updated': datetime.now()
        }
    
    async def execute_hook(self, hook_config: HookConfiguration, context: Dict[str, Any]) -> HookExecutionResult:
        """Execute a single hook with proper error handling and timeout.
        
        Now defaults to async execution unless force_sync is True.
        """
        start_time = time.time()
        self.execution_stats['total_executions'] += 1
        
        try:
            # Determine execution mode - async by default unless forced sync
            is_async_handler = asyncio.iscoroutinefunction(hook_config.handler)
            should_run_async = hook_config.prefer_async and not hook_config.force_sync
            
            # Execute hook with timeout based on execution mode
            if is_async_handler:
                # Handler is already async
                result = await asyncio.wait_for(
                    hook_config.handler(context),
                    timeout=hook_config.timeout
                )
            elif should_run_async and not hook_config.force_sync:
                # Run sync function in executor (async mode)
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        hook_config.handler,
                        context
                    ),
                    timeout=hook_config.timeout
                )
            else:
                # Force sync execution - run in executor but don't make it async
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        hook_config.handler,
                        context
                    ),
                    timeout=hook_config.timeout
                )
            
            execution_time = time.time() - start_time
            self.execution_stats['successful_executions'] += 1
            
            # Update average execution time
            self._update_average_execution_time(execution_time)
            
            return HookExecutionResult(
                hook_id=hook_config.hook_id,
                success=True,
                execution_time=execution_time,
                result=result,
                metadata={
                    'execution_mode': 'async' if (is_async_handler or should_run_async) else 'sync',
                    'prefer_async': hook_config.prefer_async,
                    'force_sync': hook_config.force_sync,
                    'is_async_handler': is_async_handler
                }
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.execution_stats['failed_executions'] += 1
            
            error_msg = f"Hook {hook_config.hook_id} timed out after {hook_config.timeout}s"
            self.logger.error(error_msg)
            
            return HookExecutionResult(
                hook_id=hook_config.hook_id,
                success=False,
                execution_time=execution_time,
                error=error_msg,
                metadata={
                    'execution_mode': 'timeout',
                    'prefer_async': hook_config.prefer_async,
                    'force_sync': hook_config.force_sync
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_stats['failed_executions'] += 1
            
            error_msg = f"Hook {hook_config.hook_id} failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return HookExecutionResult(
                hook_id=hook_config.hook_id,
                success=False,
                execution_time=execution_time,
                error=error_msg,
                metadata={
                    'execution_mode': 'error',
                    'prefer_async': hook_config.prefer_async,
                    'force_sync': hook_config.force_sync,
                    'exception_type': type(e).__name__, 
                    'traceback': traceback.format_exc()
                }
            )
    
    async def execute_hooks_batch(self, hook_configs: List[HookConfiguration], context: Dict[str, Any]) -> List[HookExecutionResult]:
        """Execute multiple hooks concurrently."""
        tasks = [
            self.execute_hook(hook_config, context)
            for hook_config in sorted(hook_configs, key=lambda h: h.priority, reverse=True)
            if hook_config.enabled
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from gather
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                hook_config = hook_configs[i]
                processed_results.append(HookExecutionResult(
                    hook_id=hook_config.hook_id,
                    success=False,
                    execution_time=0.0,
                    error=f"Batch execution error: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _update_average_execution_time(self, execution_time: float):
        """Update running average of execution time."""
        current_avg = self.execution_stats['average_execution_time']
        total_executions = self.execution_stats['total_executions']
        
        # Calculate new average
        new_avg = ((current_avg * (total_executions - 1)) + execution_time) / total_executions
        self.execution_stats['average_execution_time'] = new_avg
        self.execution_stats['last_updated'] = datetime.now()
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total = self.execution_stats['total_executions']
        return {
            **self.execution_stats,
            'success_rate': (
                self.execution_stats['successful_executions'] / max(1, total)
            ),
            'failure_rate': (
                self.execution_stats['failed_executions'] / max(1, total)
            )
        }
    
    def cleanup(self):
        """Clean up executor resources."""
        self.executor.shutdown(wait=True)