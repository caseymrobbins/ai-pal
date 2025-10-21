"""
AI Pal - Privacy-First Cognitive Partner

A hybrid AI architecture combining local SLMs with cloud LLMs,
built on the Agency Calculus for AI (AC-AI) framework.
"""

__version__ = "0.1.0"

from ai_pal.core.orchestrator import Orchestrator
from ai_pal.modules.ethics import EthicsModule

__all__ = ["Orchestrator", "EthicsModule", "__version__"]
