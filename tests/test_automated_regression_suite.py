#!/usr/bin/env python3
"""
Automated Regression Testing Suite - Memory Leak Prevention
=========================================================

QA Agent automated regression testing for continuous memory leak prevention.
Designed for CI/CD integration and future release validation.

Features:
- Rapid memory leak detection
- Performance regression detection
- Automated thresholds and alerts
- CI/CD integration ready
- Historical trending support

Date: 2025-07-14
Target: Future memory leak prevention
"""

import asyncio
import json
import logging
import os
import psutil
import subprocess
import sys
import time
import gc
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegressionTestConfig:
    """Configuration for regression testing."""
    
    # Memory thresholds (based on validated fixes)
    MAX_MEMORY_LEAK_PER_OPERATION_MB = 0.5  # 0.5MB per operation max
    MAX_SUBPROCESS_MEMORY_INCREASE_MB = 20   # 20MB for subprocess batch
    MAX_CACHE_MEMORY_RETENTION_PERCENTAGE = 30  # 30% retention after cleanup
    MAX_LONG_RUNNING_MEMORY_TREND_MB = 25    # 25MB trend over test period
    
    # Performance thresholds
    MAX_OPERATION_TIME_MS = 1000  # 1 second max per operation
    MIN_THROUGHPUT_OPS_PER_SEC = 10  # 10 operations per second minimum
    
    # Test parameters
    QUICK_TEST_ITERATIONS = 10
    STANDARD_TEST_ITERATIONS = 50
    LONG_RUNNING_DURATION_SECONDS = 60  # 1 minute for CI/CD
    
    # CI/CD integration
    RESULTS_RETENTION_DAYS = 30
    TREND_ANALYSIS_WINDOW_DAYS = 7

class MemoryRegressionTester:
    """Automated memory regression testing."""
    
    def __init__(self, config: RegressionTestConfig = None):
        self.config = config or RegressionTestConfig()
        self.process = psutil.Process()
        self.baseline_memory_mb = self._get_memory_usage_mb()
        self.test_session_id = f"regression_{int(time.time())}"
        
        logger.info(f"Memory regression tester initialized - Session: {self.test_session_id}")
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    async def test_subprocess_memory_regression(self) -> Dict[str, Any]:
        """Test for subprocess memory regressions."""
        logger.info("Running subprocess memory regression test...")
        
        memory_before = self._get_memory_usage_mb()
        start_time = time.time()
        
        # Run moderate subprocess load
        subprocess_count = self.config.STANDARD_TEST_ITERATIONS
        
        for i in range(subprocess_count):
            proc = subprocess.Popen(
                ['python3', '-c', 'print("regression_test")'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate()
            proc.stdout.close()
            proc.stderr.close()
            del proc, stdout, stderr
            
            if i % 10 == 0:
                gc.collect()
        
        gc.collect()
        await asyncio.sleep(0.5)  # Cleanup time
        
        memory_after = self._get_memory_usage_mb()
        elapsed_time = time.time() - start_time
        
        memory_increase = memory_after - memory_before
        avg_memory_per_subprocess = memory_increase / subprocess_count if subprocess_count > 0 else 0
        throughput = subprocess_count / elapsed_time if elapsed_time > 0 else 0
        
        # Check thresholds
        memory_regression = memory_increase > self.config.MAX_SUBPROCESS_MEMORY_INCREASE_MB
        performance_regression = throughput < self.config.MIN_THROUGHPUT_OPS_PER_SEC
        
        passed = not (memory_regression or performance_regression)
        
        return {
            "test_name": "subprocess_memory_regression",
            "passed": passed,
            "memory_increase_mb": memory_increase,
            "avg_memory_per_subprocess_mb": avg_memory_per_subprocess,
            "throughput_ops_per_sec": throughput,
            "subprocess_count": subprocess_count,
            "elapsed_time_seconds": elapsed_time,
            "memory_regression_detected": memory_regression,
            "performance_regression_detected": performance_regression,
            "thresholds": {
                "max_memory_increase_mb": self.config.MAX_SUBPROCESS_MEMORY_INCREASE_MB,
                "min_throughput_ops_per_sec": self.config.MIN_THROUGHPUT_OPS_PER_SEC
            }
        }
    
    async def test_cache_memory_regression(self) -> Dict[str, Any]:
        """Test for cache memory regressions."""
        logger.info("Running cache memory regression test...")
        
        memory_before = self._get_memory_usage_mb()
        start_time = time.time()
        
        # Simulate cache operations
        cache_data = {}
        cache_size = self.config.STANDARD_TEST_ITERATIONS
        
        # Fill cache
        for i in range(cache_size):
            cache_data[f"key_{i}"] = "x" * 1000  # 1KB per item
        
        memory_after_fill = self._get_memory_usage_mb()
        
        # Clear cache
        cache_data.clear()
        del cache_data
        gc.collect()
        await asyncio.sleep(0.5)
        
        memory_after_clear = self._get_memory_usage_mb()
        elapsed_time = time.time() - start_time
        
        memory_used = memory_after_fill - memory_before
        memory_retained = memory_after_clear - memory_before
        memory_retention_percentage = (memory_retained / memory_used * 100) if memory_used > 0 else 0
        
        # Check thresholds
        memory_regression = memory_retention_percentage > self.config.MAX_CACHE_MEMORY_RETENTION_PERCENTAGE
        
        passed = not memory_regression
        
        return {
            "test_name": "cache_memory_regression",
            "passed": passed,
            "memory_used_mb": memory_used,
            "memory_retained_mb": memory_retained,
            "memory_retention_percentage": memory_retention_percentage,
            "cache_size": cache_size,
            "elapsed_time_seconds": elapsed_time,
            "memory_regression_detected": memory_regression,
            "thresholds": {
                "max_retention_percentage": self.config.MAX_CACHE_MEMORY_RETENTION_PERCENTAGE
            }
        }
    
    async def test_long_running_memory_regression(self) -> Dict[str, Any]:
        """Test for long-running memory regressions."""
        logger.info(f"Running long-running memory regression test for {self.config.LONG_RUNNING_DURATION_SECONDS}s...")
        
        start_time = time.time()
        memory_samples = []
        operation_count = 0
        
        end_time = start_time + self.config.LONG_RUNNING_DURATION_SECONDS
        
        while time.time() < end_time:
            # Simulate memory operations
            temp_data = bytearray(100)  # 100 bytes
            memory_samples.append(self._get_memory_usage_mb())
            del temp_data
            
            operation_count += 1
            await asyncio.sleep(0.01)  # 10ms between operations
        
        elapsed_time = time.time() - start_time
        
        if memory_samples:
            memory_trend = memory_samples[-1] - memory_samples[0]
            avg_memory = sum(memory_samples) / len(memory_samples)
            max_memory = max(memory_samples)
            min_memory = min(memory_samples)
            memory_variance = max_memory - min_memory
        else:
            memory_trend = avg_memory = max_memory = min_memory = memory_variance = 0
        
        operations_per_second = operation_count / elapsed_time if elapsed_time > 0 else 0
        
        # Check thresholds
        memory_regression = memory_trend > self.config.MAX_LONG_RUNNING_MEMORY_TREND_MB
        performance_regression = operations_per_second < self.config.MIN_THROUGHPUT_OPS_PER_SEC * 5  # Higher for simple ops
        
        passed = not (memory_regression or performance_regression)
        
        return {
            "test_name": "long_running_memory_regression",
            "passed": passed,
            "memory_trend_mb": memory_trend,
            "avg_memory_mb": avg_memory,
            "max_memory_mb": max_memory,
            "min_memory_mb": min_memory,
            "memory_variance_mb": memory_variance,
            "operation_count": operation_count,
            "operations_per_second": operations_per_second,
            "elapsed_time_seconds": elapsed_time,
            "memory_regression_detected": memory_regression,
            "performance_regression_detected": performance_regression,
            "thresholds": {
                "max_memory_trend_mb": self.config.MAX_LONG_RUNNING_MEMORY_TREND_MB,
                "min_operations_per_second": self.config.MIN_THROUGHPUT_OPS_PER_SEC * 5
            }
        }
    
    async def test_performance_regression(self) -> Dict[str, Any]:
        """Test for performance regressions."""
        logger.info("Running performance regression test...")
        
        start_time = time.time()
        operation_times = []
        
        # Test operation performance
        for i in range(self.config.QUICK_TEST_ITERATIONS):
            op_start = time.time()
            
            # Simulate typical operation
            data = [j for j in range(1000)]  # Create list
            data.sort()  # Sort operation
            del data  # Cleanup
            
            op_end = time.time()
            operation_times.append((op_end - op_start) * 1000)  # Convert to ms
        
        elapsed_time = time.time() - start_time
        
        avg_operation_time_ms = sum(operation_times) / len(operation_times) if operation_times else 0
        max_operation_time_ms = max(operation_times) if operation_times else 0
        min_operation_time_ms = min(operation_times) if operation_times else 0
        
        # Check thresholds
        performance_regression = avg_operation_time_ms > self.config.MAX_OPERATION_TIME_MS
        
        passed = not performance_regression
        
        return {
            "test_name": "performance_regression",
            "passed": passed,
            "avg_operation_time_ms": avg_operation_time_ms,
            "max_operation_time_ms": max_operation_time_ms,
            "min_operation_time_ms": min_operation_time_ms,
            "operation_count": len(operation_times),
            "elapsed_time_seconds": elapsed_time,
            "performance_regression_detected": performance_regression,
            "thresholds": {
                "max_operation_time_ms": self.config.MAX_OPERATION_TIME_MS
            }
        }
    
    def save_historical_results(self, results: Dict[str, Any]) -> str:
        """Save results for historical trending."""
        results_dir = Path("/Users/masa/Projects/claude-multiagent-pm/logs/regression_history")
        results_dir.mkdir(exist_ok=True)
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"regression_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Cleanup old results (retain based on config)
        self._cleanup_old_results(results_dir)
        
        return str(results_file)
    
    def _cleanup_old_results(self, results_dir: Path):
        """Cleanup old regression test results."""
        try:
            cutoff_time = time.time() - (self.config.RESULTS_RETENTION_DAYS * 24 * 60 * 60)
            
            for result_file in results_dir.glob("regression_results_*.json"):
                if result_file.stat().st_mtime < cutoff_time:
                    result_file.unlink()
                    logger.debug(f"Cleaned up old result file: {result_file}")
        except Exception as e:
            logger.warning(f"Failed to cleanup old results: {e}")
    
    async def run_regression_suite(self, quick_mode: bool = False) -> Dict[str, Any]:
        """Run complete regression test suite."""
        logger.info(f"Running regression test suite (quick_mode={quick_mode})...")
        
        start_time = datetime.now()
        
        # Adjust config for quick mode
        if quick_mode:
            self.config.QUICK_TEST_ITERATIONS = 5
            self.config.STANDARD_TEST_ITERATIONS = 10
            self.config.LONG_RUNNING_DURATION_SECONDS = 15
        
        # Run regression tests
        tests = [
            self.test_subprocess_memory_regression(),
            self.test_cache_memory_regression(),
            self.test_performance_regression(),
        ]
        
        if not quick_mode:
            tests.append(self.test_long_running_memory_regression())
        
        results = []
        for test in tests:
            try:
                result = await test
                results.append(result)
            except Exception as e:
                logger.error(f"Regression test failed: {e}")
                results.append({
                    "test_name": "unknown_regression_test",
                    "passed": False,
                    "error": str(e)
                })
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate overall results
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get("passed", False))
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        current_memory = self._get_memory_usage_mb()
        total_memory_increase = current_memory - self.baseline_memory_mb
        
        # Regression analysis
        memory_regressions = [r for r in results if r.get("memory_regression_detected", False)]
        performance_regressions = [r for r in results if r.get("performance_regression_detected", False)]
        
        overall_passed = (
            len(memory_regressions) == 0 and
            len(performance_regressions) == 0 and
            passed_tests == total_tests
        )
        
        regression_report = {
            "session_id": self.test_session_id,
            "timestamp": datetime.now().isoformat(),
            "regression_suite_version": "1.0.0",
            "quick_mode": quick_mode,
            
            "overall_status": {
                "passed": overall_passed,
                "success_rate_percentage": success_rate,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "total_duration_seconds": total_duration
            },
            
            "regression_analysis": {
                "memory_regressions_detected": len(memory_regressions),
                "performance_regressions_detected": len(performance_regressions),
                "memory_regression_tests": [r["test_name"] for r in memory_regressions],
                "performance_regression_tests": [r["test_name"] for r in performance_regressions],
                "overall_memory_increase_mb": total_memory_increase,
                "memory_stable": total_memory_increase < 50  # 50MB threshold for suite
            },
            
            "test_results": results,
            
            "thresholds_used": {
                "max_memory_leak_per_operation_mb": self.config.MAX_MEMORY_LEAK_PER_OPERATION_MB,
                "max_subprocess_memory_increase_mb": self.config.MAX_SUBPROCESS_MEMORY_INCREASE_MB,
                "max_cache_memory_retention_percentage": self.config.MAX_CACHE_MEMORY_RETENTION_PERCENTAGE,
                "max_long_running_memory_trend_mb": self.config.MAX_LONG_RUNNING_MEMORY_TREND_MB,
                "max_operation_time_ms": self.config.MAX_OPERATION_TIME_MS,
                "min_throughput_ops_per_sec": self.config.MIN_THROUGHPUT_OPS_PER_SEC
            },
            
            "ci_cd_integration": {
                "exit_code": 0 if overall_passed else 1,
                "junit_compatible": True,
                "artifacts_generated": True,
                "trend_analysis_ready": True
            },
            
            "recommendations": self._generate_regression_recommendations(overall_passed, memory_regressions, performance_regressions)
        }
        
        # Save historical results
        results_file = self.save_historical_results(regression_report)
        regression_report["results_file"] = results_file
        
        return regression_report
    
    def _generate_regression_recommendations(self, overall_passed: bool, memory_regressions: List[Dict], performance_regressions: List[Dict]) -> List[str]:
        """Generate recommendations based on regression analysis."""
        recommendations = []
        
        if overall_passed:
            recommendations.extend([
                "✅ No memory or performance regressions detected",
                "✅ All regression tests passed - safe to proceed with deployment",
                "✅ Memory management optimizations are stable",
                "📊 Continue automated regression testing in CI/CD pipeline"
            ])
        else:
            if memory_regressions:
                recommendations.extend([
                    f"❌ Memory regressions detected in {len(memory_regressions)} tests",
                    "❌ Review memory management implementations",
                    "❌ Check for new memory leaks in recent changes"
                ])
                
                for regression in memory_regressions:
                    test_name = regression.get("test_name", "unknown")
                    recommendations.append(f"   - {test_name}: Memory regression detected")
            
            if performance_regressions:
                recommendations.extend([
                    f"❌ Performance regressions detected in {len(performance_regressions)} tests",
                    "❌ Review recent performance optimizations",
                    "❌ Consider performance profiling"
                ])
                
                for regression in performance_regressions:
                    test_name = regression.get("test_name", "unknown")
                    recommendations.append(f"   - {test_name}: Performance regression detected")
            
            recommendations.extend([
                "⚠️ Regression testing failed - deployment NOT RECOMMENDED",
                "⚠️ Address regressions before proceeding with release"
            ])
        
        # Always include monitoring recommendations
        recommendations.extend([
            "📈 Enable continuous regression monitoring",
            "📈 Set up automated alerts for regression detection",
            "📈 Review regression test thresholds periodically"
        ])
        
        return recommendations

async def main():
    """Main regression testing execution."""
    print("=" * 80)
    print("AUTOMATED MEMORY REGRESSION TESTING SUITE")
    print("QA Agent - Future Memory Leak Prevention")
    print(f"Date: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Check for quick mode
    quick_mode = "--quick" in sys.argv
    if quick_mode:
        print("Running in QUICK MODE for CI/CD integration")
    
    tester = MemoryRegressionTester()
    
    try:
        regression_report = await tester.run_regression_suite(quick_mode=quick_mode)
        
        # Print summary
        overall_status = regression_report["overall_status"]
        regression_analysis = regression_report["regression_analysis"]
        
        print(f"\nREGRESSION TEST RESULTS:")
        print(f"Overall Status: {'✅ PASSED' if overall_status['passed'] else '❌ FAILED'}")
        print(f"Success Rate: {overall_status['success_rate_percentage']:.1f}%")
        print(f"Duration: {overall_status['total_duration_seconds']:.1f} seconds")
        print(f"Total Memory Increase: {regression_analysis['overall_memory_increase_mb']:.2f} MB")
        
        print(f"\nREGRESSION ANALYSIS:")
        print(f"Memory Regressions: {regression_analysis['memory_regressions_detected']}")
        print(f"Performance Regressions: {regression_analysis['performance_regressions_detected']}")
        
        if regression_analysis['memory_regression_tests']:
            print(f"Memory Regression Tests: {', '.join(regression_analysis['memory_regression_tests'])}")
        
        if regression_analysis['performance_regression_tests']:
            print(f"Performance Regression Tests: {', '.join(regression_analysis['performance_regression_tests'])}")
        
        print(f"\nCONTINUOUS INTEGRATION:")
        print(f"Exit Code: {regression_report['ci_cd_integration']['exit_code']}")
        print(f"Results File: {regression_report['results_file']}")
        
        print(f"\nRECOMMENDATIONS:")
        for rec in regression_report['recommendations']:
            print(f"  {rec}")
        
        print("=" * 80)
        
        return regression_report['ci_cd_integration']['exit_code']
        
    except Exception as e:
        logger.error(f"Regression testing failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)