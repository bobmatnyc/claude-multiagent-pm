---
issue_id: ISS-0075
title: Claude Code User Executable Commands Not Recognized
description: >-
  Investigation into Claude Code slash command integration revealed that user-defined executable shell scripts in
  ~/.claude/commands/ are not recognized by Claude Code. Only .md prompt files and built-in commands work.


  **Problem:**

  - Created executable shell scripts in ~/.claude/commands/ (cmpm-helper, test, etc.)

  - Scripts have proper permissions (chmod +x) and execute correctly when run directly

  - Scripts do not appear in Claude Code slash command list (/user:command-name)

  - Fresh Claude Code instances also do not recognize the executables


  **Root Cause:**

  Claude Code appears to only support two types of user commands:

  1. Markdown (.md) prompt files - Show up as conversational prompts

  2. Built-in executable commands - Part of Claude Code core (like /config, /doctor)


  **Current Workaround:**

  Using .md prompt files that instruct the AI to execute the underlying Python commands via Bash tool.


  **Files Investigated:**

  - ~/.claude/commands/cmpm-helper (executable, not recognized)

  - ~/.claude/commands/test (executable, not recognized) 

  - ~/.claude/commands/README.md (markdown, recognized as /user:README)


  **Expected Behavior:**

  User-defined executable scripts should appear in slash command list and execute directly like built-in commands.


  **Impact:**

  - Cannot create direct executable slash commands for CMPM framework

  - Must rely on conversational prompts instead of immediate execution

  - Affects user experience compared to built-in commands like /config
status: planning
priority: medium
assignee: masa
created_date: 2025-07-11T15:44:29.296Z
updated_date: 2025-07-11T15:44:29.296Z
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

# Issue: Claude Code User Executable Commands Not Recognized

## Description
Investigation into Claude Code slash command integration revealed that user-defined executable shell scripts in ~/.claude/commands/ are not recognized by Claude Code. Only .md prompt files and built-in commands work.

**Problem:**
- Created executable shell scripts in ~/.claude/commands/ (cmpm-helper, test, etc.)
- Scripts have proper permissions (chmod +x) and execute correctly when run directly
- Scripts do not appear in Claude Code slash command list (/user:command-name)
- Fresh Claude Code instances also do not recognize the executables

**Root Cause:**
Claude Code appears to only support two types of user commands:
1. Markdown (.md) prompt files - Show up as conversational prompts
2. Built-in executable commands - Part of Claude Code core (like /config, /doctor)

**Current Workaround:**
Using .md prompt files that instruct the AI to execute the underlying Python commands via Bash tool.

**Files Investigated:**
- ~/.claude/commands/cmpm-helper (executable, not recognized)
- ~/.claude/commands/test (executable, not recognized) 
- ~/.claude/commands/README.md (markdown, recognized as /user:README)

**Expected Behavior:**
User-defined executable scripts should appear in slash command list and execute directly like built-in commands.

**Impact:**
- Cannot create direct executable slash commands for CMPM framework
- Must rely on conversational prompts instead of immediate execution
- Affects user experience compared to built-in commands like /config

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
