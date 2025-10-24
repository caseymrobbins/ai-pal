"""
Integration tests for Four Gates CI/CD pipeline.

Tests complete gate workflows with real components.
"""

import pytest
import asyncio
from pathlib import Path

from ai_pal.modules.ethics import EthicsModule, FourGatesResult, GateResult
from ai_pal.core.plugin_manager import get_plugin_manager


# ============================================================================
# Gate 1: Net-Agency Test Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate1_net_agency_with_ethics_module(
    ethics_module, sample_action_context
):
    """Test Gate 1 integration with Ethics Module."""
    # Measure agency impact
    metrics = await ethics_module.measure_agency_impact(
        action="test_action",
        context=sample_action_context,
    )

    # Verify metrics
    assert metrics.net_agency_delta >= 0.0
    assert metrics.bhir > 1.0
    assert metrics.autonomy_retention > 0.5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate1_detects_low_agency_delta(ethics_module):
    """Test Gate 1 fails when agency delta is negative."""
    context = {
        "task_efficacy": 0.1,  # Very low
        "opportunity_expansion": 0.1,
        "autonomy_retention": 0.3,
        "skill_development": -0.5,  # Deskilling
        "bhir": 1.1,
    }

    metrics = await ethics_module.measure_agency_impact("harmful_action", context)

    assert metrics.net_agency_delta < 0.0  # Should be negative


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate1_detects_low_bhir(ethics_module):
    """Test Gate 1 fails when BHIR <= 1."""
    context = {
        "task_efficacy": 0.8,
        "opportunity_expansion": 0.7,
        "autonomy_retention": 0.75,
        "skill_development": 0.6,
        "bhir": 0.9,  # Below threshold
    }

    metrics = await ethics_module.measure_agency_impact("short_term_action", context)

    assert metrics.bhir < 1.0


# ============================================================================
# Gate 2: Extraction Test Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate2_passes_for_benign_action(ethics_module):
    """Test Gate 2 passes for actions without extraction."""
    context = {
        "reduces_user_capability": False,
        "hidden_data_collection": False,
    }

    gates_result = await ethics_module.run_four_gates("help_user_learn", context)

    assert gates_result.gate2_extraction == GateResult.PASS


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate2_fails_for_extraction(ethics_module):
    """Test Gate 2 fails when extraction detected."""
    context = {
        "reduces_user_capability": True,
        "hidden_data_collection": True,
    }

    gates_result = await ethics_module.run_four_gates("extract_data", context)

    assert gates_result.gate2_extraction == GateResult.FAIL


# ============================================================================
# Gate 3: Humanity Override Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate3_passes_for_reversible_action(ethics_module):
    """Test Gate 3 passes for reversible actions."""
    context = {
        "reversible": True,
    }

    gates_result = await ethics_module.run_four_gates("reversible_action", context)

    assert gates_result.gate3_humanity_override == GateResult.PASS


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate3_fails_for_irreversible_action(ethics_module):
    """Test Gate 3 fails for non-reversible actions."""
    context = {
        "reversible": False,
    }

    gates_result = await ethics_module.run_four_gates("irreversible_action", context)

    assert gates_result.gate3_humanity_override == GateResult.FAIL


@pytest.mark.integration
def test_gate3_humanity_override_registration(ethics_module):
    """Test registering humanity overrides."""
    ethics_module.register_humanity_override(
        action_id="ACTION-123",
        reason="User disagrees with AI decision",
        user_id="user_456",
    )

    assert len(ethics_module.humanity_overrides) == 1
    override = ethics_module.humanity_overrides[0]
    assert override["action_id"] == "ACTION-123"
    assert override["user_id"] == "user_456"


# ============================================================================
# Gate 4: Non-Othering Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate4_passes_for_equitable_action(ethics_module):
    """Test Gate 4 passes for equitable actions."""
    context = {
        "uses_stereotypes": False,
        "discriminatory": False,
        "unequal_access": False,
    }

    gates_result = await ethics_module.run_four_gates("equitable_action", context)

    assert gates_result.gate4_non_othering == GateResult.PASS


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate4_fails_for_discriminatory_action(ethics_module):
    """Test Gate 4 fails for discriminatory actions."""
    context = {
        "uses_stereotypes": True,
        "discriminatory": True,
        "unequal_access": False,
    }

    gates_result = await ethics_module.run_four_gates("discriminatory_action", context)

    assert gates_result.gate4_non_othering == GateResult.FAIL


# ============================================================================
# Complete Four Gates Workflow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_four_gates_pass(ethics_module):
    """Test that all gates pass for a compliant action."""
    context = {
        # Gate 1: Net-Agency
        "task_efficacy": 0.8,
        "opportunity_expansion": 0.7,
        "autonomy_retention": 0.85,
        "skill_development": 0.6,
        "bhir": 1.3,
        # Gate 2: Extraction
        "reduces_user_capability": False,
        "hidden_data_collection": False,
        # Gate 3: Humanity Override
        "reversible": True,
        # Gate 4: Non-Othering
        "uses_stereotypes": False,
        "discriminatory": False,
        "unequal_access": False,
    }

    gates_result = await ethics_module.run_four_gates("ethical_action", context)

    assert gates_result.overall_pass is True
    assert gates_result.gate1_net_agency == GateResult.PASS
    assert gates_result.gate2_extraction == GateResult.PASS
    assert gates_result.gate3_humanity_override == GateResult.PASS
    assert gates_result.gate4_non_othering == GateResult.PASS
    assert len(gates_result.blocking_gates) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_any_gate_failure_blocks(ethics_module):
    """Test that failure of any gate blocks overall approval."""
    # Fail Gate 2 (extraction)
    context = {
        "task_efficacy": 0.8,
        "bhir": 1.3,
        "reduces_user_capability": True,  # Extraction!
        "reversible": True,
    }

    gates_result = await ethics_module.run_four_gates("extractive_action", context)

    assert gates_result.overall_pass is False
    assert "Gate 2: Extraction" in gates_result.blocking_gates


# ============================================================================
# Circuit Breaker Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_circuit_breaker_triggers_on_violations(ethics_module):
    """Test circuit breaker triggers after repeated violations."""
    # Create two metrics with high epistemic debt
    for _ in range(2):
        context = {
            "epistemic_debt": 0.5,  # Above threshold (0.3)
            "bhir": 1.2,
            "task_efficacy": 0.7,
        }
        await ethics_module.measure_agency_impact("bad_action", context)

    # Check circuit breaker
    await ethics_module._check_circuit_breakers(
        await ethics_module.run_four_gates("test", {})
    )

    # Should trigger after 2 violations
    assert ethics_module.circuit_breaker_triggered is True
    assert "Epistemic debt" in ethics_module.circuit_breaker_reason


# ============================================================================
# Plugin Manager + Ethics Integration
# ============================================================================

@pytest.mark.integration
def test_plugin_freeze_on_gate_failure(plugin_manager):
    """Test that plugin can be frozen when gate fails."""
    # Simulate Ethics Module detecting a violation
    plugin_manager.freeze_plugin(
        "violating_plugin",
        reason="Gate 2 violation: extraction detected",
    )

    assert "violating_plugin" in plugin_manager.frozen_plugins


@pytest.mark.integration
def test_frozen_plugin_cannot_execute(plugin_manager, mock_module):
    """Test that frozen plugins cannot be loaded or called."""
    from ai_pal.core.plugin_manager import (
        PluginInstance,
        PluginManifest,
        PluginStatus,
    )
    from datetime import datetime

    # Load a plugin
    manifest = PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="Test",
        author="Test",
        module_class="test:Test",
    )

    instance = PluginInstance(
        manifest=manifest,
        module=mock_module,
        status=PluginStatus.RUNNING,
        loaded_at=datetime.now(),
        code_version="1.0.0",
    )

    plugin_manager.loaded_plugins["test_plugin"] = instance

    # Freeze it (Ethics Module would do this)
    plugin_manager.freeze_plugin("test_plugin", reason="Gate violation")

    # Verify it's frozen
    status = plugin_manager.get_plugin_status("test_plugin")
    assert status["frozen"] is True
    assert status["status"] == "frozen"


# ============================================================================
# End-to-End Gate Pipeline
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_complete_gate_pipeline(ethics_module, temp_reports_dir):
    """Test complete gate pipeline from action to decision."""
    # Simulate a new feature being evaluated
    action = "implement_user_tracking"
    context = {
        # Net agency metrics
        "task_efficacy": 0.6,
        "opportunity_expansion": 0.4,
        "autonomy_retention": 0.5,
        "skill_development": -0.2,  # Slight deskilling
        "bhir": 0.9,  # Below threshold!
        # Extraction check
        "reduces_user_capability": True,
        "hidden_data_collection": True,
        # Override
        "reversible": False,
        # Non-othering
        "discriminatory": False,
    }

    # Run complete Four Gates
    gates_result = await ethics_module.run_four_gates(action, context)

    # Should fail multiple gates
    assert gates_result.overall_pass is False

    # Should have blocking gates
    assert len(gates_result.blocking_gates) >= 2

    # Verify specific failures
    assert gates_result.gate1_net_agency == GateResult.FAIL  # Low BHIR
    assert gates_result.gate2_extraction == GateResult.FAIL  # Extraction detected
    assert gates_result.gate3_humanity_override == GateResult.FAIL  # Not reversible


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate_performance(ethics_module, timer):
    """Test that gate checks complete in reasonable time."""
    context = {
        "task_efficacy": 0.8,
        "bhir": 1.3,
        "reversible": True,
    }

    timer.start()
    await ethics_module.run_four_gates("test_action", context)
    timer.stop()

    # Should complete in under 100ms
    assert timer.elapsed_ms < 100


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_sequential_gates(ethics_module):
    """Test running gates sequentially for multiple actions."""
    actions = [
        ("action1", {"task_efficacy": 0.8, "bhir": 1.2}),
        ("action2", {"task_efficacy": 0.7, "bhir": 1.1}),
        ("action3", {"task_efficacy": 0.9, "bhir": 1.4}),
    ]

    results = []
    for action, context in actions:
        result = await ethics_module.run_four_gates(action, context)
        results.append(result)

    # All should pass with these contexts
    assert all(r.overall_pass for r in results)


# ============================================================================
# Error Handling
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_gates_handle_missing_context_gracefully(ethics_module):
    """Test gates handle missing context data gracefully."""
    # Empty context
    context = {}

    # Should not crash, but use defaults
    result = await ethics_module.run_four_gates("test_action", context)

    # May pass or fail, but shouldn't raise exception
    assert isinstance(result, FourGatesResult)
