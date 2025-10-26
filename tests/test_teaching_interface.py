"""
Tests for Teaching Interface - Learn-by-Teaching Mode UI

Tests the user-facing interface layer for the Protégé Pipeline.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
from datetime import datetime

from ai_pal.ffe.interfaces.teaching_interface import (
    TeachingInterface,
    TeachingPrompt,
)
from ai_pal.ffe.modules.protege_pipeline import ProtegePipeline
from ai_pal.ffe.models import GoalPacket, GoalStatus


@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def protege_pipeline(temp_storage):
    """Create ProtegePipeline backend"""
    return ProtegePipeline(storage_dir=temp_storage)


@pytest.fixture
def teaching_interface(protege_pipeline):
    """Create TeachingInterface"""
    return TeachingInterface(protege_pipeline=protege_pipeline)


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return "test_user_interface"


@pytest.fixture
def learning_goal():
    """Test learning goal"""
    return GoalPacket(
        goal_id="goal_001",
        user_id="test_user_interface",
        description="Learn Python programming",
        goal_type="learning",
        status=GoalStatus.ACTIVE,
        priority_score=0.8,
        created_at=datetime.now(),
    )


class TestTeachingInterfaceInitialization:
    """Test Teaching Interface initialization"""

    def test_initialization(self, teaching_interface, protege_pipeline):
        """Test: Interface initializes with backend"""
        assert teaching_interface is not None
        assert teaching_interface.protege == protege_pipeline

    def test_backend_connection(self, teaching_interface):
        """Test: Interface has access to backend methods"""
        assert hasattr(teaching_interface.protege, 'start_teaching_mode')
        assert hasattr(teaching_interface.protege, 'request_explanation')
        assert hasattr(teaching_interface.protege, 'receive_explanation')


class TestStartTeaching:
    """Test starting teaching sessions"""

    @pytest.mark.asyncio
    async def test_start_teaching_from_goal(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Start teaching from learning goal"""
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Verify session created
        assert session is not None
        assert session.user_id == test_user_id
        assert "Python" in session.subject  # Extracted from goal

    @pytest.mark.asyncio
    async def test_subject_extraction_learn(self, teaching_interface):
        """Test: Extract subject from 'Learn X' goal"""
        subject = await teaching_interface._extract_subject(
            "Learn machine learning basics"
        )

        assert "machine learning" in subject.lower()

    @pytest.mark.asyncio
    async def test_subject_extraction_understand(self, teaching_interface):
        """Test: Extract subject from 'Understand X' goal"""
        subject = await teaching_interface._extract_subject(
            "Understand neural networks"
        )

        assert "neural networks" in subject.lower()

    @pytest.mark.asyncio
    async def test_subject_extraction_fallback(self, teaching_interface):
        """Test: Use full description if no keyword found"""
        description = "Deep dive into quantum computing"
        subject = await teaching_interface._extract_subject(description)

        assert subject == description


class TestTeachingPrompts:
    """Test teaching prompt generation"""

    @pytest.mark.asyncio
    async def test_get_teaching_prompt(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Get teaching prompt for active session"""
        # Start session
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Get prompt
        prompt = await teaching_interface.get_teaching_prompt(
            user_id=test_user_id,
            concept="variables"
        )

        # Verify prompt
        assert isinstance(prompt, TeachingPrompt)
        assert prompt.concept == "variables"
        assert prompt.student_question is not None
        assert len(prompt.student_question) > 0
        assert prompt.session_id is not None

    @pytest.mark.asyncio
    async def test_get_prompt_no_session(self, teaching_interface, test_user_id):
        """Test: Get prompt with no active session returns None"""
        prompt = await teaching_interface.get_teaching_prompt(
            user_id=test_user_id,
            concept="test"
        )

        assert prompt is None

    @pytest.mark.asyncio
    async def test_prompt_auto_concept_selection(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Prompt auto-selects next concept if not specified"""
        # Start session
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Get prompt without specifying concept
        prompt = await teaching_interface.get_teaching_prompt(
            user_id=test_user_id,
            concept=None
        )

        # Should auto-select concept
        assert prompt is not None
        assert prompt.concept is not None

    @pytest.mark.asyncio
    async def test_difficulty_hint_beginner(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Difficulty hint for low understanding"""
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )
        session.understanding_level = 0.3

        hint = await teaching_interface._get_difficulty_hint(session)

        assert "simpl" in hint.lower() or "beginner" in hint.lower()

    @pytest.mark.asyncio
    async def test_difficulty_hint_intermediate(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Difficulty hint for medium understanding"""
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )
        session.understanding_level = 0.6

        hint = await teaching_interface._get_difficulty_hint(session)

        assert "deeper" in hint.lower() or "basics" in hint.lower()

    @pytest.mark.asyncio
    async def test_difficulty_hint_advanced(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Difficulty hint for high understanding"""
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )
        session.understanding_level = 0.85

        hint = await teaching_interface._get_difficulty_hint(session)

        assert "advanced" in hint.lower() or "detail" in hint.lower()


class TestSubmitExplanation:
    """Test explanation submission and feedback"""

    @pytest.mark.asyncio
    async def test_submit_explanation_success(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Submit explanation successfully"""
        # Start session
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Submit explanation
        feedback = await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="functions",
            explanation_text=(
                "Functions are reusable blocks of code. For example, def greet(): print('Hi'). "
                "They help organize code because you can call them multiple times. "
                "Specifically, they take inputs and return outputs."
            )
        )

        # Verify feedback
        assert feedback is not None
        assert "understood" in feedback
        assert "student_feedback" in feedback
        assert "quality_scores" in feedback
        assert feedback["student_feedback"] is not None

        # Should have quality scores
        scores = feedback["quality_scores"]
        assert "clarity" in scores
        assert "completeness" in scores
        assert "depth" in scores

    @pytest.mark.asyncio
    async def test_submit_explanation_no_session(
        self, teaching_interface, test_user_id
    ):
        """Test: Submit explanation with no session returns error"""
        feedback = await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="test",
            explanation_text="Test explanation"
        )

        assert "error" in feedback

    @pytest.mark.asyncio
    async def test_submit_with_follow_up_question(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Submit explanation that triggers follow-up question"""
        # Start session
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Submit mediocre explanation (will trigger follow-up)
        feedback = await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="loops",
            explanation_text="Loops repeat things."  # Too short
        )

        # Should have follow-up question
        assert "follow_up_question" in feedback
        # Might be None if understanding is too high, so just check it's present

    @pytest.mark.asyncio
    async def test_quality_scores_returned(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Quality scores are returned in feedback"""
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        feedback = await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="classes",
            explanation_text=(
                "Classes are blueprints for objects. For example, class Dog: defines a dog type. "
                "They're important because they enable object-oriented programming. "
                "Specifically, you can create multiple instances from one class."
            )
        )

        scores = feedback["quality_scores"]
        assert 0.0 <= scores["clarity"] <= 1.0
        assert 0.0 <= scores["completeness"] <= 1.0
        assert 0.0 <= scores["depth"] <= 1.0


class TestTeachingProgress:
    """Test teaching progress tracking"""

    @pytest.mark.asyncio
    async def test_get_teaching_progress(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Get teaching progress"""
        # Start session
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Submit explanation
        await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="variables",
            explanation_text=(
                "Variables store values. For example, x = 5. "
                "They're fundamental because all programs use them. "
                "Specifically, they're named memory locations."
            )
        )

        # Get progress
        progress = await teaching_interface.get_teaching_progress(
            user_id=test_user_id
        )

        # Verify progress data
        assert progress is not None
        assert "session_id" in progress
        assert "subject" in progress
        assert "concepts_explained" in progress
        assert "concepts_mastered" in progress
        assert "understanding_level" in progress
        assert "teaching_quality" in progress

        assert progress["concepts_explained"] >= 1

    @pytest.mark.asyncio
    async def test_progress_no_session(self, teaching_interface, test_user_id):
        """Test: Get progress with no active session returns error"""
        progress = await teaching_interface.get_teaching_progress(
            user_id=test_user_id
        )

        assert "error" in progress

    @pytest.mark.asyncio
    async def test_progress_updates_with_activity(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Progress updates as user teaches"""
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Get initial progress
        progress1 = await teaching_interface.get_teaching_progress(test_user_id)
        initial_concepts = progress1["concepts_explained"]

        # Submit explanation
        await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="new_concept",
            explanation_text="Detailed explanation with examples and reasoning."
        )

        # Get updated progress
        progress2 = await teaching_interface.get_teaching_progress(test_user_id)

        # Should have more concepts explained
        assert progress2["concepts_explained"] > initial_concepts


class TestSessionCompletion:
    """Test completing teaching sessions"""

    @pytest.mark.asyncio
    async def test_complete_teaching_session(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Complete teaching session successfully"""
        # Start and teach
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="lists",
            explanation_text=(
                "Lists are ordered collections in Python. For example, [1, 2, 3]. "
                "They're mutable, meaning you can change them. Specifically, use append() to add items. "
                "Therefore, they're versatile for storing multiple values."
            )
        )

        # Complete session
        summary = await teaching_interface.complete_teaching_session(
            user_id=test_user_id
        )

        # Verify summary
        assert summary is not None
        assert "session_id" in summary
        assert "subject" in summary
        assert "concepts_taught" in summary
        assert "concepts_mastered" in summary
        assert "teaching_quality" in summary
        assert "final_understanding" in summary
        assert "duration_minutes" in summary
        assert "celebration_message" in summary

        assert len(summary["celebration_message"]) > 0

    @pytest.mark.asyncio
    async def test_complete_no_session(self, teaching_interface, test_user_id):
        """Test: Complete with no active session returns error"""
        summary = await teaching_interface.complete_teaching_session(
            user_id=test_user_id
        )

        assert "error" in summary

    @pytest.mark.asyncio
    async def test_celebration_message_high_quality(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: High quality teaching gets enthusiastic celebration"""
        # Start session
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Simulate high quality teaching
        session.teaching_quality_score = 0.9
        session.concepts_mastered = 5

        celebration = await teaching_interface._generate_celebration(session)

        assert "excellent" in celebration.lower() or "great" in celebration.lower()

    @pytest.mark.asyncio
    async def test_celebration_message_medium_quality(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Medium quality teaching gets encouraging celebration"""
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        session.teaching_quality_score = 0.7
        session.concepts_mastered = 3

        celebration = await teaching_interface._generate_celebration(session)

        assert "good" in celebration.lower() or "great" in celebration.lower()

    @pytest.mark.asyncio
    async def test_session_duration_calculated(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Session duration is calculated correctly"""
        # Start session
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Wait a moment
        await asyncio.sleep(0.1)

        # Complete
        summary = await teaching_interface.complete_teaching_session(
            user_id=test_user_id
        )

        # Duration should be calculated
        assert summary["duration_minutes"] >= 0


class TestConceptSelection:
    """Test automatic concept selection"""

    @pytest.mark.asyncio
    async def test_choose_first_concept(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: First concept is 'basics'"""
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        concept = await teaching_interface._choose_next_concept(session)

        assert "basics" in concept.lower()

    @pytest.mark.asyncio
    async def test_choose_next_concepts(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Subsequent concepts are numbered"""
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        # Add some explained concepts
        session.concepts_explained = ["concept1", "concept2"]

        concept = await teaching_interface._choose_next_concept(session)

        # Should reference advanced or numbered topics
        assert "advanced" in concept.lower() or any(
            str(i) in concept for i in range(1, 10)
        )


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_explanation_text(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Empty explanation handled gracefully"""
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        feedback = await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="test",
            explanation_text=""
        )

        # Should still return feedback (not understood)
        assert feedback is not None
        assert feedback["understood"] is False

    @pytest.mark.asyncio
    async def test_very_long_explanation(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Very long explanation handled"""
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        long_text = (
            "This is a very detailed explanation. " * 100 +
            "For example, here are many examples. " * 50 +
            "Therefore, this demonstrates deep understanding. " * 50
        )

        feedback = await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="test",
            explanation_text=long_text
        )

        # Should handle gracefully
        assert feedback is not None
        assert feedback["quality_scores"]["completeness"] > 0.8

    @pytest.mark.asyncio
    async def test_special_characters_in_concept(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Special characters in concept names handled"""
        await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )

        concept = "C++ pointers & references"

        feedback = await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept=concept,
            explanation_text="Detailed explanation of pointers and references in C++."
        )

        assert feedback is not None


class TestIntegration:
    """Test integration between interface and backend"""

    @pytest.mark.asyncio
    async def test_full_teaching_workflow(
        self, teaching_interface, test_user_id, learning_goal
    ):
        """Test: Complete teaching workflow from start to finish"""
        # 1. Start teaching
        session = await teaching_interface.start_teaching(
            user_id=test_user_id,
            learning_goal=learning_goal
        )
        assert session is not None

        # 2. Get first prompt
        prompt = await teaching_interface.get_teaching_prompt(
            user_id=test_user_id,
            concept="variables"
        )
        assert prompt is not None

        # 3. Submit explanation
        feedback = await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="variables",
            explanation_text=(
                "Variables store data in memory. For example, x = 10 creates a variable. "
                "They're essential because programs need to remember values. "
                "Specifically, each variable has a name, type, and value."
            )
        )
        assert feedback["understood"] is True

        # 4. Check progress
        progress = await teaching_interface.get_teaching_progress(test_user_id)
        assert progress["concepts_explained"] == 1

        # 5. Teach another concept
        await teaching_interface.submit_explanation(
            user_id=test_user_id,
            concept="functions",
            explanation_text=(
                "Functions are reusable code blocks. For example, def add(a, b): return a + b. "
                "They organize code because you can call them many times. "
                "Therefore, they reduce code duplication and improve maintainability."
            )
        )

        # 6. Complete session
        summary = await teaching_interface.complete_teaching_session(test_user_id)
        assert summary["concepts_mastered"] >= 1
        assert summary["teaching_quality"] > 0.5
