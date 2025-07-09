# Push Operations Quick Reference

## 🚀 Simple Usage

**User says**: `"push"`
**System response**: Comprehensive deployment pipeline executes automatically

## 📋 What Happens When You Say "Push"

### 1. Pre-Push Validation ✅
- Check git status
- Verify build state
- Validate dependencies
- Review configuration

### 2. Version Management 📦
- Analyze changes
- Determine version bump (patch/minor/major)
- Update version files
- Generate version tags

### 3. Documentation Updates 📝
- Update README.md
- Generate/update CHANGELOG.md
- Update API documentation
- Sync version references

### 4. Git Operations 🔄
- Stage all changes (`git add -A`)
- Create commit with proper message
- Create version tag
- Push to remote repository

### 5. Validation & Reporting 📊
- Verify successful deployment
- Generate deployment report
- Update project status
- Notify of completion

## 🎯 Supported Projects

| Project | Location | Version Method | Build Command |
|---------|----------|----------------|---------------|
| ai-trackdown-tools | `/Users/masa/Projects/managed/ai-trackdown-tools` | npm scripts | `npm run build` |
| claude-multiagent-pm | `/Users/masa/Projects/claude-multiagent-pm` | Manual VERSION file | `./scripts/health-check.sh` |
| All managed projects | `/Users/masa/Projects/managed/*` | Auto-detected | Project-specific |

## 🛡️ Error Handling

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Uncommitted changes | Auto-staged with `git add -A` |
| Build failures | Fix errors, re-run push |
| Version conflicts | Auto-resolve or manual intervention |
| Push failures | Check network/permissions |

### Rollback Commands

```bash
# If push fails (before remote push)
git reset --hard HEAD~1
git tag -d vX.Y.Z

# If push succeeds but needs rollback
git revert HEAD
git push origin main
git push origin --delete vX.Y.Z
```

## 🔧 Advanced Usage

### Specific Version Types
- `"push as patch"` - Bug fixes only
- `"push as minor"` - New features
- `"push as major"` - Breaking changes

### Skip Operations
- `"push without tests"` - Skip test validation
- `"push without changelog"` - Skip changelog generation

## 📱 Example Interactions

### Basic Push
```
User: "push"
Orchestrator: Delegating comprehensive push operation to ops agent...
Ops Agent: Executing complete deployment pipeline...
✅ Successfully deployed version 1.2.3
```

### Push with Issues
```
User: "push"
Ops Agent: Build failed - TypeScript errors detected
Ops Agent: Please fix errors and retry push
❌ Push failed - fix required
```

### Emergency Rollback
```
User: "rollback last push"
Ops Agent: Executing rollback procedures...
✅ Rollback completed - repository restored
```

## 🚨 Important Notes

1. **No Clarification Required**: System automatically executes full pipeline
2. **Intelligent Version Detection**: Analyzes changes to determine version type
3. **Comprehensive Documentation**: Updates all relevant documentation
4. **Safe Defaults**: Includes validation and rollback procedures
5. **Project-Aware**: Adapts to different project types and configurations

## 📞 Support

- **Documentation**: [Comprehensive Push Workflow](./COMPREHENSIVE_PUSH_WORKFLOW.md)
- **Ops Agent**: [Agent Role Definition](../framework/agent-roles/ops-agent.md)
- **Orchestrator**: [Configuration](../CLAUDE.md)
- **Validation**: Run `./scripts/validate-push-workflow.sh`

---

**Quick Reference Version**: 1.0.0
**Last Updated**: 2025-07-09
**Usage**: Keep this handy for push operations!