# Claude PM Framework Deprecation Timeline

## 📅 Editable Installation Deprecation Schedule

### Current Status: Phase 1 - Soft Deprecation
**Version**: v1.3.0 (Released: January 2025)

---

## Timeline Overview

```
Jan 2025    Apr 2025    Jul 2025    Oct 2025
   |           |           |           |
   v1.3.0      v1.4.0      v2.0.0      
   ↓           ↓           ↓
[Phase 1]  [Phase 2]  [Phase 3]
Warnings   Limited    Removed
```

---

## Phase 1: Soft Deprecation (Current)
**Version**: v1.3.0 - v1.3.x  
**Timeline**: January 2025 - April 2025  
**Status**: ✅ Active

### What's Happening Now:
- ⚠️ **Deprecation warnings** appear when using editable installations
- ✅ **Full functionality** maintained for backward compatibility
- 🛠️ **Migration tools** provided (scripts/migrate_to_pypi.py)
- 📚 **Documentation** updated with migration guides
- 🔕 **Suppressible warnings** via `CLAUDE_PM_SOURCE_MODE=deprecated`

### User Impact:
- **Minimal** - Everything works as before, just with warnings
- Can continue using editable mode with environment variable
- Encouraged to migrate at convenience

### What You See:
```
⚠️  DEPRECATION WARNING: Editable installation detected
You are running Claude PM from a source directory installation.
This installation method is deprecated and will be removed in v2.0.

Please migrate to PyPI installation:
  1. Run: python scripts/migrate_to_pypi.py
  2. Or manually: pip uninstall claude-multiagent-pm && pip install claude-multiagent-pm
```

---

## Phase 2: Hard Deprecation
**Version**: v1.4.0 - v1.4.x  
**Timeline**: April 2025 - July 2025  
**Status**: 🟡 Planned

### What Will Change:
- 🚨 **Stronger warnings** that can't be suppressed easily
- ⚡ **Performance penalties** for editable installations
- 🔒 **Feature limitations** - new features PyPI-only
- ⏰ **Startup delays** to encourage migration
- 📢 **Migration prompts** on every command

### User Impact:
- **Moderate** - Editable mode becomes inconvenient
- Performance degradation noticeable
- Missing out on new features
- Strong encouragement to migrate

### What You'll See:
```
🚨 CRITICAL: Editable installation will stop working in v2.0.0 (July 2025)
⏰ Adding 5-second delay to encourage migration...
❌ New features disabled in editable mode
🔄 Migrate now: python scripts/migrate_to_pypi.py
```

### Limited Features in Phase 2:
- ❌ New agent discovery features
- ❌ Performance optimizations
- ❌ Advanced memory systems
- ❌ Cloud integrations
- ✅ Core functionality only

---

## Phase 3: Complete Removal
**Version**: v2.0.0+  
**Timeline**: July 2025 onwards  
**Status**: 🔴 Future

### What Will Happen:
- ❌ **No editable support** - will not run from source
- 🚫 **Error on detection** of editable installation
- 📦 **PyPI-only** distribution
- 🆕 **Major version bump** signaling breaking change
- 🎯 **Modern features** enabled by clean architecture

### User Impact:
- **Major** - Must use PyPI installation
- No workarounds available
- Clean, optimized codebase
- Better performance and features

### What You'll See:
```
❌ ERROR: Editable installation no longer supported
Claude PM v2.0+ requires PyPI installation.

To install:
  pip install claude-multiagent-pm

For development, use virtual environments:
  python -m venv venv
  source venv/bin/activate
  pip install claude-multiagent-pm
```

---

## Migration Preparation Checklist

### For End Users:

#### ✅ Before April 2025 (Phase 1):
- [ ] Run migration script at your convenience
- [ ] Test PyPI installation in development
- [ ] Update any automation scripts
- [ ] Remove hardcoded paths

#### ⚠️ Before July 2025 (Phase 2):
- [ ] Complete migration to avoid limitations
- [ ] Update CI/CD pipelines
- [ ] Train team on new installation method
- [ ] Document any custom workflows

#### 🚨 Before October 2025 (Phase 3):
- [ ] Ensure all systems migrated
- [ ] No editable installations remaining
- [ ] All documentation updated
- [ ] Team fully transitioned

### For Contributors:

#### Development Setup Changes:
```bash
# Old method (deprecated)
git clone repo
cd repo
pip install -e .

# New method (recommended)
git clone repo
cd repo
python -m venv venv
source venv/bin/activate
pip install -e .  # Still works for development
export CLAUDE_PM_SOURCE_MODE=deprecated  # Acknowledge deprecation
```

---

## Why This Timeline?

### 6-Month Grace Period
- **3 months** (Jan-Apr): Gentle warnings, full functionality
- **3 months** (Apr-Jul): Stronger push, feature limitations
- **Final cutoff** (Jul): Clean break for v2.0

### Benefits of This Approach:
1. **No surprises** - Clear communication and timeline
2. **Gradual transition** - Time to adapt workflows
3. **Preserved stability** - No sudden breakage
4. **Clear messaging** - Users know what to expect
5. **Migration support** - Tools and guides provided

---

## Communication Plan

### Phase 1 (Current):
- ✅ Deprecation warnings in code
- ✅ Migration documentation
- ✅ Automated migration script
- ✅ README updates
- 📧 Email announcement to users
- 📢 GitHub release notes

### Phase 2:
- 🔔 Stronger in-app warnings
- 📧 Reminder emails (30 days before)
- 🎯 Targeted outreach to active users
- 📊 Migration progress tracking
- 🆘 Enhanced support

### Phase 3:
- 🚨 Final warning (30 days)
- 📧 Last chance notifications
- 📚 v2.0 migration guide
- 🎉 New features announcement
- 🏆 Migration success stories

---

## FAQ About Timeline

### Q: Can the timeline be extended?
**A**: We'll monitor migration progress. If significant users need more time, we may extend Phase 2, but Phase 3 (v2.0) timeline is firm.

### Q: What if I can't migrate by July 2025?
**A**: You can continue using v1.4.x, but won't receive updates, security patches, or new features. We strongly recommend migrating.

### Q: Will there be an LTS version?
**A**: v1.4.x will receive security updates for 6 months after v2.0 release (until January 2026).

### Q: Can I request an extension for my organization?
**A**: Contact us for enterprise migration support. We can provide additional guidance and tooling.

---

## Stay Informed

- 📧 **Mailing List**: Subscribe for migration updates
- 📢 **GitHub Releases**: Watch the repository
- 💬 **Discussions**: Join migration conversations
- 📊 **Progress**: Check migration statistics

---

*This timeline is subject to adjustment based on community feedback and migration progress.*

**Last Updated**: January 2025  
**Current Phase**: 1 (Soft Deprecation)  
**Next Milestone**: Phase 2 (April 2025)