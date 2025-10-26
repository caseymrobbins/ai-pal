"""
Base classes for LLM providers

Defines common interface and data structures for all LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime


@dataclass
class LLMRequest:
    """
    Request to an LLM

    Unified request format for all providers.
    """
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    stop_sequences: List[str] = field(default_factory=list)

    # Optional metadata
    user_id: Optional[str] = None
    request_id: Optional[str] = None

    # Provider-specific options
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """
    Response from an LLM

    Unified response format for all providers.
    """
    generated_text: str

    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Cost tracking
    cost_usd: float = 0.0

    # Metadata
    model_name: str = ""
    provider: str = ""
    latency_ms: float = 0.0
    finish_reason: str = "complete"

    # Timestamps
    requested_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Raw response (for debugging)
    raw_response: Optional[Dict[str, Any]] = None

    @property
    def tokens_used(self) -> int:
        """Total tokens used (convenience property)"""
        return self.total_tokens or (self.prompt_tokens + self.completion_tokens)


class BaseLLMProvider(ABC):
    """
    Base class for LLM providers

    All providers must implement this interface.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize provider

        Args:
            api_key: API key for provider (if required)
            **kwargs: Provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def generate(self, request: LLMRequest, model_name: str) -> LLMResponse:
        """
        Generate completion from LLM

        Args:
            request: LLM request
            model_name: Model to use

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Args:
            request: LLM request
            model_name: Model to use

        Yields:
            Tokens as they're generated
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available

        Returns:
            True if provider can be used
        """
        pass

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        input_cost_per_1k: float,
        output_cost_per_1k: float
    ) -> float:
        """
        Calculate cost in USD

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            input_cost_per_1k: Cost per 1K input tokens
            output_cost_per_1k: Cost per 1K output tokens

        Returns:
            Total cost in USD
        """
        input_cost = (prompt_tokens / 1000.0) * input_cost_per_1k
        output_cost = (completion_tokens / 1000.0) * output_cost_per_1k
        return input_cost + output_cost
