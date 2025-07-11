"""
Anthropic Provider Implementation

Provides Anthropic Claude API integration with cost tracking, error handling,
and enterprise-grade features.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx
import json

from .base_provider import BaseProvider, ModelInfo, ProviderUsage


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider implementation."""
    
    def __init__(self, auth_service, config: Optional[Dict[str, Any]] = None):
        """Initialize Anthropic provider."""
        config = config or {}
        config.setdefault("api_base_url", "https://api.anthropic.com")
        config.setdefault("default_model", "claude-3-sonnet-20240229")
        
        super().__init__(auth_service, config)
        
        # Anthropic-specific configuration
        self.api_version = config.get("api_version", "2023-06-01")
        self.timeout = config.get("timeout", 30.0)
        self.max_retries = config.get("max_retries", 3)
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
    
    def _initialize_models(self):
        """Initialize Anthropic model information."""
        self.models = {
            # Claude 3 models
            "claude-3-opus-20240229": ModelInfo(
                name="claude-3-opus-20240229",
                context_length=200000,
                input_cost_per_token=0.015 / 1000,
                output_cost_per_token=0.075 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Most capable Claude 3 model"
            ),
            "claude-3-sonnet-20240229": ModelInfo(
                name="claude-3-sonnet-20240229",
                context_length=200000,
                input_cost_per_token=0.003 / 1000,
                output_cost_per_token=0.015 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Balanced Claude 3 model"
            ),
            "claude-3-haiku-20240307": ModelInfo(
                name="claude-3-haiku-20240307",
                context_length=200000,
                input_cost_per_token=0.00025 / 1000,
                output_cost_per_token=0.00125 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Fastest Claude 3 model"
            ),
            # Claude 3.5 models
            "claude-3-5-sonnet-20240620": ModelInfo(
                name="claude-3-5-sonnet-20240620",
                context_length=200000,
                input_cost_per_token=0.003 / 1000,
                output_cost_per_token=0.015 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Enhanced Claude 3.5 Sonnet"
            ),
            # Claude 2 models (legacy)
            "claude-2.1": ModelInfo(
                name="claude-2.1",
                context_length=200000,
                input_cost_per_token=0.008 / 1000,
                output_cost_per_token=0.024 / 1000,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Legacy Claude 2.1 model"
            ),
            "claude-2.0": ModelInfo(
                name="claude-2.0",
                context_length=100000,
                input_cost_per_token=0.008 / 1000,
                output_cost_per_token=0.024 / 1000,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Legacy Claude 2.0 model"
            ),
            "claude-instant-1.2": ModelInfo(
                name="claude-instant-1.2",
                context_length=100000,
                input_cost_per_token=0.0008 / 1000,
                output_cost_per_token=0.0024 / 1000,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Fast Claude Instant model"
            )
        }
    
    def _convert_messages_to_anthropic_format(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to Anthropic format."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Add final Assistant: to get response
        if not prompt_parts[-1].startswith("Assistant:"):
            prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    async def _make_request(self, request) -> Any:
        """Make Anthropic API request."""
        api_key = self.auth_service.get_api_key(self.provider_name)
        
        # Prepare headers
        headers = {
            "anthropic-version": self.api_version,
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        # Convert messages to Anthropic format
        if hasattr(request, 'messages') and request.messages:
            # Use new Messages API format
            system_messages = [msg for msg in request.messages if msg.get("role") == "system"]
            other_messages = [msg for msg in request.messages if msg.get("role") != "system"]
            
            data = {
                "model": request.model,
                "max_tokens": request.max_tokens or 4096,
                "messages": other_messages
            }
            
            if system_messages:
                data["system"] = system_messages[0].get("content", "")
            
            if request.temperature is not None:
                data["temperature"] = request.temperature
            
            endpoint = "/v1/messages"
        else:
            # Use legacy completion format
            prompt = self._convert_messages_to_anthropic_format(request.messages)
            
            data = {
                "model": request.model,
                "prompt": prompt,
                "max_tokens_to_sample": request.max_tokens or 4096,
            }
            
            if request.temperature is not None:
                data["temperature"] = request.temperature
            
            endpoint = "/v1/complete"
        
        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.api_base_url}{endpoint}",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Rate limit hit, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    response.raise_for_status()
                    
            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise Exception("Request timeout after retries")
                await asyncio.sleep(2 ** attempt)
                continue
            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
                await asyncio.sleep(2 ** attempt)
                continue
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                continue
        
        raise Exception("Max retries exceeded")
    
    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """Calculate cost based on token usage."""
        model_info = self.models.get(usage.get("model", "claude-3-sonnet-20240229"))
        if not model_info:
            return 0.0
        
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        input_cost = input_tokens * model_info.input_cost_per_token
        output_cost = output_tokens * model_info.output_cost_per_token
        
        return input_cost + output_cost
    
    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from Anthropic response."""
        usage = response.get("usage", {})
        
        # Handle both old and new API formats
        if "input_tokens" in usage:
            # New Messages API format
            return {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                "model": response.get("model", "unknown")
            }
        else:
            # Legacy completion format - estimate tokens
            prompt_tokens = len(response.get("prompt", "").split()) * 1.3  # Rough estimate
            completion_tokens = len(response.get("completion", "").split()) * 1.3
            
            return {
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens),
                "model": response.get("model", "unknown")
            }
    
    def _extract_response_text(self, response: Any) -> str:
        """Extract response text from Anthropic response."""
        # Handle both old and new API formats
        if "content" in response:
            # New Messages API format
            content = response.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            return str(content)
        else:
            # Legacy completion format
            return response.get("completion", "")
    
    def _extract_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from Anthropic response."""
        metadata = {
            "id": response.get("id"),
            "type": response.get("type"),
            "role": response.get("role"),
            "model": response.get("model"),
            "stop_reason": response.get("stop_reason"),
            "stop_sequence": response.get("stop_sequence")
        }
        
        # Handle legacy format
        if "log_id" in response:
            metadata["log_id"] = response.get("log_id")
        
        return metadata
    
    async def validate_api_key(self) -> bool:
        """Validate Anthropic API key."""
        api_key = self.auth_service.get_api_key(self.provider_name)
        if not api_key:
            return False
        
        try:
            # Test with a minimal request
            headers = {
                "anthropic-version": self.api_version,
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            
            response = await self.client.post(
                f"{self.api_base_url}/v1/messages",
                headers=headers,
                json=data
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    async def get_model_info_from_api(self, model: str) -> Optional[Dict[str, Any]]:
        """Get model information from Anthropic API."""
        # Anthropic doesn't have a models endpoint like OpenAI
        # Return local model info if available
        model_info = self.models.get(model)
        if model_info:
            return {
                "id": model_info.name,
                "object": "model",
                "owned_by": "anthropic",
                "context_length": model_info.context_length,
                "supports_functions": model_info.supports_functions,
                "supports_vision": model_info.supports_vision,
                "supports_streaming": model_info.supports_streaming,
                "max_output_tokens": model_info.max_output_tokens,
                "description": model_info.description
            }
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform Anthropic-specific health check."""
        base_health = await super().health_check()
        
        # Test API connectivity
        try:
            api_accessible = await self.validate_api_key()
        except Exception:
            api_accessible = False
        
        return {
            **base_health,
            "api_accessible": api_accessible,
            "models_available": len(self.models),
            "api_version": self.api_version,
            "api_base_url": self.api_base_url
        }
    
    async def shutdown(self):
        """Shutdown Anthropic provider."""
        await super().shutdown()
        await self.client.aclose()
    
    def __str__(self) -> str:
        """String representation."""
        return f"AnthropicProvider(requests={self.total_requests}, cost=${self.usage.cost:.4f})"