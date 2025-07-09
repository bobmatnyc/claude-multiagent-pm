# Changelog

All notable changes to the Claude Multi-Agent Project Management Framework will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## 4.4.0 (2025-07-09)

### 🚀 Major Framework Enhancement - Three-Tier Agent Hierarchy Architecture

#### New Three-Tier Agent Hierarchy System
- **Hierarchical Agent Loading** - Complete three-tier agent system: Project → User → System
- **Agent Precedence System** - Project agents override User agents, User agents override System agents
- **Dynamic Agent Discovery** - Automatic discovery and loading of agents across all three tiers
- **Agent Configuration Management** - Comprehensive configuration system with inheritance and overrides
- **Hierarchical Agent Validator** - Service to validate agent hierarchy integrity and relationships

#### CMCP-init Enhanced Implementation
- **Comprehensive Project Indexing** - Enhanced `cmcp-init` with complete project data collection
- **Three-Tier Directory Structure** - Automated creation of framework, working, and project directories
- **Agent Template System** - Template-based agent creation for all three tiers
- **Configuration Generation** - YAML-based configuration with inheritance support
- **Dependency Verification** - Real-time verification of mem0AI, ai-trackdown-tools, and framework core

#### AI-Trackdown-Tools Integration
- **CLI Integration** - Seamless integration with `aitrackdown` and `atd` commands
- **Project Data Collection** - Automated project indexing via ai-trackdown-tools CLI
- **Graceful Fallback** - Fallback mechanisms when ai-trackdown-tools is unavailable
- **Cross-Project Coordination** - Enhanced multi-project workflow coordination

#### MCP Service Integration
- **MCP Service Detector** - Automatic detection and integration of MCP services
- **Service Orchestration** - Enhanced multi-agent orchestration with MCP service workflows
- **Service Discovery** - Dynamic discovery of available MCP services
- **Workflow Enhancement** - MCP services enhance multi-agent workflow capabilities

#### Framework Instruction Architecture
- **Complete CLAUDE.md Update** - Comprehensive framework instructions reflecting new three-tier architecture
- **Agent Coordination Protocols** - Detailed protocols for cross-tier agent coordination
- **Multi-Project Orchestration** - Instructions for managing multiple projects with shared agent hierarchy
- **MCP Integration Guidelines** - Guidelines for leveraging MCP services in agent workflows

#### Technical Enhancements
- **Agent Discovery Service** - Service for dynamic agent discovery across all tiers
- **Agent Hierarchy Validator** - Validation service ensuring proper agent hierarchy relationships
- **Hierarchical Agent Loader** - Complete loading system with precedence and inheritance
- **Service Manager Integration** - Full integration with enhanced service management architecture
- **Multi-Agent Orchestrator** - Enhanced orchestration with three-tier agent support

#### Breaking Changes
- **Agent Architecture** - Migration to three-tier agent hierarchy system
- **Configuration Format** - Enhanced YAML configuration with tier-specific settings
- **Service Integration** - New MCP service integration requirements
- **Framework Instructions** - Complete rewrite of framework coordination protocols

### Technical Implementation Details
- **56 files changed** with major architecture enhancements
- **20,000+ lines added** including new agent hierarchy system
- **Comprehensive testing** with hierarchical agent system tests
- **MCP service detection** and workflow integration
- **Enhanced documentation** with complete architecture overhaul

## 4.3.0 (2025-07-09)

### 🚀 Major Framework Enhancement - Multi-Project Orchestrator Pattern

#### New /cmpm-init Command System
- **`/cmpm-init` Command** - Comprehensive framework initialization with setup, verify, and force options
- **Multi-Project Orchestration** - Three-tier directory structure: framework, working, and project directories
- **System Init Agent** - Specialized agent for framework initialization and configuration management
- **Automated Setup** - Intelligent directory detection and automated dependency verification

#### Multi-Project Architecture Enhancements
- **Framework Directory** - Global user agents and system-trained prompt data at `~/.claude-multiagent-pm/`
- **Working Directory** - Current session configuration and context management
- **Project Directory** - Project-specific agents and configuration overrides
- **Agent Hierarchy** - Priority-based agent loading: framework → project overrides

#### System Init Agent Implementation
- **Comprehensive Setup** - Complete framework initialization with dependency checking
- **Directory Structure Creation** - Automated creation of all necessary framework directories
- **Configuration Generation** - YAML-based configuration files for all operational modes
- **Dependency Verification** - Real-time verification of mem0AI, ai-trackdown-tools, and Node.js environment
- **Troubleshooting System** - Automated issue detection and solution recommendations

#### Framework Directory Detection Fix
- **Fixed cmpm-bridge.py** - Resolved framework directory detection issues across different working directories
- **Enhanced Path Discovery** - Improved framework path resolution with multiple candidate locations
- **Environment Variable Support** - `CLAUDE_PM_FRAMEWORK_PATH` environment variable support
- **Fallback Mechanisms** - Graceful degradation when framework path is not detected

#### CLAUDE.md Configuration Updates
- **Mandatory Initialization** - Added initialization requirements to startup protocol
- **System Init Agent Integration** - Automatic delegation to System Init Agent for missing directories
- **Multi-Project Documentation** - Comprehensive documentation of three-tier directory structure
- **Agent Hierarchy Documentation** - Clear explanation of framework vs project agent precedence

#### Technical Infrastructure
- **Rich Console Output** - Professional initialization reporting with progress indicators
- **YAML Configuration** - Structured configuration management across all modes
- **Diagnostic System** - Comprehensive framework diagnostics and health reporting
- **Error Handling** - Robust error handling with detailed troubleshooting guidance

#### Breaking Changes
- **Directory Structure** - Migration from single-directory to multi-project orchestrator pattern
- **Agent Loading** - Enhanced agent hierarchy with framework and project-specific agents
- **Configuration Format** - YAML-based configuration replacing legacy configuration patterns

This release establishes the Claude PM Framework as a true multi-project orchestrator with comprehensive initialization, setup, and dependency management capabilities.

## 4.2.3 (2025-07-09)

### 📚 Documentation Enhancement - AI-Trackdown-Tools CLI Integration

#### Comprehensive Documentation Update
- **🔧 CLI Documentation** - Updated TICKETING_SYSTEM.md with complete ai-trackdown-tools CLI reference
- **📋 Command Reference** - Added comprehensive command examples for epics, issues, tasks, and PRs
- **🏗️ Hierarchical Structure** - Documented Epics → Issues → Tasks → PRs workflow
- **🔗 GitHub Integration** - Added GitHub Issues sync and portfolio management features
- **⚡ Migration Guide** - Replaced outdated manual file creation with CLI-based workflows

#### Technical Accuracy Improvements
- **🔄 Legacy Removal** - Removed deprecated manual ticket creation instructions
- **📊 Framework Alignment** - Updated version references from 4.0.0 to 4.2.2
- **🎯 CLI-First Approach** - Established ai-trackdown-tools as primary ticket management system
- **📈 Usability Enhancement** - Improved developer experience with accurate CLI documentation

#### Framework Integration Status
- **✅ CLI Integration** - Full ai-trackdown-tools CLI documentation complete
- **✅ Command Examples** - Comprehensive usage examples for all operations
- **✅ Workflow Documentation** - Clear hierarchical ticket management workflows
- **✅ GitHub Sync** - Bidirectional synchronization capabilities documented

This documentation update significantly improves framework usability and provides developers with accurate, comprehensive guidance for CLI-based ticket management.

## 4.2.2 (2025-07-09)

### 🏛️ Framework Governance - Constitutional Design Document

#### Major Governance Enhancement
- **📋 Comprehensive Design Document** - Added authoritative design document at `docs/design/claude-multiagent-pm-design.md`
- **⚖️ Constitutional Framework** - Established design document as constitutional authority for all PM decisions
- **🔍 QA Validation Protocols** - Mandatory design document alignment for all framework operations
- **📐 Scope Boundaries** - Clear definition of what IS and IS NOT in framework scope
- **🎯 Ticket Relevance Validation** - All tickets must align with design document scope

#### Framework Authority Protocols
- **🔒 Design Document Authority** - All PM decisions must reference design document sections
- **📋 Governance Protocols** - Established framework-level decision making processes
- **🎯 Orchestration Capabilities** - Enhanced multi-agent coordination with constitutional backing
- **📊 Epic/Issue Tracking** - New ai-trackdown-tools integration with cmpm dashboard development

#### Technical Enhancements
- **🚀 CMPM Dashboard** - Added slash command development tickets for portfolio manager
- **🔧 Framework Integration** - Enhanced ai-trackdown-tools coordination capabilities
- **📈 Version Management** - Upgraded to v4.2.2 with governance enhancements

This represents a **significant governance milestone** establishing the design document as the authoritative source for all Claude PM Framework operations and decisions.

## 4.2.1 (2025-07-09)

### 🚀 New Features - ai-trackdown-tools Integration

#### Comprehensive ai-trackdown-tools Integration
- **Persistent Ticket Management** - Cross-process ticket persistence for multi-agent coordination
- **Enhanced Documentation** - ai-trackdown-tools configuration across all user guides
- **Troubleshooting Guide** - Comprehensive troubleshooting section for ai-trackdown-tools
- **Agent Configuration** - ai-trackdown-tools integration in custom agent configuration
- **Framework Overview** - Enhanced architecture documentation with ai-trackdown-tools

#### Technical Enhancements
- **Configuration Integration** - ai-trackdown-tools configuration in framework.yaml
- **Fallback Mechanisms** - Graceful degradation when ai-trackdown-tools is unavailable
- **Agent Permissions** - Granular permissions for ticket operations per agent
- **Directory Organization** - Updated directory structure documentation

#### Documentation Updates
- **docs/FRAMEWORK_OVERVIEW.md** - Added ai-trackdown-tools architecture section
- **docs/user-guide/01-getting-started.md** - Added dependency setup instructions
- **docs/user-guide/04-directory-organization.md** - Added configuration information
- **docs/user-guide/05-custom-agents.md** - Added ai-trackdown-tools configuration
- **docs/user-guide/07-troubleshooting-faq.md** - Added troubleshooting section
- **docs/INDEX.md** - Updated with new references and command examples

#### Framework Orchestration Completion
- **Critical Issues Resolution** - ISS-0039, ISS-0038 framework orchestration issues resolved
- **Memory Dependencies** - Removed memory dependency barriers for enhanced performance
- **Template System** - Fixed template system configurations
- **Health Monitoring** - Enhanced health monitoring with ai-trackdown-tools integration

## 4.1.0 (2025-07-09)

### 🚀 New Features - CMPM Slash Commands

#### Professional CMPM Command Interface
- **`/cmpm:health`** - Comprehensive system health dashboard with real-time monitoring
- **`/cmpm:agents`** - Active agent registry overview with MCP infrastructure support
- **CLI Wrapper** - Professional CMPM-branded command interface via `./bin/cmpm`
- **Rich Output** - Color-coded dashboards with professional tabular data presentation

#### System Health Monitoring
- **4 Core Components** - Framework, ai-trackdown-tools, task system, and memory system monitoring
- **Reliability Scoring** - 0-100% system reliability calculation with component status aggregation
- **Response Time Tracking** - Sub-5-second performance metrics with timeout handling
- **Graceful Error Handling** - Intelligent fallback for offline components

#### Agent Registry Management
- **12 Total Agents** - Complete agent discovery with status, specialization, and coordination roles
- **MCP Integration** - Multi-agent coordination with agent discovery and monitoring
- **Agent Categories** - Standard vs user-defined agent classification
- **Real-time Status** - Live agent availability and capability reporting

### 🛠 Technical Enhancements

#### ISS-0002 Completion - Comprehensive Health Slash Command
- **100% Complete** - Full implementation of health dashboard functionality
- **ai-trackdown Integration** - Native CLI testing and status reporting
- **Memory System Testing** - mem0AI connectivity validation and performance monitoring
- **Task System Monitoring** - Epic and issue count tracking with operational status

#### Performance Optimizations
- **Async Operations** - Parallel health data collection for improved response times
- **Timeout Management** - Configurable timeouts (2-5 seconds) for reliable operations
- **Caching Strategy** - 10-second TTL for health data to balance freshness and performance
- **Error Recovery** - Comprehensive exception handling with meaningful error messages

#### Command Features
- **Support Flags** - `--json`, `--detailed`, `--filter` options for enhanced usability
- **Professional Output** - Rich console formatting with color-coded status indicators
- **Tabular Presentation** - Structured data display with component details
- **Real-time Updates** - Live status reporting with timestamp tracking

### 📊 Integration Status

#### Framework Integration
- **ai-trackdown-tools v3.0.0** - Full CLI integration with status monitoring
- **mem0AI Service** - localhost:8002 connectivity testing and health validation
- **MCP Infrastructure** - Multi-agent coordination protocol support
- **Task Management** - Epic and issue tracking with operational metrics

#### Command Usage Examples
```bash
# System health dashboard
./bin/cmpm /cmpm:health

# Detailed health information
./bin/cmpm /cmpm:health --detailed

# Agent registry overview
./bin/cmpm /cmpm:agents

# JSON output for integrations
./bin/cmpm /cmpm:health --json
./bin/cmpm /cmpm:agents --json

# Help information
./bin/cmpm help
```

### 🎯 Success Metrics

- **Response Time** - Sub-5-second health checks achieved
- **Reliability Score** - 0-100% system reliability calculation implemented
- **Agent Discovery** - 12 total agents with full status reporting
- **Integration Coverage** - 4 core components monitored (Framework, ai-trackdown, Tasks, Memory)
- **Professional Output** - Rich color-coded dashboards with tabular data
- **Error Handling** - Graceful degradation for offline components

### 📋 Implementation Details

#### File Structure
- **`claude_pm/cmpm_commands.py`** - Core CMPM command implementations
- **`bin/cmpm`** - CLI wrapper for slash command routing
- **Health Monitoring** - `CMPMHealthMonitor` class with async health collection
- **Agent Registry** - `CMPMAgentMonitor` class with MCP integration

#### Architecture
- **Async Design** - Non-blocking operations with parallel data collection
- **Modular Structure** - Separate monitor classes for health and agent functionality
- **Rich Console** - Professional terminal output with color coding and progress indicators
- **Error Resilience** - Comprehensive exception handling with fallback mechanisms

---

## 4.0.0 (2025-07-08)

### 🚀 DUAL PACKAGING DISTRIBUTION

**Universal Deployment Architecture**: The framework now supports both NPM and Python packaging systems for maximum flexibility:

#### NPM Package Distribution
- **Package Name**: `claude-multiagent-pm`
- **Universal CLI**: `claude-pm` binary available system-wide
- **Cross-Platform**: Supports Darwin, Linux, Windows (x64, ARM64)
- **Node.js Requirements**: >=16.0.0 (for deployment automation)
- **Installation**: `npm install -g claude-multiagent-pm`

#### Python Package Distribution  
- **Package Name**: `claude-multiagent-pm` (PyPI)
- **Python Requirements**: >=3.9 (supports 3.9-3.12)
- **CLI Scripts**: `claude-multiagent-pm`, `claude-multiagent-pm-health`, `claude-multiagent-pm-service`
- **Installation**: `pip install claude-multiagent-pm`

#### Deployment Flexibility
- **Development Teams**: Choose preferred package manager (npm/pip)
- **CI/CD Integration**: Both package managers supported
- **Environment Management**: Works with conda, virtualenv, nvm, etc.
- **Enterprise Distribution**: Multiple deployment vectors available

## 4.0.0 (2025-07-08)

### ⚠ BREAKING CHANGES

* **Major Architectural Overhaul**: Complete LangGraph removal and migration to pure Task tool delegation
* **Framework Optimization**: 40% size reduction (25MB space saved, 35+ obsolete files removed)
* **Production Architecture**: Simplified, reliable pure subprocess delegation model

### 🚀 Major Features

#### LangGraph Removal & Task Tool Architecture
- **Pure Task Delegation**: Eliminated LangGraph complexity in favor of direct Task tool subprocess coordination
- **Architectural Simplification**: Removed all LangGraph dependencies and related orchestration layers
- **Production Optimization**: 25MB reduction in framework size through comprehensive cleanup
- **Enhanced Reliability**: More predictable and maintainable subprocess coordination

#### Framework Performance Improvements
- **40% Size Reduction**: Removed 35+ obsolete files and dependencies
- **Simplified Dependencies**: Streamlined to essential libraries only
- **Enhanced Startup**: Faster framework initialization without LangGraph overhead
- **Memory Efficiency**: Reduced memory footprint for production deployments

#### Production-Ready Architecture
- **Task Tool Delegation**: Clean, direct subprocess creation and management
- **Isolated Agent Contexts**: Each agent receives filtered, role-specific instructions
- **Memory-Augmented Coordination**: Preserved mem0AI integration with simplified architecture
- **Systematic Communication**: Structured protocols for agent coordination without complexity

### 🛠 Technical Improvements

#### Code Quality & Maintenance
- **Documentation Cleanup**: Updated all references from LangGraph to Task delegation
- **Configuration Simplification**: Removed complex orchestration configuration
- **Testing Optimization**: Simplified test suites with Task delegation patterns
- **Error Handling**: More predictable error patterns with direct subprocess calls

#### Framework Maturity
- **Production Validated**: Battle-tested across 12+ managed projects
- **Zero-Configuration Setup**: Maintained instant memory access without complexity
- **11-Agent Ecosystem**: Full multi-agent architecture with simplified coordination
- **Performance Optimized**: Sub-second context preparation maintained with lighter architecture

### 📊 Success Metrics

- **25MB Space Saved**: Comprehensive cleanup of obsolete files and dependencies
- **35+ Files Removed**: Eliminated LangGraph-related complexity
- **40% Size Reduction**: More efficient framework distribution
- **100% Functionality Preserved**: All core features maintained with simpler architecture
- **Enhanced Reliability**: More predictable subprocess coordination patterns

### 🔄 Migration Notes

#### Breaking Changes
- **LangGraph Dependencies**: All LangGraph imports and usage removed
- **Orchestration Patterns**: Simplified to direct Task tool delegation
- **Configuration Files**: LangGraph-specific configurations no longer supported

#### Compatibility
- **mem0AI Integration**: Fully preserved and enhanced
- **Task Tool Delegation**: New standard for subprocess coordination
- **Agent Roles**: All 11 agents maintained with simplified coordination
- **Memory Patterns**: All memory integration patterns preserved

---

## 3.0.0 (2025-07-07)


### ⚠ BREAKING CHANGES

* Complete framework restructure with multi-agent orchestration

Features:
- Multi-agent orchestration with 5 specialized roles per project
- Writing authority boundaries (Engineer: code, Ops: config, QA: tests, Research: docs, Architect: scaffolding)
- Agent allocation rules (multiple Engineers, single other agents per project)
- Context isolation between PM and project contexts
- Explicit permission requirement for framework deviations
- Individual agent role documentation with detailed specifications
- Claude Code best practices integration (TDD, API-first)
- Semantic versioning with npm package structure

Documentation:
- Comprehensive agent role definitions in framework/agent-roles/
- Updated main framework configuration with explicit permission requirements
- MIT license and proper npm package.json structure
- Enhanced README with badges and proper descriptions

Workflow:
- Research → Architecture → Development → Quality → Deployment gates
- Automatic escalation when agents blocked >2-3 iterations
- Learning capture and cross-agent knowledge sharing
- Business stakeholder communication through PM only

Context Separation:
- PM context: Full framework visibility and orchestration
- Project context: Isolated, single-project awareness only
- Agent contexts: Role-specific filtered information only

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>

### Features

* complete git-portfolio-manager integration - closes M01-009 ([95eb625](https://github.com/bobmatnyc/claude-pm/commit/95eb62553c97c52d567149002db0ff987a6b88d2))
* establish managed subdirectory model - closes M01-019 ([d21aea2](https://github.com/bobmatnyc/claude-pm/commit/d21aea20d5ae3ec199f439c1baebf81755ebbdd3))
* initial Claude PM framework setup with separated repository architecture ([e69f773](https://github.com/bobmatnyc/claude-pm/commit/e69f7731b6f7f81498dd17b28fd72aa313afff46))


### Framework

* implement v2.0.0 multi-subprocess orchestration model ([dce6258](https://github.com/bobmatnyc/claude-pm/commit/dce625837591e09cbdb116353278b13e719bed9d))

## [2.0.0] - 2025-07-07

### 🚀 Features

#### Major Framework Restructure
- **Multi-Subprocess Orchestration Model**: Complete redesign with 5 specialized subprocess roles per project
- **Context Isolation**: Strict separation between PM context and managed project contexts
- **Writing Authority Boundaries**: Exclusive file type permissions for each subprocess role
- **Claude Code Best Practices Integration**: TDD, API-first design, incremental development enforcement

#### Subprocess Specialization
- **Engineer Subprocess**: Exclusive source code writing authority (.js, .py, .ts, etc.)
- **Ops Subprocess**: Configuration files, deployment scripts, CI/CD configs only
- **QA Subprocess**: Test files, quality assurance scripts only
- **Research Subprocess**: Documentation, best practice guides only
- **Architect Subprocess**: Project scaffolding, API specifications only

#### Business Interface
- **PM Orchestration**: Claude PM as single interface to business stakeholders
- **Filtered Context Sharing**: Role-specific information filtering to subprocesses
- **Learning Management**: Systematic capture and sharing of subprocess learnings
- **Quality Gates**: Multi-phase validation with research, architecture, development, quality, deployment gates

### 📋 Process Improvements

#### Task Management
- **Enhanced Ticket System**: M0X-XXX (milestones), FEP-XXX (features), PROJ-XXX (projects), LRN-XXX (learning)
- **Escalation Protocols**: Automatic PM intervention when subprocesses blocked >2-3 iterations
- **TrackDown Integration**: Learning capture in project trackdown systems
- **Future mem0ai Integration**: Planned persistent learning system

#### Quality Assurance
- **Best Practice Monitoring**: Continuous adherence checking to Claude Code standards
- **Performance Metrics**: Subprocess-specific success metrics and KPIs
- **Anti-Pattern Prevention**: Documentation and avoidance of failed approaches

### 🔧 Technical Infrastructure

#### Repository Structure
- **PM Repository**: Dedicated Claude-PM repo for all orchestration concerns
- **Project Isolation**: Individual projects with no PM framework awareness
- **Context Boundaries**: Strict information filtering between contexts
- **Documentation Separation**: PM docs vs project docs completely separated

#### Development Workflow
- **Research → Architecture → Development → Quality → Deployment**: Sequential workflow with gates
- **Incremental Development**: No >2-3 iteration blocks allowed
- **Learning Propagation**: Cross-subprocess knowledge sharing
- **Business Communication**: Executive summaries and strategic updates

### ⚠️ Breaking Changes

- **Complete Framework Restructure**: v1.x single-context model replaced with multi-subprocess orchestration
- **Context Separation**: Projects can no longer reference PM framework concerns
- **Writing Permissions**: Strict file type permissions enforced per subprocess role
- **Ticket Formats**: New ticket naming conventions for different concern types

### 📊 Success Metrics

#### Target Improvements
- **60%+ Productivity Increase**: Over baseline single-context development
- **70% Context Switching Reduction**: Through specialized subprocess contexts
- **90%+ Task Completion Rate**: Via systematic workflow and quality gates
- **<30 Minute Setup**: For new project initialization

#### Framework Maturity
- **Level 1**: Basic subprocess orchestration ✅ (This release)
- **Level 2**: Automated subprocess coordination (M01 target)
- **Level 3**: Intelligent subprocess routing (M02 target)
- **Level 4**: Self-optimizing subprocess ecosystem (M03 target)

---

### Previous Versions

## [1.0.0] - 2025-07-05

### Features
- Initial Claude PM framework with basic project management
- TrackDown integration
- Health monitoring
- Cross-project coordination
- Single-context development model

### Documentation
- Basic CLAUDE.md framework configuration
- Project management guidelines
- Task tracking system