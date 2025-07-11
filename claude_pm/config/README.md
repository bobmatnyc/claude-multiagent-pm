# Memory Trigger Configuration & Policy System

Comprehensive configuration and policy management system for the Claude PM Framework's memory trigger system. This system provides fine-grained control over memory behavior, policies, and operational parameters across different environments.

## Overview

The memory trigger configuration system consists of:

- **Core Configuration Classes**: Type-safe configuration management with validation
- **Policy Engine**: Rule-based memory trigger policies with conditional logic
- **Environment Management**: Environment-specific configurations (dev/test/staging/prod)
- **CLI Tools**: Command-line interface for configuration management
- **Validation System**: Schema and runtime validation with comprehensive error reporting
- **Hot Reloading**: Dynamic configuration updates without service restart

## Quick Start

### Basic Configuration

```python
from claude_pm.config.memory_trigger_config import (
    MemoryTriggerConfig, 
    MemoryTriggerConfigManager,
    Environment
)

# Create configuration manager
config_manager = MemoryTriggerConfigManager()

# Load configuration from file
config_manager.load_config_from_file('config/development.yaml')

# Get current configuration
config = config_manager.get_config()

# Validate configuration
errors = config.validate()
if errors:
    print(f"Configuration errors: {errors}")
```

### Policy Engine Usage

```python
from claude_pm.config.policy_engine_config import (
    PolicyEngine,
    PolicyRule,
    PolicyCondition,
    PolicyAction,
    PolicyConditionType,
    PolicyActionType
)

# Create policy engine
engine = PolicyEngine()

# Create a simple policy rule
rule = PolicyRule(
    name="error_memory_trigger",
    description="Create memory for error events",
    conditions=[
        PolicyCondition(
            type=PolicyConditionType.EQUALS,
            field="event_type",
            value="error"
        )
    ],
    actions=[
        PolicyAction(
            type=PolicyActionType.CREATE_MEMORY,
            parameters={
                "content": "Error event occurred",
                "tags": ["error", "incident"]
            }
        )
    ]
)

# Add rule to engine
engine.add_rule(rule)

# Execute rules against context
context = {"event_type": "error", "message": "Database connection failed"}
results = engine.execute_rules(context)
```

### CLI Usage

```bash
# Validate configuration
python -m claude_pm.cli.memory_config_cli validate config.yaml

# Generate configuration template
python -m claude_pm.cli.memory_config_cli generate --env production --output prod-config.yaml

# Deploy configuration
python -m claude_pm.cli.memory_config_cli deploy config.yaml --env production

# Manage policies
python -m claude_pm.cli.memory_config_cli policy list
python -m claude_pm.cli.memory_config_cli policy add error-policies.yaml

# Show statistics
python -m claude_pm.cli.memory_config_cli stats --config config.yaml
```

## Configuration Structure

### Main Configuration File

```yaml
# Environment and basic settings
environment: "production"
debug_mode: false
config_version: "1.0"
global_enabled: true
max_memory_operations_per_second: 500

# Performance configuration
performance:
  create_timeout: 5.0
  recall_timeout: 3.0
  batch_size: 100
  max_concurrent_operations: 20
  cache_enabled: true
  cache_ttl_seconds: 300

# Backend configuration
backend:
  backend_type: "mem0"
  connection_timeout: 5.0
  pool_enabled: true
  pool_size: 20
  encryption_enabled: true

# Lifecycle policies
lifecycle:
  default_retention_days: 180
  auto_cleanup_enabled: true
  archival_enabled: true

# Monitoring configuration
monitoring:
  metrics_enabled: true
  log_level: "INFO"
  alerting_enabled: true

# Feature toggles
features:
  workflow_triggers: true
  agent_triggers: true
  pattern_detection: true
  auto_recall: true

# Trigger policies
trigger_policies:
  production_workflow:
    enabled: true
    trigger_type: "workflow"
    success_threshold: 0.85
    pattern_detection_enabled: true
```

### Policy Configuration

```yaml
# Policy rules configuration
rules:
  error_handler:
    name: "error_handler"
    description: "Handle error events with memory creation"
    enabled: true
    priority: 100
    scope: "global"
    
    conditions:
      - type: "equals"
        field: "event_type"
        value: "error"
    
    condition_operator: "AND"
    
    actions:
      - type: "create_memory"
        priority: 1
        parameters:
          content: "Error event: ${error_message}"
          tags: ["error", "incident"]
          metadata:
            timestamp: "${timestamp}"
            severity: "${severity}"
      
      - type: "trigger_alert"
        priority: 2
        parameters:
          alert_type: "error"
          message: "Memory created for error event"
    
    max_executions: null
    cooldown_period: 60
```

## Environment-Specific Configurations

The system supports four pre-configured environments:

### Development (`environments/development.yaml`)

Optimized for development and debugging:
- Verbose logging (DEBUG level)
- Longer timeouts for debugging
- Smaller batch sizes
- Local backend
- Disabled caching for fresh results
- Lower quality thresholds for testing

### Testing (`environments/testing.yaml`)

Optimized for automated testing:
- Minimal logging (WARNING level)
- Fast timeouts for quick tests
- Local backend with cleanup
- Short retention periods
- Strict validation enabled

### Staging (`environments/staging.yaml`)

Production-like configuration for pre-production testing:
- Balanced logging (INFO level)
- mem0 backend with staging credentials
- Moderate retention periods
- Alerting enabled
- Archival testing

### Production (`environments/production.yaml`)

Optimized for performance, reliability, and scale:
- Minimal logging (INFO level)
- Tight timeouts for SLAs
- Large batch sizes and high concurrency
- mem0 backend with encryption
- Long retention periods
- Comprehensive monitoring and alerting

## Configuration Classes

### MemoryTriggerConfig

Main configuration class with nested components:

```python
@dataclass
class MemoryTriggerConfig:
    environment: Environment
    debug_mode: bool
    global_enabled: bool
    performance: PerformanceConfig
    lifecycle: LifecyclePolicyConfig
    monitoring: MonitoringConfig
    backend: BackendConfig
    trigger_policies: Dict[str, TriggerPolicyConfig]
    features: Dict[str, bool]
```

### PerformanceConfig

Performance tuning parameters:

```python
@dataclass
class PerformanceConfig:
    create_timeout: float
    recall_timeout: float
    batch_size: int
    max_concurrent_operations: int
    cache_enabled: bool
    cache_ttl_seconds: int
    min_memory_quality_score: float
    background_processing_enabled: bool
```

### TriggerPolicyConfig

Trigger-specific policy configuration:

```python
@dataclass
class TriggerPolicyConfig:
    enabled: bool
    trigger_type: MemoryTriggerType
    success_threshold: float
    failure_threshold: float
    pattern_detection_enabled: bool
    require_quality_validation: bool
    max_triggers_per_minute: int
```

### BackendConfig

Memory backend configuration:

```python
@dataclass
class BackendConfig:
    backend_type: MemoryBackend
    connection_timeout: float
    pool_enabled: bool
    pool_size: int
    encryption_enabled: bool
    failover_enabled: bool
```

## Policy Engine

### Policy Rules

Policy rules consist of:

- **Conditions**: When the rule should trigger
- **Actions**: What to do when conditions are met
- **Metadata**: Priority, scope, execution limits

### Condition Types

- `always` / `never`: Static conditions
- `equals` / `not_equals`: Value comparison
- `contains` / `not_contains`: String/list containment
- `matches_regex`: Regular expression matching
- `greater_than` / `less_than` / `between`: Numeric comparison
- `in_list` / `not_in_list`: List membership
- `time_range`: Time-based conditions
- `rate_limit`: Rate limiting conditions
- `probability`: Probabilistic conditions
- `composite_and` / `composite_or`: Logical combinations

### Action Types

- `create_memory`: Create new memory
- `recall_memory`: Retrieve existing memories
- `update_memory`: Modify existing memory
- `delete_memory`: Remove memory
- `set_quality_score`: Set memory quality
- `add_tag` / `remove_tag`: Tag management
- `trigger_alert`: Send alerts
- `log_event`: Log events
- `execute_webhook`: HTTP webhooks
- `chain_policy`: Chain to other policies

### Advanced Policy Examples

#### Complex Condition Logic

```yaml
rules:
  complex_error_handler:
    conditions:
      - type: "composite_and"
        sub_conditions:
          - type: "equals"
            field: "event_type"
            value: "error"
          - type: "composite_or"
            sub_conditions:
              - type: "contains"
                field: "error_message"
                value: "database"
              - type: "contains"
                field: "error_message"
                value: "connection"
          - type: "rate_limit"
            field: "user_id"
            rate_limit: 5
            time_window: 300
```

#### Conditional Actions

```yaml
actions:
  - type: "create_memory"
    condition:
      type: "greater_than"
      field: "severity"
      value: 3
    parameters:
      content: "High severity error"
  
  - type: "trigger_alert"
    condition:
      type: "equals"
      field: "environment"
      value: "production"
    parameters:
      alert_type: "critical"
```

## CLI Reference

### Command Overview

- `validate`: Validate configuration files
- `generate`: Generate configuration templates
- `deploy`: Deploy configurations to environments
- `policy`: Manage policy rules
- `stats`: Show configuration statistics
- `monitor`: Monitor configuration health
- `backup` / `restore`: Backup and restore configurations

### Validation Commands

```bash
# Basic validation
memory-config validate config.yaml

# Strict validation
memory-config validate config.yaml --strict

# Validate with custom schema
memory-config validate config.yaml --schema custom-schema.yaml
```

### Generation Commands

```bash
# Generate development configuration
memory-config generate --env development --output dev-config.yaml

# Generate minimal configuration
memory-config generate --env production --minimal --output minimal-config.yaml
```

### Deployment Commands

```bash
# Deploy to production
memory-config deploy config.yaml --env production

# Dry run deployment
memory-config deploy config.yaml --env production --dry-run

# Deploy with backup
memory-config deploy config.yaml --env production --backup
```

### Policy Management

```bash
# List all policies
memory-config policy list

# List enabled policies only
memory-config policy list --enabled-only

# Filter by scope
memory-config policy list --scope agent

# Add policy from file
memory-config policy add error-policies.yaml --validate

# Remove policy
memory-config policy remove error_handler --force

# Test policies
memory-config policy test --context test-context.json --output results.json
```

### Monitoring Commands

```bash
# Show statistics
memory-config stats --format json

# Monitor health
memory-config monitor --interval 30 --alerts

# Create backup
memory-config backup --output backup.yaml --include-policies

# Restore from backup
memory-config restore backup.yaml --dry-run
```

## Validation System

### Schema Validation

Validates configuration against YAML schema:

```python
from claude_pm.config.validation import ConfigurationSchemaValidator

validator = ConfigurationSchemaValidator()
result = validator.validate_schema(config_dict)

if not result.valid:
    for error in result.errors:
        print(f"Schema error: {error}")
```

### Runtime Validation

Validates business logic and consistency:

```python
from claude_pm.config.validation import RuntimeConfigurationValidator

validator = RuntimeConfigurationValidator()
result = validator.validate_runtime(config)

print(f"Performance score: {result.performance_score}")
for warning in result.warnings:
    print(f"Warning: {warning}")
```

### Comprehensive Validation

Combines all validation types:

```python
from claude_pm.config.validation import ComprehensiveValidator

validator = ComprehensiveValidator()
result = validator.validate_configuration(config)

print(f"Valid: {result.valid}")
print(f"Schema valid: {result.schema_valid}")
print(f"Runtime valid: {result.runtime_valid}")
print(f"Performance score: {result.performance_score}")

for issue in result.issues:
    print(issue)  # Formatted with emoji and suggestions
```

### Validation Issues

The validation system provides detailed feedback:

- **Severity Levels**: Error, Warning, Info
- **Path Information**: Exact location of issues
- **Error Codes**: Categorized error types
- **Suggestions**: Actionable recommendations
- **Performance Scoring**: Overall configuration quality

## Hot Reloading

Configuration hot reloading allows dynamic updates:

```python
# Enable hot reloading
config_manager = MemoryTriggerConfigManager('config.yaml')
config = config_manager.get_config()
config.auto_reload = True

# Configuration automatically reloads when file changes
# No service restart required
```

### File System Watcher

The system monitors configuration files for changes and automatically reloads:

- **Cooldown Period**: Prevents rapid reloads
- **Validation**: Ensures new configuration is valid before applying
- **Error Handling**: Graceful fallback if reload fails
- **Logging**: Comprehensive reload event logging

## Environment Variables

Override configuration with environment variables:

```bash
# Performance settings
export MEMORY_CREATE_TIMEOUT=10.0
export MEMORY_BATCH_SIZE=50
export MEMORY_MAX_CONCURRENT=5

# Backend settings
export MEMORY_BACKEND_TYPE=local
export MEMORY_CONNECTION_TIMEOUT=15.0

# Feature toggles
export MEMORY_TRIGGERS_ENABLED=true
export MEMORY_DEBUG_MODE=false

# Environment
export MEMORY_ENVIRONMENT=production
```

## Integration Examples

### Framework Integration

```python
from claude_pm.config import (
    initialize_config,
    get_config,
    get_config_manager
)

# Initialize configuration system
config_manager = initialize_config('config/production.yaml')

# Get configuration in your services
config = get_config()

# Use configuration values
if config.features['workflow_triggers']:
    # Enable workflow triggers
    pass

# Access specific components
backend_type = config.backend.backend_type
performance_settings = config.performance
```

### Service Integration

```python
class MemoryTriggerService:
    def __init__(self):
        self.config = get_config()
        self.policy_engine = get_policy_engine()
    
    def process_trigger(self, context):
        # Apply rate limiting from config
        if not self._check_rate_limit():
            return
        
        # Execute policies
        results = self.policy_engine.execute_rules(context)
        
        # Process results based on configuration
        for result in results:
            self._handle_policy_result(result)
```

### Testing Integration

```python
# Override configuration for tests
import os
os.environ['MEMORY_ENVIRONMENT'] = 'testing'
os.environ['MEMORY_BACKEND_TYPE'] = 'local'

# Use test-specific configuration
config_manager = MemoryTriggerConfigManager('config/testing.yaml')
config = config_manager.get_config()

# Validate test configuration
from claude_pm.config.validation import ComprehensiveValidator
validator = ComprehensiveValidator()
result = validator.validate_configuration(config)
assert result.valid, f"Test configuration invalid: {result.errors}"
```

## Best Practices

### Configuration Management

1. **Environment Separation**: Use separate configurations for each environment
2. **Version Control**: Track configuration changes in version control
3. **Validation**: Always validate configurations before deployment
4. **Backup**: Regular backups of production configurations
5. **Documentation**: Document configuration changes and rationale

### Policy Design

1. **Specific Conditions**: Use specific, testable conditions
2. **Rate Limiting**: Implement appropriate rate limits
3. **Error Handling**: Handle policy execution failures gracefully
4. **Testing**: Test policies with realistic scenarios
5. **Monitoring**: Monitor policy execution and performance

### Performance Optimization

1. **Caching**: Enable caching for frequently accessed data
2. **Batching**: Use appropriate batch sizes for your workload
3. **Concurrency**: Balance concurrency with resource limits
4. **Timeouts**: Set reasonable timeouts for operations
5. **Cleanup**: Regular cleanup of old data and logs

### Security Considerations

1. **Encryption**: Enable encryption for sensitive data
2. **Environment Variables**: Use environment variables for secrets
3. **Access Control**: Limit access to configuration files
4. **Audit Logging**: Log configuration changes
5. **Validation**: Validate all configuration inputs

## Troubleshooting

### Common Issues

#### Configuration Not Loading

```bash
# Check file permissions
ls -la config.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check configuration validity
memory-config validate config.yaml
```

#### Policy Rules Not Executing

```bash
# Test specific policy
memory-config policy test --rule error_handler --context test.json

# Check policy conditions
memory-config policy list --scope global

# Validate policy configuration
memory-config validate policy-config.yaml
```

#### Performance Issues

```bash
# Check performance score
memory-config stats --format json | jq '.performance_score'

# Monitor configuration health
memory-config monitor --interval 10

# Review performance settings
grep -A 10 'performance:' config.yaml
```

#### Hot Reload Not Working

```bash
# Check auto_reload setting
grep auto_reload config.yaml

# Check file system permissions
ls -la config.yaml

# Check logs for reload errors
grep "reload" application.log
```

### Debug Mode

Enable debug mode for detailed logging:

```yaml
debug_mode: true
monitoring:
  log_level: "DEBUG"
  log_memory_operations: true
  log_performance_metrics: true
```

### Support Resources

- **Configuration Schema**: `schemas/memory_policies.yaml`
- **Example Configurations**: `environments/` directory
- **CLI Help**: `memory-config --help`
- **Validation Errors**: Use `--verbose` flag for detailed errors
- **Performance Metrics**: Monitor via stats command

## Migration Guide

### From Manual Configuration

1. **Export Current Settings**: Document existing configuration
2. **Generate Template**: Use CLI to generate template
3. **Migrate Settings**: Transfer settings to new format
4. **Validate**: Ensure new configuration is valid
5. **Test**: Test with non-production environment
6. **Deploy**: Deploy to production with backup

### Version Upgrades

1. **Backup**: Create backup of current configuration
2. **Review Changes**: Check changelog for breaking changes
3. **Update Schema**: Update to new schema version
4. **Migrate**: Use migration tools if available
5. **Validate**: Comprehensive validation of upgraded config
6. **Test**: Thorough testing before production deployment

This comprehensive configuration and policy system provides enterprise-grade control over memory trigger behavior while maintaining simplicity for common use cases.