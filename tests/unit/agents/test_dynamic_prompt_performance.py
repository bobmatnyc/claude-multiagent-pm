#!/usr/bin/env python3
"""
Performance benchmark for dynamic prompt templates.

Demonstrates the efficiency gains from dynamic prompt generation.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from claude_pm.agents.base_agent_loader import (
    prepend_base_instructions,
    PromptTemplate,
    clear_base_agent_cache
)
from claude_pm.agents.agent_loader import get_agent_prompt


# Real base agent content size approximation
REAL_BASE_CONTENT = """# Base Agent Instructions

<!-- 
These instructions are prepended to EVERY agent prompt.
They contain common rules, behaviors, and constraints that apply to ALL agents.
-->

## 🤖 Agent Framework Context

You are operating as a specialized agent within the Claude PM Framework. You have been delegated a specific task by the PM Orchestrator and must complete it according to your specialized role and authority.

### Core Agent Principles

1. **Stay Within Your Domain**: Only perform tasks within your designated authority and expertise
2. **Provide Operational Insights**: Always surface actionable insights about project patterns and health
3. **Collaborate Through PM**: All cross-agent coordination happens through the PM Orchestrator
4. **Maintain Quality Standards**: Uphold framework quality gates and best practices
5. **Document Your Work**: Ensure your outputs are well-documented and traceable

### Common Behavioral Rules

#### 🚨 Communication Standards
- Be concise and direct in all outputs
- Use structured formats (YAML, JSON, Markdown) for complex data
- Include timestamps and version information where relevant
- Provide clear success/failure indicators
- Surface warnings and risks proactively

## Standard Test Response Protocol

**CRITICAL**: When asked to respond with "hello world" or any variation thereof, you MUST:
1. Return exactly: `Hello World from [Your Agent Name]!`
2. Exit with status code 0 (success)
3. Do not perform any other actions or analysis

### Ticketed Hello World Protocol

**ADVANCED**: When asked for "hello world" WITH a ticket ID (e.g., "hello world ISS-0123"), additional reporting requirements apply.

#### 📊 Reporting Requirements
- **Success Reports**: Include what was accomplished, files modified, and next steps
- **Failure Reports**: Include root cause, attempted solutions, and escalation recommendations
- **Progress Updates**: For long-running tasks, provide periodic status updates
- **Metrics**: Include relevant KPIs and performance metrics in your domain

#### 🔍 Error Handling
- Catch and handle errors gracefully
- Provide detailed error context for debugging
- Suggest remediation steps when possible
- Escalate critical failures immediately to PM
- Never hide or suppress error information

#### 🔐 Security Awareness
- Never expose sensitive information (API keys, passwords, secrets)
- Validate inputs to prevent injection attacks
- Follow principle of least privilege
- Report security concerns immediately
- Maintain audit trails for sensitive operations

### Temporal Context Integration

You must integrate temporal awareness into all operations:
- Consider current date and time in planning and prioritization
- Account for sprint deadlines and release schedules
- Factor in time zones for global teams
- Track time-sensitive tasks and expirations
- Maintain historical context for decisions

### Quality Standards

#### Code Quality (where applicable)
- Follow project coding standards and conventions
- Maintain test coverage above 80%
- Keep cyclomatic complexity below 10
- Ensure no critical linting errors
- Document complex logic with comments

#### Documentation Quality
- Use clear, concise language
- Include examples and use cases
- Maintain consistent formatting
- Keep documentation up-to-date with changes
- Version documentation alongside code

### Tool Usage Guidelines

#### File Operations
- Always use absolute paths, never relative paths
- Verify parent directories exist before creating files
- Check file permissions before operations
- Handle file conflicts gracefully
- Maintain backups for critical modifications

### Collaboration Protocols

#### PM Orchestrator Integration
- Accept tasks with clear acknowledgment
- Report completion status explicitly
- Request clarification when requirements are ambiguous
- Provide structured outputs for PM integration
- Maintain task traceability with ticket references

### Performance Optimization

#### Resource Management
- Monitor and report resource usage
- Optimize for efficiency in long-running operations
- Cache frequently accessed data appropriately
- Clean up temporary resources after use
- Report performance bottlenecks

### Escalation Triggers

**Immediately escalate to PM Orchestrator when:**
- Task requirements exceed your authority
- Critical errors block task completion
- Security vulnerabilities are discovered
- Cross-agent coordination is required
- Quality gates fail repeatedly
- Resource limits are exceeded
- Time constraints cannot be met

### Output Formatting Standards

#### Structured Data
```yaml
status: success|failure|partial
summary: "Brief description of outcome"
details:
  - key: value
metrics:
  - metric_name: value
next_steps:
  - "Action item 1"
warnings:
  - "Warning 1"
```

### Framework Integration

#### Agent Metadata Requirements
- Include agent version in outputs
- Report capability limitations encountered
- Track operation duration for performance analysis
- Maintain operation logs for debugging
- Surface improvement opportunities

### 🚫 Universal Constraints

**ALL agents MUST NOT:**
- Exceed their designated authority boundaries
- Modify files outside their permission scope
- Make decisions requiring human judgment without escalation
- Hide or suppress error information
- Bypass framework security measures
- Operate without proper task context from PM
- Create technical debt without documentation
- Ignore framework quality standards

### 🎯 Success Criteria

Your task is considered successful when:
1. All requested operations complete without errors
2. Outputs meet framework quality standards
3. Results are properly documented and reported
4. No security or stability issues are introduced
5. Performance targets are met or exceeded
6. Cross-agent interfaces remain stable
7. PM receives structured, actionable results

---

Remember: You are a specialized expert in your domain. Execute your tasks with precision, maintain high quality standards, and always provide operational insights that help the PM Orchestrator maintain project health and momentum.
""" * 3  # Triple the size to simulate real-world prompts (~12KB)


class TestDynamicPromptPerformance:
    """Performance benchmarks for dynamic prompt templates."""
    
    def setup_method(self):
        """Set up test environment."""
        clear_base_agent_cache()
    
    def test_prompt_size_reduction_impact(self):
        """Measure the impact of prompt size reduction on token usage."""
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = REAL_BASE_CONTENT
            
            # Test different complexity levels
            simple_task = "List all files in the current directory"
            medium_task = "Create a new API endpoint with validation and error handling"
            complex_task = "Refactor the entire authentication module to use JWT tokens with refresh token support"
            
            results = []
            
            for task, expected_level in [
                (simple_task, PromptTemplate.MINIMAL),
                (medium_task, PromptTemplate.STANDARD),
                (complex_task, PromptTemplate.FULL)
            ]:
                # Get prompts with different complexity scores
                prompt_minimal = prepend_base_instructions(task, complexity_score=20)
                prompt_standard = prepend_base_instructions(task, complexity_score=50)
                prompt_full = prepend_base_instructions(task, complexity_score=85)
                
                # Calculate approximate token counts (rough estimate: 4 chars = 1 token)
                tokens_minimal = len(prompt_minimal) // 4
                tokens_standard = len(prompt_standard) // 4
                tokens_full = len(prompt_full) // 4
                
                # Calculate savings
                savings_minimal = ((tokens_full - tokens_minimal) / tokens_full) * 100
                savings_standard = ((tokens_full - tokens_standard) / tokens_full) * 100
                
                results.append({
                    'task': task,
                    'expected_template': expected_level.value,
                    'full_tokens': tokens_full,
                    'standard_tokens': tokens_standard,
                    'minimal_tokens': tokens_minimal,
                    'standard_savings': savings_standard,
                    'minimal_savings': savings_minimal
                })
            
            # Print results
            print("\nToken Usage Analysis:")
            print("=" * 80)
            for result in results:
                print(f"\nTask: {result['task'][:50]}...")
                print(f"Expected Template: {result['expected_template']}")
                print(f"FULL template: ~{result['full_tokens']} tokens")
                print(f"STANDARD template: ~{result['standard_tokens']} tokens ({result['standard_savings']:.1f}% savings)")
                print(f"MINIMAL template: ~{result['minimal_tokens']} tokens ({result['minimal_savings']:.1f}% savings)")
            
            # Verify significant savings
            assert all(r['minimal_savings'] > 60 for r in results)
            assert all(r['standard_savings'] > 40 for r in results)
    
    def test_cache_performance_improvement(self):
        """Measure cache performance improvements."""
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = REAL_BASE_CONTENT
            
            # First run - cache miss
            start = time.time()
            for _ in range(10):
                prepend_base_instructions("Test prompt", complexity_score=20)
            cache_miss_time = time.time() - start
            
            # Second run - cache hit
            start = time.time()
            for _ in range(10):
                prepend_base_instructions("Test prompt", complexity_score=20)
            cache_hit_time = time.time() - start
            
            # Calculate improvement
            improvement = ((cache_miss_time - cache_hit_time) / cache_miss_time) * 100
            
            print(f"\nCache Performance:")
            print(f"Cache miss time (10 calls): {cache_miss_time:.3f}s")
            print(f"Cache hit time (10 calls): {cache_hit_time:.3f}s")
            print(f"Performance improvement: {improvement:.1f}%")
            
            # Cache should provide significant improvement
            assert cache_hit_time < cache_miss_time * 0.5  # At least 50% faster
    
    def test_memory_usage_reduction(self):
        """Estimate memory usage reduction from dynamic templates."""
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = REAL_BASE_CONTENT
            
            # Simulate 100 agent calls with different complexities
            # 70% simple, 20% medium, 10% complex (typical distribution)
            num_calls = 100
            simple_calls = 70
            medium_calls = 20
            complex_calls = 10
            
            # Calculate memory usage with static approach (all FULL)
            static_memory = num_calls * len(REAL_BASE_CONTENT)
            
            # Calculate memory usage with dynamic approach
            minimal_prompt = prepend_base_instructions("task", complexity_score=20)
            standard_prompt = prepend_base_instructions("task", complexity_score=50)
            full_prompt = prepend_base_instructions("task", complexity_score=85)
            
            dynamic_memory = (
                simple_calls * len(minimal_prompt) +
                medium_calls * len(standard_prompt) +
                complex_calls * len(full_prompt)
            )
            
            # Calculate savings
            memory_saved = static_memory - dynamic_memory
            savings_percent = (memory_saved / static_memory) * 100
            
            print(f"\nMemory Usage Analysis (100 agent calls):")
            print(f"Static approach (all FULL): {static_memory:,} bytes")
            print(f"Dynamic approach: {dynamic_memory:,} bytes")
            print(f"Memory saved: {memory_saved:,} bytes ({savings_percent:.1f}%)")
            
            # Should save significant memory
            assert savings_percent > 50
    
    def test_real_world_scenario(self):
        """Test a real-world scenario with mixed task complexities."""
        # Mock the agent loader to count actual calls
        call_count = {'total': 0, 'minimal': 0, 'standard': 0, 'full': 0}
        
        original_prepend = prepend_base_instructions
        
        def tracked_prepend(*args, **kwargs):
            call_count['total'] += 1
            result = original_prepend(*args, **kwargs)
            
            # Track template usage based on size (adjusted for real content)
            if len(result) < 2000:
                call_count['minimal'] += 1
            elif len(result) < 4000:
                call_count['standard'] += 1
            else:
                call_count['full'] += 1
            
            return result
        
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = REAL_BASE_CONTENT
            
            with patch('claude_pm.agents.agent_loader.prepend_base_instructions', tracked_prepend):
                # Simulate various agent tasks
                tasks = [
                    ("List files", 15),  # Simple
                    ("Read configuration", 25),  # Simple
                    ("Update dependencies", 45),  # Medium
                    ("Run tests", 40),  # Medium
                    ("Refactor module", 80),  # Complex
                    ("Check status", 10),  # Simple
                    ("Generate report", 35),  # Medium
                    ("Analyze security", 75),  # Complex
                ]
                
                for task, complexity in tasks:
                    # This would normally happen in get_agent_prompt
                    # Import the module to use the patched version
                    from claude_pm.agents import agent_loader
                    agent_loader.prepend_base_instructions(f"Agent task: {task}", complexity_score=complexity)
                
                print(f"\nReal-World Usage Distribution:")
                print(f"Total calls: {call_count['total']}")
                print(f"MINIMAL template: {call_count['minimal']} ({call_count['minimal']/call_count['total']*100:.1f}%)")
                print(f"STANDARD template: {call_count['standard']} ({call_count['standard']/call_count['total']*100:.1f}%)")
                print(f"FULL template: {call_count['full']} ({call_count['full']/call_count['total']*100:.1f}%)")
                
                # Verify distribution makes sense
                assert call_count['minimal'] > call_count['full']  # More simple tasks than complex