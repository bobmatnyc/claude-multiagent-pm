# Directory Organization & Best Practices

> **Comprehensive guide to CMPM directory structure, naming conventions, and organizational best practices for scalable AI-enhanced project management**

## 📋 Table of Contents

1. [Framework Structure Overview](#framework-structure-overview)
2. [Core Directory Layout](#core-directory-layout)
3. [Agent-Specific Organization](#agent-specific-organization)
4. [Configuration Management](#configuration-management)
5. [Multi-Project Organization](#multi-project-organization)
6. [Naming Conventions](#naming-conventions)
7. [Best Practices](#best-practices)
8. [Migration Patterns](#migration-patterns)

---

## 🏗️ Framework Structure Overview

### The CMPM Directory Philosophy

The Claude Multi-Agent PM Framework follows a **structured, hierarchical approach** that balances:

- **Clarity**: Clear separation of concerns and intuitive navigation
- **Scalability**: Support for growing project portfolios and team sizes
- **Maintainability**: Organized structure that reduces cognitive load
- **Automation**: Directory patterns that support automated processes

### Top-Level Framework Architecture

```
/Users/masa/Projects/claude-multiagent-pm/
├── claude_pm/              # 🧠 Framework core (Python package)
├── framework/              # 🤖 Agent definitions and coordination
├── tasks/                  # 📋 AI-trackdown hierarchical tickets
├── templates/              # 📄 Project and agent templates
├── docs/                   # 📚 Framework documentation
├── config/                 # ⚙️ System configuration files
├── scripts/                # 🔧 Automation and deployment scripts
├── tests/                  # 🧪 Test suite and validation
├── requirements/           # 📦 Python dependencies
├── schemas/                # 📐 Data schemas and validation
├── bin/                    # 🔗 CLI wrappers and executables
├── deployment/             # 🚀 Deployment configurations
├── logs/                   # 📊 System logs and monitoring
├── examples/               # 🎯 Usage examples and demos
└── .claude-pm/             # 🔐 Deployment-specific config
```

---

## 🗂️ Core Directory Layout

### `claude_pm/` - Framework Core

**Purpose**: Core Python package containing all framework services and utilities

```
claude_pm/
├── __init__.py                    # Package initialization
├── py.typed                       # Type hints marker
├── cli.py                         # Main CLI interface
├── cli_enforcement.py             # CLI security enforcement
├── cmpm_commands.py               # Framework commands
├── core/                          # Core services
│   ├── __init__.py
│   ├── base_service.py           # Base service class
│   ├── config.py                 # Configuration management
│   ├── enforcement.py            # Policy enforcement
│   ├── logging_config.py         # Logging configuration
│   ├── memory_config.py          # Memory service config
│   └── service_manager.py        # Service lifecycle management
├── services/                      # Framework services
│   ├── __init__.py
│   ├── claude_pm_memory.py       # Memory service integration
│   ├── continuous_learning_engine.py
│   ├── health_dashboard.py       # Health monitoring
│   ├── health_monitor.py         # Health checks
│   ├── intelligent_task_planner.py
│   ├── intelligent_workflow_orchestrator.py
│   ├── learning_integration_service.py
│   ├── mem0_context_manager.py   # Memory context management
│   ├── memory_cache.py           # Memory caching
│   ├── memory_service.py         # Core memory service
│   ├── multi_agent_orchestrator.py
│   ├── project_index_daemon.py   # Project indexing
│   ├── project_indexer.py        # Project discovery
│   ├── project_memory_manager.py # Project memory
│   ├── project_service.py        # Project management
│   ├── workflow_selection_engine.py
│   └── workflow_tracker.py       # Workflow tracking
├── integrations/                  # External integrations
│   ├── __init__.py
│   ├── mem0ai_integration.py     # mem0AI integration
│   └── security.py               # Security integration
├── adapters/                      # Service adapters
│   ├── __init__.py
│   └── health_adapter.py         # Health monitoring adapter
├── collectors/                    # Data collectors
│   ├── __init__.py
│   ├── ai_trackdown_collector.py # Ticket data collector
│   └── framework_services.py     # Service data collector
├── interfaces/                    # Service interfaces
│   ├── __init__.py
│   └── health.py                 # Health interface
├── models/                        # Data models
│   ├── __init__.py
│   └── health.py                 # Health models
├── scripts/                       # Framework scripts
│   ├── __init__.py
│   ├── security_cli.py           # Security CLI
│   └── service_manager.py        # Service management
└── utils/                         # Utility functions
    ├── __init__.py
    ├── model_context.py          # Context utilities
    └── performance.py            # Performance utilities
```

### `framework/` - Agent Definitions

**Purpose**: Agent role definitions, coordination protocols, and templates

```
framework/
├── CLAUDE.md                      # Framework configuration
├── LOCAL_SERVICES.md              # Local service documentation
├── agent-roles/                   # Agent definitions
│   ├── DELEGATION_ORDERS.md       # Delegation protocols
│   ├── ENHANCEMENT_REQUIREMENTS.md
│   ├── ENHANCEMENT_STATUS.md
│   ├── agents.json                # Agent registry
│   ├── architect-agent.md         # Architect agent definition
│   ├── code-organizer-agent.md    # Code organizer agent
│   ├── code-review-engineer-agent.md
│   ├── data-agent.md              # Data agent definition
│   ├── documentation-agent.md     # Documentation agent
│   ├── engineer-agent.md          # Engineer agent definition
│   ├── integration-agent.md       # Integration agent
│   ├── ops-agent.md               # Operations agent
│   ├── performance-agent.md       # Performance agent
│   ├── qa-agent.md                # QA agent definition
│   ├── research-agent.md          # Research agent
│   ├── security-agent.md          # Security agent
│   └── backups/                   # Agent definition backups
├── commands/                      # Framework commands
│   ├── settings.local.json        # Local command settings
│   └── commands/
│       └── pm-daily-standup.md    # Daily standup command
├── coordination/                  # Multi-agent coordination
│   ├── README.md                  # Coordination overview
│   ├── COORDINATION_IMPLEMENTATION_SPECS.md
│   ├── COORDINATION_OPERATING_PROCEDURES.md
│   ├── MULTI_AGENT_COORDINATION_ARCHITECTURE.md
│   └── FWK-007_COMPLETION_SUMMARY.md
├── multi-agent/                   # Multi-agent utilities
│   ├── git-worktree-manager.py    # Git worktree management
│   └── parallel-execution-framework.py
├── subprocess-protocols/          # Subprocess protocols
│   └── engineer-protocol.md       # Engineer protocol
└── templates/                     # Framework templates
    ├── CLAUDE.md                  # Project CLAUDE.md template
    ├── DEPLOYMENT_WORKFLOW.md     # Deployment workflow
    ├── INSTRUCTIONS.md            # Instructions template
    ├── PROJECT.md                 # Project template
    ├── TOOLCHAIN.md               # Toolchain template
    └── WORKFLOW.md                # Workflow template
```

### `tasks/` - AI-Trackdown Hierarchical Structure

**Purpose**: Hierarchical ticket management using ai-trackdown-tools

```
tasks/
├── epics/                         # Strategic epics
│   ├── EP-0003-framework-core-infrastructure.md
│   ├── EP-0004-memory-ai-integration.md
│   ├── EP-0005-multi-agent-architecture.md
│   ├── EP-0006-tracking-monitoring.md
│   ├── EP-0007-deployment-operations.md
│   ├── EP-0008-documentation-quality.md
│   ├── EP-0010-ai-code-review-enhancement.md
│   ├── EP-0011-test-epic.md
│   ├── EP-0014-template-fallback-test.md
│   ├── EP-0016-core-framework-development.md
│   └── EP-0020-test-epic-structure.md
├── issues/                        # Implementation issues
│   ├── ISS-0001-ai-trackdown-tools-cutover-implementation.md
│   ├── ISS-0002-comprehensive-health-slash-command.md
│   ├── ISS-0003-convert-managed-projects-to-ai-trackdown.md
│   ├── ISS-0018-test-issue-template.md
│   ├── ISS-0019-fix-cli-template-errors-preventing-ticket-creation.md
│   └── ISS-0021-test-issue-association.md
├── tasks/                         # Development tasks
│   ├── TSK-0001-complete-ticket-data-migration.md
│   ├── TSK-0002-validate-cli-functionality.md
│   └── epics/                     # Task grouping by epic
├── prs/                           # Pull requests (reserved)
└── templates/                     # Ticket templates
    ├── epic-default.yaml          # Epic template
    ├── issue-default.yaml         # Issue template
    └── task-default.yaml          # Task template
```

### `templates/` - Project Templates

**Purpose**: Standardized project templates for consistent project setup

```
templates/
├── deployment-claude.md           # Deployment CLAUDE.md template
├── epic-default.yaml             # Epic template
├── issue-default.yaml            # Issue template
├── task-default.yaml             # Task template
└── managed-project/               # Managed project template
    ├── CLAUDE.md.template         # Project CLAUDE.md template
    ├── README.md.template         # Project README template
    ├── config/                    # Configuration templates
    │   ├── nodejs/                # Node.js configuration
    │   │   ├── biome.json.template
    │   │   ├── package.json.template
    │   │   └── tsconfig.json.template
    │   └── python/                # Python configuration
    │       └── pyproject.toml.template
    ├── docs/                      # Documentation templates
    │   ├── INSTRUCTIONS.md.template
    │   ├── PROJECT.md.template
    │   ├── TOOLCHAIN.md.template
    │   └── WORKFLOW.md.template
    └── trackdown/                 # Trackdown templates
        ├── BACKLOG.md.template
        ├── MILESTONES.md.template
        ├── scripts/
        │   └── update-progress.py
        └── templates/
            ├── implementation-task-template.md
            └── phase-milestone-template.md
```

### `docs/` - Documentation System

**Purpose**: Comprehensive framework documentation and guides

```
docs/
├── INDEX.md                       # Documentation index
├── FRAMEWORK_OVERVIEW.md          # Framework overview
├── QUICK_START.md                 # Quick start guide
├── AGENT_DELEGATION_GUIDE.md      # Agent delegation guide
├── DEPLOYMENT_GUIDE.md            # Deployment guide
├── HEALTH_MONITORING.md           # Health monitoring
├── MEMORY_SETUP_GUIDE.md          # Memory setup guide
├── TICKETING_SYSTEM.md            # Ticketing system guide
├── PYTHON_STANDARDS.md            # Python standards
├── user-guide/                    # User guides
│   ├── 01-getting-started.md
│   ├── 02-architecture-concepts.md
│   ├── 03-slash-commands-orchestration.md
│   └── 04-directory-organization.md    # This file
├── user-guides/                   # Additional user guides
│   └── PM_ASSISTANT_GUIDE.md
├── design/                        # Design documents
│   ├── claude-pm-max-mem0.md
│   └── claude-pm-task-delegation-architecture.md
├── archive/                       # Archived documentation
│   ├── completion-reports/
│   ├── langgraph-historical/
│   └── qa-reports/
└── services.md                    # Services documentation
```

---

## 🤖 Agent-Specific Organization

### Agent Workspace Patterns

Each agent operates within defined workspace boundaries while maintaining access to shared resources:

#### Git Worktree Pattern

```
/Users/masa/Projects/
├── claude-multiagent-pm/          # Main framework
├── managed/                       # Managed projects
│   ├── project-a/
│   │   ├── main/                  # Main worktree
│   │   ├── agent-engineer/        # Engineer agent worktree
│   │   ├── agent-qa/              # QA agent worktree
│   │   └── agent-security/        # Security agent worktree
│   └── project-b/
│       ├── main/
│       ├── agent-architect/
│       └── agent-ops/
└── shared/                        # Shared resources
    ├── templates/
    ├── scripts/
    └── documentation/
```

#### Agent Isolation Boundaries

```
Agent Workspace Structure:
├── Input Boundary
│   ├── Task specification
│   ├── Context data
│   └── Shared resources
├── Processing Boundary
│   ├── Agent-specific workspace
│   ├── Isolated execution environment
│   └── Memory context
└── Output Boundary
    ├── Deliverables
    ├── Status updates
    └── Shared artifacts
```

### Agent Directory Access Patterns

| Agent Type | Read Access | Write Access | Shared Resources |
|------------|-------------|--------------|------------------|
| **Architect** | Framework, docs, templates | Design docs, architecture | Shared templates |
| **Engineer** | Framework, src, tests | Code, implementations | Code standards |
| **QA** | Framework, src, tests | Test results, reports | Test utilities |
| **Security** | Framework, src, config | Security reports, audits | Security policies |
| **Operations** | Framework, deployment | Deployment configs, logs | Deployment scripts |
| **Documentation** | Framework, docs | Documentation files | Style guides |

---

## ⚙️ Configuration Management

### Configuration Hierarchy

```
Configuration Structure:
├── Global Framework Config
│   ├── ~/.claude-multiagent-pm/config/config.yaml    # Main configuration
│   ├── ~/.claude-multiagent-pm/agents/user-defined/  # User agents
│   ├── ~/.claude-multiagent-pm/templates/            # User templates
│   ├── ~/.claude-multiagent-pm/logs/                 # System logs
│   └── framework/LOCAL_SERVICES.md                   # Service config
├── Project-Specific Config
│   ├── CLAUDE.md                        # Project instructions
│   ├── trackdown/                       # Project ticketing
│   └── config/                          # Project configuration
└── Agent-Specific Config
    ├── framework/agent-roles/           # Agent definitions
    ├── framework/commands/              # Command configs
    └── framework/coordination/          # Coordination configs
```

### Configuration File Patterns

#### Global Configuration (`~/.claude-multiagent-pm/config/config.yaml`)

```yaml
version: "4.2.0"
deployment_date: "2025-07-09T00:17:59.081Z"
platform: "darwin"
python_command: "python3"
ai_trackdown_integration: true
framework_path: "/Users/masa/Projects/claude-multiagent-pm"
memory_service:
  enabled: true
  endpoint: "http://localhost:8002"
  cache_ttl: 3600
agent_coordination:
  max_concurrent: 5
  default_timeout: 300
  git_worktree_enabled: true
user_agents_dir: "~/.claude-multiagent-pm/agents/user-defined"
templates_dir: "~/.claude-multiagent-pm/templates"
training_modifications_dir: "~/.claude-multiagent-pm/agents/training-modifications"
```

#### Project Configuration (`CLAUDE.md`)

```markdown
# Project: My AI Application

## AI Assistant Role
You are working on an AI-enhanced web application using CMPM.

### Project Context
- **Type**: Web application
- **Language**: Python/TypeScript
- **Framework**: FastAPI + React
- **Database**: PostgreSQL
- **AI Integration**: mem0AI enabled

### Directory Structure
- `src/` - Source code
- `tests/` - Test suite
- `docs/` - Documentation
- `config/` - Configuration files
- `trackdown/` - Project tickets
```

### Environment Variable Patterns

```bash
# Framework Environment Variables
export CLAUDE_PM_HOME="/Users/masa/Projects/claude-multiagent-pm"
export CLAUDE_PM_CONFIG_DIR="~/.claude-multiagent-pm"
export CLAUDE_PM_USER_AGENTS_DIR="~/.claude-multiagent-pm/agents/user-defined"
export CLAUDE_PM_TEMPLATES_DIR="~/.claude-multiagent-pm/templates"
export CLAUDE_PM_PYTHON_CMD="python3"
export CLAUDE_PM_MEMORY_URL="http://localhost:8002"

# Project Environment Variables
export PROJECT_ROOT="/Users/masa/Projects/managed/my-project"
export PROJECT_CONFIG_DIR="$PROJECT_ROOT/.claude-multiagent-pm"
export PROJECT_MEMORY_ENABLED="true"
export PROJECT_AGENTS_ENABLED="engineer,qa,security"

# Agent Environment Variables
export AGENT_WORKSPACE="/tmp/agent-workspaces"
export AGENT_ISOLATION_ENABLED="true"
export AGENT_MEMORY_CONTEXT="project-specific"
```

---

## 🏢 Multi-Project Organization

### Portfolio Structure

```
/Users/masa/Projects/
├── claude-multiagent-pm/          # 🧠 Framework core
├── managed/                       # 📁 Managed projects
│   ├── web-app-alpha/
│   │   ├── CLAUDE.md              # Project configuration
│   │   ├── src/                   # Source code
│   │   ├── tests/                 # Test suite
│   │   ├── docs/                  # Project documentation
│   │   ├── config/                # Project config
│   │   └── trackdown/             # Project tickets
│   ├── api-service-beta/
│   │   ├── CLAUDE.md
│   │   ├── src/
│   │   ├── tests/
│   │   ├── docs/
│   │   ├── config/
│   │   └── trackdown/
│   └── ml-pipeline-gamma/
│       ├── CLAUDE.md
│       ├── src/
│       ├── tests/
│       ├── docs/
│       ├── config/
│       └── trackdown/
├── shared/                        # 🔄 Shared resources
│   ├── templates/                 # Common templates
│   ├── scripts/                   # Utility scripts
│   ├── documentation/             # Shared docs
│   └── configurations/            # Common configs
└── archives/                      # 📦 Archived projects
    ├── completed/
    ├── deprecated/
    └── experimental/
```

### Project Lifecycle Management

#### Project States and Directory Organization

```
Project Lifecycle:
├── Planning Phase
│   ├── /planning/                 # Planning documents
│   ├── /research/                 # Research materials
│   └── /requirements/             # Requirements docs
├── Development Phase
│   ├── /src/                      # Source code
│   ├── /tests/                    # Test suite
│   ├── /docs/                     # Documentation
│   └── /trackdown/                # Active tickets
├── Deployment Phase
│   ├── /deployment/               # Deployment configs
│   ├── /monitoring/               # Monitoring setup
│   └── /infrastructure/           # Infrastructure code
├── Maintenance Phase
│   ├── /maintenance/              # Maintenance docs
│   ├── /updates/                  # Update logs
│   └── /backups/                  # Backup configurations
└── Archive Phase
    ├── /archive/                  # Archived materials
    ├── /legacy/                   # Legacy code
    └── /documentation/            # Final documentation
```

### Cross-Project Dependencies

```
Dependency Management:
├── Shared Libraries
│   ├── /Users/masa/Projects/shared/lib/
│   ├── /Users/masa/Projects/shared/utils/
│   └── /Users/masa/Projects/shared/configs/
├── Template Dependencies
│   ├── Framework templates
│   ├── Project templates
│   └── Agent templates
├── Service Dependencies
│   ├── Memory service (localhost:8002)
│   ├── Health monitoring
│   └── Deployment services
└── Configuration Dependencies
    ├── Global framework config
    ├── Shared environment variables
    └── Common security policies
```

---

## 📝 Naming Conventions

### File and Directory Naming

#### Directory Naming Patterns

```
Convention Rules:
├── Framework Directories: kebab-case
│   ├── claude-multiagent-pm/
│   ├── ai-trackdown-project/
│   └── managed-project/
├── Service Directories: snake_case
│   ├── claude_pm/
│   ├── memory_service/
│   └── health_monitor/
├── Project Directories: kebab-case
│   ├── web-app-alpha/
│   ├── api-service-beta/
│   └── ml-pipeline-gamma/
└── Agent Directories: agent-[role]
    ├── agent-engineer/
    ├── agent-qa/
    └── agent-security/
```

#### File Naming Patterns

```
File Types and Conventions:
├── Python Files: snake_case.py
│   ├── memory_service.py
│   ├── health_monitor.py
│   └── project_indexer.py
├── Configuration Files: kebab-case.format
│   ├── doc-sync-config.json
│   ├── health-monitoring-config.json
│   └── enhanced-doc-sync-config.json
├── Documentation Files: UPPER_CASE.md
│   ├── README.md
│   ├── CLAUDE.md
│   ├── FRAMEWORK_OVERVIEW.md
│   └── DEPLOYMENT_GUIDE.md
├── Template Files: [name].template
│   ├── CLAUDE.md.template
│   ├── README.md.template
│   └── package.json.template
└── Ticket Files: [TYPE]-[ID]-[description].md
    ├── EP-0001-project-setup.md
    ├── ISS-0001-memory-integration.md
    └── TSK-0001-implement-auth.md
```

### Versioning and Tagging

#### Version Control Integration

```
Git Integration Patterns:
├── Branch Naming
│   ├── main                       # Main branch
│   ├── develop                    # Development branch
│   ├── feature/[ticket-id]        # Feature branches
│   ├── hotfix/[issue-id]          # Hotfix branches
│   └── release/[version]          # Release branches
├── Tag Naming
│   ├── v[major].[minor].[patch]   # Version tags
│   ├── release-[date]             # Release tags
│   └── snapshot-[timestamp]       # Snapshot tags
└── Commit Conventions
    ├── feat: [description]        # New features
    ├── fix: [description]         # Bug fixes
    ├── docs: [description]        # Documentation
    ├── refactor: [description]    # Code refactoring
    └── test: [description]        # Test additions
```

---

## 📐 Best Practices

### Directory Structure Best Practices

#### 1. Logical Grouping

```
Grouping Principles:
├── By Function
│   ├── /src/                      # Source code
│   ├── /tests/                    # Test files
│   ├── /docs/                     # Documentation
│   └── /config/                   # Configuration
├── By Domain
│   ├── /authentication/           # Auth domain
│   ├── /user-management/          # User domain
│   └── /reporting/                # Reporting domain
├── By Layer
│   ├── /api/                      # API layer
│   ├── /service/                  # Service layer
│   ├── /data/                     # Data layer
│   └── /ui/                       # UI layer
└── By Responsibility
    ├── /framework/                # Framework code
    ├── /business/                 # Business logic
    ├── /infrastructure/           # Infrastructure
    └── /utilities/                # Utility functions
```

#### 2. Scalability Considerations

```
Scalability Patterns:
├── Horizontal Scaling
│   ├── /projects/[project-name]/  # Project separation
│   ├── /services/[service-name]/  # Service separation
│   └── /agents/[agent-type]/      # Agent separation
├── Vertical Scaling
│   ├── /core/                     # Core functionality
│   ├── /extensions/               # Extension points
│   └── /plugins/                  # Plugin system
├── Team Scaling
│   ├── /team-alpha/               # Team workspaces
│   ├── /team-beta/                # Team workspaces
│   └── /shared/                   # Shared resources
└── Technology Scaling
    ├── /python/                   # Python projects
    ├── /nodejs/                   # Node.js projects
    ├── /rust/                     # Rust projects
    └── /polyglot/                 # Multi-language projects
```

#### 3. Maintenance and Cleanup

```
Maintenance Practices:
├── Regular Cleanup
│   ├── Archive old projects
│   ├── Remove unused files
│   ├── Clean up temporary files
│   └── Organize documentation
├── Documentation Maintenance
│   ├── Update README files
│   ├── Review documentation accuracy
│   ├── Update configuration examples
│   └── Maintain change logs
├── Configuration Management
│   ├── Review and update configs
│   ├── Remove deprecated settings
│   ├── Update environment variables
│   └── Validate configuration files
└── Performance Optimization
    ├── Profile directory access
    ├── Optimize file organization
    ├── Implement caching strategies
    └── Monitor resource usage
```

### Security Best Practices

#### 1. Access Control

```
Security Patterns:
├── File Permissions
│   ├── 755 for directories
│   ├── 644 for regular files
│   ├── 600 for configuration files
│   └── 700 for sensitive directories
├── Directory Isolation
│   ├── Agent workspace isolation
│   ├── Project boundary enforcement
│   ├── Temporary file cleanup
│   └── Log file protection
└── Configuration Security
    ├── Environment variable usage
    ├── Secret management
    ├── Configuration validation
    └── Audit logging
```

#### 2. Backup and Recovery

```
Backup Strategies:
├── Configuration Backups
│   ├── Daily .claude-pm/ backup
│   ├── Weekly full config backup
│   └── Monthly archive creation
├── Project Backups
│   ├── Git repository backups
│   ├── Database backups
│   └── Asset backups
├── Recovery Procedures
│   ├── Configuration restore
│   ├── Project recovery
│   ├── Service restoration
│   └── Data recovery
└── Disaster Recovery
    ├── Off-site backups
    ├── Recovery testing
    ├── Documentation updates
    └── Process validation
```

---

## 🔄 Migration Patterns

### Migrating Existing Projects

#### 1. Assessment Phase

```bash
# Assess current project structure
find /path/to/existing/project -type d -name "*" | head -20
ls -la /path/to/existing/project/

# Identify migration requirements
echo "Current structure:" > migration-assessment.md
tree /path/to/existing/project >> migration-assessment.md

# Analyze dependencies
grep -r "import\|require\|include" /path/to/existing/project/src/ | head -10
```

#### 2. Migration Strategy

```
Migration Steps:
├── Phase 1: Structure Analysis
│   ├── Document current structure
│   ├── Identify dependencies
│   ├── Map to CMPM patterns
│   └── Plan migration steps
├── Phase 2: Template Application
│   ├── Create CLAUDE.md
│   ├── Set up trackdown/ directory
│   ├── Configure project settings
│   └── Apply naming conventions
├── Phase 3: Integration
│   ├── Integrate with framework
│   ├── Configure agents
│   ├── Set up memory integration
│   └── Test functionality
└── Phase 4: Validation
    ├── Validate structure
    ├── Test agent access
    ├── Verify configuration
    └── Document changes
```

#### 3. Migration Scripts

```bash
#!/bin/bash
# migrate-to-cmpm.sh

PROJECT_PATH=$1
PROJECT_NAME=$2

echo "🔄 Migrating $PROJECT_NAME to CMPM structure"

# Create CMPM directories
mkdir -p "$PROJECT_PATH"/{docs,config,trackdown,tests}

# Copy templates
cp /Users/masa/Projects/claude-multiagent-pm/templates/managed-project/CLAUDE.md.template \
   "$PROJECT_PATH/CLAUDE.md"

# Set up trackdown
cp /Users/masa/Projects/claude-multiagent-pm/templates/managed-project/trackdown/BACKLOG.md.template \
   "$PROJECT_PATH/trackdown/BACKLOG.md"

# Configure project
sed -i '' "s/PROJECT_NAME/$PROJECT_NAME/g" "$PROJECT_PATH/CLAUDE.md"

# Initialize git worktrees if needed
if [ -d "$PROJECT_PATH/.git" ]; then
    cd "$PROJECT_PATH"
    git worktree add agent-engineer
    git worktree add agent-qa
fi

echo "✅ Migration completed for $PROJECT_NAME"
```

### Framework Updates

#### 1. Framework Version Migration

```bash
# Check current version
cat /Users/masa/Projects/claude-multiagent-pm/VERSION

# Backup current configuration
cp -r /Users/masa/Projects/claude-multiagent-pm/.claude-pm/ \
      /Users/masa/Projects/claude-multiagent-pm/backups/config-$(date +%Y%m%d)/

# Update framework
cd /Users/masa/Projects/claude-multiagent-pm
git pull origin main

# Migrate configuration
./scripts/migrate-config.sh --from-version 4.0.0 --to-version 4.2.0

# Validate migration
./scripts/health-check.sh
```

#### 2. Project Structure Updates

```bash
# Update managed projects
for project in /Users/masa/Projects/managed/*/; do
    echo "Updating $project"
    
    # Update CLAUDE.md template
    if [ -f "$project/CLAUDE.md" ]; then
        ./scripts/update-claude-md.sh "$project"
    fi
    
    # Update trackdown structure
    if [ -d "$project/trackdown" ]; then
        ./scripts/update-trackdown.sh "$project"
    fi
    
    # Update configuration
    if [ -f "$project/.claude-pm/config.json" ]; then
        ./scripts/update-project-config.sh "$project"
    fi
done
```

---

## 🎯 Quick Reference

### Essential Directory Commands

```bash
# Framework navigation
cd /Users/masa/Projects/claude-multiagent-pm
ls -la claude_pm/services/          # Framework services
ls -la framework/agent-roles/       # Agent definitions
ls -la tasks/epics/                 # Epic tickets
ls -la docs/user-guide/             # User documentation

# Project navigation
cd /Users/masa/Projects/managed/my-project
ls -la src/                         # Source code
ls -la tests/                       # Test files
ls -la trackdown/                   # Project tickets
ls -la config/                      # Project configuration

# Quick structure validation
tree -d -L 3 /Users/masa/Projects/claude-multiagent-pm/
find /Users/masa/Projects/managed/ -name "CLAUDE.md" -exec ls -la {} \;
```

### Directory Creation Templates

```bash
# Create new managed project
mkdir -p /Users/masa/Projects/managed/new-project/{src,tests,docs,config,trackdown}

# Create agent workspace
mkdir -p /tmp/agent-workspaces/{engineer,qa,security,architect}

# Create configuration directory
mkdir -p ~/.claude-multiagent-pm/{config,logs,agents/user-defined,templates,cache,backups}

# Create template directory
mkdir -p /Users/masa/Projects/templates/{python,nodejs,rust,polyglot}
```

### Common File Patterns

```bash
# Find configuration files
find /Users/masa/Projects/claude-multiagent-pm -name "*.json" -o -name "*.yaml" -o -name "*.yml"

# Find documentation files
find /Users/masa/Projects/claude-multiagent-pm -name "*.md" | grep -E "(README|CLAUDE|GUIDE)"

# Find Python files
find /Users/masa/Projects/claude-multiagent-pm -name "*.py" | head -20

# Find template files
find /Users/masa/Projects/claude-multiagent-pm -name "*.template"
```

---

## 📚 Related Documentation

### Framework Documentation
- [Getting Started Guide](01-getting-started.md)
- [Architecture Concepts](02-architecture-concepts.md)
- [Slash Commands & Orchestration](03-slash-commands-orchestration.md)
- [Framework Overview](../FRAMEWORK_OVERVIEW.md)

### Configuration Guides
- [Memory Setup Guide](../MEMORY_SETUP_GUIDE.md)
- [Deployment Guide](../DEPLOYMENT_GUIDE.md)
- [Health Monitoring](../HEALTH_MONITORING.md)

### Agent Documentation
- [Agent Delegation Guide](../AGENT_DELEGATION_GUIDE.md)
- [Framework Overview](../FRAMEWORK_OVERVIEW.md)

---

**Framework Version**: 4.2.0  
**Last Updated**: 2025-07-09  
**Documentation Version**: 1.0.0  
**Author**: Claude Technical Documentation Agent  
**Review Status**: Ready for Production Use

---

*This directory organization guide is designed to scale with your project needs while maintaining consistency with CMPM best practices. For questions or suggestions, please consult the framework documentation or reach out to the development team.*