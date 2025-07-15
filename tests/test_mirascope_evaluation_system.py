"""
Comprehensive Test Suite for Mirascope Evaluation System
=======================================================

This test suite validates the complete Mirascope evaluation system implementation,
including all components and their integration.

Test Coverage:
- MirascopeEvaluator: Core evaluation functionality
- EvaluationIntegrationService: Integration with correction capture
- EvaluationMetricsSystem: Metrics collection and analysis
- EvaluationPerformanceManager: Performance optimization
- EvaluationMonitor: Monitoring and health checks
- System integration: End-to-end workflows
"""

import asyncio
import json
import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from claude_pm.core.config import Config
from claude_pm.services.correction_capture import CorrectionCapture, CorrectionData, CorrectionType
from claude_pm.services.mirascope_evaluator import (
    MirascopeEvaluator, EvaluationResult, EvaluationScore, 
    EvaluationProvider, EvaluationCriteria
)
from claude_pm.services.evaluation_integration import EvaluationIntegrationService
from claude_pm.services.evaluation_metrics import EvaluationMetricsSystem
from claude_pm.services.evaluation_performance import EvaluationPerformanceManager
from claude_pm.services.evaluation_monitoring import EvaluationMonitor


class TestMirascopeEvaluator:
    """Test the MirascopeEvaluator class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        return Config({
            "enable_evaluation": True,
            "evaluation_provider": "auto",
            "evaluation_storage_path": temp_dir,
            "evaluation_caching_enabled": True,
            "evaluation_cache_ttl_hours": 1
        })
    
    @pytest.fixture
    def evaluator(self, test_config):
        """Create MirascopeEvaluator instance."""
        return MirascopeEvaluator(test_config)
    
    def test_evaluator_initialization(self, evaluator):
        """Test evaluator initialization."""
        assert evaluator is not None
        assert evaluator.config is not None
        assert evaluator.storage_path.exists()
        assert evaluator.evaluations_dir.exists()
    
    def test_evaluator_disabled_when_mirascope_unavailable(self, test_config):
        """Test evaluator is disabled when Mirascope is unavailable."""
        with patch('claude_pm.services.mirascope_evaluator.MIRASCOPE_AVAILABLE', False):
            evaluator = MirascopeEvaluator(test_config)
            assert not evaluator.enabled
    
    def test_provider_initialization(self, evaluator):
        """Test provider initialization."""
        assert evaluator.provider in [EvaluationProvider.OPENAI, EvaluationProvider.ANTHROPIC]
    
    def test_cache_key_generation(self, evaluator):
        """Test cache key generation."""
        key1 = evaluator._generate_cache_key("engineer", "test response", {"task": "test"})
        key2 = evaluator._generate_cache_key("engineer", "test response", {"task": "test"})
        key3 = evaluator._generate_cache_key("engineer", "different response", {"task": "test"})
        
        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different keys
        assert len(key1) == 32  # MD5 hash length
    
    def test_mock_result_creation(self, evaluator):
        """Test mock result creation when evaluation is disabled."""
        evaluator.enabled = False
        
        result = evaluator._create_mock_result(
            "engineer", 
            "test response", 
            {"task": "test task"}
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.agent_type == "engineer"
        assert result.response_text == "test response"
        assert result.overall_score == 75.0
        assert len(result.criterion_scores) > 0
    
    @pytest.mark.asyncio
    async def test_evaluation_result_storage(self, evaluator):
        """Test evaluation result storage."""
        # Create mock result
        result = evaluator._create_mock_result("engineer", "test", {"task": "test"})
        
        # Store result
        await evaluator._store_evaluation_result(result)
        
        # Check if file was created
        eval_files = list(evaluator.evaluations_dir.glob("*.json"))
        assert len(eval_files) > 0
        
        # Verify file content
        with open(eval_files[0], 'r') as f:
            stored_data = json.load(f)
        
        assert stored_data["agent_type"] == "engineer"
        assert stored_data["response_text"] == "test"
    
    @pytest.mark.asyncio
    async def test_batch_evaluation(self, evaluator):
        """Test batch evaluation functionality."""
        # Create test corrections
        corrections = []
        for i in range(3):
            correction = CorrectionData(
                correction_id=f"test_correction_{i}",
                agent_type="engineer",
                original_response=f"original response {i}",
                user_correction=f"corrected response {i}",
                context={"task": f"task {i}"},
                correction_type=CorrectionType.CONTENT_CORRECTION,
                timestamp=datetime.now().isoformat()
            )
            corrections.append(correction)
        
        # Batch evaluate
        results = await evaluator.batch_evaluate_corrections(corrections)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, EvaluationResult)
            assert result.agent_type == "engineer"
    
    def test_evaluation_statistics(self, evaluator):
        """Test evaluation statistics collection."""
        # Add some mock timing data
        evaluator.evaluation_times = [100.0, 150.0, 200.0, 120.0]
        evaluator.cache_hits = 5
        evaluator.cache_misses = 3
        
        stats = evaluator.get_evaluation_statistics()
        
        assert stats["total_evaluations"] == 4
        assert stats["average_time_ms"] == 142.5
        assert stats["cache_hit_rate"] == 62.5
        assert stats["enabled"] == evaluator.enabled
    
    @pytest.mark.asyncio
    async def test_cleanup_old_evaluations(self, evaluator):
        """Test cleanup of old evaluation files."""
        # Create some test files
        old_file = evaluator.evaluations_dir / "old_eval.json"
        old_file.write_text('{"test": "data"}')
        
        # Set file time to be old
        old_time = time.time() - (48 * 3600)  # 48 hours ago
        os.utime(old_file, (old_time, old_time))
        
        # Run cleanup
        cleanup_result = await evaluator.cleanup_old_evaluations(days_to_keep=1)
        
        assert cleanup_result["removed_files"] == 1
        assert not old_file.exists()


class TestEvaluationIntegrationService:
    """Test the EvaluationIntegrationService class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        return Config({
            "enable_evaluation": True,
            "evaluation_storage_path": temp_dir,
            "auto_evaluate_corrections": True,
            "batch_evaluation_enabled": True
        })
    
    @pytest.fixture
    def integration_service(self, test_config):
        """Create EvaluationIntegrationService instance."""
        return EvaluationIntegrationService(test_config)
    
    def test_integration_service_initialization(self, integration_service):
        """Test integration service initialization."""
        assert integration_service is not None
        assert integration_service.config is not None
        assert integration_service.correction_capture is not None
        assert integration_service.evaluator is not None
        assert integration_service.integration_dir.exists()
    
    @pytest.mark.asyncio
    async def test_background_tasks_management(self, integration_service):
        """Test background tasks start and stop."""
        # Start background tasks
        await integration_service.start_background_tasks()
        assert len(integration_service.background_tasks) > 0
        
        # Stop background tasks
        await integration_service.stop_background_tasks()
        assert len(integration_service.background_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_capture_and_evaluate_correction(self, integration_service):
        """Test correction capture with automatic evaluation."""
        correction_id, evaluation_result = await integration_service.capture_and_evaluate_correction(
            agent_type="engineer",
            original_response="def hello(): pass",
            user_correction="def hello(): print('Hello, World!')",
            context={"task": "create hello function"},
            correction_type=CorrectionType.CONTENT_CORRECTION,
            subprocess_id="test_subprocess",
            task_description="Create hello function"
        )
        
        assert correction_id is not None
        assert len(correction_id) > 0
        
        if evaluation_result:
            assert isinstance(evaluation_result, EvaluationResult)
            assert evaluation_result.agent_type == "engineer"
    
    @pytest.mark.asyncio
    async def test_evaluate_agent_response(self, integration_service):
        """Test agent response evaluation."""
        result = await integration_service.evaluate_agent_response(
            agent_type="engineer",
            response_text="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            context={"task": "implement fibonacci function"}
        )
        
        if result:
            assert isinstance(result, EvaluationResult)
            assert result.agent_type == "engineer"
    
    def test_integration_statistics(self, integration_service):
        """Test integration statistics collection."""
        stats = integration_service.get_integration_statistics()
        
        assert "integration_stats" in stats
        assert "correction_stats" in stats
        assert "evaluator_stats" in stats
        assert "service_enabled" in stats
    
    @pytest.mark.asyncio
    async def test_evaluation_history(self, integration_service):
        """Test evaluation history retrieval."""
        # Generate some test history
        await integration_service.capture_and_evaluate_correction(
            agent_type="engineer",
            original_response="test",
            user_correction="corrected test",
            context={"task": "test"},
            correction_type=CorrectionType.CONTENT_CORRECTION
        )
        
        history = await integration_service.get_evaluation_history(limit=10)
        
        assert isinstance(history, list)
        # History might be empty if evaluation is disabled
    
    @pytest.mark.asyncio
    async def test_agent_improvement_metrics(self, integration_service):
        """Test agent improvement metrics calculation."""
        metrics = await integration_service.get_agent_improvement_metrics("engineer")
        
        assert "agent_type" in metrics
        assert "total_evaluations" in metrics
        assert "average_score" in metrics
        assert "improvement_trend" in metrics
        assert metrics["agent_type"] == "engineer"


class TestEvaluationMetricsSystem:
    """Test the EvaluationMetricsSystem class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        return Config({
            "enable_evaluation_metrics": True,
            "evaluation_storage_path": temp_dir
        })
    
    @pytest.fixture
    def metrics_system(self, test_config):
        """Create EvaluationMetricsSystem instance."""
        return EvaluationMetricsSystem(test_config)
    
    def test_metrics_system_initialization(self, metrics_system):
        """Test metrics system initialization."""
        assert metrics_system is not None
        assert metrics_system.config is not None
        assert metrics_system.metrics_dir.exists()
        assert len(metrics_system.benchmarks) > 0
    
    def test_benchmark_initialization(self, metrics_system):
        """Test performance benchmark initialization."""
        benchmarks = metrics_system.benchmarks
        
        assert "overall_score" in benchmarks
        assert "response_time" in benchmarks
        assert benchmarks["overall_score"].target_value == 85.0
        assert benchmarks["response_time"].target_value == 100.0
    
    def test_evaluation_recording(self, metrics_system):
        """Test evaluation result recording."""
        # Create mock evaluation result
        evaluation_result = EvaluationResult(
            evaluation_id="test_eval",
            agent_type="engineer",
            response_text="test response",
            context={"task": "test"},
            overall_score=85.0,
            criterion_scores=[
                EvaluationScore(
                    criterion=EvaluationCriteria.CORRECTNESS,
                    score=90.0,
                    explanation="Good correctness",
                    confidence=0.9
                )
            ],
            evaluation_time_ms=150.0,
            provider=EvaluationProvider.OPENAI
        )
        
        # Record evaluation
        metrics_system.record_evaluation(evaluation_result)
        
        # Check if metrics were recorded
        assert len(metrics_system.metrics) > 0
        assert len(metrics_system.agent_metrics["engineer"]) > 0
    
    def test_correction_recording(self, metrics_system):
        """Test correction data recording."""
        # Create mock correction data
        correction_data = CorrectionData(
            correction_id="test_correction",
            agent_type="engineer",
            original_response="original",
            user_correction="corrected",
            context={"task": "test"},
            correction_type=CorrectionType.CONTENT_CORRECTION,
            timestamp=datetime.now().isoformat()
        )
        
        # Record correction
        metrics_system.record_correction(correction_data)
        
        # Check if metrics were recorded
        assert len(metrics_system.metrics) > 0
        assert len(metrics_system.agent_metrics["engineer"]) > 0
    
    def test_agent_metrics_retrieval(self, metrics_system):
        """Test agent metrics retrieval."""
        # Add some test data
        metrics_system.total_evaluations_processed = 10
        
        agent_metrics = metrics_system.get_agent_metrics("engineer")
        
        assert "agent_type" in agent_metrics
        assert "metrics" in agent_metrics
        assert "summary" in agent_metrics
        assert agent_metrics["agent_type"] == "engineer"
    
    def test_system_health_calculation(self, metrics_system):
        """Test system health calculation."""
        health = metrics_system.get_system_health()
        
        assert "health_score" in health
        assert "uptime_seconds" in health
        assert "evaluations_per_hour" in health
        assert "total_evaluations" in health
        assert "metrics_enabled" in health
        assert 0 <= health["health_score"] <= 100
    
    def test_performance_benchmarks(self, metrics_system):
        """Test performance benchmarks comparison."""
        # Add some test metrics
        metrics_system._record_metric(
            "overall_score",
            metrics_system.MetricType.RESPONSE_QUALITY,
            75.0,
            "engineer"
        )
        
        benchmarks = metrics_system.get_performance_benchmarks("engineer")
        
        assert isinstance(benchmarks, dict)
        # May be empty if no matching benchmarks
    
    def test_improvement_recommendations(self, metrics_system):
        """Test improvement recommendations generation."""
        recommendations = metrics_system.generate_improvement_recommendations("engineer")
        
        assert isinstance(recommendations, list)
        # May be empty if no recommendations generated
    
    def test_metrics_export(self, metrics_system):
        """Test metrics export functionality."""
        export_data = metrics_system.export_metrics("engineer")
        
        assert "export_timestamp" in export_data
        assert "system_health" in export_data
        assert "metrics" in export_data
        assert "benchmarks" in export_data
        assert "recommendations" in export_data
    
    def test_metrics_cleanup(self, metrics_system):
        """Test metrics cleanup functionality."""
        # Add some test metrics
        metrics_system._record_metric(
            "test_metric",
            metrics_system.MetricType.RESPONSE_QUALITY,
            50.0,
            "engineer"
        )
        
        cleanup_result = metrics_system.cleanup_old_metrics(days_to_keep=0)
        
        assert "cleaned_metric_points" in cleanup_result
        assert cleanup_result["cleaned_metric_points"] >= 0


class TestEvaluationPerformanceManager:
    """Test the EvaluationPerformanceManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        return Config({
            "evaluation_performance_enabled": True,
            "evaluation_cache_max_size": 100,
            "evaluation_cache_ttl_seconds": 3600,
            "evaluation_batch_size": 5
        })
    
    @pytest.fixture
    def performance_manager(self, test_config):
        """Create EvaluationPerformanceManager instance."""
        return EvaluationPerformanceManager(test_config)
    
    def test_performance_manager_initialization(self, performance_manager):
        """Test performance manager initialization."""
        assert performance_manager is not None
        assert performance_manager.config is not None
        assert performance_manager.cache is not None
        assert performance_manager.circuit_breaker is not None
    
    def test_cache_functionality(self, performance_manager):
        """Test cache functionality."""
        cache = performance_manager.cache
        
        # Test put and get
        cache.put("test_key", "test_value")
        value = cache.get("test_key")
        
        assert value == "test_value"
        
        # Test statistics
        stats = cache.get_stats()
        assert "entries" in stats
        assert "hit_rate" in stats
        assert stats["entries"] == 1
    
    def test_circuit_breaker_functionality(self, performance_manager):
        """Test circuit breaker functionality."""
        circuit_breaker = performance_manager.circuit_breaker
        
        # Test initial state
        state = circuit_breaker.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
    
    @pytest.mark.asyncio
    async def test_performance_manager_initialization_with_evaluator(self, performance_manager, test_config):
        """Test performance manager initialization with evaluator."""
        evaluator = MirascopeEvaluator(test_config)
        
        await performance_manager.initialize(evaluator)
        
        assert performance_manager.evaluator is not None
        assert performance_manager.processor is not None
    
    def test_performance_statistics(self, performance_manager):
        """Test performance statistics collection."""
        stats = performance_manager.get_performance_stats()
        
        assert "enabled" in stats
        assert "uptime_seconds" in stats
        assert "total_evaluations" in stats
        assert "cache_stats" in stats
        assert "circuit_breaker_state" in stats
    
    def test_cache_clearing(self, performance_manager):
        """Test cache clearing functionality."""
        # Add some data to cache
        performance_manager.cache.put("test", "value")
        
        # Clear cache
        result = performance_manager.clear_cache()
        
        assert result["cache_cleared"] is True
        assert "timestamp" in result
        
        # Verify cache is empty
        cache_stats = performance_manager.cache.get_stats()
        assert cache_stats["entries"] == 0
    
    def test_circuit_breaker_reset(self, performance_manager):
        """Test circuit breaker reset functionality."""
        result = performance_manager.reset_circuit_breaker()
        
        assert result["circuit_breaker_reset"] is True
        assert "timestamp" in result
        
        # Verify circuit breaker state
        state = performance_manager.circuit_breaker.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 0


class TestEvaluationMonitor:
    """Test the EvaluationMonitor class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        return Config({
            "evaluation_monitoring_enabled": True,
            "evaluation_storage_path": temp_dir
        })
    
    @pytest.fixture
    def monitor(self, test_config):
        """Create EvaluationMonitor instance."""
        return EvaluationMonitor(test_config)
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor is not None
        assert monitor.config is not None
        assert monitor.monitoring_dir.exists()
        assert len(monitor.health_checks) > 0
        assert len(monitor.alert_rules) > 0
    
    def test_health_checks_initialization(self, monitor):
        """Test health checks initialization."""
        health_checks = monitor.health_checks
        
        assert "system_resources" in health_checks
        assert "evaluation_service" in health_checks
        assert "performance_metrics" in health_checks
        assert "integration_service" in health_checks
        assert "storage_health" in health_checks
    
    def test_alert_rules_initialization(self, monitor):
        """Test alert rules initialization."""
        alert_rules = monitor.alert_rules
        
        assert "high_cpu_usage" in alert_rules
        assert "high_memory_usage" in alert_rules
        assert "high_error_rate" in alert_rules
        assert "slow_response_time" in alert_rules
    
    def test_system_resources_health_check(self, monitor):
        """Test system resources health check."""
        result = monitor._check_system_resources()
        
        assert "status" in result
        assert "cpu_percent" in result
        assert "memory_percent" in result
        assert "disk_percent" in result
        assert "timestamp" in result
    
    def test_storage_health_check(self, monitor):
        """Test storage health check."""
        result = monitor._check_storage_health()
        
        assert "status" in result
        assert "directories" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_monitoring_tasks_management(self, monitor):
        """Test monitoring tasks start and stop."""
        # Start monitoring
        await monitor.start_monitoring()
        
        # Check tasks are running
        assert monitor.monitor_task is not None
        assert monitor.health_check_task is not None
        assert monitor.alert_check_task is not None
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        # Check tasks are stopped
        assert monitor.shutdown_event.is_set()
    
    def test_monitoring_status(self, monitor):
        """Test monitoring status retrieval."""
        status = monitor.get_monitoring_status()
        
        assert "enabled" in status
        assert "uptime_seconds" in status
        assert "overall_health" in status
        assert "health_checks" in status
        assert "active_alerts" in status
    
    def test_health_check_details(self, monitor):
        """Test health check details retrieval."""
        details = monitor.get_health_check_details()
        
        assert isinstance(details, dict)
        for name, detail in details.items():
            assert "description" in detail
            assert "enabled" in detail
            assert "interval_seconds" in detail
    
    def test_alert_rules_retrieval(self, monitor):
        """Test alert rules retrieval."""
        rules = monitor.get_alert_rules()
        
        assert isinstance(rules, dict)
        for name, rule in rules.items():
            assert "description" in rule
            assert "condition" in rule
            assert "severity" in rule
            assert "threshold" in rule
    
    def test_monitoring_report_generation(self, monitor):
        """Test monitoring report generation."""
        report = monitor.generate_monitoring_report()
        
        assert "report_timestamp" in report
        assert "monitoring_status" in report
        assert "health_checks" in report
        assert "alert_rules" in report
        assert "system_metrics" in report
    
    @pytest.mark.asyncio
    async def test_monitoring_report_saving(self, monitor):
        """Test monitoring report saving."""
        report_path = await monitor.save_monitoring_report()
        
        assert report_path is not None
        assert Path(report_path).exists()
        
        # Verify report content
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        assert "report_timestamp" in report_data
        assert "monitoring_status" in report_data


class TestSystemIntegration:
    """Test complete system integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        return Config({
            "enable_evaluation": True,
            "evaluation_storage_path": temp_dir,
            "evaluation_performance_enabled": True,
            "evaluation_monitoring_enabled": True,
            "auto_evaluate_corrections": True
        })
    
    @pytest.mark.asyncio
    async def test_full_system_integration(self, test_config):
        """Test full system integration."""
        # Initialize all components
        correction_capture = CorrectionCapture(test_config)
        evaluator = MirascopeEvaluator(test_config)
        integration_service = EvaluationIntegrationService(test_config)
        metrics_system = EvaluationMetricsSystem(test_config)
        performance_manager = EvaluationPerformanceManager(test_config)
        monitor = EvaluationMonitor(test_config)
        
        # Initialize performance manager with evaluator
        await performance_manager.initialize(evaluator)
        
        # Register services with monitor
        monitor.register_services(
            evaluator=evaluator,
            integration_service=integration_service,
            metrics_system=metrics_system,
            performance_manager=performance_manager
        )
        
        # Start background tasks
        await integration_service.start_background_tasks()
        await monitor.start_monitoring()
        
        # Test end-to-end workflow
        correction_id, evaluation_result = await integration_service.capture_and_evaluate_correction(
            agent_type="engineer",
            original_response="def test(): pass",
            user_correction="def test(): return 'Hello, World!'",
            context={"task": "implement test function"},
            correction_type=CorrectionType.CONTENT_CORRECTION
        )
        
        # Verify correction was captured
        assert correction_id is not None
        assert len(correction_id) > 0
        
        # Record metrics if evaluation succeeded
        if evaluation_result:
            metrics_system.record_evaluation(evaluation_result)
        
        # Get system status
        integration_stats = integration_service.get_integration_statistics()
        performance_stats = performance_manager.get_performance_stats()
        monitoring_status = monitor.get_monitoring_status()
        
        # Verify system is working
        assert integration_stats["service_enabled"] == integration_service.enabled
        assert performance_stats["enabled"] == performance_manager.enabled
        assert monitoring_status["enabled"] == monitor.enabled
        
        # Cleanup
        await integration_service.stop_background_tasks()
        await monitor.stop_monitoring()
        await performance_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, test_config):
        """Test error handling and recovery mechanisms."""
        # Test with invalid configuration
        invalid_config = Config({
            "enable_evaluation": True,
            "evaluation_storage_path": "/invalid/path/that/does/not/exist",
            "evaluation_provider": "invalid_provider"
        })
        
        # Components should handle invalid configuration gracefully
        evaluator = MirascopeEvaluator(invalid_config)
        integration_service = EvaluationIntegrationService(invalid_config)
        
        # Test error handling in integration service
        correction_id, evaluation_result = await integration_service.capture_and_evaluate_correction(
            agent_type="engineer",
            original_response="test",
            user_correction="corrected test",
            context={"task": "test"},
            correction_type=CorrectionType.CONTENT_CORRECTION
        )
        
        # Should handle errors gracefully
        assert isinstance(correction_id, str)
        # evaluation_result may be None if evaluation failed
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, test_config):
        """Test system performance under load."""
        # Initialize system
        evaluator = MirascopeEvaluator(test_config)
        performance_manager = EvaluationPerformanceManager(test_config)
        await performance_manager.initialize(evaluator)
        
        # Generate load
        tasks = []
        for i in range(20):
            task = performance_manager.evaluate_response(
                agent_type="engineer",
                response_text=f"test response {i}",
                context={"task": f"task {i}"}
            )
            tasks.append(task)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify results
        successful_results = [r for r in results if isinstance(r, EvaluationResult)]
        error_results = [r for r in results if isinstance(r, Exception)]
        
        # At least some should succeed
        assert len(successful_results) > 0
        
        # Get performance stats
        stats = performance_manager.get_performance_stats()
        assert stats["total_evaluations"] > 0
        
        # Cleanup
        await performance_manager.shutdown()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])