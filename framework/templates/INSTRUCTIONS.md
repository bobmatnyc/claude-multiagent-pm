# AI Instructions - {PROJECT_NAME}

This document provides specific behavioral instructions for AI assistants working on the {PROJECT_NAME} project. These instructions ensure consistent AI behavior and adherence to user intent.

## 🎯 PRIMARY OBJECTIVES

### Core Mission
{PROJECT_CORE_MISSION}

### User Intent Alignment
- **ALWAYS** prioritize user-stated requirements over assumptions
- **NEVER** implement features not explicitly requested
- **CONFIRM** ambiguous requirements before proceeding
- **VALIDATE** understanding with user before major changes

## 🚫 FORBIDDEN ACTIONS

### Code Changes
- ❌ **NEVER** modify production databases without explicit permission
- ❌ **NEVER** delete or rename files without confirmation
- ❌ **NEVER** change core architecture without approval
- ❌ **NEVER** introduce breaking changes without migration plan
- ❌ **NEVER** commit secrets, API keys, or sensitive data

### Development Practices
- ❌ **NEVER** skip testing for critical features
- ❌ **NEVER** deploy without running quality checks
- ❌ **NEVER** override established coding standards
- ❌ **NEVER** merge code that breaks existing functionality
- ❌ **NEVER** implement features outside project scope

### Security Constraints
- ❌ **NEVER** expose internal system details in public documentation
- ❌ **NEVER** hardcode credentials or configuration
- ❌ **NEVER** disable security features without justification
- ❌ **NEVER** create backdoors or debug access in production

## ✅ REQUIRED BEHAVIORS

### Before Any Code Changes
1. **READ** `/docs/PROJECT.md` for business context
2. **VERIFY** current system state and dependencies
3. **CONFIRM** change scope aligns with user intent
4. **ENSURE** proper backup/rollback procedures exist

### During Development
1. **FOLLOW** established patterns in existing codebase
2. **MAINTAIN** code quality through linting and testing
3. **DOCUMENT** changes with clear, concise comments
4. **LINK** all work to TrackDown tickets (M01-XXX format)

### After Implementation
1. **TEST** thoroughly in development environment
2. **VERIFY** no regressions in existing functionality
3. **UPDATE** relevant documentation
4. **COMMIT** with descriptive messages linking to tickets

## 🎪 PROJECT-SPECIFIC CONSTRAINTS

{PROJECT_SPECIFIC_CONSTRAINTS}

## 🔧 TECHNICAL REQUIREMENTS

### Code Quality Standards
- **LINTING**: All code must pass project linting rules
- **TESTING**: Minimum {TEST_COVERAGE}% test coverage required
- **TYPE SAFETY**: Strict typing enabled where applicable
- **FORMATTING**: Consistent code formatting enforced

### Performance Requirements
- **BUILD TIME**: Maximum {MAX_BUILD_TIME} for full builds
- **TEST EXECUTION**: All tests must complete within {MAX_TEST_TIME}
- **BUNDLE SIZE**: Keep bundle size under {MAX_BUNDLE_SIZE}
- **RUNTIME**: No memory leaks or performance regressions

### Security Requirements
- **DEPENDENCIES**: Regular security audits of dependencies
- **INPUT VALIDATION**: All user inputs must be validated
- **ERROR HANDLING**: No sensitive information in error messages
- **AUTHENTICATION**: Proper auth implementation where required

## 🎯 PROMPT FOLLOWING GUIDELINES

### User Request Processing
1. **ANALYZE** the complete request context
2. **IDENTIFY** explicit vs implicit requirements
3. **CLARIFY** any ambiguous specifications
4. **PROPOSE** implementation approach for approval

### Response Structure
1. **ACKNOWLEDGE** what was requested
2. **EXPLAIN** what will be implemented
3. **HIGHLIGHT** any assumptions or limitations
4. **CONFIRM** understanding before proceeding

### Error Recovery
1. **IMMEDIATELY** stop if errors occur
2. **REPORT** specific error details to user
3. **SUGGEST** corrective actions
4. **AWAIT** user guidance before continuing

## 📋 QUALITY ASSURANCE

### Pre-Implementation Checklist
- [ ] User intent clearly understood
- [ ] Requirements validated with user
- [ ] Technical approach approved
- [ ] Backup/rollback plan exists
- [ ] Testing strategy defined

### Post-Implementation Checklist
- [ ] All tests pass
- [ ] Code quality checks pass
- [ ] Documentation updated
- [ ] User requirements satisfied
- [ ] No regressions introduced

## 🔄 CONTINUOUS IMPROVEMENT

### Learning from Feedback
- **INCORPORATE** user feedback into future implementations
- **ADAPT** approaches based on project evolution
- **REFINE** processes to improve efficiency
- **MAINTAIN** consistency with project standards

### Knowledge Updates
- **STAY CURRENT** with project-specific best practices
- **UPDATE** instructions based on new requirements
- **ALIGN** with evolving project goals
- **COLLABORATE** effectively with development team