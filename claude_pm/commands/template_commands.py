#!/usr/bin/env python3
"""
Template Management CLI Commands - CMPM-102
==========================================

CLI commands for managing templates with versioning, backup/restore,
and deployment-aware functionality.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Prompt, Confirm

from ..services.template_manager import TemplateManager, TemplateType, TemplateSource, ConflictResolution
from ..services.template_deployment_integration import TemplateDeploymentIntegration
from ..core.logging_config import setup_logging


console = Console()
logger = setup_logging(__name__)


@click.group()
@click.pass_context
def template(ctx):
    """Template management commands with versioning and deployment awareness."""
    ctx.ensure_object(dict)


@template.command()
@click.option('--deployment-info', is_flag=True, help='Show deployment information')
@click.option('--template-sources', is_flag=True, help='Show template source paths')
@click.option('--validation', is_flag=True, help='Run template access validation')
@click.pass_context
async def status(ctx, deployment_info, template_sources, validation):
    """Show template management status and deployment information."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        console.print("\n" + "="*70)
        console.print("🗂️  [bold blue]Template Management Status[/bold blue]")
        console.print("="*70)
        
        # Get deployment configuration
        deployment_config = await integration.get_deployment_aware_template_config()
        
        # Basic status
        console.print(f"📍 Deployment Type: {deployment_config.deployment_type.value}")
        console.print(f"📂 Framework Path: {deployment_config.framework_path}")
        console.print(f"🎯 Confidence: {deployment_config.confidence}")
        console.print(f"🔧 Development Mode: {'Yes' if deployment_config.is_development else 'No'}")
        
        # Template sources
        if template_sources or deployment_info:
            console.print(f"\n📁 [bold]Template Sources:[/bold]")
            for source, path in deployment_config.template_sources.items():
                exists = "✅" if path.exists() else "❌"
                console.print(f"   • {source.value}: {path} {exists}")
        
        # Validation
        if validation:
            console.print(f"\n🔍 [bold]Template Access Validation:[/bold]")
            validation_results = await integration.validate_deployment_template_access()
            
            console.print(f"   • Accessible Templates: {validation_results['accessible_templates']}")
            console.print(f"   • Inaccessible Templates: {validation_results['inaccessible_templates']}")
            
            if validation_results['warnings']:
                console.print(f"\n⚠️  [bold yellow]Warnings:[/bold yellow]")
                for warning in validation_results['warnings']:
                    console.print(f"   • {warning}")
        
        # List templates
        templates = await integration.list_templates()
        if templates:
            console.print(f"\n📄 [bold]Available Templates:[/bold]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Template ID", style="dim")
            table.add_column("Name")
            table.add_column("Type", justify="center")
            table.add_column("Source", justify="center")
            table.add_column("Version", justify="center")
            table.add_column("Versions", justify="center")
            table.add_column("Updated", style="dim")
            
            for template in templates:
                table.add_row(
                    template["template_id"],
                    template["name"],
                    template["type"],
                    template["source"],
                    template["current_version"],
                    str(template["total_versions"]),
                    template["updated_at"][:10]  # Just the date
                )
            
            console.print(table)
        else:
            console.print(f"\n❌ No templates found")
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template status command failed: {e}")


@template.command()
@click.argument('template_id')
@click.option('--type', 'template_type', type=click.Choice(['project', 'agent', 'ticket', 'scaffolding', 'documentation', 'configuration']), default='project', help='Template type')
@click.option('--source', type=click.Choice(['system', 'framework', 'user', 'project']), default='project', help='Template source')
@click.option('--content', help='Template content (or provide via stdin)')
@click.option('--file', 'content_file', type=click.Path(exists=True), help='File containing template content')
@click.option('--variables', help='Template variables as JSON string')
@click.option('--metadata', help='Template metadata as JSON string')
@click.pass_context
async def create(ctx, template_id, template_type, source, content, content_file, variables, metadata):
    """Create a new template with versioning."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Get content
        if content_file:
            content = Path(content_file).read_text()
        elif content:
            content = content
        else:
            content = click.get_text_stream('stdin').read()
        
        if not content.strip():
            console.print("❌ Error: Template content is required")
            return
        
        # Parse variables and metadata
        template_variables = {}
        if variables:
            try:
                template_variables = json.loads(variables)
            except json.JSONDecodeError:
                console.print("❌ Error: Invalid JSON in variables")
                return
        
        template_metadata = {}
        if metadata:
            try:
                template_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                console.print("❌ Error: Invalid JSON in metadata")
                return
        
        # Create template
        version = await integration.create_template(
            template_id=template_id,
            template_type=TemplateType(template_type),
            content=content,
            variables=template_variables,
            metadata=template_metadata,
            source=TemplateSource(source)
        )
        
        console.print(f"✅ Created template: {template_id} v{version.version}")
        console.print(f"   • Type: {template_type}")
        console.print(f"   • Source: {source}")
        console.print(f"   • Checksum: {version.checksum[:8]}...")
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template create command failed: {e}")


@template.command()
@click.argument('template_id')
@click.option('--content', help='New template content (or provide via stdin)')
@click.option('--file', 'content_file', type=click.Path(exists=True), help='File containing new template content')
@click.option('--variables', help='Updated template variables as JSON string')
@click.option('--metadata', help='Updated template metadata as JSON string')
@click.option('--conflict-resolution', type=click.Choice(['backup_and_replace', 'merge', 'skip', 'prompt_user']), default='backup_and_replace', help='Conflict resolution strategy')
@click.pass_context
async def update(ctx, template_id, content, content_file, variables, metadata, conflict_resolution):
    """Update an existing template with versioning."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Get content
        if content_file:
            content = Path(content_file).read_text()
        elif content:
            content = content
        else:
            content = click.get_text_stream('stdin').read()
        
        if not content.strip():
            console.print("❌ Error: Template content is required")
            return
        
        # Parse variables and metadata
        template_variables = {}
        if variables:
            try:
                template_variables = json.loads(variables)
            except json.JSONDecodeError:
                console.print("❌ Error: Invalid JSON in variables")
                return
        
        template_metadata = {}
        if metadata:
            try:
                template_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                console.print("❌ Error: Invalid JSON in metadata")
                return
        
        # Update template
        version = await integration.update_template(
            template_id=template_id,
            content=content,
            variables=template_variables,
            metadata=template_metadata,
            conflict_resolution=ConflictResolution(conflict_resolution)
        )
        
        console.print(f"✅ Updated template: {template_id} v{version.version}")
        console.print(f"   • Checksum: {version.checksum[:8]}...")
        if version.backup_path:
            console.print(f"   • Backup: {version.backup_path}")
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template update command failed: {e}")


@template.command()
@click.argument('template_id')
@click.option('--version', help='Specific version to get (latest if not specified)')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--show-metadata', is_flag=True, help='Show template metadata')
@click.pass_context
async def get(ctx, template_id, version, output, show_metadata):
    """Get template content and information."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Get template
        template_data = await integration.get_template(template_id, version)
        if not template_data:
            console.print(f"❌ Template not found: {template_id}")
            return
        
        content, template_version = template_data
        
        # Show metadata if requested
        if show_metadata:
            console.print(f"📄 [bold]Template Information:[/bold]")
            console.print(f"   • Template ID: {template_version.template_id}")
            console.print(f"   • Version: {template_version.version}")
            console.print(f"   • Source: {template_version.source.value}")
            console.print(f"   • Created: {template_version.created_at}")
            console.print(f"   • Checksum: {template_version.checksum[:8]}...")
            
            if template_version.metadata:
                console.print(f"   • Metadata: {json.dumps(template_version.metadata, indent=2)}")
            
            if template_version.variables:
                console.print(f"   • Variables: {json.dumps(template_version.variables, indent=2)}")
            
            console.print()
        
        # Output content
        if output:
            Path(output).write_text(content)
            console.print(f"✅ Template content saved to: {output}")
        else:
            console.print(content)
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template get command failed: {e}")


@template.command()
@click.argument('template_id')
@click.option('--variables', help='Template variables as JSON string')
@click.option('--variables-file', type=click.Path(exists=True), help='File containing variables as JSON')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--version', help='Specific version to render')
@click.pass_context
async def render(ctx, template_id, variables, variables_file, output, version):
    """Render template with variables."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Get variables
        template_variables = {}
        if variables_file:
            template_variables = json.loads(Path(variables_file).read_text())
        elif variables:
            try:
                template_variables = json.loads(variables)
            except json.JSONDecodeError:
                console.print("❌ Error: Invalid JSON in variables")
                return
        
        # Render template
        rendered_content = await integration.render_template(
            template_id=template_id,
            variables=template_variables,
            version=version
        )
        
        if not rendered_content:
            console.print(f"❌ Failed to render template: {template_id}")
            return
        
        # Output content
        if output:
            Path(output).write_text(rendered_content)
            console.print(f"✅ Rendered template saved to: {output}")
        else:
            console.print(rendered_content)
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template render command failed: {e}")


@template.command()
@click.argument('template_id')
@click.option('--version', help='Specific version to validate (latest if not specified)')
@click.pass_context
async def validate(ctx, template_id, version):
    """Validate template for correctness."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Validate template
        result = await integration.validate_template(template_id, version)
        
        console.print(f"🔍 [bold]Template Validation: {template_id}[/bold]")
        console.print(f"   • Valid: {'✅' if result.is_valid else '❌'}")
        
        if result.errors:
            console.print(f"   • Errors:")
            for error in result.errors:
                console.print(f"     - {error}")
        
        if result.warnings:
            console.print(f"   • Warnings:")
            for warning in result.warnings:
                console.print(f"     - {warning}")
        
        if result.suggestions:
            console.print(f"   • Suggestions:")
            for suggestion in result.suggestions:
                console.print(f"     - {suggestion}")
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template validate command failed: {e}")


@template.command()
@click.argument('template_id')
@click.pass_context
async def backup(ctx, template_id):
    """Create a backup of a template."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Create backup
        backup_path = await integration.backup_template(template_id)
        
        if backup_path:
            console.print(f"✅ Template backup created: {backup_path}")
        else:
            console.print(f"❌ Failed to create backup for template: {template_id}")
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template backup command failed: {e}")


@template.command()
@click.argument('template_id')
@click.argument('version')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
async def restore(ctx, template_id, version, confirm):
    """Restore template from a specific version."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Confirm restoration
        if not confirm:
            if not Confirm.ask(f"Are you sure you want to restore {template_id} to version {version}?"):
                console.print("❌ Restore cancelled")
                return
        
        # Restore template
        success = await integration.restore_template(template_id, version)
        
        if success:
            console.print(f"✅ Template restored: {template_id} v{version}")
        else:
            console.print(f"❌ Failed to restore template: {template_id} v{version}")
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template restore command failed: {e}")


@template.command()
@click.argument('template_id')
@click.pass_context
async def history(ctx, template_id):
    """Show version history for a template."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Get history
        history_data = await integration.get_template_history(template_id)
        
        if not history_data:
            console.print(f"❌ No history found for template: {template_id}")
            return
        
        console.print(f"📜 [bold]Template History: {template_id}[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Version")
        table.add_column("Source", justify="center")
        table.add_column("Created", style="dim")
        table.add_column("Checksum", style="dim")
        table.add_column("Backup", justify="center")
        
        for version_info in history_data:
            backup_status = "✅" if version_info["has_backup"] else "❌"
            table.add_row(
                version_info["version"],
                version_info["source"],
                version_info["created_at"][:16],  # Date and time
                version_info["checksum"][:8],
                backup_status
            )
        
        console.print(table)
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template history command failed: {e}")


@template.command()
@click.option('--type', 'template_type', type=click.Choice(['project', 'agent', 'ticket', 'scaffolding', 'documentation', 'configuration']), help='Filter by template type')
@click.option('--source', type=click.Choice(['system', 'framework', 'user', 'project']), help='Filter by template source')
@click.option('--deployment-context', is_flag=True, help='Show deployment context information')
@click.pass_context
async def list(ctx, template_type, source, deployment_context):
    """List all templates with optional filtering."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Get templates
        if deployment_context:
            templates = await integration.get_templates_by_deployment_context(
                TemplateType(template_type) if template_type else None
            )
        else:
            templates = await integration.list_templates(
                TemplateType(template_type) if template_type else None,
                TemplateSource(source) if source else None
            )
        
        if not templates:
            console.print("❌ No templates found")
            return
        
        console.print(f"📄 [bold]Templates Found: {len(templates)}[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Template ID", style="dim")
        table.add_column("Name")
        table.add_column("Type", justify="center")
        table.add_column("Source", justify="center")
        table.add_column("Version", justify="center")
        table.add_column("Versions", justify="center")
        table.add_column("Backup", justify="center")
        table.add_column("Updated", style="dim")
        
        for template in templates:
            backup_status = "✅" if template.get("has_backup", False) else "❌"
            table.add_row(
                template["template_id"],
                template["name"],
                template["type"],
                template["source"],
                template["current_version"],
                str(template["total_versions"]),
                backup_status,
                template["updated_at"][:10]  # Just the date
            )
        
        console.print(table)
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template list command failed: {e}")


@template.command()
@click.argument('project_type')
@click.option('--requirements', help='Project requirements as JSON array')
@click.option('--show-reasons', is_flag=True, help='Show recommendation reasons')
@click.pass_context
async def recommend(ctx, project_type, requirements, show_reasons):
    """Get template recommendations for a project type."""
    try:
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Parse requirements
        req_list = []
        if requirements:
            try:
                req_list = json.loads(requirements)
            except json.JSONDecodeError:
                console.print("❌ Error: Invalid JSON in requirements")
                return
        
        # Get recommendations
        recommendations = await integration.get_deployment_specific_template_recommendations(
            project_type, req_list
        )
        
        if not recommendations:
            console.print(f"❌ No template recommendations found for project type: {project_type}")
            return
        
        console.print(f"🎯 [bold]Template Recommendations for: {project_type}[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rank", justify="center")
        table.add_column("Template ID", style="dim")
        table.add_column("Name")
        table.add_column("Type", justify="center")
        table.add_column("Source", justify="center")
        table.add_column("Score", justify="center")
        if show_reasons:
            table.add_column("Reasons", style="dim")
        
        for i, rec in enumerate(recommendations[:10], 1):  # Show top 10
            row = [
                str(i),
                rec["template_id"],
                rec["template_name"],
                rec["template_type"],
                rec["source"],
                str(rec["score"])
            ]
            if show_reasons:
                row.append("; ".join(rec["reasons"]))
            table.add_row(*row)
        
        console.print(table)
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template recommend command failed: {e}")


@template.command()
@click.option('--target-dir', type=click.Path(), help='Target directory (defaults to parent of current working directory)')
@click.option('--backup/--no-backup', default=True, help='Create backup of existing CLAUDE.md file')
@click.option('--force', is_flag=True, help='Force overwrite without confirmation')
@click.pass_context
async def deploy_claude_md(ctx, target_dir, backup, force):
    """Deploy CLAUDE.md template to parent directory with handlebars processing."""
    try:
        import platform
        import shutil
        from datetime import datetime
        
        # Initialize template deployment integration
        integration = TemplateDeploymentIntegration()
        await integration._initialize()
        
        # Get deployment config
        deployment_config = await integration.get_deployment_aware_template_config()
        
        # Determine target directory
        if target_dir:
            target_directory = Path(target_dir)
        else:
            target_directory = Path.cwd().parent
        
        # Ensure target directory exists
        target_directory.mkdir(parents=True, exist_ok=True)
        
        # Check for framework CLAUDE.md template
        # Use explicit framework path to avoid deployment detection issues
        framework_path = Path(__file__).parent.parent.parent  # Go up to project root
        framework_template_path = framework_path / "framework" / "CLAUDE.md"
        
        if not framework_template_path.exists():
            console.print(f"❌ Framework CLAUDE.md template not found at: {framework_template_path}")
            return
        
        # Read template content
        template_content = framework_template_path.read_text()
        
        # Set up template variables for handlebars processing
        template_variables = {
            "FRAMEWORK_VERSION": "4.5.1",
            "DEPLOYMENT_DATE": datetime.now().isoformat(),
            "PLATFORM": platform.system().lower(),
            "PYTHON_CMD": "python3",
            "DEPLOYMENT_ID": str(int(datetime.now().timestamp() * 1000)),
            "DEPLOYMENT_DIR": str(framework_path),
            "WORKING_DIR": str(Path.cwd()),
            "TARGET_DIR": str(target_directory),
            "AI_TRACKDOWN_PATH": "/Users/masa/.nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/ai-trackdown-tools/dist/index.js",
            "PLATFORM_NOTES": "**macOS-specific:**\n- Use `.sh` files for scripts\n- CLI wrappers: `bin/aitrackdown` and `bin/atd`\n- Health check: `scripts/health-check.sh`\n- May require Xcode Command Line Tools",
            "LAST_UPDATED": datetime.now().isoformat()
        }
        
        console.print(f"🔧 [bold]Deploying CLAUDE.md Template[/bold]")
        console.print(f"   • Framework Path: {framework_path}")
        console.print(f"   • Template Path: {framework_template_path}")
        console.print(f"   • Target Directory: {target_directory}")
        
        # Process handlebars variables
        processed_content = template_content
        for key, value in template_variables.items():
            placeholder = f"{{{{{key}}}}}"
            processed_content = processed_content.replace(placeholder, str(value))
        
        # Handle target file
        target_file = target_directory / "CLAUDE.md"
        
        # Create backup if file exists and backup is enabled
        if target_file.exists() and backup:
            backup_filename = f"CLAUDE.md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = target_directory / backup_filename
            shutil.copy2(target_file, backup_path)
            console.print(f"   • Created backup: {backup_path}")
        
        # Check if file exists and get confirmation
        if target_file.exists() and not force:
            if not Confirm.ask(f"CLAUDE.md already exists at {target_file}. Overwrite?"):
                console.print("❌ Deployment cancelled")
                return
        
        # Write processed content
        target_file.write_text(processed_content)
        
        console.print(f"✅ [bold green]CLAUDE.md deployed successfully![/bold green]")
        console.print(f"   • Target: {target_file}")
        console.print(f"   • Size: {len(processed_content)} characters")
        console.print(f"   • Variables processed: {len(template_variables)}")
        
        # Show processed variables
        console.print(f"\n🔍 [bold]Template Variables:[/bold]")
        for key, value in template_variables.items():
            console.print(f"   • {key}: {value}")
        
        await integration._cleanup()
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"Template deploy-claude-md command failed: {e}")


# Add the template command group to the main CLI
def add_template_commands(cli):
    """Add template management commands to the CLI."""
    cli.add_command(template)