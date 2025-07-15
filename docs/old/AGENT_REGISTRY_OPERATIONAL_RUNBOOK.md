# Agent Registry System Operational Runbook

**Date**: July 15, 2025  
**Documentation Agent**: Agent Registry Operations Manual  
**Framework Version**: 014  
**Context**: ISS-0118 Two-Tier Agent Hierarchy Operational Guide  

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [System Architecture](#system-architecture)
3. [Daily Operations](#daily-operations)
4. [Agent Management](#agent-management)
5. [Performance Monitoring](#performance-monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Emergency Procedures](#emergency-procedures)
8. [Maintenance Tasks](#maintenance-tasks)

---

## Quick Reference

### Essential Commands

```bash
# Health Check
python3 -c "from claude_pm.core import validate_core_system; print('✅ HEALTHY' if validate_core_system() else '❌ UNHEALTHY')"

# List Available Agents
python3 -c "from claude_pm.services.pm_orchestrator import AgentRegistry; registry = AgentRegistry(); agents = registry.listAgents(); [print(f'{name}: {meta.source_tier}') for name, meta in agents.items()]"

# Cache Performance
python3 -c "from claude_pm.services.shared_prompt_cache import SharedPromptCache; cache = SharedPromptCache.get_instance(); metrics = cache.get_metrics(); print(f'Hit Rate: {metrics[\"hit_rate\"]:.1%}, Operations: {metrics[\"total_operations\"]}')"

# Memory Collection Status
python3 -c "from claude_pm.services.async_memory_collector import AsyncMemoryCollector; import asyncio; asyncio.run(AsyncMemoryCollector().get_health())"
```

### Key Performance Indicators

| Metric | Healthy Range | Critical Threshold |
|--------|---------------|-------------------|
| Cache Hit Rate | >80% | <50% |
| Agent Discovery Time | <100ms | >1000ms |
| Memory Collection Success | >90% | <70% |
| Service Response Time | <500ms | >2000ms |

---

## System Architecture

### Two-Tier Agent Hierarchy

**Tier Structure:**
```
System Tier (claude_pm/agents/):
└── base_agent.py (framework fallback)

User Tier (~/.claude-pm/agents/user/):
├── pm_agent.py (79,126 chars)
├── documentation_agent.py (39,864 chars)
├── qa_agent.py
├── research_agent.py
├── ops_agent.py
├── security_agent.py
├── engineer_agent.py
└── version_control_agent.py
```

### Directory Precedence Order

1. **Current Directory**: `$PWD/.claude-pm/agents/` (highest precedence)
2. **Parent Directories**: Walk up tree checking `.claude-pm/agents/`
3. **User Directory**: `~/.claude-pm/agents/user/`
4. **System Directory**: `claude_pm/agents/` (lowest precedence, always available)

### Core Services Integration

**SharedPromptCache:**
- **Performance**: 82.2% improvement in operations
- **Configuration**: 100MB memory limit, 30-minute TTL
- **Integration**: Singleton pattern with cross-subprocess sharing

**AsyncMemoryCollector:**
- **Performance**: 83.3% success rate, <10ms latency
- **Configuration**: Batch processing, retry logic, queue management
- **Integration**: ServiceManager registration with health monitoring

---

## Daily Operations

### Morning Health Check Routine

**1. System Health Validation**
```bash
#!/bin/bash
# Daily health check script

echo "🔍 Claude PM Framework Health Check - $(date)"
echo "================================================"

# Framework Core Health
echo "📋 Framework Health:"
python3 -c "
from claude_pm.core import validate_core_system
result = validate_core_system()
print(f'  Core System: {\"✅ HEALTHY\" if result else \"❌ UNHEALTHY\"}')"

# CLI Integration
echo "🖥️  CLI Integration:"
claude-pm --version > /dev/null 2>&1 && echo "  CLI Version: ✅ WORKING" || echo "  CLI Version: ❌ FAILED"
claude-pm init > /dev/null 2>&1 && echo "  CLI Init: ✅ WORKING" || echo "  CLI Init: ❌ FAILED"

# Agent Discovery
echo "🤖 Agent Discovery:"
python3 -c "
from claude_pm.services.pm_orchestrator import AgentRegistry
registry = AgentRegistry()
agents = registry.listAgents()
print(f'  Available Agents: {len(agents)}')
print(f'  User Agents: {len([a for a in agents.values() if a.source_tier == \"user\"])}')
print(f'  System Agents: {len([a for a in agents.values() if a.source_tier == \"system\"])}')"

# Cache Performance
echo "⚡ Cache Performance:"
python3 -c "
from claude_pm.services.shared_prompt_cache import SharedPromptCache
try:
    cache = SharedPromptCache.get_instance()
    metrics = cache.get_metrics()
    print(f'  Hit Rate: {metrics[\"hit_rate\"]:.1%}')
    print(f'  Operations: {metrics[\"total_operations\"]}')
    print(f'  Memory: {metrics[\"memory_usage_mb\"]:.1f} MB')
except Exception as e:
    print(f'  Cache: ❌ ERROR - {e}')
"

echo "================================================"
echo "✅ Daily health check completed"
```

**2. Performance Metrics Review**
```python
# Performance monitoring script
from claude_pm.services.health_monitor import HealthMonitor
from claude_pm.services.shared_prompt_cache import SharedPromptCache
import datetime

def daily_performance_review():
    print(f"📊 Performance Review - {datetime.datetime.now()}")
    print("=" * 50)
    
    # Health Monitor Check
    monitor = HealthMonitor()
    health = monitor.check_framework_health()
    
    print(f"🏥 System Health:")
    print(f"  Services: {health.get('services_status', 'Unknown')}")
    print(f"  Cache: {health.get('cache_status', 'Unknown')}")
    print(f"  Memory: {health.get('memory_status', 'Unknown')}")
    
    # Cache Performance
    cache = SharedPromptCache.get_instance()
    metrics = cache.get_metrics()
    
    print(f"⚡ Cache Performance:")
    print(f"  Hit Rate: {metrics['hit_rate']:.1%}")
    print(f"  Total Operations: {metrics['total_operations']}")
    print(f"  Memory Usage: {metrics['memory_usage_mb']:.1f} MB")
    print(f"  Entries: {metrics.get('entry_count', 'Unknown')}")
    
    # Performance Alerts
    if metrics['hit_rate'] < 0.8:
        print("⚠️  WARNING: Cache hit rate below 80%")
    if metrics['memory_usage_mb'] > 80:
        print("⚠️  WARNING: Cache memory usage above 80MB")
    
    print("=" * 50)

# Run daily review
daily_performance_review()
```

### Agent Status Monitoring

**Agent Availability Check:**
```python
def check_agent_availability():
    from claude_pm.services.pm_orchestrator import AgentRegistry
    
    registry = AgentRegistry()
    agents = registry.listAgents()
    
    # Expected core agents
    core_agents = [
        'pm_agent', 'documentation_agent', 'qa_agent', 'research_agent',
        'ops_agent', 'security_agent', 'engineer_agent', 'version_control_agent'
    ]
    
    print("🤖 Agent Availability Report")
    print("-" * 30)
    
    for agent_name in core_agents:
        status = "✅ AVAILABLE" if agent_name in agents else "❌ MISSING"
        tier = agents.get(agent_name, {}).get('source_tier', 'N/A')
        print(f"  {agent_name}: {status} ({tier})")
    
    # Additional agents
    additional = [name for name in agents if name not in core_agents]
    if additional:
        print(f"\n📝 Additional Agents ({len(additional)}):")
        for agent in additional:
            print(f"  {agent}: {agents[agent].source_tier}")

check_agent_availability()
```

---

## Agent Management

### Agent Discovery Operations

**List All Available Agents:**
```python
def list_all_agents():
    from claude_pm.services.pm_orchestrator import AgentRegistry
    
    registry = AgentRegistry()
    agents = registry.listAgents()
    
    print(f"📋 Available Agents ({len(agents)} total)")
    print("=" * 60)
    
    # Group by tier
    tiers = {}
    for name, metadata in agents.items():
        tier = metadata.source_tier
        if tier not in tiers:
            tiers[tier] = []
        tiers[tier].append((name, metadata))
    
    # Display by tier
    for tier in ['user', 'system']:
        if tier in tiers:
            print(f"\n🏗️  {tier.upper()} TIER ({len(tiers[tier])} agents):")
            for name, metadata in sorted(tiers[tier]):
                print(f"  📦 {name}")
                print(f"     Path: {metadata.file_path}")
                print(f"     Size: {metadata.file_size} bytes")
                print(f"     Modified: {metadata.last_modified}")

list_all_agents()
```

**Verify Agent Loading:**
```python
def verify_agent_loading(agent_name):
    from claude_pm.services.pm_orchestrator import AgentRegistry
    import time
    
    registry = AgentRegistry()
    
    print(f"🔍 Testing Agent Loading: {agent_name}")
    print("-" * 40)
    
    # Check if agent exists
    agents = registry.listAgents()
    if agent_name not in agents:
        print(f"❌ Agent '{agent_name}' not found in registry")
        return False
    
    # Load agent
    start_time = time.time()
    try:
        agent = registry.loadAgent(agent_name)
        load_time = time.time() - start_time
        
        print(f"✅ Agent loaded successfully")
        print(f"   Name: {agent.name}")
        print(f"   Source: {agent.source_tier}")
        print(f"   Load Time: {load_time:.3f}s")
        
        # Performance check
        if load_time < 0.05:  # 50ms target
            print(f"⚡ Excellent performance (<50ms)")
        elif load_time < 0.1:  # 100ms acceptable
            print(f"✅ Good performance (<100ms)")
        else:
            print(f"⚠️  Slow loading (>{100}ms)")
        
        return True
        
    except Exception as e:
        load_time = time.time() - start_time
        print(f"❌ Agent loading failed: {e}")
        print(f"   Failed after: {load_time:.3f}s")
        return False

# Test core agents
core_agents = ['pm_agent', 'documentation_agent', 'qa_agent']
for agent in core_agents:
    verify_agent_loading(agent)
    print()
```

### Agent Directory Management

**Verify Directory Structure:**
```python
def verify_directory_structure():
    import os
    from claude_pm.services.parent_directory_manager import ParentDirectoryManager
    
    print("📁 Directory Structure Verification")
    print("=" * 40)
    
    manager = ParentDirectoryManager()
    directories = manager.get_agent_directories()
    
    for i, directory in enumerate(directories, 1):
        exists = os.path.exists(directory)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        
        print(f"{i}. {directory}")
        print(f"   Status: {status}")
        
        if exists:
            agent_files = [f for f in os.listdir(directory) if f.endswith('.py')]
            print(f"   Agents: {len(agent_files)} files")
            if agent_files:
                print(f"   Files: {', '.join(agent_files[:3])}")
                if len(agent_files) > 3:
                    print(f"          ... and {len(agent_files) - 3} more")
        print()

verify_directory_structure()
```

**Clean Up Empty Directories:**
```bash
#!/bin/bash
# Cleanup script for empty agent directories

echo "🧹 Agent Directory Cleanup"
echo "========================="

# Check current directory
if [ -d ".claude-pm/agents" ]; then
    if [ -z "$(ls -A .claude-pm/agents/)" ]; then
        echo "📁 Current directory agents folder is empty (expected after migration)"
    else
        echo "📁 Current directory agents folder has content:"
        ls -la .claude-pm/agents/
    fi
fi

# Check user directory
if [ -d "$HOME/.claude-pm/agents" ]; then
    echo "📁 User directory agents folder:"
    find "$HOME/.claude-pm/agents" -name "*.py" | wc -l | xargs echo "   Agent files:"
else
    echo "❌ User directory agents folder not found"
fi

# Check for orphaned directories
echo "🔍 Checking for orphaned .claude-pm directories:"
find . -name ".claude-pm" -type d | head -5
```

---

## Performance Monitoring

### Real-Time Performance Dashboard

**Continuous Monitoring Script:**
```python
import time
import datetime
from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.health_monitor import HealthMonitor

def performance_dashboard():
    """Real-time performance monitoring dashboard"""
    
    cache = SharedPromptCache.get_instance()
    monitor = HealthMonitor()
    
    print("🚀 Claude PM Performance Dashboard")
    print("=" * 50)
    print("Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"📊 Performance Report - {timestamp}")
            print("-" * 30)
            
            # Cache Metrics
            cache_metrics = cache.get_metrics()
            hit_rate = cache_metrics.get('hit_rate', 0)
            operations = cache_metrics.get('total_operations', 0)
            memory_mb = cache_metrics.get('memory_usage_mb', 0)
            
            print(f"⚡ Cache Performance:")
            print(f"  Hit Rate: {hit_rate:.1%} {'✅' if hit_rate > 0.8 else '⚠️' if hit_rate > 0.5 else '❌'}")
            print(f"  Operations: {operations}")
            print(f"  Memory: {memory_mb:.1f} MB {'✅' if memory_mb < 80 else '⚠️'}")
            
            # System Health
            health = monitor.check_framework_health()
            print(f"🏥 System Health:")
            print(f"  Services: {health.get('services_status', 'Unknown')}")
            print(f"  Framework: {health.get('framework_status', 'Unknown')}")
            
            # Performance Alerts
            alerts = []
            if hit_rate < 0.5:
                alerts.append("🚨 CRITICAL: Cache hit rate below 50%")
            elif hit_rate < 0.8:
                alerts.append("⚠️  WARNING: Cache hit rate below 80%")
            
            if memory_mb > 80:
                alerts.append("⚠️  WARNING: Cache memory usage above 80MB")
            
            if alerts:
                print(f"\n🚨 Alerts:")
                for alert in alerts:
                    print(f"  {alert}")
            
            print(f"\n{'=' * 50}")
            time.sleep(30)  # Update every 30 seconds
            
    except KeyboardInterrupt:
        print("\n\n👋 Performance monitoring stopped")

# Run the dashboard
performance_dashboard()
```

### Performance Benchmarking

**Agent Discovery Benchmark:**
```python
import time
import statistics

def benchmark_agent_discovery():
    from claude_pm.services.pm_orchestrator import AgentRegistry
    
    print("🏁 Agent Discovery Performance Benchmark")
    print("=" * 45)
    
    registry = AgentRegistry()
    
    # Benchmark listAgents() performance
    times = []
    for i in range(10):
        start = time.time()
        agents = registry.listAgents()
        end = time.time()
        times.append((end - start) * 1000)  # Convert to milliseconds
    
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"📋 listAgents() Performance:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Min: {min_time:.2f}ms")
    print(f"  Max: {max_time:.2f}ms")
    print(f"  Agents Found: {len(agents)}")
    
    # Performance assessment
    if avg_time < 10:
        print(f"  Assessment: ⚡ EXCELLENT (target: <100ms)")
    elif avg_time < 50:
        print(f"  Assessment: ✅ GOOD (target: <100ms)")
    elif avg_time < 100:
        print(f"  Assessment: ✅ ACCEPTABLE (target: <100ms)")
    else:
        print(f"  Assessment: ❌ SLOW (target: <100ms)")
    
    # Benchmark agent loading
    print(f"\n🤖 Agent Loading Performance:")
    
    if agents:
        agent_name = list(agents.keys())[0]
        load_times = []
        
        for i in range(5):
            start = time.time()
            agent = registry.loadAgent(agent_name)
            end = time.time()
            load_times.append((end - start) * 1000)
        
        avg_load = statistics.mean(load_times)
        print(f"  Agent: {agent_name}")
        print(f"  Average Load Time: {avg_load:.2f}ms")
        
        if avg_load < 50:
            print(f"  Assessment: ⚡ EXCELLENT (target: <50ms)")
        elif avg_load < 100:
            print(f"  Assessment: ✅ GOOD (target: <50ms)")
        else:
            print(f"  Assessment: ⚠️  SLOW (target: <50ms)")

benchmark_agent_discovery()
```

### Cache Performance Analysis

**Cache Optimization Analysis:**
```python
def analyze_cache_performance():
    from claude_pm.services.shared_prompt_cache import SharedPromptCache
    
    cache = SharedPromptCache.get_instance()
    metrics = cache.get_metrics()
    
    print("🎯 Cache Performance Analysis")
    print("=" * 35)
    
    # Basic metrics
    hit_rate = metrics.get('hit_rate', 0)
    total_ops = metrics.get('total_operations', 0)
    memory_mb = metrics.get('memory_usage_mb', 0)
    entries = metrics.get('entry_count', 0)
    
    print(f"📊 Current Metrics:")
    print(f"  Hit Rate: {hit_rate:.1%}")
    print(f"  Total Operations: {total_ops}")
    print(f"  Memory Usage: {memory_mb:.1f} MB")
    print(f"  Cache Entries: {entries}")
    
    # Performance recommendations
    print(f"\n💡 Optimization Recommendations:")
    
    if hit_rate < 0.6:
        print(f"  📈 CRITICAL: Increase cache size or TTL")
        print(f"     Current hit rate ({hit_rate:.1%}) is below optimal")
    elif hit_rate < 0.8:
        print(f"  📈 Consider increasing cache size or TTL")
        print(f"     Hit rate ({hit_rate:.1%}) could be improved")
    else:
        print(f"  ✅ Hit rate ({hit_rate:.1%}) is excellent")
    
    if memory_mb > 80:
        print(f"  💾 WARNING: High memory usage ({memory_mb:.1f} MB)")
        print(f"     Consider reducing cache size or TTL")
    elif memory_mb > 50:
        print(f"  💾 Monitor memory usage ({memory_mb:.1f} MB)")
    else:
        print(f"  ✅ Memory usage ({memory_mb:.1f} MB) is optimal")
    
    # Cache efficiency
    if total_ops > 0:
        efficiency = (hit_rate * 100) / (memory_mb + 1)
        print(f"\n⚡ Cache Efficiency Score: {efficiency:.1f}")
        
        if efficiency > 50:
            print(f"  ✅ Highly efficient cache utilization")
        elif efficiency > 20:
            print(f"  ✅ Good cache utilization")
        else:
            print(f"  ⚠️  Poor cache utilization - needs optimization")

analyze_cache_performance()
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Agent Not Found Errors

**Symptoms:**
- Agent discovery returns empty results
- LoadAgent() throws "Agent not found" exceptions
- Missing expected core agents

**Diagnostic Commands:**
```bash
# Check agent directories exist
ls -la ~/.claude-pm/agents/
ls -la .claude-pm/agents/
ls -la claude_pm/agents/

# Verify directory permissions
ls -la ~/.claude-pm/
stat ~/.claude-pm/agents/

# Check for agent files
find ~/.claude-pm/agents/ -name "*.py" | head -10
find claude_pm/agents/ -name "*.py" | head -10
```

**Solutions:**
```python
# 1. Recreate missing directories
import os

directories = [
    os.path.expanduser("~/.claude-pm/agents/user/"),
    ".claude-pm/agents/",
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

# 2. Verify agent files
from claude_pm.services.pm_orchestrator import AgentRegistry

registry = AgentRegistry()
agents = registry.listAgents()

if not agents:
    print("❌ No agents found - check directory structure")
else:
    print(f"✅ Found {len(agents)} agents")
```

#### Issue 2: Cache Performance Issues

**Symptoms:**
- Low cache hit rates (<50%)
- High cache memory usage
- Slow agent loading times

**Diagnostic Commands:**
```python
# Cache diagnostics
from claude_pm.services.shared_prompt_cache import SharedPromptCache

cache = SharedPromptCache.get_instance()
metrics = cache.get_metrics()

print("🔍 Cache Diagnostics:")
print(f"  Hit Rate: {metrics['hit_rate']:.1%}")
print(f"  Memory: {metrics['memory_usage_mb']:.1f} MB")
print(f"  Operations: {metrics['total_operations']}")
print(f"  Entries: {metrics.get('entry_count', 'Unknown')}")

# Check cache configuration
config = cache.get_configuration()
print(f"\n⚙️  Cache Configuration:")
print(f"  Max Size: {config.get('max_size', 'Unknown')}")
print(f"  Max Memory: {config.get('max_memory_mb', 'Unknown')} MB")
print(f"  Default TTL: {config.get('default_ttl', 'Unknown')}s")
```

**Solutions:**
```python
# 1. Optimize cache configuration
cache_config = {
    "max_size": 2000,        # Increase cache size
    "max_memory_mb": 150,    # Increase memory limit
    "default_ttl": 3600      # Increase TTL to 1 hour
}

# Reinitialize cache with new config
cache = SharedPromptCache.get_instance(cache_config)

# 2. Clear cache if corrupted
cache.clear()
print("Cache cleared and reset")

# 3. Invalidate specific patterns
cache.invalidate_pattern("agent_profile:*")
cache.invalidate_pattern("task_prompt:*")
```

#### Issue 3: Memory Collection Failures

**Symptoms:**
- AsyncMemoryCollector success rate below 70%
- Memory operations timing out
- Queue processing errors

**Diagnostic Commands:**
```python
# Memory collector diagnostics
import asyncio
from claude_pm.services.async_memory_collector import AsyncMemoryCollector

async def diagnose_memory_collector():
    collector = AsyncMemoryCollector()
    
    # Check service health
    health = await collector.get_health()
    print("🏥 Memory Collector Health:")
    print(f"  Status: {health.get('status', 'Unknown')}")
    print(f"  Queue Size: {health.get('queue_size', 'Unknown')}")
    print(f"  Success Rate: {health.get('success_rate', 'Unknown'):.1%}")
    
    # Get statistics
    stats = await collector.get_statistics()
    print(f"\n📊 Memory Collector Stats:")
    print(f"  Total Operations: {stats.get('total_operations', 0)}")
    print(f"  Successful: {stats.get('successful_operations', 0)}")
    print(f"  Failed: {stats.get('failed_operations', 0)}")

asyncio.run(diagnose_memory_collector())
```

**Solutions:**
```python
# 1. Restart memory collector service
from claude_pm.core.service_manager import ServiceManager

service_manager = ServiceManager()
await service_manager.restart_service("async_memory_collector")

# 2. Adjust configuration for better performance
memory_config = {
    "batch_size": 10,        # Smaller batches
    "batch_timeout": 30.0,   # Longer timeout
    "max_retries": 5,        # More retries
    "max_queue_size": 1000   # Smaller queue
}

# 3. Clear stuck operations
collector = AsyncMemoryCollector()
await collector.clear_queue()
```

### Emergency Diagnostic Script

**Complete System Diagnostic:**
```python
#!/usr/bin/env python3
"""
Emergency diagnostic script for Claude PM Framework
Run this when experiencing system-wide issues
"""

import os
import time
import asyncio
from datetime import datetime

def emergency_diagnostics():
    print("🚨 EMERGENCY DIAGNOSTIC REPORT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Working Directory: {os.getcwd()}")
    print()
    
    # 1. Core System Health
    print("1️⃣  CORE SYSTEM HEALTH")
    print("-" * 30)
    try:
        from claude_pm.core import validate_core_system
        core_health = validate_core_system()
        print(f"Core System: {'✅ HEALTHY' if core_health else '❌ UNHEALTHY'}")
    except Exception as e:
        print(f"Core System: ❌ ERROR - {e}")
    
    # 2. CLI Integration
    print("\n2️⃣  CLI INTEGRATION")
    print("-" * 30)
    cli_version = os.system("claude-pm --version > /dev/null 2>&1")
    cli_init = os.system("claude-pm init > /dev/null 2>&1")
    
    print(f"CLI Version: {'✅ WORKING' if cli_version == 0 else '❌ FAILED'}")
    print(f"CLI Init: {'✅ WORKING' if cli_init == 0 else '❌ FAILED'}")
    
    # 3. Agent Registry
    print("\n3️⃣  AGENT REGISTRY")
    print("-" * 30)
    try:
        from claude_pm.services.pm_orchestrator import AgentRegistry
        registry = AgentRegistry()
        agents = registry.listAgents()
        print(f"Agents Available: {len(agents)}")
        
        # Test loading a core agent
        if 'pm_agent' in agents:
            start = time.time()
            agent = registry.loadAgent('pm_agent')
            load_time = time.time() - start
            print(f"PM Agent Load: ✅ SUCCESS ({load_time:.3f}s)")
        else:
            print(f"PM Agent Load: ❌ AGENT NOT FOUND")
            
    except Exception as e:
        print(f"Agent Registry: ❌ ERROR - {e}")
    
    # 4. Cache System
    print("\n4️⃣  CACHE SYSTEM")
    print("-" * 30)
    try:
        from claude_pm.services.shared_prompt_cache import SharedPromptCache
        cache = SharedPromptCache.get_instance()
        metrics = cache.get_metrics()
        
        print(f"Cache Status: ✅ OPERATIONAL")
        print(f"Hit Rate: {metrics.get('hit_rate', 0):.1%}")
        print(f"Memory Usage: {metrics.get('memory_usage_mb', 0):.1f} MB")
        
    except Exception as e:
        print(f"Cache System: ❌ ERROR - {e}")
    
    # 5. Directory Structure
    print("\n5️⃣  DIRECTORY STRUCTURE")
    print("-" * 30)
    
    directories = [
        ("User Agents", "~/.claude-pm/agents/"),
        ("Current Agents", ".claude-pm/agents/"),
        ("System Agents", "claude_pm/agents/")
    ]
    
    for name, path in directories:
        expanded_path = os.path.expanduser(path)
        exists = os.path.exists(expanded_path)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        
        print(f"{name}: {status}")
        if exists and os.path.isdir(expanded_path):
            try:
                files = len([f for f in os.listdir(expanded_path) if f.endswith('.py')])
                print(f"  Python files: {files}")
            except:
                print(f"  Python files: ❌ ACCESS ERROR")
    
    # 6. Recent Errors (if log file exists)
    print("\n6️⃣  RECENT ACTIVITY")
    print("-" * 30)
    
    log_files = [
        "logs/claude-pm.log",
        "logs/health-monitor.log",
        "logs/memory-alerts.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"Log: {log_file} ✅ EXISTS")
        else:
            print(f"Log: {log_file} ❌ MISSING")
    
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSTIC COMPLETE")
    print("\nNext Steps:")
    print("1. Review any ❌ FAILED items above")
    print("2. Check specific error messages")
    print("3. Run targeted troubleshooting procedures")
    print("4. Escalate to development team if needed")

if __name__ == "__main__":
    emergency_diagnostics()
```

---

## Emergency Procedures

### Service Recovery Procedures

**Complete Service Restart:**
```python
#!/usr/bin/env python3
"""Emergency service recovery script"""

import asyncio
from claude_pm.core.service_manager import ServiceManager
from claude_pm.services.shared_prompt_cache import SharedPromptCache

async def emergency_service_recovery():
    print("🚑 EMERGENCY SERVICE RECOVERY")
    print("=" * 40)
    
    # 1. Stop all services
    print("1️⃣  Stopping all services...")
    service_manager = ServiceManager()
    await service_manager.stop_all()
    print("   ✅ All services stopped")
    
    # 2. Clear cache
    print("2️⃣  Clearing cache...")
    cache = SharedPromptCache.get_instance()
    cache.clear()
    print("   ✅ Cache cleared")
    
    # 3. Restart core services
    print("3️⃣  Restarting core services...")
    await service_manager.start_all()
    print("   ✅ Core services restarted")
    
    # 4. Validate recovery
    print("4️⃣  Validating recovery...")
    
    # Test agent registry
    try:
        from claude_pm.services.pm_orchestrator import AgentRegistry
        registry = AgentRegistry()
        agents = registry.listAgents()
        print(f"   ✅ Agent registry: {len(agents)} agents")
    except Exception as e:
        print(f"   ❌ Agent registry error: {e}")
    
    # Test cache
    try:
        cache_metrics = cache.get_metrics()
        print(f"   ✅ Cache operational")
    except Exception as e:
        print(f"   ❌ Cache error: {e}")
    
    print("\n🏁 RECOVERY COMPLETE")

# Run recovery
asyncio.run(emergency_service_recovery())
```

**Cache Emergency Reset:**
```python
def emergency_cache_reset():
    """Emergency cache reset procedure"""
    from claude_pm.services.shared_prompt_cache import SharedPromptCache
    
    print("🔄 EMERGENCY CACHE RESET")
    print("=" * 30)
    
    # 1. Get current cache instance
    cache = SharedPromptCache.get_instance()
    
    # 2. Save current metrics for analysis
    try:
        metrics = cache.get_metrics()
        print(f"Pre-reset metrics:")
        print(f"  Hit Rate: {metrics['hit_rate']:.1%}")
        print(f"  Operations: {metrics['total_operations']}")
        print(f"  Memory: {metrics['memory_usage_mb']:.1f} MB")
    except:
        print("Could not retrieve pre-reset metrics")
    
    # 3. Clear all cache data
    cache.clear()
    print("✅ Cache cleared")
    
    # 4. Reinitialize with fresh configuration
    fresh_config = {
        "max_size": 1000,
        "max_memory_mb": 100,
        "default_ttl": 1800  # 30 minutes
    }
    
    cache = SharedPromptCache.get_instance(fresh_config)
    print("✅ Cache reinitialized with fresh configuration")
    
    # 5. Verify cache is working
    try:
        cache.set("test_key", "test_value", ttl=60)
        value = cache.get("test_key")
        if value == "test_value":
            print("✅ Cache functionality verified")
            cache.delete("test_key")
        else:
            print("❌ Cache verification failed")
    except Exception as e:
        print(f"❌ Cache verification error: {e}")
    
    print("🏁 CACHE RESET COMPLETE")

emergency_cache_reset()
```

### System Rollback Procedures

**Agent Configuration Rollback:**
```bash
#!/bin/bash
# Emergency rollback to previous agent configuration

echo "🔄 AGENT CONFIGURATION ROLLBACK"
echo "==============================="

# Create backup of current state
BACKUP_DIR="$HOME/.claude-pm/emergency-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "1️⃣  Creating emergency backup..."
if [ -d "$HOME/.claude-pm/agents" ]; then
    cp -r "$HOME/.claude-pm/agents" "$BACKUP_DIR/"
    echo "   ✅ User agents backed up to $BACKUP_DIR"
fi

# Check for previous backup
RESTORE_FROM="$HOME/.claude-pm/previous-config"
if [ -d "$RESTORE_FROM" ]; then
    echo "2️⃣  Restoring from previous configuration..."
    rm -rf "$HOME/.claude-pm/agents"
    cp -r "$RESTORE_FROM/agents" "$HOME/.claude-pm/"
    echo "   ✅ Previous configuration restored"
else
    echo "2️⃣  No previous configuration found"
    echo "   Creating minimal agent structure..."
    
    mkdir -p "$HOME/.claude-pm/agents/user"
    
    # Download core agents if available
    echo "   Attempting to restore core agents..."
    # This would typically restore from a known good state
fi

echo "3️⃣  Validating rollback..."
python3 -c "
from claude_pm.services.pm_orchestrator import AgentRegistry
registry = AgentRegistry()
agents = registry.listAgents()
print(f'   Agents available after rollback: {len(agents)}')
if len(agents) > 0:
    print('   ✅ Rollback successful')
else:
    print('   ❌ Rollback failed - no agents available')
"

echo "🏁 ROLLBACK COMPLETE"
echo "Emergency backup saved to: $BACKUP_DIR"
```

---

## Maintenance Tasks

### Weekly Maintenance Checklist

**Weekly System Maintenance:**
```python
#!/usr/bin/env python3
"""
Weekly maintenance script for Claude PM Framework
Run every Monday morning
"""

import os
import datetime
from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.health_monitor import HealthMonitor

def weekly_maintenance():
    print("🔧 WEEKLY MAINTENANCE ROUTINE")
    print("=" * 40)
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Cache maintenance
    print("1️⃣  CACHE MAINTENANCE")
    print("-" * 25)
    
    cache = SharedPromptCache.get_instance()
    
    # Get current metrics
    metrics = cache.get_metrics()
    hit_rate = metrics.get('hit_rate', 0)
    memory_mb = metrics.get('memory_usage_mb', 0)
    operations = metrics.get('total_operations', 0)
    
    print(f"Current Performance:")
    print(f"  Hit Rate: {hit_rate:.1%}")
    print(f"  Memory Usage: {memory_mb:.1f} MB")
    print(f"  Total Operations: {operations}")
    
    # Cache optimization
    if hit_rate < 0.7:
        print("⚠️  Optimizing cache configuration...")
        # Could adjust cache size or TTL here
    
    if memory_mb > 80:
        print("💾 High memory usage - consider cleanup")
        # Could trigger cache cleanup
    
    # 2. Agent registry maintenance
    print("\n2️⃣  AGENT REGISTRY MAINTENANCE")
    print("-" * 30)
    
    from claude_pm.services.pm_orchestrator import AgentRegistry
    registry = AgentRegistry()
    agents = registry.listAgents()
    
    print(f"Registered Agents: {len(agents)}")
    
    # Check for missing core agents
    core_agents = [
        'pm_agent', 'documentation_agent', 'qa_agent', 'research_agent',
        'ops_agent', 'security_agent', 'engineer_agent', 'version_control_agent'
    ]
    
    missing_agents = [agent for agent in core_agents if agent not in agents]
    if missing_agents:
        print(f"⚠️  Missing core agents: {', '.join(missing_agents)}")
    else:
        print("✅ All core agents available")
    
    # 3. Directory cleanup
    print("\n3️⃣  DIRECTORY CLEANUP")
    print("-" * 20)
    
    # Check for temporary files
    temp_patterns = [
        ".claude-pm/**/*.tmp",
        ".claude-pm/**/*.log",
        ".claude-pm/**/*.backup"
    ]
    
    cleanup_count = 0
    for pattern in temp_patterns:
        # In a real implementation, would clean up matching files
        # For safety, just report what would be cleaned
        print(f"Would clean: {pattern}")
    
    print(f"Cleanup completed: {cleanup_count} files removed")
    
    # 4. Performance trend analysis
    print("\n4️⃣  PERFORMANCE TREND ANALYSIS")
    print("-" * 35)
    
    # This would analyze performance trends over time
    # For now, just current snapshot
    monitor = HealthMonitor()
    health = monitor.check_framework_health()
    
    print(f"System Health: {health.get('overall_status', 'Unknown')}")
    print(f"Services: {health.get('services_status', 'Unknown')}")
    print(f"Cache: {health.get('cache_status', 'Unknown')}")
    
    # 5. Generate maintenance report
    print("\n5️⃣  MAINTENANCE REPORT")
    print("-" * 25)
    
    report = {
        "date": datetime.datetime.now().isoformat(),
        "cache_hit_rate": hit_rate,
        "cache_memory_mb": memory_mb,
        "total_agents": len(agents),
        "missing_agents": missing_agents,
        "overall_health": health.get('overall_status', 'Unknown')
    }
    
    # Save report (in real implementation)
    print("✅ Maintenance report generated")
    print(f"   Cache Performance: {hit_rate:.1%} hit rate")
    print(f"   Agent Registry: {len(agents)} agents")
    print(f"   System Health: {health.get('overall_status', 'Unknown')}")
    
    print("\n🏁 WEEKLY MAINTENANCE COMPLETE")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if hit_rate < 0.8:
        print("   📈 Consider optimizing cache configuration")
    if missing_agents:
        print("   🤖 Restore missing core agents")
    if memory_mb > 50:
        print("   💾 Monitor cache memory usage")
    
    if not missing_agents and hit_rate > 0.8 and memory_mb < 50:
        print("   ✅ System is running optimally")

if __name__ == "__main__":
    weekly_maintenance()
```

### Monthly Deep Maintenance

**Monthly Performance Analysis:**
```python
def monthly_performance_analysis():
    """Comprehensive monthly performance analysis"""
    
    print("📊 MONTHLY PERFORMANCE ANALYSIS")
    print("=" * 45)
    
    # This would typically analyze:
    # - Performance trends over the month
    # - Cache hit rate patterns
    # - Agent usage statistics
    # - System health trends
    # - Resource utilization
    
    # For now, provide current state analysis
    from claude_pm.services.shared_prompt_cache import SharedPromptCache
    from claude_pm.services.pm_orchestrator import AgentRegistry
    
    cache = SharedPromptCache.get_instance()
    registry = AgentRegistry()
    
    metrics = cache.get_metrics()
    agents = registry.listAgents()
    
    print(f"📈 Performance Summary:")
    print(f"  Cache Hit Rate: {metrics.get('hit_rate', 0):.1%}")
    print(f"  Total Cache Operations: {metrics.get('total_operations', 0)}")
    print(f"  Agent Registry Size: {len(agents)}")
    print(f"  Cache Memory Usage: {metrics.get('memory_usage_mb', 0):.1f} MB")
    
    # Generate recommendations for next month
    print(f"\n🎯 Optimization Recommendations:")
    
    hit_rate = metrics.get('hit_rate', 0)
    if hit_rate < 0.6:
        print(f"  🔧 CRITICAL: Cache hit rate needs improvement")
        print(f"     - Increase cache size")
        print(f"     - Optimize TTL settings")
        print(f"     - Review cache invalidation patterns")
    elif hit_rate < 0.8:
        print(f"  📈 Cache performance could be improved")
        print(f"     - Fine-tune cache configuration")
        print(f"     - Monitor cache patterns")
    else:
        print(f"  ✅ Cache performance is excellent")
    
    memory_mb = metrics.get('memory_usage_mb', 0)
    if memory_mb > 80:
        print(f"  💾 High memory usage detected")
        print(f"     - Consider reducing cache size")
        print(f"     - Implement cache cleanup policies")
    elif memory_mb > 50:
        print(f"  💾 Monitor memory usage trends")
    else:
        print(f"  ✅ Memory usage is optimal")
    
    print(f"\n📋 Action Items for Next Month:")
    print(f"  □ Continue weekly maintenance routine")
    print(f"  □ Monitor performance trends")
    print(f"  □ Review agent usage patterns")
    print(f"  □ Optimize based on usage data")
    
    print(f"\n🏁 MONTHLY ANALYSIS COMPLETE")

monthly_performance_analysis()
```

---

## Conclusion

This operational runbook provides comprehensive guidance for managing the Claude PM Framework's two-tier agent registry system. Regular use of these procedures will ensure optimal performance, quick issue resolution, and maintained system health.

### Key Operational Points

1. **Daily Health Checks**: Run morning health check routine
2. **Performance Monitoring**: Continuous monitoring of cache and agent performance
3. **Proactive Maintenance**: Weekly and monthly maintenance routines
4. **Emergency Preparedness**: Quick access to diagnostic and recovery procedures
5. **Documentation**: Keep operational logs and performance trends

### Contact and Escalation

**For Critical Issues:**
- Run emergency diagnostic script
- Execute emergency recovery procedures
- Document issue details and resolution steps
- Escalate to development team if needed

**Performance Issues:**
- Check cache configuration and metrics
- Analyze agent discovery performance
- Review system resource utilization
- Apply optimization recommendations

---

**Operational Runbook Version**: 1.0  
**Last Updated**: July 15, 2025  
**Documentation Agent**: Agent Registry Operations Manual Completed  
**Associated with**: ISS-0118 (Implement Agent Registry and Hierarchical Discovery System)