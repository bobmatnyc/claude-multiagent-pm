"""
Configuration Fixtures for E2E Testing

Provides pre-configured settings and configurations for testing.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import os


class ConfigFixtures:
    """Collection of configuration fixtures for testing."""
    
    @staticmethod
    def base_config() -> Dict[str, Any]:
        """Create a base configuration fixture."""
        return {
            "version": "0.7.0",
            "framework": {
                "name": "claude-multiagent-pm",
                "version": "0.7.0",
                "test_mode": True
            },
            "agents": {
                "discovery": {
                    "enabled": True,
                    "directories": [
                        ".claude-pm/agents/project-specific",
                        "~/.claude-pm/agents/user-defined",
                        "claude_pm/agents"
                    ],
                    "cache_enabled": True
                }
            },
            "orchestration": {
                "mode": "subprocess",
                "timeout": 300,
                "max_retries": 3
            },
            "logging": {
                "level": "DEBUG",
                "file": "test.log",
                "console": True
            }
        }
    
    @staticmethod
    def test_environment_config() -> Dict[str, str]:
        """Create test environment variables."""
        return {
            "CLAUDE_PM_TEST_MODE": "1",
            "CLAUDE_PM_LOG_LEVEL": "DEBUG",
            "CLAUDE_PM_CACHE_DISABLED": "0",
            "CLAUDE_PM_SUBPROCESS_TIMEOUT": "30",
            "OPENAI_API_KEY": "test-key-123",
            "ANTHROPIC_API_KEY": "test-key-456"
        }
    
    @staticmethod
    def agent_registry_config() -> Dict[str, Any]:
        """Create agent registry configuration."""
        return {
            "registry": {
                "version": "1.0.0",
                "cache": {
                    "enabled": True,
                    "ttl": 3600,
                    "max_size": 100
                },
                "discovery": {
                    "scan_interval": 60,
                    "file_patterns": ["*.md"],
                    "exclude_patterns": ["test_*", "*.backup"]
                },
                "precedence": {
                    "order": ["project", "user", "system"],
                    "override_enabled": True
                }
            }
        }
    
    @staticmethod
    def orchestrator_config(mode: str = "subprocess") -> Dict[str, Any]:
        """Create orchestrator configuration."""
        return {
            "orchestrator": {
                "mode": mode,
                "subprocess": {
                    "python_executable": "python3",
                    "timeout": 300,
                    "memory_limit": "1GB",
                    "env_isolation": True
                },
                "local": {
                    "async_enabled": True,
                    "thread_pool_size": 4
                },
                "error_handling": {
                    "max_retries": 3,
                    "retry_delay": 1,
                    "fallback_enabled": True
                }
            }
        }
    
    @staticmethod
    def project_config(project_name: str = "test_project") -> Dict[str, Any]:
        """Create project-specific configuration."""
        return {
            "project": {
                "name": project_name,
                "version": "0.1.0",
                "description": "Test project for E2E testing"
            },
            "settings": {
                "auto_setup": True,
                "agent_precedence": "project",
                "custom_agents_enabled": True
            },
            "integrations": {
                "git": {
                    "enabled": True,
                    "auto_commit": False
                },
                "ticketing": {
                    "system": "github",
                    "enabled": True
                }
            }
        }
    
    @staticmethod
    def memory_config() -> Dict[str, Any]:
        """Create memory system configuration."""
        return {
            "memory": {
                "enabled": True,
                "backend": "json",
                "location": ".claude-pm/memory",
                "retention": {
                    "max_age_days": 30,
                    "max_entries": 1000,
                    "cleanup_interval": 3600
                },
                "indexing": {
                    "enabled": True,
                    "fields": ["timestamp", "agent", "task", "status"]
                }
            }
        }
    
    @staticmethod
    def create_config_file(config_dir: Path, config_name: str, 
                          config_data: Dict[str, Any]) -> Path:
        """Create a configuration file."""
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / f"{config_name}.json"
        
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)
        
        return config_file
    
    @staticmethod
    def mock_api_config() -> Dict[str, Any]:
        """Create mock API configuration for testing."""
        return {
            "apis": {
                "openai": {
                    "base_url": "http://localhost:8080/mock/openai",
                    "api_key": "test-key",
                    "model": "gpt-4",
                    "timeout": 30
                },
                "anthropic": {
                    "base_url": "http://localhost:8080/mock/anthropic",
                    "api_key": "test-key",
                    "model": "claude-3",
                    "timeout": 30
                }
            },
            "mock_responses": {
                "enabled": True,
                "delay": 0.1,
                "success_rate": 1.0
            }
        }
    
    @staticmethod
    def performance_config() -> Dict[str, Any]:
        """Create performance testing configuration."""
        return {
            "performance": {
                "benchmarks": {
                    "agent_discovery": {
                        "target_ms": 50,
                        "max_ms": 200
                    },
                    "prompt_loading": {
                        "target_ms": 10,
                        "max_ms": 50
                    },
                    "subprocess_creation": {
                        "target_ms": 100,
                        "max_ms": 500
                    }
                },
                "profiling": {
                    "enabled": True,
                    "output_dir": "tests/reports/performance"
                }
            }
        }
    
    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries."""
        result = {}
        for config in configs:
            result = ConfigFixtures._deep_merge(result, config)
        return result
    
    @staticmethod
    def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigFixtures._deep_merge(result[key], value)
            else:
                result[key] = value
        return result