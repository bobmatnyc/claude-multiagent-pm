# TicketingService Quick Reference

## Import & Initialize

```python
from claude_pm.services.ticketing_service import TicketingService, get_ticketing_service
from claude_pm.orchestration.ticketing_helpers import TicketingHelper

# Get singleton instance
ticketing = get_ticketing_service()
helper = TicketingHelper()
```

## Common Operations

### Create Ticket
```python
ticket = ticketing.create_ticket(
    title="Brief description",
    description="Detailed description",
    priority="high",  # low, medium, high, critical
    assignee="engineer-agent",
    labels=["bug", "urgent"],
    metadata={"sprint": "Q1-2025"}
)
```

### Update Ticket
```python
updated = ticketing.update_ticket(
    ticket_id,
    status="in_progress",  # open, in_progress, resolved, closed
    assignee="qa-agent",
    priority="critical"
)
```

### Add Comment
```python
ticketing.add_comment(
    ticket_id,
    "Progress update: Completed initial implementation",
    author="engineer-agent"
)
```

### Close Ticket
```python
ticketing.close_ticket(
    ticket_id,
    resolution="Fixed by refactoring imports"
)
```

### List Tickets
```python
# Filter by multiple criteria
tickets = ticketing.list_tickets(
    status="open",
    priority="high",
    assignee="engineer-agent",
    labels=["bug"],
    limit=10
)
```

### Search Tickets
```python
results = ticketing.search_tickets("ImportError", limit=5)
```

### Get Statistics
```python
stats = ticketing.get_ticket_statistics()
# Returns: total, by_status, by_priority, unassigned
```

## PM Helper Functions

### Create Agent Task
```python
ticket = helper.create_agent_task_ticket(
    agent_name="engineer",
    task_description="Implement feature X",
    priority="medium",
    additional_context={"estimated_hours": 8}
)
```

### Update Agent Task Status
```python
helper.update_agent_task_status(
    ticket_id,
    status="completed",
    comment="All tests passing"
)
```

### Get Agent Workload
```python
workload = helper.get_agent_workload("engineer")
# Returns: total_tickets, open, in_progress, high_priority
```

### Get Project Overview
```python
overview = helper.get_project_overview()
# Returns: total_tickets, agent_tasks, by_status, agents_with_tasks
```

### Find Related Tickets
```python
related = helper.find_related_tickets(
    keywords=["import", "error"],
    limit=10
)
```

## Async Operations

All methods have async equivalents:
```python
# Async versions
ticket = await ticketing.acreate_ticket(...)
ticket = await ticketing.aget_ticket(ticket_id)
tickets = await ticketing.alist_tickets(...)
updated = await ticketing.aupdate_ticket(ticket_id, ...)
```

## Automatic Ticket Creation Criteria

PM creates tickets automatically when:
- Priority is "high" or "critical"
- Task has 3+ requirements or deliverables
- Task description contains multi-agent keywords
- Explicit escalation triggers are defined

## Status Values
- `open` - New ticket
- `in_progress` - Being worked on
- `resolved` - Completed successfully
- `closed` - Closed (with or without resolution)

## Priority Levels
- `low` - Nice to have
- `medium` - Standard priority
- `high` - Important
- `critical` - Urgent/blocking

## Common Labels
- `bug` - Defect/issue
- `feature` - New functionality
- `task` - General work item
- `epic` - Large multi-ticket effort
- `security` - Security-related
- `documentation` - Docs update
- `refactor` - Code improvement

## Agent Assignee Naming
- `research-agent` - Research Agent
- `engineer-agent` - Engineer Agent  
- `qa-agent` - QA Agent
- `documentation-agent` - Documentation Agent
- `security-agent` - Security Agent
- `ops-agent` - Ops Agent
- `version-control-agent` - Version Control Agent
- `data-engineer-agent` - Data Engineer Agent
- `pm-orchestrator` - PM-level tasks

---

*Quick Reference v1.4.0 | Last Updated: 2025-07-21*