"""
Momentum Loop Orchestrator Component

Coordinates the core WIN → AFFIRM → PIVOT → REFRAME → LAUNCH cycle.
This is the "heart" of the FFE system.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

from ..interfaces import IMomentumLoopOrchestrator
from ..models import (
    MomentumLoopState,
    MomentumState,
    AtomicBlock,
    RewardMessage,
    BottleneckTask,
)


class MomentumLoopOrchestrator(IMomentumLoopOrchestrator):
    """
    Concrete implementation of Momentum Loop Orchestrator

    Coordinates all FFE components through the psychology-driven cycle:
    WIN (strength task) → AFFIRM (pride hit) → PIVOT (detect bottleneck)
    → REFRAME (via strength) → LAUNCH (growth task) → WIN (growth completed)
    """

    def __init__(self):
        """Initialize Momentum Loop Orchestrator"""
        self.active_loops = {}  # user_id -> MomentumLoopState
        self.loop_history = {}  # loop_id -> MomentumLoopState
        logger.info("Momentum Loop Orchestrator initialized")

    async def start_loop(
        self,
        user_id: str,
        strength_task: AtomicBlock
    ) -> MomentumLoopState:
        """
        Start a new momentum loop with a strength-based task

        Args:
            user_id: User starting the loop
            strength_task: The initial strength task

        Returns:
            New MomentumLoopState
        """
        logger.info(f"Starting momentum loop for user {user_id} with task {strength_task.block_id}")

        # Create new loop state
        loop_state = MomentumLoopState(
            user_id=user_id,
            current_state=MomentumState.WIN_STRENGTH,
            previous_state=MomentumState.IDLE,
            cycle_count=0,
            started_at=datetime.now(),
            last_state_change=datetime.now(),
            strength_task_block_id=strength_task.block_id,
            strength_used=strength_task.using_strength if hasattr(strength_task, 'using_strength') else None,
            strength_win_completed=False,
        )

        # Set as active loop
        self.active_loops[user_id] = loop_state

        logger.info(f"Momentum loop {loop_state.loop_id} started in WIN_STRENGTH state")

        return loop_state

    async def advance_state(
        self,
        loop_state: MomentumLoopState,
        event: Dict[str, Any]
    ) -> MomentumLoopState:
        """
        Advance the momentum loop to the next state

        Args:
            loop_state: Current loop state
            event: Event triggering state change

        Returns:
            Updated loop state
        """
        current = loop_state.current_state
        event_type = event.get('type')

        logger.debug(
            f"Advancing loop {loop_state.loop_id} from {current.value} "
            f"on event {event_type}"
        )

        # State transition logic
        if current == MomentumState.WIN_STRENGTH and event_type == 'block_completed':
            # WIN → AFFIRM
            loop_state = await self.handle_win_strength(
                loop_state,
                event.get('completed_block')
            )

        elif current == MomentumState.AFFIRM_PRIDE and event_type == 'reward_emitted':
            # AFFIRM → PIVOT
            loop_state = await self.handle_affirm_pride(
                loop_state,
                event.get('reward')
            )

        elif current == MomentumState.PIVOT_DETECT and event_type == 'bottleneck_checked':
            # PIVOT → REFRAME (if bottleneck found) or WIN (new cycle)
            loop_state = await self.handle_pivot_detect(
                loop_state,
                event.get('bottleneck')
            )

        elif current == MomentumState.REFRAME_STRENGTH and event_type == 'reframe_complete':
            # REFRAME → LAUNCH
            loop_state = await self.handle_reframe_strength(
                loop_state,
                event.get('reframed_block')
            )

        elif current == MomentumState.LAUNCH_GROWTH and event_type == 'growth_started':
            # LAUNCH → WIN_GROWTH
            loop_state = await self.handle_launch_growth(
                loop_state,
                event.get('growth_block')
            )

        elif current == MomentumState.WIN_GROWTH and event_type == 'growth_completed':
            # WIN_GROWTH → WIN_STRENGTH (new cycle with strength task)
            loop_state = await self.handle_win_growth(
                loop_state,
                event.get('completed_growth')
            )

        else:
            logger.warning(
                f"No state transition defined for {current.value} + {event_type}"
            )

        return loop_state

    async def handle_win_strength(
        self,
        loop_state: MomentumLoopState,
        completed_block: AtomicBlock
    ) -> MomentumLoopState:
        """
        Handle completion of strength task (WIN_STRENGTH → AFFIRM_PRIDE)

        Args:
            loop_state: Current loop state
            completed_block: The completed strength-based block

        Returns:
            Updated loop state
        """
        logger.info(f"WIN_STRENGTH completed for loop {loop_state.loop_id}")

        # Update state
        loop_state.strength_win_completed = True
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.AFFIRM_PRIDE
        loop_state.last_state_change = datetime.now()

        logger.debug(f"Transitioned to AFFIRM_PRIDE state")

        return loop_state

    async def handle_affirm_pride(
        self,
        loop_state: MomentumLoopState,
        reward: RewardMessage
    ) -> MomentumLoopState:
        """
        Handle pride affirmation (AFFIRM_PRIDE → PIVOT_DETECT)

        Args:
            loop_state: Current loop state
            reward: The reward message delivered

        Returns:
            Updated loop state
        """
        logger.info(f"AFFIRM_PRIDE delivered for loop {loop_state.loop_id}")

        # Record pride hit
        loop_state.pride_hit_received = True
        loop_state.affirmation_text = reward.reward_text
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.PIVOT_DETECT
        loop_state.last_state_change = datetime.now()

        logger.debug(f"Transitioned to PIVOT_DETECT state")

        return loop_state

    async def handle_pivot_detect(
        self,
        loop_state: MomentumLoopState,
        bottleneck: Optional[BottleneckTask]
    ) -> MomentumLoopState:
        """
        Handle bottleneck detection (PIVOT_DETECT → REFRAME_STRENGTH or back to WIN_STRENGTH)

        Args:
            loop_state: Current loop state
            bottleneck: Detected bottleneck (if any)

        Returns:
            Updated loop state
        """
        logger.info(f"PIVOT_DETECT checking for bottlenecks in loop {loop_state.loop_id}")

        loop_state.previous_state = loop_state.current_state

        if bottleneck:
            # Bottleneck found → REFRAME
            logger.info(f"Bottleneck detected: {bottleneck.task_description[:50]}...")
            loop_state.bottleneck_detected = True
            loop_state.bottleneck_task_id = bottleneck.bottleneck_id
            loop_state.current_state = MomentumState.REFRAME_STRENGTH
            logger.debug(f"Transitioned to REFRAME_STRENGTH state")
        else:
            # No bottleneck → Start new cycle
            logger.info(f"No bottleneck detected, starting new cycle")
            loop_state.bottleneck_detected = False
            loop_state.current_state = MomentumState.WIN_STRENGTH
            loop_state.cycle_count += 1
            logger.debug(f"Transitioned back to WIN_STRENGTH (cycle {loop_state.cycle_count})")

        loop_state.last_state_change = datetime.now()

        return loop_state

    async def handle_reframe_strength(
        self,
        loop_state: MomentumLoopState,
        reframed_block: AtomicBlock
    ) -> MomentumLoopState:
        """
        Handle strength-based reframing (REFRAME_STRENGTH → LAUNCH_GROWTH)

        Args:
            loop_state: Current loop state
            reframed_block: The reframed bottleneck as atomic block

        Returns:
            Updated loop state
        """
        logger.info(f"REFRAME_STRENGTH complete for loop {loop_state.loop_id}")

        # Record reframed task
        loop_state.growth_task_block_id = reframed_block.block_id
        loop_state.bottleneck_reframed = True
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.LAUNCH_GROWTH
        loop_state.last_state_change = datetime.now()

        logger.debug(f"Transitioned to LAUNCH_GROWTH state")

        return loop_state

    async def handle_launch_growth(
        self,
        loop_state: MomentumLoopState,
        growth_block: AtomicBlock
    ) -> MomentumLoopState:
        """
        Handle growth task launch (LAUNCH_GROWTH → WIN_GROWTH)

        Args:
            loop_state: Current loop state
            growth_block: The growth task being started

        Returns:
            Updated loop state
        """
        logger.info(f"LAUNCH_GROWTH initiated for loop {loop_state.loop_id}")

        # Update state
        loop_state.growth_task_launched = True
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.WIN_GROWTH
        loop_state.last_state_change = datetime.now()

        logger.debug(f"Transitioned to WIN_GROWTH state")

        return loop_state

    async def handle_win_growth(
        self,
        loop_state: MomentumLoopState,
        completed_growth: AtomicBlock
    ) -> MomentumLoopState:
        """
        Handle growth task completion (WIN_GROWTH → WIN_STRENGTH new cycle)

        Args:
            loop_state: Current loop state
            completed_growth: The completed growth task

        Returns:
            Updated loop state
        """
        logger.info(f"WIN_GROWTH complete for loop {loop_state.loop_id}")

        # Update state
        loop_state.growth_win_completed = True
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.WIN_STRENGTH
        loop_state.cycle_count += 1
        loop_state.last_state_change = datetime.now()

        logger.info(f"Growth cycle complete! Starting new cycle (cycle {loop_state.cycle_count})")

        return loop_state

    def get_active_loop(self, user_id: str) -> Optional[MomentumLoopState]:
        """Get the active momentum loop for a user"""
        return self.active_loops.get(user_id)

    def get_loop(self, loop_id: str) -> Optional[MomentumLoopState]:
        """Retrieve a loop from history"""
        return self.loop_history.get(loop_id)

    async def pause_loop(self, user_id: str) -> MomentumLoopState:
        """Pause active loop for a user"""
        loop = self.active_loops.get(user_id)
        if loop:
            logger.info(f"Pausing loop {loop.loop_id} for user {user_id}")
            loop.previous_state = loop.current_state
            loop.current_state = MomentumState.IDLE
            # Move to history
            self.loop_history[loop.loop_id] = loop
            del self.active_loops[user_id]
        return loop

    async def resume_loop(self, loop_id: str) -> MomentumLoopState:
        """Resume a paused loop"""
        loop = self.loop_history.get(loop_id)
        if loop:
            logger.info(f"Resuming loop {loop_id} for user {loop.user_id}")
            # Restore previous state
            loop.current_state = loop.previous_state or MomentumState.WIN_STRENGTH
            self.active_loops[loop.user_id] = loop
        return loop

    async def complete_loop(self, loop_state: MomentumLoopState) -> MomentumLoopState:
        """Complete a momentum loop cycle"""
        logger.info(f"Completing momentum loop {loop_state.loop_id}")
        loop_state.cycle_count += 1
        # Move to history
        self.loop_history[loop_state.loop_id] = loop_state
        if loop_state.user_id in self.active_loops:
            del self.active_loops[loop_state.user_id]
        return loop_state
