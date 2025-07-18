#!/usr/bin/env python3
"""
Test script to simulate global NPM installation path resolution.
"""

import sys
import os
from pathlib import Path

print("=== Global NPM Installation Simulation ===")

# Simulate common global NPM installation paths
global_npm_paths = [
    "/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm",
    "/Users/masa/.nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/claude-multiagent-pm", 
    "/opt/homebrew/lib/node_modules/@bobmatnyc/claude-multiagent-pm",
    str(Path.home() / ".npm-global/lib/node_modules/@bobmatnyc/claude-multiagent-pm")
]

print("Testing path resolution for global NPM installations:")
for npm_path in global_npm_paths:
    npm_path_obj = Path(npm_path)
    print(f"\nTesting path: {npm_path}")
    
    # Check if this could be a valid NPM global installation
    if "node_modules" in npm_path and "claude-multiagent-pm" in npm_path:
        print(f"✅ Valid NPM global path structure")
        
        # Check if claude_pm Python module would be accessible
        claude_pm_path = npm_path_obj / "claude_pm"
        print(f"   Python module path: {claude_pm_path}")
        
        # Simulate sys.path.insert behavior
        if claude_pm_path.parent.exists() or npm_path == str(Path("node_modules/@bobmatnyc/claude-multiagent-pm").resolve()):
            print(f"✅ Python path resolution would work")
            print(f"   sys.path.insert(0, '{npm_path_obj}')")
        else:
            print(f"❌ Python path resolution would fail")
    else:
        print(f"❌ Invalid NPM path structure")

# Test the bin/claude-pm script framework path detection logic
print("\n=== Bin Script Framework Path Detection ===")

def simulate_framework_detection(script_location):
    """Simulate the detect_framework_path() function from bin/claude-pm"""
    script_path = Path(script_location).resolve()
    print(f"\nSimulating script at: {script_path}")
    
    # Check if we're in a symlinked environment  
    # (we can't actually test symlinks without creating them)
    print("Checking symlink resolution...")
    if script_path.parent == Path.home() / ".local" / "bin":
        print("✅ Detected ~/.local/bin deployment")
        # Look for framework in typical locations
        framework_candidates = [
            Path.home() / ".claude-pm",
            Path.home() / "Projects" / "claude-multiagent-pm",
            Path("/Users/masa/Projects/claude-multiagent-pm"),
        ]
        
        for candidate in framework_candidates:
            if (candidate / "claude_pm").exists():
                print(f"✅ Framework found: {candidate}")
                return candidate
        
    # Check if we're in NPM global installation
    elif "node_modules" in str(script_path):
        print("✅ Detected NPM installation")
        # Navigate from bin script to package root
        if script_path.name == "claude-pm" and script_path.parent.name == "bin":
            package_root = script_path.parent.parent
            if (package_root / "claude_pm").exists():
                print(f"✅ Package root found: {package_root}")
                return package_root
    
    # Check if we're in development mode
    elif "claude-multiagent-pm" in str(script_path):
        print("✅ Detected development mode")
        if (script_path.parent.parent / "claude_pm").exists():
            dev_root = script_path.parent.parent
            print(f"✅ Development root found: {dev_root}")
            return dev_root
    
    print("❌ Framework detection failed")
    return None

# Test various script locations
test_locations = [
    "/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm/bin/claude-pm",
    str(Path.home() / ".nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/claude-multiagent-pm/bin/claude-pm"),
    str(Path.home() / ".local/bin/claude-pm"),
    "/Users/masa/Projects/claude-multiagent-pm/bin/claude-pm"
]

for location in test_locations:
    framework_path = simulate_framework_detection(location)
    if framework_path:
        print(f"   → Framework resolved to: {framework_path}")
    else:
        print(f"   → Framework resolution failed")

print("\n=== Test Complete ===")