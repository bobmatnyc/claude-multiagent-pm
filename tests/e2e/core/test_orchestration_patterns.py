"""
E2E Tests for Common Orchestration Patterns
===========================================

Tests for common orchestration patterns used by PM agents including:
- Agent delegation patterns (Documentation → QA → Version Control)
- Context filtering strategies across agent types
- Result aggregation from multiple agents
- Workflow templates (push, deploy, publish)
- Error handling and recovery patterns
- Performance optimization patterns
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from claude_pm.orchestration.backwards_compatible_orchestrator import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode,
    ReturnCode
)
from claude_pm.orchestration.message_bus import SimpleMessageBus, MessageResponse, MessageStatus


class TestOrchestrationPatterns:
    """Test common orchestration patterns used by PM agents."""
    
    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator instance for testing."""
        return BackwardsCompatibleOrchestrator(
            working_directory=str(tmp_path)
        )
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agent handlers for testing patterns."""
        agents = {}
        
        # Documentation agent mock
        async def documentation_handler(request_data):
            await asyncio.sleep(0.01)  # Simulate work
            return {
                "changelog": "## v1.0.0\n- Initial release",
                "version_impact": "major",
                "files_updated": ["CHANGELOG.md", "docs/release-notes.md"]
            }
        
        # QA agent mock
        async def qa_handler(request_data):
            await asyncio.sleep(0.02)  # Simulate work
            return {
                "test_results": {
                    "passed": 42,
                    "failed": 0,
                    "skipped": 3
                },
                "quality_score": 98.5,
                "ready_for_release": True
            }
        
        # Version Control agent mock
        async def version_control_handler(request_data):
            await asyncio.sleep(0.01)  # Simulate work
            return {
                "version_bumped": "1.0.0",
                "tags_created": ["v1.0.0"],
                "branch": "main",
                "commit": "abc123"
            }
        
        # Ops agent mock
        async def ops_handler(request_data):
            await asyncio.sleep(0.015)  # Simulate work
            return {
                "deployment_status": "success",
                "environment": request_data.get("environment", "production"),
                "url": "https://app.example.com"
            }
        
        # Security agent mock
        async def security_handler(request_data):
            await asyncio.sleep(0.01)  # Simulate work
            return {
                "vulnerabilities": [],
                "security_score": 100,
                "approved": True
            }
        
        agents["documentation"] = documentation_handler
        agents["qa"] = qa_handler
        agents["version_control"] = version_control_handler
        agents["ops"] = ops_handler
        agents["security"] = security_handler
        
        return agents
    
    @pytest.mark.asyncio
    async def test_push_pattern_delegation_flow(self, orchestrator, mock_agents):
        """Test the 'push' pattern: Documentation → QA → Version Control."""
        # Force LOCAL mode for performance
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Set up message bus with mock handlers
        message_bus = SimpleMessageBus()
        for agent_type, handler in mock_agents.items():
            message_bus.register_handler(agent_type, handler)
        
        orchestrator._local_executor._message_bus = message_bus
        
        # Track execution order
        execution_order = []
        
        # Wrap handlers to track order
        for agent_type in ["documentation", "qa", "version_control"]:
            original_handler = mock_agents[agent_type]
            async def tracking_handler(req, agent=agent_type, handler=original_handler):
                execution_order.append(agent)
                return await handler(req)
            message_bus.register_handler(agent_type, tracking_handler)
        
        # Execute push workflow
        results = {}
        
        # Step 1: Documentation agent
        doc_result, doc_code = await orchestrator.delegate_to_agent(
            agent_type="documentation",
            task_description="Generate changelog from recent commits",
            requirements=["Analyze semantic impact", "Update version docs"],
            task_id="push-001-doc"
        )
        results["documentation"] = doc_result
        
        # Step 2: QA agent (depends on documentation)
        qa_result, qa_code = await orchestrator.delegate_to_agent(
            agent_type="qa",
            task_description="Validate release readiness",
            context={
                "changelog": doc_result["results"]["changelog"],
                "version_impact": doc_result["results"]["version_impact"]
            },
            task_id="push-002-qa"
        )
        results["qa"] = qa_result
        
        # Step 3: Version Control (depends on both)
        vc_result, vc_code = await orchestrator.delegate_to_agent(
            agent_type="version_control",
            task_description="Apply version bump and create tags",
            context={
                "version_impact": doc_result["results"]["version_impact"],
                "qa_approved": qa_result["results"]["ready_for_release"],
                "changelog": doc_result["results"]["changelog"]
            },
            task_id="push-003-vc"
        )
        results["version_control"] = vc_result
        
        # Verify execution order
        assert execution_order == ["documentation", "qa", "version_control"]
        
        # Verify all succeeded
        assert all(r["success"] for r in results.values())
        
        # Verify data flow
        assert results["qa"]["subprocess_info"]["task_id"] == "push-002-qa"
        assert results["version_control"]["results"]["version_bumped"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_deploy_pattern_with_validation(self, orchestrator, mock_agents):
        """Test the 'deploy' pattern: Ops → QA validation."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Set up message bus
        message_bus = SimpleMessageBus()
        for agent_type, handler in mock_agents.items():
            message_bus.register_handler(agent_type, handler)
        
        orchestrator._local_executor._message_bus = message_bus
        
        # Step 1: Ops deployment
        deploy_result, deploy_code = await orchestrator.delegate_to_agent(
            agent_type="ops",
            task_description="Deploy to staging environment",
            environment="staging",
            task_id="deploy-001"
        )
        
        # Step 2: QA validation
        validation_result, validation_code = await orchestrator.delegate_to_agent(
            agent_type="qa",
            task_description="Validate deployment",
            context={
                "deployment_url": deploy_result["results"]["url"],
                "environment": deploy_result["results"]["environment"]
            },
            task_id="deploy-002"
        )
        
        # Verify deployment succeeded
        assert deploy_result["success"] is True
        assert deploy_result["results"]["environment"] == "staging"
        
        # Verify validation passed
        assert validation_result["success"] is True
        assert validation_result["results"]["ready_for_release"] is True
    
    @pytest.mark.asyncio
    async def test_publish_pattern_with_security(self, orchestrator, mock_agents):
        """Test the 'publish' pattern: Security → Documentation → Ops."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Set up message bus
        message_bus = SimpleMessageBus()
        for agent_type, handler in mock_agents.items():
            message_bus.register_handler(agent_type, handler)
        
        orchestrator._local_executor._message_bus = message_bus
        
        # Step 1: Security check
        security_result, _ = await orchestrator.delegate_to_agent(
            agent_type="security",
            task_description="Security audit for release",
            task_id="publish-001"
        )
        
        # Step 2: Documentation update
        doc_result, _ = await orchestrator.delegate_to_agent(
            agent_type="documentation",
            task_description="Update public documentation",
            context={"security_approved": security_result["results"]["approved"]},
            task_id="publish-002"
        )
        
        # Step 3: Publish to production
        publish_result, _ = await orchestrator.delegate_to_agent(
            agent_type="ops",
            task_description="Publish to npm/pypi",
            context={
                "security_approved": security_result["results"]["approved"],
                "docs_updated": doc_result["results"]["files_updated"]
            },
            environment="production",
            task_id="publish-003"
        )
        
        # Verify all steps succeeded
        assert security_result["success"] is True
        assert doc_result["success"] is True
        assert publish_result["success"] is True
        assert publish_result["results"]["environment"] == "production"
    
    @pytest.mark.asyncio
    async def test_context_filtering_by_agent_type(self, orchestrator):
        """Test context filtering strategies for different agent types."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Create full context
        full_context = {
            "files": {
                "src/main.py": "# Main application code",
                "src/utils.py": "# Utility functions",
                "tests/test_main.py": "# Test code",
                "docs/api.md": "# API documentation",
                "README.md": "# Project readme",
                ".env": "SECRET_KEY=xxx",
                "deploy/k8s.yaml": "# K8s config"
            },
            "memory": {
                "project_type": "python",
                "last_deploy": "2023-01-01",
                "api_keys": {"openai": "sk-xxx"}
            }
        }
        
        # Define filtering rules for each agent type
        agent_filters = {
            "documentation": {
                "file_patterns": ["*.md", "docs/*"],
                "exclude_patterns": [".env", "*.secret"],
                "memory_keys": ["project_type"]
            },
            "qa": {
                "file_patterns": ["tests/*", "src/*"],
                "exclude_patterns": [".env", "deploy/*"],
                "memory_keys": ["project_type"]
            },
            "ops": {
                "file_patterns": ["deploy/*", "*.yaml", "*.yml"],
                "exclude_patterns": [".env"],
                "memory_keys": ["last_deploy"]
            },
            "security": {
                "file_patterns": ["*"],  # Needs to see everything
                "exclude_patterns": [],
                "memory_keys": ["api_keys", "project_type"]
            }
        }
        
        # Mock context manager with filtering
        mock_context_manager = MagicMock()
        
        def filter_context(agent_type, context):
            """Apply agent-specific filtering."""
            filters = agent_filters.get(agent_type, {})
            filtered = {"files": {}, "memory": {}}
            
            # Filter files
            for path, content in context["files"].items():
                # Check excludes first
                if any(path.endswith(exc) for exc in filters.get("exclude_patterns", [])):
                    continue
                    
                # Check includes
                patterns = filters.get("file_patterns", ["*"])
                if "*" in patterns or any(
                    path.endswith(pat.replace("*", "")) or 
                    path.startswith(pat.replace("/*", ""))
                    for pat in patterns
                ):
                    filtered["files"][path] = content
            
            # Filter memory
            for key in filters.get("memory_keys", []):
                if key in context["memory"]:
                    filtered["memory"][key] = context["memory"][key]
            
            return filtered
        
        mock_context_manager.filter_context_for_agent = MagicMock(side_effect=filter_context)
        orchestrator._local_executor._context_manager = mock_context_manager
        orchestrator._local_executor.collect_full_context = AsyncMock(return_value=full_context)
        
        # Test filtering for each agent type
        results = {}
        for agent_type in ["documentation", "qa", "ops", "security"]:
            result, _ = await orchestrator.delegate_to_agent(
                agent_type=agent_type,
                task_description=f"Test context filtering for {agent_type}"
            )
            results[agent_type] = result
        
        # Verify context was filtered appropriately
        filter_calls = mock_context_manager.filter_context_for_agent.call_args_list
        
        # Documentation should only see docs
        doc_call = next(c for c in filter_calls if c[0][0] == "documentation")
        doc_filtered = filter_context("documentation", full_context)
        assert "docs/api.md" in doc_filtered["files"]
        assert ".env" not in doc_filtered["files"]
        
        # QA should see tests and source
        qa_call = next(c for c in filter_calls if c[0][0] == "qa")
        qa_filtered = filter_context("qa", full_context)
        assert "tests/test_main.py" in qa_filtered["files"]
        assert "deploy/k8s.yaml" not in qa_filtered["files"]
        
        # Security should see everything except explicitly excluded
        sec_call = next(c for c in filter_calls if c[0][0] == "security")
        sec_filtered = filter_context("security", full_context)
        assert len(sec_filtered["files"]) == len(full_context["files"])
    
    @pytest.mark.asyncio
    async def test_result_aggregation_pattern(self, orchestrator, mock_agents):
        """Test aggregating results from multiple agents."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Set up message bus
        message_bus = SimpleMessageBus()
        for agent_type, handler in mock_agents.items():
            message_bus.register_handler(agent_type, handler)
        
        orchestrator._local_executor._message_bus = message_bus
        
        # Execute parallel analysis tasks
        analysis_tasks = [
            ("documentation", "Analyze documentation coverage"),
            ("qa", "Analyze test coverage"),
            ("security", "Analyze security posture")
        ]
        
        # Execute tasks concurrently
        tasks = []
        for agent_type, description in analysis_tasks:
            task = orchestrator.delegate_to_agent(
                agent_type=agent_type,
                task_description=description,
                task_id=f"analysis-{agent_type}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        aggregated = {
            "overall_health": "good",
            "scores": {},
            "issues": [],
            "recommendations": []
        }
        
        for (result, _), (agent_type, _) in zip(results, analysis_tasks):
            if agent_type == "qa":
                aggregated["scores"]["quality"] = result["results"]["quality_score"]
            elif agent_type == "security":
                aggregated["scores"]["security"] = result["results"]["security_score"]
                if result["results"]["vulnerabilities"]:
                    aggregated["issues"].extend(result["results"]["vulnerabilities"])
        
        # Calculate overall score
        if aggregated["scores"]:
            aggregated["overall_score"] = sum(aggregated["scores"].values()) / len(aggregated["scores"])
        
        # Verify aggregation
        assert "quality" in aggregated["scores"]
        assert "security" in aggregated["scores"]
        assert aggregated["overall_score"] > 90  # High scores from mocks
        assert len(aggregated["issues"]) == 0  # No vulnerabilities from mock
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery_pattern(self, orchestrator):
        """Test error handling and recovery patterns."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Create message bus with failing handler
        message_bus = SimpleMessageBus()
        
        attempt_count = 0
        async def flaky_handler(request_data):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return {"status": "success", "attempts": attempt_count}
        
        message_bus.register_handler("flaky", flaky_handler)
        orchestrator._local_executor._message_bus = message_bus
        
        # Implement retry pattern
        max_retries = 3
        retry_delay = 0.1
        
        result = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result, return_code = await orchestrator.delegate_to_agent(
                    agent_type="flaky",
                    task_description="Task with retries",
                    task_id=f"retry-{attempt}"
                )
                if return_code == ReturnCode.SUCCESS:
                    break
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise
        
        # Verify recovery succeeded
        assert result is not None
        assert result["success"] is True
        assert result["results"]["attempts"] == 3
    
    @pytest.mark.asyncio
    async def test_performance_optimization_patterns(self, orchestrator, mock_agents):
        """Test performance optimization patterns."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Set up message bus with mock handlers
        message_bus = SimpleMessageBus()
        for agent_type, handler in mock_agents.items():
            message_bus.register_handler(agent_type, handler)
        
        orchestrator._local_executor._message_bus = message_bus
        
        # Pattern 1: Batch similar operations
        batch_start = time.perf_counter()
        
        # Execute multiple documentation tasks as a batch
        doc_tasks = [
            "Update API documentation",
            "Update user guide",
            "Update changelog"
        ]
        
        batch_results = []
        for task in doc_tasks:
            result, _ = await orchestrator.delegate_to_agent(
                agent_type="documentation",
                task_description=task,
                batch_mode=True  # Hint for optimization
            )
            batch_results.append(result)
        
        batch_time = (time.perf_counter() - batch_start) * 1000
        
        # Pattern 2: Pipeline with minimal context
        pipeline_start = time.perf_counter()
        
        # Use minimal context transfer between stages
        minimal_context = {"version": "1.0.0", "ready": True}
        
        # Quick validation pipeline
        for agent in ["qa", "security"]:
            result, _ = await orchestrator.delegate_to_agent(
                agent_type=agent,
                task_description=f"Quick {agent} check",
                context=minimal_context,
                quick_mode=True
            )
        
        pipeline_time = (time.perf_counter() - pipeline_start) * 1000
        
        # Pattern 3: Parallel independent tasks
        parallel_start = time.perf_counter()
        
        independent_tasks = [
            ("documentation", "Generate API docs"),
            ("qa", "Run unit tests"),
            ("security", "Scan dependencies")
        ]
        
        parallel_tasks = []
        for agent_type, description in independent_tasks:
            task = orchestrator.delegate_to_agent(
                agent_type=agent_type,
                task_description=description
            )
            parallel_tasks.append(task)
        
        parallel_results = await asyncio.gather(*parallel_tasks)
        parallel_time = (time.perf_counter() - parallel_start) * 1000
        
        # Verify performance characteristics
        assert batch_time < 100  # Batch should be fast
        assert pipeline_time < 50  # Pipeline with minimal context should be very fast
        assert parallel_time < 50  # Parallel execution should be fastest
        
        # Verify all operations succeeded
        assert all(r["success"] for r in batch_results)
        assert all(r[0]["success"] for r in parallel_results)
    
    @pytest.mark.asyncio
    async def test_conditional_workflow_pattern(self, orchestrator, mock_agents):
        """Test conditional workflow execution patterns."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Set up message bus with conditional logic
        message_bus = SimpleMessageBus()
        
        # QA handler with conditional results
        async def conditional_qa_handler(request_data):
            if request_data.get("strict_mode"):
                return {
                    "test_results": {"passed": 40, "failed": 2},
                    "quality_score": 85,
                    "ready_for_release": False,
                    "blocking_issues": ["Test coverage below 90%"]
                }
            return {
                "test_results": {"passed": 42, "failed": 0},
                "quality_score": 98.5,
                "ready_for_release": True
            }
        
        message_bus.register_handler("qa", conditional_qa_handler)
        for agent_type, handler in mock_agents.items():
            if agent_type != "qa":
                message_bus.register_handler(agent_type, handler)
        
        orchestrator._local_executor._message_bus = message_bus
        
        # Test workflow with condition
        qa_result, _ = await orchestrator.delegate_to_agent(
            agent_type="qa",
            task_description="Validate with strict mode",
            strict_mode=True
        )
        
        # Conditional execution based on QA results
        if qa_result["results"]["ready_for_release"]:
            # Proceed with deployment
            deploy_result, _ = await orchestrator.delegate_to_agent(
                agent_type="ops",
                task_description="Deploy to production"
            )
        else:
            # Execute remediation workflow
            # 1. Get more details from QA
            detail_result, _ = await orchestrator.delegate_to_agent(
                agent_type="qa",
                task_description="Provide detailed failure analysis",
                context={"issues": qa_result["results"]["blocking_issues"]}
            )
            
            # 2. Create documentation for fixes
            doc_result, _ = await orchestrator.delegate_to_agent(
                agent_type="documentation",
                task_description="Document required fixes",
                context={"blocking_issues": qa_result["results"]["blocking_issues"]}
            )
        
        # Verify conditional path was taken
        assert not qa_result["results"]["ready_for_release"]
        assert "blocking_issues" in qa_result["results"]
        
        # Verify remediation workflow executed
        assert doc_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_hierarchical_delegation_pattern(self, orchestrator):
        """Test hierarchical agent delegation (PM → sub-agents)."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Track delegation hierarchy
        delegation_tree = {
            "pm": {
                "task": "Coordinate release",
                "delegated_to": []
            }
        }
        
        # Create PM handler that delegates to other agents
        async def pm_handler(request_data):
            # PM delegates to multiple agents
            sub_tasks = [
                {"agent": "documentation", "task": "Prepare release notes"},
                {"agent": "qa", "task": "Final validation"},
                {"agent": "version_control", "task": "Tag release"}
            ]
            
            delegation_tree["pm"]["delegated_to"] = sub_tasks
            
            return {
                "coordination_complete": True,
                "sub_tasks": sub_tasks,
                "release_ready": True
            }
        
        # Set up message bus
        message_bus = SimpleMessageBus()
        message_bus.register_handler("pm", pm_handler)
        
        orchestrator._local_executor._message_bus = message_bus
        
        # Execute PM orchestration
        pm_result, _ = await orchestrator.delegate_to_agent(
            agent_type="pm",
            task_description="Coordinate release v1.0.0",
            task_id="pm-release-001"
        )
        
        # Verify hierarchical delegation
        assert pm_result["success"] is True
        assert pm_result["results"]["coordination_complete"] is True
        assert len(pm_result["results"]["sub_tasks"]) == 3
        
        # Verify delegation tree structure
        assert len(delegation_tree["pm"]["delegated_to"]) == 3
        agent_types = [t["agent"] for t in delegation_tree["pm"]["delegated_to"]]
        assert "documentation" in agent_types
        assert "qa" in agent_types
        assert "version_control" in agent_types