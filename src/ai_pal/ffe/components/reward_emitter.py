"""
Reward Emitter Component

Delivers identity-affirming psychological rewards when atomic blocks
are completed. Uses explicit language from Strength Amplifier.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from loguru import logger

from ..interfaces import IRewardEmitter
from ..models import (
    AtomicBlock,
    SignatureStrength,
    RewardMessage,
    StrengthType,
)


class RewardEmitter(IRewardEmitter):
    """
    Concrete implementation of Accomplishment Reward Emitter

    Generates pride-based, identity-affirming rewards that reference
    the user's signature strengths.
    """

    # Reward templates keyed by strength type
    REWARD_TEMPLATES = {
        StrengthType.VISUAL_SPATIAL: [
            "✓ Nicely done! You visualized the path forward like the {identity} you are.",
            "✓ Win! Your spatial thinking broke this down perfectly. That's your {identity} at work.",
            "✓ Accomplished! You saw the big picture. Classic {identity} strength.",
        ],
        StrengthType.LOGICAL_MATHEMATICAL: [
            "✓ Solid work! You reasoned through that systematically like the {identity} you are.",
            "✓ Completed! Your logical approach made this clear. That's your {identity} in action.",
            "✓ Success! You structured this perfectly. Textbook {identity} strength.",
        ],
        StrengthType.BODILY_KINESTHETIC: [
            "✓ Done! You built momentum through action like the {identity} you are.",
            "✓ Finished! Your hands-on approach crushed this. That's your {identity} strength.",
            "✓ Complete! You made it tangible. Pure {identity} power.",
        ],
        StrengthType.LINGUISTIC: [
            "✓ Nice! You articulated this clearly like the {identity} you are.",
            "✓ Achieved! Your way with words made the path obvious. That's your {identity} talent.",
            "✓ Completed! You expressed this perfectly. Classic {identity} strength.",
        ],
        StrengthType.INTERPERSONAL: [
            "✓ Well done! You connected the dots through empathy like the {identity} you are.",
            "✓ Success! Your people skills guided this. That's your {identity} superpower.",
            "✓ Accomplished! You saw how this affects others. True {identity} strength.",
        ],
        StrengthType.INTRAPERSONAL: [
            "✓ Completed! You understood your own capacity like the {identity} you are.",
            "✓ Done! Your self-awareness kept this on track. That's your {identity} strength.",
            "✓ Success! You knew yourself well enough to scope this right. Powerful {identity} insight.",
        ],
        StrengthType.MUSICAL_RHYTHMIC: [
            "✓ Finished! You found the rhythm of this task like the {identity} you are.",
            "✓ Completed! Your sense of flow made this smooth. That's your {identity} gift.",
            "✓ Done! You orchestrated this beautifully. Classic {identity} strength.",
        ],
        StrengthType.NATURALISTIC: [
            "✓ Accomplished! You saw the natural patterns like the {identity} you are.",
            "✓ Complete! Your systems thinking organized this. That's your {identity} talent.",
            "✓ Success! You understood the ecosystem. True {identity} strength.",
        ],
    }

    # Generic templates (when no strength specified)
    GENERIC_TEMPLATES = [
        "✓ Completed! You're building momentum.",
        "✓ Done! Another win in the books.",
        "✓ Accomplished! You followed through.",
        "✓ Success! You took action and finished.",
        "✓ Nice work! You made progress.",
    ]

    def __init__(self):
        """Initialize Reward Emitter"""
        self.emitted_rewards = {}  # message_id -> RewardMessage
        self.reward_count_by_user = {}  # user_id -> count
        logger.info("Reward Emitter initialized")

    async def emit_reward(
        self,
        block: AtomicBlock,
        strength: Optional[SignatureStrength] = None
    ) -> RewardMessage:
        """
        Generate and emit a reward for completed atomic block

        Args:
            block: The completed atomic block
            strength: The strength that was used (if any)

        Returns:
            RewardMessage containing affirmation
        """
        logger.debug(f"Emitting reward for block {block.block_id}")

        # Select template based on strength
        if strength and strength.strength_type:
            templates = self.REWARD_TEMPLATES.get(strength.strength_type, self.GENERIC_TEMPLATES)
            identity_label = strength.identity_label if strength.identity_label else f"{strength.strength_type.value} thinker"
            strength_type = strength.strength_type
        else:
            templates = self.GENERIC_TEMPLATES
            identity_label = "capable person"
            strength_type = None

        # Pick template (cycle through for variety)
        user_rewards = self.reward_count_by_user.get(block.user_id, 0)
        template = templates[user_rewards % len(templates)]

        # Generate reward text
        if "{identity}" in template:
            reward_text = template.format(identity=identity_label)
        else:
            reward_text = template

        # Create reward message
        reward = RewardMessage(
            message_id=str(uuid.uuid4()),
            user_id=block.user_id,
            block_id=block.block_id,
            reward_text=reward_text,
            strength_referenced=strength_type,
            identity_label_used=identity_label,
            template_used="strength_based" if strength else "generic",
            personalization_elements=[identity_label] if strength else [],
            emitted_at=datetime.now()
        )

        # Store reward
        self.emitted_rewards[reward.message_id] = reward
        self.reward_count_by_user[block.user_id] = user_rewards + 1

        logger.info(f"Emitted reward for user {block.user_id}: '{reward.reward_text}'")

        return reward

    async def calculate_pride_intensity(
        self,
        block: AtomicBlock,
        quality_score: float
    ) -> float:
        """
        Calculate how intense the "pride hit" should be

        Args:
            block: Completed block
            quality_score: User's self-assessed quality (0-1)

        Returns:
            Pride intensity (0-1)
        """
        # Base intensity from quality
        intensity = quality_score

        # Bonus for using signature strength
        if hasattr(block, 'strength_used') and block.strength_used:
            intensity = min(1.0, intensity + 0.2)

        # Bonus for completing harder blocks
        if block.estimated_effort > 0.7:
            intensity = min(1.0, intensity + 0.1)

        # Bonus for completing within time block
        if block.completed_on_time:
            intensity = min(1.0, intensity + 0.1)

        logger.debug(f"Calculated pride intensity: {intensity:.2f} for block {block.block_id}")

        return intensity

    async def emit_milestone_reward(
        self,
        user_id: str,
        milestone_description: str,
        blocks_completed: int
    ) -> RewardMessage:
        """
        Emit a special reward for completing a milestone (e.g., 5 blocks)

        Args:
            user_id: User who hit the milestone
            milestone_description: What milestone was reached
            blocks_completed: Number of blocks completed

        Returns:
            RewardMessage for milestone
        """
        logger.info(f"Emitting milestone reward for user {user_id}: {milestone_description}")

        milestone_templates = [
            f"🎯 Milestone! You've completed {blocks_completed} blocks. You're building serious momentum!",
            f"🚀 Achievement unlocked! {blocks_completed} blocks done. You're on a roll!",
            f"⭐ Impressive! {blocks_completed} completions show you're making this happen!",
        ]

        reward_text = milestone_templates[blocks_completed % len(milestone_templates)]

        reward = RewardMessage(
            message_id=str(uuid.uuid4()),
            user_id=user_id,
            block_id="milestone",
            reward_text=reward_text,
            strength_referenced=None,
            identity_label_used="high achiever",
            template_used="milestone",
            personalization_elements=[str(blocks_completed), milestone_description],
            emitted_at=datetime.now()
        )

        self.emitted_rewards[reward.message_id] = reward

        return reward

    def get_user_rewards(self, user_id: str) -> List[RewardMessage]:
        """Get all rewards for a user"""
        return [r for r in self.emitted_rewards.values() if r.user_id == user_id]

    def get_reward_count(self, user_id: str) -> int:
        """Get total number of rewards emitted for user"""
        return self.reward_count_by_user.get(user_id, 0)
