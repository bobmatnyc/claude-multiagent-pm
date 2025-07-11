# Claude-MultiAgent-PM Framework Architecture Knowledge Base

## Framework Overview
**Framework Version**: 4.5.1  
**Deployment Date**: 2025-07-11  
**Platform**: Darwin (macOS)  
**Deployment Type**: Local Development  

## Core Architecture Components

### 1. Framework Core (`claude_pm/`)
Primary framework modules providing the foundational infrastructure:

#### Core Services
- `services/multi_agent_orchestrator.py` - Central agent coordination and task delegation
- `services/intelligent_task_planner.py` - AI-powered task planning and prioritization
- `services/health_dashboard.py` - System health monitoring and diagnostics
- `services/parent_directory_manager.py` - Directory structure and deployment management

#### Core Infrastructure
- `core/config.py` - Global configuration management
- `core/enforcement.py` - Framework rules and policy enforcement
- `core/service_manager.py` - Service lifecycle management
- `core/base_service.py` - Base service class for all framework services
- `core/base_agent.py` - Base agent class for all agent implementations
- `core/agent_config.py` - Agent configuration and metadata management
- `core/connection_manager.py` - Inter-service communication management

#### Command Interface
- `cmpm_commands.py` - Core command implementations
- `commands/health_commands.py` - Health monitoring commands
- `commands/template_commands.py` - Template management commands

#### Memory Integration
- `config/memory_trigger_config.py` - Memory system trigger configuration
- Integration with mem0AI v0.1.113 for persistent context and learning

### 2. Configuration System (`.claude-pm/`)
Project-specific configuration and agent management:

#### Agent Hierarchy
- `agents/project-specific/` - Project-level agent implementations (highest priority)
- `agents/user-defined/` - User-level agent customizations (medium priority)  
- `agents/system-trained/` - Framework-provided system agents (lowest priority)
- `agents/hierarchy.yaml` - Agent hierarchy configuration and loading rules
- `agents/registry.json` - Agent registration and health tracking

#### Template Management
- `template_manager/registry/templates.json` - Template registry and metadata
- `template_manager/registry/versions.json` - Template versioning information
- `template_manager/registry/conflicts.json` - Template conflict resolution

#### Configuration Files
- `config.json` - Project-specific configuration
- `ai_ops_config.json` - AI operations configuration
- `config/dependencies.yaml` - Dependency management configuration

### 3. Deployment Infrastructure (`scripts/`, `bin/`)

#### CLI Wrappers
- `bin/claude-pm` - Primary CLI interface with system info and CLAUDE.md management
- `bin/cmpm` - Claude MultiAgent PM command interface
- `bin/aitrackdown` - AI-trackdown tools integration
- `bin/atd` - Alias for aitrackdown

#### Deployment Scripts
- `scripts/health-check.py` - Comprehensive health validation
- `scripts/sync-scripts.sh` - Script synchronization automation
- Various deployment and maintenance scripts

### 4. Framework Templates (`framework/`)
- `CLAUDE.md` - Framework configuration template with Handlebars variables
- Agent templates and configuration patterns
- Deployment templates and automation scripts

## Three-Tier Agent Hierarchy

### Priority Order (Highest to Lowest)
1. **Project Agents** (`$PROJECT/.claude-pm/agents/project-specific/`)
   - Project-specific implementations and overrides
   - Highest precedence for project context
   - Example: claude-multiagent-pm-ops-agent

2. **User Agents** (`~/.local/.claude-pm/agents/user-defined/`)
   - User-specific customizations across all projects
   - Mid-priority, can override system defaults
   - Personal workflow and preference agents

3. **System Agents** (`claude_pm/agents/`)
   - Core framework functionality
   - Lowest precedence but always available as fallback
   - Framework-provided base implementations

### Agent Loading Rules
- **three-tier hierarchy**: Project → User → System (with automatic fallback)
- **Precedence**: Project tier has highest priority, System tier provides fallback
- **Validation**: All agents validated during hierarchy initialization
- **Registration**: Automatic registration in `agents/registry.json`
- **Health Monitoring**: Continuous health checking and status reporting

## CLAUDE.md Deployment Tree Management

### Template System
- **Source Template**: `framework/CLAUDE.md`
- **Variable Substitution**: Handlebars-based variable replacement
- **Deployment Targets**: Multiple deployment locations with automatic management

### Variable Substitution
Key variables automatically replaced during deployment:
```handlebars
{{FRAMEWORK_VERSION}} - Current framework version (4.5.1)
{{DEPLOYMENT_DATE}} - Deployment timestamp
{{DEPLOYMENT_DIR}} - Target deployment directory
{{PLATFORM}} - Operating system platform
{{PYTHON_CMD}} - Python command path
{{AI_TRACKDOWN_PATH}} - AI-trackdown tools path
```

### Deployment Tree Cleanup
- Automatic detection and cleanup of duplicate CLAUDE.md files
- Maintenance of single authoritative CLAUDE.md per deployment level
- Backup creation before cleanup operations

## Memory System Integration (mem0AI v0.1.113)

### Architecture
- **Backend**: Removed TinyDB and InMemory backends for performance
- **Configuration**: Memory trigger-based activation
- **Integration Points**: Framework services and agent coordination
- **Persistence**: Long-term memory and context retention

### Key Features
- Context-aware memory management
- Cross-session learning and adaptation
- Agent memory sharing and coordination
- Performance-optimized memory operations

## AI-Trackdown Tools Integration

### Node.js Integration
- **CLI Interface**: `bin/aitrackdown` and `bin/atd`
- **Ticketing System**: Universal ticketing interface across platforms
- **Task Management**: Integration with framework task planning
- **Health Monitoring**: AI-trackdown service health validation

### Features
- Cross-platform ticket management
- Automated issue tracking and resolution
- Integration with framework agent coordination
- Performance monitoring and optimization

## Script Synchronization System

### Sync Architecture
- **Source**: `/Users/masa/Projects/claude-multiagent-pm/scripts`
- **Target**: `/Users/masa/.local/scripts`
- **Method**: rsync with validation and backup
- **Automation**: Integrated with deployment operations

### Validation
- Pre-sync validation of source scripts
- Post-sync execution testing
- Permission validation and correction
- Rollback capability on failure

## Health Monitoring and Diagnostics

### Monitoring Components
- **Framework Services**: Core service health and performance
- **Agent Hierarchy**: Agent availability and functionality
- **Integration Status**: External service connectivity
- **Performance Metrics**: Response times and resource usage
- **Configuration Integrity**: Config file validation and consistency

### Diagnostic Capabilities
- **Automated Health Checks**: Continuous monitoring and alerting
- **Performance Analysis**: Bottleneck identification and optimization
- **Integration Testing**: End-to-end service validation
- **Issue Detection**: Proactive problem identification
- **Recovery Procedures**: Automated recovery and restoration

## Development Workflow

### Local Development Setup
1. Framework initialization via `cmcp-init --setup`
2. Agent hierarchy validation via `cmcp-init --verify`
3. Health check execution via `scripts/health-check.py`
4. Integration testing and validation

### Deployment Workflow
1. **Preparation**: Source validation and backup creation
2. **Synchronization**: Script and binary deployment
3. **Configuration**: CLAUDE.md deployment and variable substitution
4. **Validation**: Comprehensive health checks and integration testing
5. **Activation**: Service startup and monitoring activation

### Maintenance Procedures
- **Regular Health Checks**: Automated monitoring and alerting
- **Incremental Updates**: Sync-based update deployment
- **Performance Optimization**: Monitoring and tuning
- **Backup Management**: Regular backup creation and validation
- **Security Monitoring**: Access control and audit logging

## Performance Optimization

### Key Performance Areas
- **Agent Loading**: Lazy loading and caching strategies
- **Service Communication**: Connection pooling and optimization
- **Memory Management**: Efficient memory usage and cleanup
- **Script Execution**: Parallel execution and optimization
- **Integration Performance**: External service optimization

### Monitoring Metrics
- Agent initialization and response times
- Service communication latency
- Memory usage and optimization effectiveness
- Script execution performance
- Integration connectivity and performance

## Security and Access Control

### Security Measures
- **Script Validation**: Permission and content validation
- **Configuration Security**: Secure handling of sensitive configuration
- **Access Control**: Role-based access to operations
- **Audit Logging**: Comprehensive operation logging
- **Backup Security**: Secure backup storage and access

### Best Practices
- Regular security validation and updates
- Principle of least privilege for agent operations
- Secure communication between framework components
- Regular audit log review and analysis
- Incident response and recovery procedures

## Troubleshooting Knowledge

### Common Issues and Resolutions
1. **Script Sync Failures**: Permission issues, disk space, network connectivity
2. **Agent Loading Failures**: Missing dependencies, configuration errors, hierarchy issues
3. **Memory System Issues**: Service connectivity, configuration problems, performance
4. **Integration Failures**: External service availability, authentication, configuration
5. **Performance Issues**: Resource exhaustion, service conflicts, optimization needs

### Diagnostic Procedures
- **Health Check Execution**: Comprehensive system validation
- **Log Analysis**: Error pattern identification and resolution
- **Performance Profiling**: Bottleneck identification and optimization
- **Integration Testing**: End-to-end service validation
- **Recovery Testing**: Backup and recovery validation

This knowledge base provides comprehensive understanding of the claude-multiagent-pm framework architecture, enabling effective operations, troubleshooting, and optimization of the local development deployment.