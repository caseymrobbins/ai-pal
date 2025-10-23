"""
Improvement Module - Phase 2

Self-improvement systems for continuous learning:
- Self-Improvement Loop with feedback collection
- LoRA Fine-Tuning for personalization
"""

from .self_improvement import (
    SelfImprovementLoop,
    FeedbackEvent,
    FeedbackType,
    ImprovementSuggestion,
    ImprovementAction,
    ImprovementReport,
)
from .lora_tuning import LoRAFineTuner, FineTuningConfig, FineTuningJob

__all__ = [
    "SelfImprovementLoop",
    "FeedbackEvent",
    "FeedbackType",
    "ImprovementSuggestion",
    "ImprovementAction",
    "ImprovementReport",
    "LoRAFineTuner",
    "FineTuningConfig",
    "FineTuningJob",
]
