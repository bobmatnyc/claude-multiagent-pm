## **[M01-035]** Create Managed Project Template to Standardize New Project Setup

**Type**: Framework Enhancement  
**Phase**: M01 Foundation  
**Sprint**: S01  
**Priority**: High  
**Story Points**: 5  
**Assignee**: @framework-team  
**Status**: Ready  
**Dependencies**: M01-034 (Lessons learned from py-mcp-ipc setup)

**Description:**
Create a comprehensive template system for new managed projects to eliminate confusion and ensure consistent structure. This template should standardize directory layout, documentation structure, and task management setup based on lessons learned from the py-mcp-ipc project setup.

**Problem Context:**
During M01-034 (py-mcp-ipc setup), confusion arose about proper file placement:
- Initial attempt to place WORKFLOW.md in trackdown/ directory (incorrect)
- Needed to create docs/ directory and move WORKFLOW.md there
- Missing standard documentation files (INSTRUCTIONS.md, PROJECT.md, TOOLCHAIN.md)
- No template for proper managed project structure

**Solution Requirements:**
Create a template system that provides:
1. **Directory Structure Template** - Standard layout for all managed projects
2. **Documentation Templates** - Boilerplate for required docs files
3. **TrackDown Templates** - Task management system setup
4. **Configuration Templates** - CLAUDE.md and package configuration
5. **Setup Script** - Automated new project creation

**Acceptance Criteria:**

### Template Structure Creation
- [ ] Create `~/Projects/Claude-PM/templates/managed-project/` directory
- [ ] Design standard directory layout based on existing successful projects
- [ ] Include all required documentation templates
- [ ] Provide TrackDown system templates

### Documentation Templates
- [ ] **docs/INSTRUCTIONS.md** - Project overview and quick start template
- [ ] **docs/PROJECT.md** - Executive summary and goals template  
- [ ] **docs/WORKFLOW.md** - Development workflow and TrackDown usage template
- [ ] **docs/TOOLCHAIN.md** - Technology stack and tools template
- [ ] **README.md** - Project root readme template
- [ ] **CLAUDE.md** - Claude PM framework integration template

### TrackDown System Templates
- [ ] **trackdown/BACKLOG.md** - Implementation task tracking template
- [ ] **trackdown/MILESTONES.md** - Phase milestone tracking template
- [ ] **trackdown/templates/task-template.md** - Individual task template
- [ ] **trackdown/templates/milestone-template.md** - Milestone tracking template
- [ ] **trackdown/scripts/update-progress.py** - Progress tracking script

### Configuration Templates
- [ ] **pyproject.toml** - Python project configuration template (if applicable)
- [ ] **package.json** - Node.js project configuration template (if applicable)
- [ ] **.gitignore** - Standard gitignore for managed projects
- [ ] **Makefile** - Standard development commands template

### Setup Automation
- [ ] Create `~/Projects/Claude-PM/scripts/create-managed-project.sh` script
- [ ] Script accepts project name and type (python, nodejs, etc.)
- [ ] Automatically creates directory structure and copies templates
- [ ] Customizes templates with project-specific information
- [ ] Validates setup and provides next steps

**Template Directory Structure:**
```
~/Projects/Claude-PM/templates/managed-project/
├── docs/
│   ├── INSTRUCTIONS.md.template
│   ├── PROJECT.md.template
│   ├── WORKFLOW.md.template
│   └── TOOLCHAIN.md.template
├── trackdown/
│   ├── BACKLOG.md.template
│   ├── MILESTONES.md.template
│   ├── templates/
│   │   ├── task-template.md
│   │   └── milestone-template.md
│   └── scripts/
│       └── update-progress.py
├── config/
│   ├── CLAUDE.md.template
│   ├── pyproject.toml.template
│   ├── package.json.template
│   └── .gitignore.template
├── README.md.template
└── PROJECT_STRUCTURE.md.template
```

**Script Usage Example:**
```bash
# Create new managed project
cd ~/Projects/Claude-PM/scripts
./create-managed-project.sh py-ml-engine python

# Output:
# ✅ Created ~/Projects/managed/py-ml-engine/
# ✅ Standard directory structure created
# ✅ Documentation templates customized
# ✅ TrackDown system initialized
# ✅ CLAUDE.md configured for python project
# 
# Next steps:
# 1. cd ~/Projects/managed/py-ml-engine
# 2. Review and customize docs/PROJECT.md
# 3. Update trackdown/BACKLOG.md with implementation tasks
# 4. Begin development following docs/WORKFLOW.md
```

**Template Variables:**
Templates should support variable substitution:
- `{{PROJECT_NAME}}` - Project directory name
- `{{PROJECT_TITLE}}` - Human-readable project title
- `{{PROJECT_TYPE}}` - python, nodejs, etc.
- `{{CREATION_DATE}}` - Current date
- `{{FRAMEWORK_VERSION}}` - Claude PM framework version

**Quality Standards:**
- [ ] All templates follow established managed project patterns
- [ ] Templates include comprehensive documentation examples
- [ ] Script provides clear error handling and validation
- [ ] Template system is self-documenting
- [ ] Automated testing of template generation

**Testing Requirements:**
- [ ] Test script with different project types (python, nodejs)
- [ ] Verify generated projects match established patterns
- [ ] Validate all template variable substitutions work
- [ ] Ensure generated TrackDown system is functional
- [ ] Test that generated CLAUDE.md integrates properly

**Success Criteria:**
- [ ] Template system successfully creates standardized managed projects
- [ ] No manual directory structure or file creation needed
- [ ] Generated projects match quality of hand-crafted projects
- [ ] Script reduces new project setup time from 30+ minutes to <5 minutes
- [ ] Template eliminates confusion about proper file placement

**Documentation Requirements:**
- [ ] Update `~/Projects/Claude-PM/framework/CLAUDE.md` with template usage
- [ ] Create comprehensive template documentation
- [ ] Document script usage and customization options
- [ ] Provide examples of generated project structures

**Integration Points:**
- [ ] Templates integrate with existing Claude PM framework patterns
- [ ] Generated CLAUDE.md files work with framework health monitoring
- [ ] TrackDown system integrates with framework progress tracking
- [ ] Templates support both standalone and framework-integrated projects

**Future Enhancements:**
- [ ] Support for different project archetypes (web app, cli tool, library)
- [ ] Integration with CI/CD pipeline templates
- [ ] Automated dependency management setup
- [ ] IDE configuration templates (VS Code, PyCharm)

**Definition of Done:**
- [ ] Template system created and tested
- [ ] Script successfully generates new managed projects
- [ ] Generated projects follow all established patterns
- [ ] Documentation complete and integrated with framework
- [ ] Template system validated with at least 2 test projects
- [ ] No remaining confusion about managed project structure

**Implementation Approach:**
1. **Week 1**: Analyze existing successful managed projects for patterns
2. **Week 1**: Design template structure and variable system
3. **Week 1**: Create documentation templates based on py-mcp-ipc success
4. **Week 2**: Implement creation script with validation
5. **Week 2**: Test with multiple project types and validate output
6. **Week 2**: Document system and integrate with framework

**Impact:**
- **Productivity**: Reduce new project setup time by 85%
- **Quality**: Ensure all new projects follow established best practices
- **Consistency**: Eliminate structural variations between projects
- **Onboarding**: Make it easier for new developers to start projects
- **Maintenance**: Reduce time spent on project structure corrections

---

**Ready for Implementation**: This template system will eliminate the confusion experienced during M01-034 and ensure all future managed projects follow established patterns from the start.