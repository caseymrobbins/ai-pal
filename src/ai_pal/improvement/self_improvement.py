"""
Self-Improvement Loop

Collects feedback from multiple sources and uses it to improve system behavior:
- User feedback (explicit and implicit)
- Four Gates violations
- ARI/EDM monitoring alerts
- Task performance metrics

Implements continuous improvement through:
- Prompt refinement
- Behavior adjustment
- Parameter tuning
- LoRA fine-tuning (when enough data collected)

Part of Phase 2: Advanced Monitoring & Self-Improvement
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from collections import defaultdict

from loguru import logger


class FeedbackType(Enum):
    """Types of feedback"""
    EXPLICIT_POSITIVE = "explicit_positive"  # User thumbs up
    EXPLICIT_NEGATIVE = "explicit_negative"  # User thumbs down
    IMPLICIT_POSITIVE = "implicit_positive"  # User accepted suggestion
    IMPLICIT_NEGATIVE = "implicit_negative"  # User rejected/ignored
    GATE_VIOLATION = "gate_violation"  # Four Gates failure
    ARI_ALERT = "ari_alert"  # Agency loss detected
    EDM_ALERT = "edm_alert"  # Epistemic debt detected
    PERFORMANCE_METRIC = "performance_metric"  # Task completion metrics


class ImprovementAction(Enum):
    """Types of improvement actions"""
    PROMPT_REFINEMENT = "prompt_refinement"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    BEHAVIOR_CHANGE = "behavior_change"
    FINE_TUNING = "fine_tuning"
    FEATURE_DISABLE = "feature_disable"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


@dataclass
class FeedbackEvent:
    """Single feedback event"""
    feedback_id: str
    timestamp: datetime
    feedback_type: FeedbackType
    source: str  # "user", "four_gates", "ari_monitor", etc.

    # Context
    task_id: str
    user_id: str
    module_name: str  # Which module/component
    action_taken: str  # What the system did
    context: Dict = field(default_factory=dict)

    # Feedback content
    rating: Optional[float] = None  # 0-1 scale
    comment: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ImprovementSuggestion:
    """Suggested improvement based on feedback analysis"""
    suggestion_id: str
    timestamp: datetime
    action_type: ImprovementAction
    target_component: str  # Which component to improve

    # Recommendation
    description: str
    rationale: str
    confidence: float  # 0-1

    # Supporting data
    feedback_count: int
    feedback_ids: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)

    # Status
    approved: bool = False
    implemented: bool = False
    implementation_date: Optional[datetime] = None


@dataclass
class ImprovementReport:
    """Self-improvement system report"""
    period_start: datetime
    period_end: datetime

    # Feedback summary
    total_feedback: int
    feedback_by_type: Dict[str, int]
    positive_feedback_ratio: float

    # Improvements
    suggestions_generated: int
    suggestions_implemented: int
    improvements_by_type: Dict[str, int]

    # Impact
    user_satisfaction_trend: str  # "improving", "stable", "declining"
    gate_violation_trend: str
    ari_trend: str

    # Details
    top_issues: List[Dict] = field(default_factory=list)
    recent_improvements: List[ImprovementSuggestion] = field(default_factory=list)


class SelfImprovementLoop:
    """
    Self-Improvement Loop System

    Continuously collects feedback and generates improvements:
    1. Collect feedback from multiple sources
    2. Analyze patterns and identify issues
    3. Generate improvement suggestions
    4. Implement approved improvements
    5. Monitor impact and adjust

    Implements "learning from mistakes" at system level.
    """

    def __init__(
        self,
        storage_dir: Path,
        auto_implement_threshold: float = 0.9,  # Auto-implement if confidence > this
        min_feedback_for_suggestion: int = 5,
        improvement_check_interval_hours: int = 24
    ):
        """
        Initialize Self-Improvement Loop

        Args:
            storage_dir: Directory for storing feedback and improvements
            auto_implement_threshold: Confidence threshold for auto-implementation
            min_feedback_for_suggestion: Minimum feedback events before suggesting
            improvement_check_interval_hours: How often to check for improvements
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.auto_implement_threshold = auto_implement_threshold
        self.min_feedback_for_suggestion = min_feedback_for_suggestion
        self.improvement_check_interval_hours = improvement_check_interval_hours

        # In-memory storage
        self.feedback_events: Dict[str, FeedbackEvent] = {}
        self.improvement_suggestions: Dict[str, ImprovementSuggestion] = {}

        # Feedback aggregation
        self.feedback_by_component: Dict[str, List[str]] = defaultdict(list)
        self.feedback_by_type: Dict[FeedbackType, List[str]] = defaultdict(list)

        # Load existing data
        self._load_feedback()
        self._load_suggestions()

        logger.info(
            f"Self-Improvement Loop initialized with storage at {storage_dir}, "
            f"auto-implement threshold: {auto_implement_threshold}"
        )

    def _load_feedback(self) -> None:
        """Load existing feedback events"""
        feedback_dir = self.storage_dir / "feedback"
        if not feedback_dir.exists():
            return

        for feedback_file in feedback_dir.glob("*.json"):
            try:
                with open(feedback_file, 'r') as f:
                    data = json.load(f)
                    event = FeedbackEvent(
                        feedback_id=data["feedback_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        feedback_type=FeedbackType(data["feedback_type"]),
                        source=data["source"],
                        task_id=data["task_id"],
                        user_id=data["user_id"],
                        module_name=data["module_name"],
                        action_taken=data["action_taken"],
                        context=data.get("context", {}),
                        rating=data.get("rating"),
                        comment=data.get("comment"),
                        metadata=data.get("metadata", {})
                    )

                    self.feedback_events[event.feedback_id] = event
                    self.feedback_by_component[event.module_name].append(event.feedback_id)
                    self.feedback_by_type[event.feedback_type].append(event.feedback_id)

            except Exception as e:
                logger.error(f"Failed to load feedback {feedback_file}: {e}")

    def _load_suggestions(self) -> None:
        """Load existing improvement suggestions"""
        suggestions_dir = self.storage_dir / "suggestions"
        if not suggestions_dir.exists():
            return

        for suggestion_file in suggestions_dir.glob("*.json"):
            try:
                with open(suggestion_file, 'r') as f:
                    data = json.load(f)
                    suggestion = ImprovementSuggestion(
                        suggestion_id=data["suggestion_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        action_type=ImprovementAction(data["action_type"]),
                        target_component=data["target_component"],
                        description=data["description"],
                        rationale=data["rationale"],
                        confidence=data["confidence"],
                        feedback_count=data["feedback_count"],
                        feedback_ids=data.get("feedback_ids", []),
                        metrics=data.get("metrics", {}),
                        approved=data.get("approved", False),
                        implemented=data.get("implemented", False),
                        implementation_date=datetime.fromisoformat(data["implementation_date"])
                        if data.get("implementation_date") else None
                    )

                    self.improvement_suggestions[suggestion.suggestion_id] = suggestion

            except Exception as e:
                logger.error(f"Failed to load suggestion {suggestion_file}: {e}")

    async def record_feedback(self, event: FeedbackEvent) -> None:
        """
        Record a feedback event

        Args:
            event: Feedback event to record
        """
        # Store in memory
        self.feedback_events[event.feedback_id] = event
        self.feedback_by_component[event.module_name].append(event.feedback_id)
        self.feedback_by_type[event.feedback_type].append(event.feedback_id)

        # Persist to disk
        feedback_dir = self.storage_dir / "feedback"
        feedback_dir.mkdir(exist_ok=True)

        filepath = feedback_dir / f"{event.feedback_id}.json"

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "feedback_id": event.feedback_id,
                    "timestamp": event.timestamp.isoformat(),
                    "feedback_type": event.feedback_type.value,
                    "source": event.source,
                    "task_id": event.task_id,
                    "user_id": event.user_id,
                    "module_name": event.module_name,
                    "action_taken": event.action_taken,
                    "context": event.context,
                    "rating": event.rating,
                    "comment": event.comment,
                    "metadata": event.metadata
                }, f, indent=2)

            logger.debug(
                f"Recorded {event.feedback_type.value} feedback for {event.module_name}"
            )
        except Exception as e:
            logger.error(f"Failed to persist feedback: {e}")

        # Check if we should generate suggestions
        await self._check_for_improvement_opportunities(event.module_name)

    async def _check_for_improvement_opportunities(self, component: str) -> None:
        """Check if component has enough feedback to suggest improvements"""
        feedback_ids = self.feedback_by_component[component]

        if len(feedback_ids) < self.min_feedback_for_suggestion:
            return

        # Get recent feedback (last 30 days)
        cutoff = datetime.now() - timedelta(days=30)
        recent_feedback = [
            self.feedback_events[fid]
            for fid in feedback_ids
            if self.feedback_events[fid].timestamp >= cutoff
        ]

        if len(recent_feedback) < self.min_feedback_for_suggestion:
            return

        # Analyze feedback patterns
        negative_feedback = [
            f for f in recent_feedback
            if f.feedback_type in [
                FeedbackType.EXPLICIT_NEGATIVE,
                FeedbackType.IMPLICIT_NEGATIVE,
                FeedbackType.GATE_VIOLATION,
                FeedbackType.ARI_ALERT,
                FeedbackType.EDM_ALERT
            ]
        ]

        if len(negative_feedback) / len(recent_feedback) > 0.3:  # >30% negative
            # Generate improvement suggestion
            await self._generate_improvement_suggestion(
                component=component,
                recent_feedback=recent_feedback,
                negative_feedback=negative_feedback
            )

    async def _generate_improvement_suggestion(
        self,
        component: str,
        recent_feedback: List[FeedbackEvent],
        negative_feedback: List[FeedbackEvent]
    ) -> None:
        """Generate improvement suggestion based on feedback analysis"""
        suggestion_id = f"imp_{component}_{datetime.now().timestamp()}"

        # Analyze feedback to determine improvement type
        gate_violations = [
            f for f in negative_feedback
            if f.feedback_type == FeedbackType.GATE_VIOLATION
        ]
        ari_alerts = [
            f for f in negative_feedback
            if f.feedback_type == FeedbackType.ARI_ALERT
        ]
        edm_alerts = [
            f for f in negative_feedback
            if f.feedback_type == FeedbackType.EDM_ALERT
        ]

        # Determine action type and description
        if gate_violations:
            action_type = ImprovementAction.BEHAVIOR_CHANGE
            description = f"Modify {component} behavior to prevent Four Gates violations"
            rationale = f"Detected {len(gate_violations)} gate violations in recent feedback"

        elif ari_alerts:
            action_type = ImprovementAction.PARAMETER_ADJUSTMENT
            description = f"Adjust {component} to improve user agency retention"
            rationale = f"Detected {len(ari_alerts)} agency loss alerts"

        elif edm_alerts:
            action_type = ImprovementAction.PROMPT_REFINEMENT
            description = f"Refine {component} prompts to reduce epistemic debt"
            rationale = f"Detected {len(edm_alerts)} epistemic debt instances"

        else:
            action_type = ImprovementAction.PARAMETER_ADJUSTMENT
            description = f"General improvement for {component} based on negative feedback"
            rationale = f"{len(negative_feedback)} negative feedback events"

        # Calculate confidence based on consistency and volume
        consistency = len(negative_feedback) / len(recent_feedback)
        volume_factor = min(1.0, len(negative_feedback) / 20)  # Cap at 20 events
        confidence = (consistency * 0.7 + volume_factor * 0.3)

        suggestion = ImprovementSuggestion(
            suggestion_id=suggestion_id,
            timestamp=datetime.now(),
            action_type=action_type,
            target_component=component,
            description=description,
            rationale=rationale,
            confidence=confidence,
            feedback_count=len(negative_feedback),
            feedback_ids=[f.feedback_id for f in negative_feedback],
            metrics={
                "gate_violations": len(gate_violations),
                "ari_alerts": len(ari_alerts),
                "edm_alerts": len(edm_alerts),
                "negative_ratio": len(negative_feedback) / len(recent_feedback)
            }
        )

        # Store suggestion
        self.improvement_suggestions[suggestion_id] = suggestion
        await self._persist_suggestion(suggestion)

        logger.info(
            f"Generated improvement suggestion for {component}: {description} "
            f"(confidence: {confidence:.2f})"
        )

        # Auto-implement if confidence is high enough
        if confidence >= self.auto_implement_threshold:
            await self.implement_suggestion(suggestion_id, auto=True)

    async def _persist_suggestion(self, suggestion: ImprovementSuggestion) -> None:
        """Persist improvement suggestion to disk"""
        suggestions_dir = self.storage_dir / "suggestions"
        suggestions_dir.mkdir(exist_ok=True)

        filepath = suggestions_dir / f"{suggestion.suggestion_id}.json"

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "suggestion_id": suggestion.suggestion_id,
                    "timestamp": suggestion.timestamp.isoformat(),
                    "action_type": suggestion.action_type.value,
                    "target_component": suggestion.target_component,
                    "description": suggestion.description,
                    "rationale": suggestion.rationale,
                    "confidence": suggestion.confidence,
                    "feedback_count": suggestion.feedback_count,
                    "feedback_ids": suggestion.feedback_ids,
                    "metrics": suggestion.metrics,
                    "approved": suggestion.approved,
                    "implemented": suggestion.implemented,
                    "implementation_date": suggestion.implementation_date.isoformat()
                    if suggestion.implementation_date else None
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist suggestion: {e}")

    async def implement_suggestion(
        self,
        suggestion_id: str,
        auto: bool = False
    ) -> bool:
        """
        Implement an improvement suggestion

        Args:
            suggestion_id: ID of suggestion to implement
            auto: Whether this is auto-implementation

        Returns:
            True if implemented successfully
        """
        if suggestion_id not in self.improvement_suggestions:
            logger.warning(f"Suggestion {suggestion_id} not found")
            return False

        suggestion = self.improvement_suggestions[suggestion_id]

        if suggestion.implemented:
            logger.info(f"Suggestion {suggestion_id} already implemented")
            return True

        # Mark as approved if not already
        if not suggestion.approved:
            suggestion.approved = True

        # Implement based on action type
        success = False

        if suggestion.action_type == ImprovementAction.PROMPT_REFINEMENT:
            success = await self._implement_prompt_refinement(suggestion)

        elif suggestion.action_type == ImprovementAction.PARAMETER_ADJUSTMENT:
            success = await self._implement_parameter_adjustment(suggestion)

        elif suggestion.action_type == ImprovementAction.BEHAVIOR_CHANGE:
            success = await self._implement_behavior_change(suggestion)

        elif suggestion.action_type == ImprovementAction.FINE_TUNING:
            success = await self._implement_fine_tuning(suggestion)

        elif suggestion.action_type == ImprovementAction.FEATURE_DISABLE:
            success = await self._implement_feature_disable(suggestion)

        elif suggestion.action_type == ImprovementAction.HUMAN_REVIEW_REQUIRED:
            logger.warning(
                f"Suggestion {suggestion_id} requires human review: "
                f"{suggestion.description}"
            )
            success = False

        if success:
            suggestion.implemented = True
            suggestion.implementation_date = datetime.now()
            await self._persist_suggestion(suggestion)

            logger.info(
                f"{'Auto-' if auto else ''}Implemented suggestion {suggestion_id}: "
                f"{suggestion.description}"
            )

        return success

    async def _implement_prompt_refinement(self, suggestion: ImprovementSuggestion) -> bool:
        """Implement prompt refinement improvement"""
        # In production, this would update prompt templates
        # For now, just log the action
        logger.info(f"Would refine prompts for {suggestion.target_component}")
        return True

    async def _implement_parameter_adjustment(self, suggestion: ImprovementSuggestion) -> bool:
        """Implement parameter adjustment improvement"""
        # In production, this would adjust model parameters
        logger.info(f"Would adjust parameters for {suggestion.target_component}")
        return True

    async def _implement_behavior_change(self, suggestion: ImprovementSuggestion) -> bool:
        """Implement behavior change improvement"""
        # In production, this would modify behavior policies
        logger.info(f"Would change behavior for {suggestion.target_component}")
        return True

    async def _implement_fine_tuning(self, suggestion: ImprovementSuggestion) -> bool:
        """Implement fine-tuning improvement"""
        # In production, this would trigger LoRA fine-tuning
        logger.info(f"Would fine-tune model for {suggestion.target_component}")
        return True

    async def _implement_feature_disable(self, suggestion: ImprovementSuggestion) -> bool:
        """Implement feature disable improvement"""
        # In production, this would disable problematic features
        logger.warning(f"Would disable feature: {suggestion.target_component}")
        return True

    def generate_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ImprovementReport:
        """Generate improvement report"""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Filter feedback to date range
        period_feedback = [
            f for f in self.feedback_events.values()
            if start_date <= f.timestamp <= end_date
        ]

        # Feedback summary
        total_feedback = len(period_feedback)

        feedback_by_type = {}
        for ftype in FeedbackType:
            feedback_by_type[ftype.value] = sum(
                1 for f in period_feedback if f.feedback_type == ftype
            )

        positive_count = sum(
            1 for f in period_feedback
            if f.feedback_type in [
                FeedbackType.EXPLICIT_POSITIVE,
                FeedbackType.IMPLICIT_POSITIVE
            ]
        )
        positive_ratio = (positive_count / total_feedback) if total_feedback > 0 else 0.0

        # Suggestions
        period_suggestions = [
            s for s in self.improvement_suggestions.values()
            if start_date <= s.timestamp <= end_date
        ]

        suggestions_generated = len(period_suggestions)
        suggestions_implemented = sum(1 for s in period_suggestions if s.implemented)

        improvements_by_type = {}
        for atype in ImprovementAction:
            improvements_by_type[atype.value] = sum(
                1 for s in period_suggestions
                if s.action_type == atype and s.implemented
            )

        # Trends (simplified - would need historical data for real trends)
        if positive_ratio > 0.7:
            satisfaction_trend = "improving"
        elif positive_ratio > 0.5:
            satisfaction_trend = "stable"
        else:
            satisfaction_trend = "declining"

        gate_violations = feedback_by_type.get(FeedbackType.GATE_VIOLATION.value, 0)
        gate_trend = "improving" if gate_violations < 5 else "stable"

        ari_alerts = feedback_by_type.get(FeedbackType.ARI_ALERT.value, 0)
        ari_trend = "improving" if ari_alerts < 3 else "stable"

        # Top issues
        component_issues = defaultdict(int)
        for f in period_feedback:
            if f.feedback_type in [
                FeedbackType.EXPLICIT_NEGATIVE,
                FeedbackType.GATE_VIOLATION,
                FeedbackType.ARI_ALERT,
                FeedbackType.EDM_ALERT
            ]:
                component_issues[f.module_name] += 1

        top_issues = [
            {"component": comp, "issue_count": count}
            for comp, count in sorted(component_issues.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Recent improvements
        recent_improvements = sorted(
            [s for s in period_suggestions if s.implemented],
            key=lambda x: x.implementation_date or x.timestamp,
            reverse=True
        )[:10]

        return ImprovementReport(
            period_start=start_date,
            period_end=end_date,
            total_feedback=total_feedback,
            feedback_by_type=feedback_by_type,
            positive_feedback_ratio=positive_ratio,
            suggestions_generated=suggestions_generated,
            suggestions_implemented=suggestions_implemented,
            improvements_by_type=improvements_by_type,
            user_satisfaction_trend=satisfaction_trend,
            gate_violation_trend=gate_trend,
            ari_trend=ari_trend,
            top_issues=top_issues,
            recent_improvements=recent_improvements
        )
