"""
Model Context Protocol (MCP) Integration Module - Root Level.

This module provides direct access to the claude_pm.utils.model_context functionality
for MCP tools that expect imports from 'utils.model_context'.
"""

# Re-export all model_context functionality from the main package
from claude_pm.utils.model_context import *

__all__ = [
    "MCPContextBridge",
    "get_mcp_context_bridge",
    "prepare_agent_context",
    "prepare_code_review_context",
    "get_context_stats",
    "health_check",
    "initialize_mcp_context"
]