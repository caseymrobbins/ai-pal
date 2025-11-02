"""
LLM Router

Routes requests to the appropriate LLM provider based on:
- Task complexity
- Provider availability
- User preferences (local vs. cloud)
"""

from enum import Enum
from typing import Optional, Dict, Any
from loguru import logger

from .base import LLMRequest, LLMResponse
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .local import LocalLLMProvider


class TaskComplexity(Enum):
    """Task complexity levels for routing decisions"""
    SIMPLE = "simple"          # Quick, straightforward tasks
    MODERATE = "moderate"      # Standard tasks
    COMPLEX = "complex"        # Multi-step reasoning
    CRITICAL = "critical"      # High-stakes decisions


class LLMRouter:
    """
    Intelligent LLM Router

    Routes requests to the most appropriate provider based on:
    - Task complexity
    - Provider availability
    - Cost optimization
    - User preferences
    """

    def __init__(self):
        """Initialize router with all providers"""
        logger.info("Initializing LLM Router...")

        # Initialize providers
        self.openai_provider = OpenAIProvider()
        self.anthropic_provider = AnthropicProvider()
        self.local_provider = LocalLLMProvider()

        # Track provider availability
        self._provider_health: Dict[str, bool] = {}

        logger.info("LLM Router initialized")

    async def generate(
        self,
        request: LLMRequest,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        prefer_local: bool = True
    ) -> LLMResponse:
        """
        Generate response using the most appropriate provider

        Args:
            request: LLM request
            complexity: Task complexity level
            prefer_local: Prefer local models when possible

        Returns:
            LLM response
        """
        logger.info(f"Routing {complexity.value} task (prefer_local={prefer_local})")

        # Determine best provider for this task
        provider, model = self._select_provider(complexity, prefer_local)

        if not provider:
            raise RuntimeError(
                "No LLM providers available. Please configure at least one provider "
                "(OpenAI, Anthropic, or Local)."
            )

        logger.info(f"Selected provider: {provider.__class__.__name__}, model: {model}")

        # Generate response
        try:
            response = await provider.generate(request, model)
            return response
        except Exception as e:
            logger.error(f"Generation failed with primary provider: {e}")

            # Try fallback provider
            fallback_provider, fallback_model = self._get_fallback_provider(
                provider, complexity
            )

            if fallback_provider:
                logger.info(f"Trying fallback: {fallback_provider.__class__.__name__}")
                try:
                    response = await fallback_provider.generate(request, fallback_model)
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")

            # Re-raise original error if no fallback worked
            raise

    def _select_provider(
        self,
        complexity: TaskComplexity,
        prefer_local: bool
    ) -> tuple[Optional[Any], str]:
        """
        Select the best provider for a task

        Args:
            complexity: Task complexity
            prefer_local: Prefer local models

        Returns:
            Tuple of (provider, model_name)
        """
        # For CRITICAL tasks, always use most capable cloud model
        if complexity == TaskComplexity.CRITICAL:
            if self.anthropic_provider.is_available():
                return self.anthropic_provider, "claude-3-opus-20240229"
            elif self.openai_provider.is_available():
                return self.openai_provider, "gpt-4-turbo"

        # For COMPLEX tasks, prefer powerful models
        if complexity == TaskComplexity.COMPLEX:
            if prefer_local and self.local_provider.is_available():
                # Use local for complex tasks if user prefers
                return self.local_provider, "mistral"
            elif self.anthropic_provider.is_available():
                return self.anthropic_provider, "claude-3-sonnet-20240229"
            elif self.openai_provider.is_available():
                return self.openai_provider, "gpt-4-turbo"

        # For SIMPLE and MODERATE tasks, optimize for cost/speed
        if complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
            if prefer_local and self.local_provider.is_available():
                return self.local_provider, "phi-2"
            elif self.anthropic_provider.is_available():
                return self.anthropic_provider, "claude-3-haiku-20240307"
            elif self.openai_provider.is_available():
                return self.openai_provider, "gpt-3.5-turbo"

        # Fallback: try any available provider
        if self.local_provider.is_available():
            return self.local_provider, "phi-2"
        elif self.anthropic_provider.is_available():
            return self.anthropic_provider, "claude-3-haiku-20240307"
        elif self.openai_provider.is_available():
            return self.openai_provider, "gpt-3.5-turbo"

        return None, ""

    def _get_fallback_provider(
        self,
        failed_provider: Any,
        complexity: TaskComplexity
    ) -> tuple[Optional[Any], str]:
        """
        Get a fallback provider if primary fails

        Args:
            failed_provider: Provider that failed
            complexity: Task complexity

        Returns:
            Tuple of (fallback_provider, model_name)
        """
        # Try other available providers
        providers = [
            (self.anthropic_provider, "claude-3-haiku-20240307"),
            (self.openai_provider, "gpt-3.5-turbo"),
            (self.local_provider, "phi-2"),
        ]

        for provider, model in providers:
            if provider != failed_provider and provider.is_available():
                return provider, model

        return None, ""

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Check health of all providers

        Returns:
            Health status for each provider
        """
        health = {}

        # Check OpenAI
        health["openai"] = {
            "available": self.openai_provider.is_available(),
            "provider": "OpenAI",
        }

        # Check Anthropic
        health["anthropic"] = {
            "available": self.anthropic_provider.is_available(),
            "provider": "Anthropic",
        }

        # Check Local
        health["local"] = {
            "available": self.local_provider.is_available(),
            "provider": "Local LLM",
        }

        return health
