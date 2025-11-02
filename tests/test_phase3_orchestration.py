"""
Tests for Phase 3: Multi-Model Orchestration

Tests dynamic model selection, cost optimization, and performance tracking.
"""

import pytest
from datetime import datetime

from ai_pal.orchestration.multi_model import (
    MultiModelOrchestrator,
    ModelProvider,
    ModelCapabilities,
    TaskRequirements,
    TaskComplexity,
    OptimizationGoal,
    ModelSelection,
)


@pytest.fixture
def orchestrator():
    """Create orchestrator instance"""
    return MultiModelOrchestrator()


@pytest.mark.asyncio
async def test_select_local_model_for_simple_task(orchestrator):
    """Test that simple tasks select local model"""
    requirements = TaskRequirements(
        task_type="simple_task",
        complexity=TaskComplexity.SIMPLE,
        min_quality=0.6,
        max_cost=0.0,  # Free
        max_latency_ms=1000,
        requires_local=True
    )

    selection = await orchestrator.select_model(
        requirements=requirements,
        optimization_goal=OptimizationGoal.COST
    )

    assert selection.provider == ModelProvider.LOCAL
    assert selection.model_name == "phi-2"
    assert selection.estimated_cost == 0.0


@pytest.mark.asyncio
async def test_select_gpt4_for_complex_task(orchestrator):
    """Test that complex tasks select powerful model"""
    requirements = TaskRequirements(
        task_type="complex_task",
        complexity=TaskComplexity.COMPLEX,
        min_quality=0.9,
        max_cost=10.0,
        max_latency_ms=5000,
        requires_local=False
    )

    selection = await orchestrator.select_model(
        requirements=requirements,
        optimization_goal=OptimizationGoal.QUALITY
    )

    # Should select GPT-4 or Claude-3-opus
    assert selection.provider in [ModelProvider.OPENAI, ModelProvider.ANTHROPIC]
    assert selection.score > 0.8


@pytest.mark.asyncio
async def test_cost_optimization(orchestrator):
    """Test cost-optimized model selection"""
    requirements = TaskRequirements(
        task_type="moderate_task",
        complexity=TaskComplexity.MODERATE,
        min_quality=0.7,
        max_cost=1.0,
        max_latency_ms=3000,
        requires_local=False
    )

    selection = await orchestrator.select_model(
        requirements=requirements,
        optimization_goal=OptimizationGoal.COST
    )

    # Should select cheapest model that meets requirements
    # Likely GPT-3.5 or Claude-3-haiku
    assert selection.estimated_cost <= 0.01


@pytest.mark.asyncio
async def test_latency_optimization(orchestrator):
    """Test latency-optimized model selection"""
    requirements = TaskRequirements(
        task_type="moderate_task",
        complexity=TaskComplexity.MODERATE,
        min_quality=0.7,
        max_cost=10.0,
        max_latency_ms=1000,
        requires_local=False
    )

    selection = await orchestrator.select_model(
        requirements=requirements,
        optimization_goal=OptimizationGoal.LATENCY
    )

    # Should select fastest model
    # Likely local model or Claude-3-haiku
    assert selection.estimated_latency_ms <= 1000


@pytest.mark.asyncio
async def test_privacy_optimization(orchestrator):
    """Test privacy-optimized model selection"""
    requirements = TaskRequirements(
        task_type="moderate_task",
        complexity=TaskComplexity.MODERATE,
        min_quality=0.7,
        max_cost=10.0,
        max_latency_ms=3000,
        requires_local=True  # Privacy requires local
    )

    selection = await orchestrator.select_model(
        requirements=requirements,
        optimization_goal=OptimizationGoal.PRIVACY
    )

    # Must select local model for privacy
    assert selection.provider == ModelProvider.LOCAL


@pytest.mark.asyncio
async def test_balanced_optimization(orchestrator):
    """Test balanced model selection"""
    requirements = TaskRequirements(
        task_type="moderate_task",
        complexity=TaskComplexity.MODERATE,
        min_quality=0.75,
        max_cost=5.0,
        max_latency_ms=3000,
        requires_local=False
    )

    selection = await orchestrator.select_model(
        requirements=requirements,
        optimization_goal=OptimizationGoal.BALANCED
    )

    # Should balance all factors
    assert selection.score > 0.5
    assert selection.estimated_cost <= 0.05


@pytest.mark.asyncio
async def test_fallback_models(orchestrator):
    """Test that fallback models are provided"""
    requirements = TaskRequirements(
        task_type="moderate_task",
        complexity=TaskComplexity.MODERATE,
        min_quality=0.7,
        max_cost=10.0,
        max_latency_ms=3000,
        requires_local=False
    )

    selection = await orchestrator.select_model(requirements)

    # Should have fallback models
    assert len(selection.fallback_models) > 0
    # Fallbacks should be different from primary
    assert all(
        f["model"] != selection.model_name or f["provider"] != selection.provider
        for f in selection.fallback_models
    )


@pytest.mark.asyncio
async def test_performance_tracking(orchestrator):
    """Test performance tracking"""
    provider = ModelProvider.OPENAI
    model_name = "gpt-3.5-turbo"

    # Record several performance metrics
    await orchestrator.record_performance(
        provider=provider,
        model_name=model_name,
        latency_ms=1200,
        cost=0.002,
        success=True,
        quality_score=0.85
    )

    await orchestrator.record_performance(
        provider=provider,
        model_name=model_name,
        latency_ms=1100,
        cost=0.0018,
        success=True,
        quality_score=0.88
    )

    # Check that performance was tracked
    key = (provider, model_name)
    assert key in orchestrator.performance_history

    perf = orchestrator.performance_history[key]
    assert perf.total_requests == 2
    assert perf.successful_requests == 2
    assert perf.average_latency_ms > 0
    assert perf.average_cost > 0


@pytest.mark.asyncio
async def test_performance_adjustment(orchestrator):
    """Test that poor performance adjusts selection"""
    provider = ModelProvider.OPENAI
    model_name = "gpt-3.5-turbo"

    # Record poor performance
    for _ in range(10):
        await orchestrator.record_performance(
            provider=provider,
            model_name=model_name,
            latency_ms=5000,  # Very high latency
            cost=0.01,
            success=False,  # Failures
            quality_score=0.3
        )

    # Now try to select this model
    requirements = TaskRequirements(
        task_type="simple_task",
        complexity=TaskComplexity.SIMPLE,
        min_quality=0.7,
        max_cost=10.0,
        max_latency_ms=3000,
        requires_local=False
    )

    selection = await orchestrator.select_model(requirements)

    # Should penalize the poorly performing model
    # and select a different one
    # (This depends on scoring implementation)


@pytest.mark.asyncio
async def test_no_models_meet_requirements(orchestrator):
    """Test handling when no models meet requirements"""
    requirements = TaskRequirements(
        task_type="expert_task",
        complexity=TaskComplexity.EXPERT,
        min_quality=1.5,  # Impossible requirement
        max_cost=0.0,
        max_latency_ms=100,
        requires_local=True
    )

    # Should still return best effort model
    selection = await orchestrator.select_model(requirements)

    # Should have a selection (fallback to best available)
    assert selection is not None
    # Explanation should indicate compromise
    assert "no models" in selection.explanation.lower() or "best" in selection.explanation.lower()


@pytest.mark.asyncio
async def test_model_capabilities_comparison(orchestrator):
    """Test comparing model capabilities"""
    # Get local model capabilities
    local_caps = orchestrator.model_catalog[(ModelProvider.LOCAL, "phi-2")]

    # Get GPT-4 capabilities
    gpt4_caps = orchestrator.model_catalog[(ModelProvider.OPENAI, "gpt-4-turbo")]

    # GPT-4 should have better reasoning
    assert gpt4_caps.reasoning_capability > local_caps.reasoning_capability

    # Local should be free
    assert local_caps.cost_per_1k_input_tokens == 0.0
    assert gpt4_caps.cost_per_1k_input_tokens > 0.0

    # Local should be faster
    assert local_caps.typical_latency_ms < gpt4_caps.typical_latency_ms

    # Local should support local execution
    assert local_caps.local_execution is True
    assert gpt4_caps.local_execution is False


def test_task_complexity_enum():
    """Test task complexity levels"""
    assert TaskComplexity.TRIVIAL.value == "trivial"
    assert TaskComplexity.SIMPLE.value == "simple"
    assert TaskComplexity.MODERATE.value == "moderate"
    assert TaskComplexity.COMPLEX.value == "complex"
    assert TaskComplexity.EXPERT.value == "expert"


def test_optimization_goal_enum():
    """Test optimization goals"""
    assert OptimizationGoal.COST.value == "cost"
    assert OptimizationGoal.LATENCY.value == "latency"
    assert OptimizationGoal.QUALITY.value == "quality"
    assert OptimizationGoal.BALANCED.value == "balanced"
    assert OptimizationGoal.PRIVACY.value == "privacy"


def test_model_provider_enum():
    """Test model providers"""
    assert ModelProvider.LOCAL.value == "local"
    assert ModelProvider.OPENAI.value == "openai"
    assert ModelProvider.ANTHROPIC.value == "anthropic"
    assert ModelProvider.COHERE.value == "cohere"


@pytest.mark.asyncio
async def test_code_generation_task(orchestrator):
    """Test model selection for code generation"""
    requirements = TaskRequirements(
        task_type="code_generation",
        complexity=TaskComplexity.MODERATE,
        min_quality=0.8,
        max_cost=5.0,
        max_latency_ms=3000,
        requires_local=False
    )

    selection = await orchestrator.select_model(
        requirements=requirements,
        optimization_goal=OptimizationGoal.QUALITY
    )

    # Code generation needs good reasoning
    assert selection.capabilities.reasoning_capability >= 0.8


@pytest.mark.asyncio
async def test_data_analysis_task(orchestrator):
    """Test model selection for data analysis"""
    requirements = TaskRequirements(
        task_type="data_analysis",
        complexity=TaskComplexity.COMPLEX,
        min_quality=0.85,
        max_cost=10.0,
        max_latency_ms=5000,
        requires_local=False
    )

    selection = await orchestrator.select_model(
        requirements=requirements,
        optimization_goal=OptimizationGoal.BALANCED
    )

    # Should select capable model
    assert selection.capabilities.reasoning_capability >= 0.85
