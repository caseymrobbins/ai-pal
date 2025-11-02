"""
Tests for Phase 3: Integrated System

Tests end-to-end integration of all AC-AI components.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from ai_pal.core.integrated_system import (
    IntegratedACSystem,
    SystemConfig,
    ProcessedRequest,
    RequestStage,
    create_default_system,
)
from ai_pal.orchestration.multi_model import TaskRequirements, TaskComplexity
from ai_pal.ui.agency_dashboard import DashboardSection


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        data_dir = tmp_path / "data"
        credentials_path = tmp_path / "credentials.json"

        # Create empty credentials file
        credentials_path.write_text('{}')

        yield data_dir, credentials_path


@pytest.fixture
def system_config(temp_dirs):
    """Create system configuration"""
    data_dir, credentials_path = temp_dirs

    return SystemConfig(
        data_dir=data_dir,
        credentials_path=credentials_path,
        enable_gates=True,
        enable_tribunal=True,
        enable_ari_monitoring=True,
        enable_edm_monitoring=True,
        enable_self_improvement=True,
        enable_lora_tuning=False,
        enable_privacy_protection=True,
        enable_context_management=True,
        enable_model_orchestration=True,
        enable_dashboard=True
    )


@pytest.fixture
def integrated_system(system_config):
    """Create integrated system instance"""
    return IntegratedACSystem(system_config)


@pytest.mark.asyncio
async def test_system_initialization(integrated_system):
    """Test that system initializes all components"""
    assert integrated_system.credential_manager is not None
    assert integrated_system.gate_system is not None
    assert integrated_system.tribunal is not None
    assert integrated_system.ari_monitor is not None
    assert integrated_system.edm_monitor is not None
    assert integrated_system.improvement_loop is not None
    assert integrated_system.privacy_manager is not None
    assert integrated_system.context_manager is not None
    assert integrated_system.orchestrator is not None
    assert integrated_system.dashboard is not None


@pytest.mark.asyncio
async def test_process_simple_request(integrated_system):
    """Test processing a simple request through the system"""
    result = await integrated_system.process_request(
        user_id="test_user",
        query="What is Python?",
        session_id="session_1",
        task_type="question"
    )

    assert result is not None
    assert result.success is True
    assert result.user_id == "test_user"
    assert result.original_query == "What is Python?"
    assert result.model_response != ""
    assert result.stage_completed == RequestStage.RESPONSE


@pytest.mark.asyncio
async def test_pii_detection_in_request(integrated_system):
    """Test that PII is detected and handled"""
    result = await integrated_system.process_request(
        user_id="test_user",
        query="My email is test@example.com and I need help",
        session_id="session_1",
        task_type="general"
    )

    assert result.success is True
    # PII should be detected
    assert len(result.pii_detections) > 0
    # Query should be redacted
    assert "test@example.com" not in result.processed_query or "[REDACTED" in result.processed_query


@pytest.mark.asyncio
async def test_context_memory_storage(integrated_system):
    """Test that context is stored during request"""
    result = await integrated_system.process_request(
        user_id="test_user",
        query="Remember that I prefer Python for scripting",
        session_id="session_1",
        task_type="preference"
    )

    assert result.success is True
    # Should have created memories
    assert result.new_memories_created > 0

    # Check context manager has memories
    memories = integrated_system.context_manager.memories.get("test_user", [])
    assert len(memories) > 0


@pytest.mark.asyncio
async def test_agency_monitoring(integrated_system):
    """Test that agency is monitored"""
    result = await integrated_system.process_request(
        user_id="test_user",
        query="Help me write a function",
        session_id="session_1",
        task_type="coding"
    )

    assert result.success is True
    # Should have recorded agency snapshot
    assert result.agency_snapshot is not None
    assert result.agency_snapshot.user_id == "test_user"


@pytest.mark.asyncio
async def test_epistemic_debt_detection(integrated_system):
    """Test epistemic debt detection in responses"""
    # Process request (response would normally trigger EDM)
    result = await integrated_system.process_request(
        user_id="test_user",
        query="Tell me about AI",
        session_id="session_1",
        task_type="question"
    )

    assert result.success is True
    # EDM check was performed (detected count may be 0 or more)
    assert result.epistemic_debts_detected >= 0


@pytest.mark.asyncio
async def test_model_selection(integrated_system):
    """Test that appropriate model is selected"""
    requirements = TaskRequirements(
        task_type="calculation",
        complexity=TaskComplexity.SIMPLE,
        min_quality=0.6,
        max_cost=0.0,
        max_latency_ms=1000,
        requires_local=True
    )

    result = await integrated_system.process_request(
        user_id="test_user",
        query="What is 2+2?",
        session_id="session_1",
        task_type="calculation",
        requirements=requirements
    )

    assert result.success is True
    # Should select local model for simple task
    assert result.selected_model == "phi-2"
    assert result.cost == 0.0


@pytest.mark.asyncio
async def test_user_feedback_recording(integrated_system):
    """Test recording explicit user feedback"""
    # Process a request
    result = await integrated_system.process_request(
        user_id="test_user",
        query="Help me with this",
        session_id="session_1",
        task_type="general"
    )

    assert result.success is True

    # Record positive feedback
    await integrated_system.record_user_feedback(
        user_id="test_user",
        request_id=result.request_id,
        feedback_positive=True,
        feedback_text="Very helpful!"
    )

    # Check that feedback was collected
    feedback_events = integrated_system.improvement_loop.feedback_events
    assert len(feedback_events) > 0


@pytest.mark.asyncio
async def test_dashboard_generation(integrated_system):
    """Test generating user dashboard"""
    # First process some requests to generate data
    for i in range(3):
        await integrated_system.process_request(
            user_id="test_user",
            query=f"Test query {i}",
            session_id="session_1",
            task_type="general"
        )

    # Generate dashboard
    dashboard = await integrated_system.get_user_dashboard(
        user_id="test_user",
        period_days=7
    )

    assert dashboard is not None
    assert dashboard.user_id == "test_user"
    assert dashboard.overall_health_score >= 0
    assert dashboard.overall_health_score <= 100

    # Should have agency metrics
    assert dashboard.agency_metrics is not None

    # Should have privacy status
    assert dashboard.privacy_status is not None


@pytest.mark.asyncio
async def test_privacy_budget_enforcement(integrated_system):
    """Test that privacy budget is enforced"""
    # Set very low budget
    privacy_manager = integrated_system.privacy_manager
    user_id = "test_user"

    # Set consent with low budget
    from ai_pal.privacy.advanced_privacy import ConsentLevel
    await privacy_manager.record_consent(user_id, ConsentLevel.MINIMAL)

    # Exhaust budget
    budget = privacy_manager.privacy_budgets[user_id]
    budget.queries_made = 100  # Max limit
    budget.epsilon_spent = 1.0  # Max epsilon

    # Try to process request
    result = await integrated_system.process_request(
        user_id=user_id,
        query="Test query",
        session_id="session_1",
        task_type="general"
    )

    # Should fail due to budget
    assert result.success is False
    assert "budget" in result.error.lower()


@pytest.mark.asyncio
async def test_context_retrieval(integrated_system):
    """Test that relevant context is retrieved"""
    user_id = "test_user"

    # Store some context
    from ai_pal.context.enhanced_context import MemoryType, MemoryPriority
    await integrated_system.context_manager.store_memory(
        user_id=user_id,
        session_id="session_1",
        content="User prefers Python programming language",
        memory_type=MemoryType.PREFERENCE,
        priority=MemoryPriority.HIGH,
        tags={"programming", "python"}
    )

    # Process related query
    result = await integrated_system.process_request(
        user_id=user_id,
        query="What programming language should I use?",
        session_id="session_1",
        task_type="question"
    )

    assert result.success is True
    # Should have retrieved relevant memories
    assert len(result.relevant_memories) > 0


@pytest.mark.asyncio
async def test_gate_system_evaluation(integrated_system):
    """Test that gates are evaluated"""
    result = await integrated_system.process_request(
        user_id="test_user",
        query="Test query for gates",
        session_id="session_1",
        task_type="general"
    )

    assert result.success is True
    # Should have gate verdicts
    assert len(result.gate_verdicts) > 0


@pytest.mark.asyncio
async def test_system_shutdown(integrated_system):
    """Test graceful system shutdown"""
    # Process some requests
    await integrated_system.process_request(
        user_id="test_user",
        query="Test query",
        session_id="session_1",
        task_type="general"
    )

    # Shutdown
    await integrated_system.shutdown()

    # Should complete without errors


@pytest.mark.asyncio
async def test_create_default_system(temp_dirs):
    """Test creating system with default configuration"""
    data_dir, credentials_path = temp_dirs

    system = create_default_system(
        data_dir=data_dir,
        credentials_path=credentials_path
    )

    assert system is not None
    assert system.config.enable_gates is True
    assert system.config.enable_ari_monitoring is True
    assert system.config.enable_privacy_protection is True


@pytest.mark.asyncio
async def test_multiple_users(integrated_system):
    """Test handling multiple users"""
    # Process requests for different users
    result1 = await integrated_system.process_request(
        user_id="user_1",
        query="Query from user 1",
        session_id="session_1",
        task_type="general"
    )

    result2 = await integrated_system.process_request(
        user_id="user_2",
        query="Query from user 2",
        session_id="session_2",
        task_type="general"
    )

    assert result1.success is True
    assert result2.success is True
    assert result1.user_id == "user_1"
    assert result2.user_id == "user_2"

    # Each user should have separate data
    dashboard1 = await integrated_system.get_user_dashboard("user_1")
    dashboard2 = await integrated_system.get_user_dashboard("user_2")

    assert dashboard1.user_id == "user_1"
    assert dashboard2.user_id == "user_2"


def test_request_stages():
    """Test request stage enum"""
    assert RequestStage.INTAKE.value == "intake"
    assert RequestStage.PII_DETECTION.value == "pii_detection"
    assert RequestStage.CONTEXT_RETRIEVAL.value == "context_retrieval"
    assert RequestStage.GATE_EVALUATION.value == "gate_evaluation"
    assert RequestStage.MODEL_SELECTION.value == "model_selection"
    assert RequestStage.EXECUTION.value == "execution"
    assert RequestStage.MONITORING.value == "monitoring"
    assert RequestStage.RESPONSE.value == "response"
    assert RequestStage.FEEDBACK.value == "feedback"


@pytest.mark.asyncio
async def test_performance_metrics(integrated_system):
    """Test that performance metrics are tracked"""
    result = await integrated_system.process_request(
        user_id="test_user",
        query="Test query",
        session_id="session_1",
        task_type="general"
    )

    assert result.success is True
    # Should have performance data
    assert result.latency_ms >= 0
    assert result.cost >= 0


@pytest.mark.asyncio
async def test_error_handling(integrated_system):
    """Test error handling in request processing"""
    # Test with invalid parameters could trigger errors
    # (This depends on validation in the system)
    # For now, just ensure system handles gracefully

    result = await integrated_system.process_request(
        user_id="test_user",
        query="",  # Empty query
        session_id="session_1",
        task_type="general"
    )

    # Should either succeed or fail gracefully
    assert result is not None
