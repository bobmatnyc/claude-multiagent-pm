# Changelog

All notable changes to the Claude Multi-Agent PM Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-07-18

### Fixed
- Critical npm postinstall issue: Missing Python dependencies (python-frontmatter, mistune)
- Added automatic dependency installation to npm postinstall process
- Added recovery script (scripts/install_missing_dependencies.py) for existing installations
- Added comprehensive troubleshooting documentation for common issues

## [1.2.0] - 2025-07-18

### Added
- Base agent instructions system (base_agent.md) for shared agent capabilities
- BaseAgentManager API for structured updates to base agent instructions
- Enhanced agent loader with base instruction prepending
- Agent management service for centralized agent operations
- Agent versioning system for tracking changes
- PM Orchestrator Agent role for multi-agent coordination
- New documentation structure with improved organization
- Test directory reorganization for better test categorization

### Changed
- Updated ticketing agent requirements to include aitrackdown integration
- Enhanced agent loader to support base agent instructions
- Improved agent management with hierarchical loading support
- Reorganized documentation into user/, technical/, and releases/ directories
- Reorganized test suite into unit/, integration/, e2e/, and fixtures/ directories

### Fixed
- Agent discovery issues from v1.0.1
- Import errors and undefined variables in setup commands
- ParentDirectoryManager import errors in auto-deployment

## [1.0.1] - 2025-07-18

### Fixed
- Agent discovery issues for production deployment

## [1.0.0] - 2025-07-18

### Added
- Major architectural improvements and optimizations
- Robust subprocess creation and environment handling for agent delegation
- LOCAL orchestration as default mode for instant agent responses

### Changed
- Default orchestration mode to LOCAL for better performance

### Fixed
- Unnecessary operations in agent responses
- Duplicate CLAUDE.md deployments in directory hierarchy
- Framework path detection for external project deployments
- Import errors and undefined variable issues in setup commands
- ParentDirectoryManager import error in auto-deployment
- Manager existence check in setup_commands.py

[1.2.0]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.0.1...v1.2.0
[1.0.1]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/bobmatnyc/claude-multiagent-pm/releases/tag/v1.0.0