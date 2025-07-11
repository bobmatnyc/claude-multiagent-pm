#!/usr/bin/env python3
"""
Test script for enhanced startup display functionality.

This script validates that the enhanced startup display correctly detects
and displays AI-Trackdown-Tools and Memory Manager information.
"""

import subprocess
import sys
import os
from pathlib import Path

def test_startup_display_output():
    """Test that enhanced startup display includes all required information."""
    print("🧪 Testing Enhanced Startup Display...")
    
    # Run CLI command and capture output
    try:
        result = subprocess.run(
            ['python3', '-m', 'claude_pm.cli', 'health', '--help'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"❌ CLI command failed with return code {result.returncode}")
            print(f"stderr: {result.stderr}")
            return False
        
        output_lines = result.stdout.split('\n')
        
        # Check for required display elements
        required_elements = {
            '📁 Deployment:': False,
            '📂 Working:': False, 
            '🔧 AI-Trackdown:': False,
            '🧠 Memory:': False
        }
        
        for line in output_lines:
            for element in required_elements:
                if element in line:
                    required_elements[element] = True
                    print(f"✅ Found: {line.strip()}")
        
        # Validate all elements are present
        missing_elements = [elem for elem, found in required_elements.items() if not found]
        
        if missing_elements:
            print(f"❌ Missing required elements: {missing_elements}")
            print("Full output:")
            print(result.stdout)
            return False
        
        # Validate specific content patterns
        ai_trackdown_line = next((line for line in output_lines if '🔧 AI-Trackdown:' in line), '')
        memory_line = next((line for line in output_lines if '🧠 Memory:' in line), '')
        
        # AI-Trackdown should show version and deployment method
        if 'v1.' not in ai_trackdown_line or ('global' not in ai_trackdown_line and 'framework' not in ai_trackdown_line):
            print(f"❌ AI-Trackdown line format incorrect: {ai_trackdown_line}")
            return False
        
        # Memory should show mem0AI and status
        if 'mem0AI' not in memory_line or ('active' not in memory_line and 'inactive' not in memory_line):
            print(f"❌ Memory line format incorrect: {memory_line}")
            return False
        
        print("✅ All enhanced startup display elements validated successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


def test_detection_functions():
    """Test individual detection functions."""
    print("\n🧪 Testing Detection Functions...")
    
    # Import the functions
    sys.path.insert(0, str(Path(__file__).parent))
    from claude_pm.cli import _detect_aitrackdown_info, _detect_memory_manager_info
    
    # Test AI-Trackdown detection
    print("Testing AI-Trackdown detection...")
    ai_info = _detect_aitrackdown_info()
    print(f"  Result: {ai_info}")
    
    if ai_info == "error":
        print("  ❌ AI-Trackdown detection returned error")
        return False
    elif ai_info == "not found":
        print("  ⚠️  AI-Trackdown not found (this may be expected in some environments)")
    else:
        print("  ✅ AI-Trackdown detected successfully")
    
    # Test Memory Manager detection  
    print("Testing Memory Manager detection...")
    memory_info = _detect_memory_manager_info()
    print(f"  Result: {memory_info}")
    
    if memory_info == "error":
        print("  ❌ Memory Manager detection returned error")
        return False
    elif "not available" in memory_info:
        print("  ⚠️  Memory Manager not available (this may be expected in some environments)")
    else:
        print("  ✅ Memory Manager detected successfully")
    
    print("✅ Detection functions working correctly!")
    return True


def test_performance():
    """Test that startup display performance is acceptable."""
    print("\n🧪 Testing Performance...")
    
    import time
    
    start_time = time.time()
    
    # Run startup display multiple times
    for i in range(3):
        result = subprocess.run(
            ['python3', '-m', 'claude_pm.cli', 'health', '--help'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"❌ Performance test failed on iteration {i+1}")
            return False
    
    end_time = time.time()
    average_time = (end_time - start_time) / 3
    
    print(f"Average startup time: {average_time:.2f} seconds")
    
    if average_time > 3.0:
        print("❌ Startup time too slow (>3 seconds)")
        return False
    else:
        print("✅ Startup performance acceptable")
        return True


def main():
    """Run all tests."""
    print("🚀 Enhanced Startup Display Validation Tests")
    print("=" * 50)
    
    tests = [
        ("Startup Display Output", test_startup_display_output),
        ("Detection Functions", test_detection_functions),
        ("Performance", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())