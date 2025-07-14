# Claude Multi-Agent PM Framework - Project Development Rules v0.7.0

> **⚠️ CRITICAL DISTINCTION: PROJECT DEVELOPMENT RULES**
> 
> **This file contains development rules for working on the claude-multiagent-pm framework codebase itself.**
> 
> **📍 If you are USING the framework in your projects:**
> - Look for `framework/CLAUDE.md` in your deployed project directory
> - These are development rules for framework contributors, not end-users
> 
> **📍 If you are DEVELOPING the framework codebase:**
> - These rules below apply to you
> - Follow all protection mechanisms and testing protocols
> - Maintain backward compatibility and version consistency

---

## 🚨 CRITICAL FRAMEWORK PROTECTION RULES

### ⛔ ABSOLUTE PROHIBITIONS - NEVER DO THESE

1. **NEVER DELETE OR MODIFY `framework/CLAUDE.md`**
   - This is the master template for ALL framework deployments
   - Protected by automatic backup system (keeps 2 most recent copies)
   - Any changes must go through proper version control and testing
   - **CRITICAL**: This file is ESSENTIAL to framework operation and MUST NOT be deleted by cleanup processes
   - **WARNING**: Deletion of this file will break ALL framework deployments across projects

2. **NEVER REMOVE PROTECTION MECHANISMS**
   - `_protect_framework_template()` method must remain intact
   - `_backup_framework_template()` functionality is critical
   - Framework integrity validation must stay enabled

3. **NEVER BYPASS VERSION CHECKING**
   - Template deployment version comparison prevents corruption
   - Force flags should only be used for emergency recovery
   - Version mismatch warnings indicate potential issues

### 🛡️ FRAMEWORK TEMPLATE PROTECTION SYSTEM

#### Automatic Protections in Place:
- **Backup on Access**: Every time `framework/CLAUDE.md` is read, a backup is created
- **Rotation Management**: Only 2 most recent backups are kept (automatic cleanup)
- **Integrity Validation**: Content and structure verified on system startup
- **Permission Management**: Read permissions automatically maintained
- **Path Validation**: Only legitimate framework files are protected

#### Backup Storage:
- **Location**: `.claude-pm/framework_backups/`
- **Format**: `framework_CLAUDE_md_YYYYMMDD_HHMMSS_mmm.backup`
- **Retention**: 2 most recent copies only
- **Automatic**: Created on every template access

---

## 📋 DEVELOPMENT WORKFLOW RULES

### Framework Version Management (Current: v0.7.0)
- **VERSION File**: Must match package.json version (currently 0.7.0)
- **Package.json**: Primary version source for npm deployment
- **Template Versions**: Update `CLAUDE_MD_VERSION` when making content changes
- **Version Format**: `FRAMEWORK_VERSION-NNN` (e.g., `0.7.0-001`)
- **Serial Increments**: Increment serial number for same framework version

### For Framework Changes:
1. **Test in Development Environment First**
   - Use `--force` flag carefully and only for testing
   - Verify deployment works before committing changes
   - Check backup creation is functioning

2. **Version Alignment Protocol**
   - Ensure VERSION file matches package.json version
   - Update template variables when framework version changes
   - Test deployment with version checking enabled

3. **Deployment Testing**
   - Run `python -m claude_pm.cli setup --show-version-check` to test
   - Verify version comparison logic works correctly
   - Ensure backups are created and rotated properly

### For Code Changes:
1. **Parent Directory Manager Modifications**
   - Never remove protection methods
   - Test backup functionality after any changes
   - Maintain backward compatibility for existing deployments

2. **Template System Changes**
   - Preserve framework template priority over template manager
   - Maintain handlebars variable substitution
   - Keep version checking logic intact

---

## 🔧 MAINTENANCE COMMANDS

### Framework Health Monitoring
```python
# Check framework protection status
from claude_pm.services.parent_directory_manager import ParentDirectoryManager
manager = ParentDirectoryManager()
await manager._initialize()
status = manager.get_framework_backup_status()
```

### Backup Management
```bash
# Trigger backup through setup command
python -m claude_pm.cli setup --show-version-check

# View backup history
ls -la .claude-pm/framework_backups/
```

### Version Validation
```bash
# Check version consistency
python -c "import claude_pm; print(claude_pm.__version__)"
cat VERSION
node -p "require('./package.json').version"
```

---

## 🚀 SCRIPT DEPLOYMENT AUTOMATION

**CRITICAL**: Use automated deployment system to ensure changes are properly applied.

### Deployment Commands
```bash
# Deploy all scripts (claude-pm, cmpm) to ~/.local/bin/
python scripts/deploy_scripts.py --deploy

# Deploy specific script only
python scripts/deploy_scripts.py --deploy-script claude-pm

# Check for deployment drift (recommended before changes)
python scripts/deploy_scripts.py --check

# View comprehensive deployment status
python scripts/deploy_scripts.py --status

# Verify deployed scripts are working
python scripts/deploy_scripts.py --verify
```

### Post-Change Deployment Protocol
1. **ALWAYS run deployment after changes**:
   ```bash
   python scripts/deploy_scripts.py --deploy
   ```

2. **Check status before and after**:
   ```bash
   python scripts/deploy_scripts.py --status
   ```

3. **Verify deployment works**:
   ```bash
   python scripts/deploy_scripts.py --verify
   ```

### Deployment Features
- **Automatic Backups**: Creates timestamped backups before deployment
- **Checksum Validation**: Detects drift between source and deployed scripts
- **Version Tracking**: Monitors script versions and deployment history
- **Rollback Support**: Can rollback to previous versions if needed
- **Integration**: Updates main deployment config with script status

### Emergency Rollback
```bash
# Rollback specific script to previous version
python scripts/deploy_scripts.py --rollback claude-pm
```

---

## 🧪 FRAMEWORK INTEGRITY TESTING

**CRITICAL**: Run integrity tests before making changes to prevent template corruption.

### Testing Commands
```bash
# Run all framework integrity tests
python scripts/test_framework_integrity.py

# Run only template handlebars tests
python test_framework_template.py

# Check deployment script status
python scripts/deploy_scripts.py --status

# Validate version consistency across all files
python scripts/validate_version_consistency.py
```

### Test Validation Scope
- **Handlebars Variables**: Ensures `framework/CLAUDE.md` uses `{{VARIABLE}}` format
- **Version Consistency**: Validates VERSION file, package.json, and Python package versions match
- **Template Structure**: Checks that all required variables are present and properly formatted
- **Deployment Integrity**: Validates template processing and variable substitution
- **Backup System**: Verifies backup creation and rotation functionality

### Testing Protocol
1. **Before committing changes** to framework template
2. **Before deployment** to parent directories  
3. **After modifying** deployment scripts
4. **After version updates** to ensure consistency
5. **In CI/CD pipelines** to catch template corruption early

---

## 📁 CRITICAL FILE LOCATIONS

### Protected Files (NEVER DELETE)
- `framework/CLAUDE.md` - Master template (**ESSENTIAL FOR ALL DEPLOYMENTS**)
- `.claude-pm/framework_backups/` - Automatic backups
- `claude_pm/services/parent_directory_manager.py` - Protection code
- `VERSION` - Framework version reference (must match package.json)

### ⚠️ CLEANUP PROCESS WARNING
**Any automated cleanup, maintenance, or file management processes MUST EXCLUDE:**
- `framework/CLAUDE.md` (critical for all deployments)
- `VERSION` file (version reference)
- `.claude-pm/framework_backups/` directory
- Protection mechanism code

**These files are NOT temporary and MUST persist across all operations.**
**Deletion will cascade to break ALL managed project deployments.**

### Configuration Files
- `.claude-pm/parent_directory_manager/` - Service state
- `.claude-pm/config.json` - Framework configuration
- `package.json` - NPM package configuration and primary version source

---

## 🚀 DEPLOYMENT SAFETY PROTOCOLS

### Pre-Deployment Checklist
1. **Verify Framework Template Integrity**
   - Check `framework/CLAUDE.md` exists and has expected content
   - Ensure backups are being created
   - Test version comparison logic

2. **Version Consistency Validation**
   - Ensure VERSION file matches package.json
   - Verify Python package version alignment
   - Test template variable substitution

3. **Test with Version Checking**
   - Use `--show-version-check` flag to see decision logic
   - Verify skip behavior works for same versions
   - Confirm force override works when needed

4. **Monitor Backup System**
   - Ensure old backups are properly cleaned up
   - Verify only 2 most recent copies are kept
   - Check backup file naming consistency

---

## ⚡ EMERGENCY RECOVERY PROCEDURES

### Framework Template Recovery
1. **Check Recent Backups**:
   ```bash
   ls -la .claude-pm/framework_backups/
   ```

2. **Restore from Backup**:
   ```bash
   cp .claude-pm/framework_backups/framework_CLAUDE_md_[timestamp].backup framework/CLAUDE.md
   ```

3. **Verify Restoration**:
   ```bash
   python -m claude_pm.cli setup --show-version-check
   ```

### Version Mismatch Recovery
1. **Check all version sources**:
   ```bash
   cat VERSION
   node -p "require('./package.json').version"
   python -c "import claude_pm; print(claude_pm.__version__)"
   ```

2. **Align versions manually** if automated tools fail

3. **Test deployment** after version alignment

### Protection System Recovery
1. **Never disable protection code**
2. **Fix the underlying issue instead**
3. **Test fixes in development environment**
4. **Ensure backups remain functional**

---

## 🔒 SECURITY CONSIDERATIONS

- Framework template controls all deployment behavior across projects
- Version consistency prevents security vulnerabilities from misaligned deployments
- Corruption could affect all managed projects
- Backup system provides recovery capability
- Version checking prevents accidental downgrades
- Protection methods prevent accidental deletion

---

## 📖 DEVELOPER GUIDELINES

### When Adding New Features:
1. **Preserve Existing Protection Mechanisms**
2. **Add Tests for New Functionality**
3. **Document Any Changes to Protection Logic**
4. **Maintain Backward Compatibility**
5. **Ensure Version Consistency**

### When Debugging Issues:
1. **Check Framework Template First**
2. **Verify Backup System Operation**
3. **Review Version Comparison Logic**
4. **Test with Clean Environment**
5. **Validate Version Alignment**

### When Updating Versions:
1. **Update VERSION file first**
2. **Align package.json version**
3. **Update template version references**
4. **Test deployment with new version**
5. **Verify backup system handles version changes**

---

## 🎯 FRAMEWORK DEVELOPMENT BEST PRACTICES

### Code Quality Standards
- All changes must pass integrity tests
- Version consistency is mandatory
- Protection mechanisms are non-negotiable
- Backup functionality must remain intact

### Testing Requirements
- Run full test suite before commits
- Validate template integrity after changes
- Test deployment scenarios with version checking
- Verify backup system operation

### Documentation Updates
- Keep development rules current with code changes
- Update version references when framework versions change
- Maintain clear distinction between development and usage documentation

---

**Remember**: This framework template is the foundation of the entire multi-project system. 
Treat it with extreme care, maintain version consistency, and always verify protection mechanisms are working properly.

**Framework Version**: 0.7.0  
**Documentation Version**: 0.7.0-001  
**Last Updated**: 2025-07-14