"""
Context Manager for intelligent agent-specific context filtering.

This module provides the ContextManager class that filters context based on agent type,
tracks agent interaction history, and optimizes token usage through intelligent filtering.
"""

import re
import os
import json
import tiktoken
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Use project standard logging configuration
from claude_pm.core.logging_config import get_logger
logger = get_logger(__name__)


@dataclass
class AgentInteraction:
    """Represents a single agent interaction."""
    timestamp: datetime
    agent_id: str
    agent_type: str
    context_size: int
    filtered_size: int
    request: Optional[str] = None
    response: Optional[str] = None
    additional_context_requested: bool = False


@dataclass
class ContextFilter:
    """Defines filtering rules for a specific agent type."""
    agent_type: str
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    file_extensions: List[str] = field(default_factory=list)
    directory_patterns: List[str] = field(default_factory=list)
    max_file_size: int = 100000  # Max size in characters per file
    priority_keywords: List[str] = field(default_factory=list)
    context_sections: List[str] = field(default_factory=list)


class ContextManager:
    """
    Manages context filtering for different agent types to optimize token usage.
    
    Key features:
    - Agent-specific context filtering based on predefined rules
    - Interaction history tracking (last 3 interactions per agent)
    - Shared context updates between agents
    - Token usage estimation and monitoring
    - Support for custom agent types
    """
    
    def __init__(self):
        """Initialize the ContextManager with default filters for core agent types."""
        self.filters: Dict[str, ContextFilter] = self._initialize_default_filters()
        self.interaction_history: Dict[str, List[AgentInteraction]] = {}
        self.shared_context: Dict[str, Any] = {}
        self.token_encoder = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        self._claude_md_cache: Dict[str, Dict[str, Any]] = {}  # Cache for CLAUDE.md deduplication
        
        logger.info("ContextManager initialized with filters for %d agent types", 
                   len(self.filters))
    
    def _initialize_default_filters(self) -> Dict[str, ContextFilter]:
        """Initialize default context filters for all 8 core agent types."""
        filters = {
            "documentation": ContextFilter(
                agent_type="documentation",
                include_patterns=[r"README", r"CHANGELOG", r"CONTRIBUTING", r"LICENSE"],
                file_extensions=[".md", ".rst", ".txt", ".adoc"],
                directory_patterns=["docs/", "documentation/", "wiki/"],
                priority_keywords=["documentation", "changelog", "release", "version"],
                context_sections=["project_overview", "documentation_status", "recent_changes"]
            ),
            
            "qa": ContextFilter(
                agent_type="qa",
                include_patterns=[r"test_", r"_test\.py", r"conftest", r"pytest"],
                file_extensions=[".py", ".yaml", ".yml", ".json"],
                directory_patterns=["tests/", "test/", "spec/", ".github/workflows/"],
                priority_keywords=["test", "quality", "coverage", "lint", "validation"],
                context_sections=["test_results", "coverage_reports", "quality_metrics"]
            ),
            
            "engineer": ContextFilter(
                agent_type="engineer",
                include_patterns=[r"\.py$", r"\.js$", r"\.ts$", r"\.java$", r"\.cpp$"],
                file_extensions=[".py", ".js", ".ts", ".java", ".cpp", ".h", ".c"],
                directory_patterns=["src/", "lib/", "claude_pm/", "app/"],
                exclude_patterns=[r"test_", r"_test\.py", r"\.min\.js"],
                priority_keywords=["implementation", "feature", "bug", "refactor", "code"],
                context_sections=["technical_specs", "architecture", "dependencies"]
            ),
            
            "research": ContextFilter(
                agent_type="research",
                include_patterns=[r"research", r"analysis", r"benchmark", r"comparison"],
                file_extensions=[".md", ".pdf", ".txt", ".ipynb"],
                directory_patterns=["research/", "analysis/", "benchmarks/", "docs/"],
                priority_keywords=["research", "analysis", "comparison", "evaluation"],
                context_sections=["research_findings", "external_references", "benchmarks"]
            ),
            
            "version_control": ContextFilter(
                agent_type="version_control",
                include_patterns=[r"\.git", r"VERSION", r"package\.json", r"pyproject\.toml"],
                file_extensions=[".gitignore", ".gitattributes"],
                directory_patterns=[".git/", ".github/"],
                priority_keywords=["git", "branch", "merge", "commit", "version"],
                context_sections=["git_status", "branch_info", "recent_commits"]
            ),
            
            "ops": ContextFilter(
                agent_type="ops",
                include_patterns=[r"Dockerfile", r"docker-compose", r"\.yml$", r"\.yaml$"],
                file_extensions=[".yml", ".yaml", ".sh", ".bash", ".dockerfile"],
                directory_patterns=["scripts/", "deploy/", ".github/workflows/", "infrastructure/"],
                priority_keywords=["deploy", "build", "ci", "cd", "infrastructure"],
                context_sections=["deployment_config", "ci_status", "infrastructure"]
            ),
            
            "security": ContextFilter(
                agent_type="security",
                include_patterns=[r"security", r"auth", r"\.env", r"secret", r"key"],
                file_extensions=[".py", ".js", ".env", ".yml"],
                directory_patterns=["security/", "auth/", ".github/"],
                exclude_patterns=[r"\.env\.example"],
                priority_keywords=["security", "vulnerability", "auth", "encryption", "audit"],
                context_sections=["security_policies", "vulnerabilities", "audit_logs"]
            ),
            
            "data_engineer": ContextFilter(
                agent_type="data_engineer",
                include_patterns=[r"schema", r"migration", r"model", r"database"],
                file_extensions=[".sql", ".py", ".json", ".yaml"],
                directory_patterns=["migrations/", "models/", "data/", "schemas/"],
                priority_keywords=["database", "api", "schema", "migration", "data"],
                context_sections=["database_schema", "api_endpoints", "data_models"]
            ),
            
            "orchestrator": ContextFilter(
                agent_type="orchestrator",
                include_patterns=[r"CLAUDE\.md", r"README", r"TODO"],
                file_extensions=[".md", ".txt", ".json", ".yaml"],
                directory_patterns=[".claude-pm/", "docs/"],
                priority_keywords=["orchestrate", "coordinate", "delegate", "manage", "framework"],
                context_sections=["project_overview", "active_tasks", "agent_status"]
            )
        }
        
        return filters
    
    def register_custom_filter(self, agent_type: str, filter_config: ContextFilter) -> None:
        """Register a custom context filter for a new agent type."""
        self.filters[agent_type] = filter_config
        logger.info("Registered custom filter for agent type: %s", agent_type)
    
    def _deduplicate_claude_md_content(self, claude_md_files: Dict[str, str]) -> Dict[str, str]:
        """
        Deduplicate CLAUDE.md content from multiple files.
        
        Strategy:
        1. Parse content into sections (using headers)
        2. Compute hashes for each section
        3. Keep only unique sections, prioritizing closer files
        4. Merge unique sections intelligently
        
        Args:
            claude_md_files: Dict mapping file paths to their content
            
        Returns:
            Dict with deduplicated content, preserving unique sections
        """
        if not claude_md_files:
            return {}
        
        # Sort files by proximity (project > parent > framework)
        sorted_files = sorted(claude_md_files.items(), key=lambda x: (
            'framework' not in x[0],  # Framework last
            x[0].count('/'),  # Fewer slashes = parent directory
            x[0]  # Alphabetical as tiebreaker
        ), reverse=True)
        
        # Parse sections from each file
        parsed_files = {}
        section_hashes: Dict[str, str] = {}  # hash -> first file containing it
        
        for file_path, content in sorted_files:
            sections = self._parse_markdown_sections(content)
            parsed_files[file_path] = sections
            
            # Track unique sections by full section hash (header + content)
            for section_header, section_content in sections:
                # Hash both header and content to handle same content under different headers
                full_section = f"{section_header}\n{section_content}"
                section_hash = hashlib.md5(full_section.encode()).hexdigest()
                if section_hash not in section_hashes:
                    section_hashes[section_hash] = file_path
        
        # Build deduplicated content - keep at least one file with merged unique content
        deduplicated = {}
        total_original_size = sum(len(content) for content in claude_md_files.values())
        
        # Track which sections belong to which files
        for file_path, sections in parsed_files.items():
            unique_sections = []
            
            for section_header, section_content in sections:
                # Hash both header and content for consistency
                full_section = f"{section_header}\n{section_content}"
                section_hash = hashlib.md5(full_section.encode()).hexdigest()
                # Keep section only if this file was the first to contain it
                if section_hashes[section_hash] == file_path:
                    unique_sections.append((section_header, section_content))
            
            if unique_sections:
                # Reconstruct content from unique sections
                deduplicated_content = '\n\n'.join(
                    f"{header}\n{content}" for header, content in unique_sections
                )
                deduplicated[file_path] = deduplicated_content
        
        # Log deduplication results
        total_deduplicated_size = sum(len(content) for content in deduplicated.values())
        reduction_percent = ((total_original_size - total_deduplicated_size) / total_original_size * 100) if total_original_size > 0 else 0
        
        logger.info(
            "CLAUDE.md deduplication: %d files, %d -> %d chars (%.1f%% reduction)",
            len(claude_md_files), total_original_size, total_deduplicated_size, reduction_percent
        )
        
        return deduplicated
    
    def _parse_markdown_sections(self, content: str) -> List[Tuple[str, str]]:
        """
        Parse markdown content into sections based on headers.
        
        Args:
            content: Markdown content to parse
            
        Returns:
            List of (header, content) tuples
        """
        sections = []
        current_header = "# Introduction"  # Default header for content before first header
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check if line is a header (# or ##)
            if re.match(r'^#{1,3}\s+', line):
                # Save previous section if it has content
                if current_content:
                    sections.append((current_header, '\n'.join(current_content)))
                    current_content = []
                current_header = line
            else:
                current_content.append(line)
        
        # Don't forget the last section
        if current_content:
            sections.append((current_header, '\n'.join(current_content)))
        
        return sections
    
    def _extract_claude_md_files(self, full_context: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract CLAUDE.md files from the full context.
        
        Args:
            full_context: Full context dictionary
            
        Returns:
            Dict mapping file paths to CLAUDE.md content
        """
        claude_md_files = {}
        
        # Check for CLAUDE.md files in various context locations
        if "files" in full_context:
            for file_path, content in full_context["files"].items():
                if file_path.endswith("CLAUDE.md") and isinstance(content, str):
                    claude_md_files[file_path] = content
        
        # Check for inline CLAUDE.md content (sometimes passed directly)
        if "claude_md_content" in full_context:
            if isinstance(full_context["claude_md_content"], dict):
                claude_md_files.update(full_context["claude_md_content"])
            elif isinstance(full_context["claude_md_content"], str):
                claude_md_files["inline_claude_md"] = full_context["claude_md_content"]
        
        # Check for framework instructions
        if "framework_instructions" in full_context:
            claude_md_files["framework_instructions"] = full_context["framework_instructions"]
        
        return claude_md_files
    
    def filter_context_for_agent(self, agent_type: str, full_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter the full context based on agent type to reduce token usage.
        
        Args:
            agent_type: Type of agent (e.g., 'documentation', 'qa', 'engineer')
            full_context: Complete context dictionary
            
        Returns:
            Filtered context specific to the agent type
        """
        if agent_type not in self.filters:
            logger.warning("No filter defined for agent type: %s, returning full context", agent_type)
            return full_context
        
        filter_config = self.filters[agent_type]
        # First, handle CLAUDE.md deduplication
        claude_md_files = self._extract_claude_md_files(full_context)
        deduplicated_claude_md = {}
        
        if claude_md_files:
            deduplicated_claude_md = self._deduplicate_claude_md_content(claude_md_files)
        
        filtered_context = {
            "agent_type": agent_type,
            "timestamp": datetime.now().isoformat(),
            "shared_context": self._filter_shared_context(agent_type)
        }
        
        # Filter file contents based on patterns
        if "files" in full_context:
            filtered_files = self._filter_files(full_context["files"], filter_config)
            # Add back deduplicated CLAUDE.md files for all agents (they may need references)
            if deduplicated_claude_md:
                for file_path, content in deduplicated_claude_md.items():
                    if file_path.endswith("CLAUDE.md"):
                        filtered_files[file_path] = content
            if filtered_files:
                filtered_context["files"] = filtered_files
        
        # Include relevant context sections
        for section in filter_config.context_sections:
            if section in full_context:
                filtered_context[section] = full_context[section]
        
        # Include deduplicated CLAUDE.md if relevant to agent
        # These agent types need framework instructions for orchestration
        if deduplicated_claude_md and agent_type in ['orchestrator', 'pm', 'project_manager', 'project_management']:
            filtered_context["framework_instructions"] = deduplicated_claude_md
        
        # Add priority information based on keywords
        if "current_task" in full_context:
            task_relevance = self._calculate_task_relevance(
                full_context["current_task"], 
                filter_config.priority_keywords
            )
            if task_relevance > 0:
                filtered_context["current_task"] = full_context["current_task"]
                filtered_context["task_relevance_score"] = task_relevance
        
        # Include recent interactions for context continuity
        if agent_type in self.interaction_history:
            recent_interactions = self.interaction_history[agent_type][-3:]
            filtered_context["recent_interactions"] = [
                {
                    "timestamp": i.timestamp.isoformat(),
                    "request": i.request[:200] if i.request else None,
                    "additional_context_requested": i.additional_context_requested
                }
                for i in recent_interactions
            ]
        
        # Log filtering results
        original_size = self.get_context_size_estimate(full_context)
        filtered_size = self.get_context_size_estimate(filtered_context)
        reduction_percent = ((original_size - filtered_size) / original_size * 100) if original_size > 0 else 0
        
        logger.info(
            "Filtered context for %s agent: %d -> %d tokens (%.1f%% reduction)",
            agent_type, original_size, filtered_size, reduction_percent
        )
        
        return filtered_context
    
    def _filter_files(self, files: Dict[str, Any], filter_config: ContextFilter) -> Dict[str, Any]:
        """Filter files based on agent-specific patterns and extensions."""
        filtered_files = {}
        
        for file_path, content in files.items():
            # Skip CLAUDE.md files as they're handled separately with deduplication
            if file_path.endswith("CLAUDE.md"):
                continue
            # Check if file matches include patterns
            include_match = any(
                re.search(pattern, file_path, re.IGNORECASE) 
                for pattern in filter_config.include_patterns
            )
            
            # Check if file matches exclude patterns
            exclude_match = any(
                re.search(pattern, file_path, re.IGNORECASE) 
                for pattern in filter_config.exclude_patterns
            ) if filter_config.exclude_patterns else False
            
            # Check file extension
            extension_match = any(
                file_path.endswith(ext) 
                for ext in filter_config.file_extensions
            ) if filter_config.file_extensions else True
            
            # Check directory patterns
            directory_match = any(
                pattern in file_path 
                for pattern in filter_config.directory_patterns
            ) if filter_config.directory_patterns else True
            
            # Include file if it matches criteria and doesn't match exclude patterns
            if (include_match or extension_match or directory_match) and not exclude_match:
                # Truncate large files
                if isinstance(content, str) and len(content) > filter_config.max_file_size:
                    content = content[:filter_config.max_file_size] + "\n... [truncated]"
                
                filtered_files[file_path] = content
        
        return filtered_files
    
    def _filter_shared_context(self, agent_type: str) -> Dict[str, Any]:
        """Get relevant shared context for the agent type."""
        # Return shared context that might be relevant to this agent
        relevant_context = {}
        
        # Include updates from related agents
        related_agents = self._get_related_agents(agent_type)
        for key, value in self.shared_context.items():
            if any(agent in key for agent in related_agents):
                relevant_context[key] = value
        
        return relevant_context
    
    def _get_related_agents(self, agent_type: str) -> List[str]:
        """Get list of agents that typically share context with the given agent type."""
        relationships = {
            "documentation": ["version_control", "qa"],
            "qa": ["engineer", "documentation", "security"],
            "engineer": ["qa", "research", "data_engineer"],
            "research": ["engineer", "documentation"],
            "version_control": ["documentation", "qa"],
            "ops": ["security", "qa", "engineer"],
            "security": ["qa", "ops", "engineer"],
            "data_engineer": ["engineer", "ops", "security"]
        }
        
        return relationships.get(agent_type, [])
    
    def _calculate_task_relevance(self, task: str, keywords: List[str]) -> float:
        """Calculate relevance score of a task based on priority keywords."""
        if not task or not keywords:
            return 0.0
        
        task_lower = task.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in task_lower)
        return matches / len(keywords) if keywords else 0.0
    
    def update_shared_context(self, agent_id: str, updates: Dict[str, Any]) -> None:
        """
        Update shared context that can be accessed by other agents.
        
        Args:
            agent_id: Unique identifier for the agent
            updates: Dictionary of context updates to share
        """
        for key, value in updates.items():
            context_key = f"{agent_id}_{key}"
            self.shared_context[context_key] = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id
            }
        
        logger.debug("Agent %s updated shared context with %d items", agent_id, len(updates))
    
    def get_agent_history(self, agent_id: str) -> List[AgentInteraction]:
        """
        Get the last 3 interactions for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            List of recent AgentInteraction objects
        """
        if agent_id not in self.interaction_history:
            return []
        
        return self.interaction_history[agent_id][-3:]
    
    def record_interaction(self, agent_id: str, agent_type: str, 
                          context_size: int, filtered_size: int,
                          request: Optional[str] = None, 
                          response: Optional[str] = None,
                          additional_context_requested: bool = False) -> None:
        """Record an agent interaction for history tracking."""
        interaction = AgentInteraction(
            timestamp=datetime.now(),
            agent_id=agent_id,
            agent_type=agent_type,
            context_size=context_size,
            filtered_size=filtered_size,
            request=request,
            response=response,
            additional_context_requested=additional_context_requested
        )
        
        if agent_id not in self.interaction_history:
            self.interaction_history[agent_id] = []
        
        self.interaction_history[agent_id].append(interaction)
        
        # Keep only last 10 interactions per agent to prevent memory bloat
        if len(self.interaction_history[agent_id]) > 10:
            self.interaction_history[agent_id] = self.interaction_history[agent_id][-10:]
    
    def get_context_size_estimate(self, context: Any) -> int:
        """
        Estimate the token count for a given context.
        
        Args:
            context: Context object (dict, str, list, etc.)
            
        Returns:
            Estimated token count
        """
        try:
            # Convert context to string representation
            if isinstance(context, str):
                text = context
            elif isinstance(context, (dict, list)):
                text = json.dumps(context, indent=2, default=str)
            else:
                text = str(context)
            
            # Use tiktoken to count tokens
            tokens = self.token_encoder.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning("Error estimating context size: %s", e)
            # Fallback to character-based estimation (roughly 4 chars per token)
            return len(str(context)) // 4
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """Get statistics about context filtering performance."""
        stats = {
            "registered_filters": len(self.filters),
            "agent_types": list(self.filters.keys()),
            "total_interactions": sum(len(history) for history in self.interaction_history.values()),
            "agents_tracked": len(self.interaction_history),
            "shared_context_items": len(self.shared_context)
        }
        
        # Calculate average reduction percentages per agent type
        reductions = {}
        for agent_id, interactions in self.interaction_history.items():
            if interactions:
                agent_type = interactions[-1].agent_type
                if agent_type not in reductions:
                    reductions[agent_type] = []
                
                for interaction in interactions:
                    if interaction.context_size > 0:
                        reduction = ((interaction.context_size - interaction.filtered_size) 
                                   / interaction.context_size * 100)
                        reductions[agent_type].append(reduction)
        
        avg_reductions = {}
        for agent_type, reduction_list in reductions.items():
            if reduction_list:
                avg_reductions[agent_type] = sum(reduction_list) / len(reduction_list)
        
        stats["average_token_reduction_by_type"] = avg_reductions
        
        return stats
    
    def clear_old_shared_context(self, max_age_hours: int = 24) -> int:
        """Clear shared context items older than specified hours."""
        current_time = datetime.now()
        items_removed = 0
        
        keys_to_remove = []
        for key, value in self.shared_context.items():
            if "timestamp" in value:
                timestamp = datetime.fromisoformat(value["timestamp"])
                age_hours = (current_time - timestamp).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.shared_context[key]
            items_removed += 1
        
        if items_removed > 0:
            logger.info("Cleared %d old shared context items", items_removed)
        
        return items_removed


def create_context_manager() -> ContextManager:
    """Factory function to create a ContextManager instance."""
    return ContextManager()