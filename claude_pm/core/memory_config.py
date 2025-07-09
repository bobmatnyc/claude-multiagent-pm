"""
Configuration module for ClaudePMMemory service.
Provides environment-specific configurations and factory functions.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from claude_pm.services.claude_pm_memory import ClaudePMConfig, ClaudePMMemory


@dataclass
class MemoryEnvironmentConfig:
    """Environment-specific memory configuration."""
    name: str
    description: str
    memory_config: ClaudePMConfig
    health_check_interval: int = 60
    enable_monitoring: bool = True
    log_level: str = "INFO"


class MemoryConfigManager:
    """Manages memory configurations for different environments."""
    
    def __init__(self):
        self.configs: Dict[str, MemoryEnvironmentConfig] = {}
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """Initialize default configurations for each environment."""
        
        # Development configuration
        self.configs["development"] = MemoryEnvironmentConfig(
            name="development",
            description="Development environment with verbose logging",
            memory_config=ClaudePMConfig(
                host=os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_HOST", os.getenv("CLAUDE_PM_MEMORY_HOST", "localhost")),
                port=int(os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_PORT", os.getenv("CLAUDE_PM_MEMORY_PORT", "8002"))),
                timeout=int(os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_TIMEOUT", os.getenv("CLAUDE_PM_MEMORY_TIMEOUT", "10"))),
                max_retries=2,
                retry_delay=0.5,
                connection_pool_size=5,
                enable_logging=True,
                api_key=os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_API_KEY", os.getenv("CLAUDE_PM_MEMORY_API_KEY")),
                batch_size=50,
                cache_ttl=180,  # 3 minutes
                max_memory_size=500,  # 500MB
                compression_enabled=False  # Disabled for development
            ),
            health_check_interval=30,
            enable_monitoring=True,
            log_level="DEBUG"
        )
        
        # Testing configuration
        self.configs["testing"] = MemoryEnvironmentConfig(
            name="testing",
            description="Testing environment with minimal resources",
            memory_config=ClaudePMConfig(
                host=os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_TEST_HOST", os.getenv("CLAUDE_PM_MEMORY_TEST_HOST", "localhost")),
                port=int(os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_TEST_PORT", os.getenv("CLAUDE_PM_MEMORY_TEST_PORT", "8002"))),
                timeout=5,
                max_retries=1,
                retry_delay=0.1,
                connection_pool_size=2,
                enable_logging=False,
                api_key=None,
                batch_size=10,
                cache_ttl=60,  # 1 minute
                max_memory_size=100,  # 100MB
                compression_enabled=False
            ),
            health_check_interval=10,
            enable_monitoring=False,
            log_level="WARNING"
        )
        
        # Staging configuration
        self.configs["staging"] = MemoryEnvironmentConfig(
            name="staging",
            description="Staging environment mirroring production",
            memory_config=ClaudePMConfig(
                host=os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_STAGING_HOST", os.getenv("CLAUDE_PM_MEMORY_STAGING_HOST", "memory-staging.internal")),
                port=int(os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_STAGING_PORT", os.getenv("CLAUDE_PM_MEMORY_STAGING_PORT", "8002"))),
                timeout=20,
                max_retries=3,
                retry_delay=1.0,
                connection_pool_size=15,
                enable_logging=True,
                api_key=os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_STAGING_API_KEY", os.getenv("CLAUDE_PM_MEMORY_STAGING_API_KEY")),
                batch_size=100,
                cache_ttl=300,  # 5 minutes
                max_memory_size=1000,  # 1GB
                compression_enabled=True
            ),
            health_check_interval=60,
            enable_monitoring=True,
            log_level="INFO"
        )
        
        # Production configuration
        self.configs["production"] = MemoryEnvironmentConfig(
            name="production",
            description="Production environment with high performance settings",
            memory_config=ClaudePMConfig(
                host=os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_PROD_HOST", os.getenv("CLAUDE_PM_MEMORY_PROD_HOST", "memory-service.internal")),
                port=int(os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_PROD_PORT", os.getenv("CLAUDE_PM_MEMORY_PROD_PORT", "8002"))),
                timeout=30,
                max_retries=3,
                retry_delay=1.0,
                connection_pool_size=50,
                enable_logging=True,
                api_key=os.getenv("CLAUDE_MULTIAGENT_PM_MEMORY_PROD_API_KEY", os.getenv("CLAUDE_PM_MEMORY_PROD_API_KEY")),
                batch_size=200,
                cache_ttl=600,  # 10 minutes
                max_memory_size=2000,  # 2GB
                compression_enabled=True
            ),
            health_check_interval=120,
            enable_monitoring=True,
            log_level="INFO"
        )
    
    def get_config(self, environment: Optional[str] = None) -> MemoryEnvironmentConfig:
        """
        Get configuration for specified environment.
        
        Args:
            environment: Environment name. If None, uses ENVIRONMENT env var or 'development'
            
        Returns:
            MemoryEnvironmentConfig: Configuration for the environment
        """
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        
        if environment not in self.configs:
            raise ValueError(f"Unknown environment: {environment}. Available: {list(self.configs.keys())}")
        
        return self.configs[environment]
    
    def create_memory_service(self, environment: Optional[str] = None) -> ClaudePMMemory:
        """
        Create ClaudePMMemory instance for specified environment.
        
        Args:
            environment: Environment name
            
        Returns:
            ClaudePMMemory: Configured memory service instance
        """
        config = self.get_config(environment)
        return ClaudePMMemory(config.memory_config)
    
    def get_all_environments(self) -> Dict[str, str]:
        """Get all available environments with descriptions."""
        return {name: config.description for name, config in self.configs.items()}
    
    def validate_environment(self, environment: str) -> bool:
        """Validate that an environment configuration is complete."""
        try:
            config = self.get_config(environment)
            
            # Check required fields
            if not config.memory_config.host:
                return False
            
            if config.memory_config.port <= 0:
                return False
            
            if config.memory_config.timeout <= 0:
                return False
            
            return True
            
        except Exception:
            return False


# Global configuration manager instance
config_manager = MemoryConfigManager()


def get_memory_config(environment: Optional[str] = None) -> ClaudePMConfig:
    """
    Get memory configuration for environment.
    
    Args:
        environment: Environment name
        
    Returns:
        ClaudePMConfig: Memory service configuration
    """
    return config_manager.get_config(environment).memory_config


def create_memory_service(environment: Optional[str] = None) -> ClaudePMMemory:
    """
    Factory function to create memory service for environment.
    
    Args:
        environment: Environment name
        
    Returns:
        ClaudePMMemory: Configured memory service instance
    """
    return config_manager.create_memory_service(environment)


def get_environment_info() -> Dict[str, Any]:
    """
    Get information about current environment and configuration.
    
    Returns:
        Dict: Environment information
    """
    current_env = os.getenv("ENVIRONMENT", "development")
    config = config_manager.get_config(current_env)
    
    return {
        "current_environment": current_env,
        "available_environments": config_manager.get_all_environments(),
        "configuration": {
            "host": config.memory_config.host,
            "port": config.memory_config.port,
            "timeout": config.memory_config.timeout,
            "connection_pool_size": config.memory_config.connection_pool_size,
            "enable_logging": config.memory_config.enable_logging,
            "health_check_interval": config.health_check_interval,
            "log_level": config.log_level
        },
        "validation": {
            env: config_manager.validate_environment(env) 
            for env in config_manager.configs.keys()
        }
    }


# Configuration validation functions

def validate_memory_service_config(config: ClaudePMConfig) -> Dict[str, Any]:
    """
    Validate memory service configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        Dict: Validation results
    """
    results = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "suggestions": []
    }
    
    # Check required fields
    if not config.host:
        results["errors"].append("Host is required")
        results["valid"] = False
    
    if config.port <= 0 or config.port > 65535:
        results["errors"].append("Port must be between 1 and 65535")
        results["valid"] = False
    
    if config.timeout <= 0:
        results["errors"].append("Timeout must be positive")
        results["valid"] = False
    
    # Check warnings
    if config.connection_pool_size < 5:
        results["warnings"].append("Connection pool size is quite small")
    
    if config.connection_pool_size > 100:
        results["warnings"].append("Connection pool size is very large")
    
    if config.timeout < 5:
        results["warnings"].append("Timeout is very short, may cause failures")
    
    if config.max_retries > 5:
        results["warnings"].append("High retry count may cause long delays")
    
    # Check suggestions
    if not config.enable_logging:
        results["suggestions"].append("Consider enabling logging for better debugging")
    
    if config.cache_ttl < 60:
        results["suggestions"].append("Very short cache TTL may reduce performance")
    
    if not config.compression_enabled and config.max_memory_size > 1000:
        results["suggestions"].append("Consider enabling compression for large memory limits")
    
    return results


# Environment-specific factory functions

def create_development_memory() -> ClaudePMMemory:
    """Create memory service for development environment."""
    return create_memory_service("development")


def create_testing_memory() -> ClaudePMMemory:
    """Create memory service for testing environment."""
    return create_memory_service("testing")


def create_staging_memory() -> ClaudePMMemory:
    """Create memory service for staging environment."""
    return create_memory_service("staging")


def create_production_memory() -> ClaudePMMemory:
    """Create memory service for production environment."""
    return create_memory_service("production")


# Configuration utilities

def print_environment_info():
    """Print detailed environment information."""
    info = get_environment_info()
    
    print("🧠 ClaudePM Memory Configuration")
    print("=" * 50)
    print(f"Current Environment: {info['current_environment']}")
    print(f"Host: {info['configuration']['host']}")
    print(f"Port: {info['configuration']['port']}")
    print(f"Connection Pool: {info['configuration']['connection_pool_size']}")
    print(f"Health Check Interval: {info['configuration']['health_check_interval']}s")
    print(f"Log Level: {info['configuration']['log_level']}")
    print()
    
    print("Available Environments:")
    for env, desc in info['available_environments'].items():
        status = "✅" if info['validation'][env] else "❌"
        print(f"  {status} {env}: {desc}")
    print()


def export_config_to_file(environment: str, file_path: str):
    """
    Export configuration to file.
    
    Args:
        environment: Environment to export
        file_path: Path to export file
    """
    import json
    
    config = config_manager.get_config(environment)
    
    config_dict = {
        "environment": environment,
        "description": config.description,
        "memory_service": {
            "host": config.memory_config.host,
            "port": config.memory_config.port,
            "timeout": config.memory_config.timeout,
            "max_retries": config.memory_config.max_retries,
            "retry_delay": config.memory_config.retry_delay,
            "connection_pool_size": config.memory_config.connection_pool_size,
            "enable_logging": config.memory_config.enable_logging,
            "batch_size": config.memory_config.batch_size,
            "cache_ttl": config.memory_config.cache_ttl,
            "max_memory_size": config.memory_config.max_memory_size,
            "compression_enabled": config.memory_config.compression_enabled
        },
        "monitoring": {
            "health_check_interval": config.health_check_interval,
            "enable_monitoring": config.enable_monitoring,
            "log_level": config.log_level
        }
    }
    
    with open(file_path, 'w') as f:
        json.dump(config_dict, f, indent=2)
    
    print(f"Configuration exported to: {file_path}")


if __name__ == "__main__":
    # Print environment information when run directly
    print_environment_info()
    
    # Validate all configurations
    print("Configuration Validation:")
    print("-" * 30)
    
    for env_name in config_manager.configs.keys():
        config = config_manager.get_config(env_name)
        validation = validate_memory_service_config(config.memory_config)
        
        status = "✅ Valid" if validation["valid"] else "❌ Invalid"
        print(f"{env_name}: {status}")
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"  ⚠️  {warning}")
        
        if validation["errors"]:
            for error in validation["errors"]:
                print(f"  ❌ {error}")
        
        if validation["suggestions"]:
            for suggestion in validation["suggestions"]:
                print(f"  💡 {suggestion}")
        
        print()
    
    # Test basic connectivity (if service is available)
    print("Testing Connectivity:")
    print("-" * 20)
    
    import asyncio
    
    async def test_connection():
        try:
            memory = create_development_memory()
            connected = await memory.connect()
            
            if connected:
                print("✅ Connection successful")
                stats = memory.get_statistics()
                print(f"📊 Service ready - Pool size: {stats['config']['connection_pool_size']}")
                await memory.disconnect()
            else:
                print("❌ Connection failed")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    try:
        asyncio.run(test_connection())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Make sure mem0AI service is running on localhost:8002")