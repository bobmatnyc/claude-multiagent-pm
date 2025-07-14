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

### 📋 Take Over Project
Understanding inherited or unfamiliar code:
```bash
cd inherited-project
claude-pm
# AI agents scan and explain codebase patterns
# Get up to speed faster with intelligent analysis
```

## Start Small

Try it on a simple utility first. The AI agents learn your style and get better over time.

**Safety First**: AI only suggests, never applies automatically. Start with:
- Personal utilities or side projects
- Non-mission-critical codebases
- Projects where you can easily review changes

**Requirements**: Node.js 16+, Python 3.8+

For complete documentation: [User Guide](./docs/user-guide/README.md)