"""
Strength Amplifier Component (Basic MVP Version)

The "pride engine" - transforms generic tasks into personal missions
by leveraging user's core identity and strengths.
"""

from typing import List, Optional
from loguru import logger

from ..interfaces import IStrengthAmplifier
from ..models import PersonalityProfile, SignatureStrength, StrengthType, AtomicBlock


class StrengthAmplifier(IStrengthAmplifier):
    """
    Basic implementation of Signature Strength Amplifier

    Uses template-based reframing to connect tasks to user strengths.
    Full AI-powered version will be implemented in Phase 5.2.
    """

    # Reframing templates by strength type
    REFRAME_TEMPLATES = {
        StrengthType.VISUAL_THINKING: [
            "Visualize {task} as a clear picture",
            "Picture how {task} fits into the bigger visual",
            "Use your visual thinking to see the structure of {task}",
        ],
        StrengthType.SPATIAL: [
            "Map out the space and structure of {task}",
            "Organize {task} spatially in your mind",
            "Use your spatial awareness for {task}",
        ],
        StrengthType.ANALYTICAL: [
            "Break {task} down into logical steps",
            "Apply systematic reasoning to {task}",
            "Analyze the logical structure of {task}",
        ],
        StrengthType.KINESTHETIC: [
            "Get hands-on with {task}",
            "Build momentum through action on {task}",
            "Make {task} tangible and physical",
        ],
        StrengthType.VERBAL: [
            "Articulate the key elements of {task}",
            "Express {task} in your own words",
            "Use your way with words to clarify {task}",
        ],
        StrengthType.SOCIAL: [
            "Consider how {task} connects with others",
            "Use your social skills to collaborate on {task}",
            "See {task} through a relationship lens",
        ],
        StrengthType.EMPATHETIC: [
            "Understand the emotional dimension of {task}",
            "Use empathy to approach {task}",
            "Consider how {task} affects people",
        ],
        StrengthType.SYSTEMATIC: [
            "Create a system for {task}",
            "Organize {task} methodically",
            "Build a structured approach to {task}",
        ],
        StrengthType.MUSICAL: [
            "Find the rhythm and flow of {task}",
            "Create a harmonious approach to {task}",
            "Feel the natural tempo of {task}",
        ],
        StrengthType.CREATIVE: [
            "Find a creative angle on {task}",
            "Innovate your approach to {task}",
            "Use your creativity to reimagine {task}",
        ],
    }

    def __init__(self):
        """Initialize Strength Amplifier"""
        logger.info("Strength Amplifier initialized (basic MVP version)")

    async def identify_strengths(
        self,
        personality: PersonalityProfile
    ) -> List[SignatureStrength]:
        """
        Identify user's signature strengths from personality profile

        Args:
            personality: User's personality profile

        Returns:
            List of identified signature strengths
        """
        logger.debug(f"Identifying strengths for user {personality.user_id}")

        # Return strengths from profile
        if personality.signature_strengths:
            logger.info(f"Found {len(personality.signature_strengths)} strengths for user")
            return personality.signature_strengths

        # If no strengths defined, return empty list
        logger.warning(f"No signature strengths found for user {personality.user_id}")
        return []

    async def reframe_task_via_strength(
        self,
        task_description: str,
        strength: SignatureStrength
    ) -> str:
        """
        Reframe a generic task through the lens of a signature strength

        Args:
            task_description: Original task description
            strength: Strength to apply

        Returns:
            Reframed task description
        """
        logger.debug(f"Reframing task via {strength.strength_type.value} strength")

        # Get templates for this strength type
        templates = self.REFRAME_TEMPLATES.get(
            strength.strength_type,
            ["Apply your {strength} to {task}"]
        )

        # Use first template (in full version, would rotate or AI-select)
        template = templates[0]

        # Apply template
        reframed = template.format(task=task_description)

        logger.info(f"Reframed: '{task_description[:30]}...' → '{reframed[:50]}...'")

        return reframed

    async def amplify_with_best_match(
        self,
        task_description: str,
        strengths: List[SignatureStrength]
    ) -> tuple[str, SignatureStrength]:
        """
        Find best strength match and reframe task

        Args:
            task_description: Task to amplify
            strengths: Available strengths

        Returns:
            (reframed_description, strength_used)
        """
        if not strengths:
            logger.warning("No strengths available for amplification")
            return task_description, None

        # Simple heuristic: use the first strength with proficiency > 0.5
        best_strength = None
        for strength in strengths:
            if strength.proficiency_level > 0.5:
                best_strength = strength
                break

        # Fallback to first strength if none meet threshold
        if not best_strength:
            best_strength = strengths[0]

        # Reframe via this strength
        reframed = await self.reframe_task_via_strength(task_description, best_strength)

        return reframed, best_strength

    async def generate_reward_language(
        self,
        block: AtomicBlock,
        strength: SignatureStrength
    ) -> str:
        """
        Generate identity-affirming reward language

        Args:
            block: Completed atomic block
            strength: Strength that was used

        Returns:
            Reward language string
        """
        # Use the identity label from the strength
        identity = strength.identity_label if strength.identity_label else f"{strength.strength_type.value} thinker"
        
        # Basic template
        return f"You {block.title} using your {identity} strength"

    async def match_task_to_strength(
        self,
        task_description: str,
        available_strengths: List[SignatureStrength]
    ) -> Optional[SignatureStrength]:
        """
        Find the best strength match for a task

        Args:
            task_description: Task to match
            available_strengths: Available strengths

        Returns:
            Best matched strength or None
        """
        # Simple heuristic: return first strength with high proficiency
        for strength in available_strengths:
            if strength.proficiency_level > 0.6:
                return strength
        
        # Fallback to first strength
        return available_strengths[0] if available_strengths else None
