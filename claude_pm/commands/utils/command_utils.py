"""
CMPM Command Utilities
=====================

Shared utilities for CMPM commands including base classes, error handling,
and common functionality.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union

import click
from rich.console import Console

from ...core.config import Config

console = Console()
logger = logging.getLogger(__name__)


class CMPMCommandBase:
    """Base class for CMPM command implementations."""
    
    def __init__(self):
        self.config = Config()
        self.framework_path = Path.cwd()
        self.start_time = time.time()
        self.console = Console()
    
    def get_execution_time(self) -> float:
        """Get command execution time in seconds."""
        return time.time() - self.start_time


def handle_command_error(error: Exception, command_name: str) -> Dict[str, Any]:
    """
    Handle command errors with consistent formatting.
    
    Args:
        error: The exception that occurred
        command_name: Name of the command that failed
        
    Returns:
        Error response dictionary
    """
    logger.error(f"{command_name} failed: {error}")
    
    return {
        "status": "error",
        "command": command_name,
        "error": str(error),
        "timestamp": datetime.now().isoformat()
    }


def get_framework_path() -> Path:
    """Get the framework root path."""
    return Path.cwd()


def validate_output_format(output_format: str) -> str:
    """
    Validate and normalize output format.
    
    Args:
        output_format: The output format string
        
    Returns:
        Normalized output format
        
    Raises:
        click.BadParameter: If format is invalid
    """
    valid_formats = {"json", "table", "yaml", "text"}
    normalized = output_format.lower()
    
    if normalized not in valid_formats:
        raise click.BadParameter(
            f"Invalid output format '{output_format}'. "
            f"Valid formats: {', '.join(valid_formats)}"
        )
    
    return normalized


def run_async_command(coro):
    """
    Run an async command in a new event loop.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an event loop, create a new one
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(coro)


def format_execution_time(start_time: float) -> str:
    """
    Format execution time for display.
    
    Args:
        start_time: Start time from time.time()
        
    Returns:
        Formatted time string
    """
    elapsed = time.time() - start_time
    if elapsed < 1:
        return f"{elapsed*1000:.0f}ms"
    else:
        return f"{elapsed:.2f}s"


def safe_json_serialize(obj: Any) -> str:
    """
    Safely serialize an object to JSON.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError) as e:
        logger.warning(f"JSON serialization failed: {e}")
        return json.dumps({"error": f"Serialization failed: {str(e)}"}, indent=2)


def get_service_status(service_name: str) -> Dict[str, Any]:
    """
    Get the status of a service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        Service status dictionary
    """
    try:
        # This is a placeholder - actual implementation would check service health
        return {
            "name": service_name,
            "status": "unknown",
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "name": service_name,
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }