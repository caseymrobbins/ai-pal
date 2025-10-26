"""
Protégé Pipeline - Learn-by-Teaching Mode

Reframes "learning" tasks as "teaching" tasks to boost engagement and retention.
Research shows that teaching is one of the most effective learning methods.

The AI acts as an eager "student" who wants to learn from the user.
This creates:
- Higher engagement (teaching > consuming)
- Better retention (explain to understand)
- Pride-based motivation (identity as "teacher")
- Active recall practice

Powered by:
- GoalIngestor (sets task as "Teach me X")
- ScopingAgent (breaks teaching into atomic explanations)
- GrowthScaffold (detects weak areas, asks user to teach them)

Integrates with:
- Teaching Interface (captures explanations)
- MultiModelOrchestrator (generates student questions/feedback)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from loguru import logger

from ..models import (
    GoalPacket,
    AtomicBlock,
    TaskComplexityLevel,
    GoalStatus,
)


@dataclass
class TeachingSession:
    """
    Learn-by-teaching session

    Tracks the user's progress as they "teach" a subject to the AI.
    """
    session_id: str
    user_id: str
    subject: str  # What user is "teaching"

    # Teaching blocks (each is one concept explained)
    explanation_blocks: List[AtomicBlock] = field(default_factory=list)
    concepts_explained: List[str] = field(default_factory=list)

    # "Student AI" feedback
    understanding_level: float = 0.0  # How well "student" understood (0-1)
    follow_up_questions: List[str] = field(default_factory=list)
    confusion_points: List[str] = field(default_factory=list)  # What "student" is confused about

    # Session tracking
    started_at: datetime = field(default_factory=datetime.now)
    last_explanation_at: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None

    # Learning effectiveness
    concepts_mastered: int = 0  # How many concepts user fully explained
    teaching_quality_score: float = 0.0  # Overall teaching quality (0-1)


@dataclass
class Explanation:
    """
    A single explanation given by user

    Represents one teaching moment.
    """
    explanation_id: str
    session_id: str
    user_id: str
    concept: str  # What was explained
    explanation_text: str  # User's explanation

    # Quality metrics
    clarity_score: float = 0.0  # How clear was the explanation? (0-1)
    completeness_score: float = 0.0  # How complete? (0-1)
    depth_score: float = 0.0  # How deep was understanding? (0-1)

    # Student response
    student_understood: bool = False
    student_feedback: Optional[str] = None

    # Metadata
    given_at: datetime = field(default_factory=datetime.now)


class ProtegePipeline:
    """
    Protégé Pipeline - Learn-by-teaching mode backend

    Transforms learning tasks into teaching opportunities.

    Key principles:
    - User is the "teacher", AI is eager "student"
    - Teaching forces active recall and synthesis
    - Pride-based: identity as "teacher" is motivating
    - Detects knowledge gaps through teaching struggles
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize Protégé Pipeline

        Args:
            storage_dir: Where to persist teaching sessions
        """
        self.storage_dir = storage_dir or Path("./data/protege")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self.active_sessions: Dict[str, TeachingSession] = {}  # user_id -> session
        self.session_history: Dict[str, TeachingSession] = {}  # session_id -> session

        # Student persona templates
        self.student_questions = {
            "clarification": [
                "I'm not quite following. Could you explain that part again?",
                "What do you mean by '{concept}'?",
                "Can you give me an example of that?",
            ],
            "deeper": [
                "That makes sense! But why does {concept} work that way?",
                "Interesting! How does this connect to {related_concept}?",
                "I get the basics, but what's really going on under the hood?",
            ],
            "application": [
                "Got it! So how would I use {concept} in a real situation?",
                "Can you show me a practical example?",
                "When would I choose {concept} over {alternative}?",
            ],
            "confirmation": [
                "Let me see if I understand: {summary}. Is that right?",
                "So basically, {concept} means {interpretation}?",
                "I think I get it! Can you confirm I'm understanding correctly?",
            ],
        }

        logger.info(f"Protégé Pipeline initialized with storage at {self.storage_dir}")

    async def start_teaching_mode(
        self,
        user_id: str,
        subject: str,
        from_learning_goal: bool = True
    ) -> TeachingSession:
        """
        Start learn-by-teaching session

        Reframes a learning goal as a teaching opportunity.

        Args:
            user_id: User who will be "teaching"
            subject: Subject to teach (e.g., "Python lists")
            from_learning_goal: Is this from a "Learn X" goal?

        Returns:
            New TeachingSession
        """
        logger.info(f"Starting teaching mode for user {user_id}: '{subject}'")

        # Create teaching session
        session = TeachingSession(
            session_id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            subject=subject,
            started_at=datetime.now(),
        )

        # Activate session
        self.active_sessions[user_id] = session
        self.session_history[session.session_id] = session

        logger.info(
            f"Teaching session {session.session_id} started: "
            f"User will teach '{subject}' to AI student"
        )

        return session

    async def request_explanation(
        self,
        user_id: str,
        concept: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ask user to teach a concept

        The AI "student" asks the user to explain something.

        Args:
            user_id: User being asked to explain
            concept: Concept to explain
            context: Optional context for the request

        Returns:
            Request data for UI to display
        """
        logger.info(f"Requesting explanation from user {user_id} for concept: '{concept}'")

        # Get active session
        session = self.active_sessions.get(user_id)
        if not session:
            logger.warning(f"No active teaching session for user {user_id}")
            # Create ad-hoc session
            session = await self.start_teaching_mode(user_id, concept, from_learning_goal=False)

        # Generate student question
        question = await self._generate_student_question(concept, context)

        request = {
            "session_id": session.session_id,
            "concept": concept,
            "student_question": question,
            "requested_at": datetime.now().isoformat(),
            "context": context,
        }

        logger.debug(f"Student question: '{question}'")

        return request

    async def receive_explanation(
        self,
        user_id: str,
        concept: str,
        explanation_text: str
    ) -> Explanation:
        """
        Receive and evaluate user's explanation

        Args:
            user_id: User who gave explanation
            concept: Concept being explained
            explanation_text: User's explanation

        Returns:
            Explanation with quality scores and feedback
        """
        logger.info(f"Receiving explanation from user {user_id} for: '{concept}'")

        # Get active session
        session = self.active_sessions.get(user_id)
        if not session:
            logger.warning(f"No active teaching session for user {user_id}")
            return None

        # Create explanation
        explanation = Explanation(
            explanation_id=f"exp_{datetime.now().timestamp()}",
            session_id=session.session_id,
            user_id=user_id,
            concept=concept,
            explanation_text=explanation_text,
        )

        # Evaluate explanation (simplified - would use LLM in full version)
        explanation = await self._evaluate_explanation(explanation)

        # Generate student feedback
        explanation.student_feedback = await self._generate_student_feedback(explanation)

        # Update session
        session.concepts_explained.append(concept)
        session.last_explanation_at = datetime.now()

        if explanation.student_understood:
            session.concepts_mastered += 1

        # Update understanding level (rolling average)
        total_score = explanation.clarity_score + explanation.completeness_score + explanation.depth_score
        avg_score = total_score / 3.0

        if session.understanding_level == 0.0:
            session.understanding_level = avg_score
        else:
            # Exponential moving average
            session.understanding_level = 0.7 * session.understanding_level + 0.3 * avg_score

        logger.info(
            f"Explanation evaluated: clarity={explanation.clarity_score:.2f}, "
            f"completeness={explanation.completeness_score:.2f}, "
            f"depth={explanation.depth_score:.2f}, "
            f"understood={explanation.student_understood}"
        )

        # Save
        await self._save_session(session)

        return explanation

    async def generate_follow_up_question(
        self,
        session_id: str,
        last_concept: str,
        understanding_level: float
    ) -> Optional[str]:
        """
        Generate follow-up question from AI "student"

        Based on understanding level, asks for:
        - Clarification (if confused)
        - Deeper explanation (if partially understood)
        - Application (if well understood)

        Args:
            session_id: Teaching session
            last_concept: Last concept explained
            understanding_level: How well student understood (0-1)

        Returns:
            Follow-up question or None if ready to move on
        """
        logger.debug(f"Generating follow-up for session {session_id}, understanding: {understanding_level:.2f}")

        if understanding_level < 0.5:
            # Confused - ask for clarification
            question_type = "clarification"
        elif understanding_level < 0.75:
            # Partially understood - ask deeper
            question_type = "deeper"
        elif understanding_level < 0.9:
            # Well understood - ask for application
            question_type = "application"
        else:
            # Fully understood - no follow-up needed
            return None

        # Select question template
        templates = self.student_questions.get(question_type, [])
        if not templates:
            return None

        # Simple selection (would be more sophisticated with LLM)
        template = templates[0]
        question = template.format(concept=last_concept, related_concept="related topics")

        return question

    async def complete_session(
        self,
        user_id: str,
        session_id: str
    ) -> TeachingSession:
        """
        Complete teaching session

        Args:
            user_id: User completing session
            session_id: Session to complete

        Returns:
            Completed session with final metrics
        """
        logger.info(f"Completing teaching session {session_id} for user {user_id}")

        session = self.session_history.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return None

        # Mark complete
        session.completed = True
        session.completed_at = datetime.now()

        # Calculate final teaching quality
        if session.concepts_mastered > 0:
            session.teaching_quality_score = session.understanding_level
        else:
            session.teaching_quality_score = 0.0

        # Remove from active
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]

        # Save
        await self._save_session(session)

        logger.info(
            f"Teaching session complete: {session.concepts_mastered} concepts mastered, "
            f"quality: {session.teaching_quality_score:.2f}"
        )

        return session

    # ===== HELPER METHODS =====

    async def _generate_student_question(
        self,
        concept: str,
        context: Optional[str] = None
    ) -> str:
        """Generate student question asking for explanation"""
        # Simple template-based (would use LLM in full version)
        questions = [
            f"I want to learn about {concept}. Can you teach me?",
            f"What is {concept}? I'm really curious!",
            f"I've heard about {concept} but don't understand it. Can you explain?",
        ]
        return questions[0]

    async def _evaluate_explanation(self, explanation: Explanation) -> Explanation:
        """Evaluate quality of explanation (simplified version)"""
        # In full version, would use LLM to evaluate
        # For now, simple heuristics

        text_length = len(explanation.explanation_text)

        # Clarity: based on length and structure
        if text_length > 100:
            explanation.clarity_score = 0.8
        elif text_length > 50:
            explanation.clarity_score = 0.6
        else:
            explanation.clarity_score = 0.4

        # Completeness: based on length
        if text_length > 200:
            explanation.completeness_score = 0.9
        elif text_length > 100:
            explanation.completeness_score = 0.7
        else:
            explanation.completeness_score = 0.5

        # Depth: based on keywords (simplified)
        depth_keywords = ["because", "therefore", "for example", "specifically", "in other words"]
        depth_count = sum(1 for kw in depth_keywords if kw in explanation.explanation_text.lower())
        explanation.depth_score = min(1.0, depth_count * 0.2 + 0.3)

        # Student understood if scores are high
        avg_score = (explanation.clarity_score + explanation.completeness_score + explanation.depth_score) / 3.0
        explanation.student_understood = avg_score > 0.6

        return explanation

    async def _generate_student_feedback(self, explanation: Explanation) -> str:
        """Generate feedback from AI student"""
        if explanation.student_understood:
            feedback = [
                f"Ah, I get it now! Thanks for explaining {explanation.concept} so clearly!",
                f"That makes sense! Your explanation really helped me understand {explanation.concept}.",
                f"Great explanation! I feel like I really understand {explanation.concept} now.",
            ]
        else:
            feedback = [
                f"I'm still a bit confused about {explanation.concept}. Could you explain it differently?",
                f"Hmm, I think I need a bit more detail to really understand {explanation.concept}.",
                f"I'm getting closer, but I'm not quite there yet with {explanation.concept}.",
            ]

        return feedback[0]

    async def _save_session(self, session: TeachingSession) -> None:
        """Persist teaching session"""
        try:
            file_path = self.storage_dir / f"{session.session_id}.json"

            data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "subject": session.subject,
                "concepts_explained": session.concepts_explained,
                "concepts_mastered": session.concepts_mastered,
                "understanding_level": session.understanding_level,
                "teaching_quality_score": session.teaching_quality_score,
                "started_at": session.started_at.isoformat(),
                "last_explanation_at": session.last_explanation_at.isoformat() if session.last_explanation_at else None,
                "completed": session.completed,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Teaching session saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save teaching session: {e}")
