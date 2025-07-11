"""
Agent Memory Integration Service
===============================

Service for integrating memory capabilities into the Claude PM Framework's
agent operations. Provides coordination patterns, agent handoff memory,
and memory-driven recommendations for multi-agent workflows.

Key Features:
- Agent coordination memory patterns
- Multi-agent workflow memory tracking
- Agent handoff context preservation
- Memory-driven agent recommendations
- Three-command system integration
- Agent performance pattern analysis

Architecture:
- AgentMemoryCoordinator: Central coordination for agent memory
- AgentHandoffManager: Manages memory for agent handoffs
- WorkflowMemoryTracker: Tracks multi-agent workflow patterns
- ThreeCommandMemoryIntegration: Memory integration for push/deploy/publish
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from pathlib import Path
import json
from enum import Enum

from .memory.memory_trigger_service import MemoryTriggerService
from .memory.trigger_orchestrator import TriggerEvent, TriggerResult
from .memory.trigger_types import TriggerType, TriggerPriority
from .memory.interfaces.models import MemoryCategory, MemoryItem
from ..agents.memory_enhanced_agents import (
    MemoryEnhancedAgent,
    AgentMemoryContext,
    AgentMemoryPatternRegistry,
)


class HandoffStatus(Enum):
    """Status of agent handoff operations."""

    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class WorkflowPhase(Enum):
    """Phases of multi-agent workflows."""

    PREPARATION = "preparation"
    EXECUTION = "execution"
    VALIDATION = "validation"
    COMPLETION = "completion"
    CLEANUP = "cleanup"


@dataclass
class AgentHandoffContext:
    """Context for agent handoff operations."""

    handoff_id: str
    source_agent_id: str
    target_agent_id: str
    project_name: str
    workflow_type: str
    handoff_context: Dict[str, Any]
    status: HandoffStatus = HandoffStatus.INITIATED
    start_time: float = field(default_factory=time.time)
    completion_time: Optional[float] = None
    error_message: Optional[str] = None
    memory_context: Optional[AgentMemoryContext] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "handoff_id": self.handoff_id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "project_name": self.project_name,
            "workflow_type": self.workflow_type,
            "handoff_context": self.handoff_context,
            "status": self.status.value,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "error_message": self.error_message,
            "memory_context": self.memory_context.to_dict() if self.memory_context else None,
        }


@dataclass
class WorkflowMemoryState:
    """State of multi-agent workflow memory."""

    workflow_id: str
    workflow_type: str
    project_name: str
    phase: WorkflowPhase
    agents_involved: List[str]
    start_time: float
    current_agent: Optional[str] = None
    completion_time: Optional[float] = None
    success: bool = False
    agent_handoffs: List[AgentHandoffContext] = field(default_factory=list)
    workflow_context: Dict[str, Any] = field(default_factory=dict)
    quality_gates: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "project_name": self.project_name,
            "phase": self.phase.value,
            "agents_involved": self.agents_involved,
            "start_time": self.start_time,
            "current_agent": self.current_agent,
            "completion_time": self.completion_time,
            "success": self.success,
            "agent_handoffs": [h.to_dict() for h in self.agent_handoffs],
            "workflow_context": self.workflow_context,
            "quality_gates": self.quality_gates,
            "performance_metrics": self.performance_metrics,
        }


class AgentHandoffManager:
    """Manages memory for agent handoff operations."""

    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
        self.active_handoffs: Dict[str, AgentHandoffContext] = {}
        self.handoff_timeout = 300  # 5 minutes

    async def initiate_handoff(
        self,
        source_agent_id: str,
        target_agent_id: str,
        project_name: str,
        workflow_type: str,
        handoff_context: Dict[str, Any],
    ) -> str:
        """
        Initiate agent handoff with memory context.

        Args:
            source_agent_id: ID of source agent
            target_agent_id: ID of target agent
            project_name: Project name
            workflow_type: Type of workflow
            handoff_context: Context to pass between agents

        Returns:
            Handoff ID for tracking
        """
        handoff_id = f"handoff_{source_agent_id}_{target_agent_id}_{int(time.time())}"

        # Create handoff context
        handoff = AgentHandoffContext(
            handoff_id=handoff_id,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            project_name=project_name,
            workflow_type=workflow_type,
            handoff_context=handoff_context,
        )

        # Store active handoff
        self.active_handoffs[handoff_id] = handoff

        # Recall relevant memories for handoff
        handoff.memory_context = await self._recall_handoff_memories(handoff)

        # Create handoff initiation memory
        await self._create_handoff_memory(handoff, "initiation")

        self.logger.info(f"Initiated handoff: {source_agent_id} -> {target_agent_id}")
        return handoff_id

    async def complete_handoff(
        self,
        handoff_id: str,
        success: bool,
        result_context: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Complete agent handoff and create completion memory.

        Args:
            handoff_id: Handoff ID
            success: Whether handoff was successful
            result_context: Result context from handoff
            error_message: Error message if failed

        Returns:
            True if completion was processed successfully
        """
        if handoff_id not in self.active_handoffs:
            self.logger.error(f"Handoff not found: {handoff_id}")
            return False

        handoff = self.active_handoffs[handoff_id]

        # Update handoff status
        handoff.status = HandoffStatus.COMPLETED if success else HandoffStatus.FAILED
        handoff.completion_time = time.time()
        handoff.error_message = error_message

        if result_context:
            handoff.handoff_context.update(result_context)

        # Create completion memory
        await self._create_handoff_memory(handoff, "completion")

        # Remove from active handoffs
        del self.active_handoffs[handoff_id]

        self.logger.info(f"Completed handoff: {handoff_id} (success: {success})")
        return True

    async def _recall_handoff_memories(self, handoff: AgentHandoffContext) -> AgentMemoryContext:
        """Recall relevant memories for handoff."""
        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return AgentMemoryContext(
                    agent_id=handoff.source_agent_id,
                    agent_type="coordination",
                    operation="handoff",
                    project_name=handoff.project_name,
                )

            # Search for similar handoffs
            search_query = f"handoff {handoff.source_agent_id} {handoff.target_agent_id} {handoff.project_name}"

            memories = await memory_service.search_memories(
                query=search_query,
                filters={
                    "workflow_type": handoff.workflow_type,
                    "project_name": handoff.project_name,
                },
                limit=5,
            )

            # Analyze patterns
            patterns = []
            recommendations = []

            if memories:
                # Analyze success rate
                success_count = sum(1 for m in memories if m.metadata.get("success", True))
                success_rate = success_count / len(memories)

                if success_rate < 0.8:
                    patterns.append("handoff_reliability_issues")
                    recommendations.append(
                        f"Handoff success rate is {success_rate:.1%} - review handoff process"
                    )

                # Analyze timing patterns
                durations = [m.metadata.get("duration", 0) for m in memories]
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    if avg_duration > 60:  # More than 1 minute
                        patterns.append("slow_handoffs")
                        recommendations.append(
                            f"Average handoff duration is {avg_duration:.1f}s - consider optimization"
                        )

            return AgentMemoryContext(
                agent_id=handoff.source_agent_id,
                agent_type="coordination",
                operation="handoff",
                project_name=handoff.project_name,
                related_memories=memories,
                patterns_detected=patterns,
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Failed to recall handoff memories: {e}")
            return AgentMemoryContext(
                agent_id=handoff.source_agent_id,
                agent_type="coordination",
                operation="handoff",
                project_name=handoff.project_name,
            )

    async def _create_handoff_memory(self, handoff: AgentHandoffContext, phase: str):
        """Create memory for handoff phase."""
        try:
            # Prepare memory content
            if phase == "initiation":
                content = f"Agent handoff initiated: {handoff.source_agent_id} -> {handoff.target_agent_id} for {handoff.project_name} ({handoff.workflow_type})"
            elif phase == "completion":
                duration = (
                    handoff.completion_time - handoff.start_time if handoff.completion_time else 0
                )
                content = f"Agent handoff completed: {handoff.source_agent_id} -> {handoff.target_agent_id} for {handoff.project_name}. Duration: {duration:.1f}s, Success: {handoff.status == HandoffStatus.COMPLETED}"
            else:
                content = f"Agent handoff {phase}: {handoff.handoff_id}"

            # Prepare metadata
            metadata = {
                "handoff_id": handoff.handoff_id,
                "source_agent": handoff.source_agent_id,
                "target_agent": handoff.target_agent_id,
                "project_name": handoff.project_name,
                "workflow_type": handoff.workflow_type,
                "phase": phase,
                "success": handoff.status == HandoffStatus.COMPLETED,
                "timestamp": datetime.now().isoformat(),
            }

            if handoff.completion_time:
                metadata["duration"] = handoff.completion_time - handoff.start_time

            if handoff.error_message:
                metadata["error"] = handoff.error_message

            # Create trigger event
            trigger_event = TriggerEvent(
                trigger_type=TriggerType.WORKFLOW_TRANSITION,
                priority=TriggerPriority.MEDIUM,
                project_name=handoff.project_name,
                event_id=f"handoff_{phase}_{handoff.handoff_id}",
                content=content,
                category=MemoryCategory.WORKFLOW,
                tags=["coordination", "handoff", handoff.workflow_type, phase],
                metadata=metadata,
                source="agent_coordination",
                context=handoff.handoff_context,
            )

            # Process trigger
            orchestrator = self.memory_service.get_trigger_orchestrator()
            if orchestrator:
                await orchestrator.process_trigger(trigger_event)
                self.logger.info(f"Created handoff memory: {phase} for {handoff.handoff_id}")

        except Exception as e:
            self.logger.error(f"Failed to create handoff memory: {e}")

    async def cleanup_expired_handoffs(self):
        """Clean up expired handoffs."""
        current_time = time.time()
        expired_handoffs = []

        for handoff_id, handoff in self.active_handoffs.items():
            if current_time - handoff.start_time > self.handoff_timeout:
                handoff.status = HandoffStatus.TIMEOUT
                handoff.completion_time = current_time
                expired_handoffs.append(handoff_id)

        for handoff_id in expired_handoffs:
            handoff = self.active_handoffs[handoff_id]
            await self._create_handoff_memory(handoff, "timeout")
            del self.active_handoffs[handoff_id]
            self.logger.warning(f"Handoff timeout: {handoff_id}")

    def get_active_handoffs(self) -> Dict[str, AgentHandoffContext]:
        """Get all active handoffs."""
        return self.active_handoffs.copy()


class WorkflowMemoryTracker:
    """Tracks multi-agent workflow patterns and memory."""

    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
        self.active_workflows: Dict[str, WorkflowMemoryState] = {}
        self.workflow_timeout = 1800  # 30 minutes

    async def start_workflow(
        self,
        workflow_type: str,
        project_name: str,
        agents_involved: List[str],
        workflow_context: Dict[str, Any],
    ) -> str:
        """
        Start tracking multi-agent workflow.

        Args:
            workflow_type: Type of workflow (push, deploy, publish)
            project_name: Project name
            agents_involved: List of agent IDs involved
            workflow_context: Workflow context

        Returns:
            Workflow ID for tracking
        """
        workflow_id = f"workflow_{workflow_type}_{project_name}_{int(time.time())}"

        # Create workflow state
        workflow = WorkflowMemoryState(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            project_name=project_name,
            phase=WorkflowPhase.PREPARATION,
            agents_involved=agents_involved,
            start_time=time.time(),
            workflow_context=workflow_context,
        )

        # Store active workflow
        self.active_workflows[workflow_id] = workflow

        # Create workflow start memory
        await self._create_workflow_memory(workflow, "start")

        self.logger.info(f"Started workflow tracking: {workflow_id}")
        return workflow_id

    async def update_workflow_phase(
        self,
        workflow_id: str,
        phase: WorkflowPhase,
        current_agent: Optional[str] = None,
        context_update: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update workflow phase and context.

        Args:
            workflow_id: Workflow ID
            phase: New workflow phase
            current_agent: Currently active agent
            context_update: Context updates

        Returns:
            True if update was successful
        """
        if workflow_id not in self.active_workflows:
            self.logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow = self.active_workflows[workflow_id]

        # Update workflow state
        workflow.phase = phase
        workflow.current_agent = current_agent

        if context_update:
            workflow.workflow_context.update(context_update)

        # Create phase transition memory
        await self._create_workflow_memory(workflow, "phase_transition")

        self.logger.info(f"Updated workflow phase: {workflow_id} -> {phase.value}")
        return True

    async def add_workflow_handoff(
        self, workflow_id: str, handoff_context: AgentHandoffContext
    ) -> bool:
        """
        Add handoff to workflow tracking.

        Args:
            workflow_id: Workflow ID
            handoff_context: Handoff context

        Returns:
            True if handoff was added
        """
        if workflow_id not in self.active_workflows:
            self.logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow = self.active_workflows[workflow_id]
        workflow.agent_handoffs.append(handoff_context)

        self.logger.info(f"Added handoff to workflow: {workflow_id}")
        return True

    async def complete_workflow(
        self,
        workflow_id: str,
        success: bool,
        quality_gates: List[str],
        performance_metrics: Dict[str, float],
        final_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Complete workflow tracking and create completion memory.

        Args:
            workflow_id: Workflow ID
            success: Whether workflow was successful
            quality_gates: Quality gates that were passed
            performance_metrics: Performance metrics
            final_context: Final workflow context

        Returns:
            True if completion was processed
        """
        if workflow_id not in self.active_workflows:
            self.logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow = self.active_workflows[workflow_id]

        # Update workflow completion
        workflow.phase = WorkflowPhase.COMPLETION
        workflow.success = success
        workflow.completion_time = time.time()
        workflow.quality_gates = quality_gates
        workflow.performance_metrics = performance_metrics

        if final_context:
            workflow.workflow_context.update(final_context)

        # Create completion memory
        await self._create_workflow_memory(workflow, "completion")

        # Remove from active workflows
        del self.active_workflows[workflow_id]

        self.logger.info(f"Completed workflow: {workflow_id} (success: {success})")
        return True

    async def _create_workflow_memory(self, workflow: WorkflowMemoryState, phase: str):
        """Create memory for workflow phase."""
        try:
            # Prepare memory content
            if phase == "start":
                content = f"Started {workflow.workflow_type} workflow for {workflow.project_name}. Agents: {', '.join(workflow.agents_involved)}"
            elif phase == "phase_transition":
                content = f"Workflow phase transition for {workflow.project_name}: {workflow.phase.value}. Current agent: {workflow.current_agent}"
            elif phase == "completion":
                duration = (
                    workflow.completion_time - workflow.start_time
                    if workflow.completion_time
                    else 0
                )
                content = f"Completed {workflow.workflow_type} workflow for {workflow.project_name}. Duration: {duration:.1f}s, Success: {workflow.success}, Quality gates: {len(workflow.quality_gates)}"
            else:
                content = f"Workflow {phase}: {workflow.workflow_id}"

            # Prepare metadata
            metadata = {
                "workflow_id": workflow.workflow_id,
                "workflow_type": workflow.workflow_type,
                "project_name": workflow.project_name,
                "phase": phase,
                "agents_involved": workflow.agents_involved,
                "current_agent": workflow.current_agent,
                "success": workflow.success,
                "timestamp": datetime.now().isoformat(),
            }

            if workflow.completion_time:
                metadata["duration"] = workflow.completion_time - workflow.start_time
                metadata["quality_gates"] = workflow.quality_gates
                metadata["performance_metrics"] = workflow.performance_metrics
                metadata["handoffs_count"] = len(workflow.agent_handoffs)

            # Create trigger event
            trigger_event = TriggerEvent(
                trigger_type=(
                    TriggerType.WORKFLOW_COMPLETION
                    if phase == "completion"
                    else TriggerType.WORKFLOW_TRANSITION
                ),
                priority=TriggerPriority.HIGH if phase == "completion" else TriggerPriority.MEDIUM,
                project_name=workflow.project_name,
                event_id=f"workflow_{phase}_{workflow.workflow_id}",
                content=content,
                category=MemoryCategory.WORKFLOW,
                tags=["workflow", workflow.workflow_type, phase] + workflow.agents_involved,
                metadata=metadata,
                source="workflow_coordination",
                context=workflow.workflow_context,
            )

            # Process trigger
            orchestrator = self.memory_service.get_trigger_orchestrator()
            if orchestrator:
                await orchestrator.process_trigger(trigger_event)
                self.logger.info(f"Created workflow memory: {phase} for {workflow.workflow_id}")

        except Exception as e:
            self.logger.error(f"Failed to create workflow memory: {e}")

    async def cleanup_expired_workflows(self):
        """Clean up expired workflows."""
        current_time = time.time()
        expired_workflows = []

        for workflow_id, workflow in self.active_workflows.items():
            if current_time - workflow.start_time > self.workflow_timeout:
                workflow.phase = WorkflowPhase.CLEANUP
                workflow.completion_time = current_time
                workflow.success = False
                expired_workflows.append(workflow_id)

        for workflow_id in expired_workflows:
            workflow = self.active_workflows[workflow_id]
            await self._create_workflow_memory(workflow, "timeout")
            del self.active_workflows[workflow_id]
            self.logger.warning(f"Workflow timeout: {workflow_id}")

    def get_active_workflows(self) -> Dict[str, WorkflowMemoryState]:
        """Get all active workflows."""
        return self.active_workflows.copy()


class ThreeCommandMemoryIntegration:
    """Memory integration for push/deploy/publish command workflows."""

    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
        self.command_patterns = {
            "push": ["documentation", "qa", "ops"],
            "deploy": ["ops", "qa"],
            "publish": ["ops", "documentation", "ops"],
        }

    async def start_command_workflow(
        self, command: str, project_name: str, context: Dict[str, Any]
    ) -> str:
        """
        Start memory tracking for three-command workflow.

        Args:
            command: Command type (push, deploy, publish)
            project_name: Project name
            context: Command context

        Returns:
            Workflow ID for tracking
        """
        if command not in self.command_patterns:
            raise ValueError(f"Unknown command: {command}")

        agents_involved = self.command_patterns[command]

        # Create workflow memory content
        memory_content = (
            f"Started {command} command for {project_name}. Agents: {', '.join(agents_involved)}"
        )

        # Prepare metadata
        metadata = {
            "command": command,
            "project_name": project_name,
            "agents_involved": agents_involved,
            "start_time": time.time(),
            "timestamp": datetime.now().isoformat(),
        }

        # Add command-specific context
        if command == "push":
            metadata["git_operations"] = True
            metadata["quality_gates"] = ["documentation", "testing", "linting"]
        elif command == "deploy":
            metadata["deployment_type"] = context.get("deployment_type", "local")
            metadata["quality_gates"] = ["health_check", "validation"]
        elif command == "publish":
            metadata["publication_type"] = context.get("publication_type", "package")
            metadata["quality_gates"] = ["version_check", "documentation", "build"]

        # Create trigger event
        trigger_event = TriggerEvent(
            trigger_type=TriggerType.WORKFLOW_START,
            priority=TriggerPriority.HIGH,
            project_name=project_name,
            event_id=f"{command}_workflow_{project_name}_{int(time.time())}",
            content=memory_content,
            category=MemoryCategory.WORKFLOW,
            tags=["three_command", command, "workflow_start"] + agents_involved,
            metadata=metadata,
            source="three_command_system",
            context=context,
        )

        # Process trigger
        orchestrator = self.memory_service.get_trigger_orchestrator()
        if orchestrator:
            await orchestrator.process_trigger(trigger_event)
            self.logger.info(f"Started {command} workflow memory tracking for {project_name}")
            return trigger_event.event_id

        return ""

    async def create_command_completion_memory(
        self,
        command: str,
        project_name: str,
        success: bool,
        duration: float,
        quality_gates_passed: List[str],
        context: Dict[str, Any],
    ):
        """
        Create completion memory for three-command workflow.

        Args:
            command: Command type
            project_name: Project name
            success: Whether command was successful
            duration: Command duration in seconds
            quality_gates_passed: Quality gates that passed
            context: Command context
        """
        # Create completion memory content
        memory_content = f"Completed {command} command for {project_name}. Success: {success}, Duration: {duration:.1f}s, Quality gates: {len(quality_gates_passed)}"

        # Prepare metadata
        metadata = {
            "command": command,
            "project_name": project_name,
            "success": success,
            "duration": duration,
            "quality_gates_passed": quality_gates_passed,
            "quality_gates_count": len(quality_gates_passed),
            "timestamp": datetime.now().isoformat(),
        }

        # Add command-specific results
        if command == "push":
            metadata["git_operations"] = context.get("git_operations", {})
            metadata["tests_passed"] = context.get("tests_passed", 0)
            metadata["documentation_validated"] = context.get("documentation_validated", False)
        elif command == "deploy":
            metadata["deployment_status"] = context.get("deployment_status", "unknown")
            metadata["services_deployed"] = context.get("services_deployed", [])
        elif command == "publish":
            metadata["publication_status"] = context.get("publication_status", "unknown")
            metadata["packages_published"] = context.get("packages_published", [])

        # Create trigger event
        trigger_event = TriggerEvent(
            trigger_type=TriggerType.WORKFLOW_COMPLETION,
            priority=TriggerPriority.HIGH,
            project_name=project_name,
            event_id=f"{command}_completion_{project_name}_{int(time.time())}",
            content=memory_content,
            category=MemoryCategory.WORKFLOW,
            tags=[
                "three_command",
                command,
                "workflow_completion",
                "success" if success else "failure",
            ],
            metadata=metadata,
            source="three_command_system",
            context=context,
        )

        # Process trigger
        orchestrator = self.memory_service.get_trigger_orchestrator()
        if orchestrator:
            await orchestrator.process_trigger(trigger_event)
            self.logger.info(f"Created {command} completion memory for {project_name}")


class AgentMemoryCoordinator:
    """
    Central coordinator for agent memory integration.

    Coordinates memory operations across agents, handoffs, and workflows.
    Provides unified interface for memory-enhanced agent operations.
    """

    def __init__(self, memory_service: MemoryTriggerService):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
        self.pattern_registry = AgentMemoryPatternRegistry()

        # Initialize sub-coordinators
        self.handoff_manager = AgentHandoffManager(memory_service)
        self.workflow_tracker = WorkflowMemoryTracker(memory_service)
        self.three_command_integration = ThreeCommandMemoryIntegration(memory_service)

        # Enhanced agent registry
        self.memory_enhanced_agents: Dict[str, MemoryEnhancedAgent] = {}

        # Coordination metrics
        self.coordination_metrics = {
            "total_handoffs": 0,
            "successful_handoffs": 0,
            "total_workflows": 0,
            "successful_workflows": 0,
            "memory_enhanced_agents": 0,
        }

        # Background tasks
        self.cleanup_task = None
        self.cleanup_interval = 300  # 5 minutes

    async def initialize(self):
        """Initialize the agent memory coordinator."""
        try:
            # Initialize memory service
            await self.memory_service.initialize()

            # Start background cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

            self.logger.info("Agent memory coordinator initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize agent memory coordinator: {e}")
            raise

    async def enhance_agent_with_memory(self, agent) -> MemoryEnhancedAgent:
        """
        Enhance an agent with memory capabilities.

        Args:
            agent: Agent to enhance

        Returns:
            Memory-enhanced agent
        """
        enhanced_agent = MemoryEnhancedAgent(agent, self.memory_service)
        self.memory_enhanced_agents[agent.agent_id] = enhanced_agent
        self.coordination_metrics["memory_enhanced_agents"] += 1

        self.logger.info(f"Enhanced agent with memory: {agent.agent_id}")
        return enhanced_agent

    async def coordinate_agent_handoff(
        self,
        source_agent_id: str,
        target_agent_id: str,
        project_name: str,
        workflow_type: str,
        handoff_context: Dict[str, Any],
    ) -> str:
        """
        Coordinate memory-aware agent handoff.

        Args:
            source_agent_id: Source agent ID
            target_agent_id: Target agent ID
            project_name: Project name
            workflow_type: Workflow type
            handoff_context: Handoff context

        Returns:
            Handoff ID
        """
        handoff_id = await self.handoff_manager.initiate_handoff(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            project_name=project_name,
            workflow_type=workflow_type,
            handoff_context=handoff_context,
        )

        self.coordination_metrics["total_handoffs"] += 1
        return handoff_id

    async def complete_agent_handoff(
        self,
        handoff_id: str,
        success: bool,
        result_context: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Complete agent handoff with memory tracking.

        Args:
            handoff_id: Handoff ID
            success: Whether handoff was successful
            result_context: Result context
            error_message: Error message if failed

        Returns:
            True if completion was processed
        """
        result = await self.handoff_manager.complete_handoff(
            handoff_id=handoff_id,
            success=success,
            result_context=result_context,
            error_message=error_message,
        )

        if result and success:
            self.coordination_metrics["successful_handoffs"] += 1

        return result

    async def start_workflow_tracking(
        self,
        workflow_type: str,
        project_name: str,
        agents_involved: List[str],
        workflow_context: Dict[str, Any],
    ) -> str:
        """
        Start workflow memory tracking.

        Args:
            workflow_type: Workflow type
            project_name: Project name
            agents_involved: List of agents
            workflow_context: Workflow context

        Returns:
            Workflow ID
        """
        workflow_id = await self.workflow_tracker.start_workflow(
            workflow_type=workflow_type,
            project_name=project_name,
            agents_involved=agents_involved,
            workflow_context=workflow_context,
        )

        self.coordination_metrics["total_workflows"] += 1
        return workflow_id

    async def complete_workflow_tracking(
        self,
        workflow_id: str,
        success: bool,
        quality_gates: List[str],
        performance_metrics: Dict[str, float],
        final_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Complete workflow memory tracking.

        Args:
            workflow_id: Workflow ID
            success: Whether workflow was successful
            quality_gates: Quality gates passed
            performance_metrics: Performance metrics
            final_context: Final context

        Returns:
            True if completion was processed
        """
        result = await self.workflow_tracker.complete_workflow(
            workflow_id=workflow_id,
            success=success,
            quality_gates=quality_gates,
            performance_metrics=performance_metrics,
            final_context=final_context,
        )

        if result and success:
            self.coordination_metrics["successful_workflows"] += 1

        return result

    async def integrate_three_command_memory(
        self, command: str, project_name: str, context: Dict[str, Any]
    ) -> str:
        """
        Integrate memory for three-command workflows.

        Args:
            command: Command type (push, deploy, publish)
            project_name: Project name
            context: Command context

        Returns:
            Workflow ID
        """
        return await self.three_command_integration.start_command_workflow(
            command=command, project_name=project_name, context=context
        )

    async def complete_three_command_memory(
        self,
        command: str,
        project_name: str,
        success: bool,
        duration: float,
        quality_gates_passed: List[str],
        context: Dict[str, Any],
    ):
        """
        Complete three-command memory tracking.

        Args:
            command: Command type
            project_name: Project name
            success: Whether command was successful
            duration: Command duration
            quality_gates_passed: Quality gates passed
            context: Command context
        """
        await self.three_command_integration.create_command_completion_memory(
            command=command,
            project_name=project_name,
            success=success,
            duration=duration,
            quality_gates_passed=quality_gates_passed,
            context=context,
        )

    async def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get coordination metrics."""
        return {
            **self.coordination_metrics,
            "active_handoffs": len(self.handoff_manager.get_active_handoffs()),
            "active_workflows": len(self.workflow_tracker.get_active_workflows()),
            "memory_enhanced_agents": len(self.memory_enhanced_agents),
            "timestamp": datetime.now().isoformat(),
        }

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                # Cleanup expired handoffs and workflows
                await self.handoff_manager.cleanup_expired_handoffs()
                await self.workflow_tracker.cleanup_expired_workflows()

            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")

    async def cleanup(self):
        """Cleanup coordinator resources."""
        try:
            # Cancel cleanup task
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            # Cleanup memory service
            await self.memory_service.cleanup()

            self.logger.info("Agent memory coordinator cleanup completed")

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Factory function for creating the coordinator
def create_agent_memory_coordinator(memory_service: MemoryTriggerService) -> AgentMemoryCoordinator:
    """
    Create agent memory coordinator instance.

    Args:
        memory_service: Memory trigger service

    Returns:
        Agent memory coordinator
    """
    return AgentMemoryCoordinator(memory_service)
