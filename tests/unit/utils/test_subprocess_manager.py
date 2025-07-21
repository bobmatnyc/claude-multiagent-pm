#!/usr/bin/env python3
"""
Unit tests for the Unified Subprocess Manager
"""

import asyncio
import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

from claude_pm.utils.subprocess_manager import (
    SubprocessManager, 
    SubprocessResult, 
    SubprocessConfig,
    run_command,
    run_command_async
)


class TestSubprocessManager:
    """Test suite for SubprocessManager."""
    
    def test_basic_command_execution(self):
        """Test basic command execution."""
        manager = SubprocessManager()
        result = manager.run(['echo', 'Hello, World!'])
        
        assert result.success
        assert result.returncode == 0
        assert 'Hello, World!' in result.stdout
        assert result.stderr == ''
        assert not result.timed_out
        assert result.duration > 0
    
    def test_command_failure(self):
        """Test handling of failed commands."""
        manager = SubprocessManager()
        result = manager.run(['false'])  # Command that always fails
        
        assert not result.success
        assert result.returncode != 0
        assert not result.timed_out
    
    def test_command_not_found(self):
        """Test handling of non-existent commands."""
        manager = SubprocessManager()
        result = manager.run(['this-command-does-not-exist-12345'])
        
        assert not result.success
        assert result.returncode == -1
        assert 'No such file or directory' in result.stderr or 'not found' in result.stderr
    
    def test_timeout_handling(self):
        """Test command timeout handling."""
        manager = SubprocessManager()
        start_time = time.time()
        result = manager.run(['sleep', '10'], timeout=0.5)
        duration = time.time() - start_time
        
        assert not result.success
        assert result.timed_out
        assert duration < 2  # Should timeout quickly
        assert 'timed out' in result.stderr.lower()
    
    def test_output_capture(self):
        """Test stdout and stderr capture."""
        manager = SubprocessManager()
        
        # Test stdout capture
        result = manager.run([sys.executable, '-c', 'print("stdout output")'])
        assert result.success
        assert 'stdout output' in result.stdout
        
        # Test stderr capture
        result = manager.run([sys.executable, '-c', 'import sys; sys.stderr.write("stderr output")'])
        assert result.success
        assert 'stderr output' in result.stderr
    
    def test_working_directory(self):
        """Test command execution in different working directory."""
        manager = SubprocessManager()
        temp_dir = Path('/tmp')
        
        result = manager.run(['pwd'], cwd=temp_dir)
        assert result.success
        assert str(temp_dir) in result.stdout
    
    def test_environment_variables(self):
        """Test custom environment variables."""
        manager = SubprocessManager()
        custom_env = {'TEST_VAR': 'test_value'}
        
        result = manager.run(
            [sys.executable, '-c', 'import os; print(os.environ.get("TEST_VAR", "not found"))'],
            env=custom_env
        )
        assert result.success
        assert 'test_value' in result.stdout
    
    def test_shell_execution(self):
        """Test shell command execution."""
        manager = SubprocessManager()
        result = manager.run('echo $HOME', shell=True)
        
        assert result.success
        assert result.stdout.strip() != ''  # Should contain home directory
    
    def test_statistics_tracking(self):
        """Test execution statistics tracking."""
        manager = SubprocessManager()
        
        # Reset stats
        manager.reset_stats()
        
        # Execute some commands
        manager.run(['echo', 'test1'])
        manager.run(['false'])
        manager.run(['echo', 'test2'])
        
        stats = manager.get_stats()
        assert stats['total_executed'] == 3
        assert stats['successful'] == 2
        assert stats['failed'] == 1
        assert stats['success_rate'] == 2/3
        assert stats['average_duration'] > 0
    
    @pytest.mark.asyncio
    async def test_async_execution(self):
        """Test asynchronous command execution."""
        manager = SubprocessManager()
        result = await manager.run_async(['echo', 'async test'])
        
        assert result.success
        assert 'async test' in result.stdout
    
    @pytest.mark.asyncio
    async def test_parallel_async_execution(self):
        """Test parallel async command execution."""
        manager = SubprocessManager()
        
        # Run multiple commands in parallel
        start_time = time.time()
        tasks = [
            manager.run_async(['sleep', '0.1']),
            manager.run_async(['sleep', '0.1']),
            manager.run_async(['sleep', '0.1'])
        ]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        # All should succeed
        assert all(r.success for r in results)
        # Should run in parallel (faster than sequential)
        assert duration < 0.3
    
    def test_custom_configuration(self):
        """Test custom configuration."""
        config = SubprocessConfig(
            timeout=10,
            capture_output=False,
            text=False,
            encoding='latin-1'
        )
        manager = SubprocessManager(default_config=config)
        
        # Config should be applied
        assert manager.default_config.timeout == 10
        assert not manager.default_config.capture_output
        assert not manager.default_config.text
        assert manager.default_config.encoding == 'latin-1'
    
    def test_process_tracking(self):
        """Test active process tracking."""
        manager = SubprocessManager()
        
        # Should start with no active processes
        initial_stats = manager.get_stats()
        assert initial_stats['active_processes'] == 0
        
        # Note: Detailed process tracking test would require
        # mocking psutil or running longer processes
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test run_command
        result = run_command(['echo', 'convenience test'])
        assert result.success
        assert 'convenience test' in result.stdout
        
        # Test with kwargs
        result = run_command('echo $PWD', shell=True, timeout=5)
        assert result.success
    
    @pytest.mark.asyncio
    async def test_async_convenience_function(self):
        """Test async convenience function."""
        result = await run_command_async(['echo', 'async convenience'])
        assert result.success
        assert 'async convenience' in result.stdout


class TestSubprocessResult:
    """Test suite for SubprocessResult."""
    
    def test_result_properties(self):
        """Test SubprocessResult properties."""
        result = SubprocessResult(
            command=['test', 'command'],
            returncode=0,
            stdout='output',
            stderr='',
            duration=1.5,
            timed_out=False
        )
        
        assert result.success
        assert result.command == ['test', 'command']
        assert result.returncode == 0
        assert result.stdout == 'output'
        assert result.stderr == ''
        assert result.duration == 1.5
        assert not result.timed_out
    
    def test_failed_result(self):
        """Test failed result properties."""
        result = SubprocessResult(
            command=['test'],
            returncode=1,
            stdout='',
            stderr='error',
            duration=0.5,
            timed_out=False
        )
        
        assert not result.success
        assert result.returncode == 1
        assert result.stderr == 'error'
    
    def test_timeout_result(self):
        """Test timeout result properties."""
        result = SubprocessResult(
            command=['test'],
            returncode=-1,
            stdout='partial output',
            stderr='Process timed out',
            duration=10.0,
            timed_out=True
        )
        
        assert not result.success
        assert result.timed_out
        assert 'timed out' in result.stderr
    
    def test_result_serialization(self):
        """Test result serialization to dict."""
        result = SubprocessResult(
            command=['test'],
            returncode=0,
            stdout='output',
            stderr='',
            duration=1.0,
            timed_out=False,
            memory_peak_mb=50.5
        )
        
        data = result.to_dict()
        assert data['command'] == ['test']
        assert data['returncode'] == 0
        assert data['stdout'] == 'output'
        assert data['stderr'] == ''
        assert data['duration'] == 1.0
        assert data['timed_out'] == False
        assert data['success'] == True
        assert data['memory_peak_mb'] == 50.5


class TestSubprocessConfig:
    """Test suite for SubprocessConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SubprocessConfig()
        
        assert config.timeout == 300.0  # 5 minutes
        assert config.capture_output == True
        assert config.stream_output == False
        assert config.text == True
        assert config.shell == False
        assert config.check == False
        assert config.env is None
        assert config.cwd is None
        assert config.encoding == 'utf-8'
        assert config.memory_limit_mb == 1500.0
    
    def test_config_to_kwargs(self):
        """Test conversion to subprocess kwargs."""
        config = SubprocessConfig(
            shell=True,
            text=False,
            cwd='/tmp',
            encoding='latin-1'
        )
        
        kwargs = config.to_subprocess_kwargs()
        assert kwargs['shell'] == True
        assert kwargs['text'] == False
        assert kwargs['cwd'] == '/tmp'
        assert kwargs['encoding'] == 'latin-1'
        assert 'capture_output' in kwargs
    
    def test_streaming_config(self):
        """Test streaming configuration."""
        config = SubprocessConfig(stream_output=True)
        kwargs = config.to_subprocess_kwargs()
        
        # Should set up pipes for streaming
        assert 'stdout' in kwargs
        assert 'stderr' in kwargs
        assert 'capture_output' not in kwargs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])