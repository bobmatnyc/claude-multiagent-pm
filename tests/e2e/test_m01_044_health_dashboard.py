"""
Unit tests for M01-044 Comprehensive Health Slash Command implementation.

Tests the core infrastructure including health data models, orchestrator,
circuit breaker, caching, and CLI integration.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

# Import the components to test
from claude_pm.models.health import (
    HealthStatus,
    HealthReport,
    HealthDashboard,
    ServiceHealthReport,
    SubsystemHealth,
    create_health_report,
    create_health_dashboard,
    create_service_health_report,
)
from claude_pm.interfaces.health import HealthCollector
from claude_pm.utils.performance import (
    CircuitBreaker,
    HealthCache,
    CircuitBreakerOpenError,
    CacheEntry,
)
from claude_pm.services.health_dashboard import HealthDashboardOrchestrator
from claude_pm.adapters.health_adapter import HealthMonitorServiceAdapter


class TestHealthModels:
    """Test health data models and factory functions."""

    def test_health_status_enum(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.DOWN.value == "down"
        assert HealthStatus.ERROR.value == "error"
        assert HealthStatus.UNKNOWN.value == "unknown"

    def test_service_health_report_creation(self):
        """Test ServiceHealthReport creation and serialization."""
        report = create_service_health_report(
            name="test_service",
            status=HealthStatus.HEALTHY,
            message="Service is running",
            response_time_ms=150.5,
        )

        assert report.name == "test_service"
        assert report.status == HealthStatus.HEALTHY
        assert report.message == "Service is running"
        assert report.response_time_ms == 150.5
        assert isinstance(report.timestamp, datetime)

        # Test serialization
        data = report.to_dict()
        assert data["name"] == "test_service"
        assert data["status"] == "healthy"
        assert data["response_time_ms"] == 150.5

    def test_health_report_creation_and_services(self):
        """Test HealthReport creation and service management."""
        report = create_health_report(version="3.0.0", response_time_ms=250.0)

        assert report.version == "3.0.0"
        assert report.response_time_ms == 250.0
        assert report.overall_status == HealthStatus.UNKNOWN
        assert report.total_services == 0
        assert report.overall_health_percentage == 0.0

        # Add services
        healthy_service = create_service_health_report("service1", HealthStatus.HEALTHY)
        degraded_service = create_service_health_report("service2", HealthStatus.DEGRADED)
        unhealthy_service = create_service_health_report("service3", HealthStatus.UNHEALTHY)

        report.add_service(healthy_service)
        report.add_service(degraded_service)
        report.add_service(unhealthy_service)

        assert report.total_services == 3
        assert report.healthy_services == 1
        assert report.degraded_services == 1
        assert report.unhealthy_services == 1
        assert abs(report.overall_health_percentage - 33.33) < 0.1

    def test_health_report_cache_detection(self):
        """Test cache hit detection."""
        # Fast response (cache hit)
        fast_report = create_health_report(response_time_ms=50.0)
        assert fast_report.is_cache_hit

        # Slow response (not cache hit)
        slow_report = create_health_report(response_time_ms=500.0)
        assert not slow_report.is_cache_hit

    def test_subsystem_health_calculation(self):
        """Test SubsystemHealth calculations."""
        services = [
            create_service_health_report("svc1", HealthStatus.HEALTHY),
            create_service_health_report("svc2", HealthStatus.HEALTHY),
            create_service_health_report("svc3", HealthStatus.DEGRADED),
            create_service_health_report("svc4", HealthStatus.UNHEALTHY),
        ]

        subsystem = SubsystemHealth(
            name="test_subsystem",
            status=HealthStatus.DEGRADED,
            services=services,
            total_services=4,
            healthy_services=2,
            degraded_services=1,
            unhealthy_services=1,
            down_services=0,
        )

        assert subsystem.health_percentage == 50.0  # 2/4 * 100

        data = subsystem.to_dict()
        assert data["name"] == "test_subsystem"
        assert data["health_percentage"] == 50.0
        assert len(data["services"]) == 4

    def test_health_dashboard_creation(self):
        """Test HealthDashboard creation and functionality."""
        report = create_health_report()
        report.add_service(create_service_health_report("test", HealthStatus.HEALTHY))

        dashboard = create_health_dashboard(report)

        assert dashboard.current_report == report
        assert dashboard.overall_status == report.overall_status
        assert len(dashboard.historical_reports) == 0

        # Test adding historical reports
        historical_report = create_health_report()
        dashboard.add_historical_report(historical_report)
        assert len(dashboard.historical_reports) == 1

        # Test serialization
        data = dashboard.to_dict()
        assert "current_report" in data
        assert "trends" in data
        assert "performance_metrics" in data


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        cb = CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            failure_rate_threshold=50.0,
            recovery_timeout=30.0,
        )

        assert cb.name == "test_breaker"
        assert cb.failure_threshold == 3
        assert cb.state.value == "closed"
        assert cb.stats.total_requests == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_successful_calls(self):
        """Test circuit breaker with successful calls."""
        cb = CircuitBreaker("test", failure_threshold=3)

        async def successful_function():
            return "success"

        # Make several successful calls
        for i in range(5):
            result = await cb.call(successful_function)
            assert result == "success"

        assert cb.state.value == "closed"
        assert cb.stats.total_requests == 5
        assert cb.stats.success_requests == 5
        assert cb.stats.failed_requests == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_opening(self):
        """Test circuit breaker opening after failures."""
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=0.1)

        async def failing_function():
            raise Exception("Test failure")

        # Cause failures to open circuit
        for i in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_function)

        assert cb.state.value == "open"
        assert cb.stats.failed_requests == 3

        # Subsequent calls should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(failing_function)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery process."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1, success_threshold=2)

        async def failing_function():
            raise Exception("Test failure")

        async def successful_function():
            return "success"

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_function)

        assert cb.state.value == "open"

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # First call should transition to half-open
        result = await cb.call(successful_function)
        assert result == "success"
        assert cb.state.value == "half_open"

        # Second successful call should close circuit
        result = await cb.call(successful_function)
        assert result == "success"
        assert cb.state.value == "closed"

    def test_circuit_breaker_manual_reset(self):
        """Test manual circuit breaker reset."""
        from claude_pm.utils.performance import CircuitBreakerState

        cb = CircuitBreaker("test")
        cb._state = CircuitBreakerState.OPEN
        cb._consecutive_failures = 5

        cb.reset()

        assert cb.state.value == "closed"
        assert cb._consecutive_failures == 0

    def test_circuit_breaker_status(self):
        """Test circuit breaker status reporting."""
        cb = CircuitBreaker("test", failure_threshold=3)

        status = cb.get_status()

        assert status["name"] == "test"
        assert status["state"] == "closed"
        assert "stats" in status
        assert "config" in status
        assert status["config"]["failure_threshold"] == 3


class TestHealthCache:
    """Test health cache implementation."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = HealthCache(default_ttl_seconds=30.0, max_size=100)

        assert cache.default_ttl_seconds == 30.0
        assert cache.max_size == 100
        assert len(cache) == 0

    def test_cache_set_and_get(self):
        """Test cache set and get operations."""
        cache = HealthCache(default_ttl_seconds=60.0)
        report = create_health_report()

        # Set value
        cache.set("test_key", report)
        assert len(cache) == 1

        # Get value
        retrieved = cache.get("test_key")
        assert retrieved == report

        # Non-existent key
        assert cache.get("nonexistent") is None

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = HealthCache(default_ttl_seconds=0.1)  # 100ms TTL
        report = create_health_report()

        cache.set("test_key", report)

        # Should be available immediately
        assert cache.get("test_key") == report

        # Wait for expiration
        time.sleep(0.2)

        # Should be expired
        assert cache.get("test_key") is None

    def test_cache_max_size_eviction(self):
        """Test cache eviction when max size reached."""
        cache = HealthCache(max_size=2)

        report1 = create_health_report()
        report2 = create_health_report()
        report3 = create_health_report()

        cache.set("key1", report1)
        cache.set("key2", report2)
        assert len(cache) == 2

        # Adding third item should evict oldest
        cache.set("key3", report3)
        assert len(cache) == 2
        assert cache.get("key1") is None  # Should be evicted
        assert cache.get("key2") == report2
        assert cache.get("key3") == report3

    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = HealthCache(default_ttl_seconds=0.1)

        report1 = create_health_report()
        report2 = create_health_report()

        cache.set("key1", report1)
        time.sleep(0.05)  # Partial wait
        cache.set("key2", report2)

        time.sleep(0.15)  # Wait longer for first to expire

        expired_count = cache.cleanup_expired()
        assert expired_count >= 1  # May be 1 or 2 depending on timing
        assert cache.get("key1") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = HealthCache()
        report = create_health_report()

        # Initial stats
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

        # Cache miss
        cache.get("nonexistent")
        stats = cache.get_stats()
        assert stats["misses"] == 1

        # Cache set and hit
        cache.set("key1", report)
        cache.get("key1")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 50.0


class MockHealthCollector(HealthCollector):
    """Mock health collector for testing."""

    def __init__(self, name: str, subsystem: str, services: list, should_fail: bool = False):
        super().__init__(name)
        self._subsystem = subsystem
        self._services = services
        self._should_fail = should_fail

    async def collect_health(self):
        if self._should_fail:
            raise Exception(f"Mock collector {self.name} failed")

        reports = []
        for service_name in self._services:
            status = HealthStatus.HEALTHY if not self._should_fail else HealthStatus.ERROR
            report = create_service_health_report(
                name=service_name,
                status=status,
                message=f"Mock service {service_name}",
                response_time_ms=100.0,
            )
            reports.append(report)

        return reports

    def get_subsystem_name(self):
        return self._subsystem

    def get_service_names(self):
        return self._services


class TestHealthDashboardOrchestrator:
    """Test health dashboard orchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = HealthDashboardOrchestrator(
            cache_ttl_seconds=30.0, max_parallel_collectors=3, global_timeout_seconds=2.0
        )

        assert orchestrator.cache_ttl_seconds == 30.0
        assert orchestrator.max_parallel_collectors == 3
        assert orchestrator.global_timeout_seconds == 2.0
        assert len(orchestrator._collectors) == 2  # Default legacy adapter + framework services

    @pytest.mark.asyncio
    async def test_add_remove_collectors(self):
        """Test adding and removing collectors."""
        orchestrator = HealthDashboardOrchestrator()

        collector = MockHealthCollector(
            "test_collector", "Test Subsystem", ["service1", "service2"]
        )

        # Add collector
        orchestrator.add_collector(collector)
        assert len(orchestrator._collectors) == 3  # +1 for defaults (2)
        assert "test_collector" in orchestrator._circuit_breakers

        # Remove collector
        success = orchestrator.remove_collector("test_collector")
        assert success
        assert len(orchestrator._collectors) == 2
        assert "test_collector" not in orchestrator._circuit_breakers

        # Remove non-existent collector
        success = orchestrator.remove_collector("nonexistent")
        assert not success

    @pytest.mark.asyncio
    async def test_health_dashboard_generation(self):
        """Test health dashboard generation."""
        orchestrator = HealthDashboardOrchestrator()

        # Add mock collectors
        collector1 = MockHealthCollector(
            "collector1", "Framework Services", ["service1", "service2"]
        )
        collector2 = MockHealthCollector("collector2", "External APIs", ["api1", "api2"])

        orchestrator.add_collector(collector1)
        orchestrator.add_collector(collector2)

        # Generate dashboard
        dashboard = await orchestrator.get_health_dashboard()

        assert isinstance(dashboard, HealthDashboard)
        assert dashboard.current_report.total_services > 0
        assert len(dashboard.current_report.subsystems) > 0
        assert dashboard.total_response_time_ms > 0

    @pytest.mark.asyncio
    async def test_health_dashboard_caching(self):
        """Test health dashboard caching."""
        orchestrator = HealthDashboardOrchestrator(cache_ttl_seconds=1.0)

        collector = MockHealthCollector("test", "Test", ["service1"])
        orchestrator.add_collector(collector)

        # First call should not be cached
        dashboard1 = await orchestrator.get_health_dashboard()
        assert not dashboard1.current_report.is_cache_hit

        # Second call should be cached
        dashboard2 = await orchestrator.get_health_dashboard()
        assert dashboard2.current_report.is_cache_hit

        # Force refresh should bypass cache
        dashboard3 = await orchestrator.get_health_dashboard(force_refresh=True)
        assert not dashboard3.current_report.is_cache_hit

    @pytest.mark.asyncio
    async def test_collector_failure_handling(self):
        """Test handling of collector failures."""
        orchestrator = HealthDashboardOrchestrator()

        # Add failing collector
        failing_collector = MockHealthCollector(
            "failing", "Failing Subsystem", ["bad_service"], should_fail=True
        )
        orchestrator.add_collector(failing_collector)

        # Dashboard should still generate with error reports
        dashboard = await orchestrator.get_health_dashboard()

        assert dashboard.current_report.total_services > 0
        # Should have error services from failing collector
        error_services = [
            s for s in dashboard.current_report.services if s.status == HealthStatus.ERROR
        ]
        assert len(error_services) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_health_check(self):
        """Test orchestrator self health check."""
        orchestrator = HealthDashboardOrchestrator()

        health_status = await orchestrator.health_check()

        assert "status" in health_status
        assert "response_time_ms" in health_status
        assert "performance_ok" in health_status
        assert "cache_ok" in health_status
        assert "circuit_breakers_ok" in health_status
        assert "collectors_ok" in health_status

    def test_orchestrator_stats(self):
        """Test orchestrator statistics."""
        orchestrator = HealthDashboardOrchestrator()

        stats = orchestrator.get_orchestrator_stats()

        assert "orchestrator" in stats
        assert "cache" in stats
        assert "circuit_breakers" in stats
        assert "collectors" in stats
        assert "config" in stats

        # Check orchestrator stats
        orch_stats = stats["orchestrator"]
        assert "total_requests" in orch_stats
        assert "cache_hits" in orch_stats
        assert "successful_collections" in orch_stats


class TestHealthMonitorServiceAdapter:
    """Test health monitor service adapter."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = HealthMonitorServiceAdapter()

        assert adapter.name == "health_monitor_service"
        assert adapter.get_subsystem_name() == "Legacy Health Monitor"
        assert len(adapter.get_service_names()) > 0

    @pytest.mark.asyncio
    async def test_adapter_with_mock_service(self):
        """Test adapter with mock health service."""
        mock_service = Mock()
        mock_service.running = True
        mock_service.get_health_status = AsyncMock(
            return_value={
                "overall_health": 85,
                "total_projects": 10,
                "healthy_projects": 8,
                "alerts": 2,
                "framework_compliance": 90,
            }
        )
        mock_service.run_health_check = AsyncMock(
            return_value={"status": "completed", "timestamp": datetime.now().isoformat()}
        )

        adapter = HealthMonitorServiceAdapter(mock_service)

        reports = await adapter.collect_health()

        assert len(reports) >= 1
        service_report = reports[0]
        assert service_report.name == "health_monitor_service"
        assert service_report.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    @pytest.mark.asyncio
    async def test_adapter_file_parsing(self):
        """Test adapter parsing health report file."""
        # Create mock health report data
        mock_health_data = {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "mem0ai_mcp": {
                    "status": "healthy",
                    "description": "mem0AI MCP Service",
                    "response_time": 50,
                    "port": 8002,
                }
            },
            "projects": {"test_project": {"status": "healthy"}},
            "framework": {"compliance_percentage": 85},
        }

        adapter = HealthMonitorServiceAdapter()

        # Mock file reading
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                with patch("json.load", return_value=mock_health_data):
                    reports = await adapter.collect_health()

        assert len(reports) >= 1
        # Should have parsed services, projects, and framework reports
        service_names = [r.name for r in reports]
        assert "mem0ai_mcp" in service_names


@pytest.mark.asyncio
async def test_integration_comprehensive_health_command():
    """Integration test for the comprehensive health command."""
    from claude_pm.services.health_dashboard import HealthDashboardOrchestrator

    # Initialize orchestrator
    orchestrator = HealthDashboardOrchestrator()

    # Add test collectors
    collector1 = MockHealthCollector(
        "integration_test1", "Test Framework", ["service1", "service2"]
    )
    collector2 = MockHealthCollector("integration_test2", "Test External", ["api1"])

    orchestrator.add_collector(collector1)
    orchestrator.add_collector(collector2)

    # Generate dashboard
    dashboard = await orchestrator.get_health_dashboard()

    # Verify dashboard structure
    assert isinstance(dashboard, HealthDashboard)
    assert dashboard.current_report.total_services > 0
    assert dashboard.current_report.overall_status != HealthStatus.UNKNOWN
    assert dashboard.total_response_time_ms > 0

    # Verify subsystems
    assert len(dashboard.current_report.subsystems) >= 2

    # Verify performance metrics
    dashboard.calculate_performance_metrics()
    assert "service_distribution" in dashboard.performance_metrics

    # Test JSON serialization
    json_data = dashboard.to_json()
    assert isinstance(json_data, str)

    # Test caching
    dashboard2 = await orchestrator.get_health_dashboard()
    assert dashboard2.current_report.is_cache_hit

    # Test orchestrator stats
    stats = orchestrator.get_orchestrator_stats()
    assert stats["orchestrator"]["total_requests"] >= 2
    assert stats["orchestrator"]["cache_hits"] >= 1


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
