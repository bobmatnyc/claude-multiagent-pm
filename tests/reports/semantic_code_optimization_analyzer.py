#!/usr/bin/env python3
"""
Tree-sitter based semantic analysis tool for claude_pm codebase.
Identifies unused code, redundancies, and optimization opportunities.
"""

import os
import sys
import json
import ast
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any, Optional
import subprocess
import hashlib

try:
    import tree_sitter
    from tree_sitter import Language, Parser
except ImportError:
    print("Installing tree-sitter and tree-sitter-python...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tree-sitter", "tree-sitter-python"])
    import tree_sitter
    from tree_sitter import Language, Parser

# Build Python language
try:
    from tree_sitter_python import language as python_language
    PY_LANGUAGE = Language(python_language)
except ImportError:
    print("Installing tree-sitter-python...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tree-sitter-python"])
    from tree_sitter_python import language as python_language
    PY_LANGUAGE = Language(python_language)


class SemanticCodeOptimizer:
    """Semantic analyzer for Python codebases using Tree-sitter."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.parser = Parser(PY_LANGUAGE)
        
        # Code inventory
        self.functions = {}  # file -> {name: {info}}
        self.classes = {}    # file -> {name: {info}}
        self.imports = {}    # file -> [imports]
        self.variables = {}  # file -> {name: {info}}
        
        # Usage tracking
        self.function_calls = defaultdict(set)     # function -> set of calling locations
        self.class_instantiations = defaultdict(set)  # class -> set of usage locations
        self.import_usage = defaultdict(set)       # import -> set of usage locations
        self.attribute_access = defaultdict(set)   # class.method -> set of locations
        
        # Code patterns
        self.code_hashes = defaultdict(list)  # hash -> list of (file, function, lines)
        self.similar_functions = []           # list of similar function groups
        self.complexity_scores = {}           # function -> cyclomatic complexity
        
        # Dependencies
        self.call_graph = defaultdict(set)    # function -> set of called functions
        self.import_graph = defaultdict(set)  # file -> set of imported files
        self.class_hierarchy = defaultdict(set)  # class -> set of parent classes
        
        # Issues found
        self.unused_functions = set()
        self.unused_classes = set()
        self.unused_imports = set()
        self.dead_code_blocks = []
        self.redundant_code = []
        self.circular_dependencies = []
        self.high_complexity_functions = []
        
    def analyze(self) -> Dict[str, Any]:
        """Run complete semantic analysis."""
        print("🔍 Starting semantic code optimization analysis...")
        
        # Step 1: Inventory all code elements
        print("📋 Phase 1: Building code inventory...")
        self._build_code_inventory()
        
        # Step 2: Analyze usage patterns
        print("🔗 Phase 2: Analyzing usage patterns...")
        self._analyze_usage_patterns()
        
        # Step 3: Build dependency graphs
        print("🕸️ Phase 3: Building dependency graphs...")
        self._build_dependency_graphs()
        
        # Step 4: Find unused code
        print("🗑️ Phase 4: Finding unused code...")
        self._find_unused_code()
        
        # Step 5: Calculate complexity
        print("📊 Phase 5: Calculating code complexity...")
        self._calculate_complexity()
        
        # Step 6: Find duplicate/similar code
        print("🔄 Phase 6: Finding duplicate patterns...")
        self._find_duplicate_code()
        
        # Step 7: Detect circular dependencies
        print("♻️ Phase 7: Detecting circular dependencies...")
        self._detect_circular_dependencies()
        
        # Step 8: Find dead code paths
        print("💀 Phase 8: Finding dead code paths...")
        self._find_dead_code()
        
        # Generate report
        return self._generate_optimization_report()
    
    def _build_code_inventory(self):
        """Inventory all functions, classes, and imports."""
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                tree = self.parser.parse(content)
                rel_path = str(file_path.relative_to(self.root_path))
                
                self._inventory_file(tree.root_node, content, rel_path)
                
            except Exception as e:
                print(f"Error inventorying {file_path}: {e}")
    
    def _inventory_file(self, root_node, content: bytes, file_path: str):
        """Inventory all elements in a file."""
        self.functions[file_path] = {}
        self.classes[file_path] = {}
        self.imports[file_path] = []
        self.variables[file_path] = {}
        
        def traverse(node, class_context=None):
            # Functions
            if node.type == 'function_definition':
                func_info = self._extract_function_info(node, content, class_context)
                if func_info:
                    key = f"{class_context}.{func_info['name']}" if class_context else func_info['name']
                    self.functions[file_path][key] = func_info
            
            # Classes
            elif node.type == 'class_definition':
                class_info = self._extract_class_info(node, content)
                if class_info:
                    self.classes[file_path][class_info['name']] = class_info
                    # Traverse class body with context
                    for child in node.children:
                        if child.type == 'block':
                            for stmt in child.children:
                                traverse(stmt, class_info['name'])
            
            # Imports
            elif node.type in ['import_statement', 'import_from_statement']:
                import_info = self._extract_import_info(node, content)
                if import_info:
                    self.imports[file_path].append(import_info)
            
            # Continue traversal
            else:
                for child in node.children:
                    traverse(child, class_context)
        
        traverse(root_node)
    
    def _extract_function_info(self, node, content: bytes, class_context: Optional[str]) -> Optional[Dict]:
        """Extract function information."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None
            
        name = content[name_node.start_byte:name_node.end_byte].decode('utf-8')
        
        # Get parameters
        params = []
        params_node = node.child_by_field_name('parameters')
        if params_node:
            params = self._extract_parameters(params_node, content)
        
        # Get decorators
        decorators = []
        parent = node.parent
        if parent and parent.type == 'decorated_definition':
            for child in parent.children:
                if child.type == 'decorator':
                    dec_text = content[child.start_byte:child.end_byte].decode('utf-8')
                    decorators.append(dec_text.strip('@'))
        
        # Get body for complexity analysis
        body_node = node.child_by_field_name('body')
        body_text = ""
        if body_node:
            body_text = content[body_node.start_byte:body_node.end_byte].decode('utf-8')
        
        return {
            'name': name,
            'line_start': node.start_point[0] + 1,
            'line_end': node.end_point[0] + 1,
            'params': params,
            'decorators': decorators,
            'is_method': class_context is not None,
            'class': class_context,
            'body': body_text,
            'body_hash': hashlib.md5(body_text.encode()).hexdigest()[:8]
        }
    
    def _extract_class_info(self, node, content: bytes) -> Optional[Dict]:
        """Extract class information."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None
            
        name = content[name_node.start_byte:name_node.end_byte].decode('utf-8')
        
        # Get base classes
        bases = []
        superclasses = node.child_by_field_name('superclasses')
        if superclasses:
            for arg in superclasses.children:
                if arg.type == 'identifier':
                    bases.append(content[arg.start_byte:arg.end_byte].decode('utf-8'))
        
        # Count methods
        methods = []
        body_node = node.child_by_field_name('body')
        if body_node:
            for child in body_node.children:
                if child.type == 'function_definition':
                    method_name_node = child.child_by_field_name('name')
                    if method_name_node:
                        method_name = content[method_name_node.start_byte:method_name_node.end_byte].decode('utf-8')
                        methods.append(method_name)
        
        return {
            'name': name,
            'line_start': node.start_point[0] + 1,
            'line_end': node.end_point[0] + 1,
            'bases': bases,
            'methods': methods
        }
    
    def _extract_import_info(self, node, content: bytes) -> Optional[Dict]:
        """Extract import information."""
        import_text = content[node.start_byte:node.end_byte].decode('utf-8').strip()
        
        if node.type == 'import_statement':
            # import module1, module2
            modules = []
            for child in node.children:
                if child.type == 'dotted_name':
                    modules.append(content[child.start_byte:child.end_byte].decode('utf-8'))
            
            return {
                'type': 'import',
                'modules': modules,
                'line': node.start_point[0] + 1,
                'text': import_text
            }
        
        elif node.type == 'import_from_statement':
            # from module import name1, name2
            module = None
            names = []
            
            for child in node.children:
                if child.type == 'dotted_name' and not module:
                    module = content[child.start_byte:child.end_byte].decode('utf-8')
                elif child.type == 'import_from_as_names':
                    for name_child in child.children:
                        if name_child.type == 'import_from_as_name':
                            for sub in name_child.children:
                                if sub.type == 'identifier':
                                    names.append(content[sub.start_byte:sub.end_byte].decode('utf-8'))
                                    break
                        elif name_child.type == 'identifier':
                            names.append(content[name_child.start_byte:name_child.end_byte].decode('utf-8'))
                elif child.type == 'identifier' and child.text.decode() != 'from' and child.text.decode() != 'import':
                    names.append(content[child.start_byte:child.end_byte].decode('utf-8'))
            
            return {
                'type': 'from_import',
                'module': module,
                'names': names,
                'line': node.start_point[0] + 1,
                'text': import_text
            }
        
        return None
    
    def _extract_parameters(self, params_node, content: bytes) -> List[str]:
        """Extract function parameters."""
        params = []
        for child in params_node.children:
            if child.type in ['identifier', 'typed_parameter', 'default_parameter']:
                if child.type == 'identifier':
                    params.append(content[child.start_byte:child.end_byte].decode('utf-8'))
                else:
                    # For typed/default parameters, get the identifier
                    for sub in child.children:
                        if sub.type == 'identifier':
                            params.append(content[sub.start_byte:sub.end_byte].decode('utf-8'))
                            break
        return params
    
    def _analyze_usage_patterns(self):
        """Analyze how functions, classes, and imports are used."""
        for file_path in self.functions.keys():
            try:
                with open(self.root_path / file_path, 'rb') as f:
                    content = f.read()
                
                tree = self.parser.parse(content)
                self._analyze_file_usage(tree.root_node, content, file_path)
                
            except Exception as e:
                print(f"Error analyzing usage in {file_path}: {e}")
    
    def _analyze_file_usage(self, root_node, content: bytes, file_path: str):
        """Analyze usage patterns in a file."""
        def traverse(node):
            # Function calls
            if node.type == 'call':
                func_name = self._extract_call_name(node, content)
                if func_name:
                    self.function_calls[func_name].add(file_path)
            
            # Class instantiations
            elif node.type == 'call':
                # Check if it's a class instantiation
                func_node = node.child_by_field_name('function')
                if func_node and func_node.type == 'identifier':
                    name = content[func_node.start_byte:func_node.end_byte].decode('utf-8')
                    # Check if it's a known class
                    for f, classes in self.classes.items():
                        if name in classes:
                            self.class_instantiations[name].add(file_path)
            
            # Attribute access (for methods)
            elif node.type == 'attribute':
                attr_name = self._extract_attribute_name(node, content)
                if attr_name:
                    self.attribute_access[attr_name].add(file_path)
            
            # Check import usage
            elif node.type == 'identifier':
                name = content[node.start_byte:node.end_byte].decode('utf-8')
                for imp in self.imports.get(file_path, []):
                    if imp['type'] == 'import' and name in imp['modules']:
                        self.import_usage[f"{file_path}:{imp['text']}"].add(file_path)
                    elif imp['type'] == 'from_import' and name in imp['names']:
                        self.import_usage[f"{file_path}:{imp['text']}"].add(file_path)
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
    
    def _extract_call_name(self, call_node, content: bytes) -> Optional[str]:
        """Extract the name of a function being called."""
        func_node = call_node.child_by_field_name('function')
        if not func_node:
            return None
            
        if func_node.type == 'identifier':
            return content[func_node.start_byte:func_node.end_byte].decode('utf-8')
        elif func_node.type == 'attribute':
            return self._extract_attribute_name(func_node, content)
        
        return None
    
    def _extract_attribute_name(self, attr_node, content: bytes) -> Optional[str]:
        """Extract full attribute name (e.g., obj.method)."""
        parts = []
        current = attr_node
        
        while current:
            if current.type == 'attribute':
                attr_child = current.child_by_field_name('attribute')
                if attr_child:
                    parts.append(content[attr_child.start_byte:attr_child.end_byte].decode('utf-8'))
                current = current.child_by_field_name('object')
            elif current.type == 'identifier':
                parts.append(content[current.start_byte:current.end_byte].decode('utf-8'))
                break
            else:
                break
        
        return '.'.join(reversed(parts)) if parts else None
    
    def _build_dependency_graphs(self):
        """Build call graphs and import dependencies."""
        # Build import graph
        for file_path, imports in self.imports.items():
            for imp in imports:
                if imp['type'] == 'from_import' and imp['module']:
                    # Convert module to file path
                    if imp['module'].startswith('claude_pm'):
                        module_parts = imp['module'].split('.')
                        potential_file = '/'.join(module_parts) + '.py'
                        if (self.root_path / potential_file).exists():
                            self.import_graph[file_path].add(potential_file)
        
        # Build call graph
        for file_path, functions in self.functions.items():
            for func_name, func_info in functions.items():
                # Analyze function body for calls
                if func_info['body']:
                    tree = self.parser.parse(func_info['body'].encode())
                    self._extract_function_calls(tree.root_node, func_info['body'].encode(), func_name)
    
    def _extract_function_calls(self, node, content: bytes, caller_name: str):
        """Extract function calls from a function body."""
        def traverse(node):
            if node.type == 'call':
                called_func = self._extract_call_name(node, content)
                if called_func:
                    self.call_graph[caller_name].add(called_func)
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
    
    def _find_unused_code(self):
        """Identify unused functions, classes, and imports."""
        # Find unused functions
        for file_path, functions in self.functions.items():
            for func_name, func_info in functions.items():
                # Skip special methods
                if func_name.startswith('__') or func_name.endswith('__'):
                    continue
                if any(func_name.endswith(f'.{m}') for m in ['__init__', '__str__', '__repr__']):
                    continue
                if func_info['decorators'] and any('test' in d for d in func_info['decorators']):
                    continue
                if 'test_' in func_name:
                    continue
                
                # Check if function is called
                simple_name = func_name.split('.')[-1]
                if (func_name not in self.function_calls and 
                    simple_name not in self.function_calls and
                    func_name not in self.attribute_access and
                    f".{simple_name}" not in str(self.attribute_access.keys())):
                    self.unused_functions.add(f"{file_path}:{func_name}")
        
        # Find unused classes
        for file_path, classes in self.classes.items():
            for class_name, class_info in classes.items():
                if class_name not in self.class_instantiations:
                    # Check if it's used as a base class
                    used_as_base = False
                    for _, other_classes in self.classes.items():
                        for _, other_info in other_classes.items():
                            if class_name in other_info['bases']:
                                used_as_base = True
                                break
                    
                    if not used_as_base:
                        self.unused_classes.add(f"{file_path}:{class_name}")
        
        # Find unused imports
        for file_path, imports in self.imports.items():
            for imp in imports:
                import_key = f"{file_path}:{imp['text']}"
                if import_key not in self.import_usage:
                    self.unused_imports.add(import_key)
    
    def _calculate_complexity(self):
        """Calculate cyclomatic complexity for all functions."""
        for file_path, functions in self.functions.items():
            for func_name, func_info in functions.items():
                if func_info['body']:
                    complexity = self._calculate_cyclomatic_complexity(func_info['body'])
                    self.complexity_scores[f"{file_path}:{func_name}"] = complexity
                    
                    if complexity > 10:
                        self.high_complexity_functions.append({
                            'function': f"{file_path}:{func_name}",
                            'complexity': complexity,
                            'lines': func_info['line_end'] - func_info['line_start'] + 1
                        })
    
    def _calculate_cyclomatic_complexity(self, body: str) -> int:
        """Calculate cyclomatic complexity of function body."""
        complexity = 1
        
        # Decision points
        complexity += body.count('if ')
        complexity += body.count('elif ')
        complexity += body.count('else:')
        complexity += body.count('for ')
        complexity += body.count('while ')
        complexity += body.count('except ')
        complexity += body.count(' and ')
        complexity += body.count(' or ')
        
        return complexity
    
    def _find_duplicate_code(self):
        """Find duplicate or very similar code blocks."""
        # Group functions by body hash
        for file_path, functions in self.functions.items():
            for func_name, func_info in functions.items():
                if func_info['body_hash']:
                    self.code_hashes[func_info['body_hash']].append({
                        'file': file_path,
                        'function': func_name,
                        'lines': f"{func_info['line_start']}-{func_info['line_end']}"
                    })
        
        # Find exact duplicates
        for hash_val, locations in self.code_hashes.items():
            if len(locations) > 1:
                self.redundant_code.append({
                    'type': 'exact_duplicate',
                    'locations': locations
                })
        
        # Find similar functions (same parameter count and similar size)
        func_signatures = defaultdict(list)
        for file_path, functions in self.functions.items():
            for func_name, func_info in functions.items():
                sig = (len(func_info['params']), 
                      len(func_info['body']) // 100)  # Size bucket
                func_signatures[sig].append({
                    'file': file_path,
                    'function': func_name,
                    'params': func_info['params']
                })
        
        for sig, funcs in func_signatures.items():
            if len(funcs) > 1:
                self.similar_functions.append({
                    'signature': f"params={sig[0]}, size_bucket={sig[1]}00",
                    'functions': funcs[:10]  # Limit output
                })
    
    def _detect_circular_dependencies(self):
        """Detect circular import dependencies."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.import_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    self.circular_dependencies.append(cycle)
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.import_graph:
            if node not in visited:
                has_cycle(node, [])
    
    def _find_dead_code(self):
        """Find unreachable code blocks."""
        for file_path, functions in self.functions.items():
            for func_name, func_info in functions.items():
                if func_info['body']:
                    # Look for common dead code patterns
                    lines = func_info['body'].split('\n')
                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        
                        # Code after return/raise/continue/break
                        if stripped in ['return', 'raise', 'continue', 'break']:
                            if i < len(lines) - 1:
                                next_line = lines[i + 1].strip()
                                if next_line and not next_line.startswith(('except', 'finally', 'elif', 'else')):
                                    self.dead_code_blocks.append({
                                        'file': file_path,
                                        'function': func_name,
                                        'line': func_info['line_start'] + i + 1,
                                        'reason': f'Code after {stripped}'
                                    })
                        
                        # Always false conditions
                        if 'if False:' in stripped or 'if 0:' in stripped:
                            self.dead_code_blocks.append({
                                'file': file_path,
                                'function': func_name,
                                'line': func_info['line_start'] + i,
                                'reason': 'Always false condition'
                            })
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = ['__pycache__', '.git', 'test_', 'tests/', 'venv/', 'env/']
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        total_functions = sum(len(funcs) for funcs in self.functions.values())
        total_classes = sum(len(classes) for classes in self.classes.values())
        total_imports = sum(len(imports) for imports in self.imports.items())
        
        report = {
            'summary': {
                'files_analyzed': len(self.functions),
                'total_functions': total_functions,
                'total_classes': total_classes,
                'total_imports': total_imports,
                'unused_functions': len(self.unused_functions),
                'unused_classes': len(self.unused_classes),
                'unused_imports': len(self.unused_imports),
                'high_complexity_functions': len(self.high_complexity_functions),
                'duplicate_code_blocks': len(self.redundant_code),
                'circular_dependencies': len(self.circular_dependencies),
                'dead_code_blocks': len(self.dead_code_blocks)
            },
            'unused_code': {
                'functions': sorted(list(self.unused_functions))[:50],  # Top 50
                'classes': sorted(list(self.unused_classes)),
                'imports': sorted(list(self.unused_imports))[:50]  # Top 50
            },
            'complexity_analysis': {
                'high_complexity': sorted(
                    self.high_complexity_functions,
                    key=lambda x: x['complexity'],
                    reverse=True
                )[:20],  # Top 20
                'complexity_distribution': self._get_complexity_distribution()
            },
            'code_duplication': {
                'exact_duplicates': self.redundant_code[:20],  # Top 20
                'similar_functions': self.similar_functions[:10],  # Top 10
                'total_duplicate_functions': sum(
                    len(d['locations']) - 1 for d in self.redundant_code
                )
            },
            'dependencies': {
                'circular_dependencies': [
                    ' -> '.join(cycle) for cycle in self.circular_dependencies
                ],
                'most_imported_files': self._get_most_imported_files(),
                'most_dependent_files': self._get_most_dependent_files()
            },
            'dead_code': {
                'unreachable_blocks': self.dead_code_blocks[:20],  # Top 20
                'total_dead_code_blocks': len(self.dead_code_blocks)
            },
            'optimization_opportunities': self._generate_recommendations()
        }
        
        return report
    
    def _get_complexity_distribution(self) -> Dict[str, int]:
        """Get distribution of complexity scores."""
        distribution = {
            'low (1-5)': 0,
            'medium (6-10)': 0,
            'high (11-20)': 0,
            'very_high (>20)': 0
        }
        
        for score in self.complexity_scores.values():
            if score <= 5:
                distribution['low (1-5)'] += 1
            elif score <= 10:
                distribution['medium (6-10)'] += 1
            elif score <= 20:
                distribution['high (11-20)'] += 1
            else:
                distribution['very_high (>20)'] += 1
        
        return distribution
    
    def _get_most_imported_files(self) -> List[Dict]:
        """Get files that are imported most frequently."""
        import_counts = Counter()
        for imports in self.import_graph.values():
            for imp in imports:
                import_counts[imp] += 1
        
        return [
            {'file': file, 'import_count': count}
            for file, count in import_counts.most_common(10)
        ]
    
    def _get_most_dependent_files(self) -> List[Dict]:
        """Get files with most dependencies."""
        return [
            {'file': file, 'dependency_count': len(deps)}
            for file, deps in sorted(
                self.import_graph.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
        ]
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate specific optimization recommendations."""
        recommendations = []
        
        # Unused code removal
        if self.unused_functions:
            size_estimate = len(self.unused_functions) * 10  # ~10 lines per function
            recommendations.append({
                'category': 'Remove Unused Code',
                'impact': 'high',
                'description': f'Remove {len(self.unused_functions)} unused functions',
                'estimated_line_reduction': size_estimate,
                'examples': list(self.unused_functions)[:5]
            })
        
        # High complexity refactoring
        if self.high_complexity_functions:
            recommendations.append({
                'category': 'Reduce Complexity',
                'impact': 'high',
                'description': f'Refactor {len(self.high_complexity_functions)} high-complexity functions',
                'functions': [f['function'] for f in self.high_complexity_functions[:5]]
            })
        
        # Duplicate code consolidation
        if self.redundant_code:
            recommendations.append({
                'category': 'Consolidate Duplicates',
                'impact': 'medium',
                'description': f'Consolidate {len(self.redundant_code)} duplicate code blocks',
                'examples': self.redundant_code[:3]
            })
        
        # Circular dependency resolution
        if self.circular_dependencies:
            recommendations.append({
                'category': 'Break Circular Dependencies',
                'impact': 'high',
                'description': f'Resolve {len(self.circular_dependencies)} circular import dependencies',
                'cycles': [' -> '.join(c) for c in self.circular_dependencies[:3]]
            })
        
        # Dead code removal
        if self.dead_code_blocks:
            recommendations.append({
                'category': 'Remove Dead Code',
                'impact': 'medium',
                'description': f'Remove {len(self.dead_code_blocks)} unreachable code blocks',
                'examples': self.dead_code_blocks[:5]
            })
        
        # Import cleanup
        if len(self.unused_imports) > 10:
            recommendations.append({
                'category': 'Clean Imports',
                'impact': 'low',
                'description': f'Remove {len(self.unused_imports)} unused imports',
                'examples': list(self.unused_imports)[:10]
            })
        
        return recommendations


def main():
    """Run the semantic optimization analysis."""
    print("🚀 Claude PM Semantic Code Optimization Analysis")
    print("=" * 60)
    
    analyzer = SemanticCodeOptimizer('claude_pm')
    report = analyzer.analyze()
    
    # Save detailed report
    output_path = Path('tests/reports/semantic_optimization_report.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print executive summary
    print("\n📊 EXECUTIVE SUMMARY")
    print("=" * 60)
    
    summary = report['summary']
    print(f"\n📁 Codebase Overview:")
    print(f"  • Files analyzed: {summary['files_analyzed']}")
    print(f"  • Total functions: {summary['total_functions']}")
    print(f"  • Total classes: {summary['total_classes']}")
    
    print(f"\n🗑️ Unused Code Found:")
    print(f"  • Unused functions: {summary['unused_functions']}")
    print(f"  • Unused classes: {summary['unused_classes']}")
    print(f"  • Unused imports: {summary['unused_imports']}")
    
    print(f"\n⚠️ Code Quality Issues:")
    print(f"  • High complexity functions: {summary['high_complexity_functions']}")
    print(f"  • Duplicate code blocks: {summary['duplicate_code_blocks']}")
    print(f"  • Circular dependencies: {summary['circular_dependencies']}")
    print(f"  • Dead code blocks: {summary['dead_code_blocks']}")
    
    print(f"\n🎯 TOP OPTIMIZATION OPPORTUNITIES:")
    for i, rec in enumerate(report['optimization_opportunities'][:5], 1):
        print(f"\n{i}. {rec['category']} (Impact: {rec['impact'].upper()})")
        print(f"   {rec['description']}")
        if 'estimated_line_reduction' in rec:
            print(f"   Estimated line reduction: ~{rec['estimated_line_reduction']} lines")
    
    print(f"\n✅ Full report saved to: {output_path}")
    print("\n💡 Next steps:")
    print("   1. Review unused functions and remove if truly unused")
    print("   2. Refactor high-complexity functions")
    print("   3. Consolidate duplicate code")
    print("   4. Resolve circular dependencies")
    print("   5. Run 'autopep8' or 'black' to clean up imports")


if __name__ == "__main__":
    main()