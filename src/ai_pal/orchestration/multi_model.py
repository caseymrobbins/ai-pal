"""
Multi-Model Orchestration System

Intelligent model selection and routing:
- Dynamic model selection based on task requirements
- Cost optimization
- Latency optimization
- Quality vs. speed tradeoffs
- Model capability matching
- Fallback strategies
- Performance tracking

Part of Phase 3: Enhanced Context, Privacy, Multi-Model Orchestration
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from collections import defaultdict

from loguru import logger


class ModelProvider(Enum):
    """Model providers"""
    LOCAL = "local"  # Local SLM (Phi-2, Llama, etc.)
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"


class TaskComplexity(Enum):
    """Task complexity levels"""
    TRIVIAL = "trivial"  # Simple lookup, formatting
    SIMPLE = "simple"  # Basic Q&A, simple generation
    MODERATE = "moderate"  # Analysis, reasoning
    COMPLEX = "complex"  # Deep reasoning, long-form
    EXPERT = "expert"  # Specialized knowledge required


class OptimizationGoal(Enum):
    """Optimization goals"""
    COST = "cost"  # Minimize cost
    LATENCY = "latency"  # Minimize latency
    QUALITY = "quality"  # Maximize quality
    BALANCED = "balanced"  # Balance all factors
    PRIVACY = "privacy"  # Maximize privacy (prefer local)


@dataclass
class ModelCapabilities:
    """Model capabilities profile"""
    provider: ModelProvider
    model_name: str

    # Performance characteristics
    max_tokens: int
    supports_streaming: bool
    supports_functions: bool
    supports_vision: bool

    # Quality metrics
    reasoning_capability: float  # 0-1
    knowledge_breadth: float  # 0-1
    code_capability: float  # 0-1
    creative_capability: float  # 0-1

    # Cost (per 1K tokens)
    input_cost: float  # USD
    output_cost: float  # USD

    # Performance
    typical_latency_ms: int  # Milliseconds
    availability: float  # 0-1 (uptime)

    # Privacy
    data_retention_days: int
    trains_on_data: bool
    local_execution: bool


@dataclass
class TaskRequirements:
    """Requirements for a task"""
    task_type: str
    complexity: TaskComplexity

    # Requirements
    max_cost: Optional[float] = None  # USD
    max_latency_ms: Optional[int] = None
    min_quality: float = 0.7  # 0-1
    requires_streaming: bool = False
    requires_functions: bool = False
    requires_vision: bool = False

    # Privacy requirements
    sensitive_data: bool = False
    requires_local: bool = False

    # Context
    estimated_input_tokens: int = 100
    estimated_output_tokens: int = 200


@dataclass
class ModelSelection:
    """Model selection result"""
    provider: ModelProvider
    model_name: str
    confidence: float  # 0-1

    # Predicted metrics
    estimated_cost: float
    estimated_latency_ms: int
    expected_quality: float

    # Reasoning
    selection_reason: str
    optimization_goal: OptimizationGoal

    # Fallbacks
    fallback_models: List[Tuple[ModelProvider, str]] = field(default_factory=list)


@dataclass
class ModelPerformance:
    """Model performance tracking"""
    provider: ModelProvider
    model_name: str

    # Actual metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Performance
    average_latency_ms: float = 0.0
    average_cost: float = 0.0
    average_quality: float = 0.0  # User feedback

    # Recent history
    recent_latencies: List[float] = field(default_factory=list)
    recent_costs: List[float] = field(default_factory=list)
    recent_qualities: List[float] = field(default_factory=list)

    # Errors
    error_rate: float = 0.0
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None


class MultiModelOrchestrator:
    """
    Multi-Model Orchestration System

    Intelligently routes tasks to optimal models based on:
    - Task complexity and requirements
    - Cost constraints
    - Latency requirements
    - Quality expectations
    - Privacy needs
    - Model availability and performance
    """

    def __init__(
        self,
        storage_dir: Path,
        default_optimization_goal: OptimizationGoal = OptimizationGoal.BALANCED
    ):
        """
        Initialize Multi-Model Orchestrator

        Args:
            storage_dir: Directory for performance data
            default_optimization_goal: Default optimization strategy
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.default_optimization_goal = default_optimization_goal

        # Model catalog
        self.model_capabilities: Dict[Tuple[ModelProvider, str], ModelCapabilities] = {}
        self._initialize_model_catalog()

        # Performance tracking
        self.model_performance: Dict[Tuple[ModelProvider, str], ModelPerformance] = {}
        self._load_performance_data()

        logger.info(
            f"Multi-Model Orchestrator initialized with {len(self.model_capabilities)} models, "
            f"optimization: {default_optimization_goal.value}"
        )

    def _initialize_model_catalog(self) -> None:
        """Initialize catalog of available models"""

        # Local models (Phi-2, Llama, etc.)
        self.model_capabilities[(ModelProvider.LOCAL, "phi-2")] = ModelCapabilities(
            provider=ModelProvider.LOCAL,
            model_name="phi-2",
            max_tokens=2048,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=False,
            reasoning_capability=0.7,
            knowledge_breadth=0.6,
            code_capability=0.75,
            creative_capability=0.6,
            input_cost=0.0,  # Free (local)
            output_cost=0.0,
            typical_latency_ms=500,
            availability=0.99,
            data_retention_days=0,  # No external retention
            trains_on_data=False,
            local_execution=True
        )

        # OpenAI models
        self.model_capabilities[(ModelProvider.OPENAI, "gpt-4-turbo")] = ModelCapabilities(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4-turbo",
            max_tokens=128000,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            reasoning_capability=0.95,
            knowledge_breadth=0.95,
            code_capability=0.9,
            creative_capability=0.9,
            input_cost=0.01,  # $10 per 1M tokens
            output_cost=0.03,  # $30 per 1M tokens
            typical_latency_ms=2000,
            availability=0.995,
            data_retention_days=30,
            trains_on_data=False,
            local_execution=False
        )

        self.model_capabilities[(ModelProvider.OPENAI, "gpt-3.5-turbo")] = ModelCapabilities(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            max_tokens=16385,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=False,
            reasoning_capability=0.75,
            knowledge_breadth=0.8,
            code_capability=0.7,
            creative_capability=0.75,
            input_cost=0.0005,  # $0.50 per 1M tokens
            output_cost=0.0015,  # $1.50 per 1M tokens
            typical_latency_ms=1000,
            availability=0.998,
            data_retention_days=30,
            trains_on_data=False,
            local_execution=False
        )

        # Anthropic models
        self.model_capabilities[(ModelProvider.ANTHROPIC, "claude-3-opus")] = ModelCapabilities(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-opus",
            max_tokens=200000,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=True,
            reasoning_capability=0.98,
            knowledge_breadth=0.95,
            code_capability=0.92,
            creative_capability=0.95,
            input_cost=0.015,  # $15 per 1M tokens
            output_cost=0.075,  # $75 per 1M tokens
            typical_latency_ms=2500,
            availability=0.995,
            data_retention_days=0,  # Anthropic doesn't retain by default
            trains_on_data=False,
            local_execution=False
        )

        self.model_capabilities[(ModelProvider.ANTHROPIC, "claude-3-haiku")] = ModelCapabilities(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku",
            max_tokens=200000,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=True,
            reasoning_capability=0.8,
            knowledge_breadth=0.85,
            code_capability=0.75,
            creative_capability=0.8,
            input_cost=0.00025,  # $0.25 per 1M tokens
            output_cost=0.00125,  # $1.25 per 1M tokens
            typical_latency_ms=800,
            availability=0.998,
            data_retention_days=0,
            trains_on_data=False,
            local_execution=False
        )

    def _load_performance_data(self) -> None:
        """Load historical performance data"""
        performance_file = self.storage_dir / "model_performance.json"
        if not performance_file.exists():
            return

        try:
            with open(performance_file, 'r') as f:
                data = json.load(f)
                for key_str, perf_data in data.items():
                    provider_str, model_name = key_str.split(":")
                    key = (ModelProvider(provider_str), model_name)

                    self.model_performance[key] = ModelPerformance(
                        provider=ModelProvider(provider_str),
                        model_name=model_name,
                        total_requests=perf_data.get("total_requests", 0),
                        successful_requests=perf_data.get("successful_requests", 0),
                        failed_requests=perf_data.get("failed_requests", 0),
                        average_latency_ms=perf_data.get("average_latency_ms", 0.0),
                        average_cost=perf_data.get("average_cost", 0.0),
                        average_quality=perf_data.get("average_quality", 0.0),
                        recent_latencies=perf_data.get("recent_latencies", []),
                        recent_costs=perf_data.get("recent_costs", []),
                        recent_qualities=perf_data.get("recent_qualities", []),
                        error_rate=perf_data.get("error_rate", 0.0),
                        last_error=perf_data.get("last_error"),
                        last_error_at=datetime.fromisoformat(perf_data["last_error_at"])
                        if perf_data.get("last_error_at") else None
                    )
        except Exception as e:
            logger.error(f"Failed to load performance data: {e}")

    async def select_model(
        self,
        requirements: TaskRequirements,
        optimization_goal: Optional[OptimizationGoal] = None
    ) -> ModelSelection:
        """
        Select optimal model for task

        Args:
            requirements: Task requirements
            optimization_goal: Optimization strategy (uses default if None)

        Returns:
            Model selection with reasoning
        """
        goal = optimization_goal or self.default_optimization_goal

        # Filter models by requirements
        candidate_models = self._filter_by_requirements(requirements)

        if not candidate_models:
            logger.warning("No models match requirements, using fallback")
            # Fallback to local model
            return ModelSelection(
                provider=ModelProvider.LOCAL,
                model_name="phi-2",
                confidence=0.5,
                estimated_cost=0.0,
                estimated_latency_ms=500,
                expected_quality=0.7,
                selection_reason="Fallback: no models matched requirements",
                optimization_goal=goal
            )

        # Score models based on optimization goal
        scored_models = []
        for key, capabilities in candidate_models.items():
            score = await self._score_model(
                capabilities,
                requirements,
                goal
            )
            scored_models.append((key, capabilities, score))

        # Sort by score
        scored_models.sort(key=lambda x: x[2], reverse=True)

        # Select top model
        best_key, best_capabilities, best_score = scored_models[0]

        # Calculate estimates
        estimated_cost = self._estimate_cost(
            best_capabilities,
            requirements.estimated_input_tokens,
            requirements.estimated_output_tokens
        )

        estimated_latency = best_capabilities.typical_latency_ms

        # Adjust based on actual performance
        if best_key in self.model_performance:
            perf = self.model_performance[best_key]
            if perf.average_latency_ms > 0:
                estimated_latency = int(perf.average_latency_ms)

        # Determine quality
        expected_quality = self._estimate_quality(best_capabilities, requirements)

        # Generate reasoning
        reason = self._generate_selection_reason(
            best_capabilities,
            requirements,
            goal,
            best_score
        )

        # Determine fallbacks
        fallback_models = [
            (key[0], key[1])
            for key, _, score in scored_models[1:4]  # Top 3 alternatives
            if score > 0.5
        ]

        selection = ModelSelection(
            provider=best_key[0],
            model_name=best_key[1],
            confidence=best_score,
            estimated_cost=estimated_cost,
            estimated_latency_ms=estimated_latency,
            expected_quality=expected_quality,
            selection_reason=reason,
            optimization_goal=goal,
            fallback_models=fallback_models
        )

        logger.info(
            f"Selected {best_capabilities.model_name} "
            f"(score: {best_score:.2f}, cost: ${estimated_cost:.4f}, "
            f"latency: {estimated_latency}ms)"
        )

        return selection

    def _filter_by_requirements(
        self,
        requirements: TaskRequirements
    ) -> Dict[Tuple[ModelProvider, str], ModelCapabilities]:
        """Filter models by hard requirements"""
        filtered = {}

        for key, capabilities in self.model_capabilities.items():
            # Check hard requirements
            if requirements.requires_streaming and not capabilities.supports_streaming:
                continue

            if requirements.requires_functions and not capabilities.supports_functions:
                continue

            if requirements.requires_vision and not capabilities.supports_vision:
                continue

            if requirements.requires_local and not capabilities.local_execution:
                continue

            # Check token limits
            total_tokens = requirements.estimated_input_tokens + requirements.estimated_output_tokens
            if total_tokens > capabilities.max_tokens:
                continue

            # Check cost constraint
            if requirements.max_cost:
                estimated_cost = self._estimate_cost(
                    capabilities,
                    requirements.estimated_input_tokens,
                    requirements.estimated_output_tokens
                )
                if estimated_cost > requirements.max_cost:
                    continue

            # Check latency constraint
            if requirements.max_latency_ms:
                if capabilities.typical_latency_ms > requirements.max_latency_ms:
                    continue

            # Passed all filters
            filtered[key] = capabilities

        return filtered

    async def _score_model(
        self,
        capabilities: ModelCapabilities,
        requirements: TaskRequirements,
        goal: OptimizationGoal
    ) -> float:
        """
        Score model based on optimization goal

        Returns:
            Score 0-1 (higher is better)
        """
        if goal == OptimizationGoal.COST:
            # Prefer cheaper models
            estimated_cost = self._estimate_cost(
                capabilities,
                requirements.estimated_input_tokens,
                requirements.estimated_output_tokens
            )

            # Local is free, score 1.0
            if estimated_cost == 0:
                cost_score = 1.0
            else:
                # Normalize by typical API costs
                cost_score = max(0, 1.0 - (estimated_cost / 0.1))  # $0.10 as reference

            return cost_score

        elif goal == OptimizationGoal.LATENCY:
            # Prefer faster models
            latency_score = max(0, 1.0 - (capabilities.typical_latency_ms / 5000))
            return latency_score

        elif goal == OptimizationGoal.QUALITY:
            # Prefer higher quality models
            quality_score = self._estimate_quality(capabilities, requirements)
            return quality_score

        elif goal == OptimizationGoal.PRIVACY:
            # Prefer local models
            if capabilities.local_execution:
                return 1.0
            elif capabilities.data_retention_days == 0:
                return 0.8
            elif not capabilities.trains_on_data:
                return 0.6
            else:
                return 0.3

        else:  # BALANCED
            # Balance all factors
            cost = self._estimate_cost(
                capabilities,
                requirements.estimated_input_tokens,
                requirements.estimated_output_tokens
            )
            cost_score = 1.0 if cost == 0 else max(0, 1.0 - (cost / 0.1))

            latency_score = max(0, 1.0 - (capabilities.typical_latency_ms / 5000))

            quality_score = self._estimate_quality(capabilities, requirements)

            privacy_score = 1.0 if capabilities.local_execution else 0.5

            # Weighted average
            balanced_score = (
                cost_score * 0.3 +
                latency_score * 0.2 +
                quality_score * 0.4 +
                privacy_score * 0.1
            )

            return balanced_score

    def _estimate_cost(
        self,
        capabilities: ModelCapabilities,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost in USD"""
        input_cost = (input_tokens / 1000) * capabilities.input_cost
        output_cost = (output_tokens / 1000) * capabilities.output_cost
        return input_cost + output_cost

    def _estimate_quality(
        self,
        capabilities: ModelCapabilities,
        requirements: TaskRequirements
    ) -> float:
        """
        Estimate quality match for requirements

        Returns:
            Quality score 0-1
        """
        # Match capabilities to complexity
        if requirements.complexity == TaskComplexity.TRIVIAL:
            # Any model is fine
            return 1.0

        elif requirements.complexity == TaskComplexity.SIMPLE:
            # Basic capabilities needed
            return max(capabilities.reasoning_capability, capabilities.knowledge_breadth)

        elif requirements.complexity == TaskComplexity.MODERATE:
            # Good reasoning needed
            return (capabilities.reasoning_capability * 0.6 +
                    capabilities.knowledge_breadth * 0.4)

        elif requirements.complexity == TaskComplexity.COMPLEX:
            # Strong reasoning required
            return (capabilities.reasoning_capability * 0.8 +
                    capabilities.knowledge_breadth * 0.2)

        else:  # EXPERT
            # Highest capabilities required
            return min(capabilities.reasoning_capability, capabilities.knowledge_breadth)

    def _generate_selection_reason(
        self,
        capabilities: ModelCapabilities,
        requirements: TaskRequirements,
        goal: OptimizationGoal,
        score: float
    ) -> str:
        """Generate human-readable selection reasoning"""
        reasons = []

        if goal == OptimizationGoal.COST:
            reasons.append(f"Cost-optimized selection")
            if capabilities.local_execution:
                reasons.append("Free local execution")

        elif goal == OptimizationGoal.LATENCY:
            reasons.append(f"Latency-optimized selection ({capabilities.typical_latency_ms}ms typical)")

        elif goal == OptimizationGoal.QUALITY:
            reasons.append(f"Quality-optimized selection (reasoning: {capabilities.reasoning_capability:.2f})")

        elif goal == OptimizationGoal.PRIVACY:
            reasons.append("Privacy-optimized selection")
            if capabilities.local_execution:
                reasons.append("Local execution, no data transmission")

        # Add complexity match
        reasons.append(f"{requirements.complexity.value} task complexity")

        # Add confidence
        reasons.append(f"Selection confidence: {score:.2f}")

        return " | ".join(reasons)

    async def record_performance(
        self,
        provider: ModelProvider,
        model_name: str,
        latency_ms: float,
        cost: float,
        success: bool,
        quality_score: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Record actual model performance

        Args:
            provider: Model provider
            model_name: Model name
            latency_ms: Actual latency
            cost: Actual cost
            success: Whether request succeeded
            quality_score: Optional quality feedback
            error: Optional error message
        """
        key = (provider, model_name)

        # Get or create performance record
        if key not in self.model_performance:
            self.model_performance[key] = ModelPerformance(
                provider=provider,
                model_name=model_name
            )

        perf = self.model_performance[key]

        # Update counters
        perf.total_requests += 1
        if success:
            perf.successful_requests += 1
        else:
            perf.failed_requests += 1
            perf.last_error = error
            perf.last_error_at = datetime.now()

        # Update metrics
        perf.recent_latencies.append(latency_ms)
        perf.recent_costs.append(cost)

        # Keep recent history limited
        if len(perf.recent_latencies) > 100:
            perf.recent_latencies = perf.recent_latencies[-100:]
        if len(perf.recent_costs) > 100:
            perf.recent_costs = perf.recent_costs[-100:]

        # Update averages
        perf.average_latency_ms = sum(perf.recent_latencies) / len(perf.recent_latencies)
        perf.average_cost = sum(perf.recent_costs) / len(perf.recent_costs)

        if quality_score is not None:
            perf.recent_qualities.append(quality_score)
            if len(perf.recent_qualities) > 100:
                perf.recent_qualities = perf.recent_qualities[-100:]
            perf.average_quality = sum(perf.recent_qualities) / len(perf.recent_qualities)

        # Update error rate
        perf.error_rate = perf.failed_requests / perf.total_requests

        # Persist
        await self._persist_performance_data()

        logger.debug(
            f"Recorded performance for {model_name}: "
            f"latency={latency_ms:.0f}ms, cost=${cost:.4f}, success={success}"
        )

    async def _persist_performance_data(self) -> None:
        """Persist performance data to disk"""
        performance_file = self.storage_dir / "model_performance.json"

        data = {}
        for (provider, model_name), perf in self.model_performance.items():
            key_str = f"{provider.value}:{model_name}"
            data[key_str] = {
                "total_requests": perf.total_requests,
                "successful_requests": perf.successful_requests,
                "failed_requests": perf.failed_requests,
                "average_latency_ms": perf.average_latency_ms,
                "average_cost": perf.average_cost,
                "average_quality": perf.average_quality,
                "recent_latencies": perf.recent_latencies,
                "recent_costs": perf.recent_costs,
                "recent_qualities": perf.recent_qualities,
                "error_rate": perf.error_rate,
                "last_error": perf.last_error,
                "last_error_at": perf.last_error_at.isoformat()
                if perf.last_error_at else None
            }

        try:
            with open(performance_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist performance data: {e}")

    def get_performance_report(self) -> Dict:
        """Get performance report for all models"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "models": {}
        }

        for (provider, model_name), perf in self.model_performance.items():
            key = f"{provider.value}:{model_name}"
            report["models"][key] = {
                "total_requests": perf.total_requests,
                "success_rate": perf.successful_requests / perf.total_requests
                if perf.total_requests > 0 else 0.0,
                "average_latency_ms": perf.average_latency_ms,
                "average_cost": perf.average_cost,
                "average_quality": perf.average_quality,
                "error_rate": perf.error_rate
            }

        return report
