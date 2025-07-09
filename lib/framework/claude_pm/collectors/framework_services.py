"""
Framework Services Health Collector.

Monitors core Claude PM framework services including service manager,
memory services, and other framework components.
"""

import asyncio
from datetime import datetime
from typing import List, Optional

from ..interfaces.health import HealthCollector
from ..models.health import ServiceHealthReport, HealthStatus, create_service_health_report
from ..core.service_manager import ServiceManager


class FrameworkServicesCollector(HealthCollector):
    """
    Health collector for Claude PM framework services.
    
    Monitors the health of core framework components including:
    - Service Manager
    - Memory Service
    - Project Service
    - Multi-Agent Orchestrator
    """
    
    def __init__(self, service_manager: Optional[ServiceManager] = None, timeout_seconds: float = 1.5):
        """
        Initialize framework services collector.
        
        Args:
            service_manager: Optional ServiceManager instance
            timeout_seconds: Timeout for health collection
        """
        super().__init__("framework_services", timeout_seconds)
        self._service_manager = service_manager
    
    async def collect_health(self) -> List[ServiceHealthReport]:
        """
        Collect health reports from framework services.
        
        Returns:
            List of ServiceHealthReport objects for framework services
        """
        reports = []
        
        # Service Manager health
        reports.append(await self._check_service_manager())
        
        # Individual service health (if service manager is available)
        if self._service_manager:
            service_reports = await self._check_individual_services()
            reports.extend(service_reports)
        else:
            # Fallback: try to check services independently
            reports.extend(await self._check_services_independently())
        
        return reports
    
    async def _check_service_manager(self) -> ServiceHealthReport:
        """Check service manager health."""
        try:
            if self._service_manager is None:
                return create_service_health_report(
                    name="service_manager",
                    status=HealthStatus.UNKNOWN,
                    message="Service manager not available",
                    response_time_ms=0.0
                )
            
            start_time = asyncio.get_event_loop().time()
            
            # Get service status
            service_status = self._service_manager.get_service_status()
            running_services = sum(1 for status in service_status.values() if status.get("running", False))
            total_services = len(service_status)
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Determine health status
            if total_services == 0:
                status = HealthStatus.UNKNOWN
                message = "No services registered"
            elif running_services == total_services:
                status = HealthStatus.HEALTHY
                message = f"All {total_services} services running"
            elif running_services > total_services * 0.5:
                status = HealthStatus.DEGRADED
                message = f"{running_services}/{total_services} services running"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Only {running_services}/{total_services} services running"
            
            return create_service_health_report(
                name="service_manager",
                status=status,
                message=message,
                response_time_ms=response_time,
                metrics={
                    "total_services": total_services,
                    "running_services": running_services,
                    "service_names": list(service_status.keys())
                }
            )
            
        except Exception as e:
            return create_service_health_report(
                name="service_manager",
                status=HealthStatus.ERROR,
                message=f"Service manager error: {str(e)}",
                error=str(e)
            )
    
    async def _check_individual_services(self) -> List[ServiceHealthReport]:
        """Check individual framework services through service manager."""
        reports = []
        
        try:
            # Get all services health
            health_results = await self._service_manager.health_check_all()
            
            for service_name, health in health_results.items():
                # Map service health to our format
                if health.status == "healthy":
                    status = HealthStatus.HEALTHY
                elif health.status == "degraded":
                    status = HealthStatus.DEGRADED
                elif health.status == "unhealthy":
                    status = HealthStatus.UNHEALTHY
                else:
                    status = HealthStatus.UNKNOWN
                
                report = create_service_health_report(
                    name=f"framework_{service_name}",
                    status=status,
                    message=health.message,
                    response_time_ms=None,  # Not available from base service health
                    metrics=health.metrics,
                    checks=health.checks
                )
                reports.append(report)
                
        except Exception as e:
            # Create error report for service health collection
            error_report = create_service_health_report(
                name="framework_service_health",
                status=HealthStatus.ERROR,
                message=f"Failed to collect service health: {str(e)}",
                error=str(e)
            )
            reports.append(error_report)
        
        return reports
    
    async def _check_services_independently(self) -> List[ServiceHealthReport]:
        """Check services independently when service manager is not available."""
        reports = []
        
        # Check for common framework services by trying imports
        service_checks = [
            ("memory_service", self._check_memory_service),
            ("project_service", self._check_project_service),
            ("multi_agent_orchestrator", self._check_multi_agent_orchestrator)
        ]
        
        for service_name, check_func in service_checks:
            try:
                report = await check_func()
                reports.append(report)
            except Exception as e:
                error_report = create_service_health_report(
                    name=service_name,
                    status=HealthStatus.ERROR,
                    message=f"Error checking {service_name}: {str(e)}",
                    error=str(e)
                )
                reports.append(error_report)
        
        return reports
    
    async def _check_memory_service(self) -> ServiceHealthReport:
        """Check memory service availability."""
        try:
            from ..services.memory_service import MemoryService
            
            # Try to create instance (doesn't start it)
            memory_service = MemoryService()
            
            return create_service_health_report(
                name="memory_service",
                status=HealthStatus.UNKNOWN,
                message="Memory service class available but not initialized",
                metrics={"import_successful": True}
            )
            
        except ImportError as e:
            return create_service_health_report(
                name="memory_service",
                status=HealthStatus.ERROR,
                message=f"Memory service import failed: {str(e)}",
                error=str(e)
            )
    
    async def _check_project_service(self) -> ServiceHealthReport:
        """Check project service availability."""
        try:
            from ..services.project_service import ProjectService
            
            # Try to create instance
            project_service = ProjectService()
            
            return create_service_health_report(
                name="project_service",
                status=HealthStatus.UNKNOWN,
                message="Project service class available but not initialized",
                metrics={"import_successful": True}
            )
            
        except ImportError as e:
            return create_service_health_report(
                name="project_service",
                status=HealthStatus.ERROR,
                message=f"Project service import failed: {str(e)}",
                error=str(e)
            )
    
    async def _check_multi_agent_orchestrator(self) -> ServiceHealthReport:
        """Check multi-agent orchestrator availability."""
        try:
            from ..services.multi_agent_orchestrator import MultiAgentOrchestrator
            
            return create_service_health_report(
                name="multi_agent_orchestrator",
                status=HealthStatus.UNKNOWN,
                message="Multi-agent orchestrator class available but not initialized",
                metrics={"import_successful": True}
            )
            
        except ImportError as e:
            return create_service_health_report(
                name="multi_agent_orchestrator",
                status=HealthStatus.ERROR,
                message=f"Multi-agent orchestrator import failed: {str(e)}",
                error=str(e)
            )
    
    def get_subsystem_name(self) -> str:
        """Get the subsystem name for this collector."""
        return "Framework Services"
    
    def get_service_names(self) -> List[str]:
        """Get the list of service names this collector monitors."""
        return [
            "service_manager",
            "framework_memory_service",
            "framework_project_service", 
            "framework_multi_agent_orchestrator",
            "memory_service",
            "project_service",
            "multi_agent_orchestrator"
        ]
    
    def set_service_manager(self, service_manager: ServiceManager) -> None:
        """Set the service manager instance."""
        self._service_manager = service_manager


class ProjectIndexingHealthCollector(HealthCollector):
    """
    Health collector for MEM-007 Project Indexing Service.
    
    Monitors the health and performance of the project indexing system
    including connectivity to mem0AI, cache performance, and indexing statistics.
    """
    
    def __init__(self, timeout_seconds: float = 3.0):
        """
        Initialize project indexing health collector.
        
        Args:
            timeout_seconds: Timeout for health collection
        """
        super().__init__("project_indexing", timeout_seconds)
    
    async def collect_health(self) -> List[ServiceHealthReport]:
        """
        Collect health reports from project indexing services.
        
        Returns:
            List of ServiceHealthReport objects for indexing services
        """
        reports = []
        
        # Project Indexer health
        reports.append(await self._check_project_indexer())
        
        # Project Memory Manager health
        reports.append(await self._check_project_memory_manager())
        
        # mem0AI connectivity health
        reports.append(await self._check_mem0ai_connectivity())
        
        return reports
    
    async def _check_project_indexer(self) -> ServiceHealthReport:
        """Check project indexer service health."""
        try:
            from ..services.project_indexer import create_project_indexer
            
            start_time = asyncio.get_event_loop().time()
            
            # Create and test indexer
            indexer = create_project_indexer()
            
            # Test initialization
            init_success = await indexer.initialize()
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if init_success:
                # Get statistics
                stats = indexer.get_indexer_statistics()
                
                # Determine health status based on statistics
                cache_hit_rate = stats.get('cache_hit_rate', 0)
                success_rate = stats.get('success_rate', 0)
                
                if cache_hit_rate >= 70 and success_rate >= 90:
                    status = HealthStatus.HEALTHY
                    message = f"Indexer operational (cache: {cache_hit_rate:.1f}%, success: {success_rate:.1f}%)"
                elif cache_hit_rate >= 50 and success_rate >= 70:
                    status = HealthStatus.DEGRADED
                    message = f"Indexer degraded (cache: {cache_hit_rate:.1f}%, success: {success_rate:.1f}%)"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = f"Indexer poor performance (cache: {cache_hit_rate:.1f}%, success: {success_rate:.1f}%)"
                
                await indexer.cleanup()
                
                return create_service_health_report(
                    name="project_indexer",
                    status=status,
                    message=message,
                    response_time_ms=response_time,
                    metrics={
                        "projects_indexed": stats.get('projects_indexed', 0),
                        "cache_hit_rate": cache_hit_rate,
                        "success_rate": success_rate,
                        "memory_connected": stats.get('memory_connected', False)
                    }
                )
            else:
                return create_service_health_report(
                    name="project_indexer",
                    status=HealthStatus.UNHEALTHY,
                    message="Failed to initialize project indexer",
                    response_time_ms=response_time
                )
                
        except Exception as e:
            return create_service_health_report(
                name="project_indexer",
                status=HealthStatus.ERROR,
                message=f"Project indexer error: {str(e)}",
                error=str(e)
            )
    
    async def _check_project_memory_manager(self) -> ServiceHealthReport:
        """Check project memory manager health."""
        try:
            from ..services.project_memory_manager import create_project_memory_manager
            
            start_time = asyncio.get_event_loop().time()
            
            # Create and test memory manager
            manager = create_project_memory_manager()
            
            # Test initialization
            init_success = await manager.initialize()
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if init_success:
                # Get performance statistics
                stats = manager.get_performance_stats()
                
                # Determine health based on performance - optimized thresholds
                avg_response = stats.get('avg_response_time_ms', 0)
                cache_hit_rate = stats.get('cache_hit_rate', 0)
                
                if avg_response <= 50 and cache_hit_rate >= 70:
                    status = HealthStatus.HEALTHY
                    message = f"Memory manager optimal ({avg_response:.0f}ms avg, {cache_hit_rate:.1f}% cache)"
                elif avg_response <= 200 and cache_hit_rate >= 40:
                    status = HealthStatus.DEGRADED
                    message = f"Memory manager acceptable ({avg_response:.0f}ms avg, {cache_hit_rate:.1f}% cache)"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = f"Memory manager slow ({avg_response:.0f}ms avg, {cache_hit_rate:.1f}% cache)"
                
                await manager.cleanup()
                
                return create_service_health_report(
                    name="project_memory_manager",
                    status=status,
                    message=message,
                    response_time_ms=response_time,
                    metrics={
                        "avg_response_time_ms": avg_response,
                        "cache_hit_rate": cache_hit_rate,
                        "queries_total": stats.get('queries_total', 0),
                        "memory_connected": stats.get('memory_connected', False)
                    }
                )
            else:
                return create_service_health_report(
                    name="project_memory_manager",
                    status=HealthStatus.UNHEALTHY,
                    message="Failed to initialize project memory manager",
                    response_time_ms=response_time
                )
                
        except Exception as e:
            return create_service_health_report(
                name="project_memory_manager",
                status=HealthStatus.ERROR,
                message=f"Project memory manager error: {str(e)}",
                error=str(e)
            )
    
    async def _check_mem0ai_connectivity(self) -> ServiceHealthReport:
        """Check mem0AI service connectivity."""
        try:
            from ..integrations.mem0ai_integration import create_mem0ai_integration
            
            start_time = asyncio.get_event_loop().time()
            
            async with create_mem0ai_integration() as mem0ai:
                if mem0ai.is_connected():
                    # Test basic operation
                    service_info = await mem0ai.get_service_info()
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    # Check response time for health assessment
                    if response_time <= 200:
                        status = HealthStatus.HEALTHY
                        message = f"mem0AI connected and responsive ({response_time:.0f}ms)"
                    elif response_time <= 1000:
                        status = HealthStatus.DEGRADED
                        message = f"mem0AI connected but slow ({response_time:.0f}ms)"
                    else:
                        status = HealthStatus.UNHEALTHY
                        message = f"mem0AI connected but very slow ({response_time:.0f}ms)"
                    
                    return create_service_health_report(
                        name="mem0ai_service",
                        status=status,
                        message=message,
                        response_time_ms=response_time,
                        metrics={
                            "endpoint": "http://localhost:8002",
                            "service_info": service_info,
                            "connected": True
                        }
                    )
                else:
                    return create_service_health_report(
                        name="mem0ai_service",
                        status=HealthStatus.DOWN,
                        message="mem0AI service not reachable on port 8002",
                        metrics={
                            "endpoint": "http://localhost:8002",
                            "connected": False
                        }
                    )
                    
        except Exception as e:
            return create_service_health_report(
                name="mem0ai_service",
                status=HealthStatus.ERROR,
                message=f"mem0AI connectivity error: {str(e)}",
                error=str(e),
                metrics={
                    "endpoint": "http://localhost:8002",
                    "connected": False
                }
            )
    
    def get_subsystem_name(self) -> str:
        """Get the subsystem name for this collector."""
        return "Project Indexing (MEM-007)"
    
    def get_service_names(self) -> List[str]:
        """Get the list of service names this collector monitors."""
        return [
            "project_indexer",
            "project_memory_manager", 
            "mem0ai_service"
        ]