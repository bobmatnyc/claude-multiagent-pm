"""
Tests for ContextManager CLAUDE.md deduplication functionality.

This module tests the intelligent deduplication of multiple CLAUDE.md files
to reduce token usage while preserving unique content.
"""

import pytest
from claude_pm.orchestration.context_manager import ContextManager


class TestClaudeMdDeduplication:
    """Test CLAUDE.md content deduplication."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context_manager = ContextManager()
        
        # Sample CLAUDE.md content with overlapping sections
        self.framework_claude_md = """# Claude PM Framework Configuration

## Framework Context
- Version: 015
- Platform: posix
- Core System: Framework orchestration

## A) AGENTS

### Core Agent Types
1. Documentation Agent
2. QA Agent
3. Engineer Agent

## B) TODO AND TASK TOOLS

### TodoWrite Integration
Workflow patterns for task management.

## C) COMMON SECTION
This section appears in all files."""
        
        self.parent_claude_md = """# Claude PM Framework Configuration

## Framework Context
- Version: 015
- Platform: posix
- Core System: Framework orchestration

## A) AGENTS

### Core Agent Types
1. Documentation Agent
2. QA Agent
3. Engineer Agent

## B) TODO AND TASK TOOLS

### TodoWrite Integration
Workflow patterns for task management.

## C) COMMON SECTION
This section appears in all files.

## D) PARENT SPECIFIC
This section only appears in parent."""
        
        self.project_claude_md = """# Claude PM Framework Configuration - Project Override

## Framework Context
- Version: 015
- Platform: posix
- Core System: Framework orchestration
- Project: claude-multiagent-pm

## A) AGENTS

### Core Agent Types
1. Documentation Agent
2. QA Agent
3. Engineer Agent

### Project-Specific Agents
1. Performance Agent
2. Migration Agent

## B) TODO AND TASK TOOLS

### TodoWrite Integration
Workflow patterns for task management with project customizations.

## C) COMMON SECTION
This section appears in all files.

## E) PROJECT SPECIFIC
This section only appears in project."""
    
    def test_parse_markdown_sections(self):
        """Test markdown section parsing."""
        content = """# Header 1
Content 1

## Header 2
Content 2
More content 2

### Header 3
Content 3"""
        
        sections = self.context_manager._parse_markdown_sections(content)
        
        assert len(sections) == 3
        assert sections[0][0] == "# Header 1"
        assert sections[0][1].strip() == "Content 1"
        assert sections[1][0] == "## Header 2"
        assert sections[1][1].strip() == "Content 2\nMore content 2"
        assert sections[2][0] == "### Header 3"
        assert sections[2][1].strip() == "Content 3"
    
    def test_deduplicate_claude_md_content(self):
        """Test CLAUDE.md deduplication logic."""
        claude_md_files = {
            "/Users/masa/Projects/claude-multiagent-pm/framework/CLAUDE.md": self.framework_claude_md,
            "/Users/masa/Projects/CLAUDE.md": self.parent_claude_md,
            "/Users/masa/Projects/claude-multiagent-pm/CLAUDE.md": self.project_claude_md
        }
        
        deduplicated = self.context_manager._deduplicate_claude_md_content(claude_md_files)
        
        # Should have content from all files but deduplicated
        assert len(deduplicated) <= len(claude_md_files)
        
        # Project-specific content should be preserved
        project_content = deduplicated.get("/Users/masa/Projects/claude-multiagent-pm/CLAUDE.md", "")
        assert "PROJECT SPECIFIC" in project_content
        assert "Project-Specific Agents" in project_content
        
        # Parent-specific content should be preserved
        parent_content = deduplicated.get("/Users/masa/Projects/CLAUDE.md", "")
        assert "PARENT SPECIFIC" in parent_content
        
        # Common sections should only appear once across all deduplicated content
        all_content = "\n".join(deduplicated.values())
        # The actual test is that common content was deduplicated - let's check size reduction
        original_total = len(self.framework_claude_md) + len(self.parent_claude_md) + len(self.project_claude_md)
        deduplicated_total = sum(len(content) for content in deduplicated.values())
        assert deduplicated_total < original_total * 0.7  # At least 30% reduction
    
    def test_extract_claude_md_files(self):
        """Test extraction of CLAUDE.md files from context."""
        full_context = {
            "files": {
                "/path/to/CLAUDE.md": "Content 1",
                "/path/to/other.py": "Python code",
                "/another/CLAUDE.md": "Content 2"
            },
            "claude_md_content": {
                "inline": "Inline content"
            },
            "framework_instructions": "Framework content"
        }
        
        extracted = self.context_manager._extract_claude_md_files(full_context)
        
        assert len(extracted) == 4
        assert "/path/to/CLAUDE.md" in extracted
        assert "/another/CLAUDE.md" in extracted
        assert "inline" in extracted
        assert "framework_instructions" in extracted
        assert "/path/to/other.py" not in extracted
    
    def test_filter_context_with_deduplication(self):
        """Test context filtering with CLAUDE.md deduplication."""
        full_context = {
            "files": {
                "/Users/masa/Projects/claude-multiagent-pm/framework/CLAUDE.md": self.framework_claude_md,
                "/Users/masa/Projects/CLAUDE.md": self.parent_claude_md,
                "/Users/masa/Projects/claude-multiagent-pm/CLAUDE.md": self.project_claude_md,
                "/some/other/file.py": "Python code"
            },
            "current_task": "Optimize token usage"
        }
        
        # Filter for orchestrator agent (should get deduplicated CLAUDE.md)
        filtered = self.context_manager.filter_context_for_agent("orchestrator", full_context)
        
        # Should have framework instructions with deduplicated content
        assert "framework_instructions" in filtered
        
        # Original token count
        original_claude_size = len(self.framework_claude_md) + len(self.parent_claude_md) + len(self.project_claude_md)
        
        # Deduplicated should be significantly smaller
        if isinstance(filtered["framework_instructions"], dict):
            deduplicated_size = sum(len(content) for content in filtered["framework_instructions"].values())
        else:
            deduplicated_size = len(str(filtered["framework_instructions"]))
        
        # Should achieve meaningful reduction (at least 30% given the overlap)
        reduction_percent = (original_claude_size - deduplicated_size) / original_claude_size * 100
        assert reduction_percent > 30, f"Expected >30% reduction, got {reduction_percent:.1f}%"
        
        # Verify deduplicated content is still usable
        assert deduplicated_size > 500  # Should still have substantial content
    
    def test_agent_type_filtering(self):
        """Test that CLAUDE.md is only included for relevant agent types."""
        full_context = {
            "files": {
                "/Users/masa/Projects/CLAUDE.md": self.parent_claude_md,
                "/some/code.py": "Python code"
            }
        }
        
        # Orchestrator should get CLAUDE.md
        orchestrator_context = self.context_manager.filter_context_for_agent("orchestrator", full_context)
        assert "framework_instructions" in orchestrator_context
        
        # Engineer should not get CLAUDE.md by default
        engineer_context = self.context_manager.filter_context_for_agent("engineer", full_context)
        assert "framework_instructions" not in engineer_context
        
        # But engineer should still get code files
        assert "files" in engineer_context
        assert "/some/code.py" in engineer_context["files"]
    
    def test_empty_claude_md_handling(self):
        """Test handling of contexts without CLAUDE.md files."""
        full_context = {
            "files": {
                "/some/code.py": "Python code",
                "/another/file.js": "JavaScript code"
            },
            "current_task": "Implement feature"
        }
        
        # Should not crash and should filter normally
        filtered = self.context_manager.filter_context_for_agent("engineer", full_context)
        
        assert "files" in filtered
        assert "framework_instructions" not in filtered
        assert "current_task" in filtered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])