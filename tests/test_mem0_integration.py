#!/usr/bin/env python3
"""
Comprehensive mem0 Integration Testing Script
============================================

This script performs comprehensive testing of the mem0 service integration
to validate the OpenAI API key resolution and service connectivity.

Test Categories:
1. mem0 Client Initialization
2. Service Connectivity 
3. Basic Memory Operations
4. Framework Integration
5. Performance Testing
6. Error Handling
"""

import os
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add the project root to the Python path
import sys
sys.path.insert(0, '/Users/masa/Projects/claude-multiagent-pm')

from claude_pm.integrations.mem0ai_integration import Mem0AIIntegration, create_mem0ai_integration
from claude_pm.integrations.security import create_security_config
from claude_pm.core.logging_config import get_logger

logger = get_logger(__name__)

class Mem0IntegrationTester:
    """Comprehensive mem0 integration testing suite."""
    
    def __init__(self):
        self.results = {
            "test_suite": "mem0 Integration Testing",
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
        self.mem0_integration = None
        
    def log_test_result(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log a test result."""
        test_result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.results["tests"].append(test_result)
        self.results["summary"]["total_tests"] += 1
        
        if status == "PASSED":
            self.results["summary"]["passed"] += 1
            logger.info(f"✅ {test_name}: PASSED")
        elif status == "FAILED":
            self.results["summary"]["failed"] += 1
            logger.error(f"❌ {test_name}: FAILED - {details}")
        elif status == "SKIPPED":
            self.results["summary"]["skipped"] += 1
            logger.warning(f"⏭️ {test_name}: SKIPPED - {details}")
    
    async def test_environment_configuration(self):
        """Test 1: Environment Configuration Validation"""
        try:
            # Check OpenAI API key
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                self.log_test_result("environment_config", "FAILED", {
                    "error": "OPENAI_API_KEY environment variable not set"
                })
                return False
            
            # Check mem0AI API key
            mem0_key = os.getenv("MEM0AI_API_KEY")
            if not mem0_key:
                self.log_test_result("environment_config", "FAILED", {
                    "error": "MEM0AI_API_KEY environment variable not set"
                })
                return False
            
            # Check mem0AI host and port
            mem0_host = os.getenv("MEM0AI_HOST", "localhost")
            mem0_port = int(os.getenv("MEM0AI_PORT", "8002"))
            
            self.log_test_result("environment_config", "PASSED", {
                "openai_key_configured": bool(openai_key),
                "mem0_key_configured": bool(mem0_key),
                "mem0_host": mem0_host,
                "mem0_port": mem0_port
            })
            return True
            
        except Exception as e:
            self.log_test_result("environment_config", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def test_security_configuration(self):
        """Test 2: Security Configuration Validation"""
        try:
            # Create security configuration
            security_config = create_security_config()
            
            # Validate security configuration
            from claude_pm.integrations.security import validate_security_configuration
            validation = validate_security_configuration(security_config)
            
            if validation["valid"]:
                self.log_test_result("security_config", "PASSED", {
                    "api_key_present": bool(security_config.api_key),
                    "validation_warnings": validation["warnings"],
                    "validation_recommendations": validation["recommendations"]
                })
                return True
            else:
                self.log_test_result("security_config", "FAILED", {
                    "validation_errors": validation["errors"],
                    "validation_warnings": validation["warnings"]
                })
                return False
                
        except Exception as e:
            self.log_test_result("security_config", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def test_mem0_client_initialization(self):
        """Test 3: mem0 Client Initialization"""
        try:
            # Create mem0 integration
            self.mem0_integration = create_mem0ai_integration()
            
            # Check initialization
            if self.mem0_integration:
                self.log_test_result("mem0_client_init", "PASSED", {
                    "client_created": True,
                    "config_host": self.mem0_integration.config.host,
                    "config_port": self.mem0_integration.config.port,
                    "api_key_configured": bool(self.mem0_integration.config.api_key)
                })
                return True
            else:
                self.log_test_result("mem0_client_init", "FAILED", {
                    "error": "Failed to create mem0 integration client"
                })
                return False
                
        except Exception as e:
            self.log_test_result("mem0_client_init", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def test_mem0_service_connectivity(self):
        """Test 4: mem0 Service Connectivity"""
        if not self.mem0_integration:
            self.log_test_result("mem0_service_connectivity", "SKIPPED", {
                "reason": "mem0 client not initialized"
            })
            return False
        
        try:
            # Test connection
            connection_success = await self.mem0_integration.connect()
            
            if connection_success:
                # Check connection status
                is_connected = self.mem0_integration.is_connected()
                is_authenticated = self.mem0_integration.is_authenticated()
                security_status = self.mem0_integration.get_security_status()
                
                self.log_test_result("mem0_service_connectivity", "PASSED", {
                    "connected": is_connected,
                    "authenticated": is_authenticated,
                    "security_status": security_status
                })
                return True
            else:
                self.log_test_result("mem0_service_connectivity", "FAILED", {
                    "error": "Failed to connect to mem0 service"
                })
                return False
                
        except Exception as e:
            self.log_test_result("mem0_service_connectivity", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def test_basic_memory_operations(self):
        """Test 5: Basic Memory Operations"""
        if not self.mem0_integration or not self.mem0_integration.is_connected():
            self.log_test_result("basic_memory_operations", "SKIPPED", {
                "reason": "mem0 service not connected"
            })
            return False
        
        try:
            test_project = "test_project_integration"
            
            # Test 1: Create project space
            space_created = await self.mem0_integration.create_project_space(
                test_project, 
                "Test project space for integration testing"
            )
            
            if not space_created:
                self.log_test_result("basic_memory_operations", "FAILED", {
                    "error": "Failed to create project space"
                })
                return False
            
            # Test 2: Store a memory
            memory_id = await self.mem0_integration.store_memory(
                test_project,
                "Test memory content for integration testing",
                "project_decision",
                ["test", "integration", "qa"],
                {"test_type": "integration", "test_run": datetime.now().isoformat()}
            )
            
            if not memory_id:
                self.log_test_result("basic_memory_operations", "FAILED", {
                    "error": "Failed to store memory"
                })
                return False
            
            # Test 3: Retrieve memories
            retrieved_memories = await self.mem0_integration.retrieve_memories(
                test_project,
                "integration testing",
                limit=5
            )
            
            if not retrieved_memories:
                self.log_test_result("basic_memory_operations", "FAILED", {
                    "error": "Failed to retrieve memories"
                })
                return False
            
            # Test 4: Get memory by ID
            memory_detail = await self.mem0_integration.get_memory_by_id(memory_id)
            
            if not memory_detail:
                self.log_test_result("basic_memory_operations", "FAILED", {
                    "error": "Failed to get memory by ID"
                })
                return False
            
            # Test 5: Update memory
            update_success = await self.mem0_integration.update_memory(
                memory_id,
                tags=["test", "integration", "qa", "updated"]
            )
            
            if not update_success:
                self.log_test_result("basic_memory_operations", "FAILED", {
                    "error": "Failed to update memory"
                })
                return False
            
            # Test 6: Delete memory (cleanup)
            delete_success = await self.mem0_integration.delete_memory(memory_id)
            
            self.log_test_result("basic_memory_operations", "PASSED", {
                "space_created": space_created,
                "memory_stored": bool(memory_id),
                "memories_retrieved": len(retrieved_memories),
                "memory_detail_retrieved": bool(memory_detail),
                "memory_updated": update_success,
                "memory_deleted": delete_success
            })
            return True
            
        except Exception as e:
            self.log_test_result("basic_memory_operations", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def test_memory_persistence(self):
        """Test 6: Memory Persistence and Retrieval"""
        if not self.mem0_integration or not self.mem0_integration.is_connected():
            self.log_test_result("memory_persistence", "SKIPPED", {
                "reason": "mem0 service not connected"
            })
            return False
        
        try:
            test_project = "test_persistence_project"
            
            # Create test memories
            test_memories = [
                {
                    "content": "Test decision 1: Use microservices architecture",
                    "category": "project_decision",
                    "tags": ["architecture", "microservices", "persistence_test"]
                },
                {
                    "content": "Test pattern 1: Repository pattern for data access",
                    "category": "code_pattern",
                    "tags": ["pattern", "repository", "persistence_test"]
                },
                {
                    "content": "Test solution 1: Fixed memory leak in service",
                    "category": "error_solution",
                    "tags": ["bug", "memory_leak", "persistence_test"]
                }
            ]
            
            # Store memories
            stored_ids = []
            for memory in test_memories:
                memory_id = await self.mem0_integration.store_memory(
                    test_project,
                    memory["content"],
                    memory["category"],
                    memory["tags"]
                )
                if memory_id:
                    stored_ids.append(memory_id)
            
            # Wait a moment to ensure persistence
            await asyncio.sleep(1)
            
            # Retrieve memories by category
            decision_memories = await self.mem0_integration.retrieve_memories(
                test_project, "architecture", category="project_decision"
            )
            
            pattern_memories = await self.mem0_integration.retrieve_memories(
                test_project, "repository", category="code_pattern"
            )
            
            solution_memories = await self.mem0_integration.retrieve_memories(
                test_project, "memory leak", category="error_solution"
            )
            
            # Test high-level methods
            similar_decisions = await self.mem0_integration.find_similar_decisions(
                test_project, "microservices architecture"
            )
            
            applicable_patterns = await self.mem0_integration.find_applicable_patterns(
                test_project, "data access"
            )
            
            error_solutions = await self.mem0_integration.find_error_solutions(
                test_project, "memory leak"
            )
            
            # Get project statistics
            stats = await self.mem0_integration.get_project_statistics(test_project)
            
            # Cleanup
            for memory_id in stored_ids:
                await self.mem0_integration.delete_memory(memory_id)
            
            await self.mem0_integration.delete_project_space(test_project)
            
            self.log_test_result("memory_persistence", "PASSED", {
                "memories_stored": len(stored_ids),
                "decision_memories_found": len(decision_memories),
                "pattern_memories_found": len(pattern_memories),
                "solution_memories_found": len(solution_memories),
                "similar_decisions_found": len(similar_decisions),
                "applicable_patterns_found": len(applicable_patterns),
                "error_solutions_found": len(error_solutions),
                "project_statistics": stats
            })
            return True
            
        except Exception as e:
            self.log_test_result("memory_persistence", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def test_framework_integration(self):
        """Test 7: Framework Integration"""
        try:
            # Test importing framework memory service
            from claude_pm.services.memory_service import MemoryService
            
            # Create memory service instance
            memory_service = MemoryService()
            
            # Test service initialization
            if hasattr(memory_service, 'mem0_integration'):
                self.log_test_result("framework_integration", "PASSED", {
                    "memory_service_created": True,
                    "mem0_integration_available": True
                })
                return True
            else:
                self.log_test_result("framework_integration", "FAILED", {
                    "error": "Memory service does not have mem0 integration"
                })
                return False
                
        except ImportError as e:
            self.log_test_result("framework_integration", "FAILED", {
                "error": f"Import error: {str(e)}"
            })
            return False
        except Exception as e:
            self.log_test_result("framework_integration", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def test_performance_benchmarks(self):
        """Test 8: Performance Benchmarks"""
        if not self.mem0_integration or not self.mem0_integration.is_connected():
            self.log_test_result("performance_benchmarks", "SKIPPED", {
                "reason": "mem0 service not connected"
            })
            return False
        
        try:
            test_project = "test_performance_project"
            
            # Benchmark memory storage
            start_time = time.time()
            memory_ids = []
            
            for i in range(10):
                memory_id = await self.mem0_integration.store_memory(
                    test_project,
                    f"Performance test memory {i}",
                    "project_decision",
                    ["performance", "test", f"batch_{i}"]
                )
                if memory_id:
                    memory_ids.append(memory_id)
            
            storage_time = time.time() - start_time
            
            # Benchmark memory retrieval
            start_time = time.time()
            retrieved_memories = await self.mem0_integration.retrieve_memories(
                test_project, "performance test", limit=50
            )
            retrieval_time = time.time() - start_time
            
            # Benchmark concurrent operations
            start_time = time.time()
            tasks = []
            for i in range(5):
                task = self.mem0_integration.retrieve_memories(
                    test_project, f"test {i}", limit=10
                )
                tasks.append(task)
            
            concurrent_results = await asyncio.gather(*tasks)
            concurrent_time = time.time() - start_time
            
            # Cleanup
            for memory_id in memory_ids:
                await self.mem0_integration.delete_memory(memory_id)
            await self.mem0_integration.delete_project_space(test_project)
            
            self.log_test_result("performance_benchmarks", "PASSED", {
                "storage_time_10_memories": round(storage_time, 3),
                "retrieval_time": round(retrieval_time, 3),
                "concurrent_operations_time": round(concurrent_time, 3),
                "memories_stored": len(memory_ids),
                "memories_retrieved": len(retrieved_memories),
                "concurrent_results": len(concurrent_results)
            })
            return True
            
        except Exception as e:
            self.log_test_result("performance_benchmarks", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def test_error_handling(self):
        """Test 9: Error Handling and Graceful Degradation"""
        try:
            # Test with invalid configuration
            invalid_integration = create_mem0ai_integration(
                host="invalid_host",
                port=9999,
                timeout=1
            )
            
            # Test connection failure handling
            connection_result = await invalid_integration.connect()
            
            if not connection_result:
                # Expected failure - good error handling
                self.log_test_result("error_handling", "PASSED", {
                    "connection_failure_handled": True,
                    "graceful_degradation": True
                })
                return True
            else:
                self.log_test_result("error_handling", "FAILED", {
                    "error": "Connection should have failed but succeeded"
                })
                return False
                
        except Exception as e:
            # Exception handling test
            self.log_test_result("error_handling", "PASSED", {
                "exception_handled": True,
                "exception_type": type(e).__name__,
                "exception_message": str(e)
            })
            return True
    
    async def test_health_checks(self):
        """Test 10: Health Checks and Service Monitoring"""
        try:
            # Test health check system
            from claude_pm.services.health_monitor import HealthMonitor
            
            health_monitor = HealthMonitor()
            
            # Get health status
            health_status = await health_monitor.get_comprehensive_health()
            
            # Check if memory system is included
            memory_health = health_status.get("memory_system", {})
            
            self.log_test_result("health_checks", "PASSED", {
                "health_monitor_available": True,
                "memory_system_monitored": bool(memory_health),
                "overall_health": health_status.get("overall_status", "unknown")
            })
            return True
            
        except Exception as e:
            self.log_test_result("health_checks", "FAILED", {
                "error": str(e)
            })
            return False
    
    async def cleanup(self):
        """Cleanup resources after testing."""
        if self.mem0_integration:
            try:
                await self.mem0_integration.disconnect()
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
    
    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting mem0 Integration Testing Suite...")
        
        # Test sequence
        test_methods = [
            self.test_environment_configuration,
            self.test_security_configuration,
            self.test_mem0_client_initialization,
            self.test_mem0_service_connectivity,
            self.test_basic_memory_operations,
            self.test_memory_persistence,
            self.test_framework_integration,
            self.test_performance_benchmarks,
            self.test_error_handling,
            self.test_health_checks
        ]
        
        # Run tests
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed: {e}")
                self.log_test_result(test_method.__name__, "FAILED", {
                    "error": f"Test execution failed: {str(e)}"
                })
        
        # Cleanup
        await self.cleanup()
        
        # Finalize results
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration"] = (
            datetime.fromisoformat(self.results["end_time"]) - 
            datetime.fromisoformat(self.results["start_time"])
        ).total_seconds()
        
        return self.results
    
    def generate_report(self):
        """Generate comprehensive test report."""
        report = {
            "title": "mem0 Integration Testing Report",
            "date": datetime.now().isoformat(),
            "summary": self.results["summary"],
            "success_rate": (
                self.results["summary"]["passed"] / 
                max(self.results["summary"]["total_tests"], 1)
            ) * 100,
            "recommendations": []
        }
        
        # Add recommendations based on results
        if self.results["summary"]["failed"] > 0:
            report["recommendations"].append("Address failed tests before production deployment")
        
        if self.results["summary"]["passed"] == self.results["summary"]["total_tests"]:
            report["recommendations"].append("All tests passed - system ready for production")
        
        return report


async def main():
    """Main test execution."""
    tester = Mem0IntegrationTester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Generate report
        report = tester.generate_report()
        
        # Save results
        results_file = Path("mem0_integration_test_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        report_file = Path("mem0_integration_test_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("mem0 Integration Testing Summary")
        print("="*60)
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Skipped: {results['summary']['skipped']}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        print(f"Duration: {results['duration']:.2f} seconds")
        print(f"\nDetailed results saved to: {results_file}")
        print(f"Report saved to: {report_file}")
        
        # Return success/failure
        return results['summary']['failed'] == 0
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)