"""
Version management for framework CLAUDE.md templates.

Handles version parsing, incrementing, and comparison operations.
"""

import re
from typing import Tuple, Optional
from pathlib import Path


class VersionManager:
    """Manages version numbering for framework CLAUDE.md templates."""
    
    def __init__(self):
        """Initialize version manager."""
        self.framework_version = self._get_framework_version()
    
    def _get_framework_version(self) -> str:
        """
        Get the current framework version from framework/VERSION file.
        
        Returns:
            str: Framework version (e.g., "015")
        """
        # Check if we're in a wheel installation
        package_path = Path(__file__).parent.parent.parent
        path_str = str(package_path.resolve())
        if 'site-packages' in path_str or 'dist-packages' in path_str:
            # For wheel installations, check data directory
            version_path = package_path / "data" / "framework" / "VERSION"
            if not version_path.exists():
                # Try package root as fallback
                version_path = package_path.parent / "framework" / "VERSION"
        else:
            # Source installation
            version_path = package_path.parent / "framework" / "VERSION"
        
        if version_path.exists():
            with open(version_path, 'r') as f:
                version_content = f.read().strip()
                # Framework VERSION file contains just the framework version number
                try:
                    return f"{int(version_content):03d}"
                except ValueError:
                    # If not a plain number, try to extract from version string
                    match = re.match(r'(\d+)', version_content)
                    if match:
                        return f"{int(match.group(1)):03d}"
        return "014"  # Default fallback
    
    def parse_current_version(self, content: str) -> Tuple[str, int]:
        """
        Parse the current CLAUDE_MD_VERSION from existing content.
        
        Args:
            content: Existing CLAUDE.md content
            
        Returns:
            Tuple of (framework_version, serial_number)
        """
        match = re.search(r'CLAUDE_MD_VERSION:\s*(\d+)-(\d+)', content)
        if match:
            return match.group(1), int(match.group(2))
        return self.framework_version, 1
    
    def auto_increment_version(self, current_content: Optional[str] = None) -> str:
        """
        Auto-increment the CLAUDE_MD_VERSION serial number.
        
        Args:
            current_content: Current CLAUDE.md content to parse version from
            
        Returns:
            str: New version string (e.g., "015-003")
        """
        if current_content:
            framework_ver, serial = self.parse_current_version(current_content)
            if framework_ver == self.framework_version:
                return f"{framework_ver}-{serial + 1:03d}"
        
        return f"{self.framework_version}-001"
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1: First version string (e.g., "015-002")
            version2: Second version string (e.g., "015-003")
            
        Returns:
            int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        def parse_version(v: str) -> Tuple[int, int]:
            match = re.match(r'(\d+)-(\d+)', v)
            if match:
                return int(match.group(1)), int(match.group(2))
            return 0, 0
        
        v1_fw, v1_serial = parse_version(version1)
        v2_fw, v2_serial = parse_version(version2)
        
        if v1_fw < v2_fw:
            return -1
        elif v1_fw > v2_fw:
            return 1
        else:
            if v1_serial < v2_serial:
                return -1
            elif v1_serial > v2_serial:
                return 1
            else:
                return 0