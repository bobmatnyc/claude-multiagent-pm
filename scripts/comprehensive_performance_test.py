#!/usr/bin/env python3
"""Comprehensive performance testing for Claude PM Framework."""

import asyncio
import time
import json
import psutil
import os
from pathlib import Path
import statistics
from datetime import datetime

# Add project root to Python path
import sys
sys.path.insert(0, '/Users/masa/Projects/claude-multiagent-pm')

from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator
from claude_pm.services.shared_prompt_cache import SharedPromptCache

class PerformanceTester:
    """Test various performance scenarios."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
        self.process = psutil.Process()
        
    def measure_memory(self):
        """Get current memory usage."""
        return {
            'rss_mb': self.process.memory_info().rss / 1024 / 1024,
            'percent': self.process.memory_percent()
        }
    
    async def test_subprocess_mode(self, iterations=5):
        """Test subprocess mode performance."""
        print("\n1. SUBPROCESS MODE TEST")
        print("-" * 40)
        
        # Force subprocess mode
        os.environ['CLAUDE_PM_ORCHESTRATION'] = 'false'
        
        timings = []
        memory_usage = []
        
        for i in range(iterations):
            orchestrator = BackwardsCompatibleOrchestrator()
            
            start_time = time.time()
            start_memory = self.measure_memory()
            
            result = await orchestrator.delegate_to_agent(
                agent_type="research",
                task_description=f"Test research task {i}",
                project_context="Test context with some data",
                requirements=["Requirement 1", "Requirement 2"],
                deliverables=["Deliverable 1"]
            )
            
            end_time = time.time()
            end_memory = self.measure_memory()
            
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            timings.append(execution_time)
            memory_usage.append(end_memory['rss_mb'] - start_memory['rss_mb'])
            
            print(f"  Iteration {i+1}: {execution_time:.2f}ms")
        
        avg_time = statistics.mean(timings)
        avg_memory = statistics.mean(memory_usage)
        
        self.results['tests'].append({
            'name': 'subprocess_mode',
            'iterations': iterations,
            'avg_time_ms': avg_time,
            'min_time_ms': min(timings),
            'max_time_ms': max(timings),
            'avg_memory_delta_mb': avg_memory
        })
        
        print(f"\n  Average: {avg_time:.2f}ms")
        print(f"  Memory delta: {avg_memory:.2f}MB")
        
        return timings
    
    async def test_local_mode(self, iterations=5):
        """Test LOCAL mode performance."""
        print("\n2. LOCAL MODE TEST")
        print("-" * 40)
        
        # Enable LOCAL mode (default)
        if 'CLAUDE_PM_ORCHESTRATION' in os.environ:
            del os.environ['CLAUDE_PM_ORCHESTRATION']
        
        timings = []
        memory_usage = []
        
        for i in range(iterations):
            orchestrator = BackwardsCompatibleOrchestrator()
            
            start_time = time.time()
            start_memory = self.measure_memory()
            
            result = await orchestrator.delegate_to_agent(
                agent_type="research",
                task_description=f"Test research task {i}",
                project_context="Test context with some data",
                requirements=["Requirement 1", "Requirement 2"],
                deliverables=["Deliverable 1"]
            )
            
            end_time = time.time()
            end_memory = self.measure_memory()
            
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            timings.append(execution_time)
            memory_usage.append(end_memory['rss_mb'] - start_memory['rss_mb'])
            
            print(f"  Iteration {i+1}: {execution_time:.2f}ms")
        
        avg_time = statistics.mean(timings)
        avg_memory = statistics.mean(memory_usage)
        
        self.results['tests'].append({
            'name': 'local_mode',
            'iterations': iterations,
            'avg_time_ms': avg_time,
            'min_time_ms': min(timings),
            'max_time_ms': max(timings),
            'avg_memory_delta_mb': avg_memory
        })
        
        print(f"\n  Average: {avg_time:.2f}ms")
        print(f"  Memory delta: {avg_memory:.2f}MB")
        
        return timings
    
    async def test_cache_performance(self):
        """Test shared prompt cache performance."""
        print("\n3. CACHE PERFORMANCE TEST")
        print("-" * 40)
        
        cache = SharedPromptCache(max_size=100, max_memory_mb=50)
        
        # Test cache write performance
        write_times = []
        for i in range(100):
            start = time.time()
            cache.set(f"test_key_{i}", f"Test value {i}" * 100)
            write_times.append((time.time() - start) * 1000)
        
        # Test cache read performance (hits)
        hit_times = []
        for i in range(100):
            start = time.time()
            value = cache.get(f"test_key_{i}")
            if value:
                hit_times.append((time.time() - start) * 1000)
        
        # Test cache misses
        miss_times = []
        for i in range(100, 200):
            start = time.time()
            value = cache.get(f"test_key_{i}")
            miss_times.append((time.time() - start) * 1000)
        
        stats = cache.get_stats()
        
        self.results['tests'].append({
            'name': 'cache_performance',
            'write_avg_ms': statistics.mean(write_times),
            'hit_avg_ms': statistics.mean(hit_times),
            'miss_avg_ms': statistics.mean(miss_times),
            'hit_rate': stats['hit_rate'],
            'items_count': stats['items']
        })
        
        print(f"  Write avg: {statistics.mean(write_times):.3f}ms")
        print(f"  Hit avg: {statistics.mean(hit_times):.3f}ms")
        print(f"  Miss avg: {statistics.mean(miss_times):.3f}ms")
        print(f"  Hit rate: {stats['hit_rate']:.1f}%")
    
    async def test_context_filtering(self):
        """Test context filtering with various sizes."""
        print("\n4. CONTEXT FILTERING TEST")
        print("-" * 40)
        
        from claude_pm.orchestration.context_manager import ContextManager
        
        context_manager = ContextManager()
        
        # Create contexts of different sizes
        test_sizes = [
            ("1K tokens", "x" * 4000),      # ~1K tokens
            ("10K tokens", "x" * 40000),     # ~10K tokens
            ("50K tokens", "x" * 200000),    # ~50K tokens
        ]
        
        for size_name, context in test_sizes:
            start = time.time()
            filtered = await context_manager.filter_context_for_agent(
                "research",
                {
                    "user_request": "Test request",
                    "project_context": context,
                    "framework_docs": "Framework documentation"
                }
            )
            filter_time = (time.time() - start) * 1000
            
            print(f"  {size_name}: {filter_time:.2f}ms")
            
            self.results['tests'].append({
                'name': f'context_filter_{size_name}',
                'filter_time_ms': filter_time,
                'original_size': len(context),
                'filtered_size': len(str(filtered))
            })
    
    def calculate_summary(self, subprocess_times, local_times):
        """Calculate performance summary."""
        if subprocess_times and local_times:
            subprocess_avg = statistics.mean(subprocess_times)
            local_avg = statistics.mean(local_times)
            
            improvement = ((subprocess_avg - local_avg) / subprocess_avg) * 100
            speedup = subprocess_avg / local_avg
            
            self.results['summary'] = {
                'subprocess_avg_ms': subprocess_avg,
                'local_avg_ms': local_avg,
                'improvement_percent': improvement,
                'speedup_factor': speedup,
                'cache_claim_validation': None
            }
            
            # Validate 99.7% cache improvement claim
            # This would require comparing cached vs non-cached prompt loading
            # For now, we'll mark it as requiring further testing
            
            print("\n5. PERFORMANCE SUMMARY")
            print("-" * 40)
            print(f"  Subprocess avg: {subprocess_avg:.2f}ms")
            print(f"  Local avg: {local_avg:.2f}ms")
            print(f"  Improvement: {improvement:.1f}%")
            print(f"  Speedup: {speedup:.1f}x")
    
    async def run_all_tests(self):
        """Run all performance tests."""
        print("=" * 60)
        print("COMPREHENSIVE PERFORMANCE TESTING")
        print("=" * 60)
        
        # Run tests
        subprocess_times = await self.test_subprocess_mode()
        local_times = await self.test_local_mode()
        await self.test_cache_performance()
        await self.test_context_filtering()
        
        # Calculate summary
        self.calculate_summary(subprocess_times, local_times)
        
        # Save results
        output_file = Path('/Users/masa/Projects/claude-multiagent-pm/logs/performance_test_results.json')
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
        
        # Create CSV for easy analysis
        csv_file = Path('/Users/masa/Projects/claude-multiagent-pm/logs/performance_metrics.csv')
        with open(csv_file, 'w') as f:
            f.write("Test,Metric,Value\n")
            for test in self.results['tests']:
                test_name = test['name']
                for key, value in test.items():
                    if key != 'name' and isinstance(value, (int, float)):
                        f.write(f"{test_name},{key},{value}\n")
        
        print(f"CSV saved to: {csv_file}")

async def main():
    """Run performance tests."""
    tester = PerformanceTester()
    await tester.run_all_tests()

if __name__ == '__main__':
    asyncio.run(main())