"""
Cohere Provider

Connects to Cohere API (Command models)
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Optional
from loguru import logger

from .base import BaseLLMProvider, LLMRequest, LLMResponse

# Try to import cohere
try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    logger.warning("cohere library not installed. Run: pip install cohere")


class CohereProvider(BaseLLMProvider):
    """
    Cohere API Provider

    Supports Command R, Command R+, and other Cohere models.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Cohere provider

        Args:
            api_key: Cohere API key (or set COHERE_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("COHERE_API_KEY")

        if not self.api_key:
            logger.warning("No Cohere API key provided. Set COHERE_API_KEY environment variable.")

        # Initialize client if library available
        self.client = None
        if COHERE_AVAILABLE and self.api_key:
            try:
                self.client = cohere.AsyncClient(api_key=self.api_key)
                logger.info("Cohere provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Cohere client: {e}")

    def is_available(self) -> bool:
        """Check if Cohere provider is available"""
        return COHERE_AVAILABLE and self.client is not None

    async def generate(self, request: LLMRequest, model_name: str = "command-r") -> LLMResponse:
        """
        Generate completion from Cohere

        Args:
            request: LLM request
            model_name: Cohere model name

        Returns:
            LLM response
        """
        if not self.is_available():
            raise RuntimeError("Cohere provider not available")

        start_time = datetime.now()

        try:
            # Build chat history if present
            chat_history = []
            if request.conversation_history:
                for msg in request.conversation_history:
                    chat_history.append({
                        "role": "USER" if msg["role"] == "user" else "CHATBOT",
                        "message": msg["content"]
                    })

            # Call Cohere API
            logger.debug(f"Calling Cohere {model_name} with {len(request.prompt)} chars")

            response = await self.client.chat(
                model=model_name,
                message=request.prompt,
                chat_history=chat_history if chat_history else None,
                preamble=request.system_prompt if request.system_prompt else None,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                p=request.top_p,
            )

            # Extract response
            generated_text = response.text
            finish_reason = response.finish_reason if hasattr(response, 'finish_reason') else "COMPLETE"

            # Token usage (Cohere provides this in meta)
            prompt_tokens = response.meta.tokens.input_tokens if hasattr(response.meta, 'tokens') else 0
            completion_tokens = response.meta.tokens.output_tokens if hasattr(response.meta, 'tokens') else 0
            total_tokens = prompt_tokens + completion_tokens

            # Calculate cost
            cost = self._calculate_cohere_cost(model_name, prompt_tokens, completion_tokens)

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"Cohere {model_name} response: {completion_tokens} tokens, "
                f"${cost:.4f}, {latency_ms:.0f}ms"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                model_name=model_name,
                provider="cohere",
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response=response.__dict__ if hasattr(response, '__dict__') else None,
            )

        except Exception as e:
            logger.error(f"Cohere generation failed: {e}")
            raise

    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str = "command-r"
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Args:
            request: LLM request
            model_name: Cohere model name

        Yields:
            Tokens as they're generated
        """
        if not self.is_available():
            raise RuntimeError("Cohere provider not available")

        try:
            # Build chat history
            chat_history = []
            if request.conversation_history:
                for msg in request.conversation_history:
                    chat_history.append({
                        "role": "USER" if msg["role"] == "user" else "CHATBOT",
                        "message": msg["content"]
                    })

            # Call Cohere API with streaming
            stream = await self.client.chat_stream(
                model=model_name,
                message=request.prompt,
                chat_history=chat_history if chat_history else None,
                preamble=request.system_prompt if request.system_prompt else None,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                p=request.top_p,
            )

            # Yield tokens as they arrive
            async for event in stream:
                if event.event_type == "text-generation":
                    yield event.text

        except Exception as e:
            logger.error(f"Cohere streaming failed: {e}")
            raise

    def _calculate_cohere_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for Cohere models"""

        # Cost per 1M tokens (as of 2025)
        costs = {
            "command-r-plus": {"input": 3.0, "output": 15.0},
            "command-r": {"input": 0.5, "output": 1.5},
            "command": {"input": 1.0, "output": 2.0},
            "command-light": {"input": 0.3, "output": 0.6},
        }

        # Default to command-r if unknown
        cost_data = costs.get(model_name, costs["command-r"])

        return self.calculate_cost(
            prompt_tokens,
            completion_tokens,
            cost_data["input"],
            cost_data["output"]
        )
