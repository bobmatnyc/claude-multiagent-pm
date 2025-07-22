---
epic_id: EP-0037
title: Robust Mac Installation System with Advanced Flags
description: Comprehensive installer system that downloads all components (scripts, templates, agents) to unified location with advanced flag support and Mac-specific optimizations
status: active
priority: high
assignee: masa
created_date: 2025-07-14T00:24:13.279Z
updated_date: 2025-07-14T00:24:13.279Z
estimated_tokens: 15000
actual_tokens: 0
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
related_issues: [ISS-0079, ISS-0080, ISS-0081, ISS-0091]
dependencies: []
completion_percentage: 0
---

# Epic: Robust Mac Installation System with Advanced Flags

## Overview
Comprehensive installer system that downloads all components (scripts, templates, agents) to unified location with advanced flag support and Mac-specific optimizations. This epic consolidates multiple installation enhancement tickets and follows the SuperClaude installer pattern for reference architecture.

## Strategic Context
- Consolidates multiple installation enhancement tickets
- Follows SuperClaude installer pattern for reference architecture
- Mac-only focus initially for robust implementation
- Foundation for cross-platform expansion

## Core Installation Architecture

### Unified Installation System
- NPM installer downloads all components to single unified location (`~/.claude-pm/`)
- claude-pm command acts as primary installer (similar to SuperClaude pattern)
- Platform detection with Mac-specific optimizations
- Unified component management (scripts, templates, agents)

### Advanced Flag Support
- `--update`: Update installation including NPM packages
- `--safe`: Non-YOLO mode with comprehensive safety checks
- `--version`: Display current version and component information
- `--rollback`: Rollback to previous stable version
- `--verify`: Comprehensive installation verification and health checks
- `--debug`: Verbose output for troubleshooting
- `--force`: Override safety checks when necessary

## Implementation Phases

### Phase 1: Foundation Architecture (EP-0037-P1)
- Design unified installation location structure
- Implement platform detection (Mac focus)
- Create base installer framework
- Basic flag parsing infrastructure

### Phase 2: Core Installation System (EP-0037-P2)
- NPM package download and extraction
- Script deployment with proper permissions
- Template system integration
- Agent hierarchy setup

### Phase 3: Advanced Flags Implementation (EP-0037-P3)
- Update mechanism with dependency management
- Safe mode with interactive confirmations
- Version tracking and display
- Verification system with health checks

### Phase 4: Hardening and Rollback (EP-0037-P4)
- Rollback system with state snapshots
- Installation integrity validation
- Error recovery mechanisms
- Performance optimization

### Phase 5: Testing and Polish (EP-0037-P5)
- Comprehensive test suite
- Documentation updates
- Performance benchmarking
- User experience refinements

## Objectives
- [ ] Create unified installation location (`~/.claude-pm/`)
- [ ] Implement NPM-based component download system
- [ ] Develop advanced flag architecture with inheritance
- [ ] Build Mac-specific optimizations and platform detection
- [ ] Create rollback system with state snapshots
- [ ] Implement safe mode with interactive confirmations
- [ ] Develop comprehensive verification and health checks
- [ ] Achieve >95% installation success rate
- [ ] Ensure 100% rollback success rate
- [ ] Reduce installation support tickets by 80%

## Acceptance Criteria

### Installation Experience
- [ ] Single command installation: `npm install -g @bobmatnyc/claude-pm`
- [ ] Post-install script automatically sets up environment
- [ ] All components deployed to unified location
- [ ] Proper PATH configuration and command availability

### Flag Functionality
- [ ] `--update` updates all components including NPM packages
- [ ] `--safe` mode requires confirmations for destructive operations
- [ ] `--version` shows detailed component versions
- [ ] `--rollback` restores previous working state
- [ ] `--verify` validates complete installation integrity

### Mac Platform Support
- [ ] Xcode Command Line Tools detection
- [ ] Homebrew integration when available
- [ ] macOS version compatibility checks
- [ ] Proper permissions handling

### Robustness Features
- [ ] Installation state tracking
- [ ] Automatic backup before updates
- [ ] Graceful failure handling with recovery options
- [ ] Comprehensive logging and diagnostics

## Technical Requirements

### Installation Location Structure
```
~/.claude-pm/
├── bin/           # Executable scripts
├── templates/     # Configuration templates
├── agents/        # Agent implementations
├── config/        # Configuration files
├── state/         # Installation state tracking
├── backups/       # Rollback snapshots
└── logs/          # Installation logs
```

### Flag Architecture
- Consistent flag parsing across all commands
- Flag inheritance from global to local scope
- Environment variable support for defaults
- Configuration file integration

### Safety Mechanisms
- Pre-flight checks before operations
- State snapshots before changes
- Rollback validation
- Safe mode confirmations

## Related Issues
- **ISS-0079**: Implement Robust Installer Architecture with Platform Detection
  - Platform detection (macOS, Linux, WSL)
  - Dependency validation and checking
  - Backup creation with timestamping
  - Rollback functionality and progress tracking

- **ISS-0080**: ~~Implement @include Template System for Configuration Management~~ **[CLOSED - WON'T DO]**
  - ~~Template directory structure and processor~~
  - ~~@include directive processor with recursive resolution~~
  - ~~Variable substitution engine~~
  - ~~Template validation framework and caching~~
  - **Closure Reason**: Technical research proved @include directives have 0% reliability with Claude

- **ISS-0081**: Implement Universal Flag Inheritance Architecture
  - Performance & debugging flags (--verbose, --quiet, --dry-run, --force)
  - Agent & workflow control flags (--agent-priority, --parallel, --checkpoint)
  - Context & memory flags (--memory-enhanced, --context-preserve)
  - Flag inheritance hierarchy: Global → Command → User → Project → Runtime

- **ISS-0091**: Address Dirk's Installation and Usage Questions
  - User feedback and requirements gathering
  - Installation pain points and improvement areas
  - Documentation gaps and clarity issues

## Phase-Issue Mapping
- **Phase 1 (Foundation)**: ISS-0079 (Installer Architecture), ISS-0080 (Template System), ISS-0081 (Flag Architecture)
- **Phase 2 (Core System)**: Component integration and NPM package system
- **Phase 3 (Advanced Flags)**: Flag implementation with inheritance
- **Phase 4 (Hardening)**: Rollback system and integrity validation
- **Phase 5 (Polish)**: Testing, documentation, user experience (ISS-0091 feedback)

## Dependencies
- NPM package publishing infrastructure
- ~~Template system (@include functionality)~~ **[REMOVED - NOT VIABLE]**
- Agent hierarchy system (proven alternative to @include)
- Version control integration
- CLAUDE.md hierarchy system (reliable alternative to @include)

## Success Metrics
- Installation success rate > 95%
- Update mechanism reliability > 98%
- Rollback success rate = 100%
- User satisfaction with installation experience
- Reduced support tickets for installation issues

## Timeline Estimate
- **Phase 1-2**: 2-3 weeks (Foundation + Core System)
- **Phase 3-4**: 2-3 weeks (Flags + Hardening)
- **Phase 5**: 1-2 weeks (Testing + Polish)
- **Total**: 5-8 weeks for complete implementation

## Risk Mitigation
- Platform-specific testing on multiple Mac versions
- Rollback testing with various failure scenarios
- Performance testing with large installations
- Security review of installation permissions

## Notes
This epic represents a major enhancement to the Claude PM Framework installation experience, providing users with a robust, reliable, and feature-rich installation system. The epic consolidates multiple enhancement tickets and creates a foundation for future cross-platform expansion.
