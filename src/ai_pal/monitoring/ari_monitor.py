"""
ARI (Agency Retention Index) Monitoring System

Tracks user agency metrics over time to detect patterns of:
- Agency loss (ΔAgency < 0)
- Skill atrophy (reduced user capability)
- Increasing dependency on AI assistance
- Task efficacy trends

Part of Phase 2: Advanced Monitoring & Self-Improvement
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from loguru import logger


class AgencyTrend(Enum):
    """Agency trend classification"""
    INCREASING = "increasing"  # User gaining agency
    STABLE = "stable"  # Agency maintaining
    DECREASING = "decreasing"  # User losing agency
    CRITICAL = "critical"  # Severe agency loss


@dataclass
class AgencySnapshot:
    """Single point-in-time agency measurement"""
    timestamp: datetime
    task_id: str
    task_type: str

    # Agency Impact Metrics
    delta_agency: float  # Net agency change
    bhir: float  # Benefit-to-Human-Input Ratio
    task_efficacy: float  # How well task accomplished user's goal

    # Skill Metrics
    user_skill_before: float  # User capability before assistance
    user_skill_after: float  # User capability after assistance
    skill_development: float  # Change in user capability

    # Dependency Metrics
    ai_reliance: float  # How much user relied on AI (0-1)
    autonomy_retention: float  # How much user retained control (0-1)

    # Context
    user_id: str
    session_id: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class ARIReport:
    """Agency Retention Index periodic report"""
    period_start: datetime
    period_end: datetime
    user_id: str

    # Aggregate Metrics
    average_delta_agency: float
    average_bhir: float
    average_task_efficacy: float
    average_skill_development: float

    # Trends
    agency_trend: AgencyTrend
    skill_trend: str  # "improving", "stable", "declining"
    dependency_trend: str  # "decreasing", "stable", "increasing"

    # Alerts
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Raw data
    snapshot_count: int = 0
    snapshots: List[AgencySnapshot] = field(default_factory=list)


class ARIMonitor:
    """
    Agency Retention Index Monitoring System

    Tracks user agency over time and detects concerning patterns:
    - Decreasing ΔAgency (user losing agency)
    - Skill atrophy (user becoming less capable)
    - Increasing AI dependency
    - Low BHIR (poor benefit-to-effort ratio)
    """

    def __init__(
        self,
        storage_dir: Path,
        alert_threshold_delta_agency: float = -0.1,
        alert_threshold_bhir: float = 0.8,
        alert_threshold_skill_loss: float = -0.15,
        report_interval_days: int = 7
    ):
        """
        Initialize ARI Monitor

        Args:
            storage_dir: Directory for storing agency snapshots
            alert_threshold_delta_agency: Alert if ΔAgency falls below this
            alert_threshold_bhir: Alert if BHIR falls below this
            alert_threshold_skill_loss: Alert if skill development is below this
            report_interval_days: Days between periodic reports
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.alert_threshold_delta_agency = alert_threshold_delta_agency
        self.alert_threshold_bhir = alert_threshold_bhir
        self.alert_threshold_skill_loss = alert_threshold_skill_loss
        self.report_interval_days = report_interval_days

        # In-memory cache
        self.snapshots: Dict[str, List[AgencySnapshot]] = {}

        # Load existing snapshots
        self._load_snapshots()

        logger.info(
            f"ARI Monitor initialized with storage at {storage_dir}, "
            f"ΔAgency threshold: {alert_threshold_delta_agency}, "
            f"BHIR threshold: {alert_threshold_bhir}"
        )

    def _load_snapshots(self) -> None:
        """Load existing snapshots from storage"""
        snapshot_files = list(self.storage_dir.glob("*.json"))
        logger.info(f"Loading {len(snapshot_files)} snapshot files")

        for snapshot_file in snapshot_files:
            try:
                with open(snapshot_file, 'r') as f:
                    data = json.load(f)
                    user_id = data.get("user_id")
                    if user_id:
                        if user_id not in self.snapshots:
                            self.snapshots[user_id] = []

                        snapshot = AgencySnapshot(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            task_id=data["task_id"],
                            task_type=data["task_type"],
                            delta_agency=data["delta_agency"],
                            bhir=data["bhir"],
                            task_efficacy=data["task_efficacy"],
                            user_skill_before=data["user_skill_before"],
                            user_skill_after=data["user_skill_after"],
                            skill_development=data["skill_development"],
                            ai_reliance=data["ai_reliance"],
                            autonomy_retention=data["autonomy_retention"],
                            user_id=user_id,
                            session_id=data["session_id"],
                            metadata=data.get("metadata", {})
                        )
                        self.snapshots[user_id].append(snapshot)
            except Exception as e:
                logger.error(f"Failed to load snapshot {snapshot_file}: {e}")

    async def record_snapshot(self, snapshot: AgencySnapshot) -> None:
        """
        Record a single agency measurement

        Args:
            snapshot: Agency snapshot to record
        """
        user_id = snapshot.user_id

        # Add to in-memory cache
        if user_id not in self.snapshots:
            self.snapshots[user_id] = []
        self.snapshots[user_id].append(snapshot)

        # Persist to disk
        filename = f"{user_id}_{snapshot.timestamp.isoformat()}.json"
        filepath = self.storage_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "timestamp": snapshot.timestamp.isoformat(),
                    "task_id": snapshot.task_id,
                    "task_type": snapshot.task_type,
                    "delta_agency": snapshot.delta_agency,
                    "bhir": snapshot.bhir,
                    "task_efficacy": snapshot.task_efficacy,
                    "user_skill_before": snapshot.user_skill_before,
                    "user_skill_after": snapshot.user_skill_after,
                    "skill_development": snapshot.skill_development,
                    "ai_reliance": snapshot.ai_reliance,
                    "autonomy_retention": snapshot.autonomy_retention,
                    "user_id": user_id,
                    "session_id": snapshot.session_id,
                    "metadata": snapshot.metadata
                }, f, indent=2)

            logger.debug(f"Recorded agency snapshot for user {user_id}, task {snapshot.task_id}")
        except Exception as e:
            logger.error(f"Failed to persist snapshot: {e}")

        # Check for immediate alerts
        await self._check_immediate_alerts(snapshot)

    async def _check_immediate_alerts(self, snapshot: AgencySnapshot) -> None:
        """Check if snapshot triggers immediate alerts"""
        alerts = []

        # Alert on low ΔAgency
        if snapshot.delta_agency < self.alert_threshold_delta_agency:
            alerts.append(
                f"⚠️ Low ΔAgency detected: {snapshot.delta_agency:.3f} "
                f"(threshold: {self.alert_threshold_delta_agency})"
            )

        # Alert on low BHIR
        if snapshot.bhir < self.alert_threshold_bhir:
            alerts.append(
                f"⚠️ Low BHIR detected: {snapshot.bhir:.3f} "
                f"(threshold: {self.alert_threshold_bhir})"
            )

        # Alert on skill loss
        if snapshot.skill_development < self.alert_threshold_skill_loss:
            alerts.append(
                f"⚠️ Skill atrophy detected: {snapshot.skill_development:.3f} "
                f"(threshold: {self.alert_threshold_skill_loss})"
            )

        # Alert on high AI reliance
        if snapshot.ai_reliance > 0.9:
            alerts.append(
                f"⚠️ High AI dependency: {snapshot.ai_reliance:.1%} reliance"
            )

        if alerts:
            logger.warning(
                f"Agency alerts for user {snapshot.user_id}, task {snapshot.task_id}:\n" +
                "\n".join(alerts)
            )

    def generate_report(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ARIReport:
        """
        Generate ARI report for a user over a time period

        Args:
            user_id: User to generate report for
            start_date: Start of reporting period (default: 7 days ago)
            end_date: End of reporting period (default: now)

        Returns:
            ARIReport with analysis and recommendations
        """
        if user_id not in self.snapshots:
            logger.warning(f"No snapshots found for user {user_id}")
            return ARIReport(
                period_start=start_date or datetime.now(),
                period_end=end_date or datetime.now(),
                user_id=user_id,
                average_delta_agency=0.0,
                average_bhir=0.0,
                average_task_efficacy=0.0,
                average_skill_development=0.0,
                agency_trend=AgencyTrend.STABLE,
                skill_trend="unknown",
                dependency_trend="unknown",
                alerts=["No data available for this user"],
                snapshot_count=0
            )

        # Set default date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=self.report_interval_days)

        # Filter snapshots to date range
        period_snapshots = [
            s for s in self.snapshots[user_id]
            if start_date <= s.timestamp <= end_date
        ]

        if not period_snapshots:
            return ARIReport(
                period_start=start_date,
                period_end=end_date,
                user_id=user_id,
                average_delta_agency=0.0,
                average_bhir=0.0,
                average_task_efficacy=0.0,
                average_skill_development=0.0,
                agency_trend=AgencyTrend.STABLE,
                skill_trend="unknown",
                dependency_trend="unknown",
                alerts=["No data in this period"],
                snapshot_count=0
            )

        # Calculate aggregates
        avg_delta_agency = sum(s.delta_agency for s in period_snapshots) / len(period_snapshots)
        avg_bhir = sum(s.bhir for s in period_snapshots) / len(period_snapshots)
        avg_task_efficacy = sum(s.task_efficacy for s in period_snapshots) / len(period_snapshots)
        avg_skill_development = sum(s.skill_development for s in period_snapshots) / len(period_snapshots)

        # Determine trends
        agency_trend = self._determine_agency_trend(period_snapshots)
        skill_trend = self._determine_skill_trend(period_snapshots)
        dependency_trend = self._determine_dependency_trend(period_snapshots)

        # Generate alerts and recommendations
        alerts, recommendations = self._generate_alerts_and_recommendations(
            avg_delta_agency,
            avg_bhir,
            avg_skill_development,
            agency_trend,
            skill_trend,
            dependency_trend
        )

        return ARIReport(
            period_start=start_date,
            period_end=end_date,
            user_id=user_id,
            average_delta_agency=avg_delta_agency,
            average_bhir=avg_bhir,
            average_task_efficacy=avg_task_efficacy,
            average_skill_development=avg_skill_development,
            agency_trend=agency_trend,
            skill_trend=skill_trend,
            dependency_trend=dependency_trend,
            alerts=alerts,
            recommendations=recommendations,
            snapshot_count=len(period_snapshots),
            snapshots=period_snapshots
        )

    def _determine_agency_trend(self, snapshots: List[AgencySnapshot]) -> AgencyTrend:
        """Determine agency trend from snapshots"""
        if len(snapshots) < 3:
            return AgencyTrend.STABLE

        # Calculate trend using linear regression on ΔAgency
        delta_agencies = [s.delta_agency for s in snapshots]
        avg_delta = sum(delta_agencies) / len(delta_agencies)

        # Simple trend: compare recent vs older
        recent = delta_agencies[-len(delta_agencies)//3:]
        older = delta_agencies[:len(delta_agencies)//3]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        diff = recent_avg - older_avg

        if avg_delta < -0.2:
            return AgencyTrend.CRITICAL
        elif diff < -0.1:
            return AgencyTrend.DECREASING
        elif diff > 0.1:
            return AgencyTrend.INCREASING
        else:
            return AgencyTrend.STABLE

    def _determine_skill_trend(self, snapshots: List[AgencySnapshot]) -> str:
        """Determine skill development trend"""
        if len(snapshots) < 3:
            return "stable"

        skill_changes = [s.skill_development for s in snapshots]
        recent = skill_changes[-len(skill_changes)//3:]
        older = skill_changes[:len(skill_changes)//3]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg > older_avg + 0.1:
            return "improving"
        elif recent_avg < older_avg - 0.1:
            return "declining"
        else:
            return "stable"

    def _determine_dependency_trend(self, snapshots: List[AgencySnapshot]) -> str:
        """Determine AI dependency trend"""
        if len(snapshots) < 3:
            return "stable"

        reliances = [s.ai_reliance for s in snapshots]
        recent = reliances[-len(reliances)//3:]
        older = reliances[:len(reliances)//3]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg > older_avg + 0.15:
            return "increasing"
        elif recent_avg < older_avg - 0.15:
            return "decreasing"
        else:
            return "stable"

    def _generate_alerts_and_recommendations(
        self,
        avg_delta_agency: float,
        avg_bhir: float,
        avg_skill_development: float,
        agency_trend: AgencyTrend,
        skill_trend: str,
        dependency_trend: str
    ) -> Tuple[List[str], List[str]]:
        """Generate alerts and recommendations based on metrics"""
        alerts = []
        recommendations = []

        # Agency alerts
        if agency_trend == AgencyTrend.CRITICAL:
            alerts.append("🚨 CRITICAL: Severe agency loss detected")
            recommendations.append("Reduce AI assistance and encourage independent problem-solving")
        elif agency_trend == AgencyTrend.DECREASING:
            alerts.append("⚠️ Agency is decreasing over time")
            recommendations.append("Review task delegation - user may be over-relying on AI")

        if avg_delta_agency < self.alert_threshold_delta_agency:
            alerts.append(f"⚠️ Low average ΔAgency: {avg_delta_agency:.3f}")
            recommendations.append("Tasks should increase user capability, not replace it")

        # BHIR alerts
        if avg_bhir < self.alert_threshold_bhir:
            alerts.append(f"⚠️ Low BHIR: {avg_bhir:.3f}")
            recommendations.append("Improve benefit-to-effort ratio - tasks may be too demanding")

        # Skill alerts
        if skill_trend == "declining":
            alerts.append("⚠️ User skills are declining")
            recommendations.append("Focus on skill-building tasks and educational support")

        if avg_skill_development < self.alert_threshold_skill_loss:
            alerts.append(f"⚠️ Skill atrophy: {avg_skill_development:.3f}")
            recommendations.append("Prioritize tasks that develop user capabilities")

        # Dependency alerts
        if dependency_trend == "increasing":
            alerts.append("⚠️ AI dependency is increasing")
            recommendations.append("Gradually reduce assistance level to maintain user autonomy")

        # Positive feedback
        if agency_trend == AgencyTrend.INCREASING and skill_trend == "improving":
            recommendations.append("✅ Excellent progress! User agency and skills are both improving")

        return alerts, recommendations

    def get_user_summary(self, user_id: str) -> Dict:
        """Get summary statistics for a user"""
        if user_id not in self.snapshots or not self.snapshots[user_id]:
            return {
                "user_id": user_id,
                "total_snapshots": 0,
                "status": "No data available"
            }

        snapshots = self.snapshots[user_id]

        return {
            "user_id": user_id,
            "total_snapshots": len(snapshots),
            "first_recorded": snapshots[0].timestamp.isoformat(),
            "last_recorded": snapshots[-1].timestamp.isoformat(),
            "average_delta_agency": sum(s.delta_agency for s in snapshots) / len(snapshots),
            "average_bhir": sum(s.bhir for s in snapshots) / len(snapshots),
            "average_skill_development": sum(s.skill_development for s in snapshots) / len(snapshots),
            "average_ai_reliance": sum(s.ai_reliance for s in snapshots) / len(snapshots)
        }


# Alias for backward compatibility
ARITrend = AgencyTrend
