"""
Scoping Agent Component

The "master planner" - recursively breaks down goals using the 80/20 principle
until reaching atomic blocks.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from loguru import logger

from ..interfaces import IScopingAgent
from ..models import (
    GoalPacket,
    ScopingSession,
    TaskComplexityLevel,
    GoalStatus,
)


class ScopingAgent(IScopingAgent):
    """
    Concrete implementation of Fractal 80/20 Scoping Agent

    Uses the 80/20 principle to recursively break down large goals into
    actionable atomic blocks. Each iteration identifies the 20% of effort
    that delivers 80% of value.
    """

    # Simple breakdown templates for common goal patterns
    BREAKDOWN_PATTERNS = {
        "learn": ["understand basics", "practice fundamentals", "apply to project"],
        "build": ["plan architecture", "implement core", "test & refine"],
        "write": ["outline structure", "draft content", "edit & polish"],
        "organize": ["assess current state", "create system", "implement & maintain"],
        "default": ["research & plan", "execute core work", "review & improve"],
    }

    def __init__(self):
        """Initialize Scoping Agent"""
        self.scoping_sessions = {}  # session_id -> ScopingSession
        logger.info("Scoping Agent initialized")

    async def scope_goal(
        self,
        goal: GoalPacket,
        target_complexity: TaskComplexityLevel = TaskComplexityLevel.ATOMIC
    ) -> ScopingSession:
        """
        Perform one scoping iteration on a goal

        Args:
            goal: The 100% goal to scope
            target_complexity: What level to scope down to

        Returns:
            ScopingSession documenting the scoping decision
        """
        logger.info(f"Scoping goal {goal.goal_id}: '{goal.description[:50]}...'")

        # Create scoping session
        session = ScopingSession(
            session_id=str(uuid.uuid4()),
            user_id=goal.user_id,
            input_goal=goal,
            target_complexity=target_complexity,
            achieved_complexity=goal.complexity_level,
            scoped_at=datetime.now()
        )

        # Identify the 80% win (20% of effort, 80% of value)
        eighty_win = await self.identify_80_win(goal)
        session.identified_80_win = eighty_win['description']
        session.value_effort_analysis = {
            'value_score': eighty_win['value_score'],
            'effort_score': eighty_win['effort_score'],
            'ratio': eighty_win['ratio']
        }

        # Reframe the 80% win as a new 100% goal
        output_goal = await self.reframe_as_100_percent(eighty_win, goal)
        session.output_goal = output_goal

        # The remaining 20% is deferred
        session.remaining_20 = f"Advanced aspects of: {goal.description}"

        # Determine if we've reached target complexity
        session.reached_target = output_goal.complexity_level == target_complexity
        session.completed_at = datetime.now()

        # Store session
        self.scoping_sessions[session.session_id] = session

        logger.info(
            f"Scoping session {session.session_id} complete: "
            f"{goal.complexity_level.value} → {output_goal.complexity_level.value}"
        )

        return session

    async def identify_80_win(self, goal: GoalPacket) -> Dict[str, Any]:
        """
        Identify the 20% of effort that delivers 80% of value

        Uses pattern matching and heuristics to identify the critical path.

        Args:
            goal: Goal to analyze

        Returns:
            Dictionary with identified 80% win and scores
        """
        logger.debug(f"Identifying 80% win for goal: '{goal.description[:50]}...'")

        # Detect pattern in goal description
        description_lower = goal.description.lower()
        pattern = "default"

        for key in self.BREAKDOWN_PATTERNS.keys():
            if key in description_lower:
                pattern = key
                break

        # Get breakdown steps for this pattern
        steps = self.BREAKDOWN_PATTERNS[pattern]

        # The first step is usually the 80% win (critical path)
        critical_step = steps[0]

        # Build the 80% win description
        if pattern == "default":
            eighty_win_desc = f"Core aspect of {goal.description}"
        else:
            eighty_win_desc = f"{critical_step.capitalize()}: {goal.description}"

        # Calculate scores (simplified heuristics)
        # The 80% win should have high value, moderate effort
        value_score = 0.8  # Delivers 80% of value
        effort_score = 0.2  # Requires only 20% of effort
        ratio = value_score / effort_score if effort_score > 0 else 0

        result = {
            'description': eighty_win_desc,
            'value_score': value_score,
            'effort_score': effort_score,
            'ratio': ratio,
            'pattern_used': pattern
        }

        logger.debug(f"Identified 80% win: '{eighty_win_desc}' (ratio: {ratio:.2f})")

        return result

    async def reframe_as_100_percent(
        self,
        eighty_percent_win: Dict[str, Any],
        parent_goal: GoalPacket
    ) -> GoalPacket:
        """
        Reframe the 80% win as a new 100% goal

        This is the core of the fractal scoping algorithm. The 80% win
        becomes the new 100% goal for the next iteration.

        Args:
            eighty_percent_win: The identified critical path
            parent_goal: Original goal this came from

        Returns:
            New GoalPacket at reduced complexity
        """
        logger.debug("Reframing 80% win as new 100% goal")

        # Reduce complexity level by one step
        # Complexity hierarchy: MEGA → MACRO → MINI → MICRO → ATOMIC
        current_complexity = parent_goal.complexity_level
        if current_complexity == TaskComplexityLevel.MEGA:
            new_complexity = TaskComplexityLevel.MACRO
        elif current_complexity == TaskComplexityLevel.MACRO:
            new_complexity = TaskComplexityLevel.MINI
        elif current_complexity == TaskComplexityLevel.MINI:
            new_complexity = TaskComplexityLevel.MICRO
        elif current_complexity == TaskComplexityLevel.MICRO:
            new_complexity = TaskComplexityLevel.ATOMIC
        else:  # Already atomic
            new_complexity = TaskComplexityLevel.ATOMIC

        # Create new goal packet
        new_goal = GoalPacket(
            goal_id=str(uuid.uuid4()),
            user_id=parent_goal.user_id,
            description=eighty_percent_win['description'],
            complexity_level=new_complexity,
            parent_goal_id=parent_goal.goal_id,
            scoping_iteration=parent_goal.scoping_iteration + 1,
            status=GoalStatus.PENDING,
            created_at=datetime.now(),

            # Inherit and adjust estimates
            estimated_value=eighty_percent_win['value_score'],
            estimated_effort=eighty_percent_win['effort_score'],
            value_effort_ratio=eighty_percent_win['ratio'],
        )

        # Update parent goal's children
        if not hasattr(parent_goal, 'child_goal_ids'):
            parent_goal.child_goal_ids = []
        parent_goal.child_goal_ids.append(new_goal.goal_id)

        logger.info(
            f"Created new goal {new_goal.goal_id} at {new_complexity.value} level "
            f"from parent {parent_goal.goal_id}"
        )

        return new_goal

    async def should_continue_scoping(self, goal: GoalPacket) -> bool:
        """
        Determine if goal needs further scoping

        Args:
            goal: Goal to check

        Returns:
            True if goal needs more scoping, False if atomic enough
        """
        # Continue scoping if not yet atomic
        if goal.complexity_level != TaskComplexityLevel.ATOMIC:
            logger.debug(f"Goal {goal.goal_id} needs scoping: {goal.complexity_level.value} → ATOMIC")
            return True

        # Check if effort is still too high for one block
        if goal.estimated_effort > 0.8:
            logger.debug(f"Goal {goal.goal_id} has high effort ({goal.estimated_effort:.2f}), needs scoping")
            return True

        logger.debug(f"Goal {goal.goal_id} is atomic enough")
        return False

    async def scope_to_atomic(self, goal: GoalPacket) -> list[GoalPacket]:
        """
        Recursively scope a goal down to atomic blocks

        Args:
            goal: Goal to scope

        Returns:
            List of atomic-level GoalPackets
        """
        logger.info(f"Scoping goal {goal.goal_id} to atomic level")

        atomic_goals = []
        current_goal = goal

        # Keep scoping until atomic
        max_iterations = 5  # Prevent infinite loops
        iteration = 0

        while await self.should_continue_scoping(current_goal) and iteration < max_iterations:
            session = await self.scope_goal(current_goal, TaskComplexityLevel.ATOMIC)
            current_goal = session.output_goal
            iteration += 1

            if current_goal.complexity_level == TaskComplexityLevel.ATOMIC:
                atomic_goals.append(current_goal)
                logger.debug(f"Reached atomic goal: {current_goal.goal_id}")
                break

        # If we didn't reach atomic after max iterations, include what we have
        if iteration >= max_iterations and current_goal.complexity_level != TaskComplexityLevel.ATOMIC:
            logger.warning(f"Max scoping iterations reached for goal {goal.goal_id}")
            atomic_goals.append(current_goal)

        logger.info(f"Scoped goal {goal.goal_id} into {len(atomic_goals)} atomic goal(s)")

        return atomic_goals

    def get_session(self, session_id: str) -> ScopingSession:
        """Retrieve a scoping session"""
        return self.scoping_sessions.get(session_id)
