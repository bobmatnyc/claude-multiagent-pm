"""
Base state definitions for LangGraph workflows.

Defines the foundation state classes that all Claude PM workflows inherit from,
providing structured typing and memory integration capabilities.
"""

from typing import TypedDict, List, Dict, Optional, Any, Annotated, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

import operator


class WorkflowStatus(Enum):
    """Status enumeration for workflow execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskComplexity(Enum):
    """Task complexity levels for routing decisions."""
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


class AgentMessage(BaseModel):
    """Structured message format for agent communication."""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    role: str = Field(..., description="Agent role (orchestrator, architect, engineer, etc.)")
    content: str = Field(..., description="Message content from the agent")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence level (0-1)")
    citations: List[str] = Field(default_factory=list, description="Sources or references")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseState(TypedDict):
    """
    Base state for all LangGraph workflows in Claude PM.
    
    Provides common fields that all workflow states inherit, including
    identification, user context, messaging, and metadata.
    """
    # Core identification
    id: str
    timestamp: datetime
    user_id: Optional[str]
    project_id: Optional[str]
    
    # Communication and context
    messages: Annotated[List[Dict[str, Any]], operator.add]
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    
    # Workflow tracking
    status: str
    errors: Annotated[List[Dict[str, Any]], operator.add]


class TaskState(BaseState):
    """
    State for task-level workflows.
    
    Extends BaseState with task-specific fields for managing individual
    task execution, complexity assessment, and agent coordination.
    """
    # Task definition
    task_description: str
    task_type: Optional[str]  # "feature", "bugfix", "refactor", etc.
    
    # Complexity and routing
    complexity: Optional[str]  # simple, standard, complex
    priority: Optional[str]    # low, medium, high, critical
    
    # Agent coordination
    assigned_agents: List[str]
    agent_assignments: Dict[str, Any]  # Agent-specific task assignments
    
    # Task decomposition
    subtasks: List[Dict[str, Any]]
    dependencies: List[str]
    
    # Execution results
    results: Dict[str, Any]
    deliverables: List[Dict[str, Any]]
    
    # Cost and estimation
    cost_estimate: Dict[str, float]
    actual_cost: Dict[str, float]
    time_estimate: Optional[int]  # minutes
    time_actual: Optional[int]    # minutes
    
    # Quality and validation
    quality_checks: Dict[str, Any]
    approval_required: bool
    approval_status: Optional[str]
    
    # Memory integration
    memory_context: Dict[str, Any]
    learned_patterns: List[Dict[str, Any]]


class ProjectState(BaseState):
    """
    State for project-level workflows.
    
    Extends BaseState with project-wide fields for managing milestones,
    team coordination, and strategic decisions.
    """
    # Project definition
    project_name: str
    project_description: Optional[str]
    project_type: Optional[str]  # "feature", "migration", "optimization", etc.
    
    # Milestone and sprint management
    milestones: List[Dict[str, Any]]
    current_milestone: Optional[str]
    current_sprint: Optional[str]
    sprint_goals: List[str]
    
    # Team and resource management
    team_members: List[str]
    available_agents: List[str]
    resource_allocation: Dict[str, Any]
    
    # Decision tracking
    decisions: List[Dict[str, Any]]
    architectural_decisions: List[Dict[str, Any]]
    
    # Progress and metrics
    metrics: Dict[str, Any]
    progress_indicators: Dict[str, float]
    
    # Budget and cost tracking
    budget_status: Dict[str, float]
    cost_breakdown: Dict[str, Dict[str, float]]
    
    # Risk and issue management
    risks: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    blockers: List[Dict[str, Any]]
    
    # Integration points
    external_dependencies: List[Dict[str, Any]]
    integration_status: Dict[str, str]
    
    # Memory and learning
    project_memory_id: Optional[str]
    learning_insights: List[Dict[str, Any]]
    success_patterns: List[Dict[str, Any]]


class CodeReviewState(BaseState):
    """
    State for code review workflows.
    
    Specialized state for orchestrating parallel code review processes
    including security, performance, style, and testing analysis.
    """
    # Code review target
    target_files: List[str]
    git_ref: Optional[str]
    change_summary: Optional[str]
    
    # Review configuration
    review_types: List[str]  # ["security", "performance", "style", "testing"]
    parallel_execution: bool
    
    # Review results
    security_review: Dict[str, Any]
    performance_review: Dict[str, Any]
    style_review: Dict[str, Any]
    testing_review: Dict[str, Any]
    
    # Aggregated results
    overall_score: Optional[float]
    critical_issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    
    # Approval workflow
    requires_human_review: bool
    reviewer_feedback: List[Dict[str, Any]]


def create_task_state(
    task_id: str,
    task_description: str,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    **kwargs
) -> TaskState:
    """
    Factory function to create a properly initialized TaskState.
    
    Args:
        task_id: Unique identifier for the task
        task_description: Description of the task to be executed
        user_id: Optional user identifier
        project_id: Optional project identifier
        **kwargs: Additional state fields to set
        
    Returns:
        TaskState: Initialized task state ready for workflow execution
    """
    base_state = TaskState(
        id=task_id,
        timestamp=datetime.now(),
        user_id=user_id,
        project_id=project_id,
        messages=[],
        context={},
        metadata={},
        status=WorkflowStatus.PENDING.value,
        errors=[],
        
        # Task-specific fields
        task_description=task_description,
        task_type=kwargs.get("task_type"),
        complexity=kwargs.get("complexity"),
        priority=kwargs.get("priority", "medium"),
        assigned_agents=[],
        agent_assignments={},
        subtasks=[],
        dependencies=[],
        results={},
        deliverables=[],
        cost_estimate={},
        actual_cost={},
        time_estimate=kwargs.get("time_estimate"),
        time_actual=None,
        quality_checks={},
        approval_required=kwargs.get("approval_required", False),
        approval_status=None,
        memory_context={},
        learned_patterns=[]
    )
    
    # Apply any additional kwargs
    for key, value in kwargs.items():
        if key in base_state:
            base_state[key] = value
    
    return base_state


def create_project_state(
    project_id: str,
    project_name: str,
    user_id: Optional[str] = None,
    **kwargs
) -> ProjectState:
    """
    Factory function to create a properly initialized ProjectState.
    
    Args:
        project_id: Unique identifier for the project
        project_name: Name of the project
        user_id: Optional user identifier
        **kwargs: Additional state fields to set
        
    Returns:
        ProjectState: Initialized project state ready for workflow execution
    """
    base_state = ProjectState(
        id=project_id,
        timestamp=datetime.now(),
        user_id=user_id,
        project_id=project_id,
        messages=[],
        context={},
        metadata={},
        status=WorkflowStatus.PENDING.value,
        errors=[],
        
        # Project-specific fields
        project_name=project_name,
        project_description=kwargs.get("project_description"),
        project_type=kwargs.get("project_type"),
        milestones=[],
        current_milestone=kwargs.get("current_milestone"),
        current_sprint=kwargs.get("current_sprint"),
        sprint_goals=[],
        team_members=[],
        available_agents=[],
        resource_allocation={},
        decisions=[],
        architectural_decisions=[],
        metrics={},
        progress_indicators={},
        budget_status={},
        cost_breakdown={},
        risks=[],
        issues=[],
        blockers=[],
        external_dependencies=[],
        integration_status={},
        project_memory_id=None,
        learning_insights=[],
        success_patterns=[]
    )
    
    # Apply any additional kwargs
    for key, value in kwargs.items():
        if key in base_state:
            base_state[key] = value
    
    return base_state