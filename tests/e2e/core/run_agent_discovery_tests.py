#!/usr/bin/env python3
"""
Test runner for agent discovery E2E tests
Helps validate the comprehensive test suite

Created: 2025-07-19
Purpose: Quick test execution for EP-0044 validation
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all agent discovery E2E tests"""
    test_dir = Path(__file__).parent
    test_files = [
        "test_agent_discovery.py",
        "test_agent_registry_integration.py", 
        "test_agent_discovery_edge_cases.py"
    ]
    
    print("🧪 Running Agent Discovery E2E Tests")
    print("=" * 60)
    
    all_passed = True
    
    for test_file in test_files:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            all_passed = False
            continue
        
        print(f"\n📋 Running {test_file}...")
        print("-" * 40)
        
        # Run pytest with verbose output
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-xvs", str(test_path)],
            capture_output=False
        )
        
        if result.returncode == 0:
            print(f"✅ {test_file} passed")
        else:
            print(f"❌ {test_file} failed")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All agent discovery tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()