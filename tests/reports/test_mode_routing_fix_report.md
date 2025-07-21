# Test Mode Routing Fix Report

**Date**: 2025-07-20  
**Issue**: `--test-mode` flag causing "unknown option" error when passed to Claude CLI  
**Status**: ✅ FIXED

## Problem Description

When using `claude-pm --test-mode`, the flag was being incorrectly routed through to the Claude CLI, which doesn't recognize `--test-mode` as a valid option. This resulted in the error:
```
error: unknown option '--test-mode'
```

## Root Cause Analysis

The issue occurred at multiple routing points:

1. **bin/claude-pm**: The main script was detecting `--test-mode` but not properly filtering it out before passing args to Claude CLI
2. **claude_pm/cli_flags.py**: The test mode was implemented as a Click subcommand rather than a flag, causing routing confusion
3. **scripts/claude-wrapper.js**: The Node.js wrapper was passing all arguments directly to Claude, including `--test-mode`

## Fix Implementation

### 1. **bin/claude-pm** (lines 2010-2055)
- Added detection of `--test-mode` from both command line args and environment variable
- Properly filter out `--test-mode` from args before passing to Claude CLI
- Added standalone `--test-mode` handling to launch Claude in YOLO mode with test mode enabled
- Excluded `--test-mode` from enhanced flags processing to prevent incorrect routing

### 2. **claude_pm/cli_flags.py** (lines 365-421)
- Changed from Click subcommand to Click option flag
- Moved test mode handling to the main cli_flags group
- Removed the separate `test_mode_command` function
- Added proper environment variable setup and re-launch logic

### 3. **scripts/claude-wrapper.js** (lines 128-130)
- Added filtering to remove `--test-mode` from arguments before passing to Claude CLI
- Maintains all other wrapper functionality (AbortSignal configuration, etc.)

## Testing Results

All test scenarios now pass without "unknown option" errors:
- ✅ `claude-pm --test-mode --help`
- ✅ `claude-pm --test-mode --version`
- ✅ `claude-pm --test-mode --safe`
- ✅ `claude-pm --test-mode` (standalone)
- ✅ Environment variable `CLAUDE_PM_TEST_MODE=true`

## Technical Details

The fix ensures that:
1. `--test-mode` is recognized as a valid claude-pm flag
2. It sets the appropriate environment variables for test mode
3. It enables prompt logging to `.claude-pm/logs/prompts/`
4. It launches Claude CLI with `--verbose` flag (not `--test-mode`)
5. The flag is properly filtered at all routing points

## Verification

Run the following to verify the fix:
```bash
# Simple verification
python tests/test_test_mode_simple.py

# Comprehensive testing (may have some expected failures for other reasons)
python tests/test_test_mode_comprehensive.py
```

## Impact

This fix ensures that the test mode feature works as intended, allowing developers to:
- Enable verbose prompt logging for debugging
- Test the framework without errors
- Use test mode with any combination of other flags