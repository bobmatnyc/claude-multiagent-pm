# Research Design Doc Workflow Integration

## Integration with Claude PM Commands

### 1. Planning Phase
```bash
# Start with research planning
claude-pm plan research-doc feature-name
# AI helps analyze complexity and suggests research doc if needed

# Create from template
cp ~/.claude-pm/templates/research-design-doc.md ./docs/design/feature-research.md
```

### 2. Analysis Phase
```bash
# AI assists with research questions
claude-pm analyze codebase --focus integration-points
claude-pm research dependencies --for feature-name
```

### 3. Implementation Phase
```bash
# Follow the research plan
claude-pm implement --plan ./docs/design/feature-research.md
# AI references the research doc for implementation decisions
```

### 4. Validation Phase
```bash
# Validate against research criteria
claude-pm test --validate-research-criteria
claude-pm deploy --check-success-criteria
```

## Workflow Decision Tree

```
Project Request
├── Simple/Quick? → Direct Implementation
│   └── claude-pm push
└── Complex/Multi-phase? → Research First
    ├── Create Research Doc
    ├── AI-Assisted Analysis
    ├── Stakeholder Review
    └── Phased Implementation
```

## Benefits
- **Systematic Planning**: Structured approach to complex changes
- **Risk Mitigation**: Identify issues before implementation
- **Team Alignment**: Clear communication of approach and timeline
- **Quality Assurance**: Success criteria defined upfront
- **Knowledge Capture**: Decisions and rationale documented for future reference