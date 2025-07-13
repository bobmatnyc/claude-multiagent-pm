# Claude PM Installation Guide for Mono-Repo Environments

## Overview

This guide specifically addresses installation and usage of Claude PM in mono-repository environments, providing detailed answers to common concerns about safety, compatibility, and best practices.

## Key Safety Guarantees

**⚠️ Critical Safety Assurances**:
- Claude PM **never modifies** your existing build scripts, CI/CD pipelines, or deployment processes automatically
- All changes are **suggestions only** - you review and approve everything
- Can be **instantly disabled** with `claude-pm disable`
- Works **alongside** existing tools without replacing them
- **No vendor lock-in** - all AI assistance is optional and removable

## Mono-Repo Specific Installation

### Prerequisites for Mono-Repo Environments

**System Requirements**:
- Node.js 16+ (for workspace management)
- Python 3.9+ (for AI framework)
- Git (for version control integration)
- 4GB+ RAM (8GB recommended for large mono-repos)

**Mono-Repo Compatibility Check**:
```bash
# Check if your mono-repo is compatible
cd your-mono-repo
ls -la package.json lerna.json nx.json rush.json 2>/dev/null || echo "Standard mono-repo structure detected"

# Check workspace structure
find . -name "package.json" | head -10
```

### Step 1: Global Installation (Mono-Repo Safe)

Claude PM installs globally and works across all projects without interfering with individual workspace configurations:

```bash
# Global installation - works across all projects
npm install -g @bobmatnyc/claude-multiagent-pm
npm install -g @bobmatnyc/ai-trackdown-tools

# Verify installation
claude-pm --version
aitrackdown --version
```

**Why Global Installation is Safe**:
- Does not modify any `package.json` files in your mono-repo
- Does not add dependencies to individual workspaces
- Does not interfere with workspace managers (Lerna, Nx, Rush, etc.)
- Can be uninstalled without affecting your project

### Step 2: Workspace-Level Configuration

After global installation, configure Claude PM for specific workspaces:

```bash
# Navigate to specific workspace
cd packages/your-workspace

# Initialize Claude PM (creates local .claude-pm directory only)
claude-pm init --workspace

# Verify no package.json changes
git status  # Should show only .claude-pm/ as new
```

**What Gets Created**:
```
packages/your-workspace/
├── .claude-pm/           # Local Claude PM config (gitignore recommended)
│   ├── config.json      # Workspace-specific settings
│   ├── memory/          # Local AI memory (workspace-scoped)
│   └── agents/          # Custom agents for this workspace
├── package.json         # UNCHANGED - your existing config
├── src/                 # UNCHANGED - your source code
└── tests/               # UNCHANGED - your test setup
```

### Step 3: Safety Verification

Before using Claude PM, verify it's not interfering with your existing setup:

```bash
# Test existing build process UNCHANGED
npm run build   # Should work exactly as before
npm test        # Should work exactly as before
npm run deploy  # Should work exactly as before

# Verify git status clean (except .claude-pm)
git status

# Test Claude PM is isolated
claude-pm status  # Should show workspace detected, no conflicts
```

## Mono-Repo Usage Patterns

### Pattern 1: Individual Workspace Enhancement

Use Claude PM on one workspace at a time for safety:

```bash
# Focus on single workspace
cd packages/api-service
claude-pm
# AI: "I see this is an Express.js API service. What would you like to work on?"

# Use AI assistance
claude-pm push     # AI reviews code before commits
claude-pm deploy   # AI validates deployment
claude-pm publish  # AI handles package publication
```

**Benefits**:
- Test Claude PM safely on one component
- Learn the AI's behavior before expanding
- Maintain isolation between workspaces

### Pattern 2: Gradual Rollout Across Workspaces

Once comfortable, expand to additional workspaces:

```bash
# Enable on frontend workspace
cd packages/web-app
claude-pm init --workspace

# Enable on shared library
cd packages/shared-utils
claude-pm init --workspace

# Coordinate across workspaces
claude-pm --workspace-sync
```

### Pattern 3: Mono-Repo Coordination

For advanced users, enable cross-workspace coordination:

```bash
# Enable mono-repo awareness (optional, advanced)
cd mono-repo-root
claude-pm init --mono-repo --workspaces="packages/*"

# AI now understands workspace relationships
claude-pm analyze-dependencies  # Shows workspace interdependencies
claude-pm suggest-refactoring   # Suggests cross-workspace improvements
```

## Safety and Risk Mitigation

### What Claude PM NEVER Does Automatically

**Build/Deploy Pipeline**:
- ❌ Never modifies `package.json` scripts
- ❌ Never changes CI/CD configuration (`.github/workflows/`, `.gitlab-ci.yml`, etc.)
- ❌ Never alters deployment scripts
- ❌ Never modifies Docker configurations
- ❌ Never changes environment variables

**Workspace Configuration**:
- ❌ Never modifies workspace manager configs (Lerna, Nx, Rush)
- ❌ Never changes dependency relationships between workspaces
- ❌ Never alters monorepo build order
- ❌ Never modifies shared tooling configurations

**Version Control**:
- ❌ Never commits code automatically
- ❌ Never pushes to remote repositories
- ❌ Never merges branches
- ❌ Never tags releases

### What Claude PM DOES Safely

**Code Analysis**:
- ✅ Analyzes code patterns and suggests improvements
- ✅ Identifies potential bugs and security issues
- ✅ Suggests refactoring opportunities
- ✅ Provides code documentation

**Development Assistance**:
- ✅ Generates test cases (you review and run)
- ✅ Suggests API improvements (you implement)
- ✅ Identifies performance bottlenecks
- ✅ Provides debugging assistance

**Project Management**:
- ✅ Tracks development progress
- ✅ Manages task lists and priorities
- ✅ Provides project insights and metrics
- ✅ Suggests development workflows

## Troubleshooting Mono-Repo Issues

### Issue 1: Workspace Detection Problems

**Problem**: Claude PM not recognizing mono-repo structure

**Symptoms**:
```bash
$ claude-pm
Warning: Mono-repo structure not detected
```

**Solution**:
```bash
# Check workspace manager
ls -la lerna.json nx.json rush.json yarn.lock pnpm-workspace.yaml

# Manual workspace configuration
claude-pm config set workspace-manager nx  # or lerna, rush, yarn
claude-pm config set workspace-pattern "packages/*"

# Re-initialize
claude-pm init --workspace --force
```

### Issue 2: Dependency Conflicts

**Problem**: Claude PM interfering with workspace dependencies

**Symptoms**:
```bash
npm ERR! Cannot resolve dependency conflicts
npm ERR! Claude PM dependencies conflicting
```

**Solution**:
```bash
# Check if global install corrupted local dependencies
npm ls | grep claude

# If found, remove from package.json (should not be there)
vim package.json  # Remove any claude-pm entries

# Verify global installation only
npm list -g | grep claude-multiagent-pm

# Reinstall globally if needed
npm uninstall -g @bobmatnyc/claude-multiagent-pm
npm install -g @bobmatnyc/claude-multiagent-pm
```

### Issue 3: Performance Issues in Large Mono-Repos

**Problem**: Claude PM slow in large repositories

**Symptoms**:
```bash
$ claude-pm analyze
# Takes >30 seconds or times out
```

**Solution**:
```bash
# Configure workspace exclusions
claude-pm config set ignore-patterns "node_modules,dist,build,coverage"
claude-pm config set max-file-scan 1000

# Use workspace-scoped analysis
cd packages/specific-workspace
claude-pm analyze --scope workspace

# Enable performance mode
claude-pm config set performance-mode true
```

### Issue 4: Git Integration Issues

**Problem**: Git operations conflicting with mono-repo setup

**Symptoms**:
```bash
$ claude-pm push
Error: Multiple package.json files detected, cannot determine root
```

**Solution**:
```bash
# Configure mono-repo git settings
claude-pm config set git-root $(git rev-parse --show-toplevel)
claude-pm config set workspace-root "packages"

# Test git integration
claude-pm git-status  # Should show workspace-aware status
```

## Best Practices for Mono-Repos

### 1. Start Small Strategy

**Week 1: Single Workspace**
```bash
# Choose least critical workspace
cd packages/utilities
claude-pm init --workspace

# Use for basic tasks only
claude-pm analyze
claude-pm suggest-tests
```

**Week 2: Expand Gradually**
```bash
# Add second workspace
cd packages/api
claude-pm init --workspace

# Test cross-workspace awareness
claude-pm analyze-dependencies
```

**Week 3: Full Integration**
```bash
# Enable mono-repo coordination
cd mono-repo-root
claude-pm init --mono-repo
```

### 2. Configuration Management

**Shared Configuration**:
```bash
# Create shared config for all workspaces
mkdir .claude-pm-shared
cat > .claude-pm-shared/config.json << 'EOF'
{
  "coding_standards": "team-standards.md",
  "test_framework": "jest",
  "build_tool": "webpack",
  "deployment_target": "kubernetes"
}
EOF

# Link to workspaces
cd packages/workspace1
claude-pm config link ../.claude-pm-shared/config.json
```

**Workspace-Specific Overrides**:
```bash
# Override for specific needs
cd packages/legacy-service
claude-pm config set test_framework "mocha"  # Override shared Jest config
claude-pm config set coding_standards "legacy-standards.md"
```

### 3. Team Coordination

**Team Setup**:
```bash
# Team leader configures shared settings
claude-pm team init --name "Development Team"
claude-pm team add-member --email "dev@company.com"
claude-pm team set-standards --file "team-coding-standards.md"

# Team members join
claude-pm team join --invitation-code ABC123
```

**Shared Learning**:
```bash
# Enable team memory sharing
claude-pm config set shared-memory true
claude-pm config set team-id "dev-team-1"

# AI learns from all team members' patterns
```

## Advanced Mono-Repo Features

### Cross-Workspace Dependency Analysis

```bash
# Analyze dependencies across all workspaces
claude-pm analyze --cross-workspace

# Find circular dependencies
claude-pm find-cycles --workspaces

# Suggest dependency optimization
claude-pm suggest-dependency-refactor
```

### Coordinated Releases

```bash
# Plan coordinated release across workspaces
claude-pm release plan --workspaces="api,web,shared"

# Validate release compatibility
claude-pm release validate

# AI suggests release order and coordination
claude-pm release suggest-order
```

### Workspace-Aware Testing

```bash
# Run tests affected by changes
claude-pm test --affected

# Suggest integration tests between workspaces
claude-pm suggest-integration-tests

# Coordinate test execution order
claude-pm test --coordinate-workspaces
```

## Migration Guide

### From Manual to AI-Assisted Workflow

**Before (Manual Process)**:
```bash
# Traditional mono-repo workflow
cd packages/api
npm test
npm run lint
git add .
git commit -m "Fix bug"
git push
```

**After (AI-Assisted Process)**:
```bash
# AI-enhanced workflow
cd packages/api
claude-pm test --suggest-improvements
claude-pm lint --auto-fix-safe
claude-pm push  # AI reviews before commit
```

**Benefits of AI-Assisted Workflow**:
- Code quality suggestions before commit
- Automated test case generation
- Cross-workspace impact analysis
- Documentation updates
- Dependency update recommendations

### Rollback Plan

If you need to remove Claude PM:

```bash
# Stop all Claude PM processes
claude-pm stop

# Remove workspace configurations
find . -name ".claude-pm" -type d -exec rm -rf {} +

# Uninstall globally
npm uninstall -g @bobmatnyc/claude-multiagent-pm
npm uninstall -g @bobmatnyc/ai-trackdown-tools

# Verify no changes to your code
git status  # Should show only .claude-pm removals
```

Your original mono-repo will be completely unchanged.

## Conclusion

Claude PM is designed to be mono-repo safe by:
- Installing globally without modifying workspace configs
- Providing workspace-scoped AI assistance
- Never automatically modifying build/deploy processes
- Enabling gradual adoption and easy removal

Start with a single, non-critical workspace to build confidence, then gradually expand to other workspaces as you become comfortable with the AI assistance.

**Next Steps**:
1. Try installation on a test workspace first
2. Use for code analysis and suggestions only initially
3. Gradually enable more features as confidence builds
4. Read the [Safety and Risk Mitigation Guide](./09-safety-risk-mitigation.md) for additional details
