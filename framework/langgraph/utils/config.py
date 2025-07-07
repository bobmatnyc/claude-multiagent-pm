"""
Configuration management for LangGraph workflows.

Loads and manages configuration settings for Claude PM LangGraph integration,
including model routing, workflow parameters, and checkpointing settings.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from ....core.logging_config import get_logger
except ImportError:
    # Fallback for testing
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class LangGraphConfig:
    """Configuration manager for LangGraph workflows."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default locations.
        """
        self.config_path = self._find_config_file(config_path)
        self.config = self._load_config()
        
    def _find_config_file(self, config_path: Optional[str]) -> Path:
        """Find configuration file in default locations."""
        if config_path:
            return Path(config_path)
        
        # Try common locations
        candidates = [
            Path.cwd() / "config" / "langgraph_config.yaml",
            Path.cwd() / "langgraph_config.yaml",
            Path.home() / ".claude-pm" / "langgraph_config.yaml"
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        # Return default location even if it doesn't exist
        return candidates[0]
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded LangGraph config from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file not found at {self.config_path}, using defaults")
                return self._get_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "langgraph": {
                "checkpointer": {
                    "type": "sqlite",
                    "path": ".claude-pm/checkpoints.db"
                },
                "models": {
                    "orchestrator": "claude-3-5-sonnet-20241022",
                    "architect": "claude-3-5-sonnet-20241022", 
                    "engineer": "claude-3-5-sonnet-20241022",
                    "qa": "claude-3-5-sonnet-20241022",
                    "researcher": "claude-3-5-sonnet-20241022",
                    "code_review": "claude-3-5-sonnet-20241022"
                },
                "workflows": {
                    "task": {
                        "max_iterations": 5,
                        "timeout_seconds": 300,
                        "parallel_agents": 3
                    },
                    "project": {
                        "checkpoint_frequency": "after_each_milestone",
                        "max_concurrent_tasks": 5
                    }
                },
                "cost_tracking": {
                    "track_token_usage": True,
                    "alert_threshold": 1000000,
                    "daily_limit": 10000000
                },
                "human_approval": {
                    "required_for": ["complex_tasks", "security_changes", "database_migrations"],
                    "notification_channels": ["cli", "file"],
                    "timeout_minutes": 60
                }
            },
            "directories": {
                "langgraph_root": "framework/langgraph",
                "states": "framework/langgraph/states",
                "nodes": "framework/langgraph/nodes", 
                "graphs": "framework/langgraph/graphs",
                "routers": "framework/langgraph/routers",
                "utils": "framework/langgraph/utils"
            },
            "persistence": {
                "enabled": True,
                "backend": "sqlite",
                "database_path": ".claude-pm/checkpoints.db",
                "retention_days": 30,
                "cleanup_interval_hours": 24
            },
            "monitoring": {
                "enabled": True,
                "metrics_collection": True,
                "export_format": "json",
                "metrics_file": "logs/langgraph_metrics.json"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_model_for_agent(self, agent_name: str) -> str:
        """Get the model configuration for a specific agent."""
        model = self.get(f"langgraph.models.{agent_name}")
        if model:
            return model
        
        # Fallback to default model
        return self.get("langgraph.models.engineer", "claude-3-5-sonnet-20241022")
    
    def get_checkpointer_config(self) -> Dict[str, Any]:
        """Get checkpointer configuration."""
        return self.get("langgraph.checkpointer", {
            "type": "sqlite",
            "path": ".claude-pm/checkpoints.db"
        })
    
    def get_workflow_config(self, workflow_type: str) -> Dict[str, Any]:
        """Get configuration for a specific workflow type."""
        return self.get(f"langgraph.workflows.{workflow_type}", {})
    
    def is_human_approval_required(self, task_type: str) -> bool:
        """Check if human approval is required for a task type."""
        required_types = self.get("langgraph.human_approval.required_for", [])
        return task_type in required_types
    
    def get_cost_limits(self) -> Dict[str, int]:
        """Get cost tracking limits."""
        return {
            "alert_threshold": self.get("langgraph.cost_tracking.alert_threshold", 1000000),
            "daily_limit": self.get("langgraph.cost_tracking.daily_limit", 10000000)
        }
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
        logger.info("Configuration reloaded")


# Global configuration instance
_config_instance: Optional[LangGraphConfig] = None


def load_langgraph_config(config_path: Optional[str] = None) -> LangGraphConfig:
    """
    Load or get the global LangGraph configuration instance.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        LangGraphConfig: Configuration manager instance
    """
    global _config_instance
    
    if _config_instance is None or config_path is not None:
        _config_instance = LangGraphConfig(config_path)
    
    return _config_instance


def get_model_for_agent(agent_name: str) -> str:
    """
    Get the model configuration for a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        str: Model identifier for the agent
    """
    config = load_langgraph_config()
    return config.get_model_for_agent(agent_name)