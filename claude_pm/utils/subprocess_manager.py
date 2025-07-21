#!/usr/bin/env python3
"""
Unified Subprocess Manager for Claude PM Framework
=================================================

This module provides a centralized, consistent subprocess management system
that consolidates all subprocess operations across the framework.

Key Features:
- Unified error handling and logging
- Consistent timeout management
- Output capture and streaming support
- Support for both sync and async execution
- Process lifecycle management
- Resource usage monitoring
- Automatic cleanup of zombie processes

Usage:
    from claude_pm.utils.subprocess_manager import SubprocessManager
    
    # Basic usage
    manager = SubprocessManager()
    result = manager.run(['git', 'status'], cwd='/path/to/repo')
    
    # With streaming output
    result = manager.run(['npm', 'install'], stream_output=True)
    
    # Async execution
    result = await manager.run_async(['python', 'script.py'])
"""

import os
import sys
import asyncio
import subprocess
import threading
import time
import signal
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import psutil

logger = logging.getLogger(__name__)


@dataclass
class SubprocessResult:
    """Result from a subprocess execution."""
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False
    memory_peak_mb: Optional[float] = None
    
    @property
    def success(self) -> bool:
        """Check if the subprocess completed successfully."""
        return self.returncode == 0 and not self.timed_out
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'command': self.command,
            'returncode': self.returncode,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'duration': self.duration,
            'timed_out': self.timed_out,
            'success': self.success,
            'memory_peak_mb': self.memory_peak_mb
        }


@dataclass
class SubprocessConfig:
    """Configuration for subprocess execution."""
    timeout: Optional[float] = 300.0  # 5 minutes default
    capture_output: bool = True
    stream_output: bool = False
    text: bool = True
    shell: bool = False
    check: bool = False
    env: Optional[Dict[str, str]] = None
    cwd: Optional[Union[str, Path]] = None
    encoding: str = 'utf-8'
    memory_limit_mb: Optional[float] = 1500.0  # 1.5GB default
    
    def to_subprocess_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs for subprocess functions."""
        kwargs = {
            'shell': self.shell,
            'text': self.text,
            'encoding': self.encoding,
        }
        
        if self.cwd:
            kwargs['cwd'] = str(self.cwd)
        
        if self.env:
            kwargs['env'] = self.env
        
        if self.capture_output and not self.stream_output:
            kwargs['capture_output'] = True
        elif self.stream_output:
            kwargs['stdout'] = subprocess.PIPE
            kwargs['stderr'] = subprocess.PIPE
        
        return kwargs


class SubprocessManager:
    """
    Unified subprocess management for the Claude PM framework.
    
    This manager provides consistent subprocess execution with:
    - Unified error handling
    - Resource monitoring
    - Timeout management
    - Output streaming
    - Process lifecycle tracking
    """
    
    def __init__(self, default_config: Optional[SubprocessConfig] = None):
        """Initialize the subprocess manager."""
        self.default_config = default_config or SubprocessConfig()
        self._active_processes: Dict[int, psutil.Process] = {}
        self._lock = threading.Lock()
        
        # Statistics tracking
        self._stats = {
            'total_executed': 0,
            'successful': 0,
            'failed': 0,
            'timed_out': 0,
            'total_duration': 0.0
        }
    
    def run(
        self,
        command: Union[str, List[str]],
        **kwargs
    ) -> SubprocessResult:
        """
        Run a subprocess synchronously.
        
        Args:
            command: Command to execute (string or list)
            **kwargs: Override default configuration
            
        Returns:
            SubprocessResult with execution details
        """
        # Merge configurations
        config = self._merge_config(kwargs)
        
        # Prepare command
        if isinstance(command, str) and not config.shell:
            command = command.split()
        elif isinstance(command, list) and config.shell:
            command = ' '.join(command)
        
        # Log execution
        logger.debug(f"Executing command: {command}")
        
        # Track statistics
        start_time = time.time()
        self._stats['total_executed'] += 1
        
        try:
            # Execute subprocess
            if config.stream_output:
                result = self._run_with_streaming(command, config)
            else:
                result = self._run_standard(command, config)
            
            # Update statistics
            if result.success:
                self._stats['successful'] += 1
            else:
                self._stats['failed'] += 1
            
            if result.timed_out:
                self._stats['timed_out'] += 1
            
            self._stats['total_duration'] += result.duration
            
            return result
            
        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            self._stats['failed'] += 1
            
            return SubprocessResult(
                command=command if isinstance(command, list) else [command],
                returncode=-1,
                stdout='',
                stderr=str(e),
                duration=time.time() - start_time,
                timed_out=False
            )
    
    async def run_async(
        self,
        command: Union[str, List[str]],
        **kwargs
    ) -> SubprocessResult:
        """
        Run a subprocess asynchronously.
        
        Args:
            command: Command to execute (string or list)
            **kwargs: Override default configuration
            
        Returns:
            SubprocessResult with execution details
        """
        # Merge configurations
        config = self._merge_config(kwargs)
        
        # Prepare command
        if isinstance(command, str) and not config.shell:
            command = command.split()
        elif isinstance(command, list) and config.shell:
            command = ' '.join(command)
        
        # Log execution
        logger.debug(f"Executing async command: {command}")
        
        # Track statistics
        start_time = time.time()
        self._stats['total_executed'] += 1
        
        try:
            # Execute subprocess
            result = await self._run_async_impl(command, config)
            
            # Update statistics
            if result.success:
                self._stats['successful'] += 1
            else:
                self._stats['failed'] += 1
            
            if result.timed_out:
                self._stats['timed_out'] += 1
            
            self._stats['total_duration'] += result.duration
            
            return result
            
        except Exception as e:
            logger.error(f"Async subprocess execution failed: {e}")
            self._stats['failed'] += 1
            
            return SubprocessResult(
                command=command if isinstance(command, list) else [command],
                returncode=-1,
                stdout='',
                stderr=str(e),
                duration=time.time() - start_time,
                timed_out=False
            )
    
    def _merge_config(self, kwargs: Dict[str, Any]) -> SubprocessConfig:
        """Merge kwargs with default configuration."""
        config = SubprocessConfig(
            timeout=kwargs.get('timeout', self.default_config.timeout),
            capture_output=kwargs.get('capture_output', self.default_config.capture_output),
            stream_output=kwargs.get('stream_output', self.default_config.stream_output),
            text=kwargs.get('text', self.default_config.text),
            shell=kwargs.get('shell', self.default_config.shell),
            check=kwargs.get('check', self.default_config.check),
            env=kwargs.get('env', self.default_config.env),
            cwd=kwargs.get('cwd', self.default_config.cwd),
            encoding=kwargs.get('encoding', self.default_config.encoding),
            memory_limit_mb=kwargs.get('memory_limit_mb', self.default_config.memory_limit_mb)
        )
        
        # Ensure environment includes current environment
        if config.env:
            env = os.environ.copy()
            env.update(config.env)
            config.env = env
        else:
            config.env = os.environ.copy()
        
        return config
    
    def _run_standard(self, command: Union[str, List[str]], config: SubprocessConfig) -> SubprocessResult:
        """Run subprocess without streaming."""
        start_time = time.time()
        kwargs = config.to_subprocess_kwargs()
        
        try:
            # Run with timeout
            result = subprocess.run(
                command,
                timeout=config.timeout,
                **kwargs
            )
            
            return SubprocessResult(
                command=command if isinstance(command, list) else [command],
                returncode=result.returncode,
                stdout=result.stdout if config.capture_output else '',
                stderr=result.stderr if config.capture_output else '',
                duration=time.time() - start_time,
                timed_out=False
            )
            
        except subprocess.TimeoutExpired as e:
            logger.warning(f"Command timed out after {config.timeout}s: {command}")
            
            # Try to get partial output
            stdout = e.stdout.decode(config.encoding) if e.stdout else ''
            stderr = e.stderr.decode(config.encoding) if e.stderr else ''
            
            return SubprocessResult(
                command=command if isinstance(command, list) else [command],
                returncode=-1,
                stdout=stdout,
                stderr=stderr + f"\nProcess timed out after {config.timeout} seconds",
                duration=time.time() - start_time,
                timed_out=True
            )
    
    def _run_with_streaming(self, command: Union[str, List[str]], config: SubprocessConfig) -> SubprocessResult:
        """Run subprocess with output streaming."""
        start_time = time.time()
        kwargs = config.to_subprocess_kwargs()
        
        # Force pipe for streaming
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        kwargs['bufsize'] = 1  # Line buffered
        
        stdout_lines = []
        stderr_lines = []
        
        try:
            with subprocess.Popen(command, **kwargs) as proc:
                # Track process
                self._track_process(proc)
                
                # Stream output
                for line in proc.stdout:
                    if config.text:
                        print(line.rstrip())
                        stdout_lines.append(line)
                    else:
                        sys.stdout.buffer.write(line)
                        stdout_lines.append(line.decode(config.encoding))
                
                # Wait for completion with timeout
                remaining_time = config.timeout - (time.time() - start_time) if config.timeout else None
                proc.wait(timeout=remaining_time)
                
                # Get any remaining stderr
                stderr = proc.stderr.read()
                if stderr:
                    if config.text:
                        stderr_lines.append(stderr)
                    else:
                        stderr_lines.append(stderr.decode(config.encoding))
                
                # Untrack process
                self._untrack_process(proc)
                
                return SubprocessResult(
                    command=command if isinstance(command, list) else [command],
                    returncode=proc.returncode,
                    stdout=''.join(stdout_lines),
                    stderr=''.join(stderr_lines),
                    duration=time.time() - start_time,
                    timed_out=False
                )
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Streaming command timed out after {config.timeout}s: {command}")
            
            # Terminate process
            if 'proc' in locals():
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                self._untrack_process(proc)
            
            return SubprocessResult(
                command=command if isinstance(command, list) else [command],
                returncode=-1,
                stdout=''.join(stdout_lines),
                stderr=''.join(stderr_lines) + f"\nProcess timed out after {config.timeout} seconds",
                duration=time.time() - start_time,
                timed_out=True
            )
    
    async def _run_async_impl(self, command: Union[str, List[str]], config: SubprocessConfig) -> SubprocessResult:
        """Async implementation of subprocess execution."""
        start_time = time.time()
        kwargs = config.to_subprocess_kwargs()
        
        # Remove subprocess-specific kwargs for asyncio
        kwargs.pop('capture_output', None)
        kwargs.pop('timeout', None)
        kwargs.pop('text', None)  # asyncio doesn't support text parameter
        kwargs.pop('encoding', None)  # asyncio doesn't support encoding parameter
        
        try:
            # Create subprocess
            if config.shell:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE if config.capture_output or config.stream_output else None,
                    stderr=asyncio.subprocess.PIPE if config.capture_output or config.stream_output else None,
                    **kwargs
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE if config.capture_output or config.stream_output else None,
                    stderr=asyncio.subprocess.PIPE if config.capture_output or config.stream_output else None,
                    **kwargs
                )
            
            # Track process
            if proc.pid:
                self._track_process_by_pid(proc.pid)
            
            try:
                # Wait with timeout
                if config.stream_output:
                    stdout, stderr = await self._stream_async_output(proc, config)
                else:
                    stdout_data, stderr_data = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=config.timeout
                    )
                    stdout = stdout_data.decode(config.encoding) if stdout_data else ''
                    stderr = stderr_data.decode(config.encoding) if stderr_data else ''
                
                # Untrack process
                if proc.pid:
                    self._untrack_process_by_pid(proc.pid)
                
                return SubprocessResult(
                    command=command if isinstance(command, list) else [command],
                    returncode=proc.returncode or 0,
                    stdout=stdout,
                    stderr=stderr,
                    duration=time.time() - start_time,
                    timed_out=False
                )
                
            except asyncio.TimeoutError:
                logger.warning(f"Async command timed out after {config.timeout}s: {command}")
                
                # Terminate process
                proc.terminate()
                await asyncio.sleep(0.5)
                if proc.returncode is None:
                    proc.kill()
                
                # Untrack process
                if proc.pid:
                    self._untrack_process_by_pid(proc.pid)
                
                return SubprocessResult(
                    command=command if isinstance(command, list) else [command],
                    returncode=-1,
                    stdout='',
                    stderr=f"Process timed out after {config.timeout} seconds",
                    duration=time.time() - start_time,
                    timed_out=True
                )
                
        except Exception as e:
            logger.error(f"Async subprocess failed: {e}")
            raise
    
    async def _stream_async_output(self, proc, config: SubprocessConfig) -> Tuple[str, str]:
        """Stream output from async subprocess."""
        stdout_lines = []
        stderr_lines = []
        
        async def read_stream(stream, lines, is_stderr=False):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode(config.encoding)
                if not is_stderr:
                    print(decoded.rstrip())
                lines.append(decoded)
        
        # Read both streams concurrently
        await asyncio.gather(
            read_stream(proc.stdout, stdout_lines) if proc.stdout else asyncio.sleep(0),
            read_stream(proc.stderr, stderr_lines, True) if proc.stderr else asyncio.sleep(0)
        )
        
        await proc.wait()
        
        return ''.join(stdout_lines), ''.join(stderr_lines)
    
    def _track_process(self, proc: subprocess.Popen):
        """Track an active process."""
        if proc.pid:
            with self._lock:
                try:
                    self._active_processes[proc.pid] = psutil.Process(proc.pid)
                except psutil.NoSuchProcess:
                    pass
    
    def _track_process_by_pid(self, pid: int):
        """Track an active process by PID."""
        with self._lock:
            try:
                self._active_processes[pid] = psutil.Process(pid)
            except psutil.NoSuchProcess:
                pass
    
    def _untrack_process(self, proc: subprocess.Popen):
        """Untrack a process."""
        if proc.pid:
            with self._lock:
                self._active_processes.pop(proc.pid, None)
    
    def _untrack_process_by_pid(self, pid: int):
        """Untrack a process by PID."""
        with self._lock:
            self._active_processes.pop(pid, None)
    
    def terminate_all(self):
        """Terminate all active processes."""
        with self._lock:
            for pid, proc in list(self._active_processes.items()):
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    try:
                        proc.kill()
                    except psutil.NoSuchProcess:
                        pass
                except Exception as e:
                    logger.error(f"Error terminating process {pid}: {e}")
            
            self._active_processes.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        with self._lock:
            active_count = len(self._active_processes)
        
        return {
            'total_executed': self._stats['total_executed'],
            'successful': self._stats['successful'],
            'failed': self._stats['failed'],
            'timed_out': self._stats['timed_out'],
            'success_rate': self._stats['successful'] / max(1, self._stats['total_executed']),
            'average_duration': self._stats['total_duration'] / max(1, self._stats['total_executed']),
            'active_processes': active_count
        }
    
    def reset_stats(self):
        """Reset execution statistics."""
        self._stats = {
            'total_executed': 0,
            'successful': 0,
            'failed': 0,
            'timed_out': 0,
            'total_duration': 0.0
        }


# Convenience functions for backward compatibility

def run_command(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    cwd: Optional[Union[str, Path]] = None,
    capture_output: bool = True,
    **kwargs
) -> SubprocessResult:
    """
    Run a command using the unified subprocess manager.
    
    This is a convenience function for simple subprocess execution.
    """
    manager = SubprocessManager()
    return manager.run(command, timeout=timeout, cwd=cwd, capture_output=capture_output, **kwargs)


async def run_command_async(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    cwd: Optional[Union[str, Path]] = None,
    capture_output: bool = True,
    **kwargs
) -> SubprocessResult:
    """
    Run a command asynchronously using the unified subprocess manager.
    
    This is a convenience function for simple async subprocess execution.
    """
    manager = SubprocessManager()
    return await manager.run_async(command, timeout=timeout, cwd=cwd, capture_output=capture_output, **kwargs)


# Singleton instance for global usage
_global_manager: Optional[SubprocessManager] = None


def get_global_manager() -> SubprocessManager:
    """Get or create the global subprocess manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = SubprocessManager()
    return _global_manager


if __name__ == "__main__":
    # Example usage and tests
    import asyncio
    
    def test_sync():
        """Test synchronous execution."""
        manager = SubprocessManager()
        
        # Basic command
        result = manager.run(['echo', 'Hello, World!'])
        print(f"Success: {result.success}")
        print(f"Output: {result.stdout.strip()}")
        
        # Command with timeout
        result = manager.run(['sleep', '10'], timeout=1)
        print(f"Timed out: {result.timed_out}")
        
        # Streaming output
        result = manager.run(['ls', '-la'], stream_output=True)
        print(f"Return code: {result.returncode}")
        
        # Print statistics
        print(f"\nStatistics: {json.dumps(manager.get_stats(), indent=2)}")
    
    async def test_async():
        """Test asynchronous execution."""
        manager = SubprocessManager()
        
        # Async command
        result = await manager.run_async(['echo', 'Async Hello!'])
        print(f"Async Success: {result.success}")
        print(f"Async Output: {result.stdout.strip()}")
        
        # Multiple async commands
        tasks = [
            manager.run_async(['echo', f'Task {i}'])
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)
        print(f"Completed {len(results)} async tasks")
    
    # Run tests
    print("Testing synchronous execution...")
    test_sync()
    
    print("\n\nTesting asynchronous execution...")
    asyncio.run(test_async())