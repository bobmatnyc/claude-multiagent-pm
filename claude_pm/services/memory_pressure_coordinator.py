#!/usr/bin/env python3
"""
Memory Pressure Coordinator - Claude PM Framework

Coordinates memory pressure response across all singleton services.
Provides centralized memory cleanup and pressure handling.

Created as part of ISS-0004 critical P0 memory optimization initiative.
"""

import asyncio
import gc
import logging
import psutil
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryPressureCoordinator:
    """
    Singleton coordinator for memory pressure response across all services.
    
    Coordinates cleanup actions when memory pressure is detected.
    """
    
    _instance: Optional['MemoryPressureCoordinator'] = None
    
    def __init__(self):
        """Initialize the memory pressure coordinator."""
        if MemoryPressureCoordinator._instance is not None:
            raise RuntimeError("MemoryPressureCoordinator is a singleton. Use get_instance() instead.")
        
        # Configuration
        self.warning_threshold_percent = 70  # Warning at 70% memory usage
        self.critical_threshold_percent = 85  # Critical at 85% memory usage
        self.cleanup_cooldown_seconds = 60  # Minimum time between cleanups
        
        # State
        self._last_cleanup_time = 0
        self._cleanup_handlers: Dict[str, Callable] = {}
        self._is_cleaning = False
        
        logger.info("MemoryPressureCoordinator initialized")
    
    @classmethod
    def get_instance(cls) -> 'MemoryPressureCoordinator':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_cleanup_handler(self, service_name: str, handler: Callable) -> None:
        """
        Register a cleanup handler for a service.
        
        Args:
            service_name: Name of the service
            handler: Async function that performs cleanup and returns stats dict
        """
        self._cleanup_handlers[service_name] = handler
        logger.info(f"Registered cleanup handler for {service_name}")
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory status."""
        try:
            process = psutil.Process()
            system_memory = psutil.virtual_memory()
            
            process_memory_mb = process.memory_info().rss / (1024 * 1024)
            system_used_percent = system_memory.percent
            
            # Determine pressure level
            if system_used_percent >= self.critical_threshold_percent:
                pressure_level = "critical"
            elif system_used_percent >= self.warning_threshold_percent:
                pressure_level = "warning"
            else:
                pressure_level = "normal"
            
            return {
                "timestamp": datetime.now().isoformat(),
                "process_memory_mb": process_memory_mb,
                "system_memory_percent": system_used_percent,
                "system_available_mb": system_memory.available / (1024 * 1024),
                "pressure_level": pressure_level,
                "thresholds": {
                    "warning": self.warning_threshold_percent,
                    "critical": self.critical_threshold_percent
                }
            }
        except Exception as e:
            logger.error(f"Failed to get memory status: {e}")
            return {
                "error": str(e),
                "pressure_level": "unknown"
            }
    
    async def handle_memory_pressure(self, force: bool = False) -> Dict[str, Any]:
        """
        Handle memory pressure by coordinating cleanup across all services.
        
        Args:
            force: Force cleanup even if cooldown hasn't elapsed
            
        Returns:
            Cleanup results from all services
        """
        # Check if already cleaning
        if self._is_cleaning:
            return {
                "success": False,
                "reason": "Cleanup already in progress"
            }
        
        # Check cooldown
        if not force:
            time_since_last = time.time() - self._last_cleanup_time
            if time_since_last < self.cleanup_cooldown_seconds:
                return {
                    "success": False,
                    "reason": f"Cleanup on cooldown ({self.cleanup_cooldown_seconds - time_since_last:.0f}s remaining)"
                }
        
        self._is_cleaning = True
        memory_before = self.get_memory_status()
        
        logger.warning(f"Initiating memory pressure cleanup (level: {memory_before['pressure_level']})")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "memory_before": memory_before,
            "service_cleanups": {},
            "total_freed_mb": 0
        }
        
        try:
            # Phase 1: Service-specific cleanups
            for service_name, handler in self._cleanup_handlers.items():
                try:
                    severity = "critical" if memory_before["pressure_level"] == "critical" else "warning"
                    service_result = await handler(severity)
                    results["service_cleanups"][service_name] = service_result
                    
                    # Track freed memory if reported
                    if isinstance(service_result, dict) and "memory_freed_mb" in service_result:
                        results["total_freed_mb"] += service_result["memory_freed_mb"]
                        
                except Exception as e:
                    logger.error(f"Cleanup failed for {service_name}: {e}")
                    results["service_cleanups"][service_name] = {"error": str(e)}
            
            # Phase 2: Force garbage collection
            gc_before = gc.get_stats()
            collected = gc.collect(2)  # Full collection
            results["gc_objects_collected"] = collected
            
            # Phase 3: Clear any large temporary objects
            # This is where we could add more aggressive cleanup if needed
            
            # Get memory status after cleanup
            memory_after = self.get_memory_status()
            results["memory_after"] = memory_after
            
            # Calculate improvement
            if "process_memory_mb" in memory_before and "process_memory_mb" in memory_after:
                memory_freed = memory_before["process_memory_mb"] - memory_after["process_memory_mb"]
                results["process_memory_freed_mb"] = memory_freed
                
                logger.info(f"Memory cleanup completed. Freed {memory_freed:.1f}MB process memory, "
                          f"{results['total_freed_mb']:.1f}MB from services")
            
            self._last_cleanup_time = time.time()
            results["success"] = True
            
        except Exception as e:
            logger.error(f"Memory pressure cleanup failed: {e}")
            results["success"] = False
            results["error"] = str(e)
        
        finally:
            self._is_cleaning = False
        
        return results
    
    async def monitor_and_respond(self) -> None:
        """
        Monitor memory and automatically respond to pressure.
        
        This should be called periodically by a monitoring service.
        """
        status = self.get_memory_status()
        
        if status["pressure_level"] in ["warning", "critical"]:
            logger.warning(f"Memory pressure detected: {status['pressure_level']} "
                         f"({status['system_memory_percent']:.1f}% used)")
            
            # Trigger cleanup
            await self.handle_memory_pressure()


# Singleton instance getter
def get_memory_pressure_coordinator() -> MemoryPressureCoordinator:
    """Get the singleton memory pressure coordinator instance."""
    return MemoryPressureCoordinator.get_instance()


# Integration helper for services
async def register_service_cleanup(service_name: str, cleanup_handler: Callable) -> None:
    """
    Register a service's cleanup handler with the coordinator.
    
    Args:
        service_name: Name of the service
        cleanup_handler: Async function that performs cleanup
    """
    coordinator = get_memory_pressure_coordinator()
    coordinator.register_cleanup_handler(service_name, cleanup_handler)