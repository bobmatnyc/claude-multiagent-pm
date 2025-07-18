#!/usr/bin/env python3
"""
Agent Versioning Service
========================

Handles version management for agent definitions.
Supports semantic versioning with automatic serial increments.
"""

import re
from typing import Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentVersionManager:
    """Manages agent versioning with semantic version support."""
    
    VERSION_PATTERN = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
    
    @staticmethod
    def parse_version(version: str) -> Tuple[int, int, int]:
        """
        Parse semantic version string.
        
        Args:
            version: Version string (e.g., "2.0.1")
            
        Returns:
            Tuple of (major, minor, serial)
            
        Raises:
            ValueError: If version format is invalid
        """
        match = AgentVersionManager.VERSION_PATTERN.match(version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")
        
        major, minor, serial = match.groups()
        return int(major), int(minor), int(serial)
    
    @staticmethod
    def increment_serial(version: str) -> str:
        """
        Increment the serial (patch) version.
        
        Args:
            version: Current version string
            
        Returns:
            New version with incremented serial
        """
        try:
            major, minor, serial = AgentVersionManager.parse_version(version)
            return f"{major}.{minor}.{serial + 1}"
        except ValueError:
            logger.warning(f"Invalid version format: {version}, defaulting to 1.0.1")
            return "1.0.1"
    
    @staticmethod
    def increment_minor(version: str) -> str:
        """
        Increment the minor version (resets serial to 0).
        
        Args:
            version: Current version string
            
        Returns:
            New version with incremented minor
        """
        try:
            major, minor, _ = AgentVersionManager.parse_version(version)
            return f"{major}.{minor + 1}.0"
        except ValueError:
            logger.warning(f"Invalid version format: {version}, defaulting to 1.1.0")
            return "1.1.0"
    
    @staticmethod
    def increment_major(version: str) -> str:
        """
        Increment the major version (resets minor and serial to 0).
        
        Args:
            version: Current version string
            
        Returns:
            New version with incremented major
        """
        try:
            major, _, _ = AgentVersionManager.parse_version(version)
            return f"{major + 1}.0.0"
        except ValueError:
            logger.warning(f"Invalid version format: {version}, defaulting to 2.0.0")
            return "2.0.0"
    
    @staticmethod
    def compare_versions(v1: str, v2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            v1: First version
            v2: Second version
            
        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        try:
            major1, minor1, serial1 = AgentVersionManager.parse_version(v1)
            major2, minor2, serial2 = AgentVersionManager.parse_version(v2)
            
            if major1 != major2:
                return -1 if major1 < major2 else 1
            if minor1 != minor2:
                return -1 if minor1 < minor2 else 1
            if serial1 != serial2:
                return -1 if serial1 < serial2 else 1
            return 0
        except ValueError as e:
            logger.error(f"Error comparing versions: {e}")
            return 0
    
    @staticmethod
    def format_version_for_markdown(version: str, last_updated: Optional[datetime] = None) -> str:
        """
        Format version information for markdown footer.
        
        Args:
            version: Version string
            last_updated: Optional last update timestamp
            
        Returns:
            Formatted markdown string
        """
        footer = f"**Version**: {version}"
        if last_updated:
            footer += f"\n**Last Updated**: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
        return footer
    
    @staticmethod
    def extract_version_from_markdown(content: str) -> Optional[str]:
        """
        Extract version from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Version string if found, None otherwise
        """
        # Look for version in footer format
        version_match = re.search(r'\*\*Version\*\*:\s*(\d+\.\d+\.\d+)', content, re.IGNORECASE)
        if version_match:
            return version_match.group(1)
        
        # Look for version in metadata format
        version_match = re.search(r'^Version:\s*(\d+\.\d+\.\d+)$', content, re.MULTILINE | re.IGNORECASE)
        if version_match:
            return version_match.group(1)
        
        return None
    
    @staticmethod
    def update_version_in_markdown(content: str, new_version: str) -> str:
        """
        Update version in markdown content.
        
        Args:
            content: Original markdown content
            new_version: New version to set
            
        Returns:
            Updated markdown content
        """
        # Update footer format
        content = re.sub(
            r'(\*\*Version\*\*:\s*)\d+\.\d+\.\d+',
            f'\\g<1>{new_version}',
            content,
            flags=re.IGNORECASE
        )
        
        # Update metadata format
        content = re.sub(
            r'^(Version:\s*)\d+\.\d+\.\d+$',
            f'\\g<1>{new_version}',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )
        
        # Update last updated timestamp if present
        now = datetime.now()
        content = re.sub(
            r'(\*\*Last Updated\*\*:\s*)[^\n]+',
            f'\\g<1>{now.strftime("%Y-%m-%d %H:%M:%S")}',
            content,
            flags=re.IGNORECASE
        )
        
        return content