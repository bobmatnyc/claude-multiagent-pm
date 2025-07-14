---
issue_id: ISS-0110
title: Remove SuperClaude Template Loaders and Hooks
description: |-
  ## Overview
  Remove non-functional SuperClaude template loaders and hooks that have been proven to have 0% reliability with Claude AI models.

  ## Background
  Technical research has definitively proven that @include directives and SuperClaude template loading mechanisms have 0% reliability with Claude AI models. SuperClaude's creator has confirmed that these features do not work with Claude.

  ## Components to Remove:
  - SuperClaude template loader modules
  - @include directive processors
  - Template inclusion hooks and callbacks
  - Recursive template resolution systems
  - Variable substitution engines related to @include
  - Template validation framework for @include patterns

  ## Replacement Strategy:
  Replace with proven reliable alternatives:
  - CLAUDE.md hierarchy system (proven reliable)
  - Explicit file references instead of @include directives  
  - Agent hierarchy system for configuration management
  - Direct template processing without inclusion mechanisms

  ## Priority: High (Cleanup and Performance)
status: active
priority: high
assignee: masa
created_date: 2025-07-14T01:48:03.000Z
updated_date: 2025-07-14T01:48:03.000Z
estimated_tokens: 8000
actual_tokens: 0
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
related_tasks: []
related_issues: [ISS-0080, ISS-0085]
completion_percentage: 0
blocked_by: []
blocks: []
---

# Issue: Remove SuperClaude Template Loaders and Hooks

## Description
Remove non-functional SuperClaude template loaders and hooks that have been proven to have 0% reliability with Claude AI models.

## Background
Technical research has definitively proven that @include directives and SuperClaude template loading mechanisms have 0% reliability with Claude AI models. SuperClaude's creator has confirmed that these features do not work with Claude.

## Components to Remove

### 1. Template Loader Modules
- Remove all SuperClaude-inspired template loader classes
- Remove template inclusion processors
- Remove recursive template resolution mechanisms
- Clean up associated configuration files

### 2. @include Directive Processors
- Remove @include directive parsing logic
- Remove template inclusion hooks
- Remove recursive inclusion resolution
- Clean up template caching systems related to @include

### 3. Template Validation Framework
- Remove @include-specific validation rules
- Remove template dependency checking for inclusions
- Clean up circular reference detection for @include patterns
- Remove template compilation systems

### 4. Variable Substitution Engines
- Remove variable substitution engines tied to @include systems
- Clean up template variable processing for inclusions
- Remove context passing mechanisms for included templates

## Replacement Strategy

### Proven Reliable Alternatives
1. **CLAUDE.md Hierarchy System**: Use proven reliable CLAUDE.md deployment hierarchy
2. **Explicit File References**: Replace @include with direct file path references
3. **Agent Hierarchy System**: Use three-tier agent hierarchy for configuration
4. **Direct Template Processing**: Process templates directly without inclusion mechanisms

### Migration Approach
1. **Identify Dependencies**: Catalog all components using SuperClaude template loaders
2. **Create Replacement Implementations**: Build direct alternatives using reliable patterns
3. **Update References**: Change all @include references to explicit file paths
4. **Test Migration**: Verify all functionality works with replacement systems
5. **Remove Legacy Code**: Clean up all SuperClaude template loader code

## Tasks
- [ ] Audit codebase for SuperClaude template loader usage
- [ ] Identify all @include directive implementations
- [ ] Create migration plan for dependent components
- [ ] Implement replacement using CLAUDE.md hierarchy
- [ ] Update all template references to use explicit paths
- [ ] Remove template loader classes and modules
- [ ] Remove @include directive processors
- [ ] Clean up template validation framework
- [ ] Update documentation to reflect changes
- [ ] Test all template processing functionality
- [ ] Verify no performance regressions
- [ ] Clean up unused configuration files

## Acceptance Criteria
- [ ] All SuperClaude template loaders removed from codebase
- [ ] No @include directive processors remain
- [ ] All template functionality works with replacement systems
- [ ] No performance regressions detected
- [ ] Documentation updated to reflect changes
- [ ] All tests pass with new template system
- [ ] Code cleanup removes all unused SuperClaude components
- [ ] Migration maintains backward compatibility where possible

## Technical Specifications

### Files to Review and Clean Up
- Template loading modules in framework core
- Configuration processors with @include support
- Agent template systems using SuperClaude patterns
- Documentation referencing @include functionality

### Performance Requirements
- Template processing speed maintained or improved
- Memory usage reduced by removing complex inclusion logic
- Startup time improved by simplifying template system

### Security Considerations
- Remove complex template inclusion attack vectors
- Simplify template validation requirements
- Reduce template processing complexity

## Notes
This cleanup directly addresses the proven unreliability of SuperClaude template inclusion mechanisms with Claude AI models. The replacement with CLAUDE.md hierarchy and explicit file references provides a more reliable and maintainable solution.

Related to ISS-0080 (closed - @include system) and ISS-0085 (closed - advanced template system with conditional processing).