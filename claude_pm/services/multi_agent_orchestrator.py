"""
Multi-Agent Orchestrator - MEM-003 Implementation
Enhanced multi-agent architecture with memory integration and parallel execution.
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

from .claude_pm_memory import ClaudePMMemory, MemoryCategory
from .mcp_service_detector import MCPServiceDetector, get_mcp_service_recommendations
from ..core.logging_config import get_logger
from ..core.enforcement import (
    get_enforcement_engine,
    EnforcementEngine,
    Agent as EnforcementAgent,
    Action as EnforcementAction,
    ActionType,
    AgentType as EnforcementAgentType,
    AgentDisplayNames,
)
import sys
from pathlib import Path

# Add framework path to sys.path
framework_path = Path(__file__).parent.parent.parent / "framework" / "multi-agent"
sys.path.insert(0, str(framework_path))

# Import with corrected module name
import importlib.util

spec = importlib.util.spec_from_file_location(
    "git_worktree_manager", framework_path / "git-worktree-manager.py"
)
git_worktree_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(git_worktree_module)

GitWorktreeManager = git_worktree_module.GitWorktreeManager
WorktreeContext = git_worktree_module.WorktreeContext

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Agent types in the multi-agent ecosystem."""

    # Core Agents
    ORCHESTRATOR = "orchestrator"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    QA = "qa"
    RESEARCHER = "researcher"
    OPERATIONS = "operations"

    # Specialist Agents
    SECURITY_ENGINEER = "security_engineer"
    PERFORMANCE_ENGINEER = "performance_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_ENGINEER = "data_engineer"
    UI_UX_ENGINEER = "ui_ux_engineer"
    CODE_REVIEW_ENGINEER = "code_review_engineer"  # NEW for MEM-003


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    PREPARING_CONTEXT = "preparing_context"
    EXECUTING = "executing"
    WAITING_FOR_DEPENDENCY = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class AgentTask:
    """Task definition for an agent."""

    task_id: str
    agent_type: AgentType
    description: str
    project_name: str
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    memory_context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10 scale, 10 is highest
    timeout_minutes: int = 30
    retry_count: int = 0
    max_retries: int = 2

    def get_display_name(self) -> str:
        """Get the standardized display name for this task's agent."""
        # Import here to avoid circular imports
        from ..core.enforcement import AgentDisplayNames, AgentType as EnforcementAgentType

        # Convert AgentType to EnforcementAgentType for display name lookup
        try:
            enforcement_type = EnforcementAgentType(self.agent_type.value)
            return AgentDisplayNames.get_display_name(enforcement_type)
        except ValueError:
            # Fallback for unknown types
            return self.agent_type.value.title()

    def get_task_prefix(self) -> str:
        """Get the task prefix for this agent task."""
        # Import here to avoid circular imports
        from ..core.enforcement import AgentDisplayNames, AgentType as EnforcementAgentType

        # Convert AgentType to EnforcementAgentType for prefix generation
        try:
            enforcement_type = EnforcementAgentType(self.agent_type.value)
            return AgentDisplayNames.get_task_prefix(enforcement_type)
        except ValueError:
            # Fallback for unknown types
            return f"[{self.agent_type.value.title()}]"

    def get_prefixed_description(self) -> str:
        """Get the task description with agent prefix."""
        return f"{self.get_task_prefix()} {self.description}"


@dataclass
class AgentExecution:
    """Runtime information for an agent execution."""

    execution_id: str
    task: AgentTask
    agent_type: AgentType
    status: AgentStatus
    worktree_id: Optional[str] = None
    worktree_path: Optional[Path] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    memory_updates: List[str] = field(default_factory=list)  # Memory IDs stored
    logs: List[str] = field(default_factory=list)


class MultiAgentOrchestrator:
    """
    Enhanced Multi-Agent Orchestrator with memory integration and parallel execution.

    Implements MEM-003 requirements:
    - 11-agent ecosystem with memory integration
    - Git worktree isolation for parallel execution
    - Memory-augmented context preparation
    - Agent coordination and messaging
    """

    def __init__(self, base_repo_path: str, memory: ClaudePMMemory, max_parallel: int = 5):
        """
        Initialize the multi-agent orchestrator.

        Args:
            base_repo_path: Path to the base git repository
            memory: ClaudePMMemory instance for memory operations
            max_parallel: Maximum number of parallel agent executions
        """
        self.base_repo_path = Path(base_repo_path)
        self.memory = memory
        self.max_parallel = max_parallel

        # Initialize enforcement engine for delegation constraints
        self.enforcement_engine = get_enforcement_engine()

        # Initialize MCP service detector for enhanced workflows
        self.mcp_detector = MCPServiceDetector()

        # Initialize git worktree manager
        self.worktree_manager = GitWorktreeManager(
            base_repo_path=str(self.base_repo_path),
            worktree_base_path=str(self.base_repo_path / ".worktrees"),
        )

        # Agent tracking
        self.active_executions: Dict[str, AgentExecution] = {}
        self.task_queue: List[AgentTask] = []
        self.completed_tasks: Dict[str, AgentExecution] = {}

        # Agent definitions with memory integration capabilities
        self.agent_definitions = self._initialize_agent_definitions()

        # Coordination
        self.coordination_semaphore = asyncio.Semaphore(max_parallel)
        self.message_bus: Dict[str, List[Dict[str, Any]]] = {}

        logger.info(
            f"MultiAgentOrchestrator initialized with {len(self.agent_definitions)} agents, enforcement engine, and MCP service detection"
        )

    def _initialize_agent_definitions(self) -> Dict[AgentType, Dict[str, Any]]:
        """Initialize agent definitions with memory integration capabilities."""
        return {
            # Core Agents
            AgentType.ORCHESTRATOR: {
                "name": "Orchestrator Agent",
                "description": "Coordinates multi-agent workflows and task distribution",
                "memory_categories": [MemoryCategory.PROJECT, MemoryCategory.PATTERN],
                "specializations": [
                    "workflow_coordination",
                    "task_decomposition",
                    "resource_allocation",
                ],
                "context_keywords": ["coordination", "planning", "workflow", "orchestration"],
            },
            AgentType.ARCHITECT: {
                "name": "Architect Agent",
                "description": "Designs system architecture and makes technical decisions",
                "memory_categories": [MemoryCategory.PROJECT, MemoryCategory.PATTERN],
                "specializations": [
                    "system_design",
                    "architectural_patterns",
                    "technology_selection",
                ],
                "context_keywords": [
                    "architecture",
                    "design",
                    "patterns",
                    "scalability",
                    "technical_decisions",
                ],
            },
            AgentType.ENGINEER: {
                "name": "Engineer Agent",
                "description": "Implements features and writes production code",
                "memory_categories": [
                    MemoryCategory.PATTERN,
                    MemoryCategory.TEAM,
                    MemoryCategory.ERROR,
                ],
                "specializations": ["feature_implementation", "code_development", "debugging"],
                "context_keywords": [
                    "implementation",
                    "coding",
                    "features",
                    "development",
                    "programming",
                ],
            },
            AgentType.QA: {
                "name": "QA Agent",
                "description": "Tests functionality and ensures quality standards",
                "memory_categories": [
                    MemoryCategory.ERROR,
                    MemoryCategory.PATTERN,
                    MemoryCategory.TEAM,
                ],
                "specializations": [
                    "testing",
                    "quality_assurance",
                    "bug_detection",
                    "test_automation",
                ],
                "context_keywords": ["testing", "quality", "bugs", "validation", "qa"],
            },
            AgentType.RESEARCHER: {
                "name": "Researcher Agent",
                "description": "Investigates technologies and gathers requirements",
                "memory_categories": [MemoryCategory.PATTERN, MemoryCategory.PROJECT],
                "specializations": [
                    "technology_research",
                    "requirements_analysis",
                    "market_research",
                ],
                "context_keywords": [
                    "research",
                    "analysis",
                    "requirements",
                    "investigation",
                    "exploration",
                ],
            },
            AgentType.OPERATIONS: {
                "name": "Operations Agent",
                "description": "Manages deployments, configuration, and operational tasks",
                "memory_categories": [
                    MemoryCategory.PATTERN,
                    MemoryCategory.ERROR,
                    MemoryCategory.TEAM,
                ],
                "specializations": ["deployment", "configuration", "operations", "maintenance"],
                "context_keywords": [
                    "deployment",
                    "configuration",
                    "operations",
                    "maintenance",
                    "infrastructure",
                ],
            },
            # Specialist Agents
            AgentType.SECURITY_ENGINEER: {
                "name": "Security Engineer Agent",
                "description": "Analyzes security vulnerabilities and implements security measures",
                "memory_categories": [
                    MemoryCategory.ERROR,
                    MemoryCategory.PATTERN,
                    MemoryCategory.TEAM,
                ],
                "specializations": [
                    "security_analysis",
                    "vulnerability_assessment",
                    "security_implementation",
                ],
                "context_keywords": [
                    "security",
                    "vulnerabilities",
                    "authentication",
                    "authorization",
                    "encryption",
                ],
            },
            AgentType.PERFORMANCE_ENGINEER: {
                "name": "Performance Engineer Agent",
                "description": "Optimizes performance and analyzes system bottlenecks",
                "memory_categories": [MemoryCategory.PATTERN, MemoryCategory.ERROR],
                "specializations": [
                    "performance_optimization",
                    "bottleneck_analysis",
                    "scalability_testing",
                ],
                "context_keywords": [
                    "performance",
                    "optimization",
                    "bottlenecks",
                    "scalability",
                    "speed",
                ],
            },
            AgentType.DEVOPS_ENGINEER: {
                "name": "DevOps Engineer Agent",
                "description": "Manages deployment pipelines and infrastructure",
                "memory_categories": [
                    MemoryCategory.PATTERN,
                    MemoryCategory.TEAM,
                    MemoryCategory.ERROR,
                ],
                "specializations": ["ci_cd", "infrastructure", "deployment", "monitoring"],
                "context_keywords": [
                    "deployment",
                    "infrastructure",
                    "devops",
                    "ci_cd",
                    "monitoring",
                ],
            },
            AgentType.DATA_ENGINEER: {
                "name": "Data Engineer Agent",
                "description": "Designs and implements data processing and storage solutions",
                "memory_categories": [MemoryCategory.PATTERN, MemoryCategory.PROJECT],
                "specializations": ["data_modeling", "etl_pipelines", "data_storage", "analytics"],
                "context_keywords": ["data", "storage", "pipelines", "analytics", "databases"],
            },
            AgentType.UI_UX_ENGINEER: {
                "name": "UI/UX Engineer Agent",
                "description": "Designs user interfaces and user experience flows",
                "memory_categories": [MemoryCategory.PATTERN, MemoryCategory.TEAM],
                "specializations": [
                    "ui_design",
                    "ux_design",
                    "frontend_development",
                    "user_research",
                ],
                "context_keywords": ["ui", "ux", "frontend", "design", "user_experience"],
            },
            AgentType.CODE_REVIEW_ENGINEER: {
                "name": "Code Review Engineer Agent",
                "description": "Performs comprehensive code reviews with security, performance, style, and testing analysis",
                "memory_categories": [
                    MemoryCategory.PATTERN,
                    MemoryCategory.TEAM,
                    MemoryCategory.ERROR,
                ],
                "specializations": [
                    "code_review",
                    "style_analysis",
                    "security_review",
                    "performance_review",
                    "test_coverage",
                ],
                "context_keywords": [
                    "code_review",
                    "style",
                    "standards",
                    "quality",
                    "review",
                    "analysis",
                ],
            },
        }

    async def prepare_memory_context(
        self, agent_type: AgentType, project_name: str, task_description: str
    ) -> Dict[str, Any]:
        """
        Prepare memory-augmented context for an agent.

        Args:
            agent_type: Type of agent requesting context
            project_name: Project being worked on
            task_description: Description of the task

        Returns:
            Dictionary containing relevant memories and context
        """
        try:
            agent_def = self.agent_definitions[agent_type]
            context = {
                "agent_type": agent_type.value,
                "project_name": project_name,
                "task_description": task_description,
                "relevant_memories": {},
                "patterns": [],
                "team_standards": [],
                "historical_errors": [],
                "project_decisions": [],
            }

            # Retrieve memories for each category this agent uses
            for category in agent_def["memory_categories"]:
                memories_response = await self.memory.retrieve_memories(
                    category=category, query=task_description, project_filter=project_name, limit=5
                )

                if memories_response.success and memories_response.data:
                    memories = memories_response.data.get("memories", [])
                    context["relevant_memories"][category.value] = memories

                    # Categorize memories for easier access
                    if category == MemoryCategory.PATTERN:
                        context["patterns"].extend(memories)
                    elif category == MemoryCategory.TEAM:
                        context["team_standards"].extend(memories)
                    elif category == MemoryCategory.ERROR:
                        context["historical_errors"].extend(memories)
                    elif category == MemoryCategory.PROJECT:
                        context["project_decisions"].extend(memories)

            # Add agent-specific context keywords for search
            context["specializations"] = agent_def["specializations"]
            context["context_keywords"] = agent_def["context_keywords"]

            logger.info(
                f"Prepared memory context for {agent_type.value} with {sum(len(memories) for memories in context['relevant_memories'].values())} memories"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to prepare memory context for {agent_type.value}: {e}")
            return {
                "agent_type": agent_type.value,
                "project_name": project_name,
                "task_description": task_description,
                "error": str(e),
            }

    async def submit_task(
        self,
        agent_type: AgentType,
        description: str,
        project_name: str,
        context: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        priority: int = 5,
    ) -> str:
        """
        Submit a task for execution by an agent.

        Args:
            agent_type: Type of agent to execute the task
            description: Task description
            project_name: Project context
            context: Additional context data
            dependencies: List of task IDs this task depends on
            priority: Task priority (1-10, 10 is highest)

        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())

        task = AgentTask(
            task_id=task_id,
            agent_type=agent_type,
            description=description,
            project_name=project_name,
            context=context or {},
            dependencies=dependencies or [],
            priority=priority,
        )

        # Add to queue sorted by priority
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)

        logger.info(f"Submitted task {task_id} for {agent_type.value}: {description}")
        return task_id

    async def execute_task(self, task: AgentTask) -> AgentExecution:
        """
        Execute a single task with memory context and worktree isolation.

        Args:
            task: Task to execute

        Returns:
            AgentExecution with results
        """
        execution_id = str(uuid.uuid4())
        execution = AgentExecution(
            execution_id=execution_id,
            task=task,
            agent_type=task.agent_type,
            status=AgentStatus.INITIALIZING,
        )

        self.active_executions[execution_id] = execution

        try:
            # Validate agent authorization before execution
            if not await self._validate_task_authorization(task, execution):
                execution.status = AgentStatus.FAILED
                execution.error = "Task authorization failed - delegation constraint violation"
                return execution

            # Acquire coordination semaphore for parallel execution control
            async with self.coordination_semaphore:
                execution.start_time = datetime.now()
                execution.status = AgentStatus.PREPARING_CONTEXT

                # Prepare memory-augmented context
                memory_context = await self.prepare_memory_context(
                    task.agent_type, task.project_name, task.description
                )
                execution.task.memory_context = memory_context

                # Create isolated worktree for this execution
                with WorktreeContext(self.worktree_manager, execution_id) as (
                    worktree_id,
                    worktree_path,
                ):
                    execution.worktree_id = worktree_id
                    execution.worktree_path = worktree_path
                    execution.status = AgentStatus.EXECUTING

                    # Execute the agent logic (placeholder for actual agent implementations)
                    result = await self._execute_agent_logic(execution)
                    execution.result = result
                    execution.status = AgentStatus.COMPLETED

                    # Store task completion memory
                    await self._store_execution_memory(execution)

        except Exception as e:
            execution.error = str(e)
            execution.status = AgentStatus.FAILED
            logger.error(f"Task {task.task_id} execution failed: {e}")

        finally:
            execution.end_time = datetime.now()
            self.completed_tasks[task.task_id] = execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

        return execution

    async def _validate_task_authorization(
        self, task: AgentTask, execution: AgentExecution
    ) -> bool:
        """
        Validate that the agent is authorized to perform the task based on delegation constraints.

        Args:
            task: Task to validate
            execution: Execution context

        Returns:
            True if authorized, False otherwise
        """
        try:
            # Convert orchestrator agent type to enforcement agent type
            enforcement_agent_type = self._convert_to_enforcement_agent_type(task.agent_type)

            # Create enforcement agent
            enforcement_agent = EnforcementAgent(
                agent_id=execution.execution_id,
                agent_type=enforcement_agent_type,
                project_name=task.project_name,
                working_directory=execution.worktree_path,
            )

            # If this is a file operation task, validate file access
            if task.context.get("target_files"):
                for file_path in task.context["target_files"]:
                    action = EnforcementAction(
                        action_type=(
                            ActionType.WRITE
                            if "write" in task.description.lower()
                            else ActionType.READ
                        ),
                        resource_path=Path(file_path),
                        agent=enforcement_agent,
                    )

                    result = self.enforcement_engine.validate_action(enforcement_agent, action)
                    if not result.is_valid:
                        logger.error(
                            f"Authorization failed for {task.agent_type.value} accessing {file_path}"
                        )
                        for violation in result.violations:
                            logger.error(f"  Violation: {violation.description}")
                        return False

            # General task authorization check
            task_resource = Path(task.project_name or "project")
            action = EnforcementAction(
                action_type=ActionType.EXECUTE, resource_path=task_resource, agent=enforcement_agent
            )

            result = self.enforcement_engine.validate_action(enforcement_agent, action)
            if not result.is_valid:
                logger.error(
                    f"Task authorization failed for {task.agent_type.value}: {task.description}"
                )
                return False

            logger.debug(f"Task authorization successful for {task.agent_type.value}")
            return True

        except Exception as e:
            logger.error(f"Authorization validation error: {e}")
            return False

    def _convert_to_enforcement_agent_type(
        self, orchestrator_agent_type: AgentType
    ) -> EnforcementAgentType:
        """Convert orchestrator AgentType to enforcement AgentType."""
        # Map orchestrator agent types to enforcement agent types
        mapping = {
            AgentType.ORCHESTRATOR: EnforcementAgentType.ORCHESTRATOR,
            AgentType.ARCHITECT: EnforcementAgentType.ARCHITECT,
            AgentType.ENGINEER: EnforcementAgentType.ENGINEER,
            AgentType.QA: EnforcementAgentType.QA,
            AgentType.RESEARCHER: EnforcementAgentType.RESEARCHER,
            AgentType.SECURITY_ENGINEER: EnforcementAgentType.SECURITY_ENGINEER,
            AgentType.PERFORMANCE_ENGINEER: EnforcementAgentType.PERFORMANCE_ENGINEER,
            AgentType.DEVOPS_ENGINEER: EnforcementAgentType.DEVOPS_ENGINEER,
            AgentType.DATA_ENGINEER: EnforcementAgentType.DATA_ENGINEER,
            AgentType.UI_UX_ENGINEER: EnforcementAgentType.UI_UX_ENGINEER,
            AgentType.CODE_REVIEW_ENGINEER: EnforcementAgentType.CODE_REVIEW_ENGINEER,
        }

        return mapping.get(orchestrator_agent_type, EnforcementAgentType.ENGINEER)

    async def _execute_agent_logic(self, execution: AgentExecution) -> Dict[str, Any]:
        """
        Execute agent-specific logic (placeholder for actual agent implementations).

        Args:
            execution: Agent execution context

        Returns:
            Dictionary with execution results
        """
        # This is a placeholder - in a full implementation, this would delegate
        # to specialized agent classes with their own logic

        agent_type = execution.agent_type
        task = execution.task

        # Simulate agent-specific processing
        await asyncio.sleep(1)  # Simulate work

        result = {
            "agent_type": agent_type.value,
            "task_id": task.task_id,
            "status": "completed",
            "worktree_path": str(execution.worktree_path),
            "memory_context_size": len(task.memory_context.get("relevant_memories", {})),
            "execution_time": (
                (datetime.now() - execution.start_time).total_seconds()
                if execution.start_time
                else 0
            ),
        }

        # Agent-specific result processing
        if agent_type == AgentType.CODE_REVIEW_ENGINEER:
            result.update(
                {
                    "review_dimensions": ["security", "performance", "style", "testing"],
                    "findings_count": 3,  # Placeholder
                    "recommendations": [
                        "Improve error handling",
                        "Add unit tests",
                        "Optimize algorithm",
                    ],
                }
            )
        elif agent_type == AgentType.SECURITY_ENGINEER:
            result.update(
                {
                    "vulnerabilities_found": 1,  # Placeholder
                    "security_score": 85,
                    "recommendations": ["Update dependency", "Add input validation"],
                }
            )

        execution.logs.append(f"Executed {agent_type.value} agent logic")
        return result

    async def _store_execution_memory(self, execution: AgentExecution) -> None:
        """
        Store execution results and learnings in memory.

        Args:
            execution: Completed agent execution
        """
        try:
            # Store execution pattern
            pattern_content = f"""
Agent Execution Pattern - {execution.agent_type.value}

Task: {execution.task.description}
Project: {execution.task.project_name}
Status: {execution.status.value}
Duration: {(execution.end_time - execution.start_time).total_seconds():.2f}s

Results: {json.dumps(execution.result, indent=2)}

Memory Context Used: {len(execution.task.memory_context.get('relevant_memories', {}))} memories
""".strip()

            pattern_response = await self.memory.store_memory(
                category=MemoryCategory.PATTERN,
                content=pattern_content,
                metadata={
                    "agent_type": execution.agent_type.value,
                    "execution_id": execution.execution_id,
                    "task_id": execution.task.task_id,
                    "success": execution.status == AgentStatus.COMPLETED,
                    "duration_seconds": (execution.end_time - execution.start_time).total_seconds(),
                },
                project_name=execution.task.project_name,
                tags=["agent_execution", execution.agent_type.value, "pattern"],
            )

            if pattern_response.success:
                execution.memory_updates.append(pattern_response.memory_id)
                logger.info(f"Stored execution pattern memory: {pattern_response.memory_id}")

            # Store errors if execution failed
            if execution.status == AgentStatus.FAILED and execution.error:
                error_content = f"""
Agent Execution Error - {execution.agent_type.value}

Task: {execution.task.description}
Project: {execution.task.project_name}
Error: {execution.error}

Context: {json.dumps(execution.task.context, indent=2)}
""".strip()

                error_response = await self.memory.store_memory(
                    category=MemoryCategory.ERROR,
                    content=error_content,
                    metadata={
                        "agent_type": execution.agent_type.value,
                        "execution_id": execution.execution_id,
                        "task_id": execution.task.task_id,
                        "error_type": "agent_execution_failure",
                    },
                    project_name=execution.task.project_name,
                    tags=["agent_error", execution.agent_type.value, "failure"],
                )

                if error_response.success:
                    execution.memory_updates.append(error_response.memory_id)
                    logger.info(f"Stored execution error memory: {error_response.memory_id}")

        except Exception as e:
            logger.error(f"Failed to store execution memory: {e}")

    async def run_parallel_execution(self, max_iterations: int = 10) -> Dict[str, Any]:
        """
        Run parallel execution of queued tasks.

        Args:
            max_iterations: Maximum number of execution iterations

        Returns:
            Summary of execution results
        """
        completed_count = 0
        failed_count = 0
        iterations = 0

        logger.info(f"Starting parallel execution with {len(self.task_queue)} tasks queued")

        while self.task_queue and iterations < max_iterations:
            iterations += 1

            # Find tasks ready for execution (dependencies satisfied)
            ready_tasks = []
            for task in self.task_queue[:]:
                if self._are_dependencies_satisfied(task):
                    ready_tasks.append(task)
                    self.task_queue.remove(task)

            if not ready_tasks:
                logger.warning("No tasks ready for execution - possible circular dependencies")
                break

            # Execute ready tasks in parallel (up to max_parallel limit)
            execution_tasks = []
            for task in ready_tasks[: self.max_parallel]:
                execution_tasks.append(self.execute_task(task))

            if execution_tasks:
                results = await asyncio.gather(*execution_tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.error(f"Task execution exception: {result}")
                    elif isinstance(result, AgentExecution):
                        if result.status == AgentStatus.COMPLETED:
                            completed_count += 1
                        else:
                            failed_count += 1

            # Add remaining ready tasks back to queue for next iteration
            if len(ready_tasks) > self.max_parallel:
                self.task_queue.extend(ready_tasks[self.max_parallel :])
                self.task_queue.sort(key=lambda t: t.priority, reverse=True)

        summary = {
            "iterations": iterations,
            "tasks_completed": completed_count,
            "tasks_failed": failed_count,
            "tasks_remaining": len(self.task_queue),
            "active_executions": len(self.active_executions),
            "worktree_stats": self.worktree_manager.get_stats(),
        }

        logger.info(f"Parallel execution completed: {summary}")
        return summary

    def _are_dependencies_satisfied(self, task: AgentTask) -> bool:
        """Check if all task dependencies are satisfied."""
        for dep_task_id in task.dependencies:
            if dep_task_id not in self.completed_tasks:
                return False
            if self.completed_tasks[dep_task_id].status != AgentStatus.COMPLETED:
                return False
        return True

    async def send_message(self, from_agent: str, to_agent: str, message: Dict[str, Any]) -> None:
        """
        Send a message between agents via the message bus.

        Args:
            from_agent: Source agent identifier
            to_agent: Target agent identifier
            message: Message content
        """
        if to_agent not in self.message_bus:
            self.message_bus[to_agent] = []

        message["from"] = from_agent
        message["timestamp"] = datetime.now().isoformat()
        message["message_id"] = str(uuid.uuid4())

        self.message_bus[to_agent].append(message)
        logger.debug(f"Message sent from {from_agent} to {to_agent}")

    async def get_messages(self, agent: str) -> List[Dict[str, Any]]:
        """
        Get messages for an agent from the message bus.

        Args:
            agent: Agent identifier

        Returns:
            List of messages for the agent
        """
        messages = self.message_bus.get(agent, [])
        self.message_bus[agent] = []  # Clear after reading
        return messages

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator statistics."""
        stats = {
            "agent_definitions": len(self.agent_definitions),
            "active_executions": len(self.active_executions),
            "queued_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "max_parallel": self.max_parallel,
            "worktree_stats": self.worktree_manager.get_stats(),
            "message_bus_size": sum(len(messages) for messages in self.message_bus.values()),
            "agent_types": [agent_type.value for agent_type in self.agent_definitions.keys()],
        }

        # Add enforcement statistics
        try:
            enforcement_stats = self.enforcement_engine.get_enforcement_stats()
            stats["enforcement"] = enforcement_stats
        except Exception as e:
            logger.warning(f"Failed to get enforcement stats: {e}")
            stats["enforcement"] = {"error": str(e)}

        return stats

    async def get_mcp_service_recommendations(
        self, workflow_name: str = None, context: str = None
    ) -> Dict[str, Any]:
        """
        Get MCP service recommendations for enhanced development workflows.

        Args:
            workflow_name: Optional workflow name (e.g., 'multi_agent_coordination')
            context: Optional development context (e.g., 'debugging', 'project_switching')

        Returns:
            MCP service recommendations and guidance
        """
        try:
            # Detect available MCP services
            await self.mcp_detector.detect_available_services()

            recommendations = {
                "orchestrator_guidance": self.mcp_detector.generate_orchestrator_guidance(),
                "available_services": len(self.mcp_detector.available_services),
                "detection_timestamp": datetime.now().isoformat(),
            }

            if workflow_name:
                recommendations["workflow_recommendations"] = (
                    self.mcp_detector.get_workflow_recommendations(workflow_name)
                )
                logger.info(f"Generated MCP recommendations for workflow: {workflow_name}")

            if context:
                context_services = self.mcp_detector.get_service_for_context(context)
                recommendations["context_services"] = [
                    {
                        "name": service.name,
                        "tools": service.available_tools,
                        "usage": service.usage_context,
                    }
                    for service in context_services
                ]
                logger.info(f"Generated MCP recommendations for context: {context}")

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get MCP service recommendations: {e}")
            return {
                "error": str(e),
                "available_services": 0,
                "orchestrator_guidance": {
                    "status": "error",
                    "message": f"Failed to detect MCP services: {e}",
                },
            }

    async def enhance_task_with_mcp_services(self, task: AgentTask) -> AgentTask:
        """
        Enhance a task with available MCP service integrations.

        Args:
            task: Original task to enhance

        Returns:
            Enhanced task with MCP service context
        """
        try:
            # Get workflow-specific recommendations
            workflow_recommendations = await self.get_mcp_service_recommendations(
                workflow_name="multi_agent_coordination"
            )

            # Add MCP context to task
            if "workflow_recommendations" in workflow_recommendations:
                task.context["mcp_services"] = workflow_recommendations["workflow_recommendations"]
                task.context["mcp_guidance"] = workflow_recommendations["orchestrator_guidance"]

                logger.info(f"Enhanced task {task.task_id} with MCP service context")

            return task

        except Exception as e:
            logger.warning(f"Failed to enhance task with MCP services: {e}")
            return task

    async def get_development_context_services(self, context: str) -> List[Dict[str, Any]]:
        """
        Get MCP services relevant for a specific development context.

        Args:
            context: Development context (e.g., 'debugging', 'complex_task_start', 'project_switching')

        Returns:
            List of relevant MCP services with usage suggestions
        """
        try:
            context_services = self.mcp_detector.get_service_for_context(context)

            return [
                {
                    "service_name": service.name,
                    "service_type": service.service_type.value,
                    "available_tools": service.available_tools,
                    "capabilities": service.capabilities,
                    "usage_suggestions": service.usage_context,
                    "recommended_for_context": context,
                }
                for service in context_services
            ]

        except Exception as e:
            logger.error(f"Failed to get context services for {context}: {e}")
            return []

    async def check_mcp_service_availability(self) -> Dict[str, Any]:
        """
        Check the current availability status of MCP services.

        Returns:
            Detailed status of MCP service availability
        """
        try:
            services = await self.mcp_detector.detect_available_services(force_refresh=True)

            status = {
                "total_services_detected": len(services),
                "services": {},
                "orchestrator_ready": len(services) > 0,
                "last_check": datetime.now().isoformat(),
            }

            for service_id, service in services.items():
                status["services"][service_id] = {
                    "name": service.name,
                    "type": service.service_type.value,
                    "available": service.is_available,
                    "tools": service.available_tools,
                    "capabilities": service.capabilities,
                }

            if len(services) == 0:
                status["recommendation"] = (
                    "Consider installing MCP-Zen or Context 7 for enhanced workflows"
                )
            else:
                status["recommendation"] = (
                    f"Orchestrator enhanced with {len(services)} MCP services"
                )

            return status

        except Exception as e:
            logger.error(f"Failed to check MCP service availability: {e}")
            return {
                "error": str(e),
                "total_services_detected": 0,
                "orchestrator_ready": False,
                "recommendation": "Unable to detect MCP services",
            }

    def get_mcp_integration_status(self) -> Dict[str, Any]:
        """
        Get the current MCP integration status for the orchestrator.

        Returns:
            Current MCP integration status and statistics
        """
        try:
            return {
                "mcp_detector_initialized": self.mcp_detector is not None,
                "known_services": len(self.mcp_detector.known_services),
                "available_services": len(self.mcp_detector.available_services),
                "workflow_integrations": len(self.mcp_detector.workflow_integrations),
                "cache_timeout": self.mcp_detector.detection_cache_timeout,
                "last_detection": self.mcp_detector.last_detection_time,
                "integration_features": [
                    "Automatic service detection",
                    "Workflow-specific recommendations",
                    "Context-aware service suggestions",
                    "Task enhancement with MCP context",
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get MCP integration status: {e}")
            return {"error": str(e), "mcp_detector_initialized": False}

    async def cleanup(self) -> None:
        """Cleanup orchestrator resources."""
        try:
            # Cancel any active executions
            for execution in self.active_executions.values():
                execution.status = AgentStatus.TERMINATED

            # Cleanup unused worktrees
            self.worktree_manager.cleanup_unused_worktrees()

            logger.info("MultiAgentOrchestrator cleanup completed")
        except Exception as e:
            logger.error(f"Error during orchestrator cleanup: {e}")


# Factory function
async def create_multi_agent_orchestrator(
    base_repo_path: str, memory: ClaudePMMemory, max_parallel: int = 5
) -> MultiAgentOrchestrator:
    """
    Create and initialize a multi-agent orchestrator.

    Args:
        base_repo_path: Path to the base git repository
        memory: ClaudePMMemory instance
        max_parallel: Maximum parallel executions

    Returns:
        Initialized MultiAgentOrchestrator
    """
    orchestrator = MultiAgentOrchestrator(base_repo_path, memory, max_parallel)
    return orchestrator
