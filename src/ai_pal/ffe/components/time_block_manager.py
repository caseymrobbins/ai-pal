"""
Time-Block Manager Component

Aligns scoped goals with user's time and energy. Implements both
macro-scale (5-Block Rule) and micro-scale (Atomic Blocks).
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger

from ..interfaces import ITimeBlockManager
from ..models import (
    GoalPacket,
    AtomicBlock,
    FiveBlockPlan,
    TimeBlockSize,
    TaskComplexityLevel,
)


class TimeBlockManager(ITimeBlockManager):
    """
    Concrete implementation of Time-Block Manager

    Creates 5-Block plans for macro goals and atomic time blocks
    for immediate execution. Enforces the 5-Block Stop rule for autonomy.
    """

    def __init__(self):
        """Initialize Time-Block Manager"""
        self.five_block_plans = {}  # plan_id -> FiveBlockPlan
        self.atomic_blocks = {}  # block_id -> AtomicBlock
        logger.info("Time-Block Manager initialized")

    async def create_five_block_plan(
        self,
        user_id: str,
        macro_goal: GoalPacket,
        total_months: int = 5
    ) -> FiveBlockPlan:
        """
        Create a 5-Block plan for a multi-month goal

        Args:
            user_id: User creating the plan
            macro_goal: The large goal to plan
            total_months: Total duration (default 5)

        Returns:
            FiveBlockPlan with 5 equal blocks
        """
        logger.info(f"Creating 5-Block plan for user {user_id}, goal: '{macro_goal.description[:50]}...'")

        # Calculate block duration
        block_duration = total_months // 5
        if block_duration < 1:
            block_duration = 1
            total_months = 5
            logger.warning(f"Adjusted total_months to minimum of 5 months")

        # Create 5 blocks
        blocks = []
        stop_points = []

        start_date = datetime.now()
        for i in range(5):
            block_start = start_date + timedelta(days=30 * block_duration * i)
            block_end = start_date + timedelta(days=30 * block_duration * (i + 1))

            blocks.append({
                "block_number": i + 1,
                "description": f"Block {i + 1} of 5: {macro_goal.description}",
                "start_date": block_start.isoformat(),
                "end_date": block_end.isoformat(),
                "status": "pending"
            })

            # Stop point at end of each block
            stop_points.append(block_end)

        # Create plan
        plan = FiveBlockPlan(
            plan_id=str(uuid.uuid4()),
            user_id=user_id,
            goal_id=macro_goal.goal_id,
            total_duration_months=total_months,
            block_duration_months=block_duration,
            blocks=blocks,
            current_block_index=0,
            stop_points=stop_points,
            user_confirmed_continuation=[False] * 5,
            blocks_completed=0,
            plan_started=datetime.now()
        )

        # Store plan
        self.five_block_plans[plan.plan_id] = plan

        logger.info(f"Created 5-Block plan {plan.plan_id} with {total_months} month duration")

        return plan

    async def create_atomic_block(
        self,
        user_id: str,
        goal: GoalPacket,
        preferred_duration: Optional[TimeBlockSize] = None
    ) -> AtomicBlock:
        """
        Create an atomic time block from a scoped goal

        Args:
            user_id: User the block is for
            goal: The atomic-level goal
            preferred_duration: User's preferred block size

        Returns:
            AtomicBlock ready for execution
        """
        logger.debug(f"Creating atomic block for goal {goal.goal_id}")

        # Determine time block size
        if preferred_duration:
            block_size = preferred_duration
        else:
            block_size = await self.scale_to_user_context(user_id, goal)

        # Create atomic block
        block = AtomicBlock(
            block_id=str(uuid.uuid4()),
            user_id=user_id,
            goal_id=goal.goal_id,
            title=goal.description[:100],  # Keep title concise
            description=goal.description,
            time_block_size=block_size,
            original_description=goal.description,
            strength_reframe=None,  # Will be set by StrengthAmplifier
            using_strength=None,
            scheduled_start=None,
            actual_start=None,
            actual_duration_minutes=None,
            completed=False,
            completion_time=None,
            quality_score=0.0,
            reward_emitted=False,
            reward_text=None,
            pride_hit_intensity=0.0,
            triggered_momentum_loop=False,
            led_to_growth_task=None,
        )

        # Store block
        self.atomic_blocks[block.block_id] = block

        logger.info(f"Created atomic block {block.block_id} with {block_size.value}min duration")

        return block

    async def scale_to_user_context(
        self,
        user_id: str,
        goal: GoalPacket
    ) -> TimeBlockSize:
        """
        Determine appropriate time block size based on user context

        Considers: energy levels, available time, task complexity

        Args:
            user_id: User to scale for
            goal: Goal to create block for

        Returns:
            Recommended TimeBlockSize
        """
        # Simple heuristic based on complexity and estimated effort
        complexity = goal.complexity_level
        effort = goal.estimated_effort

        # Map complexity to time blocks
        if complexity == TaskComplexityLevel.ATOMIC:
            # Atomic tasks -> shorter blocks
            if effort < 0.3:
                block_size = TimeBlockSize.SPRINT_15
            else:
                block_size = TimeBlockSize.BLOCK_30

        elif complexity == TaskComplexityLevel.SIMPLE:
            # Simple tasks -> 30-60 min blocks
            if effort < 0.5:
                block_size = TimeBlockSize.BLOCK_30
            else:
                block_size = TimeBlockSize.BLOCK_60

        elif complexity in [TaskComplexityLevel.MODERATE, TaskComplexityLevel.COMPLEX]:
            # Complex tasks -> longer blocks
            if effort < 0.5:
                block_size = TimeBlockSize.BLOCK_60
            else:
                block_size = TimeBlockSize.BLOCK_90

        else:  # MACRO
            # Macro goals shouldn't be atomic blocks
            block_size = TimeBlockSize.BLOCK_90
            logger.warning(f"Macro goal {goal.goal_id} being converted to atomic block - should be scoped first")

        logger.debug(
            f"Scaled goal {goal.goal_id} (complexity: {complexity.value}, effort: {effort:.2f}) "
            f"to {block_size.value}min block"
        )

        return block_size

    async def check_five_block_stop(
        self,
        plan: FiveBlockPlan,
        block_index: int
    ) -> bool:
        """
        Check if 5-Block Stop rule should trigger (autonomy enforcement)

        The 5-Block Stop rule enforces user autonomy by prompting the user
        to reassess after each block. This prevents the system from being
        extractive or creating dependency.

        Args:
            plan: The 5-Block plan
            block_index: Which block just completed (0-4)

        Returns:
            True if user should be prompted to reassess
        """
        # Always stop at the end of each block
        if block_index >= 0 and block_index < len(plan.blocks):
            logger.info(
                f"5-Block Stop triggered for plan {plan.plan_id}, "
                f"block {block_index + 1}/5 completed"
            )
            return True

        return False

    async def confirm_continuation(
        self,
        plan_id: str,
        block_index: int,
        user_wants_to_continue: bool
    ) -> FiveBlockPlan:
        """
        Record user's decision to continue or stop after a block

        Args:
            plan_id: ID of the 5-Block plan
            block_index: Which block was just completed
            user_wants_to_continue: Did user choose to continue?

        Returns:
            Updated FiveBlockPlan
        """
        plan = self.five_block_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # Record user's decision
        if block_index < len(plan.user_confirmed_continuation):
            plan.user_confirmed_continuation[block_index] = user_wants_to_continue

        # Update block status
        if block_index < len(plan.blocks):
            plan.blocks[block_index]["status"] = "completed"
            plan.blocks_completed = block_index + 1

        # Update current block index
        if user_wants_to_continue and block_index < 4:
            plan.current_block_index = block_index + 1
            logger.info(f"User confirmed continuation, moving to block {plan.current_block_index + 1}")
        else:
            logger.info(f"User chose to stop or plan completed")

        return plan

    def get_plan(self, plan_id: str) -> Optional[FiveBlockPlan]:
        """Retrieve a 5-Block plan"""
        return self.five_block_plans.get(plan_id)

    def get_block(self, block_id: str) -> Optional[AtomicBlock]:
        """Retrieve an atomic block"""
        return self.atomic_blocks.get(block_id)

    def get_user_blocks(self, user_id: str) -> list[AtomicBlock]:
        """Get all atomic blocks for a user"""
        return [b for b in self.atomic_blocks.values() if b.user_id == user_id]
