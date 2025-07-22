---
issue_id: ISS-0115
title: Refactor Parent Directory Manager Service Design
description: >-
  ## Overview

  Refactor the Parent Directory Manager (claude_pm/services/parent_directory_manager.py - 2,075 lines)
  into a service-oriented design with specialized components for framework template management,
  deployment orchestration, and backup management.

  ## Problem Statement:

  The current Parent Directory Manager has grown to 2,075 lines, encompassing:
  - Framework template deployment logic (600+ lines)
  - Backup and protection mechanisms (400+ lines)
  - Configuration management (300+ lines)
  - Directory hierarchy management (200+ lines)
  - Version checking and validation (300+ lines)
  - Async service coordination (275+ lines)

  ## Service-Oriented Architecture:

  **Core Service Layer:**
  - `services/deployment/framework_deployer.py` - Template deployment and validation
  - `services/deployment/backup_manager.py` - Backup creation and rotation
  - `services/deployment/version_manager.py` - Version checking and compatibility
  - `services/deployment/directory_manager.py` - Directory structure management

  **Configuration Layer:**
  - `services/config/deployment_config.py` - Deployment configuration management
  - `services/config/template_resolver.py` - Template resolution and variable substitution
  - `services/config/hierarchy_manager.py` - Directory hierarchy coordination

  **Protection Layer:**
  - `services/protection/template_protector.py` - Framework template protection
  - `services/protection/integrity_validator.py` - System integrity validation
  - `services/protection/recovery_manager.py` - Recovery and rollback operations

  ## Implementation Plan:

  **Phase 1: Service Extraction (Days 1-2)**
  1. Extract framework deployment logic into dedicated service
  2. Separate backup management into standalone component
  3. Create version management service with clear interfaces

  **Phase 2: Configuration Refactoring (Days 2-3)**
  1. Modularize configuration management
  2. Separate template resolution logic
  3. Create hierarchy management service

  **Phase 3: Protection Layer (Days 3-4)**
  1. Extract template protection mechanisms
  2. Create integrity validation service
  3. Implement recovery management system

  **Phase 4: Integration (Day 5)**
  1. Create orchestrating service coordinator
  2. Implement service dependency injection
  3. Comprehensive testing and validation

  ## Success Criteria:

  - Parent Directory Manager reduced from 2,075 lines to <400 lines (coordinator)
  - Each service component <300 lines
  - Service interfaces clearly defined with dependency injection
  - All framework protection mechanisms preserved
  - Backup functionality maintained and improved
  - Template deployment performance improved by 20%+

  ## Dependencies:

  - Framework template protection is CRITICAL - must not be compromised
  - Backup rotation and integrity must be maintained
  - Version checking logic must remain robust
  - All existing deployment functionality preserved

  ## Testing Requirements:

  - Unit tests for each service component
  - Integration tests for service coordination
  - Protection mechanism validation tests
  - Backup and recovery testing
  - Template deployment end-to-end tests

  ## Reference:

  Based on codebase analysis identifying Parent Directory Manager as second highest
  complexity target with critical framework infrastructure responsibilities.

  ## Priority: High (Phase 1 - Critical Infrastructure)
status: pending
priority: high
assignee: masa
created_date: 2025-07-14T00:00:00.000Z
updated_date: 2025-07-14T00:00:00.000Z
estimated_tokens: 1000
actual_tokens: 0
ai_context:
  - context/service_architecture
  - context/deployment_management
  - context/framework_protection
  - context/backup_systems
sync_status: local
related_tasks: [EP-0041]
related_issues: [ISS-0114, ISS-0116, ISS-0117, ISS-0118]
completion_percentage: 0
blocked_by: [ISS-0114]
blocks: []
epic_id: EP-0041
effort_estimate: 5 days
complexity: high
impact: critical
---

# Issue: Refactor Parent Directory Manager Service Design

## Description
Refactor the Parent Directory Manager (claude_pm/services/parent_directory_manager.py - 2,075 lines) into a service-oriented design with specialized components for framework template management, deployment orchestration, and backup management.

## Problem Statement:
The current Parent Directory Manager has grown to 2,075 lines, encompassing:
- Framework template deployment logic (600+ lines)
- Backup and protection mechanisms (400+ lines)
- Configuration management (300+ lines)
- Directory hierarchy management (200+ lines)
- Version checking and validation (300+ lines)
- Async service coordination (275+ lines)

## Service-Oriented Architecture:

**Core Service Layer:**
- `services/deployment/framework_deployer.py` - Template deployment and validation
- `services/deployment/backup_manager.py` - Backup creation and rotation
- `services/deployment/version_manager.py` - Version checking and compatibility
- `services/deployment/directory_manager.py` - Directory structure management

**Configuration Layer:**
- `services/config/deployment_config.py` - Deployment configuration management
- `services/config/template_resolver.py` - Template resolution and variable substitution
- `services/config/hierarchy_manager.py` - Directory hierarchy coordination

**Protection Layer:**
- `services/protection/template_protector.py` - Framework template protection
- `services/protection/integrity_validator.py` - System integrity validation
- `services/protection/recovery_manager.py` - Recovery and rollback operations

## Implementation Plan:

**Phase 1: Service Extraction (Days 1-2)**
1. Extract framework deployment logic into dedicated service
2. Separate backup management into standalone component
3. Create version management service with clear interfaces

**Phase 2: Configuration Refactoring (Days 2-3)**
1. Modularize configuration management
2. Separate template resolution logic
3. Create hierarchy management service

**Phase 3: Protection Layer (Days 3-4)**
1. Extract template protection mechanisms
2. Create integrity validation service
3. Implement recovery management system

**Phase 4: Integration (Day 5)**
1. Create orchestrating service coordinator
2. Implement service dependency injection
3. Comprehensive testing and validation

## Success Criteria:
- Parent Directory Manager reduced from 2,075 lines to <400 lines (coordinator)
- Each service component <300 lines
- Service interfaces clearly defined with dependency injection
- All framework protection mechanisms preserved
- Backup functionality maintained and improved
- Template deployment performance improved by 20%+

## Dependencies:
- Framework template protection is CRITICAL - must not be compromised
- Backup rotation and integrity must be maintained
- Version checking logic must remain robust
- All existing deployment functionality preserved

## Testing Requirements:
- Unit tests for each service component
- Integration tests for service coordination
- Protection mechanism validation tests
- Backup and recovery testing
- Template deployment end-to-end tests

## Reference:
Based on codebase analysis identifying Parent Directory Manager as second highest complexity target with critical framework infrastructure responsibilities.

## Priority: High (Phase 1 - Critical Infrastructure)

## Tasks
- [ ] Extract framework deployment logic into dedicated service
- [ ] Create backup management standalone component
- [ ] Implement version management service with clear interfaces
- [ ] Modularize deployment configuration management
- [ ] Separate template resolution logic into dedicated service
- [ ] Create directory hierarchy coordination service
- [ ] Extract framework template protection mechanisms
- [ ] Create system integrity validation service
- [ ] Implement recovery and rollback management system
- [ ] Create orchestrating service coordinator
- [ ] Implement service dependency injection pattern
- [ ] Comprehensive testing of all service components
- [ ] Performance validation and optimization
- [ ] Integration testing of service coordination

## Acceptance Criteria
- [ ] Parent Directory Manager reduced to <400 lines (coordinator only)
- [ ] Each service component is <300 lines
- [ ] Service interfaces clearly defined with dependency injection
- [ ] All framework protection mechanisms preserved and functional
- [ ] Backup functionality maintained and improved
- [ ] Template deployment performance improved by 20%+
- [ ] All existing deployment functionality preserved
- [ ] Unit test coverage >90% for all service components
- [ ] Integration tests validate service coordination

## Notes
**CRITICAL**: This service manages framework template protection - the most critical aspect of the deployment system. Framework template corruption could affect all managed projects. Protection mechanisms must be preserved and thoroughly tested during refactoring.