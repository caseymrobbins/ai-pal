"""
Groq Provider

Connects to Groq API for ultra-fast LLM inference.
Supports Llama, Mixtral, and other open-source models.
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Optional
from loguru import logger

from .base import BaseLLMProvider, LLMRequest, LLMResponse

# Try to import groq
try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("groq library not installed. Run: pip install groq")


class GroqProvider(BaseLLMProvider):
    """
    Groq API Provider

    Ultra-fast inference for Llama, Mixtral, and other models.
    Known for extremely low latency (~50-200ms).
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Groq provider

        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            logger.warning("No Groq API key provided. Set GROQ_API_KEY environment variable.")

        # Initialize client if library available
        self.client = None
        if GROQ_AVAILABLE and self.api_key:
            try:
                self.client = AsyncGroq(api_key=self.api_key)
                logger.info("Groq provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")

    def is_available(self) -> bool:
        """Check if Groq provider is available"""
        return GROQ_AVAILABLE and self.client is not None

    async def generate(self, request: LLMRequest, model_name: str = "llama-3.1-8b-instant") -> LLMResponse:
        """
        Generate completion from Groq

        Args:
            request: LLM request
            model_name: Groq model name

        Returns:
            LLM response
        """
        if not self.is_available():
            raise RuntimeError("Groq provider not available")

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

            # Call Groq API
            logger.debug(f"Calling Groq {model_name} with {len(request.prompt)} chars")

            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
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

            # Calculate cost (Groq has free tier with rate limits)
            cost = self._calculate_groq_cost(model_name, prompt_tokens, completion_tokens)

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"Groq {model_name} response: {completion_tokens} tokens, "
                f"${cost:.4f}, {latency_ms:.0f}ms ⚡"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                model_name=model_name,
                provider="groq",
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
            )

        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise

    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str = "llama-3.1-8b-instant"
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Args:
            request: LLM request
            model_name: Groq model name

        Yields:
            Tokens as they're generated
        """
        if not self.is_available():
            raise RuntimeError("Groq provider not available")

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

            # Call Groq API with streaming
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop=request.stop_sequences if request.stop_sequences else None,
                stream=True,
            )

            # Yield tokens as they arrive
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise

    def _calculate_groq_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for Groq models
        
        Note: Groq has a free tier with rate limits.
        Paid tier pricing is very competitive.
        """

        # Cost per 1M tokens (as of 2025)
        # Note: Groq often has free tier, so costs may be $0 for many users
        costs = {
            "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
            "llama-3.1-8b-instant": {"input": 0.05, "output": 0.10},
            "llama3-70b-8192": {"input": 0.59, "output": 0.79},
            "llama3-8b-8192": {"input": 0.05, "output": 0.10},
            "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
            "gemma-7b-it": {"input": 0.07, "output": 0.07},
        }

        # Default to llama-3.1-8b-instant if unknown
        cost_data = costs.get(model_name, costs["llama-3.1-8b-instant"])

        return self.calculate_cost(
            prompt_tokens,
            completion_tokens,
            cost_data["input"],
            cost_data["output"]
        )
