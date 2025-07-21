# Prompt Optimization Implementation Plan for ISS-0168

**Issue**: ISS-0168 - PM Tracking Prompt Optimization  
**Date**: 2025-07-20  
**Version**: 1.0.0

## Executive Summary

Current Claude PM Framework generates excessively large prompts (2,300+ characters for simple tasks) with 73.6% boilerplate content. This plan outlines a comprehensive solution to reduce prompt sizes by 66%, optimize model selection, and significantly reduce API costs while maintaining functionality.

## Current State Analysis

### Prompt Composition Breakdown

Based on code analysis, current prompts consist of:

1. **Base Task Prompt** (~600 chars)
   - Agent nickname and task description
   - Temporal context
   - Agent profile metadata
   - Requirements and deliverables
   - Static escalation text

2. **PM Integration Section** (~800 chars)
   - Delegation ID and coordination text
   - Cross-agent workflow boilerplate
   - Model configuration details
   - Escalation triggers (often duplicated)
   - PM workflow integration instructions

3. **Agent Profile Content** (~900+ chars)
   - Entire agent profile markdown file
   - Often includes unused sections
   - Redundant capability descriptions

### Key Issues Identified

1. **Redundant Content**: Same information appears multiple times
2. **Static Boilerplate**: Large sections unchanged across invocations
3. **Unnecessary Details**: Full agent profiles loaded for simple tasks
4. **Model Overkill**: Opus used for trivial tasks like "Hello World"
5. **No Dynamic Sizing**: Same prompt structure for all task complexities

## Proposed Solution Architecture

### Phase 1: Task Complexity Scoring (Week 1)

#### 1.1 Complexity Scoring Algorithm

```python
class TaskComplexityScorer:
    """Score task complexity on a 0-100 scale."""
    
    def score_task(self, task_description: str, requirements: List[str]) -> int:
        score = 0
        
        # Task verb analysis (0-30 points)
        simple_verbs = ["print", "log", "display", "show", "get", "list"]
        complex_verbs = ["implement", "design", "architect", "optimize", "refactor"]
        
        # Requirement count (0-20 points)
        requirement_score = min(len(requirements) * 5, 20)
        
        # Code scope analysis (0-25 points)
        scope_keywords = {
            "function": 5,
            "class": 10,
            "module": 15,
            "system": 25,
            "architecture": 25
        }
        
        # Integration complexity (0-25 points)
        integration_keywords = {
            "standalone": 0,
            "integrate": 10,
            "cross-agent": 15,
            "multi-system": 25
        }
        
        return score
```

#### 1.2 Complexity Thresholds

- **0-20**: Trivial (Hello World, simple logs)
- **21-40**: Simple (Single function, basic operations)
- **41-60**: Moderate (Feature implementation, bug fixes)
- **61-80**: Complex (System design, major refactoring)
- **81-100**: Expert (Architecture overhaul, critical systems)

### Phase 2: Dynamic Prompt Templates (Week 1)

#### 2.1 Template Structure

```python
class PromptTemplate:
    """Dynamic prompt templates based on complexity."""
    
    MINIMAL = """**{nickname}**: {task}
TASK: {task_description}
RESULT: {expected_result}"""
    
    SIMPLE = """**{nickname}**: {task}
TEMPORAL: {temporal_context}
TASK: {task_description}
REQUIREMENTS:
{requirements}
DELIVERABLES:
{deliverables}"""
    
    STANDARD = """**{nickname}**: {task}
TEMPORAL: {temporal_context}
PROFILE: {agent_role} ({tier})
TASK: {task_description}
REQUIREMENTS:
{requirements}
DELIVERABLES:
{deliverables}
AUTHORITY: {authority}
ESCALATION: {escalation}"""
    
    FULL = """[Current full template with all sections]"""
```

#### 2.2 Template Selection Logic

```python
def select_template(complexity_score: int) -> PromptTemplate:
    if complexity_score <= 20:
        return PromptTemplate.MINIMAL
    elif complexity_score <= 40:
        return PromptTemplate.SIMPLE
    elif complexity_score <= 70:
        return PromptTemplate.STANDARD
    else:
        return PromptTemplate.FULL
```

### Phase 3: Intelligent Model Selection (Week 2)

#### 3.1 Model Selection Matrix

| Complexity | Primary Model | Fallback | Max Tokens |
|------------|---------------|----------|------------|
| 0-20       | Haiku         | Sonnet   | 1024       |
| 21-40      | Sonnet        | Sonnet   | 2048       |
| 41-60      | Sonnet        | Opus     | 4096       |
| 61-80      | Sonnet-4      | Opus     | 8192       |
| 81-100     | Opus-4        | Opus     | 8192       |

#### 3.2 Override Conditions

- **User Override**: Always respect CLI `--model` flag
- **Agent Preference**: Some agents may require specific models
- **Error History**: Upgrade model if previous attempt failed

### Phase 4: Prompt Component Optimization (Week 2)

#### 4.1 Component Filtering

```python
class PromptComponentFilter:
    """Filter prompt components based on task needs."""
    
    def filter_components(self, task_context: Dict) -> Dict:
        components = {}
        
        # Only include PM integration if multi-agent
        if task_context.get('cross_agent_required'):
            components['pm_integration'] = self.get_pm_integration()
        
        # Only include model config if non-default
        if task_context.get('model_override'):
            components['model_config'] = self.get_model_config()
        
        # Minimal agent profile for simple tasks
        if task_context['complexity'] <= 40:
            components['agent_profile'] = self.get_minimal_profile()
        
        return components
```

#### 4.2 Boilerplate Reduction

- **Deduplicate Escalation**: Single escalation section
- **Conditional Sections**: Only include if relevant
- **Compact Formatting**: Remove excessive whitespace
- **Smart Abbreviations**: Use short forms for common phrases

### Phase 5: Caching and Performance (Week 3)

#### 5.1 Enhanced Caching Strategy

```python
class OptimizedPromptCache:
    """Cache computed prompts with complexity awareness."""
    
    def get_cache_key(self, agent: str, task: str, complexity: int) -> str:
        # Include complexity in cache key
        return f"{agent}:{complexity_bracket}:{hash(task)}"
    
    def should_cache(self, complexity: int, prompt_size: int) -> bool:
        # Cache complex prompts more aggressively
        return complexity > 40 or prompt_size > 1000
```

#### 5.2 Performance Metrics

- Track prompt generation time
- Monitor cache hit rates by complexity
- Measure API response times by model

## Implementation Timeline

### Week 1: Core Implementation
- [ ] Day 1-2: Implement TaskComplexityScorer
- [ ] Day 3-4: Create dynamic prompt templates
- [ ] Day 5: Integration with PMOrchestrator

### Week 2: Model Selection & Optimization
- [ ] Day 1-2: Implement intelligent model selector
- [ ] Day 3-4: Build component filtering system
- [ ] Day 5: Testing and refinement

### Week 3: Performance & Monitoring
- [ ] Day 1-2: Enhanced caching implementation
- [ ] Day 3: Metrics and monitoring setup
- [ ] Day 4-5: End-to-end testing and validation

## Success Metrics

### Primary Goals
- **66% reduction** in average prompt size
- **50% reduction** in API costs
- **Zero functionality loss**

### Specific Targets
- Hello World: 2,300 → 300 chars (87% reduction)
- Simple tasks: 3,500 → 800 chars (77% reduction)
- Standard tasks: 5,000 → 2,500 chars (50% reduction)
- Complex tasks: 8,000 → 6,000 chars (25% reduction)

### Quality Metrics
- Task success rate: Maintain 100%
- Response quality: No degradation
- Processing speed: 20% improvement

## Risk Mitigation

### Technical Risks
1. **Under-prompting**: Include fallback to fuller prompts
2. **Model Misselection**: Override mechanism for corrections
3. **Cache Invalidation**: Version-aware cache keys

### Mitigation Strategies
- Gradual rollout with A/B testing
- Comprehensive test suite for all complexity levels
- Rollback mechanism for quick reversion

## Testing Strategy

### Unit Tests
- Complexity scorer accuracy
- Template selection logic
- Component filtering rules

### Integration Tests
- End-to-end prompt generation
- Model selection integration
- Cache performance

### Validation Tests
- Compare outputs before/after optimization
- Measure actual token usage
- Verify cost reductions

## Configuration Schema

```yaml
prompt_optimization:
  enabled: true
  complexity_scoring:
    verb_weight: 0.3
    requirement_weight: 0.2
    scope_weight: 0.25
    integration_weight: 0.25
  
  model_selection:
    complexity_brackets:
      trivial: [0, 20]
      simple: [21, 40]
      moderate: [41, 60]
      complex: [61, 80]
      expert: [81, 100]
    
    model_mapping:
      trivial: "haiku"
      simple: "sonnet"
      moderate: "sonnet"
      complex: "sonnet-4"
      expert: "opus-4"
  
  prompt_templates:
    use_dynamic: true
    min_template_size: 200
    max_template_size: 8000
  
  caching:
    enabled: true
    ttl_by_complexity:
      trivial: 3600    # 1 hour
      simple: 1800     # 30 min
      moderate: 900    # 15 min
      complex: 600     # 10 min
      expert: 300      # 5 min
```

## Code Locations for Implementation

### Primary Files to Modify
1. `claude_pm/services/pm_orchestrator.py` - Main integration point
2. `claude_pm/services/core_agent_loader.py` - Prompt building logic
3. `claude_pm/services/model_selector.py` - Model selection enhancement

### New Files to Create
1. `claude_pm/services/task_complexity_scorer.py` - Complexity analysis
2. `claude_pm/services/prompt_optimizer.py` - Main optimization logic
3. `claude_pm/services/prompt_templates.py` - Dynamic templates

### Test Files
1. `tests/unit/services/test_task_complexity_scorer.py`
2. `tests/unit/services/test_prompt_optimizer.py`
3. `tests/integration/test_optimized_prompts.py`

## Monitoring and Observability

### Metrics to Track
- Prompt size distribution by complexity
- Model usage by task type
- API cost per operation
- Cache hit rates
- Task success rates

### Logging Enhancements
```python
logger.info(f"Prompt optimization: task={task_id}, "
           f"complexity={score}, template={template_type}, "
           f"original_size={original}, reduced_size={optimized}, "
           f"reduction={percent}%, model={selected_model}")
```

## Rollout Plan

### Phase 1: Internal Testing
- Enable for test mode only
- Validate with comprehensive test suite
- Compare results with baseline

### Phase 2: Opt-in Beta
- Add `--optimize-prompts` CLI flag
- Document optimization features
- Gather user feedback

### Phase 3: Default Enablement
- Enable by default with opt-out
- Monitor metrics closely
- Quick rollback if issues

## Expected Impact

### Cost Savings
- **API Costs**: 50-70% reduction
- **Processing Time**: 20-30% improvement
- **Memory Usage**: 40% reduction in cache

### User Experience
- Faster response times
- Same quality outputs
- Transparent optimization

### System Benefits
- Reduced network traffic
- Better cache efficiency
- Improved scalability

## Conclusion

This implementation plan provides a systematic approach to reducing prompt sizes by 66% while maintaining functionality. The phased approach ensures safe rollout with comprehensive testing and monitoring. Expected completion in 3 weeks with significant cost savings and performance improvements.