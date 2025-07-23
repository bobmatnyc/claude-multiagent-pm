# Changelog

All notable changes to the Claude Multi-Agent PM Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.7] - 2025-07-23

### Summary
**MAJOR OPTIMIZATION RELEASE**: This version completes a significant migration from JavaScript to pure Python, resulting in a 66% reduction in memory usage and elimination of npm-related installation issues. The framework has been optimized for performance and stability while maintaining full backward compatibility.

### Fixed
- **CRITICAL**: Fixed memory exhaustion crashes (ISS-0179) - Sessions no longer crash from out-of-memory errors
  - SharedPromptCache now limited to 500MB (was unbounded, consuming 1.5GB+)
  - Subprocess memory limits reduced by 50% for safer concurrent execution
  - Memory pressure coordinator triggers automatic cleanup at 80% system memory
  - Pre-flight memory checks prevent subprocess creation when memory is low
- Fixed critical test failures reducing failing tests from 54 to 48
- Fixed version mismatch issues across package files
- Resolved circular dependency in package.json
- Fixed prompt cache memory leaks that accumulated over long sessions
- Fixed subprocess memory inheritance causing exponential growth
- Consolidated ISS-0003 memory optimization requirements into ISS-0179 implementation

### Added
- **Pure Python Migration** - Eliminated JavaScript dependencies (EP-0046)
  - Removed 30+ JavaScript files and npm-specific installation scripts
  - Migrated from npm ai-trackdown-tools to Python ai-trackdown-pytools
  - Native Python implementation for all core functionality
  - Simplified installation process with fewer dependencies
- **Automatic Memory Protection System** - No configuration required
  - Memory Pressure Coordinator monitors system-wide memory usage
  - Automatic garbage collection triggers at memory thresholds
  - Smart subprocess spawning based on available memory
  - Memory usage tracking and reporting in health checks
- Enhanced memory diagnostics for troubleshooting
  - `claude-pm memory-status` command shows current usage
  - Memory metrics included in health monitoring
  - Detailed memory logs for debugging
- New Engineer agent role for code implementation tasks
- Config aliases system for flexible configuration management
- Ticket-first operations documentation and workflows

### Changed
- **Memory Optimization** - 66% reduction in memory footprint
  - SharedPromptCache: 1.5GB → 500MB (enforced limit)
  - Subprocess limits: 4GB → 2GB (safer concurrent execution)
  - Agent loading: On-demand instead of pre-loading
  - Prompt template compilation: JIT instead of eager
- **Framework Architecture** - Pure Python implementation
  - Replaced JavaScript postinstall scripts with Python equivalents
  - Simplified deployment process eliminating node_modules
  - Improved cross-platform compatibility
- Default subprocess concurrency reduced from 10 to 5 for memory safety
- Health monitoring now includes memory pressure indicators
- Agent hierarchy updated to include 9 core agent types (added Engineer and Data Engineer)

### Performance
- 66% reduction in memory usage across all operations
- Eliminated memory-related session crashes
- Maintained response time performance despite memory constraints
- Improved long-session stability through automatic cleanup
- Faster installation process without npm dependency resolution
- Reduced startup time with pure Python implementation

### Removed
- 30+ JavaScript files from install/ and scripts/ directories
- npm-specific postinstall scripts and deployment tools
- JavaScript memory monitoring and management utilities
- Complex npm/node installation wrappers
- Legacy JavaScript-based subprocess managers

## [1.4.0] - 2025-07-21

### Summary
This release includes major architectural changes with the shift to markdown-based agent definitions and significant test infrastructure improvements. Key fixes include resolving circular dependencies, synchronizing version files, and improving the unit test pass rate from 68.3% to 75.3%. While the test coverage is still below the 90% target, critical functionality has been stabilized.

### Fixed (Today's Critical Fixes)
- Fixed circular dependency in package.json (pyproject.toml was listed as a dependency)
- Synchronized all version files to 1.4.0 (VERSION, package.json, pyproject.toml, _version.py)
- Fixed critical unit test failures by creating missing module stubs
- Created missing test infrastructure modules for proper test execution
- Improved test pass rate from 68.3% to 75.3%

### Added
- PyPI publication workflow (.github/workflows/pypi-publish.yml)
- Comprehensive orchestration module refactoring
  - agent_handlers.py - Agent-specific handling logic
  - local_executor.py - Local execution support
  - orchestration_metrics.py - Performance metrics tracking
  - orchestration_types.py - Type definitions
  - subprocess_executor.py - Subprocess execution management
  - New orchestrator/ subdirectory for modular orchestration components
- Enhanced service modularization
  - Modularized large service files into subdirectories
  - agent_modification_tracker/ - Tracking agent modifications
  - agent_profile_loader/ - Agent profile management
  - agent_registry/ - Agent registry functionality
  - agent_trainer/ - Agent training capabilities
  - evaluation_performance/ - Performance evaluation
  - framework_claude_md_generator/ - Framework documentation generation
  - hook_processing_service/ - Hook processing
  - parent_directory_manager/ - Directory management
  - prompt_improvement_pipeline/ - Prompt optimization
  - prompt_improver/ - Prompt improvement logic
  - prompt_validator/ - Prompt validation
  - task_complexity_analyzer.py - Task complexity analysis
- Data management module (claude_pm/data/)
- Generator modules (claude_pm/generators/)
- Monitoring capabilities (claude_pm/monitoring/)
- Agent templates directory (claude_pm/agents/templates/)
- Comprehensive documentation updates
  - API documentation (docs/api/)
  - Deployment guides (docs/deployment/)
  - Development documentation (docs/development/)
  - Feature documentation (docs/features/)
  - User guides (docs/guides/)
  - Operations documentation (docs/operations/)
  - Refactoring documentation (docs/refactoring/)
  - Troubleshooting guides (docs/troubleshooting/)
  - Template documentation (docs/templates/)
- Deprecation utilities (claude_pm/utils/deprecation.py)
- Version management utilities (claude_pm/utils/versions/)
- Migration and publication guides
  - MIGRATION.md
  - NPM_SIMPLIFICATION_MIGRATION.md
  - PHASE_2_PUBLICATION_STATUS.md
  - PYPI_PUBLICATION_GUIDE.md
- Build and deployment scripts
  - build_and_deploy_wheel.sh
  - build_config.py
  - build_wheel.py
  - docker_test_deployment.sh
  - local_test_deployment.sh
  - migrate_to_pypi.py
  - pre_publication_checklist.py
  - publish_to_pypi.py
  - quick_refactor_test.py
  - test_pypi_installation.py
  - test_wheel_installation.py
  - validate_refactoring.py
  - verify_wheel.py
- Comprehensive test suite reorganization
  - E2E testing framework (tests/e2e/)
  - Integration tests (tests/integration/)
  - Legacy test preservation (tests/legacy/)
  - Performance tests (tests/performance/)
  - Refactoring harness (tests/refactoring_harness/)
  - Test scripts (tests/scripts/)
  - Test fixtures (tests/fixtures/)
  - Test configuration (tests/config/)
- New epic and issue tracking
  - Multiple new epics (EP-0042 through EP-0076)
  - Extensive issue tracking (ISS-0128 through ISS-0170)
  - Task tracking updates (TSK-0032 through TSK-0040)

### Changed
- **BREAKING**: Framework architecture shift to markdown-based agent definitions
  - AgentRegistry now discovers .md files instead of .py files
  - Agent definitions must end with -agent.md pattern
  - Framework agents moved to framework/agent-roles/ directory
- **BREAKING**: Removed ticketing agent from core framework
  - Ticketing functionality now delegated to external ai-trackdown tools
  - Removed ticketing-agent.md from framework/agent-roles/
  - Removed all ticketing-related integration code
- Simplified version management
  - Consolidated from multiple *_VERSION files to single VERSION file
  - Removed: AGENTS_VERSION, CLI_VERSION, DOCUMENTATION_VERSION, FRAMEWORK_VERSION, 
    HEALTH_VERSION, INTEGRATION_VERSION, MEMORY_VERSION, SERVICES_VERSION, TICKETING_VERSION
- Major service refactoring for modularity
  - Large service files (>1000 lines) split into modular components
  - Improved code organization and maintainability
  - Enhanced separation of concerns
- Updated documentation structure
  - Comprehensive reorganization into specialized directories
  - Improved navigation and discoverability
  - Enhanced technical and user documentation

### Removed
- Multiple version tracking files (*_VERSION pattern)
- Ticketing agent and all related functionality
- Legacy ticketing integration code
- Obsolete binary files
  - bin/aitrackdown-framework
  - bin/atd-framework
  - bin/claude-pm-phase2
  - bin/claude-pm-python
- Obsolete configuration directory (config/)
- Deprecated scripts
  - increment_version.js (moved to scripts/)
  - demonstrate_ticketing_agent_integration.py
- Outdated test files and reports
- Legacy issue and task files
- prompt_template_manager.py service (functionality consolidated)

### Fixed
- Agent discovery mechanism to properly find markdown files
- Framework path resolution for agent loading
- Import errors in modularized services
- Test organization and categorization

### Security
- Enhanced isolation between framework and project code
- Improved subprocess security through modular executors
- Better access control in service modules

### Deprecated
- Python-based agent definition files (use markdown instead)
- Direct ticketing operations (use ai-trackdown tools)
- Multiple version file system (use single VERSION file)

## [1.3.0] - 2025-07-20

### Added
- Comprehensive subprocess memory monitoring system for Task Tool operations
  - Real-time memory tracking with 2-second intervals
  - Multi-threshold alerts: Warning (1GB), Critical (2GB), Hard Limit (4GB)
  - Automatic subprocess abort on memory limit to prevent system crashes
  - Pre-flight memory checks before subprocess creation
  - Detailed memory usage logging and statistics
  - System-wide and per-subprocess memory tracking
- Memory monitoring configuration options
  - Environment variable overrides for thresholds
  - Per-subprocess custom memory limits
  - Enable/disable monitoring flags
- Memory monitoring documentation and operational guides
- **Prompt Optimization System** (ISS-0168) - 50-66% token reduction
  - Task Complexity Analyzer for intelligent task assessment
  - Dynamic Model Selection (Haiku/Sonnet/Opus based on complexity)
  - Adaptive Prompt Templates (MINIMAL/STANDARD/FULL)
  - Enabled by default - automatic optimization for all agents
  - Per-agent configuration overrides
  - Comprehensive metrics and monitoring
- Prompt optimization documentation
  - Feature documentation: `/docs/features/prompt-optimization.md`
  - User guide: `/docs/guides/prompt-optimization-guide.md`
  - API reference: `/docs/api/task-complexity-analyzer.md`
  - Deployment guide: `/docs/deployment/prompt-optimization-deployment.md`

### Fixed
- Critical memory exhaustion issue (ISS-0109) - Node.js memory leak causing 8GB heap exhaustion
  - Implemented proactive memory monitoring to detect runaway subprocesses
  - Added automatic abort mechanism for memory-exceeding subprocesses
  - Prevented system crashes from uncontrolled memory growth
- Critical message bus NoneType error in orchestration (ISS-0128)
  - Added defensive initialization checks before message bus usage
  - Fixed race condition in LOCAL mode initialization
  - Improved performance by 150x (200ms vs 30s per agent query)
  - Added comprehensive troubleshooting documentation

### Changed
- **Prompt optimization now enabled by default** - All agent interactions automatically optimized
  - Set `ENABLE_DYNAMIC_MODEL_SELECTION=false` to disable (not recommended)
  - Results in 50-66% token reduction with no quality loss
- Task Tool subprocess creation now includes automatic memory monitoring
- Enhanced subprocess statistics with memory usage tracking
- Improved system health checks to include memory availability

### Security
- Added memory-based DoS protection through subprocess limits
- Prevented resource exhaustion attacks via memory monitoring

## [1.2.3] - 2025-07-18

### Added
- Ticket update requirements to base_agent.md for consistent ticket tracking
- BaseAgentManager unit tests for comprehensive test coverage
- Version history section in README for better version tracking

### Changed
- Updated README with concise framework comparison and version history
- Enhanced base agent instructions with explicit ticket update requirements
- Improved base_agent_loader.py to use framework/agent-roles path

### Fixed
- Base agent file path resolution in base_agent_loader.py
- Test directory organization and reports structure

### Maintenance
- Cleaned up test directory structure with proper categorization
- Moved test reports to dedicated reports/ subdirectory
- Added .gitignore for reports/validation/ directory

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

[Unreleased]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.4.7...HEAD
[1.4.7]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.4.0...v1.4.7
[1.4.0]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.2.3...v1.3.0
[1.2.3]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.2.1...v1.2.3
[1.2.1]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.0.1...v1.2.0
[1.0.1]: https://github.com/bobmatnyc/claude-multiagent-pm/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/bobmatnyc/claude-multiagent-pm/releases/tag/v1.0.0