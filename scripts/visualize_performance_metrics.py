#!/usr/bin/env python3
"""Visualize performance metrics in a readable format."""

import json
from pathlib import Path
from datetime import datetime

def load_metrics():
    """Load performance metrics from analysis file."""
    metrics_file = Path('/Users/masa/Projects/claude-multiagent-pm/logs/performance_benchmarks_analysis.json')
    with open(metrics_file, 'r') as f:
        return json.load(f)

def print_section(title, width=60):
    """Print a formatted section header."""
    print(f"\n{'=' * width}")
    print(f"{title.upper():^{width}}")
    print(f"{'=' * width}")

def print_subsection(title, width=60):
    """Print a formatted subsection header."""
    print(f"\n{title}")
    print(f"{'-' * len(title)}")

def format_ms(value):
    """Format milliseconds value."""
    if value < 1:
        return f"{value * 1000:.1f}μs"
    elif value < 1000:
        return f"{value:.2f}ms"
    else:
        return f"{value / 1000:.2f}s"

def main():
    """Display performance metrics."""
    metrics = load_metrics()
    perf = metrics['performance_metrics']
    
    print_section("Claude PM Framework Performance Analysis", 70)
    print(f"\nAnalysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Orchestration Mode Comparison
    print_section("Orchestration Mode Performance", 70)
    
    subprocess = perf['orchestration_modes']['subprocess_mode']['observed_metrics']
    local = perf['orchestration_modes']['local_mode']['observed_metrics']
    
    print("\n┌─────────────────────┬────────────────┬────────────────┐")
    print("│ Metric              │ Subprocess     │ LOCAL Mode     │")
    print("├─────────────────────┼────────────────┼────────────────┤")
    print(f"│ Average Time        │ {format_ms(subprocess['average_execution_time_ms']):>14} │ {format_ms(local['average_execution_time_ms']):>14} │")
    print(f"│ Min Time            │ {format_ms(subprocess['min_execution_time_ms']):>14} │ {format_ms(local['min_execution_time_ms']):>14} │")
    print(f"│ Max Time            │ {format_ms(subprocess['max_execution_time_ms']):>14} │ {format_ms(local['max_execution_time_ms']):>14} │")
    print(f"│ Memory Overhead     │ {subprocess['memory_overhead_mb']:>12} MB │ {local['memory_overhead_mb']:>12} MB │")
    print("└─────────────────────┴────────────────┴────────────────┘")
    
    # 2. Performance Improvements
    improvements = perf['performance_improvements']['local_vs_subprocess']
    print_subsection("\nPerformance Improvements")
    print(f"  • Speedup Factor: {improvements['average_speedup']:.1f}x faster")
    print(f"  • Improvement: {improvements['percentage_improvement']:.1f}%")
    print(f"  • Response Time Reduction: {format_ms(improvements['response_time_reduction_ms'])}")
    
    # 3. Component Timing Breakdown
    print_section("Component Timing Analysis", 70)
    
    components = perf['component_timings']
    print("\n┌─────────────────────────┬──────────────┬─────────────────────────┐")
    print("│ Component               │ Average Time │ Notes                   │")
    print("├─────────────────────────┼──────────────┼─────────────────────────┤")
    
    for comp_name, comp_data in components.items():
        name = comp_data['description'].split()[0:3]
        name = ' '.join(name)[:23]
        time = format_ms(comp_data['average_ms'])
        
        if 'token_reduction_percent' in comp_data:
            note = f"{comp_data['token_reduction_percent']:.1f}% token reduction"
        elif 'impact' in comp_data:
            note = comp_data['impact']
        else:
            note = f"{comp_data.get('samples', 'N/A')} samples"
            
        print(f"│ {name:<23} │ {time:>12} │ {note:<23} │")
    
    print("└─────────────────────────┴──────────────┴─────────────────────────┘")
    
    # 4. Performance Benchmarks
    print_section("Performance Benchmarks", 70)
    
    benchmarks = perf['benchmarks']
    for bench_name, bench_data in benchmarks.items():
        print_subsection(f"\n{bench_name.replace('_', ' ').title()}")
        print(f"  • Subprocess: {format_ms(bench_data['subprocess_ms'])}")
        print(f"  • LOCAL Mode: {format_ms(bench_data['local_ms'])}")
        print(f"  • Improvement: {bench_data['improvement_factor']:.1f}x faster")
        if 'note' in bench_data:
            print(f"  • Note: {bench_data['note']}")
    
    # 5. Cache Performance
    print_section("Cache Performance (Claimed)", 70)
    
    cache = perf['cache_performance']['shared_prompt_cache']
    print(f"\n  • Claim: {cache['claim']}")
    print(f"  • Status: {cache['validation_status']}")
    print("\n  Expected Metrics:")
    for metric, value in cache['expected_metrics'].items():
        if metric.endswith('_ms'):
            print(f"    - {metric.replace('_', ' ').title()}: {format_ms(value)}")
        else:
            print(f"    - {metric.replace('_', ' ').title()}: {value}%")
    
    # 6. Memory Scaling
    print_section("Memory Usage Patterns", 70)
    
    memory = perf['memory_usage']
    print("\n┌─────────────────┬────────────────┬────────────────┐")
    print("│ Mode            │ Base Memory    │ Per Agent      │")
    print("├─────────────────┼────────────────┼────────────────┤")
    print(f"│ Subprocess      │ {memory['subprocess_mode']['base_memory_mb']:>12} MB │ {memory['subprocess_mode']['per_agent_mb']:>12} MB │")
    print(f"│ LOCAL           │ {memory['local_mode']['base_memory_mb']:>12} MB │ {memory['local_mode']['per_agent_mb']:>12} MB │")
    print("└─────────────────┴────────────────┴────────────────┘")
    
    # 7. Summary and Recommendations
    print_section("Summary & Recommendations", 70)
    
    print("\n📊 Key Findings:")
    print(f"  ✓ LOCAL mode is {improvements['average_speedup']:.1f}x faster than subprocess mode")
    print(f"  ✓ Response time improvement of {improvements['percentage_improvement']:.1f}%")
    print(f"  ✓ Context filtering reduces tokens by ~62%")
    print(f"  ✓ Memory usage 25x more efficient in LOCAL mode")
    
    print("\n💡 Recommendations:")
    for rec in metrics['recommendations']:
        print(f"  • {rec}")
    
    # 8. Visual Performance Bar
    print_section("Visual Performance Comparison", 70)
    
    # Create a simple bar chart
    subprocess_bar_length = 50
    local_bar_length = int(50 * (local['average_execution_time_ms'] / subprocess['average_execution_time_ms']))
    
    print(f"\nSubprocess Mode ({format_ms(subprocess['average_execution_time_ms'])})")
    print(f"{'█' * subprocess_bar_length}")
    
    print(f"\nLOCAL Mode ({format_ms(local['average_execution_time_ms'])})")
    print(f"{'█' * local_bar_length}")
    
    print(f"\n🚀 Performance Gain: {subprocess_bar_length - local_bar_length} units ({improvements['percentage_improvement']:.1f}%)")

if __name__ == '__main__':
    main()