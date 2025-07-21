"""
Backward compatibility stub for prompt_improvement_pipeline.

This module has been refactored into a directory-based structure.
All imports are maintained for backward compatibility.
"""

# Import all public APIs from the new structure
from claude_pm.services.prompt_improvement_pipeline import (
    PromptImprovementPipeline,
    PipelineConfig,
    PipelineExecution,
    PipelineResults,
    PipelineStage,
    PipelineStatus
)

# Maintain backward compatibility
__all__ = [
    'PromptImprovementPipeline',
    'PipelineConfig',
    'PipelineExecution',
    'PipelineResults',
    'PipelineStage',
    'PipelineStatus'
]

# Log deprecation warning
import logging
logger = logging.getLogger(__name__)
logger.warning(
    "Importing from 'claude_pm.services.prompt_improvement_pipeline' (file) is deprecated. "
    "Please import from 'claude_pm.services.prompt_improvement_pipeline' (directory) instead."
)