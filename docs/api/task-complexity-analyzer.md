# Task Complexity Analyzer API Reference

## Overview

The `TaskComplexityAnalyzer` is a core component of the prompt optimization system that analyzes task descriptions and context to determine complexity levels and provide optimization recommendations.

## Import

```python
from claude_pm.services.task_complexity_analyzer import (
    TaskComplexityAnalyzer,
    ComplexityLevel,
    ModelType,
    ComplexityAnalysisResult,
    TaskComplexityFactors
)
```

## Classes

### TaskComplexityAnalyzer

Main analyzer class that performs task complexity analysis.

#### Constructor

```python
analyzer = TaskComplexityAnalyzer()
```

No parameters required. The analyzer initializes with default configuration.

#### Methods

##### analyze_task()

Analyzes task complexity and provides recommendations.

```python
def analyze_task(
    self,
    task_description: str,
    context_size: int = 0,
    file_count: int = 0,
    integration_points: int = 0,
    requires_research: bool = False,
    requires_testing: bool = False,
    requires_documentation: bool = False,
    technical_depth: Optional[str] = None
) -> ComplexityAnalysisResult
```

**Parameters:**

- `task_description` (str, required): Description of the task to analyze
- `context_size` (int, optional): Size of context in characters. Default: 0
- `file_count` (int, optional): Number of files involved. Default: 0
- `integration_points` (int, optional): Number of system integration points. Default: 0
- `requires_research` (bool, optional): Whether task requires research. Default: False
- `requires_testing` (bool, optional): Whether task requires testing. Default: False
- `requires_documentation` (bool, optional): Whether task requires documentation. Default: False
- `technical_depth` (str, optional): Technical depth assessment. Values: "shallow", "moderate", "deep". Default: None

**Returns:**

`ComplexityAnalysisResult` object containing analysis results

**Example:**

```python
analyzer = TaskComplexityAnalyzer()
result = analyzer.analyze_task(
    task_description="Refactor the authentication module to use JWT tokens",
    file_count=5,
    integration_points=2,
    requires_testing=True,
    technical_depth="deep"
)

print(f"Complexity Score: {result.complexity_score}")
print(f"Complexity Level: {result.complexity_level.value}")
print(f"Recommended Model: {result.recommended_model.value}")
```

##### get_prompt_optimization_hints()

Get optimization hints based on analysis results.

```python
def get_prompt_optimization_hints(
    self,
    analysis_result: ComplexityAnalysisResult
) -> Dict[str, any]
```

**Parameters:**

- `analysis_result` (ComplexityAnalysisResult): Result from task analysis

**Returns:**

Dictionary containing optimization hints:
- `model`: Recommended model name
- `prompt_size_range`: Tuple of (min, max) characters
- `focus_areas`: List of areas to focus on
- `optimization_strategies`: List of optimization strategies

**Example:**

```python
result = analyzer.analyze_task(task_description="Complex refactoring task")
hints = analyzer.get_prompt_optimization_hints(result)

print(f"Recommended Model: {hints['model']}")
print(f"Prompt Size Range: {hints['prompt_size_range']}")
print(f"Focus Areas: {hints['focus_areas']}")
print(f"Strategies: {hints['optimization_strategies']}")
```

### Enums

#### ComplexityLevel

Task complexity levels.

```python
class ComplexityLevel(Enum):
    SIMPLE = "SIMPLE"    # Score: 0-30
    MEDIUM = "MEDIUM"    # Score: 31-70
    COMPLEX = "COMPLEX"  # Score: 71-100
```

#### ModelType

Available model types for task execution.

```python
class ModelType(Enum):
    HAIKU = "haiku"    # Fast, efficient for simple tasks
    SONNET = "sonnet"  # Balanced for medium tasks
    OPUS = "opus"      # Maximum capability for complex tasks
```

### Data Classes

#### ComplexityAnalysisResult

Result of task complexity analysis.

```python
@dataclass
class ComplexityAnalysisResult:
    complexity_score: int                    # Normalized score (0-100)
    complexity_level: ComplexityLevel        # SIMPLE, MEDIUM, or COMPLEX
    recommended_model: ModelType             # Recommended model type
    optimal_prompt_size: Tuple[int, int]     # (min, max) characters
    scoring_breakdown: Dict[str, int]        # Individual score components
    analysis_details: Dict[str, any]         # Detailed analysis information
```

**Fields:**

- `complexity_score`: Overall complexity score from 0-100
- `complexity_level`: Categorized complexity level
- `recommended_model`: Suggested model based on complexity
- `optimal_prompt_size`: Recommended prompt size range
- `scoring_breakdown`: Breakdown of scoring components
- `analysis_details`: Additional analysis details

#### TaskComplexityFactors

Input factors for complexity analysis.

```python
@dataclass
class TaskComplexityFactors:
    task_description: str
    context_size: int = 0
    file_count: int = 0
    integration_points: int = 0
    requires_research: bool = False
    requires_testing: bool = False
    requires_documentation: bool = False
    technical_depth: Optional[str] = None
```

## Configuration

### Verb Complexity Mappings

The analyzer categorizes verbs into three complexity levels:

```python
SIMPLE_VERBS = {
    "read", "list", "get", "fetch", "show", "display", "view",
    "check", "verify", "find", "search", "look"
}

MEDIUM_VERBS = {
    "create", "update", "modify", "add", "remove", "delete",
    "implement", "fix", "debug", "test", "validate", "integrate"
}

COMPLEX_VERBS = {
    "refactor", "architect", "design", "optimize", "analyze",
    "migrate", "transform", "orchestrate", "coordinate", "restructure"
}
```

### Complexity Thresholds

```python
COMPLEXITY_THRESHOLDS = {
    ComplexityLevel.SIMPLE: (0, 30),
    ComplexityLevel.MEDIUM: (31, 70),
    ComplexityLevel.COMPLEX: (71, 100)
}
```

### Model Recommendations

```python
PROMPT_SIZE_RECOMMENDATIONS = {
    ModelType.HAIKU: (300, 500),      # Concise prompts
    ModelType.SONNET: (700, 1000),    # Balanced prompts
    ModelType.OPUS: (1200, 1500)      # Comprehensive prompts
}
```

## Scoring Algorithm

### Score Components

1. **Description Complexity** (0-25 points)
   - Verb complexity: 0-10 points
   - Length complexity: 0-5 points
   - Technical keywords: 0-5 points
   - Multi-step indicators: 0-5 points

2. **File Complexity** (0-20 points)
   - 0-2 files: 0 points
   - 3-5 files: 10 points
   - 6+ files: 10 + 2 points per additional file (max 20)

3. **Context Complexity** (0-15 points)
   - <1KB: 0 points
   - 1-5KB: 5 points
   - 5-10KB: 10 points
   - >10KB: 15 points

4. **Integration Complexity** (0-15 points)
   - 5 points per integration point (max 15)

5. **Additional Requirements** (0-15 points)
   - Research required: 5 points
   - Testing required: 5 points
   - Documentation required: 5 points

6. **Technical Depth** (0-10 points)
   - None/shallow: 0-2 points
   - Moderate: 5 points
   - Deep: 10 points

## Usage Examples

### Basic Usage

```python
from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer

analyzer = TaskComplexityAnalyzer()

# Simple task
simple_result = analyzer.analyze_task(
    task_description="List all Python files in the project"
)
print(f"Simple task score: {simple_result.complexity_score}")  # ~10-15

# Medium task
medium_result = analyzer.analyze_task(
    task_description="Implement user authentication with email verification",
    file_count=4,
    requires_testing=True
)
print(f"Medium task score: {medium_result.complexity_score}")  # ~40-50

# Complex task
complex_result = analyzer.analyze_task(
    task_description="Refactor the entire database layer to use async operations",
    file_count=15,
    integration_points=3,
    requires_testing=True,
    requires_documentation=True,
    technical_depth="deep"
)
print(f"Complex task score: {complex_result.complexity_score}")  # ~80-90
```

### Integration with Agent Loader

```python
from claude_pm.agents.agent_loader import get_agent_prompt_with_model_info
from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer

# The agent loader uses TaskComplexityAnalyzer internally
prompt, model, config = get_agent_prompt_with_model_info(
    'engineer',
    task_description='Optimize database queries for better performance',
    file_count=8,
    technical_depth='deep'
)

# Access complexity analysis from config
print(f"Complexity Level: {config['complexity_level']}")
print(f"Complexity Score: {config['complexity_score']}")
print(f"Score Breakdown: {config['scoring_breakdown']}")
```

### Custom Analysis

```python
# Analyze without using agent loader
analyzer = TaskComplexityAnalyzer()

# Detailed analysis
result = analyzer.analyze_task(
    task_description="Migrate from REST API to GraphQL",
    context_size=15000,  # Large context
    file_count=20,       # Many files
    integration_points=5, # Multiple integrations
    requires_research=True,
    requires_testing=True,
    requires_documentation=True,
    technical_depth="deep"
)

# Get comprehensive results
print(f"Score: {result.complexity_score}")
print(f"Level: {result.complexity_level.value}")
print(f"Model: {result.recommended_model.value}")
print(f"Prompt Size: {result.optimal_prompt_size}")

# Detailed breakdown
print("\nScoring Breakdown:")
for component, score in result.scoring_breakdown.items():
    print(f"  {component}: {score} points")

# Analysis details
print("\nAnalysis Details:")
print(f"  Verb Complexity: {result.analysis_details['verb_complexity']}")
print(f"  Technical Indicators: {result.analysis_details['technical_indicators']}")
print(f"  Estimated Steps: {result.analysis_details['estimated_steps']}")
```

### Getting Optimization Hints

```python
# Get actionable optimization hints
hints = analyzer.get_prompt_optimization_hints(result)

print("Optimization Recommendations:")
print(f"  Use Model: {hints['model']}")
print(f"  Prompt Size: {hints['prompt_size_range'][0]}-{hints['prompt_size_range'][1]} chars")
print(f"  Focus On: {', '.join(hints['focus_areas'])}")
print(f"  Strategies: {', '.join(hints['optimization_strategies'])}")
```

## Error Handling

The analyzer includes graceful error handling:

```python
try:
    result = analyzer.analyze_task(
        task_description="",  # Empty description
        file_count=-1        # Invalid count
    )
except Exception as e:
    # Analyzer returns default medium complexity on errors
    print(f"Analysis failed: {e}")
    # Result will have:
    # - complexity_score: 50
    # - complexity_level: MEDIUM
    # - recommended_model: SONNET
```

## Performance Considerations

- **Analysis Speed**: <0.007ms average per analysis
- **Memory Usage**: Minimal, no persistent storage
- **Thread Safety**: Analyzer is stateless and thread-safe
- **Caching**: Results should be cached by calling code if needed

## Best Practices

1. **Provide Complete Context**: Include all relevant parameters for accurate analysis
2. **Cache Results**: Cache analysis results for repeated tasks
3. **Validate Inputs**: Ensure task_description is meaningful
4. **Use Hints**: Apply optimization hints for best results
5. **Monitor Metrics**: Track complexity distribution over time

## Related APIs

- [`agent_loader`](./agent-loader.md) - Integrates complexity analysis with agent prompt loading
- [`TaskToolHelper`](./task-tool-helper.md) - Uses complexity analysis for subprocess creation
- [`SharedPromptCache`](./shared-prompt-cache.md) - Caches analysis results with prompts

---

**API Version**: 1.0.0  
**Module**: `claude_pm.services.task_complexity_analyzer`  
**Since**: v1.3.0