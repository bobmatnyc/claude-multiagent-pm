# Performance Quick Reference Guide

## TL;DR - Key Performance Facts

### 🚀 LOCAL Mode Performance
- **14.5x faster** than subprocess mode (13.78ms vs 200ms)
- **25x more memory efficient** (2MB vs 50MB per agent)
- **62% token reduction** through intelligent context filtering
- **Default mode** as of Framework v014

### 📊 Quick Performance Wins

#### 1. Instant Configuration (Zero Setup)
```python
# Already enabled by default in v014+
orchestration_mode = OrchestratorMode.LOCAL
```

#### 2. Response Time Comparison
| Mode | Response Time | Use Case |
|------|--------------|----------|
| LOCAL | 13.78ms | Default - All standard workflows |
| Subprocess | 200ms | Only when process isolation required |

#### 3. Memory Usage
| Mode | Memory per Agent | Scaling |
|------|-----------------|---------|
| LOCAL | 2MB | Linear |
| Subprocess | 50MB | Exponential |

### ✅ When to Use LOCAL Mode (Default)
- Real-time interactive workflows
- Development and testing
- CI/CD pipelines
- Memory-constrained environments
- High-frequency agent coordination

### ⚠️ When to Consider Subprocess Mode
- Untrusted agent code execution
- Strict process isolation requirements
- Debugging agent crashes

### 🔥 Performance Tips

1. **Cache is automatically enabled** - No action needed
2. **Context filtering is automatic** - Reduces tokens by 62%
3. **Batch operations when possible** - Further improves efficiency

### 📈 Real-World Impact

**"Push" Command Performance:**
- Before: 800ms (4 agents × 200ms)
- After: 55ms (4 agents × ~14ms)
- **Result: 14.5x faster workflows**

### 🛠️ Troubleshooting

**If experiencing slow performance:**
1. Verify LOCAL mode is active: `claude-pm config --show`
2. Check cache status: `claude-pm cache --status`
3. Run benchmarks: `python scripts/benchmark_orchestration.py`

### 📚 More Information
- [Full Performance Analysis Report](./performance-analysis-report.md)
- [Performance Visualizations](./performance-visualizations.md)
- [Benchmarking Scripts](../scripts/)