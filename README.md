# Claude PM Framework

[![Version](https://img.shields.io/badge/version-1.4.4-blue.svg)](https://www.npmjs.com/package/@bobmatnyc/claude-multiagent-pm)
[![Framework](https://img.shields.io/badge/framework-014--005-green.svg)](./framework/CLAUDE.md)
[![Node.js](https://img.shields.io/badge/node->=16.0.0-green.svg)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python->=3.8.0-green.svg)](https://python.org/)

A lightweight, flexible multi-agent framework for orchestrating AI-driven development workflows with unlimited custom agent creation.

Claude PM brings the power of AI orchestration to your development workflow through a simple CLAUDE.md configuration file. By defining your project's goals and constraints in natural language, you enable specialized AI agent teams to collaborate on your codebase - with a PM orchestrator intelligently delegating tasks to Documentation, QA, Engineering, Security, and other specialized agents (including your own custom agents). This framework makes it remarkably easy to leverage AI assistance while maintaining full control over your development process.

## Framework Positioning

### Claude PM Framework vs claude-flow:

| Aspect | Claude PM Framework | claude-flow |
|--------|-------------------|-------------|
| **Focus** | Individual developers & small teams | Large enterprises |
| **Agent System** | **Unlimited custom agents** + 9 core agents | Fixed enterprise agent set |
| **Setup** | Lightweight, immediate start | Heavy enterprise configuration |
| **Customization** | **User-generated agents**, self-improving | Static templates, manual updates |
| **Best For** | Rapid development, creative workflows | Enterprise governance, compliance |

### Choose Claude PM Framework when:
- You want to **create your own custom agents** for specific tasks
- Need **lightweight setup** without enterprise overhead
- Want agents that **learn and improve** from usage patterns
- Building creative, adaptive workflows with **user-driven customization**

## Installation

### Quick Install

Choose your preferred package manager:

#### npm (Recommended for most users)
```bash
npm install -g @bobmatnyc/claude-multiagent-pm
claude-pm --version
```

#### pip (Python Package Index)
```bash
pip install claude-multiagent-pm
claude-pm --version
```

#### pipx (Recommended for macOS)
```bash
pipx install claude-multiagent-pm
claude-pm --version
```

### Platform-Specific Installation

#### 🍎 macOS
macOS users often encounter "externally-managed-environment" errors with Homebrew Python. We recommend using **pipx**:

```bash
# Install pipx if you don't have it
brew install pipx
pipx ensurepath

# Install Claude PM Framework
pipx install claude-multiagent-pm
```

**Alternative for macOS**: Use npm installation (avoids Python environment issues)
```bash
npm install -g @bobmatnyc/claude-multiagent-pm
```

#### 🐧 Linux
```bash
# Using pip with user flag
pip install --user claude-multiagent-pm

# Or using pipx (recommended)
pipx install claude-multiagent-pm

# Or using npm
npm install -g @bobmatnyc/claude-multiagent-pm
```

#### 🪟 Windows
```bash
# Using pip
pip install claude-multiagent-pm

# Or using npm (requires Node.js)
npm install -g @bobmatnyc/claude-multiagent-pm
```

### Verify Installation

After installation, verify everything is working:

```bash
# Check CLI is available
claude-pm --version

# Initialize in your project
cd your-project
claude-pm init

# Start using the framework
claude-pm
```

### Troubleshooting Installation

#### "command not found" after installation
- **npm**: Make sure npm's global bin directory is in your PATH
  ```bash
  echo 'export PATH="$PATH:$(npm prefix -g)/bin"' >> ~/.bashrc
  source ~/.bashrc
  ```
- **pip**: Make sure Python's user bin directory is in your PATH
  ```bash
  echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
  source ~/.bashrc
  ```
- **pipx**: Run `pipx ensurepath` and restart your terminal

#### Python environment errors on macOS
- Use pipx instead of pip (recommended)
- Or use npm installation to avoid Python entirely
- See our [macOS Installation Guide](./docs/MACOS_INSTALLATION_GUIDE.md) for detailed solutions

#### Module import errors
- Ensure you're using Python 3.8 or higher: `python --version`
- Try reinstalling: `pip install --force-reinstall claude-multiagent-pm`
- Check for conflicting installations: `pip show claude-multiagent-pm`

#### npm postinstall errors
- Ensure Node.js 16+ is installed: `node --version`
- Clear npm cache: `npm cache clean --force`
- Try installing without scripts: `npm install -g @bobmatnyc/claude-multiagent-pm --ignore-scripts`

### Development Installation

For contributors who want to work on the framework itself:

```bash
# Clone the repository
git clone https://github.com/bobmatnyc/claude-multiagent-pm.git
cd claude-multiagent-pm

# Install in development mode
pip install -e .

# Or use npm link
npm link
```

> **⚠️ Important**: Development installations are for framework contributors only. For using the framework in your projects, use the standard installation methods above.

## 📖 Getting Started

**New to Claude PM Framework?** Start with our comprehensive user guide:

**👉 [Complete User Guide](./docs/user-guide.md)** - Your essential starting point for understanding and using the framework effectively.

The user guide covers everything from basic concepts to advanced workflows, including practical examples and best practices for orchestrating AI-driven development workflows.

## Key Features (v1.4.4)

- **💾 Memory Safety Protection**: Real-time subprocess memory monitoring prevents system crashes from runaway processes
- **🎯 Custom Agent Creation**: Create project-specific agents tailored to your domain - architecture, performance, UI/UX, compliance, and more
- **🤖 Agent Registry & Hierarchical Discovery**: Dynamic agent discovery with project → user → system precedence
- **⚡ Performance Optimization**: 99.7% improvement through SharedPromptCache integration
- **💰 Prompt Optimization**: 50-66% token reduction through intelligent task analysis and dynamic model selection
- **🧠 Agent Training System**: Self-improving agents that learn from experience
- **📋 Unified Ticketing System**: Seamless integration with ai-trackdown-pytools for GitHub Issues management
- **🏗️ Two-Tier Agent Architecture**: Simplified architecture with extensible custom agent support
- **🔄 Real-Time Agent Modification Tracking**: Monitors agent changes and adapts workflows
- **📝 Comprehensive Documentation**: Auto-generated changelogs, semantic versioning, and project documentation
- **🔍 Quality Assurance**: Automated testing, linting, and security scanning across agent workflows
- **🚀 Deployment Coordination**: Multi-agent deployment validation and management

## 🔧 Orchestration Model - Our Own Built-in Process Manager

**IMPORTANT**: The Claude PM Framework uses its own custom-built process management system for agent orchestration. This is NOT Claude's Task Tool subprocess system - this is our framework's innovation.

### How It Works

The PM (Project Manager) agent orchestrates all work by delegating to specialized agents through **our own built-in process manager**:

1. **Process Creation**: PM analyzes tasks and creates agent processes using our process manager
2. **Isolated Execution**: Each agent runs in its own controlled process environment
3. **Context Filtering**: Agents receive only the context relevant to their specialization
4. **Result Integration**: PM collects and integrates results from multiple agents
5. **Workflow Coordination**: Complex multi-agent workflows are managed by our orchestration engine

### Enhanced Agent Selection (v1.0.2)

**NEW**: Natural language task descriptions are now automatically mapped to the right agent with 94.1% accuracy:

- **Natural Language Support**: Simply describe what you need - the framework finds the right agent
- **@agent_name Syntax**: Explicitly specify an agent using @agent_name (e.g., "@researcher find Next.js docs")
- **Smart Keyword Matching**: Semantic parsing identifies agent types from task descriptions
- **0.34ms Performance**: Lightning-fast agent selection with minimal overhead

Examples:
```bash
# Natural language automatically selects the right agent
"Research the latest Next.js features" → Research Agent
"Update the API documentation" → Documentation Agent  
"Check test coverage" → QA Agent
"Deploy to staging" → Ops Agent

# Explicit agent selection with @
"@engineer implement user authentication"
"@security scan for vulnerabilities"
```

### Benefits of Our Process Manager

- **Concurrent Execution**: Run up to 10 specialized agents simultaneously
- **Process Isolation**: Secure execution environment for each agent
- **Error Recovery**: Robust handling of agent failures and timeouts
- **Performance Tracking**: Built-in metrics and optimization
- **Easy Extension**: Simple to add custom agents that integrate seamlessly
- **Smart Routing**: Intelligent agent selection from natural language descriptions

This custom process management system is a core differentiator of the Claude PM Framework, purpose-built for AI agent coordination.

## 🧠 Agent Training & Continuous Learning

One of Claude PM Framework's most powerful features is its **built-in agent training system** that enables continuous improvement:

### Self-Improving Agents
- **Automatic Pattern Learning**: Agents learn from successful task completions
- **Error Correction Capture**: Failed attempts become learning opportunities
- **Performance Optimization**: Agents optimize their approaches based on metrics
- **Knowledge Accumulation**: Each agent builds domain-specific expertise over time

### Training Features
- **Continuous Learning Engine**: Agents improve with every interaction
- **Pattern Analysis**: Automatic detection of successful patterns
- **Cross-Agent Learning**: Agents share learnings within their specialization
- **User Feedback Integration**: Direct corrections improve agent behavior
- **Performance Metrics**: Track agent improvement over time

### How It Works
1. **Task Execution**: Agents perform their specialized tasks
2. **Outcome Analysis**: Success/failure patterns are captured
3. **Learning Integration**: Patterns update agent knowledge base
4. **Continuous Improvement**: Next execution benefits from learnings

This means your custom agents get **smarter and more efficient** the more you use them, without manual intervention.

## 💰 Prompt Optimization & Token Reduction

The Claude PM Framework includes intelligent prompt optimization that automatically reduces token usage by 50-66% while maintaining or improving task execution quality:

### Three-Phase Optimization
1. **Task Complexity Analysis**: Analyzes task requirements to determine complexity level
2. **Dynamic Model Selection**: Automatically selects the optimal Claude model (Haiku/Sonnet/Opus)
3. **Adaptive Prompt Templates**: Adjusts agent instructions based on task needs

### Key Benefits
- **50-66% Token Reduction**: Significant cost savings on API usage
- **Faster Response Times**: Smaller prompts process more quickly
- **Smart Model Selection**: Right model for the right task
- **Enabled by Default**: No configuration needed - works automatically

### Configuration
```bash
# Prompt optimization is enabled by default
# To disable (not recommended):
export ENABLE_DYNAMIC_MODEL_SELECTION=false

# The framework automatically optimizes all agent interactions
```

### How It Works
- **Simple Tasks** (e.g., "List files") → Haiku model + minimal instructions
- **Medium Tasks** (e.g., "Fix bug") → Sonnet model + standard instructions  
- **Complex Tasks** (e.g., "Refactor system") → Opus model + comprehensive context

See [Prompt Optimization Guide](./docs/guides/prompt-optimization-guide.md) for detailed configuration and best practices.

## Three Essential Commands

- **`push`** - Complete development pipeline: documentation, testing, Git operations, and changelog generation
- **`deploy`** - Local deployment with validation and health checks
- **`publish`** - Package publication with validation and registry deployment

## 📋 Ticketing System Integration

The Claude PM Framework now includes seamless integration with **ai-trackdown-pytools** for comprehensive project management:

### Features
- **GitHub Issues Integration**: Direct synchronization with GitHub Issues
- **Hierarchical Structure**: Epic → Issue → Task → PR organization
- **AI-Powered Management**: Intelligent ticket creation and tracking
- **Unified Experience**: Access ticketing features directly from claude-pm

### Usage
```bash
# The ticketing system is automatically available
# Use ai-trackdown commands within your project workflow
ai-trackdown --help
```

For detailed ticketing documentation, see the [ai-trackdown-pytools documentation](https://github.com/ai-track-down/ai-trackdown-pytools).

## Development Best Practices

### Model Recommendations

**Claude Sonnet**: Recommended for multi-agent orchestration due to fast response times and efficient task delegation capabilities. The framework's architecture is optimized for Sonnet's coordination patterns.

**YOLO Mode**: Reduces approval prompts during extended development sessions. Enables continuous multi-agent workflows for feature development and refactoring tasks.

### Agent-Driven Workflow

**QA Agents**: Provide automated testing, linting, and quality validation throughout the development process. Integrated validation occurs at multiple workflow points rather than only at project completion.

**Feature Branch Strategy**: Recommended approach for team development:
```bash
git checkout -b feature/my-feature
claude-pm  # Work with agents in isolated branch
# Agents coordinate testing, documentation, and validation
push  # Multi-agent quality pipeline before merge
```

**Agent Specialization**: 8 core agent types + custom agent creation enables domain-specific expertise:
- **Documentation Agent (`Documenter`)**: Pattern analysis and operational understanding
- **QA Agent (`QA`)**: Testing, linting, and quality validation
- **Version Control Agent (`Versioner`)**: Git operations and branch management
- **Research Agent (`Researcher`)**: Investigation and analysis
- **Ops Agent (`Ops`)**: Deployment and infrastructure
- **Security Agent (`Security`)**: Security analysis and vulnerability assessment
- **Engineer Agent (`Engineer`)**: Code implementation and development
- **Data Engineer Agent (`Data Engineer`)**: Data store and AI API management
- **Plus Custom Agents**: Create specialized agents for Architecture, Performance, UI/UX, Integration, and more via AgentRegistry

### Development Workflow Comparison

**Traditional Development**: Manual testing → Manual documentation → Manual review → Deploy

**Orchestrated Development**: Your custom agents handle testing, documentation, and review processes while you focus on creative problem-solving and core logic. Enables rapid prototyping and agile development with minimal setup overhead.

## Notable Features by Version

### Version History (Most Recent First)

#### v1.4.4 (Current) - July 2025
- **Unified Ticketing System**: Complete integration with ai-trackdown-pytools
- **Multi-Platform Support**: Full support for npm, pip, and pipx installation methods
- **Enhanced Documentation**: Comprehensive installation guides for all platforms
- **Improved Reliability**: Better error handling and dependency management

#### v1.3.0 - July 2025
- **Memory Safety Protection**: Real-time subprocess memory monitoring system
- **Automatic Resource Protection**: Prevents crashes from runaway processes (8GB+ prevention)
- **Configurable Thresholds**: Warning (1GB), Critical (2GB), Hard Limit (4GB) with env overrides
- **Comprehensive Logging**: Detailed memory statistics and alerts for debugging
- **Pre-flight Checks**: Verifies sufficient memory before subprocess creation

#### v1.2.3 - July 2025
- **Maintenance Release**: Documentation updates and test reorganization
- **Base Agent Updates**: Added ticket update requirements for consistency
- **Test Coverage**: Added BaseAgentManager unit tests
- **File Path Fix**: Corrected base_agent_loader.py to use framework path

#### v1.2.2 - July 2025
- **Python Package Publishing**: Full PyPI distribution support
- **Dependency Management**: Enhanced Python dependency handling and installation
- **Agent Discovery Optimization**: Improved agent loading performance
- **Documentation Reorganization**: Cleaner docs structure with better navigation

#### v1.2.1 - July 2025
- **Critical Fix**: Resolved npm postinstall Python dependency issues
- **Auto-Recovery**: Added automatic dependency installation scripts
- **Troubleshooting**: Comprehensive issue resolution documentation

#### v1.2.0 - July 2025
- **Base Agent Instructions**: Shared capabilities system for all agents
- **BaseAgentManager API**: Structured updates to agent behaviors
- **PM Orchestrator Agent**: Enhanced multi-agent coordination role
- **Agent Versioning**: Track and manage agent changes over time
- **Test Suite Reorganization**: Better test categorization

#### v1.0.1 - July 2025
- **Production Fixes**: Resolved agent discovery issues
- **Deployment Improvements**: Better external project support

#### v1.0.0 - July 2025
- **LOCAL Orchestration**: Default mode for instant agent responses
- **Subprocess Environment**: Robust agent delegation handling
- **Performance Optimizations**: Major architectural improvements
- **Framework Stability**: Production-ready release

#### v0.9.3 - July 2025
- **Agent Type Expansion**: Support for 35+ specialized agent types
- **Natural Language Selection**: AI-powered agent matching from descriptions
- **Performance Metrics**: 0.34ms agent selection speed

#### v0.9.2 - July 2025
- **Enhanced Agent Discovery**: Improved registry performance
- **Documentation Updates**: Comprehensive user guides

#### v0.9.1 - July 2025
- **Import Resolution**: Fixed agent system functionality
- **Interface Extraction**: Better model selection features
- **User Guide**: Complete documentation overhaul

#### v0.9.0 - July 2025
- **Agent Registry System**: Revolutionary discovery with two-tier hierarchy
- **99.7% Performance**: SharedPromptCache integration breakthrough
- **Real-time Tracking**: Agent modification monitoring
- **Streamlined Architecture**: Simplified hierarchy for maintainability

#### v0.8.5 - July 2025
- **Enhanced Testing**: Improved test coverage and reliability

#### v0.8.4 - July 2025
- **NPM Publishing**: Resolved package publication issues

#### v0.8.3 - July 2025
- **Subprocess Validation**: Protocol implementation for reliability
- **Installer Fixes**: Fresh installation support improvements

#### v0.8.2 - July 2025
- **Cleanup System**: Comprehensive file management
- **NPM Reliability**: Installation process improvements

#### v0.8.1 - July 2025
- **Dependency Fixes**: Resolved npm package issues

#### v0.8.0 - July 2025
- **Agent Restructuring**: Complete system architecture overhaul
- **Memory Expansion**: Enhanced memory system capabilities
- **Framework Foundation**: Core multi-agent capabilities established

## Quick Start

After installation (see [Installation](#installation) section above), get started:

```bash
# Navigate to your project
cd your-project

# Initialize Claude PM Framework
claude-pm init

# Start orchestrating with AI agents
claude-pm
```

## Common Use Cases

### 🌱 New Project Setup
Establish framework-based development patterns from project start:
```bash
npm install -g @bobmatnyc/claude-multiagent-pm
cd my-new-project
claude-pm
# Agents assist with establishing patterns, testing setup, and documentation structure
```

**💡 Orchestrated Development**: Feature branch workflow with agent coordination:
```bash
git checkout -b feature/auth-system
# Coordinate with specialized agents for different development aspects
# QA Agents manage testing, Documentation Agents handle documentation
push  # Multi-agent validation pipeline
```

**💡 Recommendation**: Create design documents before major feature development. Example prompt:
> "Help me design a user authentication system with JWT tokens and role-based access control"

### 🔧 Refactor Existing Project
Apply framework-guided modernization to existing codebases:
```bash
# Install globally (compatible with monorepos)
npm install -g @bobmatnyc/claude-multiagent-pm
cd existing-project
claude-pm
# Agents suggest improvements without automatic application
# Existing scripts and workflows remain unchanged
```

**💡 Orchestrated Refactoring**: Coordinate agent specialization for systematic refactoring:
```bash
git checkout -b refactor/typescript-migration
# Documentation Agents analyze current patterns
# QA Agents validate against regressions during refactoring
# Version Control Agents coordinate branch strategy
push  # Validate all changes before merge
```

**💡 Recommendation**: Start with a refactoring design document. Simple prompts aren't as ideal, but claude-pm can figure things out, especially if you ask it to research:
> "Refactor file src/auth.js to keep line size under 100 characters" --> research which best practices should be used with code patterns in those files
> "Refactor files in src/components/ to use TypeScript with strict typing" --> research which best practices should be used with code patterns in those files

### 📋 Take Over Project
Understand inherited or unfamiliar codebases through systematic analysis:
```bash
cd inherited-project
claude-pm
# Agents scan and analyze codebase patterns
# Accelerated project understanding through coordinated analysis
```

**💡 Orchestrated Analysis**: Coordinate specialized agents for comprehensive project understanding:
- **Documentation Agent**: Analyze existing patterns and architectural decisions
- **QA Agent**: Identify testing gaps and quality issues
- **Security Agent**: Scan for security vulnerabilities and compliance concerns
- **Ticketing Integration**: Use ai-trackdown for organized task breakdown and tracking

**💡 Recommendation**: Document findings in a project analysis design document. Example prompt:
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
# Use ai-trackdown to track cross-package changes
push  # Comprehensive validation across all packages
```

**💡 Monorepo Recommendation**: Create package-specific design documents to track individual package evolution while maintaining overall architecture coherence.

---

## Custom Agent Creation (v1.0.0)

### Extend the Framework with Your Own Agents

The Claude PM Framework is fully extensible through custom agent creation. Instead of providing a fixed set of agents, the framework enables you to create project-specific agents tailored to your domain, technology stack, and workflow needs.

**Why Create Custom Agents?**
- **Domain Expertise**: Build agents that understand your specific industry, technology stack, or business processes
- **Project Specialization**: Create agents for unique project requirements (e.g., compliance, architecture patterns, deployment workflows)
- **Team Workflows**: Develop agents that match your team's specific development practices and standards
- **Technology Integration**: Build agents that integrate with your specific tools, APIs, and infrastructure
- **Override Defaults**: Customize core agent behavior for your project's specific needs

**How It Works:**
Build specialized agents through a two-tier hierarchy system with dynamic discovery via AgentRegistry and real-time modification tracking. Your custom agents automatically integrate with the framework's orchestration system.

The framework includes a sophisticated **Agent Training System** that enables:
- Continuous learning from task outcomes
- Pattern recognition and optimization
- Performance improvement over time
- Knowledge sharing between similar agents

#### Agent Hierarchy and Precedence (Simplified Two-Tier)

**Directory Precedence (Highest to Lowest Priority):**
1. **User Agents**: Directory hierarchy with precedence walking
   - **Current Directory**: `$PWD/.claude-pm/agents/` (highest precedence)
   - **Parent Directories**: Walk up tree checking `../.claude-pm/agents/`, `../../.claude-pm/agents/`, etc.
   - **User Home**: `~/.claude-pm/agents/` (fallback user location)

2. **System Agents**: `claude_pm/agents/`
   - Core framework functionality (8 core agent types)
   - Always available as fallback

#### User-Agents Directory Structure (v1.0.0)

```
$PWD/.claude-pm/agents/
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

### Agent Registry Integration (v1.0.0)

**Dynamic Agent Discovery with 99.7% Performance Improvement:**
```python
from claude_pm.core.agent_registry import AgentRegistry

# Initialize registry with SharedPromptCache integration
registry = AgentRegistry()

# List all available agents with metadata (cached for performance)
agents = registry.listAgents()

# Discover agents by specialization (optimized lookup)
performance_agents = registry.listAgents(specialization='performance')
ui_agents = registry.listAgents(specialization='ui_ux')
architecture_agents = registry.listAgents(specialization='architecture')

# Multi-specialization discovery with cache optimization
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

#### Performance Considerations (v1.0.0)
- **SharedPromptCache Integration**: 99.7% faster agent loading through intelligent caching
- **Real-Time Modification Tracking**: Monitor agent changes and adapt workflows automatically
- **Optimized Discovery**: <100ms agent discovery for typical projects
- **Cache Efficiency**: Target >95% cache hit ratios for repeated operations

### Custom Agent Types You Can Create

**Extensible Agent System:**
- **Core 8**: Documentation, Version Control, QA, Research, Ops, Security, Engineer, Data Engineer
- **Architecture & Design**: Create agents for Architecture, UI/UX, Design, Strategy
- **Development**: Build agents for Frontend, Backend, Mobile, API, Integration
- **Operations**: Define agents for Infrastructure, Deployment, Monitoring, Performance
- **Business**: Develop agents for PM, Product, Marketing, Business, Customer Success
- **Compliance**: Create agents for Legal, Finance, Security, Compliance
- **Specialized**: Build agents for Migration, Optimization, Automation, Analytics

### Registry-Enhanced Delegation Patterns

**Dynamic Agent Selection Examples:**
- **"optimize"** → Performance Agent via registry discovery (specialization: ['performance', 'monitoring'])
- **"architect"** → Architecture Agent via registry discovery (specialization: ['architecture', 'design'])
- **"integrate"** → Integration Agent via registry discovery (specialization: ['integration', 'api'])
- **"ui/ux"** → UI/UX Agent via registry discovery (specialization: ['ui_ux', 'design'])
- **"monitor"** → Monitoring Agent via registry discovery (specialization: ['monitoring', 'analytics'])

### Quick Start: Creating Your First Custom Agent

**5-Minute Setup:**
```bash
# 1. Create agent directory in your project
mkdir -p .claude-pm/agents/specialized/

# 2. Create a custom agent (example: API Testing Agent)
cat > .claude-pm/agents/specialized/api-testing-agent.md << 'EOF'
# API Testing Agent

## Agent Profile
- **Nickname**: APITester
- **Type**: testing
- **Specializations**: ['api', 'testing', 'integration']
- **Authority**: API testing strategies and validation

## When to Use
- API endpoint testing and validation needed
- Integration testing between services
- API documentation and contract testing

## Why This Agent Exists
- Specialized knowledge of API testing frameworks
- Understanding of REST/GraphQL testing patterns
- Focused expertise beyond general QA testing

## Capabilities
- API endpoint testing with multiple frameworks
- Contract testing and schema validation
- Load testing for API performance
- API documentation generation and validation
EOF

# 3. Test agent discovery
python -c "from claude_pm.core.agent_registry import AgentRegistry; registry = AgentRegistry(); print('Custom agent discovered:', 'api-testing-agent' in str(registry.listAgents()))"
```

**Usage in Workflows:**
```bash
claude-pm
# Your custom APITester agent is now available for delegation
# Task Tool can automatically discover and use it for API-related tasks
```

### Complete Setup Guide

1. **Identify Specialization Gap**: Determine what expertise your project needs beyond core agents
2. **Create Agent Directory**: Set up user-agents directory structure in your project
3. **Write Agent Definition**: Use the template to create comprehensive agent documentation
4. **Test Agent Discovery**: Verify the agent is discovered by AgentRegistry
5. **Integrate with Workflows**: Update your orchestration patterns to leverage the custom agent

### Custom Agent Benefits Summary

**Extensibility Over Fixed Sets**: Rather than providing a predetermined list of agents, the Claude PM Framework empowers you to build exactly what your project needs. Whether you're working with specific cloud platforms, compliance requirements, architectural patterns, or unique deployment workflows, you can create agents that understand your context and provide specialized expertise.

**Seamless Integration**: Custom agents automatically integrate with the framework's orchestration system, AgentRegistry discovery, and Task Tool delegation patterns. Your custom agents work alongside the 9 core agents to provide comprehensive project coverage.

**Performance Optimized**: Custom agents benefit from the same 99.7% performance improvements through SharedPromptCache integration and real-time modification tracking that core agents enjoy.

---

## Developer Workflow

### Orchestrated vs Traditional Development

**Traditional Approach**: Manual handling of testing, documentation, deployment, and quality checks.

**Orchestrated Approach**: Specialized agents coordinate their respective domains while developers focus on architecture and core logic:

```bash
# Start feature development
git checkout -b feature/user-dashboard

# Work with orchestrated agents
claude-pm
# Documentation Agent: Analyze patterns and requirements
# QA Agent: Set up testing framework and validation
# Ops Agent: Configure deployment pipeline
# Use ai-trackdown to track feature development progress

# Continuous validation throughout development
push  # Multi-agent quality pipeline before commit
```

### Working with Agent Types

**Documentation Agent (`Documenter`)**: 
- Analyze your codebase patterns and architectural decisions
- Generate and maintain technical documentation
- Provide operational insights for better development practices

**Ticketing Integration**:
- Unified ticketing through ai-trackdown-pytools
- Direct GitHub Issues management from the framework
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

## Getting Started

Begin with smaller projects to understand the framework's coordination patterns before applying to larger codebases.

**Safety Approach**: Agents provide recommendations and coordinate workflows without automatic code application. Recommended starting points:
- Personal utilities or side projects
- Non-critical development environments
- Projects where changes can be easily reviewed and validated

**Technical Requirements**: Node.js 16+, Python 3.8+

**📚 Documentation**: [**User Guide**](./docs/user-guide.md) | [Quick Start Guide](./docs/QUICKSTART.md) | [Framework Guide](./framework/CLAUDE.md) | [Custom Agents](./docs/old/user-guide/README.md)

## 🛠️ Developer Documentation

**For contributors and developers working on the framework:**

**📖 [Developer Documentation](./docs/developer/README.md)** - Comprehensive guide for framework development

### Developer Guides:
- [**Architecture Guide**](./docs/developer/architecture.md) - System design and component interaction
- [**Development Setup**](./docs/developer/setup.md) - Environment configuration and toolchain
- [**Contributing Guide**](./docs/developer/contributing.md) - How to contribute code and documentation
- [**API Reference**](./docs/developer/api-reference.md) - Complete API documentation
- [**Agent Development**](./docs/developer/agent-development.md) - Creating custom agents
- [**Testing Guide**](./docs/developer/testing.md) - Test strategies and best practices
- [**Performance Guide**](./docs/developer/performance.md) - Optimization techniques
- [**Security Guide**](./docs/developer/security.md) - Security best practices
- [**Deployment Guide**](./docs/developer/deployment.md) - Deployment strategies
- [**Debugging Guide**](./docs/developer/debugging.md) - Troubleshooting techniques