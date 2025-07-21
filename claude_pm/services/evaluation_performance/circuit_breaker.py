"""
Circuit breaker pattern for evaluation system reliability.

Protects against cascading failures and provides fallback behavior.
"""

import logging
import threading
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit breaker active
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern for evaluation system reliability.
    
    Protects against cascading failures and provides fallback behavior.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Timeout before attempting half-open
            success_threshold: Number of successes to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        
        self.lock = threading.RLock()
        
        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, timeout={timeout_seconds}s")
    
    def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Awaitable[Any]:
        """Execute function with circuit breaker protection."""
        return self._call_async(func, *args, **kwargs)
    
    async def _call_async(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN - calls are blocked")
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).total_seconds() > self.timeout_seconds
    
    def _record_success(self) -> None:
        """Record successful operation."""
        with self.lock:
            self.success_count += 1
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.success_count >= self.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("Circuit breaker CLOSED - normal operation resumed")
    
    def _record_failure(self) -> None:
        """Record failed operation."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    logger.warning(f"Circuit breaker OPEN - blocking calls after {self.failure_count} failures")
            elif self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                logger.warning("Circuit breaker returned to OPEN state after failure in HALF_OPEN")
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        with self.lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.failure_threshold,
                "timeout_seconds": self.timeout_seconds,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
            }