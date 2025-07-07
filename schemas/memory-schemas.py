"""
Claude PM Framework - Memory Schema Definitions
Comprehensive memory schemas for the Claude Max + mem0AI enhancement system.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class MemoryCategory(str, Enum):
    """Core memory categories for the Claude PM system."""
    PROJECT = "project"
    PATTERN = "pattern" 
    TEAM = "team"
    ERROR = "error"


class MemoryPriority(str, Enum):
    """Memory importance levels for retrieval prioritization."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BaseMemorySchema(BaseModel):
    """Base schema for all memory types with common fields."""
    
    memory_id: Optional[str] = Field(None, description="Unique memory identifier")
    category: MemoryCategory = Field(..., description="Memory category type")
    title: str = Field(..., description="Short descriptive title")
    content: str = Field(..., description="Main memory content")
    
    # Metadata
    priority: MemoryPriority = Field(default=MemoryPriority.MEDIUM, description="Memory importance")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Context
    project_id: Optional[str] = Field(None, description="Associated project identifier")
    agent_id: Optional[str] = Field(None, description="Creating agent identifier")
    user_id: Optional[str] = Field(None, description="Associated user identifier")
    
    # Relationships
    related_memories: List[str] = Field(default_factory=list, description="Related memory IDs")
    parent_memory: Optional[str] = Field(None, description="Parent memory ID for hierarchical organization")
    
    # Success tracking
    success_count: int = Field(default=0, description="Number of times this memory was successfully applied")
    failure_count: int = Field(default=0, description="Number of times this memory failed")
    confidence_score: float = Field(default=0.5, description="Confidence in memory accuracy (0-1)")


class ProjectMemorySchema(BaseMemorySchema):
    """Memory schema for architectural decisions and project-specific knowledge."""
    
    category: MemoryCategory = Field(default=MemoryCategory.PROJECT, description="Fixed as PROJECT")
    
    # Architectural decision tracking
    decision_type: str = Field(..., description="Type of architectural decision (tech_stack, pattern, infrastructure)")
    decision_rationale: str = Field(..., description="Why this decision was made")
    alternatives_considered: List[str] = Field(default_factory=list, description="Other options that were evaluated")
    
    # Impact tracking
    impact_scope: List[str] = Field(default_factory=list, description="Areas of codebase affected")
    performance_impact: Optional[str] = Field(None, description="Performance implications")
    maintenance_impact: Optional[str] = Field(None, description="Maintenance implications")
    
    # Implementation details
    implementation_steps: List[str] = Field(default_factory=list, description="Steps taken to implement")
    rollback_plan: Optional[str] = Field(None, description="How to reverse this decision if needed")
    
    # Success metrics
    metrics_tracked: List[str] = Field(default_factory=list, description="Metrics to monitor success")
    success_criteria: List[str] = Field(default_factory=list, description="Criteria for success")


class PatternMemorySchema(BaseMemorySchema):
    """Memory schema for successful solution patterns and best practices."""
    
    category: MemoryCategory = Field(default=MemoryCategory.PATTERN, description="Fixed as PATTERN")
    
    # Pattern classification
    pattern_type: str = Field(..., description="Type of pattern (design, architectural, workflow)")
    problem_domain: str = Field(..., description="Problem domain this pattern addresses")
    complexity_level: str = Field(..., description="Pattern complexity (simple, moderate, complex)")
    
    # Pattern details
    problem_description: str = Field(..., description="Problem this pattern solves")
    solution_approach: str = Field(..., description="How the pattern solves the problem")
    implementation_code: Optional[str] = Field(None, description="Code example or template")
    
    # Usage context
    applicable_contexts: List[str] = Field(default_factory=list, description="When to use this pattern")
    anti_patterns: List[str] = Field(default_factory=list, description="When NOT to use this pattern")
    prerequisites: List[str] = Field(default_factory=list, description="Requirements before using")
    
    # Effectiveness tracking
    success_rate: float = Field(default=0.0, description="Success rate when applied (0-1)")
    time_to_implement: Optional[int] = Field(None, description="Average implementation time in minutes")
    complexity_reduction: Optional[float] = Field(None, description="Complexity reduction achieved")


class TeamMemorySchema(BaseMemorySchema):
    """Memory schema for team coding standards, conventions, and preferences."""
    
    category: MemoryCategory = Field(default=MemoryCategory.TEAM, description="Fixed as TEAM")
    
    # Standard classification
    standard_type: str = Field(..., description="Type of standard (coding, testing, documentation, workflow)")
    scope: str = Field(..., description="Scope of application (project, team, organization)")
    enforcement_level: str = Field(..., description="Enforcement level (required, recommended, optional)")
    
    # Standard details
    standard_description: str = Field(..., description="Detailed description of the standard")
    examples: List[str] = Field(default_factory=list, description="Examples of correct implementation")
    counter_examples: List[str] = Field(default_factory=list, description="Examples of what to avoid")
    
    # Tool integration
    linting_rules: List[str] = Field(default_factory=list, description="Automated linting rules")
    tooling_required: List[str] = Field(default_factory=list, description="Required tools for enforcement")
    automation_scripts: List[str] = Field(default_factory=list, description="Scripts for automated checking")
    
    # Compliance tracking
    compliance_rate: float = Field(default=0.0, description="Team compliance rate (0-1)")
    violation_patterns: List[str] = Field(default_factory=list, description="Common violation patterns")
    training_resources: List[str] = Field(default_factory=list, description="Resources for learning standard")


class ErrorMemorySchema(BaseMemorySchema):
    """Memory schema for bug patterns, error analysis, and debugging knowledge."""
    
    category: MemoryCategory = Field(default=MemoryCategory.ERROR, description="Fixed as ERROR")
    
    # Error classification
    error_type: str = Field(..., description="Type of error (runtime, logic, performance, security)")
    severity: str = Field(..., description="Error severity (critical, high, medium, low)")
    frequency: str = Field(..., description="How often this error occurs (common, occasional, rare)")
    
    # Error details
    error_description: str = Field(..., description="Detailed description of the error")
    error_symptoms: List[str] = Field(default_factory=list, description="Observable symptoms")
    error_context: str = Field(..., description="Context where error typically occurs")
    
    # Root cause analysis
    root_causes: List[str] = Field(default_factory=list, description="Identified root causes")
    contributing_factors: List[str] = Field(default_factory=list, description="Contributing factors")
    
    # Solution tracking
    solutions_attempted: List[str] = Field(default_factory=list, description="Solutions that were tried")
    successful_solution: Optional[str] = Field(None, description="Solution that worked")
    solution_effectiveness: Optional[float] = Field(None, description="Effectiveness rating (0-1)")
    
    # Prevention
    prevention_strategies: List[str] = Field(default_factory=list, description="How to prevent this error")
    detection_methods: List[str] = Field(default_factory=list, description="How to detect this error early")
    automated_tests: List[str] = Field(default_factory=list, description="Tests to prevent regression")


class MemoryTagSchema(BaseModel):
    """Schema for memory tagging system."""
    
    tag_name: str = Field(..., description="Tag name")
    tag_category: str = Field(..., description="Tag category (technology, domain, priority)")
    description: Optional[str] = Field(None, description="Tag description")
    color: Optional[str] = Field(None, description="Display color for UI")
    usage_count: int = Field(default=0, description="Number of memories using this tag")


class MemoryRelationSchema(BaseModel):
    """Schema for defining relationships between memories."""
    
    source_memory_id: str = Field(..., description="Source memory ID")
    target_memory_id: str = Field(..., description="Target memory ID")
    relationship_type: str = Field(..., description="Type of relationship (related, supersedes, conflicts, extends)")
    strength: float = Field(default=1.0, description="Relationship strength (0-1)")
    description: Optional[str] = Field(None, description="Relationship description")


class MemorySearchRequest(BaseModel):
    """Schema for memory search requests."""
    
    query: str = Field(..., description="Search query")
    categories: Optional[List[MemoryCategory]] = Field(None, description="Categories to search")
    tags: Optional[List[str]] = Field(None, description="Tags to filter by")
    priority_min: Optional[MemoryPriority] = Field(None, description="Minimum priority level")
    project_id: Optional[str] = Field(None, description="Project scope filter")
    limit: int = Field(default=10, description="Maximum results to return")
    include_related: bool = Field(default=False, description="Include related memories")


class MemorySearchResult(BaseModel):
    """Schema for memory search results."""
    
    memory: Union[ProjectMemorySchema, PatternMemorySchema, TeamMemorySchema, ErrorMemorySchema]
    relevance_score: float = Field(..., description="Search relevance score (0-1)")
    context_snippet: str = Field(..., description="Relevant content snippet")
    related_memories: Optional[List[str]] = Field(None, description="Related memory IDs")


# Schema registry for dynamic schema handling
MEMORY_SCHEMA_REGISTRY = {
    MemoryCategory.PROJECT: ProjectMemorySchema,
    MemoryCategory.PATTERN: PatternMemorySchema,
    MemoryCategory.TEAM: TeamMemorySchema,
    MemoryCategory.ERROR: ErrorMemorySchema,
}


def get_schema_for_category(category: MemoryCategory) -> BaseModel:
    """Get the appropriate schema class for a memory category."""
    return MEMORY_SCHEMA_REGISTRY.get(category, BaseMemorySchema)


def validate_memory_schema(memory_data: Dict[str, Any], category: MemoryCategory) -> BaseModel:
    """Validate memory data against the appropriate schema."""
    schema_class = get_schema_for_category(category)
    return schema_class(**memory_data)