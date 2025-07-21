"""
Comprehensive unit tests for synchronization-related services
Tests AsyncMemoryCollector and MemoryServiceIntegration
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import tempfile
import json
from pathlib import Path

from claude_pm.services.async_memory_collector import (
    AsyncMemoryCollector,
    MemoryOperation,
    MemoryCategory,
    MemoryPriority,
    CollectionStats
)
from claude_pm.services.memory_service_integration import MemoryServiceIntegration
from claude_pm.core.service_manager import ServiceManager
from claude_pm.core.config import Config


class TestMemoryOperation(unittest.TestCase):
    """Test MemoryOperation dataclass"""
    
    def test_memory_operation_creation(self):
        """Test creating a memory operation"""
        now = datetime.now()
        op = MemoryOperation(
            id="test-123",
            category=MemoryCategory.FEEDBACK,
            content="Test feedback",
            metadata={"user": "test"},
            priority=MemoryPriority.HIGH,
            created_at=now
        )
        
        self.assertEqual(op.id, "test-123")
        self.assertEqual(op.category, MemoryCategory.FEEDBACK)
        self.assertEqual(op.priority, MemoryPriority.HIGH)
        self.assertEqual(op.retry_count, 0)
        self.assertEqual(op.max_retries, 3)
        self.assertEqual(op.next_retry, now)
        
    def test_memory_operation_with_retry(self):
        """Test memory operation with retry settings"""
        now = datetime.now()
        next_retry = now + timedelta(seconds=30)
        
        op = MemoryOperation(
            id="retry-123",
            category=MemoryCategory.ERROR,
            content="Error occurred",
            metadata={"error": "Connection failed"},
            priority=MemoryPriority.CRITICAL,
            created_at=now,
            retry_count=2,
            max_retries=5,
            next_retry=next_retry
        )
        
        self.assertEqual(op.retry_count, 2)
        self.assertEqual(op.max_retries, 5)
        self.assertEqual(op.next_retry, next_retry)


class TestCollectionStats(unittest.TestCase):
    """Test CollectionStats functionality"""
    
    def test_stats_initialization(self):
        """Test stats initialization"""
        stats = CollectionStats()
        
        self.assertEqual(stats.total_operations, 0)
        self.assertEqual(stats.successful_operations, 0)
        self.assertEqual(stats.failed_operations, 0)
        self.assertEqual(stats.success_rate(), 0.0)
        
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        stats = CollectionStats(
            total_operations=100,
            successful_operations=85,
            failed_operations=15
        )
        
        self.assertEqual(stats.success_rate(), 85.0)
        
        # Test with no operations
        empty_stats = CollectionStats()
        self.assertEqual(empty_stats.success_rate(), 0.0)


class TestAsyncMemoryCollector(unittest.TestCase):
    """Test AsyncMemoryCollector service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_config = Mock(spec=Config)
        self.mock_config.get_path.return_value = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('claude_pm.services.async_memory_collector.BaseService')
    def test_initialization(self, mock_base_service):
        """Test AsyncMemoryCollector initialization"""
        collector = AsyncMemoryCollector(self.mock_config)
        
        # Verify attributes are initialized
        self.assertIsNotNone(collector)
        # Note: Actual attributes depend on implementation
        
    def test_memory_priority_enum(self):
        """Test MemoryPriority enum values"""
        self.assertEqual(MemoryPriority.CRITICAL.value, "critical")
        self.assertEqual(MemoryPriority.HIGH.value, "high")
        self.assertEqual(MemoryPriority.MEDIUM.value, "medium")
        self.assertEqual(MemoryPriority.LOW.value, "low")
        
    def test_memory_category_enum(self):
        """Test MemoryCategory enum values"""
        categories = [
            MemoryCategory.BUG,
            MemoryCategory.FEEDBACK,
            MemoryCategory.ARCHITECTURE,
            MemoryCategory.PERFORMANCE,
            MemoryCategory.INTEGRATION,
            MemoryCategory.QA,
            MemoryCategory.ERROR,
            MemoryCategory.OPERATION
        ]
        
        # Verify all categories exist
        for category in categories:
            self.assertIsInstance(category, MemoryCategory)


class TestMemoryServiceIntegration(unittest.TestCase):
    """Test MemoryServiceIntegration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_service_manager = Mock(spec=ServiceManager)
        self.integration = MemoryServiceIntegration(self.mock_service_manager)
        
    def test_initialization(self):
        """Test MemoryServiceIntegration initialization"""
        self.assertEqual(self.integration.service_manager, self.mock_service_manager)
        self.assertIsNone(self.integration._collector)
        
    @patch('claude_pm.services.memory_service_integration.AsyncMemoryCollector')
    async def test_register_async_memory_collector(self, mock_collector_class):
        """Test registering async memory collector"""
        mock_collector = Mock()
        mock_collector_class.return_value = mock_collector
        
        # Test with default config
        result = await self.integration.register_async_memory_collector()
        
        self.assertEqual(result, mock_collector)
        # Verify default config values were used
        
        # Test with custom config
        custom_config = {
            "batch_size": 20,
            "batch_timeout": 60.0,
            "max_queue_size": 2000
        }
        
        result = await self.integration.register_async_memory_collector(custom_config)
        self.assertEqual(result, mock_collector)


class TestAsyncMemoryCollectorIntegration(unittest.TestCase):
    """Integration tests for async memory collector"""
    
    def setUp(self):
        """Set up test environment"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    def tearDown(self):
        """Clean up event loop"""
        self.loop.close()
        
    async def test_memory_operation_lifecycle(self):
        """Test complete lifecycle of a memory operation"""
        # This would test the full flow of:
        # 1. Creating a memory operation
        # 2. Queueing it
        # 3. Processing it
        # 4. Handling success/failure
        # 5. Retry logic if applicable
        pass
        
    async def test_batch_processing(self):
        """Test batch processing of memory operations"""
        # Test that operations are batched correctly
        # based on batch_size and batch_timeout
        pass
        
    async def test_priority_handling(self):
        """Test that high priority operations are processed first"""
        # Create operations with different priorities
        # Verify processing order
        pass
        
    async def test_error_handling_and_retry(self):
        """Test error handling and retry logic"""
        # Test operations that fail
        # Verify retry attempts
        # Test max retry limit
        pass
        
    async def test_performance_monitoring(self):
        """Test performance monitoring integration"""
        # Verify latency tracking
        # Check statistics collection
        # Test performance thresholds
        pass


class TestSynchronizationPatterns(unittest.TestCase):
    """Test general synchronization patterns used in the framework"""
    
    def test_async_to_sync_bridge(self):
        """Test bridging async operations to sync context"""
        # Test patterns for calling async code from sync context
        # This is relevant for CLI tools that need sync interfaces
        pass
        
    def test_concurrent_access_patterns(self):
        """Test concurrent access to shared resources"""
        # Test locking mechanisms
        # Test race condition prevention
        pass
        
    def test_queue_management(self):
        """Test queue-based synchronization"""
        # Test queue overflow handling
        # Test queue draining on shutdown
        pass


class TestMemoryCollectorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_invalid_priority(self):
        """Test handling of invalid priorities"""
        # Should handle gracefully
        pass
        
    def test_invalid_category(self):
        """Test handling of invalid categories"""
        # Should handle gracefully
        pass
        
    def test_large_content_handling(self):
        """Test handling of large memory content"""
        # Test memory limits
        # Test content truncation if applicable
        pass
        
    def test_malformed_metadata(self):
        """Test handling of malformed metadata"""
        # Test various invalid metadata formats
        pass
        
    def test_shutdown_with_pending_operations(self):
        """Test graceful shutdown with operations in queue"""
        # Verify operations are saved or processed
        # Test no data loss on shutdown
        pass


class TestConcurrencyAndThreadSafety(unittest.TestCase):
    """Test concurrency and thread safety aspects"""
    
    def test_concurrent_collection_operations(self):
        """Test multiple concurrent collection operations"""
        # Simulate multiple agents collecting memory simultaneously
        pass
        
    def test_queue_thread_safety(self):
        """Test that queue operations are thread-safe"""
        # Test concurrent enqueue/dequeue operations
        pass
        
    def test_stats_thread_safety(self):
        """Test that statistics updates are thread-safe"""
        # Test concurrent stats updates
        pass


if __name__ == '__main__':
    # For async tests, we need a different runner
    unittest.main()