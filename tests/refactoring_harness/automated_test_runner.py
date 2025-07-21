#!/usr/bin/env python3
"""
Automated Test Runner for Refactoring Validation

Provides automated test execution with before/after comparison,
regression detection, and continuous validation during refactoring.

Created: 2025-07-18
Author: QA Agent
"""

import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import hashlib
import difflib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TestRun:
    """Container for test run results"""
    timestamp: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration: float
    failures: List[Dict[str, str]] = field(default_factory=list)
    coverage: Optional[float] = None
    

@dataclass
class TestRegression:
    """Container for test regression information"""
    test_name: str
    module: str
    was_passing: bool
    now_passing: bool
    error_message: Optional[str] = None
    

class AutomatedTestRunner:
    """Automated test runner for refactoring validation"""
    
    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.test_results_dir = project_root / "tests" / "refactoring_harness" / "test_results"
        self.test_results_dir.mkdir(parents=True, exist_ok=True)
        
        # Test configuration
        self.test_timeout = 300  # 5 minutes per test module
        self.coverage_threshold = 80.0  # Target coverage percentage
        
        # Module to test mapping
        self.module_test_mapping = self._build_module_test_mapping()
        
    def _build_module_test_mapping(self) -> Dict[str, List[str]]:
        """Build mapping of source modules to their test files"""
        mapping = {
            'claude_pm/services/parent_directory_manager.py': [
                'tests/unit/services/test_parent_directory_manager.py',
                'tests/integration/deployment/test_claude_md_deployment.py'
            ],
            'claude_pm/core/agent_registry.py': [
                'tests/unit/core/test_agent_registry.py',
                'tests/integration/agents/test_agent_loading_with_delegation.py'
            ],
            'claude_pm/agents/orchestration/backwards_compatible_orchestrator.py': [
                'tests/e2e/test_backwards_compatible_orchestrator.py'
            ],
            'claude_pm/core/agent_registry_sync.py': [
                'tests/unit/core/test_agent_registry.py'  # Same tests as async version
            ],
            'claude_pm/services/health_monitor.py': [
                'tests/e2e/test_m01_044_health_dashboard.py'
            ],
            'claude_pm/services/template_manager.py': [
                'tests/integration/deployment/test_template_integration.py'
            ],
            'claude_pm/services/continuous_learning_engine.py': [
                'tests/integration/test_mirascope_evaluation_system.py'
            ],
            'claude_pm/services/unified_core_service.py': [
                'tests/unit/services/test_unified_core_service.py'
            ],
            'claude_pm/agents/system_init_agent.py': [
                'tests/integration/workflows/test_auto_setup.py'
            ],
            'claude_pm/utils/ticket_parser.py': [
                'tests/e2e/test_completed_tickets.py'
            ],
            'claude_pm/agents/agent_loader.py': [
                'tests/integration/test_agent_loader_improved_prompts_comprehensive.py',
                'tests/integration/test_loader_verification.py'
            ],
            'claude_pm/__main__.py': [
                'tests/integration/workflows/test_claude_pm_cli_integration.py'
            ],
            'claude_pm/agents/base_agent_loader.py': [
                'tests/unit/agents/test_base_agent_loader.py',
                'tests/integration/agents/test_simple_agent_loading.py'
            ],
            'claude_pm/services/shared_prompt_cache.py': [
                'tests/performance/test_async_memory_collector.py'
            ],
            'claude_pm/services/project_config_repository.py': [
                'tests/unit/services/test_configuration_system.py'
            ],
            'claude_pm/utils/directory_utils.py': [
                'tests/integration/test_cleanup_system.py'
            ]
        }
        
        # Verify test files exist
        verified_mapping = {}
        for module, test_files in mapping.items():
            existing_tests = []
            for test_file in test_files:
                if (self.project_root / test_file).exists():
                    existing_tests.append(test_file)
                else:
                    print(f"⚠️  Test file not found: {test_file}")
                    
            if existing_tests:
                verified_mapping[module] = existing_tests
                
        return verified_mapping
        
    def run_tests_for_module(self, module_path: str, coverage: bool = True) -> TestRun:
        """Run all tests associated with a specific module"""
        print(f"\n🧪 Running tests for {module_path}")
        
        test_files = self.module_test_mapping.get(module_path, [])
        if not test_files:
            print(f"⚠️  No tests found for {module_path}")
            return TestRun(
                timestamp=datetime.now(),
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                duration=0.0
            )
            
        # Build pytest command
        cmd = ['pytest'] + test_files + [
            '-v',
            '--tb=short',
            '--junit-xml=test_results.xml',
            f'--timeout={self.test_timeout}'
        ]
        
        if coverage:
            module_name = module_path.replace('/', '.').replace('.py', '')
            cmd.extend([
                f'--cov={module_name}',
                '--cov-report=xml:coverage.xml',
                '--cov-report=term'
            ])
            
        # Run tests
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.test_timeout * len(test_files)
            )
            duration = time.time() - start_time
            
            # Parse results
            test_run = self._parse_test_results(result, duration)
            
            # Parse coverage if enabled
            if coverage and (self.project_root / 'coverage.xml').exists():
                test_run.coverage = self._parse_coverage_xml()
                
            return test_run
            
        except subprocess.TimeoutExpired:
            print(f"❌ Tests timed out for {module_path}")
            return TestRun(
                timestamp=datetime.now(),
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                duration=time.time() - start_time,
                failures=[{
                    'test': 'all',
                    'error': f'Tests timed out after {self.test_timeout}s'
                }]
            )
            
    def _parse_test_results(self, result: subprocess.CompletedProcess, duration: float) -> TestRun:
        """Parse pytest output to extract test results"""
        test_run = TestRun(
            timestamp=datetime.now(),
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            duration=duration
        )
        
        # Try to parse JUnit XML if it exists
        junit_file = self.project_root / 'test_results.xml'
        if junit_file.exists():
            try:
                tree = ET.parse(junit_file)
                root = tree.getroot()
                
                # Extract test counts
                test_run.total_tests = int(root.get('tests', 0))
                test_run.failed_tests = int(root.get('failures', 0)) + int(root.get('errors', 0))
                test_run.skipped_tests = int(root.get('skipped', 0))
                test_run.passed_tests = test_run.total_tests - test_run.failed_tests - test_run.skipped_tests
                
                # Extract failure details
                for testcase in root.findall('.//testcase'):
                    failure = testcase.find('failure')
                    if failure is not None:
                        test_run.failures.append({
                            'test': f"{testcase.get('classname')}.{testcase.get('name')}",
                            'error': failure.get('message', 'Unknown error')
                        })
                        
                # Clean up
                junit_file.unlink()
                
            except Exception as e:
                print(f"⚠️  Could not parse JUnit XML: {e}")
                
        # Fallback to parsing stdout
        if test_run.total_tests == 0:
            output = result.stdout
            
            # Look for pytest summary line
            for line in output.split('\n'):
                if 'passed' in line or 'failed' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            test_run.passed_tests = int(parts[i-1])
                        elif part == 'failed':
                            test_run.failed_tests = int(parts[i-1])
                        elif part == 'skipped':
                            test_run.skipped_tests = int(parts[i-1])
                            
            test_run.total_tests = test_run.passed_tests + test_run.failed_tests + test_run.skipped_tests
            
        return test_run
        
    def _parse_coverage_xml(self) -> float:
        """Parse coverage.xml to extract coverage percentage"""
        try:
            tree = ET.parse(self.project_root / 'coverage.xml')
            root = tree.getroot()
            
            line_rate = float(root.get('line-rate', 0))
            coverage_pct = line_rate * 100
            
            # Clean up
            (self.project_root / 'coverage.xml').unlink()
            
            return coverage_pct
            
        except Exception as e:
            print(f"⚠️  Could not parse coverage XML: {e}")
            return 0.0
            
    def run_all_module_tests(self, modules: Optional[List[str]] = None) -> Dict[str, TestRun]:
        """Run tests for all specified modules"""
        if modules is None:
            modules = list(self.module_test_mapping.keys())
            
        results = {}
        for module in modules:
            results[module] = self.run_tests_for_module(module)
            
        return results
        
    def detect_regressions(self, before_results: Dict[str, TestRun], 
                          after_results: Dict[str, TestRun]) -> List[TestRegression]:
        """Detect test regressions between before and after runs"""
        regressions = []
        
        for module in before_results:
            if module not in after_results:
                continue
                
            before = before_results[module]
            after = after_results[module]
            
            # Check for new failures
            if after.failed_tests > before.failed_tests:
                # Extract test names from failures
                before_failures = {f['test'] for f in before.failures}
                after_failures = {f['test'] for f in after.failures}
                
                new_failures = after_failures - before_failures
                
                for test in new_failures:
                    error_msg = next((f['error'] for f in after.failures if f['test'] == test), None)
                    regressions.append(TestRegression(
                        test_name=test,
                        module=module,
                        was_passing=True,
                        now_passing=False,
                        error_message=error_msg
                    ))
                    
            # Check for coverage regression
            if before.coverage and after.coverage:
                if after.coverage < before.coverage - 5.0:  # 5% tolerance
                    regressions.append(TestRegression(
                        test_name='coverage',
                        module=module,
                        was_passing=True,
                        now_passing=False,
                        error_message=f"Coverage dropped from {before.coverage:.1f}% to {after.coverage:.1f}%"
                    ))
                    
        return regressions
        
    def run_continuous_validation(self, module_path: str, interval: int = 300) -> None:
        """Run tests continuously during refactoring"""
        print(f"\n🔄 Starting continuous validation for {module_path}")
        print(f"   Tests will run every {interval} seconds")
        print("   Press Ctrl+C to stop")
        
        last_result = None
        run_count = 0
        
        try:
            while True:
                run_count += 1
                print(f"\n--- Test Run #{run_count} at {datetime.now().strftime('%H:%M:%S')} ---")
                
                # Run tests
                result = self.run_tests_for_module(module_path)
                
                # Compare with last run
                if last_result:
                    if result.failed_tests > last_result.failed_tests:
                        print("❌ NEW TEST FAILURES DETECTED!")
                    elif result.failed_tests < last_result.failed_tests:
                        print("✅ Some tests are now passing!")
                        
                    if result.coverage and last_result.coverage:
                        coverage_diff = result.coverage - last_result.coverage
                        if abs(coverage_diff) > 0.1:
                            print(f"📊 Coverage changed: {last_result.coverage:.1f}% → {result.coverage:.1f}%")
                            
                # Summary
                print(f"\n📊 Results: {result.passed_tests} passed, {result.failed_tests} failed, "
                      f"{result.skipped_tests} skipped")
                if result.coverage:
                    print(f"📊 Coverage: {result.coverage:.1f}%")
                    
                last_result = result
                
                # Wait for next run
                print(f"\n⏰ Next run in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Continuous validation stopped")
            
    def generate_test_report(self, results: Dict[str, TestRun], 
                           regressions: Optional[List[TestRegression]] = None,
                           output_file: Optional[str] = None) -> str:
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_file:
            output_file = self.test_results_dir / f"test_report_{timestamp}.md"
        else:
            output_file = Path(output_file)
            
        report_lines = [
            "# Refactoring Test Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Summary\n"
        ]
        
        # Overall statistics
        total_modules = len(results)
        total_tests = sum(r.total_tests for r in results.values())
        total_passed = sum(r.passed_tests for r in results.values())
        total_failed = sum(r.failed_tests for r in results.values())
        total_skipped = sum(r.skipped_tests for r in results.values())
        
        report_lines.extend([
            f"- Modules Tested: {total_modules}",
            f"- Total Tests: {total_tests}",
            f"- Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)" if total_tests > 0 else "- Passed: 0",
            f"- Failed: {total_failed}",
            f"- Skipped: {total_skipped}",
            ""
        ])
        
        # Coverage summary
        modules_with_coverage = [m for m, r in results.items() if r.coverage is not None]
        if modules_with_coverage:
            avg_coverage = sum(r.coverage for r in results.values() if r.coverage) / len(modules_with_coverage)
            report_lines.extend([
                f"- Average Coverage: {avg_coverage:.1f}%",
                f"- Modules Meeting {self.coverage_threshold}% Target: "
                f"{sum(1 for r in results.values() if r.coverage and r.coverage >= self.coverage_threshold)}",
                ""
            ])
            
        # Regressions
        if regressions:
            report_lines.extend([
                "\n## ⚠️  Test Regressions\n",
                f"Found {len(regressions)} test regressions:\n"
            ])
            
            for reg in regressions:
                report_lines.append(f"- **{reg.module}** - {reg.test_name}")
                if reg.error_message:
                    report_lines.append(f"  - Error: {reg.error_message}")
                    
        # Module details
        report_lines.append("\n## Module Details\n")
        
        for module, result in sorted(results.items()):
            status = "✅" if result.failed_tests == 0 else "❌"
            report_lines.append(f"### {status} {module}\n")
            
            report_lines.extend([
                f"- Tests: {result.passed_tests}/{result.total_tests} passed",
                f"- Duration: {result.duration:.2f}s"
            ])
            
            if result.coverage is not None:
                coverage_status = "✅" if result.coverage >= self.coverage_threshold else "⚠️"
                report_lines.append(f"- Coverage: {coverage_status} {result.coverage:.1f}%")
                
            if result.failures:
                report_lines.append("\n**Failures:**")
                for failure in result.failures[:5]:  # Show first 5 failures
                    report_lines.append(f"- {failure['test']}: {failure['error']}")
                if len(result.failures) > 5:
                    report_lines.append(f"- ... and {len(result.failures) - 5} more")
                    
            report_lines.append("")
            
        # Recommendations
        if total_failed > 0 or (regressions and len(regressions) > 0):
            report_lines.extend([
                "\n## Recommendations\n",
                "⚠️  Test failures or regressions detected:",
                "1. Review failing tests and fix issues before proceeding",
                "2. Run tests in isolation to identify specific problems",
                "3. Check for missing dependencies or environment issues",
                "4. Consider reverting changes if regressions are severe",
                ""
            ])
            
        # Write report
        report_content = "\n".join(report_lines)
        with open(output_file, 'w') as f:
            f.write(report_content)
            
        print(f"\n📄 Test report generated: {output_file}")
        return report_content
        

def main():
    """Example usage of the automated test runner"""
    runner = AutomatedTestRunner()
    
    # Example: Run tests for a specific module
    # result = runner.run_tests_for_module('claude_pm/services/parent_directory_manager.py')
    
    # Example: Run continuous validation
    # runner.run_continuous_validation('claude_pm/services/parent_directory_manager.py', interval=60)
    

if __name__ == "__main__":
    main()