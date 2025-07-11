"""
OpenRouter Provider Implementation

Provides OpenRouter API integration with cost tracking, error handling,
and access to multiple models through a single API.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx
import json

from .base_provider import BaseProvider, ModelInfo, ProviderUsage


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider implementation."""

    def __init__(self, auth_service, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenRouter provider."""
        config = config or {}
        config.setdefault("api_base_url", "https://openrouter.ai/api/v1")
        config.setdefault("default_model", "anthropic/claude-3-sonnet")

        super().__init__(auth_service, config)

        # OpenRouter-specific configuration
        self.app_name = config.get("app_name", "Claude PM Framework")
        self.app_url = config.get("app_url", "https://github.com/bobmatnyc/claude-multiagent-pm")
        self.timeout = config.get("timeout", 30.0)
        self.max_retries = config.get("max_retries", 3)

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    def _initialize_models(self):
        """Initialize OpenRouter model information."""
        # OpenRouter provides access to many models - these are popular ones
        self.models = {
            # Claude models through OpenRouter
            "anthropic/claude-3-opus": ModelInfo(
                name="anthropic/claude-3-opus",
                context_length=200000,
                input_cost_per_token=0.015 / 1000,
                output_cost_per_token=0.075 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Claude 3 Opus via OpenRouter",
            ),
            "anthropic/claude-3-sonnet": ModelInfo(
                name="anthropic/claude-3-sonnet",
                context_length=200000,
                input_cost_per_token=0.003 / 1000,
                output_cost_per_token=0.015 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Claude 3 Sonnet via OpenRouter",
            ),
            "anthropic/claude-3-haiku": ModelInfo(
                name="anthropic/claude-3-haiku",
                context_length=200000,
                input_cost_per_token=0.00025 / 1000,
                output_cost_per_token=0.00125 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Claude 3 Haiku via OpenRouter",
            ),
            # GPT models through OpenRouter
            "openai/gpt-4": ModelInfo(
                name="openai/gpt-4",
                context_length=8192,
                input_cost_per_token=0.03 / 1000,
                output_cost_per_token=0.06 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-4 via OpenRouter",
            ),
            "openai/gpt-4-turbo": ModelInfo(
                name="openai/gpt-4-turbo",
                context_length=128000,
                input_cost_per_token=0.01 / 1000,
                output_cost_per_token=0.03 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-4 Turbo via OpenRouter",
            ),
            "openai/gpt-3.5-turbo": ModelInfo(
                name="openai/gpt-3.5-turbo",
                context_length=4096,
                input_cost_per_token=0.0015 / 1000,
                output_cost_per_token=0.002 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-3.5 Turbo via OpenRouter",
            ),
            # Gemini models through OpenRouter
            "google/gemini-pro": ModelInfo(
                name="google/gemini-pro",
                context_length=32768,
                input_cost_per_token=0.0005 / 1000,
                output_cost_per_token=0.0015 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=2048,
                description="Gemini Pro via OpenRouter",
            ),
            "google/gemini-pro-vision": ModelInfo(
                name="google/gemini-pro-vision",
                context_length=16384,
                input_cost_per_token=0.0025 / 1000,
                output_cost_per_token=0.0075 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=2048,
                description="Gemini Pro Vision via OpenRouter",
            ),
            # Other popular models
            "meta-llama/llama-3-70b-instruct": ModelInfo(
                name="meta-llama/llama-3-70b-instruct",
                context_length=8192,
                input_cost_per_token=0.0009 / 1000,
                output_cost_per_token=0.0009 / 1000,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Llama 3 70B via OpenRouter",
            ),
            "mistralai/mistral-large": ModelInfo(
                name="mistralai/mistral-large",
                context_length=32000,
                input_cost_per_token=0.008 / 1000,
                output_cost_per_token=0.024 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Mistral Large via OpenRouter",
            ),
        }

    async def _make_request(self, request) -> Any:
        """Make OpenRouter API request."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
        }

        # Prepare request data (OpenRouter uses OpenAI-compatible format)
        data = {
            "model": request.model,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        # Add tools if provided
        if request.tools:
            data["tools"] = request.tools

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.api_base_url}/chat/completions", headers=headers, json=data
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = 2**attempt
                    self.logger.warning(f"Rate limit hit, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    response.raise_for_status()

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise Exception("Request timeout after retries")
                await asyncio.sleep(2**attempt)
                continue
            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
                await asyncio.sleep(2**attempt)
                continue
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)
                continue

        raise Exception("Max retries exceeded")

    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """Calculate cost based on token usage."""
        # OpenRouter provides cost information in the response
        if "cost" in usage:
            return usage["cost"]

        # Fallback to model-based calculation
        model_info = self.models.get(usage.get("model", "anthropic/claude-3-sonnet"))
        if not model_info:
            return 0.0

        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        input_cost = input_tokens * model_info.input_cost_per_token
        output_cost = output_tokens * model_info.output_cost_per_token

        return input_cost + output_cost

    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from OpenRouter response."""
        usage = response.get("usage", {})

        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "model": response.get("model", "unknown"),
            "cost": usage.get("cost", 0.0),  # OpenRouter may provide cost directly
        }

    def _extract_response_text(self, response: Any) -> str:
        """Extract response text from OpenRouter response."""
        choices = response.get("choices", [])
        if not choices:
            return ""

        message = choices[0].get("message", {})
        return message.get("content", "")

    def _extract_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from OpenRouter response."""
        return {
            "id": response.get("id"),
            "object": response.get("object"),
            "created": response.get("created"),
            "model": response.get("model"),
            "choices": len(response.get("choices", [])),
            "finish_reason": response.get("choices", [{}])[0].get("finish_reason"),
            "usage": response.get("usage", {}),
        }

    async def list_models(self) -> List[str]:
        """List available models from OpenRouter API."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
        }

        try:
            response = await self.client.get(f"{self.api_base_url}/models", headers=headers)

            if response.status_code == 200:
                result = response.json()
                return [model["id"] for model in result.get("data", [])]
            else:
                response.raise_for_status()

        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return list(self.models.keys())

    async def validate_api_key(self) -> bool:
        """Validate OpenRouter API key."""
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception:
            return False

    async def get_model_info_from_api(self, model: str) -> Optional[Dict[str, Any]]:
        """Get model information from OpenRouter API."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
        }

        try:
            response = await self.client.get(f"{self.api_base_url}/models/{model}", headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return None

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics from OpenRouter."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
        }

        try:
            response = await self.client.get(
                f"https://openrouter.ai/api/v1/auth/key", headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {}

        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Perform OpenRouter-specific health check."""
        base_health = await super().health_check()

        # Test API connectivity
        try:
            models = await self.list_models()
            api_accessible = True
            models_available = len(models)
        except Exception:
            api_accessible = False
            models_available = 0

        return {
            **base_health,
            "api_accessible": api_accessible,
            "models_available": models_available,
            "app_name": self.app_name,
            "app_url": self.app_url,
            "api_base_url": self.api_base_url,
        }

    async def shutdown(self):
        """Shutdown OpenRouter provider."""
        await super().shutdown()
        await self.client.aclose()

    def __str__(self) -> str:
        """String representation."""
        return f"OpenRouterProvider(requests={self.total_requests}, cost=${self.usage.cost:.4f})"
