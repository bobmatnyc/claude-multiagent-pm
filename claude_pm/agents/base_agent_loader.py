#!/usr/bin/env python3
"""
Base Agent Loader Utility
========================

Provides functionality to load and prepend base agent instructions to all agent prompts.
Integrates with SharedPromptCache for performance optimization.

Key Features:
- Load base_agent.md content with caching
- Prepend base instructions to agent prompts
- Thread-safe operations
- Error handling for missing base instructions
- Integration with SharedPromptCache

Usage:
    from claude_pm.agents.base_agent_loader import prepend_base_instructions
    
    # Get agent prompt with base instructions prepended
    full_prompt = prepend_base_instructions(get_documentation_agent_prompt())
"""

import logging
from pathlib import Path
from typing import Optional

from ..services.shared_prompt_cache import SharedPromptCache

# Module-level logger
logger = logging.getLogger(__name__)

# Cache key for base agent instructions
BASE_AGENT_CACHE_KEY = "base_agent:instructions"

# Base agent file path (relative to this module)
BASE_AGENT_FILE = Path(__file__).parent / "base_agent.md"


def load_base_agent_instructions(force_reload: bool = False) -> Optional[str]:
    """
    Load base agent instructions from base_agent.md with caching.
    
    Args:
        force_reload: Force reload from file, bypassing cache
        
    Returns:
        str: Base agent instructions content, or None if file not found
    """
    try:
        # Get cache instance
        cache = SharedPromptCache.get_instance()
        
        # Check cache first (unless force reload)
        if not force_reload:
            cached_content = cache.get(BASE_AGENT_CACHE_KEY)
            if cached_content is not None:
                logger.debug("Base agent instructions loaded from cache")
                return cached_content
        
        # Load from file
        if not BASE_AGENT_FILE.exists():
            logger.warning(f"Base agent instructions file not found: {BASE_AGENT_FILE}")
            return None
            
        logger.debug(f"Loading base agent instructions from: {BASE_AGENT_FILE}")
        content = BASE_AGENT_FILE.read_text(encoding='utf-8')
        
        # Cache the content with 1 hour TTL
        cache.set(BASE_AGENT_CACHE_KEY, content, ttl=3600)
        logger.debug("Base agent instructions cached successfully")
        
        return content
        
    except Exception as e:
        logger.error(f"Error loading base agent instructions: {e}")
        return None


def prepend_base_instructions(agent_prompt: str, separator: str = "\n\n---\n\n") -> str:
    """
    Prepend base agent instructions to an agent-specific prompt.
    
    Args:
        agent_prompt: The agent-specific prompt to prepend to
        separator: String to separate base instructions from agent prompt
        
    Returns:
        str: Combined prompt with base instructions prepended
    """
    # Load base instructions
    base_instructions = load_base_agent_instructions()
    
    # If no base instructions, return original prompt
    if not base_instructions:
        logger.warning("No base instructions available, returning original prompt")
        return agent_prompt
    
    # Combine base instructions with agent prompt
    combined_prompt = f"{base_instructions}{separator}{agent_prompt}"
    
    return combined_prompt


def clear_base_agent_cache() -> None:
    """Clear the cached base agent instructions."""
    try:
        cache = SharedPromptCache.get_instance()
        cache.invalidate(BASE_AGENT_CACHE_KEY)
        logger.debug("Base agent cache cleared")
    except Exception as e:
        logger.error(f"Error clearing base agent cache: {e}")


def get_base_agent_path() -> Path:
    """Get the path to the base agent instructions file."""
    return BASE_AGENT_FILE


def validate_base_agent_file() -> bool:
    """
    Validate that base agent file exists and is readable.
    
    Returns:
        bool: True if file exists and is readable, False otherwise
    """
    try:
        if not BASE_AGENT_FILE.exists():
            logger.error(f"Base agent file does not exist: {BASE_AGENT_FILE}")
            return False
            
        if not BASE_AGENT_FILE.is_file():
            logger.error(f"Base agent path is not a file: {BASE_AGENT_FILE}")
            return False
            
        # Try to read the file
        BASE_AGENT_FILE.read_text(encoding='utf-8')
        return True
        
    except Exception as e:
        logger.error(f"Base agent file validation failed: {e}")
        return False


# Module initialization - validate base agent file on import
if not validate_base_agent_file():
    logger.warning("Base agent file validation failed during module import")