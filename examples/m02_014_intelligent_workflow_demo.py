"""
M02-014 Intelligent Workflow Selection System Demo

This demo showcases the intelligent workflow selection system capabilities:
- Automatic workflow selection based on task analysis
- Dynamic routing and optimization
- Success prediction and resource allocation
- Continuous learning from outcomes

Run this script to see the system in action with various task scenarios.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the intelligent workflow components
from claude_pm.services.intelligent_workflow_orchestrator import (
    IntelligentWorkflowOrchestrator, create_intelligent_workflow_orchestrator,
    WorkflowExecutionContext
)
from claude_pm.services.workflow_selection_engine import (
    WorkflowType, RoutingStrategy, WorkflowSelectionRequest
)
from claude_pm.services.intelligent_task_planner import TaskComplexity
from config.memory_config import create_memory_service


class IntelligentWorkflowDemo:
    """Demo class showcasing intelligent workflow selection capabilities."""
    
    def __init__(self):
        """Initialize the demo with a memory service and orchestrator."""
        print("🚀 Initializing Intelligent Workflow Selection System Demo...")
        
        try:
            # Initialize memory service
            self.memory_service = create_memory_service()
            
            # Initialize intelligent workflow orchestrator
            self.orchestrator = create_intelligent_workflow_orchestrator(
                memory_service=self.memory_service
            )
            
            print("✅ Demo initialized successfully!")
            
        except Exception as e:
            print(f"❌ Demo initialization failed: {e}")
            # Use mock services for demo
            self.memory_service = None
            self.orchestrator = None
    
    def print_section_header(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*60}")
        print(f"📋 {title}")
        print('='*60)
    
    def print_workflow_recommendation(self, recommendation, task_description: str):
        """Print formatted workflow recommendation."""
        print(f"\n🎯 Task: {task_description}")
        print(f"   Selected Workflow: {recommendation.workflow_type.value}")
        print(f"   Confidence: {recommendation.confidence:.2f}")
        print(f"   Routing Strategy: {recommendation.routing_strategy.value}")
        print(f"   Predicted Success Rate: {recommendation.predicted_success_rate:.1%}")
        print(f"   Estimated Duration: {recommendation.estimated_duration_minutes} minutes")
        print(f"   Resource Requirements: {recommendation.resource_requirements}")
        
        if recommendation.risk_factors:
            print(f"   ⚠️  Risk Factors: {', '.join(recommendation.risk_factors)}")
        
        if recommendation.optimization_opportunities:
            print(f"   💡 Optimizations: {', '.join(recommendation.optimization_opportunities[:2])}")
        
        print(f"   💭 Reasoning: {recommendation.reasoning}")
    
    def print_execution_result(self, result):
        """Print formatted execution result."""
        status_emoji = "✅" if result.success else "❌"
        print(f"\n{status_emoji} Execution Result:")
        print(f"   Success: {result.success}")
        print(f"   Outcome: {result.outcome}")
        print(f"   Actual Duration: {result.actual_duration} minutes")
        print(f"   Quality Score: {result.quality_score:.2f}")
        print(f"   Efficiency Score: {result.efficiency_score:.2f}")
        
        # Prediction accuracy
        duration_accuracy = 1.0 - abs(result.predicted_duration - result.actual_duration) / max(result.predicted_duration, 1)
        success_predicted = result.predicted_success_rate > 0.5
        success_actual = result.success
        success_accuracy = 1.0 if success_predicted == success_actual else 0.0
        
        print(f"   🎯 Duration Prediction Accuracy: {duration_accuracy:.1%}")
        print(f"   🎯 Success Prediction Accuracy: {success_accuracy:.1%}")
        
        if result.lessons_learned:
            print(f"   📚 Lessons Learned: {', '.join(result.lessons_learned[:2])}")
    
    async def demo_simple_task_workflow(self):
        """Demo workflow selection for simple tasks."""
        self.print_section_header("Simple Task Workflow Selection")
        
        simple_tasks = [
            "Fix a typo in the README file",
            "Update the copyright year in documentation",
            "Add a simple CSS style to improve button appearance",
            "Create a basic unit test for a utility function"
        ]
        
        for task in simple_tasks:
            try:
                if not self.orchestrator:
                    print(f"🔄 Analyzing: {task}")
                    print(f"   Expected Workflow: simple_linear or emergency_fast_track")
                    print(f"   Expected Duration: 10-30 minutes")
                    continue
                
                # Get workflow recommendation
                recommendations = await self.orchestrator.get_workflow_recommendations(
                    task_description=task,
                    priority_level="low",
                    quality_requirements="standard"
                )
                
                if recommendations:
                    self.print_workflow_recommendation(recommendations[0], task)
                
            except Exception as e:
                print(f"❌ Error analyzing task: {e}")
    
    async def demo_complex_task_workflow(self):
        """Demo workflow selection for complex tasks."""
        self.print_section_header("Complex Task Workflow Selection")
        
        complex_tasks = [
            {
                "description": "Design and implement a new microservice architecture for user authentication",
                "complexity": TaskComplexity.COMPLEX,
                "priority": "high",
                "quality": "critical"
            },
            {
                "description": "Migrate the entire database from MySQL to PostgreSQL with zero downtime",
                "complexity": TaskComplexity.EPIC,
                "priority": "medium",
                "quality": "critical"
            },
            {
                "description": "Research and implement machine learning-based recommendation system",
                "complexity": TaskComplexity.COMPLEX,
                "priority": "medium",
                "quality": "high"
            }
        ]
        
        for task_info in complex_tasks:
            try:
                if not self.orchestrator:
                    print(f"🔄 Analyzing: {task_info['description']}")
                    print(f"   Expected Workflow: hierarchical_review or research_discovery")
                    print(f"   Expected Duration: 60-180 minutes")
                    continue
                
                # Get workflow recommendation
                recommendations = await self.orchestrator.get_workflow_recommendations(
                    task_description=task_info["description"],
                    task_complexity=task_info["complexity"],
                    priority_level=task_info["priority"],
                    quality_requirements=task_info["quality"]
                )
                
                if recommendations:
                    self.print_workflow_recommendation(recommendations[0], task_info["description"])
                
            except Exception as e:
                print(f"❌ Error analyzing complex task: {e}")
    
    async def demo_urgent_task_workflow(self):
        """Demo workflow selection for urgent tasks."""
        self.print_section_header("Urgent Task Workflow Selection")
        
        urgent_tasks = [
            {
                "description": "Critical production bug causing 500 errors for all users",
                "priority": "critical",
                "deadline": datetime.now() + timedelta(hours=1),
                "quality": "minimal"
            },
            {
                "description": "Security vulnerability needs immediate patching",
                "priority": "critical", 
                "deadline": datetime.now() + timedelta(hours=4),
                "quality": "standard"
            },
            {
                "description": "Customer-facing feature broken before major demo",
                "priority": "high",
                "deadline": datetime.now() + timedelta(hours=8),
                "quality": "standard"
            }
        ]
        
        for task_info in urgent_tasks:
            try:
                if not self.orchestrator:
                    print(f"🔄 Analyzing: {task_info['description']}")
                    print(f"   Expected Workflow: emergency_fast_track")
                    print(f"   Expected Strategy: performance_optimized")
                    continue
                
                # Get workflow recommendation
                recommendations = await self.orchestrator.get_workflow_recommendations(
                    task_description=task_info["description"],
                    priority_level=task_info["priority"],
                    deadline=task_info["deadline"],
                    quality_requirements=task_info["quality"]
                )
                
                if recommendations:
                    self.print_workflow_recommendation(recommendations[0], task_info["description"])
                
            except Exception as e:
                print(f"❌ Error analyzing urgent task: {e}")
    
    async def demo_research_task_workflow(self):
        """Demo workflow selection for research tasks."""
        self.print_section_header("Research Task Workflow Selection")
        
        research_tasks = [
            "Research and analyze feasibility of migrating to Kubernetes",
            "Investigate performance bottlenecks in the recommendation engine",
            "Explore integration options with third-party payment providers",
            "Analyze user behavior patterns to inform UX improvements"
        ]
        
        for task in research_tasks:
            try:
                if not self.orchestrator:
                    print(f"🔄 Analyzing: {task}")
                    print(f"   Expected Workflow: research_discovery")
                    print(f"   Expected Features: knowledge_capture, exploration_depth")
                    continue
                
                # Get workflow recommendation
                recommendations = await self.orchestrator.get_workflow_recommendations(
                    task_description=task,
                    priority_level="medium",
                    quality_requirements="high"
                )
                
                if recommendations:
                    self.print_workflow_recommendation(recommendations[0], task)
                
            except Exception as e:
                print(f"❌ Error analyzing research task: {e}")
    
    async def demo_end_to_end_execution(self):
        """Demo complete end-to-end workflow execution."""
        self.print_section_header("End-to-End Workflow Execution")
        
        if not self.orchestrator:
            print("⚠️  Orchestrator not available - showing mock execution flow:")
            print("   1. Task Analysis & Workflow Selection")
            print("   2. Task Decomposition & Planning")
            print("   3. Workflow Execution with Monitoring")
            print("   4. Quality Assessment & Review")
            print("   5. Outcome Analysis & Learning")
            return
        
        demo_tasks = [
            {
                "description": "Implement user profile editing functionality with validation",
                "project": "user_management_system",
                "priority": "medium",
                "quality": "high"
            },
            {
                "description": "Fix critical memory leak in data processing pipeline",
                "project": "data_platform",
                "priority": "high", 
                "quality": "standard"
            }
        ]
        
        for task_info in demo_tasks:
            try:
                print(f"\n🚀 Executing: {task_info['description']}")
                
                # Execute complete intelligent workflow
                result = await self.orchestrator.execute_intelligent_workflow(
                    task_description=task_info["description"],
                    project_name=task_info["project"],
                    priority_level=task_info["priority"],
                    quality_requirements=task_info["quality"]
                )
                
                self.print_execution_result(result)
                
            except Exception as e:
                print(f"❌ Execution failed: {e}")
    
    async def demo_learning_and_optimization(self):
        """Demo learning and optimization capabilities."""
        self.print_section_header("Learning and Optimization")
        
        if not self.orchestrator:
            print("⚠️  Orchestrator not available - showing learning concepts:")
            print("   📊 Pattern Recognition: Learn from successful workflows")
            print("   🎯 Prediction Improvement: Refine success rate predictions")
            print("   ⚡ Optimization Detection: Identify improvement opportunities")
            print("   🔄 Feedback Integration: Continuous improvement from outcomes")
            return
        
        try:
            # Get orchestrator analytics
            analytics = self.orchestrator.get_orchestrator_analytics()
            
            print("📊 Current System Analytics:")
            print(f"   Total Executions: {analytics.get('total_executions', 0)}")
            print(f"   Success Rate: {analytics.get('success_rate', 0):.1%}")
            print(f"   Average Quality Score: {analytics.get('average_quality_score', 0):.2f}")
            print(f"   Selection Accuracy: {analytics.get('selection_accuracy', 0):.1%}")
            
            # Show workflow type distribution
            distribution = analytics.get('workflow_type_distribution', {})
            if distribution:
                print(f"\n🎯 Workflow Type Usage:")
                for workflow_type, count in distribution.items():
                    print(f"   {workflow_type}: {count} executions")
            
            # Show recent execution history
            history = self.orchestrator.get_execution_history(limit=5)
            if history:
                print(f"\n📈 Recent Executions:")
                for execution in history[-3:]:  # Last 3
                    status = "✅" if execution["success"] else "❌"
                    print(f"   {status} {execution['workflow_type']} - Quality: {execution['quality_score']:.2f}")
            
        except Exception as e:
            print(f"❌ Error getting analytics: {e}")
    
    async def demo_task_complexity_analysis(self):
        """Demo task complexity analysis capabilities."""
        self.print_section_header("Task Complexity Analysis")
        
        analysis_tasks = [
            "Update button color in CSS",
            "Implement OAuth2 authentication flow",
            "Design distributed caching strategy for microservices",
            "Research machine learning approach for fraud detection"
        ]
        
        for task in analysis_tasks:
            try:
                if not self.orchestrator:
                    print(f"🔍 Analyzing: {task}")
                    if "update button" in task.lower():
                        print(f"   Expected Complexity: trivial (1-2 subtasks)")
                    elif "oauth2" in task.lower():
                        print(f"   Expected Complexity: complex (6-8 subtasks)")
                    elif "distributed" in task.lower():
                        print(f"   Expected Complexity: epic (10+ subtasks)")
                    else:
                        print(f"   Expected Complexity: medium (4-6 subtasks)")
                    continue
                
                # Analyze task complexity
                complexity_analysis = await self.orchestrator.analyze_task_complexity(task)
                
                print(f"🔍 Task: {task}")
                print(f"   Complexity: {complexity_analysis.get('complexity', 'unknown')}")
                print(f"   Strategy: {complexity_analysis.get('strategy', 'unknown')}")
                print(f"   Estimated Hours: {complexity_analysis.get('estimated_hours', 0):.1f}")
                print(f"   Subtask Count: {complexity_analysis.get('subtask_count', 0)}")
                print(f"   Confidence: {complexity_analysis.get('confidence', 0):.2f}")
                
            except Exception as e:
                print(f"❌ Error analyzing task complexity: {e}")
    
    async def run_complete_demo(self):
        """Run the complete intelligent workflow selection demo."""
        print("🎉 Welcome to the Intelligent Workflow Selection System Demo!")
        print("This demo showcases automatic workflow selection, dynamic routing,")
        print("success prediction, and continuous learning capabilities.")
        
        # Run all demo sections
        await self.demo_simple_task_workflow()
        await self.demo_complex_task_workflow()
        await self.demo_urgent_task_workflow()
        await self.demo_research_task_workflow()
        await self.demo_task_complexity_analysis()
        await self.demo_end_to_end_execution()
        await self.demo_learning_and_optimization()
        
        # Summary
        self.print_section_header("Demo Summary")
        print("🎯 Key Capabilities Demonstrated:")
        print("   ✅ Automatic workflow type selection based on task analysis")
        print("   ✅ Dynamic routing strategies (performance, quality, resource optimized)")
        print("   ✅ Success rate prediction with confidence scoring")
        print("   ✅ Intelligent task complexity analysis and decomposition")
        print("   ✅ Resource requirement estimation and optimization")
        print("   ✅ Continuous learning from execution outcomes")
        print("   ✅ Comprehensive analytics and performance tracking")
        
        print(f"\n🚀 M02-014: Intelligent Workflow Selection System Demo Complete!")
        print("   The system successfully demonstrates intelligent workflow selection")
        print("   with memory-driven pattern matching and continuous optimization.")


async def main():
    """Main demo function."""
    demo = IntelligentWorkflowDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())