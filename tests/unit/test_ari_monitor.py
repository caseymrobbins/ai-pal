"""
Unit Tests for ARI Monitor

Tests the Agency Retention Index monitoring system including:
- Snapshot recording and retrieval
- Trend analysis
- Alert detection
- Metric calculations
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from ai_pal.monitoring.ari_monitor import (
    ARIMonitor,
    AgencySnapshot,
    ARITrend,
    ARIAlert,
    AlertSeverity,
)


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    return tmp_path / "ari_test"


@pytest.fixture
def ari_monitor(temp_storage):
    """Create ARI monitor instance"""
    return ARIMonitor(storage_dir=temp_storage)


@pytest.fixture
def sample_snapshot():
    """Create a sample agency snapshot"""
    return AgencySnapshot(
        timestamp=datetime.now(),
        task_id="task-1",
        task_type="coding",
        delta_agency=0.1,
        bhir=1.5,
        task_efficacy=0.9,
        user_skill_before=0.7,
        user_skill_after=0.75,
        skill_development=0.05,
        ai_reliance=0.5,
        autonomy_retention=0.8,
        user_id="test-user",
        session_id="session-1",
    )


# ============================================================================
# Snapshot Recording Tests
# ============================================================================


@pytest.mark.asyncio
async def test_record_snapshot(ari_monitor, sample_snapshot):
    """Test recording an agency snapshot"""
    await ari_monitor.record_snapshot(sample_snapshot)

    # Verify snapshot was recorded - direct dict access
    snapshots = ari_monitor.snapshots.get("test-user", [])
    assert len(snapshots) == 1
    assert snapshots[0].task_id == "task-1"
    assert snapshots[0].delta_agency == 0.1


@pytest.mark.asyncio
async def test_record_multiple_snapshots(ari_monitor):
    """Test recording multiple snapshots"""
    for i in range(5):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1 * i,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.75,
            skill_development=0.05,
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    snapshots = ari_monitor.snapshots.get("test-user", [])
    assert len(snapshots) == 5


# ============================================================================
# Snapshot Retrieval Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_snapshots_by_user(ari_monitor):
    """Test retrieving snapshots for specific user"""
    # Record snapshots for different users
    for user_id in ["user-1", "user-2"]:
        snapshot = AgencySnapshot(
            timestamp=datetime.now(),
            task_id=f"task-{user_id}",
            task_type="coding",
            delta_agency=0.1,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.75,
            skill_development=0.05,
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id=user_id,
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Retrieve for user-1 only - direct dict access
    snapshots = ari_monitor.snapshots.get("user-1", [])
    assert len(snapshots) == 1
    assert snapshots[0].user_id == "user-1"


@pytest.mark.asyncio
async def test_get_snapshots_with_time_range(ari_monitor):
    """Test retrieving snapshots within time range"""
    now = datetime.now()

    # Record snapshots at different times
    for i in range(5):
        snapshot = AgencySnapshot(
            timestamp=now - timedelta(days=i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.75,
            skill_development=0.05,
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Retrieve only last 2 days using generate_report
    report = ari_monitor.generate_report(
        user_id="test-user",
        start_date=now - timedelta(days=2),
        end_date=now
    )

    # Report should contain snapshots from the time range
    assert report.snapshot_count <= 3  # Day 0, 1, 2


# ============================================================================
# Trend Analysis Tests
# ============================================================================


@pytest.mark.asyncio
async def test_calculate_trend_positive(ari_monitor):
    """Test trend calculation with improving agency"""
    # Record snapshots with increasing agency
    for i in range(10):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=10-i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1 + (i * 0.01),  # Increasing
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.75,
            skill_development=0.05 + (i * 0.01),  # Increasing
            ai_reliance=0.5 - (i * 0.01),  # Decreasing (good)
            autonomy_retention=0.8 + (i * 0.01),  # Increasing
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Use generate_report to get trend analysis
    report = ari_monitor.generate_report(user_id="test-user")

    assert report is not None
    # Should show INCREASING or STABLE trend
    from ai_pal.monitoring.ari_monitor import AgencyTrend
    assert report.agency_trend in [AgencyTrend.INCREASING, AgencyTrend.STABLE]


@pytest.mark.asyncio
async def test_calculate_trend_declining(ari_monitor):
    """Test trend calculation with declining agency"""
    # Record snapshots with decreasing agency
    for i in range(10):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=10-i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1 - (i * 0.01),  # Decreasing
            bhir=1.5,
            task_efficacy=0.9 - (i * 0.02),  # Decreasing
            user_skill_before=0.7,
            user_skill_after=0.75 - (i * 0.02),  # Decreasing
            skill_development=0.05 - (i * 0.005),  # Decreasing
            ai_reliance=0.5 + (i * 0.02),  # Increasing (bad)
            autonomy_retention=0.8 - (i * 0.02),  # Decreasing
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Use generate_report to get trend analysis
    report = ari_monitor.generate_report(user_id="test-user")

    assert report is not None
    # Should show DECREASING or CRITICAL trend
    from ai_pal.monitoring.ari_monitor import AgencyTrend
    assert report.agency_trend in [AgencyTrend.DECREASING, AgencyTrend.CRITICAL]


# ============================================================================
# Alert Detection Tests
# ============================================================================


@pytest.mark.asyncio
async def test_detect_high_ai_reliance_alert(ari_monitor):
    """Test alert detection for high AI reliance"""
    # Record snapshots with high AI reliance
    for i in range(5):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=5-i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.05,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.7,
            skill_development=0.0,
            ai_reliance=0.95,  # Very high
            autonomy_retention=0.3,  # Low
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Alerts are included in reports
    report = ari_monitor.generate_report(user_id="test-user")

    assert len(report.alerts) > 0
    # Should have alert about AI dependency
    assert any("dependency" in alert.lower() or "reliance" in alert.lower() for alert in report.alerts)


@pytest.mark.asyncio
async def test_detect_skill_stagnation_alert(ari_monitor):
    """Test alert detection for skill stagnation"""
    # Record snapshots with no skill development
    for i in range(10):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(days=i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.05,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.7,  # No improvement
            skill_development=0.0,  # Stagnant
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Alerts are included in reports
    report = ari_monitor.generate_report(user_id="test-user")

    assert len(report.alerts) > 0
    # Should have alert about skill issues
    assert any("skill" in alert.lower() for alert in report.alerts)


@pytest.mark.asyncio
async def test_no_alerts_for_healthy_metrics(ari_monitor):
    """Test no alerts when metrics are healthy"""
    # Record snapshots with healthy metrics
    for i in range(5):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=5-i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.75,
            skill_development=0.05,
            ai_reliance=0.5,  # Moderate
            autonomy_retention=0.8,  # Good
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Check alerts in report
    report = ari_monitor.generate_report(user_id="test-user")

    # Should have no or minimal alerts for healthy metrics
    # (May have some recommendations but not critical alerts)
    assert len(report.alerts) <= 1


# ============================================================================
# Metric Calculation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_calculate_average_metrics(ari_monitor):
    """Test calculation of average metrics"""
    # Record snapshots
    for i in range(5):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=5-i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.75,
            skill_development=0.05,
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Use get_user_summary for statistics
    summary = ari_monitor.get_user_summary(user_id="test-user")

    assert summary is not None
    assert "average_delta_agency" in summary
    assert "average_ai_reliance" in summary
    assert "average_skill_development" in summary
    assert summary["average_delta_agency"] == pytest.approx(0.1, rel=0.01)
    assert summary["average_ai_reliance"] == pytest.approx(0.5, rel=0.01)


@pytest.mark.asyncio
async def test_persistence(ari_monitor, sample_snapshot):
    """Test that snapshots persist across monitor instances"""
    # Record snapshot
    await ari_monitor.record_snapshot(sample_snapshot)

    # Create new monitor instance with same storage
    new_monitor = ARIMonitor(storage_dir=ari_monitor.storage_dir)

    # Should be able to retrieve snapshot - direct dict access
    snapshots = new_monitor.snapshots.get("test-user", [])
    assert len(snapshots) == 1
    assert snapshots[0].task_id == "task-1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
