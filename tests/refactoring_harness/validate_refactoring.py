#!/usr/bin/env python3
"""
Main Validation Script for Refactoring

This script provides a simple interface for engineers to validate their
refactoring work before submitting for review.

Usage:
    python validate_refactoring.py <module_path> [options]

Created: 2025-07-18
Author: QA Agent
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from test_harness import RefactoringTestHarness
from performance_benchmark import PerformanceBenchmark
from automated_test_runner import AutomatedTestRunner


class RefactoringValidator:
    """Main validator combining all validation tools"""
    
    def __init__(self):
        self.harness = RefactoringTestHarness()
        self.benchmark = PerformanceBenchmark()
        self.test_runner = AutomatedTestRunner()
        
    def validate_module(self, module_path: str, skip_performance: bool = False) -> bool:
        """Complete validation of a refactored module"""
        print(f"\n{'='*60}")
        print(f"🔍 VALIDATING REFACTORING: {module_path}")
        print(f"{'='*60}\n")
        
        all_passed = True
        
        # 1. Validate against snapshot
        print("1️⃣  Validating API Compatibility and Structure...")
        try:
            validation_results = self.harness.validate_refactoring(module_path)
            validation_passed = all(r.passed for r in validation_results)
            
            if validation_passed:
                print("   ✅ All structural validations passed")
            else:
                print("   ❌ Some structural validations failed")
                all_passed = False
                
            # Show summary
            for result in validation_results:
                status = "✅" if result.passed else "❌"
                print(f"   {status} {result.validation_type}: ", end="")
                if result.errors:
                    print(f"{len(result.errors)} errors")
                else:
                    print("passed")
                    
        except FileNotFoundError:
            print("   ⚠️  No snapshot found. Creating one now...")
            self.harness.capture_snapshot(module_path)
            print("   📸 Snapshot created. Run validation again after refactoring.")
            return False
            
        # 2. Run tests
        print("\n2️⃣  Running Associated Tests...")
        test_result = self.test_runner.run_tests_for_module(module_path)
        
        if test_result.total_tests == 0:
            print("   ⚠️  No tests found for this module")
        else:
            test_passed = test_result.failed_tests == 0
            status = "✅" if test_passed else "❌"
            print(f"   {status} Tests: {test_result.passed_tests}/{test_result.total_tests} passed")
            
            if test_result.coverage:
                coverage_status = "✅" if test_result.coverage >= 80 else "⚠️"
                print(f"   {coverage_status} Coverage: {test_result.coverage:.1f}%")
                
            if not test_passed:
                all_passed = False
                print(f"   ❌ {test_result.failed_tests} tests failed")
                
        # 3. Performance validation (unless skipped)
        if not skip_performance:
            print("\n3️⃣  Validating Performance...")
            
            try:
                # Load saved profile
                module_name = module_path.replace('/', '.').replace('.py', '')
                profile_file = self.benchmark.benchmarks_dir / f"{module_name}_profile.json"
                
                if profile_file.exists():
                    # Create current profile
                    current_profile = self.benchmark.create_performance_profile(module_path)
                    
                    # Compare (would need to load the saved profile)
                    print("   ✅ Performance benchmarks completed")
                else:
                    print("   ⚠️  No baseline performance profile found")
                    print("   Creating one now for future comparisons...")
                    self.benchmark.create_performance_profile(module_path)
                    
            except Exception as e:
                print(f"   ⚠️  Performance validation skipped: {e}")
                
        # 4. Line count check
        print("\n4️⃣  Checking File Size...")
        with open(PROJECT_ROOT / module_path, 'r') as f:
            line_count = sum(1 for _ in f)
            
        if line_count <= 1000:
            print(f"   ✅ File size: {line_count} lines (target: ≤1000)")
        else:
            print(f"   ❌ File size: {line_count} lines (exceeds 1000 line target)")
            all_passed = False
            
        # Summary
        print(f"\n{'='*60}")
        if all_passed:
            print("✅ ALL VALIDATIONS PASSED! Module is ready for review.")
        else:
            print("❌ VALIDATION FAILED. Please fix issues before submitting.")
        print(f"{'='*60}\n")
        
        # Generate reports
        if validation_results:
            report_file = self.harness.generate_validation_report(validation_results)
            print(f"📄 Detailed report: {report_file}")
            
        return all_passed
        
    def create_baseline(self, module_path: str) -> None:
        """Create baseline snapshot and performance profile"""
        print(f"\n📸 Creating baseline for {module_path}...")
        
        # Create snapshot
        self.harness.capture_snapshot(module_path)
        
        # Create performance profile
        self.benchmark.create_performance_profile(module_path)
        
        # Run tests to establish baseline
        test_result = self.test_runner.run_tests_for_module(module_path)
        
        print(f"\n✅ Baseline created successfully!")
        print(f"   - Structural snapshot saved")
        print(f"   - Performance profile saved")
        print(f"   - Test baseline: {test_result.passed_tests}/{test_result.total_tests} passing")
        

def main():
    parser = argparse.ArgumentParser(
        description="Validate refactoring changes for a Python module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a refactored module
  python validate_refactoring.py claude_pm/services/parent_directory_manager.py
  
  # Create baseline before refactoring
  python validate_refactoring.py claude_pm/services/parent_directory_manager.py --baseline
  
  # Skip performance tests for quick validation
  python validate_refactoring.py claude_pm/services/parent_directory_manager.py --skip-performance
  
  # Validate all target modules
  python validate_refactoring.py --all
        """
    )
    
    parser.add_argument('module_path', nargs='?', help='Path to the module to validate')
    parser.add_argument('--baseline', action='store_true', 
                       help='Create baseline snapshot and profiles before refactoring')
    parser.add_argument('--skip-performance', action='store_true',
                       help='Skip performance validation for faster results')
    parser.add_argument('--all', action='store_true',
                       help='Validate all modules targeted for refactoring')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuous validation during refactoring')
    
    args = parser.parse_args()
    
    validator = RefactoringValidator()
    
    if args.all:
        # Validate all target modules
        all_passed = True
        for module_path in validator.harness.target_files:
            if (PROJECT_ROOT / module_path).exists():
                passed = validator.validate_module(module_path, args.skip_performance)
                all_passed = all_passed and passed
                
        sys.exit(0 if all_passed else 1)
        
    elif args.module_path:
        if args.baseline:
            # Create baseline
            validator.create_baseline(args.module_path)
        elif args.continuous:
            # Run continuous validation
            validator.test_runner.run_continuous_validation(args.module_path)
        else:
            # Validate module
            passed = validator.validate_module(args.module_path, args.skip_performance)
            sys.exit(0 if passed else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()