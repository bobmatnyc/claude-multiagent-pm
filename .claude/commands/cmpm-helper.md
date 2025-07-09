# CMPM Command Helper

Helper script to execute Claude PM Framework commands via Claude Code slash commands.

## Instructions

This helper facilitates the execution of CMPM framework commands through Claude Code's slash command interface.

### Available Commands

Execute any of the following CMPM framework commands:

1. **Health Dashboard** (`/project:cmpm-health`)
   - Execute: `python .claude/commands/cmpm-bridge.py health`
   - Provides comprehensive system health dashboard

2. **Agents Registry** (`/project:cmpm-agents`)
   - Execute: `python .claude/commands/cmpm-bridge.py agents`
   - Lists all active agent types and status

3. **Project Index** (`/project:cmpm-index`)
   - Execute: `python .claude/commands/cmpm-bridge.py index`
   - Generates comprehensive project discovery index

### Direct CLI Integration

For direct CLI access (without Claude Code):

```bash
# Health dashboard
python -m claude_pm.cmpm_commands cmpm:health

# Agents registry  
python -m claude_pm.cmpm_commands cmpm:agents

# Project index
python -m claude_pm.cmpm_commands cmpm:index
```

### Framework Integration

These commands integrate with the existing Claude PM Framework:
- Use existing `CMPMHealthMonitor`, `CMPMAgentMonitor`, and `CMPMIndexOrchestrator` classes
- Leverage ai-trackdown-tools integration
- Support Rich console formatting and output
- Include mem0AI integration status

Execute the desired command using the bridge script or direct CLI access.