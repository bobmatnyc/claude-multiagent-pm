"""
Memory Trigger Types and Enums

Shared enums and types for the memory trigger system.
"""

from enum import Enum


class TriggerType(str, Enum):
    """Types of memory triggers supported by the orchestrator."""
    
    WORKFLOW_COMPLETION = "workflow_completion"
    ISSUE_RESOLUTION = "issue_resolution"
    AGENT_OPERATION = "agent_operation"
    ERROR_RESOLUTION = "error_resolution"
    PROJECT_MILESTONE = "project_milestone"
    KNOWLEDGE_CAPTURE = "knowledge_capture"
    PATTERN_DETECTION = "pattern_detection"
    DECISION_POINT = "decision_point"


class TriggerPriority(str, Enum):
    """Priority levels for memory triggers."""
    
    CRITICAL = "critical"      # Must be captured immediately
    HIGH = "high"             # Important operational knowledge
    MEDIUM = "medium"         # Helpful context and patterns
    LOW = "low"              # Optional background information


class PolicyDecision(str, Enum):
    """Possible policy decisions for trigger evaluation."""
    
    ALLOW = "allow"           # Allow trigger to proceed
    DENY = "deny"             # Deny trigger completely
    MODIFY = "modify"         # Allow but modify trigger properties
    DEFER = "defer"           # Defer trigger for later processing
    BATCH = "batch"           # Add to batch for bulk processing