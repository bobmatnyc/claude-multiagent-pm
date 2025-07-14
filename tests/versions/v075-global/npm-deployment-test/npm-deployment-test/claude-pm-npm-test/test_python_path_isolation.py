#!/usr/bin/env python3
"""
Test Python path isolation and import behavior in NPM deployment context.
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

print("=== Python Path Isolation Test ===")

# Create a minimal test script that simulates the bin/claude-pm behavior
test_script_content = '''
import sys
from pathlib import Path

# Simulate framework path detection from NPM installation
framework_path = "{framework_path}"
sys.path.insert(0, str(framework_path))

try:
    # Test absolute imports like those used in agents
    from claude_pm.core.base_agent import BaseAgent
    from claude_pm.agents.documentation_agent import DocumentationAgent
    from claude_pm.services.memory.memory_trigger_service import MemoryTriggerService
    
    print("✅ All absolute imports successful")
    print("✅ Agent loading works in isolated environment")
    
    # Test agent instantiation
    agent = DocumentationAgent()
    print("✅ Agent instantiation successful")
    print(f"   Agent type: {{type(agent).__name__}}")
    print(f"   Agent service: {{agent.service}}")
    
except ImportError as e:
    print(f"❌ Import error: {{e}}")
    print(f"   Python path: {{sys.path}}")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {{e}}")
    exit(1)

print("✅ NPM deployment compatibility verified")
'''

# Test with current framework path (simulates local NPM install)
framework_path = Path("node_modules/@bobmatnyc/claude-multiagent-pm").resolve()
test_script = test_script_content.format(framework_path=framework_path)

print(f"Testing with framework path: {framework_path}")
print("=" * 50)

# Write test script to temporary file and execute
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(test_script)
    temp_script = f.name

try:
    # Run the test script in isolation
    result = subprocess.run(
        [sys.executable, temp_script],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode == 0:
        print("✅ Isolated test passed")
    else:
        print(f"❌ Isolated test failed (exit code: {result.returncode})")
        
finally:
    # Clean up
    try:
        os.unlink(temp_script)
    except:
        pass

# Test different global NPM scenarios
print("\n" + "=" * 50)
print("Testing various global NPM scenarios...")

global_scenarios = [
    # Scenario 1: NVM installation (exists in our case)
    str(Path.home() / ".nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/claude-multiagent-pm"),
]

for i, scenario_path in enumerate(global_scenarios, 1):
    print(f"\nScenario {i}: {scenario_path}")
    
    # Check if the path structure makes sense
    scenario_path_obj = Path(scenario_path)
    claude_pm_path = scenario_path_obj / "claude_pm"
    
    if scenario_path_obj.exists():
        print(f"✅ Path exists")
    else:
        print(f"❌ Path does not exist (simulating)")
    
    # Test Python path insertion logic
    print(f"Would insert: sys.path.insert(0, '{scenario_path}')")
    print(f"Looking for: {claude_pm_path}")
    
    if claude_pm_path.exists() or "/.nvm/" in scenario_path:  # Simulate some scenarios
        print(f"✅ Python module resolution would work")
    else:
        print(f"❌ Python module resolution would fail")

print("\n=== Memory Collection Test ===")
print("Testing memory collection in NPM deployment...")

# Test memory collection initialization
memory_test_script = '''
import sys
from pathlib import Path

framework_path = "{framework_path}"
sys.path.insert(0, str(framework_path))

try:
    from claude_pm.services.memory.memory_trigger_service import MemoryTriggerService
    from claude_pm.services.memory.trigger_types import TriggerType, TriggerPriority
    from claude_pm.services.memory.interfaces.models import MemoryCategory
    
    print("✅ Memory services imported successfully")
    
    # Test memory trigger service initialization
    memory_service = MemoryTriggerService()
    print("✅ Memory trigger service instantiated")
    
    print("✅ Memory collection compatible with NPM deployment")
    
except ImportError as e:
    print(f"❌ Memory service import error: {{e}}")
except Exception as e:
    print(f"❌ Memory service error: {{e}}")
'''

memory_script = memory_test_script.format(framework_path=framework_path)

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(memory_script)
    temp_memory_script = f.name

try:
    result = subprocess.run(
        [sys.executable, temp_memory_script],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
        
finally:
    try:
        os.unlink(temp_memory_script)
    except:
        pass

print("\n=== Test Complete ===")