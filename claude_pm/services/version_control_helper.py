#!/usr/bin/env python3
"""
Version Control Helper Service - Extract from Parent Directory Manager
=====================================================================

Handles version control integration for the Claude PM Framework.
This module is extracted from parent_directory_manager.py as part of
the refactoring effort (ISS-0154).

Key Features:
- Version comparison and parsing
- Subsystem version tracking
- Version compatibility validation
- Version report generation

Created: 2025-07-18
Author: Engineer Agent
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from packaging import version


@dataclass
class VersionInfo:
    """Version information for a component."""
    component: str
    version: str
    last_updated: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VersionCompatibility:
    """Version compatibility check result."""
    compatible: bool
    component: str
    required_version: str
    current_version: Optional[str]
    message: str


class VersionControlHelper:
    """
    Manages version control operations for the Claude PM Framework.
    
    This class provides:
    - Version tracking for framework and subsystems
    - Version comparison and validation
    - Compatibility checking
    - Version history and reporting
    """
    
    def __init__(self, working_dir: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize the Version Control Helper.
        
        Args:
            working_dir: Working directory for version tracking
            logger: Optional logger instance
        """
        self.working_dir = Path(working_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # Version storage
        self.versions_file = self.working_dir / ".claude-pm" / "versions.json"
        self.subsystem_versions: Dict[str, VersionInfo] = {}
        
        # Load existing versions
        self._load_versions()
        
    def _load_versions(self) -> None:
        """Load version information from storage."""
        if self.versions_file.exists():
            try:
                with open(self.versions_file, 'r') as f:
                    data = json.load(f)
                    
                for component, info in data.items():
                    self.subsystem_versions[component] = VersionInfo(
                        component=component,
                        version=info["version"],
                        last_updated=datetime.fromisoformat(info["last_updated"]),
                        metadata=info.get("metadata", {})
                    )
                    
            except Exception as e:
                self.logger.warning(f"Failed to load versions: {e}")
                
    def _save_versions(self) -> None:
        """Save version information to storage."""
        try:
            # Create directory if needed
            self.versions_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data
            data = {}
            for component, info in self.subsystem_versions.items():
                data[component] = {
                    "version": info.version,
                    "last_updated": info.last_updated.isoformat(),
                    "metadata": info.metadata
                }
                
            # Save to file
            with open(self.versions_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save versions: {e}")
            
    def get_subsystem_version(self, subsystem: str) -> Optional[str]:
        """
        Get version for a specific subsystem.
        
        Args:
            subsystem: Subsystem name
            
        Returns:
            Version string or None
        """
        info = self.subsystem_versions.get(subsystem)
        return info.version if info else None
        
    def set_subsystem_version(
        self,
        subsystem: str,
        new_version: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set version for a subsystem.
        
        Args:
            subsystem: Subsystem name
            new_version: New version string
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            self.subsystem_versions[subsystem] = VersionInfo(
                component=subsystem,
                version=new_version,
                last_updated=datetime.now(),
                metadata=metadata or {}
            )
            self._save_versions()
            self.logger.info(f"Updated {subsystem} version to {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set version: {e}")
            return False
            
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        try:
            # Try semantic versioning comparison
            v1 = version.parse(version1)
            v2 = version.parse(version2)
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
                
        except Exception:
            # Fallback to custom comparison for non-standard versions
            return self._compare_custom_versions(version1, version2)
            
    def _compare_custom_versions(self, version1: str, version2: str) -> int:
        """
        Compare custom version formats (e.g., "1.2.3-001").
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            Comparison result
        """
        def parse_custom_version(v: str) -> Tuple[Tuple[int, ...], int]:
            """Parse custom version string."""
            if '-' in v:
                base, serial = v.rsplit('-', 1)
                base_parts = tuple(map(int, base.split('.')))
                serial_num = int(serial)
                return base_parts, serial_num
            else:
                base_parts = tuple(map(int, v.split('.')))
                return base_parts, 0
                
        try:
            v1_parsed = parse_custom_version(version1)
            v2_parsed = parse_custom_version(version2)
            
            if v1_parsed < v2_parsed:
                return -1
            elif v1_parsed > v2_parsed:
                return 1
            else:
                return 0
                
        except Exception:
            # Final fallback to string comparison
            return -1 if version1 < version2 else (0 if version1 == version2 else 1)
            
    def validate_compatibility(
        self,
        required_versions: Dict[str, str]
    ) -> List[VersionCompatibility]:
        """
        Validate version compatibility for multiple components.
        
        Args:
            required_versions: Dictionary of component -> required version
            
        Returns:
            List of compatibility check results
        """
        results = []
        
        for component, required_version in required_versions.items():
            current_version = self.get_subsystem_version(component)
            
            if current_version is None:
                results.append(VersionCompatibility(
                    compatible=False,
                    component=component,
                    required_version=required_version,
                    current_version=None,
                    message=f"{component} not installed"
                ))
                continue
                
            # Compare versions
            comparison = self.compare_versions(current_version, required_version)
            
            if comparison < 0:
                results.append(VersionCompatibility(
                    compatible=False,
                    component=component,
                    required_version=required_version,
                    current_version=current_version,
                    message=f"{component} version too old: {current_version} < {required_version}"
                ))
            else:
                results.append(VersionCompatibility(
                    compatible=True,
                    component=component,
                    required_version=required_version,
                    current_version=current_version,
                    message=f"{component} version compatible"
                ))
                
        return results
        
    def get_version_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive version report.
        
        Returns:
            Version report dictionary
        """
        # Get framework version
        try:
            from claude_pm import __version__ as framework_version
        except ImportError:
            framework_version = "unknown"
            
        report = {
            "framework_version": framework_version,
            "report_generated": datetime.now().isoformat(),
            "subsystems": {},
            "summary": {
                "total_components": len(self.subsystem_versions),
                "last_update": None
            }
        }
        
        # Add subsystem information
        latest_update = None
        for component, info in self.subsystem_versions.items():
            report["subsystems"][component] = {
                "version": info.version,
                "last_updated": info.last_updated.isoformat(),
                "metadata": info.metadata
            }
            
            if latest_update is None or info.last_updated > latest_update:
                latest_update = info.last_updated
                
        if latest_update:
            report["summary"]["last_update"] = latest_update.isoformat()
            
        return report
        
    def check_version_updates(self) -> List[Dict[str, Any]]:
        """
        Check for available version updates.
        
        Returns:
            List of components with available updates
        """
        updates = []
        
        # This is a placeholder for actual update checking logic
        # In a real implementation, this would check against a registry
        # or remote repository for available updates
        
        for component, info in self.subsystem_versions.items():
            # For now, just flag components older than 30 days
            age_days = (datetime.now() - info.last_updated).days
            if age_days > 30:
                updates.append({
                    "component": component,
                    "current_version": info.version,
                    "age_days": age_days,
                    "recommendation": "Consider checking for updates"
                })
                
        return updates
        
    def export_version_manifest(self, output_path: Optional[Path] = None) -> Path:
        """
        Export version manifest to file.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to exported manifest
        """
        if output_path is None:
            output_path = self.working_dir / "version_manifest.json"
            
        manifest = {
            "generated": datetime.now().isoformat(),
            "framework": {
                "name": "claude-multiagent-pm",
                "version": self._get_framework_version()
            },
            "components": {}
        }
        
        # Add all tracked versions
        for component, info in self.subsystem_versions.items():
            manifest["components"][component] = {
                "version": info.version,
                "last_updated": info.last_updated.isoformat(),
                "metadata": info.metadata
            }
            
        # Write manifest
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        self.logger.info(f"Exported version manifest to: {output_path}")
        return output_path
        
    def _get_framework_version(self) -> str:
        """Get framework version safely."""
        try:
            from claude_pm import __version__
            return __version__
        except ImportError:
            return "unknown"
            
    def import_version_manifest(self, manifest_path: Path) -> bool:
        """
        Import version manifest from file.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            True if successful
        """
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            # Import component versions
            for component, data in manifest.get("components", {}).items():
                self.set_subsystem_version(
                    component,
                    data["version"],
                    data.get("metadata", {})
                )
                
            self.logger.info(f"Imported version manifest from: {manifest_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import manifest: {e}")
            return False