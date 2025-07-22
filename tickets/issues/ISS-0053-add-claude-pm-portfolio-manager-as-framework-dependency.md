---
issue_id: ISS-0053
epic_id: EP-0032
title: Add claude-pm-portfolio-manager as framework dependency
description: Add claude-pm-portfolio-manager as framework dependency for /cmpm-dashboard command integration
status: active
priority: medium
assignee: masa
created_date: 2025-07-09T13:51:38.602Z
updated_date: 2025-07-09T13:51:38.602Z
estimated_tokens: 0
actual_tokens: 0
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
related_tasks: []
related_issues: []
completion_percentage: 0
blocked_by: []
blocks: []
---

# Issue: Add claude-pm-portfolio-manager as framework dependency

## Description
**FRAMEWORK DEPENDENCY INTEGRATION - Add claude-pm-portfolio-manager as framework dependency**

This issue completes Epic EP-0032 by properly integrating the claude-pm-portfolio-manager as a framework dependency, enabling the `/cmpm-dashboard` command to reliably access and launch the portfolio manager dashboard.

## Technical Analysis Complete

**Current State:**
- Portfolio manager project exists at `/Users/masa/Projects/managed/claude-pm-portfolio-manager/`
- Framework package.json has dependency structure but missing portfolio manager
- Current dependency: `"@bobmatnyc/ai-trackdown-tools": "file:../managed/ai-trackdown-tools/bobmatnyc-ai-trackdown-tools-1.0.1.tgz"`
- `/cmpm-dashboard` command expects npm package access but package not properly integrated

**Integration Requirements:**
1. **Package Management Integration**: Add portfolio manager as proper framework dependency
2. **Path Resolution**: Update dependency path to point to portfolio manager package
3. **Package Build**: Ensure portfolio manager has proper dist/ build for npm consumption
4. **Command Integration**: Verify `/cmpm-dashboard` command can access package reliably

**Technical Implementation Strategy:**
- **Recommended Approach**: Create packaged `.tgz` file from portfolio manager project
- **Framework Integration**: Add as file dependency with proper path resolution
- **Command Verification**: Test `/cmpm-dashboard` command functionality post-integration

## Tasks
- [ ] **TSK-0053-001**: Analyze portfolio manager project build requirements
  - Verify package.json structure in `/Users/masa/Projects/managed/claude-pm-portfolio-manager/`
  - Check for proper dist/ build output
  - Validate package export compatibility
- [ ] **TSK-0053-002**: Create packaged dependency file
  - Generate `.tgz` package from portfolio manager project
  - Create `@bobmatnyc/claude-pm-portfolio-manager-1.0.0.tgz` file
  - Place in framework-accessible location
- [ ] **TSK-0053-003**: Update framework package.json dependency
  - Add `"@bobmatnyc/claude-pm-portfolio-manager": "file:../managed/claude-pm-portfolio-manager/dist/package.tgz"` to dependencies
  - Run `npm install` to verify dependency resolution
  - Validate package installation in node_modules/
- [ ] **TSK-0053-004**: Test `/cmpm-dashboard` command integration
  - Verify command can access portfolio manager package
  - Test headless browser launch functionality
  - Validate dashboard startup process
- [ ] **TSK-0053-005**: Document dependency integration process
  - Update framework documentation with dependency management
  - Create integration guide for future package additions
  - Document troubleshooting steps for dependency issues

## Acceptance Criteria
- [ ] **AC-0053-001**: Portfolio manager package is properly integrated as framework dependency
  - Package appears in framework package.json dependencies
  - Package successfully installs via `npm install`
  - Package accessible from framework code
- [ ] **AC-0053-002**: `/cmpm-dashboard` command functions reliably
  - Command can locate and launch portfolio manager dashboard
  - Headless browser launches successfully
  - Dashboard accessible on expected port
- [ ] **AC-0053-003**: Framework dependency management is standardized
  - Clear pattern established for managed project dependencies
  - Documentation updated for dependency integration process
  - Integration process reusable for future packages

## Technical Implementation Details

**Framework Files to Update:**
- `/Users/masa/Projects/claude-multiagent-pm/package.json` - Add portfolio manager dependency
- `/Users/masa/Projects/claude-multiagent-pm/claude_pm/cmpm_commands.py` - Verify package access logic
- Framework configuration files for package path resolution (if needed)

**Package Integration Options:**
1. **File Dependency (Recommended)**: `"@bobmatnyc/claude-pm-portfolio-manager": "file:../managed/claude-pm-portfolio-manager/dist/package.tgz"`
2. **Local Package**: Create local npm package with proper symlink
3. **Direct Path Reference**: Reference project directory with build verification

**Command Integration Points:**
- **CMPMDashboardLauncher.portfolio_manager_path**: Verify path resolution
- **start_dashboard_if_needed()**: Ensure package.json detection works
- **Package management**: Framework should handle dependency lifecycle

## Notes
**Epic EP-0032 Progress**: This issue completes the final component for Epic EP-0032, moving progress from 50% to 83% completion.

**Framework Authority**: This integration enables full dashboard orchestration capabilities within the Claude PM Framework.

**Testing Priority**: MEDIUM - Essential for `/cmpm-dashboard` command functionality but not blocking other framework operations.

**Engineering Coordination**: This issue requires engineering team analysis and implementation - PM orchestrator delegates technical execution to appropriate agents.
