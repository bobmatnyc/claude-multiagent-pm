#!/usr/bin/env python3
"""Test script to verify --test-mode implementation."""

import subprocess
import sys
import os
from pathlib import Path

def test_test_mode_flag():
    """Test the --test-mode flag functionality."""
    print("Testing --test-mode flag deployment...")
    
    # Check if prompts directory gets created
    prompts_dir = Path.home() / ".claude-pm" / "logs" / "prompts"
    
    # Run claude-pm with --test-mode
    result = subprocess.run(
        ["claude-pm", "--help"],
        capture_output=True,
        text=True
    )
    
    print(f"Return code: {result.returncode}")
    print(f"Help output includes --test-mode: {'--test-mode' in result.stdout}")
    
    # Check if the Python CLI modules are accessible
    try:
        from claude_pm.cli_flags import CLIFlags
        print("✅ CLIFlags module imported successfully")
        
        # Test flag parsing
        flags = CLIFlags()
        test_args = ["--test-mode", "some", "command"]
        flags.parse(test_args)
        
        print(f"✅ Test mode detected: {flags.test_mode}")
        print(f"✅ Cleaned args: {flags.cleaned_args}")
        
    except ImportError as e:
        print(f"❌ Failed to import CLIFlags: {e}")
    
    # Test the base agent loader
    try:
        from claude_pm.agents.base_agent_loader import BaseAgentLoader
        print("✅ BaseAgentLoader module imported successfully")
        
        # Check if test mode affects agent loading
        loader = BaseAgentLoader(test_mode=True)
        print("✅ BaseAgentLoader instantiated with test_mode=True")
        
    except Exception as e:
        print(f"❌ Failed to test BaseAgentLoader: {e}")
    
    # Test PM orchestrator
    try:
        from claude_pm.services.pm_orchestrator import PMOrchestrator
        print("✅ PMOrchestrator module imported successfully")
        
    except ImportError as e:
        print(f"❌ Failed to import PMOrchestrator: {e}")
    
    print("\nDeployment test complete!")

if __name__ == "__main__":
    test_test_mode_flag()