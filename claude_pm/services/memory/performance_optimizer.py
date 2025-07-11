"""
Performance Optimizer

This module implements performance monitoring and optimization for the memory
recall system. It tracks recall times, cache hit rates, and provides automated
optimizations to ensure the system meets the target of sub-100ms recall operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict

from .memory_recall_service import MemoryRecallService
from .memory_context_enhancer import RecallConfig
from .similarity_matcher import MatchingConfig
from .recommendation_engine import RecommendationConfig


class OptimizationStrategy(str, Enum):
    """Available optimization strategies."""
    
    CACHE_OPTIMIZATION = "cache_optimization"
    QUERY_OPTIMIZATION = "query_optimization"
    SIMILARITY_TUNING = "similarity_tuning"
    CONCURRENT_LIMITING = "concurrent_limiting"
    MEMORY_PRUNING = "memory_pruning"
    CONFIG_TUNING = "config_tuning"


@dataclass
class PerformanceMetrics:
    """Performance metrics for memory recall operations."""
    
    # Timing metrics
    average_recall_time_ms: float = 0.0
    p95_recall_time_ms: float = 0.0
    p99_recall_time_ms: float = 0.0
    max_recall_time_ms: float = 0.0
    
    # Success metrics
    success_rate: float = 0.0
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    
    # Cache metrics
    cache_hit_rate: float = 0.0
    cache_miss_rate: float = 0.0
    cache_size: int = 0
    
    # Throughput metrics
    recalls_per_second: float = 0.0
    concurrent_recalls_avg: float = 0.0
    concurrent_recalls_peak: int = 0
    
    # Memory metrics
    total_memories_processed: int = 0
    avg_memories_per_recall: float = 0.0
    similarity_calculations_per_recall: float = 0.0
    
    # Quality metrics
    avg_confidence_score: float = 0.0
    recommendations_per_recall: float = 0.0
    
    def meets_performance_targets(self) -> bool:
        """Check if metrics meet performance targets."""
        return (
            self.average_recall_time_ms <= 100.0 and
            self.p95_recall_time_ms <= 200.0 and
            self.success_rate >= 0.95 and
            self.cache_hit_rate >= 0.3
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timing": {
                "average_recall_time_ms": self.average_recall_time_ms,
                "p95_recall_time_ms": self.p95_recall_time_ms,
                "p99_recall_time_ms": self.p99_recall_time_ms,
                "max_recall_time_ms": self.max_recall_time_ms
            },
            "success": {
                "success_rate": self.success_rate,
                "error_rate": self.error_rate,
                "timeout_rate": self.timeout_rate
            },
            "cache": {
                "cache_hit_rate": self.cache_hit_rate,
                "cache_miss_rate": self.cache_miss_rate,
                "cache_size": self.cache_size
            },
            "throughput": {
                "recalls_per_second": self.recalls_per_second,
                "concurrent_recalls_avg": self.concurrent_recalls_avg,
                "concurrent_recalls_peak": self.concurrent_recalls_peak
            },
            "memory": {
                "total_memories_processed": self.total_memories_processed,
                "avg_memories_per_recall": self.avg_memories_per_recall,
                "similarity_calculations_per_recall": self.similarity_calculations_per_recall
            },
            "quality": {
                "avg_confidence_score": self.avg_confidence_score,
                "recommendations_per_recall": self.recommendations_per_recall
            },
            "performance_targets_met": self.meets_performance_targets()
        }


@dataclass
class OptimizationRecommendation:
    """Recommendation for performance optimization."""
    
    strategy: OptimizationStrategy
    priority: str  # "high", "medium", "low"
    description: str
    expected_improvement: str
    implementation_effort: str
    config_changes: Dict[str, Any]
    rationale: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "strategy": self.strategy.value,
            "priority": self.priority,
            "description": self.description,
            "expected_improvement": self.expected_improvement,
            "implementation_effort": self.implementation_effort,
            "config_changes": self.config_changes,
            "rationale": self.rationale
        }


class PerformanceOptimizer:
    """
    Performance monitoring and optimization for memory recall system.
    
    This class monitors recall performance in real-time and provides automatic
    optimizations to ensure sub-100ms recall times while maintaining quality.
    It tracks various performance metrics and suggests configuration tuning.
    """
    
    def __init__(self, recall_service: MemoryRecallService):
        """
        Initialize the performance optimizer.
        
        Args:
            recall_service: Memory recall service to optimize
        """
        self.recall_service = recall_service
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.recall_times = deque(maxlen=1000)  # Last 1000 recall times
        self.success_history = deque(maxlen=1000)  # Success/failure history
        self.cache_hit_history = deque(maxlen=1000)  # Cache hit history
        self.concurrent_recalls_history = deque(maxlen=1000)  # Concurrency history
        
        # Optimization state
        self.optimization_history = []
        self.last_optimization_time = 0.0
        self.optimization_cooldown = 300  # 5 minutes between optimizations
        
        # Performance targets
        self.target_recall_time_ms = 100.0
        self.target_success_rate = 0.95
        self.target_cache_hit_rate = 0.3
        
        # Monitoring configuration
        self.monitoring_enabled = True
        self.auto_optimization_enabled = True
        self.optimization_aggressiveness = "moderate"  # "conservative", "moderate", "aggressive"
        
        # Start monitoring task
        self._monitoring_task = None
        self._stop_monitoring = False
    
    async def start_monitoring(self):
        """Start performance monitoring."""
        if self._monitoring_task is not None:
            return
        
        self._stop_monitoring = False
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring."""
        if self._monitoring_task is None:
            return
        
        self._stop_monitoring = True
        await self._monitoring_task
        self._monitoring_task = None
        self.logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self._stop_monitoring:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()
                
                # Check if optimization is needed
                if self.auto_optimization_enabled:
                    await self._check_and_optimize(metrics)
                
                # Wait before next collection
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """
        Collect current performance metrics.
        
        Returns:
            PerformanceMetrics: Current performance metrics
        """
        # Get service stats
        service_stats = self.recall_service.get_performance_stats()
        
        # Calculate timing metrics
        timing_metrics = self._calculate_timing_metrics()
        
        # Calculate success metrics
        success_metrics = self._calculate_success_metrics(service_stats)
        
        # Calculate cache metrics
        cache_metrics = self._calculate_cache_metrics(service_stats)
        
        # Calculate throughput metrics
        throughput_metrics = self._calculate_throughput_metrics(service_stats)
        
        # Calculate memory processing metrics
        memory_metrics = self._calculate_memory_metrics(service_stats)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(service_stats)
        
        return PerformanceMetrics(
            **timing_metrics,
            **success_metrics,
            **cache_metrics,
            **throughput_metrics,
            **memory_metrics,
            **quality_metrics
        )
    
    def _calculate_timing_metrics(self) -> Dict[str, float]:
        """Calculate timing-related metrics."""
        if not self.recall_times:
            return {
                "average_recall_time_ms": 0.0,
                "p95_recall_time_ms": 0.0,
                "p99_recall_time_ms": 0.0,
                "max_recall_time_ms": 0.0
            }
        
        times = sorted(self.recall_times)
        count = len(times)
        
        return {
            "average_recall_time_ms": sum(times) / count,
            "p95_recall_time_ms": times[int(count * 0.95)] if count > 0 else 0.0,
            "p99_recall_time_ms": times[int(count * 0.99)] if count > 0 else 0.0,
            "max_recall_time_ms": max(times) if times else 0.0
        }
    
    def _calculate_success_metrics(self, service_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate success-related metrics."""
        total_recalls = service_stats.get("total_recalls", 0)
        successful_recalls = service_stats.get("successful_recalls", 0)
        failed_recalls = service_stats.get("failed_recalls", 0)
        
        if total_recalls == 0:
            return {
                "success_rate": 0.0,
                "error_rate": 0.0,
                "timeout_rate": 0.0
            }
        
        success_rate = successful_recalls / total_recalls
        error_rate = failed_recalls / total_recalls
        timeout_rate = 0.0  # Would need specific timeout tracking
        
        return {
            "success_rate": success_rate,
            "error_rate": error_rate,
            "timeout_rate": timeout_rate
        }
    
    def _calculate_cache_metrics(self, service_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate cache-related metrics."""
        component_stats = service_stats.get("component_stats", {})
        enhancer_stats = component_stats.get("memory_enhancer", {})
        
        cache_hit_rate = enhancer_stats.get("cache_hit_rate", 0.0) / 100.0  # Convert percentage
        cache_miss_rate = 1.0 - cache_hit_rate
        cache_size = enhancer_stats.get("cache_size", 0)
        
        return {
            "cache_hit_rate": cache_hit_rate,
            "cache_miss_rate": cache_miss_rate,
            "cache_size": cache_size
        }
    
    def _calculate_throughput_metrics(self, service_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate throughput-related metrics."""
        total_recalls = service_stats.get("total_recalls", 0)
        service_uptime = time.time() - service_stats.get("service_start_time", time.time())
        
        recalls_per_second = total_recalls / max(service_uptime, 1.0)
        
        concurrent_recalls_peak = service_stats.get("concurrent_recalls_peak", 0)
        concurrent_recalls_avg = sum(self.concurrent_recalls_history) / max(len(self.concurrent_recalls_history), 1)
        
        return {
            "recalls_per_second": recalls_per_second,
            "concurrent_recalls_avg": concurrent_recalls_avg,
            "concurrent_recalls_peak": concurrent_recalls_peak
        }
    
    def _calculate_memory_metrics(self, service_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate memory processing metrics."""
        component_stats = service_stats.get("component_stats", {})
        
        # These would need to be tracked by the service
        return {
            "total_memories_processed": 0,
            "avg_memories_per_recall": 0.0,
            "similarity_calculations_per_recall": 0.0
        }
    
    def _calculate_quality_metrics(self, service_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality-related metrics."""
        # These would need to be tracked by the service
        return {
            "avg_confidence_score": 0.0,
            "recommendations_per_recall": 0.0
        }
    
    async def _check_and_optimize(self, metrics: PerformanceMetrics):
        """Check if optimization is needed and apply it."""
        # Check cooldown period
        if time.time() - self.last_optimization_time < self.optimization_cooldown:
            return
        
        # Check if optimization is needed
        if metrics.meets_performance_targets():
            return
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(metrics)
        
        if not recommendations:
            return
        
        # Apply top recommendation if auto-optimization is enabled
        top_recommendation = recommendations[0]
        
        if top_recommendation.priority == "high":
            await self._apply_optimization(top_recommendation)
            self.last_optimization_time = time.time()
            
            self.logger.info(
                f"Applied optimization: {top_recommendation.strategy.value} - "
                f"{top_recommendation.description}"
            )
    
    def _generate_optimization_recommendations(
        self,
        metrics: PerformanceMetrics
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on metrics."""
        recommendations = []
        
        # Cache optimization
        if metrics.cache_hit_rate < self.target_cache_hit_rate:
            recommendations.append(OptimizationRecommendation(
                strategy=OptimizationStrategy.CACHE_OPTIMIZATION,
                priority="high" if metrics.cache_hit_rate < 0.1 else "medium",
                description="Increase cache size and TTL to improve hit rate",
                expected_improvement="20-30% reduction in recall time",
                implementation_effort="low",
                config_changes={
                    "recall_config.performance_cache_size": min(2000, metrics.cache_size * 2),
                    "cache_ttl_seconds": 600
                },
                rationale=f"Cache hit rate {metrics.cache_hit_rate:.2f} below target {self.target_cache_hit_rate:.2f}"
            ))
        
        # Query optimization
        if metrics.average_recall_time_ms > self.target_recall_time_ms:
            recommendations.append(OptimizationRecommendation(
                strategy=OptimizationStrategy.QUERY_OPTIMIZATION,
                priority="high",
                description="Reduce similarity threshold to limit memory processing",
                expected_improvement="15-25% reduction in recall time",
                implementation_effort="low",
                config_changes={
                    "recall_config.similarity_threshold": 0.8,
                    "recall_config.max_memories_per_category": 5
                },
                rationale=f"Average recall time {metrics.average_recall_time_ms:.1f}ms above target {self.target_recall_time_ms:.1f}ms"
            ))
        
        # Similarity tuning
        if metrics.similarity_calculations_per_recall > 50:
            recommendations.append(OptimizationRecommendation(
                strategy=OptimizationStrategy.SIMILARITY_TUNING,
                priority="medium",
                description="Switch to faster similarity algorithm",
                expected_improvement="10-20% reduction in recall time",
                implementation_effort="medium",
                config_changes={
                    "matching_config.default_algorithm": "cosine",
                    "matching_config.enable_fuzzy_matching": False
                },
                rationale="High number of similarity calculations per recall"
            ))
        
        # Concurrent limiting
        if metrics.concurrent_recalls_peak > 10:
            recommendations.append(OptimizationRecommendation(
                strategy=OptimizationStrategy.CONCURRENT_LIMITING,
                priority="medium",
                description="Reduce concurrent recall limit to prevent resource contention",
                expected_improvement="More stable performance under load",
                implementation_effort="low",
                config_changes={
                    "max_concurrent_recalls": min(5, metrics.concurrent_recalls_peak // 2)
                },
                rationale=f"Peak concurrent recalls {metrics.concurrent_recalls_peak} may cause contention"
            ))
        
        # Memory pruning
        if metrics.avg_memories_per_recall > 20:
            recommendations.append(OptimizationRecommendation(
                strategy=OptimizationStrategy.MEMORY_PRUNING,
                priority="low",
                description="Reduce memory age limit to focus on recent memories",
                expected_improvement="5-10% reduction in recall time",
                implementation_effort="low",
                config_changes={
                    "recall_config.max_memory_age_days": 60
                },
                rationale="High average memories per recall may indicate too broad search"
            ))
        
        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 0), reverse=True)
        
        return recommendations
    
    async def _apply_optimization(self, recommendation: OptimizationRecommendation):
        """Apply an optimization recommendation."""
        try:
            # Get current config
            current_config = self.recall_service.get_config()
            
            # Apply config changes
            for key, value in recommendation.config_changes.items():
                self._set_nested_config_value(current_config, key, value)
            
            # Update service configuration
            self.recall_service.update_config(current_config)
            
            # Record optimization
            self.optimization_history.append({
                "timestamp": time.time(),
                "strategy": recommendation.strategy.value,
                "description": recommendation.description,
                "config_changes": recommendation.config_changes
            })
            
        except Exception as e:
            self.logger.error(f"Failed to apply optimization {recommendation.strategy.value}: {e}")
    
    def _set_nested_config_value(self, config: Any, key: str, value: Any):
        """Set a nested configuration value using dot notation."""
        parts = key.split('.')
        obj = config
        
        # Navigate to the parent object
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        # Set the final value
        setattr(obj, parts[-1], value)
    
    def record_recall_performance(self, recall_time_ms: float, success: bool, cache_hit: bool):
        """
        Record performance data for a recall operation.
        
        Args:
            recall_time_ms: Time taken for the recall
            success: Whether the recall was successful
            cache_hit: Whether the recall hit cache
        """
        if self.monitoring_enabled:
            self.recall_times.append(recall_time_ms)
            self.success_history.append(success)
            self.cache_hit_history.append(cache_hit)
    
    def record_concurrent_recalls(self, count: int):
        """
        Record concurrent recalls count.
        
        Args:
            count: Number of concurrent recalls
        """
        if self.monitoring_enabled:
            self.concurrent_recalls_history.append(count)
    
    def get_optimization_recommendations(self, metrics: PerformanceMetrics = None) -> List[OptimizationRecommendation]:
        """
        Get optimization recommendations based on current or provided metrics.
        
        Args:
            metrics: Optional metrics to use (collects current if None)
            
        Returns:
            List[OptimizationRecommendation]: Optimization recommendations
        """
        if metrics is None:
            # This would be synchronous in practice, but for consistency
            return []
        
        return self._generate_optimization_recommendations(metrics)
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        Get history of applied optimizations.
        
        Returns:
            List[Dict[str, Any]]: Optimization history
        """
        return self.optimization_history.copy()
    
    def get_performance_report(self, metrics: PerformanceMetrics = None) -> Dict[str, Any]:
        """
        Get comprehensive performance report.
        
        Args:
            metrics: Optional metrics to use
            
        Returns:
            Dict[str, Any]: Performance report
        """
        if metrics is None:
            # For synchronous operation, return basic report
            return {
                "monitoring_enabled": self.monitoring_enabled,
                "auto_optimization_enabled": self.auto_optimization_enabled,
                "optimization_aggressiveness": self.optimization_aggressiveness,
                "optimization_history_count": len(self.optimization_history),
                "last_optimization_time": self.last_optimization_time
            }
        
        report = {
            "metrics": metrics.to_dict(),
            "targets": {
                "recall_time_ms": self.target_recall_time_ms,
                "success_rate": self.target_success_rate,
                "cache_hit_rate": self.target_cache_hit_rate
            },
            "configuration": {
                "monitoring_enabled": self.monitoring_enabled,
                "auto_optimization_enabled": self.auto_optimization_enabled,
                "optimization_aggressiveness": self.optimization_aggressiveness
            },
            "optimization_history": self.get_optimization_history(),
            "recommendations": self.get_optimization_recommendations(metrics)
        }
        
        return report
    
    def configure_optimization(
        self,
        auto_optimization_enabled: bool = None,
        optimization_aggressiveness: str = None,
        target_recall_time_ms: float = None,
        target_success_rate: float = None,
        target_cache_hit_rate: float = None
    ):
        """
        Configure optimization parameters.
        
        Args:
            auto_optimization_enabled: Enable/disable auto optimization
            optimization_aggressiveness: Optimization aggressiveness level
            target_recall_time_ms: Target recall time
            target_success_rate: Target success rate
            target_cache_hit_rate: Target cache hit rate
        """
        if auto_optimization_enabled is not None:
            self.auto_optimization_enabled = auto_optimization_enabled
        
        if optimization_aggressiveness is not None:
            if optimization_aggressiveness in ["conservative", "moderate", "aggressive"]:
                self.optimization_aggressiveness = optimization_aggressiveness
            else:
                raise ValueError("optimization_aggressiveness must be 'conservative', 'moderate', or 'aggressive'")
        
        if target_recall_time_ms is not None:
            self.target_recall_time_ms = target_recall_time_ms
        
        if target_success_rate is not None:
            self.target_success_rate = target_success_rate
        
        if target_cache_hit_rate is not None:
            self.target_cache_hit_rate = target_cache_hit_rate
        
        self.logger.info("Optimization configuration updated")
    
    async def cleanup(self):
        """Cleanup optimizer resources."""
        await self.stop_monitoring()
        self.logger.info("Performance optimizer cleanup completed")