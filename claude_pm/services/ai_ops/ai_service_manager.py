"""
AI Service Manager

Manages multiple AI service providers with cost optimization, health monitoring,
and intelligent routing capabilities.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from .circuit_breaker import CircuitBreakerManager
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.google_provider import GoogleProvider
from .providers.openrouter_provider import OpenRouterProvider
from .providers.vercel_provider import VercelProvider
from .authentication_service import AuthenticationService
from .health_monitor import HealthMonitor


class ProviderStatus(Enum):
    """Provider status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNAVAILABLE = "unavailable"


@dataclass
class ProviderMetrics:
    """Provider performance metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    total_cost: float = 0.0
    last_request_time: Optional[datetime] = None
    uptime_percentage: float = 100.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


class AIServiceManager:
    """
    AI Service Manager for multi-provider operations.
    
    Provides unified interface for multiple AI providers with intelligent
    routing, cost optimization, and health monitoring.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AI Service Manager.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.auth_service = AuthenticationService(config)
        self.circuit_breaker_manager = CircuitBreakerManager()
        self.health_monitor = HealthMonitor(config)
        
        # Provider instances
        self.providers: Dict[str, Any] = {}
        self.provider_metrics: Dict[str, ProviderMetrics] = {}
        self.provider_status: Dict[str, ProviderStatus] = {}
        
        # Initialize providers
        self._initialize_providers()
        
        # Performance tracking
        self.total_requests = 0
        self.start_time = datetime.now()
        
        self.logger.info("AI Service Manager initialized with multi-provider support")
    
    def _initialize_providers(self):
        """Initialize all AI service providers."""
        try:
            # Initialize OpenAI provider
            if self.auth_service.is_provider_configured("openai"):
                self.providers["openai"] = OpenAIProvider(
                    auth_service=self.auth_service,
                    config=self.config.get("openai", {})
                )
                self.provider_metrics["openai"] = ProviderMetrics()
                self.provider_status["openai"] = ProviderStatus.HEALTHY
                self.logger.info("OpenAI provider initialized")
            
            # Initialize Anthropic provider
            if self.auth_service.is_provider_configured("anthropic"):
                self.providers["anthropic"] = AnthropicProvider(
                    auth_service=self.auth_service,
                    config=self.config.get("anthropic", {})
                )
                self.provider_metrics["anthropic"] = ProviderMetrics()
                self.provider_status["anthropic"] = ProviderStatus.HEALTHY
                self.logger.info("Anthropic provider initialized")
            
            # Initialize Google provider
            if self.auth_service.is_provider_configured("google"):
                self.providers["google"] = GoogleProvider(
                    auth_service=self.auth_service,
                    config=self.config.get("google", {})
                )
                self.provider_metrics["google"] = ProviderMetrics()
                self.provider_status["google"] = ProviderStatus.HEALTHY
                self.logger.info("Google provider initialized")
            
            # Initialize OpenRouter provider
            if self.auth_service.is_provider_configured("openrouter"):
                self.providers["openrouter"] = OpenRouterProvider(
                    auth_service=self.auth_service,
                    config=self.config.get("openrouter", {})
                )
                self.provider_metrics["openrouter"] = ProviderMetrics()
                self.provider_status["openrouter"] = ProviderStatus.HEALTHY
                self.logger.info("OpenRouter provider initialized")
            
            # Initialize Vercel provider
            if self.auth_service.is_provider_configured("vercel"):
                self.providers["vercel"] = VercelProvider(
                    auth_service=self.auth_service,
                    config=self.config.get("vercel", {})
                )
                self.provider_metrics["vercel"] = ProviderMetrics()
                self.provider_status["vercel"] = ProviderStatus.HEALTHY
                self.logger.info("Vercel provider initialized")
            
            self.logger.info(f"Initialized {len(self.providers)} AI service providers")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize providers: {e}")
            raise
    
    async def execute_request(self, request) -> Any:
        """
        Execute AI service request through appropriate provider.
        
        Args:
            request: AI service request
            
        Returns:
            AI service response
        """
        if request.provider not in self.providers:
            raise ValueError(f"Provider {request.provider} not available")
        
        provider = self.providers[request.provider]
        circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(request.provider)
        
        # Update metrics
        self.total_requests += 1
        metrics = self.provider_metrics[request.provider]
        metrics.total_requests += 1
        
        try:
            # Execute request with circuit breaker protection
            start_time = time.time()
            response = await circuit_breaker.call(
                provider.execute_request,
                request
            )
            execution_time = time.time() - start_time
            
            # Update success metrics
            metrics.successful_requests += 1
            metrics.average_response_time = (
                (metrics.average_response_time * (metrics.successful_requests - 1) + execution_time) /
                metrics.successful_requests
            )
            metrics.last_request_time = datetime.now()
            
            # Update provider status
            self.provider_status[request.provider] = ProviderStatus.HEALTHY
            
            return response
            
        except Exception as e:
            # Update failure metrics
            metrics.failed_requests += 1
            metrics.last_request_time = datetime.now()
            
            # Update provider status based on failure rate
            if metrics.failure_rate > 0.5:
                self.provider_status[request.provider] = ProviderStatus.UNHEALTHY
            elif metrics.failure_rate > 0.2:
                self.provider_status[request.provider] = ProviderStatus.DEGRADED
            
            self.logger.error(f"Request failed for provider {request.provider}: {e}")
            raise
    
    async def get_available_providers(self) -> List[str]:
        """
        Get list of available providers.
        
        Returns:
            List of provider names
        """
        return list(self.providers.keys())
    
    async def provider_supports_model(self, provider: str, model: str) -> bool:
        """
        Check if provider supports specific model.
        
        Args:
            provider: Provider name
            model: Model name
            
        Returns:
            True if provider supports model
        """
        if provider not in self.providers:
            return False
        
        try:
            return await self.providers[provider].supports_model(model)
        except Exception as e:
            self.logger.error(f"Error checking model support: {e}")
            return False
    
    async def get_provider_health(self, provider: str) -> Dict[str, Any]:
        """
        Get provider health information.
        
        Args:
            provider: Provider name
            
        Returns:
            Provider health data
        """
        if provider not in self.providers:
            return {"status": "unavailable", "error": "Provider not found"}
        
        metrics = self.provider_metrics[provider]
        status = self.provider_status[provider]
        
        # Get circuit breaker state
        circuit_state = await self.circuit_breaker_manager.get_circuit_breaker(provider).get_state()
        
        return {
            "status": status.value,
            "success_rate": metrics.success_rate,
            "failure_rate": metrics.failure_rate,
            "average_response_time": metrics.average_response_time,
            "total_requests": metrics.total_requests,
            "total_cost": metrics.total_cost,
            "uptime_percentage": metrics.uptime_percentage,
            "last_request_time": metrics.last_request_time.isoformat() if metrics.last_request_time else None,
            "circuit_breaker_state": circuit_state["state"],
            "circuit_breaker_metrics": circuit_state["metrics"]
        }
    
    async def get_all_provider_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health information for all providers.
        
        Returns:
            Dictionary of provider health data
        """
        health_data = {}
        
        for provider in self.providers.keys():
            health_data[provider] = await self.get_provider_health(provider)
        
        return health_data
    
    async def get_optimal_provider(
        self, 
        criteria: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get optimal provider based on criteria.
        
        Args:
            criteria: Selection criteria
            
        Returns:
            Optimal provider name or None
        """
        available_providers = await self.get_available_providers()
        
        if not available_providers:
            return None
        
        # Score providers based on criteria
        scores = {}
        
        for provider in available_providers:
            score = 0
            health = await self.get_provider_health(provider)
            
            # Health score (0-40 points)
            if health["status"] == "healthy":
                score += 40
            elif health["status"] == "degraded":
                score += 20
            elif health["status"] == "unhealthy":
                score += 5
            
            # Performance score (0-30 points)
            if health["average_response_time"] < 1.0:
                score += 30
            elif health["average_response_time"] < 3.0:
                score += 20
            elif health["average_response_time"] < 5.0:
                score += 10
            else:
                score += 5
            
            # Reliability score (0-30 points)
            success_rate = health["success_rate"]
            if success_rate >= 0.95:
                score += 30
            elif success_rate >= 0.90:
                score += 20
            elif success_rate >= 0.80:
                score += 10
            else:
                score += 5
            
            # Cost considerations (if provided)
            if criteria.get("cost_priority") == "low":
                # Prefer cost-effective providers
                if provider in ["openrouter", "vercel"]:
                    score += 10
            elif criteria.get("cost_priority") == "performance":
                # Prefer performance providers
                if provider in ["openai", "anthropic"]:
                    score += 10
            
            scores[provider] = score
        
        # Return provider with highest score
        return max(scores, key=scores.get) if scores else None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health check results
        """
        health_status = {
            "healthy": True,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_requests": self.total_requests,
            "providers": {}
        }
        
        # Check each provider
        for provider in self.providers.keys():
            provider_health = await self.get_provider_health(provider)
            health_status["providers"][provider] = provider_health
            
            # Update overall health
            if provider_health["status"] not in ["healthy", "degraded"]:
                health_status["healthy"] = False
        
        # Check circuit breakers
        circuit_states = await self.circuit_breaker_manager.get_all_states()
        health_status["circuit_breakers"] = circuit_states
        
        # Check if any circuit breakers are open
        for cb_state in circuit_states.values():
            if cb_state["state"] == "open":
                health_status["healthy"] = False
                break
        
        return health_status
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics.
        
        Returns:
            Performance metrics
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_requests": self.total_requests,
            "providers": {}
        }
        
        # Get metrics for each provider
        for provider, provider_metrics in self.provider_metrics.items():
            metrics["providers"][provider] = {
                "total_requests": provider_metrics.total_requests,
                "successful_requests": provider_metrics.successful_requests,
                "failed_requests": provider_metrics.failed_requests,
                "success_rate": provider_metrics.success_rate,
                "failure_rate": provider_metrics.failure_rate,
                "average_response_time": provider_metrics.average_response_time,
                "total_cost": provider_metrics.total_cost,
                "uptime_percentage": provider_metrics.uptime_percentage,
                "last_request_time": provider_metrics.last_request_time.isoformat() if provider_metrics.last_request_time else None
            }
        
        return metrics
    
    async def reset_metrics(self):
        """Reset all performance metrics."""
        self.total_requests = 0
        self.start_time = datetime.now()
        
        for provider in self.provider_metrics:
            self.provider_metrics[provider] = ProviderMetrics()
        
        # Reset circuit breaker metrics
        await self.circuit_breaker_manager.reset_all()
        
        self.logger.info("All metrics reset")
    
    async def shutdown(self):
        """Shutdown all providers gracefully."""
        for provider_name, provider in self.providers.items():
            try:
                if hasattr(provider, 'shutdown'):
                    await provider.shutdown()
                self.logger.info(f"Provider {provider_name} shutdown successfully")
            except Exception as e:
                self.logger.error(f"Error shutting down provider {provider_name}: {e}")
        
        self.logger.info("AI Service Manager shutdown complete")
    
    def __str__(self) -> str:
        """String representation."""
        return f"AIServiceManager(providers={len(self.providers)}, requests={self.total_requests})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"<AIServiceManager providers={list(self.providers.keys())} requests={self.total_requests}>"