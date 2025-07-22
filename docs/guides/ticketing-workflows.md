# PM Ticketing Workflows Guide

**Last Updated**: 2025-07-21  
**Framework Version**: 1.4.0  
**Audience**: PM Orchestrators and Framework Users

## Overview

This guide demonstrates how the PM orchestrator uses the TicketingService for project management, task delegation, and multi-agent coordination. Learn practical workflows and patterns for effective ticket-based orchestration.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Automatic Ticket Creation](#automatic-ticket-creation)
3. [Common Workflows](#common-workflows)
4. [Integration Patterns](#integration-patterns)
5. [Best Practices](#best-practices)
6. [Examples](#examples)

## Core Concepts

### Ticket Lifecycle in PM Orchestration

```
User Request → PM Analysis → Ticket Creation → Agent Delegation → Progress Tracking → Completion
```

### Key Components

1. **TicketingService**: Core service for ticket operations
2. **TicketingHelper**: PM-specific helper functions
3. **PMOrchestrator**: Integrates ticketing into delegation workflows
4. **AgentDelegationContext**: Contains task details for ticket creation

## Automatic Ticket Creation

### When PM Creates Tickets Automatically

The PM orchestrator automatically creates tickets when:

```python
# 1. High or Critical Priority Tasks
priority in ["high", "critical"]

# 2. Complex Tasks (3+ requirements or deliverables)
len(requirements) >= 3 or len(deliverables) >= 3

# 3. Multi-Agent Coordination Required
"coordinate" in task_description or "multi-agent" in task_description

# 4. Explicit Escalation Triggers Defined
escalation_triggers is not None and len(escalation_triggers) > 0
```

### Configuration

```python
# Default threshold for automatic ticket creation
self._auto_ticket_threshold = 3  # Requirements/deliverables threshold

# Enable/disable ticketing
self._ticketing_service = TicketingService.get_instance()
self._ticketing_helper = TicketingHelper()
```

## Common Workflows

### Workflow 1: Bug Fix Orchestration

```python
# User reports: "claude-pm --version shows ImportError"

# PM creates bug ticket automatically
bug_workflow = """
**Research Agent**: Investigate ImportError in claude-pm --version

TEMPORAL CONTEXT: Today is 2025-07-21. Critical production bug.

**Task**: 
1. Analyze the ImportError stack trace
2. Identify root cause of import failure
3. Document findings and proposed fix

**Context**: 
- Error: ImportError with unified_core_service
- Affects: Production users running v1.4.0
- Priority: Critical - blocking all CLI usage

**Expected Results**: Root cause analysis and fix recommendation
"""

# Ticket automatically created due to "critical" priority
# Ticket ID: CLAUDE-20250721150000

# After Research Agent completes:
engineering_workflow = """
**Engineer Agent**: Fix ImportError based on research findings

TEMPORAL CONTEXT: Today is 2025-07-21. Implement critical fix.

**Task**:
1. Review research findings from ticket CLAUDE-20250721150000
2. Implement the recommended fix
3. Ensure no circular imports remain
4. Update ticket with implementation details

**Context**:
- Research found: Circular import in core service
- Solution: Refactor import structure
- Ticket: CLAUDE-20250721150000

**Expected Results**: Working fix with clean imports
"""

# PM updates ticket status as agents progress
```

### Workflow 2: Feature Implementation

```python
# User requests: "Add real-time collaboration features"

# PM analyzes and creates comprehensive ticket
feature_workflow = orchestrator.generate_agent_prompt(
    agent_type="research",
    task_description="Research real-time collaboration implementation",
    requirements=[
        "WebSocket protocol analysis",
        "Scalability considerations",
        "Security implications",
        "Library recommendations"
    ],
    deliverables=[
        "Technical feasibility report",
        "Architecture design proposal",
        "Implementation roadmap",
        "Risk assessment"
    ],
    priority="high",  # Triggers ticket creation
    integration_notes="Multi-phase implementation requiring all agents"
)

# Automatic ticket includes orchestration plan:
# {
#   "orchestration": {
#     "agents_required": ["research", "engineer", "security", "qa"],
#     "workflow": "research → design → implement → secure → test",
#     "phases": [
#       {"phase": 1, "agent": "research", "duration": "2 days"},
#       {"phase": 2, "agent": "engineer", "duration": "5 days"},
#       {"phase": 3, "agent": "security", "duration": "1 day"},
#       {"phase": 4, "agent": "qa", "duration": "2 days"}
#     ]
#   }
# }
```

### Workflow 3: Multi-Agent Coordination

```python
# Complex task requiring multiple agents

# PM creates parent ticket and subtasks
def orchestrate_database_migration():
    # Parent ticket for overall coordination
    parent_ticket = ticketing_helper.create_agent_task_ticket(
        agent_name="pm",
        task_description="Coordinate PostgreSQL to MongoDB migration",
        priority="high",
        additional_context={
            "type": "epic",
            "estimated_days": 5,
            "business_impact": "high"
        }
    )
    
    # Create subtasks for each agent
    subtasks = [
        {
            "agent": "research",
            "task": "Analyze data models and migration patterns",
            "dependencies": []
        },
        {
            "agent": "engineer", 
            "task": "Implement migration scripts",
            "dependencies": ["research"]
        },
        {
            "agent": "qa",
            "task": "Create migration test suite",
            "dependencies": ["engineer"]
        },
        {
            "agent": "ops",
            "task": "Execute zero-downtime deployment",
            "dependencies": ["qa"]
        }
    ]
    
    for subtask in subtasks:
        ticket = ticketing_helper.create_agent_task_ticket(
            agent_name=subtask["agent"],
            task_description=subtask["task"],
            priority="high",
            additional_context={
                "parent_ticket": parent_ticket.id,
                "dependencies": subtask["dependencies"],
                "phase": subtasks.index(subtask) + 1
            }
        )
        
        # Link to parent
        ticketing.add_comment(
            parent_ticket.id,
            f"Created subtask {ticket.id} for {subtask['agent']} agent",
            author="pm-orchestrator"
        )
```

## Integration Patterns

### Pattern 1: Ticket-Driven Task Delegation

```python
from claude_pm.orchestration.ticketing_helpers import TicketingHelper

class TicketDrivenOrchestrator:
    def __init__(self):
        self.helper = TicketingHelper()
        self.orchestrator = PMOrchestrator()
    
    def delegate_with_ticket(self, agent_type, task, priority="medium"):
        # Create ticket first
        ticket = self.helper.create_agent_task_ticket(
            agent_name=agent_type,
            task_description=task,
            priority=priority
        )
        
        # Generate prompt with ticket context
        prompt = self.orchestrator.generate_agent_prompt(
            agent_type=agent_type,
            task_description=f"{task} (Ticket: {ticket.id})",
            requirements=[f"Update ticket {ticket.id} with progress"],
            priority=priority
        )
        
        # Delegate to agent
        return prompt, ticket.id
```

### Pattern 2: Progress Tracking Integration

```python
def track_agent_progress(ticket_id, agent_name, checkpoint):
    """Update ticket as agent progresses through task"""
    
    checkpoints = {
        "started": "Agent has started working on the task",
        "analysis_complete": "Initial analysis completed",
        "implementation_started": "Beginning implementation phase",
        "testing": "Running tests and validation",
        "completed": "Task completed successfully",
        "blocked": "Task blocked, escalation required"
    }
    
    # Update ticket with progress
    if checkpoint in checkpoints:
        ticketing.add_comment(
            ticket_id,
            checkpoints[checkpoint],
            author=f"{agent_name}-agent"
        )
        
        # Update status based on checkpoint
        if checkpoint == "started":
            ticketing.update_ticket(ticket_id, status="in_progress")
        elif checkpoint == "completed":
            ticketing.update_ticket(ticket_id, status="resolved")
        elif checkpoint == "blocked":
            ticketing.update_ticket(ticket_id, 
                                  status="blocked",
                                  priority="high")
```

### Pattern 3: Workload Balancing

```python
def get_agent_availability():
    """Check agent workload before delegation"""
    helper = TicketingHelper()
    
    agents = ["documentation", "engineer", "qa", "research"]
    workload = {}
    
    for agent in agents:
        stats = helper.get_agent_workload(agent)
        workload[agent] = {
            "available": stats["open"] < 3,  # Max 3 open tickets
            "current_load": stats["open"] + stats["in_progress"],
            "high_priority": stats["high_priority"],
            "capacity": 5 - (stats["open"] + stats["in_progress"])
        }
    
    return workload

# Use in delegation decision
def delegate_to_available_agent(task_type, task_description):
    workload = get_agent_availability()
    
    # Find agent with capacity
    suitable_agents = {
        "documentation": ["docs", "changelog", "readme"],
        "engineer": ["implement", "fix", "refactor"],
        "qa": ["test", "validate", "verify"],
        "research": ["investigate", "analyze", "explore"]
    }
    
    for agent, keywords in suitable_agents.items():
        if any(kw in task_description.lower() for kw in keywords):
            if workload[agent]["available"]:
                return agent
    
    # Fallback to least loaded agent
    return min(workload.items(), key=lambda x: x[1]["current_load"])[0]
```

## Best Practices

### 1. Structured Ticket Metadata

```python
# Good: Rich metadata for tracking
ticket_metadata = {
    "task_type": "bug_fix",
    "component": "core_service",
    "error_type": "ImportError",
    "affected_versions": ["1.3.9", "1.4.0"],
    "reproduction_steps": [...],
    "test_cases": [...],
    "estimated_hours": 4,
    "actual_hours": 0,
    "blockers": [],
    "related_tickets": ["CLAUDE-20250720140000"]
}

# Bad: Minimal metadata
ticket_metadata = {"type": "bug"}
```

### 2. Clear Orchestration Plans

```python
# Good: Detailed orchestration in ticket
orchestration = {
    "workflow_name": "Security Vulnerability Fix",
    "agents_required": ["security", "engineer", "qa"],
    "phases": [
        {
            "phase": 1,
            "agent": "security",
            "task": "Vulnerability assessment and fix strategy",
            "estimated_hours": 2,
            "deliverables": ["Security report", "Fix recommendations"]
        },
        {
            "phase": 2,
            "agent": "engineer",
            "task": "Implement security fixes",
            "estimated_hours": 4,
            "deliverables": ["Patched code", "Security tests"]
        },
        {
            "phase": 3,
            "agent": "qa",
            "task": "Security testing and validation",
            "estimated_hours": 3,
            "deliverables": ["Test results", "Security certification"]
        }
    ],
    "success_criteria": [
        "Vulnerability patched",
        "No regression in functionality",
        "Security tests passing"
    ]
}
```

### 3. Meaningful Progress Updates

```python
# Good: Detailed progress with context
def update_progress(ticket_id, agent, phase, details):
    update = f"""
Phase {phase} Progress Update:
- Status: {details['status']}
- Completed: {details['completed_items']}
- Remaining: {details['remaining_items']}
- Blockers: {details.get('blockers', 'None')}
- Next Steps: {details['next_steps']}
    """
    
    ticketing.add_comment(ticket_id, update.strip(), author=f"{agent}-agent")

# Bad: Vague updates
ticketing.add_comment(ticket_id, "Working on it", author="engineer-agent")
```

### 4. Ticket Lifecycle Management

```python
class TicketLifecycleManager:
    def __init__(self):
        self.ticketing = get_ticketing_service()
        self.helper = TicketingHelper()
    
    def create_and_track(self, task_type, description, priority="medium"):
        """Create ticket and set up tracking"""
        # Create with full context
        ticket = self.helper.create_agent_task_ticket(
            agent_name=self._get_primary_agent(task_type),
            task_description=description,
            priority=priority,
            additional_context={
                "created_by": "pm_orchestrator",
                "workflow_type": task_type,
                "sla_hours": self._get_sla(priority),
                "created_at": datetime.now().isoformat()
            }
        )
        
        # Set up monitoring
        self._schedule_sla_check(ticket.id)
        self._notify_stakeholders(ticket.id)
        
        return ticket
    
    def _get_sla(self, priority):
        """Get SLA hours by priority"""
        sla_map = {
            "critical": 4,
            "high": 24,
            "medium": 48,
            "low": 120
        }
        return sla_map.get(priority, 48)
```

### 5. Error Recovery Patterns

```python
def safe_ticket_operation(operation, *args, **kwargs):
    """Wrapper for resilient ticket operations"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Ticket operation failed, retrying: {e}")
                time.sleep(retry_delay * (attempt + 1))
            else:
                # Create fallback ticket manually
                fallback_ticket = {
                    "id": f"FALLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "title": kwargs.get('title', 'Fallback ticket'),
                    "description": f"Original operation failed: {e}",
                    "priority": "high",
                    "status": "open"
                }
                logger.error(f"Ticket operation failed, created fallback: {fallback_ticket['id']}")
                return fallback_ticket
```

## Examples

### Example 1: Complete Bug Fix Workflow

```python
# 1. User reports bug
user_report = "Getting ImportError when running claude-pm --version"

# 2. PM creates investigation ticket
investigation_ticket = helper.create_agent_task_ticket(
    agent_name="research",
    task_description=f"Investigate: {user_report}",
    priority="critical",
    additional_context={
        "error_type": "ImportError",
        "user_impact": "Complete CLI failure",
        "reports_count": 5
    }
)

# 3. Research agent investigates
research_prompt = f"""
**Research Agent**: Investigate ImportError in ticket {investigation_ticket.id}

TEMPORAL CONTEXT: Today is 2025-07-21. Critical production issue.

**Task**:
1. Read error reports and stack traces
2. Identify the root cause
3. Propose solution approach
4. Update ticket {investigation_ticket.id} with findings

**Expected Results**: Root cause analysis and fix recommendation
"""

# 4. After research completes, create fix ticket
fix_ticket = helper.create_agent_task_ticket(
    agent_name="engineer",
    task_description="Fix ImportError based on research findings",
    priority="critical",
    additional_context={
        "parent_ticket": investigation_ticket.id,
        "root_cause": "circular import in core.py",
        "proposed_fix": "refactor import structure"
    }
)

# 5. Engineer implements fix
# 6. QA validates fix
# 7. PM closes tickets

ticketing.close_ticket(
    investigation_ticket.id,
    resolution="Root cause identified: circular import"
)

ticketing.close_ticket(
    fix_ticket.id,
    resolution="Fixed by refactoring import structure in PR #123"
)
```

### Example 2: Feature Development with Phases

```python
# Multi-phase feature implementation
feature_request = "Add API rate limiting to prevent abuse"

# Phase 1: Research
research_ticket = create_phased_ticket(
    phase=1,
    agent="research",
    task="Research rate limiting strategies and libraries",
    deliverables=[
        "Comparison of rate limiting algorithms",
        "Library recommendations",
        "Performance impact analysis"
    ]
)

# Phase 2: Design
design_ticket = create_phased_ticket(
    phase=2,
    agent="engineer",
    task="Design rate limiting architecture",
    dependencies=[research_ticket.id],
    deliverables=[
        "Architecture diagram",
        "API design document",
        "Configuration schema"
    ]
)

# Phase 3: Implementation
impl_ticket = create_phased_ticket(
    phase=3,
    agent="engineer",
    task="Implement rate limiting system",
    dependencies=[design_ticket.id],
    deliverables=[
        "Rate limiting middleware",
        "Configuration system",
        "Admin interface"
    ]
)

# Phase 4: Testing
test_ticket = create_phased_ticket(
    phase=4,
    agent="qa",
    task="Test rate limiting under load",
    dependencies=[impl_ticket.id],
    deliverables=[
        "Load test results",
        "Edge case validation",
        "Performance benchmarks"
    ]
)

# Track overall progress
def get_feature_progress(ticket_ids):
    total = len(ticket_ids)
    completed = 0
    
    for ticket_id in ticket_ids:
        ticket = ticketing.get_ticket(ticket_id)
        if ticket and ticket.status in ["resolved", "closed"]:
            completed += 1
    
    return {
        "progress_percentage": (completed / total) * 100,
        "completed_phases": completed,
        "total_phases": total,
        "status": "complete" if completed == total else "in_progress"
    }
```

### Example 3: Emergency Response Workflow

```python
# Production emergency handling
def handle_production_emergency(error_details):
    # 1. Create emergency ticket
    emergency = helper.create_agent_task_ticket(
        agent_name="ops",
        task_description=f"EMERGENCY: {error_details['summary']}",
        priority="critical",
        additional_context={
            "type": "production_emergency",
            "severity": "P0",
            "affected_services": error_details['services'],
            "user_impact": error_details['impact'],
            "started_at": datetime.now().isoformat()
        }
    )
    
    # 2. Immediate triage
    triage_agents = ["ops", "engineer", "security"]
    for agent in triage_agents:
        subtask = helper.create_agent_task_ticket(
            agent_name=agent,
            task_description=f"Emergency triage for {emergency.id}",
            priority="critical",
            additional_context={
                "parent_emergency": emergency.id,
                "response_sla_minutes": 15
            }
        )
    
    # 3. Create war room
    war_room = {
        "emergency_ticket": emergency.id,
        "participants": triage_agents,
        "status_updates": [],
        "resolution_steps": []
    }
    
    # 4. Track resolution
    def update_emergency_status(status, details):
        ticketing.add_comment(
            emergency.id,
            f"STATUS UPDATE: {status}\n{details}",
            author="emergency-response"
        )
        war_room["status_updates"].append({
            "time": datetime.now().isoformat(),
            "status": status,
            "details": details
        })
    
    return emergency, war_room
```

## Summary

The PM ticketing workflows enable:

1. **Automatic ticket creation** for complex or high-priority tasks
2. **Multi-agent coordination** through ticket-based workflows
3. **Progress tracking** across all project phases
4. **Workload balancing** based on agent availability
5. **Emergency response** patterns for critical issues

By following these patterns and best practices, PM orchestrators can effectively manage complex projects, coordinate multiple agents, and maintain visibility throughout the development lifecycle.

---

*Workflow Guide by Documentation Agent*  
*Framework Version: 1.4.0*  
*Last Updated: 2025-07-21*