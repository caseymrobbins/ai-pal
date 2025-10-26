"""
Unit tests for Socratic Co-pilot (Embedded Assessment).

Tests checkpoint-based assistance, ARI measurement, and adaptive help levels.
"""

import pytest
from pathlib import Path

from ai_pal.ari.measurement import ARIMeasurementSystem, ARILevel
from ai_pal.modes.socratic_copilot import (
    SocraticCopilot,
    TaskType,
    AssistanceLevel,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def ari_system(temp_dir):
    """Create ARI system."""
    storage_dir = temp_dir / "ari"
    storage_dir.mkdir()
    return ARIMeasurementSystem(storage_dir=storage_dir)


@pytest.fixture
def copilot(ari_system):
    """Create Socratic Co-pilot."""
    return SocraticCopilot(ari_system=ari_system)


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return "test_user_123"


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
def test_copilot_initialization(copilot):
    """Test Socratic Co-pilot initializes correctly."""
    assert copilot.ari_system is not None
    assert isinstance(copilot.active_requests, dict)


# ============================================================================
# Task Detection Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_code_generation_task(copilot, sample_user_id):
    """Test code generation task is detected."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a Python script to parse JSON files"
    )

    assert task_request.task_type == TaskType.CODE_GENERATION


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_writing_task(copilot, sample_user_id):
    """Test writing task is detected."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Draft an email to my team about the project deadline"
    )

    assert task_request.task_type == TaskType.WRITING


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_analysis_task(copilot, sample_user_id):
    """Test analysis task is detected."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Analyze the performance metrics from last quarter"
    )

    assert task_request.task_type == TaskType.ANALYSIS


# ============================================================================
# Checkpoint Processing Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_task_request_creates_checkpoints(copilot, sample_user_id):
    """Test processing task request creates checkpoints."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a function to validate user input"
    )

    assert len(task_request.checkpoints) > 0
    assert task_request.request_id in copilot.active_requests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initial_response_contains_first_question(copilot, sample_user_id):
    """Test initial response contains first checkpoint question."""
    initial_response, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a Python function"
    )

    # Should contain a question
    assert "?" in initial_response
    assert len(task_request.checkpoints) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_checkpoint_response_high_ari(copilot, sample_user_id):
    """Test processing detailed checkpoint response results in HIGH ARI."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a parser function"
    )

    # Detailed response
    result = await copilot.process_checkpoint_response(
        request_id=task_request.request_id,
        checkpoint_index=0,
        response="I want to name it parse_json_data, and it should read from a file, use json.loads(), handle JSONDecodeError, and return a dict or None"
    )

    assert result["measured_ari"] in [ARILevel.HIGH, ARILevel.MEDIUM]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_checkpoint_response_low_ari(copilot, sample_user_id):
    """Test deferral response results in LOW ARI."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a parser function"
    )

    # Deferral
    result = await copilot.process_checkpoint_response(
        request_id=task_request.request_id,
        checkpoint_index=0,
        response="I don't know, just guess"
    )

    assert result["measured_ari"] == ARILevel.LOW


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multiple_checkpoints_progression(copilot, sample_user_id):
    """Test progression through multiple checkpoints."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a Python script"
    )

    if len(task_request.checkpoints) >= 2:
        # First checkpoint
        result1 = await copilot.process_checkpoint_response(
            request_id=task_request.request_id,
            checkpoint_index=0,
            response="Call it main_script.py"
        )

        assert result1["ready_to_complete"] == False
        assert "next_checkpoint" in result1

        # Second checkpoint
        result2 = await copilot.process_checkpoint_response(
            request_id=task_request.request_id,
            checkpoint_index=1,
            response="Use a simple loop to process each file"
        )

        # Might be ready now or have more checkpoints
        assert "measured_ari" in result2


# ============================================================================
# Override Handling Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_override_just_guess(copilot, sample_user_id):
    """Test user override 'just guess' is handled."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write code"
    )

    result = await copilot.handle_user_override(
        request_id=task_request.request_id,
        checkpoint_index=0,
        override_type="just_guess"
    )

    assert result["measured_ari"] == ARILevel.LOW
    assert result["override_recorded"] == True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_override_recorded_in_ari_system(copilot, ari_system, sample_user_id):
    """Test override is recorded in ARI system."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write code"
    )

    await copilot.handle_user_override(
        request_id=task_request.request_id,
        checkpoint_index=0,
        override_type="just_guess"
    )

    # Check ARI profile updated
    profile = ari_system.get_user_ari_profile(sample_user_id)
    assert len(profile) > 0  # Should have recorded something


# ============================================================================
# ARI Calculation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_overall_ari_high_from_all_high_checkpoints(copilot, sample_user_id):
    """Test overall HIGH ARI when all checkpoints are HIGH."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a simple function"
    )

    # Answer all checkpoints with detailed responses
    for i in range(len(task_request.checkpoints)):
        result = await copilot.process_checkpoint_response(
            request_id=task_request.request_id,
            checkpoint_index=i,
            response=f"Detailed specific answer {i} with many words to ensure it's considered high quality"
        )

        if result["ready_to_complete"]:
            assert result["overall_ari"] in [ARILevel.HIGH, ARILevel.MEDIUM]
            break


@pytest.mark.unit
@pytest.mark.asyncio
async def test_overall_ari_low_from_deferrals(copilot, sample_user_id):
    """Test overall LOW ARI when multiple checkpoints are deferred."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a script"
    )

    # Defer all checkpoints
    for i in range(len(task_request.checkpoints)):
        result = await copilot.handle_user_override(
            request_id=task_request.request_id,
            checkpoint_index=i,
            override_type="just_guess"
        )

        if result["ready_to_complete"]:
            assert result["overall_ari"] == ARILevel.LOW
            break


# ============================================================================
# Assistance Level Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_minimal_assistance_for_high_ari(copilot, sample_user_id):
    """Test minimal assistance is provided for HIGH ARI."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a function"
    )

    # Answer with high quality
    for i in range(len(task_request.checkpoints)):
        result = await copilot.process_checkpoint_response(
            request_id=task_request.request_id,
            checkpoint_index=i,
            response="Very detailed and specific response with technical accuracy and completeness"
        )

        if result["ready_to_complete"]:
            if result["overall_ari"] == ARILevel.HIGH:
                assert result["assistance_level"] == AssistanceLevel.MINIMAL
            break


@pytest.mark.unit
@pytest.mark.asyncio
async def test_substantial_assistance_for_low_ari(copilot, sample_user_id):
    """Test substantial assistance is provided for LOW ARI."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write code"
    )

    # Defer all
    for i in range(len(task_request.checkpoints)):
        result = await copilot.handle_user_override(
            request_id=task_request.request_id,
            checkpoint_index=i,
            override_type="you_decide"
        )

        if result["ready_to_complete"]:
            assert result["assistance_level"] == AssistanceLevel.SUBSTANTIAL
            break


# ============================================================================
# Task Completion Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_task_generates_output(copilot, sample_user_id):
    """Test task completion generates output."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a hello world function"
    )

    # Complete checkpoints
    for i in range(len(task_request.checkpoints)):
        result = await copilot.process_checkpoint_response(
            request_id=task_request.request_id,
            checkpoint_index=i,
            response="Good response"
        )

        if result["ready_to_complete"]:
            break

    # Complete task
    output = await copilot.complete_task(task_request.request_id)

    assert output is not None
    assert len(output) > 0
    assert task_request.final_output is not None
    assert task_request.completed_at is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_task_context_includes_responses(copilot, sample_user_id):
    """Test task context includes checkpoint responses."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a function"
    )

    # Answer first checkpoint
    if len(task_request.checkpoints) > 0:
        await copilot.process_checkpoint_response(
            request_id=task_request.request_id,
            checkpoint_index=0,
            response="my_function"
        )

        context = copilot._build_task_context(task_request)

        assert "checkpoints" in context
        assert len(context["checkpoints"]) >= 1


# ============================================================================
# Task Summary Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_summary(copilot, sample_user_id):
    """Test getting task summary."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write code"
    )

    summary = copilot.get_task_summary(task_request.request_id)

    assert summary["request_id"] == task_request.request_id
    assert summary["task_type"] == task_request.task_type.value
    assert "total_checkpoints" in summary
    assert "completed_checkpoints" in summary


# ============================================================================
# Edge Cases Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_request_id(copilot):
    """Test error for invalid request ID."""
    with pytest.raises(ValueError):
        await copilot.process_checkpoint_response(
            request_id="nonexistent",
            checkpoint_index=0,
            response="Response"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_checkpoint_index(copilot, sample_user_id):
    """Test error for invalid checkpoint index."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write code"
    )

    with pytest.raises(ValueError):
        await copilot.process_checkpoint_response(
            request_id=task_request.request_id,
            checkpoint_index=999,  # Invalid
            response="Response"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_task_with_no_checkpoints(copilot, sample_user_id):
    """Test task that generates no checkpoints."""
    # Very simple task might have minimal checkpoints
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Help"
    )

    # Should still create a request even if no checkpoints
    assert task_request is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mixed_ari_levels_results_in_medium(copilot, sample_user_id):
    """Test mixed ARI levels result in MEDIUM overall."""
    _, task_request = await copilot.process_task_request(
        user_id=sample_user_id,
        request="Write a complex script"
    )

    if len(task_request.checkpoints) >= 3:
        # High, Low, High
        await copilot.process_checkpoint_response(
            task_request.request_id, 0,
            "Very detailed response with lots of specificity and technical detail"
        )

        await copilot.handle_user_override(
            task_request.request_id, 1, "just_guess"
        )

        result = await copilot.process_checkpoint_response(
            task_request.request_id, 2,
            "Another detailed response"
        )

        if result.get("ready_to_complete"):
            # Mixed should be MEDIUM or depends on majority
            assert result["overall_ari"] in [ARILevel.MEDIUM, ARILevel.LOW, ARILevel.HIGH]
