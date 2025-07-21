#!/usr/bin/env python3
"""
Task Complexity Integration Example
===================================

Example of integrating TaskComplexityAnalyzer with agent_loader.py workflow.
This demonstrates how to use complexity analysis for dynamic prompt generation.
"""

import logging
from typing import Dict, Any

from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer, ModelType
from claude_pm.agents.agent_loader import get_agent_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_optimized_prompt(
    agent_name: str,
    task_description: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create an optimized prompt based on task complexity analysis.
    
    Args:
        agent_name: Name of the agent (e.g., 'documentation', 'engineer')
        task_description: Description of the task
        context: Additional context for the task
        
    Returns:
        Dictionary containing optimized prompt and metadata
    """
    # Initialize analyzer
    analyzer = TaskComplexityAnalyzer()
    
    # Extract complexity factors from context
    file_count = context.get('file_count', 0)
    context_size = len(str(context))
    integration_points = context.get('integration_points', 0)
    requires_testing = context.get('requires_testing', False)
    
    # Analyze task complexity
    analysis = analyzer.analyze_task(
        task_description=task_description,
        file_count=file_count,
        context_size=context_size,
        integration_points=integration_points,
        requires_testing=requires_testing
    )
    
    # Get base agent prompt
    base_prompt = get_agent_prompt(agent_name)
    
    # Optimize prompt based on complexity
    optimization_hints = analyzer.get_prompt_optimization_hints(analysis)
    
    # Build optimized prompt
    optimized_prompt = _build_optimized_prompt(
        base_prompt=base_prompt,
        task_description=task_description,
        context=context,
        analysis=analysis,
        hints=optimization_hints
    )
    
    return {
        'prompt': optimized_prompt,
        'model': analysis.recommended_model.value,
        'complexity_score': analysis.complexity_score,
        'complexity_level': analysis.complexity_level.value,
        'prompt_size': len(optimized_prompt),
        'optimization_applied': optimization_hints
    }


def _build_optimized_prompt(
    base_prompt: str,
    task_description: str,
    context: Dict[str, Any],
    analysis: Any,
    hints: Dict[str, Any]
) -> str:
    """
    Build optimized prompt based on complexity analysis.
    
    Args:
        base_prompt: Base agent prompt
        task_description: Task description
        context: Task context
        analysis: Complexity analysis result
        hints: Optimization hints
        
    Returns:
        Optimized prompt string
    """
    # Start with base prompt
    prompt_parts = [base_prompt, "\n\n## Task\n", task_description]
    
    # Add context based on complexity
    if analysis.complexity_level.value == "SIMPLE":
        # Minimal context for simple tasks
        prompt_parts.append("\n\n## Key Information\n")
        prompt_parts.append(_get_minimal_context(context))
        
    elif analysis.complexity_level.value == "MEDIUM":
        # Standard context for medium tasks
        prompt_parts.append("\n\n## Context\n")
        prompt_parts.append(_get_standard_context(context))
        
    else:  # COMPLEX
        # Comprehensive context for complex tasks
        prompt_parts.append("\n\n## Detailed Context\n")
        prompt_parts.append(_get_comprehensive_context(context))
        
        # Add examples for complex tasks
        if "include_examples_and_patterns" in hints.get('optimization_strategies', []):
            prompt_parts.append("\n\n## Examples and Patterns\n")
            prompt_parts.append(_get_relevant_examples(task_description))
    
    # Add focus areas if specified
    if hints.get('focus_areas'):
        prompt_parts.append("\n\n## Focus Areas\n")
        for area in hints['focus_areas']:
            prompt_parts.append(f"- {area.replace('_', ' ').title()}\n")
    
    # Trim to optimal size
    full_prompt = "".join(prompt_parts)
    min_size, max_size = hints['prompt_size_range']
    
    if len(full_prompt) > max_size:
        # Trim to fit within optimal range
        full_prompt = full_prompt[:max_size-3] + "..."
    
    return full_prompt


def _get_minimal_context(context: Dict[str, Any]) -> str:
    """Extract minimal context for simple tasks."""
    key_items = []
    for key in ['project_name', 'current_file', 'target_directory']:
        if key in context:
            key_items.append(f"- {key}: {context[key]}")
    return "\n".join(key_items)


def _get_standard_context(context: Dict[str, Any]) -> str:
    """Extract standard context for medium tasks."""
    sections = []
    
    # Project info
    if 'project_info' in context:
        sections.append(f"Project: {context['project_info']}")
    
    # File operations
    if 'files' in context:
        sections.append(f"Files involved: {', '.join(context['files'][:5])}")
    
    # Dependencies
    if 'dependencies' in context:
        sections.append(f"Dependencies: {', '.join(context['dependencies'][:3])}")
    
    return "\n".join(sections)


def _get_comprehensive_context(context: Dict[str, Any]) -> str:
    """Extract comprehensive context for complex tasks."""
    # Include all available context
    formatted_context = []
    
    for key, value in context.items():
        if isinstance(value, list):
            formatted_context.append(f"{key}:\n  - " + "\n  - ".join(str(v) for v in value[:10]))
        elif isinstance(value, dict):
            formatted_context.append(f"{key}:")
            for k, v in list(value.items())[:5]:
                formatted_context.append(f"  {k}: {v}")
        else:
            formatted_context.append(f"{key}: {value}")
    
    return "\n".join(formatted_context)


def _get_relevant_examples(task_description: str) -> str:
    """Get relevant examples based on task type."""
    # This would typically fetch from a database of examples
    # For now, return a placeholder
    return "Example patterns and best practices for similar tasks..."


# Example usage
if __name__ == "__main__":
    # Example task
    task = "Refactor the authentication module to implement OAuth2 with multi-factor authentication support"
    
    # Example context
    context = {
        'project_name': 'claude-multiagent-pm',
        'files': [
            'auth/login.py',
            'auth/oauth_handler.py',
            'auth/mfa_service.py',
            'auth/token_manager.py',
            'auth/user_session.py'
        ],
        'integration_points': 3,
        'requires_testing': True,
        'dependencies': ['oauth2', 'pyotp', 'jwt'],
        'current_architecture': 'Basic JWT authentication',
        'target_architecture': 'OAuth2 with MFA'
    }
    
    # Create optimized prompt
    result = create_optimized_prompt(
        agent_name='engineer',
        task_description=task,
        context=context
    )
    
    # Log results
    logger.info(f"Task Complexity: {result['complexity_level']} (score: {result['complexity_score']})")
    logger.info(f"Recommended Model: {result['model']}")
    logger.info(f"Optimized Prompt Size: {result['prompt_size']} chars")
    logger.info(f"Optimization Applied: {result['optimization_applied']}")
    
    print("\n=== OPTIMIZED PROMPT ===")
    print(result['prompt'][:500] + "..." if len(result['prompt']) > 500 else result['prompt'])