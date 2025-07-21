#!/usr/bin/env python3
"""
Claude PM Framework - Python Memory Monitor
Replaces the JavaScript memory monitor with a pure Python implementation.
Enhanced with subprocess-specific memory monitoring for Task Tool operations.
"""

import asyncio
import os
import psutil
import time
import json
import logging
from typing import Dict, Optional, Set, Tuple, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MemoryThresholds:
    """Memory thresholds for subprocess monitoring."""
    warning_mb: int = 1024  # 1GB warning
    critical_mb: int = 2048  # 2GB critical
    max_mb: int = 4096  # 4GB hard limit


@dataclass
class SubprocessMemoryStats:
    """Memory statistics for a subprocess."""
    subprocess_id: str
    start_mb: float
    current_mb: float
    peak_mb: float
    duration_seconds: float
    warnings: List[str] = field(default_factory=list)
    aborted: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SubprocessMemoryMonitor:
    """Subprocess-specific memory monitoring for Task Tool operations."""
    
    def __init__(self, thresholds: Optional[MemoryThresholds] = None, log_dir: Optional[Path] = None):
        self.thresholds = thresholds or MemoryThresholds()
        self.subprocess_memory: Dict[str, SubprocessMemoryStats] = {}
        self.active_monitors: Dict[str, asyncio.Task] = {}
        
        # Set up logging
        self.log_dir = log_dir or Path('.claude-pm/logs/memory')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_log = self.log_dir / 'memory-alerts.log'
        
        # Track start time
        self.start_time = time.time()
        
    def start_monitoring(self, subprocess_id: str, process_info: Optional[Dict] = None) -> None:
        """Start monitoring memory for a subprocess."""
        if subprocess_id in self.subprocess_memory:
            logger.warning(f"Already monitoring subprocess {subprocess_id}")
            return
            
        # Get initial memory usage
        initial_memory = self._get_current_memory_mb()
        
        # Initialize stats
        self.subprocess_memory[subprocess_id] = SubprocessMemoryStats(
            subprocess_id=subprocess_id,
            start_mb=initial_memory,
            current_mb=initial_memory,
            peak_mb=initial_memory,
            duration_seconds=0
        )
        
        # Start async monitoring task
        monitor_task = asyncio.create_task(self._monitor_subprocess(subprocess_id))
        self.active_monitors[subprocess_id] = monitor_task
        
        logger.info(f"Started monitoring subprocess {subprocess_id}, initial memory: {initial_memory:.1f}MB")
        
    async def _monitor_subprocess(self, subprocess_id: str):
        """Async monitoring loop for a specific subprocess."""
        start_time = time.time()
        
        while subprocess_id in self.subprocess_memory and not self.subprocess_memory[subprocess_id].aborted:
            try:
                # Update memory stats
                current_memory = self._get_current_memory_mb()
                stats = self.subprocess_memory[subprocess_id]
                
                stats.current_mb = current_memory
                stats.peak_mb = max(stats.peak_mb, current_memory)
                stats.duration_seconds = time.time() - start_time
                
                # Check thresholds
                if current_memory > self.thresholds.max_mb:
                    warning = f"CRITICAL: Memory exceeded {self.thresholds.max_mb}MB limit at {current_memory:.1f}MB"
                    stats.warnings.append(warning)
                    stats.aborted = True
                    logger.error(f"Subprocess {subprocess_id}: {warning}")
                    self._log_alert('CRITICAL', subprocess_id, warning)
                    break
                elif current_memory > self.thresholds.critical_mb:
                    warning = f"CRITICAL: Memory exceeded {self.thresholds.critical_mb}MB at {current_memory:.1f}MB"
                    if warning not in stats.warnings:
                        stats.warnings.append(warning)
                        logger.warning(f"Subprocess {subprocess_id}: {warning}")
                        self._log_alert('CRITICAL', subprocess_id, warning)
                elif current_memory > self.thresholds.warning_mb:
                    warning = f"WARNING: Memory exceeded {self.thresholds.warning_mb}MB at {current_memory:.1f}MB"
                    if warning not in stats.warnings:
                        stats.warnings.append(warning)
                        logger.warning(f"Subprocess {subprocess_id}: {warning}")
                        self._log_alert('WARNING', subprocess_id, warning)
                
                # Wait before next check
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring subprocess {subprocess_id}: {e}")
                break
                
    def check_memory(self, subprocess_id: str) -> Tuple[float, str]:
        """Check current memory usage and return (usage_mb, status)."""
        if subprocess_id not in self.subprocess_memory:
            return 0.0, "NOT_MONITORED"
            
        stats = self.subprocess_memory[subprocess_id]
        current_mb = stats.current_mb
        
        if stats.aborted:
            status = "ABORTED"
        elif current_mb > self.thresholds.critical_mb:
            status = "CRITICAL"
        elif current_mb > self.thresholds.warning_mb:
            status = "WARNING"
        else:
            status = "OK"
            
        return current_mb, status
        
    def stop_monitoring(self, subprocess_id: str) -> Dict:
        """Stop monitoring and return final stats."""
        if subprocess_id not in self.subprocess_memory:
            return {"error": f"Subprocess {subprocess_id} not being monitored"}
            
        # Cancel monitoring task
        if subprocess_id in self.active_monitors:
            self.active_monitors[subprocess_id].cancel()
            del self.active_monitors[subprocess_id]
            
        # Get final stats
        stats = self.subprocess_memory[subprocess_id]
        final_stats = {
            "subprocess_id": stats.subprocess_id,
            "memory_stats": {
                "start_mb": round(stats.start_mb, 1),
                "peak_mb": round(stats.peak_mb, 1),
                "end_mb": round(stats.current_mb, 1),
                "duration_seconds": round(stats.duration_seconds, 1),
                "warnings": stats.warnings,
                "aborted": stats.aborted
            }
        }
        
        # Log final stats
        self._log_subprocess_stats(final_stats)
        
        # Remove from tracking
        del self.subprocess_memory[subprocess_id]
        
        logger.info(f"Stopped monitoring subprocess {subprocess_id}, peak memory: {stats.peak_mb:.1f}MB")
        return final_stats
        
    def get_system_memory(self) -> Dict:
        """Get overall system memory stats."""
        vm = psutil.virtual_memory()
        
        return {
            "total_mb": round(vm.total / 1024 / 1024, 1),
            "available_mb": round(vm.available / 1024 / 1024, 1),
            "used_mb": round(vm.used / 1024 / 1024, 1),
            "percent": round(vm.percent, 1),
            "free_mb": round(vm.free / 1024 / 1024, 1)
        }
        
    def should_abort(self, subprocess_id: str) -> bool:
        """Check if subprocess should be aborted due to memory."""
        if subprocess_id not in self.subprocess_memory:
            return False
            
        return self.subprocess_memory[subprocess_id].aborted
        
    def can_create_subprocess(self) -> Tuple[bool, str]:
        """Check if system has enough memory to create a new subprocess."""
        system_memory = self.get_system_memory()
        available_mb = system_memory['available_mb']
        
        if available_mb < 1024:  # Less than 1GB available
            return False, f"Insufficient memory: only {available_mb:.1f}MB available (need at least 1GB)"
        elif available_mb < 2048:  # Less than 2GB available
            return True, f"WARNING: Low memory - only {available_mb:.1f}MB available"
        else:
            return True, "OK"
            
    def get_all_subprocess_stats(self) -> Dict[str, Dict]:
        """Get memory stats for all active subprocesses."""
        stats = {}
        for subprocess_id, subprocess_stats in self.subprocess_memory.items():
            stats[subprocess_id] = {
                "current_mb": round(subprocess_stats.current_mb, 1),
                "peak_mb": round(subprocess_stats.peak_mb, 1),
                "duration_seconds": round(subprocess_stats.duration_seconds, 1),
                "status": self.check_memory(subprocess_id)[1],
                "warnings_count": len(subprocess_stats.warnings)
            }
        return stats
        
    def _get_current_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
        
    def _log_alert(self, level: str, subprocess_id: str, message: str):
        """Log memory alert to file."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "subprocess_id": subprocess_id,
            "message": message,
            "system_memory": self.get_system_memory()
        }
        
        with open(self.alerts_log, 'a') as f:
            f.write(json.dumps(alert) + '\n')
            
    def _log_subprocess_stats(self, stats: Dict):
        """Log subprocess final stats."""
        stats_file = self.log_dir / 'subprocess-stats.jsonl'
        stats['timestamp'] = datetime.now().isoformat()
        
        with open(stats_file, 'a') as f:
            f.write(json.dumps(stats) + '\n')


class MemoryMonitor:
    """Pure Python memory monitoring for the Claude PM framework."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.config = {
            'memory_threshold_percent': 80,  # Alert when memory > 80%
            'check_interval': 5,  # Check every 5 seconds
            'subprocess_memory_limit_mb': 1500,  # 1.5GB per subprocess
            'max_subprocesses': 5,  # Maximum concurrent subprocesses
        }
        
        self.log_dir = log_dir or Path('.claude-pm/logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / 'memory-monitor.log'
        
        self._running = False
        self._tracked_pids: Set[int] = set()
        
    def get_memory_status(self) -> Dict:
        """Get current memory status of the system and process."""
        # System memory
        vm = psutil.virtual_memory()
        
        # Current process memory
        process = psutil.Process()
        process_info = process.memory_info()
        
        # Get child processes
        children = []
        try:
            for child in process.children(recursive=True):
                try:
                    child_info = child.memory_info()
                    children.append({
                        'pid': child.pid,
                        'name': child.name(),
                        'memory_mb': child_info.rss / 1024 / 1024,
                        'status': child.status()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except psutil.NoSuchProcess:
            pass
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'total_mb': vm.total / 1024 / 1024,
                'available_mb': vm.available / 1024 / 1024,
                'percent': vm.percent,
                'used_mb': vm.used / 1024 / 1024
            },
            'process': {
                'pid': process.pid,
                'memory_mb': process_info.rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(interval=0.1)
            },
            'children': children,
            'child_count': len(children),
            'total_child_memory_mb': sum(c['memory_mb'] for c in children)
        }
    
    def check_memory_limits(self, status: Dict) -> Dict:
        """Check if memory usage exceeds configured limits."""
        alerts = []
        
        # System memory check
        if status['system']['percent'] > self.config['memory_threshold_percent']:
            alerts.append({
                'level': 'WARNING',
                'message': f"System memory usage is {status['system']['percent']:.1f}%"
            })
        
        # Subprocess count check
        if status['child_count'] > self.config['max_subprocesses']:
            alerts.append({
                'level': 'WARNING',
                'message': f"Too many subprocesses: {status['child_count']} (max: {self.config['max_subprocesses']})"
            })
        
        # Individual subprocess memory check
        for child in status['children']:
            if child['memory_mb'] > self.config['subprocess_memory_limit_mb']:
                alerts.append({
                    'level': 'WARNING',
                    'message': f"Subprocess {child['pid']} ({child['name']}) using {child['memory_mb']:.1f}MB"
                })
        
        return alerts
    
    def cleanup_zombies(self) -> int:
        """Clean up zombie processes."""
        cleaned = 0
        for proc in psutil.process_iter(['pid', 'status', 'ppid']):
            try:
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    # Only clean zombies that are our children
                    if proc.info['ppid'] == os.getpid():
                        os.waitpid(proc.info['pid'], os.WNOHANG)
                        cleaned += 1
                        logger.info(f"Cleaned zombie process {proc.info['pid']}")
            except (psutil.NoSuchProcess, OSError):
                pass
        return cleaned
    
    def log_status(self, status: Dict, alerts: list):
        """Log memory status to file."""
        log_entry = {
            'timestamp': status['timestamp'],
            'level': 'ERROR' if any(a['level'] == 'ERROR' for a in alerts) else 
                     'WARNING' if alerts else 'INFO',
            'status': status,
            'alerts': alerts
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Starting memory monitor")
        self._running = True
        
        while self._running:
            try:
                # Get memory status
                status = self.get_memory_status()
                
                # Check limits
                alerts = self.check_memory_limits(status)
                
                # Clean zombies periodically
                if int(time.time()) % 30 == 0:  # Every 30 seconds
                    zombies_cleaned = self.cleanup_zombies()
                    if zombies_cleaned > 0:
                        logger.info(f"Cleaned {zombies_cleaned} zombie processes")
                
                # Log status
                self.log_status(status, alerts)
                
                # Print alerts to console
                for alert in alerts:
                    logger.warning(f"{alert['level']}: {alert['message']}")
                
            except Exception as e:
                logger.error(f"Error in memory monitor: {e}")
            
            await asyncio.sleep(self.config['check_interval'])
    
    def start(self):
        """Start the memory monitor."""
        asyncio.create_task(self.monitor_loop())
    
    def stop(self):
        """Stop the memory monitor."""
        self._running = False
        logger.info("Memory monitor stopped")


# Singleton instances
_monitor_instance: Optional[MemoryMonitor] = None
_subprocess_monitor_instance: Optional[SubprocessMemoryMonitor] = None


def get_memory_monitor(log_dir: Optional[Path] = None) -> MemoryMonitor:
    """Get or create the singleton memory monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = MemoryMonitor(log_dir)
    return _monitor_instance


def get_subprocess_memory_monitor(thresholds: Optional[MemoryThresholds] = None, log_dir: Optional[Path] = None) -> SubprocessMemoryMonitor:
    """Get or create the singleton subprocess memory monitor instance."""
    global _subprocess_monitor_instance
    if _subprocess_monitor_instance is None:
        _subprocess_monitor_instance = SubprocessMemoryMonitor(thresholds, log_dir)
    return _subprocess_monitor_instance


if __name__ == "__main__":
    # Test the monitor
    import asyncio
    
    async def test_monitor():
        monitor = get_memory_monitor()
        await monitor.monitor_loop()
    
    try:
        asyncio.run(test_monitor())
    except KeyboardInterrupt:
        print("\nMonitor stopped")