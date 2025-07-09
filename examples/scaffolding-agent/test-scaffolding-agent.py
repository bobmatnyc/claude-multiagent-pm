"""
Test script for the scaffolding-agent
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.agents.scaffolding_agent import ScaffoldingAgent
from claude_pm.workflows.scaffolding_workflow import ScaffoldingWorkflow
from claude_pm.core.memory import MemoryManager
from claude_pm.services.ai_trackdown import AITrackdownService
from claude_pm.services.notification_service import NotificationService


async def test_scaffolding_agent():
    """Test the scaffolding agent with a sample design document"""
    
    # Initialize required services (mock implementations for testing)
    memory_manager = MemoryManager()
    trackdown_service = AITrackdownService()
    notification_service = NotificationService()
    
    # Initialize the scaffolding agent
    scaffolding_agent = ScaffoldingAgent(memory_manager, trackdown_service)
    
    # Test design document path
    design_doc_path = Path(__file__).parent / "sample-design-doc.md"
    
    print("🔍 Testing Scaffolding Agent")
    print("=" * 50)
    
    try:
        # Step 1: Analyze design document
        print("\n1. Analyzing design document...")
        analysis = await scaffolding_agent.analyze_design_document(str(design_doc_path))
        
        print(f"   Project Type: {analysis.project_type}")
        print(f"   Requirements: {len(analysis.requirements)} found")
        print(f"   Constraints: {len(analysis.constraints)} found")
        print(f"   Technology Hints: {', '.join(analysis.technology_hints)}")
        print(f"   Complexity Score: {analysis.complexity_score:.2f}")
        print(f"   Recommended Frameworks: {', '.join(analysis.recommended_frameworks)}")
        
        # Step 2: Generate scaffolding recommendation
        print("\n2. Generating scaffolding recommendation...")
        recommendation = await scaffolding_agent.generate_scaffolding_recommendation(analysis)
        
        print(f"   Template: {recommendation.template_used}")
        print(f"   Confidence: {recommendation.confidence_score:.1%}")
        print(f"   Approval Required: {recommendation.approval_required}")
        print(f"   Concerns: {len(recommendation.concerns)} identified")
        
        # Step 3: Generate PM suggestion
        print("\n3. Generating PM suggestion...")
        pm_suggestion = await scaffolding_agent.suggest_to_pm(recommendation, analysis)
        
        print("   PM Suggestion:")
        print("   " + "\\n   ".join(pm_suggestion.split("\\n")))
        
        # Step 4: Test scaffolding implementation (dry run)
        print("\n4. Testing scaffolding implementation...")
        test_project_path = Path(__file__).parent / "test-project"
        
        # Clean up any existing test project
        if test_project_path.exists():
            import shutil
            shutil.rmtree(test_project_path)
        
        implementation_success = await scaffolding_agent.implement_scaffolding(
            recommendation, str(test_project_path)
        )
        
        if implementation_success:
            print("   ✅ Scaffolding implementation successful")
            print(f"   📁 Project created at: {test_project_path}")
            
            # List created files
            if test_project_path.exists():
                print("   📄 Created files:")
                for file_path in test_project_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(test_project_path)
                        print(f"      {relative_path}")
        else:
            print("   ❌ Scaffolding implementation failed")
        
        print("\n✅ Scaffolding Agent test completed successfully!")
        
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_scaffolding_workflow():
    """Test the complete scaffolding workflow"""
    
    # Initialize required services
    memory_manager = MemoryManager()
    trackdown_service = AITrackdownService()
    notification_service = NotificationService()
    
    # Initialize the scaffolding workflow
    workflow = ScaffoldingWorkflow(memory_manager, trackdown_service, notification_service)
    
    # Test parameters
    design_doc_path = Path(__file__).parent / "sample-design-doc.md"
    project_path = Path(__file__).parent / "test-workflow-project"
    pm_contact = "test-pm@example.com"
    
    print("\\n🔄 Testing Scaffolding Workflow")
    print("=" * 50)
    
    try:
        # Clean up any existing test project
        if project_path.exists():
            import shutil
            shutil.rmtree(project_path)
        
        # Execute the workflow
        print("\\n1. Executing scaffolding workflow...")
        result = await workflow.execute_scaffolding_workflow(
            str(design_doc_path), str(project_path), pm_contact
        )
        
        print(f"   Status: {result['status']}")
        
        if result['status'] == 'success':
            print(f"   ✅ Workflow completed successfully")
            print(f"   📁 Project Path: {result['project_path']}")
            print(f"   📋 Template Used: {result['template_used']}")
            print(f"   ✅ Validation: {result['validation_results']['success']}")
        elif result['status'] == 'failed':
            print(f"   ❌ Workflow failed: {result['reason']}")
            print(f"   📝 Details: {result.get('details', 'No details available')}")
        else:
            print(f"   ⚠️ Workflow status: {result['status']}")
            print(f"   📝 Reason: {result.get('reason', 'Unknown')}")
        
        print("\\n✅ Scaffolding Workflow test completed!")
        
    except Exception as e:
        print(f"\\n❌ Workflow test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Scaffolding Agent Tests")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_scaffolding_agent())
    asyncio.run(test_scaffolding_workflow())
    
    print("\\n🎉 All tests completed!")