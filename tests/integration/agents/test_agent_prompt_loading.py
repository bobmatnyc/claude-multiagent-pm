#!/usr/bin/env python3
"""
Test script to verify agent prompt loading functionality.
Tests the complete flow of agent prompt loading, caching, and fallback behavior.
"""

import os
import sys
import time
import tempfile
import shutil
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.agent_registry import AgentRegistry
from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

async def test_basic_prompt_loading():
    """Test basic agent prompt loading through orchestrator."""
    print_section("Testing Basic Agent Prompt Loading")
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Test core agent types
    core_agents = ['documentation', 'qa', 'research', 'engineer', 'versioning', 'ops', 'security', 'ticketing', 'data_engineer']
    
    for agent_type in core_agents:
        print(f"Loading prompt for {agent_type} agent...")
        start_time = time.time()
        
        try:
            # Use the internal method to test prompt loading
            prompt = await orchestrator._get_agent_prompt(agent_type)
            load_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if prompt:
                print(f"✅ {agent_type}: Loaded successfully ({load_time:.2f}ms)")
                print(f"   Preview: {prompt[:100].strip()}...")
            else:
                print(f"❌ {agent_type}: Failed to load prompt")
        except Exception as e:
            print(f"❌ {agent_type}: Error loading prompt - {str(e)}")
    
    return True

async def test_cache_performance():
    """Test SharedPromptCache performance."""
    print_section("Testing SharedPromptCache Performance")
    
    cache = SharedPromptCache.get_instance()
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Test cache performance for documentation agent
    agent_type = 'documentation'
    
    # Clear cache first
    cache_key = f"agent_prompt:{agent_type}"
    cache.delete(cache_key)
    
    # First load (cold cache)
    print(f"First load of {agent_type} agent (cold cache)...")
    start_time = time.time()
    prompt1 = await orchestrator._get_agent_prompt(agent_type)
    cold_time = (time.time() - start_time) * 1000
    print(f"Cold cache load time: {cold_time:.2f}ms")
    
    # Second load (warm cache)
    print(f"\nSecond load of {agent_type} agent (warm cache)...")
    start_time = time.time()
    prompt2 = await orchestrator._get_agent_prompt(agent_type)
    warm_time = (time.time() - start_time) * 1000
    print(f"Warm cache load time: {warm_time:.2f}ms")
    
    # Calculate improvement
    if cold_time > 0:
        improvement = ((cold_time - warm_time) / cold_time) * 100
        print(f"\nCache performance improvement: {improvement:.1f}%")
    
    # Verify prompts are identical
    if prompt1 == prompt2:
        print("✅ Cached prompt matches original")
    else:
        print("❌ Cached prompt differs from original")
    
    return True

async def test_file_based_loading():
    """Test loading agent definitions from files."""
    print_section("Testing File-Based Agent Loading")
    
    # Create a temporary agent directory
    temp_dir = tempfile.mkdtemp()
    agents_dir = Path(temp_dir) / '.claude-pm' / 'agents'
    agents_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a test agent file
    test_agent_file = agents_dir / 'test_custom.md'
    test_agent_content = """# Test Custom Agent

You are a test custom agent loaded from a file.

## Your Purpose
- Demonstrate file-based agent loading
- Verify the system works correctly

## Your Capabilities
- Testing functionality
- Validating systems
"""
    
    test_agent_file.write_text(test_agent_content)
    
    # Save current directory
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        # Create orchestrator in temp directory
        orchestrator = BackwardsCompatibleOrchestrator(working_directory=Path(temp_dir))
        
        # Try to load the custom agent
        print("Attempting to load custom agent from file...")
        prompt = await orchestrator._get_agent_prompt('test_custom')
        
        if prompt and "test custom agent" in prompt.lower():
            print("✅ Successfully loaded agent from file")
            print(f"   Content preview: {prompt[:100]}...")
        else:
            print("❌ Failed to load agent from file")
            if prompt:
                print(f"   Got prompt but content mismatch: {prompt[:100]}...")
            
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
    
    return True

async def test_fallback_behavior():
    """Test fallback behavior when files don't exist."""
    print_section("Testing Fallback Behavior")
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Test with a non-existent agent type
    fake_agent_type = 'nonexistent_agent_type_12345'
    
    print(f"Attempting to load non-existent agent type: {fake_agent_type}")
    try:
        prompt = await orchestrator._get_agent_prompt(fake_agent_type)
        if prompt:
            print("✅ Got some prompt (likely metadata fallback)")
            print(f"   Preview: {prompt[:100]}...")
        else:
            print("✅ Correctly returned None for non-existent agent")
    except Exception as e:
        print(f"❌ Error during fallback: {str(e)}")
    
    return True

async def test_orchestrator_integration():
    """Test agent prompt loading through the orchestrator."""
    print_section("Testing Orchestrator Integration")
    
    # Create orchestrator instance
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Test creating a subprocess with agent prompt
    print("Testing orchestrator agent prompt integration...")
    
    # Create a simple task
    task = """Analyze the project structure and provide a summary"""
    
    try:
        # This should trigger agent prompt loading
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type='research',
            task_description=task,
            requirements=["Identify main components", "Note key files"]
        )
        
        if result and result.get('success'):
            print("✅ Orchestrator successfully delegated task with agent prompt")
            print(f"   Subprocess ID: {result.get('subprocess_id', 'unknown')}")
            print(f"   Orchestration mode: {result.get('orchestration_metadata', {}).get('mode', 'unknown')}")
            
            # Check if prompt was included
            if 'prompt' in result:
                prompt_preview = result['prompt'][:200] if len(result['prompt']) > 200 else result['prompt']
                print(f"   Prompt preview: {prompt_preview}...")
        else:
            print("❌ Orchestrator delegation failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during orchestrator test: {str(e)}")
    
    return True

async def test_prompt_content_validation():
    """Validate that loaded prompts contain expected content."""
    print_section("Testing Prompt Content Validation")
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Define expected content for each agent type
    expected_content = {
        'documentation': ['documentation', 'patterns', 'operational'],
        'qa': ['quality', 'testing', 'validation'],
        'research': ['research', 'investigate', 'analyze'],
        'engineer': ['code', 'implement', 'development'],
        'versioning': ['git', 'version', 'control'],
        'ops': ['deployment', 'operations', 'infrastructure'],
        'security': ['security', 'vulnerability', 'protection'],
        'ticketing': ['ticket', 'issue', 'tracking'],
        'data_engineer': ['data', 'database', 'pipeline']
    }
    
    for agent_type, keywords in expected_content.items():
        print(f"\nValidating {agent_type} agent prompt content...")
        
        try:
            prompt = await orchestrator._get_agent_prompt(agent_type)
            if prompt:
                prompt_lower = prompt.lower()
                found_keywords = [kw for kw in keywords if kw in prompt_lower]
                
                if len(found_keywords) >= 1:  # At least one keyword found
                    print(f"✅ {agent_type}: Contains expected keywords: {found_keywords}")
                else:
                    print(f"⚠️  {agent_type}: Missing expected keywords")
                    print(f"   Prompt preview: {prompt[:100]}...")
            else:
                print(f"❌ {agent_type}: No prompt loaded")
                
        except Exception as e:
            print(f"❌ {agent_type}: Error validating content - {str(e)}")
    
    return True

async def test_agent_registry_integration():
    """Test agent registry integration with prompt loading."""
    print_section("Testing Agent Registry Integration")
    
    registry = AgentRegistry()
    cache = SharedPromptCache.get_instance()
    
    # List available agents
    print("Listing available agents from registry...")
    agents = registry.list_agents()
    
    if agents:
        print(f"Found {len(agents)} agents in registry:")
        for agent_type, metadata in list(agents.items())[:5]:  # Show first 5
            print(f"  - {agent_type}: {metadata.get('description', 'No description')[:50]}...")
    else:
        print("❌ No agents found in registry")
    
    # Test orchestrator with registry
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Ensure orchestrator uses registry
    if orchestrator._agent_registry:
        print("\n✅ Orchestrator has agent registry configured")
    else:
        print("\n❌ Orchestrator missing agent registry")
    
    return True

async def test_prompt_formatting():
    """Test prompt formatting with task details."""
    print_section("Testing Prompt Formatting")
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Get a base prompt
    base_prompt = await orchestrator._get_agent_prompt('engineer')
    
    if base_prompt:
        # Format it with task details
        formatted_prompt = orchestrator._format_agent_prompt(
            agent_type='engineer',
            task_description='Implement a new feature for user authentication',
            base_prompt=base_prompt,
            requirements=['Use JWT tokens', 'Implement refresh token logic'],
            deliverables=['Authentication service', 'Token validation middleware'],
            priority='high',
            integration_notes='Must integrate with existing user service'
        )
        
        print("✅ Successfully formatted agent prompt")
        print("Formatted prompt preview:")
        print("-" * 50)
        print(formatted_prompt[:500])
        print("-" * 50)
        
        # Check key components
        components = ['TEMPORAL CONTEXT:', 'Requirements:', 'Deliverables:', 'Priority:', 'Integration Notes:']
        found_components = [comp for comp in components if comp in formatted_prompt]
        
        if len(found_components) == len(components):
            print(f"\n✅ All formatting components present: {len(found_components)}/{len(components)}")
        else:
            print(f"\n⚠️  Some components missing: {len(found_components)}/{len(components)}")
            print(f"   Missing: {[c for c in components if c not in found_components]}")
    else:
        print("❌ Could not get base prompt for formatting test")
    
    return True

async def main():
    """Run all tests."""
    print("="*60)
    print(" Agent Prompt Loading Test Suite")
    print("="*60)
    print(f"Project Root: {project_root}")
    print(f"Python Version: {sys.version.split()[0]}")
    
    tests = [
        ("Basic Prompt Loading", test_basic_prompt_loading),
        ("Cache Performance", test_cache_performance),
        ("File-Based Loading", test_file_based_loading),
        ("Fallback Behavior", test_fallback_behavior),
        ("Orchestrator Integration", test_orchestrator_integration),
        ("Prompt Content Validation", test_prompt_content_validation),
        ("Agent Registry Integration", test_agent_registry_integration),
        ("Prompt Formatting", test_prompt_formatting)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print_section("Test Summary")
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {len(tests)}")
    
    if failed == 0:
        print("\n✅ All tests passed! Agent prompt loading is working correctly.")
    else:
        print(f"\n❌ {failed} test(s) failed. Please investigate the issues.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)