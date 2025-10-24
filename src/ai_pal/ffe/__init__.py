"""
Fractal Flow Engine (FFE) V3.0

Non-extractive engagement system that generates sustained user motivation
through the "Momentum Loop" - a psychology-driven cycle that builds
competence and autonomy using signature strengths.

Core Algorithm: WIN → AFFIRM → PIVOT → REFRAME → LAUNCH → WIN

Key Principles:
- Non-exploitative design (Gate #2 compliance)
- User autonomy (5-Block Stop rule)
- Pride-based (not shame/fear) motivation
- Builds genuine competence (not dependency)
- Signature strength amplification

Modules:
- Goal Ingestor: Front door for all tasks
- Fractal 80/20 Scoping Agent: Master planner
- Time-Block Manager: Time & energy alignment
- Signature Strength Amplifier: Pride engine
- Growth Scaffold: Bottleneck detector
- Accomplishment Reward Emitter: Identity-affirming rewards
- Momentum Loop Orchestrator: Core cycle coordinator

Expansion Plugins:
- Social Relatedness Module: Non-coercive win sharing
- Creative Sandbox Module: Process-based wins
- Epic Meaning Module: Value-goal connection
"""

from .models import (
    # Enums
    StrengthType,
    TaskComplexityLevel,
    TimeBlockSize,
    MomentumState,
    BottleneckReason,
    GoalStatus,

    # Personality & Identity
    SignatureStrength,
    PersonalityProfile,

    # Goals & Tasks
    GoalPacket,
    AtomicBlock,
    BottleneckTask,

    # Momentum Loop
    MomentumLoopState,
    RewardMessage,

    # Time Management
    FiveBlockPlan,
    ScopingSession,

    # Expansion Modules
    SharedWin,
    CreativeSandboxBlock,
    MeaningNarrative,

    # Metrics
    FFEMetrics,
)

__all__ = [
    # Enums
    "StrengthType",
    "TaskComplexityLevel",
    "TimeBlockSize",
    "MomentumState",
    "BottleneckReason",
    "GoalStatus",

    # Personality & Identity
    "SignatureStrength",
    "PersonalityProfile",

    # Goals & Tasks
    "GoalPacket",
    "AtomicBlock",
    "BottleneckTask",

    # Momentum Loop
    "MomentumLoopState",
    "RewardMessage",

    # Time Management
    "FiveBlockPlan",
    "ScopingSession",

    # Expansion Modules
    "SharedWin",
    "CreativeSandboxBlock",
    "MeaningNarrative",

    # Metrics
    "FFEMetrics",
]

__version__ = "3.0.0"
