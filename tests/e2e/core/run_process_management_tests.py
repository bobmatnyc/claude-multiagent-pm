#!/usr/bin/env python3
"""
Process Management Test Runner
==============================

Runs the process management E2E tests with proper reporting.
"""

import sys
import subprocess
from pathlib import Path
import time

def run_tests():
    """Run process management tests with detailed reporting."""
    test_dir = Path(__file__).parent
    test_files = [
        "test_process_management.py",
        "test_subprocess_isolation.py"
    ]
    
    print("=" * 80)
    print("Running Process Management E2E Tests")
    print("=" * 80)
    print()
    
    total_start = time.time()
    results = []
    
    for test_file in test_files:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running {test_file}...")
        print("-" * 60)
        
        start_time = time.time()
        
        # Run pytest with verbose output
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v",
            "--tb=short",
            "--no-header"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        # Store result
        results.append({
            'file': test_file,
            'returncode': result.returncode,
            'elapsed': elapsed,
            'stdout': result.stdout,
            'stderr': result.stderr
        })
        
        # Print summary
        if result.returncode == 0:
            print(f"✅ {test_file} - PASSED ({elapsed:.2f}s)")
        else:
            print(f"❌ {test_file} - FAILED ({elapsed:.2f}s)")
            if result.stderr:
                print("\nErrors:")
                print(result.stderr)
    
    total_elapsed = time.time() - total_start
    
    # Print final summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['returncode'] == 0)
    failed = len(results) - passed
    
    print(f"\nTotal Tests Run: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total Time: {total_elapsed:.2f}s")
    
    # Detailed failure report
    if failed > 0:
        print("\n" + "=" * 80)
        print("Failed Test Details")
        print("=" * 80)
        
        for result in results:
            if result['returncode'] != 0:
                print(f"\n❌ {result['file']}:")
                print("-" * 60)
                # Extract test failure details from stdout
                lines = result['stdout'].split('\n')
                in_failure = False
                for line in lines:
                    if 'FAILED' in line or 'ERROR' in line:
                        in_failure = True
                    if in_failure and line.strip():
                        print(f"  {line}")
                    if line.startswith('=') and in_failure:
                        break
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())