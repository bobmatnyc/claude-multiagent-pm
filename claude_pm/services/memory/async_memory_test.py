#!/usr/bin/env python3
"""
Async Memory System Load Testing and Validation

This script comprehensively tests the memory system for async operation issues,
timeout handling, concurrent access patterns, and performance under validation load.
"""

import asyncio
import time
import logging
import json
import random
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from pathlib import Path

# Setup logging for detailed debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import memory system components
try:
    from claude_pm.services.memory import (
        FlexibleMemoryService,
        ReleaseReadyMemoryService,
        MemoryCategory,
        MemoryQuery,
        validate_memory_system_for_release,
    )
    from claude_pm.services.memory.monitoring.health import HealthMonitor
    from claude_pm.services.memory.monitoring.performance import PerformanceMonitor
    logger.info("✅ Memory system imports successful")
except Exception as e:
    logger.error(f"❌ Failed to import memory system: {e}")
    raise


class AsyncMemoryTestSuite:
    """Comprehensive async memory system testing suite."""
    
    def __init__(self):
        self.results = {
            "test_start_time": time.time(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "timeout_errors": 0,
            "concurrent_errors": 0,
            "performance_issues": 0,
            "test_results": [],
            "memory_operations": 0,
            "avg_response_time": 0.0,
            "max_response_time": 0.0,
            "circuit_breaker_activations": 0,
        }
        self.operation_times = []
        
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run all async memory system tests."""
        logger.info("🚀 Starting comprehensive async memory system test suite")
        
        try:
            # Test 1: Basic memory service initialization
            await self.test_memory_service_initialization()
            
            # Test 2: Single operation timeout testing
            await self.test_single_operation_timeouts()
            
            # Test 3: Concurrent memory operations
            await self.test_concurrent_memory_operations()
            
            # Test 4: High-load stress testing
            await self.test_high_load_stress()
            
            # Test 5: Circuit breaker behavior under stress
            await self.test_circuit_breaker_behavior()
            
            # Test 6: Memory system validation load testing
            await self.test_validation_load_scenarios()
            
            # Test 7: Backend switching under load
            await self.test_backend_switching_under_load()
            
            # Test 8: Recovery and resilience testing
            await self.test_recovery_resilience()
            
            # Calculate final metrics
            self.calculate_final_metrics()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed with exception: {e}")
            traceback.print_exc()
            self.results["fatal_error"] = str(e)
            
        return self.results
    
    async def test_memory_service_initialization(self):
        """Test 1: Memory service initialization and basic health."""
        test_name = "Memory Service Initialization"
        logger.info(f"🧪 Running {test_name}")
        
        try:
            start_time = time.time()
            
            # Test FlexibleMemoryService initialization
            service = FlexibleMemoryService()
            init_success = await service.initialize()
            
            if not init_success:
                raise Exception("FlexibleMemoryService initialization failed")
                
            # Test health check
            health = await service.get_service_health()
            logger.info(f"Service health: {json.dumps(health, indent=2)}")
            
            # Test cleanup
            await service.cleanup()
            
            # Test ReleaseReadyMemoryService
            release_service = ReleaseReadyMemoryService()
            release_init = await release_service.initialize()
            
            if not release_init:
                raise Exception("ReleaseReadyMemoryService initialization failed")
                
            await release_service.cleanup()
            
            execution_time = time.time() - start_time
            self.record_test_result(test_name, True, execution_time, "All services initialized successfully")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_test_result(test_name, False, execution_time, f"Initialization failed: {e}")
    
    async def test_single_operation_timeouts(self):
        """Test 2: Single operation timeout behavior."""
        test_name = "Single Operation Timeouts"
        logger.info(f"🧪 Running {test_name}")
        
        try:
            start_time = time.time()
            timeout_count = 0
            
            service = FlexibleMemoryService({
                "mem0ai_timeout": 2.0,  # Short timeout to test behavior
                "detection_timeout": 1.0,
            })
            await service.initialize()
            
            # Test multiple add operations with timing
            for i in range(10):
                op_start = time.time()
                try:
                    memory_id = await service.add_memory(
                        "timeout_test",
                        f"Test memory {i} for timeout analysis",
                        MemoryCategory.BUG,
                        metadata={"test_id": i, "timestamp": time.time()}
                    )
                    op_time = time.time() - op_start
                    self.operation_times.append(op_time)
                    
                    if op_time > 5.0:  # Consider > 5s as slow
                        timeout_count += 1
                        logger.warning(f"Slow operation detected: {op_time:.2f}s")
                        
                    logger.info(f"Operation {i}: {op_time:.3f}s, ID: {memory_id}")
                    
                except asyncio.TimeoutError:
                    timeout_count += 1
                    logger.warning(f"Timeout on operation {i}")
                except Exception as e:
                    timeout_count += 1
                    logger.warning(f"Error on operation {i}: {e}")
            
            await service.cleanup()
            
            execution_time = time.time() - start_time
            avg_op_time = sum(self.operation_times) / len(self.operation_times) if self.operation_times else 0
            
            if timeout_count > 3:  # More than 30% timeouts is concerning
                raise Exception(f"Too many timeouts: {timeout_count}/10 operations")
                
            self.record_test_result(
                test_name, 
                True, 
                execution_time, 
                f"Timeouts: {timeout_count}/10, Avg time: {avg_op_time:.3f}s"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_test_result(test_name, False, execution_time, f"Timeout test failed: {e}")
    
    async def test_concurrent_memory_operations(self):
        """Test 3: Concurrent memory operations."""
        test_name = "Concurrent Memory Operations"
        logger.info(f"🧪 Running {test_name}")
        
        try:
            start_time = time.time()
            concurrent_errors = 0
            
            service = FlexibleMemoryService()
            await service.initialize()
            
            async def concurrent_memory_worker(worker_id: int, operations: int = 5):
                """Worker function for concurrent operations."""
                worker_errors = 0
                for i in range(operations):
                    try:
                        # Add memory
                        memory_id = await service.add_memory(
                            f"concurrent_test_{worker_id}",
                            f"Worker {worker_id} memory {i}",
                            MemoryCategory.INTEGRATION,
                            metadata={"worker": worker_id, "operation": i}
                        )
                        
                        # Search memory
                        results = await service.search_memories(
                            f"concurrent_test_{worker_id}",
                            MemoryQuery(f"Worker {worker_id}")
                        )
                        
                        # Brief delay to simulate real usage
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        worker_errors += 1
                        logger.warning(f"Worker {worker_id} operation {i} failed: {e}")
                        
                return worker_errors
            
            # Run 5 concurrent workers with 5 operations each
            tasks = [concurrent_memory_worker(i) for i in range(5)]
            worker_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(worker_results):
                if isinstance(result, Exception):
                    concurrent_errors += 5  # All operations failed
                    logger.error(f"Worker {i} completely failed: {result}")
                else:
                    concurrent_errors += result
            
            await service.cleanup()
            
            execution_time = time.time() - start_time
            total_operations = 25  # 5 workers * 5 operations
            
            if concurrent_errors > 5:  # More than 20% failures
                raise Exception(f"Too many concurrent errors: {concurrent_errors}/{total_operations}")
                
            self.record_test_result(
                test_name, 
                True, 
                execution_time, 
                f"Errors: {concurrent_errors}/{total_operations}"
            )
            self.results["concurrent_errors"] = concurrent_errors
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_test_result(test_name, False, execution_time, f"Concurrent test failed: {e}")
    
    async def test_high_load_stress(self):
        """Test 4: High-load stress testing."""
        test_name = "High Load Stress Test"
        logger.info(f"🧪 Running {test_name}")
        
        try:
            start_time = time.time()
            stress_errors = 0
            
            service = FlexibleMemoryService()
            await service.initialize()
            
            # High-load scenario: 50 rapid operations
            stress_operations = 50
            for i in range(stress_operations):
                try:
                    op_start = time.time()
                    
                    # Alternating operation types
                    if i % 3 == 0:
                        # Add memory
                        await service.add_memory(
                            "stress_test",
                            f"Stress test memory {i}",
                            MemoryCategory.PERFORMANCE,
                            metadata={"stress_id": i}
                        )
                    elif i % 3 == 1:
                        # Search memories
                        await service.search_memories(
                            "stress_test",
                            MemoryQuery("stress test")
                        )
                    else:
                        # Get project memories
                        await service.get_project_memories("stress_test", limit=10)
                    
                    op_time = time.time() - op_start
                    if op_time > 3.0:  # Operations taking > 3s under stress
                        stress_errors += 1
                        logger.warning(f"Slow stress operation {i}: {op_time:.2f}s")
                        
                except Exception as e:
                    stress_errors += 1
                    logger.warning(f"Stress operation {i} failed: {e}")
            
            await service.cleanup()
            
            execution_time = time.time() - start_time
            avg_time_per_op = execution_time / stress_operations
            
            if stress_errors > 10:  # More than 20% failures under stress
                raise Exception(f"Too many stress errors: {stress_errors}/{stress_operations}")
                
            self.record_test_result(
                test_name, 
                True, 
                execution_time, 
                f"Errors: {stress_errors}/{stress_operations}, Avg: {avg_time_per_op:.3f}s/op"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_test_result(test_name, False, execution_time, f"Stress test failed: {e}")
    
    async def test_circuit_breaker_behavior(self):
        """Test 5: Circuit breaker behavior under stress."""
        test_name = "Circuit Breaker Behavior"
        logger.info(f"🧪 Running {test_name}")
        
        try:
            start_time = time.time()
            
            service = FlexibleMemoryService({
                "circuit_breaker_threshold": 3,  # Low threshold for testing
                "circuit_breaker_recovery": 5,   # Short recovery for testing
            })
            await service.initialize()
            
            # Get initial circuit breaker states
            health = await service.get_service_health()
            initial_cb_state = health.get("circuit_breakers", {})
            logger.info(f"Initial circuit breaker states: {initial_cb_state}")
            
            # Force some operations to potentially trigger circuit breakers
            cb_activations = 0
            for i in range(20):
                try:
                    await service.add_memory(
                        "cb_test",
                        f"Circuit breaker test {i}",
                        MemoryCategory.QA
                    )
                    # Small delay to allow circuit breaker to react
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.info(f"Operation {i} failed (expected for CB testing): {e}")
            
            # Check final circuit breaker states
            final_health = await service.get_service_health()
            final_cb_state = final_health.get("circuit_breakers", {})
            logger.info(f"Final circuit breaker states: {final_cb_state}")
            
            # Count circuit breaker activations
            for backend_name, cb_info in final_cb_state.items():
                if cb_info.get("state") == "open":
                    cb_activations += 1
                    logger.info(f"Circuit breaker {backend_name} was activated")
            
            await service.cleanup()
            
            execution_time = time.time() - start_time
            self.results["circuit_breaker_activations"] = cb_activations
            
            self.record_test_result(
                test_name, 
                True, 
                execution_time, 
                f"Circuit breaker activations: {cb_activations}"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_test_result(test_name, False, execution_time, f"Circuit breaker test failed: {e}")
    
    async def test_validation_load_scenarios(self):
        """Test 6: Memory system validation load testing (reproduces QA issues)."""
        test_name = "Validation Load Scenarios"
        logger.info(f"🧪 Running {test_name}")
        
        try:
            start_time = time.time()
            validation_errors = 0
            
            # Test scenario 1: Multiple validation runs
            for run in range(3):
                try:
                    logger.info(f"Running validation scenario {run + 1}/3")
                    
                    # This reproduces the QA validation load
                    validation_start = time.time()
                    validation_results = await validate_memory_system_for_release()
                    validation_time = time.time() - validation_start
                    
                    logger.info(f"Validation run {run + 1} took {validation_time:.2f}s")
                    logger.info(f"Validation results: {validation_results}")
                    
                    if validation_time > 30.0:  # Validation taking > 30s is concerning
                        validation_errors += 1
                        logger.warning(f"Validation run {run + 1} was slow: {validation_time:.2f}s")
                        
                    if not validation_results.get("release_ready", False):
                        validation_errors += 1
                        logger.warning(f"Validation run {run + 1} failed readiness check")
                        
                except asyncio.TimeoutError:
                    validation_errors += 1
                    logger.error(f"Validation run {run + 1} timed out")
                except Exception as e:
                    validation_errors += 1
                    logger.error(f"Validation run {run + 1} failed: {e}")
                
                # Brief pause between validation runs
                await asyncio.sleep(1)
            
            # Test scenario 2: Validation during concurrent operations
            try:
                logger.info("Testing validation during concurrent operations")
                
                service = FlexibleMemoryService()
                await service.initialize()
                
                async def background_operations():
                    """Run background memory operations during validation."""
                    for i in range(10):
                        try:
                            await service.add_memory(
                                "validation_concurrent",
                                f"Background operation {i}",
                                MemoryCategory.INTEGRATION
                            )
                            await asyncio.sleep(0.2)
                        except Exception as e:
                            logger.warning(f"Background operation {i} failed: {e}")
                
                # Start background operations
                bg_task = asyncio.create_task(background_operations())
                
                # Run validation while background operations are running
                concurrent_validation = await validate_memory_system_for_release()
                
                # Wait for background operations to complete
                await bg_task
                await service.cleanup()
                
                if not concurrent_validation.get("release_ready", False):
                    validation_errors += 1
                    logger.warning("Concurrent validation failed")
                    
            except Exception as e:
                validation_errors += 1
                logger.error(f"Concurrent validation test failed: {e}")
            
            execution_time = time.time() - start_time
            
            if validation_errors > 1:  # Allow some margin for validation issues
                raise Exception(f"Too many validation errors: {validation_errors}")
                
            self.record_test_result(
                test_name, 
                True, 
                execution_time, 
                f"Validation errors: {validation_errors}"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_test_result(test_name, False, execution_time, f"Validation load test failed: {e}")
    
    async def test_backend_switching_under_load(self):
        """Test 7: Backend switching behavior under load."""
        test_name = "Backend Switching Under Load"
        logger.info(f"🧪 Running {test_name}")
        
        try:
            start_time = time.time()
            switching_errors = 0
            
            service = FlexibleMemoryService()
            await service.initialize()
            
            initial_backend = service.get_active_backend_name()
            logger.info(f"Initial backend: {initial_backend}")
            
            # Test backend switching with operations
            backends = service.get_backend_list()
            for backend_name in backends:
                try:
                    logger.info(f"Testing switch to {backend_name}")
                    
                    # Switch backend
                    switch_success = await service.switch_backend(backend_name)
                    if not switch_success:
                        switching_errors += 1
                        logger.warning(f"Failed to switch to {backend_name}")
                        continue
                    
                    # Test operations on switched backend
                    for i in range(3):
                        try:
                            await service.add_memory(
                                f"switch_test_{backend_name}",
                                f"Switch test {backend_name} operation {i}",
                                MemoryCategory.INTEGRATION
                            )
                        except Exception as e:
                            switching_errors += 1
                            logger.warning(f"Operation failed on {backend_name}: {e}")
                    
                except Exception as e:
                    switching_errors += 1
                    logger.error(f"Backend switching test failed for {backend_name}: {e}")
            
            await service.cleanup()
            
            execution_time = time.time() - start_time
            
            if switching_errors > 2:  # Allow some switching failures
                raise Exception(f"Too many backend switching errors: {switching_errors}")
                
            self.record_test_result(
                test_name, 
                True, 
                execution_time, 
                f"Switching errors: {switching_errors}"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_test_result(test_name, False, execution_time, f"Backend switching test failed: {e}")
    
    async def test_recovery_resilience(self):
        """Test 8: Recovery and resilience testing."""
        test_name = "Recovery and Resilience"
        logger.info(f"🧪 Running {test_name}")
        
        try:
            start_time = time.time()
            recovery_errors = 0
            
            service = FlexibleMemoryService({
                "circuit_breaker_threshold": 2,
                "circuit_breaker_recovery": 2,
            })
            await service.initialize()
            
            # Test recovery after simulated failures
            logger.info("Testing recovery after circuit breaker activation")
            
            # Force circuit breaker to open by causing failures
            for i in range(5):
                try:
                    # This might cause failures and trigger circuit breaker
                    await service.add_memory(
                        "recovery_test",
                        f"Recovery test {i}",
                        MemoryCategory.ERROR
                    )
                except Exception as e:
                    logger.info(f"Expected failure for recovery testing: {e}")
            
            # Wait for recovery timeout
            logger.info("Waiting for circuit breaker recovery...")
            await asyncio.sleep(3)
            
            # Test recovery operations
            recovery_success = 0
            for i in range(5):
                try:
                    await service.add_memory(
                        "recovery_test",
                        f"Recovery operation {i}",
                        MemoryCategory.INTEGRATION
                    )
                    recovery_success += 1
                except Exception as e:
                    recovery_errors += 1
                    logger.warning(f"Recovery operation {i} failed: {e}")
            
            logger.info(f"Recovery successful operations: {recovery_success}/5")
            
            # Test service cleanup and re-initialization
            await service.cleanup()
            
            # Re-initialize service
            new_service = FlexibleMemoryService()
            init_success = await new_service.initialize()
            
            if not init_success:
                recovery_errors += 1
                logger.error("Service re-initialization failed")
            else:
                # Test operation after re-initialization
                try:
                    await new_service.add_memory(
                        "recovery_test",
                        "Post-recovery test",
                        MemoryCategory.INTEGRATION
                    )
                except Exception as e:
                    recovery_errors += 1
                    logger.error(f"Post-recovery operation failed: {e}")
            
            await new_service.cleanup()
            
            execution_time = time.time() - start_time
            
            if recovery_errors > 2:
                raise Exception(f"Too many recovery errors: {recovery_errors}")
                
            self.record_test_result(
                test_name, 
                True, 
                execution_time, 
                f"Recovery errors: {recovery_errors}"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.record_test_result(test_name, False, execution_time, f"Recovery test failed: {e}")
    
    def record_test_result(self, test_name: str, passed: bool, execution_time: float, details: str):
        """Record individual test result."""
        self.results["tests_run"] += 1
        
        if passed:
            self.results["tests_passed"] += 1
            logger.info(f"✅ {test_name} PASSED in {execution_time:.2f}s: {details}")
        else:
            self.results["tests_failed"] += 1
            logger.error(f"❌ {test_name} FAILED in {execution_time:.2f}s: {details}")
        
        self.results["test_results"].append({
            "test_name": test_name,
            "passed": passed,
            "execution_time": execution_time,
            "details": details,
            "timestamp": time.time()
        })
    
    def calculate_final_metrics(self):
        """Calculate final test metrics."""
        total_time = time.time() - self.results["test_start_time"]
        
        if self.operation_times:
            self.results["avg_response_time"] = sum(self.operation_times) / len(self.operation_times)
            self.results["max_response_time"] = max(self.operation_times)
            self.results["memory_operations"] = len(self.operation_times)
        
        self.results["total_execution_time"] = total_time
        self.results["test_success_rate"] = (
            self.results["tests_passed"] / self.results["tests_run"]
            if self.results["tests_run"] > 0 else 0
        )
        
        # Determine overall test outcome
        if self.results["tests_failed"] == 0:
            self.results["overall_result"] = "PASS"
        elif self.results["test_success_rate"] >= 0.8:
            self.results["overall_result"] = "PARTIAL_PASS"
        else:
            self.results["overall_result"] = "FAIL"


async def main():
    """Main test execution function."""
    print("🔍 Async Memory System Validation and Load Testing")
    print("=" * 60)
    
    test_suite = AsyncMemoryTestSuite()
    results = await test_suite.run_comprehensive_test_suite()
    
    # Print comprehensive results
    print("\n📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    print(f"Overall Result: {results['overall_result']}")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    print(f"Success Rate: {results['test_success_rate']:.1%}")
    print(f"Total Execution Time: {results['total_execution_time']:.2f}s")
    
    if results.get('memory_operations', 0) > 0:
        print(f"Memory Operations: {results['memory_operations']}")
        print(f"Avg Response Time: {results['avg_response_time']:.3f}s")
        print(f"Max Response Time: {results['max_response_time']:.3f}s")
    
    print(f"Timeout Errors: {results['timeout_errors']}")
    print(f"Concurrent Errors: {results['concurrent_errors']}")
    print(f"Circuit Breaker Activations: {results['circuit_breaker_activations']}")
    
    print("\n📋 INDIVIDUAL TEST RESULTS:")
    for test_result in results['test_results']:
        status = "✅ PASS" if test_result['passed'] else "❌ FAIL"
        print(f"{status} {test_result['test_name']}: {test_result['details']}")
    
    # Save detailed results to file
    results_file = Path("async_memory_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Memory entry for test results
    try:
        from claude_pm.services.memory import collect_memory, MemoryCategory
        
        await collect_memory(
            "claude-multiagent-pm",
            f"Async memory system test completed: {results['overall_result']}. "
            f"Passed {results['tests_passed']}/{results['tests_run']} tests. "
            f"Performance: {results.get('avg_response_time', 0):.3f}s avg response time. "
            f"Issues: {results['timeout_errors']} timeouts, {results['concurrent_errors']} concurrent errors.",
            MemoryCategory.QA,
            metadata={
                "test_type": "async_memory_validation",
                "overall_result": results['overall_result'],
                "test_metrics": {
                    "tests_run": results['tests_run'],
                    "tests_passed": results['tests_passed'],
                    "success_rate": results['test_success_rate'],
                    "avg_response_time": results.get('avg_response_time', 0),
                    "timeout_errors": results['timeout_errors'],
                    "concurrent_errors": results['concurrent_errors'],
                }
            }
        )
        print("✅ Test results collected in memory system")
    except Exception as e:
        print(f"⚠️ Could not collect test results in memory: {e}")
    
    # Exit with appropriate code
    if results['overall_result'] == "FAIL":
        exit(1)
    elif results['overall_result'] == "PARTIAL_PASS":
        exit(2)
    else:
        exit(0)


if __name__ == "__main__":
    asyncio.run(main())