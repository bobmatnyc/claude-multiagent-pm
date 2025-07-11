"""
Cost Manager for AI Operations

Provides comprehensive cost tracking, budget management, and optimization
for AI service usage across multiple providers.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics


class BudgetPeriod(Enum):
    """Budget period types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class CostEntry:
    """Cost tracking entry."""

    timestamp: datetime
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    request_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class Budget:
    """Budget configuration."""

    provider: str
    period: BudgetPeriod
    limit: float
    current_usage: float = 0.0
    alert_threshold: float = 0.8  # Alert at 80% of budget
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @property
    def remaining(self) -> float:
        """Get remaining budget."""
        return max(0, self.limit - self.current_usage)

    @property
    def percentage_used(self) -> float:
        """Get percentage of budget used."""
        return (self.current_usage / self.limit) if self.limit > 0 else 0

    @property
    def is_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        return self.current_usage >= self.limit

    @property
    def should_alert(self) -> bool:
        """Check if budget should trigger alert."""
        return self.percentage_used >= self.alert_threshold


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation."""

    type: str
    description: str
    potential_savings: float
    priority: str
    provider: Optional[str] = None
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostManager:
    """
    Cost management system for AI operations.

    Provides cost tracking, budget management, optimization recommendations,
    and detailed analytics across multiple providers.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cost manager.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Cost tracking
        self.cost_entries: List[CostEntry] = []
        self.budgets: Dict[str, Budget] = {}

        # Configuration
        self.max_entries = self.config.get("max_cost_entries", 10000)
        self.auto_optimize = self.config.get("auto_optimize", True)
        self.cost_alert_webhooks = self.config.get("cost_alert_webhooks", [])

        # Cache for expensive calculations
        self._analytics_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update = {}

        # Performance tracking
        self.total_requests_tracked = 0
        self.total_cost_tracked = 0.0

        # Provider cost optimization settings
        self.provider_preferences = {
            "cost_priority": "balanced",  # "cost", "performance", "balanced"
            "preferred_providers": [],
            "excluded_providers": [],
        }

        self.logger.info("Cost manager initialized")

    async def track_usage(
        self,
        provider: str,
        model: str,
        usage: Dict[str, Any],
        cost: float,
        request_id: Optional[str] = None,
    ):
        """
        Track usage and cost for a request.

        Args:
            provider: AI provider name
            model: Model name
            usage: Usage statistics
            cost: Cost of the request
            request_id: Optional request identifier
        """
        # Create cost entry
        entry = CostEntry(
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cost=cost,
            request_id=request_id or f"{provider}_{int(datetime.now().timestamp() * 1000)}",
            metadata=usage,
        )

        # Store entry
        self.cost_entries.append(entry)

        # Update tracking
        self.total_requests_tracked += 1
        self.total_cost_tracked += cost

        # Update budgets
        await self._update_budgets(provider, cost)

        # Limit entries to prevent memory issues
        if len(self.cost_entries) > self.max_entries:
            self.cost_entries = self.cost_entries[-self.max_entries :]

        # Check for budget alerts
        await self._check_budget_alerts(provider)

        # Clear cache
        self._clear_cache()

        self.logger.debug(f"Tracked usage: {provider}/{model} - ${cost:.4f}")

    async def _update_budgets(self, provider: str, cost: float):
        """Update budget usage."""
        for budget_key, budget in self.budgets.items():
            if budget.provider == provider or budget.provider == "all":
                budget.current_usage += cost

    async def _check_budget_alerts(self, provider: str):
        """Check for budget alerts."""
        for budget_key, budget in self.budgets.items():
            if (budget.provider == provider or budget.provider == "all") and budget.should_alert:
                await self._trigger_budget_alert(budget)

    async def _trigger_budget_alert(self, budget: Budget):
        """Trigger budget alert."""
        alert_data = {
            "type": "budget_alert",
            "provider": budget.provider,
            "period": budget.period.value,
            "limit": budget.limit,
            "current_usage": budget.current_usage,
            "percentage_used": budget.percentage_used,
            "is_exceeded": budget.is_exceeded,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.warning(f"Budget alert: {budget.provider} - {budget.percentage_used:.1%} used")

        # Send webhook notifications
        for webhook_url in self.cost_alert_webhooks:
            try:
                # In a real implementation, you would send HTTP POST to webhook
                self.logger.info(f"Sending budget alert to webhook: {webhook_url}")
            except Exception as e:
                self.logger.error(f"Failed to send budget alert: {e}")

    def set_budget(
        self, provider: str, period: BudgetPeriod, limit: float, alert_threshold: float = 0.8
    ) -> str:
        """
        Set budget for a provider.

        Args:
            provider: Provider name or "all" for global budget
            period: Budget period
            limit: Budget limit
            alert_threshold: Alert threshold (0.0 to 1.0)

        Returns:
            Budget key
        """
        budget_key = f"{provider}_{period.value}"

        # Calculate period dates
        now = datetime.now()
        if period == BudgetPeriod.DAILY:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif period == BudgetPeriod.WEEKLY:
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        elif period == BudgetPeriod.MONTHLY:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = start_date.replace(year=now.year + 1, month=1)
            else:
                end_date = start_date.replace(month=now.month + 1)
        elif period == BudgetPeriod.QUARTERLY:
            quarter = (now.month - 1) // 3 + 1
            start_date = now.replace(
                month=(quarter - 1) * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if quarter == 4:
                end_date = start_date.replace(year=now.year + 1, month=1)
            else:
                end_date = start_date.replace(month=quarter * 3 + 1)
        elif period == BudgetPeriod.YEARLY:
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(year=now.year + 1)

        # Calculate current usage for the period
        current_usage = self._calculate_usage_for_period(provider, start_date, end_date)

        self.budgets[budget_key] = Budget(
            provider=provider,
            period=period,
            limit=limit,
            current_usage=current_usage,
            alert_threshold=alert_threshold,
            start_date=start_date,
            end_date=end_date,
        )

        self.logger.info(f"Set budget: {provider} - ${limit:.2f} per {period.value}")
        return budget_key

    def _calculate_usage_for_period(
        self, provider: str, start_date: datetime, end_date: datetime
    ) -> float:
        """Calculate usage for a specific period."""
        usage = 0.0

        for entry in self.cost_entries:
            if start_date <= entry.timestamp < end_date:
                if provider == "all" or entry.provider == provider:
                    usage += entry.cost

        return usage

    def get_budget_status(self, budget_key: str) -> Optional[Dict[str, Any]]:
        """Get budget status."""
        budget = self.budgets.get(budget_key)
        if not budget:
            return None

        return {
            "provider": budget.provider,
            "period": budget.period.value,
            "limit": budget.limit,
            "current_usage": budget.current_usage,
            "remaining": budget.remaining,
            "percentage_used": budget.percentage_used,
            "is_exceeded": budget.is_exceeded,
            "should_alert": budget.should_alert,
            "start_date": budget.start_date.isoformat() if budget.start_date else None,
            "end_date": budget.end_date.isoformat() if budget.end_date else None,
        }

    def get_all_budgets(self) -> Dict[str, Dict[str, Any]]:
        """Get all budget statuses."""
        return {key: self.get_budget_status(key) for key in self.budgets.keys()}

    async def get_remaining_budget(self, provider: str) -> float:
        """Get remaining budget for provider."""
        total_remaining = float("inf")

        for budget in self.budgets.values():
            if budget.provider == provider or budget.provider == "all":
                total_remaining = min(total_remaining, budget.remaining)

        return total_remaining if total_remaining != float("inf") else 0.0

    async def estimate_cost(self, provider: str, model: str, usage: Dict[str, Any]) -> float:
        """
        Estimate cost for a request.

        Args:
            provider: Provider name
            model: Model name
            usage: Expected usage

        Returns:
            Estimated cost
        """
        # This would integrate with provider-specific cost calculation
        # For now, use historical data to estimate

        # Get historical cost per token for this provider/model
        relevant_entries = [
            entry
            for entry in self.cost_entries
            if entry.provider == provider and entry.model == model
        ]

        if not relevant_entries:
            return 0.0

        # Calculate average cost per token
        total_cost = sum(entry.cost for entry in relevant_entries)
        total_tokens = sum(entry.total_tokens for entry in relevant_entries)

        if total_tokens == 0:
            return 0.0

        cost_per_token = total_cost / total_tokens
        estimated_tokens = usage.get("estimated_tokens", 0)

        return cost_per_token * estimated_tokens

    async def get_comprehensive_analytics(self) -> Dict[str, Any]:
        """Get comprehensive cost analytics."""
        cache_key = "comprehensive_analytics"

        # Check cache
        if self._is_cache_valid(cache_key):
            return self._analytics_cache[cache_key]

        # Calculate analytics
        analytics = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": self.total_requests_tracked,
            "total_cost": self.total_cost_tracked,
            "average_cost_per_request": self.total_cost_tracked
            / max(self.total_requests_tracked, 1),
            "providers": {},
            "models": {},
            "time_periods": {},
            "budgets": self.get_all_budgets(),
        }

        # Provider analytics
        provider_costs = {}
        for entry in self.cost_entries:
            if entry.provider not in provider_costs:
                provider_costs[entry.provider] = {
                    "total_cost": 0.0,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "models": {},
                }

            provider_costs[entry.provider]["total_cost"] += entry.cost
            provider_costs[entry.provider]["total_requests"] += 1
            provider_costs[entry.provider]["total_tokens"] += entry.total_tokens

            # Model analytics
            model_key = f"{entry.provider}/{entry.model}"
            if model_key not in provider_costs[entry.provider]["models"]:
                provider_costs[entry.provider]["models"][model_key] = {
                    "total_cost": 0.0,
                    "total_requests": 0,
                    "total_tokens": 0,
                }

            provider_costs[entry.provider]["models"][model_key]["total_cost"] += entry.cost
            provider_costs[entry.provider]["models"][model_key]["total_requests"] += 1
            provider_costs[entry.provider]["models"][model_key][
                "total_tokens"
            ] += entry.total_tokens

        # Add calculated metrics
        for provider, data in provider_costs.items():
            data["average_cost_per_request"] = data["total_cost"] / max(data["total_requests"], 1)
            data["cost_per_token"] = data["total_cost"] / max(data["total_tokens"], 1)

            for model, model_data in data["models"].items():
                model_data["average_cost_per_request"] = model_data["total_cost"] / max(
                    model_data["total_requests"], 1
                )
                model_data["cost_per_token"] = model_data["total_cost"] / max(
                    model_data["total_tokens"], 1
                )

        analytics["providers"] = provider_costs

        # Time period analytics
        now = datetime.now()
        periods = {
            "last_hour": now - timedelta(hours=1),
            "last_day": now - timedelta(days=1),
            "last_week": now - timedelta(days=7),
            "last_month": now - timedelta(days=30),
        }

        for period_name, start_time in periods.items():
            period_entries = [entry for entry in self.cost_entries if entry.timestamp >= start_time]

            analytics["time_periods"][period_name] = {
                "total_cost": sum(entry.cost for entry in period_entries),
                "total_requests": len(period_entries),
                "total_tokens": sum(entry.total_tokens for entry in period_entries),
            }

        # Cache result
        self._analytics_cache[cache_key] = analytics
        self._last_cache_update[cache_key] = datetime.now()

        return analytics

    async def get_cost_optimization_recommendations(self) -> List[CostOptimizationRecommendation]:
        """Get cost optimization recommendations."""
        recommendations = []

        # Analyze provider costs
        provider_analytics = await self._get_provider_cost_analysis()

        # Recommendation 1: Switch to cost-effective providers
        if len(provider_analytics) > 1:
            sorted_providers = sorted(
                provider_analytics.items(), key=lambda x: x[1]["cost_per_token"]
            )

            cheapest_provider = sorted_providers[0]
            most_expensive = sorted_providers[-1]

            if most_expensive[1]["cost_per_token"] > cheapest_provider[1]["cost_per_token"] * 1.5:
                potential_savings = most_expensive[1]["total_cost"] - (
                    most_expensive[1]["total_tokens"] * cheapest_provider[1]["cost_per_token"]
                )

                recommendations.append(
                    CostOptimizationRecommendation(
                        type="provider_switch",
                        description=f"Switch from {most_expensive[0]} to {cheapest_provider[0]} for similar models",
                        potential_savings=potential_savings,
                        priority="high" if potential_savings > 100 else "medium",
                        provider=most_expensive[0],
                    )
                )

        # Recommendation 2: Optimize model selection
        model_analytics = await self._get_model_cost_analysis()

        for model, data in model_analytics.items():
            if data["total_requests"] > 10 and data["cost_per_token"] > 0.001:
                # Check if there are cheaper alternatives
                cheaper_alternatives = [
                    alt
                    for alt, alt_data in model_analytics.items()
                    if alt != model and alt_data["cost_per_token"] < data["cost_per_token"] * 0.8
                ]

                if cheaper_alternatives:
                    cheapest_alt = min(
                        cheaper_alternatives, key=lambda x: model_analytics[x]["cost_per_token"]
                    )
                    potential_savings = data["total_cost"] - (
                        data["total_tokens"] * model_analytics[cheapest_alt]["cost_per_token"]
                    )

                    recommendations.append(
                        CostOptimizationRecommendation(
                            type="model_optimization",
                            description=f"Consider switching from {model} to {cheapest_alt}",
                            potential_savings=potential_savings,
                            priority="medium",
                            model=model,
                        )
                    )

        # Recommendation 3: Budget optimization
        for budget_key, budget in self.budgets.items():
            if budget.is_exceeded:
                recommendations.append(
                    CostOptimizationRecommendation(
                        type="budget_management",
                        description=f"Budget exceeded for {budget.provider} - consider increasing limit or reducing usage",
                        potential_savings=0.0,
                        priority="high",
                        provider=budget.provider,
                    )
                )

        return recommendations

    async def _get_provider_cost_analysis(self) -> Dict[str, Dict[str, Any]]:
        """Get provider cost analysis."""
        provider_data = {}

        for entry in self.cost_entries:
            if entry.provider not in provider_data:
                provider_data[entry.provider] = {
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "total_requests": 0,
                }

            provider_data[entry.provider]["total_cost"] += entry.cost
            provider_data[entry.provider]["total_tokens"] += entry.total_tokens
            provider_data[entry.provider]["total_requests"] += 1

        # Calculate metrics
        for provider, data in provider_data.items():
            data["cost_per_token"] = data["total_cost"] / max(data["total_tokens"], 1)
            data["cost_per_request"] = data["total_cost"] / max(data["total_requests"], 1)

        return provider_data

    async def _get_model_cost_analysis(self) -> Dict[str, Dict[str, Any]]:
        """Get model cost analysis."""
        model_data = {}

        for entry in self.cost_entries:
            model_key = f"{entry.provider}/{entry.model}"

            if model_key not in model_data:
                model_data[model_key] = {"total_cost": 0.0, "total_tokens": 0, "total_requests": 0}

            model_data[model_key]["total_cost"] += entry.cost
            model_data[model_key]["total_tokens"] += entry.total_tokens
            model_data[model_key]["total_requests"] += 1

        # Calculate metrics
        for model, data in model_data.items():
            data["cost_per_token"] = data["total_cost"] / max(data["total_tokens"], 1)
            data["cost_per_request"] = data["total_cost"] / max(data["total_requests"], 1)

        return model_data

    async def optimize_costs(self) -> Dict[str, Any]:
        """Automatically optimize costs."""
        recommendations = await self.get_cost_optimization_recommendations()

        optimization_result = {
            "timestamp": datetime.now().isoformat(),
            "recommendations_count": len(recommendations),
            "high_priority_recommendations": len(
                [r for r in recommendations if r.priority == "high"]
            ),
            "potential_total_savings": sum(r.potential_savings for r in recommendations),
            "actions_taken": [],
            "recommendations": [
                {
                    "type": r.type,
                    "description": r.description,
                    "potential_savings": r.potential_savings,
                    "priority": r.priority,
                    "provider": r.provider,
                    "model": r.model,
                }
                for r in recommendations
            ],
        }

        # Apply automatic optimizations if enabled
        if self.auto_optimize:
            # For now, just log recommendations
            # In a real implementation, you might automatically adjust provider selection
            for recommendation in recommendations:
                if recommendation.priority == "high":
                    self.logger.warning(f"High priority optimization: {recommendation.description}")
                    optimization_result["actions_taken"].append(
                        {"type": "logged_warning", "description": recommendation.description}
                    )

        return optimization_result

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is valid."""
        if cache_key not in self._analytics_cache:
            return False

        last_update = self._last_cache_update.get(cache_key)
        if not last_update:
            return False

        return (datetime.now() - last_update).total_seconds() < self._cache_ttl

    def _clear_cache(self):
        """Clear analytics cache."""
        self._analytics_cache.clear()
        self._last_cache_update.clear()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "healthy": True,
            "total_entries": len(self.cost_entries),
            "total_budgets": len(self.budgets),
            "total_cost_tracked": self.total_cost_tracked,
            "total_requests_tracked": self.total_requests_tracked,
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_entries": len(self.cost_entries),
            "total_budgets": len(self.budgets),
            "total_cost_tracked": self.total_cost_tracked,
            "total_requests_tracked": self.total_requests_tracked,
            "cache_size": len(self._analytics_cache),
            "auto_optimize_enabled": self.auto_optimize,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"CostManager(entries={len(self.cost_entries)}, cost=${self.total_cost_tracked:.2f})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"<CostManager entries={len(self.cost_entries)} budgets={len(self.budgets)} cost=${self.total_cost_tracked:.2f}>"
