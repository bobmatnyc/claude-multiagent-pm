"""
Orchestration Integration Example
=================================

This example shows how to integrate the BackwardsCompatibleOrchestrator
as a drop-in replacement for existing TaskToolHelper usage.

The orchestrator automatically detects whether to use local orchestration
or fall back to subprocess delegation, maintaining 100% compatibility.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Original import (commented out):
# from claude_pm.utils.task_tool_helper import TaskToolHelper

# New import (drop-in replacement):
from claude_pm.orchestration import BackwardsCompatibleOrchestrator as TaskToolHelper
from claude_pm.utils.task_tool_helper import TaskToolConfiguration


async def existing_code_example():
    """
    This represents existing code that uses TaskToolHelper.
    No changes needed - just swap the import!
    """
    print("Running existing code with backwards compatible orchestrator...")
    
    # Create helper instance (works exactly the same)
    helper = TaskToolHelper(
        working_directory=Path.cwd(),
        config=TaskToolConfiguration(
            timeout_seconds=300,
            memory_collection_required=True
        )
    )
    
    # Create agent subprocess (API unchanged)
    result = await helper.delegate_to_agent(  # Note: method name mapped internally
        agent_type="engineer",
        task_description="Implement user authentication system",
        requirements=[
            "Use JWT tokens",
            "Include refresh token mechanism",
            "Add rate limiting"
        ],
        deliverables=[
            "Authentication endpoints",
            "Token management service",
            "Unit tests",
            "API documentation"
        ],
        priority="high"
    )
    
    # Process result (structure unchanged)
    if result.get("success"):
        print(f"\n✅ Task delegated successfully!")
        print(f"Subprocess ID: {result['subprocess_id']}")
        print(f"Agent Type: {result['subprocess_info']['agent_type']}")
        
        # New: Check orchestration mode if available
        if "orchestration_metadata" in result:
            mode = result["orchestration_metadata"]["mode"]
            print(f"\n🎯 Orchestration Mode: {mode}")
            
            if mode == "local":
                print("  → Using efficient local orchestration")
            else:
                print("  → Using traditional subprocess delegation")
    else:
        print(f"\n❌ Task delegation failed: {result.get('error', 'Unknown error')}")
    
    return result


async def migration_guide():
    """
    Step-by-step migration guide for existing projects.
    """
    print("\n" + "="*60)
    print("MIGRATION GUIDE")
    print("="*60)
    
    print("""
1. IMPORT CHANGE (One-line change):
   
   OLD:
   from claude_pm.utils.task_tool_helper import TaskToolHelper
   
   NEW:
   from claude_pm.orchestration import BackwardsCompatibleOrchestrator as TaskToolHelper

2. METHOD MAPPING (Automatic):
   
   If your code uses: helper.create_agent_subprocess(...)
   It automatically maps to: helper.delegate_to_agent(...)
   
3. ENABLE LOCAL ORCHESTRATION (Optional):
   
   Set environment variable to enable local orchestration:
   export CLAUDE_PM_ORCHESTRATION=true
   
   Without this, it uses subprocess delegation (100% compatible)

4. NO OTHER CHANGES NEEDED!
   
   - Same parameters
   - Same return structure  
   - Same error handling
   - Additional metadata in 'orchestration_metadata' field
""")


async def advanced_integration():
    """
    Advanced integration with mode control and metrics.
    """
    print("\n" + "="*60)
    print("ADVANCED INTEGRATION")
    print("="*60)
    
    # Use the orchestrator directly for more control
    from claude_pm.orchestration import BackwardsCompatibleOrchestrator, OrchestrationMode
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Example 1: Check current mode
    print("\n1. Checking orchestration mode...")
    mode, reason = await orchestrator._determine_orchestration_mode()
    print(f"   Mode: {mode.value}")
    if reason:
        print(f"   Reason: {reason}")
    
    # Example 2: Force specific mode for testing
    print("\n2. Testing forced modes...")
    
    # Force local mode
    orchestrator.set_force_mode(OrchestrationMode.LOCAL)
    result = await orchestrator.delegate_to_agent(
        agent_type="qa",
        task_description="Run test suite"
    )
    print(f"   Local mode result: {result.get('orchestration_metadata', {}).get('mode')}")
    
    # Force subprocess mode  
    orchestrator.set_force_mode(OrchestrationMode.SUBPROCESS)
    result = await orchestrator.delegate_to_agent(
        agent_type="qa",
        task_description="Run test suite"
    )
    print(f"   Subprocess mode result: {result.get('orchestration_metadata', {}).get('mode')}")
    
    # Clear force mode
    orchestrator.set_force_mode(None)
    
    # Example 3: Get performance metrics
    print("\n3. Performance metrics...")
    metrics = orchestrator.get_orchestration_metrics()
    print(f"   Total delegations: {metrics['total_orchestrations']}")
    print(f"   Average decision time: {metrics['average_decision_time_ms']:.2f}ms")
    print(f"   Average execution time: {metrics['average_execution_time_ms']:.2f}ms")
    
    # Example 4: Validate compatibility
    print("\n4. Validating compatibility...")
    validation = await orchestrator.validate_compatibility()
    print(f"   Compatible: {validation['compatible']}")
    print(f"   Checks passed: {sum(1 for v in validation['checks'].values() if v)}/{len(validation['checks'])}")


async def performance_benefits():
    """
    Demonstrate performance benefits of local orchestration.
    """
    print("\n" + "="*60)
    print("PERFORMANCE BENEFITS")
    print("="*60)
    
    print("""
Local Orchestration Benefits:

1. REDUCED OVERHEAD:
   - No subprocess creation overhead
   - No inter-process communication
   - Direct in-memory message passing

2. CONTEXT FILTERING:
   - Agent-specific context filtering
   - Reduced data transfer
   - Faster context access

3. SHARED RESOURCES:
   - Shared prompt cache (99.7% faster)
   - Reused agent registry
   - Connection pooling

4. METRICS & MONITORING:
   - Built-in performance metrics
   - Orchestration mode tracking
   - Fallback reason logging

Enable with: export CLAUDE_PM_ORCHESTRATION=true
""")


async def main():
    """Run all examples."""
    print("Backwards Compatible Orchestration Integration Examples")
    print("="*60)
    
    # Check environment
    is_enabled = os.environ.get("CLAUDE_PM_ORCHESTRATION", "").lower() == "true"
    print(f"\nCLAUDE_PM_ORCHESTRATION: {is_enabled}")
    print(f"Expected behavior: {'Local orchestration' if is_enabled else 'Subprocess delegation'}")
    
    try:
        # Run examples
        await existing_code_example()
        await migration_guide()
        await advanced_integration()
        await performance_benefits()
        
        print("\n" + "="*60)
        print("EXAMPLES COMPLETE")
        print("="*60)
        print("\nTo enable local orchestration:")
        print("export CLAUDE_PM_ORCHESTRATION=true")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # For existing code compatibility, support synchronous usage too
    if sys.version_info >= (3, 7):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())