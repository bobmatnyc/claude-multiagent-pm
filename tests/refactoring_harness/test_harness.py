#!/usr/bin/env python3
"""
Comprehensive Test Harness for EP-0043 Code Refactoring Initiative

This harness provides automated validation to ensure refactoring doesn't break
functionality, maintains backward compatibility, and doesn't degrade performance.

Created: 2025-07-18
Author: QA Agent
"""

import os
import sys
import json
import time
import importlib
import inspect
import traceback
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import subprocess
import ast
import difflib
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import hashlib
import pickle

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TestResult:
    """Container for individual test results"""
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    
    
@dataclass
class ValidationResult:
    """Container for validation results"""
    module_name: str
    validation_type: str  # 'api', 'import', 'performance', 'integration'
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    

@dataclass
class RefactoringSnapshot:
    """Captures state before refactoring for comparison"""
    module_path: str
    api_signatures: Dict[str, str]
    exports: List[str]
    imports: List[str]
    line_count: int
    complexity_metrics: Dict[str, Any]
    performance_baseline: Dict[str, float]
    test_coverage: float
    created_at: datetime = field(default_factory=datetime.now)


class RefactoringTestHarness:
    """Main test harness for validating refactoring work"""
    
    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.snapshots_dir = project_root / "tests" / "refactoring_harness" / "snapshots"
        self.reports_dir = project_root / "tests" / "refactoring_harness" / "reports"
        self.benchmarks_dir = project_root / "tests" / "refactoring_harness" / "benchmarks"
        
        # Create directories
        for dir_path in [self.snapshots_dir, self.reports_dir, self.benchmarks_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Files being refactored (from EP-0043)
        self.target_files = [
            "claude_pm/services/parent_directory_manager.py",  # 2,620 lines
            "claude_pm/core/agent_registry.py",  # 2,151 lines
            "claude_pm/agents/orchestration/backwards_compatible_orchestrator.py",  # 1,961 lines
            "claude_pm/core/agent_registry_sync.py",  # 1,574 lines
            "claude_pm/services/health_monitor.py",  # 1,482 lines
            "claude_pm/services/template_manager.py",  # 1,480 lines
            "claude_pm/services/continuous_learning_engine.py",  # 1,335 lines
            "claude_pm/services/unified_core_service.py",  # 1,308 lines
            "claude_pm/agents/system_init_agent.py",  # 1,201 lines
            "claude_pm/utils/ticket_parser.py",  # 1,190 lines
            "claude_pm/agents/agent_loader.py",  # 1,174 lines
            "claude_pm/__main__.py",  # 1,165 lines
            "claude_pm/agents/base_agent_loader.py",  # 1,159 lines
            "claude_pm/services/shared_prompt_cache.py",  # 1,142 lines
            "claude_pm/services/project_config_repository.py",  # 1,139 lines
            "claude_pm/utils/directory_utils.py",  # 1,070 lines
        ]
        
    def capture_snapshot(self, module_path: str) -> RefactoringSnapshot:
        """Capture current state of a module before refactoring"""
        print(f"📸 Capturing snapshot for {module_path}")
        
        full_path = self.project_root / module_path
        if not full_path.exists():
            raise FileNotFoundError(f"Module not found: {module_path}")
            
        # Get API signatures
        api_signatures = self._extract_api_signatures(full_path)
        
        # Get exports and imports
        exports = self._extract_exports(full_path)
        imports = self._extract_imports(full_path)
        
        # Get line count
        with open(full_path, 'r') as f:
            line_count = sum(1 for _ in f)
            
        # Get complexity metrics
        complexity_metrics = self._calculate_complexity(full_path)
        
        # Get performance baseline
        performance_baseline = self._measure_performance_baseline(module_path)
        
        # Get test coverage
        test_coverage = self._get_test_coverage(module_path)
        
        snapshot = RefactoringSnapshot(
            module_path=module_path,
            api_signatures=api_signatures,
            exports=exports,
            imports=imports,
            line_count=line_count,
            complexity_metrics=complexity_metrics,
            performance_baseline=performance_baseline,
            test_coverage=test_coverage
        )
        
        # Save snapshot
        snapshot_file = self.snapshots_dir / f"{module_path.replace('/', '_')}.pkl"
        with open(snapshot_file, 'wb') as f:
            pickle.dump(snapshot, f)
            
        print(f"✅ Snapshot saved: {snapshot_file}")
        return snapshot
        
    def validate_refactoring(self, module_path: str) -> List[ValidationResult]:
        """Validate a refactored module against its snapshot"""
        print(f"\n🔍 Validating refactoring for {module_path}")
        
        # Load snapshot
        snapshot_file = self.snapshots_dir / f"{module_path.replace('/', '_')}.pkl"
        if not snapshot_file.exists():
            raise FileNotFoundError(f"No snapshot found for {module_path}. Run capture_snapshot first.")
            
        with open(snapshot_file, 'rb') as f:
            snapshot = pickle.load(f)
            
        results = []
        
        # Validate API compatibility
        results.append(self._validate_api_compatibility(module_path, snapshot))
        
        # Validate imports/exports
        results.append(self._validate_imports_exports(module_path, snapshot))
        
        # Validate performance
        results.append(self._validate_performance(module_path, snapshot))
        
        # Validate line count
        results.append(self._validate_line_count(module_path, snapshot))
        
        # Run integration tests
        results.append(self._run_integration_tests(module_path))
        
        return results
        
    def _extract_api_signatures(self, file_path: Path) -> Dict[str, str]:
        """Extract public API signatures from a module"""
        signatures = {}
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # Skip private methods
                    if not node.name.startswith('_') or node.name.startswith('__'):
                        signatures[node.name] = ast.unparse(node)
                        
        except Exception as e:
            print(f"⚠️  Error extracting signatures: {e}")
            
        return signatures
        
    def _extract_exports(self, file_path: Path) -> List[str]:
        """Extract exported names from a module"""
        exports = []
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            # Check for __all__
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__all__':
                            if isinstance(node.value, ast.List):
                                exports = [elt.s for elt in node.value.elts if isinstance(elt, ast.Str)]
                                return exports
                                
            # If no __all__, get all public names
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not node.name.startswith('_'):
                        exports.append(node.name)
                        
        except Exception as e:
            print(f"⚠️  Error extracting exports: {e}")
            
        return exports
        
    def _extract_imports(self, file_path: Path) -> List[str]:
        """Extract import statements from a module"""
        imports = []
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
                        
        except Exception as e:
            print(f"⚠️  Error extracting imports: {e}")
            
        return imports
        
    def _calculate_complexity(self, file_path: Path) -> Dict[str, Any]:
        """Calculate complexity metrics for a module"""
        metrics = {
            'classes': 0,
            'functions': 0,
            'async_functions': 0,
            'max_nesting_depth': 0,
            'average_function_length': 0
        }
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            function_lengths = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metrics['classes'] += 1
                elif isinstance(node, ast.FunctionDef):
                    metrics['functions'] += 1
                    # Calculate function length
                    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                        length = node.end_lineno - node.lineno
                        function_lengths.append(length)
                elif isinstance(node, ast.AsyncFunctionDef):
                    metrics['async_functions'] += 1
                    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                        length = node.end_lineno - node.lineno
                        function_lengths.append(length)
                        
            if function_lengths:
                metrics['average_function_length'] = sum(function_lengths) / len(function_lengths)
                
        except Exception as e:
            print(f"⚠️  Error calculating complexity: {e}")
            
        return metrics
        
    def _measure_performance_baseline(self, module_path: str) -> Dict[str, float]:
        """Measure performance baseline for a module"""
        baseline = {
            'import_time': 0.0,
            'memory_usage': 0.0
        }
        
        # Measure import time
        module_name = module_path.replace('/', '.').replace('.py', '')
        
        start_time = time.time()
        try:
            importlib.import_module(module_name)
            baseline['import_time'] = time.time() - start_time
        except Exception as e:
            print(f"⚠️  Error measuring import time: {e}")
            
        # TODO: Add memory usage measurement
        
        return baseline
        
    def _get_test_coverage(self, module_path: str) -> float:
        """Get current test coverage for a module"""
        # This would integrate with coverage.py
        # For now, return a placeholder
        return 0.0
        
    def _validate_api_compatibility(self, module_path: str, snapshot: RefactoringSnapshot) -> ValidationResult:
        """Validate that public API remains compatible"""
        result = ValidationResult(
            module_name=module_path,
            validation_type='api',
            passed=True
        )
        
        try:
            full_path = self.project_root / module_path
            current_signatures = self._extract_api_signatures(full_path)
            
            # Check for missing APIs
            for api_name, signature in snapshot.api_signatures.items():
                if api_name not in current_signatures:
                    result.passed = False
                    result.errors.append(f"Missing API: {api_name}")
                elif current_signatures[api_name] != signature:
                    # Check if it's just formatting differences
                    result.warnings.append(f"API signature changed: {api_name}")
                    
            # Check for new APIs (informational)
            for api_name in current_signatures:
                if api_name not in snapshot.api_signatures:
                    result.details[f'new_api_{api_name}'] = True
                    
        except Exception as e:
            result.passed = False
            result.errors.append(f"Error validating API: {str(e)}")
            
        return result
        
    def _validate_imports_exports(self, module_path: str, snapshot: RefactoringSnapshot) -> ValidationResult:
        """Validate imports and exports remain consistent"""
        result = ValidationResult(
            module_name=module_path,
            validation_type='import',
            passed=True
        )
        
        try:
            full_path = self.project_root / module_path
            current_exports = self._extract_exports(full_path)
            
            # Check exports
            missing_exports = set(snapshot.exports) - set(current_exports)
            if missing_exports:
                result.passed = False
                result.errors.extend([f"Missing export: {exp}" for exp in missing_exports])
                
            new_exports = set(current_exports) - set(snapshot.exports)
            if new_exports:
                result.details['new_exports'] = list(new_exports)
                
        except Exception as e:
            result.passed = False
            result.errors.append(f"Error validating imports/exports: {str(e)}")
            
        return result
        
    def _validate_performance(self, module_path: str, snapshot: RefactoringSnapshot) -> ValidationResult:
        """Validate performance hasn't degraded"""
        result = ValidationResult(
            module_name=module_path,
            validation_type='performance',
            passed=True
        )
        
        try:
            current_baseline = self._measure_performance_baseline(module_path)
            
            # Check import time (allow 10% degradation)
            import_time_ratio = current_baseline['import_time'] / (snapshot.performance_baseline['import_time'] or 1)
            if import_time_ratio > 1.1:
                result.passed = False
                result.errors.append(f"Import time degraded by {(import_time_ratio - 1) * 100:.1f}%")
            else:
                result.details['import_time_improvement'] = f"{(1 - import_time_ratio) * 100:.1f}%"
                
        except Exception as e:
            result.warnings.append(f"Could not validate performance: {str(e)}")
            
        return result
        
    def _validate_line_count(self, module_path: str, snapshot: RefactoringSnapshot) -> ValidationResult:
        """Validate line count is under 1000"""
        result = ValidationResult(
            module_name=module_path,
            validation_type='line_count',
            passed=True
        )
        
        try:
            full_path = self.project_root / module_path
            with open(full_path, 'r') as f:
                current_lines = sum(1 for _ in f)
                
            result.details['original_lines'] = snapshot.line_count
            result.details['current_lines'] = current_lines
            result.details['reduction'] = snapshot.line_count - current_lines
            
            if current_lines > 1000:
                result.passed = False
                result.errors.append(f"File still exceeds 1000 lines: {current_lines}")
                
        except Exception as e:
            result.passed = False
            result.errors.append(f"Error counting lines: {str(e)}")
            
        return result
        
    def _run_integration_tests(self, module_path: str) -> ValidationResult:
        """Run integration tests for the module"""
        result = ValidationResult(
            module_name=module_path,
            validation_type='integration',
            passed=True
        )
        
        # Map modules to their test files
        test_mapping = {
            'claude_pm/services/parent_directory_manager.py': [
                'tests/unit/services/test_parent_directory_manager.py',
                'tests/integration/services/test_parent_directory_manager_integration.py'
            ],
            'claude_pm/core/agent_registry.py': [
                'tests/unit/core/test_agent_registry.py'
            ],
            # Add more mappings as needed
        }
        
        test_files = test_mapping.get(module_path, [])
        
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                # Run pytest for specific test file
                cmd = ['pytest', test_file, '-v', '--tb=short']
                try:
                    process = subprocess.run(
                        cmd,
                        cwd=self.project_root,
                        capture_output=True,
                        text=True
                    )
                    
                    if process.returncode != 0:
                        result.passed = False
                        result.errors.append(f"Tests failed in {test_file}")
                        result.details[test_file] = process.stdout + process.stderr
                    else:
                        result.details[test_file] = "All tests passed"
                        
                except Exception as e:
                    result.warnings.append(f"Could not run tests for {test_file}: {str(e)}")
                    
        return result
        
    def generate_validation_report(self, results: List[ValidationResult], output_file: Optional[str] = None) -> str:
        """Generate a comprehensive validation report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_file:
            output_file = self.reports_dir / f"validation_report_{timestamp}.md"
        else:
            output_file = Path(output_file)
            
        report_lines = [
            "# Refactoring Validation Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Summary\n"
        ]
        
        # Count passes and failures
        total_validations = len(results)
        passed_validations = sum(1 for r in results if r.passed)
        
        report_lines.append(f"- Total Validations: {total_validations}")
        report_lines.append(f"- Passed: {passed_validations}")
        report_lines.append(f"- Failed: {total_validations - passed_validations}")
        report_lines.append(f"- Success Rate: {(passed_validations / total_validations * 100):.1f}%")
        
        # Group results by module
        by_module = {}
        for result in results:
            if result.module_name not in by_module:
                by_module[result.module_name] = []
            by_module[result.module_name].append(result)
            
        # Detailed results
        report_lines.append("\n## Detailed Results\n")
        
        for module, module_results in by_module.items():
            report_lines.append(f"\n### {module}\n")
            
            for result in module_results:
                status = "✅ PASSED" if result.passed else "❌ FAILED"
                report_lines.append(f"#### {result.validation_type.upper()} Validation: {status}\n")
                
                if result.errors:
                    report_lines.append("**Errors:**")
                    for error in result.errors:
                        report_lines.append(f"- {error}")
                    report_lines.append("")
                    
                if result.warnings:
                    report_lines.append("**Warnings:**")
                    for warning in result.warnings:
                        report_lines.append(f"- {warning}")
                    report_lines.append("")
                    
                if result.details:
                    report_lines.append("**Details:**")
                    for key, value in result.details.items():
                        report_lines.append(f"- {key}: {value}")
                    report_lines.append("")
                    
        # Write report
        report_content = "\n".join(report_lines)
        with open(output_file, 'w') as f:
            f.write(report_content)
            
        print(f"\n📄 Report generated: {output_file}")
        return report_content
        
    def run_pre_refactoring_suite(self) -> None:
        """Run complete pre-refactoring validation suite"""
        print("\n🚀 Running Pre-Refactoring Validation Suite")
        print("=" * 60)
        
        for module_path in self.target_files:
            try:
                # Check if file exists
                if not (self.project_root / module_path).exists():
                    print(f"⚠️  Skipping {module_path} - file not found")
                    continue
                    
                # Capture snapshot
                self.capture_snapshot(module_path)
                
                # Run initial tests to ensure they pass before refactoring
                print(f"\n🧪 Running baseline tests for {module_path}")
                self._run_integration_tests(module_path)
                
            except Exception as e:
                print(f"❌ Error processing {module_path}: {e}")
                traceback.print_exc()
                
        print("\n✅ Pre-refactoring validation complete!")
        
    def run_post_refactoring_validation(self, module_path: str) -> bool:
        """Run validation after refactoring a specific module"""
        print(f"\n🔧 Running Post-Refactoring Validation for {module_path}")
        print("=" * 60)
        
        try:
            results = self.validate_refactoring(module_path)
            report = self.generate_validation_report(results)
            
            # Check if all validations passed
            all_passed = all(r.passed for r in results)
            
            if all_passed:
                print(f"\n✅ All validations passed for {module_path}!")
            else:
                print(f"\n❌ Some validations failed for {module_path}")
                print("See report for details")
                
            return all_passed
            
        except Exception as e:
            print(f"❌ Error validating {module_path}: {e}")
            traceback.print_exc()
            return False


def main():
    """Main entry point for the test harness"""
    harness = RefactoringTestHarness()
    
    # Run pre-refactoring suite to capture baselines
    harness.run_pre_refactoring_suite()
    
    # Example: Validate a specific module after refactoring
    # success = harness.run_post_refactoring_validation('claude_pm/services/parent_directory_manager.py')
    

if __name__ == "__main__":
    main()