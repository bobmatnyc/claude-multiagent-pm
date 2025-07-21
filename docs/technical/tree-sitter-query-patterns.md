# Tree-sitter Query Patterns for Agent Discovery

## Overview

The Claude PM Framework uses Tree-sitter for high-performance, multi-language code analysis in agent discovery and modification tracking. This document provides comprehensive guidance on Tree-sitter query patterns, language-specific examples, and best practices for extending language support.

## Table of Contents

- [Introduction](#introduction)
- [Query Syntax Basics](#query-syntax-basics)
- [Language-Specific Patterns](#language-specific-patterns)
  - [Python](#python)
  - [JavaScript/TypeScript](#javascripttypescript)
  - [Markdown](#markdown)
  - [Generic Language Patterns](#generic-language-patterns)
- [Extending Language Support](#extending-language-support)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Query Pattern Reference](#query-pattern-reference)

## Introduction

Tree-sitter is a parser generator tool and incremental parsing library that builds concrete syntax trees for source files and efficiently updates them as the source changes. The Claude PM Framework leverages Tree-sitter to:

- Analyze code structure across 40+ programming languages
- Extract semantic information (classes, functions, imports, etc.)
- Provide 36x performance improvement over traditional AST-based approaches
- Enable incremental parsing for real-time agent modification tracking

### Key Benefits

1. **Multi-language Support**: Single interface for 40+ languages
2. **Performance**: Incremental parsing with O(log n) complexity
3. **Error Recovery**: Continues parsing even with syntax errors
4. **Query Language**: S-expression based queries for pattern matching
5. **Consistency**: Uniform API across all supported languages

## Query Syntax Basics

Tree-sitter uses S-expression queries to match patterns in syntax trees. Here's the basic syntax:

### Basic Node Matching

```scheme
; Match any function definition node
(function_definition)

; Match function definition and capture its name
(function_definition name: (identifier) @function_name)

; Match multiple node types
[(function_definition) (method_definition)] @function_or_method
```

### Node Fields

```scheme
; Match nodes with specific fields
(class_definition
  name: (identifier) @class_name
  body: (block) @class_body)

; Optional fields with ?
(function_definition
  decorators: (decorator_list)? @decorators
  name: (identifier) @function_name)
```

### Wildcards and Anchors

```scheme
; Match any child with _
(class_definition
  name: (_) @class_name)

; Anchor to direct children with .
(module . (comment) @module_docstring)
```

### Predicates

```scheme
; String equality predicate
((identifier) @constant
 (#eq? @constant "MAX_SIZE"))

; Pattern matching predicate
((string) @docstring
 (#match? @docstring "^\"\"\""))
```

## Language-Specific Patterns

### Python

Python queries focus on extracting classes, functions, imports, decorators, and documentation:

```scheme
; Class definitions with inheritance
(class_definition
  name: (identifier) @class_name
  superclasses: (argument_list)? @inheritance) @class

; Function definitions (regular and async)
[(function_definition name: (identifier) @func_name)
 (async_function_definition name: (identifier) @async_func_name)] @function

; Method definitions within classes
(class_definition
  body: (block
    (function_definition name: (identifier) @method_name)))

; Import statements
[(import_statement) @import
 (import_from_statement
   module_name: (dotted_name) @module
   name: (dotted_name)? @imported_name)] @import_from

; Decorators
(decorator
  (identifier) @decorator_name) @decorator

; Docstrings (module, class, or function level)
[(module . (expression_statement (string) @module_docstring))
 (class_definition
   body: (block . (expression_statement (string) @class_docstring)))
 (function_definition
   body: (block . (expression_statement (string) @function_docstring)))]

; Type annotations
(function_definition
  parameters: (parameters
    (typed_parameter
      name: (identifier) @param_name
      type: (_) @param_type))
  return_type: (_)? @return_type)

; Exception handling
(try_statement
  body: (block) @try_body
  (except_clause
    type: (_)? @exception_type
    body: (block) @except_body))
```

### JavaScript/TypeScript

JavaScript and TypeScript queries handle modern ES6+ syntax and TypeScript-specific constructs:

```scheme
; Class declarations
(class_declaration
  name: (identifier) @class_name
  heritage: (class_heritage)? @extends) @class

; Function declarations and expressions
[(function_declaration name: (identifier) @func_name)
 (function_expression name: (identifier)? @func_expr_name)
 (arrow_function
   parameter: (identifier) @arrow_param)] @function

; Variable declarations with destructuring
(variable_declaration
  (variable_declarator
    name: [(identifier) @var_name
           (object_pattern) @destructured_object
           (array_pattern) @destructured_array]
    value: (_)? @initial_value))

; Import/Export statements
[(import_statement
   source: (string) @import_source)
 (export_statement
   declaration: (_)? @export_declaration)
 (export_statement
   source: (string) @reexport_source)] @import_export

; JSX Elements (React)
(jsx_element
  opening_element: (jsx_opening_element
    name: (identifier) @component_name)
  children: (_)* @jsx_children
  closing_element: (jsx_closing_element))

; TypeScript interfaces
(interface_declaration
  name: (identifier) @interface_name
  body: (interface_body) @interface_members) @interface

; TypeScript type aliases
(type_alias_declaration
  name: (identifier) @type_name
  value: (_) @type_definition) @type_alias

; TypeScript generics
[(class_declaration
   type_parameters: (type_parameters) @class_generics)
 (function_declaration
   type_parameters: (type_parameters) @function_generics)]

; Async/await patterns
[(function_declaration
   (await_expression) @await_usage)
 (arrow_function
   async: "async" @async_arrow)]
```

### Markdown

Markdown queries extract document structure and embedded code:

```scheme
; Headings with levels
(atx_heading
  (atx_h1_marker) @h1_marker
  (heading_content) @h1_content) @h1

(atx_heading
  [(atx_h2_marker) @h2_marker
   (atx_h3_marker) @h3_marker
   (atx_h4_marker) @h4_marker
   (atx_h5_marker) @h5_marker
   (atx_h6_marker) @h6_marker]
  (heading_content) @heading_content) @heading

; Code blocks with language
(fenced_code_block
  (info_string) @language
  (code_fence_content) @code_content) @code_block

; Lists (ordered and unordered)
[(unordered_list
   (list_item
     (list_marker) @bullet
     (paragraph) @item_content))
 (ordered_list
   (list_item
     (list_marker) @number
     (paragraph) @item_content))] @list

; Links and references
[(inline_link
   (link_text) @link_text
   (link_destination) @url)
 (reference_link
   (link_label) @ref_label)
 (link_reference_definition
   (link_label) @def_label
   (link_destination) @def_url)] @link

; Emphasis and strong emphasis
[(emphasis
   (emphasis_content) @italic_text)
 (strong_emphasis
   (strong_emphasis_content) @bold_text)]

; Block quotes
(block_quote
  (paragraph) @quote_content) @quote

; Tables
(table
  (table_header
    (table_cell) @header_cell)
  (table_row
    (table_cell) @data_cell)) @table
```

### Generic Language Patterns

For languages without specific handlers, use pattern-based node discovery:

```scheme
; Function-like constructs
[(function_definition)
 (method_definition)
 (function_declaration)
 (procedure_declaration)
 (subroutine_declaration)] @function_like

; Class-like constructs
[(class_definition)
 (class_declaration)
 (struct_declaration)
 (interface_declaration)
 (trait_declaration)] @class_like

; Import-like constructs
[(import_statement)
 (import_declaration)
 (include_statement)
 (require_statement)
 (use_statement)
 (using_directive)] @import_like

; Variable declarations
[(variable_declaration)
 (let_declaration)
 (const_declaration)
 (var_declaration)
 (field_declaration)] @variable_like

; Control flow
[(if_statement)
 (while_statement)
 (for_statement)
 (switch_statement)
 (match_expression)] @control_flow

; Error handling
[(try_statement)
 (catch_clause)
 (finally_clause)
 (throw_statement)] @error_handling
```

## Extending Language Support

To add support for a new language, follow these steps:

### 1. Add Language Mapping

Update the `LANGUAGE_MAP` dictionary in `tree_sitter_analyzer.py`:

```python
LANGUAGE_MAP = {
    # ... existing mappings ...
    '.nim': 'nim',           # Add new extension mapping
    '.zig': 'zig',           # Multiple extensions can map to same language
    '.zir': 'zig',
}
```

### 2. Define Language Queries

Add language-specific queries in the `_setup_queries` method:

```python
def _setup_queries(self):
    # ... existing queries ...
    
    # Nim language queries
    self._queries['nim'] = {
        'procedures': '(proc_declaration name: (identifier) @proc_name)',
        'types': '(type_declaration name: (identifier) @type_name)',
        'imports': '(import_statement (identifier) @import_name)',
        'templates': '(template_declaration name: (identifier) @template_name)',
        'macros': '(macro_declaration name: (identifier) @macro_name)',
    }
```

### 3. Create Analysis Method

Add a language-specific analysis method:

```python
def _analyze_nim_tree(self, tree, content: str) -> Dict[str, Any]:
    """Analyze Nim-specific constructs."""
    analysis = {}
    
    try:
        # Extract procedures
        if 'procedures' in self._queries['nim']:
            query = tsl.get_query('nim', self._queries['nim']['procedures'])
            procedures = [match[0].text.decode() for match in query.matches(tree.root_node)]
            analysis['procedures'] = procedures
        
        # Extract types
        if 'types' in self._queries['nim']:
            query = tsl.get_query('nim', self._queries['nim']['types'])
            types = [match[0].text.decode() for match in query.matches(tree.root_node)]
            analysis['types'] = types
        
        # Add more Nim-specific analysis...
        
    except Exception as e:
        analysis['nim_analysis_error'] = str(e)
    
    return analysis
```

### 4. Update Analysis Router

Add the new language to the analysis router in `analyze_file`:

```python
# Language-specific analysis
if language == 'python':
    analysis.update(self._analyze_python_tree(tree, content))
elif language in ('javascript', 'typescript', 'tsx'):
    analysis.update(self._analyze_javascript_tree(tree, content, language))
elif language == 'markdown':
    analysis.update(self._analyze_markdown_tree(tree, content))
elif language == 'nim':  # Add new language
    analysis.update(self._analyze_nim_tree(tree, content))
else:
    # Generic analysis for other languages
    analysis.update(self._analyze_generic_tree(tree, content, language))
```

### 5. Test Language Support

Create comprehensive tests for the new language:

```python
@pytest.fixture
def sample_nim_file(self, tmp_path):
    """Create sample Nim file."""
    content = '''# Sample Nim file
import os, strutils

type
  Person = object
    name: string
    age: int

proc greet(p: Person): string =
  result = "Hello, " & p.name

template log(msg: string) =
  echo "[LOG] ", msg

when isMainModule:
  let person = Person(name: "Alice", age: 30)
  echo greet(person)
'''
    file_path = tmp_path / "sample.nim"
    file_path.write_text(content)
    return file_path

async def test_nim_analysis(self, analyzer, sample_nim_file):
    """Test Nim file analysis."""
    result = await analyzer.analyze_file(sample_nim_file, 'nim')
    
    assert result['language'] == 'nim'
    assert 'procedures' in result
    assert 'greet' in result['procedures']
    assert 'types' in result
    assert 'Person' in result['types']
```

## Performance Optimization

### 1. Query Caching

Tree-sitter queries are compiled and cached for reuse:

```python
class TreeSitterAnalyzer:
    def __init__(self):
        self._parsers = {}      # Cache parsers by language
        self._queries = {}      # Cache query strings
        self._compiled_queries = {}  # Cache compiled queries
    
    def _get_compiled_query(self, language: str, query_name: str):
        """Get or compile a query with caching."""
        cache_key = f"{language}:{query_name}"
        
        if cache_key not in self._compiled_queries:
            query_string = self._queries[language][query_name]
            self._compiled_queries[cache_key] = tsl.get_query(language, query_string)
        
        return self._compiled_queries[cache_key]
```

### 2. Incremental Parsing

For large files or real-time updates, use incremental parsing:

```python
def update_parse_tree(self, tree, old_content: bytes, new_content: bytes, edit):
    """Incrementally update parse tree with changes."""
    # Apply edit to the tree
    tree.edit(
        start_byte=edit.start_byte,
        old_end_byte=edit.old_end_byte,
        new_end_byte=edit.new_end_byte,
        start_point=edit.start_point,
        old_end_point=edit.old_end_point,
        new_end_point=edit.new_end_point
    )
    
    # Re-parse only the changed portion
    parser = self._get_parser(language)
    return parser.parse(new_content, tree)
```

### 3. Parallel Processing

Process multiple files in parallel for better performance:

```python
async def analyze_files_parallel(self, file_paths: List[Path], max_workers: int = 4):
    """Analyze multiple files in parallel."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = []
        for file_path in file_paths:
            language = self._detect_language(file_path)
            if language:
                task = asyncio.create_task(
                    self.analyze_file(file_path, language)
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip(file_paths, results))
```

### 4. Memory Management

For very large files, use streaming analysis:

```python
def analyze_large_file_streaming(self, file_path: Path, language: str, chunk_size: int = 1024 * 1024):
    """Analyze large files in chunks to manage memory."""
    parser = self._get_parser(language)
    tree = None
    
    with open(file_path, 'rb') as f:
        offset = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            # Parse chunk with previous tree as context
            tree = parser.parse(chunk, tree)
            
            # Analyze current tree state
            yield self._analyze_tree_chunk(tree, offset, len(chunk))
            
            offset += len(chunk)
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Query Syntax Errors

**Problem**: Query compilation fails with syntax error.

**Solution**: Validate query syntax using Tree-sitter playground or test script:

```python
def validate_query(language: str, query_string: str):
    """Validate a Tree-sitter query."""
    try:
        query = tsl.get_query(language, query_string)
        print(f"✓ Query valid for {language}")
        return True
    except Exception as e:
        print(f"✗ Query invalid: {e}")
        return False

# Test query
validate_query('python', '(class_definition name: (identifier) @class_name)')
```

#### 2. Missing Language Support

**Problem**: Language not supported by tree-sitter-languages.

**Solution**: Install additional language parser:

```python
# Check available languages
import tree_sitter_languages as tsl
print("Available languages:", tsl.LANGUAGES)

# For missing languages, use tree-sitter directly
import tree_sitter
from tree_sitter_language_pack import get_language

# Load language grammar
language = get_language('exotic_lang')
parser = tree_sitter.Parser()
parser.set_language(language)
```

#### 3. Performance Issues

**Problem**: Analysis is slow for large codebases.

**Solution**: Profile and optimize:

```python
import cProfile
import pstats

def profile_analysis():
    """Profile Tree-sitter analysis performance."""
    profiler = cProfile.Profile()
    
    profiler.enable()
    # Run analysis
    analyzer = TreeSitterAnalyzer()
    asyncio.run(analyzer.analyze_file(large_file, 'python'))
    profiler.disable()
    
    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

#### 4. Unicode and Encoding Issues

**Problem**: Parser fails with unicode/encoding errors.

**Solution**: Handle encoding explicitly:

```python
def safe_read_file(file_path: Path) -> bytes:
    """Safely read file content for Tree-sitter parsing."""
    try:
        # Tree-sitter works with bytes
        return file_path.read_bytes()
    except Exception:
        # Fallback to UTF-8 with error handling
        content = file_path.read_text(encoding='utf-8', errors='replace')
        return content.encode('utf-8')
```

#### 5. Memory Leaks

**Problem**: Memory usage grows with repeated parsing.

**Solution**: Properly manage parser lifecycle:

```python
class TreeSitterAnalyzer:
    def cleanup(self):
        """Clean up parser resources."""
        self._parsers.clear()
        self._compiled_queries.clear()
        # Force garbage collection for large trees
        import gc
        gc.collect()
```

## Query Pattern Reference

### Quick Reference Table

| Pattern | Description | Example |
|---------|-------------|---------|
| `(node_type)` | Match node by type | `(function_definition)` |
| `@capture` | Capture matched node | `(identifier) @name` |
| `[alternatives]` | Match any of the alternatives | `[(class) (struct)] @type` |
| `field:` | Match specific field | `name: (identifier) @func_name` |
| `(_)` | Match any node type | `value: (_) @any_value` |
| `.` | Anchor to direct child | `(module . (comment) @first)` |
| `?` | Optional match | `decorators: (decorator_list)? @decorators` |
| `*` | Zero or more | `children: (_)* @all_children` |
| `+` | One or more | `parameters: (identifier)+ @params` |
| `#predicate?` | Apply predicate | `(#eq? @name "main")` |

### Advanced Patterns

```scheme
; Negation patterns
(function_definition
  name: (identifier) @func_name
  (#not-eq? @func_name "test"))

; Regular expression matching
((string) @version
 (#match? @version "^[0-9]+\\.[0-9]+\\.[0-9]+$"))

; Positional patterns
(call_expression
  function: (identifier) @func
  arguments: (argument_list
    . (string) @first_arg))  ; First argument must be string

; Nested captures
(class_definition
  name: (identifier) @class_name
  body: (block
    (function_definition
      name: (identifier) @method_name
      parameters: (parameters
        . (identifier) @self))))  ; First param is 'self'

; Complex field matching
(assignment
  left: [(identifier) @var
         (attribute
           object: (identifier) @obj
           attribute: (identifier) @attr)]
  right: (_) @value)
```

## Best Practices

1. **Start Simple**: Begin with basic patterns and add complexity as needed
2. **Test Incrementally**: Test each query component separately
3. **Use Captures Wisely**: Only capture what you need to minimize memory usage
4. **Handle Errors Gracefully**: Always include error handling for parse failures
5. **Profile Performance**: Measure query performance on representative code samples
6. **Document Patterns**: Comment complex queries for maintainability
7. **Version Control**: Track query changes as they can affect analysis results

## Conclusion

Tree-sitter provides a powerful, efficient way to analyze code across multiple languages in the Claude PM Framework. By understanding query patterns and following best practices, you can extend language support and create sophisticated code analysis tools for agent discovery and modification tracking.

For more information:
- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [Tree-sitter Query Syntax](https://tree-sitter.github.io/tree-sitter/using-parsers#pattern-matching-with-queries)
- [Tree-sitter Playground](https://tree-sitter.github.io/tree-sitter/playground)