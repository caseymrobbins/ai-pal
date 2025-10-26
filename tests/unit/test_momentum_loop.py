"""
Unit tests for Momentum Loop State Machine (Phase 5.3).

Tests event-driven state transitions, state persistence, timeout handling,
and metrics tracking.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

from ai_pal.ffe.components.momentum_loop import (
    MomentumLoop,
    MomentumState,
    EventType,
    MomentumLoopState,
)
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
def momentum_loop(temp_dir):
    """Create a momentum loop instance."""
    storage_dir = temp_dir / "momentum"
    storage_dir.mkdir()
    return MomentumLoop(storage_dir=storage_dir)


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return "test_user_123"


@pytest.fixture
def sample_personality():
    """Sample personality profile."""
    return PersonalityProfile(
        user_id="test_user_123",
        signature_strengths=[
            SignatureStrength(
                strength_type=StrengthType.ANALYTICAL,
                proficiency_level=0.8,
                identity_label="analytical thinker"
            )
        ]
    )


@pytest.fixture
def sample_block():
    """Sample atomic block."""
    return AtomicBlock(
        block_id="block_001",
        title="Write unit tests",
        description="Create comprehensive unit tests for momentum loop",
        estimated_minutes=30,
        strength_used=StrengthType.ANALYTICAL
    )


@pytest.fixture
def sample_bottleneck():
    """Sample micro-bottleneck."""
    return MicroBottleneck(
        bottleneck_id="bottleneck_001",
        description="Unclear test requirements",
        bottleneck_type=BottleneckType.CLARITY,
        detected_at=datetime.now(),
        atomic_block_id="block_001"
    )


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
def test_momentum_loop_initialization(momentum_loop):
    """Test momentum loop initializes correctly."""
    assert momentum_loop.storage_dir is not None
    assert isinstance(momentum_loop.active_loops, dict)
    assert isinstance(momentum_loop.event_queue, list)
    assert isinstance(momentum_loop.metrics, dict)
    assert len(momentum_loop.active_loops) == 0


@pytest.mark.unit
def test_event_handlers_registered(momentum_loop):
    """Test all state handlers are registered."""
    # Should have handlers for all states
    assert MomentumState.IDLE in momentum_loop.event_handlers
    assert MomentumState.WIN_STRENGTH in momentum_loop.event_handlers
    assert MomentumState.AFFIRM_PRIDE in momentum_loop.event_handlers
    assert MomentumState.PIVOT_DETECT in momentum_loop.event_handlers
    assert MomentumState.REFRAME_STRENGTH in momentum_loop.event_handlers
    assert MomentumState.LAUNCH_GROWTH in momentum_loop.event_handlers
    assert MomentumState.WIN_GROWTH in momentum_loop.event_handlers


@pytest.mark.unit
def test_valid_transitions_defined(momentum_loop):
    """Test valid state transitions are defined."""
    # Check critical transitions
    assert MomentumState.WIN_STRENGTH in momentum_loop.valid_transitions[MomentumState.IDLE]
    assert MomentumState.AFFIRM_PRIDE in momentum_loop.valid_transitions[MomentumState.WIN_STRENGTH]
    assert MomentumState.PIVOT_DETECT in momentum_loop.valid_transitions[MomentumState.AFFIRM_PRIDE]
    assert MomentumState.REFRAME_STRENGTH in momentum_loop.valid_transitions[MomentumState.PIVOT_DETECT]
    assert MomentumState.LAUNCH_GROWTH in momentum_loop.valid_transitions[MomentumState.REFRAME_STRENGTH]
    assert MomentumState.WIN_GROWTH in momentum_loop.valid_transitions[MomentumState.LAUNCH_GROWTH]

    # Check cycle can restart
    assert MomentumState.WIN_STRENGTH in momentum_loop.valid_transitions[MomentumState.WIN_GROWTH]


# ============================================================================
# State Transition Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_loop_creates_state(momentum_loop, sample_user_id, sample_personality):
    """Test starting a loop creates initial state."""
    loop_state = await momentum_loop.start_loop(sample_user_id, sample_personality)

    assert loop_state is not None
    assert loop_state.user_id == sample_user_id
    assert loop_state.current_state == MomentumState.IDLE
    assert loop_state.personality == sample_personality
    assert loop_state.cycle_count == 0
    assert sample_user_id in momentum_loop.active_loops


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transition_idle_to_win_strength(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test transition from IDLE to WIN_STRENGTH."""
    # Start loop
    await momentum_loop.start_loop(sample_user_id, sample_personality)

    # Process block completion event
    loop_state = await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )

    assert loop_state.current_state == MomentumState.WIN_STRENGTH
    assert loop_state.current_block == sample_block


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transition_win_to_affirm(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test transition from WIN_STRENGTH to AFFIRM_PRIDE."""
    # Setup: get to WIN_STRENGTH state
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )

    # Process reward emitted event
    loop_state = await momentum_loop.process_event(
        sample_user_id,
        EventType.REWARD_EMITTED,
        {"reward": "Great job using your analytical thinking!"}
    )

    assert loop_state.current_state == MomentumState.AFFIRM_PRIDE
    assert loop_state.last_reward is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_full_momentum_cycle(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block,
    sample_bottleneck
):
    """Test full momentum loop cycle through all states."""
    # 1. Start: IDLE
    await momentum_loop.start_loop(sample_user_id, sample_personality)

    # 2. IDLE → WIN_STRENGTH (block completed)
    state = await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )
    assert state.current_state == MomentumState.WIN_STRENGTH

    # 3. WIN_STRENGTH → AFFIRM_PRIDE (reward emitted)
    state = await momentum_loop.process_event(
        sample_user_id,
        EventType.REWARD_EMITTED,
        {"reward": "Well done!"}
    )
    assert state.current_state == MomentumState.AFFIRM_PRIDE

    # 4. AFFIRM_PRIDE → PIVOT_DETECT (bottleneck check)
    state = await momentum_loop.process_event(
        sample_user_id,
        EventType.BOTTLENECK_CHECKED,
        {"bottleneck": sample_bottleneck}
    )
    assert state.current_state == MomentumState.PIVOT_DETECT
    assert state.current_bottleneck == sample_bottleneck

    # 5. PIVOT_DETECT → REFRAME_STRENGTH (reframe complete)
    state = await momentum_loop.process_event(
        sample_user_id,
        EventType.REFRAME_COMPLETE,
        {"new_framing": "Use your analytical skills to clarify requirements"}
    )
    assert state.current_state == MomentumState.REFRAME_STRENGTH

    # 6. REFRAME_STRENGTH → LAUNCH_GROWTH (growth started)
    state = await momentum_loop.process_event(
        sample_user_id,
        EventType.GROWTH_STARTED,
        {"growth_task": "Learn pytest fixtures"}
    )
    assert state.current_state == MomentumState.LAUNCH_GROWTH

    # 7. LAUNCH_GROWTH → WIN_GROWTH (growth completed)
    state = await momentum_loop.process_event(
        sample_user_id,
        EventType.GROWTH_COMPLETED,
        {"growth_result": "Mastered pytest fixtures"}
    )
    assert state.current_state == MomentumState.WIN_GROWTH
    assert state.cycle_count == 1  # Completed one full cycle


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_transition_prevented(
    momentum_loop,
    sample_user_id,
    sample_personality
):
    """Test invalid state transitions are prevented."""
    # Start in IDLE
    await momentum_loop.start_loop(sample_user_id, sample_personality)

    # Try to jump directly to AFFIRM_PRIDE (should stay in IDLE or handle gracefully)
    with pytest.raises(Exception):
        await momentum_loop.process_event(
            sample_user_id,
            EventType.REWARD_EMITTED,  # Event for wrong state
            {"reward": "Invalid transition"}
        )


# ============================================================================
# State Persistence Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_state_persistence(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test state is persisted to disk."""
    # Create state
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )

    # Check file was created
    state_file = momentum_loop.storage_dir / f"{sample_user_id}_momentum.json"
    assert state_file.exists()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_state_loading(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test state can be loaded from disk."""
    # Create and persist state
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )

    # Create new instance and load state
    new_loop = MomentumLoop(storage_dir=momentum_loop.storage_dir)
    await new_loop._load_active_loops()

    assert sample_user_id in new_loop.active_loops
    assert new_loop.active_loops[sample_user_id].current_state == MomentumState.WIN_STRENGTH


@pytest.mark.unit
@pytest.mark.asyncio
async def test_state_serialization_roundtrip(
    momentum_loop,
    sample_user_id,
    sample_personality
):
    """Test state serialization and deserialization preserves data."""
    # Create state
    original_state = await momentum_loop.start_loop(sample_user_id, sample_personality)

    # Serialize
    state_dict = momentum_loop._serialize_loop_state(original_state)

    # Deserialize
    restored_state = momentum_loop._deserialize_loop_state(state_dict)

    # Verify
    assert restored_state.user_id == original_state.user_id
    assert restored_state.current_state == original_state.current_state
    assert restored_state.personality.user_id == original_state.personality.user_id


# ============================================================================
# Timeout Handling Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_timeout_detection(
    momentum_loop,
    sample_user_id,
    sample_personality
):
    """Test timeout detection for stuck states."""
    # Start loop
    loop_state = await momentum_loop.start_loop(sample_user_id, sample_personality)

    # Manually set state entry time to past
    loop_state.state_entered_at = datetime.now() - timedelta(hours=2)

    # Check for timeouts
    timed_out = await momentum_loop._check_timeouts()

    # Should detect timeout (default timeout is 1 hour)
    assert len(timed_out) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_timeout_recovery(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test automatic recovery from timeout."""
    # Get to WIN_STRENGTH state
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )

    # Simulate timeout
    loop_state = momentum_loop.active_loops[sample_user_id]
    loop_state.state_entered_at = datetime.now() - timedelta(hours=2)

    # Process timeout event
    recovered_state = await momentum_loop.process_event(
        sample_user_id,
        EventType.TIMEOUT,
        {}
    )

    # Should transition to IDLE or safe state
    assert recovered_state.current_state == MomentumState.IDLE


# ============================================================================
# Metrics Tracking Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_metrics_tracking(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test metrics are tracked correctly."""
    # Perform transitions
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )
    await momentum_loop.process_event(
        sample_user_id,
        EventType.REWARD_EMITTED,
        {"reward": "Great!"}
    )

    # Check metrics
    assert "total_transitions" in momentum_loop.metrics
    assert momentum_loop.metrics["total_transitions"] >= 2

    assert "state_transitions" in momentum_loop.metrics
    assert "block_completed" in momentum_loop.metrics["state_transitions"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cycle_duration_tracking(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block,
    sample_bottleneck
):
    """Test cycle duration is tracked."""
    # Complete full cycle
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(sample_user_id, EventType.BLOCK_COMPLETED, {"block": sample_block})
    await momentum_loop.process_event(sample_user_id, EventType.REWARD_EMITTED, {"reward": "Good!"})
    await momentum_loop.process_event(sample_user_id, EventType.BOTTLENECK_CHECKED, {"bottleneck": sample_bottleneck})
    await momentum_loop.process_event(sample_user_id, EventType.REFRAME_COMPLETE, {"new_framing": "Test"})
    await momentum_loop.process_event(sample_user_id, EventType.GROWTH_STARTED, {"growth_task": "Learn"})
    await momentum_loop.process_event(sample_user_id, EventType.GROWTH_COMPLETED, {"growth_result": "Done"})

    # Check metrics
    loop_state = momentum_loop.active_loops[sample_user_id]
    assert loop_state.cycle_count == 1


# ============================================================================
# State Change Hooks Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_state_change_hooks(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test state change hooks are called."""
    hook_called = []

    def test_hook(user_id: str, old_state: MomentumState, new_state: MomentumState):
        hook_called.append({
            "user_id": user_id,
            "old_state": old_state,
            "new_state": new_state
        })

    # Register hook
    momentum_loop.register_state_change_hook(test_hook)

    # Trigger state change
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )

    # Check hook was called
    assert len(hook_called) > 0
    assert hook_called[-1]["user_id"] == sample_user_id
    assert hook_called[-1]["new_state"] == MomentumState.WIN_STRENGTH


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multiple_hooks(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test multiple hooks can be registered."""
    calls = {"hook1": 0, "hook2": 0}

    def hook1(user_id, old_state, new_state):
        calls["hook1"] += 1

    def hook2(user_id, old_state, new_state):
        calls["hook2"] += 1

    # Register both hooks
    momentum_loop.register_state_change_hook(hook1)
    momentum_loop.register_state_change_hook(hook2)

    # Trigger state change
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )

    # Both hooks should be called
    assert calls["hook1"] > 0
    assert calls["hook2"] > 0


# ============================================================================
# Edge Cases Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_for_nonexistent_user(momentum_loop):
    """Test processing event for user with no active loop."""
    with pytest.raises(KeyError):
        await momentum_loop.process_event(
            "nonexistent_user",
            EventType.BLOCK_COMPLETED,
            {"block": None}
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stop_loop(momentum_loop, sample_user_id, sample_personality):
    """Test stopping an active loop."""
    # Start loop
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    assert sample_user_id in momentum_loop.active_loops

    # Stop loop
    await momentum_loop.stop_loop(sample_user_id)

    # Should be removed from active loops
    assert sample_user_id not in momentum_loop.active_loops


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_loop_status(
    momentum_loop,
    sample_user_id,
    sample_personality,
    sample_block
):
    """Test getting loop status."""
    # Start and advance loop
    await momentum_loop.start_loop(sample_user_id, sample_personality)
    await momentum_loop.process_event(
        sample_user_id,
        EventType.BLOCK_COMPLETED,
        {"block": sample_block}
    )

    # Get status
    status = await momentum_loop.get_loop_status(sample_user_id)

    assert status is not None
    assert "current_state" in status
    assert "cycle_count" in status
    assert status["current_state"] == MomentumState.WIN_STRENGTH.value
