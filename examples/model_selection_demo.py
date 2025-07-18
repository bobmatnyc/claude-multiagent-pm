#!/usr/bin/env python3
"""
Model Selection Demonstration for Claude PM Framework
======================================================

This script demonstrates the comprehensive model selection capabilities
implemented in the Agent Registry and ModelSelector services.

Features demonstrated:
- Agent-specific model selection
- Task complexity analysis
- Environment variable overrides
- Model recommendations and validation
- Task Tool Helper integration
- Performance analysis
"""

import asyncio
import os
from pprint import pprint
from claude_pm.services.model_selector import ModelSelector, ModelSelectionCriteria
from claude_pm.services.agent_registry import AgentRegistry
from claude_pm.utils.task_tool_helper import TaskToolHelper
from claude_pm.services.shared_prompt_cache import SharedPromptCache


async def demonstrate_model_selection():
    """Demonstrate comprehensive model selection capabilities."""
    
    print("=" * 80)
    print("CLAUDE PM FRAMEWORK - MODEL SELECTION SYSTEM DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Initialize services
    print("🔧 Initializing Services...")
    cache = SharedPromptCache.get_instance()
    model_selector = ModelSelector()
    agent_registry = AgentRegistry(cache_service=cache, model_selector=model_selector)
    task_helper = TaskToolHelper()
    print("✅ Services initialized successfully!")
    print()
    
    # 1. Basic Model Selection Rules
    print("📋 1. DEFAULT MODEL SELECTION RULES")
    print("-" * 50)
    
    opus_agents = ['orchestrator', 'engineer', 'architecture', 'backend', 'performance', 'integration', 'machine_learning', 'data_science']
    sonnet_agents = ['documentation', 'qa', 'research', 'ops', 'security', 'data_engineer', 'ticketing', 'version_control']
    
    print("Opus Agents (Complex Implementation):")
    for agent_type in opus_agents[:4]:  # Show first 4
        model_type, config = model_selector.select_model_for_agent(agent_type)
        print(f"  {agent_type:15} → {model_type.value}")
    
    print("\nSonnet Agents (Balanced Performance):")
    for agent_type in sonnet_agents[:4]:  # Show first 4
        model_type, config = model_selector.select_model_for_agent(agent_type)
        print(f"  {agent_type:15} → {model_type.value}")
    print()
    
    # 2. Criteria-Based Selection
    print("🧠 2. INTELLIGENT CRITERIA-BASED SELECTION")
    print("-" * 50)
    
    test_scenarios = [
        {
            "name": "Expert Engineering Task",
            "agent_type": "engineer",
            "criteria": ModelSelectionCriteria(
                agent_type="engineer",
                task_complexity="expert",
                reasoning_depth_required="expert",
                creativity_required=True
            )
        },
        {
            "name": "Quick Documentation Task",
            "agent_type": "documentation",
            "criteria": ModelSelectionCriteria(
                agent_type="documentation",
                task_complexity="low",
                speed_priority=True
            )
        },
        {
            "name": "Performance Analysis",
            "agent_type": "performance",
            "criteria": ModelSelectionCriteria(
                agent_type="performance",
                task_complexity="high",
                reasoning_depth_required="deep"
            )
        }
    ]
    
    for scenario in test_scenarios:
        model_type, config = model_selector.select_model_for_agent(
            scenario["agent_type"], 
            scenario["criteria"]
        )
        print(f"Scenario: {scenario['name']}")
        print(f"  Agent: {scenario['agent_type']}")
        print(f"  Selected Model: {model_type.value}")
        print(f"  Reasoning Quality: {config.performance_profile['reasoning_quality']}")
        print(f"  Speed Tier: {config.speed_tier}")
        print()
    
    # 3. Task Description Analysis
    print("📝 3. TASK DESCRIPTION ANALYSIS")
    print("-" * 50)
    
    task_examples = [
        {
            "agent_type": "engineer",
            "task": "Implement complex microservices architecture with AI-powered optimization",
            "expected_complexity": "expert"
        },
        {
            "agent_type": "documentation",
            "task": "Update simple README file with installation instructions",
            "expected_complexity": "low"
        },
        {
            "agent_type": "qa",
            "task": "Analyze system performance and create comprehensive test strategy",
            "expected_complexity": "high"
        }
    ]
    
    for example in task_examples:
        recommendation = model_selector.get_model_recommendation(
            example["agent_type"],
            example["task"]
        )
        
        print(f"Task: {example['task'][:60]}...")
        print(f"  Agent: {example['agent_type']}")
        print(f"  Recommended Model: {recommendation['recommended_model']}")
        print(f"  Detected Complexity: {recommendation['selection_criteria']['task_complexity']}")
        print(f"  Reasoning: {recommendation['selection_reasoning'][:80]}...")
        print()
    
    # 4. Model Validation
    print("✅ 4. MODEL VALIDATION SYSTEM")
    print("-" * 50)
    
    validation_tests = [
        ("engineer", "claude-3-opus-20240229"),       # Should match
        ("engineer", "claude-3-haiku-20240307"),      # Should warn
        ("documentation", "claude-3-5-sonnet-20241022"),  # Should match
        ("invalid_agent", "claude-3-opus-20240229")   # Should handle gracefully
    ]
    
    for agent_type, model_id in validation_tests:
        validation = model_selector.validate_model_selection(agent_type, model_id)
        status = "✅ Valid" if validation.get("valid", False) else "⚠️  Warning"
        print(f"{status} {agent_type:15} + {model_id}")
        
        if not validation.get("matches_recommendation", True):
            warnings = validation.get("warnings", [])
            if warnings:
                print(f"      Warning: {warnings[0]}")
    print()
    
    # 5. Environment Variable Overrides
    print("🌍 5. ENVIRONMENT VARIABLE OVERRIDES")
    print("-" * 50)
    
    print("Available override variables:")
    print("  CLAUDE_PM_MODEL_OVERRIDE          - Global override for all agents")
    print("  CLAUDE_PM_MODEL_ENGINEER          - Override for engineer agents")
    print("  CLAUDE_PM_MODEL_DOCUMENTATION     - Override for documentation agents")
    print("  ... (and more for each agent type)")
    print()
    
    # Check current environment
    current_global = os.getenv('CLAUDE_PM_MODEL_OVERRIDE')
    current_engineer = os.getenv('CLAUDE_PM_MODEL_ENGINEER')
    
    print("Current environment:")
    print(f"  Global Override: {current_global or 'None'}")
    print(f"  Engineer Override: {current_engineer or 'None'}")
    print()
    
    # 6. Task Tool Helper Integration
    print("🔗 6. TASK TOOL HELPER INTEGRATION")
    print("-" * 50)
    
    # Demonstrate subprocess creation with automatic model selection
    subprocess_result = await task_helper.create_agent_subprocess(
        agent_type="engineer",
        task_description="Implement advanced caching system with Redis and performance optimization",
        requirements=["High performance", "Scalability", "Monitoring"],
        deliverables=["Cache implementation", "Performance tests", "Documentation"]
    )
    
    if subprocess_result.get("success"):
        subprocess_info = subprocess_result["subprocess_info"]
        model_config = subprocess_info.get("model_config", {})
        
        print("Subprocess created with automatic model selection:")
        print(f"  Subprocess ID: {subprocess_info['subprocess_id']}")
        print(f"  Agent Type: {subprocess_info['agent_type']}")
        print(f"  Selected Model: {subprocess_info['selected_model']}")
        print(f"  Selection Method: {model_config.get('selection_method', 'N/A')}")
        
        criteria = model_config.get('criteria', {})
        if criteria:
            print(f"  Task Complexity: {criteria.get('task_complexity', 'N/A')}")
            print(f"  Reasoning Depth: {criteria.get('reasoning_depth', 'N/A')}")
            print(f"  Speed Priority: {criteria.get('speed_priority', False)}")
        print()
    
    # 7. Agent Registry Model Statistics
    print("📊 7. MODEL USAGE STATISTICS")
    print("-" * 50)
    
    # Discover agents and get model statistics
    await agent_registry.discover_agents()
    model_stats = await agent_registry.get_model_usage_statistics()
    
    print("Model distribution across discovered agents:")
    distribution = model_stats.get("model_distribution", {})
    for model, count in distribution.items():
        print(f"  {model}: {count} agents")
    
    print(f"\nTotal agents analyzed: {model_stats.get('total_agents', 0)}")
    print(f"Auto-selected configurations: {model_stats.get('auto_selected_count', 0)}")
    print(f"Manually configured: {model_stats.get('manually_configured_count', 0)}")
    print()
    
    # 8. Model Selection Statistics
    print("📈 8. SELECTION ALGORITHM STATISTICS")
    print("-" * 50)
    
    selection_stats = model_selector.get_selection_statistics()
    
    print("Available models and their capabilities:")
    config_summary = selection_stats.get("configuration_summary", {})
    for model, summary in config_summary.items():
        print(f"  {model}:")
        print(f"    Capabilities: {summary['capabilities_count']}")
        print(f"    Cost Tier: {summary['cost_tier']}")
        print(f"    Speed Tier: {summary['speed_tier']}")
        print(f"    Reasoning Tier: {summary['reasoning_tier']}")
    print()
    
    # 9. Performance Configuration
    print("⚡ 9. PERFORMANCE CONFIGURATION")
    print("-" * 50)
    
    print("Task Tool Helper Performance Settings:")
    print(f"  Model Selection Enabled: {task_helper.config.enable_model_selection}")
    print(f"  Auto Model Optimization: {task_helper.config.auto_model_optimization}")
    print(f"  Performance Priority: {task_helper.config.performance_priority}")
    print(f"  Model Override: {task_helper.config.model_override or 'None'}")
    print()
    
    # Test performance priority settings
    priorities = ["speed", "quality", "balanced"]
    print("Performance priority impact on model selection:")
    for priority in priorities:
        task_helper.configure_model_selection(performance_priority=priority)
        
        # Test with a sample task
        recommendation = await task_helper.get_agent_model_recommendation(
            "engineer", 
            "Quick bug fix for authentication issue"
        )
        
        print(f"  {priority:10} priority → {recommendation.get('recommended_model', 'N/A')}")
    
    # Reset to balanced
    task_helper.configure_model_selection(performance_priority="balanced")
    print()
    
    # 10. Summary and Best Practices
    print("📚 10. SUMMARY AND BEST PRACTICES")
    print("-" * 50)
    
    print("Model Selection Rules Successfully Implemented:")
    print("✅ Opus: Orchestrator, Engineer agents (complex implementation)")
    print("✅ Sonnet: Documentation, QA, Research, Ops, Security, Data Engineer")
    print("✅ Intelligent task complexity analysis")
    print("✅ Environment variable configuration support")
    print("✅ Performance requirement matching")
    print("✅ Model fallback and error handling")
    print("✅ Task Tool Helper integration")
    print("✅ Agent Registry metadata support")
    print()
    
    print("Best Practices:")
    print("• Use environment variables for project-specific model preferences")
    print("• Let the system auto-select models based on task complexity")
    print("• Override only when specific performance requirements demand it")
    print("• Monitor model usage statistics to optimize selections")
    print("• Validate model configurations before production use")
    print()
    
    print("=" * 80)
    print("MODEL SELECTION DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demonstrate_model_selection())