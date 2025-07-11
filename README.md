# Claude Multi-Agent Project Management Framework v0.4.6 - Three-Tier Agent Hierarchy with Cross-Project Management

[![Version](https://img.shields.io/badge/Version-0.4.6-blue.svg)](https://github.com/masa/claude-multiagent-pm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Architecture](https://img.shields.io/badge/Architecture-Three--Tier%20Agent%20Hierarchy-brightgreen.svg)](./docs/10-architecture-frameworks-comprehensive-guide.md)
[![Cross-Project](https://img.shields.io/badge/Management-Cross--Project%20CMCP--init-purple.svg)](./docs/DEPLOYMENT-GUIDE-v4.5.1.md)
[![Memory Integration](https://img.shields.io/badge/Memory-mem0AI%20Integration-orange.svg)](./docs/INDEX.md)
[![MCP Services](https://img.shields.io/badge/MCP-Context7%20%26%20Zen-blue.svg)](./docs/04-integrations-comprehensive-guide.md)

> **Advanced three-tier agent hierarchy with cross-project CMCP-init management**

Claude Multi-Agent Project Management Framework delivers sophisticated AI-assisted project management through an advanced three-tier agent hierarchy and cross-project coordination system. The v0.4.6 release features **ISS-0074 session cleanup implementation** with 77% performance improvement (67+ sec → <15 sec), comprehensive security agent implementation, and robust CMCP-init bridge system for seamless multi-project workflow orchestration.

## 📋 Version Note

**Version Shift: 0.4.6 → 0.4.6**

This framework has been reset from version 0.4.6 to 0.4.6 to establish a cleaner semantic versioning approach as we prepare for broader release. All functionality remains intact with significant improvements in session cleanup, health monitoring, and multi-agent orchestration.

## 🚀 Quick Start

### Two-Step Setup

```bash
# 1. Install via NPM
npm install -g @bobmatnyc/claude-multiagent-pm

# 2. Run in any project directory
cd /path/to/your/project
claude-pm
```

That's it! The framework auto-detects your environment and sets up the complete multi-agent system.

### What You Can Do Next

Once running, use these three powerful commands:
- **`push`** - Complete quality validation and version control operations
- **`deploy`** - Local deployment with automated testing and validation  
- **`publish`** - Package publication to NPM, PyPI, and other registries

> 💡 **Need more control?** See the [Advanced Installation](#-prerequisites--advanced-installation) section for development setup and customization options.

## 🚀 Key Features

### 🏗️ Three-Tier Agent Hierarchy Architecture

#### Hierarchical Agent Management
- **Project Agents**: `$PROJECT/.claude-pm/agents/project-specific/` - Highest precedence, project-specific implementations
- **User Agents**: `~/.claude-pm/agents/user-defined/` - Global user customizations across all projects
- **System Agents**: `/framework/claude_pm/agents/` - Core framework functionality with automatic fallback
- **Dynamic Loading**: Automatic agent discovery with precedence-based selection (Project → User → System)
- **Configuration Inheritance**: Hierarchical configuration merging with override capabilities

#### Cross-Project CMCP-init Bridge System
- **Universal Framework Access**: CMCP-init enables non-descendant projects to access framework capabilities
- **Cross-Directory Management**: Work seamlessly across multiple project directories
- **Project Indexing**: Comprehensive project discovery with ai-trackdown-tools integration
- **Three-Layer Configuration**: Framework, Working, and Project-specific configurations
- **Automatic Setup**: `python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup`

### 🎯 Professional Command Interface

#### CMPM Slash Commands

#### Professional Command Interface
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

### 🤖 Multi-Agent Orchestration

#### Core Agent Framework
- **11 Specialized Agents**: PM, Documentation, Ticketing, Engineer, QA, Security, Performance, Data, DevOps, Research, Architect
- **Agent Hierarchy Validation**: Real-time validation of three-tier agent system consistency
- **Template-Based Agent Creation**: Standardized agent templates for system, user, and project tiers
- **Dynamic Agent Discovery**: Automatic agent file monitoring and lifecycle management
- **Performance Monitoring**: Comprehensive agent health checks and performance metrics

### Memory-Augmented Intelligence

#### Simplified Memory Integration (mem0AI)
- **Instant Memory Access**: Requires OpenAI API key configuration
- **Universal Memory Service**: Automatic service discovery on localhost:8002
- **Memory Categories**: Project, Pattern, Team, and Error memories with enterprise schemas
- **Factory Functions**: Simple memory access via environment-based configuration

#### Task Tool Subprocess Coordination with ai-trackdown-tools
- **Direct Delegation**: Clean subprocess creation via Task tool
- **Persistent Issue & PR Tracking**: Comprehensive ticket lifecycle management via ai-trackdown-tools
- **Subprocess State Persistence**: Issues and PRs persist beyond process termination
- **Isolated Contexts**: Each agent receives filtered, role-specific instructions
- **Memory-Augmented Tasks**: Context enhancement from historical project data
- **Systematic Communication**: Structured protocols for agent coordination

#### 11-Agent Orchestration Ecosystem
- **Core Agents**: Orchestrator, Architect, Engineer, QA, Researcher
- **Specialist Agents**: Security, Performance, DevOps, Data, UI/UX Engineers
- **Code Review Agent**: Multi-dimensional analysis (security, performance, style, testing)
- **Memory-Augmented Context**: Intelligent context preparation for enhanced performance
- **Parallel Execution**: Up to 5 concurrent agents with git worktree isolation

### Continuous Learning Engine with Persistent Tracking
- **Pattern Recognition**: Automatic identification of successful patterns
- **Memory-Driven Insights**: Context enhancement from historical project data
- **Team Knowledge Amplification**: Shared learning across all agents and projects
- **Intelligent Task Decomposition**: Memory-guided task planning and execution
- **Persistent Issue Tracking**: ai-trackdown-tools provides comprehensive ticket lifecycle management
- **Multi-Agent Coordination**: Persistent state enables coordinated work across subprocess boundaries

## 📊 Proven Results

- **83% Phase 1 Complete**: 106/127 story points completed
- **Zero-Configuration Setup**: Instant memory access without manual configuration
- **11-Agent Ecosystem**: Memory-augmented multi-agent architecture operational
- **Production Validated**: Tested across 12+ managed projects in `/Users/masa/Projects/managed/`
- **Universal Memory Access**: All Claude instances have instant memory integration
- **Sub-Second Performance**: Context preparation and memory operations optimized

## 🏗️ Architecture

### Memory-Augmented Agent Ecosystem with ai-trackdown-tools
- **11 Specialized Agents**: Core + Specialist agents with memory integration
- **Zero-Configuration Access**: Automatic memory service discovery and connection
- **Git Worktree Isolation**: Parallel execution environments for concurrent agents
- **Task Tool Coordination**: Direct subprocess delegation with structured protocols
- **ai-trackdown-tools Integration**: Persistent issue and PR tracking across subprocess boundaries
- **Memory Categories**: Project, Pattern, Team, Error memories with enterprise schemas

### Why ai-trackdown-tools is Essential

**Subprocess Coordination Challenge**: When agents operate in separate subprocesses, traditional in-memory state management fails. Each subprocess has its own memory space, making coordination complex.

**Solution**: ai-trackdown-tools provides:
- **Persistent State**: Issues and PRs persist beyond individual process lifetimes
- **Cross-Process Communication**: Multiple agents can coordinate through shared ticket system
- **Hierarchical Organization**: Epics → Issues → Tasks → PRs enable complex project management
- **Comprehensive Tracking**: Every issue and PR is tracked with full lifecycle management
- **Multi-Agent Coordination**: Agents can hand off work through persistent ticket assignments

### Memory Integration Architecture
- **Universal Memory Service**: localhost:8002 with environment-based configuration
- **Factory Functions**: ClaudePMMemory class with automatic client creation
- **Role-Specific Context**: Agent-aware memory filtering and context preparation
- **Cross-Project Memory**: Shared learning and patterns across all managed projects

### Framework Purpose
- **Zero-Configuration Experience**: Eliminate manual setup and configuration complexity
- **Intelligent Memory Integration**: Context-aware assistance with historical pattern recognition
- **Multi-Agent Orchestration**: Coordinated team of specialists with shared memory
- **Continuous Learning**: Pattern recognition and knowledge amplification across projects

## 🏗️ Framework Architecture

### Three-Layer Configuration System

The Claude PM Framework uses a sophisticated three-layer configuration system that enables cross-project management and flexible agent deployment:

```
Framework Architecture
├── Framework Layer: ~/framework/.claude-pm/
│   ├── Global framework-level configuration
│   ├── System agents and templates
│   └── Cross-project shared resources
├── Working Layer: $PWD/.claude-pm/
│   ├── Session-specific configuration
│   ├── Working directory context
│   └── Temporary session data
└── Project Layer: $PROJECT_ROOT/.claude-pm/
    ├── Project-specific agents and overrides
    ├── Project configuration and metadata
    └── Local project resources
```

### CMCP-init Bridge System

The CMCP-init system enables the framework to work across any project directory, even those not descended from the framework:

```bash
# Initialize framework access in any project
python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup

# Verify three-tier agent hierarchy
python ~/.claude/commands/cmpm-bridge.py cmcp-init --verify

# Reindex projects with ai-trackdown-tools integration
python ~/.claude/commands/cmpm-bridge.py cmcp-init --reindex
```

### Agent Hierarchy System

```
Agent Precedence (Highest to Lowest)
├── 🔹 Project Agents (Priority 3)
│   ├── Location: $PROJECT/.claude-pm/agents/project-specific/
│   ├── Scope: Project-specific implementations
│   └── Authority: Override user and system agents
├── 🔸 User Agents (Priority 2)
│   ├── Location: ~/.claude-pm/agents/user-defined/
│   ├── Scope: Global user customizations
│   └── Authority: Override system defaults
└── 🔹 System Agents (Priority 1)
    ├── Location: /framework/claude_pm/agents/
    ├── Scope: Core framework functionality
    └── Authority: Fallback when higher tiers unavailable
```

### Directory Structure
```
claude-pm/
├── .git/                           # Dedicated PM git repository
├── README.md                      # This file (updated for v0.4.6)
├── claude_pm/                     # Core framework implementation
│   ├── agents/                    # Agent hierarchy system
│   │   ├── hierarchical_agent_loader.py # Three-tier agent loading
│   │   ├── system_init_agent.py         # CMCP-init implementation
│   │   ├── pm_agent.py                  # Project management agent
│   │   ├── documentation_agent.py       # Documentation agent
│   │   ├── ticketing_agent.py           # Specialized ticketing agent
│   │   └── templates/                   # Agent templates for all tiers
│   ├── core/                      # Core framework services
│   │   ├── agent_config.py              # Hierarchical configuration
│   │   ├── service_manager.py           # Enhanced service management
│   │   └── config.py                    # Framework configuration
│   └── services/                  # Framework services
│       ├── agent_discovery_service.py   # Real-time agent discovery
│       ├── agent_hierarchy_validator.py # Hierarchy validation
│       ├── mcp_service_detector.py      # MCP service integration
│       └── mem0_context_manager.py      # Memory integration
├── tasks/                         # AI-trackdown-tools integration
│   ├── epics/                     # Strategic epics
│   ├── issues/                    # Implementation issues
│   ├── tasks/                     # Development tasks
│   └── templates/                 # Ticket templates
├── docs/                          # Comprehensive documentation
│   ├── FRAMEWORK_OVERVIEW.md            # Architecture overview
│   ├── MCP_SERVICE_INTEGRATION.md       # MCP service guide
│   ├── SECURITY_AGENT_INSTRUCTIONS.md   # Security agent documentation
│   └── user-guide/                      # Complete user guide
├── examples/                      # Integration demonstrations
│   ├── ai_trackdown_tools_integration_demo.py
│   └── scaffolding-agent/               # Agent scaffolding examples
└── deployment/                    # Production deployment
    ├── docker/                          # Container configuration
    └── scripts/                         # Deployment automation
```

## 🎯 Framework Principles

### Zero-Configuration Memory Integration
**Universal memory access without setup complexity**:
- **Environment-Based Config**: Automatic service discovery and connection
- **Factory Functions**: ClaudePMMemory class with instant access
- **OpenAI API Key Required**: localhost:8002 service with configurable defaults
- **Universal Compatibility**: Works across all Claude instances and projects

### 42-Ticket Enhancement System
**Systematic Claude Max + mem0AI integration with pure subprocess delegation**:
- **MEM-001 to MEM-006**: Core memory integration ✅ COMPLETED (Phase 1)
- **TSK-001 to TSK-003**: Task tool subprocess protocols ✅ COMPLETED (Phase 2)
- **Architecture Status**: Complete - pure delegation model established
- **Completion Tracking**: Individual status reports for each major ticket

### Memory-Augmented Development
- **4 Memory Categories**: Project, Pattern, Team, Error with enterprise schemas
- **Intelligent Context**: Role-specific memory retrieval for all 11 agents
- **Continuous Learning**: Pattern recognition and success analysis
- **Cross-Project Memory**: Shared knowledge across 12+ managed projects

## 📦 Prerequisites & Advanced Installation

### Prerequisites

```bash
# Required: ai-trackdown-tools for project management
npm install -g @bobmatnyc/ai-trackdown-tools

# Verify installation
aitrackdown --version
atd --version  # alias command
```

### Advanced Installation Options

#### Option 1: Framework Development (Recommended)
```bash
# Clone the framework repository
git clone https://github.com/masa/claude-multiagent-pm.git claude-pm
cd claude-pm

# Install dependencies
pip install -r requirements/production.txt

# Initialize framework
python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup
```

#### Option 2: Cross-Project Usage
```bash
# Initialize framework access in any existing project
cd /path/to/your/project
python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup

# Verify three-tier agent hierarchy
python ~/.claude/commands/cmpm-bridge.py cmcp-init --verify
```

### Why ai-trackdown-tools Integration?
- **Cross-Project Coordination**: Manage tickets across multiple project directories
- **Persistent State Management**: Issues persist beyond individual Claude sessions
- **Hierarchical Organization**: Epic → Issue → Task → PR lifecycle management
- **Rich Project Indexing**: Comprehensive project metadata collection
- **Multi-Agent Coordination**: Enables sophisticated agent workflows

### Framework Capabilities

#### Three Shortcut Commands
- **`push`**: Comprehensive deployment with versioning, changelog, and git operations
- **`deploy`**: Production deployment with health validation and rollback support
- **`publish`**: Package publishing with automated distribution across NPM and PyPI

#### Core Agent System
- **PM Agent**: Project management orchestration and delegation coordination
- **Documentation Agent**: Intelligent documentation updates with project pattern scanning
- **Ticketing Agent**: Specialized issue management with ai-trackdown-tools integration
- **Security Agent**: Pre-push veto authority with comprehensive security scanning
- **11 Specialized Agents**: Complete ecosystem for software development workflows

#### MCP Service Integration
- **Context 7**: Up-to-date library documentation and API references
- **MCP-Zen**: Second opinion validation and mindfulness tools for productivity
- **Automatic Detection**: Runtime MCP service discovery and contextual recommendations
- **Enhanced Workflows**: MCP-enhanced agent workflows for improved accuracy

#### Cross-Project Management Features
- **Project Indexing**: Comprehensive project discovery across multiple directories
- **Unified Configuration**: Three-layer configuration system (Framework → User → Project)
- **Agent Customization**: Hierarchical agent customization with precedence rules
- **Template System**: Standardized templates for agents, projects, and configurations

## 🚀 Getting Started

### Quick Setup for New Projects

```bash
# Setup framework access in any project directory
cd /path/to/your/project
python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup

# Verify agent hierarchy
python ~/.claude/commands/cmpm-bridge.py cmcp-init --verify

# Check available agents
python ~/.claude/commands/cmpm-bridge.py cmcp-init --show-index
```

### Framework Development Setup

```bash
# Clone and setup framework for development
git clone https://github.com/masa/claude-multiagent-pm.git claude-pm
cd claude-pm

# Install dependencies
pip install -r requirements/production.txt
npm install -g @bobmatnyc/ai-trackdown-tools

# Initialize framework
python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup
```

### Agent Customization

#### Creating Project-Specific Agents
```bash
# Create a project-specific QA agent
cd /path/to/your/project
python ~/.claude/commands/cmpm-bridge.py cmcp-init --create-agent qa --tier project

# Create a user-defined documentation agent
python ~/.claude/commands/cmpm-bridge.py cmcp-init --create-agent documentation --tier user
```

#### Agent Hierarchy Usage
```python
# Framework automatically selects highest precedence agent
# Order: Project → User → System

# Load agent (automatic hierarchy resolution)
from claude_pm.core.service_manager import ServiceManager
service_manager = ServiceManager()
agent = await service_manager.load_agent("engineer")

# Agent will be loaded from:
# 1. $PROJECT/.claude-pm/agents/project-specific/ (if exists)
# 2. ~/.claude-pm/agents/user-defined/ (if exists)
# 3. /framework/claude_pm/agents/ (system fallback)
```

### Configuration Examples

#### Cross-Project Configuration
```yaml
# ~/.claude-pm/config/agents.yaml
agent_hierarchy:
  precedence_order: ["project_agents", "user_agents", "system_agents"]
  conflict_resolution: "highest_priority_wins"
  fallback_enabled: true

user_preferences:
  default_agent_template: "advanced"
  enable_mcp_services: true
  context7_enabled: true
```

### CMCP-init Commands Reference

```bash
# Basic initialization and verification
python ~/.claude/commands/cmpm-bridge.py cmcp-init                    # Basic status
python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup            # Complete setup
python ~/.claude/commands/cmpm-bridge.py cmcp-init --verify           # Hierarchy validation

# Project management
python ~/.claude/commands/cmpm-bridge.py cmcp-init --reindex          # Reindex projects
python ~/.claude/commands/cmpm-bridge.py cmcp-init --show-index       # Display project index

# Agent management
python ~/.claude/commands/cmpm-bridge.py cmcp-init --create-agent qa --tier project
python ~/.claude/commands/cmpm-bridge.py cmcp-init --list-agents       # List available agents
python ~/.claude/commands/cmpm-bridge.py cmcp-init --validate-agents   # Validate agent hierarchy
```

### Health Monitoring and Validation

```bash
# Framework health check
./scripts/health-check.sh

# AI-trackdown-tools status
aitrackdown status --current-sprint
atd epic list --status active

# Agent hierarchy validation
python ~/.claude/commands/cmpm-bridge.py cmcp-init --verify

# MCP service detection
echo "Available MCP services:"
claude mcp list | grep -E "context7|zen"
```

### Advanced Usage Patterns

#### Framework Development vs Framework Usage

**Framework Development**: Working on the framework itself
```bash
cd ~/Projects/claude-pm  # Framework directory
# Full agent development capabilities
# Access to framework internals
# Can modify system agents
```

**Framework Usage**: Using framework for project management
```bash
cd /path/to/any/project             # Any project directory
python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup
# Framework capabilities available
# Project-specific agent customization
# Cross-project coordination
```

#### Configuration Inheritance Flow

1. **System Configuration**: Framework defaults
2. **User Configuration**: `~/.claude-pm/config/`
3. **Project Configuration**: `$PROJECT/.claude-pm/config/`
4. **Session Configuration**: `$PWD/.claude-pm/config/`

Each layer can override the previous, enabling flexible customization.

### Usage Patterns

#### Cross-Project Workflow Management
- **Universal Framework Access**: Any project can leverage the full framework via CMCP-init
- **Project Indexing**: Automatic discovery and indexing of projects with ai-trackdown-tools
- **Agent Customization**: Project-specific agents override user and system defaults
- **Configuration Inheritance**: Hierarchical configuration with per-project customization

#### Memory Integration
- **mem0AI Integration**: Intelligent context management with historical pattern recognition
- **Cross-Project Learning**: Shared patterns and insights across all managed projects
- **Agent-Aware Context**: Role-specific memory filtering and context preparation
- **Enterprise Schemas**: Structured memory categories with validation and migration support

## 🔗 Integration Points

### MCP Service Integration
- **Context 7**: Up-to-date library documentation and API references
- **MCP-Zen**: Second opinion validation with alternative LLM perspectives
- **Automatic Detection**: Runtime MCP service discovery and contextual recommendations
- **Workflow Enhancement**: MCP services enhance agent accuracy and decision-making

### AI-Trackdown-Tools Integration
- **Project Management**: Epic → Issue → Task → PR hierarchical lifecycle management
- **Cross-Process State**: Persistent tickets that survive Claude session boundaries
- **Rich Project Data**: Comprehensive project metadata and progress tracking
- **CLI Integration**: Seamless `aitrackdown` and `atd` command integration

### Three-Tier Agent System
- **Dynamic Agent Loading**: Runtime agent discovery with precedence-based selection
- **Configuration Inheritance**: Hierarchical configuration merging with override support
- **Template System**: Standardized agent creation templates for all tiers
- **Real-time Validation**: Continuous agent hierarchy health monitoring

### Cross-Project Coordination
- **CMCP-init Bridge**: Universal framework access regardless of project location
- **Project Indexing**: Automatic project discovery and metadata collection
- **Unified Configuration**: Three-layer configuration system enabling flexible customization
- **Session Management**: Context-aware session handling across multiple projects

## 📊 Current Status & Metrics

### Recent Developments (July 2025)

#### v0.4.6 - Comprehensive Framework Cleanup and Optimization
- **Space Savings**: 139MB+ recovered through systematic cleanup (185MB → 46MB total)
- **Framework Integrity**: Complete validation of core systems post-cleanup
- **Dependency Cleanup**: Removed obsolete node_modules and coverage reports
- **Structure Compliance**: Achieved canonical v0.4.6 directory structure

#### v0.4.5 - Security Agent Implementation
- **Security Agent**: Comprehensive security agent with pre-push veto authority
- **Multi-Tier Security**: Medium security default with automatic high security escalation
- **Vulnerability Detection**: Comprehensive patterns for secrets, code vulnerabilities, and configuration issues
- **Regulatory Compliance**: HIPAA, COPPA, PII protection, and SOC 2 compliance support

#### v4.4.0 - Three-Tier Agent Hierarchy
- **Agent Hierarchy**: Complete three-tier system (Project → User → System)
- **CMCP-init Enhancement**: Comprehensive project indexing and cross-directory management
- **AI-Trackdown Integration**: Seamless CLI integration with graceful fallback
- **MCP Service Integration**: Automatic service detection and workflow enhancement

### Architecture Status - Three-Tier Hierarchy Complete
- **🏗️ Three-Tier Agent Hierarchy**: Project → User → System precedence fully operational
- **🔄 CMCP-init Bridge System**: Cross-project framework access implemented
- **🤖 Agent System**: 11 specialized agents with hierarchical loading and validation
- **🔐 Security Integration**: Comprehensive security agent with pre-push veto authority
- **📊 Project Indexing**: AI-trackdown-tools integration with rich project metadata
- **🛠️ MCP Service Integration**: Context 7 and MCP-Zen service detection and workflows

### Infrastructure Metrics
- **Agent Discovery**: ~100ms for typical project hierarchy validation
- **Agent Loading**: ~50ms per agent with precedence resolution
- **Project Indexing**: Comprehensive project metadata with ai-trackdown-tools
- **MCP Service Detection**: Automatic detection of Context 7 and MCP-Zen services
- **Cross-Project Coordination**: Seamless framework access across multiple directories
- **Framework Size**: 46MB optimized framework (139MB+ savings from cleanup)

### Next Phase Targets
- **Agent Versioning**: Version management and backward compatibility for agents
- **Performance Optimization**: Agent loading caching and optimization
- **Enhanced Monitoring**: Visual hierarchy monitoring and performance dashboards
- **Security Enhancements**: Agent sandboxing and permission systems
- **Template Marketplace**: Shared agent template repository and distribution

---

**Repository Created**: 2025-07-05  
**Framework Version**: v0.4.6 (Three-Tier Agent Hierarchy with Cross-Project Management)  
**Architecture Status**: ✅ Complete - Three-Tier Agent Hierarchy Operational  
**Cross-Project System**: ✅ CMCP-init Bridge with Universal Framework Access  
**Agent Hierarchy**: ✅ Project → User → System Precedence with Dynamic Loading  
**Security Integration**: ✅ Comprehensive Security Agent with Pre-Push Veto Authority  
**MCP Integration**: ✅ Context 7 and MCP-Zen Service Detection and Workflows  
**Project Management**: ✅ AI-Trackdown-Tools Integration with Rich Project Indexing  
**Framework Optimization**: ✅ 139MB+ Space Savings with Complete Validation  
**Maintenance**: Active development with advanced multi-agent coordination and cross-project orchestration

## 📚 Documentation & Resources

### Quick Navigation
📚 **[Complete Documentation Index](./docs/INDEX.md)** - Your starting point for all framework documentation

**Essential Guides**:
1. **[Framework Overview](./docs/FRAMEWORK_OVERVIEW.md)** - Three-tier architecture and CMCP-init system
2. **[User Guide](./docs/user-guide/README.md)** - Complete user guide with examples
3. **[MCP Service Integration](./docs/MCP_SERVICE_INTEGRATION.md)** - Context 7 and MCP-Zen usage
4. **[Security Agent Instructions](./docs/SECURITY_AGENT_INSTRUCTIONS.md)** - Security scanning and validation
5. **[Deployment Guide](./docs/DEPLOYMENT_GUIDE.md)** - Production deployment and configuration

**Agent Development**:
- **[Agent Delegation Guide](./docs/AGENT_DELEGATION_GUIDE.md)** - Systematic agent delegation patterns
- **[Agent Templates](./claude_pm/agents/templates/)** - Templates for system, user, and project agents
- **[Agent Discovery Service](./claude_pm/services/agent_discovery_service.py)** - Real-time agent monitoring

### Framework Status Check
```bash
# CMCP-init system validation
python ~/.claude/commands/cmpm-bridge.py cmcp-init --verify
python ~/.claude/commands/cmpm-bridge.py cmcp-init --show-index

# Agent hierarchy validation
python ~/.claude/commands/cmpm-bridge.py cmcp-init --validate-agents

# Framework health monitoring
./scripts/health-check.sh

# AI-trackdown-tools integration
aitrackdown status --current-sprint
atd epic list --status active

# MCP service detection
echo "Checking MCP services..."
claude mcp list | grep -E "context7|zen" || echo "MCP services not detected"

# Framework core validation
python3 -c "import claude_pm; print('✓ Framework core accessible')"
python3 -c "from claude_pm.agents.hierarchical_agent_loader import HierarchicalAgentLoader; print('✓ Agent hierarchy system operational')"
```

### Advanced Framework Usage
```python
# Three-tier agent system usage
from claude_pm.core.service_manager import ServiceManager
from claude_pm.agents.hierarchical_agent_loader import HierarchicalAgentLoader

# Initialize service manager with three-tier support
service_manager = ServiceManager()
await service_manager.initialize_agent_system()

# Load agent (automatic precedence resolution)
engineer_agent = await service_manager.load_agent("engineer")
# Loads from: Project → User → System (highest precedence available)

# Validate agent hierarchy
from claude_pm.services.agent_hierarchy_validator import AgentHierarchyValidator
validator = AgentHierarchyValidator()
report = await validator.validate_hierarchy_comprehensive()
print(f"Hierarchy health: {report.overall_health}")
```

The framework is production-ready with three-tier agent hierarchy, cross-project CMCP-init coordination, and comprehensive MCP service integration. All major infrastructure is complete and validated across multiple deployment scenarios.

**New to the framework?** → Start with the **[User Guide](./docs/user-guide/README.md)** for comprehensive examples and tutorials.