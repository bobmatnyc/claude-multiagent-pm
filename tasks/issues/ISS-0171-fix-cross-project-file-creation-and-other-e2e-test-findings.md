---
issue_id: ISS-0171
title: Fix cross-project file creation and other E2E test findings
description: >-
  During E2E testing, several issues were discovered that need to be addressed:


  ## Critical Issues:

  1. **Cross-Project File Creation**: Files are being created in /Users/masa/Projects/claude-multiagent-pm/tasks/
  instead of the current project directory

  2. **YAML Parsing Warnings**: Multiple files missing required fields causing parse failures


  ## Improvements:

  1. **Comment Functionality**: Extend comments to work with epics and tasks, not just issues

  2. **Index Maintenance**: Implement proactive index health checks

  3. **File Naming**: Fix double dash (--) to single dash (-) inconsistency

  4. **Field Validation**: Add validation for required fields in legacy files


  ## Technical Details:

  - The CLI appears to be using a different project context than expected

  - This may be related to config file search or environment variable issues

  - Index auto-repair works but could be more efficient
status: planning
priority: high
assignee: masa
created_date: 2025-07-21T13:01:28.489Z
updated_date: 2025-07-21T13:01:28.489Z
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
  - enhancement
  - cli
completion_percentage: 0
blocked_by: []
blocks: []
---

# Issue: Fix cross-project file creation and other E2E test findings

## Description
During E2E testing, several issues were discovered that need to be addressed:

## Critical Issues:
1. **Cross-Project File Creation**: Files are being created in /Users/masa/Projects/claude-multiagent-pm/tasks/ instead of the current project directory
2. **YAML Parsing Warnings**: Multiple files missing required fields causing parse failures

## Improvements:
1. **Comment Functionality**: Extend comments to work with epics and tasks, not just issues
2. **Index Maintenance**: Implement proactive index health checks
3. **File Naming**: Fix double dash (--) to single dash (-) inconsistency
4. **Field Validation**: Add validation for required fields in legacy files

## Technical Details:
- The CLI appears to be using a different project context than expected
- This may be related to config file search or environment variable issues
- Index auto-repair works but could be more efficient

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
