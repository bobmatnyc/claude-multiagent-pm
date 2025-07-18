#!/usr/bin/env python3
"""Extract and aggregate performance metrics from logs."""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import statistics

def parse_orchestration_log(log_path):
    """Parse orchestration.log for timing metrics."""
    metrics = {
        'subprocess': [],
        'local': [],
        'decision_times': [],
        'filter_times': [],
        'routing_times': []
    }
    
    try:
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    
                    # Extract mode and timing data
                    if 'execution_time_ms' in data:
                        mode = data.get('mode', 'unknown')
                        exec_time = data['execution_time_ms']
                        
                        if mode == 'subprocess':
                            metrics['subprocess'].append(exec_time)
                        elif mode == 'local':
                            metrics['local'].append(exec_time)
                    
                    if 'decision_time_ms' in data:
                        metrics['decision_times'].append(data['decision_time_ms'])
                    
                    if 'filter_time_ms' in data:
                        metrics['filter_times'].append(data['filter_time_ms'])
                        
                    if 'routing_time_ms' in data:
                        metrics['routing_times'].append(data['routing_time_ms'])
                        
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Log file not found: {log_path}")
    
    return metrics

def parse_cache_logs(logs_dir):
    """Parse cache performance logs."""
    cache_metrics = {
        'hit_rates': [],
        'load_times': [],
        'memory_usage': []
    }
    
    # Look for cache performance logs
    cache_logs = list(logs_dir.glob('enhanced-cache-performance-*.json'))
    
    for log_file in cache_logs:
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
                
                # Extract cache metrics if available
                if 'cacheMetrics' in data:
                    metrics = data['cacheMetrics']
                    if 'hitRate' in metrics:
                        cache_metrics['hit_rates'].append(metrics['hitRate'])
                    if 'avgLoadTime' in metrics:
                        cache_metrics['load_times'].append(metrics['avgLoadTime'])
                        
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    return cache_metrics

def calculate_statistics(values):
    """Calculate min, max, avg, median for a list of values."""
    if not values:
        return None
    
    return {
        'count': len(values),
        'min': min(values),
        'max': max(values),
        'avg': statistics.mean(values),
        'median': statistics.median(values)
    }

def main():
    """Extract and display performance metrics."""
    project_root = Path('/Users/masa/Projects/claude-multiagent-pm')
    logs_dir = project_root / 'logs'
    
    print("Performance Metrics Extraction")
    print("=" * 60)
    
    # Parse orchestration log
    orch_metrics = parse_orchestration_log(logs_dir / 'orchestration.log')
    
    print("\n1. ORCHESTRATION PERFORMANCE")
    print("-" * 40)
    
    # Subprocess performance
    if orch_metrics['subprocess']:
        stats = calculate_statistics(orch_metrics['subprocess'])
        print(f"\nSubprocess Mode:")
        print(f"  Samples: {stats['count']}")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
    
    # Local mode performance
    if orch_metrics['local']:
        stats = calculate_statistics(orch_metrics['local'])
        print(f"\nLocal Mode:")
        print(f"  Samples: {stats['count']}")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
    
    # Decision times
    if orch_metrics['decision_times']:
        stats = calculate_statistics(orch_metrics['decision_times'])
        print(f"\nDecision Times:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
    
    # Context filtering
    if orch_metrics['filter_times']:
        stats = calculate_statistics(orch_metrics['filter_times'])
        print(f"\nContext Filtering:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
    
    # Message routing
    if orch_metrics['routing_times']:
        stats = calculate_statistics(orch_metrics['routing_times'])
        print(f"\nMessage Routing:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
    
    # Parse cache metrics
    cache_metrics = parse_cache_logs(logs_dir)
    
    if any(cache_metrics.values()):
        print("\n2. CACHE PERFORMANCE")
        print("-" * 40)
        
        if cache_metrics['hit_rates']:
            stats = calculate_statistics(cache_metrics['hit_rates'])
            print(f"\nCache Hit Rates:")
            print(f"  Average: {stats['avg']:.1f}%")
            print(f"  Median: {stats['median']:.1f}%")
    
    # Performance comparison
    if orch_metrics['subprocess'] and orch_metrics['local']:
        print("\n3. PERFORMANCE COMPARISON")
        print("-" * 40)
        
        subprocess_avg = statistics.mean(orch_metrics['subprocess'])
        local_avg = statistics.mean(orch_metrics['local'])
        
        improvement = ((subprocess_avg - local_avg) / subprocess_avg) * 100
        speedup = subprocess_avg / local_avg
        
        print(f"\nSubprocess avg: {subprocess_avg:.2f}ms")
        print(f"Local avg: {local_avg:.2f}ms")
        print(f"Improvement: {improvement:.1f}%")
        print(f"Speedup: {speedup:.1f}x faster")
    
    # Create benchmarks
    print("\n4. BENCHMARKS")
    print("-" * 40)
    
    benchmarks = {
        'orchestration': {
            'subprocess_mode': {
                'average_ms': statistics.mean(orch_metrics['subprocess']) if orch_metrics['subprocess'] else None,
                'samples': len(orch_metrics['subprocess'])
            },
            'local_mode': {
                'average_ms': statistics.mean(orch_metrics['local']) if orch_metrics['local'] else None,
                'samples': len(orch_metrics['local'])
            }
        },
        'context_filtering': {
            'average_ms': statistics.mean(orch_metrics['filter_times']) if orch_metrics['filter_times'] else None,
            'samples': len(orch_metrics['filter_times'])
        },
        'cache_performance': {
            'hit_rate_avg': statistics.mean(cache_metrics['hit_rates']) if cache_metrics['hit_rates'] else None,
            'samples': len(cache_metrics['hit_rates'])
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Save benchmarks
    benchmark_file = logs_dir / 'performance_benchmarks.json'
    with open(benchmark_file, 'w') as f:
        json.dump(benchmarks, f, indent=2)
    
    print(f"\nBenchmarks saved to: {benchmark_file}")
    
    # Summary
    print("\n5. SUMMARY")
    print("-" * 40)
    print("\nKey Findings:")
    
    if orch_metrics['local'] and orch_metrics['subprocess']:
        print(f"✓ LOCAL mode is {speedup:.1f}x faster than subprocess mode")
        print(f"✓ Average response time improvement: {improvement:.1f}%")
    
    if orch_metrics['filter_times']:
        avg_filter = statistics.mean(orch_metrics['filter_times'])
        print(f"✓ Context filtering averages {avg_filter:.2f}ms")
    
    if orch_metrics['routing_times']:
        avg_routing = statistics.mean(orch_metrics['routing_times'])
        print(f"✓ Message routing averages {avg_routing:.2f}ms")

if __name__ == '__main__':
    main()