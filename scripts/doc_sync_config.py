#!/usr/bin/env python3
"""
Documentation Synchronization Configuration Management
Part of M01-041: Implement Documentation Status Synchronization System

This module provides centralized configuration management for the documentation 
synchronization system, integrating with the Claude PM health monitoring infrastructure.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class DocSyncConfig:
    """Configuration for documentation synchronization system"""
    
    # Basic paths
    claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"
    
    # Sync intervals (in seconds)
    sync_interval: int = 300  # 5 minutes
    notification_check_interval: int = 600  # 10 minutes
    force_sync_interval: int = 3600  # 1 hour
    
    # Notification settings
    significant_change_threshold: float = 5.0  # 5% change
    notification_cooldown: int = 3600  # 1 hour
    alert_on_inconsistencies: bool = True
    
    # Health monitoring integration
    health_monitoring_enabled: bool = True
    health_check_interval: int = 1800  # 30 minutes
    
    # Validation settings
    strict_validation: bool = True
    auto_fix_inconsistencies: bool = False
    
    # Logging configuration
    log_level: str = "INFO"
    max_log_files: int = 10
    max_report_files: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocSyncConfig':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

class DocSyncConfigManager:
    """Manages configuration for documentation synchronization system"""
    
    def __init__(self, claude_pm_root: Optional[str] = None):
        self.claude_pm_root = Path(claude_pm_root or "/Users/masa/Projects/claude-multiagent-pm")
        self.config_file = self.claude_pm_root / "config" / "doc_sync_config.json"
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for configuration management"""
        logger = logging.getLogger('DocSyncConfig')
        logger.setLevel(logging.INFO)
        
        # Create console handler if not already present
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def load_config(self) -> DocSyncConfig:
        """Load configuration from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    config = DocSyncConfig.from_dict(data)
                    # Update claude_pm_root to current path
                    config.claude_pm_root = str(self.claude_pm_root)
                    self.logger.info(f"Loaded configuration from {self.config_file}")
                    return config
            else:
                self.logger.info("No configuration file found, using defaults")
                return DocSyncConfig(claude_pm_root=str(self.claude_pm_root))
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.logger.info("Using default configuration")
            return DocSyncConfig(claude_pm_root=str(self.claude_pm_root))
    
    def save_config(self, config: DocSyncConfig) -> bool:
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            self.logger.info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def update_config(self, **kwargs) -> DocSyncConfig:
        """Update configuration with new values"""
        config = self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
                self.logger.info(f"Updated {key} = {value}")
            else:
                self.logger.warning(f"Unknown configuration key: {key}")
        
        self.save_config(config)
        return config
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables"""
        env_config = {}
        
        # Environment variable mappings
        env_mappings = {
            'CLAUDE_PM_DOC_SYNC_INTERVAL': ('sync_interval', int),
            'CLAUDE_PM_DOC_NOTIFICATION_INTERVAL': ('notification_check_interval', int),
            'CLAUDE_PM_DOC_FORCE_SYNC_INTERVAL': ('force_sync_interval', int),
            'CLAUDE_PM_DOC_CHANGE_THRESHOLD': ('significant_change_threshold', float),
            'CLAUDE_PM_DOC_COOLDOWN': ('notification_cooldown', int),
            'CLAUDE_PM_DOC_HEALTH_MONITORING': ('health_monitoring_enabled', lambda x: x.lower() == 'true'),
            'CLAUDE_PM_DOC_STRICT_VALIDATION': ('strict_validation', lambda x: x.lower() == 'true'),
            'CLAUDE_PM_DOC_AUTO_FIX': ('auto_fix_inconsistencies', lambda x: x.lower() == 'true'),
            'CLAUDE_PM_DOC_LOG_LEVEL': ('log_level', str),
        }
        
        for env_var, (config_key, type_converter) in env_mappings.items():
            if env_var in os.environ:
                try:
                    env_config[config_key] = type_converter(os.environ[env_var])
                    self.logger.info(f"Environment override: {config_key} = {env_config[config_key]}")
                except Exception as e:
                    self.logger.error(f"Error parsing environment variable {env_var}: {e}")
        
        return env_config
    
    def get_effective_config(self) -> DocSyncConfig:
        """Get effective configuration with environment overrides applied"""
        config = self.load_config()
        env_config = self.get_environment_config()
        
        # Apply environment overrides
        for key, value in env_config.items():
            setattr(config, key, value)
        
        return config
    
    def validate_config(self, config: DocSyncConfig) -> bool:
        """Validate configuration values"""
        try:
            # Validate paths
            if not Path(config.claude_pm_root).exists():
                self.logger.error(f"Claude PM root directory does not exist: {config.claude_pm_root}")
                return False
            
            # Validate intervals
            if config.sync_interval <= 0:
                self.logger.error("Sync interval must be positive")
                return False
            
            if config.notification_check_interval <= 0:
                self.logger.error("Notification check interval must be positive")
                return False
            
            # Validate thresholds
            if not (0 <= config.significant_change_threshold <= 100):
                self.logger.error("Significant change threshold must be between 0 and 100")
                return False
            
            # Validate log level
            valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if config.log_level not in valid_log_levels:
                self.logger.error(f"Invalid log level: {config.log_level}")
                return False
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
            return False
    
    def create_default_config(self) -> bool:
        """Create default configuration file"""
        try:
            config = DocSyncConfig(claude_pm_root=str(self.claude_pm_root))
            return self.save_config(config)
        except Exception as e:
            self.logger.error(f"Error creating default configuration: {e}")
            return False
    
    def reset_config(self) -> bool:
        """Reset configuration to defaults"""
        try:
            if self.config_file.exists():
                backup_path = self.config_file.with_suffix('.json.backup')
                self.config_file.rename(backup_path)
                self.logger.info(f"Backed up existing config to {backup_path}")
            
            return self.create_default_config()
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False

def main():
    """Main entry point for configuration management"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Documentation Synchronization Configuration Management"
    )
    parser.add_argument(
        "--claude-pm-root",
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show current configuration"
    )
    parser.add_argument(
        "--create-default",
        action="store_true",
        help="Create default configuration file"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset configuration to defaults"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current configuration"
    )
    parser.add_argument(
        "--set",
        nargs=2,
        metavar=('KEY', 'VALUE'),
        action='append',
        help="Set configuration value (can be used multiple times)"
    )
    
    args = parser.parse_args()
    
    config_manager = DocSyncConfigManager(args.claude_pm_root)
    
    if args.create_default:
        success = config_manager.create_default_config()
        print(f"{'✅' if success else '❌'} Default configuration created")
        return 0 if success else 1
    
    if args.reset:
        success = config_manager.reset_config()
        print(f"{'✅' if success else '❌'} Configuration reset")
        return 0 if success else 1
    
    if args.set:
        updates = {}
        for key, value in args.set:
            # Try to convert value to appropriate type
            if value.lower() in ('true', 'false'):
                updates[key] = value.lower() == 'true'
            elif value.isdigit():
                updates[key] = int(value)
            elif '.' in value and value.replace('.', '').isdigit():
                updates[key] = float(value)
            else:
                updates[key] = value
        
        config = config_manager.update_config(**updates)
        print("✅ Configuration updated")
    
    if args.validate:
        config = config_manager.get_effective_config()
        valid = config_manager.validate_config(config)
        print(f"{'✅' if valid else '❌'} Configuration validation")
        if not valid:
            return 1
    
    if args.show_config or not any([args.create_default, args.reset, args.set, args.validate]):
        config = config_manager.get_effective_config()
        print("📋 Current Configuration:")
        print(json.dumps(config.to_dict(), indent=2))
    
    return 0

if __name__ == "__main__":
    exit(main())