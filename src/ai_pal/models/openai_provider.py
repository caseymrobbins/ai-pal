"""
OpenAI Provider

Connects to OpenAI API (GPT-4, GPT-3.5, etc.)
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Optional
from loguru import logger

from .base import BaseLLMProvider, LLMRequest, LLMResponse

# Try to import openai
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai library not installed. Run: pip install openai")


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API Provider

    Supports GPT-4, GPT-3.5-Turbo, and other OpenAI models.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI provider

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")

        # Initialize client if library available
        self.client = None
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = AsyncOpenAI(api_key=self.api_key)
                logger.info("OpenAI provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        return OPENAI_AVAILABLE and self.client is not None

    async def generate(self, request: LLMRequest, model_name: str = "gpt-3.5-turbo") -> LLMResponse:
        """
        Generate completion from OpenAI

        Args:
            request: LLM request
            model_name: OpenAI model name

        Returns:
            LLM response
        """
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available")

        start_time = datetime.now()

        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            # Call OpenAI API
            logger.debug(f"Calling OpenAI {model_name} with {len(request.prompt)} chars")

            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop_sequences if request.stop_sequences else None,
            )

            # Extract response
            generated_text = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            # Token usage
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Calculate cost (approximate)
            cost = self._calculate_openai_cost(model_name, prompt_tokens, completion_tokens)

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"OpenAI {model_name} response: {completion_tokens} tokens, "
                f"${cost:.4f}, {latency_ms:.0f}ms"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                model_name=model_name,
                provider="openai",
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str = "gpt-3.5-turbo"
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Args:
            request: LLM request
            model_name: OpenAI model name

        Yields:
            Tokens as they're generated
        """
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available")

        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            # Call OpenAI API with streaming
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop_sequences if request.stop_sequences else None,
                stream=True,
            )

            # Yield tokens as they arrive
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise

    def _calculate_openai_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for OpenAI models"""

        # Cost per 1K tokens (as of 2025)
        costs = {
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
        }

        # Default to gpt-3.5-turbo if unknown
        cost_data = costs.get(model_name, costs["gpt-3.5-turbo"])

        return self.calculate_cost(
            prompt_tokens,
            completion_tokens,
            cost_data["input"],
            cost_data["output"]
        )
