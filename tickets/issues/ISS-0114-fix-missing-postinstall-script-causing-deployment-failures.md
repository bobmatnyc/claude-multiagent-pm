---
issue_id: ISS-0114
title: Fix missing postinstall script causing deployment failures
description: >-
  Users getting "No postinstall script found" and "Post-install setup failed\!" after NPM installation.


  Issue: The package.json is missing a postinstall script that should automatically setup the framework after
  installation.


  Impact: Critical - blocking all new users from successfully installing and using claude-pm on MacOS.


  Steps to Reproduce:

  1. Run: npm install -g @bobmatnyc/claude-multiagent-pm

  2. See "No postinstall script found" error

  3. Framework deployment fails


  Expected: Post-install should automatically setup .claude-pm directories and configuration


  Focus: MacOS compatibility only for rapid fixes
status: planning
priority: critical
assignee: masa
created_date: 2025-07-15T01:25:45.264Z
updated_date: 2025-07-15T01:25:45.264Z
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

# Issue: Fix missing postinstall script causing deployment failures

## Description
Users getting "No postinstall script found" and "Post-install setup failed\!" after NPM installation.

Issue: The package.json is missing a postinstall script that should automatically setup the framework after installation.

Impact: Critical - blocking all new users from successfully installing and using claude-pm on MacOS.

Steps to Reproduce:
1. Run: npm install -g @bobmatnyc/claude-multiagent-pm
2. See "No postinstall script found" error
3. Framework deployment fails

Expected: Post-install should automatically setup .claude-pm directories and configuration

Focus: MacOS compatibility only for rapid fixes

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
