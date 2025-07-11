# Template Management System - CMPM-102

## Overview

The Template Management System (CMPM-102) provides comprehensive versioned template management with backup/restore capabilities, deployment-aware template sourcing, and integration with the CMPM-101 Deployment Detection System.

## Architecture

### Core Components

1. **TemplateManager** - Core template management with versioning
2. **TemplateDeploymentIntegration** - Deployment-aware template operations
3. **Template CLI Commands** - Command-line interface for template operations
4. **Template Validation** - Template correctness and completeness validation

### Key Features

- **Versioned Templates**: Full version control with automatic backup creation
- **Deployment Awareness**: Templates sourced based on deployment configuration
- **Conflict Resolution**: Automated conflict detection and resolution strategies
- **Template Hierarchy**: System → Framework → User → Project template precedence
- **Cross-Platform Support**: Works across all deployment types
- **CLI Integration**: Rich command-line interface for all operations

## Template Sources

The system supports a hierarchical template source system:

### Source Hierarchy (Lowest to Highest Priority)

1. **System Templates** (`/framework/claude_pm/templates/`)
   - Core framework templates
   - Immutable, always available
   - Lowest precedence

2. **Framework Templates** (`/framework/framework/templates/`)
   - Framework-provided templates
   - Available in all deployments
   - Standard templates for common scenarios

3. **User Templates** (`~/.claude-pm/templates/`)
   - User-defined global templates
   - Available across all projects
   - Personal customizations

4. **Project Templates** (`$PROJECT/.claude-pm/templates/`)
   - Project-specific templates
   - Highest precedence
   - Override all other sources

### Template Types

- **Project Templates**: Complete project scaffolding
- **Agent Templates**: AI agent implementations
- **Ticket Templates**: Issue, epic, and task templates
- **Scaffolding Templates**: Component and module templates
- **Documentation Templates**: README, documentation patterns
- **Configuration Templates**: Config file templates

## Template Versioning

### Version Management

- **Semantic Versioning**: Uses `major.minor.patch` format
- **Automatic Incrementing**: Patch version increments on updates
- **Version History**: Complete history of all template versions
- **Backup Integration**: Automatic backup creation on updates

### Conflict Resolution Strategies

1. **Backup and Replace** (Default)
   - Creates backup of current version
   - Replaces with new content
   - Preserves all history

2. **Merge** 
   - Attempts intelligent merging
   - Manual review may be required
   - Preserves both versions

3. **Skip**
   - Skips update due to conflicts
   - Preserves current version
   - Logs conflict for review

4. **Prompt User**
   - Interactive conflict resolution
   - User chooses resolution strategy
   - Full control over conflicts

## Deployment Integration

### CMPM-101 Integration

The system integrates with CMPM-101 Deployment Detection for:

- **Deployment-Aware Paths**: Template sources based on deployment type
- **Configuration Discovery**: Automatic deployment configuration detection
- **Cross-Deployment Compatibility**: Works with all deployment scenarios
- **Fallback Mechanisms**: Graceful degradation when deployment detection fails

### Deployment Types Supported

- **Local Source**: Development from source repository
- **NPM Global**: Global npm installation
- **NPM Local**: Local npm installation
- **NPX**: NPX execution
- **Deployed**: Deployed instance
- **Environment**: Environment-configured
- **Fallback**: Manual configuration

## Template Operations

### Core Operations

#### Create Template
```python
version = await template_manager.create_template(
    template_id="my-template",
    template_type=TemplateType.PROJECT,
    content="Template content with {{variables}}",
    variables={"variable": "default_value"},
    metadata={"author": "user", "category": "web"}
)
```

#### Update Template
```python
version = await template_manager.update_template(
    template_id="my-template",
    content="Updated content with {{variables}}",
    variables={"variable": "updated_value"},
    conflict_resolution=ConflictResolution.BACKUP_AND_REPLACE
)
```

#### Get Template
```python
template_data = await template_manager.get_template(
    template_id="my-template",
    version="1.0.0"  # Optional, latest if not specified
)
if template_data:
    content, version = template_data
```

#### Render Template
```python
rendered = await template_manager.render_template(
    template_id="my-template",
    variables={"variable": "custom_value", "name": "Project Name"}
)
```

#### Backup Template
```python
backup_path = await template_manager.backup_template("my-template")
```

#### Restore Template
```python
success = await template_manager.restore_template(
    template_id="my-template",
    version="1.0.0"
)
```

#### Validate Template
```python
result = await template_manager.validate_template("my-template")
if result.is_valid:
    print("Template is valid")
else:
    print("Errors:", result.errors)
    print("Warnings:", result.warnings)
```

### Template Listing and Discovery

#### List Templates
```python
# List all templates
templates = await template_manager.list_templates()

# Filter by type
project_templates = await template_manager.list_templates(
    template_type=TemplateType.PROJECT
)

# Filter by source
user_templates = await template_manager.list_templates(
    source=TemplateSource.USER
)
```

#### Get Template History
```python
history = await template_manager.get_template_history("my-template")
for version_info in history:
    print(f"Version {version_info['version']}: {version_info['created_at']}")
```

#### Get Recommendations
```python
recommendations = await integration.get_deployment_specific_template_recommendations(
    project_type="web-app",
    requirements=["typescript", "react", "nextjs"]
)
```

## CLI Interface

### Template Status
```bash
# Show template management status
claude-pm template status

# Show deployment information
claude-pm template status --deployment-info

# Show template sources
claude-pm template status --template-sources

# Run validation
claude-pm template status --validation
```

### Template Operations
```bash
# Create template
claude-pm template create my-template --type project --content "Template content"

# Create from file
claude-pm template create my-template --type project --file template.txt

# Update template
claude-pm template update my-template --content "Updated content"

# Get template
claude-pm template get my-template

# Get specific version
claude-pm template get my-template --version 1.0.0

# Render template
claude-pm template render my-template --variables '{"name": "My Project"}'

# Validate template
claude-pm template validate my-template
```

### Template Management
```bash
# List templates
claude-pm template list

# Filter by type
claude-pm template list --type project

# Filter by source
claude-pm template list --source user

# Show template history
claude-pm template history my-template

# Backup template
claude-pm template backup my-template

# Restore template
claude-pm template restore my-template 1.0.0
```

### Template Recommendations
```bash
# Get recommendations
claude-pm template recommend web-app --requirements '["typescript", "react"]'

# Show recommendation reasons
claude-pm template recommend web-app --show-reasons
```

## Configuration

### Template Manager Configuration

Templates are configured through the deployment configuration system:

```json
{
  "template_manager": {
    "backup_retention_days": 30,
    "max_versions_per_template": 10,
    "auto_backup_enabled": true,
    "conflict_resolution": "backup_and_replace"
  }
}
```

### Template Metadata

Templates support rich metadata:

```json
{
  "template_id": "web-app-template",
  "metadata": {
    "author": "framework-team",
    "category": "web-application",
    "description": "Full-stack web application template",
    "tags": ["typescript", "react", "nextjs"],
    "difficulty": "intermediate",
    "estimated_setup_time": "30 minutes"
  }
}
```

## Template Development

### Template Syntax

Templates use simple variable substitution:

```markdown
# {{PROJECT_NAME}}

## Description
{{PROJECT_DESCRIPTION}}

## Technology Stack
- **Language**: {{LANGUAGE}}
- **Framework**: {{FRAMEWORK}}

## Setup
\`\`\`bash
{{SETUP_COMMANDS}}
\`\`\`

## Usage
{{USAGE_INSTRUCTIONS}}
```

### Template Variables

Variables can have default values:

```python
variables = {
    "PROJECT_NAME": "My Project",
    "PROJECT_DESCRIPTION": "A new project",
    "LANGUAGE": "TypeScript",
    "FRAMEWORK": "Next.js",
    "SETUP_COMMANDS": "npm install",
    "USAGE_INSTRUCTIONS": "npm run dev"
}
```

### Template Validation Rules

1. **Syntax Validation**
   - No unclosed variable brackets
   - Valid variable names
   - Proper template structure

2. **Variable Validation**
   - All variables defined
   - No undefined variables used
   - Consistent variable naming

3. **Content Validation**
   - Non-empty template content
   - Readable template files
   - Valid file permissions

## Error Handling

### Common Errors

1. **Template Not Found**
   - Check template ID spelling
   - Verify template exists in expected source
   - Use `list` command to see available templates

2. **Version Not Found**
   - Check version number format
   - Use `history` command to see available versions
   - Verify version exists in registry

3. **Conflict Detection**
   - Review conflict resolution strategy
   - Check for file modifications outside system
   - Use backup/restore for recovery

4. **Permission Errors**
   - Check file system permissions
   - Verify write access to template directories
   - Use appropriate user permissions

### Recovery Procedures

1. **Restore from Backup**
   ```bash
   claude-pm template restore template-id version
   ```

2. **Rebuild Template Registry**
   ```bash
   # Re-initialize template manager
   claude-pm template status --validation
   ```

3. **Manual Recovery**
   - Check backup directory: `.claude-pm/template_manager/backups/`
   - Review version registry: `.claude-pm/template_manager/registry/`
   - Restore from file system if needed

## Best Practices

### Template Organization

1. **Naming Conventions**
   - Use descriptive template IDs
   - Include technology stack in names
   - Use consistent naming patterns

2. **Version Management**
   - Create backups before major changes
   - Use semantic versioning principles
   - Document version changes

3. **Template Design**
   - Keep templates focused and specific
   - Use meaningful variable names
   - Include comprehensive documentation

### Deployment Considerations

1. **Source Management**
   - Use project templates for specific customizations
   - Keep user templates for personal preferences
   - Contribute useful templates to framework

2. **Conflict Resolution**
   - Use backup-and-replace for safety
   - Review conflicts before resolution
   - Test templates after updates

3. **Performance**
   - Limit template size
   - Use efficient variable substitution
   - Clean up old versions regularly

## Integration Points

### With CMPM-101

- **Deployment Detection**: Automatic deployment configuration
- **Path Resolution**: Deployment-aware template paths
- **Configuration Management**: Integrated configuration system

### With Agent System

- **Agent Templates**: Templates for creating new agents
- **Agent Customization**: Project-specific agent templates
- **Template Validation**: Agent-based template validation

### With CLI System

- **Command Integration**: Full CLI command support
- **Interactive Operations**: Interactive conflict resolution
- **Batch Operations**: Bulk template operations

## Monitoring and Maintenance

### Health Monitoring

- **Template Validation**: Regular template health checks
- **Backup Verification**: Verify backup integrity
- **Version Cleanup**: Automatic old version cleanup

### Maintenance Tasks

- **Backup Cleanup**: Remove old backups based on retention policy
- **Registry Optimization**: Optimize template registry files
- **Template Updates**: Keep framework templates current

## Future Enhancements

### Planned Features

1. **Template Sharing**: Share templates between users/projects
2. **Template Marketplace**: Central repository of templates
3. **Advanced Templating**: Jinja2 or similar templating engine
4. **Template Analytics**: Usage tracking and analytics
5. **Template Validation**: Enhanced validation rules
6. **Template Testing**: Automated template testing

### Extension Points

1. **Custom Validators**: Plugin-based validation system
2. **Template Transformers**: Content transformation plugins
3. **Deployment Integrations**: Additional deployment type support
4. **Storage Backends**: Alternative storage mechanisms

---

## API Reference

For detailed API documentation, see the inline documentation in:
- `claude_pm/services/template_manager.py`
- `claude_pm/services/template_deployment_integration.py`
- `claude_pm/commands/template_commands.py`

## Testing

Comprehensive tests are available in:
- `tests/test_template_manager.py`
- `tests/test_template_integration.py`

Run tests with:
```bash
pytest tests/test_template_manager.py -v
pytest tests/test_template_integration.py -v
```