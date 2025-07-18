# Release Documentation

[← Back to Documentation Home](../README.md) | [Documentation Index](../index.md)

This section contains release notes, changelogs, and version history for the Claude Multi-Agent PM framework.

## 📦 Current Release

### Latest Stable: v0.7.0
- **Release Date**: January 2025
- **[Release Notes](./v0.7.0/README.md)**
- **[Changelog](./v0.7.0/CHANGELOG.md)**
- **[Migration Guide](./migration/v0.6-to-v0.7.md)**

### Quick Links
- **[Download Latest](https://www.npmjs.com/package/@bobmatnyc/claude-multiagent-pm)**
- **[Installation Guide](../user/getting-started/installation.md)**
- **[What's New in v0.7.0](./v0.7.0/whats-new.md)**

## 🔄 Release History

### Active Releases

#### [v0.7.x Series](./v0.7.0/README.md) - Current Stable
- **Status**: Active Development
- **Support**: Full support with regular updates
- **Key Features**: 
  - Enhanced agent orchestration
  - Improved performance (99.7% faster)
  - New agent registry system
  - Better error handling

#### [v0.6.x Series](./archive/v0.6.x/README.md) - Previous Stable
- **Status**: Maintenance Mode
- **Support**: Security fixes only until 2025-12-31
- **Key Features**:
  - Multi-project support
  - Agent hierarchy system
  - Basic orchestration

### [Release Archive](./archive/README.md)
Historical releases (no longer supported):

- **[v0.5.x Series](./archive/v0.5.x/README.md)** - EOL June 2025
- **[v0.4.x Series](./archive/v0.4.x/README.md)** - Unsupported
- **[Earlier Versions](./archive/legacy/README.md)** - Historical reference

## 📋 Release Documentation Structure

Each release includes:

### Release Notes
- **Overview**: High-level summary of the release
- **New Features**: Major functionality additions
- **Improvements**: Enhancements to existing features
- **Bug Fixes**: Resolved issues with references
- **Breaking Changes**: Changes requiring code updates
- **Deprecations**: Features marked for future removal

### Changelog
- Detailed list of all changes
- Commit references
- Contributor acknowledgments
- Following [Keep a Changelog](https://keepachangelog.com/) format

### Migration Guide
- Step-by-step upgrade instructions
- Breaking change handling
- Code migration examples
- Rollback procedures

## 🚀 Upgrading

### Quick Upgrade Commands

```bash
# Check current version
claude-pm --version

# Update to latest
npm update -g @bobmatnyc/claude-multiagent-pm

# Verify upgrade
claude-pm --version
```

### Migration Guides

- **[v0.6.x to v0.7.0](./migration/v0.6-to-v0.7.md)** - Current migration
- **[v0.5.x to v0.6.x](./migration/v0.5-to-v0.6.md)** - Legacy migration
- **[General Best Practices](./migration/best-practices.md)** - Upgrade tips

### Pre-Upgrade Checklist

1. ✅ Review breaking changes
2. ✅ Backup your projects
3. ✅ Test in development first
4. ✅ Update dependencies
5. ✅ Run migration scripts

## 📊 Version Support Matrix

| Version | Release Date | Status | Support Until | Node.js | Python |
|---------|--------------|--------|---------------|---------|--------|
| v0.7.x | Jan 2025 | **Current** | Active | ≥16.0 | ≥3.8 |
| v0.6.x | Oct 2024 | Maintenance | Dec 2025 | ≥14.0 | ≥3.7 |
| v0.5.x | Jun 2024 | EOL | Jun 2025 | ≥14.0 | ≥3.7 |
| v0.4.x | Mar 2024 | Unsupported | - | ≥12.0 | ≥3.6 |
| < v0.4 | - | Unsupported | - | - | - |

### Support Levels

- **Active**: New features, improvements, and bug fixes
- **Maintenance**: Critical bug fixes and security updates only
- **EOL**: End of life, upgrade recommended
- **Unsupported**: No updates, immediate upgrade required

## 🔍 Finding Release Information

### By Feature
- Use GitHub search to find when features were introduced
- Check release notes for feature announcements
- Review changelog for implementation details

### By Issue
- Search fixed issues in release notes
- Check GitHub issues for fix versions
- Review migration guides for workarounds

### By Date
- Browse archive for historical releases
- Check release timeline in version matrix
- Review commit history for precise dates

## 📝 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **Major (X.0.0)**: Breaking changes
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, backward compatible

### Release Cycle
- **Major Releases**: Annually (January)
- **Minor Releases**: Quarterly
- **Patch Releases**: As needed
- **Security Releases**: Within 48 hours of discovery

### Changelog Categories
- **Added**: New features
- **Changed**: Existing functionality changes
- **Deprecated**: Soon-to-be removed features
- **Removed**: Deleted features
- **Fixed**: Bug fixes
- **Security**: Vulnerability patches

## 🔔 Release Notifications

### Stay Updated
- **GitHub Releases**: Watch the repository
- **NPM**: Follow package updates
- **Changelog**: Subscribe to release feed
- **Security**: Join security mailing list

## 🔄 Navigation

- **[↑ Top](#release-documentation)**
- **[← Documentation Home](../README.md)**
- **[→ Latest Release](./v0.7.0/README.md)**
- **[→ Migration Guides](./migration/README.md)**

Last Updated: 2025-07-18