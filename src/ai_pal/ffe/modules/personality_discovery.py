"""
Advanced Personality Discovery Module

Interactive discovery of:
- Signature strengths (with confidence scoring)
- Core values
- Learning preferences (VARK style)
- Work patterns
- Growth areas

Continuously refined based on actual usage patterns.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from datetime import datetime
from enum import Enum
import uuid

from ..models import SignatureStrength, StrengthType


class AssessmentStage(str, Enum):
    """Stages of personality discovery"""
    INITIAL = "initial"                    # First-time setup
    REFINING = "refining"                  # Clarifying discovered strengths
    VALIDATING = "validating"              # Confirming through usage
    DISCOVERING_NEW = "discovering_new"    # Finding new strengths


class QuestionType(str, Enum):
    """Types of discovery questions"""
    MULTIPLE_CHOICE = "multiple_choice"
    RANKING = "ranking"
    OPEN_ENDED = "open_ended"
    SCENARIO = "scenario"


@dataclass
class DiscoveryQuestion:
    """A question for personality discovery"""
    question_id: str
    question_text: str
    question_type: QuestionType

    # For assessment
    assesses: str                           # What this question reveals
    strength_indicators: Dict[StrengthType, float] = field(default_factory=dict)

    # Options (for multiple choice/ranking)
    options: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    stage: AssessmentStage = AssessmentStage.INITIAL
    asked_count: int = 0


@dataclass
class DiscoverySession:
    """A personality discovery session"""
    session_id: str
    user_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Progress
    stage: AssessmentStage = AssessmentStage.INITIAL
    questions_asked: List[str] = field(default_factory=list)
    answers: Dict[str, Any] = field(default_factory=dict)

    # Discovered insights
    discovered_strengths: List[SignatureStrength] = field(default_factory=list)
    discovered_values: List[str] = field(default_factory=list)
    learning_style: Optional[str] = None

    # Confidence
    discovery_confidence: float = 0.0       # How confident we are in discoveries


@dataclass
class UsagePattern:
    """Pattern observed from actual usage"""
    pattern_id: str
    user_id: str
    observed_at: datetime

    # What was observed
    pattern_type: str                       # task_preference, strength_use, etc.
    pattern_description: str

    # Evidence
    evidence_count: int = 1
    examples: List[str] = field(default_factory=list)

    # Implications
    suggests_strength: Optional[StrengthType] = None
    confidence_delta: float = 0.0           # How much to adjust strength confidence


class PersonalityDiscoveryModule:
    """
    Advanced Personality Discovery Module

    Interactive assessment and continuous refinement of:
    - Signature strengths
    - Core values
    - Learning preferences
    - Work patterns

    Discovery methods:
    1. Interactive assessment (user answers questions)
    2. Usage pattern analysis (observe actual behavior)
    3. Win analysis (what led to successes?)
    4. Struggle analysis (what challenges reveal)
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize Personality Discovery Module

        Args:
            storage_dir: Where to persist discovery data
        """
        self.storage_dir = storage_dir or "./data/personality"

        # In-memory storage
        self._sessions: Dict[str, DiscoverySession] = {}
        self._user_patterns: Dict[str, List[UsagePattern]] = {}

        # Question bank
        self._question_bank = self._initialize_question_bank()

    def _initialize_question_bank(self) -> List[DiscoveryQuestion]:
        """Initialize the discovery question bank"""
        questions = []

        # Analytical strength questions
        questions.append(DiscoveryQuestion(
            question_id="analytical_1",
            question_text="When solving a problem, I prefer to:",
            question_type=QuestionType.MULTIPLE_CHOICE,
            assesses="analytical_thinking",
            strength_indicators={
                StrengthType.ANALYTICAL: 0.8,
                StrengthType.CREATIVE: 0.2
            },
            options=[
                {"id": "a", "text": "Break it down into logical steps", "strength": StrengthType.ANALYTICAL, "weight": 0.9},
                {"id": "b", "text": "Brainstorm multiple creative approaches", "strength": StrengthType.CREATIVE, "weight": 0.9},
                {"id": "c", "text": "Ask others for their perspectives", "strength": StrengthType.SOCIAL, "weight": 0.8},
                {"id": "d", "text": "Trust my intuition and experience", "strength": StrengthType.PRACTICAL, "weight": 0.7}
            ]
        ))

        # Creative strength questions
        questions.append(DiscoveryQuestion(
            question_id="creative_1",
            question_text="I feel most energized when:",
            question_type=QuestionType.MULTIPLE_CHOICE,
            assesses="creative_energy",
            strength_indicators={
                StrengthType.CREATIVE: 0.9,
                StrengthType.ANALYTICAL: 0.1
            },
            options=[
                {"id": "a", "text": "Designing something new from scratch", "strength": StrengthType.CREATIVE, "weight": 1.0},
                {"id": "b", "text": "Optimizing an existing system", "strength": StrengthType.ANALYTICAL, "weight": 0.8},
                {"id": "c", "text": "Building connections between people", "strength": StrengthType.SOCIAL, "weight": 0.9},
                {"id": "d", "text": "Getting things done efficiently", "strength": StrengthType.PRACTICAL, "weight": 0.7}
            ]
        ))

        # Social strength questions
        questions.append(DiscoveryQuestion(
            question_id="social_1",
            question_text="In group projects, I naturally:",
            question_type=QuestionType.MULTIPLE_CHOICE,
            assesses="social_interaction",
            strength_indicators={
                StrengthType.SOCIAL: 0.9
            },
            options=[
                {"id": "a", "text": "Facilitate discussions and coordinate", "strength": StrengthType.SOCIAL, "weight": 1.0},
                {"id": "b", "text": "Analyze the problem and propose solutions", "strength": StrengthType.ANALYTICAL, "weight": 0.8},
                {"id": "c", "text": "Generate innovative ideas", "strength": StrengthType.CREATIVE, "weight": 0.8},
                {"id": "d", "text": "Execute tasks and deliver results", "strength": StrengthType.PRACTICAL, "weight": 0.9}
            ]
        ))

        # Practical strength questions
        questions.append(DiscoveryQuestion(
            question_id="practical_1",
            question_text="When learning something new, I prefer to:",
            question_type=QuestionType.MULTIPLE_CHOICE,
            assesses="learning_approach",
            strength_indicators={
                StrengthType.PRACTICAL: 0.8
            },
            options=[
                {"id": "a", "text": "Jump in and learn by doing", "strength": StrengthType.PRACTICAL, "weight": 1.0},
                {"id": "b", "text": "Study the theory first", "strength": StrengthType.ANALYTICAL, "weight": 0.9},
                {"id": "c", "text": "Experiment and explore creatively", "strength": StrengthType.CREATIVE, "weight": 0.8},
                {"id": "d", "text": "Learn from others' experiences", "strength": StrengthType.SOCIAL, "weight": 0.7}
            ]
        ))

        # Values questions
        questions.append(DiscoveryQuestion(
            question_id="values_1",
            question_text="What matters most to you in your work/goals?",
            question_type=QuestionType.RANKING,
            assesses="core_values",
            options=[
                {"id": "a", "text": "Making a meaningful impact"},
                {"id": "b", "text": "Continuous learning and growth"},
                {"id": "c", "text": "Building strong relationships"},
                {"id": "d", "text": "Achieving mastery and excellence"},
                {"id": "e", "text": "Creating something original"}
            ]
        ))

        return questions

    # ===== INTERACTIVE ASSESSMENT =====

    async def start_discovery_session(
        self,
        user_id: str,
        stage: AssessmentStage = AssessmentStage.INITIAL
    ) -> DiscoverySession:
        """
        Start a personality discovery session

        Args:
            user_id: User to assess
            stage: Which stage of discovery

        Returns:
            New DiscoverySession
        """
        session_id = str(uuid.uuid4())

        session = DiscoverySession(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.utcnow(),
            stage=stage
        )

        self._sessions[session_id] = session

        return session

    async def get_next_question(
        self,
        session_id: str
    ) -> Optional[DiscoveryQuestion]:
        """
        Get next discovery question for session

        Args:
            session_id: Current session

        Returns:
            Next question or None if complete
        """
        if session_id not in self._sessions:
            return None

        session = self._sessions[session_id]

        # Find questions not yet asked
        available_questions = [
            q for q in self._question_bank
            if q.question_id not in session.questions_asked
            and q.stage == session.stage
        ]

        if not available_questions:
            return None

        # Return first available question
        # (Would be smarter in production - adaptive questioning)
        return available_questions[0]

    async def record_answer(
        self,
        session_id: str,
        question_id: str,
        answer: Any
    ) -> Dict[str, Any]:
        """
        Record answer to discovery question

        Args:
            session_id: Current session
            question_id: Question being answered
            answer: User's answer

        Returns:
            Analysis of answer
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self._sessions[session_id]

        # Find question
        question = next(
            (q for q in self._question_bank if q.question_id == question_id),
            None
        )
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Record answer
        session.questions_asked.append(question_id)
        session.answers[question_id] = answer
        question.asked_count += 1

        # Analyze answer
        analysis = await self._analyze_answer(session, question, answer)

        return analysis

    async def _analyze_answer(
        self,
        session: DiscoverySession,
        question: DiscoveryQuestion,
        answer: Any
    ) -> Dict[str, Any]:
        """Analyze a discovery answer"""
        analysis = {
            "question_id": question.question_id,
            "answer": answer,
            "insights": []
        }

        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Find selected option
            selected_option = next(
                (opt for opt in question.options if opt["id"] == answer),
                None
            )

            if selected_option and "strength" in selected_option:
                strength_type = selected_option["strength"]
                weight = selected_option.get("weight", 0.5)

                analysis["insights"].append({
                    "type": "strength_indicator",
                    "strength": strength_type.value,
                    "confidence": weight,
                    "reason": f"Selected: {selected_option['text']}"
                })

        return analysis

    async def complete_session(
        self,
        session_id: str
    ) -> DiscoverySession:
        """
        Complete discovery session and generate insights

        Args:
            session_id: Session to complete

        Returns:
            Completed session with discovered insights
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self._sessions[session_id]

        # Analyze all answers to discover strengths
        strength_scores: Dict[StrengthType, float] = {}

        for question_id, answer in session.answers.items():
            question = next(
                (q for q in self._question_bank if q.question_id == question_id),
                None
            )
            if not question:
                continue

            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                selected_option = next(
                    (opt for opt in question.options if opt["id"] == answer),
                    None
                )

                if selected_option and "strength" in selected_option:
                    strength_type = selected_option["strength"]
                    weight = selected_option.get("weight", 0.5)

                    if strength_type not in strength_scores:
                        strength_scores[strength_type] = 0.0
                    strength_scores[strength_type] += weight

        # Normalize scores
        if strength_scores:
            max_score = max(strength_scores.values())
            for strength_type in strength_scores:
                strength_scores[strength_type] /= max_score

        # Create SignatureStrength objects for top strengths
        top_strengths = sorted(
            strength_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]  # Top 3 strengths

        for strength_type, score in top_strengths:
            strength = SignatureStrength(
                strength_type=strength_type,
                identity_label=self._get_identity_label(strength_type),
                strength_description=self._get_strength_description(strength_type),
                confidence_score=score
            )
            session.discovered_strengths.append(strength)

        # Calculate overall discovery confidence
        if session.discovered_strengths:
            session.discovery_confidence = sum(
                s.confidence_score for s in session.discovered_strengths
            ) / len(session.discovered_strengths)

        # Mark complete
        session.completed_at = datetime.utcnow()

        return session

    # ===== USAGE PATTERN ANALYSIS =====

    async def record_usage_pattern(
        self,
        user_id: str,
        pattern_type: str,
        pattern_description: str,
        suggests_strength: Optional[StrengthType] = None,
        example: Optional[str] = None
    ) -> UsagePattern:
        """
        Record an observed usage pattern

        Args:
            user_id: User exhibiting pattern
            pattern_type: Type of pattern
            pattern_description: Description
            suggests_strength: Strength this suggests
            example: Example of the pattern

        Returns:
            UsagePattern object
        """
        pattern_id = str(uuid.uuid4())

        pattern = UsagePattern(
            pattern_id=pattern_id,
            user_id=user_id,
            observed_at=datetime.utcnow(),
            pattern_type=pattern_type,
            pattern_description=pattern_description,
            suggests_strength=suggests_strength
        )

        if example:
            pattern.examples.append(example)

        # Store
        if user_id not in self._user_patterns:
            self._user_patterns[user_id] = []
        self._user_patterns[user_id].append(pattern)

        return pattern

    async def update_strength_confidence(
        self,
        user_id: str,
        strength: SignatureStrength,
        confidence_delta: float,
        reason: str
    ) -> SignatureStrength:
        """
        Update strength confidence based on usage

        Args:
            user_id: User whose strength to update
            strength: Strength to update
            confidence_delta: Amount to adjust (+/-)
            reason: Why the adjustment

        Returns:
            Updated SignatureStrength
        """
        # Adjust confidence
        new_confidence = strength.confidence_score + confidence_delta
        new_confidence = max(0.0, min(1.0, new_confidence))  # Clamp to [0, 1]

        strength.confidence_score = new_confidence

        # Record reason as example if positive
        if confidence_delta > 0:
            strength.demonstrated_examples.append(reason)

        return strength

    # ===== HELPER METHODS =====

    def _get_identity_label(self, strength_type: StrengthType) -> str:
        """Get identity label for strength type"""
        labels = {
            StrengthType.ANALYTICAL: "Analytical Thinker",
            StrengthType.CREATIVE: "Creative Innovator",
            StrengthType.SOCIAL: "Connector & Collaborator",
            StrengthType.PRACTICAL: "Hands-On Implementer",
            StrengthType.STRATEGIC: "Strategic Planner",
            StrengthType.EMPATHETIC: "Empathetic Supporter",
            StrengthType.RESILIENT: "Resilient Achiever",
            StrengthType.CURIOUS: "Curious Explorer"
        }
        return labels.get(strength_type, "Unique Strength")

    def _get_strength_description(self, strength_type: StrengthType) -> str:
        """Get description for strength type"""
        descriptions = {
            StrengthType.ANALYTICAL: "You excel at breaking down complex problems into logical components and finding systematic solutions.",
            StrengthType.CREATIVE: "You thrive on generating novel ideas and finding innovative approaches to challenges.",
            StrengthType.SOCIAL: "You naturally build connections, facilitate collaboration, and bring people together.",
            StrengthType.PRACTICAL: "You prefer hands-on approaches and learn best by doing and experimenting.",
            StrengthType.STRATEGIC: "You see the big picture and excel at long-term planning and positioning.",
            StrengthType.EMPATHETIC: "You understand others deeply and create supportive, inclusive environments.",
            StrengthType.RESILIENT: "You bounce back from setbacks and persist through challenges.",
            StrengthType.CURIOUS: "You're driven by a desire to learn, explore, and understand how things work."
        }
        return descriptions.get(strength_type, "A unique way of approaching the world.")
