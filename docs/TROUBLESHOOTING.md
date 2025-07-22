# Claude PM Troubleshooting Guide

## Common Issues and Solutions

### ModuleNotFoundError: No module named 'frontmatter'

**Problem**: When trying to import AgentRegistry or other components, you may encounter:
```
ModuleNotFoundError: No module named 'frontmatter'
```

**Cause**: The `python-frontmatter` and `mistune` dependencies were not included in earlier versions of the npm package installation process.

**Solution**:

1. **For new installations**: The dependencies are now included in the installation process and will be installed automatically.

2. **For existing installations**: Run the missing dependencies installer:
   ```bash
   npm run install:missing-deps
   ```
   
   Or manually:
   ```bash
   python3 scripts/install_missing_dependencies.py
   ```

3. **Alternative manual installation**:
   ```bash
   pip install --user python-frontmatter>=1.0.0 mistune>=3.0.0
   ```

   If you encounter "externally-managed-environment" errors:
   ```bash
   pip install --user --break-system-packages python-frontmatter>=1.0.0 mistune>=3.0.0
   ```
   
   **📱 macOS Users**: For a comprehensive solution to the "externally-managed-environment" error, see our [macOS Installation Guide](./MACOS_INSTALLATION_GUIDE.md). Quick fix:
   ```bash
   # Use pipx (recommended)
   brew install pipx
   pipx install @bobmatnyc/claude-multiagent-pm
   
   # Or run our installer script
   ./scripts/install-claude-pm-macos.sh
   ```

### Other Missing Dependencies

The framework requires several Python packages. If you encounter import errors for any of these modules:
- click
- rich
- pydantic
- yaml (pyyaml)
- dotenv (python-dotenv)
- requests
- openai
- aiohttp
- httpx
- typer
- toml
- psutil
- pathspec

Run the missing dependencies installer as shown above, or install all base requirements:
```bash
pip install -r requirements/base.txt
```

### Verifying Installation

After fixing dependencies, verify the installation:
```bash
claude-pm --version
python3 -c "from claude_pm.core.agent_registry import AgentRegistry; print('AgentRegistry OK')"
```

Both commands should execute without errors.

## Orchestration and Message Bus Issues

### AttributeError: 'NoneType' object has no attribute 'send_request'

**Problem**: When orchestrating agents, you may encounter:
```
AttributeError: 'NoneType' object has no attribute 'send_request'
```

**Cause**: The message bus component is accessed before initialization in LOCAL orchestration mode. This is a race condition that occurs when the orchestrator tries to use components before they're fully initialized.

**Solution**:

1. **Immediate Fix**: The framework now includes defensive initialization checks:
   ```python
   # Defensive check before message bus usage
   if not self._message_bus:
       self._message_bus = SimpleMessageBus()
       self._register_default_agent_handlers()
   ```

2. **Verify Orchestration Mode**:
   ```bash
   # Check current mode (should be LOCAL by default)
   echo $CLAUDE_PM_ORCHESTRATION_MODE
   
   # If set to SUBPROCESS, remove the override for better performance
   unset CLAUDE_PM_ORCHESTRATION_MODE
   ```

3. **Force LOCAL Mode** (if needed):
   ```bash
   export CLAUDE_PM_ORCHESTRATION_MODE=LOCAL
   ```

**Performance Impact**: LOCAL mode is 150x faster (~200ms vs 30+ seconds per agent query).

### Slow Agent Response Times

**Problem**: Agent queries taking 30+ seconds instead of milliseconds.

**Cause**: System falling back to SUBPROCESS mode due to initialization failures or explicit configuration.

**Solution**:

1. **Check orchestration logs**:
   ```bash
   # Look for mode indicators in recent logs
   grep -E "orchestration_mode|subprocess|LOCAL" ~/.claude-pm/logs/claude-pm.log | tail -20
   ```

2. **Ensure LOCAL mode is default**:
   ```bash
   # Remove any subprocess mode overrides
   unset CLAUDE_PM_FORCE_SUBPROCESS_MODE
   ```

3. **Verify initialization is working**:
   ```python
   # Test orchestration initialization
   python3 -c "
   from claude_pm.orchestration import BackwardsCompatibleOrchestrator
   orch = BackwardsCompatibleOrchestrator()
   print(f'Mode: {orch.mode}')
   print(f'Message Bus: {orch._message_bus is not None}')
   "
   ```

### Handler Registration Failures

**Problem**: "No handler registered for agent: [agent_type]" errors during orchestration.

**Solution**:

1. **Ensure handlers are registered after message bus initialization**
2. **Check available handlers**:
   ```python
   python3 -c "
   from claude_pm.orchestration import create_backwards_compatible_orchestrator
   orch = create_backwards_compatible_orchestrator()
   print('Registered agents:', orch._message_bus.registered_agents if orch._message_bus else 'Bus not initialized')
   "
   ```

3. **Verify agent type is supported** (14 default types are pre-registered)

## Memory Monitoring Issues

### Subprocess Aborted Due to Memory Limit

**Problem**: Task Tool subprocess terminates with "Memory exceeded 4096MB limit" error.

**Cause**: Subprocess memory usage exceeded the configured hard limit (default 4GB).

**Solution**:

1. **Check memory alerts for details**:
   ```bash
   # View recent memory alerts
   tail -20 .claude-pm/logs/memory/memory-alerts.log | jq '.'
   
   # Find specific subprocess alerts
   grep "subprocess_id_here" .claude-pm/logs/memory/memory-alerts.log
   ```

2. **Analyze subprocess memory usage**:
   ```bash
   # View subprocess statistics
   cat .claude-pm/logs/memory/subprocess-stats.jsonl | jq 'select(.subprocess_id == "subprocess_id_here")'
   ```

3. **Increase memory limits if needed**:
   ```bash
   # For systems with more RAM
   export CLAUDE_PM_MEMORY_WARNING_MB=2048
   export CLAUDE_PM_MEMORY_CRITICAL_MB=4096
   export CLAUDE_PM_MEMORY_MAX_MB=8192
   ```

4. **Break large tasks into smaller chunks**:
   - Split file processing into batches
   - Process data incrementally
   - Use streaming where possible

### Cannot Create Subprocess - Insufficient Memory

**Problem**: "Insufficient memory: only XXX MB available (need at least 1GB)" error.

**Cause**: System doesn't have enough free memory to safely create a new subprocess.

**Solution**:

1. **Check system memory status**:
   ```bash
   # View current memory usage
   python3 -c "from claude_pm.monitoring import get_memory_monitor; import json; print(json.dumps(get_memory_monitor().get_memory_status(), indent=2))"
   
   # System command alternatives
   free -h  # Linux
   vm_stat  # macOS
   ```

2. **Free up memory**:
   - Close unnecessary applications
   - Wait for current subprocesses to complete
   - Restart the Claude PM framework

3. **Check for memory leaks**:
   ```bash
   # Identify high-memory subprocesses
   python3 -c "
   from claude_pm.monitoring import get_subprocess_memory_monitor
   m = get_subprocess_memory_monitor()
   stats = m.get_all_subprocess_stats()
   for sid, info in stats.items():
       if info['current_mb'] > 1000:
           print(f'{sid}: {info[\"current_mb\"]:.1f} MB')
   "
   ```

### Memory Monitoring Not Working

**Problem**: Memory monitoring features appear to be disabled or not functioning.

**Cause**: Memory monitoring module not properly initialized or explicitly disabled.

**Solution**:

1. **Verify monitoring is available**:
   ```python
   python3 -c "
   try:
       from claude_pm.monitoring import get_memory_monitor
       print('Memory monitoring is available')
   except ImportError as e:
       print(f'Memory monitoring not available: {e}')
   "
   ```

2. **Check configuration**:
   ```bash
   # Ensure monitoring is not disabled
   unset CLAUDE_PM_DISABLE_MEMORY_MONITOR
   
   # Or check current setting
   echo $CLAUDE_PM_DISABLE_MEMORY_MONITOR
   ```

3. **Verify log directory exists**:
   ```bash
   # Create log directory if missing
   mkdir -p .claude-pm/logs/memory
   
   # Check permissions
   ls -la .claude-pm/logs/memory/
   ```

### High Memory Usage Warnings

**Problem**: Frequent memory warnings but no actual problems observed.

**Cause**: Memory thresholds may be too low for your workload.

**Solution**:

1. **Analyze historical memory usage**:
   ```python
   # Calculate optimal thresholds
   python3 -c "
   import json
   import statistics
   
   stats = []
   with open('.claude-pm/logs/memory/subprocess-stats.jsonl', 'r') as f:
       for line in f:
           if line.strip():
               stats.append(json.loads(line))
   
   peaks = [s['memory_stats']['peak_mb'] for s in stats if not s['memory_stats']['aborted']]
   if peaks:
       print(f'Average peak: {statistics.mean(peaks):.1f} MB')
       print(f'Max peak: {max(peaks):.1f} MB')
       print(f'Suggested warning: {int(statistics.mean(peaks) * 1.5)} MB')
       print(f'Suggested critical: {int(max(peaks) * 1.2)} MB')
   "
   ```

2. **Adjust thresholds based on analysis**:
   ```bash
   # Example for higher thresholds
   export CLAUDE_PM_MEMORY_WARNING_MB=3072
   export CLAUDE_PM_MEMORY_CRITICAL_MB=6144
   export CLAUDE_PM_MEMORY_MAX_MB=8192
   ```

### Memory Logs Growing Too Large

**Problem**: Memory log files consuming significant disk space.

**Cause**: Long-running framework with many subprocess operations.

**Solution**:

1. **Check log file sizes**:
   ```bash
   du -h .claude-pm/logs/memory/*
   ```

2. **Rotate logs manually**:
   ```bash
   # Archive old logs
   cd .claude-pm/logs/memory
   for file in *.log *.jsonl; do
     if [ -f "$file" ] && [ $(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null) -gt 104857600 ]; then
       mv "$file" "${file}.$(date +%Y%m%d)"
       touch "$file"
     fi
   done
   ```

3. **Set up automatic rotation** (cron job):
   ```bash
   # Add to crontab
   0 0 * * * find ~/.claude-pm/logs/memory -name "*.log" -size +100M -exec mv {} {}.$(date +\%Y\%m\%d) \; -exec touch {} \;
   ```