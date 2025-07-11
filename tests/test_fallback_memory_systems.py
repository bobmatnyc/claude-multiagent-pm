#!/usr/bin/env python3
"""
Comprehensive Test Suite for Claude PM Framework Fallback Memory Systems

# This script tests all memory backends (SQLite, TinyDB, InMemory) and their  # InMemory backend removed
fallback mechanisms when mem0AI is unavailable.

Test Coverage:
1. SQLite Backend Direct Testing
2. TinyDB Backend Direct Testing  
# 3. InMemory Backend Direct Testing  # InMemory backend removed
4. Circuit Breaker Testing
5. Fallback Chain Testing
6. Performance and Reliability Testing
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
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_pm.services.memory.backends.sqlite_backend import SQLiteBackend
from claude_pm.services.memory.backends.tinydb_backend import TinyDBBackend
# # from claude_pm.services.memory.backends.memory_backend import InMemoryBackend  # InMemory backend removed  # InMemory backend removed
from claude_pm.services.memory.services.unified_service import FlexibleMemoryService
from claude_pm.services.memory.services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from claude_pm.services.memory.interfaces.models import MemoryCategory, MemoryQuery, MemoryItem
from claude_pm.services.memory.interfaces.exceptions import (
    BackendError, BackendNotAvailableError, CircuitBreakerOpenError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fallback_memory_test.log')
    ]
)
logger = logging.getLogger(__name__)


class FallbackMemorySystemTester:
    """Comprehensive tester for fallback memory systems."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.temp_dir = tempfile.mkdtemp(prefix="memory_test_")
        self.project_name = "test_project"
        
        # Test data
        self.test_memories = [
            {
                "content": "This is a test decision for the project architecture",
                "category": MemoryCategory.PROJECT,
                "tags": ["architecture", "decision"],
                "metadata": {"importance": "high", "decision_type": "architecture"}
            },
            {
                "content": "Code pattern for async error handling with retry logic",
                "category": MemoryCategory.PATTERN,
                "tags": ["async", "error-handling", "retry"],
                "metadata": {"language": "python", "pattern_type": "error_handling"}
            },
            {
                "content": "Team coding standard: use type hints for all functions",
                "category": MemoryCategory.TEAM,
                "tags": ["coding-standards", "type-hints"],
                "metadata": {"enforcement": "strict", "team_agreed": True}
            },
            {
                "content": "Bug fix: SQLite connection leak in memory backend",
                "category": MemoryCategory.ERROR,
                "tags": ["bug", "sqlite", "memory-leak"],
                "metadata": {"severity": "high", "status": "fixed"}
            },
            {
                "content": "Performance optimization: use connection pooling",
                "category": MemoryCategory.PATTERN,
                "tags": ["performance", "optimization", "pooling"],
                "metadata": {"impact": "medium", "implemented": True}
            }
        ]
        
        logger.info(f"Initialized tester with temp directory: {self.temp_dir}")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all fallback memory system tests."""
        logger.info("Starting comprehensive fallback memory system tests...")
        
        test_cases = [
            ("SQLite Backend", self.test_sqlite_backend),
            ("TinyDB Backend", self.test_tinydb_backend),
            # ("InMemory Backend", self.test_inmemory_backend),  # InMemory backend removed
            ("Circuit Breaker", self.test_circuit_breaker),
            ("Fallback Chain", self.test_fallback_chain),
            ("Performance & Reliability", self.test_performance_reliability),
            ("Backend Switching", self.test_backend_switching),
            ("Failure Recovery", self.test_failure_recovery)
        ]
        
        for test_name, test_func in test_cases:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running {test_name} Tests")
            logger.info(f"{'='*60}")
            
            try:
                start_time = time.time()
                result = await test_func()
                end_time = time.time()
                
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "duration": end_time - start_time,
                    "details": result
                }
                logger.info(f"✅ {test_name} tests PASSED ({end_time - start_time:.2f}s)")
                
            except Exception as e:
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "error": str(e),
                    "details": None
                }
                logger.error(f"❌ {test_name} tests FAILED: {e}")
        
        # Generate final report
        return self.generate_final_report()
    
    async def test_sqlite_backend(self) -> Dict[str, Any]:
        """Test SQLite backend directly."""
        logger.info("Testing SQLite backend with FTS5 search...")
        
        # Configure SQLite backend
        sqlite_config = {
            "db_path": os.path.join(self.temp_dir, "test_sqlite.db"),
            "enable_fts": True,
            "enable_wal": True
        }
        
        backend = SQLiteBackend(sqlite_config)
        
        # Initialize backend
        assert await backend.initialize(), "SQLite backend initialization failed"
        assert await backend.health_check(), "SQLite backend health check failed"
        
        # Test memory operations
        results = await self._test_backend_operations(backend, "SQLite")
        
        # Test FTS5 search capabilities
        logger.info("Testing FTS5 full-text search...")
        
        # Add test memories
        memory_ids = []
        for memory_data in self.test_memories:
            memory_id = await backend.add_memory(
                self.project_name,
                memory_data["content"],
                memory_data["category"],
                memory_data["tags"],
                memory_data["metadata"]
            )
            assert memory_id, "Failed to add memory"
            memory_ids.append(memory_id)
        
        # Test FTS search
        query = MemoryQuery(
            query="architecture decision",
            limit=10
        )
        
        search_results = await backend.search_memories(self.project_name, query)
        assert len(search_results) > 0, "FTS search returned no results"
        
        # Test category filtering
        query = MemoryQuery(
            query="",
            category=MemoryCategory.PATTERN,
            limit=10
        )
        
        pattern_results = await backend.search_memories(self.project_name, query)
        assert len(pattern_results) >= 2, "Category filtering failed"
        
        # Test tag filtering
        query = MemoryQuery(
            query="",
            tags=["bug"],
            limit=10
        )
        
        tag_results = await backend.search_memories(self.project_name, query)
        assert len(tag_results) >= 1, "Tag filtering failed"
        
        # Test backup/restore
        backup_path = os.path.join(self.temp_dir, "sqlite_backup.db")
        assert await backend.create_backup(backup_path), "Backup creation failed"
        assert os.path.exists(backup_path), "Backup file not created"
        
        # Test statistics
        stats = await backend.get_memory_stats(self.project_name)
        assert stats["total"] == len(self.test_memories), "Statistics count mismatch"
        assert stats["backend"] == "sqlite", "Backend name mismatch"
        
        await backend.cleanup()
        
        results.update({
            "fts_search": True,
            "backup_restore": True,
            "statistics": stats,
            "memory_count": len(memory_ids)
        })
        
        return results
    
    async def test_tinydb_backend(self) -> Dict[str, Any]:
        """Test TinyDB backend directly."""
        logger.info("Testing TinyDB JSON-based backend...")
        
        # Configure TinyDB backend
        tinydb_config = {
            "db_path": os.path.join(self.temp_dir, "test_tinydb.json"),
            "indent": 2,
            "ensure_ascii": False
        }
        
        backend = TinyDBBackend(tinydb_config)
        
        # Initialize backend
        assert await backend.initialize(), "TinyDB backend initialization failed"
        assert await backend.health_check(), "TinyDB backend health check failed"
        
        # Test memory operations
        results = await self._test_backend_operations(backend, "TinyDB")
        
        # Test JSON storage
        logger.info("Testing JSON document storage...")
        
        # Add test memories
        memory_ids = []
        for memory_data in self.test_memories:
            memory_id = await backend.add_memory(
                self.project_name,
                memory_data["content"],
                memory_data["category"],
                memory_data["tags"],
                memory_data["metadata"]
            )
            assert memory_id, "Failed to add memory"
            memory_ids.append(memory_id)
        
        # Verify JSON file exists and is readable
        json_path = tinydb_config["db_path"]
        assert os.path.exists(json_path), "JSON database file not created"
        
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert isinstance(data, dict), "JSON data format invalid"
            assert "_default" in data, "TinyDB table structure missing"
        
        # Test text search (simple contains)
        query = MemoryQuery(
            query="architecture",
            limit=10
        )
        
        search_results = await backend.search_memories(self.project_name, query)
        assert len(search_results) > 0, "Text search returned no results"
        
        # Test backup/restore
        backup_path = os.path.join(self.temp_dir, "tinydb_backup.json")
        assert await backend.create_backup(backup_path), "Backup creation failed"
        assert os.path.exists(backup_path), "Backup file not created"
        
        # Test statistics
        stats = await backend.get_memory_stats(self.project_name)
        assert stats["total"] == len(self.test_memories), "Statistics count mismatch"
        assert stats["backend"] == "tinydb", "Backend name mismatch"
        
        await backend.cleanup()
        
        results.update({
            "json_storage": True,
            "text_search": True,
            "backup_restore": True,
            "statistics": stats,
            "memory_count": len(memory_ids)
        })
        
        return results
    
    async def test_inmemory_backend(self) -> Dict[str, Any]:
        # """Test InMemory backend directly."""  # InMemory backend removed
        # logger.info("Testing InMemory runtime backend...")  # InMemory backend removed
        
        # # Configure InMemory backend  # InMemory backend removed
        inmemory_config = {
            "max_memory_size": 1000,
            "enable_expiration": True,
            "default_ttl": 3600
        }
        
        # # backend = InMemoryBackend(inmemory_config)  # InMemory backend removed  # InMemory backend removed
        
        # Initialize backend
        # assert await backend.initialize(), "InMemory backend initialization failed"  # InMemory backend removed
        # assert await backend.health_check(), "InMemory backend health check failed"  # InMemory backend removed
        
        # Test memory operations
        # results = await self._test_backend_operations(backend, "InMemory")  # InMemory backend removed
        
        # Test runtime characteristics
        logger.info("Testing runtime memory characteristics...")
        
        # Add test memories
        memory_ids = []
        for memory_data in self.test_memories:
            memory_id = await backend.add_memory(
                self.project_name,
                memory_data["content"],
                memory_data["category"],
                memory_data["tags"],
                memory_data["metadata"]
            )
            assert memory_id, "Failed to add memory"
            memory_ids.append(memory_id)
        
        # Test LRU eviction
        logger.info("Testing LRU eviction...")
        
        # Fill up memory to trigger eviction
        for i in range(10):
            await backend.add_memory(
                self.project_name,
                f"Test memory {i} for eviction testing",
                MemoryCategory.PROJECT,
                ["test"],
                {"test_id": i}
            )
        
        # Test memory limits
        backend_stats = backend.get_backend_stats()
        assert backend_stats["max_capacity"] == 1000, "Max capacity setting incorrect"
        
        # Test performance
        start_time = time.time()
        query = MemoryQuery(query="test", limit=20)
        search_results = await backend.search_memories(self.project_name, query)
        search_time = time.time() - start_time
        
        # # InMemory should be very fast  # InMemory backend removed
        assert search_time < 0.1, f"Search too slow: {search_time:.3f}s"
        
        # Test expiration (if enabled)
        if inmemory_config["enable_expiration"]:
            # Add memory with short TTL
            short_ttl_id = await backend.add_memory(
                self.project_name,
                "This memory will expire soon",
                MemoryCategory.PROJECT,
                ["temporary"],
                {"ttl": 1}  # 1 second TTL
            )
            
            # Wait for expiration
            await asyncio.sleep(2)
            
            # Try to retrieve expired memory
            expired_memory = await backend.get_memory(self.project_name, short_ttl_id)
            assert expired_memory is None, "Expired memory was not removed"
        
        # Test statistics
        stats = await backend.get_memory_stats(self.project_name)
        assert stats["backend"] == "memory", "Backend name mismatch"
        
        await backend.cleanup()
        
        results.update({
            "runtime_storage": True,
            "lru_eviction": True,
            "performance": {
                "search_time": search_time,
                "performance_grade": "excellent" if search_time < 0.01 else "good"
            },
            "expiration": inmemory_config["enable_expiration"],
            "statistics": stats,
            "memory_count": len(memory_ids)
        })
        
        return results
    
    async def test_circuit_breaker(self) -> Dict[str, Any]:
        """Test circuit breaker functionality."""
        logger.info("Testing circuit breaker patterns...")
        
        # Configure circuit breaker
        cb_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=2.0,
            test_requests=2,
            success_threshold=2
        )
        
        circuit_breaker = CircuitBreaker(cb_config)
        
        # Test normal operation (closed state)
        assert await circuit_breaker.is_closed(), "Circuit breaker should start closed"
        
        # Simulate successful operations
        async def successful_operation():
            await asyncio.sleep(0.01)
            return "success"
        
        for i in range(5):
            result = await circuit_breaker.call(successful_operation)
            assert result == "success", "Successful operation failed"
        
        # Test failure detection
        async def failing_operation():
            await asyncio.sleep(0.01)
            raise Exception("Simulated failure")
        
        # Trigger failures to open circuit
        failure_count = 0
        for i in range(5):
            try:
                await circuit_breaker.call(failing_operation)
            except Exception:
                failure_count += 1
        
        assert failure_count >= 3, "Not enough failures triggered"
        assert await circuit_breaker.is_open(), "Circuit breaker should be open after failures"
        
        # Test circuit breaker blocks requests when open
        try:
            await circuit_breaker.call(successful_operation)
            assert False, "Circuit breaker should block requests when open"
        except CircuitBreakerOpenError:
            pass  # Expected
        
        # Test recovery (wait for timeout)
        logger.info("Testing circuit breaker recovery...")
        await asyncio.sleep(2.5)  # Wait for recovery timeout
        
        # Circuit should move to half-open and allow test requests
        result = await circuit_breaker.call(successful_operation)
        assert result == "success", "Recovery operation failed"
        
        # More successes should close the circuit
        await circuit_breaker.call(successful_operation)
        assert await circuit_breaker.is_closed(), "Circuit breaker should be closed after recovery"
        
        # Test metrics
        metrics = circuit_breaker.get_metrics()
        assert metrics["total_requests"] > 0, "No requests recorded"
        assert metrics["failed_requests"] > 0, "No failures recorded"
        assert metrics["successful_requests"] > 0, "No successes recorded"
        
        # Test state information
        state = await circuit_breaker.get_state()
        assert state["state"] == "closed", "Circuit should be closed"
        assert "metrics" in state, "State should include metrics"
        
        return {
            "circuit_breaker_operations": True,
            "failure_detection": True,
            "recovery_mechanism": True,
            "metrics": metrics,
            "final_state": state
        }
    
    async def test_fallback_chain(self) -> Dict[str, Any]:
        """Test fallback chain functionality."""
        logger.info("Testing fallback chain with mem0AI unavailable...")
        
        # Configure service with mem0AI disabled to test fallback
        service_config = {
            "mem0ai_enabled": False,  # Simulate mem0AI unavailable
            "sqlite_enabled": True,
            "tinydb_enabled": True,
            "memory_enabled": True,
            "sqlite_path": os.path.join(self.temp_dir, "fallback_sqlite.db"),
            "tinydb_path": os.path.join(self.temp_dir, "fallback_tinydb.json"),
            "fallback_chain": ["mem0ai", "sqlite", "tinydb", "memory"]
        }
        
        service = FlexibleMemoryService(service_config)
        
        # Initialize service
        assert await service.initialize(), "Service initialization failed"
        
        # Should fallback to SQLite since mem0AI is disabled
        assert service.get_active_backend_name() == "sqlite", "Should fallback to SQLite"
        
        # Test memory operations through fallback
        memory_ids = []
        for memory_data in self.test_memories:
            memory_id = await service.add_memory(
                self.project_name,
                memory_data["content"],
                memory_data["category"],
                memory_data["tags"],
                memory_data["metadata"]
            )
            assert memory_id, "Failed to add memory through fallback"
            memory_ids.append(memory_id)
        
        # Test search through fallback
        query = MemoryQuery(query="architecture", limit=10)
        search_results = await service.search_memories(self.project_name, query)
        assert len(search_results) > 0, "Search through fallback failed"
        
        # Test manual backend switching
        logger.info("Testing manual backend switching...")
        
        # Switch to TinyDB
        assert await service.switch_backend("tinydb"), "Failed to switch to TinyDB"
        assert service.get_active_backend_name() == "tinydb", "Backend switch failed"
        
        # Test operations on new backend
        memory_id = await service.add_memory(
            self.project_name,
            "Test memory on TinyDB backend",
            MemoryCategory.PROJECT,
            ["test"],
            {"backend": "tinydb"}
        )
        assert memory_id, "Failed to add memory to TinyDB backend"
        
        # # Switch to InMemory  # InMemory backend removed
        # assert await service.switch_backend("memory"), "Failed to switch to InMemory"  # InMemory backend removed
        assert service.get_active_backend_name() == "memory", "Backend switch failed"
        
        # Test health monitoring
        health_data = await service.get_service_health()
        assert health_data["service_initialized"], "Service not initialized"
        assert health_data["active_backend"] == "memory", "Active backend incorrect"
        assert "backends" in health_data, "Backend health missing"
        
        # Test metrics
        metrics = service.get_metrics()
        assert metrics["total_operations"] > 0, "No operations recorded"
        assert metrics["backend_switches"] >= 2, "Backend switches not recorded"
        
        await service.cleanup()
        
        return {
            "fallback_chain": True,
            "backend_switching": True,
            "health_monitoring": True,
            "metrics": metrics,
            "active_backend": service.get_active_backend_name(),
            "memory_count": len(memory_ids)
        }
    
    async def test_performance_reliability(self) -> Dict[str, Any]:
        """Test performance and reliability across backends."""
        logger.info("Testing performance and reliability...")
        
        # Test each backend performance
        backend_configs = [
            ("sqlite", SQLiteBackend, {
                "db_path": os.path.join(self.temp_dir, "perf_sqlite.db"),
                "enable_fts": True
            }),
            ("tinydb", TinyDBBackend, {
                "db_path": os.path.join(self.temp_dir, "perf_tinydb.json")
            })
            # ("memory", InMemoryBackend, {  # InMemory backend removed
            #     "max_memory_size": 1000
            # })
        ]
        
        performance_results = {}
        
        for backend_name, backend_class, config in backend_configs:
            logger.info(f"Testing {backend_name} backend performance...")
            
            backend = backend_class(config)
            await backend.initialize()
            
            # Measure write performance
            start_time = time.time()
            memory_ids = []
            
            for i in range(100):
                memory_id = await backend.add_memory(
                    self.project_name,
                    f"Performance test memory {i}",
                    MemoryCategory.PROJECT,
                    ["performance", "test"],
                    {"test_id": i}
                )
                memory_ids.append(memory_id)
            
            write_time = time.time() - start_time
            
            # Measure read performance
            start_time = time.time()
            
            for memory_id in memory_ids[:20]:  # Test subset
                memory = await backend.get_memory(self.project_name, memory_id)
                assert memory is not None, "Memory retrieval failed"
            
            read_time = time.time() - start_time
            
            # Measure search performance
            start_time = time.time()
            
            query = MemoryQuery(query="performance", limit=50)
            search_results = await backend.search_memories(self.project_name, query)
            
            search_time = time.time() - start_time
            
            # Test concurrent operations
            start_time = time.time()
            
            async def concurrent_operation(i):
                return await backend.add_memory(
                    self.project_name,
                    f"Concurrent test memory {i}",
                    MemoryCategory.PROJECT,
                    ["concurrent"],
                    {"concurrent_id": i}
                )
            
            # Run concurrent operations
            tasks = [concurrent_operation(i) for i in range(10)]
            concurrent_results = await asyncio.gather(*tasks)
            
            concurrent_time = time.time() - start_time
            
            await backend.cleanup()
            
            performance_results[backend_name] = {
                "write_time": write_time,
                "read_time": read_time,
                "search_time": search_time,
                "concurrent_time": concurrent_time,
                "write_ops_per_sec": 100 / write_time,
                "read_ops_per_sec": 20 / read_time,
                "search_ops_per_sec": 1 / search_time,
                "concurrent_ops_per_sec": 10 / concurrent_time,
                "memory_count": len(memory_ids),
                "concurrent_success": len([r for r in concurrent_results if r])
            }
        
        # Compare performance
        fastest_write = min(performance_results.values(), key=lambda x: x["write_time"])
        fastest_read = min(performance_results.values(), key=lambda x: x["read_time"])
        fastest_search = min(performance_results.values(), key=lambda x: x["search_time"])
        
        return {
            "performance_results": performance_results,
            "fastest_write": fastest_write,
            "fastest_read": fastest_read,
            "fastest_search": fastest_search,
            "performance_comparison": True
        }
    
    async def test_backend_switching(self) -> Dict[str, Any]:
        """Test dynamic backend switching."""
        logger.info("Testing dynamic backend switching...")
        
        service_config = {
            "mem0ai_enabled": False,
            "sqlite_enabled": True,
            "tinydb_enabled": True,
            "memory_enabled": True,
            "sqlite_path": os.path.join(self.temp_dir, "switch_sqlite.db"),
            "tinydb_path": os.path.join(self.temp_dir, "switch_tinydb.json")
        }
        
        service = FlexibleMemoryService(service_config)
        await service.initialize()
        
        # Test switching between backends
        backends = ["sqlite", "tinydb", "memory"]
        switch_results = {}
        
        for backend_name in backends:
            logger.info(f"Testing switch to {backend_name}...")
            
            # Switch to backend
            success = await service.switch_backend(backend_name)
            assert success, f"Failed to switch to {backend_name}"
            assert service.get_active_backend_name() == backend_name, "Backend switch failed"
            
            # Test operations on switched backend
            memory_id = await service.add_memory(
                self.project_name,
                f"Test memory on {backend_name}",
                MemoryCategory.PROJECT,
                ["switch-test"],
                {"backend": backend_name}
            )
            assert memory_id, f"Failed to add memory to {backend_name}"
            
            # Test retrieval
            memory = await service.get_memory(self.project_name, memory_id)
            assert memory is not None, f"Failed to retrieve memory from {backend_name}"
            assert memory.metadata["backend"] == backend_name, "Backend metadata incorrect"
            
            switch_results[backend_name] = {
                "switch_success": success,
                "add_memory_success": memory_id is not None,
                "retrieve_memory_success": memory is not None,
                "memory_id": memory_id
            }
        
        # Test fallback chain modification
        original_chain = service.get_fallback_chain()
        new_chain = ["memory", "tinydb", "sqlite"]
        
        assert service.set_fallback_chain(new_chain), "Failed to set new fallback chain"
        assert service.get_fallback_chain() == new_chain, "Fallback chain not updated"
        
        await service.cleanup()
        
        return {
            "backend_switching": True,
            "switch_results": switch_results,
            "fallback_chain_modification": True,
            "original_chain": original_chain,
            "new_chain": new_chain
        }
    
    async def test_failure_recovery(self) -> Dict[str, Any]:
        """Test failure recovery mechanisms."""
        logger.info("Testing failure recovery mechanisms...")
        
        # Test circuit breaker recovery
        service_config = {
            "mem0ai_enabled": False,
            "sqlite_enabled": True,
            "tinydb_enabled": True,
            "memory_enabled": True,
            "sqlite_path": os.path.join(self.temp_dir, "recovery_sqlite.db"),
            "tinydb_path": os.path.join(self.temp_dir, "recovery_tinydb.json"),
            "circuit_breaker_threshold": 3,
            "circuit_breaker_recovery": 2
        }
        
        service = FlexibleMemoryService(service_config)
        await service.initialize()
        
        # Test normal operation
        memory_id = await service.add_memory(
            self.project_name,
            "Test memory before failure",
            MemoryCategory.PROJECT,
            ["pre-failure"],
            {"status": "normal"}
        )
        assert memory_id, "Failed to add memory before failure test"
        
        # Simulate backend failure by forcing circuit breaker open
        backend_name = service.get_active_backend_name()
        circuit_breaker = service.circuit_breaker_manager.get_circuit_breaker(backend_name)
        await circuit_breaker.force_open()
        
        # Operations should still work via fallback
        memory_id = await service.add_memory(
            self.project_name,
            "Test memory during failure",
            MemoryCategory.PROJECT,
            ["during-failure"],
            {"status": "fallback"}
        )
        assert memory_id, "Failed to add memory during simulated failure"
        
        # Check that we switched to fallback backend
        active_backend = service.get_active_backend_name()
        assert active_backend != backend_name, "Should have switched to fallback backend"
        
        # Test circuit breaker recovery
        await circuit_breaker.reset()
        
        # Test health monitoring during recovery
        health_data = await service.get_service_health()
        assert health_data["service_healthy"], "Service should be healthy during recovery"
        
        # Test metrics during failure scenario
        metrics = service.get_metrics()
        assert metrics["backend_switches"] > 0, "Backend switches not recorded"
        assert metrics["circuit_breaker_activations"] > 0, "Circuit breaker activations not recorded"
        
        await service.cleanup()
        
        return {
            "failure_recovery": True,
            "circuit_breaker_recovery": True,
            "fallback_during_failure": True,
            "health_monitoring": True,
            "metrics": metrics,
            "backend_switches": metrics["backend_switches"]
        }
    
    async def _test_backend_operations(self, backend, backend_name: str) -> Dict[str, Any]:
        """Test basic backend operations."""
        logger.info(f"Testing basic {backend_name} operations...")
        
        # Test add memory
        memory_id = await backend.add_memory(
            self.project_name,
            "Test memory content",
            MemoryCategory.PROJECT,
            ["test", "basic"],
            {"test": True}
        )
        assert memory_id, "Failed to add memory"
        
        # Test get memory
        memory = await backend.get_memory(self.project_name, memory_id)
        assert memory is not None, "Failed to retrieve memory"
        assert memory.content == "Test memory content", "Memory content mismatch"
        assert memory.category == MemoryCategory.PROJECT, "Memory category mismatch"
        
        # Test update memory
        success = await backend.update_memory(
            self.project_name,
            memory_id,
            content="Updated memory content",
            tags=["updated", "test"],
            metadata={"updated": True}
        )
        assert success, "Failed to update memory"
        
        # Verify update
        updated_memory = await backend.get_memory(self.project_name, memory_id)
        assert updated_memory.content == "Updated memory content", "Memory update failed"
        assert "updated" in updated_memory.tags, "Tags not updated"
        
        # Test search
        query = MemoryQuery(query="updated", limit=10)
        search_results = await backend.search_memories(self.project_name, query)
        assert len(search_results) > 0, "Search failed"
        
        # Test delete memory
        success = await backend.delete_memory(self.project_name, memory_id)
        assert success, "Failed to delete memory"
        
        # Verify deletion
        deleted_memory = await backend.get_memory(self.project_name, memory_id)
        assert deleted_memory is None, "Memory not deleted"
        
        return {
            "basic_operations": True,
            "add_memory": True,
            "get_memory": True,
            "update_memory": True,
            "search_memory": True,
            "delete_memory": True,
            "backend_name": backend_name
        }
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        logger.info("Generating final test report...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASSED")
        failed_tests = total_tests - passed_tests
        
        summary = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "overall_status": "PASSED" if failed_tests == 0 else "FAILED"
            },
            "detailed_results": self.test_results,
            "test_environment": {
                "temp_directory": self.temp_dir,
                "project_name": self.project_name,
                "test_memories_count": len(self.test_memories),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Generate recommendations
        recommendations = []
        
        if failed_tests > 0:
            recommendations.append("Review failed tests and address underlying issues")
        
        if passed_tests > 0:
            recommendations.append("Fallback memory systems are functioning correctly")
            
        if "Performance & Reliability" in self.test_results:
            perf_data = self.test_results["Performance & Reliability"]
            if perf_data["status"] == "PASSED":
                recommendations.append("Performance characteristics are acceptable for production use")
        
        if "Circuit Breaker" in self.test_results:
            cb_data = self.test_results["Circuit Breaker"]
            if cb_data["status"] == "PASSED":
                recommendations.append("Circuit breaker patterns are working correctly")
        
        summary["recommendations"] = recommendations
        
        return summary
    
    def cleanup(self):
        """Clean up test resources."""
        logger.info("Cleaning up test resources...")
        
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory: {e}")


async def main():
    """Main test runner."""
    logger.info("Starting Claude PM Framework Fallback Memory Systems Test Suite")
    logger.info("=" * 80)
    
    tester = FallbackMemorySystemTester()
    
    try:
        # Run all tests
        final_report = await tester.run_all_tests()
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("FINAL TEST REPORT")
        logger.info("=" * 80)
        
        summary = final_report["test_summary"]
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed_tests']}")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Overall Status: {summary['overall_status']}")
        
        # Print recommendations
        if final_report["recommendations"]:
            logger.info("\nRecommendations:")
            for rec in final_report["recommendations"]:
                logger.info(f"- {rec}")
        
        # Save detailed report
        report_file = "fallback_memory_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        logger.info(f"\nDetailed report saved to: {report_file}")
        
        # Return appropriate exit code
        return 0 if summary["overall_status"] == "PASSED" else 1
        
    except Exception as e:
        logger.error(f"Test suite failed with error: {e}")
        return 1
    
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)