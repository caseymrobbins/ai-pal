"""
Integration tests for Socratic Features (Learn About Me & Socratic Co-pilot).

Tests the two ARI measurement features:
1. Learn About Me (Deep Dive Mode) - Socratic dialogue for skill profiling
2. Socratic Co-pilot - Embedded capability assessment during assistance
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from ai_pal.monitoring.ari_monitor import ARIMonitor
from ai_pal.context.enhanced_context import EnhancedContextManager, MemoryType
from ai_pal.orchestration.multi_model import MultiModelOrchestrator
from ai_pal.ffe.interfaces import (
    LearnAboutMeInterface,
    DeepDiveSession,
    SocraticQuestion,
    DifficultyLevel,
    ResponseQuality,
    SocraticCopilotInterface,
    CopilotRequest,
    CheckpointResponse,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_socratic_dir(temp_dir):
    """Create temporary directory structure for Socratic features"""
    socratic_dir = temp_dir / "socratic_features"
    socratic_dir.mkdir()
    (socratic_dir / "ari").mkdir()
    (socratic_dir / "context").mkdir()
    return socratic_dir


@pytest.fixture
def ari_monitor(temp_socratic_dir):
    """Create ARI monitor"""
    return ARIMonitor(storage_dir=temp_socratic_dir / "ari")


@pytest.fixture
def context_manager(temp_socratic_dir):
    """Create context manager"""
    return EnhancedContextManager(
        storage_dir=temp_socratic_dir / "context",
        max_context_tokens=4096,
    )


@pytest.fixture
def orchestrator():
    """Create multi-model orchestrator (mock for testing)"""
    # Note: In real tests, this would use actual orchestrator
    # For now, we'll create a mock that returns predictable responses
    class MockOrchestrator:
        async def route_request(self, prompt, task_complexity, optimization_goal):
            # Return mock responses based on prompt content
            if "Generate a Socratic question" in prompt:
                return {
                    "response": '{"question": "What are the key principles of this concept?", '
                    '"context": "Understanding fundamentals is crucial", '
                    '"expected_concepts": ["principle1", "principle2"], '
                    '"hints": ["Think about the core ideas"]}'
                }
            elif "Grade this response" in prompt:
                return {
                    "response": '{"accuracy": 0.8, "logic": 0.75, "completeness": 0.85, '
                    '"concepts_covered": ["principle1"], '
                    '"novel_insights": ["interesting connection"], '
                    '"feedback": "Good analysis!", '
                    '"validation": "You demonstrated strong understanding.", '
                    '"next_challenge": "Now let\'s explore advanced topics"}'
                }
            elif "Identify the task category" in prompt:
                return {"response": "code"}
            elif "identify the key checkpoints" in prompt:
                return {
                    "response": '[{"type": "parameter", "probe_question": "What should I name the main function?", '
                    '"context": "Function naming affects code readability", "expected_level": 0.4}, '
                    '{"type": "logic", "probe_question": "What should the core algorithm do?", '
                    '"context": "This is the heart of the script", "expected_level": 0.7}]'
                }
            elif "Complete this" in prompt:
                return {"response": "def parse_file():\n    # Implementation here\n    pass"}
            else:
                return {"response": "Mock response"}

    return MockOrchestrator()


@pytest.fixture
def learn_about_me(ari_monitor, context_manager, orchestrator):
    """Create Learn About Me interface"""
    return LearnAboutMeInterface(
        ari_monitor=ari_monitor,
        context_manager=context_manager,
        orchestrator=orchestrator,
    )


@pytest.fixture
def socratic_copilot(ari_monitor, context_manager, orchestrator):
    """Create Socratic Co-pilot interface"""
    return SocraticCopilotInterface(
        ari_monitor=ari_monitor,
        context_manager=context_manager,
        orchestrator=orchestrator,
    )


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return "socratic_test_user"


# ============================================================================
# Learn About Me (Deep Dive Mode) Tests
# ============================================================================

@pytest.mark.asyncio
async def test_start_deep_dive(learn_about_me, test_user_id):
    """Test starting a Deep Dive session"""
    session = await learn_about_me.start_deep_dive(
        user_id=test_user_id,
        domain="machine_learning",
    )

    assert session.user_id == test_user_id
    assert session.domain == "machine_learning"
    assert session.active is True
    assert session.current_difficulty == DifficultyLevel.BASIC
    assert session.session_id in learn_about_me.active_sessions


@pytest.mark.asyncio
async def test_get_next_question(learn_about_me, test_user_id):
    """Test getting Socratic question"""
    session = await learn_about_me.start_deep_dive(test_user_id, "python")

    question = await learn_about_me.get_next_question(test_user_id)

    assert isinstance(question, SocraticQuestion)
    assert question.domain == "python"
    assert question.difficulty == DifficultyLevel.BASIC
    assert question.question_text
    assert question in session.questions_asked


@pytest.mark.asyncio
async def test_submit_excellent_response(learn_about_me, test_user_id):
    """Test submitting excellent response that advances difficulty"""
    session = await learn_about_me.start_deep_dive(test_user_id, "philosophy")
    question = await learn_about_me.get_next_question(test_user_id)

    # Submit excellent response
    response = await learn_about_me.submit_response(
        user_id=test_user_id,
        question_id=question.question_id,
        response_text="This is a thoughtful, comprehensive answer demonstrating deep understanding of the concept. "
        "I can explain the principles clearly and make connections to related ideas.",
    )

    assert response.question_id == question.question_id
    assert response.rubric is not None
    assert response.rubric.quality in [ResponseQuality.EXCELLENT, ResponseQuality.PROFICIENT]
    assert response in session.responses_given

    # Difficulty should potentially increase
    # (depends on score threshold in implementation)


@pytest.mark.asyncio
async def test_progression_through_difficulties(learn_about_me, test_user_id):
    """Test progressive difficulty increase with good performance"""
    session = await learn_about_me.start_deep_dive(test_user_id, "algorithms")

    initial_difficulty = session.current_difficulty

    # Submit multiple excellent responses
    for i in range(3):
        question = await learn_about_me.get_next_question(test_user_id)
        await learn_about_me.submit_response(
            user_id=test_user_id,
            question_id=question.question_id,
            response_text="Excellent detailed answer showing mastery. " * 5,
        )

    # Check if difficulty increased or skill ceiling updated
    assert (
        session.highest_difficulty_achieved.value >= initial_difficulty.value
        or session.skill_ceiling_score > 0.0
    )


@pytest.mark.asyncio
async def test_request_scaffold(learn_about_me, test_user_id):
    """Test requesting scaffold/hint when struggling"""
    await learn_about_me.start_deep_dive(test_user_id, "physics")
    question = await learn_about_me.get_next_question(test_user_id)

    scaffold = await learn_about_me.request_scaffold(
        user_id=test_user_id,
        question_id=question.question_id,
    )

    assert "hint" in scaffold
    assert "encouragement" in scaffold
    assert "simpler_question" in scaffold


@pytest.mark.asyncio
async def test_exit_deep_dive(learn_about_me, test_user_id):
    """Test exiting Deep Dive mode"""
    session = await learn_about_me.start_deep_dive(test_user_id, "history")
    question = await learn_about_me.get_next_question(test_user_id)
    await learn_about_me.submit_response(
        user_id=test_user_id,
        question_id=question.question_id,
        response_text="Some answer",
    )

    summary = await learn_about_me.exit_deep_dive(
        user_id=test_user_id,
        reason="User requested exit",
    )

    assert summary["session_id"] == session.session_id
    assert summary["questions_answered"] == 1
    assert "duration_minutes" in summary
    assert "skill_ceiling_score" in summary
    assert session.active is False
    assert test_user_id not in learn_about_me.active_sessions


@pytest.mark.asyncio
async def test_knowledge_profile_storage(learn_about_me, context_manager, test_user_id):
    """Test that knowledge profile is stored after session"""
    session = await learn_about_me.start_deep_dive(test_user_id, "data_science")

    # Answer questions
    for i in range(2):
        question = await learn_about_me.get_next_question(test_user_id)
        await learn_about_me.submit_response(
            user_id=test_user_id,
            question_id=question.question_id,
            response_text="Detailed response showing understanding",
        )

    # Exit session
    await learn_about_me.exit_deep_dive(test_user_id)

    # Check that profile was stored
    profile = await learn_about_me.get_knowledge_profile(test_user_id, "data_science")

    assert profile is not None
    assert profile.domain == "data_science"
    assert profile.total_sessions == 1
    assert profile.total_questions_answered == 2


@pytest.mark.asyncio
async def test_ari_synthesis_recording(learn_about_me, ari_monitor, test_user_id):
    """Test that ARI-Synthesis snapshots are recorded"""
    await learn_about_me.start_deep_dive(test_user_id, "economics")
    question = await learn_about_me.get_next_question(test_user_id)

    # Submit response
    await learn_about_me.submit_response(
        user_id=test_user_id,
        question_id=question.question_id,
        response_text="Good analytical response",
    )

    # Check ARI snapshots
    assert test_user_id in ari_monitor.snapshots
    snapshots = ari_monitor.snapshots[test_user_id]
    assert len(snapshots) > 0

    # Check that snapshot has synthesis metadata
    snapshot = snapshots[-1]
    assert snapshot.task_type == "deep_dive_economics"
    assert "synthesis_accuracy" in snapshot.metadata
    assert "synthesis_logic" in snapshot.metadata
    assert "synthesis_completeness" in snapshot.metadata


@pytest.mark.asyncio
async def test_appeal_grade(learn_about_me, test_user_id):
    """Test appealing AI's grade (Humanity Override)"""
    await learn_about_me.start_deep_dive(test_user_id, "mathematics")
    question = await learn_about_me.get_next_question(test_user_id)

    response = await learn_about_me.submit_response(
        user_id=test_user_id,
        question_id=question.question_id,
        response_text="My answer",
    )

    # Appeal the grade
    appeal_result = await learn_about_me.appeal_grade(
        user_id=test_user_id,
        response_id=question.question_id,
        appeal_reason="I think my reasoning was valid",
    )

    assert "appeal_accepted" in appeal_result
    assert "original_score" in appeal_result
    assert "explanation" in appeal_result
    assert appeal_result["humanity_override_logged"] is True


# ============================================================================
# Socratic Co-pilot (Embedded Assessment) Tests
# ============================================================================

@pytest.mark.asyncio
async def test_process_copilot_request(socratic_copilot, test_user_id):
    """Test processing a request with copilot"""
    request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Write a Python script to parse a CSV file",
        session_id="test_session",
    )

    assert isinstance(request, CopilotRequest)
    assert request.user_id == test_user_id
    assert request.task_category == "code"
    assert len(request.checkpoints) > 0
    assert request.request_id in socratic_copilot.active_requests


@pytest.mark.asyncio
async def test_get_probes(socratic_copilot, test_user_id):
    """Test getting checkpoint probes"""
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Create a presentation about AI",
        session_id="test_session",
    )

    # Get first probe
    probe = await socratic_copilot.get_next_probe(copilot_request.request_id)

    assert probe is not None
    assert probe.question
    assert "just guess" in probe.delegation_trigger.lower()

    # Probe should match first checkpoint
    assert probe.checkpoint_id == copilot_request.checkpoints[0].checkpoint_id


@pytest.mark.asyncio
async def test_high_ari_response(socratic_copilot, test_user_id):
    """Test user providing answer (HIGH ARI)"""
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Write email to team",
        session_id="test_session",
    )

    probe = await socratic_copilot.get_next_probe(copilot_request.request_id)

    # User provides answer (demonstrates capability)
    response = await socratic_copilot.submit_checkpoint_response(
        request_id=copilot_request.request_id,
        checkpoint_id=probe.checkpoint_id,
        response_text="The main points are: 1) Project status, 2) Next milestones, 3) Action items",
    )

    assert response.response_type == CheckpointResponse.PROVIDED
    assert response.demonstrated_capability is True
    assert copilot_request.high_ari_count == 1
    assert copilot_request.low_ari_count == 0


@pytest.mark.asyncio
async def test_low_ari_delegation(socratic_copilot, test_user_id):
    """Test user delegating (LOW ARI)"""
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Build database schema",
        session_id="test_session",
    )

    probe = await socratic_copilot.get_next_probe(copilot_request.request_id)

    # User delegates (no capability demonstrated)
    response = await socratic_copilot.submit_checkpoint_response(
        request_id=copilot_request.request_id,
        checkpoint_id=probe.checkpoint_id,
        response_text="I don't know, just guess",
    )

    assert response.response_type == CheckpointResponse.DELEGATED
    assert response.demonstrated_capability is False
    assert copilot_request.low_ari_count == 1
    assert copilot_request.high_ari_count == 0


@pytest.mark.asyncio
async def test_complete_copilot_request(socratic_copilot, test_user_id):
    """Test completing full copilot workflow"""
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Draft marketing copy",
        session_id="test_session",
    )

    # Answer all checkpoints
    while True:
        probe = await socratic_copilot.get_next_probe(copilot_request.request_id)
        if probe is None:
            break

        await socratic_copilot.submit_checkpoint_response(
            request_id=copilot_request.request_id,
            checkpoint_id=probe.checkpoint_id,
            response_text="User's answer",
        )

    # Complete request
    result = await socratic_copilot.complete_request(copilot_request.request_id)

    assert result["request_id"] == copilot_request.request_id
    assert "final_output" in result
    assert "ari_score" in result
    assert 0.0 <= result["ari_score"] <= 1.0
    assert copilot_request.request_id not in socratic_copilot.active_requests


@pytest.mark.asyncio
async def test_mixed_responses(socratic_copilot, test_user_id):
    """Test mix of provided answers and delegations"""
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Design API endpoints",
        session_id="test_session",
    )

    responses = [
        "GET /api/users",  # Provided answer
        "just guess",      # Delegation
    ]

    for response_text in responses:
        probe = await socratic_copilot.get_next_probe(copilot_request.request_id)
        if probe is None:
            break

        await socratic_copilot.submit_checkpoint_response(
            request_id=copilot_request.request_id,
            checkpoint_id=probe.checkpoint_id,
            response_text=response_text,
        )

    result = await socratic_copilot.complete_request(copilot_request.request_id)

    # Should have mixed ARI score
    assert copilot_request.high_ari_count >= 1
    assert copilot_request.low_ari_count >= 1
    assert 0.0 < result["ari_score"] < 1.0


@pytest.mark.asyncio
async def test_ari_capability_recording(socratic_copilot, ari_monitor, test_user_id):
    """Test that ARI-Capability snapshots are recorded"""
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Write unit tests",
        session_id="test_session",
    )

    # Answer all checkpoints
    while True:
        probe = await socratic_copilot.get_next_probe(copilot_request.request_id)
        if probe is None:
            break

        await socratic_copilot.submit_checkpoint_response(
            request_id=copilot_request.request_id,
            checkpoint_id=probe.checkpoint_id,
            response_text="User answer",
        )

    await socratic_copilot.complete_request(copilot_request.request_id)

    # Check ARI snapshot recorded
    assert test_user_id in ari_monitor.snapshots
    snapshots = ari_monitor.snapshots[test_user_id]
    assert len(snapshots) > 0

    snapshot = snapshots[-1]
    assert "copilot" in snapshot.task_type
    assert "high_ari_count" in snapshot.metadata
    assert "low_ari_count" in snapshot.metadata


@pytest.mark.asyncio
async def test_capability_gap_tracking(socratic_copilot, context_manager, test_user_id):
    """Test that capability gaps are tracked"""
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Implement authentication",
        session_id="test_session",
    )

    # Delegate all checkpoints (create gaps)
    while True:
        probe = await socratic_copilot.get_next_probe(copilot_request.request_id)
        if probe is None:
            break

        await socratic_copilot.submit_checkpoint_response(
            request_id=copilot_request.request_id,
            checkpoint_id=probe.checkpoint_id,
            response_text="I don't know, you decide",
        )

    await socratic_copilot.complete_request(copilot_request.request_id)

    # Check that gaps were tracked in context
    memories = await context_manager.search_memories(
        user_id=test_user_id,
        query="capability_gap",
        memory_types=[MemoryType.SKILL],
        tags={"capability_gap"},
        limit=10,
    )

    assert len(memories) > 0


@pytest.mark.asyncio
async def test_get_capability_profile(socratic_copilot, context_manager, test_user_id):
    """Test getting capability profile"""
    # Process a request first
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Write SQL queries",
        session_id="test_session",
    )

    # Complete with some delegations
    while True:
        probe = await socratic_copilot.get_next_probe(copilot_request.request_id)
        if probe is None:
            break

        await socratic_copilot.submit_checkpoint_response(
            request_id=copilot_request.request_id,
            checkpoint_id=probe.checkpoint_id,
            response_text="just guess",
        )

    await socratic_copilot.complete_request(copilot_request.request_id)

    # Get profile
    profile = await socratic_copilot.get_capability_profile(
        user_id=test_user_id,
        task_category="code",
    )

    assert profile["task_category"] == "code"
    assert profile["requests_processed"] >= 1
    assert 0.0 <= profile["average_ari"] <= 1.0


# ============================================================================
# Integration Tests (Both Systems Together)
# ============================================================================

@pytest.mark.asyncio
async def test_deep_dive_then_copilot(
    learn_about_me,
    socratic_copilot,
    ari_monitor,
    test_user_id,
):
    """Test using Deep Dive to build profile, then Copilot measures application"""
    # Phase 1: Deep Dive to establish skill ceiling
    session = await learn_about_me.start_deep_dive(test_user_id, "python")

    for i in range(2):
        question = await learn_about_me.get_next_question(test_user_id)
        await learn_about_me.submit_response(
            user_id=test_user_id,
            question_id=question.question_id,
            response_text="Strong understanding demonstrated",
        )

    await learn_about_me.exit_deep_dive(test_user_id)

    # Check profile created
    profile = await learn_about_me.get_knowledge_profile(test_user_id, "python")
    assert profile is not None

    # Phase 2: Copilot measures capability in practice
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Write Python function",
        session_id="test_session",
    )

    while True:
        probe = await socratic_copilot.get_next_probe(copilot_request.request_id)
        if probe is None:
            break

        await socratic_copilot.submit_checkpoint_response(
            request_id=copilot_request.request_id,
            checkpoint_id=probe.checkpoint_id,
            response_text="User provides answer",
        )

    result = await socratic_copilot.complete_request(copilot_request.request_id)

    # Both systems should have recorded ARI snapshots
    assert len(ari_monitor.snapshots[test_user_id]) >= 3  # 2 from Deep Dive + 1 from Copilot


@pytest.mark.asyncio
async def test_copilot_identifies_gaps_deep_dive_fills(
    socratic_copilot,
    learn_about_me,
    test_user_id,
):
    """Test Copilot identifying gaps, then Deep Dive filling them"""
    # Phase 1: Copilot identifies capability gaps
    copilot_request = await socratic_copilot.process_request(
        user_id=test_user_id,
        request="Implement sorting algorithm",
        session_id="test_session",
    )

    # User struggles/delegates
    while True:
        probe = await socratic_copilot.get_next_probe(copilot_request.request_id)
        if probe is None:
            break

        await socratic_copilot.submit_checkpoint_response(
            request_id=copilot_request.request_id,
            checkpoint_id=probe.checkpoint_id,
            response_text="not sure",
        )

    result = await socratic_copilot.complete_request(copilot_request.request_id)

    # Low ARI score indicates gaps
    assert result["ari_score"] < 0.5

    # Phase 2: User opts into Deep Dive to learn
    session = await learn_about_me.start_deep_dive(test_user_id, "algorithms")

    question = await learn_about_me.get_next_question(test_user_id)

    # User engages with learning
    await learn_about_me.submit_response(
        user_id=test_user_id,
        question_id=question.question_id,
        response_text="Now I understand the concept better",
    )

    await learn_about_me.exit_deep_dive(test_user_id)

    # System has tracked both delegation and learning
    profile = await learn_about_me.get_knowledge_profile(test_user_id, "algorithms")
    assert profile is not None
