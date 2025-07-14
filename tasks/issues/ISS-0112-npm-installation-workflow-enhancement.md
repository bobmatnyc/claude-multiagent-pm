---
issue_id: ISS-0112
title: NPM Installation Workflow Enhancement
description: |-
  ## Overview
  Enhance NPM installation workflow where NPM handles all script/template installation, and claude-pm focuses on deployment, verification, and launch operations.

  ## Core Architecture:
  - NPM installs all components (scripts, templates, agents) to unified location
  - claude-pm becomes deployment/verification/launch tool only
  - Framework deployment required - exit with error if not deployed
  - Clear separation of concerns between installation and deployment

  ## Installation Flow:
  1. NPM: Download and install all components
  2. NPM: Set up initial directory structure  
  3. claude-pm: Deploy framework to working directory
  4. claude-pm: Verify deployment integrity
  5. claude-pm: Launch framework operations

  ## Priority: Critical (Architecture Foundation)
status: active
priority: critical
assignee: masa
created_date: 2025-07-14T01:48:03.000Z
updated_date: 2025-07-14T01:48:03.000Z
estimated_tokens: 15000
actual_tokens: 0
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
related_tasks: []
related_issues: [EP-0037, ISS-0079]
completion_percentage: 0
blocked_by: []
blocks: []
---

# Issue: NPM Installation Workflow Enhancement

## Description
Enhance NPM installation workflow where NPM handles all script/template installation, and claude-pm focuses on deployment, verification, and launch operations.

## Background
Currently there's confusion between installation and deployment phases. This enhancement creates a clear separation where NPM handles the installation of all components, and claude-pm becomes a deployment/verification/launch tool that requires framework to be pre-installed.

## Core Architecture Principles

### 1. Installation vs Deployment Separation
- **NPM Responsibility**: Download, install, and set up all framework components
- **claude-pm Responsibility**: Deploy framework to working directories, verify, and launch
- **Clear Boundaries**: No overlap between installation and deployment concerns

### 2. Framework Deployment Requirement
- **Mandatory Deployment**: claude-pm requires framework to be deployed before operation
- **Exit with Error**: If framework not deployed, exit with clear error message and instructions
- **Validation**: Comprehensive deployment validation before any operations

### 3. Unified Component Management
- **Single Installation Location**: All components installed to `~/.claude-pm/`
- **Centralized Management**: NPM manages all component downloads and updates
- **Version Consistency**: Ensure all components are version-aligned

## NPM Installation Responsibilities

### 1. Component Download and Installation
```json
{
  "postinstall": "node install/postinstall.js",
  "scripts": {
    "setup": "node install/setup-framework.js",
    "verify": "node install/verify-installation.js",
    "deploy-scripts": "node install/deploy-scripts.js"
  }
}
```

### 2. Directory Structure Creation
```
~/.claude-pm/
├── bin/                 # Executable scripts (installed by NPM)
├── templates/           # Configuration templates (installed by NPM)
├── agents/              # Agent implementations (installed by NPM)
├── framework/           # Framework core files (installed by NPM)
├── config/              # Configuration templates (installed by NPM)
├── backups/             # Backup storage (created by NPM)
└── logs/                # Log storage (created by NPM)
```

### 3. Component Installation Process
1. **Download Framework**: Download latest framework components
2. **Install Scripts**: Deploy executable scripts to `~/.claude-pm/bin/`
3. **Install Templates**: Deploy templates to `~/.claude-pm/templates/`
4. **Install Agents**: Deploy agent implementations to `~/.claude-pm/agents/`
5. **Configure Environment**: Set up initial configuration files
6. **Validate Installation**: Run installation validation tests

## claude-pm Deployment Responsibilities

### 1. Framework Deployment Validation
```python
class FrameworkDeploymentValidator:
    def validate_framework_installed(self) -> bool
    def validate_component_integrity(self) -> Dict[str, bool]
    def validate_version_compatibility(self) -> bool
    def generate_validation_report(self) -> Dict[str, Any]
```

### 2. Working Directory Deployment
```python
class WorkingDirectoryDeployer:
    def deploy_framework_to_working_dir(self) -> bool
    def create_project_structure(self) -> bool
    def configure_project_settings(self) -> bool
    def validate_deployment(self) -> bool
```

### 3. Mandatory Deployment Check
```python
def require_framework_deployment():
    """Exit with error if framework not properly deployed."""
    if not validate_framework_installed():
        print("ERROR: Claude PM Framework not deployed.")
        print("Run deployment command first:")
        print("  claude-pm deploy")
        print("  # or")
        print("  npm run deploy")
        sys.exit(1)
```

## Installation Flow Enhancement

### Phase 1: NPM Installation
1. **Package Download**: NPM downloads @bobmatnyc/claude-pm package
2. **Postinstall Script**: Automatically runs postinstall configuration
3. **Component Installation**: Installs all framework components to `~/.claude-pm/`
4. **Environment Setup**: Configures PATH and environment variables
5. **Initial Validation**: Verifies installation completeness

### Phase 2: Framework Deployment
1. **Deployment Command**: User runs `claude-pm deploy` or `npm run deploy`
2. **Working Directory Setup**: Framework deployed to current working directory
3. **Project Configuration**: Project-specific configuration created
4. **Deployment Validation**: Comprehensive validation of deployment
5. **Ready State**: Framework ready for project operations

### Phase 3: Operation Verification
1. **Startup Validation**: Every claude-pm command validates deployment
2. **Component Check**: Verify all required components available
3. **Version Compatibility**: Ensure version alignment across components
4. **Health Monitoring**: Continuous monitoring of framework health

## Error Handling and User Guidance

### 1. Framework Not Installed Error
```
ERROR: Claude PM Framework not installed.

The framework must be installed via NPM before use.

Installation Steps:
1. Install the NPM package:
   npm install -g @bobmatnyc/claude-pm

2. Verify installation:
   claude-pm --version

3. Deploy to current project:
   claude-pm deploy

For more information, visit: https://github.com/bobmatnyc/claude-pm
```

### 2. Framework Not Deployed Error
```
ERROR: Claude PM Framework not deployed to current directory.

The framework must be deployed before use in this project.

Deployment Steps:
1. Deploy framework:
   claude-pm deploy

2. Verify deployment:
   claude-pm status

3. Initialize project:
   claude-pm init

Current directory: /path/to/project
Framework location: ~/.claude-pm/
```

### 3. Version Mismatch Error
```
ERROR: Framework version mismatch detected.

Installed framework: v0.6.1
Required framework: v0.6.2

Update Steps:
1. Update NPM package:
   npm update -g @bobmatnyc/claude-pm

2. Redeploy framework:
   claude-pm deploy --force

3. Verify version:
   claude-pm --version
```

## Tasks
- [ ] Redesign NPM postinstall script for complete component installation
- [ ] Implement framework deployment validation system
- [ ] Create working directory deployment mechanism
- [ ] Build mandatory deployment checking for all claude-pm commands
- [ ] Implement clear error messages and user guidance
- [ ] Create deployment verification and health checking
- [ ] Build version compatibility validation
- [ ] Implement deployment rollback capabilities
- [ ] Create comprehensive installation testing
- [ ] Update documentation for new installation flow
- [ ] Implement deployment status and diagnostic commands
- [ ] Create deployment repair and recovery mechanisms

## Acceptance Criteria
- [ ] NPM handles all component installation automatically
- [ ] claude-pm requires framework deployment before any operations
- [ ] Clear error messages guide users through installation and deployment
- [ ] All components installed to unified `~/.claude-pm/` location
- [ ] Framework deployment to working directories works reliably
- [ ] Version compatibility validation prevents mismatched components
- [ ] Installation success rate >98% across supported platforms
- [ ] Deployment validation comprehensive and reliable
- [ ] User guidance clear and actionable for all error scenarios
- [ ] Rollback capabilities for failed deployments

## Technical Specifications

### NPM Package Configuration
- Postinstall script: Complete framework installation
- Bin configuration: Deploy claude-pm command globally
- File inclusion: All framework components bundled
- Dependency management: All required dependencies included

### Deployment Validation
- Component integrity checking
- Version compatibility validation
- Configuration completeness verification
- Permission and access validation

### Error Recovery
- Deployment repair mechanisms
- Component reinstallation capabilities
- Configuration restoration
- Backup and rollback systems

## Performance Requirements
- NPM installation: <120 seconds for complete setup
- Framework deployment: <30 seconds to working directory
- Deployment validation: <5 seconds for complete check
- Error detection: <2 seconds for validation failures

## Testing Requirements
- Test NPM installation on all supported platforms
- Test framework deployment in various project structures
- Test error scenarios and recovery mechanisms
- Test version compatibility across framework versions
- Test deployment validation in various states

## Documentation Requirements
- Updated installation guide for new workflow
- Framework deployment documentation
- Error resolution guide
- Troubleshooting documentation for deployment issues

## Notes
This enhancement creates a clear architectural separation between installation (NPM's responsibility) and deployment (claude-pm's responsibility), improving reliability and user experience while maintaining consistency across all supported platforms.

Related to EP-0037 (robust Mac installation system) and ISS-0079 (installer architecture).