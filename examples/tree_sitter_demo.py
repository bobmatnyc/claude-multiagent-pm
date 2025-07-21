#!/usr/bin/env python3
"""Demonstration of tree-sitter integration for code analysis."""

from claude_pm.utils.tree_sitter_utils import TreeSitterAnalyzer, analyze_file

def main():
    """Demonstrate tree-sitter capabilities."""
    print("=== Tree-sitter Code Analysis Demo ===\n")
    
    # Initialize analyzer
    analyzer = TreeSitterAnalyzer()
    print(f"Available languages: {list(analyzer.parsers.keys())}\n")
    
    # Example 1: Parse Python code
    python_code = '''
def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    return sum(numbers)

class Calculator:
    def __init__(self):
        self.memory = 0
    
    def add(self, x, y):
        return x + y
    
    def multiply(self, x, y):
        return x * y

import math
from typing import List, Dict
'''
    
    print("=== Python Code Analysis ===")
    tree = analyzer.parse_code(python_code, 'python')
    if tree:
        functions = analyzer.find_functions(tree, 'python')
        classes = analyzer.find_classes(tree, 'python')
        imports = analyzer.get_imports(tree, 'python')
        
        print(f"Functions found: {[f['name'] for f in functions]}")
        print(f"Classes found: {[c['name'] for c in classes]}")
        print(f"Import statements: {len(imports)}")
        print()
    
    # Example 2: Parse JavaScript code
    js_code = '''
function greet(name) {
    console.log(`Hello, ${name}!`);
}

const arrowGreet = (name) => {
    console.log(`Hi, ${name}!`);
};

class Person {
    constructor(name) {
        this.name = name;
    }
    
    sayHello() {
        console.log(`Hello, I'm ${this.name}`);
    }
}

import { readFile } from 'fs';
import express from 'express';
'''
    
    print("=== JavaScript Code Analysis ===")
    tree = analyzer.parse_code(js_code, 'javascript')
    if tree:
        functions = analyzer.find_functions(tree, 'javascript')
        classes = analyzer.find_classes(tree, 'javascript')
        imports = analyzer.get_imports(tree, 'javascript')
        
        print(f"Functions found: {[f.get('name', 'anonymous') for f in functions]}")
        print(f"Classes found: {[c['name'] for c in classes]}")
        print(f"Import statements: {len(imports)}")
        print()
    
    # Example 3: Analyze this file itself
    print("=== Analyzing This Script ===")
    import __file__ as current_file
    result = analyze_file(__file__)
    
    print(f"Language: {result.get('language', 'unknown')}")
    print(f"Functions: {[f['name'] for f in result.get('functions', [])]}")
    print(f"Classes: {[c['name'] for c in result.get('classes', [])]}")
    print(f"Imports: {len(result.get('imports', []))}")


if __name__ == "__main__":
    main()