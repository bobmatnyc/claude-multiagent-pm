#!/usr/bin/env python3
"""Test script to demonstrate orchestration usage after deployment."""
import asyncio
import os
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

async def test_orchestration():
    """Test the orchestration functionality."""
    from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator
    from claude_pm.orchestration.orchestration_detector import OrchestrationDetector
    
    print("=== Orchestration Usage Test ===")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if orchestration is enabled
    detector = OrchestrationDetector()
    if not detector.is_orchestration_enabled():
        print("❌ Orchestration is not enabled. Creating CLAUDE.md...")
        Path("CLAUDE.md").write_text("# Test Project\n\nCLAUDE_PM_ORCHESTRATION: ENABLED\n")
    
    print(f"✅ Orchestration enabled: {detector.is_orchestration_enabled()}")
    print(f"   CLAUDE.md path: {detector.get_claude_md_path()}")
    
    # Create orchestrator
    orchestrator = BackwardsCompatibleOrchestrator()
    print("\n📦 BackwardsCompatibleOrchestrator created")
    
    # Test delegation
    print("\n🚀 Testing agent delegation...")
    
    # Example: Delegate to Documentation Agent
    try:
        result = await orchestrator.delegate_to_agent(
            agent_type="documentation",
            task_description="Analyze the orchestration module documentation and provide a summary",
            requirements=[
                "Review the orchestration module structure",
                "Identify key components and their roles",
                "Provide a brief summary of capabilities"
            ],
            deliverables=[
                "Summary of orchestration module components",
                "List of key features and capabilities"
            ],
            priority="high"
        )
        
        print(f"\n✅ Delegation completed!")
        print(f"   Result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            print(f"   Status: {result.get('status', 'N/A')}")
            if 'output' in result:
                print(f"   Output preview: {str(result['output'])[:200]}...")
        
        # Get metrics
        metrics = orchestrator.get_orchestration_metrics()
        print(f"\n📊 Orchestration Metrics:")
        print(f"   Total orchestrations: {metrics['total_orchestrations']}")
        
    except Exception as e:
        print(f"\n❌ Delegation error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ Orchestration test complete!")

if __name__ == "__main__":
    asyncio.run(test_orchestration())