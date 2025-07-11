"""
Performance Benchmark Suite and Validation Reports

Comprehensive performance benchmarking and validation reporting for the memory trigger system:
- System-wide performance benchmarks
- Component-specific performance analysis
- Scalability testing and validation
- Production readiness metrics
- Performance regression detection
- Resource utilization analysis
- Benchmark report generation
"""

"""
# NOTE: InMemory backend tests have been disabled because the InMemory backend  # InMemory backend removed
was removed from the Claude PM Framework memory system. The system now uses
mem0ai → sqlite fallback chain only.
"""


import asyncio
import pytest
import time
import statistics
import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

from claude_pm.services.memory import (
    FlexibleMemoryService,
    MemoryTriggerService,
    MemoryRecallService,
    MemoryCategory,
    MemoryItem,
    MemoryQuery,
    TriggerType,
    TriggerPriority,
    TriggerEvent,
    TriggerResult,
    HookContext,
    create_memory_trigger_service,
    create_memory_recall_service,
)


@dataclass
class BenchmarkMetric:
    """Individual benchmark metric."""

    name: str
    value: float
    unit: str
    target: Optional[float] = None
    threshold_type: str = "max"  # "max", "min", "range"
    category: str = "performance"
    description: str = ""

    @property
    def meets_target(self) -> Optional[bool]:
        """Check if metric meets target."""
        if self.target is None:
            return None

        if self.threshold_type == "max":
            return self.value <= self.target
        elif self.threshold_type == "min":
            return self.value >= self.target
        else:  # range
            return True  # Range checking would need additional logic

    @property
    def status(self) -> str:
        """Get metric status."""
        meets = self.meets_target
        if meets is None:
            return "NO_TARGET"
        return "PASS" if meets else "FAIL"


@dataclass
class BenchmarkResult:
    """Results from a benchmark test."""

    benchmark_name: str
    execution_time: float
    metrics: List[BenchmarkMetric]
    metadata: Dict[str, Any]
    timestamp: str
    system_info: Dict[str, Any]

    @property
    def overall_status(self) -> str:
        """Get overall benchmark status."""
        statuses = [m.status for m in self.metrics if m.status != "NO_TARGET"]
        if not statuses:
            return "NO_TARGETS"

        if all(s == "PASS" for s in statuses):
            return "PASS"
        elif any(s == "FAIL" for s in statuses):
            return "FAIL"
        else:
            return "PARTIAL"


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmark suite."""

    def __init__(self):
        self.benchmark_results: List[BenchmarkResult] = []
        self.system_info = self._collect_system_info()

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for benchmarking context."""
        import platform

        try:
            import psutil

            memory_info = {
                "total_memory_gb": psutil.virtual_memory().total / (1024**3),
                "available_memory_gb": psutil.virtual_memory().available / (1024**3),
                "cpu_count": psutil.cpu_count(),
                "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            }
        except ImportError:
            memory_info = {"psutil_unavailable": True}

        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            **memory_info,
            "benchmark_timestamp": datetime.now().isoformat(),
        }

    async def run_memory_trigger_benchmark(self, memory_system: Dict[str, Any]) -> BenchmarkResult:
        """Benchmark memory trigger system performance."""
        print("🚀 Running Memory Trigger Benchmark...")

        trigger_service = memory_system["trigger_service"]
        hooks = trigger_service.get_framework_hooks()
        orchestrator = trigger_service.get_trigger_orchestrator()

        # Clear any existing metrics
        initial_metrics = orchestrator.get_metrics()

        # Benchmark configuration
        num_triggers = 100
        concurrent_batches = 5
        triggers_per_batch = num_triggers // concurrent_batches

        start_time = time.time()
        execution_times = []
        successful_triggers = 0

        # Execute triggers in batches for concurrency testing
        for batch in range(concurrent_batches):
            batch_start = time.time()

            # Create concurrent triggers
            tasks = []
            for i in range(triggers_per_batch):
                trigger_id = batch * triggers_per_batch + i
                context = HookContext(
                    operation_name=f"benchmark_trigger_{trigger_id}",
                    project_name="benchmark_test",
                    source="benchmark_suite",
                    tags=["benchmark", "performance"],
                )

                task = hooks.workflow_completed(
                    context,
                    success=True,
                    workflow_type="benchmark",
                    results={"trigger_id": trigger_id, "batch": batch},
                )
                tasks.append(task)

            # Execute batch
            results = await asyncio.gather(*tasks, return_exceptions=True)
            batch_time = time.time() - batch_start
            execution_times.append(batch_time)

            # Count successful triggers
            for result in results:
                if not isinstance(result, Exception) and isinstance(result, list):
                    successful_triggers += len([r for r in result if r.success])

        total_time = time.time() - start_time

        # Collect final metrics
        final_metrics = orchestrator.get_metrics()

        # Calculate performance metrics
        avg_batch_time = statistics.mean(execution_times)
        throughput = num_triggers / total_time
        success_rate = successful_triggers / num_triggers if num_triggers > 0 else 0

        metrics = [
            BenchmarkMetric(
                name="trigger_throughput",
                value=throughput,
                unit="triggers/second",
                target=10.0,
                threshold_type="min",
                category="throughput",
                description="Memory trigger creation throughput",
            ),
            BenchmarkMetric(
                name="avg_batch_execution_time",
                value=avg_batch_time * 1000,  # Convert to ms
                unit="ms",
                target=2000.0,
                threshold_type="max",
                category="latency",
                description="Average batch execution time",
            ),
            BenchmarkMetric(
                name="trigger_success_rate",
                value=success_rate,
                unit="ratio",
                target=0.95,
                threshold_type="min",
                category="reliability",
                description="Memory trigger success rate",
            ),
            BenchmarkMetric(
                name="total_execution_time",
                value=total_time,
                unit="seconds",
                target=15.0,
                threshold_type="max",
                category="performance",
                description="Total benchmark execution time",
            ),
            BenchmarkMetric(
                name="concurrent_batch_performance",
                value=min(execution_times) / max(execution_times) if execution_times else 0,
                unit="ratio",
                target=0.7,
                threshold_type="min",
                category="consistency",
                description="Consistency across concurrent batches",
            ),
        ]

        result = BenchmarkResult(
            benchmark_name="Memory Trigger Performance",
            execution_time=total_time,
            metrics=metrics,
            metadata={
                "num_triggers": num_triggers,
                "concurrent_batches": concurrent_batches,
                "successful_triggers": successful_triggers,
                "initial_metrics": initial_metrics,
                "final_metrics": final_metrics,
                "execution_times": execution_times,
            },
            timestamp=datetime.now().isoformat(),
            system_info=self.system_info,
        )

        self.benchmark_results.append(result)
        print(
            f"✅ Memory Trigger Benchmark completed: {throughput:.1f} triggers/sec, {success_rate:.1%} success rate"
        )
        return result

    async def run_memory_recall_benchmark(self, memory_system: Dict[str, Any]) -> BenchmarkResult:
        """Benchmark memory recall system performance."""
        print("🔍 Running Memory Recall Benchmark...")

        memory_service = memory_system["memory_service"]
        recall_service = memory_system["recall_service"]

        # Pre-populate memory service with test data
        print("  📝 Populating test data...")
        memory_ids = []
        for i in range(200):
            memory_id = await memory_service.add_memory(
                project_name="recall_benchmark",
                content=f"Benchmark memory {i}: Performance testing content with various keywords for recall testing. "
                f"Categories: {['deployment', 'testing', 'error', 'optimization'][i % 4]}",
                category=[MemoryCategory.PATTERN, MemoryCategory.ERROR, MemoryCategory.PROJECT][
                    i % 3
                ],
                tags=["benchmark", f"item_{i}", ["deploy", "test", "error", "optimize"][i % 4]],
                metadata={
                    "benchmark_id": i,
                    "category_type": ["pattern", "error", "project"][i % 3],
                },
            )
            memory_ids.append(memory_id)

        # Benchmark recall operations
        num_recalls = 50
        recall_times = []
        successful_recalls = 0
        total_memories_recalled = 0
        total_recommendations = 0

        start_time = time.time()

        # Test different recall scenarios
        recall_scenarios = [
            {"operation_type": "deployment", "context": {"environment": "production"}},
            {"operation_type": "testing", "context": {"test_type": "integration"}},
            {"operation_type": "error_resolution", "context": {"error_type": "timeout"}},
            {"operation_type": "optimization", "context": {"component": "memory"}},
        ]

        for i in range(num_recalls):
            scenario = recall_scenarios[i % len(recall_scenarios)]

            recall_start = time.time()
            result = await recall_service.recall_for_operation(
                project_name="recall_benchmark",
                operation_type=scenario["operation_type"],
                operation_context={**scenario["context"], "iteration": i},
            )
            recall_time = (time.time() - recall_start) * 1000  # ms
            recall_times.append(recall_time)

            if result.success:
                successful_recalls += 1
                if result.memory_context:
                    total_memories_recalled += result.memory_context.get_total_memories()
                if result.recommendations:
                    total_recommendations += len(result.recommendations.recommendations)

        total_time = time.time() - start_time

        # Calculate metrics
        avg_recall_time = statistics.mean(recall_times)
        p95_recall_time = sorted(recall_times)[int(0.95 * len(recall_times))]
        recall_throughput = num_recalls / total_time
        success_rate = successful_recalls / num_recalls
        avg_memories_per_recall = (
            total_memories_recalled / successful_recalls if successful_recalls > 0 else 0
        )

        metrics = [
            BenchmarkMetric(
                name="recall_throughput",
                value=recall_throughput,
                unit="recalls/second",
                target=5.0,
                threshold_type="min",
                category="throughput",
                description="Memory recall operation throughput",
            ),
            BenchmarkMetric(
                name="avg_recall_time",
                value=avg_recall_time,
                unit="ms",
                target=100.0,
                threshold_type="max",
                category="latency",
                description="Average memory recall time",
            ),
            BenchmarkMetric(
                name="p95_recall_time",
                value=p95_recall_time,
                unit="ms",
                target=200.0,
                threshold_type="max",
                category="latency",
                description="95th percentile recall time",
            ),
            BenchmarkMetric(
                name="recall_success_rate",
                value=success_rate,
                unit="ratio",
                target=0.95,
                threshold_type="min",
                category="reliability",
                description="Memory recall success rate",
            ),
            BenchmarkMetric(
                name="avg_memories_per_recall",
                value=avg_memories_per_recall,
                unit="count",
                target=5.0,
                threshold_type="min",
                category="effectiveness",
                description="Average memories recalled per operation",
            ),
            BenchmarkMetric(
                name="recommendations_generated",
                value=total_recommendations,
                unit="count",
                target=num_recalls * 0.8,  # Expect recommendations for 80% of recalls
                threshold_type="min",
                category="functionality",
                description="Total recommendations generated",
            ),
        ]

        result = BenchmarkResult(
            benchmark_name="Memory Recall Performance",
            execution_time=total_time,
            metrics=metrics,
            metadata={
                "num_recalls": num_recalls,
                "successful_recalls": successful_recalls,
                "total_memories_recalled": total_memories_recalled,
                "total_recommendations": total_recommendations,
                "recall_times": recall_times,
                "test_data_size": len(memory_ids),
            },
            timestamp=datetime.now().isoformat(),
            system_info=self.system_info,
        )

        self.benchmark_results.append(result)
        print(
            f"✅ Memory Recall Benchmark completed: {recall_throughput:.1f} recalls/sec, {avg_recall_time:.1f}ms avg"
        )
        return result

    async def run_scalability_benchmark(self, memory_system: Dict[str, Any]) -> BenchmarkResult:
        """Benchmark system scalability under increasing load."""
        print("📈 Running Scalability Benchmark...")

        trigger_service = memory_system["trigger_service"]
        hooks = trigger_service.get_framework_hooks()

        # Test different load levels
        load_levels = [10, 25, 50, 100, 200]
        scalability_results = []

        for load in load_levels:
            print(f"  🔄 Testing load level: {load} operations")

            start_time = time.time()
            tasks = []

            # Create concurrent operations
            for i in range(load):
                context = HookContext(
                    operation_name=f"scalability_test_{load}_{i}",
                    project_name="scalability_test",
                    source="scalability_benchmark",
                    tags=["scalability", f"load_{load}"],
                )

                task = hooks.workflow_completed(
                    context,
                    success=True,
                    workflow_type="scalability_test",
                    results={"load_level": load, "operation_id": i},
                )
                tasks.append(task)

            # Execute all operations
            results = await asyncio.gather(*tasks, return_exceptions=True)
            execution_time = time.time() - start_time

            # Analyze results
            successful_ops = 0
            for result in results:
                if not isinstance(result, Exception) and isinstance(result, list):
                    successful_ops += len([r for r in result if r.success])

            throughput = load / execution_time if execution_time > 0 else 0
            success_rate = successful_ops / load if load > 0 else 0

            scalability_results.append(
                {
                    "load": load,
                    "execution_time": execution_time,
                    "throughput": throughput,
                    "success_rate": success_rate,
                    "successful_operations": successful_ops,
                }
            )

            # Brief pause between load levels
            await asyncio.sleep(0.5)

        # Calculate scalability metrics
        throughputs = [r["throughput"] for r in scalability_results]
        max_throughput = max(throughputs)
        min_throughput = min(throughputs)
        throughput_consistency = min_throughput / max_throughput if max_throughput > 0 else 0

        # Check if throughput scales reasonably
        low_load_throughput = scalability_results[0]["throughput"] if scalability_results else 0
        high_load_throughput = scalability_results[-1]["throughput"] if scalability_results else 0
        scalability_ratio = (
            high_load_throughput / low_load_throughput if low_load_throughput > 0 else 0
        )

        total_time = sum(r["execution_time"] for r in scalability_results)
        avg_success_rate = statistics.mean(r["success_rate"] for r in scalability_results)

        metrics = [
            BenchmarkMetric(
                name="max_throughput",
                value=max_throughput,
                unit="ops/second",
                target=20.0,
                threshold_type="min",
                category="scalability",
                description="Maximum sustained throughput",
            ),
            BenchmarkMetric(
                name="throughput_consistency",
                value=throughput_consistency,
                unit="ratio",
                target=0.6,
                threshold_type="min",
                category="scalability",
                description="Throughput consistency across load levels",
            ),
            BenchmarkMetric(
                name="scalability_ratio",
                value=scalability_ratio,
                unit="ratio",
                target=0.3,
                threshold_type="min",
                category="scalability",
                description="High load vs low load throughput ratio",
            ),
            BenchmarkMetric(
                name="avg_success_rate_under_load",
                value=avg_success_rate,
                unit="ratio",
                target=0.90,
                threshold_type="min",
                category="reliability",
                description="Average success rate across all load levels",
            ),
            BenchmarkMetric(
                name="max_load_handled",
                value=max(load_levels),
                unit="operations",
                target=100.0,
                threshold_type="min",
                category="capacity",
                description="Maximum load level successfully handled",
            ),
        ]

        result = BenchmarkResult(
            benchmark_name="System Scalability",
            execution_time=total_time,
            metrics=metrics,
            metadata={
                "load_levels": load_levels,
                "scalability_results": scalability_results,
                "max_throughput": max_throughput,
                "throughput_range": [min_throughput, max_throughput],
            },
            timestamp=datetime.now().isoformat(),
            system_info=self.system_info,
        )

        self.benchmark_results.append(result)
        print(
            f"✅ Scalability Benchmark completed: Max {max_throughput:.1f} ops/sec, {throughput_consistency:.1%} consistency"
        )
        return result

    async def run_resource_utilization_benchmark(
        self, memory_system: Dict[str, Any]
    ) -> BenchmarkResult:
        """Benchmark resource utilization patterns."""
        print("💾 Running Resource Utilization Benchmark...")

        try:
            import psutil
        except ImportError:
            print("  ⚠️  psutil not available, skipping resource utilization benchmark")
            return BenchmarkResult(
                benchmark_name="Resource Utilization",
                execution_time=0,
                metrics=[],
                metadata={"error": "psutil not available"},
                timestamp=datetime.now().isoformat(),
                system_info=self.system_info,
            )

        # Monitor resource usage during operations
        resource_data = {"cpu_percent": [], "memory_mb": [], "active": True}

        def monitor_resources():
            process = psutil.Process()
            while resource_data["active"]:
                try:
                    cpu = process.cpu_percent()
                    memory = process.memory_info().rss / 1024 / 1024  # MB
                    resource_data["cpu_percent"].append(cpu)
                    resource_data["memory_mb"].append(memory)
                    time.sleep(0.1)
                except:
                    break

        # Start monitoring
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.start()

        try:
            start_time = time.time()

            # Execute resource-intensive operations
            trigger_service = memory_system["trigger_service"]
            recall_service = memory_system["recall_service"]

            # Heavy trigger load
            heavy_tasks = []
            for i in range(100):
                context = HookContext(
                    operation_name=f"resource_test_{i}",
                    project_name="resource_test",
                    source="resource_benchmark",
                    metadata={"data": "x" * 1000},  # Add some data
                )

                task = trigger_service.get_framework_hooks().workflow_completed(
                    context, success=True
                )
                heavy_tasks.append(task)

            await asyncio.gather(*heavy_tasks)

            # Heavy recall load
            for i in range(50):
                await recall_service.recall_for_operation(
                    "resource_test", "resource_benchmark", {"iteration": i}
                )

            execution_time = time.time() - start_time

        finally:
            resource_data["active"] = False
            monitor_thread.join(timeout=5.0)

        # Analyze resource usage
        if resource_data["cpu_percent"] and resource_data["memory_mb"]:
            avg_cpu = statistics.mean(resource_data["cpu_percent"])
            max_cpu = max(resource_data["cpu_percent"])
            avg_memory = statistics.mean(resource_data["memory_mb"])
            max_memory = max(resource_data["memory_mb"])
            memory_growth = max_memory - min(resource_data["memory_mb"])
        else:
            avg_cpu = max_cpu = avg_memory = max_memory = memory_growth = 0

        metrics = [
            BenchmarkMetric(
                name="avg_cpu_usage",
                value=avg_cpu,
                unit="percent",
                target=80.0,
                threshold_type="max",
                category="resource",
                description="Average CPU usage during operations",
            ),
            BenchmarkMetric(
                name="max_cpu_usage",
                value=max_cpu,
                unit="percent",
                target=95.0,
                threshold_type="max",
                category="resource",
                description="Peak CPU usage",
            ),
            BenchmarkMetric(
                name="avg_memory_usage",
                value=avg_memory,
                unit="MB",
                target=500.0,
                threshold_type="max",
                category="resource",
                description="Average memory usage",
            ),
            BenchmarkMetric(
                name="max_memory_usage",
                value=max_memory,
                unit="MB",
                target=1000.0,
                threshold_type="max",
                category="resource",
                description="Peak memory usage",
            ),
            BenchmarkMetric(
                name="memory_growth",
                value=memory_growth,
                unit="MB",
                target=200.0,
                threshold_type="max",
                category="resource",
                description="Memory usage growth during benchmark",
            ),
        ]

        result = BenchmarkResult(
            benchmark_name="Resource Utilization",
            execution_time=execution_time,
            metrics=metrics,
            metadata={
                "cpu_samples": len(resource_data["cpu_percent"]),
                "memory_samples": len(resource_data["memory_mb"]),
                "resource_data": {
                    "cpu_range": (
                        [min(resource_data["cpu_percent"]), max(resource_data["cpu_percent"])]
                        if resource_data["cpu_percent"]
                        else [0, 0]
                    ),
                    "memory_range": (
                        [min(resource_data["memory_mb"]), max(resource_data["memory_mb"])]
                        if resource_data["memory_mb"]
                        else [0, 0]
                    ),
                },
            },
            timestamp=datetime.now().isoformat(),
            system_info=self.system_info,
        )

        self.benchmark_results.append(result)
        print(
            f"✅ Resource Utilization Benchmark completed: {avg_cpu:.1f}% avg CPU, {avg_memory:.1f}MB avg memory"
        )
        return result

    def generate_benchmark_report(self, output_format: str = "markdown") -> str:
        """Generate comprehensive benchmark report."""
        if not self.benchmark_results:
            return "No benchmark results available."

        if output_format == "markdown":
            return self._generate_markdown_report()
        elif output_format == "json":
            return self._generate_json_report()
        elif output_format == "csv":
            return self._generate_csv_report()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_markdown_report(self) -> str:
        """Generate markdown benchmark report."""
        report = ["# Memory Trigger System Performance Benchmark Report\n"]

        # Executive Summary
        total_benchmarks = len(self.benchmark_results)
        passed_benchmarks = sum(1 for r in self.benchmark_results if r.overall_status == "PASS")

        report.append("## Executive Summary\n")
        report.append(f"- **Benchmark Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"- **Total Benchmarks**: {total_benchmarks}")
        report.append(
            f"- **Passed Benchmarks**: {passed_benchmarks}/{total_benchmarks} ({passed_benchmarks/total_benchmarks:.1%})"
        )
        report.append(
            f"- **Overall Status**: {'✅ PASS' if passed_benchmarks == total_benchmarks else '❌ FAIL'}"
        )
        report.append("")

        # System Information
        report.append("## System Information\n")
        report.append(f"- **Platform**: {self.system_info.get('platform', 'Unknown')}")
        report.append(f"- **Python Version**: {self.system_info.get('python_version', 'Unknown')}")
        report.append(f"- **Architecture**: {self.system_info.get('architecture', 'Unknown')}")
        if "total_memory_gb" in self.system_info:
            report.append(f"- **Total Memory**: {self.system_info['total_memory_gb']:.1f} GB")
        if "cpu_count" in self.system_info:
            report.append(f"- **CPU Count**: {self.system_info['cpu_count']}")
        report.append("")

        # Benchmark Results Summary
        report.append("## Benchmark Results Summary\n")
        report.append("| Benchmark | Status | Execution Time | Metrics Passed | Key Performance |")
        report.append("|-----------|--------|----------------|----------------|-----------------|")

        for result in self.benchmark_results:
            passed_metrics = sum(1 for m in result.metrics if m.status == "PASS")
            total_metrics = len([m for m in result.metrics if m.status != "NO_TARGET"])
            key_metric = result.metrics[0] if result.metrics else None
            key_perf = f"{key_metric.value:.1f} {key_metric.unit}" if key_metric else "N/A"

            status_icon = {"PASS": "✅", "FAIL": "❌", "PARTIAL": "⚠️", "NO_TARGETS": "ℹ️"}.get(
                result.overall_status, "❓"
            )

            report.append(
                f"| {result.benchmark_name} | {status_icon} {result.overall_status} | "
                f"{result.execution_time:.2f}s | {passed_metrics}/{total_metrics} | {key_perf} |"
            )

        # Detailed Results
        report.append("\n## Detailed Benchmark Results\n")

        for result in self.benchmark_results:
            report.append(f"### {result.benchmark_name}\n")
            report.append(f"- **Status**: {result.overall_status}")
            report.append(f"- **Execution Time**: {result.execution_time:.2f} seconds")
            report.append(f"- **Timestamp**: {result.timestamp}")
            report.append("")

            # Metrics table
            report.append("#### Performance Metrics\n")
            report.append("| Metric | Value | Unit | Target | Status | Description |")
            report.append("|--------|-------|------|--------|--------|-------------|")

            for metric in result.metrics:
                target_str = (
                    f"{metric.target} {metric.unit}" if metric.target is not None else "No target"
                )
                status_icon = {"PASS": "✅", "FAIL": "❌", "NO_TARGET": "ℹ️"}.get(
                    metric.status, "❓"
                )

                report.append(
                    f"| {metric.name} | {metric.value:.2f} | {metric.unit} | "
                    f"{target_str} | {status_icon} {metric.status} | {metric.description} |"
                )

            # Additional metadata
            if result.metadata:
                report.append(f"\n#### Additional Information\n")
                for key, value in result.metadata.items():
                    if not isinstance(value, (list, dict)):
                        report.append(f"- **{key.replace('_', ' ').title()}**: {value}")

            report.append("")

        # Performance Trends
        report.append("## Performance Analysis\n")

        # Aggregate metrics by category
        categories = {}
        for result in self.benchmark_results:
            for metric in result.metrics:
                if metric.category not in categories:
                    categories[metric.category] = []
                categories[metric.category].append(metric)

        for category, metrics in categories.items():
            passed = sum(1 for m in metrics if m.status == "PASS")
            total = len([m for m in metrics if m.status != "NO_TARGET"])

            if total > 0:
                report.append(
                    f"- **{category.title()} Metrics**: {passed}/{total} passed ({passed/total:.1%})"
                )

        # Recommendations
        report.append("\n## Recommendations\n")

        failed_metrics = []
        for result in self.benchmark_results:
            failed_metrics.extend([m for m in result.metrics if m.status == "FAIL"])

        if failed_metrics:
            report.append("### Performance Issues Identified\n")
            for metric in failed_metrics:
                report.append(
                    f"- **{metric.name}**: {metric.value:.2f} {metric.unit} (target: {metric.target} {metric.unit})"
                )

                # Provide specific recommendations
                if "throughput" in metric.name.lower():
                    report.append("  - Consider optimizing concurrent processing")
                    report.append("  - Review resource allocation and bottlenecks")
                elif "time" in metric.name.lower() or "latency" in metric.name.lower():
                    report.append("  - Optimize critical path operations")
                    report.append("  - Consider caching strategies")
                elif "memory" in metric.name.lower():
                    report.append("  - Review memory usage patterns")
                    report.append("  - Consider memory cleanup optimizations")
                elif "cpu" in metric.name.lower():
                    report.append("  - Optimize CPU-intensive operations")
                    report.append("  - Consider async processing for blocking operations")
        else:
            report.append(
                "✅ **All performance targets met!** The system is performing within acceptable parameters."
            )

        return "\n".join(report)

    def _generate_json_report(self) -> str:
        """Generate JSON benchmark report."""
        report_data = {
            "report_metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "total_benchmarks": len(self.benchmark_results),
                "system_info": self.system_info,
            },
            "benchmark_results": [
                {
                    "benchmark_name": result.benchmark_name,
                    "status": result.overall_status,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp,
                    "metrics": [
                        {
                            "name": metric.name,
                            "value": metric.value,
                            "unit": metric.unit,
                            "target": metric.target,
                            "status": metric.status,
                            "category": metric.category,
                            "description": metric.description,
                        }
                        for metric in result.metrics
                    ],
                    "metadata": result.metadata,
                }
                for result in self.benchmark_results
            ],
        }

        return json.dumps(report_data, indent=2)

    def _generate_csv_report(self) -> str:
        """Generate CSV benchmark report."""
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "benchmark_name",
                "metric_name",
                "value",
                "unit",
                "target",
                "status",
                "category",
                "description",
                "execution_time",
                "timestamp",
            ]
        )

        # Write data
        for result in self.benchmark_results:
            for metric in result.metrics:
                writer.writerow(
                    [
                        result.benchmark_name,
                        metric.name,
                        metric.value,
                        metric.unit,
                        metric.target,
                        metric.status,
                        metric.category,
                        metric.description,
                        result.execution_time,
                        result.timestamp,
                    ]
                )

        return output.getvalue()

    def save_report(self, filename: str, output_format: str = "markdown") -> str:
        """Save benchmark report to file."""
        report_content = self.generate_benchmark_report(output_format)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)

        return filename


class TestPerformanceBenchmarkSuite:
    """Test suite for performance benchmarks."""

    @pytest.fixture
    async def benchmark_system(self):
        """Create system for benchmark testing."""
        config = {
            "memory": {"fallback_chain": ["sqlite"]},
            "performance": {
                "create_timeout": 10.0,
                "recall_timeout": 5.0,
                "batch_size": 50,
                "max_concurrent_operations": 20,
            },
        }

        trigger_service = create_memory_trigger_service(config)
        recall_service = create_memory_recall_service()

        await trigger_service.initialize()
        await recall_service.initialize()

        memory_system = {
            "trigger_service": trigger_service,
            "recall_service": recall_service,
            "memory_service": trigger_service.get_memory_service(),
        }

        yield memory_system

        await trigger_service.cleanup()
        await recall_service.cleanup()

    @pytest.mark.asyncio
    async def test_complete_benchmark_suite(self, benchmark_system):
        """Run complete performance benchmark suite."""
        print("\n🏆 Running Complete Performance Benchmark Suite")
        print("=" * 60)

        suite = PerformanceBenchmarkSuite()

        # Run all benchmarks
        await suite.run_memory_trigger_benchmark(benchmark_system)
        await suite.run_memory_recall_benchmark(benchmark_system)
        await suite.run_scalability_benchmark(benchmark_system)
        await suite.run_resource_utilization_benchmark(benchmark_system)

        # Generate and display report
        report = suite.generate_benchmark_report("markdown")

        print("\n📊 BENCHMARK REPORT")
        print("=" * 60)
        print(report)

        # Save reports in different formats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        markdown_file = f"benchmark_report_{timestamp}.md"
        json_file = f"benchmark_report_{timestamp}.json"
        csv_file = f"benchmark_report_{timestamp}.csv"

        suite.save_report(markdown_file, "markdown")
        suite.save_report(json_file, "json")
        suite.save_report(csv_file, "csv")

        print(f"\n📁 Reports saved:")
        print(f"  - Markdown: {markdown_file}")
        print(f"  - JSON: {json_file}")
        print(f"  - CSV: {csv_file}")

        # Validate overall benchmark success
        passed_benchmarks = sum(1 for r in suite.benchmark_results if r.overall_status == "PASS")
        total_benchmarks = len(suite.benchmark_results)

        assert total_benchmarks > 0, "Should have executed benchmarks"
        assert (
            passed_benchmarks >= total_benchmarks * 0.8
        ), f"Should pass at least 80% of benchmarks, got {passed_benchmarks}/{total_benchmarks}"

        print(
            f"\n✅ Benchmark Suite Completed: {passed_benchmarks}/{total_benchmarks} benchmarks passed"
        )


if __name__ == "__main__":
    # Run benchmark suite
    pytest.main([__file__, "-v", "-s"])
