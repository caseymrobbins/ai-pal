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


class ABTestStatus(Enum):
    """A/B test status"""
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantType(Enum):
    """Types of variants in A/B tests"""
    CONTROL = "control"  # Current implementation
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


@dataclass
class ABTestVariant:
    """Single variant in an A/B test"""
    variant_id: str
    variant_type: VariantType
    description: str

    # Configuration for this variant
    configuration: Dict  # Prompts, parameters, etc.

    # Metrics
    samples: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    total_cost: float = 0.0
    user_satisfaction_score: float = 0.0  # 0-1
    gate_violation_count: int = 0

    # Statistical
    confidence_interval: Tuple[float, float] = (0.0, 1.0)
    is_statistically_significant: bool = False


@dataclass
class ABTest:
    """A/B test for comparing improvement variants"""
    test_id: str
    component: str
    started_at: datetime
    status: ABTestStatus

    # Variants
    control: ABTestVariant
    variants: List[ABTestVariant]

    # Test configuration
    min_samples_per_variant: int = 100
    max_duration_hours: int = 168  # 1 week
    confidence_level: float = 0.95

    # Results
    winner: Optional[str] = None  # variant_id of winning variant
    completed_at: Optional[datetime] = None
    conclusion: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for a component or improvement"""
    component: str
    period_start: datetime
    period_end: datetime

    # Success metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 0.0

    # Performance
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    # Cost
    total_cost: float = 0.0
    average_cost_per_request: float = 0.0

    # Quality
    user_satisfaction: float = 0.0  # 0-1
    gate_violation_rate: float = 0.0
    ari_alert_rate: float = 0.0
    edm_alert_rate: float = 0.0

    # Trends (vs previous period)
    success_rate_delta: float = 0.0
    latency_delta: float = 0.0
    satisfaction_delta: float = 0.0


@dataclass
class LoRATrainingConfig:
    """Configuration for LoRA fine-tuning"""
    model_name: str
    target_component: str

    # Training data
    training_samples: int
    validation_samples: int
    data_sources: List[str]

    # LoRA parameters
    rank: int = 8  # LoRA rank
    alpha: int = 16  # LoRA alpha
    dropout: float = 0.05

    # Training parameters
    learning_rate: float = 3e-4
    batch_size: int = 4
    num_epochs: int = 3
    warmup_steps: int = 100

    # Constraints
    max_training_time_hours: int = 24
    max_cost: float = 50.0


@dataclass
class LoRATrainingRun:
    """Record of a LoRA fine-tuning run"""
    run_id: str
    config: LoRATrainingConfig
    started_at: datetime

    # Status
    status: str  # "running", "completed", "failed"
    progress: float = 0.0  # 0-1

    # Results
    final_loss: Optional[float] = None
    validation_accuracy: Optional[float] = None
    training_cost: Optional[float] = None
    completed_at: Optional[datetime] = None

    # Model artifact
    model_path: Optional[Path] = None
    checkpoint_paths: List[Path] = field(default_factory=list)

    # Performance (before/after)
    baseline_metrics: Optional[PerformanceMetrics] = None
    post_tuning_metrics: Optional[PerformanceMetrics] = None


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


class ImprovementStatus(Enum):
    """Status of an improvement suggestion"""
    PENDING = "pending"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"


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

        # Phase 4.2: A/B testing (Advanced Self-Improvement)
        self.ab_tests: Dict[str, ABTest] = {}
        self.active_tests_by_component: Dict[str, str] = {}  # component -> test_id

        # Phase 4.2: Performance tracking
        self.performance_data: Dict[str, List[Dict]] = defaultdict(list)  # component -> [metrics]

        # Phase 4.2: LoRA fine-tuning
        self.lora_training_runs: Dict[str, LoRATrainingRun] = {}
        self.fine_tuned_models: Dict[str, Path] = {}  # component -> model_path

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

    # ==================== Phase 4.2: A/B Testing ====================

    async def start_ab_test(
        self,
        component: str,
        control_config: Dict,
        variant_configs: List[Dict],
        min_samples: int = 100,
        max_duration_hours: int = 168
    ) -> ABTest:
        """
        Start A/B test for comparing improvement variants

        Args:
            component: Component to test
            control_config: Configuration for control (current implementation)
            variant_configs: List of variant configurations to test
            min_samples: Minimum samples per variant
            max_duration_hours: Maximum test duration

        Returns:
            Created AB test
        """
        test_id = f"abtest_{component}_{datetime.now().timestamp()}"

        # Create control variant
        control = ABTestVariant(
            variant_id=f"{test_id}_control",
            variant_type=VariantType.CONTROL,
            description="Current implementation (control)",
            configuration=control_config
        )

        # Create test variants
        variant_types = [VariantType.VARIANT_A, VariantType.VARIANT_B, VariantType.VARIANT_C]
        variants = []

        for i, config in enumerate(variant_configs[:3]):  # Max 3 variants
            variant = ABTestVariant(
                variant_id=f"{test_id}_{variant_types[i].value}",
                variant_type=variant_types[i],
                description=config.get("description", f"Variant {chr(65+i)}"),
                configuration=config
            )
            variants.append(variant)

        # Create test
        test = ABTest(
            test_id=test_id,
            component=component,
            started_at=datetime.now(),
            status=ABTestStatus.RUNNING,
            control=control,
            variants=variants,
            min_samples_per_variant=min_samples,
            max_duration_hours=max_duration_hours
        )

        self.ab_tests[test_id] = test
        self.active_tests_by_component[component] = test_id

        logger.info(
            f"Started A/B test {test_id} for {component} "
            f"with {len(variants)} variants, min samples: {min_samples}"
        )

        return test

    async def record_ab_test_sample(
        self,
        test_id: str,
        variant_id: str,
        success: bool,
        latency_ms: float,
        cost: float,
        user_satisfaction: Optional[float] = None,
        gate_violation: bool = False
    ) -> None:
        """
        Record a sample for A/B test variant

        Args:
            test_id: A/B test ID
            variant_id: Variant that was used
            success: Whether the request succeeded
            latency_ms: Request latency
            cost: Request cost
            user_satisfaction: Optional user satisfaction score (0-1)
            gate_violation: Whether a gate was violated
        """
        if test_id not in self.ab_tests:
            logger.warning(f"A/B test {test_id} not found")
            return

        test = self.ab_tests[test_id]

        # Find variant
        variant = None
        if test.control.variant_id == variant_id:
            variant = test.control
        else:
            for v in test.variants:
                if v.variant_id == variant_id:
                    variant = v
                    break

        if not variant:
            logger.warning(f"Variant {variant_id} not found in test {test_id}")
            return

        # Update metrics
        variant.samples += 1
        if success:
            variant.success_count += 1
        else:
            variant.failure_count += 1

        variant.total_latency_ms += latency_ms
        variant.total_cost += cost

        if user_satisfaction is not None:
            # Running average
            variant.user_satisfaction_score = (
                (variant.user_satisfaction_score * (variant.samples - 1) + user_satisfaction)
                / variant.samples
            )

        if gate_violation:
            variant.gate_violation_count += 1

        # Check if test should complete
        await self._check_ab_test_completion(test_id)

    async def _check_ab_test_completion(self, test_id: str) -> None:
        """Check if A/B test has enough data to conclude"""
        test = self.ab_tests[test_id]

        if test.status != ABTestStatus.RUNNING:
            return

        # Check if minimum samples reached
        all_variants = [test.control] + test.variants
        min_samples_reached = all(
            v.samples >= test.min_samples_per_variant
            for v in all_variants
        )

        # Check if max duration exceeded
        duration_hours = (datetime.now() - test.started_at).total_seconds() / 3600
        max_duration_exceeded = duration_hours >= test.max_duration_hours

        if min_samples_reached or max_duration_exceeded:
            await self._complete_ab_test(test_id)

    async def _complete_ab_test(self, test_id: str) -> None:
        """Complete A/B test and determine winner"""
        test = self.ab_tests[test_id]

        # Calculate success rates
        all_variants = [test.control] + test.variants

        for variant in all_variants:
            if variant.samples > 0:
                success_rate = variant.success_count / variant.samples
                avg_latency = variant.total_latency_ms / variant.samples
                avg_cost = variant.total_cost / variant.samples

                # Simple statistical significance check (Z-test approximation)
                # In production, would use proper statistical tests
                variant.is_statistically_significant = variant.samples >= test.min_samples_per_variant

                logger.info(
                    f"Variant {variant.variant_type.value}: "
                    f"success_rate={success_rate:.2%}, "
                    f"avg_latency={avg_latency:.0f}ms, "
                    f"avg_cost=${avg_cost:.4f}, "
                    f"satisfaction={variant.user_satisfaction_score:.2f}"
                )

        # Determine winner (highest success rate with statistical significance)
        significant_variants = [v for v in all_variants if v.is_statistically_significant]

        if significant_variants:
            winner = max(
                significant_variants,
                key=lambda v: (
                    v.success_count / v.samples if v.samples > 0 else 0,
                    v.user_satisfaction_score,
                    -v.total_cost / v.samples if v.samples > 0 else float('inf')
                )
            )

            test.winner = winner.variant_id
            test.conclusion = (
                f"Winner: {winner.variant_type.value} with "
                f"{winner.success_count/winner.samples:.1%} success rate"
            )

            logger.info(f"A/B test {test_id} completed: {test.conclusion}")
        else:
            test.conclusion = "Inconclusive - insufficient samples"
            logger.warning(f"A/B test {test_id} inconclusive")

        test.status = ABTestStatus.COMPLETED
        test.completed_at = datetime.now()

        # Remove from active tests
        if test.component in self.active_tests_by_component:
            del self.active_tests_by_component[test.component]

    # ==================== Phase 4.2: Performance Tracking ====================

    async def record_performance_metric(
        self,
        component: str,
        success: bool,
        latency_ms: float,
        cost: float,
        user_satisfaction: Optional[float] = None,
        gate_violation: bool = False,
        ari_alert: bool = False,
        edm_alert: bool = False
    ) -> None:
        """
        Record performance metric for a component

        Args:
            component: Component name
            success: Whether request succeeded
            latency_ms: Request latency
            cost: Request cost
            user_satisfaction: User satisfaction score (0-1)
            gate_violation: Gate violation occurred
            ari_alert: ARI alert triggered
            edm_alert: EDM alert triggered
        """
        metric = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "latency_ms": latency_ms,
            "cost": cost,
            "user_satisfaction": user_satisfaction,
            "gate_violation": gate_violation,
            "ari_alert": ari_alert,
            "edm_alert": edm_alert
        }

        self.performance_data[component].append(metric)

        # Keep only last 10,000 metrics per component
        if len(self.performance_data[component]) > 10000:
            self.performance_data[component] = self.performance_data[component][-10000:]

    async def get_performance_metrics(
        self,
        component: str,
        period_hours: int = 24
    ) -> PerformanceMetrics:
        """
        Get performance metrics for a component

        Args:
            component: Component name
            period_hours: Time period in hours

        Returns:
            Performance metrics
        """
        cutoff = datetime.now() - timedelta(hours=period_hours)
        period_start = cutoff
        period_end = datetime.now()

        # Filter metrics to period
        period_metrics = [
            m for m in self.performance_data.get(component, [])
            if datetime.fromisoformat(m["timestamp"]) >= cutoff
        ]

        if not period_metrics:
            return PerformanceMetrics(
                component=component,
                period_start=period_start,
                period_end=period_end
            )

        # Calculate metrics
        total_requests = len(period_metrics)
        successful_requests = sum(1 for m in period_metrics if m["success"])
        failed_requests = total_requests - successful_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0

        # Latency
        latencies = [m["latency_ms"] for m in period_metrics]
        latencies.sort()
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_index = int(len(latencies) * 0.95)
        p99_index = int(len(latencies) * 0.99)
        p95_latency = latencies[p95_index] if p95_index < len(latencies) else 0.0
        p99_latency = latencies[p99_index] if p99_index < len(latencies) else 0.0

        # Cost
        total_cost = sum(m["cost"] for m in period_metrics)
        avg_cost = total_cost / total_requests if total_requests > 0 else 0.0

        # Quality
        satisfaction_scores = [m["user_satisfaction"] for m in period_metrics if m["user_satisfaction"] is not None]
        user_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0.0

        gate_violations = sum(1 for m in period_metrics if m.get("gate_violation", False))
        ari_alerts = sum(1 for m in period_metrics if m.get("ari_alert", False))
        edm_alerts = sum(1 for m in period_metrics if m.get("edm_alert", False))

        gate_violation_rate = gate_violations / total_requests if total_requests > 0 else 0.0
        ari_alert_rate = ari_alerts / total_requests if total_requests > 0 else 0.0
        edm_alert_rate = edm_alerts / total_requests if total_requests > 0 else 0.0

        return PerformanceMetrics(
            component=component,
            period_start=period_start,
            period_end=period_end,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            average_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            total_cost=total_cost,
            average_cost_per_request=avg_cost,
            user_satisfaction=user_satisfaction,
            gate_violation_rate=gate_violation_rate,
            ari_alert_rate=ari_alert_rate,
            edm_alert_rate=edm_alert_rate
        )

    # ==================== Phase 4.2: LoRA Fine-Tuning ====================

    async def initiate_lora_training(
        self,
        component: str,
        model_name: str,
        min_training_samples: int = 1000
    ) -> Optional[LoRATrainingRun]:
        """
        Initiate LoRA fine-tuning for a component

        Args:
            component: Component to fine-tune
            model_name: Base model to fine-tune
            min_training_samples: Minimum samples required

        Returns:
            Training run if initiated, None if insufficient data
        """
        # Check if we have enough positive/negative feedback for training
        component_feedback = self.feedback_by_component.get(component, [])

        if len(component_feedback) < min_training_samples:
            logger.info(
                f"Insufficient training data for {component}: "
                f"{len(component_feedback)}/{min_training_samples}"
            )
            return None

        # Create training config
        training_samples = int(len(component_feedback) * 0.8)  # 80% train
        validation_samples = len(component_feedback) - training_samples  # 20% val

        config = LoRATrainingConfig(
            model_name=model_name,
            target_component=component,
            training_samples=training_samples,
            validation_samples=validation_samples,
            data_sources=[f"feedback_{component}"]
        )

        # Create training run
        run_id = f"lora_{component}_{datetime.now().timestamp()}"

        training_run = LoRATrainingRun(
            run_id=run_id,
            config=config,
            started_at=datetime.now(),
            status="running"
        )

        self.lora_training_runs[run_id] = training_run

        # Get baseline metrics before training
        training_run.baseline_metrics = await self.get_performance_metrics(component)

        logger.info(
            f"Initiated LoRA training {run_id} for {component} "
            f"({training_samples} train, {validation_samples} val samples)"
        )

        # In production, this would trigger actual LoRA training
        # For now, simulate completion
        await self._simulate_lora_training(run_id)

        return training_run

    async def _simulate_lora_training(self, run_id: str) -> None:
        """Simulate LoRA training completion (placeholder for actual training)"""
        training_run = self.lora_training_runs[run_id]

        # Simulate training progress
        for progress in [0.25, 0.5, 0.75, 1.0]:
            await asyncio.sleep(0.1)  # Simulate time
            training_run.progress = progress

        # Simulate results
        training_run.status = "completed"
        training_run.final_loss = 0.15
        training_run.validation_accuracy = 0.92
        training_run.training_cost = 15.50
        training_run.completed_at = datetime.now()

        # Store model path (simulated)
        model_dir = self.storage_dir / "lora_models"
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / f"{run_id}.pt"
        training_run.model_path = model_path

        # Register as fine-tuned model
        self.fine_tuned_models[training_run.config.target_component] = model_path

        logger.info(
            f"LoRA training {run_id} completed: "
            f"loss={training_run.final_loss:.3f}, "
            f"accuracy={training_run.validation_accuracy:.2%}, "
            f"cost=${training_run.training_cost:.2f}"
        )
