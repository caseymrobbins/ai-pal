"""
FFE Dashboard Section - Fractal Flow Engine Metrics

Provides visualization and insights for:
- Progress Tapestry (visual win tracking)
- Momentum Loop metrics (planning → working → review → celebrate cycle)
- Bottleneck insights (where user gets stuck)
- Goal progress tracking
- Strength utilization analysis
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from ..ffe.engine import FractalFlowEngine
from ..ffe.models import Goal, AtomicBlock, MomentumState, StrengthType
from ..ffe.components.momentum_loop import MomentumLoopState
from .visualizations import (
    VisualizationEngine,
    ChartData,
    DataPoint,
    ChartType,
    OutputFormat,
    ASCIIChart
)
from .predictive_analytics import PredictiveAnalytics, GoalCompletionEstimate


@dataclass
class ProgressTapestryEntry:
    """Single entry in progress tapestry"""
    timestamp: datetime
    win_description: str
    win_type: str  # "task_complete", "bottleneck_resolved", "milestone", "streak"
    goal_id: Optional[str]
    pride_level: float  # 0-1
    strengths_used: List[StrengthType]
    connected_to: List[str]  # IDs of related wins (narrative connections)


@dataclass
class MomentumMetrics:
    """Momentum loop metrics"""
    # Current state
    current_state: MomentumLoopState
    time_in_current_state: timedelta
    total_cycles_completed: int

    # State distribution (% of time in each state)
    planning_percentage: float
    working_percentage: float
    reviewing_percentage: float
    celebrating_percentage: float

    # Efficiency metrics
    avg_cycle_duration: timedelta
    optimal_cycle_duration: timedelta
    time_wasted_in_transitions: timedelta

    # Flow metrics
    in_flow_percentage: float  # % of time in productive flow
    flow_disruptions: int  # Interruptions per day
    longest_flow_streak: timedelta


@dataclass
class BottleneckInsight:
    """Insight about a bottleneck"""
    bottleneck_id: str
    description: str
    first_encountered: datetime
    times_encountered: int
    time_spent_stuck: timedelta

    # Analysis
    bottleneck_type: str  # "knowledge_gap", "tool_limitation", "complexity", "unclear_requirements"
    affected_goals: List[str]  # Goal IDs
    related_skill_gap: Optional[str]

    # Resolution
    resolved: bool
    resolution_date: Optional[datetime]
    resolution_strategy: Optional[str]
    scaffolding_provided: List[str]

    # Impact
    agency_impact: float  # How much this hurt autonomy
    time_cost: timedelta  # Total time lost


@dataclass
class StrengthUtilization:
    """Analysis of signature strength usage"""
    strength_type: StrengthType
    utilization_rate: float  # 0-1 (how often used)
    effectiveness: float  # 0-1 (how well it works)

    # Usage patterns
    tasks_using_strength: int
    tasks_not_using_strength: int
    total_tasks: int

    # Performance
    avg_success_rate_with_strength: float
    avg_success_rate_without_strength: float
    strength_advantage: float  # with - without

    # Recommendations
    underutilized: bool
    recommended_tasks: List[str]


class FFEDashboard:
    """FFE-specific dashboard section"""

    def __init__(
        self,
        ffe_engine: FractalFlowEngine,
        viz_engine: Optional[VisualizationEngine] = None,
        predictive_analytics: Optional[PredictiveAnalytics] = None
    ):
        """
        Initialize FFE dashboard

        Args:
            ffe_engine: Fractal Flow Engine instance
            viz_engine: Visualization engine (creates if None)
            predictive_analytics: Predictive analytics engine (optional)
        """
        self.ffe_engine = ffe_engine
        self.viz_engine = viz_engine or VisualizationEngine()
        self.predictive_analytics = predictive_analytics

        # In-memory storage for demo (would use persistent storage in production)
        self.tapestry_entries: Dict[str, List[ProgressTapestryEntry]] = {}
        self.momentum_history: Dict[str, List[Tuple[datetime, MomentumLoopState]]] = {}

    async def get_progress_tapestry(
        self,
        user_id: str,
        days: int = 30
    ) -> List[ProgressTapestryEntry]:
        """
        Get progress tapestry (visual win tracking)

        Args:
            user_id: User ID
            days: Number of days to include

        Returns:
            List of progress tapestry entries
        """
        # Get entries from storage
        all_entries = self.tapestry_entries.get(user_id, [])

        # Filter to last N days
        cutoff = datetime.now() - timedelta(days=days)
        recent_entries = [e for e in all_entries if e.timestamp >= cutoff]

        # Sort by timestamp
        recent_entries.sort(key=lambda e: e.timestamp)

        return recent_entries

    async def add_win_to_tapestry(
        self,
        user_id: str,
        win_description: str,
        win_type: str,
        goal_id: Optional[str] = None,
        pride_level: float = 0.7,
        strengths_used: Optional[List[StrengthType]] = None
    ) -> ProgressTapestryEntry:
        """
        Add a win to the progress tapestry

        Args:
            user_id: User ID
            win_description: Description of the win
            win_type: Type of win
            goal_id: Associated goal ID (optional)
            pride_level: How proud user should feel (0-1)
            strengths_used: Strengths utilized

        Returns:
            Created tapestry entry
        """
        entry = ProgressTapestryEntry(
            timestamp=datetime.now(),
            win_description=win_description,
            win_type=win_type,
            goal_id=goal_id,
            pride_level=pride_level,
            strengths_used=strengths_used or [],
            connected_to=[]  # Could use ML to find narrative connections
        )

        # Add to storage
        if user_id not in self.tapestry_entries:
            self.tapestry_entries[user_id] = []
        self.tapestry_entries[user_id].append(entry)

        return entry

    async def visualize_progress_tapestry(
        self,
        user_id: str,
        days: int = 30,
        output_format: OutputFormat = OutputFormat.ASCII
    ) -> Any:
        """
        Visualize progress tapestry

        Args:
            user_id: User ID
            days: Number of days to show
            output_format: Output format

        Returns:
            Visualization (string for ASCII, dict for JSON)
        """
        entries = await self.get_progress_tapestry(user_id, days)

        if output_format == OutputFormat.ASCII:
            # Create timeline visualization
            events = []
            for entry in entries:
                event_type_map = {
                    "task_complete": "win",
                    "bottleneck_resolved": "bottleneck",
                    "milestone": "milestone",
                    "streak": "milestone"
                }
                events.append({
                    "timestamp": entry.timestamp,
                    "title": entry.win_description,
                    "type": event_type_map.get(entry.win_type, "info")
                })

            timeline = ASCIIChart.timeline(events, width=70)

            # Add summary stats
            total_wins = len(entries)
            avg_pride = sum(e.pride_level for e in entries) / max(1, len(entries))

            summary = f"\n\n📊 Progress Summary ({days} days):\n"
            summary += f"  Total Wins: {total_wins}\n"
            summary += f"  Avg Pride Level: {avg_pride:.2f}\n"
            summary += f"  Win Rate: {total_wins / max(1, days):.1f} wins/day\n"

            return timeline + summary

        elif output_format == OutputFormat.JSON:
            return {
                "title": f"Progress Tapestry ({days} days)",
                "entries": [
                    {
                        "timestamp": e.timestamp.isoformat(),
                        "description": e.win_description,
                        "type": e.win_type,
                        "goal_id": e.goal_id,
                        "pride_level": e.pride_level,
                        "strengths_used": [s.value for s in e.strengths_used]
                    }
                    for e in entries
                ],
                "summary": {
                    "total_wins": len(entries),
                    "avg_pride": sum(e.pride_level for e in entries) / max(1, len(entries)),
                    "win_rate": len(entries) / max(1, days)
                }
            }

    async def get_momentum_metrics(
        self,
        user_id: str,
        days: int = 7
    ) -> MomentumMetrics:
        """
        Get momentum loop metrics

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Momentum metrics
        """
        # Get momentum history
        history = self.momentum_history.get(user_id, [])

        if not history:
            # No data - return defaults
            return MomentumMetrics(
                current_state=MomentumLoopState.PLANNING,
                time_in_current_state=timedelta(0),
                total_cycles_completed=0,
                planning_percentage=0.0,
                working_percentage=0.0,
                reviewing_percentage=0.0,
                celebrating_percentage=0.0,
                avg_cycle_duration=timedelta(hours=2),
                optimal_cycle_duration=timedelta(hours=2),
                time_wasted_in_transitions=timedelta(0),
                in_flow_percentage=0.0,
                flow_disruptions=0,
                longest_flow_streak=timedelta(0)
            )

        # Filter to last N days
        cutoff = datetime.now() - timedelta(days=days)
        recent_history = [(ts, state) for ts, state in history if ts >= cutoff]

        # Current state
        current_state = recent_history[-1][1] if recent_history else MomentumLoopState.PLANNING
        time_in_current_state = datetime.now() - recent_history[-1][0] if recent_history else timedelta(0)

        # Count cycles
        cycles = 0
        for i in range(1, len(recent_history)):
            prev_state = recent_history[i-1][1]
            curr_state = recent_history[i][1]
            if prev_state == MomentumLoopState.CELEBRATING and curr_state == MomentumLoopState.PLANNING:
                cycles += 1

        # Calculate time in each state
        total_time = timedelta(0)
        state_times = {
            MomentumLoopState.PLANNING: timedelta(0),
            MomentumLoopState.WORKING: timedelta(0),
            MomentumLoopState.REVIEWING: timedelta(0),
            MomentumLoopState.CELEBRATING: timedelta(0)
        }

        for i in range(1, len(recent_history)):
            prev_ts, prev_state = recent_history[i-1]
            curr_ts, _ = recent_history[i]
            duration = curr_ts - prev_ts
            state_times[prev_state] += duration
            total_time += duration

        # Calculate percentages
        if total_time.total_seconds() > 0:
            planning_pct = state_times[MomentumLoopState.PLANNING] / total_time * 100
            working_pct = state_times[MomentumLoopState.WORKING] / total_time * 100
            reviewing_pct = state_times[MomentumLoopState.REVIEWING] / total_time * 100
            celebrating_pct = state_times[MomentumLoopState.CELEBRATING] / total_time * 100
        else:
            planning_pct = working_pct = reviewing_pct = celebrating_pct = 0.0

        # Calculate flow percentage (time in WORKING state is considered flow)
        in_flow_percentage = working_pct

        # Calculate avg cycle duration
        if cycles > 0:
            avg_cycle = total_time / cycles
        else:
            avg_cycle = timedelta(hours=2)

        return MomentumMetrics(
            current_state=current_state,
            time_in_current_state=time_in_current_state,
            total_cycles_completed=cycles,
            planning_percentage=planning_pct,
            working_percentage=working_pct,
            reviewing_percentage=reviewing_pct,
            celebrating_percentage=celebrating_pct,
            avg_cycle_duration=avg_cycle,
            optimal_cycle_duration=timedelta(hours=2),
            time_wasted_in_transitions=timedelta(minutes=5 * len(recent_history)),
            in_flow_percentage=in_flow_percentage,
            flow_disruptions=max(0, len(recent_history) - 20),  # Estimate
            longest_flow_streak=max(state_times.values(), default=timedelta(0))
        )

    async def get_bottleneck_insights(
        self,
        user_id: str,
        days: int = 30,
        include_resolved: bool = False
    ) -> List[BottleneckInsight]:
        """
        Get bottleneck insights

        Args:
            user_id: User ID
            days: Number of days to analyze
            include_resolved: Include resolved bottlenecks

        Returns:
            List of bottleneck insights
        """
        # In a real implementation, this would query the Growth Scaffold
        # For now, return mock data structure
        insights = []

        # This would typically come from Growth Scaffold storage
        # showing common patterns where users get stuck

        return insights

    async def get_strength_utilization(
        self,
        user_id: str,
        days: int = 30
    ) -> List[StrengthUtilization]:
        """
        Analyze signature strength utilization

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            List of strength utilization analyses
        """
        # Get tapestry entries to see which strengths were used
        entries = await self.get_progress_tapestry(user_id, days)

        if not entries:
            return []

        # Count strength usage
        strength_counts = {}
        total_tasks = len(entries)

        for entry in entries:
            for strength in entry.strengths_used:
                if strength not in strength_counts:
                    strength_counts[strength] = 0
                strength_counts[strength] += 1

        # Create utilization analysis for each strength
        utilizations = []
        for strength_type in StrengthType:
            tasks_with = strength_counts.get(strength_type, 0)
            tasks_without = total_tasks - tasks_with
            utilization_rate = tasks_with / max(1, total_tasks)

            # Mock effectiveness data (would come from success rates)
            effectiveness = 0.8 if utilization_rate > 0 else 0.5

            # Determine if underutilized
            # A strength is underutilized if it appears in personality but isn't used much
            underutilized = utilization_rate < 0.3  # Used less than 30% of the time

            utilizations.append(StrengthUtilization(
                strength_type=strength_type,
                utilization_rate=utilization_rate,
                effectiveness=effectiveness,
                tasks_using_strength=tasks_with,
                tasks_not_using_strength=tasks_without,
                total_tasks=total_tasks,
                avg_success_rate_with_strength=0.85,  # Mock
                avg_success_rate_without_strength=0.70,  # Mock
                strength_advantage=0.15,  # Mock
                underutilized=underutilized,
                recommended_tasks=[]  # Could suggest tasks that use this strength
            ))

        # Sort by utilization rate (most used first)
        utilizations.sort(key=lambda u: u.utilization_rate, reverse=True)

        return utilizations

    async def get_goal_progress_summary(
        self,
        user_id: str,
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive goal progress summary

        Args:
            user_id: User ID
            include_predictions: Include completion estimates

        Returns:
            Goal progress summary with predictions
        """
        # Get active goals from FFE engine
        # This would query the goal ingestor
        active_goals = []  # self.ffe_engine.goal_ingestor.get_active_goals(user_id)

        summary = {
            "total_active_goals": len(active_goals),
            "goals": []
        }

        for goal in active_goals:
            goal_data = {
                "goal_id": goal.goal_id,
                "description": goal.description,
                "importance": getattr(goal, 'importance', 5),
                "created_at": getattr(goal, 'created_at', datetime.now()).isoformat()
            }

            # Add prediction if available
            if include_predictions and self.predictive_analytics:
                # Mock task counts (would come from actual task tracking)
                completed = 5
                total = 20
                elapsed = 7

                estimate = await self.predictive_analytics.estimate_goal_completion(
                    goal, completed, total, elapsed
                )

                goal_data["prediction"] = {
                    "estimated_completion": estimate.estimated_completion_date.isoformat(),
                    "confidence": estimate.confidence,
                    "percent_complete": estimate.percent_complete,
                    "risk_level": estimate.risk_level,
                    "recommendations": estimate.recommendations
                }

            summary["goals"].append(goal_data)

        return summary
