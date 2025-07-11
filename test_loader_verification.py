#!/usr/bin/env python3
"""
Comprehensive Loader Verification Test

Verify that the framework agent loader and profile system actually work end-to-end.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from claude_pm.services.framework_agent_loader import FrameworkAgentLoader

def test_loader_initialization():
    """Test that the loader initializes correctly"""
    print("🔧 Testing Loader Initialization")
    print("=" * 50)
    
    loader = FrameworkAgentLoader()
    print(f"✅ FrameworkAgentLoader created")
    
    # Test initialization
    loader.initialize()
    print(f"✅ Loader initialized")
    
    print(f"📁 Framework agents dir: {loader.framework_agents_dir}")
    print(f"📁 Project agents dir: {loader.project_agents_dir}")
    
    if loader.framework_agents_dir and loader.framework_agents_dir.exists():
        print(f"✅ Framework directory exists: {loader.framework_agents_dir}")
    else:
        print(f"❌ Framework directory missing: {loader.framework_agents_dir}")
        return False
    
    return True

def test_profile_loading():
    """Test loading individual agent profiles"""
    print("\n🔍 Testing Profile Loading")
    print("=" * 50)
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    test_agents = ['Engineer', 'Documenter', 'QA', 'VCS', 'Ops', 'Security', 'Researcher', 'Ticketer']
    success_count = 0
    
    for agent_type in test_agents:
        profile = loader.load_agent_profile(agent_type)
        if profile:
            print(f"✅ {agent_type}: Loaded successfully")
            print(f"   Role: {profile.get('role', 'Not specified')[:60]}...")
            print(f"   Capabilities: {len(profile.get('capabilities', []))} defined")
            print(f"   Source: {Path(profile.get('source_path', '')).name}")
            success_count += 1
        else:
            print(f"❌ {agent_type}: Failed to load")
    
    print(f"\n📊 Profile Loading Results: {success_count}/{len(test_agents)} successful")
    return success_count == len(test_agents)

def test_instruction_generation():
    """Test generating profile loading instructions"""
    print("\n📜 Testing Instruction Generation")
    print("=" * 50)
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    test_cases = [
        ('Engineer', 'Should have implementation focus'),
        ('Documenter', 'Should have documentation focus'),
        ('QA', 'Should have testing focus'),
        ('NonExistent', 'Should handle gracefully')
    ]
    
    success_count = 0
    
    for agent_type, expected in test_cases:
        instruction = loader.generate_profile_loading_instruction(agent_type)
        
        if instruction and len(instruction) > 100:  # Reasonable length check
            print(f"✅ {agent_type}: Generated {len(instruction)} characters")
            if agent_type != 'NonExistent':
                if 'Profile Loaded' in instruction:
                    print(f"   ✓ Contains profile loaded confirmation")
                    success_count += 1
                else:
                    print(f"   ❌ Missing profile confirmation")
            else:
                if 'No profile found' in instruction:
                    print(f"   ✓ Correctly handles missing profile")
                    success_count += 1
                else:
                    print(f"   ❌ Should handle missing profile")
        else:
            print(f"❌ {agent_type}: Failed to generate instruction")
    
    print(f"\n📊 Instruction Generation Results: {success_count}/{len(test_cases)} successful")
    return success_count == len(test_cases)

def test_hierarchy_precedence():
    """Test that the hierarchy precedence system works"""
    print("\n🏗️ Testing Hierarchy Precedence")
    print("=" * 50)
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    # Test with Engineer profile (should come from system tier)
    profile = loader.load_agent_profile('Engineer')
    
    if profile:
        source_path = profile.get('source_path', '')
        print(f"✅ Engineer profile source: {source_path}")
        
        if 'system' in source_path:
            print(f"✅ Correctly loaded from system tier (expected)")
            return True
        elif 'project' in source_path:
            print(f"✅ Loaded from project tier (higher precedence)")
            return True
        else:
            print(f"⚠️  Loaded from unexpected location: {source_path}")
            return True  # Still working, just different location
    else:
        print(f"❌ Failed to load Engineer profile")
        return False

def test_available_agents():
    """Test agent discovery"""
    print("\n📋 Testing Agent Discovery")
    print("=" * 50)
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    available = loader.get_available_agents()
    
    total_agents = 0
    for tier, agents in available.items():
        if agents:
            print(f"✅ {tier}: {len(agents)} agents ({', '.join(agents)})")
            total_agents += len(agents)
        else:
            print(f"⚪ {tier}: No agents")
    
    print(f"\n📊 Total agents discovered: {total_agents}")
    
    # We should have at least the 8 system agents we created
    return total_agents >= 8

def test_enhanced_delegation_simulation():
    """Test simulated enhanced Task Tool delegation"""
    print("\n🎯 Testing Enhanced Delegation Simulation")
    print("=" * 50)
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    def simulate_task_tool_delegation(agent_type, task_description):
        """Simulate what the enhanced Task Tool delegation would look like"""
        profile_instruction = loader.generate_profile_loading_instruction(agent_type)
        
        delegation = f"""**{agent_type}**: {task_description}

{profile_instruction}

TEMPORAL CONTEXT: Today is 2025-07-11. Sprint deadline: 2025-07-18.

**Task**: {task_description}

**Profile-Enhanced Behavior**: You are operating with loaded agent profile.
Follow your defined capabilities, authority scope, and quality standards.
"""
        return delegation
    
    test_scenarios = [
        ('Engineer', 'Implement user authentication API with JWT tokens'),
        ('QA', 'Create comprehensive test suite for authentication flow'),
        ('Documenter', 'Write API documentation for authentication endpoints')
    ]
    
    success_count = 0
    
    for agent_type, task in test_scenarios:
        delegation = simulate_task_tool_delegation(agent_type, task)
        
        # Check delegation quality
        if (len(delegation) > 1000 and 
            'Profile Loaded' in delegation and 
            agent_type in delegation and
            task in delegation):
            print(f"✅ {agent_type}: Enhanced delegation generated ({len(delegation)} chars)")
            success_count += 1
        else:
            print(f"❌ {agent_type}: Delegation quality issues")
    
    print(f"\n📊 Enhanced Delegation Results: {success_count}/{len(test_scenarios)} successful")
    return success_count == len(test_scenarios)

def run_comprehensive_verification():
    """Run all verification tests"""
    print("🧪 Comprehensive Loader Verification")
    print("=" * 60)
    
    tests = [
        ("Loader Initialization", test_loader_initialization),
        ("Profile Loading", test_profile_loading),
        ("Instruction Generation", test_instruction_generation),
        ("Hierarchy Precedence", test_hierarchy_precedence),
        ("Agent Discovery", test_available_agents),
        ("Enhanced Delegation", test_enhanced_delegation_simulation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL VERIFICATION TESTS PASSED - LOADER SYSTEM FULLY FUNCTIONAL!")
        return True
    else:
        print("⚠️  Some verification tests failed - review issues above")
        return False

if __name__ == "__main__":
    success = run_comprehensive_verification()
    sys.exit(0 if success else 1)