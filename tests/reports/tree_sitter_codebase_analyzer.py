#!/usr/bin/env python3
"""
Tree-sitter based semantic analysis for claude_pm codebase.
Identifies unused code, complex functions, circular dependencies, and optimization opportunities.
"""

import os
import json
import ast
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime

# Optional import for circular dependency detection
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("Warning: networkx not installed - circular dependency detection disabled")

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser, Node
except ImportError:
    print("Error: tree-sitter-python not installed")
    print("Install with: pip install tree-sitter tree-sitter-python")
    exit(1)


class CodebaseAnalyzer:
    """Comprehensive codebase analyzer using tree-sitter."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.parser = Parser()
        self.parser.set_language(Language(tspython.language()))
        
        # Analysis results
        self.functions: Dict[str, Dict] = {}
        self.classes: Dict[str, Dict] = {}
        self.imports: Dict[str, List] = defaultdict(list)
        self.function_calls: Dict[str, Set[str]] = defaultdict(set)
        self.class_instantiations: Dict[str, Set[str]] = defaultdict(set)
        self.import_usage: Dict[str, Set[str]] = defaultdict(set)
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.complexity_scores: Dict[str, int] = {}
        self.line_counts: Dict[str, int] = {}
        self.docstring_coverage: Dict[str, bool] = {}
        
    def analyze(self) -> Dict[str, Any]:
        """Run complete analysis on the codebase."""
        print(f"Analyzing codebase at: {self.root_path}")
        
        # Collect all Python files
        python_files = list(self.root_path.rglob("*.py"))
        print(f"Found {len(python_files)} Python files")
        
        # First pass: Extract definitions and imports
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
            self._analyze_file_definitions(file_path)
        
        # Second pass: Analyze usage
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
            self._analyze_file_usage(file_path)
        
        # Analyze results
        results = {
            "timestamp": datetime.now().isoformat(),
            "root_path": str(self.root_path),
            "total_files": len(python_files),
            "unused_functions": self._find_unused_functions(),
            "unused_classes": self._find_unused_classes(),
            "unused_imports": self._find_unused_imports(),
            "complex_functions": self._find_complex_functions(),
            "circular_dependencies": self._find_circular_dependencies(),
            "large_files": self._find_large_files(),
            "missing_docstrings": self._find_missing_docstrings(),
            "duplicate_patterns": self._find_duplicate_patterns(),
            "optimization_opportunities": self._identify_optimizations(),
        }
        
        return results
    
    def _analyze_file_definitions(self, file_path: Path):
        """Extract function and class definitions from a file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = self.parser.parse(bytes(content, 'utf-8'))
            
            rel_path = str(file_path.relative_to(self.root_path))
            self.line_counts[rel_path] = len(content.splitlines())
            
            self._extract_definitions(tree.root_node, rel_path, content)
            self._extract_imports(tree.root_node, rel_path, content)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _analyze_file_usage(self, file_path: Path):
        """Analyze function calls and class usage in a file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = self.parser.parse(bytes(content, 'utf-8'))
            
            rel_path = str(file_path.relative_to(self.root_path))
            self._extract_usage(tree.root_node, rel_path, content)
            
        except Exception as e:
            print(f"Error analyzing usage in {file_path}: {e}")
    
    def _extract_definitions(self, node: Node, file_path: str, content: str):
        """Extract function and class definitions."""
        if node.type == 'function_definition':
            func_name = self._get_node_text(node.child_by_field_name('name'), content)
            if func_name:
                func_key = f"{file_path}::{func_name}"
                self.functions[func_key] = {
                    'name': func_name,
                    'file': file_path,
                    'line': node.start_point[0] + 1,
                    'complexity': self._calculate_complexity(node),
                    'lines': node.end_point[0] - node.start_point[0] + 1,
                    'has_docstring': self._has_docstring(node),
                    'parameters': self._get_parameters(node, content),
                    'is_async': node.child_by_field_name('async') is not None,
                    'decorators': self._get_decorators(node, content),
                }
                self.complexity_scores[func_key] = self.functions[func_key]['complexity']
                self.docstring_coverage[func_key] = self.functions[func_key]['has_docstring']
        
        elif node.type == 'class_definition':
            class_name = self._get_node_text(node.child_by_field_name('name'), content)
            if class_name:
                class_key = f"{file_path}::{class_name}"
                self.classes[class_key] = {
                    'name': class_name,
                    'file': file_path,
                    'line': node.start_point[0] + 1,
                    'methods': self._get_class_methods(node, content),
                    'has_docstring': self._has_docstring(node),
                    'decorators': self._get_decorators(node, content),
                }
                self.docstring_coverage[class_key] = self.classes[class_key]['has_docstring']
        
        # Recurse
        for child in node.children:
            self._extract_definitions(child, file_path, content)
    
    def _extract_imports(self, node: Node, file_path: str, content: str):
        """Extract import statements."""
        if node.type == 'import_statement':
            import_names = []
            for child in node.children:
                if child.type == 'dotted_name' or child.type == 'identifier':
                    import_names.append(self._get_node_text(child, content))
            
            for name in import_names:
                self.imports[file_path].append({
                    'name': name,
                    'type': 'import',
                    'line': node.start_point[0] + 1,
                })
        
        elif node.type == 'import_from_statement':
            module_node = node.child_by_field_name('module')
            module_name = self._get_node_text(module_node, content) if module_node else ''
            
            import_list = []
            for child in node.children:
                if child.type == 'import_list' or child.type == 'identifier':
                    if child.type == 'identifier' and child != module_node:
                        import_list.append(self._get_node_text(child, content))
                    elif child.type == 'import_list':
                        for import_child in child.children:
                            if import_child.type == 'identifier' or import_child.type == 'dotted_name':
                                import_list.append(self._get_node_text(import_child, content))
            
            for name in import_list:
                self.imports[file_path].append({
                    'name': name,
                    'module': module_name,
                    'type': 'from_import',
                    'line': node.start_point[0] + 1,
                })
        
        # Recurse
        for child in node.children:
            self._extract_imports(child, file_path, content)
    
    def _extract_usage(self, node: Node, file_path: str, content: str):
        """Extract function calls and class instantiations."""
        if node.type == 'call':
            func_node = node.child_by_field_name('function')
            if func_node:
                func_name = self._get_call_name(func_node, content)
                if func_name:
                    self.function_calls[file_path].add(func_name)
                    
                    # Track import usage
                    base_name = func_name.split('.')[0]
                    self.import_usage[file_path].add(base_name)
                    
                    # Check if it's a class instantiation
                    if func_name[0].isupper() or '.' in func_name and func_name.split('.')[-1][0].isupper():
                        self.class_instantiations[file_path].add(func_name)
        
        elif node.type == 'attribute':
            # Track attribute access for import usage
            obj_name = self._get_attribute_base(node, content)
            if obj_name:
                self.import_usage[file_path].add(obj_name)
        
        # Recurse
        for child in node.children:
            self._extract_usage(child, file_path, content)
    
    def _calculate_complexity(self, node: Node) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        def count_branches(n: Node):
            nonlocal complexity
            if n.type in ['if_statement', 'elif_clause', 'while_statement', 
                         'for_statement', 'except_clause', 'with_statement']:
                complexity += 1
            elif n.type == 'boolean_operator':
                complexity += 1
            elif n.type == 'conditional_expression':  # ternary
                complexity += 1
            
            for child in n.children:
                count_branches(child)
        
        count_branches(node)
        return complexity
    
    def _has_docstring(self, node: Node) -> bool:
        """Check if a function or class has a docstring."""
        body_node = node.child_by_field_name('body')
        if body_node and body_node.children:
            first_stmt = body_node.children[0]
            if first_stmt.type == 'expression_statement' and first_stmt.children:
                expr = first_stmt.children[0]
                return expr.type == 'string'
        return False
    
    def _get_parameters(self, node: Node, content: str) -> List[str]:
        """Extract function parameters."""
        params = []
        param_node = node.child_by_field_name('parameters')
        if param_node:
            for child in param_node.children:
                if child.type in ['identifier', 'typed_parameter', 'default_parameter']:
                    param_name = self._get_parameter_name(child, content)
                    if param_name and param_name not in ['self', 'cls']:
                        params.append(param_name)
        return params
    
    def _get_parameter_name(self, node: Node, content: str) -> str:
        """Extract parameter name from various parameter node types."""
        if node.type == 'identifier':
            return self._get_node_text(node, content)
        elif node.type in ['typed_parameter', 'default_parameter']:
            for child in node.children:
                if child.type == 'identifier':
                    return self._get_node_text(child, content)
        return ''
    
    def _get_decorators(self, node: Node, content: str) -> List[str]:
        """Extract decorators from a function or class."""
        decorators = []
        for child in node.children:
            if child.type == 'decorator':
                dec_text = self._get_node_text(child, content).strip('@')
                decorators.append(dec_text)
        return decorators
    
    def _get_class_methods(self, node: Node, content: str) -> List[str]:
        """Extract method names from a class."""
        methods = []
        body_node = node.child_by_field_name('body')
        if body_node:
            for child in body_node.children:
                if child.type == 'function_definition':
                    method_name = self._get_node_text(child.child_by_field_name('name'), content)
                    if method_name:
                        methods.append(method_name)
        return methods
    
    def _get_call_name(self, node: Node, content: str) -> str:
        """Extract the full name from a call node."""
        if node.type == 'identifier':
            return self._get_node_text(node, content)
        elif node.type == 'attribute':
            return self._get_node_text(node, content)
        return ''
    
    def _get_attribute_base(self, node: Node, content: str) -> str:
        """Get the base object name from an attribute access."""
        obj_node = node.child_by_field_name('object')
        if obj_node and obj_node.type == 'identifier':
            return self._get_node_text(obj_node, content)
        return ''
    
    def _get_node_text(self, node: Node, content: str) -> str:
        """Extract text content from a node."""
        if node is None:
            return ''
        return content[node.start_byte:node.end_byte]
    
    def _find_unused_functions(self) -> List[Dict]:
        """Find functions that are never called."""
        unused = []
        
        # Build set of all called functions
        all_calls = set()
        for calls in self.function_calls.values():
            all_calls.update(calls)
        
        for func_key, func_info in self.functions.items():
            func_name = func_info['name']
            
            # Skip special methods and private functions
            if func_name.startswith('__') or func_name == 'main':
                continue
            
            # Skip decorated functions (might be used externally)
            if func_info['decorators']:
                continue
            
            # Check if function is called
            found = False
            for call in all_calls:
                if call == func_name or call.endswith(f'.{func_name}'):
                    found = True
                    break
            
            if not found:
                unused.append({
                    'function': func_name,
                    'file': func_info['file'],
                    'line': func_info['line'],
                    'complexity': func_info['complexity'],
                    'lines_of_code': func_info['lines'],
                })
        
        return sorted(unused, key=lambda x: x['complexity'], reverse=True)
    
    def _find_unused_classes(self) -> List[Dict]:
        """Find classes that are never instantiated."""
        unused = []
        
        # Build set of all instantiated classes
        all_instantiations = set()
        for instantiations in self.class_instantiations.values():
            all_instantiations.update(instantiations)
        
        for class_key, class_info in self.classes.items():
            class_name = class_info['name']
            
            # Skip decorated classes
            if class_info['decorators']:
                continue
            
            # Check if class is instantiated
            found = False
            for inst in all_instantiations:
                if inst == class_name or inst.endswith(f'.{class_name}'):
                    found = True
                    break
            
            # Also check if it's used as a base class
            if not found:
                for other_class in self.classes.values():
                    if class_name in str(other_class.get('decorators', [])):
                        found = True
                        break
            
            if not found:
                unused.append({
                    'class': class_name,
                    'file': class_info['file'],
                    'line': class_info['line'],
                    'methods': len(class_info['methods']),
                })
        
        return sorted(unused, key=lambda x: x['methods'], reverse=True)
    
    def _find_unused_imports(self) -> List[Dict]:
        """Find imports that are never used."""
        unused = []
        
        for file_path, imports_list in self.imports.items():
            used_names = self.import_usage.get(file_path, set())
            
            for import_info in imports_list:
                import_name = import_info['name']
                base_name = import_name.split('.')[0]
                
                # Check various forms of usage
                if (import_name not in used_names and 
                    base_name not in used_names and
                    not any(import_name in str(call) for call in self.function_calls.get(file_path, []))):
                    
                    unused.append({
                        'import': import_name,
                        'file': file_path,
                        'line': import_info['line'],
                        'type': import_info['type'],
                        'module': import_info.get('module', ''),
                    })
        
        return sorted(unused, key=lambda x: (x['file'], x['line']))
    
    def _find_complex_functions(self, threshold: int = 10) -> List[Dict]:
        """Find functions with high cyclomatic complexity."""
        complex_funcs = []
        
        for func_key, complexity in self.complexity_scores.items():
            if complexity > threshold:
                func_info = self.functions[func_key]
                complex_funcs.append({
                    'function': func_info['name'],
                    'file': func_info['file'],
                    'line': func_info['line'],
                    'complexity': complexity,
                    'lines_of_code': func_info['lines'],
                    'parameters': len(func_info['parameters']),
                })
        
        return sorted(complex_funcs, key=lambda x: x['complexity'], reverse=True)
    
    def _find_circular_dependencies(self) -> List[List[str]]:
        """Find circular import dependencies."""
        if not HAS_NETWORKX:
            return []
            
        # Build dependency graph
        G = nx.DiGraph()
        
        for file_path, imports_list in self.imports.items():
            for import_info in imports_list:
                if import_info['type'] == 'from_import' and import_info['module']:
                    module = import_info['module']
                    if module.startswith('claude_pm'):
                        # Convert module to file path
                        module_path = module.replace('.', '/') + '.py'
                        if module_path.startswith('claude_pm/'):
                            module_path = module_path[len('claude_pm/'):]
                        
                        G.add_edge(file_path, module_path)
        
        # Find cycles
        cycles = list(nx.simple_cycles(G))
        return [cycle for cycle in cycles if len(cycle) > 1]
    
    def _find_large_files(self, threshold: int = 500) -> List[Dict]:
        """Find files with too many lines."""
        large_files = []
        
        for file_path, line_count in self.line_counts.items():
            if line_count > threshold:
                large_files.append({
                    'file': file_path,
                    'lines': line_count,
                    'functions': len([f for f in self.functions.values() if f['file'] == file_path]),
                    'classes': len([c for c in self.classes.values() if c['file'] == file_path]),
                })
        
        return sorted(large_files, key=lambda x: x['lines'], reverse=True)
    
    def _find_missing_docstrings(self) -> List[Dict]:
        """Find functions and classes missing docstrings."""
        missing = []
        
        for key, has_docstring in self.docstring_coverage.items():
            if not has_docstring:
                if key in self.functions:
                    info = self.functions[key]
                    if not info['name'].startswith('_'):  # Skip private functions
                        missing.append({
                            'type': 'function',
                            'name': info['name'],
                            'file': info['file'],
                            'line': info['line'],
                            'complexity': info['complexity'],
                        })
                elif key in self.classes:
                    info = self.classes[key]
                    missing.append({
                        'type': 'class',
                        'name': info['name'],
                        'file': info['file'],
                        'line': info['line'],
                        'methods': len(info['methods']),
                    })
        
        return sorted(missing, key=lambda x: x['file'])
    
    def _find_duplicate_patterns(self) -> Dict[str, List[Dict]]:
        """Find duplicate code patterns."""
        # Group functions by similar characteristics
        patterns = defaultdict(list)
        
        # Group by parameter count and complexity
        for func_key, func_info in self.functions.items():
            if func_info['lines'] > 5:  # Skip tiny functions
                pattern_key = f"params:{len(func_info['parameters'])}_complexity:{func_info['complexity']}_lines:{func_info['lines'] // 5 * 5}"
                patterns[pattern_key].append({
                    'function': func_info['name'],
                    'file': func_info['file'],
                    'line': func_info['line'],
                })
        
        # Filter to show only patterns with multiple occurrences
        duplicate_patterns = {k: v for k, v in patterns.items() if len(v) > 1}
        
        return duplicate_patterns
    
    def _identify_optimizations(self) -> List[Dict]:
        """Identify specific optimization opportunities."""
        optimizations = []
        
        # Long parameter lists
        for func_key, func_info in self.functions.items():
            if len(func_info['parameters']) > 5:
                optimizations.append({
                    'type': 'long_parameter_list',
                    'function': func_info['name'],
                    'file': func_info['file'],
                    'line': func_info['line'],
                    'parameter_count': len(func_info['parameters']),
                    'suggestion': 'Consider using a configuration object or kwargs',
                })
        
        # Async functions that might not need to be async
        for func_key, func_info in self.functions.items():
            if func_info['is_async'] and func_info['complexity'] < 3:
                optimizations.append({
                    'type': 'unnecessary_async',
                    'function': func_info['name'],
                    'file': func_info['file'],
                    'line': func_info['line'],
                    'suggestion': 'Simple async function - verify if async is needed',
                })
        
        # Files with too many imports
        for file_path, imports_list in self.imports.items():
            if len(imports_list) > 20:
                optimizations.append({
                    'type': 'too_many_imports',
                    'file': file_path,
                    'import_count': len(imports_list),
                    'suggestion': 'Consider splitting into multiple modules',
                })
        
        return optimizations


def generate_report(results: Dict[str, Any]) -> str:
    """Generate a markdown report from analysis results."""
    report = f"""# Claude PM Codebase Analysis Report

Generated: {results['timestamp']}
Root Path: {results['root_path']}
Total Files Analyzed: {results['total_files']}

## Executive Summary

- **Unused Functions**: {len(results['unused_functions'])}
- **Unused Classes**: {len(results['unused_classes'])}
- **Unused Imports**: {len(results['unused_imports'])}
- **Complex Functions**: {len(results['complex_functions'])}
- **Circular Dependencies**: {len(results['circular_dependencies'])}
- **Large Files**: {len(results['large_files'])}
- **Missing Docstrings**: {len(results['missing_docstrings'])}

## Detailed Findings

### 1. Unused Functions

Functions that are defined but never called within the codebase:

"""
    
    if results['unused_functions']:
        for func in results['unused_functions'][:20]:  # Show top 20
            report += f"- `{func['function']}` in `{func['file']}:{func['line']}` (complexity: {func['complexity']}, {func['lines_of_code']} lines)\n"
        
        if len(results['unused_functions']) > 20:
            report += f"\n... and {len(results['unused_functions']) - 20} more\n"
    else:
        report += "No unused functions found.\n"
    
    report += "\n### 2. Unused Classes\n\nClasses that are defined but never instantiated:\n\n"
    
    if results['unused_classes']:
        for cls in results['unused_classes']:
            report += f"- `{cls['class']}` in `{cls['file']}:{cls['line']}` ({cls['methods']} methods)\n"
    else:
        report += "No unused classes found.\n"
    
    report += "\n### 3. Unused Imports\n\nImports that are not used in their files:\n\n"
    
    if results['unused_imports']:
        # Group by file
        imports_by_file = defaultdict(list)
        for imp in results['unused_imports']:
            imports_by_file[imp['file']].append(imp)
        
        for file_path, imports in list(imports_by_file.items())[:10]:  # Show first 10 files
            report += f"\n**{file_path}**:\n"
            for imp in imports[:5]:  # Show first 5 imports per file
                if imp['type'] == 'from_import':
                    report += f"- Line {imp['line']}: `from {imp['module']} import {imp['import']}`\n"
                else:
                    report += f"- Line {imp['line']}: `import {imp['import']}`\n"
            if len(imports) > 5:
                report += f"- ... and {len(imports) - 5} more\n"
    else:
        report += "No unused imports found.\n"
    
    report += "\n### 4. Complex Functions\n\nFunctions with high cyclomatic complexity (>10):\n\n"
    
    if results['complex_functions']:
        for func in results['complex_functions'][:15]:
            report += f"- `{func['function']}` in `{func['file']}:{func['line']}`\n"
            report += f"  - Complexity: {func['complexity']}\n"
            report += f"  - Lines: {func['lines_of_code']}\n"
            report += f"  - Parameters: {func['parameters']}\n"
    else:
        report += "No overly complex functions found.\n"
    
    report += "\n### 5. Circular Dependencies\n\n"
    
    if results['circular_dependencies']:
        for cycle in results['circular_dependencies']:
            report += f"- Cycle: {' → '.join(cycle)} → {cycle[0]}\n"
    else:
        report += "No circular dependencies found.\n"
    
    report += "\n### 6. Large Files\n\nFiles with more than 500 lines:\n\n"
    
    if results['large_files']:
        for file_info in results['large_files']:
            report += f"- `{file_info['file']}`: {file_info['lines']} lines ({file_info['functions']} functions, {file_info['classes']} classes)\n"
    else:
        report += "No excessively large files found.\n"
    
    report += "\n### 7. Missing Docstrings\n\nPublic functions and classes without docstrings:\n\n"
    
    if results['missing_docstrings']:
        # Group by type
        funcs = [d for d in results['missing_docstrings'] if d['type'] == 'function']
        classes = [d for d in results['missing_docstrings'] if d['type'] == 'class']
        
        if funcs:
            report += "**Functions:**\n"
            for doc in funcs[:10]:
                report += f"- `{doc['name']}` in `{doc['file']}:{doc['line']}` (complexity: {doc['complexity']})\n"
            if len(funcs) > 10:
                report += f"... and {len(funcs) - 10} more\n"
        
        if classes:
            report += "\n**Classes:**\n"
            for doc in classes[:10]:
                report += f"- `{doc['name']}` in `{doc['file']}:{doc['line']}` ({doc['methods']} methods)\n"
            if len(classes) > 10:
                report += f"... and {len(classes) - 10} more\n"
    else:
        report += "All public functions and classes have docstrings.\n"
    
    report += "\n### 8. Optimization Opportunities\n\n"
    
    if results['optimization_opportunities']:
        # Group by type
        opt_by_type = defaultdict(list)
        for opt in results['optimization_opportunities']:
            opt_by_type[opt['type']].append(opt)
        
        for opt_type, opts in opt_by_type.items():
            report += f"\n**{opt_type.replace('_', ' ').title()}:**\n"
            for opt in opts[:5]:
                if 'function' in opt:
                    report += f"- `{opt['function']}` in `{opt['file']}:{opt['line']}`\n"
                else:
                    report += f"- `{opt['file']}`\n"
                report += f"  - {opt['suggestion']}\n"
    else:
        report += "No specific optimization opportunities identified.\n"
    
    report += "\n## Recommendations\n\n"
    report += "1. **Remove unused code**: Delete or deprecate unused functions and classes\n"
    report += "2. **Clean up imports**: Remove unused imports to improve clarity\n"
    report += "3. **Refactor complex functions**: Break down functions with high complexity\n"
    report += "4. **Resolve circular dependencies**: Refactor to eliminate circular imports\n"
    report += "5. **Split large files**: Consider breaking up files over 500 lines\n"
    report += "6. **Add documentation**: Write docstrings for public APIs\n"
    report += "7. **Optimize structures**: Address specific optimization opportunities\n"
    
    return report


def main():
    """Run the analysis and generate reports."""
    # Analyze claude_pm directory
    analyzer = CodebaseAnalyzer("/Users/masa/Projects/claude-multiagent-pm/claude_pm")
    results = analyzer.analyze()
    
    # Save raw results as JSON
    json_path = "/Users/masa/Projects/claude-multiagent-pm/tests/reports/tree_sitter_analysis_results.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved raw results to: {json_path}")
    
    # Generate and save markdown report
    report = generate_report(results)
    report_path = "/Users/masa/Projects/claude-multiagent-pm/tests/reports/tree_sitter_analysis_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Saved report to: {report_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Unused Functions: {len(results['unused_functions'])}")
    print(f"Unused Classes: {len(results['unused_classes'])}")
    print(f"Unused Imports: {len(results['unused_imports'])}")
    print(f"Complex Functions: {len(results['complex_functions'])}")
    print(f"Circular Dependencies: {len(results['circular_dependencies'])}")
    print(f"Large Files: {len(results['large_files'])}")
    print(f"Missing Docstrings: {len(results['missing_docstrings'])}")
    print("="*60)


if __name__ == "__main__":
    main()