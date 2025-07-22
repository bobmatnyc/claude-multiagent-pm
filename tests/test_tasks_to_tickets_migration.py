#!/usr/bin/env python3
"""
Comprehensive test suite for tasks/ to tickets/ migration functionality
Testing automatic migration and directory structure updates
"""

import os
import shutil
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import asyncio

from claude_pm.utils.tasks_to_tickets_migration import (
    TasksToTicketsMigration,
    check_and_migrate_tasks_directory
)


class TestTasksToTicketsMigration:
    """Test suite for tasks to tickets migration utility."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with tasks/ structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "test_project"
            project_dir.mkdir()
            
            # Create tasks directory with content
            tasks_dir = project_dir / "tasks"
            tasks_dir.mkdir()
            
            # Create sample task files
            (tasks_dir / "task1.md").write_text("# Task 1\nContent for task 1")
            (tasks_dir / "task2.md").write_text("# Task 2\nContent for task 2")
            
            # Create subdirectories
            sub_dir = tasks_dir / "archive"
            sub_dir.mkdir()
            (sub_dir / "old_task.md").write_text("# Old Task\nArchived content")
            
            yield project_dir
    
    @pytest.fixture
    def migration(self):
        """Create migration instance."""
        return TasksToTicketsMigration()
    
    def test_check_for_tasks_directory(self, migration, temp_project):
        """Test detection of tasks/ directory."""
        assert migration.check_for_tasks_directory(temp_project) is True
        
        # Test non-existent directory
        assert migration.check_for_tasks_directory(temp_project / "nonexistent") is False
    
    def test_check_for_tickets_directory(self, migration, temp_project):
        """Test detection of tickets/ directory."""
        assert migration.check_for_tickets_directory(temp_project) is False
        
        # Create tickets directory
        (temp_project / "tickets").mkdir()
        assert migration.check_for_tickets_directory(temp_project) is True
    
    def test_needs_migration(self, migration, temp_project):
        """Test migration need detection."""
        # Should need migration (has tasks, no tickets)
        assert migration.needs_migration(temp_project) is True
        
        # Create tickets directory - should not need migration
        (temp_project / "tickets").mkdir()
        assert migration.needs_migration(temp_project) is False
        
        # Remove tasks directory - should not need migration
        shutil.rmtree(temp_project / "tasks")
        assert migration.needs_migration(temp_project) is False
    
    def test_perform_migration_dry_run(self, migration, temp_project):
        """Test dry run migration."""
        result = migration.perform_migration(temp_project, dry_run=True)
        
        assert result["success"] is True
        assert result["migrated"] is False  # Dry run doesn't actually migrate
        assert result["files_migrated"] == 3  # task1.md, task2.md, old_task.md
        assert (temp_project / "tasks").exists()  # Original still exists
        assert not (temp_project / "tickets").exists()  # Not created in dry run
    
    def test_perform_migration_actual(self, migration, temp_project):
        """Test actual migration."""
        result = migration.perform_migration(temp_project, dry_run=False)
        
        assert result["success"] is True
        assert result["migrated"] is True
        assert result["files_migrated"] == 3
        assert not (temp_project / "tasks").exists()  # Original removed
        assert (temp_project / "tickets").exists()  # New directory created
        
        # Check files were moved
        assert (temp_project / "tickets" / "task1.md").exists()
        assert (temp_project / "tickets" / "task2.md").exists()
        assert (temp_project / "tickets" / "archive" / "old_task.md").exists()
        
        # Check backup was created
        assert result["backup_created"] is not None
        backup_path = Path(result["backup_created"])
        assert backup_path.exists()
        assert backup_path.name.startswith("tasks_backup_")
    
    def test_migration_when_tickets_exists(self, migration, temp_project):
        """Test migration when tickets/ already exists."""
        # Create tickets directory
        (temp_project / "tickets").mkdir()
        
        result = migration.perform_migration(temp_project, dry_run=False)
        
        assert result["success"] is True
        assert result["migrated"] is False
        assert "tickets/ directory already exists" in result["migration_log"][0]
    
    def test_config_file_updates(self, migration, temp_project):
        """Test configuration file updates during migration."""
        # Create config files with tasks/ references
        gitignore = temp_project / ".gitignore"
        gitignore.write_text("tasks/temp/\ntasks/*.log\n")
        
        readme = temp_project / "README.md"
        readme.write_text("# Project\n\nSee tasks/ directory for task list.\n")
        
        package_json = temp_project / "package.json"
        package_json.write_text(json.dumps({
            "scripts": {
                "task": "cd tasks && npm run start"
            }
        }, indent=2))
        
        # Perform migration
        result = migration.perform_migration(temp_project, dry_run=False)
        
        assert result["success"] is True
        assert len(result["config_files_updated"]) >= 3
        
        # Check file contents were updated
        assert "tickets/temp/" in gitignore.read_text()
        assert "tickets/*.log" in gitignore.read_text()
        assert "See tickets/ directory" in readme.read_text()
        
        package_data = json.loads(package_json.read_text())
        assert "cd tickets" in package_data["scripts"]["task"]
    
    def test_ai_trackdown_config_update(self, migration, temp_project):
        """Test ai-trackdown specific config updates."""
        # Create ai-trackdown config
        ai_config_dir = temp_project / ".ai-trackdown"
        ai_config_dir.mkdir()
        
        ai_config = ai_config_dir / "config.json"
        ai_config.write_text(json.dumps({
            "tasksDirectory": "tasks/",
            "paths": {
                "tasks": "tasks/",
                "archive": "tasks/archive/"
            },
            "ignore": ["tasks/temp/*"]
        }, indent=2))
        
        # Perform migration
        result = migration.perform_migration(temp_project, dry_run=False)
        
        assert result["success"] is True
        assert ".ai-trackdown/config.json" in result["config_files_updated"]
        
        # Check config was updated
        updated_config = json.loads(ai_config.read_text())
        assert updated_config["tasksDirectory"] == "tickets/"
        assert updated_config["paths"]["tasks"] == "tickets/"
        assert updated_config["paths"]["archive"] == "tickets/archive/"
        assert "tickets/temp/*" in updated_config["ignore"]
    
    def test_user_notification(self, migration, temp_project):
        """Test user notification generation."""
        result = migration.perform_migration(temp_project, dry_run=False)
        
        assert "user_notification" in result
        notification = result["user_notification"]
        
        assert "AUTOMATIC MIGRATION COMPLETED" in notification
        assert f"Migrated: {result['files_migrated']} files" in notification
        assert "No action required" in notification
    
    def test_error_handling(self, migration, temp_project):
        """Test error handling during migration."""
        # Make tasks directory read-only to trigger error
        tasks_dir = temp_project / "tasks"
        os.chmod(tasks_dir, 0o444)
        
        try:
            result = migration.perform_migration(temp_project, dry_run=False)
            
            # Should handle error gracefully
            assert result["success"] is False
            assert result["error"] is not None
            assert len(result["migration_log"]) > 0
        finally:
            # Restore permissions for cleanup
            os.chmod(tasks_dir, 0o755)
    
    @pytest.mark.asyncio
    async def test_check_and_migrate_tasks_directory(self, temp_project):
        """Test the main entry point function."""
        # Test with migration needed
        result = await check_and_migrate_tasks_directory(temp_project, silent=True)
        
        assert result["success"] is True
        assert result["migrated"] is True
        assert (temp_project / "tickets").exists()
        assert not (temp_project / "tasks").exists()
        
        # Test when no migration needed
        result2 = await check_and_migrate_tasks_directory(temp_project, silent=True)
        
        assert result2["success"] is True
        assert result2["migrated"] is False
        assert result2["message"] == "No migration needed"
    
    def test_migration_preserves_file_permissions(self, migration, temp_project):
        """Test that file permissions are preserved during migration."""
        # Create a file with specific permissions
        task_file = temp_project / "tasks" / "executable_task.sh"
        task_file.write_text("#!/bin/bash\necho 'Task script'")
        os.chmod(task_file, 0o755)  # Make executable
        
        # Get original permissions
        original_mode = task_file.stat().st_mode
        
        # Perform migration
        result = migration.perform_migration(temp_project, dry_run=False)
        
        assert result["success"] is True
        
        # Check permissions were preserved
        migrated_file = temp_project / "tickets" / "executable_task.sh"
        assert migrated_file.exists()
        assert migrated_file.stat().st_mode == original_mode
    
    def test_edge_case_empty_tasks_directory(self, migration):
        """Test migration with empty tasks directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "empty_project"
            project_dir.mkdir()
            
            # Create empty tasks directory
            tasks_dir = project_dir / "tasks"
            tasks_dir.mkdir()
            
            result = migration.perform_migration(project_dir, dry_run=False)
            
            assert result["success"] is True
            assert result["migrated"] is True
            assert result["files_migrated"] == 0
            assert (project_dir / "tickets").exists()
            assert not (project_dir / "tasks").exists()
    
    def test_edge_case_deeply_nested_structure(self, migration):
        """Test migration with deeply nested directory structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "nested_project"
            project_dir.mkdir()
            
            # Create deeply nested structure
            deep_path = project_dir / "tasks" / "level1" / "level2" / "level3"
            deep_path.mkdir(parents=True)
            
            # Add files at various levels
            (project_dir / "tasks" / "root_task.md").write_text("Root level task")
            (project_dir / "tasks" / "level1" / "level1_task.md").write_text("Level 1 task")
            (deep_path / "deep_task.md").write_text("Deep task")
            
            result = migration.perform_migration(project_dir, dry_run=False)
            
            assert result["success"] is True
            assert result["migrated"] is True
            assert result["files_migrated"] == 3
            
            # Check structure was preserved
            assert (project_dir / "tickets" / "root_task.md").exists()
            assert (project_dir / "tickets" / "level1" / "level1_task.md").exists()
            assert (project_dir / "tickets" / "level1" / "level2" / "level3" / "deep_task.md").exists()


class TestMigrationIntegration:
    """Test migration integration with CLI commands."""
    
    @pytest.mark.integration
    def test_init_command_integration(self):
        """Test that init command properly integrates migration."""
        # This would test the actual CLI command integration
        # Requires setting up a test environment with the CLI
        pass
    
    @pytest.mark.integration
    def test_deploy_command_integration(self):
        """Test that deploy command properly integrates migration."""
        # This would test the actual CLI command integration
        # Requires setting up a test environment with the CLI
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])