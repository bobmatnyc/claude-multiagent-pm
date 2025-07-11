# Homebrew Version Management Strategy

## Version Architecture Analysis

### Current Version Structure
The project maintains a dual-version system:

1. **Package Version (0.4.6)**: Used for actual software releases
   - `package.json` → 0.4.6
   - `pyproject.toml` → 0.4.6  
   - `VERSION` → 0.4.6
   - `claude_pm/__init__.py` → 0.4.6
   - All QA service files → 0.4.6

2. **Framework Version (4.5.1)**: Used for internal framework evolution
   - `CLAUDE.md` metadata → 4.5.1
   - Documentation versioning → 4.5.1
   - Deployment configuration → 4.5.1

## Version Consistency Status: ✅ COMPLETE

### Core Package Files (All Aligned to 0.4.6)
- ✅ `/VERSION` → 0.4.6
- ✅ `/package.json` → 0.4.6  
- ✅ `/package-lock.json` → 0.4.6
- ✅ `/pyproject.toml` → 0.4.6
- ✅ `/claude_pm/__init__.py` → 0.4.6
- ✅ `/README.md` → v0.4.6 (all references)
- ✅ `/install/README.md` → 0.4.6

### QA Service Files (All Aligned to 0.4.6)
- ✅ `/cmpm-qa/service/qa_service.py` → 0.4.6
- ✅ `/cmpm-qa/extension/manifest.json` → 0.4.6
- ✅ `/cmpm-qa/native-host/native_host.py` → 0.4.6

### Framework Files (Intentionally Different - 4.5.1)
- ✅ `/framework/CLAUDE.md` → 4.5.1 (framework version)
- ✅ `/docs/*` → 4.5.1 (documentation framework version)

## Homebrew Packaging Readiness

### 1. Version Source Strategy
For Homebrew formula creation, use:
```ruby
class ClaudeMultiagentPm < Formula
  desc "Claude Multi-Agent Project Management Framework"
  homepage "https://github.com/masa/claude-multiagent-pm"
  url "https://github.com/masa/claude-multiagent-pm/archive/v#{version}.tar.gz"
  version "0.4.6"  # Always use package version, not framework version
end
```

### 2. Version Detection Script
Create `scripts/get-version.sh`:
```bash
#!/bin/bash
# Get the current package version for Homebrew
cat VERSION
```

### 3. Release Tagging Strategy
- **Git Tags**: Use package version (v0.4.6)
- **Release Notes**: Reference both versions clearly
- **Archive URLs**: Point to package version tags

### 4. Homebrew Formula Version Management
```ruby
# Use the VERSION file as the single source of truth
version File.read("VERSION").strip

# Validation in formula
if version != File.read("package.json").match(/"version":\s*"([^"]+)"/)[1]
  raise "Version mismatch between VERSION file and package.json"
end
```

## Version Management Best Practices

### 1. Single Source of Truth
- **Primary**: `/VERSION` file (0.4.6)
- **Synchronized**: All package files must match VERSION file
- **Independent**: Framework documentation can use separate versioning

### 2. Release Process
1. Update `/VERSION` file
2. Run version sync script to update all package files
3. Create git tag with package version
4. Update Homebrew formula
5. Update framework documentation separately if needed

### 3. Validation Commands
```bash
# Verify version consistency
python3 -c "import claude_pm; print(claude_pm.__version__)"  # Should output 0.4.6
node -e "console.log(require('./package.json').version)"     # Should output 0.4.6
cat VERSION                                                  # Should output 0.4.6
```

## Conclusion

✅ **Version Consistency**: All package files are properly aligned to 0.4.6
✅ **Homebrew Ready**: Version management follows Homebrew best practices
✅ **Dual Architecture**: Package versions (0.4.6) separate from framework versions (4.5.1)
✅ **Release Strategy**: Clear git tagging and formula management approach

The project is **100% ready for Homebrew packaging** with consistent version management across all critical package files.