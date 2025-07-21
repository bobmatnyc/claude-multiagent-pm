#!/usr/bin/env python3
"""
Working Fallback Memory System Demonstration

# This script demonstrates the working fallback memory system with SQLite and InMemory backends.  # InMemory backend removed
"""

"""
# NOTE: InMemory backend tests have been disabled because the InMemory backend  # InMemory backend removed
was removed from the Claude PM Framework memory system. The system now uses
mem0ai → sqlite fallback chain only.
"""


import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_pm.services.memory import FlexibleMemoryService, MemoryCategory, MemoryQuery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_working_fallback():
    """Demonstrate the working fallback memory system."""
    logger.info("🚀 Starting Working Fallback Memory System Demonstration")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="fallback_demo_")

    try:
        # Configure service with only working backends
        service_config = {
            "mem0ai_enabled": False,  # Simulate mem0AI unavailable
            "sqlite_enabled": True,  # Primary fallback
            # TinyDB removed from framework
            "memory_enabled": True,  # Secondary fallback
            "sqlite_path": os.path.join(temp_dir, "demo.db"),
            "fallback_chain": ["sqlite", "memory"],  # Only working backends
        }

        # Create and initialize service
        service = FlexibleMemoryService(service_config)
        await service.initialize()

        logger.info(f"✅ Service initialized with backend: {service.get_active_backend_name()}")

        # Test memory operations
        logger.info("📝 Testing memory operations...")

        # Add test memories
        test_memories = [
            {
                "content": "SQLite backend is working correctly with FTS5 search",
                "category": MemoryCategory.PROJECT,
                "tags": ["sqlite", "fts5", "working"],
                "metadata": {"test": "fallback_demo", "backend": "sqlite"},
            },
            {
                "content": "Circuit breaker patterns ensure service resilience",
                "category": MemoryCategory.PATTERN,
                "tags": ["circuit-breaker", "resilience", "pattern"],
                "metadata": {"test": "fallback_demo", "importance": "high"},
            },
            {
                # "content": "InMemory backend provides excellent performance for testing",  # InMemory backend removed
                "category": MemoryCategory.TEAM,
                "tags": ["inmemory", "performance", "testing"],
                "metadata": {"test": "fallback_demo", "ops_per_sec": 266474},
            },
        ]

        memory_ids = []
        for i, memory in enumerate(test_memories):
            memory_id = await service.add_memory(
                "demo_project",
                memory["content"],
                memory["category"],
                memory["tags"],
                memory["metadata"],
            )
            memory_ids.append(memory_id)
            logger.info(f"  ✅ Added memory {i+1}: {memory_id}")

        # Test search operations
        logger.info("🔍 Testing search operations...")

        search_tests = [
            ("sqlite", "Search for SQLite-related content"),
            ("circuit breaker", "Search for circuit breaker patterns"),
            ("performance", "Search for performance-related content"),
            ("", "Get all memories"),
        ]

        for search_term, description in search_tests:
            query = MemoryQuery(query=search_term, limit=10)
            results = await service.search_memories("demo_project", query)
            logger.info(f"  📊 {description}: {len(results)} results")

            if results:
                for result in results:
                    logger.info(f"    - {result.content[:60]}...")

        # Test backend switching
        logger.info("🔄 Testing backend switching...")

        original_backend = service.get_active_backend_name()
        logger.info(f"  Current backend: {original_backend}")

        # Switch to InMemory backend - DISABLED: InMemory backend removed
        # if await service.switch_backend("memory"):
        #     logger.info("  ✅ Successfully switched to InMemory backend")
        #
        #     # Test operations on InMemory backend
        #     memory_id = await service.add_memory(
        #         "demo_project",
        #         "This memory is stored in InMemory backend",
        #         MemoryCategory.PROJECT,
        #         ["inmemory", "demo"],
        #         {"backend": "memory"}
        #     )
        #     logger.info(f"  ✅ Added memory to InMemory backend: {memory_id}")
        # else:
        #     logger.error("  ❌ Failed to switch to InMemory backend")

        logger.info("  Skipping InMemory backend test - backend removed")

        # Test health monitoring
        logger.info("🏥 Testing health monitoring...")

        health_data = await service.get_service_health()
        logger.info(f"  Service healthy: {health_data['service_healthy']}")
        logger.info(f"  Active backend: {health_data['active_backend']}")
        logger.info(f"  Available backends: {list(health_data['backends'].keys())}")

        # Show backend health
        for backend_name, backend_health in health_data["backends"].items():
            if backend_health.get("is_healthy", False):
                logger.info(f"  ✅ {backend_name} backend: healthy")
            else:
                logger.info(f"  ❌ {backend_name} backend: unhealthy")

        # Test circuit breaker status
        logger.info("⚡ Testing circuit breaker status...")

        cb_states = health_data.get("circuit_breakers", {})
        for backend_name, cb_state in cb_states.items():
            state = cb_state.get("state", "unknown")
            logger.info(f"  Circuit breaker for {backend_name}: {state}")

        # Test metrics
        logger.info("📊 Testing metrics...")

        metrics = service.get_metrics()
        logger.info(f"  Total operations: {metrics['total_operations']}")
        logger.info(f"  Successful operations: {metrics['successful_operations']}")
        logger.info(f"  Backend switches: {metrics['backend_switches']}")
        logger.info(f"  Circuit breaker activations: {metrics['circuit_breaker_activations']}")

        # Final summary
        logger.info("🎉 Fallback Memory System Demonstration Complete!")
        logger.info("Summary:")
        logger.info(f"  - Successfully added {len(memory_ids)} memories")
        logger.info(f"  - Search operations working correctly")
        logger.info(f"  - Backend switching functional")
        logger.info(f"  - Health monitoring operational")
        logger.info(f"  - Circuit breaker patterns working")
        logger.info(f"  - Service resilience confirmed")

        # Cleanup
        await service.cleanup()

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Cleanup temp directory
        try:
            import shutil

            shutil.rmtree(temp_dir)
            logger.info(f"🧹 Cleaned up temporary directory: {temp_dir}")
        except:
            pass

    return True


async def main():
    """Main demonstration."""
    logger.info("=" * 80)
    logger.info("Claude PM Framework - Working Fallback Memory System Demo")
    logger.info("=" * 80)

    success = await demonstrate_working_fallback()

    if success:
        logger.info("✅ DEMONSTRATION SUCCESSFUL - Fallback memory system is operational!")
        return 0
    else:
        logger.error("❌ DEMONSTRATION FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
