---
issue_id: ISS-0074
title: Fix aiohttp session cleanup in health monitoring system
description: >-
  **Problem:**

  The CMPM health monitoring system creates unclosed aiohttp sessions during service health checks, causing connection
  leaks and timeout warnings.


  **Root Cause:**

  1. Framework services collector creates MemoryService() and ProjectService() instances during health checks

  2. Services initialize aiohttp sessions in __init__ but cleanup is incomplete

  3. ClaudePMMemory.disconnect() only sets session to None without actually closing connections

  4. Multiple service instances created without proper singleton pattern


  **Current Impact:**

  - Health command shows 'Unclosed client session' warnings

  - Connection leaks consume system resources

  - Framework Core status shows DEGRADED (75% reliability)


  **Solution Required:**

  1. Implement singleton service startup process

  2. Fix ClaudePMMemory session cleanup to actually close connections

  3. Ensure proper service lifecycle management in health collectors

  4. Add proper session cleanup in connection manager


  **Technical Details:**

  - Files affected: claude_pm/collectors/framework_services.py, claude_pm/services/memory_service.py

  - Error location: Framework services collector lines 188, 211

  - Cleanup added but session.close() not being called properly


  **Priority:** High - affects system reliability and resource management
status: planning
priority: high
assignee: masa
created_date: 2025-07-11T15:24:18.926Z
updated_date: 2025-07-11T15:24:18.926Z
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

# Issue: Fix aiohttp session cleanup in health monitoring system

## Description
**Problem:**
The CMPM health monitoring system creates unclosed aiohttp sessions during service health checks, causing connection leaks and timeout warnings.

**Root Cause:**
1. Framework services collector creates MemoryService() and ProjectService() instances during health checks
2. Services initialize aiohttp sessions in __init__ but cleanup is incomplete
3. ClaudePMMemory.disconnect() only sets session to None without actually closing connections
4. Multiple service instances created without proper singleton pattern

**Current Impact:**
- Health command shows 'Unclosed client session' warnings
- Connection leaks consume system resources
- Framework Core status shows DEGRADED (75% reliability)

**Solution Required:**
1. Implement singleton service startup process
2. Fix ClaudePMMemory session cleanup to actually close connections
3. Ensure proper service lifecycle management in health collectors
4. Add proper session cleanup in connection manager

**Technical Details:**
- Files affected: claude_pm/collectors/framework_services.py, claude_pm/services/memory_service.py
- Error location: Framework services collector lines 188, 211
- Cleanup added but session.close() not being called properly

**Priority:** High - affects system reliability and resource management

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Notes
Add any additional notes here.
