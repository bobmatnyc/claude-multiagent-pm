#!/usr/bin/env python3
"""
Claude PM Framework - Python Subprocess Manager
Replaces the JavaScript subprocess manager with a pure Python implementation.
"""

import os
import signal
import psutil
import asyncio
import logging
import json
from typing import Dict, Optional, Set
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import subprocess
import time

logger = logging.getLogger(__name__)


@dataclass
class SubprocessInfo:
    """Information about a tracked subprocess."""
    pid: int
    name: str
    command: str
    created_at: float
    parent_pid: int
    memory_limit_mb: Optional[float] = None
    cpu_limit_percent: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class SubprocessManager:
    """Pure Python subprocess management for the Claude PM framework."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.config = {
            'max_concurrent_subprocesses': 5,
            'subprocess_memory_limit_mb': 1500,  # 1.5GB per subprocess
            'subprocess_timeout_seconds': 300,  # 5 minutes
            'cleanup_interval_seconds': 30,
            'zombie_check_interval_seconds': 60,
        }
        
        self.log_dir = log_dir or Path('.claude-pm/logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / 'subprocess-manager.log'
        
        self._subprocesses: Dict[int, SubprocessInfo] = {}
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
    def track_subprocess(self, pid: int, name: str, command: str, 
                        memory_limit_mb: Optional[float] = None) -> bool:
        """Track a new subprocess."""
        # Validate PID belongs to us
        try:
            proc = psutil.Process(pid)
            if proc.ppid() != os.getpid():
                logger.warning(f"Refusing to track unrelated process {pid}")
                return False
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} does not exist")
            return False
        
        info = SubprocessInfo(
            pid=pid,
            name=name,
            command=command,
            created_at=time.time(),
            parent_pid=os.getpid(),
            memory_limit_mb=memory_limit_mb or self.config['subprocess_memory_limit_mb']
        )
        
        self._subprocesses[pid] = info
        self._log_event('SUBPROCESS_TRACKED', f"Tracking {name} (PID: {pid})", {'info': info.to_dict()})
        logger.info(f"Tracking subprocess {pid}: {name}")
        return True
    
    def untrack_subprocess(self, pid: int, reason: str = "normal") -> bool:
        """Stop tracking a subprocess."""
        if pid in self._subprocesses:
            info = self._subprocesses.pop(pid)
            self._log_event('SUBPROCESS_UNTRACKED', f"Untracking {info.name} (PID: {pid})", 
                          {'reason': reason, 'lifetime_seconds': time.time() - info.created_at})
            logger.info(f"Untracked subprocess {pid}: {reason}")
            return True
        return False
    
    def terminate_subprocess(self, pid: int, reason: str = "manual", force: bool = False) -> bool:
        """Terminate a tracked subprocess."""
        if pid not in self._subprocesses:
            logger.warning(f"Process {pid} not tracked")
            return False
        
        try:
            proc = psutil.Process(pid)
            
            # Verify it's still our child
            if proc.ppid() != os.getpid():
                logger.warning(f"Process {pid} is no longer our child")
                self.untrack_subprocess(pid, "not_our_child")
                return False
            
            if force:
                proc.kill()  # SIGKILL
                logger.info(f"Force killed subprocess {pid}")
            else:
                proc.terminate()  # SIGTERM
                logger.info(f"Terminated subprocess {pid}")
                
                # Give it time to terminate gracefully
                try:
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    proc.kill()
                    logger.warning(f"Force killed subprocess {pid} after timeout")
            
            self.untrack_subprocess(pid, reason)
            return True
            
        except psutil.NoSuchProcess:
            self.untrack_subprocess(pid, "already_terminated")
            return True
        except Exception as e:
            logger.error(f"Error terminating process {pid}: {e}")
            return False
    
    def get_subprocess_status(self, pid: int) -> Optional[Dict]:
        """Get status of a tracked subprocess."""
        if pid not in self._subprocesses:
            return None
        
        try:
            proc = psutil.Process(pid)
            mem_info = proc.memory_info()
            
            return {
                'pid': pid,
                'name': self._subprocesses[pid].name,
                'status': proc.status(),
                'memory_mb': mem_info.rss / 1024 / 1024,
                'cpu_percent': proc.cpu_percent(interval=0.1),
                'lifetime_seconds': time.time() - self._subprocesses[pid].created_at
            }
        except psutil.NoSuchProcess:
            return None
    
    def cleanup_terminated(self) -> int:
        """Clean up terminated subprocesses."""
        cleaned = 0
        pids_to_remove = []
        
        for pid in list(self._subprocesses.keys()):
            try:
                proc = psutil.Process(pid)
                if proc.status() == psutil.STATUS_ZOMBIE:
                    # Try to reap zombie
                    try:
                        os.waitpid(pid, os.WNOHANG)
                        pids_to_remove.append(pid)
                        cleaned += 1
                    except OSError:
                        pass
            except psutil.NoSuchProcess:
                pids_to_remove.append(pid)
                cleaned += 1
        
        for pid in pids_to_remove:
            self.untrack_subprocess(pid, "cleaned_up")
        
        return cleaned
    
    def enforce_limits(self) -> Dict[str, int]:
        """Enforce configured limits on subprocesses."""
        stats = {
            'memory_violations': 0,
            'timeout_violations': 0,
            'terminated': 0
        }
        
        current_time = time.time()
        
        for pid, info in list(self._subprocesses.items()):
            try:
                status = self.get_subprocess_status(pid)
                if not status:
                    continue
                
                # Check memory limit
                if status['memory_mb'] > info.memory_limit_mb:
                    logger.warning(f"Subprocess {pid} exceeds memory limit: {status['memory_mb']:.1f}MB > {info.memory_limit_mb}MB")
                    stats['memory_violations'] += 1
                    if self.terminate_subprocess(pid, "memory_limit_exceeded"):
                        stats['terminated'] += 1
                    continue
                
                # Check timeout
                if current_time - info.created_at > self.config['subprocess_timeout_seconds']:
                    logger.warning(f"Subprocess {pid} exceeded timeout")
                    stats['timeout_violations'] += 1
                    if self.terminate_subprocess(pid, "timeout_exceeded"):
                        stats['terminated'] += 1
                        
            except Exception as e:
                logger.error(f"Error enforcing limits for {pid}: {e}")
        
        # Enforce max concurrent subprocesses
        if len(self._subprocesses) > self.config['max_concurrent_subprocesses']:
            # Terminate oldest subprocesses
            sorted_procs = sorted(self._subprocesses.items(), 
                                key=lambda x: x[1].created_at)
            excess = len(self._subprocesses) - self.config['max_concurrent_subprocesses']
            
            for pid, _ in sorted_procs[:excess]:
                if self.terminate_subprocess(pid, "max_concurrent_exceeded"):
                    stats['terminated'] += 1
        
        return stats
    
    async def cleanup_loop(self):
        """Background cleanup loop."""
        logger.info("Starting subprocess cleanup loop")
        
        while self._running:
            try:
                # Cleanup terminated processes
                cleaned = self.cleanup_terminated()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} terminated subprocesses")
                
                # Enforce limits
                stats = self.enforce_limits()
                if any(stats.values()):
                    logger.info(f"Limit enforcement: {stats}")
                
                # Log current state
                self._log_event('CLEANUP_CYCLE', 'Cleanup completed', {
                    'active_subprocesses': len(self._subprocesses),
                    'cleaned': cleaned,
                    'enforcement_stats': stats
                })
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
            
            await asyncio.sleep(self.config['cleanup_interval_seconds'])
    
    def _log_event(self, event_type: str, message: str, data: Optional[Dict] = None):
        """Log an event to the subprocess log file."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'data': data or {},
            'active_subprocesses': len(self._subprocesses)
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def start(self):
        """Start the subprocess manager."""
        if not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self.cleanup_loop())
            logger.info("Subprocess manager started")
    
    def stop(self):
        """Stop the subprocess manager."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Terminate all tracked subprocesses
        for pid in list(self._subprocesses.keys()):
            self.terminate_subprocess(pid, "manager_shutdown")
        
        logger.info("Subprocess manager stopped")
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        return {
            'active_subprocesses': len(self._subprocesses),
            'subprocesses': [self.get_subprocess_status(pid) 
                           for pid in self._subprocesses],
            'config': self.config
        }


# Singleton instance
_manager_instance: Optional[SubprocessManager] = None


def get_subprocess_manager(log_dir: Optional[Path] = None) -> SubprocessManager:
    """Get or create the singleton subprocess manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SubprocessManager(log_dir)
    return _manager_instance


if __name__ == "__main__":
    # Test the manager
    import asyncio
    
    async def test_manager():
        manager = get_subprocess_manager()
        manager.start()
        
        # Test tracking a subprocess
        proc = subprocess.Popen(['sleep', '10'])
        manager.track_subprocess(proc.pid, 'test_sleep', 'sleep 10')
        
        # Let it run for a bit
        await asyncio.sleep(5)
        
        # Check stats
        print(json.dumps(manager.get_stats(), indent=2))
        
        # Stop
        manager.stop()
    
    try:
        asyncio.run(test_manager())
    except KeyboardInterrupt:
        print("\nManager stopped")