# Comprehensive Push Operations Workflow

## 🚀 Overview

This document defines the comprehensive push operations workflow for the Claude PM Framework. When anyone says "push", it triggers a complete deployment pipeline that includes version management, documentation updates, and git operations.

## 🎯 Scope

**Primary Goal**: Standardize deployment across all projects with a single "push" command.

**Supported Projects**:
- `/Users/masa/Projects/managed/ai-trackdown-tools`
- `/Users/masa/Projects/claude-multiagent-pm`
- All managed projects in `/Users/masa/Projects/managed/`

## 📋 Complete Push Workflow

### Phase 1: Pre-Push Validation

**Objectives**: Ensure project is ready for deployment

**Steps**:
1. **Check Project Status**
   ```bash
   git status
   git diff --stat
   ```

2. **Validate Build State**
   ```bash
   # For npm projects
   npm run build
   npm test
   
   # For Python projects
   python -m pytest
   pip install -r requirements.txt
   ```

3. **Dependency Verification**
   ```bash
   # Check for outdated packages
   npm outdated
   pip list --outdated
   ```

4. **Configuration Review**
   - Verify environment variables
   - Check configuration files
   - Validate deployment settings

### Phase 2: Version Management

**Objectives**: Determine and apply appropriate version increment

**Version Determination Logic**:
- **Patch (x.y.Z)**: Bug fixes, documentation updates, minor improvements
- **Minor (x.Y.z)**: New features, enhancements, non-breaking changes
- **Major (X.y.z)**: Breaking changes, major architecture updates

**Implementation**:
```bash
# For ai-trackdown-tools
npm run version:patch
npm run version:minor
npm run version:major

# For projects with custom release scripts
tsx scripts/release.ts patch
tsx scripts/release.ts minor
tsx scripts/release.ts major

# For manual version management
echo "1.2.3" > VERSION
```

### Phase 3: Documentation Updates

**Objectives**: Update documentation to reflect changes

**Required Updates**:
1. **README.md**
   - Version badges
   - New feature descriptions
   - Installation instructions
   - Usage examples

2. **CHANGELOG.md**
   - Version entry
   - Feature additions
   - Bug fixes
   - Breaking changes

3. **API Documentation**
   - Function signatures
   - Parameter changes
   - Return value updates

4. **Version Files**
   - `VERSION` file
   - `package.json` version
   - Python `__version__` variables

### Phase 4: Git Operations

**Objectives**: Commit changes and create version tags

**Git Workflow**:
1. **Stage All Changes**
   ```bash
   git add -A
   ```

2. **Generate Commit Message**
   ```
   chore: release version X.Y.Z
   
   Features:
   - New feature A
   - Enhancement B
   
   Bug Fixes:
   - Fix issue C
   - Resolve problem D
   
   Documentation:
   - Update README
   - Add changelog entries
   ```

3. **Commit Changes**
   ```bash
   git commit -m "commit message"
   ```

4. **Create Version Tag**
   ```bash
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   ```

### Phase 5: Remote Deployment

**Objectives**: Deploy to remote repository

**Deployment Steps**:
1. **Push Commits**
   ```bash
   git push origin main
   ```

2. **Push Tags**
   ```bash
   git push origin --tags
   ```

3. **Verify Deployment**
   - Check GitHub/GitLab repository
   - Verify tags are present
   - Confirm CI/CD pipeline triggers

### Phase 6: Post-Deployment Validation

**Objectives**: Confirm successful deployment

**Validation Checks**:
1. **Remote Repository Verification**
   - Commits appear in remote
   - Tags are visible
   - Branch is up to date

2. **CI/CD Pipeline Check**
   - Build pipeline triggered
   - Tests passing
   - Deployment artifacts created

3. **Health Check**
   - Application starts correctly
   - All services responsive
   - No breaking changes detected

## 🛡️ Error Handling

### Common Failure Scenarios

#### 1. Pre-Push Validation Failures
- **Uncommitted Changes**: Stage or stash changes before proceeding
- **Build Failures**: Fix build errors, run tests
- **Dependency Issues**: Update dependencies, resolve conflicts

#### 2. Version Management Failures
- **Version Conflicts**: Resolve with remote, increment appropriately
- **Invalid Version Format**: Validate semver format
- **Missing Scripts**: Fall back to manual version management

#### 3. Documentation Failures
- **README Conflicts**: Manual merge required
- **Missing CHANGELOG**: Generate basic changelog template
- **Documentation Errors**: Fix or skip with explicit approval

#### 4. Git Operation Failures
- **Commit Failures**: Resolve merge conflicts
- **Tag Conflicts**: Check existing tags, use different version
- **Push Failures**: Check network, permissions, repository state

### Rollback Procedures

#### Immediate Rollback (Before Push)
```bash
# Rollback last commit
git reset --hard HEAD~1

# Remove tag
git tag -d vX.Y.Z

# Restore previous version
git checkout HEAD~1 -- package.json VERSION
```

#### Post-Push Rollback
```bash
# Create rollback commit
git revert HEAD
git push origin main

# Remove remote tag
git push origin --delete vX.Y.Z
```

#### Emergency Rollback
1. **Stop Process**: Immediately halt deployment
2. **Assess Impact**: Determine rollback scope
3. **Execute Rollback**: Use appropriate rollback commands
4. **Verify Success**: Confirm rollback completed
5. **Document Issue**: Record incident for future prevention

## 🔧 Project-Specific Configurations

### AI-Trackdown-Tools
```yaml
location: /Users/masa/Projects/managed/ai-trackdown-tools
build_command: npm run build
test_command: npm test
version_scripts:
  - npm run version:patch
  - npm run version:minor
  - npm run version:major
release_scripts:
  - npm run release:patch
  - npm run release:minor
  - npm run release:major
```

### Claude-Multiagent-PM
```yaml
location: /Users/masa/Projects/claude-multiagent-pm
build_command: python -m pytest
test_command: ./scripts/health-check.sh
version_management: manual
version_file: VERSION
dependencies: requirements/production.txt
```

### Managed Projects Pattern
```yaml
location: /Users/masa/Projects/managed/*
detection:
  - Check package.json for version scripts
  - Look for VERSION file
  - Detect project type (npm, python, etc.)
fallback:
  - Use git tagging for version
  - Basic README/CHANGELOG updates
  - Standard commit message format
```

## 🚨 Agent Responsibilities

### Orchestrator Role
- **Recognition**: Immediately recognize "push" command
- **No Clarification**: Do not ask for clarification
- **Delegation**: Automatically delegate to ops agent
- **Monitoring**: Track deployment progress
- **Reporting**: Report results to user

### Ops Agent Role
- **Execution**: Execute complete push pipeline
- **Validation**: Perform all pre-push checks
- **Error Handling**: Handle failures gracefully
- **Rollback**: Provide rollback when needed
- **Documentation**: Document deployment results

## 📊 Success Metrics

### Deployment Success Rate
- **Target**: >95% successful pushes
- **Metric**: Successful deployments / Total attempts
- **Monitoring**: Track failures and root causes

### Deployment Speed
- **Target**: <5 minutes for standard push
- **Metric**: Time from "push" command to completion
- **Optimization**: Identify and reduce bottlenecks

### Rollback Efficiency
- **Target**: <2 minutes for emergency rollback
- **Metric**: Time to restore previous state
- **Preparation**: Maintain rollback procedures

## 📝 Usage Examples

### Basic Push
```
User: "push"
Orchestrator: Delegating comprehensive push operation to ops agent...
Ops Agent: Executing complete deployment pipeline...
Result: Successfully deployed version 1.2.3
```

### Push with Specific Version
```
User: "push as major version"
Orchestrator: Delegating major version push to ops agent...
Ops Agent: Executing major version deployment pipeline...
Result: Successfully deployed version 2.0.0
```

### Push with Rollback
```
User: "push"
Ops Agent: Deployment failed - build errors detected
Ops Agent: Executing rollback procedures...
Result: Rollback completed, repository restored to previous state
```

## 🔍 Monitoring and Alerting

### Key Metrics to Monitor
- Push success rate
- Deployment duration
- Rollback frequency
- Error patterns
- Resource utilization

### Alert Conditions
- Push failure rate >5%
- Deployment time >10 minutes
- Rollback execution
- Critical errors
- Resource exhaustion

## 📚 Related Documentation

- [Ops Agent Role Definition](../framework/agent-roles/ops-agent.md)
- [Orchestrator Configuration](../CLAUDE.md)
- [Version Management Guide](./VERSION_MANAGEMENT.md)
- [Error Handling Procedures](./ERROR_HANDLING.md)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-07-09
**Author**: DevOps Team
**Review Date**: 2025-08-09