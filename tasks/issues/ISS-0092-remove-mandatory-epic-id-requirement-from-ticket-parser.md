---
issue_id: ISS-0092
title: Remove mandatory epic_id requirement from ticket parser
description: >-
  Epic ID Requirement Bug in Ticket Parser


  Problem Description:

  The current ticket parser implementation requires both issue_id AND epic_id fields to be present for successful
  parsing. This is causing ticket creation failures when tickets are created without epic assignment.


  Current Impact:

  - 10 tickets currently failing parsing: ISS-0087 through ISS-0091 and other recent tickets

  - Parser throws errors when epic_id field is missing  

  - Prevents standalone ticket creation workflow

  - Forces artificial epic assignment for tickets that do not belong to epics


  Root Cause:

  The parser validation logic treats epic_id as a mandatory field rather than optional.


  Required Fix:

  1. Make epic_id field optional in ticket parser validation

  2. Allow tickets to exist without epic assignment initially

  3. Maintain ability to assign epics later via move/update operations

  4. Update parser schema to reflect optional epic_id field

  5. Add validation tests for tickets without epic_id


  Affected Components:

  - Ticket parser validation logic

  - Schema definitions for ticket structure

  - Ticket creation workflows

  - Epic assignment operations


  Expected Behavior After Fix:

  - Tickets can be created with just issue_id

  - Epic assignment remains available but optional

  - Existing epic-assigned tickets continue working

  - Failed tickets (ISS-0087 through ISS-0091) can be successfully parsed


  Priority Justification:

  - System bug affecting active operations

  - 10 tickets currently inaccessible

  - Blocks normal ticket workflow

  - Simple fix with significant operational impact


  Testing Requirements:

  - Verify tickets can be created without epic_id

  - Confirm existing epic-assigned tickets still work

  - Test epic assignment via update operations

  - Validate parser handles both scenarios correctly
status: planning
priority: high
assignee: masa
created_date: 2025-07-13T22:01:14.484Z
updated_date: 2025-07-13T22:01:14.484Z
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
  - parser
  - system
  - high-priority
completion_percentage: 0
blocked_by: []
blocks: []
---

# Issue: Remove mandatory epic_id requirement from ticket parser

## Description
Epic ID Requirement Bug in Ticket Parser

Problem Description:
The current ticket parser implementation requires both issue_id AND epic_id fields to be present for successful parsing. This is causing ticket creation failures when tickets are created without epic assignment.

Current Impact:
- 10 tickets currently failing parsing: ISS-0087 through ISS-0091 and other recent tickets
- Parser throws errors when epic_id field is missing  
- Prevents standalone ticket creation workflow
- Forces artificial epic assignment for tickets that do not belong to epics

Root Cause:
The parser validation logic treats epic_id as a mandatory field rather than optional.

Required Fix:
1. Make epic_id field optional in ticket parser validation
2. Allow tickets to exist without epic assignment initially
3. Maintain ability to assign epics later via move/update operations
4. Update parser schema to reflect optional epic_id field
5. Add validation tests for tickets without epic_id

Affected Components:
- Ticket parser validation logic
- Schema definitions for ticket structure
- Ticket creation workflows
- Epic assignment operations

Expected Behavior After Fix:
- Tickets can be created with just issue_id
- Epic assignment remains available but optional
- Existing epic-assigned tickets continue working
- Failed tickets (ISS-0087 through ISS-0091) can be successfully parsed

Priority Justification:
- System bug affecting active operations
- 10 tickets currently inaccessible
- Blocks normal ticket workflow
- Simple fix with significant operational impact

Testing Requirements:
- Verify tickets can be created without epic_id
- Confirm existing epic-assigned tickets still work
- Test epic assignment via update operations
- Validate parser handles both scenarios correctly

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
