# Claude Multi-Agent PM Framework Development Rules v1.2.5

> **🚨 THIS FILE IS FOR FRAMEWORK DEVELOPERS ONLY**
> 
> **This file contains development rules for contributors working on the claude-multiagent-pm framework codebase itself.**
> 
> **📍 If you are USING the framework:**
> - DO NOT follow these rules - they are for framework development only
> - Look for `framework/CLAUDE.md` in your deployed project for usage instructions
> - These rules apply ONLY to the framework source code repository
> 
> **📍 If you are DEVELOPING the framework:**
> - Follow ALL rules below strictly
> - Maintain clean root directory structure
> - Run comprehensive tests before commits
> - Preserve backward compatibility

---

## 📂 ROOT DIRECTORY HYGIENE RULES

### ✅ ALLOWED ROOT DOCUMENTS (ONLY THESE)
1. **CLAUDE.md** - Framework development rules (this file)
2. **README.md** - Framework overview and quick start
3. **CHANGELOG.md** - Version history and changes
4. **RELEASE_NOTES.md** - Detailed release information

### ⛔ STRICT DIRECTORY ORGANIZATION
- **ALL tests** → `tests/` directory (NO test files in root)
- **ALL documentation** → `docs/` directory (except the 4 allowed root files)
- **ALL scripts** → `scripts/` directory
- **ALL build artifacts** → `.gitignore` them (never commit)
- **NO temporary files** in root directory
- **NO example files** in root directory
- **NO generated reports** in root directory

### 🧹 ROOT CLEANUP CHECKLIST
Before committing, ensure:
- [ ] Only 4 allowed .md files exist in root
- [ ] All test files are in `tests/`
- [ ] All docs are in `docs/`
- [ ] No temporary or generated files in root
- [ ] `.gitignore` is properly configured

---

## 🔄 DEVELOPMENT WORKFLOW

### 1. Feature Development Process
```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes following all rules
# 3. Run comprehensive tests
pytest tests/
npm test

# 4. Verify root directory hygiene
ls -la | grep -E '\.(md|py|js|json)$'  # Should show only allowed files

# 5. Run integrity checks
python scripts/test_framework_integrity.py
python scripts/validate_version_consistency.py

# 6. Commit with conventional commits
git commit -m "feat: Add new capability" 
# or "fix:", "docs:", "test:", "refactor:", "chore:"

# 7. Push and create PR
git push origin feature/your-feature-name
```

### 2. Testing Requirements
**MANDATORY before ANY commit:**
- ✅ Unit tests pass: `pytest tests/unit/`
- ✅ Integration tests pass: `pytest tests/integration/`
- ✅ E2E tests pass: `pytest tests/e2e/`
- ✅ Framework integrity validated
- ✅ Version consistency verified
- ✅ Root directory hygiene maintained

### 3. Code Review Checklist
- [ ] No files in root except 4 allowed .md files
- [ ] All tests in `tests/` directory
- [ ] All docs in `docs/` directory
- [ ] No deployment code mixed with development code
- [ ] Framework template (`framework/CLAUDE.md`) unchanged
- [ ] Version files synchronized if version changed
- [ ] Backward compatibility maintained

---

## 👥 CONTRIBUTION GUIDELINES

### Pull Request Requirements
1. **Title**: Use conventional commit format
2. **Description**: Explain what and why (not how)
3. **Tests**: Include tests for new features
4. **Documentation**: Update relevant docs
5. **Breaking Changes**: Clearly marked and justified

### Coding Standards
- **Python**: Follow PEP 8, use type hints
- **JavaScript**: Follow ESLint configuration
- **Markdown**: Use consistent formatting
- **File Organization**: Respect directory structure

### Documentation Standards
- **Root Docs**: Only 4 allowed files, keep concise
- **Feature Docs**: Detailed docs go in `docs/features/`
- **API Docs**: Technical docs go in `docs/technical/`
- **Examples**: All examples go in `docs/examples/`

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

## 📋 VERSION MANAGEMENT

### 🔢 DUAL VERSIONING SYSTEM

The Claude PM Framework uses **TWO INDEPENDENT** versioning systems:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE PM VERSIONING SYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PACKAGE VERSION (1.4.0)          FRAMEWORK VERSION (014)       │
│  ├─ Software releases             ├─ Template structure         │
│  ├─ NPM/PyPI packages            ├─ Agent architecture         │
│  ├─ Bug fixes & features         ├─ Core system changes        │
│  └─ Semantic versioning          └─ Serial numbering           │
│                                                                 │
│  Examples:                        Examples:                     │
│  1.3.9 → 1.4.0 (minor)           013 → 014 (structure change)  │
│  1.4.0 → 1.4.1 (patch)           014 → 014 (no change)         │
│  1.4.1 → 2.0.0 (major)           014 → 015 (agent updates)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 1. **Package Version** (e.g., `1.4.0`)
- **Format**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Purpose**: NPM/PyPI package releases, software versioning
- **Files**:
  - `package.json` - Primary for npm
  - `pyproject.toml` - Primary for PyPI
  - `VERSION` - Root directory reference
  - `claude_pm/_version.py` - Python module version
- **Usage**: CLI `--version`, package installations, release tags

#### 2. **Framework Version** (e.g., `014`, `015`)
- **Format**: Three-digit serial number (001-999)
- **Purpose**: Framework template evolution tracking
- **Files**:
  - `framework/VERSION` - Primary source (used by core systems)
  - `claude_pm/utils/versions/FRAMEWORK_VERSION` - Development reference
  - `claude_pm/data/framework/VERSION` - Framework data copy
- **Usage**: CLAUDE.md templates, agent system versioning, framework integrity

### 🎯 Version Independence
- **Package Version**: Changes with software releases (features, fixes)
- **Framework Version**: Changes ONLY when framework structure evolves
- **Example**: Package can go from 1.4.0 → 1.4.1 → 1.5.0 while Framework stays at 014

### 📊 CLAUDE_MD_VERSION Format
- **Format**: Simple serial number (e.g., 016, 017, 018)
- **Example**: `016` is the 16th framework version
- **Purpose**: Tracks framework template structure changes
- **Usage**: Enables proper version comparison for updates

### Version Update Process

#### Package Version Update:
```bash
# 1. Update all package version files
npm version patch  # or minor/major
# This updates package.json automatically

# 2. Sync other version files
python scripts/validate_version_consistency.py --fix

# 3. Commit and tag
git commit -m "chore: bump version to X.Y.Z"
git tag vX.Y.Z
```

#### Framework Version Update:
```bash
# 1. Update all three framework version files (MANUAL - no automated tool)
echo "015" > framework/VERSION
echo "015" > claude_pm/utils/versions/FRAMEWORK_VERSION
echo "015" > claude_pm/data/framework/VERSION

# 2. Verify all files are synchronized
cat framework/VERSION
cat claude_pm/utils/versions/FRAMEWORK_VERSION
cat claude_pm/data/framework/VERSION

# 3. Reset serial to 001 in CLAUDE.md templates
# The serial will auto-increment from 001 on next generation

# 4. Document framework changes
# Update CHANGELOG.md with framework structure changes

# 5. Commit with clear message
git commit -m "feat: increment framework version to 015"
```

## 🛠️ VERSIONING TOOLS & SCRIPTS

### Available Versioning Tools

#### 1. **validate_version_consistency.py**
```bash
# Check version consistency across all files
python scripts/validate_version_consistency.py

# Auto-fix version inconsistencies
python scripts/validate_version_consistency.py --fix
```
- Validates package versions across package.json, pyproject.toml, VERSION, _version.py
- Does NOT handle framework version (014 format)

#### 2. **increment_version.js**
```bash
# Increment CLAUDE_MD_VERSION serial number
node scripts/increment_version.js
```
- **DEPRECATED**: This script is no longer needed with simple serial numbers
- Framework version is now a single number that increments directly

#### 3. **dev-version-manager.py**
```bash
# Interactive version management for services
python scripts/dev-version-manager.py

# Show all service versions
python scripts/dev-version-manager.py --show-all

# Update specific service version
python scripts/dev-version-manager.py --service core --increment
```
- Manages individual service/subsystem versions
- Uses serial number format for services

#### 4. **Manual Framework Version Update**
Currently NO automated tool exists for framework version bumps. Use:
```bash
# Update all three framework version files manually
echo "016" > framework/VERSION
echo "016" > claude_pm/utils/versions/FRAMEWORK_VERSION
echo "016" > claude_pm/data/framework/VERSION

# Verify the update
cat framework/VERSION
cat claude_pm/utils/versions/FRAMEWORK_VERSION
cat claude_pm/data/framework/VERSION
```

### Version Checking Commands
```bash
# Check package version
claude-pm --version
npm list @bobmatnyc/claude-multiagent-pm
python -c "import claude_pm; print(claude_pm.__version__)"

# Check framework version
cat framework/VERSION
cat claude_pm/utils/versions/FRAMEWORK_VERSION
cat claude_pm/data/framework/VERSION

# Check CLAUDE_MD_VERSION in deployed projects
grep "CLAUDE_MD_VERSION" .claude-pm/CLAUDE.md | head -1
```

### Common Version Operations

#### When to Update Package Version:
- New features added
- Bug fixes released
- Breaking changes introduced
- Follow semantic versioning rules

#### When to Update Framework Version:
- Agent system architecture changes
- CLAUDE.md template structure changes
- Core framework behavior modifications
- Major agent hierarchy updates

### ⚠️ Common Version Confusion Points

#### DON'T Confuse These:
- ❌ `VERSION: 1.4.0` in root → This is PACKAGE version
- ✅ `framework/VERSION: 015` → This is FRAMEWORK version (primary source)
- ✅ `FRAMEWORK_VERSION: 015` → This is also framework version

#### Version File Locations Reference:
```
claude-multiagent-pm/
├── VERSION                                    # Package: 1.4.0
├── package.json                               # Package: 1.4.0
├── pyproject.toml                             # Package: 1.4.0
├── framework/
│   └── VERSION                                # Framework: 015 (primary) ✅
├── claude_pm/
│   ├── _version.py                           # Package: 1.4.0
│   ├── data/framework/
│   │   └── VERSION                            # Framework: 015 (copy) ✅
│   └── utils/versions/
│       └── FRAMEWORK_VERSION                  # Framework: 015 (dev ref) ✅
```

#### Troubleshooting Version Issues:
1. **"Version mismatch" errors**: Check you're comparing same version type
2. **"Framework version 1.4.0"**: Wrong - framework uses 015 format (three digits)
3. **"Can't find framework version"**: Primary source is `framework/VERSION`
4. **"CLAUDE_MD_VERSION confusion"**: Now uses simple serial numbers (e.g., 016, 017)
5. **"Version files out of sync"**: All three framework version files must match

---

## 🔧 DEVELOPMENT COMMANDS

### Essential Development Scripts
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Check framework integrity
python scripts/test_framework_integrity.py

# Validate version consistency
python scripts/validate_version_consistency.py

# Check root directory hygiene
ls -la | grep -v "^d" | grep -v -E "(CLAUDE|README|CHANGELOG|RELEASE_NOTES)\.md$"
# Should return empty - no other files allowed in root
```


## 🧪 TESTING REQUIREMENTS

### Test Categories (ALL REQUIRED)
1. **Unit Tests** (`tests/unit/`)
   - Test individual components in isolation
   - Mock external dependencies
   - Fast execution, high coverage

2. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Verify service integrations
   - Test with real file system

3. **E2E Tests** (`tests/e2e/`)
   - Test complete workflows
   - Simulate real usage scenarios
   - Verify CLI functionality

4. **Framework Integrity Tests**
   - Template validation
   - Version consistency
   - Protection mechanisms

### Pre-Commit Testing Checklist
```bash
# 1. Run all tests
pytest tests/ -v

# 2. Check code coverage
pytest tests/ --cov=claude_pm --cov-report=html

# 3. Validate framework integrity
python scripts/test_framework_integrity.py

# 4. Check version consistency
python scripts/validate_version_consistency.py

# 5. Lint Python code
flake8 claude_pm/
mypy claude_pm/

# 6. Lint JavaScript code
npm run lint

# 7. Verify root directory hygiene
bash scripts/check_root_hygiene.sh
```

---

## 📁 PROJECT STRUCTURE

### Root Directory (KEEP CLEAN!)
```
claude-multiagent-pm/
├── CLAUDE.md              # This file - development rules
├── README.md              # Project overview
├── CHANGELOG.md           # Version history
├── RELEASE_NOTES.md       # Release details
├── package.json           # NPM configuration
├── pyproject.toml         # Python package config
├── VERSION                # Version reference
├── .gitignore            # Git ignore rules
├── claude_pm/            # Source code
├── framework/            # Deployment templates
├── tests/                # ALL tests go here
├── docs/                 # ALL other docs go here
├── scripts/              # Development scripts
└── requirements/         # Python dependencies
```

### Key Development Directories
- `claude_pm/` - Framework source code
- `tests/` - ALL test files (unit, integration, e2e)
- `docs/` - ALL documentation except 4 root files
- `scripts/` - Development and build scripts
- `framework/` - Deployment templates (DO NOT MODIFY)

### Protected Framework Files
- `framework/CLAUDE.md` - Deployment template (NEVER EDIT DIRECTLY)
- `VERSION` - Version synchronization file
- Protection mechanisms in `parent_directory_manager.py`

---


## 🛠️ DEVELOPMENT BEST PRACTICES

### Code Quality Standards
1. **Type Hints**: Use Python type hints everywhere
2. **Docstrings**: Document all public functions/classes
3. **Error Handling**: Explicit error messages
4. **Logging**: Use structured logging
5. **Testing**: Maintain >80% code coverage

### Commit Message Format
```
type(scope): subject

body (optional)

footer (optional)
```

Types: feat, fix, docs, style, refactor, test, chore

### Branch Naming Convention
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation only
- `refactor/description` - Code refactoring
- `test/description` - Test additions/fixes

---

## 🚫 COMMON MISTAKES TO AVOID

1. **Adding files to root directory** - Use proper subdirectories
2. **Mixing deployment with development** - Keep concerns separated
3. **Editing framework/CLAUDE.md directly** - This breaks deployments
4. **Inconsistent versions** - Always sync all 4 version files
5. **Skipping tests** - All PRs must have passing tests
6. **Poor commit messages** - Use conventional commits

---

## 📞 GETTING HELP

- **Documentation**: Check `docs/development/`
- **Issues**: File on GitHub with clear reproduction steps
- **Questions**: Use discussions, not issues
- **Security**: Email security concerns privately

---

**Documentation Version**: 010  
**Last Updated**: 2025-07-20

**Remember**: This file is for FRAMEWORK DEVELOPERS ONLY. If you're using the framework in your projects, refer to the deployed `framework/CLAUDE.md` instead.