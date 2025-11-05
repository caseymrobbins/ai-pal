"""
Mistral AI Provider

Connects to Mistral AI API (Mistral Large, Medium, Small, etc.)
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Optional
from loguru import logger

from .base import BaseLLMProvider, LLMRequest, LLMResponse

# Try to import mistralai
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    logger.warning("mistralai library not installed. Run: pip install mistralai")


class MistralProvider(BaseLLMProvider):
    """
    Mistral AI API Provider

    Supports Mistral Large, Medium, Small and other Mistral models.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Mistral provider

        Args:
            api_key: Mistral API key (or set MISTRAL_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")

        if not self.api_key:
            logger.warning("No Mistral API key provided. Set MISTRAL_API_KEY environment variable.")

        # Initialize client if library available
        self.client = None
        if MISTRAL_AVAILABLE and self.api_key:
            try:
                self.client = Mistral(api_key=self.api_key)
                logger.info("Mistral provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Mistral client: {e}")

    def is_available(self) -> bool:
        """Check if Mistral provider is available"""
        return MISTRAL_AVAILABLE and self.client is not None

    async def generate(self, request: LLMRequest, model_name: str = "mistral-small-latest") -> LLMResponse:
        """
        Generate completion from Mistral AI

        Args:
            request: LLM request
            model_name: Mistral model name

        Returns:
            LLM response
        """
        if not self.is_available():
            raise RuntimeError("Mistral provider not available")

        start_time = datetime.now()

        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            # Add conversation history
            if request.conversation_history:
                for msg in request.conversation_history:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Add current prompt
            messages.append({"role": "user", "content": request.prompt})

            # Call Mistral API
            logger.debug(f"Calling Mistral {model_name} with {len(request.prompt)} chars")

            response = await self.client.chat.complete_async(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
            )

            # Extract response
            generated_text = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            # Token usage
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Calculate cost
            cost = self._calculate_mistral_cost(model_name, prompt_tokens, completion_tokens)

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"Mistral {model_name} response: {completion_tokens} tokens, "
                f"${cost:.4f}, {latency_ms:.0f}ms"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                model_name=model_name,
                provider="mistral",
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
            )

        except Exception as e:
            logger.error(f"Mistral generation failed: {e}")
            raise

    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str = "mistral-small-latest"
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Args:
            request: LLM request
            model_name: Mistral model name

        Yields:
            Tokens as they're generated
        """
        if not self.is_available():
            raise RuntimeError("Mistral provider not available")

        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            if request.conversation_history:
                for msg in request.conversation_history:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            messages.append({"role": "user", "content": request.prompt})

            # Call Mistral API with streaming
            stream = await self.client.chat.stream_async(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
            )

            # Yield tokens as they arrive
            async for chunk in stream:
                if chunk.data.choices[0].delta.content:
                    yield chunk.data.choices[0].delta.content

        except Exception as e:
            logger.error(f"Mistral streaming failed: {e}")
            raise

    def _calculate_mistral_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for Mistral models"""

        # Cost per 1M tokens (as of 2025)
        costs = {
            "mistral-large-latest": {"input": 4.0, "output": 12.0},
            "mistral-medium-latest": {"input": 2.7, "output": 8.1},
            "mistral-small-latest": {"input": 1.0, "output": 3.0},
            "open-mistral-7b": {"input": 0.25, "output": 0.25},
            "open-mixtral-8x7b": {"input": 0.7, "output": 0.7},
            "open-mixtral-8x22b": {"input": 2.0, "output": 6.0},
        }

        # Default to small if unknown
        cost_data = costs.get(model_name, costs["mistral-small-latest"])

        return self.calculate_cost(
            prompt_tokens,
            completion_tokens,
            cost_data["input"],
            cost_data["output"]
        )
