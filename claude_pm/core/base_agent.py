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

    async def get_pm_notifications(self) -> List[Dict[str, Any]]:
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

    async def enable_pm_collaboration(self) -> Dict[str, Any]:
        """Enable PM collaboration mode."""
        self.pm_collaboration_enabled = True
        return {"collaboration_enabled": True}

    async def disable_pm_collaboration(self) -> Dict[str, Any]:
        """Disable PM collaboration mode."""
        self.pm_collaboration_enabled = False
        return {"collaboration_enabled": False}

    async def get_collaboration_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get collaboration history with PM."""
        if limit:
            return self.collaboration_history[-limit:]
        return self.collaboration_history

    async def get_agent_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    async def validate_capability(self, capability: str) -> bool:
        """Validate if agent has a specific capability."""
        return capability in self.capabilities

    async def add_capability(self, capability: str) -> Dict[str, Any]:
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

    async def remove_capability(self, capability: str) -> Dict[str, Any]:
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
        }

        return {**base_metrics, **agent_metrics}

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id='{self.agent_id}', type='{self.agent_type}', tier='{self.tier}')"

    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return f"<{self.__class__.__name__} id='{self.agent_id}' type='{self.agent_type}' tier='{self.tier}' running={self.running}>"
