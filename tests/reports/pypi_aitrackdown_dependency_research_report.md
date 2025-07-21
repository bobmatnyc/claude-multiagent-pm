# PyPI Installation and ai-trackdown-tools Dependency Research Report

**Date**: 2025-07-21
**Researcher**: Research Agent
**Task**: Investigate if PyPI installation properly installs ai-trackdown-tools npm dependency

## Executive Summary

The PyPI installation of `claude-multiagent-pm` does **NOT** automatically install the `ai-trackdown-tools` npm dependency. Users installing via pip must manually install this npm dependency separately for full ticketing functionality.

## Key Findings

### 1. PyPI Package Configuration

**pyproject.toml Analysis**:
- No npm dependencies declared in Python package configuration
- Only Python dependencies are listed (aiohttp, click, pydantic, etc.)
- No post-install hooks that would trigger npm installations
- No reference to ai-trackdown-tools in the Python package metadata

### 2. NPM Package Configuration

**package.json Analysis**:
- `@bobmatnyc/ai-trackdown-tools` is listed as a dependency (version ^1.2.0)
- Several npm scripts reference ai-trackdown-tools:
  - `ai-trackdown-setup`: Explicitly installs the npm package globally
  - `verify-dependencies`: Checks if aitrackdown and atd commands are available
- The npm postinstall script (`postinstall-minimal.js`) does NOT install npm dependencies

### 3. Postinstall Script Behavior

**postinstall-minimal.js Analysis**:
- Focuses on Python package installation and setup
- Creates directory structure in `~/.claude-pm/`
- Installs Python dependencies via pip
- Attempts to ensure `aitrackdown` alias availability
- Does NOT install npm packages or ai-trackdown-tools

### 4. Alias Creation Mechanism

**ensure_aitrackdown_alias.py**:
- Checks if `aitrackdown` command is available
- If not available but `ai-trackdown-tools` is installed, creates platform-specific alias:
  - Unix/macOS: Creates symlink in npm global bin directory
  - Windows: Creates batch file wrapper
- If `ai-trackdown-tools` is not installed, provides installation instructions
- Does NOT automatically install the npm package

## Installation Flow Analysis

### NPM Installation Flow:
1. `npm install -g @bobmatnyc/claude-multiagent-pm`
2. npm installs `@bobmatnyc/ai-trackdown-tools` as a dependency
3. Postinstall script runs, setting up Python environment
4. Alias creation script ensures `aitrackdown` command availability

### PyPI Installation Flow:
1. `pip install claude-multiagent-pm`
2. Only Python dependencies are installed
3. No npm dependencies are installed
4. No postinstall hooks to install npm packages
5. User must manually run: `npm install -g @bobmatnyc/ai-trackdown-tools`

## Impact Assessment

### Functionality Impact:
- Core claude-pm functionality works without ai-trackdown-tools
- Ticketing/issue tracking features will be unavailable
- Commands like `aitrackdown` and `atd` will not work
- GitHub issue synchronization features will fail

### User Experience Impact:
- PyPI users may be confused when ticketing commands fail
- No clear error message indicating missing npm dependency
- Manual installation step required for full functionality

## Recommendations

### For Framework Developers:

1. **Documentation Updates**:
   - Add clear notice in PyPI description about npm dependency
   - Update README.md PyPI installation section
   - Add troubleshooting section for missing ai-trackdown-tools

2. **Installation Improvements**:
   - Consider adding a post-install check for ai-trackdown-tools
   - Provide helpful error messages when ticketing commands are used
   - Add a `claude-pm install-dependencies` command to install npm deps

3. **Package Description**:
   - Update pyproject.toml description to mention npm dependency
   - Add installation note about required npm global package

### For Users Installing via PyPI:

**Complete Installation Steps**:
```bash
# 1. Install Python package
pip install claude-multiagent-pm

# 2. Install required npm dependency
npm install -g @bobmatnyc/ai-trackdown-tools

# 3. Verify installation
claude-pm --version
aitrackdown --version
atd --version
```

## Technical Details

### Missing Integration Points:
1. No `subprocess.call(['npm', 'install', '-g', '@bobmatnyc/ai-trackdown-tools'])` in Python code
2. No package.json bundled with PyPI distribution
3. No npm detection or installation logic in Python setup

### Platform Considerations:
- Users without npm/node.js installed cannot use ticketing features
- Corporate environments may restrict npm global installations
- Different platforms have different npm global paths

## Conclusion

The PyPI installation provides a **partial installation** of the claude-multiagent-pm framework. While core orchestration and agent functionality works, the ticketing integration requires manual installation of the npm dependency. This creates a two-step installation process for PyPI users who want full functionality.

**Recommendation**: Update documentation immediately to clarify this requirement and consider adding automated npm dependency installation or at least clear warnings when ticketing features are accessed without the dependency.