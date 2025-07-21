"""
Performance metrics tracking for evaluation system.
"""

from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0
    peak_memory_usage: float = 0.0
    error_count: int = 0
    circuit_breaker_trips: int = 0
    
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    def error_rate(self) -> float:
        """Calculate error rate."""
        return (self.error_count / self.total_requests * 100) if self.total_requests > 0 else 0.0