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
- **Memory**: Learns your project patterns over time

## Three Commands

- **`push`** - Test, review, and commit changes
- **`deploy`** - Deploy locally with validation  
- **`publish`** - Publish to NPM/PyPI

## Common Use Cases

### 🌱 New Project Setup
Starting a fresh project? Get AI-enhanced development from day one:
```bash
npm install -g @bobmatnyc/claude-multiagent-pm
cd my-new-project
claude-pm
# AI agents help establish patterns, testing, and documentation
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

**💡 Recommendation**: Start with a [refactoring design doc](./docs/design/refactoring-design-doc-template.md). Simple prompts work great:
> "Refactor file src/auth.js to keep line size under 100 characters"
> "Refactor files in src/components/ to use TypeScript with strict typing"

See our [TypeScript refactoring example](./docs/design/typescript-refactoring-example.md) for detailed guidance.

### 📋 Take Over Project
Understanding inherited or unfamiliar code:
```bash
cd inherited-project
claude-pm
# AI agents scan and explain codebase patterns
# Get up to speed faster with intelligent analysis
```

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

**💡 Monorepo Recommendation**: Create package-specific design docs in `docs/packages/[package-name]/` to track individual package evolution while maintaining overall architecture coherence.

## Start Small

Try it on a simple utility first. The AI agents learn your style and get better over time.

**Safety First**: AI only suggests, never applies automatically. Start with:
- Personal utilities or side projects
- Non-mission-critical codebases
- Projects where you can easily review changes

**Requirements**: Node.js 16+, Python 3.8+

For complete documentation: [User Guide](./docs/user-guide/README.md)