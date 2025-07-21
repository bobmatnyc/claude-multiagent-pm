# QA Agent Delegation Template

## Agent Overview
- **Nickname**: QA
- **Type**: qa
- **Role**: Quality assurance, testing, and validation
- **Authority**: ALL testing and validation decisions

## Delegation Template

```
**QA Agent**: [Testing/validation task]

TEMPORAL CONTEXT: Today is [date]. Consider release schedules and quality gates.

**Task**: [Specific QA work]
- Execute test suites and validate functionality
- Perform integration and regression testing
- Validate code quality and standards
- Check for security vulnerabilities
- Ensure deployment readiness

**Authority**: ALL testing operations and quality decisions
**Expected Results**: Test results, quality metrics, and validation status
**Ticket Reference**: [ISS-XXXX if applicable]
**Progress Reporting**: Report test results, coverage, and quality issues
```

## Example Usage

### Comprehensive Test Suite Execution
```
**QA Agent**: Execute full regression test suite

TEMPORAL CONTEXT: Today is 2025-07-20. Pre-release validation required.

**Task**: Run comprehensive test validation
- Execute unit tests across all modules
- Run integration test suite
- Perform E2E testing scenarios
- Check code coverage metrics
- Validate performance benchmarks
- Run security vulnerability scans

**Authority**: ALL testing and validation operations
**Expected Results**: Complete test report with pass/fail status
**Ticket Reference**: ISS-0456
**Progress Reporting**: Report failures, coverage %, and recommendations
```

### Feature Validation
```
**QA Agent**: Validate new authentication system

TEMPORAL CONTEXT: Today is 2025-07-20. Feature ready for QA.

**Task**: Thoroughly test authentication implementation
- Test all auth endpoints (login, logout, refresh)
- Validate JWT token generation and expiry
- Test error scenarios and edge cases
- Verify security best practices
- Check integration with existing systems
- Validate performance under load

**Authority**: ALL testing and quality decisions
**Expected Results**: Feature validation report with findings
**Ticket Reference**: ISS-0234
**Progress Reporting**: Report critical issues and test coverage
```

## Integration Points

### With Engineer Agent
- Tests code implementations
- Reports bugs for fixes
- Validates bug fixes

### With Security Agent
- Performs security testing
- Validates security fixes

### With Ops Agent
- Validates deployment readiness
- Tests in deployment environments

### With Documentation Agent
- Verifies documentation accuracy
- Tests code examples

## Progress Reporting Format

```
✅ QA Agent Progress Report
- Task: [current testing focus]
- Status: [in progress/completed/blocked]
- Test Results:
  * Passed: [X tests]
  * Failed: [Y tests]
  * Skipped: [Z tests]
- Coverage: [XX%]
- Critical Issues:
  * [issue 1 with severity]
  * [issue 2 with severity]
- Quality Metrics:
  * Code Quality: [score]
  * Performance: [status]
  * Security: [status]
- Recommendations: [testing recommendations]
- Blockers: [if any]
```

## Testing Categories

### Unit Testing
- Individual component validation
- Function-level testing
- Mock dependencies

### Integration Testing
- Component interaction testing
- API endpoint validation
- Database integration checks

### E2E Testing
- User workflow validation
- Full system testing
- Browser/client testing

### Performance Testing
- Load testing
- Stress testing
- Memory profiling
- Response time validation

### Security Testing
- Vulnerability scanning
- Penetration testing
- Authentication/authorization checks
- Input validation testing

## Error Handling

Common issues and responses:
- **Test environment issues**: Coordinate with Ops Agent
- **Flaky tests**: Investigate and stabilize
- **Missing test coverage**: Request Engineer Agent to add tests
- **Performance degradation**: Profile and report to Engineer Agent
- **Security vulnerabilities**: Escalate to Security Agent
- **Breaking changes**: Document impact and escalate