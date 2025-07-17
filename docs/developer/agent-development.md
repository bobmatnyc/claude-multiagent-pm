# Agent Development Guide

## Overview

Agents are the core execution units of the Claude PM Framework. This guide covers everything you need to know about developing custom agents, from basic concepts to advanced patterns.

## Agent Architecture

### Agent Types

The framework supports two categories of agents:

1. **System Agents** (Code-based)
   - Built into the framework
   - Located in `claude_pm/agents/`
   - 9 core types: Documentation, Ticketing, Version Control, QA, Research, Ops, Security, Engineer, Data Engineer

2. **User Agents** (Filesystem-based)
   - Custom agents defined in markdown files
   - Discovered through directory hierarchy
   - Can override system agents or add new capabilities

### Agent Hierarchy

```
User Agents (Highest Priority)
├── Current Directory: $PWD/.claude-pm/agents/
├── Parent Directories: ../.claude-pm/agents/
└── User Home: ~/.claude-pm/agents/

System Agents (Lowest Priority)
└── Framework: claude_pm/agents/
```

## Creating a Custom Agent

### 1. Basic Agent Structure

Create a markdown file in `.claude-pm/agents/` with this structure:

```markdown
# Performance Optimization Agent

## Agent Profile
- **Nickname**: Optimizer
- **Type**: performance
- **Specializations**: ['performance', 'monitoring', 'optimization', 'profiling']
- **Authority**: Performance analysis, optimization recommendations, monitoring setup

## When to Use
- Application performance is degrading
- Database queries are slow
- Memory usage is high
- Need to set up performance monitoring
- Load testing is required

## Why This Agent Exists
This agent provides specialized knowledge in:
- Performance profiling tools and techniques
- Database query optimization
- Memory leak detection and prevention
- Load testing frameworks
- Performance monitoring best practices

## Capabilities
- **Performance Analysis**: Profile applications to identify bottlenecks
- **Database Optimization**: Analyze and optimize database queries
- **Memory Management**: Detect and fix memory leaks
- **Load Testing**: Design and execute load tests
- **Monitoring Setup**: Configure performance monitoring dashboards

## Task Tool Integration
When delegated to via Task Tool, use this format:

**Optimizer**: [Specific performance task]

TEMPORAL CONTEXT: Today is [date]. Apply date awareness to performance analysis.

**Task**: [Detailed task breakdown]
1. Analyze current performance metrics
2. Identify bottlenecks and issues
3. Provide optimization recommendations
4. Implement approved changes

**Context**: [Performance-specific context]
- Application architecture
- Current performance metrics
- Business requirements
- Technical constraints

**Authority**: Performance analysis, optimization recommendations
**Expected Results**: Performance report with actionable recommendations
**Integration**: Coordinate with Engineer Agent for implementation

## Collaboration Patterns
- Works with **QA Agent** for performance testing
- Coordinates with **Engineer Agent** for implementation
- Consults **Data Engineer Agent** for database optimization
- Reports to **Documentation Agent** for performance documentation

## Performance Considerations
- Use profiling tools judiciously to avoid overhead
- Consider production vs development environment differences
- Balance optimization effort with business value
- Document all performance changes and their impact

## Knowledge Base
### Tools and Frameworks
- **Profiling**: cProfile, py-spy, Chrome DevTools, perf
- **Monitoring**: Prometheus, Grafana, DataDog, New Relic
- **Load Testing**: JMeter, Locust, K6, Artillery
- **Database**: EXPLAIN plans, query analyzers, index optimization

### Best Practices
1. Measure before optimizing
2. Focus on bottlenecks with highest impact
3. Consider algorithmic improvements before micro-optimizations
4. Monitor performance continuously
5. Document baseline metrics
```

### 2. Agent Metadata Requirements

Every agent must include:

- **Nickname**: Short name for Task Tool delegation
- **Type**: Agent category (e.g., performance, architecture, security)
- **Specializations**: List of specialized capabilities
- **Authority**: What the agent can decide and modify

### 3. Directory Organization

Organize agents by purpose:

```
.claude-pm/agents/
├── specialized/          # Domain-specific agents
│   ├── performance-agent.md
│   ├── architecture-agent.md
│   └── ui-ux-agent.md
├── custom/              # Project-specific agents  
│   ├── legacy-migration-agent.md
│   └── compliance-agent.md
└── overrides/           # System agent overrides
    └── qa-agent.md      # Enhanced QA agent
```

## Advanced Agent Development

### 1. Agent Specializations

Define clear specializations for discovery:

```markdown
## Agent Profile
- **Specializations**: ['api', 'rest', 'graphql', 'integration', 'swagger']
```

These enable discovery via:
```python
api_agents = registry.listAgents(specialization='api')
```

### 2. Context Filtering

Agents should specify what context they need:

```markdown
## Context Requirements
- **Required Context**:
  - API specifications and schemas
  - Authentication mechanisms
  - Rate limiting rules
  - Integration test results
- **Optional Context**:
  - Performance metrics
  - Usage analytics
  - Client feedback
```

### 3. Decision Authority

Be explicit about agent authority:

```markdown
## Authority
- **Can Decide**:
  - API endpoint design
  - Response format standards
  - Error handling patterns
  - Rate limiting strategies
- **Cannot Decide**:
  - Business logic changes
  - Data model modifications
  - Security policy changes
- **Must Consult**:
  - Breaking API changes → PM
  - New authentication methods → Security Agent
  - Performance impacts → Performance Agent
```

### 4. Integration Patterns

Define how the agent integrates with others:

```markdown
## Integration Patterns

### Pre-Task Dependencies
- **Security Agent**: Review API security before implementation
- **Architecture Agent**: Validate API design patterns

### Parallel Coordination
- **Documentation Agent**: API documentation generation
- **QA Agent**: API contract testing

### Post-Task Handoffs
- **Engineer Agent**: Implementation of API endpoints
- **Ops Agent**: API deployment and monitoring
```

## Agent Training System

### 1. Learning Patterns

Agents can learn from:
- Successful task completions
- Error corrections
- User feedback
- Performance metrics

```markdown
## Learning Configuration
- **Learning Enabled**: true
- **Pattern Categories**:
  - api_design_patterns
  - error_handling_patterns
  - performance_optimizations
- **Feedback Integration**: 
  - Direct corrections improve future responses
  - Success patterns are reinforced
  - Failed approaches are avoided
```

### 2. Knowledge Accumulation

```markdown
## Knowledge Base
### Learned Patterns
- **Successful API Designs**: [Accumulated patterns]
- **Common Pitfalls**: [Identified anti-patterns]
- **Optimization Techniques**: [Proven approaches]

### Metrics Tracking
- Task success rate: 95%
- Average completion time: 12 minutes
- User satisfaction: 4.8/5
```

## Testing Custom Agents

### 1. Agent Validation

```bash
# Validate agent file structure
python -m claude_pm.agents.validator .claude-pm/agents/my-agent.md

# Test agent discovery
python -c "
from claude_pm.core.agent_registry import AgentRegistry
registry = AgentRegistry()
agents = registry.listAgents()
print('My agent discovered:', 'my-agent' in agents)
"
```

### 2. Integration Testing

```python
# test_custom_agent.py
import pytest
from claude_pm.core.agent_registry import AgentRegistry
from claude_pm.orchestration import TaskTool

@pytest.mark.asyncio
async def test_custom_agent_execution():
    """Test custom agent task execution."""
    registry = AgentRegistry()
    
    # Verify agent discovery
    agents = registry.listAgents(specialization='performance')
    assert 'performance-optimization' in agents
    
    # Test task delegation
    result = await TaskTool.create_subprocess(
        agent_type='performance',
        task_description='Analyze API response times',
        context={'api_endpoints': ['/users', '/products']}
    )
    
    assert result.success
    assert 'performance_report' in result.output
```

### 3. Performance Testing

```python
# Benchmark agent performance
import time
from claude_pm.utils.performance import PerformanceMonitor

monitor = PerformanceMonitor()

# Time agent loading
timer_id = monitor.start_timer('agent_loading')
agents = registry.listAgents()
load_time = monitor.end_timer(timer_id)

print(f"Agent loading time: {load_time:.3f}s")
assert load_time < 0.1  # Should load in under 100ms
```

## Best Practices

### 1. Agent Design

- **Single Responsibility**: Each agent should have a clear, focused purpose
- **Clear Authority**: Define what the agent can and cannot do
- **Explicit Dependencies**: Document required context and integrations
- **Performance Aware**: Consider the impact of agent operations

### 2. Documentation

- **Comprehensive Examples**: Include real-world usage examples
- **Clear Scenarios**: Describe when to use (and not use) the agent
- **Integration Guide**: Explain how the agent works with others
- **Maintenance Notes**: Include debugging and troubleshooting tips

### 3. Error Handling

```markdown
## Error Handling
### Common Errors
1. **Missing Context**: Agent requires API specification
   - **Solution**: Ensure API docs are provided in context
   
2. **Authority Exceeded**: Attempting to modify security policies
   - **Solution**: Delegate security changes to Security Agent
   
3. **Performance Impact**: Analysis causing system slowdown
   - **Solution**: Run profiling during off-peak hours
```

### 4. Version Compatibility

```markdown
## Compatibility
- **Framework Version**: ≥0.9.0
- **Dependencies**: 
  - Performance monitoring tools
  - Database query analyzers
- **Breaking Changes**: 
  - v0.8.x: Different specialization format
  - v0.7.x: No learning system support
```

## Debugging Agents

### 1. Enable Debug Logging

```bash
export CLAUDE_PM_DEBUG=true
export CLAUDE_PM_LOG_LEVEL=debug
claude-pm
```

### 2. Agent Execution Trace

```python
# Trace agent execution
from claude_pm.core.agent_registry import AgentRegistry
import logging

logging.basicConfig(level=logging.DEBUG)

registry = AgentRegistry()
# This will show detailed loading and execution logs
```

### 3. Common Issues

**Agent Not Discovered:**
- Check file location and permissions
- Verify markdown structure
- Ensure specializations are properly formatted

**Poor Performance:**
- Check SharedPromptCache integration
- Verify agent isn't loading unnecessary data
- Profile agent execution time

**Integration Failures:**
- Verify dependent agents are available
- Check context filtering logic
- Review authority boundaries

## Agent Examples

### Example 1: Database Migration Agent

```markdown
# Database Migration Agent

## Agent Profile
- **Nickname**: Migrator
- **Type**: migration
- **Specializations**: ['database', 'migration', 'schema', 'data']
- **Authority**: Schema analysis, migration script generation

## When to Use
- Database schema needs updating
- Data needs to be migrated between systems
- Database version upgrades required
- Schema drift detection needed

## Capabilities
- Analyze schema differences
- Generate migration scripts
- Validate data integrity
- Plan zero-downtime migrations
- Handle rollback scenarios
```

### Example 2: Security Audit Agent

```markdown
# Security Audit Agent

## Agent Profile
- **Nickname**: Auditor
- **Type**: security
- **Specializations**: ['security', 'audit', 'compliance', 'vulnerability']
- **Authority**: Security analysis, vulnerability reporting

## When to Use
- Regular security audits
- Pre-deployment security checks
- Compliance verification needed
- Vulnerability assessment required

## Capabilities
- Scan for common vulnerabilities
- Check compliance with security policies
- Analyze authentication/authorization
- Review encryption practices
- Generate security reports
```

## Next Steps

- Review [API Reference](./api-reference.md) for technical details
- See [Testing Guide](./testing.md) for testing strategies
- Check [Contributing Guide](./contributing.md) for submission process
- Read [Performance Guide](./performance.md) for optimization tips

---

*For more examples, see the `claude_pm/agents/` directory and community-contributed agents.*