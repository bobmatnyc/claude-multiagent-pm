"""
Claude PM Framework Utilities Package.

Contains utility classes for performance optimization, caching, resilience patterns,
and Model Context Protocol (MCP) integration.
"""

from .performance import CircuitBreaker, HealthCache, CacheEntry
from .model_context import (
    MCPContextBridge,
    get_mcp_context_bridge,
    prepare_agent_context,
    prepare_code_review_context,
    get_context_stats,
    health_check,
    initialize_mcp_context,
)

__all__ = [
    "CircuitBreaker",
    "HealthCache",
    "CacheEntry",
    "MCPContextBridge",
    "get_mcp_context_bridge",
    "prepare_agent_context",
    "prepare_code_review_context",
    "get_context_stats",
    "health_check",
    "initialize_mcp_context",
]
