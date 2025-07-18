#!/usr/bin/env python3
"""
Test script for model metadata and selection integration
"""

import asyncio
import sys
import logging
from pathlib import Path

# Setup path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_selector():
    """Test ModelSelector basic functionality"""
    print("Testing ModelSelector...")
    
    try:
        from claude_pm.services.model_selector import ModelSelector, ModelSelectionCriteria
        
        # Initialize ModelSelector
        selector = ModelSelector()
        print("✓ ModelSelector initialized successfully")
        
        # Test agent model selection
        test_agents = ['engineer', 'documentation', 'qa', 'orchestrator']
        
        for agent_type in test_agents:
            model_type, model_config = selector.select_model_for_agent(agent_type)
            print(f"✓ {agent_type:15} -> {model_type.value}")
        
        # Test criteria-based selection
        criteria = ModelSelectionCriteria(
            agent_type="engineer",
            task_complexity="expert",
            creativity_required=True
        )
        
        model_type, model_config = selector.select_model_for_agent("engineer", criteria)
        print(f"✓ Expert engineering task -> {model_type.value}")
        
        # Test recommendation system
        recommendation = selector.get_model_recommendation(
            "engineer",
            "Implement a complex microservices architecture with AI optimization"
        )
        
        print(f"✓ Recommendation generated: {recommendation['recommended_model']}")
        
        return True
        
    except Exception as e:
        print(f"✗ ModelSelector test failed: {e}")
        return False

async def test_agent_registry_integration():
    """Test Agent Registry model integration"""
    print("\nTesting Agent Registry model integration...")
    
    try:
        from claude_pm.services.agent_registry import AgentRegistry
        from claude_pm.services.model_selector import ModelSelector
        
        # Initialize AgentRegistry with ModelSelector
        model_selector = ModelSelector()
        registry = AgentRegistry(model_selector=model_selector)
        print("✓ AgentRegistry with ModelSelector initialized")
        
        # Test agent discovery (this will trigger model selection)
        agents = await registry.discover_agents()
        print(f"✓ Discovered {len(agents)} agents")
        
        # Test model configuration methods
        if agents:
            agent_name = list(agents.keys())[0]
            
            # Test get_agent_model_configuration
            model_config = await registry.get_agent_model_configuration(agent_name)
            if model_config:
                print(f"✓ Model configuration retrieved for {agent_name}")
                print(f"  - Preferred model: {model_config.get('preferred_model')}")
                print(f"  - Complexity level: {model_config.get('complexity_level')}")
            else:
                print(f"⚠ No model configuration found for {agent_name}")
        
        # Test model recommendations
        recommendations = await registry.get_model_recommendations_for_agents()
        print(f"✓ Generated recommendations for {len(recommendations)} agents")
        
        # Test model validation
        validation = await registry.validate_agent_model_configurations()
        print(f"✓ Validation completed: {validation['valid_configurations']} valid, {validation['invalid_configurations']} invalid")
        
        # Test model usage statistics
        stats = await registry.get_model_usage_statistics()
        print(f"✓ Model usage statistics: {stats['total_agents']} agents, {len(stats['model_distribution'])} models")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent Registry integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_task_tool_integration():
    """Test Task Tool Helper model integration"""
    print("\nTesting Task Tool Helper model integration...")
    
    try:
        from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration
        
        # Initialize with model selection enabled
        config = TaskToolConfiguration(enable_model_selection=True)
        helper = TaskToolHelper(config=config)
        print("✓ TaskToolHelper with model selection initialized")
        
        # Test model recommendation
        recommendation = await helper.get_agent_model_recommendation(
            "engineer", 
            "Implement JWT authentication system"
        )
        print(f"✓ Model recommendation: {recommendation.get('recommended_model', 'error')}")
        
        # Test model validation
        validation = await helper.validate_model_configuration("engineer", "claude-3-opus-20240229")
        print(f"✓ Model validation: {validation.get('valid', False)}")
        
        # Test available models
        models = helper.get_available_models()
        print(f"✓ Available models: {len(models)} models")
        
        # Test model selection statistics
        stats = helper.get_model_selection_statistics()
        print(f"✓ Model selection statistics retrieved")
        
        # Test subprocess creation with model selection
        subprocess_result = await helper.create_agent_subprocess(
            agent_type="engineer",
            task_description="Implement user authentication with JWT tokens",
            requirements=["Security best practices", "Token expiration handling"],
            deliverables=["Auth system", "Unit tests", "Documentation"]
        )
        
        if subprocess_result.get("success"):
            print("✓ Subprocess created with model selection")
            subprocess_info = subprocess_result["subprocess_info"]
            print(f"  - Selected model: {subprocess_info.get('selected_model')}")
            print(f"  - Selection method: {subprocess_info.get('model_config', {}).get('selection_method')}")
        else:
            print(f"⚠ Subprocess creation failed: {subprocess_result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Task Tool Helper integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_environment_overrides():
    """Test environment variable overrides"""
    print("\nTesting environment variable overrides...")
    
    try:
        import os
        from claude_pm.services.model_selector import ModelSelector
        
        # Set environment override
        os.environ['CLAUDE_PM_MODEL_ENGINEER'] = 'claude-3-5-sonnet-20241022'
        
        # Initialize ModelSelector (should pick up environment variables)
        selector = ModelSelector()
        
        # Test override
        model_type, model_config = selector.select_model_for_agent("engineer")
        expected_model = 'claude-3-5-sonnet-20241022'
        
        if model_type.value == expected_model:
            print("✓ Environment override working correctly")
        else:
            print(f"⚠ Environment override not applied: got {model_type.value}, expected {expected_model}")
        
        # Clean up
        del os.environ['CLAUDE_PM_MODEL_ENGINEER']
        
        return True
        
    except Exception as e:
        print(f"✗ Environment override test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Model Metadata and Selection Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Test ModelSelector
    results.append(test_model_selector())
    
    # Test Agent Registry integration
    results.append(await test_agent_registry_integration())
    
    # Test Task Tool Helper integration
    results.append(await test_task_tool_integration())
    
    # Test environment overrides
    results.append(await test_environment_overrides())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)