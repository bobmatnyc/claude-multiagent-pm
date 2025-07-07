"""
Orchestrator Agent Node Implementation

Multi-agent coordination specialist that manages task decomposition,
agent assignment, and workflow orchestration with memory-driven decisions.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from .base import BaseAgentNode, AgentExecutionContext, AgentNodeResult
from ..states.base import TaskState, TaskComplexity, AgentMessage
from ...core.logging_config import get_logger

logger = get_logger(__name__)


class OrchestratorNode(BaseAgentNode):
    """
    Orchestrator agent node for multi-agent coordination.
    
    Responsibilities:
    - Task complexity analysis and routing decisions
    - Agent assignment and resource allocation
    - Workflow coordination and conflict resolution
    - Multi-agent communication management
    - Memory-driven optimization of agent assignments
    """
    
    def __init__(self, 
                 agent_id: str = "orchestrator_agent",
                 memory_client=None,
                 config: Optional[Dict] = None):
        """
        Initialize Orchestrator agent node.
        
        Args:
            agent_id: Unique identifier for this agent instance
            memory_client: Optional mem0AI client for memory operations
            config: Optional configuration for orchestration parameters
        """
        super().__init__(
            agent_id=agent_id,
            role="orchestrator", 
            memory_client=memory_client,
            config=config
        )
        
        # Orchestration configuration
        self.orchestration_config = {
            "max_parallel_agents": 5,
            "complexity_thresholds": {
                "simple": {"keywords": ["fix", "update", "rename", "comment"], "max_agents": 2},
                "standard": {"keywords": ["implement", "add", "create"], "max_agents": 3}, 
                "complex": {"keywords": ["refactor", "migrate", "redesign", "optimize"], "max_agents": 5}
            },
            "agent_priorities": {
                "architect": 1,
                "engineer": 2, 
                "qa": 3,
                "researcher": 4,
                "code_review": 0  # Highest priority for quality
            },
            "memory_weight": 0.3,  # Weight for memory-based decisions
            **self.config.get("orchestration", {})
        }
    
    async def _execute_agent_logic(self, 
                                 context: AgentExecutionContext, 
                                 state: TaskState) -> AgentNodeResult:
        """
        Execute orchestrator logic for task analysis and agent coordination.
        
        Args:
            context: Execution context with memory and configuration
            state: Current workflow state
            
        Returns:
            AgentNodeResult with orchestration decisions
        """
        logger.info(f"Starting orchestration for task: {context.task_description}")
        
        # Analyze task complexity
        complexity_analysis = await self._analyze_task_complexity(context, state)
        
        # Determine required agents based on complexity and memory patterns
        agent_assignments = await self._determine_agent_assignments(
            context, complexity_analysis
        )
        
        # Plan execution strategy
        execution_plan = await self._plan_execution_strategy(
            context, complexity_analysis, agent_assignments
        )
        
        # Estimate costs and timeline
        cost_estimation = await self._estimate_costs_and_timeline(
            context, complexity_analysis, agent_assignments
        )
        
        # Check if human approval is required
        approval_required = self._requires_human_approval(
            complexity_analysis, cost_estimation
        )
        
        # Generate orchestration metadata
        orchestration_metadata = {
            "complexity_analysis": complexity_analysis,
            "agent_assignments": agent_assignments,
            "execution_plan": execution_plan,
            "cost_estimation": cost_estimation,
            "approval_required": approval_required,
            "orchestration_confidence": self._calculate_orchestration_confidence(
                complexity_analysis, agent_assignments
            )
        }
        
        return AgentNodeResult(
            status="completed",
            agent_id=self.agent_id,
            role=self.role,
            content=self._format_orchestration_summary(orchestration_metadata),
            metadata=orchestration_metadata,
            execution_time_ms=0,  # Will be set by base class
            confidence=orchestration_metadata["orchestration_confidence"],
            citations=self._extract_orchestration_citations(context),
            errors=[]
        )
    
    async def _analyze_task_complexity(self, 
                                     context: AgentExecutionContext,
                                     state: TaskState) -> Dict[str, Any]:
        """
        Analyze task complexity using heuristics and memory patterns.
        
        Args:
            context: Execution context
            state: Current workflow state
            
        Returns:
            Dict containing complexity analysis results
        """
        task_description = context.task_description.lower()
        
        # Keyword-based analysis
        complexity_scores = {}
        for complexity, config in self.orchestration_config["complexity_thresholds"].items():
            keyword_matches = sum(1 for keyword in config["keywords"] if keyword in task_description)
            complexity_scores[complexity] = keyword_matches
        
        # Determine base complexity
        base_complexity = max(complexity_scores, key=complexity_scores.get)
        if all(score == 0 for score in complexity_scores.values()):
            base_complexity = "standard"  # Default complexity
        
        # Memory-augmented complexity adjustment
        memory_adjustment = await self._get_memory_complexity_adjustment(context)
        
        # Final complexity determination
        final_complexity = self._adjust_complexity_with_memory(
            base_complexity, memory_adjustment
        )
        
        # Additional analysis factors
        task_length = len(context.task_description)
        has_security_implications = any(
            keyword in task_description 
            for keyword in ["security", "auth", "password", "encrypt", "permission"]
        )
        has_performance_implications = any(
            keyword in task_description
            for keyword in ["performance", "optimize", "scale", "cache", "query"]
        )
        
        return {
            "complexity": final_complexity,
            "base_complexity": base_complexity,
            "memory_adjustment": memory_adjustment,
            "keyword_scores": complexity_scores,
            "task_length": task_length,
            "security_implications": has_security_implications,
            "performance_implications": has_performance_implications,
            "estimated_effort_hours": self._estimate_effort_hours(final_complexity),
            "risk_factors": self._identify_risk_factors(task_description)
        }
    
    async def _determine_agent_assignments(self, 
                                         context: AgentExecutionContext,
                                         complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine which agents should be assigned based on complexity and memory patterns.
        
        Args:
            context: Execution context
            complexity_analysis: Results from complexity analysis
            
        Returns:
            Dict containing agent assignment decisions
        """
        complexity = complexity_analysis["complexity"]
        required_agents = []
        
        # Base agent requirements by complexity
        if complexity == "simple":
            required_agents = ["engineer", "qa"]
        elif complexity == "standard":
            required_agents = ["architect", "engineer", "qa"]
        elif complexity == "complex":
            required_agents = ["architect", "engineer", "qa", "researcher"]
        
        # Add specialized agents based on task characteristics
        if complexity_analysis["security_implications"]:
            required_agents.append("code_review")
        
        if complexity_analysis["performance_implications"]:
            if "researcher" not in required_agents:
                required_agents.append("researcher")
        
        # Memory-based agent optimization
        memory_recommendations = await self._get_memory_agent_recommendations(
            context, complexity_analysis
        )
        
        # Apply memory recommendations
        optimized_agents = self._optimize_agent_assignments(
            required_agents, memory_recommendations
        )
        
        # Determine execution order and dependencies
        execution_order = self._determine_execution_order(optimized_agents)
        
        return {
            "assigned_agents": optimized_agents,
            "execution_order": execution_order,
            "agent_roles": {agent: self._get_agent_role_description(agent) for agent in optimized_agents},
            "memory_recommendations": memory_recommendations,
            "parallel_groups": self._identify_parallel_groups(optimized_agents),
            "estimated_agent_hours": {
                agent: self._estimate_agent_hours(agent, complexity) 
                for agent in optimized_agents
            }
        }
    
    async def _plan_execution_strategy(self, 
                                     context: AgentExecutionContext,
                                     complexity_analysis: Dict[str, Any],
                                     agent_assignments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan the execution strategy for the assigned agents.
        
        Args:
            context: Execution context
            complexity_analysis: Complexity analysis results
            agent_assignments: Agent assignment decisions
            
        Returns:
            Dict containing execution strategy
        """
        # Determine execution phases
        phases = self._plan_execution_phases(agent_assignments["execution_order"])
        
        # Identify dependencies and blockers
        dependencies = self._identify_agent_dependencies(agent_assignments["assigned_agents"])
        
        # Plan parallel execution opportunities
        parallel_opportunities = self._identify_parallel_opportunities(
            agent_assignments["parallel_groups"]
        )
        
        # Determine checkpoints and milestones
        checkpoints = self._plan_checkpoints(phases, complexity_analysis["complexity"])
        
        # Risk mitigation strategies
        risk_mitigation = self._plan_risk_mitigation(
            complexity_analysis["risk_factors"],
            agent_assignments["assigned_agents"]
        )
        
        return {
            "execution_phases": phases,
            "dependencies": dependencies,
            "parallel_opportunities": parallel_opportunities,
            "checkpoints": checkpoints,
            "risk_mitigation": risk_mitigation,
            "estimated_total_duration": self._estimate_total_duration(phases),
            "quality_gates": self._define_quality_gates(complexity_analysis["complexity"])
        }
    
    async def _estimate_costs_and_timeline(self, 
                                         context: AgentExecutionContext,
                                         complexity_analysis: Dict[str, Any],
                                         agent_assignments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate costs and timeline for the orchestrated execution.
        
        Args:
            context: Execution context
            complexity_analysis: Complexity analysis results
            agent_assignments: Agent assignment decisions
            
        Returns:
            Dict containing cost and timeline estimates
        """
        # Base cost estimates by agent type
        agent_hourly_costs = {
            "architect": 0.15,
            "engineer": 0.12,
            "qa": 0.10,
            "researcher": 0.08,
            "code_review": 0.14
        }
        
        # Calculate cost by agent
        agent_costs = {}
        total_cost = 0.0
        
        for agent in agent_assignments["assigned_agents"]:
            hours = agent_assignments["estimated_agent_hours"].get(agent, 1.0)
            hourly_rate = agent_hourly_costs.get(agent, 0.10)
            agent_cost = hours * hourly_rate
            agent_costs[agent] = agent_cost
            total_cost += agent_cost
        
        # Timeline estimation
        sequential_hours = sum(agent_assignments["estimated_agent_hours"].values())
        parallel_hours = self._calculate_parallel_duration(
            agent_assignments["parallel_groups"],
            agent_assignments["estimated_agent_hours"]
        )
        
        return {
            "total_estimated_cost_usd": round(total_cost, 3),
            "agent_costs": agent_costs,
            "sequential_duration_hours": sequential_hours,
            "parallel_duration_hours": parallel_hours,
            "estimated_completion_time": datetime.now().isoformat(),
            "cost_confidence": 0.8,
            "timeline_confidence": 0.7,
            "cost_breakdown": {
                "agent_execution": total_cost * 0.8,
                "coordination_overhead": total_cost * 0.1,
                "quality_assurance": total_cost * 0.1
            }
        }
    
    def _requires_human_approval(self, 
                               complexity_analysis: Dict[str, Any],
                               cost_estimation: Dict[str, Any]) -> bool:
        """Determine if human approval is required."""
        # Require approval for complex tasks
        if complexity_analysis["complexity"] == "complex":
            return True
        
        # Require approval for high-cost tasks
        if cost_estimation["total_estimated_cost_usd"] > 0.50:
            return True
        
        # Require approval for security-sensitive tasks
        if complexity_analysis["security_implications"]:
            return True
        
        # Require approval for high-risk tasks
        if len(complexity_analysis["risk_factors"]) > 2:
            return True
        
        return False
    
    def _calculate_orchestration_confidence(self, 
                                          complexity_analysis: Dict[str, Any],
                                          agent_assignments: Dict[str, Any]) -> float:
        """Calculate confidence in orchestration decisions."""
        confidence_factors = []
        
        # Base confidence from complexity analysis
        complexity_confidence = {
            "simple": 0.9,
            "standard": 0.8,
            "complex": 0.7
        }.get(complexity_analysis["complexity"], 0.8)
        confidence_factors.append(complexity_confidence)
        
        # Memory-based confidence
        memory_recommendations = agent_assignments.get("memory_recommendations", [])
        if memory_recommendations:
            memory_confidence = min(0.9, 0.6 + len(memory_recommendations) * 0.1)
            confidence_factors.append(memory_confidence)
        
        # Agent assignment confidence
        assigned_count = len(agent_assignments["assigned_agents"])
        assignment_confidence = min(0.9, 0.5 + assigned_count * 0.1)
        confidence_factors.append(assignment_confidence)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def _format_orchestration_summary(self, metadata: Dict[str, Any]) -> str:
        """Format orchestration results into human-readable summary."""
        complexity = metadata["complexity_analysis"]["complexity"]
        agents = metadata["agent_assignments"]["assigned_agents"]
        cost = metadata["cost_estimation"]["total_estimated_cost_usd"]
        duration = metadata["cost_estimation"]["parallel_duration_hours"]
        
        summary_lines = [
            f"Task Orchestration Complete",
            f"Complexity: {complexity.title()}",
            f"Assigned Agents: {', '.join(agents)}",
            f"Estimated Cost: ${cost:.3f}",
            f"Estimated Duration: {duration:.1f} hours",
            ""
        ]
        
        if metadata["approval_required"]:
            summary_lines.append("⚠️  Human approval required")
        
        if metadata["complexity_analysis"]["security_implications"]:
            summary_lines.append("🔒 Security review included")
        
        if metadata["complexity_analysis"]["performance_implications"]:
            summary_lines.append("⚡ Performance optimization considered")
        
        return "\n".join(summary_lines)
    
    # Helper methods (implementation details)
    async def _get_memory_complexity_adjustment(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """Get complexity adjustment recommendations from memory."""
        # Placeholder - implement with mem0AI
        return {"adjustment": 0, "confidence": 0.5, "patterns": []}
    
    async def _get_memory_agent_recommendations(self, 
                                              context: AgentExecutionContext,
                                              complexity_analysis: Dict[str, Any]) -> List[Dict]:
        """Get agent assignment recommendations from memory."""
        # Placeholder - implement with mem0AI
        return []
    
    def _adjust_complexity_with_memory(self, base_complexity: str, memory_adjustment: Dict) -> str:
        """Adjust complexity based on memory patterns."""
        # Simple implementation - extend with actual memory logic
        return base_complexity
    
    def _estimate_effort_hours(self, complexity: str) -> float:
        """Estimate effort hours based on complexity."""
        return {"simple": 1.0, "standard": 3.0, "complex": 8.0}.get(complexity, 3.0)
    
    def _identify_risk_factors(self, task_description: str) -> List[str]:
        """Identify risk factors in task description."""
        risk_keywords = {
            "data_loss": ["delete", "remove", "drop", "truncate"],
            "breaking_change": ["breaking", "incompatible", "major"],
            "security": ["security", "vulnerability", "exploit"],
            "performance": ["performance", "slow", "timeout", "bottleneck"]
        }
        
        risks = []
        for risk_type, keywords in risk_keywords.items():
            if any(keyword in task_description.lower() for keyword in keywords):
                risks.append(risk_type)
        
        return risks
    
    def _optimize_agent_assignments(self, base_agents: List[str], memory_recs: List[Dict]) -> List[str]:
        """Optimize agent assignments based on memory recommendations."""
        # Simple implementation - extend with memory-based optimization
        return list(set(base_agents))  # Remove duplicates
    
    def _determine_execution_order(self, agents: List[str]) -> List[str]:
        """Determine optimal execution order for agents."""
        # Priority-based ordering
        priority_order = ["architect", "engineer", "qa", "code_review", "researcher"]
        return sorted(agents, key=lambda x: priority_order.index(x) if x in priority_order else 999)
    
    def _get_agent_role_description(self, agent: str) -> str:
        """Get role description for agent."""
        descriptions = {
            "architect": "System design and API specifications",
            "engineer": "Source code implementation",
            "qa": "Testing and quality assurance",
            "researcher": "Research and best practices",
            "code_review": "Multi-dimensional code review"
        }
        return descriptions.get(agent, "Unknown role")
    
    def _identify_parallel_groups(self, agents: List[str]) -> List[List[str]]:
        """Identify which agents can run in parallel."""
        # Simple grouping - extend with dependency analysis
        if "architect" in agents:
            return [["architect"], [a for a in agents if a != "architect"]]
        else:
            return [agents]
    
    def _estimate_agent_hours(self, agent: str, complexity: str) -> float:
        """Estimate hours for specific agent based on complexity."""
        base_hours = {
            "simple": {"architect": 0.5, "engineer": 1.0, "qa": 0.5, "researcher": 0.25, "code_review": 0.25},
            "standard": {"architect": 1.0, "engineer": 2.0, "qa": 1.0, "researcher": 0.5, "code_review": 0.5},
            "complex": {"architect": 2.0, "engineer": 4.0, "qa": 2.0, "researcher": 1.0, "code_review": 1.0}
        }
        return base_hours.get(complexity, {}).get(agent, 1.0)
    
    def _plan_execution_phases(self, execution_order: List[str]) -> List[Dict[str, Any]]:
        """Plan execution phases based on agent order."""
        phases = []
        for i, agent in enumerate(execution_order):
            phases.append({
                "phase": i + 1,
                "agent": agent,
                "description": f"{self._get_agent_role_description(agent)}",
                "dependencies": execution_order[:i] if i > 0 else []
            })
        return phases
    
    def _identify_agent_dependencies(self, agents: List[str]) -> Dict[str, List[str]]:
        """Identify dependencies between agents."""
        dependencies = {}
        if "architect" in agents:
            for agent in ["engineer", "qa"]:
                if agent in agents:
                    dependencies[agent] = ["architect"]
        if "engineer" in agents and "qa" in agents:
            dependencies["qa"] = dependencies.get("qa", []) + ["engineer"]
        return dependencies
    
    def _identify_parallel_opportunities(self, parallel_groups: List[List[str]]) -> List[Dict[str, Any]]:
        """Identify opportunities for parallel execution."""
        opportunities = []
        for i, group in enumerate(parallel_groups):
            if len(group) > 1:
                opportunities.append({
                    "group_id": i,
                    "agents": group,
                    "estimated_speedup": len(group) * 0.7  # Assuming 70% efficiency
                })
        return opportunities
    
    def _plan_checkpoints(self, phases: List[Dict], complexity: str) -> List[Dict[str, Any]]:
        """Plan checkpoints and milestones."""
        checkpoints = []
        checkpoint_phases = {
            "simple": [len(phases)],
            "standard": [len(phases) // 2, len(phases)],
            "complex": [len(phases) // 3, 2 * len(phases) // 3, len(phases)]
        }.get(complexity, [len(phases)])
        
        for i, phase_num in enumerate(checkpoint_phases):
            checkpoints.append({
                "checkpoint_id": i + 1,
                "after_phase": min(phase_num, len(phases)),
                "description": f"Milestone {i + 1}",
                "success_criteria": f"Phase {phase_num} completed successfully"
            })
        
        return checkpoints
    
    def _plan_risk_mitigation(self, risk_factors: List[str], agents: List[str]) -> List[Dict[str, Any]]:
        """Plan risk mitigation strategies."""
        mitigation_strategies = []
        
        for risk in risk_factors:
            if risk == "security" and "code_review" not in agents:
                mitigation_strategies.append({
                    "risk": risk,
                    "strategy": "Add security-focused code review",
                    "implementation": "Include code_review agent"
                })
        
        return mitigation_strategies
    
    def _estimate_total_duration(self, phases: List[Dict]) -> float:
        """Estimate total duration considering dependencies."""
        return len(phases) * 1.5  # Rough estimate
    
    def _define_quality_gates(self, complexity: str) -> List[Dict[str, Any]]:
        """Define quality gates based on complexity."""
        base_gates = [
            {"gate": "code_review", "criteria": "All critical issues resolved"},
            {"gate": "testing", "criteria": "Minimum test coverage achieved"},
        ]
        
        if complexity == "complex":
            base_gates.insert(0, {"gate": "architecture_review", "criteria": "Design approved"})
        
        return base_gates
    
    def _calculate_parallel_duration(self, parallel_groups: List[List[str]], agent_hours: Dict[str, float]) -> float:
        """Calculate duration considering parallel execution."""
        total_duration = 0.0
        
        for group in parallel_groups:
            if len(group) == 1:
                total_duration += agent_hours.get(group[0], 1.0)
            else:
                # Parallel execution - use maximum duration in group
                group_max = max(agent_hours.get(agent, 1.0) for agent in group)
                total_duration += group_max
        
        return total_duration
    
    def _extract_orchestration_citations(self, context: AgentExecutionContext) -> List[str]:
        """Extract citations for orchestration decisions."""
        citations = []
        
        # Add memory-based citations
        memory_context = context.memory_context
        if "relevant_memories" in memory_context:
            for memory in memory_context["relevant_memories"]:
                if "source" in memory:
                    citations.append(memory["source"])
        
        return citations