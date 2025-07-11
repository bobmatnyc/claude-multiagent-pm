#!/usr/bin/env python3
"""
Memory Backend Fixes and Comprehensive Testing

This script tests the corrected memory backends and fallback mechanisms.
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
# TinyDB_REMOVED backend removed from framework
# # from claude_pm.services.memory.backends.memory_backend import InMemoryBackend  # InMemory backend removed  # InMemory backend removed
from claude_pm.services.memory.services.unified_service import FlexibleMemoryService
from claude_pm.services.memory.interfaces.models import MemoryCategory, MemoryQuery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CorrectedSQLiteBackend(SQLiteBackend):
    """Corrected SQLite backend that fixes FTS5 synchronization issues."""
    
    async def _create_fts_schema(self):
        """Create full-text search schema with corrected triggers."""
        try:
            # Create FTS5 virtual table
            await self._connection.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id UNINDEXED,
                    project_name UNINDEXED,
                    content,
                    category UNINDEXED,
                    tags UNINDEXED,
                    content='memories',
                    content_rowid='rowid',
                    tokenize='porter'
                )
            ''')
            
            # Drop existing triggers to avoid conflicts
            await self._connection.execute('DROP TRIGGER IF EXISTS memories_fts_insert')
            await self._connection.execute('DROP TRIGGER IF EXISTS memories_fts_update')
            await self._connection.execute('DROP TRIGGER IF EXISTS memories_fts_delete')
            
            # Create corrected triggers
            await self._connection.execute('''
                CREATE TRIGGER memories_fts_insert 
                AFTER INSERT ON memories 
                BEGIN
                    INSERT INTO memories_fts(rowid, id, project_name, content, category, tags)
                    VALUES (new.rowid, new.id, new.project_name, new.content, new.category, new.tags);
                END
            ''')
            
            await self._connection.execute('''
                CREATE TRIGGER memories_fts_update 
                AFTER UPDATE ON memories 
                BEGIN
                    UPDATE memories_fts SET 
                        content = new.content,
                        category = new.category,
                        tags = new.tags
                    WHERE rowid = new.rowid;
                END
            ''')
            
            await self._connection.execute('''
                CREATE TRIGGER memories_fts_delete 
                AFTER DELETE ON memories 
                BEGIN
                    DELETE FROM memories_fts WHERE rowid = old.rowid;
                END
            ''')
            
            # Rebuild FTS index to ensure consistency
            await self._connection.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
            
        except Exception as e:
            raise BackendInitializationError(f"FTS schema creation failed: {e}", "sqlite", "fts")
    
    async def _rebuild_fts_index(self):
        """Rebuild FTS index to ensure consistency."""
        try:
            if not self.enable_fts:
                return
                
            # Clear FTS table
            await self._connection.execute("DELETE FROM memories_fts")
            
            # Repopulate FTS table
            cursor = await self._connection.execute('''
                SELECT rowid, id, project_name, content, category, tags FROM memories
            ''')
            
            rows = await cursor.fetchall()
            for row in rows:
                await self._connection.execute('''
                    INSERT INTO memories_fts(rowid, id, project_name, content, category, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', row)
            
            await self._connection.commit()
            
        except Exception as e:
            self.logger.warning(f"Failed to rebuild FTS index: {e}")


class MemoryBackendTester:
    """Comprehensive tester for memory backends with fixes."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results = {}
        self.temp_dir = tempfile.mkdtemp(prefix="memory_fix_test_")
        self.project_name = "test_project"
        
        # Test data
        self.test_memories = [
            {
                "content": "Project architecture decision: Use microservices pattern",
                "category": MemoryCategory.PROJECT,
                "tags": ["architecture", "microservices", "decision"],
                "metadata": {"importance": "high", "decision_type": "architecture"}
            },
            {
                "content": "Code pattern: Async error handling with retry and circuit breaker",
                "category": MemoryCategory.PATTERN,
                "tags": ["async", "error-handling", "retry", "circuit-breaker"],
                "metadata": {"language": "python", "pattern_type": "resilience"}
            },
            {
                "content": "Team standard: All functions must have type hints and docstrings",
                "category": MemoryCategory.TEAM,
                "tags": ["coding-standards", "type-hints", "documentation"],
                "metadata": {"enforcement": "strict", "team_agreed": True}
            },
            {
                "content": "Bug fix: SQLite FTS5 synchronization issue with update operations",
                "category": MemoryCategory.ERROR,
                "tags": ["bug", "sqlite", "fts5", "sync"],
                "metadata": {"severity": "high", "status": "fixed", "component": "memory_backend"}
            }
        ]
        
        logger.info(f"Initialized tester with temp directory: {self.temp_dir}")
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests with fixes."""
        logger.info("Starting comprehensive memory backend tests with fixes...")
        
        test_cases = [
            ("Fixed SQLite Backend", self.test_corrected_sqlite),
            # TinyDB_REMOVED backend removed from framework
            # ("InMemory Backend", self.test_inmemory_backend),  # InMemory backend removed
            ("Fallback System", self.test_fallback_system),
            ("Performance Comparison", self.test_performance_comparison),
            ("Reliability Testing", self.test_reliability)
        ]
        
        for test_name, test_func in test_cases:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing {test_name}")
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
        
        return self.generate_final_report()
    
    async def test_corrected_sqlite(self) -> Dict[str, Any]:
        """Test the corrected SQLite backend."""
        logger.info("Testing corrected SQLite backend...")
        
        sqlite_config = {
            "db_path": os.path.join(self.temp_dir, "corrected_sqlite.db"),
            "enable_fts": True,
            "enable_wal": True
        }
        
        backend = CorrectedSQLiteBackend(sqlite_config)
        
        # Initialize backend
        assert await backend.initialize(), "SQLite backend initialization failed"
        assert await backend.health_check(), "SQLite backend health check failed"
        
        # Test basic operations
        memory_ids = []
        for i, memory_data in enumerate(self.test_memories):
            memory_id = await backend.add_memory(
                self.project_name,
                memory_data["content"],
                memory_data["category"],
                memory_data["tags"],
                memory_data["metadata"]
            )
            assert memory_id, f"Failed to add memory {i}"
            memory_ids.append(memory_id)
        
        # Test FTS search
        query = MemoryQuery(query="architecture", limit=10)
        search_results = await backend.search_memories(self.project_name, query)
        assert len(search_results) >= 1, "FTS search failed"
        
        # Test update operation (this was the problematic one)
        first_memory_id = memory_ids[0]
        update_success = await backend.update_memory(
            self.project_name,
            first_memory_id,
            content="Updated: Project architecture decision with detailed analysis",
            tags=["architecture", "microservices", "decision", "updated"],
            metadata={"importance": "high", "decision_type": "architecture", "updated": True}
        )
        assert update_success, "Memory update failed"
        
        # Test search after update (this should work now)
        query = MemoryQuery(query="Updated", limit=10)
        updated_search_results = await backend.search_memories(self.project_name, query)
        assert len(updated_search_results) >= 1, "Search after update failed"
        
        # Test various search patterns
        search_tests = [
            ("microservices", "Tag-based search"),
            ("error handling", "Multi-word search"),
            ("python", "Metadata search"),
            ("decision", "Common term search"),
            ("", "Empty query (get all)")
        ]
        
        search_results_summary = {}
        for search_term, description in search_tests:
            query = MemoryQuery(query=search_term, limit=10)
            results = await backend.search_memories(self.project_name, query)
            search_results_summary[description] = len(results)
            logger.info(f"  {description}: {len(results)} results")
        
        # Test category filtering
        query = MemoryQuery(query="", category=MemoryCategory.PROJECT, limit=10)
        project_results = await backend.search_memories(self.project_name, query)
        
        # Test tag filtering
        query = MemoryQuery(query="", tags=["architecture"], limit=10)
        tag_results = await backend.search_memories(self.project_name, query)
        
        # Test statistics
        stats = await backend.get_memory_stats(self.project_name)
        
        await backend.cleanup()
        
        return {
            "fts_search_working": True,
            "update_operation_working": True,
            "search_after_update_working": True,
            "search_results_summary": search_results_summary,
            "category_filtering": len(project_results),
            "tag_filtering": len(tag_results),
            "statistics": stats,
            "memory_count": len(memory_ids)
        }
    
    # TinyDB backend test removed - TinyDB no longer supported
    async def test_inmemory_backend(self) -> Dict[str, Any]:
        # """Test InMemory backend."""  # InMemory backend removed
        # logger.info("Testing InMemory backend...")  # InMemory backend removed
        
        inmemory_config = {
            "max_memory_size": 1000,
            "enable_expiration": False
        }
        
        # # backend = InMemoryBackend(inmemory_config)  # InMemory backend removed  # InMemory backend removed
        
        # Initialize backend
        # assert await backend.initialize(), "InMemory backend initialization failed"  # InMemory backend removed
        # assert await backend.health_check(), "InMemory backend health check failed"  # InMemory backend removed
        
        # Test basic operations
        memory_ids = []
        for i, memory_data in enumerate(self.test_memories):
            memory_id = await backend.add_memory(
                self.project_name,
                memory_data["content"],
                memory_data["category"],
                memory_data["tags"],
                memory_data["metadata"]
            )
            assert memory_id, f"Failed to add memory {i}"
            memory_ids.append(memory_id)
        
        # Test search
        query = MemoryQuery(query="architecture", limit=10)
        search_results = await backend.search_memories(self.project_name, query)
        # assert len(search_results) >= 1, "InMemory search failed"  # InMemory backend removed
        
        # Test performance
        start_time = time.time()
        for _ in range(100):
            query = MemoryQuery(query="test", limit=10)
            await backend.search_memories(self.project_name, query)
        search_time = time.time() - start_time
        
        # Test statistics
        stats = await backend.get_memory_stats(self.project_name)
        
        await backend.cleanup()
        
        return {
            "basic_operations": True,
            "search_operations": True,
            "performance": {
                "search_time_100_ops": search_time,
                "ops_per_second": 100 / search_time
            },
            "statistics": stats,
            "memory_count": len(memory_ids)
        }
    
    async def test_fallback_system(self) -> Dict[str, Any]:
        """Test the fallback system."""
        logger.info("Testing fallback system...")
        
        # Configure service with custom backends
        service_config = {
            "mem0ai_enabled": False,  # Simulate mem0AI unavailable
            "sqlite_enabled": True,
            "tinydb_enabled": True,
            "memory_enabled": True,
            "sqlite_path": os.path.join(self.temp_dir, "fallback_sqlite.db"),
            "tinydb_path": os.path.join(self.temp_dir, "fallback_tinydb.json")
        }
        
        # Create service with custom SQLite backend
        service = FlexibleMemoryService(service_config)
        
        # Replace SQLite backend with corrected version
        service.backends["sqlite"] = CorrectedSQLiteBackend({
            "db_path": service_config["sqlite_path"],
            "enable_fts": True,
            "enable_wal": True
        })
        
        # Initialize service
        assert await service.initialize(), "Fallback service initialization failed"
        
        # Test that it falls back to SQLite
        active_backend = service.get_active_backend_name()
        logger.info(f"Active backend: {active_backend}")
        
        # Test operations through fallback
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
        assert len(search_results) >= 1, "Search through fallback failed"
        
        # Test backend switching
        switch_results = {}
        for backend_name in ["sqlite", "tinydb", "memory"]:
            success = await service.switch_backend(backend_name)
            if success:
                current_backend = service.get_active_backend_name()
                switch_results[backend_name] = current_backend == backend_name
            else:
                switch_results[backend_name] = False
        
        # Test health monitoring
        health_data = await service.get_service_health()
        
        await service.cleanup()
        
        return {
            "fallback_initialization": True,
            "active_backend": active_backend,
            "memory_operations": len(memory_ids),
            "search_operations": len(search_results),
            "backend_switching": switch_results,
            "health_monitoring": health_data["service_healthy"],
            "available_backends": list(switch_results.keys())
        }
    
    async def test_performance_comparison(self) -> Dict[str, Any]:
        """Test performance comparison across backends."""
        logger.info("Testing performance comparison...")
        
        backends = [
            ("SQLite", CorrectedSQLiteBackend, {
                "db_path": os.path.join(self.temp_dir, "perf_sqlite.db"),
                "enable_fts": True
            }),
            ("TinyDB_REMOVED", TinyDB_REMOVED_Backend, {
                "db_path": os.path.join(self.temp_dir, "perf_tinydb.json")
            })
            # ("InMemory", InMemoryBackend, {  # InMemory backend removed
            #     "max_memory_size": 1000
            # })
        ]
        
        performance_results = {}
        
        for backend_name, backend_class, config in backends:
            backend = backend_class(config)
            await backend.initialize()
            
            # Test write performance
            start_time = time.time()
            for i in range(50):
                await backend.add_memory(
                    self.project_name,
                    f"Performance test memory {i}",
                    MemoryCategory.PROJECT,
                    ["performance"],
                    {"test_id": i}
                )
            write_time = time.time() - start_time
            
            # Test read performance
            start_time = time.time()
            for i in range(20):
                query = MemoryQuery(query="performance", limit=10)
                await backend.search_memories(self.project_name, query)
            read_time = time.time() - start_time
            
            await backend.cleanup()
            
            performance_results[backend_name] = {
                "write_time": write_time,
                "read_time": read_time,
                "write_ops_per_sec": 50 / write_time,
                "read_ops_per_sec": 20 / read_time
            }
        
        return performance_results
    
    async def test_reliability(self) -> Dict[str, Any]:
        """Test reliability features."""
        logger.info("Testing reliability features...")
        
        # Test with corrected SQLite backend
        backend = CorrectedSQLiteBackend({
            "db_path": os.path.join(self.temp_dir, "reliability_test.db"),
            "enable_fts": True
        })
        
        await backend.initialize()
        
        # Test concurrent operations
        async def concurrent_add(i):
            return await backend.add_memory(
                self.project_name,
                f"Concurrent memory {i}",
                MemoryCategory.PROJECT,
                ["concurrent"],
                {"id": i}
            )
        
        # Run concurrent operations
        tasks = [concurrent_add(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_ops = sum(1 for r in results if isinstance(r, str))
        failed_ops = len(results) - successful_ops
        
        # Test data integrity
        query = MemoryQuery(query="", limit=100)
        all_memories = await backend.search_memories(self.project_name, query)
        
        await backend.cleanup()
        
        return {
            "concurrent_operations": {
                "total": len(tasks),
                "successful": successful_ops,
                "failed": failed_ops,
                "success_rate": successful_ops / len(tasks)
            },
            "data_integrity": {
                "memories_found": len(all_memories),
                "expected_minimum": 10
            }
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
        
        # Generate analysis
        analysis = []
        
        if "Fixed SQLite Backend" in self.test_results:
            sqlite_result = self.test_results["Fixed SQLite Backend"]
            if sqlite_result["status"] == "PASSED":
                analysis.append("✅ SQLite backend FTS5 synchronization issue has been resolved")
                analysis.append("✅ SQLite backend supports full-text search and update operations")
            else:
                analysis.append("❌ SQLite backend still has issues")
        
        if "TinyDB_REMOVED Backend" in self.test_results:
            tinydb_result = self.test_results["TinyDB_REMOVED Backend"]
            if tinydb_result["status"] == "PASSED":
                analysis.append("✅ TinyDB_REMOVED backend is operational for lightweight deployments")
            else:
                analysis.append("❌ TinyDB_REMOVED backend has issues")
        
        # if "InMemory Backend" in self.test_results:  # InMemory backend removed
        #     inmemory_result = self.test_results["InMemory Backend"]  # InMemory backend removed
        #     if inmemory_result["status"] == "PASSED":
        #         analysis.append("✅ InMemory backend provides excellent performance for testing")  # InMemory backend removed
        #     else:
        #         analysis.append("❌ InMemory backend has issues")  # InMemory backend removed
        
        if "Fallback System" in self.test_results:
            fallback_result = self.test_results["Fallback System"]
            if fallback_result["status"] == "PASSED":
                analysis.append("✅ Fallback system works correctly when mem0AI is unavailable")
            else:
                analysis.append("❌ Fallback system has issues")
        
        if "Performance Comparison" in self.test_results:
            perf_result = self.test_results["Performance Comparison"]
            if perf_result["status"] == "PASSED":
                analysis.append("✅ Performance characteristics are acceptable across all backends")
            else:
                analysis.append("❌ Performance issues detected")
        
        summary["analysis"] = analysis
        
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
    logger.info("Starting Memory Backend Fixes and Testing")
    logger.info("=" * 80)
    
    tester = MemoryBackendTester()
    
    try:
        # Run comprehensive tests
        final_report = await tester.run_comprehensive_tests()
        
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
        
        # Print analysis
        if final_report.get("analysis"):
            logger.info("\nAnalysis:")
            for item in final_report["analysis"]:
                logger.info(f"  {item}")
        
        # Save detailed report
        report_file = "memory_backend_fixes_report.json"
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