---
task_id: TSK-0037
issue_id: ISS-0167
epic_id: EP-0001
title: Update base agent with correct comment syntax for agents
description: Task description
status: completed
priority: high
assignee: masa
created_date: 2025-07-20T05:41:02.881Z
updated_date: 2025-07-20T05:41:02.881Z
estimated_tokens: 0
actual_tokens: 0
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
subtasks: []
blocked_by: []
blocks: []
---

# Task: Update base agent with correct comment syntax for agents

## Description
Updated the base agent file with correct aitrackdown comment syntax to prevent CLI errors when agents attempt to add comments to tickets.

## Steps
1. Added explicit examples of correct `aitrackdown comment add` syntax with `-b` flag
2. Included common error scenarios showing what NOT to do
3. Added ticket comment templates for different scenarios (start, progress, completion, failure)
4. Included debugging tips for common CLI errors
5. Updated ticket format to support both ISS-XXXX and TSK-XXXX formats

## Acceptance Criteria
- [x] Base agent file includes correct aitrackdown comment syntax examples
- [x] Common error scenarios are documented with clear "DO NOT" examples
- [x] Multi-line comment formatting is explained
- [x] Debugging tips for CLI errors are provided
- [x] Both ISS-XXXX and TSK-XXXX ticket formats are supported

## Notes
File modified: `/Users/masa/Projects/claude-multiagent-pm/claude_pm/data/framework/agent-roles/base_agent.md`

The aitrackdown CLI requires specific syntax:
- Always use `comment add` (not just `comment`)
- Always include `-b` flag before the comment body
- Always quote the comment text properly
- Use `\n` for line breaks within quotes
