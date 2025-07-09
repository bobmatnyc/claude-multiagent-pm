## **[M01-020]** Create Claude PM Portfolio Manager as new managed project

**Type:** Milestone Task  
**Milestone:** M01_Foundation  
**Epic:** FEP-001 Framework Infrastructure Setup  
**Priority:** High  
**Story Points:** 8  
**Assignee:** @claude  
**Status:** Pending  
**Sprint:** S01  
**Projects Affected:** claude-pm-portfolio-manager (new)

**Description:**
Create a specialized portfolio management dashboard specifically for Claude PM managed projects. This will be a React-based dashboard that monitors and reports on all projects under Claude PM management, including TrackDown tickets, project health, milestones, and framework metrics.

**Milestone Context:**
- Provides dedicated visibility into Claude PM framework operations
- Enables monitoring of managed projects specifically (~/Projects/managed/*)
- Integrates with TrackDown system for ticket and milestone tracking
- Critical for achieving framework monitoring and reporting capabilities (Level 2)

**Acceptance Criteria:**
- [ ] Create new project directory: `~/Projects/managed/claude-pm-portfolio-manager/`
- [ ] Set up Node.js/React project structure with TypeScript
- [ ] Create comprehensive CLAUDE.md configuration for project-specific development
- [ ] Establish package.json with all necessary dependencies and scripts
- [ ] Set up development toolchain (TypeScript, ESLint, testing framework)
- [ ] Create initial project structure following best practices
- [ ] Configure git repository with proper .gitignore
- [ ] Add project to Claude-PM framework mapping and health monitoring
- [ ] Create development environment setup documentation

**Technical Specifications:**
- **Framework**: React with TypeScript
- **Build Tool**: Vite or Next.js (decision to be made during development)
- **Styling**: Tailwind CSS (following existing patterns)
- **State Management**: React Query for server state, Zustand for client state
- **Testing**: Vitest for unit tests, Playwright for e2e
- **Linting**: ESLint + Prettier
- **Package Manager**: npm (consistent with git-portfolio-manager)

**Core Features to Implement:**
1. **Dashboard Overview**
   - Managed projects summary
   - Health status indicators
   - Milestone progress tracking
   - Recent activity feed

2. **TrackDown Integration**
   - Live ticket status from Claude-PM/trackdown/
   - Sprint progress visualization
   - Milestone timeline view
   - Backlog management interface

3. **Project Health Monitoring**
   - Automated health checks for managed projects
   - Git activity tracking
   - Build/test status monitoring
   - Dependency health analysis

4. **Framework Metrics**
   - Productivity improvements tracking
   - Task completion rates
   - Framework maturity level indicators
   - Success metrics dashboard

**Data Sources:**
- `~/Projects/Claude-PM/trackdown/BACKLOG.md` - TrackDown tickets
- `~/Projects/Claude-PM/trackdown/MILESTONES.md` - Milestone data
- `~/Projects/Claude-PM/integration/project-mapping.json` - Project metadata
- `~/Projects/managed/*/` - Managed project directories
- Git repositories for commit activity and health data

**Cross-Project Dependencies:**
- [ ] Must integrate with existing TrackDown system
- [ ] Should reuse patterns from git-portfolio-manager where applicable
- [ ] Needs access to Claude-PM framework configuration
- [ ] Should coordinate with framework health monitoring scripts

**Development Environment:**
- **CLI Development**: Use existing git-portfolio-manager as reference
- **React Dashboard**: Modern React patterns with hooks and functional components
- **API Layer**: RESTful API for data fetching from TrackDown and project sources
- **Real-time Updates**: WebSocket or polling for live dashboard updates

**Definition of Done:**
- [ ] Project directory created in managed subdirectory
- [ ] Complete development environment setup with all tooling
- [ ] CLAUDE.md configuration file complete and comprehensive
- [ ] Package.json with all necessary scripts (dev, build, test, lint)
- [ ] TypeScript configuration and project structure established
- [ ] Git repository initialized with proper .gitignore
- [ ] Development server can start successfully
- [ ] Basic React app renders without errors
- [ ] Project added to Claude-PM framework tracking
- [ ] Documentation ready for development handoff to new Claude instance

**Setup Checklist:**
1. **Directory Structure:**
   - [ ] Create `~/Projects/managed/claude-pm-portfolio-manager/`
   - [ ] Initialize git repository
   - [ ] Create basic project structure

2. **Development Environment:**
   - [ ] Set up package.json with React/TypeScript
   - [ ] Configure build tooling (Vite recommended)
   - [ ] Set up linting and formatting
   - [ ] Configure testing framework

3. **Configuration:**
   - [ ] Create comprehensive CLAUDE.md
   - [ ] Set up TypeScript configuration
   - [ ] Configure development scripts
   - [ ] Set up environment variables template

4. **Framework Integration:**
   - [ ] Add to Claude-PM project mapping
   - [ ] Update health monitoring to include project
   - [ ] Document integration points

5. **Development Handoff:**
   - [ ] Verify all tooling works correctly
   - [ ] Create development setup guide
   - [ ] Prepare for new Claude Code instance

**Success Metrics:**
- Development environment starts without errors
- All package scripts run successfully
- Project properly tracked by Claude-PM framework
- Ready for immediate development by new Claude instance