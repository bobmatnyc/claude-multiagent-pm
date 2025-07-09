---
issue_id: ISS-0052
epic_id: EP-0032
title: Publish claude-pm-portfolio-manager as @bobmatnyc/claude-pm-portfolio-manager NPM package
description: Establish and maintain automated NPM publishing workflow for @bobmatnyc/claude-pm-portfolio-manager package to enable seamless deployment and distribution of the portfolio manager dashboard component for Claude PM Framework integration.
status: planning
priority: high
assignee: devops-team
created_date: 2025-07-09T13:51:29.868Z
updated_date: 2025-07-09T14:30:00.000Z
estimated_tokens: 2400
actual_tokens: 0
ai_context:
  - context/npm-package-analysis
  - context/vite-build-pipeline
  - context/github-actions-workflow
  - context/semantic-versioning
  - context/framework-integration
sync_status: local
related_tasks: []
related_issues: [ISS-0051]
completion_percentage: 15
blocked_by: []
blocks: []
---

# Issue: Publish claude-pm-portfolio-manager as @bobmatnyc/claude-pm-portfolio-manager NPM package

## Description
Establish and maintain automated NPM publishing workflow for `@bobmatnyc/claude-pm-portfolio-manager` package to enable seamless deployment and distribution of the portfolio manager dashboard component for Claude PM Framework integration.

**Current Status**: Package v1.0.0 successfully published to NPM registry (July 9, 2025, 14:09 UTC)

## DevOps Analysis & Requirements

### Current Package Status
- **Package Name**: `@bobmatnyc/claude-pm-portfolio-manager`
- **Current Version**: 1.0.0 (published)
- **Registry**: NPM public registry
- **Main Entry Points**: `dist/index.js` (CJS), `dist/index.mjs` (ESM)
- **TypeScript Definitions**: `dist/index.d.ts`
- **Build System**: Vite with TypeScript and React support
- **Package Size**: 2.97MB unpacked, 43 files included

### Build Pipeline Architecture
- **Build Tool**: Vite 4.4.9 with React plugin
- **TypeScript**: Full TypeScript support with declaration generation
- **Library Mode**: Configured for both ES modules and CommonJS
- **External Dependencies**: React/ReactDOM as peer dependencies
- **Source Maps**: Enabled for production builds
- **Type Generation**: Automated via vite-plugin-dts

### Publishing Workflow Requirements

#### 1. Automated Version Management
- **Current Script**: `npm run publish:npm` (manual)
- **Dry Run Testing**: `npm run publish:dry` available
- **Pre-publish Hook**: `prepublishOnly` runs full build
- **Version Strategy**: Semantic versioning required

#### 2. CI/CD Pipeline Setup
- **Build Validation**: `npm run ci` (check, type-check, test, build)
- **Quality Gates**: Biome linting, TypeScript checking, Vitest testing
- **Deployment Target**: NPM registry with public access
- **GitHub Integration**: Repository linked, requires GitHub Actions setup

#### 3. Release Management
- **Current State**: Manual publishing workflow
- **Required**: Automated release pipeline
- **Versioning**: Major.Minor.Patch semantic versioning
- **Release Notes**: Automated changelog generation needed

## Tasks
- [ ] Analyze current GitHub repository setup and CI/CD capabilities
- [ ] Design automated publishing workflow with GitHub Actions
- [ ] Implement version bump automation (patch/minor/major)
- [ ] Create release validation pipeline (tests, build, security checks)
- [ ] Set up NPM publishing automation with proper token management
- [ ] Configure automated changelog generation
- [ ] Implement rollback procedures for failed releases
- [ ] Create monitoring for package health and download metrics
- [ ] Document publishing workflow for maintainers
- [ ] Test automated workflow with patch release (v1.0.1)

## Acceptance Criteria
- [ ] Automated GitHub Actions workflow publishes to NPM on version tags
- [ ] All quality gates pass before publishing (lint, test, build, security)
- [ ] Semantic versioning is enforced and automated
- [ ] Release notes are automatically generated from commit history
- [ ] NPM package includes only necessary dist files (no source code)
- [ ] TypeScript definitions are properly generated and included
- [ ] Package can be consumed by Claude PM Framework `/cmpm-dashboard` command
- [ ] Publishing workflow supports both manual and automated triggers
- [ ] Rollback mechanism exists for problematic releases
- [ ] Package health monitoring is implemented

## Technical Specifications

### Build Configuration
- **Entry Point**: `src/index.ts` (library mode)
- **Output Formats**: ES modules (.mjs) and CommonJS (.js)
- **Bundle Size**: Optimized for production use
- **External Dependencies**: React ecosystem excluded from bundle

### Distribution Strategy
- **Registry**: NPM public registry (`@bobmatnyc/claude-pm-portfolio-manager`)
- **Access**: Public package with MIT license
- **Maintenance**: Single maintainer (bobmatnyc)
- **Integration**: Direct consumption by Claude PM Framework

### Security Considerations
- **NPM Token**: Secure token management for automated publishing
- **Dependency Scanning**: Automated vulnerability checks
- **Code Signing**: Package integrity verification
- **Access Control**: Proper registry permissions

## Framework Integration Context
This NPM package is critical for the Claude PM Framework's `/cmpm-dashboard` command functionality, enabling:
- Portfolio manager dashboard deployment
- Real-time project monitoring
- Multi-agent coordination interfaces
- Claude PM Framework status reporting

## Notes
- Package already exists and is functional - focus on automation and reliability
- Current manual publishing workflow is operational but needs automation
- Integration with ISS-0051 dashboard command implementation
- Consider semantic-release or similar tools for automated versioning
- Package serves as external dependency for framework dashboard functionality
- Build pipeline is mature and production-ready (Vite + TypeScript + React)
