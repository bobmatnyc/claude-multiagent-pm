"""
Model Context Protocol (MCP) Integration Module.

This module provides a bridge between MCP tools and the Claude PM Framework's
memory-driven context management system.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Import from the existing mem0 context manager
from ..services.mem0_context_manager import (
    Mem0ContextManager,
    ContextRequest,
    ContextBundle,
    ContextType,
    ContextScope,
    create_mem0_context_manager,
)
from ..services.claude_pm_memory import ClaudePMMemory, MemoryCategory
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class MCPContextBridge:
    """
    Bridge between MCP tools and Claude PM Framework context management.

    This class provides the interface that MCP tools expect while delegating
    to the existing mem0 context management system.
    """

    def __init__(self, memory: Optional[ClaudePMMemory] = None):
        """
        Initialize the MCP context bridge.

        Args:
            memory: Optional ClaudePMMemory instance. If None, will create a new one.
        """
        self.memory = memory or self._create_memory_instance()
        self.context_manager = create_mem0_context_manager(self.memory)
        self._initialized = False

        logger.info("MCPContextBridge initialized")

    def _create_memory_instance(self) -> ClaudePMMemory:
        """Create a new ClaudePMMemory instance with default configuration."""
        try:
            from ..services.claude_pm_memory import create_claude_pm_memory

            return create_claude_pm_memory()
        except Exception as e:
            logger.error(f"Failed to create memory instance: {e}")
            raise RuntimeError(f"Could not initialize memory system: {e}")

    async def initialize(self) -> bool:
        """
        Initialize the MCP context bridge.

        Returns:
            bool: True if initialization was successful
        """
        try:
            # Initialize the underlying memory system
            # ClaudePMMemory uses connect() instead of initialize()
            if hasattr(self.memory, "connect"):
                await self.memory.connect()
            elif hasattr(self.memory, "initialize"):
                await self.memory.initialize()
            # If neither method exists, assume it's already initialized

            self._initialized = True
            logger.info("MCP context bridge initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP context bridge: {e}")
            return False

    async def prepare_context(
        self,
        context_type: str = "agent_task",
        agent_type: Optional[str] = None,
        project_name: Optional[str] = None,
        task_description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        max_memories: int = 20,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Prepare context for MCP tools.

        Args:
            context_type: Type of context to prepare
            agent_type: Type of agent requesting context
            project_name: Project being worked on
            task_description: Description of the task
            keywords: Keywords for context search
            max_memories: Maximum number of memories to return
            **kwargs: Additional parameters

        Returns:
            Dict containing prepared context data
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Convert string context_type to ContextType enum
            ctx_type = ContextType.AGENT_TASK
            if context_type == "code_review":
                ctx_type = ContextType.CODE_REVIEW
            elif context_type == "architecture_decision":
                ctx_type = ContextType.ARCHITECTURE_DECISION
            elif context_type == "debugging_session":
                ctx_type = ContextType.DEBUGGING_SESSION
            elif context_type == "pattern_matching":
                ctx_type = ContextType.PATTERN_MATCHING
            elif context_type == "project_initialization":
                ctx_type = ContextType.PROJECT_INITIALIZATION

            # Create context request
            request = ContextRequest(
                context_type=ctx_type,
                scope=(
                    ContextScope.PROJECT_SPECIFIC if project_name else ContextScope.GLOBAL_PATTERNS
                ),
                project_name=project_name,
                agent_type=agent_type,
                task_description=task_description,
                keywords=keywords or [],
                max_memories=max_memories,
            )

            # Get context from the context manager
            bundle = await self.context_manager.prepare_context(request)

            # Convert to MCP-compatible format
            return self._convert_bundle_to_mcp_format(bundle)

        except Exception as e:
            logger.error(f"Failed to prepare context: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": {},
                "memories": [],
                "summary": f"Error preparing context: {str(e)}",
            }

    def _convert_bundle_to_mcp_format(self, bundle: ContextBundle) -> Dict[str, Any]:
        """
        Convert ContextBundle to MCP-compatible format.

        Args:
            bundle: ContextBundle from context manager

        Returns:
            Dict in MCP-compatible format
        """
        return {
            "success": True,
            "context_id": bundle.context_id,
            "prepared_at": bundle.prepared_at.isoformat(),
            "context": {
                "type": bundle.request.context_type.value,
                "scope": bundle.request.scope.value,
                "project": bundle.request.project_name,
                "agent_type": bundle.request.agent_type,
                "task_description": bundle.request.task_description,
                "total_memories": bundle.total_memories,
                "preparation_time_ms": bundle.preparation_time_ms,
            },
            "memories": {
                "by_category": bundle.memories_by_category,
                "patterns": bundle.patterns,
                "team_standards": bundle.team_standards,
                "historical_errors": bundle.historical_errors,
                "project_decisions": bundle.project_decisions,
            },
            "scoring": {"relevance_scores": bundle.relevance_scores},
            "metadata": {
                "security_level": bundle.security_level,
                "team_access_level": bundle.team_access_level,
                "context_filters_applied": bundle.context_filters_applied,
                "project_history": bundle.project_history,
                "pattern_insights": bundle.pattern_insights,
            },
            "summary": bundle.context_summary,
        }

    async def get_agent_context(
        self, agent_type: str, project_name: str, task_description: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Get context specifically for an agent task.

        Args:
            agent_type: Type of agent requesting context
            project_name: Project being worked on
            task_description: Description of the task
            **kwargs: Additional parameters

        Returns:
            Dict containing agent-specific context
        """
        return await self.prepare_context(
            context_type="agent_task",
            agent_type=agent_type,
            project_name=project_name,
            task_description=task_description,
            **kwargs,
        )

    async def get_code_review_context(
        self, project_name: str, files_changed: List[str], **kwargs
    ) -> Dict[str, Any]:
        """
        Get context for code review.

        Args:
            project_name: Project being reviewed
            files_changed: List of files that changed
            **kwargs: Additional parameters

        Returns:
            Dict containing code review context
        """
        return await self.prepare_context(
            context_type="code_review",
            project_name=project_name,
            keywords=["code_review", "quality", "standards"] + files_changed,
            **kwargs,
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get context bridge statistics.

        Returns:
            Dict containing statistics
        """
        if not self._initialized:
            return {"initialized": False}

        try:
            stats = self.context_manager.get_context_stats()
            stats["initialized"] = self._initialized
            stats["mcp_bridge_version"] = "1.0.0"
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"initialized": self._initialized, "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the MCP context bridge.

        Returns:
            Dict containing health status
        """
        health_data = {
            "status": "healthy",
            "initialized": self._initialized,
            "timestamp": datetime.now().isoformat(),
            "checks": {},
        }

        try:
            # Check memory system
            if self.memory:
                health_data["checks"]["memory"] = {"status": "healthy"}
            else:
                health_data["checks"]["memory"] = {
                    "status": "unhealthy",
                    "error": "No memory instance",
                }
                health_data["status"] = "unhealthy"

            # Check context manager
            if self.context_manager:
                stats = self.context_manager.get_context_stats()
                health_data["checks"]["context_manager"] = {
                    "status": "healthy",
                    "cached_contexts": stats.get("cached_contexts", 0),
                    "agent_roles_supported": stats.get("agent_roles_supported", 0),
                }
            else:
                health_data["checks"]["context_manager"] = {
                    "status": "unhealthy",
                    "error": "No context manager",
                }
                health_data["status"] = "unhealthy"

            # Test basic functionality
            test_context = await self.prepare_context(
                context_type="agent_task",
                agent_type="test",
                task_description="health check test",
                max_memories=1,
            )

            if test_context.get("success", False):
                health_data["checks"]["functionality"] = {"status": "healthy"}
            else:
                health_data["checks"]["functionality"] = {
                    "status": "unhealthy",
                    "error": test_context.get("error", "Unknown error"),
                }
                health_data["status"] = "unhealthy"

        except Exception as e:
            health_data["status"] = "unhealthy"
            health_data["error"] = str(e)
            logger.error(f"Health check failed: {e}")

        return health_data


# Global instance for MCP tools
_mcp_context_bridge: Optional[MCPContextBridge] = None


def get_mcp_context_bridge() -> MCPContextBridge:
    """
    Get the global MCP context bridge instance.

    Returns:
        MCPContextBridge instance
    """
    global _mcp_context_bridge
    if _mcp_context_bridge is None:
        _mcp_context_bridge = MCPContextBridge()
    return _mcp_context_bridge


# Convenience functions for MCP tools
async def prepare_agent_context(
    agent_type: str, project_name: str, task_description: str, **kwargs
) -> Dict[str, Any]:
    """
    Prepare context for an agent task.

    Args:
        agent_type: Type of agent requesting context
        project_name: Project being worked on
        task_description: Description of the task
        **kwargs: Additional parameters

    Returns:
        Dict containing prepared context
    """
    bridge = get_mcp_context_bridge()
    return await bridge.get_agent_context(agent_type, project_name, task_description, **kwargs)


async def prepare_code_review_context(
    project_name: str, files_changed: List[str], **kwargs
) -> Dict[str, Any]:
    """
    Prepare context for code review.

    Args:
        project_name: Project being reviewed
        files_changed: List of files that changed
        **kwargs: Additional parameters

    Returns:
        Dict containing code review context
    """
    bridge = get_mcp_context_bridge()
    return await bridge.get_code_review_context(project_name, files_changed, **kwargs)


async def get_context_stats() -> Dict[str, Any]:
    """
    Get context system statistics.

    Returns:
        Dict containing statistics
    """
    bridge = get_mcp_context_bridge()
    return bridge.get_stats()


async def health_check() -> Dict[str, Any]:
    """
    Perform health check on the context system.

    Returns:
        Dict containing health status
    """
    bridge = get_mcp_context_bridge()
    return await bridge.health_check()


# Module-level initialization
def initialize_mcp_context() -> bool:
    """
    Initialize the MCP context system.

    Returns:
        bool: True if initialization was successful
    """
    try:
        bridge = get_mcp_context_bridge()
        # Note: This is a synchronous wrapper, actual initialization happens async
        return True
    except Exception as e:
        logger.error(f"Failed to initialize MCP context system: {e}")
        return False


# Export main interfaces
__all__ = [
    "MCPContextBridge",
    "get_mcp_context_bridge",
    "prepare_agent_context",
    "prepare_code_review_context",
    "get_context_stats",
    "health_check",
    "initialize_mcp_context",
]
