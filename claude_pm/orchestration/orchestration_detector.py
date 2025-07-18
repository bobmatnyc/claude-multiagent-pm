"""
Orchestration Detector Module

This module provides functionality to detect whether a project has local orchestration enabled
by checking for CLAUDE.md files with the appropriate orchestration flag.

Example usage:
    from claude_pm.orchestration import OrchestrationDetector
    
    # Check if orchestration is enabled in current directory
    detector = OrchestrationDetector()
    if detector.is_orchestration_enabled():
        print("Orchestration is enabled!")
        claude_md_path = detector.get_claude_md_path()
        print(f"CLAUDE.md found at: {claude_md_path}")
    else:
        print("Orchestration is not enabled")
"""

import os
from pathlib import Path
from typing import Optional, Tuple

# Use project standard logging configuration
from claude_pm.core.logging_config import get_logger
logger = get_logger(__name__)


class OrchestrationDetector:
    """
    Detects whether a project has local orchestration enabled.
    
    The detector searches for CLAUDE.md files in the current and parent directories
    (up to 3 levels) and checks for the presence of the orchestration enable flag.
    """
    
    CLAUDE_MD_FILENAME = "CLAUDE.md"
    ORCHESTRATION_DISABLE_FLAG = "CLAUDE_PM_ORCHESTRATION: DISABLED"
    # Legacy flag for backward compatibility
    ORCHESTRATION_ENABLE_FLAG = "CLAUDE_PM_ORCHESTRATION: ENABLED"
    MAX_PARENT_LEVELS = 3
    
    def __init__(self, start_path: Optional[Path] = None):
        """
        Initialize the OrchestrationDetector.
        
        Args:
            start_path: The starting directory for detection. Defaults to current working directory.
        """
        self.start_path = Path(start_path) if start_path else Path.cwd()
        logger.debug(f"Initialized OrchestrationDetector with start_path: {self.start_path}")
    
    def is_orchestration_enabled(self) -> bool:
        """
        Check if orchestration is enabled for the current project.
        
        By default, orchestration is ENABLED unless explicitly disabled.
        
        Returns:
            bool: True if orchestration is enabled (default), False if explicitly disabled.
        """
        # Check for explicit disable first
        disabled, disable_path = self._detect_orchestration_disable()
        if disabled:
            logger.info(f"Orchestration explicitly disabled in: {disable_path}")
            return False
            
        # Check for legacy explicit enable (for backward compatibility)
        enabled, enable_path = self._detect_orchestration_enable()
        if enabled:
            logger.info(f"Orchestration explicitly enabled (legacy) in: {enable_path}")
            return True
            
        # Default behavior: orchestration is ENABLED
        logger.info("Orchestration enabled by default (no disable flag found)")
        return True
    
    def _detect_orchestration_disable(self) -> Tuple[bool, Optional[Path]]:
        """
        Search for CLAUDE.md files and check for orchestration disable flag.
        
        Returns:
            Tuple[bool, Optional[Path]]: (is_disabled, path_to_claude_md)
        """
        return self._detect_flag(self.ORCHESTRATION_DISABLE_FLAG)
    
    def _detect_orchestration_enable(self) -> Tuple[bool, Optional[Path]]:
        """
        Search for CLAUDE.md files and check for orchestration enable flag (legacy).
        
        Returns:
            Tuple[bool, Optional[Path]]: (is_enabled, path_to_claude_md)
        """
        return self._detect_flag(self.ORCHESTRATION_ENABLE_FLAG)
    
    def _detect_orchestration(self) -> Tuple[bool, Optional[Path]]:
        """
        Legacy method for backward compatibility.
        Now delegates to _detect_orchestration_enable().
        """
        return self._detect_orchestration_enable()
    
    def _detect_flag(self, flag: str) -> Tuple[bool, Optional[Path]]:
        """
        Search for CLAUDE.md files and check for a specific flag.
        
        Args:
            flag: The flag to search for in CLAUDE.md files.
            
        Returns:
            Tuple[bool, Optional[Path]]: (flag_found, path_to_claude_md)
        """
        current_path = self.start_path.absolute()
        levels_checked = 0
        
        while levels_checked <= self.MAX_PARENT_LEVELS:
            claude_md_path = current_path / self.CLAUDE_MD_FILENAME
            
            logger.debug(f"Checking for CLAUDE.md at: {claude_md_path}")
            
            if self._check_claude_md_for_flag(claude_md_path, flag):
                return True, claude_md_path
            
            # Don't go beyond root directory
            if current_path.parent == current_path:
                logger.debug("Reached root directory, stopping search")
                break
                
            current_path = current_path.parent
            levels_checked += 1
        
        return False, None
    
    def _check_claude_md_for_flag(self, file_path: Path, flag: str) -> bool:
        """
        Check if a CLAUDE.md file exists and contains a specific flag.
        
        Args:
            file_path: Path to the CLAUDE.md file to check.
            flag: The flag to search for.
            
        Returns:
            bool: True if file exists and contains the flag, False otherwise.
        """
        if not file_path.exists():
            return False
            
        if not file_path.is_file():
            logger.warning(f"CLAUDE.md exists but is not a file: {file_path}")
            return False
        
        try:
            # Read file and check for flag (case-sensitive)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for exact flag match
            if flag in content:
                logger.debug(f"Found flag '{flag}' in: {file_path}")
                return True
                
        except PermissionError:
            logger.error(f"Permission denied reading file: {file_path}")
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {str(e)}")
        
        return False
    
    def _detect_any_claude_md(self) -> Tuple[bool, Optional[Path]]:
        """
        Search for any CLAUDE.md file regardless of flags.
        
        Returns:
            Tuple[bool, Optional[Path]]: (found, path_to_claude_md)
        """
        current_path = self.start_path.absolute()
        levels_checked = 0
        
        while levels_checked <= self.MAX_PARENT_LEVELS:
            claude_md_path = current_path / self.CLAUDE_MD_FILENAME
            
            logger.debug(f"Checking for CLAUDE.md at: {claude_md_path}")
            
            if claude_md_path.exists() and claude_md_path.is_file():
                return True, claude_md_path
            
            # Don't go beyond root directory
            if current_path.parent == current_path:
                logger.debug("Reached root directory, stopping search")
                break
                
            current_path = current_path.parent
            levels_checked += 1
        
        return False, None
    
    def get_claude_md_path(self) -> Optional[Path]:
        """
        Get the path to the CLAUDE.md file with orchestration enabled.
        
        Returns:
            Optional[Path]: Path to CLAUDE.md if orchestration is enabled, None otherwise.
        """
        # Try to find CLAUDE.md with either flag
        disabled, disable_path = self._detect_orchestration_disable()
        if disabled:
            return disable_path
            
        enabled, enable_path = self._detect_orchestration_enable()
        if enabled:
            return enable_path
            
        # Return first CLAUDE.md found even without flags
        _, claude_md_path = self._detect_any_claude_md()
        return claude_md_path