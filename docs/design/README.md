# Design Documentation Guide

Welcome to the Claude PM Framework design documentation. This directory contains templates and examples to help you create effective design documents before implementing features or refactoring code.

## 📋 Why Design Documents?

Design documents help you:
- **Plan before coding**: Think through the problem and solution space
- **Communicate clearly**: Share your approach with team members and AI agents
- **Avoid scope creep**: Define clear boundaries and success criteria
- **Enable better reviews**: Give reviewers context and decision rationale
- **Improve AI assistance**: Provide Claude with clear goals and constraints

## 🎯 When to Write Design Docs

### Always Create Design Docs For:
- **New Features**: Any significant new functionality
- **Major Refactoring**: Large-scale code restructuring
- **Architecture Changes**: Modifications to system design
- **Performance Optimization**: Changes targeting performance improvements
- **Security Updates**: Authentication, authorization, or data protection changes
- **Breaking Changes**: Any changes that affect public APIs or user workflows

### Consider Design Docs For:
- **Bug Fixes**: Complex bugs that require architectural understanding
- **Library Upgrades**: Major version updates that might affect multiple components
- **Configuration Changes**: Updates to build systems, deployment, or environment configs
- **Documentation Updates**: Large-scale documentation restructuring

## 📚 Available Templates

### 1. [Refactoring Design Doc Template](./refactoring-design-doc-template.md)
**Use for**: Code modernization, structure improvements, technical debt reduction

**Key Sections**:
- Problem statement and current issues
- Target architecture and key changes
- Risk analysis and testing strategy
- Implementation phases with timelines
- Size constraints and quality standards

**Perfect for prompts like**:
- "Refactor file src/auth.js to keep line size under 100 characters"
- "Modernize components/ directory to use TypeScript"
- "Split large utils.js file into focused modules"

### 2. [TypeScript Refactoring Example](./typescript-refactoring-example.md)
**Use for**: JavaScript to TypeScript migration guidance

**Demonstrates**:
- Before/after code examples
- Type definition strategies
- Validation layer improvements
- Error handling modernization
- Performance considerations

**Perfect for understanding**:
- How to structure TypeScript conversions
- Best practices for type safety
- Integration with validation libraries
- Maintaining backward compatibility

### 3. Feature Design Doc Template *(Coming Soon)*
**Use for**: New feature development, API design, system additions

### 4. Architecture Design Doc Template *(Coming Soon)*
**Use for**: System-wide changes, microservice design, data flow modifications

## 🚀 Quick Start Guide

### Step 1: Choose Your Template
- **Refactoring existing code?** → Use [Refactoring Template](./refactoring-design-doc-template.md)
- **Converting to TypeScript?** → Reference [TypeScript Example](./typescript-refactoring-example.md)
- **Building new features?** → Feature template (coming soon)

### Step 2: Copy and Customize
```bash
# Copy template to your project
cp docs/design/refactoring-design-doc-template.md docs/my-auth-refactor.md

# Edit with your specific details
# Fill in all sections before starting implementation
```

### Step 3: Get Review and Approval
- Share with team members for feedback
- Include link in your Claude PM prompts
- Update status as you progress through implementation

### Step 4: Implement with Clear Goals
```bash
# Example prompt with design doc context
claude-pm
> "Following the design in docs/my-auth-refactor.md, refactor src/auth/ 
  module to TypeScript with strict typing. Focus on the validation 
  layer first as outlined in Phase 2."
```

## 💡 Best Practices

### Design Document Writing
1. **Be Specific**: Include exact file paths, line counts, and success metrics
2. **Show Examples**: Use before/after code snippets for clarity
3. **Consider Constraints**: Document size limits, performance requirements, and technology restrictions
4. **Plan for Risk**: Include rollback strategies and testing approaches
5. **Define "Done"**: Clear completion criteria and quality gates

### Working with Claude PM
1. **Reference Your Design**: Always mention your design doc in prompts
2. **Break Down Phases**: Implement in the phases outlined in your design
3. **Validate Frequently**: Check progress against your success criteria
4. **Update as Needed**: Revise design docs when you discover new requirements

### Monorepo Considerations
For monorepo projects, consider creating package-specific design docs:
```
docs/
├── design/
│   ├── README.md (this file)
│   └── templates/
└── packages/
    ├── shared-ui/
    │   └── design/
    │       └── component-library-redesign.md
    ├── api-server/
    │   └── design/
    │       └── auth-service-refactor.md
    └── mobile-app/
        └── design/
            └── state-management-migration.md
```

## 🔗 Integration with Claude PM

### Simple Prompt Examples
Once you have a design doc, your prompts become much more effective:

**Instead of**: "Refactor the authentication code"
**Try**: "Following docs/auth-refactor-design.md, convert src/auth/ to TypeScript maintaining the interface contracts defined in Phase 1"

**Instead of**: "Make the code better" 
**Try**: "Implement the validation layer described in docs/user-input-validation-design.md, focusing on the Zod schemas and error handling patterns"

**Instead of**: "Fix performance issues"
**Try**: "Execute the optimization plan in docs/performance-improvement-design.md, starting with the database query improvements in Phase 1"

### Validation and Feedback
Claude PM agents can help validate your design docs:
```bash
claude-pm
> "Review docs/my-design.md and identify any missing considerations 
  for a TypeScript migration project. Are there any risks or 
  implementation details I should add?"
```

## 📖 Additional Resources

### Related Documentation
- [User Guide](../user-guide/README.md) - Complete framework usage guide
- [Architecture Concepts](../user-guide/02-architecture-concepts.md) - Understanding the framework structure
- [Troubleshooting](../user-guide/07-troubleshooting-faq.md) - Common issues and solutions

### External References
- [C4 Architecture Model](https://c4model.com/) - For system architecture documentation
- [ADR (Architecture Decision Records)](https://adr.github.io/) - For documenting architectural decisions
- [RFC Process](https://en.wikipedia.org/wiki/Request_for_Comments) - For proposal and review workflows

## ✅ Template Checklist

Before starting implementation, ensure your design doc includes:

- [ ] **Clear problem statement** with specific examples
- [ ] **Defined scope** with file paths and size estimates  
- [ ] **Success criteria** with measurable outcomes
- [ ] **Risk analysis** with mitigation strategies
- [ ] **Implementation phases** with realistic timelines
- [ ] **Quality constraints** (line length, complexity, test coverage)
- [ ] **Testing strategy** including rollback plans
- [ ] **Definition of done** with completion checklist

## 🤝 Contributing

Found issues with templates or have suggestions for new ones?
- Create an issue describing the template need
- Propose improvements to existing templates
- Share successful design docs as examples

---

**Remember**: Good design docs make for better implementation. Take time to plan, and Claude PM will help you execute more effectively.