"""
LLM Router - Task-based model selection

Routes tasks to appropriate LLM providers based on complexity,
requirements, and availability.

Note: This is a compatibility stub. The main routing logic is now
in orchestration.multi_model.MultiModelOrchestrator.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from loguru import logger


class TaskComplexity(Enum):
    """Task complexity levels for routing decisions"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class RoutingDecision:
    """Decision about which model to use"""
    provider: str
    model_name: str
    reasoning: str
    estimated_cost: float
    estimated_latency_ms: float


class LLMRouter:
    """
    Routes tasks to appropriate LLM providers

    This is a compatibility stub for older code.
    New code should use MultiModelOrchestrator from orchestration.multi_model.
    """

    def __init__(self):
        """Initialize router"""
        logger.warning(
            "LLMRouter is deprecated. Use MultiModelOrchestrator instead."
        )
        self.provider_preferences = {
            TaskComplexity.SIMPLE: "local",
            TaskComplexity.MODERATE: "anthropic",
            TaskComplexity.COMPLEX: "anthropic",
            TaskComplexity.EXPERT: "anthropic",
        }
        # Compatibility: Old orchestrator expects these attributes
        self.local_provider = None
        self.anthropic_provider = None
        self.openai_provider = None

    def route(
        self,
        task: str,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        Route a task to appropriate provider

        Args:
            task: Task description
            complexity: Task complexity level
            context: Additional context

        Returns:
            RoutingDecision with provider/model selection
        """
        provider = self.provider_preferences.get(complexity, "anthropic")

        # Simple routing logic
        if provider == "local":
            model = "phi-2"
        elif provider == "anthropic":
            model = "claude-3-haiku-20240307"
        else:
            model = "gpt-3.5-turbo"

        return RoutingDecision(
            provider=provider,
            model_name=model,
            reasoning=f"Task complexity: {complexity.value}",
            estimated_cost=0.0,
            estimated_latency_ms=1000.0,
        )

    async def route_async(
        self,
        task: str,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """Async version of route"""
        return self.route(task, complexity, context)
