# Claude PM - Project Management Framework

**Dedicated Repository for Claude Code Project Management**

This repository contains the comprehensive project management framework for all projects in `~/Projects/`, implementing TrackDown-based markdown project management with multi-agent coordination patterns.

## 🏗️ Architecture

### Repository Purpose
- **Separation of Concerns**: Project management separate from project code
- **Clean Git History**: PM decisions tracked independently from code changes
- **Cross-Project Coordination**: Unified view across all projects
- **Framework Evolution**: PM system can evolve without affecting project repos

### Directory Structure
```
Claude-PM/
├── .git/                    # Dedicated PM git repository
├── README.md               # This file
├── trackdown/              # TrackDown project management system
│   ├── BACKLOG.md         # All work items across framework
│   ├── MILESTONES.md      # M01/M02/M03 milestone tracking
│   ├── ROADMAP.md         # Strategic planning
│   ├── RETROSPECTIVES.md  # Sprint retrospectives
│   ├── METRICS.md         # Framework success metrics
│   ├── templates/         # Work item templates
│   ├── scripts/           # Automation and health checks
│   └── archive/           # Completed sprints
├── framework/             # Framework configuration
│   ├── CLAUDE.md         # Master framework config
│   ├── commands/         # Custom slash commands
│   ├── templates/        # Project templates
│   └── workflows/        # Orchestration patterns
├── integration/          # Cross-project coordination
│   ├── project-mapping.json
│   ├── dependency-graph.md
│   └── scripts/
└── docs/                # Framework documentation
    ├── SETUP.md
    ├── WORKFLOWS.md
    └── BEST-PRACTICES.md
```

## 🎯 Framework Principles

### Mandatory Ticket System
**EVERY** task, feature, bug fix, or change requires a TrackDown ticket:
- Format: `[M0X-XXX]` for milestone tasks, `[FEP-XXX]` for framework epics
- No exceptions - even "quick fixes" need tickets
- Ensures complete project visibility and accountability

### Milestone Organization
- **M01 Foundation**: Core infrastructure and essential tooling
- **M02 Automation**: Workflow automation and multi-agent coordination  
- **M03 Orchestration**: Advanced orchestration and enterprise patterns

### Cross-Project Integration
- Unified tracking across all `~/Projects/` repositories
- Standardized CLAUDE.md configurations
- Automated health monitoring and dependency tracking

## 🚀 Quick Start

### Daily Workflow
```bash
# Navigate to PM repository
cd ~/Projects/Claude-PM

# Pull latest PM updates
git pull

# Run framework health check
./trackdown/scripts/health-check.sh

# Update your tasks in BACKLOG.md
# Commit PM changes
git add . && git commit -m "chore: update task status for [M01-XXX]"
git push
```

### Creating New Tasks
1. Copy appropriate template from `trackdown/templates/`
2. Add to BACKLOG.md with proper milestone prefix
3. Commit the PM change to this repository
4. Reference ticket in project work: `git commit -m "feat: implement feature - closes M01-007"`

### Project Integration
Individual project repositories remain focused on code, while this repository manages:
- Task planning and tracking
- Cross-project dependencies
- Framework evolution
- Team coordination

## 🔗 Integration Points

### Project References
- Projects reference PM tickets in commit messages
- Health monitoring scans all `~/Projects/` directories
- Framework templates deployed to individual projects as needed

### Automation
- Custom slash commands: `/pm:daily-standup`, `/pm:health-check`
- Automated project discovery and health monitoring
- Cross-project dependency tracking

## 📊 Success Metrics
- 60%+ productivity improvement over baseline
- <30 minute project setup time
- 70% context switching reduction  
- 90%+ task completion rate

---

**Repository Created**: 2025-07-05
**Framework Version**: v1.0.0-alpha
**Maintenance**: Active development