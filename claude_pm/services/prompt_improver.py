"""
Backward compatibility stub for prompt_improver module.

This module maintains backward compatibility by re-exporting all public APIs
from the refactored prompt_improver package.

Author: Claude PM Framework
Date: 2025-07-19
Version: 1.0.0
"""

# Import and re-export all public APIs from the package
from claude_pm.services.prompt_improver import *

# Ensure backward compatibility
__all__ = [
    'PromptImprover',
    'analyze_and_improve_prompts',
    'get_improvement_dashboard',
    'ImprovementStrategy',
    'PromptImprovement',
    'CorrectionPattern',
    'ImprovementMetrics'
]