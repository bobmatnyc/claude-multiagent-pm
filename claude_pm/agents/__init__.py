"""
Claude PM Framework Agents Package

System-level agent implementations with Task Tool integration.
These agents provide specialized prompts and capabilities for PM orchestration.
"""

from .ticketing_agent import get_ticketing_agent_prompt, AGENT_CONFIG as TICKETING_CONFIG

# Available system agents
__all__ = [
    'get_ticketing_agent_prompt',
    'TICKETING_CONFIG'
]

# System agent registry
SYSTEM_AGENTS = {
    'ticketing': {
        'prompt_function': get_ticketing_agent_prompt,
        'config': TICKETING_CONFIG,
        'version': '2.0.0',
        'integration': 'ai_trackdown_tools'
    }
}
