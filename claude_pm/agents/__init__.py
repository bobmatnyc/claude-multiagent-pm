"""
Claude PM Framework Agents Package

System-level agent implementations with Task Tool integration.
These agents provide specialized prompts and capabilities for PM orchestration.
"""

# Import all agent modules and their configs
from .documentation_agent import get_documentation_agent_prompt, AGENT_CONFIG as DOCUMENTATION_CONFIG
from .ticketing_agent import get_ticketing_agent_prompt, AGENT_CONFIG as TICKETING_CONFIG
from .version_control_agent import get_version_control_agent_prompt, AGENT_CONFIG as VERSION_CONTROL_CONFIG
from .qa_agent import get_qa_agent_prompt, AGENT_CONFIG as QA_CONFIG
from .research_agent import get_research_agent_prompt, AGENT_CONFIG as RESEARCH_CONFIG
from .ops_agent import get_ops_agent_prompt, AGENT_CONFIG as OPS_CONFIG
from .security_agent import get_security_agent_prompt, AGENT_CONFIG as SECURITY_CONFIG
from .engineer_agent import get_engineer_agent_prompt, AGENT_CONFIG as ENGINEER_CONFIG
from .data_engineer_agent import get_data_engineer_agent_prompt, AGENT_CONFIG as DATA_ENGINEER_CONFIG

# Available system agents
__all__ = [
    # Agent prompt functions
    'get_documentation_agent_prompt',
    'get_ticketing_agent_prompt',
    'get_version_control_agent_prompt',
    'get_qa_agent_prompt',
    'get_research_agent_prompt',
    'get_ops_agent_prompt',
    'get_security_agent_prompt',
    'get_engineer_agent_prompt',
    'get_data_engineer_agent_prompt',
    # Agent configs
    'DOCUMENTATION_CONFIG',
    'TICKETING_CONFIG',
    'VERSION_CONTROL_CONFIG',
    'QA_CONFIG',
    'RESEARCH_CONFIG',
    'OPS_CONFIG',
    'SECURITY_CONFIG',
    'ENGINEER_CONFIG',
    'DATA_ENGINEER_CONFIG',
    # System registry
    'SYSTEM_AGENTS'
]

# System agent registry
SYSTEM_AGENTS = {
    'documentation': {
        'prompt_function': get_documentation_agent_prompt,
        'config': DOCUMENTATION_CONFIG,
        'version': '2.0.0',
        'integration': 'claude_pm_framework'
    },
    'ticketing': {
        'prompt_function': get_ticketing_agent_prompt,
        'config': TICKETING_CONFIG,
        'version': '2.0.0',
        'integration': 'ai_trackdown_tools'
    },
    'version_control': {
        'prompt_function': get_version_control_agent_prompt,
        'config': VERSION_CONTROL_CONFIG,
        'version': '2.0.0',
        'integration': 'claude_pm_framework'
    },
    'qa': {
        'prompt_function': get_qa_agent_prompt,
        'config': QA_CONFIG,
        'version': '2.0.0',
        'integration': 'claude_pm_framework'
    },
    'research': {
        'prompt_function': get_research_agent_prompt,
        'config': RESEARCH_CONFIG,
        'version': '2.0.0',
        'integration': 'claude_pm_framework'
    },
    'ops': {
        'prompt_function': get_ops_agent_prompt,
        'config': OPS_CONFIG,
        'version': '2.0.0',
        'integration': 'claude_pm_framework'
    },
    'security': {
        'prompt_function': get_security_agent_prompt,
        'config': SECURITY_CONFIG,
        'version': '2.0.0',
        'integration': 'claude_pm_framework'
    },
    'engineer': {
        'prompt_function': get_engineer_agent_prompt,
        'config': ENGINEER_CONFIG,
        'version': '2.0.0',
        'integration': 'claude_pm_framework'
    },
    'data_engineer': {
        'prompt_function': get_data_engineer_agent_prompt,
        'config': DATA_ENGINEER_CONFIG,
        'version': '2.0.0',
        'integration': 'claude_pm_framework'
    }
}
