# AI Code Review CLI Tool Operations Guide

## Service Overview
AI Code Review is a comprehensive TypeScript CLI tool for AI-powered code reviews, supporting multiple AI providers (Gemini, Claude, OpenAI, OpenRouter). This tool provides automated code analysis, security review, architectural assessment, and performance optimization recommendations.

## Local Deployment

### Service Status
- **Type**: CLI Tool (globally installable)
- **Location**: `~/Projects/managed/ai-code-review/`
- **Package**: `@bobmatnyc/ai-code-review`
- **Runtime**: Node.js 20+ with pnpm package manager
- **Build System**: TypeScript 5.8.3 with Biome toolchain

### Service Architecture
- **CLI Interface**: Command-line tool with multiple review strategies
- **AI Providers**: Multi-provider support (Anthropic, Google, OpenAI, OpenRouter)
- **Review Strategies**: Architectural, security, performance, unused code analysis
- **Token Management**: Advanced token counting and estimation
- **Output Formats**: Markdown, JSON, structured reports

### Installation and Setup
```bash
# Navigate to project directory
cd ~/Projects/managed/ai-code-review

# Install dependencies
pnpm install

# Build project
pnpm run build

# Run tests
pnpm test

# Global installation (optional)
npm link
```

## CLI Usage

### Basic Commands
```bash
# Basic code review
ai-code-review --path ./src --strategy quick-fixes

# Multi-pass review with specific model
ai-code-review --path ./src --strategy architectural --model claude-3-sonnet

# Security-focused review
ai-code-review --path ./src --strategy security --output security-report.md

# Performance analysis
ai-code-review --path ./src --strategy performance --format json

# Test specific models
ai-code-review test-model --model gemini-1.5-pro
ai-code-review list-models --provider anthropic
```

### Review Strategies
1. **Quick Fixes**: Fast issue identification and recommendations
2. **Architectural Review**: Deep structural analysis and design patterns
3. **Security Review**: Security vulnerability detection and remediation
4. **Performance Review**: Performance bottleneck identification
5. **Unused Code**: Dead code detection and cleanup recommendations
6. **Extract Patterns**: Code pattern analysis and best practice suggestions

## Environment Configuration

### Required API Keys
All environment variables use the `AI_CODE_REVIEW_` prefix:

```bash
AI_CODE_REVIEW_GOOGLE_API_KEY=your_google_api_key_here
AI_CODE_REVIEW_ANTHROPIC_API_KEY=your_anthropic_api_key_here
AI_CODE_REVIEW_OPENROUTER_API_KEY=your_openrouter_api_key_here
AI_CODE_REVIEW_OPENAI_API_KEY=your_openai_api_key_here
AI_CODE_REVIEW_DEFAULT_MODEL=gemini-1.5-pro
AI_CODE_REVIEW_DEFAULT_STRATEGY=quick-fixes
```

### Configuration Files
- **`.env`**: Local environment variables
- **`.ai-code-review.yaml`**: Project-specific configuration
- **`package.json`**: Project dependencies and scripts
- **`biome.json`**: Linting and formatting configuration

## Development Commands

### Essential Workflow
```bash
# Development workflow
pnpm run lint && pnpm run build:types && pnpm test

# Biome toolchain (10x faster)
pnpm run lint                   # Biome linting
pnpm run lint:fix               # Auto-fix issues
pnpm run format                 # Biome formatting
pnpm run format:check           # Check formatting

# Testing and development
pnpm run dev                    # Run with ts-node
pnpm run test:watch            # Watch mode testing
pnpm run test:coverage         # Coverage reports
```

### Quality Assurance
```bash
# Before any commit
pnpm run lint && pnpm run build:types && pnpm test

# Coverage analysis (target: >70% core code)
pnpm run test:coverage

# End-to-end testing
pnpm run test:e2e
```

## Integration Patterns

### CI/CD Integration
```yaml
# GitHub Actions example
- name: AI Code Review
  run: |
    npx @bobmatnyc/ai-code-review \
      --path src/ \
      --strategy security \
      --format json \
      --output ai-review.json
```

### Pre-commit Hooks
```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ai-code-review
        name: AI Code Review
        entry: ai-code-review --path src/ --strategy quick-fixes
        language: node
```

### IDE Integration
```bash
# VS Code task configuration
{
  "label": "AI Code Review",
  "type": "shell",
  "command": "ai-code-review",
  "args": ["--path", "${workspaceFolder}/src", "--strategy", "quick-fixes"],
  "group": "build"
}
```

## Service Management

### Development Status Check
```bash
cd ~/Projects/managed/ai-code-review

# Check project status
git status
pnpm run lint
pnpm test

# Verify CLI functionality
./dist/index.js --version
./dist/index.js --listmodels

# Check dependencies
pnpm audit
pnpm outdated
```

### Performance Monitoring
```bash
# Token usage analysis
ai-code-review --path src/ --estimate

# Review execution time
time ai-code-review --path src/ --strategy quick-fixes

# Memory usage monitoring
/usr/bin/time -v ai-code-review --path src/ --strategy architectural
```

### Troubleshooting
```bash
# Debug mode
AI_CODE_REVIEW_LOG_LEVEL=debug ai-code-review --path src/ --strategy quick-fixes

# Check API connectivity
ai-code-review test-model --model gemini-1.5-pro
ai-code-review test-model --model claude-3-sonnet

# Validate configuration
ai-code-review --validate-config

# Check error logs
ls -la logs/error-logs/
tail -f logs/error-logs/error-*.json
```

## Output Formats and Analysis

### Report Types
- **Markdown**: Human-readable reports with formatting
- **JSON**: Structured data for CI/CD integration
- **Console**: Interactive terminal output
- **File Output**: Saved reports with timestamps

### Analysis Capabilities
- **Code Quality**: Best practice compliance and maintainability
- **Security Analysis**: Vulnerability detection and remediation
- **Performance Review**: Bottleneck identification and optimization
- **Architectural Assessment**: Design pattern analysis and recommendations
- **Dead Code Detection**: Unused code identification and cleanup

## Remote Deployment

### NPM Package Publishing
```bash
# Build and test
pnpm run build
pnpm test

# Publish to NPM
npm publish --access=public

# Verify publication
npm info @bobmatnyc/ai-code-review
```

### Docker Deployment (Optional)
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install
COPY . .
RUN pnpm run build
ENTRYPOINT ["node", "dist/index.js"]
```

## Monitoring and Maintenance

### Health Checks
```bash
# CLI functionality test
ai-code-review --version

# Model connectivity test
ai-code-review list-models

# Configuration validation
ai-code-review test-model --model gemini-1.5-pro

# Performance benchmark
time ai-code-review --path test-project/ --strategy quick-fixes
```

### Update Procedures
```bash
# Update dependencies
pnpm update

# Run security audit
pnpm audit

# Test after updates
pnpm run lint && pnpm run build:types && pnpm test

# Rebuild and retest
pnpm run build
```

## Common Issues and Solutions

### API Key Issues
```bash
# Verify API keys are set
echo $AI_CODE_REVIEW_GOOGLE_API_KEY | cut -c1-10
echo $AI_CODE_REVIEW_ANTHROPIC_API_KEY | cut -c1-10

# Test API connectivity
ai-code-review test-model --model gemini-1.5-pro
ai-code-review test-model --model claude-3-sonnet
```

### Build Issues
```bash
# Clean rebuild
rm -rf dist/ node_modules/
pnpm install
pnpm run build

# Check TypeScript errors
pnpm run build:types

# Verify dependencies
pnpm install --frozen-lockfile
```

### Performance Issues
```bash
# Check token limits
ai-code-review --path large-project/ --estimate

# Use chunking for large projects
ai-code-review --path large-project/ --chunk-size 50

# Monitor memory usage
/usr/bin/time -v ai-code-review --path project/
```

---

**Service Type**: CLI Development Tool  
**Last Updated**: 2025-07-06  
**Deployment Status**: Locally managed, NPM published  
**Integration**: Claude PM Framework