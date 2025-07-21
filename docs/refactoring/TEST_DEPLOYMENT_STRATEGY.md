# EP-0043 Test Deployment Strategy

## Overview

This document outlines a comprehensive test deployment strategy for the EP-0043 refactoring changes. The strategy prioritizes safety, isolation, and rollback capabilities while ensuring thorough validation before production deployment.

**Created**: 2025-07-19  
**Epic**: EP-0043 - Code Maintainability - Reduce File Sizes to 1000 Lines  
**Risk Level**: High (significant architectural changes)  

## Key Refactoring Changes to Test

1. **parent_directory_manager.py** → 6 module structure
2. **agent_registry.py** + **agent_registry_sync.py** → Wrapper pattern
3. **backwards_compatible_orchestrator.py** → 8 module structure
4. All using backward compatibility wrappers

## Test Deployment Architecture

### 1. Isolated Test Environment Setup

```bash
# Create isolated test environment
mkdir -p ~/test-deployments/claude-pm-refactor-test
cd ~/test-deployments/claude-pm-refactor-test

# Clone fresh copy of the repository
git clone https://github.com/[repo]/claude-multiagent-pm.git .
git checkout feature/EP-0043-file-size-refactoring

# Create virtual environment for isolation
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
```

### 2. Parallel Testing Strategy

**Production Environment**: Keep running normally  
**Test Environment**: Isolated testing of refactored code  
**Staging Environment**: Integration testing before production  

```
Production (main branch)         Test Environment              Staging
    ├── Running normally   →   ├── Refactored code      →   ├── Pre-production
    ├── No changes              ├── Full test suite          ├── User acceptance
    └── Fallback option         └── Performance tests        └── Final validation
```

## Phased Deployment Process

### Phase 1: Local Development Testing (Days 1-3)

**Objective**: Verify basic functionality in isolated environment

1. **Unit Test Validation**
   ```bash
   # Run all unit tests for refactored modules
   pytest tests/unit/services/test_parent_directory_manager.py -v
   pytest tests/unit/core/test_agent_registry.py -v
   pytest tests/unit/test_backwards_compatible_orchestrator.py -v
   ```

2. **Integration Test Suite**
   ```bash
   # Run integration tests
   pytest tests/integration/ -v --cov=claude_pm
   ```

3. **Backward Compatibility Tests**
   ```bash
   # Test old import paths still work
   python -c "from claude_pm.services.parent_directory_manager import ParentDirectoryManager"
   python -c "from claude_pm.core.agent_registry import AgentRegistry"
   python -c "from claude_pm.orchestration import BackwardsCompatibleOrchestrator"
   ```

### Phase 2: Docker Container Testing (Days 4-6)

**Objective**: Test in clean, reproducible environment

1. **Create Test Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install -e .
   RUN pip install pytest pytest-cov
   CMD ["pytest", "tests/", "-v"]
   ```

2. **Build and Test**
   ```bash
   docker build -t claude-pm-refactor-test .
   docker run --rm claude-pm-refactor-test
   ```

3. **Performance Benchmarking**
   ```bash
   # Compare with production baseline
   docker run --rm claude-pm-refactor-test python scripts/benchmark_performance.py
   ```

### Phase 3: Staging Environment Testing (Days 7-10)

**Objective**: Test with real-world usage patterns

1. **Deploy to Staging**
   ```bash
   # Create staging branch
   git checkout -b staging/EP-0043-test
   git merge feature/EP-0043-file-size-refactoring
   
   # Deploy to staging server
   ssh staging-server
   cd /opt/claude-pm-staging
   git pull
   git checkout staging/EP-0043-test
   ```

2. **User Acceptance Testing**
   - Run through all major workflows
   - Test with production-like data
   - Monitor for memory leaks or performance issues

3. **Load Testing**
   ```bash
   # Simulate concurrent usage
   python scripts/load_test_refactored_modules.py --concurrent-users 50
   ```

### Phase 4: Canary Deployment (Days 11-13)

**Objective**: Gradual rollout with monitoring

1. **Feature Flag Implementation**
   ```python
   # In claude_pm/config.py
   FEATURE_FLAGS = {
       'use_refactored_parent_directory': os.getenv('USE_REFACTORED_PDM', 'false') == 'true',
       'use_refactored_agent_registry': os.getenv('USE_REFACTORED_AR', 'false') == 'true',
       'use_refactored_orchestrator': os.getenv('USE_REFACTORED_ORCH', 'false') == 'true'
   }
   ```

2. **Gradual Rollout**
   ```bash
   # 10% of users
   export USE_REFACTORED_PDM=true
   # Monitor for 24 hours
   
   # 50% of users
   export USE_REFACTORED_AR=true
   # Monitor for 24 hours
   
   # 100% of users
   export USE_REFACTORED_ORCH=true
   ```

### Phase 5: Production Deployment (Day 14)

**Objective**: Full production deployment with rollback ready

1. **Pre-deployment Checklist**
   - [ ] All tests passing
   - [ ] Performance metrics acceptable
   - [ ] No memory leaks detected
   - [ ] Staging environment stable for 48 hours
   - [ ] Rollback procedure tested
   - [ ] Team notification sent

2. **Deployment Commands**
   ```bash
   # Tag current production state
   git tag pre-EP-0043-deployment
   git push origin pre-EP-0043-deployment
   
   # Merge to main
   git checkout main
   git merge feature/EP-0043-file-size-refactoring
   git push origin main
   ```

## Testing Checklist

### Functional Testing

- [ ] **Core Functionality**
  - [ ] Parent directory manager operations
  - [ ] Agent registry discovery and loading
  - [ ] Orchestrator task delegation
  - [ ] All CLI commands working

- [ ] **Backward Compatibility**
  - [ ] Old import paths work
  - [ ] Existing API contracts maintained
  - [ ] No breaking changes in public methods
  - [ ] Deprecation warnings appropriate

- [ ] **Integration Points**
  - [ ] Database connections stable
  - [ ] File system operations correct
  - [ ] Network calls functioning
  - [ ] External API integrations working

### Performance Testing

- [ ] **Benchmarks**
  - [ ] Module import time ≤ 105% of baseline
  - [ ] Memory usage ≤ 100% of baseline
  - [ ] CPU usage comparable
  - [ ] No new performance bottlenecks

- [ ] **Load Testing**
  - [ ] Handles expected concurrent users
  - [ ] No memory leaks under load
  - [ ] Response times acceptable
  - [ ] Resource cleanup working

### Security Testing

- [ ] **Vulnerability Scanning**
  - [ ] No new security warnings
  - [ ] Dependencies up to date
  - [ ] File permissions correct
  - [ ] No exposed sensitive data

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

```bash
# If critical issues found immediately
git revert HEAD
git push origin main

# Notify team
echo "CRITICAL: Rollback initiated for EP-0043" | slack-notify
```

### Standard Rollback (< 30 minutes)

```bash
# Revert to pre-deployment tag
git checkout main
git reset --hard pre-EP-0043-deployment
git push --force-with-lease origin main

# Restart services
systemctl restart claude-pm

# Verify rollback
claude-pm --version
python -c "import claude_pm; print(claude_pm.__version__)"
```

### Emergency Recovery (< 1 hour)

```bash
# If git rollback fails, use backup
cd /opt/claude-pm
tar -xzf /backups/claude-pm-pre-EP0043.tar.gz

# Restore database if needed
psql claude_pm < /backups/claude-pm-db-pre-EP0043.sql

# Restart all services
systemctl restart claude-pm
systemctl restart postgresql
```

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Application Health**
   - Error rate (should remain < 0.1%)
   - Response time (p95 < 500ms)
   - Memory usage (stable, no growth)
   - CPU usage (< 80% sustained)

2. **Functional Metrics**
   - Successful task completions
   - Agent loading success rate
   - File operation success rate
   - API call success rate

3. **User Impact Metrics**
   - Active user sessions
   - Feature usage patterns
   - Error reports from users
   - Performance complaints

### Alert Thresholds

```yaml
alerts:
  - name: error_rate_high
    condition: error_rate > 1%
    duration: 5m
    action: notify_oncall
    
  - name: memory_leak_detected
    condition: memory_growth > 10% per hour
    duration: 30m
    action: initiate_rollback
    
  - name: performance_degradation
    condition: p95_response_time > 1000ms
    duration: 10m
    action: investigate_immediately
```

## Communication Plan

### Pre-Deployment

1. **Team Notification** (Day -2)
   - Deployment schedule
   - Expected impacts
   - Rollback procedures

2. **User Communication** (Day -1)
   - Maintenance window
   - Feature improvements
   - Support contacts

### During Deployment

1. **Status Updates**
   - Every 30 minutes during deployment
   - Immediate notification of issues
   - Clear go/no-go decisions

### Post-Deployment

1. **Success Notification**
   - Deployment complete
   - Metrics summary
   - Next steps

2. **Incident Report** (if rollback needed)
   - Root cause analysis
   - Lessons learned
   - Prevention measures

## Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| Import errors | Medium | High | Comprehensive import testing |
| Performance regression | Low | Medium | Benchmark testing |
| Memory leaks | Low | High | Load testing with monitoring |
| API contract breaks | Low | High | Contract testing suite |
| Data corruption | Very Low | Critical | Database backups |

## Success Criteria

The deployment is considered successful when:

1. **All tests pass** in production environment
2. **No increase** in error rates after 24 hours
3. **Performance metrics** remain within acceptable bounds
4. **No rollback** required within 48 hours
5. **User feedback** is neutral or positive

## Lessons Learned Template

After deployment, document:

1. What went well
2. What could be improved
3. Unexpected issues encountered
4. Time estimates vs actual
5. Recommendations for future refactoring

---

**Document Version**: 1.0  
**Last Updated**: 2025-07-19  
**Next Review**: Post-deployment