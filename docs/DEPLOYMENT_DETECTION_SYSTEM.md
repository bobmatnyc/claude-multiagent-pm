# Claude PM Framework - Deployment Detection System

## Overview

The Claude PM Framework Deployment Detection System (CMPM-101) provides comprehensive detection and resolution of all deployment scenarios for the Claude PM Framework. This system ensures that the framework can be executed correctly regardless of how it was installed or deployed.

## Architecture

### Core Components

#### 1. DeploymentDetector Class
- **Location**: `bin/claude-pm`
- **Purpose**: Detect and classify deployment scenarios
- **Features**:
  - Multi-strategy detection algorithm
  - Caching mechanism for performance
  - Cross-platform compatibility
  - Confidence scoring

#### 2. Detection Strategies

The system implements seven detection strategies in order of precedence:

1. **Local Source Development**
   - Detects framework development environment
   - Identifies source repository structure
   - Validates package.json authenticity

2. **NPM Global Installation**
   - Detects global npm installations
   - Locates framework in global node_modules
   - Validates installation integrity

3. **NPX Execution**
   - Detects npx-based execution
   - Finds framework in npx cache
   - Handles temporary installations

4. **NPM Local Installation**
   - Detects local project installations
   - Searches node_modules hierarchy
   - Identifies project root context

5. **Deployed Instance**
   - Detects deployed framework instances
   - Reads deployment configuration
   - Validates deployment structure

6. **Environment-based Detection**
   - Uses environment variables
   - Supports legacy variable names
   - Provides configuration override

7. **Fallback Detection**
   - Searches common installation paths
   - Provides last-resort detection
   - Maintains system compatibility

#### 3. Configuration Object

Each detection results in a standardized configuration object:

```javascript
{
  deploymentType: 'local_source' | 'npm_global' | 'npx' | 'npm_local' | 'deployed' | 'environment' | 'fallback' | 'not_found',
  found: boolean,
  platform: 'win32' | 'darwin' | 'linux',
  detectedAt: string, // ISO timestamp
  confidence: 'high' | 'medium' | 'low' | 'unknown',
  frameworkPath: string,
  claudePmPath: string,
  paths: {
    framework: string,
    claudePm: string,
    bin: string,
    config: string,
    templates: string,
    schemas: string
  },
  metadata: object // Type-specific metadata
}
```

## Detection Algorithms

### Local Source Development Detection

```javascript
_detectLocalSource() {
  // Check if we're in the source repository
  const sourceRoot = path.join(__dirname, '..');
  const claudePmPath = path.join(sourceRoot, 'claude_pm');
  const packageJsonPath = path.join(sourceRoot, 'package.json');
  
  if (fs.existsSync(claudePmPath) && fs.existsSync(packageJsonPath)) {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    if (packageJson.name === '@bobmatnyc/claude-multiagent-pm') {
      return {
        found: true,
        frameworkPath: sourceRoot,
        claudePmPath: claudePmPath,
        packageJson: packageJson,
        confidence: 'high'
      };
    }
  }
  
  return { found: false };
}
```

### NPM Global Installation Detection

```javascript
_detectNpmGlobal() {
  // Find global npm installation
  const globalPath = execSync('npm root -g', { encoding: 'utf8' }).trim();
  const globalClaudePm = path.join(globalPath, '@bobmatnyc', 'claude-multiagent-pm');
  const globalFrameworkPath = path.join(globalClaudePm, 'claude_pm');
  
  if (fs.existsSync(globalFrameworkPath)) {
    return {
      found: true,
      frameworkPath: globalClaudePm,
      claudePmPath: globalFrameworkPath,
      globalPath: globalPath,
      confidence: 'high'
    };
  }
  
  return { found: false };
}
```

### Deployed Instance Detection

```javascript
_detectDeployedInstance() {
  // Check for deployed configuration
  const deployedConfigPath = path.join(process.cwd(), '.claude-pm', 'config.json');
  const deployedClaudePmPath = path.join(process.cwd(), 'claude_pm');
  
  if (fs.existsSync(deployedConfigPath) && fs.existsSync(deployedClaudePmPath)) {
    const deployedConfig = JSON.parse(fs.readFileSync(deployedConfigPath, 'utf8'));
    
    return {
      found: true,
      frameworkPath: process.cwd(),
      claudePmPath: deployedClaudePmPath,
      deployedConfig: deployedConfig,
      confidence: 'high'
    };
  }
  
  return { found: false };
}
```

## Usage

### Basic Usage

```javascript
const { DeploymentDetector } = require('./bin/claude-pm');

const detector = new DeploymentDetector();
const config = detector.detectDeployment();

if (config.found) {
  console.log(`Framework found at: ${config.frameworkPath}`);
  console.log(`Deployment type: ${config.deploymentType}`);
  console.log(`Confidence: ${config.confidence}`);
} else {
  console.log('Framework not found');
}
```

### Advanced Usage

```javascript
const { getDeploymentConfig } = require('./bin/claude-pm');

const deploymentStrategy = getDeploymentConfig();

if (deploymentStrategy.strategy !== 'install_required') {
  // Use the deployment strategy
  const env = {
    ...process.env,
    ...deploymentStrategy.environmentSetup
  };
  
  // Execute framework with proper environment
  spawn('python3', ['-m', 'claude_pm.cli'], {
    env: env,
    cwd: deploymentStrategy.config.frameworkPath
  });
}
```

### CLI Integration

The deployment detection system is integrated into the main CLI:

```bash
# Show deployment information
claude-pm --deployment-info

# Normal usage (detection happens automatically)
claude-pm health status
```

## Configuration

### Environment Variables

The system recognizes several environment variables:

- `CLAUDE_MULTIAGENT_PM_ROOT`: Primary framework root path
- `CLAUDE_PM_ROOT`: Legacy framework root path (deprecated)
- `CLAUDE_PM_FRAMEWORK_PATH`: Direct framework path override

### Deployment Configuration

Deployed instances include a configuration file at `.claude-pm/config.json`:

```json
{
  "version": "4.5.1",
  "deployedAt": "2025-07-11T00:00:00.000Z",
  "platform": "darwin",
  "deploymentDir": "/path/to/deployment",
  "pythonCmd": "python3",
  "aiTrackdownPath": "/path/to/ai-trackdown-tools",
  "paths": {
    "framework": "/path/to/deployment/claude_pm",
    "templates": "/path/to/deployment/templates",
    "schemas": "/path/to/deployment/schemas",
    "tasks": "/path/to/deployment/tasks",
    "bin": "/path/to/deployment/bin",
    "config": "/path/to/deployment/.claude-pm"
  },
  "features": {
    "aiTrackdownIntegration": true,
    "memoryIntegration": true,
    "multiAgentSupport": true,
    "portableDeployment": true
  }
}
```

## Error Handling

### Detection Failures

When no deployment is found, the system provides helpful error messages:

```bash
❌ Claude PM Framework not found
Please install the framework:
   npm install -g @bobmatnyc/claude-multiagent-pm

Detected deployment scenarios:
- No valid framework installation found
- Checked: local source, npm global, npx, npm local, deployed instances
```

### Diagnostic Information

Use the `--deployment-info` flag to get detailed diagnostic information:

```bash
claude-pm --deployment-info
```

This provides:
- Detection results for all strategies
- Path information
- Configuration details
- Confidence scores
- Error messages (if any)

## Performance Considerations

### Caching

The system implements intelligent caching:
- Detection results are cached per execution context
- Cache keys include working directory and binary location
- Cache prevents redundant file system operations

### Optimization

Detection strategies are ordered by:
1. **Reliability**: Most reliable methods first
2. **Performance**: Fastest methods prioritized
3. **Common Usage**: Most common scenarios first

## Cross-Platform Support

### Platform Detection

The system automatically detects the platform:
- Windows (`win32`)
- macOS (`darwin`)
- Linux (`linux`)

### Path Handling

Platform-specific path handling:
- Windows: Backslash separators, case-insensitive
- Unix-like: Forward slash separators, case-sensitive

### Script Extensions

Appropriate script extensions for each platform:
- Windows: `.bat` files
- Unix-like: `.sh` files

## Testing

### Unit Tests

Comprehensive unit tests are provided:

```bash
# Run deployment detection tests
node tests/test_deployment_detection.js
```

### Test Coverage

Tests cover:
- All detection strategies
- Configuration object validation
- Error handling
- Cross-platform compatibility
- Performance characteristics
- Caching mechanism

### Test Report

Tests generate a detailed report:
- Test results summary
- Platform compatibility
- Performance metrics
- Detailed error information

## Integration Points

### CLI Integration

The deployment detection system is fully integrated with the main CLI:

```javascript
// Enhanced main execution function
function main() {
  const deploymentStrategy = deploymentDetector.getDeploymentStrategy();
  
  if (deploymentStrategy.strategy === 'install_required') {
    // Handle missing framework
    process.exit(1);
  }
  
  // Execute with proper environment
  const enhancedEnv = {
    ...process.env,
    ...deploymentStrategy.environmentSetup
  };
  
  spawn(pythonCmd, ['-m', 'claude_pm.cli', ...args], {
    env: enhancedEnv,
    cwd: deploymentStrategy.config.frameworkPath
  });
}
```

### Python Integration

The Python configuration system can access deployment information:

```python
import os
deployment_type = os.getenv('CLAUDE_PM_DEPLOYMENT_TYPE')
deployment_confidence = os.getenv('CLAUDE_PM_DEPLOYMENT_CONFIDENCE')
```

## Best Practices

### Development

1. **Use Local Source**: Develop using the local source detection
2. **Test All Scenarios**: Test with different deployment types
3. **Validate Paths**: Always validate detected paths before use

### Deployment

1. **Use Deployed Instances**: Create proper deployed instances for production
2. **Configure Environment**: Set appropriate environment variables
3. **Validate Installation**: Use health checks to verify deployment

### Troubleshooting

1. **Check Deployment Info**: Use `--deployment-info` for diagnostics
2. **Verify Paths**: Ensure all paths are accessible
3. **Check Permissions**: Verify file and directory permissions

## Future Enhancements

### Planned Features

1. **Remote Detection**: Support for remote framework instances
2. **Version Validation**: Detect and validate framework versions
3. **Automatic Updates**: Detect and suggest framework updates
4. **Configuration Validation**: Validate deployment configurations

### Performance Improvements

1. **Async Detection**: Asynchronous detection algorithms
2. **Parallel Strategies**: Parallel execution of detection strategies
3. **Smart Caching**: More intelligent caching strategies

## Conclusion

The Claude PM Framework Deployment Detection System provides a robust, comprehensive solution for detecting and configuring framework deployments across all supported scenarios. Its multi-strategy approach, intelligent caching, and cross-platform compatibility ensure reliable framework execution regardless of installation method.

The system's integration with the main CLI and Python configuration system provides seamless operation while maintaining detailed diagnostic capabilities for troubleshooting and optimization.