"""
Policy Engine Configuration System

Advanced policy engine for memory triggers with rule-based configuration,
conditional logic, and dynamic policy evaluation.
"""

import re
import yaml
import logging
from typing import Dict, Any, Optional, List, Union, Callable, Set
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)


class PolicyConditionType(Enum):
    """Types of policy conditions"""
    ALWAYS = "always"
    NEVER = "never"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES_REGEX = "matches_regex"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    TIME_RANGE = "time_range"
    RATE_LIMIT = "rate_limit"
    PROBABILITY = "probability"
    COMPOSITE_AND = "composite_and"
    COMPOSITE_OR = "composite_or"


class PolicyActionType(Enum):
    """Types of policy actions"""
    CREATE_MEMORY = "create_memory"
    RECALL_MEMORY = "recall_memory"
    UPDATE_MEMORY = "update_memory"
    DELETE_MEMORY = "delete_memory"
    ARCHIVE_MEMORY = "archive_memory"
    SET_QUALITY_SCORE = "set_quality_score"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    TRIGGER_ALERT = "trigger_alert"
    LOG_EVENT = "log_event"
    EXECUTE_WEBHOOK = "execute_webhook"
    CHAIN_POLICY = "chain_policy"
    ABORT = "abort"
    SKIP = "skip"


class PolicyScope(Enum):
    """Policy application scope"""
    GLOBAL = "global"
    AGENT = "agent"
    WORKFLOW = "workflow"
    TASK = "task"
    USER = "user"
    SESSION = "session"


@dataclass
class PolicyCondition:
    """Individual policy condition"""
    type: PolicyConditionType
    field: Optional[str] = None
    value: Any = None
    values: Optional[List[Any]] = None
    regex_pattern: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    rate_limit: Optional[int] = None
    time_window: Optional[int] = None
    probability: Optional[float] = None
    sub_conditions: Optional[List['PolicyCondition']] = None
    negate: bool = False
    
    def __post_init__(self):
        """Validate condition after initialization"""
        if self.type == PolicyConditionType.MATCHES_REGEX and not self.regex_pattern:
            raise ValueError("regex_pattern required for MATCHES_REGEX condition")
        
        if self.type == PolicyConditionType.BETWEEN and (self.min_value is None or self.max_value is None):
            raise ValueError("min_value and max_value required for BETWEEN condition")
        
        if self.type in [PolicyConditionType.IN_LIST, PolicyConditionType.NOT_IN_LIST] and not self.values:
            raise ValueError("values required for IN_LIST/NOT_IN_LIST conditions")
        
        if self.type == PolicyConditionType.TIME_RANGE and (not self.start_time or not self.end_time):
            raise ValueError("start_time and end_time required for TIME_RANGE condition")
        
        if self.type == PolicyConditionType.RATE_LIMIT and (not self.rate_limit or not self.time_window):
            raise ValueError("rate_limit and time_window required for RATE_LIMIT condition")
        
        if self.type == PolicyConditionType.PROBABILITY and (self.probability is None or 
                                                           self.probability < 0 or self.probability > 1):
            raise ValueError("probability must be between 0 and 1 for PROBABILITY condition")
        
        if self.type in [PolicyConditionType.COMPOSITE_AND, PolicyConditionType.COMPOSITE_OR] and not self.sub_conditions:
            raise ValueError("sub_conditions required for composite conditions")


@dataclass
class PolicyAction:
    """Policy action configuration"""
    type: PolicyActionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[PolicyCondition] = None
    priority: int = 0
    async_execution: bool = False
    retry_count: int = 0
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    
    def validate(self) -> List[str]:
        """Validate action configuration"""
        errors = []
        
        if self.priority < 0:
            errors.append("priority must be non-negative")
        if self.retry_count < 0:
            errors.append("retry_count must be non-negative")
        if self.retry_delay < 0:
            errors.append("retry_delay must be non-negative")
        if self.timeout is not None and self.timeout <= 0:
            errors.append("timeout must be positive")
        
        # Validate required parameters for specific action types
        if self.type == PolicyActionType.CREATE_MEMORY:
            required_params = ['content']
            for param in required_params:
                if param not in self.parameters:
                    errors.append(f"Parameter '{param}' required for CREATE_MEMORY action")
        
        elif self.type == PolicyActionType.RECALL_MEMORY:
            if 'query' not in self.parameters and 'memory_id' not in self.parameters:
                errors.append("Either 'query' or 'memory_id' required for RECALL_MEMORY action")
        
        elif self.type == PolicyActionType.SET_QUALITY_SCORE:
            if 'score' not in self.parameters:
                errors.append("Parameter 'score' required for SET_QUALITY_SCORE action")
            elif not (0 <= self.parameters['score'] <= 1):
                errors.append("Quality score must be between 0 and 1")
        
        elif self.type == PolicyActionType.ADD_TAG:
            if 'tag' not in self.parameters:
                errors.append("Parameter 'tag' required for ADD_TAG action")
        
        elif self.type == PolicyActionType.EXECUTE_WEBHOOK:
            required_params = ['url']
            for param in required_params:
                if param not in self.parameters:
                    errors.append(f"Parameter '{param}' required for EXECUTE_WEBHOOK action")
        
        return errors


@dataclass
class PolicyRule:
    """Complete policy rule with conditions and actions"""
    name: str
    description: Optional[str] = None
    enabled: bool = True
    priority: int = 0
    scope: PolicyScope = PolicyScope.GLOBAL
    
    # Rule matching
    conditions: List[PolicyCondition] = field(default_factory=list)
    condition_operator: str = "AND"  # AND or OR
    
    # Actions to execute
    actions: List[PolicyAction] = field(default_factory=list)
    
    # Execution control
    max_executions: Optional[int] = None
    execution_count: int = 0
    last_execution: Optional[datetime] = None
    cooldown_period: Optional[timedelta] = None
    
    # Metadata
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate policy rule"""
        errors = []
        
        if not self.name:
            errors.append("name is required")
        if not self.conditions:
            errors.append("at least one condition is required")
        if not self.actions:
            errors.append("at least one action is required")
        if self.condition_operator not in ["AND", "OR"]:
            errors.append("condition_operator must be 'AND' or 'OR'")
        if self.priority < 0:
            errors.append("priority must be non-negative")
        if self.max_executions is not None and self.max_executions <= 0:
            errors.append("max_executions must be positive")
        
        # Validate actions
        for i, action in enumerate(self.actions):
            action_errors = action.validate()
            for error in action_errors:
                errors.append(f"Action {i}: {error}")
        
        return errors
    
    def can_execute(self) -> bool:
        """Check if rule can be executed based on limits and cooldown"""
        if not self.enabled:
            return False
        
        # Check execution count limit
        if self.max_executions is not None and self.execution_count >= self.max_executions:
            return False
        
        # Check cooldown period
        if (self.cooldown_period is not None and 
            self.last_execution is not None and 
            datetime.now() - self.last_execution < self.cooldown_period):
            return False
        
        return True
    
    def record_execution(self) -> None:
        """Record rule execution"""
        self.execution_count += 1
        self.last_execution = datetime.now()


class PolicyConditionEvaluator:
    """Evaluates policy conditions against context"""
    
    def __init__(self):
        self._rate_limit_cache: Dict[str, List[datetime]] = {}
        self._cache_lock = threading.RLock()
    
    def evaluate_condition(self, condition: PolicyCondition, context: Dict[str, Any]) -> bool:
        """Evaluate a single condition against context"""
        try:
            result = self._evaluate_condition_internal(condition, context)
            return not result if condition.negate else result
        except Exception as e:
            logger.error(f"Error evaluating condition {condition.type}: {e}")
            return False
    
    def _evaluate_condition_internal(self, condition: PolicyCondition, context: Dict[str, Any]) -> bool:
        """Internal condition evaluation logic"""
        if condition.type == PolicyConditionType.ALWAYS:
            return True
        
        elif condition.type == PolicyConditionType.NEVER:
            return False
        
        elif condition.type == PolicyConditionType.EQUALS:
            field_value = self._get_field_value(context, condition.field)
            return field_value == condition.value
        
        elif condition.type == PolicyConditionType.NOT_EQUALS:
            field_value = self._get_field_value(context, condition.field)
            return field_value != condition.value
        
        elif condition.type == PolicyConditionType.CONTAINS:
            field_value = self._get_field_value(context, condition.field)
            if isinstance(field_value, str):
                return condition.value in field_value
            elif isinstance(field_value, (list, set, tuple)):
                return condition.value in field_value
            return False
        
        elif condition.type == PolicyConditionType.NOT_CONTAINS:
            field_value = self._get_field_value(context, condition.field)
            if isinstance(field_value, str):
                return condition.value not in field_value
            elif isinstance(field_value, (list, set, tuple)):
                return condition.value not in field_value
            return True
        
        elif condition.type == PolicyConditionType.MATCHES_REGEX:
            field_value = self._get_field_value(context, condition.field)
            if isinstance(field_value, str):
                return bool(re.search(condition.regex_pattern, field_value))
            return False
        
        elif condition.type == PolicyConditionType.GREATER_THAN:
            field_value = self._get_field_value(context, condition.field)
            try:
                return float(field_value) > condition.value
            except (ValueError, TypeError):
                return False
        
        elif condition.type == PolicyConditionType.LESS_THAN:
            field_value = self._get_field_value(context, condition.field)
            try:
                return float(field_value) < condition.value
            except (ValueError, TypeError):
                return False
        
        elif condition.type == PolicyConditionType.BETWEEN:
            field_value = self._get_field_value(context, condition.field)
            try:
                value = float(field_value)
                return condition.min_value <= value <= condition.max_value
            except (ValueError, TypeError):
                return False
        
        elif condition.type == PolicyConditionType.IN_LIST:
            field_value = self._get_field_value(context, condition.field)
            return field_value in condition.values
        
        elif condition.type == PolicyConditionType.NOT_IN_LIST:
            field_value = self._get_field_value(context, condition.field)
            return field_value not in condition.values
        
        elif condition.type == PolicyConditionType.TIME_RANGE:
            return self._evaluate_time_range(condition)
        
        elif condition.type == PolicyConditionType.RATE_LIMIT:
            return self._evaluate_rate_limit(condition, context)
        
        elif condition.type == PolicyConditionType.PROBABILITY:
            import random
            return random.random() < condition.probability
        
        elif condition.type == PolicyConditionType.COMPOSITE_AND:
            return all(self.evaluate_condition(sub_cond, context) 
                      for sub_cond in condition.sub_conditions)
        
        elif condition.type == PolicyConditionType.COMPOSITE_OR:
            return any(self.evaluate_condition(sub_cond, context) 
                      for sub_cond in condition.sub_conditions)
        
        else:
            logger.warning(f"Unknown condition type: {condition.type}")
            return False
    
    def _get_field_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """Get nested field value from context using dot notation"""
        if not field_path:
            return None
        
        parts = field_path.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
    
    def _evaluate_time_range(self, condition: PolicyCondition) -> bool:
        """Evaluate time range condition"""
        try:
            now = datetime.now()
            current_time = now.time()
            
            start_time = datetime.strptime(condition.start_time, "%H:%M").time()
            end_time = datetime.strptime(condition.end_time, "%H:%M").time()
            
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                # Handle overnight range (e.g., 22:00 to 06:00)
                return current_time >= start_time or current_time <= end_time
        except Exception as e:
            logger.error(f"Error evaluating time range: {e}")
            return False
    
    def _evaluate_rate_limit(self, condition: PolicyCondition, context: Dict[str, Any]) -> bool:
        """Evaluate rate limit condition"""
        try:
            # Create unique key for rate limiting
            key_parts = [condition.field or 'global']
            if condition.field:
                field_value = self._get_field_value(context, condition.field)
                if field_value is not None:
                    key_parts.append(str(field_value))
            
            cache_key = ':'.join(key_parts)
            
            with self._cache_lock:
                now = datetime.now()
                time_window = timedelta(seconds=condition.time_window)
                
                # Get or create rate limit entries
                if cache_key not in self._rate_limit_cache:
                    self._rate_limit_cache[cache_key] = []
                
                entries = self._rate_limit_cache[cache_key]
                
                # Remove old entries outside time window
                entries[:] = [entry for entry in entries if now - entry < time_window]
                
                # Check if under rate limit
                if len(entries) < condition.rate_limit:
                    entries.append(now)
                    return True
                else:
                    return False
        
        except Exception as e:
            logger.error(f"Error evaluating rate limit: {e}")
            return False


class PolicyEngine:
    """Main policy engine for rule evaluation and execution"""
    
    def __init__(self):
        self.rules: Dict[str, PolicyRule] = {}
        self.evaluator = PolicyConditionEvaluator()
        self._execution_lock = threading.RLock()
        self._execution_stats: Dict[str, Dict[str, int]] = {}
    
    def add_rule(self, rule: PolicyRule) -> None:
        """Add policy rule to engine"""
        # Validate rule
        errors = rule.validate()
        if errors:
            raise ValueError(f"Invalid policy rule '{rule.name}': {', '.join(errors)}")
        
        self.rules[rule.name] = rule
        logger.info(f"Added policy rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove policy rule from engine"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed policy rule: {rule_name}")
            return True
        return False
    
    def get_rule(self, rule_name: str) -> Optional[PolicyRule]:
        """Get policy rule by name"""
        return self.rules.get(rule_name)
    
    def list_rules(self, scope: Optional[PolicyScope] = None, 
                   enabled_only: bool = True) -> List[PolicyRule]:
        """List policy rules with optional filtering"""
        rules = []
        for rule in self.rules.values():
            if enabled_only and not rule.enabled:
                continue
            if scope is not None and rule.scope != scope:
                continue
            rules.append(rule)
        
        # Sort by priority (higher priority first)
        return sorted(rules, key=lambda r: r.priority, reverse=True)
    
    def evaluate_rules(self, context: Dict[str, Any], 
                      scope: Optional[PolicyScope] = None) -> List[PolicyRule]:
        """Evaluate all applicable rules against context"""
        matching_rules = []
        
        for rule in self.list_rules(scope=scope, enabled_only=True):
            if not rule.can_execute():
                continue
            
            # Evaluate conditions
            if self._evaluate_rule_conditions(rule, context):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _evaluate_rule_conditions(self, rule: PolicyRule, context: Dict[str, Any]) -> bool:
        """Evaluate all conditions for a rule"""
        if not rule.conditions:
            return True
        
        if rule.condition_operator == "AND":
            return all(self.evaluator.evaluate_condition(condition, context) 
                      for condition in rule.conditions)
        else:  # OR
            return any(self.evaluator.evaluate_condition(condition, context) 
                      for condition in rule.conditions)
    
    def execute_rules(self, context: Dict[str, Any], 
                     scope: Optional[PolicyScope] = None) -> List[Dict[str, Any]]:
        """Execute all matching rules and return results"""
        results = []
        
        matching_rules = self.evaluate_rules(context, scope)
        
        for rule in matching_rules:
            try:
                with self._execution_lock:
                    rule_result = self._execute_rule(rule, context)
                    rule.record_execution()
                    results.append(rule_result)
                    
                    # Update execution stats
                    if rule.name not in self._execution_stats:
                        self._execution_stats[rule.name] = {
                            'executions': 0, 
                            'successes': 0, 
                            'failures': 0
                        }
                    
                    self._execution_stats[rule.name]['executions'] += 1
                    if rule_result['success']:
                        self._execution_stats[rule.name]['successes'] += 1
                    else:
                        self._execution_stats[rule.name]['failures'] += 1
                        
            except Exception as e:
                logger.error(f"Error executing rule '{rule.name}': {e}")
                results.append({
                    'rule_name': rule.name,
                    'success': False,
                    'error': str(e),
                    'actions_executed': 0
                })
        
        return results
    
    def _execute_rule(self, rule: PolicyRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single rule's actions"""
        result = {
            'rule_name': rule.name,
            'success': True,
            'actions_executed': 0,
            'action_results': [],
            'error': None
        }
        
        # Sort actions by priority
        sorted_actions = sorted(rule.actions, key=lambda a: a.priority, reverse=True)
        
        for action in sorted_actions:
            try:
                # Check action condition if present
                if action.condition and not self.evaluator.evaluate_condition(action.condition, context):
                    continue
                
                action_result = self._execute_action(action, context)
                result['action_results'].append(action_result)
                result['actions_executed'] += 1
                
                if not action_result['success']:
                    result['success'] = False
                
                # Handle special actions
                if action.type == PolicyActionType.ABORT:
                    break
                elif action.type == PolicyActionType.SKIP:
                    continue
                    
            except Exception as e:
                logger.error(f"Error executing action {action.type} in rule '{rule.name}': {e}")
                result['success'] = False
                result['error'] = str(e)
                result['action_results'].append({
                    'action_type': action.type.value,
                    'success': False,
                    'error': str(e)
                })
        
        return result
    
    def _execute_action(self, action: PolicyAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single policy action"""
        result = {
            'action_type': action.type.value,
            'success': True,
            'result': None,
            'error': None
        }
        
        try:
            if action.type == PolicyActionType.CREATE_MEMORY:
                result['result'] = self._create_memory_action(action, context)
            
            elif action.type == PolicyActionType.RECALL_MEMORY:
                result['result'] = self._recall_memory_action(action, context)
            
            elif action.type == PolicyActionType.UPDATE_MEMORY:
                result['result'] = self._update_memory_action(action, context)
            
            elif action.type == PolicyActionType.DELETE_MEMORY:
                result['result'] = self._delete_memory_action(action, context)
            
            elif action.type == PolicyActionType.ARCHIVE_MEMORY:
                result['result'] = self._archive_memory_action(action, context)
            
            elif action.type == PolicyActionType.SET_QUALITY_SCORE:
                result['result'] = self._set_quality_score_action(action, context)
            
            elif action.type == PolicyActionType.ADD_TAG:
                result['result'] = self._add_tag_action(action, context)
            
            elif action.type == PolicyActionType.REMOVE_TAG:
                result['result'] = self._remove_tag_action(action, context)
            
            elif action.type == PolicyActionType.TRIGGER_ALERT:
                result['result'] = self._trigger_alert_action(action, context)
            
            elif action.type == PolicyActionType.LOG_EVENT:
                result['result'] = self._log_event_action(action, context)
            
            elif action.type == PolicyActionType.EXECUTE_WEBHOOK:
                result['result'] = self._execute_webhook_action(action, context)
            
            elif action.type == PolicyActionType.CHAIN_POLICY:
                result['result'] = self._chain_policy_action(action, context)
            
            else:
                result['success'] = False
                result['error'] = f"Unknown action type: {action.type}"
        
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def _create_memory_action(self, action: PolicyAction, context: Dict[str, Any]) -> str:
        """Execute create memory action"""
        # This would integrate with the actual memory system
        content = action.parameters.get('content', '')
        tags = action.parameters.get('tags', [])
        metadata = action.parameters.get('metadata', {})
        
        logger.info(f"Policy action: Create memory with content length {len(content)}")
        return f"memory_created_{datetime.now().isoformat()}"
    
    def _recall_memory_action(self, action: PolicyAction, context: Dict[str, Any]) -> List[str]:
        """Execute recall memory action"""
        query = action.parameters.get('query')
        memory_id = action.parameters.get('memory_id')
        limit = action.parameters.get('limit', 10)
        
        logger.info(f"Policy action: Recall memory with query='{query}', memory_id='{memory_id}'")
        return [f"recalled_memory_{i}" for i in range(min(3, limit))]
    
    def _update_memory_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute update memory action"""
        memory_id = action.parameters.get('memory_id')
        updates = action.parameters.get('updates', {})
        
        logger.info(f"Policy action: Update memory {memory_id} with {len(updates)} updates")
        return True
    
    def _delete_memory_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute delete memory action"""
        memory_id = action.parameters.get('memory_id')
        
        logger.info(f"Policy action: Delete memory {memory_id}")
        return True
    
    def _archive_memory_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute archive memory action"""
        memory_id = action.parameters.get('memory_id')
        archive_location = action.parameters.get('archive_location', 'default')
        
        logger.info(f"Policy action: Archive memory {memory_id} to {archive_location}")
        return True
    
    def _set_quality_score_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute set quality score action"""
        memory_id = action.parameters.get('memory_id')
        score = action.parameters.get('score')
        
        logger.info(f"Policy action: Set quality score for memory {memory_id} to {score}")
        return True
    
    def _add_tag_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute add tag action"""
        memory_id = action.parameters.get('memory_id')
        tag = action.parameters.get('tag')
        
        logger.info(f"Policy action: Add tag '{tag}' to memory {memory_id}")
        return True
    
    def _remove_tag_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute remove tag action"""
        memory_id = action.parameters.get('memory_id')
        tag = action.parameters.get('tag')
        
        logger.info(f"Policy action: Remove tag '{tag}' from memory {memory_id}")
        return True
    
    def _trigger_alert_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute trigger alert action"""
        alert_type = action.parameters.get('alert_type', 'info')
        message = action.parameters.get('message', 'Policy alert triggered')
        
        logger.warning(f"Policy alert ({alert_type}): {message}")
        return True
    
    def _log_event_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute log event action"""
        level = action.parameters.get('level', 'info')
        message = action.parameters.get('message', 'Policy event logged')
        
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"Policy event: {message}")
        return True
    
    def _execute_webhook_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute webhook action"""
        url = action.parameters.get('url')
        method = action.parameters.get('method', 'POST')
        headers = action.parameters.get('headers', {})
        data = action.parameters.get('data', {})
        
        logger.info(f"Policy action: Execute webhook {method} {url}")
        # This would make an actual HTTP request in real implementation
        return True
    
    def _chain_policy_action(self, action: PolicyAction, context: Dict[str, Any]) -> bool:
        """Execute chain policy action"""
        policy_name = action.parameters.get('policy_name')
        new_context = action.parameters.get('context', context)
        
        logger.info(f"Policy action: Chain to policy '{policy_name}'")
        
        # Execute chained policy
        if policy_name in self.rules:
            chained_rule = self.rules[policy_name]
            if chained_rule.can_execute():
                result = self._execute_rule(chained_rule, new_context)
                return result['success']
        
        return False
    
    def get_execution_stats(self) -> Dict[str, Dict[str, int]]:
        """Get execution statistics for all rules"""
        with self._execution_lock:
            return dict(self._execution_stats)
    
    def reset_execution_stats(self) -> None:
        """Reset execution statistics"""
        with self._execution_lock:
            self._execution_stats.clear()
    
    def export_rules(self) -> Dict[str, Any]:
        """Export all rules to dictionary format"""
        rules_data = {}
        for name, rule in self.rules.items():
            rules_data[name] = {
                'name': rule.name,
                'description': rule.description,
                'enabled': rule.enabled,
                'priority': rule.priority,
                'scope': rule.scope.value,
                'conditions': [self._serialize_condition(cond) for cond in rule.conditions],
                'condition_operator': rule.condition_operator,
                'actions': [self._serialize_action(action) for action in rule.actions],
                'max_executions': rule.max_executions,
                'cooldown_period': rule.cooldown_period.total_seconds() if rule.cooldown_period else None,
                'tags': list(rule.tags),
                'metadata': rule.metadata
            }
        return rules_data
    
    def import_rules(self, rules_data: Dict[str, Any]) -> List[str]:
        """Import rules from dictionary format"""
        errors = []
        
        for rule_name, rule_config in rules_data.items():
            try:
                rule = self._deserialize_rule(rule_config)
                self.add_rule(rule)
            except Exception as e:
                errors.append(f"Failed to import rule '{rule_name}': {e}")
        
        return errors
    
    def _serialize_condition(self, condition: PolicyCondition) -> Dict[str, Any]:
        """Serialize condition to dictionary"""
        data = {
            'type': condition.type.value,
            'negate': condition.negate
        }
        
        for field in ['field', 'value', 'values', 'regex_pattern', 'min_value', 'max_value',
                     'start_time', 'end_time', 'rate_limit', 'time_window', 'probability']:
            value = getattr(condition, field)
            if value is not None:
                data[field] = value
        
        if condition.sub_conditions:
            data['sub_conditions'] = [self._serialize_condition(sub) for sub in condition.sub_conditions]
        
        return data
    
    def _serialize_action(self, action: PolicyAction) -> Dict[str, Any]:
        """Serialize action to dictionary"""
        data = {
            'type': action.type.value,
            'parameters': action.parameters,
            'priority': action.priority,
            'async_execution': action.async_execution,
            'retry_count': action.retry_count,
            'retry_delay': action.retry_delay
        }
        
        if action.timeout is not None:
            data['timeout'] = action.timeout
        
        if action.condition:
            data['condition'] = self._serialize_condition(action.condition)
        
        return data
    
    def _deserialize_rule(self, rule_config: Dict[str, Any]) -> PolicyRule:
        """Deserialize rule from dictionary"""
        conditions = [self._deserialize_condition(cond) for cond in rule_config.get('conditions', [])]
        actions = [self._deserialize_action(action) for action in rule_config.get('actions', [])]
        
        cooldown_period = None
        if rule_config.get('cooldown_period'):
            cooldown_period = timedelta(seconds=rule_config['cooldown_period'])
        
        return PolicyRule(
            name=rule_config['name'],
            description=rule_config.get('description'),
            enabled=rule_config.get('enabled', True),
            priority=rule_config.get('priority', 0),
            scope=PolicyScope(rule_config.get('scope', 'global')),
            conditions=conditions,
            condition_operator=rule_config.get('condition_operator', 'AND'),
            actions=actions,
            max_executions=rule_config.get('max_executions'),
            cooldown_period=cooldown_period,
            tags=set(rule_config.get('tags', [])),
            metadata=rule_config.get('metadata', {})
        )
    
    def _deserialize_condition(self, cond_config: Dict[str, Any]) -> PolicyCondition:
        """Deserialize condition from dictionary"""
        sub_conditions = None
        if 'sub_conditions' in cond_config:
            sub_conditions = [self._deserialize_condition(sub) for sub in cond_config['sub_conditions']]
        
        return PolicyCondition(
            type=PolicyConditionType(cond_config['type']),
            field=cond_config.get('field'),
            value=cond_config.get('value'),
            values=cond_config.get('values'),
            regex_pattern=cond_config.get('regex_pattern'),
            min_value=cond_config.get('min_value'),
            max_value=cond_config.get('max_value'),
            start_time=cond_config.get('start_time'),
            end_time=cond_config.get('end_time'),
            rate_limit=cond_config.get('rate_limit'),
            time_window=cond_config.get('time_window'),
            probability=cond_config.get('probability'),
            sub_conditions=sub_conditions,
            negate=cond_config.get('negate', False)
        )
    
    def _deserialize_action(self, action_config: Dict[str, Any]) -> PolicyAction:
        """Deserialize action from dictionary"""
        condition = None
        if 'condition' in action_config:
            condition = self._deserialize_condition(action_config['condition'])
        
        return PolicyAction(
            type=PolicyActionType(action_config['type']),
            parameters=action_config.get('parameters', {}),
            condition=condition,
            priority=action_config.get('priority', 0),
            async_execution=action_config.get('async_execution', False),
            retry_count=action_config.get('retry_count', 0),
            retry_delay=action_config.get('retry_delay', 1.0),
            timeout=action_config.get('timeout')
        )


class PolicyEngineConfig:
    """Policy engine configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.engine = PolicyEngine()
        self.config_file = config_file
        
        if config_file:
            self.load_from_file(config_file)
    
    def load_from_file(self, file_path: str) -> None:
        """Load policy configuration from YAML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if 'rules' in config_data:
                errors = self.engine.import_rules(config_data['rules'])
                if errors:
                    logger.warning(f"Errors importing rules: {', '.join(errors)}")
            
            logger.info(f"Policy configuration loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load policy configuration from {file_path}: {e}")
            raise
    
    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """Save policy configuration to YAML file"""
        if not file_path:
            file_path = self.config_file
        
        if not file_path:
            raise ValueError("No file path specified for saving configuration")
        
        try:
            config_data = {
                'rules': self.engine.export_rules()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"Policy configuration saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save policy configuration to {file_path}: {e}")
            raise
    
    def get_engine(self) -> PolicyEngine:
        """Get the policy engine instance"""
        return self.engine


# Global policy engine instance
_policy_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    """Get global policy engine instance"""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine


def initialize_policy_engine(config_file: Optional[str] = None) -> PolicyEngine:
    """Initialize global policy engine with configuration"""
    global _policy_engine
    config = PolicyEngineConfig(config_file)
    _policy_engine = config.get_engine()
    return _policy_engine