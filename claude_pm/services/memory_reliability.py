#!/usr/bin/env python3
"""
Memory Reliability Service

Provides comprehensive error handling, circuit breaker integration, and automatic
recovery mechanisms for memory service failures in claude-pm CLI operations.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from contextlib import asynccontextmanager

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class MemoryServiceStatus(str, Enum):
    """Memory service status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RECOVERING = "recovering"
    OFFLINE = "offline"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3
    timeout: int = 30  # seconds
    enabled: bool = True


@dataclass
class MemoryReliabilityMetrics:
    """Memory reliability metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_breaker_trips: int = 0
    recovery_attempts: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    average_response_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100.0


class MemoryCircuitBreaker:
    """Circuit breaker for memory service operations."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.logger = get_logger(f"{__name__}.CircuitBreaker")
    
    def is_call_allowed(self) -> bool:
        """Check if a call is allowed through the circuit breaker."""
        if not self.config.enabled:
            return True
            
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record a successful call."""
        if not self.config.enabled:
            return
            
        self.failure_count = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.success_count = 0
                self.logger.info("Circuit breaker reset to CLOSED")
    
    def record_failure(self):
        """Record a failed call."""
        if not self.config.enabled:
            return
            
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            self.logger.warning("Circuit breaker opened from HALF_OPEN due to failure")
        elif (self.state == CircuitBreakerState.CLOSED and 
              self.failure_count >= self.config.failure_threshold):
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get circuit breaker state information."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "enabled": self.config.enabled,
            }
        }


class MemoryServiceRecovery:
    """Automatic recovery mechanisms for memory service."""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.logger = get_logger(f"{__name__}.Recovery")
        self.recovery_strategies = [
            self._restart_service_check,
            self._validate_configuration,
            self._test_basic_connectivity,
            self._verify_chromadb_persistence,
        ]
    
    async def attempt_recovery(self) -> bool:
        """Attempt to recover memory service."""
        self.logger.info("Starting memory service recovery process")
        
        for i, strategy in enumerate(self.recovery_strategies, 1):
            try:
                self.logger.info(f"Attempting recovery strategy {i}/{len(self.recovery_strategies)}: {strategy.__name__}")
                success = await strategy()
                if success:
                    self.logger.info(f"Recovery successful with strategy: {strategy.__name__}")
                    return True
                else:
                    self.logger.warning(f"Recovery strategy failed: {strategy.__name__}")
            except Exception as e:
                self.logger.error(f"Recovery strategy {strategy.__name__} threw exception: {e}")
        
        self.logger.error("All recovery strategies failed")
        return False
    
    async def _restart_service_check(self) -> bool:
        """Check if service needs restart."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        self.logger.info("Memory service is responding to health checks")
                        return True
        except Exception as e:
            self.logger.warning(f"Service health check failed: {e}")
        
        return False
    
    async def _validate_configuration(self) -> bool:
        """Validate memory service configuration."""
        try:
            # Check if chromadb directory exists and is accessible
            import os
            from pathlib import Path
            
            chroma_paths = ["./chroma_db", "./chroma_db_persist"]
            for path in chroma_paths:
                chroma_path = Path(path)
                if not chroma_path.exists():
                    chroma_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created ChromaDB directory: {path}")
                
                if not os.access(chroma_path, os.R_OK | os.W_OK):
                    self.logger.error(f"ChromaDB directory not accessible: {path}")
                    return False
            
            self.logger.info("ChromaDB configuration validated")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    async def _test_basic_connectivity(self) -> bool:
        """Test basic connectivity to memory service."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Test basic endpoints
                endpoints = ["/health", "/memories", "/"]
                for endpoint in endpoints:
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            if response.status in [200, 404]:  # 404 is OK for some endpoints
                                self.logger.info(f"Endpoint {endpoint} responding")
                                return True
                    except Exception as e:
                        self.logger.debug(f"Endpoint {endpoint} failed: {e}")
                        continue
        except Exception as e:
            self.logger.error(f"Connectivity test failed: {e}")
        
        return False
    
    async def _verify_chromadb_persistence(self) -> bool:
        """Verify ChromaDB persistence is working."""
        try:
            # Test data persistence by adding and retrieving a test memory
            test_data = {
                "messages": [{"role": "user", "content": "test_memory_reliability_check"}],
                "user_id": "reliability_test",
                "metadata": {"test": True, "timestamp": datetime.now().isoformat()}
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                # Add test memory
                async with session.post(f"{self.base_url}/memories", json=test_data) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to add test memory: {response.status}")
                        return False
                
                # Retrieve memories to verify persistence
                async with session.get(f"{self.base_url}/memories?user_id=reliability_test") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("count", 0) > 0:
                            self.logger.info("ChromaDB persistence verified")
                            return True
                        else:
                            self.logger.warning("No memories found after adding test memory")
                    else:
                        self.logger.error(f"Failed to retrieve test memories: {response.status}")
            
        except Exception as e:
            self.logger.error(f"ChromaDB persistence test failed: {e}")
        
        return False


class MemoryReliabilityService:
    """Comprehensive memory reliability service for CLI operations."""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.circuit_breaker = MemoryCircuitBreaker(CircuitBreakerConfig())
        self.recovery_service = MemoryServiceRecovery(base_url)
        self.metrics = MemoryReliabilityMetrics()
        self.status = MemoryServiceStatus.OFFLINE
        self.logger = get_logger(__name__)
        
        # Health monitoring
        self.last_health_check: Optional[datetime] = None
        self.health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Initialize memory reliability service."""
        self.logger.info("Initializing memory reliability service")
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_monitor_loop())
        
        # Initial health check
        is_healthy = await self._perform_health_check()
        if is_healthy:
            self.status = MemoryServiceStatus.HEALTHY
            self.logger.info("Memory reliability service initialized successfully")
        else:
            self.status = MemoryServiceStatus.UNHEALTHY
            self.logger.warning("Memory reliability service initialized with unhealthy status")
        
        return True
    
    async def cleanup(self):
        """Cleanup resources."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
    
    @asynccontextmanager
    async def safe_memory_operation(self, operation_name: str):
        """Context manager for safe memory operations with circuit breaker."""
        if not self.circuit_breaker.is_call_allowed():
            self.logger.warning(f"Circuit breaker blocked operation: {operation_name}")
            raise MemoryServiceUnavailableError("Circuit breaker is open")
        
        start_time = time.time()
        self.metrics.total_requests += 1
        
        try:
            yield
            
            # Record success
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            self.circuit_breaker.record_success()
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = datetime.now()
            
            if self.status == MemoryServiceStatus.UNHEALTHY:
                self.status = MemoryServiceStatus.RECOVERING
                
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = datetime.now()
            
            if self.circuit_breaker.state == CircuitBreakerState.OPEN:
                self.metrics.circuit_breaker_trips += 1
                self.status = MemoryServiceStatus.OFFLINE
            else:
                self.status = MemoryServiceStatus.DEGRADED
            
            self.logger.error(f"Memory operation failed: {operation_name} - {e}")
            raise
    
    async def test_memory_service(self) -> Dict[str, Any]:
        """Test memory service and return detailed results."""
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "tests": {},
            "circuit_breaker": self.circuit_breaker.get_state_info(),
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": self.metrics.success_rate,
                "failure_rate": self.metrics.failure_rate,
                "average_response_time": self.metrics.average_response_time,
            }
        }
        
        # Test basic connectivity
        try:
            async with self.safe_memory_operation("connectivity_test"):
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(f"{self.base_url}/health") as response:
                        test_results["tests"]["connectivity"] = {
                            "status": "pass" if response.status == 200 else "fail",
                            "response_code": response.status,
                            "response_time": time.time() - time.time()  # Placeholder
                        }
        except Exception as e:
            test_results["tests"]["connectivity"] = {"status": "fail", "error": str(e)}
        
        # Test memory operations
        try:
            async with self.safe_memory_operation("memory_test"):
                test_data = {
                    "messages": [{"role": "user", "content": "reliability_test"}],
                    "user_id": "test_user",
                    "metadata": {"test": True}
                }
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                    async with session.post(f"{self.base_url}/memories", json=test_data) as response:
                        test_results["tests"]["memory_operations"] = {
                            "status": "pass" if response.status == 200 else "fail",
                            "response_code": response.status
                        }
        except Exception as e:
            test_results["tests"]["memory_operations"] = {"status": "fail", "error": str(e)}
        
        # Determine overall status
        all_tests_passed = all(
            test.get("status") == "pass" 
            for test in test_results["tests"].values()
        )
        test_results["overall_status"] = "healthy" if all_tests_passed else "unhealthy"
        
        return test_results
    
    async def attempt_recovery(self) -> bool:
        """Attempt automatic recovery."""
        self.logger.info("Attempting automatic memory service recovery")
        self.metrics.recovery_attempts += 1
        self.status = MemoryServiceStatus.RECOVERING
        
        success = await self.recovery_service.attempt_recovery()
        if success:
            self.status = MemoryServiceStatus.HEALTHY
            # Reset circuit breaker on successful recovery
            self.circuit_breaker.failure_count = 0
            self.circuit_breaker.state = CircuitBreakerState.CLOSED
        else:
            self.status = MemoryServiceStatus.OFFLINE
        
        return success
    
    async def _perform_health_check(self) -> bool:
        """Perform health check."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    is_healthy = response.status == 200
                    self.last_health_check = datetime.now()
                    return is_healthy
        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            return False
    
    async def _health_monitor_loop(self):
        """Background health monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                is_healthy = await self._perform_health_check()
                
                if not is_healthy and self.status in [MemoryServiceStatus.HEALTHY, MemoryServiceStatus.RECOVERING]:
                    self.logger.warning("Memory service health degraded")
                    self.status = MemoryServiceStatus.DEGRADED
                    
                    # Attempt recovery if service is offline
                    if self.status == MemoryServiceStatus.OFFLINE:
                        await self.attempt_recovery()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
    
    def _update_response_time(self, response_time: float):
        """Update average response time."""
        if self.metrics.successful_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.average_response_time = (
                alpha * response_time + (1 - alpha) * self.metrics.average_response_time
            )
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary."""
        return {
            "status": self.status.value,
            "circuit_breaker": self.circuit_breaker.get_state_info(),
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate,
                "failure_rate": self.metrics.failure_rate,
                "circuit_breaker_trips": self.metrics.circuit_breaker_trips,
                "recovery_attempts": self.metrics.recovery_attempts,
                "average_response_time": self.metrics.average_response_time,
                "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
                "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
            },
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
        }


class MemoryServiceUnavailableError(Exception):
    """Raised when memory service is unavailable."""
    pass


# Global reliability service instance
_global_reliability_service: Optional[MemoryReliabilityService] = None


async def get_memory_reliability_service() -> MemoryReliabilityService:
    """Get or create global memory reliability service."""
    global _global_reliability_service
    if _global_reliability_service is None:
        _global_reliability_service = MemoryReliabilityService()
        await _global_reliability_service.initialize()
    return _global_reliability_service


async def cleanup_memory_reliability_service():
    """Cleanup global memory reliability service."""
    global _global_reliability_service
    if _global_reliability_service:
        await _global_reliability_service.cleanup()
        _global_reliability_service = None


if __name__ == "__main__":
    async def test_reliability_service():
        """Test the memory reliability service."""
        service = MemoryReliabilityService()
        await service.initialize()
        
        try:
            # Test memory operations
            test_results = await service.test_memory_service()
            print("Test Results:")
            print(json.dumps(test_results, indent=2))
            
            # Test recovery
            if test_results["overall_status"] != "healthy":
                print("Attempting recovery...")
                recovery_success = await service.attempt_recovery()
                print(f"Recovery successful: {recovery_success}")
            
            # Get status summary
            status = service.get_status_summary()
            print("Status Summary:")
            print(json.dumps(status, indent=2))
            
        finally:
            await service.cleanup()
    
    import json
    asyncio.run(test_reliability_service())