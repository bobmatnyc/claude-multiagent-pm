# Memory Monitoring for Task Tool Subprocesses

## Overview

The Claude PM Framework includes a comprehensive memory monitoring system designed to prevent memory exhaustion during Task Tool subprocess operations. This feature addresses the critical issue of subprocess memory leaks that can consume up to 8GB of system memory, causing system instability and crashes.

### Key Features

- **Real-time Memory Tracking**: Monitors memory usage of Task Tool subprocesses every 2 seconds
- **Multi-threshold Alerts**: Warning (1GB), Critical (2GB), and Hard Limit (4GB) thresholds
- **Automatic Abort**: Prevents system crashes by terminating runaway subprocesses
- **Detailed Logging**: Comprehensive memory usage logs for debugging and analysis
- **System Memory Checks**: Pre-flight checks before creating new subprocesses
- **Performance Metrics**: Tracks peak memory, duration, and warning history

## How It Works

### 1. Subprocess Creation

When a Task Tool subprocess is created, the memory monitoring system automatically:

1. Checks available system memory (requires at least 1GB free)
2. Initializes monitoring for the subprocess
3. Records initial memory baseline
4. Starts async monitoring loop

### 2. Continuous Monitoring

During subprocess execution:

```python
# Monitoring happens every 2 seconds
- Current memory usage is checked
- Peak memory is tracked
- Thresholds are evaluated
- Warnings are logged if exceeded
- Subprocess is aborted if hard limit is reached
```

### 3. Memory Thresholds

| Threshold | Default Value | Action |
|-----------|--------------|--------|
| Warning | 1024 MB (1GB) | Log warning, continue execution |
| Critical | 2048 MB (2GB) | Log critical warning, alert user |
| Hard Limit | 4096 MB (4GB) | Abort subprocess, prevent crash |

### 4. Subprocess Termination

When a subprocess completes or is aborted:

1. Final memory statistics are collected
2. Peak memory usage is recorded
3. Warnings and abort status are logged
4. Memory tracking is cleaned up

## Configuration

### Environment Variables

```bash
# Override default memory thresholds
export CLAUDE_PM_MEMORY_WARNING_MB=1024    # Warning threshold (default: 1GB)
export CLAUDE_PM_MEMORY_CRITICAL_MB=2048   # Critical threshold (default: 2GB)
export CLAUDE_PM_MEMORY_MAX_MB=4096        # Hard limit (default: 4GB)

# Disable memory monitoring (not recommended)
export CLAUDE_PM_DISABLE_MEMORY_MONITOR=false
```

### TaskToolConfiguration

```python
from claude_pm.utils.task_tool_helper import TaskToolConfiguration

config = TaskToolConfiguration(
    # Memory monitoring settings
    enable_memory_monitoring=True,     # Enable/disable monitoring
    memory_warning_mb=1024,           # Warning threshold
    memory_critical_mb=2048,          # Critical threshold
    memory_max_mb=4096,               # Hard limit
    abort_on_memory_limit=True        # Auto-abort on limit
)
```

### Per-Subprocess Configuration

```python
from claude_pm.monitoring import MemoryThresholds

# Custom thresholds for specific subprocess
thresholds = MemoryThresholds(
    warning_mb=512,    # Lower warning for lightweight tasks
    critical_mb=1024,  # Lower critical threshold
    max_mb=2048        # Lower hard limit
)
```

## Log Files and Monitoring

### Log Locations

Memory monitoring creates the following log files:

```
.claude-pm/logs/memory/
├── memory-alerts.log      # Real-time alerts and warnings
├── subprocess-stats.jsonl # Per-subprocess statistics
└── memory-monitor.log     # System-wide memory tracking
```

### Alert Log Format

```json
{
  "timestamp": "2025-07-20T10:30:45.123456",
  "level": "WARNING",
  "subprocess_id": "engineer_abc123",
  "message": "WARNING: Memory exceeded 1024MB at 1156.3MB",
  "system_memory": {
    "total_mb": 16384.0,
    "available_mb": 4096.5,
    "used_mb": 12287.5,
    "percent": 75.0
  }
}
```

### Subprocess Statistics Format

```json
{
  "subprocess_id": "researcher_xyz789",
  "memory_stats": {
    "start_mb": 256.4,
    "peak_mb": 1892.7,
    "end_mb": 512.3,
    "duration_seconds": 45.2,
    "warnings": [
      "WARNING: Memory exceeded 1024MB at 1156.3MB"
    ],
    "aborted": false
  },
  "timestamp": "2025-07-20T10:31:20.456789"
}
```

## Integration with Task Tool

The memory monitoring system is fully integrated with Task Tool operations:

### Automatic Monitoring

```python
# Memory monitoring starts automatically
helper = TaskToolHelper()
result = helper.create_agent_subprocess(
    agent_type="engineer",
    task_description="Implement feature X"
)

# Monitor provides real-time status
memory_mb, status = helper.check_subprocess_memory(subprocess_id)
# Returns: (1523.4, "WARNING")
```

### Pre-flight Checks

```python
# System checks before creating subprocess
can_create, message = monitor.can_create_subprocess()
if not can_create:
    print(f"Cannot create subprocess: {message}")
    # "Insufficient memory: only 512.3MB available (need at least 1GB)"
```

### Abort Detection

```python
# Check if subprocess should be aborted
if monitor.should_abort(subprocess_id):
    # Subprocess exceeded memory limit
    # Cleanup and error handling
    pass
```

## Troubleshooting

### Common Issues

#### 1. Subprocess Aborted Due to Memory

**Symptoms**: Task Tool subprocess terminates unexpectedly with memory error

**Solution**:
- Check memory alerts log for specific threshold exceeded
- Reduce task complexity or break into smaller subtasks
- Increase memory thresholds if system has sufficient RAM
- Optimize agent operations to use less memory

#### 2. Cannot Create New Subprocess

**Symptoms**: "Insufficient memory" error when creating subprocess

**Solution**:
- Check system memory with `free -h` or Activity Monitor
- Close unnecessary applications
- Wait for current subprocesses to complete
- Restart the framework to clear any memory leaks

#### 3. Frequent Memory Warnings

**Symptoms**: Regular warnings in logs but no aborts

**Solution**:
- Review subprocess statistics to identify memory-hungry operations
- Consider adjusting warning threshold if false positives
- Optimize agent code for memory efficiency
- Monitor for memory leak patterns

### Debug Commands

```bash
# View current memory status
python -c "from claude_pm.monitoring import get_memory_monitor; print(get_memory_monitor().get_memory_status())"

# Check subprocess memory usage
python -c "from claude_pm.monitoring import get_subprocess_memory_monitor; print(get_subprocess_memory_monitor().get_all_subprocess_stats())"

# View recent memory alerts
tail -f .claude-pm/logs/memory/memory-alerts.log

# Analyze subprocess statistics
jq . .claude-pm/logs/memory/subprocess-stats.jsonl | less
```

## Best Practices

### 1. Resource Planning

- Allocate sufficient system memory (minimum 8GB recommended)
- Monitor baseline memory usage before heavy operations
- Plan for peak usage during multi-agent coordination

### 2. Task Design

- Break large tasks into smaller, memory-efficient subtasks
- Avoid loading large datasets entirely into memory
- Use streaming processing where possible
- Clean up temporary data during long-running tasks

### 3. Monitoring Strategy

- Set up alerts for critical memory events
- Review subprocess statistics regularly
- Identify and optimize memory-intensive operations
- Use memory profiling for custom agents

### 4. Configuration Tuning

- Adjust thresholds based on system capabilities
- Lower limits for development/testing environments
- Higher limits for production systems with more RAM
- Consider per-agent memory budgets

## Performance Impact

The memory monitoring system has minimal performance overhead:

- **CPU Usage**: < 0.1% for monitoring operations
- **Memory Overhead**: ~10MB for monitoring infrastructure
- **Latency**: No impact on subprocess execution speed
- **I/O**: Minimal, with buffered log writes

## Future Enhancements

Planned improvements to the memory monitoring system:

1. **Predictive Analysis**: ML-based memory usage prediction
2. **Dynamic Thresholds**: Auto-adjust based on system load
3. **Memory Profiling**: Detailed memory allocation tracking
4. **Dashboard Integration**: Real-time web-based monitoring
5. **Alert Webhooks**: Integration with monitoring services