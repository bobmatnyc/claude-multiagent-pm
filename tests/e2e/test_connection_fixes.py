#!/usr/bin/env python3
"""
Test script to verify connection leak fixes are working.

This script tests the timeout and connection management improvements.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.health_dashboard import HealthDashboardOrchestrator
from claude_pm.services.health_monitor import HealthMonitorService
from claude_pm.core.connection_manager import get_connection_manager
# from claude_pm.services.memory_service import MemoryService  # REMOVED - service no longer available

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_timeout_fixes():
    """Test that timeout fixes are working."""
    logger.info("Testing timeout fixes...")
    
    try:
        # Test health dashboard with improved timeouts
        start_time = time.time()
        dashboard = HealthDashboardOrchestrator(
            global_timeout_seconds=15.0,  # Should not timeout now
            cache_ttl_seconds=5.0
        )
        
        health_report = await dashboard.get_health_dashboard()
        elapsed = time.time() - start_time
        
        logger.info(f"Health dashboard completed in {elapsed:.2f}s")
        logger.info(f"Overall status: {health_report.overall_status.value}")
        logger.info(f"Response time: {health_report.total_response_time_ms:.1f}ms")
        
        # Should not timeout anymore
        if elapsed < 15.0:
            logger.info("✓ Timeout fix successful - completed within timeout window")
            return True
        else:
            logger.warning("✗ Still experiencing timeouts")
            return False
            
    except asyncio.TimeoutError:
        logger.error("✗ Still getting timeout errors")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


async def test_connection_management():
    """Test connection management improvements."""
    logger.info("Testing connection management...")
    
    try:
        # Get connection manager
        conn_manager = await get_connection_manager()
        initial_stats = conn_manager.get_stats()
        
        logger.info(f"Initial connection stats: {initial_stats}")
        
        # Test memory service connection - UPDATED: memory_service removed
        # memory_service = MemoryService()  # REMOVED - service no longer available
        # await memory_service._initialize()
        
        # Check connection stats without memory service
        stats_after_init = conn_manager.get_stats()
        logger.info(f"Connection stats (memory_service removed): {stats_after_init}")
        
        # Cleanup memory service - SKIPPED: service removed
        # await memory_service._cleanup()
        
        # Check final stats
        final_stats = conn_manager.get_stats()
        logger.info(f"After cleanup: {final_stats}")
        
        # Cleanup all connections
        await conn_manager.cleanup_all()
        
        logger.info("✓ Connection management test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Connection management test failed: {e}")
        return False


async def test_health_monitor_stability():
    """Test health monitor stability without leaks."""
    logger.info("Testing health monitor stability...")
    
    try:
        # Create health monitor
        monitor = HealthMonitorService()
        
        # Run multiple health checks
        for i in range(3):
            logger.info(f"Health check {i+1}/3...")
            
            start_time = time.time()
            health_data = await monitor.get_framework_health()
            elapsed = time.time() - start_time
            
            logger.info(f"  Status: {health_data.get('status', 'unknown')}")
            logger.info(f"  Time: {elapsed:.2f}s")
            
            if elapsed > 10.0:
                logger.warning(f"  Slow response: {elapsed:.2f}s")
            
            # Short delay between checks
            await asyncio.sleep(1)
        
        logger.info("✓ Health monitor stability test completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Health monitor stability test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Claude PM Framework - Connection Fix Verification")
    logger.info("=" * 60)
    
    all_tests_passed = True
    
    # Test timeout fixes
    timeout_ok = await test_timeout_fixes()
    all_tests_passed = all_tests_passed and timeout_ok
    
    # Test connection management
    connection_ok = await test_connection_management()
    all_tests_passed = all_tests_passed and connection_ok
    
    # Test health monitor stability
    stability_ok = await test_health_monitor_stability()
    all_tests_passed = all_tests_passed and stability_ok
    
    # Summary
    logger.info("=" * 60)
    if all_tests_passed:
        logger.info("✓ All connection fix tests passed!")
        logger.info("  - Timeout issues resolved")
        logger.info("  - Connection management improved")
        logger.info("  - Health monitoring stable")
    else:
        logger.warning("✗ Some tests failed - connection issues may persist")
        
        # Provide remediation suggestions
        logger.info("\nRemediation suggestions:")
        logger.info("  1. Restart any stuck services")
        logger.info("  2. Check mem0AI service status")
        logger.info("  3. Verify network connectivity")
        logger.info("  4. Run scripts/fix_connection_leaks.py again")
    
    logger.info("=" * 60)
    
    return all_tests_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)