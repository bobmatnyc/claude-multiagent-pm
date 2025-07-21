# Memory Monitoring Quick Reference

## Essential Commands

### Check System Memory
```bash
python3 -c "from claude_pm.monitoring import get_memory_monitor; import json; print(json.dumps(get_memory_monitor().get_memory_status(), indent=2))"
```

### View Active Subprocesses
```bash
python3 -c "from claude_pm.monitoring import get_subprocess_memory_monitor; import json; print(json.dumps(get_subprocess_memory_monitor().get_all_subprocess_stats(), indent=2))"
```

### Monitor Alerts Real-time
```bash
tail -f .claude-pm/logs/memory/memory-alerts.log | jq '.'
```

## Environment Variables

```bash
export CLAUDE_PM_MEMORY_WARNING_MB=1024    # Default: 1GB
export CLAUDE_PM_MEMORY_CRITICAL_MB=2048   # Default: 2GB  
export CLAUDE_PM_MEMORY_MAX_MB=4096        # Default: 4GB
```

## Configuration in Code

```python
from claude_pm.utils.task_tool_helper import TaskToolConfiguration

config = TaskToolConfiguration(
    enable_memory_monitoring=True,
    memory_warning_mb=1024,
    memory_critical_mb=2048,
    memory_max_mb=4096,
    abort_on_memory_limit=True
)
```

## Log Files

```
.claude-pm/logs/memory/
├── memory-alerts.log      # Warnings and critical alerts
├── subprocess-stats.jsonl # Per-subprocess statistics
└── memory-monitor.log     # System-wide tracking
```

## Common Issues & Solutions

### Subprocess Aborted (Memory Limit)
```bash
# Check which limit was hit
grep "CRITICAL" .claude-pm/logs/memory/memory-alerts.log | tail -5

# Increase limits for high-memory systems
export CLAUDE_PM_MEMORY_MAX_MB=8192
```

### Insufficient Memory Error
```bash
# Check available memory
free -h  # Linux
vm_stat | grep "Pages free"  # macOS

# Close other applications or wait for subprocesses to complete
```

### Find Memory-Hungry Subprocesses
```bash
cat .claude-pm/logs/memory/subprocess-stats.jsonl | jq 'select(.memory_stats.peak_mb > 2000)'
```

## Performance Tips

1. **Break Large Tasks**: Split into smaller subtasks to reduce memory per subprocess
2. **Monitor Peaks**: Review subprocess-stats.jsonl to identify optimization opportunities
3. **Adjust Thresholds**: Set based on your system's available RAM
4. **Clean Logs**: Rotate large log files to save disk space

## Emergency Commands

```bash
# Stop all subprocesses
pkill -f "claude-pm"

# Clear memory logs
rm -f .claude-pm/logs/memory/*.log

# Disable monitoring (temporary)
export CLAUDE_PM_DISABLE_MEMORY_MONITOR=true
```