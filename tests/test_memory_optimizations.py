#!/usr/bin/env python3
"""
Test script for Phase 1 memory optimizations.

This script verifies that the memory optimization changes work correctly:
1. SharedPromptCache with reduced TTL and memory-based eviction
2. Subprocess memory thresholds reduced by 50%
3. Memory pressure coordinator for cross-service cleanup
4. Integration with memory diagnostics
"""

import asyncio
import logging
import time
import psutil
from pathlib import Path

# Add framework to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.memory_diagnostics import get_memory_diagnostics
from claude_pm.services.memory_pressure_coordinator import get_memory_pressure_coordinator
from claude_pm.monitoring.subprocess_manager import get_subprocess_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_shared_prompt_cache():
    """Test SharedPromptCache memory optimizations."""
    logger.info("=== Testing SharedPromptCache ===")
    
    # Get cache instance
    cache = SharedPromptCache.get_instance()
    await cache.start()
    
    try:
        # Test 1: Verify reduced TTL (5 minutes)
        logger.info(f"Default TTL: {cache.default_ttl} seconds (expected: 300)")
        assert cache.default_ttl == 300, f"Expected TTL 300, got {cache.default_ttl}"
        
        # Test 2: Verify reduced max memory (50MB)
        logger.info(f"Max memory: {cache.max_memory_mb} MB (expected: 50)")
        assert cache.max_memory_mb == 50, f"Expected max memory 50MB, got {cache.max_memory_mb}"
        
        # Test 3: Add items and verify memory-based eviction
        logger.info("Testing memory-based eviction...")
        
        # Add items until we approach memory limit
        large_data = "x" * (1024 * 1024)  # 1MB string
        for i in range(60):  # Try to add 60MB of data
            cache.set(f"test_key_{i}", large_data)
        
        # Check metrics
        metrics = cache.get_metrics()
        logger.info(f"Cache metrics after filling:")
        logger.info(f"  Entries: {metrics['entry_count']}")
        logger.info(f"  Memory: {metrics['size_mb']:.2f} MB")
        logger.info(f"  Evictions: {metrics['evictions']}")
        
        # Verify memory limit is respected
        assert metrics['size_mb'] <= cache.max_memory_mb * 1.1, "Cache exceeded memory limit"
        assert metrics['evictions'] > 0, "No evictions occurred when memory limit was reached"
        
        # Test 4: Test memory pressure handling
        logger.info("Testing memory pressure response...")
        stats = await cache.handle_memory_pressure("critical")
        logger.info(f"Memory pressure cleanup stats: {stats}")
        
        # Verify cache was cleaned
        metrics_after = cache.get_metrics()
        logger.info(f"Cache after pressure cleanup: {metrics_after['entry_count']} entries, {metrics_after['size_mb']:.2f} MB")
        assert metrics_after['entry_count'] < metrics['entry_count'], "Cache not cleaned during pressure"
        
        logger.info("✅ SharedPromptCache tests passed")
        
    finally:
        await cache.stop()


async def test_subprocess_thresholds():
    """Test subprocess memory threshold reductions."""
    logger.info("\n=== Testing Subprocess Thresholds ===")
    
    manager = get_subprocess_manager()
    
    # Verify thresholds
    logger.info(f"Memory limit per subprocess: {manager.config['subprocess_memory_limit_mb']} MB (expected: 1000)")
    logger.info(f"Warning threshold: {manager.config['memory_warning_threshold_mb']} MB (expected: 500)")
    logger.info(f"Aggregate limit: {manager.config['aggregate_memory_limit_mb']} MB (expected: 2000)")
    
    assert manager.config['subprocess_memory_limit_mb'] == 1000, "Subprocess limit not reduced"
    assert manager.config['memory_warning_threshold_mb'] == 500, "Warning threshold not set"
    assert manager.config['aggregate_memory_limit_mb'] == 2000, "Aggregate limit not set"
    
    logger.info("✅ Subprocess threshold tests passed")


async def test_memory_pressure_coordinator():
    """Test memory pressure coordinator."""
    logger.info("\n=== Testing Memory Pressure Coordinator ===")
    
    coordinator = get_memory_pressure_coordinator()
    
    # Test 1: Get memory status
    status = coordinator.get_memory_status()
    logger.info(f"Current memory status:")
    logger.info(f"  Process memory: {status['process_memory_mb']:.1f} MB")
    logger.info(f"  System memory: {status['system_memory_percent']:.1f}%")
    logger.info(f"  Pressure level: {status['pressure_level']}")
    
    # Test 2: Register test cleanup handler
    cleanup_called = False
    async def test_cleanup(severity):
        nonlocal cleanup_called
        cleanup_called = True
        return {"test_service": "cleaned", "memory_freed_mb": 1.0}
    
    coordinator.register_cleanup_handler("test_service", test_cleanup)
    
    # Test 3: Trigger cleanup (force to bypass cooldown)
    result = await coordinator.handle_memory_pressure(force=True)
    logger.info(f"Cleanup result: {result}")
    
    assert cleanup_called, "Test cleanup handler not called"
    assert "test_service" in result.get("service_cleanups", {}), "Test service not in cleanup results"
    
    logger.info("✅ Memory pressure coordinator tests passed")


async def test_integration():
    """Test integration between components."""
    logger.info("\n=== Testing Component Integration ===")
    
    # Start memory diagnostics
    diagnostics = get_memory_diagnostics()
    await diagnostics.start()
    
    try:
        # Get diagnostics report
        report = await diagnostics.get_memory_diagnostics()
        logger.info(f"Memory diagnostics report:")
        logger.info(f"  Pressure detected: {report['pressure_detected']}")
        logger.info(f"  Auto cleanup enabled: {report['auto_cleanup_enabled']}")
        logger.info(f"  Process threshold: {report['thresholds']['process_mb']} MB")
        
        # Verify SharedPromptCache is registered with coordinator
        coordinator = get_memory_pressure_coordinator()
        assert "shared_prompt_cache" in coordinator._cleanup_handlers, "SharedPromptCache not registered"
        assert "memory_diagnostics" in coordinator._cleanup_handlers, "MemoryDiagnostics not registered"
        
        logger.info("✅ Integration tests passed")
        
    finally:
        await diagnostics.stop()


async def main():
    """Run all tests."""
    logger.info("Starting memory optimization tests...")
    
    try:
        await test_shared_prompt_cache()
        await test_subprocess_thresholds()
        await test_memory_pressure_coordinator()
        await test_integration()
        
        logger.info("\n✅ All memory optimization tests passed!")
        
    except AssertionError as e:
        logger.error(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())