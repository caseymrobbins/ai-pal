"""
AHO Tribunal - Bridge to Phase 1 Implementation

Bridges Phase 2-3 expectations to actual Phase 1 implementation.
The actual implementation is in api.aho_tribunal.
"""

from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# Import actual Phase 1 implementation
from ..api.aho_tribunal import (
    Appeal,
    AppealStatus,
    AppealPriority,
    OverrideAction,
    RestoreAction,
    RepairTicket,
    AHODatabase
)

__all__ = [
    'AHOTribunal',
    'Verdict',
    'ImpactScore',
    'Appeal',
    'AppealStatus',
    'AppealPriority',
    'OverrideAction',
    'RestoreAction',
    'RepairTicket'
]


class Verdict(Enum):
    """Tribunal verdict on an appeal."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    PENDING = "pending"


@dataclass
class ImpactScore:
    """
    Quantifies the impact of an AI decision on user agency.

    Used by the tribunal to assess severity of appeals.
    """

    agency_delta: float  # Change in user agency (-1.0 to 1.0)
    privacy_impact: float  # Privacy violation score (0.0 to 1.0)
    transparency_score: float  # How transparent was the decision (0.0 to 1.0)
    harm_severity: float = 0.0  # Severity of potential harm (0.0 to 1.0)

    @property
    def overall_impact(self) -> float:
        """Calculate overall impact score."""
        # Negative agency and high privacy impact increase score
        # High transparency decreases score
        return (
            abs(self.agency_delta) * 0.4 +
            self.privacy_impact * 0.3 +
            (1.0 - self.transparency_score) * 0.2 +
            self.harm_severity * 0.1
        )


class AHOTribunal:
    """
    Bridge class to Phase 1 AHO implementation.

    Provides the interface expected by Phase 2-3 while delegating
    to the actual Appeal-based implementation.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize tribunal with storage."""
        self.db = AHODatabase(storage_dir=storage_dir)

    async def submit_appeal(
        self,
        user_id: str,
        action_id: str,
        ai_decision: str,
        user_complaint: str,
        context: Dict[str, Any],
        priority: AppealPriority = AppealPriority.MEDIUM
    ) -> Appeal:
        """
        Submit an appeal to the tribunal.

        Maps to Phase 1's Appeal submission.
        """
        from ..api.aho_tribunal import submit_appeal

        return await submit_appeal(
            user_id=user_id,
            action_id=action_id,
            ai_decision=ai_decision,
            user_complaint=user_complaint,
            decision_context=context,
            priority=priority,
            db=self.db
        )

    async def review_appeal(
        self,
        appeal_id: str,
        reviewer_id: str,
        verdict: Verdict,
        notes: str
    ) -> Appeal:
        """
        Review an appeal and issue a verdict.

        Args:
            appeal_id: ID of appeal to review
            reviewer_id: ID of human reviewer
            verdict: Verdict on the appeal
            notes: Review notes

        Returns:
            Updated appeal
        """
        appeal = self.db.get_appeal(appeal_id)
        if not appeal:
            raise ValueError(f"Appeal {appeal_id} not found")

        # Map verdict to AppealStatus
        status_map = {
            Verdict.APPROVED: AppealStatus.APPROVED,
            Verdict.REJECTED: AppealStatus.DENIED,
            Verdict.NEEDS_REVIEW: AppealStatus.UNDER_REVIEW,
            Verdict.PENDING: AppealStatus.PENDING
        }

        appeal.status = status_map[verdict]
        appeal.reviewer_id = reviewer_id
        appeal.reviewed_at = datetime.now()
        appeal.review_notes = notes

        self.db.update_appeal(appeal)
        return appeal

    async def calculate_impact(
        self,
        action_context: Dict[str, Any],
        user_state_before: Dict[str, Any],
        user_state_after: Dict[str, Any]
    ) -> ImpactScore:
        """
        Calculate impact score for an AI decision.

        Args:
            action_context: Context of the AI decision
            user_state_before: User state before action
            user_state_after: User state after action

        Returns:
            Impact score
        """
        # Calculate agency delta
        agency_before = user_state_before.get('agency_score', 0.5)
        agency_after = user_state_after.get('agency_score', 0.5)
        agency_delta = agency_after - agency_before

        # Calculate privacy impact
        pii_exposed = action_context.get('pii_exposed', False)
        data_shared = action_context.get('data_shared', [])
        privacy_impact = (
            (0.5 if pii_exposed else 0.0) +
            (len(data_shared) * 0.1)
        )
        privacy_impact = min(privacy_impact, 1.0)

        # Calculate transparency
        explanation_provided = action_context.get('explanation_provided', False)
        user_notified = action_context.get('user_notified', False)
        transparency_score = (
            (0.5 if explanation_provided else 0.0) +
            (0.5 if user_notified else 0.0)
        )

        # Calculate harm severity
        harm_indicators = action_context.get('harm_indicators', [])
        harm_severity = min(len(harm_indicators) * 0.25, 1.0)

        return ImpactScore(
            agency_delta=agency_delta,
            privacy_impact=privacy_impact,
            transparency_score=transparency_score,
            harm_severity=harm_severity
        )

    async def execute_override(
        self,
        appeal_id: str,
        override_action: str,
        reason: str
    ) -> bool:
        """
        Execute an override action for an approved appeal.

        Args:
            appeal_id: ID of appeal
            override_action: Action to take
            reason: Reason for override

        Returns:
            True if successful
        """
        appeal = self.db.get_appeal(appeal_id)
        if not appeal:
            raise ValueError(f"Appeal {appeal_id} not found")

        if appeal.status != AppealStatus.APPROVED:
            raise ValueError(f"Appeal must be approved before override")

        appeal.override_executed = True
        self.db.update_appeal(appeal)

        logger.info(f"Override executed for appeal {appeal_id}: {override_action}")
        return True

    async def get_pending_appeals(self) -> list:
        """Get all pending appeals."""
        return self.db.get_appeals_by_status(AppealStatus.PENDING)

    async def get_appeal(self, appeal_id: str) -> Optional[Appeal]:
        """Get a specific appeal."""
        return self.db.get_appeal(appeal_id)
