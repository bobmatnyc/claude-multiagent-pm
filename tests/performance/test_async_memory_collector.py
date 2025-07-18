"""
Test suite for AsyncMemoryCollector service.

Comprehensive tests for fire-and-forget memory collection,
queue processing, error handling, and performance characteristics.
"""

import asyncio
import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, patch

from claude_pm.services.async_memory_collector import (
    AsyncMemoryCollector,
    MemoryOperation,
    MemoryCategory,
    MemoryPriority,
    CollectionStats
)
from claude_pm.services.memory_service_integration import MemoryServiceIntegration
from claude_pm.core.service_manager import ServiceManager
from claude_pm.config.async_memory_config import get_config, validate_config


class TestAsyncMemoryCollector:
    """Test suite for AsyncMemoryCollector."""
    
    @pytest.fixture
    async def collector(self):
        """Create AsyncMemoryCollector instance for testing."""
        config = get_config("development")
        collector = AsyncMemoryCollector(config)
        await collector.start()
        yield collector
        await collector.stop()
    
    @pytest.fixture
    async def service_manager(self):
        """Create ServiceManager instance for testing."""
        manager = ServiceManager()
        yield manager
        if manager._running:
            await manager.stop_all()
    
    @pytest.fixture
    async def integration(self, service_manager):
        """Create MemoryServiceIntegration for testing."""
        integration = MemoryServiceIntegration(service_manager)
        yield integration
    
    def test_memory_operation_creation(self):
        """Test MemoryOperation dataclass creation."""
        from datetime import datetime
        
        operation = MemoryOperation(
            id="test_op_1",
            category=MemoryCategory.BUG,
            content="Test bug report",
            metadata={"severity": "high"},
            priority=MemoryPriority.CRITICAL,
            created_at=datetime.now()
        )
        
        assert operation.id == "test_op_1"
        assert operation.category == MemoryCategory.BUG
        assert operation.content == "Test bug report"
        assert operation.metadata["severity"] == "high"
        assert operation.priority == MemoryPriority.CRITICAL
        assert operation.retry_count == 0
        assert operation.max_retries == 3
        assert operation.next_retry is not None
    
    def test_collection_stats_success_rate(self):
        """Test CollectionStats success rate calculation."""
        stats = CollectionStats()
        
        # Test with no operations
        assert stats.success_rate() == 0.0
        
        # Test with operations
        stats.total_operations = 10
        stats.successful_operations = 8
        stats.failed_operations = 2
        
        assert stats.success_rate() == 80.0
    
    @pytest.mark.asyncio
    async def test_collector_initialization(self):
        """Test AsyncMemoryCollector initialization."""
        config = get_config("development")
        collector = AsyncMemoryCollector(config)
        
        assert collector.batch_size == 5
        assert collector.max_queue_size == 500
        assert collector.cache_enabled is True
        assert collector.stats.total_operations == 0
        assert not collector.running
        
        await collector.start()
        assert collector.running
        
        await collector.stop()
        assert not collector.running
    
    @pytest.mark.asyncio
    async def test_collect_async_basic(self, collector):
        """Test basic async collection functionality."""
        # Test valid collection
        op_id = await collector.collect_async(
            category="bug",
            content="Test bug report",
            metadata={"severity": "high"},
            priority="critical"
        )
        
        assert op_id is not None
        assert op_id.startswith("op_")
        assert collector.stats.total_operations == 1
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Test invalid category
        with pytest.raises(ValueError, match="Invalid category"):
            await collector.collect_async(
                category="invalid_category",
                content="Test content",
                metadata={}
            )
        
        # Test invalid priority
        with pytest.raises(ValueError, match="Invalid priority"):
            await collector.collect_async(
                category="bug",
                content="Test content",
                metadata={},
                priority="invalid_priority"
            )
    
    @pytest.mark.asyncio
    async def test_collect_async_different_categories(self, collector):
        """Test collection with different memory categories."""
        categories = ["bug", "feedback", "architecture", "performance", "integration", "qa", "error", "operation"]
        
        for category in categories:
            op_id = await collector.collect_async(
                category=category,
                content=f"Test {category} content",
                metadata={"category": category}
            )
            assert op_id is not None
        
        assert collector.stats.total_operations == len(categories)
    
    @pytest.mark.asyncio
    async def test_collect_async_different_priorities(self, collector):
        """Test collection with different priority levels."""
        priorities = ["critical", "high", "medium", "low"]
        
        for priority in priorities:
            op_id = await collector.collect_async(
                category="bug",
                content=f"Test {priority} priority content",
                metadata={"priority": priority},
                priority=priority
            )
            assert op_id is not None
        
        assert collector.stats.total_operations == len(priorities)
    
    @pytest.mark.asyncio
    async def test_queue_processing(self, collector):
        """Test queue processing and batch operations."""
        # Submit multiple operations
        operation_count = 10
        for i in range(operation_count):
            await collector.collect_async(
                category="performance",
                content=f"Performance test {i}",
                metadata={"test_id": i}
            )
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Check stats
        stats = await collector.get_stats()
        assert stats.total_operations == operation_count
        assert stats.batch_operations > 0
    
    @pytest.mark.asyncio
    async def test_flush_queue(self, collector):
        """Test queue flushing functionality."""
        # Submit operations
        for i in range(5):
            await collector.collect_async(
                category="qa",
                content=f"QA test {i}",
                metadata={"test_id": i}
            )
        
        # Flush queue
        processed = await collector.flush_queue(timeout=5.0)
        assert processed >= 0
        
        # Queue should be empty after flush
        stats = await collector.get_stats()
        assert stats.queue_size == 0
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, collector):
        """Test cache functionality."""
        assert collector.cache_enabled is True
        
        # Submit operations that might be cached
        content = "Cached content test"
        for i in range(3):
            await collector.collect_async(
                category="architecture",
                content=content,
                metadata={"iteration": i}
            )
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Check cache stats
        stats = await collector.get_stats()
        assert stats.cache_hits + stats.cache_misses > 0
    
    @pytest.mark.asyncio
    async def test_performance_characteristics(self, collector):
        """Test performance characteristics."""
        operation_count = 50
        start_time = time.time()
        
        # Submit operations
        tasks = []
        for i in range(operation_count):
            task = collector.collect_async(
                category="performance",
                content=f"Performance test {i}",
                metadata={"test_id": i}
            )
            tasks.append(task)
        
        # Wait for all submissions
        await asyncio.gather(*tasks)
        
        submission_time = time.time() - start_time
        avg_latency = submission_time / operation_count
        
        # Check performance requirements
        assert avg_latency < 0.1  # Less than 100ms per operation
        assert collector.stats.total_operations == operation_count
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check processing stats
        stats = await collector.get_stats()
        assert stats.average_latency < 5.0  # Less than 5s average processing
    
    @pytest.mark.asyncio
    async def test_error_handling(self, collector):
        """Test error handling and recovery."""
        # Test with mock storage failure
        with patch.object(collector, '_store_memory', side_effect=Exception("Storage failed")):
            # Submit operation
            op_id = await collector.collect_async(
                category="error",
                content="Test error handling",
                metadata={"test": "error_handling"}
            )
            
            # Wait for processing attempt
            await asyncio.sleep(0.5)
            
            # Check that operation was queued but might have failed
            stats = await collector.get_stats()
            assert stats.total_operations >= 1
    
    @pytest.mark.asyncio
    async def test_health_check(self, collector):
        """Test health check functionality."""
        health = await collector.health_check()
        
        assert health.status in ["healthy", "degraded", "unhealthy"]
        assert "queue_operational" in health.checks
        assert "queue_size_ok" in health.checks
        assert "success_rate_ok" in health.checks
        assert "average_latency_ok" in health.checks
        
        if collector.cache_enabled:
            assert "cache_operational" in health.checks
    
    @pytest.mark.asyncio
    async def test_service_integration(self, integration, service_manager):
        """Test service integration functionality."""
        # Register collector
        config = get_config("development")
        collector = await integration.register_async_memory_collector(config)
        
        assert collector is not None
        assert collector.name == "async_memory_collector"
        
        # Start services
        await service_manager.start_all()
        
        # Test integration methods
        bug_id = await integration.collect_bug("Integration test bug")
        assert bug_id is not None
        
        feedback_id = await integration.collect_feedback("Integration test feedback")
        assert feedback_id is not None
        
        error_id = await integration.collect_error("Integration test error")
        assert error_id is not None
        
        perf_id = await integration.collect_performance_data("Integration test performance")
        assert perf_id is not None
        
        arch_id = await integration.collect_architecture_info("Integration test architecture")
        assert arch_id is not None
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Check stats
        stats = await integration.get_collection_stats()
        assert stats is not None
        assert stats["total_operations"] >= 5
        
        # Test flush
        flushed = await integration.flush_collector()
        assert flushed is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, collector):
        """Test concurrent operation handling."""
        # Submit operations concurrently
        tasks = []
        for i in range(20):
            task = collector.collect_async(
                category="integration",
                content=f"Concurrent test {i}",
                metadata={"test_id": i}
            )
            tasks.append(task)
        
        # Wait for all submissions
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(result is not None for result in results)
        assert collector.stats.total_operations == 20
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Check final stats
        stats = await collector.get_stats()
        assert stats.total_operations == 20


class TestAsyncMemoryConfig:
    """Test suite for async memory configuration."""
    
    def test_get_config_default(self):
        """Test getting default configuration."""
        config = get_config("default")
        
        assert config["batch_size"] == 10
        assert config["max_queue_size"] == 1000
        assert config["cache"]["enabled"] is True
    
    def test_get_config_environments(self):
        """Test getting configuration for different environments."""
        dev_config = get_config("development")
        prod_config = get_config("production")
        
        assert dev_config["batch_size"] == 5
        assert prod_config["batch_size"] == 20
        
        assert dev_config["max_queue_size"] == 500
        assert prod_config["max_queue_size"] == 2000
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config = get_config("default")
        assert validate_config(config) is True
    
    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config."""
        invalid_configs = [
            {"batch_size": 0},  # Invalid batch size
            {"batch_size": 10, "max_queue_size": -1},  # Invalid queue size
            {"batch_size": 10, "max_queue_size": 100, "max_retries": -1},  # Invalid retries
            {"batch_size": 10, "max_queue_size": 100, "cache": "invalid"}  # Invalid cache config
        ]
        
        for config in invalid_configs:
            assert validate_config(config) is False
    
    def test_config_immutability(self):
        """Test that config modifications don't affect original."""
        config1 = get_config("default")
        config2 = get_config("default")
        
        config1["batch_size"] = 999
        assert config2["batch_size"] == 10  # Original unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])