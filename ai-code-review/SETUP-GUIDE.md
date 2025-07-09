# AI Code Review Setup Guide

## Overview
This guide documents the setup process for the `@bobmatnyc/ai-code-review` tool for automated code reviews after substantial code changes.

## Prerequisites
- Node.js >= 16.0.0
- npm or pnpm package manager
- API key for AI model provider (OpenAI, Gemini, Anthropic, or OpenRouter)

## Installation

### 1. Install AI Code Review Tool
```bash
# Install globally using npm
npm install -g @bobmatnyc/ai-code-review

# Or install globally using pnpm (recommended)
pnpm add -g @bobmatnyc/ai-code-review
```

### 2. Verify Installation
```bash
ai-code-review --version
# Should display: AI Code Review Tool v4.3.0
```

## Configuration

### 1. Create Environment Configuration
Create a `.env.local` file in your project root:

```bash
# For OpenAI (recommended)
AI_CODE_REVIEW_OPENAI_API_KEY=your_openai_api_key_here
AI_CODE_REVIEW_MODEL=openai:gpt-4o

# For Gemini
AI_CODE_REVIEW_GOOGLE_API_KEY=your_gemini_api_key_here
AI_CODE_REVIEW_MODEL=gemini:gemini-1.5-pro

# For Anthropic Claude
AI_CODE_REVIEW_ANTHROPIC_API_KEY=your_anthropic_api_key_here
AI_CODE_REVIEW_MODEL=anthropic:claude-3.5-sonnet

# For OpenRouter
AI_CODE_REVIEW_OPENROUTER_API_KEY=your_openrouter_api_key_here
AI_CODE_REVIEW_MODEL=openrouter:anthropic/claude-4-sonnet
```

### 2. Generate Configuration File
```bash
ai-code-review generate-config
```

This creates `.ai-code-review.yaml` with default settings.

### 3. Customize Configuration
Edit `.ai-code-review.yaml` to customize settings:

```yaml
output:
  format: markdown
  dir: ./ai-code-review  # Output directory for reviews
review:
  type: quick-fixes      # Review type
  interactive: false
  include_tests: false
  include_project_docs: true
  include_dependency_analysis: true
api:
  model: openai:gpt-4o   # AI model to use
system:
  debug: false
  log_level: info
```

## Usage

### Basic Usage
```bash
# Review current directory with quick-fixes
ai-code-review

# Review specific directory
ai-code-review src/

# Review specific file
ai-code-review src/index.ts
```

### Advanced Usage
```bash
# Architectural review
ai-code-review --type architectural

# Security review
ai-code-review --type security

# Performance review
ai-code-review --type performance

# Find unused code
ai-code-review --type unused-code

# Interactive mode
ai-code-review --interactive

# Use specific model
ai-code-review --model gemini:gemini-1.5-pro

# Custom output directory
ai-code-review --output-dir ./custom-reviews
```

## Review Types

| Type | Description |
|------|-------------|
| `quick-fixes` | Identify low-hanging fruit and easy improvements |
| `architectural` | Holistic review of code structure and APIs |
| `security` | Focus on security vulnerabilities and best practices |
| `performance` | Identify performance bottlenecks and optimizations |
| `unused-code` | Find dead code and unused variables |

## Output

Reviews are saved to the `ai-code-review/` directory (or custom output directory) as markdown files with timestamps.

Example output: `quick-fixes-review-current-dir-openai-gpt-4o-2025-07-08T06-11-43-200Z.md`

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: AI Code Review
on:
  pull_request:
    branches: [main]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-node@v3
      with:
        node-version: '18'
    - run: npm install -g @bobmatnyc/ai-code-review
    - run: ai-code-review --no-confirm
      env:
        AI_CODE_REVIEW_OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    - uses: actions/upload-artifact@v3
      with:
        name: ai-code-review
        path: ai-code-review/
```

## Best Practices

1. **API Key Security**
   - Use environment variables for API keys
   - Never commit API keys to version control
   - Use secure storage (AWS Secrets Manager, etc.) for production

2. **Regular Reviews**
   - Run reviews after significant code changes
   - Integrate with CI/CD pipeline
   - Review output regularly and act on recommendations

3. **Configuration Management**
   - Customize review types based on project needs
   - Use consistent configuration across team
   - Version control the configuration file

4. **Cost Management**
   - Monitor API usage and costs
   - Use appropriate models for different review types
   - Consider caching for repeated reviews

## Troubleshooting

### Common Issues
1. **API Key Not Found**
   - Ensure `.env.local` file exists in project root
   - Check environment variable names are correct
   - Verify API key format and validity

2. **Model Not Available**
   - Check supported models with `ai-code-review --models`
   - Verify API key has access to the model
   - Try alternative models if one fails

3. **Large Codebase Issues**
   - Tool automatically handles large codebases with multi-pass reviews
   - Use `--force-single-pass` to override if needed
   - Consider reviewing specific directories instead of entire codebase

### Testing Setup
```bash
# Test API connection
ai-code-review --test-api

# Test with simple model call
ai-code-review test-model

# Debug mode for troubleshooting
ai-code-review --debug
```

## Deployment Experience

### Claude Multi-Agent PM Project
- **Project**: `/Users/masa/Projects/claude-multiagent-pm/`
- **Model Used**: OpenAI GPT-4o
- **Review Type**: Quick Fixes
- **Files Analyzed**: 123 files
- **Tokens Used**: 76,261 tokens
- **Cost**: $0.077172 USD
- **Duration**: ~25 seconds

### Key Findings
- Generated comprehensive B+ grade review
- Identified 5 actionable improvements
- Created structured tickets for high-priority issues
- Effective for large codebases with multi-pass analysis

## Files Created

1. **Configuration Files**
   - `.env.local` - Environment variables for API keys
   - `.ai-code-review.yaml` - Tool configuration

2. **Review Output**
   - `ai-code-review/quick-fixes-review-*.md` - Review results
   - `ai-code-review/TICKET-*.md` - Generated tickets

3. **Documentation**
   - `ai-code-review/SETUP-GUIDE.md` - This setup guide

## Next Steps

1. **Implement Recommendations**
   - Review generated tickets in `ai-code-review/` directory
   - Prioritize high-impact improvements
   - Track implementation progress

2. **Automate Reviews**
   - Set up CI/CD integration
   - Schedule regular reviews
   - Create team workflow for review responses

3. **Expand Usage**
   - Apply to other projects in the organization
   - Experiment with different review types
   - Customize for specific project needs

---
*Setup completed on 2025-07-08 for claude-multiagent-pm project*