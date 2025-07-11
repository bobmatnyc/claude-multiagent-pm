"""
Circuit Breaker Pattern Implementation for AI Operations

This module implements the circuit breaker pattern for resilient AI service operations.
It provides automatic failure detection and recovery mechanisms with enterprise-grade
monitoring and configuration.
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Callable, Any, Dict, Optional, List
from dataclasses import dataclass

from ..memory.interfaces.exceptions import CircuitBreakerOpenError


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: float = 60.0  # Seconds before attempting recovery
    test_requests: int = 3  # Number of test requests in half-open state
    success_threshold: int = 2  # Successes needed to close circuit
    slow_call_threshold: float = 10.0  # Seconds after which call is considered slow
    slow_call_rate_threshold: float = 0.6  # Percentage of slow calls that triggers open
    max_failure_rate: float = 0.5  # Maximum failure rate before opening


class CircuitBreaker:
    """
    Circuit breaker implementation for AI service resilience.

    The circuit breaker monitors operations and automatically opens when
    failures exceed a threshold, preventing cascading failures. It attempts
    recovery after a timeout period.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.slow_call_count = 0
        self.total_calls = 0
        self.last_failure_time = 0
        self.test_request_count = 0
        self.success_count = 0
        self.consecutive_failures = 0
        self.logger = logging.getLogger(__name__)

        # Enhanced metrics for AI operations
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "slow_requests": 0,
            "circuit_opens": 0,
            "circuit_closes": 0,
            "fallback_triggers": 0,
            "recovery_attempts": 0,
            "timeout_requests": 0,
            "rate_limit_hits": 0,
            "cost_threshold_breaches": 0,
        }

        # Response time tracking
        self.response_times = []
        self.max_response_time_history = 100

        # State lock for thread safety
        self._lock = asyncio.Lock()

        # AI-specific failure tracking
        self.ai_failure_types = {
            "timeout": 0,
            "rate_limit": 0,
            "auth_failure": 0,
            "quota_exceeded": 0,
            "model_unavailable": 0,
            "invalid_request": 0,
            "server_error": 0,
        }

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Any: Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        async with self._lock:
            self.metrics["total_requests"] += 1

            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.test_request_count = 0
                    self.success_count = 0
                    self.metrics["recovery_attempts"] += 1
                    self.logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    self.metrics["fallback_triggers"] += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                    )

        # Execute function with timing
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            async with self._lock:
                await self._on_success(execution_time)

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            async with self._lock:
                await self._on_failure(execution_time, e)

            raise

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        return (
            self.state == CircuitState.OPEN
            and time.time() - self.last_failure_time >= self.config.recovery_timeout
        )

    async def _on_success(self, execution_time: float):
        """Handle successful request."""
        self.metrics["successful_requests"] += 1
        self.total_calls += 1
        self.consecutive_failures = 0

        # Track response time
        self.response_times.append(execution_time)
        if len(self.response_times) > self.max_response_time_history:
            self.response_times.pop(0)

        # Check if call was slow
        if execution_time > self.config.slow_call_threshold:
            self.slow_call_count += 1
            self.metrics["slow_requests"] += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self.test_request_count += 1

            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.slow_call_count = 0
                self.total_calls = 0
                self.consecutive_failures = 0
                self.metrics["circuit_closes"] += 1
                self.logger.info("Circuit breaker reset to CLOSED state")
        else:
            # In CLOSED state, reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)

    async def _on_failure(self, execution_time: float, exception: Exception):
        """Handle failed request."""
        self.metrics["failed_requests"] += 1
        self.failure_count += 1
        self.total_calls += 1
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

        # Track response time even for failures
        self.response_times.append(execution_time)
        if len(self.response_times) > self.max_response_time_history:
            self.response_times.pop(0)

        # Categorize AI-specific failures
        self._categorize_ai_failure(exception)

        # Check if call was slow
        if execution_time > self.config.slow_call_threshold:
            self.slow_call_count += 1
            self.metrics["slow_requests"] += 1

        if self.state == CircuitState.HALF_OPEN:
            self.test_request_count += 1

            if self.test_request_count >= self.config.test_requests:
                self.state = CircuitState.OPEN
                self.metrics["circuit_opens"] += 1
                self.logger.warning("Circuit breaker moved to OPEN state after test failures")

        elif self.state == CircuitState.CLOSED:
            should_open = False

            # Check consecutive failures
            if self.consecutive_failures >= self.config.failure_threshold:
                should_open = True
                self.logger.warning(
                    f"Circuit breaker opening due to {self.consecutive_failures} consecutive failures"
                )

            # Check failure rate
            elif self.total_calls >= self.config.failure_threshold:
                failure_rate = self.failure_count / self.total_calls
                if failure_rate >= self.config.max_failure_rate:
                    should_open = True
                    self.logger.warning(
                        f"Circuit breaker opening due to failure rate: {failure_rate:.2%}"
                    )

                # Check slow call rate
                slow_call_rate = self.slow_call_count / self.total_calls
                if slow_call_rate >= self.config.slow_call_rate_threshold:
                    should_open = True
                    self.logger.warning(
                        f"Circuit breaker opening due to slow call rate: {slow_call_rate:.2%}"
                    )

            if should_open:
                self.state = CircuitState.OPEN
                self.metrics["circuit_opens"] += 1

    def _categorize_ai_failure(self, exception: Exception):
        """Categorize AI-specific failures."""
        error_str = str(exception).lower()

        if "timeout" in error_str:
            self.ai_failure_types["timeout"] += 1
            self.metrics["timeout_requests"] += 1
        elif "rate limit" in error_str or "429" in error_str:
            self.ai_failure_types["rate_limit"] += 1
            self.metrics["rate_limit_hits"] += 1
        elif "auth" in error_str or "401" in error_str:
            self.ai_failure_types["auth_failure"] += 1
        elif "quota" in error_str or "exceeded" in error_str:
            self.ai_failure_types["quota_exceeded"] += 1
        elif "model" in error_str and "unavailable" in error_str:
            self.ai_failure_types["model_unavailable"] += 1
        elif "invalid" in error_str or "400" in error_str:
            self.ai_failure_types["invalid_request"] += 1
        elif "5" in error_str and "server" in error_str:
            self.ai_failure_types["server_error"] += 1

    async def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state information."""
        async with self._lock:
            slow_call_rate = (
                (self.slow_call_count / self.total_calls) if self.total_calls > 0 else 0
            )
            failure_rate = (self.failure_count / self.total_calls) if self.total_calls > 0 else 0
            avg_response_time = (
                sum(self.response_times) / len(self.response_times) if self.response_times else 0
            )

            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "consecutive_failures": self.consecutive_failures,
                "slow_call_count": self.slow_call_count,
                "total_calls": self.total_calls,
                "failure_rate": failure_rate,
                "slow_call_rate": slow_call_rate,
                "last_failure_time": self.last_failure_time,
                "test_request_count": self.test_request_count,
                "success_count": self.success_count,
                "time_since_last_failure": time.time() - self.last_failure_time,
                "average_response_time": avg_response_time,
                "metrics": self.metrics.copy(),
                "ai_failure_types": self.ai_failure_types.copy(),
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "test_requests": self.config.test_requests,
                    "success_threshold": self.config.success_threshold,
                    "slow_call_threshold": self.config.slow_call_threshold,
                    "slow_call_rate_threshold": self.config.slow_call_rate_threshold,
                    "max_failure_rate": self.config.max_failure_rate,
                },
            }

    async def reset(self):
        """Manually reset circuit breaker."""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.slow_call_count = 0
            self.total_calls = 0
            self.consecutive_failures = 0
            self.test_request_count = 0
            self.success_count = 0
            self.response_times.clear()
            self.ai_failure_types = {key: 0 for key in self.ai_failure_types}
            self.logger.info("Circuit breaker manually reset")

    async def force_open(self):
        """Manually force circuit breaker open."""
        async with self._lock:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            self.metrics["circuit_opens"] += 1
            self.logger.warning("Circuit breaker manually forced OPEN")

    async def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        async with self._lock:
            return self.state == CircuitState.OPEN

    async def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open."""
        async with self._lock:
            return self.state == CircuitState.HALF_OPEN

    async def is_closed(self) -> bool:
        """Check if circuit breaker is closed."""
        async with self._lock:
            return self.state == CircuitState.CLOSED

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        metrics = self.metrics.copy()
        metrics["ai_failure_types"] = self.ai_failure_types.copy()
        return metrics

    def reset_metrics(self):
        """Reset circuit breaker metrics."""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "slow_requests": 0,
            "circuit_opens": 0,
            "circuit_closes": 0,
            "fallback_triggers": 0,
            "recovery_attempts": 0,
            "timeout_requests": 0,
            "rate_limit_hits": 0,
            "cost_threshold_breaches": 0,
        }
        self.ai_failure_types = {key: 0 for key in self.ai_failure_types}

    def __repr__(self) -> str:
        """String representation of circuit breaker."""
        return (
            f"CircuitBreaker(state={self.state.value}, "
            f"failure_count={self.failure_count}, "
            f"total_calls={self.total_calls})"
        )


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.

    This class manages circuit breakers for different AI providers or operations,
    allowing for independent failure tracking and recovery.
    """

    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker manager.

        Args:
            default_config: Default configuration for new circuit breakers
        """
        self.default_config = default_config or CircuitBreakerConfig()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = logging.getLogger(__name__)

    def get_circuit_breaker(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker.

        Args:
            name: Circuit breaker name
            config: Optional custom configuration

        Returns:
            CircuitBreaker: Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            cb_config = config or self.default_config
            self.circuit_breakers[name] = CircuitBreaker(cb_config)
            self.logger.debug(f"Created circuit breaker for {name}")

        return self.circuit_breakers[name]

    async def call_with_circuit_breaker(
        self,
        name: str,
        func: Callable,
        *args,
        config: Optional[CircuitBreakerConfig] = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with named circuit breaker.

        Args:
            name: Circuit breaker name
            func: Function to execute
            *args: Function arguments
            config: Optional custom configuration
            **kwargs: Function keyword arguments

        Returns:
            Any: Function result
        """
        circuit_breaker = self.get_circuit_breaker(name, config)
        return await circuit_breaker.call(func, *args, **kwargs)

    async def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers."""
        states = {}
        for name, cb in self.circuit_breakers.items():
            states[name] = await cb.get_state()
        return states

    async def reset_all(self):
        """Reset all circuit breakers."""
        for name, cb in self.circuit_breakers.items():
            await cb.reset()
            self.logger.info(f"Reset circuit breaker for {name}")

    async def reset_circuit_breaker(self, name: str):
        """Reset a specific circuit breaker."""
        if name in self.circuit_breakers:
            await self.circuit_breakers[name].reset()
            self.logger.info(f"Reset circuit breaker for {name}")

    def remove_circuit_breaker(self, name: str):
        """Remove a circuit breaker."""
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            self.logger.info(f"Removed circuit breaker for {name}")

    def get_circuit_breaker_names(self) -> List[str]:
        """Get names of all circuit breakers."""
        return list(self.circuit_breakers.keys())

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all circuit breakers."""
        return {
            "total_circuit_breakers": len(self.circuit_breakers),
            "open_circuit_breakers": sum(
                1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.OPEN
            ),
            "half_open_circuit_breakers": sum(
                1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.HALF_OPEN
            ),
            "closed_circuit_breakers": sum(
                1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.CLOSED
            ),
            "circuit_breaker_names": list(self.circuit_breakers.keys()),
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary of all circuit breakers."""
        summary = self.get_summary()

        # Calculate overall health
        total_cbs = summary["total_circuit_breakers"]
        open_cbs = summary["open_circuit_breakers"]

        if total_cbs == 0:
            health_status = "unknown"
        elif open_cbs == 0:
            health_status = "healthy"
        elif open_cbs < total_cbs * 0.3:
            health_status = "degraded"
        else:
            health_status = "unhealthy"

        return {
            **summary,
            "health_status": health_status,
            "health_percentage": ((total_cbs - open_cbs) / total_cbs * 100) if total_cbs > 0 else 0,
        }
