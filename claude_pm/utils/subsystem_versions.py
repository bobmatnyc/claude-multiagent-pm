#!/usr/bin/env python3
"""
Subsystem Version Management Utilities for Claude PM Framework.

This module provides utilities for managing and tracking subsystem versions
across the framework, enabling better change tracking and compatibility
validation.

Features:
- Subsystem version detection and validation
- Version comparison and compatibility checking  
- Bulk version updates and management
- Integration with framework deployment
- CLI utilities for version management
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..core.logging_config import setup_logging

logger = setup_logging(__name__)


class VersionStatus(Enum):
    """Status of subsystem version checking."""
    FOUND = "found"
    MISSING = "missing"
    ERROR = "error"
    OUTDATED = "outdated"
    COMPATIBLE = "compatible"
    EXACT_MATCH = "exact_match"


@dataclass
class SubsystemVersionInfo:
    """Information about a subsystem version."""
    
    name: str
    version: str
    status: VersionStatus
    file_path: str
    last_checked: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


@dataclass
class VersionCompatibilityCheck:
    """Result of version compatibility checking."""
    
    subsystem: str
    required_version: str
    current_version: Optional[str]
    compatible: bool
    status: VersionStatus
    message: Optional[str] = None


class SubsystemVersionManager:
    """Utility class for managing subsystem versions."""

    # Standard subsystem version files
    SUBSYSTEM_FILES = {
        "health": "HEALTH_VERSION"
    }
    
    # Service-specific version files (relative to framework path)
    SERVICE_VERSION_FILES = {
        # "memory_service": "claude_pm/services/memory/VERSION",  # REMOVED - service deprecated
        "agents_service": "claude_pm/agents/VERSION",
        "cli_service": "claude_pm/cli/VERSION",
        "services_core": "claude_pm/services/VERSION",
        "version_control_service": "claude_pm/services/version_control/VERSION",
        "framework_core": "framework/VERSION",
        "script_system": "bin/VERSION",
        "deployment_scripts": "scripts/VERSION"
    }

    def __init__(self, framework_path: Optional[Path] = None):
        """
        Initialize subsystem version manager.
        
        Args:
            framework_path: Path to framework root (auto-detected if None)
        """
        self.framework_path = framework_path or self._detect_framework_path()
        self.subsystem_info: Dict[str, SubsystemVersionInfo] = {}
        
        # Centralized backup directory for version file backups
        self.backup_dir = self.framework_path / ".claude-pm" / "backups" / "versions"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def _detect_framework_path(self) -> Path:
        """Detect framework path from environment or current location."""
        import os
        
        # Try environment variable first
        if framework_path := os.getenv('CLAUDE_PM_FRAMEWORK_PATH'):
            return Path(framework_path)
            
        # Try deployment directory
        if deployment_dir := os.getenv('CLAUDE_PM_DEPLOYMENT_DIR'):
            return Path(deployment_dir)
            
        # Try relative to current module
        current_dir = Path(__file__).parent.parent.parent
        if (current_dir / 'FRAMEWORK_VERSION').exists():
            return current_dir
            
        # Fallback to current working directory
        return Path.cwd()

    async def scan_subsystem_versions(self) -> Dict[str, SubsystemVersionInfo]:
        """
        Scan and load all subsystem versions.
        
        Returns:
            Dictionary of subsystem name to version information
        """
        try:
            self.subsystem_info.clear()
            
            # Scan standard subsystem versions
            for subsystem, filename in self.SUBSYSTEM_FILES.items():
                version_file = self.framework_path / filename
                
                try:
                    if version_file.exists():
                        version = version_file.read_text().strip()
                        info = SubsystemVersionInfo(
                            name=subsystem,
                            version=version,
                            status=VersionStatus.FOUND,
                            file_path=str(version_file)
                        )
                    else:
                        info = SubsystemVersionInfo(
                            name=subsystem,
                            version="not_found",
                            status=VersionStatus.MISSING,
                            file_path=str(version_file)
                        )
                    
                    self.subsystem_info[subsystem] = info
                    logger.debug(f"Scanned {subsystem}: {info.version}")
                    
                except Exception as e:
                    error_info = SubsystemVersionInfo(
                        name=subsystem,
                        version="error",
                        status=VersionStatus.ERROR,
                        file_path=str(version_file),
                        error=str(e)
                    )
                    self.subsystem_info[subsystem] = error_info
                    logger.error(f"Error reading {subsystem} version: {e}")
            
            # Scan service-specific versions
            for service, filename in self.SERVICE_VERSION_FILES.items():
                version_file = self.framework_path / filename
                
                try:
                    if version_file.exists():
                        version = version_file.read_text().strip()
                        info = SubsystemVersionInfo(
                            name=service,
                            version=version,
                            status=VersionStatus.FOUND,
                            file_path=str(version_file)
                        )
                    else:
                        info = SubsystemVersionInfo(
                            name=service,
                            version="not_found",
                            status=VersionStatus.MISSING,
                            file_path=str(version_file)
                        )
                    
                    self.subsystem_info[service] = info
                    logger.debug(f"Scanned service {service}: {info.version}")
                    
                except Exception as e:
                    error_info = SubsystemVersionInfo(
                        name=service,
                        version="error",
                        status=VersionStatus.ERROR,
                        file_path=str(version_file),
                        error=str(e)
                    )
                    self.subsystem_info[service] = error_info
                    logger.error(f"Error reading service {service} version: {e}")
            
            logger.info(f"Scanned {len(self.subsystem_info)} subsystem and service versions")
            return self.subsystem_info
            
        except Exception as e:
            logger.error(f"Failed to scan subsystem versions: {e}")
            return {}

    def get_version(self, subsystem: str) -> Optional[str]:
        """
        Get version for a specific subsystem or service.
        
        Args:
            subsystem: Name of the subsystem or service
            
        Returns:
            Version string or None if not found
        """
        info = self.subsystem_info.get(subsystem)
        return info.version if info and info.status == VersionStatus.FOUND else None
    
    def get_all_available_subsystems(self) -> List[str]:
        """
        Get list of all available subsystems and services.
        
        Returns:
            List of subsystem and service names
        """
        return list(self.SUBSYSTEM_FILES.keys()) + list(self.SERVICE_VERSION_FILES.keys())

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        Supports both serial numbers (001, 002) and semantic versioning (x.y.z).
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        try:
            # Handle serial number format (001, 002, etc.)
            if version1.isdigit() and version2.isdigit():
                v1_num = int(version1)
                v2_num = int(version2)
                return (v1_num > v2_num) - (v1_num < v2_num)
            
            # Handle semantic versioning (x.y.z)
            if "." in version1 and "." in version2:
                v1_parts = [int(x) for x in version1.split(".")]
                v2_parts = [int(x) for x in version2.split(".")]
                
                # Pad shorter version with zeros
                max_len = max(len(v1_parts), len(v2_parts))
                v1_parts.extend([0] * (max_len - len(v1_parts)))
                v2_parts.extend([0] * (max_len - len(v2_parts)))
                
                for i in range(max_len):
                    if v1_parts[i] < v2_parts[i]:
                        return -1
                    elif v1_parts[i] > v2_parts[i]:
                        return 1
                
                return 0
            
            # String comparison fallback
            return (version1 > version2) - (version1 < version2)

        except Exception as e:
            logger.error(f"Failed to compare versions {version1} vs {version2}: {e}")
            return -1 if version1 != version2 else 0

    async def validate_compatibility(self, requirements: Dict[str, str]) -> List[VersionCompatibilityCheck]:
        """
        Validate subsystem version compatibility against requirements.
        
        Args:
            requirements: Dictionary of subsystem -> required version
            
        Returns:
            List of compatibility check results
        """
        try:
            # Ensure we have current version information
            if not self.subsystem_info:
                await self.scan_subsystem_versions()
            
            results = []
            
            for subsystem, required_version in requirements.items():
                current_info = self.subsystem_info.get(subsystem)
                current_version = current_info.version if current_info else None
                
                # Determine compatibility
                if not current_info or current_info.status != VersionStatus.FOUND:
                    check = VersionCompatibilityCheck(
                        subsystem=subsystem,
                        required_version=required_version,
                        current_version=current_version,
                        compatible=False,
                        status=VersionStatus.MISSING,
                        message="Subsystem version file not found"
                    )
                elif current_version == required_version:
                    check = VersionCompatibilityCheck(
                        subsystem=subsystem,
                        required_version=required_version,
                        current_version=current_version,
                        compatible=True,
                        status=VersionStatus.EXACT_MATCH,
                        message="Version matches exactly"
                    )
                else:
                    # Compare versions
                    comparison = self.compare_versions(current_version, required_version)
                    if comparison >= 0:
                        status = VersionStatus.COMPATIBLE if comparison > 0 else VersionStatus.EXACT_MATCH
                        check = VersionCompatibilityCheck(
                            subsystem=subsystem,
                            required_version=required_version,
                            current_version=current_version,
                            compatible=True,
                            status=status,
                            message="Version is compatible"
                        )
                    else:
                        check = VersionCompatibilityCheck(
                            subsystem=subsystem,
                            required_version=required_version,
                            current_version=current_version,
                            compatible=False,
                            status=VersionStatus.OUTDATED,
                            message=f"Version {current_version} is older than required {required_version}"
                        )
                
                results.append(check)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to validate compatibility: {e}")
            return []

    async def update_version(self, subsystem: str, new_version: str, backup: bool = True) -> bool:
        """
        Update version for a specific subsystem or service.
        
        Args:
            subsystem: Name of the subsystem or service
            new_version: New version string
            backup: Create backup before updating
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if it's a standard subsystem or service-specific version
            if subsystem in self.SUBSYSTEM_FILES:
                filename = self.SUBSYSTEM_FILES[subsystem]
                version_file = self.framework_path / filename
            elif subsystem in self.SERVICE_VERSION_FILES:
                filename = self.SERVICE_VERSION_FILES[subsystem]
                version_file = self.framework_path / filename
            else:
                logger.error(f"Unknown subsystem or service: {subsystem}")
                return False
            
            # Ensure parent directory exists
            version_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if requested and file exists
            if backup and version_file.exists():
                backup_path = self._create_backup(version_file)
                if backup_path:
                    logger.info(f"Created backup: {backup_path}")
            
            # Write new version
            version_file.write_text(new_version.strip())
            
            # Update internal tracking
            info = SubsystemVersionInfo(
                name=subsystem,
                version=new_version,
                status=VersionStatus.FOUND,
                file_path=str(version_file)
            )
            self.subsystem_info[subsystem] = info
            
            logger.info(f"Updated {subsystem} version to: {new_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update {subsystem} version: {e}")
            return False

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of a version file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path.name}_backup_{timestamp}"
            backup_path = self.backup_dir / backup_filename
            
            import shutil
            shutil.copy2(file_path, backup_path)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None

    async def bulk_update(self, updates: Dict[str, str], backup: bool = True) -> Dict[str, bool]:
        """
        Update multiple subsystem versions in bulk.
        
        Args:
            updates: Dictionary of subsystem -> new version
            backup: Create backups before updating
            
        Returns:
            Dictionary of subsystem -> success status
        """
        results = {}
        
        for subsystem, new_version in updates.items():
            success = await self.update_version(subsystem, new_version, backup)
            results[subsystem] = success
        
        return results

    def get_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of all subsystem versions.
        
        Returns:
            Dictionary with summary information
        """
        try:
            total = len(self.subsystem_info)
            found = sum(1 for info in self.subsystem_info.values() if info.status == VersionStatus.FOUND)
            missing = sum(1 for info in self.subsystem_info.values() if info.status == VersionStatus.MISSING)
            errors = sum(1 for info in self.subsystem_info.values() if info.status == VersionStatus.ERROR)
            
            return {
                "framework_path": str(self.framework_path),
                "scan_timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_subsystems": total,
                    "found": found,
                    "missing": missing,
                    "errors": errors,
                    "coverage_percentage": (found / total * 100) if total > 0 else 0
                },
                "subsystems": {
                    name: {
                        "version": info.version,
                        "status": info.status.value,
                        "file_path": info.file_path,
                        "last_checked": info.last_checked,
                        "error": info.error
                    }
                    for name, info in self.subsystem_info.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            return {
                "error": str(e),
                "scan_timestamp": datetime.now().isoformat()
            }

    def export_versions(self, format_type: str = "json") -> str:
        """
        Export version information in specified format.
        
        Args:
            format_type: Export format ('json' or 'yaml')
            
        Returns:
            Formatted version information string
        """
        try:
            report = self.get_summary_report()
            
            if format_type == "json":
                return json.dumps(report, indent=2)
            elif format_type == "yaml":
                try:
                    import yaml
                    return yaml.dump(report, default_flow_style=False)
                except ImportError:
                    logger.error("PyYAML not installed for YAML export")
                    return json.dumps(report, indent=2)
            else:
                logger.error(f"Unsupported export format: {format_type}")
                return json.dumps(report, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to export versions: {e}")
            return json.dumps({"error": str(e)}, indent=2)


# Standalone utility functions

async def scan_framework_versions(framework_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Quick scan of framework subsystem versions.
    
    Args:
        framework_path: Path to framework root
        
    Returns:
        Dictionary of subsystem -> version
    """
    manager = SubsystemVersionManager(framework_path)
    await manager.scan_subsystem_versions()
    
    return {
        name: info.version 
        for name, info in manager.subsystem_info.items()
        if info.status == VersionStatus.FOUND
    }


async def validate_framework_compatibility(
    requirements: Dict[str, str], 
    framework_path: Optional[Path] = None
) -> Tuple[bool, List[VersionCompatibilityCheck]]:
    """
    Validate framework compatibility against requirements.
    
    Args:
        requirements: Dictionary of subsystem -> required version
        framework_path: Path to framework root
        
    Returns:
        Tuple of (is_compatible, check_results)
    """
    manager = SubsystemVersionManager(framework_path)
    checks = await manager.validate_compatibility(requirements)
    
    is_compatible = all(check.compatible for check in checks)
    return is_compatible, checks


def increment_version(current_version: str, increment_type: str = "patch") -> str:
    """
    Increment a version string.
    
    Args:
        current_version: Current version string
        increment_type: Type of increment ('major', 'minor', 'patch', or 'serial')
        
    Returns:
        Incremented version string
    """
    try:
        # Handle serial numbers (001, 002, etc.)
        if current_version.isdigit():
            current_num = int(current_version)
            new_num = current_num + 1
            # Preserve zero-padding
            padding = len(current_version)
            return f"{new_num:0{padding}d}"
        
        # Handle semantic versioning
        if "." in current_version:
            parts = [int(x) for x in current_version.split(".")]
            
            if increment_type == "major":
                parts[0] += 1
                if len(parts) > 1:
                    parts[1] = 0
                if len(parts) > 2:
                    parts[2] = 0
            elif increment_type == "minor" and len(parts) > 1:
                parts[1] += 1
                if len(parts) > 2:
                    parts[2] = 0
            elif increment_type == "patch" and len(parts) > 2:
                parts[2] += 1
            else:
                # Default to incrementing last part
                parts[-1] += 1
            
            return ".".join(str(p) for p in parts)
        
        # Fallback for unknown format
        return current_version + ".1"
        
    except Exception as e:
        logger.error(f"Failed to increment version {current_version}: {e}")
        return current_version


# CLI integration helpers

def create_version_manager_from_env() -> SubsystemVersionManager:
    """Create version manager using environment configuration."""
    return SubsystemVersionManager()


async def cli_scan_versions() -> Dict[str, Any]:
    """CLI helper to scan and return version information."""
    manager = create_version_manager_from_env()
    await manager.scan_subsystem_versions()
    return manager.get_summary_report()


async def cli_update_version(subsystem: str, version: str, backup: bool = True) -> bool:
    """CLI helper to update a subsystem version."""
    manager = create_version_manager_from_env()
    return await manager.update_version(subsystem, version, backup)


async def cli_validate_versions(requirements: Dict[str, str]) -> Dict[str, Any]:
    """CLI helper to validate version compatibility."""
    manager = create_version_manager_from_env()
    checks = await manager.validate_compatibility(requirements)
    
    return {
        "compatible": all(check.compatible for check in checks),
        "validation_timestamp": datetime.now().isoformat(),
        "checks": [
            {
                "subsystem": check.subsystem,
                "required_version": check.required_version,
                "current_version": check.current_version,
                "compatible": check.compatible,
                "status": check.status.value,
                "message": check.message
            }
            for check in checks
        ]
    }


if __name__ == "__main__":
    async def main():
        """Example usage of subsystem version utilities."""
        print("🔢 Subsystem Version Manager Example")
        
        # Create manager
        manager = SubsystemVersionManager()
        
        # Scan versions
        print("📡 Scanning subsystem versions...")
        await manager.scan_subsystem_versions()
        
        # Show summary
        report = manager.get_summary_report()
        print(f"✅ Found {report['summary']['found']}/{report['summary']['total_subsystems']} subsystem versions")
        
        # Example validation using dynamic version loading
        try:
            from .version_loader import get_service_version, get_framework_version
            requirements = {
                "memory": get_service_version("memory"), 
                "framework": get_framework_version()
            }
        except ImportError:
            # Fallback to hardcoded values
            requirements = {"memory": "002", "framework": "010"}
        print(f"🔍 Validating against requirements: {requirements}")
        checks = await manager.validate_compatibility(requirements)
        
        for check in checks:
            status = "✅" if check.compatible else "❌"
            print(f"{status} {check.subsystem}: {check.current_version} vs {check.required_version}")
    
    asyncio.run(main())