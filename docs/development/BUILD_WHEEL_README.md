# Building Python Wheels for claude-multiagent-pm

This document describes the wheel building infrastructure implemented for ISS-0163 Phase 1.

## Overview

The Python wheel building system ensures that all framework files, including the critical `framework/CLAUDE.md`, are properly packaged and distributed with the claude-multiagent-pm package.

## Key Components

### 1. **pyproject.toml** Configuration
- Updated to version 1.2.3
- Includes comprehensive package-data configuration
- Uses setuptools >= 68.0 for modern build features
- Properly configured to include all markdown, yaml, and json files

### 2. **MANIFEST.in**
- Ensures source distributions include all necessary files
- Includes the framework directory using `graft framework`
- Includes the claude_pm/data directory for wheel builds

### 3. **Package Data Structure**
- Framework files are copied to `claude_pm/data/framework/` during build
- This ensures framework files are included within the Python package
- Accessible via `importlib.resources` in Python 3.9+

### 4. **Build Scripts**

#### a. `scripts/build_wheel.py`
- Comprehensive Python script for building and testing wheels
- Validates wheel contents
- Tests installation in isolated environment
- Provides detailed logging

#### b. `scripts/build_and_deploy_wheel.sh`
- Simple bash script for quick builds
- Handles cleanup and verification
- Provides deployment instructions

#### c. `scripts/verify_wheel.py`
- Standalone verification script
- Checks for required files and patterns
- Validates minimum file counts

#### d. `scripts/test_wheel_installation.py`
- Tests wheel installation in virtual environment
- Verifies imports and framework data access
- Tests CLI entry points

### 5. **scripts/build_config.py**
- Documents build configuration
- Provides programmatic access to build settings
- Can be used for automated build processes

## Building a Wheel

### Quick Build
```bash
# Using bash script
./scripts/build_and_deploy_wheel.sh

# Or using Python directly
python -m build --wheel
```

### Full Build with Testing
```bash
# Run the comprehensive build script
python scripts/build_wheel.py
```

### Manual Build Steps
```bash
# 1. Clean previous builds
rm -rf build dist *.egg-info

# 2. Ensure framework data is in place
mkdir -p claude_pm/data
cp -r framework claude_pm/data/

# 3. Build the wheel
python -m build --wheel

# 4. Verify the wheel
python scripts/verify_wheel.py
```

## Verifying Wheel Contents

The built wheel should contain:
- 280+ Python files
- 40+ Markdown documentation files
- Complete framework directory under `claude_pm/data/framework/`
- All agent role definitions
- All service documentation

### Critical Files
The following files MUST be present in the wheel:
- `claude_pm/__init__.py`
- `claude_pm/cli.py`
- `claude_pm/data/framework/CLAUDE.md`
- `claude_pm/data/framework/VERSION`
- `claude_pm/data/framework/agent-roles/base_agent.md`

## Installation

### From Built Wheel
```bash
pip install dist/claude_multiagent_pm-1.2.3-py3-none-any.whl
```

### Testing Installation
```bash
# Test in isolated environment
python scripts/test_wheel_installation.py

# Or manually
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
pip install dist/claude_multiagent_pm-1.2.3-py3-none-any.whl
python -c "import claude_pm; print(claude_pm.__version__)"
```

## Accessing Framework Data

After installation, framework data can be accessed programmatically:

```python
from importlib import resources

# Access framework CLAUDE.md
framework_data = resources.files('claude_pm') / 'data' / 'framework'
claude_md = framework_data / 'CLAUDE.md'

with claude_md.open('r') as f:
    content = f.read()
```

## Deployment to PyPI

Once the wheel is built and verified:

```bash
# Install twine if not already installed
pip install twine

# Upload to PyPI (requires credentials)
python -m twine upload dist/claude_multiagent_pm-1.2.3-py3-none-any.whl
```

## Troubleshooting

### Missing Framework Files
If framework files are missing from the wheel:
1. Ensure `claude_pm/data/framework/` exists and contains files
2. Check that `pyproject.toml` includes `"data/framework/**/*"` in package-data
3. Rebuild with clean build directory

### Import Errors
If imports fail after installation:
1. Check Python version compatibility (requires >= 3.9)
2. Ensure all dependencies are installed
3. Verify wheel was built from correct source directory

### Version Mismatches
Ensure version consistency across:
- `pyproject.toml`
- `VERSION` file
- `claude_pm/__version__.py` (if exists)

## Summary

The wheel building infrastructure ensures that claude-multiagent-pm can be properly packaged and distributed with all necessary framework files. The build process is automated, verified, and reproducible, making it suitable for both development and production deployments.