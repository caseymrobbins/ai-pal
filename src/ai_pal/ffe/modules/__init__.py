"""
FFE Phase 6: Expansion Modules

These modules provide additional backend logic for the user-facing interfaces.

Modules:
- Epic Meaning: Connect atomic wins to core values and life goals
- Protégé Pipeline: Learn-by-teaching mode backend
- Social Relatedness: Social win sharing backend
"""

from .epic_meaning import EpicMeaningModule, NarrativeArc
from .protege_pipeline import ProtegePipeline, TeachingSession, Explanation

__all__ = [
    "EpicMeaningModule",
    "NarrativeArc",
    "ProtegePipeline",
    "TeachingSession",
    "Explanation",
]
