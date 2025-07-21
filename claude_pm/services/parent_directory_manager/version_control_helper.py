#!/usr/bin/env python3
"""
Version Control Helper Module
=============================

This module provides version control utilities for the Parent Directory Manager.
It handles git operations and version control integration for the framework.

Key Features:
- Git repository detection
- Branch management helpers
- Commit status checking
- Version control integration utilities
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import logging


class VersionControlHelper:
    """
    Helper class for version control operations.
    
    This class provides utilities for interacting with git repositories
    and managing version control operations within the framework.
    """
    
    def __init__(self, working_dir: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize the Version Control Helper.
        
        Args:
            working_dir: The working directory path
            logger: Optional logger instance
        """
        self.working_dir = Path(working_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache git repository detection
        self._is_git_repo: Optional[bool] = None
        self._git_root: Optional[Path] = None
    
    def is_git_repository(self) -> bool:
        """
        Check if the working directory is inside a git repository.
        
        Returns:
            True if inside a git repository, False otherwise
        """
        if self._is_git_repo is not None:
            return self._is_git_repo
        
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            self._is_git_repo = result.returncode == 0
            
            if self._is_git_repo:
                # Get the root of the git repository
                root_result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if root_result.returncode == 0:
                    self._git_root = Path(root_result.stdout.strip())
            
            return self._is_git_repo
        except (subprocess.SubprocessError, FileNotFoundError):
            self._is_git_repo = False
            return False
    
    def get_git_root(self) -> Optional[Path]:
        """
        Get the root directory of the git repository.
        
        Returns:
            Path to git root directory, or None if not in a git repo
        """
        if self.is_git_repository():
            return self._git_root
        return None
    
    def get_current_branch(self) -> Optional[str]:
        """
        Get the current git branch name.
        
        Returns:
            Branch name or None if not in a git repository
        """
        if not self.is_git_repository():
            return None
        
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except subprocess.SubprocessError:
            pass
        
        return None
    
    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes in the repository.
        
        Returns:
            True if there are uncommitted changes, False otherwise
        """
        if not self.is_git_repository():
            return False
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return bool(result.stdout.strip())
        except subprocess.SubprocessError:
            pass
        
        return False
    
    def get_file_status(self, file_path: Path) -> Optional[str]:
        """
        Get the git status of a specific file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            Git status string or None if not tracked
        """
        if not self.is_git_repository():
            return None
        
        try:
            # Make path relative to git root for consistent results
            git_root = self.get_git_root()
            if git_root:
                try:
                    relative_path = file_path.relative_to(git_root)
                except ValueError:
                    # File is outside git repository
                    return None
            else:
                relative_path = file_path
            
            result = subprocess.run(
                ["git", "status", "--porcelain", str(relative_path)],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except subprocess.SubprocessError:
            pass
        
        return None
    
    def is_file_ignored(self, file_path: Path) -> bool:
        """
        Check if a file is ignored by git.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is ignored, False otherwise
        """
        if not self.is_git_repository():
            return False
        
        try:
            result = subprocess.run(
                ["git", "check-ignore", str(file_path)],
                cwd=self.working_dir,
                capture_output=True,
                check=False
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False
    
    def add_to_gitignore(self, pattern: str) -> bool:
        """
        Add a pattern to .gitignore file.
        
        Args:
            pattern: Pattern to add to gitignore
            
        Returns:
            True if successfully added, False otherwise
        """
        if not self.is_git_repository():
            self.logger.debug("Not in a git repository, skipping gitignore update")
            return False
        
        git_root = self.get_git_root()
        if not git_root:
            return False
        
        gitignore_path = git_root / ".gitignore"
        
        try:
            # Read existing content
            existing_patterns = set()
            if gitignore_path.exists():
                existing_patterns = set(gitignore_path.read_text().strip().split('\n'))
            
            # Add pattern if not already present
            if pattern not in existing_patterns:
                with open(gitignore_path, 'a') as f:
                    if gitignore_path.exists() and gitignore_path.stat().st_size > 0:
                        f.write('\n')
                    f.write(f"{pattern}\n")
                
                self.logger.info(f"Added '{pattern}' to .gitignore")
                return True
            else:
                self.logger.debug(f"Pattern '{pattern}' already in .gitignore")
                return True
                
        except Exception as e:
            self.logger.warning(f"Failed to update .gitignore: {e}")
            return False
    
    def get_last_commit_info(self) -> Optional[Dict[str, str]]:
        """
        Get information about the last commit.
        
        Returns:
            Dictionary with commit info or None if not in a git repo
        """
        if not self.is_git_repository():
            return None
        
        try:
            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Get commit message
            msg_result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Get commit author
            author_result = subprocess.run(
                ["git", "log", "-1", "--pretty=%an <%ae>"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Get commit date
            date_result = subprocess.run(
                ["git", "log", "-1", "--pretty=%ai"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            if all(r.returncode == 0 for r in [hash_result, msg_result, author_result, date_result]):
                return {
                    "hash": hash_result.stdout.strip(),
                    "message": msg_result.stdout.strip(),
                    "author": author_result.stdout.strip(),
                    "date": date_result.stdout.strip()
                }
                
        except subprocess.SubprocessError:
            pass
        
        return None
    
    def create_version_tag(self, version: str, message: Optional[str] = None) -> bool:
        """
        Create a git tag for a version.
        
        Args:
            version: Version string (e.g., "v1.0.0")
            message: Optional tag message
            
        Returns:
            True if tag was created successfully
        """
        if not self.is_git_repository():
            return False
        
        try:
            if message:
                cmd = ["git", "tag", "-a", version, "-m", message]
            else:
                cmd = ["git", "tag", version]
            
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.logger.info(f"Created git tag: {version}")
                return True
            else:
                self.logger.warning(f"Failed to create git tag: {result.stderr}")
                return False
                
        except subprocess.SubprocessError as e:
            self.logger.warning(f"Error creating git tag: {e}")
            return False