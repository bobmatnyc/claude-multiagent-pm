#!/usr/bin/env python3
"""
Tasks to Tickets Migration Utility

Provides automatic migration from legacy tasks/ directory structure to new tickets/ structure.
This ensures backward compatibility for existing projects using the old naming convention.
"""

import os
import shutil
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TasksToTicketsMigration:
    """Handles automatic migration from tasks/ to tickets/ directory structure."""
    
    def __init__(self):
        self.migration_log = []
        self.dry_run = False
        
    def check_for_tasks_directory(self, project_root: Path) -> bool:
        """Check if a tasks/ directory exists in the project."""
        tasks_dir = project_root / "tasks"
        return tasks_dir.exists() and tasks_dir.is_dir()
    
    def check_for_tickets_directory(self, project_root: Path) -> bool:
        """Check if a tickets/ directory exists in the project."""
        tickets_dir = project_root / "tickets"
        return tickets_dir.exists() and tickets_dir.is_dir()
    
    def needs_migration(self, project_root: Path) -> bool:
        """Determine if migration is needed."""
        has_tasks = self.check_for_tasks_directory(project_root)
        has_tickets = self.check_for_tickets_directory(project_root)
        
        # Migration needed if tasks exists but tickets doesn't
        return has_tasks and not has_tickets
    
    def perform_migration(self, project_root: Path, dry_run: bool = False) -> Dict[str, Any]:
        """
        Perform the migration from tasks/ to tickets/.
        
        Args:
            project_root: Root directory of the project
            dry_run: If True, only simulate the migration without making changes
            
        Returns:
            Dictionary containing migration results
        """
        self.dry_run = dry_run
        self.migration_log = []
        
        result = {
            "success": False,
            "migrated": False,
            "tasks_dir": str(project_root / "tasks"),
            "tickets_dir": str(project_root / "tickets"),
            "files_migrated": 0,
            "config_files_updated": [],
            "backup_created": None,
            "migration_log": [],
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check if migration is needed
            if not self.needs_migration(project_root):
                if self.check_for_tickets_directory(project_root):
                    result["success"] = True
                    result["migrated"] = False
                    result["migration_log"].append("tickets/ directory already exists, no migration needed")
                else:
                    result["success"] = True
                    result["migrated"] = False
                    result["migration_log"].append("No tasks/ directory found, no migration needed")
                return result
            
            tasks_dir = project_root / "tasks"
            tickets_dir = project_root / "tickets"
            
            self._log(f"Starting migration from {tasks_dir} to {tickets_dir}")
            
            if not dry_run:
                # Create backup
                backup_path = self._create_backup(tasks_dir)
                result["backup_created"] = str(backup_path)
                self._log(f"Created backup at {backup_path}")
                
                # Rename directory
                shutil.move(str(tasks_dir), str(tickets_dir))
                self._log(f"Renamed {tasks_dir} to {tickets_dir}")
                result["migrated"] = True
                
                # Count migrated files
                file_count = sum(1 for _ in tickets_dir.rglob("*") if _.is_file())
                result["files_migrated"] = file_count
                self._log(f"Migrated {file_count} files")
            else:
                self._log("DRY RUN: Would rename tasks/ to tickets/")
                # Count files that would be migrated
                file_count = sum(1 for _ in tasks_dir.rglob("*") if _.is_file())
                result["files_migrated"] = file_count
                self._log(f"DRY RUN: Would migrate {file_count} files")
            
            # Update configuration files
            config_updates = self._update_config_files(project_root, dry_run)
            result["config_files_updated"] = config_updates
            
            # Update ai-trackdown config if present
            ai_trackdown_updates = self._update_ai_trackdown_config(project_root, dry_run)
            if ai_trackdown_updates:
                result["config_files_updated"].extend(ai_trackdown_updates)
            
            result["success"] = True
            result["migration_log"] = self.migration_log
            
            # Add user notification message
            if not dry_run and result["migrated"]:
                notification = self._create_user_notification(result)
                result["user_notification"] = notification
            
            return result
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            result["error"] = str(e)
            result["migration_log"] = self.migration_log
            return result
    
    def _log(self, message: str):
        """Add message to migration log."""
        self.migration_log.append(message)
        logger.info(f"Migration: {message}")
    
    def _create_backup(self, tasks_dir: Path) -> Path:
        """Create a backup of the tasks directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"tasks_backup_{timestamp}"
        backup_path = tasks_dir.parent / backup_name
        
        shutil.copytree(tasks_dir, backup_path)
        return backup_path
    
    def _update_config_files(self, project_root: Path, dry_run: bool) -> List[str]:
        """Update any configuration files that reference tasks/."""
        updated_files = []
        
        # Common config files to check
        config_patterns = [
            ".claude-pm/config.json",
            "claude-pm.config.json",
            "package.json",
            ".gitignore",
            "README.md",
            "*.md"
        ]
        
        for pattern in config_patterns:
            if "*" in pattern:
                # Handle glob patterns
                for file_path in project_root.glob(pattern):
                    if file_path.is_file():
                        if self._update_file_references(file_path, dry_run):
                            updated_files.append(str(file_path.relative_to(project_root)))
            else:
                # Handle specific files
                file_path = project_root / pattern
                if file_path.exists() and file_path.is_file():
                    if self._update_file_references(file_path, dry_run):
                        updated_files.append(pattern)
        
        return updated_files
    
    def _update_ai_trackdown_config(self, project_root: Path, dry_run: bool) -> List[str]:
        """Update ai-trackdown specific configuration files."""
        updated_files = []
        
        # Check for ai-trackdown config files
        ai_trackdown_configs = [
            ".ai-trackdown/config.json",
            "ai-trackdown.config.json",
            ".ai-trackdown.json"
        ]
        
        for config_file in ai_trackdown_configs:
            file_path = project_root / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        config_data = json.load(f)
                    
                    # Update paths in config
                    updated = False
                    if isinstance(config_data, dict):
                        updated = self._update_dict_paths(config_data)
                    
                    if updated and not dry_run:
                        with open(file_path, 'w') as f:
                            json.dump(config_data, f, indent=2)
                        updated_files.append(config_file)
                        self._log(f"Updated ai-trackdown config: {config_file}")
                    elif updated and dry_run:
                        self._log(f"DRY RUN: Would update ai-trackdown config: {config_file}")
                        updated_files.append(config_file)
                        
                except Exception as e:
                    logger.warning(f"Failed to update {config_file}: {e}")
        
        return updated_files
    
    def _update_dict_paths(self, data: Dict[str, Any]) -> bool:
        """Recursively update paths in dictionary from tasks/ to tickets/."""
        updated = False
        
        for key, value in data.items():
            if isinstance(value, str) and ("tasks/" in value or "tasks\\" in value):
                data[key] = value.replace("tasks/", "tickets/").replace("tasks\\", "tickets\\")
                updated = True
            elif isinstance(value, dict):
                if self._update_dict_paths(value):
                    updated = True
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and ("tasks/" in item or "tasks\\" in item):
                        value[i] = item.replace("tasks/", "tickets/").replace("tasks\\", "tickets\\")
                        updated = True
                    elif isinstance(item, dict):
                        if self._update_dict_paths(item):
                            updated = True
        
        return updated
    
    def _update_file_references(self, file_path: Path, dry_run: bool) -> bool:
        """Update references from tasks/ to tickets/ in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file contains references to tasks
            original_content = content
            
            # Replace different patterns of tasks references
            # Pattern 1: tasks/ or tasks\ (with path separator)
            content = content.replace("tasks/", "tickets/").replace("tasks\\", "tickets\\")
            
            # Pattern 2: "tasks" in common contexts (quotes, spaces, etc.)
            # Be careful to only replace when it's clearly referring to the directory
            # Match tasks preceded by: quotes, spaces, =, or start of line
            # and followed by: quotes, spaces, &&, ||, ;, or end of line
            content = re.sub(r'(["\'`\s=]|^)tasks(["\'`\s&|;]|$)', r'\1tickets\2', content)
            
            # Check if any changes were made
            if content == original_content:
                return False
            
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self._log(f"Updated references in {file_path.name}")
            else:
                self._log(f"DRY RUN: Would update references in {file_path.name}")
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to update {file_path}: {e}")
            return False
    
    def _create_user_notification(self, result: Dict[str, Any]) -> str:
        """Create a user-friendly notification message."""
        notification = f"""
╔══════════════════════════════════════════════════════════════╗
║           AUTOMATIC MIGRATION COMPLETED                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Your 'tasks/' directory has been automatically migrated     ║
║  to 'tickets/' to match the new framework structure.        ║
║                                                              ║
║  ✓ Migrated: {result['files_migrated']} files                           ║
║  ✓ Backup created: {Path(result['backup_created']).name if result['backup_created'] else 'None'}      ║
║  ✓ Config files updated: {len(result['config_files_updated'])}                        ║
║                                                              ║
║  No action required - your project continues to work         ║
║  normally with the new structure.                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        return notification.strip()


async def check_and_migrate_tasks_directory(project_root: Path, silent: bool = False) -> Dict[str, Any]:
    """
    Check for tasks/ directory and migrate if needed.
    
    This is the main entry point for automatic migration during initialization.
    
    Args:
        project_root: Root directory of the project
        silent: If True, suppress user notifications
        
    Returns:
        Migration result dictionary
    """
    migration = TasksToTicketsMigration()
    
    # First do a dry run to check what would happen
    dry_run_result = migration.perform_migration(project_root, dry_run=True)
    
    if dry_run_result["files_migrated"] > 0:
        # Perform actual migration
        result = migration.perform_migration(project_root, dry_run=False)
        
        # Display notification unless silent
        if not silent and result.get("user_notification"):
            print(result["user_notification"])
        
        return result
    else:
        return {
            "success": True,
            "migrated": False,
            "message": "No migration needed"
        }