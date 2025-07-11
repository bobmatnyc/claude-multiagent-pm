# Claude Multi-Agent PM Framework - Codebase Management Rules

## 🚨 CRITICAL FRAMEWORK PROTECTION RULES

### ⛔ ABSOLUTE PROHIBITIONS - NEVER DO THESE

1. **NEVER DELETE OR MODIFY `framework/CLAUDE.md`**
   - This is the master template for all deployments
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

### 📋 DEVELOPMENT WORKFLOW RULES

#### For Framework Changes:
1. **Test in Development Environment First**
   - Use `--force` flag carefully and only for testing
   - Verify deployment works before committing changes
   - Check backup creation is functioning

2. **Version Management**
   - Update `CLAUDE_MD_VERSION` when making content changes
   - Follow format: `FRAMEWORK_VERSION-NNN` (e.g., `4.5.1-002`)
   - Increment serial number for same framework version

3. **Deployment Testing**
   - Run `python -m claude_pm.cli setup --show-version-check` to test
   - Verify version comparison logic works correctly
   - Ensure backups are created and rotated properly

#### For Code Changes:
1. **Parent Directory Manager Modifications**
   - Never remove protection methods
   - Test backup functionality after any changes
   - Maintain backward compatibility for existing deployments

2. **Template System Changes**
   - Preserve framework template priority over template manager
   - Maintain handlebars variable substitution
   - Keep version checking logic intact

### 🔧 MAINTENANCE COMMANDS

#### Check Framework Protection Status:
```python
# In Python code or debugging
from claude_pm.services.parent_directory_manager import ParentDirectoryManager
manager = ParentDirectoryManager()
await manager._initialize()
status = manager.get_framework_backup_status()
```

#### Manual Backup Creation:
```bash
# Trigger backup through setup command
python -m claude_pm.cli setup --show-version-check
```

#### View Backup History:
```bash
ls -la .claude-pm/framework_backups/
```

### 🚀 SCRIPT DEPLOYMENT AUTOMATION

**CRITICAL**: Use automated deployment system to ensure changes are properly applied.

#### Script Deployment Commands:
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

#### When Making Changes to bin/ Scripts:
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

#### Deployment Features:
- **Automatic Backups**: Creates timestamped backups before deployment
- **Checksum Validation**: Detects drift between source and deployed scripts
- **Version Tracking**: Monitors script versions and deployment history
- **Rollback Support**: Can rollback to previous versions if needed
- **Integration**: Updates main deployment config with script status

#### Emergency Rollback:
```bash
# Rollback specific script to previous version
python scripts/deploy_scripts.py --rollback claude-pm
```

### 🧪 FRAMEWORK INTEGRITY TESTING

**CRITICAL**: Run integrity tests before making changes to prevent template corruption.

#### Framework Testing Commands:
```bash
# Run all framework integrity tests
python scripts/test_framework_integrity.py

# Run only template handlebars tests
python test_framework_template.py

# Check deployment script status
python scripts/deploy_scripts.py --status
```

#### What the Tests Validate:
- **Handlebars Variables**: Ensures `framework/CLAUDE.md` uses `{{VARIABLE}}` format instead of hardcoded values
- **Version Consistency**: Validates VERSION file, package.json, and Python package versions match
- **Template Structure**: Checks that all required variables are present and properly formatted
- **Deployment Integrity**: Validates template processing and variable substitution

#### When to Run Tests:
1. **Before committing changes** to framework template
2. **Before deployment** to parent directories  
3. **After modifying** deployment scripts
4. **In CI/CD pipelines** to catch template corruption early

#### Test Files:
- `test_framework_template.py` - Handlebars and template integrity tests
- `scripts/test_framework_integrity.py` - Comprehensive integrity test suite

### 📁 CRITICAL FILE LOCATIONS

#### Protected Files:
- `framework/CLAUDE.md` - Master template (NEVER DELETE - ESSENTIAL FOR ALL DEPLOYMENTS)
- `.claude-pm/framework_backups/` - Automatic backups
- `claude_pm/services/parent_directory_manager.py` - Protection code

#### ⚠️ CLEANUP PROCESS WARNING:
**Any automated cleanup, maintenance, or file management processes MUST EXCLUDE `framework/CLAUDE.md`**
- Add explicit exclusions for `framework/CLAUDE.md` in all cleanup scripts
- This file is NOT temporary and MUST persist across all operations
- Deletion will cascade to break ALL managed project deployments

#### Configuration Files:
- `.claude-pm/parent_directory_manager/` - Service state
- `.claude-pm/config.json` - Framework configuration
- `VERSION` - Framework version reference

### 🚀 DEPLOYMENT SAFETY

#### Before Deploying to Parent Directories:
1. **Verify Framework Template Integrity**
   - Check `framework/CLAUDE.md` exists and has expected content
   - Ensure backups are being created
   - Test version comparison logic

2. **Test with Version Checking**
   - Use `--show-version-check` flag to see decision logic
   - Verify skip behavior works for same versions
   - Confirm force override works when needed

3. **Monitor Backup Rotation**
   - Ensure old backups are properly cleaned up
   - Verify only 2 most recent copies are kept
   - Check backup file naming consistency

### ⚡ EMERGENCY RECOVERY

#### If Framework Template is Corrupted:
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

#### If Protection System Fails:
1. **Never disable protection code**
2. **Fix the underlying issue instead**
3. **Test fixes in development environment**
4. **Ensure backups remain functional**

## 🔒 SECURITY CONSIDERATIONS

- Framework template controls all deployment behavior
- Corruption could affect all managed projects
- Backup system provides recovery capability
- Version checking prevents accidental downgrades
- Protection methods prevent accidental deletion

## 📖 DEVELOPER GUIDELINES

### When Adding New Features:
1. **Preserve Existing Protection**
2. **Add Tests for New Functionality**
3. **Document Any Changes to Protection Logic**
4. **Maintain Backward Compatibility**

### When Debugging Issues:
1. **Check Framework Template First**
2. **Verify Backup System Operation**
3. **Review Version Comparison Logic**
4. **Test with Clean Environment**

---

**Remember**: The framework template is the foundation of the entire system. Treat it with extreme care and always verify protection mechanisms are working properly.