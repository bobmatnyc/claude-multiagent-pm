# Agent Selection Guide

## Overview

The Claude PM Framework v1.0.2 introduces enhanced agent selection capabilities that allow natural language task descriptions to be automatically mapped to the appropriate specialized agent. This guide explains how agent selection works and provides best practices for optimal routing.

## Agent Selection Methods

### 1. Natural Language Selection (94.1% Accuracy)

Simply describe what you need in natural language, and the framework will automatically select the appropriate agent:

```bash
# Examples of natural language task descriptions
"Research the latest Next.js 14 features"          → Research Agent
"Update the installation documentation"            → Documentation Agent
"Fix the authentication bug in login.js"          → Engineer Agent
"Run the test suite and check coverage"           → QA Agent
"Deploy the application to staging"               → Ops Agent
"Scan for security vulnerabilities"               → Security Agent
"Create a ticket for the UI rendering issue"     → Ticketing Agent
"Set up PostgreSQL database connection"           → Data Engineer Agent
"Create a new feature branch"                     → Version Control Agent
```

### 2. Explicit Agent Selection with @agent_name

For precise control over agent selection, use the `@agent_name` syntax at the beginning of your task:

```bash
# Explicit agent selection examples
"@researcher find documentation on React Server Components"
"@documenter update the API reference guide"
"@engineer implement the user profile feature"
"@qa validate the payment processing flow"
"@ops configure the CI/CD pipeline"
"@security audit the authentication system"
"@ticketer create epic for mobile app development"
"@data_engineer optimize database queries"
"@versioner merge feature branch to main"
```

### 3. Keyword-Based Selection

The framework uses semantic keyword matching to identify the appropriate agent:

#### Research Agent Keywords
- research, investigate, find, search, explore, analyze, study, review literature
- discover, examine, look into, gather information, documentation lookup

#### Documentation Agent Keywords
- document, documentation, docs, readme, changelog, guide, tutorial
- api reference, write docs, update docs, technical writing

#### Engineer Agent Keywords
- implement, code, develop, fix, debug, refactor, optimize code
- feature, bug, enhancement, function, class, module, api

#### QA Agent Keywords
- test, testing, quality, validate, verify, check, coverage
- unit test, integration test, e2e, lint, quality assurance

#### Ops Agent Keywords
- deploy, deployment, infrastructure, devops, ci/cd, pipeline
- server, hosting, environment, configuration, docker, kubernetes

#### Security Agent Keywords
- security, vulnerability, audit, scan, penetration, compliance
- authentication, authorization, encryption, certificate, threat

#### Ticketing Agent Keywords
- ticket, issue, epic, task, story, bug report, feature request
- jira, github issues, project tracking, sprint, backlog

#### Data Engineer Agent Keywords
- database, data, sql, nosql, mongodb, postgresql, redis
- data pipeline, etl, api integration, data store, cache

#### Version Control Agent Keywords
- git, branch, merge, commit, version, tag, release
- checkout, rebase, cherry-pick, pull request, version control

## Hierarchy and Precedence

When multiple agents could handle a task, the framework follows this precedence order:

1. **Explicit @agent_name** - Always takes highest priority
2. **Project-specific agents** - Custom agents in your project directory
3. **User-defined agents** - Personal agents in ~/.claude-pm/agents/
4. **System agents** - Core framework agents (fallback)

## Performance Characteristics

- **Selection Speed**: 0.34ms average parsing time
- **Accuracy**: 94.1% correct agent selection from natural language
- **Caching**: Agent metadata cached for repeated operations
- **Overhead**: Minimal impact on overall task execution time

## Advanced Features

### Multi-Agent Coordination

Some tasks automatically trigger multi-agent workflows:

```bash
"push" → Documentation Agent → QA Agent → Version Control Agent
"deploy" → Ops Agent → QA Agent
"publish" → Documentation Agent → Ops Agent
```

### Custom Agent Creation

Create specialized agents for your domain:

```bash
# Create a custom Performance Agent
mkdir -p .claude-pm/agents/specialized/
cat > .claude-pm/agents/specialized/performance-agent.md << 'EOF'
# Performance Agent

## Agent Profile
- **Nickname**: PerfOptimizer
- **Specializations**: ['performance', 'optimization', 'profiling']

## When to Use
- Application performance issues
- Database query optimization
- Memory leak detection
- Load testing coordination
EOF
```

### Agent Discovery

List all available agents in your environment:

```python
from claude_pm.core.agent_registry import AgentRegistry

registry = AgentRegistry()
agents = registry.listAgents()

for agent_id, metadata in agents.items():
    print(f"{agent_id}: {metadata.get('specializations', [])}")
```

## Troubleshooting

### Common Issues

1. **Wrong Agent Selected**
   - Use explicit @agent_name syntax for precise control
   - Check for ambiguous keywords in your task description
   - Verify custom agent precedence isn't overriding

2. **Agent Not Found**
   - Ensure agent files are in correct directory structure
   - Check file permissions on agent definitions
   - Verify agent metadata is properly formatted

3. **Slow Agent Selection**
   - Clear the SharedPromptCache if performance degrades
   - Check for circular dependencies in custom agents
   - Verify no infinite loops in agent discovery

### Debug Mode

Enable debug logging to see agent selection process:

```bash
export CLAUDE_PM_DEBUG=true
claude-pm
```

## Best Practices

1. **Natural Language First**: Start with natural descriptions and only use @agent_name when needed
2. **Clear Task Descriptions**: Be specific about what you want to accomplish
3. **Leverage Multi-Agent Workflows**: Use built-in commands like "push" for coordinated operations
4. **Custom Agent Naming**: Use clear, descriptive names for custom agents
5. **Test Agent Selection**: Verify correct agent routing before complex operations

## Examples

### Research Tasks
```bash
"Research best practices for React Server Components"
"Find documentation on Next.js 14 app router"
"Investigate performance optimization techniques"
```

### Development Tasks
```bash
"Implement user authentication with JWT tokens"
"Fix the memory leak in the dashboard component"
"Refactor the API client to use async/await"
```

### DevOps Tasks
```bash
"Deploy the application to staging environment"
"Set up CI/CD pipeline with GitHub Actions"
"Configure Docker containers for microservices"
```

### Quality Assurance
```bash
"Run all tests and generate coverage report"
"Validate the payment processing workflow"
"Check for accessibility compliance"
```

## Conclusion

The enhanced agent selection system in Claude PM Framework v1.0.2 makes it easier than ever to leverage specialized agents for your development workflow. Whether using natural language descriptions or explicit agent selection, the framework ensures your tasks are routed to the most appropriate specialist for optimal results.