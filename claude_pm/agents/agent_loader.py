#!/usr/bin/env python3
"""
Unified Agent Loader System
==========================

Provides unified loading of agent prompts from framework markdown files with fallback
to Python constants. Integrates with SharedPromptCache for performance optimization.

Key Features:
- Loads agent prompts from framework/agent-roles/*.md files
- Falls back to existing Python constants if MD file not found
- Handles base_agent.md prepending
- Provides backward-compatible get_*_agent_prompt() functions
- Uses SharedPromptCache for performance
- Special handling for ticketing agent's dynamic CLI help

Usage:
    from claude_pm.agents.agent_loader import get_documentation_agent_prompt
    
    # Get agent prompt (from MD file or fallback to Python constant)
    prompt = get_documentation_agent_prompt()
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import importlib

from ..services.shared_prompt_cache import SharedPromptCache
from .base_agent_loader import prepend_base_instructions

# Module-level logger
logger = logging.getLogger(__name__)

# Framework agent-roles directory
FRAMEWORK_AGENT_ROLES_DIR = Path(__file__).parent.parent.parent / "framework" / "agent-roles"

# Cache prefix for agent prompts
AGENT_CACHE_PREFIX = "agent_prompt:"

# Agent name mappings (Python module name -> MD file name)
AGENT_MAPPINGS = {
    "documentation": "documentation-agent.md",
    "ticketing": "ticketing-agent.md",
    "version_control": "version-control-agent.md",
    "qa": "qa-agent.md",
    "research": "research-agent.md",
    "ops": "ops-agent.md",
    "security": "security-agent.md",
    "engineer": "engineer-agent.md",
    "data_engineer": "data-agent.md",  # Note: data-agent.md maps to data_engineer
}

# Python module fallbacks
PYTHON_MODULES = {
    "documentation": "documentation_agent",
    "ticketing": "ticketing_agent",
    "version_control": "version_control_agent",
    "qa": "qa_agent",
    "research": "research_agent",
    "ops": "ops_agent",
    "security": "security_agent",
    "engineer": "engineer_agent",
    "data_engineer": "data_engineer_agent",
}


def load_agent_prompt_from_md(agent_name: str, force_reload: bool = False) -> Optional[str]:
    """
    Load agent prompt from framework markdown file.
    
    Args:
        agent_name: Agent name (e.g., 'documentation', 'ticketing')
        force_reload: Force reload from file, bypassing cache
        
    Returns:
        str: Agent prompt content from MD file, or None if not found
    """
    try:
        # Get cache instance
        cache = SharedPromptCache.get_instance()
        cache_key = f"{AGENT_CACHE_PREFIX}{agent_name}:md"
        
        # Check cache first (unless force reload)
        if not force_reload:
            cached_content = cache.get(cache_key)
            if cached_content is not None:
                logger.debug(f"Agent prompt for '{agent_name}' loaded from cache")
                return cached_content
        
        # Get MD file path
        md_filename = AGENT_MAPPINGS.get(agent_name)
        if not md_filename:
            logger.warning(f"No MD file mapping found for agent: {agent_name}")
            return None
            
        md_path = FRAMEWORK_AGENT_ROLES_DIR / md_filename
        
        # Check if file exists
        if not md_path.exists():
            logger.warning(f"Agent MD file not found: {md_path}")
            return None
            
        logger.debug(f"Loading agent prompt from: {md_path}")
        content = md_path.read_text(encoding='utf-8')
        
        # Cache the content with 1 hour TTL
        cache.set(cache_key, content, ttl=3600)
        logger.debug(f"Agent prompt for '{agent_name}' cached successfully")
        
        return content
        
    except Exception as e:
        logger.error(f"Error loading agent prompt from MD for '{agent_name}': {e}")
        return None


def load_agent_prompt_from_python(agent_name: str) -> Optional[str]:
    """
    Load agent prompt from Python module (fallback).
    
    Args:
        agent_name: Agent name (e.g., 'documentation', 'ticketing')
        
    Returns:
        str: Agent prompt content from Python module, or None if not found
    """
    try:
        module_name = PYTHON_MODULES.get(agent_name)
        if not module_name:
            logger.error(f"No Python module mapping found for agent: {agent_name}")
            return None
            
        # Import the module
        module = importlib.import_module(f".{module_name}", package="claude_pm.agents")
        
        # Get the prompt constant (without base instructions)
        prompt_constant_name = f"{agent_name.upper()}_AGENT_PROMPT"
        if hasattr(module, prompt_constant_name):
            return getattr(module, prompt_constant_name)
        
        # Some modules might use PROMPT_TEMPLATE
        if hasattr(module, f"{agent_name.upper()}_AGENT_PROMPT_TEMPLATE"):
            return getattr(module, f"{agent_name.upper()}_AGENT_PROMPT_TEMPLATE")
            
        logger.error(f"No prompt constant found in module: {module_name}")
        return None
        
    except Exception as e:
        logger.error(f"Error loading agent prompt from Python for '{agent_name}': {e}")
        return None


def get_agent_prompt(agent_name: str, force_reload: bool = False, **kwargs) -> str:
    """
    Get agent prompt with MD file priority and Python fallback.
    
    Args:
        agent_name: Agent name (e.g., 'documentation', 'ticketing')
        force_reload: Force reload from source, bypassing cache
        **kwargs: Additional arguments for specific agents (e.g., force_refresh_help for ticketing)
        
    Returns:
        str: Complete agent prompt with base instructions prepended
    """
    # Try loading from MD file first
    prompt = load_agent_prompt_from_md(agent_name, force_reload)
    
    # Fall back to Python module if MD not found
    if prompt is None:
        logger.info(f"Falling back to Python module for agent: {agent_name}")
        
        # Special handling for ticketing agent with dynamic help
        if agent_name == "ticketing" and "force_refresh_help" in kwargs:
            try:
                module = importlib.import_module(".ticketing_agent", package="claude_pm.agents")
                if hasattr(module, "get_ticketing_agent_prompt"):
                    # Call the function directly to handle dynamic help
                    return module.get_ticketing_agent_prompt(
                        force_refresh_help=kwargs.get("force_refresh_help", False)
                    )
            except Exception as e:
                logger.error(f"Error calling ticketing agent function: {e}")
        
        # Standard fallback to Python constant
        prompt = load_agent_prompt_from_python(agent_name)
        
        if prompt is None:
            raise ValueError(f"No agent prompt found for: {agent_name}")
    
    # Handle ticketing agent template formatting if needed
    if agent_name == "ticketing" and "{dynamic_help}" in prompt:
        try:
            # Import ticketing module to get dynamic help
            module = importlib.import_module(".ticketing_agent", package="claude_pm.agents")
            if hasattr(module, "_dynamic_help_section"):
                prompt = prompt.format(dynamic_help=getattr(module, "_dynamic_help_section"))
            else:
                # Initialize help if not already done
                if hasattr(module, "_cli_helper"):
                    cli_helper = getattr(module, "_cli_helper")
                    help_content, _ = cli_helper.get_cli_help()
                    dynamic_help = cli_helper.format_help_for_prompt(help_content)
                    prompt = prompt.format(dynamic_help=dynamic_help)
        except Exception as e:
            logger.warning(f"Could not format dynamic help for ticketing agent: {e}")
            # Remove the placeholder if we can't fill it
            prompt = prompt.replace("{dynamic_help}", "")
    
    # Prepend base instructions
    return prepend_base_instructions(prompt)


# Backward-compatible functions
def get_documentation_agent_prompt() -> str:
    """Get the complete Documentation Agent prompt with base instructions."""
    return get_agent_prompt("documentation")


def get_ticketing_agent_prompt(force_refresh_help: bool = False) -> str:
    """Get the complete Ticketing Agent prompt with AI Trackdown Tools integration."""
    return get_agent_prompt("ticketing", force_refresh_help=force_refresh_help)


def get_version_control_agent_prompt() -> str:
    """Get the complete Version Control Agent prompt with base instructions."""
    return get_agent_prompt("version_control")


def get_qa_agent_prompt() -> str:
    """Get the complete QA Agent prompt with base instructions."""
    return get_agent_prompt("qa")


def get_research_agent_prompt() -> str:
    """Get the complete Research Agent prompt with base instructions."""
    return get_agent_prompt("research")


def get_ops_agent_prompt() -> str:
    """Get the complete Ops Agent prompt with base instructions."""
    return get_agent_prompt("ops")


def get_security_agent_prompt() -> str:
    """Get the complete Security Agent prompt with base instructions."""
    return get_agent_prompt("security")


def get_engineer_agent_prompt() -> str:
    """Get the complete Engineer Agent prompt with base instructions."""
    return get_agent_prompt("engineer")


def get_data_engineer_agent_prompt() -> str:
    """Get the complete Data Engineer Agent prompt with base instructions."""
    return get_agent_prompt("data_engineer")


# Utility functions
def list_available_agents() -> Dict[str, Dict[str, Any]]:
    """
    List all available agents with their sources.
    
    Returns:
        dict: Agent information including source (md/python) and path
    """
    agents = {}
    
    for agent_name, md_filename in AGENT_MAPPINGS.items():
        md_path = FRAMEWORK_AGENT_ROLES_DIR / md_filename
        python_module = PYTHON_MODULES.get(agent_name)
        
        agents[agent_name] = {
            "md_file": md_filename if md_path.exists() else None,
            "md_path": str(md_path) if md_path.exists() else None,
            "python_module": python_module,
            "has_md": md_path.exists(),
            "has_python": python_module is not None
        }
    
    return agents


def clear_agent_cache(agent_name: Optional[str] = None) -> None:
    """
    Clear cached agent prompts.
    
    Args:
        agent_name: Specific agent to clear, or None to clear all
    """
    try:
        cache = SharedPromptCache.get_instance()
        
        if agent_name:
            cache_key = f"{AGENT_CACHE_PREFIX}{agent_name}:md"
            cache.invalidate(cache_key)
            logger.debug(f"Cache cleared for agent: {agent_name}")
        else:
            # Clear all agent caches
            for name in AGENT_MAPPINGS:
                cache_key = f"{AGENT_CACHE_PREFIX}{name}:md"
                cache.invalidate(cache_key)
            logger.debug("All agent caches cleared")
            
    except Exception as e:
        logger.error(f"Error clearing agent cache: {e}")


def validate_agent_files() -> Dict[str, bool]:
    """
    Validate that all expected agent files exist.
    
    Returns:
        dict: Validation results for each agent
    """
    results = {}
    
    for agent_name, md_filename in AGENT_MAPPINGS.items():
        md_path = FRAMEWORK_AGENT_ROLES_DIR / md_filename
        results[agent_name] = {
            "md_exists": md_path.exists(),
            "md_path": str(md_path),
            "python_fallback": PYTHON_MODULES.get(agent_name) is not None
        }
    
    return results