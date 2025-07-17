---
issue_id: ISS-0120
title: "Fix startup script errors: Parent Directory Manager import failure"
description: |-
  The claude-pm startup script is failing with the following errors:

  1. Failed to import Parent Directory Manager: No module named 'claude_pm.services.parent_directory_manager'
  2. Framework may not be properly installed
  3. Auto-deployment failed - manual deployment required

  Error occurs when running claude-pm from ai-trackdown-tools directory.

  Stack trace:
  ❌ Failed to import Parent Directory Manager: No module named 'claude_pm.services.parent_directory_manager'
  💡 Framework may not be properly installed
  💭 This usually indicates the framework is not properly installed or accessible
  ❌ Auto-deployment failed - manual deployment required

  Expected behavior: The startup script should properly import all required modules and initialize the framework.
status: planning
priority: high
assignee: masa
created_date: 2025-07-17T20:09:20.287Z
updated_date: 2025-07-17T20:09:20.287Z
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
tags:
  - bug
  - startup
  - import-error
completion_percentage: 0
blocked_by: []
blocks: []
---

# Issue: Fix startup script errors: Parent Directory Manager import failure

## Description
The claude-pm startup script is failing with the following errors:

1. Failed to import Parent Directory Manager: No module named 'claude_pm.services.parent_directory_manager'
2. Framework may not be properly installed
3. Auto-deployment failed - manual deployment required

Error occurs when running claude-pm from ai-trackdown-tools directory.

Stack trace:
❌ Failed to import Parent Directory Manager: No module named 'claude_pm.services.parent_directory_manager'
💡 Framework may not be properly installed
💭 This usually indicates the framework is not properly installed or accessible
❌ Auto-deployment failed - manual deployment required

Expected behavior: The startup script should properly import all required modules and initialize the framework.

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
