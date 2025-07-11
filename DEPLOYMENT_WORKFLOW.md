# Claude PM Framework v0.5.1 - Installation & Deployment Workflow

## 📦 NPM Package Installation Workflow

### Complete Installation Process

```bash
# Install globally from NPM
npm install -g @bobmatnyc/claude-multiagent-pm

# Verify installation
claude-pm --version
claude-pm --system-info
```

### What Happens During Installation

#### 1. Package Download & Extraction
- NPM downloads `@bobmatnyc/claude-multiagent-pm@0.5.1` package
- Package extracted to global npm modules directory
- Binary `claude-pm` becomes available in PATH

#### 2. Postinstall Script Execution (`install/postinstall.js`)

**Global Configuration Creation:**
```json
{
  "version": "0.5.1",
  "installType": "global",
  "installDate": "2025-07-11T...",
  "platform": "darwin",
  "packageRoot": "/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm",
  "paths": {
    "framework": "/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm/lib/framework",
    "templates": "/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm/lib/templates",
    "schemas": "/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm/lib/schemas",
    "bin": "/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm/bin"
  }
}
```

**Framework Library Preparation:**
- Copies `claude_pm/` Python modules to `lib/framework/claude_pm/`
- Copies additional framework files: `requirements/`, `config/`, `docs/`, `templates/`, `schemas/`
- Creates lib directory structure for organized access

**Template & Schema Setup:**
- Creates default project templates in `lib/templates/`
- Generates configuration schemas in `lib/schemas/`
- Sets up validation and project creation infrastructure

**Platform-Specific Configuration:**
- **macOS/Linux**: Makes CLI scripts executable (`chmod 755`)
- **Windows**: Configures appropriate script extensions
- Sets platform-specific paths and configuration

**Framework CLAUDE.md Deployment:**
- Reads `framework/CLAUDE.md` template
- Performs variable substitution:
  - `{{CLAUDE_MD_VERSION}}` → `0.5.1-001`
  - `{{FRAMEWORK_VERSION}}` → `0.5.1`
  - `{{DEPLOYMENT_DATE}}` → Current timestamp
  - `{{PLATFORM}}` → `darwin`/`linux`/`win32`
  - `{{DEPLOYMENT_ID}}` → Unique deployment identifier
  - `{{PLATFORM_NOTES}}` → Platform-specific setup instructions
- Deploys processed template to working directory as `CLAUDE.md`
- Preserves existing user/project CLAUDE.md files

**Version Synchronization:**
- Updates any existing deployed instance configurations
- Synchronizes versions across all deployment locations
- Updates `.claude-pm/config.json` files with current package version

#### 3. Installation Validation
- Verifies required paths exist: `bin/claude-pm`, `lib/`, `install/`
- Validates CLI script permissions
- Confirms framework library structure
- Tests Python environment compatibility

## 🔧 Framework CLAUDE.md Deployment System

### Automatic Deployment Logic

```javascript
// Working directory check
const workingClaudemd = path.join(workingDir, 'CLAUDE.md');

// Preserve user files
if (fs.existsSync(workingClaudemd)) {
    const content = fs.readFileSync(workingClaudemd, 'utf8');
    
    // Skip if user/project file
    if (!content.includes('Claude PM Framework Configuration - Deployment') && 
        !content.includes('AI ASSISTANT ROLE DESIGNATION')) {
        console.log('Working directory has custom CLAUDE.md, skipping framework deployment');
        return;
    }
}

// Deploy framework template with variable substitution
```

### Variable Substitution Process

**Template Variables:**
```markdown
<!-- 
CLAUDE_MD_VERSION: {{CLAUDE_MD_VERSION}}
FRAMEWORK_VERSION: {{FRAMEWORK_VERSION}}
DEPLOYMENT_DATE: {{DEPLOYMENT_DATE}}
LAST_UPDATED: {{LAST_UPDATED}}
-->

## 🤖 AI ASSISTANT ROLE DESIGNATION

### Framework Context
- **Version**: {{FRAMEWORK_VERSION}}
- **Deployment Date**: {{DEPLOYMENT_DATE}}
- **Platform**: {{PLATFORM}}
```

**Processed Output:**
```markdown
<!-- 
CLAUDE_MD_VERSION: 0.5.1-001
FRAMEWORK_VERSION: 0.5.1
DEPLOYMENT_DATE: 2025-07-11T20:47:37.016Z
LAST_UPDATED: 2025-07-11T20:47:37.016Z
-->

## 🤖 AI ASSISTANT ROLE DESIGNATION

### Framework Context
- **Version**: 0.5.1
- **Deployment Date**: 2025-07-11T20:47:37.016Z
- **Platform**: darwin
```

## 🚀 CLI Functionality & Deployment Detection

### Universal Deployment Detection (`bin/claude-pm`)

**Detection Strategies (Priority Order):**
1. **NPM Local Installation** - `node_modules/@bobmatnyc/claude-multiagent-pm`
2. **NPM Global Installation** - Global npm modules directory
3. **NPX Execution** - NPX cache directory
4. **Local Source Development** - Source repository
5. **Deployed Instance** - User deployed configurations
6. **Environment-Based** - Environment variables
7. **Fallback Detection** - Common installation locations

**Version Resolution System:**
```javascript
function resolveVersion() {
    // Strategy 1: package.json relative to script
    // Strategy 2: VERSION file
    // Strategy 3: NPM package in node_modules
    // Strategy 4: npm list command
    // Fallback: Error with installation instructions
}
```

### Memory Management & Performance

**Memory Leak Prevention:**
- Cache cleanup every 30 seconds
- Automatic garbage collection
- Process cleanup on exit signals
- Spawned process management
- Memory usage monitoring

**Performance Optimizations:**
- Detection result caching
- Parallel deployment operations
- Timeout management
- Resource cleanup

## 🔨 Troubleshooting & Fix Scripts

### NPM Deployment Fix Script (`scripts/fix_npm_deployment.js`)

**Fixes Applied:**
1. **Version Synchronization** - Updates deployed instance versions
2. **Framework Deployment** - Deploys/updates framework CLAUDE.md
3. **Configuration Repair** - Fixes corrupted configurations
4. **Path Resolution** - Corrects framework path issues

**Usage:**
```bash
# Manual fix execution
node scripts/fix_npm_deployment.js

# Available via package scripts
npm run fix-npm-deployment
```

### Installation Verification

**Health Check Commands:**
```bash
# Basic version check
claude-pm --version

# Comprehensive system information
claude-pm --system-info

# Deployment detection details
claude-pm --deployment-info

# Framework template management
claude-pm --manage-claude-md

# Service status checks
claude-pm --template-status
claude-pm --dependency-status
claude-pm --parent-directory-status
```

## 📊 Installation Success Verification

### Verification Checklist

**✅ Package Installation:**
- [ ] `claude-pm --version` shows correct version (0.5.1)
- [ ] Command available in PATH globally

**✅ Framework Deployment:**
- [ ] `CLAUDE.md` deployed to working directory
- [ ] Variable substitution completed correctly
- [ ] Platform-specific configuration included

**✅ Configuration Setup:**
- [ ] Global config created at `~/.claude-pm/config.json`
- [ ] Framework library prepared in package lib directory
- [ ] Templates and schemas available

**✅ Python Integration:**
- [ ] Python modules accessible via PYTHONPATH
- [ ] Framework imports work correctly
- [ ] CLI commands execute successfully

**✅ Cross-Platform Compatibility:**
- [ ] CLI scripts executable on Unix systems
- [ ] Platform-specific paths configured correctly
- [ ] Environment variables set appropriately

### Common Installation Issues & Solutions

**Issue: Version mismatch**
```bash
# Solution: Run NPM deployment fix
npm run fix-npm-deployment
```

**Issue: Framework CLAUDE.md not deployed**
```bash
# Solution: Manual framework deployment
claude-pm --manage-claude-md
```

**Issue: CLI not found**
```bash
# Solution: Verify global installation
npm list -g @bobmatnyc/claude-multiagent-pm
npm install -g @bobmatnyc/claude-multiagent-pm
```

**Issue: Python integration failure**
```bash
# Solution: Verify Python environment
python3 --version
claude-pm --system-info
```

## 🎯 User Experience Flow

### First-Time Installation
1. User runs `npm install -g @bobmatnyc/claude-multiagent-pm`
2. Postinstall script automatically configures everything
3. Framework CLAUDE.md deployed to working directory
4. User can immediately run `claude-pm --help` for usage

### Subsequent Updates
1. User runs `npm update -g @bobmatnyc/claude-multiagent-pm`
2. Postinstall script updates configurations
3. Existing user files preserved
4. Framework deployments updated with new version

### Project Usage
1. User navigates to project directory
2. Runs `claude-pm` (launches with system info)
3. Framework automatically detects deployment type
4. Optimized Claude interface with memory management

This workflow ensures a seamless installation and deployment experience with comprehensive error handling, automatic configuration, and intelligent framework management.