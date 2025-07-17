"""
Orchestration-specific logging setup.

This module provides orchestration-specific logging configuration that:
- Writes to .claude-pm/logs/orchestration.log with JSON format for structured logging
- Automatically finds the project's .claude-pm directory by walking up the directory tree
- Enables log rotation to prevent unbounded growth
- Provides both console and file output
- Supports performance tracking and metrics

Usage:
    The logging is automatically initialized when the orchestration module is imported.
    Log files are written to .claude-pm/logs/orchestration.log in the project directory.
    
    To manually configure logging:
    
        from claude_pm.orchestration.logging_setup import setup_orchestration_logging
        
        # Use default settings (JSON format to .claude-pm/logs/orchestration.log)
        setup_orchestration_logging()
        
        # Custom configuration
        setup_orchestration_logging(
            log_dir=Path("/custom/log/path"),
            level="DEBUG",
            use_json=False,  # Use text format instead of JSON
            console_output=True,
            working_directory=Path("/specific/project")  # Specify project directory
        )
    
    All orchestration modules automatically use the configured loggers.
"""

from pathlib import Path
import os
from claude_pm.core.logging_config import setup_logging, get_logger


def _find_project_root(start_path: Path = None) -> Path:
    """
    Find the project root by looking for .claude-pm directory.
    
    Walks up the directory tree from start_path looking for a .claude-pm directory.
    Falls back to current working directory if none found.
    
    Args:
        start_path: Path to start searching from (defaults to cwd)
        
    Returns:
        Path to directory containing .claude-pm, or cwd if not found
    """
    current = Path(start_path or os.getcwd()).resolve()
    
    # Walk up directory tree looking for .claude-pm
    while current != current.parent:
        if (current / ".claude-pm").exists():
            return current
        current = current.parent
    
    # If no .claude-pm found, use working directory
    return Path(os.getcwd())


def setup_orchestration_logging(
    log_dir: Path = None,
    level: str = "INFO",
    use_json: bool = True,
    console_output: bool = True,
    working_directory: Path = None
) -> None:
    """
    Setup specialized logging for orchestration components.
    
    Args:
        log_dir: Directory for log files (defaults to .claude-pm/logs in project)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Use JSON format for structured logging
        console_output: Enable console output in addition to file
        working_directory: Working directory to find .claude-pm (defaults to cwd)
    """
    if log_dir is None:
        # Find project root and use .claude-pm/logs
        project_root = _find_project_root(working_directory)
        
        # Ensure full .claude-pm structure exists (fallback if CLI auto-setup fails)
        claude_pm_dir = project_root / ".claude-pm"
        if not claude_pm_dir.exists():
            try:
                claude_pm_dir.mkdir(parents=True, exist_ok=True)
                # Create standard subdirectories
                (claude_pm_dir / "logs").mkdir(exist_ok=True)
                (claude_pm_dir / "agents").mkdir(exist_ok=True)
                (claude_pm_dir / "config").mkdir(exist_ok=True)
            except PermissionError:
                # Fall back to temp directory if we can't create in project
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "claude-pm-logs"
                temp_dir.mkdir(parents=True, exist_ok=True)
                log_dir = temp_dir
                import warnings
                warnings.warn(f"Could not create .claude-pm in {project_root}, using {temp_dir}")
        
        if log_dir is None:
            log_dir = project_root / ".claude-pm" / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "orchestration.log"
    
    # Setup logging for orchestration modules
    orchestration_modules = [
        "claude_pm.orchestration.backwards_compatible_orchestrator",
        "claude_pm.orchestration.context_manager",
        "claude_pm.orchestration.message_bus",
        "claude_pm.orchestration.orchestration_detector"
    ]
    
    for module_name in orchestration_modules:
        logger = setup_logging(
            name=module_name,
            level=level,
            log_file=log_file,
            use_rich=console_output and not use_json,
            json_format=use_json
        )
        
        # Add orchestration-specific context to logs
        logger.info("orchestration_logging_initialized", extra={
            "module_name": module_name,
            "log_file": str(log_file),
            "log_level": level,
            "json_format": use_json
        })


def get_orchestration_logger(name: str, working_directory: Path = None):
    """
    Get a logger configured for orchestration use.
    
    This ensures the logger has the proper handlers and formatting
    for orchestration-specific logging needs.
    
    Args:
        name: Logger name (usually __name__)
        working_directory: Working directory to find .claude-pm (defaults to cwd)
        
    Returns:
        Configured logger instance
    """
    logger = get_logger(name)
    
    # Find project root and ensure logs directory exists
    project_root = _find_project_root(working_directory)
    claude_pm_dir = project_root / ".claude-pm"
    
    # Ensure full .claude-pm structure exists (fallback if CLI auto-setup fails)
    if not claude_pm_dir.exists():
        try:
            claude_pm_dir.mkdir(parents=True, exist_ok=True)
            # Create standard subdirectories
            (claude_pm_dir / "logs").mkdir(exist_ok=True)
            (claude_pm_dir / "agents").mkdir(exist_ok=True)
            (claude_pm_dir / "config").mkdir(exist_ok=True)
        except PermissionError:
            # Fall back to temp directory if we can't create in project
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "claude-pm-logs"
            temp_dir.mkdir(parents=True, exist_ok=True)
            log_dir = temp_dir
            import warnings
            warnings.warn(f"Could not create .claude-pm in {project_root}, using {temp_dir}")
    
    log_dir = claude_pm_dir / "logs" if 'log_dir' not in locals() else log_dir
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
        
    # Setup file handler if not already configured
    has_file_handler = any(
        hasattr(handler, 'baseFilename') and 'orchestration.log' in handler.baseFilename
        for handler in logger.handlers
    )
    
    if not has_file_handler:
        log_file = log_dir / "orchestration.log"
        # Convert numeric level to string name
        import logging
        level_name = logging.getLevelName(logger.level)
        setup_logging(
            name=name,
            level=level_name,
            log_file=log_file,
            json_format=True
        )
    
    return logger


# Example structured logging helpers
def log_agent_delegation(logger, event: str, **kwargs):
    """Log agent delegation events with structured data."""
    logger.info(event, extra={
        "timestamp": kwargs.get("timestamp"),
        "agent_type": kwargs.get("agent_type"),
        "task_id": kwargs.get("task_id"),
        "task_description": kwargs.get("task_description", "")[:100],
        "priority": kwargs.get("priority", "medium"),
        "requirements_count": kwargs.get("requirements_count", 0),
        "deliverables_count": kwargs.get("deliverables_count", 0),
        **{k: v for k, v in kwargs.items() if k not in [
            "timestamp", "agent_type", "task_id", "task_description",
            "priority", "requirements_count", "deliverables_count"
        ]}
    })


def log_orchestration_metrics(logger, metrics: dict):
    """Log orchestration performance metrics."""
    logger.info("orchestration_metrics", extra={
        "total_orchestrations": metrics.get("total_orchestrations", 0),
        "local_orchestrations": metrics.get("local_orchestrations", 0),
        "subprocess_orchestrations": metrics.get("subprocess_orchestrations", 0),
        "success_rate": metrics.get("success_rate", 0.0),
        "average_decision_time_ms": metrics.get("average_decision_time_ms", 0.0),
        "average_execution_time_ms": metrics.get("average_execution_time_ms", 0.0),
        "average_token_reduction_percent": metrics.get("average_token_reduction_percent", 0.0),
        "agent_type_distribution": metrics.get("agent_type_distribution", {})
    })