# Claude PM Framework - Deployment System

This directory contains the portable deployment system for the Claude PM Framework, enabling full framework deployments to any directory with complete ai-trackdown-pytools integration.

## 🚀 Quick Start

### Deploy to a New Directory

```bash
# Deploy to ~/Clients/my-project
npm run deploy -- --target ~/Clients/my-project --verbose

# Test deployment first
npm run deploy:dry-run -- --target ~/Clients/my-project

# Validate existing deployment
npm run validate-deployment -- --target ~/Clients/my-project --verbose
```

### Deploy using Node.js directly

```bash
# Deploy to current directory
node install/deploy.js --verbose

# Deploy to specific directory
node install/deploy.js --target ~/Clients/my-project --verbose

# Dry run (test without changes)
node install/deploy.js --target ~/Clients/my-project --dry-run --verbose
```

## 📁 Deployment Structure

A successful deployment creates this structure:

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
│   ├── aitrackdown*        # Placeholder script (ai-trackdown-pytools is a Python library)
│   └── atd*                # Placeholder script (ai-trackdown-pytools is a Python library)
├── scripts/                # Deployment scripts
│   └── health-check*       # Health validation
├── requirements/           # Python dependencies
├── .claude-pm/             # Deployment config
│   └── config.json         # Configuration file
└── CLAUDE.md               # Framework configuration
```

## 🔧 Deployment Scripts

### `deploy.js`
Main deployment script that creates a complete framework deployment.

### `preuninstall.js` - **NEW** Comprehensive Cleanup System
Complete removal and cleanup system with user data handling.

**Features:**
- Interactive and automatic cleanup modes
- User data detection and backup creation
- Multi-platform installation detection (NPM, pip, manual)
- Safety checks and user confirmations
- Comprehensive file size analysis (detects 107MB+ installations)
- Operation tracking for cleanup insights
- Verification system for complete removal

**Usage:**
```bash
# CLI integration
claude-pm --cleanup              # Interactive (safest)
claude-pm --cleanup --auto       # Automatic (keeps user data)
claude-pm --cleanup --full       # Complete removal with backup

# NPM scripts
npm run cleanup                  # Interactive mode
npm run cleanup:full             # Full interactive cleanup
npm run cleanup:auto             # Automatic conservative cleanup
npm run uninstall:complete       # Full uninstall process

# Automatic during uninstall
npm uninstall -g @bobmatnyc/claude-multiagent-pm  # Triggers preuninstall.js
```

### `deploy.js`
Main deployment script that creates a complete framework deployment.

**Features:**
- Environment validation (Node.js, Python, ai-trackdown-pytools)
- Framework core deployment
- Task hierarchy initialization
- Configuration generation
- Platform-specific optimizations
- Python package integration
- **CLAUDE.md preservation** - Protects existing custom project instructions

**CLAUDE.md Protection:**
- **Default behavior**: Preserves existing CLAUDE.md files to protect custom instructions
- **Warning displayed**: When existing CLAUDE.md found, script warns and skips generation
- **Force option**: Use `--force` flag to overwrite (creates backup first)
- **Backup creation**: When using --force, creates timestamped backup before overwriting

**Usage:**
```bash
node install/deploy.js [options]

Options:
  --target, -t       Target directory for deployment
  --verbose, -v      Verbose output
  --dry-run          Test deployment without changes
  --skip-validation  Skip environment validation
  --force            DANGEROUS: Overwrite existing CLAUDE.md (creates backup)
```

**Examples:**
```bash
# Safe deployment (preserves existing CLAUDE.md)
node install/deploy.js --target ~/Projects/my-project

# Force regeneration with backup
node install/deploy.js --target ~/Projects/my-project --force
# Creates: CLAUDE.md.backup.[timestamp] before overwriting
```

### `validate-deployment.js`
Validates that a deployment is fully functional.

**Features:**
- Structure validation
- Configuration validation
- CLI wrapper testing
- AI-trackdown integration testing
- Python environment validation
- Health check validation

**Usage:**
```bash
node install/validate-deployment.js [options]

Options:
  --target, -t    Deployment directory to validate
  --verbose, -v   Verbose output
  --json          Output results as JSON
```

### `install.js`
Legacy installation script (maintained for compatibility).

## 🛠️ Configuration System

### Three-Layer Configuration
1. **Package Defaults**: Built into the framework
2. **Environment Variables**: System-level configuration
3. **Project-Specific**: `.claude-pm/config.json` in deployment

### Configuration File Structure
```json
{
  "version": "1.4.2",
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
    "coreIntegration": true,
    "multiAgentSupport": true,
    "portableDeployment": true
  }
}
```

## 🔍 AI-Trackdown Integration

### Python Library Integration
The ai-trackdown-pytools is a Python library that provides programmatic access to task management:

**Python Usage:**
```python
from ai_trackdown import Task, Issue, Epic

# Create a new task
task = Task(
    id="TSK-001",
    title="Implement feature",
    description="Feature implementation",
    status="open"
)

# Create an issue
issue = Issue(
    id="ISS-001",
    title="Bug fix",
    priority="high"
)
```

### Integration Notes
- ai-trackdown-pytools is a Python library, not a CLI tool
- Access task management features through Python code
- The deployment creates placeholder scripts that inform users about Python usage

## 🏥 Health Monitoring

### Health Check Script
Each deployment includes a health check script that validates:
- Framework core presence
- CLI wrapper functionality
- AI-trackdown integration
- Python environment
- Configuration validity

**Usage:**
```bash
# Unix/Linux/macOS
./scripts/health-check.sh

# Windows
.\scripts\health-check.bat
```

### Validation Tool
Comprehensive validation using the validation script:
```bash
node install/validate-deployment.js --target /path/to/deployment --verbose
```

## 🚨 Prerequisites

### Required Software
- **Node.js**: 16.0.0 or higher
- **Python**: 3.8 or higher
- **ai-trackdown-pytools**: 1.1.0 (Python package)

### Installation Commands
```bash
# Install ai-trackdown-pytools via pip
pip install --user ai-trackdown-pytools==1.1.0

# Verify installation
python -c "import ai_trackdown; print('ai-trackdown-pytools installed')"
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Node.js 16+ installed
- [ ] Python 3.8+ installed
- [ ] ai-trackdown-pytools installed via pip
- [ ] Target directory accessible

### Deployment Process
- [ ] Run deployment script
- [ ] Validate deployment structure
- [ ] Test CLI wrappers
- [ ] Run health check
- [ ] Validate ai-trackdown integration

### Post-Deployment
- [ ] Framework core accessible
- [ ] CLI commands working
- [ ] Python environment ready
- [ ] Configuration generated
- [ ] Health check passing

## 🔧 Troubleshooting

### Common Issues

**1. ai-trackdown-pytools not found**
```bash
# Install via pip
pip install --user ai-trackdown-pytools==1.1.0

# Verify installation
python -c "import ai_trackdown; print('Installed')"
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

### Support Commands
```bash
# Full validation with details
npm run validate-deployment -- --target /path/to/deployment --verbose --json

# Dry run deployment
npm run deploy:dry-run -- --target /path/to/deployment

# Check framework version
grep version .claude-pm/config.json
```

## 🚀 Advanced Usage

### Custom Deployment Scripts
Extend the deployment system by creating custom deployment scripts:

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

### Environment-Specific Configuration
Create environment-specific configuration files:

```json
{
  "development": {
    "pythonCmd": "python3",
    "verbose": true,
    "skipValidation": false
  },
  "production": {
    "pythonCmd": "python3",
    "verbose": false,
    "skipValidation": false
  }
}
```

## 📖 Related Documentation

- [Framework Overview](../docs/FRAMEWORK_OVERVIEW.md)
- [AI-Trackdown Integration](../docs/TICKETING_SYSTEM.md)
- [Core Integration](../docs/CORE_SETUP_GUIDE.md)
- [Health Monitoring](../docs/HEALTH_MONITORING.md)

---

**Last Updated**: 2025-07-08
**Framework Version**: 4.0.0
**Deployment System Version**: 1.0.0