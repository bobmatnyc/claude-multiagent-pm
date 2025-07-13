# Docker-Based Pre-Publish Validation System

## Overview

The Docker-based pre-publish validation system provides comprehensive clean environment testing for the Claude Multi-Agent PM Framework before npm publish operations. This system ensures package reliability by testing in isolated Docker containers that mirror production deployment environments.

**DevOps Agent Implementation - 2025-07-13**

## Architecture

### Core Components

1. **Pre-Publish Validation Script** (`scripts/pre-publish-docker-validation.js`)
   - Main validation orchestrator
   - Comprehensive testing pipeline
   - Clean environment validation
   - Automated resource management

2. **Docker Validation Helper** (`scripts/docker-validation-helper.sh`)
   - Command-line interface for validation operations
   - Docker resource management utilities
   - Quick testing and debugging tools

3. **Validation Configuration** (`config/docker-validation-config.json`)
   - Centralized configuration management
   - Timeout and retry settings
   - Stage configuration and thresholds

4. **Existing Docker Infrastructure**
   - Leverages `deployment/docker/Dockerfile`
   - Uses `docker-compose.yml` configuration
   - Integrates with health monitoring systems

## Validation Stages

### 1. Docker Availability Check
- Verifies Docker daemon is running
- Checks Docker and Docker Compose versions
- Validates Docker connectivity and permissions

### 2. Build Validation Environment
- Builds testing Docker image using existing Dockerfile
- Creates isolated test network and volumes
- Sets up resource constraints and security settings

### 3. Package Build Testing
- Creates npm package tarball (`npm pack`)
- Tests installation in clean container environment
- Validates CLI commands and Python imports
- Ensures package integrity and completeness

### 4. Functionality Testing
- Tests core framework functionality
- Validates Python module imports
- Checks configuration system
- Tests agent loading and basic operations

### 5. Health Check Validation
- Runs comprehensive health validation script
- Tests service startup and integration
- Validates health monitoring endpoints
- Checks service logs for errors

### 6. Service Integration Testing
- Starts framework services in containers
- Tests inter-service communication
- Validates API endpoints and dashboard
- Checks mem0AI integration (if configured)

### 7. Resource Cleanup
- Stops and removes test containers
- Cleans up Docker networks and volumes
- Removes temporary resources
- Provides cleanup status and error reporting

## Usage Guide

### Quick Start

```bash
# Quick Docker environment test
npm run docker:quick-test

# Full pre-publish validation
npm run pre-publish

# Verbose validation with detailed output
npm run pre-publish:full
```

### Advanced Usage

```bash
# Build validation environment only
npm run docker:build-env

# Run validation with dry-run mode
npm run docker:validate:dry-run

# Check Docker validation status
npm run docker:status

# Clean up Docker resources
npm run docker:clean

# Debug Docker validation issues
npm run docker:debug
```

### Direct Script Usage

```bash
# Direct validation script usage
node scripts/pre-publish-docker-validation.js --verbose

# Helper script usage
./scripts/docker-validation-helper.sh validate --verbose
./scripts/docker-validation-helper.sh pre-publish
./scripts/docker-validation-helper.sh clean --force
```

## Configuration

### Docker Configuration

The validation system uses the following Docker configuration:

```json
{
  "docker": {
    "imageConfig": {
      "baseTag": "claude-pm-validation",
      "target": "testing",
      "buildArgs": {
        "BUILD_DATE": "${BUILD_DATE}",
        "VCS_REF": "${VCS_REF}",
        "CLAUDE_PM_VERSION": "${PACKAGE_VERSION}"
      }
    },
    "containerConfig": {
      "namePrefix": "claude-pm-val",
      "networkName": "claude-pm-test-net",
      "volumeName": "claude-pm-test-vol",
      "resourceLimits": {
        "memory": "512m",
        "cpus": "1.0"
      }
    },
    "ports": {
      "api": 18001,
      "dashboard": 17001,
      "mem0": 18002
    }
  }
}
```

### Timeout Configuration

```json
{
  "validation": {
    "timeouts": {
      "dockerBuild": 600000,
      "packageTest": 300000,
      "serviceTest": 180000,
      "healthCheck": 120000,
      "cleanup": 60000
    },
    "retries": {
      "dockerCommands": 2,
      "serviceStartup": 3,
      "healthCheck": 2
    }
  }
}
```

## Integration with Publish Workflow

### NPM Scripts Integration

The validation system integrates with npm publish workflow through:

```json
{
  "scripts": {
    "pre-publish": "./scripts/docker-validation-helper.sh pre-publish --verbose",
    "pre-publish:quick": "npm run docker:quick-test && npm run test",
    "pre-publish:full": "npm run pre-publish"
  }
}
```

### CI/CD Integration

For continuous integration environments:

```yaml
# GitHub Actions example
- name: Docker Pre-Publish Validation
  run: |
    npm run docker:quick-test
    npm run pre-publish:full
  env:
    DOCKER_BUILDKIT: 1
```

### Manual Publish Workflow

```bash
# Recommended pre-publish workflow
npm run pre-publish:full  # Full Docker validation
npm run test             # Additional tests
npm version patch        # Bump version
npm publish             # Publish to registry
```

## Validation Reports

### Report Structure

Validation reports are saved in JSON format in the `logs/` directory:

```json
{
  "timestamp": "2025-07-13T00:00:00Z",
  "validationId": "uuid",
  "passed": true,
  "summary": {
    "totalStages": 7,
    "completedStages": 7,
    "successfulStages": 7,
    "totalErrors": 0,
    "totalWarnings": 1,
    "overallSuccess": true
  },
  "stages": {
    "docker-availability": {
      "completed": true,
      "success": true,
      "details": {...}
    }
  },
  "errors": [],
  "warnings": []
}
```

### Report Analysis

```bash
# View recent validation logs
npm run docker:status

# Show validation history
./scripts/docker-validation-helper.sh logs

# Debug specific validation
./scripts/docker-validation-helper.sh debug --json
```

## Troubleshooting

### Common Issues

#### Docker Not Running
```bash
# Check Docker status
docker info

# Start Docker Desktop (macOS/Windows)
# or start Docker service (Linux)
sudo systemctl start docker
```

#### Port Conflicts
```bash
# Check port usage
netstat -ln | grep :18001
lsof -i :18001

# Kill conflicting processes
./scripts/docker-validation-helper.sh clean --force
```

#### Build Timeouts
```bash
# Increase timeout in config/docker-validation-config.json
# Check network connectivity
# Use verbose mode for diagnosis
npm run docker:validate:verbose
```

#### Memory Issues
```bash
# Check Docker memory settings
docker system info | grep -i memory

# Increase Docker memory limits
# Reduce resource usage in configuration
```

### Debug Commands

```bash
# Comprehensive debug information
npm run docker:debug

# Check Docker resources
docker system df
docker images | grep claude-pm
docker ps -a | grep claude-pm

# Validate Docker setup
npm run docker:quick-test

# Manual cleanup
npm run docker:clean
./scripts/docker-validation-helper.sh clean --force
```

## Performance Considerations

### Resource Usage

- **Memory**: ~512MB per validation container
- **CPU**: ~1.0 CPU cores during build/test
- **Disk**: ~2GB for Docker images and volumes
- **Network**: Minimal network usage

### Optimization Tips

1. **Pre-built Images**: Build validation environment once, reuse
2. **Parallel Testing**: Use Docker multi-stage builds
3. **Resource Limits**: Configure appropriate memory/CPU limits
4. **Cleanup Automation**: Regular cleanup of validation resources

### Timing Benchmarks

- **Quick Test**: ~30 seconds
- **Full Validation**: ~5-10 minutes
- **Build Environment**: ~2-5 minutes (first time)
- **Package Testing**: ~2-3 minutes

## Security Considerations

### Container Isolation
- All validation runs in isolated containers
- No host system access during testing
- Temporary networks and volumes
- Automatic resource cleanup

### Image Security
- Uses official Python base images
- No privileged container execution
- Resource limits and constraints
- Read-only volume mounts where possible

### Data Protection
- No sensitive data in validation containers
- Temporary test volumes only
- Automatic cleanup of test data
- No persistent storage of credentials

## Future Enhancements

### Planned Features
1. **Multi-platform Testing**: Test on different OS/architecture combinations
2. **Performance Benchmarking**: Automated performance regression testing
3. **Security Scanning**: Container vulnerability scanning
4. **Parallel Validation**: Run multiple validation stages concurrently

### Integration Opportunities
1. **GitHub Actions**: Pre-built action for repository validation
2. **Registry Integration**: Direct validation before publish
3. **Monitoring Integration**: Validation metrics and alerting
4. **Documentation Validation**: Automated documentation testing

## Support and Maintenance

### Monitoring
- Validation reports in `logs/` directory
- Health check integration
- Error tracking and alerting

### Maintenance
- Regular Docker image updates
- Configuration optimization
- Performance monitoring
- Security patch management

### Support Channels
- GitHub Issues for bugs and feature requests
- Documentation updates for new features
- Community contributions welcome

---

**DevOps Agent Implementation Complete**
*Docker-based validation system ready for package.json integration and production use*