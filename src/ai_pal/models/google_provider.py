"""
Google Gemini Provider

Connects to Google Gemini API (Gemini Pro, Gemini Pro Vision, etc.)
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Optional
from loguru import logger

from .base import BaseLLMProvider, LLMRequest, LLMResponse

# Try to import google-generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai library not installed. Run: pip install google-generativeai")


class GoogleProvider(BaseLLMProvider):
    """
    Google Gemini API Provider

    Supports Gemini models (Gemini Pro, Gemini Pro Vision, etc.)
    """

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "gemini-pro": {"input": 0.0005, "output": 0.0015},  # $0.50/$1.50 per 1M tokens
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},  # $1.25/$5.00 per 1M tokens
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},  # Very cheap!
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Google Gemini provider

        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            logger.warning("No Google API key provided. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        # Initialize client if library available
        self.configured = False
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.configured = True
                logger.info("Google Gemini provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Gemini client: {e}")

    def is_available(self) -> bool:
        """Check if Google Gemini provider is available"""
        return GEMINI_AVAILABLE and self.configured

    async def generate(self, request: LLMRequest, model_name: str = "gemini-1.5-flash") -> LLMResponse:
        """
        Generate completion from Gemini

        Args:
            request: LLM request
            model_name: Gemini model name (gemini-pro, gemini-1.5-pro, gemini-1.5-flash)

        Returns:
            LLM response
        """
        if not self.is_available():
            raise RuntimeError("Google Gemini provider not available")

        start_time = datetime.now()

        try:
            # Initialize model
            logger.debug(f"Calling Google Gemini {model_name} with {len(request.prompt)} chars")

            model = genai.GenerativeModel(model_name)

            # Configure generation
            generation_config = genai.GenerationConfig(
                temperature=request.temperature,
                top_p=request.top_p,
                max_output_tokens=request.max_tokens,
                stop_sequences=request.stop_sequences if request.stop_sequences else None,
            )

            # Build prompt (Gemini doesn't have separate system prompt in simple API)
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            # Generate response
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            # Extract response
            generated_text = response.text
            finish_reason = "stop"  # Gemini uses different finish reasons

            # Estimate tokens (Gemini doesn't always return usage in free tier)
            # Use rough approximation: 1 token ≈ 4 chars
            prompt_tokens = len(full_prompt) // 4
            completion_tokens = len(generated_text) // 4

            # Try to get actual usage if available
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count

            total_tokens = prompt_tokens + completion_tokens

            # Calculate cost
            pricing = self.PRICING.get(model_name, {"input": 0.001, "output": 0.002})
            input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
            output_cost = (completion_tokens / 1_000_000) * pricing["output"]
            total_cost = input_cost + output_cost

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"Google Gemini {model_name} response: {completion_tokens} tokens, "
                f"${total_cost:.4f}, {latency_ms:.0f}ms"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=total_cost,
                model_name=model_name,
                provider="google",
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response={"finish_reason": finish_reason},
            )

        except Exception as e:
            logger.error(f"Google Gemini generation failed: {e}")
            raise

    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str = "gemini-1.5-flash"
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Args:
            request: LLM request
            model_name: Gemini model name

        Yields:
            Tokens as they're generated
        """
        if not self.is_available():
            raise RuntimeError("Google Gemini provider not available")

        try:
            # Initialize model
            model = genai.GenerativeModel(model_name)

            # Configure generation
            generation_config = genai.GenerationConfig(
                temperature=request.temperature,
                top_p=request.top_p,
                max_output_tokens=request.max_tokens,
            )

            # Build prompt
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            # Stream response
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config,
                stream=True
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Google Gemini streaming failed: {e}")
            raise


# Alias for backward compatibility
GeminiProvider = GoogleProvider
