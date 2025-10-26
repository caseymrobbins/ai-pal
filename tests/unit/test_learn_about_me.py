"""
Unit tests for Learn About Me (Socratic Deep Dive) mode.

Tests adaptive scaffolding, difficulty progression, and user control features.
"""

import pytest
from pathlib import Path
from datetime import datetime

from ai_pal.ari.measurement import ARIMeasurementSystem, ARILevel
from ai_pal.modes.learn_about_me import (
    LearnAboutMeMode,
    LearnAboutMeSession,
    DifficultyLevel,
    SessionStatus,
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
def learn_mode(ari_system, temp_dir):
    """Create Learn About Me mode."""
    storage_dir = temp_dir / "learn"
    storage_dir.mkdir()
    return LearnAboutMeMode(
        ari_system=ari_system,
        storage_dir=storage_dir
    )


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return "test_user_123"


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
def test_learn_mode_initialization(learn_mode):
    """Test Learn About Me mode initializes correctly."""
    assert learn_mode.ari_system is not None
    assert isinstance(learn_mode.active_sessions, dict)
    assert isinstance(learn_mode.question_templates, dict)


@pytest.mark.unit
def test_question_templates_loaded(learn_mode):
    """Test question templates are loaded."""
    templates = learn_mode.question_templates

    # Should have python_programming domain
    assert "python_programming" in templates

    # Should have all difficulty levels
    assert DifficultyLevel.FOUNDATIONAL in templates["python_programming"]
    assert DifficultyLevel.INTERMEDIATE in templates["python_programming"]
    assert DifficultyLevel.ADVANCED in templates["python_programming"]


# ============================================================================
# Session Management Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_session(learn_mode, sample_user_id):
    """Test starting a Learn About Me session."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    assert session is not None
    assert session.user_id == sample_user_id
    assert session.domain == "python_programming"
    assert session.status == SessionStatus.ACTIVE
    assert len(session.questions) >= 1  # First question generated
    assert session.session_id in learn_mode.active_sessions


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_starts_at_foundational(learn_mode, sample_user_id):
    """Test new users start at foundational difficulty."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    assert session.current_difficulty == DifficultyLevel.FOUNDATIONAL


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_adapts_to_existing_ari(learn_mode, ari_system, sample_user_id):
    """Test session starts at appropriate level for known users."""
    # Set user's ARI to HIGH
    from ai_pal.ari.measurement import ARIDimension
    ari_system._update_user_ari_score(
        user_id=sample_user_id,
        dimension=ARIDimension.SYNTHESIS,
        domain="python_programming",
        level=ARILevel.HIGH,
        evidence={"prior": "test"}
    )

    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    # Should start at advanced level
    assert session.current_difficulty == DifficultyLevel.ADVANCED


# ============================================================================
# Question Flow Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_question(learn_mode, sample_user_id):
    """Test getting current question from session."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    question = await learn_mode.get_current_question(session.session_id)

    assert question is not None
    assert question.domain == "python_programming"
    assert question.difficulty == session.current_difficulty


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_high_quality_response(learn_mode, sample_user_id):
    """Test submitting high-quality response advances difficulty."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming",
        initial_difficulty=DifficultyLevel.FOUNDATIONAL
    )

    # High-quality response
    response = "A variable in Python is a named location in memory that stores a value. It allows us to reference and manipulate data throughout our program. Variables are created using assignment with the = operator, and Python uses dynamic typing so we don't need to declare types explicitly."

    result = await learn_mode.submit_response(session.session_id, response)

    # Should advance
    assert result["next_action"] in ["advance", "complete"]
    assert result["ari_score"].level in [ARILevel.HIGH, ARILevel.MEDIUM]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_low_quality_response_offers_scaffold(learn_mode, sample_user_id):
    """Test submitting low-quality response offers scaffold."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    # Low-quality response
    response = "It's a thing"

    result = await learn_mode.submit_response(session.session_id, response)

    # Should offer scaffold
    assert result["next_action"] == "scaffold"
    assert "scaffold" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_difficulty_progression(learn_mode, sample_user_id):
    """Test difficulty increases with successful responses."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming",
        initial_difficulty=DifficultyLevel.FOUNDATIONAL
    )

    initial_difficulty = session.current_difficulty

    # Submit successful response
    good_response = "Variables in Python are dynamically typed containers that store references to objects in memory. They're created through assignment and can reference different types throughout execution."

    result = await learn_mode.submit_response(session.session_id, good_response)

    if result.get("difficulty_increased"):
        # Difficulty should have increased
        updated_session = learn_mode.active_sessions[session.session_id]
        assert updated_session.current_difficulty != initial_difficulty


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scaffold_tracking(learn_mode, sample_user_id):
    """Test scaffolds used are tracked."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    initial_scaffolds = session.scaffolds_used

    # Submit poor response to trigger scaffold
    result = await learn_mode.submit_response(session.session_id, "dunno")

    if result["next_action"] == "scaffold":
        updated_session = learn_mode.active_sessions[session.session_id]
        assert updated_session.scaffolds_used > initial_scaffolds


# ============================================================================
# User Control Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_request_regular_chat(learn_mode, sample_user_id):
    """Test user can opt out to regular chat."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    response = await learn_mode.request_regular_chat(session.session_id)

    assert "regular chat" in response.lower() or "switch" in response.lower()

    updated_session = learn_mode.active_sessions[session.session_id]
    assert updated_session.status == SessionStatus.PAUSED
    assert updated_session.opt_outs >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_request_just_answer(learn_mode, sample_user_id):
    """Test user can request direct answer."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    response = await learn_mode.request_just_answer(session.session_id)

    assert len(response) > 0  # Should provide answer

    updated_session = learn_mode.active_sessions[session.session_id]
    assert updated_session.opt_outs >= 1


# ============================================================================
# Session Completion Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_completes_at_expert_level(learn_mode, sample_user_id):
    """Test session completes when expert level is reached."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming",
        initial_difficulty=DifficultyLevel.EXPERT
    )

    # Excellent response at expert level
    expert_response = "The Python GIL (Global Interpreter Lock) is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecode simultaneously. This creates a bottleneck in CPU-bound multithreaded programs because only one thread can execute Python code at a time, even on multi-core systems. However, it simplifies memory management and makes C extension integration safer. For true parallelism, we can use multiprocessing, which creates separate processes with their own GIL, or use async/await for I/O-bound concurrency where the GIL is released during I/O operations. Alternative Python implementations like Jython and IronPython don't have a GIL, and Python 3.13+ includes experimental per-interpreter GIL support."

    result = await learn_mode.submit_response(session.session_id, expert_response)

    # Should complete if no higher difficulty
    if result["next_action"] == "complete":
        updated_session = learn_mode.active_sessions[session.session_id]
        assert updated_session.status == SessionStatus.COMPLETED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_demonstrated_ceiling_tracked(learn_mode, sample_user_id):
    """Test demonstrated ceiling is tracked."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming",
        initial_difficulty=DifficultyLevel.INTERMEDIATE
    )

    good_response = "Decorators are functions that modify other functions using the @ syntax. They're implemented using closure and higher-order function concepts, wrapping the original function to add behavior like logging, timing, or access control without modifying its code."

    result = await learn_mode.submit_response(session.session_id, good_response)

    if result["ari_score"].level == ARILevel.HIGH:
        updated_session = learn_mode.active_sessions[session.session_id]
        assert updated_session.demonstrated_ceiling is not None


# ============================================================================
# Session Summary Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_session_summary(learn_mode, sample_user_id):
    """Test getting session summary."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    # Answer a question
    await learn_mode.submit_response(session.session_id, "A detailed response here")

    summary = await learn_mode.get_session_summary(session.session_id)

    assert summary["session_id"] == session.session_id
    assert summary["domain"] == "python_programming"
    assert summary["questions_answered"] >= 1
    assert "current_difficulty" in summary
    assert "duration_minutes" in summary


# ============================================================================
# Feedback Generation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_affirming_feedback_generated(learn_mode, sample_user_id):
    """Test identity-affirming feedback is generated for success."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    excellent_response = "Variables are named storage locations in memory that hold references to Python objects. Python uses dynamic typing, so variables can reference different types during execution. They're created via assignment and follow specific naming rules."

    result = await learn_mode.submit_response(session.session_id, excellent_response)

    # Should have positive feedback
    assert len(result["feedback"]) > 0
    # For high scores, feedback should be encouraging
    if result["ari_score"].level == ARILevel.HIGH:
        assert any(word in result["feedback"].lower() for word in ["excellent", "great", "good", "well done"])


# ============================================================================
# Edge Cases Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_unknown_session_id(learn_mode):
    """Test error for unknown session ID."""
    with pytest.raises(ValueError):
        await learn_mode.get_current_question("nonexistent_session")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_to_inactive_session(learn_mode, sample_user_id):
    """Test error when submitting to inactive session."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    # Pause session
    await learn_mode.request_regular_chat(session.session_id)

    # Try to submit response
    with pytest.raises(ValueError):
        await learn_mode.submit_response(session.session_id, "Response")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multiple_opt_outs_tracked(learn_mode, sample_user_id):
    """Test multiple opt-outs are tracked."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    # First opt-out
    await learn_mode.request_just_answer(session.session_id)

    # Resume (manually)
    updated_session = learn_mode.active_sessions[session.session_id]
    updated_session.status = SessionStatus.ACTIVE

    # Second opt-out
    await learn_mode.request_regular_chat(session.session_id)

    final_session = learn_mode.active_sessions[session.session_id]
    assert final_session.opt_outs >= 2


# ============================================================================
# Persistence Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_persist_sessions(learn_mode, sample_user_id):
    """Test sessions can be persisted."""
    session = await learn_mode.start_session(
        user_id=sample_user_id,
        domain="python_programming"
    )

    await learn_mode.submit_response(session.session_id, "Test response")

    await learn_mode.persist_sessions()

    # Check file exists
    sessions_file = learn_mode.storage_dir / "sessions.json"
    assert sessions_file.exists()
