"""
Logging configuration for Claude PM Framework.

Provides standardized logging setup with:
- Console and file output
- Rich formatting for development
- JSON formatting for production
- Log rotation
- Performance monitoring
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console
import json


def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    use_rich: bool = True,
    json_format: bool = False,
) -> logging.Logger:
    """
    Setup logging for a Claude PM service.

    Args:
        name: Logger name (usually service name)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        use_rich: Use Rich handler for colored console output
        json_format: Use JSON format for structured logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear any existing handlers
    logger.handlers.clear()

    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create formatters
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console handler
    if use_rich and not json_format:
        console = Console(stderr=True)
        console_handler = RichHandler(console=console, show_time=True, show_path=True, markup=True)
        console_handler.setFormatter(logging.Formatter(fmt="%(message)s", datefmt="[%X]"))
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Use rotating file handler to manage log size
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with Claude PM defaults."""
    return logging.getLogger(name)


def log_performance(func):
    """Decorator to log function execution time."""
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise

    return wrapper


async def log_async_performance(func):
    """Decorator to log async function execution time."""
    import functools
    import time

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise

    return wrapper
