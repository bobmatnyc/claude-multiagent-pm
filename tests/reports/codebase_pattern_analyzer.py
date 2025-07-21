#!/usr/bin/env python3
"""Pattern-based codebase analyzer for Python vs TypeScript evaluation."""

import os
import json
import re
import ast
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set

class PatternAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.results = {
            "async_patterns": {
                "async_functions": 0,
                "await_expressions": 0,
                "async_with": 0,
                "async_for": 0,
                "files_with_async": []
            },
            "type_hints": {
                "annotated_functions": 0,
                "total_functions": 0,
                "annotated_parameters": 0,
                "total_parameters": 0,
                "complex_types": Counter(),
                "type_patterns": Counter()
            },
            "subprocess_patterns": {
                "subprocess_run": 0,
                "subprocess_popen": 0,
                "os_system": 0,
                "asyncio_subprocess": 0,
                "files_with_subprocess": []
            },
            "io_operations": {
                "file_open": 0,
                "path_operations": 0,
                "json_operations": 0,
                "yaml_operations": 0,
                "files_with_heavy_io": []
            },
            "class_patterns": {
                "total_classes": 0,
                "abc_classes": 0,
                "dataclasses": 0,
                "metaclasses": 0,
                "decorators": Counter()
            },
            "dependencies": {
                "imports": Counter(),
                "ai_ml_libs": set(),
                "async_libs": set(),
                "system_libs": set(),
                "web_frameworks": set()
            },
            "concurrency": {
                "threading": 0,
                "multiprocessing": 0,
                "asyncio": 0,
                "concurrent_futures": 0
            },
            "metaprogramming": {
                "getattr_setattr": 0,
                "exec_eval": 0,
                "importlib": 0,
                "monkey_patching": 0
            },
            "code_metrics": {
                "total_lines": 0,
                "total_files": 0,
                "avg_file_size": 0,
                "large_files": []
            }
        }
        
        # Known library categories
        self.ai_ml_libs = {"openai", "anthropic", "mirascope", "langchain", "transformers", "torch", "tensorflow", "numpy", "pandas", "sklearn"}
        self.async_libs = {"asyncio", "aiohttp", "aiofiles", "trio", "anyio", "httpx"}
        self.system_libs = {"os", "sys", "subprocess", "pathlib", "shutil", "platform", "psutil"}
        self.web_frameworks = {"flask", "fastapi", "django", "aiohttp", "sanic", "starlette"}
        
    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file using AST and pattern matching."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Update metrics
            lines = len(content.splitlines())
            self.results["code_metrics"]["total_lines"] += lines
            self.results["code_metrics"]["total_files"] += 1
            
            if lines > 1000:
                self.results["code_metrics"]["large_files"].append({
                    "file": str(file_path.relative_to(self.root_path)),
                    "lines": lines
                })
            
            # Parse AST
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, file_path)
            except SyntaxError:
                print(f"Syntax error in {file_path}")
                
            # Pattern-based analysis
            self._analyze_patterns(content, file_path)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            
    def _analyze_ast(self, tree: ast.AST, file_path: Path) -> None:
        """Analyze AST for structural patterns."""
        relative_path = str(file_path.relative_to(self.root_path))
        has_async = False
        
        for node in ast.walk(tree):
            # Async patterns
            if isinstance(node, ast.AsyncFunctionDef):
                self.results["async_patterns"]["async_functions"] += 1
                has_async = True
            elif isinstance(node, ast.Await):
                self.results["async_patterns"]["await_expressions"] += 1
                has_async = True
            elif isinstance(node, ast.AsyncWith):
                self.results["async_patterns"]["async_with"] += 1
                has_async = True
            elif isinstance(node, ast.AsyncFor):
                self.results["async_patterns"]["async_for"] += 1
                has_async = True
                
            # Function analysis
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.results["type_hints"]["total_functions"] += 1
                if node.returns:
                    self.results["type_hints"]["annotated_functions"] += 1
                    
                # Count parameters
                for arg in node.args.args:
                    self.results["type_hints"]["total_parameters"] += 1
                    if arg.annotation:
                        self.results["type_hints"]["annotated_parameters"] += 1
                        
            # Class analysis
            elif isinstance(node, ast.ClassDef):
                self.results["class_patterns"]["total_classes"] += 1
                
                # Check decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        self.results["class_patterns"]["decorators"][decorator.id] += 1
                    elif isinstance(decorator, ast.Attribute):
                        self.results["class_patterns"]["decorators"][decorator.attr] += 1
                        
            # Import analysis
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    self._categorize_import(module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    self._categorize_import(module)
                    
        if has_async:
            self.results["async_patterns"]["files_with_async"].append(relative_path)
            
    def _analyze_patterns(self, content: str, file_path: Path) -> None:
        """Analyze code patterns using regex."""
        relative_path = str(file_path.relative_to(self.root_path))
        
        # Subprocess patterns
        subprocess_patterns = [
            (r'subprocess\.run\s*\(', 'subprocess_run'),
            (r'subprocess\.Popen\s*\(', 'subprocess_popen'),
            (r'os\.system\s*\(', 'os_system'),
            (r'asyncio\.create_subprocess', 'asyncio_subprocess')
        ]
        
        subprocess_found = False
        for pattern, key in subprocess_patterns:
            matches = len(re.findall(pattern, content))
            if matches > 0:
                self.results["subprocess_patterns"][key] += matches
                subprocess_found = True
                
        if subprocess_found:
            self.results["subprocess_patterns"]["files_with_subprocess"].append(relative_path)
            
        # I/O operations
        io_patterns = [
            (r'open\s*\(', 'file_open'),
            (r'Path\s*\(|os\.path', 'path_operations'),
            (r'json\.dump|json\.load|json\.dumps|json\.loads', 'json_operations'),
            (r'yaml\.dump|yaml\.load|yaml\.safe_load', 'yaml_operations')
        ]
        
        heavy_io = False
        for pattern, key in io_patterns:
            matches = len(re.findall(pattern, content))
            if matches > 0:
                self.results["io_operations"][key] += matches
                if matches > 5:
                    heavy_io = True
                    
        if heavy_io:
            self.results["io_operations"]["files_with_heavy_io"].append(relative_path)
            
        # Type hint patterns
        type_patterns = [
            (r'List\[', 'List'),
            (r'Dict\[', 'Dict'),
            (r'Optional\[', 'Optional'),
            (r'Union\[', 'Union'),
            (r'Tuple\[', 'Tuple'),
            (r'Callable\[', 'Callable'),
            (r'TypeVar\(', 'TypeVar'),
            (r'Generic\[', 'Generic')
        ]
        
        for pattern, type_name in type_patterns:
            matches = len(re.findall(pattern, content))
            if matches > 0:
                self.results["type_hints"]["type_patterns"][type_name] += matches
                
        # Concurrency patterns
        if 'threading' in content:
            self.results["concurrency"]["threading"] += 1
        if 'multiprocessing' in content:
            self.results["concurrency"]["multiprocessing"] += 1
        if 'asyncio' in content:
            self.results["concurrency"]["asyncio"] += 1
        if 'concurrent.futures' in content:
            self.results["concurrency"]["concurrent_futures"] += 1
            
        # Metaprogramming patterns
        metaprog_patterns = [
            (r'getattr\s*\(|setattr\s*\(', 'getattr_setattr'),
            (r'exec\s*\(|eval\s*\(', 'exec_eval'),
            (r'importlib\.import_module|__import__', 'importlib'),
            (r'\.__dict__\[|\.__class__', 'monkey_patching')
        ]
        
        for pattern, key in metaprog_patterns:
            matches = len(re.findall(pattern, content))
            if matches > 0:
                self.results["metaprogramming"][key] += matches
                
        # Special patterns
        if '@dataclass' in content:
            self.results["class_patterns"]["dataclasses"] += content.count('@dataclass')
        if 'ABC' in content or 'abstractmethod' in content:
            self.results["class_patterns"]["abc_classes"] += 1
        if 'metaclass=' in content:
            self.results["class_patterns"]["metaclasses"] += content.count('metaclass=')
            
    def _categorize_import(self, module: str) -> None:
        """Categorize imports by type."""
        self.results["dependencies"]["imports"][module] += 1
        
        if module in self.ai_ml_libs:
            self.results["dependencies"]["ai_ml_libs"].add(module)
        elif module in self.async_libs:
            self.results["dependencies"]["async_libs"].add(module)
        elif module in self.system_libs:
            self.results["dependencies"]["system_libs"].add(module)
        elif module in self.web_frameworks:
            self.results["dependencies"]["web_frameworks"].add(module)
            
    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the entire codebase."""
        py_files = []
        for root, dirs, files in os.walk(self.root_path / "claude_pm"):
            # Skip __pycache__ directories
            if '__pycache__' in root:
                continue
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    py_files.append(Path(root) / file)
                    
        print(f"\nAnalyzing {len(py_files)} Python files...")
        
        for i, file_path in enumerate(py_files):
            if (i + 1) % 50 == 0:
                print(f"Progress: {i + 1}/{len(py_files)} files analyzed")
            self.analyze_file(file_path)
            
        # Convert sets to lists and calculate summaries
        self._finalize_results()
        
        return self.results
        
    def _finalize_results(self) -> None:
        """Finalize results for output."""
        # Convert sets to lists
        self.results["dependencies"]["ai_ml_libs"] = list(self.results["dependencies"]["ai_ml_libs"])
        self.results["dependencies"]["async_libs"] = list(self.results["dependencies"]["async_libs"])
        self.results["dependencies"]["system_libs"] = list(self.results["dependencies"]["system_libs"])
        self.results["dependencies"]["web_frameworks"] = list(self.results["dependencies"]["web_frameworks"])
        
        # Convert Counters to dicts (top items only)
        self.results["dependencies"]["imports"] = dict(self.results["dependencies"]["imports"].most_common(50))
        self.results["type_hints"]["type_patterns"] = dict(self.results["type_hints"]["type_patterns"])
        self.results["class_patterns"]["decorators"] = dict(self.results["class_patterns"]["decorators"])
        
        # Calculate summaries
        total_files = self.results["code_metrics"]["total_files"]
        if total_files > 0:
            self.results["code_metrics"]["avg_file_size"] = self.results["code_metrics"]["total_lines"] / total_files
            
        # Type hint coverage
        total_funcs = self.results["type_hints"]["total_functions"]
        if total_funcs > 0:
            self.results["type_hints"]["function_coverage"] = (
                self.results["type_hints"]["annotated_functions"] / total_funcs * 100
            )
            
        total_params = self.results["type_hints"]["total_parameters"]
        if total_params > 0:
            self.results["type_hints"]["parameter_coverage"] = (
                self.results["type_hints"]["annotated_parameters"] / total_params * 100
            )
            
        # Async usage
        self.results["async_patterns"]["async_file_percentage"] = (
            len(self.results["async_patterns"]["files_with_async"]) / total_files * 100
            if total_files > 0 else 0
        )
        
        # Create summary
        self.results["summary"] = {
            "total_files": total_files,
            "total_lines": self.results["code_metrics"]["total_lines"],
            "avg_file_size": round(self.results["code_metrics"]["avg_file_size"], 1),
            "async_usage": {
                "files_with_async": len(self.results["async_patterns"]["files_with_async"]),
                "percentage": round(self.results["async_patterns"]["async_file_percentage"], 1),
                "total_async_constructs": sum([
                    self.results["async_patterns"]["async_functions"],
                    self.results["async_patterns"]["await_expressions"],
                    self.results["async_patterns"]["async_with"],
                    self.results["async_patterns"]["async_for"]
                ])
            },
            "type_hints": {
                "function_coverage": round(self.results["type_hints"].get("function_coverage", 0), 1),
                "parameter_coverage": round(self.results["type_hints"].get("parameter_coverage", 0), 1),
                "uses_complex_types": len(self.results["type_hints"]["type_patterns"]) > 0
            },
            "dependencies": {
                "ai_ml_count": len(self.results["dependencies"]["ai_ml_libs"]),
                "async_libs_count": len(self.results["dependencies"]["async_libs"]),
                "total_unique_imports": len(self.results["dependencies"]["imports"])
            },
            "subprocess_usage": {
                "files_count": len(self.results["subprocess_patterns"]["files_with_subprocess"]),
                "total_calls": sum([
                    self.results["subprocess_patterns"]["subprocess_run"],
                    self.results["subprocess_patterns"]["subprocess_popen"],
                    self.results["subprocess_patterns"]["os_system"],
                    self.results["subprocess_patterns"]["asyncio_subprocess"]
                ])
            },
            "architecture": {
                "total_classes": self.results["class_patterns"]["total_classes"],
                "uses_abc": self.results["class_patterns"]["abc_classes"] > 0,
                "uses_dataclasses": self.results["class_patterns"]["dataclasses"] > 0,
                "uses_metaclasses": self.results["class_patterns"]["metaclasses"] > 0
            }
        }

def main():
    """Run the analysis."""
    analyzer = PatternAnalyzer("/Users/masa/Projects/claude-multiagent-pm")
    results = analyzer.analyze_codebase()
    
    # Save results
    output_path = Path("/Users/masa/Projects/claude-multiagent-pm/tests/reports/python_codebase_analysis.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\n✅ Analysis complete! Results saved to {output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("CODEBASE ANALYSIS SUMMARY")
    print("="*60)
    
    summary = results["summary"]
    print(f"\n📊 Code Metrics:")
    print(f"  - Total files: {summary['total_files']}")
    print(f"  - Total lines: {summary['total_lines']:,}")
    print(f"  - Average file size: {summary['avg_file_size']} lines")
    
    print(f"\n⚡ Async Usage:")
    print(f"  - Files with async: {summary['async_usage']['files_with_async']} ({summary['async_usage']['percentage']}%)")
    print(f"  - Total async constructs: {summary['async_usage']['total_async_constructs']}")
    
    print(f"\n📝 Type Hints:")
    print(f"  - Function coverage: {summary['type_hints']['function_coverage']}%")
    print(f"  - Parameter coverage: {summary['type_hints']['parameter_coverage']}%")
    print(f"  - Uses complex types: {summary['type_hints']['uses_complex_types']}")
    
    print(f"\n📦 Dependencies:")
    print(f"  - AI/ML libraries: {summary['dependencies']['ai_ml_count']}")
    print(f"  - Async libraries: {summary['dependencies']['async_libs_count']}")
    print(f"  - Total unique imports: {summary['dependencies']['total_unique_imports']}")
    
    print(f"\n🔧 Subprocess Usage:")
    print(f"  - Files with subprocess: {summary['subprocess_usage']['files_count']}")
    print(f"  - Total subprocess calls: {summary['subprocess_usage']['total_calls']}")
    
    print(f"\n🏗️ Architecture:")
    print(f"  - Total classes: {summary['architecture']['total_classes']}")
    print(f"  - Uses ABC: {summary['architecture']['uses_abc']}")
    print(f"  - Uses dataclasses: {summary['architecture']['uses_dataclasses']}")
    print(f"  - Uses metaclasses: {summary['architecture']['uses_metaclasses']}")

if __name__ == "__main__":
    main()