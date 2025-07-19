#!/usr/bin/env python3
"""
Performance Benchmarking Tool for Refactoring Validation

Measures and compares performance metrics before and after refactoring
to ensure no performance degradation occurs.

Created: 2025-07-18
Author: QA Agent
"""

import os
import sys
import time
import json
import psutil
import tracemalloc
import gc
import statistics
from typing import Dict, List, Callable, Any, Tuple, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import importlib
import subprocess
import threading
import queue

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    test_name: str
    metric: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class PerformanceProfile:
    """Complete performance profile for a module"""
    module_name: str
    import_time: float
    memory_usage: Dict[str, float]
    cpu_usage: Dict[str, float]
    function_benchmarks: Dict[str, Dict[str, float]]
    timestamp: datetime = field(default_factory=datetime.now)
    

class PerformanceBenchmark:
    """Performance benchmarking for refactoring validation"""
    
    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.benchmarks_dir = project_root / "tests" / "refactoring_harness" / "benchmarks"
        self.benchmarks_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.warmup_runs = 3
        self.benchmark_runs = 10
        self.cpu_sample_interval = 0.1  # seconds
        
    def measure_import_time(self, module_name: str, runs: int = 10) -> Dict[str, float]:
        """Measure module import time"""
        times = []
        
        for i in range(runs + self.warmup_runs):
            # Clear any cached imports
            if module_name in sys.modules:
                del sys.modules[module_name]
                
            # Force garbage collection
            gc.collect()
            
            start_time = time.perf_counter()
            try:
                importlib.import_module(module_name)
                end_time = time.perf_counter()
                
                # Skip warmup runs
                if i >= self.warmup_runs:
                    times.append(end_time - start_time)
                    
            except Exception as e:
                print(f"⚠️  Error importing {module_name}: {e}")
                return {}
                
        if not times:
            return {}
            
        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times),
            'runs': len(times)
        }
        
    def measure_memory_usage(self, module_name: str) -> Dict[str, float]:
        """Measure memory usage of a module"""
        # Clear any cached imports
        if module_name in sys.modules:
            del sys.modules[module_name]
            
        gc.collect()
        
        # Start memory tracking
        tracemalloc.start()
        
        try:
            # Get baseline memory
            baseline = tracemalloc.get_traced_memory()
            
            # Import module
            module = importlib.import_module(module_name)
            
            # Get peak memory
            current, peak = tracemalloc.get_traced_memory()
            
            # Stop tracking
            tracemalloc.stop()
            
            return {
                'import_memory_mb': (current - baseline[0]) / 1024 / 1024,
                'peak_memory_mb': (peak - baseline[1]) / 1024 / 1024,
                'current_memory_mb': current / 1024 / 1024
            }
            
        except Exception as e:
            tracemalloc.stop()
            print(f"⚠️  Error measuring memory for {module_name}: {e}")
            return {}
            
    def measure_function_performance(self, func: Callable, args: tuple = (), 
                                   kwargs: dict = None, runs: int = 10) -> Dict[str, float]:
        """Measure performance of a specific function"""
        if kwargs is None:
            kwargs = {}
            
        times = []
        memory_usage = []
        
        for i in range(runs + self.warmup_runs):
            gc.collect()
            
            # Measure memory
            tracemalloc.start()
            baseline = tracemalloc.get_traced_memory()[0]
            
            # Measure time
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                
                # Get memory usage
                current = tracemalloc.get_traced_memory()[0]
                tracemalloc.stop()
                
                # Skip warmup runs
                if i >= self.warmup_runs:
                    times.append(end_time - start_time)
                    memory_usage.append((current - baseline) / 1024 / 1024)
                    
            except Exception as e:
                tracemalloc.stop()
                print(f"⚠️  Error benchmarking function: {e}")
                return {}
                
        if not times:
            return {}
            
        return {
            'time_mean_ms': statistics.mean(times) * 1000,
            'time_median_ms': statistics.median(times) * 1000,
            'time_stdev_ms': statistics.stdev(times) * 1000 if len(times) > 1 else 0,
            'time_min_ms': min(times) * 1000,
            'time_max_ms': max(times) * 1000,
            'memory_mean_mb': statistics.mean(memory_usage),
            'memory_max_mb': max(memory_usage),
            'runs': len(times)
        }
        
    def measure_cpu_usage(self, func: Callable, duration: float = 5.0) -> Dict[str, float]:
        """Measure CPU usage during function execution"""
        cpu_samples = []
        stop_event = threading.Event()
        
        def sample_cpu():
            """Sample CPU usage in a separate thread"""
            process = psutil.Process()
            while not stop_event.is_set():
                cpu_samples.append(process.cpu_percent(interval=self.cpu_sample_interval))
                
        # Start CPU sampling
        cpu_thread = threading.Thread(target=sample_cpu)
        cpu_thread.start()
        
        # Run function for specified duration
        start_time = time.time()
        iterations = 0
        
        try:
            while time.time() - start_time < duration:
                func()
                iterations += 1
        except Exception as e:
            print(f"⚠️  Error during CPU measurement: {e}")
        finally:
            stop_event.set()
            cpu_thread.join()
            
        if not cpu_samples:
            return {}
            
        return {
            'cpu_mean': statistics.mean(cpu_samples),
            'cpu_median': statistics.median(cpu_samples),
            'cpu_max': max(cpu_samples),
            'cpu_stdev': statistics.stdev(cpu_samples) if len(cpu_samples) > 1 else 0,
            'iterations': iterations,
            'iterations_per_second': iterations / duration
        }
        
    def create_performance_profile(self, module_path: str) -> PerformanceProfile:
        """Create a complete performance profile for a module"""
        print(f"\n📊 Creating performance profile for {module_path}")
        
        module_name = module_path.replace('/', '.').replace('.py', '')
        
        # Import time
        print("  ⏱️  Measuring import time...")
        import_stats = self.measure_import_time(module_name, runs=self.benchmark_runs)
        import_time = import_stats.get('median', 0)
        
        # Memory usage
        print("  💾 Measuring memory usage...")
        memory_usage = self.measure_memory_usage(module_name)
        
        # CPU usage (import the module first)
        cpu_usage = {}
        try:
            module = importlib.import_module(module_name)
            
            # Find key functions to benchmark
            print("  🔧 Benchmarking key functions...")
            function_benchmarks = self._benchmark_module_functions(module)
            
        except Exception as e:
            print(f"  ⚠️  Error profiling module: {e}")
            function_benchmarks = {}
            
        profile = PerformanceProfile(
            module_name=module_name,
            import_time=import_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            function_benchmarks=function_benchmarks
        )
        
        # Save profile
        profile_file = self.benchmarks_dir / f"{module_name}_profile.json"
        with open(profile_file, 'w') as f:
            json.dump(asdict(profile), f, indent=2, default=str)
            
        print(f"  ✅ Profile saved: {profile_file}")
        return profile
        
    def _benchmark_module_functions(self, module) -> Dict[str, Dict[str, float]]:
        """Benchmark key functions in a module"""
        benchmarks = {}
        
        # Define key functions to benchmark for each module
        function_benchmarks = {
            'claude_pm.services.parent_directory_manager': [
                ('ParentDirectoryManager.__init__', [], {}),
                ('ParentDirectoryManager._initialize', [], {}),
            ],
            'claude_pm.core.agent_registry': [
                ('AgentRegistry.__init__', [], {}),
                ('AgentRegistry.listAgents', [], {}),
            ],
            # Add more module-specific benchmarks
        }
        
        module_name = module.__name__
        if module_name in function_benchmarks:
            for func_path, args, kwargs in function_benchmarks[module_name]:
                try:
                    # Navigate to the function
                    obj = module
                    for part in func_path.split('.'):
                        obj = getattr(obj, part)
                        
                    # Benchmark it
                    if callable(obj):
                        result = self.measure_function_performance(obj, args, kwargs, self.benchmark_runs)
                        if result:
                            benchmarks[func_path] = result
                            
                except Exception as e:
                    print(f"    ⚠️  Could not benchmark {func_path}: {e}")
                    
        return benchmarks
        
    def compare_profiles(self, before_profile: PerformanceProfile, 
                        after_profile: PerformanceProfile, 
                        threshold: float = 0.1) -> Dict[str, Any]:
        """Compare two performance profiles and check for regressions"""
        comparison = {
            'module': before_profile.module_name,
            'regressions': [],
            'improvements': [],
            'details': {}
        }
        
        # Compare import time
        if before_profile.import_time > 0:
            import_ratio = after_profile.import_time / before_profile.import_time
            comparison['details']['import_time_ratio'] = import_ratio
            
            if import_ratio > (1 + threshold):
                comparison['regressions'].append({
                    'metric': 'import_time',
                    'before': before_profile.import_time,
                    'after': after_profile.import_time,
                    'degradation': f"{(import_ratio - 1) * 100:.1f}%"
                })
            elif import_ratio < (1 - threshold):
                comparison['improvements'].append({
                    'metric': 'import_time',
                    'before': before_profile.import_time,
                    'after': after_profile.import_time,
                    'improvement': f"{(1 - import_ratio) * 100:.1f}%"
                })
                
        # Compare memory usage
        before_mem = before_profile.memory_usage.get('import_memory_mb', 0)
        after_mem = after_profile.memory_usage.get('import_memory_mb', 0)
        
        if before_mem > 0:
            mem_ratio = after_mem / before_mem
            comparison['details']['memory_ratio'] = mem_ratio
            
            if mem_ratio > (1 + threshold):
                comparison['regressions'].append({
                    'metric': 'memory_usage',
                    'before': before_mem,
                    'after': after_mem,
                    'degradation': f"{(mem_ratio - 1) * 100:.1f}%"
                })
                
        # Compare function benchmarks
        for func_name in before_profile.function_benchmarks:
            if func_name in after_profile.function_benchmarks:
                before_time = before_profile.function_benchmarks[func_name].get('time_median_ms', 0)
                after_time = after_profile.function_benchmarks[func_name].get('time_median_ms', 0)
                
                if before_time > 0:
                    time_ratio = after_time / before_time
                    
                    if time_ratio > (1 + threshold):
                        comparison['regressions'].append({
                            'metric': f'{func_name}_time',
                            'before': before_time,
                            'after': after_time,
                            'degradation': f"{(time_ratio - 1) * 100:.1f}%"
                        })
                        
        comparison['passed'] = len(comparison['regressions']) == 0
        return comparison
        
    def generate_benchmark_report(self, comparisons: List[Dict[str, Any]], 
                                 output_file: Optional[str] = None) -> str:
        """Generate a benchmark comparison report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_file:
            output_file = self.benchmarks_dir / f"benchmark_report_{timestamp}.md"
        else:
            output_file = Path(output_file)
            
        report_lines = [
            "# Performance Benchmark Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Summary\n"
        ]
        
        # Count regressions
        total_modules = len(comparisons)
        modules_with_regressions = sum(1 for c in comparisons if c['regressions'])
        total_regressions = sum(len(c['regressions']) for c in comparisons)
        total_improvements = sum(len(c['improvements']) for c in comparisons)
        
        report_lines.extend([
            f"- Modules Tested: {total_modules}",
            f"- Modules with Regressions: {modules_with_regressions}",
            f"- Total Regressions: {total_regressions}",
            f"- Total Improvements: {total_improvements}",
            ""
        ])
        
        # Detailed results
        report_lines.append("## Detailed Results\n")
        
        for comparison in comparisons:
            module = comparison['module']
            status = "✅ PASSED" if comparison['passed'] else "❌ REGRESSIONS DETECTED"
            
            report_lines.append(f"### {module}: {status}\n")
            
            if comparison['regressions']:
                report_lines.append("**Performance Regressions:**")
                for reg in comparison['regressions']:
                    report_lines.append(f"- {reg['metric']}: {reg['before']:.3f} → {reg['after']:.3f} "
                                      f"({reg['degradation']} slower)")
                report_lines.append("")
                
            if comparison['improvements']:
                report_lines.append("**Performance Improvements:**")
                for imp in comparison['improvements']:
                    report_lines.append(f"- {imp['metric']}: {imp['before']:.3f} → {imp['after']:.3f} "
                                      f"({imp['improvement']} faster)")
                report_lines.append("")
                
            if comparison['details']:
                report_lines.append("**Details:**")
                for key, value in comparison['details'].items():
                    report_lines.append(f"- {key}: {value:.3f}")
                report_lines.append("")
                
        # Recommendations
        if total_regressions > 0:
            report_lines.extend([
                "\n## Recommendations\n",
                "⚠️  Performance regressions detected. Consider:",
                "- Profiling the affected functions to identify bottlenecks",
                "- Reviewing algorithm changes in refactored code",
                "- Checking for unnecessary object creation or loops",
                "- Verifying that optimizations weren't lost during refactoring",
                ""
            ])
            
        # Write report
        report_content = "\n".join(report_lines)
        with open(output_file, 'w') as f:
            f.write(report_content)
            
        print(f"\n📄 Benchmark report generated: {output_file}")
        return report_content
        

def main():
    """Example usage of the performance benchmark tool"""
    benchmark = PerformanceBenchmark()
    
    # Example: Create a performance profile
    # profile = benchmark.create_performance_profile('claude_pm/services/parent_directory_manager.py')
    
    # Example: Compare before and after profiles
    # comparison = benchmark.compare_profiles(before_profile, after_profile)
    # benchmark.generate_benchmark_report([comparison])
    

if __name__ == "__main__":
    main()