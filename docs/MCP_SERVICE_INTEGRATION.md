# MCP Service Integration Guide

## Overview

The Claude PM Framework now includes comprehensive MCP (Model Context Protocol) service integration, enabling enhanced development workflows through productivity and context management tools.

## Supported MCP Services

### MCP-Zen
**Purpose**: Second opinion service that validates responses with another LLM, plus mindfulness tools
**Available Tools**: 
- `zen_quote` - Generate motivational zen quotes
- `breathing_exercise` - Provide breathing exercises for stress relief  
- `focus_timer` - Set focused work sessions

**Key Capability**: Provides alternative LLM perspective for response validation and decision-making

**Usage Contexts**:
- When needing a second opinion on complex technical decisions
- During critical code review processes requiring validation
- For validating architectural decisions with alternative perspective
- When seeking different approaches to challenging problems
- During stress management in development workflows

### Context 7
**Purpose**: Up-to-date code documentation and library examples fetcher
**Available Tools**:
- `resolve-library-id` - Resolve library names to Context7-compatible IDs
- `get-library-docs` - Fetch current documentation for any library

**Key Benefits**: Provides current, version-specific documentation instead of outdated training data

**Usage Contexts**:
- When needing current library documentation and examples
- For up-to-date API references and code samples
- When working with new or recently updated libraries
- To avoid hallucinated or outdated API information
- During development tasks requiring specific library knowledge

## Orchestrator Integration

### Automatic Detection

The orchestrator automatically detects available MCP services during initialization and provides contextual recommendations based on:

1. **Workflow Type**: Multi-agent coordination, code development, project management
2. **Development Context**: Debugging, project switching, complex tasks
3. **Agent Task Type**: Specific agent roles and responsibilities

### MCP-Enhanced Workflows

#### Multi-Agent Coordination Workflow

```python
# Orchestrator automatically detects and recommends:
{
    "task_start": "Use zen_quote for motivation, context_switch for project setup",
    "agent_handoff": "Use workflow_optimizer to optimize transitions", 
    "error_handling": "Use breathing_exercise for stress management",
    "task_completion": "Use project_memory to store learnings"
}
```

#### Code Development Workflow

```python
# Enhanced with productivity tools:
{
    "complex_task_start": "Use focus_timer to set dedicated work sessions",
    "debugging_session": "Use zen_quote for maintaining calm perspective", 
    "refactoring": "Use breathing_exercise before major changes"
}
```

#### Library Integration Workflow

```python
# Documentation-enhanced development:
{
    "library_selection": "Use resolve-library-id to identify proper library documentation",
    "implementation": "Use get-library-docs for current API references and examples", 
    "troubleshooting": "Use get-library-docs with specific topics for targeted help"
}
```

## Usage Instructions for Orchestrator

### 1. Service Detection

The orchestrator should regularly check MCP service availability:

```python
# Check available services
mcp_status = await orchestrator.check_mcp_service_availability()

if mcp_status["orchestrator_ready"]:
    logger.info(f"Orchestrator enhanced with {mcp_status['total_services_detected']} MCP services")
else:
    logger.info("Consider installing MCP services for enhanced workflows")
```

### 2. Workflow Enhancement

When coordinating multi-agent tasks, the orchestrator should:

```python
# Get workflow-specific recommendations
recommendations = await orchestrator.get_mcp_service_recommendations(
    workflow_name="multi_agent_coordination"
)

# Apply recommendations to task execution
for recommendation in recommendations.get("workflow_recommendations", []):
    # Integrate MCP tools at appropriate workflow stages
    if "zen_quote" in recommendation["available_tools"]:
        # Use for motivation before complex tasks
        pass
    if "context_switch" in recommendation["available_tools"]:
        # Use for project context management
        pass
```

### 3. Context-Aware Service Usage

For specific development contexts:

```python
# Get services for specific contexts
debugging_services = await orchestrator.get_development_context_services("debugging")
project_switching_services = await orchestrator.get_development_context_services("project_switching")

# Apply context-specific enhancements
if debugging_services:
    # Use breathing exercises for stress management during debugging
    # Use zen quotes for maintaining perspective
    pass

if project_switching_services:
    # Use context switching tools for seamless transitions
    # Use project memory for maintaining state
    pass
```

### 4. Task Enhancement

Before executing agent tasks, enhance them with MCP context:

```python
# Enhance task with MCP services
enhanced_task = await orchestrator.enhance_task_with_mcp_services(original_task)

# Task now includes MCP service context:
# - Available tools for the workflow
# - Integration points for enhanced execution
# - Usage guidance for optimal results
```

## Orchestrator Decision Framework

### When to Recommend MCP Services

1. **Complex Multi-Agent Coordination**:
   - Multiple agents working in parallel
   - Cross-project context switching required
   - Extended work sessions planned

2. **High-Stress Development Contexts**:
   - Debugging difficult issues
   - Major refactoring tasks
   - Critical deadline pressure

3. **Productivity Optimization**:
   - Long coding sessions
   - Context switching between projects
   - Need for focused work periods

### Service Selection Logic

```python
def select_mcp_services_for_context(context: str, available_services: List[MCPService]) -> List[str]:
    """
    Select appropriate MCP services based on development context.
    
    Context-Service Mapping:
    - "debugging" -> MCP-Zen (breathing exercises, zen quotes)
    - "project_switching" -> Context 7 (context switching, project memory)
    - "complex_task_start" -> MCP-Zen (focus timer, motivation)
    - "multi_agent_coordination" -> Both services for comprehensive enhancement
    """
    recommendations = []
    
    if context in ["debugging", "stress_management", "difficult_bugs"]:
        if "mcp-zen" in available_services:
            recommendations.extend(["zen_quote", "breathing_exercise"])
    
    if context in ["project_switching", "context_management", "multi_project"]:
        if "context-7" in available_services:
            recommendations.extend(["context_switch", "project_memory"])
    
    if context in ["complex_task_start", "focused_work", "productivity"]:
        if "mcp-zen" in available_services:
            recommendations.append("focus_timer")
    
    return recommendations
```

## Integration Patterns

### Pattern 1: Pre-Task Preparation

```python
# Before starting a complex task:
1. Check available MCP services
2. Get context-appropriate recommendations  
3. Suggest relevant tools (focus_timer, zen_quote, context_switch)
4. Enhance task with MCP context
5. Execute enhanced task
```

### Pattern 2: Inter-Agent Communication

```python
# When coordinating between agents:
1. Use workflow_optimizer for transition planning
2. Use project_memory to maintain context
3. Use zen_quote for maintaining team morale
4. Store learnings for future optimization
```

### Pattern 3: Error Recovery

```python
# When agents encounter errors:
1. Use breathing_exercise for stress management
2. Use zen_quote for perspective maintenance
3. Use workflow_optimizer to improve process
4. Store error patterns in project_memory
```

## Configuration and Setup

### Installation Verification

The orchestrator should verify MCP service installation:

```bash
# MCP-Zen verification
npx @modelcontextprotocol/server-zen --help

# Context 7 verification  
context-7-mcp --version
```

### Configuration Integration

Services should be configured in Claude settings:

```json
{
  "mcpServers": {
    "zen": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-zen"]
    },
    "context7": {
      "command": "context-7-mcp", 
      "args": ["--port", "3007"]
    }
  }
}
```

## Best Practices

### For Orchestrator Operation

1. **Regular Service Detection**: Check MCP service availability every 5 minutes
2. **Context-Aware Recommendations**: Match services to specific development contexts
3. **Workflow Integration**: Embed MCP tools at natural workflow transition points
4. **Progressive Enhancement**: Use MCP services to enhance rather than replace core functionality
5. **User Guidance**: Provide clear recommendations on when and how to use MCP tools

### For Development Teams

1. **Install Recommended Services**: Set up MCP-Zen and Context 7 for optimal experience
2. **Configure Properly**: Ensure services are properly configured in Claude settings
3. **Use Contextually**: Apply MCP tools based on orchestrator recommendations
4. **Feedback Loop**: Provide feedback on MCP service effectiveness for continuous improvement

## Troubleshooting

### Service Detection Issues

```python
# If services aren't detected:
1. Verify installation: npx @modelcontextprotocol/server-zen --help
2. Check configuration: Review Claude MCP settings
3. Force refresh: await orchestrator.check_mcp_service_availability()
4. Review logs: Check orchestrator logs for detection errors
```

### Integration Problems

```python  
# If integration isn't working:
1. Check orchestrator MCP status: orchestrator.get_mcp_integration_status()
2. Verify service availability: await orchestrator.detect_available_services()
3. Review recommendations: Check workflow and context recommendations
4. Test individual services: Verify each MCP service works independently
```

## Future Enhancements

### Planned Integrations

1. **Additional MCP Services**: Support for more productivity and development tools
2. **Advanced Context Detection**: More sophisticated context analysis for service recommendations
3. **Performance Metrics**: Track MCP service usage effectiveness
4. **Custom Workflows**: User-defined workflow patterns with MCP integration
5. **AI-Driven Optimization**: Machine learning-based service recommendation improvements

---

This integration enhances the Claude PM Framework with intelligent productivity and context management capabilities, making multi-agent development workflows more efficient and user-friendly.