"""
Local LLM Provider

Connects to locally-running LLMs (Ollama, llama.cpp, etc.)
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Optional
from loguru import logger

from .base import BaseLLMProvider, LLMRequest, LLMResponse

# Try to import httpx for API calls
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not installed. Run: pip install httpx")


class LocalLLMProvider(BaseLLMProvider):
    """
    Local LLM Provider

    Supports locally-running models via Ollama API or compatible endpoints.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        """
        Initialize Local LLM provider

        Args:
            api_key: Not used for local models
            base_url: Base URL for local API (default: Ollama default)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        self.base_url = base_url or os.getenv("LOCAL_LLM_URL", "http://localhost:11434")

        logger.info(f"Local LLM provider initialized with base_url: {self.base_url}")

    def is_available(self) -> bool:
        """Check if local LLM provider is available"""
        # For now, assume it's available if httpx is installed
        # Could add a health check ping here
        return HTTPX_AVAILABLE

    async def generate(self, request: LLMRequest, model_name: str = "phi-2") -> LLMResponse:
        """
        Generate completion from local LLM

        Args:
            request: LLM request
            model_name: Local model name

        Returns:
            LLM response
        """
        if not self.is_available():
            raise RuntimeError("Local LLM provider not available (httpx not installed)")

        start_time = datetime.now()

        try:
            # Build prompt with system message if present
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\nUser: {request.prompt}\n\nAssistant:"

            # Call local API (Ollama format)
            logger.debug(f"Calling local {model_name} with {len(full_prompt)} chars")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": request.temperature,
                            "top_p": request.top_p,
                            "num_predict": request.max_tokens,
                        }
                    }
                )

                response.raise_for_status()
                data = response.json()

            # Extract response
            generated_text = data.get("response", "")

            # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
            prompt_tokens = len(full_prompt) // 4
            completion_tokens = len(generated_text) // 4
            total_tokens = prompt_tokens + completion_tokens

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"Local {model_name} response: ~{completion_tokens} tokens, "
                f"{latency_ms:.0f}ms"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=0.0,  # Local models are free
                model_name=model_name,
                provider="local",
                latency_ms=latency_ms,
                finish_reason="complete",
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response=data,
            )

        except httpx.HTTPError as e:
            logger.error(f"Local LLM generation failed (HTTP error): {e}")
            logger.warning("Make sure Ollama is running: ollama serve")
            raise
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            raise

    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str = "phi-2"
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Args:
            request: LLM request
            model_name: Local model name

        Yields:
            Tokens as they're generated
        """
        if not self.is_available():
            raise RuntimeError("Local LLM provider not available")

        try:
            # Build prompt
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\nUser: {request.prompt}\n\nAssistant:"

            # Call local API with streaming
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": full_prompt,
                        "stream": True,
                        "options": {
                            "temperature": request.temperature,
                            "top_p": request.top_p,
                            "num_predict": request.max_tokens,
                        }
                    }
                ) as response:
                    response.raise_for_status()

                    # Parse NDJSON stream
                    async for line in response.aiter_lines():
                        if line.strip():
                            import json
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]

        except Exception as e:
            logger.error(f"Local LLM streaming failed: {e}")
            raise
