#!/usr/bin/env python3
"""
Test Agent Management Service
=============================

Demonstrates the agent management service capabilities.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from claude_pm.services.agent_management_service import AgentManager
from claude_pm.models.agent_definition import (
    AgentDefinition, AgentMetadata, AgentType,
    AgentWorkflow, AgentPermissions
)


async def test_agent_management():
    """Test agent management service."""
    print("Testing Agent Management Service\n")
    
    # Initialize manager
    manager = AgentManager()
    
    # Test 1: List existing agents
    print("1. Listing existing agents:")
    agents = manager.list_agents()
    for name, info in agents.items():
        print(f"   - {name}: v{info['version']} ({info['location']})")
    print()
    
    # Test 2: Read an existing agent
    print("2. Reading documentation agent:")
    doc_agent = manager.read_agent("documentation-agent")
    if doc_agent:
        print(f"   Title: {doc_agent.title}")
        print(f"   Version: {doc_agent.metadata.version}")
        print(f"   Type: {doc_agent.metadata.type.value}")
        print(f"   Primary Role: {doc_agent.primary_role[:100]}...")
        print(f"   Capabilities: {len(doc_agent.capabilities)} defined")
        print(f"   Workflows: {len(doc_agent.workflows)} defined")
    print()
    
    # Test 3: Create a test agent
    print("3. Creating a test performance agent:")
    test_agent = AgentDefinition(
        name="performance-agent",
        title="Performance Optimization Agent",
        file_path="",
        metadata=AgentMetadata(
            type=AgentType.SPECIALIZED,
            model_preference="claude-3-opus",
            version="1.0.0",
            specializations=["performance", "optimization", "monitoring"]
        ),
        primary_role="Performance analysis and optimization specialist responsible for identifying bottlenecks and improving system performance.",
        when_to_use={
            "select": [
                "Keywords: 'performance', 'optimize', 'speed', 'bottleneck', 'profiling'",
                "Analyzing system performance metrics",
                "Optimizing code execution speed",
                "Identifying performance bottlenecks"
            ],
            "do_not_select": [
                "General code implementation (Engineer Agent)",
                "Security vulnerabilities (Security Agent)",
                "Documentation tasks (Documentation Agent)"
            ]
        },
        capabilities=[
            "**Performance Profiling**: Profile code execution and identify bottlenecks",
            "**Optimization Strategies**: Recommend and implement performance improvements",
            "**Metrics Analysis**: Analyze performance metrics and trends",
            "**Load Testing**: Design and execute load testing scenarios"
        ],
        authority=AgentPermissions(
            exclusive_write_access=["**/performance/", "**/*.perf.json", "**/benchmarks/"],
            forbidden_operations=["Modifying core business logic", "Changing security configurations"]
        ),
        workflows=[
            AgentWorkflow(
                name="Performance Analysis Workflow",
                trigger="Performance issue reported or optimization request",
                process=[
                    "Profile current performance baseline",
                    "Identify performance bottlenecks",
                    "Develop optimization strategies",
                    "Implement improvements",
                    "Validate performance gains"
                ],
                output="Performance report with implemented optimizations"
            )
        ],
        escalation_triggers=[
            "Performance degradation >50% from baseline",
            "Critical system components running at >90% capacity",
            "User-facing latency exceeding SLA thresholds"
        ],
        kpis=[
            "Response time improvement: >20% reduction",
            "Resource utilization: <70% under normal load",
            "Performance regression detection: <24 hours"
        ],
        dependencies=[
            "**Monitoring Agent**: Requires performance metrics and alerts",
            "**Engineer Agent**: Coordinates on code optimizations",
            "**QA Agent**: Validates performance improvements"
        ],
        tools_commands="""```bash
# Profile Python code
python -m cProfile -o profile.stats script.py

# Analyze memory usage
python -m memory_profiler script.py

# Run performance benchmarks
pytest benchmarks/ --benchmark-only

# Monitor system resources
htop
iostat -x 1
```"""
    )
    
    # Create the agent in project directory
    created_path = manager.create_agent("performance-agent", test_agent, location="project")
    print(f"   Created at: {created_path}")
    print()
    
    # Test 4: Update agent section
    print("4. Updating agent section:")
    updated_agent = manager.update_section(
        "performance-agent",
        AgentSection.CAPABILITIES,
        """- **Real-time Monitoring**: Monitor application performance in real-time
- **Performance Profiling**: Profile code execution and identify bottlenecks
- **Optimization Strategies**: Recommend and implement performance improvements
- **Metrics Analysis**: Analyze performance metrics and trends
- **Load Testing**: Design and execute load testing scenarios
- **Caching Strategies**: Implement and optimize caching mechanisms"""
    )
    if updated_agent:
        print(f"   Updated to version: {updated_agent.metadata.version}")
        print(f"   New capabilities count: {len(updated_agent.capabilities)}")
    print()
    
    # Test 5: Get agent API data
    print("5. Getting agent API data:")
    api_data = manager.get_agent_api("performance-agent")
    if api_data:
        print(f"   Agent: {api_data['name']}")
        print(f"   Version: {api_data['metadata']['version']}")
        print(f"   Specializations: {api_data['metadata']['specializations']}")
        print(f"   Capabilities: {len(api_data['capabilities'])}")
    print()
    
    # Test 6: Test version management
    print("6. Testing version management:")
    from claude_pm.services.agent_versioning import AgentVersionManager
    
    version_mgr = AgentVersionManager()
    current_version = "2.0.0"
    
    print(f"   Current version: {current_version}")
    print(f"   Serial increment: {version_mgr.increment_serial(current_version)}")
    print(f"   Minor increment: {version_mgr.increment_minor(current_version)}")
    print(f"   Major increment: {version_mgr.increment_major(current_version)}")
    
    # Compare versions
    v1, v2 = "2.0.1", "2.1.0"
    comparison = version_mgr.compare_versions(v1, v2)
    comp_str = "<" if comparison == -1 else ">" if comparison == 1 else "="
    print(f"   Version comparison: {v1} {comp_str} {v2}")
    print()
    
    # Test 7: Clean up test agent
    print("7. Cleaning up test agent:")
    if manager.delete_agent("performance-agent"):
        print("   Test agent deleted successfully")
    print()
    
    print("✅ Agent Management Service test completed!")


if __name__ == "__main__":
    asyncio.run(test_agent_management())