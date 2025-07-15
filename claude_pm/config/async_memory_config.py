"""
Configuration for AsyncMemoryCollector service.

Provides default configurations for different environments and use cases.
"""

from typing import Dict, Any


# Default configuration for AsyncMemoryCollector
DEFAULT_CONFIG: Dict[str, Any] = {
    "batch_size": 10,
    "batch_timeout": 30.0,
    "max_queue_size": 1000,
    "max_retries": 3,
    "retry_delay": 1.0,
    "operation_timeout": 15.0,
    "max_concurrent_ops": 20,
    "health_check_interval": 60,
    "cache": {
        "enabled": True,
        "max_size": 1000,
        "ttl_seconds": 300
    }
}


# Development environment configuration
DEVELOPMENT_CONFIG: Dict[str, Any] = {
    **DEFAULT_CONFIG,
    "batch_size": 5,
    "batch_timeout": 10.0,
    "max_queue_size": 500,
    "health_check_interval": 30,
    "cache": {
        "enabled": True,
        "max_size": 500,
        "ttl_seconds": 120
    }
}


# Production environment configuration
PRODUCTION_CONFIG: Dict[str, Any] = {
    **DEFAULT_CONFIG,
    "batch_size": 20,
    "batch_timeout": 60.0,
    "max_queue_size": 2000,
    "max_concurrent_ops": 50,
    "health_check_interval": 120,
    "cache": {
        "enabled": True,
        "max_size": 2000,
        "ttl_seconds": 600
    }
}


# High-performance configuration
HIGH_PERFORMANCE_CONFIG: Dict[str, Any] = {
    **DEFAULT_CONFIG,
    "batch_size": 50,
    "batch_timeout": 5.0,
    "max_queue_size": 5000,
    "max_concurrent_ops": 100,
    "operation_timeout": 5.0,
    "health_check_interval": 30,
    "cache": {
        "enabled": True,
        "max_size": 5000,
        "ttl_seconds": 300
    }
}


# Low-resource configuration
LOW_RESOURCE_CONFIG: Dict[str, Any] = {
    **DEFAULT_CONFIG,
    "batch_size": 3,
    "batch_timeout": 60.0,
    "max_queue_size": 100,
    "max_concurrent_ops": 5,
    "operation_timeout": 30.0,
    "health_check_interval": 180,
    "cache": {
        "enabled": False,
        "max_size": 100,
        "ttl_seconds": 60
    }
}


def get_config(environment: str = "default") -> Dict[str, Any]:
    """
    Get configuration for specified environment.
    
    Args:
        environment: Environment name (default, development, production, 
                    high_performance, low_resource)
    
    Returns:
        Configuration dictionary
    """
    configs = {
        "default": DEFAULT_CONFIG,
        "development": DEVELOPMENT_CONFIG,
        "production": PRODUCTION_CONFIG,
        "high_performance": HIGH_PERFORMANCE_CONFIG,
        "low_resource": LOW_RESOURCE_CONFIG
    }
    
    return configs.get(environment, DEFAULT_CONFIG).copy()


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate AsyncMemoryCollector configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_keys = [
        "batch_size", "batch_timeout", "max_queue_size", 
        "max_retries", "retry_delay", "operation_timeout",
        "max_concurrent_ops", "health_check_interval"
    ]
    
    # Check required keys
    for key in required_keys:
        if key not in config:
            return False
    
    # Validate numeric values
    try:
        assert config["batch_size"] > 0
        assert config["batch_timeout"] > 0
        assert config["max_queue_size"] > 0
        assert config["max_retries"] >= 0
        assert config["retry_delay"] > 0
        assert config["operation_timeout"] > 0
        assert config["max_concurrent_ops"] > 0
        assert config["health_check_interval"] > 0
    except (AssertionError, TypeError):
        return False
    
    # Validate cache configuration if present
    if "cache" in config:
        cache_config = config["cache"]
        if not isinstance(cache_config, dict):
            return False
        
        try:
            if "enabled" in cache_config:
                assert isinstance(cache_config["enabled"], bool)
            if "max_size" in cache_config:
                assert cache_config["max_size"] > 0
            if "ttl_seconds" in cache_config:
                assert cache_config["ttl_seconds"] > 0
        except (AssertionError, TypeError):
            return False
    
    return True