---
issue_id: ISS-0118
title: Implement Agent Registry and Hierarchical Discovery System
description: Create comprehensive agent registry system with two-tier hierarchy (System → User), directory-based
  precedence, and integration with SharedPromptCache service for orchestrator functionality. This system will enable the
  orchestrator to discover and load custom/specialized agents beyond base agent types, implement directory hierarchy
  precedence (current directory > parent directories > system), and provide agent registry with listAgents() method in
  AgentPromptBuilder.
status: completed
priority: high
assignee: Engineer Agent
created_date: 2025-07-15T14:52:29.207Z
updated_date: 2025-07-15T19:38:49.000Z
estimated_tokens: 2500
actual_tokens: 3200
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
related_tasks: []
related_issues: []
tags:
  - agent-management
  - orchestrator
  - discovery-system
completion_percentage: 100
blocked_by: []
blocks: []
---

# Issue: Implement Agent Registry and Hierarchical Discovery System

## Description
Create comprehensive agent registry system with two-tier hierarchy (System → User), directory-based precedence, and integration with SharedPromptCache service for orchestrator functionality. This system will enable the orchestrator to discover and load custom/specialized agents beyond base agent types, implement directory hierarchy precedence (current directory > parent directories > system), and provide agent registry with listAgents() method in AgentPromptBuilder.

## Tasks
- [ ] Design and implement AgentRegistry class with agent discovery mechanisms
- [ ] Implement two-tier agent hierarchy (System → User) with directory-based precedence
- [ ] Create listAgents() method in AgentPromptBuilder for agent enumeration
- [ ] Integrate agent registry with SharedPromptCache service for performance
- [ ] Implement agent modification tracking and persistence
- [ ] Create specialized agent discovery mechanisms (custom agent loading)
- [ ] Design directory hierarchy precedence system: current directory > parent directories > system
- [ ] Implement agent loading fallback mechanisms and error handling
- [ ] Create comprehensive test suite for agent registry functionality
- [ ] Document agent registry API and integration patterns

## Acceptance Criteria
- [ ] AgentRegistry class provides listAgents() method returning available agents with metadata
- [ ] Two-tier hierarchy properly implemented: System agents (code-based) → User agents (filesystem-based)
- [ ] Directory precedence works: current directory > parent directories > system agents
- [ ] Agent registry integrates seamlessly with SharedPromptCache for performance optimization
- [ ] Custom/specialized agent discovery works beyond base agent types (Documentation, Ticketing, Version Control, QA, Research, Ops, Security, Engineer, Data Engineer)
- [ ] Agent modifications are tracked and persisted to appropriate locations (system vs user)
- [ ] Comprehensive error handling for missing agents, corrupted configs, and loading failures
- [ ] Performance benchmarks show <100ms agent discovery time for typical project
- [ ] All agent registry operations support caching and invalidation strategies
- [ ] Test coverage exceeds 90% for agent registry functionality

## Technical Requirements

### Agent Hierarchy Structure
```
System Agents (claude_pm/agents/):
├── documentation_agent.py
├── ticketing_agent.py
├── version_control_agent.py
├── qa_agent.py
├── research_agent.py
├── ops_agent.py
├── security_agent.py
├── engineer_agent.py
└── data_engineer_agent.py

User Agents (~/.claude-pm/agents/):
├── custom_agent.py
├── specialized_analyzer.py
└── project_specific_agent.py
```

### Directory Precedence Rules
1. **Current Directory**: `$PWD/.claude-pm/agents/` (highest precedence)
2. **Parent Directories**: Walk up directory tree checking `.claude-pm/agents/` 
3. **User Directory**: `~/.claude-pm/agents/` 
4. **System Directory**: `claude_pm/agents/` (lowest precedence, always available)

### AgentPromptBuilder Integration
```python
class AgentPromptBuilder:
    def listAgents(self) -> Dict[str, AgentMetadata]:
        """Return all available agents with metadata and precedence info"""
        pass
    
    def loadAgent(self, agent_name: str) -> Agent:
        """Load agent respecting hierarchy precedence"""
        pass
```

### SharedPromptCache Integration
- Cache agent discovery results for performance
- Invalidate cache when agent files change
- Support batch agent loading operations
- Optimize for repeated agent queries

## Implementation Notes

### Revised Agent Hierarchy (Simplified from Three-Tier)
- **REMOVED**: Project tier (`$PROJECT/.claude-pm/agents/project-specific/`)
- **RETAINED**: System tier (code-based agents)
- **RETAINED**: User tier (filesystem-based agents)
- **NEW**: Directory-based precedence for user agents

### Report-to-Ticket Workflow
All agent registry operations and discoveries should generate reports that are automatically associated with related tickets for tracking and analysis.

### Integration Points
- **Task Tool**: Agent registry must support subprocess agent creation
- **PM Orchestrator**: Registry provides agent discovery for delegation
- **Framework Services**: Integration with existing health monitoring and validation systems

### Performance Targets
- Agent discovery: <100ms for typical project
- Agent loading: <50ms per agent
- Registry initialization: <200ms
- Cache hit ratio: >95% for repeated queries

## Dependencies
- SharedPromptCache service implementation
- AgentPromptBuilder base infrastructure 
- Framework service integration points
- Existing agent loading mechanisms (for compatibility)

## Risks and Mitigation
- **Risk**: Agent loading conflicts between hierarchy levels
  - **Mitigation**: Clear precedence rules and conflict resolution
- **Risk**: Performance degradation with large agent registries
  - **Mitigation**: Caching and lazy loading strategies
- **Risk**: Breaking changes to existing agent loading
  - **Mitigation**: Backward compatibility layer and migration path
