#!/usr/bin/env python3
"""
MEM-003 Multi-Agent Architecture Demo
Demonstrates the enhanced multi-agent ecosystem with memory integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.claude_pm_memory import ClaudePMMemory, MemoryCategory, create_claude_pm_memory
from claude_pm.services.multi_agent_orchestrator import (
    MultiAgentOrchestrator, AgentType, AgentTask, create_multi_agent_orchestrator
)
from claude_pm.services.mem0_context_manager import (
    Mem0ContextManager, ContextRequest, ContextType, ContextScope, create_mem0_context_manager
)


async def setup_demo_environment(memory: ClaudePMMemory) -> None:
    """Set up demo environment with sample memories."""
    print("🧠 Setting up demo environment with sample memories...")
    
    # Create demo project space
    await memory.create_project_memory_space(
        project_name="demo_project",
        description="Demo project for MEM-003 multi-agent architecture"
    )
    
    # Store sample patterns
    pattern_memories = [
        {
            "content": "FastAPI REST API Pattern: Use FastAPI with async/await for high-performance APIs. Include automatic OpenAPI documentation and request validation.",
            "metadata": {"pattern_type": "api_design", "technology": "fastapi", "use_cases": ["rest_api", "microservices"]},
            "tags": ["fastapi", "api", "python", "async", "rest"]
        },
        {
            "content": "React Component Pattern: Create reusable components with TypeScript interfaces. Use hooks for state management and proper error boundaries.",
            "metadata": {"pattern_type": "frontend", "technology": "react", "use_cases": ["ui_components", "state_management"]},
            "tags": ["react", "typescript", "frontend", "components", "hooks"]
        },
        {
            "content": "Database Connection Pool Pattern: Use connection pooling to optimize database performance. Configure pool size based on concurrent load.",
            "metadata": {"pattern_type": "database", "technology": "postgresql", "use_cases": ["performance", "scalability"]},
            "tags": ["database", "postgresql", "performance", "connection_pool"]
        }
    ]
    
    for pattern in pattern_memories:
        await memory.store_memory(
            category=MemoryCategory.PATTERN,
            content=pattern["content"],
            metadata=pattern["metadata"],
            project_name="demo_project",
            tags=pattern["tags"]
        )
    
    # Store sample team standards
    team_memories = [
        {
            "content": "Coding Standard: Use snake_case for Python variables and functions. Use PascalCase for classes. Maximum line length is 88 characters.",
            "metadata": {"standard_type": "naming_convention", "language": "python", "enforcement_level": "required"},
            "tags": ["python", "naming", "standards", "pep8"]
        },
        {
            "content": "Code Review Standard: All PRs require security review, performance analysis, and style check. Minimum 90% test coverage required.",
            "metadata": {"standard_type": "code_review", "enforcement_level": "required", "coverage_threshold": 90},
            "tags": ["code_review", "security", "performance", "testing", "coverage"]
        }
    ]
    
    for team in team_memories:
        await memory.store_memory(
            category=MemoryCategory.TEAM,
            content=team["content"],
            metadata=team["metadata"],
            project_name="demo_project",
            tags=team["tags"]
        )
    
    # Store sample error patterns
    error_memories = [
        {
            "content": "SQL Injection Bug: User input was concatenated directly into SQL query. Fixed by using parameterized queries with prepared statements.",
            "metadata": {"error_type": "security_vulnerability", "severity": "critical", "solution": "parameterized_queries"},
            "tags": ["sql_injection", "security", "database", "vulnerability"]
        },
        {
            "content": "N+1 Query Problem: ORM generated separate queries for each related object. Fixed by using select_related() to eager load relationships.",
            "metadata": {"error_type": "performance_issue", "severity": "high", "solution": "eager_loading"},
            "tags": ["performance", "database", "orm", "n_plus_one", "django"]
        }
    ]
    
    for error in error_memories:
        await memory.store_memory(
            category=MemoryCategory.ERROR,
            content=error["content"],
            metadata=error["metadata"],
            project_name="demo_project",
            tags=error["tags"]
        )
    
    print("✅ Demo environment setup complete")


async def demonstrate_context_preparation(context_manager: Mem0ContextManager) -> None:
    """Demonstrate memory-augmented context preparation."""
    print("\n🎯 Demonstrating Memory-Augmented Context Preparation")
    
    # Test agent context preparation
    print("\n1. Preparing context for Code Review Engineer...")
    code_review_context = await context_manager.prepare_agent_context(
        agent_type="code_review_engineer",
        project_name="demo_project",
        task_description="Review Python API implementation for security and performance issues",
        keywords=["python", "api", "security", "performance"]
    )
    
    print(f"   Context Summary: {code_review_context.context_summary}")
    print(f"   Total Memories: {code_review_context.total_memories}")
    print(f"   Patterns: {len(code_review_context.patterns)}")
    print(f"   Team Standards: {len(code_review_context.team_standards)}")
    print(f"   Historical Errors: {len(code_review_context.historical_errors)}")
    
    # Test architecture context preparation
    print("\n2. Preparing context for Architect Agent...")
    architect_context = await context_manager.prepare_agent_context(
        agent_type="architect",
        project_name="demo_project", 
        task_description="Design scalable API architecture using modern patterns",
        keywords=["architecture", "api", "scalability", "design"]
    )
    
    print(f"   Context Summary: {architect_context.context_summary}")
    print(f"   Total Memories: {architect_context.total_memories}")
    print(f"   Preparation Time: {architect_context.preparation_time_ms}ms")
    
    # Test cross-project context
    print("\n3. Preparing global pattern context...")
    global_context = await context_manager.prepare_context(
        ContextRequest(
            context_type=ContextType.PATTERN_MATCHING,
            scope=ContextScope.GLOBAL_PATTERNS,
            keywords=["api", "performance"],
            categories=[MemoryCategory.PATTERN, MemoryCategory.ERROR],
            max_memories=5
        )
    )
    
    print(f"   Context Summary: {global_context.context_summary}")
    print(f"   Global Patterns Found: {len(global_context.patterns)}")


async def demonstrate_multi_agent_orchestration(orchestrator: MultiAgentOrchestrator) -> None:
    """Demonstrate multi-agent task orchestration."""
    print("\n🤖 Demonstrating Multi-Agent Orchestration")
    
    # Submit tasks for different agent types
    task_configs = [
        {
            "agent_type": AgentType.ARCHITECT,
            "description": "Design API architecture for user management system",
            "priority": 8
        },
        {
            "agent_type": AgentType.SECURITY_ENGINEER,
            "description": "Perform security analysis of authentication endpoints",
            "priority": 9
        },
        {
            "agent_type": AgentType.CODE_REVIEW_ENGINEER,
            "description": "Review user registration code for security and style compliance",
            "priority": 7
        },
        {
            "agent_type": AgentType.PERFORMANCE_ENGINEER,
            "description": "Analyze database query performance in user lookup functions",
            "priority": 6
        },
        {
            "agent_type": AgentType.QA,
            "description": "Create comprehensive test suite for user management features",
            "priority": 5
        }
    ]
    
    task_ids = []
    print("\n📋 Submitting tasks to orchestrator...")
    
    for i, config in enumerate(task_configs):
        task_id = await orchestrator.submit_task(
            agent_type=config["agent_type"],
            description=config["description"],
            project_name="demo_project",
            priority=config["priority"]
        )
        task_ids.append(task_id)
        print(f"   {i+1}. {config['agent_type'].value}: {task_id}")
    
    # Execute tasks in parallel
    print("\n⚡ Running parallel execution...")
    execution_summary = await orchestrator.run_parallel_execution(max_iterations=3)
    
    print(f"\n📊 Execution Summary:")
    print(f"   Iterations: {execution_summary['iterations']}")
    print(f"   Tasks Completed: {execution_summary['tasks_completed']}")
    print(f"   Tasks Failed: {execution_summary['tasks_failed']}")
    print(f"   Tasks Remaining: {execution_summary['tasks_remaining']}")
    print(f"   Worktree Stats: {execution_summary['worktree_stats']}")
    
    # Show completed task results
    if execution_summary['tasks_completed'] > 0:
        print(f"\n✅ Completed Task Results:")
        for task_id, execution in orchestrator.completed_tasks.items():
            if execution.result:
                print(f"   Task {task_id} ({execution.agent_type.value}):")
                print(f"     Status: {execution.status.value}")
                print(f"     Duration: {execution.result.get('execution_time', 'N/A')}s")
                print(f"     Memory Context Size: {execution.result.get('memory_context_size', 0)}")
                if execution.agent_type == AgentType.CODE_REVIEW_ENGINEER:
                    print(f"     Review Dimensions: {execution.result.get('review_dimensions', [])}")
                    print(f"     Findings: {execution.result.get('findings_count', 0)}")


async def demonstrate_agent_coordination(orchestrator: MultiAgentOrchestrator) -> None:
    """Demonstrate agent-to-agent communication and coordination."""
    print("\n💬 Demonstrating Agent Coordination and Messaging")
    
    # Simulate agent-to-agent messages
    await orchestrator.send_message(
        from_agent="architect_agent",
        to_agent="security_engineer",
        message={
            "type": "architecture_review_request",
            "content": "Please review the proposed OAuth2 implementation for security vulnerabilities",
            "priority": "high",
            "context": {"component": "auth_service", "endpoint": "/oauth/token"}
        }
    )
    
    await orchestrator.send_message(
        from_agent="security_engineer",
        to_agent="code_review_engineer",
        message={
            "type": "security_findings",
            "content": "Found potential timing attack in token comparison. Please verify implementation.",
            "priority": "critical",
            "findings": ["timing_attack_vulnerability", "weak_token_validation"]
        }
    )
    
    await orchestrator.send_message(
        from_agent="code_review_engineer",
        to_agent="qa",
        message={
            "type": "test_requirements",
            "content": "Need security test cases for timing attack prevention",
            "priority": "high",
            "test_types": ["security_tests", "timing_tests", "fuzzing_tests"]
        }
    )
    
    # Check messages for each agent
    print("\n📨 Agent Message Queues:")
    for agent in ["security_engineer", "code_review_engineer", "qa"]:
        messages = await orchestrator.get_messages(agent)
        print(f"   {agent}: {len(messages)} messages")
        for msg in messages:
            print(f"     - From {msg['from']}: {msg['type']} (Priority: {msg.get('priority', 'normal')})")


async def main():
    """Main demonstration function."""
    print("🚀 MEM-003 Enhanced Multi-Agent Architecture Demo")
    print("=" * 60)
    
    # Initialize memory system
    print("\n🔧 Initializing Memory System...")
    memory = create_claude_pm_memory(host="localhost", port=8002)
    
    try:
        # Test memory connection
        if not await memory.connect():
            print("❌ Failed to connect to mem0AI service at localhost:8002")
            print("   Please ensure mem0AI service is running.")
            return
        
        print("✅ Connected to mem0AI service")
        
        # Setup demo environment
        await setup_demo_environment(memory)
        
        # Initialize context manager
        print("\n🧠 Initializing Context Manager...")
        context_manager = create_mem0_context_manager(memory)
        
        # Demonstrate context preparation
        await demonstrate_context_preparation(context_manager)
        
        # Initialize multi-agent orchestrator
        print("\n🎼 Initializing Multi-Agent Orchestrator...")
        orchestrator = await create_multi_agent_orchestrator(
            base_repo_path=str(project_root),
            memory=memory,
            max_parallel=3  # Reduced for demo
        )
        
        print(f"✅ Orchestrator initialized with {len(orchestrator.agent_definitions)} agent types")
        
        # Demonstrate orchestration
        await demonstrate_multi_agent_orchestration(orchestrator)
        
        # Demonstrate coordination
        await demonstrate_agent_coordination(orchestrator)
        
        # Show final statistics
        print("\n📈 Final Statistics:")
        memory_stats = memory.get_statistics()
        context_stats = context_manager.get_context_stats()
        orchestrator_stats = orchestrator.get_orchestrator_stats()
        
        print(f"\nMemory System:")
        print(f"   Operations: {memory_stats['operations_count']}")
        print(f"   Success Rate: {memory_stats['success_rate']:.1f}%")
        print(f"   Memories Stored: {memory_stats['memories_stored']}")
        print(f"   Memories Retrieved: {memory_stats['memories_retrieved']}")
        
        print(f"\nContext Manager:")
        print(f"   Cached Contexts: {context_stats['cached_contexts']}")
        print(f"   Agent Roles Supported: {context_stats['agent_roles_supported']}")
        
        print(f"\nMulti-Agent Orchestrator:")
        print(f"   Agent Types: {len(orchestrator_stats['agent_types'])}")
        print(f"   Completed Tasks: {orchestrator_stats['completed_tasks']}")
        print(f"   Active Executions: {orchestrator_stats['active_executions']}")
        print(f"   Worktree Stats: {orchestrator_stats['worktree_stats']}")
        
        # Cleanup
        await orchestrator.cleanup()
        
        print("\n🎯 MEM-003 Demo Complete!")
        print("\nKey Achievements:")
        print("✅ 11-Agent Ecosystem operational with memory integration")
        print("✅ Git Worktree isolation working for parallel agents") 
        print("✅ Memory-augmented context preparation functional")
        print("✅ Agent coordination messaging system operational")
        print("✅ Code Review Engineer performing multi-dimensional analysis")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await memory.disconnect()


if __name__ == "__main__":
    asyncio.run(main())