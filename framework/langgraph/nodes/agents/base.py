"""
Base agent node implementation for LangGraph workflows.

Provides the foundation class for all agent nodes with memory integration,
parallel execution support, and standardized interfaces.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypedDict
from datetime import datetime
from dataclasses import dataclass

from ..states.base import TaskState, AgentMessage
from ...core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AgentExecutionContext:
    """Execution context for agent nodes."""
    agent_id: str
    role: str
    workflow_id: str
    task_description: str
    memory_context: Dict[str, Any]
    assigned_agents: List[str]
    worktree_context: Optional[Any] = None  # WorktreeContext when using parallel execution
    execution_start: datetime = None
    

class AgentNodeResult(TypedDict):
    """Standardized result format for agent nodes."""
    status: str
    agent_id: str
    role: str
    content: str
    metadata: Dict[str, Any]
    execution_time_ms: int
    confidence: float
    citations: List[str]
    errors: List[Dict[str, Any]]


class BaseAgentNode(ABC):
    """
    Base class for all agent nodes in the Claude PM Framework.
    
    Provides common functionality including:
    - Memory integration patterns
    - Standardized execution interface
    - Error handling and logging
    - Performance metrics
    - State management
    """
    
    def __init__(self, 
                 agent_id: str, 
                 role: str,
                 memory_client=None,
                 config: Optional[Dict] = None):
        """
        Initialize base agent node.
        
        Args:
            agent_id: Unique identifier for this agent instance
            role: Agent role (orchestrator, architect, engineer, etc.)
            memory_client: Optional mem0AI client for memory operations
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.role = role
        self.memory_client = memory_client
        self.config = config or {}
        
        # Performance tracking
        self._execution_count = 0
        self._total_execution_time = 0
        self._last_execution_time = None
        
    async def __call__(self, state: TaskState) -> Dict[str, Any]:
        """
        Main entry point for agent execution.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict containing state updates from agent execution
        """
        execution_context = self._create_execution_context(state)
        start_time = time.time()
        
        try:
            logger.info(f"Agent {self.agent_id} ({self.role}) starting execution")
            
            # Load memory context
            await self._load_memory_context(execution_context)
            
            # Execute agent-specific logic
            result = await self._execute_agent_logic(execution_context, state)
            
            # Store memory if successful
            await self._store_memory_context(execution_context, result)
            
            # Update performance metrics
            execution_time = int((time.time() - start_time) * 1000)
            self._update_performance_metrics(execution_time)
            
            # Return state updates
            return self._format_state_updates(execution_context, result, execution_time)
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Agent {self.agent_id} execution failed: {e}")
            
            return self._format_error_response(execution_context, e, execution_time)
    
    @abstractmethod
    async def _execute_agent_logic(self, 
                                 context: AgentExecutionContext, 
                                 state: TaskState) -> AgentNodeResult:
        """
        Execute agent-specific logic.
        
        This method must be implemented by each agent type to provide
        their specific functionality.
        
        Args:
            context: Execution context with memory and configuration
            state: Current workflow state
            
        Returns:
            AgentNodeResult with agent's output
        """
        pass
    
    def _create_execution_context(self, state: TaskState) -> AgentExecutionContext:
        """Create execution context from workflow state."""
        return AgentExecutionContext(
            agent_id=self.agent_id,
            role=self.role,
            workflow_id=state["id"],
            task_description=state["task_description"],
            memory_context=state.get("memory_context", {}),
            assigned_agents=state.get("assigned_agents", []),
            execution_start=datetime.now()
        )
    
    async def _load_memory_context(self, context: AgentExecutionContext) -> None:
        """
        Load relevant memory context for this agent execution.
        
        Args:
            context: Execution context to populate with memory data
        """
        if not self.memory_client:
            return
            
        try:
            # Search for relevant memories based on task and agent role
            memories = await self._search_relevant_memories(
                context.task_description, 
                context.role
            )
            context.memory_context.update({
                "relevant_memories": memories,
                "agent_role_patterns": await self._get_role_patterns(context.role),
                "task_patterns": await self._get_task_patterns(context.task_description)
            })
            
        except Exception as e:
            logger.warning(f"Memory context loading failed for {self.agent_id}: {e}")
    
    async def _store_memory_context(self, 
                                  context: AgentExecutionContext, 
                                  result: AgentNodeResult) -> None:
        """
        Store execution results and patterns in memory.
        
        Args:
            context: Execution context
            result: Agent execution result to store
        """
        if not self.memory_client or result["status"] != "completed":
            return
            
        try:
            # Store execution pattern
            await self._store_execution_pattern(context, result)
            
            # Store successful approaches
            if result["confidence"] > 0.7:
                await self._store_successful_pattern(context, result)
                
        except Exception as e:
            logger.warning(f"Memory storage failed for {self.agent_id}: {e}")
    
    async def _search_relevant_memories(self, 
                                      task_description: str, 
                                      role: str) -> List[Dict]:
        """
        Search for memories relevant to current task and role.
        
        Args:
            task_description: Current task description
            role: Agent role
            
        Returns:
            List of relevant memory objects
        """
        # Placeholder - implement with actual mem0AI search
        return []
    
    async def _get_role_patterns(self, role: str) -> List[Dict]:
        """Get successful patterns for this agent role."""
        # Placeholder - implement with mem0AI pattern retrieval
        return []
    
    async def _get_task_patterns(self, task_description: str) -> List[Dict]:
        """Get successful patterns for similar tasks."""
        # Placeholder - implement with mem0AI pattern retrieval
        return []
    
    async def _store_execution_pattern(self, 
                                     context: AgentExecutionContext, 
                                     result: AgentNodeResult) -> None:
        """Store execution pattern in memory."""
        # Placeholder - implement with mem0AI storage
        pass
    
    async def _store_successful_pattern(self, 
                                      context: AgentExecutionContext, 
                                      result: AgentNodeResult) -> None:
        """Store successful execution pattern."""
        # Placeholder - implement with mem0AI storage
        pass
    
    def _update_performance_metrics(self, execution_time_ms: int) -> None:
        """Update internal performance metrics."""
        self._execution_count += 1
        self._total_execution_time += execution_time_ms
        self._last_execution_time = execution_time_ms
    
    def _format_state_updates(self, 
                             context: AgentExecutionContext,
                             result: AgentNodeResult, 
                             execution_time_ms: int) -> Dict[str, Any]:
        """
        Format agent result into state updates.
        
        Args:
            context: Execution context
            result: Agent execution result
            execution_time_ms: Execution duration
            
        Returns:
            Dictionary of state updates for the workflow
        """
        # Create agent message
        agent_message = {
            "agent_id": result["agent_id"],
            "role": result["role"],
            "content": result["content"],
            "confidence": result["confidence"],
            "citations": result["citations"],
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                **result["metadata"],
                "execution_time_ms": execution_time_ms
            }
        }
        
        # Prepare state updates
        state_updates = {
            "messages": [agent_message],
            "metadata": {
                f"{self.role}_execution_time": execution_time_ms,
                f"{self.role}_confidence": result["confidence"]
            }
        }
        
        # Add role-specific results
        if result["status"] == "completed":
            state_updates["results"] = {
                self.role: result["metadata"]
            }
        
        # Add errors if any
        if result["errors"]:
            state_updates["errors"] = result["errors"]
        
        return state_updates
    
    def _format_error_response(self, 
                              context: AgentExecutionContext,
                              error: Exception, 
                              execution_time_ms: int) -> Dict[str, Any]:
        """
        Format error into state updates.
        
        Args:
            context: Execution context
            error: Exception that occurred
            execution_time_ms: Execution duration
            
        Returns:
            Dictionary of state updates for error handling
        """
        error_info = {
            "type": f"{self.role}_error",
            "message": str(error),
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "execution_time_ms": execution_time_ms
        }
        
        return {
            "errors": [error_info],
            "messages": [{
                "agent_id": self.agent_id,
                "role": self.role,
                "content": f"Execution failed: {str(error)}",
                "confidence": 0.0,
                "citations": [],
                "timestamp": datetime.now().isoformat(),
                "metadata": {"error": True}
            }]
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this agent."""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "execution_count": self._execution_count,
            "total_execution_time_ms": self._total_execution_time,
            "average_execution_time_ms": (
                self._total_execution_time / self._execution_count 
                if self._execution_count > 0 else 0
            ),
            "last_execution_time_ms": self._last_execution_time
        }