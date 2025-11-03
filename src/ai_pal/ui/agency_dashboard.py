"""
Agency Dashboard - Phase 3

User-facing transparency dashboard providing:
- Real-time agency metrics and trends
- Privacy budget visualization
- Consent management interface
- Model selection explanations
- Epistemic debt reports
- Self-improvement actions
- Historical performance analytics

This provides a UI-agnostic backend that generates dashboard data
for various frontends (web, CLI, desktop app, etc.)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from loguru import logger

# Import monitoring systems
from ..monitoring.ari_monitor import ARIMonitor, AgencyTrend
from ..monitoring.edm_monitor import EDMMonitor, DebtSeverity
from ..monitoring.ari_engine import ARIEngine, ARISignalLevel
from ..monitoring.rdi_monitor import RDIMonitor, RDILevel
from ..improvement.self_improvement import SelfImprovementLoop, ImprovementStatus
from ..privacy.advanced_privacy import AdvancedPrivacyManager, ConsentLevel
from ..orchestration.multi_model import MultiModelOrchestrator, ModelProvider
from ..context.enhanced_context import EnhancedContextManager


class DashboardSection(Enum):
    """Dashboard sections"""
    OVERVIEW = "overview"
    AGENCY_METRICS = "agency_metrics"
    ARI_ENGINE = "ari_engine"  # NEW: Skill atrophy detection
    RDI_MONITOR = "rdi_monitor"  # NEW: Reality drift detection (PRIVATE)
    PRIVACY_STATUS = "privacy_status"
    MODEL_USAGE = "model_usage"
    EPISTEMIC_DEBT = "epistemic_debt"
    IMPROVEMENTS = "improvements"
    CONTEXT_MEMORY = "context_memory"


@dataclass
class AgencyMetrics:
    """Current agency metrics for dashboard"""
    # Current values
    current_delta_agency: float
    current_bhir: float
    current_skill_level: float
    current_ai_reliance: float

    # Trends (over reporting period)
    agency_trend: AgencyTrend
    skill_trend: str  # "improving", "stable", "declining"
    dependency_trend: str  # "decreasing", "stable", "increasing"

    # Alerts
    active_alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Historical data points (timestamp, value)
    delta_agency_history: List[tuple] = field(default_factory=list)
    bhir_history: List[tuple] = field(default_factory=list)
    skill_history: List[tuple] = field(default_factory=list)


@dataclass
class PrivacyStatus:
    """Privacy status for dashboard"""
    # Consent level
    consent_level: ConsentLevel
    consent_granted_date: Optional[datetime]
    consent_expiry_date: Optional[datetime]

    # Privacy budget
    epsilon_spent: float
    epsilon_limit: float
    epsilon_percentage: float
    queries_made: int
    queries_limit: int
    queries_percentage: float
    budget_reset_date: datetime

    # PII detections
    pii_detections_today: int
    pii_detections_total: int

    # Data minimization
    data_retention_days: int
    auto_deletion_enabled: bool

    # Optional fields with defaults
    pii_actions_taken: Dict[str, int] = field(default_factory=dict)  # action -> count

    # Alerts
    budget_near_limit: bool = False
    consent_expiring_soon: bool = False


@dataclass
class ModelUsageStats:
    """Model usage statistics for dashboard"""
    # Current session
    current_model: Optional[str]
    current_provider: Optional[ModelProvider]

    # Usage breakdown
    total_requests: int

    # Cost tracking
    total_cost: float
    estimated_cost_savings: float  # vs always using most expensive model

    # Performance
    average_latency_ms: float
    average_quality_score: float
    success_rate: float

    # Optional fields with defaults
    requests_by_provider: Dict[ModelProvider, int] = field(default_factory=dict)
    requests_by_model: Dict[str, int] = field(default_factory=dict)
    cost_by_provider: Dict[ModelProvider, float] = field(default_factory=dict)
    recent_selections: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EpistemicDebtStatus:
    """Epistemic debt status for dashboard"""
    # Current debt levels
    total_active_debts: int

    # Resolution stats
    total_resolved: int
    total_disputed: int
    resolution_rate: float

    # Trends
    debt_trend: str  # "improving", "stable", "worsening"

    # Optional fields with defaults
    debts_by_severity: Dict[DebtSeverity, int] = field(default_factory=dict)
    debts_by_type: Dict[str, int] = field(default_factory=dict)

    # Recent debts
    recent_debts: List[Dict[str, Any]] = field(default_factory=list)

    # Alerts
    high_severity_count: int = 0
    critical_alerts: List[str] = field(default_factory=list)


@dataclass
class ImprovementActivity:
    """Self-improvement activity for dashboard"""
    # Recent improvements
    total_improvements: int
    pending_count: int
    approved_count: int
    implemented_count: int
    rejected_count: int

    # Impact tracking
    average_confidence: float

    # User feedback integration
    user_feedback_count: int
    gate_violation_count: int
    ari_alert_count: int

    # Optional fields with defaults
    # Recent actions
    recent_improvements: List[Dict[str, Any]] = field(default_factory=list)
    improvements_by_component: Dict[str, int] = field(default_factory=dict)


@dataclass
class ContextMemoryStatus:
    """Context memory status for dashboard"""
    # Memory stats
    total_memories: int

    # Storage
    total_tokens: int
    max_tokens: int
    utilization_percentage: float

    # Consolidation
    last_consolidation: Optional[datetime]
    unconsolidated_count: int
    needs_consolidation: bool

    # Optional fields with defaults
    memories_by_type: Dict[str, int] = field(default_factory=dict)
    memories_by_priority: Dict[str, int] = field(default_factory=dict)

    # Recent memories
    recent_memories: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ARIEngineStatus:
    """ARI Engine status for dashboard"""
    # Overall ARI score
    overall_ari: float  # 0-1, where 1 is best
    signal_level: str  # "high", "medium", "low", "critical"

    # Component scores
    lexical_ari: float  # From passive text analysis
    interaction_ari: float  # From Socratic co-pilot
    baseline_deviation: float  # Deviation from deep dive baseline

    # Trend analysis
    trend_direction: str  # "improving", "stable", "declining"
    days_in_trend: int

    # Alerts and recommendations
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Historical data (timestamp, ari_score)
    ari_history: List[tuple] = field(default_factory=list)

    # Recent UCC responses (capability checkpoints)
    recent_uccs: List[Dict[str, Any]] = field(default_factory=list)

    # Deep dive baseline status
    has_baseline: bool = False
    baseline_domain: Optional[str] = None
    baseline_established_at: Optional[datetime] = None


@dataclass
class RDIMonitorStatus:
    """
    RDI Monitor status for dashboard

    **PRIVACY:** This data is PRIVATE and shown only to the user.
    Never shared with platform or third parties.
    """
    # Overall RDI score
    overall_rdi: float  # 0-1, where 0 is aligned, 1 is maximum drift
    rdi_level: str  # "aligned", "minor_drift", "moderate_drift", "significant_drift", "critical_drift"

    # Component scores
    semantic_drift: float  # Semantic understanding drift
    factual_drift: float  # Factual baseline drift
    logical_drift: float  # Logical reasoning drift

    # Trend analysis
    trend_direction: str  # "stable", "increasing", "decreasing"

    # Private alerts (shown only to user)
    private_alerts: List[str] = field(default_factory=list)

    # Historical data (timestamp, rdi_score)
    rdi_history: List[tuple] = field(default_factory=list)

    # Privacy notice
    privacy_notice: str = "This data is private and stored only on your device."

    # Aggregate opt-in status
    opted_into_aggregates: bool = False


@dataclass
class DashboardData:
    """Complete dashboard data"""
    user_id: str
    generated_at: datetime
    reporting_period_days: int

    # Section data
    agency_metrics: AgencyMetrics
    ari_engine_status: Optional[ARIEngineStatus] = None  # NEW: Skill atrophy detection
    rdi_monitor_status: Optional[RDIMonitorStatus] = None  # NEW: Reality drift (PRIVATE)
    privacy_status: PrivacyStatus = None
    model_usage: ModelUsageStats = None
    epistemic_debt: EpistemicDebtStatus = None
    improvements: ImprovementActivity = None
    context_memory: ContextMemoryStatus = None

    # Overall health score (0-100)
    overall_health_score: float = 0.0

    # System alerts (high priority)
    system_alerts: List[str] = field(default_factory=list)


class AgencyDashboard:
    """
    Agency-Centric Dashboard

    Provides comprehensive transparency into AI system behavior,
    user agency metrics, privacy status, and improvement activities.

    This is the primary user interface for understanding how the AI
    is impacting their agency, skills, and autonomy.
    """

    def __init__(
        self,
        ari_monitor: ARIMonitor,
        edm_monitor: EDMMonitor,
        improvement_loop: SelfImprovementLoop,
        privacy_manager: AdvancedPrivacyManager,
        orchestrator: MultiModelOrchestrator,
        context_manager: EnhancedContextManager,
        reporting_period_days: int = 7,
        ari_engine: Optional[ARIEngine] = None,  # NEW: Multi-layered skill atrophy detection
        rdi_monitor: Optional[RDIMonitor] = None  # NEW: Privacy-first reality drift detection
    ):
        """
        Initialize Agency Dashboard

        Args:
            ari_monitor: Agency Retention Index monitor
            edm_monitor: Epistemic Debt monitor
            improvement_loop: Self-improvement loop
            privacy_manager: Privacy manager
            orchestrator: Multi-model orchestrator
            context_manager: Context manager
            reporting_period_days: Default reporting period
            ari_engine: Optional ARI Engine for skill atrophy detection
            rdi_monitor: Optional RDI Monitor for reality drift detection
        """
        self.ari_monitor = ari_monitor
        self.edm_monitor = edm_monitor
        self.improvement_loop = improvement_loop
        self.privacy_manager = privacy_manager
        self.orchestrator = orchestrator
        self.context_manager = context_manager
        self.reporting_period_days = reporting_period_days
        self.ari_engine = ari_engine
        self.rdi_monitor = rdi_monitor

        logger.info(
            f"Agency Dashboard initialized with {reporting_period_days}-day reporting period"
        )
        if ari_engine:
            logger.info("ARI Engine integration enabled")
        if rdi_monitor:
            logger.info("RDI Monitor integration enabled (privacy-first)")

    async def generate_dashboard(
        self,
        user_id: str,
        sections: Optional[List[DashboardSection]] = None,
        period_days: Optional[int] = None
    ) -> DashboardData:
        """
        Generate complete dashboard data

        Args:
            user_id: User to generate dashboard for
            sections: Specific sections to include (None = all)
            period_days: Reporting period override

        Returns:
            Complete dashboard data
        """
        period = period_days or self.reporting_period_days

        # If no sections specified, include all
        if sections is None:
            sections = list(DashboardSection)

        logger.info(f"Generating dashboard for user {user_id}, period: {period} days")

        # Generate each section in parallel
        tasks = []
        section_data = {}

        if DashboardSection.AGENCY_METRICS in sections:
            tasks.append(self._generate_agency_metrics(user_id, period))

        if DashboardSection.ARI_ENGINE in sections and self.ari_engine:
            tasks.append(self._generate_ari_engine_status(user_id, period))

        if DashboardSection.RDI_MONITOR in sections and self.rdi_monitor:
            tasks.append(self._generate_rdi_monitor_status(user_id, period))

        if DashboardSection.PRIVACY_STATUS in sections:
            tasks.append(self._generate_privacy_status(user_id))

        if DashboardSection.MODEL_USAGE in sections:
            tasks.append(self._generate_model_usage(user_id, period))

        if DashboardSection.EPISTEMIC_DEBT in sections:
            tasks.append(self._generate_epistemic_debt(user_id, period))

        if DashboardSection.IMPROVEMENTS in sections:
            tasks.append(self._generate_improvements(user_id, period))

        if DashboardSection.CONTEXT_MEMORY in sections:
            tasks.append(self._generate_context_memory(user_id))

        # Execute all section generation in parallel
        results = await asyncio.gather(*tasks)

        # Map results to sections
        result_idx = 0
        agency_metrics = None
        ari_engine_status = None
        rdi_monitor_status = None
        privacy_status = None
        model_usage = None
        epistemic_debt = None
        improvements = None
        context_memory = None

        if DashboardSection.AGENCY_METRICS in sections:
            agency_metrics = results[result_idx]
            result_idx += 1

        if DashboardSection.ARI_ENGINE in sections and self.ari_engine:
            ari_engine_status = results[result_idx]
            result_idx += 1

        if DashboardSection.RDI_MONITOR in sections and self.rdi_monitor:
            rdi_monitor_status = results[result_idx]
            result_idx += 1

        if DashboardSection.PRIVACY_STATUS in sections:
            privacy_status = results[result_idx]
            result_idx += 1

        if DashboardSection.MODEL_USAGE in sections:
            model_usage = results[result_idx]
            result_idx += 1

        if DashboardSection.EPISTEMIC_DEBT in sections:
            epistemic_debt = results[result_idx]
            result_idx += 1

        if DashboardSection.IMPROVEMENTS in sections:
            improvements = results[result_idx]
            result_idx += 1

        if DashboardSection.CONTEXT_MEMORY in sections:
            context_memory = results[result_idx]
            result_idx += 1

        # Calculate overall health score
        health_score = self._calculate_health_score(
            agency_metrics,
            privacy_status,
            epistemic_debt
        )

        # Collect system alerts
        system_alerts = []
        if agency_metrics and agency_metrics.agency_trend == AgencyTrend.CRITICAL:
            system_alerts.append("🚨 CRITICAL: Severe agency loss detected")

        if ari_engine_status and ari_engine_status.signal_level == "critical":
            system_alerts.append("🚨 CRITICAL: Severe skill atrophy detected")
        elif ari_engine_status and ari_engine_status.signal_level == "low":
            system_alerts.append("⚠️ LOW ARI: Skill retention concerns detected")

        if rdi_monitor_status and rdi_monitor_status.rdi_level in ["significant_drift", "critical_drift"]:
            system_alerts.append("⚠️ Reality drift detected (Private alert)")

        if privacy_status and privacy_status.budget_near_limit:
            system_alerts.append("⚠️ Privacy budget near limit")

        if epistemic_debt and epistemic_debt.high_severity_count > 0:
            system_alerts.extend(epistemic_debt.critical_alerts)

        dashboard = DashboardData(
            user_id=user_id,
            generated_at=datetime.now(),
            reporting_period_days=period,
            agency_metrics=agency_metrics,
            ari_engine_status=ari_engine_status,
            rdi_monitor_status=rdi_monitor_status,
            privacy_status=privacy_status,
            model_usage=model_usage,
            epistemic_debt=epistemic_debt,
            improvements=improvements,
            context_memory=context_memory,
            overall_health_score=health_score,
            system_alerts=system_alerts
        )

        logger.info(
            f"Dashboard generated for {user_id}: "
            f"health={health_score:.1f}, alerts={len(system_alerts)}"
        )

        return dashboard

    async def _generate_agency_metrics(
        self,
        user_id: str,
        period_days: int
    ) -> AgencyMetrics:
        """Generate agency metrics section"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Get ARI report
        report = self.ari_monitor.generate_report(user_id, start_date, end_date)

        # Get historical snapshots for charts
        if user_id in self.ari_monitor.snapshots:
            snapshots = [
                s for s in self.ari_monitor.snapshots[user_id]
                if start_date <= s.timestamp <= end_date
            ]

            delta_agency_history = [
                (s.timestamp.isoformat(), s.delta_agency)
                for s in snapshots
            ]
            bhir_history = [
                (s.timestamp.isoformat(), s.bhir)
                for s in snapshots
            ]
            skill_history = [
                (s.timestamp.isoformat(), s.user_skill_after)
                for s in snapshots
            ]

            # Get most recent values
            latest = snapshots[-1] if snapshots else None
            current_delta = latest.delta_agency if latest else 0.0
            current_bhir = latest.bhir if latest else 0.0
            current_skill = latest.user_skill_after if latest else 0.0
            current_reliance = latest.ai_reliance if latest else 0.0
        else:
            delta_agency_history = []
            bhir_history = []
            skill_history = []
            current_delta = 0.0
            current_bhir = 0.0
            current_skill = 0.0
            current_reliance = 0.0

        return AgencyMetrics(
            current_delta_agency=current_delta,
            current_bhir=current_bhir,
            current_skill_level=current_skill,
            current_ai_reliance=current_reliance,
            agency_trend=report.agency_trend,
            skill_trend=report.skill_trend,
            dependency_trend=report.dependency_trend,
            active_alerts=report.alerts,
            recommendations=report.recommendations,
            delta_agency_history=delta_agency_history,
            bhir_history=bhir_history,
            skill_history=skill_history
        )

    async def _generate_privacy_status(self, user_id: str) -> PrivacyStatus:
        """Generate privacy status section"""
        # Get consent record
        consent = self.privacy_manager.consent_records.get(user_id)

        # Get privacy budget
        budget = self.privacy_manager.privacy_budgets.get(user_id)

        # Get PII detection stats
        pii_count_today = 0
        pii_count_total = 0
        pii_actions = {}

        if user_id in self.privacy_manager.pii_detections:
            detections = self.privacy_manager.pii_detections[user_id]
            today = datetime.now().date()

            for detection in detections:
                pii_count_total += 1
                if detection.timestamp.date() == today:
                    pii_count_today += 1

                action = detection.action_taken.value
                pii_actions[action] = pii_actions.get(action, 0) + 1

        # Get data minimization policy
        policy = self.privacy_manager.minimization_policies.get(user_id)

        # Calculate budget percentages
        epsilon_pct = 0.0
        queries_pct = 0.0
        budget_near_limit = False

        if budget:
            epsilon_pct = (budget.epsilon_spent / budget.max_epsilon) * 100
            queries_pct = (budget.queries_made / budget.max_queries_per_day) * 100
            budget_near_limit = epsilon_pct > 80 or queries_pct > 80

        # Check consent expiry
        consent_expiring = False
        if consent and consent.consent_expiry:
            days_until_expiry = (consent.consent_expiry - datetime.now()).days
            consent_expiring = days_until_expiry < 7

        return PrivacyStatus(
            consent_level=consent.consent_level if consent else ConsentLevel.NONE,
            consent_granted_date=consent.consent_date if consent else None,
            consent_expiry_date=consent.consent_expiry if consent else None,
            epsilon_spent=budget.epsilon_spent if budget else 0.0,
            epsilon_limit=budget.max_epsilon if budget else 1.0,
            epsilon_percentage=epsilon_pct,
            queries_made=budget.queries_made if budget else 0,
            queries_limit=budget.max_queries_per_day if budget else 100,
            queries_percentage=queries_pct,
            budget_reset_date=budget.last_reset if budget else datetime.now(),
            pii_detections_today=pii_count_today,
            pii_detections_total=pii_count_total,
            pii_actions_taken=pii_actions,
            data_retention_days=policy.retention_days if policy else 90,
            auto_deletion_enabled=policy.auto_delete if policy else True,
            budget_near_limit=budget_near_limit,
            consent_expiring_soon=consent_expiring
        )

    async def _generate_model_usage(
        self,
        user_id: str,
        period_days: int
    ) -> ModelUsageStats:
        """Generate model usage section"""
        # Get performance data from orchestrator
        perf_data = self.orchestrator.performance_history

        # Filter to user and period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        total_requests = 0
        requests_by_provider = {}
        requests_by_model = {}
        cost_by_provider = {}
        total_cost = 0.0
        latencies = []
        quality_scores = []
        successes = 0

        recent_selections = []

        for (provider, model), perf in perf_data.items():
            # Filter by date (using model's performance records)
            for record in perf.request_history[-100:]:  # Last 100 requests
                # Assume all requests in last period (simplified)
                total_requests += 1

                requests_by_provider[provider] = requests_by_provider.get(provider, 0) + 1
                model_key = f"{provider.value}:{model}"
                requests_by_model[model_key] = requests_by_model.get(model_key, 0) + 1

                # Aggregate performance
                if record.get("success", False):
                    successes += 1

                if "latency_ms" in record:
                    latencies.append(record["latency_ms"])

                if "cost" in record:
                    cost = record["cost"]
                    total_cost += cost
                    cost_by_provider[provider] = cost_by_provider.get(provider, 0.0) + cost

                if "quality_score" in record and record["quality_score"]:
                    quality_scores.append(record["quality_score"])

        # Calculate averages
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        success_rate = (successes / total_requests) if total_requests > 0 else 1.0

        # Estimate cost savings (vs always using GPT-4)
        gpt4_cost_per_request = 0.05  # Estimated
        estimated_savings = (total_requests * gpt4_cost_per_request) - total_cost

        return ModelUsageStats(
            current_model=None,  # Would need session context
            current_provider=None,
            total_requests=total_requests,
            requests_by_provider=requests_by_provider,
            requests_by_model=requests_by_model,
            total_cost=total_cost,
            cost_by_provider=cost_by_provider,
            estimated_cost_savings=max(0, estimated_savings),
            average_latency_ms=avg_latency,
            average_quality_score=avg_quality,
            success_rate=success_rate,
            recent_selections=recent_selections
        )

    async def _generate_epistemic_debt(
        self,
        user_id: str,
        period_days: int
    ) -> EpistemicDebtStatus:
        """Generate epistemic debt section"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Get EDM report
        report = self.edm_monitor.generate_report(user_id, start_date, end_date)

        # Count by severity
        debts_by_severity = {}
        for severity in DebtSeverity:
            debts_by_severity[severity] = 0

        # Count by type
        debts_by_type = {}

        high_severity_count = 0
        critical_alerts = []

        if user_id in self.edm_monitor.debt_snapshots:
            active_debts = [
                d for d in self.edm_monitor.debt_snapshots[user_id]
                if not d.resolved and start_date <= d.timestamp <= end_date
            ]

            for debt in active_debts:
                debts_by_severity[debt.severity] = debts_by_severity.get(debt.severity, 0) + 1
                debts_by_type[debt.debt_type] = debts_by_type.get(debt.debt_type, 0) + 1

                if debt.severity in [DebtSeverity.HIGH, DebtSeverity.CRITICAL]:
                    high_severity_count += 1

                if debt.severity == DebtSeverity.CRITICAL:
                    critical_alerts.append(
                        f"🚨 Critical epistemic debt: {debt.debt_type} - {debt.problematic_claim[:50]}..."
                    )

        # Get recent debts
        recent_debts = []
        if user_id in self.edm_monitor.debt_snapshots:
            recent = sorted(
                self.edm_monitor.debt_snapshots[user_id],
                key=lambda d: d.timestamp,
                reverse=True
            )[:10]

            for debt in recent:
                recent_debts.append({
                    "timestamp": debt.timestamp.isoformat(),
                    "type": debt.debt_type,
                    "severity": debt.severity.value,
                    "claim": debt.problematic_claim[:100],
                    "resolved": debt.resolved
                })

        return EpistemicDebtStatus(
            total_active_debts=report.total_active_debts,
            debts_by_severity=debts_by_severity,
            debts_by_type=debts_by_type,
            total_resolved=report.total_resolved,
            total_disputed=report.total_disputed,
            resolution_rate=report.resolution_rate,
            recent_debts=recent_debts,
            debt_trend=report.trend,
            high_severity_count=high_severity_count,
            critical_alerts=critical_alerts
        )

    async def _generate_improvements(
        self,
        user_id: str,
        period_days: int
    ) -> ImprovementActivity:
        """Generate improvements section"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Get improvement suggestions
        all_suggestions = self.improvement_loop.suggestions

        # Filter to user and period
        user_suggestions = [
            s for s in all_suggestions.values()
            if s.generated_at >= start_date and s.generated_at <= end_date
        ]

        # Count by status
        pending = sum(1 for s in user_suggestions if s.status == ImprovementStatus.PENDING)
        approved = sum(1 for s in user_suggestions if s.status == ImprovementStatus.APPROVED)
        implemented = sum(1 for s in user_suggestions if s.status == ImprovementStatus.IMPLEMENTED)
        rejected = sum(1 for s in user_suggestions if s.status == ImprovementStatus.REJECTED)

        # Count by component
        by_component = {}
        for s in user_suggestions:
            by_component[s.component] = by_component.get(s.component, 0) + 1

        # Average confidence
        avg_confidence = (
            sum(s.confidence for s in user_suggestions) / len(user_suggestions)
            if user_suggestions else 0.0
        )

        # Count feedback sources
        user_feedback_count = sum(
            1 for f in self.improvement_loop.feedback_events
            if f.feedback_type.value.startswith("user_") and
            start_date <= f.timestamp <= end_date
        )

        gate_violation_count = sum(
            1 for f in self.improvement_loop.feedback_events
            if f.feedback_type.value == "gate_violation" and
            start_date <= f.timestamp <= end_date
        )

        ari_alert_count = sum(
            1 for f in self.improvement_loop.feedback_events
            if f.feedback_type.value == "ari_alert" and
            start_date <= f.timestamp <= end_date
        )

        # Recent improvements
        recent = sorted(user_suggestions, key=lambda s: s.generated_at, reverse=True)[:10]
        recent_improvements = [
            {
                "id": s.suggestion_id,
                "component": s.component,
                "description": s.description[:100],
                "action": s.action.value,
                "confidence": s.confidence,
                "status": s.status.value,
                "generated_at": s.generated_at.isoformat()
            }
            for s in recent
        ]

        return ImprovementActivity(
            total_improvements=len(user_suggestions),
            pending_count=pending,
            approved_count=approved,
            implemented_count=implemented,
            rejected_count=rejected,
            recent_improvements=recent_improvements,
            average_confidence=avg_confidence,
            improvements_by_component=by_component,
            user_feedback_count=user_feedback_count,
            gate_violation_count=gate_violation_count,
            ari_alert_count=ari_alert_count
        )

    async def _generate_context_memory(self, user_id: str) -> ContextMemoryStatus:
        """Generate context memory section"""
        # Get memories for user
        all_memories = self.context_manager.memories.get(user_id, [])

        # Count by type
        by_type = {}
        for memory in all_memories:
            mem_type = memory.memory_type.value
            by_type[mem_type] = by_type.get(mem_type, 0) + 1

        # Count by priority
        by_priority = {}
        for memory in all_memories:
            priority = memory.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1

        # Calculate token usage
        total_tokens = sum(
            len(m.content.split()) * 1.3  # Rough token estimate
            for m in all_memories
        )

        max_tokens = self.context_manager.max_context_tokens
        utilization = (total_tokens / max_tokens) * 100 if max_tokens > 0 else 0.0

        # Check consolidation status
        unconsolidated = sum(
            1 for m in all_memories
            if not m.consolidated
        )
        needs_consolidation = unconsolidated >= self.context_manager.consolidation_threshold

        # Get last consolidation time
        last_consolidation = None
        if user_id in self.context_manager.last_consolidation:
            last_consolidation = self.context_manager.last_consolidation[user_id]

        # Recent memories
        recent = sorted(all_memories, key=lambda m: m.timestamp, reverse=True)[:10]
        recent_memories = [
            {
                "id": m.memory_id,
                "type": m.memory_type.value,
                "priority": m.priority.value,
                "content": m.content[:100],
                "timestamp": m.timestamp.isoformat(),
                "tags": list(m.tags)
            }
            for m in recent
        ]

        return ContextMemoryStatus(
            total_memories=len(all_memories),
            memories_by_type=by_type,
            memories_by_priority=by_priority,
            total_tokens=int(total_tokens),
            max_tokens=max_tokens,
            utilization_percentage=utilization,
            last_consolidation=last_consolidation,
            unconsolidated_count=unconsolidated,
            needs_consolidation=needs_consolidation,
            recent_memories=recent_memories
        )

    async def _generate_ari_engine_status(
        self,
        user_id: str,
        period_days: int
    ) -> ARIEngineStatus:
        """Generate ARI Engine status section"""
        if not self.ari_engine:
            logger.warning("ARI Engine not available")
            return None

        # Calculate comprehensive ARI
        ari_score = self.ari_engine.calculate_comprehensive_ari(user_id)

        # Get ARI history
        ari_history_scores = self.ari_engine.get_ari_history(user_id, days=period_days)
        ari_history = [
            (score.timestamp.isoformat(), score.overall_ari)
            for score in ari_history_scores
        ]

        # Get recent UCC responses
        if user_id in self.ari_engine.socratic_copilot.ucc_history:
            uccs = self.ari_engine.socratic_copilot.ucc_history[user_id]
            recent_uccs = sorted(uccs, key=lambda u: u.created_at, reverse=True)[:5]
            recent_ucc_data = [
                {
                    "question": ucc.question[:100],
                    "response_type": ucc.response_type.value,
                    "capability": ucc.capability_demonstrated,
                    "signal": ucc.ari_signal.value,
                    "timestamp": ucc.created_at.isoformat()
                }
                for ucc in recent_uccs
            ]
        else:
            recent_ucc_data = []

        # Check for deep dive baseline
        has_baseline = False
        baseline_domain = None
        baseline_established_at = None

        if user_id in self.ari_engine.deep_dive.baselines:
            # Get first baseline (any domain)
            baselines = self.ari_engine.deep_dive.baselines[user_id]
            if baselines:
                first_domain = list(baselines.keys())[0]
                baseline = baselines[first_domain]
                has_baseline = True
                baseline_domain = baseline.domain
                baseline_established_at = baseline.established_at

        # Generate recommendations
        recommendations = []
        if ari_score.signal_level == ARISignalLevel.LOW or ari_score.signal_level == ARISignalLevel.CRITICAL:
            recommendations.append("Consider completing a Deep Dive session to establish baseline")
            recommendations.append("Engage more deeply with task delegation questions")

        if ari_score.trend_direction == "declining":
            recommendations.append("Skill retention concerns detected - try hands-on practice")

        if not has_baseline:
            recommendations.append("Complete a Deep Dive session to establish your capability baseline")

        return ARIEngineStatus(
            overall_ari=ari_score.overall_ari,
            signal_level=ari_score.signal_level.value,
            lexical_ari=ari_score.lexical_ari,
            interaction_ari=ari_score.interaction_ari,
            baseline_deviation=ari_score.baseline_deviation,
            trend_direction=ari_score.trend_direction,
            days_in_trend=ari_score.days_in_trend,
            alerts=ari_score.alerts,
            recommendations=recommendations,
            ari_history=ari_history,
            recent_uccs=recent_ucc_data,
            has_baseline=has_baseline,
            baseline_domain=baseline_domain,
            baseline_established_at=baseline_established_at
        )

    async def _generate_rdi_monitor_status(
        self,
        user_id: str,
        period_days: int
    ) -> RDIMonitorStatus:
        """
        Generate RDI Monitor status section

        **PRIVACY:** This data is PRIVATE and shown only to the user.
        """
        if not self.rdi_monitor:
            logger.warning("RDI Monitor not available")
            return None

        # Get RDI data from monitor (private, for user only)
        rdi_data = self.rdi_monitor.get_user_rdi_for_dashboard(user_id)

        if not rdi_data.get("rdi_available"):
            # No RDI data yet
            return RDIMonitorStatus(
                overall_rdi=0.0,
                rdi_level="aligned",
                semantic_drift=0.0,
                factual_drift=0.0,
                logical_drift=0.0,
                trend_direction="stable",
                private_alerts=["No RDI data yet - continue using the system to establish baseline"],
                rdi_history=[],
                privacy_notice=rdi_data.get("_privacy_notice", "This data is private and stored only on your device."),
                opted_into_aggregates=False
        )

        # Check if user opted into aggregates
        hashed_user_id = self.rdi_monitor._hash_user_id(user_id)
        opted_in = hashed_user_id in self.rdi_monitor._aggregate_opt_ins

        # Build RDI history from dashboard data
        rdi_history = [
            (entry["timestamp"], entry["rdi"])
            for entry in rdi_data.get("history", [])
        ]

        return RDIMonitorStatus(
            overall_rdi=rdi_data["current_rdi"],
            rdi_level=rdi_data["rdi_level"],
            semantic_drift=rdi_data["semantic_drift"],
            factual_drift=rdi_data["factual_drift"],
            logical_drift=rdi_data["logical_drift"],
            trend_direction=rdi_data["trend"],
            private_alerts=rdi_data.get("alerts", []),
            rdi_history=rdi_history,
            privacy_notice=rdi_data.get("_privacy_notice", "This data is private and stored only on your device."),
            opted_into_aggregates=opted_in
        )

    def _calculate_health_score(
        self,
        agency_metrics: Optional[AgencyMetrics],
        privacy_status: Optional[PrivacyStatus],
        epistemic_debt: Optional[EpistemicDebtStatus]
    ) -> float:
        """
        Calculate overall system health score (0-100)

        Factors:
        - Agency metrics (40%)
        - Privacy compliance (30%)
        - Epistemic debt (30%)
        """
        score = 0.0

        # Agency component (40 points)
        if agency_metrics:
            agency_score = 0.0

            # ΔAgency score (0-15 points)
            if agency_metrics.current_delta_agency >= 0.2:
                agency_score += 15
            elif agency_metrics.current_delta_agency >= 0:
                agency_score += 10
            elif agency_metrics.current_delta_agency >= -0.1:
                agency_score += 5

            # BHIR score (0-10 points)
            agency_score += min(10, agency_metrics.current_bhir * 10)

            # Trend score (0-15 points)
            if agency_metrics.agency_trend == AgencyTrend.INCREASING:
                agency_score += 15
            elif agency_metrics.agency_trend == AgencyTrend.STABLE:
                agency_score += 10
            elif agency_metrics.agency_trend == AgencyTrend.DECREASING:
                agency_score += 5
            elif agency_metrics.agency_trend == AgencyTrend.CRITICAL:
                agency_score += 0

            score += agency_score
        else:
            score += 20  # Neutral score if no data

        # Privacy component (30 points)
        if privacy_status:
            privacy_score = 0.0

            # Budget management (0-15 points)
            budget_usage = max(
                privacy_status.epsilon_percentage,
                privacy_status.queries_percentage
            )
            if budget_usage < 50:
                privacy_score += 15
            elif budget_usage < 80:
                privacy_score += 10
            elif budget_usage < 95:
                privacy_score += 5

            # Consent level (0-10 points)
            consent_scores = {
                ConsentLevel.FULL: 10,
                ConsentLevel.STANDARD: 8,
                ConsentLevel.MINIMAL: 5,
                ConsentLevel.NONE: 0
            }
            privacy_score += consent_scores.get(privacy_status.consent_level, 0)

            # PII handling (0-5 points)
            if privacy_status.pii_detections_today < 5:
                privacy_score += 5
            elif privacy_status.pii_detections_today < 10:
                privacy_score += 3

            score += privacy_score
        else:
            score += 15  # Neutral score

        # Epistemic debt component (30 points)
        if epistemic_debt:
            debt_score = 30.0

            # Deduct for active debts
            debt_score -= min(15, epistemic_debt.total_active_debts * 0.5)

            # Deduct more for high severity
            debt_score -= min(10, epistemic_debt.high_severity_count * 2)

            # Bonus for good resolution rate
            if epistemic_debt.resolution_rate > 0.8:
                debt_score += 5

            score += max(0, debt_score)
        else:
            score += 15  # Neutral score

        return min(100.0, max(0.0, score))

    def export_dashboard_json(self, dashboard: DashboardData) -> str:
        """Export dashboard data as JSON string"""
        import json

        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        return json.dumps(dashboard, default=default_serializer, indent=2)

    def format_dashboard_text(self, dashboard: DashboardData) -> str:
        """Format dashboard data as human-readable text"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"AGENCY-CENTRIC AI DASHBOARD - User: {dashboard.user_id}")
        lines.append(f"Generated: {dashboard.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Reporting Period: Last {dashboard.reporting_period_days} days")
        lines.append(f"Overall Health Score: {dashboard.overall_health_score:.1f}/100")
        lines.append("=" * 80)

        # System alerts
        if dashboard.system_alerts:
            lines.append("\n🚨 SYSTEM ALERTS:")
            for alert in dashboard.system_alerts:
                lines.append(f"  {alert}")

        # Agency Metrics
        if dashboard.agency_metrics:
            m = dashboard.agency_metrics
            lines.append("\n📊 AGENCY METRICS:")
            lines.append(f"  Current ΔAgency: {m.current_delta_agency:+.3f}")
            lines.append(f"  Current BHIR: {m.current_bhir:.3f}")
            lines.append(f"  Skill Level: {m.current_skill_level:.3f}")
            lines.append(f"  AI Reliance: {m.current_ai_reliance:.1%}")
            lines.append(f"  Trend: {m.agency_trend.value.upper()}")

            if m.active_alerts:
                lines.append("  Alerts:")
                for alert in m.active_alerts:
                    lines.append(f"    {alert}")

        # Privacy Status
        if dashboard.privacy_status:
            p = dashboard.privacy_status
            lines.append("\n🔒 PRIVACY STATUS:")
            lines.append(f"  Consent Level: {p.consent_level.value}")
            lines.append(f"  Privacy Budget: ε={p.epsilon_spent:.3f}/{p.epsilon_limit:.3f} ({p.epsilon_percentage:.1f}%)")
            lines.append(f"  Queries: {p.queries_made}/{p.queries_limit} ({p.queries_percentage:.1f}%)")
            lines.append(f"  PII Detections Today: {p.pii_detections_today}")

        # Model Usage
        if dashboard.model_usage:
            m = dashboard.model_usage
            lines.append("\n🤖 MODEL USAGE:")
            lines.append(f"  Total Requests: {m.total_requests}")
            lines.append(f"  Total Cost: ${m.total_cost:.4f}")
            lines.append(f"  Est. Savings: ${m.estimated_cost_savings:.4f}")
            lines.append(f"  Avg Latency: {m.average_latency_ms:.0f}ms")
            lines.append(f"  Success Rate: {m.success_rate:.1%}")

        # Epistemic Debt
        if dashboard.epistemic_debt:
            e = dashboard.epistemic_debt
            lines.append("\n📚 EPISTEMIC DEBT:")
            lines.append(f"  Active Debts: {e.total_active_debts}")
            lines.append(f"  High Severity: {e.high_severity_count}")
            lines.append(f"  Resolution Rate: {e.resolution_rate:.1%}")
            lines.append(f"  Trend: {e.debt_trend}")

        # Improvements
        if dashboard.improvements:
            i = dashboard.improvements
            lines.append("\n🔧 SELF-IMPROVEMENT:")
            lines.append(f"  Total Improvements: {i.total_improvements}")
            lines.append(f"  Pending: {i.pending_count}")
            lines.append(f"  Implemented: {i.implemented_count}")
            lines.append(f"  Avg Confidence: {i.average_confidence:.2f}")

        # Context Memory
        if dashboard.context_memory:
            c = dashboard.context_memory
            lines.append("\n🧠 CONTEXT MEMORY:")
            lines.append(f"  Total Memories: {c.total_memories}")
            lines.append(f"  Token Usage: {c.total_tokens}/{c.max_tokens} ({c.utilization_percentage:.1f}%)")
            lines.append(f"  Needs Consolidation: {'Yes' if c.needs_consolidation else 'No'}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)
