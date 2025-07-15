"""
Demonstration of AsyncMemoryCollector usage.

Shows how to integrate and use the AsyncMemoryCollector service
for fire-and-forget memory collection operations.
"""

import asyncio
import logging
import time
from typing import Dict, Any

from ..core.service_manager import ServiceManager
from .async_memory_collector import AsyncMemoryCollector
from .memory_service_integration import MemoryServiceIntegration, set_memory_integration
from ..config.async_memory_config import get_config


async def demo_basic_usage():
    """Demonstrate basic AsyncMemoryCollector usage."""
    print("=== AsyncMemoryCollector Basic Usage Demo ===")
    
    # Create service manager
    service_manager = ServiceManager()
    
    # Create memory service integration
    integration = MemoryServiceIntegration(service_manager)
    set_memory_integration(integration)
    
    # Register AsyncMemoryCollector
    config = get_config("development")
    collector = await integration.register_async_memory_collector(config)
    
    # Start services
    await service_manager.start_all()
    
    try:
        # Collect different types of memory operations
        print("\n1. Collecting bug information...")
        bug_id = await integration.collect_bug(
            "Memory leak detected in async processor",
            metadata={"component": "async_processor", "severity": "high"}
        )
        print(f"   Bug operation ID: {bug_id}")
        
        print("\n2. Collecting user feedback...")
        feedback_id = await integration.collect_feedback(
            "The new async memory collection is much faster!",
            metadata={"user_id": "user123", "rating": 5}
        )
        print(f"   Feedback operation ID: {feedback_id}")
        
        print("\n3. Collecting error information...")
        error_id = await integration.collect_error(
            "Database connection failed during batch processing",
            metadata={"error_code": "DB_CONN_FAILED", "timestamp": time.time()}
        )
        print(f"   Error operation ID: {error_id}")
        
        print("\n4. Collecting performance data...")
        perf_id = await integration.collect_performance_data(
            "Queue processing latency: 2.3ms",
            metadata={"operation": "queue_processing", "latency_ms": 2.3}
        )
        print(f"   Performance operation ID: {perf_id}")
        
        print("\n5. Collecting architecture information...")
        arch_id = await integration.collect_architecture_info(
            "Implemented fire-and-forget async memory collection",
            metadata={"change_type": "enhancement", "impact": "performance"}
        )
        print(f"   Architecture operation ID: {arch_id}")
        
        # Wait a bit for processing
        print("\n6. Waiting for background processing...")
        await asyncio.sleep(2)
        
        # Get collection statistics
        stats = await integration.get_collection_stats()
        if stats:
            print(f"\n7. Collection Statistics:")
            print(f"   Total operations: {stats['total_operations']}")
            print(f"   Successful operations: {stats['successful_operations']}")
            print(f"   Failed operations: {stats['failed_operations']}")
            print(f"   Success rate: {stats['success_rate']:.1f}%")
            print(f"   Average latency: {stats['average_latency']:.3f}s")
            print(f"   Queue size: {stats['queue_size']}")
            print(f"   Cache hits: {stats['cache_hits']}")
            print(f"   Cache misses: {stats['cache_misses']}")
        
        # Flush remaining operations
        print("\n8. Flushing remaining operations...")
        flushed = await integration.flush_collector()
        print(f"   Flushed {flushed} operations")
        
    finally:
        # Cleanup
        await service_manager.stop_all()
        print("\n=== Demo completed ===")


async def demo_performance_test():
    """Demonstrate performance characteristics."""
    print("\n=== AsyncMemoryCollector Performance Test ===")
    
    # Create service manager
    service_manager = ServiceManager()
    
    # Create memory service integration with high-performance config
    integration = MemoryServiceIntegration(service_manager)
    config = get_config("high_performance")
    collector = await integration.register_async_memory_collector(config)
    
    # Start services
    await service_manager.start_all()
    
    try:
        # Performance test
        operation_count = 100
        start_time = time.time()
        
        print(f"\nSubmitting {operation_count} operations...")
        
        # Submit operations rapidly
        tasks = []
        for i in range(operation_count):
            task = integration.collect_performance_data(
                f"Performance test operation {i}",
                metadata={"test_id": i, "batch": "performance_test"}
            )
            tasks.append(task)
        
        # Wait for all submissions to complete
        results = await asyncio.gather(*tasks)
        
        submission_time = time.time() - start_time
        print(f"Submitted {len([r for r in results if r])} operations in {submission_time:.3f}s")
        print(f"Average submission latency: {(submission_time / operation_count) * 1000:.1f}ms")
        
        # Wait for processing
        print("\nWaiting for background processing...")
        await asyncio.sleep(5)
        
        # Check final statistics
        stats = await integration.get_collection_stats()
        if stats:
            print(f"\nFinal Statistics:")
            print(f"   Total operations: {stats['total_operations']}")
            print(f"   Success rate: {stats['success_rate']:.1f}%")
            print(f"   Average processing latency: {stats['average_latency']:.3f}s")
            print(f"   Batch operations: {stats['batch_operations']}")
        
    finally:
        # Cleanup
        await service_manager.stop_all()
        print("\n=== Performance test completed ===")


async def demo_error_handling():
    """Demonstrate error handling and retry logic."""
    print("\n=== AsyncMemoryCollector Error Handling Demo ===")
    
    # Create service manager
    service_manager = ServiceManager()
    
    # Create memory service integration
    integration = MemoryServiceIntegration(service_manager)
    config = get_config("development")
    collector = await integration.register_async_memory_collector(config)
    
    # Start services
    await service_manager.start_all()
    
    try:
        # Test with invalid category (should fail gracefully)
        print("\n1. Testing invalid category...")
        try:
            await collector.collect_async(
                category="invalid_category",
                content="This should fail",
                metadata={}
            )
        except ValueError as e:
            print(f"   Caught expected error: {e}")
        
        # Test with invalid priority (should fail gracefully)
        print("\n2. Testing invalid priority...")
        try:
            await collector.collect_async(
                category="bug",
                content="This should fail",
                metadata={},
                priority="invalid_priority"
            )
        except ValueError as e:
            print(f"   Caught expected error: {e}")
        
        # Test queue full scenario (if we could simulate it)
        print("\n3. Testing normal operations after errors...")
        for i in range(5):
            op_id = await integration.collect_bug(
                f"Bug {i} after error handling test",
                metadata={"test": "error_handling", "index": i}
            )
            print(f"   Operation {i}: {op_id}")
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check statistics
        stats = await integration.get_collection_stats()
        if stats:
            print(f"\nStatistics after error handling:")
            print(f"   Total operations: {stats['total_operations']}")
            print(f"   Failed operations: {stats['failed_operations']}")
            print(f"   Success rate: {stats['success_rate']:.1f}%")
        
    finally:
        # Cleanup
        await service_manager.stop_all()
        print("\n=== Error handling demo completed ===")


async def main():
    """Run all demonstration scenarios."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("AsyncMemoryCollector Demonstration")
    print("=" * 50)
    
    try:
        # Run demo scenarios
        await demo_basic_usage()
        await demo_performance_test()
        await demo_error_handling()
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nAll demonstrations completed!")


if __name__ == "__main__":
    asyncio.run(main())