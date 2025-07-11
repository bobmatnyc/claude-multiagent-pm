"""
Memory Trigger Policy Engine

Policy-based decision engine for memory triggers in the Claude PM Framework.
Provides configurable policies for when and how memories should be created
based on different trigger types and contexts.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import fnmatch

from .trigger_types import TriggerType, TriggerPriority, PolicyDecision
from .interfaces.models import MemoryCategory

# Forward declaration for TriggerEvent - avoid circular import
TriggerEvent = None


@dataclass
class PolicyRule:
    """Individual policy rule configuration."""
    
    name: str
    condition: str              # Condition expression or pattern
    action: PolicyDecision      # Action to take when condition matches
    priority: int = 0           # Rule priority (higher = evaluated first)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, event) -> bool:
        """
        Check if this rule matches the given trigger event.
        
        Args:
            event: The trigger event to evaluate
            
        Returns:
            bool: True if rule matches
        """
        return self._evaluate_condition(event)
    
    def _evaluate_condition(self, event) -> bool:
        """
        Evaluate the condition against the trigger event.
        
        Args:
            event: The trigger event
            
        Returns:
            bool: True if condition matches
        """
        try:
            # Simple pattern matching for now
            condition_lower = self.condition.lower()
            
            # Check trigger type
            if condition_lower.startswith("type:"):
                expected_type = condition_lower[5:].strip()
                return event.trigger_type.value == expected_type
            
            # Check priority
            if condition_lower.startswith("priority:"):
                expected_priority = condition_lower[9:].strip()
                return event.priority.value == expected_priority
            
            # Check project pattern
            if condition_lower.startswith("project:"):
                pattern = condition_lower[8:].strip()
                return fnmatch.fnmatch(event.project_name.lower(), pattern)
            
            # Check source pattern
            if condition_lower.startswith("source:"):
                pattern = condition_lower[7:].strip()
                return fnmatch.fnmatch(event.source.lower(), pattern)
            
            # Check content pattern
            if condition_lower.startswith("content:"):
                pattern = condition_lower[8:].strip()
                return pattern in event.content.lower()
            
            # Check tag pattern
            if condition_lower.startswith("tag:"):
                pattern = condition_lower[4:].strip()
                return any(fnmatch.fnmatch(tag.lower(), pattern) for tag in event.tags)
            
            # Check metadata pattern
            if condition_lower.startswith("metadata:"):
                key_value = condition_lower[9:].strip()
                if "=" in key_value:
                    key, value = key_value.split("=", 1)
                    return event.metadata.get(key.strip()) == value.strip()
                else:
                    return key_value in event.metadata
            
            # Default: match all
            return True
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error evaluating condition '{self.condition}': {e}")
            return False


@dataclass
class PolicyConfig:
    """Configuration for memory trigger policies."""
    
    enabled: bool = True
    default_decision: PolicyDecision = PolicyDecision.ALLOW
    rules: List[PolicyRule] = field(default_factory=list)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    batch_settings: Dict[str, Any] = field(default_factory=dict)
    
    def add_rule(self, rule: PolicyRule):
        """Add a policy rule."""
        self.rules.append(rule)
        # Sort by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a policy rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                return True
        return False


class TriggerPolicyEngine:
    """
    Policy engine for memory trigger decision making.
    
    Evaluates trigger events against configured policies to determine
    whether triggers should be processed, modified, or rejected.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the trigger policy engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Policy configurations by trigger type
        self.policies: Dict[TriggerType, PolicyConfig] = {}
        
        # Rate limiting tracking
        self.rate_limits: Dict[str, Dict[str, int]] = {}
        
        # Initialize default policies
        self._setup_default_policies()
    
    def _setup_default_policies(self):
        """Setup default policies for all trigger types."""
        
        # Workflow completion policies
        workflow_policy = PolicyConfig(
            enabled=True,
            default_decision=PolicyDecision.ALLOW,
            rate_limits={
                "per_project_per_hour": 10,
                "per_workflow_per_hour": 3
            },
            batch_settings={
                "batch_size": 5,
                "batch_timeout": 30
            }
        )
        
        # High priority for successful workflows
        workflow_policy.add_rule(PolicyRule(
            name="successful_workflow",
            condition="metadata:success=true",
            action=PolicyDecision.ALLOW,
            priority=100
        ))
        
        # Lower priority for failed workflows
        workflow_policy.add_rule(PolicyRule(
            name="failed_workflow",
            condition="metadata:success=false",
            action=PolicyDecision.MODIFY,
            priority=50,
            metadata={"modified_priority": TriggerPriority.LOW}
        ))
        
        self.policies[TriggerType.WORKFLOW_COMPLETION] = workflow_policy
        
        # Issue resolution policies
        issue_policy = PolicyConfig(
            enabled=True,
            default_decision=PolicyDecision.ALLOW,
            rate_limits={
                "per_project_per_hour": 15,
                "per_issue_per_day": 1
            }
        )
        
        # Critical issues always captured
        issue_policy.add_rule(PolicyRule(
            name="critical_issue",
            condition="priority:critical",
            action=PolicyDecision.ALLOW,
            priority=200
        ))
        
        # Batch low priority issues
        issue_policy.add_rule(PolicyRule(
            name="low_priority_issue",
            condition="priority:low",
            action=PolicyDecision.BATCH,
            priority=10
        ))
        
        self.policies[TriggerType.ISSUE_RESOLUTION] = issue_policy
        
        # Agent operation policies
        agent_policy = PolicyConfig(
            enabled=True,
            default_decision=PolicyDecision.ALLOW,
            rate_limits={
                "per_agent_per_hour": 20,
                "per_project_per_hour": 50
            },
            batch_settings={
                "batch_size": 10,
                "batch_timeout": 60
            }
        )
        
        # QA operations are important
        agent_policy.add_rule(PolicyRule(
            name="qa_operations",
            condition="source:qa_agent",
            action=PolicyDecision.ALLOW,
            priority=150
        ))
        
        # Documentation operations can be batched
        agent_policy.add_rule(PolicyRule(
            name="documentation_operations",
            condition="source:documentation_agent",
            action=PolicyDecision.BATCH,
            priority=75
        ))
        
        self.policies[TriggerType.AGENT_OPERATION] = agent_policy
        
        # Error resolution policies
        error_policy = PolicyConfig(
            enabled=True,
            default_decision=PolicyDecision.ALLOW,
            rate_limits={
                "per_error_type_per_hour": 5,
                "per_project_per_hour": 20
            }
        )
        
        # All error resolutions are high priority
        error_policy.add_rule(PolicyRule(
            name="error_resolution",
            condition="type:error_resolution",
            action=PolicyDecision.ALLOW,
            priority=300
        ))
        
        self.policies[TriggerType.ERROR_RESOLUTION] = error_policy
        
        # Project milestone policies
        milestone_policy = PolicyConfig(
            enabled=True,
            default_decision=PolicyDecision.ALLOW,
            rate_limits={
                "per_project_per_day": 5
            }
        )
        
        # All milestones are important
        milestone_policy.add_rule(PolicyRule(
            name="project_milestone",
            condition="type:project_milestone",
            action=PolicyDecision.ALLOW,
            priority=250
        ))
        
        self.policies[TriggerType.PROJECT_MILESTONE] = milestone_policy
        
        # Knowledge capture policies
        knowledge_policy = PolicyConfig(
            enabled=True,
            default_decision=PolicyDecision.BATCH,
            rate_limits={
                "per_project_per_hour": 100
            },
            batch_settings={
                "batch_size": 20,
                "batch_timeout": 120
            }
        )
        
        # Important knowledge should be processed immediately
        knowledge_policy.add_rule(PolicyRule(
            name="important_knowledge",
            condition="priority:high",
            action=PolicyDecision.ALLOW,
            priority=100
        ))
        
        self.policies[TriggerType.KNOWLEDGE_CAPTURE] = knowledge_policy
        
        # Pattern detection policies
        pattern_policy = PolicyConfig(
            enabled=True,
            default_decision=PolicyDecision.ALLOW,
            rate_limits={
                "per_pattern_per_hour": 10,
                "per_project_per_hour": 30
            }
        )
        
        self.policies[TriggerType.PATTERN_DETECTION] = pattern_policy
        
        # Decision point policies
        decision_policy = PolicyConfig(
            enabled=True,
            default_decision=PolicyDecision.ALLOW,
            rate_limits={
                "per_project_per_hour": 25
            }
        )
        
        # Critical decisions are always captured
        decision_policy.add_rule(PolicyRule(
            name="critical_decision",
            condition="priority:critical",
            action=PolicyDecision.ALLOW,
            priority=200
        ))
        
        self.policies[TriggerType.DECISION_POINT] = decision_policy
        
        self.logger.info("Initialized default trigger policies")
    
    def evaluate_trigger(self, event) -> tuple[PolicyDecision, Dict[str, Any]]:
        """
        Evaluate a trigger event against configured policies.
        
        Args:
            event: The trigger event to evaluate
            
        Returns:
            tuple[PolicyDecision, Dict[str, Any]]: Decision and metadata
        """
        try:
            # Get policy for trigger type
            policy = self.policies.get(event.trigger_type)
            if not policy:
                self.logger.warning(f"No policy found for trigger type: {event.trigger_type}")
                return PolicyDecision.ALLOW, {}
            
            # Check if policy is enabled
            if not policy.enabled:
                return PolicyDecision.DENY, {"reason": "Policy disabled"}
            
            # Check rate limits
            if not self._check_rate_limits(event, policy):
                return PolicyDecision.DEFER, {"reason": "Rate limit exceeded"}
            
            # Evaluate rules
            for rule in policy.rules:
                if rule.matches(event):
                    self.logger.debug(f"Rule '{rule.name}' matched for event {event.event_id}")
                    
                    # Apply rule action
                    if rule.action == PolicyDecision.MODIFY:
                        # Return modification metadata
                        return rule.action, rule.metadata
                    else:
                        return rule.action, {}
            
            # No rules matched, use default decision
            return policy.default_decision, {}
            
        except Exception as e:
            self.logger.error(f"Error evaluating trigger policy: {e}")
            return PolicyDecision.ALLOW, {"error": str(e)}
    
    def _check_rate_limits(self, event, policy: PolicyConfig) -> bool:
        """
        Check if the trigger event is within rate limits.
        
        Args:
            event: The trigger event
            policy: The policy configuration
            
        Returns:
            bool: True if within rate limits
        """
        # TODO: Implement proper rate limiting with time windows
        # For now, always return True
        return True
    
    def update_policy(self, trigger_type: TriggerType, policy_config: PolicyConfig):
        """
        Update policy configuration for a trigger type.
        
        Args:
            trigger_type: The trigger type
            policy_config: New policy configuration
        """
        self.policies[trigger_type] = policy_config
        self.logger.info(f"Updated policy for trigger type: {trigger_type.value}")
    
    def add_policy_rule(self, trigger_type: TriggerType, rule: PolicyRule):
        """
        Add a policy rule to a trigger type.
        
        Args:
            trigger_type: The trigger type
            rule: The policy rule to add
        """
        if trigger_type not in self.policies:
            self.policies[trigger_type] = PolicyConfig()
        
        self.policies[trigger_type].add_rule(rule)
        self.logger.info(f"Added policy rule '{rule.name}' to trigger type: {trigger_type.value}")
    
    def remove_policy_rule(self, trigger_type: TriggerType, rule_name: str) -> bool:
        """
        Remove a policy rule from a trigger type.
        
        Args:
            trigger_type: The trigger type
            rule_name: Name of the rule to remove
            
        Returns:
            bool: True if rule was removed
        """
        if trigger_type not in self.policies:
            return False
        
        removed = self.policies[trigger_type].remove_rule(rule_name)
        if removed:
            self.logger.info(f"Removed policy rule '{rule_name}' from trigger type: {trigger_type.value}")
        
        return removed
    
    def get_policy_config(self, trigger_type: TriggerType) -> Optional[PolicyConfig]:
        """
        Get policy configuration for a trigger type.
        
        Args:
            trigger_type: The trigger type
            
        Returns:
            Optional[PolicyConfig]: Policy configuration if found
        """
        return self.policies.get(trigger_type)
    
    def get_all_policies(self) -> Dict[TriggerType, PolicyConfig]:
        """
        Get all policy configurations.
        
        Returns:
            Dict[TriggerType, PolicyConfig]: All policies
        """
        return self.policies.copy()
    
    def get_policy_metrics(self) -> Dict[str, Any]:
        """
        Get policy engine metrics.
        
        Returns:
            Dict[str, Any]: Metrics dictionary
        """
        return {
            "total_policies": len(self.policies),
            "enabled_policies": sum(1 for p in self.policies.values() if p.enabled),
            "total_rules": sum(len(p.rules) for p in self.policies.values()),
            "policies_by_type": {
                trigger_type.value: {
                    "enabled": policy.enabled,
                    "rules_count": len(policy.rules),
                    "default_decision": policy.default_decision.value,
                    "rate_limits": policy.rate_limits
                }
                for trigger_type, policy in self.policies.items()
            }
        }
    
    def validate_policy_config(self, policy_config: PolicyConfig) -> List[str]:
        """
        Validate a policy configuration.
        
        Args:
            policy_config: Policy configuration to validate
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate batch settings
        if policy_config.batch_settings:
            batch_size = policy_config.batch_settings.get("batch_size", 0)
            if batch_size <= 0:
                errors.append("batch_size must be greater than 0")
            
            batch_timeout = policy_config.batch_settings.get("batch_timeout", 0)
            if batch_timeout <= 0:
                errors.append("batch_timeout must be greater than 0")
        
        # Validate rate limits
        for limit_name, limit_value in policy_config.rate_limits.items():
            if limit_value <= 0:
                errors.append(f"Rate limit '{limit_name}' must be greater than 0")
        
        # Validate rules
        for rule in policy_config.rules:
            if not rule.name:
                errors.append("Rule name cannot be empty")
            
            if not rule.condition:
                errors.append(f"Rule '{rule.name}' condition cannot be empty")
        
        return errors
    
    def reset_rate_limits(self):
        """Reset all rate limit counters."""
        self.rate_limits.clear()
        self.logger.info("Reset all rate limit counters")
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TriggerPolicyEngine(policies={len(self.policies)}, "
            f"enabled={sum(1 for p in self.policies.values() if p.enabled)})"
        )