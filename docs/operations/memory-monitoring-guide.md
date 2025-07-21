# Memory Monitoring Operational Guide

## Quick Start

### Enable Memory Monitoring

Memory monitoring is enabled by default. To verify it's working:

```bash
# Check if monitoring is active
python -c "from claude_pm.monitoring import get_memory_monitor; print('Memory monitoring active')"

# View current system memory
python -c "from claude_pm.monitoring import get_memory_monitor; import json; print(json.dumps(get_memory_monitor().get_memory_status(), indent=2))"
```

### Monitor Active Subprocesses

```bash
# View all active subprocess memory usage
python -c "from claude_pm.monitoring import get_subprocess_memory_monitor; import json; print(json.dumps(get_subprocess_memory_monitor().get_all_subprocess_stats(), indent=2))"

# Check specific subprocess
python -c "from claude_pm.monitoring import get_subprocess_memory_monitor; m = get_subprocess_memory_monitor(); print(m.check_memory('subprocess_id_here'))"
```

## Configuration Reference

### Default Thresholds

| Setting | Default | Environment Variable | Description |
|---------|---------|---------------------|-------------|
| Warning | 1024 MB | `CLAUDE_PM_MEMORY_WARNING_MB` | First alert level |
| Critical | 2048 MB | `CLAUDE_PM_MEMORY_CRITICAL_MB` | Serious alert level |
| Hard Limit | 4096 MB | `CLAUDE_PM_MEMORY_MAX_MB` | Subprocess termination |
| Check Interval | 2 sec | `CLAUDE_PM_MEMORY_CHECK_INTERVAL` | Monitoring frequency |

### Configuration Examples

#### Low Memory System (4GB RAM)

```bash
export CLAUDE_PM_MEMORY_WARNING_MB=512
export CLAUDE_PM_MEMORY_CRITICAL_MB=1024
export CLAUDE_PM_MEMORY_MAX_MB=2048
```

#### High Memory System (32GB+ RAM)

```bash
export CLAUDE_PM_MEMORY_WARNING_MB=2048
export CLAUDE_PM_MEMORY_CRITICAL_MB=4096
export CLAUDE_PM_MEMORY_MAX_MB=8192
```

#### Development/Testing

```bash
export CLAUDE_PM_MEMORY_WARNING_MB=256
export CLAUDE_PM_MEMORY_CRITICAL_MB=512
export CLAUDE_PM_MEMORY_MAX_MB=1024
export CLAUDE_PM_MEMORY_CHECK_INTERVAL=1
```

## Monitoring Operations

### Real-time Monitoring

```bash
# Watch memory alerts in real-time
tail -f .claude-pm/logs/memory/memory-alerts.log

# Monitor with JSON formatting
tail -f .claude-pm/logs/memory/memory-alerts.log | jq '.'

# Filter for critical alerts only
tail -f .claude-pm/logs/memory/memory-alerts.log | jq 'select(.level == "CRITICAL")'
```

### Subprocess Statistics Analysis

```bash
# View all subprocess statistics
cat .claude-pm/logs/memory/subprocess-stats.jsonl | jq '.'

# Find memory-intensive subprocesses
cat .claude-pm/logs/memory/subprocess-stats.jsonl | jq 'select(.memory_stats.peak_mb > 1000)'

# Calculate average memory usage
cat .claude-pm/logs/memory/subprocess-stats.jsonl | jq -s 'map(.memory_stats.peak_mb) | add/length'

# Find aborted subprocesses
cat .claude-pm/logs/memory/subprocess-stats.jsonl | jq 'select(.memory_stats.aborted == true)'
```

### System Memory Health Check

```bash
# Create memory health check script
cat > check_memory_health.py << 'EOF'
#!/usr/bin/env python3
from claude_pm.monitoring import get_memory_monitor
import json

monitor = get_memory_monitor()
status = monitor.get_memory_status()

print(f"System Memory Health Check")
print(f"=" * 50)
print(f"Total Memory: {status['system']['total_mb']:.1f} MB")
print(f"Available: {status['system']['available_mb']:.1f} MB ({100 - status['system']['percent']:.1f}%)")
print(f"Used: {status['system']['used_mb']:.1f} MB ({status['system']['percent']:.1f}%)")
print(f"\nProcess Status:")
print(f"Current Process: {status['process']['memory_mb']:.1f} MB")
print(f"Child Processes: {status['child_count']}")
print(f"Total Child Memory: {status['total_child_memory_mb']:.1f} MB")

if status['system']['percent'] > 80:
    print("\n⚠️  WARNING: High memory usage detected!")
elif status['system']['percent'] > 90:
    print("\n🚨 CRITICAL: Very high memory usage!")
else:
    print("\n✅ Memory usage is healthy")
EOF

python check_memory_health.py
```

## Troubleshooting Procedures

### High Memory Usage Investigation

1. **Identify the Problem Subprocess**

```bash
# Find high memory subprocesses
python -c "
from claude_pm.monitoring import get_subprocess_memory_monitor
monitor = get_subprocess_memory_monitor()
stats = monitor.get_all_subprocess_stats()
for sid, info in stats.items():
    if info['current_mb'] > 1000:
        print(f'{sid}: {info[\"current_mb\"]:.1f} MB (Peak: {info[\"peak_mb\"]:.1f} MB)')
"
```

2. **Check Alert History**

```bash
# Recent memory alerts
grep "CRITICAL" .claude-pm/logs/memory/memory-alerts.log | tail -20

# Alerts for specific subprocess
grep "subprocess_id_here" .claude-pm/logs/memory/memory-alerts.log
```

3. **Analyze Memory Growth Pattern**

```bash
# Create memory growth analysis
cat > analyze_memory_growth.py << 'EOF'
#!/usr/bin/env python3
import json
import sys
from datetime import datetime

subprocess_id = sys.argv[1] if len(sys.argv) > 1 else None

with open('.claude-pm/logs/memory/memory-alerts.log', 'r') as f:
    alerts = [json.loads(line) for line in f if line.strip()]

if subprocess_id:
    alerts = [a for a in alerts if a.get('subprocess_id') == subprocess_id]

for alert in alerts:
    timestamp = datetime.fromisoformat(alert['timestamp'])
    print(f"{timestamp}: {alert['message']}")
    print(f"  System Available: {alert['system_memory']['available_mb']:.1f} MB")
    print()
EOF

python analyze_memory_growth.py [subprocess_id]
```

### Memory Leak Detection

```bash
# Monitor for gradual memory increase
cat > detect_memory_leak.py << 'EOF'
#!/usr/bin/env python3
import json
from collections import defaultdict
from datetime import datetime

stats = []
with open('.claude-pm/logs/memory/subprocess-stats.jsonl', 'r') as f:
    for line in f:
        if line.strip():
            stats.append(json.loads(line))

# Group by subprocess type
by_type = defaultdict(list)
for stat in stats:
    agent_type = stat['subprocess_id'].split('_')[0]
    by_type[agent_type].append(stat)

# Analyze trends
print("Memory Usage Trends by Agent Type")
print("=" * 50)
for agent_type, agent_stats in by_type.items():
    if len(agent_stats) > 1:
        avg_peak = sum(s['memory_stats']['peak_mb'] for s in agent_stats) / len(agent_stats)
        max_peak = max(s['memory_stats']['peak_mb'] for s in agent_stats)
        growth_rate = (agent_stats[-1]['memory_stats']['peak_mb'] - agent_stats[0]['memory_stats']['peak_mb']) / len(agent_stats)
        
        print(f"\n{agent_type}:")
        print(f"  Runs: {len(agent_stats)}")
        print(f"  Avg Peak: {avg_peak:.1f} MB")
        print(f"  Max Peak: {max_peak:.1f} MB")
        print(f"  Growth Rate: {growth_rate:+.1f} MB/run")
        
        if growth_rate > 100:
            print(f"  ⚠️  WARNING: Possible memory leak detected!")
EOF

python detect_memory_leak.py
```

### Emergency Response Procedures

#### 1. System Running Out of Memory

```bash
# Emergency shutdown of all subprocesses
pkill -f "claude-pm"

# Clear memory monitoring logs if full
rm -f .claude-pm/logs/memory/*.log
rm -f .claude-pm/logs/memory/*.jsonl

# Restart with lower limits
export CLAUDE_PM_MEMORY_MAX_MB=1024
claude-pm init
```

#### 2. Subprocess Stuck in High Memory State

```python
# Force terminate specific subprocess
from claude_pm.monitoring import get_subprocess_memory_monitor
monitor = get_subprocess_memory_monitor()

# Get subprocess ID from logs or monitoring
subprocess_id = "engineer_abc123"

# Force stop monitoring and cleanup
monitor.stop_monitoring(subprocess_id)
```

#### 3. Disable Memory Monitoring (Emergency Only)

```bash
# Temporarily disable monitoring
export CLAUDE_PM_DISABLE_MEMORY_MONITOR=true

# Or in Python
from claude_pm.utils.task_tool_helper import TaskToolConfiguration
config = TaskToolConfiguration(enable_memory_monitoring=False)
```

## Maintenance Tasks

### Daily Maintenance

```bash
# Rotate logs if they get too large
if [ $(stat -f%z ".claude-pm/logs/memory/subprocess-stats.jsonl" 2>/dev/null || stat -c%s ".claude-pm/logs/memory/subprocess-stats.jsonl" 2>/dev/null || echo 0) -gt 104857600 ]; then
    mv .claude-pm/logs/memory/subprocess-stats.jsonl .claude-pm/logs/memory/subprocess-stats.$(date +%Y%m%d).jsonl
    touch .claude-pm/logs/memory/subprocess-stats.jsonl
fi
```

### Weekly Analysis

```bash
# Generate weekly memory report
cat > weekly_memory_report.py << 'EOF'
#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from collections import Counter

# Load subprocess stats
stats = []
with open('.claude-pm/logs/memory/subprocess-stats.jsonl', 'r') as f:
    for line in f:
        if line.strip():
            stats.append(json.loads(line))

# Filter last 7 days
week_ago = datetime.now() - timedelta(days=7)
recent_stats = [s for s in stats if datetime.fromisoformat(s['timestamp']) > week_ago]

print("Weekly Memory Usage Report")
print("=" * 50)
print(f"Total Subprocesses: {len(recent_stats)}")
print(f"Aborted Subprocesses: {sum(1 for s in recent_stats if s['memory_stats']['aborted'])}")

# Memory statistics
all_peaks = [s['memory_stats']['peak_mb'] for s in recent_stats]
if all_peaks:
    print(f"\nMemory Statistics:")
    print(f"  Average Peak: {sum(all_peaks) / len(all_peaks):.1f} MB")
    print(f"  Maximum Peak: {max(all_peaks):.1f} MB")
    print(f"  Minimum Peak: {min(all_peaks):.1f} MB")

# Warnings summary
all_warnings = []
for s in recent_stats:
    all_warnings.extend(s['memory_stats']['warnings'])

if all_warnings:
    print(f"\nWarnings Summary:")
    warning_types = Counter(w.split(':')[0] for w in all_warnings)
    for wtype, count in warning_types.items():
        print(f"  {wtype}: {count}")
EOF

python weekly_memory_report.py
```

## Performance Tuning

### Optimize Memory Thresholds

```python
# Analyze historical data to set optimal thresholds
import json
import numpy as np

# Load all subprocess stats
stats = []
with open('.claude-pm/logs/memory/subprocess-stats.jsonl', 'r') as f:
    for line in f:
        if line.strip():
            stats.append(json.loads(line))

# Calculate percentiles
peaks = [s['memory_stats']['peak_mb'] for s in stats if not s['memory_stats']['aborted']]
if peaks:
    p50 = np.percentile(peaks, 50)
    p90 = np.percentile(peaks, 90)
    p99 = np.percentile(peaks, 99)
    
    print(f"Recommended Thresholds based on {len(peaks)} successful runs:")
    print(f"  Warning: {int(p90)} MB (90th percentile)")
    print(f"  Critical: {int(p99)} MB (99th percentile)")
    print(f"  Max: {int(p99 * 1.5)} MB (150% of 99th percentile)")
```

### Memory-Efficient Task Patterns

```python
# Example: Breaking large tasks into smaller chunks
from claude_pm.utils.task_tool_helper import TaskToolHelper

helper = TaskToolHelper()

# Instead of one large task
# DON'T: Process 1000 files at once
# result = helper.create_agent_subprocess(
#     agent_type="engineer",
#     task_description="Process all 1000 files"
# )

# DO: Process in batches
batch_size = 100
for i in range(0, 1000, batch_size):
    result = helper.create_agent_subprocess(
        agent_type="engineer",
        task_description=f"Process files {i} to {i+batch_size}"
    )
    # Memory is released between batches
```

## Integration with Monitoring Services

### Prometheus Metrics Export

```python
# Export memory metrics for Prometheus
from prometheus_client import Gauge, start_http_server
from claude_pm.monitoring import get_subprocess_memory_monitor

# Create metrics
subprocess_memory = Gauge('claude_pm_subprocess_memory_mb', 'Subprocess memory usage in MB', ['subprocess_id'])
subprocess_count = Gauge('claude_pm_subprocess_count', 'Number of active subprocesses')

# Update metrics
def update_metrics():
    monitor = get_subprocess_memory_monitor()
    stats = monitor.get_all_subprocess_stats()
    
    subprocess_count.set(len(stats))
    for sid, info in stats.items():
        subprocess_memory.labels(subprocess_id=sid).set(info['current_mb'])

# Start metrics server
start_http_server(8000)
```

### Alert Integration

```bash
# Send alerts to Slack/Discord/Email
cat > send_memory_alert.py << 'EOF'
#!/usr/bin/env python3
import json
import requests
from datetime import datetime

WEBHOOK_URL = "YOUR_WEBHOOK_URL"

with open('.claude-pm/logs/memory/memory-alerts.log', 'r') as f:
    # Get last line
    for line in f:
        pass
    last_alert = json.loads(line)

if last_alert['level'] == 'CRITICAL':
    message = {
        "text": f"🚨 Claude PM Memory Alert",
        "attachments": [{
            "color": "danger",
            "fields": [
                {"title": "Level", "value": last_alert['level'], "short": True},
                {"title": "Subprocess", "value": last_alert['subprocess_id'], "short": True},
                {"title": "Message", "value": last_alert['message']},
                {"title": "System Memory", "value": f"{last_alert['system_memory']['percent']:.1f}% used"}
            ],
            "timestamp": last_alert['timestamp']
        }]
    }
    requests.post(WEBHOOK_URL, json=message)
EOF
```