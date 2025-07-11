"""
OpenAI Provider Implementation

Provides OpenAI API integration with cost tracking, error handling,
and enterprise-grade features.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx
import json

from .base_provider import BaseProvider, ModelInfo, ProviderUsage


class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""

    def __init__(self, auth_service, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI provider."""
        config = config or {}
        config.setdefault("api_base_url", "https://api.openai.com/v1")
        config.setdefault("default_model", "gpt-3.5-turbo")

        super().__init__(auth_service, config)

        # OpenAI-specific configuration
        self.organization = config.get("organization")
        self.timeout = config.get("timeout", 30.0)
        self.max_retries = config.get("max_retries", 3)

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    def _initialize_models(self):
        """Initialize OpenAI model information."""
        self.models = {
            # GPT-4 models
            "gpt-4": ModelInfo(
                name="gpt-4",
                context_length=8192,
                input_cost_per_token=0.03 / 1000,
                output_cost_per_token=0.06 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Most capable GPT-4 model",
            ),
            "gpt-4-32k": ModelInfo(
                name="gpt-4-32k",
                context_length=32768,
                input_cost_per_token=0.06 / 1000,
                output_cost_per_token=0.12 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-4 with 32k context",
            ),
            "gpt-4-turbo": ModelInfo(
                name="gpt-4-turbo",
                context_length=128000,
                input_cost_per_token=0.01 / 1000,
                output_cost_per_token=0.03 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-4 Turbo with vision",
            ),
            "gpt-4o": ModelInfo(
                name="gpt-4o",
                context_length=128000,
                input_cost_per_token=0.005 / 1000,
                output_cost_per_token=0.015 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-4o multimodal model",
            ),
            # GPT-3.5 models
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                context_length=4096,
                input_cost_per_token=0.0015 / 1000,
                output_cost_per_token=0.002 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Fast and efficient GPT-3.5",
            ),
            "gpt-3.5-turbo-16k": ModelInfo(
                name="gpt-3.5-turbo-16k",
                context_length=16384,
                input_cost_per_token=0.003 / 1000,
                output_cost_per_token=0.004 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-3.5 with 16k context",
            ),
            # Text models
            "text-davinci-003": ModelInfo(
                name="text-davinci-003",
                context_length=4000,
                input_cost_per_token=0.02 / 1000,
                output_cost_per_token=0.02 / 1000,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=False,
                max_output_tokens=4000,
                description="Legacy text completion model",
            ),
            # Embedding models
            "text-embedding-ada-002": ModelInfo(
                name="text-embedding-ada-002",
                context_length=8191,
                input_cost_per_token=0.0001 / 1000,
                output_cost_per_token=0.0,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=False,
                description="Text embedding model",
            ),
            "text-embedding-3-small": ModelInfo(
                name="text-embedding-3-small",
                context_length=8191,
                input_cost_per_token=0.00002 / 1000,
                output_cost_per_token=0.0,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=False,
                description="Small text embedding model",
            ),
            "text-embedding-3-large": ModelInfo(
                name="text-embedding-3-large",
                context_length=8191,
                input_cost_per_token=0.00013 / 1000,
                output_cost_per_token=0.0,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=False,
                description="Large text embedding model",
            ),
        }

    async def _make_request(self, request) -> Any:
        """Make OpenAI API request."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        # Prepare headers
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        if self.organization:
            headers["OpenAI-Organization"] = self.organization

        # Prepare request data
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
        model_info = self.models.get(usage.get("model", "gpt-3.5-turbo"))
        if not model_info:
            return 0.0

        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        input_cost = input_tokens * model_info.input_cost_per_token
        output_cost = output_tokens * model_info.output_cost_per_token

        return input_cost + output_cost

    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from OpenAI response."""
        usage = response.get("usage", {})

        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "model": response.get("model", "unknown"),
        }

    def _extract_response_text(self, response: Any) -> str:
        """Extract response text from OpenAI response."""
        choices = response.get("choices", [])
        if not choices:
            return ""

        message = choices[0].get("message", {})
        return message.get("content", "")

    def _extract_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from OpenAI response."""
        return {
            "id": response.get("id"),
            "object": response.get("object"),
            "created": response.get("created"),
            "model": response.get("model"),
            "system_fingerprint": response.get("system_fingerprint"),
            "choices": len(response.get("choices", [])),
            "finish_reason": response.get("choices", [{}])[0].get("finish_reason"),
        }

    async def create_embedding(
        self, text: str, model: str = "text-embedding-3-small"
    ) -> Dict[str, Any]:
        """Create text embedding."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        data = {"model": model, "input": text}

        try:
            response = await self.client.post(
                f"{self.api_base_url}/embeddings", headers=headers, json=data
            )

            if response.status_code == 200:
                result = response.json()

                # Track usage
                usage = result.get("usage", {})
                cost = self._calculate_cost(
                    {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": 0,
                        "total_tokens": usage.get("total_tokens", 0),
                        "model": model,
                    }
                )

                self.usage.add_usage(
                    ProviderUsage(
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0),
                        requests=1,
                        cost=cost,
                    )
                )

                return {"embedding": result["data"][0]["embedding"], "usage": usage, "cost": cost}
            else:
                response.raise_for_status()

        except Exception as e:
            self.logger.error(f"Embedding creation failed: {e}")
            raise

    async def list_models(self) -> List[str]:
        """List available models from OpenAI API."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        headers = {"Authorization": f"Bearer {api_key}"}

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
        """Validate OpenAI API key."""
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception:
            return False

    async def get_model_info_from_api(self, model: str) -> Optional[Dict[str, Any]]:
        """Get model information from OpenAI API."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = await self.client.get(f"{self.api_base_url}/models/{model}", headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Perform OpenAI-specific health check."""
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
            "organization": self.organization is not None,
            "api_base_url": self.api_base_url,
        }

    async def shutdown(self):
        """Shutdown OpenAI provider."""
        await super().shutdown()
        await self.client.aclose()

    def __str__(self) -> str:
        """String representation."""
        return f"OpenAIProvider(requests={self.total_requests}, cost=${self.usage.cost:.4f})"
