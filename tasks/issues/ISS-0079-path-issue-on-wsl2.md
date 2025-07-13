---
issue_id: ISS-0079
title: PATH issue on WSL2
description: |-
  NPM installation succeeds but claude-pm fails to launch Claude CLI on WSL2 with PATH issues.

  **Error Output:**
  ```
  adminuser@GSI-LR914P78B:~/projects$ npm install -g @bobmatnyc/claude-multiagent-pm

  added 7 packages, and changed 171 packages in 11s

  42 packages are looking for funding
    run `npm fund` for details
  adminuser@GSI-LR914P78B:~/projects$ cd pm-test/
  adminuser@GSI-LR914P78B:~/projects/pm-test$ claude-pm

  ======================================================================
  🚀 CLAUDE PM FRAMEWORK - SYSTEM INFORMATION
  ======================================================================
  📅 System Status as of 2025-07-13

  📦 Claude PM Framework Version: v0.5.4
  📁 Install Path: /home/adminuser/.nvm/versions/node/v24.3.0/lib/node_modules/@bobmatnyc/claude-multiagent-pm
  📂 Working Path: /home/adminuser/projects/pm-test
  /bin/sh: 1: aitrackdown: not found
  🔍 AI-trackdown-tools Version: Not installed or not accessible
  ⚙️  Install Type: Global NPM Installation
  🧠 Memory: Unable to determine status
  📄 User CLAUDE.md: not in working path

  ======================================================================
  🎯 Launching Claude with optimized settings...
  ======================================================================

  ❌ Failed to launch Claude: spawn claude ENOENT
  Make sure Claude CLI is installed and available in your PATH
  ```

  **Note:** Running Claude normally works fine

  **GitHub Issue:** #1
  **Created:** 2025-07-13T02:38:36Z
  **Reporter:** External user
  **Priority:** High - blocks WSL2 users

  🤖 Synced from GitHub Issues
status: planning
priority: high
assignee: masa
created_date: 2025-07-13T18:59:59.044Z
updated_date: 2025-07-13T18:59:59.044Z
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

# Issue: PATH issue on WSL2

## Description
NPM installation succeeds but claude-pm fails to launch Claude CLI on WSL2 with PATH issues.

**Error Output:**
```
adminuser@GSI-LR914P78B:~/projects$ npm install -g @bobmatnyc/claude-multiagent-pm

added 7 packages, and changed 171 packages in 11s

42 packages are looking for funding
  run `npm fund` for details
adminuser@GSI-LR914P78B:~/projects$ cd pm-test/
adminuser@GSI-LR914P78B:~/projects/pm-test$ claude-pm

======================================================================
🚀 CLAUDE PM FRAMEWORK - SYSTEM INFORMATION
======================================================================
📅 System Status as of 2025-07-13

📦 Claude PM Framework Version: v0.5.4
📁 Install Path: /home/adminuser/.nvm/versions/node/v24.3.0/lib/node_modules/@bobmatnyc/claude-multiagent-pm
📂 Working Path: /home/adminuser/projects/pm-test
/bin/sh: 1: aitrackdown: not found
🔍 AI-trackdown-tools Version: Not installed or not accessible
⚙️  Install Type: Global NPM Installation
🧠 Memory: Unable to determine status
📄 User CLAUDE.md: not in working path

======================================================================
🎯 Launching Claude with optimized settings...
======================================================================

❌ Failed to launch Claude: spawn claude ENOENT
Make sure Claude CLI is installed and available in your PATH
```

**Note:** Running Claude normally works fine

**GitHub Issue:** #1
**Created:** 2025-07-13T02:38:36Z
**Reporter:** External user
**Priority:** High - blocks WSL2 users

🤖 Synced from GitHub Issues

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
