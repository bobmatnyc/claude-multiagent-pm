# NPM vs PIP Installation Comparison for claude-multiagent-pm

## Summary

Based on my research, **pip does NOT create all the same scripts as npm**. There are significant differences in what each package manager installs.

## NPM Installation

When installed via `npm install -g @bobmatnyc/claude-multiagent-pm`, NPM creates the following:

### Primary Script
- `/Users/masa/.nvm/versions/node/v20.19.0/bin/claude-pm` → symlink to `../lib/node_modules/@bobmatnyc/claude-multiagent-pm/bin/claude-pm`

### What NPM Does
1. Creates a symlink in the global npm bin directory pointing to `bin/claude-pm`
2. The `bin/claude-pm` is the actual Python script (96KB) with full functionality
3. Only installs the script specified in package.json's `bin` field

### Additional Scripts in the Package
The package contains these scripts in the `bin/` directory:
- `claude-pm` - Main CLI script (Python)
- `cmpm` - Alternative command wrapper
- `aitrackdown` - AI Trackdown integration
- `atd` - Shortcut for aitrackdown
- `claude-pm.cmd` - Windows batch file

**However, NPM only installs `claude-pm` because that's what's specified in package.json:**
```json
"bin": {
  "claude-pm": "./bin/claude-pm"
}
```

## PIP Installation

When installed via `pip install claude-multiagent-pm`, pip creates the following scripts based on `pyproject.toml`:

### Scripts Created by PIP
- `/Users/masa/Library/Python/3.13/bin/claude-pm` - Entry point wrapper (240 bytes)
- `/Users/masa/Library/Python/3.13/bin/claude-multiagent-pm` - Same functionality
- `/Users/masa/Library/Python/3.13/bin/claude-multiagent-pm-health` - Health monitoring
- `/Users/masa/Library/Python/3.13/bin/claude-multiagent-pm-service` - Service manager

### PIP Script Structure
PIP creates small wrapper scripts that look like:
```python
#!/opt/homebrew/opt/python@3.13/bin/python3.13
# -*- coding: utf-8 -*-
import re
import sys
from claude_pm.cli import main
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
```

## Key Differences

### 1. Script Installation
- **NPM**: Only installs `claude-pm` (the actual 96KB Python script)
- **PIP**: Installs 4 console scripts as defined in `pyproject.toml`:
  - `claude-pm`
  - `claude-multiagent-pm`
  - `claude-multiagent-pm-health`
  - `claude-multiagent-pm-service`

### 2. Script Type
- **NPM**: Installs the actual Python script directly
- **PIP**: Creates small wrapper scripts that import and call Python functions

### 3. Missing Scripts
PIP does NOT install:
- `cmpm` - The alternative command wrapper
- `aitrackdown` - AI Trackdown integration
- `atd` - Shortcut for aitrackdown

### 4. Additional Scripts
PIP installs these additional scripts not available via NPM:
- `claude-multiagent-pm-health` - For health monitoring
- `claude-multiagent-pm-service` - For service management

## Recommendations

To achieve parity between npm and pip installations:

### Option 1: Update package.json
Add all desired scripts to the `bin` field:
```json
"bin": {
  "claude-pm": "./bin/claude-pm",
  "cmpm": "./bin/cmpm",
  "aitrackdown": "./bin/aitrackdown",
  "atd": "./bin/atd"
}
```

### Option 2: Update pyproject.toml
Remove the extra console scripts that npm doesn't install:
```toml
[project.scripts]
claude-pm = "claude_pm.cli:main"
# Remove these if not needed:
# claude-multiagent-pm = "claude_pm.cli:main"
# claude-multiagent-pm-health = "claude_pm.scripts.health_monitor:main"
# claude-multiagent-pm-service = "claude_pm.scripts.service_manager:main"
```

### Option 3: Manual Installation
Users can manually copy the additional scripts from the `bin/` directory to their PATH.

## Current State

As of now:
- **NPM users** get only `claude-pm`
- **PIP users** get `claude-pm`, `claude-multiagent-pm`, plus health and service scripts
- Neither installation method provides `cmpm`, `aitrackdown`, or `atd` automatically