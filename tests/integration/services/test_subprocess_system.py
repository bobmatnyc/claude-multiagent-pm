#!/usr/bin/env python3
"""
Test the subprocess system to ensure environment variables are properly handled.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add framework to path
framework_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(framework_path))

from claude_pm.services.subprocess_runner import SubprocessRunner
from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator


async def test_subprocess_runner():
    """Test the subprocess runner directly."""
    print("=" * 80)
    print("Testing SubprocessRunner")
    print("=" * 80)
    
    runner = SubprocessRunner()
    
    # Test environment
    print("\n1. Testing environment setup...")
    test_result = runner.test_environment()
    print(f"Environment test result: {test_result}")
    
    if not test_result.get('success'):
        print(f"❌ Environment test failed: {test_result.get('error')}")
        return False
    
    print(f"✅ Environment test passed")
    print(f"   Framework path: {test_result.get('framework_path')}")
    print(f"   Available agents: {test_result.get('agents', {})}")
    
    # Test running an agent subprocess
    print("\n2. Testing agent subprocess execution...")
    task_data = {
        'task_description': 'Test subprocess execution with proper environment',
        'requirements': ['Verify environment variables are set', 'Load agent profile successfully'],
        'deliverables': ['Confirmation that agent profile was loaded', 'Environment details'],
        'current_date': '2025-11-18'
    }
    
    return_code, stdout, stderr = await runner.run_agent_subprocess_async(
        agent_type='engineer',
        task_data=task_data,
        timeout=30
    )
    
    print(f"\nSubprocess completed with return code: {return_code}")
    print(f"\nStdout:\n{stdout}")
    if stderr:
        print(f"\nStderr:\n{stderr}")
    
    return return_code == 0


async def test_orchestrator_subprocess():
    """Test the orchestrator with real subprocess mode."""
    print("\n" + "=" * 80)
    print("Testing BackwardsCompatibleOrchestrator with Real Subprocess")
    print("=" * 80)
    
    # Enable real subprocess mode
    os.environ['CLAUDE_PM_USE_REAL_SUBPROCESS'] = 'true'
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Test delegation
    result, return_code = await orchestrator.delegate_to_agent(
        agent_type='qa',
        task_description='Verify subprocess system is working correctly',
        requirements=['Check environment variables', 'Verify agent profile loading'],
        deliverables=['Test results', 'Environment verification']
    )
    
    print(f"\nOrchestration result:")
    print(f"Success: {result.get('success')}")
    print(f"Return code: {return_code}")
    print(f"Subprocess ID: {result.get('subprocess_id')}")
    
    if 'stdout' in result:
        print(f"\nSubprocess output:\n{result['stdout']}")
    
    if 'error' in result:
        print(f"\nError: {result['error']}")
    
    return result.get('success', False)


async def main():
    """Run all tests."""
    print("Claude PM Subprocess System Test")
    print("================================\n")
    
    # Test 1: Direct subprocess runner
    test1_passed = await test_subprocess_runner()
    
    # Test 2: Orchestrator with subprocess
    test2_passed = await test_orchestrator_subprocess()
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"SubprocessRunner test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Orchestrator subprocess test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed! Subprocess system is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)