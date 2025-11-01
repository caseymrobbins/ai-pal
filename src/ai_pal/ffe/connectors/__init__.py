"""
FFE Connectors - Dynamic Integration Components

Connectors that automatically update FFE components based on usage:
- Personality Connector: Refines strengths from behavioral observation
- (Future connectors for other dynamic updates)
"""

from .personality_connector import (
    DynamicPersonalityConnector,
    StrengthEvidence,
)

__all__ = [
    "DynamicPersonalityConnector",
    "StrengthEvidence",
]
