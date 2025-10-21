"""
Learning Module - VARK-based personalized learning.

Implements the VARK learning model:
- Visual: Diagrams, charts, images
- Aural: Listening, discussion, verbal explanation
- Read/Write: Text, reading, writing
- Kinesthetic: Hands-on, practice, examples

Maintains Zone of Proximal Development for optimal learning.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from ai_pal.modules.base import BaseModule, ModuleRequest, ModuleResponse


class VARKStyle(Enum):
    """VARK learning styles."""

    VISUAL = "visual"
    AURAL = "aural"
    READ_WRITE = "read_write"
    KINESTHETIC = "kinesthetic"
    MULTIMODAL = "multimodal"


@dataclass
class LearningProfile:
    """User's learning profile."""

    user_id: str
    primary_style: VARKStyle
    secondary_styles: List[VARKStyle]
    skill_level: Dict[str, float]  # domain -> level (0-1)
    learning_velocity: float  # How fast they learn
    preferred_challenge_level: float  # 0-1, where 0.5 is optimal ZPD
    interests: List[str]
    learning_goals: List[str]
    last_updated: datetime


class LearningModule(BaseModule):
    """Personalized learning module using VARK model."""

    def __init__(self):
        super().__init__(
            name="learning",
            description="VARK-based personalized learning system",
            version="0.1.0",
        )

        self.learning_profiles: Dict[str, LearningProfile] = {}

    async def initialize(self) -> None:
        """Initialize the module."""
        logger.info("Initializing Learning module...")
        self.initialized = True
        logger.info("Learning module initialized")

    async def process(self, request: ModuleRequest) -> ModuleResponse:
        """Process a learning request."""
        start_time = datetime.now()

        user_id = request.user_id
        task = request.task
        context = request.context

        # Get or create learning profile
        profile = self._get_or_create_profile(user_id, context)

        # Detect learning style if not set
        if profile.primary_style == VARKStyle.MULTIMODAL:
            profile.primary_style = await self._detect_learning_style(
                user_id, context
            )

        # Adapt content to learning style
        adapted_content = self._adapt_to_learning_style(task, profile, context)

        # Track learning progress
        self._update_learning_progress(user_id, task, context)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ModuleResponse(
            result=adapted_content,
            confidence=0.8,
            metadata={
                "learning_style": profile.primary_style.value,
                "skill_level": profile.skill_level,
                "learning_velocity": profile.learning_velocity,
            },
            timestamp=datetime.now(),
            processing_time_ms=processing_time,
        )

    def _get_or_create_profile(
        self, user_id: str, context: Dict[str, Any]
    ) -> LearningProfile:
        """Get or create learning profile for user."""
        if user_id not in self.learning_profiles:
            # Create new profile
            profile = LearningProfile(
                user_id=user_id,
                primary_style=VARKStyle.MULTIMODAL,  # Detect on first use
                secondary_styles=[],
                skill_level={},
                learning_velocity=0.5,  # Average
                preferred_challenge_level=0.5,  # Optimal ZPD
                interests=context.get("interests", []),
                learning_goals=context.get("learning_goals", []),
                last_updated=datetime.now(),
            )
            self.learning_profiles[user_id] = profile
            logger.info(f"Created new learning profile for user {user_id}")

        return self.learning_profiles[user_id]

    async def _detect_learning_style(
        self, user_id: str, context: Dict[str, Any]
    ) -> VARKStyle:
        """
        Detect user's learning style from interactions.

        In production, this would analyze:
        - Preference for diagrams vs text
        - Engagement with audio explanations
        - Request for hands-on examples
        - Reading/writing patterns
        """
        # Simplified detection from context hints
        preferences = context.get("style_preferences", {})

        if preferences.get("prefers_diagrams"):
            return VARKStyle.VISUAL
        elif preferences.get("prefers_audio"):
            return VARKStyle.AURAL
        elif preferences.get("prefers_text"):
            return VARKStyle.READ_WRITE
        elif preferences.get("prefers_practice"):
            return VARKStyle.KINESTHETIC

        # Default to read/write (most common in text interfaces)
        return VARKStyle.READ_WRITE

    def _adapt_to_learning_style(
        self, content: str, profile: LearningProfile, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapt content to user's learning style.

        Args:
            content: Content to adapt
            profile: User's learning profile
            context: Additional context

        Returns:
            Adapted content
        """
        adapted = {
            "content": content,
            "style": profile.primary_style.value,
            "adaptations": [],
        }

        if profile.primary_style == VARKStyle.VISUAL:
            adapted["adaptations"].append(
                "Include diagrams, charts, and visual representations"
            )
            adapted["suggestion"] = (
                "I'll explain this with visual aids and diagrams where possible."
            )

        elif profile.primary_style == VARKStyle.AURAL:
            adapted["adaptations"].append(
                "Use conversational tone, verbal explanations"
            )
            adapted["suggestion"] = (
                "I'll explain this verbally with analogies and discussion."
            )

        elif profile.primary_style == VARKStyle.READ_WRITE:
            adapted["adaptations"].append(
                "Provide detailed text, lists, written summaries"
            )
            adapted["suggestion"] = (
                "I'll provide detailed written explanations and summaries."
            )

        elif profile.primary_style == VARKStyle.KINESTHETIC:
            adapted["adaptations"].append(
                "Include hands-on examples, practice exercises, real-world applications"
            )
            adapted["suggestion"] = (
                "I'll include hands-on examples and practice exercises you can try."
            )

        # Add ZPD-appropriate challenge level
        skill_level = self._estimate_skill_level(profile, context)
        adapted["challenge_level"] = self._calculate_zpd_level(skill_level)

        return adapted

    def _estimate_skill_level(
        self, profile: LearningProfile, context: Dict[str, Any]
    ) -> float:
        """
        Estimate user's skill level for current topic.

        Returns:
            Skill level (0-1)
        """
        domain = context.get("domain", "general")

        if domain in profile.skill_level:
            return profile.skill_level[domain]

        # Default to beginner-intermediate
        return 0.3

    def _calculate_zpd_level(self, current_skill: float) -> float:
        """
        Calculate optimal Zone of Proximal Development level.

        The ZPD is slightly above current skill level - challenging but achievable.

        Args:
            current_skill: Current skill level (0-1)

        Returns:
            Optimal challenge level (0-1)
        """
        # Optimal ZPD is typically current_skill + 0.2
        # (i.e., 20% more difficult than current level)
        zpd = min(current_skill + 0.2, 1.0)
        return zpd

    def _update_learning_progress(
        self, user_id: str, task: str, context: Dict[str, Any]
    ) -> None:
        """
        Update learning progress for user.

        Tracks:
        - Skill development
        - Learning velocity
        - Topic mastery
        """
        if user_id not in self.learning_profiles:
            return

        profile = self.learning_profiles[user_id]

        # Update skill level if provided in context
        domain = context.get("domain", "general")
        success = context.get("task_success", True)

        if success:
            # Increase skill level slightly
            current = profile.skill_level.get(domain, 0.3)
            profile.skill_level[domain] = min(current + 0.05, 1.0)

            # Increase learning velocity slightly
            profile.learning_velocity = min(profile.learning_velocity + 0.01, 1.0)

        profile.last_updated = datetime.now()

        logger.debug(
            f"Updated learning progress for {user_id}: "
            f"{domain} -> {profile.skill_level.get(domain, 0):.2f}"
        )

    async def shutdown(self) -> None:
        """Cleanup resources."""
        logger.info("Shutting down Learning module...")
        # Save learning profiles if needed
        self.initialized = False
