---
id: ISS-0008
title: "Migrate mcp-desktop-gateway to Claude Desktop Extensions (CDX)"
type: enhancement
priority: medium
status: new
created: 2025-07-14
sprint: Q3-2025
project: eva-monorepo
epic_id: 
assignee: masa
tags: [migration, cdx, mcp, desktop-gateway]
estimated_tokens: 2000
actual_tokens: 
---

# ISS-0008: Migrate mcp-desktop-gateway to Claude Desktop Extensions (CDX)

**Issue Type**: Enhancement  
**Priority**: Medium  
**Status**: New  
**Created**: 2025-07-14  
**Sprint**: Q3-2025  

## Summary

Migrate the existing mcp-desktop-gateway service from a traditional MCP server implementation to Anthropic's new Claude Desktop Extensions (CDX) format to leverage native extension capabilities and improved user experience.

## Current State Analysis

### Existing Implementation
- **Package**: @bobmatnyc/mcp-desktop-gateway v1.3.1
- **Architecture**: Python-based MCP server with Node.js CLI wrapper
- **Deployment**: pm2-managed service with ecosystem.config.js
- **Features**: 15+ built-in tools, prompt training system, cross-platform support
- **Installation**: NPM global package with automatic Claude Desktop configuration

### Technical Stack
- **Runtime**: Python 3.8+ with virtual environment
- **Process Management**: pm2 with ecosystem configuration
- **Configuration**: Manual Claude Desktop config.json management
- **Tools**: Shell commands, AppleScript, Terminal integration, prompt training
- **Security**: Command filtering, timeouts, sandboxed execution

## Migration Benefits

### User Experience Improvements
1. **One-click Installation**: CDX ".dxt" file format eliminates complex setup
2. **Automatic Updates**: Built-in update mechanism through CDX platform
3. **Simplified Management**: Native extension management in Claude Desktop
4. **Cross-platform Consistency**: "Package once, run anywhere" approach

### Developer Benefits
1. **Simplified Packaging**: Use @anthropic-ai/dxt CLI tools for packaging
2. **Built-in Runtime Management**: Automatic Python environment handling
3. **Secure Configuration**: OS keychain integration for secrets
4. **Template System**: Dynamic configuration with user parameters

### Enterprise Features
1. **Group Policy Support**: MDM integration for enterprise deployment
2. **Private Extension Directory**: Custom extension distribution
3. **Centralized Management**: Blocklist/allowlist capabilities

## Technical Migration Plan

### Phase 1: CDX Architecture Assessment (1-2 weeks)
- [ ] Analyze current mcp-desktop-gateway architecture for CDX compatibility
- [ ] Identify components that map to CDX manifest structure
- [ ] Assess Python runtime requirements within CDX framework
- [ ] Review current npm package structure vs CDX packaging requirements

### Phase 2: Manifest Creation (1 week)
- [ ] Initialize CDX manifest using `npx @anthropic-ai/dxt init`
- [ ] Configure user parameters for:
  - Working directories
  - API keys (OpenAI for prompt training)
  - Timeout settings
  - Connector preferences
- [ ] Define platform-specific runtime configurations
- [ ] Map existing tools to CDX resource/tool definitions

### Phase 3: Packaging Adaptation (2-3 weeks)
- [ ] Restructure project for CDX packaging requirements
- [ ] Migrate from ecosystem.config.js to CDX runtime management
- [ ] Update Python entry points for CDX compatibility
- [ ] Integrate @anthropic-ai/dxt CLI tools into build process
- [ ] Test cross-platform packaging

### Phase 4: Feature Preservation (2-3 weeks)
- [ ] Ensure all 15+ tools maintain functionality in CDX format
- [ ] Migrate prompt training system to work within CDX constraints
- [ ] Preserve security features (command filtering, timeouts)
- [ ] Maintain AppleScript and Terminal integration capabilities
- [ ] Validate connector architecture compatibility

### Phase 5: Testing & Validation (1-2 weeks)
- [ ] Test installation flow on macOS, Linux, Windows
- [ ] Validate all existing tools and connectors
- [ ] Test automatic update mechanism
- [ ] Performance comparison: pm2 vs CDX runtime
- [ ] Security validation in CDX environment

### Phase 6: Documentation & Migration (1 week)
- [ ] Update README and documentation for CDX installation
- [ ] Create migration guide for existing users
- [ ] Update npm package to redirect to CDX version
- [ ] Submit extension to Anthropic directory for review

## Implementation Considerations

### Technical Challenges
1. **Runtime Management**: Transition from pm2 to CDX runtime handling
2. **Python Environment**: Ensure virtual environment compatibility within CDX
3. **Configuration Migration**: Map existing YAML configs to CDX parameters
4. **Tool Registration**: Adapt MCP tool definitions to CDX format
5. **Prompt Training**: Maintain LangChain integration within CDX constraints

### Compatibility Requirements
- Maintain backward compatibility during transition period
- Support both installation methods temporarily
- Preserve all existing tool functionality
- Maintain security posture and command filtering

### Performance Considerations
- Compare CDX runtime overhead vs pm2 management
- Evaluate memory usage in CDX environment
- Assess startup time differences
- Monitor tool execution performance

## Success Criteria

### Primary Goals
- [ ] Full feature parity with existing mcp-desktop-gateway
- [ ] Successful CDX packaging and installation
- [ ] Improved user installation experience
- [ ] Maintained security and performance characteristics

### Quality Metrics
- Installation time reduced by >50%
- User support requests decreased
- Cross-platform compatibility maintained
- All existing tests passing in CDX environment

## Dependencies

### External Dependencies
- Anthropic CDX platform stability and documentation
- @anthropic-ai/dxt CLI tools availability
- Claude Desktop extension directory review process

### Internal Dependencies
- EVA monorepo integration testing
- Event hub communication compatibility
- Memory service integration validation

## Risks & Mitigation

### High Risk
1. **CDX Platform Limitations**: Unknown constraints on Python runtime
   - *Mitigation*: Early prototyping and Anthropic support engagement

2. **Feature Loss**: Prompt training or advanced tools may not be compatible
   - *Mitigation*: Incremental migration with fallback options

### Medium Risk
1. **Performance Regression**: CDX runtime may be slower than pm2
   - *Mitigation*: Benchmark testing and optimization

2. **Enterprise Adoption**: Organizations may prefer traditional deployment
   - *Mitigation*: Maintain both options during transition

## Timeline

**Total Estimated Duration**: 8-12 weeks

- **Week 1-2**: Architecture assessment and CDX learning
- **Week 3**: Manifest creation and initial packaging
- **Week 4-6**: Core migration and packaging adaptation
- **Week 7-9**: Feature preservation and testing
- **Week 10-11**: Validation and performance testing
- **Week 12**: Documentation, submission, and release

## Related Issues

- EP-0004: MCP Desktop Gateway stability and fixes
- ISS-0001: Published mcp-desktop-gateway v1.2.0 with Safari fixes

## Additional Notes

This migration represents a strategic move toward Anthropic's preferred extension distribution model while maintaining the robust functionality that makes mcp-desktop-gateway valuable. The CDX format should significantly improve the user experience while providing better long-term sustainability and enterprise support.

The migration will be implemented as a parallel track initially, allowing users to choose between traditional npm installation and the new CDX format until the CDX version is fully validated and adopted.