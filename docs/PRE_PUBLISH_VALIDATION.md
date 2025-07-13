# Pre-Publish Docker Validation Integration

## Overview

The claude-multiagent-pm framework now includes comprehensive pre-publish validation that automatically runs before any `npm publish` operation. This ensures package quality and prevents deployment of broken versions.

## Integration Components

### 1. npm Lifecycle Hook
- **`prepublishOnly`**: Automatically runs before `npm publish`
- **Script**: `npm run pre-publish:validation`
- **Behavior**: Runs comprehensive validation including Docker tests when available

### 2. Validation Scripts

#### Comprehensive Validation (`scripts/comprehensive-pre-publish-validation.js`)
- **Purpose**: Orchestrates all validation stages with intelligent fallback
- **Features**:
  - Standard validation (npm test, deployment validation)
  - Docker validation (when Docker is available)
  - Integration testing (framework structure, CLI wrappers)
  - Graceful fallback when Docker is unavailable

#### Docker Validation System
- **Main Script**: `scripts/pre-publish-docker-validation.js`
- **Helper**: `scripts/docker-validation-helper.sh`
- **Features**:
  - Isolated container testing
  - Package build and installation tests
  - Service integration testing
  - Comprehensive health checks

### 3. Available npm Scripts

```bash
# Automatic validation (runs before npm publish)
npm run prepublishOnly

# Manual validation options
npm run pre-publish:validation        # Comprehensive with Docker if available
npm run pre-publish:comprehensive     # Verbose comprehensive validation
npm run pre-publish:no-docker        # Skip Docker validation
npm run pre-publish:standard          # Basic validation only

# Docker-specific validation
npm run docker:validate              # Full Docker validation
npm run docker:quick-test            # Quick Docker environment test
npm run docker:validate:verbose      # Verbose Docker validation
npm run docker:validate:dry-run      # Dry run Docker validation

# Legacy Docker scripts
npm run pre-publish:full             # Original Docker workflow
npm run pre-publish:quick            # Quick validation
```

## Validation Stages

### 1. Standard Validation (Required)
- **npm test**: Runs test suite via `node install/validate.js --verbose`
- **Deployment validation**: Runs `npm run validate-deployment`
- **Health check**: Optional health check script execution
- **Status**: Must pass for overall validation success

### 2. Docker Validation (Optional)
- **Availability check**: Tests if Docker daemon is running
- **Quick test**: Basic Docker operations (pull, run, network)
- **Full validation**: Comprehensive container-based testing
- **Fallback**: Gracefully skipped if Docker unavailable
- **Status**: Failures generate warnings but don't block publish

### 3. Integration Testing (Required)
- **Script integrity**: Validates required npm scripts are present
- **CLI wrapper**: Checks executable permissions on CLI scripts
- **Framework structure**: Validates critical directories exist
- **Status**: Must pass for overall validation success

## Docker Validation Features

### Environment Isolation
- **Clean environment**: Each test runs in isolated containers
- **Package testing**: Tests actual npm package installation
- **Service integration**: Validates framework services work in containers
- **Resource cleanup**: Automatic cleanup of test resources

### Validation Stages
1. **Docker availability**: Checks Docker daemon and basic functionality
2. **Build environment**: Creates validation Docker image
3. **Package build**: Tests npm pack and installation in container
4. **Functionality test**: Tests core framework imports and CLI
5. **Health check**: Runs comprehensive health validation
6. **Service integration**: Tests service startup and health monitoring
7. **Cleanup**: Removes test containers, networks, and volumes

### Intelligent Fallback
- **No Docker**: Runs standard validation only
- **Docker errors**: Logs warnings but continues with standard validation
- **Build failures**: Attempts recovery or graceful degradation
- **Timeout handling**: Prevents hanging on long-running operations

## Usage Examples

### Basic Usage
```bash
# Automatic validation before publish
npm publish

# Manual comprehensive validation
npm run pre-publish:validation
```

### Development Workflow
```bash
# Quick validation during development
npm run pre-publish:no-docker

# Full validation with Docker
npm run pre-publish:comprehensive

# Docker-only testing
npm run docker:validate:verbose
```

### CI/CD Integration
```bash
# In CI environments with Docker
npm run pre-publish:validation

# In CI environments without Docker
npm run pre-publish:no-docker

# For debugging CI issues
npm run pre-publish:validation --json > validation-report.json
```

## Configuration Options

### Command Line Options
- `--verbose, -v`: Enable detailed output
- `--dry-run`: Show commands without executing
- `--skip-docker`: Skip Docker validation entirely
- `--json`: Output results in JSON format
- `--project, -p <path>`: Specify project root directory

### Environment Variables
- `DOCKER_VALIDATION_TIMEOUT`: Override default timeouts
- `SKIP_DOCKER_VALIDATION`: Skip Docker validation (same as --skip-docker)

## Validation Reports

### Report Generation
- **Location**: `logs/comprehensive-validation-{timestamp}.json`
- **Format**: Structured JSON with detailed results
- **Content**: Stage results, errors, warnings, timing information

### Report Structure
```json
{
  "timestamp": "2025-07-13T20:17:18.041Z",
  "overall": { "passed": true, "errors": [], "warnings": [] },
  "stages": {
    "standard": { "completed": true, "passed": true, "details": {} },
    "docker": { "completed": true, "passed": true, "skipped": false, "details": {} },
    "integration": { "completed": true, "passed": true, "details": {} }
  },
  "summary": {
    "totalStages": 3,
    "completedStages": 3,
    "passedStages": 3,
    "totalErrors": 0,
    "totalWarnings": 0,
    "overallSuccess": true,
    "dockerAvailable": true
  }
}
```

## Troubleshooting

### Common Issues

#### Docker Not Available
```bash
# Solution: Use no-docker validation
npm run pre-publish:no-docker
```

#### Docker Build Failures
```bash
# Check Docker environment
npm run docker:status

# Clean Docker resources
npm run docker:clean

# Rebuild environment
npm run docker:build-env --force
```

#### Validation Timeouts
```bash
# Use verbose mode for debugging
npm run pre-publish:comprehensive

# Check specific stages
npm run docker:debug
```

### Debug Information
```bash
# Comprehensive debug information
npm run docker:debug --json

# Validation logs
ls -la logs/comprehensive-validation-*.json

# Docker validation status
npm run docker:status
```

## Best Practices

### Development Workflow
1. **Regular validation**: Run `npm run pre-publish:no-docker` during development
2. **Pre-commit**: Run full validation before committing major changes
3. **Release preparation**: Always run `npm run pre-publish:comprehensive`

### CI/CD Integration
1. **Early validation**: Run validation in early CI stages
2. **Parallel testing**: Run Docker and standard validation in parallel when possible
3. **Artifact storage**: Save validation reports as CI artifacts

### Docker Usage
1. **Clean environment**: Run `npm run docker:clean` regularly
2. **Resource monitoring**: Use `npm run docker:status` to check resource usage
3. **Debug mode**: Use verbose flags when troubleshooting

## Migration Notes

### From Previous Versions
- **Legacy scripts**: Old `pre-publish:full` scripts still work
- **Backward compatibility**: All existing workflows remain functional
- **New features**: New comprehensive validation provides better error handling

### Configuration Updates
- **package.json**: Updated with new `prepublishOnly` hook
- **Scripts**: Added comprehensive validation scripts
- **Dependencies**: No new dependencies required

## Future Enhancements

### Planned Features
1. **Parallel validation**: Run Docker and standard validation simultaneously
2. **Custom validation**: Plugin system for project-specific validation
3. **Performance metrics**: Detailed timing and performance analysis
4. **Integration testing**: Extended integration with external services

### Performance Optimizations
1. **Caching**: Docker image caching for faster builds
2. **Incremental testing**: Skip unchanged validation stages
3. **Resource optimization**: Better resource cleanup and management

---

**Integration completed**: 2025-07-13  
**Framework version**: 0.6.0  
**Docker validation**: Fully integrated with graceful fallback