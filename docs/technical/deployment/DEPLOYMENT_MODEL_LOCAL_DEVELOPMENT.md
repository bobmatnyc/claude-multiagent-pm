# Claude PM Framework - Local Development Machine Deployment Model

## Overview

This document explains the deployment model for local development machines where the Claude PM Framework is actively developed. It provides guidance on when to use different deployment methods and how they relate to production deployment.

## Development Environment Context

On a local development machine (like `/Users/masa/Projects/claude-multiagent-pm`), you have several deployment options available:

1. **Direct Development Mode** - Working directly with the source code
2. **npm link Mode** - Simulating global installation while maintaining development flexibility
3. **Local Testing Mode** - Testing deployment scripts and installation processes
4. **Production Simulation** - Testing the full npm installation experience

## Deployment Methods Decision Tree

```
┌─────────────────────────────────────┐
│  What are you trying to accomplish? │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Are you actively developing features? │
└──────────┬───────────┬───────────────┘
           │ Yes       │ No
           ▼           ▼
┌──────────────────┐ ┌────────────────────────┐
│ Use Direct Dev   │ │ Testing deployment?    │
│ or npm link      │ └──────┬─────────┬───────┘
└──────────────────┘        │ Yes     │ No
                            ▼         ▼
                   ┌──────────────┐ ┌─────────────────┐
                   │ Use deploy.js│ │ Use npm install │
                   │ or dry-run   │ │ from registry   │
                   └──────────────┘ └─────────────────┘
```

## Deployment Methods Explained

### 1. Direct Development Mode

**When to use:**
- Making active code changes
- Debugging framework issues
- Testing new features immediately

**How it works:**
```bash
# Work directly in the source directory
cd /Users/masa/Projects/claude-multiagent-pm

# Run commands directly
./bin/claude-pm init
python -m claude_pm.cli

# Changes take effect immediately
```

**Advantages:**
- Instant feedback on code changes
- Full debugging capabilities
- No installation steps needed

**Disadvantages:**
- Not representative of user experience
- May have path dependencies

### 2. npm link Mode

**When to use:**
- Testing CLI behavior as if globally installed
- Developing while needing global command access
- Simulating user installation experience

**How it works:**
```bash
# In the framework directory
cd /Users/masa/Projects/claude-multiagent-pm
npm link

# Now claude-pm is available globally
claude-pm --version

# To unlink when done
npm unlink -g @bobmatnyc/claude-multiagent-pm
```

**Advantages:**
- Global command availability
- Changes reflected immediately
- Closer to production experience

**Disadvantages:**
- Can interfere with actual global installations
- May create symlink issues

### 3. Local Testing Mode (deploy.js)

**When to use:**
- Testing deployment to other directories
- Validating deployment scripts
- Creating portable installations

**How it works:**
```bash
# Deploy to a test directory
npm run deploy -- --target ~/test-deployment

# Or use the script directly
node install/deploy.js --target ~/test-deployment --verbose

# Test in the deployed directory
cd ~/test-deployment
./bin/claude-pm init
```

**Advantages:**
- Tests actual deployment process
- Creates isolated environments
- Validates all deployment steps

**Disadvantages:**
- Takes more time than direct development
- Requires cleanup of test deployments

### 4. Production Simulation

**When to use:**
- Final testing before npm publish
- Validating user installation experience
- Testing version-specific behavior

**How it works:**
```bash
# Publish to local npm registry (like Verdaccio)
npm publish --registry http://localhost:4873

# Or test with pack/install
npm pack
npm install -g ./bobmatnyc-claude-multiagent-pm-0.9.3.tgz

# Test as a user would
claude-pm init
```

**Advantages:**
- Exact production experience
- Tests npm installation process
- Validates package.json configuration

**Disadvantages:**
- Requires local npm registry setup
- More complex workflow

## Development Workflow Best Practices

### 1. Feature Development Workflow

```bash
# 1. Start with direct development
cd /Users/masa/Projects/claude-multiagent-pm
# Make your changes

# 2. Test locally
python -m pytest tests/

# 3. Test CLI with npm link
npm link
claude-pm init --dry-run

# 4. Test deployment
node install/deploy.js --target ~/test-deploy --dry-run

# 5. Clean up
npm unlink
```

### 2. Bug Fix Workflow

```bash
# 1. Reproduce the issue
claude-pm [problematic command]

# 2. Fix in development
# Edit the relevant files

# 3. Test the fix
npm link
claude-pm [previously problematic command]

# 4. Validate no regressions
npm test
```

### 3. Release Testing Workflow

```bash
# 1. Update version numbers
npm version patch

# 2. Test deployment script
node install/deploy.js --target ~/release-test

# 3. Test in deployed environment
cd ~/release-test
./scripts/health-check.sh

# 4. Test npm installation
npm pack
cd /tmp
npm install /path/to/package.tgz
npx claude-pm init

# 5. If all passes, publish
npm publish
```

## Relationship to Production

### Development vs Production Differences

| Aspect | Development | Production |
|--------|-------------|------------|
| Installation | Direct/npm link | npm install -g |
| Python packages | pip install -e . | Bundled in npm |
| Configuration | Local .claude-pm | User's ~/.claude-pm |
| Updates | Git pull | npm update |
| Debugging | Full source access | Limited to logs |

### Key Considerations

1. **Path Resolution**
   - Development: Relative paths work
   - Production: Must use absolute paths

2. **Dependencies**
   - Development: Can install on-demand
   - Production: Must be bundled or documented

3. **Permissions**
   - Development: Full write access
   - Production: Limited to user directories

4. **Performance**
   - Development: Debug mode acceptable
   - Production: Must be optimized

## Testing Strategy

### 1. Unit Tests
```bash
# Run in development
pytest tests/
npm test
```

### 2. Integration Tests
```bash
# Test with npm link
npm link
./tests/integration/test_cli.sh
```

### 3. Deployment Tests
```bash
# Test deployment process
./tests/deployment/test_deploy.sh
```

### 4. End-to-End Tests
```bash
# Full user simulation
./tests/e2e/test_full_install.sh
```

## Common Scenarios

### Scenario 1: Testing a CLI Change

```bash
# Edit bin/claude-pm
# Test immediately
./bin/claude-pm --version

# Test as global command
npm link
claude-pm --version
```

### Scenario 2: Testing Installation Process

```bash
# Make changes to install scripts
# Test deployment
node install/deploy.js --target ~/test --dry-run
node install/deploy.js --target ~/test

# Verify installation
cd ~/test
./scripts/health-check.sh
```

### Scenario 3: Testing Framework Loading

```bash
# Edit framework files
# Test with forced reload
claude-pm init --force

# Check logs
tail -f ~/.claude-pm/logs/claude-pm.log
```

## Troubleshooting Development Issues

### Issue: npm link not working
```bash
# Check existing links
npm ls -g --depth=0 --link=true

# Force unlink and relink
npm unlink -g @bobmatnyc/claude-multiagent-pm
npm link
```

### Issue: Python import errors
```bash
# Ensure development installation
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

### Issue: Version mismatches
```bash
# Sync all version files
npm run sync-versions

# Verify versions
grep -r "version" package.json pyproject.toml
```

## Summary

On a local development machine, you have multiple deployment options:

1. **Use Direct Development** for active feature development
2. **Use npm link** for testing CLI behavior while developing
3. **Use deploy.js** for testing deployment processes
4. **Use Production Simulation** for final validation before release

The key is choosing the right method for your current task while understanding how it relates to the production deployment experience that end users will have.

Remember: What works in development might not work in production, so always test the full deployment process before releasing changes.