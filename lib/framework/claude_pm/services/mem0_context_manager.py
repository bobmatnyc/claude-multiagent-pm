"""
Mem0ContextManager - Memory-Driven Context Management System
Implements MEM-004 for intelligent context preparation using mem0AI patterns.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .claude_pm_memory import ClaudePMMemory, MemoryCategory, MemoryResponse
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class ContextType(str, Enum):
    """Types of context that can be prepared."""
    AGENT_TASK = "agent_task"
    PROJECT_INITIALIZATION = "project_initialization"
    CODE_REVIEW = "code_review"
    ARCHITECTURE_DECISION = "architecture_decision"
    DEBUGGING_SESSION = "debugging_session"
    PATTERN_MATCHING = "pattern_matching"


class ContextScope(str, Enum):
    """Scope of context preparation."""
    PROJECT_SPECIFIC = "project_specific"
    CROSS_PROJECT = "cross_project"
    GLOBAL_PATTERNS = "global_patterns"
    TEAM_KNOWLEDGE = "team_knowledge"


@dataclass
class ContextRequest:
    """Request for context preparation."""
    context_type: ContextType
    scope: ContextScope
    project_name: Optional[str] = None
    agent_type: Optional[str] = None
    task_description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    categories: List[MemoryCategory] = field(default_factory=list)
    max_memories: int = 20
    time_window_days: Optional[int] = None
    priority_tags: List[str] = field(default_factory=list)


@dataclass
class ContextBundle:
    """Prepared context bundle with memories and metadata."""
    request: ContextRequest
    context_id: str
    prepared_at: datetime
    memories_by_category: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    team_standards: List[Dict[str, Any]] = field(default_factory=list)
    historical_errors: List[Dict[str, Any]] = field(default_factory=list)
    project_decisions: List[Dict[str, Any]] = field(default_factory=list)
    relevance_scores: Dict[str, float] = field(default_factory=dict)
    context_summary: str = ""
    total_memories: int = 0
    preparation_time_ms: int = 0
    # New fields for enhanced context management
    project_history: Dict[str, Any] = field(default_factory=dict)
    pattern_insights: Dict[str, Any] = field(default_factory=dict)
    context_filters_applied: List[str] = field(default_factory=list)
    security_level: str = "public"
    team_access_level: str = "all"


class Mem0ContextManager:
    """
    Memory-driven context management system that prepares intelligent context
    for agents using historical patterns, team knowledge, and project-specific data.
    """
    
    def __init__(self, memory: ClaudePMMemory):
        """
        Initialize the context manager.
        
        Args:
            memory: ClaudePMMemory instance for memory operations
        """
        self.memory = memory
        self.context_cache: Dict[str, ContextBundle] = {}
        self.cache_ttl_minutes = 30
        
        # Agent role context filters
        self.agent_role_filters = self._initialize_agent_role_filters()
        
        # Pattern matching configuration
        self.pattern_weights = {
            "exact_match": 1.0,
            "keyword_match": 0.8,
            "semantic_similarity": 0.6,
            "project_relevance": 0.7,
            "recency": 0.5,
            "team_preference": 0.9,
            "success_pattern": 1.2,
            "error_prevention": 1.1
        }
        
        # Advanced context capabilities
        self.context_enhancers = self._initialize_context_enhancers()
        self.pattern_recognizers = self._initialize_pattern_recognizers()
        self.team_knowledge_filters = self._initialize_team_knowledge_filters()
        
        logger.info("Mem0ContextManager initialized")
    
    def _initialize_agent_role_filters(self) -> Dict[str, Dict[str, Any]]:
        """Initialize context filters for different agent roles."""
        return {
            "orchestrator": {
                "primary_categories": [MemoryCategory.PROJECT, MemoryCategory.PATTERN],
                "keywords": ["coordination", "planning", "workflow", "orchestration"],
                "exclude_tags": ["implementation_detail"]
            },
            "architect": {
                "primary_categories": [MemoryCategory.PROJECT, MemoryCategory.PATTERN],
                "keywords": ["architecture", "design", "patterns", "scalability", "decisions"],
                "exclude_tags": ["minor_bug", "style_issue"]
            },
            "engineer": {
                "primary_categories": [MemoryCategory.PATTERN, MemoryCategory.TEAM, MemoryCategory.ERROR],
                "keywords": ["implementation", "coding", "features", "development"],
                "exclude_tags": ["high_level_design"]
            },
            "qa": {
                "primary_categories": [MemoryCategory.ERROR, MemoryCategory.PATTERN, MemoryCategory.TEAM],
                "keywords": ["testing", "quality", "bugs", "validation"],
                "exclude_tags": ["architecture_decision"]
            },
            "security_engineer": {
                "primary_categories": [MemoryCategory.ERROR, MemoryCategory.PATTERN],
                "keywords": ["security", "vulnerabilities", "authentication", "authorization"],
                "exclude_tags": ["performance_issue", "style_issue"]
            },
            "performance_engineer": {
                "primary_categories": [MemoryCategory.PATTERN, MemoryCategory.ERROR],
                "keywords": ["performance", "optimization", "bottlenecks", "scalability"],
                "exclude_tags": ["security_issue", "style_issue"]
            },
            "code_review_engineer": {
                "primary_categories": [MemoryCategory.PATTERN, MemoryCategory.TEAM, MemoryCategory.ERROR],
                "keywords": ["code_review", "style", "standards", "quality", "best_practices"],
                "exclude_tags": ["implementation_detail"]
            }
        }
    
    def _initialize_context_enhancers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize context enhancement configurations for different scenarios."""
        return {
            "code_review": {
                "pattern_types": ["code_quality", "best_practices", "common_errors"],
                "team_standards": ["coding_style", "review_guidelines", "quality_gates"],
                "historical_focus": ["similar_files", "recent_changes", "team_feedback"]
            },
            "architecture_design": {
                "pattern_types": ["architectural_patterns", "design_decisions", "scalability"],
                "team_standards": ["architecture_principles", "technology_preferences"],
                "historical_focus": ["design_outcomes", "performance_results", "maintainability"]
            },
            "debugging": {
                "pattern_types": ["error_patterns", "debugging_strategies", "root_causes"],
                "team_standards": ["debugging_protocols", "logging_practices"],
                "historical_focus": ["similar_errors", "successful_fixes", "prevention_strategies"]
            },
            "feature_development": {
                "pattern_types": ["implementation_patterns", "feature_designs", "user_stories"],
                "team_standards": ["development_workflow", "testing_requirements"],
                "historical_focus": ["similar_features", "implementation_success", "user_feedback"]
            }
        }
    
    def _initialize_pattern_recognizers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pattern recognition configurations for intelligent context selection."""
        return {
            "success_indicators": {
                "tags": ["successful", "approved", "high_quality", "best_practice"],
                "metadata_keys": ["success_score", "approval_rating", "reuse_count"],
                "weight_multiplier": 1.5
            },
            "team_preferences": {
                "tags": ["team_standard", "preferred_approach", "recommended"],
                "metadata_keys": ["team_approval", "adoption_rate", "preference_score"],
                "weight_multiplier": 1.3
            },
            "error_prevention": {
                "tags": ["error_prone", "requires_attention", "vulnerability", "anti_pattern"],
                "metadata_keys": ["error_frequency", "severity", "prevention_strategy"],
                "weight_multiplier": 1.4
            },
            "recent_learnings": {
                "time_decay_days": 30,
                "recency_boost": 0.8,
                "learning_tags": ["lesson_learned", "recent_discovery", "new_approach"]
            }
        }
    
    def _initialize_team_knowledge_filters(self) -> Dict[str, Dict[str, Any]]:
        """Initialize team-specific knowledge filtering for context boundaries."""
        return {
            "access_levels": {
                "public": {"min_security": 0, "team_access": "all"},
                "team_only": {"min_security": 1, "team_access": "team_members"},
                "sensitive": {"min_security": 2, "team_access": "senior_team"},
                "confidential": {"min_security": 3, "team_access": "leads_only"}
            },
            "context_scopes": {
                "project_focused": {
                    "memory_sources": ["current_project", "related_projects"],
                    "cross_project_limit": 20
                },
                "domain_focused": {
                    "memory_sources": ["domain_expertise", "technology_stack"],
                    "domain_relevance_threshold": 0.7
                },
                "global_insights": {
                    "memory_sources": ["global_patterns", "best_practices"],
                    "insight_relevance_threshold": 0.8
                }
            }
        }
    
    async def prepare_context(self, request: ContextRequest) -> ContextBundle:
        """
        Prepare memory-augmented context for the given request.
        
        Args:
            request: Context preparation request
            
        Returns:
            ContextBundle with prepared context and memories
        """
        start_time = datetime.now()
        context_id = f"ctx_{int(start_time.timestamp())}_{hash(str(request))}"
        
        # Check cache first
        cached_context = self._get_cached_context(request)
        if cached_context:
            logger.debug(f"Returning cached context {cached_context.context_id}")
            return cached_context
        
        try:
            # Initialize context bundle
            bundle = ContextBundle(
                request=request,
                context_id=context_id,
                prepared_at=start_time
            )
            
            # Determine categories to search based on context type and agent role
            search_categories = self._determine_search_categories(request)
            
            # Prepare search queries
            search_queries = self._prepare_search_queries(request)
            
            # Retrieve memories for each category with enhanced pattern recognition
            for category in search_categories:
                for query in search_queries:
                    memories = await self._retrieve_category_memories(
                        category, query, request
                    )
                    
                    if memories:
                        category_key = category.value
                        if category_key not in bundle.memories_by_category:
                            bundle.memories_by_category[category_key] = []
                        bundle.memories_by_category[category_key].extend(memories)
            
            # Apply pattern recognition enhancements
            bundle = await self._apply_pattern_recognition(bundle)
            
            # Load project context history if requested
            if request.scope in [ContextScope.PROJECT_SPECIFIC, ContextScope.CROSS_PROJECT]:
                bundle = await self._load_project_context_history(bundle)
            
            # Deduplicate and score memories with enhanced scoring
            bundle = await self._process_and_score_memories(bundle)
            
            # Apply context filtering and boundaries
            bundle = self._apply_context_filtering(bundle)
            
            # Categorize memories by type
            bundle = self._categorize_memories(bundle)
            
            # Generate enhanced context summary
            bundle.context_summary = self._generate_context_summary(bundle)
            
            # Calculate preparation time
            end_time = datetime.now()
            bundle.preparation_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Cache the result
            self._cache_context(bundle)
            
            logger.info(f"Prepared context {context_id} with {bundle.total_memories} memories in {bundle.preparation_time_ms}ms")
            return bundle
            
        except Exception as e:
            logger.error(f"Failed to prepare context: {e}")
            # Return minimal context bundle on error
            return ContextBundle(
                request=request,
                context_id=context_id,
                prepared_at=start_time,
                context_summary=f"Error preparing context: {str(e)}"
            )
    
    def _determine_search_categories(self, request: ContextRequest) -> List[MemoryCategory]:
        """Determine which memory categories to search based on the request."""
        if request.categories:
            return request.categories
        
        # Default categories based on context type
        if request.context_type == ContextType.AGENT_TASK and request.agent_type:
            agent_filter = self.agent_role_filters.get(request.agent_type, {})
            return agent_filter.get("primary_categories", [MemoryCategory.PATTERN, MemoryCategory.PROJECT])
        
        elif request.context_type == ContextType.CODE_REVIEW:
            return [MemoryCategory.PATTERN, MemoryCategory.TEAM, MemoryCategory.ERROR]
        
        elif request.context_type == ContextType.ARCHITECTURE_DECISION:
            return [MemoryCategory.PROJECT, MemoryCategory.PATTERN]
        
        elif request.context_type == ContextType.DEBUGGING_SESSION:
            return [MemoryCategory.ERROR, MemoryCategory.PATTERN]
        
        else:
            return [MemoryCategory.PATTERN, MemoryCategory.PROJECT]
    
    def _prepare_search_queries(self, request: ContextRequest) -> List[str]:
        """Prepare search queries based on the request."""
        queries = []
        
        # Primary query from task description
        if request.task_description:
            queries.append(request.task_description)
        
        # Keyword-based queries
        if request.keywords:
            queries.extend(request.keywords)
        
        # Agent-specific queries
        if request.agent_type and request.agent_type in self.agent_role_filters:
            agent_keywords = self.agent_role_filters[request.agent_type]["keywords"]
            queries.extend(agent_keywords)
        
        # Context type specific queries
        if request.context_type == ContextType.CODE_REVIEW:
            queries.extend(["code quality", "review patterns", "best practices"])
        elif request.context_type == ContextType.ARCHITECTURE_DECISION:
            queries.extend(["architectural patterns", "design decisions", "technology choices"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        return unique_queries[:5]  # Limit to top 5 queries
    
    async def _retrieve_category_memories(self, category: MemoryCategory, query: str, 
                                        request: ContextRequest) -> List[Dict[str, Any]]:
        """Retrieve memories for a specific category and query."""
        try:
            # Build search parameters
            project_filter = None
            if request.scope == ContextScope.PROJECT_SPECIFIC and request.project_name:
                project_filter = request.project_name
            
            # Time window filtering
            search_tags = request.priority_tags.copy()
            if request.time_window_days:
                cutoff_date = datetime.now() - timedelta(days=request.time_window_days)
                search_tags.append(f"after_{cutoff_date.strftime('%Y_%m_%d')}")
            
            # Execute search
            response = await self.memory.retrieve_memories(
                category=category,
                query=query,
                project_filter=project_filter,
                tags=search_tags if search_tags else None,
                limit=min(request.max_memories // 2, 10)  # Distribute across queries
            )
            
            if response.success and response.data:
                memories = response.data.get("memories", [])
                
                # Apply agent role filters if applicable
                if request.agent_type and request.agent_type in self.agent_role_filters:
                    memories = self._apply_agent_filters(memories, request.agent_type)
                
                return memories
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories for category {category.value}, query '{query}': {e}")
            return []
    
    def _apply_agent_filters(self, memories: List[Dict[str, Any]], agent_type: str) -> List[Dict[str, Any]]:
        """Apply agent-specific filters to memories."""
        agent_filter = self.agent_role_filters.get(agent_type, {})
        exclude_tags = set(agent_filter.get("exclude_tags", []))
        
        if not exclude_tags:
            return memories
        
        filtered_memories = []
        for memory in memories:
            memory_tags = set(memory.get("metadata", {}).get("tags", []))
            if not memory_tags.intersection(exclude_tags):
                filtered_memories.append(memory)
        
        return filtered_memories
    
    async def _apply_pattern_recognition(self, bundle: ContextBundle) -> ContextBundle:
        """Apply advanced pattern recognition to enhance memory selection."""
        try:
            # Get pattern recognizer configs
            recognizers = self.pattern_recognizers
            
            # Apply success pattern recognition
            for category, memories in bundle.memories_by_category.items():
                enhanced_memories = []
                for memory in memories:
                    memory_metadata = memory.get("metadata", {})
                    memory_tags = set(memory_metadata.get("tags", []))
                    
                    # Check for success indicators
                    success_tags = set(recognizers["success_indicators"]["tags"])
                    if memory_tags.intersection(success_tags):
                        memory["pattern_boost"] = recognizers["success_indicators"]["weight_multiplier"]
                        memory["pattern_type"] = "success_pattern"
                    
                    # Check for team preferences
                    team_tags = set(recognizers["team_preferences"]["tags"])
                    if memory_tags.intersection(team_tags):
                        memory["pattern_boost"] = memory.get("pattern_boost", 1.0) * recognizers["team_preferences"]["weight_multiplier"]
                        memory["pattern_type"] = memory.get("pattern_type", "") + "_team_preferred"
                    
                    # Check for error prevention patterns
                    error_tags = set(recognizers["error_prevention"]["tags"])
                    if memory_tags.intersection(error_tags):
                        memory["pattern_boost"] = memory.get("pattern_boost", 1.0) * recognizers["error_prevention"]["weight_multiplier"]
                        memory["pattern_type"] = memory.get("pattern_type", "") + "_error_prevention"
                    
                    enhanced_memories.append(memory)
                
                bundle.memories_by_category[category] = enhanced_memories
            
            logger.debug(f"Applied pattern recognition to {bundle.total_memories} memories")
            return bundle
            
        except Exception as e:
            logger.error(f"Failed to apply pattern recognition: {e}")
            return bundle
    
    async def _load_project_context_history(self, bundle: ContextBundle) -> ContextBundle:
        """Load project-specific context history for enhanced decision making."""
        try:
            if not bundle.request.project_name:
                return bundle
            
            project_name = bundle.request.project_name
            
            # Load architectural decisions for this project
            arch_decisions = await self._retrieve_project_memories(
                project_name, "architectural decisions", MemoryCategory.PROJECT, limit=5
            )
            
            # Load team-specific patterns for this project
            team_patterns = await self._retrieve_project_memories(
                project_name, "team patterns coding standards", MemoryCategory.TEAM, limit=3
            )
            
            # Load historical errors and their solutions for this project
            error_history = await self._retrieve_project_memories(
                project_name, "errors bugs fixes", MemoryCategory.ERROR, limit=5
            )
            
            # Load successful implementation patterns for this project
            success_patterns = await self._retrieve_project_memories(
                project_name, "successful implementation", MemoryCategory.PATTERN, limit=5
            )
            
            # Add to bundle as project history context
            bundle.project_history = {
                "architectural_decisions": arch_decisions,
                "team_patterns": team_patterns,
                "error_history": error_history,
                "success_patterns": success_patterns,
                "loaded_at": datetime.now().isoformat()
            }
            
            # Merge into existing categories with special tagging
            for memory in arch_decisions + team_patterns + error_history + success_patterns:
                memory["context_source"] = "project_history"
                category = memory.get("metadata", {}).get("category", "project")
                if category in bundle.memories_by_category:
                    bundle.memories_by_category[category].append(memory)
                else:
                    bundle.memories_by_category[category] = [memory]
            
            logger.info(f"Loaded project context history for {project_name}: {len(arch_decisions + team_patterns + error_history + success_patterns)} memories")
            return bundle
            
        except Exception as e:
            logger.error(f"Failed to load project context history: {e}")
            return bundle
    
    async def _retrieve_project_memories(self, project_name: str, query: str, 
                                       category: MemoryCategory, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve project-specific memories for a given query and category."""
        try:
            response = await self.memory.retrieve_memories(
                category=category,
                query=query,
                project_filter=project_name,
                limit=limit
            )
            
            if response.success and response.data:
                return response.data.get("memories", [])
            return []
            
        except Exception as e:
            logger.error(f"Failed to retrieve project memories for {project_name}: {e}")
            return []
    
    def _apply_context_filtering(self, bundle: ContextBundle) -> ContextBundle:
        """Apply context filtering and boundary management based on agent role and security."""
        try:
            filters_applied = []
            
            # Apply security-based filtering
            security_level = self._determine_security_level(bundle.request)
            bundle.security_level = security_level
            
            # Apply team access filtering
            team_access = self._determine_team_access(bundle.request)
            bundle.team_access_level = team_access
            
            # Filter memories based on security and access levels
            filtered_memories = {}
            for category, memories in bundle.memories_by_category.items():
                filtered_category_memories = []
                for memory in memories:
                    if self._memory_passes_filters(memory, security_level, team_access):
                        filtered_category_memories.append(memory)
                    else:
                        filters_applied.append(f"filtered_{category}_memory")
                
                if filtered_category_memories:
                    filtered_memories[category] = filtered_category_memories
            
            bundle.memories_by_category = filtered_memories
            
            # Apply scope-based filtering
            if bundle.request.scope == ContextScope.PROJECT_SPECIFIC:
                filters_applied.append("project_scope_filter")
                bundle = self._apply_project_scope_filter(bundle)
            elif bundle.request.scope == ContextScope.GLOBAL_PATTERNS:
                filters_applied.append("global_patterns_filter")
                bundle = self._apply_global_patterns_filter(bundle)
            
            # Apply agent role boundaries
            if bundle.request.agent_type:
                filters_applied.append(f"{bundle.request.agent_type}_role_boundaries")
                bundle = self._apply_agent_role_boundaries(bundle)
            
            bundle.context_filters_applied = filters_applied
            
            logger.debug(f"Applied context filters: {filters_applied}")
            return bundle
            
        except Exception as e:
            logger.error(f"Failed to apply context filtering: {e}")
            return bundle
    
    def _determine_security_level(self, request: ContextRequest) -> str:
        """Determine security level based on request context."""
        # Default to public for most operations
        if request.context_type == ContextType.DEBUGGING_SESSION:
            return "team_only"  # Debugging might contain sensitive info
        elif request.context_type == ContextType.ARCHITECTURE_DECISION:
            return "team_only"  # Architecture decisions are team-sensitive
        else:
            return "public"
    
    def _determine_team_access(self, request: ContextRequest) -> str:
        """Determine team access level based on request context."""
        # Most operations can be accessed by all team members
        if request.agent_type in ["architect", "security_engineer"]:
            return "senior_team"  # Senior roles need broader access
        else:
            return "team_members"
    
    def _memory_passes_filters(self, memory: Dict[str, Any], security_level: str, team_access: str) -> bool:
        """Check if a memory passes security and access filters."""
        memory_metadata = memory.get("metadata", {})
        
        # Check security level
        memory_security = memory_metadata.get("security_level", "public")
        security_hierarchy = {"public": 0, "team_only": 1, "sensitive": 2, "confidential": 3}
        
        required_level = security_hierarchy.get(security_level, 0)
        memory_level = security_hierarchy.get(memory_security, 0)
        
        if memory_level > required_level:
            return False
        
        # Check team access
        memory_access = memory_metadata.get("team_access", "all")
        access_hierarchy = {"all": 0, "team_members": 1, "senior_team": 2, "leads_only": 3}
        
        required_access = access_hierarchy.get(team_access, 0)
        memory_access_level = access_hierarchy.get(memory_access, 0)
        
        if memory_access_level > required_access:
            return False
        
        return True
    
    def _apply_project_scope_filter(self, bundle: ContextBundle) -> ContextBundle:
        """Apply project-specific scope filtering."""
        if not bundle.request.project_name:
            return bundle
        
        # Limit cross-project memories
        cross_project_limit = self.team_knowledge_filters["context_scopes"]["project_focused"]["cross_project_limit"]
        cross_project_count = 0
        
        filtered_memories = {}
        for category, memories in bundle.memories_by_category.items():
            category_memories = []
            for memory in memories:
                memory_project = memory.get("metadata", {}).get("project", "")
                if memory_project == bundle.request.project_name:
                    # Always include project-specific memories
                    category_memories.append(memory)
                elif cross_project_count < cross_project_limit:
                    # Include cross-project memories up to limit
                    category_memories.append(memory)
                    cross_project_count += 1
            
            if category_memories:
                filtered_memories[category] = category_memories
        
        bundle.memories_by_category = filtered_memories
        return bundle
    
    def _apply_global_patterns_filter(self, bundle: ContextBundle) -> ContextBundle:
        """Apply global patterns scope filtering."""
        # Focus on high-quality global patterns
        insight_threshold = self.team_knowledge_filters["context_scopes"]["global_insights"]["insight_relevance_threshold"]
        
        filtered_memories = {}
        for category, memories in bundle.memories_by_category.items():
            category_memories = []
            for memory in memories:
                relevance_score = bundle.relevance_scores.get(memory.get("id", ""), 0.0)
                if relevance_score >= insight_threshold:
                    category_memories.append(memory)
            
            if category_memories:
                filtered_memories[category] = category_memories
        
        bundle.memories_by_category = filtered_memories
        return bundle
    
    def _apply_agent_role_boundaries(self, bundle: ContextBundle) -> ContextBundle:
        """Apply agent role-specific boundaries and filters."""
        agent_type = bundle.request.agent_type
        if agent_type not in self.agent_role_filters:
            return bundle
        
        role_config = self.agent_role_filters[agent_type]
        exclude_tags = set(role_config.get("exclude_tags", []))
        
        if not exclude_tags:
            return bundle
        
        # Filter out memories with excluded tags
        filtered_memories = {}
        for category, memories in bundle.memories_by_category.items():
            category_memories = []
            for memory in memories:
                memory_tags = set(memory.get("metadata", {}).get("tags", []))
                if not memory_tags.intersection(exclude_tags):
                    category_memories.append(memory)
            
            if category_memories:
                filtered_memories[category] = category_memories
        
        bundle.memories_by_category = filtered_memories
        return bundle
    
    async def _process_and_score_memories(self, bundle: ContextBundle) -> ContextBundle:
        """Process memories, remove duplicates, and calculate relevance scores."""
        all_memories = []
        seen_ids = set()
        
        # Collect and deduplicate memories
        for category, memories in bundle.memories_by_category.items():
            for memory in memories:
                memory_id = memory.get("id")
                if memory_id and memory_id not in seen_ids:
                    seen_ids.add(memory_id)
                    memory["source_category"] = category
                    all_memories.append(memory)
        
        # Calculate relevance scores
        scored_memories = []
        for memory in all_memories:
            score = self._calculate_relevance_score(memory, bundle.request)
            bundle.relevance_scores[memory.get("id", "")] = score
            scored_memories.append((score, memory))
        
        # Sort by relevance and limit to max_memories
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        top_memories = scored_memories[:bundle.request.max_memories]
        
        # Rebuild category mapping with top memories
        bundle.memories_by_category = {}
        for score, memory in top_memories:
            category = memory.get("source_category", "unknown")
            if category not in bundle.memories_by_category:
                bundle.memories_by_category[category] = []
            bundle.memories_by_category[category].append(memory)
        
        bundle.total_memories = len(top_memories)
        return bundle
    
    def _calculate_relevance_score(self, memory: Dict[str, Any], request: ContextRequest) -> float:
        """Calculate enhanced relevance score for a memory based on the request and pattern recognition."""
        score = 0.0
        memory_content = memory.get("content", "").lower()
        memory_metadata = memory.get("metadata", {})
        memory_tags = set(memory_metadata.get("tags", []))
        
        # Exact match scoring
        if request.task_description:
            task_lower = request.task_description.lower()
            if task_lower in memory_content:
                score += self.pattern_weights["exact_match"]
        
        # Keyword match scoring
        keyword_matches = 0
        total_keywords = len(request.keywords)
        if total_keywords > 0:
            for keyword in request.keywords:
                if keyword.lower() in memory_content:
                    keyword_matches += 1
            keyword_score = (keyword_matches / total_keywords) * self.pattern_weights["keyword_match"]
            score += keyword_score
        
        # Project relevance
        if request.project_name:
            memory_project = memory_metadata.get("project", "")
            if memory_project == request.project_name:
                score += self.pattern_weights["project_relevance"]
        
        # Priority tag boost
        priority_tag_matches = len(memory_tags.intersection(set(request.priority_tags)))
        if priority_tag_matches > 0:
            score += priority_tag_matches * 0.2
        
        # Enhanced pattern recognition scoring
        # Team preference scoring
        team_preference_tags = {"team_standard", "preferred_approach", "recommended"}
        if memory_tags.intersection(team_preference_tags):
            score += self.pattern_weights["team_preference"]
        
        # Success pattern scoring
        success_tags = {"successful", "approved", "high_quality", "best_practice"}
        if memory_tags.intersection(success_tags):
            score += self.pattern_weights["success_pattern"]
        
        # Error prevention scoring
        error_prevention_tags = {"error_prone", "requires_attention", "vulnerability", "anti_pattern"}
        if memory_tags.intersection(error_prevention_tags):
            score += self.pattern_weights["error_prevention"]
        
        # Pattern boost from pattern recognition
        pattern_boost = memory.get("pattern_boost", 1.0)
        score *= pattern_boost
        
        # Context source boost (project history gets extra weight)
        if memory.get("context_source") == "project_history":
            score *= 1.2
        
        # Agent-specific relevance boost
        if request.agent_type and request.agent_type in self.agent_role_filters:
            agent_keywords = self.agent_role_filters[request.agent_type]["keywords"]
            agent_keyword_matches = sum(1 for kw in agent_keywords if kw.lower() in memory_content)
            if agent_keyword_matches > 0:
                score += (agent_keyword_matches / len(agent_keywords)) * 0.3
        
        # Recency scoring with learning boost
        stored_at_str = memory_metadata.get("stored_at", "")
        if stored_at_str:
            try:
                stored_at = datetime.fromisoformat(stored_at_str.replace('Z', '+00:00'))
                days_ago = (datetime.now() - stored_at.replace(tzinfo=None)).days
                recency_score = max(0, 1 - (days_ago / 365)) * self.pattern_weights["recency"]
                
                # Recent learning boost
                recent_learning_tags = {"lesson_learned", "recent_discovery", "new_approach"}
                if memory_tags.intersection(recent_learning_tags) and days_ago <= 30:
                    recency_score *= 1.5
                
                score += recency_score
            except:
                pass  # Skip recency scoring if date parsing fails
        
        return score
    
    def _categorize_memories(self, bundle: ContextBundle) -> ContextBundle:
        """Categorize memories into specific lists for easier access."""
        for category, memories in bundle.memories_by_category.items():
            if category == MemoryCategory.PATTERN.value:
                bundle.patterns.extend(memories)
            elif category == MemoryCategory.TEAM.value:
                bundle.team_standards.extend(memories)
            elif category == MemoryCategory.ERROR.value:
                bundle.historical_errors.extend(memories)
            elif category == MemoryCategory.PROJECT.value:
                bundle.project_decisions.extend(memories)
        
        return bundle
    
    def _generate_context_summary(self, bundle: ContextBundle) -> str:
        """Generate a human-readable summary of the prepared context."""
        summary_parts = []
        
        # Basic statistics
        summary_parts.append(f"Context prepared for {bundle.request.context_type.value}")
        if bundle.request.agent_type:
            summary_parts.append(f"Agent: {bundle.request.agent_type}")
        if bundle.request.project_name:
            summary_parts.append(f"Project: {bundle.request.project_name}")
        
        # Memory breakdown
        if bundle.total_memories > 0:
            memory_breakdown = []
            for category, memories in bundle.memories_by_category.items():
                if memories:
                    memory_breakdown.append(f"{len(memories)} {category}")
            
            if memory_breakdown:
                summary_parts.append(f"Memories: {', '.join(memory_breakdown)}")
        
        # Top patterns
        if bundle.patterns:
            top_patterns = [p.get("metadata", {}).get("pattern_type", "pattern") 
                          for p in bundle.patterns[:3]]
            if any(top_patterns):
                summary_parts.append(f"Key patterns: {', '.join(filter(None, top_patterns))}")
        
        # Team standards
        if bundle.team_standards:
            summary_parts.append(f"{len(bundle.team_standards)} team standards available")
        
        # Historical insights
        if bundle.historical_errors:
            summary_parts.append(f"{len(bundle.historical_errors)} historical error patterns")
        
        return " | ".join(summary_parts)
    
    def _get_cached_context(self, request: ContextRequest) -> Optional[ContextBundle]:
        """Check if a cached context is available and still valid."""
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self.context_cache:
            bundle = self.context_cache[cache_key]
            
            # Check if cache is still valid
            age_minutes = (datetime.now() - bundle.prepared_at).total_seconds() / 60
            if age_minutes < self.cache_ttl_minutes:
                return bundle
            else:
                # Remove expired cache
                del self.context_cache[cache_key]
        
        return None
    
    def _cache_context(self, bundle: ContextBundle) -> None:
        """Cache the prepared context bundle."""
        cache_key = self._generate_cache_key(bundle.request)
        self.context_cache[cache_key] = bundle
        
        # Cleanup old cache entries
        self._cleanup_expired_cache()
    
    def _generate_cache_key(self, request: ContextRequest) -> str:
        """Generate a cache key for the request."""
        key_components = [
            request.context_type.value,
            request.scope.value,
            request.project_name or "global",
            request.agent_type or "generic",
            "|".join(sorted(request.keywords)),
            "|".join(sorted([c.value for c in request.categories])),
            str(request.max_memories)
        ]
        return "_".join(key_components)
    
    def _cleanup_expired_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = datetime.now()
        expired_keys = []
        
        for cache_key, bundle in self.context_cache.items():
            age_minutes = (current_time - bundle.prepared_at).total_seconds() / 60
            if age_minutes >= self.cache_ttl_minutes:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.context_cache[key]
    
    async def prepare_agent_context(self, agent_type: str, project_name: str, 
                                  task_description: str, **kwargs) -> ContextBundle:
        """
        Convenience method to prepare context for an agent task.
        
        Args:
            agent_type: Type of agent requesting context
            project_name: Project being worked on
            task_description: Description of the task
            **kwargs: Additional parameters for context request
            
        Returns:
            ContextBundle with prepared context
        """
        request = ContextRequest(
            context_type=ContextType.AGENT_TASK,
            scope=ContextScope.PROJECT_SPECIFIC,
            project_name=project_name,
            agent_type=agent_type,
            task_description=task_description,
            **kwargs
        )
        
        return await self.prepare_context(request)
    
    async def prepare_code_review_context(self, project_name: str, files_changed: List[str],
                                        **kwargs) -> ContextBundle:
        """
        Convenience method to prepare context for code review.
        
        Args:
            project_name: Project being reviewed
            files_changed: List of files that changed
            **kwargs: Additional parameters
            
        Returns:
            ContextBundle with code review context
        """
        request = ContextRequest(
            context_type=ContextType.CODE_REVIEW,
            scope=ContextScope.PROJECT_SPECIFIC,
            project_name=project_name,
            keywords=["code_review", "quality", "standards"] + files_changed,
            categories=[MemoryCategory.PATTERN, MemoryCategory.TEAM, MemoryCategory.ERROR],
            **kwargs
        )
        
        return await self.prepare_context(request)
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        return {
            "cached_contexts": len(self.context_cache),
            "cache_ttl_minutes": self.cache_ttl_minutes,
            "agent_roles_supported": len(self.agent_role_filters),
            "pattern_weights": self.pattern_weights,
            "context_types_supported": [ct.value for ct in ContextType]
        }


# Factory function
def create_mem0_context_manager(memory: ClaudePMMemory) -> Mem0ContextManager:
    """
    Create and initialize a Mem0ContextManager.
    
    Args:
        memory: ClaudePMMemory instance for memory operations
        
    Returns:
        Initialized Mem0ContextManager
    """
    return Mem0ContextManager(memory)