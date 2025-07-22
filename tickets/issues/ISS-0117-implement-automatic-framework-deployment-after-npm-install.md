---
issue_id: ISS-0117
title: Implement automatic framework deployment after NPM install
description: |-
  Create postinstall script that sets up .claude-pm directories and configuration automatically.

  Scope:
  - Create .claude-pm directory structure in user home and project directories
  - Initialize framework configuration files
  - Set up agent hierarchy (project → user → system)
  - Copy necessary framework files to user locations
  - Provide clear success/failure feedback to user

  Integration: Works with postinstall script from package.json ticket
  Platform: MacOS focus initially, Windows/Linux later
  User Experience: Silent success with clear error messages if issues occur
status: planning
priority: high
assignee: masa
created_date: 2025-07-15T01:25:46.112Z
updated_date: 2025-07-15T01:25:46.112Z
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

# Issue: Implement automatic framework deployment after NPM install

## Description
Create postinstall script that sets up .claude-pm directories and configuration automatically.

Scope:
- Create .claude-pm directory structure in user home and project directories
- Initialize framework configuration files
- Set up agent hierarchy (project → user → system)
- Copy necessary framework files to user locations
- Provide clear success/failure feedback to user

Integration: Works with postinstall script from package.json ticket
Platform: MacOS focus initially, Windows/Linux later
User Experience: Silent success with clear error messages if issues occur

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
