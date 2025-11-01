"""
Momentum Loop Orchestrator Component

Coordinates the core WIN → AFFIRM → PIVOT → REFRAME → LAUNCH cycle.
This is the "heart" of the FFE system.

Phase 5.3 Enhancements:
- Full event-driven state machine
- State transition validation & guards
- Automatic state progression
- State persistence to disk
- Metrics tracking & analytics
- Error recovery & timeout handling
- State change hooks for component integration
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from enum import Enum
import json
import asyncio
from dataclasses import asdict
from loguru import logger

from ..component_interfaces import IMomentumLoopOrchestrator
from ..models import (
    MomentumLoopState,
    MomentumState,
    AtomicBlock,
    RewardMessage,
    BottleneckTask,
    StrengthType,
)


class EventType(Enum):
    """Events that trigger state transitions"""
    BLOCK_COMPLETED = "block_completed"
    REWARD_EMITTED = "reward_emitted"
    BOTTLENECK_CHECKED = "bottleneck_checked"
    REFRAME_COMPLETE = "reframe_complete"
    GROWTH_STARTED = "growth_started"
    GROWTH_COMPLETED = "growth_completed"
    TIMEOUT = "timeout"
    ERROR = "error"
    USER_ACTION = "user_action"


class MomentumLoopOrchestrator(IMomentumLoopOrchestrator):
    """
    Concrete implementation of Momentum Loop Orchestrator

    Coordinates all FFE components through the psychology-driven cycle:
    WIN (strength task) → AFFIRM (pride hit) → PIVOT (detect bottleneck)
    → REFRAME (via strength) → LAUNCH (growth task) → WIN (growth completed)
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize Momentum Loop Orchestrator

        Args:
            storage_dir: Directory for persisting loop state
        """
        # State storage
        self.active_loops: Dict[str, MomentumLoopState] = {}  # user_id -> MomentumLoopState
        self.loop_history: Dict[str, MomentumLoopState] = {}  # loop_id -> MomentumLoopState

        # Event system
        self.event_queue: List[Dict[str, Any]] = []
        self.event_handlers: Dict[MomentumState, Dict[EventType, Callable]] = self._init_event_handlers()

        # State change hooks (for component integration)
        self.state_change_hooks: List[Callable] = []

        # Persistence
        self.storage_dir = storage_dir or Path("./data/momentum_loops")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Valid state transitions (state machine guards)
        self.valid_transitions = {
            MomentumState.IDLE: [MomentumState.WIN_STRENGTH],
            MomentumState.WIN_STRENGTH: [MomentumState.AFFIRM_PRIDE, MomentumState.IDLE],
            MomentumState.AFFIRM_PRIDE: [MomentumState.PIVOT_DETECT, MomentumState.IDLE],
            MomentumState.PIVOT_DETECT: [MomentumState.REFRAME_STRENGTH, MomentumState.WIN_STRENGTH, MomentumState.IDLE],
            MomentumState.REFRAME_STRENGTH: [MomentumState.LAUNCH_GROWTH, MomentumState.IDLE],
            MomentumState.LAUNCH_GROWTH: [MomentumState.WIN_GROWTH, MomentumState.IDLE],
            MomentumState.WIN_GROWTH: [MomentumState.WIN_STRENGTH, MomentumState.IDLE],
        }

        # Metrics tracking
        self.metrics = {
            "total_loops_started": 0,
            "total_cycles_completed": 0,
            "total_growth_wins": 0,
            "average_cycle_duration_seconds": 0.0,
            "state_transition_counts": {},
            "error_count": 0,
        }

        # Timeout configuration (in seconds)
        self.state_timeouts = {
            MomentumState.WIN_STRENGTH: 7200,  # 2 hours for strength task
            MomentumState.AFFIRM_PRIDE: 60,  # 1 minute for reward delivery
            MomentumState.PIVOT_DETECT: 300,  # 5 minutes for bottleneck detection
            MomentumState.REFRAME_STRENGTH: 300,  # 5 minutes for reframing
            MomentumState.LAUNCH_GROWTH: 60,  # 1 minute to launch
            MomentumState.WIN_GROWTH: 14400,  # 4 hours for growth task
        }

        # Load persisted loops
        self._load_active_loops()

        logger.info(f"Momentum Loop Orchestrator initialized with storage at {self.storage_dir}")

    def _init_event_handlers(self) -> Dict[MomentumState, Dict[EventType, Callable]]:
        """Initialize event handler mappings for each state"""
        return {
            MomentumState.WIN_STRENGTH: {
                EventType.BLOCK_COMPLETED: self.handle_win_strength,
            },
            MomentumState.AFFIRM_PRIDE: {
                EventType.REWARD_EMITTED: self.handle_affirm_pride,
            },
            MomentumState.PIVOT_DETECT: {
                EventType.BOTTLENECK_CHECKED: self.handle_pivot_detect,
            },
            MomentumState.REFRAME_STRENGTH: {
                EventType.REFRAME_COMPLETE: self.handle_reframe_strength,
            },
            MomentumState.LAUNCH_GROWTH: {
                EventType.GROWTH_STARTED: self.handle_launch_growth,
            },
            MomentumState.WIN_GROWTH: {
                EventType.GROWTH_COMPLETED: self.handle_win_growth,
            },
        }

    def _load_active_loops(self) -> None:
        """Load active loops from disk"""
        active_loops_file = self.storage_dir / "active_loops.json"
        if not active_loops_file.exists():
            return

        try:
            with open(active_loops_file, 'r') as f:
                data = json.load(f)

            for user_id, loop_data in data.items():
                # Reconstruct MomentumLoopState from dict
                loop_state = self._deserialize_loop_state(loop_data)
                self.active_loops[user_id] = loop_state

            logger.info(f"Loaded {len(self.active_loops)} active loops from disk")

        except Exception as e:
            logger.error(f"Failed to load active loops: {e}")

    async def _persist_active_loops(self) -> None:
        """Persist active loops to disk"""
        active_loops_file = self.storage_dir / "active_loops.json"

        data = {}
        for user_id, loop_state in self.active_loops.items():
            data[user_id] = self._serialize_loop_state(loop_state)

        try:
            with open(active_loops_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"Persisted {len(self.active_loops)} active loops")

        except Exception as e:
            logger.error(f"Failed to persist active loops: {e}")

    def _serialize_loop_state(self, loop_state: MomentumLoopState) -> Dict[str, Any]:
        """Convert MomentumLoopState to JSON-serializable dict"""
        data = asdict(loop_state)
        # Convert enums to strings
        data['current_state'] = loop_state.current_state.value
        if loop_state.previous_state:
            data['previous_state'] = loop_state.previous_state.value
        if loop_state.strength_used:
            data['strength_used'] = loop_state.strength_used.value
        return data

    def _deserialize_loop_state(self, data: Dict[str, Any]) -> MomentumLoopState:
        """Convert dict to MomentumLoopState"""
        # Convert string states back to enums
        data['current_state'] = MomentumState(data['current_state'])
        if data.get('previous_state'):
            data['previous_state'] = MomentumState(data['previous_state'])

        # Convert datetime strings
        for field in ['started_at', 'last_state_change']:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])

        return MomentumLoopState(**data)

    def _validate_transition(
        self,
        current_state: MomentumState,
        next_state: MomentumState
    ) -> bool:
        """Validate if state transition is allowed"""
        valid_next_states = self.valid_transitions.get(current_state, [])

        if next_state not in valid_next_states:
            logger.warning(
                f"Invalid transition: {current_state.value} → {next_state.value}. "
                f"Valid transitions: {[s.value for s in valid_next_states]}"
            )
            return False

        return True

    async def _notify_state_change(
        self,
        loop_state: MomentumLoopState,
        old_state: MomentumState,
        new_state: MomentumState
    ) -> None:
        """Notify registered hooks about state change"""
        for hook in self.state_change_hooks:
            try:
                await hook(loop_state, old_state, new_state)
            except Exception as e:
                logger.error(f"State change hook failed: {e}")

    def register_state_change_hook(self, hook: Callable) -> None:
        """Register a callback to be notified of state changes"""
        self.state_change_hooks.append(hook)
        logger.debug(f"Registered state change hook: {hook.__name__}")

    async def _update_metrics(
        self,
        event_type: str,
        loop_state: Optional[MomentumLoopState] = None
    ) -> None:
        """Update metrics for analytics"""
        transition_key = f"{loop_state.previous_state.value if loop_state and loop_state.previous_state else 'none'} → {loop_state.current_state.value if loop_state else 'unknown'}"

        if transition_key not in self.metrics["state_transition_counts"]:
            self.metrics["state_transition_counts"][transition_key] = 0

        self.metrics["state_transition_counts"][transition_key] += 1

        # Update specific metrics based on event
        if event_type == "loop_started":
            self.metrics["total_loops_started"] += 1
        elif event_type == "cycle_completed":
            self.metrics["total_cycles_completed"] += 1
        elif event_type == "growth_win":
            self.metrics["total_growth_wins"] += 1

    async def check_timeouts(self) -> List[str]:
        """Check for timed-out states and return affected user IDs"""
        timed_out_users = []
        now = datetime.now()

        for user_id, loop_state in self.active_loops.items():
            timeout_seconds = self.state_timeouts.get(loop_state.current_state, 3600)
            time_in_state = (now - loop_state.last_state_change).total_seconds()

            if time_in_state > timeout_seconds:
                logger.warning(
                    f"Loop {loop_state.loop_id} timed out in {loop_state.current_state.value} "
                    f"({time_in_state:.0f}s > {timeout_seconds}s)"
                )
                timed_out_users.append(user_id)

                # Auto-transition to IDLE on timeout
                await self._handle_timeout(loop_state)

        return timed_out_users

    async def _handle_timeout(self, loop_state: MomentumLoopState) -> None:
        """Handle state timeout"""
        logger.info(f"Handling timeout for loop {loop_state.loop_id}")

        old_state = loop_state.current_state
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.IDLE
        loop_state.last_state_change = datetime.now()

        await self._notify_state_change(loop_state, old_state, MomentumState.IDLE)
        await self._persist_active_loops()

    async def process_event(
        self,
        user_id: str,
        event_type: EventType,
        event_data: Dict[str, Any]
    ) -> Optional[MomentumLoopState]:
        """
        Process an event for a user's momentum loop

        Args:
            user_id: User ID
            event_type: Type of event
            event_data: Event payload

        Returns:
            Updated loop state or None if no active loop
        """
        loop_state = self.active_loops.get(user_id)

        if not loop_state:
            logger.debug(f"No active loop for user {user_id}, ignoring event {event_type.value}")
            return None

        current_state = loop_state.current_state

        # Get handler for this state + event combination
        handlers = self.event_handlers.get(current_state, {})
        handler = handlers.get(event_type)

        if not handler:
            logger.warning(
                f"No handler for {event_type.value} in state {current_state.value}"
            )
            return loop_state

        try:
            # Call handler
            logger.debug(f"Processing {event_type.value} in {current_state.value}")

            # Handlers expect different parameters based on event type
            if event_type == EventType.BLOCK_COMPLETED:
                loop_state = await handler(loop_state, event_data.get('completed_block'))
            elif event_type == EventType.REWARD_EMITTED:
                loop_state = await handler(loop_state, event_data.get('reward'))
            elif event_type == EventType.BOTTLENECK_CHECKED:
                loop_state = await handler(loop_state, event_data.get('bottleneck'))
            elif event_type == EventType.REFRAME_COMPLETE:
                loop_state = await handler(loop_state, event_data.get('reframed_block'))
            elif event_type == EventType.GROWTH_STARTED:
                loop_state = await handler(loop_state, event_data.get('growth_block'))
            elif event_type == EventType.GROWTH_COMPLETED:
                loop_state = await handler(loop_state, event_data.get('completed_growth'))

            # Persist after state change
            await self._persist_active_loops()

            # Update metrics
            await self._update_metrics(event_type.value, loop_state)

            return loop_state

        except Exception as e:
            logger.error(f"Error processing event {event_type.value}: {e}")
            self.metrics["error_count"] += 1
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get momentum loop metrics"""
        return self.metrics.copy()

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

        # Persist
        await self._persist_active_loops()

        # Update metrics
        await self._update_metrics("loop_started", loop_state)

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

        # Validate transition
        if not self._validate_transition(loop_state.current_state, MomentumState.AFFIRM_PRIDE):
            logger.error(f"Cannot transition from {loop_state.current_state.value} to AFFIRM_PRIDE")
            return loop_state

        # Update state
        old_state = loop_state.current_state
        loop_state.strength_win_completed = True
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.AFFIRM_PRIDE
        loop_state.last_state_change = datetime.now()

        # Notify hooks
        await self._notify_state_change(loop_state, old_state, MomentumState.AFFIRM_PRIDE)

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

        # Validate transition
        if not self._validate_transition(loop_state.current_state, MomentumState.PIVOT_DETECT):
            logger.error(f"Cannot transition from {loop_state.current_state.value} to PIVOT_DETECT")
            return loop_state

        # Record pride hit
        old_state = loop_state.current_state
        loop_state.pride_hit_received = True
        loop_state.affirmation_text = reward.reward_text
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.PIVOT_DETECT
        loop_state.last_state_change = datetime.now()

        # Notify hooks
        await self._notify_state_change(loop_state, old_state, MomentumState.PIVOT_DETECT)

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

        old_state = loop_state.current_state
        loop_state.previous_state = loop_state.current_state

        if bottleneck:
            # Bottleneck found → REFRAME
            next_state = MomentumState.REFRAME_STRENGTH

            # Validate transition
            if not self._validate_transition(loop_state.current_state, next_state):
                logger.error(f"Cannot transition to REFRAME_STRENGTH")
                return loop_state

            logger.info(f"Bottleneck detected: {bottleneck.task_description[:50]}...")
            loop_state.bottleneck_detected = True
            loop_state.bottleneck_task_id = bottleneck.bottleneck_id
            loop_state.current_state = next_state
            logger.debug(f"Transitioned to REFRAME_STRENGTH state")

            # Notify hooks
            await self._notify_state_change(loop_state, old_state, next_state)
        else:
            # No bottleneck → Start new cycle
            next_state = MomentumState.WIN_STRENGTH

            # Validate transition
            if not self._validate_transition(loop_state.current_state, next_state):
                logger.error(f"Cannot transition to WIN_STRENGTH")
                return loop_state

            logger.info(f"No bottleneck detected, starting new cycle")
            loop_state.bottleneck_detected = False
            loop_state.current_state = next_state
            loop_state.cycle_count += 1
            logger.debug(f"Transitioned back to WIN_STRENGTH (cycle {loop_state.cycle_count})")

            # Notify hooks
            await self._notify_state_change(loop_state, old_state, next_state)

            # Update metrics for cycle completion
            await self._update_metrics("cycle_completed", loop_state)

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

        # Validate transition
        if not self._validate_transition(loop_state.current_state, MomentumState.LAUNCH_GROWTH):
            logger.error(f"Cannot transition to LAUNCH_GROWTH")
            return loop_state

        # Record reframed task
        old_state = loop_state.current_state
        loop_state.growth_task_block_id = reframed_block.block_id
        loop_state.bottleneck_reframed = True
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.LAUNCH_GROWTH
        loop_state.last_state_change = datetime.now()

        # Notify hooks
        await self._notify_state_change(loop_state, old_state, MomentumState.LAUNCH_GROWTH)

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

        # Validate transition
        if not self._validate_transition(loop_state.current_state, MomentumState.WIN_GROWTH):
            logger.error(f"Cannot transition to WIN_GROWTH")
            return loop_state

        # Update state
        old_state = loop_state.current_state
        loop_state.growth_task_launched = True
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.WIN_GROWTH
        loop_state.last_state_change = datetime.now()

        # Notify hooks
        await self._notify_state_change(loop_state, old_state, MomentumState.WIN_GROWTH)

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

        # Validate transition
        if not self._validate_transition(loop_state.current_state, MomentumState.WIN_STRENGTH):
            logger.error(f"Cannot transition to WIN_STRENGTH")
            return loop_state

        # Update state
        old_state = loop_state.current_state
        loop_state.growth_win_completed = True
        loop_state.previous_state = loop_state.current_state
        loop_state.current_state = MomentumState.WIN_STRENGTH
        loop_state.cycle_count += 1
        loop_state.last_state_change = datetime.now()

        # Notify hooks
        await self._notify_state_change(loop_state, old_state, MomentumState.WIN_STRENGTH)

        # Update metrics
        await self._update_metrics("growth_win", loop_state)
        await self._update_metrics("cycle_completed", loop_state)

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
