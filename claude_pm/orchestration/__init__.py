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

__all__ = [
    'OrchestrationDetector',
    'SimpleMessageBus',
    'Message',
    'Request',
    'Response',
    'MessageStatus'
]