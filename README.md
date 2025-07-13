# Claude PM Framework

## TLDR

Claude PM gives you specialized AI agents that handle code review, testing, deployment, and documentation. Install once, use three commands (`push`, `deploy`, `publish`), get autonomous AI help that learns your codebase patterns and prevents mistakes. Perfect for mono-repo environments where you want AI assistance without breaking existing workflows.

## Installation (Mono-Repo Safe)

```bash
# Global install - works across all projects
npm install -g @bobmatnyc/claude-multiagent-pm
npm install -g @bobmatnyc/ai-trackdown-tools

# Navigate to any project and start
cd your-project
claude-pm
```

**Safety**: Claude PM works **alongside** your existing tools without replacing them. It won't modify your build scripts, CI/CD, or deployment processes unless you specifically ask.

## Four Scenarios

### 1. New Project: "Start with AI assistance from day one"

```bash
mkdir my-new-app && cd my-new-app && npm init -y
claude-pm  # AI helps set up structure, testing, docs from start
```
**Benefit**: AI learns your coding style and prevents mistakes early. Perfect for side projects and utilities.

### 2. Mono-Repo Developer: "Safe workspace-scoped usage"

```bash
cd packages/utilities  # Start with one low-risk workspace
claude-pm init --workspace  # Isolated to single workspace only
```
**Safety**: Claude PM detects mono-repo structure and respects workspace boundaries. No interference with Lerna/Nx/Rush.

### 3. Legacy Code Maintainer: "Refactor safely with comprehensive testing"

```bash
cd legacy-project && claude-pm init
claude-pm analyze technical-debt  # Assessment before refactoring
claude-pm suggest tests --comprehensive  # Improve coverage first
```
**Strategy**: Test-driven refactoring with incremental changes. AI suggests improvements while you maintain full control.

### 4. Team Evaluation: "Pilot program with gradual adoption"

```bash
claude-pm team init --name "Development Team"
claude-pm init --workspace  # Start with internal tools only
```
**Approach**: 3-week evaluation (personal → pilot project → team decision). Voluntary participation with safety measures.

## Start Small Recommendation

**Recommended first project**: Try Claude PM on a simple utility or side project first. The AI agents need 2-3 interactions to learn your style effectively. Avoid mission-critical production systems until you're comfortable with the workflow.

**Example small projects**:
- Personal automation scripts
- Small libraries or utilities  
- Documentation projects
- Prototypes or experiments

## Planning Complex Projects

For multi-phase projects beyond simple refactoring, use research design docs:

```bash
claude-pm plan research-doc my-complex-feature
# Creates structured planning template for analysis before implementation
```

**When to use**: Cross-system integration, architectural changes, performance-critical work, team coordination. **When to skip**: Bug fixes, simple features, documentation updates. See [planning guide](./templates/when-to-use-research-docs.md).

## Why Claude PM?

- **Memory**: Learns your patterns and coding style over time
- **Safety**: Suggests changes, never applies automatically
- **Integration**: Works with existing tools and workflows
- **Autonomy**: Handles routine tasks so you focus on architecture

**Documentation**: [Getting Started Guide](./docs/user-guide/01-getting-started.md) | [Framework Overview](./docs/FRAMEWORK_OVERVIEW.md)