# Refactoring Test Harness

## Overview

This test harness provides comprehensive validation tools for the EP-0043 code refactoring initiative. It ensures that refactoring work maintains functionality, preserves backward compatibility, and doesn't degrade performance.

## Quick Start

### Before Refactoring

Create a baseline snapshot and performance profile:

```bash
python tests/refactoring_harness/validate_refactoring.py claude_pm/services/parent_directory_manager.py --baseline
```

### During Refactoring

Run continuous validation to catch issues immediately:

```bash
python tests/refactoring_harness/validate_refactoring.py claude_pm/services/parent_directory_manager.py --continuous
```

### After Refactoring

Validate all changes:

```bash
python tests/refactoring_harness/validate_refactoring.py claude_pm/services/parent_directory_manager.py
```

## Components

### 1. Test Harness (`test_harness.py`)

The main validation framework that:
- Captures module snapshots before refactoring
- Validates API compatibility
- Checks import/export consistency
- Verifies line count targets
- Runs integration tests

### 2. Performance Benchmark (`performance_benchmark.py`)

Performance validation that:
- Measures import times
- Tracks memory usage
- Benchmarks key functions
- Detects performance regressions

### 3. Automated Test Runner (`automated_test_runner.py`)

Test automation that:
- Runs all tests for a module
- Tracks test coverage
- Detects test regressions
- Supports continuous testing

### 4. Validation Script (`validate_refactoring.py`)

The main entry point that combines all tools for easy validation.

## Validation Checklist

Before submitting refactored code, ensure:

- [ ] ✅ API Compatibility - All public APIs remain unchanged
- [ ] ✅ Import/Export Validation - All exports still available
- [ ] ✅ Test Suite - All existing tests pass
- [ ] ✅ Test Coverage - Coverage maintained or improved
- [ ] ✅ Performance - No significant performance degradation
- [ ] ✅ Line Count - File is ≤1000 lines

## Detailed Usage

### Creating Baselines

Always create baselines before starting refactoring:

```bash
# Single module
python validate_refactoring.py <module_path> --baseline

# All target modules
python test_harness.py  # Run pre-refactoring suite
```

### Validation Options

```bash
# Full validation (recommended)
python validate_refactoring.py <module_path>

# Quick validation (skip performance tests)
python validate_refactoring.py <module_path> --skip-performance

# Validate all refactored modules
python validate_refactoring.py --all
```

### Understanding Results

#### Successful Validation

```
✅ ALL VALIDATIONS PASSED! Module is ready for review.
```

#### Failed Validation

```
❌ VALIDATION FAILED. Please fix issues before submitting.
```

Check the detailed report for specific issues:
- `reports/validation_report_*.md` - Structural validation details
- `reports/test_report_*.md` - Test execution results
- `benchmarks/benchmark_report_*.md` - Performance comparison

## Common Issues

### No Snapshot Found

If you see "No snapshot found", create a baseline first:

```bash
python validate_refactoring.py <module> --baseline
```

### Test Failures

If tests fail after refactoring:
1. Check the test report for specific failures
2. Ensure all imports are updated if modules were split
3. Verify mock objects match new structure

### Performance Regressions

If performance degrades:
1. Profile the specific functions showing regression
2. Check for unnecessary loops or object creation
3. Ensure optimizations weren't removed

### Line Count Exceeded

If file still exceeds 1000 lines:
1. Consider further modularization
2. Extract additional helper modules
3. Move constants/configs to separate files

## Best Practices

1. **Always Create Baselines First**
   - Run baseline creation before any changes
   - This provides a comparison point

2. **Use Continuous Validation**
   - Keep validation running while refactoring
   - Catches issues immediately

3. **Refactor Incrementally**
   - Make small, testable changes
   - Validate after each significant change

4. **Maintain Test Coverage**
   - Add tests for new modules created
   - Update tests for changed interfaces

5. **Document Changes**
   - Note any API changes (even internal ones)
   - Update docstrings for moved functions

## Module-Specific Notes

### parent_directory_manager.py (2,620 lines)
- Consider splitting into: config, deployment, monitoring
- Heavy file I/O - watch performance carefully

### agent_registry.py (2,151 lines)
- Remove async version, keep only sync
- Many interconnected methods - test thoroughly

### backwards_compatible_orchestrator.py (1,961 lines)
- Extract agent strategies into separate modules
- Maintain facade for backward compatibility

## Reporting Issues

If the test harness has issues:
1. Check error messages and stack traces
2. Ensure all dependencies are installed
3. Report to QA team with:
   - Module being validated
   - Error messages
   - Steps to reproduce

## Integration with CI/CD

The validation script returns exit codes:
- `0` - All validations passed
- `1` - One or more validations failed

This allows integration with CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Validate Refactoring
  run: python tests/refactoring_harness/validate_refactoring.py --all
```

## Future Enhancements

Planned improvements:
- Automatic git bisect for regression detection
- Visual diff tools for API changes
- Parallel test execution
- Integration with code review tools