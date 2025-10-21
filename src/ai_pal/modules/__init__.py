"""Specialized modules for AI Pal."""

from ai_pal.modules.base import BaseModule
from ai_pal.modules.ethics import EthicsModule
from ai_pal.modules.echo_chamber_buster import EchoChamberBuster
from ai_pal.modules.learning import LearningModule
from ai_pal.modules.dream import DreamModule
from ai_pal.modules.personal_data import PersonalDataModule

__all__ = [
    "BaseModule",
    "EthicsModule",
    "EchoChamberBuster",
    "LearningModule",
    "DreamModule",
    "PersonalDataModule",
]
