"""
Privacy Module - Phase 3

Advanced privacy protection:
- Enhanced PII detection
- Differential privacy
- Data minimization
- Consent management
- Privacy budget tracking
"""

from .advanced_privacy import (
    AdvancedPrivacyManager,
    PIIType,
    PIIDetection,
    PrivacyAction,
    PrivacyBudget,
    ConsentLevel,
    ConsentRecord,
    DataMinimizationPolicy,
)

__all__ = [
    "AdvancedPrivacyManager",
    "PIIType",
    "PIIDetection",
    "PrivacyAction",
    "PrivacyBudget",
    "ConsentLevel",
    "ConsentRecord",
    "DataMinimizationPolicy",
]
