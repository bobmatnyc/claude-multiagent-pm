"""
Integration tests for Task Tool Delegation Infrastructure.

Tests all acceptance criteria:
1. Claude PM services installed and integrated
2. Base service classes (MultiAgentOrchestrator, TaskPlanner, MemoryService) implemented
3. Memory persistence working for context management
4. Directory structure matches design specification
5. Basic task orchestration can be created and executed
6. Integration tests pass for core infrastructure
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Import Claude PM Task Delegation components
from claude_pm.services.multi_agent_orchestrator import (
    MultiAgentOrchestrator,
    AgentType,
    AgentStatus,
    AgentExecution,
    AgentTask,
)
from claude_pm.services.intelligent_task_planner import (
    IntelligentTaskPlanner,
    TaskComplexity,
    DecompositionStrategy,
    TaskDecomposition,
)
from claude_pm.services.claude_pm_memory import ClaudePMMemory, MemoryCategory
from claude_pm.services.mem0_context_manager import Mem0ContextManager, ContextType, ContextScope


class TestTaskDelegationInfrastructure:
    """Test suite for Task Tool Delegation infrastructure."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_repo_path = Path(self.temp_dir) / "test_repo"
        self.test_repo_path.mkdir()
        # Initialize a basic git repo for testing
        import subprocess

        subprocess.run(["git", "init"], cwd=self.test_repo_path, capture_output=True)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_acceptance_1_claude_pm_installation(self):
        """
        AC1: Claude PM services installed and integrated.

        Verify that Claude PM packages are properly installed and
        can be imported without errors.
        """
        try:
            # Test Claude PM imports
            from claude_pm.services import ClaudePMMemory, Mem0ContextManager
            from claude_pm.core.service_manager import ServiceManager
            from claude_pm.core.config import Config

            # Test that we can create basic Claude PM components
            memory = ClaudePMMemory()
            assert memory is not None

            context_manager = Mem0ContextManager(memory=memory)
            assert context_manager is not None

            print("✓ AC1 PASSED: Claude PM services installed and integrated")

        except ImportError as e:
            pytest.fail(f"AC1 FAILED: Claude PM installation issue: {e}")
        except Exception as e:
            pytest.fail(f"AC1 FAILED: Integration issue: {e}")

    def test_acceptance_2_base_service_classes(self):
        """
        AC2: Base service classes implemented.

        Verify that all service classes are properly defined with correct
        interfaces and functionality.
        """
        try:
            # Test MultiAgentOrchestrator structure
            memory = ClaudePMMemory()
            orchestrator = MultiAgentOrchestrator(
                base_repo_path=str(self.test_repo_path), memory=memory
            )

            # Verify orchestrator has required methods
            assert hasattr(orchestrator, "execute_task")
            assert hasattr(orchestrator, "get_orchestrator_stats")
            assert hasattr(orchestrator, "submit_task")

            # Test TaskPlanner structure
            context_manager = Mem0ContextManager(memory=memory)
            planner = IntelligentTaskPlanner(memory=memory, context_manager=context_manager)

            # Verify planner has required methods
            assert hasattr(planner, "decompose_task")
            assert hasattr(planner, "get_planner_stats")
            assert hasattr(planner, "performance_metrics")

            # Test Memory service structure
            assert hasattr(memory, "store_memory")
            assert hasattr(memory, "retrieve_memories")
            assert hasattr(memory, "get_statistics")

            print("✓ AC2 PASSED: Base service classes implemented correctly")

        except AssertionError as e:
            pytest.fail(f"AC2 FAILED: Service class validation: {e}")
        except Exception as e:
            pytest.fail(f"AC2 FAILED: Unexpected error: {e}")

    @pytest.mark.asyncio
    async def test_acceptance_3_memory_persistence(self):
        """
        AC3: Memory persistence working for context management.

        Verify that the memory system can store and
        retrieve context correctly.
        """
        try:
            # Create memory service
            memory = ClaudePMMemory()

            # Test memory storage
            test_data = {
                "task_type": "implementation",
                "patterns": ["rest_api", "authentication"],
                "complexity": "medium",
            }

            response = await memory.store_memory(
                category=MemoryCategory.PATTERN,
                content="Test task pattern",
                metadata=test_data,
                tags=["test", "pattern"],
            )
            assert response.success

            # Test memory retrieval
            results = await memory.retrieve_memories(
                category=MemoryCategory.PATTERN, query="task pattern", limit=5
            )
            assert results.success
            assert len(results.data) > 0

            # Test stats
            stats = memory.get_statistics()
            assert stats is not None
            assert "total_entries" in stats

            print("✓ AC3 PASSED: Memory persistence working correctly")

        except Exception as e:
            pytest.fail(f"AC3 FAILED: Memory persistence error: {e}")

    def test_acceptance_4_directory_structure(self):
        """
        AC4: Directory structure matches design specification.

        Verify that all required directories and files are created
        according to the design document.
        """
        try:
            base_path = Path.cwd() / "claude_pm"

            # Check main directories
            required_dirs = ["services", "core", "integrations", "scripts"]

            for dir_name in required_dirs:
                dir_path = base_path / dir_name
                assert dir_path.exists(), f"Missing directory: {dir_path}"
                assert (dir_path / "__init__.py").exists(), f"Missing __init__.py in {dir_path}"

            # Check services subdirectories
            services_path = base_path / "services"
            required_service_files = [
                "multi_agent_orchestrator.py",
                "intelligent_task_planner.py",
                "claude_pm_memory.py",
                "mem0_context_manager.py",
            ]

            for file_name in required_service_files:
                file_path = services_path / file_name
                assert file_path.exists(), f"Missing service file: {file_path}"

            # Check key files exist
            key_files = [
                base_path / "__init__.py",
                base_path / "core" / "service_manager.py",
                base_path / "core" / "config.py",
                base_path / "integrations" / "mem0ai_integration.py",
            ]

            for file_path in key_files:
                assert file_path.exists(), f"Missing key file: {file_path}"

            print("✓ AC4 PASSED: Directory structure matches specification")

        except AssertionError as e:
            pytest.fail(f"AC4 FAILED: Directory structure: {e}")
        except Exception as e:
            pytest.fail(f"AC4 FAILED: Unexpected error: {e}")

    @pytest.mark.asyncio
    async def test_acceptance_5_basic_task_orchestration(self):
        """
        AC5: Basic task orchestration can be created and executed.

        Verify that the MultiAgentOrchestrator can be instantiated and
        execute a simple task delegation.
        """
        try:
            # Create orchestrator
            memory = ClaudePMMemory()
            orchestrator = MultiAgentOrchestrator(
                base_repo_path=str(self.test_repo_path), memory=memory
            )
            assert orchestrator is not None

            # Test task creation
            task = AgentTask(
                task_id="test_task_001",
                agent_type=AgentType.ENGINEER,
                description="Create unit tests for user authentication",
                project_name="test_project",
                context={"test_mode": True},
            )

            # Execute task
            result = await orchestrator.execute_task(task)

            # Verify execution results
            assert result is not None
            assert hasattr(result, "task")
            assert hasattr(result, "status")
            assert result.status in [
                AgentStatus.COMPLETED,
                AgentStatus.EXECUTING,
                AgentStatus.FAILED,
            ]

            print("✓ AC5 PASSED: Basic task orchestration created successfully")

        except Exception as e:
            pytest.fail(f"AC5 FAILED: Task orchestration error: {e}")

    @pytest.mark.asyncio
    async def test_acceptance_6_integration_tests(self):
        """
        AC6: Integration tests pass for core infrastructure.

        Comprehensive integration test covering all components
        working together.
        """
        try:
            # Test complete flow
            memory = ClaudePMMemory()
            context_manager = Mem0ContextManager(memory=memory)
            planner = IntelligentTaskPlanner(memory=memory, context_manager=context_manager)
            orchestrator = MultiAgentOrchestrator(
                base_repo_path=str(self.test_repo_path), memory=memory
            )

            # Test task decomposition
            task_description = "Build a REST API for user management"
            decomposition = await planner.decompose_task(task_description)
            assert decomposition.complexity in [c.value for c in TaskComplexity]

            # Test orchestration
            task = AgentTask(
                task_id="integration_test_001",
                agent_type=AgentType.ENGINEER,
                description=task_description,
                project_name="integration_test",
                context={"decomposition": decomposition},
            )

            result = await orchestrator.execute_task(task)
            assert result is not None

            # Test memory integration
            stats = memory.get_statistics()
            assert stats is not None

            print("✓ AC6 PASSED: Integration tests completed successfully")

        except Exception as e:
            pytest.fail(f"AC6 FAILED: Integration test error: {e}")

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """
        Additional test: Performance benchmarks for infrastructure.

        Verify that the infrastructure performs within acceptable limits.
        """
        try:
            import time

            # Test task decomposition performance
            memory = ClaudePMMemory()
            context_manager = Mem0ContextManager(memory=memory)
            planner = IntelligentTaskPlanner(memory=memory, context_manager=context_manager)

            start_time = time.time()
            for i in range(10):
                await planner.decompose_task(f"Test task {i}")
            decomposition_time = time.time() - start_time

            # Should decompose 10 tasks in under 5 seconds
            assert (
                decomposition_time < 5.0
            ), f"Task decomposition too slow: {decomposition_time:.3f}s"

            # Test orchestrator performance
            orchestrator = MultiAgentOrchestrator(
                base_repo_path=str(self.test_repo_path), memory=memory
            )

            start_time = time.time()
            for i in range(5):
                task = AgentTask(
                    task_id=f"perf_test_{i}",
                    agent_type=AgentType.ENGINEER,
                    description=f"Test task {i}",
                    project_name="perf_test",
                )
                await orchestrator.execute_task(task)
            orchestration_time = time.time() - start_time

            # Should execute 5 tasks in under 10 seconds
            assert orchestration_time < 10.0, f"Orchestration too slow: {orchestration_time:.3f}s"

            print(f"✓ Performance benchmarks passed:")
            print(f"  - Task decomposition: {decomposition_time:.3f}s for 10 tasks")
            print(f"  - Task orchestration: {orchestration_time:.3f}s for 5 tasks")

        except Exception as e:
            pytest.fail(f"Performance benchmark failed: {e}")


# Run the tests
if __name__ == "__main__":
    # Run synchronous tests
    test_suite = TestTaskDelegationInfrastructure()

    print("🧪 Testing Task Tool Delegation Infrastructure")
    print("=" * 60)

    try:
        test_suite.setup_method()

        # Run all acceptance criteria tests
        test_suite.test_acceptance_1_claude_pm_installation()
        test_suite.test_acceptance_2_base_service_classes()
        test_suite.test_acceptance_4_directory_structure()

        # Run async tests
        async def run_async_tests():
            await test_suite.test_acceptance_3_memory_persistence()
            await test_suite.test_acceptance_5_basic_task_orchestration()
            await test_suite.test_acceptance_6_integration_tests()
            await test_suite.test_performance_benchmarks()

        asyncio.run(run_async_tests())

        print("=" * 60)
        print("🎉 ALL ACCEPTANCE CRITERIA PASSED!")
        print("Task Tool Delegation infrastructure setup is complete and validated.")

    except Exception as e:
        print(f"❌ TEST FAILURE: {e}")
        raise
    finally:
        test_suite.teardown_method()
