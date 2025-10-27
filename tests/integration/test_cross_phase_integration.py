"""
Integration Tests for Cross-Phase Workflows

Tests that verify components from different phases work together correctly:
- Phase 1 (Gates) + Phase 2 (Monitoring) integration
- Phase 2 (ARI/EDM) + Phase 3 (Orchestrator) integration
- Phase 3 (Orchestrator) + Phase 5 (FFE) integration
- Full pipeline integration tests
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from pathlib import Path

from ai_pal.core.integrated_system import IntegratedACSystem, ACConfig
from ai_pal.monitoring.ari_monitor import ARIMonitor, AgencySnapshot
from ai_pal.monitoring.edm_monitor import EDMMonitor, DebtSeverity
from ai_pal.orchestration.multi_model import (
    MultiModelOrchestrator,
    TaskComplexity,
    OptimizationGoal,
    LLMResponse,
)
from ai_pal.gates.gate_system import GateSystem, GateStatus
from ai_pal.ffe.engine import FractalFlowEngine
from ai_pal.ffe.models import GoalPacket, TaskComplexityLevel


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    return tmp_path / "integration_test"


@pytest.fixture
def test_config(temp_storage):
    """Create test configuration"""
    temp_storage.mkdir(exist_ok=True)
    return ACConfig(
        data_dir=temp_storage,
        enable_gates=True,
        enable_ari_monitoring=True,
        enable_edm_monitoring=True,
        enable_model_orchestration=True,
        enable_ffe=True,
    )


# ============================================================================
# Phase 1 (Gates) + Phase 2 (Monitoring) Integration
# ============================================================================


@pytest.mark.asyncio
async def test_gate1_uses_ari_snapshots(temp_storage):
    """Test that Gate 1 integrates with ARI monitoring"""
    # Create ARI monitor and gate system
    ari_monitor = ARIMonitor(storage_dir=temp_storage / "ari")
    gate_system = GateSystem()

    # Record snapshots showing skill development
    for i in range(10):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=10-i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7 + (i * 0.01),
            user_skill_after=0.75 + (i * 0.01),
            skill_development=0.05,
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Get snapshots and evaluate gate
    snapshots = await ari_monitor.get_snapshots(user_id="test-user")
    gate_result = await gate_system.evaluate_gate1(snapshots)

    # Gate should pass with positive skill development
    assert gate_result.status == GateStatus.PASS
    assert gate_result.gate_name == "Net Agency"


@pytest.mark.asyncio
async def test_gate1_fails_when_ari_shows_deskilling(temp_storage):
    """Test that Gate 1 fails when ARI detects deskilling"""
    ari_monitor = ARIMonitor(storage_dir=temp_storage / "ari")
    gate_system = GateSystem()

    # Record snapshots showing skill decline
    for i in range(10):
        snapshot = AgencySnapshot(
            timestamp=datetime.now() - timedelta(hours=10-i),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=-0.05,
            bhir=1.0,
            task_efficacy=0.6,
            user_skill_before=0.7 - (i * 0.02),
            user_skill_after=0.65 - (i * 0.02),
            skill_development=-0.05,  # Deskilling
            ai_reliance=0.9,
            autonomy_retention=0.4,
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    snapshots = await ari_monitor.get_snapshots(user_id="test-user")
    gate_result = await gate_system.evaluate_gate1(snapshots)

    # Gate should fail with deskilling
    assert gate_result.status == GateStatus.FAIL
    assert len(gate_result.violations) > 0


# ============================================================================
# Phase 2 (ARI/EDM) + Phase 3 (Orchestrator) Integration
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrator_response_triggers_edm_analysis(temp_storage):
    """Test that orchestrator responses are analyzed by EDM"""
    orchestrator = MultiModelOrchestrator()
    edm_monitor = EDMMonitor(storage_dir=temp_storage / "edm", fact_check_enabled=False)

    # Mock model response with epistemic debt
    mock_response = LLMResponse(
        generated_text="Everyone knows that AI will replace all jobs. Studies show this is inevitable.",
        model_name="test-model",
        provider="test",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        finish_reason="stop",
        cost_usd=0.001,
        latency_ms=100.0,
        timestamp=datetime.now(),
    )

    with patch.object(orchestrator, 'execute_model', return_value=mock_response):
        # Execute model
        response = await orchestrator.route_request(
            prompt="Tell me about AI and jobs",
            task_complexity=TaskComplexity.SIMPLE,
        )

        # Analyze response with EDM
        debts = await edm_monitor.analyze_text(
            text=response["response"],
            task_id="test-task",
            user_id="test-user",
        )

        # Should detect epistemic debt
        assert len(debts) > 0
        assert any(debt.debt_type in ["unfalsifiable", "missing_citation"] for debt in debts)


@pytest.mark.asyncio
async def test_high_cost_responses_trigger_ari_alerts(temp_storage):
    """Test that expensive model usage affects ARI monitoring"""
    orchestrator = MultiModelOrchestrator()
    ari_monitor = ARIMonitor(storage_dir=temp_storage / "ari")

    # Mock expensive model response
    mock_response = LLMResponse(
        generated_text="Here's your solution...",
        model_name="gpt-4",
        provider="openai",
        prompt_tokens=1000,
        completion_tokens=2000,
        total_tokens=3000,
        finish_reason="stop",
        cost_usd=0.15,  # Expensive!
        latency_ms=5000.0,
        timestamp=datetime.now(),
    )

    with patch.object(orchestrator, 'execute_model', return_value=mock_response):
        response = await orchestrator.route_request(
            prompt="Complex coding task",
            optimization_goal="quality",
        )

        # Record ARI snapshot showing high reliance
        snapshot = AgencySnapshot(
            timestamp=datetime.now(),
            task_id="expensive-task",
            task_type="coding",
            delta_agency=-0.1,
            bhir=1.0,
            task_efficacy=0.7,
            user_skill_before=0.7,
            user_skill_after=0.65,
            skill_development=-0.05,
            ai_reliance=0.95,  # Very high reliance
            autonomy_retention=0.3,
            user_id="test-user",
            session_id="session-1",
            metadata={"cost": response["cost"], "model": response["model"]},
        )
        await ari_monitor.record_snapshot(snapshot)

        # Check for alerts
        alerts = await ari_monitor.detect_alerts(user_id="test-user")

        # Should have alert about high AI reliance
        assert len(alerts) > 0


# ============================================================================
# Phase 3 (Orchestrator) + Phase 5 (FFE) Integration
# ============================================================================


@pytest.mark.asyncio
async def test_ffe_uses_orchestrator_for_scoping(temp_storage):
    """Test that FFE components use orchestrator for AI-powered decisions"""
    orchestrator = MultiModelOrchestrator()
    ffe = FractalFlowEngine(
        storage_dir=temp_storage / "ffe",
        orchestrator=orchestrator,
    )

    # Verify FFE has orchestrator
    assert ffe.orchestrator is orchestrator

    # Verify FFE components have orchestrator
    assert ffe.scoping_agent.orchestrator is orchestrator
    assert ffe.strength_amplifier.orchestrator is orchestrator
    assert ffe.reward_emitter.orchestrator is orchestrator


@pytest.mark.asyncio
async def test_ffe_scoping_triggers_model_execution(temp_storage):
    """Test that FFE scoping actually calls the orchestrator"""
    orchestrator = MultiModelOrchestrator()
    ffe = FractalFlowEngine(
        storage_dir=temp_storage / "ffe",
        orchestrator=orchestrator,
    )

    # Mock AI response for scoping
    mock_response = LLMResponse(
        generated_text="""CRITICAL_PATH: Implement user authentication first
VALUE_SCORE: 0.85
EFFORT_SCORE: 0.25
REASONING: Auth is the foundation""",
        model_name="test-model",
        provider="test",
        prompt_tokens=50,
        completion_tokens=30,
        total_tokens=80,
        finish_reason="stop",
        cost_usd=0.002,
        latency_ms=200.0,
        timestamp=datetime.now(),
    )

    with patch.object(orchestrator, 'select_model', return_value=Mock(provider="test", model_name="test")):
        with patch.object(orchestrator, 'execute_model', return_value=mock_response) as mock_execute:
            # Create a goal
            goal = GoalPacket(
                goal_id="goal-1",
                user_id="test-user",
                description="Build web application",
                complexity_level=TaskComplexityLevel.LARGE,
                status="pending",
                created_at=datetime.now(),
            )

            # Scope the goal (should trigger AI)
            session = await ffe.scoping_agent.scope_goal(goal)

            # Verify model was called
            mock_execute.assert_called_once()

            # Verify scoping worked
            assert session is not None
            assert "auth" in session.identified_80_win.lower()


# ============================================================================
# Full Pipeline Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_request_pipeline_with_all_phases(test_config):
    """Test complete request through all phases"""
    system = IntegratedACSystem(config=test_config)

    # Mock model execution
    mock_response = LLMResponse(
        generated_text="Here's a clean, well-reasoned response with no epistemic debt.",
        model_name="test-model",
        provider="test",
        prompt_tokens=20,
        completion_tokens=30,
        total_tokens=50,
        finish_reason="stop",
        cost_usd=0.001,
        latency_ms=150.0,
        timestamp=datetime.now(),
    )

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_response):
        # Process request through full pipeline
        result = await system.process_request(
            user_id="test-user",
            query="How do I implement user authentication?",
            session_id="session-1",
        )

        # Verify all stages completed
        assert result is not None
        assert result.model_response is not None
        assert result.stage_completed is not None

        # Verify monitoring occurred
        if system.edm_monitor:
            assert hasattr(result, 'epistemic_debts_detected')

        # Verify response validation
        if hasattr(result, 'metadata'):
            assert 'validation_warnings' in result.metadata or 'finish_reason' in result.metadata


@pytest.mark.asyncio
async def test_request_pipeline_with_epistemic_debt_detection(test_config):
    """Test that full pipeline detects and reports epistemic debt"""
    system = IntegratedACSystem(config=test_config)

    # Mock response with epistemic debt
    mock_response = LLMResponse(
        generated_text="Everyone knows this is the best approach. Studies show it's superior.",
        model_name="test-model",
        provider="test",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        finish_reason="stop",
        cost_usd=0.001,
        latency_ms=100.0,
        timestamp=datetime.now(),
    )

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_response):
        result = await system.process_request(
            user_id="test-user",
            query="What's the best approach?",
            session_id="session-1",
        )

        # Should have detected epistemic debt
        if system.edm_monitor:
            assert result.epistemic_debts_detected > 0

            # Should have debt metadata
            if hasattr(result, 'metadata') and 'epistemic_debts' in result.metadata:
                debt_info = result.metadata['epistemic_debts']
                assert debt_info['total_count'] > 0


@pytest.mark.asyncio
async def test_concurrent_requests_across_phases(test_config):
    """Test that system handles concurrent requests correctly"""
    system = IntegratedACSystem(config=test_config)

    mock_response = LLMResponse(
        generated_text="Response",
        model_name="test",
        provider="test",
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20,
        finish_reason="stop",
        cost_usd=0.001,
        latency_ms=100.0,
        timestamp=datetime.now(),
    )

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_response):
        # Process multiple requests concurrently
        import asyncio
        tasks = [
            system.process_request(
                user_id=f"user-{i}",
                query=f"Query {i}",
                session_id=f"session-{i}",
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # All requests should complete successfully
        assert len(results) == 5
        assert all(r.model_response is not None for r in results)


# ============================================================================
# Error Handling Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_model_failure_doesnt_break_pipeline(test_config):
    """Test that model failures are handled gracefully"""
    system = IntegratedACSystem(config=test_config)

    # Mock model failure
    with patch.object(system.orchestrator, 'execute_model', side_effect=Exception("API Error")):
        result = await system.process_request(
            user_id="test-user",
            query="Test query",
            session_id="session-1",
        )

        # Should have error but not crash
        assert result is not None
        assert result.error is not None or "Error" in result.model_response


@pytest.mark.asyncio
async def test_edm_failure_doesnt_block_response(test_config):
    """Test that EDM failures don't prevent responses"""
    system = IntegratedACSystem(config=test_config)

    mock_response = LLMResponse(
        generated_text="Clean response",
        model_name="test",
        provider="test",
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20,
        finish_reason="stop",
        cost_usd=0.001,
        latency_ms=100.0,
        timestamp=datetime.now(),
    )

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_response):
        # Mock EDM failure
        if system.edm_monitor:
            with patch.object(system.edm_monitor, 'analyze_text', side_effect=Exception("EDM Error")):
                result = await system.process_request(
                    user_id="test-user",
                    query="Test query",
                    session_id="session-1",
                )

                # Response should still work
                assert result.model_response is not None
                assert "Clean response" in result.model_response


# ============================================================================
# Multi-User Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_multi_user_isolation(test_config):
    """Test that different users' data is properly isolated"""
    system = IntegratedACSystem(config=test_config)

    mock_response = LLMResponse(
        generated_text="User-specific response",
        model_name="test",
        provider="test",
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20,
        finish_reason="stop",
        cost_usd=0.001,
        latency_ms=100.0,
        timestamp=datetime.now(),
    )

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_response):
        # Process requests for different users
        result1 = await system.process_request(
            user_id="user-1",
            query="User 1 query",
            session_id="session-1",
        )

        result2 = await system.process_request(
            user_id="user-2",
            query="User 2 query",
            session_id="session-2",
        )

        # Both should succeed
        assert result1.model_response is not None
        assert result2.model_response is not None

        # Verify ARI snapshots are user-specific
        if system.ari_monitor:
            user1_snapshots = await system.ari_monitor.get_snapshots(user_id="user-1")
            user2_snapshots = await system.ari_monitor.get_snapshots(user_id="user-2")

            # Each user should only see their own snapshots
            assert all(s.user_id == "user-1" for s in user1_snapshots)
            assert all(s.user_id == "user-2" for s in user2_snapshots)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
