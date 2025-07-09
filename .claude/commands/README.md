# Claude PM Framework - Claude Code Slash Commands

This directory contains custom Claude Code slash commands for the Claude PM Framework, providing seamless integration between Claude Code's slash command system and the framework's native functionality.

## Available Commands

### 1. `/project:cmpm-health` - System Health Dashboard
- **File**: `cmpm-health.md`
- **Function**: Comprehensive system health dashboard
- **Features**:
  - Framework core health monitoring
  - AI-trackdown tools integration status
  - Memory system connectivity check
  - Task management system validation
  - System reliability scoring (0-100%)

### 2. `/project:cmpm-agents` - Agent Registry Overview
- **File**: `cmpm-agents.md`
- **Function**: Active agent types and status listing
- **Features**:
  - Standard and user-defined agent listings
  - Agent specialization and capability assessment
  - MCP infrastructure support
  - Coordination role mapping
  - Agent availability statistics

### 3. `/project:cmpm-index` - Project Discovery Index
- **File**: `cmpm-index.md`
- **Function**: Comprehensive project discovery and analysis
- **Features**:
  - Automated project discovery
  - Documentation agent delegation
  - Project health assessment
  - Complexity and documentation scoring
  - Project type distribution analysis

## Implementation Architecture

### Command Structure
```
.claude/commands/
├── cmpm-health.md          # Health dashboard slash command
├── cmpm-agents.md          # Agents registry slash command  
├── cmpm-index.md           # Project index slash command
├── cmpm-bridge.py          # Bridge script for framework integration
├── cmpm-helper.md          # Command usage helper
└── README.md              # This documentation
```

### Integration Method
The commands use a bridge script (`cmpm-bridge.py`) that:
1. Imports the existing CMPM framework modules
2. Executes the native command implementations
3. Provides Rich-formatted console output
4. Handles error cases gracefully

### Bridge Script Usage
```bash
python .claude/commands/cmpm-bridge.py health
python .claude/commands/cmpm-bridge.py agents
python .claude/commands/cmpm-bridge.py index
```

## Claude Code Integration

### How It Works
1. **Command Discovery**: Claude Code automatically discovers `.md` files in `.claude/commands/`
2. **Command Execution**: When user types `/project:cmpm-health`, Claude Code reads the markdown file
3. **Framework Integration**: The markdown instructs Claude to execute the bridge script
4. **Output**: Rich-formatted dashboard output is displayed in Claude Code

### Command Usage in Claude Code
```
/project:cmpm-health       # Execute health dashboard
/project:cmpm-agents       # Execute agents registry
/project:cmpm-index        # Execute project index
```

## Features

### Health Dashboard (`/project:cmpm-health`)
- System reliability score calculation
- Component-by-component health breakdown
- AI-trackdown tools integration status
- Memory system connectivity testing
- Performance metrics and response times

### Agents Registry (`/project:cmmp-agents`)
- Complete agent inventory from `framework/agent-roles/agents.json`
- Agent type classification (standard vs user-defined)
- Specialization and capability listing
- MCP coordination framework integration
- Agent availability statistics

### Project Index (`/project:cmpm-index`)
- Automated project discovery and metadata extraction
- Documentation agent delegation for enhanced analysis
- Project health assessment (Excellent, Good, Fair, Poor)
- Documentation and complexity scoring
- Project type distribution and statistics

## Technical Requirements

### Dependencies
- Python 3.8+
- Claude PM Framework installed
- Rich library for console formatting
- Existing CMPM modules and services

### Environment
- Commands execute in the Claude PM Framework root directory
- Require access to framework configuration files
- Need network connectivity for memory service checks

## Success Criteria

✅ **Command Discovery**: All three commands appear in Claude Code's slash command autocomplete
✅ **Command Execution**: Commands execute successfully when typed in Claude Code
✅ **Output Formatting**: Rich-formatted output displays properly in Claude Code interface
✅ **Framework Integration**: Commands access existing CMPM functionality seamlessly
✅ **Error Handling**: Graceful error handling and meaningful error messages

## Usage Examples

### In Claude Code:
```
# Type in Claude Code interface:
/project:cmpm-health

# Claude Code will execute the health dashboard and display:
# - System reliability score
# - Component health status
# - Performance metrics
# - Framework version information
```

### Direct CLI (alternative):
```bash
# Direct framework command execution:
python -m claude_pm.cmpm_commands cmpm:health
python -m claude_pm.cmpm_commands cmpm:agents  
python -m claude_pm.cmpm_commands cmpm:index
```

## Installation Verification

To verify the installation:
1. Ensure `.claude/commands/` directory exists
2. Check that all `.md` files are present
3. Verify `cmpm-bridge.py` is executable
4. Test bridge script functionality
5. Confirm Claude Code discovers the commands

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure Claude PM Framework is properly installed
2. **Path Issues**: Run commands from framework root directory
3. **Permission Errors**: Check that bridge script is executable
4. **Module Not Found**: Verify Python path includes framework modules

### Debug Steps
```bash
# Test bridge script directly
python .claude/commands/cmpm-bridge.py health

# Check Claude Code command discovery
# Commands should appear in Claude Code autocomplete

# Verify framework functionality
python -m claude_pm.cmpm_commands cmpm:health
```

## Integration Benefits

1. **Native Claude Code Experience**: Commands work seamlessly within Claude Code interface
2. **Consistent Branding**: All commands use CMPM prefixes and styling
3. **Framework Integration**: Direct access to existing framework functionality
4. **Rich Output**: Professional dashboard formatting with colors and tables
5. **Error Handling**: Graceful degradation and meaningful error messages

This implementation provides a professional integration between Claude Code's slash command system and the Claude PM Framework, enabling users to access framework functionality directly from the Claude Code interface.