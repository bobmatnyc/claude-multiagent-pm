#!/usr/bin/env python3
"""
Test Agent Memory Integration
============================

Comprehensive test suite for validating memory-enhanced agent operations
in the Claude PM Framework. Tests memory triggers, agent coordination,
and three-command system integration.

Test Categories:
- Memory-enhanced agent wrapper functionality
- Agent memory trigger creation and recall
- Agent coordination memory patterns
- Three-command memory integration
- Performance and reliability validation
"""

import asyncio
import json
import logging
import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, AsyncMock, patch

# Test imports
from claude_pm.agents.memory_enhanced_agents import (
    MemoryEnhancedAgent,
    AgentMemoryPattern,
    AgentMemoryPatternRegistry,
    AgentMemoryContext
)
from claude_pm.services.agent_memory_integration import (
    AgentMemoryCoordinator,
    AgentHandoffManager,
    WorkflowMemoryTracker,
    ThreeCommandMemoryIntegration
)
from claude_pm.services.agent_coordination_memory import (
    CoordinationMemoryManager,
    HandoffPatternAnalyzer,
    CoordinationLearningEngine,
    PerformanceOptimizer
)
from claude_pm.services.three_command_memory_integration import (
    ThreeCommandMemoryIntegration as ThreeCommandIntegration,
    CommandWorkflowState,
    CommandPhase,
    QualityGate
)
from claude_pm.services.memory.memory_trigger_service import MemoryTriggerService
from claude_pm.services.memory.interfaces.models import MemoryCategory, MemoryItem
from claude_pm.core.base_agent import BaseAgent


# Mock agent for testing
class MockAgent(BaseAgent):
    """Mock agent for testing memory integration."""
    
    def __init__(self, agent_id: str = "test-agent", agent_type: str = "test"):
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=["test_capability"],
            config={}
        )
        self.execute_calls = []
        self.execute_results = []
    
    async def _initialize(self):
        pass
    
    async def _cleanup(self):
        pass
    
    async def _execute_operation(self, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        self.execute_calls.append({"operation": operation, "context": context, "kwargs": kwargs})
        return self.execute_results.pop(0) if self.execute_results else {"success": True}
    
    def set_next_result(self, result: Dict[str, Any]):
        """Set next result for execute method."""
        self.execute_results.append(result)


class TestMemoryEnhancedAgent:
    """Test memory-enhanced agent wrapper functionality."""
    
    @pytest.fixture
    async def memory_service(self):
        """Create mock memory service."""
        service = Mock(spec=MemoryTriggerService)
        service.get_memory_service.return_value = Mock()
        service.get_trigger_orchestrator.return_value = Mock()
        service.get_trigger_orchestrator.return_value.process_trigger = AsyncMock()
        return service
    
    @pytest.fixture
    async def mock_agent(self):
        """Create mock agent."""
        return MockAgent()
    
    @pytest.fixture
    async def enhanced_agent(self, mock_agent, memory_service):
        """Create memory-enhanced agent."""
        return MemoryEnhancedAgent(mock_agent, memory_service)
    
    @pytest.mark.asyncio
    async def test_memory_enhanced_agent_creation(self, enhanced_agent, mock_agent, memory_service):
        """Test memory-enhanced agent creation."""
        assert enhanced_agent.wrapped_agent == mock_agent
        assert enhanced_agent.memory_service == memory_service
        assert enhanced_agent.memory_enabled == True
        assert enhanced_agent.auto_recall_enabled == True
    
    @pytest.mark.asyncio
    async def test_execute_with_memory_success(self, enhanced_agent):
        """Test successful execution with memory integration."""
        # Set up mock agent result
        enhanced_agent.wrapped_agent.set_next_result({"success": True, "result": "test_result"})
        
        # Mock memory service
        enhanced_agent.memory_service.get_memory_service.return_value.search_memories = AsyncMock(return_value=[])
        
        # Execute operation
        result = await enhanced_agent.execute_with_memory(
            operation="test_operation",
            context={"project_name": "test_project"}
        )
        
        # Verify result
        assert result["success"] == True
        assert result["result"] == "test_result"
        assert "memory_context" in result
        assert result["memory_context"]["memory_enhanced"] == True
        
        # Verify memory trigger was called
        enhanced_agent.memory_service.get_trigger_orchestrator.return_value.process_trigger.assert_called()
    
    @pytest.mark.asyncio
    async def test_memory_recall_before_operation(self, enhanced_agent):
        """Test memory recall before operation execution."""
        # Create mock memories
        mock_memories = [
            MemoryItem(
                id="mem1",
                content="Previous test operation",
                category=MemoryCategory.WORKFLOW,
                metadata={"success": True, "execution_time": 30.0}
            )
        ]
        
        enhanced_agent.memory_service.get_memory_service.return_value.search_memories = AsyncMock(return_value=mock_memories)
        enhanced_agent.wrapped_agent.set_next_result({"success": True})
        
        # Execute operation
        result = await enhanced_agent.execute_with_memory(
            operation="test_operation",
            context={"project_name": "test_project"}
        )
        
        # Verify memory was recalled
        enhanced_agent.memory_service.get_memory_service.return_value.search_memories.assert_called()
        
        # Verify memory context was enhanced
        assert "memory_context" in result
        assert result["memory_context"]["related_memories_count"] == 1
    
    @pytest.mark.asyncio
    async def test_memory_pattern_registry(self):
        """Test agent memory pattern registry."""
        registry = AgentMemoryPatternRegistry()
        
        # Test getting documentation agent patterns
        doc_patterns = registry.get_patterns_by_agent("documentation")
        assert "scan_project" in doc_patterns
        assert "validate_documentation" in doc_patterns
        
        # Test getting QA agent patterns
        qa_patterns = registry.get_patterns_by_agent("qa")
        assert "test_execution" in qa_patterns
        assert "browser_testing" in qa_patterns
        
        # Test recall triggers
        recall_patterns = registry.get_recall_patterns("pre_push_validation")
        assert len(recall_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_error_memory_creation(self, enhanced_agent):
        """Test memory creation for failed operations."""
        # Mock error in wrapped agent
        enhanced_agent.wrapped_agent.set_next_result({"success": False})
        
        # Mock search to return empty
        enhanced_agent.memory_service.get_memory_service.return_value.search_memories = AsyncMock(return_value=[])
        
        with pytest.raises(Exception):
            # This should raise an exception and create error memory
            await enhanced_agent.execute_with_memory(
                operation="failing_operation",
                context={"project_name": "test_project"}
            )
        
        # Verify error memory trigger was called
        enhanced_agent.memory_service.get_trigger_orchestrator.return_value.process_trigger.assert_called()


class TestAgentMemoryCoordinator:
    """Test agent memory coordination functionality."""
    
    @pytest.fixture
    async def memory_service(self):
        """Create mock memory service."""
        service = Mock(spec=MemoryTriggerService)
        service.initialize = AsyncMock()
        service.cleanup = AsyncMock()
        return service
    
    @pytest.fixture
    async def coordinator(self, memory_service):
        """Create agent memory coordinator."""
        coordinator = AgentMemoryCoordinator(memory_service)
        await coordinator.initialize()
        return coordinator
    
    @pytest.mark.asyncio
    async def test_coordinator_initialization(self, coordinator):
        """Test coordinator initialization."""
        assert coordinator.memory_service is not None
        assert coordinator.handoff_manager is not None
        assert coordinator.workflow_tracker is not None
        assert coordinator.three_command_integration is not None
    
    @pytest.mark.asyncio
    async def test_agent_enhancement(self, coordinator):
        """Test agent enhancement with memory capabilities."""
        mock_agent = MockAgent()
        
        enhanced_agent = await coordinator.enhance_agent_with_memory(mock_agent)
        
        assert isinstance(enhanced_agent, MemoryEnhancedAgent)
        assert enhanced_agent.wrapped_agent == mock_agent
        assert mock_agent.agent_id in coordinator.memory_enhanced_agents
    
    @pytest.mark.asyncio
    async def test_agent_handoff_coordination(self, coordinator):
        """Test agent handoff coordination."""
        # Mock handoff manager
        coordinator.handoff_manager.initiate_handoff = AsyncMock(return_value="handoff_123")
        coordinator.handoff_manager.complete_handoff = AsyncMock(return_value=True)
        
        # Initiate handoff
        handoff_id = await coordinator.coordinate_agent_handoff(
            source_agent_id="doc_agent",
            target_agent_id="qa_agent",
            project_name="test_project",
            workflow_type="push",
            handoff_context={"validation_results": "passed"}
        )
        
        assert handoff_id == "handoff_123"
        coordinator.handoff_manager.initiate_handoff.assert_called_once()
        
        # Complete handoff
        success = await coordinator.complete_agent_handoff(
            handoff_id=handoff_id,
            success=True,
            result_context={"qa_results": "passed"}
        )
        
        assert success == True
        coordinator.handoff_manager.complete_handoff.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_tracking(self, coordinator):
        """Test workflow memory tracking."""
        # Mock workflow tracker
        coordinator.workflow_tracker.start_workflow = AsyncMock(return_value="workflow_456")
        coordinator.workflow_tracker.complete_workflow = AsyncMock(return_value=True)
        
        # Start workflow
        workflow_id = await coordinator.start_workflow_tracking(
            workflow_type="push",
            project_name="test_project",
            agents_involved=["documentation", "qa", "ops"],
            workflow_context={"branch": "main"}
        )
        
        assert workflow_id == "workflow_456"
        coordinator.workflow_tracker.start_workflow.assert_called_once()
        
        # Complete workflow
        success = await coordinator.complete_workflow_tracking(
            workflow_id=workflow_id,
            success=True,
            quality_gates=["documentation", "testing"],
            performance_metrics={"duration": 120.5}
        )
        
        assert success == True
        coordinator.workflow_tracker.complete_workflow.assert_called_once()


class TestThreeCommandMemoryIntegration:
    """Test three-command memory integration."""
    
    @pytest.fixture
    async def memory_service(self):
        """Create mock memory service."""
        service = Mock(spec=MemoryTriggerService)
        service.get_trigger_orchestrator.return_value = Mock()
        service.get_trigger_orchestrator.return_value.process_trigger = AsyncMock()
        return service
    
    @pytest.fixture
    async def three_command_integration(self, memory_service):
        """Create three command integration."""
        return ThreeCommandIntegration(memory_service)
    
    @pytest.mark.asyncio
    async def test_push_command_workflow(self, three_command_integration):
        """Test push command workflow tracking."""
        # Start push workflow
        workflow_id = await three_command_integration.start_command_workflow(
            command="push",
            project_name="test_project",
            context={"branch": "feature/test"}
        )
        
        assert workflow_id.startswith("push_test_project_")
        assert workflow_id in three_command_integration.active_workflows
        
        # Get workflow state
        workflow = three_command_integration.active_workflows[workflow_id]
        assert workflow.command == "push"
        assert workflow.project_name == "test_project"
        assert workflow.phase == CommandPhase.INITIALIZATION
        assert workflow.agents_sequence == ["documentation", "qa", "ops"]
    
    @pytest.mark.asyncio
    async def test_workflow_phase_advancement(self, three_command_integration):
        """Test workflow phase advancement."""
        # Start workflow
        workflow_id = await three_command_integration.start_command_workflow(
            command="deploy",
            project_name="test_project"
        )
        
        # Advance to next phase
        success = await three_command_integration.advance_workflow_phase(
            workflow_id=workflow_id,
            phase=CommandPhase.OPERATIONS,
            agent_result={"success": True, "deployment_status": "ready"}
        )
        
        assert success == True
        
        # Verify phase was updated
        workflow = three_command_integration.active_workflows[workflow_id]
        assert workflow.phase == CommandPhase.OPERATIONS
        assert workflow.context["deployment_status"] == "ready"
    
    @pytest.mark.asyncio
    async def test_workflow_completion(self, three_command_integration):
        """Test workflow completion and memory creation."""
        # Start workflow
        workflow_id = await three_command_integration.start_command_workflow(
            command="publish",
            project_name="test_project"
        )
        
        # Complete workflow
        summary = await three_command_integration.complete_command_workflow(
            workflow_id=workflow_id,
            success=True,
            final_result={"published_packages": ["test-package@1.0.0"]}
        )
        
        assert summary["success"] == True
        assert summary["command"] == "publish"
        assert summary["project_name"] == "test_project"
        assert "duration" in summary
        assert "performance_metrics" in summary
        
        # Verify workflow was removed from active
        assert workflow_id not in three_command_integration.active_workflows


class TestCoordinationMemoryManager:
    """Test coordination memory management."""
    
    @pytest.fixture
    async def memory_service(self):
        """Create mock memory service."""
        service = Mock(spec=MemoryTriggerService)
        service.get_memory_service.return_value = Mock()
        service.get_memory_service.return_value.search_memories = AsyncMock(return_value=[])
        service.get_trigger_orchestrator.return_value = Mock()
        service.get_trigger_orchestrator.return_value.process_trigger = AsyncMock()
        return service
    
    @pytest.fixture
    async def coordination_manager(self, memory_service):
        """Create coordination memory manager."""
        return CoordinationMemoryManager(memory_service)
    
    @pytest.mark.asyncio
    async def test_handoff_analysis(self, coordination_manager):
        """Test agent handoff analysis."""
        # Mock memory data
        mock_memories = [
            MemoryItem(
                id="handoff1",
                content="Handoff from doc to qa",
                category=MemoryCategory.WORKFLOW,
                metadata={
                    "success": True,
                    "duration": 45.0,
                    "timestamp": datetime.now().isoformat(),
                    "source_agent": "documentation",
                    "target_agent": "qa"
                }
            )
        ]
        
        coordination_manager.memory_service.get_memory_service.return_value.search_memories = AsyncMock(return_value=mock_memories)
        
        # Analyze handoff
        analysis = await coordination_manager.analyze_coordination_handoff(
            source_agent="documentation",
            target_agent="qa",
            project_name="test_project"
        )
        
        assert analysis.source_agent == "documentation"
        assert analysis.target_agent == "qa"
        assert analysis.handoff_quality is not None
        assert analysis.duration > 0
    
    @pytest.mark.asyncio
    async def test_pattern_learning(self, coordination_manager):
        """Test coordination pattern learning."""
        # Define coordination context and outcome
        coordination_context = {
            "agents_involved": ["documentation", "qa", "ops"],
            "project_name": "test_project",
            "workflow_type": "push"
        }
        
        outcome = {
            "success": True,
            "duration": 180.0,
            "context_preservation": 0.85,
            "performance_impact": 0.7,
            "success_factors": ["good_handoffs", "clear_context"],
            "failure_modes": []
        }
        
        # Learn pattern
        pattern = await coordination_manager.learn_coordination_pattern(
            coordination_context, outcome
        )
        
        assert pattern is not None
        assert pattern.agents_involved == ["documentation", "qa", "ops"]
        assert pattern.success_rate == 1.0
        assert pattern.average_duration == 180.0
    
    @pytest.mark.asyncio
    async def test_sequence_optimization(self, coordination_manager):
        """Test agent sequence optimization."""
        agents_sequence = ["documentation", "qa", "ops"]
        
        optimization = await coordination_manager.optimize_coordination_sequence(
            agents_sequence=agents_sequence,
            project_name="test_project",
            context={"workflow_type": "push"}
        )
        
        assert "original_sequence" in optimization
        assert optimization["original_sequence"] == agents_sequence
        assert "optimizations" in optimization
        assert "expected_improvements" in optimization


class TestPerformanceAndReliability:
    """Test performance and reliability of memory integration."""
    
    @pytest.mark.asyncio
    async def test_memory_integration_performance(self):
        """Test performance of memory-enhanced operations."""
        # Create memory service mock
        memory_service = Mock(spec=MemoryTriggerService)
        memory_service.get_memory_service.return_value = Mock()
        memory_service.get_memory_service.return_value.search_memories = AsyncMock(return_value=[])
        memory_service.get_trigger_orchestrator.return_value = Mock()
        memory_service.get_trigger_orchestrator.return_value.process_trigger = AsyncMock()
        
        # Create enhanced agent
        mock_agent = MockAgent()
        enhanced_agent = MemoryEnhancedAgent(mock_agent, memory_service)
        
        # Measure performance of multiple operations
        start_time = time.time()
        
        for i in range(10):
            mock_agent.set_next_result({"success": True, "iteration": i})
            result = await enhanced_agent.execute_with_memory(
                operation=f"test_operation_{i}",
                context={"project_name": "performance_test"}
            )
            assert result["success"] == True
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance should be reasonable (< 5 seconds for 10 operations)
        assert total_time < 5.0
        
        # Verify all memory triggers were called
        assert memory_service.get_trigger_orchestrator.return_value.process_trigger.call_count == 10
    
    @pytest.mark.asyncio
    async def test_memory_service_failure_handling(self):
        """Test handling of memory service failures."""
        # Create memory service that raises exceptions
        memory_service = Mock(spec=MemoryTriggerService)
        memory_service.get_memory_service.side_effect = Exception("Memory service error")
        
        # Create enhanced agent
        mock_agent = MockAgent()
        enhanced_agent = MemoryEnhancedAgent(mock_agent, memory_service)
        mock_agent.set_next_result({"success": True})
        
        # Operation should still succeed even with memory service failure
        result = await enhanced_agent.execute_with_memory(
            operation="test_operation",
            context={"project_name": "test_project"}
        )
        
        # Operation should succeed despite memory failure
        assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """Test concurrent memory operations."""
        # Create memory service mock
        memory_service = Mock(spec=MemoryTriggerService)
        memory_service.get_memory_service.return_value = Mock()
        memory_service.get_memory_service.return_value.search_memories = AsyncMock(return_value=[])
        memory_service.get_trigger_orchestrator.return_value = Mock()
        memory_service.get_trigger_orchestrator.return_value.process_trigger = AsyncMock()
        
        # Create multiple enhanced agents
        agents = []
        for i in range(5):
            mock_agent = MockAgent(agent_id=f"agent_{i}", agent_type=f"type_{i}")
            enhanced_agent = MemoryEnhancedAgent(mock_agent, memory_service)
            agents.append((mock_agent, enhanced_agent))
        
        # Execute concurrent operations
        async def execute_agent_operation(mock_agent, enhanced_agent, operation_id):
            mock_agent.set_next_result({"success": True, "operation_id": operation_id})
            return await enhanced_agent.execute_with_memory(
                operation=f"concurrent_operation_{operation_id}",
                context={"project_name": "concurrent_test"}
            )
        
        # Run operations concurrently
        tasks = []
        for i, (mock_agent, enhanced_agent) in enumerate(agents):
            task = execute_agent_operation(mock_agent, enhanced_agent, i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        for i, result in enumerate(results):
            assert result["success"] == True
            assert result["operation_id"] == i
        
        # Verify memory triggers were called for all operations
        assert memory_service.get_trigger_orchestrator.return_value.process_trigger.call_count == 5


# Integration test runner
async def run_integration_tests():
    """Run comprehensive integration tests."""
    
    print("Starting Agent Memory Integration Tests...")
    print("=" * 50)
    
    # Test memory-enhanced agent wrapper
    print("\n1. Testing Memory-Enhanced Agent Wrapper...")
    memory_service = Mock(spec=MemoryTriggerService)
    memory_service.get_memory_service.return_value = Mock()
    memory_service.get_memory_service.return_value.search_memories = AsyncMock(return_value=[])
    memory_service.get_trigger_orchestrator.return_value = Mock()
    memory_service.get_trigger_orchestrator.return_value.process_trigger = AsyncMock()
    
    mock_agent = MockAgent()
    enhanced_agent = MemoryEnhancedAgent(mock_agent, memory_service)
    mock_agent.set_next_result({"success": True, "test": "passed"})
    
    result = await enhanced_agent.execute_with_memory(
        operation="test_operation",
        context={"project_name": "integration_test"}
    )
    
    assert result["success"] == True
    assert "memory_context" in result
    print("✓ Memory-enhanced agent wrapper working correctly")
    
    # Test agent coordination
    print("\n2. Testing Agent Coordination...")
    coordinator = AgentMemoryCoordinator(memory_service)
    await coordinator.initialize()
    
    # Mock the underlying managers
    coordinator.handoff_manager.initiate_handoff = AsyncMock(return_value="test_handoff")
    coordinator.workflow_tracker.start_workflow = AsyncMock(return_value="test_workflow")
    
    handoff_id = await coordinator.coordinate_agent_handoff(
        source_agent_id="test_agent",
        target_agent_id="test_target", 
        project_name="integration_test",
        workflow_type="test",
        handoff_context={}
    )
    
    assert handoff_id == "test_handoff"
    print("✓ Agent coordination working correctly")
    
    # Test three-command integration
    print("\n3. Testing Three-Command Integration...")
    three_command = ThreeCommandIntegration(memory_service)
    
    workflow_id = await three_command.start_command_workflow(
        command="push",
        project_name="integration_test",
        context={"test": True}
    )
    
    assert workflow_id in three_command.active_workflows
    print("✓ Three-command integration working correctly")
    
    # Test coordination memory
    print("\n4. Testing Coordination Memory...")
    coord_manager = CoordinationMemoryManager(memory_service)
    
    analysis = await coord_manager.analyze_coordination_handoff(
        source_agent="test_source",
        target_agent="test_target",
        project_name="integration_test"
    )
    
    assert analysis.source_agent == "test_source"
    print("✓ Coordination memory working correctly")
    
    print("\n" + "=" * 50)
    print("All Agent Memory Integration Tests Passed! ✓")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    return {
        "success": True,
        "tests_run": 4,
        "timestamp": datetime.now().isoformat(),
        "components_tested": [
            "memory_enhanced_agents",
            "agent_memory_integration", 
            "three_command_memory_integration",
            "agent_coordination_memory"
        ]
    }


if __name__ == "__main__":
    # Run integration tests
    result = asyncio.run(run_integration_tests())
    print(f"\nTest Results: {json.dumps(result, indent=2)}")