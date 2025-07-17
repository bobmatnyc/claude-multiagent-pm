# Orchestration Logging Documentation

## Overview

The BackwardsCompatibleOrchestrator now includes comprehensive structured logging for all agent delegations, providing rich observability into the orchestration system's behavior, performance, and error handling.

## Return Codes

The system uses the following return codes to indicate operation status:

| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Operation completed successfully |
| 1 | GENERAL_FAILURE | General/unspecified failure |
| 2 | TIMEOUT | Operation timed out |
| 3 | CONTEXT_FILTERING_ERROR | Error during context filtering |
| 4 | AGENT_NOT_FOUND | Requested agent type not found |
| 5 | MESSAGE_BUS_ERROR | Error in message bus routing |

## Structured Log Events

### 1. agent_delegation_start

Logged when an agent delegation begins.

**Fields:**
- `agent_type`: Type of agent being delegated to
- `task_id`: Unique 8-character task identifier
- `task_description`: First 100 characters of the task
- `priority`: Task priority (low/medium/high)
- `timestamp`: Unix timestamp
- `requirements_count`: Number of requirements
- `deliverables_count`: Number of deliverables

### 2. orchestration_mode_selected

Logged after determining which orchestration mode to use.

**Fields:**
- `mode`: Selected mode (local/subprocess)
- `fallback_reason`: Reason if fallback occurred
- `decision_time_ms`: Time taken to decide mode
- `task_id`: Task identifier

### 3. context_filtered

Logged after context filtering (local orchestration only).

**Fields:**
- `agent_type`: Agent type
- `task_id`: Task identifier
- `filter_time_ms`: Time taken to filter context
- `original_tokens`: Original context size in tokens
- `filtered_tokens`: Filtered context size in tokens
- `reduction_percent`: Percentage reduction in tokens
- `files_after_filter`: Number of files after filtering

### 4. message_bus_routing_complete

Logged after message bus routing (local orchestration only).

**Fields:**
- `agent_type`: Agent type
- `task_id`: Task identifier
- `routing_time_ms`: Time taken for routing
- `response_status`: Response status from message bus
- `return_code`: Operation return code

### 5. agent_delegation_end

Logged when agent delegation completes.

**Fields:**
- `agent_type`: Agent type
- `task_id`: Task identifier
- `duration_ms`: Total delegation duration
- `execution_time_ms`: Execution time (excluding decision)
- `return_code`: Final return code
- `mode`: Orchestration mode used
- `context_tokens_original`: Original context size
- `context_tokens_filtered`: Filtered context size
- `token_reduction_percent`: Token reduction percentage
- `timestamp`: Unix timestamp

### 6. Error Events

Various error events with specific context:
- `agent_not_found`: Agent type not found in registry
- `component_initialization_failed`: Orchestration component failed
- `emergency_fallback_triggered`: Emergency fallback initiated
- `agent_delegation_timeout`: Operation timed out
- `agent_delegation_error`: General delegation error

## Performance Metrics

The orchestrator tracks comprehensive metrics accessible via `get_orchestration_metrics()`:

```python
{
    "total_orchestrations": 100,
    "local_orchestrations": 80,
    "subprocess_orchestrations": 20,
    "success_count": 95,
    "success_rate": 95.0,
    "failure_by_code": {
        "AGENT_NOT_FOUND": 3,
        "TIMEOUT": 2
    },
    "average_decision_time_ms": 2.5,
    "average_execution_time_ms": 150.0,
    "average_context_filter_time_ms": 15.0,
    "average_token_reduction_percent": 85.0,
    "agent_type_distribution": {
        "engineer": 40,
        "documentation": 30,
        "qa": 30
    },
    "recent_metrics": [...],  # Last 10 delegations
    "fallback_reasons": [...]  # Unique fallback reasons
}
```

## Integration with JSON Logging

The logging is designed to work with JSON formatters for structured log aggregation:

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        
        # Add all extra fields
        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith('_'):
                log_obj[key] = value
                
        return json.dumps(log_obj)
```

## Usage Examples

### Monitoring Token Reduction

```python
# Filter logs for context filtering events
grep "context_filtered" logs.json | jq '.reduction_percent' | stats
```

### Tracking Error Rates

```python
# Count failures by return code
grep "agent_delegation_end" logs.json | jq '.return_code' | sort | uniq -c
```

### Performance Analysis

```python
# Average execution time by agent type
grep "agent_delegation_end" logs.json | \
  jq -r '[.agent_type, .execution_time_ms] | @csv' | \
  awk -F, '{sum[$1]+=$2; count[$1]++} END {for (a in sum) print a, sum[a]/count[a]}'
```

## Best Practices

1. **Task ID Tracking**: Use the task_id field to correlate all events for a single delegation
2. **Return Code Monitoring**: Alert on non-zero return codes
3. **Token Reduction**: Monitor token_reduction_percent to ensure context filtering is effective
4. **Performance Baselines**: Establish baselines for decision_time_ms and execution_time_ms
5. **Error Patterns**: Look for patterns in failure_by_code to identify systemic issues

## Configuration

The logging uses Python's standard logging framework:

```python
# Set log level
logger = logging.getLogger('claude_pm.orchestration')
logger.setLevel(logging.DEBUG)  # For detailed logs
logger.setLevel(logging.INFO)   # For production

# Add custom handler
handler = YourLogHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
```