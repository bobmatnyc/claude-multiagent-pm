# Architecture Guide

## Overview

The Claude PM Framework is a multi-agent orchestration system designed for AI-driven development workflows. It follows a modular, extensible architecture that enables seamless integration of custom agents while maintaining high performance and reliability.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface Layer                      │
│              (claude-pm, cmpm commands)                      │
├─────────────────────────────────────────────────────────────┤
│                  Orchestration Layer                         │
│            (PM Orchestrator, Task Tool)                      │
├─────────────────────────────────────────────────────────────┤
│                    Agent Layer                               │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│     │ Core Agents │  │ User Agents │  │Custom Agents│     │
│     └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                   Service Layer                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Registry │ │  Cache   │ │ Health   │ │ Template │      │
│  │ Service  │ │ Service  │ │ Monitor  │ │ Manager  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    Core Layer                                │
│         (Configuration, Logging, Utilities)                  │
└─────────────────────────────────────────────────────────────┘
```

### Component Overview

#### 1. CLI Interface Layer
- **Purpose**: Provides command-line interface for user interaction
- **Components**:
  - `claude-pm`: Main CLI entry point
  - `cmpm`: Productivity commands interface
  - CLI flag processing and validation

#### 2. Orchestration Layer
- **Purpose**: Coordinates multi-agent workflows and task delegation
- **Key Components**:
  - **PM Orchestrator**: Central workflow coordinator
  - **Task Tool**: Subprocess creation and management
  - **TodoWrite Integration**: Task tracking and status management

#### 3. Agent Layer
- **Purpose**: Executes specialized tasks through domain-specific agents
- **Agent Types**:
  - **Core Agents** (9): Documentation, Ticketing, Version Control, QA, Research, Ops, Security, Engineer, Data Engineer
  - **User Agents**: Custom agents with directory-based precedence
  - **System Agents**: Framework-provided fallback agents

#### 4. Service Layer
- **Purpose**: Provides shared services across the framework
- **Core Services**:
  - **Agent Registry**: Dynamic agent discovery and management
  - **SharedPromptCache**: 99.7% performance improvement through caching
  - **Health Monitor**: System health and performance monitoring
  - **Template Manager**: Configuration and template processing

#### 5. Core Layer
- **Purpose**: Foundation utilities and cross-cutting concerns
- **Components**:
  - Configuration management
  - Logging infrastructure
  - Error handling
  - Utility functions

## Key Design Patterns

### 1. Two-Tier Agent Architecture

The framework uses a simplified two-tier agent hierarchy:

```
User Agents (Filesystem-based)
├── Current Directory: $PWD/.claude-pm/agents/
├── Parent Directories: ../.claude-pm/agents/
└── User Home: ~/.claude-pm/agents/

System Agents (Code-based)
└── Framework: claude_pm/agents/
```

### 2. Agent Registry Pattern

Dynamic agent discovery with precedence-based selection:

```python
# Pseudo-code representation
registry = AgentRegistry()
agents = registry.listAgents(
    specializations=['performance', 'monitoring'],
    scope='all'  # Searches all tiers with precedence
)
optimal_agent = registry.selectOptimalAgent(agents, task_type)
```

### 3. Task Delegation Pattern

Standardized subprocess creation for agent coordination:

```
PM Orchestrator → Task Tool → Agent Subprocess
                    ↓
              Context Filtering
                    ↓
              Agent Execution
                    ↓
              Result Integration
```

### 4. Performance Optimization

#### SharedPromptCache
- **Purpose**: Reduce agent loading time by 99.7%
- **Implementation**: LRU cache with automatic invalidation
- **Usage**: Transparent caching of agent prompts and configurations

#### Lazy Loading
- Agents loaded only when needed
- Configuration loaded on-demand
- Service initialization deferred until first use

## Data Flow

### 1. Command Execution Flow

```
User Command → CLI Parser → Command Handler
                              ↓
                        PM Orchestrator
                              ↓
                    Agent Task Delegation
                              ↓
                      Agent Execution
                              ↓
                      Result Aggregation
                              ↓
                        User Output
```

### 2. Agent Discovery Flow

```
Task Requirement → Agent Registry
                        ↓
                 Directory Scanning
                        ↓
                Precedence Resolution
                        ↓
                 Agent Selection
                        ↓
                 Cache Optimization
```

## Security Architecture

### 1. API Key Management
- Environment variable isolation
- No hardcoded credentials
- Secure key rotation support

### 2. File System Security
- Permission validation for agent files
- Sandbox execution for untrusted agents
- Path traversal prevention

### 3. Process Isolation
- Subprocess execution for agent tasks
- Resource limits and timeouts
- Error boundary implementation

## Extension Points

### 1. Custom Agent Creation
- Markdown-based agent definitions
- Standardized metadata format
- Automatic registry integration

### 2. Service Extensions
- Plugin architecture for new services
- Dependency injection support
- Event-driven hooks

### 3. CLI Command Extensions
- Command registration API
- Flag and argument parsing
- Output formatting hooks

## Performance Characteristics

### 1. Startup Performance
- Cold start: <500ms
- Warm start: <200ms (with cache)
- Agent discovery: <100ms

### 2. Memory Usage
- Base framework: ~50MB
- Per agent: ~5-10MB
- Cache overhead: ~20MB max

### 3. Scalability
- Concurrent agents: 10 (configurable)
- Task queue depth: Unlimited
- File handle limit: OS-dependent

## Configuration Architecture

### 1. Configuration Hierarchy
```
Framework Defaults
    ↓
User Configuration (~/.claude-pm/config.json)
    ↓
Project Configuration (.claude-pm/config.json)
    ↓
Environment Variables
    ↓
Command-line Arguments
```

### 2. Configuration Categories
- **Framework**: Core behavior settings
- **Agents**: Agent-specific configurations
- **Services**: Service parameters and limits
- **Performance**: Optimization settings

## Deployment Architecture

### 1. Package Structure
- **NPM Package**: Node.js CLI and orchestration
- **Python Package**: Core services and agent execution
- **Templates**: Framework and project templates

### 2. Installation Flow
```
NPM Install → Postinstall Scripts
                    ↓
            Python Validation
                    ↓
            Template Deployment
                    ↓
            Framework Setup
```

## Error Handling Strategy

### 1. Error Boundaries
- CLI-level error catching
- Service-level error isolation
- Agent-level error recovery

### 2. Error Reporting
- Structured error messages
- Context preservation
- Recovery suggestions

### 3. Graceful Degradation
- Fallback to system agents
- Cache bypass on corruption
- Service isolation on failure

## Future Architecture Considerations

### 1. Planned Enhancements
- Distributed agent execution
- Real-time collaboration features
- Cloud-based agent registry

### 2. Scalability Improvements
- Agent pooling and reuse
- Distributed caching
- Async task processing

### 3. Integration Opportunities
- IDE plugins
- CI/CD pipeline integration
- Cloud platform adapters

---

*For implementation details, see the [API Reference](./api-reference.md) and source code documentation.*