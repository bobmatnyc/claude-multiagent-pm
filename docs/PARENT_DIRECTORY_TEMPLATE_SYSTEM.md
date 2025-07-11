# Parent Directory Template System - CMPM-104

## Overview

The Parent Directory Template System provides comprehensive parent directory management with deployment awareness, building on the foundations of CMPM-101 (Deployment Detection), CMPM-102 (Template Management), and CMPM-103 (Dependency Management).

## Key Features

### Core Capabilities
- **Parent Directory CLAUDE.md Management**: Automated installation, updates, and maintenance of CLAUDE.md files in parent directories
- **Deployment Awareness**: Integration with CMPM-101 for deployment-aware template sourcing and management
- **Template Installation Workflow**: Complete workflow for installing templates to parent directories with conflict resolution
- **Existing File Detection and Backup**: Comprehensive backup and restore system for safe operations
- **Version Control Integration**: Full integration with version control systems for template management
- **Cross-Platform Compatibility**: Works across all deployment scenarios (local source, npm global, deployed instances)

### Integration Architecture
- **CMPM-101 Integration**: Uses DeploymentDetector for deployment-aware path resolution
- **CMPM-102 Integration**: Leverages TemplateManager for template operations and versioning
- **CMPM-103 Integration**: Uses DependencyManager for dependency verification and deployment context

## Architecture

### Service Structure

```python
ParentDirectoryManager(BaseService)
├── Template Installation Workflow
├── Existing File Detection and Backup
├── Version Control Integration
├── Deployment Context Management
└── CMPM Integration Layer
```

### Core Components

#### 1. ParentDirectoryConfig
Configuration object for managing parent directories:
```python
@dataclass
class ParentDirectoryConfig:
    target_directory: Path
    context: ParentDirectoryContext
    template_id: str
    template_variables: Dict[str, Any]
    backup_enabled: bool
    version_control: bool
    conflict_resolution: str
    deployment_metadata: Dict[str, Any]
```

#### 2. ParentDirectoryStatus
Status information for parent directory files:
```python
@dataclass
class ParentDirectoryStatus:
    file_path: Path
    exists: bool
    is_managed: bool
    current_version: Optional[str]
    last_modified: Optional[datetime]
    checksum: Optional[str]
    backup_available: bool
    template_source: Optional[str]
    deployment_context: Optional[str]
```

#### 3. ParentDirectoryOperation
Result tracking for parent directory operations:
```python
@dataclass
class ParentDirectoryOperation:
    action: ParentDirectoryAction
    target_path: Path
    success: bool
    template_id: Optional[str]
    version: Optional[str]
    backup_path: Optional[Path]
    error_message: Optional[str]
    changes_made: List[str]
    warnings: List[str]
```

### Context Types

#### ParentDirectoryContext Enum
- **DEPLOYMENT_ROOT**: Directory containing a deployment (has claude-multiagent-pm subdirectory)
- **PROJECT_COLLECTION**: Directory containing multiple projects
- **WORKSPACE_ROOT**: Directory with workspace indicators (.vscode, .idea, etc.)
- **USER_HOME**: User home directory
- **CUSTOM**: Custom context for specific use cases

### Operations

#### ParentDirectoryAction Enum
- **INSTALL**: Install template to parent directory
- **UPDATE**: Update existing template
- **BACKUP**: Create backup of existing file
- **RESTORE**: Restore from backup
- **VALIDATE**: Validate template and configuration
- **REMOVE**: Remove managed template

## API Reference

### Core Methods

#### Registration and Management

```python
async def register_parent_directory(
    self,
    target_directory: Path,
    context: ParentDirectoryContext,
    template_id: str,
    template_variables: Dict[str, Any] = None,
    **kwargs
) -> bool
```
Register a parent directory for management with specified template and context.

```python
async def install_template_to_parent_directory(
    self,
    target_directory: Path,
    template_id: str,
    template_variables: Dict[str, Any] = None,
    force: bool = False
) -> ParentDirectoryOperation
```
Install a template to a parent directory with conflict resolution.

```python
async def update_parent_directory_template(
    self,
    target_directory: Path,
    template_variables: Dict[str, Any] = None,
    force: bool = False
) -> ParentDirectoryOperation
```
Update an existing template in a parent directory.

#### Status and Monitoring

```python
async def get_parent_directory_status(
    self,
    target_directory: Path
) -> ParentDirectoryStatus
```
Get comprehensive status information for a parent directory.

```python
async def list_managed_directories(self) -> List[Dict[str, Any]]
```
List all managed directories with their current status.

```python
async def get_operation_history(
    self,
    limit: int = 50
) -> List[Dict[str, Any]]
```
Get history of operations performed on parent directories.

#### Backup and Restore

```python
async def backup_parent_directory(
    self,
    target_directory: Path
) -> Optional[Path]
```
Create a backup of a parent directory's CLAUDE.md file.

```python
async def restore_parent_directory(
    self,
    target_directory: Path,
    backup_timestamp: Optional[str] = None
) -> ParentDirectoryOperation
```
Restore a parent directory from backup.

#### Validation

```python
async def validate_parent_directory(
    self,
    target_directory: Path
) -> ParentDirectoryOperation
```
Validate a parent directory's template and configuration.

#### Context Detection

```python
async def detect_parent_directory_context(
    self,
    target_directory: Path
) -> ParentDirectoryContext
```
Automatically detect the context type of a parent directory.

```python
async def auto_register_parent_directories(
    self,
    search_paths: List[Path],
    template_id: str = "parent_directory_claude_md"
) -> List[Path]
```
Automatically register parent directories that should be managed.

## Usage Examples

### Basic Usage

```python
from claude_pm.services.parent_directory_manager import (
    ParentDirectoryManager,
    ParentDirectoryContext
)

# Initialize manager
manager = ParentDirectoryManager()
await manager.initialize()

# Register a parent directory
target_dir = Path("/Users/masa/Projects")
await manager.register_parent_directory(
    target_dir,
    ParentDirectoryContext.PROJECT_COLLECTION,
    "parent_directory_claude_md",
    {
        "DIRECTORY_NAME": "Projects",
        "SHARED_TOOLS": "git, docker, node",
        "ACTIVE_PROJECTS": "5"
    }
)

# Install template
result = await manager.install_template_to_parent_directory(
    target_dir,
    "parent_directory_claude_md",
    {"PROJECT_COUNT": "8"}
)

print(f"Installation {'successful' if result.success else 'failed'}")
```

### Deployment-Aware Usage

```python
# Automatic context detection
context = await manager.detect_parent_directory_context(target_dir)
print(f"Detected context: {context}")

# Auto-register directories
search_paths = [
    Path("/Users/masa/Projects"),
    Path("/Users/masa/Workspace"),
    Path("/Users/masa/Development")
]

registered = await manager.auto_register_parent_directories(search_paths)
print(f"Auto-registered {len(registered)} directories")
```

### Backup and Restore Workflow

```python
# Create backup before making changes
backup_path = await manager.backup_parent_directory(target_dir)
print(f"Backup created: {backup_path}")

# Update template
result = await manager.update_parent_directory_template(
    target_dir,
    {"PROJECT_COUNT": "10"}
)

# Restore if needed
if not result.success:
    restore_result = await manager.restore_parent_directory(target_dir)
    print(f"Restore {'successful' if restore_result.success else 'failed'}")
```

### Status Monitoring

```python
# Get status of specific directory
status = await manager.get_parent_directory_status(target_dir)
print(f"Directory managed: {status.is_managed}")
print(f"File exists: {status.exists}")
print(f"Template source: {status.template_source}")

# List all managed directories
directories = await manager.list_managed_directories()
for dir_info in directories:
    print(f"Directory: {dir_info['directory']}")
    print(f"Context: {dir_info['context']}")
    print(f"Template: {dir_info['template_id']}")
```

## Template System

### Parent Directory Template

The system includes a comprehensive template for parent directories:
- Location: `framework/templates/projects/parent_directory_claude_md.template`
- Variables: Extensive variable support for customization
- Context-aware: Adapts based on directory context type

### Template Variables

Key template variables include:
- `{{DIRECTORY_NAME}}`: Name of the directory
- `{{DIRECTORY_PATH}}`: Full path to directory
- `{{CONTEXT}}`: Directory context type
- `{{PLATFORM}}`: Operating system platform
- `{{TIMESTAMP}}`: Creation timestamp
- `{{DEPLOYMENT_TYPE}}`: Type of deployment
- `{{SHARED_TOOLS}}`: Shared development tools
- `{{ACTIVE_PROJECTS}}`: Number of active projects

## Integration with CMPM Services

### CMPM-101 Integration (Deployment Detection)
- Uses deployment configuration for template sourcing
- Adapts behavior based on deployment type
- Provides deployment-aware path resolution

### CMPM-102 Integration (Template Management)
- Leverages template manager for all template operations
- Uses versioning and backup capabilities
- Benefits from conflict resolution strategies

### CMPM-103 Integration (Dependency Management)
- Uses deployment context from dependency manager
- Integrates with deployment health monitoring
- Leverages cross-platform compatibility

## Error Handling

### Comprehensive Error Handling
- **File System Errors**: Handles permission errors, missing files, etc.
- **Template Errors**: Validates templates and handles rendering failures
- **Backup Failures**: Graceful handling of backup creation and restoration issues
- **Integration Errors**: Handles failures in CMPM service integrations

### Recovery Mechanisms
- **Automatic Rollback**: Restores previous state on critical failures
- **Backup Recovery**: Uses backup system for data recovery
- **State Persistence**: Maintains configuration across service restarts
- **Health Monitoring**: Continuous health checking and issue detection

## Configuration

### Service Configuration

```python
config = {
    "backup_retention_days": 30,
    "auto_backup_enabled": True,
    "version_control_enabled": True,
    "deployment_aware": True
}

manager = ParentDirectoryManager(config)
```

### Directory Structure

```
.claude-pm/parent_directory_manager/
├── configs/
│   └── managed_directories.json
├── backups/
│   ├── CLAUDE.md_20250711_120000.backup
│   └── CLAUDE.md_20250711_130000.backup
├── versions/
│   └── template_versions/
├── logs/
│   └── operation_history.json
```

## Best Practices

### Template Management
1. **Use Context-Appropriate Templates**: Match templates to directory context
2. **Maintain Variable Consistency**: Use consistent variable naming across templates
3. **Regular Updates**: Keep templates updated with current project needs
4. **Backup Before Changes**: Always create backups before major updates

### Directory Management
1. **Auto-Detection**: Use context detection for automatic configuration
2. **Bulk Operations**: Use auto-registration for managing multiple directories
3. **Regular Validation**: Periodically validate all managed directories
4. **Monitor History**: Track operations for troubleshooting and auditing

### Integration
1. **Service Dependencies**: Ensure CMPM-101, 102, and 103 are properly initialized
2. **Deployment Awareness**: Leverage deployment context for optimal behavior
3. **Error Handling**: Implement proper error handling and recovery mechanisms
4. **Performance**: Monitor performance for large numbers of managed directories

## Testing

### Unit Tests
Comprehensive unit test suite covering:
- Service initialization and cleanup
- Directory registration and management
- Template installation and updates
- Backup and restore operations
- Status monitoring and validation
- Integration with CMPM services
- Error handling and recovery

### Test Coverage
- **Core Functionality**: 100% coverage of public API methods
- **Error Scenarios**: Comprehensive error condition testing
- **Integration**: Full integration testing with mock CMPM services
- **Cross-Platform**: Testing across different deployment scenarios

### Running Tests

```bash
# Run all parent directory manager tests
pytest tests/test_parent_directory_manager.py -v

# Run with coverage
pytest tests/test_parent_directory_manager.py --cov=claude_pm.services.parent_directory_manager

# Run integration tests
pytest tests/test_parent_directory_manager.py::TestParentDirectoryManager::test_integration_with_template_manager -v
```

## Troubleshooting

### Common Issues

#### Template Not Found
```python
# Check template availability
template_data = await manager.template_manager.get_template("parent_directory_claude_md")
if not template_data:
    print("Template not found - check template manager configuration")
```

#### Permission Errors
```python
# Check directory permissions
if not target_dir.exists():
    print("Target directory does not exist")
elif not os.access(target_dir, os.W_OK):
    print("Target directory is not writable")
```

#### Backup Failures
```python
# Check backup directory
if not manager.backups_dir.exists():
    print("Backup directory not available")
elif not os.access(manager.backups_dir, os.W_OK):
    print("Backup directory is not writable")
```

### Debug Information

Enable debug logging for detailed operation information:

```python
import logging
logging.getLogger('claude_pm.services.parent_directory_manager').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Git Integration**: Direct integration with version control systems
2. **Template Inheritance**: Support for template inheritance and composition
3. **Remote Templates**: Support for remote template repositories
4. **Workflow Automation**: Automated workflows for common operations
5. **Performance Optimization**: Optimization for large-scale directory management

### Extension Points
1. **Custom Context Types**: Support for custom directory context types
2. **Plugin System**: Plugin architecture for extending functionality
3. **Custom Templates**: Support for user-defined custom templates
4. **Integration APIs**: APIs for integration with external systems

---

*This documentation is part of the Claude PM Framework CMPM-104 implementation.*
*For more information, see the complete CMPM documentation.*