"""
Root-level utils package for MCP compatibility.

This package provides direct access to the claude_pm.utils functionality
for MCP tools that expect imports from 'utils.model_context'.
"""

# Re-export all utilities from the main package
from claude_pm.utils import *

# Import framework detection utilities
from .framework_detection import (
    is_framework_source_directory,
    ensure_not_framework_source,
    ensure_is_framework_source
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
    "TreeSitterAnalyzer",
    "analyze_file",
    "analyze_directory",
    # Framework detection utilities
    "is_framework_source_directory",
    "ensure_not_framework_source",
    "ensure_is_framework_source"
]