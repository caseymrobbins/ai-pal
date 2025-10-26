"""
Anthropic Provider

Connects to Anthropic API (Claude models)
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Optional
from loguru import logger

from .base import BaseLLMProvider, LLMRequest, LLMResponse

# Try to import anthropic
try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic library not installed. Run: pip install anthropic")


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic API Provider

    Supports Claude 3 models (Opus, Sonnet, Haiku).
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Anthropic provider

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            logger.warning("No Anthropic API key provided. Set ANTHROPIC_API_KEY environment variable.")

        # Initialize client if library available
        self.client = None
        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = AsyncAnthropic(api_key=self.api_key)
                logger.info("Anthropic provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

    def is_available(self) -> bool:
        """Check if Anthropic provider is available"""
        return ANTHROPIC_AVAILABLE and self.client is not None

    async def generate(self, request: LLMRequest, model_name: str = "claude-3-haiku-20240307") -> LLMResponse:
        """
        Generate completion from Claude

        Args:
            request: LLM request
            model_name: Claude model name

        Returns:
            LLM response
        """
        if not self.is_available():
            raise RuntimeError("Anthropic provider not available")

        start_time = datetime.now()

        try:
            # Call Anthropic API
            logger.debug(f"Calling Anthropic {model_name} with {len(request.prompt)} chars")

            response = await self.client.messages.create(
                model=model_name,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                system=request.system_prompt if request.system_prompt else None,
                messages=[
                    {"role": "user", "content": request.prompt}
                ],
                stop_sequences=request.stop_sequences if request.stop_sequences else None,
            )

            # Extract response
            generated_text = response.content[0].text
            finish_reason = response.stop_reason or "end_turn"

            # Token usage
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens
            total_tokens = prompt_tokens + completion_tokens

            # Calculate cost
            cost = self._calculate_anthropic_cost(model_name, prompt_tokens, completion_tokens)

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"Anthropic {model_name} response: {completion_tokens} tokens, "
                f"${cost:.4f}, {latency_ms:.0f}ms"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                model_name=model_name,
                provider="anthropic",
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
            )

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise

    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str = "claude-3-haiku-20240307"
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Args:
            request: LLM request
            model_name: Claude model name

        Yields:
            Tokens as they're generated
        """
        if not self.is_available():
            raise RuntimeError("Anthropic provider not available")

        try:
            # Call Anthropic API with streaming
            async with self.client.messages.stream(
                model=model_name,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                system=request.system_prompt if request.system_prompt else None,
                messages=[
                    {"role": "user", "content": request.prompt}
                ],
                stop_sequences=request.stop_sequences if request.stop_sequences else None,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            raise

    def _calculate_anthropic_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for Anthropic models"""

        # Cost per 1K tokens (as of 2025)
        costs = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        }

        # Default to haiku if unknown
        cost_data = costs.get(model_name, costs["claude-3-haiku-20240307"])

        return self.calculate_cost(
            prompt_tokens,
            completion_tokens,
            cost_data["input"],
            cost_data["output"]
        )
