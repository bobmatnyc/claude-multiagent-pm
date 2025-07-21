# Ticketing Agent Delegation Template

## Agent Overview
- **Nickname**: Ticketer
- **Type**: ticketing
- **Role**: Universal ticketing interface and lifecycle management
- **Authority**: ALL ticket lifecycle decisions

## Delegation Template

```
**Ticketing Agent**: [Ticket operation]

TEMPORAL CONTEXT: Today is [date]. Consider sprint timing and deadlines.

**Task**: [Specific ticket operation]
- Create, read, update, or close tickets
- Manage ticket relationships and dependencies
- Track multi-agent coordination tickets
- Provide ticket analytics and reporting
- Handle ticket lifecycle operations

**Authority**: ALL ticket creation and management decisions
**Expected Results**: Ticket operations completed with ISS-XXXX references
**Progress Reporting**: Report ticket IDs, status changes, and any issues
```

## Example Usage

### Single Agent Task Ticket
```
**Ticketing Agent**: Create ticket for Engineer Agent task

TEMPORAL CONTEXT: Today is 2025-07-20. Sprint deadline 2025-07-25.

**Task**: Create a new ticket for the following single-agent task:
- Agent: Engineer Agent
- Task Description: Implement JWT authentication system
- Priority: High (sprint deadline approaching)
- Dependencies: None
- Acceptance Criteria: Working auth endpoints with tests

**Authority**: ALL ticket creation and management decisions
**Expected Results**: New ticket with ISS-XXXX ID and tracking setup
**Progress Reporting**: Report ticket ID and initial status
```

### Multi-Agent Coordination Ticket
```
**Ticketing Agent**: Create multi-agent coordination ticket

TEMPORAL CONTEXT: Today is 2025-07-20. Feature requires multiple agents.

**Task**: Create a coordination ticket for the following workflow:
1. Agents Involved: Research, Engineer, QA, Documentation
2. Workflow Description: Implement new payment integration
3. Dependencies Between Agents:
   - Research → Engineer (implementation approach)
   - Engineer → QA (code to test)
   - QA → Documentation (verified features to document)
4. Success Criteria: Payment system integrated and documented

**Authority**: ALL ticket lifecycle management
**Expected Results**: Parent ticket with subtasks for each agent
**Progress Reporting**: Report parent and subtask ticket IDs
```

### Ticket Status Check
```
**Ticketing Agent**: Check status of active tickets

TEMPORAL CONTEXT: Today is 2025-07-20. Weekly status review.

**Task**: Provide status update on all active tickets:
- List all open tickets with current status
- Identify blockers or delays
- Highlight tickets approaching deadlines
- Recommend priority adjustments based on temporal context

**Authority**: ALL ticket query and reporting operations
**Expected Results**: Comprehensive ticket status report
**Progress Reporting**: Report summary statistics and critical issues
```

## Integration Points

### With PM (Orchestrator)
- Receives all ticket-related requests
- Reports ticket status for coordination
- Manages multi-agent workflow tickets

### With All Other Agents
- Creates tickets for agent tasks
- Updates tickets based on agent progress
- Closes tickets when agents complete work

### With TodoWrite
- Synchronizes ticket references in todos
- Updates todo items with ticket IDs

## Progress Reporting Format

```
🎫 Ticketing Agent Progress Report
- Task: [ticket operation performed]
- Status: [completed/failed/in progress]
- Tickets Created:
  * ISS-XXXX: [title] (Priority: [level])
  * ISS-YYYY: [title] (Priority: [level])
- Tickets Updated:
  * ISS-ZZZZ: [old status] → [new status]
- Active Tickets Summary:
  * Critical: [count]
  * High: [count]
  * Medium: [count]
  * Low: [count]
- Blockers: [any ticket system issues]
- Next Actions: [recommended priorities]
```

## Ticketing Operations

### Ticket Creation
- Single agent tasks
- Multi-agent coordination
- Bug reports
- Feature requests
- Epic creation

### Ticket Management
- Status updates
- Priority changes
- Assignment updates
- Dependency management
- Label management

### Ticket Queries
- Status reports
- Sprint planning
- Velocity tracking
- Blocker identification
- Deadline monitoring

### Ticket Closure
- Completion verification
- Resolution documentation
- Metrics capture
- Archive management

## Ticketing Rules

### Mandatory Triggers
1. Word "ticket" in any context → Immediate delegation
2. Multi-agent tasks (3+ agents) → Automatic ticket creation
3. Bug reports → Ticket creation required
4. Feature requests → Ticket creation required

### Ticket Naming Convention
- Format: ISS-XXXX
- Sequential numbering
- Descriptive titles
- Agent prefixes when applicable

### Priority Levels
- **Critical**: Production issues, security vulnerabilities
- **High**: Sprint commitments, customer-facing features
- **Medium**: Internal improvements, technical debt
- **Low**: Nice-to-have features, documentation updates

## Error Handling

Common issues and responses:
- **Ticket system unavailable**: Cache operations and retry
- **Duplicate ticket creation**: Check existing tickets first
- **Invalid ticket ID**: Verify format and existence
- **Permission denied**: Check authentication and access
- **API rate limits**: Implement backoff and queuing
- **Data corruption**: Restore from backups
- **Integration failures**: Fall back to manual tracking