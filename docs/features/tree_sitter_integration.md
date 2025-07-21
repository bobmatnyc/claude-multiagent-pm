# Tree-sitter Integration

Tree-sitter is now integrated as a core dependency of the Claude PM Framework, providing fast and reliable code analysis capabilities for the Research Agent and other components.

## Overview

Tree-sitter is a parser generator tool and an incremental parsing library that provides:
- Fast, incremental parsing of source code
- Consistent AST structure across different languages
- Error recovery for incomplete or invalid code
- Language-agnostic query system

## Supported Languages

The framework includes support for:
- **Python** (`.py`)
- **JavaScript** (`.js`, `.jsx`)
- **TypeScript** (`.ts`, `.tsx`)

## Installation

Tree-sitter is automatically installed as a core dependency when you install the Claude PM Framework:

```bash
# Via npm
npm install -g @bobmatnyc/claude-multiagent-pm

# Via pip
pip install claude-multiagent-pm
```

## Usage

### Basic Usage

```python
from claude_pm.utils.tree_sitter_utils import TreeSitterAnalyzer

# Initialize the analyzer
analyzer = TreeSitterAnalyzer()

# Parse code from a string
tree = analyzer.parse_code("def hello(): pass", "python")

# Find functions in the parsed tree
functions = analyzer.find_functions(tree, "python")
```

### Analyzing Files

```python
from claude_pm.utils.tree_sitter_utils import analyze_file, analyze_directory

# Analyze a single file
result = analyze_file("path/to/module.py")
print(f"Found {len(result['functions'])} functions")
print(f"Found {len(result['classes'])} classes")

# Analyze an entire directory
results = analyze_directory("./src", extensions=['.py', '.js', '.ts'])
for file_result in results:
    print(f"{file_result['file']}: {len(file_result['functions'])} functions")
```

### Research Agent Integration

The Research Agent uses tree-sitter for semantic code analysis:

```python
# Example from Research Agent
analyzer = TreeSitterAnalyzer()

# Analyze project structure
for file_path in project_files:
    tree = analyzer.parse_file(file_path)
    functions = analyzer.find_functions(tree, language)
    
    # Generate insights about code organization
    # Identify patterns and anti-patterns
    # Analyze dependencies and imports
```

## API Reference

### TreeSitterAnalyzer

The main class for code analysis:

- `parse_file(file_path)` - Parse a file and return the syntax tree
- `parse_code(code, language)` - Parse code string and return the syntax tree
- `find_functions(tree, language)` - Find all function definitions
- `find_classes(tree, language)` - Find all class definitions
- `get_imports(tree, language)` - Extract import statements

### Convenience Functions

- `analyze_file(file_path)` - Analyze a single file and return structured data
- `analyze_directory(directory, extensions)` - Analyze all matching files in a directory

## Performance Considerations

Tree-sitter is designed for performance:
- Incremental parsing allows for fast updates when code changes
- Memory-efficient parsing suitable for large codebases
- Parallel processing support for directory analysis

## Future Enhancements

Planned improvements include:
- Support for additional languages (Go, Rust, Java, C++)
- Advanced query patterns for complex code analysis
- Integration with code generation and refactoring tools
- Real-time code analysis during development