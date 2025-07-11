"""
Google Gemini Provider Implementation

Provides Google Gemini API integration with cost tracking, error handling,
and enterprise-grade features.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx
import json

from .base_provider import BaseProvider, ModelInfo, ProviderUsage


class GoogleProvider(BaseProvider):
    """Google Gemini API provider implementation."""

    def __init__(self, auth_service, config: Optional[Dict[str, Any]] = None):
        """Initialize Google provider."""
        config = config or {}
        config.setdefault("api_base_url", "https://generativelanguage.googleapis.com/v1beta")
        config.setdefault("default_model", "gemini-1.5-flash")

        super().__init__(auth_service, config)

        # Google-specific configuration
        self.timeout = config.get("timeout", 30.0)
        self.max_retries = config.get("max_retries", 3)

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    def _initialize_models(self):
        """Initialize Google Gemini model information."""
        self.models = {
            # Gemini 1.5 models
            "gemini-1.5-pro": ModelInfo(
                name="gemini-1.5-pro",
                context_length=2097152,  # 2M tokens
                input_cost_per_token=0.0035 / 1000,
                output_cost_per_token=0.0105 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=8192,
                description="Most capable Gemini 1.5 model",
            ),
            "gemini-1.5-flash": ModelInfo(
                name="gemini-1.5-flash",
                context_length=1048576,  # 1M tokens
                input_cost_per_token=0.00035 / 1000,
                output_cost_per_token=0.00105 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=8192,
                description="Fast and efficient Gemini 1.5 model",
            ),
            # Gemini 1.0 models
            "gemini-1.0-pro": ModelInfo(
                name="gemini-1.0-pro",
                context_length=32768,
                input_cost_per_token=0.0005 / 1000,
                output_cost_per_token=0.0015 / 1000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                max_output_tokens=2048,
                description="Gemini 1.0 Pro model",
            ),
            "gemini-1.0-pro-vision": ModelInfo(
                name="gemini-1.0-pro-vision",
                context_length=16384,
                input_cost_per_token=0.0025 / 1000,
                output_cost_per_token=0.0075 / 1000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                max_output_tokens=2048,
                description="Gemini 1.0 Pro with vision capabilities",
            ),
            # Gemini embedding models
            "text-embedding-004": ModelInfo(
                name="text-embedding-004",
                context_length=2048,
                input_cost_per_token=0.0000125 / 1000,
                output_cost_per_token=0.0,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=False,
                description="Text embedding model",
            ),
        }

    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Convert OpenAI-style messages to Gemini format."""
        system_instruction = None
        contents = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        result = {"contents": contents}
        if system_instruction:
            result["system_instruction"] = {"parts": [{"text": system_instruction}]}

        return result

    async def _make_request(self, request) -> Any:
        """Make Google Gemini API request."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        # Prepare request data
        gemini_data = self._convert_messages_to_gemini_format(request.messages)

        # Add generation config
        generation_config = {}
        if request.max_tokens:
            generation_config["maxOutputTokens"] = request.max_tokens
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature

        if generation_config:
            gemini_data["generationConfig"] = generation_config

        # Add tools if provided
        if request.tools:
            gemini_data["tools"] = self._convert_tools_to_gemini_format(request.tools)

        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.api_base_url}/models/{request.model}:generateContent",
                    params={"key": api_key},
                    json=gemini_data,
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

    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style tools to Gemini format."""
        gemini_tools = []

        for tool in tools:
            if tool.get("type") == "function":
                function = tool.get("function", {})
                gemini_tools.append(
                    {
                        "function_declarations": [
                            {
                                "name": function.get("name"),
                                "description": function.get("description"),
                                "parameters": function.get("parameters", {}),
                            }
                        ]
                    }
                )

        return gemini_tools

    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """Calculate cost based on token usage."""
        model_info = self.models.get(usage.get("model", "gemini-1.5-flash"))
        if not model_info:
            return 0.0

        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)

        input_cost = input_tokens * model_info.input_cost_per_token
        output_cost = output_tokens * model_info.output_cost_per_token

        return input_cost + output_cost

    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from Gemini response."""
        usage_metadata = response.get("usageMetadata", {})

        return {
            "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
            "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
            "total_tokens": usage_metadata.get("totalTokenCount", 0),
            "model": response.get("modelVersion", "unknown"),
        }

    def _extract_response_text(self, response: Any) -> str:
        """Extract response text from Gemini response."""
        candidates = response.get("candidates", [])
        if not candidates:
            return ""

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if parts:
            return parts[0].get("text", "")

        return ""

    def _extract_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from Gemini response."""
        candidates = response.get("candidates", [])
        candidate = candidates[0] if candidates else {}

        return {
            "modelVersion": response.get("modelVersion"),
            "finishReason": candidate.get("finishReason"),
            "safetyRatings": candidate.get("safetyRatings", []),
            "citationMetadata": candidate.get("citationMetadata"),
            "tokenCount": response.get("usageMetadata", {}).get("totalTokenCount", 0),
            "candidateCount": len(candidates),
        }

    async def create_embedding(
        self, text: str, model: str = "text-embedding-004"
    ) -> Dict[str, Any]:
        """Create text embedding using Gemini."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        data = {"model": f"models/{model}", "content": {"parts": [{"text": text}]}}

        try:
            response = await self.client.post(
                f"{self.api_base_url}/models/{model}:embedContent",
                params={"key": api_key},
                json=data,
            )

            if response.status_code == 200:
                result = response.json()

                # Estimate token usage for embedding
                token_count = len(text.split()) * 1.3  # Rough estimate
                cost = self._calculate_cost(
                    {
                        "promptTokenCount": int(token_count),
                        "candidatesTokenCount": 0,
                        "totalTokenCount": int(token_count),
                        "model": model,
                    }
                )

                self.usage.add_usage(
                    ProviderUsage(
                        prompt_tokens=int(token_count),
                        total_tokens=int(token_count),
                        requests=1,
                        cost=cost,
                    )
                )

                return {
                    "embedding": result["embedding"]["values"],
                    "usage": {"prompt_tokens": int(token_count), "total_tokens": int(token_count)},
                    "cost": cost,
                }
            else:
                response.raise_for_status()

        except Exception as e:
            self.logger.error(f"Embedding creation failed: {e}")
            raise

    async def list_models(self) -> List[str]:
        """List available models from Google API."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        try:
            response = await self.client.get(f"{self.api_base_url}/models", params={"key": api_key})

            if response.status_code == 200:
                result = response.json()
                models = []
                for model in result.get("models", []):
                    model_name = model.get("name", "").replace("models/", "")
                    if model_name:
                        models.append(model_name)
                return models
            else:
                response.raise_for_status()

        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return list(self.models.keys())

    async def validate_api_key(self) -> bool:
        """Validate Google API key."""
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception:
            return False

    async def get_model_info_from_api(self, model: str) -> Optional[Dict[str, Any]]:
        """Get model information from Google API."""
        api_key = self.auth_service.get_api_key(self.provider_name)

        try:
            response = await self.client.get(
                f"{self.api_base_url}/models/{model}", params={"key": api_key}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Perform Google-specific health check."""
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
            "api_base_url": self.api_base_url,
        }

    async def shutdown(self):
        """Shutdown Google provider."""
        await super().shutdown()
        await self.client.aclose()

    def __str__(self) -> str:
        """String representation."""
        return f"GoogleProvider(requests={self.total_requests}, cost=${self.usage.cost:.4f})"
