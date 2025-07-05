# TrackDown - Claude PM Project Management

This directory contains the TrackDown project management system for the entire Claude PM framework across all projects in ~/Projects.

## Overview

TrackDown is a markdown-based project tracking system that treats project management artifacts as code, storing everything in version-controlled markdown files. This implementation manages the complete Claude PM ecosystem.

## Quick Start

### View Current Sprint
```bash
grep -A20 "## 🎯 Current Sprint" BACKLOG.md
```

### Check Framework Status
```bash
./scripts/status-report.sh
```

### Update Task Status
1. Open `BACKLOG.md`
2. Find your task
3. Update status field
4. Mark checkboxes as complete: `- [x]`
5. Commit changes

## Files

- **BACKLOG.md** - All work items across the entire PM framework
- **ROADMAP.md** - Strategic planning and milestone roadmap
- **METRICS.md** - Productivity metrics and framework success tracking
- **RETROSPECTIVES.md** - Sprint retrospectives and learnings
- **MILESTONES.md** - M01, M02, M03 milestone tracking
- **templates/** - Templates for new work items
- **scripts/** - Automation tools and health checks
- **archive/** - Completed sprints and historical data

## Workflow

### Daily Framework Operations
1. Pull latest: `git pull`
2. Run framework health check: `./scripts/health-check.sh`
3. Update your tasks in BACKLOG.md
4. Update project status in MILESTONES.md
5. Commit changes: `git commit -m "chore(trackdown): update PM framework status"`
6. Push: `git push`

### Sprint Planning
1. Review milestone progress in MILESTONES.md
2. Move backlog items to "Current Sprint" section
3. Assign items to appropriate milestones (M01/M02/M03)
4. Update sprint number in frontmatter
5. Commit changes

### Creating New Items
Use templates in `templates/` as starting point:
- `milestone-task-template.md` - For milestone-specific tasks
- `framework-epic-template.md` - For cross-project epics
- `integration-task-template.md` - For cross-project integrations
- `bug-template.md` - For framework bugs

## Naming Conventions

### Project Management Framework
- **Milestones:** M01-XXX, M02-XXX, M03-XXX (M01-001, M02-015...)
- **Framework Epics:** FEP-XXX (FEP-001, FEP-002...)
- **Cross-Project Tasks:** CPT-XXX (CPT-001, CPT-002...)
- **Integration Tasks:** INT-XXX (INT-001, INT-002...)
- **Infrastructure:** INF-XXX (INF-001, INF-002...)

### Legacy Compatibility
- **Epics:** EP-XXX (for single-project epics)
- **Tasks:** T-XXX (for single-project tasks)
- **Bugs:** BUG-XXX (for project-specific bugs)

## Status Values

- `Backlog` - Not started
- `Ready` - Ready to work on
- `In Progress` - Being worked on
- `In Review` - In code review
- `Testing` - Being tested
- `Done` - Complete
- `Blocked` - Cannot proceed
- `Deferred` - Postponed to future milestone

## Milestone Integration

### M01 Foundation Tasks
Prefix: M01-XXX
Focus: Core infrastructure and essential tooling

### M02 Automation Tasks  
Prefix: M02-XXX
Focus: Workflow automation and multi-agent coordination

### M03 Orchestration Tasks
Prefix: M03-XXX
Focus: Advanced orchestration and enterprise patterns

## Integration with Projects

Reference TrackDown items in commits across any project:
```bash
git commit -m "feat: implement MCP gateway - closes M01-007"
git commit -m "fix: resolve cross-project dependency - closes CPT-012"
```

## Reports

### Framework Health Report
```bash
./scripts/framework-health.sh
```

### Milestone Progress Report  
```bash
./scripts/milestone-progress.sh
```

### Cross-Project Status
```bash
./scripts/cross-project-status.sh
```

## Current Focus

**Sprint S01**: Claude PM Framework Foundation
- **Milestone**: M01 Foundation
- **Epic**: FEP-001 - Framework Infrastructure Setup
- **Goal**: Establish core PM framework with tracking and automation

**Key Metrics Target**:
- 60%+ productivity improvement
- <30 minute project setup
- 70% context switching reduction
- 90%+ task completion rate

## Framework Integration Points

### MCP Services
- **mcp-desktop-gateway**: Service orchestration
- **zen-mcp-server**: Core server infrastructure
- **mcp-cloud-bridge**: Cloud service coordination

### Project Tracking
- **git-portfolio-manager**: Automated git monitoring
- **ai-code-review**: Quality gate enforcement
- **TrackDown**: Centralized task and milestone tracking

### Automation Tools
- **Custom Slash Commands**: `/pm:daily-standup`, `/pm:sprint-progress`
- **Health Monitoring**: Automated project health checks
- **Cross-Project Coordination**: Dependency tracking and resolution