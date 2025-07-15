# Claude PM Framework

[![Version](https://img.shields.io/badge/version-0.6.1-blue.svg)](https://www.npmjs.com/package/@bobmatnyc/claude-multiagent-pm)
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

- **Code Review**: AI agents review changes before commits
- **Testing**: Automated testing and quality checks
- **Documentation**: Scans and explains your codebase
- **Deployment**: Safe local and package deployment
- **Orchestration**: Coordinates specialized agents for workflow efficiency

## Three Commands

- **`push`** - Test, review, and commit changes
- **`deploy`** - Deploy locally with validation  
- **`publish`** - Publish to NPM/PyPI

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

**Agent Specialization**: Each agent type focuses on their domain expertise:
- **Documentation Agents**: Pattern analysis and operational understanding
- **QA Agents**: Testing, linting, and quality validation
- **Version Control Agents**: Git operations and branch management
- **DevOps Agents**: Deployment and infrastructure

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

**💡 Recommendation**: Create a [design document](./docs/design/) before major feature development. Example prompt:
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

**💡 Recommendation**: Start with a [refactoring design doc](./docs/design/refactoring-design-doc-template.md). Simple prompts aren't as ideal, but claude-pm can figure things out, especially if you ask it to research:
> "Refactor file src/auth.js to keep line size under 100 characters" --> research which best practices should be used with code patterns in those files
> "Refactor files in src/components/ to use TypeScript with strict typing" --> research which best practices should be used with code patterns in those files

See our [TypeScript refactoring example](./docs/design/typescript-refactoring-example.md) for detailed guidance.

### 📋 Take Over Project
Understanding inherited or unfamiliar code:
```bash
cd inherited-project
claude-pm
# AI agents scan and explain codebase patterns
# Get up to speed faster with intelligent analysis
```

**💡 Orchestrated Analysis**: Use specialized agents for comprehensive project understanding:
- **Documentation Agents**: Analyze existing patterns and architectural decisions
- **QA Agents**: Identify testing gaps and quality issues
- **Security Agents**: Scan for security vulnerabilities and compliance

**💡 Recommendation**: Document your understanding in a [project analysis design doc](./docs/design/) first. Example prompt:
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
# Documentation Agents analyze package dependencies
# QA Agents validate cross-package impacts
# DevOps Agents coordinate workspace builds
push  # Comprehensive validation across all packages
```

**💡 Monorepo Recommendation**: Create package-specific design docs in `docs/packages/[package-name]/` to track individual package evolution while maintaining overall architecture coherence.

## Developer Workflow

### Orchestrated vs Traditional Development

**Traditional Approach**: You handle all aspects manually - testing, documentation, deployment, quality checks.

**Orchestrated Approach**: Specialized AI agents handle their domains while you focus on architecture and core logic:

```bash
# Start feature development
git checkout -b feature/user-dashboard

# Work with orchestrated agents
claude-pm
# Documentation Agents: Analyze patterns and requirements
# QA Agents: Set up testing framework and validation
# DevOps Agents: Configure deployment pipeline

# Continuous validation throughout development
push  # Multi-agent quality pipeline before commit
```

### Working with Agent Types

**Documentation Agents**: 
- Analyze your codebase patterns and architectural decisions
- Generate and maintain technical documentation
- Provide operational insights for better development practices

**QA Agents**: 
- Catch errors before they reach your codebase
- Set up comprehensive testing strategies
- Validate code quality and adherence to best practices

**Version Control Agents**: 
- Manage branch strategies and Git operations
- Handle merge conflicts and integration challenges
- Coordinate feature branch workflows

**DevOps Agents**: 
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

**📚 Complete Documentation**: [Quick Start Guide](./docs/QUICKSTART.md)