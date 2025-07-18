# Developer Documentation

[← Back to Documentation Home](../README.md) | [Documentation Index](../index.md)

[![Version](https://img.shields.io/badge/version-0.7.0-blue.svg)](https://www.npmjs.com/package/@bobmatnyc/claude-multiagent-pm)
[![Framework](https://img.shields.io/badge/framework-014-green.svg)](../../framework/CLAUDE.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../../LICENSE)

> Comprehensive developer documentation for contributing to and extending the Claude PM Framework

## 📚 Documentation Overview

This section contains detailed technical documentation for developers working with the Claude PM Framework - whether you're contributing to the core, building extensions, or integrating with other systems.

## 📖 Documentation Structure

### [API Documentation](./api/README.md)
Complete API reference for all framework components.

- **[Core API](./api/core.md)** - Core system APIs and interfaces
- **[Agent API](./api/agents.md)** - Agent development and interaction APIs
- **[Services API](./api/services.md)** - Service layer documentation
- **[Utilities API](./api/utilities.md)** - Helper functions and utilities
- **[Events API](./api/events.md)** - Event system and messaging

### [Extension Development](./extensions/README.md)
Guides for extending the framework with custom functionality.

- **[Creating Custom Agents](./extensions/custom-agents.md)** - Build your own specialized agents
- **[Plugin Development](./extensions/plugins.md)** - Create reusable plugins
- **[Integration Guide](./extensions/integrations.md)** - Connect with external systems
- **[Hook System](./extensions/hooks.md)** - Extend framework behavior
- **[Custom Commands](./extensions/commands.md)** - Add CLI commands

### [Contributing](./contributing/README.md)
Everything you need to contribute to the project.

- **[Development Setup](./contributing/setup.md)** - Get your environment ready
- **[Code Standards](./contributing/standards.md)** - Coding conventions and style
- **[Testing Guide](./contributing/testing.md)** - Write and run tests
- **[Pull Request Guide](./contributing/pull-requests.md)** - Submit your changes
- **[Documentation Guide](./contributing/documentation.md)** - Help improve docs

### [Architecture](./architecture/README.md)
Deep dives into the framework's design and implementation.

- **[System Overview](./architecture/overview.md)** - High-level architecture
- **[Agent Architecture](./architecture/agents.md)** - How agents work internally
- **[Communication Protocol](./architecture/communication.md)** - Inter-agent messaging
- **[State Management](./architecture/state.md)** - System state handling
- **[Security Model](./architecture/security.md)** - Security architecture

## 🚀 Developer Quick Start

### Setting Up Development Environment

1. **[Clone and Setup](./contributing/setup.md)** (15 minutes)
   ```bash
   git clone https://github.com/bobmatnyc/claude-multiagent-pm.git
   cd claude-multiagent-pm
   npm install
   ```

2. **[Run Tests](./contributing/testing.md)** (5 minutes)
   ```bash
   npm test
   ```

3. **[Build Your First Agent](./extensions/custom-agents.md)** (30 minutes)
   - Use the agent template
   - Implement core methods
   - Test your agent

4. **[Submit Your Contribution](./contributing/pull-requests.md)**
   - Follow code standards
   - Write tests
   - Open a PR

## 💡 Common Development Tasks

### By Goal
- **Add a Feature**: [Contributing Guide](./contributing/README.md) → [Pull Request Guide](./contributing/pull-requests.md)
- **Fix a Bug**: [Development Setup](./contributing/setup.md) → [Testing Guide](./contributing/testing.md)
- **Create an Agent**: [Custom Agents Guide](./extensions/custom-agents.md) → [Agent API](./api/agents.md)
- **Build Integration**: [Integration Guide](./extensions/integrations.md) → [Services API](./api/services.md)
- **Improve Performance**: [Architecture Overview](./architecture/overview.md) → [Performance Tips](./contributing/performance.md)

### By Component
- **Core System**: [Core API](./api/core.md) | [System Architecture](./architecture/overview.md)
- **Agent System**: [Agent API](./api/agents.md) | [Agent Architecture](./architecture/agents.md)
- **CLI Interface**: [Commands Guide](./extensions/commands.md) | [CLI Architecture](./architecture/cli.md)
- **Service Layer**: [Services API](./api/services.md) | [Service Patterns](./architecture/services.md)

## 📋 Version Information

- **Framework Version**: 0.7.0
- **Node.js Requirement**: ≥16.0.0
- **Python Requirement**: ≥3.8.0
- **Documentation Updated**: 2025-07-18

## 🤝 Contributing Guidelines

### Code Contributions
1. Read [Code Standards](./contributing/standards.md)
2. Follow [Development Setup](./contributing/setup.md)
3. Write tests per [Testing Guide](./contributing/testing.md)
4. Submit via [Pull Request Guide](./contributing/pull-requests.md)

### Documentation Contributions
- Follow [Documentation Guide](./contributing/documentation.md)
- Use clear, concise language
- Include code examples
- Keep versions updated

## 🔧 Developer Resources

### Tools & Utilities
- **[Development Scripts](./tools/scripts.md)** - Helpful automation
- **[Debugging Tools](./tools/debugging.md)** - Debug effectively
- **[Performance Profiling](./tools/profiling.md)** - Find bottlenecks
- **[Test Utilities](./tools/testing.md)** - Testing helpers

### References
- **[Glossary](./reference/glossary.md)** - Technical terms
- **[FAQ](./reference/faq.md)** - Common questions
- **[Troubleshooting](./reference/troubleshooting.md)** - Common issues
- **[Changelog](../releases/README.md)** - Version history

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/bobmatnyc/claude-multiagent-pm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bobmatnyc/claude-multiagent-pm/discussions)
- **Security**: [Security Policy](./contributing/security.md)

## 🔄 Navigation

- **[↑ Top](#developer-documentation)**
- **[← Documentation Home](../README.md)**
- **[← User Docs](../user/README.md)**
- **[→ Technical Docs](../technical/README.md)**