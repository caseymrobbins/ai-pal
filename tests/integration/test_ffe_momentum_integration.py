"""
Integration tests for FFE components with Momentum Loop.

Tests integration of:
- Strength Amplifier (AI-powered)
- Momentum Loop State Machine
- Enhanced Context Window
- Self-Improvement Loop
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from ai_pal.ffe.components.momentum_loop import (
    MomentumLoop,
    MomentumState,
    EventType,
)
from ai_pal.ffe.components.strength_amplifier import StrengthAmplifier
from ai_pal.context.enhanced_context import (
    EnhancedContextManager,
    MemoryType,
    MemoryPriority,
)
from ai_pal.improvement.self_improvement import SelfImprovementLoop
from ai_pal.ffe.models import (
    PersonalityProfile,
    SignatureStrength,
    StrengthType,
    AtomicBlock,
    MicroBottleneck,
    BottleneckType,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_ffe_dir(temp_dir):
    """Create temporary FFE directory structure."""
    ffe_dir = temp_dir / "ffe_integration"
    ffe_dir.mkdir()
    (ffe_dir / "momentum").mkdir()
    (ffe_dir / "context").mkdir()
    (ffe_dir / "improvements").mkdir()
    return ffe_dir


@pytest.fixture
def momentum_loop(temp_ffe_dir):
    """Create momentum loop."""
    return MomentumLoop(storage_dir=temp_ffe_dir / "momentum")


@pytest.fixture
def strength_amplifier():
    """Create strength amplifier (without orchestrator for now)."""
    return StrengthAmplifier(orchestrator=None)


@pytest.fixture
def context_manager(temp_ffe_dir):
    """Create context manager."""
    return EnhancedContextManager(
        storage_dir=temp_ffe_dir / "context",
        max_context_tokens=2000
    )


@pytest.fixture
def improvement_loop(temp_ffe_dir):
    """Create improvement loop."""
    return SelfImprovementLoop(storage_dir=temp_ffe_dir / "improvements")


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "integration_test_user"


@pytest.fixture
def test_personality():
    """Test personality profile."""
    return PersonalityProfile(
        user_id="integration_test_user",
        signature_strengths=[
            SignatureStrength(
                strength_type=StrengthType.ANALYTICAL,
                proficiency_level=0.85,
                identity_label="analytical thinker"
            ),
            SignatureStrength(
                strength_type=StrengthType.SYSTEMATIC,
                proficiency_level=0.75,
                identity_label="systematic organizer"
            )
        ]
    )


# ============================================================================
# Full Momentum Cycle Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_ffe_cycle_with_context(
    momentum_loop,
    strength_amplifier,
    context_manager,
    test_user_id,
    test_personality
):
    """Test full FFE cycle integrating momentum loop and context manager."""
    # 1. Start momentum loop
    loop_state = await momentum_loop.start_loop(test_user_id, test_personality)
    assert loop_state.current_state == MomentumState.IDLE

    # 2. Add context about user's current work
    await context_manager.add_memory(
        user_id=test_user_id,
        content="Working on implementing unit tests for momentum loop",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.HIGH
    )

    # 3. Create task and amplify with strength
    task = "Write comprehensive tests"
    reframed_task, strength = await strength_amplifier.amplify_with_best_match(
        task_description=task,
        strengths=test_personality.signature_strengths
    )

    assert reframed_task != task  # Should be reframed
    assert strength is not None

    # 4. Create atomic block
    block = AtomicBlock(
        block_id="block_001",
        title=reframed_task,
        description="Complete unit tests for momentum loop",
        estimated_minutes=30,
        strength_used=strength.strength_type
    )

    # 5. Progress through momentum cycle
    # IDLE → WIN_STRENGTH
    loop_state = await momentum_loop.process_event(
        test_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": block}
    )
    assert loop_state.current_state == MomentumState.WIN_STRENGTH

    # Record in context
    await context_manager.add_memory(
        user_id=test_user_id,
        content=f"Completed: {block.title}",
        memory_type=MemoryType.ACHIEVEMENT,
        priority=MemoryPriority.HIGH
    )

    # WIN_STRENGTH → AFFIRM_PRIDE
    reward = await strength_amplifier.generate_reward_language(block, strength)
    loop_state = await momentum_loop.process_event(
        test_user_id,
        EventType.REWARD_EMITTED,
        {"reward": reward}
    )
    assert loop_state.current_state == MomentumState.AFFIRM_PRIDE

    # AFFIRM_PRIDE → PIVOT_DETECT
    bottleneck = MicroBottleneck(
        bottleneck_id="bn_001",
        description="Unclear requirements for edge cases",
        bottleneck_type=BottleneckType.CLARITY,
        detected_at=datetime.now(),
        atomic_block_id=block.block_id
    )

    loop_state = await momentum_loop.process_event(
        test_user_id,
        EventType.BOTTLENECK_CHECKED,
        {"bottleneck": bottleneck}
    )
    assert loop_state.current_state == MomentumState.PIVOT_DETECT

    # PIVOT_DETECT → REFRAME_STRENGTH
    loop_state = await momentum_loop.process_event(
        test_user_id,
        EventType.REFRAME_COMPLETE,
        {"new_framing": "Break down edge cases systematically"}
    )
    assert loop_state.current_state == MomentumState.REFRAME_STRENGTH

    # REFRAME_STRENGTH → LAUNCH_GROWTH
    loop_state = await momentum_loop.process_event(
        test_user_id,
        EventType.GROWTH_STARTED,
        {"growth_task": "Learn pytest parametrize for edge cases"}
    )
    assert loop_state.current_state == MomentumState.LAUNCH_GROWTH

    # LAUNCH_GROWTH → WIN_GROWTH
    loop_state = await momentum_loop.process_event(
        test_user_id,
        EventType.GROWTH_COMPLETED,
        {"growth_result": "Mastered parametrized tests"}
    )
    assert loop_state.current_state == MomentumState.WIN_GROWTH
    assert loop_state.cycle_count == 1

    # 6. Verify context window can retrieve relevant memories
    window = await context_manager.create_context_window(
        user_id=test_user_id,
        query="What am I working on?"
    )

    assert len(window.memory_ids) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_momentum_loop_with_performance_tracking(
    momentum_loop,
    improvement_loop,
    test_user_id,
    test_personality
):
    """Test momentum loop integrated with performance tracking."""
    # Start momentum loop
    await momentum_loop.start_loop(test_user_id, test_personality)

    # Track performance of each state transition
    component = "momentum_loop"

    # Complete a few transitions and track performance
    block = AtomicBlock(
        block_id="perf_block_001",
        title="Performance test task",
        description="Testing performance tracking",
        estimated_minutes=15,
        strength_used=StrengthType.ANALYTICAL
    )

    # Transition and track
    start_time = datetime.now()
    await momentum_loop.process_event(
        test_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": block}
    )
    latency_ms = (datetime.now() - start_time).total_seconds() * 1000

    # Record performance
    await improvement_loop.record_performance_metric(
        component=component,
        success=True,
        latency_ms=latency_ms,
        user_satisfaction=0.9
    )

    # Get metrics
    metrics = await improvement_loop.get_performance_metrics(
        component=component,
        period_start=datetime.now() - timedelta(hours=1),
        period_end=datetime.now() + timedelta(minutes=1)
    )

    assert metrics.total_requests >= 1
    assert metrics.success_rate > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_driven_strength_selection(
    context_manager,
    strength_amplifier,
    test_user_id,
    test_personality
):
    """Test using context to inform strength selection."""
    # Add context about recent successes with analytical thinking
    await context_manager.add_memory(
        user_id=test_user_id,
        content="Successfully used analytical thinking to debug complex issue",
        memory_type=MemoryType.ACHIEVEMENT,
        priority=MemoryPriority.HIGH
    )

    await context_manager.add_memory(
        user_id=test_user_id,
        content="Analytical approach worked well for API design",
        memory_type=MemoryType.ACHIEVEMENT,
        priority=MemoryPriority.HIGH
    )

    # Get context window
    window = await context_manager.create_context_window(
        user_id=test_user_id,
        query="What strengths work best for me?"
    )

    # Use strength amplifier
    task = "Design new database schema"
    reframed_task, strength = await strength_amplifier.amplify_with_best_match(
        task_description=task,
        strengths=test_personality.signature_strengths
    )

    # Should select analytical (highest proficiency)
    assert strength.strength_type == StrengthType.ANALYTICAL


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ab_test_different_reframing_strategies(
    improvement_loop,
    strength_amplifier,
    test_personality
):
    """Test A/B testing different task reframing strategies."""
    # Start A/B test for strength amplifier
    control_config = {
        "strategy": "template_based",
        "version": "v1.0"
    }

    variant_configs = [
        {
            "strategy": "ai_powered",
            "version": "v2.0",
            "model": "gpt-3.5-turbo"
        }
    ]

    test = await improvement_loop.start_ab_test(
        component="strength_amplifier",
        control_config=control_config,
        variant_configs=variant_configs,
        min_samples=20
    )

    # Simulate testing different approaches
    task = "Write documentation"
    strength = test_personality.signature_strengths[0]

    # Test control (template-based)
    for i in range(20):
        reframed = await strength_amplifier._reframe_task_template(task, strength)

        # Record outcome
        await improvement_loop.record_ab_test_sample(
            test_id=test.test_id,
            variant_id=test.control.variant_id,
            success=True,
            latency_ms=50.0,
            cost=0.0,
            user_satisfaction=0.75
        )

    # Test variant (would use AI if orchestrator available)
    for i in range(20):
        # Simulate variant
        await improvement_loop.record_ab_test_sample(
            test_id=test.test_id,
            variant_id=test.variants[0].variant_id,
            success=True,
            latency_ms=200.0,  # AI slower
            cost=0.001,  # AI costs money
            user_satisfaction=0.85  # But better quality
        )

    # Complete test
    await improvement_loop._complete_ab_test(test.test_id)

    # Check results
    updated_test = improvement_loop.ab_tests[test.test_id]
    assert updated_test.status == "completed"
    assert updated_test.winner is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_pruning_under_load(
    context_manager,
    test_user_id
):
    """Test context manager handles pruning under memory pressure."""
    # Add many memories to trigger pruning
    memory_ids = []
    for i in range(50):
        priority = MemoryPriority.CRITICAL if i < 5 else MemoryPriority.MEDIUM
        memory_id = await context_manager.add_memory(
            user_id=test_user_id,
            content=f"Memory {i}: " + " ".join(["word"] * 50),  # ~50 tokens each
            memory_type=MemoryType.CONTEXT,
            priority=priority
        )
        memory_ids.append(memory_id)

    # Create context window with limited tokens
    context_manager.max_context_tokens = 500
    window = await context_manager.create_context_window(
        user_id=test_user_id,
        query="Recent work"
    )

    # Should have pruned some memories
    assert len(window.memory_ids) < 50

    # CRITICAL memories should still be present
    critical_ids = memory_ids[:5]
    for crit_id in critical_ids:
        # Either in window or protected during pruning
        assert crit_id in window.memory_ids or crit_id not in window.pruned_memories


@pytest.mark.integration
@pytest.mark.asyncio
async def test_momentum_state_recovery_from_timeout(
    momentum_loop,
    context_manager,
    test_user_id,
    test_personality
):
    """Test momentum loop recovers from timeout with context."""
    # Start loop
    loop_state = await momentum_loop.start_loop(test_user_id, test_personality)

    # Progress to WIN_STRENGTH
    block = AtomicBlock(
        block_id="timeout_block",
        title="Task that times out",
        description="Testing timeout recovery",
        estimated_minutes=20,
        strength_used=StrengthType.ANALYTICAL
    )

    await momentum_loop.process_event(
        test_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": block}
    )

    # Simulate timeout
    loop_state = momentum_loop.active_loops[test_user_id]
    loop_state.state_entered_at = datetime.now() - timedelta(hours=2)

    # Record timeout in context
    await context_manager.add_memory(
        user_id=test_user_id,
        content="Momentum loop timed out in WIN_STRENGTH state",
        memory_type=MemoryType.SYSTEM,
        priority=MemoryPriority.MEDIUM
    )

    # Process timeout
    recovered_state = await momentum_loop.process_event(
        test_user_id,
        EventType.TIMEOUT,
        {}
    )

    # Should recover to safe state
    assert recovered_state.current_state == MomentumState.IDLE

    # Context should show timeout
    window = await context_manager.create_context_window(
        user_id=test_user_id,
        query="What happened to the momentum loop?"
    )

    assert len(window.memory_ids) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multi_user_momentum_loops(
    momentum_loop,
    context_manager,
    test_personality
):
    """Test multiple users can have independent momentum loops."""
    users = ["user_1", "user_2", "user_3"]

    # Start loops for all users
    for user_id in users:
        await momentum_loop.start_loop(user_id, test_personality)

        # Add user-specific context
        await context_manager.add_memory(
            user_id=user_id,
            content=f"Context for {user_id}",
            memory_type=MemoryType.CONTEXT,
            priority=MemoryPriority.MEDIUM
        )

    # Progress each user independently
    for i, user_id in enumerate(users):
        block = AtomicBlock(
            block_id=f"block_{user_id}",
            title=f"Task for {user_id}",
            description=f"User {i+1} specific task",
            estimated_minutes=10 + i * 5,
            strength_used=StrengthType.ANALYTICAL
        )

        await momentum_loop.process_event(
            user_id,
            EventType.BLOCK_COMPLETED,
            {"block": block}
        )

    # Verify all users are in different or same states independently
    for user_id in users:
        loop_state = momentum_loop.active_loops[user_id]
        assert loop_state.current_state == MomentumState.WIN_STRENGTH

        # Each user has their own context
        window = await context_manager.create_context_window(
            user_id=user_id,
            query="My context"
        )
        assert len(window.memory_ids) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performance_trends_over_cycles(
    momentum_loop,
    improvement_loop,
    test_user_id,
    test_personality
):
    """Test tracking performance trends across multiple momentum cycles."""
    component = "full_momentum_cycle"

    # Run multiple cycles and track performance
    for cycle in range(5):
        # Start/restart loop
        if cycle == 0:
            await momentum_loop.start_loop(test_user_id, test_personality)
        else:
            # Reset to IDLE for new cycle
            loop_state = momentum_loop.active_loops[test_user_id]
            loop_state.current_state = MomentumState.IDLE

        # Run through cycle
        block = AtomicBlock(
            block_id=f"cycle_{cycle}_block",
            title=f"Cycle {cycle} task",
            description="Testing performance trends",
            estimated_minutes=15,
            strength_used=StrengthType.SYSTEMATIC
        )

        # Track cycle performance
        cycle_start = datetime.now()

        # Go through states
        await momentum_loop.process_event(test_user_id, EventType.BLOCK_COMPLETED, {"block": block})
        await momentum_loop.process_event(test_user_id, EventType.REWARD_EMITTED, {"reward": "Good!"})

        cycle_duration = (datetime.now() - cycle_start).total_seconds() * 1000

        # Record performance (simulate improvement over cycles)
        user_satisfaction = 0.7 + (cycle * 0.05)  # Improving over time
        await improvement_loop.record_performance_metric(
            component=component,
            success=True,
            latency_ms=cycle_duration,
            user_satisfaction=user_satisfaction
        )

    # Get overall metrics
    metrics = await improvement_loop.get_performance_metrics(
        component=component,
        period_start=datetime.now() - timedelta(hours=1),
        period_end=datetime.now() + timedelta(minutes=1)
    )

    assert metrics.total_requests == 5
    assert metrics.success_rate == 1.0
    # Average satisfaction should reflect improvement
    assert metrics.user_satisfaction > 0.7


# ============================================================================
# Error Handling Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_graceful_degradation_on_component_failure(
    momentum_loop,
    strength_amplifier,
    test_user_id,
    test_personality
):
    """Test system degrades gracefully when component fails."""
    # Start loop
    await momentum_loop.start_loop(test_user_id, test_personality)

    # Simulate strength amplifier failure (no orchestrator)
    task = "Complex task"

    # Should fall back to template
    reframed_task, strength = await strength_amplifier.amplify_with_best_match(
        task_description=task,
        strengths=test_personality.signature_strengths
    )

    # Should still work with template fallback
    assert reframed_task != task
    assert strength is not None

    # Momentum loop should still function
    block = AtomicBlock(
        block_id="fallback_block",
        title=reframed_task,
        description="Testing fallback",
        estimated_minutes=20,
        strength_used=strength.strength_type
    )

    loop_state = await momentum_loop.process_event(
        test_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": block}
    )

    assert loop_state.current_state == MomentumState.WIN_STRENGTH
