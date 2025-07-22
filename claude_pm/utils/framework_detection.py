"""
Framework Detection Utilities

This module provides utilities for detecting whether a directory is the framework source
directory or a user project using the framework. This is critical for preventing
accidental modifications to user projects when working on framework development.
"""

from pathlib import Path
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


def is_framework_source_directory(directory: Path) -> Tuple[bool, List[str]]:
    """
    Check if the given directory is the framework source directory.
    
    This function performs multiple checks to determine if we're in the
    claude-multiagent-pm framework source directory rather than a user project
    that's using the framework.
    
    Args:
        directory: The directory path to check
        
    Returns:
        tuple: (is_framework_source, list_of_detected_markers)
            - is_framework_source: True if this is the framework source directory
            - list_of_detected_markers: List of strings describing what markers were found
            
    Example:
        >>> from pathlib import Path
        >>> is_source, markers = is_framework_source_directory(Path.cwd())
        >>> if is_source:
        ...     print(f"Framework source detected: {', '.join(markers)}")
    """
    is_framework_source = False
    framework_markers = []
    
    # Ensure directory is a Path object
    directory = Path(directory)
    
    # Check for pyproject.toml with our package name
    pyproject_path = directory / "pyproject.toml"
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text()
            if 'name = "claude-multiagent-pm"' in content:
                is_framework_source = True
                framework_markers.append("pyproject.toml (claude-multiagent-pm)")
        except Exception as e:
            logger.debug(f"Error reading pyproject.toml: {e}")
    
    # Check for package.json with our package name
    package_json_path = directory / "package.json"
    if package_json_path.exists():
        try:
            content = package_json_path.read_text()
            if '"@bobmatnyc/claude-multiagent-pm"' in content:
                is_framework_source = True
                framework_markers.append("package.json (@bobmatnyc/claude-multiagent-pm)")
        except Exception as e:
            logger.debug(f"Error reading package.json: {e}")
    
    # Check for claude_pm source directory
    if (directory / "claude_pm").is_dir():
        is_framework_source = True
        framework_markers.append("claude_pm/ source directory")
    
    # Check if CLAUDE.md mentions framework developers
    claude_md_path = directory / "CLAUDE.md"
    if claude_md_path.exists():
        try:
            content = claude_md_path.read_text()
            if "FRAMEWORK DEVELOPERS ONLY" in content:
                is_framework_source = True
                framework_markers.append("CLAUDE.md (development version)")
        except Exception as e:
            logger.debug(f"Error reading CLAUDE.md: {e}")
    
    # Additional checks for framework source indicators
    framework_indicators = [
        ("tests/", "tests/ directory"),
        ("scripts/", "scripts/ directory"),
        ("requirements/", "requirements/ directory"),
        ("framework/", "framework/ templates directory"),
        (".github/workflows/", ".github/workflows/ directory")
    ]
    
    for indicator_path, indicator_name in framework_indicators:
        if (directory / indicator_path).exists():
            is_framework_source = True
            framework_markers.append(indicator_name)
    
    return is_framework_source, framework_markers


def ensure_is_framework_source(directory: Path) -> None:
    """
    Ensure that the given directory IS the framework source directory.
    
    This is a safety check to ensure we're operating on the framework source
    when performing framework development operations.
    
    Args:
        directory: The directory to check
        
    Raises:
        ValueError: If the directory is NOT the framework source
        
    Example:
        >>> ensure_is_framework_source(Path.cwd())
        # Raises ValueError if NOT in framework source
    """
    is_source, markers = is_framework_source_directory(directory)
    if not is_source:
        raise ValueError(
            f"This appears to be a user project, not the framework source. "
            f"Framework operations should only be performed in the framework source directory. "
            f"No framework markers found in: {directory}"
        )


def ensure_not_framework_source(directory: Path) -> None:
    """
    Ensure that the given directory is NOT the framework source directory.
    
    This is a safety check to ensure we're operating on a user project
    and not accidentally modifying the framework source.
    
    Args:
        directory: The directory to check
        
    Raises:
        ValueError: If the directory IS the framework source
        
    Example:
        >>> ensure_not_framework_source(Path.cwd())
        # Raises ValueError if in framework source
    """
    is_source, markers = is_framework_source_directory(directory)
    if is_source:
        raise ValueError(
            f"This appears to be the framework source directory, not a user project. "
            f"User project operations should not be performed in the framework source. "
            f"Framework markers found: {', '.join(markers)}"
        )