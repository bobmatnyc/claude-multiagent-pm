"""
Memory Recall System Performance Tests

Comprehensive performance testing for the memory recall system including:
- Recall speed and accuracy validation
- Similarity matching performance
- Recommendation generation efficiency
- Concurrent operation handling
- Memory usage optimization
- Cache effectiveness
"""

import asyncio
import pytest
import time
import statistics
import threading
import gc
import uuid
from unittest.mock import Mock, AsyncMock
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from claude_pm.services.memory import (
    FlexibleMemoryService,
    MemoryRecallService,
    MemoryCategory,
    MemoryItem,
    MemoryQuery,
    create_memory_recall_service
)
from claude_pm.services.memory.memory_context_enhancer import (
    MemoryContextEnhancer,
    RecallTrigger,
    RecallConfig,
    MemoryContext
)
from claude_pm.services.memory.similarity_matcher import (
    SimilarityMatcher,
    SimilarityAlgorithm,
    MatchingConfig,
    SimilarityResult
)
from claude_pm.services.memory.recommendation_engine import (
    RecommendationEngine,
    RecommendationType,
    RecommendationConfig
)
from claude_pm.services.memory.performance_optimizer import (
    PerformanceOptimizer,
    OptimizationStrategy,
    PerformanceMetrics
)


@dataclass
class PerformanceTestResult:
    """Results from a performance test."""
    test_name: str
    operation_count: int
    total_time_seconds: float
    average_time_ms: float
    median_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    success_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_ops_per_second: float
    target_met: bool
    notes: str = ""


class PerformanceTestSuite:
    """Base class for performance test suites."""
    
    def __init__(self):
        self.results: List[PerformanceTestResult] = []
        self.resource_monitor: Optional[Dict[str, Any]] = None
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start_resource_monitoring(self):
        """Start monitoring system resources."""
        try:
            import psutil
            
            self.resource_monitor = {
                "cpu_percent": [],
                "memory_mb": [],
                "active": True,
                "process": psutil.Process()
            }
            
            def monitor():
                while self.resource_monitor["active"]:
                    try:
                        cpu = self.resource_monitor["process"].cpu_percent()
                        memory = self.resource_monitor["process"].memory_info().rss / 1024 / 1024
                        self.resource_monitor["cpu_percent"].append(cpu)
                        self.resource_monitor["memory_mb"].append(memory)
                        time.sleep(0.1)
                    except:
                        break
            
            self.monitor_thread = threading.Thread(target=monitor)
            self.monitor_thread.start()
            
        except ImportError:
            # psutil not available, skip resource monitoring
            pass
    
    def stop_resource_monitoring(self) -> Tuple[float, float]:
        """Stop resource monitoring and return averages."""
        if self.resource_monitor:
            self.resource_monitor["active"] = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5.0)
            
            avg_cpu = statistics.mean(self.resource_monitor["cpu_percent"]) if self.resource_monitor["cpu_percent"] else 0.0
            avg_memory = statistics.mean(self.resource_monitor["memory_mb"]) if self.resource_monitor["memory_mb"] else 0.0
            
            return avg_cpu, avg_memory
        
        return 0.0, 0.0
    
    def calculate_percentiles(self, times: List[float]) -> Dict[str, float]:
        """Calculate timing percentiles."""
        if not times:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        
        sorted_times = sorted(times)
        n = len(sorted_times)
        
        return {
            "p50": sorted_times[int(0.5 * n)],
            "p95": sorted_times[int(0.95 * n)],
            "p99": sorted_times[int(0.99 * n)]
        }
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report."""
        report = ["# Memory Recall System Performance Report\n"]
        
        if not self.results:
            report.append("No performance test results available.\n")
            return "\n".join(report)
        
        # Summary table
        report.append("## Performance Summary\n")
        report.append("| Test | Operations | Avg Time (ms) | P95 (ms) | Success Rate | Throughput (ops/s) | Target Met |")
        report.append("|------|------------|---------------|----------|--------------|-------------------|------------|")
        
        for result in self.results:
            report.append(
                f"| {result.test_name} | {result.operation_count} | "
                f"{result.average_time_ms:.1f} | {result.p95_time_ms:.1f} | "
                f"{result.success_rate:.1%} | {result.throughput_ops_per_second:.1f} | "
                f"{'✅' if result.target_met else '❌'} |"
            )
        
        # Detailed results
        report.append("\n## Detailed Results\n")
        for result in self.results:
            report.append(f"### {result.test_name}\n")
            report.append(f"- **Operations**: {result.operation_count}")
            report.append(f"- **Total Time**: {result.total_time_seconds:.2f}s")
            report.append(f"- **Average Time**: {result.average_time_ms:.1f}ms")
            report.append(f"- **Median Time**: {result.median_time_ms:.1f}ms")
            report.append(f"- **95th Percentile**: {result.p95_time_ms:.1f}ms")
            report.append(f"- **99th Percentile**: {result.p99_time_ms:.1f}ms")
            report.append(f"- **Success Rate**: {result.success_rate:.1%}")
            report.append(f"- **Throughput**: {result.throughput_ops_per_second:.1f} ops/second")
            report.append(f"- **Memory Usage**: {result.memory_usage_mb:.1f}MB")
            report.append(f"- **CPU Usage**: {result.cpu_usage_percent:.1f}%")
            report.append(f"- **Target Met**: {'✅ Yes' if result.target_met else '❌ No'}")
            if result.notes:
                report.append(f"- **Notes**: {result.notes}")
            report.append("")
        
        # Performance targets
        report.append("## Performance Targets\n")
        report.append("- **Memory Recall**: < 100ms average, < 200ms P95")
        report.append("- **Similarity Matching**: < 50ms per comparison")
        report.append("- **Recommendation Generation**: < 150ms")
        report.append("- **Concurrent Operations**: > 10 ops/second")
        report.append("- **Success Rate**: > 95%")
        report.append("- **Memory Usage**: < 500MB")
        report.append("- **CPU Usage**: < 80% average")
        
        return "\n".join(report)


class TestMemoryRecallPerformance(PerformanceTestSuite):
    """Test memory recall system performance."""
    
    @pytest.fixture
    async def populated_memory_service(self):
        """Create memory service with test data."""
        config = {
            "fallback_chain": ["memory"],
            "memory_enabled": True
        }
        
        service = FlexibleMemoryService(config)
        await service.initialize()
        
        # Populate with diverse test memories
        memory_ids = []
        
        # Pattern memories
        for i in range(50):
            memory_id = await service.add_memory(
                project_name="performance_test",
                content=f"Successful deployment pattern {i}: Used blue-green deployment strategy with automated rollback. Completed in {120 + i*2} seconds with 99.{90 + i%10}% uptime.",
                category=MemoryCategory.PATTERN,
                tags=["deployment", "blue-green", "success", f"pattern_{i}"],
                metadata={
                    "deployment_time": 120 + i*2,
                    "uptime_percentage": 99.90 + i%10/100,
                    "strategy": "blue-green",
                    "pattern_id": i
                }
            )
            memory_ids.append(memory_id)
        
        # Error memories
        for i in range(30):
            memory_id = await service.add_memory(
                project_name="performance_test",
                content=f"Error resolution {i}: Fixed {['timeout', 'connection', 'memory', 'cpu'][i%4]} issue by implementing {['retry logic', 'connection pooling', 'garbage collection', 'load balancing'][i%4]}. Resolution time: {30 + i*5} minutes.",
                category=MemoryCategory.ERROR,
                tags=["error", "resolution", ["timeout", "connection", "memory", "cpu"][i%4]],
                metadata={
                    "error_type": ["timeout", "connection", "memory", "cpu"][i%4],
                    "resolution_time_minutes": 30 + i*5,
                    "solution": ["retry logic", "connection pooling", "garbage collection", "load balancing"][i%4]
                }
            )
            memory_ids.append(memory_id)
        
        # Project memories
        for i in range(20):
            memory_id = await service.add_memory(
                project_name="performance_test",
                content=f"Project milestone {i}: Completed {['frontend', 'backend', 'database', 'api'][i%4]} implementation with {['React', 'Python', 'PostgreSQL', 'FastAPI'][i%4]} technology stack.",
                category=MemoryCategory.PROJECT,
                tags=["milestone", "implementation", ["frontend", "backend", "database", "api"][i%4]],
                metadata={
                    "milestone_id": i,
                    "technology": ["React", "Python", "PostgreSQL", "FastAPI"][i%4],
                    "component": ["frontend", "backend", "database", "api"][i%4]
                }
            )
            memory_ids.append(memory_id)
        
        yield service
        
        await service.cleanup()
    
    @pytest.fixture
    async def recall_service(self, populated_memory_service):
        """Create recall service with optimized config."""
        config = RecallConfig(
            max_recall_time_ms=100.0,
            max_memories_per_category=20,
            enable_caching=True,
            cache_ttl_seconds=300,
            performance_cache_size=1000
        )
        
        service = MemoryRecallService(populated_memory_service, config)
        await service.initialize()
        
        yield service
        
        await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_basic_recall_performance(self, recall_service):
        """Test basic recall operation performance."""
        operation_times = []
        successful_operations = 0
        
        self.start_resource_monitoring()
        
        try:
            start_time = time.time()
            
            # Execute multiple recall operations
            for i in range(100):
                operation_start = time.time()
                
                result = await recall_service.recall_for_operation(
                    project_name="performance_test",
                    operation_type="deployment",
                    operation_context={
                        "environment": "production",
                        "strategy": "blue-green",
                        "iteration": i
                    }
                )
                
                operation_time = (time.time() - operation_start) * 1000  # ms
                operation_times.append(operation_time)
                
                if result.success:
                    successful_operations += 1
            
            total_time = time.time() - start_time
            
        finally:
            avg_cpu, avg_memory = self.stop_resource_monitoring()
        
        # Calculate performance metrics
        percentiles = self.calculate_percentiles(operation_times)
        avg_time = statistics.mean(operation_times)
        success_rate = successful_operations / 100
        throughput = 100 / total_time
        
        # Performance targets
        target_avg_time = 100.0  # ms
        target_p95_time = 200.0  # ms
        target_success_rate = 0.95
        target_throughput = 5.0  # ops/second
        
        target_met = (
            avg_time <= target_avg_time and
            percentiles["p95"] <= target_p95_time and
            success_rate >= target_success_rate and
            throughput >= target_throughput
        )
        
        result = PerformanceTestResult(
            test_name="Basic Recall Performance",
            operation_count=100,
            total_time_seconds=total_time,
            average_time_ms=avg_time,
            median_time_ms=percentiles["p50"],
            p95_time_ms=percentiles["p95"],
            p99_time_ms=percentiles["p99"],
            success_rate=success_rate,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            throughput_ops_per_second=throughput,
            target_met=target_met,
            notes=f"Target: <{target_avg_time}ms avg, <{target_p95_time}ms P95, >{target_success_rate:.0%} success, >{target_throughput} ops/s"
        )
        
        self.results.append(result)
        
        # Assertions for test failure
        assert success_rate >= 0.90, f"Success rate too low: {success_rate:.1%}"
        assert avg_time <= 150.0, f"Average time too high: {avg_time:.1f}ms"
        assert percentiles["p95"] <= 300.0, f"P95 time too high: {percentiles['p95']:.1f}ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_recall_performance(self, recall_service):
        """Test concurrent recall operation performance."""
        operation_times = []
        successful_operations = 0
        
        self.start_resource_monitoring()
        
        try:
            start_time = time.time()
            
            # Create concurrent recall tasks
            tasks = []
            for i in range(50):
                task = self._timed_recall_operation(
                    recall_service,
                    i,
                    operation_times
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful operations
            for result in results:
                if not isinstance(result, Exception) and result:
                    successful_operations += 1
            
            total_time = time.time() - start_time
            
        finally:
            avg_cpu, avg_memory = self.stop_resource_monitoring()
        
        # Calculate metrics
        if operation_times:
            percentiles = self.calculate_percentiles(operation_times)
            avg_time = statistics.mean(operation_times)
        else:
            percentiles = {"p50": 0, "p95": 0, "p99": 0}
            avg_time = 0
        
        success_rate = successful_operations / 50
        throughput = 50 / total_time
        
        # Performance targets for concurrent operations
        target_avg_time = 150.0  # ms (higher due to concurrency)
        target_p95_time = 300.0  # ms
        target_success_rate = 0.90
        target_throughput = 10.0  # ops/second
        
        target_met = (
            avg_time <= target_avg_time and
            percentiles["p95"] <= target_p95_time and
            success_rate >= target_success_rate and
            throughput >= target_throughput
        )
        
        result = PerformanceTestResult(
            test_name="Concurrent Recall Performance",
            operation_count=50,
            total_time_seconds=total_time,
            average_time_ms=avg_time,
            median_time_ms=percentiles["p50"],
            p95_time_ms=percentiles["p95"],
            p99_time_ms=percentiles["p99"],
            success_rate=success_rate,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            throughput_ops_per_second=throughput,
            target_met=target_met,
            notes=f"Concurrent operations. Target: <{target_avg_time}ms avg, >{target_throughput} ops/s"
        )
        
        self.results.append(result)
        
        # Assertions
        assert success_rate >= 0.80, f"Concurrent success rate too low: {success_rate:.1%}"
        assert throughput >= 5.0, f"Concurrent throughput too low: {throughput:.1f} ops/s"
    
    async def _timed_recall_operation(self, recall_service, iteration, operation_times):
        """Execute a timed recall operation."""
        try:
            operation_start = time.time()
            
            result = await recall_service.recall_for_operation(
                project_name="performance_test",
                operation_type="concurrent_test",
                operation_context={
                    "iteration": iteration,
                    "test_type": "concurrent"
                }
            )
            
            operation_time = (time.time() - operation_start) * 1000  # ms
            operation_times.append(operation_time)
            
            return result.success
            
        except Exception as e:
            return False
    
    @pytest.mark.asyncio
    async def test_cache_effectiveness(self, recall_service):
        """Test cache effectiveness for repeated operations."""
        # Perform identical operations to test caching
        operation_context = {
            "environment": "production",
            "strategy": "blue-green",
            "test_type": "cache_test"
        }
        
        # First batch - populate cache
        first_batch_times = []
        for i in range(10):
            start_time = time.time()
            result = await recall_service.recall_for_operation(
                "performance_test", "deployment", operation_context
            )
            operation_time = (time.time() - start_time) * 1000
            first_batch_times.append(operation_time)
            assert result.success
        
        # Second batch - should hit cache
        second_batch_times = []
        for i in range(10):
            start_time = time.time()
            result = await recall_service.recall_for_operation(
                "performance_test", "deployment", operation_context
            )
            operation_time = (time.time() - start_time) * 1000
            second_batch_times.append(operation_time)
            assert result.success
        
        # Calculate improvement
        first_avg = statistics.mean(first_batch_times)
        second_avg = statistics.mean(second_batch_times)
        improvement_ratio = first_avg / second_avg if second_avg > 0 else 1.0
        
        # Cache should provide significant improvement
        assert improvement_ratio >= 1.2, f"Cache improvement insufficient: {improvement_ratio:.1f}x"
        assert second_avg <= 50.0, f"Cached operations too slow: {second_avg:.1f}ms"
        
        # Get cache statistics
        context_enhancer = recall_service.context_enhancer
        if hasattr(context_enhancer, 'get_performance_stats'):
            stats = context_enhancer.get_performance_stats()
            cache_hit_rate = stats.get("cache_hit_rate", 0.0)
            assert cache_hit_rate >= 0.5, f"Cache hit rate too low: {cache_hit_rate:.1%}"
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, recall_service):
        """Test memory usage stability under sustained load."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        self.start_resource_monitoring()
        
        try:
            # Sustained load test
            for batch in range(10):
                batch_tasks = []
                
                for i in range(20):
                    context = {
                        "batch": batch,
                        "iteration": i,
                        "data": f"sustained_load_test_{batch}_{i}"
                    }
                    
                    task = recall_service.recall_for_operation(
                        "performance_test", "sustained_load", context
                    )
                    batch_tasks.append(task)
                
                # Wait for batch completion
                await asyncio.gather(*batch_tasks)
                
                # Force garbage collection between batches
                gc.collect()
                
                # Brief pause to allow monitoring
                await asyncio.sleep(0.1)
            
        finally:
            avg_cpu, avg_memory = self.stop_resource_monitoring()
        
        # Memory usage should remain stable
        if self.resource_monitor and self.resource_monitor["memory_mb"]:
            memory_values = self.resource_monitor["memory_mb"]
            initial_memory = statistics.mean(memory_values[:5]) if len(memory_values) >= 5 else memory_values[0]
            final_memory = statistics.mean(memory_values[-5:]) if len(memory_values) >= 5 else memory_values[-1]
            
            memory_growth = final_memory - initial_memory
            memory_growth_percent = (memory_growth / initial_memory) * 100 if initial_memory > 0 else 0
            
            # Memory growth should be minimal
            assert memory_growth_percent <= 20.0, f"Excessive memory growth: {memory_growth_percent:.1f}%"
            assert final_memory <= 1000.0, f"Final memory usage too high: {final_memory:.1f}MB"


class TestSimilarityMatchingPerformance(PerformanceTestSuite):
    """Test similarity matching performance."""
    
    @pytest.fixture
    def sample_memories(self):
        """Create sample memories for similarity testing."""
        memories = []
        
        # Create diverse memory content for similarity testing
        templates = [
            "Deployment to {env} environment using {strategy} strategy completed in {time} seconds with {uptime}% uptime",
            "Error in {component} component: {error_type} resolved by implementing {solution}",
            "Code review for {feature} feature found {issues} issues, implemented {fixes} fixes",
            "Performance optimization in {module} improved response time by {improvement}%",
            "Database migration {version} completed successfully, {records} records processed",
            "API endpoint {endpoint} experiencing {issue}, fixed by {solution}",
            "Frontend component {component} refactored to use {technology} architecture",
            "Security audit identified {count} vulnerabilities, {fixed} fixed, {remaining} remaining"
        ]
        
        environments = ["development", "staging", "production"]
        strategies = ["blue-green", "canary", "rolling", "recreate"]
        components = ["frontend", "backend", "database", "api", "cache"]
        error_types = ["timeout", "connection", "memory", "cpu", "disk"]
        
        for i in range(200):
            template = templates[i % len(templates)]
            
            if "deployment" in template.lower():
                content = template.format(
                    env=environments[i % len(environments)],
                    strategy=strategies[i % len(strategies)],
                    time=120 + i % 300,
                    uptime=99.0 + (i % 99) / 100
                )
                category = MemoryCategory.PATTERN
                tags = ["deployment", environments[i % len(environments)], strategies[i % len(strategies)]]
            
            elif "error" in template.lower():
                content = template.format(
                    component=components[i % len(components)],
                    error_type=error_types[i % len(error_types)],
                    solution=f"solution_{i % 10}"
                )
                category = MemoryCategory.ERROR
                tags = ["error", components[i % len(components)], error_types[i % len(error_types)]]
            
            else:
                content = template.format(
                    feature=f"feature_{i % 20}",
                    issues=i % 10,
                    fixes=i % 8,
                    improvement=10 + i % 50,
                    module=components[i % len(components)],
                    version=f"v{1 + i % 5}.{i % 10}",
                    records=1000 + i * 100,
                    endpoint=f"/api/v1/endpoint_{i % 15}",
                    issue=error_types[i % len(error_types)],
                    solution=f"solution_{i % 8}",
                    component=f"component_{i % 12}",
                    technology=["React", "Vue", "Angular", "Svelte"][i % 4],
                    count=i % 20,
                    fixed=i % 15,
                    remaining=max(0, (i % 20) - (i % 15))
                )
                category = MemoryCategory.PROJECT
                tags = ["project", f"item_{i % 30}"]
            
            memory = MemoryItem(
                id=f"mem_{i}",
                content=content,
                category=category,
                tags=tags,
                metadata={"index": i, "test_type": "similarity_performance"},
                created_at=f"2025-07-{1 + i % 10:02d}T{10 + i % 12:02d}:00:00Z",
                updated_at=f"2025-07-{1 + i % 10:02d}T{10 + i % 12:02d}:00:00Z",
                project_name="similarity_test"
            )
            memories.append(memory)
        
        return memories
    
    @pytest.fixture
    def similarity_matcher(self):
        """Create similarity matcher with performance config."""
        config = MatchingConfig(
            min_similarity_threshold=0.1,
            max_results=50,
            enable_caching=True,
            cache_size=10000
        )
        return SimilarityMatcher(config)
    
    @pytest.mark.asyncio
    async def test_cosine_similarity_performance(self, similarity_matcher, sample_memories):
        """Test cosine similarity calculation performance."""
        query = "deployment to production using blue-green strategy"
        calculation_times = []
        successful_calculations = 0
        
        self.start_resource_monitoring()
        
        try:
            start_time = time.time()
            
            # Test similarity calculations
            for memory in sample_memories:
                calc_start = time.time()
                
                result = similarity_matcher.calculate_similarity(
                    query, memory, algorithm=SimilarityAlgorithm.COSINE
                )
                
                calc_time = (time.time() - calc_start) * 1000  # ms
                calculation_times.append(calc_time)
                
                if result.similarity_score >= 0.0:  # Valid result
                    successful_calculations += 1
            
            total_time = time.time() - start_time
            
        finally:
            avg_cpu, avg_memory = self.stop_resource_monitoring()
        
        # Calculate performance metrics
        percentiles = self.calculate_percentiles(calculation_times)
        avg_time = statistics.mean(calculation_times)
        success_rate = successful_calculations / len(sample_memories)
        throughput = len(sample_memories) / total_time
        
        # Performance targets
        target_avg_time = 5.0  # ms per calculation
        target_p95_time = 15.0  # ms
        target_success_rate = 1.0
        target_throughput = 50.0  # calculations/second
        
        target_met = (
            avg_time <= target_avg_time and
            percentiles["p95"] <= target_p95_time and
            success_rate >= target_success_rate and
            throughput >= target_throughput
        )
        
        result = PerformanceTestResult(
            test_name="Cosine Similarity Performance",
            operation_count=len(sample_memories),
            total_time_seconds=total_time,
            average_time_ms=avg_time,
            median_time_ms=percentiles["p50"],
            p95_time_ms=percentiles["p95"],
            p99_time_ms=percentiles["p99"],
            success_rate=success_rate,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            throughput_ops_per_second=throughput,
            target_met=target_met,
            notes=f"Target: <{target_avg_time}ms avg, >{target_throughput} calc/s"
        )
        
        self.results.append(result)
        
        # Assertions
        assert success_rate >= 0.95, f"Similarity calculation success rate too low: {success_rate:.1%}"
        assert avg_time <= 10.0, f"Average calculation time too high: {avg_time:.1f}ms"
    
    @pytest.mark.asyncio
    async def test_memory_ranking_performance(self, similarity_matcher, sample_memories):
        """Test memory ranking performance."""
        queries = [
            "deployment to production environment",
            "error in database connection",
            "frontend component optimization",
            "API endpoint performance issue",
            "security vulnerability fix"
        ]
        
        ranking_times = []
        successful_rankings = 0
        
        self.start_resource_monitoring()
        
        try:
            start_time = time.time()
            
            for query in queries:
                for limit in [10, 25, 50]:
                    rank_start = time.time()
                    
                    ranked_results = similarity_matcher.rank_memories_by_similarity(
                        query, sample_memories, limit=limit
                    )
                    
                    rank_time = (time.time() - rank_start) * 1000  # ms
                    ranking_times.append(rank_time)
                    
                    if len(ranked_results) > 0:
                        successful_rankings += 1
                        
                        # Verify ranking quality
                        scores = [result[1].similarity_score for result in ranked_results]
                        assert scores == sorted(scores, reverse=True), "Results not properly ranked"
            
            total_time = time.time() - start_time
            
        finally:
            avg_cpu, avg_memory = self.stop_resource_monitoring()
        
        # Calculate metrics
        percentiles = self.calculate_percentiles(ranking_times)
        avg_time = statistics.mean(ranking_times)
        success_rate = successful_rankings / (len(queries) * 3)  # 3 limits per query
        throughput = (len(queries) * 3) / total_time
        
        # Performance targets
        target_avg_time = 50.0  # ms per ranking
        target_p95_time = 100.0  # ms
        target_success_rate = 1.0
        target_throughput = 5.0  # rankings/second
        
        target_met = (
            avg_time <= target_avg_time and
            percentiles["p95"] <= target_p95_time and
            success_rate >= target_success_rate and
            throughput >= target_throughput
        )
        
        result = PerformanceTestResult(
            test_name="Memory Ranking Performance",
            operation_count=len(queries) * 3,
            total_time_seconds=total_time,
            average_time_ms=avg_time,
            median_time_ms=percentiles["p50"],
            p95_time_ms=percentiles["p95"],
            p99_time_ms=percentiles["p99"],
            success_rate=success_rate,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            throughput_ops_per_second=throughput,
            target_met=target_met,
            notes=f"Ranking {len(sample_memories)} memories with various limits"
        )
        
        self.results.append(result)
        
        # Assertions
        assert success_rate >= 0.95, f"Ranking success rate too low: {success_rate:.1%}"
        assert avg_time <= 75.0, f"Average ranking time too high: {avg_time:.1f}ms"


class TestRecommendationEnginePerformance(PerformanceTestSuite):
    """Test recommendation engine performance."""
    
    @pytest.fixture
    def recommendation_engine(self):
        """Create recommendation engine with performance config."""
        config = RecommendationConfig(
            max_recommendations_per_type=10,
            min_confidence_threshold=0.3,
            enable_caching=True,
            cache_ttl_seconds=300
        )
        
        similarity_matcher = Mock()
        return RecommendationEngine(similarity_matcher, config)
    
    @pytest.fixture
    def enriched_contexts(self):
        """Create enriched contexts for recommendation testing."""
        from claude_pm.services.memory.context_builder import EnrichedContext, ContextType
        from claude_pm.services.memory.memory_context_enhancer import MemoryContext
        
        contexts = []
        
        for i in range(50):
            # Create diverse memory contexts
            memories = [
                MemoryItem(
                    id=f"ctx_mem_{i}_{j}",
                    content=f"Context memory {i}_{j}: Some relevant content for testing",
                    category=[MemoryCategory.PATTERN, MemoryCategory.ERROR, MemoryCategory.PROJECT][j % 3],
                    tags=["context", "test", f"item_{i}"],
                    metadata={"context_id": i, "memory_index": j},
                    created_at=f"2025-07-01T{10 + j % 12:02d}:00:00Z",
                    updated_at=f"2025-07-01T{10 + j % 12:02d}:00:00Z",
                    project_name="recommendation_test"
                )
                for j in range(3 + i % 5)
            ]
            
            memory_context = MemoryContext(
                operation_type=["deploy", "test", "build", "review"][i % 4],
                operation_context={"test_id": i, "context_type": "recommendation_test"},
                relevant_memories=memories,
                pattern_memories=[m for m in memories if m.category == MemoryCategory.PATTERN],
                error_memories=[m for m in memories if m.category == MemoryCategory.ERROR],
                decision_memories=[],
                performance_memories=[],
                recall_trigger=RecallTrigger.PRE_OPERATION,
                recall_timestamp=time.time(),
                similarity_scores={m.id: 0.8 - j * 0.1 for j, m in enumerate(memories)},
                recommendations=[]
            )
            
            enriched_context = EnrichedContext(
                context_type=ContextType.WORKFLOW_COMMAND,
                original_context={"operation": f"test_{i}"},
                memory_context=memory_context,
                enriched_data={},
                analysis_summary={
                    "pattern_count": len(memory_context.pattern_memories),
                    "error_count": len(memory_context.error_memories),
                    "confidence": 0.8 - i * 0.01
                },
                recommendations=[],
                warnings=[],
                confidence_score=0.8 - i * 0.01,
                build_timestamp=time.time(),
                processing_time_ms=10.0 + i
            )
            
            contexts.append(enriched_context)
        
        return contexts
    
    @pytest.mark.asyncio
    async def test_recommendation_generation_performance(self, recommendation_engine, enriched_contexts):
        """Test recommendation generation performance."""
        generation_times = []
        successful_generations = 0
        total_recommendations = 0
        
        self.start_resource_monitoring()
        
        try:
            start_time = time.time()
            
            for context in enriched_contexts:
                gen_start = time.time()
                
                recommendations = recommendation_engine.generate_recommendations(context)
                
                gen_time = (time.time() - gen_start) * 1000  # ms
                generation_times.append(gen_time)
                
                if recommendations and len(recommendations.recommendations) > 0:
                    successful_generations += 1
                    total_recommendations += len(recommendations.recommendations)
            
            total_time = time.time() - start_time
            
        finally:
            avg_cpu, avg_memory = self.stop_resource_monitoring()
        
        # Calculate metrics
        percentiles = self.calculate_percentiles(generation_times)
        avg_time = statistics.mean(generation_times)
        success_rate = successful_generations / len(enriched_contexts)
        throughput = len(enriched_contexts) / total_time
        avg_recommendations = total_recommendations / successful_generations if successful_generations > 0 else 0
        
        # Performance targets
        target_avg_time = 100.0  # ms per generation
        target_p95_time = 200.0  # ms
        target_success_rate = 0.80  # 80% should generate recommendations
        target_throughput = 5.0  # generations/second
        
        target_met = (
            avg_time <= target_avg_time and
            percentiles["p95"] <= target_p95_time and
            success_rate >= target_success_rate and
            throughput >= target_throughput
        )
        
        result = PerformanceTestResult(
            test_name="Recommendation Generation Performance",
            operation_count=len(enriched_contexts),
            total_time_seconds=total_time,
            average_time_ms=avg_time,
            median_time_ms=percentiles["p50"],
            p95_time_ms=percentiles["p95"],
            p99_time_ms=percentiles["p99"],
            success_rate=success_rate,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            throughput_ops_per_second=throughput,
            target_met=target_met,
            notes=f"Generated {total_recommendations} recommendations, avg {avg_recommendations:.1f} per context"
        )
        
        self.results.append(result)
        
        # Assertions
        assert success_rate >= 0.70, f"Recommendation generation success rate too low: {success_rate:.1%}"
        assert avg_time <= 150.0, f"Average generation time too high: {avg_time:.1f}ms"
        assert avg_recommendations >= 1.0, f"Too few recommendations generated on average: {avg_recommendations:.1f}"


@pytest.mark.asyncio
async def test_generate_performance_report():
    """Test that generates a comprehensive performance report."""
    
    # Create test suite instances
    recall_suite = TestMemoryRecallPerformance()
    similarity_suite = TestSimilarityMatchingPerformance()
    recommendation_suite = TestRecommendationEnginePerformance()
    
    # Add some mock results for report generation
    mock_results = [
        PerformanceTestResult(
            test_name="Memory Recall Test",
            operation_count=100,
            total_time_seconds=5.0,
            average_time_ms=50.0,
            median_time_ms=45.0,
            p95_time_ms=90.0,
            p99_time_ms=120.0,
            success_rate=0.98,
            memory_usage_mb=150.0,
            cpu_usage_percent=25.0,
            throughput_ops_per_second=20.0,
            target_met=True,
            notes="Excellent performance"
        ),
        PerformanceTestResult(
            test_name="Similarity Matching Test",
            operation_count=200,
            total_time_seconds=2.0,
            average_time_ms=10.0,
            median_time_ms=8.0,
            p95_time_ms=20.0,
            p99_time_ms=35.0,
            success_rate=1.0,
            memory_usage_mb=75.0,
            cpu_usage_percent=15.0,
            throughput_ops_per_second=100.0,
            target_met=True,
            notes="Very fast calculations"
        )
    ]
    
    recall_suite.results = mock_results
    
    # Generate report
    report = recall_suite.generate_performance_report()
    
    # Verify report content
    assert "# Memory Recall System Performance Report" in report
    assert "## Performance Summary" in report
    assert "## Detailed Results" in report
    assert "## Performance Targets" in report
    assert "Memory Recall Test" in report
    assert "Similarity Matching Test" in report
    assert "✅" in report  # Target met indicators
    assert "98.0%" in report  # Success rates
    assert "20.0" in report  # Throughput values
    
    print("\nGenerated Performance Report:")
    print("=" * 50)
    print(report)


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-s"])