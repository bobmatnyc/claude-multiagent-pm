"""
Agent Keyword Parser
==================

Translates natural language task descriptions into appropriate agent types
using semantic keyword matching. Supports fuzzy matching and explicit
@agent_name syntax.

Part of ISS-0123: Fix agent selection bug
"""

import re
from typing import Optional, Dict, List, Tuple
from difflib import get_close_matches


class AgentKeywordParser:
    """Parse task descriptions to determine appropriate agent type."""
    
    # Core agent type mappings based on CLAUDE.md patterns
    KEYWORD_MAPPINGS: Dict[str, List[str]] = {
        "engineer": [
            "code", "implement", "develop", "programming", "coding",
            "write code", "create", "build", "fix", "bug", "feature",
            "function", "class", "method", "api", "endpoint",
            "refactor", "optimize", "debug", "integrate", "authentication",
            "payment gateway", "memory leak"
        ],
        "qa": [
            "test", "tests", "validate", "qa", "quality", "assurance",
            "testing", "validation", "verify", "check", "ensure",
            "coverage", "unit test", "integration test", "pytest",
            "assert", "expect", "mock", "fixture", "regression test",
            "regression tests", "run tests", "test suite"
        ],
        "research": [
            "research", "investigate", "analyze", "explore",
            "study", "examine", "review", "understand", "learn",
            "discover", "find", "search", "look into", "assess",
            "evaluate", "compare", "survey", "best practices",
            "microservices", "algorithms", "ml algorithms"
        ],
        "security": [
            "security", "scan", "vulnerability", "vulnerabilities", "secure", "auth",
            "authentication", "authorization", "encrypt", "decrypt",
            "permission", "access", "credential", "token", "ssl",
            "https", "firewall", "penetration", "audit", "penetration testing"
        ],
        "data_engineer": [
            "database", "schema", "sql", "query",
            "table", "migration", "etl", "pipeline", "storage",
            "cache", "caching", "redis", "postgres", "postgresql", "mysql", "mongodb",
            "api integration", "data flow", "backup", "restore",
            "database schema", "set up database", "database optimization",
            "set up postgresql", "postgresql database"
        ],
        "ops": [
            "deploy", "ops", "infrastructure", "devops", "cicd",
            "deployment", "server", "container", "docker", "kubernetes",
            "aws", "cloud", "provision", "scale", "monitor",
            "logging", "metrics", "performance", "load", "production",
            "production server"
        ],
        "documentation": [
            "document", "docs", "readme", "documentation", "write docs",
            "update docs", "api docs", "api documentation", "user guide", "tutorial",
            "manual", "help", "instructions", "changelog", "release notes",
            "update documentation", "documnt", "docmnt", "documentat",  # Include typos
            "documenting", "document the", "update the documentation"
        ],
        "version_control": [
            "branch", "merge", "git", "commit", "push",
            "pull", "rebase", "cherry-pick", "tag",
            "version", "checkout", "stash", "diff",
            "repository", "repo", "fork", "clone",
            "feature branch", "create branch", "new branch"
        ],
        "pm_agent": [
            "pm", "project management", "timeline", "milestone",
            "roadmap", "planning", "schedule", "deadline",
            "project timeline", "update timeline", "milestones"
        ]
    }
    
    # Agent type aliases for flexibility
    AGENT_ALIASES: Dict[str, str] = {
        "eng": "engineer",
        "qa_agent": "qa",
        "tester": "qa",
        "researcher": "research",
        "sec": "security",
        "data": "data_engineer",
        "devops": "ops",
        "operations": "ops",
        "doc": "documentation",
        "documenter": "documentation",
        "git": "version_control",
        "vcs": "version_control",
        "versioner": "version_control"
    }
    
    def __init__(self, fuzzy_threshold: float = 0.6):
        """
        Initialize the parser.
        
        Args:
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0-1)
        """
        self.fuzzy_threshold = fuzzy_threshold
        self._build_reverse_mappings()
    
    def _build_reverse_mappings(self):
        """Build reverse keyword mappings for efficient lookup."""
        self.keyword_to_agent = {}
        for agent_type, keywords in self.KEYWORD_MAPPINGS.items():
            for keyword in keywords:
                self.keyword_to_agent[keyword.lower()] = agent_type
    
    def parse_task_description(self, task_description: str) -> Optional[str]:
        """
        Parse a task description to determine the appropriate agent type.
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Agent type string or None if no match found
            
        Examples:
            >>> parser = AgentKeywordParser()
            >>> parser.parse_task_description("implement user authentication")
            'engineer'
            >>> parser.parse_task_description("run tests for the new feature")
            'qa'
            >>> parser.parse_task_description("@security scan the codebase")
            'security'
        """
        if not task_description:
            return None
            
        task_lower = task_description.lower().strip()
        
        # 1. Check for explicit @agent_name syntax
        explicit_match = re.match(r'@(\w+)\s+', task_lower)
        if explicit_match:
            agent_name = explicit_match.group(1)
            # Check if it's a valid agent type or alias
            if agent_name in self.KEYWORD_MAPPINGS:
                return agent_name
            if agent_name in self.AGENT_ALIASES:
                return self.AGENT_ALIASES[agent_name]
        
        # 2. First check for multi-word phrases (higher priority)
        agent_scores: Dict[str, int] = {}
        
        for agent_type, keywords in self.KEYWORD_MAPPINGS.items():
            for keyword in keywords:
                if ' ' in keyword and keyword in task_lower:
                    # Multi-word phrases get highest priority
                    agent_scores[agent_type] = agent_scores.get(agent_type, 0) + 5
        
        # 3. Extract keywords from task description
        # Remove common words and split
        words = re.findall(r'\b\w+\b', task_lower)
        
        # 4. Score each agent type based on keyword matches
        for word in words:
            # Exact match
            if word in self.keyword_to_agent:
                agent_type = self.keyword_to_agent[word]
                agent_scores[agent_type] = agent_scores.get(agent_type, 0) + 2
            
            # Fuzzy match
            else:
                close_matches = get_close_matches(
                    word, 
                    self.keyword_to_agent.keys(), 
                    n=1, 
                    cutoff=self.fuzzy_threshold
                )
                if close_matches:
                    agent_type = self.keyword_to_agent[close_matches[0]]
                    agent_scores[agent_type] = agent_scores.get(agent_type, 0) + 1
        
        # 5. Special cases handling
        # If "research" appears at the beginning and has a reasonable score, prioritize it
        if task_lower.startswith(("research", "investigate", "analyze", "explore")):
            if "research" in agent_scores and agent_scores["research"] >= 2:
                return "research"
        
        # Check for documentation typos with API - documentation should win
        if any(typo in task_lower for typo in ["documnt", "docmnt", "documentat"]):
            if "documentation" in agent_scores and "engineer" in agent_scores:
                # If documentation score is close to engineer score, prefer documentation
                if agent_scores["documentation"] >= agent_scores["engineer"] - 1:
                    return "documentation"
        
        # 6. Return the agent type with highest score
        if agent_scores:
            return max(agent_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def get_agent_keywords(self, agent_type: str) -> List[str]:
        """
        Get keywords associated with an agent type.
        
        Args:
            agent_type: The agent type to look up
            
        Returns:
            List of keywords or empty list if agent type not found
        """
        # Normalize agent type through aliases
        normalized_type = self.AGENT_ALIASES.get(agent_type, agent_type)
        return self.KEYWORD_MAPPINGS.get(normalized_type, [])
    
    def suggest_agent_type(self, task_description: str) -> List[Tuple[str, int]]:
        """
        Suggest multiple agent types with confidence scores.
        
        Args:
            task_description: Natural language task description
            
        Returns:
            List of (agent_type, score) tuples, sorted by score descending
            
        Example:
            >>> parser = AgentKeywordParser()
            >>> parser.suggest_agent_type("implement tests for the database schema")
            [('qa', 4), ('engineer', 2), ('data_engineer', 2)]
        """
        if not task_description:
            return []
            
        task_lower = task_description.lower().strip()
        
        # Score each agent type
        agent_scores: Dict[str, int] = {}
        
        # First check for multi-word phrases (higher priority)
        for agent_type, keywords in self.KEYWORD_MAPPINGS.items():
            for keyword in keywords:
                if ' ' in keyword and keyword in task_lower:
                    agent_scores[agent_type] = agent_scores.get(agent_type, 0) + 5
        
        # Extract words
        words = re.findall(r'\b\w+\b', task_lower)
        
        for word in words:
            # Exact match
            if word in self.keyword_to_agent:
                agent_type = self.keyword_to_agent[word]
                agent_scores[agent_type] = agent_scores.get(agent_type, 0) + 2
            
            # Fuzzy match
            else:
                close_matches = get_close_matches(
                    word, 
                    self.keyword_to_agent.keys(), 
                    n=3, 
                    cutoff=self.fuzzy_threshold
                )
                for match in close_matches:
                    agent_type = self.keyword_to_agent[match]
                    agent_scores[agent_type] = agent_scores.get(agent_type, 0) + 1
        
        # Sort by score
        return sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)


# Example usage and testing
if __name__ == "__main__":
    parser = AgentKeywordParser()
    
    # Test cases from various task descriptions
    test_cases = [
        "implement user authentication system",
        "run unit tests for the login module",
        "research best practices for API design",
        "@security perform vulnerability scan",
        "setup database schema and migrations",
        "deploy to production server",
        "update API documentation",
        "create new github issue for bug",
        "merge feature branch to main"
    ]
    
    print("Agent Keyword Parser Test Results:")
    print("=" * 50)
    
    for task in test_cases:
        agent_type = parser.parse_task_description(task)
        suggestions = parser.suggest_agent_type(task)
        print(f"\nTask: {task}")
        print(f"Selected Agent: {agent_type}")
        if suggestions:
            print(f"All Suggestions: {suggestions[:3]}")