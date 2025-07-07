# Claude PM Operations Guide

## Project Overview
Dedicated project management repository providing framework configuration, TrackDown system, and orchestration for all managed projects.

**Repository**: `~/Projects/Claude-PM/`
**Tech Stack**: Markdown, Shell Scripts, YAML
**Purpose**: Centralized project management and coordination framework

## Repository Structure

### Core Directories
```
~/Projects/Claude-PM/
├── .git/                   # PM-specific git tracking
├── trackdown/              # TrackDown task management system
├── framework/              # Framework configuration
├── integration/            # Cross-project coordination
├── ops/                    # Operations documentation
└── docs/                   # PM documentation
```

### Key Files
- **CLAUDE.md** - Main framework configuration
- **trackdown/BACKLOG.md** - Central task tracking
- **trackdown/MILESTONES.md** - Milestone planning
- **ops/index.md** - Operations documentation index
- **integration/project-mapping.json** - Project relationships

## TrackDown System

### Ticket Management
**Location**: `~/Projects/Claude-PM/trackdown/BACKLOG.md`

#### Ticket Format
```markdown
## [M01-007] Core Infrastructure Setup
**Status**: In Progress
**Priority**: High
**Milestone**: M01 Foundation
**Assigned**: Claude Code
**Created**: 2025-07-05
**Due**: 2025-07-15

### Description
Set up core infrastructure components for the Claude PM framework.

### Acceptance Criteria
- [ ] Repository structure established
- [ ] TrackDown system operational
- [ ] Basic documentation complete

### Implementation Notes
- Focus on minimal viable structure
- Ensure clean separation between PM and code
```

#### Ticket Prefixes
- **M01-XXX** - Milestone 1 (Foundation)
- **M02-XXX** - Milestone 2 (Automation) 
- **M03-XXX** - Milestone 3 (Orchestration)
- **FEP-XXX** - Feature Enhancement Proposal
- **BUG-XXX** - Bug fixes
- **DOC-XXX** - Documentation tasks

### Workflow Commands
```bash
# Daily workflow
cd ~/Projects/Claude-PM
git pull

# Check current tasks
cat trackdown/BACKLOG.md | grep "Status.*In Progress"

# Update task status
# Edit BACKLOG.md manually

# Commit changes
git add trackdown/BACKLOG.md
git commit -m "chore: update M01-007 status"
git push
```

## Framework Configuration

### Main Configuration
**File**: `~/Projects/Claude-PM/framework/CLAUDE.md`

This file contains detailed framework instructions including:
- Configuration hierarchies
- Multi-agent coordination patterns
- Project memory management
- Integration specifications

### Local Services Configuration
**File**: `~/Projects/Claude-PM/framework/LOCAL_SERVICES.md`

Documents local service configurations:
- Port assignments
- Service dependencies
- Health check procedures
- Integration points

## Operations Documentation

### Operations Index
**File**: `~/Projects/Claude-PM/ops/index.md`

Central index of all operational documentation including:
- Project-specific operation guides
- Deployment procedures
- Service management
- Troubleshooting guides

### Individual Project Ops
Each managed project has dedicated ops documentation:
- `ops/mem0ai.md` - Memory service operations
- `ops/ai-code-review.md` - Code review tool operations
- `ops/eva-agent.md` - EVA agent operations
- `ops/vercel.md` - Vercel deployment procedures

## Health Monitoring

### Health Check Script
**File**: `~/Projects/Claude-PM/trackdown/scripts/health-check.sh`

```bash
#!/bin/bash
# Framework health monitoring

echo "=== Claude PM Framework Health Check ==="

# Check repository status
echo "Repository Status:"
git status --porcelain

# Check milestone progress
echo "Milestone Progress:"
grep -c "Status.*Completed" trackdown/BACKLOG.md
grep -c "Status.*In Progress" trackdown/BACKLOG.md
grep -c "Status.*Pending" trackdown/BACKLOG.md

# Check operations documentation
echo "Operations Documentation:"
ls -la ops/*.md | wc -l

# Check integration status
echo "Integration Status:"
cat integration/project-mapping.json | jq '.projects | length'

echo "=== Health Check Complete ==="
```

### Usage
```bash
cd ~/Projects/Claude-PM
./trackdown/scripts/health-check.sh
```

## Project Integration

### Project Mapping
**File**: `~/Projects/Claude-PM/integration/project-mapping.json`

```json
{
  "projects": {
    "mem0ai": {
      "path": "~/Projects/_archive/mem0ai/",
      "type": "service",
      "status": "active",
      "port": 8766,
      "ops_file": "ops/mem0ai.md"
    },
    "ai-code-review": {
      "path": "~/Projects/ai-code-review/",
      "type": "tool",
      "status": "active",
      "ops_file": "ops/ai-code-review.md"
    },
    "eva-agent": {
      "path": "~/Projects/_archive/eva-agent/",
      "type": "agent",
      "status": "archived",
      "ops_file": "ops/eva-agent.md"
    }
  },
  "services": {
    "mem0ai": {
      "url": "http://localhost:8766",
      "health_endpoint": "/docs",
      "dependencies": []
    }
  }
}
```

### Cross-Project Coordination
```bash
# Check project status
python integration/check_project_status.py

# Update project mapping
python integration/update_mapping.py

# Generate project report
python integration/generate_report.py
```

## Milestone Management

### Milestone Structure
**File**: `~/Projects/Claude-PM/trackdown/MILESTONES.md`

```markdown
# M01 Foundation
**Goal**: Core infrastructure and essential tooling
**Status**: In Progress
**Due Date**: 2025-07-31

## Key Deliverables
- [x] Repository structure
- [x] TrackDown system
- [x] Operations documentation
- [ ] MCP services integration
- [ ] Automated health monitoring

# M02 Automation  
**Goal**: Workflow automation and multi-agent coordination
**Status**: Planning
**Due Date**: 2025-08-31

# M03 Orchestration
**Goal**: Advanced orchestration and enterprise patterns
**Status**: Planning
**Due Date**: 2025-09-30
```

### Milestone Commands
```bash
# Check milestone progress
grep -A 10 "# M01 Foundation" trackdown/MILESTONES.md

# Update milestone status
# Edit MILESTONES.md manually

# Generate milestone report
python trackdown/scripts/milestone-report.py
```

## Git Workflow

### Branch Strategy
- **main** - Stable framework configuration
- **develop** - Integration testing
- **feature/milestone-XX** - Milestone-specific work

### Commit Conventions
```bash
# Framework updates
git commit -m "feat: add operations documentation structure"

# Task updates
git commit -m "chore: update M01-007 status to completed"

# Documentation
git commit -m "docs: add troubleshooting guide for mem0ai"

# Bug fixes
git commit -m "fix: correct health check script permissions"
```

### Daily Workflow
```bash
# Morning routine
cd ~/Projects/Claude-PM
git pull
./trackdown/scripts/health-check.sh

# Work in individual projects
cd ~/Projects/[project-name]
# Reference PM tickets in commits

# Evening update
cd ~/Projects/Claude-PM
# Update task status in BACKLOG.md
git add .
git commit -m "chore: daily task status update"
git push
```

## Custom Commands

### Planned Commands
- `/pm:daily-standup` - Generate daily status report
- `/pm:health-check` - Run framework health monitoring
- `/pm:create-ticket` - Create new TrackDown ticket
- `/pm:milestone-progress` - Show milestone progress

### Implementation
Commands will be implemented as:
1. Shell scripts in `trackdown/scripts/`
2. Python utilities in `integration/`
3. MCP tools for Claude Code integration

## Monitoring & Metrics

### Key Metrics
- **Story Points Completed**: Tracked in BACKLOG.md
- **Milestone Progress**: Percentage completion
- **Project Health**: Service availability
- **Documentation Coverage**: Ops files per project

### Reporting
```bash
# Weekly report
python trackdown/scripts/weekly-report.py

# Milestone dashboard
python trackdown/scripts/milestone-dashboard.py

# Project health summary
python integration/health-summary.py
```

## Troubleshooting

### Common Issues

#### Git Conflicts
```bash
# Resolve BACKLOG.md conflicts
git checkout --theirs trackdown/BACKLOG.md
# Manually merge changes
git add trackdown/BACKLOG.md
git commit -m "resolve: merge BACKLOG.md updates"
```

#### Missing Operations Documentation
```bash
# Check for missing ops files
python integration/check_ops_coverage.py

# Generate template ops file
python ops/generate_template.py --project [project-name]
```

#### Health Check Failures
```bash
# Debug health check
bash -x trackdown/scripts/health-check.sh

# Fix permissions
chmod +x trackdown/scripts/*.sh

# Update health check
# Edit trackdown/scripts/health-check.sh
```

## Maintenance

### Regular Tasks
```bash
# Weekly cleanup
python trackdown/scripts/cleanup.py

# Update project mapping
python integration/update_mapping.py

# Backup framework data
tar -czf claude-pm-backup-$(date +%Y%m%d).tar.gz \
  trackdown/ framework/ ops/ integration/
```

### Updates
```bash
# Update framework version
# Edit framework/CLAUDE.md version number

# Update operations documentation
# Review and update ops/*.md files

# Commit updates
git add .
git commit -m "chore: framework maintenance update"
git push
```

---

**Repository**: ~/Projects/Claude-PM/
**Framework Version**: v1.0.0-alpha
**Architecture**: Separated PM/Code repositories
**TrackDown Location**: trackdown/BACKLOG.md
**Health Check**: trackdown/scripts/health-check.sh
**Last Updated**: 2025-07-05