"""
Interaction Modes for AI-PAL.

Provides different interaction modes optimized for learning, assessment,
and capability-appropriate assistance.
"""

from ai_pal.modes.learn_about_me import (
    LearnAboutMeMode,
    LearnAboutMeSession,
    DifficultyLevel,
    SessionStatus,
)

from ai_pal.modes.socratic_copilot import (
    SocraticCopilot,
    TaskRequest,
    TaskType,
    AssistanceLevel,
)

__all__ = [
    "LearnAboutMeMode",
    "LearnAboutMeSession",
    "DifficultyLevel",
    "SessionStatus",
    "SocraticCopilot",
    "TaskRequest",
    "TaskType",
    "AssistanceLevel",
]
