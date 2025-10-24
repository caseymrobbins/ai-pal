"""
Fractal Flow Engine (FFE) V3.0 - Data Models

Core data structures for the FFE system:
- Personality profiles and signature strengths
- Goal packets and atomic blocks
- Bottleneck tasks and momentum states
- Time blocks and scoping levels

Integrates with AC-AI framework components:
- EnhancedContextManager (Personality Module storage)
- ARIMonitor (Bottleneck detection)
- MultiModelOrchestrator (AI response generation)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid


# ============================================================================
# ENUMS - FFE Type Definitions
# ============================================================================

class StrengthType(Enum):
    """User signature strength types"""
    VISUAL_THINKING = "visual_thinking"
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"
    CREATIVE = "creative"
    SYSTEMATIC = "systematic"
    SOCIAL = "social"
    KINESTHETIC = "kinesthetic"
    VERBAL = "verbal"
    MUSICAL = "musical"
    SPATIAL = "spatial"


class TaskComplexityLevel(Enum):
    """Task complexity levels for scoping"""
    ATOMIC = "atomic"  # 15-60 min, cannot be subdivided
    MICRO = "micro"    # 1-4 hours, 1 day's work
    MINI = "mini"      # 1-5 days, 1 week's work
    MACRO = "macro"    # 1-4 weeks, 1 month's work
    MEGA = "mega"      # 1-5 months, multi-month project


class TimeBlockSize(Enum):
    """Standard time block durations"""
    SPRINT_15 = 15      # 15-minute sprint
    BLOCK_30 = 30       # 30-minute block
    BLOCK_60 = 60       # 1-hour block
    BLOCK_90 = 90       # 90-minute deep work
    BLOCK_120 = 120     # 2-hour session


class MomentumState(Enum):
    """States in the Momentum Loop"""
    IDLE = "idle"                    # No active loop
    WIN_STRENGTH = "win_strength"    # Completing strength-based task
    AFFIRM_PRIDE = "affirm_pride"    # Reward emitter firing
    PIVOT_DETECT = "pivot_detect"    # Growth scaffold detecting opportunity
    REFRAME_STRENGTH = "reframe_strength"  # Reframing bottleneck via strength
    LAUNCH_GROWTH = "launch_growth"  # Starting growth task
    WIN_GROWTH = "win_growth"        # Completing growth task


class BottleneckReason(Enum):
    """Why a task became a bottleneck"""
    AVOIDED = "avoided"              # User actively avoids
    DIFFICULT = "difficult"          # User finds challenging
    BORING = "boring"                # Low engagement
    ANXIETY_INDUCING = "anxiety_inducing"  # Causes stress
    SKILL_GAP = "skill_gap"          # Missing prerequisite skills
    UNCLEAR = "unclear"              # Poorly defined


class GoalStatus(Enum):
    """Status of goals in the system"""
    PENDING = "pending"              # Not started
    IN_PROGRESS = "in_progress"      # Currently active
    COMPLETED = "completed"          # Finished
    SCOPED = "scoped"                # Subdivided into smaller goals
    DEFERRED = "deferred"            # Postponed
    CANCELLED = "cancelled"          # No longer relevant


# ============================================================================
# PERSONALITY & IDENTITY MODELS
# ============================================================================

@dataclass
class SignatureStrength:
    """
    A user's core identity-based strength

    Used by the Signature Strength Amplifier to reframe tasks
    and generate identity-affirming reward language.
    """
    strength_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strength_type: StrengthType = StrengthType.ANALYTICAL

    # Identity language
    identity_label: str = "Analytical Thinker"  # How user self-identifies
    strength_description: str = ""  # Detailed description of strength

    # Evidence & confidence
    demonstrated_examples: List[str] = field(default_factory=list)  # Past wins using this strength
    confidence_score: float = 0.8  # How confident we are in this strength (0-1)

    # Task mapping
    compatible_task_types: Set[str] = field(default_factory=set)  # Task types this strength excels at
    incompatible_task_types: Set[str] = field(default_factory=set)  # Tasks this strength struggles with

    # Metadata
    discovered_date: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0


@dataclass
class PersonalityProfile:
    """
    User's central personality/identity profile

    The FFE's "config file" - links to EnhancedContextManager for storage.
    Feeds into all FFE components for personalization.
    """
    user_id: str
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Core identity
    signature_strengths: List[SignatureStrength] = field(default_factory=list)
    primary_strength: Optional[StrengthType] = None

    # Values & meaning (for Epic Meaning Module)
    core_values: List[str] = field(default_factory=list)  # e.g., ["Family", "Community", "Growth"]
    life_goals: List[str] = field(default_factory=list)   # e.g., ["Build app for community"]

    # Priorities (for Goal Ingestor)
    current_priorities: List[str] = field(default_factory=list)  # e.g., ["Learn Python", "Write novel"]
    priority_weights: Dict[str, float] = field(default_factory=dict)  # Priority importance scores

    # Psychological characteristics
    energy_patterns: Dict[str, Any] = field(default_factory=dict)  # Morning person, etc.
    preferred_block_sizes: List[TimeBlockSize] = field(default_factory=list)  # Preferred time blocks
    autonomy_preference: float = 0.8  # How much autonomy user prefers (0-1)

    # Social context (for Social Relatedness Module)
    social_groups: List[str] = field(default_factory=list)  # User-defined groups
    share_wins_with: Set[str] = field(default_factory=set)  # Who to share wins with

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


# ============================================================================
# GOAL & TASK MODELS
# ============================================================================

@dataclass
class GoalPacket:
    """
    A goal at any level of scoping

    The fundamental unit of work in FFE. Goals flow through the
    Fractal 80/20 Scoping Agent and are recursively subdivided.
    """
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Goal definition
    description: str = ""  # What the goal is
    complexity_level: TaskComplexityLevel = TaskComplexityLevel.MACRO

    # Scoping hierarchy
    parent_goal_id: Optional[str] = None  # What goal is this derived from?
    child_goal_ids: List[str] = field(default_factory=list)  # What goals derived from this?
    scoping_iteration: int = 0  # How many 80/20 iterations deep?

    # 80/20 Analysis
    estimated_value: float = 0.0  # Expected value/impact (0-1)
    estimated_effort: float = 0.0  # Expected effort required (0-1)
    value_effort_ratio: float = 0.0  # Value/Effort (for 80/20 identification)

    # Status & timing
    status: GoalStatus = GoalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Personalization
    linked_strength: Optional[StrengthType] = None  # Strength this goal uses
    linked_value: Optional[str] = None  # Core value this goal serves

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)


@dataclass
class AtomicBlock:
    """
    A time-boxed, indivisible unit of work

    The final output of the Scoping Agent. An atomic block is:
    - Small enough to complete in one session (15-90 min)
    - Clear enough to know when it's "done"
    - Achievable enough to generate an "Earned Win"
    """
    block_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    goal_id: str = ""  # Which goal does this block serve?

    # Block definition
    title: str = ""  # e.g., "Master Python Lists"
    description: str = ""  # Clear success criteria
    time_block_size: TimeBlockSize = TimeBlockSize.BLOCK_30

    # Strength reframing
    original_description: str = ""  # Before strength reframing
    strength_reframe: Optional[str] = None  # After strength amplification
    using_strength: Optional[StrengthType] = None

    # Scheduling
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None

    # Completion & reward
    completed: bool = False
    completion_time: Optional[datetime] = None
    quality_score: float = 0.0  # Self-assessed quality (0-1)

    # Reward emitter data
    reward_emitted: bool = False
    reward_text: Optional[str] = None  # Identity-affirming reward message
    pride_hit_intensity: float = 0.0  # How strong was the pride response? (0-1)

    # Momentum loop integration
    triggered_momentum_loop: bool = False
    led_to_growth_task: Optional[str] = None  # Block ID of growth task spawned

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BottleneckTask:
    """
    A task the user avoids or struggles with

    Detected by Growth Scaffold (via ARI integration).
    Queued for strength-based reframing during momentum loops.
    """
    bottleneck_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Task identification
    task_description: str = ""
    task_category: str = ""  # e.g., "budgeting", "exercise", "writing"

    # Bottleneck analysis
    bottleneck_reason: BottleneckReason = BottleneckReason.AVOIDED
    detection_method: str = "ari_alert"  # How was this detected?
    avoidance_count: int = 0  # How many times avoided?
    last_avoided: Optional[datetime] = None

    # Impact assessment
    importance_score: float = 0.0  # How important is this task? (0-1)
    skill_gap_severity: float = 0.0  # How severe is the skill gap? (0-1)

    # Reframing attempts
    reframe_attempts: List[Dict[str, Any]] = field(default_factory=list)
    successful_reframe: Optional[Dict[str, Any]] = None

    # Queue status
    queued: bool = True
    queued_date: datetime = field(default_factory=datetime.now)
    activated: bool = False
    activation_date: Optional[datetime] = None

    # Resolution
    resolved: bool = False
    resolution_date: Optional[datetime] = None
    resolution_method: Optional[str] = None  # How was bottleneck overcome?


# ============================================================================
# MOMENTUM LOOP MODELS
# ============================================================================

@dataclass
class MomentumLoopState:
    """
    State tracking for the Momentum Loop

    Tracks progress through WIN → AFFIRM → PIVOT → REFRAME → LAUNCH cycle.
    """
    loop_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Current state
    current_state: MomentumState = MomentumState.IDLE
    previous_state: Optional[MomentumState] = None

    # Cycle tracking
    cycle_count: int = 0  # How many complete loops?
    started_at: datetime = field(default_factory=datetime.now)
    last_state_change: datetime = field(default_factory=datetime.now)

    # Strength task (WIN_STRENGTH)
    strength_task_block_id: Optional[str] = None
    strength_used: Optional[StrengthType] = None
    strength_win_completed: bool = False

    # Pride hit (AFFIRM_PRIDE)
    pride_hit_received: bool = False
    pride_intensity: float = 0.0
    affirmation_text: Optional[str] = None

    # Bottleneck detection (PIVOT_DETECT)
    bottleneck_detected: bool = False
    bottleneck_task_id: Optional[str] = None

    # Strength reframe (REFRAME_STRENGTH)
    reframe_proposed: bool = False
    reframe_description: Optional[str] = None
    user_accepted_reframe: bool = False

    # Growth task (LAUNCH_GROWTH)
    growth_task_block_id: Optional[str] = None
    growth_task_launched: bool = False
    growth_task_completed: bool = False

    # Outcomes
    successful_cycle: bool = False
    bottleneck_resolved: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RewardMessage:
    """
    Identity-affirming reward generated by Accomplishment Reward Emitter

    Uses explicit language from Signature Strength Amplifier.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    block_id: str = ""  # Which atomic block was completed?

    # Reward content
    reward_text: str = ""  # The actual affirmation message
    strength_referenced: Optional[StrengthType] = None
    identity_label_used: str = ""  # e.g., "strong visual thinker"

    # Template structure (for consistency)
    template_used: str = "standard"  # Which reward template?
    personalization_elements: List[str] = field(default_factory=list)

    # Delivery
    emitted_at: datetime = field(default_factory=datetime.now)
    displayed_to_user: bool = False

    # Impact tracking
    triggered_momentum_loop: bool = False
    user_reaction: Optional[str] = None  # Positive, neutral, negative


# ============================================================================
# TIME MANAGEMENT MODELS
# ============================================================================

@dataclass
class FiveBlockPlan:
    """
    5-Block Rule implementation for macro time management

    Breaks large goals into 5 equal blocks (e.g., 5-month → 5x1-month).
    Enforces autonomy via the 5-Block Stop rule.
    """
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    goal_id: str = ""  # Macro goal being planned

    # Time scale
    total_duration_months: int = 5
    block_duration_months: int = 1

    # Block definitions
    blocks: List[Dict[str, Any]] = field(default_factory=list)  # 5 blocks
    current_block_index: int = 0

    # 5-Block Stop enforcement
    stop_points: List[datetime] = field(default_factory=list)  # When to pause & reassess
    user_confirmed_continuation: List[bool] = field(default_factory=list)  # User chose to continue?

    # Progress
    blocks_completed: int = 0
    plan_started: Optional[datetime] = None
    plan_completed: Optional[datetime] = None

    # Autonomy tracking
    user_initiated_plan: bool = True  # Did user create this plan?
    user_can_modify: bool = True  # Can user change the plan?


@dataclass
class ScopingSession:
    """
    A single pass through the Fractal 80/20 Scoping Agent

    Documents the scoping decision-making process.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Input
    input_goal: GoalPacket = None  # The 100% goal input

    # Analysis
    identified_80_win: Optional[str] = None  # The 20% that delivers 80% value
    value_effort_analysis: Dict[str, Any] = field(default_factory=dict)

    # Output
    output_goal: Optional[GoalPacket] = None  # The reframed 80% as new 100%
    remaining_20: Optional[str] = None  # What's left for future iteration

    # Recursion
    requires_further_scoping: bool = True
    target_complexity: TaskComplexityLevel = TaskComplexityLevel.ATOMIC
    achieved_complexity: TaskComplexityLevel = TaskComplexityLevel.MACRO

    # Timing
    scoped_at: datetime = field(default_factory=datetime.now)
    scoping_duration_seconds: float = 0.0

    # AI assistance
    ai_model_used: Optional[str] = None
    ai_confidence: float = 0.0


# ============================================================================
# EXPANSION MODULE MODELS
# ============================================================================

@dataclass
class SharedWin:
    """
    An "Earned Win" shared with a social group (Social Relatedness Module)
    """
    share_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    block_id: str = ""  # Which atomic block was shared?

    # Sharing
    shared_with_groups: List[str] = field(default_factory=list)
    share_message: str = ""
    shared_at: datetime = field(default_factory=datetime.now)

    # Privacy
    user_initiated_share: bool = True  # Non-coercive requirement
    share_level: str = "group_only"  # privacy level

    # Engagement
    reactions: List[Dict[str, Any]] = field(default_factory=list)
    supportive_responses: int = 0


@dataclass
class CreativeSandboxBlock:
    """
    Process-based creative block (Creative Sandbox Module)

    Wins based on time spent, not outcome quality.
    """
    sandbox_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Creative activity
    activity_type: str = ""  # e.g., "painting", "writing", "music"
    process_description: str = "Explore and create"

    # Time-based win
    target_duration_minutes: int = 30
    actual_duration_minutes: Optional[int] = None

    # Outcome (not judged)
    output_description: Optional[str] = None
    user_satisfaction: float = 0.0  # How did it feel? (0-1)

    # Flow state
    entered_flow_state: bool = False
    flow_indicators: List[str] = field(default_factory=list)


@dataclass
class MeaningNarrative:
    """
    Epic meaning connection (Epic Meaning Module)

    Links atomic wins to core values and life goals.
    """
    narrative_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    block_id: str = ""  # Atomic block completed

    # Value connection
    linked_core_value: str = ""  # e.g., "Community"
    linked_life_goal: str = ""   # e.g., "Build app for community"

    # Narrative text
    connection_narrative: str = ""  # How this win serves the value/goal

    # Impact
    meaning_intensity: float = 0.0  # How meaningful? (0-1)
    long_term_vision_reminder: bool = True


# ============================================================================
# INTEGRATION MODELS
# ============================================================================

@dataclass
class FFEMetrics:
    """
    FFE system metrics for monitoring and dashboard integration
    """
    user_id: str = ""

    # Momentum loop stats
    total_loops_completed: int = 0
    successful_loops: int = 0
    loop_success_rate: float = 0.0

    # Task completion
    atomic_blocks_completed: int = 0
    strength_tasks_completed: int = 0
    growth_tasks_completed: int = 0

    # Bottleneck resolution
    bottlenecks_detected: int = 0
    bottlenecks_resolved: int = 0
    bottleneck_resolution_rate: float = 0.0

    # Pride & engagement
    total_pride_hits: int = 0
    average_pride_intensity: float = 0.0

    # Autonomy respect
    five_block_stops_honored: int = 0
    user_plan_modifications: int = 0

    # Time tracking
    total_time_in_atomic_blocks_minutes: int = 0
    average_block_completion_rate: float = 0.0

    # Integration with AC-AI
    humanity_gate_score_contribution: float = 0.0
    ari_improvement_delta: float = 0.0

    # Reporting period
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
