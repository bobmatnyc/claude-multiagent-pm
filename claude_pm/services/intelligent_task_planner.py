"""
IntelligentTaskPlanner - Memory-Driven Task Decomposition System
Implements MEM-005 for intelligent task planning and decomposition using mem0AI patterns.
"""

import asyncio
import json
import logging
import math
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .claude_pm_memory import ClaudePMMemory, MemoryCategory, MemoryResponse
from .mem0_context_manager import Mem0ContextManager, ContextRequest, ContextType, ContextScope
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class TaskComplexity(str, Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EPIC = "epic"


class DecompositionStrategy(str, Enum):
    """Task decomposition strategies."""
    LINEAR = "linear"           # Sequential step-by-step
    PARALLEL = "parallel"       # Concurrent subtasks
    HIERARCHICAL = "hierarchical"  # Tree-like decomposition
    ITERATIVE = "iterative"     # Agile sprint-style
    EXPLORATORY = "exploratory" # Research-first approach


@dataclass
class TaskMetadata:
    """Metadata for task analysis."""
    domain: str = "general"
    technology_stack: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    estimated_hours: Optional[float] = None
    risk_factors: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class SubTask:
    """Individual subtask in a decomposition."""
    id: str
    title: str
    description: str
    complexity: TaskComplexity
    estimated_hours: float
    dependencies: List[str] = field(default_factory=list)
    skills_required: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high
    priority: int = 5  # 1-10 scale
    validation_steps: List[str] = field(default_factory=list)
    
    # Agent assignment fields
    assigned_agent_type: Optional[str] = None  # Agent type for this subtask
    agent_display_name: Optional[str] = None   # Display name for task prefixing
    
    # Memory-augmented fields
    similar_tasks: List[str] = field(default_factory=list)
    pattern_confidence: float = 0.0
    historical_success_rate: float = 0.0
    
    def get_task_prefix(self) -> str:
        """Get the agent prefix for this subtask."""
        if self.agent_display_name:
            return f"[{self.agent_display_name}]"
        elif self.assigned_agent_type:
            # Import here to avoid circular imports
            from ..core.enforcement import AgentDisplayNames
            return AgentDisplayNames.get_task_prefix(self.assigned_agent_type)
        return ""
    
    def get_prefixed_title(self) -> str:
        """Get the task title with agent prefix."""
        prefix = self.get_task_prefix()
        if prefix:
            return f"{prefix} {self.title}"
        return self.title
    
    def get_prefixed_description(self) -> str:
        """Get the task description with agent prefix."""
        prefix = self.get_task_prefix()
        if prefix:
            return f"{prefix} {self.description}"
        return self.description


@dataclass
class TaskDecomposition:
    """Complete task decomposition result."""
    original_task: str
    strategy: DecompositionStrategy
    complexity: TaskComplexity
    subtasks: List[SubTask]
    total_estimated_hours: float
    confidence_score: float
    decomposition_id: str
    created_at: datetime
    
    # Memory integration
    similar_decompositions: List[str] = field(default_factory=list)
    pattern_matches: List[Dict[str, Any]] = field(default_factory=list)
    memory_context_size: int = 0
    adaptation_notes: str = ""
    
    # Learning metrics
    complexity_prediction_confidence: float = 0.0
    strategy_selection_confidence: float = 0.0
    estimated_accuracy_score: float = 0.0


@dataclass
class SimilarTask:
    """Similar task found in memory."""
    task_id: str
    task_description: str
    similarity_score: float
    decomposition: Dict[str, Any]
    outcome: str  # success, partial, failure
    lessons_learned: List[str]
    complexity_actual: TaskComplexity
    hours_actual: float


class IntelligentTaskPlanner:
    """
    Memory-driven task decomposition system that uses historical patterns,
    team knowledge, and similarity detection for intelligent task planning.
    """
    
    def __init__(self, memory: ClaudePMMemory, context_manager: Mem0ContextManager):
        """
        Initialize the intelligent task planner.
        
        Args:
            memory: ClaudePMMemory instance for memory operations
            context_manager: Mem0ContextManager for context preparation
        """
        self.memory = memory
        self.context_manager = context_manager
        
        # Decomposition patterns and weights
        self.complexity_indicators = self._initialize_complexity_indicators()
        self.strategy_patterns = self._initialize_strategy_patterns()
        self.similarity_weights = self._initialize_similarity_weights()
        self.agent_assignment_patterns = self._initialize_agent_assignment_patterns()
        
        # Learning system
        self.decomposition_history: List[TaskDecomposition] = []
        self.performance_metrics = {
            "total_decompositions": 0,
            "accuracy_scores": [],
            "complexity_predictions": [],
            "strategy_effectiveness": {},
            "pattern_reuse_rate": 0.0
        }
        
        logger.info("IntelligentTaskPlanner initialized with memory integration")
    
    def _initialize_complexity_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Initialize complexity detection patterns."""
        return {
            "trivial": {
                "keywords": ["fix typo", "update text", "change color", "simple update"],
                "max_estimated_hours": 1,
                "typical_subtasks": 1,
                "complexity_score_range": (0.0, 0.2)
            },
            "simple": {
                "keywords": ["add button", "update function", "simple feature", "minor change"],
                "max_estimated_hours": 8,
                "typical_subtasks": 2-3,
                "complexity_score_range": (0.2, 0.4)
            },
            "medium": {
                "keywords": ["implement feature", "create component", "add integration", "refactor"],
                "max_estimated_hours": 24,
                "typical_subtasks": 3-6,
                "complexity_score_range": (0.4, 0.6)
            },
            "complex": {
                "keywords": ["design system", "architecture", "multi-service", "complex feature"],
                "max_estimated_hours": 80,
                "typical_subtasks": 6-12,
                "complexity_score_range": (0.6, 0.8)
            },
            "epic": {
                "keywords": ["platform", "migration", "complete rewrite", "major overhaul"],
                "max_estimated_hours": 200,
                "typical_subtasks": 10-25,
                "complexity_score_range": (0.8, 1.0)
            }
        }
    
    def _initialize_strategy_patterns(self) -> Dict[DecompositionStrategy, Dict[str, Any]]:
        """Initialize decomposition strategy patterns."""
        return {
            DecompositionStrategy.LINEAR: {
                "best_for": ["migration", "step-by-step", "sequential", "setup"],
                "complexity_preference": [TaskComplexity.SIMPLE, TaskComplexity.MEDIUM],
                "subtask_dependencies": "high",  # Many dependencies between subtasks
                "parallelization": "low"
            },
            DecompositionStrategy.PARALLEL: {
                "best_for": ["independent features", "team work", "concurrent development"],
                "complexity_preference": [TaskComplexity.MEDIUM, TaskComplexity.COMPLEX],
                "subtask_dependencies": "low",   # Few dependencies between subtasks
                "parallelization": "high"
            },
            DecompositionStrategy.HIERARCHICAL: {
                "best_for": ["architecture", "system design", "complex features"],
                "complexity_preference": [TaskComplexity.COMPLEX, TaskComplexity.EPIC],
                "subtask_dependencies": "medium",
                "parallelization": "medium"
            },
            DecompositionStrategy.ITERATIVE: {
                "best_for": ["agile development", "mvp", "iterative improvement"],
                "complexity_preference": [TaskComplexity.MEDIUM, TaskComplexity.COMPLEX],
                "subtask_dependencies": "medium",
                "parallelization": "medium"
            },
            DecompositionStrategy.EXPLORATORY: {
                "best_for": ["research", "poc", "unknown territory", "investigation"],
                "complexity_preference": [TaskComplexity.MEDIUM, TaskComplexity.COMPLEX, TaskComplexity.EPIC],
                "subtask_dependencies": "variable",
                "parallelization": "low"
            }
        }
    
    def _initialize_similarity_weights(self) -> Dict[str, float]:
        """Initialize similarity calculation weights."""
        return {
            "keyword_overlap": 0.3,
            "domain_match": 0.2,
            "technology_stack": 0.15,
            "complexity_level": 0.1,
            "task_type": 0.15,
            "semantic_similarity": 0.1
        }
    
    def _initialize_agent_assignment_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for intelligent agent assignment based on task content."""
        return {
            "researcher": [
                "research", "investigate", "analyze", "study", "explore", "evaluation", "assessment",
                "literature review", "market research", "competitive analysis", "requirements gathering",
                "feasibility study", "discovery", "analysis", "examination", "survey"
            ],
            "engineer": [
                "implement", "code", "develop", "build", "create", "program", "write code",
                "refactor", "optimize", "debug", "fix", "patch", "enhancement", "feature",
                "algorithm", "function", "method", "class", "module", "component", "api",
                "endpoint", "database", "integration", "backend", "frontend"
            ],
            "qa": [
                "test", "testing", "validate", "verification", "quality assurance", "qa",
                "unit test", "integration test", "e2e test", "acceptance test", "performance test",
                "load test", "security test", "regression test", "smoke test", "bug fix validation",
                "test case", "test plan", "test strategy", "automated testing"
            ],
            "architect": [
                "design", "architecture", "system design", "technical design", "blueprint",
                "specification", "technical specification", "architecture review", "design pattern",
                "system architecture", "solution design", "technical planning", "scalability design"
            ],
            "operations": [
                "deploy", "deployment", "devops", "infrastructure", "ci/cd", "pipeline",
                "docker", "kubernetes", "aws", "cloud", "server", "environment", "configuration",
                "monitoring", "logging", "alerting", "provisioning", "automation", "orchestration"
            ],
            "security_engineer": [
                "security", "secure", "authentication", "authorization", "encryption", "vulnerability",
                "security audit", "penetration test", "security review", "compliance", "privacy",
                "security scan", "threat analysis", "risk assessment", "security policy"
            ],
            "performance_engineer": [
                "performance", "optimization", "profiling", "benchmarking", "load testing",
                "performance tuning", "scalability", "latency", "throughput", "capacity planning",
                "performance monitoring", "bottleneck analysis", "memory optimization"
            ],
            "ui_ux_engineer": [
                "ui", "ux", "user interface", "user experience", "frontend", "design system",
                "component library", "styling", "css", "responsive design", "accessibility",
                "usability", "wireframe", "mockup", "prototype", "user flow"
            ],
            "data_engineer": [
                "data", "database", "etl", "data pipeline", "data processing", "analytics",
                "data warehouse", "data lake", "sql", "nosql", "mongodb", "postgresql",
                "data migration", "data modeling", "data transformation"
            ]
        }
    
    async def decompose_task(self, task_description: str, project_name: str = None,
                           metadata: TaskMetadata = None, **kwargs) -> TaskDecomposition:
        """
        Intelligently decompose a task using memory-driven analysis.
        
        Args:
            task_description: Description of the task to decompose
            project_name: Optional project context
            metadata: Optional task metadata
            **kwargs: Additional parameters
            
        Returns:
            TaskDecomposition with intelligent subtask breakdown
        """
        start_time = datetime.now()
        decomposition_id = f"decomp_{int(start_time.timestamp())}_{hash(task_description[:50])}"
        
        logger.info(f"Starting intelligent decomposition for: {task_description[:100]}...")
        
        try:
            # Step 1: Prepare memory context for decomposition
            context = await self._prepare_decomposition_context(
                task_description, project_name, metadata
            )
            
            # Step 2: Find similar historical tasks
            similar_tasks = await self._find_similar_tasks(task_description, context)
            
            # Step 3: Analyze task complexity using patterns and history
            complexity = await self._analyze_task_complexity(
                task_description, similar_tasks, metadata
            )
            
            # Step 4: Select optimal decomposition strategy
            strategy = await self._select_decomposition_strategy(
                task_description, complexity, similar_tasks, context
            )
            
            # Step 5: Generate adaptive decomposition using memory patterns
            subtasks = await self._generate_adaptive_decomposition(
                task_description, complexity, strategy, similar_tasks, context, metadata
            )
            
            # Step 6: Calculate confidence and estimates
            total_hours, confidence_score = self._calculate_decomposition_metrics(
                subtasks, similar_tasks, complexity
            )
            
            # Step 7: Create decomposition result
            decomposition = TaskDecomposition(
                original_task=task_description,
                strategy=strategy,
                complexity=complexity,
                subtasks=subtasks,
                total_estimated_hours=total_hours,
                confidence_score=confidence_score,
                decomposition_id=decomposition_id,
                created_at=start_time,
                similar_decompositions=[t.task_id for t in similar_tasks[:5]],
                pattern_matches=self._extract_pattern_matches(context, similar_tasks),
                memory_context_size=context.total_memories if context else 0,
                adaptation_notes=self._generate_adaptation_notes(similar_tasks, strategy)
            )
            
            # Step 8: Store decomposition in memory for future learning
            await self._store_decomposition_in_memory(decomposition, project_name)
            
            # Step 9: Update learning metrics
            self._update_learning_metrics(decomposition)
            
            logger.info(f"Decomposition completed: {len(subtasks)} subtasks, "
                       f"{total_hours:.1f}h estimated, {confidence_score:.2f} confidence")
            
            return decomposition
            
        except Exception as e:
            logger.error(f"Failed to decompose task: {e}")
            # Return fallback decomposition
            return self._create_fallback_decomposition(
                task_description, decomposition_id, start_time
            )
    
    async def _prepare_decomposition_context(self, task_description: str, 
                                           project_name: str = None,
                                           metadata: TaskMetadata = None) -> Any:
        """Prepare memory context for task decomposition."""
        try:
            # Build keywords for context preparation
            keywords = ["task decomposition", "planning", "subtasks"]
            
            if metadata:
                keywords.extend(metadata.technology_stack)
                keywords.extend(metadata.required_skills)
                keywords.append(metadata.domain)
            
            # Extract keywords from task description
            task_keywords = self._extract_task_keywords(task_description)
            keywords.extend(task_keywords)
            
            # Prepare context request
            context_request = ContextRequest(
                context_type=ContextType.PATTERN_MATCHING,
                scope=ContextScope.PROJECT_SPECIFIC if project_name else ContextScope.GLOBAL_PATTERNS,
                project_name=project_name,
                task_description=task_description,
                keywords=keywords,
                categories=[MemoryCategory.PATTERN, MemoryCategory.PROJECT],
                max_memories=30
            )
            
            context = await self.context_manager.prepare_context(context_request)
            return context
            
        except Exception as e:
            logger.error(f"Failed to prepare decomposition context: {e}")
            return None
    
    def _extract_task_keywords(self, task_description: str) -> List[str]:
        """Extract relevant keywords from task description."""
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = []
        
        # Technology keywords
        tech_patterns = [
            r'\b(python|javascript|react|vue|angular|django|flask|fastapi)\b',
            r'\b(api|rest|graphql|database|sql|mongodb|postgresql)\b',
            r'\b(frontend|backend|fullstack|ui|ux|design)\b',
            r'\b(test|testing|unit test|integration|e2e)\b',
            r'\b(deploy|deployment|ci|cd|devops|docker)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, task_description.lower())
            keywords.extend(matches)
        
        # Action keywords
        action_words = ['implement', 'create', 'build', 'design', 'refactor', 
                       'optimize', 'fix', 'update', 'migrate', 'integrate']
        
        for action in action_words:
            if action in task_description.lower():
                keywords.append(action)
        
        return list(set(keywords))  # Remove duplicates
    
    def _assign_agent_type(self, task_title: str, task_description: str, skills_required: List[str] = None) -> str:
        """
        Intelligently assign an agent type based on task content analysis.
        
        Args:
            task_title: The task title
            task_description: The task description
            skills_required: Optional list of required skills
            
        Returns:
            Agent type string (e.g., 'engineer', 'researcher', 'qa')
        """
        # Combine all text for analysis
        combined_text = f"{task_title} {task_description}".lower()
        if skills_required:
            combined_text += " " + " ".join(skills_required).lower()
        
        # Score each agent type based on keyword matches
        agent_scores = {}
        
        for agent_type, keywords in self.agent_assignment_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    # Weight longer keywords more heavily
                    weight = len(keyword.split()) * 1.5
                    score += weight
            
            # Normalize score by number of keywords for that agent type
            if keywords:
                agent_scores[agent_type] = score / len(keywords)
        
        # Find the agent type with the highest score
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1])
            if best_agent[1] > 0:  # Only return if there's at least some match
                return best_agent[0]
        
        # Default fallback based on common patterns
        if any(word in combined_text for word in ["implement", "code", "develop", "build", "create"]):
            return "engineer"
        elif any(word in combined_text for word in ["test", "testing", "validate", "verify"]):
            return "qa"
        elif any(word in combined_text for word in ["research", "analyze", "investigate", "study"]):
            return "researcher"
        elif any(word in combined_text for word in ["design", "architecture", "plan"]):
            return "architect"
        elif any(word in combined_text for word in ["deploy", "infrastructure", "devops"]):
            return "operations"
        
        # Final fallback
        return "engineer"
    
    def _get_agent_display_name(self, agent_type: str) -> str:
        """
        Get the display name for an agent type.
        
        Args:
            agent_type: Agent type string
            
        Returns:
            Display name for the agent
        """
        # Import here to avoid circular imports
        from ..core.enforcement import AgentDisplayNames, AgentType as EnforcementAgentType
        
        # Map our internal agent types to enforcement agent types
        agent_type_mapping = {
            "researcher": EnforcementAgentType.RESEARCHER,
            "engineer": EnforcementAgentType.ENGINEER,
            "qa": EnforcementAgentType.QA,
            "architect": EnforcementAgentType.ARCHITECT,
            "operations": EnforcementAgentType.OPERATIONS,
            "security_engineer": EnforcementAgentType.SECURITY_ENGINEER,
            "performance_engineer": EnforcementAgentType.PERFORMANCE_ENGINEER,
            "ui_ux_engineer": EnforcementAgentType.UI_UX_ENGINEER,
            "data_engineer": EnforcementAgentType.DATA_ENGINEER
        }
        
        try:
            enforcement_type = agent_type_mapping.get(agent_type)
            if enforcement_type:
                return AgentDisplayNames.get_display_name(enforcement_type)
            else:
                # Fallback for unknown types
                return agent_type.replace("_", "").title()
        except Exception:
            return agent_type.replace("_", "").title()
    
    async def _find_similar_tasks(self, task_description: str, context: Any) -> List[SimilarTask]:
        """Find similar tasks from memory with decomposition history."""
        try:
            similar_tasks = []
            
            # Search for similar task decompositions in memory
            response = await self.memory.retrieve_memories(
                category=MemoryCategory.PATTERN,
                query=f"task decomposition {task_description}",
                tags=["task_decomposition", "planning"],
                limit=10
            )
            
            if response.success and response.data:
                memories = response.data.get("memories", [])
                
                for memory in memories:
                    # Calculate similarity score
                    similarity_score = self._calculate_task_similarity(
                        task_description, memory.get("content", "")
                    )
                    
                    if similarity_score > 0.3:  # Minimum similarity threshold
                        similar_task = self._parse_similar_task(memory, similarity_score)
                        if similar_task:
                            similar_tasks.append(similar_task)
            
            # Sort by similarity score
            similar_tasks.sort(key=lambda x: x.similarity_score, reverse=True)
            return similar_tasks[:5]  # Return top 5 similar tasks
            
        except Exception as e:
            logger.error(f"Failed to find similar tasks: {e}")
            return []
    
    def _calculate_task_similarity(self, task1: str, task2: str) -> float:
        """Calculate similarity score between two tasks."""
        # Simple similarity calculation (can be enhanced with embeddings)
        task1_lower = task1.lower()
        task2_lower = task2.lower()
        
        # Keyword overlap
        words1 = set(task1_lower.split())
        words2 = set(task2_lower.split())
        common_words = words1.intersection(words2)
        
        if not words1 or not words2:
            return 0.0
        
        keyword_similarity = len(common_words) / max(len(words1), len(words2))
        
        # Length similarity (tasks of similar scope tend to be similar length)
        length_ratio = min(len(task1), len(task2)) / max(len(task1), len(task2))
        
        # Combined similarity score
        return (keyword_similarity * 0.7 + length_ratio * 0.3)
    
    def _parse_similar_task(self, memory: Dict[str, Any], similarity_score: float) -> Optional[SimilarTask]:
        """Parse a memory into a SimilarTask object."""
        try:
            metadata = memory.get("metadata", {})
            
            return SimilarTask(
                task_id=memory.get("id", "unknown"),
                task_description=memory.get("content", ""),
                similarity_score=similarity_score,
                decomposition=metadata.get("decomposition", {}),
                outcome=metadata.get("outcome", "unknown"),
                lessons_learned=metadata.get("lessons_learned", []),
                complexity_actual=TaskComplexity(metadata.get("complexity", "medium")),
                hours_actual=float(metadata.get("hours_actual", 0))
            )
            
        except Exception as e:
            logger.error(f"Failed to parse similar task: {e}")
            return None
    
    async def _analyze_task_complexity(self, task_description: str, 
                                     similar_tasks: List[SimilarTask],
                                     metadata: TaskMetadata = None) -> TaskComplexity:
        """Analyze task complexity using patterns and historical data."""
        complexity_scores = {}
        
        # Keyword-based complexity indicators
        for complexity_level, indicators in self.complexity_indicators.items():
            score = 0.0
            
            # Check keyword matches
            for keyword in indicators["keywords"]:
                if keyword.lower() in task_description.lower():
                    score += 0.2
            
            # Check estimated hours from metadata
            if metadata and metadata.estimated_hours:
                max_hours = indicators["max_estimated_hours"]
                if metadata.estimated_hours <= max_hours:
                    score += 0.3
            
            complexity_scores[complexity_level] = score
        
        # Historical pattern influence
        if similar_tasks:
            historical_complexities = [task.complexity_actual for task in similar_tasks]
            most_common_complexity = max(set(historical_complexities), 
                                       key=historical_complexities.count)
            
            # Boost score for historically common complexity
            if most_common_complexity.value in complexity_scores:
                complexity_scores[most_common_complexity.value] += 0.3
        
        # Select complexity with highest score
        if complexity_scores:
            best_complexity = max(complexity_scores.items(), key=lambda x: x[1])
            return TaskComplexity(best_complexity[0])
        
        # Fallback to medium complexity
        return TaskComplexity.MEDIUM
    
    async def _select_decomposition_strategy(self, task_description: str,
                                           complexity: TaskComplexity,
                                           similar_tasks: List[SimilarTask],
                                           context: Any) -> DecompositionStrategy:
        """Select optimal decomposition strategy based on patterns and history."""
        strategy_scores = {}
        
        # Analyze task description for strategy indicators
        task_lower = task_description.lower()
        
        for strategy, pattern in self.strategy_patterns.items():
            score = 0.0
            
            # Check keyword matches
            for keyword in pattern["best_for"]:
                if keyword in task_lower:
                    score += 0.3
            
            # Check complexity preference
            if complexity in pattern["complexity_preference"]:
                score += 0.4
            
            strategy_scores[strategy] = score
        
        # Historical strategy effectiveness
        if similar_tasks:
            historical_strategies = []
            for task in similar_tasks:
                decomp = task.decomposition
                if decomp and "strategy" in decomp:
                    strategy = decomp["strategy"]
                    if task.outcome == "success":
                        historical_strategies.append((strategy, 1.0))
                    elif task.outcome == "partial":
                        historical_strategies.append((strategy, 0.5))
            
            # Boost scores for successful historical strategies
            for strategy_name, success_weight in historical_strategies:
                if strategy_name in strategy_scores:
                    strategy_scores[strategy_name] += success_weight * 0.2
        
        # Select strategy with highest score
        if strategy_scores:
            best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
            return DecompositionStrategy(best_strategy[0])
        
        # Fallback strategy based on complexity
        if complexity in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]:
            return DecompositionStrategy.LINEAR
        elif complexity == TaskComplexity.EPIC:
            return DecompositionStrategy.HIERARCHICAL
        else:
            return DecompositionStrategy.PARALLEL
    
    async def _generate_adaptive_decomposition(self, task_description: str,
                                             complexity: TaskComplexity,
                                             strategy: DecompositionStrategy,
                                             similar_tasks: List[SimilarTask],
                                             context: Any,
                                             metadata: TaskMetadata = None) -> List[SubTask]:
        """Generate adaptive decomposition using memory patterns."""
        subtasks = []
        
        # Base decomposition patterns by complexity
        base_patterns = self._get_base_decomposition_patterns(complexity, strategy)
        
        # Adapt based on similar tasks
        if similar_tasks:
            subtasks = await self._adapt_from_similar_tasks(
                task_description, base_patterns, similar_tasks, strategy
            )
        else:
            subtasks = self._generate_from_base_patterns(
                task_description, base_patterns, metadata
            )
        
        # Apply strategy-specific adjustments
        subtasks = self._apply_strategy_adjustments(subtasks, strategy)
        
        # Add memory-augmented insights
        subtasks = self._enhance_with_memory_insights(subtasks, context)
        
        return subtasks
    
    def _get_base_decomposition_patterns(self, complexity: TaskComplexity,
                                       strategy: DecompositionStrategy) -> Dict[str, Any]:
        """Get base decomposition patterns for complexity and strategy."""
        patterns = {
            TaskComplexity.TRIVIAL: {
                "subtask_count": 1,
                "typical_subtasks": ["Execute the task"],
                "estimated_hours_per_subtask": [1]
            },
            TaskComplexity.SIMPLE: {
                "subtask_count": 2-3,
                "typical_subtasks": ["Plan and design", "Implement", "Test and verify"],
                "estimated_hours_per_subtask": [1, 4, 2]
            },
            TaskComplexity.MEDIUM: {
                "subtask_count": 4-6,
                "typical_subtasks": [
                    "Requirements analysis", "Design and architecture", 
                    "Core implementation", "Integration", "Testing", "Documentation"
                ],
                "estimated_hours_per_subtask": [2, 4, 8, 4, 4, 2]
            },
            TaskComplexity.COMPLEX: {
                "subtask_count": 6-12,
                "typical_subtasks": [
                    "Research and analysis", "System design", "Component breakdown",
                    "Core development", "Integration development", "Testing strategy",
                    "Unit testing", "Integration testing", "Documentation", 
                    "Deployment planning", "Monitoring setup"
                ],
                "estimated_hours_per_subtask": [4, 8, 6, 16, 12, 4, 8, 6, 4, 3, 3]
            },
            TaskComplexity.EPIC: {
                "subtask_count": 10-25,
                "typical_subtasks": [
                    "Epic planning", "Architecture design", "Technology selection",
                    "Phase 1 planning", "Phase 1 development", "Phase 1 testing",
                    "Phase 2 planning", "Phase 2 development", "Phase 2 testing",
                    "Integration planning", "System integration", "End-to-end testing",
                    "Performance testing", "Security review", "Documentation",
                    "Deployment strategy", "Monitoring and alerting", "Training",
                    "Go-live planning", "Post-launch monitoring"
                ],
                "estimated_hours_per_subtask": [8, 16, 8, 6, 24, 16, 6, 32, 20,
                                               8, 16, 12, 8, 6, 8, 6, 4, 4, 4, 8]
            }
        }
        
        return patterns.get(complexity, patterns[TaskComplexity.MEDIUM])
    
    async def _adapt_from_similar_tasks(self, task_description: str,
                                      base_patterns: Dict[str, Any],
                                      similar_tasks: List[SimilarTask],
                                      strategy: DecompositionStrategy) -> List[SubTask]:
        """Adapt decomposition from similar historical tasks."""
        subtasks = []
        
        # Find the most similar successful task
        successful_tasks = [t for t in similar_tasks if t.outcome == "success"]
        if not successful_tasks:
            successful_tasks = similar_tasks  # Fall back to any similar task
        
        if successful_tasks:
            best_similar = successful_tasks[0]  # Highest similarity score
            historical_decomp = best_similar.decomposition
            
            if historical_decomp and "subtasks" in historical_decomp:
                # Adapt historical subtasks to current task
                historical_subtasks = historical_decomp["subtasks"]
                
                for i, hist_subtask in enumerate(historical_subtasks):
                    adapted_subtask = self._adapt_subtask_from_history(
                        hist_subtask, task_description, i, best_similar
                    )
                    subtasks.append(adapted_subtask)
        
        # If no historical subtasks found, use base patterns
        if not subtasks:
            subtasks = self._generate_from_base_patterns(task_description, base_patterns)
        
        return subtasks
    
    def _adapt_subtask_from_history(self, historical_subtask: Dict[str, Any],
                                   current_task: str, index: int,
                                   similar_task: SimilarTask) -> SubTask:
        """Adapt a historical subtask for the current task."""
        subtask_id = f"subtask_{index + 1:02d}"
        
        # Adapt title and description to current context
        original_title = historical_subtask.get("title", f"Subtask {index + 1}")
        original_desc = historical_subtask.get("description", "")
        
        # Simple adaptation (can be enhanced with LLM)
        adapted_title = original_title.replace(
            similar_task.task_description.split()[0], 
            current_task.split()[0]
        )
        
        # Assign agent type based on adapted content
        agent_type = self._assign_agent_type(adapted_title, original_desc, historical_subtask.get("skills_required", []))
        agent_display_name = self._get_agent_display_name(agent_type)
        
        return SubTask(
            id=subtask_id,
            title=adapted_title,
            description=original_desc,
            complexity=TaskComplexity(historical_subtask.get("complexity", "medium")),
            estimated_hours=float(historical_subtask.get("estimated_hours", 4)),
            dependencies=historical_subtask.get("dependencies", []),
            skills_required=historical_subtask.get("skills_required", []),
            success_criteria=historical_subtask.get("success_criteria", []),
            risk_level=historical_subtask.get("risk_level", "low"),
            priority=int(historical_subtask.get("priority", 5)),
            assigned_agent_type=agent_type,
            agent_display_name=agent_display_name,
            similar_tasks=[similar_task.task_id],
            pattern_confidence=similar_task.similarity_score,
            historical_success_rate=1.0 if similar_task.outcome == "success" else 0.5
        )
    
    def _generate_from_base_patterns(self, task_description: str,
                                   base_patterns: Dict[str, Any],
                                   metadata: TaskMetadata = None) -> List[SubTask]:
        """Generate subtasks from base patterns when no similar tasks found."""
        subtasks = []
        typical_subtasks = base_patterns["typical_subtasks"]
        estimated_hours = base_patterns["estimated_hours_per_subtask"]
        
        for i, (title, hours) in enumerate(zip(typical_subtasks, estimated_hours)):
            subtask_id = f"subtask_{i + 1:02d}"
            
            # Customize subtask for the specific task
            customized_title = self._customize_subtask_title(title, task_description)
            customized_desc = self._generate_subtask_description(title, task_description, metadata)
            
            subtasks.append(SubTask(
                id=subtask_id,
                title=customized_title,
                description=customized_desc,
                complexity=self._estimate_subtask_complexity(hours),
                estimated_hours=hours,
                skills_required=self._infer_required_skills(title, metadata),
                success_criteria=self._generate_success_criteria(title),
                risk_level=self._assess_risk_level(title),
                priority=self._calculate_priority(i, len(typical_subtasks)),
                pattern_confidence=0.5,  # Medium confidence for base patterns
                historical_success_rate=0.75  # Default success rate assumption
            ))
        
        return subtasks
    
    def _customize_subtask_title(self, base_title: str, task_description: str) -> str:
        """Customize subtask title for the specific task."""
        # Extract key terms from task description
        key_terms = self._extract_task_keywords(task_description)
        
        # Simple customization (can be enhanced with templates)
        if "implement" in task_description.lower() and "implementation" in base_title.lower():
            if key_terms:
                return f"{base_title} - {key_terms[0]}"
        
        return base_title
    
    def _generate_subtask_description(self, title: str, task_description: str,
                                    metadata: TaskMetadata = None) -> str:
        """Generate detailed description for a subtask."""
        descriptions = {
            "Plan and design": f"Plan the approach and design solution for: {task_description}",
            "Requirements analysis": f"Analyze requirements and constraints for: {task_description}",
            "Core implementation": f"Implement the main functionality: {task_description}",
            "Testing": f"Test the implementation to ensure it meets requirements",
            "Documentation": f"Document the solution and usage instructions"
        }
        
        # Check for partial matches
        for key, desc in descriptions.items():
            if key.lower() in title.lower():
                return desc
        
        return f"Complete subtask: {title}"
    
    def _estimate_subtask_complexity(self, estimated_hours: float) -> TaskComplexity:
        """Estimate subtask complexity based on hours."""
        if estimated_hours <= 1:
            return TaskComplexity.TRIVIAL
        elif estimated_hours <= 4:
            return TaskComplexity.SIMPLE
        elif estimated_hours <= 12:
            return TaskComplexity.MEDIUM
        elif estimated_hours <= 32:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.EPIC
    
    def _infer_required_skills(self, title: str, metadata: TaskMetadata = None) -> List[str]:
        """Infer required skills for a subtask."""
        skills = []
        
        title_lower = title.lower()
        
        if "design" in title_lower or "architecture" in title_lower:
            skills.extend(["system_design", "architecture"])
        if "implement" in title_lower or "development" in title_lower:
            skills.extend(["programming", "development"])
        if "test" in title_lower:
            skills.extend(["testing", "qa"])
        if "document" in title_lower:
            skills.extend(["documentation", "technical_writing"])
        
        # Add skills from metadata
        if metadata and metadata.required_skills:
            skills.extend(metadata.required_skills)
        
        return list(set(skills))
    
    def _generate_success_criteria(self, title: str) -> List[str]:
        """Generate success criteria for a subtask."""
        criteria = []
        
        title_lower = title.lower()
        
        if "implement" in title_lower:
            criteria.append("Feature works as specified")
            criteria.append("Code follows team standards")
        if "test" in title_lower:
            criteria.append("All tests pass")
            criteria.append("Coverage meets requirements")
        if "design" in title_lower:
            criteria.append("Design reviewed and approved")
            criteria.append("Design meets requirements")
        if "document" in title_lower:
            criteria.append("Documentation is complete and clear")
        
        return criteria
    
    def _assess_risk_level(self, title: str) -> str:
        """Assess risk level for a subtask."""
        title_lower = title.lower()
        
        high_risk_indicators = ["integration", "migration", "architecture", "complex"]
        medium_risk_indicators = ["implement", "development", "design"]
        
        for indicator in high_risk_indicators:
            if indicator in title_lower:
                return "high"
        
        for indicator in medium_risk_indicators:
            if indicator in title_lower:
                return "medium"
        
        return "low"
    
    def _calculate_priority(self, index: int, total_subtasks: int) -> int:
        """Calculate priority for a subtask based on position."""
        # Earlier tasks generally have higher priority
        priority_score = 10 - int((index / total_subtasks) * 5)
        return max(1, min(10, priority_score))
    
    def _apply_strategy_adjustments(self, subtasks: List[SubTask],
                                  strategy: DecompositionStrategy) -> List[SubTask]:
        """Apply strategy-specific adjustments to subtasks."""
        if strategy == DecompositionStrategy.PARALLEL:
            # Reduce dependencies for parallel execution
            for subtask in subtasks:
                subtask.dependencies = [dep for dep in subtask.dependencies 
                                      if "critical" in dep.lower()]
        
        elif strategy == DecompositionStrategy.LINEAR:
            # Add sequential dependencies
            for i, subtask in enumerate(subtasks[1:], 1):
                prev_subtask = subtasks[i-1]
                if prev_subtask.id not in subtask.dependencies:
                    subtask.dependencies.append(prev_subtask.id)
        
        elif strategy == DecompositionStrategy.ITERATIVE:
            # Group subtasks into sprints/iterations
            for i, subtask in enumerate(subtasks):
                sprint_num = (i // 3) + 1  # 3 subtasks per sprint
                subtask.title = f"Sprint {sprint_num}: {subtask.title}"
        
        return subtasks
    
    def _enhance_with_memory_insights(self, subtasks: List[SubTask], context: Any) -> List[SubTask]:
        """Enhance subtasks with insights from memory context."""
        if not context or not context.patterns:
            return subtasks
        
        # Extract relevant patterns from context
        patterns = context.patterns
        
        for subtask in subtasks:
            # Look for relevant patterns for this subtask
            relevant_patterns = []
            for pattern in patterns:
                pattern_content = pattern.get("content", "").lower()
                if any(skill.lower() in pattern_content for skill in subtask.skills_required):
                    relevant_patterns.append(pattern)
            
            if relevant_patterns:
                # Enhance subtask with pattern insights
                subtask.validation_steps.extend([
                    "Review relevant patterns from team knowledge",
                    "Apply learned best practices"
                ])
                
                # Increase confidence based on pattern matches
                subtask.pattern_confidence = min(1.0, subtask.pattern_confidence + 0.2)
        
        return subtasks
    
    def _calculate_decomposition_metrics(self, subtasks: List[SubTask],
                                       similar_tasks: List[SimilarTask],
                                       complexity: TaskComplexity) -> Tuple[float, float]:
        """Calculate total estimated hours and confidence score."""
        total_hours = sum(subtask.estimated_hours for subtask in subtasks)
        
        # Calculate confidence based on multiple factors
        confidence_factors = []
        
        # Pattern confidence (average of subtask confidences)
        if subtasks:
            avg_pattern_confidence = sum(s.pattern_confidence for s in subtasks) / len(subtasks)
            confidence_factors.append(avg_pattern_confidence)
        
        # Historical similarity confidence
        if similar_tasks:
            similarity_confidence = similar_tasks[0].similarity_score
            confidence_factors.append(similarity_confidence)
        
        # Complexity confidence (higher for well-understood complexities)
        complexity_confidence = {
            TaskComplexity.TRIVIAL: 0.9,
            TaskComplexity.SIMPLE: 0.8,
            TaskComplexity.MEDIUM: 0.7,
            TaskComplexity.COMPLEX: 0.6,
            TaskComplexity.EPIC: 0.5
        }.get(complexity, 0.5)
        confidence_factors.append(complexity_confidence)
        
        # Overall confidence is the average of all factors
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        return total_hours, overall_confidence
    
    def _extract_pattern_matches(self, context: Any, similar_tasks: List[SimilarTask]) -> List[Dict[str, Any]]:
        """Extract pattern matches from context and similar tasks."""
        patterns = []
        
        if context and context.patterns:
            for pattern in context.patterns[:5]:  # Top 5 patterns
                patterns.append({
                    "type": "memory_pattern",
                    "content": pattern.get("content", "")[:200],  # Truncate for storage
                    "confidence": context.relevance_scores.get(pattern.get("id", ""), 0.5)
                })
        
        for task in similar_tasks[:3]:  # Top 3 similar tasks
            patterns.append({
                "type": "similar_task",
                "task_id": task.task_id,
                "similarity_score": task.similarity_score,
                "outcome": task.outcome
            })
        
        return patterns
    
    def _generate_adaptation_notes(self, similar_tasks: List[SimilarTask],
                                 strategy: DecompositionStrategy) -> str:
        """Generate notes about how the decomposition was adapted."""
        notes = []
        
        if similar_tasks:
            best_similar = similar_tasks[0]
            notes.append(f"Adapted from similar task (similarity: {best_similar.similarity_score:.2f})")
            
            if best_similar.outcome == "success":
                notes.append("Used successful historical pattern")
            elif best_similar.outcome == "partial":
                notes.append("Improved upon partially successful pattern")
        
        notes.append(f"Applied {strategy.value} decomposition strategy")
        
        return " | ".join(notes)
    
    async def _store_decomposition_in_memory(self, decomposition: TaskDecomposition,
                                           project_name: str = None) -> None:
        """Store the decomposition in memory for future learning."""
        try:
            # Prepare decomposition data for storage
            decomposition_data = {
                "original_task": decomposition.original_task,
                "strategy": decomposition.strategy.value,
                "complexity": decomposition.complexity.value,
                "subtasks": [
                    {
                        "id": subtask.id,
                        "title": subtask.title,
                        "description": subtask.description,
                        "complexity": subtask.complexity.value,
                        "estimated_hours": subtask.estimated_hours,
                        "skills_required": subtask.skills_required,
                        "risk_level": subtask.risk_level,
                        "priority": subtask.priority
                    }
                    for subtask in decomposition.subtasks
                ],
                "total_estimated_hours": decomposition.total_estimated_hours,
                "confidence_score": decomposition.confidence_score
            }
            
            # Store in memory
            await self.memory.store_memory(
                category=MemoryCategory.PATTERN,
                content=f"Task decomposition: {decomposition.original_task}",
                metadata={
                    "type": "task_decomposition",
                    "decomposition": decomposition_data,
                    "decomposition_id": decomposition.decomposition_id,
                    "created_at": decomposition.created_at.isoformat(),
                    "complexity": decomposition.complexity.value,
                    "strategy": decomposition.strategy.value,
                    "confidence": decomposition.confidence_score
                },
                project_name=project_name or "global",
                tags=["task_decomposition", "planning", decomposition.strategy.value, 
                      decomposition.complexity.value]
            )
            
            logger.info(f"Stored decomposition {decomposition.decomposition_id} in memory")
            
        except Exception as e:
            logger.error(f"Failed to store decomposition in memory: {e}")
    
    def _update_learning_metrics(self, decomposition: TaskDecomposition) -> None:
        """Update learning metrics with the new decomposition."""
        self.performance_metrics["total_decompositions"] += 1
        self.performance_metrics["accuracy_scores"].append(decomposition.confidence_score)
        
        # Update strategy effectiveness
        strategy = decomposition.strategy.value
        if strategy not in self.performance_metrics["strategy_effectiveness"]:
            self.performance_metrics["strategy_effectiveness"][strategy] = []
        
        self.performance_metrics["strategy_effectiveness"][strategy].append(
            decomposition.confidence_score
        )
        
        # Calculate pattern reuse rate
        if decomposition.similar_decompositions:
            self.performance_metrics["pattern_reuse_rate"] = (
                self.performance_metrics["pattern_reuse_rate"] * 0.9 + 0.1  # Moving average
            )
        
        # Store decomposition in history
        self.decomposition_history.append(decomposition)
        
        # Keep only recent history (last 100 decompositions)
        if len(self.decomposition_history) > 100:
            self.decomposition_history = self.decomposition_history[-100:]
    
    def _create_fallback_decomposition(self, task_description: str,
                                     decomposition_id: str,
                                     start_time: datetime) -> TaskDecomposition:
        """Create a fallback decomposition when the intelligent process fails."""
        # Simple 3-step fallback
        subtasks = [
            SubTask(
                id="subtask_01",
                title="Plan and analyze",
                description=f"Plan and analyze requirements for: {task_description}",
                complexity=TaskComplexity.SIMPLE,
                estimated_hours=2.0,
                priority=9
            ),
            SubTask(
                id="subtask_02", 
                title="Implement solution",
                description=f"Implement the solution: {task_description}",
                complexity=TaskComplexity.MEDIUM,
                estimated_hours=6.0,
                dependencies=["subtask_01"],
                priority=8
            ),
            SubTask(
                id="subtask_03",
                title="Test and verify",
                description="Test the implementation and verify it meets requirements",
                complexity=TaskComplexity.SIMPLE,
                estimated_hours=2.0,
                dependencies=["subtask_02"],
                priority=7
            )
        ]
        
        return TaskDecomposition(
            original_task=task_description,
            strategy=DecompositionStrategy.LINEAR,
            complexity=TaskComplexity.MEDIUM,
            subtasks=subtasks,
            total_estimated_hours=10.0,
            confidence_score=0.3,  # Low confidence for fallback
            decomposition_id=decomposition_id,
            created_at=start_time,
            adaptation_notes="Fallback decomposition due to processing error"
        )
    
    def get_planner_stats(self) -> Dict[str, Any]:
        """Get intelligent task planner statistics."""
        stats = self.performance_metrics.copy()
        
        # Calculate averages
        if stats["accuracy_scores"]:
            stats["average_accuracy"] = sum(stats["accuracy_scores"]) / len(stats["accuracy_scores"])
        else:
            stats["average_accuracy"] = 0.0
        
        # Strategy effectiveness summary
        strategy_summary = {}
        for strategy, scores in stats["strategy_effectiveness"].items():
            if scores:
                strategy_summary[strategy] = {
                    "usage_count": len(scores),
                    "average_confidence": sum(scores) / len(scores)
                }
        stats["strategy_summary"] = strategy_summary
        
        return stats


# Factory function
def create_intelligent_task_planner(memory: ClaudePMMemory, 
                                   context_manager: Mem0ContextManager) -> IntelligentTaskPlanner:
    """
    Create and initialize an IntelligentTaskPlanner.
    
    Args:
        memory: ClaudePMMemory instance for memory operations
        context_manager: Mem0ContextManager for context preparation
        
    Returns:
        Initialized IntelligentTaskPlanner
    """
    return IntelligentTaskPlanner(memory, context_manager)