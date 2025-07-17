"""
Claude PM Orchestration Package

This package contains components for detecting and managing local project orchestration.
"""

from .orchestration_detector import OrchestrationDetector
from .message_bus import (
    SimpleMessageBus,
    Message,
    Request,
    Response,
    MessageStatus
)
from .context_manager import (
    ContextManager,
    ContextFilter,
    AgentInteraction,
    create_context_manager
)

__all__ = [
    'OrchestrationDetector',
    'SimpleMessageBus',
    'Message',
    'Request',
    'Response',
    'MessageStatus',
    'ContextManager',
    'ContextFilter',
    'AgentInteraction',
    'create_context_manager'
]