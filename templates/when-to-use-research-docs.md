# When to Use Research Design Documents

## Quick Decision Framework

### Use Research Design Docs When:
✅ **Complex Multi-Phase Projects** (>1 week, multiple components)
✅ **Cross-System Integration** (touching multiple services/APIs)
✅ **Performance-Critical Changes** (database schema, core algorithms)
✅ **Team Coordination Required** (multiple developers, stakeholder alignment)
✅ **High-Risk Modifications** (security, data migration, breaking changes)
✅ **Architectural Decisions** (technology choices, design patterns)

### Skip Research Docs For:
❌ **Simple Refactoring** (renaming variables, small function changes)
❌ **Bug Fixes** (straightforward issue resolution)
❌ **Minor Feature Additions** (adding a form field, simple UI changes)
❌ **Documentation Updates** (README changes, comment additions)
❌ **Configuration Changes** (environment variables, build settings)

## Examples

### ✅ Use Research Doc
- "Migrate from MySQL to PostgreSQL"
- "Implement real-time collaboration features"
- "Add multi-tenant architecture support"
- "Integrate with external payment processor"

### ❌ Skip Research Doc
- "Fix button color in dark mode"
- "Add email validation to contact form"
- "Update dependency versions"
- "Add logging to existing function"

## Template Usage
```bash
# Copy template to your project
cp ~/.claude-pm/templates/research-design-doc.md ./docs/design/my-project-research.md

# Start planning
claude-pm analyze research-doc ./docs/design/my-project-research.md
```