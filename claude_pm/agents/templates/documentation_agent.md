# Documentation Agent Delegation Template

## Agent Overview
- **Nickname**: Documenter
- **Type**: documentation
- **Role**: Project documentation pattern analysis and operational understanding
- **Authority**: ALL documentation operations + changelog generation

## Delegation Template

```
**Documentation Agent**: [Documentation task]

TEMPORAL CONTEXT: Today is [date]. Apply date awareness to documentation decisions.

**Task**: [Specific documentation work]
- Analyze documentation patterns and health
- Generate changelogs from git commit history
- Analyze commits for semantic versioning impact
- Update version-related documentation and release notes

**Authority**: ALL documentation operations + changelog generation
**Expected Results**: Documentation deliverables and operational insights
**Ticket Reference**: [ISS-XXXX if applicable]
**Progress Reporting**: Report documentation updates, version impact analysis, and any issues
```

## Example Usage

### Changelog Generation
```
**Documentation Agent**: Generate changelog for v1.3.0 release

TEMPORAL CONTEXT: Today is 2025-07-20. Preparing for release cycle.

**Task**: Generate comprehensive changelog for version 1.3.0
- Analyze all commits since v1.2.3 tag
- Categorize changes (features, fixes, breaking changes)
- Determine semantic version impact (major/minor/patch)
- Create CHANGELOG.md update with proper formatting

**Authority**: ALL documentation operations + changelog generation
**Expected Results**: Updated CHANGELOG.md with categorized changes
**Ticket Reference**: ISS-0123
**Progress Reporting**: Report version recommendation and notable changes
```

### Documentation Pattern Analysis
```
**Documentation Agent**: Analyze project documentation health

TEMPORAL CONTEXT: Today is 2025-07-20. Monthly documentation review.

**Task**: Comprehensive documentation health check
- Scan all .md files for outdated information
- Check for missing documentation in new features
- Verify all code examples are current
- Identify documentation gaps and inconsistencies

**Authority**: ALL documentation operations + pattern analysis
**Expected Results**: Documentation health report with recommendations
**Progress Reporting**: Report critical gaps and improvement priorities
```

## Integration Points

### With Version Control Agent
- Provides semantic version recommendations based on changelog
- Coordinates on release documentation updates

### With QA Agent
- Documents test coverage and quality metrics
- Creates testing documentation

### With Engineer Agent
- Ensures code changes have corresponding documentation
- Reviews inline documentation quality

## Progress Reporting Format

```
📚 Documentation Agent Progress Report
- Task: [current task]
- Status: [in progress/completed/blocked]
- Key Findings:
  * [finding 1]
  * [finding 2]
- Version Impact: [major/minor/patch/none]
- Deliverables:
  * [deliverable 1]
  * [deliverable 2]
- Next Steps: [if applicable]
- Blockers: [if any]
```

## Error Handling

Common issues and responses:
- **Missing git history**: Request git repository initialization
- **No commits to analyze**: Report empty changelog
- **Conflicting version tags**: Escalate to Version Control Agent
- **Documentation conflicts**: Propose resolution strategy