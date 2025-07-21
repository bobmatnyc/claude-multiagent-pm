"""Tree-sitter utilities for code analysis in Research Agent.

This module provides helper functions for parsing and analyzing code
using tree-sitter, supporting multiple languages like Python, JavaScript,
and TypeScript.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import tree_sitter
from tree_sitter import Language, Parser, Node, Tree

# Language modules
try:
    # Try individual language modules first
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    INDIVIDUAL_MODULES = True
except ImportError:
    # Fall back to language pack
    try:
        import tree_sitter_language_pack
        INDIVIDUAL_MODULES = False
    except ImportError as e:
        print(f"Warning: Neither individual tree-sitter language modules nor language pack available: {e}")
        INDIVIDUAL_MODULES = None


class TreeSitterAnalyzer:
    """Analyzer for parsing code using tree-sitter."""
    
    def __init__(self):
        """Initialize the analyzer with supported languages."""
        self.parsers: Dict[str, Parser] = {}
        self._initialize_languages()
    
    def _initialize_languages(self):
        """Initialize parsers for supported languages."""
        if INDIVIDUAL_MODULES is None:
            print("Warning: No tree-sitter language modules available")
            return
        
        if INDIVIDUAL_MODULES:
            # Use individual language modules
            # Python
            try:
                py_language = Language(tree_sitter_python.language())
                py_parser = Parser(py_language)
                self.parsers['python'] = py_parser
                self.parsers['py'] = py_parser  # Alias
            except Exception as e:
                print(f"Failed to initialize Python parser: {e}")
            
            # JavaScript
            try:
                js_language = Language(tree_sitter_javascript.language())
                js_parser = Parser(js_language)
                self.parsers['javascript'] = js_parser
                self.parsers['js'] = js_parser  # Alias
            except Exception as e:
                print(f"Failed to initialize JavaScript parser: {e}")
            
            # TypeScript
            try:
                ts_language = Language(tree_sitter_typescript.language())
                ts_parser = Parser(ts_language)
                self.parsers['typescript'] = ts_parser
                self.parsers['ts'] = ts_parser  # Alias
            except Exception as e:
                print(f"Failed to initialize TypeScript parser: {e}")
        else:
            # Use language pack
            # Python
            try:
                py_language = tree_sitter_language_pack.get_language('python')
                py_parser = Parser(py_language)
                self.parsers['python'] = py_parser
                self.parsers['py'] = py_parser  # Alias
            except Exception as e:
                print(f"Failed to initialize Python parser from language pack: {e}")
            
            # JavaScript
            try:
                js_language = tree_sitter_language_pack.get_language('javascript')
                js_parser = Parser(js_language)
                self.parsers['javascript'] = js_parser
                self.parsers['js'] = js_parser  # Alias
            except Exception as e:
                print(f"Failed to initialize JavaScript parser from language pack: {e}")
            
            # TypeScript
            try:
                ts_language = tree_sitter_language_pack.get_language('typescript')
                ts_parser = Parser(ts_language)
                self.parsers['typescript'] = ts_parser
                self.parsers['ts'] = ts_parser  # Alias
            except Exception as e:
                print(f"Failed to initialize TypeScript parser from language pack: {e}")
    
    def parse_file(self, file_path: Union[str, Path]) -> Optional[Tree]:
        """Parse a file and return the syntax tree.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Tree object if successful, None otherwise
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return None
        
        # Determine language from file extension
        ext = file_path.suffix.lstrip('.')
        language = self._get_language_from_extension(ext)
        
        if language not in self.parsers:
            print(f"Unsupported language: {language}")
            return None
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
        
        # Parse the content
        parser = self.parsers[language]
        return parser.parse(content)
    
    def parse_code(self, code: str, language: str) -> Optional[Tree]:
        """Parse code string and return the syntax tree.
        
        Args:
            code: Code string to parse
            language: Language identifier (python, javascript, typescript)
            
        Returns:
            Tree object if successful, None otherwise
        """
        if language not in self.parsers:
            print(f"Unsupported language: {language}")
            return None
        
        parser = self.parsers[language]
        return parser.parse(bytes(code, 'utf-8'))
    
    def _get_language_from_extension(self, ext: str) -> str:
        """Map file extension to language identifier."""
        extension_map = {
            'py': 'python',
            'js': 'javascript', 
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
        }
        return extension_map.get(ext, ext)
    
    def find_functions(self, tree: Tree, language: str) -> List[Dict[str, Any]]:
        """Find all function definitions in the syntax tree.
        
        Args:
            tree: Parsed syntax tree
            language: Language identifier
            
        Returns:
            List of function information dictionaries
        """
        functions = []
        
        # Language-specific function node types
        function_types = {
            'python': ['function_definition', 'async_function_definition'],
            'javascript': ['function_declaration', 'function_expression', 'arrow_function'],
            'typescript': ['function_declaration', 'function_expression', 'arrow_function'],
        }
        
        node_types = function_types.get(language, [])
        if not node_types:
            return functions
        
        # Traverse the tree
        def traverse(node: Node):
            if node.type in node_types:
                func_info = self._extract_function_info(node, language)
                if func_info:
                    functions.append(func_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return functions
    
    def _extract_function_info(self, node: Node, language: str) -> Optional[Dict[str, Any]]:
        """Extract function information from a node."""
        info = {
            'type': node.type,
            'start_point': node.start_point,
            'end_point': node.end_point,
        }
        
        # Extract function name based on language
        if language == 'python':
            name_node = node.child_by_field_name('name')
            if name_node:
                info['name'] = name_node.text.decode('utf-8')
        elif language in ['javascript', 'typescript']:
            name_node = node.child_by_field_name('name')
            if name_node:
                info['name'] = name_node.text.decode('utf-8')
            else:
                # For arrow functions, try to get the variable name
                parent = node.parent
                if parent and parent.type == 'variable_declarator':
                    name_node = parent.child_by_field_name('name')
                    if name_node:
                        info['name'] = name_node.text.decode('utf-8')
        
        return info if 'name' in info else None
    
    def find_classes(self, tree: Tree, language: str) -> List[Dict[str, Any]]:
        """Find all class definitions in the syntax tree.
        
        Args:
            tree: Parsed syntax tree
            language: Language identifier
            
        Returns:
            List of class information dictionaries
        """
        classes = []
        
        # Language-specific class node types
        class_types = {
            'python': ['class_definition'],
            'javascript': ['class_declaration'],
            'typescript': ['class_declaration'],
        }
        
        node_types = class_types.get(language, [])
        if not node_types:
            return classes
        
        # Traverse the tree
        def traverse(node: Node):
            if node.type in node_types:
                class_info = self._extract_class_info(node, language)
                if class_info:
                    classes.append(class_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return classes
    
    def _extract_class_info(self, node: Node, language: str) -> Optional[Dict[str, Any]]:
        """Extract class information from a node."""
        info = {
            'type': node.type,
            'start_point': node.start_point,
            'end_point': node.end_point,
        }
        
        # Extract class name
        name_node = node.child_by_field_name('name')
        if name_node:
            info['name'] = name_node.text.decode('utf-8')
        
        return info if 'name' in info else None
    
    def get_imports(self, tree: Tree, language: str) -> List[Dict[str, Any]]:
        """Extract import statements from the syntax tree.
        
        Args:
            tree: Parsed syntax tree
            language: Language identifier
            
        Returns:
            List of import information dictionaries
        """
        imports = []
        
        # Language-specific import node types
        import_types = {
            'python': ['import_statement', 'import_from_statement'],
            'javascript': ['import_statement'],
            'typescript': ['import_statement'],
        }
        
        node_types = import_types.get(language, [])
        if not node_types:
            return imports
        
        # Traverse the tree
        def traverse(node: Node):
            if node.type in node_types:
                import_info = {
                    'type': node.type,
                    'text': node.text.decode('utf-8'),
                    'start_point': node.start_point,
                    'end_point': node.end_point,
                }
                imports.append(import_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return imports


# Convenience functions
def analyze_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Analyze a single file and return structured information.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    analyzer = TreeSitterAnalyzer()
    file_path = Path(file_path)
    
    tree = analyzer.parse_file(file_path)
    if not tree:
        return {'error': f'Failed to parse {file_path}'}
    
    ext = file_path.suffix.lstrip('.')
    language = analyzer._get_language_from_extension(ext)
    
    return {
        'file': str(file_path),
        'language': language,
        'functions': analyzer.find_functions(tree, language),
        'classes': analyzer.find_classes(tree, language),
        'imports': analyzer.get_imports(tree, language),
    }


def analyze_directory(directory: Union[str, Path], extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Analyze all files in a directory.
    
    Args:
        directory: Directory path to analyze
        extensions: List of file extensions to include (default: py, js, ts)
        
    Returns:
        List of analysis results for each file
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []
    
    if extensions is None:
        extensions = ['.py', '.js', '.jsx', '.ts', '.tsx']
    
    results = []
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix in extensions:
            result = analyze_file(file_path)
            if 'error' not in result:
                results.append(result)
    
    return results