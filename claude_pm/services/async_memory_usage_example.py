"""
AsyncMemoryCollector Usage Examples and Integration Guide.

This module provides comprehensive examples of how to use the AsyncMemoryCollector
service in various scenarios and integrate it with the Claude PM Framework.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.service_manager import ServiceManager
from .async_memory_collector import AsyncMemoryCollector, MemoryCategory, MemoryPriority
from .memory_service_integration import MemoryServiceIntegration, set_memory_integration
from ..config.async_memory_config import get_config


class AsyncMemoryUsageExamples:
    """Examples of AsyncMemoryCollector usage in different scenarios."""
    
    @staticmethod
    async def example_1_basic_setup():
        """Example 1: Basic setup and usage."""
        print("=== Example 1: Basic Setup ===")
        
        # Create service manager
        service_manager = ServiceManager()
        
        # Create memory service integration
        integration = MemoryServiceIntegration(service_manager)
        
        # Register AsyncMemoryCollector with development config
        config = get_config("development")
        collector = await integration.register_async_memory_collector(config)
        
        # Start services
        await service_manager.start_all()
        
        try:
            # Basic collection operations
            print("Collecting various memory types...")
            
            # Bug report
            bug_id = await integration.collect_bug(
                "Memory leak detected in cache cleanup",
                metadata={
                    "component": "cache",
                    "severity": "high", 
                    "reported_by": "user123"
                }
            )
            print(f"Bug collected: {bug_id}")
            
            # User feedback
            feedback_id = await integration.collect_feedback(
                "The async memory collection is working great!",
                metadata={
                    "user_id": "user456",
                    "rating": 5,
                    "feature": "memory_collection"
                }
            )
            print(f"Feedback collected: {feedback_id}")
            
            # Error information
            error_id = await integration.collect_error(
                "Database connection timeout during batch processing",
                metadata={
                    "error_code": "DB_TIMEOUT",
                    "operation": "batch_process",
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"Error collected: {error_id}")
            
            # Wait for processing
            await asyncio.sleep(1)
            
            # Check statistics
            stats = await integration.get_collection_stats()
            if stats:
                print(f"\nCollection Statistics:")
                print(f"  Total operations: {stats['total_operations']}")
                print(f"  Success rate: {stats['success_rate']:.1f}%")
                print(f"  Average latency: {stats['average_latency']:.3f}s")
                print(f"  Queue size: {stats['queue_size']}")
            
        finally:
            await service_manager.stop_all()
    
    @staticmethod
    async def example_2_high_performance():
        """Example 2: High-performance configuration."""
        print("\n=== Example 2: High-Performance Configuration ===")
        
        service_manager = ServiceManager()
        integration = MemoryServiceIntegration(service_manager)
        
        # Use high-performance configuration
        config = get_config("high_performance")
        collector = await integration.register_async_memory_collector(config)
        
        await service_manager.start_all()
        
        try:
            # Rapid-fire operations
            print("Performing high-volume operations...")
            
            start_time = asyncio.get_event_loop().time()
            
            # Submit 100 operations rapidly
            tasks = []
            for i in range(100):
                task = integration.collect_performance_data(
                    f"Performance metric {i}",
                    metadata={
                        "metric_type": "latency",
                        "value": i * 0.1,
                        "unit": "seconds"
                    }
                )
                tasks.append(task)
            
            # Wait for all submissions
            results = await asyncio.gather(*tasks)
            
            submission_time = asyncio.get_event_loop().time() - start_time
            successful_ops = len([r for r in results if r])
            
            print(f"Submitted {successful_ops} operations in {submission_time:.3f}s")
            print(f"Average submission latency: {(submission_time/100)*1000:.1f}ms")
            
            # Wait for background processing
            await asyncio.sleep(2)
            
            # Check final stats
            stats = await integration.get_collection_stats()
            if stats:
                print(f"\nFinal Performance Statistics:")
                print(f"  Total operations: {stats['total_operations']}")
                print(f"  Batch operations: {stats['batch_operations']}")
                print(f"  Success rate: {stats['success_rate']:.1f}%")
                print(f"  Cache hits: {stats['cache_hits']}")
                print(f"  Cache misses: {stats['cache_misses']}")
            
        finally:
            await service_manager.stop_all()
    
    @staticmethod
    async def example_3_error_scenarios():
        """Example 3: Error handling and recovery scenarios."""
        print("\n=== Example 3: Error Handling Scenarios ===")
        
        service_manager = ServiceManager()
        integration = MemoryServiceIntegration(service_manager)
        
        config = get_config("development")
        collector = await integration.register_async_memory_collector(config)
        
        await service_manager.start_all()
        
        try:
            print("Testing error scenarios...")
            
            # Test invalid category (should fail gracefully)
            try:
                await collector.collect_async(
                    category="invalid_category",
                    content="This should fail",
                    metadata={}
                )
                print("ERROR: Should have failed!")
            except ValueError as e:
                print(f"✓ Correctly caught invalid category: {e}")
            
            # Test invalid priority (should fail gracefully)
            try:
                await collector.collect_async(
                    category="bug",
                    content="This should fail",
                    metadata={},
                    priority="invalid_priority"
                )
                print("ERROR: Should have failed!")
            except ValueError as e:
                print(f"✓ Correctly caught invalid priority: {e}")
            
            # Test normal operations after errors
            print("\nTesting recovery after errors...")
            for i in range(3):
                op_id = await integration.collect_bug(
                    f"Bug report {i} after error test",
                    metadata={"test": "error_recovery", "index": i}
                )
                print(f"✓ Successfully collected operation {i}: {op_id}")
            
            await asyncio.sleep(1)
            
            # Check stats
            stats = await integration.get_collection_stats()
            if stats:
                print(f"\nError Recovery Statistics:")
                print(f"  Total operations: {stats['total_operations']}")
                print(f"  Failed operations: {stats['failed_operations']}")
                print(f"  Success rate: {stats['success_rate']:.1f}%")
            
        finally:
            await service_manager.stop_all()
    
    @staticmethod
    async def example_4_integration_with_agents():
        """Example 4: Integration with Claude PM agents."""
        print("\n=== Example 4: Agent Integration ===")
        
        service_manager = ServiceManager()
        integration = MemoryServiceIntegration(service_manager)
        set_memory_integration(integration)  # Set global integration
        
        config = get_config("production")
        collector = await integration.register_async_memory_collector(config)
        
        await service_manager.start_all()
        
        try:
            # Simulate agent memory collection scenarios
            print("Simulating agent memory collection...")
            
            # Documentation Agent scenario
            await integration.collect_architecture_info(
                "Updated framework architecture with async memory collection",
                metadata={
                    "agent": "documentation",
                    "change_type": "enhancement",
                    "impact": "performance"
                }
            )
            
            # QA Agent scenario  
            await integration.collect_bug(
                "Test failure in memory collection stress test",
                metadata={
                    "agent": "qa",
                    "test_suite": "memory_stress_test",
                    "failure_type": "timeout"
                }
            )
            
            # Engineer Agent scenario
            await integration.collect_performance_data(
                "Code optimization reduced memory allocation by 30%",
                metadata={
                    "agent": "engineer",
                    "optimization_type": "memory",
                    "improvement": "30%"
                }
            )
            
            # Ops Agent scenario
            await integration.collect_error(
                "Deployment failed due to memory configuration mismatch",
                metadata={
                    "agent": "ops",
                    "deployment_stage": "production",
                    "error_type": "configuration"
                }
            )
            
            # Research Agent scenario
            await integration.collect_feedback(
                "Async memory collection shows 80% latency improvement",
                metadata={
                    "agent": "research",
                    "research_type": "performance_analysis",
                    "improvement": "80%"
                }
            )
            
            # Wait for processing
            await asyncio.sleep(2)
            
            # Show final statistics
            stats = await integration.get_collection_stats()
            if stats:
                print(f"\nAgent Integration Statistics:")
                print(f"  Total operations: {stats['total_operations']}")
                print(f"  Success rate: {stats['success_rate']:.1f}%")
                print(f"  Average latency: {stats['average_latency']:.3f}s")
                print(f"  Batch operations: {stats['batch_operations']}")
            
        finally:
            await service_manager.stop_all()
    
    @staticmethod
    async def example_5_custom_configuration():
        """Example 5: Custom configuration for specific needs."""
        print("\n=== Example 5: Custom Configuration ===")
        
        # Custom configuration for a specific use case
        custom_config = {
            "batch_size": 25,
            "batch_timeout": 10.0,
            "max_queue_size": 1500,
            "max_retries": 5,
            "retry_delay": 2.0,
            "operation_timeout": 20.0,
            "max_concurrent_ops": 30,
            "health_check_interval": 45,
            "cache": {
                "enabled": True,
                "max_size": 1500,
                "ttl_seconds": 400
            }
        }
        
        service_manager = ServiceManager()
        integration = MemoryServiceIntegration(service_manager)
        
        # Use custom configuration
        collector = await integration.register_async_memory_collector(custom_config)
        
        await service_manager.start_all()
        
        try:
            print("Testing custom configuration...")
            
            # Test with custom batch size
            for i in range(30):  # More than custom batch_size
                await integration.collect_performance_data(
                    f"Custom config test {i}",
                    metadata={"test": "custom_config", "index": i}
                )
            
            # Wait for batch processing
            await asyncio.sleep(3)
            
            stats = await integration.get_collection_stats()
            if stats:
                print(f"\nCustom Configuration Results:")
                print(f"  Total operations: {stats['total_operations']}")
                print(f"  Batch operations: {stats['batch_operations']}")
                print(f"  Success rate: {stats['success_rate']:.1f}%")
                print(f"  Cache performance: {stats['cache_hits']}/{stats['cache_misses']} hits/misses")
            
        finally:
            await service_manager.stop_all()


class AsyncMemoryIntegrationGuide:
    """Guide for integrating AsyncMemoryCollector into existing services."""
    
    @staticmethod
    def print_integration_guide():
        """Print comprehensive integration guide."""
        print("\n" + "="*60)
        print("ASYNC MEMORY COLLECTOR INTEGRATION GUIDE")
        print("="*60)
        
        print("""
1. BASIC SETUP
--------------
from claude_pm.core.service_manager import ServiceManager
from claude_pm.services.memory_service_integration import MemoryServiceIntegration
from claude_pm.config.async_memory_config import get_config

# Create service manager
service_manager = ServiceManager()

# Create memory integration
integration = MemoryServiceIntegration(service_manager)

# Register with configuration
config = get_config("production")  # or "development", "high_performance"
collector = await integration.register_async_memory_collector(config)

# Start services
await service_manager.start_all()

2. COLLECTING MEMORY DATA
-------------------------
# Bug reports
bug_id = await integration.collect_bug(
    "Bug description",
    metadata={"component": "module", "severity": "high"}
)

# User feedback
feedback_id = await integration.collect_feedback(
    "User feedback text",
    metadata={"user_id": "123", "rating": 5}
)

# Error information
error_id = await integration.collect_error(
    "Error description",
    metadata={"error_code": "E001", "timestamp": "2025-07-15T10:00:00Z"}
)

# Performance data
perf_id = await integration.collect_performance_data(
    "Performance metric description",
    metadata={"metric": "latency", "value": 0.5, "unit": "seconds"}
)

# Architecture information
arch_id = await integration.collect_architecture_info(
    "Architecture change description",
    metadata={"change_type": "enhancement", "impact": "performance"}
)

3. MONITORING AND STATISTICS
-----------------------------
# Get collection statistics
stats = await integration.get_collection_stats()
print(f"Total operations: {stats['total_operations']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Average latency: {stats['average_latency']:.3f}s")

# Force flush queue
processed = await integration.flush_collector(timeout=30.0)
print(f"Processed {processed} operations")

4. CONFIGURATION OPTIONS
-------------------------
# Development (smaller batches, more frequent health checks)
config = get_config("development")

# Production (larger batches, optimized for throughput)
config = get_config("production")

# High performance (maximum throughput)
config = get_config("high_performance")

# Low resource (minimal memory usage)
config = get_config("low_resource")

# Custom configuration
custom_config = {
    "batch_size": 20,
    "batch_timeout": 15.0,
    "max_queue_size": 2000,
    "max_retries": 3,
    "cache": {"enabled": True, "max_size": 1000, "ttl_seconds": 300}
}

5. ERROR HANDLING
-----------------
try:
    operation_id = await integration.collect_bug("Bug report", metadata={})
    if operation_id:
        print(f"Successfully queued operation: {operation_id}")
    else:
        print("Failed to queue operation")
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Collection error: {e}")

6. HEALTH MONITORING
--------------------
# Check collector health
collector = await integration.get_collector()
if collector:
    health = await collector.health_check()
    print(f"Health status: {health.status}")
    print(f"Health checks: {health.checks}")

7. CLEANUP
----------
# Always cleanup when done
await service_manager.stop_all()

8. PERFORMANCE CONSIDERATIONS
-----------------------------
- Fire-and-forget operations return immediately (<100ms)
- Background processing handles actual storage
- Batch operations reduce database load
- Cache improves performance for repeated content
- Queue size limits prevent memory exhaustion
- Retry logic handles temporary failures

9. BEST PRACTICES
-----------------
- Use appropriate priority levels (critical, high, medium, low)
- Include relevant metadata for better organization
- Monitor queue size and processing latency
- Configure batch sizes based on your workload
- Enable caching for frequently accessed data
- Set up health monitoring for production systems
""")


async def main():
    """Run all usage examples."""
    print("AsyncMemoryCollector Usage Examples")
    print("="*50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Run examples
        await AsyncMemoryUsageExamples.example_1_basic_setup()
        await AsyncMemoryUsageExamples.example_2_high_performance()
        await AsyncMemoryUsageExamples.example_3_error_scenarios()
        await AsyncMemoryUsageExamples.example_4_integration_with_agents()
        await AsyncMemoryUsageExamples.example_5_custom_configuration()
        
        # Print integration guide
        AsyncMemoryIntegrationGuide.print_integration_guide()
        
    except Exception as e:
        print(f"Example failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main())