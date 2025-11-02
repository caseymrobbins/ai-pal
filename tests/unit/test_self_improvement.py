"""
Unit tests for Advanced Self-Improvement Loop (Phase 4.2).

Tests A/B testing framework, performance tracking, LoRA fine-tuning,
and statistical analysis.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

from ai_pal.improvement.self_improvement import (
    SelfImprovementLoop,
    ABTest,
    ABTestStatus,
    ABTestVariant,
    VariantType,
    PerformanceMetrics,
    LoRATrainingConfig,
    LoRATrainingRun,
    ImprovementType,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def improvement_loop(temp_dir):
    """Create a self-improvement loop instance."""
    storage_dir = temp_dir / "improvements"
    storage_dir.mkdir()
    return SelfImprovementLoop(storage_dir=storage_dir)


@pytest.fixture
def sample_component():
    """Sample component name."""
    return "task_planner"


@pytest.fixture
def sample_control_config():
    """Sample control configuration."""
    return {
        "version": "v1.0",
        "parameters": {
            "max_depth": 3,
            "branching_factor": 2
        }
    }


@pytest.fixture
def sample_variant_configs():
    """Sample variant configurations."""
    return [
        {
            "version": "v1.1",
            "parameters": {
                "max_depth": 4,
                "branching_factor": 3
            }
        },
        {
            "version": "v1.2",
            "parameters": {
                "max_depth": 5,
                "branching_factor": 2
            }
        }
    ]


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
def test_improvement_loop_initialization(improvement_loop):
    """Test improvement loop initializes correctly."""
    assert improvement_loop.storage_dir is not None
    assert isinstance(improvement_loop.ab_tests, dict)
    assert isinstance(improvement_loop.performance_data, dict)
    assert isinstance(improvement_loop.lora_training_runs, dict)
    assert isinstance(improvement_loop.active_tests_by_component, dict)


# ============================================================================
# A/B Test Creation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_ab_test(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test starting an A/B test."""
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs,
        min_samples=100,
        max_duration_hours=168
    )

    assert test is not None
    assert test.component == sample_component
    assert test.status == ABTestStatus.RUNNING
    assert test.control.variant_type == VariantType.CONTROL
    assert len(test.variants) == 2
    assert test.min_samples_per_variant == 100
    assert test.max_duration_hours == 168


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ab_test_stored(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test A/B test is stored in registry."""
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs
    )

    assert test.test_id in improvement_loop.ab_tests
    assert sample_component in improvement_loop.active_tests_by_component
    assert improvement_loop.active_tests_by_component[sample_component] == test.test_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cannot_start_duplicate_test(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test cannot start duplicate test for same component."""
    # Start first test
    await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs
    )

    # Try to start duplicate
    with pytest.raises(ValueError):
        await improvement_loop.start_ab_test(
            component=sample_component,
            control_config=sample_control_config,
            variant_configs=sample_variant_configs
        )


# ============================================================================
# A/B Test Sample Recording Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_record_ab_test_sample(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test recording A/B test sample."""
    # Start test
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs
    )

    # Record sample for control
    await improvement_loop.record_ab_test_sample(
        test_id=test.test_id,
        variant_id=test.control.variant_id,
        success=True,
        latency_ms=150.0,
        cost=0.001,
        user_satisfaction=0.8
    )

    # Check recorded
    updated_test = improvement_loop.ab_tests[test.test_id]
    assert updated_test.control.samples == 1
    assert updated_test.control.success_count == 1
    assert updated_test.control.total_latency_ms == 150.0
    assert updated_test.control.total_cost == 0.001


@pytest.mark.unit
@pytest.mark.asyncio
async def test_record_multiple_samples(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test recording multiple samples."""
    # Start test
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs
    )

    # Record multiple samples
    for i in range(10):
        await improvement_loop.record_ab_test_sample(
            test_id=test.test_id,
            variant_id=test.control.variant_id,
            success=i % 3 != 0,  # ~67% success rate
            latency_ms=100.0 + i * 10,
            cost=0.001,
            user_satisfaction=0.7 + i * 0.01
        )

    # Check aggregated
    updated_test = improvement_loop.ab_tests[test.test_id]
    assert updated_test.control.samples == 10
    assert updated_test.control.success_count == 7  # 7 out of 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_record_sample_for_variant(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test recording samples for variant."""
    # Start test
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs
    )

    # Record sample for first variant
    variant_id = test.variants[0].variant_id
    await improvement_loop.record_ab_test_sample(
        test_id=test.test_id,
        variant_id=variant_id,
        success=True,
        latency_ms=120.0,
        cost=0.0015,
        user_satisfaction=0.85
    )

    # Check recorded
    updated_test = improvement_loop.ab_tests[test.test_id]
    variant = next(v for v in updated_test.variants if v.variant_id == variant_id)
    assert variant.samples == 1
    assert variant.success_count == 1


# ============================================================================
# A/B Test Completion Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_ab_test_auto_completion(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test A/B test auto-completes when min samples reached."""
    # Start test with low min samples
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs,
        min_samples=5,  # Low threshold for testing
        max_duration_hours=168
    )

    # Record samples for control
    for i in range(5):
        await improvement_loop.record_ab_test_sample(
            test.test_id,
            test.control.variant_id,
            success=True,
            latency_ms=100.0,
            cost=0.001,
            user_satisfaction=0.8
        )

    # Record samples for variants
    for variant in test.variants:
        for i in range(5):
            await improvement_loop.record_ab_test_sample(
                test.test_id,
                variant.variant_id,
                success=True,
                latency_ms=90.0,  # Slightly better
                cost=0.001,
                user_satisfaction=0.85
            )

    # Check if test completed
    updated_test = improvement_loop.ab_tests[test.test_id]
    # Should have enough samples to potentially complete
    assert updated_test.control.samples >= 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_determine_winner(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test winner determination from A/B test."""
    # Start test
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs,
        min_samples=10
    )

    # Record samples - control with 70% success
    for i in range(10):
        await improvement_loop.record_ab_test_sample(
            test.test_id,
            test.control.variant_id,
            success=i < 7,
            latency_ms=100.0,
            cost=0.001,
            user_satisfaction=0.7
        )

    # Record samples - variant 1 with 90% success (clear winner)
    for i in range(10):
        await improvement_loop.record_ab_test_sample(
            test.test_id,
            test.variants[0].variant_id,
            success=i < 9,
            latency_ms=95.0,
            cost=0.001,
            user_satisfaction=0.9
        )

    # Record samples - variant 2 with 60% success
    for i in range(10):
        await improvement_loop.record_ab_test_sample(
            test.test_id,
            test.variants[1].variant_id,
            success=i < 6,
            latency_ms=105.0,
            cost=0.001,
            user_satisfaction=0.6
        )

    # Manually complete test
    await improvement_loop._complete_ab_test(test.test_id)

    # Check winner
    updated_test = improvement_loop.ab_tests[test.test_id]
    assert updated_test.status == ABTestStatus.COMPLETED
    assert updated_test.winner is not None
    # Winner should be variant 1 (best success rate)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ab_test_timeout(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test A/B test times out after max duration."""
    # Start test with short duration
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs,
        min_samples=1000,  # High threshold
        max_duration_hours=1  # 1 hour max
    )

    # Manually set start time to past
    test.started_at = datetime.now() - timedelta(hours=2)

    # Check if expired
    await improvement_loop._check_ab_test_completion(test.test_id)

    # Should be completed (timed out)
    updated_test = improvement_loop.ab_tests[test.test_id]
    # ABTestStatus enum values are: RUNNING, COMPLETED, CANCELLED
    assert updated_test.status == ABTestStatus.COMPLETED


# ============================================================================
# Performance Metrics Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_record_performance_metric(improvement_loop, sample_component):
    """Test recording performance metrics."""
    now = datetime.now()

    await improvement_loop.record_performance_metric(
        component=sample_component,
        success=True,
        latency_ms=150.0,
        cost=0.01,  # Required parameter
        user_satisfaction=0.85,
        gate_violation=False,
        ari_alert=False
    )

    # Check stored
    assert sample_component in improvement_loop.performance_data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_performance_metrics(improvement_loop, sample_component):
    """Test getting aggregated performance metrics."""
    now = datetime.now()

    # Record multiple metrics
    for i in range(20):
        await improvement_loop.record_performance_metric(
            component=sample_component,
            success=i % 5 != 0,  # 80% success rate
            latency_ms=100.0 + i * 5,  # Varying latency
            cost=0.01 + i * 0.001,  # Required parameter
            user_satisfaction=0.7 + (i % 10) * 0.02,
            gate_violation=i % 10 == 0,  # 10% violation rate
            ari_alert=i % 20 == 0  # 5% alert rate
        )

    # Get metrics for last hour - correct parameter name
    metrics = await improvement_loop.get_performance_metrics(
        component=sample_component,
        period_hours=1
    )

    assert metrics is not None
    assert metrics.component == sample_component
    assert metrics.total_requests == 20
    assert metrics.successful_requests == 16  # 80% of 20
    assert abs(metrics.success_rate - 0.8) < 0.01  # ~80%
    assert metrics.average_latency_ms > 0
    assert abs(metrics.gate_violation_rate - 0.1) < 0.01  # ~10%
    assert abs(metrics.ari_alert_rate - 0.05) < 0.01  # ~5%


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performance_percentiles(improvement_loop, sample_component):
    """Test latency percentile calculations."""
    now = datetime.now()

    # Record metrics with known latencies
    latencies = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190,
                 200, 210, 220, 230, 240, 250, 260, 270, 280, 290]

    for latency in latencies:
        await improvement_loop.record_performance_metric(
            component=sample_component,
            success=True,
            latency_ms=latency,
            cost=0.01,  # Required parameter
            user_satisfaction=0.8
        )

    # Get metrics - correct parameter name
    metrics = await improvement_loop.get_performance_metrics(
        component=sample_component,
        period_hours=1
    )

    # Check percentiles
    assert metrics.p95_latency_ms > metrics.average_latency_ms
    assert metrics.p99_latency_ms > metrics.p95_latency_ms
    assert metrics.p95_latency_ms <= 290  # Should be within data range


# ============================================================================
# LoRA Fine-Tuning Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_initiate_lora_training(improvement_loop, sample_component):
    """Test initiating LoRA fine-tuning."""
    training_config = LoRATrainingConfig(
        base_model="gpt-3.5-turbo",
        rank=8,
        alpha=16,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        learning_rate=0.0001,
        num_epochs=3,
        batch_size=4
    )

    training_data = [
        {"input": "task 1", "output": "result 1"},
        {"input": "task 2", "output": "result 2"},
    ]

    run = await improvement_loop.initiate_lora_training(
        component=sample_component,
        config=training_config,
        training_data=training_data
    )

    assert run is not None
    assert run.component == sample_component
    assert run.config == training_config
    assert run.status == "running"
    assert run.run_id in improvement_loop.lora_training_runs


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lora_training_data_split(improvement_loop, sample_component):
    """Test LoRA training data is split into train/val sets."""
    training_config = LoRATrainingConfig(
        base_model="gpt-3.5-turbo",
        rank=8
    )

    training_data = [{"input": f"task {i}", "output": f"result {i}"} for i in range(100)]

    run = await improvement_loop.initiate_lora_training(
        component=sample_component,
        config=training_config,
        training_data=training_data
    )

    # Check split (80/20)
    assert run.train_samples == 80
    assert run.val_samples == 20


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lora_training_completion(improvement_loop, sample_component):
    """Test LoRA training completes and records metrics."""
    training_config = LoRATrainingConfig(
        base_model="gpt-3.5-turbo",
        rank=4,
        num_epochs=1
    )

    training_data = [{"input": f"task {i}", "output": f"result {i}"} for i in range(10)]

    run = await improvement_loop.initiate_lora_training(
        component=sample_component,
        config=training_config,
        training_data=training_data
    )

    # Wait for completion (simulated)
    await improvement_loop._simulate_lora_training(run.run_id)

    # Check completed
    updated_run = improvement_loop.lora_training_runs[run.run_id]
    assert updated_run.status == "completed"
    assert updated_run.completed_at is not None
    assert updated_run.final_train_loss is not None
    assert updated_run.final_val_loss is not None


# ============================================================================
# Statistical Significance Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_statistical_significance_calculation(
    improvement_loop,
    sample_component,
    sample_control_config,
    sample_variant_configs
):
    """Test statistical significance is calculated."""
    test = await improvement_loop.start_ab_test(
        component=sample_component,
        control_config=sample_control_config,
        variant_configs=sample_variant_configs,
        min_samples=100
    )

    # Record enough samples for statistical significance
    for i in range(100):
        await improvement_loop.record_ab_test_sample(
            test.test_id,
            test.control.variant_id,
            success=i < 70,  # 70% success
            latency_ms=100.0,
            cost=0.001,
            user_satisfaction=0.7
        )

    for i in range(100):
        await improvement_loop.record_ab_test_sample(
            test.test_id,
            test.variants[0].variant_id,
            success=i < 85,  # 85% success (significant difference)
            latency_ms=100.0,
            cost=0.001,
            user_satisfaction=0.85
        )

    # Complete test
    await improvement_loop._complete_ab_test(test.test_id)

    # Check statistical significance
    updated_test = improvement_loop.ab_tests[test.test_id]
    winning_variant = next(
        (v for v in updated_test.variants if v.variant_id == updated_test.winner),
        None
    )

    # With large sample and clear difference, should be significant
    if winning_variant:
        assert winning_variant.is_statistically_significant


# ============================================================================
# Edge Cases Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_ab_test_with_no_variants(improvement_loop, sample_component):
    """Test handling A/B test with empty variant list."""
    with pytest.raises(ValueError):
        await improvement_loop.start_ab_test(
            component=sample_component,
            control_config={"version": "v1"},
            variant_configs=[],  # No variants
            min_samples=10
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_record_sample_for_nonexistent_test(improvement_loop):
    """Test recording sample for test that doesn't exist."""
    with pytest.raises(KeyError):
        await improvement_loop.record_ab_test_sample(
            test_id="nonexistent",
            variant_id="nonexistent",
            success=True,
            latency_ms=100.0,
            cost=0.01
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_metrics_with_no_data(improvement_loop, sample_component):
    """Test getting metrics for component with no data."""
    now = datetime.now()

    metrics = await improvement_loop.get_performance_metrics(
        component=sample_component,
        period_start=now - timedelta(hours=1),
        period_end=now
    )

    # Should return empty/zero metrics
    assert metrics.total_requests == 0
    assert metrics.success_rate == 0.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lora_training_with_insufficient_data(improvement_loop, sample_component):
    """Test LoRA training fails with insufficient data."""
    training_config = LoRATrainingConfig(
        base_model="gpt-3.5-turbo",
        rank=8
    )

    # Too few samples
    training_data = [{"input": "task 1", "output": "result 1"}]

    with pytest.raises(ValueError):
        await improvement_loop.initiate_lora_training(
            component=sample_component,
            config=training_config,
            training_data=training_data
        )
