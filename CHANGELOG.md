# Changelog

All notable changes to the Claude PM Framework will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [2.0.0] - 2025-07-07

### 🚀 Features

#### Major Framework Restructure
- **Multi-Subprocess Orchestration Model**: Complete redesign with 5 specialized subprocess roles per project
- **Context Isolation**: Strict separation between PM context and managed project contexts
- **Writing Authority Boundaries**: Exclusive file type permissions for each subprocess role
- **Claude Code Best Practices Integration**: TDD, API-first design, incremental development enforcement

#### Subprocess Specialization
- **Engineer Subprocess**: Exclusive source code writing authority (.js, .py, .ts, etc.)
- **Ops Subprocess**: Configuration files, deployment scripts, CI/CD configs only
- **QA Subprocess**: Test files, quality assurance scripts only
- **Research Subprocess**: Documentation, best practice guides only
- **Architect Subprocess**: Project scaffolding, API specifications only

#### Business Interface
- **PM Orchestration**: Claude PM as single interface to business stakeholders
- **Filtered Context Sharing**: Role-specific information filtering to subprocesses
- **Learning Management**: Systematic capture and sharing of subprocess learnings
- **Quality Gates**: Multi-phase validation with research, architecture, development, quality, deployment gates

### 📋 Process Improvements

#### Task Management
- **Enhanced Ticket System**: M0X-XXX (milestones), FEP-XXX (features), PROJ-XXX (projects), LRN-XXX (learning)
- **Escalation Protocols**: Automatic PM intervention when subprocesses blocked >2-3 iterations
- **TrackDown Integration**: Learning capture in project trackdown systems
- **Future mem0ai Integration**: Planned persistent learning system

#### Quality Assurance
- **Best Practice Monitoring**: Continuous adherence checking to Claude Code standards
- **Performance Metrics**: Subprocess-specific success metrics and KPIs
- **Anti-Pattern Prevention**: Documentation and avoidance of failed approaches

### 🔧 Technical Infrastructure

#### Repository Structure
- **PM Repository**: Dedicated Claude-PM repo for all orchestration concerns
- **Project Isolation**: Individual projects with no PM framework awareness
- **Context Boundaries**: Strict information filtering between contexts
- **Documentation Separation**: PM docs vs project docs completely separated

#### Development Workflow
- **Research → Architecture → Development → Quality → Deployment**: Sequential workflow with gates
- **Incremental Development**: No >2-3 iteration blocks allowed
- **Learning Propagation**: Cross-subprocess knowledge sharing
- **Business Communication**: Executive summaries and strategic updates

### ⚠️ Breaking Changes

- **Complete Framework Restructure**: v1.x single-context model replaced with multi-subprocess orchestration
- **Context Separation**: Projects can no longer reference PM framework concerns
- **Writing Permissions**: Strict file type permissions enforced per subprocess role
- **Ticket Formats**: New ticket naming conventions for different concern types

### 📊 Success Metrics

#### Target Improvements
- **60%+ Productivity Increase**: Over baseline single-context development
- **70% Context Switching Reduction**: Through specialized subprocess contexts
- **90%+ Task Completion Rate**: Via systematic workflow and quality gates
- **<30 Minute Setup**: For new project initialization

#### Framework Maturity
- **Level 1**: Basic subprocess orchestration ✅ (This release)
- **Level 2**: Automated subprocess coordination (M01 target)
- **Level 3**: Intelligent subprocess routing (M02 target)
- **Level 4**: Self-optimizing subprocess ecosystem (M03 target)

---

### Previous Versions

## [1.0.0] - 2025-07-05

### Features
- Initial Claude PM framework with basic project management
- TrackDown integration
- Health monitoring
- Cross-project coordination
- Single-context development model

### Documentation
- Basic CLAUDE.md framework configuration
- Project management guidelines
- Task tracking system