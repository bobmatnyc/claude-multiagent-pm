"""
Auto-Detection Engine

This module implements intelligent backend detection with performance profiling
and health checking capabilities.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from ..interfaces.backend import MemoryBackend
from ..interfaces.models import BackendHealth, HealthStatus


@dataclass
class DetectionResult:
    """Result of backend detection."""
    backend_name: str
    backend: MemoryBackend
    health: BackendHealth
    score: float
    selection_reason: str


class AutoDetectionEngine:
    """
    Intelligent backend detection with performance profiling.
    
    This engine evaluates available backends based on:
    - Health status and response time
    - Feature capabilities
    - Performance history
    - Configuration preferences
    """
    
    def __init__(self, timeout: float = 2.0, retry_attempts: int = 3):
        """
        Initialize auto-detection engine.
        
        Args:
            timeout: Timeout for health checks in seconds
            retry_attempts: Number of retry attempts for health checks
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.logger = logging.getLogger(__name__)
        
        # Health cache
        self.health_cache: Dict[str, BackendHealth] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Performance history
        self.performance_history: Dict[str, List[float]] = {}
        self.max_history_size = 100
        
        # Detection preferences
        self.backend_preferences = {
            "mem0ai": {
                "priority": 4,
                "features": ["similarity_search", "advanced_indexing"],
                "min_response_time": 0.1,
                "max_response_time": 5.0
            },
            "sqlite": {
                "priority": 3,
                "features": ["full_text_search", "backup", "transactions"],
                "min_response_time": 0.01,
                "max_response_time": 1.0
            },
            "tinydb": {
                "priority": 2,
                "features": ["simplicity", "json_storage"],
                "min_response_time": 0.01,
                "max_response_time": 0.5
            },
            "memory": {
                "priority": 1,
                "features": ["speed", "testing"],
                "min_response_time": 0.001,
                "max_response_time": 0.1
            }
        }
    
    async def detect_best_backend(
        self,
        backends: Dict[str, MemoryBackend],
        priority_order: List[str] = None
    ) -> Optional[DetectionResult]:
        """
        Detect the best available backend based on priority and health.
        
        Args:
            backends: Available backends
            priority_order: Optional custom priority order
            
        Returns:
            Optional[DetectionResult]: Best backend or None if none available
        """
        if not backends:
            self.logger.warning("No backends provided for detection")
            return None
        
        # Use custom priority order or default
        if priority_order:
            ordered_backends = [name for name in priority_order if name in backends]
            # Add any backends not in priority_order
            ordered_backends.extend([name for name in backends if name not in ordered_backends])
        else:
            # Sort by default priority
            ordered_backends = sorted(
                backends.keys(),
                key=lambda name: self.backend_preferences.get(name, {}).get("priority", 0),
                reverse=True
            )
        
        # Check health of all backends concurrently
        health_results = await self._check_all_backends_health(backends)
        
        # Score and rank backends
        candidates = []
        for backend_name in ordered_backends:
            if backend_name in health_results:
                health = health_results[backend_name]
                backend = backends[backend_name]
                
                if health.is_healthy:
                    score = self._calculate_backend_score(backend_name, health, backend)
                    candidates.append(DetectionResult(
                        backend_name=backend_name,
                        backend=backend,
                        health=health,
                        score=score,
                        selection_reason=self._get_selection_reason(backend_name, health, score)
                    ))
        
        if not candidates:
            self.logger.warning("No healthy backends detected")
            return None
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        best_candidate = candidates[0]
        self.logger.info(f"Selected backend: {best_candidate.backend_name} (score: {best_candidate.score:.2f})")
        self.logger.info(f"Selection reason: {best_candidate.selection_reason}")
        
        # Log other candidates for debugging
        for candidate in candidates[1:]:
            self.logger.debug(f"Alternative: {candidate.backend_name} (score: {candidate.score:.2f})")
        
        return best_candidate
    
    async def _check_all_backends_health(
        self,
        backends: Dict[str, MemoryBackend]
    ) -> Dict[str, BackendHealth]:
        """Check health of all backends concurrently."""
        health_results = {}
        
        # Check cache first
        current_time = time.time()
        for name, backend in backends.items():
            cached_health = self._get_cached_health(name)
            if cached_health and (current_time - cached_health.last_checked) < self.cache_ttl:
                health_results[name] = cached_health
                continue
        
        # Check remaining backends
        backends_to_check = {
            name: backend for name, backend in backends.items()
            if name not in health_results
        }
        
        if backends_to_check:
            tasks = []
            for name, backend in backends_to_check.items():
                task = asyncio.create_task(
                    self._check_backend_health_with_retry(name, backend),
                    name=f"health_check_{name}"
                )
                tasks.append(task)
            
            # Wait for all health checks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                task_name = tasks[i].get_name()
                backend_name = task_name.replace("health_check_", "")
                
                if isinstance(result, Exception):
                    self.logger.error(f"Health check failed for {backend_name}: {result}")
                    health_results[backend_name] = BackendHealth(
                        backend_name=backend_name,
                        is_healthy=False,
                        response_time=float('inf'),
                        error_message=str(result)
                    )
                else:
                    health_results[backend_name] = result
        
        return health_results
    
    async def _check_backend_health_with_retry(
        self,
        name: str,
        backend: MemoryBackend
    ) -> BackendHealth:
        """Check backend health with retry logic."""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                health = await self._check_backend_health(name, backend)
                
                # Cache successful health check
                self.health_cache[name] = health
                
                # Update performance history
                self._update_performance_history(name, health.response_time)
                
                return health
                
            except Exception as e:
                last_error = e
                self.logger.debug(f"Health check attempt {attempt + 1} failed for {name}: {e}")
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
        
        # All attempts failed
        health = BackendHealth(
            backend_name=name,
            is_healthy=False,
            response_time=float('inf'),
            error_message=str(last_error)
        )
        
        self.health_cache[name] = health
        return health
    
    async def _check_backend_health(
        self,
        name: str,
        backend: MemoryBackend
    ) -> BackendHealth:
        """Check individual backend health with timeout."""
        start_time = time.time()
        
        try:
            # Initialize backend if not already initialized
            if not backend.is_initialized():
                init_success = await asyncio.wait_for(
                    backend.initialize(),
                    timeout=self.timeout
                )
                if not init_success:
                    raise Exception("Backend initialization failed")
            
            # Perform health check
            health_check = asyncio.wait_for(
                backend.health_check(),
                timeout=self.timeout
            )
            
            is_healthy = await health_check
            response_time = time.time() - start_time
            
            # Get backend features
            features = backend.get_features()
            
            health = BackendHealth(
                backend_name=name,
                is_healthy=is_healthy,
                response_time=response_time,
                features=features,
                last_checked=time.time()
            )
            
            if is_healthy:
                health.consecutive_successes += 1
                health.consecutive_failures = 0
            else:
                health.consecutive_failures += 1
                health.consecutive_successes = 0
            
            return health
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            health = BackendHealth(
                backend_name=name,
                is_healthy=False,
                response_time=response_time,
                error_message=f"Timeout after {self.timeout}s",
                last_checked=time.time()
            )
            health.consecutive_failures += 1
            return health
            
        except Exception as e:
            response_time = time.time() - start_time
            health = BackendHealth(
                backend_name=name,
                is_healthy=False,
                response_time=response_time,
                error_message=str(e),
                last_checked=time.time()
            )
            health.consecutive_failures += 1
            return health
    
    def _calculate_backend_score(
        self,
        backend_name: str,
        health: BackendHealth,
        backend: MemoryBackend
    ) -> float:
        """Calculate backend score based on various factors."""
        if not health.is_healthy:
            return 0.0
        
        score = 0.0
        
        # Base priority score (0-40 points)
        base_priority = self.backend_preferences.get(backend_name, {}).get("priority", 0)
        score += base_priority * 10
        
        # Response time score (0-30 points)
        response_score = self._calculate_response_time_score(backend_name, health.response_time)
        score += response_score
        
        # Reliability score (0-20 points)
        reliability_score = self._calculate_reliability_score(health)
        score += reliability_score
        
        # Feature score (0-10 points)
        feature_score = self._calculate_feature_score(backend_name, health.features)
        score += feature_score
        
        # Bonus for consistent performance
        performance_bonus = self._calculate_performance_bonus(backend_name)
        score += performance_bonus
        
        return score
    
    def _calculate_response_time_score(self, backend_name: str, response_time: float) -> float:
        """Calculate score based on response time."""
        preferences = self.backend_preferences.get(backend_name, {})
        min_time = preferences.get("min_response_time", 0.001)
        max_time = preferences.get("max_response_time", 1.0)
        
        if response_time <= min_time:
            return 30.0
        elif response_time >= max_time:
            return 0.0
        else:
            # Linear interpolation between min and max
            normalized = (max_time - response_time) / (max_time - min_time)
            return 30.0 * normalized
    
    def _calculate_reliability_score(self, health: BackendHealth) -> float:
        """Calculate score based on reliability."""
        if health.total_requests == 0:
            return 15.0  # Neutral score for untested backends
        
        success_rate = health.get_success_rate() / 100.0
        
        # Bonus for consecutive successes
        consecutive_bonus = min(health.consecutive_successes, 10) * 0.5
        
        return success_rate * 15.0 + consecutive_bonus
    
    def _calculate_feature_score(self, backend_name: str, features: Dict[str, bool]) -> float:
        """Calculate score based on supported features."""
        preferences = self.backend_preferences.get(backend_name, {})
        preferred_features = preferences.get("features", [])
        
        if not preferred_features:
            return 5.0  # Neutral score
        
        supported_count = sum(1 for feature in preferred_features if features.get(feature, False))
        return (supported_count / len(preferred_features)) * 10.0
    
    def _calculate_performance_bonus(self, backend_name: str) -> float:
        """Calculate performance consistency bonus."""
        history = self.performance_history.get(backend_name, [])
        if len(history) < 5:
            return 0.0
        
        # Calculate coefficient of variation (lower is better)
        avg_time = sum(history) / len(history)
        if avg_time == 0:
            return 5.0
        
        variance = sum((t - avg_time) ** 2 for t in history) / len(history)
        std_dev = variance ** 0.5
        cv = std_dev / avg_time
        
        # Bonus for consistency (lower CV)
        if cv < 0.1:
            return 5.0
        elif cv < 0.3:
            return 3.0
        elif cv < 0.5:
            return 1.0
        else:
            return 0.0
    
    def _get_selection_reason(self, backend_name: str, health: BackendHealth, score: float) -> str:
        """Get human-readable selection reason."""
        reasons = []
        
        # Priority reason
        priority = self.backend_preferences.get(backend_name, {}).get("priority", 0)
        if priority >= 4:
            reasons.append("high priority")
        elif priority >= 3:
            reasons.append("medium priority")
        
        # Performance reason
        if health.response_time < 0.1:
            reasons.append("fast response")
        elif health.response_time < 1.0:
            reasons.append("good response time")
        
        # Reliability reason
        if health.consecutive_successes > 5:
            reasons.append("highly reliable")
        elif health.consecutive_successes > 0:
            reasons.append("reliable")
        
        # Feature reason
        if health.features.get("similarity_search", False):
            reasons.append("supports similarity search")
        if health.features.get("full_text_search", False):
            reasons.append("supports full-text search")
        
        if not reasons:
            reasons.append("available and healthy")
        
        return f"Selected for: {', '.join(reasons)} (score: {score:.2f})"
    
    def _update_performance_history(self, backend_name: str, response_time: float):
        """Update performance history for a backend."""
        if backend_name not in self.performance_history:
            self.performance_history[backend_name] = []
        
        history = self.performance_history[backend_name]
        history.append(response_time)
        
        # Keep only recent history
        if len(history) > self.max_history_size:
            history.pop(0)
    
    def _get_cached_health(self, backend_name: str) -> Optional[BackendHealth]:
        """Get cached health if still valid."""
        if backend_name in self.health_cache:
            health = self.health_cache[backend_name]
            if time.time() - health.last_checked < self.cache_ttl:
                return health
        return None
    
    def invalidate_cache(self, backend_name: Optional[str] = None):
        """Invalidate health cache."""
        if backend_name:
            self.health_cache.pop(backend_name, None)
        else:
            self.health_cache.clear()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary of all cached backends."""
        summary = {
            "total_backends": len(self.health_cache),
            "healthy_backends": sum(1 for h in self.health_cache.values() if h.is_healthy),
            "unhealthy_backends": sum(1 for h in self.health_cache.values() if not h.is_healthy),
            "backends": {}
        }
        
        for name, health in self.health_cache.items():
            summary["backends"][name] = {
                "healthy": health.is_healthy,
                "response_time": health.response_time,
                "last_checked": health.last_checked,
                "consecutive_successes": health.consecutive_successes,
                "consecutive_failures": health.consecutive_failures
            }
        
        return summary
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of all backends."""
        summary = {}
        
        for name, history in self.performance_history.items():
            if history:
                avg_time = sum(history) / len(history)
                min_time = min(history)
                max_time = max(history)
                
                summary[name] = {
                    "samples": len(history),
                    "avg_response_time": avg_time,
                    "min_response_time": min_time,
                    "max_response_time": max_time,
                    "recent_samples": history[-10:]  # Last 10 samples
                }
        
        return summary
    
    def configure_backend_preference(
        self,
        backend_name: str,
        priority: int = None,
        features: List[str] = None,
        min_response_time: float = None,
        max_response_time: float = None
    ):
        """Configure backend preferences."""
        if backend_name not in self.backend_preferences:
            self.backend_preferences[backend_name] = {}
        
        prefs = self.backend_preferences[backend_name]
        
        if priority is not None:
            prefs["priority"] = priority
        if features is not None:
            prefs["features"] = features
        if min_response_time is not None:
            prefs["min_response_time"] = min_response_time
        if max_response_time is not None:
            prefs["max_response_time"] = max_response_time
        
        self.logger.info(f"Updated preferences for {backend_name}: {prefs}")
    
    def clear_performance_history(self, backend_name: str = None):
        """Clear performance history."""
        if backend_name:
            self.performance_history.pop(backend_name, None)
        else:
            self.performance_history.clear()
        
        self.logger.info(f"Cleared performance history for {backend_name or 'all backends'}")
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AutoDetectionEngine(timeout={self.timeout}, "
            f"retry_attempts={self.retry_attempts}, "
            f"cached_backends={len(self.health_cache)})"
        )