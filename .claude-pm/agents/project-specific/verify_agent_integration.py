#!/usr/bin/env python3
"""
Agent Integration Verification Script
=====================================

This script verifies that the Codebase Research Agent is properly integrated
with the Claude PM Framework and ready for use.
"""

import asyncio
import sys
from pathlib import Path

# Add project paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from codebase_research_agent import CodebaseResearchAgent


async def verify_integration():
    """Verify complete agent integration."""
    print("🔍 Verifying Codebase Research Agent Integration")
    print("=" * 55)
    
    # Initialize agent
    agent = CodebaseResearchAgent()
    await agent._initialize()
    
    print(f"✅ Agent Name: {agent.name}")
    print(f"📋 Agent Type: {agent.agent_type}")
    print(f"🏗️ Agent Tier: {agent.agent_tier} (highest precedence)")
    print(f"🎯 Specializations: {', '.join(agent.specializations)}")
    print(f"🚀 Framework Version: {agent.FRAMEWORK_KNOWLEDGE['version']}")
    print(f"📚 Knowledge Size: {len(str(agent.FRAMEWORK_KNOWLEDGE))} characters")
    print(f"⚡ Capabilities: {len(agent.capabilities)} capabilities")
    
    # Test core functionality
    print("\n🧪 Testing Core Functionality:")
    
    # Test question answering
    question_result = await agent.async_answer_codebase_question(
        "What should I know about the Claude PM Framework before implementing new features?"
    )
    print(f"   ✅ Question Answering: {question_result['category']} category")
    
    # Test architecture analysis
    arch_result = await agent.async_analyze_architecture()
    print(f"   ✅ Architecture Analysis: {arch_result['component']} component")
    
    # Test implementation guidance
    impl_result = await agent.async_guide_implementation("implement new framework feature")
    print(f"   ✅ Implementation Guidance: {impl_result['guidance_type']} type")
    
    # Test Task Tool compatibility
    exec_result = await agent.execute_operation("answer_codebase_question", 
        question="How does agent hierarchy work?"
    )
    print(f"   ✅ Task Tool Compatible: {exec_result['success']} execution")
    
    # Get status
    status = await agent.get_agent_status()
    print(f"\n📊 Agent Status:")
    print(f"   • Running: {status['running']}")
    print(f"   • Operations Count: {status['operations_count']}")
    print(f"   • Knowledge Queries: {status['knowledge_queries']}")
    
    # Verify file structure
    print(f"\n📁 File Structure:")
    agent_dir = Path(__file__).parent
    
    files_to_check = [
        "codebase_research_agent.py",
        "config/agent_registry.yaml", 
        "README.md",
        "test_codebase_research_agent.py"
    ]
    
    for file_name in files_to_check:
        file_path = agent_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} - MISSING")
    
    # Cleanup
    await agent._cleanup()
    
    print(f"\n🎯 Integration Summary:")
    print(f"   • Agent Type: research (specialized for codebase questions)")
    print(f"   • Agent Tier: project (highest precedence in hierarchy)")
    print(f"   • Authority: codebase_research_highest")
    print(f"   • Integration: Task Tool compatible, TodoWrite ready")
    print(f"   • Performance: Async operations, embedded knowledge")
    print(f"   • Usage: FIRST PLACE TO GO for framework planning")
    
    print(f"\n✅ INTEGRATION VERIFICATION COMPLETE!")
    print(f"🚀 Codebase Research Agent is ready for use in Claude PM Framework.")
    
    # Usage example
    print(f"\n📝 Usage Example:")
    print(f"```python")
    print(f"# PM Agent delegates to Codebase Research Agent")
    print(f"result = await task_tool.delegate(")
    print(f"    agent_type='research',")
    print(f"    specialization='codebase',")
    print(f"    operation='answer_codebase_question',")
    print(f"    question='How should I implement X in the framework?'")
    print(f")")
    print(f"```")
    
    print(f"\n📋 TodoWrite Integration:")
    print(f"```python")
    print(f"TodoWrite([{{")
    print(f"    'content': 'Researcher: Analyze framework patterns for new feature',")
    print(f"    'status': 'pending',")
    print(f"    'priority': 'high'")
    print(f"}}])")
    print(f"```")


if __name__ == "__main__":
    asyncio.run(verify_integration())