# EP-0043 File Size Refactoring - Branching Strategy

## Overview

This document outlines the branching strategy for Epic EP-0043: Code Maintainability - Reduce File Sizes to 1000 Lines.

**Feature Branch**: `feature/EP-0043-file-size-refactoring`
**Created**: 2025-07-18
**Expected Duration**: 8-12 weeks
**Total Issues**: 16 files to refactor

## Branch Structure

### Main Feature Branch
- **Name**: `feature/EP-0043-file-size-refactoring`
- **Purpose**: Main integration branch for all refactoring work
- **Based on**: `main` branch
- **Merge Target**: `main` branch (after full completion and testing)

### Sub-branches for Individual Files

Each file refactoring should be done in its own sub-branch:

**Naming Convention**: `refactor/ISS-[NUMBER]-[filename]`

Examples:
- `refactor/ISS-0154-parent-directory-manager`
- `refactor/ISS-0155-agent-registry`
- `refactor/ISS-0156-backwards-compatible-orchestrator`

## Workflow

### 1. Starting Work on a File

```bash
# Ensure you're on the latest feature branch
git checkout feature/EP-0043-file-size-refactoring
git pull origin feature/EP-0043-file-size-refactoring

# Create sub-branch for specific file
git checkout -b refactor/ISS-[NUMBER]-[filename]
```

### 2. During Development

- Make incremental commits with clear messages
- Follow the refactoring guidelines and patterns
- Ensure tests pass at each commit
- Keep changes focused on the specific file and its direct dependencies

### 3. Completing a File Refactor

```bash
# Push sub-branch
git push -u origin refactor/ISS-[NUMBER]-[filename]

# Create PR to merge into feature/EP-0043-file-size-refactoring
# Not into main!
```

### 4. Pull Request Process

1. **Sub-branch → Feature Branch PRs**:
   - Title: `[ISS-NUMBER] Refactor [filename] - Reduce to <1000 lines`
   - Description should include:
     - Original line count
     - New line count
     - Summary of changes
     - Test results
   - Requires code review
   - Must pass all tests

2. **Feature Branch → Main PR** (Final):
   - Created after all 16 files are refactored
   - Comprehensive testing required
   - Full regression test suite
   - Performance benchmarks

## Merge Strategy

### For Sub-branches
- Use **squash and merge** for cleaner history
- Delete sub-branch after merge

### For Feature Branch
- Use **regular merge** to preserve full history
- Do NOT squash - we want the complete refactoring history

## Coordination Guidelines

### Multiple Engineers
Since multiple engineers may work on different files simultaneously:

1. **Claim Issues**: Assign yourself to an issue before starting
2. **Communicate**: Use issue comments for updates
3. **Avoid Conflicts**: Check dependencies before starting
4. **Regular Syncs**: Pull from feature branch daily

### Dependency Management
Some files have interdependencies. Refactor order:

1. **Independent files first** (no dependencies)
2. **Base services** (utils, core services)
3. **Dependent services** (that use base services)
4. **Top-level components** (CLI, main orchestrator)

## Testing Requirements

### For Each Sub-branch
- Unit tests for refactored module must pass
- Integration tests involving the module must pass
- No regression in functionality
- Performance should not degrade

### For Feature Branch
- Full test suite must pass
- Integration tests across all refactored modules
- End-to-end testing of key workflows
- Performance benchmarking

## Rollback Strategy

If issues are discovered:

1. **Individual File Issues**: Revert the specific sub-branch merge
2. **Systemic Issues**: Feature branch can be rebased/reset
3. **Production Issues**: Full feature branch can be reverted from main

## Timeline Considerations

### Weekly Goals
- Week 1-2: 3-4 simple files (independent utilities)
- Week 3-4: 2-3 medium complexity files
- Week 5-6: 2-3 complex service files
- Week 7-8: 1-2 most complex files
- Week 9-10: Integration testing and fixes
- Week 11-12: Buffer for issues and final testing

### Milestones
- **25% Complete**: After 4 files (Week 2-3)
- **50% Complete**: After 8 files (Week 4-5)
- **75% Complete**: After 12 files (Week 6-7)
- **100% Complete**: All 16 files (Week 8-9)
- **Ready to Merge**: After full testing (Week 10-12)

## Branch Protection Rules

### Feature Branch Protection
- Require pull request reviews (1 approval minimum)
- Require status checks to pass (tests, linting)
- Require branches to be up to date before merging
- Include administrators in restrictions

### Sub-branch Guidelines
- No direct pushes to feature branch
- All changes through PRs
- Automated testing on all PRs

## Communication

### Progress Tracking
- Update issue status when starting/completing work
- Use issue comments for important decisions
- Weekly status updates in epic EP-0043

### Coordination Channels
- GitHub Issues for async communication
- PR reviews for code-specific discussions
- Team meetings for blockers/dependencies

## Success Criteria

The feature branch is ready to merge to main when:

1. All 16 files have been successfully refactored
2. All files are under 1000 lines
3. Full test suite passes
4. No performance regressions
5. Code review completed for all changes
6. Documentation updated where needed
7. Integration testing completed