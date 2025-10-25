"""
Signature Strength Interface - User interaction layer for strength-based task reframing

This is both a backend component (StrengthAmplifier) and a frontend interface.
It provides:
1. Interactive task reframing (show user how their strength transforms a task)
2. Reward message display (show identity-affirming rewards)
3. Strength selection (let user choose which strength to apply)

Powered by:
- StrengthAmplifier (backend engine)
- RewardEmitter (reward generation)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from loguru import logger

from ..models import (
    SignatureStrength,
    AtomicBlock,
    RewardMessage,
    StrengthType,
)


@dataclass
class ReframePresentation:
    """
    Presentation of task reframing for user

    Shows before/after transformation through strength lens
    """
    task_id: str
    original_task: str
    reframed_task: str
    strength_used: SignatureStrength
    identity_label: str
    explanation: str  # Why this reframe works


class StrengthInterface:
    """
    User-facing interface for signature strength amplification

    Provides interactive methods for users to:
    - See how their strengths transform tasks
    - Choose which strength to apply
    - View identity-affirming rewards
    """

    def __init__(self, strength_amplifier, reward_emitter):
        """
        Initialize Strength Interface

        Args:
            strength_amplifier: StrengthAmplifier instance (backend)
            reward_emitter: RewardEmitter instance (backend)
        """
        self.strength_amplifier = strength_amplifier
        self.reward_emitter = reward_emitter

        logger.info("Strength Interface initialized")

    async def present_task_reframe(
        self,
        user_id: str,
        task: str,
        strengths: List[SignatureStrength]
    ) -> List[ReframePresentation]:
        """
        Show user how their strengths can reframe a task

        Presents multiple options so user can choose their preferred framing.

        Args:
            user_id: User viewing reframes
            task: Generic task description
            strengths: User's available signature strengths

        Returns:
            List of reframe presentations (one per strength)
        """
        logger.info(f"Presenting task reframes for user {user_id}: '{task[:50]}...'")

        presentations = []

        for strength in strengths[:3]:  # Show top 3 strengths
            # Reframe via this strength
            reframed = await self.strength_amplifier.reframe_task_via_strength(task, strength)

            # Create presentation
            presentation = ReframePresentation(
                task_id=f"{user_id}_{hash(task)}",
                original_task=task,
                reframed_task=reframed,
                strength_used=strength,
                identity_label=strength.identity_label,
                explanation=f"Uses your {strength.identity_label} ability to approach this differently"
            )

            presentations.append(presentation)

            logger.debug(
                f"Reframe via {strength.strength_type.value}: "
                f"'{task[:30]}...' -> '{reframed[:30]}...'"
            )

        logger.info(f"Generated {len(presentations)} reframe options")

        return presentations

    async def select_strength(
        self,
        user_id: str,
        task: str,
        available_strengths: List[SignatureStrength]
    ) -> SignatureStrength:
        """
        Let user choose which strength to apply to a task

        In a full UI implementation, this would show options and wait for user input.
        For now, uses the amplifier's best-match algorithm.

        Args:
            user_id: User making the selection
            task: Task to reframe
            available_strengths: Strengths to choose from

        Returns:
            Selected signature strength
        """
        logger.info(f"User {user_id} selecting strength for task: '{task[:50]}...'")

        # Use amplifier's matching algorithm
        reframed, selected_strength = await self.strength_amplifier.amplify_with_best_match(
            task,
            available_strengths
        )

        logger.info(f"Selected strength: {selected_strength.strength_type.value if selected_strength else 'None'}")

        return selected_strength

    async def display_reward(
        self,
        user_id: str,
        reward: RewardMessage
    ) -> Dict[str, Any]:
        """
        Display identity-affirming reward to user

        Formats the reward for visual presentation.

        Args:
            user_id: User receiving reward
            reward: Reward message to display

        Returns:
            Display-ready reward data
        """
        logger.info(f"Displaying reward for user {user_id}")

        display_data = {
            "reward_text": reward.reward_text,
            "strength_referenced": reward.strength_referenced.value if reward.strength_referenced else None,
            "identity_label": reward.identity_label_used,
            "emitted_at": reward.emitted_at.isoformat(),
            "display_format": "celebration",  # UI hint
            "animation": "pride_hit",  # UI animation hint
        }

        logger.debug(f"Reward display: '{reward.reward_text[:50]}...'")

        return display_data

    async def show_strength_summary(
        self,
        user_id: str,
        strengths: List[SignatureStrength]
    ) -> Dict[str, Any]:
        """
        Show user a summary of their signature strengths

        Args:
            user_id: User to show summary for
            strengths: User's signature strengths

        Returns:
            Summary data for display
        """
        logger.info(f"Showing strength summary for user {user_id}")

        summary = {
            "total_strengths": len(strengths),
            "primary_strength": strengths[0].strength_type.value if strengths else None,
            "strengths_detail": [],
        }

        for strength in strengths:
            detail = {
                "strength_type": strength.strength_type.value,
                "identity_label": strength.identity_label,
                "description": strength.strength_description,
                "confidence": strength.confidence_score,
                "usage_count": strength.usage_count,
                "last_used": strength.last_used.isoformat() if strength.last_used else None,
            }
            summary["strengths_detail"].append(detail)

        return summary
