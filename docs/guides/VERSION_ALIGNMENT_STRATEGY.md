# Version Alignment Strategy

## Overview
This document outlines the version management strategy for the Claude Multi-Agent PM Framework to prevent version misalignment issues.

## Version Alignment Requirements

### Main Version Sources (Must Be Synchronized)
1. **package.json** - Primary NPM package version
2. **VERSION** - Framework root version reference  
3. **claude_pm/_version.py** - Python package version
4. **claude_pm/__init__.py** - Python package initialization version

### Independent Version Sources (Separate Versioning)
1. **framework/VERSION** - Framework template version (tracks template changes)
2. **bin/VERSION** - CLI script version (tracks script changes)

## Version Alignment Process

### Pre-Release Checklist
1. Identify target version for release
2. Update all main version sources to target version
3. Verify independent versions are appropriate for their components
4. Run version alignment validation
5. Document version changes

### Version Update Commands
```bash
# Update package.json version
sed -i 's/"version": "[^"]*"/"version": "X.Y.Z"/' package.json

# Update VERSION file
echo "X.Y.Z" > VERSION

# Update Python version files
sed -i 's/__version__ = "[^"]*"/__version__ = "X.Y.Z"/' claude_pm/_version.py
sed -i 's/__version__ = "[^"]*"/__version__ = "X.Y.Z"/' claude_pm/__init__.py
```

### Validation Commands
```bash
# Verify alignment
echo "package.json:" && grep '"version"' package.json | head -1
echo "VERSION:" && cat VERSION  
echo "_version.py:" && grep "__version__" claude_pm/_version.py
echo "__init__.py:" && grep "__version__" claude_pm/__init__.py
```

## Versioning Strategy

### Semantic Versioning (SemVer)
- **Major (X.0.0)**: Breaking API changes
- **Minor (0.Y.0)**: New features, significant improvements
- **Patch (0.0.Z)**: Bug fixes, minor improvements

### Recent Version History
- **0.7.0**: QA cleanup, documentation reorganization, version alignment
- **0.6.4**: Enhanced flags system, NPM installation improvements  
- **0.6.1**: Framework enhancements, memory management

## Common Issues and Solutions

### Issue: Version Misalignment
**Symptoms**: Different version numbers across main version sources
**Solution**: Follow version alignment process to synchronize all main sources

### Issue: Dependency Confusion
**Symptoms**: Package managers or tools reporting different versions
**Solution**: Ensure all main version sources are aligned before release

### Issue: Release Validation Failures
**Symptoms**: QA validation fails due to version inconsistencies
**Solution**: Run version alignment validation as part of pre-release process

## Automation Recommendations

1. **Pre-commit hooks**: Validate version consistency before commits
2. **CI/CD validation**: Check version alignment in pipeline
3. **Automated updates**: Script to update all version sources simultaneously
4. **Release automation**: Integrate version alignment into release process

## Notes

- Framework and script versions remain independent as they track different components
- All main version sources must be synchronized for consistent releases
- Version alignment is critical for QA validation and release processes