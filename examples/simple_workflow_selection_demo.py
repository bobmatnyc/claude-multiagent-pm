#!/usr/bin/env python3
"""
Simple Intelligent Workflow Selection Demo

This demo showcases the core concepts and capabilities of the M02-014
Intelligent Workflow Selection System without complex dependencies.
"""

from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


class WorkflowType(str, Enum):
    """Available workflow types."""
    SIMPLE_LINEAR = "simple_linear"
    PARALLEL_MULTI_AGENT = "parallel_multi_agent"
    HIERARCHICAL_REVIEW = "hierarchical_review"
    ITERATIVE_REFINEMENT = "iterative_refinement"
    RESEARCH_DISCOVERY = "research_discovery"
    CRITICAL_PATH = "critical_path"
    EMERGENCY_FAST_TRACK = "emergency_fast_track"


class RoutingStrategy(str, Enum):
    """Routing strategies."""
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    RESOURCE_OPTIMIZED = "resource_optimized"
    BALANCED = "balanced"
    LEARNING_OPTIMIZED = "learning_optimized"


@dataclass
class WorkflowRecommendation:
    """Workflow recommendation with reasoning."""
    workflow_type: WorkflowType
    confidence: float
    reasoning: str
    predicted_success_rate: float
    estimated_duration_minutes: int
    routing_strategy: RoutingStrategy
    risk_factors: List[str]
    optimization_opportunities: List[str]


class SimpleWorkflowSelector:
    """Simplified workflow selector for demonstration."""
    
    def __init__(self):
        self.selection_rules = {
            "simple_keywords": ["typo", "update", "fix", "change", "simple"],
            "complex_keywords": ["design", "implement", "architecture", "system", "migrate"],
            "urgent_keywords": ["critical", "emergency", "urgent", "production", "bug"],
            "research_keywords": ["research", "analyze", "investigate", "explore", "study"]
        }
    
    def select_workflow(self, task_description: str, priority: str = "medium", 
                       deadline: Optional[datetime] = None) -> WorkflowRecommendation:
        """Select optimal workflow based on task characteristics."""
        
        task_lower = task_description.lower()
        
        # Check for urgent tasks
        if priority in ["critical", "high"] or any(keyword in task_lower for keyword in self.selection_rules["urgent_keywords"]):
            return WorkflowRecommendation(
                workflow_type=WorkflowType.EMERGENCY_FAST_TRACK,
                confidence=0.9,
                reasoning="Urgent task requires fast-track workflow",
                predicted_success_rate=0.8,
                estimated_duration_minutes=20,
                routing_strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
                risk_factors=["Time pressure may compromise quality"],
                optimization_opportunities=["Focus on MVP approach"]
            )
        
        # Check for research tasks
        if any(keyword in task_lower for keyword in self.selection_rules["research_keywords"]):
            return WorkflowRecommendation(
                workflow_type=WorkflowType.RESEARCH_DISCOVERY,
                confidence=0.85,
                reasoning="Research task requires discovery-focused workflow",
                predicted_success_rate=0.75,
                estimated_duration_minutes=90,
                routing_strategy=RoutingStrategy.LEARNING_OPTIMIZED,
                risk_factors=["Scope uncertainty"],
                optimization_opportunities=["Set clear research boundaries"]
            )
        
        # Check for complex tasks
        if any(keyword in task_lower for keyword in self.selection_rules["complex_keywords"]):
            return WorkflowRecommendation(
                workflow_type=WorkflowType.HIERARCHICAL_REVIEW,
                confidence=0.8,
                reasoning="Complex task benefits from hierarchical review",
                predicted_success_rate=0.85,
                estimated_duration_minutes=120,
                routing_strategy=RoutingStrategy.QUALITY_OPTIMIZED,
                risk_factors=["High complexity may lead to scope creep"],
                optimization_opportunities=["Implement early feedback loops"]
            )
        
        # Check for simple tasks
        if any(keyword in task_lower for keyword in self.selection_rules["simple_keywords"]):
            return WorkflowRecommendation(
                workflow_type=WorkflowType.SIMPLE_LINEAR,
                confidence=0.9,
                reasoning="Simple task suitable for linear workflow",
                predicted_success_rate=0.95,
                estimated_duration_minutes=15,
                routing_strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
                risk_factors=[],
                optimization_opportunities=["Consider automation for similar tasks"]
            )
        
        # Default: parallel multi-agent
        return WorkflowRecommendation(
            workflow_type=WorkflowType.PARALLEL_MULTI_AGENT,
            confidence=0.7,
            reasoning="Standard task suitable for parallel execution",
            predicted_success_rate=0.8,
            estimated_duration_minutes=60,
            routing_strategy=RoutingStrategy.BALANCED,
            risk_factors=["Coordination overhead"],
            optimization_opportunities=["Consider task decomposition"]
        )


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print('='*60)


def print_recommendation(task: str, recommendation: WorkflowRecommendation):
    """Print formatted workflow recommendation."""
    print(f"\n🎯 Task: {task}")
    print(f"   ✅ Selected Workflow: {recommendation.workflow_type.value}")
    print(f"   🎯 Confidence: {recommendation.confidence:.2f}")
    print(f"   🚀 Strategy: {recommendation.routing_strategy.value}")
    print(f"   📊 Success Rate: {recommendation.predicted_success_rate:.1%}")
    print(f"   ⏱️  Duration: {recommendation.estimated_duration_minutes} minutes")
    print(f"   💭 Reasoning: {recommendation.reasoning}")
    
    if recommendation.risk_factors:
        print(f"   ⚠️  Risks: {', '.join(recommendation.risk_factors)}")
    
    if recommendation.optimization_opportunities:
        print(f"   💡 Optimizations: {', '.join(recommendation.optimization_opportunities)}")


def demo_simple_tasks():
    """Demo simple task workflow selection."""
    print_section("Simple Task Workflow Selection")
    
    selector = SimpleWorkflowSelector()
    
    simple_tasks = [
        "Fix a typo in the README file",
        "Update the copyright year in documentation", 
        "Change button color from blue to green",
        "Simple CSS style adjustment for mobile"
    ]
    
    for task in simple_tasks:
        recommendation = selector.select_workflow(task, priority="low")
        print_recommendation(task, recommendation)


def demo_complex_tasks():
    """Demo complex task workflow selection."""
    print_section("Complex Task Workflow Selection")
    
    selector = SimpleWorkflowSelector()
    
    complex_tasks = [
        "Design and implement a new microservice architecture",
        "Migrate database from MySQL to PostgreSQL",
        "Implement distributed caching system",
        "Create comprehensive API documentation system"
    ]
    
    for task in complex_tasks:
        recommendation = selector.select_workflow(task, priority="medium")
        print_recommendation(task, recommendation)


def demo_urgent_tasks():
    """Demo urgent task workflow selection."""
    print_section("Urgent Task Workflow Selection")
    
    selector = SimpleWorkflowSelector()
    
    urgent_tasks = [
        "Critical production bug causing 500 errors",
        "Emergency security vulnerability patch",
        "Urgent customer-facing feature repair",
        "High priority database performance issue"
    ]
    
    for task in urgent_tasks:
        recommendation = selector.select_workflow(task, priority="critical")
        print_recommendation(task, recommendation)


def demo_research_tasks():
    """Demo research task workflow selection."""
    print_section("Research Task Workflow Selection")
    
    selector = SimpleWorkflowSelector()
    
    research_tasks = [
        "Research feasibility of migrating to Kubernetes",
        "Analyze performance bottlenecks in recommendation engine",
        "Investigate integration options with payment providers",
        "Study user behavior patterns for UX improvements"
    ]
    
    for task in research_tasks:
        recommendation = selector.select_workflow(task, priority="medium")
        print_recommendation(task, recommendation)


def demo_mixed_scenarios():
    """Demo mixed real-world scenarios."""
    print_section("Mixed Real-World Scenarios")
    
    selector = SimpleWorkflowSelector()
    
    scenarios = [
        ("Implement user authentication with OAuth2", "high"),
        ("Update API documentation for new endpoints", "low"),
        ("Research machine learning fraud detection approach", "medium"), 
        ("Critical memory leak in data processing pipeline", "critical"),
        ("Design scalable notification system architecture", "medium")
    ]
    
    for task, priority in scenarios:
        recommendation = selector.select_workflow(task, priority=priority)
        print_recommendation(task, recommendation)


def demo_workflow_characteristics():
    """Demo workflow type characteristics."""
    print_section("Workflow Type Characteristics")
    
    characteristics = {
        WorkflowType.SIMPLE_LINEAR: {
            "description": "Sequential execution with minimal overhead",
            "best_for": ["Small fixes", "Simple updates", "Quick tasks"],
            "agents": "1-2",
            "duration": "5-30 minutes"
        },
        WorkflowType.EMERGENCY_FAST_TRACK: {
            "description": "Minimized overhead for urgent tasks",
            "best_for": ["Critical bugs", "Security issues", "Production problems"],
            "agents": "1",
            "duration": "10-60 minutes"
        },
        WorkflowType.PARALLEL_MULTI_AGENT: {
            "description": "Concurrent execution with multiple agents",
            "best_for": ["Independent features", "Parallel development", "Team tasks"],
            "agents": "3-4",
            "duration": "30-120 minutes"
        },
        WorkflowType.HIERARCHICAL_REVIEW: {
            "description": "Multi-stage execution with review gates",
            "best_for": ["Quality-critical tasks", "Complex implementations", "High-risk changes"],
            "agents": "4-6",
            "duration": "60-180 minutes"
        },
        WorkflowType.RESEARCH_DISCOVERY: {
            "description": "Research-first approach with knowledge capture",
            "best_for": ["Unknown territory", "Technology evaluation", "Feasibility studies"],
            "agents": "2-3",
            "duration": "45-150 minutes"
        },
        WorkflowType.ITERATIVE_REFINEMENT: {
            "description": "Agile approach with feedback cycles",
            "best_for": ["MVP development", "Iterative improvement", "User feedback integration"],
            "agents": "2-4",
            "duration": "60-200 minutes"
        },
        WorkflowType.CRITICAL_PATH: {
            "description": "Dependencies-optimized execution",
            "best_for": ["Complex dependencies", "Resource constraints", "Timeline optimization"],
            "agents": "4-6",
            "duration": "90-240 minutes"
        }
    }
    
    for workflow_type, info in characteristics.items():
        print(f"\n🔧 {workflow_type.value.upper()}")
        print(f"   📝 {info['description']}")
        print(f"   🎯 Best for: {', '.join(info['best_for'])}")
        print(f"   👥 Agents: {info['agents']}")
        print(f"   ⏱️  Duration: {info['duration']}")


def main():
    """Run the complete workflow selection demo."""
    print("🎉 Welcome to the Intelligent Workflow Selection System Demo!")
    print("This demo showcases how the system automatically selects optimal")
    print("workflows based on task analysis and characteristics.")
    
    demo_simple_tasks()
    demo_complex_tasks() 
    demo_urgent_tasks()
    demo_research_tasks()
    demo_mixed_scenarios()
    demo_workflow_characteristics()
    
    print_section("Demo Summary")
    print("🎯 Key Capabilities Demonstrated:")
    print("   ✅ Automatic workflow type selection based on task keywords")
    print("   ✅ Dynamic routing strategies (performance, quality, balanced)")
    print("   ✅ Success rate prediction with confidence scoring")
    print("   ✅ Risk assessment and optimization opportunity identification")
    print("   ✅ Appropriate resource allocation per workflow type")
    print("   ✅ Context-aware reasoning for workflow selection decisions")
    
    print(f"\n🚀 M02-014: Intelligent Workflow Selection System Demo Complete!")
    print("   This simplified demo shows the core intelligence of the full system.")
    print("   The actual implementation includes memory-driven pattern matching,")
    print("   continuous learning, and integration with the Claude PM Framework.")


if __name__ == "__main__":
    main()