#!/usr/bin/env python3
"""
Centralized Version Loading Utility for Claude PM Framework.

This module provides a unified interface for loading version information
from various sources (VERSION file, package.json, etc.) and ensures
consistency across all framework components.

Features:
- Dynamic version loading from multiple sources
- Package.json version extraction
- Framework version detection
- Service version loading
- Cached version information for performance
- Fallback mechanisms for missing version files

Usage:
    from claude_pm.utils.version_loader import get_package_version, get_framework_version
    
    # Get package version (from package.json or VERSION file)
    package_version = get_package_version()
    
    # Get framework version (from framework/VERSION file)
    framework_version = get_framework_version()
    
    # Get service version
    service_version = get_service_version("memory")
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache
import sys

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

from ..core.logging_config import setup_logging

logger = setup_logging(__name__)


class VersionLoader:
    """Centralized version loading utility."""
    
    def __init__(self, framework_root: Optional[Path] = None):
        """
        Initialize version loader.
        
        Args:
            framework_root: Path to framework root directory
        """
        self.framework_root = framework_root or self._detect_framework_root()
        self._version_cache: Dict[str, str] = {}
    
    def _detect_framework_root(self) -> Path:
        """Detect framework root directory."""
        # Try environment variable first
        if framework_path := os.getenv('CLAUDE_PM_FRAMEWORK_PATH'):
            return Path(framework_path)
        
        # Check if we're running from a wheel/installed package
        if self._is_wheel_installation():
            # For wheel installations, return the package directory itself
            return Path(__file__).parent.parent
        
        # Try from current module path (source installation)
        current_file = Path(__file__)
        
        # Go up from claude_pm/utils/version_loader.py to find root
        potential_root = current_file.parent.parent.parent
        
        # Look for key files to confirm we're in the right place
        if (potential_root / 'package.json').exists():
            return potential_root
        
        if (potential_root / 'VERSION').exists():
            return potential_root
            
        # Try current working directory
        cwd = Path.cwd()
        if (cwd / 'package.json').exists():
            return cwd
        
        # Fallback to current module's parent
        return potential_root
    
    def _is_wheel_installation(self) -> bool:
        """Check if we're running from a wheel/installed package."""
        # Check if we're in site-packages or dist-packages
        current_path = Path(__file__).resolve()
        path_str = str(current_path)
        return 'site-packages' in path_str or 'dist-packages' in path_str
    
    @lru_cache(maxsize=32)
    def get_package_version(self) -> str:
        """
        Get package version from package metadata, package.json, or VERSION file.
        
        Returns:
            Package version string
        """
        try:
            # First, try to get version from package metadata (wheel installations)
            if self._is_wheel_installation():
                try:
                    version = metadata.version('claude-multiagent-pm')
                    self._version_cache['package'] = version
                    logger.debug(f"Loaded package version from metadata: {version}")
                    return version
                except metadata.PackageNotFoundError:
                    logger.debug("Package metadata not found, trying fallback methods")
            
            # Try package.json first (source installations)
            package_json_path = self.framework_root / 'package.json'
            if package_json_path.exists():
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    if 'version' in package_data:
                        version = package_data['version']
                        self._version_cache['package'] = version
                        logger.debug(f"Loaded package version from package.json: {version}")
                        return version
            
            # Fallback to VERSION file
            version_file = self.framework_root / 'VERSION'
            if version_file.exists():
                version = version_file.read_text().strip()
                self._version_cache['package'] = version
                logger.debug(f"Loaded package version from VERSION file: {version}")
                return version
            
            # Last resort - try to find in parent directories
            current_path = self.framework_root
            for _ in range(3):  # Search up to 3 levels
                parent_package_json = current_path / 'package.json'
                if parent_package_json.exists():
                    with open(parent_package_json, 'r') as f:
                        package_data = json.load(f)
                        if 'version' in package_data:
                            version = package_data['version']
                            self._version_cache['package'] = version
                            logger.debug(f"Loaded package version from parent package.json: {version}")
                            return version
                current_path = current_path.parent
            
            # Default fallback
            logger.warning("Could not find package version, using default")
            return "0.0.0"
            
        except Exception as e:
            logger.error(f"Error loading package version: {e}")
            return "0.0.0"
    
    @lru_cache(maxsize=32)
    def get_framework_version(self) -> str:
        """
        Get framework version from framework/VERSION file.
        
        Returns:
            Framework version string (serial number format)
        """
        try:
            # Try framework/VERSION
            framework_version_file = self.framework_root / 'framework' / 'VERSION'
            if framework_version_file.exists():
                version = framework_version_file.read_text().strip()
                self._version_cache['framework'] = version
                logger.debug(f"Loaded framework version from framework/VERSION: {version}")
                return version
            
            # Default fallback
            logger.warning("Could not find framework version, using default")
            return "001"
            
        except Exception as e:
            logger.error(f"Error loading framework version: {e}")
            return "001"
    
    @lru_cache(maxsize=128)
    def get_service_version(self, service_name: str) -> str:
        """
        Get service version from service-specific VERSION file.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service version string
        """
        try:
            # Service version file mapping
            service_version_files = {
                "health": "HEALTH_VERSION",
                # Service-specific files
                # "memory_service": "claude_pm/services/memory/VERSION",  # REMOVED - service deprecated
                "agents_service": "claude_pm/agents/VERSION",
                "cli_service": "claude_pm/cli/VERSION",
                "services_core": "claude_pm/services/VERSION",
                "version_control_service": "claude_pm/services/version_control/VERSION",
                "framework_core": "framework/VERSION",
                "script_system": "bin/VERSION",
                "deployment_scripts": "scripts/VERSION"
            }
            
            if service_name in service_version_files:
                version_file_path = self.framework_root / service_version_files[service_name]
                if version_file_path.exists():
                    version = version_file_path.read_text().strip()
                    cache_key = f"service_{service_name}"
                    self._version_cache[cache_key] = version
                    logger.debug(f"Loaded {service_name} version: {version}")
                    return version
            
            # Default fallback
            logger.warning(f"Could not find version for service {service_name}, using default")
            return "001"
            
        except Exception as e:
            logger.error(f"Error loading service version for {service_name}: {e}")
            return "001"
    
    def get_all_versions(self) -> Dict[str, str]:
        """
        Get all available version information.
        
        Returns:
            Dictionary with all version information
        """
        versions = {
            "package": self.get_package_version(),
            "framework": self.get_framework_version(),
        }
        
        # Add service versions
        service_names = [
            "memory", "agents", "documentation", "services", 
            "cli", "integration", "health", "agents_service", 
            "cli_service", "services_core", "version_control_service", 
            "framework_core", "script_system", "deployment_scripts"
        ]
        
        for service_name in service_names:
            versions[service_name] = self.get_service_version(service_name)
        
        return versions
    
    def clear_cache(self):
        """Clear version cache."""
        self._version_cache.clear()
        # Clear lru_cache
        self.get_package_version.cache_clear()
        self.get_framework_version.cache_clear()
        self.get_service_version.cache_clear()
    
    def reload_versions(self):
        """Reload all version information."""
        self.clear_cache()
        # Trigger reloading by calling the methods
        self.get_package_version()
        self.get_framework_version()
    
    def update_config_files(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Update configuration files with current version information.
        
        Args:
            dry_run: If True, only report what would be changed without making changes
            
        Returns:
            Dictionary with update results
        """
        results = {
            "updated_files": [],
            "errors": [],
            "changes": []
        }
        
        try:
            current_package_version = self.get_package_version()
            current_framework_version = self.get_framework_version()
            
            # Update main config.json
            config_path = Path.home() / ".claude-pm" / "config.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    
                    changes_made = False
                    
                    # Update version fields
                    if config_data.get("version") != current_package_version:
                        results["changes"].append(f"config.json: version {config_data.get('version')} -> {current_package_version}")
                        if not dry_run:
                            config_data["version"] = current_package_version
                        changes_made = True
                    
                    if config_data.get("publication", {}).get("npmVersion") != current_package_version:
                        results["changes"].append(f"config.json: publication.npmVersion -> {current_package_version}")
                        if not dry_run:
                            config_data.setdefault("publication", {})["npmVersion"] = current_package_version
                        changes_made = True
                    
                    if changes_made and not dry_run:
                        with open(config_path, 'w') as f:
                            json.dump(config_data, f, indent=2)
                        results["updated_files"].append(str(config_path))
                        
                except Exception as e:
                    results["errors"].append(f"Error updating config.json: {e}")
            
            # Update framework.yaml
            framework_config_path = Path.home() / ".claude-pm" / "config" / "framework.yaml"
            if framework_config_path.exists():
                try:
                    import yaml
                    
                    with open(framework_config_path, 'r') as f:
                        framework_data = yaml.safe_load(f)
                    
                    changes_made = False
                    
                    # Update version in claude-pm section
                    if framework_data.get("claude-pm", {}).get("version") != current_package_version:
                        results["changes"].append(f"framework.yaml: claude-pm.version -> {current_package_version}")
                        if not dry_run:
                            framework_data.setdefault("claude-pm", {})["version"] = current_package_version
                        changes_made = True
                    
                    if changes_made and not dry_run:
                        with open(framework_config_path, 'w') as f:
                            yaml.safe_dump(framework_data, f, default_flow_style=False)
                        results["updated_files"].append(str(framework_config_path))
                        
                except ImportError:
                    results["errors"].append("PyYAML not available for updating framework.yaml")
                except Exception as e:
                    results["errors"].append(f"Error updating framework.yaml: {e}")
            
            logger.info(f"Version config update completed: {len(results['updated_files'])} files updated")
            return results
            
        except Exception as e:
            logger.error(f"Error updating config files: {e}")
            results["errors"].append(f"General error: {e}")
            return results


# Global instance for convenient access
_version_loader = None


def get_version_loader() -> VersionLoader:
    """Get global version loader instance."""
    global _version_loader
    if _version_loader is None:
        _version_loader = VersionLoader()
    return _version_loader


def get_package_version() -> str:
    """Get package version (convenience function)."""
    return get_version_loader().get_package_version()


def get_framework_version() -> str:
    """Get framework version (convenience function)."""
    return get_version_loader().get_framework_version()


def get_service_version(service_name: str) -> str:
    """Get service version (convenience function)."""
    return get_version_loader().get_service_version(service_name)


def get_all_versions() -> Dict[str, str]:
    """Get all versions (convenience function)."""
    return get_version_loader().get_all_versions()


def clear_version_cache():
    """Clear version cache (convenience function)."""
    get_version_loader().clear_cache()


def reload_versions():
    """Reload all versions (convenience function)."""
    get_version_loader().reload_versions()


def update_config_files(dry_run: bool = False) -> Dict[str, Any]:
    """Update configuration files with current versions (convenience function)."""
    return get_version_loader().update_config_files(dry_run)


# Compatibility with existing code
def get_current_version() -> str:
    """Get current package version (compatibility function)."""
    return get_package_version()


if __name__ == "__main__":
    # Example usage
    print("Claude PM Framework Version Loader")
    print("=" * 40)
    
    loader = VersionLoader()
    
    print(f"Package Version: {loader.get_package_version()}")
    print(f"Framework Version: {loader.get_framework_version()}")
    print(f"Memory Service Version: {loader.get_service_version('memory')}")
    
    print("\nAll Versions:")
    versions = loader.get_all_versions()
    for name, version in versions.items():
        print(f"  {name}: {version}")