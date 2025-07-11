"""
Configuration Validation System

Comprehensive validation utilities for memory trigger configuration and policies.
Provides schema validation, runtime validation, and configuration testing.
"""

import re
import yaml
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

from .memory_trigger_config import (
    MemoryTriggerConfig,
    PerformanceConfig,
    TriggerPolicyConfig,
    LifecyclePolicyConfig,
    MonitoringConfig,
    BackendConfig,
    Environment,
    MemoryTriggerType,
    MemoryBackend
)
from .policy_engine_config import (
    PolicyRule,
    PolicyCondition,
    PolicyAction,
    PolicyConditionType,
    PolicyActionType,
    PolicyScope
)

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    severity: ValidationSeverity
    message: str
    path: Optional[str] = None
    code: Optional[str] = None
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        prefix = {
            ValidationSeverity.ERROR: "❌",
            ValidationSeverity.WARNING: "⚠️",
            ValidationSeverity.INFO: "ℹ️"
        }[self.severity]
        
        result = f"{prefix} {self.message}"
        if self.path:
            result += f" (at {self.path})"
        if self.suggestion:
            result += f"\n   💡 {self.suggestion}"
        return result


@dataclass
class ValidationResult:
    """Complete validation result"""
    valid: bool
    issues: List[ValidationIssue]
    schema_valid: bool = True
    runtime_valid: bool = True
    performance_score: Optional[float] = None
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]
    
    @property
    def infos(self) -> List[ValidationIssue]:
        """Get only info-level issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.INFO]
    
    def add_issue(self, severity: ValidationSeverity, message: str, 
                  path: Optional[str] = None, code: Optional[str] = None,
                  suggestion: Optional[str] = None) -> None:
        """Add a validation issue"""
        issue = ValidationIssue(severity, message, path, code, suggestion)
        self.issues.append(issue)
        
        if severity == ValidationSeverity.ERROR:
            self.valid = False


class ConfigurationSchemaValidator:
    """Schema-based configuration validator"""
    
    def __init__(self, schema_path: Optional[str] = None):
        if schema_path:
            self.schema = self._load_schema(schema_path)
        else:
            # Use built-in schema
            schema_file = Path(__file__).parent / "schemas" / "memory_policies.yaml"
            self.schema = self._load_schema(str(schema_file))
    
    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """Load validation schema from file"""
        try:
            with open(schema_path, 'r') as f:
                schema_data = yaml.safe_load(f)
            
            # Convert YAML schema to JSON Schema format if needed
            if 'memory_trigger_config' in schema_data:
                return schema_data['memory_trigger_config']
            else:
                return schema_data
                
        except Exception as e:
            logger.error(f"Failed to load schema from {schema_path}: {e}")
            return {}
    
    def validate_schema(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against schema"""
        result = ValidationResult(valid=True, issues=[])
        
        if not self.schema:
            result.add_issue(
                ValidationSeverity.WARNING,
                "No validation schema available",
                suggestion="Provide a valid schema file for comprehensive validation"
            )
            result.schema_valid = False
            return result
        
        try:
            # Validate against JSON Schema
            validate(instance=config_data, schema=self.schema)
            result.add_issue(
                ValidationSeverity.INFO,
                "Configuration passes schema validation"
            )
            
        except ValidationError as e:
            result.schema_valid = False
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Schema validation failed: {e.message}",
                path=f"$.{'.'.join(str(p) for p in e.absolute_path)}",
                code="SCHEMA_VIOLATION",
                suggestion=self._get_schema_suggestion(e)
            )
        
        except Exception as e:
            result.schema_valid = False
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Schema validation error: {e}",
                code="SCHEMA_ERROR"
            )
        
        return result
    
    def _get_schema_suggestion(self, error: ValidationError) -> str:
        """Get helpful suggestion for schema validation error"""
        if "is not of type" in error.message:
            return f"Ensure the value is of the correct type as specified in the schema"
        elif "is not one of" in error.message:
            return f"Use one of the allowed values from the enumeration"
        elif "is a required property" in error.message:
            return f"Add the required property to your configuration"
        elif "does not match" in error.message:
            return f"Ensure the value matches the expected pattern or format"
        else:
            return "Check the configuration against the schema requirements"


class RuntimeConfigurationValidator:
    """Runtime configuration validator with business logic"""
    
    def __init__(self):
        self.validation_rules = [
            self._validate_performance_consistency,
            self._validate_backend_compatibility,
            self._validate_lifecycle_policies,
            self._validate_monitoring_settings,
            self._validate_trigger_policies,
            self._validate_environment_settings,
            self._validate_security_settings,
            self._validate_resource_limits,
            self._validate_feature_compatibility
        ]
    
    def validate_runtime(self, config: MemoryTriggerConfig) -> ValidationResult:
        """Validate configuration with runtime business logic"""
        result = ValidationResult(valid=True, issues=[])
        
        # Run all validation rules
        for rule in self.validation_rules:
            try:
                rule(config, result)
            except Exception as e:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Validation rule failed: {e}",
                    code="VALIDATION_RULE_ERROR"
                )
        
        # Calculate performance score
        result.performance_score = self._calculate_performance_score(config)
        
        return result
    
    def _validate_performance_consistency(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate performance configuration consistency"""
        perf = config.performance
        
        # Check timeout relationships
        if perf.create_timeout < perf.recall_timeout:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Create timeout should typically be >= recall timeout",
                path="performance.create_timeout",
                suggestion="Consider increasing create_timeout or decreasing recall_timeout"
            )
        
        # Check concurrency vs rate limits
        theoretical_max = perf.max_concurrent_operations * perf.rate_limit_per_second
        if theoretical_max > config.max_memory_operations_per_second * 2:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Concurrency settings may exceed global rate limits",
                path="performance.max_concurrent_operations",
                suggestion="Adjust concurrency or increase global rate limit"
            )
        
        # Check cache settings
        if perf.cache_enabled and perf.cache_ttl_seconds > 3600:
            result.add_issue(
                ValidationSeverity.INFO,
                "Cache TTL is quite long (>1 hour), ensure this is intentional",
                path="performance.cache_ttl_seconds"
            )
        
        # Check quality threshold
        if perf.min_memory_quality_score < 0.3:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Very low quality threshold may allow poor quality memories",
                path="performance.min_memory_quality_score",
                suggestion="Consider raising quality threshold to 0.5 or higher"
            )
    
    def _validate_backend_compatibility(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate backend configuration compatibility"""
        backend = config.backend
        
        # Check backend-specific settings
        if backend.backend_type == MemoryBackend.MEM0:
            settings = backend.backend_settings
            
            if not settings.get('api_key_env'):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "mem0 backend requires api_key_env setting",
                    path="backend.backend_settings.api_key_env",
                    suggestion="Specify environment variable name for API key"
                )
            
            if backend.encryption_enabled and not backend.encryption_key_path:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Encryption enabled but no key path specified",
                    path="backend.encryption_key_path"
                )
        
        elif backend.backend_type == MemoryBackend.LOCAL:
            if backend.pool_enabled and backend.pool_size > 5:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Large connection pool not needed for local backend",
                    path="backend.pool_size",
                    suggestion="Consider reducing pool size for local backend"
                )
        
        # Check failover configuration
        if backend.failover_enabled and not backend.failover_backends:
            result.add_issue(
                ValidationSeverity.ERROR,
                "Failover enabled but no failover backends specified",
                path="backend.failover_backends",
                suggestion="Specify at least one failover backend"
            )
    
    def _validate_lifecycle_policies(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate lifecycle policy consistency"""
        lifecycle = config.lifecycle
        
        # Check retention periods
        if lifecycle.important_memory_retention_days < lifecycle.default_retention_days:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Important memories have shorter retention than default",
                path="lifecycle.important_memory_retention_days",
                suggestion="Important memories should typically have longer retention"
            )
        
        # Check cleanup settings
        if lifecycle.auto_cleanup_enabled and lifecycle.cleanup_interval_hours < 1:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Very frequent cleanup may impact performance",
                path="lifecycle.cleanup_interval_hours",
                suggestion="Consider cleanup intervals of at least 1 hour"
            )
        
        # Check archival settings
        if lifecycle.archival_enabled:
            if not lifecycle.archive_backend:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Archival enabled but no archive backend specified",
                    path="lifecycle.archive_backend"
                )
            
            if lifecycle.archive_after_days < lifecycle.default_retention_days:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Archival happens before default retention expires",
                    path="lifecycle.archive_after_days",
                    suggestion="Archive period should be >= retention period"
                )
    
    def _validate_monitoring_settings(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate monitoring configuration"""
        monitoring = config.monitoring
        
        # Check collection intervals
        if monitoring.metrics_collection_interval < 10:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Very frequent metrics collection may impact performance",
                path="monitoring.metrics_collection_interval",
                suggestion="Consider intervals of at least 10 seconds"
            )
        
        # Check health check settings
        if monitoring.health_check_enabled:
            if monitoring.health_check_timeout >= monitoring.health_check_interval:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Health check timeout should be less than interval",
                    path="monitoring.health_check_timeout"
                )
        
        # Check alerting configuration
        if monitoring.alerting_enabled and not monitoring.alert_channels:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Alerting enabled but no alert channels configured",
                path="monitoring.alert_channels",
                suggestion="Configure at least one alert channel"
            )
        
        # Environment-specific monitoring recommendations
        if config.environment == Environment.PRODUCTION:
            if not monitoring.metrics_enabled:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Metrics collection should be enabled in production",
                    path="monitoring.metrics_enabled"
                )
            
            if monitoring.log_level == "DEBUG":
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "DEBUG logging not recommended for production",
                    path="monitoring.log_level",
                    suggestion="Use INFO or WARNING level for production"
                )
    
    def _validate_trigger_policies(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate trigger policy configurations"""
        for name, policy in config.trigger_policies.items():
            self._validate_single_trigger_policy(name, policy, result)
    
    def _validate_single_trigger_policy(self, name: str, policy: TriggerPolicyConfig, result: ValidationResult) -> None:
        """Validate a single trigger policy"""
        path_prefix = f"trigger_policies.{name}"
        
        # Check threshold consistency
        if policy.success_threshold <= policy.failure_threshold:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Success threshold must be > failure threshold in policy '{name}'",
                path=f"{path_prefix}.success_threshold"
            )
        
        # Check context length settings
        if policy.max_context_length <= policy.min_context_length:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Max context length must be > min context length in policy '{name}'",
                path=f"{path_prefix}.max_context_length"
            )
        
        # Check rate limiting
        if policy.max_triggers_per_minute > 1000:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"Very high trigger rate limit in policy '{name}' may cause performance issues",
                path=f"{path_prefix}.max_triggers_per_minute",
                suggestion="Consider reducing rate limit to < 1000/minute"
            )
        
        # Check agent-specific settings
        if policy.trigger_type == MemoryTriggerType.AGENT:
            if not policy.agent_name and not policy.agent_trigger_patterns:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"Agent trigger policy '{name}' has no agent-specific settings",
                    path=f"{path_prefix}.agent_name",
                    suggestion="Specify agent_name or agent_trigger_patterns"
                )
        
        # Environment-specific validation
        if config.environment == Environment.PRODUCTION:
            if policy.min_trigger_confidence < 0.7:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"Low confidence threshold in production policy '{name}'",
                    path=f"{path_prefix}.min_trigger_confidence",
                    suggestion="Use higher confidence (≥0.7) for production"
                )
    
    def _validate_environment_settings(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate environment-specific settings"""
        env = config.environment
        
        if env == Environment.DEVELOPMENT:
            if config.validation_strict:
                result.add_issue(
                    ValidationSeverity.INFO,
                    "Strict validation enabled in development (may slow iteration)",
                    path="validation_strict"
                )
        
        elif env == Environment.TESTING:
            if config.performance.background_processing_enabled:
                result.add_issue(
                    ValidationSeverity.INFO,
                    "Background processing in testing may affect test determinism",
                    path="performance.background_processing_enabled"
                )
        
        elif env == Environment.PRODUCTION:
            if config.debug_mode:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Debug mode should not be enabled in production",
                    path="debug_mode"
                )
            
            if config.auto_reload:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Auto-reload should typically be disabled in production",
                    path="auto_reload",
                    suggestion="Disable auto-reload for production stability"
                )
            
            if not config.backend.encryption_enabled:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Encryption should be enabled in production",
                    path="backend.encryption_enabled"
                )
    
    def _validate_security_settings(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate security-related settings"""
        # Check encryption settings
        if config.backend.encryption_enabled:
            if not config.backend.encryption_key_path:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Encryption enabled but no key path specified",
                    path="backend.encryption_key_path"
                )
            elif config.backend.encryption_key_path.startswith('./'):
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Relative path for encryption key may be insecure",
                    path="backend.encryption_key_path",
                    suggestion="Use absolute path for encryption key"
                )
        
        # Check backend settings for sensitive data
        if config.backend.backend_type == MemoryBackend.MEM0:
            settings = config.backend.backend_settings
            for key, value in settings.items():
                if isinstance(value, str) and any(sensitive in key.lower() for sensitive in ['key', 'token', 'secret', 'password']):
                    if not key.endswith('_env'):
                        result.add_issue(
                            ValidationSeverity.WARNING,
                            f"Sensitive setting '{key}' should reference environment variable",
                            path=f"backend.backend_settings.{key}",
                            suggestion=f"Use '{key}_env' to reference environment variable"
                        )
    
    def _validate_resource_limits(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate resource limit settings"""
        perf = config.performance
        
        # Check memory limits
        total_estimated_memory = (
            perf.max_memories_per_context * perf.cache_max_size * 0.001  # Rough estimate
        )
        
        if total_estimated_memory > perf.max_memory_size_mb:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Estimated memory usage may exceed limit",
                path="performance.max_memory_size_mb",
                suggestion="Increase memory limit or reduce cache/context settings"
            )
        
        # Check worker thread limits
        if perf.worker_thread_count > 20:
            result.add_issue(
                ValidationSeverity.WARNING,
                "High worker thread count may cause resource contention",
                path="performance.worker_thread_count",
                suggestion="Consider reducing worker threads or increasing system resources"
            )
        
        # Check queue size limits
        if perf.background_queue_size > 10000:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Very large background queue may consume excessive memory",
                path="performance.background_queue_size"
            )
    
    def _validate_feature_compatibility(self, config: MemoryTriggerConfig, result: ValidationResult) -> None:
        """Validate feature flag compatibility"""
        features = config.features
        
        # Check feature dependencies
        if features.get('auto_recall', False) and not features.get('pattern_detection', False):
            result.add_issue(
                ValidationSeverity.WARNING,
                "Auto recall works best with pattern detection enabled",
                path="features.auto_recall",
                suggestion="Enable pattern_detection for better auto recall"
            )
        
        if features.get('quality_assessment', False) and not config.performance.cache_enabled:
            result.add_issue(
                ValidationSeverity.INFO,
                "Quality assessment benefits from caching for performance",
                path="features.quality_assessment"
            )
        
        # Environment-specific feature recommendations
        if config.environment == Environment.PRODUCTION:
            if not features.get('quality_assessment', False):
                result.add_issue(
                    ValidationSeverity.INFO,
                    "Quality assessment recommended for production",
                    path="features.quality_assessment"
                )
    
    def _calculate_performance_score(self, config: MemoryTriggerConfig) -> float:
        """Calculate overall performance score (0-1)"""
        score = 1.0
        
        # Performance configuration scoring
        perf = config.performance
        
        # Timeout scoring (lower is better, but not too low)
        optimal_create_timeout = 5.0
        timeout_score = 1.0 - abs(perf.create_timeout - optimal_create_timeout) / 10.0
        score *= max(0.5, timeout_score)
        
        # Concurrency scoring
        if perf.max_concurrent_operations < 5:
            score *= 0.8  # Too low concurrency
        elif perf.max_concurrent_operations > 50:
            score *= 0.9  # Very high concurrency may cause contention
        
        # Caching scoring
        if perf.cache_enabled:
            score *= 1.1  # Bonus for caching
            if 60 <= perf.cache_ttl_seconds <= 600:
                score *= 1.05  # Optimal TTL range
        else:
            score *= 0.9  # Penalty for no caching
        
        # Quality threshold scoring
        if 0.6 <= perf.min_memory_quality_score <= 0.8:
            score *= 1.05  # Good quality threshold
        elif perf.min_memory_quality_score < 0.4:
            score *= 0.8  # Too low quality threshold
        
        # Environment-specific adjustments
        if config.environment == Environment.PRODUCTION:
            if config.backend.encryption_enabled:
                score *= 1.1  # Security bonus
            if config.monitoring.metrics_enabled:
                score *= 1.05  # Monitoring bonus
        
        return min(1.0, score)


class PolicyValidator:
    """Validator for policy engine rules"""
    
    def validate_policy_rule(self, rule: PolicyRule) -> ValidationResult:
        """Validate a policy rule"""
        result = ValidationResult(valid=True, issues=[])
        
        # Basic rule validation
        basic_errors = rule.validate()
        for error in basic_errors:
            result.add_issue(ValidationSeverity.ERROR, error)
        
        # Advanced validation
        self._validate_rule_conditions(rule, result)
        self._validate_rule_actions(rule, result)
        self._validate_rule_performance(rule, result)
        
        return result
    
    def _validate_rule_conditions(self, rule: PolicyRule, result: ValidationResult) -> None:
        """Validate rule conditions"""
        for i, condition in enumerate(rule.conditions):
            self._validate_single_condition(condition, result, f"conditions[{i}]")
    
    def _validate_single_condition(self, condition: PolicyCondition, result: ValidationResult, path: str) -> None:
        """Validate a single condition"""
        # Check regex patterns
        if condition.type == PolicyConditionType.MATCHES_REGEX:
            try:
                re.compile(condition.regex_pattern)
            except re.error as e:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Invalid regex pattern: {e}",
                    path=f"{path}.regex_pattern"
                )
        
        # Check time range format
        if condition.type == PolicyConditionType.TIME_RANGE:
            for time_field, time_value in [('start_time', condition.start_time), ('end_time', condition.end_time)]:
                if time_value and not re.match(r'^\d{2}:\d{2}$', time_value):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        f"Invalid time format, expected HH:MM",
                        path=f"{path}.{time_field}"
                    )
        
        # Check rate limit settings
        if condition.type == PolicyConditionType.RATE_LIMIT:
            if condition.rate_limit and condition.time_window:
                rate_per_second = condition.rate_limit / condition.time_window
                if rate_per_second > 100:
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        "Very high rate limit may cause performance issues",
                        path=f"{path}.rate_limit"
                    )
        
        # Validate sub-conditions recursively
        if condition.sub_conditions:
            for i, sub_condition in enumerate(condition.sub_conditions):
                self._validate_single_condition(sub_condition, result, f"{path}.sub_conditions[{i}]")
    
    def _validate_rule_actions(self, rule: PolicyRule, result: ValidationResult) -> None:
        """Validate rule actions"""
        for i, action in enumerate(rule.actions):
            self._validate_single_action(action, result, f"actions[{i}]")
    
    def _validate_single_action(self, action: PolicyAction, result: ValidationResult, path: str) -> None:
        """Validate a single action"""
        # Check webhook URLs
        if action.type == PolicyActionType.EXECUTE_WEBHOOK:
            url = action.parameters.get('url')
            if url and not url.startswith(('http://', 'https://')):
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Webhook URL should use HTTP/HTTPS protocol",
                    path=f"{path}.parameters.url"
                )
        
        # Check memory action parameters
        if action.type == PolicyActionType.CREATE_MEMORY:
            content = action.parameters.get('content')
            if isinstance(content, str) and len(content) > 10000:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Very long memory content may impact performance",
                    path=f"{path}.parameters.content"
                )
        
        # Check quality score range
        if action.type == PolicyActionType.SET_QUALITY_SCORE:
            score = action.parameters.get('score')
            if score is not None and not (0 <= score <= 1):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Quality score must be between 0 and 1",
                    path=f"{path}.parameters.score"
                )
        
        # Validate action condition if present
        if action.condition:
            self._validate_single_condition(action.condition, result, f"{path}.condition")
    
    def _validate_rule_performance(self, rule: PolicyRule, result: ValidationResult) -> None:
        """Validate rule performance characteristics"""
        # Check for potential infinite loops
        if any(action.type == PolicyActionType.CHAIN_POLICY for action in rule.actions):
            chain_targets = [action.parameters.get('policy_name') for action in rule.actions 
                           if action.type == PolicyActionType.CHAIN_POLICY]
            if rule.name in chain_targets:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Policy rule chains to itself, creating infinite loop",
                    path="actions",
                    suggestion="Remove self-referencing chain action"
                )
        
        # Check for excessive action count
        if len(rule.actions) > 10:
            result.add_issue(
                ValidationSeverity.WARNING,
                "Rule has many actions, may impact performance",
                path="actions",
                suggestion="Consider splitting into multiple rules"
            )
        
        # Check complex conditions
        complex_conditions = sum(1 for cond in rule.conditions 
                               if cond.type in [PolicyConditionType.COMPOSITE_AND, PolicyConditionType.COMPOSITE_OR])
        if complex_conditions > 3:
            result.add_issue(
                ValidationSeverity.INFO,
                "Rule has complex condition structure",
                path="conditions",
                suggestion="Consider simplifying conditions for better maintainability"
            )


class ComprehensiveValidator:
    """Comprehensive configuration validator combining all validation types"""
    
    def __init__(self, schema_path: Optional[str] = None):
        self.schema_validator = ConfigurationSchemaValidator(schema_path)
        self.runtime_validator = RuntimeConfigurationValidator()
        self.policy_validator = PolicyValidator()
    
    def validate_configuration(self, config: MemoryTriggerConfig) -> ValidationResult:
        """Perform comprehensive configuration validation"""
        # Convert config to dictionary for schema validation
        config_dict = config.to_dict()
        self._convert_enums_to_strings(config_dict)
        
        # Schema validation
        schema_result = self.schema_validator.validate_schema(config_dict)
        
        # Runtime validation
        runtime_result = self.runtime_validator.validate_runtime(config)
        
        # Combine results
        combined_result = ValidationResult(valid=True, issues=[])
        combined_result.issues.extend(schema_result.issues)
        combined_result.issues.extend(runtime_result.issues)
        combined_result.schema_valid = schema_result.schema_valid
        combined_result.runtime_valid = runtime_result.runtime_valid
        combined_result.performance_score = runtime_result.performance_score
        
        # Overall validity
        combined_result.valid = (schema_result.valid and runtime_result.valid and 
                               len(combined_result.errors) == 0)
        
        return combined_result
    
    def validate_configuration_file(self, file_path: str) -> ValidationResult:
        """Validate configuration from file"""
        try:
            from .memory_trigger_config import MemoryTriggerConfigManager
            
            manager = MemoryTriggerConfigManager()
            manager.load_config_from_file(file_path)
            config = manager.get_config()
            
            return self.validate_configuration(config)
            
        except Exception as e:
            result = ValidationResult(valid=False, issues=[])
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Failed to load configuration: {e}",
                code="LOAD_ERROR"
            )
            return result
    
    def validate_policy_rules(self, rules: Dict[str, PolicyRule]) -> Dict[str, ValidationResult]:
        """Validate multiple policy rules"""
        results = {}
        
        for name, rule in rules.items():
            results[name] = self.policy_validator.validate_policy_rule(rule)
        
        return results
    
    def _convert_enums_to_strings(self, data: Any) -> None:
        """Convert enum values to strings for schema validation"""
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(value, 'value'):  # Enum
                    data[key] = value.value
                else:
                    self._convert_enums_to_strings(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if hasattr(item, 'value'):  # Enum
                    data[i] = item.value
                else:
                    self._convert_enums_to_strings(item)


# Utility functions for validation testing
def create_test_configuration() -> MemoryTriggerConfig:
    """Create a test configuration for validation testing"""
    from .memory_trigger_config import MemoryTriggerConfig, TriggerPolicyConfig, MemoryTriggerType
    
    config = MemoryTriggerConfig()
    
    # Add a test trigger policy
    test_policy = TriggerPolicyConfig(
        enabled=True,
        trigger_type=MemoryTriggerType.WORKFLOW,
        success_threshold=0.8,
        failure_threshold=0.3
    )
    config.trigger_policies['test_policy'] = test_policy
    
    return config


def validate_config_dict(config_dict: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate configuration dictionary"""
    validator = ComprehensiveValidator()
    
    try:
        from .memory_trigger_config import MemoryTriggerConfig
        config = MemoryTriggerConfig.from_dict(config_dict)
        return validator.validate_configuration(config)
    except Exception as e:
        result = ValidationResult(valid=False, issues=[])
        result.add_issue(
            ValidationSeverity.ERROR,
            f"Failed to create configuration from dictionary: {e}",
            code="CONFIG_CREATE_ERROR"
        )
        return result


def get_validation_summary(result: ValidationResult) -> str:
    """Get a human-readable validation summary"""
    if result.valid:
        status = "✅ VALID"
    else:
        status = "❌ INVALID"
    
    summary = [f"Configuration Status: {status}"]
    
    if result.performance_score is not None:
        score_str = f"{result.performance_score:.2f}"
        summary.append(f"Performance Score: {score_str}/1.0")
    
    if result.issues:
        summary.append(f"Issues Found: {len(result.issues)}")
        summary.append(f"  Errors: {len(result.errors)}")
        summary.append(f"  Warnings: {len(result.warnings)}")
        summary.append(f"  Info: {len(result.infos)}")
    
    summary.append(f"Schema Valid: {'✅' if result.schema_valid else '❌'}")
    summary.append(f"Runtime Valid: {'✅' if result.runtime_valid else '❌'}")
    
    return "\n".join(summary)