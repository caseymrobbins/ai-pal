"""
Integration tests for Advanced ARI-FFE Integration.

Tests the three advanced integration systems:
- RealTimeBottleneckDetector: Real-time bottleneck detection from ARI snapshots
- AdaptiveDifficultyScaler: Adaptive difficulty scaling based on ARI metrics
- SkillAtrophyPrevention: Proactive skill atrophy prevention system
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from ai_pal.monitoring.ari_monitor import (
    ARIMonitor,
    AgencySnapshot,
    AgencyTrend,
)
from ai_pal.ffe.components.growth_scaffold import GrowthScaffold
from ai_pal.ffe.integration import (
    RealTimeBottleneckDetector,
    AdaptiveDifficultyScaler,
    SkillAtrophyPrevention,
    BottleneckSeverity,
)
from ai_pal.ffe.models import (
    BottleneckTask,
    BottleneckReason,
    TimeBlockSize,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_ari_dir(temp_dir):
    """Create temporary ARI directory structure."""
    ari_dir = temp_dir / "advanced_ari_ffe"
    ari_dir.mkdir()
    (ari_dir / "ari_snapshots").mkdir()
    return ari_dir


@pytest.fixture
def ari_monitor(temp_ari_dir):
    """Create ARI monitor."""
    return ARIMonitor(
        storage_dir=temp_ari_dir / "ari_snapshots",
        alert_threshold_delta_agency=-0.1,
        alert_threshold_bhir=0.8,
        alert_threshold_skill_loss=-0.15,
    )


@pytest.fixture
def growth_scaffold():
    """Create growth scaffold."""
    return GrowthScaffold()


@pytest.fixture
def real_time_detector(ari_monitor, growth_scaffold):
    """Create real-time bottleneck detector."""
    return RealTimeBottleneckDetector(
        ari_monitor=ari_monitor,
        growth_scaffold=growth_scaffold,
        skill_loss_threshold=-0.15,
        agency_loss_threshold=-0.1,
        high_reliance_threshold=0.9,
    )


@pytest.fixture
def difficulty_scaler(ari_monitor):
    """Create adaptive difficulty scaler."""
    return AdaptiveDifficultyScaler(
        ari_monitor=ari_monitor,
        lookback_days=14,
    )


@pytest.fixture
def atrophy_prevention(ari_monitor, growth_scaffold):
    """Create skill atrophy prevention system."""
    return SkillAtrophyPrevention(
        ari_monitor=ari_monitor,
        growth_scaffold=growth_scaffold,
        warning_days=14,
        critical_days=30,
    )


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "advanced_test_user"


# ============================================================================
# Helper Functions
# ============================================================================

async def create_snapshot(
    ari_monitor: ARIMonitor,
    user_id: str,
    task_type: str,
    delta_agency: float = 0.0,
    skill_development: float = 0.0,
    ai_reliance: float = 0.5,
    skill_after: float = 0.75,
    timestamp: datetime = None,
) -> AgencySnapshot:
    """Helper to create and record ARI snapshot."""
    if timestamp is None:
        timestamp = datetime.now()

    snapshot = AgencySnapshot(
        timestamp=timestamp,
        task_id=f"task_{timestamp.timestamp()}",
        task_type=task_type,
        delta_agency=delta_agency,
        bhir=0.9,
        task_efficacy=0.85,
        user_skill_before=skill_after - skill_development,
        user_skill_after=skill_after,
        skill_development=skill_development,
        ai_reliance=ai_reliance,
        autonomy_retention=1.0 - ai_reliance,
        user_id=user_id,
        session_id="test_session",
    )

    await ari_monitor.record_snapshot(snapshot)
    return snapshot


# ============================================================================
# RealTimeBottleneckDetector Tests
# ============================================================================

@pytest.mark.asyncio
async def test_real_time_detector_skill_loss(
    real_time_detector, ari_monitor, growth_scaffold, test_user_id
):
    """Test that skill loss triggers bottleneck creation."""
    # Create snapshot with severe skill loss
    snapshot = await create_snapshot(
        ari_monitor,
        test_user_id,
        "coding",
        skill_development=-0.2,  # Below threshold of -0.15
        skill_after=0.6,
    )

    # Analyze snapshot
    bottleneck = await real_time_detector.analyze_snapshot(snapshot)

    # Should create bottleneck
    assert bottleneck is not None
    assert bottleneck.user_id == test_user_id
    assert bottleneck.task_category == "coding"
    assert bottleneck.bottleneck_reason == BottleneckReason.SKILL_DEFICIT
    assert bottleneck.detection_method == "real_time_ari_monitor"

    # Should be queued to growth scaffold
    queued = await growth_scaffold.get_next_bottleneck(test_user_id)
    assert queued is not None
    assert queued.bottleneck_id == bottleneck.bottleneck_id


@pytest.mark.asyncio
async def test_real_time_detector_agency_loss(
    real_time_detector, ari_monitor, test_user_id
):
    """Test that agency loss triggers bottleneck creation."""
    snapshot = await create_snapshot(
        ari_monitor,
        test_user_id,
        "writing",
        delta_agency=-0.15,  # Below threshold of -0.1
        skill_after=0.7,
    )

    bottleneck = await real_time_detector.analyze_snapshot(snapshot)

    assert bottleneck is not None
    assert bottleneck.bottleneck_reason == BottleneckReason.ANXIETY_INDUCING


@pytest.mark.asyncio
async def test_real_time_detector_high_reliance(
    real_time_detector, ari_monitor, test_user_id
):
    """Test that high AI reliance triggers bottleneck creation."""
    snapshot = await create_snapshot(
        ari_monitor,
        test_user_id,
        "debugging",
        ai_reliance=0.95,  # Above threshold of 0.9
        skill_after=0.5,
    )

    bottleneck = await real_time_detector.analyze_snapshot(snapshot)

    assert bottleneck is not None
    assert bottleneck.bottleneck_reason == BottleneckReason.DEPENDENCY


@pytest.mark.asyncio
async def test_real_time_detector_no_bottleneck(
    real_time_detector, ari_monitor, test_user_id
):
    """Test that healthy metrics don't trigger bottleneck."""
    snapshot = await create_snapshot(
        ari_monitor,
        test_user_id,
        "testing",
        delta_agency=0.05,  # Positive
        skill_development=0.1,  # Positive
        ai_reliance=0.5,  # Moderate
        skill_after=0.8,
    )

    bottleneck = await real_time_detector.analyze_snapshot(snapshot)

    assert bottleneck is None


@pytest.mark.asyncio
async def test_real_time_detector_duplicate_prevention(
    real_time_detector, ari_monitor, test_user_id
):
    """Test that duplicate bottlenecks aren't created."""
    # Create first bottleneck
    snapshot1 = await create_snapshot(
        ari_monitor,
        test_user_id,
        "coding",
        skill_development=-0.2,
    )
    bottleneck1 = await real_time_detector.analyze_snapshot(snapshot1)
    assert bottleneck1 is not None

    # Try to create another for same task type
    snapshot2 = await create_snapshot(
        ari_monitor,
        test_user_id,
        "coding",
        skill_development=-0.25,
    )
    bottleneck2 = await real_time_detector.analyze_snapshot(snapshot2)

    # Should not create duplicate
    assert bottleneck2 is None


@pytest.mark.asyncio
async def test_real_time_detector_severity_calculation(
    real_time_detector, ari_monitor, test_user_id
):
    """Test severity calculation for bottlenecks."""
    # Create high-severity snapshot
    snapshot = await create_snapshot(
        ari_monitor,
        test_user_id,
        "design",
        delta_agency=-0.2,
        skill_development=-0.3,
        ai_reliance=0.95,
        skill_after=0.3,  # Very low skill
    )

    bottleneck = await real_time_detector.analyze_snapshot(snapshot)

    assert bottleneck is not None
    # High severity due to low skill, high reliance, agency loss
    assert bottleneck.skill_gap_severity >= 0.5


@pytest.mark.asyncio
async def test_real_time_detector_reset(
    real_time_detector, ari_monitor, test_user_id
):
    """Test resetting created bottlenecks tracking."""
    # Create bottleneck
    snapshot = await create_snapshot(
        ari_monitor,
        test_user_id,
        "coding",
        skill_development=-0.2,
    )
    bottleneck1 = await real_time_detector.analyze_snapshot(snapshot)
    assert bottleneck1 is not None

    # Reset for this user
    real_time_detector.reset_created_bottlenecks(test_user_id)

    # Now should be able to create again
    snapshot2 = await create_snapshot(
        ari_monitor,
        test_user_id,
        "coding",
        skill_development=-0.25,
    )
    bottleneck2 = await real_time_detector.analyze_snapshot(snapshot2)
    assert bottleneck2 is not None


# ============================================================================
# AdaptiveDifficultyScaler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_difficulty_scaler_high_performance(
    difficulty_scaler, ari_monitor, test_user_id
):
    """Test difficulty scaling for high-performing user."""
    # Create multiple snapshots showing good performance
    now = datetime.now()
    for i in range(10):
        await create_snapshot(
            ari_monitor,
            test_user_id,
            "coding",
            delta_agency=0.05,
            skill_development=0.1,
            ai_reliance=0.3,
            skill_after=0.85,
            timestamp=now - timedelta(days=10-i),
        )

    difficulty = await difficulty_scaler.calculate_optimal_difficulty(test_user_id)

    # Should recommend challenging tasks
    assert difficulty["performance_score"] >= 0.7
    assert difficulty["complexity"] == "challenging"
    assert difficulty["time_block_size"] == TimeBlockSize.LARGE
    assert difficulty["growth_task_ratio"] >= 0.4


@pytest.mark.asyncio
async def test_difficulty_scaler_low_performance(
    difficulty_scaler, ari_monitor, test_user_id
):
    """Test difficulty scaling for struggling user."""
    # Create snapshots showing poor performance
    now = datetime.now()
    for i in range(10):
        await create_snapshot(
            ari_monitor,
            test_user_id,
            "writing",
            delta_agency=-0.05,
            skill_development=-0.1,
            ai_reliance=0.85,
            skill_after=0.4,
            timestamp=now - timedelta(days=10-i),
        )

    difficulty = await difficulty_scaler.calculate_optimal_difficulty(test_user_id)

    # Should recommend easier tasks
    assert difficulty["performance_score"] <= 0.4
    assert difficulty["complexity"] in ["easy", "comfortable"]
    assert difficulty["time_block_size"] in [TimeBlockSize.TINY, TimeBlockSize.SMALL]
    assert difficulty["growth_task_ratio"] <= 0.3


@pytest.mark.asyncio
async def test_difficulty_scaler_moderate_performance(
    difficulty_scaler, ari_monitor, test_user_id
):
    """Test difficulty scaling for moderate performance."""
    now = datetime.now()
    for i in range(10):
        await create_snapshot(
            ari_monitor,
            test_user_id,
            "testing",
            delta_agency=0.0,
            skill_development=0.0,
            ai_reliance=0.6,
            skill_after=0.65,
            timestamp=now - timedelta(days=10-i),
        )

    difficulty = await difficulty_scaler.calculate_optimal_difficulty(test_user_id)

    # Should recommend moderate difficulty
    assert 0.4 <= difficulty["performance_score"] <= 0.7
    assert difficulty["complexity"] in ["moderate", "comfortable"]
    assert difficulty["time_block_size"] in [TimeBlockSize.SMALL, TimeBlockSize.MEDIUM]


@pytest.mark.asyncio
async def test_difficulty_scaler_category_specific(
    difficulty_scaler, ari_monitor, test_user_id
):
    """Test category-specific difficulty calculation."""
    now = datetime.now()

    # Good at coding
    for i in range(5):
        await create_snapshot(
            ari_monitor,
            test_user_id,
            "coding",
            skill_development=0.1,
            ai_reliance=0.3,
            timestamp=now - timedelta(days=5-i),
        )

    # Bad at design
    for i in range(5):
        await create_snapshot(
            ari_monitor,
            test_user_id,
            "design",
            skill_development=-0.15,
            ai_reliance=0.9,
            timestamp=now - timedelta(days=5-i),
        )

    # Check coding difficulty
    coding_diff = await difficulty_scaler.calculate_optimal_difficulty(
        test_user_id, task_category="coding"
    )
    assert coding_diff["performance_score"] >= 0.5

    # Check design difficulty
    design_diff = await difficulty_scaler.calculate_optimal_difficulty(
        test_user_id, task_category="design"
    )
    assert design_diff["performance_score"] <= 0.4


@pytest.mark.asyncio
async def test_difficulty_scaler_no_data(
    difficulty_scaler, test_user_id
):
    """Test default settings when no data available."""
    difficulty = await difficulty_scaler.calculate_optimal_difficulty(test_user_id)

    # Should return defaults
    assert difficulty["performance_score"] == 0.5
    assert difficulty["complexity"] == "moderate"
    assert difficulty["time_block_size"] == TimeBlockSize.SMALL
    assert "No historical data" in difficulty["recommendation"]


# ============================================================================
# SkillAtrophyPrevention Tests
# ============================================================================

@pytest.mark.asyncio
async def test_atrophy_detection_unused_skill(
    atrophy_prevention, ari_monitor, test_user_id
):
    """Test detection of unused skills."""
    # Create snapshot for skill used 20 days ago
    old_date = datetime.now() - timedelta(days=20)
    await create_snapshot(
        ari_monitor,
        test_user_id,
        "video_editing",
        skill_after=0.8,
        timestamp=old_date,
    )

    declining = await atrophy_prevention.detect_declining_skills(test_user_id)

    # Should detect as unused (>14 days)
    assert len(declining) == 1
    assert declining[0]["skill_category"] == "video_editing"
    assert declining[0]["days_since_use"] == 20
    assert declining[0]["status"] == "warning"


@pytest.mark.asyncio
async def test_atrophy_detection_critical_skill(
    atrophy_prevention, ari_monitor, test_user_id
):
    """Test detection of critically unused skills."""
    # Create snapshot for skill used 35 days ago
    old_date = datetime.now() - timedelta(days=35)
    await create_snapshot(
        ari_monitor,
        test_user_id,
        "public_speaking",
        skill_after=0.75,
        timestamp=old_date,
    )

    declining = await atrophy_prevention.detect_declining_skills(test_user_id)

    # Should detect as critical (>30 days)
    assert len(declining) == 1
    assert declining[0]["status"] == "critical"
    assert declining[0]["practice_urgency"] >= 0.5


@pytest.mark.asyncio
async def test_atrophy_detection_declining_skill(
    atrophy_prevention, ari_monitor, test_user_id
):
    """Test detection of actively declining skills."""
    now = datetime.now()

    # Create snapshots showing skill decline
    for i, skill_level in enumerate([0.8, 0.75, 0.7, 0.65, 0.6]):
        await create_snapshot(
            ari_monitor,
            test_user_id,
            "negotiation",
            skill_after=skill_level,
            timestamp=now - timedelta(days=5-i),
        )

    declining = await atrophy_prevention.detect_declining_skills(test_user_id)

    # Should detect declining skill
    assert len(declining) >= 1
    skill = next(s for s in declining if s["skill_category"] == "negotiation")
    assert skill["skill_change"] < -0.1
    assert skill["status"] in ["declining", "warning"]


@pytest.mark.asyncio
async def test_practice_suggestions_generation(
    atrophy_prevention, ari_monitor, test_user_id
):
    """Test generation of practice suggestions."""
    # Create unused skills
    old_date = datetime.now() - timedelta(days=20)
    await create_snapshot(ari_monitor, test_user_id, "skill_a", timestamp=old_date)
    await create_snapshot(ari_monitor, test_user_id, "skill_b", timestamp=old_date - timedelta(days=5))
    await create_snapshot(ari_monitor, test_user_id, "skill_c", timestamp=old_date - timedelta(days=10))

    suggestions = await atrophy_prevention.generate_practice_suggestions(
        test_user_id, max_suggestions=2
    )

    # Should generate suggestions (max 2)
    assert len(suggestions) == 2
    assert all("suggested_task" in s for s in suggestions)
    assert all("rationale" in s for s in suggestions)
    assert all(s["time_block_size"] == TimeBlockSize.SMALL for s in suggestions)


@pytest.mark.asyncio
async def test_practice_task_queuing(
    atrophy_prevention, ari_monitor, growth_scaffold, test_user_id
):
    """Test queueing practice tasks to Growth Scaffold."""
    # Create unused skill
    old_date = datetime.now() - timedelta(days=25)
    await create_snapshot(
        ari_monitor,
        test_user_id,
        "presentation_skills",
        skill_after=0.8,
        timestamp=old_date,
    )

    # Queue practice tasks
    queued = await atrophy_prevention.queue_practice_tasks(test_user_id, max_tasks=1)

    # Should queue one task
    assert len(queued) == 1
    assert queued[0].task_category == "presentation_skills"
    assert queued[0].detection_method == "skill_atrophy_prevention"

    # Should be in growth scaffold queue
    next_bottleneck = await growth_scaffold.get_next_bottleneck(test_user_id)
    assert next_bottleneck is not None
    assert next_bottleneck.bottleneck_id == queued[0].bottleneck_id


@pytest.mark.asyncio
async def test_practice_urgency_calculation(
    atrophy_prevention, ari_monitor, test_user_id
):
    """Test practice urgency prioritization."""
    now = datetime.now()

    # High-level skill unused for long time (high urgency)
    await create_snapshot(
        ari_monitor,
        test_user_id,
        "advanced_skill",
        skill_after=0.9,
        timestamp=now - timedelta(days=28),
    )

    # Low-level skill unused for short time (low urgency)
    await create_snapshot(
        ari_monitor,
        test_user_id,
        "basic_skill",
        skill_after=0.4,
        timestamp=now - timedelta(days=15),
    )

    declining = await atrophy_prevention.detect_declining_skills(test_user_id)

    # Advanced skill should have higher urgency
    advanced = next(s for s in declining if s["skill_category"] == "advanced_skill")
    basic = next(s for s in declining if s["skill_category"] == "basic_skill")

    assert advanced["practice_urgency"] > basic["practice_urgency"]


@pytest.mark.asyncio
async def test_skill_trends_visualization(
    atrophy_prevention, ari_monitor, test_user_id
):
    """Test skill trend data generation for visualization."""
    now = datetime.now()

    # Create trend data
    skill_levels = [0.5, 0.55, 0.6, 0.65, 0.7]
    for i, level in enumerate(skill_levels):
        await create_snapshot(
            ari_monitor,
            test_user_id,
            "data_analysis",
            skill_after=level,
            timestamp=now - timedelta(days=5-i),
        )

    trends = await atrophy_prevention.get_skill_trends(
        test_user_id, "data_analysis"
    )

    # Should return trend data
    assert trends["task_category"] == "data_analysis"
    assert trends["data_points"] == 5
    assert len(trends["skill_levels"]) == 5
    assert trends["trend_direction"] == "improving"  # Skill increasing
    assert trends["current_level"] == 0.7
    assert trends["days_since_last"] == 0


@pytest.mark.asyncio
async def test_no_declining_skills(
    atrophy_prevention, ari_monitor, test_user_id
):
    """Test when no skills are declining."""
    # Create recent, healthy snapshots
    now = datetime.now()
    for i in range(5):
        await create_snapshot(
            ari_monitor,
            test_user_id,
            "coding",
            skill_after=0.8,
            timestamp=now - timedelta(days=i),
        )

    declining = await atrophy_prevention.detect_declining_skills(test_user_id)

    # Should find no declining skills
    assert len(declining) == 0


# ============================================================================
# Integration Tests (All Systems Working Together)
# ============================================================================

@pytest.mark.asyncio
async def test_full_integration_workflow(
    ari_monitor,
    growth_scaffold,
    real_time_detector,
    difficulty_scaler,
    atrophy_prevention,
    test_user_id
):
    """Test full workflow of all advanced integration systems."""
    now = datetime.now()

    # Step 1: User performs tasks with declining performance
    for i in range(10):
        snapshot = await create_snapshot(
            ari_monitor,
            test_user_id,
            "coding",
            delta_agency=-0.05,
            skill_development=-0.1 - (i * 0.01),  # Getting worse
            ai_reliance=0.7 + (i * 0.02),  # Increasing reliance
            skill_after=0.7 - (i * 0.02),  # Skill dropping
            timestamp=now - timedelta(days=10-i),
        )

        # Real-time detector analyzes each snapshot
        bottleneck = await real_time_detector.analyze_snapshot(snapshot)

        # Should eventually trigger (when thresholds exceeded)
        if i >= 5:  # After sufficient decline
            if bottleneck:
                print(f"Bottleneck created on iteration {i}")

    # Step 2: Check adaptive difficulty recommendation
    difficulty = await difficulty_scaler.calculate_optimal_difficulty(test_user_id)
    assert difficulty["performance_score"] < 0.5
    assert difficulty["complexity"] in ["easy", "comfortable"]
    assert difficulty["recommendation"]

    # Step 3: Create old skill for atrophy prevention
    await create_snapshot(
        ari_monitor,
        test_user_id,
        "design",
        skill_after=0.8,
        timestamp=now - timedelta(days=25),
    )

    # Step 4: Detect and queue practice tasks
    practice_tasks = await atrophy_prevention.queue_practice_tasks(
        test_user_id, max_tasks=1
    )
    assert len(practice_tasks) >= 1

    # Step 5: Verify Growth Scaffold has bottlenecks queued
    queued_count = growth_scaffold.get_bottleneck_count(test_user_id)
    assert queued_count > 0

    # Full integration verified: real-time detection, difficulty scaling,
    # and atrophy prevention all working together
