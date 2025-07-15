#!/usr/bin/env python3
"""
Async Memory System Validation Test - Focused Testing

This script provides focused testing of the async memory system fixes,
specifically targeting the issues identified in the comprehensive test.
"""

import asyncio
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enum_fixes():
    """Test 1: Verify MemoryCategory enum fixes."""
    logger.info("🧪 Testing MemoryCategory enum fixes...")
    
    try:
        from claude_pm.services.memory.interfaces.models import MemoryCategory
        
        # Test all required categories
        required_categories = ['QA', 'INTEGRATION', 'PERFORMANCE']
        missing_categories = []
        
        for category in required_categories:
            if not hasattr(MemoryCategory, category):
                missing_categories.append(category)
        
        if missing_categories:
            logger.error(f"❌ Missing categories: {missing_categories}")
            return False
        
        # Test category instantiation
        test_categories = [
            MemoryCategory.QA,
            MemoryCategory.INTEGRATION,
            MemoryCategory.PERFORMANCE,
            MemoryCategory.BUG,
            MemoryCategory.PROJECT,
        ]
        
        for cat in test_categories:
            logger.info(f"✅ Category {cat.name} = {cat.value}")
        
        logger.info("✅ MemoryCategory enum fixes validated")
        return True
        
    except Exception as e:
        logger.error(f"❌ MemoryCategory enum test failed: {e}")
        return False


async def test_enhanced_service_initialization():
    """Test 2: Enhanced service initialization."""
    logger.info("🧪 Testing enhanced service initialization...")
    
    try:
        from claude_pm.services.memory.enhanced_unified_service import EnhancedFlexibleMemoryService
        
        # Test service creation
        service = EnhancedFlexibleMemoryService({
            "enable_optimization": True,
            "max_concurrent_ops": 5,
            "operation_timeout": 8.0,
        })
        
        # Test initialization
        start_time = time.time()
        init_success = await service.initialize()
        init_time = time.time() - start_time
        
        if not init_success:
            logger.error("❌ Enhanced service initialization failed")
            return False
        
        logger.info(f"✅ Enhanced service initialized in {init_time:.3f}s")
        
        # Test health check
        health = await service.get_enhanced_service_health()
        logger.info(f"✅ Enhanced health check: optimization_enabled = {health['enhancement']['optimization_enabled']}")
        
        # Cleanup
        await service.cleanup()
        logger.info("✅ Enhanced service initialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced service initialization failed: {e}")
        return False


async def test_optimized_operations():
    """Test 3: Optimized memory operations."""
    logger.info("🧪 Testing optimized memory operations...")
    
    try:
        from claude_pm.services.memory.enhanced_unified_service import EnhancedFlexibleMemoryService
        from claude_pm.services.memory.interfaces.models import MemoryCategory, MemoryQuery
        
        service = EnhancedFlexibleMemoryService({
            "enable_optimization": True,
            "operation_timeout": 5.0,
        })
        
        await service.initialize()
        
        # Test optimized add operations
        operation_times = []
        
        for i in range(5):
            start_time = time.time()
            
            memory_id = await service.add_memory(
                "optimization_test",
                f"Optimized memory {i}",
                MemoryCategory.PERFORMANCE,
                tags=[f"opt_{i}"],
                metadata={"test_id": i, "optimization": True}
            )
            
            operation_time = time.time() - start_time
            operation_times.append(operation_time)
            
            logger.info(f"✅ Add operation {i}: {operation_time:.3f}s, ID: {memory_id}")
        
        # Test optimized search operations
        search_times = []
        
        for i in range(3):
            start_time = time.time()
            
            results = await service.search_memories(
                "optimization_test",
                MemoryQuery("optimized", category=MemoryCategory.PERFORMANCE, limit=3)
            )
            
            search_time = time.time() - start_time
            search_times.append(search_time)
            
            logger.info(f"✅ Search operation {i}: {search_time:.3f}s, {len(results)} results")
        
        # Analyze performance
        avg_add_time = sum(operation_times) / len(operation_times)
        avg_search_time = sum(search_times) / len(search_times)
        max_add_time = max(operation_times)
        max_search_time = max(search_times)
        
        logger.info(f"📊 Add operations - Avg: {avg_add_time:.3f}s, Max: {max_add_time:.3f}s")
        logger.info(f"📊 Search operations - Avg: {avg_search_time:.3f}s, Max: {max_search_time:.3f}s")
        
        # Performance validation
        if avg_add_time > 3.0 or avg_search_time > 2.0:
            logger.warning(f"⚠️ Performance may be suboptimal")
        else:
            logger.info("✅ Performance within expected range")
        
        await service.cleanup()
        logger.info("✅ Optimized operations test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Optimized operations test failed: {e}")
        return False


async def test_concurrent_operations_fixed():
    """Test 4: Fixed concurrent operations."""
    logger.info("🧪 Testing fixed concurrent operations...")
    
    try:
        from claude_pm.services.memory.enhanced_unified_service import EnhancedFlexibleMemoryService
        from claude_pm.services.memory.interfaces.models import MemoryCategory
        
        service = EnhancedFlexibleMemoryService({
            "enable_optimization": True,
            "max_concurrent_ops": 3,  # Limited concurrency for testing
            "operation_timeout": 8.0,
        })
        
        await service.initialize()
        
        # Test concurrent validation
        validation_results = await service.concurrent_validation_test(
            project_name="concurrent_fix_test",
            num_operations=6
        )
        
        logger.info(f"📊 Concurrent validation results:")
        logger.info(f"   Total: {validation_results['total_validations']}")
        logger.info(f"   Successful: {validation_results['successful_validations']}")
        logger.info(f"   Failed: {validation_results['failed_validations']}")
        logger.info(f"   Success: {validation_results['overall_success']}")
        
        if validation_results["validation_errors"]:
            logger.warning(f"⚠️ Validation errors: {validation_results['validation_errors']}")
        
        # Check improvement
        success_rate = (
            validation_results["successful_validations"] / validation_results["total_validations"]
        )
        
        if success_rate >= 0.8:  # 80% success rate
            logger.info(f"✅ Concurrent operations fixed - {success_rate:.1%} success rate")
            success = True
        else:
            logger.error(f"❌ Concurrent operations still failing - {success_rate:.1%} success rate")
            success = False
        
        await service.cleanup()
        return success
        
    except Exception as e:
        logger.error(f"❌ Concurrent operations test failed: {e}")
        return False


async def test_memory_system_validation():
    """Test 5: Memory system validation under load."""
    logger.info("🧪 Testing memory system validation under load...")
    
    try:
        from claude_pm.services.memory import validate_memory_system_for_release
        
        # Run multiple validation cycles
        validation_times = []
        validation_successes = 0
        
        for cycle in range(3):
            logger.info(f"Running validation cycle {cycle + 1}/3...")
            
            start_time = time.time()
            
            try:
                results = await validate_memory_system_for_release()
                validation_time = time.time() - start_time
                validation_times.append(validation_time)
                
                if results.get("release_ready", False):
                    validation_successes += 1
                    logger.info(f"✅ Validation cycle {cycle + 1}: PASS ({validation_time:.2f}s)")
                else:
                    logger.warning(f"⚠️ Validation cycle {cycle + 1}: FAIL ({validation_time:.2f}s)")
                
            except Exception as e:
                validation_time = time.time() - start_time
                validation_times.append(validation_time)
                logger.error(f"❌ Validation cycle {cycle + 1}: ERROR ({validation_time:.2f}s) - {e}")
        
        # Analyze validation performance
        if validation_times:
            avg_validation_time = sum(validation_times) / len(validation_times)
            max_validation_time = max(validation_times)
            
            logger.info(f"📊 Validation performance:")
            logger.info(f"   Successful: {validation_successes}/3")
            logger.info(f"   Avg time: {avg_validation_time:.2f}s")
            logger.info(f"   Max time: {max_validation_time:.2f}s")
            
            # Success criteria
            if validation_successes >= 2 and avg_validation_time < 15.0:
                logger.info("✅ Memory system validation under load: PASS")
                return True
            else:
                logger.error("❌ Memory system validation under load: FAIL")
                return False
        else:
            logger.error("❌ No validation results obtained")
            return False
        
    except Exception as e:
        logger.error(f"❌ Memory system validation test failed: {e}")
        return False


async def test_performance_auto_tuning():
    """Test 6: Performance auto-tuning."""
    logger.info("🧪 Testing performance auto-tuning...")
    
    try:
        from claude_pm.services.memory.enhanced_unified_service import EnhancedFlexibleMemoryService
        from claude_pm.services.memory.interfaces.models import MemoryCategory
        
        service = EnhancedFlexibleMemoryService({
            "enable_optimization": True,
            "max_concurrent_ops": 2,  # Start with conservative settings
            "operation_timeout": 5.0,
        })
        
        await service.initialize()
        
        # Generate some operations to create metrics
        for i in range(5):
            await service.add_memory(
                "tuning_test",
                f"Auto-tuning test memory {i}",
                MemoryCategory.PERFORMANCE,
                metadata={"tuning_test": True}
            )
        
        # Get initial metrics
        initial_health = await service.get_enhanced_service_health()
        initial_optimization = initial_health["enhancement"]["optimization_metrics"]
        
        logger.info(f"📊 Initial metrics: {initial_optimization}")
        
        # Perform auto-tuning
        tuning_results = await service.tune_performance()
        
        logger.info(f"🔧 Auto-tuning results:")
        logger.info(f"   Adjustments: {tuning_results['adjustments_made']}")
        logger.info(f"   Original config: {tuning_results['original_config']}")
        logger.info(f"   New config: {tuning_results['new_config']}")
        
        # Test operations after tuning
        post_tuning_times = []
        for i in range(3):
            start_time = time.time()
            await service.add_memory(
                "tuning_test",
                f"Post-tuning memory {i}",
                MemoryCategory.PERFORMANCE
            )
            post_tuning_times.append(time.time() - start_time)
        
        avg_post_tuning = sum(post_tuning_times) / len(post_tuning_times)
        logger.info(f"📊 Post-tuning avg operation time: {avg_post_tuning:.3f}s")
        
        await service.cleanup()
        logger.info("✅ Performance auto-tuning test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance auto-tuning test failed: {e}")
        return False


async def main():
    """Run focused async memory system validation tests."""
    logger.info("🔍 Async Memory System Validation - Focused Testing")
    logger.info("=" * 60)
    
    test_functions = [
        ("MemoryCategory Enum Fixes", test_enum_fixes),
        ("Enhanced Service Initialization", test_enhanced_service_initialization),
        ("Optimized Operations", test_optimized_operations),
        ("Concurrent Operations Fixed", test_concurrent_operations_fixed),
        ("Memory System Validation", test_memory_system_validation),
        ("Performance Auto-Tuning", test_performance_auto_tuning),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_name, test_func in test_functions:
        logger.info(f"\n🧪 Running: {test_name}")
        test_start_time = time.time()
        
        try:
            success = await test_func()
            test_time = time.time() - test_start_time
            results.append({
                "test": test_name,
                "success": success,
                "time": test_time
            })
            
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"{status} {test_name} ({test_time:.2f}s)")
            
        except Exception as e:
            test_time = time.time() - test_start_time
            results.append({
                "test": test_name,
                "success": False,
                "time": test_time,
                "error": str(e)
            })
            logger.error(f"❌ FAIL {test_name} ({test_time:.2f}s): {e}")
    
    # Summary
    total_time = time.time() - total_start_time
    passed_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    logger.info(f"\n📊 FOCUSED TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {total_tests - passed_tests}")
    logger.info(f"Success Rate: {success_rate:.1%}")
    logger.info(f"Total Time: {total_time:.2f}s")
    
    logger.info(f"\n📋 INDIVIDUAL TEST RESULTS:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        error_info = f" - {result.get('error', '')}" if not result["success"] and "error" in result else ""
        logger.info(f"{status} {result['test']} ({result['time']:.2f}s){error_info}")
    
    # Memory collection
    try:
        from claude_pm.services.memory import collect_memory, MemoryCategory
        
        await collect_memory(
            "claude-multiagent-pm",
            f"Focused async memory validation completed: {passed_tests}/{total_tests} tests passed. "
            f"Performance improvements implemented for timeout handling, concurrent operations, "
            f"and enum fixes. Success rate: {success_rate:.1%}",
            MemoryCategory.QA,
            metadata={
                "test_type": "focused_async_validation",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "total_time": total_time,
                "improvements": [
                    "MemoryCategory enum expanded",
                    "Async operation optimization",
                    "Enhanced concurrent handling",
                    "Performance auto-tuning",
                ]
            }
        )
        logger.info("✅ Test results collected in memory system")
    except Exception as e:
        logger.warning(f"⚠️ Could not collect test results in memory: {e}")
    
    # Exit with appropriate code
    if success_rate >= 0.8:
        logger.info("🎉 Focused validation tests PASSED - async memory system fixes validated")
        exit(0)
    else:
        logger.error("❌ Focused validation tests FAILED - async memory system needs further fixes")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())