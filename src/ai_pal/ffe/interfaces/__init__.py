"""
FFE Phase 6: User-Facing "Light Pattern" Interfaces

These interfaces provide the user interaction layer for the FFE V3.0 backend.
They implement non-extractive engagement patterns that build genuine competence,
autonomy, and meaning.

Priority 1 Interfaces (Basic UX):
- Signature Strength Interface: Task reframing and reward display
- Progress Tapestry: Visual timeline of earned wins
- Narrative Arc Engine: Epic meaning connections

Priority 2 Interfaces (Enhanced Engagement):
- Protégé Pipeline: Learn-by-teaching mode
- Curiosity Compass: Exploration opportunity discovery

Priority 3 Interfaces (Social Expansion):
- Social Relatedness: Win sharing with groups

Priority 4 Interfaces (ARI Measurement):
- Learn About Me: Socratic dialogue for deep skill profiling
- Socratic Co-pilot: Embedded capability assessment during assistance
"""

from .progress_tapestry import ProgressTapestry, TapestryView
from .strength_interface import StrengthInterface
from .teaching_interface import TeachingInterface, TeachingPrompt
from .curiosity_compass import CuriosityCompass, CuriosityMap, ExplorationOpportunity
from .learn_about_me import (
    LearnAboutMeInterface,
    DeepDiveSession,
    SocraticQuestion,
    SocraticResponse,
    SynthesisRubric,
    KnowledgeProfile,
    DifficultyLevel,
    ResponseQuality,
)
from .socratic_copilot import (
    SocraticCopilotInterface,
    CopilotRequest,
    CopilotProbe,
    UnassistedCapabilityCheckpoint,
    CheckpointResponseData,
    CheckpointType,
    CheckpointResponse,
)

__all__ = [
    "ProgressTapestry",
    "TapestryView",
    "StrengthInterface",
    "TeachingInterface",
    "TeachingPrompt",
    "CuriosityCompass",
    "CuriosityMap",
    "ExplorationOpportunity",
    "LearnAboutMeInterface",
    "DeepDiveSession",
    "SocraticQuestion",
    "SocraticResponse",
    "SynthesisRubric",
    "KnowledgeProfile",
    "DifficultyLevel",
    "ResponseQuality",
    "SocraticCopilotInterface",
    "CopilotRequest",
    "CopilotProbe",
    "UnassistedCapabilityCheckpoint",
    "CheckpointResponseData",
    "CheckpointType",
    "CheckpointResponse",
]
