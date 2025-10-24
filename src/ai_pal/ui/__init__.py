"""
UI Module - Phase 3

User interface components for transparency and agency monitoring:
- Agency dashboard with real-time metrics
- Privacy status visualization
- Model usage analytics
- Epistemic debt reports
- Self-improvement tracking
"""

from .agency_dashboard import (
    AgencyDashboard,
    DashboardSection,
    DashboardData,
    AgencyMetrics,
    PrivacyStatus,
    ModelUsageStats,
    EpistemicDebtStatus,
    ImprovementActivity,
    ContextMemoryStatus,
)

__all__ = [
    "AgencyDashboard",
    "DashboardSection",
    "DashboardData",
    "AgencyMetrics",
    "PrivacyStatus",
    "ModelUsageStats",
    "EpistemicDebtStatus",
    "ImprovementActivity",
    "ContextMemoryStatus",
]
