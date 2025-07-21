# Refactor __main__.py (1,165 lines)

**Issue ID**: ISS-0165  
**Epic**: EP-0043  
**Status**: open  
**Priority**: low  
**Created**: 2025-07-18  
**Updated**: 2025-07-18  
**Estimated Effort**: 2 days  
**Tags**: refactoring, maintainability, low-priority

## Summary
Refactor the CLI __main__.py entry point to reduce its size from 1,165 lines to multiple focused modules, improving CLI architecture and command organization.

## Current State
- **File**: `claude_pm/__main__.py`
- **Current Size**: 1,165 lines
- **Complexity**: Main CLI entry point handling:
  - Command parsing
  - Subcommand routing
  - Argument validation
  - Output formatting
  - Error handling
  - Help generation

## Proposed Refactoring

### Module Split Strategy
1. **__main__.py** (~100 lines)
   - Entry point only
   - Basic CLI setup
   - Command router initialization
   
2. **cli_commands.py** (~300 lines)
   - Command definitions
   - Command grouping
   - Command metadata
   
3. **argument_parser.py** (~200 lines)
   - Argument parsing logic
   - Validation rules
   - Type conversions
   
4. **command_handlers.py** (~250 lines)
   - Command implementation
   - Business logic routing
   - Response handling
   
5. **output_formatter.py** (~150 lines)
   - Output formatting
   - Table generation
   - JSON/YAML output
   
6. **cli_utils.py** (~165 lines)
   - CLI helpers
   - Common utilities
   - Error formatting

### Implementation Plan
1. **Day 1**: Extract command definitions and parsing
2. **Day 2**: Separate handlers and formatting

## Testing Requirements
- [ ] CLI command tests
- [ ] Argument parsing tests
- [ ] Output format tests
- [ ] Error handling tests
- [ ] Help text validation

## Acceptance Criteria
- [ ] No file exceeds 1000 lines
- [ ] All CLI commands work
- [ ] Help text accurate
- [ ] Error messages clear
- [ ] Performance maintained

## Risk Assessment
- **Low Risk**: CLI refactoring with good test coverage
- **Mitigation**: Comprehensive CLI testing

## Documentation Updates Required
- [ ] CLI command reference
- [ ] Argument documentation
- [ ] Output format guide
- [ ] Extension guide

## Notes
- Opportunity to improve CLI UX
- Consider adding command aliases
- Evaluate autocomplete support