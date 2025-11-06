"""
FFE (Fractal Flow Engine) Background Tasks

Tasks for:
- Long-running goal planning and analysis
- 80/20 fractal scoping
- Task decomposition
- Block estimation and optimization
"""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime
import json

from celery import shared_task
from loguru import logger

from ai_pal.tasks.base_task import AIpalTask


class FFEGoalPlanningTask(AIpalTask):
    """Long-running FFE goal planning and decomposition"""

    name = "ai_pal.tasks.ffe_tasks.plan_goal"
    bind = True
    max_retries = 3
    default_retry_delay = 60

    def run(
        self,
        goal_id: str,
        user_id: str,
        goal_description: str,
        complexity_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Plan FFE goal with fractal decomposition

        Args:
            goal_id: Goal ID
            user_id: User ID
            goal_description: Goal description
            complexity_level: Goal complexity (simple, medium, complex)

        Returns:
            Planning result with atomic blocks
        """
        try:
            logger.info(f"Planning FFE goal {goal_id} for user {user_id}")

            return asyncio.run(
                self._plan_goal_async(goal_id, user_id, goal_description, complexity_level)
            )

        except Exception as exc:
            logger.error(f"Error planning FFE goal: {exc}")
            raise

    async def _plan_goal_async(
        self,
        goal_id: str,
        user_id: str,
        goal_description: str,
        complexity_level: str
    ) -> Dict[str, Any]:
        """
        Async implementation of goal planning

        Args:
            goal_id: Goal ID
            user_id: User ID
            goal_description: Goal description
            complexity_level: Complexity level

        Returns:
            Planning result
        """
        from ai_pal.storage.database import GoalRepository

        if not self.db_manager:
            raise RuntimeError("Database manager not configured")

        goal_repo = GoalRepository(self.db_manager)

        # Determine block count based on complexity
        block_counts = {
            "simple": 3,
            "medium": 5,
            "complex": 7
        }

        num_blocks = block_counts.get(complexity_level, 5)

        # Create estimated time blocks (example: even distribution)
        total_hours = 8 if complexity_level == "simple" else 16 if complexity_level == "medium" else 24
        time_per_block = total_hours / num_blocks

        atomic_blocks = []
        for i in range(num_blocks):
            atomic_blocks.append({
                "block_index": i + 1,
                "description": f"Step {i + 1}: {goal_description} - Block {i + 1}/{num_blocks}",
                "size": "medium",
                "estimated_minutes": int(time_per_block * 60)
            })

        result = {
            "goal_id": goal_id,
            "user_id": user_id,
            "status": "planned",
            "complexity_level": complexity_level,
            "atomic_blocks_count": len(atomic_blocks),
            "atomic_blocks": atomic_blocks,
            "total_estimated_minutes": sum(b["estimated_minutes"] for b in atomic_blocks),
            "planning_timestamp": datetime.now().isoformat()
        }

        logger.info(
            f"FFE goal planning complete: {len(atomic_blocks)} atomic blocks created"
        )

        return result


class FFEProgressTrackingTask(AIpalTask):
    """Track FFE goal progress and momentum"""

    name = "ai_pal.tasks.ffe_tasks.track_progress"
    bind = True
    max_retries = 2
    default_retry_delay = 30

    def run(
        self,
        goal_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Track progress on FFE goal

        Args:
            goal_id: Goal ID
            user_id: User ID

        Returns:
            Progress tracking result
        """
        try:
            logger.info(f"Tracking progress for goal {goal_id}")

            return asyncio.run(self._track_progress_async(goal_id, user_id))

        except Exception as exc:
            logger.error(f"Error tracking FFE progress: {exc}")
            raise

    async def _track_progress_async(
        self,
        goal_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Async implementation of progress tracking

        Args:
            goal_id: Goal ID
            user_id: User ID

        Returns:
            Progress tracking result
        """
        from ai_pal.storage.database import GoalRepository

        if not self.db_manager:
            raise RuntimeError("Database manager not configured")

        goal_repo = GoalRepository(self.db_manager)

        # Get goal details
        goals = await goal_repo.get_active_goals(user_id)
        goal = None
        for g in goals:
            if g["goal_id"] == goal_id:
                goal = g
                break

        if not goal:
            return {
                "goal_id": goal_id,
                "status": "not_found",
                "message": "Goal not found"
            }

        # Calculate progress metrics
        result = {
            "goal_id": goal_id,
            "user_id": user_id,
            "goal_description": goal["description"],
            "status": goal["status"],
            "progress_timestamp": datetime.now().isoformat()
        }

        logger.info(f"FFE progress tracking complete for goal {goal_id}")

        return result


# Celery task instances
@shared_task(bind=True, base=FFEGoalPlanningTask)
def plan_ffe_goal(
    self,
    goal_id: str,
    user_id: str,
    goal_description: str,
    complexity_level: str = "medium"
):
    """Plan FFE goal - Celery task wrapper"""
    return self.run(
        goal_id=goal_id,
        user_id=user_id,
        goal_description=goal_description,
        complexity_level=complexity_level
    )


@shared_task(bind=True, base=FFEProgressTrackingTask)
def track_ffe_progress(self, goal_id: str, user_id: str):
    """Track FFE progress - Celery task wrapper"""
    return self.run(goal_id=goal_id, user_id=user_id)
