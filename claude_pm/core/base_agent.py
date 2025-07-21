"""
Base Agent class for Claude PM Framework agents.

Provides common functionality for all agent types including:
- Agent lifecycle management
- Communication interfaces
- Memory integration
- Three-tier hierarchy support
- Performance monitoring
"""

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

from .base_service import BaseService
from .config import Config
# Memory system removed - use fallback MemoryCategory locally

# Temporary fallback for MemoryCategory
class MemoryCategory:
    """Temporary fallback MemoryCategory class while memory system is disabled"""
    PROJECT = "project"
    ISSUE = "issue" 
    DECISION = "decision"
    ERROR = "error"
    WORKFLOW = "workflow"
    BUG = "bug"
    USER_FEEDBACK = "user_feedback"
    SYSTEM = "system"


class BaseAgent(BaseService, ABC):
    """
    Abstract base class for all Claude PM agents.

    Provides common infrastructure for agent lifecycle management,
    communication, memory integration, and hierarchy management.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        config: Optional[Dict[str, Any]] = None,
        tier: str = "system",
    ):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (e.g., 'documentation', 'ticketing')
            capabilities: List of agent capabilities
            config: Optional configuration dictionary
            tier: Agent tier (system, user, project)
        """
        super().__init__(name=agent_id, config=config)

        # Agent identity
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.tier = tier
        self.capabilities = capabilities

        # Agent hierarchy information
        self.priority = self._get_tier_priority(tier)
        self.authority_level = self._get_authority_level(tier)

        # Agent state
        self.operations_count = 0
        self.last_operation_time = None
        self.collaboration_history = []

        # PM collaboration interface
        self.pm_collaboration_enabled = True
        self.pm_notification_queue = []

        # Memory integration removed from framework
        if "memory_integration" not in self.capabilities:
            self.capabilities.append("memory_integration")

        self.logger.info(f"Initialized {agent_type} agent: {agent_id} (tier: {tier})")

    def _get_tier_priority(self, tier: str) -> int:
        """Get priority based on tier (lower number = higher priority)."""
        tier_priorities = {
            "project": 1,  # Highest priority
            "user": 2,  # Medium priority
            "system": 3,  # Lowest priority (fallback)
        }
        return tier_priorities.get(tier, 3)

    def _get_authority_level(self, tier: str) -> str:
        """Get authority level based on tier."""
        authority_levels = {"project": "override", "user": "customize", "system": "fallback"}
        return authority_levels.get(tier, "fallback")

    @property
    def agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "tier": self.tier,
            "priority": self.priority,
            "authority_level": self.authority_level,
            "running": self.running,
            "uptime": self.uptime,
            "capabilities": self.capabilities,
            "operations_count": self.operations_count,
            "last_operation": (
                self.last_operation_time.isoformat() if self.last_operation_time else None
            ),
            "collaboration_enabled": self.pm_collaboration_enabled,
            "pending_notifications": len(self.pm_notification_queue),
            "memory_enabled": self.memory_enabled,
            "memory_service_connected": self.memory_service is not None,
            "memory_project": self.memory_project_name,
        }

    # Memory Integration Methods
    
    async def enable_memory_integration(self, memory_service) -> Dict[str, Any]:
        """
        Enable memory integration for the agent.
        
        Args:
            memory_service: Memory service instance
            
        Returns:
            Dict[str, Any]: Integration status
        """
        try:
            self.memory_service = memory_service
            self.memory_enabled = True
            
            self.logger.info(f"Memory integration enabled for {self.agent_type} agent: {self.agent_id}")
            
            return {
                "success": True,
                "memory_enabled": True,
                "memory_service_connected": True,
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to enable memory integration: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_enabled": False,
                "memory_service_connected": False
            }
    
    def disable_memory_integration(self) -> Dict[str, Any]:
        """
        Disable memory integration for the agent.
        
        Returns:
            Dict[str, Any]: Integration status
        """
        self.memory_service = None
        self.memory_enabled = False
        
        self.logger.info(f"Memory integration disabled for {self.agent_type} agent: {self.agent_id}")
        
        return {
            "success": True,
            "memory_enabled": False,
            "memory_service_connected": False,
            "agent_id": self.agent_id
        }
    
    async def collect_memory(
        self,
        content: str,
        category: MemoryCategory,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Collect memory for bugs, feedback, and operational insights.
        
        Args:
            content: Memory content
            category: Memory category
            metadata: Optional metadata
            tags: Optional tags
            
        Returns:
            Optional[str]: Memory ID if successful
        """
        return await self._collect_memory(content, category, metadata, tags)
    
    async def _collect_memory(
        self,
        content: str,
        category: MemoryCategory,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Internal memory collection method.
        
        Args:
            content: Memory content
            category: Memory category
            metadata: Optional metadata
            tags: Optional tags
            
        Returns:
            Optional[str]: Memory ID if successful
        """
        if not self.memory_enabled or not self.memory_service:
            self.logger.debug("Memory collection skipped - memory integration not enabled")
            return None
        
        try:
            # Enhance metadata with agent context
            enhanced_metadata = {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "tier": self.tier,
                "timestamp": datetime.now().isoformat(),
                "operations_count": self.operations_count,
                **(metadata or {})
            }
            
            # Enhance tags with agent context
            enhanced_tags = [
                f"agent:{self.agent_type}",
                f"tier:{self.tier}",
                f"agent_id:{self.agent_id}",
                *(tags or [])
            ]
            
            # Store memory if service is available
            if hasattr(self.memory_service, 'store_memory'):
                from ..services.memory.interfaces.models import MemoryItem
                import uuid
                
                memory_item = MemoryItem(
                    id=str(uuid.uuid4()),
                    content=content,
                    category=category,
                    tags=enhanced_tags,
                    metadata=enhanced_metadata,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                result = await self.memory_service.store_memory(memory_item)
                memory_id = memory_item.id if result.success else None
            else:
                self.logger.warning("Memory service does not support store_memory method")
                return None
            
            if memory_id:
                self.logger.debug(f"Memory collected: {memory_id[:8]}... for {category.value}")
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Failed to collect memory: {e}")
            return None
    
    async def collect_error_memory(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Collect memory for errors and exceptions.
        
        Args:
            error: Exception that occurred
            operation: Operation that failed
            context: Optional context information
            
        Returns:
            Optional[str]: Memory ID if successful
        """
        error_content = f"Error in {self.agent_type} agent during {operation}: {str(error)}"
        
        error_metadata = {
            "error_type": type(error).__name__,
            "operation": operation,
            "error_message": str(error),
            "context": context or {},
            "severity": "high" if isinstance(error, (MemoryError, RuntimeError)) else "medium"
        }
        
        return await self._collect_memory(
            error_content,
            MemoryCategory.BUG,
            error_metadata,
            ["error", "bug", operation]
        )
    
    async def collect_feedback_memory(
        self,
        feedback: str,
        source: str = "user",
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Collect memory for user feedback and suggestions.
        
        Args:
            feedback: Feedback content
            source: Source of feedback (user, system, agent)
            context: Optional context information
            
        Returns:
            Optional[str]: Memory ID if successful
        """
        feedback_content = f"Feedback for {self.agent_type} agent from {source}: {feedback}"
        
        feedback_metadata = {
            "feedback_source": source,
            "feedback_type": "suggestion",
            "context": context or {}
        }
        
        return await self._collect_memory(
            feedback_content,
            MemoryCategory.USER_FEEDBACK,
            feedback_metadata,
            ["feedback", source, "improvement"]
        )
    
    async def collect_performance_memory(
        self,
        operation: str,
        performance_data: Dict[str, Any],
        threshold_exceeded: bool = False
    ) -> Optional[str]:
        """
        Collect memory for performance observations.
        
        Args:
            operation: Operation that was measured
            performance_data: Performance metrics
            threshold_exceeded: Whether performance thresholds were exceeded
            
        Returns:
            Optional[str]: Memory ID if successful
        """
        performance_content = f"Performance observation for {self.agent_type} agent operation {operation}"
        
        if threshold_exceeded:
            performance_content += " - Performance threshold exceeded"
        
        performance_metadata = {
            "operation": operation,
            "performance_data": performance_data,
            "threshold_exceeded": threshold_exceeded,
            "measurement_type": "performance"
        }
        
        category = MemoryCategory.BUG if threshold_exceeded else MemoryCategory.SYSTEM
        tags = ["performance", operation]
        if threshold_exceeded:
            tags.append("slow_performance")
        
        return await self._collect_memory(
            performance_content,
            category,
            performance_metadata,
            tags
        )
    
    async def search_agent_memories(
        self,
        query: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories related to this agent.
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum results to return
            
        Returns:
            List[Dict[str, Any]]: Matching memories
        """
        if not self.memory_enabled or not self.memory_service:
            return []
        
        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return []
            
            from ..services.memory.interfaces.models import MemoryQuery
            
            # Create query with agent context
            memory_query = MemoryQuery(
                query_text=f"{query} agent:{self.agent_type}",
                category=category,
                limit=limit,
                include_metadata=True
            )
            
            memories = await memory_service.search_memories(
                project_name=self.memory_project_name,
                query=memory_query
            )
            
            # Convert to dictionaries for easier handling
            return [
                {
                    "id": memory.id,
                    "content": memory.content,
                    "category": memory.category.value,
                    "tags": memory.tags,
                    "metadata": memory.metadata,
                    "created_at": memory.created_at.isoformat() if memory.created_at else None
                }
                for memory in memories
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to search agent memories: {e}")
            return []
    
    async def get_memory_health_status(self) -> Dict[str, Any]:
        """
        Get memory system health status.
        
        Returns:
            Dict[str, Any]: Memory health information
        """
        if not self.memory_service:
            return {
                "memory_enabled": False,
                "memory_service_connected": False,
                "memory_health": "disabled"
            }
        
        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return {
                    "memory_enabled": self.memory_enabled,
                    "memory_service_connected": False,
                    "memory_health": "service_unavailable"
                }
            
            health_data = await memory_service.get_service_health()
            
            return {
                "memory_enabled": self.memory_enabled,
                "memory_service_connected": True,
                "memory_health": "healthy" if health_data.get("service_healthy") else "unhealthy",
                "active_backend": health_data.get("active_backend"),
                "memory_metrics": health_data.get("metrics", {})
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get memory health status: {e}")
            return {
                "memory_enabled": self.memory_enabled,
                "memory_service_connected": False,
                "memory_health": "error",
                "error": str(e)
            }

    async def execute_operation(
        self, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an agent operation with performance tracking.

        Args:
            operation: Operation name
            context: Optional operation context
            **kwargs: Operation parameters

        Returns:
            Operation result with metadata
        """
        operation_start = time.time()
        self.operations_count += 1
        self.last_operation_time = datetime.now()

        try:
            self.logger.info(f"Executing operation: {operation}")

            # Execute the operation
            result = await self._execute_operation(operation, context, **kwargs)

            # Record success metrics
            execution_time = time.time() - operation_start

            operation_result = {
                "success": True,
                "operation": operation,
                "result": result,
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "tier": self.tier,
                "timestamp": self.last_operation_time.isoformat(),
            }

            # Collect memory for significant operations or performance issues
            if self.memory_auto_collect and self.memory_enabled:
                # Collect performance memory if operation took too long
                if execution_time > 5.0:  # 5 second threshold
                    await self.collect_performance_memory(
                        operation,
                        {"execution_time": execution_time, "result_type": type(result).__name__},
                        threshold_exceeded=True
                    )
                
                # Collect memory for critical operations
                if operation.startswith("critical_") or operation.endswith("_complete"):
                    await self.collect_memory(
                        f"Completed operation: {operation}",
                        MemoryCategory.SYSTEM,
                        {"operation_result": operation_result, "context": context},
                        [operation, "completion"]
                    )

            # Notify PM if collaboration enabled
            if self.pm_collaboration_enabled and self._should_notify_pm(operation, result):
                await self._notify_pm(operation, operation_result)

            return operation_result

        except Exception as e:
            execution_time = time.time() - operation_start

            self.logger.error(f"Operation {operation} failed: {e}")

            error_result = {
                "success": False,
                "operation": operation,
                "error": str(e),
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "tier": self.tier,
                "timestamp": self.last_operation_time.isoformat(),
            }

            # Collect error memory automatically
            if self.memory_auto_collect and self.memory_enabled:
                await self.collect_error_memory(e, operation, context)

            # Notify PM of error if collaboration enabled
            if self.pm_collaboration_enabled:
                await self._notify_pm_error(operation, error_result)

            return error_result

    @abstractmethod
    async def _execute_operation(
        self, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Any:
        """
        Execute the specific operation. Must be implemented by subclasses.

        Args:
            operation: Operation name
            context: Optional operation context
            **kwargs: Operation parameters

        Returns:
            Operation result
        """
        pass

    async def collaborate_with_pm(
        self, message: str, context: Optional[Dict[str, Any]] = None, priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Send a collaboration message to PM.

        Args:
            message: Message to PM
            context: Optional context information
            priority: Message priority (low, normal, high, urgent)

        Returns:
            Collaboration result
        """
        collaboration_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "message": message,
            "context": context or {},
            "priority": priority,
        }

        self.collaboration_history.append(collaboration_entry)
        self.pm_notification_queue.append(collaboration_entry)

        self.logger.info(f"Collaboration message sent to PM: {message}")

        return {"success": True, "message_id": len(self.collaboration_history), "queued": True}

    def get_pm_notifications(self) -> List[Dict[str, Any]]:
        """Get pending PM notifications and clear the queue."""
        notifications = self.pm_notification_queue.copy()
        self.pm_notification_queue.clear()
        return notifications

    def _should_notify_pm(self, operation: str, result: Any) -> bool:
        """Determine if PM should be notified of operation completion."""
        # Override in subclasses for operation-specific logic
        return operation.startswith("critical_") or operation.endswith("_complete")

    async def _notify_pm(self, operation: str, result: Dict[str, Any]) -> None:
        """Notify PM of successful operation."""
        await self.collaborate_with_pm(
            f"Operation completed: {operation}",
            context={"operation_result": result},
            priority="normal",
        )

    async def _notify_pm_error(self, operation: str, error_result: Dict[str, Any]) -> None:
        """Notify PM of operation error."""
        await self.collaborate_with_pm(
            f"Operation failed: {operation} - {error_result.get('error', 'Unknown error')}",
            context={"error_result": error_result},
            priority="high",
        )

    def enable_pm_collaboration(self) -> Dict[str, Any]:
        """Enable PM collaboration mode."""
        self.pm_collaboration_enabled = True
        return {"collaboration_enabled": True}

    def disable_pm_collaboration(self) -> Dict[str, Any]:
        """Disable PM collaboration mode."""
        self.pm_collaboration_enabled = False
        return {"collaboration_enabled": False}

    def get_collaboration_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get collaboration history with PM."""
        if limit:
            return self.collaboration_history[-limit:]
        return self.collaboration_history

    def get_agent_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    def validate_capability(self, capability: str) -> bool:
        """Validate if agent has a specific capability."""
        return capability in self.capabilities

    def add_capability(self, capability: str) -> Dict[str, Any]:
        """Add a new capability to the agent."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.logger.info(f"Added capability: {capability}")
            return {"success": True, "capability": capability, "added": True}
        return {
            "success": True,
            "capability": capability,
            "added": False,
            "reason": "already_exists",
        }

    def remove_capability(self, capability: str) -> Dict[str, Any]:
        """Remove a capability from the agent."""
        if capability in self.capabilities:
            self.capabilities.remove(capability)
            self.logger.info(f"Removed capability: {capability}")
            return {"success": True, "capability": capability, "removed": True}
        return {"success": True, "capability": capability, "removed": False, "reason": "not_found"}

    async def _health_check(self) -> Dict[str, bool]:
        """Agent-specific health check."""
        checks = await super()._health_check()

        # Agent-specific health checks
        checks["capabilities_available"] = len(self.capabilities) > 0
        checks["pm_collaboration_ready"] = self.pm_collaboration_enabled
        checks["recent_activity"] = self.last_operation_time is not None
        checks["memory_integration_available"] = "memory_integration" in self.capabilities
        checks["memory_service_connected"] = self.memory_service is not None
        
        # Check memory system health if available
        if self.memory_enabled and self.memory_service:
            try:
                memory_health = await self.get_memory_health_status()
                checks["memory_system_healthy"] = memory_health.get("memory_health") == "healthy"
            except Exception:
                checks["memory_system_healthy"] = False
        else:
            checks["memory_system_healthy"] = not self.memory_enabled  # OK if disabled

        return checks

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        # Get base metrics from BaseService.metrics property
        base_metrics = {
            "requests_total": self.metrics.requests_total,
            "requests_failed": self.metrics.requests_failed,
            "response_time_avg": self.metrics.response_time_avg,
            "uptime_seconds": self.metrics.uptime_seconds,
            "memory_usage_mb": self.metrics.memory_usage_mb,
            "custom_metrics": self.metrics.custom_metrics,
        }

        # Add agent-specific metrics
        agent_metrics = {
            "operations_per_minute": self.operations_count / max((self.uptime or 1) / 60, 1),
            "collaboration_messages": len(self.collaboration_history),
            "pending_notifications": len(self.pm_notification_queue),
            "last_operation_time": (
                self.last_operation_time.isoformat() if self.last_operation_time else None
            ),
            "tier_priority": self.priority,
            "authority_level": self.authority_level,
            "memory_enabled": self.memory_enabled,
            "memory_service_connected": self.memory_service is not None,
            "memory_auto_collect": self.memory_auto_collect,
            "memory_project_name": self.memory_project_name,
        }

        # Add memory metrics if available
        if self.memory_enabled and self.memory_service:
            try:
                memory_health = await self.get_memory_health_status()
                agent_metrics["memory_health"] = memory_health.get("memory_health")
                agent_metrics["memory_metrics"] = memory_health.get("memory_metrics", {})
            except Exception as e:
                agent_metrics["memory_health"] = f"error: {e}"

        return {**base_metrics, **agent_metrics}

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id='{self.agent_id}', type='{self.agent_type}', tier='{self.tier}')"

    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return f"<{self.__class__.__name__} id='{self.agent_id}' type='{self.agent_type}' tier='{self.tier}' running={self.running}>"
