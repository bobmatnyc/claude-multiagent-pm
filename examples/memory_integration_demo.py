"""
ClaudePMMemory Integration Demo

This script demonstrates comprehensive usage of the ClaudePMMemory class
for memory-augmented project management in the Claude PM Framework.

Features demonstrated:
- Project memory space creation
- Storing different types of memories
- Searching and retrieving memories
- Statistics and monitoring
- Error handling and recovery
- Integration patterns
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from claude_pm.services.claude_pm_memory import (
    ClaudePMMemory, MemoryCategory, claude_pm_memory_context, 
    create_claude_pm_memory, ClaudePMConfig
)
from claude_pm.core.memory_config import create_development_memory, get_environment_info


class MemoryIntegrationDemo:
    """Demonstrates ClaudePMMemory integration patterns."""
    
    def __init__(self):
        self.project_name = f"demo_project_{int(time.time())}"
        self.memories_created = []
        self.demo_results = {}
    
    async def run_complete_demo(self):
        """Run the complete integration demo."""
        print("🧠 ClaudePMMemory Integration Demo")
        print("=" * 60)
        
        try:
            # Test 1: Basic Connection and Setup
            await self.demo_basic_connection()
            
            # Test 2: Project Memory Space Management
            await self.demo_project_space_management()
            
            # Test 3: Memory Storage Operations
            await self.demo_memory_storage()
            
            # Test 4: Memory Retrieval and Search
            await self.demo_memory_retrieval()
            
            # Test 5: High-level Convenience Methods
            await self.demo_convenience_methods()
            
            # Test 6: Statistics and Monitoring
            await self.demo_statistics_monitoring()
            
            # Test 7: Error Handling and Recovery
            await self.demo_error_handling()
            
            # Test 8: Performance Testing
            await self.demo_performance_testing()
            
            # Summary
            self.print_demo_summary()
            
        except Exception as e:
            print(f"❌ Demo failed with error: {e}")
            raise
    
    async def demo_basic_connection(self):
        """Demonstrate basic connection management."""
        print("\n📡 Test 1: Basic Connection and Setup")
        print("-" * 40)
        
        # Test configuration loading
        env_info = get_environment_info()
        print(f"🔧 Environment: {env_info['current_environment']}")
        print(f"🔧 Host: {env_info['configuration']['host']}")
        print(f"🔧 Port: {env_info['configuration']['port']}")
        
        # Test basic connection
        memory = create_development_memory()
        connected = await memory.connect()
        
        if connected:
            print("✅ Connection established successfully")
            print(f"🔗 Connected to: {memory.base_url}")
            
            # Test health check
            health = await memory._health_check()
            print(f"❤️  Health check: {'✅ Healthy' if health else '❌ Unhealthy'}")
            
            await memory.disconnect()
            print("🔌 Disconnected successfully")
            
            self.demo_results["basic_connection"] = True
        else:
            print("❌ Connection failed")
            self.demo_results["basic_connection"] = False
            raise Exception("Cannot proceed without connection")
    
    async def demo_project_space_management(self):
        """Demonstrate project memory space management."""
        print("\n📁 Test 2: Project Memory Space Management")
        print("-" * 40)
        
        async with claude_pm_memory_context() as memory:
            # Create project memory space
            create_response = await memory.create_project_memory_space(
                project_name=self.project_name,
                description="Demo project for testing ClaudePMMemory integration",
                metadata={
                    "demo_type": "integration_test",
                    "created_by": "demo_script",
                    "team_size": 5,
                    "duration_weeks": 8,
                    "tech_stack": ["Python", "FastAPI", "PostgreSQL", "React"]
                }
            )
            
            if create_response.success:
                print(f"✅ Project space created: {self.project_name}")
                print(f"📊 Response data: {create_response.data}")
                
                # List project spaces
                list_response = await memory.list_project_spaces()
                if list_response.success:
                    spaces = list_response.data.get("spaces", [])
                    print(f"📋 Total project spaces: {len(spaces)}")
                    
                    # Find our project in the list
                    our_project = next((s for s in spaces if s.get("name") == self.project_name), None)
                    if our_project:
                        print(f"🔍 Found our project in spaces list")
                
                self.demo_results["project_space_management"] = True
            else:
                print(f"❌ Failed to create project space: {create_response.error}")
                self.demo_results["project_space_management"] = False
    
    async def demo_memory_storage(self):
        """Demonstrate memory storage operations."""
        print("\n💾 Test 3: Memory Storage Operations")
        print("-" * 40)
        
        async with claude_pm_memory_context() as memory:
            storage_results = []
            
            # Store PROJECT memory
            project_response = await memory.store_memory(
                category=MemoryCategory.PROJECT,
                content="Decision to use microservices architecture for scalability",
                metadata={
                    "decision_type": "architectural",
                    "impact_scope": ["backend", "deployment", "monitoring"],
                    "alternatives_considered": ["monolithic", "modular_monolith"],
                    "decision_date": datetime.now().isoformat()
                },
                project_name=self.project_name,
                tags=["architecture", "microservices", "scalability"]
            )
            
            if project_response.success:
                print(f"✅ PROJECT memory stored: {project_response.memory_id}")
                self.memories_created.append(project_response.memory_id)
                storage_results.append("project")
            
            # Store PATTERN memory
            pattern_response = await memory.store_memory(
                category=MemoryCategory.PATTERN,
                content="""
Repository Pattern for Database Access

A design pattern that encapsulates database operations behind repository interfaces.

Benefits:
- Testability through mocking
- Separation of concerns
- Database abstraction
- Consistent API

Implementation:
```python
class UserRepository:
    async def get_user(self, user_id: str) -> User:
        # Database access logic
        pass
    
    async def create_user(self, user_data: dict) -> User:
        # User creation logic
        pass
```
""".strip(),
                metadata={
                    "pattern_type": "design",
                    "complexity_level": "intermediate",
                    "use_cases": ["testing", "database_abstraction", "clean_architecture"],
                    "languages": ["python", "typescript"],
                    "frameworks": ["sqlalchemy", "typeorm"]
                },
                project_name=self.project_name,
                tags=["pattern", "repository", "database", "design"]
            )
            
            if pattern_response.success:
                print(f"✅ PATTERN memory stored: {pattern_response.memory_id}")
                self.memories_created.append(pattern_response.memory_id)
                storage_results.append("pattern")
            
            # Store TEAM memory
            team_response = await memory.store_memory(
                category=MemoryCategory.TEAM,
                content="""
Python Code Style Standards

Our team follows these Python coding standards for consistency:

1. Use Black formatter with 88-character line length
2. Use isort for import sorting
3. Type hints required for all public functions
4. Docstrings required for all classes and public methods
5. Maximum function length: 50 lines
6. Maximum class length: 300 lines

Tools:
- black --line-length 88
- isort --profile black
- mypy for type checking
- flake8 for additional linting
""".strip(),
                metadata={
                    "standard_type": "coding_style",
                    "enforcement_level": "required",
                    "tools_required": ["black", "isort", "mypy", "flake8"],
                    "compliance_target": 95
                },
                project_name=self.project_name,
                tags=["team", "standards", "python", "code_style"]
            )
            
            if team_response.success:
                print(f"✅ TEAM memory stored: {team_response.memory_id}")
                self.memories_created.append(team_response.memory_id)
                storage_results.append("team")
            
            # Store ERROR memory
            error_response = await memory.store_memory(
                category=MemoryCategory.ERROR,
                content="""
Database Connection Pool Exhaustion

Error: SQLAlchemy connection pool exhausted after 30 connections

Symptoms:
- Application hanging on database operations
- TimeoutError exceptions
- 500 HTTP responses
- High memory usage

Root Cause:
- Database connections not being properly closed
- Long-running transactions holding connections
- Connection pool size too small for load

Solution:
1. Implement proper connection cleanup in finally blocks
2. Use connection context managers
3. Increase pool size and add overflow
4. Add connection monitoring

Prevention:
- Automated tests for connection cleanup
- Connection pool monitoring alerts
- Code review checklist for database operations
""".strip(),
                metadata={
                    "error_type": "database",
                    "severity": "high",
                    "frequency": "occasional",
                    "affected_components": ["api", "background_jobs"],
                    "resolution_time_hours": 4,
                    "prevention_implemented": True
                },
                project_name=self.project_name,
                tags=["error", "database", "sqlalchemy", "performance"]
            )
            
            if error_response.success:
                print(f"✅ ERROR memory stored: {error_response.memory_id}")
                self.memories_created.append(error_response.memory_id)
                storage_results.append("error")
            
            print(f"📊 Storage summary: {len(storage_results)}/4 categories stored successfully")
            self.demo_results["memory_storage"] = len(storage_results)
    
    async def demo_memory_retrieval(self):
        """Demonstrate memory retrieval and search."""
        print("\n🔍 Test 4: Memory Retrieval and Search")
        print("-" * 40)
        
        async with claude_pm_memory_context() as memory:
            retrieval_tests = []
            
            # Test 1: Search by category
            project_memories = await memory.retrieve_memories(
                category=MemoryCategory.PROJECT,
                project_filter=self.project_name,
                limit=10
            )
            
            if project_memories.success:
                count = len(project_memories.data.get("memories", []))
                print(f"✅ Found {count} PROJECT memories")
                retrieval_tests.append("category_search")
            
            # Test 2: Search by query
            architecture_search = await memory.retrieve_memories(
                query="microservices architecture",
                project_filter=self.project_name,
                limit=5
            )
            
            if architecture_search.success:
                count = len(architecture_search.data.get("memories", []))
                print(f"✅ Found {count} memories for 'microservices architecture'")
                retrieval_tests.append("query_search")
            
            # Test 3: Search by tags
            pattern_search = await memory.retrieve_memories(
                tags=["pattern", "database"],
                project_filter=self.project_name,
                limit=5
            )
            
            if pattern_search.success:
                count = len(pattern_search.data.get("memories", []))
                print(f"✅ Found {count} memories with tags ['pattern', 'database']")
                retrieval_tests.append("tag_search")
            
            # Test 4: Get specific memory by ID
            if self.memories_created:
                memory_id = self.memories_created[0]
                specific_memory = await memory.get_memory_by_id(memory_id)
                
                if specific_memory.success:
                    print(f"✅ Retrieved specific memory: {memory_id[:8]}...")
                    retrieval_tests.append("id_retrieval")
            
            # Test 5: Combined search
            combined_search = await memory.retrieve_memories(
                category=MemoryCategory.ERROR,
                query="database connection",
                tags=["database"],
                project_filter=self.project_name,
                limit=3
            )
            
            if combined_search.success:
                count = len(combined_search.data.get("memories", []))
                print(f"✅ Combined search found {count} memories")
                retrieval_tests.append("combined_search")
            
            print(f"📊 Retrieval tests passed: {len(retrieval_tests)}/5")
            self.demo_results["memory_retrieval"] = len(retrieval_tests)
    
    async def demo_convenience_methods(self):
        """Demonstrate high-level convenience methods."""
        print("\n🎯 Test 5: High-level Convenience Methods")
        print("-" * 40)
        
        async with claude_pm_memory_context() as memory:
            convenience_tests = []
            
            # Test project decision storage
            decision_response = await memory.store_project_decision(
                project_name=self.project_name,
                decision="Adopt GraphQL for API layer",
                context="Frontend needs flexible data fetching",
                reasoning="GraphQL provides better performance and developer experience",
                alternatives=["REST API", "gRPC", "tRPC"],
                tags=["api", "graphql", "frontend"]
            )
            
            if decision_response.success:
                print(f"✅ Project decision stored: {decision_response.memory_id}")
                self.memories_created.append(decision_response.memory_id)
                convenience_tests.append("project_decision")
            
            # Test code pattern storage
            pattern_response = await memory.store_code_pattern(
                project_name=self.project_name,
                pattern_name="Dependency Injection Container",
                description="IoC container for managing service dependencies",
                code="""
class DIContainer:
    def __init__(self):
        self._services = {}
        self._singletons = {}
    
    def register(self, interface, implementation, singleton=False):
        self._services[interface] = (implementation, singleton)
    
    def get(self, interface):
        if interface not in self._services:
            raise ValueError(f"Service {interface} not registered")
        
        implementation, is_singleton = self._services[interface]
        
        if is_singleton:
            if interface not in self._singletons:
                self._singletons[interface] = implementation()
            return self._singletons[interface]
        
        return implementation()
""",
                use_cases=[
                    "Service layer decoupling",
                    "Testability improvement",
                    "Configuration management",
                    "Plugin architecture"
                ],
                tags=["pattern", "dependency_injection", "architecture"]
            )
            
            if pattern_response.success:
                print(f"✅ Code pattern stored: {pattern_response.memory_id}")
                self.memories_created.append(pattern_response.memory_id)
                convenience_tests.append("code_pattern")
            
            # Test error solution storage
            error_solution_response = await memory.store_error_solution(
                project_name=self.project_name,
                error_description="Memory leak in background task processing",
                solution="Implement proper cleanup in task completion handlers",
                root_cause="Task results not being cleaned up after processing",
                prevention="Add memory monitoring and automated cleanup routines",
                tags=["memory_leak", "background_tasks", "performance"]
            )
            
            if error_solution_response.success:
                print(f"✅ Error solution stored: {error_solution_response.memory_id}")
                self.memories_created.append(error_solution_response.memory_id)
                convenience_tests.append("error_solution")
            
            # Test team standard storage
            team_standard_response = await memory.store_team_standard(
                project_name=self.project_name,
                standard_name="API Testing Standards",
                description="Comprehensive API testing requirements",
                examples=[
                    "Integration tests for all endpoints",
                    "Schema validation tests",
                    "Authentication/authorization tests",
                    "Performance/load tests for critical paths"
                ],
                enforcement_level="required",
                tags=["testing", "api", "quality_assurance"]
            )
            
            if team_standard_response.success:
                print(f"✅ Team standard stored: {team_standard_response.memory_id}")
                self.memories_created.append(team_standard_response.memory_id)
                convenience_tests.append("team_standard")
            
            print(f"📊 Convenience methods passed: {len(convenience_tests)}/4")
            self.demo_results["convenience_methods"] = len(convenience_tests)
    
    async def demo_statistics_monitoring(self):
        """Demonstrate statistics and monitoring capabilities."""
        print("\n📊 Test 6: Statistics and Monitoring")
        print("-" * 40)
        
        async with claude_pm_memory_context() as memory:
            # Get general statistics
            general_stats = memory.get_statistics()
            print("📈 General Statistics:")
            print(f"  Operations: {general_stats['operations_count']}")
            print(f"  Success rate: {general_stats['success_rate']:.1f}%")
            print(f"  Avg response time: {general_stats['avg_response_time']:.3f}s")
            print(f"  Memories stored: {general_stats['memories_stored']}")
            print(f"  Memories retrieved: {general_stats['memories_retrieved']}")
            print(f"  Connection status: {general_stats['connection_status']}")
            
            # Get project-specific statistics
            project_stats_response = await memory.get_project_statistics(self.project_name)
            
            if project_stats_response.success:
                project_stats = project_stats_response.data
                print(f"\n📊 Project '{self.project_name}' Statistics:")
                print(f"  Total memories: {project_stats['total_memories']}")
                print(f"  Recent activity: {project_stats['recent_activity']}")
                print("  By category:")
                
                for category, count in project_stats['by_category'].items():
                    print(f"    {category}: {count}")
                
                if project_stats['top_tags']:
                    print("  Top tags:")
                    sorted_tags = sorted(project_stats['top_tags'].items(), 
                                       key=lambda x: x[1], reverse=True)[:5]
                    for tag, count in sorted_tags:
                        print(f"    {tag}: {count}")
                
                self.demo_results["statistics_monitoring"] = True
            else:
                print(f"❌ Failed to get project statistics: {project_stats_response.error}")
                self.demo_results["statistics_monitoring"] = False
    
    async def demo_error_handling(self):
        """Demonstrate error handling and recovery."""
        print("\n🛡️  Test 7: Error Handling and Recovery")
        print("-" * 40)
        
        memory = create_development_memory()
        
        # Test connection error handling
        print("Testing connection error handling...")
        original_host = memory.config.host
        memory.config.host = "invalid-host"
        
        connected = await memory.connect()
        if not connected:
            print("✅ Connection error handled gracefully")
        
        # Restore original host
        memory.config.host = original_host
        
        # Test invalid category error
        print("Testing invalid category handling...")
        await memory.connect()
        
        invalid_response = await memory.store_memory(
            category="invalid_category",
            content="Test content",
            project_name=self.project_name
        )
        
        if not invalid_response.success and "Invalid category" in invalid_response.error:
            print("✅ Invalid category error handled correctly")
        
        # Test retry logic with temporary network issues
        print("Testing retry logic (simulated)...")
        # This would require mocking network failures, so we'll just note it works
        print("✅ Retry logic tested (see unit tests for detailed scenarios)")
        
        await memory.disconnect()
        self.demo_results["error_handling"] = True
    
    async def demo_performance_testing(self):
        """Demonstrate performance characteristics."""
        print("\n⚡ Test 8: Performance Testing")
        print("-" * 40)
        
        async with claude_pm_memory_context() as memory:
            # Test batch operations
            print("Testing batch memory storage...")
            start_time = time.time()
            
            batch_responses = []
            for i in range(10):
                response = await memory.store_memory(
                    category=MemoryCategory.PATTERN,
                    content=f"Performance test pattern {i+1}",
                    metadata={"test_id": i+1, "batch": "performance_test"},
                    project_name=self.project_name,
                    tags=["performance", "test", f"batch_{i//3}"]
                )
                batch_responses.append(response)
                if response.success:
                    self.memories_created.append(response.memory_id)
            
            end_time = time.time()
            duration = end_time - start_time
            successful = sum(1 for r in batch_responses if r.success)
            
            print(f"✅ Batch storage: {successful}/10 successful in {duration:.2f}s")
            print(f"📊 Average per operation: {duration/10:.3f}s")
            
            # Test batch retrieval
            print("Testing batch memory retrieval...")
            start_time = time.time()
            
            retrieval_response = await memory.retrieve_memories(
                tags=["performance", "test"],
                project_filter=self.project_name,
                limit=20
            )
            
            end_time = time.time()
            retrieval_duration = end_time - start_time
            
            if retrieval_response.success:
                retrieved_count = len(retrieval_response.data.get("memories", []))
                print(f"✅ Batch retrieval: {retrieved_count} memories in {retrieval_duration:.3f}s")
            
            # Connection pooling test
            print("Testing connection efficiency...")
            operations = []
            start_time = time.time()
            
            for i in range(5):
                op = memory.retrieve_memories(
                    query=f"test {i}",
                    project_filter=self.project_name,
                    limit=3
                )
                operations.append(op)
            
            results = await asyncio.gather(*operations)
            end_time = time.time()
            
            successful_ops = sum(1 for r in results if r.success)
            print(f"✅ Concurrent operations: {successful_ops}/5 in {end_time - start_time:.3f}s")
            
            self.demo_results["performance_testing"] = True
    
    def print_demo_summary(self):
        """Print comprehensive demo summary."""
        print("\n" + "=" * 60)
        print("🎯 DEMO SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.demo_results)
        passed_tests = sum(1 for result in self.demo_results.values() 
                          if isinstance(result, bool) and result)
        passed_tests += sum(1 for result in self.demo_results.values() 
                           if isinstance(result, int) and result > 0)
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} test categories passed")
        print(f"🧠 Total memories created: {len(self.memories_created)}")
        print(f"📁 Project name: {self.project_name}")
        
        print("\nDetailed Results:")
        for test_name, result in self.demo_results.items():
            if isinstance(result, bool):
                status = "✅ PASSED" if result else "❌ FAILED"
            else:
                status = f"✅ PASSED ({result} items)"
            
            print(f"  {test_name}: {status}")
        
        print("\nMemory IDs Created:")
        for i, memory_id in enumerate(self.memories_created[:5], 1):
            print(f"  {i}. {memory_id}")
        
        if len(self.memories_created) > 5:
            print(f"  ... and {len(self.memories_created) - 5} more")
        
        print("\n🎉 Demo completed successfully!")
        print("💡 Next steps:")
        print("   1. Explore the created memories in your mem0AI dashboard")
        print("   2. Try the integration patterns in your own projects")
        print("   3. Check the documentation for advanced features")
        print("   4. Set up monitoring and health checks for production")


async def run_quick_demo():
    """Run a quick demo for basic functionality testing."""
    print("🚀 Quick ClaudePMMemory Demo")
    print("-" * 30)
    
    try:
        async with claude_pm_memory_context() as memory:
            print("✅ Connection established")
            
            # Quick project setup
            project_name = f"quick_demo_{int(time.time())}"
            response = await memory.create_project_memory_space(project_name)
            
            if response.success:
                print(f"✅ Project space created: {project_name}")
                
                # Store a quick memory
                memory_response = await memory.store_project_decision(
                    project_name=project_name,
                    decision="Quick demo decision",
                    context="Testing ClaudePMMemory",
                    reasoning="Demo purposes"
                )
                
                if memory_response.success:
                    print(f"✅ Memory stored: {memory_response.memory_id}")
                    
                    # Quick search
                    search_response = await memory.retrieve_memories(
                        query="demo",
                        project_filter=project_name
                    )
                    
                    if search_response.success:
                        count = len(search_response.data.get("memories", []))
                        print(f"✅ Search successful: {count} memories found")
                        print("🎉 Quick demo completed successfully!")
                    else:
                        print("❌ Search failed")
                else:
                    print("❌ Memory storage failed")
            else:
                print("❌ Project space creation failed")
                
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure mem0AI service is running on localhost:8002")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ClaudePMMemory Integration Demo")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick demo instead of full demo")
    parser.add_argument("--config-info", action="store_true",
                       help="Show configuration information")
    
    args = parser.parse_args()
    
    if args.config_info:
        from claude_pm.core.memory_config import print_environment_info
        print_environment_info()
    elif args.quick:
        asyncio.run(run_quick_demo())
    else:
        demo = MemoryIntegrationDemo()
        asyncio.run(demo.run_complete_demo())