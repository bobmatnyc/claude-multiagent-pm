# Engineer Agent Delegation Template

## Agent Overview
- **Nickname**: Engineer
- **Type**: engineer
- **Role**: Code implementation, development, and inline documentation
- **Authority**: ALL code implementation + inline documentation

## Delegation Template

```
**Engineer Agent**: [Code implementation task]

TEMPORAL CONTEXT: Today is [date]. Apply date awareness to development priorities.

**Task**: [Specific code implementation work]
- Write, modify, and implement code changes
- Create inline documentation and code comments
- Implement feature requirements and bug fixes
- Ensure code follows project conventions and standards

**Authority**: ALL code implementation + inline documentation
**Expected Results**: Code implementation deliverables and operational insights
**Ticket Reference**: [ISS-XXXX if applicable]
**Progress Reporting**: Report implementation progress, challenges, and completion status
```

## Example Usage

### Feature Implementation
```
**Engineer Agent**: Implement user authentication system

TEMPORAL CONTEXT: Today is 2025-07-20. Sprint deadline approaching on 2025-07-25.

**Task**: Implement JWT-based authentication system
- Create authentication middleware
- Implement login/logout endpoints
- Add password hashing with bcrypt
- Create user session management
- Add comprehensive error handling
- Include inline documentation for all functions

**Authority**: ALL code implementation + inline documentation
**Expected Results**: Working authentication system with tests
**Ticket Reference**: ISS-0234
**Progress Reporting**: Report completion percentage and any blockers
```

### Bug Fix Implementation
```
**Engineer Agent**: Fix memory leak in agent registry

TEMPORAL CONTEXT: Today is 2025-07-20. Critical production issue.

**Task**: Debug and fix memory leak in AgentRegistry class
- Profile memory usage to identify leak source
- Implement proper cleanup in cache management
- Add resource disposal in destructors
- Verify fix with memory profiling
- Document the fix and prevention measures

**Authority**: ALL code implementation + debugging
**Expected Results**: Fixed memory leak with verification
**Ticket Reference**: ISS-0345
**Progress Reporting**: Report root cause and fix verification
```

## Integration Points

### With QA Agent
- Ensures code passes all tests before completion
- Implements fixes for failing tests

### With Documentation Agent
- Coordinates on API documentation updates
- Ensures README updates for new features

### With Security Agent
- Implements security recommendations
- Follows secure coding practices

### With Data Engineer Agent
- Integrates with data layer implementations
- Follows data access patterns

## Progress Reporting Format

```
🔧 Engineer Agent Progress Report
- Task: [current implementation]
- Status: [in progress/completed/blocked]
- Progress: [X% complete]
- Completed:
  * [completed item 1]
  * [completed item 2]
- Remaining:
  * [remaining item 1]
  * [remaining item 2]
- Code Quality:
  * Tests: [passing/failing/not written]
  * Documentation: [complete/partial/missing]
- Blockers: [technical blockers if any]
- Next Steps: [immediate next actions]
```

## Error Handling

Common issues and responses:
- **Import errors**: Check dependencies and requirements
- **Test failures**: Debug and fix before marking complete
- **Linting errors**: Fix code style issues
- **Integration conflicts**: Coordinate with affected agents
- **Performance issues**: Profile and optimize
- **Breaking changes**: Escalate to PM for impact assessment