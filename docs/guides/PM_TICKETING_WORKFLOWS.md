# PM Ticketing Workflows Guide

**Last Updated**: 2025-07-21  
**Framework Version**: 1.4.0

## Overview

This guide provides practical examples of how the PM uses ticketing for project orchestration and multi-agent coordination.

## PM Ticketing Mental Model

```
User Request → PM Creates Ticket → PM Orchestrates Agents → Agents Update Ticket → PM Tracks Progress
```

## Common PM Ticketing Scenarios

### Scenario 1: User Reports a Bug

**User**: "The claude-pm --version command is throwing an ImportError"

**PM Response**:
```markdown
I'll create a critical bug ticket and coordinate the fix across our agent team.

Creating ticket BUG-2025-001 for this issue...

**Orchestration Plan**:
1. Research Agent will investigate the root cause
2. Engineer Agent will implement the fix
3. QA Agent will verify the resolution

Starting multi-agent coordination now...
```

**PM Actions**:
1. Creates ticket with bug details
2. Sets priority based on impact
3. Defines agent workflow
4. Delegates to agents in sequence
5. Monitors progress through ticket updates

### Scenario 2: Feature Request

**User**: "I want to create custom agent templates"

**PM Response**:
```markdown
I'll create a feature ticket and coordinate implementation across multiple agents.

Creating ticket FEAT-2025-002 for custom agent templates...

**Orchestration Plan**:
1. Research Agent will investigate best practices
2. Engineer Agent will design and implement
3. Documentation Agent will create user guides
4. QA Agent will test the feature

This is a high-priority feature with 12 user votes. Starting coordination...
```

### Scenario 3: Documentation Update

**User**: "Update the README with ticketing instructions"

**PM Response**:
```markdown
I'll create a documentation ticket and delegate to our Documentation Agent.

Creating ticket DOC-2025-003 for README updates...

This is a focused task that our Documentation Agent can handle independently.
Delegating now...
```

## PM Ticketing Patterns

### Pattern 1: Sequential Workflow

```python
# PM orchestrates agents in sequence
workflow = {
    "steps": [
        {"agent": "Research Agent", "task": "Analyze problem", "depends_on": None},
        {"agent": "Engineer Agent", "task": "Implement solution", "depends_on": "Research Agent"},
        {"agent": "QA Agent", "task": "Test solution", "depends_on": "Engineer Agent"}
    ]
}
```

### Pattern 2: Parallel Workflow

```python
# PM orchestrates agents in parallel
workflow = {
    "parallel_groups": [
        {
            "group": 1,
            "agents": ["Research Agent", "Security Agent"],
            "can_run_together": True
        },
        {
            "group": 2,
            "agents": ["Engineer Agent"],
            "depends_on_group": 1
        }
    ]
}
```

### Pattern 3: Conditional Workflow

```python
# PM adjusts workflow based on agent results
workflow = {
    "initial": "Research Agent",
    "conditions": {
        "if_security_issue": "Security Agent",
        "if_performance_issue": "Ops Agent",
        "default": "Engineer Agent"
    }
}
```

## PM Ticket Management Commands

### Creating Tickets Programmatically

```python
# PM creates different ticket types

def create_bug_ticket(title, description, error_message):
    return {
        "id": generate_ticket_id("BUG"),
        "title": title,
        "description": description,
        "priority": "critical" if "production" in description else "high",
        "metadata": {
            "error_message": error_message,
            "affected_users": estimate_impact(error_message)
        },
        "orchestration": {
            "agents_required": ["Research Agent", "Engineer Agent", "QA Agent"],
            "workflow": "diagnose -> fix -> test"
        }
    }

def create_feature_ticket(title, description, user_votes=0):
    return {
        "id": generate_ticket_id("FEAT"),
        "title": title,
        "description": description,
        "priority": "high" if user_votes > 10 else "medium",
        "metadata": {
            "user_votes": user_votes,
            "estimated_effort": estimate_effort(description)
        },
        "orchestration": {
            "agents_required": ["Research Agent", "Engineer Agent", "Documentation Agent", "QA Agent"],
            "workflow": "research -> implement -> document -> test"
        }
    }
```

### Monitoring Ticket Progress

```python
# PM monitors active tickets

def get_active_tickets():
    tickets_dir = Path("tasks")
    active_tickets = []
    
    for ticket_file in tickets_dir.glob("*.json"):
        with open(ticket_file, 'r') as f:
            ticket = json.load(f)
        
        if ticket["status"] in ["open", "in_progress"]:
            active_tickets.append(ticket)
    
    return sorted(active_tickets, 
                  key=lambda t: {"critical": 0, "high": 1, "medium": 2, "low": 3}[t["priority"]])

# PM provides status update
active = get_active_tickets()
print(f"Currently tracking {len(active)} active tickets:")
for ticket in active:
    print(f"  {ticket['id']}: {ticket['title']} ({ticket['status']})")
```

### Updating Tickets Based on Agent Results

```python
# PM updates ticket after agent completes work

def handle_agent_completion(ticket_id, agent_name, result):
    ticket = load_ticket(ticket_id)
    
    # Add agent update
    ticket["agent_updates"].append({
        "agent": agent_name,
        "timestamp": datetime.now().isoformat(),
        "result": result["status"],
        "details": result["summary"]
    })
    
    # Update ticket status based on workflow
    if agent_name == "QA Agent" and result["status"] == "passed":
        ticket["status"] = "closed"
        ticket["resolution"] = "fixed"
    elif result["status"] == "failed":
        ticket["status"] = "blocked"
        ticket["blocker"] = f"{agent_name} reported: {result['error']}"
    
    save_ticket(ticket)
```

## Real-World PM Examples

### Example 1: Critical Production Bug

```markdown
**User**: "Production is down! ImportError in core service!"

**PM Internal Process**:
1. Create critical bug ticket
2. Alert all required agents
3. Coordinate immediate response

**PM to User**: 
"I've created critical ticket BUG-2025-004 and initiated emergency response:

🚨 **Emergency Coordination**:
- Research Agent: Analyzing error logs (ETA: 5 min)
- Engineer Agent: Standing by for fix implementation
- QA Agent: Preparing emergency test suite
- Ops Agent: Ready for deployment

I'll update you as each agent reports progress."

**PM Task Tool Delegations**:
**Research Agent**: URGENT - Analyze production ImportError in core service
**Engineer Agent**: STANDBY - Implement emergency fix once root cause identified
**QA Agent**: PREPARE - Ready emergency test suite for hotfix validation
**Ops Agent**: STANDBY - Prepare for emergency deployment
```

### Example 2: Feature Planning

```markdown
**User**: "Plan implementation for custom agent templates feature"

**PM Internal Process**:
1. Create feature ticket with planning phase
2. Gather requirements from Research Agent
3. Create subtasks for implementation

**PM to User**:
"I'll coordinate a comprehensive feature implementation plan.

Created FEAT-2025-005 with the following phases:

📋 **Phase 1: Research & Design** (This week)
- Research Agent: Best practices analysis
- Documentation Agent: API design draft

📋 **Phase 2: Implementation** (Next week)
- Engineer Agent: Core functionality
- Data Engineer Agent: Storage design

📋 **Phase 3: Testing & Documentation** (Week 3)
- QA Agent: Comprehensive testing
- Documentation Agent: User guides

Starting Phase 1 coordination now..."
```

### Example 3: Multi-Ticket Dependency

```markdown
**User**: "We need to refactor the auth system and update all documentation"

**PM Internal Process**:
1. Create parent epic ticket
2. Create child tickets for each component
3. Define dependencies between tickets

**PM to User**:
"I'll create an epic with multiple coordinated tickets:

🎯 **Epic EPIC-2025-001: Auth System Refactor**

Child Tickets:
- FEAT-2025-006: Refactor authentication module
- FEAT-2025-007: Update authorization logic  
- DOC-2025-004: Update auth documentation
- QA-2025-001: Create auth test suite

Dependencies:
- Documentation depends on both feature completions
- QA suite can start with feature development

Initiating parallel coordination for independent tasks..."
```

## Advanced PM Patterns

### 1. Ticket Templates for Common Scenarios

```python
PM_TICKET_TEMPLATES = {
    "security_vulnerability": {
        "priority": "critical",
        "tags": ["security", "urgent"],
        "orchestration": {
            "agents_required": ["Security Agent", "Engineer Agent", "QA Agent"],
            "workflow": "assess -> patch -> verify",
            "sla": "4 hours"
        }
    },
    "performance_issue": {
        "priority": "high",
        "tags": ["performance", "optimization"],
        "orchestration": {
            "agents_required": ["Research Agent", "Engineer Agent", "Ops Agent"],
            "workflow": "profile -> optimize -> deploy"
        }
    }
}
```

### 2. Ticket Escalation Rules

```python
# PM escalation logic
def should_escalate(ticket):
    # Critical bugs open > 2 hours
    if ticket["priority"] == "critical" and hours_open(ticket) > 2:
        return True
    
    # Blocked tickets
    if ticket["status"] == "blocked":
        return True
    
    # Multiple failed agent attempts
    failed_attempts = count_failed_updates(ticket)
    if failed_attempts >= 3:
        return True
    
    return False
```

### 3. Sprint Planning with Tickets

```python
# PM organizes tickets into sprints
def plan_sprint(available_hours=80):
    tickets = get_open_tickets()
    sprint_tickets = []
    allocated_hours = 0
    
    # Sort by priority and effort
    tickets.sort(key=lambda t: (
        priority_value(t["priority"]),
        t.get("metadata", {}).get("estimated_hours", 8)
    ))
    
    for ticket in tickets:
        estimated = ticket.get("metadata", {}).get("estimated_hours", 8)
        if allocated_hours + estimated <= available_hours:
            sprint_tickets.append(ticket)
            allocated_hours += estimated
    
    return sprint_tickets
```

## Best Practices for PM Ticketing

### 1. Clear Ticket Descriptions
Always include:
- What is broken/needed
- Why it matters
- Who is affected
- When it's needed

### 2. Appropriate Priority Setting
- **Critical**: Production down, security breach
- **High**: Major features, significant bugs  
- **Medium**: Standard work items
- **Low**: Nice-to-haves

### 3. Workflow Definition
Define clear agent sequences:
- Linear workflows for simple tasks
- Parallel workflows for independent tasks
- Conditional workflows for complex scenarios

### 4. Progress Communication
Keep users informed:
- Ticket created confirmation
- Agent assignment updates
- Progress milestones
- Completion notifications

### 5. Ticket Hygiene
- Close completed tickets
- Update blocked tickets
- Archive old tickets
- Regular status reviews

## Troubleshooting Common Issues

### Issue 1: Can't Find Tickets
```bash
# List all tickets
ls -la tickets/

# Find specific ticket
find tasks -name "*BUG*"

# Search ticket content
grep -r "import error" tickets/
```

### Issue 2: Ticket Updates Not Saving
```python
# Ensure directory exists
Path("tasks").mkdir(parents=True, exist_ok=True)

# Check file permissions
os.chmod("tasks", 0o755)
```

### Issue 3: Agent Can't Access Ticket
```python
# Provide ticket path in agent context
context = {
    "ticket_path": f"tickets/{ticket_id}.json",
    "ticket_id": ticket_id
}
```

## Summary

PM ticketing workflows enable sophisticated project orchestration through:

1. **Structured ticket creation** for all work items
2. **Multi-agent coordination** based on ticket workflows
3. **Progress tracking** through agent updates
4. **Priority-based orchestration** for efficient delivery
5. **Clear communication** with users about work status

The ticketing system serves as the PM's memory and coordination tool, ensuring nothing falls through the cracks and all work is properly tracked and delegated.

---

*PM Ticketing Workflows Guide - Created by Documentation Agent*