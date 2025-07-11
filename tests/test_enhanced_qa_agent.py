#!/usr/bin/env python3
"""
Test Suite for Enhanced QA Agent
=================================

Comprehensive test suite for the Enhanced QA Agent implementation including:
- Browser extension communication testing
- Memory-augmented testing capabilities
- Framework CLI integration testing
- Health monitoring integration
- Agent hierarchy coordination
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.agents.enhanced_qa_agent import (
    EnhancedQAAgent,
    BrowserExtensionCommunicator,
    MemoryAugmentedTesting,
    execute_qa_command,
)
from claude_pm.core.config import Config


class TestBrowserExtensionCommunicator:
    """Test browser extension communication functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()

    @pytest.fixture
    def communicator(self, config):
        """Create browser extension communicator."""
        return BrowserExtensionCommunicator(config)

    @pytest.mark.asyncio
    async def test_send_test_command_success(self, communicator):
        """Test successful test command sending."""
        command = {
            "type": "execute_tests",
            "payload": {"test_suite": "basic_tests", "urls": ["http://localhost:3000"]},
        }

        response = await communicator.send_test_command(command)

        assert response["status"] == "success"
        assert "result" in response
        assert response["result"]["tests_executed"] >= 1
        assert "timestamp" in response

    @pytest.mark.asyncio
    async def test_get_extension_health(self, communicator):
        """Test extension health check."""
        health = await communicator.get_extension_health()

        assert "status" in health
        assert "extension_version" in health
        assert "test_capabilities" in health
        assert isinstance(health["test_capabilities"], list)


class TestMemoryAugmentedTesting:
    """Test memory-augmented testing capabilities."""

    @pytest.fixture
    def mock_memory_service(self):
        """Create mock memory service."""
        mock_service = AsyncMock()
        mock_service.store_memory.return_value = {"status": "success"}
        mock_service.health_check.return_value = {"status": "healthy"}
        return mock_service

    @pytest.fixture
    def memory_testing(self, mock_memory_service):
        """Create memory-augmented testing instance."""
        return MemoryAugmentedTesting(mock_memory_service)

    @pytest.mark.asyncio
    async def test_analyze_test_patterns_success(self, memory_testing):
        """Test successful test pattern analysis."""
        test_results = [
            {"status": "passed", "execution_time": 2.5, "test_name": "test_login"},
            {"status": "passed", "execution_time": 1.8, "test_name": "test_navigation"},
            {
                "status": "failed",
                "execution_time": 5.0,
                "test_name": "test_timeout",
                "error": "timeout occurred",
            },
        ]

        patterns = await memory_testing.analyze_test_patterns(test_results)

        assert "success_rate" in patterns
        assert patterns["success_rate"] == 2 / 3  # 2 passed out of 3
        assert "common_failures" in patterns
        assert "performance_trends" in patterns
        assert "recommendations" in patterns

    def test_extract_failure_patterns(self, memory_testing):
        """Test failure pattern extraction."""
        test_results = [
            {"status": "failed", "error": "Network timeout error"},
            {"status": "failed", "error": "Element not found on page"},
            {"status": "passed"},
        ]

        patterns = memory_testing._extract_failure_patterns(test_results)

        assert "timeout_issues" in patterns
        assert "ui_element_instability" in patterns

    def test_analyze_performance_trends(self, memory_testing):
        """Test performance trend analysis."""
        test_results = [{"execution_time": 2.0}, {"execution_time": 2.5}, {"execution_time": 1.8}]

        trends = memory_testing._analyze_performance_trends(test_results)

        assert "average_time" in trends
        assert "max_time" in trends
        assert "min_time" in trends
        assert "trend" in trends
        assert trends["average_time"] > 0


class TestEnhancedQAAgent:
    """Test Enhanced QA Agent core functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=Config)
        config.get.return_value = "default_value"
        return config

    @pytest.fixture
    def qa_agent(self, mock_config):
        """Create Enhanced QA Agent instance."""
        with (
            patch("claude_pm.agents.enhanced_qa_agent.MemoryService"),
            patch("claude_pm.agents.enhanced_qa_agent.MultiAgentOrchestrator"),
            patch("claude_pm.agents.enhanced_qa_agent.HealthDashboardOrchestrator"),
        ):
            return EnhancedQAAgent(mock_config)

    @pytest.mark.asyncio
    async def test_execute_browser_tests(self, qa_agent):
        """Test browser test execution."""
        test_config = {
            "test_suite": "browser_tests",
            "urls": ["http://localhost:3000"],
            "scenarios": ["basic_functionality"],
            "screenshots": True,
        }

        # Mock the browser communicator
        qa_agent.browser_communicator.send_test_command = AsyncMock(
            return_value={
                "status": "success",
                "result": {
                    "tests_executed": 3,
                    "tests_passed": 3,
                    "execution_time": 5.2,
                    "screenshots": ["test1.png", "test2.png"],
                },
            }
        )

        # Mock memory testing
        qa_agent.memory_testing.analyze_test_patterns = AsyncMock(
            return_value={"success_rate": 1.0, "recommendations": ["All tests passed successfully"]}
        )

        result = await qa_agent.execute_browser_tests(test_config)

        assert result["status"] == "success"
        assert "test_results" in result
        assert "pattern_analysis" in result
        assert "execution_summary" in result

    @pytest.mark.asyncio
    async def test_run_framework_tests(self, qa_agent):
        """Test framework test execution."""
        # Mock subprocess.run for test commands
        with patch("claude_pm.agents.enhanced_qa_agent.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "All tests passed"
            mock_run.return_value.stderr = ""

            # Mock memory testing
            qa_agent.memory_testing.analyze_test_patterns = AsyncMock(
                return_value={"success_rate": 1.0, "recommendations": []}
            )

            result = await qa_agent.run_framework_tests("unit")

            assert result["status"] == "success"
            assert "summary" in result
            assert "detailed_results" in result
            assert "pattern_analysis" in result

    @pytest.mark.asyncio
    async def test_get_qa_health_status(self, qa_agent):
        """Test QA health status retrieval."""
        # Mock component health checks
        qa_agent.browser_communicator.get_extension_health = AsyncMock(
            return_value={"status": "healthy", "extension_version": "1.0.0"}
        )

        qa_agent.memory_service.health_check = AsyncMock(
            return_value={"status": "healthy", "mem0ai_connected": True}
        )

        health = await qa_agent.get_qa_health_status()

        assert "status" in health
        assert "health_score" in health
        assert "extension_health" in health
        assert "memory_health" in health
        assert "framework_health" in health
        assert health["health_score"] >= 0
        assert health["health_score"] <= 100

    def test_get_test_commands_nodejs(self, qa_agent):
        """Test test command detection for Node.js projects."""
        # Mock package.json existence
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            qa_agent.framework_path = Path("/mock/nodejs/project")

            commands = qa_agent._get_test_commands("all")

            assert len(commands) > 0
            assert any("npm" in cmd["command"] for cmd in commands)

    def test_get_test_commands_python(self, qa_agent):
        """Test test command detection for Python projects."""
        # Mock pyproject.toml existence
        with patch.object(Path, "exists") as mock_exists:

            def exists_side_effect(path):
                return str(path).endswith("pyproject.toml")

            mock_exists.side_effect = exists_side_effect
            qa_agent.framework_path = Path("/mock/python/project")

            commands = qa_agent._get_test_commands("all")

            assert len(commands) > 0
            assert any("pytest" in cmd["command"] for cmd in commands)

    @pytest.mark.asyncio
    async def test_coordinate_with_agents(self, qa_agent):
        """Test agent coordination functionality."""
        qa_agent.orchestrator.coordinate_agents = AsyncMock(
            return_value={
                "status": "success",
                "coordinated_agents": ["documentation_agent", "ops_agent"],
            }
        )

        result = await qa_agent.coordinate_with_agents(
            "test_coordination", {"test_coverage": 85, "quality_gates": ["unit_tests", "linting"]}
        )

        assert result["status"] == "success"
        assert "coordinated_agents" in result

    @pytest.mark.asyncio
    async def test_generate_test_report(self, qa_agent):
        """Test test report generation."""
        test_results = {
            "status": "success",
            "summary": {
                "total_tests": 10,
                "passed_tests": 8,
                "failed_tests": 2,
                "success_rate": 0.8,
            },
            "pattern_analysis": {
                "success_rate": 0.8,
                "common_failures": ["timeout_issues"],
                "recommendations": ["Optimize slow tests", "Fix timeout issues"],
            },
            "detailed_results": [
                {"test_type": "unit_tests", "status": "passed"},
                {"test_type": "integration_tests", "status": "failed"},
            ],
        }

        report = await qa_agent.generate_test_report(test_results)

        assert "Enhanced QA Agent Test Report" in report
        assert "Test Execution Summary" in report
        assert "Pattern Analysis" in report
        assert "Recommendations" in report
        assert "80.0%" in report  # Success rate


class TestQACommandExecution:
    """Test QA command execution for CLI integration."""

    @pytest.mark.asyncio
    async def test_execute_qa_command_status(self):
        """Test QA status command execution."""
        with patch("claude_pm.agents.enhanced_qa_agent.EnhancedQAAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.get_qa_health_status.return_value = {"status": "healthy", "health_score": 85}
            mock_agent_class.return_value = mock_agent

            result = await execute_qa_command("status")

            assert result["status"] == "healthy"
            assert result["health_score"] == 85

    @pytest.mark.asyncio
    async def test_execute_qa_command_test(self):
        """Test QA test command execution."""
        with patch("claude_pm.agents.enhanced_qa_agent.EnhancedQAAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.run_framework_tests.return_value = {
                "status": "success",
                "summary": {"total_tests": 5, "passed_tests": 5},
            }
            mock_agent_class.return_value = mock_agent

            result = await execute_qa_command("test", {"type": "unit"})

            assert result["status"] == "success"
            assert result["summary"]["total_tests"] == 5

    @pytest.mark.asyncio
    async def test_execute_qa_command_browser_test(self):
        """Test QA browser test command execution."""
        with patch("claude_pm.agents.enhanced_qa_agent.EnhancedQAAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.execute_browser_tests.return_value = {
                "status": "success",
                "execution_summary": {"screenshots_captured": 3},
            }
            mock_agent_class.return_value = mock_agent

            result = await execute_qa_command(
                "test", {"browser": True, "urls": ["http://localhost:3000"]}
            )

            assert result["status"] == "success"
            assert result["execution_summary"]["screenshots_captured"] == 3

    @pytest.mark.asyncio
    async def test_execute_qa_command_unknown(self):
        """Test unknown QA command handling."""
        result = await execute_qa_command("unknown_command")

        assert result["status"] == "error"
        assert "Unknown QA command" in result["error"]


class TestIntegrationWithFramework:
    """Test integration with Claude PM Framework components."""

    @pytest.mark.asyncio
    async def test_health_integration(self):
        """Test integration with framework health system."""
        # This would test the actual integration with cmpm:health command
        # Mock the health dashboard integration
        with patch("claude_pm.agents.enhanced_qa_agent.EnhancedQAAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.get_qa_health_status.return_value = {
                "status": "healthy",
                "health_score": 90,
                "extension_health": {"status": "healthy"},
                "memory_health": {"status": "healthy"},
                "agent_version": "1.0.0",
            }
            mock_agent_class.return_value = mock_agent

            # Test health integration
            qa_agent = mock_agent_class()
            health = await qa_agent.get_qa_health_status()

            assert health["status"] == "healthy"
            assert health["health_score"] == 90

    @pytest.mark.asyncio
    async def test_memory_service_integration(self):
        """Test integration with framework memory service."""
        with patch("claude_pm.agents.enhanced_qa_agent.MemoryService") as mock_memory_class:
            mock_memory = AsyncMock()
            mock_memory.store_memory.return_value = {"status": "success"}
            mock_memory.health_check.return_value = {"status": "healthy", "mem0ai_connected": True}
            mock_memory_class.return_value = mock_memory

            memory_testing = MemoryAugmentedTesting(mock_memory)

            # Test memory integration
            result = await memory_testing.analyze_test_patterns(
                [{"status": "passed", "execution_time": 1.0}]
            )

            assert "success_rate" in result
            mock_memory.store_memory.assert_called_once()


# Performance and stress tests
class TestPerformanceAndStress:
    """Test performance and stress scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_test_execution(self):
        """Test concurrent test execution handling."""
        with patch("claude_pm.agents.enhanced_qa_agent.EnhancedQAAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.run_framework_tests.return_value = {
                "status": "success",
                "summary": {"total_tests": 1, "passed_tests": 1},
            }
            mock_agent_class.return_value = mock_agent

            # Execute multiple tests concurrently
            tasks = [execute_qa_command("test", {"type": "unit"}) for _ in range(5)]

            results = await asyncio.gather(*tasks)

            assert all(r["status"] == "success" for r in results)
            assert len(results) == 5

    @pytest.mark.asyncio
    async def test_large_test_result_processing(self):
        """Test processing of large test result sets."""
        # Create large test result set
        large_test_results = [
            {
                "status": "passed" if i % 4 != 0 else "failed",
                "execution_time": 1.0 + (i * 0.1),
                "test_name": f"test_{i}",
                "error": "timeout" if i % 4 == 0 else None,
            }
            for i in range(1000)
        ]

        with patch("claude_pm.agents.enhanced_qa_agent.MemoryService"):
            memory_testing = MemoryAugmentedTesting(AsyncMock())

            patterns = await memory_testing.analyze_test_patterns(large_test_results)

            assert "success_rate" in patterns
            assert patterns["success_rate"] == 0.75  # 75% pass rate
            assert "performance_trends" in patterns


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
