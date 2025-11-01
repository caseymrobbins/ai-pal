"""
Social Features Module - Privacy-First Win Sharing

Enables optional social connection through:
- User-defined groups
- User-initiated win sharing
- Mutual encouragement
- Privacy-first design

Key Principles:
- User-initiated only (no automatic sharing)
- Granular privacy controls
- No social pressure
- No metrics gaming
"""

from .relatedness import (
    SocialRelatednessModule,
    SocialGroup,
    SharedWin,
    Encouragement,
    PrivacyLevel,
    GroupRole,
)

__all__ = [
    "SocialRelatednessModule",
    "SocialGroup",
    "SharedWin",
    "Encouragement",
    "PrivacyLevel",
    "GroupRole",
]
