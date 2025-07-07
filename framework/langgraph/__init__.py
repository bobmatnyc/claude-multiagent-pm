"""
LangGraph Integration for Claude PM Framework.

This module provides the foundation for state-based workflow orchestration
using LangGraph, with integration to Claude PM's memory system and multi-agent
architecture.

Key Components:
- States: Base state management for workflows
- Nodes: Agent nodes for workflow execution
- Graphs: Workflow graph definitions
- Routers: Conditional routing logic
- Utils: Utilities for checkpointing, visualization, metrics
"""

from .states.base import BaseState, TaskState, ProjectState

# Import TaskWorkflowGraph only if needed
try:
    from .graphs.task_graph import TaskWorkflowGraph
    _TASK_WORKFLOW_AVAILABLE = True
except ImportError:
    _TASK_WORKFLOW_AVAILABLE = False
    TaskWorkflowGraph = None

__all__ = [
    "BaseState",
    "TaskState", 
    "ProjectState",
    "TaskWorkflowGraph"
]

__version__ = "1.0.0"