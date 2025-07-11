# Dependency Management System

**CMPM-103: Dependency Management Strategy**

## Overview

The Claude PM Framework includes a comprehensive dependency management system that provides deployment-aware dependency resolution, installation automation, and health monitoring. This system integrates with the CMPM-101 Deployment Detection system to provide context-aware dependency management across all deployment scenarios.

## Core Features

### 1. Deployment-Aware Dependency Resolution
- Automatic detection of deployment context (local source, npm global, deployed instance, etc.)
- Context-specific dependency strategies
- Integration with DeploymentDetector for enhanced compatibility

### 2. ai-trackdown-tools Integration
- Automated installation and verification of ai-trackdown-tools
- Support for multiple installation methods (npm global, npm local, npx, source)
- Functionality verification with command testing

### 3. Python Package Management
- Automatic Python package detection and verification
- Integration with pip for package installation
- Requirements file parsing and dependency tracking

### 4. Cross-Platform Compatibility
- Support for macOS, Linux, and Windows
- Platform-specific installation strategies
- Automatic command detection (python3 vs python, etc.)

### 5. Health Monitoring
- Comprehensive health checks for all dependencies
- Real-time dependency status monitoring
- Health score calculation and reporting

## Architecture

### Core Components

#### DependencyManager
The main service class that orchestrates all dependency operations:

```python
from claude_pm.services.dependency_manager import DependencyManager

# Initialize dependency manager
dependency_manager = DependencyManager()
await dependency_manager._initialize()

# Check dependencies
dependencies = dependency_manager.get_dependencies()

# Install missing dependencies
result = await dependency_manager.install_dependency("ai-trackdown-tools")

# Generate comprehensive report
report = await dependency_manager.generate_dependency_report()
```

#### DependencyType Enumeration
Defines the types of dependencies managed by the system:

- `PYTHON_PACKAGE`: Python packages installed via pip
- `NPM_GLOBAL`: npm packages installed globally
- `NPM_LOCAL`: npm packages installed locally
- `SYSTEM_BINARY`: System binaries (python, node, git, etc.)
- `AI_TRACKDOWN_TOOLS`: Special handling for ai-trackdown-tools

#### InstallationMethod Enumeration
Defines available installation methods:

- `NPM_GLOBAL`: Global npm installation
- `NPM_LOCAL`: Local npm installation
- `NPX`: NPX execution (no installation)
- `SOURCE`: Source-based installation
- `PIP`: Python pip installation
- `SYSTEM`: System package manager

### Data Models

#### DependencyInfo
Comprehensive information about a dependency:

```python
@dataclass
class DependencyInfo:
    name: str
    type: DependencyType
    version: Optional[str] = None
    required_version: Optional[str] = None
    is_installed: bool = False
    installation_path: Optional[str] = None
    installation_method: Optional[InstallationMethod] = None
    last_checked: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

#### InstallationResult
Result of dependency installation operations:

```python
@dataclass
class InstallationResult:
    success: bool
    dependency_name: str
    method: InstallationMethod
    version: Optional[str] = None
    installation_path: Optional[str] = None
    error_message: Optional[str] = None
    logs: Optional[List[str]] = None
```

#### DependencyReport
Comprehensive dependency status report:

```python
@dataclass
class DependencyReport:
    deployment_type: str
    platform: str
    timestamp: str
    dependencies: Dict[str, DependencyInfo]
    missing_dependencies: List[str]
    outdated_dependencies: List[str]
    installation_recommendations: List[str]
    health_score: int
```

## Core Dependencies

The system manages these core dependencies:

### ai-trackdown-tools
- **Type**: AI_TRACKDOWN_TOOLS
- **NPM Package**: `@bobmatnyc/ai-trackdown-tools`
- **Required Version**: `>=1.1.0`
- **Commands**: `aitrackdown`, `atd`
- **Critical**: Yes

### python
- **Type**: SYSTEM_BINARY
- **Commands**: `python3`, `python`
- **Required Version**: `>=3.8.0`
- **Critical**: Yes

### node
- **Type**: SYSTEM_BINARY
- **Commands**: `node`
- **Required Version**: `>=16.0.0`
- **Critical**: Yes

### npm
- **Type**: SYSTEM_BINARY
- **Commands**: `npm`
- **Required Version**: `>=8.0.0`
- **Critical**: Yes

### git
- **Type**: SYSTEM_BINARY
- **Commands**: `git`
- **Required Version**: `>=2.0.0`
- **Critical**: Yes

## CLI Interface

### Basic Usage

```bash
# Show dependency status
claude-pm dependency status

# Check all dependencies
claude-pm dependency check

# Install a dependency
claude-pm dependency install ai-trackdown-tools

# Verify installation
claude-pm dependency verify ai-trackdown-tools

# Generate report
claude-pm dependency report

# Check health
claude-pm dependency health
```

### Advanced Usage

```bash
# Show status in JSON format
claude-pm dependency status --format json

# Show only missing dependencies
claude-pm dependency status --missing-only

# Force refresh dependencies
claude-pm dependency check --refresh --verbose

# Install with specific method
claude-pm dependency install ai-trackdown-tools --method npm_global

# Dry run installation
claude-pm dependency install ai-trackdown-tools --dry-run

# Verify all dependencies
claude-pm dependency verify --all

# Generate detailed report
claude-pm dependency report --format detailed --output report.json

# Check health with details
claude-pm dependency health --detailed

# AI-Trackdown-Tools specific operations
claude-pm dependency ai-trackdown --status
claude-pm dependency ai-trackdown --install
claude-pm dependency ai-trackdown --verify
```

## Integration with Deployment Detection

The dependency management system integrates seamlessly with the CMPM-101 Deployment Detection system:

### Deployment-Specific Strategies

#### Local Source Development
- Checks requirements files in the source repository
- Validates development dependencies
- Supports source-based ai-trackdown-tools installation

#### NPM Global Installation
- Verifies global npm environment
- Checks global package installations
- Manages npm global dependencies

#### Deployed Instance
- Reads deployed configuration
- Validates deployed dependencies
- Supports deployment-specific package management

### Configuration Integration

The dependency manager automatically detects and integrates with the deployment configuration:

```python
# Automatic deployment integration
await dependency_manager._initialize_deployment_integration()

# Access deployment configuration
deployment_config = dependency_manager.deployment_config
deployment_type = deployment_config.get("config", {}).get("deploymentType")
```

## Installation Strategies

### ai-trackdown-tools Installation

The system supports multiple installation methods for ai-trackdown-tools:

#### NPM Global (Recommended)
```bash
npm install -g @bobmatnyc/ai-trackdown-tools
```

#### NPM Local
```bash
npm install @bobmatnyc/ai-trackdown-tools
```

#### NPX (No Installation)
```bash
npx @bobmatnyc/ai-trackdown-tools
```

#### Source Installation
For development environments with source access.

### Python Package Installation

Automatic detection and installation of Python packages:

```python
# Install Python package
result = await dependency_manager.install_dependency("pydantic")

# Verify installation
dependency_info = dependency_manager.get_dependency("pydantic")
```

### System Binary Verification

Automatic detection of system binaries:

- Python (python3, python)
- Node.js (node)
- npm (npm)
- Git (git)

## Health Monitoring

### Health Checks

The system performs comprehensive health checks:

- **python_available**: Python interpreter availability
- **node_available**: Node.js runtime availability
- **npm_available**: npm package manager availability
- **git_available**: Git version control availability
- **ai_trackdown_tools_available**: ai-trackdown-tools functionality
- **deployment_detector_available**: Deployment detection integration
- **deployment_config_valid**: Deployment configuration validity
- **dependencies_tracked**: Dependency tracking status
- **critical_dependencies_met**: Critical dependency satisfaction

### Health Score Calculation

Health score is calculated as:
```
Health Score = (Passed Checks / Total Checks) × 100
```

### Continuous Monitoring

Background monitoring task that:
- Periodically checks all dependencies
- Updates dependency status
- Detects changes in installation status
- Maintains health metrics

## Error Handling and Recovery

### Installation Failures

The system provides comprehensive error handling:

```python
result = await dependency_manager.install_dependency("package-name")
if not result.success:
    print(f"Installation failed: {result.error_message}")
    if result.logs:
        print("Installation logs:", result.logs)
```

### Dependency Verification

Failed dependencies are handled gracefully:

```python
# Verify ai-trackdown-tools functionality
is_functional = await dependency_manager.verify_ai_trackdown_tools()
if not is_functional:
    # Handle non-functional installation
    recommendations = await dependency_manager.get_installation_recommendations()
```

### Recovery Strategies

Automatic recovery strategies:
- Retry installation with different methods
- Fallback to alternative installation approaches
- Provide detailed error reporting and recommendations

## Configuration

### Service Configuration

```python
config = {
    "check_interval": 1800,  # 30 minutes
    "auto_install": True,
    "installation_timeout": 300,  # 5 minutes
    "enable_dependency_monitoring": True
}

dependency_manager = DependencyManager(config)
```

### Environment Variables

Supported environment variables:
- `CLAUDE_PM_FRAMEWORK_PATH`: Framework installation path
- `CLAUDE_PM_DEPENDENCY_AUTO_INSTALL`: Enable/disable auto-installation
- `CLAUDE_PM_DEPENDENCY_TIMEOUT`: Installation timeout

## Testing

### Unit Tests

Comprehensive unit test suite:

```bash
# Run dependency manager tests
python -m pytest tests/test_dependency_manager.py

# Run with coverage
python -m pytest tests/test_dependency_manager.py --cov=claude_pm.services.dependency_manager
```

### Integration Tests

Integration tests verify:
- Deployment detection integration
- Cross-platform compatibility
- Real dependency installation
- Health monitoring accuracy

### Demo Script

Interactive demonstration:

```bash
# Run dependency integration demo
python scripts/dependency_integration_demo.py
```

## Best Practices

### Dependency Management

1. **Regular Health Checks**: Monitor dependency health regularly
2. **Automated Installation**: Use auto-installation for critical dependencies
3. **Version Pinning**: Specify required versions for stability
4. **Deployment Awareness**: Leverage deployment-specific strategies
5. **Error Handling**: Implement robust error handling and recovery

### Performance Optimization

1. **Caching**: Cache dependency information to reduce check frequency
2. **Parallel Checks**: Perform dependency checks in parallel when possible
3. **Selective Monitoring**: Focus monitoring on critical dependencies
4. **Batch Operations**: Group related operations for efficiency

### Security Considerations

1. **Trusted Sources**: Only install from trusted package repositories
2. **Version Validation**: Validate package versions before installation
3. **Permission Checking**: Verify installation permissions
4. **Audit Logging**: Log all dependency operations for audit trails

## Troubleshooting

### Common Issues

#### ai-trackdown-tools Not Found
```bash
# Check installation
claude-pm dependency ai-trackdown --status

# Install if missing
claude-pm dependency ai-trackdown --install

# Verify functionality
claude-pm dependency ai-trackdown --verify
```

#### Python Version Issues
```bash
# Check Python availability
claude-pm dependency verify python

# Check system Python installations
which python3
python3 --version
```

#### NPM Global Path Issues
```bash
# Check npm global path
npm root -g

# Verify npm global installation
npm list -g @bobmatnyc/ai-trackdown-tools
```

### Debug Information

Enable verbose logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

dependency_manager = DependencyManager()
await dependency_manager._initialize()
```

### Support Resources

- **GitHub Issues**: Report issues and request features
- **Documentation**: Comprehensive documentation and examples
- **Community**: Community support and discussions
- **Professional Support**: Enterprise support available

## Future Enhancements

### Planned Features

1. **Package Manager Integration**: Direct integration with system package managers
2. **Dependency Graphs**: Visual dependency relationship mapping
3. **Automated Updates**: Automatic dependency updates with compatibility checking
4. **Security Scanning**: Vulnerability scanning for dependencies
5. **Performance Metrics**: Detailed performance metrics and optimization suggestions

### Extensibility

The system is designed for extensibility:

- **Custom Dependency Types**: Add new dependency types
- **Installation Methods**: Implement custom installation methods
- **Health Checks**: Add custom health check implementations
- **Reporting Formats**: Create custom report formats
- **Integration Points**: Add integration with external systems

## Conclusion

The Claude PM Framework Dependency Management System provides a comprehensive, deployment-aware solution for managing dependencies across all deployment scenarios. With its tight integration with the deployment detection system, automated installation capabilities, and comprehensive health monitoring, it ensures reliable dependency management for the Claude PM Framework ecosystem.

The system's architecture promotes maintainability, extensibility, and reliability while providing a rich CLI interface for both automated and manual dependency management operations. Whether you're developing locally, deploying to production, or managing a complex multi-deployment environment, the dependency management system provides the tools and automation needed for successful dependency management.