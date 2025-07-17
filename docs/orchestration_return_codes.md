# Orchestration Return Codes

## Overview

The BackwardsCompatibleOrchestrator now returns a tuple of `(result_dict, return_code)` from all orchestration methods. This provides better error handling and status tracking for orchestration operations.

## Return Code Values

| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Operation completed successfully |
| 1 | GENERAL_FAILURE | General operation failure |
| 2 | TIMEOUT | Operation timed out |
| 3 | CONTEXT_FILTERING_ERROR | Error during context filtering |
| 4 | AGENT_NOT_FOUND | Requested agent not found |
| 5 | MESSAGE_BUS_ERROR | Error in message bus routing |

**Note**: Unlike Unix conventions, 0 represents success (as requested).

## API Changes

### Main Delegation Method

```python
# Before (returns only dict)
result = await orchestrator.delegate_to_agent(
    agent_type="engineer",
    task_description="Implement feature"
)

# After (returns tuple)
result, return_code = await orchestrator.delegate_to_agent(
    agent_type="engineer", 
    task_description="Implement feature"
)
```

### Convenience Function

```python
from claude_pm.orchestration.backwards_compatible_orchestrator import delegate_with_compatibility

result, return_code = await delegate_with_compatibility(
    agent_type="engineer",
    task_description="Implement feature"
)
```

## Usage Examples

### Basic Error Handling

```python
orchestrator = BackwardsCompatibleOrchestrator()

result, return_code = await orchestrator.delegate_to_agent(
    agent_type="engineer",
    task_description="Implement new feature"
)

if return_code == ReturnCode.SUCCESS:
    print("Task completed successfully")
    print(f"Results: {result.get('results', 'No results')}")
elif return_code == ReturnCode.TIMEOUT:
    print("Task timed out")
elif return_code == ReturnCode.AGENT_NOT_FOUND:
    print(f"Agent '{agent_type}' not found")
else:
    print(f"Task failed with code: {return_code}")
```

### Checking Specific Errors

```python
from claude_pm.orchestration.backwards_compatible_orchestrator import ReturnCode

result, return_code = await orchestrator.delegate_to_agent(
    agent_type="researcher",
    task_description="Research best practices",
    timeout_seconds=30
)

# Check for specific errors
if return_code == ReturnCode.CONTEXT_FILTERING_ERROR:
    # Handle context filtering issues
    print("Context was too large or couldn't be filtered properly")
elif return_code == ReturnCode.MESSAGE_BUS_ERROR:
    # Handle message routing issues
    print("Internal routing error occurred")
```

### Integration with Metrics

Return codes are automatically tracked in orchestration metrics:

```python
# After running several orchestrations
metrics = orchestrator.get_orchestration_metrics()

print(f"Total orchestrations: {metrics['total_orchestrations']}")
print(f"Success rate: {metrics['success_rate']:.1f}%")
print(f"Failures by code: {metrics['failure_by_code']}")
# Output: {'TIMEOUT': 2, 'AGENT_NOT_FOUND': 1}
```

## Backwards Compatibility Note

The return code is also included in the result dictionary for compatibility:

```python
result, return_code = await orchestrator.delegate_to_agent(...)

# Return code is available in both places
assert result["return_code"] == return_code
```

This allows gradual migration of existing code that expects only a dictionary result.

## Implementation Details

1. **Return codes are determined throughout the orchestration flow**:
   - During agent discovery
   - During context filtering
   - During message bus routing
   - During subprocess delegation

2. **Fallback behavior preserves error codes**:
   - If local orchestration fails, the error code is preserved
   - Subprocess fallback may succeed but original error is tracked

3. **Metrics integration**:
   - All return codes are tracked in metrics
   - Success/failure rates calculated automatically
   - Failure breakdown by code available

## Testing

Unit tests are provided in `tests/test_orchestration_return_codes.py` to verify:
- Correct return codes for each error scenario
- Metrics tracking of return codes
- API compatibility
- Error propagation through fallback mechanisms