#!/usr/bin/env python3
"""
Backwards Compatible Orchestration Demo
======================================

Demonstrates the BackwardsCompatibleOrchestrator with automatic mode selection
and seamless fallback between local orchestration and subprocess delegation.

Usage:
    # Default mode (auto-detect based on CLAUDE_PM_ORCHESTRATION)
    python scripts/backwards_compatible_orchestration_demo.py
    
    # Force local orchestration
    CLAUDE_PM_ORCHESTRATION=true python scripts/backwards_compatible_orchestration_demo.py
    
    # Force subprocess delegation
    python scripts/backwards_compatible_orchestration_demo.py --force-subprocess
    
    # Force local orchestration via flag
    python scripts/backwards_compatible_orchestration_demo.py --force-local
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from claude_pm.orchestration import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode,
    create_backwards_compatible_orchestrator,
    delegate_with_compatibility
)
from claude_pm.utils.task_tool_helper import TaskToolConfiguration


async def demonstrate_basic_delegation():
    """Demonstrate basic delegation with auto mode selection."""
    print("\n" + "="*60)
    print("BASIC DELEGATION DEMO")
    print("="*60)
    
    # Create orchestrator
    orchestrator = await create_backwards_compatible_orchestrator()
    
    # Check current mode
    is_enabled = os.environ.get("CLAUDE_PM_ORCHESTRATION", "").lower() == "true"
    print(f"\nCLAUDE_PM_ORCHESTRATION: {is_enabled}")
    print(f"Expected mode: {'local' if is_enabled else 'subprocess'}")
    
    # Delegate a task
    print("\nDelegating task to engineer agent...")
    result = await orchestrator.delegate_to_agent(
        agent_type="engineer",
        task_description="Implement a simple REST API endpoint",
        requirements=[
            "Use FastAPI framework",
            "Include input validation",
            "Add appropriate error handling"
        ],
        deliverables=[
            "API endpoint implementation",
            "Unit tests",
            "API documentation"
        ],
        priority="high"
    )
    
    # Display results
    print(f"\nDelegation successful: {result.get('success', False)}")
    print(f"Subprocess ID: {result.get('subprocess_id', 'N/A')}")
    
    if "orchestration_metadata" in result:
        metadata = result["orchestration_metadata"]
        print(f"\nOrchestration Mode: {metadata['mode']}")
        print(f"Decision Time: {metadata['metrics']['decision_time_ms']:.2f}ms")
        print(f"Execution Time: {metadata['metrics']['execution_time_ms']:.2f}ms")
        if metadata['metrics'].get('fallback_reason'):
            print(f"Fallback Reason: {metadata['metrics']['fallback_reason']}")
    
    if "local_orchestration" in result:
        local_info = result["local_orchestration"]
        print(f"\nLocal Orchestration Details:")
        print(f"  Context Filtering: {local_info.get('context_filtering_ms', 0):.2f}ms")
        print(f"  Message Routing: {local_info.get('message_routing_ms', 0):.2f}ms")
        print(f"  Filtered Context Size: {local_info.get('filtered_context_size', 0)} bytes")
    
    return orchestrator


async def demonstrate_forced_modes():
    """Demonstrate forced orchestration modes."""
    print("\n" + "="*60)
    print("FORCED MODE DEMO")
    print("="*60)
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Test forced local mode
    print("\n1. Testing FORCED LOCAL mode...")
    orchestrator.set_force_mode(OrchestrationMode.LOCAL)
    
    try:
        result = await orchestrator.delegate_to_agent(
            agent_type="qa",
            task_description="Run unit test suite",
            requirements=["Execute all tests", "Generate coverage report"]
        )
        
        mode = result.get("orchestration_metadata", {}).get("mode", "unknown")
        print(f"   Mode used: {mode}")
        print(f"   Success: {result.get('success', False)}")
    except Exception as e:
        print(f"   Error in local mode: {e}")
    
    # Test forced subprocess mode
    print("\n2. Testing FORCED SUBPROCESS mode...")
    orchestrator.set_force_mode(OrchestrationMode.SUBPROCESS)
    
    result = await orchestrator.delegate_to_agent(
        agent_type="documentation",
        task_description="Update API documentation",
        requirements=["Document all endpoints", "Include examples"]
    )
    
    mode = result.get("orchestration_metadata", {}).get("mode", "unknown")
    print(f"   Mode used: {mode}")
    print(f"   Success: {result.get('success', False)}")
    
    # Clear force mode
    orchestrator.set_force_mode(None)
    print("\n3. Force mode cleared - back to auto-detection")


async def demonstrate_performance_comparison():
    """Compare performance between modes."""
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON DEMO")
    print("="*60)
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Run multiple delegations in each mode
    modes = [OrchestrationMode.LOCAL, OrchestrationMode.SUBPROCESS]
    results = {}
    
    for mode in modes:
        print(f"\nTesting {mode.value} mode...")
        orchestrator.set_force_mode(mode)
        
        mode_results = []
        for i in range(3):
            try:
                result = await orchestrator.delegate_to_agent(
                    agent_type="research",
                    task_description=f"Research task {i+1}",
                    requirements=[f"Requirement {i+1}"]
                )
                
                if "orchestration_metadata" in result:
                    metrics = result["orchestration_metadata"]["metrics"]
                    mode_results.append({
                        "decision_time": metrics["decision_time_ms"],
                        "execution_time": metrics["execution_time_ms"],
                        "total_time": metrics["total_time_ms"]
                    })
            except Exception as e:
                print(f"   Error in {mode.value} mode: {e}")
        
        if mode_results:
            results[mode.value] = mode_results
    
    # Display comparison
    print("\n" + "-"*40)
    print("PERFORMANCE SUMMARY")
    print("-"*40)
    
    for mode, mode_results in results.items():
        if mode_results:
            avg_decision = sum(r["decision_time"] for r in mode_results) / len(mode_results)
            avg_execution = sum(r["execution_time"] for r in mode_results) / len(mode_results)
            avg_total = sum(r["total_time"] for r in mode_results) / len(mode_results)
            
            print(f"\n{mode.upper()} MODE:")
            print(f"  Avg Decision Time: {avg_decision:.2f}ms")
            print(f"  Avg Execution Time: {avg_execution:.2f}ms")
            print(f"  Avg Total Time: {avg_total:.2f}ms")


async def demonstrate_api_compatibility():
    """Demonstrate API compatibility with existing code."""
    print("\n" + "="*60)
    print("API COMPATIBILITY DEMO")
    print("="*60)
    
    print("\nTesting drop-in replacement compatibility...")
    
    # Use convenience function (like quick_create_subprocess)
    result = await delegate_with_compatibility(
        agent_type="ops",
        task_description="Deploy application to staging",
        requirements=["Validate configuration", "Run health checks"],
        deliverables=["Deployment report", "Health check results"]
    )
    
    # Check that result has expected structure
    required_fields = ["success", "subprocess_id", "subprocess_info", "prompt"]
    missing_fields = [field for field in required_fields if field not in result]
    
    print(f"\nAPI Compatibility Check:")
    print(f"  Required fields present: {len(required_fields) - len(missing_fields)}/{len(required_fields)}")
    if missing_fields:
        print(f"  Missing fields: {missing_fields}")
    else:
        print("  ✓ All required fields present")
    
    # Validate subprocess_info structure
    if "subprocess_info" in result:
        info = result["subprocess_info"]
        info_fields = ["subprocess_id", "agent_type", "task_description", "status"]
        info_present = [field for field in info_fields if field in info]
        print(f"\n  Subprocess info fields: {len(info_present)}/{len(info_fields)}")
    
    return result


async def demonstrate_validation():
    """Demonstrate validation capabilities."""
    print("\n" + "="*60)
    print("VALIDATION DEMO")
    print("="*60)
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    print("\nRunning compatibility validation...")
    validation = await orchestrator.validate_compatibility()
    
    print(f"\nValidation Results:")
    print(f"  Compatible: {validation['compatible']}")
    print(f"\n  Checks:")
    for check, result in validation["checks"].items():
        status = "✓" if result else "✗"
        print(f"    {status} {check}: {result}")
    
    # Get metrics
    metrics = orchestrator.get_orchestration_metrics()
    print(f"\n  Orchestration Metrics:")
    print(f"    Total orchestrations: {metrics['total_orchestrations']}")
    print(f"    Local orchestrations: {metrics['local_orchestrations']}")
    print(f"    Subprocess orchestrations: {metrics['subprocess_orchestrations']}")


async def main():
    """Run all demonstrations."""
    parser = argparse.ArgumentParser(description="Backwards Compatible Orchestration Demo")
    parser.add_argument("--force-local", action="store_true", 
                       help="Force local orchestration mode")
    parser.add_argument("--force-subprocess", action="store_true",
                       help="Force subprocess delegation mode")
    parser.add_argument("--skip-basic", action="store_true",
                       help="Skip basic delegation demo")
    parser.add_argument("--skip-forced", action="store_true",
                       help="Skip forced mode demo")
    parser.add_argument("--skip-performance", action="store_true",
                       help="Skip performance comparison")
    parser.add_argument("--skip-compatibility", action="store_true",
                       help="Skip API compatibility demo")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip validation demo")
    
    args = parser.parse_args()
    
    # Handle forced modes via environment
    if args.force_local:
        os.environ["CLAUDE_PM_ORCHESTRATION"] = "true"
        print("Forcing local orchestration via environment variable")
    elif args.force_subprocess:
        os.environ.pop("CLAUDE_PM_ORCHESTRATION", None)
        print("Forcing subprocess delegation by removing environment variable")
    
    print(f"\nBackwards Compatible Orchestration Demo")
    print(f"Current Time: {datetime.now().isoformat()}")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    try:
        # Run demonstrations
        if not args.skip_basic:
            orchestrator = await demonstrate_basic_delegation()
        
        if not args.skip_forced:
            await demonstrate_forced_modes()
        
        if not args.skip_performance:
            await demonstrate_performance_comparison()
        
        if not args.skip_compatibility:
            await demonstrate_api_compatibility()
        
        if not args.skip_validation:
            await demonstrate_validation()
        
        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())