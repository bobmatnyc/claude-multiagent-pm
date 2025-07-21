# PyPI Publication Guide for Claude Multi-Agent PM

## Overview

This guide covers the complete process for publishing the `claude-multiagent-pm` package to PyPI (Python Package Index). The framework includes automated tools and workflows to ensure safe and reliable package publication.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Publication Checklist](#pre-publication-checklist)
3. [Local Testing](#local-testing)
4. [Test PyPI Publication](#test-pypi-publication)
5. [Production PyPI Publication](#production-pypi-publication)
6. [GitHub Actions Workflow](#github-actions-workflow)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Prerequisites

### Required Tools

Before publishing, ensure you have the following tools installed:

```bash
# Install required packages
pip install build twine wheel setuptools setuptools-scm

# Verify installations
python -m build --version
twine --version
```

### API Tokens

You'll need API tokens for both Test PyPI and PyPI:

1. **Test PyPI Token**: https://test.pypi.org/manage/account/token/
2. **PyPI Token**: https://pypi.org/manage/account/token/

Store these tokens securely:
- For local use: Set environment variables `TWINE_TEST_TOKEN` and `TWINE_TOKEN`
- For GitHub Actions: Add as repository secrets `TEST_PYPI_API_TOKEN` and `PYPI_API_TOKEN`

## Pre-Publication Checklist

Run the comprehensive pre-publication checklist to ensure everything is ready:

```bash
# Run all pre-publication checks
python scripts/pre_publication_checklist.py
```

This script validates:
- ✅ Version consistency across all files
- ✅ CHANGELOG.md contains entry for current version
- ✅ All required files exist (README.md, LICENSE, etc.)
- ✅ Package metadata is complete
- ✅ Build tools are installed
- ✅ Code quality checks pass
- ✅ Test suite passes
- ✅ Distribution files can be built

### Manual Checks

Additionally, manually verify:
1. All new features are documented
2. Breaking changes are clearly noted
3. Dependencies are up to date
4. Security vulnerabilities are addressed

## Local Testing

### 1. Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
python -m build

# Verify built files
ls -la dist/
```

### 2. Validate Package

```bash
# Check package with twine
twine check dist/*

# Test wheel installation locally
pip install dist/claude_multiagent_pm-*.whl

# Verify it works
python -c "import claude_pm; print(claude_pm.__version__)"
claude-pm --version
```

## Test PyPI Publication

Always test on Test PyPI before publishing to production:

### 1. Publish to Test PyPI

```bash
# Publish to Test PyPI (will prompt for token if not in environment)
python scripts/publish_to_pypi.py

# Or with explicit token
TWINE_TEST_TOKEN=your-test-token python scripts/publish_to_pypi.py
```

### 2. Validate Test PyPI Installation

```bash
# Test installation from Test PyPI
python scripts/test_pypi_installation.py

# Test specific version
python scripts/test_pypi_installation.py --version 1.2.3

# Keep test environment for debugging
python scripts/test_pypi_installation.py --keep-env
```

The validation script will:
- Create a clean virtual environment
- Install from Test PyPI
- Test imports and basic functionality
- Verify CLI commands work
- Run integration tests

### 3. Manual Testing

After automated tests, manually verify:

```bash
# Create a new virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from Test PyPI
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ claude-multiagent-pm

# Test the installation
claude-pm --version
claude-pm init
python -c "from claude_pm.core import ServiceManager; print('Import successful')"
```

## Production PyPI Publication

Once Test PyPI validation passes:

### 1. Final Checks

```bash
# Run pre-publication checklist one more time
python scripts/pre_publication_checklist.py

# Ensure you're on the correct branch
git status
git log --oneline -5
```

### 2. Publish to PyPI

```bash
# Publish to production PyPI
python scripts/publish_to_pypi.py --production

# Or with explicit token
TWINE_TOKEN=your-pypi-token python scripts/publish_to_pypi.py --production
```

### 3. Verify Production Installation

```bash
# Wait a few minutes for PyPI to update, then test
pip install claude-multiagent-pm==1.2.3  # Use specific version
claude-pm --version
```

## GitHub Actions Workflow

The repository includes an automated GitHub Actions workflow for releases.

### Manual Trigger

1. Go to Actions → "Publish to PyPI" workflow
2. Click "Run workflow"
3. Choose options:
   - `test_pypi`: true (default) or false
   - `version_override`: leave empty or specify version

### Automatic Release Trigger

Create a GitHub release to automatically publish:

```bash
# Tag the release
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# Create release on GitHub
# This will trigger automatic PyPI publication
```

### Workflow Configuration

The workflow (`pypi-publish.yml`) handles:
- Building distribution files
- Running package validation
- Publishing to Test PyPI or PyPI
- Attaching artifacts to GitHub releases

## Troubleshooting

### Common Issues

#### 1. Version Already Exists

```
ERROR: File already exists: claude-multiagent-pm-1.2.3.tar.gz
```

**Solution**: Increment version in `pyproject.toml` and related files.

#### 2. Authentication Failed

```
ERROR: Invalid or non-existent authentication information
```

**Solution**: Check your API token and ensure it's set correctly:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=your-token-here
```

#### 3. Package Validation Failed

```
ERROR: The long_description has invalid markup
```

**Solution**: Run `twine check dist/*` and fix any markup issues in README.md.

#### 4. Import Errors After Installation

**Solution**: Ensure all dependencies are listed in `pyproject.toml` and test in a clean environment.

### Debug Commands

```bash
# Verbose twine upload
twine upload --verbose dist/*

# Check package metadata
python -m build --help
twine check --help

# Inspect built wheel
unzip -l dist/*.whl | head -20
```

## Best Practices

### 1. Version Management

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in all required files simultaneously
- Document all changes in CHANGELOG.md

### 2. Testing Protocol

- Always test on Test PyPI first
- Run full test suite before publishing
- Test installation in clean environments
- Verify both pip and CLI functionality

### 3. Security

- Never commit tokens to version control
- Use API tokens, not passwords
- Rotate tokens periodically
- Use GitHub secrets for CI/CD

### 4. Documentation

- Update README.md with new features
- Keep CHANGELOG.md current
- Document breaking changes prominently
- Update installation instructions if needed

### 5. Release Process

1. Create feature branch for release prep
2. Update version numbers
3. Update CHANGELOG.md
4. Run pre-publication checks
5. Create pull request
6. After merge, tag release
7. Let GitHub Actions handle publication

## Quick Reference

```bash
# Pre-publication check
python scripts/pre_publication_checklist.py

# Build package
python -m build

# Test PyPI publication
python scripts/publish_to_pypi.py

# Validate Test PyPI
python scripts/test_pypi_installation.py

# Production publication
python scripts/publish_to_pypi.py --production

# Manual Test PyPI install
pip install -i https://test.pypi.org/simple/ claude-multiagent-pm

# Manual PyPI install
pip install claude-multiagent-pm
```

## Support

For issues with publication:
1. Check this guide first
2. Review error messages carefully
3. Test in isolated environments
4. Check PyPI status page
5. Open an issue if problems persist

Remember: It's always better to be cautious with package publication. Test thoroughly before releasing to production PyPI!