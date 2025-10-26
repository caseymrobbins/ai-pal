"""
Learn About Me Mode: Socratic Deep Dive for User Profiling.

"Your Cognitive Release Valve" - An opt-in space for users to be challenged,
understood, and explore complex ideas with a true cognitive partner.

Builds deep, accurate profiles of user knowledge and synthesis skills through
adaptive Socratic questioning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from loguru import logger

from ai_pal.ari.measurement import (
    ARIMeasurementSystem,
    ARIDimension,
    ARILevel,
    ARIScore
)


class DifficultyLevel(Enum):
    """Difficulty levels for Socratic questions."""
    FOUNDATIONAL = "foundational"      # Basic concepts
    INTERMEDIATE = "intermediate"      # Connecting ideas
    ADVANCED = "advanced"              # Complex synthesis
    EXPERT = "expert"                  # Novel insights


class SessionStatus(Enum):
    """Status of a Learn About Me session."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class SocraticQuestion:
    """A Socratic question in the progression."""
    question_id: str
    domain: str
    difficulty: DifficultyLevel
    question_text: str

    # Expected response criteria
    expected_criteria: Dict[str, Any] = field(default_factory=dict)

    # User response
    user_response: Optional[str] = None
    responded_at: Optional[datetime] = None

    # Assessment
    ari_score: Optional[ARIScore] = None
    scaffold_offered: bool = False
    scaffold_text: Optional[str] = None


@dataclass
class LearnAboutMeSession:
    """A single Learn About Me session."""
    session_id: str
    user_id: str
    domain: str                        # Domain being explored

    # Progression
    current_difficulty: DifficultyLevel
    questions: List[SocraticQuestion] = field(default_factory=list)
    current_question_index: int = 0

    # Status
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # User's skill ceiling in this session
    demonstrated_ceiling: Optional[DifficultyLevel] = None

    # Engagement tracking
    scaffolds_used: int = 0
    total_questions_answered: int = 0
    opt_outs: int = 0                  # Times user requested "regular chat"


class LearnAboutMeMode:
    """
    Socratic Deep Dive mode for building user capability profiles.

    Key Features:
    - Adaptive scaffolding (start basic, move up)
    - ARI-Synthesis grading
    - Rewarding engagement
    - Full user control (opt-in/opt-out)
    """

    def __init__(
        self,
        ari_system: ARIMeasurementSystem,
        orchestrator: Optional[Any] = None,
        storage_dir: Optional[Path] = None
    ):
        """Initialize Learn About Me mode."""
        self.ari_system = ari_system
        self.orchestrator = orchestrator
        self.storage_dir = storage_dir or Path("./data/learn_about_me")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Active sessions
        self.active_sessions: Dict[str, LearnAboutMeSession] = {}

        # Question templates by domain and difficulty
        self.question_templates = self._load_question_templates()

        logger.info("Learn About Me mode initialized")

    def _load_question_templates(self) -> Dict[str, Dict[DifficultyLevel, List[Dict]]]:
        """Load question templates for different domains and difficulties."""
        # In production, this would load from a rich question bank
        # For now, hardcoded templates

        templates = {
            "python_programming": {
                DifficultyLevel.FOUNDATIONAL: [
                    {
                        "text": "What is a variable in Python, and how would you explain it to someone new to programming?",
                        "criteria": {
                            "keywords": ["store", "value", "name", "data"],
                            "required_components": ["definition", "purpose"]
                        }
                    },
                    {
                        "text": "What's the difference between a list and a tuple in Python?",
                        "criteria": {
                            "keywords": ["mutable", "immutable", "list", "tuple"],
                            "required_components": ["mutability", "use_case"]
                        }
                    }
                ],
                DifficultyLevel.INTERMEDIATE: [
                    {
                        "text": "Explain how decorators work in Python and when you would use them.",
                        "criteria": {
                            "keywords": ["function", "wrapper", "modify", "behavior"],
                            "required_components": ["mechanism", "use_case", "example"]
                        }
                    },
                    {
                        "text": "How do you handle exceptions in Python, and why is it important?",
                        "criteria": {
                            "keywords": ["try", "except", "finally", "error"],
                            "required_components": ["syntax", "purpose", "best_practice"]
                        }
                    }
                ],
                DifficultyLevel.ADVANCED: [
                    {
                        "text": "Design a metaclass for automatic property validation. Explain your design choices.",
                        "criteria": {
                            "keywords": ["metaclass", "validation", "property", "class"],
                            "required_components": ["design", "rationale", "implementation"]
                        }
                    },
                    {
                        "text": "Explain the GIL (Global Interpreter Lock) and its implications for concurrent programming.",
                        "criteria": {
                            "keywords": ["GIL", "thread", "concurrency", "performance"],
                            "required_components": ["mechanism", "impact", "workarounds"]
                        }
                    }
                ],
                DifficultyLevel.EXPERT: [
                    {
                        "text": "Compare asyncio's event loop to Go's goroutines. When would you choose one over the other?",
                        "criteria": {
                            "keywords": ["asyncio", "goroutines", "concurrency", "performance"],
                            "required_components": ["comparison", "tradeoffs", "use_cases"]
                        }
                    }
                ]
            },
            "machine_learning": {
                DifficultyLevel.FOUNDATIONAL: [
                    {
                        "text": "What is the difference between supervised and unsupervised learning?",
                        "criteria": {
                            "keywords": ["labeled", "unlabeled", "supervised", "unsupervised"],
                            "required_components": ["definition", "examples"]
                        }
                    }
                ],
                DifficultyLevel.INTERMEDIATE: [
                    {
                        "text": "Explain overfitting and how you would prevent it in a neural network.",
                        "criteria": {
                            "keywords": ["overfitting", "generalization", "regularization"],
                            "required_components": ["problem", "detection", "solutions"]
                        }
                    }
                ],
                DifficultyLevel.ADVANCED: [
                    {
                        "text": "Design a training strategy for a transformer model on a limited dataset.",
                        "criteria": {
                            "keywords": ["transformer", "data", "training", "strategy"],
                            "required_components": ["challenges", "techniques", "rationale"]
                        }
                    }
                ]
            }
        }

        return templates

    # ========================================================================
    # Session Management
    # ========================================================================

    async def start_session(
        self,
        user_id: str,
        domain: str,
        initial_difficulty: Optional[DifficultyLevel] = None
    ) -> LearnAboutMeSession:
        """
        Start a new Learn About Me session.

        Args:
            user_id: User identifier
            domain: Domain to explore (e.g., "python_programming")
            initial_difficulty: Starting difficulty (default: FOUNDATIONAL)

        Returns:
            New session
        """
        import uuid

        session_id = f"lam_{uuid.uuid4().hex[:12]}"

        # Check user's existing ARI level for this domain
        existing_level = self.ari_system.get_user_ari_level(
            user_id=user_id,
            dimension=ARIDimension.SYNTHESIS,
            domain=domain
        )

        # Adjust starting difficulty based on existing knowledge
        if initial_difficulty is None:
            if existing_level == ARILevel.HIGH:
                initial_difficulty = DifficultyLevel.ADVANCED
            elif existing_level == ARILevel.MEDIUM:
                initial_difficulty = DifficultyLevel.INTERMEDIATE
            else:
                initial_difficulty = DifficultyLevel.FOUNDATIONAL

        session = LearnAboutMeSession(
            session_id=session_id,
            user_id=user_id,
            domain=domain,
            current_difficulty=initial_difficulty
        )

        # Generate first question
        first_question = self._generate_question(domain, initial_difficulty)
        session.questions.append(first_question)

        self.active_sessions[session_id] = session

        logger.info(f"Started Learn About Me session: {session_id} (domain={domain}, difficulty={initial_difficulty.value})")
        return session

    def _generate_question(
        self,
        domain: str,
        difficulty: DifficultyLevel
    ) -> SocraticQuestion:
        """Generate a Socratic question for the given domain and difficulty."""
        import uuid
        import random

        # Get templates for this domain/difficulty
        domain_templates = self.question_templates.get(domain, {})
        difficulty_templates = domain_templates.get(difficulty, [])

        if not difficulty_templates:
            # Fallback: generic question
            question_text = f"Tell me about an interesting aspect of {domain} at the {difficulty.value} level."
            criteria = {"keywords": [domain], "required_components": ["concept", "explanation"]}
        else:
            # Select random template
            template = random.choice(difficulty_templates)
            question_text = template["text"]
            criteria = template["criteria"]

        return SocraticQuestion(
            question_id=f"sq_{uuid.uuid4().hex[:8]}",
            domain=domain,
            difficulty=difficulty,
            question_text=question_text,
            expected_criteria=criteria
        )

    # ========================================================================
    # Question Flow
    # ========================================================================

    async def get_current_question(self, session_id: str) -> SocraticQuestion:
        """Get the current question for a session."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Unknown session: {session_id}")

        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session {session_id} is not active")

        return session.questions[session.current_question_index]

    async def submit_response(
        self,
        session_id: str,
        response: str
    ) -> Dict[str, Any]:
        """
        Submit user's response to current question.

        Returns:
            Feedback dict with:
            - ari_score: ARIScore for the response
            - feedback: Text feedback to user
            - next_action: "advance", "scaffold", or "complete"
            - next_question: Optional next question
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Unknown session: {session_id}")

        current_question = session.questions[session.current_question_index]

        # Record response
        current_question.user_response = response
        current_question.responded_at = datetime.now()
        session.total_questions_answered += 1

        # Score the response
        ari_score = self.ari_system.score_synthesis_response(
            user_response=response,
            expected_criteria=current_question.expected_criteria,
            domain=session.domain,
            user_id=session.user_id
        )
        current_question.ari_score = ari_score

        # Determine next action based on score
        if ari_score.level == ARILevel.HIGH:
            # Success! Move to next difficulty
            return await self._handle_success(session, current_question)

        elif ari_score.level == ARILevel.MEDIUM:
            # Partial success - offer scaffold or advance
            return await self._handle_partial_success(session, current_question)

        else:  # LOW
            # Struggle - offer scaffold
            return await self._handle_struggle(session, current_question)

    async def _handle_success(
        self,
        session: LearnAboutMeSession,
        question: SocraticQuestion
    ) -> Dict[str, Any]:
        """Handle successful response - advance to harder question."""
        # Update demonstrated ceiling
        session.demonstrated_ceiling = question.difficulty

        # Generate affirming feedback
        feedback = self._generate_affirming_feedback(question)

        # Check if we can advance difficulty
        next_difficulty = self._get_next_difficulty(question.difficulty)

        if next_difficulty:
            # Generate next question at higher difficulty
            next_question = self._generate_question(session.domain, next_difficulty)
            session.questions.append(next_question)
            session.current_question_index += 1
            session.current_difficulty = next_difficulty

            return {
                "ari_score": question.ari_score,
                "feedback": feedback,
                "next_action": "advance",
                "next_question": next_question,
                "difficulty_increased": True
            }
        else:
            # Reached expert level!
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.now()

            return {
                "ari_score": question.ari_score,
                "feedback": feedback + "\n\nCongratulations! You've demonstrated expert-level understanding.",
                "next_action": "complete",
                "next_question": None,
                "session_complete": True
            }

    async def _handle_partial_success(
        self,
        session: LearnAboutMeSession,
        question: SocraticQuestion
    ) -> Dict[str, Any]:
        """Handle partial success - advance with encouragement."""
        feedback = "Good thinking! You've got some key concepts. Let me build on that..."

        # Stay at same difficulty but new question
        next_question = self._generate_question(session.domain, question.difficulty)
        session.questions.append(next_question)
        session.current_question_index += 1

        return {
            "ari_score": question.ari_score,
            "feedback": feedback,
            "next_action": "advance",
            "next_question": next_question,
            "difficulty_increased": False
        }

    async def _handle_struggle(
        self,
        session: LearnAboutMeSession,
        question: SocraticQuestion
    ) -> Dict[str, Any]:
        """Handle struggle - offer scaffold."""
        if not question.scaffold_offered:
            # First time struggling - offer scaffold
            scaffold = self._generate_scaffold(question)
            question.scaffold_offered = True
            question.scaffold_text = scaffold
            session.scaffolds_used += 1

            return {
                "ari_score": question.ari_score,
                "feedback": "Let me help you think through this...",
                "next_action": "scaffold",
                "scaffold": scaffold,
                "next_question": None
            }
        else:
            # Already scaffolded - provide answer and move to easier question
            feedback = "No worries! Let me explain..."
            explanation = self._generate_explanation(question)

            # Drop difficulty
            easier_difficulty = self._get_easier_difficulty(question.difficulty)
            next_question = self._generate_question(session.domain, easier_difficulty)
            session.questions.append(next_question)
            session.current_question_index += 1
            session.current_difficulty = easier_difficulty

            return {
                "ari_score": question.ari_score,
                "feedback": feedback,
                "explanation": explanation,
                "next_action": "advance",
                "next_question": next_question,
                "difficulty_decreased": True
            }

    def _generate_affirming_feedback(self, question: SocraticQuestion) -> str:
        """Generate identity-affirming feedback for correct answer."""
        import random

        templates = [
            "Excellent! That shows strong {domain} thinking.",
            "Great insight! You clearly understand {domain} deeply.",
            "Precisely! Your {domain} knowledge is impressive.",
            "Well done! That's exactly the kind of {domain} reasoning we want."
        ]

        template = random.choice(templates)
        return template.format(domain=question.domain.replace("_", " "))

    def _generate_scaffold(self, question: SocraticQuestion) -> str:
        """Generate a scaffold (hint) for a question."""
        # In production, would use LLM to generate contextual scaffold
        # For now, use question criteria to generate hint

        criteria = question.expected_criteria
        keywords = criteria.get("keywords", [])
        components = criteria.get("required_components", [])

        if keywords:
            return f"Think about these concepts: {', '.join(keywords[:2])}. How do they relate?"
        elif components:
            return f"Try breaking this down into: {', '.join(components[:2])}."
        else:
            return "Let's think about this step by step. What's the fundamental concept here?"

    def _generate_explanation(self, question: SocraticQuestion) -> str:
        """Generate explanation for a question."""
        # In production, would use LLM to generate full explanation
        return f"Here's the key: {question.question_text} involves understanding {', '.join(question.expected_criteria.get('keywords', ['the core concepts']))}."

    def _get_next_difficulty(self, current: DifficultyLevel) -> Optional[DifficultyLevel]:
        """Get next higher difficulty level."""
        progression = [
            DifficultyLevel.FOUNDATIONAL,
            DifficultyLevel.INTERMEDIATE,
            DifficultyLevel.ADVANCED,
            DifficultyLevel.EXPERT
        ]

        try:
            current_index = progression.index(current)
            if current_index < len(progression) - 1:
                return progression[current_index + 1]
        except ValueError:
            pass

        return None

    def _get_easier_difficulty(self, current: DifficultyLevel) -> DifficultyLevel:
        """Get next lower difficulty level."""
        progression = [
            DifficultyLevel.FOUNDATIONAL,
            DifficultyLevel.INTERMEDIATE,
            DifficultyLevel.ADVANCED,
            DifficultyLevel.EXPERT
        ]

        try:
            current_index = progression.index(current)
            if current_index > 0:
                return progression[current_index - 1]
        except ValueError:
            pass

        return DifficultyLevel.FOUNDATIONAL

    # ========================================================================
    # User Control
    # ========================================================================

    async def request_regular_chat(self, session_id: str) -> str:
        """
        User requests to exit deep dive and return to regular chat.

        This is the "off-ramp" - user can disengage at any time.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Unknown session: {session_id}")

        session.status = SessionStatus.PAUSED
        session.opt_outs += 1

        logger.info(f"User opted out of session {session_id} (opt-outs={session.opt_outs})")

        return "No problem! Switching back to regular chat mode. You can resume the Deep Dive anytime by saying 'continue learning'."

    async def request_just_answer(self, session_id: str) -> str:
        """
        User requests direct answer instead of Socratic exploration.

        This is the "humanity override" - respects user's right to convenience.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Unknown session: {session_id}")

        current_question = session.questions[session.current_question_index]

        # Provide direct answer
        explanation = self._generate_explanation(current_question)

        # Record this as opt-out but don't penalize
        session.opt_outs += 1

        return f"Understood! Here's the answer: {explanation}\n\nWould you like to continue exploring, or switch to regular chat?"

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session progress."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Unknown session: {session_id}")

        return {
            "session_id": session_id,
            "domain": session.domain,
            "questions_answered": session.total_questions_answered,
            "current_difficulty": session.current_difficulty.value,
            "demonstrated_ceiling": session.demonstrated_ceiling.value if session.demonstrated_ceiling else None,
            "scaffolds_used": session.scaffolds_used,
            "opt_outs": session.opt_outs,
            "status": session.status.value,
            "duration_minutes": (datetime.now() - session.started_at).total_seconds() / 60
        }

    # ========================================================================
    # Persistence
    # ========================================================================

    async def persist_sessions(self) -> None:
        """Persist active sessions to disk."""
        sessions_file = self.storage_dir / "sessions.json"

        sessions_data = {}
        for session_id, session in self.active_sessions.items():
            sessions_data[session_id] = {
                "user_id": session.user_id,
                "domain": session.domain,
                "current_difficulty": session.current_difficulty.value,
                "current_question_index": session.current_question_index,
                "status": session.status.value,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "demonstrated_ceiling": session.demonstrated_ceiling.value if session.demonstrated_ceiling else None,
                "scaffolds_used": session.scaffolds_used,
                "total_questions_answered": session.total_questions_answered,
                "opt_outs": session.opt_outs
            }

        with open(sessions_file, 'w') as f:
            json.dump(sessions_data, f, indent=2)

        logger.info(f"Persisted {len(sessions_data)} sessions")
