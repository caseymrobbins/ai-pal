"""
Fractal Flow Engine (FFE) - Component Interfaces

Defines the contracts for all FFE components. Each component must
implement its corresponding interface to ensure proper integration
with the Momentum Loop and AC-AI framework.

Components:
1. IGoalIngestor - Task intake
2. IScopingAgent - 80/20 fractal scoping
3. ITimeBlockManager - Time/energy alignment
4. IStrengthAmplifier - Pride engine
5. IGrowthScaffold - Bottleneck detection
6. IRewardEmitter - Accomplishment rewards
7. IMomentumLoopOrchestrator - Core cycle coordination
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import (
    GoalPacket,
    AtomicBlock,
    PersonalityProfile,
    SignatureStrength,
    BottleneckTask,
    MomentumLoopState,
    RewardMessage,
    TimeBlockSize,
    TaskComplexityLevel,
    ScopingSession,
    FiveBlockPlan,
)


# ============================================================================
# CORE COMPONENT INTERFACES
# ============================================================================

class IGoalIngestor(ABC):
    """
    Interface for Goal Ingestor

    The "front door" for all tasks - accepts macro-goals and user tasks,
    generates "100% Goal" packets for the Scoping Agent.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def validate_goal(self, goal: GoalPacket) -> bool:
        """Validate that a goal is well-formed and actionable"""
        pass


class IScopingAgent(ABC):
    """
    Interface for Fractal 80/20 Scoping Agent

    The "master planner" - recursively breaks down goals using 80/20 principle
    until reaching atomic blocks.
    """

    @abstractmethod
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
        pass

    @abstractmethod
    async def identify_80_win(self, goal: GoalPacket) -> Dict[str, Any]:
        """
        Identify the 20% of effort that delivers 80% of value

        Returns:
            {
                'description': str,
                'value_score': float,
                'effort_score': float,
                'ratio': float
            }
        """
        pass

    @abstractmethod
    async def reframe_as_100_percent(
        self,
        eighty_percent_win: Dict[str, Any],
        parent_goal: GoalPacket
    ) -> GoalPacket:
        """
        Reframe the 80% win as a new 100% goal

        This is the core of the fractal scoping algorithm.
        """
        pass

    @abstractmethod
    async def should_continue_scoping(self, goal: GoalPacket) -> bool:
        """Determine if goal needs further scoping"""
        pass


class ITimeBlockManager(ABC):
    """
    Interface for Time-Block Manager

    Aligns scoped goals with user's time and energy. Implements both
    macro-scale (5-Block Rule) and micro-scale (Atomic Blocks).
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def scale_to_user_context(
        self,
        user_id: str,
        goal: GoalPacket
    ) -> TimeBlockSize:
        """
        Determine appropriate time block size based on user context

        Considers: energy levels, available time, task complexity
        """
        pass

    @abstractmethod
    async def check_five_block_stop(
        self,
        plan: FiveBlockPlan,
        block_index: int
    ) -> bool:
        """
        Check if 5-Block Stop rule should trigger (autonomy enforcement)

        Returns:
            True if user should be prompted to reassess
        """
        pass


class IStrengthAmplifier(ABC):
    """
    Interface for Signature Strength Amplifier

    The "pride engine" - transforms generic tasks into personal missions
    by leveraging user's core identity and strengths.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
            Custom reward message text
        """
        pass

    @abstractmethod
    async def match_task_to_strength(
        self,
        task_description: str,
        available_strengths: List[SignatureStrength]
    ) -> Optional[SignatureStrength]:
        """
        Find the best strength match for a task

        Returns:
            Matching strength, or None if no good match
        """
        pass


class IGrowthScaffold(ABC):
    """
    Interface for Growth Scaffold (Bottleneck Detector)

    The "subtle helper" - passively detects avoided tasks and queues them
    for strength-based reframing during momentum loops.
    """

    @abstractmethod
    async def detect_bottlenecks(
        self,
        user_id: str,
        lookback_days: int = 30
    ) -> List[BottleneckTask]:
        """
        Detect tasks the user avoids or struggles with

        Integrates with ARI Monitor to identify patterns.

        Args:
            user_id: User to analyze
            lookback_days: How far back to look

        Returns:
            List of detected bottleneck tasks
        """
        pass

    @abstractmethod
    async def queue_bottleneck(
        self,
        bottleneck: BottleneckTask
    ) -> None:
        """
        Queue a bottleneck task for future reframing

        Bottleneck will be activated when next pride hit occurs.
        """
        pass

    @abstractmethod
    async def get_queued_bottleneck(
        self,
        user_id: str,
        strength: Optional[SignatureStrength] = None
    ) -> Optional[BottleneckTask]:
        """
        Get the next bottleneck from queue

        Args:
            user_id: User to get bottleneck for
            strength: If provided, find bottleneck matchable to this strength

        Returns:
            Next bottleneck task, or None if queue empty
        """
        pass

    @abstractmethod
    async def activate_bottleneck_on_pride_hit(
        self,
        user_id: str,
        pride_hit_intensity: float
    ) -> Optional[BottleneckTask]:
        """
        Trigger bottleneck activation when pride hit occurs

        This is the key integration point with the Momentum Loop.

        Args:
            user_id: User who got pride hit
            pride_hit_intensity: How strong the pride response was

        Returns:
            Activated bottleneck, or None if conditions not met
        """
        pass


class IRewardEmitter(ABC):
    """
    Interface for Accomplishment Reward Emitter

    Delivers identity-affirming psychological rewards when atomic blocks
    are completed. Uses explicit language from Strength Amplifier.
    """

    @abstractmethod
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
        pass

    @abstractmethod
    async def calculate_pride_intensity(
        self,
        block: AtomicBlock,
        quality_score: float
    ) -> float:
        """
        Calculate how intense the "pride hit" should be

        Args:
            block: Completed block
            quality_score: User's self-assessed quality

        Returns:
            Pride intensity (0-1)
        """
        pass

    @abstractmethod
    async def get_reward_template(
        self,
        strength_type: Optional[str] = None,
        is_growth_task: bool = False
    ) -> str:
        """
        Get appropriate reward message template

        Args:
            strength_type: Type of strength used
            is_growth_task: Was this a bottleneck/growth task?

        Returns:
            Reward template string
        """
        pass


class IMomentumLoopOrchestrator(ABC):
    """
    Interface for Momentum Loop Orchestrator

    Coordinates the core WIN → AFFIRM → PIVOT → REFRAME → LAUNCH cycle.
    This is the "heart" of the FFE system.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def handle_win_strength(
        self,
        loop_state: MomentumLoopState,
        completed_block: AtomicBlock
    ) -> MomentumLoopState:
        """
        Handle completion of strength task (WIN_STRENGTH → AFFIRM_PRIDE)
        """
        pass

    @abstractmethod
    async def handle_affirm_pride(
        self,
        loop_state: MomentumLoopState,
        reward: RewardMessage
    ) -> MomentumLoopState:
        """
        Handle pride affirmation (AFFIRM_PRIDE → PIVOT_DETECT)
        """
        pass

    @abstractmethod
    async def handle_pivot_detect(
        self,
        loop_state: MomentumLoopState,
        bottleneck: Optional[BottleneckTask]
    ) -> MomentumLoopState:
        """
        Handle bottleneck detection (PIVOT_DETECT → REFRAME_STRENGTH)
        """
        pass

    @abstractmethod
    async def handle_reframe_strength(
        self,
        loop_state: MomentumLoopState,
        reframe_proposal: str,
        user_accepted: bool
    ) -> MomentumLoopState:
        """
        Handle strength-based reframing (REFRAME_STRENGTH → LAUNCH_GROWTH)
        """
        pass

    @abstractmethod
    async def handle_launch_growth(
        self,
        loop_state: MomentumLoopState,
        growth_block: AtomicBlock
    ) -> MomentumLoopState:
        """
        Handle growth task launch (LAUNCH_GROWTH → WIN_GROWTH)
        """
        pass

    @abstractmethod
    async def complete_loop(
        self,
        loop_state: MomentumLoopState,
        successful: bool
    ) -> MomentumLoopState:
        """
        Complete the momentum loop cycle

        Args:
            loop_state: Current loop state
            successful: Was the loop successful?

        Returns:
            Final loop state (IDLE)
        """
        pass


# ============================================================================
# EXPANSION MODULE INTERFACES
# ============================================================================

class ISocialRelatednessModule(ABC):
    """
    Interface for Social Relatedness Module

    Allows users to share "Earned Wins" with groups (non-coercively).
    """

    @abstractmethod
    async def share_win(
        self,
        user_id: str,
        block: AtomicBlock,
        groups: List[str],
        message: Optional[str] = None
    ) -> bool:
        """
        Share a completed atomic block as a win

        Args:
            user_id: User sharing
            block: Completed block to share
            groups: Groups to share with
            message: Optional custom message

        Returns:
            True if shared successfully
        """
        pass

    @abstractmethod
    async def check_share_eligibility(
        self,
        user_id: str,
        block: AtomicBlock
    ) -> bool:
        """
        Check if user can share this win (non-coercive check)
        """
        pass


class ICreativeSandboxModule(ABC):
    """
    Interface for Creative Sandbox Module

    Reframes atomic blocks around process (not outcome) for creative work.
    """

    @abstractmethod
    async def create_creative_block(
        self,
        user_id: str,
        activity_type: str,
        duration_minutes: int
    ) -> AtomicBlock:
        """
        Create a process-based creative block

        Args:
            user_id: User creating block
            activity_type: Type of creative activity
            duration_minutes: How long to create

        Returns:
            Creative atomic block (win = time spent)
        """
        pass


class IEpicMeaningModule(ABC):
    """
    Interface for Epic Meaning Module

    Links atomic wins to core values and life goals.
    """

    @abstractmethod
    async def generate_meaning_narrative(
        self,
        user_id: str,
        block: AtomicBlock,
        personality: PersonalityProfile
    ) -> str:
        """
        Generate narrative connecting win to values/goals

        Args:
            user_id: User who completed block
            block: Completed atomic block
            personality: User's personality profile

        Returns:
            Meaning narrative text
        """
        pass


# ============================================================================
# INTEGRATION INTERFACES
# ============================================================================

class IPersonalityModuleConnector(ABC):
    """
    Interface for connecting to Personality Module

    Links FFE to EnhancedContextManager for personality data storage.
    """

    @abstractmethod
    async def load_personality_profile(
        self,
        user_id: str
    ) -> PersonalityProfile:
        """Load user's personality profile from context manager"""
        pass

    @abstractmethod
    async def save_personality_profile(
        self,
        profile: PersonalityProfile
    ) -> bool:
        """Save updated personality profile to context manager"""
        pass

    @abstractmethod
    async def update_strength(
        self,
        user_id: str,
        strength: SignatureStrength
    ) -> bool:
        """Update a signature strength (e.g., after using it)"""
        pass


class IARIConnector(ABC):
    """
    Interface for connecting to ARI Monitor

    Links FFE Growth Scaffold to ARI for bottleneck detection.
    """

    @abstractmethod
    async def detect_skill_atrophy(
        self,
        user_id: str,
        lookback_days: int = 30
    ) -> List[str]:
        """
        Detect skills that are atrophying (from ARI alerts)

        Returns:
            List of skill/task categories being avoided
        """
        pass

    @abstractmethod
    async def get_avoided_tasks(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get tasks user is avoiding (from ARI tracking)
        """
        pass


class IDashboardConnector(ABC):
    """
    Interface for connecting to Agency Dashboard

    Adds FFE metrics section to dashboard.
    """

    @abstractmethod
    async def get_ffe_metrics(
        self,
        user_id: str,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get FFE metrics for dashboard display
        """
        pass

    @abstractmethod
    async def format_ffe_dashboard_section(
        self,
        metrics: Dict[str, Any]
    ) -> str:
        """
        Format FFE data for dashboard display
        """
        pass
