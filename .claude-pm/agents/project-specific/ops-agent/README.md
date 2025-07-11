# Claude-MultiAgent-PM Ops Agent

## Overview
Project-specific operations agent with comprehensive knowledge of the claude-multiagent-pm framework architecture, deployment processes, and local development workflows.

## Agent Information
- **Name**: claude-multiagent-pm-ops-agent
- **Version**: 1.0.0
- **Type**: project-specific
- **Tier**: project (highest priority in three-tier hierarchy)
- **Framework Version**: 4.5.1
- **Authority Level**: project-deployment
- **Created**: 2025-07-11

## Core Capabilities

### Deployment Operations
- **Full Deployment**: Complete framework deployment with all components
- **Incremental Sync**: Synchronize changes without full redeployment
- **Script Synchronization**: Deploy and sync scripts with validation
- **Binary Deployment**: Deploy CLI tools and executable components
- **CLAUDE.md Management**: Deploy configuration with variable substitution

### Diagnostic Operations
- **Comprehensive Diagnostics**: Advanced system health analysis
- **Health Monitoring**: Quick health status checks
- **Integration Validation**: External service connectivity testing
- **Performance Analysis**: System performance metrics and optimization
- **Troubleshooting**: Automated issue detection and resolution recommendations

### Knowledge Management
- **Framework Architecture**: Deep understanding of claude-multiagent-pm structure
- **Deployment Processes**: Expert knowledge of local development workflows
- **Integration Points**: Comprehensive understanding of external integrations
- **Best Practices**: Operational guidelines and optimization strategies

## Directory Structure
```
ops-agent/
├── config/
│   └── agent-definition.yaml      # Agent configuration and metadata
├── automation/
│   ├── full-deployment.py         # Complete deployment automation
│   └── incremental-sync.py        # Incremental synchronization
├── diagnostics/
│   └── comprehensive-diagnostics.py # Advanced diagnostic procedures
├── knowledge/
│   └── framework-architecture.md   # Framework knowledge base
├── ops-agent.py                    # Main agent interface
└── README.md                       # This file
```

## Usage Examples

### Basic Operations
```bash
# Display agent information
python ops-agent.py info

# Show system status
python ops-agent.py status

# Run comprehensive diagnostics
python ops-agent.py diagnose

# Access knowledge base
python ops-agent.py knowledge
python ops-agent.py knowledge framework-architecture
```

### Deployment Operations
```bash
# Execute full deployment
python ops-agent.py deploy-full

# Run incremental synchronization
python ops-agent.py deploy-incremental

# Show available operations
python ops-agent.py help
```

### Integration with Framework
This agent integrates with the three-tier agent hierarchy:
1. **Project Level** (this agent) - Highest priority
2. **User Level** - User-specific customizations
3. **System Level** - Framework defaults

The agent can be invoked via the Task Tool for delegation from the main PM orchestrator.

## Framework Integration Points

### Memory System (mem0AI v0.1.113)
- Context-aware memory management
- Cross-session learning and adaptation
- Performance-optimized memory operations

### AI-Trackdown Tools
- Universal ticketing interface
- Issue tracking and resolution
- Performance monitoring integration

### Three-Tier Agent Hierarchy
- Project-specific overrides and customizations
- User-level fallback capabilities
- System-level core functionality

### CLAUDE.md Deployment Tree
- Template-based deployment with variable substitution
- Multi-target deployment management
- Automatic backup and rollback capabilities

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure Python path includes project root
2. **Permission Issues**: Check script and binary execution permissions
3. **Sync Failures**: Verify source/target directory accessibility
4. **Integration Issues**: Validate external service connectivity

### Diagnostic Reports
The agent generates comprehensive diagnostic reports in:
- `/logs/comprehensive-diagnostics-report.json`
- `/logs/ops-agent-deployment.log`
- `/logs/ops-agent-sync.log`
- `/logs/ops-agent-diagnostics.log`

### Support
For issues specific to this agent:
1. Run comprehensive diagnostics: `python ops-agent.py diagnose`
2. Check logs in the project's `logs/` directory
3. Review framework knowledge base: `python ops-agent.py knowledge`
4. Validate agent hierarchy: `python ~/.claude/commands/cmpm-bridge.py cmcp-init --verify`

## Development Notes

### Extension Points
- Add new automation scripts in `automation/`
- Expand diagnostic procedures in `diagnostics/`
- Add knowledge topics in `knowledge/`
- Update agent configuration in `config/`

### Best Practices
- Always run diagnostics after making changes
- Use incremental sync for routine updates
- Maintain comprehensive logging for troubleshooting
- Test integrations after framework updates

## Version History
- **v1.0.0** (2025-07-11): Initial implementation with full deployment, sync, and diagnostic capabilities