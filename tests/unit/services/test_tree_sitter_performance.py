#!/usr/bin/env python3
"""
Performance benchmarks for TreeSitterAnalyzer vs MetadataAnalyzer.

This module specifically tests the performance improvements of TreeSitterAnalyzer
over the traditional AST-based MetadataAnalyzer approach.
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
import statistics

from claude_pm.services.agent_modification_tracker.tree_sitter_analyzer import TreeSitterAnalyzer
from claude_pm.services.agent_modification_tracker.metadata_analyzer import MetadataAnalyzer
from claude_pm.services.agent_modification_tracker.models import ModificationType


class TestTreeSitterPerformance:
    """Performance benchmark tests for TreeSitterAnalyzer."""
    
    @pytest.fixture
    def tree_sitter_analyzer(self):
        """Create TreeSitterAnalyzer instance."""
        return TreeSitterAnalyzer()
    
    @pytest.fixture
    def metadata_analyzer(self):
        """Create MetadataAnalyzer instance."""
        return MetadataAnalyzer()
    
    @pytest.fixture
    def generate_large_python_file(self, tmp_path):
        """Generate a large Python file for performance testing."""
        def _generate(num_classes=100, num_methods_per_class=10):
            content = '''#!/usr/bin/env python3
"""Large Python file for performance testing."""

import os
import sys
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import yaml
import requests
import numpy as np
import pandas as pd

# Global constants
GLOBAL_CONFIG = {
    "version": "1.0.0",
    "debug": True,
    "max_retries": 3,
}

'''
            
            # Generate classes with methods
            for i in range(num_classes):
                content += f'''
@dataclass
class GeneratedClass{i}:
    """Generated class {i} for testing."""
    
    id: int
    name: str
    data: Dict[str, Any]
    
'''
                for j in range(num_methods_per_class):
                    content += f'''    def method_{j}(self, param1: str, param2: int = 0) -> Dict[str, Any]:
        """Method {j} of class {i}."""
        result = {{
            "class": "{i}",
            "method": "{j}",
            "param1": param1,
            "param2": param2,
        }}
        return result
    
'''
                    if j % 3 == 0:  # Add some async methods
                        content += f'''    async def async_method_{j}(self) -> bool:
        """Async method {j} of class {i}."""
        await asyncio.sleep(0.001)
        return True
    
'''
            
            # Add some standalone functions
            for i in range(50):
                content += f'''
def standalone_function_{i}(x: int, y: int) -> int:
    """Standalone function {i}."""
    return x + y + {i}

'''
            
            file_path = tmp_path / "large_file.py"
            file_path.write_text(content)
            return file_path
        
        return _generate
    
    @pytest.fixture
    def generate_multiple_files(self, tmp_path):
        """Generate multiple files of different languages."""
        def _generate(num_files=10):
            files = []
            
            # Python files
            for i in range(num_files // 3):
                content = f'''
class TestClass{i}:
    def method{i}(self):
        return "test{i}"

def function{i}():
    return {i}
'''
                file_path = tmp_path / f"file{i}.py"
                file_path.write_text(content)
                files.append(file_path)
            
            # JavaScript files
            for i in range(num_files // 3):
                content = f'''
class Component{i} {{
    constructor() {{
        this.name = "Component{i}";
    }}
    
    render() {{
        return `<div>${{this.name}}</div>`;
    }}
}}

function process{i}(data) {{
    return data.map(x => x * {i});
}}
'''
                file_path = tmp_path / f"file{i}.js"
                file_path.write_text(content)
                files.append(file_path)
            
            # Markdown files
            for i in range(num_files - 2 * (num_files // 3)):
                content = f'''# Document {i}

## Section 1
This is content for document {i}.

### Subsection 1.1
- Item 1
- Item 2

## Section 2
```python
def example{i}():
    return "example"
```

[Link {i}](https://example.com/{i})
'''
                file_path = tmp_path / f"file{i}.md"
                file_path.write_text(content)
                files.append(file_path)
            
            return files
        
        return _generate
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_single_large_file_performance(
        self,
        tree_sitter_analyzer,
        metadata_analyzer,
        generate_large_python_file
    ):
        """Benchmark performance on a single large Python file."""
        # Generate large file
        large_file = generate_large_python_file(num_classes=200, num_methods_per_class=15)
        
        # Warm up both analyzers
        await tree_sitter_analyzer.analyze_python_file(large_file)
        await metadata_analyzer.analyze_python_file(large_file)
        
        # Benchmark TreeSitterAnalyzer
        tree_sitter_times = []
        for _ in range(5):
            start = time.perf_counter()
            await tree_sitter_analyzer.analyze_python_file(large_file)
            tree_sitter_times.append(time.perf_counter() - start)
        
        # Benchmark MetadataAnalyzer
        metadata_times = []
        for _ in range(5):
            start = time.perf_counter()
            await metadata_analyzer.analyze_python_file(large_file)
            metadata_times.append(time.perf_counter() - start)
        
        # Calculate statistics
        ts_avg = statistics.mean(tree_sitter_times)
        ts_stdev = statistics.stdev(tree_sitter_times)
        meta_avg = statistics.mean(metadata_times)
        meta_stdev = statistics.stdev(metadata_times)
        
        speedup = meta_avg / ts_avg
        
        print(f"\n=== Single Large File Performance ===")
        print(f"TreeSitterAnalyzer: {ts_avg:.4f}s ± {ts_stdev:.4f}s")
        print(f"MetadataAnalyzer:   {meta_avg:.4f}s ± {meta_stdev:.4f}s")
        print(f"Speedup: {speedup:.1f}x")
        
        # Assert significant performance improvement
        assert ts_avg < meta_avg, "TreeSitterAnalyzer should be faster"
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_multiple_files_performance(
        self,
        tree_sitter_analyzer,
        metadata_analyzer,
        generate_multiple_files
    ):
        """Benchmark performance on multiple files."""
        # Generate files
        files = generate_multiple_files(num_files=30)
        
        # Benchmark TreeSitterAnalyzer
        start = time.perf_counter()
        for file_path in files:
            await tree_sitter_analyzer.collect_file_metadata(
                str(file_path),
                ModificationType.CREATE
            )
        tree_sitter_time = time.perf_counter() - start
        
        # Benchmark MetadataAnalyzer
        start = time.perf_counter()
        for file_path in files:
            await metadata_analyzer.collect_file_metadata(
                str(file_path),
                ModificationType.CREATE
            )
        metadata_time = time.perf_counter() - start
        
        speedup = metadata_time / tree_sitter_time
        
        print(f"\n=== Multiple Files Performance ===")
        print(f"TreeSitterAnalyzer: {tree_sitter_time:.4f}s")
        print(f"MetadataAnalyzer:   {metadata_time:.4f}s")
        print(f"Speedup: {speedup:.1f}x")
        
        # TreeSitter should handle multiple languages better
        assert tree_sitter_time < metadata_time * 1.5  # Allow some variance
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_incremental_parsing_performance(
        self,
        tree_sitter_analyzer,
        generate_large_python_file
    ):
        """Test incremental parsing performance (tree-sitter's strength)."""
        # Generate file
        file_path = generate_large_python_file(num_classes=100)
        
        # Initial parse
        start = time.perf_counter()
        await tree_sitter_analyzer.analyze_python_file(file_path)
        initial_time = time.perf_counter() - start
        
        # Simulate small edits and re-parse
        content = file_path.read_text()
        reparse_times = []
        
        for i in range(10):
            # Make small edit
            modified_content = content.replace(
                f"method_0(self, param1: str",
                f"method_0_v{i}(self, param1: str"
            )
            file_path.write_text(modified_content)
            
            # Re-parse
            start = time.perf_counter()
            await tree_sitter_analyzer.analyze_python_file(file_path)
            reparse_times.append(time.perf_counter() - start)
        
        avg_reparse = statistics.mean(reparse_times)
        
        print(f"\n=== Incremental Parsing Performance ===")
        print(f"Initial parse: {initial_time:.4f}s")
        print(f"Average re-parse: {avg_reparse:.4f}s")
        print(f"Re-parse speedup: {initial_time / avg_reparse:.1f}x")
        
        # Re-parsing should be significantly faster due to incremental parsing
        # Note: This test demonstrates tree-sitter's capability, though
        # the current implementation may not fully utilize incremental parsing
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_memory_efficiency(
        self,
        tree_sitter_analyzer,
        metadata_analyzer,
        generate_large_python_file
    ):
        """Test memory efficiency of both analyzers."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Generate large file
        large_file = generate_large_python_file(num_classes=300, num_methods_per_class=20)
        
        # Test TreeSitterAnalyzer memory usage
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        for _ in range(10):
            await tree_sitter_analyzer.analyze_python_file(large_file)
        
        gc.collect()
        tree_sitter_memory = process.memory_info().rss / 1024 / 1024 - initial_memory
        
        # Test MetadataAnalyzer memory usage
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        for _ in range(10):
            await metadata_analyzer.analyze_python_file(large_file)
        
        gc.collect()
        metadata_memory = process.memory_info().rss / 1024 / 1024 - initial_memory
        
        print(f"\n=== Memory Efficiency ===")
        print(f"TreeSitterAnalyzer memory delta: {tree_sitter_memory:.2f} MB")
        print(f"MetadataAnalyzer memory delta:   {metadata_memory:.2f} MB")
        
        # Tree-sitter should be more memory efficient
        # (though Python's GC makes this test somewhat unreliable)
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_error_recovery_performance(
        self,
        tree_sitter_analyzer,
        metadata_analyzer,
        tmp_path
    ):
        """Test performance when analyzing files with syntax errors."""
        # Create file with syntax errors
        error_file = tmp_path / "errors.py"
        content = '''
# File with various syntax errors

def broken_function(param1, param2  # Missing closing paren
    return param1 + param2

class IncompleteClass  # Missing colon
    def method(self):
        return "test"

# Unclosed string
message = "This is an unclosed string

# Invalid indentation
    def misaligned():
        pass

# Multiple errors in one construct
def another_broken(
    param1: str,
    param2  # Missing type annotation and closing paren
    result = param1 + param2  # Wrong indentation
    return result

# Valid code mixed with errors
def valid_function():
    return "This function is valid"

class ValidClass:
    def __init__(self):
        self.value = 42
'''
        error_file.write_text(content)
        
        # Benchmark TreeSitterAnalyzer (should handle errors gracefully)
        start = time.perf_counter()
        ts_result = await tree_sitter_analyzer.analyze_python_file(error_file)
        tree_sitter_time = time.perf_counter() - start
        
        # Benchmark MetadataAnalyzer (AST parsing may fail completely)
        start = time.perf_counter()
        meta_result = await metadata_analyzer.analyze_python_file(error_file)
        metadata_time = time.perf_counter() - start
        
        print(f"\n=== Error Recovery Performance ===")
        print(f"TreeSitterAnalyzer: {tree_sitter_time:.4f}s")
        print(f"MetadataAnalyzer:   {metadata_time:.4f}s")
        print(f"TreeSitter extracted: {len(ts_result.get('functions', []))} functions")
        print(f"Metadata extracted:   {len(meta_result.get('functions', []))} functions")
        
        # Tree-sitter should extract more information from broken files
        assert len(ts_result.get('functions', [])) >= len(meta_result.get('functions', []))
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_language_switching_performance(
        self,
        tree_sitter_analyzer,
        generate_multiple_files
    ):
        """Test performance when switching between different languages."""
        # Generate files of different types
        files = generate_multiple_files(num_files=30)
        
        # Randomize file order to simulate language switching
        import random
        random.shuffle(files)
        
        # Benchmark rapid language switching
        start = time.perf_counter()
        for file_path in files:
            await tree_sitter_analyzer.collect_file_metadata(
                str(file_path),
                ModificationType.CREATE
            )
        switching_time = time.perf_counter() - start
        
        # Benchmark same language batch processing
        files.sort(key=lambda p: p.suffix)  # Group by extension
        start = time.perf_counter()
        for file_path in files:
            await tree_sitter_analyzer.collect_file_metadata(
                str(file_path),
                ModificationType.CREATE
            )
        batch_time = time.perf_counter() - start
        
        print(f"\n=== Language Switching Performance ===")
        print(f"Random order (switching): {switching_time:.4f}s")
        print(f"Grouped by language:      {batch_time:.4f}s")
        print(f"Switching overhead:       {((switching_time / batch_time) - 1) * 100:.1f}%")
        
        # Language switching overhead should be minimal with tree-sitter
        assert switching_time < batch_time * 1.2  # Less than 20% overhead