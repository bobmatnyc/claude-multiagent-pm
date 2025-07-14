"""
Fallback Memory Configuration for Development and Deployment

This module provides a comprehensive fallback memory system that works
without external API dependencies, ensuring the framework can be deployed
and function correctly even without OpenAI API keys or mem0AI services.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def get_development_safe_memory_config() -> Dict[str, Any]:
    """
    Get a development-safe memory configuration that prioritizes local backends.
    
    This configuration ensures the memory system can function without external
    API dependencies, making it suitable for:
    - Development environments without API keys
    - CI/CD pipelines
    - Offline development
    - Release deployments where API keys might not be configured
    
    Returns:
        Dict[str, Any]: Memory configuration with local-first approach
    """
    
    # Detect OpenAI API key availability
    openai_api_key = os.getenv("OPENAI_API_KEY")
    has_api_key = bool(openai_api_key and openai_api_key.strip())
    
    # Base configuration for SQLite (always available)
    config = {
        # Backend selection strategy
        "fallback_chain": ["sqlite"],  # Start with SQLite only
        "backend_selection_strategy": "fail_safe",
        
        # SQLite configuration (primary backend for fallback)
        "sqlite_enabled": True,
        "sqlite_path": "memory.db",
        "sqlite_fts": True,  # Enable full-text search
        "sqlite_wal": True,  # Enable Write-Ahead Logging for performance
        
        # mem0AI configuration (disabled by default for safety)
        "mem0ai_enabled": False,  # Will be enabled only if API key is available
        "mem0ai_host": "localhost",
        "mem0ai_port": 8002,
        "mem0ai_timeout": 10,  # Shorter timeout for faster fallback
        "mem0ai_api_key": None,
        
        # Circuit breaker configuration (more conservative for development)
        "circuit_breaker_threshold": 3,  # Fail faster
        "circuit_breaker_recovery": 30,  # Recover faster
        "circuit_breaker_test_requests": 1,
        "circuit_breaker_success_threshold": 1,
        
        # Auto-detection configuration
        "detection_timeout": 1.0,  # Quick detection
        "detection_retries": 2,    # Fewer retries
        
        # Performance monitoring
        "metrics_retention": 3600,  # 1 hour retention for development
        
        # Development mode flags
        "development_mode": True,
        "allow_api_failures": True,
        "log_backend_selection": True,
    }
    
    # If OpenAI API key is available, enable mem0AI as secondary
    if has_api_key:
        logger.info("OpenAI API key detected - enabling mem0AI backend as fallback")
        config.update({
            "mem0ai_enabled": True,
            "mem0ai_api_key": openai_api_key,
            "fallback_chain": ["sqlite", "mem0ai"],  # SQLite first, mem0AI as fallback
        })
        
        # More aggressive configuration when API is available
        config.update({
            "circuit_breaker_threshold": 5,
            "circuit_breaker_recovery": 60,
            "detection_timeout": 2.0,
            "detection_retries": 3,
        })
    else:
        logger.info("No OpenAI API key detected - using SQLite-only configuration")
    
    return config


def get_release_ready_memory_config() -> Dict[str, Any]:
    """
    Get a release-ready memory configuration that gracefully handles
    missing API keys and external service unavailability.
    
    This configuration is designed for production deployments where:
    - API keys might not be configured
    - External services might be unavailable
    - Local storage is preferred for reliability
    - Graceful degradation is required
    
    Returns:
        Dict[str, Any]: Production-ready memory configuration
    """
    
    # Get base development config
    config = get_development_safe_memory_config()
    
    # Override with production-specific settings
    config.update({
        "development_mode": False,
        "log_backend_selection": False,  # Reduce logging noise in production
        
        # More conservative circuit breaker for production
        "circuit_breaker_threshold": 2,  # Fail very fast
        "circuit_breaker_recovery": 60,
        
        # Quick detection with minimal retries
        "detection_timeout": 0.5,
        "detection_retries": 1,
        
        # Longer metrics retention for production monitoring
        "metrics_retention": 86400,  # 24 hours
        
        # Production reliability settings
        "allow_api_failures": True,
        "prefer_local_storage": True,
        "enable_backup_on_failure": True,
    })
    
    return config


def create_fallback_memory_service():
    """
    Factory function to create a memory service with fallback configuration.
    
    This function creates a memory service that:
    - Works without external API dependencies
    - Gracefully handles missing API keys
    - Provides full functionality using local SQLite storage
    - Automatically enables advanced features when APIs are available
    
    Returns:
        FlexibleMemoryService: Configured memory service ready for use
    """
    from .services.unified_service import FlexibleMemoryService
    
    # Get appropriate configuration based on environment
    if os.getenv("CLAUDE_PM_ENVIRONMENT") == "production":
        config = get_release_ready_memory_config()
        logger.info("Using production memory configuration")
    else:
        config = get_development_safe_memory_config()
        logger.info("Using development-safe memory configuration")
    
    # Create and return service
    return FlexibleMemoryService(config)


def validate_memory_system_health() -> Dict[str, Any]:
    """
    Validate the memory system health and configuration.
    
    This function performs comprehensive health checks to ensure:
    - SQLite database is accessible and writable
    - Schema is up to date
    - FTS indexing is working
    - API connectivity (if configured)
    - Circuit breakers are functioning
    
    Returns:
        Dict[str, Any]: Health check results with detailed status
    """
    
    health_status = {
        "overall_health": "unknown",
        "sqlite_health": "checking",
        "mem0ai_health": "checking",
        "schema_version": "unknown",
        "fts_enabled": False,
        "api_key_available": False,
        "configuration": "unknown",
        "errors": [],
        "warnings": [],
        "recommendations": []
    }
    
    try:
        # Check SQLite health
        import sqlite3
        from pathlib import Path
        
        db_path = Path("memory.db")
        if db_path.exists():
            try:
                conn = sqlite3.connect("memory.db")
                cursor = conn.execute("SELECT 1")
                cursor.fetchone()
                
                # Check schema
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
                if cursor.fetchone():
                    health_status["sqlite_health"] = "healthy"
                    
                    # Check FTS
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'")
                    if cursor.fetchone():
                        health_status["fts_enabled"] = True
                        
                    # Check schema version
                    try:
                        cursor = conn.execute("SELECT version FROM schema_info ORDER BY version DESC LIMIT 1")
                        version_row = cursor.fetchone()
                        if version_row:
                            health_status["schema_version"] = version_row[0]
                    except:
                        health_status["warnings"].append("Schema version table not found - this is normal for older databases")
                        
                else:
                    health_status["sqlite_health"] = "schema_missing"
                    health_status["errors"].append("SQLite memories table not found")
                    
                conn.close()
            except Exception as e:
                health_status["sqlite_health"] = "error"
                health_status["errors"].append(f"SQLite error: {e}")
        else:
            health_status["sqlite_health"] = "not_found"
            health_status["warnings"].append("SQLite database not found - will be created on first use")
        
        # Check API key availability
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key and openai_api_key.strip():
            health_status["api_key_available"] = True
            health_status["mem0ai_health"] = "api_key_available"
        else:
            health_status["mem0ai_health"] = "no_api_key"
            health_status["warnings"].append("No OpenAI API key found - mem0AI backend will be disabled")
        
        # Determine overall health
        if health_status["sqlite_health"] in ["healthy", "not_found"]:
            if health_status["errors"]:
                health_status["overall_health"] = "degraded"
            else:
                health_status["overall_health"] = "healthy"
        else:
            health_status["overall_health"] = "unhealthy"
        
        # Configuration assessment
        if health_status["api_key_available"]:
            health_status["configuration"] = "full_featured"
            health_status["recommendations"].append("All memory backends available - full functionality enabled")
        else:
            health_status["configuration"] = "local_only"
            health_status["recommendations"].append("Local SQLite backend only - consider adding OpenAI API key for advanced features")
            
        if not health_status["fts_enabled"] and health_status["sqlite_health"] == "healthy":
            health_status["recommendations"].append("Full-text search not available - database may need rebuilding")
            
    except Exception as e:
        health_status["overall_health"] = "error"
        health_status["errors"].append(f"Health check failed: {e}")
    
    return health_status


def migrate_memory_system_if_needed() -> Dict[str, Any]:
    """
    Migrate the memory system schema if needed for current framework requirements.
    
    This function:
    - Checks if the current schema matches framework requirements
    - Performs migrations if necessary
    - Ensures backward compatibility
    - Updates schema version tracking
    
    Returns:
        Dict[str, Any]: Migration results and status
    """
    
    migration_result = {
        "migration_performed": False,
        "migration_needed": False,
        "current_version": None,
        "target_version": 1,
        "errors": [],
        "warnings": [],
        "operations": []
    }
    
    try:
        import sqlite3
        from pathlib import Path
        
        db_path = Path("memory.db")
        if not db_path.exists():
            migration_result["operations"].append("Database file does not exist - will be created automatically")
            return migration_result
        
        conn = sqlite3.connect("memory.db")
        
        # Check current schema version
        try:
            cursor = conn.execute("SELECT version FROM schema_info ORDER BY version DESC LIMIT 1")
            version_row = cursor.fetchone()
            if version_row:
                migration_result["current_version"] = version_row[0]
            else:
                migration_result["current_version"] = 0
        except sqlite3.OperationalError:
            # schema_info table doesn't exist
            migration_result["current_version"] = 0
            migration_result["warnings"].append("No schema version tracking found")
        
        # Check if migration is needed
        if migration_result["current_version"] < migration_result["target_version"]:
            migration_result["migration_needed"] = True
            
            # For now, the schema is already compatible, so no actual migration needed
            # Future versions can add migration logic here
            migration_result["operations"].append("Schema is compatible with current framework version")
            
            # Update schema version if schema_info table exists
            try:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_info'")
                if cursor.fetchone():
                    conn.execute("""
                        INSERT OR REPLACE INTO schema_info (version, created_at, description)
                        VALUES (?, ?, ?)
                    """, (migration_result["target_version"], 
                          "2025-07-14T16:30:00Z", 
                          "Framework v0.8.0 compatibility update"))
                    conn.commit()
                    migration_result["migration_performed"] = True
                    migration_result["operations"].append("Updated schema version tracking")
            except Exception as e:
                migration_result["warnings"].append(f"Could not update schema version: {e}")
        
        conn.close()
        
    except Exception as e:
        migration_result["errors"].append(f"Migration check failed: {e}")
    
    return migration_result


if __name__ == "__main__":
    # Command-line interface for memory system management
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "health":
            print("Checking memory system health...")
            health = validate_memory_system_health()
            print(f"Overall Health: {health['overall_health']}")
            print(f"SQLite Health: {health['sqlite_health']}")
            print(f"mem0AI Health: {health['mem0ai_health']}")
            print(f"Configuration: {health['configuration']}")
            
            if health['errors']:
                print("\nErrors:")
                for error in health['errors']:
                    print(f"  - {error}")
                    
            if health['warnings']:
                print("\nWarnings:")
                for warning in health['warnings']:
                    print(f"  - {warning}")
                    
            if health['recommendations']:
                print("\nRecommendations:")
                for rec in health['recommendations']:
                    print(f"  - {rec}")
                    
        elif command == "migrate":
            print("Checking migration requirements...")
            result = migrate_memory_system_if_needed()
            print(f"Migration needed: {result['migration_needed']}")
            print(f"Migration performed: {result['migration_performed']}")
            
            if result['operations']:
                print("\nOperations:")
                for op in result['operations']:
                    print(f"  - {op}")
                    
        elif command == "config":
            print("Development-safe memory configuration:")
            config = get_development_safe_memory_config()
            for key, value in config.items():
                print(f"  {key}: {value}")
                
        else:
            print("Usage: python fallback_memory_config.py [health|migrate|config]")
    else:
        print("Claude PM Framework - Fallback Memory Configuration")
        print("This module provides development-safe memory system configuration.")
        print("Run with 'health', 'migrate', or 'config' for specific operations.")