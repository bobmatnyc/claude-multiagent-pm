---
issue_id: ISS-0116
title: Fix CLI binary deployment and PATH configuration for MacOS
description: |-
  Ensure claude-pm command works after NPM installation on MacOS without manual PATH configuration.

  Current Issue: Users cannot run claude-pm command after installation
  Root Cause: CLI binary not properly configured in package.json bin field or PATH issues

  Requirements:
  - Verify package.json "bin" field correctly maps to executable script
  - Ensure bin/claude-pm script has proper shebang and execution permissions
  - Test on MacOS npm global installation paths
  - Validate command works: claude-pm --version, claude-pm init

  Success Criteria: User can immediately run claude-pm commands after npm install
status: planning
priority: high
assignee: masa
created_date: 2025-07-15T01:25:45.815Z
updated_date: 2025-07-15T01:25:45.815Z
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

# Issue: Fix CLI binary deployment and PATH configuration for MacOS

## Description
Ensure claude-pm command works after NPM installation on MacOS without manual PATH configuration.

Current Issue: Users cannot run claude-pm command after installation
Root Cause: CLI binary not properly configured in package.json bin field or PATH issues

Requirements:
- Verify package.json "bin" field correctly maps to executable script
- Ensure bin/claude-pm script has proper shebang and execution permissions
- Test on MacOS npm global installation paths
- Validate command works: claude-pm --version, claude-pm init

Success Criteria: User can immediately run claude-pm commands after npm install

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
