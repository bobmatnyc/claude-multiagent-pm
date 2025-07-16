# Project-Specific Agents for Claude PM Framework

This directory contains project-specific agents that have the highest precedence in the Claude PM Framework agent hierarchy.

## Codebase Research Agent

### 🎯 Primary Purpose
**The FIRST PLACE TO GO when planning work on the Claude PM Framework codebase.**

The Codebase Research Agent is a specialized Research Agent with maximum-size embedded knowledge about the entire Claude PM Framework architecture, services, patterns, and business logic.

### 🏗️ Agent Specification
- **Agent Type**: research
- **Tier**: project (highest precedence)
- **Specializations**: codebase, architecture, business_logic, framework, claude_pm_framework
- **Authority**: codebase_research_highest

### 📚 Embedded Knowledge Coverage
The agent contains comprehensive knowledge about:

#### Architecture
- Core philosophy and design principles
- Two-tier agent hierarchy (System + User agents)
- Agent precedence and discovery patterns
- Service architecture and integration patterns
- Performance optimization strategies

#### Business Logic
- Operational workflows (startup, push, deploy, publish)
- TodoWrite integration with agent prefixes
- Subprocess validation protocol
- Task Tool delegation patterns
- Temporal context integration

#### Deployment Patterns
- Framework protection mechanisms
- Script deployment automation
- Integrity testing requirements
- Version consistency validation
- Critical file location management

#### Performance Optimization
- Agent registry performance targets
- SharedPromptCache integration
- Health monitoring patterns
- Optimization strategies and benchmarks

### 🚀 Core Operations

#### 1. `async_answer_codebase_question(question, context=None)`
Answer specific questions about framework architecture, patterns, and implementation.

**Usage:**
```python
result = await agent.async_answer_codebase_question(
    "What is the agent hierarchy in Claude PM Framework?"
)
```

#### 2. `async_analyze_architecture(component=None, depth="detailed")`
Analyze framework architecture components in detail.

**Usage:**
```python
result = await agent.async_analyze_architecture("agent", "comprehensive")
```

#### 3. `async_explain_business_logic(workflow=None, detail_level="comprehensive")`
Explain business logic and operational workflows.

**Usage:**
```python
result = await agent.async_explain_business_logic("push", "detailed")
```

#### 4. `async_guide_implementation(task, context=None)`
Provide implementation guidance for framework tasks.

**Usage:**
```python
result = await agent.async_guide_implementation("create new agent")
```

#### 5. `async_research_patterns(pattern_type, scope="comprehensive")`
Research framework patterns and optimizations.

**Usage:**
```python
result = await agent.async_research_patterns("performance", "exhaustive")
```

### 🔧 Integration with Framework

#### Task Tool Delegation
```python
# PM Agent delegates to Codebase Research Agent
result = await task_tool.delegate(
    agent_type="research",
    specialization="codebase",
    operation="answer_codebase_question",
    question="How does the push workflow work?"
)
```

#### TodoWrite Integration
```python
# Use "Researcher:" prefix for codebase research tasks
TodoWrite([
    {
        "id": "research-001",
        "content": "Researcher: Analyze framework architecture for new feature implementation",
        "status": "pending",
        "priority": "high"
    }
])
```

### 📊 Performance Characteristics

#### Targets
- **Agent Discovery**: < 100ms for typical project
- **Agent Loading**: < 50ms per agent
- **Query Response**: < 100ms for knowledge queries
- **Cache Hit Ratio**: > 95% for repeated queries

#### Optimization Features
- SharedPromptCache integration
- Lazy loading of capabilities
- Async operations throughout
- Comprehensive error handling
- Performance metrics collection

### 🔍 Usage Guidelines

#### When to Use
1. **Planning framework modifications or extensions**
2. **Understanding framework architecture and patterns**
3. **Getting implementation guidance for framework tasks**
4. **Researching framework business logic and workflows**
5. **Analyzing framework performance and optimization**

#### Delegation Pattern
```
PM Agent → Codebase Research Agent (for all framework planning questions)
```

#### Authority Scope
- Complete framework knowledge and architectural guidance
- Highest precedence as project-tier agent
- Comprehensive implementation recommendations
- Performance optimization strategies

### 🛠️ Agent Hierarchy Integration

#### Precedence Order
1. **Project Agents** (THIS AGENT): `.claude-pm/agents/project-specific/` - Highest precedence
2. **User Agents**: `~/.claude-pm/agents/user-defined/` - Mid-priority
3. **System Agents**: `claude_pm/agents/` - Lowest precedence, fallback

#### Discovery and Loading
- Automatic discovery via agent registry
- Specialization-based routing for codebase questions
- Performance-optimized loading with caching
- Comprehensive error handling and recovery

### 📝 Example Usage Session

```python
import asyncio
from codebase_research_agent import CodebaseResearchAgent

async def planning_session():
    # Initialize agent
    agent = CodebaseResearchAgent()
    await agent._initialize()
    
    # Get architecture overview
    arch_analysis = await agent.async_analyze_architecture()
    
    # Ask specific implementation question
    question_result = await agent.async_answer_codebase_question(
        "How should I implement a new service in the framework?"
    )
    
    # Get workflow guidance
    workflow_info = await agent.async_explain_business_logic("push")
    
    # Research patterns for implementation
    patterns = await agent.async_research_patterns("service", "comprehensive")
    
    # Get implementation guidance
    guidance = await agent.async_guide_implementation(
        "create new service for data processing"
    )
    
    await agent._cleanup()

# Run planning session
asyncio.run(planning_session())
```

### 🚨 Critical Notes

#### Framework Version Alignment
- Agent knowledge is aligned with Framework v0.9.0
- Must be updated when framework version changes
- Knowledge embedding reflects current architecture

#### Integration Requirements
- Respects agent hierarchy precedence
- Integrates with Task Tool subprocess creation
- Compatible with SharedPromptCache optimization
- Provides comprehensive operational insights

#### Performance Considerations
- Embedded knowledge for maximum response speed
- Async operations throughout for performance
- Comprehensive caching strategies
- Performance monitoring and metrics collection

---

**This agent serves as the authoritative source for Claude PM Framework codebase knowledge and should be the first resource consulted when planning any framework-related work.**