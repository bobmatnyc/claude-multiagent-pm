#!/usr/bin/env python3
"""
Test Profile-Enhanced Subprocess Behavior

Demonstrates the integration between agent profiles and Task Tool subprocess delegation.
Shows how profiles enhance subprocess context with agent-specific capabilities and knowledge.
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_profile_loading():
    """Test basic profile loading functionality."""
    print("\n" + "="*80)
    print("🧪 TEST 1: Basic Profile Loading")
    print("="*80)
    
    try:
        from claude_pm.services.agent_profile_loader import AgentProfileLoader
        
        # Initialize loader
        loader = AgentProfileLoader(working_directory=Path.cwd())
        await loader.initialize()
        
        # Test loading engineer profile
        engineer_profile = await loader.load_profile('engineer')
        
        if engineer_profile:
            print(f"✅ Loaded Engineer Profile:")
            print(f"   - Name: {engineer_profile.name}")
            print(f"   - Role: {engineer_profile.role}")
            print(f"   - Tier: {engineer_profile.tier.value}")
            print(f"   - Capabilities: {len(engineer_profile.capabilities)}")
            print(f"   - Authority Scope: {len(engineer_profile.authority_scope)}")
            print(f"   - Profile Path: {engineer_profile.path}")
            
            # Show first few capabilities
            if engineer_profile.capabilities:
                print(f"   - Top Capabilities:")
                for i, cap in enumerate(engineer_profile.capabilities[:3], 1):
                    print(f"     {i}. {cap}")
                    
        else:
            print("❌ No engineer profile found")
            
        return engineer_profile is not None
        
    except Exception as e:
        print(f"❌ Profile loading test failed: {e}")
        return False

async def test_profile_hierarchy():
    """Test three-tier profile hierarchy."""
    print("\n" + "="*80)
    print("🧪 TEST 2: Profile Hierarchy Detection")
    print("="*80)
    
    try:
        from claude_pm.services.agent_profile_loader import AgentProfileLoader
        
        loader = AgentProfileLoader(working_directory=Path.cwd())
        await loader.initialize()
        
        # List available profiles by tier
        available_profiles = await loader.list_available_profiles()
        
        print("📊 Available Profiles by Tier:")
        for tier, profiles in available_profiles.items():
            print(f"   {tier.value.upper()} ({len(profiles)} profiles):")
            for profile_name in profiles[:5]:  # Show first 5
                print(f"     - {profile_name}")
            if len(profiles) > 5:
                print(f"     ... and {len(profiles) - 5} more")
                
        # Test hierarchy for specific agent
        test_agent = 'engineer'
        hierarchy = await loader.get_profile_hierarchy(test_agent)
        
        print(f"\n🔍 Profile Hierarchy for '{test_agent}':")
        for profile in hierarchy:
            print(f"   {profile.tier.value}: {profile.path}")
            
        return len(hierarchy) > 0
        
    except Exception as e:
        print(f"❌ Profile hierarchy test failed: {e}")
        return False

async def test_task_tool_integration():
    """Test Task Tool integration with profile enhancement."""
    print("\n" + "="*80)
    print("🧪 TEST 3: Task Tool Profile Integration")
    print("="*80)
    
    try:
        from claude_pm.services.task_tool_profile_integration import TaskToolProfileIntegrator
        
        # Initialize integrator
        integrator = TaskToolProfileIntegrator(working_directory=Path.cwd())
        await integrator.initialize()
        
        # Test enhanced delegation
        task_description = "Implement user authentication system with JWT tokens"
        technical_context = "Create secure login/logout with password hashing and token validation"
        
        enhanced_delegation = await integrator.enhance_task_delegation(
            'engineer',
            task_description, 
            technical_context,
            {
                'priority': 'high',
                'deadline': '2025-07-15',
                'dependencies': ['database setup', 'API framework']
            }
        )
        
        print("✅ Enhanced Task Tool Delegation Generated:")
        print("-" * 60)
        print(enhanced_delegation)
        print("-" * 60)
        
        # Test profile summary
        profile_summary = await integrator.get_profile_summary('engineer')
        
        if profile_summary:
            print(f"\n📋 Profile Summary:")
            print(f"   Agent: {profile_summary['agent_name']} ({profile_summary['role']})")
            print(f"   Tier: {profile_summary['tier']}")
            print(f"   Capabilities: {profile_summary['capabilities_count']}")
            print(f"   Authority Items: {profile_summary['authority_scope_count']}")
            print(f"   Escalation Triggers: {profile_summary['escalation_triggers_count']}")
            print(f"   Coordination Protocols: {profile_summary['coordination_protocols']}")
            
        return len(enhanced_delegation) > 500  # Should be substantial
        
    except Exception as e:
        print(f"❌ Task Tool integration test failed: {e}")
        return False

async def test_multi_agent_coordination():
    """Test multi-agent coordination with profiles."""
    print("\n" + "="*80)
    print("🧪 TEST 4: Multi-Agent Coordination")
    print("="*80)
    
    try:
        from claude_pm.services.task_tool_profile_integration import TaskToolProfileIntegrator
        
        integrator = TaskToolProfileIntegrator(working_directory=Path.cwd())
        await integrator.initialize()
        
        # Define coordinated tasks
        agents_and_tasks = {
            'documentation': 'Create API documentation for authentication system',
            'engineer': 'Implement JWT authentication with secure password hashing',
            'qa': 'Create comprehensive test suite for authentication flows'
        }
        
        coordination_context = """
Multi-agent authentication system implementation requiring:
- Coordinated API design and implementation
- Comprehensive documentation and testing
- Security best practices throughout
        """
        
        coordinated_delegations = await integrator.create_multi_agent_coordination(
            agents_and_tasks,
            coordination_context
        )
        
        print("✅ Multi-Agent Coordinated Delegations:")
        for agent_name, delegation in coordinated_delegations.items():
            print(f"\n📄 {agent_name.upper()} AGENT DELEGATION:")
            print("-" * 40)
            # Show first 300 characters
            preview = delegation[:300] + "..." if len(delegation) > 300 else delegation
            print(preview)
            
        return len(coordinated_delegations) == len(agents_and_tasks)
        
    except Exception as e:
        print(f"❌ Multi-agent coordination test failed: {e}")
        return False

async def test_convenience_functions():
    """Test convenience functions for common delegation patterns."""
    print("\n" + "="*80)
    print("🧪 TEST 5: Convenience Functions")
    print("="*80)
    
    try:
        from claude_pm.services.task_tool_profile_integration import (
            enhance_engineer_delegation,
            enhance_documentation_delegation,
            enhance_qa_delegation
        )
        
        # Test engineer delegation
        engineer_task = await enhance_engineer_delegation(
            "Optimize database query performance",
            "Analyze slow queries and implement indexing strategies"
        )
        
        # Test documentation delegation
        doc_task = await enhance_documentation_delegation(
            "Update API documentation for new endpoints",
            "Include examples, error codes, and authentication requirements"
        )
        
        # Test QA delegation
        qa_task = await enhance_qa_delegation(
            "Create performance test suite",
            "Test API response times under load with 1000 concurrent users"
        )
        
        print("✅ Convenience Functions Generated:")
        print(f"   Engineer Delegation: {len(engineer_task)} characters")
        print(f"   Documentation Delegation: {len(doc_task)} characters")
        print(f"   QA Delegation: {len(qa_task)} characters")
        
        # Show engineer delegation sample
        print(f"\n📄 Engineer Delegation Sample:")
        print("-" * 40)
        print(engineer_task[:200] + "...")
        
        return all(len(task) > 200 for task in [engineer_task, doc_task, qa_task])
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {e}")
        return False

async def test_deployment_integration():
    """Test integration with deployment system."""
    print("\n" + "="*80)
    print("🧪 TEST 6: Deployment Integration")
    print("="*80)
    
    try:
        from claude_pm.services.agent_profile_loader import AgentProfileLoader
        
        loader = AgentProfileLoader(working_directory=Path.cwd())
        await loader.initialize()
        
        # Test deployment structure creation
        structure_results = await loader.create_profile_deployment_structure()
        
        print("✅ Deployment Structure Creation:")
        for component, success in structure_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {component}")
            
        # Test profile deployment
        deployment_results = await loader.deploy_system_profiles()
        
        print(f"\n📦 Profile Deployment Results:")
        deployed_count = sum(1 for success in deployment_results.values() if success)
        total_count = len(deployment_results)
        
        print(f"   Deployed: {deployed_count}/{total_count} profiles")
        
        for profile_name, deployed in deployment_results.items():
            status = "✅ Deployed" if deployed else "ℹ️  Already exists"
            print(f"   {status}: {profile_name}")
            
        return len(structure_results) > 0
        
    except Exception as e:
        print(f"❌ Deployment integration test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive test suite."""
    print("🚀 PROFILE-ENHANCED SUBPROCESS BEHAVIOR TEST SUITE")
    print("Testing Task Tool integration with agent profiles")
    print(f"Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Profile Loading", test_profile_loading),
        ("Profile Hierarchy", test_profile_hierarchy), 
        ("Task Tool Integration", test_task_tool_integration),
        ("Multi-Agent Coordination", test_multi_agent_coordination),
        ("Convenience Functions", test_convenience_functions),
        ("Deployment Integration", test_deployment_integration)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results[test_name] = result
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            test_results[test_name] = False
            
    # Summary report
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        
    print("-" * 80)
    print(f"Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Profile-enhanced subprocess system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check individual test output for details.")
        
    # Save results
    results_file = Path("profile_enhancement_test_results.json")
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "test_results": test_results,
        "summary": {
            "passed": passed,
            "total": total,
            "success_rate": passed/total*100
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
        
    print(f"📁 Results saved to: {results_file}")
    
    return test_results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())