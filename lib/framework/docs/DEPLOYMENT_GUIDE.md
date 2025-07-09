# Claude PM Framework - Deployment Guide

## Overview

The Claude PM Framework deployment system enables portable deployment of the complete framework to any directory, maintaining full ai-trackdown-tools integration and 42-ticket management capabilities.

## 🚀 Quick Deployment

### Deploy to Client Directory

```bash
# Deploy to ~/Clients/project-name
npm run deploy -- --target ~/Clients/project-name --verbose

# Test deployment first
npm run deploy:dry-run -- --target ~/Clients/project-name

# Validate deployment
npm run validate-deployment -- --target ~/Clients/project-name --verbose
```

### Deploy using Direct Commands

```bash
# Deploy to current directory
node install/deploy.js --verbose

# Deploy to specific directory
node install/deploy.js --target ~/Clients/project-name --verbose

# Dry run (test without changes)
node install/deploy.js --target ~/Clients/project-name --dry-run --verbose
```

## 📋 Prerequisites

### Required Software
- **Node.js**: 16.0.0 or higher
- **Python**: 3.8 or higher
- **ai-trackdown-tools**: 1.0.1 or higher

### Installation Commands
```bash
# Install ai-trackdown-tools globally
npm install -g @bobmatnyc/ai-trackdown-tools

# Verify installation
aitrackdown --version
```

## 🏗️ Deployment Architecture

### Hybrid NPM + Local Build Strategy
- **NPM Package**: Distributable framework package
- **Local Build**: Environment-specific deployment creation
- **Portable Dependencies**: ai-trackdown-tools integration maintained across deployments

### Three-Layer Configuration
1. **Package Defaults**: Built into framework
2. **Environment Variables**: System-level configuration
3. **Project-Specific**: `.claude-pm/config.json` in deployment

## 📁 Deployment Structure

```
deployment-directory/
├── claude_pm/              # Framework core
│   ├── cli.py              # Main CLI interface
│   ├── core/               # Core services
│   ├── services/           # Framework services
│   ├── integrations/       # External integrations
│   └── utils/              # Utility functions
├── tasks/                  # Ticket hierarchy
│   ├── epics/              # Strategic epics
│   ├── issues/             # Implementation issues
│   ├── tasks/              # Development tasks
│   ├── prs/                # Pull requests
│   └── templates/          # Ticket templates
├── templates/              # Project templates
├── schemas/                # Data schemas
├── bin/                    # CLI wrappers
│   ├── aitrackdown*        # Main CLI wrapper
│   └── atd*                # CLI alias
├── scripts/                # Deployment scripts
│   └── health-check*       # Health validation
├── requirements/           # Python dependencies
├── .claude-pm/             # Deployment config
│   └── config.json         # Configuration file
└── CLAUDE.md               # Framework configuration
```

## 🔧 AI-Trackdown Integration

### Automatic Path Resolution
The deployment system automatically:
1. Locates ai-trackdown-tools in global node_modules
2. Tries local node_modules as fallback
3. Uses npm ls to find installation
4. Creates environment-specific wrappers

### CLI Wrapper Creation
Platform-specific CLI wrappers maintain full functionality:

**Unix (Linux/macOS):**
```bash
#!/bin/bash
cd "/path/to/deployment"
node "/path/to/ai-trackdown-tools/dist/index.js" "$@"
```

**Windows:**
```batch
@echo off
cd /d "C:\path\to\deployment"
node "C:\path\to\ai-trackdown-tools\dist\index.js" %*
```

### Available Commands
- `./bin/aitrackdown` - Main CLI command
- `./bin/atd` - Alias for aitrackdown
- `./bin/aitrackdown status` - Current status
- `./bin/aitrackdown epic list` - List epics
- `./bin/aitrackdown issue list` - List issues

## 🏥 Health Monitoring

### Health Check Script
Each deployment includes a comprehensive health check:

```bash
# Unix/Linux/macOS
./scripts/health-check.sh

# Windows
.\scripts\health-check.bat
```

### Validation Tool
Comprehensive deployment validation:

```bash
node install/validate-deployment.js --target /path/to/deployment --verbose
```

### Health Check Components
- Framework core presence
- CLI wrapper functionality
- AI-trackdown integration
- Python environment
- Configuration validity

## 🚨 Deployment Process

### Step 1: Environment Validation
- Check Node.js version (16.0.0+)
- Check Python version (3.8+)
- Locate ai-trackdown-tools installation
- Verify target directory accessibility

### Step 2: Framework Core Deployment
- Copy `claude_pm/` directory
- Deploy templates and schemas
- Copy requirements and configuration

### Step 3: CLI Wrapper Creation
- Create platform-specific aitrackdown wrapper
- Create atd alias wrapper
- Set proper file permissions

### Step 4: Task Hierarchy Initialization
- Create tasks/ directory structure
- Initialize epics/, issues/, tasks/, prs/ directories
- Copy template files

### Step 5: Configuration Generation
- Generate `.claude-pm/config.json`
- Create deployment-specific CLAUDE.md
- Set up environment-specific configuration

### Step 6: Health Check Creation
- Create platform-specific health check script
- Set up validation tools
- Configure monitoring capabilities

## 🔍 Validation Infrastructure

### Deployment Validation
The validation system checks:
- Directory structure completeness
- Configuration file validity
- CLI wrapper functionality
- AI-trackdown integration
- Python environment readiness

### Health Check Validation
Regular health monitoring includes:
- Framework core accessibility
- CLI command functionality
- Python import capabilities
- Configuration integrity

## 🚀 Success Criteria

### Deployment Completion
- ✅ All framework files deployed
- ✅ AI-trackdown CLI wrappers created
- ✅ Task hierarchy initialized
- ✅ Configuration generated
- ✅ Health check passing

### Functional Verification
- ✅ `./bin/aitrackdown status` works
- ✅ `./bin/atd epic list` works
- ✅ Python framework importable
- ✅ Health check script passes
- ✅ All 42-ticket management capabilities preserved

## 🛠️ Troubleshooting

### Common Issues

**1. ai-trackdown-tools not found**
```bash
# Install globally
npm install -g @bobmatnyc/ai-trackdown-tools

# Verify installation
npm list -g @bobmatnyc/ai-trackdown-tools
```

**2. CLI wrappers not executable**
```bash
# Fix permissions (Unix)
chmod +x ./bin/aitrackdown ./bin/atd

# Fix permissions (Windows)
# No action needed for .bat files
```

**3. Python import errors**
```bash
# Check Python path
python3 -c "import sys; print(sys.path)"

# Install framework in development mode
pip install -e .
```

**4. Health check failures**
```bash
# Run validation
node install/validate-deployment.js --target /path/to/deployment --verbose

# Check configuration
cat .claude-pm/config.json
```

### Diagnostic Commands
```bash
# Full validation with details
npm run validate-deployment -- --target /path/to/deployment --verbose --json

# Test deployment without changes
npm run deploy:dry-run -- --target /path/to/deployment

# Check framework version
grep version .claude-pm/config.json

# Test CLI functionality
./bin/aitrackdown --help
./bin/atd status
```

## 📖 Configuration Reference

### Configuration File Structure
```json
{
  "version": "4.0.0",
  "deployedAt": "2025-07-08T...",
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

### Environment Variables
```bash
# Python command override
export CLAUDE_PM_PYTHON_CMD=python3

# AI-trackdown path override
export CLAUDE_PM_AI_TRACKDOWN_PATH=/custom/path/to/ai-trackdown-tools

# Deployment verbosity
export CLAUDE_PM_VERBOSE=true
```

## 🔄 Maintenance

### Updating Deployments
```bash
# Redeploy to update framework
npm run deploy -- --target /path/to/deployment --verbose

# Validate after update
npm run validate-deployment -- --target /path/to/deployment --verbose
```

### Backup Configuration
```bash
# Backup deployment configuration
cp -r /path/to/deployment/.claude-pm /path/to/backup/

# Backup task hierarchy
cp -r /path/to/deployment/tasks /path/to/backup/
```

### Monitoring Health
```bash
# Regular health check
/path/to/deployment/scripts/health-check.sh

# Comprehensive validation
node install/validate-deployment.js --target /path/to/deployment --verbose
```

## 🚀 Advanced Usage

### Custom Deployment Scripts
```javascript
const ClaudePMDeploymentEngine = require('./install/deploy.js');

const deployer = new ClaudePMDeploymentEngine({
    targetDir: '/custom/path',
    verbose: true,
    customOptions: {
        // Your custom options
    }
});

deployer.deploy()
    .then(() => console.log('Deployment completed'))
    .catch(error => console.error('Deployment failed:', error));
```

### Multi-Environment Deployments
```bash
# Development deployment
npm run deploy -- --target ~/dev/claude-pm --verbose

# Staging deployment
npm run deploy -- --target ~/staging/claude-pm --verbose

# Production deployment
npm run deploy -- --target ~/prod/claude-pm --verbose
```

## 📊 Performance Considerations

### Deployment Speed
- Framework core copy: ~1-2 seconds
- CLI wrapper creation: ~0.5 seconds
- Configuration generation: ~0.5 seconds
- Health check creation: ~0.5 seconds
- **Total deployment time**: ~3-5 seconds

### Resource Usage
- **Disk space**: ~50MB per deployment
- **Memory**: Minimal during deployment
- **CPU**: Low during deployment process

## 📚 Related Documentation

- [Framework Overview](./FRAMEWORK_OVERVIEW.md)
- [AI-Trackdown Integration](./TICKETING_SYSTEM.md)
- [Memory Integration](./MEMORY_SETUP_GUIDE.md)
- [Health Monitoring](./HEALTH_MONITORING.md)
- [Installation Guide](../install/README.md)

---

**Last Updated**: 2025-07-08
**Framework Version**: 4.0.0
**Deployment System Version**: 1.0.0