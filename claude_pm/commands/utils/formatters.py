"""
CMPM Command Formatters
======================

Output formatting utilities for CMPM commands including Rich console
formatting, JSON output, and table generation.
"""

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn


def format_health_status(status: str) -> Text:
    """
    Format health status with appropriate colors.
    
    Args:
        status: Health status string
        
    Returns:
        Formatted Rich Text object
    """
    color_map = {
        "healthy": "green",
        "degraded": "yellow",
        "error": "red",
        "unknown": "dim"
    }
    
    color = color_map.get(status.lower(), "white")
    return Text(status.upper(), style=f"bold {color}")


def format_agent_status(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format agent status data for display.
    
    Args:
        agent_data: Raw agent data
        
    Returns:
        Formatted agent data
    """
    return {
        "name": agent_data.get("name", "Unknown"),
        "type": agent_data.get("type", "Unknown"),
        "status": agent_data.get("status", "unknown"),
        "last_seen": agent_data.get("last_seen", "Never"),
        "capabilities": agent_data.get("capabilities", [])
    }


def format_json_output(data: Any, indent: int = 2) -> str:
    """
    Format data as JSON with proper serialization.
    
    Args:
        data: Data to format
        indent: JSON indentation level
        
    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(data, indent=indent, default=str)
    except (TypeError, ValueError):
        # Fallback for non-serializable objects
        return json.dumps({"error": "Data not serializable"}, indent=indent)


def format_table_output(data: List[Dict[str, Any]], title: str = "Results") -> Table:
    """
    Format data as a Rich table.
    
    Args:
        data: List of dictionaries to display
        title: Table title
        
    Returns:
        Rich Table object
    """
    if not data:
        table = Table(title=title)
        table.add_column("Message", style="dim")
        table.add_row("No data available")
        return table
    
    table = Table(title=title)
    
    # Add columns from first row keys
    if data:
        for key in data[0].keys():
            table.add_column(key.replace("_", " ").title())
        
        # Add rows
        for row in data:
            table.add_row(*[str(value) for value in row.values()])
    
    return table


def create_status_panel(title: str, content: str, status: str = "info") -> Panel:
    """
    Create a status panel with appropriate styling.
    
    Args:
        title: Panel title
        content: Panel content
        status: Status type for styling
        
    Returns:
        Rich Panel object
    """
    style_map = {
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "info": "blue"
    }
    
    style = style_map.get(status.lower(), "white")
    
    return Panel(
        content,
        title=title,
        border_style=style,
        padding=(1, 2)
    )


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_timestamp(timestamp: Union[str, datetime]) -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp: Timestamp string or datetime object
        
    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return timestamp
    else:
        dt = timestamp
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_progress_spinner(description: str = "Processing...") -> Progress:
    """
    Create a progress spinner for long-running operations.
    
    Args:
        description: Description text for the spinner
        
    Returns:
        Rich Progress object
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=Console(),
        transient=True
    )


def format_bytes(size: int) -> str:
    """
    Format byte size in human-readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}PB"


def format_percentage(value: float, total: float) -> str:
    """
    Format percentage with proper handling of edge cases.
    
    Args:
        value: Current value
        total: Total value
        
    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0%"
    
    percentage = (value / total) * 100
    return f"{percentage:.1f}%"