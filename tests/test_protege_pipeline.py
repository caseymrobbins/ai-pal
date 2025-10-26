"""
Tests for Protégé Pipeline - Learn-by-Teaching Mode

Tests the backend module that transforms learning into teaching opportunities.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
from datetime import datetime

from ai_pal.ffe.modules.protege_pipeline import (
    ProtegePipeline,
    TeachingSession,
    Explanation,
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def protege_pipeline(temp_storage):
    """Create ProtegePipeline instance"""
    return ProtegePipeline(storage_dir=temp_storage)


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return "test_user_protege"


class TestProtegePipelineInitialization:
    """Test Protégé Pipeline initialization"""

    def test_initialization(self, protege_pipeline, temp_storage):
        """Test: Pipeline initializes correctly"""
        assert protege_pipeline is not None
        assert protege_pipeline.storage_dir == temp_storage
        assert protege_pipeline.active_sessions == {}
        assert protege_pipeline.session_history == {}
        assert len(protege_pipeline.student_questions) == 4

    def test_storage_directory_created(self, temp_storage):
        """Test: Storage directory is created if it doesn't exist"""
        new_dir = temp_storage / "protege_test"
        pipeline = ProtegePipeline(storage_dir=new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()


class TestTeachingSessionLifecycle:
    """Test teaching session lifecycle"""

    @pytest.mark.asyncio
    async def test_start_teaching_mode(self, protege_pipeline, test_user_id):
        """Test: Start teaching mode creates session"""
        subject = "Python lists"

        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject=subject,
            from_learning_goal=True
        )

        # Verify session created
        assert session is not None
        assert session.user_id == test_user_id
        assert session.subject == subject
        assert not session.completed
        assert session.understanding_level == 0.0
        assert len(session.concepts_explained) == 0

        # Verify session is active
        assert test_user_id in protege_pipeline.active_sessions
        assert session.session_id in protege_pipeline.session_history

    @pytest.mark.asyncio
    async def test_multiple_sessions_same_user(self, protege_pipeline, test_user_id):
        """Test: Starting new session replaces old active session"""
        # Start first session
        session1 = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Python",
            from_learning_goal=True
        )

        # Start second session
        session2 = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="JavaScript",
            from_learning_goal=True
        )

        # Only second session should be active
        assert protege_pipeline.active_sessions[test_user_id] == session2

        # But both should be in history
        assert session1.session_id in protege_pipeline.session_history
        assert session2.session_id in protege_pipeline.session_history


class TestExplanationFlow:
    """Test explanation request and submission flow"""

    @pytest.mark.asyncio
    async def test_request_explanation(self, protege_pipeline, test_user_id):
        """Test: Request explanation generates student question"""
        # Start session
        await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Machine Learning",
            from_learning_goal=True
        )

        # Request explanation
        concept = "neural networks"
        request = await protege_pipeline.request_explanation(
            user_id=test_user_id,
            concept=concept,
            context=None
        )

        # Verify request
        assert request is not None
        assert request["concept"] == concept
        assert "student_question" in request
        assert "session_id" in request
        assert len(request["student_question"]) > 0

    @pytest.mark.asyncio
    async def test_receive_explanation_good_quality(self, protege_pipeline, test_user_id):
        """Test: Receive good quality explanation"""
        # Start session
        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Python",
            from_learning_goal=True
        )

        # Submit good explanation
        concept = "lists"
        explanation_text = (
            "Lists in Python are ordered collections that can store multiple items. "
            "For example, you can create a list like [1, 2, 3]. "
            "They're useful because you can add, remove, and access items easily. "
            "Specifically, you use append() to add items and you can access items by index. "
            "In other words, lists are like containers that maintain order."
        )

        explanation = await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept=concept,
            explanation_text=explanation_text
        )

        # Verify explanation evaluated
        assert explanation is not None
        assert explanation.concept == concept
        assert explanation.clarity_score > 0.5
        assert explanation.completeness_score > 0.5
        assert explanation.depth_score > 0.5
        assert explanation.student_understood is True
        assert explanation.student_feedback is not None

        # Verify session updated
        updated_session = protege_pipeline.active_sessions[test_user_id]
        assert concept in updated_session.concepts_explained
        assert updated_session.concepts_mastered == 1
        assert updated_session.understanding_level > 0.0

    @pytest.mark.asyncio
    async def test_receive_explanation_poor_quality(self, protege_pipeline, test_user_id):
        """Test: Receive poor quality explanation"""
        # Start session
        await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Python",
            from_learning_goal=True
        )

        # Submit poor explanation (too short, no depth)
        concept = "functions"
        explanation_text = "Functions are code."

        explanation = await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept=concept,
            explanation_text=explanation_text
        )

        # Verify low scores
        assert explanation is not None
        assert explanation.clarity_score < 0.7
        assert explanation.completeness_score < 0.7
        assert explanation.student_understood is False

        # Verify session shows no mastery
        updated_session = protege_pipeline.active_sessions[test_user_id]
        assert updated_session.concepts_mastered == 0


class TestFollowUpQuestions:
    """Test AI student follow-up question generation"""

    @pytest.mark.asyncio
    async def test_follow_up_low_understanding(self, protege_pipeline, test_user_id):
        """Test: Low understanding generates clarification question"""
        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        follow_up = await protege_pipeline.generate_follow_up_question(
            session_id=session.session_id,
            last_concept="variables",
            understanding_level=0.3
        )

        assert follow_up is not None
        assert "clarif" in follow_up.lower() or "explain" in follow_up.lower()

    @pytest.mark.asyncio
    async def test_follow_up_medium_understanding(self, protege_pipeline, test_user_id):
        """Test: Medium understanding generates deeper question"""
        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        follow_up = await protege_pipeline.generate_follow_up_question(
            session_id=session.session_id,
            last_concept="loops",
            understanding_level=0.6
        )

        assert follow_up is not None
        assert "why" in follow_up.lower() or "how" in follow_up.lower()

    @pytest.mark.asyncio
    async def test_follow_up_high_understanding(self, protege_pipeline, test_user_id):
        """Test: High understanding generates application question"""
        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        follow_up = await protege_pipeline.generate_follow_up_question(
            session_id=session.session_id,
            last_concept="classes",
            understanding_level=0.8
        )

        assert follow_up is not None
        assert "use" in follow_up.lower() or "example" in follow_up.lower()

    @pytest.mark.asyncio
    async def test_no_follow_up_full_understanding(self, protege_pipeline, test_user_id):
        """Test: Full understanding generates no follow-up"""
        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        follow_up = await protege_pipeline.generate_follow_up_question(
            session_id=session.session_id,
            last_concept="objects",
            understanding_level=0.95
        )

        assert follow_up is None


class TestSessionCompletion:
    """Test session completion and metrics"""

    @pytest.mark.asyncio
    async def test_complete_session(self, protege_pipeline, test_user_id):
        """Test: Complete teaching session"""
        # Start and run session
        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Python",
            from_learning_goal=True
        )

        # Add some explanations
        await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="lists",
            explanation_text="Lists are ordered collections. For example, [1,2,3]. They're mutable, meaning you can change them. You access items by index."
        )
        await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="tuples",
            explanation_text="Tuples are like lists but immutable. For example, (1,2,3). You can't change them after creation. They're faster than lists."
        )

        # Complete session
        completed_session = await protege_pipeline.complete_session(
            user_id=test_user_id,
            session_id=session.session_id
        )

        # Verify completion
        assert completed_session.completed is True
        assert completed_session.completed_at is not None
        assert completed_session.concepts_mastered >= 0
        assert completed_session.teaching_quality_score > 0.0

        # Verify removed from active
        assert test_user_id not in protege_pipeline.active_sessions

        # But still in history
        assert session.session_id in protege_pipeline.session_history

    @pytest.mark.asyncio
    async def test_complete_nonexistent_session(self, protege_pipeline, test_user_id):
        """Test: Completing nonexistent session returns None"""
        result = await protege_pipeline.complete_session(
            user_id=test_user_id,
            session_id="nonexistent_session"
        )

        assert result is None


class TestPersistence:
    """Test session persistence"""

    @pytest.mark.asyncio
    async def test_session_persistence(self, protege_pipeline, test_user_id):
        """Test: Sessions are persisted to disk"""
        # Create session with explanations
        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Testing",
            from_learning_goal=True
        )

        await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="unit tests",
            explanation_text="Unit tests verify individual functions work correctly. For example, testing a sum function. They help catch bugs early."
        )

        # Check file exists
        session_file = protege_pipeline.storage_dir / f"{session.session_id}.json"
        assert session_file.exists()

        # Verify file has content
        import json
        with open(session_file, 'r') as f:
            data = json.load(f)

        assert data["session_id"] == session.session_id
        assert data["user_id"] == test_user_id
        assert data["subject"] == "Testing"
        assert len(data["concepts_explained"]) == 1


class TestExplanationEvaluation:
    """Test explanation quality evaluation"""

    @pytest.mark.asyncio
    async def test_depth_keywords_detection(self, protege_pipeline, test_user_id):
        """Test: Depth score increases with depth keywords"""
        await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        # Explanation with depth keywords
        explanation_text = (
            "Variables store data because they allocate memory. "
            "Therefore, you can reuse values. For example, x = 5. "
            "Specifically, the variable points to a memory address. "
            "In other words, it's a reference to stored data."
        )

        explanation = await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="variables",
            explanation_text=explanation_text
        )

        # Should have high depth score due to keywords
        assert explanation.depth_score > 0.6

    @pytest.mark.asyncio
    async def test_length_affects_scores(self, protege_pipeline, test_user_id):
        """Test: Explanation length affects clarity and completeness"""
        await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        # Very short explanation
        short_exp = await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="loops",
            explanation_text="Loops repeat code."
        )

        # Long explanation
        long_exp = await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="conditionals",
            explanation_text=(
                "Conditionals allow code to make decisions. For example, if statements check conditions. "
                "When the condition is True, the code block runs. Otherwise, it skips. "
                "You can also use elif for multiple conditions, and else as a fallback. "
                "This is important because it enables dynamic program behavior. "
                "Specifically, your program can respond to different inputs differently."
            )
        )

        # Long explanation should have better scores
        assert long_exp.clarity_score > short_exp.clarity_score
        assert long_exp.completeness_score > short_exp.completeness_score


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_request_explanation_no_session(self, protege_pipeline, test_user_id):
        """Test: Request explanation with no active session creates ad-hoc session"""
        request = await protege_pipeline.request_explanation(
            user_id=test_user_id,
            concept="testing",
            context=None
        )

        # Should create ad-hoc session
        assert request is not None
        assert test_user_id in protege_pipeline.active_sessions

    @pytest.mark.asyncio
    async def test_receive_explanation_no_session(self, protege_pipeline, test_user_id):
        """Test: Receive explanation with no active session returns None"""
        explanation = await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="testing",
            explanation_text="Test content"
        )

        assert explanation is None

    @pytest.mark.asyncio
    async def test_empty_explanation_text(self, protege_pipeline, test_user_id):
        """Test: Empty explanation text is handled"""
        await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        explanation = await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="test",
            explanation_text=""
        )

        # Should still process but with low scores
        assert explanation is not None
        assert explanation.clarity_score < 0.5
        assert explanation.completeness_score < 0.5
        assert explanation.student_understood is False


class TestMetricsTracking:
    """Test metrics and progress tracking"""

    @pytest.mark.asyncio
    async def test_understanding_level_tracking(self, protege_pipeline, test_user_id):
        """Test: Understanding level updates with each explanation"""
        session = await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        initial_understanding = session.understanding_level
        assert initial_understanding == 0.0

        # Submit good explanation
        await protege_pipeline.receive_explanation(
            user_id=test_user_id,
            concept="concept1",
            explanation_text=(
                "This is a comprehensive explanation with good length. "
                "For example, it includes examples. Therefore, it demonstrates understanding. "
                "Specifically, it covers key points thoroughly."
            )
        )

        updated_session = protege_pipeline.active_sessions[test_user_id]
        assert updated_session.understanding_level > initial_understanding

    @pytest.mark.asyncio
    async def test_concepts_mastered_tracking(self, protege_pipeline, test_user_id):
        """Test: Concepts mastered count increases with good explanations"""
        await protege_pipeline.start_teaching_mode(
            user_id=test_user_id,
            subject="Test",
            from_learning_goal=True
        )

        # Submit 3 good explanations
        for i in range(3):
            await protege_pipeline.receive_explanation(
                user_id=test_user_id,
                concept=f"concept_{i}",
                explanation_text=(
                    f"Detailed explanation of concept {i}. For example, here's an example. "
                    f"Therefore, this demonstrates understanding. Specifically, it's thorough. "
                    f"Because it covers all aspects in depth."
                )
            )

        session = protege_pipeline.active_sessions[test_user_id]
        assert session.concepts_mastered >= 2  # At least 2 should be "mastered"
        assert len(session.concepts_explained) == 3
