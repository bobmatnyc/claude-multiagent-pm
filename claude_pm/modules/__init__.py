"""
Claude PM Framework - Modular Architecture Components

This package contains extracted modular components from the main CLI for better
maintainability, testability, and code organization as part of ISS-0085 Phase 2.

Modules:
- deployment_detector: Environment and service detection functionality
- framework_manager: Framework operations and management
- command_dispatcher: Command routing and execution logic
"""

__version__ = "0.6.0"
__author__ = "Claude PM Framework Team"

# Module imports for easy access
from .deployment_detector import (
    DeploymentDetector,
    detect_aitrackdown_info,
    detect_memory_manager_info,
    get_framework_version,
    detect_claude_md_version,
    display_directory_context
)

__all__ = [
    "DeploymentDetector",
    "detect_aitrackdown_info", 
    "detect_memory_manager_info",
    "get_framework_version",
    "detect_claude_md_version",
    "display_directory_context"
]