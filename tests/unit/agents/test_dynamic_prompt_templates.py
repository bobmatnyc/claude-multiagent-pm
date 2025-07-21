#!/usr/bin/env python3
"""
Unit tests for dynamic prompt template functionality.

Tests the new dynamic prompt generation based on task complexity.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from claude_pm.agents.base_agent_loader import (
    prepend_base_instructions,
    PromptTemplate,
    _build_dynamic_prompt,
    _parse_content_sections,
    TEMPLATE_SECTIONS,
    clear_base_agent_cache
)


# Sample base agent content for testing
SAMPLE_BASE_CONTENT = """# Base Agent Instructions

## 🤖 Agent Framework Context

You are operating as a specialized agent within the Claude PM Framework.

### Core Agent Principles

1. Stay Within Your Domain
2. Provide Operational Insights
3. Collaborate Through PM

### Communication Standards

- Be concise and direct
- Use structured formats
- Include timestamps

### Test Response Protocol

When asked to respond with "hello world":
1. Return exactly: `Hello World from [Your Agent Name]!`
2. Exit with status code 0

### Reporting Requirements

- Success Reports: Include accomplishments
- Failure Reports: Include root cause
- Progress Updates: Provide periodic status

### Error Handling

- Catch and handle errors gracefully
- Provide detailed error context
- Escalate critical failures

### Security Awareness

- Never expose sensitive information
- Validate inputs
- Report security concerns

### Temporal Context Integration

You must integrate temporal awareness into operations.

### Quality Standards

#### Code Quality
- Follow project standards
- Maintain test coverage

### Tool Usage Guidelines

#### File Operations
- Always use absolute paths
- Verify parent directories

### Collaboration Protocols

#### PM Orchestrator Integration
- Accept tasks with acknowledgment
- Report completion status

### Performance Optimization

#### Resource Management
- Monitor resource usage
- Optimize for efficiency

### Escalation Triggers

Immediately escalate when:
- Task requirements exceed authority
- Critical errors block completion

### Output Formatting Standards

#### Structured Data
```yaml
status: success|failure
summary: "Brief description"
```

### Framework Integration

#### Agent Metadata Requirements
- Include agent version
- Report capability limitations

### Universal Constraints

ALL agents MUST NOT:
- Exceed authority boundaries
- Hide error information

### Success Criteria

Your task is successful when:
1. All operations complete
2. Quality standards met
"""


class TestDynamicPromptTemplates:
    """Test suite for dynamic prompt templates."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any cached content
        clear_base_agent_cache()
    
    def test_parse_content_sections(self):
        """Test parsing content into sections."""
        sections = _parse_content_sections(SAMPLE_BASE_CONTENT)
        
        # Verify expected sections are parsed
        assert "Core Agent Principles" in sections
        assert "Communication Standards" in sections
        assert "Test Response Protocol" in sections
        assert "Escalation Triggers" in sections
        
        # Verify section content
        assert "Stay Within Your Domain" in sections["Core Agent Principles"]
        assert "Be concise and direct" in sections["Communication Standards"]
    
    def test_minimal_template(self):
        """Test MINIMAL template includes only core sections."""
        result = _build_dynamic_prompt(SAMPLE_BASE_CONTENT, PromptTemplate.MINIMAL)
        
        # Should include core sections
        assert "Core Agent Principles" in result
        assert "Communication Standards" in result
        assert "Universal Constraints" in result
        
        # Should NOT include advanced sections
        assert "Escalation Triggers" not in result
        assert "Security Awareness" not in result
        assert "Performance Optimization" not in result
        assert "Quality Standards" not in result
        
        # Verify size is minimal
        assert len(result) < 1000  # Should be under 1000 chars
    
    def test_standard_template(self):
        """Test STANDARD template includes medium sections."""
        result = _build_dynamic_prompt(SAMPLE_BASE_CONTENT, PromptTemplate.STANDARD)
        
        # Should include core + standard sections
        assert "Core Agent Principles" in result
        assert "Communication Standards" in result
        assert "Reporting Requirements" in result
        assert "Error Handling" in result
        assert "Collaboration Protocols" in result
        
        # Should NOT include full sections (moved from STANDARD to FULL)
        assert "Test Response Protocol" not in result  # Moved to FULL
        assert "Tool Usage Guidelines" not in result  # Moved to FULL
        assert "Escalation Triggers" not in result
        assert "Security Awareness" not in result
        assert "Performance Optimization" not in result
        assert "Temporal Context Integration" not in result  # Moved to FULL
        
        # Verify size is reduced
        assert 800 < len(result) < 1600
    
    def test_full_template(self):
        """Test FULL template includes all sections."""
        result = _build_dynamic_prompt(SAMPLE_BASE_CONTENT, PromptTemplate.FULL)
        
        # Should return the full content unchanged
        assert result == SAMPLE_BASE_CONTENT
    
    def test_complexity_score_template_selection(self):
        """Test automatic template selection based on complexity score."""
        # Mock load_base_agent_instructions to return sample content
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = SAMPLE_BASE_CONTENT
            
            # Test low complexity -> MINIMAL
            result_low = prepend_base_instructions("Agent prompt", complexity_score=20)
            assert "Escalation Triggers" not in result_low
            assert "Core Agent Principles" in result_low
            assert "Test Response Protocol" not in result_low
            
            # Test medium complexity -> STANDARD  
            result_med = prepend_base_instructions("Agent prompt", complexity_score=50)
            assert "Reporting Requirements" in result_med
            assert "Collaboration Protocols" in result_med
            assert "Test Response Protocol" not in result_med  # Now in FULL only
            assert "Escalation Triggers" not in result_med
            
            # Test high complexity -> FULL
            result_high = prepend_base_instructions("Agent prompt", complexity_score=85)
            assert "Escalation Triggers" in result_high
            assert "Performance Optimization" in result_high
            assert "Test Response Protocol" in result_high
    
    def test_test_mode_forces_full_template(self):
        """Test that test mode always uses FULL template."""
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = SAMPLE_BASE_CONTENT
            
            # Set test mode
            with patch.dict('os.environ', {'CLAUDE_PM_TEST_MODE': 'true'}):
                # Even with low complexity, should use FULL template
                result = prepend_base_instructions("Agent prompt", complexity_score=10)
                assert "Escalation Triggers" in result
                assert "Performance Optimization" in result
    
    def test_template_enum_values(self):
        """Test PromptTemplate enum values."""
        assert PromptTemplate.MINIMAL.value == "MINIMAL"
        assert PromptTemplate.STANDARD.value == "STANDARD"
        assert PromptTemplate.FULL.value == "FULL"
    
    def test_template_sections_configuration(self):
        """Test template sections are properly configured."""
        # Verify all sections have required fields
        for section_key, config in TEMPLATE_SECTIONS.items():
            assert "templates" in config
            assert "content" in config
            assert isinstance(config["templates"], list)
            assert all(t in ["MINIMAL", "STANDARD", "FULL"] for t in config["templates"])
        
        # Verify section hierarchy
        minimal_sections = [k for k, v in TEMPLATE_SECTIONS.items() if "MINIMAL" in v["templates"]]
        standard_sections = [k for k, v in TEMPLATE_SECTIONS.items() if "STANDARD" in v["templates"]]
        full_sections = [k for k, v in TEMPLATE_SECTIONS.items() if "FULL" in v["templates"]]
        
        # MINIMAL should be subset of STANDARD
        assert all(s in standard_sections for s in minimal_sections)
        # STANDARD should be subset of FULL
        assert all(s in full_sections for s in standard_sections)
    
    def test_caching_per_template(self):
        """Test that different templates are cached separately."""
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = SAMPLE_BASE_CONTENT
            
            # Create cache mock
            cache_mock = MagicMock()
            with patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance') as mock_cache:
                mock_cache.return_value = cache_mock
                cache_mock.get.return_value = None  # Force cache miss
                
                # Request different templates
                prepend_base_instructions("prompt", template=PromptTemplate.MINIMAL)
                prepend_base_instructions("prompt", template=PromptTemplate.STANDARD)
                prepend_base_instructions("prompt", template=PromptTemplate.FULL)
                
                # Verify different cache keys were used
                cache_calls = cache_mock.set.call_args_list
                assert len(cache_calls) == 3
                
                # Extract cache keys
                cache_keys = [call[0][0] for call in cache_calls]
                assert any("MINIMAL" in key for key in cache_keys)
                assert any("STANDARD" in key for key in cache_keys)
                assert any("FULL" in key for key in cache_keys)
    
    def test_size_reduction_metrics(self):
        """Test and document size reduction achievements."""
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = SAMPLE_BASE_CONTENT
            
            # Get prompts for each template
            minimal = _build_dynamic_prompt(SAMPLE_BASE_CONTENT, PromptTemplate.MINIMAL)
            standard = _build_dynamic_prompt(SAMPLE_BASE_CONTENT, PromptTemplate.STANDARD)
            full = _build_dynamic_prompt(SAMPLE_BASE_CONTENT, PromptTemplate.FULL)
            
            # Calculate reductions
            minimal_reduction = (1 - len(minimal) / len(full)) * 100
            standard_reduction = (1 - len(standard) / len(full)) * 100
            
            print(f"\nSize Reduction Metrics:")
            print(f"FULL template: {len(full)} chars")
            print(f"STANDARD template: {len(standard)} chars ({standard_reduction:.1f}% reduction)")
            print(f"MINIMAL template: {len(minimal)} chars ({minimal_reduction:.1f}% reduction)")
            
            # Verify we achieve significant reduction
            assert minimal_reduction > 60  # Should achieve >60% reduction for simple tasks
            assert standard_reduction > 30  # Should achieve >30% reduction for medium tasks with new config
            
            # Document achieved reductions
            assert 65 <= minimal_reduction <= 75  # Actual: ~70.6%
            assert 45 <= standard_reduction <= 55  # Actual: ~50.3% with optimized sections