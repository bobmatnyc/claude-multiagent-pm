# Ticketing API Reference

**Last Updated**: 2025-07-21  
**Framework Version**: 1.4.0  
**ai-trackdown-pytools Version**: 1.1.0

## Overview

This technical reference documents the Python API for ticketing operations using ai-trackdown-pytools within the Claude PM Framework.

## Python API

### Importing the Module

```python
import ai_trackdown
from ai_trackdown import (
    create_task,
    list_tasks, 
    get_task,
    update_task,
    add_comment
)
```

### Core Functions

#### create_task()

Creates a new task/ticket.

```python
def create_task(
    title: str,
    description: str = "",
    issue_id: str = None,
    assignee: str = None,
    priority: str = "medium",
    tags: List[str] = None
) -> dict:
    """
    Create a new task.
    
    Args:
        title: Task title
        description: Detailed description
        issue_id: Parent issue ID (e.g., "ISS-0162")
        assignee: Who the task is assigned to
        priority: low, medium, high, critical
        tags: List of tags
    
    Returns:
        dict: Created task with generated ID
    """
```

**Example:**
```python
task = create_task(
    title="Fix ImportError in core service",
    description="Users getting ImportError when running claude-pm --version",
    priority="critical",
    tags=["bug", "core"]
)
print(f"Created task: {task['task_id']}")
```

#### list_tasks()

Lists all tasks with optional filtering.

```python
def list_tasks(
    status: str = None,
    assignee: str = None,
    issue_id: str = None,
    tags: List[str] = None
) -> List[dict]:
    """
    List tasks with optional filters.
    
    Args:
        status: Filter by status (open, in_progress, completed)
        assignee: Filter by assignee
        issue_id: Filter by parent issue
        tags: Filter by tags
    
    Returns:
        List[dict]: List of matching tasks
    """
```

**Example:**
```python
# Get all open critical bugs
critical_bugs = list_tasks(
    status="open",
    tags=["bug", "critical"]
)

for bug in critical_bugs:
    print(f"{bug['task_id']}: {bug['title']}")
```

#### get_task()

Retrieves a specific task by ID.

```python
def get_task(task_id: str) -> dict:
    """
    Get task details by ID.
    
    Args:
        task_id: Task ID (e.g., "TSK-0032")
    
    Returns:
        dict: Task details or None if not found
    """
```

**Example:**
```python
task = get_task("TSK-0032")
if task:
    print(f"Title: {task['title']}")
    print(f"Status: {task['status']}")
    print(f"Assignee: {task['assignee']}")
```

#### update_task()

Updates task properties.

```python
def update_task(
    task_id: str,
    status: str = None,
    assignee: str = None,
    priority: str = None,
    add_tags: List[str] = None,
    remove_tags: List[str] = None,
    metadata: dict = None
) -> dict:
    """
    Update task properties.
    
    Args:
        task_id: Task ID to update
        status: New status
        assignee: New assignee
        priority: New priority
        add_tags: Tags to add
        remove_tags: Tags to remove
        metadata: Additional metadata to merge
    
    Returns:
        dict: Updated task
    """
```

**Example:**
```python
# Update task status and add agent update
updated = update_task(
    task_id="TSK-0032",
    status="in_progress",
    assignee="Engineer Agent",
    metadata={
        "agent_updates": [{
            "agent": "Research Agent",
            "timestamp": datetime.now().isoformat(),
            "action": "Completed analysis",
            "details": "Found circular import"
        }]
    }
)
```

#### add_comment()

Adds a comment to the parent issue (not directly to tasks).

```python
def add_comment(
    issue_id: str,
    comment: str,
    author: str = "Claude PM"
) -> dict:
    """
    Add comment to parent issue.
    
    Args:
        issue_id: Parent issue ID
        comment: Comment text
        author: Comment author
    
    Returns:
        dict: Comment details
    """
```

**Example:**
```python
# Add task-related comment to parent issue
add_comment(
    issue_id="ISS-0162",
    comment="Engineer Agent (TSK-0032): Fixed import error, ready for QA",
    author="Engineer Agent"
)
```

## File-Based Storage API

For direct file manipulation when needed:

### Ticket File Structure

```python
import json
from pathlib import Path
from datetime import datetime

class TicketManager:
    def __init__(self, tickets_dir="tasks"):
        self.tickets_dir = Path(tickets_dir)
        self.tickets_dir.mkdir(parents=True, exist_ok=True)
    
    def create_ticket(self, ticket_type, title, description, **kwargs):
        """Create a new ticket file"""
        ticket_id = self._generate_id(ticket_type)
        
        ticket = {
            "id": ticket_id,
            "title": title,
            "description": description,
            "status": "open",
            "priority": kwargs.get("priority", "medium"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "assignee": kwargs.get("assignee", "PM"),
            "tags": kwargs.get("tags", []),
            "metadata": kwargs.get("metadata", {}),
            "orchestration": kwargs.get("orchestration", {}),
            "agent_updates": []
        }
        
        ticket_path = self.tickets_dir / f"{ticket_id}.json"
        with open(ticket_path, 'w') as f:
            json.dump(ticket, f, indent=2)
        
        return ticket
    
    def load_ticket(self, ticket_id):
        """Load ticket from file"""
        ticket_path = self.tickets_dir / f"{ticket_id}.json"
        if ticket_path.exists():
            with open(ticket_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_ticket(self, ticket):
        """Save ticket to file"""
        ticket["updated_at"] = datetime.now().isoformat()
        ticket_path = self.tickets_dir / f"{ticket['id']}.json"
        with open(ticket_path, 'w') as f:
            json.dump(ticket, f, indent=2)
    
    def list_tickets(self, **filters):
        """List tickets with optional filters"""
        tickets = []
        
        for ticket_file in self.tickets_dir.glob("*.json"):
            with open(ticket_file, 'r') as f:
                ticket = json.load(f)
            
            # Apply filters
            if filters.get("status") and ticket["status"] != filters["status"]:
                continue
            if filters.get("priority") and ticket["priority"] != filters["priority"]:
                continue
            if filters.get("assignee") and ticket["assignee"] != filters["assignee"]:
                continue
            
            tickets.append(ticket)
        
        return tickets
    
    def _generate_id(self, ticket_type):
        """Generate unique ticket ID"""
        year = datetime.now().year
        existing = list(self.tickets_dir.glob(f"{ticket_type}-{year}-*.json"))
        next_num = len(existing) + 1
        return f"{ticket_type}-{year}-{next_num:03d}"
```

## Integration Patterns

### PM Integration

```python
class PMTicketingMixin:
    """Mixin for PM ticket operations"""
    
    def __init__(self):
        self.ticket_manager = TicketManager()
    
    def create_bug_ticket(self, title, description, error_details):
        """Create bug ticket with orchestration"""
        return self.ticket_manager.create_ticket(
            ticket_type="BUG",
            title=title,
            description=description,
            priority="critical" if "production" in description.lower() else "high",
            tags=["bug"],
            metadata={
                "error_message": error_details,
                "stack_trace": self._extract_stack_trace(error_details)
            },
            orchestration={
                "agents_required": ["Research Agent", "Engineer Agent", "QA Agent"],
                "workflow": "research -> fix -> test"
            }
        )
    
    def create_feature_ticket(self, title, description, requirements):
        """Create feature ticket with planning"""
        return self.ticket_manager.create_ticket(
            ticket_type="FEAT",
            title=title,
            description=description,
            priority="high",
            tags=["feature"],
            metadata={
                "requirements": requirements,
                "acceptance_criteria": self._extract_criteria(requirements)
            },
            orchestration={
                "agents_required": ["Research Agent", "Engineer Agent", "Documentation Agent", "QA Agent"],
                "workflow": "research -> design -> implement -> document -> test"
            }
        )
    
    def update_ticket_from_agent(self, ticket_id, agent_name, update):
        """Update ticket with agent progress"""
        ticket = self.ticket_manager.load_ticket(ticket_id)
        if not ticket:
            return None
        
        ticket["agent_updates"].append({
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "action": update["action"],
            "details": update["details"]
        })
        
        # Update status based on agent completion
        if update.get("completed"):
            ticket["status"] = self._next_status(ticket, agent_name)
        
        self.ticket_manager.save_ticket(ticket)
        return ticket
```

### Agent Integration

```python
class AgentTicketingMixin:
    """Mixin for agent ticket operations"""
    
    def get_ticket_context(self, ticket_id):
        """Get ticket context for agent work"""
        manager = TicketManager()
        ticket = manager.load_ticket(ticket_id)
        
        if not ticket:
            return None
        
        # Extract relevant context for agent
        return {
            "ticket_id": ticket["id"],
            "title": ticket["title"],
            "description": ticket["description"],
            "priority": ticket["priority"],
            "tags": ticket["tags"],
            "metadata": ticket.get("metadata", {}),
            "previous_updates": [
                u for u in ticket.get("agent_updates", [])
                if u["agent"] != self.agent_name
            ]
        }
    
    def update_ticket_progress(self, ticket_id, action, details, completed=False):
        """Update ticket with agent progress"""
        manager = TicketManager()
        ticket = manager.load_ticket(ticket_id)
        
        if not ticket:
            return None
        
        update = {
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        
        ticket["agent_updates"].append(update)
        
        if completed:
            # Mark agent's portion as complete
            update["completed"] = True
        
        manager.save_ticket(ticket)
        return ticket
```

## Advanced Usage

### Batch Operations

```python
def batch_update_tickets(criteria, updates):
    """Update multiple tickets matching criteria"""
    manager = TicketManager()
    updated = []
    
    for ticket in manager.list_tickets(**criteria):
        for key, value in updates.items():
            if key == "add_tags":
                ticket["tags"].extend(value)
            elif key == "remove_tags":
                ticket["tags"] = [t for t in ticket["tags"] if t not in value]
            else:
                ticket[key] = value
        
        manager.save_ticket(ticket)
        updated.append(ticket["id"])
    
    return updated

# Example: Close all QA-approved bugs
batch_update_tickets(
    criteria={"status": "in_progress", "tags": ["bug", "qa-approved"]},
    updates={"status": "closed", "resolution": "fixed"}
)
```

### Ticket Analytics

```python
def ticket_analytics():
    """Generate ticket statistics"""
    manager = TicketManager()
    all_tickets = manager.list_tickets()
    
    stats = {
        "total": len(all_tickets),
        "by_status": {},
        "by_priority": {},
        "by_type": {},
        "avg_resolution_time": None,
        "agent_workload": {}
    }
    
    resolution_times = []
    
    for ticket in all_tickets:
        # Status distribution
        status = ticket["status"]
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # Priority distribution
        priority = ticket["priority"]
        stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
        
        # Type distribution
        ticket_type = ticket["id"].split("-")[0]
        stats["by_type"][ticket_type] = stats["by_type"].get(ticket_type, 0) + 1
        
        # Agent workload
        for update in ticket.get("agent_updates", []):
            agent = update["agent"]
            stats["agent_workload"][agent] = stats["agent_workload"].get(agent, 0) + 1
        
        # Resolution time
        if ticket["status"] == "closed":
            created = datetime.fromisoformat(ticket["created_at"])
            updated = datetime.fromisoformat(ticket["updated_at"])
            resolution_times.append((updated - created).total_seconds() / 3600)
    
    if resolution_times:
        stats["avg_resolution_time"] = sum(resolution_times) / len(resolution_times)
    
    return stats
```

### Ticket Relationships

```python
def link_tickets(parent_id, child_id, relationship="blocks"):
    """Create relationships between tickets"""
    manager = TicketManager()
    
    parent = manager.load_ticket(parent_id)
    child = manager.load_ticket(child_id)
    
    if not parent or not child:
        return False
    
    # Add to parent
    if "linked_tickets" not in parent:
        parent["linked_tickets"] = []
    parent["linked_tickets"].append({
        "ticket_id": child_id,
        "relationship": relationship
    })
    
    # Add to child
    if "linked_tickets" not in child:
        child["linked_tickets"] = []
    child["linked_tickets"].append({
        "ticket_id": parent_id,
        "relationship": f"blocked_by" if relationship == "blocks" else "related_to"
    })
    
    manager.save_ticket(parent)
    manager.save_ticket(child)
    return True
```

## Error Handling

### Common Errors and Solutions

```python
def safe_ticket_operation(operation, *args, **kwargs):
    """Wrapper for safe ticket operations"""
    try:
        return operation(*args, **kwargs)
    except FileNotFoundError:
        print(f"Ticket not found: {args[0] if args else 'unknown'}")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid ticket format: {e}")
        return None
    except PermissionError:
        print("Permission denied accessing ticket files")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Usage
ticket = safe_ticket_operation(manager.load_ticket, "BUG-2025-001")
```

## Performance Considerations

### Caching for Large Ticket Volumes

```python
class CachedTicketManager(TicketManager):
    """Ticket manager with caching for performance"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def load_ticket(self, ticket_id):
        """Load ticket with caching"""
        cache_key = f"ticket:{ticket_id}"
        cached = self._cache.get(cache_key)
        
        if cached and (datetime.now() - cached["timestamp"]).seconds < self._cache_ttl:
            return cached["data"]
        
        ticket = super().load_ticket(ticket_id)
        if ticket:
            self._cache[cache_key] = {
                "data": ticket,
                "timestamp": datetime.now()
            }
        
        return ticket
    
    def save_ticket(self, ticket):
        """Save ticket and invalidate cache"""
        super().save_ticket(ticket)
        cache_key = f"ticket:{ticket['id']}"
        if cache_key in self._cache:
            del self._cache[cache_key]
```

## Migration Guide

### Migrating from Old Ticketing System

```python
def migrate_legacy_tickets(legacy_dir, ticket_manager):
    """Migrate tickets from legacy format"""
    legacy_path = Path(legacy_dir)
    migrated = 0
    
    for old_file in legacy_path.glob("*.txt"):
        # Parse legacy format
        with open(old_file, 'r') as f:
            lines = f.readlines()
        
        # Extract data (example format)
        title = lines[0].strip()
        description = "\n".join(lines[1:]).strip()
        
        # Create new ticket
        ticket = ticket_manager.create_ticket(
            ticket_type="LEGACY",
            title=title,
            description=description,
            tags=["migrated"],
            metadata={"legacy_file": old_file.name}
        )
        
        migrated += 1
        print(f"Migrated: {old_file.name} -> {ticket['id']}")
    
    return migrated
```

## Summary

The ticketing API provides flexible options for ticket management:

1. **ai_trackdown module** for standard operations
2. **File-based API** for custom requirements
3. **Integration patterns** for PM and agents
4. **Advanced features** for analytics and relationships
5. **Performance optimizations** for scale

Choose the appropriate API based on your specific needs:
- Use ai_trackdown for standard task management
- Use file-based API for custom workflows
- Implement caching for high-volume scenarios
- Add error handling for production robustness

---

*Technical Reference by Documentation Agent*