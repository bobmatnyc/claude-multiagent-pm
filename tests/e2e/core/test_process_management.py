"""
E2E Tests for Process Management
================================

This module tests the complete process management functionality including:
- Subprocess creation and lifecycle
- Process state tracking
- Resource management and cleanup
- Process communication (stdin/stdout/stderr)
- Process timeout handling
- Concurrent process management
- Process monitoring and health checks
- Error handling and recovery
"""

import os
import sys
import pytest
import psutil
import asyncio
import signal
import time
import json
import tempfile
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import subprocess

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.e2e.utils.base_e2e_test import BaseE2ETest
from claude_pm.orchestration.subprocess_executor import SubprocessExecutor
from claude_pm.services.subprocess_runner import SubprocessRunner
from claude_pm.utils.task_tool_helper import TaskToolConfiguration
from claude_pm.orchestration.orchestration_types import ReturnCode


class TestProcessManagement(BaseE2ETest):
    """Test process management functionality."""
    
    @pytest.fixture
    def subprocess_executor(self):
        """Create a subprocess executor for testing."""
        config = TaskToolConfiguration(
            enabled=True,
            debug_mode=True,
            timeout_seconds=30
        )
        return SubprocessExecutor(self.test_dir, config)
    
    @pytest.fixture
    def subprocess_runner(self):
        """Create a subprocess runner for testing."""
        return SubprocessRunner(framework_path=self.project_root)
    
    def test_subprocess_creation_lifecycle(self, subprocess_runner):
        """Test subprocess creation and lifecycle management."""
        # Test basic subprocess creation
        task_data = {
            'task_description': 'Test process creation',
            'requirements': ['Create a test file'],
            'deliverables': ['test_output.txt']
        }
        
        # Run subprocess
        return_code, stdout, stderr = subprocess_runner.run_agent_subprocess(
            agent_type='test',
            task_data=task_data,
            timeout=10
        )
        
        # Verify process completed successfully
        assert return_code in [0, 1], f"Unexpected return code: {return_code}"
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)
    
    def test_process_state_tracking(self, subprocess_runner):
        """Test process state tracking during execution."""
        # Create a test script that runs for a predictable duration
        test_script = Path(self.test_dir) / "long_running.py"
        test_script.write_text("""
import time
import sys

print("Process started")
sys.stdout.flush()

for i in range(5):
    print(f"Working... {i}")
    sys.stdout.flush()
    time.sleep(0.5)

print("Process completed")
""")
        
        # Track process states
        states = []
        
        def track_process():
            """Track process states in a separate thread."""
            start_time = time.time()
            while time.time() - start_time < 5:
                # Get all Python processes
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'python' in proc.info['name'].lower():
                            cmdline = proc.info.get('cmdline', [])
                            if any('long_running.py' in arg for arg in cmdline):
                                states.append({
                                    'time': time.time() - start_time,
                                    'pid': proc.info['pid'],
                                    'status': proc.status(),
                                    'cpu_percent': proc.cpu_percent(interval=0.1),
                                    'memory_info': proc.memory_info()._asdict()
                                })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                time.sleep(0.1)
        
        # Start tracking thread
        tracker = threading.Thread(target=track_process)
        tracker.start()
        
        # Run the subprocess
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True
        )
        
        # Wait for tracker to finish
        tracker.join()
        
        # Verify we tracked some states
        assert len(states) > 0, "No process states were tracked"
        assert result.returncode == 0
        assert "Process started" in result.stdout
        assert "Process completed" in result.stdout
    
    def test_resource_management_cleanup(self, subprocess_runner):
        """Test resource management and cleanup after process completion."""
        # Create a script that creates temporary resources
        test_script = Path(self.test_dir) / "resource_test.py"
        test_script.write_text("""
import tempfile
import os
import sys

# Create temporary files
temp_files = []
for i in range(5):
    tf = tempfile.NamedTemporaryFile(delete=False, prefix=f"test_resource_{i}_")
    temp_files.append(tf.name)
    tf.write(b"test data")
    tf.close()

# Print file paths for verification
for f in temp_files:
    print(f"Created: {f}")

# Simulate work
import time
time.sleep(1)

# Clean up some files (simulate partial cleanup)
for f in temp_files[:3]:
    try:
        os.unlink(f)
        print(f"Cleaned: {f}")
    except:
        pass
""")
        
        # Run subprocess
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        # Extract created file paths
        created_files = []
        for line in result.stdout.split('\n'):
            if line.startswith("Created:"):
                created_files.append(line.split("Created:")[-1].strip())
        
        # Verify some files were created
        assert len(created_files) == 5
        
        # Check cleanup status
        remaining_files = [f for f in created_files if os.path.exists(f)]
        assert len(remaining_files) == 2, "Expected 2 files to remain after partial cleanup"
        
        # Clean up remaining files
        for f in remaining_files:
            try:
                os.unlink(f)
            except:
                pass
    
    def test_process_communication_streams(self, subprocess_runner):
        """Test process communication via stdin/stdout/stderr."""
        # Create an interactive test script
        test_script = Path(self.test_dir) / "interactive_test.py"
        test_script.write_text("""
import sys

print("Process ready", flush=True)

# Read from stdin
while True:
    line = sys.stdin.readline().strip()
    if not line or line == "exit":
        break
    
    # Echo to stdout
    print(f"STDOUT: Received '{line}'", flush=True)
    
    # Echo to stderr
    print(f"STDERR: Processing '{line}'", file=sys.stderr, flush=True)

print("Process completed", flush=True)
""")
        
        # Run interactive subprocess
        proc = subprocess.Popen(
            [sys.executable, str(test_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait for ready signal
        ready_line = proc.stdout.readline()
        assert "Process ready" in ready_line
        
        # Test communication
        test_messages = ["hello", "test123", "final message"]
        stdout_lines = []
        stderr_lines = []
        
        for msg in test_messages:
            # Send to stdin
            proc.stdin.write(f"{msg}\n")
            proc.stdin.flush()
            
            # Read from stdout
            stdout_line = proc.stdout.readline()
            stdout_lines.append(stdout_line.strip())
            
        # Send exit command
        proc.stdin.write("exit\n")
        proc.stdin.flush()
        
        # Wait for completion
        stdout_remaining, stderr_output = proc.communicate()
        
        # Verify communication
        assert all(f"STDOUT: Received '{msg}'" in line 
                  for msg, line in zip(test_messages, stdout_lines))
        assert all(f"STDERR: Processing '{msg}'" in stderr_output 
                  for msg in test_messages)
        assert proc.returncode == 0
    
    def test_process_timeout_handling(self, subprocess_runner):
        """Test process timeout handling and termination."""
        # Create a long-running script
        test_script = Path(self.test_dir) / "timeout_test.py"
        test_script.write_text("""
import time
import signal
import sys

def signal_handler(signum, frame):
    print(f"Received signal {signum}")
    sys.exit(1)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

print("Starting long task", flush=True)

# Run for 10 seconds
for i in range(10):
    print(f"Working... {i}", flush=True)
    time.sleep(1)

print("Task completed (should not reach here)")
""")
        
        # Test timeout with subprocess runner
        start_time = time.time()
        return_code, stdout, stderr = subprocess_runner.run_agent_subprocess(
            agent_type='test',
            task_data={'script': str(test_script)},
            timeout=3  # 3 second timeout
        )
        elapsed = time.time() - start_time
        
        # Verify timeout occurred
        assert elapsed < 5, "Process should have timed out within 5 seconds"
        assert return_code == -1, "Expected timeout return code"
        assert "Timeout" in stderr or "Timeout" in stdout
        
        # Test timeout with direct subprocess
        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                capture_output=True,
                text=True,
                timeout=2
            )
            assert False, "Should have raised TimeoutExpired"
        except subprocess.TimeoutExpired as e:
            assert e.timeout == 2
            assert "Starting long task" in e.stdout.decode() if e.stdout else True
    
    @pytest.mark.asyncio
    async def test_concurrent_process_management(self, subprocess_executor):
        """Test managing multiple concurrent processes."""
        # Enable real subprocess mode
        os.environ['CLAUDE_PM_USE_REAL_SUBPROCESS'] = 'true'
        
        try:
            # Create multiple concurrent tasks
            tasks = []
            num_processes = 5
            
            async def run_agent_task(agent_num: int):
                """Run a single agent task."""
                result, return_code = await subprocess_executor.execute_subprocess_delegation(
                    agent_type=f"test_agent_{agent_num}",
                    task_description=f"Concurrent test task {agent_num}",
                    task_id=f"concurrent_{agent_num}",
                    timeout_seconds=10
                )
                return agent_num, result, return_code
            
            # Start all tasks concurrently
            start_time = time.time()
            tasks = [run_agent_task(i) for i in range(num_processes)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            # Verify results
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) >= num_processes - 1, \
                f"Expected at least {num_processes-1} successful results, got {len(successful_results)}"
            
            # Verify concurrent execution (should be faster than sequential)
            assert elapsed < num_processes * 2, \
                f"Concurrent execution took too long: {elapsed}s"
            
            # Check individual results
            for result in successful_results:
                agent_num, task_result, return_code = result
                assert isinstance(task_result, dict)
                assert 'task_id' in task_result
                assert task_result['task_id'] == f"concurrent_{agent_num}"
                
        finally:
            os.environ.pop('CLAUDE_PM_USE_REAL_SUBPROCESS', None)
    
    def test_process_monitoring_health_checks(self, subprocess_runner):
        """Test process monitoring and health check capabilities."""
        # Create a script with health check endpoint
        test_script = Path(self.test_dir) / "health_check_test.py"
        test_script.write_text("""
import time
import sys
import json

health_status = {
    'status': 'starting',
    'uptime': 0,
    'tasks_completed': 0
}

# Write initial health status
with open('health_status.json', 'w') as f:
    json.dump(health_status, f)

print("Process started with health monitoring", flush=True)

# Simulate work with health updates
for i in range(5):
    health_status['status'] = 'running'
    health_status['uptime'] = i + 1
    health_status['tasks_completed'] = i
    
    with open('health_status.json', 'w') as f:
        json.dump(health_status, f)
    
    print(f"Task {i} completed", flush=True)
    time.sleep(0.5)

health_status['status'] = 'completed'
with open('health_status.json', 'w') as f:
    json.dump(health_status, f)

print("All tasks completed", flush=True)
""")
        
        # Start the process
        proc = subprocess.Popen(
            [sys.executable, str(test_script)],
            cwd=self.test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor health status
        health_checks = []
        health_file = Path(self.test_dir) / "health_status.json"
        
        # Wait for health file to be created
        for _ in range(10):
            if health_file.exists():
                break
            time.sleep(0.1)
        
        # Monitor health while process runs
        while proc.poll() is None:
            if health_file.exists():
                try:
                    with open(health_file, 'r') as f:
                        health_data = json.load(f)
                        health_checks.append({
                            'timestamp': time.time(),
                            'data': health_data.copy()
                        })
                except:
                    pass
            time.sleep(0.2)
        
        # Get final output
        stdout, stderr = proc.communicate()
        
        # Verify health monitoring worked
        assert len(health_checks) > 0, "No health checks were recorded"
        assert any(h['data']['status'] == 'starting' for h in health_checks)
        assert any(h['data']['status'] == 'running' for h in health_checks)
        assert any(h['data']['status'] == 'completed' for h in health_checks)
        
        # Verify progression
        uptimes = [h['data']['uptime'] for h in health_checks]
        assert max(uptimes) >= 4, "Process didn't run long enough"
        
        # Verify process completed successfully
        assert proc.returncode == 0
        assert "All tasks completed" in stdout
    
    def test_error_handling_recovery(self, subprocess_runner):
        """Test error handling and recovery mechanisms."""
        # Create a script that simulates various errors
        test_script = Path(self.test_dir) / "error_test.py"
        test_script.write_text("""
import sys
import time
import random

error_type = sys.argv[1] if len(sys.argv) > 1 else "none"

print(f"Testing error type: {error_type}", flush=True)

if error_type == "exception":
    # Unhandled exception
    raise RuntimeError("Simulated runtime error")
    
elif error_type == "segfault":
    # Simulate segmentation fault
    import ctypes
    ctypes.string_at(0)
    
elif error_type == "memory":
    # Memory exhaustion
    data = []
    while True:
        data.append("x" * 10**6)  # 1MB strings
        
elif error_type == "infinite_loop":
    # Infinite loop
    while True:
        time.sleep(0.01)
        
elif error_type == "exit_code":
    # Non-zero exit code
    print("Exiting with error code 42", flush=True)
    sys.exit(42)
    
else:
    print("No error, completing normally", flush=True)
""")
        
        # Test different error scenarios
        error_scenarios = [
            ("exception", "RuntimeError"),
            ("exit_code", "error code 42"),
            ("none", "completing normally")
        ]
        
        for error_type, expected_output in error_scenarios:
            # Run subprocess with error scenario
            return_code, stdout, stderr = subprocess_runner.run_agent_subprocess(
                agent_type='error_test',
                task_data={
                    'script': str(test_script),
                    'args': [error_type]
                },
                timeout=5
            )
            
            # Verify error handling
            if error_type == "none":
                assert return_code in [0, 1], f"Expected success for 'none' scenario"
                assert expected_output in stdout or expected_output in stderr
            else:
                assert return_code != 0, f"Expected failure for '{error_type}' scenario"
                # Error message might be in stdout or stderr
                output = stdout + stderr
                assert error_type in output or "error" in output.lower()
    
    def test_zombie_process_prevention(self):
        """Test prevention of zombie processes."""
        # Create a parent script that spawns children
        parent_script = Path(self.test_dir) / "parent_process.py"
        parent_script.write_text("""
import subprocess
import sys
import time
import os

# Spawn child processes that exit quickly
children = []
for i in range(3):
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(0.1); print('Child done')"],
        stdout=subprocess.PIPE
    )
    children.append(child)
    print(f"Spawned child {i} with PID {child.pid}")

# Don't wait for children (creates zombies without proper handling)
print("Parent continuing without waiting...")
time.sleep(2)

# Now properly reap children
for child in children:
    child.wait()
    print(f"Reaped child with return code: {child.returncode}")

print("Parent completed")
""")
        
        # Run the parent process
        result = subprocess.run(
            [sys.executable, str(parent_script)],
            capture_output=True,
            text=True
        )
        
        # Verify no zombies were left
        assert result.returncode == 0
        assert "Parent completed" in result.stdout
        assert all(f"Reaped child with return code: 0" in result.stdout 
                  for i in range(3))
    
    def test_process_pool_management(self):
        """Test process pool management for efficient resource usage."""
        # Create a worker script
        worker_script = Path(self.test_dir) / "pool_worker.py"
        worker_script.write_text("""
import sys
import time
import os

task_id = sys.argv[1] if len(sys.argv) > 1 else "unknown"
print(f"Worker {os.getpid()} processing task {task_id}", flush=True)

# Simulate work
time.sleep(0.5)

print(f"Worker {os.getpid()} completed task {task_id}", flush=True)
""")
        
        # Test with ProcessPoolExecutor
        num_tasks = 10
        max_workers = 3
        
        start_time = time.time()
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            # Submit tasks
            futures = []
            for i in range(num_tasks):
                future = pool.submit(
                    subprocess.run,
                    [sys.executable, str(worker_script), str(i)],
                    capture_output=True,
                    text=True
                )
                futures.append(future)
            
            # Collect results
            results = []
            for future in futures:
                result = future.result()
                results.append(result)
        
        elapsed = time.time() - start_time
        
        # Verify all tasks completed
        assert all(r.returncode == 0 for r in results)
        
        # Verify pool efficiency (should be faster than sequential)
        expected_sequential_time = num_tasks * 0.5
        assert elapsed < expected_sequential_time * 0.7, \
            f"Pool execution too slow: {elapsed}s vs expected < {expected_sequential_time * 0.7}s"
        
        # Extract worker PIDs to verify pool reuse
        worker_pids = set()
        for result in results:
            for line in result.stdout.split('\n'):
                if "Worker" in line and "processing" in line:
                    pid = int(line.split("Worker")[1].split("processing")[0].strip())
                    worker_pids.add(pid)
        
        # Should have reused workers (fewer PIDs than tasks)
        assert len(worker_pids) <= max_workers + 1, \
            f"Too many worker PIDs: {len(worker_pids)} (expected <= {max_workers + 1})"
    
    @pytest.mark.asyncio
    async def test_inter_process_communication(self):
        """Test inter-process communication mechanisms."""
        # Create producer and consumer scripts
        producer_script = Path(self.test_dir) / "ipc_producer.py"
        producer_script.write_text("""
import sys
import time
import json

# Produce messages
messages = [
    {"id": 1, "type": "data", "content": "First message"},
    {"id": 2, "type": "data", "content": "Second message"},
    {"id": 3, "type": "control", "content": "stop"}
]

for msg in messages:
    print(json.dumps(msg), flush=True)
    time.sleep(0.1)

sys.stderr.write("Producer completed\\n")
""")
        
        consumer_script = Path(self.test_dir) / "ipc_consumer.py"
        consumer_script.write_text("""
import sys
import json

received = []

for line in sys.stdin:
    try:
        msg = json.loads(line.strip())
        received.append(msg)
        
        if msg.get("type") == "control" and msg.get("content") == "stop":
            break
            
        # Echo processed message
        print(f"Processed: {msg['id']} - {msg['content']}", flush=True)
        
    except json.JSONDecodeError:
        continue

print(f"Consumer received {len(received)} messages", flush=True)
sys.stderr.write("Consumer completed\\n")
""")
        
        # Create pipeline: producer | consumer
        producer = await asyncio.create_subprocess_exec(
            sys.executable, str(producer_script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        consumer = await asyncio.create_subprocess_exec(
            sys.executable, str(consumer_script),
            stdin=producer.stdout,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for both to complete
        producer_stderr = await producer.stderr.read()
        consumer_stdout, consumer_stderr = await consumer.communicate()
        
        # Verify communication
        assert producer.returncode == 0
        assert consumer.returncode == 0
        assert b"Producer completed" in producer_stderr
        assert b"Consumer completed" in consumer_stderr
        assert b"Consumer received 3 messages" in consumer_stdout
        assert b"Processed: 1" in consumer_stdout
        assert b"Processed: 2" in consumer_stdout
    
    def test_process_crash_recovery(self, subprocess_runner):
        """Test recovery from process crashes."""
        # Create a script that can crash or recover
        crash_script = Path(self.test_dir) / "crash_recovery.py"
        crash_script.write_text("""
import sys
import os
import json
import time

# Read recovery state if exists
state_file = "recovery_state.json"
attempt = 1
last_checkpoint = 0

if os.path.exists(state_file):
    with open(state_file, 'r') as f:
        state = json.load(f)
        attempt = state.get('attempt', 1)
        last_checkpoint = state.get('checkpoint', 0)

print(f"Attempt {attempt}, starting from checkpoint {last_checkpoint}", flush=True)

# Process work in checkpoints
checkpoints = list(range(last_checkpoint, 10))

for checkpoint in checkpoints:
    print(f"Processing checkpoint {checkpoint}", flush=True)
    
    # Save state
    with open(state_file, 'w') as f:
        json.dump({
            'attempt': attempt,
            'checkpoint': checkpoint + 1
        }, f)
    
    # Simulate crash on attempt 1, checkpoint 5
    if attempt == 1 and checkpoint == 5:
        print("Simulating crash!", flush=True)
        sys.exit(1)
    
    time.sleep(0.1)

print("Work completed successfully!", flush=True)

# Clean up state file on success
if os.path.exists(state_file):
    os.unlink(state_file)
""")
        
        state_file = Path(self.test_dir) / "recovery_state.json"
        
        # First attempt (will crash)
        return_code, stdout, stderr = subprocess_runner.run_agent_subprocess(
            agent_type='crash_test',
            task_data={'script': str(crash_script)},
            timeout=5
        )
        
        # Verify crash occurred
        assert return_code != 0
        assert "Simulating crash!" in stdout
        assert state_file.exists(), "Recovery state should be saved"
        
        # Read recovery state
        with open(state_file, 'r') as f:
            state = json.load(f)
            assert state['checkpoint'] == 6, "Should have saved checkpoint before crash"
        
        # Second attempt (should recover and complete)
        return_code, stdout, stderr = subprocess_runner.run_agent_subprocess(
            agent_type='crash_test',
            task_data={'script': str(crash_script)},
            timeout=5
        )
        
        # Verify recovery and completion
        assert return_code in [0, 1]
        assert "Attempt 1, starting from checkpoint 6" in stdout or \
               "starting from checkpoint 6" in stdout
        assert "Work completed successfully!" in stdout
        assert not state_file.exists(), "State file should be cleaned up on success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])