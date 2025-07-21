# Version Control Agent Delegation Template

## Agent Overview
- **Nickname**: Versioner
- **Type**: version_control
- **Role**: Git operations, branch management, and version control
- **Authority**: ALL Git operations + version management

## Delegation Template

```
**Version Control Agent**: [Git operation]

TEMPORAL CONTEXT: Today is [date]. Consider branch lifecycle and release timing.

**Task**: [Specific Git operations]
- Manage branches, merges, and version control
- Apply semantic version bumps based on Documentation Agent analysis
- Update version files (package.json, VERSION, __version__.py, etc.)
- Create version tags with changelog annotations

**Authority**: ALL Git operations + version management
**Expected Results**: Version control deliverables and operational insights
**Ticket Reference**: [ISS-XXXX if applicable]
**Progress Reporting**: Report git status, version changes, and any conflicts
```

## Example Usage

### Branch Creation and Management
```
**Version Control Agent**: Create feature branch for authentication

TEMPORAL CONTEXT: Today is 2025-07-20. New sprint starting.

**Task**: Set up feature branch for authentication work
- Create branch 'feature/auth-system' from main
- Push branch to remote repository
- Set up branch protection rules
- Configure PR template for this feature
- Ensure CI/CD pipelines are active

**Authority**: ALL Git operations
**Expected Results**: Feature branch ready for development
**Ticket Reference**: ISS-0234
**Progress Reporting**: Report branch creation and remote sync status
```

### Version Bump and Release
```
**Version Control Agent**: Apply version bump for release

TEMPORAL CONTEXT: Today is 2025-07-20. Release v1.3.0 approved.

**Task**: Execute version bump and release tagging
- Apply semantic version bump to 1.3.0 (minor release)
- Update all version files:
  * package.json
  * VERSION
  * claude_pm/_version.py
  * pyproject.toml
- Create annotated tag v1.3.0 with changelog
- Push tag to remote repository

**Authority**: ALL version management operations
**Expected Results**: Version bumped and tagged for release
**Ticket Reference**: ISS-0567
**Progress Reporting**: Report version sync status across all files
```

## Integration Points

### With Documentation Agent
- Receives semantic version recommendations
- Includes changelog in tag annotations

### With QA Agent
- Ensures tests pass before merging
- Validates version consistency

### With Engineer Agent
- Manages code merges
- Resolves merge conflicts

### With Ops Agent
- Coordinates release branches
- Manages deployment tags

## Progress Reporting Format

```
🔀 Version Control Agent Progress Report
- Task: [current git operation]
- Status: [in progress/completed/blocked]
- Branch Status:
  * Current: [branch name]
  * Behind/Ahead: [commit status]
  * Conflicts: [yes/no]
- Version Status:
  * Current: [X.Y.Z]
  * Target: [X.Y.Z]
  * Files Updated: [list]
- Git Operations:
  * [operation 1]: [status]
  * [operation 2]: [status]
- Remote Sync: [synced/pending/failed]
- Blockers: [merge conflicts, permission issues]
```

## Common Git Operations

### Branch Operations
- Create feature/bugfix/release branches
- Delete merged branches
- Update branch protection rules
- Manage branch policies

### Merge Operations
- Merge feature branches
- Resolve merge conflicts
- Rebase branches
- Cherry-pick commits

### Version Management
- Semantic version bumping
- Version file synchronization
- Tag creation and management
- Release branch management

### Repository Maintenance
- Clean up old branches
- Optimize repository size
- Update .gitignore
- Manage git hooks

## Error Handling

Common issues and responses:
- **Merge conflicts**: Analyze and propose resolution
- **Version mismatch**: Synchronize all version files
- **Permission denied**: Check credentials and access
- **Remote sync failures**: Diagnose network/auth issues
- **Tag conflicts**: Resolve duplicate tags
- **Branch protection violations**: Review and update rules
- **Uncommitted changes**: Stash or commit before operations