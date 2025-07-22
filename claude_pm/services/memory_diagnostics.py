#!/usr/bin/env python3
"""
Memory Diagnostics Service - Claude PM Framework

Provides memory profiling, monitoring, and emergency cleanup capabilities
to address critical memory exhaustion issues in framework operations.

This module implements:
- Real-time memory profiling and tracking
- Memory pressure detection with configurable thresholds
- Emergency memory cleanup procedures
- Integration with HealthMonitor for holistic system monitoring
- CLI command support for manual interventions

Created as part of ISS-0004 critical P0 memory optimization initiative.
"""

import asyncio
import gc
import json
import logging
import os
import psutil
import sys
import time
import tracemalloc
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

from ..core.base_service import BaseService


class MemoryDiagnosticsService(BaseService):
    """
    Memory diagnostics and profiling service for Claude PM Framework.
    
    Provides real-time memory monitoring, profiling, and emergency cleanup
    to prevent Node.js heap exhaustion and performance degradation.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize memory diagnostics service."""
        super().__init__("memory_diagnostics", config)
        
        # Configuration
        self.enable_profiling = self.get_config("enable_profiling", True)
        self.profile_interval = self.get_config("profile_interval", 60)  # seconds
        self.memory_threshold_mb = self.get_config("memory_threshold_mb", 500)  # Python process
        self.cache_pressure_threshold = self.get_config("cache_pressure_threshold", 0.8)  # 80%
        self.subprocess_threshold_mb = self.get_config("subprocess_threshold_mb", 1000)
        self.enable_auto_cleanup = self.get_config("enable_auto_cleanup", True)
        
        # State tracking
        self._profiling_enabled = False
        self._snapshot_baseline = None
        self._memory_history: List[Dict] = []
        self._cache_stats: Dict[str, Dict] = {}
        self._subprocess_memory: Dict[int, float] = {}
        self._memory_leaks: List[Dict] = []
        self._last_cleanup_time = 0
        self._cleanup_cooldown = 300  # 5 minutes between cleanups
        
        # Background tasks
        self._profile_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Service references (lazy loaded)
        self._shared_cache = None
        self._health_monitor = None
        
        self.logger.info(f"MemoryDiagnosticsService initialized with threshold={self.memory_threshold_mb}MB")
    
    async def _initialize(self) -> None:
        """Initialize the memory diagnostics service."""
        self.logger.info("Initializing Memory Diagnostics Service...")
        
        # Start memory profiling if enabled
        if self.enable_profiling:
            self._start_profiling()
        
        # Start background monitoring
        self._monitor_task = asyncio.create_task(self._memory_monitoring_task())
        self._profile_task = asyncio.create_task(self._profiling_task())
        
        # Register with memory pressure coordinator
        try:
            from .memory_pressure_coordinator import register_service_cleanup
            await register_service_cleanup("memory_diagnostics", self.perform_emergency_cleanup)
            self.logger.info("Registered with memory pressure coordinator")
        except Exception as e:
            self.logger.warning(f"Failed to register with memory pressure coordinator: {e}")
        
        self.logger.info("Memory Diagnostics Service initialized successfully")
    
    async def _cleanup(self) -> None:
        """Cleanup memory diagnostics service."""
        self.logger.info("Cleaning up Memory Diagnostics Service...")
        
        # Stop profiling
        if self._profiling_enabled:
            self._stop_profiling()
        
        # Cancel background tasks
        for task in [self._monitor_task, self._profile_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.logger.info("Memory Diagnostics Service cleanup completed")
    
    async def _health_check(self) -> Dict[str, bool]:
        """Perform memory diagnostics health checks."""
        checks = {}
        
        try:
            # Check memory profiling
            checks["profiling_enabled"] = self._profiling_enabled
            
            # Check memory usage
            current_mb = self._get_process_memory_mb()
            checks["memory_below_threshold"] = current_mb < self.memory_threshold_mb
            
            # Check monitoring task
            checks["monitoring_active"] = (
                self._monitor_task is not None and not self._monitor_task.done()
            )
            
            # Check for memory pressure
            checks["no_memory_pressure"] = not self._detect_memory_pressure()
            
        except Exception as e:
            self.logger.error(f"Memory diagnostics health check failed: {e}")
            checks["health_check_error"] = False
        
        return checks
    
    def _start_profiling(self) -> None:
        """Start memory profiling."""
        try:
            if not self._profiling_enabled:
                tracemalloc.start()
                self._snapshot_baseline = tracemalloc.take_snapshot()
                self._profiling_enabled = True
                self.logger.info("Memory profiling started")
        except Exception as e:
            self.logger.error(f"Failed to start memory profiling: {e}")
    
    def _stop_profiling(self) -> None:
        """Stop memory profiling."""
        try:
            if self._profiling_enabled:
                tracemalloc.stop()
                self._profiling_enabled = False
                self.logger.info("Memory profiling stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop memory profiling: {e}")
    
    def _get_process_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _get_system_memory_info(self) -> Dict[str, float]:
        """Get system-wide memory information."""
        try:
            mem = psutil.virtual_memory()
            return {
                "total_mb": mem.total / (1024 * 1024),
                "available_mb": mem.available / (1024 * 1024),
                "used_mb": mem.used / (1024 * 1024),
                "percent": mem.percent,
                "swap_used_mb": psutil.swap_memory().used / (1024 * 1024)
            }
        except Exception:
            return {}
    
    def _detect_memory_pressure(self) -> bool:
        """Detect if system is under memory pressure."""
        try:
            # Check process memory
            process_mb = self._get_process_memory_mb()
            if process_mb > self.memory_threshold_mb:
                return True
            
            # Check system memory
            sys_mem = self._get_system_memory_info()
            if sys_mem.get("percent", 0) > 90:
                return True
            
            # Check cache pressure
            if self._shared_cache:
                cache_metrics = self._shared_cache.get_metrics()
                memory_usage_percent = cache_metrics.get("memory_usage_percent", 0)
                if memory_usage_percent > (self.cache_pressure_threshold * 100):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to detect memory pressure: {e}")
            return False
    
    async def get_memory_profile(self) -> Dict[str, Any]:
        """Get comprehensive memory profile."""
        profile = {
            "timestamp": datetime.now().isoformat(),
            "process": {
                "memory_mb": self._get_process_memory_mb(),
                "threshold_mb": self.memory_threshold_mb,
                "python_version": sys.version,
                "gc_stats": gc.get_stats()
            },
            "system": self._get_system_memory_info(),
            "memory_pressure": self._detect_memory_pressure()
        }
        
        # Add profiling data if available
        if self._profiling_enabled and self._snapshot_baseline:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.compare_to(self._snapshot_baseline, 'lineno')
            
            profile["top_allocations"] = [
                {
                    "file": stat.traceback.format()[0] if stat.traceback else "unknown",
                    "size_diff_mb": stat.size_diff / (1024 * 1024),
                    "count_diff": stat.count_diff
                }
                for stat in sorted(top_stats, key=lambda x: x.size_diff, reverse=True)[:10]
            ]
        
        # Add cache statistics
        if self._shared_cache:
            try:
                cache_info = await self._get_cache_memory_info()
                profile["cache"] = cache_info
            except Exception as e:
                self.logger.warning(f"Failed to get cache info: {e}")
                profile["cache"] = {"error": str(e)}
        
        # Add subprocess memory
        profile["subprocesses"] = await self._get_subprocess_memory()
        
        # Add memory history summary
        if self._memory_history:
            recent_history = self._memory_history[-10:]  # Last 10 entries
            profile["history"] = {
                "entries": len(self._memory_history),
                "recent": recent_history,
                "avg_memory_mb": sum(h["process_mb"] for h in recent_history) / len(recent_history)
            }
        
        # Add detected leaks
        if self._memory_leaks:
            profile["potential_leaks"] = self._memory_leaks[-5:]  # Last 5 detected
        
        return profile
    
    async def _get_cache_memory_info(self) -> Dict[str, Any]:
        """Get memory information from SharedPromptCache."""
        if not self._shared_cache:
            try:
                from .shared_prompt_cache import SharedPromptCache
                self._shared_cache = SharedPromptCache.get_instance()
            except Exception:
                return {"status": "unavailable"}
        
        cache_metrics = self._shared_cache.get_metrics()
        cache_info = self._shared_cache.get_cache_info()
        
        return {
            "size_mb": cache_metrics.get("size_mb", 0),
            "entry_count": cache_metrics.get("entry_count", 0),
            "hit_rate": cache_metrics.get("hit_rate", 0),
            "memory_usage_percent": cache_metrics.get("memory_usage_percent", 0),
            "max_memory_mb": cache_metrics.get("max_memory_mb", 100),
            "largest_entries": sorted(
                cache_info.get("entries", []), 
                key=lambda x: x.get("size_bytes", 0), 
                reverse=True
            )[:5]
        }
    
    async def _get_subprocess_memory(self) -> Dict[str, Any]:
        """Get memory usage of subprocesses."""
        subprocess_info = {}
        
        try:
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            
            total_subprocess_mb = 0
            for child in children:
                try:
                    child_mb = child.memory_info().rss / (1024 * 1024)
                    subprocess_info[str(child.pid)] = {
                        "pid": child.pid,
                        "name": child.name(),
                        "memory_mb": child_mb,
                        "status": child.status()
                    }
                    total_subprocess_mb += child_mb
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            subprocess_info["total_mb"] = total_subprocess_mb
            subprocess_info["count"] = len(children)
            subprocess_info["threshold_mb"] = self.subprocess_threshold_mb
            subprocess_info["exceeds_threshold"] = total_subprocess_mb > self.subprocess_threshold_mb
            
        except Exception as e:
            self.logger.error(f"Failed to get subprocess memory: {e}")
            subprocess_info["error"] = str(e)
        
        return subprocess_info
    
    async def perform_emergency_cleanup(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform emergency memory cleanup.
        
        Args:
            force: Force cleanup even if cooldown period hasn't elapsed
            
        Returns:
            Cleanup results and statistics
        """
        # Check cooldown unless forced
        if not force:
            time_since_last = time.time() - self._last_cleanup_time
            if time_since_last < self._cleanup_cooldown:
                remaining = self._cleanup_cooldown - time_since_last
                return {
                    "success": False,
                    "reason": f"Cleanup on cooldown, {remaining:.0f}s remaining"
                }
        
        self.logger.warning("Performing emergency memory cleanup...")
        
        cleanup_stats = {
            "timestamp": datetime.now().isoformat(),
            "before": {
                "process_mb": self._get_process_memory_mb(),
                "system": self._get_system_memory_info()
            },
            "actions": []
        }
        
        # 1. Clear SharedPromptCache
        if self._shared_cache:
            try:
                cache_metrics_before = self._shared_cache.get_metrics()
                self._shared_cache.clear()
                cache_metrics_after = self._shared_cache.get_metrics()
                
                cleanup_stats["actions"].append({
                    "action": "clear_cache",
                    "freed_mb": cache_metrics_before["size_mb"] - cache_metrics_after["size_mb"],
                    "entries_cleared": cache_metrics_before["entry_count"]
                })
            except Exception as e:
                self.logger.error(f"Failed to clear cache: {e}")
                cleanup_stats["actions"].append({
                    "action": "clear_cache",
                    "error": str(e)
                })
        
        # 2. Force garbage collection
        try:
            gc_stats_before = gc.get_stats()
            collected = gc.collect(2)  # Full collection
            gc_stats_after = gc.get_stats()
            
            cleanup_stats["actions"].append({
                "action": "garbage_collection",
                "objects_collected": collected,
                "generation_stats": gc_stats_after
            })
        except Exception as e:
            self.logger.error(f"Failed to run garbage collection: {e}")
            cleanup_stats["actions"].append({
                "action": "garbage_collection",
                "error": str(e)
            })
        
        # 3. Clear internal diagnostics data
        try:
            history_size = len(self._memory_history)
            self._memory_history = self._memory_history[-100:]  # Keep last 100
            self._memory_leaks = self._memory_leaks[-10:]  # Keep last 10
            
            cleanup_stats["actions"].append({
                "action": "clear_diagnostics",
                "history_entries_removed": history_size - len(self._memory_history)
            })
        except Exception as e:
            self.logger.error(f"Failed to clear diagnostics: {e}")
        
        # 4. Terminate zombie subprocesses
        try:
            terminated = await self._cleanup_zombie_processes()
            if terminated:
                cleanup_stats["actions"].append({
                    "action": "terminate_zombies",
                    "processes_terminated": len(terminated),
                    "pids": terminated
                })
        except Exception as e:
            self.logger.error(f"Failed to cleanup zombie processes: {e}")
        
        # Record cleanup results
        cleanup_stats["after"] = {
            "process_mb": self._get_process_memory_mb(),
            "system": self._get_system_memory_info()
        }
        
        cleanup_stats["freed_mb"] = (
            cleanup_stats["before"]["process_mb"] - cleanup_stats["after"]["process_mb"]
        )
        cleanup_stats["success"] = True
        
        self._last_cleanup_time = time.time()
        
        self.logger.info(f"Emergency cleanup completed, freed {cleanup_stats['freed_mb']:.2f}MB")
        
        return cleanup_stats
    
    async def _cleanup_zombie_processes(self) -> List[int]:
        """Cleanup zombie or stuck subprocesses."""
        terminated = []
        
        try:
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            
            for child in children:
                try:
                    # Check if process is zombie or consuming too much memory
                    if (child.status() == psutil.STATUS_ZOMBIE or 
                        child.memory_info().rss / (1024 * 1024) > self.subprocess_threshold_mb):
                        
                        child.terminate()
                        terminated.append(child.pid)
                        
                        # Give it time to terminate gracefully
                        try:
                            child.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            child.kill()  # Force kill if needed
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup zombie processes: {e}")
        
        return terminated
    
    async def _memory_monitoring_task(self) -> None:
        """Background task for continuous memory monitoring."""
        while not self._stop_event.is_set():
            try:
                # Collect memory snapshot
                snapshot = {
                    "timestamp": time.time(),
                    "process_mb": self._get_process_memory_mb(),
                    "system_percent": psutil.virtual_memory().percent
                }
                
                self._memory_history.append(snapshot)
                
                # Keep only recent history (last hour)
                cutoff_time = time.time() - 3600
                self._memory_history = [
                    h for h in self._memory_history if h["timestamp"] > cutoff_time
                ]
                
                # Check for memory pressure
                if self._detect_memory_pressure() and self.enable_auto_cleanup:
                    self.logger.warning("Memory pressure detected, initiating coordinated cleanup...")
                    
                    # Use memory pressure coordinator for system-wide cleanup
                    try:
                        from .memory_pressure_coordinator import get_memory_pressure_coordinator
                        coordinator = get_memory_pressure_coordinator()
                        await coordinator.handle_memory_pressure()
                    except Exception as e:
                        self.logger.warning(f"Coordinator cleanup failed, falling back to local cleanup: {e}")
                        await self.perform_emergency_cleanup()
                
                # Update metrics
                self.update_metrics(
                    memory_usage_mb=snapshot["process_mb"],
                    memory_pressure=self._detect_memory_pressure(),
                    history_size=len(self._memory_history)
                )
                
                await asyncio.sleep(self.profile_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(self.profile_interval)
    
    async def _profiling_task(self) -> None:
        """Background task for memory profiling analysis."""
        while not self._stop_event.is_set():
            try:
                if self._profiling_enabled:
                    # Analyze memory allocations
                    await self._analyze_memory_allocations()
                
                await asyncio.sleep(self.profile_interval * 5)  # Less frequent than monitoring
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Profiling task error: {e}")
                await asyncio.sleep(self.profile_interval * 5)
    
    async def _analyze_memory_allocations(self) -> None:
        """Analyze memory allocations for potential leaks."""
        if not self._profiling_enabled or not self._snapshot_baseline:
            return
        
        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.compare_to(self._snapshot_baseline, 'lineno')
            
            # Look for significant growth
            for stat in sorted(top_stats, key=lambda x: x.size_diff, reverse=True)[:5]:
                if stat.size_diff > 10 * 1024 * 1024:  # 10MB growth
                    leak_info = {
                        "timestamp": datetime.now().isoformat(),
                        "location": stat.traceback.format()[0] if stat.traceback else "unknown",
                        "growth_mb": stat.size_diff / (1024 * 1024),
                        "count_diff": stat.count_diff
                    }
                    self._memory_leaks.append(leak_info)
                    self.logger.warning(f"Potential memory leak detected: {leak_info}")
            
            # Keep only recent leak detections
            self._memory_leaks = self._memory_leaks[-20:]
            
        except Exception as e:
            self.logger.error(f"Failed to analyze memory allocations: {e}")
    
    async def get_memory_diagnostics(self) -> Dict[str, Any]:
        """Get complete memory diagnostics report."""
        return {
            "profile": await self.get_memory_profile(),
            "pressure_detected": self._detect_memory_pressure(),
            "auto_cleanup_enabled": self.enable_auto_cleanup,
            "last_cleanup": datetime.fromtimestamp(self._last_cleanup_time).isoformat() if self._last_cleanup_time else None,
            "thresholds": {
                "process_mb": self.memory_threshold_mb,
                "cache_pressure": self.cache_pressure_threshold,
                "subprocess_mb": self.subprocess_threshold_mb
            },
            "profiling_enabled": self._profiling_enabled
        }
    
    def set_memory_threshold(self, threshold_mb: float) -> None:
        """Update memory threshold for pressure detection."""
        self.memory_threshold_mb = threshold_mb
        self.logger.info(f"Memory threshold updated to {threshold_mb}MB")
    
    def enable_auto_cleanup(self, enabled: bool) -> None:
        """Enable or disable automatic memory cleanup."""
        self.enable_auto_cleanup = enabled
        self.logger.info(f"Auto cleanup {'enabled' if enabled else 'disabled'}")


# Singleton instance management
_memory_diagnostics_instance: Optional[MemoryDiagnosticsService] = None


def get_memory_diagnostics() -> MemoryDiagnosticsService:
    """Get or create the memory diagnostics service instance."""
    global _memory_diagnostics_instance
    if _memory_diagnostics_instance is None:
        _memory_diagnostics_instance = MemoryDiagnosticsService()
    return _memory_diagnostics_instance


# Export for backward compatibility
MemoryDiagnostics = MemoryDiagnosticsService