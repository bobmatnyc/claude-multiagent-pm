#!/usr/bin/env python3
"""
Tests for Template Manager Service - CMPM-102
=============================================

Comprehensive tests for the template management system including:
- Template creation and versioning
- Backup/restore functionality
- Conflict resolution
- Deployment integration
- Template validation
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import Mock, AsyncMock, patch

# Import the services to test
from claude_pm.services.template_manager import (
    TemplateManager, 
    TemplateType, 
    TemplateSource, 
    ConflictResolution,
    TemplateVersion,
    TemplateConflict,
    TemplateValidationResult
)
from claude_pm.services.template_deployment_integration import (
    TemplateDeploymentIntegration,
    DeploymentType,
    DeploymentAwareTemplateConfig
)


class TestTemplateManager:
    """Tests for the core Template Manager functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def deployment_config(self, temp_dir):
        """Create a mock deployment configuration."""
        return {
            "config": {
                "deploymentType": "local_source",
                "found": True,
                "platform": "darwin",
                "confidence": "high",
                "frameworkPath": str(temp_dir / "framework"),
                "paths": {
                    "framework": str(temp_dir / "framework"),
                    "working": str(temp_dir / "working"),
                    "templates": str(temp_dir / "framework" / "templates"),
                    "config": str(temp_dir / ".claude-pm")
                }
            }
        }
    
    @pytest.fixture
    async def template_manager(self, temp_dir, deployment_config):
        """Create a template manager instance for testing."""
        # Create test directory structure
        (temp_dir / "framework" / "templates").mkdir(parents=True)
        (temp_dir / "working" / ".claude-pm").mkdir(parents=True)
        
        manager = TemplateManager(deployment_config)
        await manager.initialize()
        yield manager
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_template_creation(self, template_manager):
        """Test creating a new template."""
        template_id = "test-template"
        content = "Hello {{name}}!"
        variables = {"name": "World"}
        metadata = {"author": "test"}
        
        version = await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content=content,
            variables=variables,
            metadata=metadata
        )
        
        assert version.template_id == template_id
        assert version.version == "1.0.0"
        assert version.source == TemplateSource.PROJECT
        assert version.checksum is not None
        assert version.variables == variables
        assert version.metadata == metadata
        
        # Verify template is registered
        assert template_id in template_manager.template_registry
        assert template_id in template_manager.version_registry
    
    @pytest.mark.asyncio
    async def test_template_update(self, template_manager):
        """Test updating an existing template."""
        template_id = "test-template"
        original_content = "Hello {{name}}!"
        updated_content = "Hello {{name}}, welcome!"
        
        # Create initial template
        await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content=original_content
        )
        
        # Update template
        updated_version = await template_manager.update_template(
            template_id=template_id,
            content=updated_content,
            conflict_resolution=ConflictResolution.BACKUP_AND_REPLACE
        )
        
        assert updated_version.version == "1.0.1"
        assert updated_version.template_id == template_id
        assert updated_version.backup_path is not None
        
        # Verify version history
        versions = template_manager.version_registry[template_id]
        assert len(versions) == 2
        assert versions[0].version == "1.0.0"
        assert versions[1].version == "1.0.1"
    
    @pytest.mark.asyncio
    async def test_template_retrieval(self, template_manager):
        """Test retrieving template content."""
        template_id = "test-template"
        content = "Hello {{name}}!"
        
        # Create template
        await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content=content
        )
        
        # Retrieve template
        template_data = await template_manager.get_template(template_id)
        assert template_data is not None
        
        retrieved_content, version = template_data
        assert retrieved_content == content
        assert version.template_id == template_id
        assert version.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_template_rendering(self, template_manager):
        """Test rendering template with variables."""
        template_id = "test-template"
        content = "Hello {{name}}! You are {{age}} years old."
        variables = {"name": "Alice", "age": "25"}
        
        # Create template
        await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content=content,
            variables={"name": "Default", "age": "0"}
        )
        
        # Render template
        rendered = await template_manager.render_template(
            template_id=template_id,
            variables=variables
        )
        
        expected = "Hello Alice! You are 25 years old."
        assert rendered == expected
    
    @pytest.mark.asyncio
    async def test_template_backup_restore(self, template_manager):
        """Test template backup and restore functionality."""
        template_id = "test-template"
        original_content = "Original content"
        updated_content = "Updated content"
        
        # Create initial template
        version1 = await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content=original_content
        )
        
        # Update template
        version2 = await template_manager.update_template(
            template_id=template_id,
            content=updated_content
        )
        
        # Create explicit backup
        backup_path = await template_manager.backup_template(template_id)
        assert backup_path is not None
        assert Path(backup_path).exists()
        
        # Restore to previous version
        success = await template_manager.restore_template(
            template_id=template_id,
            version=version1.version
        )
        assert success is True
        
        # Verify restoration
        template_data = await template_manager.get_template(template_id)
        assert template_data is not None
        
        restored_content, restored_version = template_data
        # Note: After restore, the current version should be updated
        assert template_manager.template_registry[template_id]["current_version"] == version1.version
    
    @pytest.mark.asyncio
    async def test_template_validation(self, template_manager):
        """Test template validation."""
        template_id = "test-template"
        content = "Hello {{name}}! Missing variable: {{missing}}"
        
        # Create template with undefined variable
        await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content=content,
            variables={"name": "World"}  # missing variable not defined
        )
        
        # Validate template
        result = await template_manager.validate_template(template_id)
        
        assert isinstance(result, TemplateValidationResult)
        assert result.template_id == template_id
        assert result.is_valid is True  # Should be valid even with warnings
        assert len(result.warnings) > 0  # Should have warnings about undefined variables
    
    @pytest.mark.asyncio
    async def test_template_listing(self, template_manager):
        """Test listing templates with filtering."""
        # Create multiple templates
        await template_manager.create_template(
            template_id="project-template",
            template_type=TemplateType.PROJECT,
            content="Project template"
        )
        
        await template_manager.create_template(
            template_id="agent-template",
            template_type=TemplateType.AGENT,
            content="Agent template"
        )
        
        # List all templates
        all_templates = await template_manager.list_templates()
        assert len(all_templates) >= 2
        
        # Filter by type
        project_templates = await template_manager.list_templates(
            template_type=TemplateType.PROJECT
        )
        assert len(project_templates) >= 1
        assert all(t["type"] == "project" for t in project_templates)
        
        agent_templates = await template_manager.list_templates(
            template_type=TemplateType.AGENT
        )
        assert len(agent_templates) >= 1
        assert all(t["type"] == "agent" for t in agent_templates)
    
    @pytest.mark.asyncio
    async def test_template_history(self, template_manager):
        """Test template version history."""
        template_id = "test-template"
        
        # Create template
        await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content="Version 1"
        )
        
        # Update template multiple times
        await template_manager.update_template(
            template_id=template_id,
            content="Version 2"
        )
        
        await template_manager.update_template(
            template_id=template_id,
            content="Version 3"
        )
        
        # Get history
        history = await template_manager.get_template_history(template_id)
        assert len(history) == 3
        
        # Verify history order (should be chronological)
        versions = [h["version"] for h in history]
        assert versions == ["1.0.0", "1.0.1", "1.0.2"]
    
    @pytest.mark.asyncio
    async def test_conflict_resolution(self, template_manager):
        """Test conflict resolution strategies."""
        template_id = "test-template"
        content = "Original content"
        
        # Create template
        await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content=content
        )
        
        # Test backup and replace strategy
        updated_version = await template_manager.update_template(
            template_id=template_id,
            content="Updated content",
            conflict_resolution=ConflictResolution.BACKUP_AND_REPLACE
        )
        
        assert updated_version.backup_path is not None
        assert Path(updated_version.backup_path).exists()
        
        # Test skip strategy
        # First, we need to simulate a conflict situation
        # This would require more sophisticated conflict detection
        # For now, just verify the method accepts the parameter
        await template_manager.update_template(
            template_id=template_id,
            content="Another update",
            conflict_resolution=ConflictResolution.SKIP
        )
    
    def test_checksum_calculation(self, template_manager):
        """Test file checksum calculation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()
            
            checksum = template_manager._calculate_file_checksum(Path(f.name))
            assert checksum is not None
            assert len(checksum) == 64  # SHA256 is 64 characters
        
        os.unlink(f.name)
    
    def test_version_generation(self, template_manager):
        """Test version number generation."""
        template_id = "test-template"
        
        # First version
        version1 = template_manager._generate_next_version(template_id)
        assert version1 == "1.0.0"
        
        # Simulate existing version
        template_manager.version_registry[template_id] = [
            Mock(version="1.0.5")
        ]
        
        version2 = template_manager._generate_next_version(template_id)
        assert version2 == "1.0.6"


class TestTemplateDeploymentIntegration:
    """Tests for the deployment integration functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_deployment_config(self, temp_dir):
        """Create a mock deployment configuration."""
        return {
            "strategy": "local_source",
            "config": {
                "deploymentType": "local_source",
                "found": True,
                "platform": "darwin",
                "confidence": "high",
                "frameworkPath": str(temp_dir / "framework"),
                "paths": {
                    "framework": str(temp_dir / "framework"),
                    "working": str(temp_dir / "working"),
                    "templates": str(temp_dir / "framework" / "templates"),
                    "config": str(temp_dir / ".claude-pm")
                },
                "metadata": {
                    "isDevelopment": True
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_deployment_integration_initialization(self, temp_dir, mock_deployment_config):
        """Test deployment integration initialization."""
        # Create test directory structure
        (temp_dir / "framework" / "templates").mkdir(parents=True)
        (temp_dir / "working" / ".claude-pm").mkdir(parents=True)
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            success = await integration.initialize()
            
            assert success is True
            assert integration.deployment_config == mock_deployment_config
            assert integration.template_manager is not None
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_deployment_aware_template_config(self, temp_dir, mock_deployment_config):
        """Test deployment-aware template configuration."""
        # Create test directory structure
        (temp_dir / "framework" / "templates").mkdir(parents=True)
        (temp_dir / "working" / ".claude-pm").mkdir(parents=True)
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            config = await integration.get_deployment_aware_template_config()
            
            assert isinstance(config, DeploymentAwareTemplateConfig)
            assert config.deployment_type == DeploymentType.LOCAL_SOURCE
            assert config.is_development is True
            assert config.confidence == "high"
            assert TemplateSource.SYSTEM in config.template_sources
            assert TemplateSource.FRAMEWORK in config.template_sources
            assert TemplateSource.USER in config.template_sources
            assert TemplateSource.PROJECT in config.template_sources
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_deployment_template_validation(self, temp_dir, mock_deployment_config):
        """Test deployment template access validation."""
        # Create test directory structure
        (temp_dir / "framework" / "templates").mkdir(parents=True)
        (temp_dir / "working" / ".claude-pm").mkdir(parents=True)
        
        # Create some test templates
        (temp_dir / "framework" / "templates" / "test.template").write_text("test content")
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            validation = await integration.validate_deployment_template_access()
            
            assert "deployment_type" in validation
            assert "template_sources" in validation
            assert "accessible_templates" in validation
            assert validation["deployment_type"] == "local_source"
            assert validation["accessible_templates"] >= 0
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_deployment_template_recommendations(self, temp_dir, mock_deployment_config):
        """Test deployment-specific template recommendations."""
        # Create test directory structure
        (temp_dir / "framework" / "templates").mkdir(parents=True)
        (temp_dir / "working" / ".claude-pm").mkdir(parents=True)
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Mock the template manager to return some templates
            mock_templates = [
                {
                    "template_id": "project-template",
                    "name": "Project Template",
                    "type": "project",
                    "source": "framework",
                    "current_version": "1.0.0",
                    "total_versions": 1,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00",
                    "has_backup": False
                }
            ]
            
            with patch.object(integration, 'get_templates_by_deployment_context') as mock_get_templates:
                mock_get_templates.return_value = mock_templates
                
                recommendations = await integration.get_deployment_specific_template_recommendations(
                    project_type="project",
                    requirements=["web", "typescript"]
                )
                
                assert len(recommendations) > 0
                assert all("score" in rec for rec in recommendations)
                assert all("reasons" in rec for rec in recommendations)
                assert all("deployment_context" in rec for rec in recommendations)
            
            await integration.cleanup()


class TestTemplateManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def template_manager(self, temp_dir):
        """Create a template manager instance for testing."""
        deployment_config = {
            "config": {
                "deploymentType": "local_source",
                "found": True,
                "platform": "darwin",
                "confidence": "high",
                "frameworkPath": str(temp_dir / "framework"),
                "paths": {
                    "framework": str(temp_dir / "framework"),
                    "working": str(temp_dir / "working"),
                    "templates": str(temp_dir / "framework" / "templates"),
                    "config": str(temp_dir / ".claude-pm")
                }
            }
        }
        
        # Create test directory structure
        (temp_dir / "framework" / "templates").mkdir(parents=True)
        (temp_dir / "working" / ".claude-pm").mkdir(parents=True)
        
        manager = TemplateManager(deployment_config)
        await manager.initialize()
        yield manager
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_create_template_with_empty_content(self, template_manager):
        """Test creating template with empty content."""
        with pytest.raises(ValueError):
            await template_manager.create_template(
                template_id="empty-template",
                template_type=TemplateType.PROJECT,
                content=""
            )
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_template(self, template_manager):
        """Test updating a template that doesn't exist."""
        with pytest.raises(ValueError):
            await template_manager.update_template(
                template_id="nonexistent-template",
                content="new content"
            )
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self, template_manager):
        """Test retrieving a template that doesn't exist."""
        result = await template_manager.get_template("nonexistent-template")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_render_nonexistent_template(self, template_manager):
        """Test rendering a template that doesn't exist."""
        result = await template_manager.render_template(
            template_id="nonexistent-template",
            variables={"test": "value"}
        )
        assert result is None
    
    @pytest.mark.asyncio
    async def test_backup_nonexistent_template(self, template_manager):
        """Test backing up a template that doesn't exist."""
        result = await template_manager.backup_template("nonexistent-template")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_restore_nonexistent_template(self, template_manager):
        """Test restoring a template that doesn't exist."""
        result = await template_manager.restore_template(
            template_id="nonexistent-template",
            version="1.0.0"
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_nonexistent_template(self, template_manager):
        """Test validating a template that doesn't exist."""
        result = await template_manager.validate_template("nonexistent-template")
        assert result.is_valid is False
        assert "Template not found" in result.errors
    
    @pytest.mark.asyncio
    async def test_template_validation_with_errors(self, template_manager):
        """Test template validation with various error conditions."""
        # Create template with unclosed variables
        template_id = "bad-template"
        content = "Hello {{name! This is broken {{unclosed"
        
        await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content=content
        )
        
        result = await template_manager.validate_template(template_id)
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_version_cleanup(self, template_manager):
        """Test cleanup of old versions."""
        template_id = "test-template"
        
        # Set max versions to 3 for testing
        template_manager.max_versions_per_template = 3
        
        # Create template
        await template_manager.create_template(
            template_id=template_id,
            template_type=TemplateType.PROJECT,
            content="Version 1"
        )
        
        # Update multiple times to exceed max versions
        for i in range(5):
            await template_manager.update_template(
                template_id=template_id,
                content=f"Version {i+2}"
            )
        
        # Check that only max versions are kept
        versions = template_manager.version_registry[template_id]
        assert len(versions) <= template_manager.max_versions_per_template
    
    @pytest.mark.asyncio
    async def test_permission_errors(self, template_manager, temp_dir):
        """Test handling of permission errors."""
        # Create a directory with restricted permissions
        restricted_dir = temp_dir / "restricted"
        restricted_dir.mkdir(mode=0o000)
        
        try:
            # Try to create template in restricted directory
            template_manager.template_paths[TemplateSource.PROJECT] = restricted_dir
            
            with pytest.raises(PermissionError):
                await template_manager.create_template(
                    template_id="restricted-template",
                    template_type=TemplateType.PROJECT,
                    content="test content"
                )
        finally:
            # Restore permissions for cleanup
            restricted_dir.chmod(0o755)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])