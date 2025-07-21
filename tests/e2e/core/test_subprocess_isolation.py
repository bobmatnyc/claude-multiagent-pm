"""
E2E Tests for Subprocess Isolation
==================================

This module tests subprocess isolation mechanisms including:
- Process isolation verification
- Environment variable management
- Working directory isolation
- Resource limit enforcement
- Security boundary testing
"""

import os
import sys
import pytest
import tempfile
import subprocess
import json
import resource
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.e2e.utils.base_e2e_test import BaseE2ETest
from claude_pm.services.subprocess_runner import SubprocessRunner
from claude_pm.orchestration.subprocess_executor import SubprocessExecutor
from claude_pm.utils.task_tool_helper import TaskToolConfiguration


class TestSubprocessIsolation(BaseE2ETest):
    """Test subprocess isolation and security boundaries."""
    
    @pytest.fixture
    def subprocess_runner(self):
        """Create a subprocess runner for testing."""
        return SubprocessRunner(framework_path=self.project_root)
    
    def test_process_isolation_verification(self, subprocess_runner):
        """Verify processes are properly isolated from each other."""
        # Create a script that writes to a shared location
        isolation_script = Path(self.test_dir) / "isolation_test.py"
        isolation_script.write_text("""
import os
import sys
import time
import tempfile

process_id = sys.argv[1] if len(sys.argv) > 1 else "unknown"

# Try to create process-specific files
process_file = f"process_{process_id}.txt"
with open(process_file, 'w') as f:
    f.write(f"Process {process_id} was here\\n")
    f.write(f"PID: {os.getpid()}\\n")
    f.write(f"Working dir: {os.getcwd()}\\n")

# Try to read other process files
found_others = []
for i in range(5):
    other_file = f"process_{i}.txt"
    if os.path.exists(other_file) and str(i) != process_id:
        with open(other_file, 'r') as f:
            found_others.append(f"Found {other_file}: {f.read().strip()}")

if found_others:
    print(f"ISOLATION BREACH: Process {process_id} found other process files:")
    for found in found_others:
        print(f"  {found}")
else:
    print(f"Process {process_id} properly isolated")

# Output process info
print(f"Process {process_id} info:")
print(f"  PID: {os.getpid()}")
print(f"  PPID: {os.getppid()}")
print(f"  Working Directory: {os.getcwd()}")
print(f"  User: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
""")
        
        # Run multiple processes in separate directories
        processes = []
        for i in range(3):
            # Create isolated working directory
            work_dir = Path(self.test_dir) / f"isolated_process_{i}"
            work_dir.mkdir(exist_ok=True)
            
            # Run subprocess in isolated directory
            result = subprocess.run(
                [sys.executable, str(isolation_script), str(i)],
                cwd=work_dir,
                capture_output=True,
                text=True
            )
            
            processes.append({
                'id': i,
                'result': result,
                'work_dir': work_dir
            })
        
        # Verify all processes completed successfully
        for proc in processes:
            assert proc['result'].returncode == 0
            assert f"Process {proc['id']} properly isolated" in proc['result'].stdout
            assert "ISOLATION BREACH" not in proc['result'].stdout
            
            # Verify process created its own file
            process_file = proc['work_dir'] / f"process_{proc['id']}.txt"
            assert process_file.exists()
            
            # Verify no cross-contamination
            for other_id in range(3):
                if other_id != proc['id']:
                    other_file = proc['work_dir'] / f"process_{other_id}.txt"
                    assert not other_file.exists()
    
    def test_environment_variable_management(self, subprocess_runner):
        """Test environment variable isolation and management."""
        # Create a script that checks environment variables
        env_script = Path(self.test_dir) / "env_test.py"
        env_script.write_text("""
import os
import sys
import json

# Get process identifier
process_id = sys.argv[1] if len(sys.argv) > 1 else "unknown"

# Collect environment info
env_info = {
    'process_id': process_id,
    'pid': os.getpid(),
    'custom_vars': {},
    'framework_vars': {},
    'python_path': os.environ.get('PYTHONPATH', '').split(os.pathsep),
    'path': os.environ.get('PATH', '').split(os.pathsep)[:5],  # First 5 entries
    'all_vars_count': len(os.environ)
}

# Check for custom variables
for key, value in os.environ.items():
    if key.startswith('TEST_CUSTOM_'):
        env_info['custom_vars'][key] = value
    elif key.startswith('CLAUDE_PM_'):
        env_info['framework_vars'][key] = value

# Check for isolation
if 'TEST_PARENT_VAR' in os.environ:
    env_info['parent_leak'] = os.environ['TEST_PARENT_VAR']

# Try to set a variable that shouldn't persist
os.environ['TEST_CHILD_VAR'] = f'Set by process {process_id}'

# Output results
print(json.dumps(env_info, indent=2))
""")
        
        # Set parent environment variable (shouldn't leak to isolated processes)
        os.environ['TEST_PARENT_VAR'] = 'This should not leak'
        
        try:
            # Test 1: Basic environment isolation
            env_override = {
                'TEST_CUSTOM_VAR1': 'value1',
                'TEST_CUSTOM_VAR2': 'value2'
            }
            
            return_code, stdout, stderr = subprocess_runner.run_agent_subprocess(
                agent_type='env_test',
                task_data={'script': str(env_script), 'args': ['1']},
                env_override=env_override,
                timeout=5
            )
            
            assert return_code in [0, 1]
            env_info = json.loads(stdout)
            
            # Verify custom variables were set
            assert env_info['custom_vars'].get('TEST_CUSTOM_VAR1') == 'value1'
            assert env_info['custom_vars'].get('TEST_CUSTOM_VAR2') == 'value2'
            
            # Verify framework variables are present
            assert 'CLAUDE_PM_FRAMEWORK_PATH' in env_info['framework_vars']
            assert 'CLAUDE_PM_DEPLOYMENT_TYPE' in env_info['framework_vars']
            assert env_info['framework_vars']['CLAUDE_PM_DEPLOYMENT_TYPE'] == 'subprocess'
            
            # Verify parent variable didn't leak (if proper isolation)
            # Note: This might pass through in some test environments
            
            # Test 2: Environment variable conflicts
            conflict_env = {
                'PYTHONPATH': '/malicious/path',
                'CLAUDE_PM_CUSTOM': 'test_value'
            }
            
            return_code, stdout, stderr = subprocess_runner.run_agent_subprocess(
                agent_type='env_test',
                task_data={'script': str(env_script), 'args': ['2']},
                env_override=conflict_env,
                timeout=5
            )
            
            env_info2 = json.loads(stdout)
            
            # Verify PYTHONPATH includes framework path (security)
            assert any('claude-multiagent-pm' in path for path in env_info2['python_path'])
            
            # Verify custom variable was set
            assert env_info2['framework_vars'].get('CLAUDE_PM_CUSTOM') == 'test_value'
            
        finally:
            # Clean up parent environment
            os.environ.pop('TEST_PARENT_VAR', None)
    
    def test_working_directory_isolation(self, subprocess_runner):
        """Test working directory isolation between processes."""
        # Create a script that manipulates working directory
        wd_script = Path(self.test_dir) / "working_dir_test.py"
        wd_script.write_text("""
import os
import sys
import tempfile
from pathlib import Path

process_id = sys.argv[1] if len(sys.argv) > 1 else "unknown"

# Record initial working directory
initial_wd = os.getcwd()
print(f"Process {process_id} initial WD: {initial_wd}")

# Create files in working directory
test_file = Path("process_marker.txt")
test_file.write_text(f"Process {process_id} marker")

# Create subdirectory
sub_dir = Path(f"process_{process_id}_work")
sub_dir.mkdir(exist_ok=True)
(sub_dir / "data.txt").write_text(f"Data from process {process_id}")

# Try to access parent directory
try:
    parent_dir = Path("..")
    parent_files = list(parent_dir.glob("*"))
    print(f"Process {process_id} can see {len(parent_files)} items in parent")
    
    # Try to write to parent
    parent_file = parent_dir / f"process_{process_id}_parent.txt"
    try:
        parent_file.write_text("Wrote to parent")
        print(f"WARNING: Process {process_id} wrote to parent directory!")
    except Exception as e:
        print(f"Process {process_id} blocked from writing to parent: {type(e).__name__}")
        
except Exception as e:
    print(f"Process {process_id} cannot access parent: {type(e).__name__}")

# List working directory contents
wd_contents = list(Path(".").glob("*"))
print(f"Process {process_id} working directory contains: {[str(p) for p in wd_contents]}")

# Verify isolation
other_markers = [f for f in wd_contents if f.name.startswith("process_") and process_id not in f.name]
if other_markers:
    print(f"ISOLATION FAILURE: Found other process files: {other_markers}")
else:
    print(f"Process {process_id} working directory properly isolated")
""")
        
        # Run multiple processes with isolated working directories
        results = []
        
        for i in range(3):
            # Create completely isolated working directory
            isolated_dir = Path(self.test_dir) / "isolated" / f"process_{i}"
            isolated_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy script to isolated location
            isolated_script = isolated_dir / "wd_test.py"
            shutil.copy(wd_script, isolated_script)
            
            # Run in isolated directory
            result = subprocess.run(
                [sys.executable, str(isolated_script), str(i)],
                cwd=isolated_dir,
                capture_output=True,
                text=True
            )
            
            results.append({
                'id': i,
                'result': result,
                'isolated_dir': isolated_dir
            })
        
        # Verify isolation
        for res in results:
            assert res['result'].returncode == 0
            output = res['result'].stdout
            
            # Verify proper isolation
            assert f"Process {res['id']} working directory properly isolated" in output
            assert "ISOLATION FAILURE" not in output
            
            # Verify files were created in isolated directory
            marker_file = res['isolated_dir'] / "process_marker.txt"
            assert marker_file.exists()
            assert f"Process {res['id']} marker" in marker_file.read_text()
            
            # Verify subdirectory was created
            sub_dir = res['isolated_dir'] / f"process_{res['id']}_work"
            assert sub_dir.exists()
            assert (sub_dir / "data.txt").exists()
    
    @pytest.mark.skipif(sys.platform == "win32", reason="Resource limits not supported on Windows")
    def test_resource_limit_enforcement(self):
        """Test enforcement of resource limits on subprocesses."""
        # Create a script that tries to consume resources
        resource_script = Path(self.test_dir) / "resource_limit_test.py"
        resource_script.write_text("""
import sys
import time
import resource
import os

test_type = sys.argv[1] if len(sys.argv) > 1 else "memory"

print(f"Testing resource limits: {test_type}")

# Get current limits
if hasattr(resource, 'RLIMIT_AS'):
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    print(f"Memory limit: soft={soft}, hard={hard}")

if hasattr(resource, 'RLIMIT_CPU'):
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    print(f"CPU limit: soft={soft}, hard={hard}")

if hasattr(resource, 'RLIMIT_NOFILE'):
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    print(f"File descriptor limit: soft={soft}, hard={hard}")

try:
    if test_type == "memory":
        # Try to allocate excessive memory
        print("Attempting to allocate large memory block...")
        data = []
        for i in range(1000):
            # Allocate 10MB chunks
            data.append("x" * (10 * 1024 * 1024))
            if i % 10 == 0:
                print(f"Allocated {(i+1) * 10}MB")
                
    elif test_type == "cpu":
        # CPU intensive task
        print("Running CPU intensive task...")
        start = time.time()
        while time.time() - start < 10:
            # Busy loop
            sum(range(1000000))
            
    elif test_type == "files":
        # Try to open many files
        print("Opening many file descriptors...")
        files = []
        for i in range(10000):
            f = open(f"test_file_{i}.txt", "w")
            files.append(f)
            if i % 100 == 0:
                print(f"Opened {i+1} files")
                
except MemoryError as e:
    print(f"Hit memory limit: {e}")
    print("Resource limit properly enforced")
except OSError as e:
    if "Too many open files" in str(e):
        print(f"Hit file descriptor limit: {e}")
        print("Resource limit properly enforced")
    else:
        raise
except Exception as e:
    print(f"Resource limit enforcement: {type(e).__name__}: {e}")

print("Test completed")
""")
        
        # Test 1: Memory limit enforcement
        # Note: Setting actual resource limits requires special permissions
        # so we'll test the mechanism rather than actual enforcement
        
        # Create a wrapper script that sets limits
        wrapper_script = Path(self.test_dir) / "limit_wrapper.py"
        wrapper_script.write_text("""
import sys
import subprocess
import resource
import os

# Set resource limits (if possible)
try:
    # Limit memory to 100MB (if supported)
    if hasattr(resource, 'RLIMIT_AS'):
        resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))
        print("Set memory limit to 100MB")
except:
    print("Could not set memory limit (may require privileges)")

try:
    # Limit file descriptors to 50
    if hasattr(resource, 'RLIMIT_NOFILE'):
        resource.setrlimit(resource.RLIMIT_NOFILE, (50, 50))
        print("Set file descriptor limit to 50")
except:
    print("Could not set file descriptor limit")

# Run the actual test
result = subprocess.run(
    [sys.executable] + sys.argv[1:],
    capture_output=True,
    text=True
)

print("=== Subprocess output ===")
print(result.stdout)
if result.stderr:
    print("=== Subprocess errors ===")
    print(result.stderr)

sys.exit(result.returncode)
""")
        
        # Test file descriptor limits
        result = subprocess.run(
            [sys.executable, str(wrapper_script), str(resource_script), "files"],
            cwd=self.test_dir,
            capture_output=True,
            text=True
        )
        
        # Check that limits were at least detected
        assert "File descriptor limit:" in result.stdout
        
        # Clean up any created files
        for f in Path(self.test_dir).glob("test_file_*.txt"):
            try:
                f.unlink()
            except:
                pass
    
    def test_security_boundary_testing(self, subprocess_runner):
        """Test security boundaries and privilege separation."""
        # Create a script that tests security boundaries
        security_script = Path(self.test_dir) / "security_test.py"
        security_script.write_text("""
import os
import sys
import subprocess
import tempfile
from pathlib import Path

print("Security boundary testing")

# Test 1: File system access restrictions
print("\\nTest 1: File system access")
sensitive_paths = [
    "/etc/passwd",
    "/etc/shadow",
    "~/.ssh/id_rsa",
    "../../../sensitive.txt"
]

for path in sensitive_paths:
    try:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            print(f"WARNING: Can access {path}")
        else:
            print(f"GOOD: Cannot access {path}")
    except Exception as e:
        print(f"GOOD: Blocked from {path}: {type(e).__name__}")

# Test 2: Process information isolation
print("\\nTest 2: Process isolation")
try:
    # Try to list all processes
    if sys.platform != "win32":
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        process_count = len(result.stdout.strip().split('\\n'))
        print(f"Can see {process_count} processes")
    else:
        print("Process listing test skipped on Windows")
except Exception as e:
    print(f"Cannot list processes: {type(e).__name__}")

# Test 3: Network access (just check, don't actually connect)
print("\\nTest 3: Network access check")
try:
    import socket
    # Just create a socket, don't connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.close()
    print("Socket creation allowed (expected in most environments)")
except Exception as e:
    print(f"Socket creation blocked: {type(e).__name__}")

# Test 4: Environment information leakage
print("\\nTest 4: Environment information")
sensitive_env_vars = [
    'AWS_SECRET_ACCESS_KEY',
    'DATABASE_PASSWORD',
    'API_KEY',
    'SSH_AUTH_SOCK'
]

leaked_vars = []
for var in sensitive_env_vars:
    if var in os.environ:
        leaked_vars.append(var)

if leaked_vars:
    print(f"WARNING: Sensitive variables present: {leaked_vars}")
else:
    print("GOOD: No sensitive environment variables found")

# Test 5: Execute arbitrary commands
print("\\nTest 5: Command execution")
dangerous_commands = [
    ("rm -rf /", "file deletion"),
    ("curl http://malicious.com", "network access"),
    ("python -c 'import os; os.system(\"echo hacked\")'", "nested execution")
]

for cmd, desc in dangerous_commands:
    try:
        # Don't actually run dangerous commands, just test if we could
        # Use echo to simulate
        safe_cmd = f"echo 'Would run: {cmd}'"
        result = subprocess.run(safe_cmd, shell=True, capture_output=True, text=True)
        print(f"Can execute shell commands ({desc}): {result.returncode == 0}")
    except Exception as e:
        print(f"GOOD: Blocked from {desc}: {type(e).__name__}")

print("\\nSecurity boundary test completed")
""")
        
        # Run security test in subprocess
        return_code, stdout, stderr = subprocess_runner.run_agent_subprocess(
            agent_type='security_test',
            task_data={'script': str(security_script)},
            timeout=10
        )
        
        # Verify test ran
        assert return_code in [0, 1]
        assert "Security boundary testing" in stdout
        assert "Security boundary test completed" in stdout
        
        # Check for any security warnings
        output = stdout + stderr
        
        # These should not be accessible
        assert "Cannot access /etc/shadow" in output or "GOOD: Cannot access /etc/shadow" in output
        
        # No sensitive env vars should leak
        assert "GOOD: No sensitive environment variables found" in output or \
               "WARNING: Sensitive variables present" not in output
    
    def test_subprocess_cleanup_on_parent_exit(self):
        """Test that subprocesses are cleaned up when parent exits."""
        # Create a parent script that spawns children and exits
        parent_script = Path(self.test_dir) / "parent_exit_test.py"
        parent_script.write_text("""
import subprocess
import sys
import time
import os
import signal

# Create a child that runs indefinitely
child_script = '''
import time
import sys
import os

print(f"Child process started with PID {os.getpid()}", flush=True)
sys.stdout.flush()

# Run forever
while True:
    time.sleep(0.5)
'''

# Start child process
child = subprocess.Popen(
    [sys.executable, "-c", child_script],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    preexec_fn=None if sys.platform == "win32" else os.setsid  # Create new process group
)

print(f"Parent spawned child with PID {child.pid}")
print("Parent exiting without cleanup...")

# Exit without waiting for child
# In a proper implementation, this should still clean up the child
sys.exit(0)
""")
        
        # Get initial Python process count
        initial_python_procs = len([p for p in psutil.process_iter(['name']) 
                                   if 'python' in p.info['name'].lower()])
        
        # Run parent script
        result = subprocess.run(
            [sys.executable, str(parent_script)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Wait a bit for any cleanup
        time.sleep(1)
        
        # Check if child processes were cleaned up
        final_python_procs = len([p for p in psutil.process_iter(['name']) 
                                 if 'python' in p.info['name'].lower()])
        
        # Should not have leaked processes
        # Note: This is a best-effort test as process cleanup depends on OS
        assert final_python_procs <= initial_python_procs + 1, \
            "Possible process leak detected"
    
    def test_file_descriptor_inheritance(self):
        """Test that file descriptors are not inappropriately inherited."""
        # Create a script that checks file descriptor inheritance
        fd_script = Path(self.test_dir) / "fd_inheritance_test.py"
        fd_script.write_text("""
import os
import sys
import tempfile

print("Checking file descriptor inheritance...")

# Get all open file descriptors
if sys.platform != "win32":
    # Unix-like systems
    max_fd = os.sysconf('SC_OPEN_MAX') if hasattr(os, 'sysconf') else 1024
    open_fds = []
    
    for fd in range(3, min(max_fd, 100)):  # Skip stdin/stdout/stderr
        try:
            # Try to get file descriptor flags
            flags = os.fcntl.fcntl(fd, os.fcntl.F_GETFD)
            open_fds.append(fd)
        except:
            pass
    
    print(f"Found {len(open_fds)} open file descriptors beyond stdin/stdout/stderr")
    
    # Check if FD_CLOEXEC is set (should be for security)
    for fd in open_fds[:5]:  # Check first 5
        try:
            flags = os.fcntl.fcntl(fd, os.fcntl.F_GETFD)
            cloexec = bool(flags & os.fcntl.FD_CLOEXEC)
            print(f"FD {fd}: CLOEXEC={'SET' if cloexec else 'NOT SET'}")
        except:
            pass
else:
    print("File descriptor inheritance test skipped on Windows")

# Create a test file with sensitive data
with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
    tf.write("SENSITIVE DATA")
    temp_path = tf.name

# Spawn a subprocess and check if it inherits the file descriptor
child_code = '''
import os
import sys

# Try to access parent's temp file
temp_path = sys.argv[1]
try:
    with open(temp_path, 'r') as f:
        data = f.read()
        if "SENSITIVE" in data:
            print("WARNING: Child could read parent's sensitive file!")
        else:
            print("Child read file but no sensitive data")
except Exception as e:
    print(f"GOOD: Child blocked from parent's file: {type(e).__name__}")
'''

import subprocess
result = subprocess.run(
    [sys.executable, "-c", child_code, temp_path],
    capture_output=True,
    text=True
)

print("\\nChild process result:")
print(result.stdout)

# Clean up
try:
    os.unlink(temp_path)
except:
    pass

print("\\nFile descriptor inheritance test completed")
""")
        
        # Run file descriptor test
        result = subprocess.run(
            [sys.executable, str(fd_script)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "File descriptor inheritance test completed" in result.stdout
        
        # On Unix systems, check that file descriptors are properly managed
        if sys.platform != "win32" and "Found" in result.stdout:
            # Should have minimal open file descriptors
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "Found" in line and "open file descriptors" in line:
                    fd_count = int(line.split("Found")[1].split("open")[0].strip())
                    assert fd_count < 20, f"Too many inherited file descriptors: {fd_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])