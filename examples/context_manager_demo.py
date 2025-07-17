#!/usr/bin/env python3
"""
Demonstration of the ContextManager component for token optimization.

This script shows how the ContextManager filters context for different agent types,
significantly reducing token usage while preserving relevant information.
"""

import json
from claude_pm.orchestration import ContextManager


def create_sample_context():
    """Create a realistic sample context similar to what an orchestrator would have."""
    return {
        "files": {
            # Documentation files
            "README.md": "# Claude PM Framework\n\nA multi-agent project management framework...",
            "CHANGELOG.md": "# Changelog\n## v0.9.3\n- Added ContextManager for token optimization",
            "docs/architecture.md": "# System Architecture\n\nThe system uses a three-tier agent hierarchy...",
            
            # Code files
            "src/main.py": "import asyncio\nfrom claude_pm import orchestrator\n\ndef main():\n    pass",
            "src/utils.py": "def format_date(date):\n    return date.strftime('%Y-%m-%d')",
            "claude_pm/orchestration/context_manager.py": "class ContextManager:\n    # ... implementation",
            
            # Test files
            "tests/test_main.py": "import pytest\n\ndef test_main():\n    assert True",
            "tests/test_context_manager.py": "def test_filtering():\n    # Test implementation",
            
            # Configuration files
            ".env": "SECRET_KEY=abc123\nAPI_KEY=xyz789",
            "config.yaml": "database:\n  host: localhost\n  port: 5432",
            "docker-compose.yml": "version: '3.8'\nservices:\n  app:\n    image: claude-pm:latest",
            
            # Security files
            "security/audit.log": "2025-07-17: Security scan completed",
            "auth/permissions.py": "ROLES = {'admin': ['read', 'write', 'delete']}",
            
            # Data files
            "migrations/001_initial.sql": "CREATE TABLE users (id INT PRIMARY KEY);",
            "schemas/user.json": '{"type": "object", "properties": {"id": {"type": "integer"}}}',
        },
        
        "current_task": "Update documentation and add comprehensive tests for new features",
        "project_overview": "Claude PM is a multi-agent orchestration framework",
        
        # Agent-specific context sections
        "test_results": {
            "passed": 245,
            "failed": 2,
            "coverage": 89.5
        },
        "git_status": "On branch feature/context-manager\n3 files changed",
        "active_tickets": ["ISS-0120", "ISS-0121", "ISS-0122"],
        "technical_specs": {
            "language": "Python 3.9+",
            "frameworks": ["pytest", "asyncio", "tiktoken"]
        },
        "deployment_config": {
            "environment": "production",
            "replicas": 3
        },
        "security_policies": {
            "encryption": "AES-256",
            "auth": "JWT tokens"
        },
        "database_schema": {
            "tables": ["users", "agents", "tasks", "interactions"]
        },
        
        # Large data that should be filtered
        "debug_logs": "x" * 50000,  # 50KB of logs
        "previous_interactions": ["interaction1", "interaction2"] * 1000  # Large history
    }


def format_size(size_bytes):
    """Format size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} GB"


def main():
    """Demonstrate ContextManager functionality."""
    print("=== ContextManager Token Optimization Demo ===\n")
    
    # Initialize the context manager
    context_manager = ContextManager()
    
    # Create sample context
    full_context = create_sample_context()
    
    # Calculate original size
    original_tokens = context_manager.get_context_size_estimate(full_context)
    original_json = json.dumps(full_context, indent=2)
    original_bytes = len(original_json.encode('utf-8'))
    
    print(f"Original Context:")
    print(f"  - Tokens: {original_tokens:,}")
    print(f"  - Size: {format_size(original_bytes)}")
    print(f"  - Files: {len(full_context.get('files', {}))}")
    print(f"  - Sections: {len(full_context)}")
    print()
    
    # Test filtering for different agent types
    agent_types = [
        "documentation",
        "qa", 
        "engineer",
        "security",
        "data_engineer",
        "ops"
    ]
    
    print("Context Filtering by Agent Type:")
    print("-" * 60)
    
    for agent_type in agent_types:
        # Filter context for this agent
        filtered = context_manager.filter_context_for_agent(agent_type, full_context)
        
        # Calculate filtered size
        filtered_tokens = context_manager.get_context_size_estimate(filtered)
        filtered_json = json.dumps(filtered, indent=2)
        filtered_bytes = len(filtered_json.encode('utf-8'))
        
        # Calculate reduction
        token_reduction = ((original_tokens - filtered_tokens) / original_tokens * 100) if original_tokens > 0 else 0
        byte_reduction = ((original_bytes - filtered_bytes) / original_bytes * 100) if original_bytes > 0 else 0
        
        # Count filtered files
        filtered_files = len(filtered.get('files', {}))
        
        print(f"\n{agent_type.upper()} Agent:")
        print(f"  - Tokens: {filtered_tokens:,} ({token_reduction:.1f}% reduction)")
        print(f"  - Size: {format_size(filtered_bytes)} ({byte_reduction:.1f}% reduction)")
        print(f"  - Files: {filtered_files}/{len(full_context.get('files', {}))}")
        
        # Show what files were included
        if filtered_files > 0:
            print(f"  - Included files:")
            for file_path in sorted(filtered.get('files', {}).keys())[:5]:
                print(f"    • {file_path}")
            if filtered_files > 5:
                print(f"    • ... and {filtered_files - 5} more")
    
    print("\n" + "-" * 60)
    
    # Demonstrate shared context functionality
    print("\nShared Context Demo:")
    
    # Simulate agents updating shared context
    context_manager.update_shared_context("doc_agent_001", {
        "latest_version": "0.9.3",
        "changelog_complete": True
    })
    
    context_manager.update_shared_context("qa_agent_001", {
        "test_status": "passed",
        "coverage": 89.5
    })
    
    # Show how QA agent sees shared context from related agents
    qa_filtered = context_manager.filter_context_for_agent("qa", {})
    shared = qa_filtered.get("shared_context", {})
    
    print(f"\nQA Agent sees {len(shared)} shared context items:")
    for key, value in shared.items():
        print(f"  - {key}: {value['value']}")
    
    # Show statistics
    print(f"\n{'-' * 60}")
    print("\nContext Manager Statistics:")
    stats = context_manager.get_filter_statistics()
    print(f"  - Registered filters: {stats['registered_filters']}")
    print(f"  - Agent types: {', '.join(stats['agent_types'][:5])}...")
    print(f"  - Shared context items: {stats['shared_context_items']}")
    
    print("\n✅ Demo complete! The ContextManager successfully reduces token usage")
    print("   while preserving agent-specific relevant information.")


if __name__ == "__main__":
    main()