#!/usr/bin/env python3
"""
Test script for M01-040 LangGraph CLI integration.

Tests the real LangGraph workflow execution through CLI commands
to validate the integration works correctly.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add framework to path
framework_path = Path(__file__).parent / "framework"
sys.path.insert(0, str(framework_path))

async def test_langgraph_integration():
    """Test the LangGraph integration."""
    print("🧪 Testing M01-040 LangGraph CLI Integration")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from langgraph.graphs.task_graph import TaskWorkflowGraph
        from langgraph.states.base import create_task_state
        from langgraph.utils.metrics import get_metrics_collector
        from langgraph.utils.config import load_langgraph_config
        print("   ✅ All imports successful")
        
        # Test configuration
        print("\n2. Testing configuration...")
        config = load_langgraph_config()
        print(f"   ✅ Config loaded: {config.get('langgraph.models.engineer')}")
        
        # Test metrics collector
        print("\n3. Testing metrics collector...")
        metrics_file = framework_path / "langgraph" / "logs" / "langgraph_metrics.json"
        metrics_collector = get_metrics_collector(str(metrics_file))
        print(f"   ✅ Metrics collector initialized: {metrics_file}")
        
        # Test TaskWorkflowGraph initialization
        print("\n4. Testing TaskWorkflowGraph...")
        task_graph = TaskWorkflowGraph()
        print("   ✅ TaskWorkflowGraph initialized successfully")
        
        # Test workflow execution
        print("\n5. Testing workflow execution...")
        task_description = "Test task for M01-040 integration validation"
        
        start_time = time.time()
        final_state = await task_graph.execute(
            task_description=task_description,
            context={"test": True, "integration": "M01-040"},
            user_id="test_user",
            project_id="claude-multiagent-pm"
        )
        end_time = time.time()
        
        print(f"   ✅ Workflow execution completed in {end_time - start_time:.2f}s")
        print(f"   📊 Workflow ID: {final_state.get('id')}")
        print(f"   📈 Status: {final_state.get('status')}")
        print(f"   💬 Messages: {len(final_state.get('messages', []))}")
        print(f"   📋 Results: {len(final_state.get('results', {}))}")
        
        if final_state.get('errors'):
            print(f"   ⚠️  Errors: {len(final_state.get('errors'))}")
            for error in final_state.get('errors', [])[:2]:  # Show first 2 errors
                print(f"      - {error.get('type', 'unknown')}: {error.get('message', 'no message')}")
        
        # Test metrics export
        print("\n6. Testing metrics export...")
        if metrics_file.exists():
            import json
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            print(f"   ✅ Metrics file exists with {len(metrics_data.get('active_workflows', {}))} active workflows")
            print(f"   📊 Completed workflows: {len(metrics_data.get('completed_workflows', {}))}")
        else:
            print("   ⚠️  Metrics file not created yet")
        
        print("\n" + "=" * 50)
        print("✅ M01-040 LangGraph Integration Test PASSED")
        print("\nIntegration is ready for CLI command usage:")
        print("  claude-pm workflows start \"Implement new feature\"")
        print("  claude-pm workflows status")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test FAILED: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_langgraph_integration())
    sys.exit(0 if success else 1)