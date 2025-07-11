#!/usr/bin/env python3
"""
Integration Tests for Template Management System - CMPM-102
==========================================================

End-to-end integration tests for the complete template management system
including deployment detection, template operations, and CLI integration.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import Mock, AsyncMock, patch

# Import the services and CLI
from claude_pm.services.template_manager import TemplateManager, TemplateType, TemplateSource
from claude_pm.services.template_deployment_integration import TemplateDeploymentIntegration
from claude_pm.commands.template_commands import template


class TestTemplateSystemIntegration:
    """Integration tests for the complete template management system."""
    
    @pytest.fixture
    def temp_framework_dir(self):
        """Create a temporary framework directory with structure."""
        temp_dir = tempfile.mkdtemp()
        framework_dir = Path(temp_dir)
        
        # Create framework structure
        (framework_dir / "claude_pm" / "templates").mkdir(parents=True)
        (framework_dir / "framework" / "templates").mkdir(parents=True)
        (framework_dir / "bin").mkdir(parents=True)
        (framework_dir / "scripts").mkdir(parents=True)
        (framework_dir / "tasks").mkdir(parents=True)
        (framework_dir / ".claude-pm").mkdir(parents=True)
        
        # Create some sample templates
        (framework_dir / "framework" / "templates" / "projects").mkdir(parents=True)
        (framework_dir / "framework" / "templates" / "tickets").mkdir(parents=True)
        (framework_dir / "framework" / "templates" / "agents").mkdir(parents=True)
        
        # Sample project template
        project_template = """# Project: {{PROJECT_NAME}}

## Description
{{PROJECT_DESCRIPTION}}

## Technology Stack
- **Language**: {{LANGUAGE}}
- **Framework**: {{FRAMEWORK}}

## Setup Instructions
{{SETUP_INSTRUCTIONS}}

## Usage
{{USAGE_INSTRUCTIONS}}
"""
        (framework_dir / "framework" / "templates" / "projects" / "basic-project.template").write_text(project_template)
        
        # Sample ticket template
        ticket_template = """# {{TICKET_TYPE}}: {{TITLE}}

## Description
{{DESCRIPTION}}

## Acceptance Criteria
{{ACCEPTANCE_CRITERIA}}

## Tasks
{{TASKS}}

## Priority: {{PRIORITY}}
## Status: {{STATUS}}
"""
        (framework_dir / "framework" / "templates" / "tickets" / "basic-ticket.template").write_text(ticket_template)
        
        # Sample agent template
        agent_template = '''#!/usr/bin/env python3
"""
{{AGENT_NAME}} Agent - {{AGENT_DESCRIPTION}}
"""

from claude_pm.core.base_agent import BaseAgent

class {{AGENT_CLASS}}(BaseAgent):
    """{{AGENT_DESCRIPTION}}"""
    
    def __init__(self):
        super().__init__(
            agent_id="{{AGENT_ID}}",
            agent_type="{{AGENT_TYPE}}",
            capabilities=[{{CAPABILITIES}}]
        )
    
    async def execute_task(self, task_description: str) -> dict:
        """Execute a task for this agent."""
        return {
            "status": "completed",
            "result": f"{{AGENT_NAME}} executed: {task_description}"
        }
'''
        (framework_dir / "framework" / "templates" / "agents" / "basic-agent.template").write_text(agent_template)
        
        yield framework_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_deployment_config(self, temp_framework_dir):
        """Create a comprehensive mock deployment configuration."""
        working_dir = temp_framework_dir / "working"
        working_dir.mkdir()
        
        return {
            "strategy": "local_source",
            "config": {
                "deploymentType": "local_source",
                "found": True,
                "platform": "darwin",
                "confidence": "high",
                "frameworkPath": str(temp_framework_dir),
                "paths": {
                    "framework": str(temp_framework_dir),
                    "claudePm": str(temp_framework_dir / "claude_pm"),
                    "bin": str(temp_framework_dir / "bin"),
                    "config": str(temp_framework_dir / ".claude-pm"),
                    "templates": str(temp_framework_dir / "framework" / "templates"),
                    "schemas": str(temp_framework_dir / "schemas"),
                    "working": str(working_dir)
                },
                "metadata": {
                    "packageJson": {},
                    "isDevelopment": True
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_full_template_lifecycle(self, temp_framework_dir, mock_deployment_config):
        """Test complete template lifecycle from creation to deployment."""
        
        # Initialize the template deployment integration
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Test 1: Create a new template
            template_id = "test-integration-template"
            template_content = """# {{PROJECT_NAME}} Integration Test

## Description
This is a test template for {{PROJECT_TYPE}} projects.

## Requirements
- {{LANGUAGE}} {{VERSION}}
- {{FRAMEWORK}}

## Features
{{FEATURES}}

## Configuration
```{{CONFIG_FORMAT}}
{{CONFIG_CONTENT}}
```

## Scripts
{{SCRIPTS}}
"""
            variables = {
                "PROJECT_NAME": "My Project",
                "PROJECT_TYPE": "web",
                "LANGUAGE": "TypeScript",
                "VERSION": "5.0",
                "FRAMEWORK": "Next.js",
                "FEATURES": "Authentication, Database, API",
                "CONFIG_FORMAT": "json",
                "CONFIG_CONTENT": "{}",
                "SCRIPTS": "npm run dev"
            }
            
            version = await integration.create_template(
                template_id=template_id,
                template_type=TemplateType.PROJECT,
                content=template_content,
                variables=variables,
                metadata={"author": "integration-test", "category": "web-app"}
            )
            
            assert version.template_id == template_id
            assert version.version == "1.0.0"
            
            # Test 2: Retrieve and render the template
            template_data = await integration.get_template(template_id)
            assert template_data is not None
            
            content, retrieved_version = template_data
            assert content == template_content
            assert retrieved_version.version == "1.0.0"
            
            # Test rendering with custom variables
            custom_variables = {
                "PROJECT_NAME": "Custom Project",
                "PROJECT_TYPE": "api",
                "LANGUAGE": "Python",
                "VERSION": "3.11",
                "FRAMEWORK": "FastAPI",
                "FEATURES": "REST API, Database, Authentication",
                "CONFIG_FORMAT": "yaml",
                "CONFIG_CONTENT": "server:\\n  port: 8000",
                "SCRIPTS": "python main.py"
            }
            
            rendered_content = await integration.render_template(
                template_id=template_id,
                variables=custom_variables
            )
            
            assert "Custom Project" in rendered_content
            assert "Python" in rendered_content
            assert "FastAPI" in rendered_content
            
            # Test 3: Update the template
            updated_content = template_content + "\n\n## Additional Notes\n{{NOTES}}"
            updated_variables = {**variables, "NOTES": "Added in update"}
            
            updated_version = await integration.update_template(
                template_id=template_id,
                content=updated_content,
                variables=updated_variables
            )
            
            assert updated_version.version == "1.0.1"
            assert updated_version.backup_path is not None
            
            # Test 4: Validate the template
            validation_result = await integration.validate_template(template_id)
            assert validation_result.is_valid is True
            assert validation_result.template_id == template_id
            
            # Test 5: Create a backup
            backup_path = await integration.backup_template(template_id)
            assert backup_path is not None
            assert Path(backup_path).exists()
            
            # Test 6: Get template history
            history = await integration.get_template_history(template_id)
            assert len(history) == 2
            assert history[0]["version"] == "1.0.0"
            assert history[1]["version"] == "1.0.1"
            
            # Test 7: Restore previous version
            restore_success = await integration.restore_template(
                template_id=template_id,
                version="1.0.0"
            )
            assert restore_success is True
            
            # Test 8: List templates
            templates = await integration.list_templates()
            template_ids = [t["template_id"] for t in templates]
            assert template_id in template_ids
            
            # Test 9: Get deployment-specific recommendations
            recommendations = await integration.get_deployment_specific_template_recommendations(
                project_type="project",
                requirements=["web", "typescript"]
            )
            assert len(recommendations) > 0
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_template_discovery_and_registration(self, temp_framework_dir, mock_deployment_config):
        """Test automatic template discovery and registration."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # The existing templates should be discovered
            templates = await integration.list_templates()
            template_ids = [t["template_id"] for t in templates]
            
            # Should find our pre-created templates
            assert any("basic-project.template" in tid for tid in template_ids)
            assert any("basic-ticket.template" in tid for tid in template_ids)
            assert any("basic-agent.template" in tid for tid in template_ids)
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_deployment_aware_template_filtering(self, temp_framework_dir, mock_deployment_config):
        """Test deployment-aware template filtering."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Create templates in different sources
            await integration.create_template(
                template_id="user-template",
                template_type=TemplateType.PROJECT,
                content="User template content",
                source=TemplateSource.USER
            )
            
            await integration.create_template(
                template_id="project-template",
                template_type=TemplateType.PROJECT,
                content="Project template content",
                source=TemplateSource.PROJECT
            )
            
            # Test deployment context filtering
            deployment_templates = await integration.get_templates_by_deployment_context(
                template_type=TemplateType.PROJECT,
                include_development=True
            )
            
            assert len(deployment_templates) > 0
            
            # Should include both user and project templates
            template_sources = [t["source"] for t in deployment_templates]
            assert "user" in template_sources
            assert "project" in template_sources
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_template_conflict_resolution(self, temp_framework_dir, mock_deployment_config):
        """Test template conflict detection and resolution."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Create a template
            template_id = "conflict-test-template"
            original_content = "Original content: {{variable}}"
            
            version1 = await integration.create_template(
                template_id=template_id,
                template_type=TemplateType.PROJECT,
                content=original_content,
                variables={"variable": "value1"}
            )
            
            # Update the template to create a potential conflict
            updated_content = "Updated content: {{variable}} {{new_variable}}"
            
            version2 = await integration.update_template(
                template_id=template_id,
                content=updated_content,
                variables={"variable": "value2", "new_variable": "new_value"}
            )
            
            # Verify backup was created
            assert version2.backup_path is not None
            assert Path(version2.backup_path).exists()
            
            # Verify version history
            history = await integration.get_template_history(template_id)
            assert len(history) == 2
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_template_validation_comprehensive(self, temp_framework_dir, mock_deployment_config):
        """Test comprehensive template validation."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Test valid template
            valid_template = "Hello {{name}}! Welcome to {{project}}."
            valid_variables = {"name": "User", "project": "My Project"}
            
            await integration.create_template(
                template_id="valid-template",
                template_type=TemplateType.PROJECT,
                content=valid_template,
                variables=valid_variables
            )
            
            validation_result = await integration.validate_template("valid-template")
            assert validation_result.is_valid is True
            assert len(validation_result.errors) == 0
            
            # Test template with warnings (undefined variables)
            warning_template = "Hello {{name}}! Welcome to {{project}}. Your role is {{role}}."
            partial_variables = {"name": "User", "project": "My Project"}  # missing 'role'
            
            await integration.create_template(
                template_id="warning-template",
                template_type=TemplateType.PROJECT,
                content=warning_template,
                variables=partial_variables
            )
            
            validation_result = await integration.validate_template("warning-template")
            assert validation_result.is_valid is True  # Still valid, but with warnings
            assert len(validation_result.warnings) > 0
            
            # Test invalid template (malformed syntax)
            invalid_template = "Hello {{name! This is broken {{unclosed"
            
            await integration.create_template(
                template_id="invalid-template",
                template_type=TemplateType.PROJECT,
                content=invalid_template
            )
            
            validation_result = await integration.validate_template("invalid-template")
            assert validation_result.is_valid is False
            assert len(validation_result.errors) > 0
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_deployment_access_validation(self, temp_framework_dir, mock_deployment_config):
        """Test deployment template access validation."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Test deployment access validation
            validation_results = await integration.validate_deployment_template_access()
            
            assert "deployment_type" in validation_results
            assert "template_sources" in validation_results
            assert "accessible_templates" in validation_results
            assert "inaccessible_templates" in validation_results
            
            assert validation_results["deployment_type"] == "local_source"
            assert validation_results["accessible_templates"] >= 0
            
            # Should have template sources
            template_sources = validation_results["template_sources"]
            assert "framework" in template_sources
            assert "project" in template_sources
            assert "user" in template_sources
            assert "system" in template_sources
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_template_recommendation_system(self, temp_framework_dir, mock_deployment_config):
        """Test template recommendation system."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Create templates of different types
            await integration.create_template(
                template_id="web-app-template",
                template_type=TemplateType.PROJECT,
                content="Web app template for {{framework}}",
                variables={"framework": "React"},
                metadata={"category": "web", "technology": "react"}
            )
            
            await integration.create_template(
                template_id="api-template",
                template_type=TemplateType.PROJECT,
                content="API template for {{language}}",
                variables={"language": "Python"},
                metadata={"category": "api", "technology": "python"}
            )
            
            # Test recommendations
            recommendations = await integration.get_deployment_specific_template_recommendations(
                project_type="project",
                requirements=["web", "react"]
            )
            
            assert len(recommendations) > 0
            
            # Should be sorted by score
            scores = [r["score"] for r in recommendations]
            assert scores == sorted(scores, reverse=True)
            
            # Each recommendation should have required fields
            for rec in recommendations:
                assert "template_id" in rec
                assert "score" in rec
                assert "reasons" in rec
                assert "deployment_context" in rec
                assert rec["deployment_context"] == "local_source"
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_template_backup_restore_workflow(self, temp_framework_dir, mock_deployment_config):
        """Test comprehensive backup and restore workflow."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Create initial template
            template_id = "backup-restore-template"
            v1_content = "Version 1 content: {{variable}}"
            v1_variables = {"variable": "value1"}
            
            v1 = await integration.create_template(
                template_id=template_id,
                template_type=TemplateType.PROJECT,
                content=v1_content,
                variables=v1_variables
            )
            
            # Update to version 2
            v2_content = "Version 2 content: {{variable}} {{new_var}}"
            v2_variables = {"variable": "value2", "new_var": "new_value"}
            
            v2 = await integration.update_template(
                template_id=template_id,
                content=v2_content,
                variables=v2_variables
            )
            
            # Update to version 3
            v3_content = "Version 3 content: {{variable}} {{new_var}} {{third_var}}"
            v3_variables = {"variable": "value3", "new_var": "new_value", "third_var": "third"}
            
            v3 = await integration.update_template(
                template_id=template_id,
                content=v3_content,
                variables=v3_variables
            )
            
            # Verify we have 3 versions
            history = await integration.get_template_history(template_id)
            assert len(history) == 3
            
            # Create explicit backup
            backup_path = await integration.backup_template(template_id)
            assert backup_path is not None
            assert Path(backup_path).exists()
            
            # Restore to version 1
            restore_success = await integration.restore_template(template_id, v1.version)
            assert restore_success is True
            
            # Verify restoration
            template_data = await integration.get_template(template_id)
            assert template_data is not None
            
            # Restore to version 2
            restore_success = await integration.restore_template(template_id, v2.version)
            assert restore_success is True
            
            # Try to restore non-existent version
            restore_success = await integration.restore_template(template_id, "99.99.99")
            assert restore_success is False
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_template_deployment_config_integration(self, temp_framework_dir, mock_deployment_config):
        """Test integration with deployment configuration."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Get deployment-aware configuration
            deployment_config = await integration.get_deployment_aware_template_config()
            
            assert deployment_config.deployment_type.value == "local_source"
            assert deployment_config.is_development is True
            assert deployment_config.confidence == "high"
            
            # Template sources should be properly configured
            template_sources = deployment_config.template_sources
            assert TemplateSource.SYSTEM in template_sources
            assert TemplateSource.FRAMEWORK in template_sources
            assert TemplateSource.USER in template_sources
            assert TemplateSource.PROJECT in template_sources
            
            # Framework path should be correct
            assert deployment_config.framework_path == temp_framework_dir
            
            await integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, temp_framework_dir, mock_deployment_config):
        """Test error handling and recovery scenarios."""
        
        with patch.object(TemplateDeploymentIntegration, '_get_deployment_configuration') as mock_get_config:
            mock_get_config.return_value = mock_deployment_config
            
            integration = TemplateDeploymentIntegration()
            await integration.initialize()
            
            # Test creating template with invalid ID
            with pytest.raises(ValueError):
                await integration.create_template(
                    template_id="",  # Empty ID
                    template_type=TemplateType.PROJECT,
                    content="test content"
                )
            
            # Test updating non-existent template
            with pytest.raises(ValueError):
                await integration.update_template(
                    template_id="non-existent-template",
                    content="new content"
                )
            
            # Test getting non-existent template
            result = await integration.get_template("non-existent-template")
            assert result is None
            
            # Test rendering non-existent template
            result = await integration.render_template(
                template_id="non-existent-template",
                variables={"test": "value"}
            )
            assert result is None
            
            # Test validation of non-existent template
            validation_result = await integration.validate_template("non-existent-template")
            assert validation_result.is_valid is False
            assert "Template not found" in validation_result.errors
            
            # Test backup of non-existent template
            backup_path = await integration.backup_template("non-existent-template")
            assert backup_path is None
            
            # Test restore of non-existent template
            restore_success = await integration.restore_template(
                template_id="non-existent-template",
                version="1.0.0"
            )
            assert restore_success is False
            
            await integration.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])