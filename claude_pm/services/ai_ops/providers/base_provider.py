"""
Base Provider Abstract Class

Defines the interface and common functionality for all AI service providers.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from ..authentication_service import AuthenticationService


@dataclass
class ProviderUsage:
    """Usage statistics for a provider."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0
    cost: float = 0.0
    
    def add_usage(self, other: 'ProviderUsage'):
        """Add usage from another instance."""
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        self.requests += other.requests
        self.cost += other.cost


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    context_length: int
    input_cost_per_token: float
    output_cost_per_token: float
    supports_functions: bool = False
    supports_vision: bool = False
    supports_streaming: bool = False
    max_output_tokens: Optional[int] = None
    description: str = ""


class BaseProvider(ABC):
    """
    Abstract base class for AI service providers.
    
    Provides common functionality for authentication, cost tracking,
    error handling, and usage monitoring.
    """
    
    def __init__(
        self,
        auth_service: AuthenticationService,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base provider.
        
        Args:
            auth_service: Authentication service instance
            config: Provider-specific configuration
        """
        self.auth_service = auth_service
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Provider metadata
        self.provider_name = self.__class__.__name__.lower().replace("provider", "")
        self.api_base_url = self.config.get("api_base_url", "")
        self.default_model = self.config.get("default_model", "")
        
        # Usage tracking
        self.usage = ProviderUsage()
        self.request_history: List[Dict[str, Any]] = []
        self.max_history_size = self.config.get("max_history_size", 1000)
        
        # Rate limiting
        self.rate_limit_requests = self.config.get("rate_limit_requests", 100)
        self.rate_limit_window = self.config.get("rate_limit_window", 60)
        self.request_timestamps: List[float] = []
        
        # Model information
        self.models: Dict[str, ModelInfo] = {}
        self._initialize_models()
        
        # Performance metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        
        self.logger.info(f"Provider {self.provider_name} initialized")
    
    @abstractmethod
    def _initialize_models(self):
        """Initialize model information. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _make_request(self, request) -> Any:
        """Make actual API request. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """Calculate cost for usage. Must be implemented by subclasses."""
        pass
    
    async def execute_request(self, request) -> Any:
        """
        Execute AI service request with tracking and error handling.
        
        Args:
            request: AI service request
            
        Returns:
            AI service response
        """
        # Check rate limits
        if not await self._check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        # Validate API key
        api_key = self.auth_service.get_api_key(self.provider_name)
        if not api_key:
            raise Exception(f"No API key available for {self.provider_name}")
        
        # Track request
        request_start = time.time()
        self.total_requests += 1
        
        try:
            # Make the actual request
            response = await self._make_request(request)
            
            # Track success
            self.successful_requests += 1
            execution_time = time.time() - request_start
            self.total_response_time += execution_time
            
            # Extract usage information
            usage = self._extract_usage(response)
            cost = self._calculate_cost(usage)
            
            # Update tracking
            self.usage.add_usage(ProviderUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                requests=1,
                cost=cost
            ))
            
            # Record request history
            self._record_request(request, response, execution_time, cost)
            
            # Create response object
            from ..ai_service_manager import AIServiceResponse
            return AIServiceResponse(
                success=True,
                provider=self.provider_name,
                model=request.model,
                response_text=self._extract_response_text(response),
                usage=usage,
                cost=cost,
                execution_time=execution_time,
                metadata=self._extract_metadata(response)
            )
            
        except Exception as e:
            # Track failure
            self.failed_requests += 1
            execution_time = time.time() - request_start
            self.total_response_time += execution_time
            
            # Record failed request
            self._record_request(request, None, execution_time, 0.0, str(e))
            
            self.logger.error(f"Request failed: {e}")
            raise
    
    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from response."""
        # Default implementation - override in subclasses
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    
    def _extract_response_text(self, response: Any) -> str:
        """Extract response text from response."""
        # Default implementation - override in subclasses
        return str(response)
    
    def _extract_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from response."""
        # Default implementation - override in subclasses
        return {}
    
    def _record_request(
        self,
        request: Any,
        response: Any,
        execution_time: float,
        cost: float,
        error: Optional[str] = None
    ):
        """Record request in history."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "model": getattr(request, "model", "unknown"),
            "execution_time": execution_time,
            "cost": cost,
            "success": error is None,
            "error": error
        }
        
        self.request_history.append(record)
        
        # Limit history size
        if len(self.request_history) > self.max_history_size:
            self.request_history = self.request_history[-self.max_history_size:]
    
    async def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits."""
        current_time = time.time()
        
        # Remove old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if current_time - ts < self.rate_limit_window
        ]
        
        # Check if we can make another request
        if len(self.request_timestamps) >= self.rate_limit_requests:
            return False
        
        # Add current timestamp
        self.request_timestamps.append(current_time)
        return True
    
    async def supports_model(self, model: str) -> bool:
        """
        Check if provider supports a specific model.
        
        Args:
            model: Model name
            
        Returns:
            True if model is supported
        """
        return model in self.models
    
    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """
        Get information about a model.
        
        Args:
            model: Model name
            
        Returns:
            Model information or None
        """
        return self.models.get(model)
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List of model names
        """
        return list(self.models.keys())
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Usage statistics
        """
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "average_response_time": self.total_response_time / max(self.total_requests, 1),
            "total_tokens": self.usage.total_tokens,
            "total_cost": self.usage.cost,
            "cost_per_request": self.usage.cost / max(self.total_requests, 1)
        }
    
    def get_recent_requests(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent requests.
        
        Args:
            count: Number of requests to return
            
        Returns:
            List of recent requests
        """
        return self.request_history[-count:]
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.usage = ProviderUsage()
        self.request_history.clear()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.request_timestamps.clear()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "provider": self.provider_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "average_response_time": self.total_response_time / max(self.total_requests, 1),
            "total_cost": self.usage.cost,
            "cost_per_request": self.usage.cost / max(self.total_requests, 1),
            "models_supported": len(self.models),
            "recent_requests": len(self.request_history)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        api_key = self.auth_service.get_api_key(self.provider_name)
        
        return {
            "healthy": api_key is not None,
            "provider": self.provider_name,
            "api_key_available": api_key is not None,
            "models_available": len(self.models),
            "total_requests": self.total_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "average_response_time": self.total_response_time / max(self.total_requests, 1)
        }
    
    async def shutdown(self):
        """Shutdown provider gracefully."""
        self.logger.info(f"Provider {self.provider_name} shutting down")
        # Subclasses can override for cleanup
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(requests={self.total_requests}, cost=${self.usage.cost:.2f})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"<{self.__class__.__name__} provider='{self.provider_name}' requests={self.total_requests}>"