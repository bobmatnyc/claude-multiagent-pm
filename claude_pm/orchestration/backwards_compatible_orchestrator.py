"""
Backwards Compatible Orchestrator - Compatibility Wrapper
========================================================

This module provides backward compatibility by importing from the refactored
orchestrator modules. All functionality has been preserved.
"""

# Import everything from the refactored module to maintain backward compatibility
from .orchestrator import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode,
    ReturnCode,
    OrchestrationMetrics,
    create_backwards_compatible_orchestrator,
    delegate_with_compatibility
)

# Re-export all public members
__all__ = [
    'BackwardsCompatibleOrchestrator',
    'OrchestrationMode',
    'ReturnCode',
    'OrchestrationMetrics',
    'create_backwards_compatible_orchestrator',
    'delegate_with_compatibility'
]