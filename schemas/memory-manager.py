"""
Claude PM Framework - Memory Management System
Implementation of memory categorization, tagging, and retrieval system.
"""

import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import uuid

from memory_schemas import (
    BaseMemorySchema, ProjectMemorySchema, PatternMemorySchema,
    TeamMemorySchema, ErrorMemorySchema, MemoryCategory,
    MemoryTagSchema, MemoryRelationSchema, MemorySearchRequest,
    MemorySearchResult, get_schema_for_category, validate_memory_schema
)


class ClaudePMMemoryManager:
    """
    Core memory management system for Claude PM Framework.
    Handles categorization, tagging, storage, and retrieval of memories.
    """
    
    def __init__(self, mem0_client=None):
        """Initialize memory manager with optional mem0 client."""
        self.mem0_client = mem0_client
        self.tag_registry: Dict[str, MemoryTagSchema] = {}
        self.memory_relations: List[MemoryRelationSchema] = []
        
        # Initialize default tags
        self._initialize_default_tags()
    
    def _initialize_default_tags(self):
        """Initialize default tag categories for the system."""
        default_tags = [
            # Technology tags
            ("python", "technology", "Python programming language"),
            ("javascript", "technology", "JavaScript programming language"),
            ("typescript", "technology", "TypeScript programming language"),
            ("react", "technology", "React frontend framework"),
            ("fastapi", "technology", "FastAPI Python framework"),
            ("docker", "technology", "Docker containerization"),
            
            # Domain tags
            ("backend", "domain", "Backend development"),
            ("frontend", "domain", "Frontend development"),
            ("devops", "domain", "DevOps and infrastructure"),
            ("testing", "domain", "Testing and QA"),
            ("security", "domain", "Security-related"),
            ("performance", "domain", "Performance optimization"),
            
            # Priority tags
            ("urgent", "priority", "Urgent/time-sensitive"),
            ("blocker", "priority", "Blocking other work"),
            ("optimization", "priority", "Performance optimization"),
            ("technical-debt", "priority", "Technical debt"),
            
            # Pattern tags
            ("design-pattern", "pattern", "Software design pattern"),
            ("anti-pattern", "pattern", "Anti-pattern to avoid"),
            ("best-practice", "pattern", "Recommended best practice"),
            ("workflow", "pattern", "Development workflow"),
            
            # Context tags
            ("onboarding", "context", "New team member onboarding"),
            ("debugging", "context", "Debugging and troubleshooting"),
            ("architecture", "context", "System architecture"),
            ("deployment", "context", "Deployment and release"),
        ]
        
        for tag_name, category, description in default_tags:
            self.tag_registry[tag_name] = MemoryTagSchema(
                tag_name=tag_name,
                tag_category=category,
                description=description
            )
    
    def create_memory(
        self,
        category: MemoryCategory,
        title: str,
        content: str,
        **kwargs
    ) -> str:
        """
        Create a new memory with the appropriate schema.
        
        Args:
            category: Memory category type
            title: Memory title
            content: Memory content
            **kwargs: Additional schema-specific fields
            
        Returns:
            memory_id: Unique identifier for the created memory
        """
        # Generate unique memory ID
        memory_id = str(uuid.uuid4())
        
        # Prepare base data
        memory_data = {
            "memory_id": memory_id,
            "category": category,
            "title": title,
            "content": content,
            "created_at": datetime.now(),
            **kwargs
        }
        
        # Validate against appropriate schema
        schema_class = get_schema_for_category(category)
        validated_memory = schema_class(**memory_data)
        
        # Update tag usage counts
        for tag in validated_memory.tags:
            if tag in self.tag_registry:
                self.tag_registry[tag].usage_count += 1
        
        # Store in mem0 if client available
        if self.mem0_client:
            self._store_in_mem0(validated_memory)
        
        return memory_id
    
    def _store_in_mem0(self, memory: BaseMemorySchema):
        """Store memory in mem0AI service."""
        try:
            # Convert memory to messages format for mem0
            messages = [
                {"role": "system", "content": f"Memory Category: {memory.category.value}"},
                {"role": "system", "content": f"Title: {memory.title}"},
                {"role": "user", "content": memory.content}
            ]
            
            # Add metadata
            metadata = {
                "memory_id": memory.memory_id,
                "category": memory.category.value,
                "title": memory.title,
                "tags": memory.tags,
                "priority": memory.priority.value,
                "created_at": memory.created_at.isoformat()
            }
            
            # Store in mem0
            self.mem0_client.add(
                messages=messages,
                user_id=memory.user_id or "claude_pm_system",
                agent_id=memory.agent_id or "claude_pm_agent",
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Warning: Failed to store memory in mem0: {e}")
    
    def search_memories(
        self,
        query: str,
        categories: Optional[List[MemoryCategory]] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[MemorySearchResult]:
        """
        Search memories with filtering options.
        
        Args:
            query: Search query string
            categories: Filter by memory categories
            tags: Filter by tags
            project_id: Filter by project
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        if not self.mem0_client:
            return []
        
        try:
            # Build search filters
            filters = {}
            if categories:
                filters["category"] = [cat.value for cat in categories]
            if tags:
                filters["tags"] = tags
            if project_id:
                filters["project_id"] = project_id
            
            # Search in mem0
            results = self.mem0_client.search(
                query=query,
                user_id="claude_pm_system",
                filters=filters,
                limit=limit
            )
            
            # Convert to search result format
            search_results = []
            for result in results:
                # Extract memory data from result
                memory_data = result.get("metadata", {})
                memory_content = result.get("memory", "")
                
                # Create appropriate memory schema
                category = MemoryCategory(memory_data.get("category", "project"))
                schema_class = get_schema_for_category(category)
                
                # Build memory object
                memory = schema_class(
                    memory_id=memory_data.get("memory_id"),
                    category=category,
                    title=memory_data.get("title", ""),
                    content=memory_content,
                    tags=memory_data.get("tags", []),
                    priority=memory_data.get("priority", "medium")
                )
                
                # Create search result
                search_result = MemorySearchResult(
                    memory=memory,
                    relevance_score=result.get("score", 0.0),
                    context_snippet=memory_content[:200] + "..." if len(memory_content) > 200 else memory_content
                )
                
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            print(f"Warning: Memory search failed: {e}")
            return []
    
    def add_tag(self, tag_name: str, category: str, description: str = "") -> bool:
        """Add a new tag to the registry."""
        if tag_name in self.tag_registry:
            return False
        
        self.tag_registry[tag_name] = MemoryTagSchema(
            tag_name=tag_name,
            tag_category=category,
            description=description
        )
        return True
    
    def get_tags_by_category(self, category: str) -> List[MemoryTagSchema]:
        """Get all tags in a specific category."""
        return [tag for tag in self.tag_registry.values() if tag.tag_category == category]
    
    def add_memory_relation(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        strength: float = 1.0,
        description: str = ""
    ) -> bool:
        """Add a relationship between two memories."""
        relation = MemoryRelationSchema(
            source_memory_id=source_id,
            target_memory_id=target_id,
            relationship_type=relationship_type,
            strength=strength,
            description=description
        )
        
        self.memory_relations.append(relation)
        return True
    
    def get_related_memories(self, memory_id: str) -> List[MemoryRelationSchema]:
        """Get all memories related to a specific memory."""
        return [
            relation for relation in self.memory_relations
            if relation.source_memory_id == memory_id or relation.target_memory_id == memory_id
        ]
    
    def categorize_content(self, content: str) -> MemoryCategory:
        """
        Automatically categorize content based on keywords and patterns.
        
        Args:
            content: Content to categorize
            
        Returns:
            Suggested memory category
        """
        content_lower = content.lower()
        
        # Pattern keywords
        pattern_keywords = ["pattern", "solution", "approach", "method", "technique", "best practice"]
        if any(keyword in content_lower for keyword in pattern_keywords):
            return MemoryCategory.PATTERN
        
        # Error keywords
        error_keywords = ["error", "bug", "issue", "problem", "exception", "failure", "debug"]
        if any(keyword in content_lower for keyword in error_keywords):
            return MemoryCategory.ERROR
        
        # Team keywords
        team_keywords = ["standard", "convention", "guideline", "process", "workflow", "policy"]
        if any(keyword in content_lower for keyword in team_keywords):
            return MemoryCategory.TEAM
        
        # Default to project
        return MemoryCategory.PROJECT
    
    def suggest_tags(self, content: str, category: MemoryCategory) -> List[str]:
        """
        Suggest tags based on content analysis.
        
        Args:
            content: Content to analyze
            category: Memory category
            
        Returns:
            List of suggested tag names
        """
        content_lower = content.lower()
        suggested_tags = []
        
        # Technology detection
        tech_keywords = {
            "python": ["python", "py", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "npm"],
            "typescript": ["typescript", "ts"],
            "react": ["react", "jsx", "component"],
            "docker": ["docker", "container", "dockerfile"],
        }
        
        for tag, keywords in tech_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                suggested_tags.append(tag)
        
        # Domain detection
        domain_keywords = {
            "backend": ["api", "server", "database", "endpoint"],
            "frontend": ["ui", "interface", "component", "styling"],
            "testing": ["test", "spec", "mock", "coverage"],
            "security": ["auth", "password", "token", "permission"],
            "performance": ["performance", "optimization", "speed", "memory"],
        }
        
        for tag, keywords in domain_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                suggested_tags.append(tag)
        
        # Category-specific suggestions
        if category == MemoryCategory.PATTERN:
            suggested_tags.append("design-pattern")
        elif category == MemoryCategory.ERROR:
            suggested_tags.append("debugging")
        elif category == MemoryCategory.TEAM:
            suggested_tags.append("best-practice")
        
        return list(set(suggested_tags))  # Remove duplicates
    
    def export_schema_documentation(self) -> str:
        """Export complete schema documentation in markdown format."""
        doc = """# Claude PM Framework - Memory Schema Documentation

## Overview

The Claude PM Framework uses a comprehensive memory schema system to categorize and organize different types of project knowledge.

## Memory Categories

### 1. Project Memory (ProjectMemorySchema)
**Purpose**: Store architectural decisions and project-specific knowledge.

**Key Fields**:
- `decision_type`: Type of architectural decision
- `decision_rationale`: Reasoning behind the decision
- `alternatives_considered`: Other options evaluated
- `impact_scope`: Areas of codebase affected
- `implementation_steps`: Steps taken to implement
- `success_criteria`: Criteria for measuring success

### 2. Pattern Memory (PatternMemorySchema)
**Purpose**: Store successful solution patterns and best practices.

**Key Fields**:
- `pattern_type`: Type of pattern (design, architectural, workflow)
- `problem_domain`: Problem domain addressed
- `problem_description`: Problem this pattern solves
- `solution_approach`: How the pattern solves the problem
- `applicable_contexts`: When to use this pattern
- `success_rate`: Effectiveness when applied

### 3. Team Memory (TeamMemorySchema)
**Purpose**: Store team coding standards, conventions, and preferences.

**Key Fields**:
- `standard_type`: Type of standard (coding, testing, documentation)
- `enforcement_level`: How strictly enforced (required, recommended, optional)
- `examples`: Examples of correct implementation
- `linting_rules`: Automated linting rules
- `compliance_rate`: Team compliance rate

### 4. Error Memory (ErrorMemorySchema)
**Purpose**: Store bug patterns, error analysis, and debugging knowledge.

**Key Fields**:
- `error_type`: Type of error (runtime, logic, performance, security)
- `severity`: Error severity level
- `error_symptoms`: Observable symptoms
- `root_causes`: Identified root causes
- `successful_solution`: Solution that worked
- `prevention_strategies`: How to prevent this error

## Tagging System

### Tag Categories
- **Technology**: python, javascript, react, docker, etc.
- **Domain**: backend, frontend, devops, testing, security
- **Priority**: urgent, blocker, optimization, technical-debt
- **Pattern**: design-pattern, anti-pattern, best-practice, workflow
- **Context**: onboarding, debugging, architecture, deployment

## Memory Relationships

Memories can be related through:
- **Related**: General relationship
- **Supersedes**: Newer memory replaces older one
- **Conflicts**: Memories that contradict each other
- **Extends**: Memory that builds upon another

## Usage Examples

### Creating a Project Memory
```python
memory_manager.create_memory(
    category=MemoryCategory.PROJECT,
    title="Migration to FastAPI",
    content="Decision to migrate from Flask to FastAPI for better async support",
    decision_type="tech_stack",
    decision_rationale="Need better async handling for real-time features",
    alternatives_considered=["Django", "Tornado"],
    tags=["python", "backend", "architecture"]
)
```

### Searching Memories
```python
results = memory_manager.search_memories(
    query="async database connection",
    categories=[MemoryCategory.PATTERN, MemoryCategory.ERROR],
    tags=["python", "backend"],
    limit=5
)
```

## Schema Validation

All memories are validated against their appropriate schema before storage, ensuring data consistency and completeness.
"""
        
        return doc


# Factory function for creating memory manager
def create_memory_manager(mem0_client=None) -> ClaudePMMemoryManager:
    """Create and initialize a memory manager instance."""
    return ClaudePMMemoryManager(mem0_client=mem0_client)