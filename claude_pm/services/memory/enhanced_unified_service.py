"""
Enhanced Unified Memory Service with Async Optimization

This module provides an enhanced version of the FlexibleMemoryService
that integrates async optimization for better performance, timeout handling,
and concurrent operation management.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Union

from .services.unified_service import FlexibleMemoryService
from .async_optimization import AsyncMemoryOperationOptimizer, optimized_memory_context
from .interfaces.models import (
    MemoryItem,
    MemoryQuery,
    MemoryCategory,
    HealthStatus,
    OperationResult,
)
from .interfaces.exceptions import (
    MemoryServiceError,
    BackendNotAvailableError,
    CircuitBreakerOpenError,
)

logger = logging.getLogger(__name__)


class EnhancedFlexibleMemoryService(FlexibleMemoryService):
    """
    Enhanced FlexibleMemoryService with async optimization.
    
    Provides all the functionality of FlexibleMemoryService with:
    - Optimized async operations
    - Better timeout handling
    - Improved concurrent operation management
    - Performance monitoring and auto-tuning
    - Operation caching for frequent queries
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced memory service."""
        super().__init__(config)
        
        # Enhanced configuration
        self.optimization_config = {
            "max_concurrent_ops": self.config.get("max_concurrent_ops", 8),
            "operation_timeout": self.config.get("operation_timeout", 10.0),
            "batch_size": self.config.get("batch_size", 3),
            "cache_ttl": self.config.get("cache_ttl", 180),
            "enable_optimization": self.config.get("enable_optimization", True),
        }
        
        # Async optimizer
        self.optimizer: Optional[AsyncMemoryOperationOptimizer] = None
        
        # Enhanced metrics
        self.enhanced_metrics = {
            "optimization_enabled": False,
            "optimization_metrics": {},
            "enhanced_operations": 0,
            "optimization_errors": 0,
        }
    
    async def initialize(self) -> bool:
        """Initialize service with async optimization."""
        # Initialize base service
        if not await super().initialize():
            return False
        
        # Initialize async optimizer if enabled
        if self.optimization_config["enable_optimization"]:
            try:
                self.optimizer = AsyncMemoryOperationOptimizer(self.optimization_config)
                await self.optimizer.start()
                self.enhanced_metrics["optimization_enabled"] = True
                logger.info("Async memory optimization enabled")
            except Exception as e:
                logger.warning(f"Failed to enable async optimization: {e}")
                self.enhanced_metrics["optimization_errors"] += 1
                # Continue without optimization
        
        return True
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Enhanced memory addition with optimization."""
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")
        
        # Use optimization if available
        if self.optimizer and self.enhanced_metrics["optimization_enabled"]:
            try:
                self.enhanced_metrics["enhanced_operations"] += 1
                return await self.optimizer.optimized_add_memory(
                    self.active_backend,
                    project_name,
                    content,
                    category,
                    tags,
                    metadata,
                )
            except Exception as e:
                logger.warning(f"Optimization failed, falling back to standard operation: {e}")
                self.enhanced_metrics["optimization_errors"] += 1
                # Fall back to standard operation
        
        # Standard operation
        return await super().add_memory(project_name, content, category, tags, metadata)
    
    async def search_memories(self, project_name: str, query: MemoryQuery) -> List[MemoryItem]:
        """Enhanced memory search with optimization and caching."""
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")
        
        # Use optimization if available
        if self.optimizer and self.enhanced_metrics["optimization_enabled"]:
            try:
                self.enhanced_metrics["enhanced_operations"] += 1
                return await self.optimizer.optimized_search_memories(
                    self.active_backend,
                    project_name,
                    query,
                )
            except Exception as e:
                logger.warning(f"Optimization failed, falling back to standard operation: {e}")
                self.enhanced_metrics["optimization_errors"] += 1
                # Fall back to standard operation
        
        # Standard operation
        return await super().search_memories(project_name, query)
    
    async def batch_add_memories(
        self,
        memories: List[Dict[str, Any]],
        project_name: str,
    ) -> List[Optional[str]]:
        """Enhanced batch memory addition."""
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")
        
        if not memories:
            return []
        
        # Use optimization for batch operations
        if self.optimizer and self.enhanced_metrics["optimization_enabled"]:
            try:
                # Create batch operations
                operations = []
                for memory_data in memories:
                    operation = lambda data=memory_data: self.optimizer.optimized_add_memory(
                        self.active_backend,
                        project_name,
                        data["content"],
                        MemoryCategory.from_string(data.get("category", "project")),
                        data.get("tags"),
                        data.get("metadata"),
                    )
                    operations.append(operation)
                
                self.enhanced_metrics["enhanced_operations"] += len(operations)
                return await self.optimizer.optimized_batch_operations(operations)
                
            except Exception as e:
                logger.warning(f"Batch optimization failed: {e}")
                self.enhanced_metrics["optimization_errors"] += 1
        
        # Fallback to sequential operations
        results = []
        for memory_data in memories:
            try:
                memory_id = await self.add_memory(
                    project_name,
                    memory_data["content"],
                    MemoryCategory.from_string(memory_data.get("category", "project")),
                    memory_data.get("tags"),
                    memory_data.get("metadata"),
                )
                results.append(memory_id)
            except Exception as e:
                logger.error(f"Failed to add batch memory: {e}")
                results.append(None)
        
        return results
    
    async def concurrent_validation_test(
        self,
        project_name: str = "validation_test",
        num_operations: int = 10,
    ) -> Dict[str, Any]:
        """Perform concurrent validation test to verify system stability."""
        if not self._initialized:
            raise MemoryServiceError("Memory service not initialized")
        
        if self.optimizer and self.enhanced_metrics["optimization_enabled"]:
            # Create validation functions
            validation_functions = []
            
            # Memory addition validations
            for i in range(num_operations // 2):
                async def add_validation(operation_id=i):
                    return await self.add_memory(
                        project_name,
                        f"Concurrent validation memory {operation_id}",
                        MemoryCategory.QA,
                        tags=[f"validation_{operation_id}"],
                        metadata={"validation_type": "concurrent", "operation_id": operation_id}
                    )
                validation_functions.append(add_validation)
            
            # Memory search validations
            for i in range(num_operations // 2):
                async def search_validation(operation_id=i):
                    return await self.search_memories(
                        project_name,
                        MemoryQuery(f"validation {operation_id}", category=MemoryCategory.QA, limit=5)
                    )
                validation_functions.append(search_validation)
            
            # Execute concurrent validations
            return await self.optimizer.optimized_concurrent_validation(
                validation_functions,
                project_name
            )
        else:
            # Fallback validation without optimization
            results = {
                "total_validations": num_operations,
                "successful_validations": 0,
                "failed_validations": 0,
                "validation_errors": [],
                "overall_success": False,
            }
            
            try:
                # Simple sequential validation
                for i in range(num_operations):
                    await self.add_memory(
                        project_name,
                        f"Validation memory {i}",
                        MemoryCategory.QA,
                        metadata={"validation_id": i}
                    )
                    results["successful_validations"] += 1
                    
                results["overall_success"] = True
                
            except Exception as e:
                results["failed_validations"] += 1
                results["validation_errors"].append(str(e))
            
            return results
    
    async def get_enhanced_service_health(self) -> Dict[str, Any]:
        """Get comprehensive service health including optimization metrics."""
        health_data = await super().get_service_health()
        
        # Add enhancement metrics
        health_data["enhancement"] = self.enhanced_metrics.copy()
        
        # Add optimizer metrics if available
        if self.optimizer:
            health_data["enhancement"]["optimization_metrics"] = self.optimizer.get_performance_metrics()
        
        return health_data
    
    async def tune_performance(self) -> Dict[str, Any]:
        """Auto-tune performance based on current metrics."""
        if not self.optimizer:
            return {"error": "Optimization not enabled"}
        
        metrics = self.optimizer.get_performance_metrics()
        tuning_results = {
            "original_config": self.optimization_config.copy(),
            "adjustments_made": [],
            "new_config": {},
        }
        
        # Analyze performance and make adjustments
        avg_time = metrics.get("avg_operation_time", 0)
        timeout_rate = metrics.get("timeout_operations", 0) / max(metrics.get("total_operations", 1), 1)
        
        # Adjust timeout if too many timeouts
        if timeout_rate > 0.1:  # More than 10% timeouts
            new_timeout = min(self.optimization_config["operation_timeout"] * 1.5, 30.0)
            self.optimization_config["operation_timeout"] = new_timeout
            tuning_results["adjustments_made"].append(f"Increased timeout to {new_timeout}s")
        
        # Adjust concurrency if operations are slow
        if avg_time > 5.0:  # Average operation > 5s
            new_concurrency = max(self.optimization_config["max_concurrent_ops"] // 2, 2)
            self.optimization_config["max_concurrent_ops"] = new_concurrency
            tuning_results["adjustments_made"].append(f"Reduced concurrency to {new_concurrency}")
        
        # Adjust batch size based on success rate
        success_rate = metrics.get("successful_operations", 0) / max(metrics.get("total_operations", 1), 1)
        if success_rate < 0.8:  # Less than 80% success
            new_batch_size = max(self.optimization_config["batch_size"] - 1, 1)
            self.optimization_config["batch_size"] = new_batch_size
            tuning_results["adjustments_made"].append(f"Reduced batch size to {new_batch_size}")
        
        tuning_results["new_config"] = self.optimization_config.copy()
        
        # Apply tuning if any adjustments were made
        if tuning_results["adjustments_made"]:
            # Create new optimizer with updated config
            await self.optimizer.stop()
            self.optimizer = AsyncMemoryOperationOptimizer(self.optimization_config)
            await self.optimizer.start()
            logger.info(f"Performance tuning applied: {tuning_results['adjustments_made']}")
        
        return tuning_results
    
    async def cleanup(self):
        """Enhanced cleanup including optimizer."""
        # Cleanup optimizer
        if self.optimizer:
            try:
                await self.optimizer.stop()
                logger.info("Async memory optimizer stopped")
            except Exception as e:
                logger.warning(f"Error stopping optimizer: {e}")
        
        # Cleanup base service
        await super().cleanup()
        
        logger.info("Enhanced flexible memory service cleanup completed")


# Factory function for enhanced service
def create_enhanced_memory_service(config: Optional[Dict[str, Any]] = None) -> EnhancedFlexibleMemoryService:
    """
    Factory function to create an EnhancedFlexibleMemoryService.
    
    Args:
        config: Service configuration
        
    Returns:
        EnhancedFlexibleMemoryService: Enhanced memory service instance
    """
    return EnhancedFlexibleMemoryService(config)


# Context manager for enhanced memory operations
@asynccontextmanager
async def enhanced_memory_service(config: Optional[Dict[str, Any]] = None):
    """Context manager for enhanced memory service."""
    service = create_enhanced_memory_service(config)
    try:
        await service.initialize()
        yield service
    finally:
        await service.cleanup()