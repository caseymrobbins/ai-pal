"""
Teaching Interface - Learn-by-Teaching Mode UI

User-facing interface for the Protégé Pipeline.
Provides interactive teaching experience where user teaches AI.

Powered by:
- ProtegePipeline (backend module)
- GoalIngestor (creates teaching goals)
- ScopingAgent (breaks teaching into concepts)
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from loguru import logger

from ..modules import ProtegePipeline, TeachingSession, Explanation
from ..models import GoalPacket, AtomicBlock


@dataclass
class TeachingPrompt:
    """
    Prompt for user to teach a concept

    Displayed to user as the AI "student" asking for explanation.
    """
    session_id: str
    concept: str
    student_question: str
    context: Optional[str] = None
    difficulty_hint: Optional[str] = None  # "Start simple" or "Go deeper"


class TeachingInterface:
    """
    User-facing interface for learn-by-teaching mode

    Provides methods for:
    - Starting teaching sessions
    - Receiving teaching prompts
    - Submitting explanations
    - Getting student feedback
    - Viewing teaching progress
    """

    def __init__(self, protege_pipeline: ProtegePipeline):
        """
        Initialize Teaching Interface

        Args:
            protege_pipeline: ProtegePipeline backend module
        """
        self.protege = protege_pipeline

        logger.info("Teaching Interface initialized")

    async def start_teaching(
        self,
        user_id: str,
        learning_goal: GoalPacket
    ) -> TeachingSession:
        """
        Start teaching mode from a learning goal

        Reframes "Learn X" as "Teach me X"

        Args:
            user_id: User who will teach
            learning_goal: Learning goal to reframe

        Returns:
            TeachingSession
        """
        logger.info(
            f"Starting teaching mode for user {user_id}: "
            f"'{learning_goal.description}'"
        )

        # Extract subject from learning goal
        subject = await self._extract_subject(learning_goal.description)

        # Start session
        session = await self.protege.start_teaching_mode(
            user_id=user_id,
            subject=subject,
            from_learning_goal=True
        )

        logger.info(f"Teaching session {session.session_id} started")

        return session

    async def get_teaching_prompt(
        self,
        user_id: str,
        concept: Optional[str] = None
    ) -> TeachingPrompt:
        """
        Get next concept for user to teach

        AI "student" asks user to explain something.

        Args:
            user_id: User who will teach
            concept: Specific concept to teach (optional)

        Returns:
            TeachingPrompt with student question
        """
        logger.info(f"Getting teaching prompt for user {user_id}, concept: {concept}")

        # Get active session
        session = self.protege.active_sessions.get(user_id)
        if not session:
            logger.warning(f"No active session for user {user_id}")
            return None

        # If no concept specified, choose next concept
        if not concept:
            concept = await self._choose_next_concept(session)

        # Request explanation from protege pipeline
        request = await self.protege.request_explanation(
            user_id=user_id,
            concept=concept,
            context=None
        )

        # Create prompt
        prompt = TeachingPrompt(
            session_id=request["session_id"],
            concept=request["concept"],
            student_question=request["student_question"],
            context=request.get("context"),
            difficulty_hint=await self._get_difficulty_hint(session)
        )

        logger.debug(f"Teaching prompt: '{prompt.student_question}'")

        return prompt

    async def submit_explanation(
        self,
        user_id: str,
        concept: str,
        explanation_text: str
    ) -> Dict[str, Any]:
        """
        Submit user's explanation

        Args:
            user_id: User submitting explanation
            concept: Concept being explained
            explanation_text: User's teaching

        Returns:
            Feedback from AI "student"
        """
        logger.info(
            f"Receiving explanation from user {user_id} for '{concept}': "
            f"{len(explanation_text)} chars"
        )

        # Pass to protege pipeline
        explanation = await self.protege.receive_explanation(
            user_id=user_id,
            concept=concept,
            explanation_text=explanation_text
        )

        if not explanation:
            return {"error": "No active teaching session"}

        # Format feedback for display
        feedback = {
            "understood": explanation.student_understood,
            "student_feedback": explanation.student_feedback,
            "quality_scores": {
                "clarity": explanation.clarity_score,
                "completeness": explanation.completeness_score,
                "depth": explanation.depth_score,
            },
            "follow_up_question": None,
        }

        # Check if student has follow-up question
        session = self.protege.active_sessions.get(user_id)
        if session:
            follow_up = await self.protege.generate_follow_up_question(
                session_id=session.session_id,
                last_concept=concept,
                understanding_level=session.understanding_level
            )
            feedback["follow_up_question"] = follow_up

        logger.info(
            f"Feedback: understood={feedback['understood']}, "
            f"follow_up={feedback['follow_up_question'] is not None}"
        )

        return feedback

    async def get_teaching_progress(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Show user their teaching progress

        Args:
            user_id: User to show progress for

        Returns:
            Progress data
        """
        logger.info(f"Getting teaching progress for user {user_id}")

        session = self.protege.active_sessions.get(user_id)
        if not session:
            return {"error": "No active teaching session"}

        progress = {
            "session_id": session.session_id,
            "subject": session.subject,
            "concepts_explained": len(session.concepts_explained),
            "concepts_mastered": session.concepts_mastered,
            "understanding_level": session.understanding_level,
            "teaching_quality": session.teaching_quality_score,
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_explanation_at.isoformat() if session.last_explanation_at else None,
        }

        return progress

    async def complete_teaching_session(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Complete teaching session and show results

        Args:
            user_id: User completing session

        Returns:
            Session summary
        """
        logger.info(f"Completing teaching session for user {user_id}")

        session = self.protege.active_sessions.get(user_id)
        if not session:
            return {"error": "No active teaching session"}

        # Complete session
        completed_session = await self.protege.complete_session(
            user_id=user_id,
            session_id=session.session_id
        )

        # Format summary
        summary = {
            "session_id": completed_session.session_id,
            "subject": completed_session.subject,
            "concepts_taught": completed_session.concepts_explained,
            "concepts_mastered": completed_session.concepts_mastered,
            "teaching_quality": completed_session.teaching_quality_score,
            "final_understanding": completed_session.understanding_level,
            "duration_minutes": (
                (completed_session.completed_at - completed_session.started_at).total_seconds() / 60
                if completed_session.completed_at
                else 0
            ),
            "celebration_message": await self._generate_celebration(completed_session),
        }

        logger.info(
            f"Teaching session complete: {summary['concepts_mastered']} concepts mastered, "
            f"quality: {summary['teaching_quality']:.2f}"
        )

        return summary

    # ===== HELPER METHODS =====

    async def _extract_subject(self, learning_goal_description: str) -> str:
        """Extract subject from learning goal description"""
        # Simple extraction (would be more sophisticated in full version)
        # "Learn Python" -> "Python"
        # "Understand machine learning" -> "machine learning"

        description_lower = learning_goal_description.lower()

        if "learn" in description_lower:
            # Find what comes after "learn"
            parts = description_lower.split("learn")
            if len(parts) > 1:
                subject = parts[1].strip()
                return subject.capitalize()

        if "understand" in description_lower:
            parts = description_lower.split("understand")
            if len(parts) > 1:
                subject = parts[1].strip()
                return subject.capitalize()

        # Default: use full description
        return learning_goal_description

    async def _choose_next_concept(self, session: TeachingSession) -> str:
        """Choose next concept to teach"""
        # Simple logic - in full version would use scoping agent
        if not session.concepts_explained:
            return f"{session.subject} basics"
        else:
            return f"{session.subject} advanced topic {len(session.concepts_explained) + 1}"

    async def _get_difficulty_hint(self, session: TeachingSession) -> str:
        """Get hint about difficulty level for user"""
        if session.understanding_level < 0.5:
            return "Try explaining it more simply - imagine I'm a complete beginner"
        elif session.understanding_level < 0.75:
            return "I'm getting the basics, so feel free to go a bit deeper"
        else:
            return "I'm following well! You can dive into advanced details"

    async def _generate_celebration(self, session: TeachingSession) -> str:
        """Generate celebration message for completed session"""
        if session.teaching_quality_score >= 0.8:
            return f"Excellent teaching! You mastered {session.concepts_mastered} concepts. You're a natural teacher!"
        elif session.teaching_quality_score >= 0.6:
            return f"Great job! Teaching {session.concepts_mastered} concepts really solidified your understanding."
        else:
            return f"Nice work! Teaching {session.concepts_mastered} concepts helped you learn through explaining."
