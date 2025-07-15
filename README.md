# Claude PM Framework

[![Version](https://img.shields.io/badge/version-0.9.0-blue.svg)](https://www.npmjs.com/package/@bobmatnyc/claude-multiagent-pm)
[![Framework](https://img.shields.io/badge/framework-014--005-green.svg)](./framework/CLAUDE.md)
[![Node.js](https://img.shields.io/badge/node->=16.0.0-green.svg)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python->=3.8.0-green.svg)](https://python.org/)

AI project manager that orchestrates specialized agents for your development workflow.

## Install & Run

```bash
npm install -g @bobmatnyc/claude-multiagent-pm
cd your-project
claude-pm
```

## What It Does

- **🤖 AI Agent Orchestration**: 9 specialized agents handle documentation, testing, deployment, and quality assurance
- **📋 Smart Ticketing**: Integrated ticket management with GitHub Issues sync (Linear, JIRA, Asana coming soon)
- **📝 Intelligent Documentation**: Auto-generates and maintains project documentation
- **🔍 Code Quality**: Automated testing, linting, and security scanning
- **🚀 Safe Deployment**: Validates deployments locally and to production
- **🧠 Memory Integration**: Learns from your patterns and preferences over time

## Three Essential Commands

- **`push`** - Complete development pipeline: documentation, testing, Git operations, and changelog generation
- **`deploy`** - Local deployment with validation and health checks
- **`publish`** - Package publication with validation and registry deployment

## Orchestrated Development Best Practices

### Model Recommendations

**Claude Sonnet**: Recommended for orchestrated development due to superior speed and efficiency. The framework's multi-agent architecture benefits from Sonnet's rapid task delegation and coordination.

**YOLO Mode**: Enable for extended development sessions. Reduces permission bottlenecks and enables fluid multi-agent workflows. Particularly effective for feature development and refactoring sessions.

### Agent-Driven Workflow

**QA Agents**: Automatically catch most coding errors before they reach your codebase. The orchestrated approach means quality validation happens at every step, not just at the end.

**Feature Branch Strategy**: Essential for safe orchestrated development:
```bash
git checkout -b feature/my-feature
claude-pm  # Work with agents in isolated branch
# Agents handle testing, documentation, and validation
push  # Comprehensive quality pipeline before merge
```

**Agent Specialization**: 9 core agent types + 35+ specialized agents focus on their domain expertise:
- **Documentation Agent (`Documenter`)**: Pattern analysis and operational understanding
- **Ticketing Agent (`Ticketer`)**: Universal ticketing with GitHub Issues sync
- **QA Agent (`QA`)**: Testing, linting, and quality validation
- **Version Control Agent (`Versioner`)**: Git operations and branch management
- **Research Agent (`Researcher`)**: Investigation and analysis
- **Ops Agent (`Ops`)**: Deployment and infrastructure
- **Security Agent (`Security`)**: Security analysis and vulnerability assessment
- **Engineer Agent (`Engineer`)**: Code implementation and development
- **Data Engineer Agent (`Data Engineer`)**: Data store and AI API management
- **Plus Specialized Agents**: Architecture, Performance, UI/UX, Integration, and more via AgentRegistry

### Development Speed Benefits

**Traditional Development**: Manual testing → Manual documentation → Manual review → Deploy

**Orchestrated Development**: AI agents handle testing, documentation, and review automatically while you focus on core logic and architecture decisions.

## Common Use Cases

### 🌱 New Project Setup
Starting a fresh project? Get AI-enhanced development from day one:
```bash
npm install -g @bobmatnyc/claude-multiagent-pm
cd my-new-project
claude-pm
# AI agents help establish patterns, testing, and documentation
```

**💡 Orchestrated Development**: Use feature branches with agent coordination:
```bash
git checkout -b feature/auth-system
# Work with specialized agents for each aspect
# QA Agents handle testing, Documentation Agents handle docs
push  # Comprehensive validation pipeline
```

**💡 Recommendation**: Create a design document before major feature development. Example prompt:
> "Help me design a user authentication system with JWT tokens and role-based access control"

### 🔧 Refactor Existing Project
Safely modernize your codebase with AI guidance:
```bash
# Install globally (safe for mono-repos)
npm install -g @bobmatnyc/claude-multiagent-pm
cd existing-project
claude-pm
# AI suggests improvements, never applies automatically
# Your existing scripts remain untouched
```

**💡 Orchestrated Refactoring**: Leverage agent specialization for safe, comprehensive refactoring:
```bash
git checkout -b refactor/typescript-migration
# Documentation Agents analyze current patterns
# QA Agents ensure no regressions during refactoring
# Version Control Agents manage branch strategy
push  # Validate all changes before merge
```

**💡 Recommendation**: Start with a refactoring design document. Simple prompts aren't as ideal, but claude-pm can figure things out, especially if you ask it to research:
> "Refactor file src/auth.js to keep line size under 100 characters" --> research which best practices should be used with code patterns in those files
> "Refactor files in src/components/ to use TypeScript with strict typing" --> research which best practices should be used with code patterns in those files

### 📋 Take Over Project
Understanding inherited or unfamiliar code:
```bash
cd inherited-project
claude-pm
# AI agents scan and explain codebase patterns
# Get up to speed faster with intelligent analysis
```

**💡 Orchestrated Analysis**: Use specialized agents for comprehensive project understanding:
- **Documentation Agent**: Analyze existing patterns and architectural decisions
- **QA Agent**: Identify testing gaps and quality issues
- **Security Agent**: Scan for security vulnerabilities and compliance
- **Ticketing Agent**: Create organized task breakdown and tracking

**💡 Recommendation**: Document your understanding in a project analysis design document first. Example prompt:
> "Analyze the current authentication flow and document any security concerns or improvement opportunities"

### 🏢 Monorepo Best Practices
Managing multiple packages in a single repository:
```bash
cd my-monorepo
claude-pm
# AI agents understand workspace structures and cross-package dependencies
# Provides coordinated development across multiple projects
```

**Key Monorepo Features:**
- **Workspace Detection**: Automatically identifies package.json workspaces, Lerna, Rush, or Nx configurations
- **Cross-Package Dependencies**: Tracks and validates dependencies between internal packages
- **Coordinated Testing**: Runs tests across affected packages when changes are made
- **Shared Configuration**: Manages consistent linting, formatting, and build configs across packages
- **Release Coordination**: Handles version bumping and publishing for multiple packages

**Simple Monorepo Prompts:**
> "Update all packages in workspace to use TypeScript 5.0"
> "Run tests for packages affected by changes in packages/shared"
> "Refactor common utilities from packages/app-a and packages/app-b into packages/shared"
> "Ensure all packages follow the same ESLint configuration"

**💡 Orchestrated Monorepo Management**: Use agent coordination for complex monorepo operations:
```bash
# Feature branch for cross-package changes
git checkout -b feature/shared-utility-extraction
# Documentation Agent analyzes package dependencies
# QA Agent validates cross-package impacts
# Ops Agent coordinates workspace builds
# Ticketing Agent tracks cross-package changes
push  # Comprehensive validation across all packages
```

**💡 Monorepo Recommendation**: Create package-specific design documents to track individual package evolution while maintaining overall architecture coherence.

---

## Custom Agent Development

### Creating Custom Agents

The Claude PM Framework supports custom agents through a three-tier hierarchy system with automatic discovery. Create specialized agents for your specific project needs.

#### Agent Hierarchy and Precedence

**Directory Precedence (Highest to Lowest Priority):**
1. **Project Agents**: `$PROJECT/.claude-pm/agents/project-specific/`
   - Project-specific implementations and overrides
   - Highest precedence for project context

2. **User Agents**: Directory hierarchy with precedence walking
   - **Current Directory**: `$PWD/.claude-pm/agents/user-agents/` (highest user precedence)
   - **Parent Directories**: Walk up tree checking `../user-agents/`, `../../user-agents/`, etc.
   - **User Home**: `~/.claude-pm/agents/user-defined/` (fallback user location)

3. **System Agents**: `claude_pm/agents/`
   - Core framework functionality (9 core agent types)
   - Always available as fallback

#### User-Agents Directory Structure

```
$PWD/.claude-pm/agents/user-agents/
├── specialized/
│   ├── performance-agent.md
│   ├── architecture-agent.md
│   └── integration-agent.md
├── custom/
│   ├── project-manager-agent.md
│   └── business-analyst-agent.md
└── overrides/
    ├── documentation-agent.md  # Override system Documentation Agent
    └── qa-agent.md             # Override system QA Agent
```

### WHEN/WHY/WHAT Requirements for Custom Agents

**MANDATORY: Custom agents must provide clear usage guidelines:**

#### 1. **WHEN to Use the Agent**
```markdown
# Custom Agent: Performance Optimization Specialist

## When to Use This Agent
- Database query optimization tasks
- Application performance bottlenecks
- Memory usage analysis and optimization
- Load testing and stress testing coordination
- Performance monitoring setup
```

#### 2. **WHY the Agent Exists**
```markdown
## Why This Agent Exists
- Specialized knowledge in performance profiling tools
- Deep understanding of database optimization techniques
- Experience with load testing frameworks and analysis
- Focused expertise beyond general QA or Engineering agents
```

#### 3. **WHAT the Agent Does**
```markdown
## Agent Capabilities
- **Primary Role**: Application and database performance optimization
- **Specializations**: ['performance', 'monitoring', 'database', 'optimization']
- **Tools**: Profiling tools, performance monitors, load testing frameworks
- **Authority**: Performance analysis, optimization recommendations, monitoring setup

## Specific Tasks This Agent Handles
1. **Database Optimization**: Query analysis, index optimization, schema tuning
2. **Application Profiling**: Memory analysis, CPU optimization, bottleneck identification
3. **Load Testing**: Stress test design, performance baseline establishment
4. **Monitoring Setup**: Performance dashboard creation, alerting configuration
5. **Optimization Reporting**: Performance analysis reports, improvement recommendations
```

### Custom Agent File Template

```markdown
# [Agent Name] Agent

## Agent Profile
- **Nickname**: [Short name for Task Tool delegation]
- **Type**: [Agent category]
- **Specializations**: [List of specialization tags]
- **Authority**: [What this agent has authority over]

## When to Use
[Specific scenarios where this agent should be selected]

## Why This Agent Exists
[Rationale for specialized functionality beyond core agents]

## Capabilities
[Detailed list of what this agent can do]

## Task Tool Integration
**Standard Delegation Format:**
```
**[Agent Nickname]**: [Task description]

TEMPORAL CONTEXT: Today is [date]. Apply date awareness to [agent-specific considerations].

**Task**: [Specific work items]
1. [Action item 1]
2. [Action item 2]
3. [Action item 3]

**Context**: [Agent-specific context requirements]
**Authority**: [Agent's decision-making scope]
**Expected Results**: [Specific deliverables]
**Integration**: [How results integrate with other agents]
```

## Collaboration Patterns
[How this agent works with other agents]

## Performance Considerations
[Agent-specific performance requirements or optimizations]
```

### Agent Registry Integration

**Dynamic Agent Discovery:**
```python
from claude_pm.core.agent_registry import AgentRegistry

# Initialize registry with directory precedence
registry = AgentRegistry()

# List all available agents with metadata
agents = registry.listAgents()

# Discover agents by specialization
performance_agents = registry.listAgents(specialization='performance')
ui_agents = registry.listAgents(specialization='ui_ux')
architecture_agents = registry.listAgents(specialization='architecture')

# Multi-specialization discovery
multi_spec = registry.listAgents(specializations=['integration', 'performance'])
```

### Custom Agent Best Practices

#### Agent Metadata Requirements
- **Clear Specializations**: Use specific tags for agent discovery
- **Authority Scope**: Define what decisions the agent can make
- **Collaboration Patterns**: Specify how the agent works with others
- **Performance Profile**: Include performance considerations

#### Delegation Format Standards
- Use consistent Task Tool delegation format
- Include temporal context for date awareness
- Provide comprehensive context filtering
- Specify expected results and integration patterns

#### Performance Considerations
- Leverage SharedPromptCache for 99.7% faster loading
- Design for repeated orchestration optimization
- Consider agent modification tracking
- Optimize for cache hit ratios >95%

### Specialized Agent Types Beyond Core 9

**35+ Agent Types Supported:**
- **Core 9**: Documentation, Ticketing, Version Control, QA, Research, Ops, Security, Engineer, Data Engineer
- **Architecture & Design**: Architecture, UI/UX, Design, Strategy
- **Development**: Frontend, Backend, Mobile, API, Integration
- **Operations**: Infrastructure, Deployment, Monitoring, Performance
- **Business**: PM, Product, Marketing, Business, Customer Success
- **Compliance**: Legal, Finance, Security, Compliance
- **Specialized**: Migration, Optimization, Automation, Analytics

### Registry-Enhanced Delegation Patterns

**Dynamic Agent Selection Examples:**
- **"optimize"** → Performance Agent via registry discovery (specialization: ['performance', 'monitoring'])
- **"architect"** → Architecture Agent via registry discovery (specialization: ['architecture', 'design'])
- **"integrate"** → Integration Agent via registry discovery (specialization: ['integration', 'api'])
- **"ui/ux"** → UI/UX Agent via registry discovery (specialization: ['ui_ux', 'design'])
- **"monitor"** → Monitoring Agent via registry discovery (specialization: ['monitoring', 'analytics'])

### Getting Started with Custom Agents

1. **Identify Specialization Gap**: Determine what expertise your project needs beyond core agents
2. **Create Agent Directory**: Set up user-agents directory structure in your project
3. **Write Agent Definition**: Use the template to create comprehensive agent documentation
4. **Test Agent Discovery**: Verify the agent is discovered by AgentRegistry
5. **Integrate with Workflows**: Update your orchestration patterns to leverage the custom agent

**Example Custom Agent Creation:**
```bash
# Create user-agents directory
mkdir -p .claude-pm/agents/user-agents/specialized/

# Create custom performance agent
cat > .claude-pm/agents/user-agents/specialized/performance-agent.md << 'EOF'
# Performance Optimization Agent

## Agent Profile
- **Nickname**: Optimizer
- **Type**: performance
- **Specializations**: ['performance', 'monitoring', 'optimization']
- **Authority**: Performance analysis and optimization recommendations

## When to Use
- Database query optimization needed
- Application performance bottlenecks identified
- Load testing and performance monitoring required

## Why This Agent Exists
- Specialized expertise in performance profiling
- Deep knowledge of optimization techniques
- Focused beyond general QA capabilities

## Capabilities
- Performance analysis and bottleneck identification
- Database query optimization
- Load testing coordination
- Monitoring setup and configuration
EOF

# Test agent discovery
python -c "from claude_pm.core.agent_registry import AgentRegistry; registry = AgentRegistry(); print(registry.listAgents(specialization='performance'))"
```

## Developer Workflow

### Orchestrated vs Traditional Development

**Traditional Approach**: You handle all aspects manually - testing, documentation, deployment, quality checks.

**Orchestrated Approach**: Specialized AI agents handle their domains while you focus on architecture and core logic:

```bash
# Start feature development
git checkout -b feature/user-dashboard

# Work with orchestrated agents
claude-pm
# Documentation Agent: Analyze patterns and requirements
# QA Agent: Set up testing framework and validation
# Ops Agent: Configure deployment pipeline
# Ticketing Agent: Track feature development progress

# Continuous validation throughout development
push  # Multi-agent quality pipeline before commit
```

### Working with Agent Types

**Documentation Agent (`Documenter`)**: 
- Analyze your codebase patterns and architectural decisions
- Generate and maintain technical documentation
- Provide operational insights for better development practices

**Ticketing Agent (`Ticketer`)**:
- Manage tickets using ai-trackdown-tools with GitHub Issues sync
- Create hierarchical Epic → Issue → Task → PR structure
- Track project progress and coordinate development workflow

**QA Agent (`QA`)**: 
- Catch errors before they reach your codebase
- Set up comprehensive testing strategies
- Validate code quality and adherence to best practices

**Version Control Agent (`Versioner`)**: 
- Manage branch strategies and Git operations
- Handle merge conflicts and integration challenges
- Coordinate feature branch workflows

**Engineer Agent (`Engineer`)**:
- Write, modify, and implement code changes
- Create inline documentation and code comments
- Implement feature requirements and bug fixes

**Ops Agent (`Ops`)**: 
- Manage local and production deployments
- Configure CI/CD pipelines and infrastructure
- Handle environment setup and dependency management

### Recommended Workflow

1. **Start with Design**: Create design documents for complex features
2. **Feature Branches**: Always work in isolated feature branches
3. **Agent Coordination**: Let specialized agents handle their domains
4. **Continuous Validation**: Use `push` command for comprehensive quality checks
5. **YOLO Mode**: Enable for extended development sessions without interruptions

## Start Small

Try it on a simple utility first. The AI agents learn your style and get better over time.

**Safety First**: AI only suggests, never applies automatically. Start with:
- Personal utilities or side projects
- Non-mission-critical codebases
- Projects where you can easily review changes

**Requirements**: Node.js 16+, Python 3.8+

**📚 Complete Documentation**: [Quick Start Guide](./docs/QUICKSTART.md) | [Framework Guide](./framework/CLAUDE.md) | [Custom Agents](./docs/old/user-guide/README.md)