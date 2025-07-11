"""
Framework Integration Examples

Examples showing how to integrate memory triggers into existing
Claude PM Framework components using decorators and context managers.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from ..decorators import (
    workflow_memory_trigger,
    agent_memory_trigger,
    issue_memory_trigger,
    error_memory_trigger,
    knowledge_memory_trigger,
    decision_memory_trigger,
    workflow_trigger_context,
    agent_trigger_context,
    issue_trigger_context
)
from ..memory_trigger_service import MemoryTriggerService, create_memory_trigger_service
from ....agents.enhanced_qa_agent import EnhancedQAAgent


# Example 1: Workflow Memory Triggers

@workflow_memory_trigger(project_name="claude-multiagent-pm", workflow_type="push")
async def execute_push_workflow(project_name: str, branch: str = "main") -> Dict[str, Any]:
    """
    Example push workflow with automatic memory capture.
    
    This demonstrates how to add memory triggers to workflow functions.
    """
    result = {
        "workflow": "push",
        "project": project_name,
        "branch": branch,
        "steps": [],
        "success": True
    }
    
    try:
        # Step 1: Documentation validation
        result["steps"].append("documentation_validation")
        
        # Step 2: Quality checks
        result["steps"].append("quality_checks")
        
        # Step 3: Git operations
        result["steps"].append("git_operations")
        
        # Simulate some work
        await asyncio.sleep(0.1)
        
        result["message"] = f"Successfully pushed {project_name} to {branch}"
        
        return result
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise


@workflow_memory_trigger(project_name="claude-multiagent-pm", workflow_type="deploy")
async def execute_deploy_workflow(project_name: str, environment: str = "local") -> Dict[str, Any]:
    """
    Example deploy workflow with automatic memory capture.
    """
    result = {
        "workflow": "deploy",
        "project": project_name,
        "environment": environment,
        "steps": [],
        "success": True
    }
    
    try:
        # Step 1: Environment preparation
        result["steps"].append("environment_preparation")
        
        # Step 2: Service deployment
        result["steps"].append("service_deployment")
        
        # Step 3: Health validation
        result["steps"].append("health_validation")
        
        # Simulate deployment
        await asyncio.sleep(0.2)
        
        result["message"] = f"Successfully deployed {project_name} to {environment}"
        
        return result
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise


# Example 2: Agent Memory Triggers

@agent_memory_trigger(agent_type="qa", project_name="claude-multiagent-pm")
async def execute_qa_validation(test_suite: str, project_name: str) -> Dict[str, Any]:
    """
    Example QA validation with automatic memory capture.
    """
    result = {
        "agent": "qa",
        "test_suite": test_suite,
        "project": project_name,
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "success": True
    }
    
    try:
        # Simulate test execution
        result["tests_run"] = 25
        result["tests_passed"] = 24
        result["tests_failed"] = 1
        
        await asyncio.sleep(0.3)
        
        result["message"] = f"QA validation completed for {test_suite}"
        
        return result
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise


@agent_memory_trigger(agent_type="documentation", project_name="claude-multiagent-pm")
async def execute_documentation_validation(project_name: str) -> Dict[str, Any]:
    """
    Example documentation validation with automatic memory capture.
    """
    result = {
        "agent": "documentation",
        "project": project_name,
        "files_checked": 0,
        "issues_found": 0,
        "success": True
    }
    
    try:
        # Simulate documentation check
        result["files_checked"] = 15
        result["issues_found"] = 2
        
        await asyncio.sleep(0.1)
        
        result["message"] = f"Documentation validation completed for {project_name}"
        
        return result
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise


# Example 3: Issue Memory Triggers

@issue_memory_trigger(issue_id="ISS-001", project_name="claude-multiagent-pm")
async def resolve_memory_integration_issue(issue_id: str, solution: str) -> Dict[str, Any]:
    """
    Example issue resolution with automatic memory capture.
    """
    result = {
        "issue_id": issue_id,
        "solution": solution,
        "resolution_time": "2 hours",
        "success": True
    }
    
    try:
        # Simulate issue resolution
        await asyncio.sleep(0.1)
        
        result["message"] = f"Issue {issue_id} resolved successfully"
        
        return result
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise


# Example 4: Error Memory Triggers

@error_memory_trigger(error_type="memory_backend_failure", project_name="claude-multiagent-pm")
async def handle_memory_backend_error(error_message: str) -> Dict[str, Any]:
    """
    Example error handling with automatic memory capture.
    """
    result = {
        "error_type": "memory_backend_failure",
        "error_message": error_message,
        "resolution_steps": [],
        "success": True
    }
    
    try:
        # Step 1: Diagnose the issue
        result["resolution_steps"].append("diagnose_backend_connectivity")
        
        # Step 2: Attempt fallback
        result["resolution_steps"].append("activate_fallback_backend")
        
        # Step 3: Validate recovery
        result["resolution_steps"].append("validate_recovery")
        
        await asyncio.sleep(0.2)
        
        result["message"] = "Memory backend error resolved using fallback"
        
        return result
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise


# Example 5: Knowledge Memory Triggers

@knowledge_memory_trigger(knowledge_type="pattern_solution", project_name="claude-multiagent-pm")
async def capture_solution_pattern(pattern_name: str, solution: str) -> Dict[str, Any]:
    """
    Example knowledge capture with automatic memory capture.
    """
    result = {
        "knowledge_type": "pattern_solution",
        "pattern_name": pattern_name,
        "solution": solution,
        "success": True
    }
    
    try:
        # Process the solution pattern
        await asyncio.sleep(0.1)
        
        result["message"] = f"Solution pattern '{pattern_name}' captured successfully"
        
        return result
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise


# Example 6: Decision Memory Triggers

@decision_memory_trigger(decision_type="architecture_choice", project_name="claude-multiagent-pm")
async def record_architecture_decision(decision: str, rationale: str) -> Dict[str, Any]:
    """
    Example decision recording with automatic memory capture.
    """
    result = {
        "decision_type": "architecture_choice",
        "decision": decision,
        "rationale": rationale,
        "success": True
    }
    
    try:
        # Record the decision
        await asyncio.sleep(0.1)
        
        result["message"] = f"Architecture decision recorded: {decision}"
        
        return result
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise


# Example 7: Context Manager Usage

async def complex_workflow_with_context_manager():
    """
    Example of using context managers for complex workflows.
    """
    # Workflow context manager
    async with workflow_trigger_context(
        operation_name="complex_deployment",
        project_name="claude-multiagent-pm",
        workflow_type="deploy"
    ) as ctx:
        
        # Add metadata as we go
        ctx.add_metadata(environment="production", version="1.0.0")
        ctx.add_tags("production", "deployment", "v1.0.0")
        
        # Step 1: Preparation
        await asyncio.sleep(0.1)
        ctx.add_metadata(step="preparation_complete")
        
        # Step 2: Deployment
        await asyncio.sleep(0.2)
        ctx.add_metadata(step="deployment_complete")
        
        # Step 3: Validation
        await asyncio.sleep(0.1)
        ctx.add_metadata(step="validation_complete")
        
        # Set final result
        ctx.set_result({
            "status": "success",
            "duration": "0.4 seconds",
            "steps_completed": 3
        })


async def agent_operation_with_context_manager():
    """
    Example of using context managers for agent operations.
    """
    # Agent context manager
    async with agent_trigger_context(
        operation_name="comprehensive_qa",
        project_name="claude-multiagent-pm",
        agent_type="qa"
    ) as ctx:
        
        # Add operation metadata
        ctx.add_metadata(test_suite="integration", coverage_threshold=80)
        ctx.add_tags("integration", "qa", "testing")
        
        # Execute tests
        test_results = {
            "total_tests": 50,
            "passed": 48,
            "failed": 2,
            "coverage": 85
        }
        
        await asyncio.sleep(0.3)
        
        # Set results
        ctx.set_result(test_results)


# Example 8: Integration with existing framework components

class MemoryIntegratedWorkflowService:
    """
    Example service that integrates memory triggers with existing workflow patterns.
    """
    
    def __init__(self, memory_trigger_service: MemoryTriggerService):
        self.memory_service = memory_trigger_service
        self.logger = logging.getLogger(__name__)
    
    @workflow_memory_trigger(project_name="claude-multiagent-pm", workflow_type="comprehensive")
    async def execute_comprehensive_workflow(self, project_name: str) -> Dict[str, Any]:
        """
        Execute a comprehensive workflow with memory triggers.
        """
        result = {
            "workflow": "comprehensive",
            "project": project_name,
            "phases": [],
            "success": True
        }
        
        try:
            # Phase 1: Documentation
            doc_result = await self.execute_documentation_phase(project_name)
            result["phases"].append(doc_result)
            
            # Phase 2: Quality Assurance
            qa_result = await self.execute_qa_phase(project_name)
            result["phases"].append(qa_result)
            
            # Phase 3: Deployment
            deploy_result = await self.execute_deployment_phase(project_name)
            result["phases"].append(deploy_result)
            
            result["message"] = "Comprehensive workflow completed successfully"
            
            return result
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            self.logger.error(f"Comprehensive workflow failed: {e}")
            raise
    
    @agent_memory_trigger(agent_type="documentation", project_name="claude-multiagent-pm")
    async def execute_documentation_phase(self, project_name: str) -> Dict[str, Any]:
        """Documentation phase with memory trigger."""
        return {
            "phase": "documentation",
            "status": "completed",
            "duration": "1.2 seconds",
            "files_processed": 23
        }
    
    @agent_memory_trigger(agent_type="qa", project_name="claude-multiagent-pm")
    async def execute_qa_phase(self, project_name: str) -> Dict[str, Any]:
        """QA phase with memory trigger."""
        return {
            "phase": "qa",
            "status": "completed",
            "duration": "3.5 seconds",
            "tests_run": 42,
            "success_rate": 0.95
        }
    
    @workflow_memory_trigger(project_name="claude-multiagent-pm", workflow_type="deploy")
    async def execute_deployment_phase(self, project_name: str) -> Dict[str, Any]:
        """Deployment phase with memory trigger."""
        return {
            "phase": "deployment",
            "status": "completed",
            "duration": "2.1 seconds",
            "services_deployed": 3
        }


# Example 9: Error handling with memory triggers

class MemoryIntegratedErrorHandler:
    """
    Example error handler that captures error resolution patterns.
    """
    
    def __init__(self, memory_trigger_service: MemoryTriggerService):
        self.memory_service = memory_trigger_service
        self.logger = logging.getLogger(__name__)
    
    @error_memory_trigger(error_type="service_unavailable", project_name="claude-multiagent-pm")
    async def handle_service_unavailable(self, service_name: str, error: Exception) -> Dict[str, Any]:
        """
        Handle service unavailable errors with memory capture.
        """
        result = {
            "error_type": "service_unavailable",
            "service_name": service_name,
            "error_message": str(error),
            "resolution_steps": [],
            "success": False
        }
        
        try:
            # Step 1: Check service health
            result["resolution_steps"].append("check_service_health")
            
            # Step 2: Attempt restart
            result["resolution_steps"].append("attempt_service_restart")
            
            # Step 3: Validate recovery
            result["resolution_steps"].append("validate_service_recovery")
            
            # Simulate recovery
            await asyncio.sleep(0.2)
            
            result["success"] = True
            result["message"] = f"Service {service_name} recovered successfully"
            
            return result
            
        except Exception as recovery_error:
            result["recovery_error"] = str(recovery_error)
            self.logger.error(f"Failed to recover service {service_name}: {recovery_error}")
            raise
    
    @error_memory_trigger(error_type="memory_backend_failure", project_name="claude-multiagent-pm")
    async def handle_memory_backend_failure(self, backend_name: str, error: Exception) -> Dict[str, Any]:
        """
        Handle memory backend failures with automatic fallback.
        """
        result = {
            "error_type": "memory_backend_failure",
            "backend_name": backend_name,
            "error_message": str(error),
            "fallback_activated": False,
            "success": False
        }
        
        try:
            # Activate fallback backend
            fallback_result = await self.memory_service.get_memory_service().switch_backend("sqlite")
            
            if fallback_result:
                result["fallback_activated"] = True
                result["success"] = True
                result["message"] = f"Switched from {backend_name} to sqlite fallback"
            else:
                result["message"] = f"Failed to activate fallback for {backend_name}"
            
            return result
            
        except Exception as fallback_error:
            result["fallback_error"] = str(fallback_error)
            self.logger.error(f"Fallback activation failed: {fallback_error}")
            raise


# Example 10: Demo function

async def run_memory_trigger_demo():
    """
    Run a comprehensive demo of memory trigger functionality.
    """
    print("🚀 Memory Trigger Demo Starting...")
    
    # Initialize memory trigger service
    config = {
        "enabled": True,
        "memory": {
            "fallback_chain": ["sqlite"],  # Use sqlite for demo
        }
    }
    
    async with create_memory_trigger_service(config) as service:
        print(f"✅ Memory trigger service initialized")
        
        # Demo 1: Workflow triggers
        print("\n📋 Demo 1: Workflow Memory Triggers")
        push_result = await execute_push_workflow("claude-multiagent-pm", "feature-branch")
        print(f"   Push workflow result: {push_result['message']}")
        
        deploy_result = await execute_deploy_workflow("claude-multiagent-pm", "staging")
        print(f"   Deploy workflow result: {deploy_result['message']}")
        
        # Demo 2: Agent triggers
        print("\n🤖 Demo 2: Agent Memory Triggers")
        qa_result = await execute_qa_validation("unit_tests", "claude-multiagent-pm")
        print(f"   QA validation result: {qa_result['message']}")
        
        doc_result = await execute_documentation_validation("claude-multiagent-pm")
        print(f"   Documentation validation result: {doc_result['message']}")
        
        # Demo 3: Issue triggers
        print("\n🐛 Demo 3: Issue Resolution Memory Triggers")
        issue_result = await resolve_memory_integration_issue("ISS-001", "Added memory trigger hooks")
        print(f"   Issue resolution result: {issue_result['message']}")
        
        # Demo 4: Error triggers
        print("\n🔧 Demo 4: Error Resolution Memory Triggers")
        error_result = await handle_memory_backend_error("Backend connection timeout")
        print(f"   Error resolution result: {error_result['message']}")
        
        # Demo 5: Knowledge triggers
        print("\n📚 Demo 5: Knowledge Capture Memory Triggers")
        knowledge_result = await capture_solution_pattern("async_memory_integration", "Use decorators and context managers")
        print(f"   Knowledge capture result: {knowledge_result['message']}")
        
        # Demo 6: Decision triggers
        print("\n🎯 Demo 6: Decision Recording Memory Triggers")
        decision_result = await record_architecture_decision("Use trigger-based memory system", "Provides automatic, policy-driven memory creation")
        print(f"   Decision recording result: {decision_result['message']}")
        
        # Demo 7: Context managers
        print("\n🔄 Demo 7: Context Manager Memory Triggers")
        await complex_workflow_with_context_manager()
        print("   Complex workflow with context manager completed")
        
        await agent_operation_with_context_manager()
        print("   Agent operation with context manager completed")
        
        # Demo 8: Service health
        print("\n🏥 Demo 8: Service Health Check")
        health = await service.get_service_health()
        print(f"   Memory service status: {health['memory_service']['status']}")
        print(f"   Trigger orchestrator status: {health['trigger_orchestrator']['status']}")
        print(f"   Policy engine status: {health['policy_engine']['status']}")
        print(f"   Framework hooks status: {health['framework_hooks']['status']}")
        
        # Demo 9: Service metrics
        print("\n📊 Demo 9: Service Metrics")
        metrics = await service.get_service_metrics()
        if 'framework_hooks' in metrics:
            hooks_metrics = metrics['framework_hooks']
            print(f"   Total hooks executed: {hooks_metrics.get('hooks_executed', 0)}")
            print(f"   Successful hooks: {hooks_metrics.get('successful_hooks', 0)}")
            print(f"   Memory captures: {hooks_metrics.get('memory_captures', 0)}")
    
    print("\n🎉 Memory Trigger Demo Completed!")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(run_memory_trigger_demo())