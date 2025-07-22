# TicketingService API Reference

**Last Updated**: 2025-07-21  
**Framework Version**: 1.4.0  
**Service Module**: `claude_pm.services.ticketing_service`

## Overview

The TicketingService is a core service that wraps ai-trackdown-pytools to provide simplified ticket management for PM orchestration and agent operations. It implements a singleton pattern for consistent ticket management across the framework.

## Key Features

- **Singleton Pattern**: Ensures consistent ticket management across all framework components
- **Simplified API**: Clean interface wrapping ai-trackdown-pytools complexity
- **Automatic Directory Management**: Handles ticket directory creation and discovery
- **Thread-Safe Operations**: Safe for concurrent use in multi-agent scenarios
- **Comprehensive Error Handling**: Graceful degradation when ai-trackdown is unavailable
- **Async Support**: Provides async methods for PM orchestration

## Installation & Import

```python
from claude_pm.services.ticketing_service import TicketingService, TicketData, get_ticketing_service

# Get singleton instance
ticketing = TicketingService.get_instance()

# Or use convenience function
ticketing = get_ticketing_service()
```

## Core Classes

### TicketData

A simplified data structure for ticket information:

```python
@dataclass
class TicketData:
    id: str                              # Unique ticket identifier
    title: str                           # Ticket title
    description: str                     # Detailed description
    status: str = "open"                 # open, in_progress, resolved, closed
    priority: str = "medium"             # low, medium, high, critical
    assignee: Optional[str] = None       # Who the ticket is assigned to
    labels: List[str] = field(default_factory=list)  # Categorization labels
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # Custom metadata
```

## API Methods

### Initialization

#### `TicketingService.get_instance()`

Returns the singleton instance of TicketingService.

```python
ticketing = TicketingService.get_instance()
```

### Ticket Operations

#### `create_ticket()`

Creates a new ticket with specified parameters.

```python
def create_ticket(
    title: str,
    description: str,
    priority: str = "medium",
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> TicketData
```

**Parameters:**
- `title`: Brief ticket title (required)
- `description`: Detailed description (required)
- `priority`: Priority level - "low", "medium", "high", "critical" (default: "medium")
- `assignee`: Optional assignee name
- `labels`: Optional list of categorization labels
- `metadata`: Optional dictionary of custom metadata

**Returns:** `TicketData` object with created ticket information

**Example:**
```python
ticket = ticketing.create_ticket(
    title="Implement user authentication",
    description="Add JWT-based authentication to the API endpoints",
    priority="high",
    assignee="engineer-agent",
    labels=["feature", "security", "backend"],
    metadata={
        "estimated_hours": 8,
        "sprint": "2025-Q1-Sprint3",
        "dependencies": ["database-schema", "jwt-library"]
    }
)
print(f"Created ticket: {ticket.id}")
```

#### `get_ticket()`

Retrieves a ticket by its ID.

```python
def get_ticket(ticket_id: str) -> Optional[TicketData]
```

**Parameters:**
- `ticket_id`: Unique ticket identifier

**Returns:** `TicketData` object or None if not found

**Example:**
```python
ticket = ticketing.get_ticket("CLAUDE-20250721120000")
if ticket:
    print(f"Title: {ticket.title}")
    print(f"Status: {ticket.status}")
    print(f"Assignee: {ticket.assignee}")
else:
    print("Ticket not found")
```

#### `list_tickets()`

Lists tickets with optional filtering.

```python
def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> List[TicketData]
```

**Parameters:**
- `status`: Filter by status ("open", "in_progress", "resolved", "closed")
- `priority`: Filter by priority ("low", "medium", "high", "critical")
- `assignee`: Filter by assignee name
- `labels`: Filter by labels (tickets must have ALL specified labels)
- `limit`: Maximum number of tickets to return

**Returns:** List of `TicketData` objects matching the criteria

**Example:**
```python
# Get all high-priority open tickets
urgent_tickets = ticketing.list_tickets(
    status="open",
    priority="high"
)

# Get tickets assigned to engineer agent
engineer_tasks = ticketing.list_tickets(
    assignee="engineer-agent",
    status="in_progress"
)

# Get security-related tickets
security_tickets = ticketing.list_tickets(
    labels=["security"],
    limit=10
)
```

#### `update_ticket()`

Updates an existing ticket's properties.

```python
def update_ticket(
    ticket_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[TicketData]
```

**Parameters:**
- `ticket_id`: Ticket identifier (required)
- `title`: New title (optional)
- `description`: New description (optional)
- `status`: New status (optional)
- `priority`: New priority (optional)
- `assignee`: New assignee (optional)
- `labels`: New labels (optional, replaces existing)
- `metadata`: New metadata (optional, merges with existing)

**Returns:** Updated `TicketData` object or None if not found

**Example:**
```python
# Update ticket status and assignee
updated = ticketing.update_ticket(
    "CLAUDE-20250721120000",
    status="in_progress",
    assignee="qa-agent",
    metadata={"qa_test_plan": "regression-suite-v2"}
)

# Update multiple properties
updated = ticketing.update_ticket(
    "CLAUDE-20250721120000",
    priority="critical",
    labels=["bug", "production", "urgent"],
    metadata={
        "escalated": True,
        "escalation_reason": "Customer impact"
    }
)
```

#### `add_comment()`

Adds a comment to a ticket.

```python
def add_comment(
    ticket_id: str,
    comment: str,
    author: Optional[str] = None
) -> bool
```

**Parameters:**
- `ticket_id`: Ticket identifier
- `comment`: Comment text
- `author`: Comment author (default: "claude-pm")

**Returns:** True if successful, False otherwise

**Example:**
```python
# Add progress update
success = ticketing.add_comment(
    "CLAUDE-20250721120000",
    "Completed initial implementation. Ready for code review.",
    author="engineer-agent"
)

# Add PM coordination note
ticketing.add_comment(
    "CLAUDE-20250721120000",
    "Escalating to QA Agent for comprehensive testing",
    author="pm-orchestrator"
)
```

#### `close_ticket()`

Closes a ticket with optional resolution.

```python
def close_ticket(
    ticket_id: str,
    resolution: Optional[str] = None
) -> Optional[TicketData]
```

**Parameters:**
- `ticket_id`: Ticket identifier
- `resolution`: Optional resolution description

**Returns:** Updated `TicketData` object or None if not found

**Example:**
```python
# Close with resolution
closed = ticketing.close_ticket(
    "CLAUDE-20250721120000",
    resolution="Fixed by implementing proper error handling in core service"
)

# Simple close
closed = ticketing.close_ticket("CLAUDE-20250721120001")
```

### Utility Methods

#### `search_tickets()`

Searches tickets by text query.

```python
def search_tickets(
    query: str,
    limit: Optional[int] = None
) -> List[TicketData]
```

**Parameters:**
- `query`: Search query (searches in title and description)
- `limit`: Maximum number of results

**Returns:** List of matching `TicketData` objects

**Example:**
```python
# Search for import-related tickets
import_issues = ticketing.search_tickets("ImportError", limit=5)

# Search for authentication tickets
auth_tickets = ticketing.search_tickets("authentication JWT")
```

#### `get_ticket_statistics()`

Returns ticket statistics for dashboard/reporting.

```python
def get_ticket_statistics() -> Dict[str, Any]
```

**Returns:** Dictionary with ticket statistics

**Example:**
```python
stats = ticketing.get_ticket_statistics()
print(f"Total tickets: {stats['total']}")
print(f"By status: {stats['by_status']}")
print(f"By priority: {stats['by_priority']}")
print(f"Unassigned: {stats['unassigned']}")
```

### Async Methods

All core methods have async equivalents for PM orchestration:

```python
# Async versions of all methods
await ticketing.acreate_ticket(...)
await ticketing.aget_ticket(ticket_id)
await ticketing.alist_tickets(...)
await ticketing.aupdate_ticket(ticket_id, ...)
```

**Example:**
```python
# Async ticket creation in PM orchestrator
async def orchestrate_bug_fix(error_details):
    # Create ticket asynchronously
    ticket = await ticketing.acreate_ticket(
        title=f"Fix: {error_details['error_type']}",
        description=error_details['full_description'],
        priority="high",
        labels=["bug", "auto-created"]
    )
    
    # Delegate to agents asynchronously
    await delegate_to_agent("research", ticket.id)
    await delegate_to_agent("engineer", ticket.id)
    
    return ticket.id
```

## Integration with PM Orchestrator

### Automatic Ticket Creation

The PM orchestrator automatically creates tickets based on these criteria:

1. **High/Critical Priority Tasks**: Any task marked as high or critical priority
2. **Complex Tasks**: Tasks with 3+ requirements or deliverables
3. **Multi-Agent Coordination**: Tasks requiring multiple agents
4. **Explicit Escalation Triggers**: Tasks with defined escalation conditions

```python
# In pm_orchestrator.py
def _should_create_ticket(self, delegation_context: AgentDelegationContext) -> bool:
    """Determine if a ticket should be created for this delegation."""
    if not self._ticketing_service:
        return False
        
    # High priority tasks always get tickets
    if delegation_context.priority in ["high", "critical"]:
        return True
    
    # Complex tasks with many requirements/deliverables
    if (len(delegation_context.requirements) >= self._auto_ticket_threshold or 
        len(delegation_context.deliverables) >= self._auto_ticket_threshold):
        return True
    
    # Multi-agent coordination indicators
    keywords = ["coordinate", "multi-agent", "cross-team", "integration"]
    if any(keyword in delegation_context.task_description.lower() for keyword in keywords):
        return True
    
    # Has explicit escalation triggers
    if delegation_context.escalation_triggers:
        return True
    
    return False
```

### PM Orchestration Example

```python
from claude_pm.services.pm_orchestrator import PMOrchestrator
from claude_pm.services.ticketing_service import get_ticketing_service

# Initialize orchestrator with ticketing
orchestrator = PMOrchestrator()
ticketing = get_ticketing_service()

# Create a complex task that triggers automatic ticket creation
prompt = orchestrator.generate_agent_prompt(
    agent_type="engineer",
    task_description="Implement comprehensive error handling system",
    requirements=[
        "Handle all async errors gracefully",
        "Implement retry logic with exponential backoff",
        "Add detailed logging for debugging",
        "Create user-friendly error messages"
    ],
    deliverables=[
        "Error handling utility module",
        "Updated async functions with error handling",
        "Comprehensive test suite",
        "Error handling documentation"
    ],
    priority="high",  # This triggers automatic ticket creation
    integration_notes="Coordinate with QA for test coverage"
)

# The orchestrator automatically creates a ticket for this high-priority, complex task
```

## Usage Patterns

### Pattern 1: Bug Tracking Workflow

```python
# 1. Create bug ticket when error is discovered
bug_ticket = ticketing.create_ticket(
    title="ImportError in unified_core_service",
    description="Users report ImportError when running claude-pm --version",
    priority="critical",
    labels=["bug", "production", "import-error"],
    metadata={
        "error_message": "ImportError: cannot import name 'unified_core_service'",
        "affected_versions": ["1.3.9", "1.4.0"],
        "user_reports": 5
    }
)

# 2. Assign to research agent
ticketing.update_ticket(
    bug_ticket.id,
    assignee="research-agent",
    status="in_progress"
)

# 3. Add findings
ticketing.add_comment(
    bug_ticket.id,
    "Root cause: Circular import between core.py and services.py",
    author="research-agent"
)

# 4. Reassign to engineer
ticketing.update_ticket(
    bug_ticket.id,
    assignee="engineer-agent",
    metadata={"root_cause": "circular_import"}
)

# 5. Close after fix
ticketing.close_ticket(
    bug_ticket.id,
    resolution="Refactored imports to eliminate circular dependency"
)
```

### Pattern 2: Feature Development Workflow

```python
# 1. Create feature ticket
feature = ticketing.create_ticket(
    title="Add real-time collaboration features",
    description="Implement WebSocket-based real-time updates for multi-user editing",
    priority="high",
    labels=["feature", "enhancement", "websocket"],
    assignee="engineer-agent"
)

# 2. Track progress through phases
phases = [
    ("research", "Investigating WebSocket libraries and patterns"),
    ("design", "Created architecture design document"),
    ("implementation", "Core WebSocket server implemented"),
    ("testing", "Integration tests passing"),
    ("documentation", "API docs and user guide complete")
]

for phase, update in phases:
    ticketing.add_comment(feature.id, update, author=f"{phase}-agent")
    ticketing.update_ticket(
        feature.id,
        metadata={f"{phase}_complete": True}
    )

# 3. Complete feature
ticketing.update_ticket(feature.id, status="resolved")
```

### Pattern 3: Multi-Agent Coordination

```python
# Create parent ticket for complex workflow
parent = ticketing.create_ticket(
    title="Migrate database from PostgreSQL to MongoDB",
    description="Complete database migration with zero downtime",
    priority="high",
    labels=["migration", "database", "multi-agent"],
    metadata={
        "agents_required": ["research", "engineer", "qa", "ops"],
        "estimated_days": 5
    }
)

# Create sub-tickets for each agent
subtasks = [
    ("research", "Analyze data models and migration strategies"),
    ("engineer", "Implement migration scripts and adapters"),
    ("qa", "Create comprehensive migration tests"),
    ("ops", "Plan and execute zero-downtime deployment")
]

for agent, task in subtasks:
    sub_ticket = ticketing.create_ticket(
        title=f"[{agent}] {task}",
        description=f"Subtask for {parent.id}: {task}",
        assignee=f"{agent}-agent",
        labels=["subtask", agent],
        metadata={"parent_ticket": parent.id}
    )
    
    ticketing.add_comment(
        parent.id,
        f"Created subtask {sub_ticket.id} for {agent} agent",
        author="pm-orchestrator"
    )
```

## Error Handling

The TicketingService includes comprehensive error handling:

```python
try:
    ticket = ticketing.create_ticket(
        title="Test ticket",
        description="Testing error handling"
    )
except Exception as e:
    logger.error(f"Failed to create ticket: {e}")
    # Service logs detailed error and returns gracefully
```

### Fallback Behavior

When ai-trackdown-pytools is not available:
- Create operations return stub TicketData with generated IDs
- Read operations return None or empty lists
- The service continues to function with limited capabilities

## Best Practices

### 1. Use Meaningful Ticket IDs

The service generates IDs in the format `CLAUDE-YYYYMMDDHHMMss`. Consider using prefixes in titles:
- `[Bug]` for bug reports
- `[Feature]` for new features
- `[Task]` for general tasks
- `[Epic]` for large multi-ticket efforts

### 2. Leverage Metadata

Use metadata for structured information:
```python
metadata = {
    "environment": "production",
    "affected_users": 150,
    "business_impact": "high",
    "technical_debt": True,
    "estimated_hours": 16,
    "actual_hours": 0,
    "code_review_required": True
}
```

### 3. Consistent Label Usage

Establish a labeling convention:
- **Type**: `bug`, `feature`, `task`, `epic`
- **Priority**: `p0`, `p1`, `p2`, `p3`
- **Component**: `frontend`, `backend`, `database`, `api`
- **Status**: `needs-review`, `blocked`, `ready-to-deploy`

### 4. Agent Assignment Patterns

Use consistent assignee naming:
- `research-agent` for Research Agent
- `engineer-agent` for Engineer Agent
- `qa-agent` for QA Agent
- `documentation-agent` for Documentation Agent
- `pm-orchestrator` for PM-level tasks

### 5. Progress Tracking

Add meaningful comments at key milestones:
```python
# Starting work
ticketing.add_comment(ticket_id, "Starting analysis of the issue", "research-agent")

# Providing updates
ticketing.add_comment(ticket_id, "Found root cause: memory leak in cache layer", "research-agent")

# Completion
ticketing.add_comment(ticket_id, "Fix implemented and tested successfully", "engineer-agent")
```

## Performance Considerations

### Singleton Pattern Benefits

- Single instance reduces memory overhead
- Consistent state across all components
- Efficient resource utilization

### Directory Management

The service automatically finds or creates the tickets directory:
1. Checks current directory for `tickets/`
2. Checks `.claude-pm/tickets/`
3. Creates `tickets/` in current directory if needed

### Thread Safety

The service uses thread locks for singleton initialization, making it safe for concurrent use in multi-agent scenarios.

## Troubleshooting

### Common Issues

1. **"Ticket not found" errors**
   - Verify ticket ID format
   - Check tickets directory location
   - Ensure proper permissions

2. **"ai-trackdown not available" warnings**
   - Install ai-trackdown-pytools: `pip install ai-trackdown-pytools`
   - Service continues with stub implementation

3. **Performance issues with many tickets**
   - Consider implementing pagination in list operations
   - Use search instead of listing all tickets
   - Limit results with the `limit` parameter

### Debug Mode

Enable detailed logging:
```python
import logging
logging.getLogger("claude_pm.services.ticketing_service").setLevel(logging.DEBUG)
```

## Summary

The TicketingService provides a robust, thread-safe interface for ticket management within the Claude PM Framework. Key benefits include:

1. **Simplified API** compared to raw ai-trackdown-pytools
2. **Automatic integration** with PM orchestrator
3. **Comprehensive error handling** and fallback behavior
4. **Async support** for modern Python applications
5. **Flexible metadata** for custom workflows

The service enables effective project management, multi-agent coordination, and progress tracking throughout the development lifecycle.

---

*API Reference generated by Documentation Agent*  
*Framework Version: 1.4.0*  
*Last Updated: 2025-07-21*