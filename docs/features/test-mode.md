# Test Mode Feature

## Overview

The `--test-mode` flag enables prompt logging for debugging and testing purposes. When enabled, all prompts sent to Claude Code are logged to the `.claude-pm/logs/prompts/` directory.

## Usage

### Basic Usage
```bash
# Enable test mode for YOLO mode (no arguments)
claude-pm --test-mode

# Enable test mode with other arguments
claude-pm --test-mode --continue

# Enable test mode with file paths
claude-pm --test-mode /path/to/file.py
```

### What it Does

1. **Creates Log Directory**: Automatically creates `.claude-pm/logs/prompts/` if it doesn't exist
2. **Enables Verbose Mode**: Passes `--verbose` flag to Claude CLI for prompt logging
3. **Sets Environment Variables**: 
   - `CLAUDE_PM_TEST_MODE=true`
   - `CLAUDE_PM_PROMPTS_DIR=/path/to/.claude-pm/logs/prompts/`
4. **Displays Status**: Shows test mode activation message before launching Claude

### Integration with CLI Architecture

The `--test-mode` flag integrates with both:
- **YOLO Mode**: Direct Claude CLI launch with essential flags
- **Enhanced Flags**: Works alongside other CLI options
- **Pass-through Arguments**: Compatible with file paths and other Claude CLI arguments

### Log Output Location

Prompts are logged to:
```
.claude-pm/
  └── logs/
      └── prompts/
          └── [timestamp]_prompt.log
```

### Use Cases

1. **Debugging Agent Interactions**: See exact prompts sent by the PM orchestrator
2. **Performance Analysis**: Review prompt complexity and frequency
3. **Testing Framework Changes**: Verify prompt formatting and content
4. **Training and Documentation**: Capture real-world usage examples

### Technical Details

- The flag is handled before other argument processing
- It's removed from args before passing to Claude CLI (not a native Claude flag)
- Works with both the Node.js wrapper and direct Claude CLI launch
- Compatible with all existing CLI modes and features

### Limitations

- Requires Claude CLI to support `--verbose` flag for prompt logging
- Log format depends on Claude CLI's verbose output implementation
- Directory permissions must allow write access to `.claude-pm/logs/prompts/`