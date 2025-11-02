"""
Predictive Analytics - Dashboard Forecasting

Provides predictive insights for:
- Agency trend forecasting (will user's autonomy increase/decrease?)
- Skill gap predictions (what skills need development?)
- Goal completion estimates (when will goals be achieved?)
- Bottleneck predictions (where will user get stuck?)

Uses simple time-series forecasting and pattern analysis.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import statistics

from ..monitoring.ari_monitor import ARIMonitor, ARISnapshot
from ..monitoring.edm_monitor import EDMMonitor
from ..ffe.models import Goal, StrengthType


class ForecastHorizon(Enum):
    """Forecast time horizons"""
    SHORT_TERM = "short_term"  # 7 days
    MEDIUM_TERM = "medium_term"  # 30 days
    LONG_TERM = "long_term"  # 90 days


class TrendDirection(Enum):
    """Trend directions"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class AgencyForecast:
    """Agency trend forecast"""
    horizon: ForecastHorizon
    current_ari: float
    predicted_ari: float
    confidence: float  # 0-1
    trend: TrendDirection

    # Contributing factors
    skill_development_trend: float
    ai_reliance_trend: float
    engagement_trend: float

    # Warnings
    warnings: List[str]
    recommendations: List[str]

    # Forecast data points (for visualization)
    forecast_points: List[Tuple[datetime, float]]  # (timestamp, predicted_ari)


@dataclass
class SkillGap:
    """Identified skill gap"""
    skill_area: str
    current_level: float  # 0-1
    target_level: float  # 0-1
    gap_size: float  # target - current
    urgency: str  # "low", "medium", "high", "critical"

    # Evidence
    recent_struggles: List[str]  # Recent bottlenecks in this area
    declining_performance: bool

    # Recommendations
    recommended_actions: List[str]
    estimated_time_to_close: timedelta


@dataclass
class GoalCompletionEstimate:
    """Goal completion prediction"""
    goal_id: str
    goal_description: str

    # Estimates
    estimated_completion_date: datetime
    confidence: float  # 0-1
    percent_complete: float  # 0-100

    # Velocity
    current_velocity: float  # tasks/day
    required_velocity: float  # tasks/day to hit deadline
    velocity_gap: float  # required - current

    # Risk factors
    risk_level: str  # "low", "medium", "high"
    risk_factors: List[str]

    # Recommendations
    recommendations: List[str]


class PredictiveAnalytics:
    """Predictive analytics engine"""

    def __init__(
        self,
        ari_monitor: ARIMonitor,
        edm_monitor: Optional[EDMMonitor] = None
    ):
        """
        Initialize predictive analytics

        Args:
            ari_monitor: ARI monitor for historical data
            edm_monitor: EDM monitor (optional)
        """
        self.ari_monitor = ari_monitor
        self.edm_monitor = edm_monitor

    async def forecast_agency_trend(
        self,
        user_id: str,
        horizon: ForecastHorizon = ForecastHorizon.SHORT_TERM
    ) -> AgencyForecast:
        """
        Forecast agency trend

        Uses simple linear regression on recent ARI snapshots to predict future trend.

        Args:
            user_id: User ID
            horizon: Forecast horizon

        Returns:
            Agency forecast
        """
        # Get historical snapshots
        days_history = 30  # Use last 30 days for forecast
        snapshots = self.ari_monitor.get_snapshots_in_range(
            user_id,
            datetime.now() - timedelta(days=days_history),
            datetime.now()
        )

        if len(snapshots) < 3:
            # Not enough data for forecast
            return AgencyForecast(
                horizon=horizon,
                current_ari=0.5,
                predicted_ari=0.5,
                confidence=0.0,
                trend=TrendDirection.STABLE,
                skill_development_trend=0.0,
                ai_reliance_trend=0.0,
                engagement_trend=0.0,
                warnings=["Insufficient data for forecast (need at least 3 snapshots)"],
                recommendations=["Continue using AI-PAL to build history"],
                forecast_points=[]
            )

        # Calculate current ARI
        current_snapshot = snapshots[-1]
        current_ari = current_snapshot.autonomy_retention

        # Extract trends using linear regression
        ari_values = [s.autonomy_retention for s in snapshots]
        skill_values = [s.skill_development for s in snapshots]
        reliance_values = [s.ai_reliance for s in snapshots]
        engagement_values = [s.engagement for s in snapshots]

        # Simple linear regression
        ari_slope = self._calculate_slope([
            (i, val) for i, val in enumerate(ari_values)
        ])
        skill_slope = self._calculate_slope([
            (i, val) for i, val in enumerate(skill_values)
        ])
        reliance_slope = self._calculate_slope([
            (i, val) for i, val in enumerate(reliance_values)
        ])
        engagement_slope = self._calculate_slope([
            (i, val) for i, val in enumerate(engagement_values)
        ])

        # Forecast based on horizon
        horizon_days = {
            ForecastHorizon.SHORT_TERM: 7,
            ForecastHorizon.MEDIUM_TERM: 30,
            ForecastHorizon.LONG_TERM: 90
        }[horizon]

        # Project forward
        predicted_ari = current_ari + (ari_slope * horizon_days)
        predicted_ari = max(0.0, min(1.0, predicted_ari))  # Clamp to 0-1

        # Determine trend
        if ari_slope > 0.01:
            trend = TrendDirection.IMPROVING
        elif ari_slope < -0.01:
            trend = TrendDirection.DECLINING
        else:
            trend = TrendDirection.STABLE

        # Calculate confidence based on data consistency
        ari_std = statistics.stdev(ari_values) if len(ari_values) > 1 else 0.5
        confidence = max(0.0, 1.0 - ari_std)  # Lower variance = higher confidence

        # Generate forecast points
        forecast_points = []
        now = datetime.now()
        for day in range(0, horizon_days + 1, max(1, horizon_days // 10)):
            predicted_val = current_ari + (ari_slope * day)
            predicted_val = max(0.0, min(1.0, predicted_val))
            forecast_points.append((now + timedelta(days=day), predicted_val))

        # Generate warnings and recommendations
        warnings = []
        recommendations = []

        if trend == TrendDirection.DECLINING:
            warnings.append(f"Agency predicted to decline to {predicted_ari:.2f} in {horizon_days} days")
            recommendations.append("Work more independently before asking AI for help")
            recommendations.append("Focus on understanding, not just task completion")

        if reliance_slope > 0.01:
            warnings.append("AI reliance is increasing")
            recommendations.append("Set explicit learning goals instead of output goals")

        if skill_slope < -0.01:
            warnings.append("Skill development is declining")
            recommendations.append("Use FFE to break tasks into learning opportunities")

        if predicted_ari < 0.5:
            warnings.append("Critical: Agency floor breach predicted")
            recommendations.append("URGENT: Reduce AI assistance and focus on skill building")

        return AgencyForecast(
            horizon=horizon,
            current_ari=current_ari,
            predicted_ari=predicted_ari,
            confidence=confidence,
            trend=trend,
            skill_development_trend=skill_slope,
            ai_reliance_trend=reliance_slope,
            engagement_trend=engagement_slope,
            warnings=warnings,
            recommendations=recommendations,
            forecast_points=forecast_points
        )

    async def identify_skill_gaps(
        self,
        user_id: str,
        min_gap_size: float = 0.2
    ) -> List[SkillGap]:
        """
        Identify skill gaps from ARI history

        Analyzes bottleneck patterns and declining performance to identify
        areas where user needs skill development.

        Args:
            user_id: User ID
            min_gap_size: Minimum gap size to report (0-1)

        Returns:
            List of identified skill gaps
        """
        # Get recent snapshots (last 30 days)
        snapshots = self.ari_monitor.get_snapshots_in_range(
            user_id,
            datetime.now() - timedelta(days=30),
            datetime.now()
        )

        if not snapshots:
            return []

        skill_gaps = []

        # Analyze skill development dimension
        skill_values = [s.skill_development for s in snapshots]
        avg_skill = statistics.mean(skill_values)

        if avg_skill < 0.7:  # Below good threshold
            gap_size = 0.7 - avg_skill
            if gap_size >= min_gap_size:
                # Calculate urgency
                skill_slope = self._calculate_slope([
                    (i, val) for i, val in enumerate(skill_values)
                ])
                declining = skill_slope < -0.01

                if avg_skill < 0.5:
                    urgency = "critical"
                elif declining:
                    urgency = "high"
                elif gap_size > 0.3:
                    urgency = "high"
                elif gap_size > 0.2:
                    urgency = "medium"
                else:
                    urgency = "low"

                # Estimate time to close gap
                if skill_slope > 0:
                    days_to_close = int(gap_size / skill_slope)
                else:
                    days_to_close = 90  # Default estimate

                skill_gaps.append(SkillGap(
                    skill_area="General Skill Development",
                    current_level=avg_skill,
                    target_level=0.7,
                    gap_size=gap_size,
                    urgency=urgency,
                    recent_struggles=[],
                    declining_performance=declining,
                    recommended_actions=[
                        "Work on tasks independently before consulting AI",
                        "Use FFE learn-by-teaching mode",
                        "Focus on understanding concepts, not just solutions"
                    ],
                    estimated_time_to_close=timedelta(days=min(days_to_close, 180))
                ))

        # Analyze bottleneck resolution
        bottleneck_values = [s.bottleneck_resolution for s in snapshots]
        avg_bottleneck = statistics.mean(bottleneck_values)

        if avg_bottleneck < 0.7:
            gap_size = 0.7 - avg_bottleneck
            if gap_size >= min_gap_size:
                bottleneck_slope = self._calculate_slope([
                    (i, val) for i, val in enumerate(bottleneck_values)
                ])
                declining = bottleneck_slope < -0.01

                urgency = "high" if avg_bottleneck < 0.5 or declining else "medium"

                skill_gaps.append(SkillGap(
                    skill_area="Problem Solving & Bottleneck Resolution",
                    current_level=avg_bottleneck,
                    target_level=0.7,
                    gap_size=gap_size,
                    urgency=urgency,
                    recent_struggles=[],
                    declining_performance=declining,
                    recommended_actions=[
                        "Practice debugging independently",
                        "Use Growth Scaffold for structured problem-solving",
                        "Document your problem-solving process"
                    ],
                    estimated_time_to_close=timedelta(days=30)
                ))

        # Sort by urgency
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        skill_gaps.sort(key=lambda g: urgency_order.get(g.urgency, 4))

        return skill_gaps

    async def estimate_goal_completion(
        self,
        goal: Goal,
        completed_tasks: int,
        total_tasks: int,
        days_elapsed: int
    ) -> GoalCompletionEstimate:
        """
        Estimate when a goal will be completed

        Args:
            goal: Goal object
            completed_tasks: Number of tasks completed
            total_tasks: Total tasks in goal
            days_elapsed: Days since goal started

        Returns:
            Goal completion estimate
        """
        # Calculate current velocity
        if days_elapsed > 0:
            current_velocity = completed_tasks / days_elapsed  # tasks/day
        else:
            current_velocity = 0.0

        # Calculate percent complete
        percent_complete = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Estimate remaining time
        remaining_tasks = total_tasks - completed_tasks
        if current_velocity > 0:
            days_remaining = remaining_tasks / current_velocity
            estimated_completion_date = datetime.now() + timedelta(days=days_remaining)
        else:
            # No velocity yet - estimate conservatively
            days_remaining = remaining_tasks * 2  # Assume 0.5 tasks/day
            estimated_completion_date = datetime.now() + timedelta(days=days_remaining)

        # Calculate required velocity if there's a deadline
        if hasattr(goal, 'deadline') and goal.deadline:
            deadline = goal.deadline
            days_until_deadline = (deadline - datetime.now()).days
            if days_until_deadline > 0:
                required_velocity = remaining_tasks / days_until_deadline
            else:
                required_velocity = float('inf')  # Already past deadline
        else:
            required_velocity = current_velocity

        velocity_gap = required_velocity - current_velocity

        # Assess risk
        risk_factors = []
        if velocity_gap > 0.5:
            risk_factors.append(f"Need to increase velocity by {velocity_gap:.1f} tasks/day")
        if current_velocity == 0 and days_elapsed > 3:
            risk_factors.append("No progress in several days")
        if percent_complete < 20 and days_elapsed > 7:
            risk_factors.append("Low progress after one week")

        # Determine risk level
        if len(risk_factors) >= 3 or velocity_gap > 1.0:
            risk_level = "high"
        elif len(risk_factors) >= 2 or velocity_gap > 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Calculate confidence
        if days_elapsed < 3:
            confidence = 0.3  # Low confidence with little data
        elif days_elapsed < 7:
            confidence = 0.6
        else:
            confidence = 0.8

        # Generate recommendations
        recommendations = []
        if risk_level == "high":
            recommendations.append("Consider breaking goal into smaller sub-goals")
            recommendations.append("Use 80/20 scoping to focus on high-impact tasks")
            recommendations.append("Review deadline - may need to adjust expectations")
        elif velocity_gap > 0:
            recommendations.append("Increase daily time allocation")
            recommendations.append("Remove blockers identified by Growth Scaffold")
        else:
            recommendations.append("Maintain current pace")
            recommendations.append("Celebrate progress to maintain momentum")

        return GoalCompletionEstimate(
            goal_id=goal.goal_id,
            goal_description=goal.description,
            estimated_completion_date=estimated_completion_date,
            confidence=confidence,
            percent_complete=percent_complete,
            current_velocity=current_velocity,
            required_velocity=required_velocity,
            velocity_gap=velocity_gap,
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendations=recommendations
        )

    def _calculate_slope(self, points: List[Tuple[float, float]]) -> float:
        """
        Calculate slope using simple linear regression

        Args:
            points: List of (x, y) points

        Returns:
            Slope (rate of change)
        """
        if len(points) < 2:
            return 0.0

        # Simple linear regression
        n = len(points)
        x_values = [p[0] for p in points]
        y_values = [p[1] for p in points]

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in points)
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        return slope
