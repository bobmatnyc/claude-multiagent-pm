"""
System-Level AI Operations Agent

This agent provides comprehensive AI service management, cost optimization,
and enterprise-grade operations for the Claude PM Framework.

Features:
- Multi-provider AI service management (OpenAI, Anthropic, Google, OpenRouter, Vercel)
- Enterprise security and compliance framework
- Token economics and cost optimization
- Tools management with sandboxed execution
- Circuit breaker patterns for resilience
- Real-time monitoring and health checks
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.base_agent import BaseAgent
from ..core.config import Config
from ..services.ai_ops.ai_service_manager import AIServiceManager
from ..services.ai_ops.cost_manager import CostManager
from ..services.ai_ops.tools_manager import ToolsManager
from ..services.ai_ops.security_framework import SecurityFramework
from ..services.ai_ops.config_manager import ConfigManager


class AIServiceProvider(Enum):
    """Supported AI service providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    VERCEL = "vercel"


@dataclass
class AIServiceRequest:
    """AI service request definition."""

    provider: str
    model: str
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    context: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    cost_budget: Optional[float] = None
    priority: str = "normal"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AIServiceResponse:
    """AI service response definition."""

    success: bool
    provider: str
    model: str
    response_text: str
    usage: Dict[str, Any]
    cost: float
    execution_time: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AIOpsAgent(BaseAgent):
    """
    System-Level AI Operations Agent.

    This agent provides comprehensive AI service management with enterprise-grade
    features including multi-provider support, cost optimization, security,
    and tools management.
    """

    def __init__(self, agent_id: str = "ai_ops_agent", config: Optional[Dict[str, Any]] = None):
        """
        Initialize AI Ops Agent.

        Args:
            agent_id: Unique identifier for the agent
            config: Optional configuration dictionary
        """
        capabilities = [
            "ai_service_management",
            "multi_provider_support",
            "cost_optimization",
            "security_compliance",
            "tools_management",
            "circuit_breaker_patterns",
            "real_time_monitoring",
            "budget_management",
            "key_rotation",
            "audit_logging",
            "performance_optimization",
            "provider_selection",
            "sandboxed_execution",
            "enterprise_security",
        ]

        super().__init__(
            agent_id=agent_id,
            agent_type="ai_operations",
            capabilities=capabilities,
            config=config,
            tier="system",  # System-level agent with highest authority
        )

        # Initialize service managers
        self.ai_service_manager = AIServiceManager(config)
        self.cost_manager = CostManager(config)
        self.tools_manager = ToolsManager(config)
        self.security_framework = SecurityFramework(config)
        self.config_manager = ConfigManager()

        # Agent state
        self.active_requests: Dict[str, AIServiceRequest] = {}
        self.provider_health: Dict[str, Dict[str, Any]] = {}
        self.cost_tracking: Dict[str, float] = {}
        self.security_events: List[Dict[str, Any]] = []

        # Performance metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_cost = 0.0
        self.average_response_time = 0.0

        self.logger.info("AI Ops Agent initialized with enterprise-grade capabilities")

    async def _execute_operation(
        self, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Any:
        """
        Execute AI Ops operations.

        Args:
            operation: Operation to execute
            context: Operation context
            **kwargs: Operation parameters

        Returns:
            Operation result
        """
        try:
            # Route to appropriate handler
            if operation == "ai_service_request":
                return await self.handle_ai_service_request(
                    request=kwargs.get("request"), context=context
                )
            elif operation == "optimize_provider_selection":
                return await self.optimize_provider_selection(
                    requirements=kwargs.get("requirements"), context=context
                )
            elif operation == "manage_enterprise_security":
                return await self.manage_enterprise_security(context=context)
            elif operation == "get_cost_analytics":
                return await self.get_cost_analytics(context=context)
            elif operation == "execute_tool":
                return await self.execute_tool(
                    tool_name=kwargs.get("tool_name"),
                    parameters=kwargs.get("parameters"),
                    context=context,
                )
            elif operation == "health_check":
                return await self.comprehensive_health_check(context=context)
            elif operation == "rotate_keys":
                return await self.rotate_keys(context=context)
            elif operation == "audit_compliance":
                return await self.audit_compliance(context=context)
            elif operation == "optimize_costs":
                return await self.optimize_costs(context=context)
            elif operation == "monitor_performance":
                return await self.monitor_performance(context=context)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            self.logger.error(f"Operation {operation} failed: {e}")
            raise

    async def handle_ai_service_request(
        self, request: AIServiceRequest, context: Optional[Dict[str, Any]] = None
    ) -> AIServiceResponse:
        """
        Handle AI service request with cost optimization and security.

        Args:
            request: AI service request
            context: Optional context

        Returns:
            AI service response
        """
        request_id = f"req_{int(time.time() * 1000)}"
        self.active_requests[request_id] = request

        try:
            # Validate request security
            await self.security_framework.validate_request(request)

            # Check budget constraints
            if request.cost_budget:
                remaining_budget = await self.cost_manager.get_remaining_budget(
                    provider=request.provider
                )
                if remaining_budget < request.cost_budget:
                    raise ValueError(
                        f"Insufficient budget: {remaining_budget} < {request.cost_budget}"
                    )

            # Optimize provider selection if needed
            if request.provider == "auto":
                optimal_provider = await self.optimize_provider_selection(
                    {
                        "model_requirements": request.model,
                        "cost_budget": request.cost_budget,
                        "priority": request.priority,
                    }
                )
                request.provider = optimal_provider

            # Execute request through AI service manager
            start_time = time.time()
            response = await self.ai_service_manager.execute_request(request)
            execution_time = time.time() - start_time

            # Track costs and metrics
            await self.cost_manager.track_usage(
                provider=request.provider,
                model=request.model,
                usage=response.usage,
                cost=response.cost,
            )

            # Update performance metrics
            self.total_requests += 1
            if response.success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            self.total_cost += response.cost
            self.average_response_time = (
                self.average_response_time * (self.total_requests - 1) + execution_time
            ) / self.total_requests

            # Security audit logging
            await self.security_framework.log_request(request, response)

            return response

        except Exception as e:
            self.logger.error(f"AI service request failed: {e}")

            # Create error response
            error_response = AIServiceResponse(
                success=False,
                provider=request.provider,
                model=request.model,
                response_text="",
                usage={},
                cost=0.0,
                execution_time=time.time() - start_time,
                error=str(e),
            )

            # Track failure
            self.failed_requests += 1
            self.total_requests += 1

            # Security event logging
            await self.security_framework.log_security_event(
                event_type="request_failure", details={"request_id": request_id, "error": str(e)}
            )

            return error_response

        finally:
            # Clean up active request
            if request_id in self.active_requests:
                del self.active_requests[request_id]

    async def optimize_provider_selection(
        self, requirements: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Optimize provider selection based on requirements.

        Args:
            requirements: Service requirements
            context: Optional context

        Returns:
            Optimal provider name
        """
        # Get all available providers
        available_providers = await self.ai_service_manager.get_available_providers()

        # Score providers based on requirements
        provider_scores = {}

        for provider in available_providers:
            score = 0

            # Check model availability
            if requirements.get("model_requirements"):
                if await self.ai_service_manager.provider_supports_model(
                    provider, requirements["model_requirements"]
                ):
                    score += 30

            # Check cost efficiency
            if requirements.get("cost_budget"):
                provider_cost = await self.cost_manager.estimate_cost(
                    provider=provider,
                    model=requirements.get("model_requirements", "default"),
                    usage=requirements.get("estimated_usage", {}),
                )
                if provider_cost <= requirements["cost_budget"]:
                    score += 25
                    # Bonus for being under budget
                    if provider_cost < requirements["cost_budget"] * 0.8:
                        score += 10

            # Check performance and reliability
            provider_health = await self.ai_service_manager.get_provider_health(provider)
            if provider_health.get("status") == "healthy":
                score += 20

            # Check response time
            avg_response_time = provider_health.get("avg_response_time", 0)
            if avg_response_time > 0:
                # Prefer faster providers
                if avg_response_time < 2.0:
                    score += 15
                elif avg_response_time < 5.0:
                    score += 10
                else:
                    score += 5

            # Priority adjustments
            priority = requirements.get("priority", "normal")
            if priority == "urgent":
                # Prefer most reliable providers for urgent requests
                if provider_health.get("success_rate", 0) > 0.95:
                    score += 10
            elif priority == "low":
                # Prefer cost-effective providers for low priority
                if provider == "openrouter":  # Often more cost-effective
                    score += 10

            provider_scores[provider] = score

        # Select provider with highest score
        if not provider_scores:
            raise ValueError("No available providers found")

        optimal_provider = max(provider_scores, key=provider_scores.get)

        self.logger.info(
            f"Selected optimal provider: {optimal_provider} (score: {provider_scores[optimal_provider]})"
        )

        return optimal_provider

    async def manage_enterprise_security(
        self, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Manage enterprise security and compliance.

        Args:
            context: Optional context

        Returns:
            Security status
        """
        security_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks_performed": [],
            "issues_found": [],
            "recommendations": [],
        }

        try:
            # Validate all provider authentications
            auth_status = await self.security_framework.validate_all_authentications()
            security_status["checks_performed"].append("authentication_validation")

            if not auth_status["all_valid"]:
                security_status["overall_status"] = "warning"
                security_status["issues_found"].extend(auth_status["issues"])
                security_status["recommendations"].append("Rotate invalid API keys")

            # Check for security events
            recent_events = await self.security_framework.get_recent_security_events(hours=24)
            security_status["checks_performed"].append("security_events_review")

            if recent_events:
                security_status["recent_security_events"] = len(recent_events)
                if any(event.get("severity") == "high" for event in recent_events):
                    security_status["overall_status"] = "critical"
                    security_status["recommendations"].append(
                        "Review high-severity security events"
                    )

            # Validate compliance
            compliance_status = await self.security_framework.check_compliance()
            security_status["checks_performed"].append("compliance_validation")

            if not compliance_status["compliant"]:
                security_status["overall_status"] = "warning"
                security_status["issues_found"].extend(compliance_status["issues"])
                security_status["recommendations"].extend(compliance_status["recommendations"])

            # Check key rotation status
            rotation_status = await self.security_framework.check_key_rotation_status()
            security_status["checks_performed"].append("key_rotation_status")

            if rotation_status["keys_need_rotation"]:
                security_status["overall_status"] = "warning"
                security_status["recommendations"].append("Rotate aging API keys")

            return security_status

        except Exception as e:
            self.logger.error(f"Security management failed: {e}")
            security_status["overall_status"] = "error"
            security_status["issues_found"].append(f"Security check failed: {str(e)}")
            return security_status

    async def get_cost_analytics(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get comprehensive cost analytics.

        Args:
            context: Optional context

        Returns:
            Cost analytics
        """
        try:
            analytics = await self.cost_manager.get_comprehensive_analytics()

            # Add agent-specific metrics
            analytics["agent_metrics"] = {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": (
                    (self.successful_requests / self.total_requests)
                    if self.total_requests > 0
                    else 0
                ),
                "total_cost": self.total_cost,
                "average_response_time": self.average_response_time,
                "cost_per_request": (
                    self.total_cost / self.total_requests if self.total_requests > 0 else 0
                ),
            }

            return analytics

        except Exception as e:
            self.logger.error(f"Cost analytics failed: {e}")
            return {"error": str(e)}

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute tool with sandboxed security.

        Args:
            tool_name: Tool to execute
            parameters: Tool parameters
            context: Optional context

        Returns:
            Tool execution result
        """
        try:
            # Validate tool security
            await self.security_framework.validate_tool_execution(tool_name, parameters)

            # Execute tool through tools manager
            result = await self.tools_manager.execute_tool(
                tool_name=tool_name, parameters=parameters, context=context
            )

            # Log tool execution
            await self.security_framework.log_tool_execution(
                tool_name=tool_name, parameters=parameters, result=result
            )

            return result

        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def comprehensive_health_check(
        self, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive health check.

        Args:
            context: Optional context

        Returns:
            Health check results
        """
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
        }

        try:
            # Check AI service manager health
            ai_service_health = await self.ai_service_manager.health_check()
            health_status["components"]["ai_service_manager"] = ai_service_health

            # Check cost manager health
            cost_manager_health = await self.cost_manager.health_check()
            health_status["components"]["cost_manager"] = cost_manager_health

            # Check tools manager health
            tools_manager_health = await self.tools_manager.health_check()
            health_status["components"]["tools_manager"] = tools_manager_health

            # Check security framework health
            security_health = await self.security_framework.health_check()
            health_status["components"]["security_framework"] = security_health

            # Check config manager health
            config_health = await self.config_manager.health_check()
            health_status["components"]["config_manager"] = config_health

            # Determine overall status
            for component, status in health_status["components"].items():
                if not status.get("healthy", False):
                    health_status["overall_status"] = "unhealthy"
                    break

            # Add agent metrics
            health_status["agent_metrics"] = {
                "total_requests": self.total_requests,
                "success_rate": (
                    (self.successful_requests / self.total_requests)
                    if self.total_requests > 0
                    else 0
                ),
                "average_response_time": self.average_response_time,
                "active_requests": len(self.active_requests),
            }

            return health_status

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
            return health_status

    async def rotate_keys(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Rotate API keys with zero downtime.

        Args:
            context: Optional context

        Returns:
            Key rotation results
        """
        try:
            return await self.security_framework.rotate_keys()
        except Exception as e:
            self.logger.error(f"Key rotation failed: {e}")
            return {"success": False, "error": str(e)}

    async def audit_compliance(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform compliance audit.

        Args:
            context: Optional context

        Returns:
            Compliance audit results
        """
        try:
            return await self.security_framework.audit_compliance()
        except Exception as e:
            self.logger.error(f"Compliance audit failed: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_costs(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize costs across all providers.

        Args:
            context: Optional context

        Returns:
            Cost optimization results
        """
        try:
            return await self.cost_manager.optimize_costs()
        except Exception as e:
            self.logger.error(f"Cost optimization failed: {e}")
            return {"success": False, "error": str(e)}

    async def monitor_performance(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor performance across all services.

        Args:
            context: Optional context

        Returns:
            Performance monitoring results
        """
        try:
            performance_metrics = {
                "timestamp": datetime.now().isoformat(),
                "agent_performance": {
                    "total_requests": self.total_requests,
                    "successful_requests": self.successful_requests,
                    "failed_requests": self.failed_requests,
                    "success_rate": (
                        (self.successful_requests / self.total_requests)
                        if self.total_requests > 0
                        else 0
                    ),
                    "average_response_time": self.average_response_time,
                    "total_cost": self.total_cost,
                    "cost_per_request": (
                        self.total_cost / self.total_requests if self.total_requests > 0 else 0
                    ),
                },
                "service_performance": {},
            }

            # Get performance from all managers
            performance_metrics["service_performance"][
                "ai_service_manager"
            ] = await self.ai_service_manager.get_performance_metrics()
            performance_metrics["service_performance"][
                "cost_manager"
            ] = await self.cost_manager.get_performance_metrics()
            performance_metrics["service_performance"][
                "tools_manager"
            ] = await self.tools_manager.get_performance_metrics()

            return performance_metrics

        except Exception as e:
            self.logger.error(f"Performance monitoring failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        base_status = await super().get_agent_status()

        # Add AI Ops specific status
        ai_ops_status = {
            "providers_available": (
                await self.ai_service_manager.get_available_providers()
                if hasattr(self, "ai_service_manager")
                else []
            ),
            "active_requests": len(self.active_requests),
            "total_requests": self.total_requests,
            "success_rate": (
                (self.successful_requests / self.total_requests) if self.total_requests > 0 else 0
            ),
            "total_cost": self.total_cost,
            "average_response_time": self.average_response_time,
            "security_events": len(self.security_events),
        }

        return {**base_status, **ai_ops_status}

    def __str__(self) -> str:
        """String representation."""
        return f"AIOpsAgent(requests={self.total_requests}, success_rate={self.successful_requests/max(self.total_requests, 1):.2%})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"<AIOpsAgent id='{self.agent_id}' tier='{self.tier}' requests={self.total_requests} cost=${self.total_cost:.2f}>"

    async def _initialize(self) -> None:
        """Initialize AI Operations Agent."""
        try:
            # Initialize configuration manager
            self.config_manager = ConfigManager()

            # Validate configuration
            validation = self.config_manager.validate_configuration()
            if not validation["valid"]:
                logger.warning(f"AI Ops configuration issues: {validation['errors']}")

            # Initialize service components
            await self.service_manager.initialize_ai_services()

            # Initialize cost tracking
            await self.cost_manager.initialize_cost_tracking()

            # Set up health monitoring
            await self.health_monitor.start_monitoring()

            logger.info(f"AI Operations Agent '{self.agent_id}' initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AI Operations Agent: {e}")
            raise

    async def _cleanup(self) -> None:
        """Cleanup AI Operations Agent resources."""
        try:
            # Stop health monitoring
            if hasattr(self, "health_monitor"):
                await self.health_monitor.stop_monitoring()

            # Cleanup service components
            if hasattr(self, "service_manager"):
                await self.service_manager.cleanup_ai_services()

            # Finalize cost tracking
            if hasattr(self, "cost_manager"):
                await self.cost_manager.finalize_cost_tracking()

            logger.info(f"AI Operations Agent '{self.agent_id}' cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during AI Operations Agent cleanup: {e}")
            # Don't re-raise during cleanup
