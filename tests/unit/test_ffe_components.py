"""
Unit Tests for FFE Components

Tests the core FFE components:
- GoalIngestor (front door for tasks and goals)
- TimeBlockManager (5-block plans and atomic blocks)
- GrowthScaffold (bottleneck detection and queuing)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from ai_pal.ffe.components import (
    GoalIngestor,
    TimeBlockManager,
    GrowthScaffold,
)
from ai_pal.ffe.models import (
    GoalPacket,
    GoalStatus,
    TaskComplexityLevel,
    AtomicBlock,
    BottleneckTask,
    BottleneckReason,
    SignatureStrength,
    StrengthType,
    TimeBlockSize,
)


# ============================================================================
# GoalIngestor Tests
# ============================================================================


@pytest.fixture
def goal_ingestor():
    """Create GoalIngestor instance"""
    return GoalIngestor()


@pytest.mark.asyncio
async def test_ingest_macro_goal(goal_ingestor):
    """Test ingesting a macro-level goal"""
    goal = await goal_ingestor.ingest_macro_goal(
        user_id="test-user",
        goal_description="Build a complete web application",
        from_personality_module=True,
    )

    assert goal is not None
    assert goal.user_id == "test-user"
    assert "web application" in goal.description.lower()
    assert goal.complexity_level == TaskComplexityLevel.MACRO
    assert goal.status == GoalStatus.PENDING
    assert goal.estimated_value > 0
    assert goal.value_effort_ratio > 0


@pytest.mark.asyncio
async def test_ingest_macro_goal_stores_in_memory(goal_ingestor):
    """Test that ingested goals are stored"""
    goal = await goal_ingestor.ingest_macro_goal(
        user_id="test-user",
        goal_description="Learn Python",
    )

    # Goal should be stored
    assert goal.goal_id in goal_ingestor.ingested_goals
    assert goal_ingestor.ingested_goals[goal.goal_id] == goal


@pytest.mark.asyncio
async def test_ingest_multiple_macro_goals(goal_ingestor):
    """Test ingesting multiple goals"""
    goals = []
    for i in range(5):
        goal = await goal_ingestor.ingest_macro_goal(
            user_id="test-user",
            goal_description=f"Goal {i}",
        )
        goals.append(goal)

    # All goals should be stored
    assert len(goal_ingestor.ingested_goals) == 5

    # Each goal should have unique ID
    goal_ids = {g.goal_id for g in goals}
    assert len(goal_ids) == 5


@pytest.mark.asyncio
async def test_ingest_macro_goal_higher_value_from_personality(goal_ingestor):
    """Test that personality-sourced goals have higher initial value"""
    goal_from_personality = await goal_ingestor.ingest_macro_goal(
        user_id="test-user",
        goal_description="Important goal from personality",
        from_personality_module=True,
    )

    goal_adhoc = await goal_ingestor.ingest_macro_goal(
        user_id="test-user",
        goal_description="Random ad-hoc goal",
        from_personality_module=False,
    )

    # Personality goals should have higher estimated value
    assert goal_from_personality.estimated_value > goal_adhoc.estimated_value


@pytest.mark.asyncio
async def test_ingest_adhoc_task(goal_ingestor):
    """Test ingesting an ad-hoc task"""
    task = await goal_ingestor.ingest_adhoc_task(
        user_id="test-user",
        task_description="Write README file",
        estimated_duration_minutes=30,
    )

    assert task is not None
    assert task.user_id == "test-user"
    assert "README" in task.description
    assert task.complexity_level == TaskComplexityLevel.SMALL
    assert task.status == GoalStatus.PENDING


@pytest.mark.asyncio
async def test_ingest_adhoc_task_without_duration(goal_ingestor):
    """Test ingesting ad-hoc task without duration estimate"""
    task = await goal_ingestor.ingest_adhoc_task(
        user_id="test-user",
        task_description="Quick task",
    )

    assert task is not None
    # Should still create a valid task
    assert task.complexity_level in [
        TaskComplexityLevel.ATOMIC,
        TaskComplexityLevel.SMALL,
    ]


@pytest.mark.asyncio
async def test_retrieve_goal(goal_ingestor):
    """Test retrieving a stored goal"""
    original = await goal_ingestor.ingest_macro_goal(
        user_id="test-user",
        goal_description="Test goal",
    )

    retrieved = await goal_ingestor.get_goal(original.goal_id)

    assert retrieved is not None
    assert retrieved.goal_id == original.goal_id
    assert retrieved.description == original.description


@pytest.mark.asyncio
async def test_retrieve_nonexistent_goal(goal_ingestor):
    """Test retrieving a goal that doesn't exist"""
    retrieved = await goal_ingestor.get_goal("nonexistent-id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_get_all_goals_for_user(goal_ingestor):
    """Test retrieving all goals for a specific user"""
    # Create goals for different users
    for user_id in ["user-1", "user-2"]:
        for i in range(3):
            await goal_ingestor.ingest_macro_goal(
                user_id=user_id,
                goal_description=f"Goal {i} for {user_id}",
            )

    # Get goals for user-1
    user1_goals = await goal_ingestor.get_user_goals("user-1")

    assert len(user1_goals) == 3
    assert all(g.user_id == "user-1" for g in user1_goals)


# ============================================================================
# TimeBlockManager Tests
# ============================================================================


@pytest.fixture
def time_block_manager():
    """Create TimeBlockManager instance"""
    return TimeBlockManager()


@pytest.fixture
def sample_macro_goal():
    """Create a sample macro goal"""
    return GoalPacket(
        goal_id="goal-1",
        user_id="test-user",
        description="Build full-stack application",
        complexity_level=TaskComplexityLevel.MACRO,
        status=GoalStatus.IN_PROGRESS,
        created_at=datetime.now(),
        estimated_value=0.9,
        estimated_effort=0.8,
    )


@pytest.mark.asyncio
async def test_create_five_block_plan(time_block_manager, sample_macro_goal):
    """Test creating a 5-block plan"""
    plan = await time_block_manager.create_five_block_plan(
        user_id="test-user",
        macro_goal=sample_macro_goal,
        total_months=5,
    )

    assert plan is not None
    assert len(plan.blocks) == 5
    assert len(plan.stop_points) == 5
    assert plan.macro_goal_id == sample_macro_goal.goal_id


@pytest.mark.asyncio
async def test_five_block_plan_dates(time_block_manager, sample_macro_goal):
    """Test that 5-block plan has correct date progression"""
    plan = await time_block_manager.create_five_block_plan(
        user_id="test-user",
        macro_goal=sample_macro_goal,
        total_months=5,
    )

    # Blocks should be sequential
    for i in range(4):
        block_end = datetime.fromisoformat(plan.blocks[i]["end_date"])
        next_block_start = datetime.fromisoformat(plan.blocks[i+1]["start_date"])

        # End of one block should be close to start of next
        time_diff = abs((next_block_start - block_end).days)
        assert time_diff <= 1  # Allow 1 day variance for date math


@pytest.mark.asyncio
async def test_five_block_plan_with_different_durations(time_block_manager, sample_macro_goal):
    """Test creating plans with different total durations"""
    durations = [5, 10, 15]

    for duration in durations:
        plan = await time_block_manager.create_five_block_plan(
            user_id="test-user",
            macro_goal=sample_macro_goal,
            total_months=duration,
        )

        # Should always have exactly 5 blocks
        assert len(plan.blocks) == 5

        # Total duration should match (approximately)
        first_start = datetime.fromisoformat(plan.blocks[0]["start_date"])
        last_end = datetime.fromisoformat(plan.blocks[4]["end_date"])
        total_days = (last_end - first_start).days
        expected_days = duration * 30

        # Allow 10% variance for date math
        assert abs(total_days - expected_days) / expected_days < 0.1


@pytest.mark.asyncio
async def test_create_atomic_block(time_block_manager):
    """Test creating an atomic time block"""
    block = await time_block_manager.create_atomic_block(
        user_id="test-user",
        task_description="Implement login feature",
        estimated_minutes=25,
        parent_goal_id="goal-1",
    )

    assert block is not None
    assert block.user_id == "test-user"
    assert "login" in block.description.lower()
    assert block.estimated_minutes == 25
    assert block.parent_goal_id == "goal-1"


@pytest.mark.asyncio
async def test_atomic_block_size_classification(time_block_manager):
    """Test that atomic blocks are classified by size"""
    # Tiny block (5-15 min)
    tiny = await time_block_manager.create_atomic_block(
        user_id="test-user",
        task_description="Quick fix",
        estimated_minutes=10,
    )
    assert tiny.time_block_size == TimeBlockSize.TINY

    # Small block (15-30 min)
    small = await time_block_manager.create_atomic_block(
        user_id="test-user",
        task_description="Small task",
        estimated_minutes=20,
    )
    assert small.time_block_size == TimeBlockSize.SMALL

    # Medium block (30-60 min)
    medium = await time_block_manager.create_atomic_block(
        user_id="test-user",
        task_description="Medium task",
        estimated_minutes=45,
    )
    assert medium.time_block_size == TimeBlockSize.MEDIUM

    # Large block (60+ min)
    large = await time_block_manager.create_atomic_block(
        user_id="test-user",
        task_description="Large task",
        estimated_minutes=90,
    )
    assert large.time_block_size == TimeBlockSize.LARGE


@pytest.mark.asyncio
async def test_get_atomic_block(time_block_manager):
    """Test retrieving an atomic block"""
    original = await time_block_manager.create_atomic_block(
        user_id="test-user",
        task_description="Test task",
        estimated_minutes=25,
    )

    retrieved = await time_block_manager.get_atomic_block(original.block_id)

    assert retrieved is not None
    assert retrieved.block_id == original.block_id
    assert retrieved.description == original.description


@pytest.mark.asyncio
async def test_get_user_blocks(time_block_manager):
    """Test retrieving all blocks for a user"""
    # Create blocks for multiple users
    for user_id in ["user-1", "user-2"]:
        for i in range(3):
            await time_block_manager.create_atomic_block(
                user_id=user_id,
                task_description=f"Task {i}",
                estimated_minutes=25,
            )

    user1_blocks = await time_block_manager.get_user_blocks("user-1")

    assert len(user1_blocks) == 3
    assert all(b.user_id == "user-1" for b in user1_blocks)


# ============================================================================
# GrowthScaffold Tests
# ============================================================================


@pytest.fixture
def growth_scaffold():
    """Create GrowthScaffold instance"""
    return GrowthScaffold()


@pytest.fixture
def sample_bottleneck():
    """Create a sample bottleneck task"""
    return BottleneckTask(
        bottleneck_id="bottleneck-1",
        user_id="test-user",
        task_description="Write unit tests",
        reason=BottleneckReason.AVOIDED,
        detected_at=datetime.now(),
        avoidance_count=5,
        last_avoided=datetime.now(),
    )


@pytest.mark.asyncio
async def test_detect_bottlenecks_empty(growth_scaffold):
    """Test detecting bottlenecks when none exist"""
    bottlenecks = await growth_scaffold.detect_bottlenecks(
        user_id="test-user",
        lookback_days=30,
    )

    assert bottlenecks == []


@pytest.mark.asyncio
async def test_register_bottleneck(growth_scaffold, sample_bottleneck):
    """Test registering a new bottleneck"""
    await growth_scaffold.register_bottleneck(sample_bottleneck)

    # Should be stored
    assert sample_bottleneck.bottleneck_id in growth_scaffold.detected_bottlenecks


@pytest.mark.asyncio
async def test_detect_bottlenecks_after_registration(growth_scaffold, sample_bottleneck):
    """Test detecting bottlenecks after registering them"""
    await growth_scaffold.register_bottleneck(sample_bottleneck)

    bottlenecks = await growth_scaffold.detect_bottlenecks(
        user_id="test-user",
        lookback_days=30,
    )

    assert len(bottlenecks) == 1
    assert bottlenecks[0].bottleneck_id == sample_bottleneck.bottleneck_id


@pytest.mark.asyncio
async def test_detect_bottlenecks_filters_by_user(growth_scaffold):
    """Test that bottleneck detection filters by user"""
    # Register bottlenecks for different users
    for user_id in ["user-1", "user-2"]:
        for i in range(3):
            bottleneck = BottleneckTask(
                bottleneck_id=f"{user_id}-bottleneck-{i}",
                user_id=user_id,
                task_description=f"Task {i}",
                reason=BottleneckReason.AVOIDED,
                detected_at=datetime.now(),
            )
            await growth_scaffold.register_bottleneck(bottleneck)

    # Get only user-1's bottlenecks
    user1_bottlenecks = await growth_scaffold.detect_bottlenecks(
        user_id="user-1",
        lookback_days=30,
    )

    assert len(user1_bottlenecks) == 3
    assert all(b.user_id == "user-1" for b in user1_bottlenecks)


@pytest.mark.asyncio
async def test_detect_bottlenecks_filters_by_time(growth_scaffold):
    """Test that bottleneck detection filters by lookback period"""
    # Create old bottleneck
    old_bottleneck = BottleneckTask(
        bottleneck_id="old-1",
        user_id="test-user",
        task_description="Old task",
        reason=BottleneckReason.AVOIDED,
        detected_at=datetime.now() - timedelta(days=60),  # 60 days old
    )

    # Create recent bottleneck
    recent_bottleneck = BottleneckTask(
        bottleneck_id="recent-1",
        user_id="test-user",
        task_description="Recent task",
        reason=BottleneckReason.AVOIDED,
        detected_at=datetime.now() - timedelta(days=10),  # 10 days old
    )

    await growth_scaffold.register_bottleneck(old_bottleneck)
    await growth_scaffold.register_bottleneck(recent_bottleneck)

    # Look back only 30 days
    bottlenecks = await growth_scaffold.detect_bottlenecks(
        user_id="test-user",
        lookback_days=30,
    )

    # Should only find the recent one
    assert len(bottlenecks) == 1
    assert bottlenecks[0].bottleneck_id == "recent-1"


@pytest.mark.asyncio
async def test_queue_bottleneck(growth_scaffold, sample_bottleneck):
    """Test queuing a bottleneck for reframing"""
    await growth_scaffold.queue_bottleneck(sample_bottleneck)

    # Should be in queue
    assert sample_bottleneck.bottleneck_id in growth_scaffold.bottleneck_queue


@pytest.mark.asyncio
async def test_get_next_bottleneck_empty_queue(growth_scaffold):
    """Test getting next bottleneck from empty queue"""
    next_bottleneck = await growth_scaffold.get_next_bottleneck("test-user")

    assert next_bottleneck is None


@pytest.mark.asyncio
async def test_get_next_bottleneck(growth_scaffold):
    """Test getting next bottleneck from queue"""
    # Queue multiple bottlenecks
    bottlenecks = []
    for i in range(3):
        bottleneck = BottleneckTask(
            bottleneck_id=f"bottleneck-{i}",
            user_id="test-user",
            task_description=f"Task {i}",
            reason=BottleneckReason.AVOIDED,
            detected_at=datetime.now(),
        )
        await growth_scaffold.register_bottleneck(bottleneck)
        await growth_scaffold.queue_bottleneck(bottleneck)
        bottlenecks.append(bottleneck)

    # Get next bottleneck
    next_bottleneck = await growth_scaffold.get_next_bottleneck("test-user")

    assert next_bottleneck is not None
    assert next_bottleneck.bottleneck_id == "bottleneck-0"  # First one queued


@pytest.mark.asyncio
async def test_get_next_bottleneck_removes_from_queue(growth_scaffold):
    """Test that getting next bottleneck removes it from queue"""
    bottleneck = BottleneckTask(
        bottleneck_id="bottleneck-1",
        user_id="test-user",
        task_description="Test task",
        reason=BottleneckReason.AVOIDED,
        detected_at=datetime.now(),
    )

    await growth_scaffold.register_bottleneck(bottleneck)
    await growth_scaffold.queue_bottleneck(bottleneck)

    # Queue should have 1 item
    assert len(growth_scaffold.bottleneck_queue) == 1

    # Get next bottleneck
    await growth_scaffold.get_next_bottleneck("test-user")

    # Queue should now be empty
    assert len(growth_scaffold.bottleneck_queue) == 0


@pytest.mark.asyncio
async def test_clear_resolved_bottleneck(growth_scaffold, sample_bottleneck):
    """Test clearing a resolved bottleneck"""
    await growth_scaffold.register_bottleneck(sample_bottleneck)

    # Mark as resolved
    await growth_scaffold.clear_bottleneck(sample_bottleneck.bottleneck_id)

    # Should no longer be in detected bottlenecks
    bottlenecks = await growth_scaffold.detect_bottlenecks(
        user_id="test-user",
        lookback_days=30,
    )

    assert len(bottlenecks) == 0


@pytest.mark.asyncio
async def test_bottleneck_reasons(growth_scaffold):
    """Test different bottleneck reasons"""
    reasons = [
        BottleneckReason.AVOIDED,
        BottleneckReason.STRUGGLED,
        BottleneckReason.INCOMPLETE,
    ]

    for i, reason in enumerate(reasons):
        bottleneck = BottleneckTask(
            bottleneck_id=f"bottleneck-{i}",
            user_id="test-user",
            task_description=f"Task {i}",
            reason=reason,
            detected_at=datetime.now(),
        )
        await growth_scaffold.register_bottleneck(bottleneck)

    bottlenecks = await growth_scaffold.detect_bottlenecks(
        user_id="test-user",
        lookback_days=30,
    )

    # Should have all three
    assert len(bottlenecks) == 3

    # Should have all different reasons
    detected_reasons = {b.reason for b in bottlenecks}
    assert len(detected_reasons) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
