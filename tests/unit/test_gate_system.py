"""
Unit Tests for Gate System

Tests the 4-gate validation system:
- Gate 1: Net Agency (no user deskilling)
- Gate 2: Extraction Static Analysis (no dark patterns)
- Gate 3: Humanity Override (user can always override)
- Gate 4: Performance Parity (with-AI ≈ without-AI)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from ai_pal.gates.gate_system import (
    GateSystem,
    GateResult,
    GateStatus,
    GateViolation,
)
from ai_pal.monitoring.ari_monitor import AgencySnapshot


@pytest.fixture
def gate_system():
    """Create gate system instance"""
    return GateSystem()


# ============================================================================
# Gate 1: Net Agency Tests
# ============================================================================


@pytest.mark.asyncio
async def test_gate1_passes_with_positive_skill_development(gate_system):
    """Test Gate 1 passes when user skills improve"""
    snapshots = [
        AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7 + (i * 0.01),
            user_skill_after=0.75 + (i * 0.01),
            skill_development=0.05,  # Positive skill growth
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id="test-user",
            session_id="session-1",
        )
        for i in range(10)
    ]

    result = await gate_system.evaluate_gate1(snapshots)

    assert result.status == GateStatus.PASS
    assert result.gate_name == "Net Agency"


@pytest.mark.asyncio
async def test_gate1_fails_with_skill_decline(gate_system):
    """Test Gate 1 fails when user skills decline"""
    snapshots = [
        AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=-0.05,
            bhir=1.5,
            task_efficacy=0.6,
            user_skill_before=0.7 - (i * 0.02),
            user_skill_after=0.65 - (i * 0.02),
            skill_development=-0.05,  # Negative skill growth (deskilling)
            ai_reliance=0.9,  # High reliance
            autonomy_retention=0.4,  # Low autonomy
            user_id="test-user",
            session_id="session-1",
        )
        for i in range(10)
    ]

    result = await gate_system.evaluate_gate1(snapshots)

    assert result.status == GateStatus.FAIL
    assert len(result.violations) > 0
    assert any("skill" in v.description.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_gate1_warns_on_stagnation(gate_system):
    """Test Gate 1 warns when skills stagnate"""
    snapshots = [
        AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.0,
            bhir=1.5,
            task_efficacy=0.8,
            user_skill_before=0.7,
            user_skill_after=0.7,  # No change
            skill_development=0.0,  # Stagnant
            ai_reliance=0.6,
            autonomy_retention=0.7,
            user_id="test-user",
            session_id="session-1",
        )
        for i in range(10)
    ]

    result = await gate_system.evaluate_gate1(snapshots)

    # Should warn but not necessarily fail
    assert result.status in [GateStatus.WARN, GateStatus.PASS]
    if result.status == GateStatus.WARN:
        assert any("stagnation" in v.description.lower() for v in result.violations)


# ============================================================================
# Gate 2: Extraction Static Analysis Tests
# ============================================================================


@pytest.mark.asyncio
async def test_gate2_passes_with_clean_code(gate_system):
    """Test Gate 2 passes with code free of dark patterns"""
    code = """
    def calculate_total(items):
        return sum(item.price for item in items)

    def process_order(order):
        total = calculate_total(order.items)
        return {"total": total, "status": "processed"}
    """

    result = await gate_system.evaluate_gate2(code)

    assert result.status == GateStatus.PASS
    assert result.gate_name == "Extraction Static Analysis"


@pytest.mark.asyncio
async def test_gate2_fails_with_dark_pattern_language(gate_system):
    """Test Gate 2 detects dark pattern language"""
    code = """
    # YOU MUST use this feature daily or your account will be downgraded
    def force_user_action():
        if not user.used_today:
            show_modal("You should really use this feature!")
            disable_account_access()  # Coercive pattern
    """

    result = await gate_system.evaluate_gate2(code)

    # Should at least warn about coercive language
    assert result.status in [GateStatus.WARN, GateStatus.FAIL]
    assert len(result.violations) > 0


@pytest.mark.asyncio
async def test_gate2_detects_manipulative_patterns(gate_system):
    """Test Gate 2 detects manipulative UI patterns"""
    code = """
    def show_upgrade_modal():
        # Make "No" button tiny and hard to click
        no_button_size = "2px"
        yes_button_size = "200px"

        # Shame user for declining
        if user_clicks_no:
            show_message("You're missing out on amazing features!")
    """

    result = await gate_system.evaluate_gate2(code)

    assert result.status in [GateStatus.WARN, GateStatus.FAIL]


# ============================================================================
# Gate 3: Humanity Override Tests
# ============================================================================


@pytest.mark.asyncio
async def test_gate3_passes_with_override_capability(gate_system):
    """Test Gate 3 passes when AI decisions can be overridden"""
    # Simulate code with override mechanisms
    system_config = {
        "ai_decision_override": True,
        "user_can_reject_suggestions": True,
        "manual_mode_available": True,
        "ai_assistance_optional": True,
    }

    result = await gate_system.evaluate_gate3(system_config)

    assert result.status == GateStatus.PASS
    assert result.gate_name == "Humanity Override"


@pytest.mark.asyncio
async def test_gate3_fails_without_override(gate_system):
    """Test Gate 3 fails when user cannot override AI"""
    # Simulate forced AI decisions
    system_config = {
        "ai_decision_override": False,
        "user_can_reject_suggestions": False,
        "manual_mode_available": False,
        "ai_assistance_optional": False,
    }

    result = await gate_system.evaluate_gate3(system_config)

    assert result.status == GateStatus.FAIL
    assert len(result.violations) > 0
    assert any("override" in v.description.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_gate3_requires_manual_fallback(gate_system):
    """Test Gate 3 requires manual mode fallback"""
    system_config = {
        "ai_decision_override": True,
        "user_can_reject_suggestions": True,
        "manual_mode_available": False,  # No manual fallback
        "ai_assistance_optional": True,
    }

    result = await gate_system.evaluate_gate3(system_config)

    # Should at least warn about lack of manual fallback
    assert result.status in [GateStatus.WARN, GateStatus.FAIL]


# ============================================================================
# Gate 4: Performance Parity Tests
# ============================================================================


@pytest.mark.asyncio
async def test_gate4_passes_with_comparable_performance(gate_system):
    """Test Gate 4 passes when with-AI ≈ without-AI performance"""
    # Simulate comparable performance
    with_ai_metrics = {
        "task_completion_time": 100,
        "error_rate": 0.05,
        "quality_score": 0.9,
        "user_satisfaction": 0.85,
    }

    without_ai_metrics = {
        "task_completion_time": 105,  # Slightly slower without AI
        "error_rate": 0.06,
        "quality_score": 0.88,
        "user_satisfaction": 0.83,
    }

    result = await gate_system.evaluate_gate4(with_ai_metrics, without_ai_metrics)

    assert result.status == GateStatus.PASS
    assert result.gate_name == "Performance Parity"


@pytest.mark.asyncio
async def test_gate4_fails_with_significant_degradation(gate_system):
    """Test Gate 4 fails when without-AI performance degrades significantly"""
    with_ai_metrics = {
        "task_completion_time": 100,
        "error_rate": 0.05,
        "quality_score": 0.9,
        "user_satisfaction": 0.85,
    }

    without_ai_metrics = {
        "task_completion_time": 300,  # 3x slower without AI (dependency)
        "error_rate": 0.30,  # 6x more errors
        "quality_score": 0.50,  # Much worse quality
        "user_satisfaction": 0.40,  # Much less satisfied
    }

    result = await gate_system.evaluate_gate4(with_ai_metrics, without_ai_metrics)

    assert result.status == GateStatus.FAIL
    assert len(result.violations) > 0
    assert any("degradation" in v.description.lower() or "dependency" in v.description.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_gate4_acceptable_moderate_improvement(gate_system):
    """Test Gate 4 allows moderate improvement with AI"""
    with_ai_metrics = {
        "task_completion_time": 100,
        "error_rate": 0.05,
        "quality_score": 0.9,
        "user_satisfaction": 0.85,
    }

    without_ai_metrics = {
        "task_completion_time": 120,  # 20% slower without AI (acceptable)
        "error_rate": 0.08,  # Slightly more errors
        "quality_score": 0.85,  # Slightly worse
        "user_satisfaction": 0.80,  # Slightly less satisfied
    }

    result = await gate_system.evaluate_gate4(with_ai_metrics, without_ai_metrics)

    # Moderate degradation is acceptable (shows non-dependency)
    assert result.status in [GateStatus.PASS, GateStatus.WARN]


# ============================================================================
# All Gates Evaluation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_evaluate_all_gates_passing(gate_system):
    """Test evaluating all gates when they all pass"""
    # Mock successful individual gate evaluations
    with patch.object(gate_system, 'evaluate_gate1', return_value=Mock(status=GateStatus.PASS, violations=[])):
        with patch.object(gate_system, 'evaluate_gate2', return_value=Mock(status=GateStatus.PASS, violations=[])):
            with patch.object(gate_system, 'evaluate_gate3', return_value=Mock(status=GateStatus.PASS, violations=[])):
                with patch.object(gate_system, 'evaluate_gate4', return_value=Mock(status=GateStatus.PASS, violations=[])):
                    results = await gate_system.evaluate_all_gates(
                        snapshots=[],
                        code="",
                        system_config={},
                        performance_metrics=({}, {}),
                    )

                    assert len(results) == 4
                    assert all(r.status == GateStatus.PASS for r in results)


@pytest.mark.asyncio
async def test_evaluate_all_gates_one_failure(gate_system):
    """Test evaluating all gates when one fails"""
    # Mock one failing gate
    with patch.object(gate_system, 'evaluate_gate1', return_value=Mock(status=GateStatus.FAIL, violations=[Mock()])):
        with patch.object(gate_system, 'evaluate_gate2', return_value=Mock(status=GateStatus.PASS, violations=[])):
            with patch.object(gate_system, 'evaluate_gate3', return_value=Mock(status=GateStatus.PASS, violations=[])):
                with patch.object(gate_system, 'evaluate_gate4', return_value=Mock(status=GateStatus.PASS, violations=[])):
                    results = await gate_system.evaluate_all_gates(
                        snapshots=[],
                        code="",
                        system_config={},
                        performance_metrics=({}, {}),
                    )

                    assert len(results) == 4
                    failed_gates = [r for r in results if r.status == GateStatus.FAIL]
                    assert len(failed_gates) == 1


# ============================================================================
# Violation Tracking Tests
# ============================================================================


@pytest.mark.asyncio
async def test_violation_includes_details(gate_system):
    """Test that violations include sufficient detail for debugging"""
    snapshots = [
        AgencySnapshot(
            timestamp=datetime.now(),
            task_id="task-1",
            task_type="coding",
            delta_agency=-0.1,
            bhir=1.0,
            task_efficacy=0.5,
            user_skill_before=0.8,
            user_skill_after=0.7,  # Skill declined
            skill_development=-0.1,
            ai_reliance=0.95,
            autonomy_retention=0.3,
            user_id="test-user",
            session_id="session-1",
        )
    ]

    result = await gate_system.evaluate_gate1(snapshots)

    if result.status == GateStatus.FAIL:
        assert len(result.violations) > 0
        for violation in result.violations:
            assert violation.description is not None
            assert len(violation.description) > 10  # Has meaningful description
            assert violation.severity is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
