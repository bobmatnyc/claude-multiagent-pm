"""
Claude PM Orchestration Package

This package contains components for detecting and managing local project orchestration.
"""

# Initialize orchestration logging
from .logging_setup import setup_orchestration_logging
setup_orchestration_logging()

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
from .backwards_compatible_orchestrator import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode,
    OrchestrationMetrics,
    create_backwards_compatible_orchestrator,
    delegate_with_compatibility
)
from .terminal_handoff import (
    TerminalHandoffManager,
    TerminalProxy,
    HandoffRequest,
    HandoffResponse,
    HandoffSession,
    HandoffState,
    HandoffPermission
)
from .interactive_agent_base import (
    InteractiveAgentBase,
    InteractiveContext,
    SimpleInteractiveAgent
)
from .ticketing_helpers import (
    TicketingHelper,
    quick_create_task,
    quick_update_status,
    get_workload_summary
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
    'create_context_manager',
    'BackwardsCompatibleOrchestrator',
    'OrchestrationMode',
    'OrchestrationMetrics',
    'create_backwards_compatible_orchestrator',
    'delegate_with_compatibility',
    'TerminalHandoffManager',
    'TerminalProxy',
    'HandoffRequest',
    'HandoffResponse',
    'HandoffSession',
    'HandoffState',
    'HandoffPermission',
    'InteractiveAgentBase',
    'InteractiveContext',
    'SimpleInteractiveAgent',
    'TicketingHelper',
    'quick_create_task',
    'quick_update_status',
    'get_workload_summary'
]