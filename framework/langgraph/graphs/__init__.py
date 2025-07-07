"""
Graph definitions for LangGraph workflows.

Provides pre-built workflow graphs for common Claude PM operations:
- TaskWorkflowGraph: Single task execution with agent coordination
- ProjectWorkflowGraph: Project-level milestone management
- CodeReviewWorkflowGraph: Parallel code review with multiple agents
"""

from .task_graph import TaskWorkflowGraph

# Only import other graphs if they exist
try:
    from .project_graph import ProjectWorkflowGraph
except ImportError:
    ProjectWorkflowGraph = None

try:
    from .review_graph import CodeReviewWorkflowGraph
except ImportError:
    CodeReviewWorkflowGraph = None

__all__ = [
    "TaskWorkflowGraph"
]

# Add to __all__ only if successfully imported
if ProjectWorkflowGraph:
    __all__.append("ProjectWorkflowGraph")
if CodeReviewWorkflowGraph:
    __all__.append("CodeReviewWorkflowGraph")