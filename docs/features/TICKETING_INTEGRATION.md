# Claude PM Framework Ticketing Integration

**Last Updated**: 2025-07-21  
**Framework Version**: 1.4.0  
**ai-trackdown-pytools Version**: 1.1.0

## Overview

The Claude PM Framework integrates with `ai-trackdown-pytools` to provide comprehensive ticketing functionality for project management and multi-agent orchestration. This integration enables the PM to track work items, coordinate agent tasks, and maintain project visibility.

## Installation

The ticketing functionality is provided by the `ai-trackdown-pytools` package, which is automatically installed with Claude PM Framework:

```bash
# Included in standard installation
npm install -g @bobmatnyc/claude-multiagent-pm

# Verify installation
python -c "import ai_trackdown; print(ai_trackdown.__version__)"  # Should show 1.1.0+
```

## Architecture

### Ticketing System Design

The ticketing system uses a **file-based JSON storage** approach:

```
.claude-pm/
└── tickets/
    ├── BUG-2025-001.json
    ├── FEAT-2025-002.json
    └── DOC-2025-003.json
```

### Ticket Structure

Each ticket is stored as a JSON file with the following structure:

```json
{
  "id": "BUG-2025-001",
  "title": "Fix async import error in core service",
  "description": "Detailed description of the issue",
  "status": "open",  // open, in_progress, closed
  "priority": "critical",  // low, medium, high, critical
  "created_at": "2025-07-21T10:00:00",
  "updated_at": "2025-07-21T11:00:00",
  "reporter": "user@example.com",
  "assignee": "PM",
  "tags": ["bug", "core", "import-error"],
  "metadata": {
    // Custom fields for ticket-specific data
  },
  "orchestration": {
    "agents_required": ["Research Agent", "Engineer Agent", "QA Agent"],
    "workflow": "research -> fix -> test -> verify"
  },
  "agent_updates": [
    {
      "agent": "Research Agent",
      "timestamp": "2025-07-21T10:30:00",
      "action": "Completed root cause analysis",
      "details": "Found circular import in core service module"
    }
  ]
}
```

## PM Ticketing Workflows

### 1. Creating Tickets

The PM can create tickets programmatically based on user requests:

```python
# PM creates a bug ticket
import json
from pathlib import Path
from datetime import datetime

def create_ticket(ticket_type, title, description, priority="medium"):
    tickets_dir = Path("tasks")
    tickets_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate ticket ID
    ticket_id = f"{ticket_type.upper()}-{datetime.now().strftime('%Y')}-{get_next_number()}"
    
    ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "status": "open",
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "assignee": "PM",
        "tags": [ticket_type.lower()],
        "orchestration": determine_workflow(ticket_type)
    }
    
    # Save ticket
    with open(tickets_dir / f"{ticket_id}.json", 'w') as f:
        json.dump(ticket, f, indent=2)
    
    return ticket_id
```

### 2. Multi-Agent Orchestration

PM uses tickets to coordinate multi-agent workflows:

```markdown
**PM Orchestration for BUG-2025-001**

1. **Research Agent**: Investigate ImportError in core service
   - Task: Analyze import structure and identify root cause
   - Context: Error message and affected version from ticket
   - Expected: Root cause analysis and recommended fix

2. **Engineer Agent**: Implement fix for import error
   - Task: Fix unified_core_service import issue
   - Context: Research findings and ticket priority
   - Expected: Working code with proper imports

3. **QA Agent**: Verify import error is resolved
   - Task: Test claude-pm --version and all imports
   - Context: Original error and fix implementation
   - Expected: All tests passing, no import errors
```

### 3. Ticket Status Management

```python
# PM updates ticket status as work progresses
def update_ticket_status(ticket_id, new_status, agent=None, details=None):
    ticket_path = Path(f"tickets/{ticket_id}.json")
    
    with open(ticket_path, 'r') as f:
        ticket = json.load(f)
    
    ticket["status"] = new_status
    ticket["updated_at"] = datetime.now().isoformat()
    
    if agent and details:
        if "agent_updates" not in ticket:
            ticket["agent_updates"] = []
        
        ticket["agent_updates"].append({
            "agent": agent,
            "timestamp": datetime.now().isoformat(),
            "action": f"Updated status to {new_status}",
            "details": details
        })
    
    with open(ticket_path, 'w') as f:
        json.dump(ticket, f, indent=2)
```

## Agent Integration Patterns

### 1. Agent Context from Tickets

Agents receive ticket context through Task Tool delegation:

```markdown
**Engineer Agent**: Fix issue described in ticket BUG-2025-001

TEMPORAL CONTEXT: Today is 2025-07-21. Critical bug affecting production.

**Task**: 
1. Read ticket BUG-2025-001 for issue details
2. Implement fix for ImportError in core service
3. Update ticket with implementation details

**Context**: 
- Ticket ID: BUG-2025-001
- Priority: Critical
- Error: ImportError with unified_core_service
- Research findings: Circular import detected

**Authority**: Code implementation and bug fixes
**Expected Results**: Working fix with updated ticket status
```

### 2. Agent Progress Updates

Agents update tickets with their progress:

```python
# Agent updates ticket with progress
def agent_update_ticket(ticket_id, agent_name, action, details):
    ticket_path = Path(f"tickets/{ticket_id}.json")
    
    with open(ticket_path, 'r') as f:
        ticket = json.load(f)
    
    if "agent_updates" not in ticket:
        ticket["agent_updates"] = []
    
    ticket["agent_updates"].append({
        "agent": agent_name,
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details
    })
    
    ticket["updated_at"] = datetime.now().isoformat()
    
    with open(ticket_path, 'w') as f:
        json.dump(ticket, f, indent=2)
```

## Common Ticketing Patterns

### 1. Bug Fix Workflow

```json
{
  "orchestration": {
    "agents_required": ["Research Agent", "Engineer Agent", "QA Agent"],
    "workflow": "research -> fix -> test -> verify",
    "steps": [
      {"agent": "Research Agent", "task": "Analyze root cause"},
      {"agent": "Engineer Agent", "task": "Implement fix"},
      {"agent": "QA Agent", "task": "Verify resolution"}
    ]
  }
}
```

### 2. Feature Implementation Workflow

```json
{
  "orchestration": {
    "agents_required": ["Research Agent", "Engineer Agent", "Documentation Agent", "QA Agent"],
    "workflow": "research -> design -> implement -> document -> test",
    "steps": [
      {"agent": "Research Agent", "task": "Investigate requirements"},
      {"agent": "Engineer Agent", "task": "Design and implement"},
      {"agent": "Documentation Agent", "task": "Update documentation"},
      {"agent": "QA Agent", "task": "Test feature"}
    ]
  }
}
```

### 3. Documentation Update Workflow

```json
{
  "orchestration": {
    "agents_required": ["Documentation Agent"],
    "workflow": "document",
    "steps": [
      {"agent": "Documentation Agent", "task": "Update documentation"}
    ]
  }
}
```

## Practical Examples

### Example 1: PM Creating a Bug Ticket

```python
# User reports: "claude-pm --version is broken"

# PM creates ticket
ticket = create_ticket(
    ticket_type="bug",
    title="Fix claude-pm --version command error",
    description="Users report ImportError when running claude-pm --version",
    priority="critical"
)

# PM orchestrates fix
print(f"Created ticket {ticket['id']}")
print("Initiating multi-agent workflow...")
# Delegate to Research Agent first...
```

### Example 2: Reading Tickets for Context

```python
# PM lists open tickets
tickets_dir = Path("tasks")
open_tickets = []

for ticket_file in tickets_dir.glob("*.json"):
    with open(ticket_file, 'r') as f:
        ticket = json.load(f)
    if ticket["status"] == "open":
        open_tickets.append(ticket)

# Sort by priority
priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
open_tickets.sort(key=lambda t: priority_order.get(t["priority"], 4))

# Display for orchestration
for ticket in open_tickets:
    print(f"🎫 {ticket['id']}: {ticket['title']} ({ticket['priority']})")
```

### Example 3: Tracking Multi-Agent Progress

```python
# PM monitors ticket progress
def get_ticket_progress(ticket_id):
    ticket_path = Path(f"tickets/{ticket_id}.json")
    
    with open(ticket_path, 'r') as f:
        ticket = json.load(f)
    
    print(f"Ticket: {ticket['id']} - {ticket['title']}")
    print(f"Status: {ticket['status']}")
    print(f"Assigned: {ticket['assignee']}")
    
    if "agent_updates" in ticket:
        print("\nAgent Progress:")
        for update in ticket["agent_updates"]:
            print(f"  {update['timestamp']}: {update['agent']} - {update['action']}")
```

## Current Limitations

### 1. No CLI Commands
Currently, there are no built-in CLI commands for ticket operations. All operations must be done programmatically or through file manipulation.

**Workaround**: Create wrapper scripts or aliases:
```bash
# List tickets
alias pm-tickets="ls -la tickets/"

# View ticket
alias pm-ticket-show="cat tickets/"
```

### 2. No Search Functionality
Finding specific tickets requires manual file enumeration.

**Workaround**: Use grep or find commands:
```bash
# Find tickets by keyword
grep -r "import error" tickets/

# Find tickets by status
grep -l '"status": "open"' tickets/*.json
```

### 3. No Validation
Ticket IDs and required fields are not validated.

**Best Practice**: Implement validation in PM logic before creating tickets.

## Future Enhancements

### Planned CLI Commands
```bash
# Create ticket
claude-pm ticket create --type bug --priority high

# List tickets
claude-pm ticket list --status open

# Show ticket details
claude-pm ticket show BUG-2025-001

# Update ticket
claude-pm ticket update BUG-2025-001 --status closed
```

### Ticket Templates
Pre-defined templates for common scenarios:
- Bug report template
- Feature request template
- Documentation update template
- Security issue template

### Integration Features
- Link tickets to git commits
- Auto-create tickets from error logs
- Ticket-based sprint planning
- Time tracking per ticket

## Best Practices

### 1. Ticket Naming Convention
Use consistent prefixes:
- `BUG-YYYY-NNN` for bugs
- `FEAT-YYYY-NNN` for features
- `DOC-YYYY-NNN` for documentation
- `SEC-YYYY-NNN` for security issues

### 2. Priority Guidelines
- **Critical**: Production breaking, security vulnerabilities
- **High**: Major features, significant bugs
- **Medium**: Standard features, non-critical bugs
- **Low**: Nice-to-have features, minor issues

### 3. Workflow Definition
Always include orchestration data for multi-agent coordination:
```json
"orchestration": {
  "agents_required": ["Agent1", "Agent2"],
  "workflow": "step1 -> step2",
  "dependencies": ["ticket-id-1", "ticket-id-2"]
}
```

### 4. Progress Tracking
Encourage agents to update tickets with meaningful progress:
- Starting work on task
- Completed analysis/research
- Implementation complete
- Tests passing
- Documentation updated

## Conclusion

The ticketing integration with ai-trackdown-pytools provides a flexible foundation for PM orchestration and multi-agent coordination. While currently lacking some user conveniences like CLI commands, the system successfully enables:

1. **Ticket-based project management** through JSON storage
2. **Multi-agent orchestration** with defined workflows
3. **Progress tracking** through agent updates
4. **Context sharing** between PM and agents

The file-based approach allows for easy customization and extension while maintaining simplicity. Future enhancements will add CLI commands and additional features to improve the user experience.

---

*Documentation generated by Documentation Agent on 2025-07-21*