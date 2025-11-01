"""
Enhanced AHO Tribunal with Multi-Stakeholder Voting

Implements advanced tribunal features:
- Multi-stakeholder voting (users, reviewers, technical experts, ethicists)
- Appeal and re-appeal processes
- Comprehensive audit trails
- Voting quorum and consensus rules
- Automated escalation for controversial decisions
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import Counter

from .aho_tribunal import (
    Appeal,
    AppealStatus,
    AppealPriority,
    AHODatabase,
    OverrideAction,
)

logger = logging.getLogger(__name__)


class StakeholderRole(Enum):
    """Types of stakeholders in tribunal voting"""
    USER = "user"  # Affected users
    REVIEWER = "reviewer"  # Human reviewers
    TECHNICAL_EXPERT = "technical_expert"  # Engineers/developers
    ETHICIST = "ethicist"  # Ethics/policy experts
    PRODUCT_OWNER = "product_owner"  # Product team
    LEGAL = "legal"  # Legal compliance
    COMMUNITY_REP = "community_rep"  # Community representatives


class VoteDecision(Enum):
    """Possible vote decisions"""
    APPROVE = "approve"
    DENY = "deny"
    ABSTAIN = "abstain"
    NEEDS_MORE_INFO = "needs_more_info"


class AppealStage(Enum):
    """Stages in the appeal process"""
    INITIAL_REVIEW = "initial_review"  # First review
    STAKEHOLDER_VOTING = "stakeholder_voting"  # Multi-stakeholder vote
    RE_APPEAL = "re_appeal"  # User re-appeals
    FINAL_DECISION = "final_decision"  # Final binding decision
    CLOSED = "closed"  # Case closed


@dataclass
class Vote:
    """A single stakeholder vote"""
    voter_id: str
    stakeholder_role: StakeholderRole
    decision: VoteDecision
    reasoning: str
    timestamp: datetime
    confidence_score: float = 0.5  # 0.0 to 1.0
    additional_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "voter_id": self.voter_id,
            "stakeholder_role": self.stakeholder_role.value,
            "decision": self.decision.value,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "confidence_score": self.confidence_score,
            "additional_context": self.additional_context,
        }


@dataclass
class VotingRound:
    """A round of stakeholder voting"""
    round_id: str
    appeal_id: str
    stage: AppealStage
    started_at: datetime
    deadline: datetime
    votes: List[Vote] = field(default_factory=list)
    quorum_met: bool = False
    consensus_reached: bool = False
    final_decision: Optional[VoteDecision] = None
    decision_reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "round_id": self.round_id,
            "appeal_id": self.appeal_id,
            "stage": self.stage.value,
            "started_at": self.started_at.isoformat(),
            "deadline": self.deadline.isoformat(),
            "votes": [v.to_dict() for v in self.votes],
            "quorum_met": self.quorum_met,
            "consensus_reached": self.consensus_reached,
            "final_decision": self.final_decision.value if self.final_decision else None,
            "decision_reasoning": self.decision_reasoning,
        }


@dataclass
class EnhancedAppeal:
    """Enhanced appeal with multi-stakeholder voting"""
    appeal: Appeal
    stage: AppealStage
    voting_rounds: List[VotingRound] = field(default_factory=list)
    re_appeal_count: int = 0
    escalated: bool = False
    escalation_reason: str = ""
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def add_audit_entry(self, action: str, details: Dict[str, Any]) -> None:
        """Add entry to audit trail"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
        }
        self.audit_trail.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "appeal_id": self.appeal.appeal_id,
            "stage": self.stage.value,
            "voting_rounds": [vr.to_dict() for vr in self.voting_rounds],
            "re_appeal_count": self.re_appeal_count,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
            "audit_trail": self.audit_trail,
        }


class VotingRules:
    """Rules for multi-stakeholder voting"""

    # Minimum number of votes needed for quorum (by role)
    QUORUM_REQUIREMENTS = {
        StakeholderRole.REVIEWER: 1,  # At least 1 reviewer
        StakeholderRole.TECHNICAL_EXPERT: 1,  # At least 1 technical expert
    }

    # Roles that must be consulted for high-priority appeals
    CRITICAL_ROLES = {
        StakeholderRole.REVIEWER,
        StakeholderRole.ETHICIST,
        StakeholderRole.LEGAL,
    }

    # Consensus threshold (percentage of non-abstain votes)
    CONSENSUS_THRESHOLD = 0.66  # 66% agreement

    # Maximum time for voting rounds
    VOTING_DEADLINES = {
        AppealPriority.LOW: timedelta(days=7),
        AppealPriority.MEDIUM: timedelta(days=3),
        AppealPriority.HIGH: timedelta(days=1),
        AppealPriority.CRITICAL: timedelta(hours=6),
    }

    @staticmethod
    def check_quorum(votes: List[Vote], appeal_priority: AppealPriority) -> bool:
        """Check if quorum is met"""
        votes_by_role = {}
        for vote in votes:
            role = vote.stakeholder_role
            if role not in votes_by_role:
                votes_by_role[role] = []
            votes_by_role[role].append(vote)

        # Check basic quorum
        for role, min_count in VotingRules.QUORUM_REQUIREMENTS.items():
            if len(votes_by_role.get(role, [])) < min_count:
                return False

        # For critical appeals, require critical roles
        if appeal_priority == AppealPriority.CRITICAL:
            for role in VotingRules.CRITICAL_ROLES:
                if role not in votes_by_role:
                    return False

        return True

    @staticmethod
    def calculate_consensus(votes: List[Vote]) -> tuple[bool, Optional[VoteDecision], str]:
        """
        Calculate if consensus is reached.

        Returns:
            (consensus_reached, final_decision, reasoning)
        """
        if not votes:
            return False, None, "No votes cast"

        # Filter out abstentions
        active_votes = [v for v in votes if v.decision != VoteDecision.ABSTAIN]

        if not active_votes:
            return False, None, "All votes were abstentions"

        # Count votes
        decision_counts = Counter(v.decision for v in active_votes)
        total_active = len(active_votes)

        # Find majority decision
        most_common_decision, count = decision_counts.most_common(1)[0]
        percentage = count / total_active

        # Check if consensus threshold met
        consensus_reached = percentage >= VotingRules.CONSENSUS_THRESHOLD

        reasoning = f"{count}/{total_active} votes ({percentage:.1%}) for {most_common_decision.value}"

        if consensus_reached:
            return True, most_common_decision, reasoning
        else:
            return False, None, f"No consensus reached. {reasoning}"


class EnhancedTribunal:
    """
    Enhanced AHO Tribunal with multi-stakeholder voting.

    Features:
    - Multi-stakeholder voting with configurable quorum
    - Appeal and re-appeal processes
    - Automated escalation for controversial decisions
    - Comprehensive audit trails
    - Voting deadlines and reminders
    """

    def __init__(self, db: Optional[AHODatabase] = None):
        """Initialize enhanced tribunal"""
        self.db = db or AHODatabase()
        self.enhanced_appeals: Dict[str, EnhancedAppeal] = {}
        self.voting_rounds: Dict[str, VotingRound] = {}

    async def submit_appeal(
        self,
        appeal: Appeal
    ) -> EnhancedAppeal:
        """
        Submit an appeal for multi-stakeholder review.

        Args:
            appeal: Base appeal object

        Returns:
            Enhanced appeal with voting capabilities
        """
        # Create enhanced appeal
        enhanced = EnhancedAppeal(
            appeal=appeal,
            stage=AppealStage.INITIAL_REVIEW,
        )

        enhanced.add_audit_entry("appeal_submitted", {
            "user_id": appeal.user_id,
            "priority": appeal.priority.value,
        })

        self.enhanced_appeals[appeal.appeal_id] = enhanced
        self.db.add_appeal(appeal)

        # Start initial voting round
        await self._start_voting_round(enhanced)

        return enhanced

    async def _start_voting_round(
        self,
        enhanced_appeal: EnhancedAppeal
    ) -> VotingRound:
        """Start a new voting round"""
        import uuid

        appeal = enhanced_appeal.appeal
        round_id = f"round_{uuid.uuid4().hex[:8]}"

        # Calculate deadline based on priority
        deadline = datetime.now() + VotingRules.VOTING_DEADLINES[appeal.priority]

        voting_round = VotingRound(
            round_id=round_id,
            appeal_id=appeal.appeal_id,
            stage=enhanced_appeal.stage,
            started_at=datetime.now(),
            deadline=deadline,
        )

        self.voting_rounds[round_id] = voting_round
        enhanced_appeal.voting_rounds.append(voting_round)

        enhanced_appeal.add_audit_entry("voting_round_started", {
            "round_id": round_id,
            "stage": enhanced_appeal.stage.value,
            "deadline": deadline.isoformat(),
        })

        logger.info(
            f"Started voting round {round_id} for appeal {appeal.appeal_id}, "
            f"deadline: {deadline}"
        )

        return voting_round

    async def cast_vote(
        self,
        appeal_id: str,
        voter_id: str,
        stakeholder_role: StakeholderRole,
        decision: VoteDecision,
        reasoning: str,
        confidence_score: float = 0.5,
    ) -> Vote:
        """
        Cast a vote in the current voting round.

        Args:
            appeal_id: ID of the appeal
            voter_id: ID of the voter
            stakeholder_role: Role of the stakeholder
            decision: Vote decision
            reasoning: Reasoning for the vote
            confidence_score: Confidence in the decision (0.0 to 1.0)

        Returns:
            The cast vote
        """
        enhanced = self.enhanced_appeals.get(appeal_id)
        if not enhanced:
            raise ValueError(f"Appeal {appeal_id} not found")

        # Get current voting round
        if not enhanced.voting_rounds:
            raise ValueError(f"No active voting round for appeal {appeal_id}")

        current_round = enhanced.voting_rounds[-1]

        # Check if deadline passed
        if datetime.now() > current_round.deadline:
            raise ValueError(f"Voting deadline has passed for round {current_round.round_id}")

        # Check if voter already voted in this round
        existing_vote = next(
            (v for v in current_round.votes if v.voter_id == voter_id),
            None
        )

        if existing_vote:
            raise ValueError(f"Voter {voter_id} has already voted in this round")

        # Create vote
        vote = Vote(
            voter_id=voter_id,
            stakeholder_role=stakeholder_role,
            decision=decision,
            reasoning=reasoning,
            timestamp=datetime.now(),
            confidence_score=confidence_score,
        )

        current_round.votes.append(vote)

        enhanced.add_audit_entry("vote_cast", {
            "round_id": current_round.round_id,
            "voter_id": voter_id,
            "role": stakeholder_role.value,
            "decision": decision.value,
        })

        # Check if quorum and consensus reached
        await self._evaluate_voting_round(enhanced, current_round)

        return vote

    async def _evaluate_voting_round(
        self,
        enhanced_appeal: EnhancedAppeal,
        voting_round: VotingRound
    ) -> None:
        """Evaluate a voting round for quorum and consensus"""
        appeal = enhanced_appeal.appeal

        # Check quorum
        quorum_met = VotingRules.check_quorum(voting_round.votes, appeal.priority)
        voting_round.quorum_met = quorum_met

        if not quorum_met:
            logger.info(f"Quorum not yet met for round {voting_round.round_id}")
            return

        # Check consensus
        consensus_reached, final_decision, reasoning = VotingRules.calculate_consensus(
            voting_round.votes
        )

        voting_round.consensus_reached = consensus_reached
        voting_round.final_decision = final_decision
        voting_round.decision_reasoning = reasoning

        if consensus_reached:
            enhanced_appeal.add_audit_entry("consensus_reached", {
                "round_id": voting_round.round_id,
                "decision": final_decision.value,
                "reasoning": reasoning,
            })

            # Apply decision
            await self._apply_decision(enhanced_appeal, final_decision)

        else:
            # Check if deadline passed - if so, escalate
            if datetime.now() > voting_round.deadline:
                await self._escalate_appeal(
                    enhanced_appeal,
                    f"No consensus reached by deadline. {reasoning}"
                )

    async def _apply_decision(
        self,
        enhanced_appeal: EnhancedAppeal,
        decision: VoteDecision
    ) -> None:
        """Apply the voting decision"""
        appeal = enhanced_appeal.appeal

        if decision == VoteDecision.APPROVE:
            appeal.status = AppealStatus.APPROVED
            enhanced_appeal.stage = AppealStage.CLOSED

            enhanced_appeal.add_audit_entry("appeal_approved", {
                "voting_rounds": len(enhanced_appeal.voting_rounds),
            })

        elif decision == VoteDecision.DENY:
            appeal.status = AppealStatus.DENIED
            enhanced_appeal.stage = AppealStage.CLOSED

            enhanced_appeal.add_audit_entry("appeal_denied", {
                "voting_rounds": len(enhanced_appeal.voting_rounds),
            })

        elif decision == VoteDecision.NEEDS_MORE_INFO:
            # Request more information from user
            enhanced_appeal.add_audit_entry("more_info_requested", {})

        self.db.update_appeal(appeal)

        logger.info(
            f"Applied decision {decision.value} to appeal {appeal.appeal_id}"
        )

    async def _escalate_appeal(
        self,
        enhanced_appeal: EnhancedAppeal,
        reason: str
    ) -> None:
        """Escalate an appeal to higher authority"""
        enhanced_appeal.escalated = True
        enhanced_appeal.escalation_reason = reason

        enhanced_appeal.add_audit_entry("appeal_escalated", {
            "reason": reason,
        })

        logger.warning(
            f"Appeal {enhanced_appeal.appeal.appeal_id} escalated: {reason}"
        )

        # Notify stakeholders about escalation
        # In production, would send notifications

    async def submit_re_appeal(
        self,
        appeal_id: str,
        additional_evidence: str,
        user_justification: str
    ) -> EnhancedAppeal:
        """
        Submit a re-appeal after denial.

        Args:
            appeal_id: Original appeal ID
            additional_evidence: New evidence provided by user
            user_justification: Why user is re-appealing

        Returns:
            Updated enhanced appeal
        """
        enhanced = self.enhanced_appeals.get(appeal_id)
        if not enhanced:
            raise ValueError(f"Appeal {appeal_id} not found")

        # Check if re-appeal is allowed
        if enhanced.appeal.status != AppealStatus.DENIED:
            raise ValueError("Can only re-appeal denied appeals")

        if enhanced.re_appeal_count >= 2:  # Max 2 re-appeals
            raise ValueError("Maximum re-appeals reached")

        # Update appeal
        enhanced.re_appeal_count += 1
        enhanced.stage = AppealStage.RE_APPEAL
        enhanced.appeal.status = AppealStatus.UNDER_REVIEW

        enhanced.add_audit_entry("re_appeal_submitted", {
            "re_appeal_count": enhanced.re_appeal_count,
            "additional_evidence": additional_evidence[:200],  # Truncate for logging
        })

        # Start new voting round for re-appeal
        await self._start_voting_round(enhanced)

        return enhanced

    def get_voting_statistics(self, appeal_id: str) -> Dict[str, Any]:
        """Get voting statistics for an appeal"""
        enhanced = self.enhanced_appeals.get(appeal_id)
        if not enhanced:
            raise ValueError(f"Appeal {appeal_id} not found")

        stats = {
            "total_rounds": len(enhanced.voting_rounds),
            "current_stage": enhanced.stage.value,
            "escalated": enhanced.escalated,
            "rounds": [],
        }

        for vr in enhanced.voting_rounds:
            round_stats = {
                "round_id": vr.round_id,
                "stage": vr.stage.value,
                "total_votes": len(vr.votes),
                "votes_by_role": {},
                "votes_by_decision": {},
                "quorum_met": vr.quorum_met,
                "consensus_reached": vr.consensus_reached,
                "final_decision": vr.final_decision.value if vr.final_decision else None,
            }

            # Count by role
            for vote in vr.votes:
                role = vote.stakeholder_role.value
                decision = vote.decision.value

                round_stats["votes_by_role"][role] = round_stats["votes_by_role"].get(role, 0) + 1
                round_stats["votes_by_decision"][decision] = round_stats["votes_by_decision"].get(decision, 0) + 1

            stats["rounds"].append(round_stats)

        return stats

    def get_audit_trail(self, appeal_id: str) -> List[Dict[str, Any]]:
        """Get complete audit trail for an appeal"""
        enhanced = self.enhanced_appeals.get(appeal_id)
        if not enhanced:
            raise ValueError(f"Appeal {appeal_id} not found")

        return enhanced.audit_trail
