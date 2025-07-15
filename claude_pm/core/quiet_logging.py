"""
Quiet logging configuration for --force flag operations.
"""
import logging
import sys
from io import StringIO
from contextlib import contextmanager


class QuietLogFilter(logging.Filter):
    """Filter to suppress INFO and WARNING messages during --force operations."""
    
    def filter(self, record):
        """Filter out INFO and WARNING messages."""
        return record.levelno >= logging.ERROR


@contextmanager
def quiet_logging():
    """Context manager to temporarily suppress INFO and WARNING logging."""
    # Get all existing loggers
    root_logger = logging.getLogger()
    existing_loggers = [logging.getLogger(name) for name in logging.Logger.manager.loggerDict]
    
    # Store original levels and handlers
    original_levels = {}
    original_handlers = {}
    
    # Create quiet filter
    quiet_filter = QuietLogFilter()
    
    try:
        # Configure root logger
        original_levels['root'] = root_logger.level
        original_handlers['root'] = root_logger.handlers[:]
        
        # Clear existing handlers and add quiet handlers
        root_logger.handlers.clear()
        
        # Add a simple handler that only shows errors
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(quiet_filter)
        root_logger.addHandler(error_handler)
        root_logger.setLevel(logging.ERROR)
        
        # Configure existing loggers
        for logger in existing_loggers:
            logger_name = logger.name
            original_levels[logger_name] = logger.level
            original_handlers[logger_name] = logger.handlers[:]
            
            # Clear handlers and add quiet filter
            logger.handlers.clear()
            logger.addFilter(quiet_filter)
            logger.setLevel(logging.ERROR)
        
        yield
        
    finally:
        # Restore original configuration
        # Restore root logger
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers['root'])
        root_logger.setLevel(original_levels['root'])
        
        # Restore existing loggers
        for logger in existing_loggers:
            logger_name = logger.name
            if logger_name in original_levels:
                logger.handlers.clear()
                logger.handlers.extend(original_handlers[logger_name])
                logger.setLevel(original_levels[logger_name])
                # Remove the quiet filter
                logger.removeFilter(quiet_filter)


def setup_quiet_logging():
    """Setup quiet logging for --force operations."""
    # Configure all loggers to ERROR level
    logging.basicConfig(level=logging.ERROR, handlers=[])
    
    # Get all existing loggers and set them to ERROR
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)
        
        # Add quiet filter to all handlers
        quiet_filter = QuietLogFilter()
        for handler in logger.handlers:
            handler.addFilter(quiet_filter)
            handler.setLevel(logging.ERROR)
    
    # Also configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)
    quiet_filter = QuietLogFilter()
    for handler in root_logger.handlers:
        handler.addFilter(quiet_filter)
        handler.setLevel(logging.ERROR)