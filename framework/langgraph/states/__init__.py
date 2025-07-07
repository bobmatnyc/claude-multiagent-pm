"""
State management for LangGraph workflows.

Provides TypedDict-based state classes for workflow orchestration:
- BaseState: Common fields for all workflows
- TaskState: Task-level workflow state
- ProjectState: Project-level workflow state
"""

from .base import BaseState, TaskState, ProjectState, AgentMessage

__all__ = ["BaseState", "TaskState", "ProjectState", "AgentMessage"]