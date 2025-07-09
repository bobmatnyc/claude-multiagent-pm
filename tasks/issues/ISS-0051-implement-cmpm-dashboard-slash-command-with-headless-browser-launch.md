---
issue_id: ISS-0051
epic_id: EP-0032
title: Implement /cmpm-dashboard slash command with headless browser launch
description: Implement /cmpm-dashboard slash command with headless browser launch - comprehensive implementation already exists, focus on integration testing and quality assurance
status: ready
priority: high
assignee: masa
created_date: 2025-07-09T13:51:23.248Z
updated_date: 2025-07-09T17:15:00.000Z
estimated_tokens: 150
actual_tokens: 0
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
related_tasks: []
related_issues: 
  - ISS-0052
completion_percentage: 85
blocked_by: []
blocks: 
  - ISS-0052
---

# Issue: Implement /cmpm-dashboard slash command with headless browser launch

## Description
Implement the `/cmpm-dashboard` slash command to launch the Claude PM Portfolio Manager dashboard in headless browser mode. This command integrates with the existing comprehensive implementation in `cmpm_commands.py` and provides orchestrated access to the portfolio dashboard with automated browser launch capabilities.

## Current Implementation Status
**ANALYSIS COMPLETE** - A comprehensive implementation already exists in `/Users/masa/Projects/claude-multiagent-pm/claude_pm/cmpm_commands.py`:

### Existing CMPMDashboardLauncher Class Features:
- **Dashboard Detection**: Automatically detects if portfolio manager is running on ports 3000, 8080, 8081, or 5173
- **Auto-Start Capability**: Launches portfolio manager using `npm run dev` if not already running
- **Chrome Binary Detection**: Multi-platform Chrome/Chromium binary detection with fallback paths
- **Headless Browser Launch**: Full headless Chrome launch with optimized parameters
- **Process Management**: Proper process lifecycle management with cleanup handlers
- **Signal Handling**: SIGINT/SIGTERM signal handling for graceful shutdown
- **Progress Indicators**: Rich console progress indicators using Rich library
- **Error Handling**: Comprehensive error handling and user feedback
- **Keep-Alive Mode**: Optional foreground mode with process monitoring

### Portfolio Manager Status:
- **Location**: `/Users/masa/Projects/managed/claude-pm-portfolio-manager`
- **Package**: `@bobmatnyc/claude-pm-portfolio-manager@1.0.0`
- **Dev Server**: Vite-based development server (confirmed functional)
- **Build System**: Modern TypeScript/React build pipeline
- **Scripts**: Comprehensive npm scripts for development and deployment

## Tasks
- [ ] **Code Integration Testing** - Verify `/cmpm-dashboard` command integration with existing CLI infrastructure
- [ ] **Chrome Binary Detection Testing** - Test Chrome/Chromium detection across different system configurations
- [ ] **Dashboard Auto-Start Testing** - Verify automatic portfolio manager startup when not running
- [ ] **Headless Browser Launch Testing** - Test headless Chrome launch with various dashboard ports
- [ ] **Process Management Testing** - Verify proper process cleanup and signal handling
- [ ] **Error Scenario Testing** - Test error handling for missing dependencies, port conflicts, etc.
- [ ] **Keep-Alive Mode Testing** - Test foreground mode with process monitoring
- [ ] **CLI Command Registration** - Ensure command is properly registered in main CLI group
- [ ] **Documentation Updates** - Update command documentation and help text
- [ ] **Cross-Platform Testing** - Test on macOS, Linux, and Windows environments

## Acceptance Criteria
- [ ] **Command Accessibility** - `/cmpm-dashboard` command is available in CMPM CLI
- [ ] **Dashboard Auto-Detection** - Automatically detects running portfolio manager on standard ports
- [ ] **Auto-Start Functionality** - Launches portfolio manager if not running using `npm run dev`
- [ ] **Browser Launch Success** - Successfully launches headless Chrome/Chromium pointing to dashboard
- [ ] **Process Management** - Proper cleanup of browser and dashboard processes on exit
- [ ] **Error Handling** - Graceful error handling with informative user messages
- [ ] **Progress Feedback** - Clear progress indicators during dashboard launch process
- [ ] **Signal Handling** - Proper response to SIGINT/SIGTERM for graceful shutdown
- [ ] **Cross-Platform Support** - Works on macOS, Linux, and Windows systems
- [ ] **Documentation Complete** - Updated help text and usage documentation

## Technical Implementation Details

### Command Structure
```python
@click.command(name="cmpm:dashboard")
@click.option('--keep-alive', is_flag=True, help='Keep dashboard running in foreground')
@click.option('--port', type=int, help='Specify dashboard port (auto-detect if not provided)')
def cmpm_dashboard(keep_alive: bool, port: Optional[int]):
    """🚀 /cmpm:dashboard - Launch portfolio manager dashboard in headless browser mode."""
```

### Key Classes and Methods
- **CMPMDashboardLauncher**: Main orchestrator class (already implemented)
- **detect_dashboard_port()**: Port detection logic (already implemented)
- **start_dashboard_if_needed()**: Dashboard startup logic (already implemented)
- **find_chrome_binary()**: Chrome binary detection (already implemented)
- **launch_headless_browser()**: Headless browser launch (already implemented)
- **cleanup_processes()**: Process cleanup logic (already implemented)

### Integration Points
- **CLI Registration**: Command registration in main CLI group
- **Config System**: Integration with Claude PM configuration
- **Service Manager**: Integration with service management infrastructure
- **Health Monitoring**: Integration with health dashboard system

## Dependencies
- **Chrome/Chromium**: Required for headless browser functionality
- **Portfolio Manager**: `@bobmatnyc/claude-pm-portfolio-manager` package
- **Node.js/npm**: Required for running portfolio manager development server
- **Rich Library**: For progress indicators and console output
- **Click**: For CLI command definition and options

## Testing Requirements
- **Unit Tests**: Test individual methods and error scenarios
- **Integration Tests**: Test full command workflow from CLI invocation
- **Cross-Platform Tests**: Verify functionality across operating systems
- **Performance Tests**: Ensure acceptable launch times and resource usage
- **Error Handling Tests**: Test various failure scenarios and recovery

## Notes
**IMPLEMENTATION STATUS**: The core functionality is already fully implemented in `cmpm_commands.py`. This ticket focuses on **integration testing, quality assurance, and deployment verification** rather than new development.

The existing implementation includes sophisticated features like:
- Multi-port dashboard detection
- Automatic portfolio manager startup
- Cross-platform Chrome binary detection
- Headless browser launch with optimized parameters
- Process lifecycle management
- Signal handling for graceful shutdown
- Rich progress indicators
- Comprehensive error handling

**Next Steps**: Focus on testing existing implementation, verifying integration points, and ensuring cross-platform compatibility.
