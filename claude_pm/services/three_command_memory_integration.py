"""
Three Command Memory Integration
===============================

Memory integration for the Claude PM Framework's three intelligent shortcut commands:
- push: Git integration & quality assurance
- deploy: Local deployment operations
- publish: Package publication pipeline

This module provides memory-enhanced workflows for these commands, creating
and recalling memories to improve agent coordination and decision-making.

Key Features:
- Memory triggers for command workflow phases
- Agent handoff memory tracking
- Quality gate memory integration
- Performance pattern analysis
- Failure pattern detection and learning
- Multi-agent coordination memory
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from enum import Enum

from .memory.memory_trigger_service import MemoryTriggerService
from .memory.trigger_orchestrator import TriggerEvent, TriggerResult
from .memory.trigger_types import TriggerType, TriggerPriority
from .memory.interfaces.models import MemoryCategory
from .agent_memory_integration import AgentMemoryCoordinator


class CommandPhase(Enum):
    """Phases of three-command workflows."""

    INITIALIZATION = "initialization"
    DOCUMENTATION_VALIDATION = "documentation_validation"
    QUALITY_ASSURANCE = "quality_assurance"
    OPERATIONS = "operations"
    BRANCH_MANAGEMENT = "branch_management"
    DEPLOYMENT = "deployment"
    PUBLICATION = "publication"
    CLEANUP = "cleanup"
    COMPLETION = "completion"


class QualityGate(Enum):
    """Quality gates for command workflows."""

    DOCUMENTATION_HEALTH = "documentation_health"
    TEST_EXECUTION = "test_execution"
    CODE_QUALITY = "code_quality"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_CHECK = "performance_check"
    DEPLOYMENT_VALIDATION = "deployment_validation"
    PUBLICATION_READINESS = "publication_readiness"


@dataclass
class CommandWorkflowState:
    """State tracking for command workflows."""

    workflow_id: str
    command: str
    project_name: str
    phase: CommandPhase
    agents_sequence: List[str]
    current_agent_index: int = 0
    start_time: float = field(default_factory=time.time)
    completion_time: Optional[float] = None
    success: bool = False
    quality_gates_passed: List[QualityGate] = field(default_factory=list)
    quality_gates_failed: List[QualityGate] = field(default_factory=list)
    agent_handoffs: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    memory_insights: Dict[str, Any] = field(default_factory=dict)

    @property
    def current_agent(self) -> Optional[str]:
        """Get current agent in sequence."""
        if 0 <= self.current_agent_index < len(self.agents_sequence):
            return self.agents_sequence[self.current_agent_index]
        return None

    @property
    def duration(self) -> float:
        """Get workflow duration."""
        end_time = self.completion_time or time.time()
        return end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "command": self.command,
            "project_name": self.project_name,
            "phase": self.phase.value,
            "agents_sequence": self.agents_sequence,
            "current_agent_index": self.current_agent_index,
            "current_agent": self.current_agent,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "success": self.success,
            "duration": self.duration,
            "quality_gates_passed": [qg.value for qg in self.quality_gates_passed],
            "quality_gates_failed": [qg.value for qg in self.quality_gates_failed],
            "agent_handoffs": self.agent_handoffs,
            "context": self.context,
            "performance_metrics": self.performance_metrics,
            "error_history": self.error_history,
            "memory_insights": self.memory_insights,
        }


class ThreeCommandMemoryIntegration:
    """
    Memory integration for three-command workflows.

    Provides comprehensive memory integration for push, deploy, and publish
    commands with agent coordination, quality gates, and performance tracking.
    """

    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)

        # Active workflows
        self.active_workflows: Dict[str, CommandWorkflowState] = {}

        # Command configurations
        self.command_configs = {
            "push": {
                "agents_sequence": ["documentation", "qa", "ops"],
                "quality_gates": [
                    QualityGate.DOCUMENTATION_HEALTH,
                    QualityGate.TEST_EXECUTION,
                    QualityGate.CODE_QUALITY,
                ],
                "branch_management": True,
                "memory_importance": 0.9,
            },
            "deploy": {
                "agents_sequence": ["ops", "qa"],
                "quality_gates": [QualityGate.DEPLOYMENT_VALIDATION, QualityGate.PERFORMANCE_CHECK],
                "branch_management": False,
                "memory_importance": 0.8,
            },
            "publish": {
                "agents_sequence": ["ops", "documentation", "ops"],
                "quality_gates": [
                    QualityGate.PUBLICATION_READINESS,
                    QualityGate.DOCUMENTATION_HEALTH,
                    QualityGate.SECURITY_SCAN,
                ],
                "branch_management": True,
                "memory_importance": 0.9,
            },
        }

        # Performance tracking
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        self.success_rates: Dict[str, float] = {}

        self.logger.info("Three Command Memory Integration initialized")

    async def start_command_workflow(
        self, command: str, project_name: str, context: Dict[str, Any] = None
    ) -> str:
        """
        Start memory-enhanced command workflow.

        Args:
            command: Command type (push, deploy, publish)
            project_name: Project name
            context: Additional context

        Returns:
            Workflow ID for tracking
        """
        if command not in self.command_configs:
            raise ValueError(f"Unknown command: {command}")

        context = context or {}
        workflow_id = f"{command}_{project_name}_{int(time.time())}"

        # Get command configuration
        config = self.command_configs[command]

        # Recall relevant memories for command
        memory_insights = await self._recall_command_memories(command, project_name)

        # Create workflow state
        workflow = CommandWorkflowState(
            workflow_id=workflow_id,
            command=command,
            project_name=project_name,
            phase=CommandPhase.INITIALIZATION,
            agents_sequence=config["agents_sequence"],
            context=context,
            memory_insights=memory_insights,
        )

        # Store active workflow
        self.active_workflows[workflow_id] = workflow

        # Create workflow start memory
        await self._create_workflow_memory(workflow, "start")

        self.logger.info(f"Started {command} workflow for {project_name}: {workflow_id}")
        return workflow_id

    async def advance_workflow_phase(
        self,
        workflow_id: str,
        phase: CommandPhase,
        agent_result: Optional[Dict[str, Any]] = None,
        quality_gates_result: Optional[Dict[QualityGate, bool]] = None,
    ) -> bool:
        """
        Advance workflow to next phase with memory tracking.

        Args:
            workflow_id: Workflow ID
            phase: New phase
            agent_result: Result from current agent
            quality_gates_result: Quality gates results

        Returns:
            True if phase advance was successful
        """
        if workflow_id not in self.active_workflows:
            self.logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow = self.active_workflows[workflow_id]

        # Update workflow state
        previous_phase = workflow.phase
        workflow.phase = phase

        # Process agent result
        if agent_result:
            workflow.context.update(agent_result)

            # Track agent handoff
            if workflow.current_agent:
                workflow.agent_handoffs.append(workflow.current_agent)

            # Check for errors
            if not agent_result.get("success", True):
                workflow.error_history.append(
                    {
                        "phase": previous_phase.value,
                        "agent": workflow.current_agent,
                        "error": agent_result.get("error", "Unknown error"),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Process quality gates
        if quality_gates_result:
            for gate, passed in quality_gates_result.items():
                if passed:
                    workflow.quality_gates_passed.append(gate)
                else:
                    workflow.quality_gates_failed.append(gate)

        # Advance agent sequence
        if phase in [
            CommandPhase.DOCUMENTATION_VALIDATION,
            CommandPhase.QUALITY_ASSURANCE,
            CommandPhase.OPERATIONS,
        ]:
            workflow.current_agent_index += 1

        # Create phase transition memory
        await self._create_workflow_memory(workflow, "phase_transition")

        self.logger.info(f"Advanced workflow {workflow_id} to phase: {phase.value}")
        return True

    async def complete_command_workflow(
        self, workflow_id: str, success: bool, final_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Complete command workflow with memory creation.

        Args:
            workflow_id: Workflow ID
            success: Whether workflow was successful
            final_result: Final workflow result

        Returns:
            Workflow completion summary
        """
        if workflow_id not in self.active_workflows:
            self.logger.error(f"Workflow not found: {workflow_id}")
            return {"success": False, "error": "Workflow not found"}

        workflow = self.active_workflows[workflow_id]

        # Update workflow completion
        workflow.phase = CommandPhase.COMPLETION
        workflow.success = success
        workflow.completion_time = time.time()

        if final_result:
            workflow.context.update(final_result)

        # Calculate performance metrics
        workflow.performance_metrics = self._calculate_performance_metrics(workflow)

        # Create completion memory
        await self._create_workflow_memory(workflow, "completion")

        # Update success rates
        self._update_success_rates(workflow.command, success)

        # Create workflow summary
        summary = {
            "workflow_id": workflow_id,
            "command": workflow.command,
            "project_name": workflow.project_name,
            "success": success,
            "duration": workflow.duration,
            "agents_involved": len(workflow.agents_sequence),
            "quality_gates_passed": len(workflow.quality_gates_passed),
            "quality_gates_failed": len(workflow.quality_gates_failed),
            "agent_handoffs": len(workflow.agent_handoffs),
            "performance_metrics": workflow.performance_metrics,
            "error_count": len(workflow.error_history),
            "memory_insights": workflow.memory_insights,
        }

        # Remove from active workflows
        del self.active_workflows[workflow_id]

        self.logger.info(
            f"Completed {workflow.command} workflow: {workflow_id} (success: {success})"
        )
        return summary

    async def _recall_command_memories(self, command: str, project_name: str) -> Dict[str, Any]:
        """Recall relevant memories for command."""
        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return {}

            # Search for similar command executions
            search_query = f"command:{command} project:{project_name}"

            memories = await memory_service.search_memories(
                query=search_query,
                filters={"command": command, "project_name": project_name},
                limit=10,
            )

            if not memories:
                return {"historical_executions": 0, "recommendations": []}

            # Analyze memory patterns
            success_count = sum(1 for m in memories if m.metadata.get("success", False))
            success_rate = success_count / len(memories)

            # Analyze common failures
            failures = [m for m in memories if not m.metadata.get("success", False)]
            common_failures = self._analyze_failure_patterns(failures)

            # Analyze performance trends
            durations = [m.metadata.get("duration", 0) for m in memories]
            avg_duration = sum(durations) / len(durations) if durations else 0

            # Generate recommendations
            recommendations = []
            if success_rate < 0.8:
                recommendations.append(
                    f"Command has {success_rate:.1%} success rate - review common issues"
                )
            if avg_duration > 300:  # 5 minutes
                recommendations.append(
                    f"Average duration is {avg_duration:.1f}s - consider optimization"
                )
            if common_failures:
                recommendations.append("Review common failure patterns before proceeding")

            return {
                "historical_executions": len(memories),
                "success_rate": success_rate,
                "average_duration": avg_duration,
                "common_failures": common_failures,
                "recommendations": recommendations,
            }

        except Exception as e:
            self.logger.error(f"Failed to recall command memories: {e}")
            return {}

    def _analyze_failure_patterns(self, failures: List[Any]) -> List[str]:
        """Analyze common failure patterns."""
        patterns = []

        # Extract error types
        error_types = []
        for failure in failures:
            error_history = failure.metadata.get("error_history", [])
            for error in error_history:
                error_types.append(error.get("error", "").lower())

        # Find common patterns
        if error_types:
            from collections import Counter

            common_errors = Counter(error_types).most_common(3)
            patterns.extend([error for error, count in common_errors])

        return patterns

    def _calculate_performance_metrics(self, workflow: CommandWorkflowState) -> Dict[str, float]:
        """Calculate performance metrics for workflow."""
        metrics = {}

        # Basic metrics
        metrics["duration"] = workflow.duration
        metrics["success_rate"] = 1.0 if workflow.success else 0.0
        metrics["quality_gates_rate"] = (
            len(workflow.quality_gates_passed)
            / (len(workflow.quality_gates_passed) + len(workflow.quality_gates_failed))
            if (workflow.quality_gates_passed or workflow.quality_gates_failed)
            else 1.0
        )

        # Agent handoff efficiency
        expected_handoffs = len(workflow.agents_sequence) - 1
        actual_handoffs = len(workflow.agent_handoffs)
        metrics["handoff_efficiency"] = (
            expected_handoffs / actual_handoffs if actual_handoffs > 0 else 1.0
        )

        # Error rate
        metrics["error_rate"] = len(workflow.error_history) / len(workflow.agents_sequence)

        # Compare with baselines
        if workflow.command in self.performance_baselines:
            baseline = self.performance_baselines[workflow.command]
            metrics["duration_vs_baseline"] = metrics["duration"] / baseline.get(
                "duration", metrics["duration"]
            )
            metrics["success_vs_baseline"] = metrics["success_rate"] / baseline.get(
                "success_rate", 1.0
            )

        return metrics

    def _update_success_rates(self, command: str, success: bool):
        """Update success rates for command."""
        if command not in self.success_rates:
            self.success_rates[command] = 0.0

        # Simple moving average (could be improved with more sophisticated tracking)
        current_rate = self.success_rates[command]
        weight = 0.1  # Weight for new data point
        self.success_rates[command] = (
            current_rate * (1 - weight) + (1.0 if success else 0.0) * weight
        )

    async def _create_workflow_memory(self, workflow: CommandWorkflowState, phase: str):
        """Create memory for workflow phase."""
        try:
            # Prepare memory content
            if phase == "start":
                content = f"Started {workflow.command} workflow for {workflow.project_name}. Agents: {', '.join(workflow.agents_sequence)}"
            elif phase == "phase_transition":
                content = f"Workflow phase transition for {workflow.project_name}: {workflow.phase.value}. Current agent: {workflow.current_agent}"
            elif phase == "completion":
                content = f"Completed {workflow.command} workflow for {workflow.project_name}. Success: {workflow.success}, Duration: {workflow.duration:.1f}s"
            else:
                content = f"Workflow {phase}: {workflow.workflow_id}"

            # Prepare metadata
            metadata = {
                "workflow_id": workflow.workflow_id,
                "command": workflow.command,
                "project_name": workflow.project_name,
                "phase": phase,
                "current_phase": workflow.phase.value,
                "agents_sequence": workflow.agents_sequence,
                "current_agent": workflow.current_agent,
                "success": workflow.success,
                "timestamp": datetime.now().isoformat(),
            }

            # Add phase-specific metadata
            if phase == "completion":
                metadata.update(
                    {
                        "duration": workflow.duration,
                        "quality_gates_passed": len(workflow.quality_gates_passed),
                        "quality_gates_failed": len(workflow.quality_gates_failed),
                        "agent_handoffs": len(workflow.agent_handoffs),
                        "error_count": len(workflow.error_history),
                        "performance_metrics": workflow.performance_metrics,
                    }
                )

            # Create trigger event
            trigger_event = TriggerEvent(
                trigger_type=(
                    TriggerType.WORKFLOW_COMPLETION
                    if phase == "completion"
                    else TriggerType.WORKFLOW_TRANSITION
                ),
                priority=TriggerPriority.HIGH if phase == "completion" else TriggerPriority.MEDIUM,
                project_name=workflow.project_name,
                event_id=f"three_command_{phase}_{workflow.workflow_id}",
                content=content,
                category=MemoryCategory.WORKFLOW,
                tags=["three_command", workflow.command, phase] + workflow.agents_sequence,
                metadata=metadata,
                source="three_command_integration",
                context=workflow.context,
            )

            # Process trigger
            orchestrator = self.memory_service.get_trigger_orchestrator()
            if orchestrator:
                await orchestrator.process_trigger(trigger_event)
                self.logger.info(f"Created workflow memory: {phase} for {workflow.workflow_id}")

        except Exception as e:
            self.logger.error(f"Failed to create workflow memory: {e}")

    async def get_command_analytics(self, command: str, project_name: str = None) -> Dict[str, Any]:
        """Get analytics for command executions."""
        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return {"error": "Memory service not available"}

            # Build search query
            search_query = f"command:{command}"
            if project_name:
                search_query += f" project:{project_name}"

            # Search for command memories
            memories = await memory_service.search_memories(
                query=search_query, filters={"command": command}, limit=50
            )

            if not memories:
                return {"command": command, "executions": 0, "analytics": {}}

            # Analyze memories
            analytics = {}

            # Success rate
            successes = sum(1 for m in memories if m.metadata.get("success", False))
            analytics["success_rate"] = successes / len(memories)

            # Average duration
            durations = [m.metadata.get("duration", 0) for m in memories]
            analytics["average_duration"] = sum(durations) / len(durations) if durations else 0

            # Quality gates performance
            total_passed = sum(m.metadata.get("quality_gates_passed", 0) for m in memories)
            total_failed = sum(m.metadata.get("quality_gates_failed", 0) for m in memories)
            analytics["quality_gates_success_rate"] = (
                total_passed / (total_passed + total_failed)
                if (total_passed + total_failed) > 0
                else 0
            )

            # Error patterns
            error_counts = sum(m.metadata.get("error_count", 0) for m in memories)
            analytics["average_errors"] = error_counts / len(memories)

            # Recent trend (last 10 executions)
            recent_memories = sorted(
                memories, key=lambda m: m.metadata.get("timestamp", ""), reverse=True
            )[:10]
            recent_successes = sum(1 for m in recent_memories if m.metadata.get("success", False))
            analytics["recent_success_rate"] = (
                recent_successes / len(recent_memories) if recent_memories else 0
            )

            return {
                "command": command,
                "project_name": project_name,
                "executions": len(memories),
                "analytics": analytics,
                "success_rate": self.success_rates.get(command, 0.0),
            }

        except Exception as e:
            self.logger.error(f"Failed to get command analytics: {e}")
            return {"error": str(e)}

    def get_active_workflows(self) -> Dict[str, CommandWorkflowState]:
        """Get all active workflows."""
        return {wid: workflow.to_dict() for wid, workflow in self.active_workflows.items()}

    async def cleanup_stale_workflows(self, timeout_seconds: int = 1800):
        """Clean up workflows that have been running too long."""
        current_time = time.time()
        stale_workflows = []

        for workflow_id, workflow in self.active_workflows.items():
            if current_time - workflow.start_time > timeout_seconds:
                stale_workflows.append(workflow_id)

        for workflow_id in stale_workflows:
            workflow = self.active_workflows[workflow_id]
            await self.complete_command_workflow(
                workflow_id=workflow_id,
                success=False,
                final_result={"error": "Workflow timeout", "timeout": True},
            )
            self.logger.warning(f"Cleaned up stale workflow: {workflow_id}")


# Factory function for creating three command integration
def create_three_command_memory_integration(
    memory_service: MemoryTriggerService,
) -> ThreeCommandMemoryIntegration:
    """
    Create three command memory integration instance.

    Args:
        memory_service: Memory trigger service

    Returns:
        Three command memory integration instance
    """
    return ThreeCommandMemoryIntegration(memory_service)
