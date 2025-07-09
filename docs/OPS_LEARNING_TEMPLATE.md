# Operational Learning Template

## Template Usage

This template should be used to capture operational learnings from all ops tasks, issues, and improvements in the Claude PM Framework. Each entry becomes part of the searchable knowledge base for future custom user agents.

**File Naming Convention**: `ops-learning-YYYY-MM-DD-HH-MM-SS-{category}-{brief-description}.md`

**Categories**: `issue`, `performance`, `configuration`, `deployment`, `recovery`, `monitoring`, `maintenance`

---

## Learning Entry

### Issue Summary
- **Date**: [ISO format: 2025-07-09T14:30:00Z]
- **Category**: [issue/performance/configuration/deployment/recovery/monitoring/maintenance]
- **Title**: [Brief descriptive title]
- **Severity**: [LOW/MEDIUM/HIGH/CRITICAL]
- **Duration**: [Time to resolve]
- **Impact**: [Description of system impact]

### Context
- **System State**: [Description of system state when issue occurred]
- **Symptoms**: [What was observed/reported]
- **Environment**: [Production/staging/development]
- **Related Services**: [List of affected services]
- **Trigger**: [What caused the issue]

### Root Cause Analysis
- **Primary Cause**: [Main cause of the issue]
- **Secondary Causes**: [Contributing factors]
- **Systemic Issues**: [Underlying system problems]
- **Human Factors**: [Process or procedural issues]

### Resolution Steps
1. [Step 1 with command/action]
2. [Step 2 with command/action]
3. [Step 3 with command/action]
4. [Continue as needed]

### Commands Used
```bash
# Include all commands used during resolution
command1 --option value
command2 --flag

# Include any diagnostic commands
diagnostic_command --verbose
```

### Code Changes
```python
# Include any code changes made
# Before:
old_code_snippet

# After:
new_code_snippet
```

### Configuration Changes
```json
// Include any configuration changes
// Before:
{
  "old_setting": "old_value"
}

// After:
{
  "new_setting": "new_value"
}
```

### Prevention Measures
- [Measure 1]: [Description and implementation]
- [Measure 2]: [Description and implementation]
- [Measure 3]: [Description and implementation]

### Learning Points
- [Key insight 1]
- [Key insight 2]
- [Key insight 3]
- [Process improvement]
- [Tool enhancement]

### Documentation Updates
- [Document 1]: [What was updated]
- [Document 2]: [What was updated]
- [New documentation]: [What was created]

### Monitoring Improvements
- [Metric 1]: [Added/modified monitoring]
- [Alert 1]: [Added/modified alerts]
- [Dashboard 1]: [Added/modified dashboards]

### Automation Opportunities
- [Opportunity 1]: [Description and potential implementation]
- [Opportunity 2]: [Description and potential implementation]

### Testing Improvements
- [Test 1]: [Added/modified tests]
- [Test 2]: [Added/modified tests]
- [Validation 1]: [Added/modified validations]

### Knowledge Base Updates
- [Update 1]: [What was added to knowledge base]
- [Update 2]: [What was added to knowledge base]
- [Pattern 1]: [New pattern identified]

### Future Considerations
- [Consideration 1]: [Long-term implications]
- [Consideration 2]: [Long-term implications]
- [Upgrade path]: [Future upgrade considerations]

### Related Issues
- [Issue 1]: [Link to related issue]
- [Issue 2]: [Link to related issue]
- [Pattern]: [Link to similar pattern]

### Metrics
- **Time to Detection**: [How long before issue was detected]
- **Time to Resolution**: [How long to resolve]
- **System Availability**: [Percentage uptime during incident]
- **Performance Impact**: [Quantified performance impact]

### Validation
- [Validation 1]: [How resolution was validated]
- [Validation 2]: [How resolution was validated]
- [Test results]: [Results of validation tests]

### Follow-up Actions
- [ ] [Action 1 with owner and deadline]
- [ ] [Action 2 with owner and deadline]
- [ ] [Action 3 with owner and deadline]

### Additional Notes
[Any additional context, observations, or information that doesn't fit above categories]

---

## Template Examples

### Example 1: Service Issue

```markdown
# Operational Learning Entry

## Learning Entry

### Issue Summary
- **Date**: 2025-07-09T14:30:00Z
- **Category**: issue
- **Title**: Memory Service Connection Pool Exhaustion
- **Severity**: HIGH
- **Duration**: 45 minutes
- **Impact**: Memory operations failing, context preparation degraded

### Context
- **System State**: High load period with multiple agent executions
- **Symptoms**: Connection timeouts, "Pool exhausted" errors
- **Environment**: Production
- **Related Services**: Memory Service, Multi-Agent Orchestrator
- **Trigger**: Concurrent agent executions exceeded pool capacity

### Root Cause Analysis
- **Primary Cause**: Connection pool size (10) insufficient for concurrent load
- **Secondary Causes**: No connection pooling monitoring, no backpressure
- **Systemic Issues**: No load testing of connection pool
- **Human Factors**: Default configuration not reviewed for production load

### Resolution Steps
1. Identified pool exhaustion in logs: `grep "Pool exhausted" logs/memory_service.log`
2. Increased pool size from 10 to 50 connections
3. Added connection pool monitoring
4. Implemented backpressure mechanism
5. Tested with load simulation

### Commands Used
```bash
# Check current pool usage
python3 -c "from claude_pm.services.memory_service import get_memory_service; print(get_memory_service().client._connection_pool)"

# Update pool configuration
python3 -c "
from claude_pm.services.memory_service import ClaudePMConfig
config = ClaudePMConfig(connection_pool_size=50)
print('Pool size updated to:', config.connection_pool_size)
"

# Test with load
python3 scripts/test_connection_pool_load.py --concurrent=20
```

### Configuration Changes
```python
# Before:
connection_pool_size = 10

# After:
connection_pool_size = 50
```

### Prevention Measures
- **Load Testing**: Implement regular load testing of connection pool
- **Monitoring**: Added connection pool usage metrics
- **Alerting**: Alert when pool usage exceeds 80%
- **Documentation**: Updated capacity planning guide

### Learning Points
- Default connection pool sizes need production validation
- Connection pool monitoring is essential for high-load systems
- Backpressure mechanisms prevent cascade failures
- Load testing should include all service components

### Monitoring Improvements
- **Pool Usage**: Added connection pool utilization metrics
- **Pool Exhaustion Alert**: Alert when pool usage > 80%
- **Connection Time**: Monitor connection establishment time

### Follow-up Actions
- [ ] Implement automatic pool scaling based on load
- [ ] Add connection pool health checks
- [ ] Update deployment documentation with pool sizing guide
```

### Example 2: Performance Optimization

```markdown
# Operational Learning Entry

## Learning Entry

### Issue Summary
- **Date**: 2025-07-09T16:15:00Z
- **Category**: performance
- **Title**: Memory Context Preparation Performance Optimization
- **Severity**: MEDIUM
- **Duration**: 2 hours
- **Impact**: Slow agent context preparation affecting response times

### Context
- **System State**: Normal operation with acceptable but slow performance
- **Symptoms**: Context preparation taking 2-3 seconds per agent
- **Environment**: Production
- **Related Services**: Memory Service, Multi-Agent Orchestrator
- **Trigger**: Performance monitoring identified bottleneck

### Root Cause Analysis
- **Primary Cause**: N+1 query pattern in memory retrieval
- **Secondary Causes**: No result caching, inefficient query structure
- **Systemic Issues**: No performance benchmarking in development
- **Human Factors**: Performance testing not included in development workflow

### Resolution Steps
1. Profiled memory context preparation: `python3 -m cProfile -s cumulative context_prep.py`
2. Identified N+1 query pattern in memory retrieval
3. Implemented batch query mechanism
4. Added result caching with TTL
5. Optimized query structure

### Performance Results
- **Before**: 2.5 seconds average context preparation
- **After**: 0.3 seconds average context preparation
- **Improvement**: 88% reduction in context preparation time

### Code Changes
```python
# Before: N+1 query pattern
for category in categories:
    memories = await self.memory.retrieve_memories(category, query)
    context[category] = memories

# After: Batch query with caching
batch_queries = [(category, query) for category in categories]
batch_results = await self.memory.batch_retrieve_memories(batch_queries)
for category, memories in batch_results.items():
    context[category] = memories
```

### Prevention Measures
- **Performance Testing**: Added performance benchmarks to CI/CD
- **Profiling**: Regular profiling of critical paths
- **Monitoring**: Added performance metrics and alerts
- **Code Review**: Performance review checklist

### Learning Points
- N+1 query patterns are common performance bottlenecks
- Batch operations significantly improve performance
- Caching with appropriate TTL reduces load
- Performance monitoring should be continuous, not reactive

### Monitoring Improvements
- **Context Prep Time**: Monitor context preparation duration
- **Query Performance**: Track memory query response times
- **Cache Hit Rate**: Monitor cache effectiveness

### Follow-up Actions
- [ ] Implement similar batch operations in other services
- [ ] Add automated performance regression tests
- [ ] Update development guidelines with performance best practices
```

### Example 3: Configuration Management

```markdown
# Operational Learning Entry

## Learning Entry

### Issue Summary
- **Date**: 2025-07-09T10:45:00Z
- **Category**: configuration
- **Title**: Health Monitoring Configuration Validation
- **Severity**: LOW
- **Duration**: 30 minutes
- **Impact**: Invalid configuration causing health check failures

### Context
- **System State**: Health monitoring reporting inconsistent results
- **Symptoms**: Some health checks failing intermittently
- **Environment**: Development
- **Related Services**: Health Monitor
- **Trigger**: Configuration update introduced invalid values

### Root Cause Analysis
- **Primary Cause**: JSON configuration contained invalid threshold values
- **Secondary Causes**: No configuration validation on update
- **Systemic Issues**: Manual configuration management
- **Human Factors**: No configuration review process

### Resolution Steps
1. Validated configuration: `python3 -m json.tool config/health_monitoring_config.json`
2. Identified invalid threshold values (negative numbers)
3. Corrected threshold values
4. Implemented configuration validation
5. Added configuration schema

### Configuration Changes
```json
// Before:
{
  "alert_thresholds": {
    "critical_issues": -1,
    "broken_links": 5
  }
}

// After:
{
  "alert_thresholds": {
    "critical_issues": 1,
    "broken_links": 5
  }
}
```

### Prevention Measures
- **Schema Validation**: Implemented JSON schema validation
- **Configuration Tests**: Added configuration validation tests
- **Automated Validation**: Configuration validation in CI/CD
- **Documentation**: Updated configuration documentation

### Learning Points
- Configuration validation prevents operational issues
- JSON schema validation catches common errors
- Automated configuration testing is essential
- Configuration changes should be reviewed like code

### Automation Opportunities
- **Configuration Validation**: Automated validation on config changes
- **Configuration Testing**: Automated testing of configuration values
- **Configuration Deployment**: Automated configuration deployment

### Follow-up Actions
- [ ] Implement configuration validation for all services
- [ ] Add configuration change tracking
- [ ] Create configuration management documentation
```

---

## Knowledge Base Integration

### Pattern Recognition
This learning entry contributes to the following patterns:
- **Service Recovery**: Steps for similar service issues
- **Performance Optimization**: Approaches for similar bottlenecks
- **Configuration Management**: Best practices for config changes

### Searchable Tags
Add relevant tags for knowledge base searching:
- `memory-service`, `connection-pool`, `performance`, `high-load`
- `context-preparation`, `n-plus-one`, `batch-queries`, `caching`
- `configuration`, `validation`, `json-schema`, `health-monitoring`

### Future Agent Context
This information will be used to provide context for future custom user agents:
- **Issue Recognition**: Identify similar issues based on symptoms
- **Solution Patterns**: Apply similar solutions to related problems
- **Prevention Strategies**: Implement similar prevention measures
- **Optimization Approaches**: Use similar optimization techniques

### Knowledge Base Location
Store completed learning entries in:
```
docs/ops-knowledge/
├── issues/
│   ├── memory-service/
│   ├── health-monitoring/
│   └── ai-trackdown/
├── performance/
│   ├── optimizations/
│   └── benchmarks/
├── configurations/
│   ├── changes/
│   └── validations/
└── procedures/
    ├── deployments/
    └── recovery/
```

### Integration with Framework
Learning entries are integrated into the framework through:
- **Memory Service**: Stored as operational memories
- **Agent Context**: Provided to agents for similar tasks
- **Monitoring**: Used to improve monitoring and alerting
- **Documentation**: Automatically update relevant documentation

---

## Template Completion Checklist

Before saving a learning entry, ensure:
- [ ] All required fields are completed
- [ ] Commands and code are accurate and tested
- [ ] Prevention measures are actionable
- [ ] Learning points are clear and specific
- [ ] Follow-up actions have owners and deadlines
- [ ] Entry is properly categorized and tagged
- [ ] Related issues are linked
- [ ] Metrics are quantified where possible

## Version History

- **v1.0**: Initial template creation
- **v1.1**: Added performance optimization example
- **v1.2**: Enhanced knowledge base integration
- **v1.3**: Added pattern recognition and tagging

This template ensures consistent, comprehensive capture of operational knowledge that can be effectively used by future custom user agents to handle similar situations with full context and historical insight.