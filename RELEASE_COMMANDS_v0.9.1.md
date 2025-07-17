# Release Commands for v0.9.1

## 🚀 Ready to Release!

The v0.9.1 release has been prepared with:
- ✅ CHANGELOG.md updated with comprehensive release notes
- ✅ All version files showing 0.9.1
- ✅ Release commit created
- ✅ All tests passing (100% success rate)
- ✅ Framework imports resolved

## 📋 Execute these commands to complete the release:

### 1. Create Git Tag
```bash
git tag -a v0.9.1 -m "Release v0.9.1: Import Resolution and Agent System Restoration

Critical patch release that resolves CRITICAL-001 by restoring the missing
framework_agent_loader.py module.

Key fixes:
- Restored missing framework_agent_loader.py (322 lines)
- Fixed 20 test import failures (now 100% passing)
- Restored agent profile loading functionality
- Cleaned up development backup directories"
```

### 2. Push to GitHub
```bash
# Push the commits
git push origin main

# Push the tag
git push origin v0.9.1
```

### 3. Publish to NPM
```bash
# Ensure you're logged in to npm
npm whoami

# If not logged in:
# npm login

# Publish the package
npm publish
```

### 4. Create GitHub Release
1. Go to https://github.com/[your-username]/claude-multiagent-pm/releases/new
2. Select the `v0.9.1` tag
3. Title: "v0.9.1: Import Resolution and Agent System Restoration"
4. Copy the CHANGELOG.md content for v0.9.1 into the release description
5. Mark as "Latest release"
6. Publish release

## 🎯 Post-Release Verification

After publishing, verify the release:

```bash
# Check npm package
npm view @bobmatnyc/claude-multiagent-pm@0.9.1

# Test installation
cd /tmp && mkdir test-0.9.1 && cd test-0.9.1
npm install @bobmatnyc/claude-multiagent-pm@0.9.1
npx claude-pm --version  # Should show 0.9.1
```

## 📊 Release Summary

**Version**: 0.9.1  
**Type**: Critical Patch Release  
**Key Fix**: Restored missing framework_agent_loader.py module  
**Impact**: Resolved 20 test failures, restored agent system functionality  
**Status**: Ready for production deployment  