#!/usr/bin/env python3
"""
Test script to verify Python import paths work correctly in NPM deployment.
"""

import sys
import os
from pathlib import Path

print("=== NPM Deployment Import Test ===")
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {__file__}")
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
print()

# Test 1: Check if claude_pm can be imported from NPM installation
print("Test 1: NPM Package Import")
try:
    npm_package_path = Path("node_modules/@bobmatnyc/claude-multiagent-pm")
    if npm_package_path.exists():
        print(f"✅ NPM package found at: {npm_package_path.resolve()}")
        # Add to Python path
        sys.path.insert(0, str(npm_package_path.resolve()))
        print(f"Added to Python path: {npm_package_path.resolve()}")
    else:
        print("❌ NPM package not found")
        # Don't exit during test collection
        if __name__ == "__main__":
            sys.exit(1)
except Exception as e:
    print(f"❌ Error finding NPM package: {e}")
    # Don't exit during test collection
    if __name__ == "__main__":
        sys.exit(1)

# Test 2: Try importing claude_pm
print("\nTest 2: Claude PM Import")
try:
    import claude_pm
    print(f"✅ claude_pm imported successfully")
    print(f"   Location: {claude_pm.__file__}")
    if hasattr(claude_pm, '__version__'):
        print(f"   Version: {claude_pm.__version__}")
except ImportError as e:
    print(f"❌ Failed to import claude_pm: {e}")
except Exception as e:
    print(f"❌ Unexpected error importing claude_pm: {e}")

# Test 3: Try importing core modules with absolute imports
print("\nTest 3: Core Module Imports (Absolute)")
test_imports = [
    "claude_pm.core.base_agent",
    "claude_pm.core.config", 
    "claude_pm.core.base_service",
    "claude_pm.agents.documentation_agent",
    "claude_pm.agents.qa_agent",
    "claude_pm.services.memory.memory_trigger_service"
]

for module_name in test_imports:
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
    except Exception as e:
        print(f"❌ {module_name}: Unexpected error: {e}")

# Test 4: Test agent instantiation
print("\nTest 4: Agent Instantiation")
try:
    from claude_pm.core.base_agent import BaseAgent
    from claude_pm.agents.documentation_agent import DocumentationAgent
    
    print("✅ BaseAgent imported successfully")
    print("✅ DocumentationAgent imported successfully")
    
    # Try creating agent instance
    agent = DocumentationAgent()
    print("✅ DocumentationAgent instantiated successfully")
    
except ImportError as e:
    print(f"❌ Import error during agent test: {e}")
except Exception as e:
    print(f"❌ Unexpected error during agent test: {e}")

# Test 5: Check package structure
print("\nTest 5: Package Structure Verification")
npm_pkg = Path("node_modules/@bobmatnyc/claude-multiagent-pm")
expected_dirs = ["claude_pm", "bin", "framework", "install"]
for dir_name in expected_dirs:
    dir_path = npm_pkg / dir_name
    if dir_path.exists():
        print(f"✅ {dir_name}/ directory found")
    else:
        print(f"❌ {dir_name}/ directory missing")

print("\n=== Test Complete ===")