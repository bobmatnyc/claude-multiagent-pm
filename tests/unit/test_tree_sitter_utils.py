"""Test tree-sitter utilities for code analysis."""

import pytest
from pathlib import Path
from claude_pm.utils.tree_sitter_utils import (
    TreeSitterAnalyzer,
    analyze_file,
    analyze_directory
)


class TestTreeSitterAnalyzer:
    """Test the TreeSitterAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes with supported languages."""
        analyzer = TreeSitterAnalyzer()
        
        # Check that parsers are initialized
        assert hasattr(analyzer, 'parsers')
        assert isinstance(analyzer.parsers, dict)
        
        # Check supported languages
        expected_languages = ['python', 'javascript', 'typescript']
        for lang in expected_languages:
            assert lang in analyzer.parsers
    
    def test_parse_python_code(self):
        """Test parsing Python code."""
        analyzer = TreeSitterAnalyzer()
        
        code = '''
def hello_world():
    """Say hello."""
    print("Hello, World!")

class Greeter:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        print(f"Hello, {self.name}!")
'''
        
        tree = analyzer.parse_code(code, 'python')
        assert tree is not None
        assert tree.root_node is not None
    
    def test_find_python_functions(self):
        """Test finding functions in Python code."""
        analyzer = TreeSitterAnalyzer()
        
        code = '''
def function_one():
    pass

def function_two(arg1, arg2):
    return arg1 + arg2

async def async_function():
    pass
'''
        
        tree = analyzer.parse_code(code, 'python')
        functions = analyzer.find_functions(tree, 'python')
        
        assert len(functions) == 3
        function_names = [f['name'] for f in functions]
        assert 'function_one' in function_names
        assert 'function_two' in function_names
        assert 'async_function' in function_names
    
    def test_find_python_classes(self):
        """Test finding classes in Python code."""
        analyzer = TreeSitterAnalyzer()
        
        code = '''
class ClassOne:
    pass

class ClassTwo(BaseClass):
    def method(self):
        pass
'''
        
        tree = analyzer.parse_code(code, 'python')
        classes = analyzer.find_classes(tree, 'python')
        
        assert len(classes) == 2
        class_names = [c['name'] for c in classes]
        assert 'ClassOne' in class_names
        assert 'ClassTwo' in class_names
    
    def test_get_python_imports(self):
        """Test extracting imports from Python code."""
        analyzer = TreeSitterAnalyzer()
        
        code = '''
import os
import sys
from pathlib import Path
from typing import List, Dict
from claude_pm.utils import TreeSitterAnalyzer
'''
        
        tree = analyzer.parse_code(code, 'python')
        imports = analyzer.get_imports(tree, 'python')
        
        assert len(imports) == 5
        import_texts = [imp['text'] for imp in imports]
        assert 'import os' in import_texts
        assert 'from pathlib import Path' in import_texts
    
    def test_parse_javascript_code(self):
        """Test parsing JavaScript code."""
        analyzer = TreeSitterAnalyzer()
        
        code = '''
function helloWorld() {
    console.log("Hello, World!");
}

const arrowFunc = (x, y) => x + y;

class MyClass {
    constructor(name) {
        this.name = name;
    }
}
'''
        
        tree = analyzer.parse_code(code, 'javascript')
        assert tree is not None
        
        functions = analyzer.find_functions(tree, 'javascript')
        assert len(functions) >= 1  # At least helloWorld
        
        classes = analyzer.find_classes(tree, 'javascript')
        assert len(classes) == 1
        assert classes[0]['name'] == 'MyClass'
    
    def test_analyze_file_wrapper(self, tmp_path):
        """Test the analyze_file convenience function."""
        # Create a temporary Python file
        test_file = tmp_path / "test_module.py"
        test_file.write_text('''
def test_function():
    """Test function."""
    pass

class TestClass:
    """Test class."""
    pass

import os
from pathlib import Path
''')
        
        result = analyze_file(test_file)
        
        assert 'file' in result
        assert 'language' in result
        assert 'functions' in result
        assert 'classes' in result
        assert 'imports' in result
        
        assert result['language'] == 'python'
        assert len(result['functions']) == 1
        assert len(result['classes']) == 1
        assert len(result['imports']) == 2
    
    def test_analyze_directory_wrapper(self, tmp_path):
        """Test the analyze_directory convenience function."""
        # Create test files
        (tmp_path / "module1.py").write_text('def func1(): pass')
        (tmp_path / "module2.py").write_text('class Class1: pass')
        (tmp_path / "script.js").write_text('function jsFunc() {}')
        (tmp_path / "ignore.txt").write_text('This should be ignored')
        
        results = analyze_directory(tmp_path)
        
        assert len(results) == 3  # Only .py and .js files
        
        # Check that all files were analyzed
        analyzed_files = [Path(r['file']).name for r in results]
        assert 'module1.py' in analyzed_files
        assert 'module2.py' in analyzed_files
        assert 'script.js' in analyzed_files
        assert 'ignore.txt' not in analyzed_files
    
    def test_unsupported_language(self):
        """Test handling of unsupported language."""
        analyzer = TreeSitterAnalyzer()
        
        tree = analyzer.parse_code("some code", "unsupported_lang")
        assert tree is None
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        analyzer = TreeSitterAnalyzer()
        
        tree = analyzer.parse_file("/path/to/nonexistent/file.py")
        assert tree is None