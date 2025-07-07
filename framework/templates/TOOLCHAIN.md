# Toolchain Best Practices - {PROJECT_NAME}

This document outlines modern development toolchain best practices for 2025, incorporating the latest industry standards for code quality, security, and performance.

## 🛠️ CORE DEVELOPMENT STACK

### Language & Runtime
{LANGUAGE_RUNTIME_SPECIFICS}

### Package Management
{PACKAGE_MANAGER_SPECIFICS}

### Build & Bundling
{BUILD_BUNDLING_SPECIFICS}

## 🔍 CODE QUALITY TOOLS

### Linting & Formatting (2025 Standards)
**TypeScript/JavaScript Projects:**
```bash
# ESLint with TypeScript support
npm install -D @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install -D eslint-plugin-import eslint-plugin-react eslint-plugin-react-hooks

# Biome (2025 alternative - faster than ESLint)
npm install -D @biomejs/biome

# Prettier for formatting
npm install -D prettier @trivago/prettier-plugin-sort-imports
```

**Python Projects:**
```bash
# Ruff (2025 standard - replaces Black, isort, and most of Flake8)
pip install ruff

# MyPy for type checking
pip install mypy

# Pre-commit hooks
pip install pre-commit
```

### Configuration Examples
**ESLint + TypeScript (2025):**
```json
{
  "extends": [
    "@typescript-eslint/recommended",
    "@typescript-eslint/recommended-requiring-type-checking"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": 2024,
    "sourceType": "module",
    "project": "./tsconfig.json"
  },
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/strict-boolean-expressions": "error",
    "@typescript-eslint/prefer-nullish-coalescing": "error"
  }
}
```

**Ruff Configuration (pyproject.toml):**
```toml
[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E", "F", "W",  # pycodestyle, pyflakes
    "I",            # isort
    "N",            # pep8-naming
    "S",            # bandit security
    "B",            # flake8-bugbear
    "C4",           # flake8-comprehensions
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

## 🧪 TESTING FRAMEWORK (2025 Standards)

### Test Runners
**JavaScript/TypeScript:**
- **Vitest** (recommended for 2025) - faster than Jest, native ESM support
- **Jest** (established) - comprehensive testing framework
- **Playwright** - end-to-end testing

**Python:**
- **pytest** - standard for Python testing
- **pytest-cov** - coverage reporting
- **pytest-xdist** - parallel test execution

### Testing Configuration
**Vitest Configuration:**
```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    }
  }
})
```

**Pytest Configuration:**
```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80"
]
```

## 🔒 SECURITY & VULNERABILITY SCANNING

### Dependency Security (2025)
**JavaScript/TypeScript:**
```bash
# npm audit (built-in)
npm audit --audit-level=moderate

# Snyk for comprehensive scanning
npm install -g snyk
snyk test

# Socket.dev for supply chain security
npx socket npm ls
```

**Python:**
```bash
# Safety for known vulnerabilities
pip install safety
safety check

# Bandit for security issues in code
pip install bandit
bandit -r src/

# pip-audit (official Python tool)
pip install pip-audit
pip-audit
```

### Pre-commit Hooks (Security Focus)
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-private-key
      - id: check-merge-conflict

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        additional_dependencies: ['@typescript-eslint/parser', '@typescript-eslint/eslint-plugin']
```

## 🚀 CI/CD PIPELINE (2025 Best Practices)

### GitHub Actions Template
```yaml
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=moderate
      - run: npx snyk test
```

### Build Optimization (2025)
**Vite Configuration (Modern Bundling):**
```typescript
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    target: 'esnext',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['date-fns', 'lodash-es']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
})
```

## 📊 MONITORING & OBSERVABILITY

### Performance Monitoring
**Web Vitals Tracking:**
```typescript
// Core Web Vitals monitoring
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

getCLS(console.log)
getFID(console.log)
getFCP(console.log)
getLCP(console.log)
getTTFB(console.log)
```

**Build Performance Tracking:**
```bash
# Bundle analyzer
npm install -D webpack-bundle-analyzer
npm install -D rollup-plugin-visualizer

# Build time tracking
npm install -D speed-measure-webpack-plugin
```

## 🎯 PROJECT-SPECIFIC CONFIGURATIONS

{PROJECT_SPECIFIC_TOOLCHAIN}

## 📋 QUALITY GATES

### Automated Checks (Required)
- [ ] **Linting**: ESLint/Ruff passes with zero errors
- [ ] **Type Safety**: TypeScript/MyPy strict mode enabled
- [ ] **Testing**: Minimum 80% code coverage
- [ ] **Security**: Vulnerability scan passes
- [ ] **Performance**: Build time under 3 minutes
- [ ] **Bundle Size**: Production bundle under specified limits

### Manual Reviews (Required)
- [ ] **Architecture**: Design patterns consistent
- [ ] **Performance**: No regressions in key metrics
- [ ] **Security**: Security implications reviewed
- [ ] **UX**: User experience not degraded
- [ ] **Documentation**: Changes properly documented

## 🔄 TOOLCHAIN MAINTENANCE

### Regular Updates
- **Weekly**: Dependency security scans
- **Bi-weekly**: Minor dependency updates
- **Monthly**: Major dependency evaluation
- **Quarterly**: Toolchain modernization review

### Version Pinning Strategy
- **Lock Files**: Always commit lock files
- **Renovate Bot**: Automated dependency updates
- **Security Patches**: Immediate application
- **Breaking Changes**: Scheduled maintenance windows