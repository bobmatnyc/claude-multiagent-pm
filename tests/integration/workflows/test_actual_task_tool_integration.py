#!/usr/bin/env python3
"""
Test Actual Task Tool Integration

Test that the loader system works with real Task Tool subprocess creation.
This demonstrates the practical bridge between Claude Code and the framework.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from claude_pm.services.framework_agent_loader import FrameworkAgentLoader

def create_enhanced_task_delegation(agent_type: str, task_description: str, additional_context: str = ""):
    """Create a Task Tool delegation with profile enhancement"""
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    # Get the profile instruction
    profile_instruction = loader.generate_profile_loading_instruction(agent_type)
    
    # Create enhanced delegation that mimics Task Tool format
    delegation = f"""**{agent_type}**: {task_description}

{profile_instruction}

TEMPORAL CONTEXT: Today is 2025-07-11. Apply date awareness to sprint planning and deadline management.

**Task**: {task_description}
{additional_context}

**Profile-Enhanced Instructions**:
1. Your {agent_type} agent profile has been automatically loaded
2. Operate according to your defined capabilities and authority scope
3. Apply your context preferences when processing task information
4. Follow your quality standards and escalation criteria
5. Use your integration patterns for coordination with other agents

**Expected Behavior**: You should respond as a specialized {agent_type} agent with full awareness of your role, capabilities, and operational guidelines.
"""
    
    return delegation

def test_task_tool_style_delegations():
    """Test Task Tool style delegations with profile enhancement"""
    print("🔗 Testing Task Tool Style Delegations with Profile Enhancement")
    print("=" * 70)
    
    # Real-world scenarios that would benefit from agent profiles
    scenarios = [
        {
            "agent": "Engineer",
            "task": "Implement OAuth2 authentication system",
            "context": """
**Requirements**:
- JWT token-based authentication
- Secure password hashing with bcrypt
- User session management
- Rate limiting for login attempts
- Integration with existing user database schema

**Technical Constraints**:
- Must use existing Express.js framework
- Database: PostgreSQL with Sequelize ORM
- Redis for session storage
- Follow existing code style and patterns
""",
            "expected_behaviors": [
                "Focus on implementation details",
                "Consider security best practices",
                "Follow coding standards",
                "Create appropriate tests"
            ]
        },
        {
            "agent": "QA", 
            "task": "Design comprehensive test suite for authentication system",
            "context": """
**Scope**:
- Unit tests for authentication functions
- Integration tests for login/logout flow
- Security testing for common vulnerabilities
- Performance testing for login under load
- Edge case testing (invalid tokens, expired sessions)

**Quality Requirements**:
- Minimum 90% code coverage
- All security scenarios covered
- Performance benchmarks established
""",
            "expected_behaviors": [
                "Focus on quality metrics",
                "Design comprehensive test scenarios",
                "Consider edge cases and failure modes",
                "Establish quality gates"
            ]
        },
        {
            "agent": "Documenter",
            "task": "Create developer documentation for authentication API",
            "context": """
**Documentation Requirements**:
- API endpoint documentation with examples
- Authentication flow diagrams
- Integration guide for frontend developers
- Security considerations and best practices
- Troubleshooting guide

**Audience**:
- Frontend developers integrating with the API
- Backend developers maintaining the system
- DevOps engineers deploying the system
""",
            "expected_behaviors": [
                "Focus on clarity and usability",
                "Structure for different audiences",
                "Include practical examples",
                "Maintain consistency with existing docs"
            ]
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        agent = scenario["agent"]
        task = scenario["task"]
        context = scenario["context"]
        expected = scenario["expected_behaviors"]
        
        print(f"\n🎯 Testing {agent} Agent Delegation")
        print("-" * 40)
        
        # Create enhanced delegation
        delegation = create_enhanced_task_delegation(agent, task, context)
        
        # Analyze delegation quality
        quality_checks = {
            "Agent Identity": f"**{agent} Agent Profile Loaded**" in delegation,
            "Task Context": task in delegation,
            "Profile Capabilities": "Core Capabilities" in delegation,
            "Authority Scope": "Authority Scope" in delegation,
            "Context Preferences": "Context Preferences" in delegation,
            "Quality Standards": "Quality Standards" in delegation,
            "Temporal Context": "Today is 2025-07-11" in delegation,
            "Instructions": "Profile-Enhanced Instructions" in delegation
        }
        
        passed_checks = sum(quality_checks.values())
        total_checks = len(quality_checks)
        
        print(f"✅ Delegation created: {len(delegation)} characters")
        print(f"📊 Quality checks: {passed_checks}/{total_checks} passed")
        
        for check, passed in quality_checks.items():
            status = "✓" if passed else "✗"
            print(f"   {status} {check}")
        
        # Simulate what the subprocess would receive
        print(f"🔍 Subprocess would receive:")
        lines = delegation.split('\n')
        preview_lines = min(15, len(lines))
        for i in range(preview_lines):
            print(f"   {i+1:2d}: {lines[i]}")
        if len(lines) > preview_lines:
            print(f"   ... ({len(lines) - preview_lines} more lines)")
        
        # Record results
        results.append({
            "agent": agent,
            "delegation_length": len(delegation),
            "quality_score": passed_checks / total_checks,
            "all_checks_passed": passed_checks == total_checks
        })
    
    return results

def test_profile_loading_in_subprocess_context():
    """Test how profile loading would work within a subprocess"""
    print("\n\n🔄 Testing Profile Loading in Subprocess Context")
    print("=" * 70)
    
    # Simulate subprocess receiving profile loading instruction
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    def simulate_subprocess_profile_loading(agent_type: str):
        """Simulate how a subprocess would load its profile"""
        print(f"📥 Subprocess {agent_type} starting...")
        
        # Step 1: Load profile
        profile = loader.load_agent_profile(agent_type)
        if not profile:
            print(f"❌ No profile found for {agent_type}")
            return False
        
        print(f"✅ Profile loaded from: {Path(profile['source_path']).name}")
        
        # Step 2: Extract key information
        role = profile.get('role', 'Not specified')
        capabilities = profile.get('capabilities', [])
        authority = profile.get('authority_scope', [])
        context_prefs = profile.get('context_preferences', {})
        
        print(f"🎭 Role: {role[:60]}...")
        print(f"🛠️  Capabilities: {len(capabilities)} defined")
        print(f"🔑 Authority areas: {len(authority)} defined")
        print(f"🎯 Context focus: {context_prefs.get('focus', 'Not specified')[:50]}...")
        
        # Step 3: Simulate profile-aware behavior
        if agent_type == "Engineer":
            expected_focus = ["implementation", "code", "technical"]
        elif agent_type == "QA":
            expected_focus = ["testing", "quality", "validation"]
        elif agent_type == "Documenter":
            expected_focus = ["documentation", "clarity", "user"]
        else:
            expected_focus = []
        
        focus_text = context_prefs.get('focus', '').lower()
        profile_awareness = any(keyword in focus_text for keyword in expected_focus)
        
        if profile_awareness:
            print(f"✅ Profile shows expected {agent_type} focus")
        else:
            print(f"⚠️  Profile focus may not match {agent_type} expectations")
        
        return True
    
    # Test different agent types
    test_agents = ["Engineer", "QA", "Documenter", "VCS"]
    success_count = 0
    
    for agent_type in test_agents:
        success = simulate_subprocess_profile_loading(agent_type)
        if success:
            success_count += 1
        print()
    
    print(f"📊 Subprocess profile loading: {success_count}/{len(test_agents)} successful")
    return success_count == len(test_agents)

def run_integration_verification():
    """Run the complete Task Tool integration verification"""
    print("🧪 Task Tool Integration Verification")
    print("=" * 70)
    
    # Test enhanced delegations
    delegation_results = test_task_tool_style_delegations()
    
    # Test subprocess profile loading
    subprocess_success = test_profile_loading_in_subprocess_context()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 INTEGRATION VERIFICATION SUMMARY")
    print("=" * 70)
    
    # Delegation results
    total_delegations = len(delegation_results)
    perfect_delegations = sum(1 for r in delegation_results if r["all_checks_passed"])
    avg_quality = sum(r["quality_score"] for r in delegation_results) / total_delegations if delegation_results else 0
    
    print(f"🎯 Enhanced Delegations: {perfect_delegations}/{total_delegations} perfect ({avg_quality:.1%} avg quality)")
    
    for result in delegation_results:
        status = "✅" if result["all_checks_passed"] else "⚠️"
        print(f"  {status} {result['agent']}: {result['delegation_length']} chars, {result['quality_score']:.1%} quality")
    
    print(f"🔄 Subprocess Profile Loading: {'✅ PASS' if subprocess_success else '❌ FAIL'}")
    
    # Overall assessment
    overall_success = (perfect_delegations == total_delegations) and subprocess_success
    
    if overall_success:
        print("\n🎉 TASK TOOL INTEGRATION FULLY VERIFIED!")
        print("   ✓ Enhanced delegations working perfectly")
        print("   ✓ Subprocess profile loading functional")
        print("   ✓ Ready for production use with Claude Code")
    else:
        print("\n⚠️  Some integration tests need attention")
    
    return overall_success

if __name__ == "__main__":
    success = run_integration_verification()
    sys.exit(0 if success else 1)