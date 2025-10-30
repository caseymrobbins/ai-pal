"""
Learn About Me (Deep Dive Mode) - Socratic Chat Interface

User-facing "cognitive release valve" for users who want to be challenged, understood,
and explore complex ideas with a true cognitive partner.

Core Function:
- Build deep, accurate profile of user's knowledge domains, synthesis skills, logical style
- Provide "gold standard" measurement for ARI-Synthesis and ARI-Knowledge
- Adaptive Socratic scaffolding from basics to advanced concepts
- Rewarding progression with user agency controls

Powered by:
- ARIMonitor (for tracking synthesis and knowledge metrics)
- EnhancedContextManager (for storing knowledge profiles)
- MultiModelOrchestrator (for generating Socratic questions and grading)
"""

import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger

from ...monitoring.ari_monitor import ARIMonitor, AgencySnapshot
from ...context.enhanced_context import (
    EnhancedContextManager,
    MemoryType,
    MemoryPriority,
)
from ...orchestration.multi_model import MultiModelOrchestrator, TaskComplexity


class DifficultyLevel(Enum):
    """Difficulty levels for Socratic questioning"""
    BASIC = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    MASTERY = 5


class ResponseQuality(Enum):
    """Quality assessment of user responses"""
    EXCELLENT = "excellent"       # Exceeds expectations, deep insight
    PROFICIENT = "proficient"     # Meets expectations, solid understanding
    DEVELOPING = "developing"     # Partial understanding, needs scaffolding
    STRUGGLING = "struggling"     # Significant gaps, needs simpler question
    INSUFFICIENT = "insufficient" # Unable to engage, offer escape


@dataclass
class SynthesisRubric:
    """
    Rubric for grading synthesis quality (per your ARI-Synthesis spec)

    Three components:
    - Accuracy: Logical correctness
    - Logic: Sound reasoning chain
    - Completeness: Addresses all key aspects
    """
    accuracy_score: float  # 0-1: Is the reasoning logically sound?
    logic_score: float     # 0-1: Does the chain of reasoning hold up?
    completeness_score: float  # 0-1: Did they address all key aspects?

    @property
    def overall_score(self) -> float:
        """Weighted average of the three components"""
        return (
            0.35 * self.accuracy_score +
            0.35 * self.logic_score +
            0.30 * self.completeness_score
        )

    @property
    def quality(self) -> ResponseQuality:
        """Map overall score to quality level"""
        if self.overall_score >= 0.85:
            return ResponseQuality.EXCELLENT
        elif self.overall_score >= 0.70:
            return ResponseQuality.PROFICIENT
        elif self.overall_score >= 0.50:
            return ResponseQuality.DEVELOPING
        elif self.overall_score >= 0.30:
            return ResponseQuality.STRUGGLING
        else:
            return ResponseQuality.INSUFFICIENT


@dataclass
class SocraticQuestion:
    """
    A single Socratic question in the dialogue

    Progressively increases difficulty as user demonstrates mastery.
    """
    question_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    domain: str = ""  # e.g., "machine learning", "philosophy"
    difficulty: DifficultyLevel = DifficultyLevel.BASIC
    question_text: str = ""
    context: Optional[str] = None  # Background info user needs
    expected_concepts: List[str] = field(default_factory=list)  # Key concepts to cover
    scaffold_hints: List[str] = field(default_factory=list)  # Hints if struggling


@dataclass
class SocraticResponse:
    """
    User's response to a Socratic question with assessment
    """
    question_id: str
    response_text: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Assessment
    rubric: Optional[SynthesisRubric] = None
    concepts_covered: List[str] = field(default_factory=list)
    novel_insights: List[str] = field(default_factory=list)

    # Feedback
    ai_feedback: str = ""
    validation: str = ""  # On success: affirm insight
    next_challenge: Optional[str] = None  # Next harder question


@dataclass
class DeepDiveSession:
    """
    A complete Learn About Me session

    Tracks progression through Socratic dialogue in a domain.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    domain: str = ""

    # Session state
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    active: bool = True

    # Progression tracking
    current_difficulty: DifficultyLevel = DifficultyLevel.BASIC
    questions_asked: List[SocraticQuestion] = field(default_factory=list)
    responses_given: List[SocraticResponse] = field(default_factory=list)

    # Skill ceiling measurement
    highest_difficulty_achieved: DifficultyLevel = DifficultyLevel.BASIC
    skill_ceiling_score: float = 0.0  # 0-1, based on highest quality response

    # User control
    user_requested_exit: bool = False
    opted_out_at: Optional[datetime] = None


@dataclass
class KnowledgeProfile:
    """
    Long-term user knowledge profile for a domain

    Stored in EnhancedContextManager as specialized memories.
    Gold standard measurement for ARI-Knowledge.
    """
    user_id: str
    domain: str

    # Validated capabilities
    validated_difficulty_level: DifficultyLevel = DifficultyLevel.BASIC
    skill_ceiling: float = 0.0  # 0-1
    synthesis_avg_accuracy: float = 0.0
    synthesis_avg_logic: float = 0.0
    synthesis_avg_completeness: float = 0.0

    # Learning style
    prefers_concrete_examples: bool = False
    prefers_abstract_theory: bool = False
    typical_response_depth: int = 0  # Average word count of responses

    # Engagement
    total_sessions: int = 0
    last_session_date: Optional[datetime] = None
    total_questions_answered: int = 0

    # Profile confidence
    confidence_score: float = 0.0  # 0-1, higher with more data


class LearnAboutMeInterface:
    """
    User-facing interface for "Learn About Me" (Deep Dive) mode

    This is the "cognitive release valve" - an opt-in space for users who
    want to be challenged and build a validated skill profile.

    Key Features:
    - User-initiated opt-in (never default)
    - Adaptive Socratic questioning (basic → mastery)
    - Synthesis grading (Accuracy, Logic, Completeness)
    - Rewarding progression or scaffolding support
    - Profile updates to long-term user model
    - Full user control (off-ramp always available)
    - Humanity override (appeal AI's grade)
    """

    def __init__(
        self,
        ari_monitor: ARIMonitor,
        context_manager: EnhancedContextManager,
        orchestrator: MultiModelOrchestrator,
    ):
        """
        Initialize Learn About Me interface

        Args:
            ari_monitor: For recording ARI-Synthesis and ARI-Knowledge metrics
            context_manager: For storing knowledge profiles
            orchestrator: For generating Socratic questions and grading responses
        """
        self.ari_monitor = ari_monitor
        self.context_manager = context_manager
        self.orchestrator = orchestrator

        # Active sessions
        self.active_sessions: Dict[str, DeepDiveSession] = {}

        logger.info("Learn About Me Interface initialized")

    async def start_deep_dive(
        self,
        user_id: str,
        domain: str
    ) -> DeepDiveSession:
        """
        Start a Deep Dive session (user-initiated opt-in)

        Args:
            user_id: User who wants to be challenged
            domain: Knowledge domain to explore (e.g., "machine learning")

        Returns:
            DeepDiveSession
        """
        logger.info(f"Starting Deep Dive session for user {user_id} in domain '{domain}'")

        # Load existing knowledge profile if available
        profile = await self._load_knowledge_profile(user_id, domain)

        # Create session
        session = DeepDiveSession(
            user_id=user_id,
            domain=domain,
            current_difficulty=profile.validated_difficulty_level if profile else DifficultyLevel.BASIC,
        )

        self.active_sessions[user_id] = session

        logger.info(
            f"Deep Dive session {session.session_id} started "
            f"(starting difficulty: {session.current_difficulty})"
        )

        return session

    async def get_next_question(
        self,
        user_id: str
    ) -> SocraticQuestion:
        """
        Get next Socratic question adapted to user's level

        Progressively increases difficulty as user demonstrates mastery.

        Args:
            user_id: User in active session

        Returns:
            SocraticQuestion at appropriate difficulty level
        """
        session = self.active_sessions.get(user_id)
        if not session or not session.active:
            raise ValueError(f"No active Deep Dive session for user {user_id}")

        logger.info(
            f"Generating Socratic question for {user_id} "
            f"(domain: {session.domain}, difficulty: {session.current_difficulty})"
        )

        # Generate question using AI
        question = await self._generate_socratic_question(
            domain=session.domain,
            difficulty=session.current_difficulty,
            previous_responses=session.responses_given[-3:],  # Last 3 responses for context
        )

        # Record question
        session.questions_asked.append(question)

        logger.debug(f"Generated question: '{question.question_text[:100]}...'")

        return question

    async def submit_response(
        self,
        user_id: str,
        question_id: str,
        response_text: str
    ) -> SocraticResponse:
        """
        Submit user's response and get AI assessment + feedback

        Args:
            user_id: User submitting response
            question_id: Question being answered
            response_text: User's answer

        Returns:
            SocraticResponse with assessment and feedback
        """
        session = self.active_sessions.get(user_id)
        if not session or not session.active:
            raise ValueError(f"No active Deep Dive session for user {user_id}")

        # Find question
        question = next(
            (q for q in session.questions_asked if q.question_id == question_id),
            None
        )
        if not question:
            raise ValueError(f"Question {question_id} not found")

        logger.info(
            f"Evaluating response from {user_id} "
            f"(length: {len(response_text)} chars, difficulty: {question.difficulty})"
        )

        # Grade response using AI
        assessment = await self._grade_response(
            question=question,
            response_text=response_text,
            domain=session.domain,
        )

        # Create response record
        response = SocraticResponse(
            question_id=question_id,
            response_text=response_text,
            rubric=assessment["rubric"],
            concepts_covered=assessment["concepts_covered"],
            novel_insights=assessment["novel_insights"],
            ai_feedback=assessment["feedback"],
            validation=assessment["validation"],
            next_challenge=assessment.get("next_challenge"),
        )

        # Record response
        session.responses_given.append(response)

        # Update session based on performance
        await self._update_session_progression(session, response)

        # Record ARI snapshot for ARI-Synthesis measurement
        await self._record_ari_synthesis_snapshot(user_id, session, question, response)

        logger.info(
            f"Response assessed: {response.rubric.quality.value} "
            f"(overall score: {response.rubric.overall_score:.2f})"
        )

        return response

    async def request_scaffold(
        self,
        user_id: str,
        question_id: str
    ) -> Dict[str, Any]:
        """
        User requests a hint/scaffold for current question

        Args:
            user_id: User requesting help
            question_id: Question needing scaffold

        Returns:
            Dict with scaffold hint and simplified question
        """
        session = self.active_sessions.get(user_id)
        if not session:
            raise ValueError(f"No active session for user {user_id}")

        question = next(
            (q for q in session.questions_asked if q.question_id == question_id),
            None
        )
        if not question:
            raise ValueError(f"Question {question_id} not found")

        logger.info(f"User {user_id} requested scaffold for question {question_id}")

        # Provide hint or simpler question
        if question.scaffold_hints:
            hint = question.scaffold_hints[0]  # First hint
        else:
            hint = await self._generate_scaffold_hint(question, session.domain)

        return {
            "hint": hint,
            "encouragement": "That's okay! Let's break this down together.",
            "simpler_question": await self._simplify_question(question),
        }

    async def exit_deep_dive(
        self,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        User exits Deep Dive mode (full user control)

        Args:
            user_id: User exiting
            reason: Optional reason for exit

        Returns:
            Dict with session summary
        """
        session = self.active_sessions.get(user_id)
        if not session:
            raise ValueError(f"No active session for user {user_id}")

        logger.info(f"User {user_id} exiting Deep Dive mode (reason: {reason})")

        # Mark session as ended
        session.active = False
        session.ended_at = datetime.now()
        session.user_requested_exit = True
        session.opted_out_at = datetime.now()

        # Update knowledge profile
        await self._update_knowledge_profile(session)

        # Generate summary
        summary = {
            "session_id": session.session_id,
            "duration_minutes": (session.ended_at - session.started_at).total_seconds() / 60,
            "questions_answered": len(session.responses_given),
            "highest_difficulty_reached": session.highest_difficulty_achieved.value,
            "skill_ceiling_score": session.skill_ceiling_score,
            "average_quality": self._calculate_average_quality(session),
        }

        # Clean up active session
        del self.active_sessions[user_id]

        logger.info(f"Deep Dive session {session.session_id} completed: {summary}")

        return summary

    async def appeal_grade(
        self,
        user_id: str,
        response_id: str,
        appeal_reason: str
    ) -> Dict[str, Any]:
        """
        User appeals AI's grade (Humanity Override)

        Args:
            user_id: User appealing
            response_id: Response being appealed
            appeal_reason: Why user disagrees

        Returns:
            Dict with appeal result
        """
        session = self.active_sessions.get(user_id)
        if not session:
            raise ValueError(f"No active session for user {user_id}")

        logger.info(f"User {user_id} appealing grade for response {response_id}")

        # Find response
        response = next(
            (r for r in session.responses_given if r.question_id == response_id),
            None
        )
        if not response:
            raise ValueError(f"Response {response_id} not found")

        # Re-evaluate with human oversight flag
        reevaluation = await self._reevaluate_response(
            response,
            appeal_reason,
            session.domain,
        )

        return {
            "appeal_accepted": reevaluation["grade_changed"],
            "original_score": response.rubric.overall_score,
            "new_score": reevaluation.get("new_score"),
            "explanation": reevaluation["explanation"],
            "humanity_override_logged": True,  # Logged for oversight
        }

    async def get_knowledge_profile(
        self,
        user_id: str,
        domain: str
    ) -> Optional[KnowledgeProfile]:
        """
        Get user's validated knowledge profile for domain

        Args:
            user_id: User to look up
            domain: Knowledge domain

        Returns:
            KnowledgeProfile if exists, else None
        """
        return await self._load_knowledge_profile(user_id, domain)

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _generate_socratic_question(
        self,
        domain: str,
        difficulty: DifficultyLevel,
        previous_responses: List[SocraticResponse],
    ) -> SocraticQuestion:
        """Generate Socratic question using AI"""

        # Build prompt for AI
        prompt = self._build_question_generation_prompt(
            domain, difficulty, previous_responses
        )

        # Generate question using orchestrator
        response = await self.orchestrator.route_request(
            prompt=prompt,
            task_complexity=TaskComplexity.MODERATE,
            optimization_goal="quality",
        )

        # Parse AI response into SocraticQuestion
        question_data = self._parse_question_response(response["response"])

        return SocraticQuestion(
            domain=domain,
            difficulty=difficulty,
            question_text=question_data["question"],
            context=question_data.get("context"),
            expected_concepts=question_data.get("expected_concepts", []),
            scaffold_hints=question_data.get("hints", []),
        )

    def _build_question_generation_prompt(
        self,
        domain: str,
        difficulty: DifficultyLevel,
        previous_responses: List[SocraticResponse],
    ) -> str:
        """Build prompt for AI question generation"""

        context = ""
        if previous_responses:
            context = "Previous responses:\n"
            for i, resp in enumerate(previous_responses[-3:], 1):
                context += f"{i}. {resp.response_text[:200]}...\n"

        prompt = f"""Generate a Socratic question to probe understanding of {domain}.

Difficulty level: {difficulty.name} (scale 1-5: {difficulty.value})

{context}

Generate a question that:
1. Builds on previous responses if available
2. Probes deeper understanding at the specified difficulty
3. Encourages synthesis and logical reasoning
4. Has clear expected concepts to cover

Return as JSON:
{{
    "question": "The Socratic question text",
    "context": "Background info if needed",
    "expected_concepts": ["concept1", "concept2"],
    "hints": ["hint if they struggle"]
}}
"""
        return prompt

    def _parse_question_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into question data"""
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if AI doesn't return valid JSON
            return {
                "question": response,
                "context": None,
                "expected_concepts": [],
                "hints": [],
            }

    async def _grade_response(
        self,
        question: SocraticQuestion,
        response_text: str,
        domain: str,
    ) -> Dict[str, Any]:
        """Grade user response using Synthesis Rubric"""

        prompt = f"""Grade this response using the Synthesis Rubric:

Domain: {domain}
Question: {question.question_text}
Expected concepts: {', '.join(question.expected_concepts)}

User's response:
{response_text}

Grade on three dimensions (0-1 scale):
1. Accuracy: Is the reasoning logically correct?
2. Logic: Does the chain of reasoning hold up?
3. Completeness: Did they address all key aspects?

Also identify:
- Concepts covered from expected list
- Novel insights (unexpected connections/ideas)
- Appropriate feedback
- Validation message (if excellent/proficient)
- Next challenge (if they're ready for harder question)

Return as JSON:
{{
    "accuracy": 0.0-1.0,
    "logic": 0.0-1.0,
    "completeness": 0.0-1.0,
    "concepts_covered": ["concept1", ...],
    "novel_insights": ["insight1", ...],
    "feedback": "Constructive feedback",
    "validation": "Affirmation of insight (if applicable)",
    "next_challenge": "Next harder question (if ready)"
}}
"""

        response = await self.orchestrator.route_request(
            prompt=prompt,
            task_complexity=TaskComplexity.MODERATE,
            optimization_goal="quality",
        )

        # Parse grading response
        grading = self._parse_grading_response(response["response"])

        # Create rubric
        rubric = SynthesisRubric(
            accuracy_score=grading["accuracy"],
            logic_score=grading["logic"],
            completeness_score=grading["completeness"],
        )

        return {
            "rubric": rubric,
            "concepts_covered": grading.get("concepts_covered", []),
            "novel_insights": grading.get("novel_insights", []),
            "feedback": grading.get("feedback", ""),
            "validation": grading.get("validation", ""),
            "next_challenge": grading.get("next_challenge"),
        }

    def _parse_grading_response(self, response: str) -> Dict[str, Any]:
        """Parse AI grading response"""
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback with default grades
            return {
                "accuracy": 0.7,
                "logic": 0.7,
                "completeness": 0.7,
                "concepts_covered": [],
                "novel_insights": [],
                "feedback": "Thank you for your response.",
                "validation": "",
                "next_challenge": None,
            }

    async def _update_session_progression(
        self,
        session: DeepDiveSession,
        response: SocraticResponse,
    ) -> None:
        """Update session based on response quality"""

        quality = response.rubric.quality

        # On success: increase difficulty
        if quality in [ResponseQuality.EXCELLENT, ResponseQuality.PROFICIENT]:
            if response.rubric.overall_score >= 0.80:
                # Ready for next level
                if session.current_difficulty.value < DifficultyLevel.MASTERY.value:
                    session.current_difficulty = DifficultyLevel(
                        session.current_difficulty.value + 1
                    )
                    logger.info(f"Difficulty increased to {session.current_difficulty}")

                # Update skill ceiling
                session.highest_difficulty_achieved = max(
                    session.highest_difficulty_achieved,
                    session.current_difficulty,
                    key=lambda d: d.value,
                )
                session.skill_ceiling_score = max(
                    session.skill_ceiling_score,
                    response.rubric.overall_score,
                )

        # On struggle: offer scaffold (handled via request_scaffold)
        elif quality == ResponseQuality.STRUGGLING:
            logger.info(f"User struggling at difficulty {session.current_difficulty}")

        # On insufficient: decrease difficulty
        elif quality == ResponseQuality.INSUFFICIENT:
            if session.current_difficulty.value > DifficultyLevel.BASIC.value:
                session.current_difficulty = DifficultyLevel(
                    session.current_difficulty.value - 1
                )
                logger.info(f"Difficulty decreased to {session.current_difficulty}")

    async def _record_ari_synthesis_snapshot(
        self,
        user_id: str,
        session: DeepDiveSession,
        question: SocraticQuestion,
        response: SocraticResponse,
    ) -> None:
        """Record ARI snapshot for synthesis measurement"""

        # Map synthesis rubric to ARI metrics
        rubric = response.rubric

        snapshot = AgencySnapshot(
            timestamp=datetime.now(),
            task_id=response.question_id,
            task_type=f"deep_dive_{session.domain}",
            # Synthesis quality maps to skill metrics
            delta_agency=0.1 if rubric.quality in [ResponseQuality.EXCELLENT, ResponseQuality.PROFICIENT] else -0.05,
            bhir=0.95,  # High benefit from learning
            task_efficacy=rubric.overall_score,
            user_skill_before=session.skill_ceiling_score,
            user_skill_after=max(session.skill_ceiling_score, rubric.overall_score),
            skill_development=max(0, rubric.overall_score - session.skill_ceiling_score),
            ai_reliance=0.2,  # Low - user doing synthesis themselves
            autonomy_retention=0.95,  # High - full user control
            user_id=user_id,
            session_id=session.session_id,
            metadata={
                "mode": "deep_dive",
                "domain": session.domain,
                "difficulty": question.difficulty.value,
                "synthesis_accuracy": rubric.accuracy_score,
                "synthesis_logic": rubric.logic_score,
                "synthesis_completeness": rubric.completeness_score,
            },
        )

        await self.ari_monitor.record_snapshot(snapshot)

        logger.debug(f"ARI-Synthesis snapshot recorded for {user_id}")

    async def _load_knowledge_profile(
        self,
        user_id: str,
        domain: str,
    ) -> Optional[KnowledgeProfile]:
        """Load knowledge profile from context manager"""

        # Search for knowledge profile memory
        memories = await self.context_manager.search_memories(
            user_id=user_id,
            query=f"knowledge_profile_{domain}",
            memory_types=[MemoryType.SKILL],
            tags={"knowledge_profile", domain},
            limit=1,
        )

        if not memories:
            return None

        # Parse profile from memory metadata
        memory = memories[0]
        metadata = memory.metadata

        return KnowledgeProfile(
            user_id=user_id,
            domain=domain,
            validated_difficulty_level=DifficultyLevel(metadata.get("difficulty_level", 1)),
            skill_ceiling=metadata.get("skill_ceiling", 0.0),
            synthesis_avg_accuracy=metadata.get("avg_accuracy", 0.0),
            synthesis_avg_logic=metadata.get("avg_logic", 0.0),
            synthesis_avg_completeness=metadata.get("avg_completeness", 0.0),
            total_sessions=metadata.get("total_sessions", 0),
            total_questions_answered=metadata.get("total_questions", 0),
            confidence_score=metadata.get("confidence", 0.0),
        )

    async def _update_knowledge_profile(
        self,
        session: DeepDiveSession,
    ) -> None:
        """Update knowledge profile after session"""

        # Load existing profile
        profile = await self._load_knowledge_profile(session.user_id, session.domain)

        if not profile:
            profile = KnowledgeProfile(
                user_id=session.user_id,
                domain=session.domain,
            )

        # Update with session data
        profile.validated_difficulty_level = max(
            profile.validated_difficulty_level,
            session.highest_difficulty_achieved,
            key=lambda d: d.value,
        )
        profile.skill_ceiling = max(profile.skill_ceiling, session.skill_ceiling_score)
        profile.total_sessions += 1
        profile.last_session_date = session.ended_at
        profile.total_questions_answered += len(session.responses_given)

        # Calculate average synthesis scores
        if session.responses_given:
            profile.synthesis_avg_accuracy = sum(
                r.rubric.accuracy_score for r in session.responses_given
            ) / len(session.responses_given)
            profile.synthesis_avg_logic = sum(
                r.rubric.logic_score for r in session.responses_given
            ) / len(session.responses_given)
            profile.synthesis_avg_completeness = sum(
                r.rubric.completeness_score for r in session.responses_given
            ) / len(session.responses_given)

        # Increase confidence with more data
        profile.confidence_score = min(1.0, profile.total_questions_answered / 20.0)

        # Save to context manager
        await self.context_manager.add_memory(
            user_id=profile.user_id,
            content=f"Knowledge profile for {profile.domain}: Level {profile.validated_difficulty_level.value}, Ceiling {profile.skill_ceiling:.2f}",
            memory_type=MemoryType.SKILL,
            priority=MemoryPriority.HIGH,
            tags={"knowledge_profile", profile.domain},
            metadata={
                "difficulty_level": profile.validated_difficulty_level.value,
                "skill_ceiling": profile.skill_ceiling,
                "avg_accuracy": profile.synthesis_avg_accuracy,
                "avg_logic": profile.synthesis_avg_logic,
                "avg_completeness": profile.synthesis_avg_completeness,
                "total_sessions": profile.total_sessions,
                "total_questions": profile.total_questions_answered,
                "confidence": profile.confidence_score,
            },
        )

        logger.info(
            f"Knowledge profile updated for {profile.user_id} in {profile.domain}: "
            f"Level {profile.validated_difficulty_level.value}, Confidence {profile.confidence_score:.2f}"
        )

    async def _generate_scaffold_hint(
        self,
        question: SocraticQuestion,
        domain: str,
    ) -> str:
        """Generate scaffold hint for struggling user"""

        prompt = f"""Generate a helpful hint for this Socratic question:

Domain: {domain}
Question: {question.question_text}

The user is struggling. Provide a hint that:
1. Doesn't give away the answer
2. Guides them toward the key concepts
3. Encourages them to keep thinking
4. Is supportive and non-judgmental

Return just the hint text.
"""

        response = await self.orchestrator.route_request(
            prompt=prompt,
            task_complexity=TaskComplexity.TRIVIAL,
            optimization_goal="speed",
        )

        return response["response"]

    async def _simplify_question(
        self,
        question: SocraticQuestion,
    ) -> str:
        """Generate simpler version of question"""

        prompt = f"""Simplify this question to be more accessible:

Original: {question.question_text}

Create a simpler version that:
1. Uses more concrete language
2. Breaks down the complexity
3. Maintains the core concept

Return just the simplified question.
"""

        response = await self.orchestrator.route_request(
            prompt=prompt,
            task_complexity=TaskComplexity.TRIVIAL,
            optimization_goal="speed",
        )

        return response["response"]

    async def _reevaluate_response(
        self,
        response: SocraticResponse,
        appeal_reason: str,
        domain: str,
    ) -> Dict[str, Any]:
        """Re-evaluate response after user appeal"""

        prompt = f"""Re-evaluate this response after user appeal:

Domain: {domain}
Original response: {response.response_text}
Original scores: Accuracy={response.rubric.accuracy_score}, Logic={response.rubric.logic_score}, Completeness={response.rubric.completeness_score}

User's appeal: {appeal_reason}

Consider:
1. Did the AI miss valid reasoning?
2. Are there alternative valid interpretations?
3. Should the grade be adjusted?

Return as JSON:
{{
    "grade_changed": true/false,
    "new_score": 0.0-1.0 (if changed),
    "explanation": "Why grade was/wasn't changed"
}}
"""

        result = await self.orchestrator.route_request(
            prompt=prompt,
            task_complexity=TaskComplexity.MODERATE,
            optimization_goal="quality",
        )

        import json
        try:
            return json.loads(result["response"])
        except json.JSONDecodeError:
            return {
                "grade_changed": False,
                "explanation": "Unable to re-evaluate at this time.",
            }

    def _calculate_average_quality(self, session: DeepDiveSession) -> float:
        """Calculate average response quality for session"""
        if not session.responses_given:
            return 0.0

        return sum(r.rubric.overall_score for r in session.responses_given) / len(
            session.responses_given
        )
