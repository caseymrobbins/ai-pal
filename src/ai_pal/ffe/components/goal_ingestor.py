"""
Goal Ingestor Component

The "front door" for all tasks - accepts macro-goals and ad-hoc tasks,
generates "100% Goal" packets ready for the Scoping Agent.
"""

import uuid
from datetime import datetime
from typing import Optional
from loguru import logger

from ..component_interfaces import IGoalIngestor
from ..models import GoalPacket, GoalStatus, TaskComplexityLevel


class GoalIngestor(IGoalIngestor):
    """
    Concrete implementation of Goal Ingestor

    Accepts goals from users or the personality module and packages
    them into standardized GoalPackets ready for fractal scoping.
    """

    def __init__(self):
        """Initialize Goal Ingestor"""
        self.ingested_goals = {}  # goal_id -> GoalPacket
        logger.info("Goal Ingestor initialized")

    async def ingest_macro_goal(
        self,
        user_id: str,
        goal_description: str,
        from_personality_module: bool = True
    ) -> GoalPacket:
        """
        Ingest a macro-level goal from Personality Module or user

        Args:
            user_id: User creating the goal
            goal_description: What the goal is
            from_personality_module: Was this from stored priorities?

        Returns:
            GoalPacket ready for scoping
        """
        logger.info(f"Ingesting macro goal for user {user_id}: '{goal_description[:50]}...'")

        goal = GoalPacket(
            goal_id=str(uuid.uuid4()),
            user_id=user_id,
            description=goal_description,
            complexity_level=TaskComplexityLevel.MACRO,
            status=GoalStatus.PENDING,
            created_at=datetime.now(),
            scoping_iteration=0,

            # Initial estimates (will be refined by Scoping Agent)
            estimated_value=0.7 if from_personality_module else 0.5,
            estimated_effort=0.5,  # Unknown at this stage
        )

        # Calculate initial value/effort ratio
        if goal.estimated_effort > 0:
            goal.value_effort_ratio = goal.estimated_value / goal.estimated_effort

        # Store goal
        self.ingested_goals[goal.goal_id] = goal

        logger.debug(f"Created goal packet {goal.goal_id} with value/effort ratio {goal.value_effort_ratio:.2f}")

        return goal

    async def ingest_adhoc_task(
        self,
        user_id: str,
        task_description: str,
        estimated_duration_minutes: Optional[int] = None
    ) -> GoalPacket:
        """
        Ingest an ad-hoc user task (e.g., "Clean the kitchen")

        Args:
            user_id: User creating the task
            task_description: What needs to be done
            estimated_duration_minutes: How long user thinks it will take

        Returns:
            GoalPacket ready for scoping
        """
        logger.info(f"Ingesting ad-hoc task for user {user_id}: '{task_description[:50]}...'")

        # Determine complexity based on estimated duration
        if estimated_duration_minutes:
            if estimated_duration_minutes <= 30:
                complexity = TaskComplexityLevel.ATOMIC
            elif estimated_duration_minutes <= 90:
                complexity = TaskComplexityLevel.SIMPLE
            elif estimated_duration_minutes <= 240:
                complexity = TaskComplexityLevel.MODERATE
            else:
                complexity = TaskComplexityLevel.COMPLEX
        else:
            # Default to SIMPLE for ad-hoc tasks
            complexity = TaskComplexityLevel.SIMPLE

        goal = GoalPacket(
            goal_id=str(uuid.uuid4()),
            user_id=user_id,
            description=task_description,
            complexity_level=complexity,
            status=GoalStatus.PENDING,
            created_at=datetime.now(),
            scoping_iteration=0,

            # Ad-hoc tasks have moderate value (not from deep priorities)
            estimated_value=0.4,
            estimated_effort=0.3 if complexity == TaskComplexityLevel.ATOMIC else 0.5,
        )

        # Calculate value/effort ratio
        if goal.estimated_effort > 0:
            goal.value_effort_ratio = goal.estimated_value / goal.estimated_effort

        # Store goal
        self.ingested_goals[goal.goal_id] = goal

        logger.debug(
            f"Created ad-hoc task packet {goal.goal_id} "
            f"(complexity: {complexity.value}, duration: {estimated_duration_minutes}min)"
        )

        return goal

    async def validate_goal(self, goal: GoalPacket) -> bool:
        """
        Validate that a goal is well-formed and actionable

        Args:
            goal: GoalPacket to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not goal.user_id:
            logger.warning(f"Goal {goal.goal_id} missing user_id")
            return False

        if not goal.description or len(goal.description.strip()) < 3:
            logger.warning(f"Goal {goal.goal_id} has invalid description")
            return False

        # Check value/effort are in valid range
        if goal.estimated_value < 0 or goal.estimated_value > 1:
            logger.warning(f"Goal {goal.goal_id} has invalid estimated_value: {goal.estimated_value}")
            return False

        if goal.estimated_effort < 0 or goal.estimated_effort > 1:
            logger.warning(f"Goal {goal.goal_id} has invalid estimated_effort: {goal.estimated_effort}")
            return False

        # Check IDs are valid UUIDs
        try:
            uuid.UUID(goal.goal_id)
        except ValueError:
            logger.warning(f"Goal has invalid UUID: {goal.goal_id}")
            return False

        logger.debug(f"Goal {goal.goal_id} validated successfully")
        return True

    def get_goal(self, goal_id: str) -> Optional[GoalPacket]:
        """Retrieve a previously ingested goal"""
        return self.ingested_goals.get(goal_id)

    def get_user_goals(self, user_id: str) -> list[GoalPacket]:
        """Get all goals for a specific user"""
        return [g for g in self.ingested_goals.values() if g.user_id == user_id]
