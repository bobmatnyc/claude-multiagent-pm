#!/usr/bin/env python3
"""
Backup Manager Service - Extract from Parent Directory Manager
=============================================================

Handles all backup and restore operations for the Claude PM Framework.
This module is extracted from parent_directory_manager.py as part of
the refactoring effort (ISS-0154).

Key Features:
- File and directory backup operations
- Backup rotation and cleanup
- Restore functionality
- Framework template protection
- Backup status reporting

Created: 2025-07-18
Author: Engineer Agent
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging


@dataclass
class BackupInfo:
    """Information about a backup."""
    
    source_path: Path
    backup_path: Path
    timestamp: datetime
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BackupManager:
    """
    Manages backup and restore operations for the Claude PM Framework.
    
    This class provides:
    - File and directory backup operations
    - Automatic backup rotation and cleanup
    - Restore functionality with validation
    - Framework template protection backups
    - Backup history and status reporting
    """
    
    def __init__(self, base_dir: Path, retention_days: int = 30, logger: Optional[logging.Logger] = None):
        """
        Initialize the Backup Manager.
        
        Args:
            base_dir: Base directory for storing backups
            retention_days: Number of days to retain backups
            logger: Optional logger instance
        """
        self.base_dir = Path(base_dir)
        self.retention_days = retention_days
        self.logger = logger or logging.getLogger(__name__)
        
        # Create backup directories
        self.backups_dir = self.base_dir / ".claude-pm" / "backups"
        self.framework_backups_dir = self.backups_dir / "framework"
        self.parent_dir_backups_dir = self.backups_dir / "parent_directories"
        
        # Initialize directories
        self._initialize_directories()
        
    def _initialize_directories(self) -> None:
        """Create necessary backup directories."""
        for directory in [self.backups_dir, self.framework_backups_dir, self.parent_dir_backups_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    async def create_backup(self, file_path: Path, backup_type: str = "general") -> Optional[Path]:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            backup_type: Type of backup (general, framework, parent_directory)
            
        Returns:
            Path to the backup file, or None if backup failed
        """
        if not file_path.exists():
            self.logger.warning(f"Cannot backup non-existent file: {file_path}")
            return None
            
        # Determine backup directory based on type
        if backup_type == "framework":
            backup_dir = self.framework_backups_dir
        elif backup_type == "parent_directory":
            backup_dir = self.parent_dir_backups_dir
        else:
            backup_dir = self.backups_dir / "general"
            backup_dir.mkdir(exist_ok=True)
            
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}.backup"
        backup_path = backup_dir / backup_filename
        
        try:
            # Copy the file
            shutil.copy2(file_path, backup_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(file_path)
            
            # Save backup metadata
            metadata = {
                "source_path": str(file_path),
                "backup_path": str(backup_path),
                "timestamp": datetime.now().isoformat(),
                "checksum": checksum,
                "file_size": file_path.stat().st_size,
                "backup_type": backup_type
            }
            
            metadata_path = backup_path.with_suffix(".json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
            
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    async def restore_backup(self, backup_path: Path, target_path: Optional[Path] = None) -> bool:
        """
        Restore a file from backup.
        
        Args:
            backup_path: Path to the backup file
            target_path: Optional target path (defaults to original location)
            
        Returns:
            True if restore was successful, False otherwise
        """
        if not backup_path.exists():
            self.logger.error(f"Backup file not found: {backup_path}")
            return False
            
        # Load backup metadata
        metadata_path = backup_path.with_suffix(".json")
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            # Determine target path
            if target_path is None:
                target_path = Path(metadata["source_path"])
                
        else:
            # No metadata, use provided target path
            if target_path is None:
                self.logger.error("No target path specified and no metadata found")
                return False
                
        try:
            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the backup file to target
            shutil.copy2(backup_path, target_path)
            
            self.logger.info(f"Restored backup to: {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
            
    def backup_framework_template(self, framework_template_path: Path) -> Optional[Path]:
        """
        Create a backup of the framework template with special handling.
        
        Args:
            framework_template_path: Path to the framework template
            
        Returns:
            Path to the backup file, or None if backup failed
        """
        if not framework_template_path.exists():
            self.logger.warning(f"Framework template not found: {framework_template_path}")
            return None
            
        # Create backup with special naming for framework templates
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        backup_filename = f"framework_CLAUDE_md_{timestamp}.backup"
        backup_path = self.framework_backups_dir / backup_filename
        
        try:
            shutil.copy2(framework_template_path, backup_path)
            self.logger.info(f"Created framework template backup: {backup_path}")
            
            # Rotate framework backups (keep only 2 most recent)
            self._rotate_framework_backups()
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to backup framework template: {e}")
            return None
            
    def _rotate_framework_backups(self) -> None:
        """Keep only the 2 most recent framework template backups."""
        backup_files = sorted(
            [f for f in self.framework_backups_dir.glob("framework_CLAUDE_md_*.backup")],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        # Keep only the 2 most recent
        for old_backup in backup_files[2:]:
            try:
                old_backup.unlink()
                self.logger.debug(f"Removed old framework backup: {old_backup}")
            except Exception as e:
                self.logger.warning(f"Failed to remove old backup {old_backup}: {e}")
                
    async def cleanup_old_backups(self) -> int:
        """
        Clean up backups older than retention period.
        
        Returns:
            Number of backups removed
        """
        removed_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        # Check all backup directories except framework (special handling)
        for backup_dir in [self.backups_dir / "general", self.parent_dir_backups_dir]:
            if not backup_dir.exists():
                continue
                
            for backup_file in backup_dir.glob("*.backup"):
                # Check metadata for timestamp
                metadata_path = backup_file.with_suffix(".json")
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        backup_time = datetime.fromisoformat(metadata["timestamp"])
                        
                        if backup_time < cutoff_date:
                            backup_file.unlink()
                            metadata_path.unlink()
                            removed_count += 1
                            self.logger.debug(f"Removed old backup: {backup_file}")
                            
                    except Exception as e:
                        self.logger.warning(f"Error processing backup {backup_file}: {e}")
                        
        return removed_count
        
    def get_backup_status(self) -> Dict[str, Any]:
        """
        Get status information about backups.
        
        Returns:
            Dictionary containing backup statistics and information
        """
        status = {
            "total_backups": 0,
            "framework_backups": 0,
            "parent_directory_backups": 0,
            "general_backups": 0,
            "total_size": 0,
            "oldest_backup": None,
            "newest_backup": None,
            "backup_directories": {}
        }
        
        # Count backups by type
        if self.framework_backups_dir.exists():
            framework_backups = list(self.framework_backups_dir.glob("*.backup"))
            status["framework_backups"] = len(framework_backups)
            status["total_backups"] += len(framework_backups)
            
        if self.parent_dir_backups_dir.exists():
            parent_backups = list(self.parent_dir_backups_dir.glob("*.backup"))
            status["parent_directory_backups"] = len(parent_backups)
            status["total_backups"] += len(parent_backups)
            
        general_dir = self.backups_dir / "general"
        if general_dir.exists():
            general_backups = list(general_dir.glob("*.backup"))
            status["general_backups"] = len(general_backups)
            status["total_backups"] += len(general_backups)
            
        # Calculate total size and find oldest/newest
        all_backups = []
        for backup_dir in [self.framework_backups_dir, self.parent_dir_backups_dir, general_dir]:
            if backup_dir.exists():
                for backup_file in backup_dir.glob("*.backup"):
                    all_backups.append(backup_file)
                    status["total_size"] += backup_file.stat().st_size
                    
        if all_backups:
            sorted_backups = sorted(all_backups, key=lambda f: f.stat().st_mtime)
            status["oldest_backup"] = {
                "path": str(sorted_backups[0]),
                "timestamp": datetime.fromtimestamp(sorted_backups[0].stat().st_mtime).isoformat()
            }
            status["newest_backup"] = {
                "path": str(sorted_backups[-1]),
                "timestamp": datetime.fromtimestamp(sorted_backups[-1].stat().st_mtime).isoformat()
            }
            
        # Directory information
        status["backup_directories"] = {
            "base": str(self.backups_dir),
            "framework": str(self.framework_backups_dir),
            "parent_directory": str(self.parent_dir_backups_dir),
            "general": str(general_dir)
        }
        
        return status
        
    def get_framework_backup_status(self) -> Dict[str, Any]:
        """
        Get detailed status about framework template backups.
        
        Returns:
            Dictionary containing framework backup information
        """
        backups = []
        
        if self.framework_backups_dir.exists():
            for backup_file in sorted(
                self.framework_backups_dir.glob("framework_CLAUDE_md_*.backup"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            ):
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size": backup_file.stat().st_size,
                    "created": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                    "age_days": (datetime.now() - datetime.fromtimestamp(backup_file.stat().st_mtime)).days
                })
                
        return {
            "framework_backups_dir": str(self.framework_backups_dir),
            "backup_count": len(backups),
            "total_size": sum(b["size"] for b in backups),
            "backups": backups[:10],  # Return only 10 most recent
            "rotation_policy": "Keep 2 most recent backups"
        }