"""
Vercel AI Provider Implementation

Provides Vercel AI SDK integration with cost tracking, error handling,
and access to multiple models through Vercel's AI platform.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx
import json

from .base_provider import BaseProvider, ModelInfo, ProviderUsage


class VercelProvider(BaseProvider):
    """Vercel AI SDK provider implementation."""

    def __init__(self, auth_service, config: Optional[Dict[str, Any]] = None):
        """Initialize Vercel provider."""
        config = config or {}
        config.setdefault("api_base_url", "https://api.vercel.com/v1/ai")
        config.setdefault("default_model", "gpt-3.5-turbo")

        super().__init__(auth_service, config)

        # Vercel-specific configuration
        self.team_id = config.get("team_id")
        self.timeout = config.get("timeout", 30.0)
        self.max_retries = config.get("max_retries", 3)

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    def _initialize_models(self):
        """Initialize Vercel AI model information."""
        # Vercel AI provides access to various models
        self.models = {
            # OpenAI models via Vercel
            "gpt-4": ModelInfo(
                name="gpt-4",
                context_length=8192,
                input_cost_per_token=0.03 / 1000,
                output_cost_per_token=0.06 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-4 via Vercel AI",
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
                description="GPT-4 Turbo via Vercel AI",
            ),
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                context_length=4096,
                input_cost_per_token=0.0015 / 1000,
                output_cost_per_token=0.002 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=4096,
                description="GPT-3.5 Turbo via Vercel AI",
            ),
            # Anthropic models via Vercel
            "claude-3-opus": ModelInfo(
                name="claude-3-opus",
                context_length=200000,
                input_cost_per_token=0.015 / 1000,
                output_cost_per_token=0.075 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Claude 3 Opus via Vercel AI",
            ),
            "claude-3-sonnet": ModelInfo(
                name="claude-3-sonnet",
                context_length=200000,
                input_cost_per_token=0.003 / 1000,
                output_cost_per_token=0.015 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Claude 3 Sonnet via Vercel AI",
            ),
            "claude-3-haiku": ModelInfo(
                name="claude-3-haiku",
                context_length=200000,
                input_cost_per_token=0.00025 / 1000,
                output_cost_per_token=0.00125 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=4096,
                description="Claude 3 Haiku via Vercel AI",
            ),
            # Google models via Vercel
            "gemini-pro": ModelInfo(
                name="gemini-pro",
                context_length=32768,
                input_cost_per_token=0.0005 / 1000,
                output_cost_per_token=0.0015 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=2048,
                description="Gemini Pro via Vercel AI",
            ),
            "gemini-pro-vision": ModelInfo(
                name="gemini-pro-vision",
                context_length=16384,
                input_cost_per_token=0.0025 / 1000,
                output_cost_per_token=0.0075 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=2048,
                description="Gemini Pro Vision via Vercel AI",
            ),
            # Embedding models
            "text-embedding-3-small": ModelInfo(
                name="text-embedding-3-small",
                context_length=8191,
                input_cost_per_token=0.00002 / 1000,
                output_cost_per_token=0.0,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=False,
                description="Text embedding model via Vercel AI",
            ),
        }

    async def _make_request(self, request) -> Any:
        """Make Vercel AI API request."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        # Prepare headers
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        if self.team_id:
            headers["X-Vercel-Team"] = self.team_id

        # Prepare request data (Vercel AI uses OpenAI-compatible format)
        data = {
            "model": request.model,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": False,  # Non-streaming for now
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
        # Vercel AI may provide cost information in the response
        if "cost" in usage:
            return usage["cost"]

        # Fallback to model-based calculation
        model_info = self.models.get(usage.get("model", "gpt-3.5-turbo"))
        if not model_info:
            return 0.0

        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        input_cost = input_tokens * model_info.input_cost_per_token
        output_cost = output_tokens * model_info.output_cost_per_token

        return input_cost + output_cost

    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from Vercel AI response."""
        usage = response.get("usage", {})

        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "model": response.get("model", "unknown"),
            "cost": usage.get("cost", 0.0),  # Vercel may provide cost directly
        }

    def _extract_response_text(self, response: Any) -> str:
        """Extract response text from Vercel AI response."""
        choices = response.get("choices", [])
        if not choices:
            return ""

        message = choices[0].get("message", {})
        return message.get("content", "")

    def _extract_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from Vercel AI response."""
        return {
            "id": response.get("id"),
            "object": response.get("object"),
            "created": response.get("created"),
            "model": response.get("model"),
            "choices": len(response.get("choices", [])),
            "finish_reason": response.get("choices", [{}])[0].get("finish_reason"),
            "usage": response.get("usage", {}),
            "provider": "vercel",
        }

    async def create_embedding(
        self, text: str, model: str = "text-embedding-3-small"
    ) -> Dict[str, Any]:
        """Create text embedding via Vercel AI."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        if self.team_id:
            headers["X-Vercel-Team"] = self.team_id

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
        """List available models from Vercel AI."""
        # Vercel AI doesn't have a public models endpoint
        # Return our configured models
        return list(self.models.keys())

    async def validate_api_key(self) -> bool:
        """Validate Vercel API key."""
        api_key = self.auth_service.get_api_key(self.provider_name)
        if not api_key:
            return False

        try:
            # Test with a minimal request
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            if self.team_id:
                headers["X-Vercel-Team"] = self.team_id

            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 1,
            }

            response = await self.client.post(
                f"{self.api_base_url}/chat/completions", headers=headers, json=data
            )

            return response.status_code == 200

        except Exception:
            return False

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics from Vercel."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        headers = {"Authorization": f"Bearer {api_key}"}

        if self.team_id:
            headers["X-Vercel-Team"] = self.team_id

        try:
            response = await self.client.get(f"https://api.vercel.com/v1/ai/usage", headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                return {}

        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Perform Vercel-specific health check."""
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
            "team_id": self.team_id is not None,
            "api_base_url": self.api_base_url,
        }

    async def shutdown(self):
        """Shutdown Vercel provider."""
        await super().shutdown()
        await self.client.aclose()

    def __str__(self) -> str:
        """String representation."""
        return f"VercelProvider(requests={self.total_requests}, cost=${self.usage.cost:.4f})"
