"""
Gates Module - AC-AI Framework Enforcement

Implements the Four Gates system and AHO Tribunal for ethical AI governance.

Components:
- aho_tribunal: Appeals & Human Override system
- gate_system: Four Gates validation

Part of Phase 1.5 integration work.
"""

from .aho_tribunal import (
    AHOTribunal,
    Verdict,
    ImpactScore,
    Appeal,
    AppealStatus,
    AppealPriority,
    OverrideAction,
    RestoreAction,
    RepairTicket
)

from .gate_system import (
    GateSystem,
    GateType,
    GateResult
)

__all__ = [
    # AHO Tribunal
    'AHOTribunal',
    'Verdict',
    'ImpactScore',
    'Appeal',
    'AppealStatus',
    'AppealPriority',
    'OverrideAction',
    'RestoreAction',
    'RepairTicket',
    # Gate System
    'GateSystem',
    'GateType',
    'GateResult'
]
