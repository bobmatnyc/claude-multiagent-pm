# Deployment Guide

## Overview

This guide covers deployment strategies, release management, and best practices for deploying the Claude PM Framework to production environments. It includes both local deployments and package publication procedures.

## Deployment Architecture

### Package Distribution

```
┌────────────────────────────────────────────┐
│            Source Repository               │
│         (GitHub: main branch)              │
└────────────────┬───────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼─────┐        ┌─────▼─────┐
│   NPM     │        │   PyPI    │
│ Registry  │        │ Registry  │
└─────┬─────┘        └─────┬─────┘
      │                     │
      └──────────┬──────────┘
                 │
         ┌───────▼────────┐
         │     Users      │
         │  npm install   │
         └────────────────┘
```

### Deployment Components

1. **NPM Package**: Node.js CLI and orchestration layer
2. **Python Package**: Core services and agent execution (bundled)
3. **Framework Templates**: Deployment configurations
4. **Agent Definitions**: System and user agent files

## Local Deployment

### 1. Development Deployment

```bash
# Clone repository
git clone https://github.com/Bobjayafam/claude-multiagent-pm.git
cd claude-multiagent-pm

# Install dependencies
npm install
pip install -r requirements/dev.txt

# Link for local development
npm link

# Deploy to local project
cd /path/to/your/project
npm link @bobmatnyc/claude-multiagent-pm
claude-pm init
```

### 2. Production Deployment

```bash
# Install from npm registry
npm install -g @bobmatnyc/claude-multiagent-pm

# Initialize in project
cd /path/to/production/project
claude-pm init --production

# Verify deployment
claude-pm status
```

### 3. Docker Deployment

```dockerfile
# Dockerfile
FROM node:18-python3.10

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Claude PM Framework
RUN npm install -g @bobmatnyc/claude-multiagent-pm

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Initialize framework
RUN claude-pm init

# Set environment variables
ENV CLAUDE_PM_PRODUCTION=true

# Run application
CMD ["claude-pm"]
```

### 4. Kubernetes Deployment

```yaml
# claude-pm-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-pm-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: claude-pm
  template:
    metadata:
      labels:
        app: claude-pm
    spec:
      containers:
      - name: claude-pm
        image: claude-pm:latest
        env:
        - name: CLAUDE_PM_PRODUCTION
          value: "true"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic
        resources:
          limits:
            memory: "2Gi"
            cpu: "1"
          requests:
            memory: "512Mi"
            cpu: "250m"
        volumeMounts:
        - name: agent-config
          mountPath: /app/.claude-pm/agents
      volumes:
      - name: agent-config
        configMap:
          name: custom-agents
```

## Release Management

### 1. Version Strategy

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes
MINOR: New features (backwards compatible)
PATCH: Bug fixes
```

### 2. Release Workflow

```bash
# 1. Update version
npm version minor  # or major/patch

# 2. Update Python version
# Edit claude_pm/_version.py to match

# 3. Update changelog
# Edit CHANGELOG.md with release notes

# 4. Run release validation
npm run release:validate

# 5. Create git tag
git tag -a v0.9.3 -m "Release v0.9.3"

# 6. Push to repository
git push origin main --tags
```

### 3. Pre-Release Checklist

```python
# scripts/pre_release_checklist.py
import subprocess
import json
import sys

class PreReleaseChecker:
    """Validate release readiness."""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
    
    def run_all_checks(self) -> bool:
        """Run all pre-release checks."""
        checks = [
            self.check_version_sync,
            self.check_tests_passing,
            self.check_lint_clean,
            self.check_documentation,
            self.check_changelog,
            self.check_dependencies,
            self.check_security
        ]
        
        for check in checks:
            try:
                check()
                self.checks_passed.append(check.__name__)
            except Exception as e:
                self.checks_failed.append((check.__name__, str(e)))
        
        self._print_report()
        return len(self.checks_failed) == 0
    
    def check_version_sync(self):
        """Ensure versions are synchronized."""
        # Check package.json
        with open('package.json', 'r') as f:
            npm_version = json.load(f)['version']
        
        # Check Python version
        with open('claude_pm/_version.py', 'r') as f:
            py_version = f.read().split('"')[1]
        
        # Check VERSION file
        with open('VERSION', 'r') as f:
            file_version = f.read().strip()
        
        if not (npm_version == py_version == file_version):
            raise ValueError(
                f"Version mismatch: npm={npm_version}, "
                f"py={py_version}, file={file_version}"
            )
    
    def check_tests_passing(self):
        """Ensure all tests pass."""
        # Run Python tests
        result = subprocess.run(['pytest'], capture_output=True)
        if result.returncode != 0:
            raise RuntimeError("Python tests failed")
        
        # Run JavaScript tests
        result = subprocess.run(['npm', 'test'], capture_output=True)
        if result.returncode != 0:
            raise RuntimeError("JavaScript tests failed")
    
    def check_lint_clean(self):
        """Ensure code passes linting."""
        # Python linting
        result = subprocess.run(['flake8', 'claude_pm'], capture_output=True)
        if result.returncode != 0:
            raise RuntimeError("Python linting failed")
        
        # JavaScript linting
        result = subprocess.run(['npm', 'run', 'lint'], capture_output=True)
        if result.returncode != 0:
            raise RuntimeError("JavaScript linting failed")
    
    def check_documentation(self):
        """Ensure documentation is updated."""
        # Check for TODO items in docs
        result = subprocess.run(
            ['grep', '-r', 'TODO', 'docs/'],
            capture_output=True
        )
        if result.returncode == 0:
            raise ValueError("Found TODO items in documentation")
    
    def check_changelog(self):
        """Ensure changelog is updated."""
        with open('CHANGELOG.md', 'r') as f:
            content = f.read()
        
        # Check for unreleased section
        if '## [Unreleased]' in content and len(content.split('## [Unreleased]')[1].strip()) < 50:
            raise ValueError("Changelog unreleased section is empty")
    
    def check_dependencies(self):
        """Check for security vulnerabilities."""
        # NPM audit
        result = subprocess.run(
            ['npm', 'audit', '--audit-level=high'],
            capture_output=True
        )
        if result.returncode != 0:
            raise RuntimeError("NPM audit found high vulnerabilities")
    
    def check_security(self):
        """Run security checks."""
        # Check for hardcoded secrets
        result = subprocess.run(
            ['grep', '-r', '-E', '(api_key|secret|password)\\s*=\\s*["\']\\w+["\']', 'claude_pm'],
            capture_output=True
        )
        if result.returncode == 0:
            raise ValueError("Found potential hardcoded secrets")
    
    def _print_report(self):
        """Print check report."""
        print("\n=== Pre-Release Check Report ===\n")
        
        if self.checks_passed:
            print("✅ Passed Checks:")
            for check in self.checks_passed:
                print(f"  - {check}")
        
        if self.checks_failed:
            print("\n❌ Failed Checks:")
            for check, error in self.checks_failed:
                print(f"  - {check}: {error}")
        
        print(f"\nTotal: {len(self.checks_passed)} passed, {len(self.checks_failed)} failed")

if __name__ == '__main__':
    checker = PreReleaseChecker()
    if not checker.run_all_checks():
        sys.exit(1)
```

## Package Publication

### 1. NPM Publication

```bash
# Login to npm
npm login

# Publish package
npm publish

# Verify publication
npm view @bobmatnyc/claude-multiagent-pm
```

### 2. Automated Publication

```yaml
# .github/workflows/publish.yml
name: Publish Package

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        registry-url: 'https://registry.npmjs.org'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test
    
    - name: Publish to NPM
      run: npm publish
      env:
        NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### 3. Publication Validation

```python
# scripts/validate_publication.py
import requests
import json
import time

def validate_npm_publication(package_name: str, expected_version: str):
    """Validate NPM package publication."""
    
    # Wait for NPM to update
    time.sleep(30)
    
    # Check NPM registry
    response = requests.get(
        f'https://registry.npmjs.org/{package_name}'
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Package not found: {package_name}")
    
    data = response.json()
    latest_version = data['dist-tags']['latest']
    
    if latest_version != expected_version:
        raise ValueError(
            f"Version mismatch: expected {expected_version}, "
            f"got {latest_version}"
        )
    
    print(f"✅ Package published successfully: {package_name}@{latest_version}")
    
    # Validate package contents
    tarball_url = data['versions'][latest_version]['dist']['tarball']
    
    # Download and verify tarball
    response = requests.get(tarball_url)
    if response.status_code != 200:
        raise RuntimeError("Failed to download package tarball")
    
    print(f"✅ Package tarball accessible: {len(response.content)} bytes")

if __name__ == '__main__':
    validate_npm_publication('@bobmatnyc/claude-multiagent-pm', '0.9.3')
```

## Environment Configuration

### 1. Production Configuration

```bash
# Production environment variables
export CLAUDE_PM_PRODUCTION=true
export CLAUDE_PM_LOG_LEVEL=info
export CLAUDE_PM_CACHE_ENABLED=true
export CLAUDE_PM_MAX_CONCURRENT_AGENTS=20
export CLAUDE_PM_TIMEOUT=120

# API Keys (use secret management in production)
export OPENAI_API_KEY=$SECRET_OPENAI_KEY
export ANTHROPIC_API_KEY=$SECRET_ANTHROPIC_KEY
```

### 2. Configuration Management

```python
# claude_pm/config/production.py
import os
from typing import Dict, Any

class ProductionConfig:
    """Production environment configuration."""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get production configuration."""
        return {
            'debug': False,
            'log_level': os.getenv('CLAUDE_PM_LOG_LEVEL', 'info'),
            'cache': {
                'enabled': True,
                'ttl': 3600,
                'max_size': 5000
            },
            'agents': {
                'max_concurrent': int(os.getenv('CLAUDE_PM_MAX_CONCURRENT_AGENTS', '20')),
                'timeout': int(os.getenv('CLAUDE_PM_TIMEOUT', '120')),
                'sandbox': True
            },
            'security': {
                'validate_inputs': True,
                'enforce_permissions': True,
                'audit_logging': True
            },
            'performance': {
                'enable_profiling': False,
                'batch_operations': True,
                'connection_pooling': True
            }
        }
```

## Monitoring and Health Checks

### 1. Health Check Endpoint

```python
# claude_pm/services/health_endpoint.py
from fastapi import FastAPI, Response
from typing import Dict, Any
import psutil

app = FastAPI()

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """System health check endpoint."""
    
    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Check framework components
    framework_health = await check_framework_components()
    
    # Overall status
    is_healthy = (
        cpu_percent < 90 and
        memory.percent < 90 and
        disk.percent < 90 and
        framework_health['status'] == 'healthy'
    )
    
    return {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent
        },
        'framework': framework_health
    }

@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    metrics_data = generate_prometheus_metrics()
    return Response(content=metrics_data, media_type="text/plain")
```

### 2. Deployment Monitoring

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
  
  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"

volumes:
  prometheus_data:
  grafana_data:
```

## Rollback Procedures

### 1. Version Rollback

```bash
#!/bin/bash
# scripts/rollback.sh

PREVIOUS_VERSION=$1

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Usage: ./rollback.sh <previous_version>"
    exit 1
fi

echo "Rolling back to version $PREVIOUS_VERSION..."

# Revert NPM package
npm unpublish @bobmatnyc/claude-multiagent-pm@latest
npm publish --tag latest @bobmatnyc/claude-multiagent-pm@$PREVIOUS_VERSION

# Revert git tags
git tag -d v$CURRENT_VERSION
git push origin :refs/tags/v$CURRENT_VERSION

# Create rollback tag
git tag -a "rollback-from-$CURRENT_VERSION-to-$PREVIOUS_VERSION" -m "Rollback"
git push origin --tags

echo "Rollback complete"
```

### 2. Emergency Hotfix

```python
# scripts/emergency_hotfix.py
import subprocess
import sys

def apply_hotfix(fix_branch: str):
    """Apply emergency hotfix."""
    
    # Create hotfix branch
    subprocess.run(['git', 'checkout', '-b', f'hotfix/{fix_branch}'])
    
    # Apply fix
    # ... make necessary changes ...
    
    # Fast-track testing
    subprocess.run(['npm', 'run', 'test:critical'])
    
    # Version bump
    subprocess.run(['npm', 'version', 'patch'])
    
    # Publish
    subprocess.run(['npm', 'publish', '--tag', 'hotfix'])
    
    print(f"Hotfix published with tag 'hotfix'")
    print("Users can install with: npm install @bobmatnyc/claude-multiagent-pm@hotfix")

if __name__ == '__main__':
    apply_hotfix(sys.argv[1])
```

## Deployment Best Practices

### 1. Blue-Green Deployment

```python
# Blue-green deployment strategy
class BlueGreenDeployment:
    """Manage blue-green deployments."""
    
    def __init__(self, blue_env: str, green_env: str):
        self.blue_env = blue_env
        self.green_env = green_env
        self.active_env = self.blue_env
    
    def deploy_to_inactive(self, version: str):
        """Deploy to inactive environment."""
        inactive = self.green_env if self.active_env == self.blue_env else self.blue_env
        
        # Deploy new version
        self._deploy(inactive, version)
        
        # Run smoke tests
        if self._smoke_test(inactive):
            return inactive
        else:
            raise RuntimeError("Smoke tests failed")
    
    def switch_active(self):
        """Switch active environment."""
        self.active_env = self.green_env if self.active_env == self.blue_env else self.blue_env
        
        # Update load balancer
        self._update_load_balancer(self.active_env)
```

### 2. Canary Deployment

```python
# Canary deployment configuration
CANARY_CONFIG = {
    'initial_percentage': 5,
    'increment': 10,
    'interval_minutes': 30,
    'success_threshold': 0.99,
    'error_threshold': 0.01
}

def canary_rollout(new_version: str):
    """Gradual canary rollout."""
    percentage = CANARY_CONFIG['initial_percentage']
    
    while percentage <= 100:
        # Route traffic
        update_traffic_split(new_version, percentage)
        
        # Monitor metrics
        time.sleep(CANARY_CONFIG['interval_minutes'] * 60)
        
        metrics = get_deployment_metrics(new_version)
        
        if metrics['success_rate'] < CANARY_CONFIG['success_threshold']:
            # Rollback
            update_traffic_split(new_version, 0)
            raise RuntimeError("Canary deployment failed")
        
        # Increase traffic
        percentage += CANARY_CONFIG['increment']
    
    print(f"Canary deployment successful: {new_version}")
```

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version numbers synchronized
- [ ] Security scan completed
- [ ] Performance benchmarks run

### Deployment
- [ ] Backup current deployment
- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor metrics

### Post-Deployment
- [ ] Verify all services healthy
- [ ] Check error rates
- [ ] Monitor performance metrics
- [ ] Update status page
- [ ] Notify stakeholders
- [ ] Document any issues

---

*For emergency procedures, see the incident response documentation.*